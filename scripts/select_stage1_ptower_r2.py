"""Select on validation only; evaluate the selected tower once per fold.

The decision rule is the first round's, reused unchanged from
``select_stage1_ptower.select`` so the tie-breaks and their tests are shared.
The learning rate widens the table but never enters the tie-break.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

import torch
import yaml
from omegaconf import OmegaConf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
import stage1_ptower_r2 as r2  # noqa: E402
from run_stage1_ptower_r2 import TASK, evidence_for, grid  # noqa: E402
from select_stage1_ptower import select  # noqa: E402

DEST = ROOT / "experiments/phase1/stage1_ptower_r2"
ROUND_ONE = ROOT / "experiments/phase1/stage1_ptower"
KEY = ("candidate", "layers", "smoothing_weight", "history", "ft_lr")


def round_one_rows():
    """The frozen-feature control: the first round's runs, same folds and seeds."""
    path = ROUND_ONE / "validation_runs.csv"
    return list(csv.DictReader(path.open(encoding="utf-8-sig")))


def validation_table():
    groups, all_runs = {}, []
    for params in grid("HEAD"):
        done = evidence_for(params)
        if done is None:
            raise RuntimeError(f"Missing run: {params}")
        path, metrics = done
        record = {**{k: params[k] for k in ("candidate", "layers", "smoothing_weight",
                                            "history", "ft_lr", "fold", "seed")},
                  "path": str(path.relative_to(ROOT)), "jaccard": metrics["phase_jaccard"],
                  "accuracy": metrics["phase_accuracy"], "seconds": metrics["elapsed_seconds"]}
        groups.setdefault(tuple(record[k] for k in KEY), []).append(record)
        all_runs.append(record)
    assert len(groups) == 20 and len(all_runs) == 140

    control = {}
    for row in round_one_rows():
        control.setdefault((row["candidate"], int(row["layers"]), float(row["smoothing_weight"]),
                            int(row["history"]), row["fold"]), []).append(float(row["jaccard"]))

    table = []
    for key, runs in groups.items():
        row = dict(zip(KEY, key))
        for fold in "ABCDE":
            fold_runs = [r for r in runs if r["fold"] == fold]
            assert len(fold_runs) == (3 if fold == "A" else 1)
            row[f"{fold}_jaccard"] = statistics.mean(r["jaccard"] for r in fold_runs)
            row[f"{fold}_accuracy"] = statistics.mean(r["accuracy"] for r in fold_runs)
            frozen = control.get((row["candidate"], row["layers"], row["smoothing_weight"],
                                  row["history"], fold), [])
            row[f"{fold}_frozen_jaccard"] = statistics.mean(frozen) if frozen else ""
        a = [r["jaccard"] for r in runs if r["fold"] == "A"]
        frozen_means = [row[f"{f}_frozen_jaccard"] for f in "ABCDE"]
        row.update(mean_jaccard=statistics.mean(row[f"{f}_jaccard"] for f in "ABCDE"),
                   mean_accuracy=statistics.mean(row[f"{f}_accuracy"] for f in "ABCDE"),
                   frozen_mean_jaccard=(statistics.mean(frozen_means)
                                        if all(v != "" for v in frozen_means) else ""),
                   fold_A_pstd=statistics.pstdev(a), fold_A_sstd=statistics.stdev(a),
                   mean_seconds=statistics.mean(r["seconds"] for r in runs))
        table.append(row)

    DEST.mkdir(parents=True, exist_ok=True)
    for name, rows in (("validation_runs.csv", all_runs), ("validation_recipes.csv", table)):
        with (DEST / name).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    chosen, reason = select(table)
    selection = {"task_id": TASK, "recipe": chosen, "reason": reason, "test_seed": 42,
                 "P21": "UNKNOWN", "validation_runs": 140,
                 "source_table_sha256": base.sha256(DEST / "validation_recipes.csv")}
    with (DEST / "selection.json").open("x") as handle:
        json.dump(selection, handle, indent=2)
    print(json.dumps(selection, indent=2))


def test_selected():
    selection = json.loads((DEST / "selection.json").read_text())
    assert base.sha256(DEST / "validation_recipes.csv") == selection["source_table_sha256"]
    recipe = selection["recipe"]
    for fold in "ABCDE":
        params = {k: recipe[k] for k in KEY}
        params.update(action="train", fold=fold, seed=42)
        path, _ = evidence_for(params)
        cfg = OmegaConf.create(yaml.safe_load((path / "config.yaml").read_text()))
        cfg.device = "cuda:0"
        cfg.action = "test"
        base.deterministic(cfg.seed)
        names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
        model = base.build_model(cfg, len(names)).to(cfg.device)
        checkpoint = path / "checkpoints/best.pth"
        model.load_state_dict(torch.load(checkpoint, map_location=cfg.device,
                                         weights_only=True)["model"])
        run = r2.tracking.init(f"{TASK}_selected_test_{fold}", group=TASK, job_type="test",
                               config=OmegaConf.to_container(cfg, resolve=True))
        if run is None:
            raise RuntimeError("W&B could not start for test")
        # Claim before accessing test: interruptions must not cause silent re-evaluation.
        claim = DEST / f"test_access_{fold}.json"
        with claim.open("x") as handle:
            json.dump({"task_id": TASK, "fold": fold, "source_run": str(path.relative_to(ROOT)),
                       "checkpoint_sha256": base.sha256(checkpoint), "status": "started"}, handle)
        _, data = base.load_fold(cfg, parts=("test",))
        metrics = base.evaluate(model, data["test"], cfg.device, names)
        base.write_json(DEST / f"test_{fold}.json",
                        {"fold": fold, "seed": 42, "source_run": str(path.relative_to(ROOT)),
                         "metrics": metrics, "checkpoint_sha256": base.sha256(checkpoint)})
        identity = DEST / f"test_tracking_{fold}"
        identity.mkdir(exist_ok=False)
        r2.tracking.record_run_identity(identity)
        r2.tracking.log({f"test/{k}": v for k, v in metrics.items()
                         if isinstance(v, (int, float))})
        r2.tracking.finish()
        claimed = json.loads(claim.read_text())
        claimed["status"] = "completed"
        base.write_json(claim, claimed)
        print(f"TEST_COMPLETE {fold} J={metrics['phase_jaccard']}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["select", "test"])
    args = parser.parse_args()
    validation_table() if args.action == "select" else test_selected()

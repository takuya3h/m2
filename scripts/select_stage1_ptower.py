"""Select using validation only; evaluate the selected seed42 tower once per fold."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

import stage1_ptower as tower
import torch
import yaml
from omegaconf import OmegaConf
from run_stage1_ptower import TASK, completed, grid

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "experiments/phase1/stage1_ptower"


def select(rows):
    ranked = sorted(rows, key=lambda r: r["mean_jaccard"], reverse=True)
    best, second = ranked[:2]
    if best["mean_accuracy"] < second["mean_accuracy"]:
        raise ValueError("Co-primary directions disagree between best and runner-up")
    reason = "largest validation Jaccard with co-primary in same direction"
    if best["mean_jaccard"] - second["mean_jaccard"] <= best["fold_A_pstd"]:
        pair = [best, second]
        fast, slow = sorted(pair, key=lambda r: r["mean_seconds"])
        if slow["mean_seconds"] <= 1.20 * fast["mean_seconds"]:
            rank = {"A": 0, "C": 1, "B": 2}
            best = min(pair, key=lambda r: (rank[r["candidate"]], r["layers"]))
            reason = "within SD and 20% runtime: A before C before B, then shorter RF"
            # Same candidate and same RF: the 2026-09-18 amendment takes the steadier seeds.
            other = second if best is ranked[0] else ranked[0]
            if (best["candidate"], best["layers"]) == (other["candidate"], other["layers"]):
                best = min(pair, key=lambda r: r["fold_A_pstd"])
                reason = "within SD and 20% runtime, same candidate and RF: smaller fold A seed pstd"
        else:
            best, reason = fast, "within SD: shorter mean run time"
    return best, reason


def validation_table():
    groups = {}
    all_runs = []
    for params in grid("A") + grid("D"):
        done = completed(params)
        if done is None:
            raise RuntimeError(f"Missing run: {params}")
        path, metrics = done
        key = tuple(params[k] for k in ("candidate", "layers", "smoothing_weight", "history"))
        record = {**params, "path": str(path.relative_to(ROOT)),
                  "jaccard": metrics["phase_jaccard"], "accuracy": metrics["phase_accuracy"],
                  "seconds": metrics["elapsed_seconds"]}
        groups.setdefault(key, []).append(record)
        all_runs.append(record)
    assert len(groups) == 10 and len(all_runs) == 70
    table = []
    for key, runs in groups.items():
        row = dict(zip(("candidate", "layers", "smoothing_weight", "history"), key))
        for fold in "ABCDE":
            fold_runs = [r for r in runs if r["fold"] == fold]
            assert len(fold_runs) == (3 if fold == "A" else 1)
            row[f"{fold}_jaccard"] = statistics.mean(r["jaccard"] for r in fold_runs)
            row[f"{fold}_accuracy"] = statistics.mean(r["accuracy"] for r in fold_runs)
        a = [r["jaccard"] for r in runs if r["fold"] == "A"]
        row.update(mean_jaccard=statistics.mean(row[f"{f}_jaccard"] for f in "ABCDE"),
                   mean_accuracy=statistics.mean(row[f"{f}_accuracy"] for f in "ABCDE"),
                   fold_A_pstd=statistics.pstdev(a), fold_A_sstd=statistics.stdev(a),
                   mean_seconds=statistics.mean(r["seconds"] for r in runs))
        table.append(row)
    DEST.mkdir(parents=True, exist_ok=True)
    for name, rows in (("validation_runs.csv", all_runs), ("validation_recipes.csv", table)):
        with (DEST / name).open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    chosen, reason = select(table)
    selection = {"task_id": TASK, "recipe": chosen, "reason": reason,
                 "test_seed": 42, "P21": "UNKNOWN", "validation_runs": 70,
                 "source_table_sha256": tower.sha256(DEST / "validation_recipes.csv")}
    with (DEST / "selection.json").open("x") as f:
        json.dump(selection, f, indent=2)
    print(json.dumps(selection, indent=2))


def test_selected():
    selection = json.loads((DEST / "selection.json").read_text())
    assert tower.sha256(DEST / "validation_recipes.csv") == selection["source_table_sha256"]
    recipe = selection["recipe"]
    for fold in "ABCDE":
        params = {k: recipe[k] for k in ("candidate", "layers", "smoothing_weight", "history")}
        params.update(fold=fold, seed=42)
        path, _ = completed(params)
        cfg = OmegaConf.create(yaml.safe_load((path / "config.yaml").read_text()))
        cfg.device = "cuda:0"
        cfg.action = "test"
        tower.deterministic(cfg.seed)
        names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
        model = tower.build_model(cfg, len(names)).to(cfg.device)
        checkpoint = path / "checkpoints/best.pth"
        model.load_state_dict(torch.load(checkpoint, map_location=cfg.device, weights_only=True)["model"])
        run = tower.tracking.init(f"{TASK}_selected_test_{fold}", group=TASK, job_type="test",
                                  config=OmegaConf.to_container(cfg, resolve=True))
        if run is None:
            raise RuntimeError("W&B could not start for test")
        # Claim before accessing test: interruptions must not cause silent re-evaluation.
        claim = DEST / f"test_access_{fold}.json"
        with claim.open("x") as f:
            json.dump({"task_id": TASK, "fold": fold, "source_run": str(path.relative_to(ROOT)),
                       "checkpoint_sha256": tower.sha256(checkpoint), "status": "started"}, f)
        _, data = tower.load_fold(cfg, parts=("test",))
        metrics = tower.evaluate(model, data["test"], cfg.device, names)
        result = {"fold": fold, "seed": 42, "source_run": str(path.relative_to(ROOT)),
                  "metrics": metrics, "checkpoint_sha256": tower.sha256(checkpoint)}
        tower.write_json(DEST / f"test_{fold}.json", result)
        identity_dir = DEST / f"test_tracking_{fold}"
        identity_dir.mkdir(exist_ok=False)
        tower.tracking.record_run_identity(identity_dir)
        tower.tracking.log({f"test/{k}": v for k, v in metrics.items() if isinstance(v, (int, float))})
        tower.tracking.finish()
        claim_data = json.loads(claim.read_text())
        claim_data["status"] = "completed"
        tower.write_json(claim, claim_data)
        print(f"TEST_COMPLETE {fold} J={metrics['phase_jaccard']}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["select", "test"])
    args = parser.parse_args()
    if args.action == "select":
        validation_table()
    else:
        test_selected()

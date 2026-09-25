"""Select per init chain on validation only; evaluate each selected tower once per fold.

The decision rule is the first round's, reused unchanged from
``select_stage1_ptower.select`` so the tie-breaks and their tests are shared. The
learning rate widens the table but never enters the tie-break, and the init chain is
not a tie-break either: the contract keeps both chains, so the rule is applied once
per chain and two towers are confirmed.

The table carries the second round's confirmed tower and the first round's confirmed
tower on the same folds, so the effect of the resolution and of the init chain can be
read off in steps.
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
import stage1_ptower_r3 as r3  # noqa: E402
from run_stage1_ptower_r3 import INITS, TASK, evidence_for, grid  # noqa: E402
from select_stage1_ptower import select  # noqa: E402

DEST = ROOT / "experiments/phase1/stage1_ptower_r3"
ROUND_TWO = ROOT / "experiments/phase1/stage1_ptower_r2"
ROUND_ONE = ROOT / "experiments/phase1/stage1_ptower"
KEY = ("init", "candidate", "layers", "smoothing_weight", "history", "ft_lr")
HEAD_KEY = ("candidate", "layers", "smoothing_weight", "history", "ft_lr")


def confirmed(path):
    """A previous round's confirmed tower: its per-fold validation Jaccard."""
    recipe = json.loads((path / "selection.json").read_text())["recipe"]
    return {fold: recipe.get(f"{fold}_jaccard") for fold in "ABCDE"}


def select_chain(rows):
    """prereg §6 for one init chain, plus what to do when the co-primary disagrees.

    The prereg assumes the primary and the co-primary point the same way and does
    not say what to do otherwise. The user directed (2026-09-25) that the
    disagreement be recorded and the tie-break applied, which the observed case
    reaches anyway: the gap is inside fold A's seed spread. §6-2's "shorter
    receptive field" step is not in the shared rule; where it would apply this
    function reports whether it agrees with the step that is, so the gap between
    the prereg and the implementation is visible rather than assumed away.
    """
    ranked = sorted(rows, key=lambda r: r["mean_jaccard"], reverse=True)
    best, second = ranked[:2]
    if best["mean_accuracy"] >= second["mean_accuracy"]:
        chosen, reason = select(rows)
        return chosen, reason, None
    chosen, reason = select(rows, co_primary="record")
    shorter = min((best, second), key=lambda r: r["history"])
    disagreement = {
        "primary": {"best": best["mean_jaccard"], "runner_up": second["mean_jaccard"]},
        "co_primary": {"best": best["mean_accuracy"], "runner_up": second["mean_accuracy"]},
        "gap_within_fold_A_seed_spread":
            best["mean_jaccard"] - second["mean_jaccard"] <= best["fold_A_pstd"],
        "fold_A_pstd": best["fold_A_pstd"],
        "shorter_receptive_field_agrees":
            (shorter["candidate"], shorter["layers"], shorter["smoothing_weight"],
             shorter["history"], shorter["ft_lr"])
            == (chosen["candidate"], chosen["layers"], chosen["smoothing_weight"],
                chosen["history"], chosen["ft_lr"]),
        "resolved_by": reason,
    }
    return chosen, reason, disagreement


def validation_table():
    groups, all_runs = {}, []
    for params in grid("HEAD"):
        done = evidence_for(params)
        if done is None:
            raise RuntimeError(f"Missing run: {params}")
        path, metrics = done
        record = {**{k: params[k] for k in (*KEY, "fold", "seed")},
                  "path": str(path.relative_to(ROOT)), "jaccard": metrics["phase_jaccard"],
                  "accuracy": metrics["phase_accuracy"], "seconds": metrics["elapsed_seconds"]}
        groups.setdefault(tuple(record[k] for k in KEY), []).append(record)
        all_runs.append(record)
    assert len(groups) == 40 and len(all_runs) == 280, (len(groups), len(all_runs))

    round_two, round_one = confirmed(ROUND_TWO), confirmed(ROUND_ONE)
    table = []
    for key, runs in groups.items():
        row = dict(zip(KEY, key))
        for fold in "ABCDE":
            fold_runs = [r for r in runs if r["fold"] == fold]
            assert len(fold_runs) == (3 if fold == "A" else 1)
            row[f"{fold}_jaccard"] = statistics.mean(r["jaccard"] for r in fold_runs)
            row[f"{fold}_accuracy"] = statistics.mean(r["accuracy"] for r in fold_runs)
            row[f"{fold}_r2_jaccard"] = round_two[fold]
            row[f"{fold}_r1_jaccard"] = round_one[fold]
        a = [r["jaccard"] for r in runs if r["fold"] == "A"]
        row.update(mean_jaccard=statistics.mean(row[f"{f}_jaccard"] for f in "ABCDE"),
                   mean_accuracy=statistics.mean(row[f"{f}_accuracy"] for f in "ABCDE"),
                   r2_mean_jaccard=statistics.mean(round_two[f] for f in "ABCDE"),
                   r1_mean_jaccard=statistics.mean(round_one[f] for f in "ABCDE"),
                   fold_A_pstd=statistics.pstdev(a), fold_A_sstd=statistics.stdev(a),
                   mean_seconds=statistics.mean(r["seconds"] for r in runs))
        table.append(row)

    DEST.mkdir(parents=True, exist_ok=True)
    for name, rows in (("validation_runs.csv", all_runs), ("validation_recipes.csv", table)):
        with (DEST / name).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    chains = {}
    for init in INITS:
        rows = [r for r in table if r["init"] == init]
        assert len(rows) == 20, (init, len(rows))
        chosen, reason, disagreement = select_chain(rows)
        chains[init] = {"recipe": chosen, "reason": reason,
                        "co_primary_disagreement": disagreement}
    selection = {"task_id": TASK, "chains": chains, "test_seed": 42,
                 "P21": "UNKNOWN: frames for videos 17-22 are not on this host",
                 "validation_runs": len(all_runs), "recipes": len(table),
                 "source_table_sha256": base.sha256(DEST / "validation_recipes.csv")}
    with (DEST / "selection.json").open("x") as handle:
        json.dump(selection, handle, indent=2)
    print(json.dumps(selection, indent=2))


def test_selected():
    selection = json.loads((DEST / "selection.json").read_text())
    assert base.sha256(DEST / "validation_recipes.csv") == selection["source_table_sha256"]
    for init, chain in selection["chains"].items():
        recipe = chain["recipe"]
        for fold in "ABCDE":
            params = {k: recipe[k] for k in HEAD_KEY}
            params.update(action="train", init=init, fold=fold, seed=42)
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
            run = r3.tracking.init(f"{TASK}_selected_test_{init}_{fold}", group=TASK,
                                   job_type="test",
                                   config=OmegaConf.to_container(cfg, resolve=True))
            if run is None:
                raise RuntimeError("W&B could not start for test")
            # Claim before accessing test: interruptions must not cause silent re-evaluation.
            claim = DEST / f"test_access_{init}_{fold}.json"
            with claim.open("x") as handle:
                json.dump({"task_id": TASK, "init": init, "fold": fold,
                           "source_run": str(path.relative_to(ROOT)),
                           "checkpoint_sha256": base.sha256(checkpoint),
                           "status": "started"}, handle)
            _, data = base.load_fold(cfg, parts=("test",))
            metrics = base.evaluate(model, data["test"], cfg.device, names)
            base.write_json(DEST / f"test_{init}_{fold}.json",
                            {"init": init, "fold": fold, "seed": 42,
                             "source_run": str(path.relative_to(ROOT)), "metrics": metrics,
                             "checkpoint_sha256": base.sha256(checkpoint)})
            identity = DEST / f"test_tracking_{init}_{fold}"
            identity.mkdir(exist_ok=False)
            r3.tracking.record_run_identity(identity)
            r3.tracking.log({f"test/{k}": v for k, v in metrics.items()
                             if isinstance(v, (int, float))})
            r3.tracking.finish()
            claimed = json.loads(claim.read_text())
            claimed["status"] = "completed"
            base.write_json(claim, claimed)
            print(f"TEST_COMPLETE {init} {fold} J={metrics['phase_jaccard']}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["select", "test"])
    args = parser.parse_args()
    validation_table() if args.action == "select" else test_selected()

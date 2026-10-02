"""Tabulate P*-20 beside P*-15, test each confirmed tower once, measure the sender gap.

No selection happens: the recipe is the third round's. ``table`` puts the val of every
P*-20 run beside the third round's run with the same chain, fold and seed, plus the
host-difference control. ``test`` evaluates each chain's seed-42 tower once per fold,
claiming the slot before reading test so an interruption cannot re-evaluate silently.
``gap`` runs each confirmed tower (P*-15 and P*-20, both chains, seed 42) on its own
train videos and its val videos and records the difference against the crossfit
threshold. Only train and val are read there.
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

import run_stage1_ptower_r3 as round3  # noqa: E402
import stage1_ptower as base  # noqa: E402
import stage1_ptower_20 as p20  # noqa: E402
from run_stage1_ptower_20 import (  # noqa: E402
    FOLD_SEEDS,
    INITS,
    TASK,
    evidence_for,
    grid,
    head_of,
)

DEST = ROOT / "experiments/phase1/stage1_ptower_20"
DOCS = ROOT / "docs/stage1"
ROUND3_DEST = ROOT / "experiments/phase1/stage1_ptower_r3"
CROSSFIT_THRESHOLD = 0.03  # conventions#crossfit: 3 points of macro Jaccard
_canonical_folds = base.folds


def round3_run(init, fold, seed):
    params = dict(action="train", init=init, ft_lr=0.0001, fold=fold, seed=seed, **head_of(init))
    done = round3.evidence_for(params)
    if done is None:
        raise RuntimeError(f"Third-round run missing: {params}")
    return done


def p20_run(init, fold, seed):
    params = dict(action="train", data_setting="P20", init=init, ft_lr=0.0001,
                  fold=fold, seed=seed, **head_of(init))
    done = evidence_for(params)
    if done is None:
        raise RuntimeError(f"P*-20 run missing: {params}")
    return done


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def table():
    rows = []
    for init in INITS:
        for fold, seed in FOLD_SEEDS:
            path20, m20 = p20_run(init, fold, seed)
            path15, m15 = round3_run(init, fold, seed)
            rows.append({"init": init, "fold": fold, "seed": seed, "host": "efros",
                         "p20_val_jaccard": m20["phase_jaccard"],
                         "p20_val_accuracy": m20["phase_accuracy"],
                         "p15_val_jaccard": m15["phase_jaccard"],
                         "p15_val_accuracy": m15["phase_accuracy"],
                         "delta_jaccard": m20["phase_jaccard"] - m15["phase_jaccard"],
                         "delta_accuracy": m20["phase_accuracy"] - m15["phase_accuracy"],
                         "p20_run": str(path20.relative_to(ROOT)),
                         "p15_run": str(path15.relative_to(ROOT))})
    control, m = evidence_for(grid("CTRL")[-1])
    _, ref = round3_run("coco", "A", 42)
    rows.append({"init": "coco", "fold": "A", "seed": 42, "host": "efros_control_P15",
                 "p20_val_jaccard": None, "p20_val_accuracy": None,
                 "p15_val_jaccard": m["phase_jaccard"], "p15_val_accuracy": m["phase_accuracy"],
                 "delta_jaccard": m["phase_jaccard"] - ref["phase_jaccard"],
                 "delta_accuracy": m["phase_accuracy"] - ref["phase_accuracy"],
                 "p20_run": None, "p15_run": str(control.relative_to(ROOT))})
    assert len(rows) == 15, len(rows)
    summary = {}
    for init in INITS:
        chain = [r for r in rows[:-1] if r["init"] == init]
        per_fold = {}
        for fold in "ABCDE":
            runs = [r for r in chain if r["fold"] == fold]
            per_fold[fold] = {k: statistics.mean(r[k] for r in runs) for k in
                              ("p20_val_jaccard", "p20_val_accuracy",
                               "p15_val_jaccard", "p15_val_accuracy")}
        deltas = [per_fold[f]["p20_val_jaccard"] - per_fold[f]["p15_val_jaccard"] for f in "ABCDE"]
        summary[init] = {
            "per_fold": per_fold,
            **{f"mean_{k}": statistics.mean(per_fold[f][k] for f in "ABCDE")
               for k in ("p20_val_jaccard", "p20_val_accuracy",
                         "p15_val_jaccard", "p15_val_accuracy")},
            "delta_jaccard_per_fold": deltas, "delta_jaccard_mean": statistics.mean(deltas),
            "delta_jaccard_fold_sd": statistics.stdev(deltas),
            "p15_fold_sd": statistics.stdev(per_fold[f]["p15_val_jaccard"] for f in "ABCDE"),
        }
        summary[init]["delta_standardized_by_p15_fold_sd"] = (
            summary[init]["delta_jaccard_mean"] / summary[init]["p15_fold_sd"])
    write_csv(DEST / "validation_runs.csv", rows)
    write_csv(DOCS / "ptower_20_validation_runs.csv", rows)
    base.write_json(DEST / "validation_summary.json", {"task_id": TASK, "chains": summary})
    print(json.dumps(summary, indent=2))


def load_head(path, device):
    cfg = OmegaConf.create(yaml.safe_load((path / "config.yaml").read_text()))
    cfg.device = device
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    model = base.build_model(cfg, len(names)).to(device)
    checkpoint = path / "checkpoints/best.pth"
    model.load_state_dict(torch.load(checkpoint, map_location=device,
                                     weights_only=True)["model"])
    return cfg, model, names, checkpoint


def use_folds(setting):
    base.folds = p20.folds_p20 if setting == "P20" else _canonical_folds


def test_confirmed():
    for init in INITS:
        for fold in "ABCDE":
            path, _ = p20_run(init, fold, 42)
            cfg, model, names, checkpoint = load_head(path, "cuda:0")
            use_folds("P20")
            base.deterministic(cfg.seed)
            run = p20.r3.tracking.init(f"{TASK}_confirmed_test_{init}_{fold}", group=TASK,
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
            assert not set(p20.EXTRA_TRAIN) & {v for v, _, _ in data["test"]}
            metrics = base.evaluate(model, data["test"], cfg.device, names)
            p15 = json.loads((ROUND3_DEST / f"test_{init}_{fold}.json").read_text())
            base.write_json(DEST / f"test_{init}_{fold}.json",
                            {"init": init, "fold": fold, "seed": 42, "data_setting": "P20",
                             "source_run": str(path.relative_to(ROOT)), "metrics": metrics,
                             "checkpoint_sha256": base.sha256(checkpoint),
                             "p15_test_jaccard": p15["metrics"]["phase_jaccard"],
                             "p15_test_accuracy": p15["metrics"]["phase_accuracy"]})
            identity = DEST / f"test_tracking_{init}_{fold}"
            identity.mkdir(exist_ok=False)
            p20.r3.tracking.record_run_identity(identity)
            p20.r3.tracking.log({f"test/{k}": v for k, v in metrics.items()
                                 if isinstance(v, (int, float))})
            p20.r3.tracking.finish()
            claimed = json.loads(claim.read_text())
            claimed["status"] = "completed"
            base.write_json(claim, claimed)
            print(f"TEST_COMPLETE {init} {fold} J={metrics['phase_jaccard']}", flush=True)


def sender_gap():
    """Each confirmed tower on its own train videos and on its val videos."""
    rows = []
    run = p20.r3.tracking.init(f"{TASK}_sender_gap", group=TASK, job_type="sender_gap",
                               config={"task_id": TASK, "threshold": CROSSFIT_THRESHOLD})
    if run is None:
        raise RuntimeError("W&B could not start for the sender gap")
    for init in INITS:
        for setting, finder in (("P15", round3_run), ("P20", p20_run)):
            for fold in "ABCDE":
                path, _ = finder(init, fold, 42)
                cfg, model, names, _ = load_head(path, "cuda:0")
                use_folds(setting)
                base.deterministic(cfg.seed)
                split, data = base.load_fold(cfg, parts=("train", "val"))
                trained_on = yaml.safe_load((path / "config.yaml").read_text())["data"]["videos"]
                assert sorted(trained_on["train"]) == sorted(split["train"]), (path, split)
                train = base.evaluate(model, data["train"], cfg.device, names)
                val = base.evaluate(model, data["val"], cfg.device, names)
                gap_j = train["phase_jaccard"] - val["phase_jaccard"]
                gap_a = train["phase_accuracy"] - val["phase_accuracy"]
                rows.append({"init": init, "data_setting": setting, "fold": fold, "seed": 42,
                             "train_videos": " ".join(sorted(split["train"])),
                             "val_videos": " ".join(sorted(split["val"])),
                             "train_jaccard": train["phase_jaccard"],
                             "val_jaccard": val["phase_jaccard"], "gap_jaccard": gap_j,
                             "train_accuracy": train["phase_accuracy"],
                             "val_accuracy": val["phase_accuracy"], "gap_accuracy": gap_a,
                             "over_threshold_jaccard": gap_j > CROSSFIT_THRESHOLD,
                             "over_threshold_accuracy": gap_a > CROSSFIT_THRESHOLD,
                             "source_run": str(path.relative_to(ROOT))})
                print(f"GAP {init} {setting} {fold} J {gap_j:+.4f} acc {gap_a:+.4f}", flush=True)
    use_folds("P15")
    assert len(rows) == 20, len(rows)
    write_csv(DEST / "sender_gap.csv", rows)
    write_csv(DOCS / "ptower_20_sender_gap.csv", rows)
    p20.r3.tracking.log({f"gap/{r['init']}_{r['data_setting']}_{r['fold']}": r["gap_jaccard"]
                         for r in rows})
    p20.r3.tracking.finish()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["table", "test", "gap"])
    args = parser.parse_args()
    {"table": table, "test": test_confirmed, "gap": sender_gap}[args.action]()

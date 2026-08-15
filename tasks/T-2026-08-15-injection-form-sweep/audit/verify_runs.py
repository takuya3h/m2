"""Phase B Step 3（G2）— 完走・条件・陽性対照を実物で確かめる。

説明文ではなく run の実体（metrics.json）で確かめる。
評価条件は分母を構成する既存 run と recipes_match で照合し、
構成キーを一つだけ変えた偽の条件が一致**しない**ことを対照とする。
"""

import json
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from egosurgery.utils.eval_recipe import recipes_match  # noqa: E402

TASK = "T-2026-08-15-injection-form-sweep"
SEEDS = {42, 123, 456, 7, 89, 101, 202, 303, 404, 505}
# 分母を構成する既存 run（評価条件の照合の基準）。
DENOM_RUN = ROOT / "experiments/phase1/s4_phase_baseline_001_frozen_tecno_phase_baseline_seed42"
EXPECT_SPLIT = {"split_train_images": 9657, "split_val_images": 1515, "split_test_images": 4265}
EXPECT_BACKBONE = "relation_detr_resnet50_frozen_seed42"


def main() -> None:
    runs = []
    for d in sorted((ROOT / "experiments/phase1").glob("s4_grasp_injection_*")):
        m_path = d / "metrics.json"
        if not m_path.exists():
            continue
        m = json.loads(m_path.read_text())
        if m.get("task_id") != TASK:
            continue
        runs.append((d.name, m))

    by_arm = defaultdict(list)
    for name, m in runs:
        key = f"{m['arm']}:{m['signal']}{':staged' if m.get('staged') else ''}"
        by_arm[key].append((name, m))

    denom_recipe = json.loads((DENOM_RUN / "metrics.json").read_text())["eval_recipe"]

    recipe_ok, split_ok, backbone_ok, seed_ok = [], [], [], []
    oracle_flagged, elapsed_by_arm = [], defaultdict(list)
    for name, m in runs:
        r = m["eval_recipe"]
        recipe_ok.append((name, recipes_match(denom_recipe, r)))
        split_ok.append((name, all(r.get(k) == v for k, v in EXPECT_SPLIT.items())))
        backbone_ok.append((name, r["test_cfg"].get("backbone") == EXPECT_BACKBONE))
        seed_ok.append((name, int(name.rsplit("seed", 1)[1]) in SEEDS))
        if m["signal"] == "oracle_upper_bound_only":
            oracle_flagged.append((name, m.get("oracle_upper_bound_only_do_not_report") is True))
        elapsed_by_arm[f"{m['arm']}:{m['signal']}{':staged' if m.get('staged') else ''}"].append(
            m["elapsed_seconds"]
        )

    # 陽性対照 — 構成キーを一つだけ変えた偽の条件は一致しない。
    controls = []
    for key, val in (
        ("inference_protocol", "offline_noncausal"),
        ("temporal_head", "mstcn"),
        ("backbone", "relation_detr_resnet50_frozen_seed123"),
    ):
        fake = deepcopy(denom_recipe)
        fake["test_cfg"][key] = val
        controls.append({"changed": key, "matches": recipes_match(denom_recipe, fake)})

    result = {
        "n_runs": len(runs),
        "per_arm_counts": {k: len(v) for k, v in sorted(by_arm.items())},
        "all_recipes_match_denominator": all(ok for _, ok in recipe_ok),
        "recipe_mismatch": [n for n, ok in recipe_ok if not ok],
        "all_splits_expected": all(ok for _, ok in split_ok),
        "split_mismatch": [n for n, ok in split_ok if not ok],
        "all_backbone_frozen_seed42": all(ok for _, ok in backbone_ok),
        "backbone_mismatch": [n for n, ok in backbone_ok if not ok],
        "all_seeds_planned": all(ok for _, ok in seed_ok),
        "oracle_runs": len(oracle_flagged),
        "oracle_all_flagged_do_not_report": all(ok for _, ok in oracle_flagged),
        "positive_controls": controls,
        "positive_controls_all_rejected": all(not c["matches"] for c in controls),
        "elapsed_seconds_by_arm": {
            k: {"n": len(v), "mean": sum(v) / len(v), "min": min(v), "max": max(v)}
            for k, v in sorted(elapsed_by_arm.items())
        },
    }
    (AUDIT / "verify_runs.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"記録: {AUDIT / 'verify_runs.json'}")
    print(f"完走した本数 = {result['n_runs']}")
    for k, n in result["per_arm_counts"].items():
        print(f"  {k:<44} {n}")
    print(f"評価条件が分母と全件一致  : {result['all_recipes_match_denominator']}")
    print(f"分割 9657/1515/4265 全件  : {result['all_splits_expected']}")
    print(f"凍結源 seed42 全件        : {result['all_backbone_frozen_seed42']}")
    print(f"種が計画どおり            : {result['all_seeds_planned']}")
    print(f"oracle の報告不可の印     : {result['oracle_runs']} 本すべて={result['oracle_all_flagged_do_not_report']}")
    print(f"陽性対照 3 件すべて棄却   : {result['positive_controls_all_rejected']}")
    print()
    print("一本あたりの所要時間（秒）")
    for k, v in result["elapsed_seconds_by_arm"].items():
        print(f"  {k:<44} mean={v['mean']:.2f} min={v['min']:.2f} max={v['max']:.2f}")


if __name__ == "__main__":
    main()

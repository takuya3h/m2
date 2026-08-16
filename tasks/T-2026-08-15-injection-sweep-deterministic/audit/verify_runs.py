#!/usr/bin/env python
"""Phase B Step 3: 完走と条件を確かめる（G2）。

照合は**読まれる側**で行う（前の契約の実測による）。

  凍結源   … 設定の frozen_source.* ではなく data.feature_cache の経路
  評価規約 … 設定の eval_recipe.* ではなく metrics.json の証跡

陽性対照を置く。構成キーを一つだけ変えた偽の条件で一致しないことを確かめる。

出力: audit/g2_verification.json
"""

from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]
TASK_ID = "T-2026-08-15-injection-sweep-deterministic"
EXPECTED_RUNS = 360
EXPECTED_SPLITS = {"split_train_images": 9657, "split_val_images": 1515, "split_test_images": 4265}
BROKEN_POPULATION = 14977  # これになっていれば実装が壊れている

_spec = importlib.util.spec_from_file_location("h", PROJ / "tools" / "harvest_runindex.py")
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)


def main() -> None:
    import yaml

    ref = "phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42"
    den = [r for r in csv.DictReader(
        open(PROJ / "runindex/experiments.csv", encoding="utf-8")) if r["experiment_id"] == ref][0]
    den_recipe_id = den["eval_recipe_id"]
    den_frozen = ref.split("~")[-1]

    runs, problems = [], []
    for metrics_path in sorted((PROJ / "experiments").rglob("metrics.json")):
        try:
            m = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if m.get("task_id") != TASK_ID:
            continue
        run = metrics_path.parent
        cfg = yaml.safe_load((run / "config.yaml").read_text(encoding="utf-8"))
        cache = str(cfg["data"]["feature_cache"]).rstrip("/")
        recipe = m.get("eval_recipe")
        rid = H.eval_recipe_id(recipe) if recipe else None
        g = cfg.get("grasp_inference", {})
        rec = {
            "run": str(run.relative_to(PROJ)),
            "seed": int(cfg["seed"]),
            "arm": str(g.get("arm")),
            "signal": str(g.get("signal")),
            "staged": bool(g.get("staged", False)),
            "completed": bool(m.get("completed", False)),
            "frozen_tag_from_cache": cache.split("/")[-1],
            "eval_recipe_id": rid,
            "recipe_matches_denominator": rid == den_recipe_id,
            "splits": {k: (recipe or {}).get(k) for k in EXPECTED_SPLITS},
            "deterministic": bool((m.get("determinism") or {}).get("deterministic", False)),
            "do_not_report": m.get("oracle_upper_bound_only_do_not_report"),
            "elapsed_seconds": m.get("elapsed_seconds"),
        }
        for label, ok in (
            ("未完走", rec["completed"]),
            ("評価条件が分母と不一致", rec["recipe_matches_denominator"]),
            ("凍結源が分母と不一致", rec["frozen_tag_from_cache"] == den_frozen),
            ("分割が期待と不一致", rec["splits"] == EXPECTED_SPLITS),
            ("決定化の印なし", rec["deterministic"]),
        ):
            if not ok:
                problems.append({"run": rec["run"], "problem": label, "detail": rec})
        if BROKEN_POPULATION in (rec["splits"] or {}).values():
            problems.append({"run": rec["run"], "problem": "母集団が 14977（実装が壊れている）"})
        runs.append(rec)

    # 陽性対照: 構成キーを一つだけ変えた偽の条件が一致しないこと
    sample = next((r for r in runs if r["eval_recipe_id"]), None)
    fake = None
    if sample:
        m = json.loads((PROJ / sample["run"] / "metrics.json").read_text(encoding="utf-8"))
        bogus = json.loads(json.dumps(m["eval_recipe"]))
        bogus["test_cfg"]["num_layers"] = 4          # 8 -> 4 を一つだけ変える
        fake = H.eval_recipe_id(bogus)

    oracle = [r for r in runs if r["signal"] == "oracle_upper_bound_only"]
    payload = {
        "expected_runs": EXPECTED_RUNS,
        "found_runs": len(runs),
        "all_completed": all(r["completed"] for r in runs),
        "arm_counts": dict(Counter(
            (r["arm"], r["signal"], r["staged"]).__str__() for r in runs)),
        "seed_counts_ok": {
            k: v for k, v in Counter(r["seed"] for r in runs).items() if v != 6
        },
        "denominator": {"eval_recipe_id": den_recipe_id, "frozen_source_tag": den_frozen},
        "all_recipes_match_denominator": all(r["recipe_matches_denominator"] for r in runs),
        "all_frozen_match_denominator": all(
            r["frozen_tag_from_cache"] == den_frozen for r in runs),
        "distinct_frozen_tags": sorted({r["frozen_tag_from_cache"] for r in runs}),
        "all_splits_expected": all(r["splits"] == EXPECTED_SPLITS for r in runs),
        "expected_splits": EXPECTED_SPLITS,
        "all_deterministic": all(r["deterministic"] for r in runs),
        "oracle_runs": len(oracle),
        "oracle_all_flagged_do_not_report": all(r["do_not_report"] is True for r in oracle),
        "non_oracle_flag_false": all(
            r["do_not_report"] is False for r in runs if r["signal"] != "oracle_upper_bound_only"),
        "positive_control": {
            "changed": "eval_recipe.test_cfg.num_layers 8 -> 4",
            "fake_recipe_id": fake,
            "matches_denominator": fake == den_recipe_id,
            "expected": False,
        },
        "problems": problems,
        "elapsed_seconds_mean_by_arm": {},
        "runs": runs,
    }
    by_arm: dict[str, list] = {}
    for r in runs:
        by_arm.setdefault(f"{r['signal']}{'+staged' if r['staged'] else ''}", []).append(
            r["elapsed_seconds"] or 0.0)
    payload["elapsed_seconds_mean_by_arm"] = {
        k: round(sum(v) / len(v), 2) for k, v in sorted(by_arm.items())}

    (AUDIT / "g2_verification.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"見つかった run           : {payload['found_runs']} / {EXPECTED_RUNS}")
    print(f"全本が完走               : {payload['all_completed']}")
    print(f"腕ごとの内訳             : {json.dumps(payload['arm_counts'], ensure_ascii=False)}")
    print(f"6 本でない種             : {payload['seed_counts_ok'] or 'なし（全種 6 本）'}")
    print(f"評価条件が分母と一致(全本): {payload['all_recipes_match_denominator']}")
    print(f"凍結源が分母と一致(全本)  : {payload['all_frozen_match_denominator']} {payload['distinct_frozen_tags']}")
    print(f"分割が期待どおり(全本)    : {payload['all_splits_expected']} {EXPECTED_SPLITS}")
    print(f"決定化の印(全本)          : {payload['all_deterministic']}")
    print(f"正解の腕の報告不可の印    : {payload['oracle_all_flagged_do_not_report']} ({payload['oracle_runs']} 本)")
    print(f"陽性対照(偽の条件)        : 一致={payload['positive_control']['matches_denominator']} （False であるべき）")
    print(f"所要時間の平均            : {json.dumps(payload['elapsed_seconds_mean_by_arm'], ensure_ascii=False)}")
    print(f"問題                      : {len(problems)} 件")
    for p in problems[:5]:
        print("   -", p["problem"], p["run"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Phase C: 対の差を腕ごとに測る。

**事前登録の決め方をそのまま当てる。結果を見てから変えない。**

    主たる差 = 正解を渡した腕 − 無情報な信号を渡した腕
    判定      = |平均| / 平均の標準誤差 >= 2
    標準誤差  = 対の差の母標準偏差 / sqrt(種の数)

全種同符号は要件としない（事前登録に理由がある）。効果の大きさと
符号が正の種の割合は併せて報告するが、判定には使わない。

出力: audit/sweep.json
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]
TASK_ID = "T-2026-08-15-injection-sweep-deterministic"
METRIC = "phase_accuracy"          # 測る側 val の accuracy
CONTROL = "uninformative"          # 全ての差の引き算の相手
PRIMARY = "oracle"                 # 主たる腕（上限であって成果ではない）
SECONDARY = ["inferred", "raw_logits", "standardized", "staged"]

# 設定から腕を同定するための対応（audit/arm_table.json と同じ実測値）
ARM_KEY = {
    ("ctrl", "zeros", False): "uninformative",
    ("inj", "oracle_upper_bound_only", False): "oracle",
    ("inj", "predicted_sigmoid", False): "inferred",
    ("inj", "raw_logits", False): "raw_logits",
    ("inj", "standardized", False): "standardized",
    ("inj", "predicted_sigmoid", True): "staged",
}


def pstd(xs: list[float]) -> float:
    """母標準偏差（事前登録の指定）。"""
    n = len(xs)
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / n)


def collect() -> dict:
    """本契約の run を集める。task_id で選ぶ（指示書と run を結ぶ唯一の鍵）。"""
    import yaml

    by_arm: dict[str, dict[int, dict]] = {}
    skipped = []
    for metrics_path in sorted((PROJ / "experiments").rglob("metrics.json")):
        try:
            m = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if m.get("task_id") != TASK_ID:
            continue
        run = metrics_path.parent
        cfg = yaml.safe_load((run / "config.yaml").read_text(encoding="utf-8"))
        g = cfg.get("grasp_inference", {})
        key = (str(g.get("arm")), str(g.get("signal")), bool(g.get("staged", False)))
        arm = ARM_KEY.get(key)
        if arm is None:
            skipped.append({"run": str(run.relative_to(PROJ)), "key": list(key)})
            continue
        seed = int(cfg.get("seed"))
        by_arm.setdefault(arm, {})[seed] = {
            "run": str(run.relative_to(PROJ)),
            "metrics": m,
            "do_not_report": bool(m.get("oracle_upper_bound_only_do_not_report", False)),
            "deterministic": bool((m.get("determinism") or {}).get("deterministic", False)),
            "elapsed_seconds": m.get("elapsed_seconds"),
        }
    return {"by_arm": by_arm, "skipped": skipped}


def paired(by_arm: dict, arm: str) -> dict:
    """腕と対照の、同じ種で対にした差。"""
    ctrl = by_arm[CONTROL]
    test = by_arm.get(arm, {})
    seeds = sorted(set(ctrl) & set(test))
    diffs = [
        {
            "seed": s,
            "arm_value": float(test[s]["metrics"][METRIC]),
            "control_value": float(ctrl[s]["metrics"][METRIC]),
            "diff": float(test[s]["metrics"][METRIC]) - float(ctrl[s]["metrics"][METRIC]),
        }
        for s in seeds
    ]
    d = [x["diff"] for x in diffs]
    n = len(d)
    if n == 0:
        return {"arm": arm, "n_pairs": 0}
    mean = sum(d) / n
    sd = pstd(d)
    sem = sd / math.sqrt(n)
    ratio = abs(mean) / sem if sem > 0 else float("inf")
    n_pos = sum(1 for x in d if x > 0)
    n_zero = sum(1 for x in d if x == 0)
    return {
        "arm": arm,
        "n_pairs": n,
        "mean": mean,
        "pstd": sd,
        "sem": sem,
        "abs_mean_over_sem": ratio,
        "meets_rule_ratio_ge_2": ratio >= 2,
        "effect_size_mean_over_pstd": mean / sd if sd > 0 else None,
        "n_positive": n_pos,
        "n_zero": n_zero,
        "fraction_positive": n_pos / n,
        "detectable_2sem": 2 * sem,
        "min_diff": min(d),
        "max_diff": max(d),
        "per_seed": diffs,
    }


def main() -> None:
    data = collect()
    by_arm = data["by_arm"]
    counts = {a: len(v) for a, v in sorted(by_arm.items())}
    print("腕ごとの run 数:", counts, "合計", sum(counts.values()))
    if CONTROL not in by_arm:
        raise SystemExit("対照の腕が見つからない。Phase B が終わっていない可能性がある")

    primary = paired(by_arm, PRIMARY)
    secondary = {a: paired(by_arm, a) for a in SECONDARY}

    # 過去の実験との突き合わせ（推論した値の腕・基準点の 3 種に限る）
    three = [42, 123, 456]
    inf3 = [x for x in secondary["inferred"].get("per_seed", []) if x["seed"] in three]
    three_seed_mean = sum(x["diff"] for x in inf3) / len(inf3) if inf3 else None

    # 無情報な腕と既存の基準点との差（対にできない。参考値）
    ref = "phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42"
    den = [r for r in csv.DictReader(
        open(PROJ / "runindex/experiments.csv", encoding="utf-8")) if r["experiment_id"] == ref][0]
    ctrl_vals = [float(v["metrics"][METRIC]) for v in by_arm[CONTROL].values()]
    ctrl_mean = sum(ctrl_vals) / len(ctrl_vals)

    payload = {
        "task_id": TASK_ID,
        "metric": METRIC,
        "split": "val",
        "control_arm": CONTROL,
        "run_counts": counts,
        "total_runs": sum(counts.values()),
        "skipped_runs": data["skipped"],
        "all_deterministic": all(
            r["deterministic"] for v in by_arm.values() for r in v.values()),
        "oracle_flagged_do_not_report": all(
            r["do_not_report"] for r in by_arm.get(PRIMARY, {}).values()),
        "primary": primary,
        "secondary_exploratory": secondary,
        "past_comparison": {
            "note": "推論した値の腕。基準点の 3 種に限った平均。過去の 2 実験は -0.0044 と +0.0004",
            "seeds": three,
            "per_seed": inf3,
            "mean_over_three_seeds": three_seed_mean,
            "previous_experiments": [-0.0044, 0.0004],
        },
        "detectability": {
            "prereg_expected_2sem_at_60_seeds": 0.0014,
            "achieved_2sem_primary": primary.get("detectable_2sem"),
            "prereg_assumed_pstd": 0.0054519,
            "observed_pstd_primary": primary.get("pstd"),
        },
        "control_vs_existing_baseline": {
            "note": "対にできない参考値。既存の基準点は決定化しない状態で測られている",
            "control_mean": ctrl_mean,
            "control_n": len(ctrl_vals),
            "baseline_mean": float(den["accuracy_mean"]),
            "baseline_pstd": float(den["accuracy_pstd"]),
            "baseline_n_runs": int(den["n_runs"]),
            "difference": ctrl_mean - float(den["accuracy_mean"]),
        },
        "timing": {
            "mean_elapsed_seconds_by_arm": {
                a: sum(r["elapsed_seconds"] for r in v.values()) / len(v)
                for a, v in sorted(by_arm.items())
            }
        },
    }
    (AUDIT / "sweep.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    p = primary
    print()
    print("=== 主たる差（正解 − 無情報） ===")
    print(f"  対の数        {p['n_pairs']}")
    print(f"  平均          {p['mean']:+.7f}")
    print(f"  母標準偏差    {p['pstd']:.7f}")
    print(f"  標準誤差      {p['sem']:.7f}")
    print(f"  |平均|/標準誤差 {p['abs_mean_over_sem']:.4f}   判定(>=2): {p['meets_rule_ratio_ge_2']}")
    print(f"  効果の大きさ  {p['effect_size_mean_over_pstd']:+.4f}")
    print(f"  符号が正の割合 {p['n_positive']}/{p['n_pairs']} = {p['fraction_positive']:.3f}")
    print(f"  達成された値(2SEM) {p['detectable_2sem']:.7f}  （見込み 0.0014）")
    print()
    print("=== 従たる腕（探索。確認のための判断には使わない） ===")
    for a, s in secondary.items():
        if s.get("n_pairs"):
            print(f"  {a:14s} n={s['n_pairs']:3d} mean={s['mean']:+.7f} "
                  f"ratio={s['abs_mean_over_sem']:.3f} rule={s['meets_rule_ratio_ge_2']} "
                  f"pos={s['fraction_positive']:.3f}")
    print()
    print(f"written: {AUDIT / 'sweep.json'}")


if __name__ == "__main__":
    main()

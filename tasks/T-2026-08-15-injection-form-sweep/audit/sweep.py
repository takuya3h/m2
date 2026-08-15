"""Phase C — 対の差を腕ごとに測る（G3）。

事前登録の決め方をそのまま当てる。**結果を見てから変えない。**

    差 = 各腕 − 無情報な腕（同じ種で対にする）
    判定 = abs(平均) / 母標準偏差 >= 1 かつ 全ての種で符号が揃う

確認のための判断に使うのは**正解を渡した腕（上限測定専用）only**。
残る四つは探索であり、四つを同時に見るためたまたま条件を満たすものが出やすい。

数値の出所は 60 本の metrics.json（丸めも転記も挟まない）。
"""

import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent

TASK = "T-2026-08-15-injection-form-sweep"
SEEDS = [42, 123, 456, 7, 89, 101, 202, 303, 404, 505]
PRIOR = {"mean": -0.004400440044004379, "pstd": 0.0008232469497852892, "ratio": 5.345224838248179}
ARM_ORDER = [
    "inj:oracle_upper_bound_only",
    "inj:predicted_sigmoid",
    "inj:raw_logits",
    "inj:standardized",
    "inj:predicted_sigmoid:staged",
]
PRIMARY = "inj:oracle_upper_bound_only"


def _arm_key(m: dict) -> str:
    return f"{m['arm']}:{m['signal']}{':staged' if m.get('staged') else ''}"


def _pstd(values: list[float]) -> float:
    mean = sum(values) / len(values)
    return math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))


def _judge(diffs: list[float]) -> dict:
    mean = sum(diffs) / len(diffs)
    pstd = _pstd(diffs)
    signs = [(x > 0) - (x < 0) for x in diffs]
    same_sign = len(set(signs)) == 1 and signs[0] != 0
    ratio = abs(mean) / pstd if pstd > 0 else float("inf")
    return {
        "diffs_by_seed": dict(zip(map(str, SEEDS), diffs)),
        "mean": mean,
        "pstd": pstd,
        "abs_mean_over_pstd": ratio,
        "signs": signs,
        "all_same_nonzero_sign": same_sign,
        "rule_satisfied": ratio >= 1.0 and same_sign,
        "direction": "positive" if mean > 0 else "negative" if mean < 0 else "zero",
    }


def main() -> None:
    acc = defaultdict(dict)  # arm -> seed -> phase_accuracy
    for d in sorted((ROOT / "experiments/phase1").glob("s4_grasp_injection_*")):
        p = d / "metrics.json"
        if not p.exists():
            continue
        m = json.loads(p.read_text())
        if m.get("task_id") != TASK:
            continue
        acc[_arm_key(m)][int(d.name.rsplit("seed", 1)[1])] = float(m["phase_accuracy"])

    assert all(len(acc[a]) == 10 for a in ARM_ORDER + ["ctrl:zeros"]), {
        a: len(acc[a]) for a in acc
    }
    ctrl = acc["ctrl:zeros"]

    arms = {}
    for arm in ARM_ORDER:
        diffs = [acc[arm][s] - ctrl[s] for s in SEEDS]
        arms[arm] = _judge(diffs)
        arms[arm]["arm_mean_accuracy"] = sum(acc[arm].values()) / 10
    ctrl_mean = sum(ctrl.values()) / 10

    # 前の実験の再現（同じ三つの種に限る）。
    rep_diffs = [acc["inj:predicted_sigmoid"][s] - ctrl[s] for s in (42, 123, 456)]
    reproduction = _judge_subset = {
        "diffs_by_seed": dict(zip(("42", "123", "456"), rep_diffs)),
        "mean": sum(rep_diffs) / 3,
        "pstd": _pstd(rep_diffs),
        "prior": PRIOR,
        "mean_delta_vs_prior": sum(rep_diffs) / 3 - PRIOR["mean"],
    }

    # 達成された検出できる下限。前の電力契約と同じ式:
    #   n 本の対の平均の揺らぎ SE = σ_d / √n、「二倍の揺らぎを超えて捉える」= Δ ≥ 2·SE
    #   Δ_min = 2 σ_d / √n
    sigma_d = arms[PRIMARY]["pstd"]
    sigma_d_all = {a: arms[a]["pstd"] for a in ARM_ORDER}
    mde = {
        "formula": "Δ_min = 2 * σ_d / sqrt(n)   （n=10、σ_d は各腕の対の差の母標準偏差）",
        "n": 10,
        "primary_sigma_d": sigma_d,
        "primary_mde": 2 * sigma_d / math.sqrt(10),
        "per_arm": {a: 2 * s / math.sqrt(10) for a, s in sigma_d_all.items()},
        "prior_3seed_reference": "前の実験（3 種）は 0.010 級",
    }

    result = {
        "task_id": TASK,
        "primary_arm": PRIMARY,
        "primary_note": "上限測定専用。成果として報告してはならない。機構の可否のみを判定する",
        "ctrl_mean_accuracy": ctrl_mean,
        "primary": arms[PRIMARY],
        "exploratory_note": "従たる四つは探索。四つを同時に見るため、たまたま条件を満たすものが出やすい",
        "exploratory": {a: arms[a] for a in ARM_ORDER if a != PRIMARY},
        "reproduction_of_prior": reproduction,
        "detectable_minimum": mde,
    }
    (AUDIT / "sweep.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"記録: {AUDIT / 'sweep.json'}")
    print(f"無情報な腕の平均 accuracy = {ctrl_mean:.7f}")
    print()
    print(f"{'腕':<34}{'差の平均':>12}{'pstd':>11}{'比':>8}{'同符号':>7}{'判定':>7}")
    for a in ARM_ORDER:
        j = arms[a]
        mark = "★主たる腕（上限専用）" if a == PRIMARY else "（探索）"
        print(f"{a:<34}{j['mean']:>+12.7f}{j['pstd']:>11.7f}{j['abs_mean_over_pstd']:>8.3f}"
              f"{str(j['all_same_nonzero_sign']):>7}{str(j['rule_satisfied']):>7}  {mark}")
    print()
    r = reproduction
    print(f"再現（42/123/456 の inferred）: 平均 {r['mean']:+.7f}  前回 {PRIOR['mean']:+.7f}"
          f"  差 {r['mean_delta_vs_prior']:+.7f}")
    print(f"達成された下限（主たる腕）: {mde['primary_mde']:.7f}")


if __name__ == "__main__":
    main()

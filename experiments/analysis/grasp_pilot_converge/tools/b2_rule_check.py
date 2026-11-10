"""Task B-2 収束規則の対照（T-2026-11-09-grasp-pilot-converge、SPEC §3.1・Task B-2）。本体の .venv。GPU を使わない。

dp_train.ConvergeRule（学習が通る同じ実装）に人工の val の記録を流し、学習率を落とす epoch と打ち切る epoch を確かめる。
上限は学習側と同じ CONVERGE["max_epochs"]（打ち切りが無ければ上限まで走る）。

    1 改善しない記録（一定）               → 8 epoch 後（epoch 9）に落とし、さらに 8 epoch 後（epoch 17）に止まる
    2 改善し続ける記録（+1e-3 ずつ）        → 落とさず止まらず上限 120 まで
    3 最良から min_delta 未満の揺れ（0.7 と 0.70005 の交互） → 改善と数えず 1 と同じ（9・17）
    3b 累積で上がる記録（+5e-5 ずつ）     → 最良から 1e-4 を超えるたびに改善と数え、上限まで（最初に書いた期待 9・17 は誤り）
    4 落とした後に改善が来る記録           → 改善で数え直し、そこから 8 epoch 後に止まる
    5 陰性対照: patience を 1 ずらした規則  → 1 の epoch がずれる（規則の値を読んでいることの確かめ）

    .venv/bin/python b2_rule_check.py --out <S>/b/b2_rule.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from stage2pilot import dp_train as D  # noqa: E402


def trace(scores, rule=None):
    rule = rule or D.ConvergeRule()
    drop = stop = None
    for epoch, sc in enumerate(scores[:D.CONVERGE["max_epochs"]], start=1):
        _, action = rule.step(sc)
        if action == "drop":
            drop = epoch
        elif action == "stop":
            stop = epoch
            break
    return {"drop_epoch": drop, "stop_epoch": stop, "epochs_run": stop or min(len(scores), D.CONVERGE["max_epochs"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    n = 200
    cases = {
        "1_constant": [0.7] * n,
        "2_increasing_1e-3": [0.5 + 1e-3 * i for i in range(n)],
        "3_jitter_below_min_delta": [0.7 + 5e-5 * (i % 2) for i in range(n)],
        "3b_drift_5e-5": [0.5 + 5e-5 * i for i in range(n)],
        "4_improve_after_drop": [0.7] * 11 + [0.71] + [0.71] * (n - 12),
    }
    expect = {"1_constant": (9, 17), "2_increasing_1e-3": (None, None), "3_jitter_below_min_delta": (9, 17), "3b_drift_5e-5": (None, None),
              "4_improve_after_drop": (9, 20)}
    out = {"task_id": "T-2026-11-09-grasp-pilot-converge", "converge": D.CONVERGE, "cases": {}}
    for k, sc in cases.items():
        t = trace(sc)
        t["expected_drop_stop"] = list(expect[k])
        t["as_expected"] = (t["drop_epoch"], t["stop_epoch"]) == expect[k]
        out["cases"][k] = t
    out["cases"]["2_increasing_1e-3"]["reaches_cap"] = out["cases"]["2_increasing_1e-3"]["epochs_run"] == D.CONVERGE["max_epochs"]
    neg = trace(cases["1_constant"], D.ConvergeRule(patience=D.CONVERGE["patience"] + 1))
    out["negative_control_patience_plus1"] = {**neg, "differs_from_case1": (neg["drop_epoch"], neg["stop_epoch"]) != expect["1_constant"]}
    out["all_as_expected"] = all(v["as_expected"] for v in out["cases"].values())
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

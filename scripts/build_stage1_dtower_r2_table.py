#!/usr/bin/env python
"""二周目の結果表を作る。契約 T-2026-09-19-stage1-detector-towers-r2 / Task D-2〜D-5。

**数値は評価の出力と学習の記録からしか取らない。** 手で書かない。

    val / test の mAP と per-class AP  : experiments/baselines/stage1_dtower{,_r2}/<run>/eval_{val,test}.json
    低下・打ち切り・最良 epoch          : experiments/baselines/stage1_dtower_r2/<run>/work/convergence.json
    壁時計                              : start.txt / end.txt

一周目の値は同じ評価 recipe（eval_relation_detr_map.py）の出力を並置する。
**標的群 AP は集合の定義が repo に無いため UNKNOWN**（利用者の決定 2026-09-25）。
代わりに全 15 クラスの per-class AP と AP_rare / AP_common を出す。

出力: experiments/baselines/stage1_dtower_r2/results_table.md と results.json
"""
from __future__ import annotations

import json
import math
import statistics
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
R1 = REPO / "experiments/baselines/stage1_dtower"
R2 = REPO / "experiments/baselines/stage1_dtower_r2"
RARE = {"Skewer", "Syringe"}
RUNS = [(t, f, s) for t in ("coco", "imagenet")
        for f, s in [("A", 42), ("A", 123), ("A", 456), ("B", 42), ("C", 42), ("D", 42), ("E", 42)]]
FMT = "%Y-%m-%d %H:%M:%S UTC"
UNKNOWN = "UNKNOWN"


def load(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def group_ap(per_class: dict | None, names: set[str]) -> float | None:
    if per_class is None:
        return None
    vals = [v for k, v in per_class.items() if k in names and not math.isnan(v)]
    return sum(vals) / len(vals) if vals else None


def f4(x) -> str:
    return UNKNOWN if x is None else f"{x:.4f}"


def sgn(x) -> str:
    return UNKNOWN if x is None else f"{x:+.4f}"


def wall_hours(d: Path) -> float | None:
    try:
        s = datetime.strptime((d / "start.txt").read_text().strip(), FMT)
        e = datetime.strptime((d / "end.txt").read_text().strip(), FMT)
    except (FileNotFoundError, ValueError):
        return None
    return (e - s).total_seconds() / 3600


def main() -> None:
    rows = []
    for tower, fold, seed in RUNS:
        name = f"d{tower}_fold{fold}_seed{seed}"
        v1, v2 = load(R1 / name / "eval_val.json"), load(R2 / name / "eval_val.json")
        t1, t2 = load(R1 / name / "eval_test.json"), load(R2 / name / "eval_test.json")
        conv = load(R2 / name / "work" / "convergence.json") or {}
        all_names = set((v2 or v1 or {}).get("per_class_ap", {}))
        rows.append({
            "run": name, "tower": "D*-COCO" if tower == "coco" else "D*-ImageNet",
            "fold": fold, "seed": seed,
            "val_map_r1": v1["AP"] if v1 else None, "val_map_r2": v2["AP"] if v2 else None,
            "ap_rare_r1": group_ap(v1 and v1["per_class_ap"], RARE),
            "ap_rare_r2": group_ap(v2 and v2["per_class_ap"], RARE),
            "ap_common_r1": group_ap(v1 and v1["per_class_ap"], all_names - RARE),
            "ap_common_r2": group_ap(v2 and v2["per_class_ap"], all_names - RARE),
            "ap_target_group": UNKNOWN,
            "test_map_r1": t1["AP"] if t1 else None, "test_map_r2": t2["AP"] if t2 else None,
            "per_class_ap_r2": (v2 or {}).get("per_class_ap"),
            "per_class_ap_r1": (v1 or {}).get("per_class_ap"),
            "decayed_epoch": conv.get("decayed_epoch"), "stopped_epoch": conv.get("stopped_epoch"),
            "best_epoch": conv.get("best_epoch"), "observed_epochs": conv.get("observed_epochs"),
            "reached_cap": conv.get("stopped_epoch") is None if conv else None,
            "train_best_val_map_r2": conv.get("best_ap"),
            "wall_hours": wall_hours(R2 / name),
        })

    def vals(tower, key, folds="ABCDE", seeds=(42,)):
        return [r[key] for r in rows if r["tower"] == tower and r["fold"] in folds
                and r["seed"] in seeds and r[key] is not None]

    def mean_sd(xs):
        if not xs:
            return None, None
        return statistics.mean(xs), (statistics.stdev(xs) if len(xs) > 1 else 0.0)

    agg = {}
    for rnd in ("r1", "r2"):
        k = f"val_map_{rnd}"
        c, cs = mean_sd(vals("D*-COCO", k, "A", (42, 123, 456)))
        i, is_ = mean_sd(vals("D*-ImageNet", k, "A", (42, 123, 456)))
        gaps = {}
        for f in "ABCDE":
            a = vals("D*-COCO", k, f)
            b = vals("D*-ImageNet", k, f)
            gaps[f] = (a[0] - b[0]) if a and b else None
        g = [v for v in gaps.values() if v is not None]
        agg[rnd] = {"foldA_coco_mean": c, "foldA_coco_sd": cs, "foldA_imagenet_mean": i,
                    "foldA_imagenet_sd": is_, "foldA_gap": (c - i) if c is not None and i is not None else None,
                    "gap_per_fold_seed42": gaps, "gap_mean_5folds": (sum(g) / len(g)) if g else None}
    gains = {}
    for tower in ("D*-COCO", "D*-ImageNet"):
        g = [r["val_map_r2"] - r["val_map_r1"] for r in rows
             if r["tower"] == tower and r["val_map_r1"] is not None and r["val_map_r2"] is not None]
        gains[tower] = {"n": len(g), "mean": (sum(g) / len(g)) if g else None,
                        "min": min(g) if g else None, "max": max(g) if g else None}
    caps = {t: sum(1 for r in rows if r["tower"] == t and r["reached_cap"]) for t in ("D*-COCO", "D*-ImageNet")}
    no_decay_cap = {t: sum(1 for r in rows if r["tower"] == t and r["reached_cap"] and r["decayed_epoch"] is None)
                    for t in ("D*-COCO", "D*-ImageNet")}
    n_test_r2 = sum(1 for r in rows if r["test_map_r2"] is not None)

    def epoch_range(tower, key):
        xs = [r[key] for r in rows if r["tower"] == tower and r[key] is not None]
        return f"{min(xs)}〜{max(xs)}" if xs else UNKNOWN

    # ---- prereg §4 の予測の判定（機械的に出せるものだけ。解釈は RESULT で行う） ----
    a1 = agg["r1"]
    a2 = agg["r2"]
    preds = {
        "1 D*-ImageNet は一周目より上がる": {
            "measured": f"折り A 3 seed の平均 {f4(a1['foldA_imagenet_mean'])} → {f4(a2['foldA_imagenet_mean'])}、"
                        f"7 run の上がり幅 平均 {sgn(gains['D*-ImageNet']['mean'])}",
        },
        "2 両塔の差は縮むが零にならない": {
            "measured": f"折り A の差 {f4(a1['foldA_gap'])} → {f4(a2['foldA_gap'])}、"
                        f"5 折りの差の平均 {f4(a1['gap_mean_5folds'])} → {f4(a2['gap_mean_5folds'])}",
        },
        "3 D*-COCO は一周目と同程度（±1 mAP）": {
            "measured": f"7 run の上がり幅 平均 {sgn(gains['D*-COCO']['mean'])}、範囲 "
                        f"{sgn(gains['D*-COCO']['min'])}〜{sgn(gains['D*-COCO']['max'])}",
        },
        "4 D*-ImageNet の低下と打ち切りは D*-COCO より遅い": {
            "measured": "低下 COCO {} / ImageNet {}、打ち切り COCO {} / ImageNet {}".format(
                *[epoch_range(t, k) for k in ("decayed_epoch", "stopped_epoch")
                  for t in ("D*-COCO", "D*-ImageNet")]),
        },
        "5 折り B〜E は折り A より低い": {
            "measured": "COCO A {} / B〜E {}〜{}、ImageNet A {} / B〜E {}〜{}".format(
                f4(a2["foldA_coco_mean"]), f4(min(vals("D*-COCO", "val_map_r2", "BCDE") or [None])),
                f4(max(vals("D*-COCO", "val_map_r2", "BCDE") or [None])),
                f4(a2["foldA_imagenet_mean"]), f4(min(vals("D*-ImageNet", "val_map_r2", "BCDE") or [None])),
                f4(max(vals("D*-ImageNet", "val_map_r2", "BCDE") or [None]))),
        },
    }

    out = {"rows": rows, "aggregates": agg, "gains": gains, "reached_cap": caps,
           "reached_cap_without_decay": no_decay_cap, "n_test_evals_r2": n_test_r2, "predictions": preds}
    (R2 / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    md = ["# 二周目の結果表 — T-2026-09-19-stage1-detector-towers-r2", "",
          "値は評価 recipe（`eval_relation_detr_map.py`、NMS-free）の出力。一周目は同じ recipe の `eval_val.json`。",
          "**標的群 AP は集合の定義が repo に無いため UNKNOWN**（全 15 クラスの per-class AP を下に置く）。", "",
          "## 塔 × 折り × seed（完了判定 c・d・e・f）", "",
          "| run | val mAP 一周目 | val mAP 二周目 | 上がり幅 | AP_rare 一周目 | AP_rare 二周目 | AP_common 二周目 | 標的群 | test 一周目 | test 二周目 | 低下 | 打ち切り | 最良 | epoch 数 | 壁時計 h |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        gain = (r["val_map_r2"] - r["val_map_r1"]) if r["val_map_r1"] is not None and r["val_map_r2"] is not None else None
        md.append("| {run} | {v1} | {v2} | {g} | {r1} | {r2} | {c2} | {tg} | {t1} | {t2} | {d} | {s} | {b} | {n} | {w} |".format(
            run=r["run"], v1=f4(r["val_map_r1"]), v2=f4(r["val_map_r2"]), g=sgn(gain),
            r1=f4(r["ap_rare_r1"]), r2=f4(r["ap_rare_r2"]), c2=f4(r["ap_common_r2"]), tg=UNKNOWN,
            t1=f4(r["test_map_r1"]) if r["test_map_r1"] is not None else "—",
            t2=f4(r["test_map_r2"]) if r["test_map_r2"] is not None else "—",
            d=r["decayed_epoch"], s=r["stopped_epoch"] if r["stopped_epoch"] is not None else "上限",
            b=r["best_epoch"], n=r["observed_epochs"],
            w=f"{r['wall_hours']:.2f}" if r["wall_hours"] is not None else UNKNOWN))
    md += ["", f"行数 {len(rows)}。test 二周目の評価回数 **{n_test_r2}**（両塔 × 5 折り、折り A は seed 42）。", "",
           "## 折り A（3 seed）と塔間の差", "",
           "| | 一周目 | 二周目 |", "|---|---|---|"]
    for label, key in (("D*-COCO 平均 (SD)", "coco"), ("D*-ImageNet 平均 (SD)", "imagenet")):
        md.append(f"| {label} | {f4(a1[f'foldA_{key}_mean'])} ({f4(a1[f'foldA_{key}_sd'])}) | {f4(a2[f'foldA_{key}_mean'])} ({f4(a2[f'foldA_{key}_sd'])}) |")
    md.append(f"| 差（COCO − ImageNet） | **{f4(a1['foldA_gap'])}** | **{f4(a2['foldA_gap'])}** |")
    md += ["", "| 折り（seed 42）の差 | 一周目 | 二周目 |", "|---|---|---|"]
    for f in "ABCDE":
        md.append(f"| {f} | {sgn(a1['gap_per_fold_seed42'][f])} | {sgn(a2['gap_per_fold_seed42'][f])} |")
    md.append(f"| 平均 | {sgn(a1['gap_mean_5folds'])} | {sgn(a2['gap_mean_5folds'])} |")
    md += ["", "## 上がり幅（塔ごと、7 run）", "", "| 塔 | n | 平均 | 最小 | 最大 |", "|---|---|---|---|---|"]
    for t, g in gains.items():
        md.append(f"| {t} | {g['n']} | {sgn(g['mean'])} | {sgn(g['min'])} | {sgn(g['max'])} |")
    md += ["", "## 上限 36 に達した run（完了判定 e）", "",
           "| 塔 | 上限到達 | うち低下を受けずに到達 |", "|---|---|---|"]
    for t in caps:
        md.append(f"| {t} | {caps[t]} | {no_decay_cap[t]} |")
    md += ["", "## prereg §4 の予測（実測。当たり外れの解釈は RESULT）", "", "| 予測 | 実測 |", "|---|---|"]
    for k, v in preds.items():
        md.append(f"| {k} | {v['measured']} |")
    names = sorted(set().union(*[set(r["per_class_ap_r2"] or {}) for r in rows]))
    if names:
        md += ["", "## per-class AP（val、二周目）", "", "| run | " + " | ".join(names) + " |",
               "|---|" + "---|" * len(names)]
        for r in rows:
            pc = r["per_class_ap_r2"] or {}
            md.append(f"| {r['run']} | " + " | ".join(
                ("NaN" if math.isnan(pc[n]) else f"{pc[n]:.3f}") if n in pc else UNKNOWN for n in names) + " |")
    (R2 / "results_table.md").write_text("\n".join(md) + "\n")
    print(f"行数 {len(rows)} / val 二周目 {sum(1 for r in rows if r['val_map_r2'] is not None)} / test 二周目 {n_test_r2}")
    print(f"折り A の差: 一周目 {f4(a1['foldA_gap'])} → 二周目 {f4(a2['foldA_gap'])}")


if __name__ == "__main__":
    main()

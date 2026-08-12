#!/usr/bin/env python3
"""report_detector_results.py — 検出器ベンチの集計表を metrics.json 直読みで機械生成。

背景(lessons.md E1): Slack 報告で平均値を手打ちして誤記した事故の再発防止。
本スクリプトの stdout を**そのまま**貼ることで、手打ち・暗算・記憶からの転記を根絶する。

experiments/baselines/ 配下の s0_*/metrics.json を検出器ごとにグルーピングし、
mAP / AP_rare / AP_common / mAP_50 の mean±std (母標準偏差) を算出する。
全て metrics.json の生値から計算。手打ち介入の余地なし。

Usage:
  python scripts/report_detector_results.py                # 全検出器
  python scripts/report_detector_results.py --markdown     # Slack/md 貼り付け用
  python scripts/report_detector_results.py --group ddq    # 特定検出器のみ
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import statistics as st
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE = REPO_ROOT / "experiments" / "baselines"

# 検出器名(フォルダ中の識別子) -> 表示名。順序は表示順。
DETECTORS = [
    ("maskdino_bbox", "Mask DINO"),
    ("varifocanet_bbox", "VFNet"),
    ("codetr_bbox", "Co-DETR"),
    ("ddq_bbox", "DDQ-DETR"),
    ("stabledino_bbox", "Stable-DINO"),
    ("relationdetr_bbox", "Relation-DETR"),
    ("dimaskdino_bbox", "DI-MaskDINO"),
    ("sensex_codino_bbox", "Sense-X Co-DINO 9enc"),
    ("focusdetr_bbox", "Focus-DETR"),
    ("aligndetr_bbox", "Align-DETR"),
    ("mrdetrdino_bbox", "Mr.DETR-DINO"),
    ("mrdetralign_bbox", "Mr.DETR-Align"),
    ("dacdetr_bbox", "DAC-DETR"),
]


def _collect(group_filter: str | None):
    rows = {}
    for key, disp in DETECTORS:
        if group_filter and group_filter not in key:
            continue
        # key の前に必ず "_" を要求 (フォルダは s0_NNN_<key>_seedX)。
        # これにより "maskdino_bbox" が "dimaskdino_bbox" を部分一致で誤って拾う問題を防ぐ。
        dirs = sorted(
            d for d in glob.glob(str(BASE / f"s0_*_{key}*"))
            if os.path.isfile(os.path.join(d, "metrics.json"))
        )
        seeds = []
        for d in dirs:
            try:
                m = json.loads(Path(d, "metrics.json").read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            mp = m.get("val/mAP", m.get("mAP"))
            if not isinstance(mp, (int, float)):
                continue
            seed = None
            mm = re.search(r"seed(\d+)", os.path.basename(d))
            if mm:
                seed = int(mm.group(1))
            seeds.append({
                "dir": os.path.basename(d),
                "seed": seed,
                "mAP": mp,
                "AP_rare": m.get("val/AP_rare"),
                "AP_common": m.get("val/AP_common"),
                "mAP_50": m.get("val/mAP_50"),
            })
        if seeds:
            rows[disp] = seeds
    return rows


def _agg(vals):
    clean = [v for v in vals if isinstance(v, (int, float))]
    if not clean:
        return None, None
    mean = st.mean(clean)
    std = st.pstdev(clean) if len(clean) > 1 else 0.0
    return mean, std


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default=None)
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args()

    rows = _collect(args.group)
    if not rows:
        print("(該当する完了済み実験が見つかりません)")
        return 1

    # 集計
    summary = []
    for disp, seeds in rows.items():
        maps = [s["mAP"] for s in seeds]
        mean, std = _agg(maps)
        rare_m, _ = _agg([s["AP_rare"] for s in seeds])
        com_m, _ = _agg([s["AP_common"] for s in seeds])
        m50_m, _ = _agg([s["mAP_50"] for s in seeds])
        summary.append({
            "det": disp, "n": len(seeds), "mAP_mean": mean, "mAP_std": std,
            "rare": rare_m, "common": com_m, "m50": m50_m,
            "vals": [s["mAP"] for s in sorted(seeds, key=lambda x: (x["seed"] or 0))],
        })
    # mAP 降順
    summary.sort(key=lambda r: r["mAP_mean"], reverse=True)

    if args.markdown:
        print("| 順位 | 検出器 | n | mAP | AP_rare | AP_common | mAP_50 |")
        print("|---|---|---|---|---|---|---|")
        for i, r in enumerate(summary, 1):
            vals = "/".join(f"{v:.3f}" for v in r["vals"])
            rare = f"{r['rare']:.4f}" if r["rare"] is not None else "n/a"
            com = f"{r['common']:.4f}" if r["common"] is not None else "n/a"
            m50 = f"{r['m50']:.4f}" if r["m50"] is not None else "n/a"
            print(f"| {i} | {r['det']} | {r['n']} | "
                  f"{r['mAP_mean']:.4f}±{r['mAP_std']:.4f} ({vals}) | {rare} | {com} | {m50} |")
    else:
        print("=== 検出器ベンチ集計 (metrics.json 直読み, 手打ち介入なし) ===\n")
        for i, r in enumerate(summary, 1):
            vals = "/".join(f"{v:.4f}" for v in r["vals"])
            print(f"{i}. {r['det']} ({r['n']} seed)")
            print(f"   mAP       = {r['mAP_mean']:.4f} ± {r['mAP_std']:.4f}  ({vals})")
            if r["rare"] is not None:
                print(f"   AP_rare   = {r['rare']:.4f}")
            if r["common"] is not None:
                print(f"   AP_common = {r['common']:.4f}")
            if r["m50"] is not None:
                print(f"   mAP_50    = {r['m50']:.4f}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

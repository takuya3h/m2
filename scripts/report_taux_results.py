#!/usr/bin/env python3
"""report_taux_results.py — 系統② region-token 補助→工程（taux_*）の Δ_phase 集計を機械生成。

`experiments/transfer/taux_*` の metrics.json を直読みし、手法(step tag)×seed で
phase_accuracy / phase_macro_f1 を集めて per-seed Δ（vs S4 base acc 0.8986 / macro-F1 0.709）
を計算、手法ごとに mean(Δ)・母標準偏差 σ(=statistics.pstdev)・|mean|/σ・全seed同符号 を出し、
paired-σ 判定(§10.1: |mean|>σ かつ 同符号 で ✓)を付けた markdown 表を
`experiments/analysis/taux/REPORT.md` に書き出す。

集計本体は `egosurgery.utils.transfer_delta_report`（haux 版と共有・判定式は 1 箇所）。
背景(lessons.md E1): 平均値の手打ち誤記の再発防止。stdout / REPORT.md をそのまま貼る。

Usage:
  .venv/bin/python scripts/report_taux_results.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.utils.transfer_delta_report import build_report  # noqa: E402


def main() -> int:
    build_report(
        family_prefix="taux",
        aux_label="region-token 補助→工程（系統② det→phase・②特徴レベル / T1a 系）",
        transfer_dir=PROJ / "experiments" / "transfer",
        out_path=PROJ / "experiments" / "analysis" / "taux" / "REPORT.md",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

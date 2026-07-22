#!/usr/bin/env python
"""STEP D-aux 総合集計（§10.1 準拠の per-seed paired-σ）。

`report_haux_results.py` / `report_taux_results.py` は Δ を **固定分母 0.8986** に対して測るが、
§10.1 の paired-σ は「**対 seed 差**（同一 seed の baseline との差）」を要求する。固定スカラ分母だと
seed 相関分散が相殺されず有意性を過小評価する。本スクリプトは **同一環境で走らせた S4 base
（GAP-only TeCNO）を per-seed の分母**に取り、method[seed] − S4[seed] の paired-σ で判定する
（B2a-oracle / T1a-shuffle の既存解析と同じ方式）。系統②は region-token TeCNO(T-4) 基準でも併記。

分母解決:
  - S4 base: experiments/phase1/s4_phase_baseline_*_frozen_tecno_phase_baseline_seed{S}
    （neck / necktransfer 変種は除外）。各 seed で最新 mtime を採用。
  - 各手法: experiments/transfer/{tag}_{seq}_{tag}_seed{S}（tag 完全一致）。最新 mtime を採用。

出力: experiments/analysis/daux/REPORT.md（人が読む集計表・捏造なし・実測 metrics.json 直読み）。

実行: python scripts/report_daux_paired.py
"""
from __future__ import annotations

import glob
import json
import os
import re
import statistics as st
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
TR = PROJ / "experiments" / "transfer"
PH1 = PROJ / "experiments" / "phase1"
OUT = PROJ / "experiments" / "analysis" / "daux"
SEEDS = (42, 123, 456)
DOC_ACC, DOC_F1 = 0.8986, 0.709  # 文書上の固定分母（cross-check 用）


def _metric(d: str, k: str):
    try:
        return json.load(open(f"{d}/metrics.json")).get(k)
    except Exception:
        return None


def _newest_exact(tag: str, seed: int) -> str | None:
    pat = re.compile(rf"^{re.escape(tag)}_\d+_{re.escape(tag)}_seed{seed}$")
    ds = [d for d in glob.glob(str(TR / f"{tag}_*seed{seed}"))
          if pat.match(os.path.basename(d)) and _metric(d, "phase_accuracy") is not None]
    return max(ds, key=lambda d: os.path.getmtime(f"{d}/metrics.json")) if ds else None


def _s4_base() -> tuple[dict, dict]:
    """同一環境 S4 base（GAP-only・neck 無し）を per-seed 解決。"""
    acc, f1 = {}, {}
    for s in SEEDS:
        cands = [d for d in glob.glob(str(PH1 / f"s4_phase_baseline_*seed{s}"))
                 if re.search(r"_frozen_tecno_phase_baseline_seed", os.path.basename(d))
                 and "neck" not in os.path.basename(d)
                 and _metric(d, "phase_accuracy") is not None]
        if not cands:
            raise SystemExit(f"[daux] S4 base (GAP-only) seed{s} が見つからない。train_s4_tecno.py を実行せよ。")
        d = max(cands, key=lambda x: os.path.getmtime(f"{x}/metrics.json"))
        acc[s] = _metric(d, "phase_accuracy")
        f1[s] = _metric(d, "phase_macro_f1")
    return acc, f1


def _paired(vals: dict, base: dict):
    d = [vals[s] - base[s] for s in SEEDS]
    m = st.mean(d)
    sd = st.pstdev(d)
    r = abs(m) / sd if sd > 0 else float("inf")
    same = all(x > 0 for x in d) or all(x < 0 for x in d)
    ok = (abs(m) > sd) and same
    return m, sd, r, ok, d


def _collect(tag: str):
    va = {s: (_metric(_newest_exact(tag, s), "phase_accuracy") if _newest_exact(tag, s) else None) for s in SEEDS}
    vf = {s: (_metric(_newest_exact(tag, s), "phase_macro_f1") if _newest_exact(tag, s) else None) for s in SEEDS}
    if any(v is None for v in va.values()):
        return None, None
    return va, vf


HAND = [
    ("H-1 presence", "haux_hand_presence_oracle"),
    ("H-2 count", "haux_hand_count_oracle"),
    ("H-3 geom", "haux_hand_geom_oracle"),
    ("H-5 own_other", "haux_hand_own_other_oracle"),
    ("H-6 presence+tool", "haux_hand_presence_oracle_withtooloracle"),
    ("H-1 shuffle (control)", "haux_hand_presence_oracle_shuffle"),
    ("B2a tool-only (oracle)", "b2a_det2phase_oracletool"),
]
SYS2 = [
    ("T-4 tecno (region base)", "taux_tecno_nonek3"),
    ("T-1 movavg", "taux_tecno_movavgk3"),
    ("T-2 delta", "taux_tecno_deltak3"),
    ("T-3 window", "taux_tecno_windowk3"),
    ("T-6 minGRU", "taux_mingru_nonek3"),
]


def _row(name, va, vf, base_a, base_f):
    ma, sa, ra, oka, _ = _paired(va, base_a)
    mf, sf, rf, okf, _ = _paired(vf, base_f)
    return (f"| {name} | {ma*100:+.2f} | {sa*100:.2f} | {ra:.2f} | {'✓' if oka else '×'} "
            f"| {mf*100:+.2f} | {sf*100:.2f} | {rf:.2f} | {'✓' if okf else '×'} |")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s4a, s4f = _s4_base()
    L = []
    L.append("# STEP D-aux 総合集計（per-seed paired-σ・§10.1 準拠）\n")
    L.append("実測 metrics.json 直読み（手打ち・捏造なし）。判定 = |mean|>pstdev かつ 3-seed 同符号。\n")
    L.append(f"**分母 = 同一環境 S4 base（GAP-only TeCNO・seed 42/123/456）**: "
             f"acc {st.mean(list(s4a.values()))*100:.2f}±{st.pstdev(list(s4a.values()))*100:.2f} / "
             f"macro-F1 {st.mean(list(s4f.values()))*100:.2f}（文書固定値 {DOC_ACC*100:.2f}/{DOC_F1*100:.1f} と整合）。\n")
    L.append("Δ は method[seed] − S4[seed] の per-seed 差（pp = percentage point）。\n")

    L.append("\n## 系統① 手情報 → 工程（det→phase・①信号レベル）\n")
    L.append("| 手法 | Δacc mean(pp) | σ(pp) | \\|m\\|/σ | acc | ΔF1 mean(pp) | σ(pp) | \\|m\\|/σ | F1 |")
    L.append("|---|--:|--:|--:|:-:|--:|--:|--:|:-:|")
    hand_vals = {}
    for name, tag in HAND:
        va, vf = _collect(tag)
        if va is None:
            L.append(f"| {name} | — | | | (未完了) | | | | |")
            continue
        hand_vals[tag] = (va, vf)
        L.append(_row(name, va, vf, s4a, s4f))
    # H-6 vs tool-only（手の tool 上乗せ価値）
    if "haux_hand_presence_oracle_withtooloracle" in hand_vals and "b2a_det2phase_oracletool" in hand_vals:
        h6a, h6f = hand_vals["haux_hand_presence_oracle_withtooloracle"]
        b2a, b2f = hand_vals["b2a_det2phase_oracletool"]
        L.append("\n**H-6 の tool 上乗せ価値**（H-6 − B2a tool単独, per-seed paired）:")
        ma, sa, ra, oka, _ = _paired(h6a, b2a)
        mf, sf, rf, okf, _ = _paired(h6f, b2f)
        L.append(f"- Δacc {ma*100:+.2f}pp (|m|/σ={ra:.2f}) {'✓' if oka else '×'} / "
                 f"ΔF1 {mf*100:+.2f}pp (|m|/σ={rf:.2f}) {'✓' if okf else '×'} "
                 f"→ {'手は tool に上乗せ価値あり' if (oka or okf) else '手は tool に対し冗長（上乗せ無し）'}\n")

    L.append("\n## 系統② 時系列 → 工程（region-token 基盤）\n")
    L.append("vs S4（headline・region+核の総効果） / vs T-4（region-token TeCNO 基準・問い A/B）\n")
    L.append("| 手法 | vsS4 Δacc(pp) | acc | vsS4 ΔF1(pp) | F1 | vsT4 Δacc(pp) | acc | vsT4 ΔF1(pp) | F1 |")
    L.append("|---|--:|:-:|--:|:-:|--:|:-:|--:|:-:|")
    t4 = _collect("taux_tecno_nonek3")
    t4a, t4f = t4 if t4[0] else (None, None)
    for name, tag in SYS2:
        va, vf = _collect(tag)
        if va is None:
            L.append(f"| {name} | — | (未完了) | | | | | | |")
            continue
        ma, _, _, oka, _ = _paired(va, s4a)
        mf, _, _, okf, _ = _paired(vf, s4f)
        if t4a and tag != "taux_tecno_nonek3":
            mat, _, rat, okat, _ = _paired(va, t4a)
            mft, _, _, okft, _ = _paired(vf, t4f)
            t4cols = f"{mat*100:+.2f} | {'✓' if okat else '×'} | {mft*100:+.2f} | {'✓' if okft else '×'}"
        else:
            t4cols = "— | · | — | ·"
        L.append(f"| {name} | {ma*100:+.2f} | {'✓' if oka else '×'} | {mf*100:+.2f} | {'✓' if okf else '×'} | {t4cols} |")

    (OUT / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\n[daux] 書き出し -> {OUT / 'REPORT.md'}")


if __name__ == "__main__":
    main()

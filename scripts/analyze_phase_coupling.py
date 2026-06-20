#!/usr/bin/env python
"""②特徴レベル結合（C5 線形 neck）の per-phase 深掘り分析（STEP C）。

比較の三角形の Δ_phase 軸で、3系統を seed をそろえて分解する:

  S4   = base       … neck なし TeCNO（Δ_phase 分母）
  S4'  = neck       … 工程側で独立学習した neck を載せた TeCNO（容量効果の上限）
  S4'' = transfer   … 検出で学習し凍結した C5 neck を工程へ載せた TeCNO（真の一方向結合）

分解（共通 seed 上, seed-matched）:
  Δcap  = S4' - S4    … neck の容量（capacity）寄与
  Δxfer = S4'' - S4'  … 検出→工程の転移（transfer）寄与
  ΔL2   = S4'' - S4   … ②結合の総効果（capacity + transfer）

研究インテグリティ:
  - 数値は metrics.json / per_class_ap.json の実測のみ。捏造しない。
  - per-class は F1 のみ永続化（per_class_ap.json）。per-class Jaccard は
    predictions 未保存のため再計算不可 → 出さない。
  - base 3-seed（001/002/003, 06-16〜17）は jaccard 計装より前で phase_jaccard
    未永続化 → base 絡みの jaccard Δ は n/a と明示し、転移差(S4''-S4')のみ出す。
  - 改善主張は §10.1 に従い |Δ| > 1σ のときのみ。1σ は base 3-seed の標本(n-1)標準偏差。

実行: .venv/bin/python scripts/analyze_phase_coupling.py
"""
from __future__ import annotations

import json
import re
import statistics as st
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
PHASE_DIR = PROJ / "experiments/phase1"

# 集計スカラ（metrics.json のキー → 表示名）。accuracy/Jaccard/edit/seg-F1 を全部そろえる。
SCALARS = [
    ("phase_accuracy", "accuracy"),
    ("phase_macro_f1", "macro_f1"),
    ("phase_jaccard", "jaccard"),
    ("phase_edit_score", "edit"),
    ("phase_seg_f1_10", "seg_f1@10"),
    ("phase_seg_f1_25", "seg_f1@25"),
    ("phase_seg_f1_50", "seg_f1@50"),
]
# 0-1 の分率 → ×100 で pp 表示。edit のみ 0-100 の素値。
PCT = {"accuracy", "macro_f1", "jaccard", "seg_f1@10", "seg_f1@25", "seg_f1@50"}
ORDER = ["S4_base", "S4'_neck", "S4''_transfer"]


def system_of(name: str) -> str | None:
    if "necktransfer" in name:
        return "S4''_transfer"
    if "baseline_neck" in name:
        return "S4'_neck"
    if "phase_baseline_seed" in name:
        return "S4_base"
    return None


def seed_of(name: str) -> int | None:
    m = re.search(r"_seed(\d+)", name)
    return int(m.group(1)) if m else None


def load_runs() -> dict[str, dict[int, dict]]:
    """{system: {seed: {"scalars": {...}, "per_class": {...}, "dir": ...}}} を返す。"""
    runs: dict[str, dict[int, dict]] = {}
    for d in sorted(PHASE_DIR.glob("s4_phase_baseline_*")):
        sysname, seed = system_of(d.name), seed_of(d.name)
        if sysname is None or seed is None:
            continue
        m = json.load(open(d / "metrics.json"))
        pc_path = d / "per_class_ap.json"
        pc = json.load(open(pc_path)) if pc_path.exists() else {}
        runs.setdefault(sysname, {})[seed] = {
            "scalars": {k: m.get(k) for k, _ in SCALARS},
            "per_class": pc,
            "dir": d.name,
        }
    return runs


def scaled(sysname: str, seed: int, key: str, runs: dict, scale: float):
    v = runs[sysname][seed]["scalars"].get(key)
    return None if v is None else v * scale


def mean_std(vals: list) -> str:
    vals = [v for v in vals if v is not None]
    if not vals:
        return "n/a"
    mu = st.mean(vals)
    sd = st.stdev(vals) if len(vals) > 1 else 0.0
    return f"{mu:.2f}±{sd:.2f}"


def main() -> None:
    runs = load_runs()

    print("=" * 80)
    print("②特徴レベル結合 per-phase 分析  (Δ_phase 軸 / frozen backbone=Relation-DETR seed42)")
    print("=" * 80)
    for sysname in ORDER:
        seeds = sorted(runs.get(sysname, {}))
        print(f"\n[{sysname}]  seeds={seeds}  n={len(seeds)}")
        for s in seeds:
            print(f"    seed{s}: {runs[sysname][s]['dir']}")

    common = sorted(set.intersection(*[set(runs[s]) for s in ORDER if s in runs]))
    print(f"\n--- 共通 seed（3系統で揃う）: {common} ---")

    # === 1. 集計スカラ（フルセット）: 全 seed 平均±std ===
    print("\n[集計スカラ] mean±std  ※ pp=accuracy/macro_f1/jaccard/seg-F1(×100), edit=0-100素値")
    print(f'{"metric":<11}' + "".join(f"{s:<22}" for s in ORDER))
    for key, disp in SCALARS:
        scale = 100 if disp in PCT else 1
        row = f"{disp:<11}"
        for sysname in ORDER:
            seeds = sorted(runs.get(sysname, {}))
            row += f"{mean_std([scaled(sysname, s, key, runs, scale) for s in seeds]):<22}"
        print(row)

    # === 2. Δ 分解（共通 seed 上 seed-matched 差分） ===
    print(f"\n[Δ 分解] 共通 seed {common} 上 seed-matched 平均差")
    print("  Δcap = S4'-S4 (容量) | Δxfer = S4''-S4' (転移) | ΔL2 = S4''-S4 (総結合)")
    print("  ※ matched 差の有意性は base群σ でなく対seed差σ(paired) で判定（符号反転の見落とし防止）")
    print(f'\n  {"metric":<11}{"Δcap":>9}{"Δxfer":>9}{"ΔL2(paired)":>16}{"base1σ":>8}  判定')

    def matched(sysname: str, key: str, scale: float):
        vals = [scaled(sysname, s, key, runs, scale) for s in common]
        return None if any(v is None for v in vals) else st.mean(vals)

    def paired(sys_a: str, sys_b: str, key: str, scale: float):
        """共通 seed 上の対応差 (sys_a−sys_b) のリスト。欠測があれば None。"""
        out = []
        for s in common:
            a = scaled(sys_a, s, key, runs, scale)
            b = scaled(sys_b, s, key, runs, scale)
            if a is None or b is None:
                return None
            out.append(a - b)
        return out

    def diff(a, b):
        return None if a is None or b is None else a - b

    def show(x):
        return "n/a" if x is None else f"{x:+.2f}"

    for key, disp in SCALARS:
        scale = 100 if disp in PCT else 1
        base_vals = [scaled("S4_base", s, key, runs, scale) for s in sorted(runs["S4_base"])]
        base_vals = [v for v in base_vals if v is not None]
        base_sd = st.stdev(base_vals) if len(base_vals) > 1 else None
        dcap = diff(matched("S4'_neck", key, scale), matched("S4_base", key, scale))
        dxfer = diff(matched("S4''_transfer", key, scale), matched("S4'_neck", key, scale))
        pl2 = paired("S4''_transfer", "S4_base", key, scale)  # ΔL2 を対応差で評価
        if pl2 is None:
            dl2_s, verdict = "n/a", "n/a(base欠測)"
        else:
            mu = st.mean(pl2)
            psd = st.stdev(pl2) if len(pl2) > 1 else 0.0
            dl2_s = f"{mu:+.2f}±{psd:.2f}"
            # 対応差: |平均| > paired1σ かつ 全 seed 同符号 のときのみ有意。
            same_sign = all(d > 0 for d in pl2) or all(d < 0 for d in pl2)
            if abs(mu) > psd and same_sign:
                verdict = "有意(改善)" if mu > 0 else "有意(悪化)"
            else:
                verdict = "中立"
        bsd = "n/a" if base_sd is None else f"{base_sd:.2f}"
        print(f"  {disp:<11}{show(dcap):>9}{show(dxfer):>9}{dl2_s:>16}{bsd:>8}  {verdict}")

    # === 3. per-phase F1 分解（共通 seed 上） ===
    if not runs["S4_base"][common[0]]["per_class"]:
        print("\n[per-phase] base に per_class_ap.json なし → スキップ")
        return
    phases = sorted(runs["S4_base"][common[0]]["per_class"])
    print(f"\n[per-phase F1] 共通 seed {common} 平均 (×100) と Δ 分解")
    print(f'  {"phase":<14}{"S4":>8}{"S4’":>8}{"S4’’":>8}{"Δcap":>8}{"Δxfer":>8}{"ΔL2":>8}')

    def pc_mean(sysname: str, ph: str) -> float:
        return st.mean(runs[sysname][s]["per_class"][ph] for s in common) * 100

    rows = []
    for ph in phases:
        s4, s4n, s4t = pc_mean("S4_base", ph), pc_mean("S4'_neck", ph), pc_mean("S4''_transfer", ph)
        rows.append((ph, s4, s4n, s4t, s4n - s4, s4t - s4n, s4t - s4))
    for ph, s4, s4n, s4t, dcap, dxfer, dl2 in rows:
        print(f"  {ph:<14}{s4:>8.2f}{s4n:>8.2f}{s4t:>8.2f}{dcap:>+8.2f}{dxfer:>+8.2f}{dl2:>+8.2f}")
    macro = [st.mean(r[i] for r in rows) for i in range(1, 7)]
    print(f'  {"MACRO(平均)":<12}{macro[0]:>8.2f}{macro[1]:>8.2f}{macro[2]:>8.2f}'
          f"{macro[3]:>+8.2f}{macro[4]:>+8.2f}{macro[5]:>+8.2f}")

    # === 4. 機構の要約 ===
    print("\n[機構の要約]")
    cap_sorted = sorted(rows, key=lambda r: r[4], reverse=True)
    xfer_sorted = sorted(rows, key=lambda r: r[5])
    print("  容量(Δcap) が効いた工程 上位:", ", ".join(f"{r[0]}({r[4]:+.1f})" for r in cap_sorted[:3]))
    print("  容量(Δcap) が逆効果の工程  :", ", ".join(f"{r[0]}({r[4]:+.1f})" for r in cap_sorted[-2:]))
    print("  転移(Δxfer) で最も壊れた工程:", ", ".join(f"{r[0]}({r[5]:+.1f})" for r in xfer_sorted[:3]))
    print("  転移(Δxfer) で耐えた/改善工程:", ", ".join(f"{r[0]}({r[5]:+.1f})" for r in xfer_sorted[-2:]))
    print("\n  ※ per-phase は F1 のみ（per_class_ap.json）。per-class Jaccard は")
    print("    predictions 未保存のため再計算不可。base の集計 Jaccard も当時未永続化(n/a)。")


if __name__ == "__main__":
    main()

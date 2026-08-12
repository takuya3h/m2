#!/usr/bin/env python3
"""検出器 3-seed paired-σ 集計（§10.1・phase-seed 平均でノイズ除去）。

logs/phase3seed_results.tsv （列: detector_seed, phase_seed, method, arm, exp_dir）を読み、
(method, detector_seed, arm) ごとに phase_seed を平均 → phase 学習の非決定性を除去。
その上で detector_seed を対にした Δ = aug - frozen を取り、
paired-σ 判定（|mean(Δ)| > pstdev(Δ) かつ 全 detector_seed 同符号）を出す。

使い方: python3 scripts/paired_sigma_3seed.py [results.tsv]
"""
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
RES = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJ / "logs/phase3seed_results.tsv"


def load_metric(exp_dir):
    try:
        m = json.load(open(Path(exp_dir.strip()) / "metrics.json"))
        return m.get("phase_accuracy"), m.get("phase_macro_f1")
    except Exception:
        return None, None


def main():
    if not RES.exists():
        print(f"[ERR] 結果ファイルが無い: {RES}")
        return
    # cells[method][dseed][arm] = list of (acc, f1) over phase_seeds
    cells = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for line in RES.read_text().splitlines():
        if not line.strip():
            continue
        p = line.split("\t")
        if len(p) < 5:
            continue  # 旧フォーマット(ps無し)は無視
        dseed, pseed, method, arm, d = p[0], p[1], p[2], p[3], p[4]
        acc, f1 = load_metric(d)
        if acc is not None:
            cells[method][dseed][arm].append((acc, f1))

    print(f"=== 検出器 3-seed paired-σ 集計（phase-seed平均, source: {RES.name}）===")
    print("Δ = augstrong − frozen（各セルは phase-seed 平均）。有意: |mean(Δ)|>pstdev(Δ) かつ 全detector-seed同符号\n")
    for method in ("S4", "B2a", "T1a"):
        if method not in cells:
            continue
        seeds = sorted(cells[method].keys(), key=lambda x: int(x))
        d_acc, d_f1, detail = [], [], []
        for s in seeds:
            fro = cells[method][s].get("frozen", [])
            aug = cells[method][s].get("aug", [])
            if not fro or not aug:
                detail.append(f"  det{s}: 欠測 (frozen_n={len(fro)} aug_n={len(aug)})")
                continue
            fa = st.mean(x[0] for x in fro); ff = st.mean(x[1] for x in fro)
            aa = st.mean(x[0] for x in aug); af = st.mean(x[1] for x in aug)
            da = (aa - fa) * 100; df = (af - ff) * 100
            d_acc.append(da); d_f1.append(df)
            detail.append(
                f"  det{s}: frozen acc={fa:.4f}/F1={ff:.4f} (n={len(fro)})  "
                f"aug acc={aa:.4f}/F1={af:.4f} (n={len(aug)})  Δacc={da:+.2f}pp ΔF1={df:+.2f}pp"
            )
        print(f"[{method}]  (detector-seeds={len(d_acc)})")
        for ln in detail:
            print(ln)
        if len(d_acc) >= 2:
            _verdict("Δacc", d_acc)
            _verdict("ΔF1 ", d_f1)
        else:
            print("  → detector-seed 不足で paired-σ 未判定")
        print()


def _verdict(name, deltas):
    mean = st.mean(deltas)
    sigma = st.pstdev(deltas)
    same_sign = all(d > 0 for d in deltas) or all(d < 0 for d in deltas)
    sig = abs(mean) > sigma and same_sign
    tag = "✅有意" if sig else "❌非有意"
    print(f"  {name}: mean={mean:+.2f}pp  pstdev={sigma:.2f}pp  同符号={same_sign}  "
          f"→ {tag}  (Δ={['%+.2f' % d for d in deltas]})")


if __name__ == "__main__":
    main()

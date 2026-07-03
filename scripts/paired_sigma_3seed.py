#!/usr/bin/env python3
"""検出器 3-seed paired-σ 集計（§10.1）。

logs/phase3seed_results.tsv （列: detector_seed, method, arm, exp_dir）を読み、
method ごとに detector_seed を対にした Δ = aug - frozen を取り、
paired-σ 判定（|mean(Δ)| > pstdev(Δ) かつ 全 seed 同符号）を出す。

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
    # rows[method][detseed][arm] = (acc, f1)
    rows = defaultdict(lambda: defaultdict(dict))
    for line in RES.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        dseed, method, arm, d = parts[0], parts[1], parts[2], parts[3]
        rows[method][dseed][arm] = load_metric(d)

    print(f"=== 検出器 3-seed paired-σ 集計（source: {RES.name}）===")
    print("Δ = augstrong − frozen（検出器seedを対にした差）。有意: |mean(Δ)|>pstdev(Δ) かつ 全seed同符号\n")
    for method in ("S4", "B2a", "T1a"):
        if method not in rows:
            continue
        seeds = sorted(rows[method].keys(), key=lambda x: int(x))
        d_acc, d_f1, detail = [], [], []
        for s in seeds:
            fro = rows[method][s].get("frozen", (None, None))
            aug = rows[method][s].get("aug", (None, None))
            if None in fro or None in aug:
                detail.append(f"  det{s}: 欠測 (frozen={fro} aug={aug})")
                continue
            da = (aug[0] - fro[0]) * 100
            df = (aug[1] - fro[1]) * 100
            d_acc.append(da)
            d_f1.append(df)
            detail.append(
                f"  det{s}: frozen acc={fro[0]:.4f}/F1={fro[1]:.4f}  "
                f"aug acc={aug[0]:.4f}/F1={aug[1]:.4f}  Δacc={da:+.2f}pp ΔF1={df:+.2f}pp"
            )
        print(f"[{method}]  (n={len(d_acc)} detector-seeds)")
        for ln in detail:
            print(ln)
        if len(d_acc) >= 2:
            _verdict("Δacc", d_acc)
            _verdict("ΔF1 ", d_f1)
        else:
            print("  → seed 不足で paired-σ 未判定")
        print()


def _verdict(name, deltas):
    mean = st.mean(deltas)
    sigma = st.pstdev(deltas)  # 母標準偏差（paired, §10.1）
    same_sign = all(d > 0 for d in deltas) or all(d < 0 for d in deltas)
    sig = abs(mean) > sigma and same_sign
    tag = "✅有意" if sig else "❌非有意"
    print(
        f"  {name}: mean={mean:+.2f}pp  pstdev={sigma:.2f}pp  同符号={same_sign}  "
        f"→ {tag}  (Δ={['%+.2f' % d for d in deltas]})"
    )


if __name__ == "__main__":
    main()

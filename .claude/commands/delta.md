---
description: experiments/baselines/ から Δ（相互改善幅）と 1σ 有意性を集計する
argument-hint: [baseline_step] [metric] (省略時 s0 / mAP)
---

Δ（相互改善幅）分析を行います。引数: `$ARGUMENTS`（省略時は基準 step=`s0`, metric=`mAP`）。

手順:

1. `.venv` の Python で `egosurgery.metrics.delta.DeltaCalculator` を用いる。
2. `experiments/baselines/` 配下の各 step（`s0_*`, `s1_*`, ...）の `metrics.json` を
   集約し、指定 metric の 3-seed 平均±標準偏差を算出する。
3. 基準 step に対する各実験の Δ を計算する。
4. 研究計画 §10.1 に従い、**`|Δ| > 1σ` のときのみ「有意」**と表示する。
   1σ 以内は「有意差なし（改善と主張しない）」と明記する。
5. step × (mean ± std, Δ, 有意性) の表で出力する。
6. `metrics.json` が存在しない / 数値が入っていない step はスキップし、その旨を報告する。
   実測値のみを使い、欠損を埋めるための仮値を作らない。

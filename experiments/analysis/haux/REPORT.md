# haux 系統 Δ_phase 集計レポート

対象: 手情報→工程（系統① det→phase・①信号レベル / train_haux.py）

走査元: `experiments/transfer/haux_*`（metrics.json 直読み・手打ち介入なし）。

分母（S4 base・固定値）: phase accuracy = **0.8986** / 公式 macro-F1 = **0.709**。
各手法の per-seed Δ = (実測 − base)。σ は per-seed Δ の母標準偏差 (`statistics.pstdev`)。
判定（§10.1）: `|mean(Δ)| > σ` かつ 全 seed 同符号 のとき ✓（有意）。seed<2 は判定不能 (n/a)。pp = ×100 表示。

## phase accuracy Δ（vs base 0.8986）

| 手法 (step tag) | seeds (n) | per-seed 生値(Δpp) | Δ mean±σ (pp) | \|Δ\|/σ | 同符号 | 有意(paired-σ) |
|---|---|---|---|---|---|---|
| `haux_hand_count_oracle` | 42/123/456 (n=3) | 42=0.8970(-0.16) 123=0.9050(+0.64) 456=0.8950(-0.36) | +0.04±0.43 | 0.10 | × | × |
| `haux_hand_geom_oracle` | 42/123/456 (n=3) | 42=0.9056(+0.70) 123=0.9142(+1.56) 456=0.9122(+1.36) | +1.21±0.37 | 3.29 | ✓ | ✓ |
| `haux_hand_own_other_oracle` | 42/123/456 (n=3) | 42=0.9010(+0.24) 123=0.8977(-0.09) 456=0.8983(-0.03) | +0.04±0.14 | 0.29 | × | × |
| `haux_hand_presence_oracle` | 42/123/456 (n=3) | 42=0.9056(+0.70) 123=0.9142(+1.56) 456=0.8904(-0.82) | +0.48±0.98 | 0.49 | × | × |
| `haux_hand_presence_oracle_shuffle` | 42/123/456 (n=3) | 42=0.9030(+0.44) 123=0.9056(+0.70) 456=0.8871(-1.15) | -0.00±0.82 | 0.00 | × | × |
| `haux_hand_presence_oracle_withtooloracle` | 42/123/456 (n=3) | 42=0.9545(+5.59) 123=0.9578(+5.92) 456=0.9584(+5.98) | +5.83±0.17 | 33.64 | ✓ | ✓ |

## phase macro-F1 Δ（vs base 0.709）

| 手法 (step tag) | seeds (n) | per-seed 生値(Δpp) | Δ mean±σ (pp) | \|Δ\|/σ | 同符号 | 有意(paired-σ) |
|---|---|---|---|---|---|---|
| `haux_hand_count_oracle` | 42/123/456 (n=3) | 42=0.7046(-0.44) 123=0.6934(-1.56) 456=0.6690(-4.00) | -2.00±1.49 | 1.34 | ✓ | ✓ |
| `haux_hand_geom_oracle` | 42/123/456 (n=3) | 42=0.7084(-0.06) 123=0.7459(+3.69) 456=0.7530(+4.40) | +2.67±1.96 | 1.37 | × | × |
| `haux_hand_own_other_oracle` | 42/123/456 (n=3) | 42=0.6715(-3.75) 123=0.7088(-0.02) 456=0.7016(-0.74) | -1.50±1.61 | 0.93 | ✓ | × |
| `haux_hand_presence_oracle` | 42/123/456 (n=3) | 42=0.7474(+3.84) 123=0.7417(+3.27) 456=0.7037(-0.53) | +2.19±1.94 | 1.13 | × | × |
| `haux_hand_presence_oracle_shuffle` | 42/123/456 (n=3) | 42=0.7510(+4.20) 123=0.7189(+0.99) 456=0.6387(-7.03) | -0.61±4.72 | 0.13 | × | × |
| `haux_hand_presence_oracle_withtooloracle` | 42/123/456 (n=3) | 42=0.8224(+11.34) 123=0.8257(+11.67) 456=0.8254(+11.64) | +11.55±0.15 | 76.61 | ✓ | ✓ |

## 有意判定サマリ

- accuracy で有意(✓): `haux_hand_geom_oracle`, `haux_hand_presence_oracle_withtooloracle`
- macro-F1 で有意(✓): `haux_hand_count_oracle`, `haux_hand_presence_oracle_withtooloracle`

（集計: 6 手法 / 実験フォルダ 18 件。同一 (手法, seed) の重複は最新 seq を採用。）

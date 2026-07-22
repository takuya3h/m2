# STEP D-aux 総合集計（per-seed paired-σ・§10.1 準拠）

実測 metrics.json 直読み（手打ち・捏造なし）。判定 = |mean|>pstdev かつ 3-seed 同符号。

**分母 = 同一環境 S4 base（GAP-only TeCNO・seed 42/123/456）**: acc 89.83±0.90 / macro-F1 69.65（文書固定値 89.86/70.9 と整合）。

Δ は method[seed] − S4[seed] の per-seed 差（pp = percentage point）。


## 系統① 手情報 → 工程（det→phase・①信号レベル）

| 手法 | Δacc mean(pp) | σ(pp) | \|m\|/σ | acc | ΔF1 mean(pp) | σ(pp) | \|m\|/σ | F1 |
|---|--:|--:|--:|:-:|--:|--:|--:|:-:|
| H-1 presence | +0.51 | 0.08 | 6.15 | ✓ | +3.44 | 1.24 | 2.78 | ✓ |
| H-2 count | +0.07 | 0.56 | 0.12 | × | -0.75 | 1.67 | 0.45 | × |
| H-3 geom | +1.23 | 0.95 | 1.30 | ✓ | +3.92 | 3.60 | 1.09 | ✓ |
| H-5 own_other | +0.07 | 0.92 | 0.07 | × | -0.25 | 2.93 | 0.09 | × |
| H-6 presence+tool | +5.85 | 0.97 | 6.05 | ✓ | +12.80 | 2.52 | 5.07 | ✓ |
| H-1 shuffle (control) | +0.02 | 0.22 | 0.10 | × | +0.64 | 3.15 | 0.20 | × |
| B2a tool-only (oracle) | +5.81 | 0.73 | 8.01 | ✓ | +12.70 | 2.44 | 5.19 | ✓ |

**H-6 の tool 上乗せ価値**（H-6 − B2a tool単独, per-seed paired）:
- Δacc +0.04pp (|m|/σ=0.18) × / ΔF1 +0.10pp (|m|/σ=1.05) × → 手は tool に対し冗長（上乗せ無し）


## 系統② 時系列 → 工程（region-token 基盤）

vs S4（headline・region+核の総効果） / vs T-4（region-token TeCNO 基準・問い A/B）

| 手法 | vsS4 Δacc(pp) | acc | vsS4 ΔF1(pp) | F1 | vsT4 Δacc(pp) | acc | vsT4 ΔF1(pp) | F1 |
|---|--:|:-:|--:|:-:|--:|:-:|--:|:-:|
| T-4 tecno (region base) | +5.06 | ✓ | +11.13 | ✓ | — | · | — | · |
| T-1 movavg | +4.47 | ✓ | +9.59 | ✓ | -0.59 | ✓ | -1.54 | ✓ |
| T-2 delta | +3.17 | ✓ | +8.57 | ✓ | -1.89 | ✓ | -2.55 | ✓ |
| T-3 window | +5.21 | ✓ | +11.64 | ✓ | +0.15 | × | +0.51 | × |
| T-6 minGRU | +5.13 | ✓ | +10.42 | ✓ | +0.07 | × | -0.71 | × |

# T1a-Boundary 総合集計（per-seed paired-σ・§10.1）

実測 metrics.json + checkpoint 直読み（捏造なし）。判定 = |mean(Δ)|>pstdev かつ 3-seed 同符号。

**分母 = 同一環境 efros 再学習 T1a base（region⊕GAP・val）**: acc 94.76 / macro-F1 80.30 / edit 32.96 （lecun T1a base acc 94.83/F1 80.44 と整合＝env parity）。

Δ = method[seed] − base[seed]（per-seed 対差）。acc/macroF1 は pp、edit/segF1 は素点。


## 機構(1) boundary 監督（plain decode = 共有 trunk 正則化単独）

| 指標 | Δ mean | σ | \|m\|/σ | 判定 |
|---|--:|--:|--:|:-:|
| acc | -0.18pp | 0.22 | 0.78 | × |
| macroF1 | +0.19pp | 0.95 | 0.20 | × |
| edit | +1.07 | 4.05 | 0.26 | × |
| segF1@10 | -0.15 | 3.44 | 0.04 | × |
| segF1@25 | +0.04 | 3.11 | 0.01 | × |
| segF1@50 | +0.47 | 3.25 | 0.15 | × |

→ boundary 監督を共有 trunk に足すだけでは edit/seg-F1 は実質改善せず（正則化効果は僅少）。


## 機構(2) 因果 boundary-gated sticky decode（τ 掃引・seed 平均と paired-σ）

τ↑ で遷移抑制↑（edit↑ だが誤 phase 固着で acc↓）。**edit を上げる τ は必ず acc を大きく損なう**。

| τ | acc | Δacc(paired) | edit | Δedit(paired) | segF1@50 |
|--:|--:|--:|--:|--:|--:|
| 0.10 | 90.80 | -3.96pp (✓) | 40.88 | +7.92 (×) | 0.431 |
| 0.30 | 84.88 | -9.88pp (✓) | 44.33 | +11.38 (×) | 0.372 |
| 0.50 | 75.14 | -19.63pp (✓) | 48.57 | +15.61 (✓) | 0.457 |
| 0.70 | 71.35 | -23.41pp (✓) | 52.13 | +19.17 (✓) | 0.558 |

→ 学習 boundary の確信度で gate しても、edit を有意に上げる τ では acc が数〜20pp 有意低下。**boundary-gate では acc 維持で edit 改善する τ は存在しない**（§8 の学習 boundary head 提案は非有効）。


## 機構(3) min-segment debounce（因果・boundary head 非依存・新 phase が k 連続で確定）

boundary head を使わず、k 未満の短 blip を除く単純な因果後処理。**edit/seg-F1 を大きく改善**。

| k | Δacc | acc維持? | ΔmacroF1 | Δedit | edit✓ | ΔsegF1@50 | seg✓ |
|--:|--:|:-:|--:|--:|:-:|--:|:-:|
| 2 | -0.95pp | 維持 | -2.03pp | +23.43 | ✓ | +0.229 | ✓ |
| 3 | -2.27pp | -2.27pp | -4.97pp | +37.71 | ✓ | +0.226 | ✓ |
| 5 | -4.69pp | -4.69pp | -10.83pp | +35.27 | ✓ | +0.196 | ✓ |

→ **k=2 の debounce が最良の運用点**: edit/seg-F1 を大幅改善しつつ acc 低下は約 −1pp に留まる（遷移を k−1 フレーム遅延させる latency と引き換え・online 許容）。


## 結論

- **§8 が推す「学習 boundary head」は online では非有効**: plain 監督は無効（全指標 ×）、boundary-gated sticky は edit↔acc の急なトレードオフ（未来を見て区間多数決する offline ASRF が使えない online 制約が本質）。

- 一方 **パラメタフリーの因果 min-segment debounce(k=2) は edit/seg-F1 を大幅改善**（Δedit ≈ +23, ΔsegF1@50 ≈ +0.22）しつつ acc は約 −1pp に維持 → 過分節は online でも**区間長 prior**で実用的に低減可能。「学習した boundary evidence」より「単純な最小区間長」が効く。

- T1a の過分節の一部は per-frame region-token 信号の**実変動**を反映し、boundary head では真/偽の遷移を分離しきれない。系統②「ボトルネックは時系列機構でなく入力信号」を別軸で追認しつつ、**edit-score は安価な因果後処理(k=2)で回収でき、acc 改善には入力信号（検出/region 表現）強化が要る**という運用指針を得た。


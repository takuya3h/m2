# ③ T1c 双方向 §4.6 パイロット v2（非対称・高品質S4事後 / 1-seed=42・frame 粒度）— **partial fix・mutual gain 未達**

**日付**: 2026-07-08 ／ **データ**: 検出 **val** mAP + 工程 **val** per-frame acc（seed42, warm-start S0-frozen Relation-DETR）
**証跡**: `results.json` ／ 生 run: `transfer/t1c_bidir_v2_pilot_seed42/{bidir_s4,plasticphase}_result.json`（`per_epoch_eval` 付き）
**コード**: `scripts/{train_t1c_bidir.py(--phase2det-source s4), run_t1c_bidir_v2_pilot.sh}`（commit 66a5c10）／ v1: `experiments/analysis/t1c_bidir_pilot/`

## 問い（v1 の是正）
v1 pilot は **naive 対称双方向が negative**（online 低品質事後の注入で検出器不安定化）と確定。remedy 候補②「**高品質事後の注入**」を採用し、
phase→det を **収束済 S4 事後（precomputed phase context）** に置換した **非対称結合**（det→phase のみ online 学習）で、
検出破壊が是正され相互改善に届くかを 1-seed で判定する。

## 方法（v1 との差分のみ）
- **A'=v2-bidir**: phase→det = **S4 事後注入**（`--phase2det-source s4`, camt, train_t1b 既存 npz）／ det→phase = online phase head（trainable=all 可塑）。
- **C=plastic-phase**: det→phase（可塑検出器 + phase head）のみ・**phase→det off**。可塑性単独の phase 寄与を分離する対照。
- 恒等ガード: A' init det mAP=0.7303 assert（camt zero-init 恒等・S4注入でも warm-start 寄与0）。判定基準は下表。

## 結果（final epoch, n=1）
| 指標 | A'=v2-bidir(S4) | 対照 | **Δ** |
|---|---:|---:|---:|
| det mAP (final) | **0.7106** | ① camt-all **inj** 0.7181 | **−0.75pp** |
| det mAP (final) | 0.7106 | ① camt-all **ctrl** 0.7110 | −0.04pp（≈ctrl） |
| det mAP (final) | 0.7106 | **v1 bidir** 0.7067 | **+0.39pp**（v2 改善） |
| phase acc (mean 6ep) | 0.3585 | frozen head 0.3690 | **−1.05pp** |
| phase acc (final) | 0.3188 | frozen head 0.3690 | −5.02pp |
| phase acc (mean) A'−C | 0.3585 | C 0.3589 | **≈0（同値）** |

### 軌跡（per-epoch）
| ep | -1 | 0 | 1 | 2 | 3 | 4(LR↓) | 5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A' det mAP | 0.7303 | 0.7078 | 0.7024 | 0.6919 | 0.6761 | 0.7051 | **0.7106** |
| C  det mAP | 0.7303 | 0.7003 | 0.7052 | 0.6841 | 0.6882 | 0.7097 | 0.7142 |
| A' phase acc | 0.028 | 0.3974 | 0.3888 | 0.3888 | 0.3287 | 0.3287 | 0.3188 |
| C  phase acc | 0.028 | **0.5023** | 0.4554 | 0.3716 | 0.3776 | 0.2475 | **0.1987**(崩壊) |

## 判定 — **v2 は検出破壊を是正したが、双方向の相互改善は未達（両方向とも収束時 ≈ 中立）**
- **phase→det（検出）: 破壊は是正、しかし利得は洗い流される**。v2 det は v1 (0.7067) を **+0.39pp** 上回り、LR decay 後 0.7106 へ回復
  ＝ **S4 高品質事後の根本是正が効いた**。だが final 0.7106 は **① inj 0.7181 に −0.75pp 未達**で、**① ctrl 0.7110 と同値**。
  さらに **C(注入なし) 0.7142 ≥ A'(S4注入) 0.7106** で、co-training 下では S4 注入の検出上乗せ（① 単独では inj−ctrl=+0.71pp）が**消失**している。
  → **det→phase の phase 損失を同時に流すと、phase→det の利得が相殺される**。
- **det→phase（工程）: 安定利得なし**。A'/C の phase **平均はほぼ同値**（0.3585 vs 0.3589）で**ともに frozen baseline(0.3690) 近傍**、
  かつ**激しく振動**（C は best 0.5023→final 0.1987 と末尾崩壊、A' も best 0.3974→final 0.3188）。
  final の A'−C=+12.0pp は **C の末尾崩壊由来のノイズ**であり、平均で見れば **S4 注入は phase を安定化も改善もしない**。
- **配線は正**（恒等 init 0.7303 厳密・loss 有限）。これは設計課題であってバグではない（v1 と同じ結論）。

## 解釈 — 高品質事後で「破壊」は消えたが「相互改善」は frame 粒度が阻む
S4 事後注入は v1 の検出不安定化（online 低品質事後が原因）を**確かに解消**した（det が ctrl 水準へ回復）。
しかし (a) **phase→det**: 単独では出た検出利得(① +0.71pp)が、**det→phase の同時最適化下で中立化**（det≈ctrl、A'≤C）。
(b) **det→phase**: 可塑検出器 + frame 粒度 phase head は **frozen baseline を安定して超えず**、振動が支配的。
→ **ボトルネックは frame 粒度 phase head（時系列モデル無し）**。工程は本質的に時系列構造を持つため、frame 独立予測では
頭打ち・不安定になり、双方向の "det→phase→det" ループが有効な信号を還流できない。

## ③ 総括（v1 + v2）— 双方向 §4.6 は本 pilot 群で mutual gain を示さず
| 版 | 結合 | phase→det | det→phase | 結論 |
|---|---|---|---|---|
| **v1** | naive 対称・online 事後 | 負（det 破壊 −0.42〜−2.36pp） | 中立・不安定 | **negative** |
| **v2** | 非対称・S4 事後 | 中立（det≈ctrl・利得相殺） | 中立・不安定 | **partial fix, no mutual gain** |

**docs 564「勾配が双方向に流れる結合が相互改善する」仮説は、本 frame 粒度 pilot 群では支持されない**。
①(可塑×広域CA)・②(frozen×排他ゲート) が示した「**phase→det は結合様式に強く依存**」という統一像とも整合し、
「単に双方向に繋げば伸びる」ものではないことを安価に確定した。残 remedy は **phase の時系列化（TeCNO 等・v1 report remedy④）**。

## 残 remedy と位置づけ
- **remedy④ phase 時系列化（本命）**: frame 粒度 PhaseHead → TeCNO 時系列 head に戻し、phase 振動を抑えた上で双方向を再評価。
  ただし TeCNO 統合は相応の実装コスト（時系列 dataloader・因果 TCN・清書学習）で、pilot ではなく本実装フェーズの規模。
- **誠実な限界**: n=1・**val**・frame 粒度。確定は seed 揃い＆ test 追認後。単点 final は phase 振動の影響大（mean/best/trajectory 併記済）。
- ③ は **v1(negative)→v2(partial fix)** で「双方向は結合様式・phase 表現に依存し、frame 粒度では mutual gain 不成立」を確定。
  ①(phase→det 成立: 可塑×広域CA)・②(phase→det 成立: frozen×排他ゲート) と合わせ、**M2 の "phase→det は regime 依存" 統一像**を補強した。

> ⚠ **誠実性**: 数値は全て val・n=1 pilot の実測（捏造なし）。det の "相殺"・phase の "同値/振動" は上記軌跡・results.json に基づく。
> 未達（① inj 未到達・mutual gain 不成立）は未達として報告。test 追認・多 seed は未実施。

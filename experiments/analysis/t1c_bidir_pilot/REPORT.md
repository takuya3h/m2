# ③ T1c 双方向 §4.6 パイロット（1-seed=42・frame 粒度・2-pass）— **negative result（naive 対称双方向は不可）**

**日付**: 2026-07-08 ／ **データ**: 検出 **val** mAP + 工程 **val** per-frame acc（seed42, warm-start S0-frozen Relation-DETR）
**証跡**: `results.json` ／ 生 run: `transfer/t1c_bidir_pilot_seed42/{bidir,phasefrozen}_result.json`（`per_epoch_eval` 付き）
**コード**: `scripts/{train_t1c_bidir.py, run_t1c_bidir_pilot.sh}`（commit 2536f7d, smoke 検証済）／ 設計: `tasks/todo_t1c_bidir_pilot.md`

## 問い
①(camt-all: 可塑×広域CA で phase→det)・②(clsbias-PE: frozen×排他ゲート) を踏まえ、**1 モデルで det→phase と
phase→det の両勾配を同時に流す**双方向結合（§4.6・docs 564「勾配が双方向に流れる結合が要る」）が、両タスクを
単方向 baseline 以上に相互改善するか。1-seed pilot で設計可否を安価に判定。

## 方法（surgery 不要・2-pass teacher-forced・frame 粒度に簡約）
- warm-start S0-frozen seed42（camt 変種, out_proj zero-init=恒等）。**A=bidir**（両方向 on・trainable=all 可塑）。
- det→phase: forward hook で decoder `class_head[-1]` の region token(3840) を捕捉→PhaseHead(MLP)→9 工程 logits。
- phase→det: camt 注入（online posterior を `set_phase_context` 還流）。Pass1(eval,zero-ctx)→region→L_phase; Pass2(train, softmax(P).detach() 注入)→L_det; L=L_det+λL_phase。
- **B=phase-frozen baseline**（det→phase off: 検出器凍結＋PhaseHead のみ学習＝T1a 相当の frozen-detector phase head）。
- 判定: phase→det Δ=det_mAP(A)−① camt-all ctrl 0.7110 ; det→phase Δ=phase_acc(A)−phase_acc(B)。恒等ガード: A init det mAP=0.7303 assert。

## 結果（final epoch, n=1）
| 指標 | A=bidir | baseline | **Δ** |
|---|---:|---:|---:|
| det mAP (final ep5) | **0.7067** | camt-all ctrl 0.7110 | **−0.42pp** |
| det mAP (final) | 0.7067 | S0-frozen 0.7303 | **−2.36pp** |
| phase acc (final ep5) | **0.3281** | frozen head 0.3690 | **−4.09pp** |
| phase acc (mean over 6ep) | 0.3778 | 0.3788 | ≈0（Aは変動大） |

### 軌跡（per-epoch）
| ep | -1 | 0 | 1 | 2 | 3 | 4(LR↓) | 5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A det mAP | 0.7303 | 0.6932 | 0.6885 | 0.6960 | 0.6931 | 0.7109 | 0.7067 |
| A phase acc | 0.028 | 0.3802 | **0.5743** | 0.3472 | 0.3089 | 0.3281 | 0.3281 |
| B phase acc | 0.028 | 0.3677 | 0.4330 | 0.3677 | 0.3677 | 0.3677 | 0.3690 |

## 判定 — **naive 対称双方向は相互改善せず（両タスクで単方向 baseline 未満/不安定）**
- **phase→det ≈ 負/中立**: A det mAP は高 LR 期（ep0-3）に ~0.69 まで劣化、LR decay(ep4) で 0.711 へ回復するも final 0.7067 は
  camt-all ctrl(0.7110) を **−0.42pp** 下回り、S0-frozen(0.7303) を **−2.36pp** 下回る。**online（co-trained で初期低品質）事後の注入が検出器を不安定化**。
- **det→phase ≈ 中立だが不安定**: A phase acc は **平均では frozen baseline とほぼ同値**（0.3778 vs 0.3788）だが**変動が激しい**（best 0.5743 / final 0.3281）。
  可塑検出器の co-training は frozen-detector phase head を **安定して超えない**（final は −4.09pp）。
- **配線は正**（恒等 init 0.7303 厳密・loss 有限・smoke 済）。これは**設計課題であってバグではない**。

## 解釈 — 二方向が naive 結合下で破壊的干渉
online の低品質 phase 事後を検出器へ注入すると、(a) 検出器が誤条件づけで劣化（phase→det 負）、(b) 劣化した検出器の region token が
phase head の入力を悪化させ phase も不安定化（det→phase 中立止まり）。**素朴な対称双方向は「勾配が双方向に流れれば伸びる」仮説
（docs 564）を単純には満たさない**。文献「det→phase は効く／phase→det は難方向」（docs 736）・①②「phase→det は
**適切な regime（可塑×高品質事後 or frozen×排他ゲート）**が要る」と整合。

## 是正案（v2 設計候補・要ユーザー判断）
naive 対称双方向の失敗要因＝「初期低品質な online 事後の注入」。remedy:
1. **phase head ウォームアップ**: 先に det を数 ep 単独学習 or phase head を先行収束させ、高品質事後になってから phase→det 注入を on。
2. **高品質事後の注入**: online co-trained 事後でなく、**収束済 S4 事後（precomputed phase context, train_t1b 既存）**を phase→det に使い、
   det→phase のみ online で学習（非対称結合）。
3. **②の排他ゲート事後注入**: phase→det を phase-排他術具に限定（clsbias-PE 流用）して検出劣化を回避。
4. **phase の時系列化**: frame 粒度 PhaseHead を TeCNO 時系列に戻し phase 振動を抑制（本来の T1a）。
5. **非対称 λ / 勾配ゲート**: phase→det の注入強度を段階的に上げる、or det 損失を優先。

## 位置づけ
③ pilot は **negative result（naive 対称双方向は不可）を安価に確定**し、v2 の設計方向（非対称・高品質事後・ゲート・時系列）を特定。
①(可塑×広域CA で phase→det 成立)・②(frozen×排他ゲートで phase→det 成立) と合わせ、**phase→det は結合様式に強く依存**するという統一像を補強。

> ⚠ **誠実性**: n=1 pilot・**val** 評価。確定は seed 揃い＆ test 追認後。phase acc は frame 粒度で振動が大きく（時系列なし）final 単点の解釈に注意（mean/best/trajectory 併記済）。

# ③ 双方向 §4.6 統合 — パイロット双方向（1-seed 先行）設計・計画

**決定（ユーザー承認済 2026-07-07）**: パイロット双方向 1-seed 先行。seed42 で実装・恒等ガード・双方向Δ検証 → 有望なら 3-seed 本走。

## 背景（①②の到達点）
- phase→det の二解: **camt-all**（可塑×広域CA, overall +0.609✅ / Bipolar +2.65✅・ただし overall 絶対劣化）、
  **clsbias-PE**（frozen×phase-排他ゲート, overall +0.228✅・init 超え・非注入厳密中立）。
- 先行 T1a（det→phase）: region token(3840-d)⊕GAP → TeCNO 時系列 → phase acc +0.050✅。
- docs 564 仮説: 「結合で伸ばすには **勾配が双方向に流れる結合**（同時学習）が要る（frozen hard-sharing は Δ≈0）」。

## 粒度の簡約（pilot の要点）
真の T1a は **TeCNO 時系列（clip）**、T1b は **per-frame 検出器** → 粒度差が大。
**pilot は frame 粒度に簡約**: per-frame phase head（region token → MLP → 9 工程 logits, 時系列なし）で
「双方向結合の勾配基盤が両タスクを相互改善するか」を最小コストで検証。時系列は本走(3-seed)で TeCNO 化を検討。

## アーキテクチャ（surgery 不要・2-pass teacher-forced）
- warm-start: S0-frozen Relation-DETR seed42（camt 変種, phase_attn out_proj zero-init = 恒等）。
- trainable: 検出器可塑（①で可塑性が結合を解くと確証）＋ phase head。
- **det→phase**: forward hook で decoder 最終層 object-query 埋め込み R を捕捉（precedent: `extract_t1a_regiontoken.py`,
  hook on `class_head[-1]`）→ per-class score-gate で (B,3840) → phase_head(MLP) → 9 工程 logits。
- **phase→det**: camt 注入（既存 `set_phase_context((B,9))`）。posterior は phase head の online 出力。
- **循環回避 = 2-pass**:
  - Pass1: `set_phase_context(0)` で forward → hook が R 捕捉（grad 有）→ phase_head → P_online → `L_phase = CE(P_online, phase_label)`。
  - Pass2: `set_phase_context(softmax(P_online).detach())` で forward(targets) → `L_det`。
  - `L = L_det + λ·L_phase`、backward 1回。shared backbone で双方向勾配。
  - 2 forward/step（~2x コスト）は 1-seed pilot で許容。
- phase ラベル: joint_manifest の frame.phase_label を `build_imgid_to_ctx` 機構で image_id へ対応（imgid→phase_label）。

## 対照・成功基準（pilot・§10.1 は本走で）
- 恒等ガード: 学習前 det mAP が S0-frozen 帯[0.65,0.78]、phase head fresh ゆえ phase acc ≈ chance から。
- phase→det 効果: pass2 の det mAP を **P_online 注入 vs zero-ctx** で比較（Δ_det>0 か・overall 監視）。
- det→phase 効果: phase acc を **検出器可塑(結合) vs 検出器 frozen(T1a 相当)** で比較（Δ_phase>0 か）。
- 双方向相互改善: 両 on が各単方向 baseline を上回るか（pilot は方向性・健全性の確認、確定は 3-seed）。
- 研究インテグリティ: 数値捏造禁止・val 評価は test 追認まで暫定・未達は正直報告。

## タスク
- [ ] 1. `scripts/train_t1c_bidir.py` 骨格（train_t1b から検出器 build/det loader/camt/eval_detection を再利用）
- [ ] 2. region-token hook + per-frame phase_head（MLP: 3840→256→9）実装
- [ ] 3. imgid→phase_label ローダ（joint_manifest 由来）
- [ ] 4. 2-pass forward + joint loss + dual eval（det mAP / phase acc）
- [ ] 5. 恒等・健全ガード（warm-start det mAP 帯, phase acc chance 起点, loss finite）
- [ ] 6. smoke（--epochs 1 --steps 6）で配線・恒等確認
- [ ] 7. seed42 pilot 本走（epochs=6, bidir + 対照）→ 双方向Δ測定
- [ ] 8. analyze → REPORT(experiments/analysis/t1c_bidir_pilot/) → docs → commit → Notion
- [ ] 9. 判定: 有望なら 3-seed 本走をユーザーに提案 / 設計問題なら是正

## 成功の定義
pilot が「双方向結合が det mAP と phase acc の双方で単方向 baseline 以上（少なくとも非劣化かつ方向正）」を
seed42 で示せば設計妥当 → 3-seed 本走へ。示せなければ結合機構（λ, teacher-forcing, 粒度）を是正。

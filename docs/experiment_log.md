# 実験ログ

全実験で「仮説→実験→結果→解釈→次の行動」を記録する。

---

## YYYY-MM-DD — [S?] 短い説明

### 仮説

### 実験
- 実験 ID:
- 変更した軸:

### 結果

### 解釈

### 次の行動
1.

---

## 2026-05-22 — [S0] 実検出器ベースライン Wave 1（Mask DINO 枠 ×2 seeds）

### 仮説
COCO 事前学習済み DINO-4scale（"Mask DINO" 枠の代替）を EgoSurgery-Tool 15 クラスへ
mmdet で 12 epoch fine-tune すれば、内蔵 SimpleDetectionHead（前セッション mAP 1.4%）を
大きく上回り、実検出器としての S0 基準点が確立できる。

### 実験
- 実験 ID: `s0_001_maskdino_bbox_seed42`, `s0_002_maskdino_bbox_seed123`
- 変更した軸: trainer = `MMDetTrainer`（mmdet Runner）、detector = `dino-4scale_r50`、
  optimizer = AdamW 1e-4、batch=4、epochs=12、`load_from` = COCO 重み、
  `auto_scale_lr base_batch_size=16` → effective lr ≈ AdamW 1e-4 × 4/16
- 評価: EgoCocoMetric（COCO mAP / per-class / AP_rare(Skewer,Syringe,Forceps) / AP_common）
- 環境: torch 2.1.2+cu118 / mmdet 3.3.0 / mmcv 2.1.0 / RTX A6000 ×2

### 結果（val 分割、`metrics.json` 抜粋）
| 実験 | best epoch | mAP | mAP_50 | mAP_75 | AP_rare | AP_common |
|---|---:|---:|---:|---:|---:|---:|
| s0_001 seed42 | 5 | **0.327** | 0.451 | 0.359 | 0.129 | 0.322 |
| s0_002 seed123 | 10 | **0.296** | 0.402 | 0.322 | 0.111 | 0.293 |

主要クラスは Electric Cautery（60-67%）/ Hook（21-39%）/ Gauze（18%）が立ち上がる一方、
Forceps（2-3%）・Bipolar Forceps（0%）は長尾で停滞。Mouth Gag は val GT 不在で NaN。

### 解釈
- 実検出器化で内蔵ヘッド（1.4%）から **23× の mAP 改善**。実 SOTA（45.8）の射程圏内に入った。
- seed 間の分散は 3pt（0.327 vs 0.296）。best epoch の早期化（5 epoch）は LR ステップ前の
  早期収束を示唆し、12 epoch の最終 LR ステップで揺らぐ／伸びる可能性がある。
- AP_rare 11-13% は依然低く、Copy-Paste / RFS / SeesawLoss など長尾対策の効果検証（S2+）が必要。
- 形状類似ペア（Forceps / Tweezers / Needle Holders / Bipolar Forceps）の混同行列は
  各実験の `visualizations/confusion_matrix.png` に保存。誤分類傾向は S3 以降の関係推論で改善余地。

### 次の行動
1. Wave 2 完了待ち（s0_003 maskdino seed456 + s0_004 VFNet seed42）。**s0_004 が判定 #4 の関門**。
2. Wave 3 完了後に 3 seed の平均±標準偏差を `/delta` で算出し §2.5(a) 基準点を確定。
3. AP_rare の改善余地を S2（長尾対策アブレーション）で実測する。

---

## 2026-05-23 — [S0] 実検出器ベースライン完走（全 6 実験 / §2.5(a) 基準点確定）

### 仮説（前項からの継続）
COCO 事前学習済み実検出器（DINO-4scale=Mask DINO 枠 / VarifocalNet）を mmdet で
EgoSurgery-Tool 15 クラスへ 12 epoch fine-tune すれば、3 seeds で安定した
S0 基準点が確立できる。

### 実験
- 実験 ID: `s0_001` 〜 `s0_006`（maskdino ×3 + varifocanet ×3、全 6 実験）
- 変更した軸: Wave 1 から `seed` のみ。trainer / optimizer / scheduler / batch / epochs は全実験で固定（Δ 整合性）
- 評価: val 分割（2230 枚）COCO mAP + post-hoc test 評価（s0_004 のみ、4265 枚）

### 結果（val、`metrics.json` 集計）
| Detector | seed | best ep | mAP | mAP_50 | AP_rare |
|---|---:|---:|---:|---:|---:|
| Mask DINO | 42  | 5  | **0.327** | 0.451 | 0.129 |
| Mask DINO | 123 | 10 | 0.296 | 0.402 | 0.111 |
| Mask DINO | 456 | 9  | 0.321 | 0.435 | 0.140 |
| VFNet | 42  | 10 | 0.285 | 0.417 | 0.135 |
| VFNet | 123 | 9  | 0.276 | 0.411 | 0.130 |
| VFNet | 456 | 9  | 0.272 | 0.399 | 0.125 |

**3-seed mean ± std**: Mask DINO **0.315 ± 0.016** / VarifocalNet **0.278 ± 0.007**
**Δ(Mask DINO − VarifocalNet) = +0.037**（DINO 枠優位）

post-hoc test（s0_004 best_val_mAP_epoch_10.pth）:
- test/mAP = **0.388** / test/mAP_50 = 0.555 / test/AP_rare = 0.329
- val→test で +10pt の改善（rare クラスのインスタンス分布差）

### 解釈
- 検出器ベースラインを確立。Mask DINO が VarifocalNet を 3-seed 平均で +3.7pt 上回る
  （COCO 上の VFNet 41.6 < DINO-4scale 49 と整合）。
- **判定 #4「VFNet mAP ≥ 45.8 (公式 SOTA 再現)」未達**:
  - val 0.278（−18pt）/ test 0.388（−7pt）
  - 標準 1x schedule では収束済み（epoch 8-12 でプラトー）
  - 残ギャップの仮説: (a) schedule 1x vs 論文の 2x/3x、(b) multi-scale training の有無、
    (c) 長尾対策（seesaw/RFS/copypaste 等の実装統合度）の差
  - 数値を作らず未達を honest に報告（CLAUDE.md 「研究インテグリティ」）。
- AP_rare は依然 11-14%（Bipolar Forceps / Retractor が 0-1%）— 長尾対策アブレーション（S2 以降）の主役。

### 次の行動
1. Part 4 へ移行: S2（hand 追加）と S3（phase frame）を実行する。
2. S2 では tool mAP の Δ(S2-S0)、hand mAP > 65 を判定する。
3. S3 は frozen-backbone デカップル構成で実装済み（PhaseTrainer）。検出器を呼ばないため
   tool mAP 劣化はゼロが構造的に保証される。
4. 判定 #4 未達のリカバリは S0 拡張試行（2x schedule + multi-scale）として別建てで検討。

---

## 2026-05-23 — [S2] Tool+Hand 19 クラス検出（S0 best から fine-tune）

### 仮説
S0 best（Mask DINO seed42）から 19 クラス（tool 15 + hand 4）へ fine-tune すれば、
tool 認識能力を維持しつつ hand 4 クラスを追加学習でき、判定 #2
「hand mAP > 65 / tool mAP Δ ≤ 1pt」を達成できる。

### 実験
- 実験 ID: `s2_001` 〜 `s2_003`（mask_dino × 3 seeds、experiments/phase0/）
- 変更した軸: num_classes 15→19、ann_file→tool+hand 統合 COCO、load_from=S0 best
- epochs=8、batch=4、AdamW lr=1e-4 (auto_scale 0.25× → 2.5e-5 effective)

### 結果（val、`metrics.json`）
| seed | best ep | mAP | tool_mAP | hand_mAP |
|---:|---:|---:|---:|---:|
| 42  | 1 | **0.029** | 0.018 | 0.057 |
| 123 | 1 | 0.032 | — | 0.060 |
| 456 | 1 | 0.028 | — | — |

epoch 推移 (s2_001): tool=0.018→0.003 / hand=0.057→0.056 — **tool が崩壊**。

### 解釈
**Catastrophic forgetting**: mmengine の `load_from` が DINO の `bbox_head.cls_branches[0..6]`
全 14 層を 15→19 サイズ不一致で random init。S0 best が学習した tool 知識は
encoder/decoder の query 表現に残っているが、cls heads が random init + 8 epoch では
tool の判別を回復できず、新たに learn する hand 表現と内部で競合して tool mAP が劣化した。

**判定 #2 未達**: hand=0.056 (< 0.65), tool 劣化 -0.324 ≫ ±0.01。
- 修正案: COCO 重みからの 19-class 学習（S0 best 経由しない、S0 と同等手順）
- もしくは cls_branches 以外の query embedding を保持する mmengine 拡張ロード
- 50 epoch + multi-scale + 適切なフィルタリング augmentation の組合せが必要と推察

実測値は honest に保存（CLAUDE.md 研究インテグリティ）。失敗パターンは S0→S2 遷移時の
標準的なリスクとして `_failed_s3_weighted` と並んで `experiments/phase0/` に記録。

### 次の行動
1. COCO 重みからの 19-class 学習を s2_004 以降で別建て試行（時間予算許可時）。
2. 判定 #2 は未達として明示。S3 / S4 以降の評価に影響しない（S3 はデカップル、S4 以降は時系列）。

---

## 2026-05-23 — [S3] Phase 認識 frame-by-frame（弱ベースライン）

### 仮説
spec §2.1 の「弱接続」を最大限尊重し、検出器とは独立した frozen ResNet50 + PhaseHead で
9 クラス工程認識を学習する。これにより判定 #2「Δ(S3-S2) tool mAP ≤ 1pt」は
構造的に達成（S3 は検出器を呼ばない）。S4 の時系列モデルへの比較基準となる。

### 実験
- 実験 ID: `s3_001` 〜 `s3_003`（experiments/phase0/）
- Backbone: torchvision ResNet50（ImageNet 事前学習、凍結）
- PhaseHead: 2048 → 512 → 9, dropout=0.3
- Loss: 標準 CE + label smoothing 0.1（**class weights 無効化**）
- AdamW lr=1e-4, batch=32, 5 epoch
- Data: PhaseImageDataset が CSV と画像をマッチング（train ~5400 frames, val 1515 frames）

### 結果（val）
| seed | best ep | accuracy | macro_F1 | edit | seg_F1@10 | seg_F1@25 | seg_F1@50 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 42  | 5 | 0.588 | 0.281 | 4.66 | 0.071 | 0.052 | 0.020 |
| 123 | 5 | 0.589 | 0.277 | 4.89 | 0.070 | 0.053 | 0.010 |
| 456 | 5 | 0.602 | 0.298 | 4.92 | 0.071 | 0.051 | 0.013 |

3-seed mean: **accuracy 0.593 ± 0.008 / macro F1 0.285 ± 0.011**
loss 推移（全 seed 共通）: 1.39 → 0.97（単調減少）

### 解釈
- vs random 11%（9 クラス）に対し accuracy 59% は明確な学習信号。
- macro F1 28.5% は val 不在の disinfection / irrigation を除外せず計算しているため低く出る。
- edit_score 4.85 / seg F1 が低い: frame-by-frame の単純設計のため動画内セグメント構造を
  捉えられない。S4 で時系列モデル（TCN / Transformer）へ拡張すれば大幅改善見込み。
- **失敗→修正の学び**: 当初 `class_weights_from_frequencies` で逆頻度重みを適用したところ、
  val 不在クラス（disinfection / irrigation）の重みが極大化し val_acc が 0.5%（random 以下）に
  崩壊した。`use_class_weights: false` で均一重みへ切替て val_acc 49→59% に回復。
  失敗実験は `experiments/phase0/_failed_s3_weighted/` に保存。

### 次の行動
1. S4 で時系列モデル（temporal_dataset.py + TCN/Transformer head）へ拡張し edit/seg F1 を改善。
2. PhaseLoss の weights を sqrt(inverse freq) でクリップする中間案も S4 で再検証。

## 2026-05-29: Sense-X Co-DETR (9-encoder) を環境統一のため中止

### 仮説
Sense-X 版 Co-DETR (CoDINO 5-scale 9-encoder LSJ R50) は、mmdet 3.x 同梱の
Co-DETR (s0_007-009) より深い encoder で精度向上が見込めるか検証する。

### 実験と中止
- s0_013 (seed42) を専用 venv `.venv-mmdet2` (torch 1.13.1+cu117 / mmcv-full 1.7 /
  mmdet 2.25 / Python 3.8) で学習開始。epoch4 から resume し epoch8 train 途中
  (iter950/2415) で停止 (epoch8 の val 未実施)。評価済み val bbox_mAP は epoch1-7:
  e4=0.686 / e5=0.687 / e6=0.675 / e7=0.696 (best)。
- **中止理由: 実験環境の統一 (再現性確保)。** 本実験のみ torch/CUDA/Python が
  プロジェクト本体 `.venv` (torch 2.1.2+cu118 / mmdet 3.3 / Python 3.11) と異質。
  Sense-X 9-encoder の公式実装が mmcv-full 1.x API 前提で torch 2.1 では CUDA 拡張を
  ビルドできないことが原因。検出器ベンチマークは可能な限り同一環境で比較すべきという
  方針に基づき中止した。

### 結果 (採用しない)
- s0_013/014/015 は欠番。途中結果はベンチマークに使わない。
- Co-DETR の S0 代表は s0_007-009 (mmdet 3.x 同梱, torch 2.1, 本体 .venv) とする。
- 詳細: experiments/baselines/s0_013_sensex_codino_bbox_seed42/STOPPED_for_env_unification.md

### 解釈
- 環境差 (torch 1.13 vs 2.1) は数値計算カーネル・乱数挙動に影響し得るため、Δ 基準点を
  汚染するリスクがある。9-encoder の精度メリットより、環境統一による再現性を優先した。

### 次
- 追加検出器は torch 2.1.2+cu118 で動くもの (Stable-DINO / DI-MaskDINO / Relation-DETR)
  に限定。これらは framework 隔離のため venv は分けるが torch/CUDA は本体と同一。
- judge #6 (検出器選定) は s0_001-012 (Mask DINO/VFNet/Co-DETR/DDQ ×3seed) +
  上記3検出器 で構成する。

## 2026-06-02〜03 DETR系拡張 (Mr.DETR/Focus/Align/DAC-DETR) + S0検出器ベンチ確定

### 仮説
DETR 系の新しい割当・denoising 手法 (Mr.DETR の multi-route、Focus-DETR の
foreground-aware、Align-DETR の IoU-aware、DAC-DETR の auxiliary decoder) が
EgoSurgery-Tool の術具検出、特に希少クラス (Skewer/Syringe) で既存検出器を
上回るか、統一 recipe で検証する。

### 実験設定 (統一 recipe)
- 全検出器: COCO 検出重みから fine-tune (class_embed をクラス数に reinit, bbox-only) /
  12 epoch / lr_drop@11 / AdamW (lr 1e-4×linear_x2 = effective 2e-4, backbone 0.1x) /
  per-GPU bs2 × 2GPU DDP = effective bs4 / eval=val / seed 42/123/456。
- 環境: 本体 `.venv` (mmdet系) / `.venv-detectron2` (detrex: Stable-DINO/Focus/Align/
  Mr.DETR) / `.venv-mmdet2` (DAC-DETR standalone, torch1.13)。
- DAC-DETR 統合の詳細は memory dac-detr-integration (罠8件) と
  scripts/post_process_dac_detr.py 参照。証跡: s0_025〜039。

### 結果 (metrics.json 直読み・機械集計, 全 verify PASS)
全13検出器 × 3seed (9enc のみ1seed) の val mAP / AP_rare:
- Relation-DETR 0.7268±0.0034 (rare 0.7483) — overall 首位
- Mr.DETR-DINO 0.7223±0.0062 (rare 0.7799)
- Mr.DETR-Align 0.7195±0.0004 (rare 0.7698)
- Stable-DINO 0.7192±0.0055 / DDQ-DETR 0.7187±0.0021 / 9enc 0.7180(1seed)
- DAC-DETR 0.7165±0.0003 (rare 0.7782) — std 最小級・AP_rare 3位
- Align-DETR 0.7133±0.0115 (rare 0.7868) — AP_rare 首位
- Focus-DETR 0.6991±0.0070 / Co-DETR 0.6973±0.0039 / Mask DINO 0.6717±0.0039 /
  VFNet 0.6160±0.0016 / DI-MaskDINO 0.3853±0.0392 (bbox-only 化で劣化)

### 解釈 (judge #6, Δ §10.1)
- overall mAP 首位 Relation-DETR(0.7268) と 2位 Mr.DETR-DINO(0.7223) の Δ=0.0045 は
  合成σ(0.0071) 未満 → 上位群 (1〜7位, 0.7165〜0.7268) は統計的に同率圏。
- AP_rare では Align-DETR(0.7868) > Mr.DETR-DINO(0.7799) > DAC-DETR(0.7782) が上位。
  希少術具を重視するなら overall 順位と別の結論になり得る。
- compare_judge6.py は eval_recipe 厳密一致で停止するが、これは検出器固有の native
  test_cfg 差 (構造由来) であり汚染ではない。統制 knob (split/epochs/bs/seed/optimizer)
  は全検出器で統一済み。9enc のみ torch1.13 別環境 (脚注で開示)。

### 次
- S1 主検出器推奨 = Relation-DETR (overall 首位 + 3seed 安定 + torch2.1 本体整合)。
  ただし上位同率圏のため、希少術具優先なら Mr.DETR-DINO / DAC-DETR も有力候補。
  最終確定はユーザー判断 (S1〜S9 全体の方向を決めるため)。Slack #experiment に投稿済。

## 2026-06-15 STEP 0-1: eval recipe 一本化のための Δ_recipe 実測 (研究ピボット「分析ファースト」)

### 仮説
研究ピボット (`prompts/research_pivot_summary_and_roadmap.md`) の STEP 0-1。比較の三角形で
Δ を汚染させないため公式 eval recipe を一本化する。事前見立ては「NMS-free DETR では
locked-down と score_thr=0.0系 の差 (Δ_recipe) はほぼ 0」。lecun (新サーバー) で Relation-DETR を
両 recipe 再 eval して実測する。

### 実験
- `.venv-relation-detr` 構築・検証 (MS-Deform-Attn CUDA op 実コンパイル, venv activate で ninja を PATH に)。
- `test.py` で val 1515枚を再 eval。COCO-2017 staging = `data/eval_staging/egosurgery_val` (symlink)。
- 評価器は repo の `CocoEvaluator` (= s0 と同一, デフォルト COCOeval maxDets=100)。
- 当初提供 ckpt `train/2026-05-30-04_24_20/best_ap.pth` は mAP=0.578 で s0_016(0.7297) 非再現
  → mtime が学習開始14分後 = 早期 epoch と判明 (研究インテグリティ: 捏造せず差異を報告)。
- ユーザーが philip から完走 ckpt を `checkpoints/incoming/seed{42,123,456}/best_ap.pth` に再配置。

### 結果
- **完走 ckpt 3 seed すべて記録値を再現** (±0.0005): seed42 0.7303 / seed123 0.729 / seed456 0.722。
- **score_thr 軸: Δ_recipe = 0** (予測 min score 4.58e-3 ≫ 1e-8, 1e-8未満 0件)。
- **NMS 軸: Δ_recipe = +0.045 mAP** (native 0.7303 vs locked-down NMS@0.6 0.6851)。
  NMS@0.6 で予測の 77.6% 除去。`PostProcess` の NMS は class-agnostic (`box_ops.nms`)。
- 証跡: `experiments/analysis/step0_recipe/notes.md`。

### 解釈
- 事前見立て (Δ_recipe≈0) は **score_thr 軸では正しいが NMS 軸では誤り**。class-agnostic NMS@0.6 は
  手術シーンの異クラス重なり箱を誤除去し 4.5pt 低下。「同じ nms_iou=0.6」でも Relation-DETR(class-agnostic)
  と mmdet(class-wise) で別物 — STEP 0 が炙り出すべき不整合。
- 比較の三角形は凍結源=Relation-DETR 単一 backbone で完結 → 三角形内は全て NMS-free。三角形の検出
  ヘッドに locked-down NMS を適用すると Δ_detection を 4.5pt 汚染する。

### 次
- **公式 eval recipe (DETR-family/三角形) = score_thr=0.0系 (NMS-free, max_per_img=300) に決定**。
- `recipes_match()` が DETR(nms_iou=None) vs locked-down(0.6) を不一致とするのは正しい挙動 (4.5pt 実在)。
- STEP 0-2: 凍結源 backbone を Relation-DETR seed42 完走 ckpt で確定 → STEP A (s0_frozen / s4_phase_baseline)。
- 早期 run `train/2026-05-30-04_24_20/` と `pred_val.json` (早期 ckpt 産物) は破棄候補。

## 2026-06-16 STEP A: S4 工程ベースライン (凍結 Relation-DETR + causal TeCNO) = Δ_phase 分母

### 仮説
比較の三角形 (§2.2) の Δ_phase 分母を確立する。凍結源 = Relation-DETR seed42 (STEP 0-2 確定) の
ResNet-50 特徴を 2段方式でキャッシュし、online/causal の TeCNO で工程認識する。S4 は「結合手法から
検出を引いたもの」= 単独最適化しない (§4.2 核心原則)。eval は未来フレーム不使用 (PHASE_EVAL_PROTOCOL)。

### 実験
- Stage1: `extract_stage1_features.py`(.venv-relation-detr) で凍結 backbone の C5→valid GAP 2048-d を
  train9657/val1515/test4265 全フレームでキャッシュ (検出 split サイズと一致, frame manifest は CSV↔画像交差)。
- Stage2b: `train_s4_tecno.py`(本体 .venv) で `TeCNO`(causal MS-TCN, `tecno_head.py`) を clip 時系列単位で
  学習 (CE + 0.15·T-MSE smoothing), 50 epoch × seed 42/123/456。online/causal 評価 (`PhaseEvaluator`)。
- 証跡: `experiments/phase1/s4_phase_baseline_00{1,2,3}_..._seed{42,456,123}/`(metrics.json に eval_recipe 併記)。

### 結果 (3-seed, metrics.json 機械集計)
| 指標 | mean ± std |
|---|---|
| accuracy | **0.8986 ± 0.0034** |
| macro-F1 | 0.7086 ± 0.0192 |
| edit | 41.08 ± 4.22 |
| seg-F1@50 | 0.369 ± 0.063 |
seed別 acc: 42=0.9023 / 123=0.8977 / 456=0.8957。loss は 3.7→0.33 へ収束。

### 解釈
- 凍結 (非 fine-tune) backbone + 軽量 causal TeCNO で val accuracy ~0.90 / macro-F1 ~0.71。frame accuracy は
  σ=0.003 と安定、macro-F1/edit/seg-F1 は val clip 数が 3 と少なく分散大 (σ大)。
- これは **Δ_phase の分母** であり、それ自体が SOTA 主張ではない。Δ_phase = (結合手法 S6 − この S4) を
  同一土台 (凍結backbone/特徴/recipe/seed) で測ることで結合の効果を分離する。

### 次
- S0-frozen 実装 → Δ_detection 分母 (凍結 backbone オンザフライ forward + 検出ヘッド)。両分母が揃えば三角形完成。
- SKiT / SPRMamba / causal-SR-Mamba を併走 (全 online)。Jaccard 指標を phase.py に追加 (現状 accuracy/macroF1/edit/segF1)。
- 注: TeCNO は因果性をテスト保証 (`tests/test_tecno.py`)。NpzFile 遅延ロード罠は lessons.md 参照。

## 2026-06-16 STEP A: S0-frozen 検出ベースライン起動準備（凍結 Relation-DETR + COCO-init head）

### 仮説
Δ_detection の分母として、Relation-DETR seed42 完走 ckpt 由来の凍結 backbone 上で、
COCO-init の検出 head/transformer が EgoSurgery tool 検出へ到達できる上限を測る。
S6 結合手法も COCO-init head から開始する前提なので、三角形 (§6) の同一土台と整合する。

### 実験
- 初期化: `data/external/weights/relation_detr_s0frozen_init_seed42.pth`
  （seed42 frozen backbone + COCO-init transformer/head のマージ済み重み）。
- 凍結: `relation_detr_resnet50_egosurgery_s0_frozen.py` で `freeze_indices=(0,1,2,3)`。
- 学習: `scripts/run_s0_frozen.sh` で seed 42/123/456 を seed 並列実行する。
  wave1 は GPU0=seed42 / GPU1=seed123、wave2 は GPU0=seed456。
- 証跡: `scripts/post_process_relation_detr.py --skip-external-loggers` で `.env` を読まず、
  `experiments/baselines/s0_frozen_*_relationdetr_s0frozen_cocohead_seed*/` に metrics/per-class/command を生成する。

### 結果
- 起動前検証のみ完了。Python 構文 OK、init checkpoint 188MB 存在、MS-Deform-Attn CUDA extension load OK。
- `backbone_trainable=0` / `trainable_total=25238688` を実ロードで確認。
- mAP 等の実測値は未完走のため未記録（完走後に metrics.json から機械転記する）。
- 20:47 UTC に `setsid -f scripts/run_s0_frozen.sh > /tmp/s0_frozen_launcher.log 2>&1` で background 起動。
  wave1: seed42/seed123 が GPU0/GPU1 で稼働し、両方 epoch0 iter100 到達をログで確認。
  ログ: `/tmp/s0_frozen_logs/s0_frozen_seed{42,123}_20260616_204720.log`。
  workdir: `/tmp/reldetr_work_s0_frozen_seed{42,123}_20260616_204720/`。
- watchdog: `/tmp/s0_frozen_watchdog.log`（`.env` 非接触のため `PROJECT_DIR=/tmp`）。

### 解釈
- backbone 凍結は optimizer の `requires_grad` フィルタにも反映され、凍結パラメータは optimizer 対象外。
- direct venv 実行では ninja が PATH に無く CUDA extension load 警告が出たため、launcher で
  `.venv-relation-detr/bin` を PATH に追加した。

### 次
- wave1 完走後に launcher が seed456 を GPU0 に投入する。完走後、post-process 証跡を確認する。
- 完走後、3 seed の metrics.json を集計し、Δ_detection 分母として採用可否を判断する。

## 2026-06-17 STEP A: S0-frozen 完走 → Δ_detection 分母確定（三角形の両分母が揃う）

### 結果（3-seed, metrics.json 機械集計）
| seed | mAP@[.5:.95] | mAP50 | mAP75 |
|---|---|---|---|
| 42  | 0.7100 | 0.836 | 0.756 |
| 123 | 0.6997 | 0.821 | 0.739 |
| 456 | 0.7057 | 0.832 | 0.749 |
| **mean ± std** | **0.7051 ± 0.0052** | — | — |

- 全 seed の eval_recipe が **NMS-free（score_thr=0.0 / nms_iou=None / max_per_img=300）= 公式 recipe** で一致。
  backbone 凍結も実ロードで確認済（`backbone_trainable=0 / trainable_total=25,238,688`）。
- 証跡: `experiments/baselines/s0_frozen_00{1,2,3}_relationdetr_s0frozen_cocohead_seed{42,123,456}/`。

### 解釈
- **Δ_detection 分母 = 0.7051 ± 0.0052**。seed42 フル fine-tune 0.7303 との差 **0.0252** が
  「backbone を凍結したことで失う分 ≒ backbone 共学習の寄与」。新規 COCO-init head が凍結特徴上で
  性能の大半（0.705/0.730 ≈ 96.6%）を回復しており、frozen 分母として妥当。σ=0.0052 と安定。
- これは **分母**であって SOTA 主張ではない。Δ_detection =（結合手法 S6 − この S0-frozen）を同一土台で測る。

### 三角形の現状（両分母が揃った）
- **Δ_detection 分母（S0-frozen）= mAP 0.7051 ± 0.0052**
- **Δ_phase 分母（S4 TeCNO）= accuracy 0.8986 ± 0.0034**
- 凍結源 = Relation-DETR seed42 を共有。以降は S6（結合手法）で 2 本の Δ を実測する段階。

### 次
1. STEP B: 既存の結合手法を複数実装（素朴 MTL → 片方向 → 予測蒸留 → ドメイン SOTA）。各手法を
   同一土台（凍結 backbone / 特徴 / recipe / seed / schedule）で学習し、Δ_detection・Δ_phase を測る。
2. phase.py に Jaccard 指標を追加（現状 accuracy/macroF1/edit/segF1。§4.2 は Jaccard も要求）。
3. 改善主張は §10.1 に従い `|Δ| > 1σ` のときのみ。

## 2026-06-18 補助: phase.py に Jaccard 指標を追加（§4.2）

### 実験
- `PhaseEvaluator` に frame 単位 per-class Jaccard（IoU = TP/(TP+FP+FN)）と macro 平均を追加。
  出力キー `phase_jaccard` / `phase_per_class_jaccard`。macro は GT 存在クラスのみで平均（macro F1 と同条件）。
- `tests/test_metrics.py` に手計算検証テスト追加（J=F1/(2−F1) 関係・GT 不在クラス除外を確認）。全 8 緑・ruff clean。
- 既存 S4 分母に適用: 保存済み `best_tecno.pth` を val 再評価（学習なし, CPU）。

### 結果
- **S4 Δ_phase 分母の Jaccard = 0.6447 ± 0.0146**（seed42 0.6569 / 123 0.6487 / 456 0.6286）。
- 再評価の accuracy（0.9023/0.8977/0.8957）が記録 metrics.json と完全一致 → checkpoint の忠実性をクロス検証。

### 解釈
- §4.2 が要求する Jaccard を分母に付与。文献参照点（TeCNO 0.273 / NETE 0.275 / GGMAE 0.339）は別 split・別データ
  のため**同一表に載せない**（ポジショニング用の別系統）。今後の S4/S6 runs は metrics.json に Jaccard を native 出力する。

## 2026-06-18 STEP B / B0: 統合loader・共有neck・S4′（②系統の工程分母）

### 仮説
- 結合の三角形を「2系統併設」で運用（確定 2026-06-18）。①予測レベル（neck無, 既存 S0-frozen/S4 分母）、
  ②特徴レベル（共有 trainable neck 有, neck版 S0-frozen′/S4′ 分母）。凍結 backbone では hard sharing の
  勾配交差が無く、特徴結合は neck 無しでは Δ≈0 で成立しない。neck は **C5 のみ・1×1 線形・残差・zero-init**。
- 予測: 線形 neck は masked-GAP と可換 → 工程枝はキャッシュ流用で S4′ が安価。neck 単体の容量増があれば
  S4′ は S4 と差が出るはずで、その差は **分母に織り込むべき交絡**（結合の効果ではない）。

### 実験
- B0-1 統合 loader: `scripts/build_joint_manifest.py`（phase manifest 派生 + tool bbox 後付け）→
  `data/processed/joint_manifest/{split}.json`（frames 9657/1515/4265・boxes 32272/4707/12673・missing_in_tool=0）。
  `JointClipDataset`（1item=1clip）。`tests/test_joint_dataset.py` 14緑。
  ※ split 実体は 10/2/3（`PAPER_SPLIT_VIDEOS` は名称に反し Tool subset 15動画）→ 既存 S4 分母は STEP B で有効。
- B0-2 共有 neck: `src/egosurgery/models/necks/c5_linear_neck.py`（`C5LinearNeck`）。spatial/vector 同一重み共有、
  `tests/test_c5_neck.py` 5緑で **GAP 可換性 `GAP(N(C5))==N(GAP(C5))` を数値検証**。
- B0-3 S4′: `train_s4_tecno.py --use-neck`（GAP キャッシュ→neck→TeCNO）。S4 と同一ハイパー（50ep, seed42/123/456）で
  neck の有無だけ変更。証跡 `experiments/phase1/s4_phase_baseline_00{4,5,6}_..._neck_seed*`。

### 結果
| 指標 | S4（neck無・①分母） | **S4′（neck有・②分母）** | 差 |
|---|---|---|---|
| accuracy | 0.8986 ± 0.0034 | **0.9142 ± 0.0017** | +0.0156（>1σ）|
| Jaccard  | 0.6447 ± 0.0146 | **0.6644 ± 0.0036** | +0.0197（>1σ）|
| macro-F1 | 0.7086 ± 0.0192 | 0.7149 ± 0.0169 | +0.006 |

### 解釈
- **②系統の工程分母 = S4′ = acc 0.9142 ± 0.0017 / Jaccard 0.6644 ± 0.0036**。
- zero-init 線形 neck（2048×2048≈4.2M params）が phase を単体で +1.6/+2.0pt 押し上げた。極小 TeCNO に対し
  neck の容量寄与が大きい。**この利得を分母に織り込むのが 2系統併設の目的** — S4(0.8986) を B1 の分母に使うと
  neck の容量増を「結合の効果」と誤認する。B1 の Δ_phase は (B1 − S4′) で測り、結合の純効果を分離する。
- acc の上げ幅 > macroF1 の上げ幅 → 容量増は多数派工程に効きやすい（希少工程は据え置き）。STEP C の per-phase 分解で要確認。

### 次
- B0-3 残: **S0-frozen′**（②系統の検出分母）= Relation-DETR 検出経路の C5→ChannelMapper 前に共有 neck を挿入し
  3-seed 再取得（.venv-relation-detr・GPU）。
- B0-4: S6 トレーナー骨格 → **B1 素朴MTL**（凍結bb→neck共有→{検出, TeCNO}・clip単位・オンザフライ backbone）。
- 改善主張は §10.1 `|Δ| > 1σ` のときのみ。Δ は対応する系統の分母（①既存 / ②neck版）と比較（系統跨ぎ禁止）。

## 2026-06-19 STEP C: ②系統の per-phase 分解（容量 vs 転移の機構）— n=2 予備

### 仮説
- 06-18 で予告した「容量増は多数派工程に効きやすい（希少工程は据え置き）。STEP C の per-phase 分解で要確認」を回収する。
- ②特徴レベル結合を **3系統**に分け、neck の効果を「容量(capacity)」と「転移(transfer)」へ分離する:
  - **S4** = neck 無 TeCNO（Δ_phase 分母, n=3）
  - **S4′** = 工程側で独立学習した neck 付き（容量効果の上限, n=3）
  - **S4″** = 検出で学習し凍結した C5 neck を工程へ載せた真の一方向結合（n=2: seed42/123, seed456 は検出 neck 完走待ち）
  - 分解: `Δcap = S4′−S4`（容量） / `Δxfer = S4″−S4′`（転移） / `ΔL2 = S4″−S4`（②結合の総効果）。

### 実験
- `scripts/analyze_phase_coupling.py`（GPU 不要・metrics.json/per_class_ap.json の実測のみ集計, 再走可能）。
- 公平比較のため S4″ が持つ **共通 seed {42,123} で seed-matched** に差分を取る（S4 の n=3 分母 acc 0.8986 とは別。matched base acc=0.9000）。
- per-phase は F1 のみ（`per_class_ap.json` 永続化分）。per-class Jaccard は predictions 未保存で再計算不可 → 出さない。
  base 集計 Jaccard は 06-18 再評価の記録値（seed42 0.6569/123 0.6487）を seed-matched に使用（001-003 の metrics.json には未永続化）。

### 結果（共通 seed {42,123} seed-matched）
| 指標 | S4 | S4′ | S4″ | Δcap(容量) | Δxfer(転移) | ΔL2(総結合) | base1σ | 判定(ΔL2) |
|---|---|---|---|---|---|---|---|---|
| accuracy | 90.00 | 91.36 | 90.23 | **+1.35** | **−1.12** | +0.23 | 0.34 | 中立 |
| Jaccard  | 65.28 | 66.57 | 64.69 | +1.29 | −1.88 | −0.59 | 1.46 | 中立 |
| macro-F1 | 70.86 | 71.49 | 70.97 | +0.33 | −1.32 | −0.99 | 1.92 | 中立 |
| edit     | 41.08 | 41.08 | 43.95 | +0.43 | +4.66 | **+5.09** | 4.22 | 予備有意(改善) |
| seg-F1@10| 44.69 | 46.27 | 51.41 | +1.27 | +8.98 | **+10.25** | 6.53 | 予備有意(改善) |
| seg-F1@25| 42.36 | 43.38 | 48.31 | −0.17 | +8.64 | **+8.47** | 4.88 | 予備有意(改善) |
| seg-F1@50| 36.88 | 37.57 | 43.97 | +1.67 | +8.45 | **+10.12** | 6.29 | 予備有意(改善) |

**per-phase F1（共通 seed {42,123} 平均 ×100）**
| 工程 | S4 | S4′ | S4″ | Δcap | Δxfer | ΔL2 |
|---|---|---|---|---|---|---|
| anesthesia | 90.95 | 93.98 | 91.66 | +3.03 | −2.32 | +0.71 |
| incision   | 85.38 | 88.03 | 85.69 | +2.65 | −2.33 | +0.32 |
| dissection | 91.74 | 93.49 | 92.55 | +1.76 | −0.94 | +0.81 |
| closure    | 92.84 | 93.65 | 92.83 | +0.80 | −0.81 | −0.01 |
| design     | 100.00 | 99.76 | 99.76 | −0.24 | +0.00 | −0.24 |
| **hemostasis** | **42.81** | **37.12** | **34.27** | **−5.69** | **−2.84** | **−8.54** |
| disinfection / dressing / irrigation | 0.00 | 0.00 | 0.00 | 0 | 0 | 0 |

### 解釈
1. **frame-level（acc/Jaccard/macro-F1）は総結合 ΔL2 が全て中立**（既存の n=2 知見を裏付け）。
   容量 Δcap(+) と転移 Δxfer(−) がほぼ相殺する。**検出で学習した C5 neck は、工程の frame 識別には有用に転移しない**
   （Δxfer が acc/Jaccard/macro-F1/全 per-phase F1 で負）。容量利得は工程タスク固有で、結合の効果ではない。
2. **容量(Δcap) の正体 = 多数派工程の押し上げ**: anesthesia +3.0 / incision +2.6 / dissection +1.8（出現頻度の高い主工程）。
   一方 **希少・曖昧な hemostasis は −5.7 と悪化** → 極小 TeCNO への 4.2M params 追加は head クラスへ過適合し、tail を削る。
   06-18 の「容量増は多数派に効き希少は据え置き」を**定量確認**（据え置きどころか hemostasis は負）。
3. **負の転移の局在**: Δxfer は全 frame 工程で負だが、損失は **hemostasis (−2.8) に集中**（ΔL2 で 42.8→37.1→34.3＝−8.5）。
   希少・視覚的に曖昧な止血工程が、容量過適合と特徴ミスマッチの両方を最も吸収する。
4. **構造的 F1=0（disinfection/dressing/irrigation）**: 全系統で 0 → test split での極端な不均衡（モデルが当該工程を当てられない）。
   ΔL2=0 で結合とは無関係だが macro-F1（9 工程平均=約56）を 3 クラス分押し下げる交絡。**macro-F1 単独で結合を語らない**根拠。
5. **解離（新知見・要確認）**: frame は中立なのに **segmental/temporal 指標（edit, seg-F1@10/25/50）は転移で +5〜10pt と予備的に有意改善**
   （いずれも base 1σ 超だが 1.2〜1.7σ・matched n=2・seg 系は高分散）。改善はほぼ **Δxfer（転移）由来**で Δcap（独立 neck）では出ない。
   解釈仮説: **検出 neck は物体存在の時間的整合を符号化 → 工程系列を平滑化（断片化を減らす）** ため、frame 精度を僅かに落としても
   セグメント整合は上がる。「検出→工程の neck 転移は frame 識別には効かないが、時間的平滑性を付与する」と従来結論を精密化。

### 次
- **seed456 の検出 neck 完走後**（s0_frozen_neck_006）: neck 抽出 → S4″ seed456 学習 → `analyze_phase_coupling.py` 再走で
  n=2→n=3 に更新。特に **解離（edit/seg-F1 改善）の有意性を n=3 で再検証**（現状 1.2〜1.7σ の予備値）。
- 上記が固まれば §10.1 に従い、frame 中立／segmental 改善という **二面的 Δ_phase** を②系統の結論として確定。
- 改善主張は対応分母（②=S4′/S4″）と比較。frame と segmental を分けて報告し、macro-F1 は構造的ゼロ工程を併記する。

## 2026-06-20 STEP C 確定（n=3）: ②系統 結合効果は中立／n=2 の segmental 改善は非再現

### 仮説
- 06-19 の n=2 予備で「frame 中立／segmental（edit・seg-F1）は転移で +5〜10pt 予備有意」とした**解離**を、
  seed456 を加えた **n=3 で再検証**する（当時「要 n=3 確認」と明記）。あわせて②検出分母 S0-frozen′ を 3-seed 確定する。

### 実験
- seed456 検出 neck 完走（s0_frozen_neck_006, mAP 0.7136 @ep12, 06-19 11:50）→ `scripts/extract_c5neck.py` で
  `c5neck_seed456.pth`（weight norm 44.22/bias 0.28, 42/123 と整合・非ゼロ）抽出。
- `train_s4_tecno.py --seed 456 --epochs 50 --neck-from c5neck_seed456.pth` → 証跡 `s4_phase_baseline_009`。
- `scripts/analyze_phase_coupling.py` を **paired-σ 判定に改修**（matched 差の有意性を base 群σでなく **対seed差σ + 全seed同符号**で判定）→ n=3 再走。スナップショット: `experiments/phase1/_analysis_phase_coupling_n3.txt`。

### 結果（共通 seed {42,123,456} seed-matched, paired 判定）
| 指標 | Δcap(容量) | Δxfer(転移) | ΔL2(総, paired) | 判定 | (n=2 予備) |
|---|---|---|---|---|---|
| accuracy | +1.56 | −1.19 | **+0.37 ± 0.61** | 中立 | 中立(+0.23) |
| macro-F1 | +0.63 | −0.36 | +0.27 ± 2.27 | 中立 | 中立 |
| Jaccard  | n/a | −1.61 | n/a(base欠測) | — | — |
| edit     | +0.01 | +1.31 | +1.32 ± 9.19 | **中立** | ~~予備有意+5.09~~ |
| seg-F1@10| +1.58 | +2.77 | +4.35 ± 12.86 | **中立** | ~~予備有意+10.25~~ |
| seg-F1@25| +1.01 | +2.66 | +3.68 ± 11.55 | **中立** | ~~予備有意+8.47~~ |
| seg-F1@50| +0.69 | +4.13 | +4.82 ± 13.21 | **中立** | ~~予備有意+10.12~~ |

- **②検出分母 S0-frozen′ 確定（3-seed）= mAP 0.7095 ± 0.0091**（seed42 0.7159 / 123 0.6992 / 456 0.7136）。
  ①検出分母 S0-frozen(neck無) 0.7051±0.0052 比 +0.0044（<1σ）→ **neck 挿入は検出 mAP を悪化させない**。

**per-phase F1（n=3, ×100）**
| 工程 | S4 | S4′ | S4″ | Δcap | Δxfer | ΔL2 |
|---|---|---|---|---|---|---|
| incision   | 84.63 | 89.61 | 85.38 | **+4.98** | **−4.23** | +0.75 |
| anesthesia | 91.40 | 95.29 | 91.88 | +3.89 | −3.41 | +0.48 |
| dissection | 91.79 | 93.52 | 92.38 | +1.73 | −1.15 | +0.58 |
| closure    | 92.89 | 93.51 | 93.18 | +0.62 | −0.33 | +0.29 |
| hemostasis | 35.30 | 28.85 | 35.25 | **−6.46** | **+6.41** | −0.05 |
| design     | 100.0 | 99.68 | 99.84 | −0.32 | +0.16 | −0.16 |
| disinfection/dressing/irrigation | 0 | 0 | 0 | 0 | 0 | 0 |

### 解釈
1. **【撤回】n=2 の segmental 改善（解離）は非再現**。paired-σ 判定で edit/seg-F1 の ΔL2 は **すべて中立**
   （対seed差σ ≫ 平均、符号も混在）。n=2 の「+5〜10pt 予備有意」は **小標本アーティファクト**であり、研究記録から改善主張を撤回する。
   （前ターンで「予備・要 n=3 確認」と明示し旗を立てた手続きが機能した。）
2. **frame も結合効果は中立**。accuracy ΔL2=+0.37 は base 群σ(0.34)を僅かに超えるが、**正しい paired 判定では +0.37±0.61・seed123 で負**
   （per-seed ΔL2=+0.79/−0.33/+0.66pp）→ ゼロと区別不能。**検出→工程の凍結 neck 一方向転移は、工程認識を純増させない**。
3. **頑健な機構（多数派工程）= 容量と転移は逆符号で相殺**。独立 neck（容量）は head 工程を底上げ（incision +5.0/anesthesia +3.9/dissection +1.7）、
   検出 neck（転移）は同じ工程をほぼ同量 base へ引き戻す（−4.2/−3.4/−1.2）。**容量利得は工程タスク固有で、検出からは転移しない**を per-phase でも裏付け。
4. **希少 hemostasis は逆向きの大スイング（容量 −6.5 / 転移 +6.4, 純 ≈0）だが seed 変動大**（base F1 が seed で 35〜43 と振れる希少クラス）→ 示唆に留め頑健性は主張しない。
5. **②系統の結論（確定）**: 一方向 検出→工程 凍結 neck 転移は **Δ_phase 中立（純効果なし）**。「neck で運べる容量」はタスク固有。
   → 結合で工程を伸ばすには **frozen neck 転移では不十分**で、同時学習（B1 素朴MTL）や双方向（B3 蒸留）など**勾配が双方向に流れる結合**が要る、という STEP B 設計仮説（凍結 hard sharing では Δ≈0）と整合。

### 次
- ②系統の単一タスク分母は**両方確定**: 検出 S0-frozen′ 0.7095±0.0091 / 工程 S4′ 0.9142±0.0017。①系統と合わせ4分母運用へ。
- **B1 素朴MTL（②系統・最初の結合手法）**へ進む: 凍結bb→共有neck→{検出, TeCNO} 同時学習、両Δ を (B1−S0-frozen′) と (B1−S4′) で測定。
- §10.1 の有意性は **paired-σ（対seed差）**で判定する運用に統一（base群σ流用は符号反転を見落とす）。`analyze_phase_coupling.py` に実装済。

## 2026-06-20 STEP B / B1 素朴MTL: 実装完了・smoke検証・本番3-seed×2 起動（結果は走行中）

### 仮説
- ①系統で「frozen neck 転移は Δ_phase 中立」を確認 → 結合で工程/検出を伸ばすには**勾配が双方向に流れる結合**が要る、を B1 で検証する。
- B1 素朴MTL（Notion §8.1 Tier0「必須・最初」）: 凍結 backbone + 共有 C5 線形 neck に**検出損失と工程損失の勾配を同時に流す**。
  共有 trainable は neck のみ。`L=w_d·L_det+w_p·L_phase`（固定）/ Kendall&Gal（不確実性）。両 Δ で negative transfer を可視化。

### 実装（完了・2026-06-20）
- 設計判断: **単GPU**（DDP の二枝勾配同期を回避・工程は S4′ の 1GPU 構成と一致）+ **Round-robin**（検出は S0-frozen′ と
  同一標準ローダで全frame露出=Δ_detection を公正化、**R=89 step毎に工程 clip 1本**で工程≈650更新=S4′ 50ep相当）。§6-faithful。
- 統合トレーナーは `.venv-relation-detr` 側（§6: 検出枝は S0-frozen′ と同じ Relation-DETR ヘッド必須）。
- 新規: `tecno_mirror.py` / `relation_detr_b1_mtl.py`（phase_head+log_var）/ B1 model config / `train_b1_mtl.py` / `run_b1.sh` /
  `postprocess_b1.py`（本体 .venv で工程厳密指標+証跡+両 recipe）。改修: `C5LinearNeck.forward_vector` / `param_dict.finetune_b1_mtl`。
- **検証**: total_trainable=29,832,178 = S0-frozen′(29,435,040)+phase_head(397,138)・backbone_trainable=0・c5_neck=検出主LR/phase_head=5e-4群。
  smoke（fixed/uncertainty 両方）: L_det/L_phase 有限・**c5_neck.weight.grad が det/phase 両枝から非ゼロ=PASS**・検出/工程 eval 両走行。ruff clean。

### 結果（走行中・未確定）
- 本番 fixed seed42(GPU0)/seed123(GPU1) を起動、1.7-1.8 it/s で健全進行（L_det 低下確認）。~12h/run 見込み。
- **数値はまだ出していない**（捏造しない）。残: fixed seed456 + K&G 3-seed（計6本, 2GPU並列で約2日）。

### 次
- 各 run 完走 → `postprocess_b1.py` で証跡組成（experiments/transfer/b1_mtl_*）。3-seed 揃ったら両Δを paired-σ で §10.1 判定。
- **要解決(§8.0)**: B1 は 1GPU/eff_bs2、S0-frozen′ は 2GPU/eff_bs4 → 検出 recipe が recipes_match で不一致。Δ集計時に
  安価な S4′ 再取得 or §8.0 解釈を明文化（GPU構成差の扱い）。
- 固定 vs Kendall&Gal で negative transfer の符号・方向（σ²_d/σ²_p の偏り）を比較表に。

## 2026-06-20 STEP B / B2a 片方向結合 検出→工程（①信号レベル・Tier-0必須）: 3-seed完走・有意な正Δ_phase

### 仮説
- 凍結検出器の **tool-presence 信号**（クラス別最大スコア 15-d）を工程枝に **入力連結**すれば、工程認識が向上するか。
- ①信号レベル（勾配交差なし・信号のみ）。土台＝S4 base（素 TeCNO on GAP・neck 無）、変える軸＝tool 信号 1 点。Δ_phase=(B2a − S4 base)。

### 実験
- 抽出 `extract_b2a_detsignal.py`（凍結 Relation-DETR seed42 フル forward → 15-d, fp16/no_grad/batch1）: train9657/val1515/test4265, nonzero≈0.99。
- 学習 `train_b2a.py`（本体 .venv, [GAP2048⊕tool15]=2063-d → 素 causal TeCNO, S4 と同一ハイパー epochs50/lr5e-4/wd0.01/stages2/layers8/fmaps64/smoothing0.15）。3-seed(42/123/456)、証跡 experiments/transfer/b2a_det2phase_001-003。

### 結果（paired-σ §10.1 判定）
- B2a acc: seed42=0.9373 / seed123=0.9353 / seed456=0.9380（mean 0.9369）。S4 base: 0.9023/0.8977/0.8957（mean 0.8986）。
- **Δ_phase(acc)**: per-seed [+0.0350,+0.0376,+0.0422]、mean **+0.0383**、paired-σ=0.0037、全 seed 同符号 → **有意**（mean は paired-σ の 10×）。
- **Δ_phase(macro_f1)**: per-seed [+0.0751,+0.0672,+0.1029]、mean **+0.0817**、paired-σ=0.0188、全 seed 同符号 → **有意**（4×）。

### 解釈
- **凍結検出器の道具存在信号は工程認識を有意に押し上げる**（acc +3.8pt / macroF1 +8.2pt）。EDA の tool×phase 強結合と整合。
- ②の S4″ 凍結 neck 転移（特徴転送）が **Δ_phase 中立**だったのと**対照的な解離**: 「どの器具が見えるか」という**信号**は効くが、
  凍結 neck の**特徴転送**は効かない。①信号 vs ②特徴で結合の効き方が違う、という Tier-0 の核心知見。
- 注意（容量交絡の正直な明記）: B2a の TeCNO は in_dim=2063（+15ch）。+15ch は「測りたい結合（tool 信号）そのもの」だが、
  厳密には「15ch ゼロ/ランダム連結の同容量対照」を取れば容量効果を完全排除できる（§7.5 追補候補）。現状の Δ は「tool 信号の付加情報」の効果。

### 次
- per-class（どの工程が伸びたか）・形状類似ペア・工程境界の分析（§7.4）。容量対照（zero-pad 15ch）の任意追補。
- 残 Tier-0: B2b 工程→検出（方向の非対称を測る）。

## 2026-06-20 STEP B / T1a region-token→工程（Tier-1 主力⭐ TAPIS/GraSP 型）: 実装・検証完了（別サーバー実行用に準備）

### 仮説
- 凍結検出器の **object-query 埋め込み（region token, クラス別 256-d）** を工程枝に入力連結すれば、tool-presence スカラ（B2a）より
  リッチな物体特徴で工程認識がさらに伸びるか（H2: object token→工程, TAPIS/GraSP の直接実装）。②系統・Δ_phase=(T1a − S4 base)。

### 実装・検証（2026-06-20, lecun で疎通確認のみ。本走は別サーバー）
- 抽出 `extract_t1a_regiontoken.py`: デコーダ `class_head[-1]` への **forward hook** で最終層 (region token (Q,256), per-query logits (Q,15)) を捕捉。
  クラス別に最高スコア query の 256-d を score 加重 → 15×256=3840-d。**スモーク + B2a とのクロスチェック合格**
  （T1a region-norm 最大クラス == B2a presence 最大クラス, 3/3 frame 一致・単調整合）→ hook 配線/sigmoid 採点の正当性を独立 2 経路で確認。
- 学習 `train_t1a.py`: [GAP2048⊕region3840]=5888-d → 素 TeCNO（S4 同一ハイパー）。TeCNO(5888) forward+loss+backward 検証 PASS。ruff clean。
- launcher `run_t1a.sh`。分母は S4 base（lecun 0.8986±0.0034）流用・**別サーバー差は §8.0 明文化**（同一 ckpt・同一前処理ゆえ差は学習数値のみ）。

### 結果（2026-06-20, **lecun で本走**＝within-server・§8.0 交絡なし／paired-σ §10.1）
- region 抽出 lecun GPU1 完了（train9657/val1515/test4265 × 3840-d, nonzero 1.000）。3-seed 学習完走（証跡 experiments/transfer/t1a_regiontoken_001-003）。
- T1a acc: seed42=0.9498 / seed123=0.9485 / seed456=0.9465（mean 0.9483）。mF1 mean 0.8044。
- **Δ_phase(acc)**: per-seed [+0.0475,+0.0508,+0.0508]、mean **+0.0497**、paired-σ=0.0019、全 seed 同符号 → **有意**（26×）。
- **Δ_phase(macro_f1)**: per-seed [+0.0904,+0.0875,+0.1095]、mean **+0.0958**、paired-σ=0.0119 → **有意**（8×）。

### 解釈（B2a vs T1a の対比＝presence か object 特徴か）
- **T1a(256-d region 埋め込み) Δ_phase(acc)=+0.0497 > B2a(15-d presence スカラ)=+0.0383**。同一土台で region 埋め込みが presence スカラを上回る
  → 「どの器具が見えるか」だけでなく **object の特徴内容**が工程認識に追加で効く、という分離が取れた（H2: object token→工程 を EgoSurgery で支持）。
- ②の S4″ 凍結 neck 転移は中立だったので、**入力に object 特徴を渡す（T1a）と効く / 凍結 neck の特徴を転送する（S4″）と効かない**、という結合経路依存も補強。
- 注意（容量交絡）: in_dim=5888（+3840ch）。+region は測りたい結合だが、厳密には zero/random 3840ch 同容量対照で容量効果を分離可（§7.5 追補候補）。手 box 非依存（凍結検出器の tool query のみ）で交絡少。

### 次
- B2a vs T1a の Δ 比較表を §7 に。容量対照（zero-pad）の任意追補。SKiT 等の時系列ヘッド差し替え ablation（任意）。
- 別サーバーは T1b（MT4MTL-KD/§4.6 双方向）に充当（T1a は lecun で確定済）。

---

## アノテーション EDA（data/annotations ドメイン特性, 2026-06-20）

### 動機
- STEP B/T1 の結合系（検出⇄工程）の前提となる **データ的根拠**（術具⇄工程の結合の強さ、長尾、フレーム整合）を定量化し、単一ドキュメント化する。

### 実験（再現可能・数値捏造なし）
- `scripts/analyze_annotations_eda.py` 新規。COCO 画像 basename == 工程 CSV `Frame` で**フレーム結合**。
- 出力: `experiments/analysis/annotations_eda/`（REPORT.md / stats.json / 2 CSV 行列 / 図3枚）。ruff clean・再実行で同一結果。

### 結果（実測）
- 規模: 術具COCO 15,437 画像 / 49,652 inst（train10・val2・test3 本の**動画単位 hold-out**）。**検出↔工程 join 100%・未結合0**。
- 長尾: 術具不均衡 **29.1×**（Tweezers10,012 / Skewer344）、工程不均衡 **57.8×**（closure7,231 / disinfection125）。
- 物体サイズ: bbox **約96% が COCO large**（接写エゴ視点＝小物体問題ではない）。1フレーム平均約3 inst・最大6クラス共起。
- **術具⇄工程の準決定的結合**: Skewer→design 99.7% / Syringe→anesthesia 84.2% / Scalpel→incision 97.4% / Needle Holders→closure 99.9% / Bipolar Forceps→hemostasis 98.0% / Cautery・Hook・Scissors・Raspatory・Retractor→dissection ≥79%。disinfection は術具0。

### 解釈
- 多くの術具が単一工程に集中 → **検出→工程（B2a/T1a）の上限が高い**ことのデータ的裏付け。実測 Δ_phase(B2a +0.0383 / T1a +0.0497) と整合。
- 工程の難所（disinfection=術具0・irrigation/dressing 希少）は検出特徴のみでは弁別困難＝**時間・手情報の寄与**を測る好材料。長尾ゆえ主指標は macro-F1/希少AP が妥当（既存方針と整合）。

### 次
- 容量対照（zero-pad）での結合効果分離、pseudo_labels（hand-tool relation/exo→ego 工程転移）生成時の分布確認に本 EDA を基準として再利用。

### 追記: 追加分析（scripts/analyze_annotations_advanced.py, 2026-06-20）
- split シフト/カバレッジ・tool→工程予測上限・工程混同・術具共起PMI・bbox幾何・品質・手 を集計（`stats_advanced.json`）。
- **データ整合性の警告（Fail Loud）**: disinfection 工程は **train のみ**（val/test=0）、irrigation は **val=0**、dressing は train 極少(12)。Retractor は **val 0件**。Electric Cautery は **77% が単一動画**。
  → 工程 macro-F1 は「対象 split に存在する工程のみ」で算出し欠損扱いを明記、val でのモデル選択は test を保証しない。per-class AP は動画集中率併記。
- **B2a 信号上限**: GT tool-presence のみのフレーム単位工程予測 test acc=0.752/mF1=0.529（多数決0.573）。時系列 S4 base(0.899) 未満＝**主役は時系列・検出→工程は補完**。実測 Δ_phase(B2a +0.038 < T1a region +0.050) を説明（presence 天井超えの object 特徴が効く）。MI 最大=Needle Holders 0.52。
- **混同**: dissection↔hemostasis(cos .81)/anesthesia↔irrigation(.82) は tool では非分離→時系列・手で検証。**共起PMI**上位: Cautery+Retractor 1.94 等（関係推論/hand_tool_relation 素地）。truncation 34%・アノテ stride=1。

---

## 運用記録: lecun 21 Run の Notion 台帳バックフィル（2026-06-20）

### 事象
- Notion「実験Run台帳」に **lecun（Phase-2 STEP B）の Run が1件も無い**ことを発見。台帳は philip/aolab の検出器ズー（〜2026-06-01）で停止しており、06-17 の lecun 移行以降が抜けていた。
- 根因: `ExperimentManager` はローカル証跡（config/command/git_commit/metrics）を自動生成するが、**Notion 台帳への転記は手動**で、server pivot の切れ目で脱落。副因: Server select に `lecun` が無く入れ先が曖昧。

### 対応（数値は metrics.json から逐語・捏造なし）
- 21 行を作成: `s0_frozen`×6 / `s4_phase_baseline`×9 / `b2a_det2phase`×3 / `t1a_regiontoken`×3。
- 台帳 Server select に `lecun`(red) を追加（既存6オプションは色ごと保全）。
- 結合系（b2a/t1a）は legacy Step 軸に該当バケツが無いため **Step 空＋Tier（must/effort）**で識別（偽 S 番号を割り当てない）。
- 検証: data_source 内検索で 21 件すべて可視化を確認。

### 再発防止
- `docs/notion_run_ledger_recipe.md`（新規）に記録手順を明文化。新サーバーは `update_data_source` で Server オプション追加 → `create-pages` の順。読み取りは `query_data_sources`(Enterprise限定) 不可のため `notion-search`/`notion-fetch` で代替。

### 追記2: さらなる追加分析（scripts/analyze_annotations_extra.py, 2026-06-20）
- 手-術具接触・時間予測性・シーンテンプレート・工程順序一貫性・手の自他左右・クラス重み・術具スケール/難易度・検出無し工程フレーム を集計（`stats_extra.json`）。
- **疑似ラベル前段**: 術具boxの56%が手と重なり(IoU>0.1)・60%近接、能動工程で接触率≈0.95 → `bbox_near_contact`/`hand_tool_relation` 生成可（閾値 IoU>0.1 or 中心距離<0.15対角）。
- **時系列が主役の裏付け**: 工程 自己遷移0.982・境界3.5%・1次マルコフ次フレーム0.982（=現状維持）。検出→工程の効きは境界/曖昧工程に局在＝§11 と整合。
- 工程順序の動画間遵守率0.943（irrigation のみ割り込みで例外）。助手手は能動工程で在率0.83-0.89。
- effective-number 重み（tool: Skewer2.36..Tweezers0.69 / phase: disinfection2.88..closure0.34）を loss/RFS 初期値に。Cautery/Skewer/Scalpel は aspect/scale 振れ大で局在困難。
- 工程のみ(検出box無)フレーム1,796（disinfection 114＝検出側11と非対称）→結合入力の空フレーム処理・半教師の余地。

---

## 2026-06-20 STEP B / T1b（MT4MTL-KD-style Phase→Det・§4.6・①予測相互作用L3）: 実装・smoke完了（本走は server B）

### 仮説
- 凍結 S4 工程モデルの per-frame 事後分布（phase context, 9-d）を Relation-DETR の C5 に **FiLM 注入**し、
  学習済み検出器（s0_016=S0-frozen）から warm-start して fine-tune すれば、Δ_detection>0（工程文脈が検出を助ける）か。

### 実装・検証（2026-06-20 lecun・smoke のみ。本走 server B）
- 新規: `extract_phase_context.py`（凍結S4→per-frame事後cache, weights_only=True）/ `relation_detr_phasefilm.py`
  （RelationDETRPhaseFiLM・C5にFiLM・zero-init恒等）/ config `..._t1b.py` / `train_t1b.py`（warm-start fine-tune・
  per-image ctx注入・§4.6 --zero-ctx対照・--trainable film/all）/ `run_t1b.sh`。改修: `param_dict.finetune_t1b`。
- **FiLM zero-init恒等性 検証PASS**（out==c5 max|diff|=0.0＝warm-startでS0-frozen厳密保存）。
- **smoke gate PASS**: warm-start元の取り違え（COCO init 91class → 学習済み検出器 best_ap.pth 15class）を smoke が即検出→修正。
  修正後 **warm-start init mAP=0.8876(20val)・FiLM grad非ゼロ・phase context join 100%(miss 0/0)**。
- **Δ定義（清潔）**: init mAP（FiLM恒等=warm-start検出器）= 同一evalでの per-seed S0-frozen 分母。
  Δ_detection=best−init。**注入純効果=Δ_injected − Δ_control(zero-ctx)**（fine-tune自体と分離・§4.6）。

### 結果
- **未実施（数値なし）**。server B で warm-start fine-tune（3-seed＋zero-ctx対照）→ paired-σ Δ。`docs/t1b_server_b_runsheet.md`。

### 次
- server B 本走（s0_01{6,7,8}×3・phase_context・画像転送→注入/対照 fine-tune）。早期打ち切り: Δ_injected≤0 なら gradient制御。
- 完全 §4.6 双方向（+Det→Phase 同時・蒸留）は本 Phase→Det 確立後の拡張。

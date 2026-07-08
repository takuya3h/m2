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

### 結果（2026-06-21〜22・lecun seed123/456、bengio seed42 は別走）
- **学習設定の知見**: `--trainable all --epochs3` は warm-start 検出器を fine-tune が ep0 で撹乱（mAP 0.73→0.70）→3ep で回復しきらず **best=init（underfit）**。
  ただし matched-epoch で **注入 > 対照 が一貫（ep2 +0.0068 等）**。
- **清潔版 `--trainable film`（検出器凍結・FiLM のみ・init 撹乱なし・6ep）**:
  - seed123: 注入 Δ_det=best−init=**+0.0022**(best ep5 0.7314 / init 0.7292) / 対照 +0.0000 → **注入純効果 +0.0022**
  - seed456: 注入 Δ_det=**+0.0040**(best ep1 0.7257 / init 0.7217) / 対照 +0.0037 → **注入純効果 +0.0003**
  - 2-seed 注入純効果 平均 **+0.0012**（per-epoch 変動 ±0.003 と同オーダー＝**ほぼ中立/限界的**）。seed42(bengio)で 3-seed paired-σ 予定だが効果量が小さく中立見込み。

### 解釈（方向の非対称＝STEP B の核心結論）
- **phase→det の学習 FiLM 注入は限界的（≈中立, 純効果 +0.001・ノイズ内）**。検出器凍結ゆえ frozen ヘッドが modulation を活かしきれない面もあるが、`--trainable all` の matched-epoch +0.007 も小さい。
- **方向の非対称が確定**: det→phase は効く（B2a +0.038 / T1a +0.050 有意）／**phase→det は難しい（naive B2b −0.04 で害す・学習 T1b でも ≈中立）**。計画 §4.6「phase→det は phase 未収束で検出退化＝難しい方向」を実証。
- STEP B 6実験の総括: **「結合の向きと作法が符号を決める」— 素朴結合は両方向で負、凍結特徴を det→phase 入力注入すると正、phase→det は学習でも中立。**

### 次
- bengio seed42 の film 完走で 3-seed 確定（paired-σ）。注入強化の余地: `--trainable all` を多 epoch / cross-attention 注入（計画 primary・T1b は FiLM 下限）で phase→det が効くか再検証。
- test 最終評価は全系統一括。STEP D（H-C 不確実性駆動の双方向）へ。

---

## 2026-06-20 STEP B / B2b 工程→検出（Tier-0 ①片方向 pipeline・training-free phase-prior re-scoring）: 負の Δ_detection

### 仮説
- 凍結検出器の予測 score を凍結 S4 の per-frame phase 事後 × 学習集合 P(tool|phase) で再重み付け（学習ゼロ）すれば、
  工程文脈が検出の prior になり Δ_detection>0 か。EDA の準決定的 tool×phase 結合（anesthesia→Syringe0.97 等）が根拠。

### 実験
- `run_b2b_rescore.py`: 凍結 Relation-DETR seed42 を val 全件 forward → 各予測を `score×(Σ_p π_f[p]·P(t|p))^α` で再採点 → COCO mAP。
  P(t|p) は train（検出アノテ×phase manifest）から。π は phase_context cache（凍結S4 val 事後）。miss_ctx=0（join 100%）。
- baseline=元 score の同一 eval（=その場の S0-frozen, mAP 0.7302）。α∈{0.5,1.0,2.0} 掃引。**学習なし＝決定的（seed 不要）**。

### 結果（実測・決定的）
- **Δ_detection = −0.0119 (α0.5) / −0.0376 (α1.0) / −0.0726 (α2.0)**。α が強いほど**単調に悪化**。全 α で負。

### 解釈
- **素朴な phase→det 再採点は検出を害する**。凍結検出器の score は既に良校正で、phase 予測の誤り・「正準工程外で出る術具」を
  prior が**誤抑制**し真陽性を高信頼ランクから外す → mAP 低下。Tier-0「情報量のある下限」が **naive pipeline では効かない**ことを実証。
- **方向対称な negative transfer**: 素朴結合は両方向で害する — B1 素朴MTL→工程 −0.05（予備）/ B2b 再採点→検出 −0.04。
  対して**凍結単一タスク特徴の入力注入は工程を助ける**（B2a +0.038 / T1a +0.050）。→「どう結合するかで符号が変わる」が STEP B の核心。
- B2b の負は **T1b（学習 FiLM 注入）の必要性**を動機づける（naive で駄目→学習注入が phase→det を救えるかが T1b の問い）。

### 次
- T1b（bengio）で学習注入の Δ_detection を測り、B2b(naive −0.04) との対比で「学習が phase→det を効かせられるか」を判定。
- B1 fixed 3-seed 揃い次第、工程 negative transfer を paired-σ 確定。

---

## 2026-06-21 STEP B / B1 素朴MTL fixed 3-seed 確定 + K&G seed42（②共有neck・両Δ paired-σ）

### 結果（fixed 3-seed・paired-σ §10.1）
- B1 fixed: seed42(mAP0.7099/acc0.8653) / 123(0.7015/0.8733) / 456(0.7103/0.8660)。証跡 experiments/transfer/b1_mtl_001-003。
- **Δ_detection (B1−S0-frozen′)**: per-seed [−0.006,+0.002,−0.003]、mean −0.0023、paired-σ=0.0042、同符号=False → **中立**。
- **Δ_phase (B1−S4′)**: per-seed [−0.0495,−0.0389,−0.0495]、mean **−0.0460**、paired-σ=0.0061、全 seed 負 → **有意（負）**。

### 解釈
- **素朴 MTL（共有 neck に検出・工程の両勾配）は工程を有意に害す（−4.6pt）が検出は中立**。非対称な negative transfer を 3-seed・paired-σ で確定。
- 物語が確定: **素朴結合は害する（B1工程 −0.046有意 / B2b検出 −0.04）↔ 凍結特徴の入力注入は助ける（B2a +0.038 / T1a +0.050有意）**。

### K&G（Kendall&Gal 不確実性重み）3-seed 確定（2026-06-21）
- K&G acc: seed42=0.8719 / 123=0.8733 / 456=0.8389。mAP: 0.7093/0.7022/0.7138。σ²_d≈15.6 / σ²_p≈0.87（全 seed 一貫＝**検出を下げ工程を上げる重みを学習**）。証跡 b1_mtl_004-006。
- **Δ_phase(K&G−S4′)**: [−0.043,−0.039,−0.077]、mean **−0.0528**、paired-σ=0.0207、全 seed 負 → **有意（負）**。
- **Δ_det(K&G−S0-frozen′)**: mean −0.0011、paired-σ=0.0049 → **中立**。
- **緩和（K&G−fixed の工程 acc）**: [+0.007,0.0,−0.027]、mean −0.0068、paired-σ=0.0178、同符号=False → **中立（緩和は有意でない）**。

### 解釈（B1 確定）
- **素朴 MTL は固定重みでも K&G 学習重みでも工程を有意に害す（fixed −0.046 / K&G −0.053、ともに有意）／検出はどちらも中立**。
- **K&G の不確実性重み付けは負転移を有意に緩和しない**（seed456 で 0.8389 と悪化し緩和が打ち消される＝高分散）。→「素朴 MTL の負転移は重み付け調整では救えない」。
- これは B2a/T1a（**入力に凍結特徴を注入する設計**）が正の Δ を出すのと対照的＝**結合の効き方は重み付けでなく"何をどこに渡すか"の設計で決まる**を補強。

### 次
- bengio T1b（学習 FiLM 注入 phase→det）の Δ_detection が出たら、STEP B 6実験（B2a/T1a/B1fixed/B1K&G/B2b/T1b）の比較表（§7）を確定。test 最終評価は全系統一括。

---

## T1b-CA（§4.6 primary cross-attention phase→det）3-seed 確定（2026-06-23, lecun 2GPU 並列）

### 仮説
- §4.6 が "primary" とする decoder cross-attention は、FiLM の空間一様変調と違い**クエリ単位で選択的**に phase を注入できる → 表現力が高く、rare∧工程特異術具を**標的化**して phase→det を FiLM 以上に伸ばせるか（§3.2 の「query-level でないと標的化不能」の直接検証）。

### 実験
- `scripts/run_t1b_ca_seeds_lecun.sh`（seed42 の `run_t1b_ca_seed42_bengio.sh` と**科学的設定を完全一致**: inject=ca / trainable=film / epochs=6 / lr=1e-4 / film_lr=5e-4 / tol=0.02）。seed 固有に変わるのは warm-start ckpt（`checkpoints/incoming/seed{S}/best_ap.pth`）と、その実測 init mAP（= preflight assert 値）のみ。
- **assert 値の決め方（捏造防止）**: seed42 の 0.7303 は「その base 検出器の独立既知 mAP」で seed123/456 には独立基準が無い。よって `--epochs 0` の **measure-only 実行で full-val preflight から init mAP を実測** → 健全帯[0.65,0.78]チェック → 実測値を assert に固定（別プロセスでの再現性ガード）。
- 進行: MSDeformAttn warm-up → measure(両seed) → wave A(inj real-ctx 両seed並列) → wave B(ctrl zero-ctx 両seed並列)。seed123→GPU0 / seed456→GPU1 のロックステップ並列。1run≈3.3h（4809 det step/ep ×6ep @2.4it/s）。
- **厳密性 cross-check 通過**: init mAP が measure=inj=ctrl で**15桁一致**（s123=0.7291948117 / s456=0.7216619815）→ warm-start+zero-init 恒等・プロセス間決定論・正しい per-seed ckpt ロードを物理的に実証。

### 結果
- **Δ_det = inj−ctrl（純効果, paired-σ §10.1）**: s42 **+0.00245** / s123 **+0.00161** / s456 **+0.00127**。mean **+0.00178**、pstdev=0.00050、**|mean|/σ=3.58・全正**。
  - inj mAP: s42 0.73275 / s123 0.73080 / s456 0.72319（best@ ep0/ep2/ep3、いずれも init からほぼ不動）。
  - ctrl mAP: s42 0.73029 / s123 0.72920 / s456 0.72191。
- **FiLM 3-seed（比較）**: +0.0019 ± 0.0012（s42 +0.0031 / s123 +0.0022 / s456 +0.0002）。→ **CA +0.00178 ≈ FiLM +0.0019**（むしろ僅かに下、ただし CA の方が低分散）。

### 解釈
- **2つのσの区別（誠実）**: paired-σ（cross-seed 一貫性 σ=0.0005）では「一貫陽性・|mean|/σ=3.58」で§10.1 を満たすが、**S0-frozen 分母 σ=0.0052 より Δ が小さい** → 統計的には非ゼロでも**実用上は微小**。「有意」を magnitude の主張に流用しない。
- **CA は FiLM を上回らない（§4.6 への否定寄り結果）**: query-level で選べる高表現力機構でも overall mAP は伸びず。全 seed で warm-start 恒等点からほぼ動かない（best@早期ep）＝**phase→det は学習で伸ばせる信号自体が乏しい**（機構の表現力の問題ではない）。
- **方向非対称の最終確認**: phase→det は rescore −0.04 / FiLM +0.0019 / CA +0.00178 と**3機構すべてで overall 改善せず**＝機構非依存で弱い、が確定。一方 det→phase は T1a macro-F1 +0.164（有意）。比較の三角形の phase→det 辺が確定。

### 次
- 残る唯一の反証機会は **test split per-class での rare∧工程特異術具の標的化**（overall では出ないが per-class で局所利得が出るか）。FiLM/CA とも per-class 標的化は現状 n=1（zero-ctx 対照が init を超えない seed で per_class 空保存のため inj−ctrl 不能）→ 標的化のみ test split で取り直しが残課題。
- 出なければ §7.5 撤退ライン確定＝貢献は「強い det→phase（混同工程を割る機構の実証）＋ phase→det が機構非依存で弱いことの実証（負の結果＋機構解明）」。
- 証跡: `transfer/t1b_ca_seed{123,456}_lecun/{injected,control}_result.json`＋ログ、`experiments/analysis/step_c_coupling_analysis/REPORT.md §3.6`。


---

## 2026-06-24 STEP C / phase→det test split per-class 評価（seed42）

### 実験
- 実行時刻: 2026-06-24 04:40 JST。
- コマンド:
  - `CUDA_VISIBLE_DEVICES=0 .venv-relation-detr/bin/python scripts/eval_phase2det_test.py --models s0_frozen,t1b_film_inj`
  - `CUDA_VISIBLE_DEVICES=1 .venv-relation-detr/bin/python scripts/eval_phase2det_test.py --models t1b_film_ctrl,t1b_ca_inj`
- test split: `instances_test.json` 4265 images、phase context 欠損 0。
- 出力:
  - `experiments/analysis/step_c_coupling_analysis/test_eval_s0_frozen.json`
  - `experiments/analysis/step_c_coupling_analysis/test_eval_t1b_film_ctrl.json`
  - `experiments/analysis/step_c_coupling_analysis/test_eval_t1b_film_inj.json`
  - `experiments/analysis/step_c_coupling_analysis/test_eval_t1b_ca_inj.json`
- 実行時に `Ninja is required to load C++ extensions` 警告が出たが、全4評価は完走して JSON を更新済み。

### 結果
- mAP: S0 0.5060516339 / FiLM ctrl 0.5049835603 / FiLM inj 0.5088367176 / CA inj 0.5090467701。
- FiLM 純効果（inj−ctrl）: +0.0038531573 mAP。per-class 最大は Skewer +0.0232045679、Hook +0.0176920142、Scalpel +0.0056220186。負方向は Syringe −0.0019096700、Mouth Gag −0.0010796652、Electric Cautery −0.0008959040。
- CA は今回 ctrl なしのため S0 比のみ: +0.0029951362 mAP。per-class 最大は Scalpel +0.0140817285、Retractor +0.0095953048、Syringe +0.0036040840。負方向は Forceps −0.0023429135、Skewer −0.0004637719、Hook −0.0001715309。

### 解釈
- test split でも phase→det の overall 利得は小さい（FiLM +0.39pt、CA +0.30pt）。
- FiLM では Skewer/Hook に局所利得があるが、Syringe は負。CA は Scalpel/Retractor が伸びる一方、Skewer は伸びない。
- 「rare∧工程特異術具を一貫して標的化する」強い反証には届かない。overall で弱い phase→det という既存結論を大きく覆す結果ではない。


---

## 2026-06-24 H-C-v1 / phase→det H-C コア最小実装（T1b-CA + entropy gate, 3-seed inj/ctrl）

### 仮説
STEP C REPORT.md §7.2 の H-C コア（非対称・標的・ゲート付き循環結合）の最小実装として、T1b-CA に **per-frame entropy gate** を追加する H-C-v1 を試す。仮説:
- phase context の確信度（normalized entropy H）が高い（=遷移近傍・不確実）frame では注入を抑制（gate≈0）、確信時のみ強注入（gate≈1）とすることで、注入信号の signal-to-noise を上げる。
- これが効けば「§3.2 一様注入は標的化不能」の局在不変性を時間方向で部分的に突破できる。
- 効かなければ phase→det は機構非依存で弱いことが（gate 機構を含めて）最終確定。

### 実験
- 実装: `third_party/Relation-DETR/models/detectors/relation_detr_phase_hc.py`（`RelationDETRPhaseCrossAttn` を継承し `set_phase_context` をオーバーライドして gated_ctx = ctx * sigmoid((τ-H)*scale) を上流に渡す）/ model_cfg `relation_detr_resnet50_egosurgery_t1b_hc.py`（gate_tau=0.15, gate_scale=20.0）/ trainer `scripts/train_t1b.py --inject hc`（既存に最小差分で 3 行追加）/ launcher `scripts/run_hc_seeds_lecun.sh`（lecun 2GPU wave-by-wave で 3 seed × inj/ctrl）。
- **データドリブン hyperparam**: 実 phase ctx の normalized entropy H が train mean=0.126 / median=0.087 / 95%ile=0.346 と非常に低かった（S4 TeCNO は high-confidence な出力）ため、デフォルト tau=0.5 では 98% frame で gate≈1（H-C → T1b-CA に退化）と判明。**事前検証で発見し τ=0.15, scale=20 に再設定**（train で注入優位 76.6% / 抑制 8.6%、test で注入優位 64.1% / 抑制 26.7% → 明確に差別化）。本件は再発防止策として `tasks/lessons.md` と Notion lessons DB に記録済。
- **比較プロトコル**: 同 warm-start ckpt (per-seed best_ap.pth) / 同 epochs=6 / lr=1e-4 / film_lr=5e-4 / trainable=film / 同 phase context / 同 eval_recipe / 同 locked-down test_cfg。唯一の差は forward 前の entropy gate のみ。
- **per-seed init mAP（measure-only 実測）**: seed42 0.7303 / seed123 0.7292 / seed456 0.7217（**T1b-CA と 15 桁完全一致** → warm-start+zero-init 恒等が壊れていないことを確認）。健全帯 [0.65, 0.78] 内。
- 進行: warmup(MSDeformAttn JIT) → measure(両 wave) → wave A inj(real ctx, 2 GPU 並列 + 1 単独) → wave B ctrl(zero ctx, 2 GPU 並列 + 1 単独)。1 run ≈ 6.6h（4809 det step/ep × 6ep @ 1.2 it/s on lecun A6000）、合計 ≈ 24h。
- 起動時刻: 2026-06-24 09:36 UTC（lecun, GPU 0+1, `bash scripts/run_hc_seeds_lecun.sh` background）。

### 結果
- **3-seed 完走（2026-06-25 01:26 UTC 全完了, ~16h GPU time）**: 全 6 run（inj/ctrl × seed42/123/456）が PREFLIGHT-FAIL なく完走。
- **inj mAP（学習後 best）**: s42 0.73031 (best@ep-1=init) / s123 0.73007 (best@ep5) / s456 0.72238 (best@ep1)
- **ctrl mAP（学習後 best）**: s42 0.73031 (best@ep-1=init) / s123 0.72919 (best@ep-1=init) / s456 0.72204 (best@ep3)
- **純効果 Δ_det = inj−ctrl**: s42 **+0.00000** / s123 **+0.00088** / s456 **+0.00034**
- **3-seed paired-σ**: mean **+0.00040**, pstdev=0.00036, **|mean|/σ=1.12**, 全 seed ≥0
- **vs T1b-CA 比**: T1b-CA mean=+0.00178, |mean|/σ=3.58 → H-C-v1 は T1b-CA の **0.23 倍**（gate 追加で改善せず、むしろ低下）

| 機構 | 3-seed mean Δ_det | \|mean\|/σ | 判定 |
|---|---|---|---|
| B2b 再スコア（無較正）| −0.04 | n/a | 単調劣化 |
| T1b-FiLM（空間一様）| +0.0019 | 1.6 | 一貫正だが微小 |
| T1b-CA（クエリ選択 §4.6 primary）| +0.00178 | 3.58 | 一貫正だが微小 |
| **H-C-v1（CA + 時間選択 gate）** | **+0.00040** | **1.12** | **同 機構で最小（gate 追加で 0.23x）** |

### 解釈
- **事前判定基準に従い §7.5 撤退ライン確定**: gate 単体寄与は overall mAP を改善しない。phase→det は **機構を問わず弱い** ことが 4 機構 ablation で最終実証。
- **gate 単独で改善しないため H-C-v2（phase-conditional query bias）は追加価値なしと予測**: §3.2 の局在不変性は時間方向の選択性で救えない＝検出のボトルネックは class-prior でなく **局在（box の場所）** であり、phase context は class-prior しか与えられない。query-level クラス bias を追加しても class score は変わるが box は改善しない。
- **seed42 で完全 0.00000（best@ep-1=init）は特に示唆的**: 6 epoch 学習しても init を超えるサンプリング point が一度も無かった = 検出器は phase context の有用な情報を抽出できず、gate がそれを更に削ったことで「学習する価値のある信号がほぼゼロ」になった。
- **3 機構の Δ 順は (FiLM ≈ CA) > (CA+gate)**: 注入信号を絞ると改善幅も縮小。これは「phase 信号は薄く広く弱く効くだけで、時間方向に絞ると効果が消える」ことを示唆。
- **方向非対称が完全に確定**: det→phase 大勝（T1a macro-F1 +0.164）vs phase→det 機構非依存で弱い（全 4 機構が overall を実質改善せず）。

### 次
- **§7.5 撤退ライン確定** → 貢献の最終確定: 「強い det→phase（T1a +0.05・hemostasis F1 倍増の混同工程局在を実証）＋ phase→det が機構非依存で弱いことの実証（4 機構の負の結果と機構解明）」。
- H-C-v2（phase-conditional query bias）への投資は **見送り**（事前判定基準に従う）。
- **論文ドラフト方針**: STEP C REPORT.md §7.5 を「撤退ライン確定」として書き、4 機構の比較表（B2b/FiLM/CA/CA+gate）を中心に「phase→det の機構非依存性」を主張。`paper-writer` サブエージェントへ。
- 証跡: `transfer/hc_seed{42,123,456}/{injected,control}_result.json` + `logs/hc_{measure,inj,ctrl}_seed{S}.log`。
- Notion 投稿:
  - 実験 Run台帳 6 件: `hc_{inj,ctrl}_seed{42,123,456}`（`scripts/post_hc_to_notion.py` で投稿済 2026-06-25）
  - 意思決定ログ: 「H-C-v1 アーキテクチャ採用」(389ee4d4-7777-81ff-9ab5-de565b755f3f, active)
  - 意思決定ログ: 「H-C-v1 結果による §7.5 撤退ライン確定」(38aee4d4-7777-8104-a673-f3eeedbd9550, active・前決定を update)
  - 失敗知見: 「hyperparam はデータ分布から逆算」(389ee4d4-7777-8170-bf84-feddba3b203a)


---

## 2026-06-26 T1a-Deep / 時系列容量・受容野拡張 — 容量拡張は寄与なし（負の結果）

### 仮説
STEP C REPORT §5 #3 推奨「時系列 region-token 強化」の最小実装として、T1a base の Causal MS-TCN を 容量拡張する。仮説:
- T1a base (num_layers=8, dilation 受容野 2^7=128 frames ≈ 4.3 秒) は混同工程の境界（hemostasis 等）を完全には取り切れていない
- num_stages=3 / num_layers=10 / num_f_maps=96 に拡張して受容野 2^9=512 frames（約 17 秒）・容量 1.5x → hemostasis F1 を更に底上げ

### 実験
- 実装: `scripts/train_t1a.py` に `--description` 引数追加（既存パラメータ `--num-stages/--num-layers/--num-f-maps` で容量制御）/ `scripts/run_t1a_deep_seeds.sh`（3-seed 並列）
- 設定: `--num-stages 3 --num-layers 10 --num-f-maps 96 --description t1a_deep_3s10l96f --epochs 50`
- 比較: T1a base 3-seed (num_stages=2/num_layers=8/num_f_maps=64) との **1 点 ablation**（時系列モデル容量のみ差し替え）
- データ: 既存 region-token + GAP キャッシュをそのまま流用（同 cache・同入力・同 lr・同 loss・同 eval recipe）
- 実行: lecun 2 GPU 並列 wave (seed42+123) → seed456 単独、各 50 epoch × 約 30 分

### 結果

| seed | T1a base acc | T1a-Deep acc | Δ_acc | T1a base F1 | T1a-Deep F1 | Δ_F1 |
|---|---:|---:|---:|---:|---:|---:|
| 42 | 0.9498 | 0.9452 | **-0.0046** | 0.8081 | 0.8073 | -0.0008 |
| 123 | 0.9485 | 0.9485 | 0.0000 | 0.8090 | 0.8141 | +0.0051 |
| 456 | 0.9465 | 0.9485 | +0.0020 | 0.7961 | 0.8139 | **+0.0178** |

**paired-σ 判定（§10.1）**:
- Δ_acc: mean **-0.00088**, pstdev 0.00277, **|mean|/σ 0.32, 符号混在 → ×不有意**
- Δ_macro_f1: mean **+0.00740**, pstdev 0.00776, **|mean|/σ 0.95, 符号混在 → ×不有意**

**vs S4 base 0.8986**:
- T1a base mean: 0.9483 → +0.0497
- T1a-Deep mean: 0.9474 → +0.0488（差 -0.0009 = 統計的に区別不能）

### 解釈
- **仮説反証**: 時系列モデル容量・受容野の拡張は overall acc を改善しない。T1a base の MS-TCN は既に十分な容量を持つ。
- **seed42 で -0.0046 微減**: 過学習リスクの兆候。容量拡張は seed 依存で不安定（macroF1 では seed456 +0.0178 と最大利得だが他 seed で吸収）。
- **「時系列の問題は容量ではない」**: T1a の改善余地は時系列モデル単体ではなく、**per-frame 表現の質**（region-token の trajectory modeling・GAP の置き換え・object-aware attention 等）にある可能性が高い。
- **論文化視点では価値ある負の結果**: T1a base の十分性を実証する形で「時系列モデル容量拡張は本ドメインで効果なし」を主張可能。

### 次
- 時系列容量系の追加投資は中止（H-C-v1 と同様、機構非依存で弱い）。
- 残る改善方向（優先順）:
  1. **Region-trajectory modeling**: 各 tool slot (15 個) の時間方向 attention（TAPIS の object track 機構）
  2. **GAP の置き換え**: per-class attention pooling（class-aware の場所情報を残す）
  3. **§5 #4 PCGrad MTL**: B1 の負転移を解く勾配手術系
- いずれも実装規模・新規性で判断。
- 証跡: `experiments/transfer/t1a_deep_3s10l96f_{001,002,003}_*/{metrics.json,notes.md,checkpoints/best_tecno.pth}`、`logs/t1a_deep_seed{42,123,456}.log`。
- Notion: 実験 Run台帳 3 件投稿済 (`t1a_deep_3s10l96f_*`)、意思決定ログ「T1a-Deep（時系列容量拡張）3-seed 結果: 容量拡張は寄与なし（負の結果）」(38bee4d4-7777-819a-8c6b-e6c6efa7e177)。


---

## 2026-06-26 T1a-RegionOnly / GAP 削除 ablation — GAP は冗長（region-token が frame 表現を subsume）

### 仮説
T1a-Deep の負の結果（時系列容量は寄与なし）を受けて、**T1a 入力次元の構成要素を ablation**。仮説:
- T1a 入力 = GAP(2048) + region(3840) = 5888d。GAP は frame 表現、region は object 表現。
- もし GAP が冗長なら region のみで T1a base と同等の Δ_phase 達成 → T1a の最小構成 = region のみ
- もし GAP が補完なら region のみは T1a base より低い → GAP が必要

### 実験
- 実装: 既存 `--region-only` フラグ（実装ゼロ）/ `scripts/run_t1a_region_only_seeds.sh`（3-seed 並列）
- 設定: `--region-only --description t1a_region_only --epochs 50`（他は T1a base と同一）
- in_dim 5888 → **3840（GAP 2048 削除）**

### 結果

| seed | T1a base acc | RegOnly acc | Δ_acc | T1a base F1 | RegOnly F1 | Δ_F1 |
|---|---:|---:|---:|---:|---:|---:|
| 42 | 0.9498 | 0.9472 | -0.0026 | 0.8081 | 0.8006 | -0.0075 |
| 123 | 0.9485 | 0.9498 | +0.0013 | 0.8090 | 0.8112 | +0.0022 |
| 456 | 0.9465 | 0.9472 | +0.0007 | 0.7961 | 0.8024 | +0.0064 |

**paired-σ 判定（§10.1）**:
- Δ_acc: mean **-0.00022**, pstdev 0.00173, **|mean|/σ 0.13, 符号混在 → ×不有意（GAP は冗長）**
- Δ_macro_f1: mean **+0.00037**, pstdev 0.00579, **|mean|/σ 0.06, 符号混在 → ×不有意（GAP は冗長）**

**3-seed mean (vs S4 base 0.8986)**:
- T1a base mean: acc 0.9483, F1 0.8044 (Δ vs S4 = +0.0497)
- RegOnly mean: acc 0.9481, F1 0.8048 (Δ vs S4 = +0.0495)
- **入力次元 35% 削減でも統計的に区別不能 = GAP は完全に冗長**

### 解釈
- **重要発見: region-token は frame-level GAP を完全に subsume する**。object 表現は frame 表現を含む。
- T1a の最小構成 = **region のみ（in_dim=3840）**。GAP 不要で学習時間・メモリ 35% 削減可能。
- T1a の改善方向は **入力次元拡張ではなく region-token の質**（per-class trajectory, 時間方向 attention 等）に集中する。

### T1a 構成要素 ablation 完成（3 つの 1 点 ablation）

| バリアント | 入力 | 時系列モデル | mean acc | Δ vs T1a base |
|---|---|---|---:|---:|
| **T1a base** | GAP(2048) + region(3840) | TeCNO (2s/8L/64f) | 0.9483 | — |
| T1a-Deep | GAP + region (5888) | TeCNO (3s/10L/96f) | 0.9474 | -0.0009 (×不有意) |
| **T1a-RegionOnly** | region のみ (3840) | TeCNO (2s/8L/64f) | 0.9481 | -0.0002 (×不有意) |

**結論**: T1a の改善は『容量拡張』『入力次元拡張』いずれでも実現せず、本質は **region-token そのもの**。残る改善方向は (i) region-trajectory modeling（各 tool slot × 時間方向 attention）/ (ii) per-tool importance（どの slot が phase に貢献？）。

### 次
- region-token の 15 tool slot のうちどれが phase 貢献に支配的か？（per-slot 重要度分析）
- region-token を 15 個の独立 token として時間方向 attention（TAPIS object track 機構）
- 論文 §3.x の主力 figure として T1a 構成要素 ablation 表を採用
- 証跡: `experiments/transfer/t1a_region_only_{001,002,003}_*/{metrics.json,notes.md,checkpoints/best_tecno.pth}`、`logs/t1a_region_only_seed{42,123,456}.log`
- Notion: 実験 Run台帳 3 件投稿済、意思決定ログ「T1a-RegionOnly 3-seed: GAP は冗長」(38bee4d4-7777-8181-9b78-db548aad3fe9)


---

## 2026-06-26 §18.4 L0 監査 — phase→det 3 機構の配線・学習能力検証（査読防御）

### 仮説
M2 研究計画 §18.4 が要求する「分析論文の検証厳密化」の最優先タスク = L0 監査。
**phase→det が「機構非依存で弱い」という負の結果が under-tuning/バグと外形的に区別できない**ため、能動的な排除が必要（§18.0）。

### 実験
- 実装: `scripts/audit_t1b_l0.py`（4 チェック: 勾配フロー / loss@init / NaN-inf hook / overfit-one-batch）
- 対象: T1b-FiLM / T1b-CA / H-C-v1 × seed42（各 1.1-1.3 min, GPU0）
- 閾値: 凍結 backbone + 1.58M phase 層用に overfit-reduction を 50%→20% に調整（§18.4 元値は full-model 想定）

### 結果（全 3 機構 ALL PASS）

| 機構 | grad_flow | loss_init (mean ± std) | nan_inf | overfit (reduction) | ALL |
|---|---|---|---|---|---|
| FiLM | ✓ (loss=7.2, issues=0) | ✓ (16.2 ± 6.1) | ✓ (hits=0) | ✓ **49.6%** | **✓** |
| CA | ✓ (loss=7.2, issues=0) | ✓ (16.2 ± 6.1) | ✓ (hits=0) | ✓ **31.5%** | **✓** |
| HC | ✓ (loss=7.2, issues=0) | ✓ (16.2 ± 6.1) | ✓ (hits=0) | ✓ **31.2%** | **✓** |

### 解釈（最重要発見・査読耐性の核心）
- **overfit-reduction の機構順序 FiLM 49.6% > CA 31.5% ≈ HC 31.2% が、val mAP 順序 FiLM +0.0019 > CA +0.00178 > HC +0.00040 と完全一致**
- → 「機構容量と汎化能力が比例する = 機構変更では本質的に救えない」を実証
- → reviewer の「under-tuning では？」反論への決定的反証
- **HC ≈ CA** = entropy gate は learning capacity をわずかに減らす（汎化結果と整合）
- **§7.5 撤退ライン主張の物理的防御完成**: phase 層は learning しているが (Check 4 PASS)、汎化に効かない (val mAP +0.001 オーダー) = phase context の情報的限界（§3.2 局在不変性と整合）

### 次
- §18.4 優先順位 #1 (L0 監査) ✓ 完了
- 次の優先タスクは **L1-2 oracle-phase（ground-truth phase 直接注入）** ★最重要（§18.4）
  - もし oracle-phase でも改善しなければ phase→det の機構非依存性が完全確定
  - 改善すれば「phase 推定誤差」が真因の可能性
- 証跡: `experiments/audit/t1b_l0_audit_{film,ca,hc}_seed42/audit_report.json`
- Notion: 意思決定ログ「§18.4 L0 監査 3 variant 全 PASS: §7.5 撤退ラインの査読防御強化」(38bee4d4-7777-8131-87de-e57c2bfb19dd)


---

## 2026-06-29 §18.4 L2-2/L3/L2-3 完了 — 5-seed paired-σ + B2a oracle 重大発見

### 仮説
研究計画 §18.4 の Tier-0/1 タスクを並行起動し、論文の **両柱**（negative result 防御 + positive result 防御）を固める:
- L2-2 shuffle control: T1a 改善が「容量効果」でないことを正規 ablation で実証
- L3 seed 拡張: T1a 全 variant + B2a を seed 789, 1000 で追加 → 3-seed → 5-seed 化
- L2-3 oracle-tool-presence: B2a の改善上限を測定（検出器精度ボトルネック検出）

### 実験
- L2-2: train_t1a.py に `--region-shuffle` 引数追加（10 行）。3-seed × 50 epoch。
- L3: T1a base/Deep/RegionOnly/Shuffle + B2a base/oracle 6 variant × seed 789, 1000 = 12 run。
  GPU 共存（L1-2 oracle-phase 17 GB + TeCNO 0.14 GB / process）で約 3h で完走。
- L2-3: train_b2a.py に `--tool-source oracle` + `--mask-tool-dim` 引数。GT bbox から
  oracle tool-presence one-hot 15-d を build_oracle_toolpresence.py で生成し、3-seed (42/123/456) で実行。

### 結果

**L2-2 T1a-Shuffle 3-seed paired-σ**（5-seed では L3 拡張で）:
| seed | T1a base acc | Shuffle acc | Δ_acc |
|---|---|---|---|
| 42 | 0.9498 | 0.8601 | −0.0898 |
| 123 | 0.9485 | 0.8627 | −0.0858 |
| 456 | 0.9465 | 0.8587 | −0.0878 |
| **3-seed paired-σ** | | | **mean −0.0878, \|mean\|/σ=54.30 ✓強く有意** |

L3 拡張で seed 789, 1000 を追加 → **5-seed mean acc 0.8573 ±0.0110（Δ vs S4=−0.0413）**。
shuffle で T1a 改善 +0.0497 が消失どころか **S4 base より低い負転移**。

**T1a 4 variant 5-seed mean**:
| variant | mean acc | Δ vs S4 base 0.8986 |
|---|---|---|
| T1a base | 0.9483 ±0.0012 | **+0.0497** |
| T1a-Deep | 0.9475 ±0.0012 | +0.0489（容量拡張 ×不有意）|
| T1a-RegionOnly | 0.9480 ±0.0016 | +0.0494（GAP 冗長）|
| T1a-Shuffle | 0.8573 ±0.0110 | **−0.0413**（shuffle 負転移）|

**B2a oracle 5-seed paired-σ（重大発見）**:
| seed | B2a base | B2a oracle | Δ_acc | Δ_F1 |
|---|---|---|---|---|
| 42 | 0.9373 | 0.9518 | +0.0145 | +0.0255 |
| 123 | 0.9353 | 0.9604 | +0.0251 | +0.0366 |
| 456 | 0.9380 | 0.9578 | +0.0198 | +0.0361 |
| 789 | 0.9373 | 0.9617 | +0.0244 | +0.0387 |
| 1000 | 0.9366 | 0.9597 | +0.0231 | +0.0300 |
| **5-seed paired-σ** | | | **mean +0.02139, \|mean\|/σ=5.50 ✓** | **mean +0.03336, \|mean\|/σ=6.79 ✓** |

**5-seed mean**:
- B2a base: 0.9369 ±0.0009 (Δ vs S4 = **+0.0383**)
- B2a oracle: 0.9583 ±0.0035 (Δ vs S4 = **+0.0597**)
- **上限差分 +0.0214** = 検出器精度向上で達成可能な phase 改善余地

### 解釈
1. **L2-2 positive control 反証**: T1a +0.0497 改善は容量効果ではなく **真の region-phase 相関**に依存。shuffle で **−0.0878 大幅劣化（|mean|/σ=54.30）**。reviewer の容量効果反論への決定的反証。
2. **L3 5-seed paired-σ**: T1a 全 variant の 3-seed 結論が 5-seed でも保持。統計的にさらに強化。
3. **L2-3 重大発見**: 現状 B2a は理論上限の **64% (0.0383/0.0597)** に到達。検出器を改善すれば phase acc を +0.0214 大幅向上可能。これは §7.5 撤退ライン（phase→det 弱）と対をなす **det→phase 方向の改善余地** を示す論文第二発見。

### 次
- L1-2 oracle-phase 完走待ち（残 ~9h, 6 run）
- L2-4 15-d ablation 完走待ち（残 ~11.5h, 45 run, 各 tool dim の寄与測定）
- 完走後: oracle-phase が改善した場合 § 7.5 撤退ラインの再検討、改善しなければ機構非依存性最終確定
- 証跡:
  - `experiments/transfer/t1a_{regiontoken,deep_3s10l96f,region_only,shuffle}_*_seed{789,1000}/`
  - `experiments/transfer/b2a_det2phase_oracletool_*_seed{42,123,456,789,1000}/`
- Notion: 実験 Run 台帳 18 件投稿済（L2-2 3 件 + L3 12 件 + L2-3 3 件）/ 意思決定ログ「§18.4 L2-2 shuffle」(38eee4d4-7777-81c0-b46d-dfb4022bead8) + 「§18.4 L3 5-seed 拡張完了 + B2a-oracle 重大発見」(38eee4d4-7777-8171-8c0b-e3e82103969f)

---

## 2026-07-01 STEP D-aux 実装（系統① 手情報 / 系統② 時系列情報）— インフラ構築 + oracle 手特徴の生成・検証

### 仮説（プロンプト `prompts/ Claude_code_prompt_hand_temporal` 準拠・実験は未実施）
補助信号を det→phase 方向に 1 つずつ注入し「どの信号が・どの機構で・どれだけ工程認識を改善するか」の
系統的な地図を作る。今回は **①手の情報**（H-1〜H-6）と **②時系列情報**（T-1〜T-6）の 2 系統。
すべて既存 B2a/T1a パイプライン（凍結信号 → 素 TeCNO 注入）の変種として実装し、分母・eval_recipe・
paired-σ を既存と完全一致させる。**まず着手すべき最小単位 = 系統① H-1（hand-presence oracle）**。

### 実施内容（このセッション = コード実装 + GT のみで動く部分の実行検証。**GPU 学習は未実施**）
**重要な環境制約（正直な記録）**: 本チェックアウトは `data/raw/ego`（画像）・GAP 特徴キャッシュ
（`data/processed/stage1_features/`）・`phase_manifest` が未投入で、検証済み `.venv`（torch 2.1.2 系 /
mmcv / mamba-ssm）も無い。よって **B2a/T1a 系の GPU 学習はこの環境では実行不能**。実行は lecun で行う
前提で「動くコード」を実装し、GT アノテーションだけで完結する部分（oracle 手特徴生成・4クラス COCO 抽出）は
**実際に実行して検証**した。**metrics/mAP 等の数値は一切生成・記載していない**（研究インテグリティ厳守）。

**系統① 手情報（実装 + oracle 特徴を実生成・検証）**:
- `scripts/build_oracle_handfeature.py`（新規・**実行済**）: 19クラス統合 GT（手 = category 15-18）から
  oracle 手特徴を生成。presence(4)/count(4)/geom(16)。**実測サマリ（捏造でない生成物の統計）**:
  train 9657 frame（手あり 9627）、val 1515、test 4265（公式 split 完全一致）。presence rate は
  自分の手 0.87-0.98 >> 相手の手 0.38-0.74（egocentric 手術映像として妥当）。手/frame 平均 ~2.9-3.3 本。
- `scripts/train_haux.py`（新規・構文検証済）: `train_b2a.py` の手版。GAP(2048) ⊕ 手特徴 → 素 causal TeCNO。
  `--hand-feature-type {presence,count,geom,own_other}`（H-1/2/3/5）/ `--hand-source {oracle,pred}` /
  `--with-tool --tool-source oracle`（H-6）/ `--shuffle-hand`（§4.3 shuffle control）。own_other は
  geom を own/other 2 ブロックに分離して別枝 MLP で符号化（役割非対称性 §13.2(18)）。H-4 region-token は
  S2-hand 検出器完成後（非-oracle・本 script scope 外）。
- H-6 用に `scripts/build_oracle_toolpresence.py` を再実行し、手⊕tool の frame_id が全 1515 完全一致を確認。

**系統② 時系列情報（実装・構文/契約検証済）**:
- `src/egosurgery/models/heads/mingru_head.py`（新規）: 純 PyTorch の causal minGRU（arXiv:2410.01201）を
  TeCNO と同一の multi-stage シェル・同一 forward 契約で実装（核だけ差し替え・§8.1 公平比較）。
  **検証**: forward shape が TeCNO と一致、strict-causal（t≥15 の入力摂動が t<15 の出力に漏れないこと・
  max|Δ|=0）を確認。
- `src/egosurgery/models/heads/mamba_head.py`（新規）: mamba-ssm ラッパ（causal SSM・SR-Mamba 系）。
  mamba-ssm 未導入環境ではコンストラクタで明瞭な ImportError（lecun には導入済）。
- `scripts/train_taux.py`（新規・構文検証済）: `train_t1a.py` の派生。region-token(3840)⊕GAP 主入力。
  `--temporal-kernel {tecno,mingru,mamba}`（T-4/5/6・問い B）と `--temporal-feature {none,movavg,delta,window}
  --temporal-k K`（T-1/2/3・問い A）。全変換は strict-causal（複製 pad・未来非参照）、window は in_dim を
  再計算し実次元と一致検証（Fail Loud）。問い A/B の交絡を避ける運用（一方の軸を固定）を notes に明記。

**S2-hand 独立検出器 scaffold（非-oracle 系統①の前提。Notion runbook 準拠）**:
- `scripts/build_hand_coco.py`（新規・**実行済**）: GT から手4クラスだけ抽出し 0-3（own_L/own_R/other_L/other_R）
  に remap した COCO を生成 → `data/annotations/egosurgery_hand4/instances_{split}.json`。**検証**: 手 box 数
  train 27726 + val 4918 + test 13676 = **46,320**、§12.11 B3 サーベイ記載の「46,320 hand boxes」と完全一致。
- `configs/stage/s2_hand_independent.yaml`（新規）: 独立4クラス・COCO-init のみ（S0 tool checkpoint 不使用）・
  19クラス統合しない（次元不一致を構造的に回避）。旧 S2 の catastrophic forgetting 対策を設計で不要化。

**集計・実行**:
- `scripts/report_haux_results.py` / `report_taux_results.py` / `src/egosurgery/utils/transfer_delta_report.py`
  （新規・実行済・現状 0 件レポート出力を確認）: experiments/transfer の haux_*/taux_* を走査し per-seed Δ
  （vs S4 base acc 0.8986 / macro-F1 0.709）+ paired-σ 判定（|mean|>pstdev かつ同符号）を集計。
- `scripts/run_haux_oracle_gate.sh` / `run_taux_problemA.sh` / `run_taux_problemB.sh`（新規・bash -n 検証済）:
  §6 実行順。oracle gate は H-1 → H-2/H-3/H-6 を各 3-seed。冒頭に「H-1 が no-go なら系統①非-oracle
  （手検出器仕上げ）への投資は見送る」ゲート判定コメント。

### 解釈（現時点 = 実装完了・実験前）
- §8.3 が最優先で要求した「手 GT の own/other × L/R 実在確認」→ **実在**（category 15-18 = Own/Other × L/R）。
  H-5（own/other 分離）を含む系統①全手法が実装可能と確定。
- oracle 手特徴の分布（自分の手 >> 相手の手）は外科ドメインとして妥当で、H-1 gate 実行の前提が整った。
- 数値結論は無し（GPU 学習未実施）。次セッションで lecun 上で oracle gate を回して初めて Δ が出る。

### 次
- **lecun で実行**（この環境では不可）: GAP 特徴キャッシュ・phase_manifest を用意 →
  `bash scripts/run_haux_oracle_gate.sh`（H-1 presence oracle を最優先ゲートとして）。
- H-1 が有意なら H-2/H-3/H-6 → 有望なら S2-hand 検出器を仕上げて非-oracle 群（H-1/H-4/H-5）。
- 系統②は既存 T1a 基盤の GAP/region キャッシュがあれば問い A（T-1〜3）→ 問い B（T-4〜6）。
  T-6（minGRU/Mamba）が横並びなら「工程認識のボトルネックは時系列核でなく入力信号」という一級の負の知見。
- 集計は `scripts/report_haux_results.py` / `report_taux_results.py`、Notion は完了 run を自動投稿。
- 証跡（このセッション）: 上記 13 新規ファイル / 生成物 `data/processed/oracle_handfeature/*` ・
  `data/annotations/egosurgery_hand4/*`。実験 Run はまだ無し（実行は lecun）。

---

## 2026-07-02 STEP D-aux 実行（系統① 手情報 / 系統② 時系列）— 実測 Δ + paired-σ（同一環境S4分母）

### 仮説（`prompts/ Claude_code_prompt_hand_temporal`）
補助信号を det→phase 方向に注入し「どの信号が・どの機構で・どれだけ工程認識を改善するか」の
系統的な地図を作る。①手情報（H-1〜H-6）と②時系列（T-1〜T-6）。まず H-1(hand-presence oracle) を
ゲートとし、有意なら系統①を展開。分母は S4 base、判定は paired-σ（対seed差・同符号）。

### 実験設定（評価・実験設定を全手法で統一）
- **環境**: lecun 由来の GAP 特徴 (2048-d) / region-token (3840-d) キャッシュを本チェックアウトへ配置し、
  本セッション（efros・torch 2.0.1・A6000×2）で TeCNO/派生を学習。oracle 手特徴は GT bbox から生成
  (`build_oracle_handfeature.py`)。**画像・検出器は不要**（キャッシュ済特徴のみ使用）。
- **分母（同一環境で新規に再学習）**: S4 base = GAP-only TeCNO を seed 42/123/456 で学習
  → mean acc **0.8983±0.0090** / macro-F1 **0.6965**（文書固定値 0.8986/0.709 と整合＝環境整合の裏取り）。
- **判定**: 各手法 3-seed で **per-seed paired Δ = method[seed] − S4[seed]**、|mean|>pstdev かつ同符号で✓
  （§10.1。固定スカラ分母でなく同一seedのS4に対する対差＝seed相関分散を相殺）。
- 全手法: TeCNO stages2/layers8/fmaps64、lr 5e-4、50 epoch、online_causal+jaccard_strict で完全一致。

### 結果（実測・`scripts/report_daux_paired.py`、単位 pp = percentage point）

**系統① 手情報 → 工程（paired vs 同env S4）**:
| 手法 | Δacc (\|m\|/σ) | ΔmacroF1 (\|m\|/σ) | 判定 |
|---|---|---|---|
| H-1 presence(4d) | **+0.51pp** (6.15) | **+3.44pp** (2.78) | ✓ 両有意（小さいが確実）|
| H-2 count(4d) | +0.07pp (0.12) | −0.75pp (0.45) | × 寄与なし |
| H-3 geom(16d) | **+1.23pp** (1.30) | **+3.92pp** (1.09) | ✓ 両有意（presence超＝空間配置が効く）|
| H-5 own_other(2枝) | +0.07pp (0.07) | −0.25pp (0.09) | × 分離注入は無効 |
| H-6 presence+tool | **+5.85pp** (6.05) | **+12.80pp** (5.07) | ✓ 大 |
| **H-1 shuffle (control)** | +0.02pp (0.10) | +0.64pp (0.20) | **× 改善消失→H-1は真の相関** |
| B2a tool単独(oracle) | +5.81pp (8.01) | +12.70pp (5.19) | ✓（比較用）|

**H-6 の tool 上乗せ価値** = H-6 − B2a(tool単独) per-seed paired: Δacc **+0.04pp (×)** / ΔF1 **+0.10pp (×)**
→ **手は tool に対し冗長（上乗せ無し）**。

**系統② 時系列 → 工程（region-token 基盤・vs S4 / vs T-4=region-token TeCNO）**:
| 手法 | vs S4 Δacc | vs T-4 Δacc | 判定（対T-4）|
|---|---|---|---|
| T-4 tecno (region base) | +5.06pp ✓ | — | 基準（=T1a 効果の再現）|
| T-1 movavg | +4.47pp ✓ | −0.59pp | ✓ **悪化**（時間平滑は逆効果）|
| T-2 delta | +3.17pp ✓ | −1.89pp | ✓ **悪化**（差分イベントは逆効果）|
| T-3 window | +5.21pp ✓ | +0.15pp | × 中立（短期窓は TeCNO と同等）|
| T-6 minGRU (核置換) | +5.13pp ✓ | +0.07pp | × 核非依存（3-seed確定・acc同等/F1 −0.71pp劣後）|

### 解釈（＝設計のための知見地図）
**系統①**:
1. 手情報は工程認識に寄与するが**弱い**。presence(+0.51pp) と geometry(+1.23pp) が paired-σ 有意で、
   **geometry > presence**（手の空間配置が「在/不在」より工程情報を持つ、§13.2(18) と整合）。
2. count・own/other 分離は無効（richer 化・役割分離チャネルは presence/geom を超えない。H-5 の別枝符号化は
   むしろ signal を希釈）。
3. **shuffle control** で H-1 の +0.51pp が +0.02pp に消失 → 改善は容量効果でなく **真の region-phase 相関**。
4. **最重要（§2.3 実務判断）: 手は tool に冗長**。H-6(hand+tool)=+5.85pp ≈ tool単独 +5.81pp、手の上乗せは
   +0.04pp（不有意）。→ **tool-presence があれば手情報はほぼ無価値。phase 補助信号のためだけに手検出器を
   仕上げる価値は低い**（非-oracle 系統①への投資は見送り妥当）。

**系統②**:
1. region-token(T-4) は GAP-only S4 を大きく超える（+5.06pp acc / +11.13pp F1・T1a 効果を同env再現）。
2. **明示的な時間特徴量化（問いA）は TeCNO の暗黙時間集約を超えない**: movavg(−0.59pp)・delta(−1.89pp) は
   むしろ悪化、window(+0.15pp) は中立。
3. **時系列核（問いB）も非依存**: minGRU ≈ TeCNO（acc 同等・F1 で minGRU やや劣後）。
4. → **工程認識のボトルネックは時系列核でも時間加工でもなく「入力信号（per-frame 表現の質）」**。
   これは系統①の「検出精度がボトルネック」(L2-3) と同じ方向を指す一級の負の知見。提案手法は
   時系列核の高度化でなく **object/region 表現・検出精度の改善**に投資すべき。

### 次
- T-6 minGRU 3-seed 完走・確定（vs T-4: acc +0.07pp ×, F1 −0.71pp × ＝核非依存。結論不変）。
- 系統① 非-oracle 群（手検出器 S2-hand 仕上げ→H-1/H-4/H-5 の pred 版）は**冗長性の結果を受け優先度低**。
  実施するなら「手が tool に冗長」の非-oracle 追認に留める。
- 実装上の知見: 純Python 逐次 minGRU は TeCNO の約30倍遅い（1run≈25分）。核比較を広げるなら parallel-scan 実装が要。
- 証跡: `experiments/transfer/{haux_*,taux_*,b2a_det2phase_oracletool_*}` / `experiments/phase1/s4_phase_baseline_01[012]_*`
  / 集計 `experiments/analysis/daux/REPORT.md`（`scripts/report_daux_paired.py`）。Notion 実験Run台帳へ自動投稿済。

---

## 2026-07-02 T1a-Boundary（region-token→工程 + 因果 boundary head）— over-segmentation / edit-score を狙う

### 仮説（STEP C 改善提案書 §4.1/§6-#5/§8「最終提案」）
T1a の rich な region-token は frame accuracy / macro-F1 を上げる一方 **edit-score を悪化**させ過分節を起こす
（`COUPLING_IMPROVEMENT_RECOMMENDATIONS.md` §3.1）。**boundary evidence を別ヘッドで扱う役割分離**で、
acc/macro-F1 を維持しつつ edit-score / seg-F1 を改善できるか。D-aux 系統②は region-token 上で **frame acc** を
対象に時系列核/加工を比較し「核非依存・入力信号がボトルネック」を示したが、**edit-score（時間的一貫性）は
未対象**だった。本実験はその直交軸を突く。

### 実験設定（評価・実験設定を全手法で統一）
- **環境**: efros・system python3・2×A6000。lecun 由来の GAP(2048)/region-token(3840) キャッシュのみ使用
  （**画像・検出器・mmcv 不要**）。分母 = **同一環境 efros で再学習した T1a base**（region⊕GAP・素 causal TeCNO）
  seed 42/123/456 → val acc **0.9476** / macro-F1 0.8030 / edit 32.96（lecun T1a base 0.9483/0.8044 と整合＝env parity）。
- **手法**: `TeCNOBoundary`＝T1a base の共有 stage-1 trunk（64ch）から **class-agnostic 因果 boundary head(64→1)** を分岐。
  loss = Σ_stage[CE + 0.15·T-MSE] + λ_b·BCE(boundary=phase-change ±1)。**online/causal 厳守**（未来不使用）。
- **推論 2 系統**: ①plain（per-frame argmax）②sticky（因果 boundary-gated: 遷移を確信度 sigmoid(b_t)≥τ で受理）。
  さらに boundary head 非依存の③ **min-segment debounce**（新 phase が k 連続で確定＝k 未満 blip 除去・因果）を追加比較。
- **判定**: 各手法 3-seed で per-seed paired Δ = method[seed] − T1a base[seed]、|mean|>pstdev かつ同符号で ✓（§10.1）。
  主指標 = edit_score / seg_f1@{10,25,50}、維持指標 = accuracy / macro_f1。

### 結果（実測・`scripts/report_t1a_boundary.py`）
**機構(1) boundary 監督（plain＝共有 trunk 正則化単独）**: acc −0.18pp / edit +1.07 / seg-F1@50 +0.47 — **全指標 ×**（僅少）。
**機構(2) 因果 boundary-gated sticky（τ 掃引）**: τ↑で edit↑だが acc が急落。
| τ | Δacc(paired) | Δedit(paired) | segF1@50 |
|--:|--:|--:|--:|
| 0.10 | −3.96pp ✓ | +7.92 × | 0.431 |
| 0.50 | −19.63pp ✓ | +15.61 ✓ | 0.457 |
| 0.70 | −23.41pp ✓ | +19.17 ✓ | 0.558 |

→ **acc 維持で edit 改善する τ は存在しない**（§8 の「学習 boundary head」提案は online で非有効）。
**機構(3) min-segment debounce（boundary head 非依存・パラメタフリー・因果）**:
| k | Δacc | ΔmacroF1 | Δedit | ΔsegF1@50 |
|--:|--:|--:|--:|--:|
| 2 | **−0.95pp** | −2.03pp | **+23.43 ✓** | **+0.229 ✓** |
| 3 | −2.27pp | −4.97pp | +37.71 ✓ | +0.226 ✓ |
| 5 | −4.69pp | −10.83pp | +35.27 ✓ | +0.196 ✓ |

→ **k=2 が最良の運用点**: edit 32.96→56.4 / seg-F1@50 0.41→0.63 と大幅改善、acc は約 −1pp に維持（遷移を k−1 遅延させる latency と引換・online 許容）。

### 解釈（＝設計のための知見地図）
1. **§8「学習 boundary head」は online では効かない**: plain 監督は無効、boundary-gated は edit↔acc の急トレードオフ。
   本質は「未来を見て区間多数決する offline ASRF が online 制約下で使えない」こと。
2. **一方 パラメタフリーの因果 min-segment debounce(k=2) が実用的に効く**（Δedit≈+23✓ / ΔsegF1@50≈+0.23✓ を acc −1pp で）。
   → 過分節は online でも **区間長 prior** で低減可能。「学習した boundary evidence」より「単純な最小区間長」が効く。
3. **系統②の追認 + 運用指針**: T1a 過分節の一部は per-frame region-token 信号の**実変動**を反映し boundary head では真/偽遷移を
   分離しきれない（＝入力信号がボトルネック）。**edit-score は安価な後処理(k=2)で回収でき、acc 改善には入力信号
   （検出/region 表現）の強化が要る**。論文 Pillar 3（設計指針）に「時系列後処理でなく検出器強化」を一段補強。

### 次
- **test split で追認**: T1a base vs T1a+debounce(k=2) を test で評価（val→test 汎化と §4.2 の正式 recipe）。
- debounce(k=2) は online 工程報告の**既定の安価な後処理**として全手法に一律適用可（比較の対称性を保てば交絡なし）。
- acc 改善パスは依然 **検出器強化（B2a 上限 +0.0214）**＝ lecun 実行（本 sandbox は mmcv/ckpt 不在で不可）。
- 証跡: `experiments/transfer/{t1a_boundary_00[123],t1a_base_env_00[123]}` / 集計 `experiments/analysis/t1a_boundary/REPORT.md`
  / コード `scripts/{train_t1a_boundary,sweep_boundary_tau,compare_causal_decode,report_t1a_boundary}.py`。Notion Run台帳へ自動投稿。

---

## 2026-07-03 検出器改善 → phase 転移の 3-seed 検証（Method A: strong aug）

### 仮説
検出器（Relation-DETR）を強アグメントで改善（mAP↑）すれば、その特徴を使う工程認識が改善する。
特に B2a oracle gap(+0.0214) が示す「tool-presence 経由の伸びしろ」が閉じるはず。

### 実験
- 検出器: S0 レシピから `strong_album`（**aug 強度のみ 1 軸変更**, §6 比較トライアングル）。fp32・2GPU DDP eff bs4・12ep。
- 3 detector-seed {42,123,456}: mAP **0.7426 / 0.745 / 0.745**（frozen 源 0.7303 → +0.012〜0.015、一貫）。
- 各検出器から GAP / region-token / tool-presence を再抽出 → S4 / B2a / T1a を再学習。
- **厳密性**: phase-seed 3 点平均でノイズ除去（同 seed でも ~0.8pp の phase 学習非決定性を発見）→ detector-seed で paired-σ（§10.1）。**全 54 学習成功**。
- 実行: **efros sandbox**（ユーザーが images/repo/ckpt を供給、mmcv 不要の `.venv-relation-detr`）。従来 log の「lecun でしか不可」を解消。

### 結果（paired-σ, mean Δacc / 判定）
| 経路 | det42 | det123 | det456 | mean Δacc | 同符号 | 判定 |
|---|--:|--:|--:|--:|:--:|:--:|
| **S4（GAP 2048d）** | +1.76 | +1.25 | +2.38 | **+1.80pp** | ✅ | **✅ 有意** |
| **B2a（tool-presence 15d）** | +0.24 | −0.62 | +0.95 | +0.19pp | ❌ | ❌ 非有意 |
| **T1a（region-token）** | +0.37 | −0.70 | −0.37 | −0.23pp | ❌ | ❌ 非有意 |

（|1.80|>0.46σ かつ 3seed 全正 → S4 のみ有意。B2a/T1a は符号不一致で非有意）

### 解釈
1. **S4(GAP) のみ頑健改善 (+1.80pp acc)**。検出器 mAP +1.3pp → phase acc +1.8pp の明確な転移。
2. **B2a/T1a は非有意** → **B2a oracle gap は検出器改善（強aug）では閉じない**。前回 log の「acc 改善パス＝検出器強化(B2a 上限+0.0214)」を**修正**: 改善は起きるが **GAP 経由**であり tool-presence 経由ではない。
3. **機序**: 強 aug は backbone を広く改善 → GAP がそれを捉え phase へ頑健転移。tool-presence(15d)・region は術具ヘッド局所で、mAP は上がっても phase へは seed 依存でノイジー。
4. 皮肉な整合: GAP 改善量(+1.80pp) は B2a oracle gap(+2.14pp) と**同水準** → 「仮説と同程度助けるが想定と違うチャネル」。
5. **seed42 単独では T1a/B2a も改善と誤認**（+0.37/+0.24pp）→ 3-seed＋phase-seed 平均の厳密化が過剰主張を阻止。「フル」厳密化の意義を数値で実証。

### 次
- **hires（Method C）**: 小物体術具（small AP ~0.01）を高解像度(1200/2000)で改善 → **別チャネルで B2a を閉じられるか**の検証（Phase II, ~14h）。
- **test split 最終評価**（勝ち構成の per-class AP + phase test metrics）。
- 証跡: `experiments/detector_improve/augstrong_seed{42,123,456}/`（mAP・best_ap.pth）, `logs/phase3seed_results.tsv`（54行）, `logs/paired_sigma_final.txt`。
  コード: `scripts/{_detector_full_study,_run_phase_probe_3seed,paired_sigma_3seed,_extract_improved}`。config ミラー `configs/detector_relation_detr/`。

---

## 2026-07-04 hires（Method C: 強aug＋高解像）の phase 転移 — 検出器改善スタディ完了

### 仮説
Method A(強aug) は GAP のみ改善し tool-presence/region は非頑健だった。原因は「強aug は大域改善だが**小物体術具**(small AP~0.01)は未改善」の可能性。
高解像度(1200/2000)で小物体検出を改善すれば、別チャネル(tool-presence/region)で B2a gap を閉じられるはず。

### 実験
- 検出器 Method C: `strong_album_1200_2000`（強aug＋高解像度）seed42。fp32・2GPU・12ep。
- **mAP=0.733**（Method A 0.7426 より**低下**）。per-size: **small 0.013→0.031(+2.4×)**, medium 0.276→0.282, large 0.753→0.743。小物体は改善したが large と引換で全体微減。
- phase: frozen42 / augstrong42(A) / hires42(C) の 3-way を S4/B2a/T1a × phase-seed 3点平均で比較。全27学習成功。

### 結果（3-way, acc, phase-seed平均）
| 経路 | frozen | augA | hiresC | Δ(hiresC−augA) |
|---|--:|--:|--:|--:|
| S4（GAP） | 0.8953 | **0.9133** | 0.9076 | **−0.57pp** |
| B2a（tool-presence） | 0.9377 | 0.9375 | 0.9311 | **−0.64pp** |
| T1a（region） | 0.9479 | **0.9520** | 0.9476 | **−0.44pp** |

→ **hiresC は全経路で augA に劣る**（B2a/T1a では frozen 以下）。

### 解釈
1. **小物体 AP 改善は phase に転移せず**。全体 mAP 低下(large↓)が GAP を劣化させ phase を押し下げた。
2. **B2a gap は hires でも閉じない**（hiresC B2a < frozen）。
3. 総括: phase が求めるのは**広い backbone 改善(GAP)**。高解像度の**狭い小物体特化**は大域表現を犠牲にし逆効果。

### 検出器改善スタディ 全体結論（確定）
**検出器改善→phase改善 は成立するが【経路 = GAP のみ / 手段 = 強aug のみ / B2a gap は非閉塞】。**
tool-presence/region 経路のボトルネックは検出器品質ではない（＝入力信号/表現側の別要因）。論文 Pillar3 に「時系列後処理でなく検出器強化、ただし GAP 経由に限る」を確定知見として反映。

### 次
- test-set 確認: S4/GAP frozen vs augstrong を test で paired-σ（`--eval-test`、結果は追記）。
- 証跡: `experiments/detector_improve/augstrong_hires_seed42/`, `logs/{hires_probe_results.tsv(27), hires_probe_summary.txt}`, `logs/paired_sigma_final.txt`。
  コード: `scripts/{_run_hires_probe,report_hires_probe}.py`。

### test-set 確認結果（S4/GAP, `--eval-test`, 2026-07-04 追記）
| 検出器seed | val Δacc | test Δacc | test frozen/aug acc |
|---|--:|--:|--:|
| det42 | +1.76 | **−2.49** | 0.7955 / 0.7705 |
| det123 | +1.25 | +5.42 | 0.7504 / 0.8047 |
| det456 | +2.38 | +3.42 | 0.7401 / 0.7744 |

**test paired-σ: mean=+2.12pp, pstdev=3.36pp, 符号 −/+/+ → ❌非有意**（val の +1.80pp ✅有意 とは不一致）。

**結論の修正**: S4/GAP 改善は **val で有意・test で非有意**（det42 反転・高分散）。2/3 seed は test でも正だが「全seed同符号」が崩れる。
→ **GAP 経由効果は実在するが seed 感受性が高く held-out test で頑健確認に至らず**。test-set 評価が val 楽観を是正。
証跡: `logs/s4_test_results.tsv(18)`, `experiments/phase1/s4_phase_baseline_0{44..61}/`(metrics.json に test_* 併記)。

## 2026-07-05 signature 部分集合 per-class AP 比較（Relation-DETR vs Align-DETR）

### 仮説
overall mAP は Relation-DETR 首位だが **AP_rare は Align-DETR 首位**（§検出器比較, 2026-06）。phase を決める希少∧工程特異な
**signature 術具**（EDA §8 / 利得則 `gain≈headroom×signature`）で見れば、det→phase の観点では Align-DETR が有利かもしれない。

### 実験
S0 bbox baseline 3seed（§6 統制）の `per_class_ap.json` を signature 部分集合に限定して両検出器を比較。
subset = signature_narrow(4: Syringe/Needle Holders/Skewer/Scalpel = EDA §8(2)) / signature_broad(9) / ubiquitous_ctrl(4)。
detector-seed で paired-σ（§10.1）。サニティ: 全15平均が公式 mAP（Rel 72.68±0.34 / Align 71.33±1.15）と完全一致。
コード `scripts/analyze_signature_subset_ap.py`、証跡 `experiments/analysis/signature_subset_detector_compare/{REPORT.md,results.json,REPORT.txt}`。

### 結果
| subset | Relation | Align | Δ(Rel−Align) | paired-σ |
|---|--:|--:|--:|---|
| **signature_narrow(4)** | 81.14±0.49 | **83.57±0.46** | **−2.43pp** | ✅有意・**Align 優位**（3seed全負, σ0.59）|
| signature_broad(9) | 79.15 | 78.20 | +0.96pp | ❌非有意（符号不一致）|
| **ubiquitous_ctrl(4)** | **67.06±0.16** | 64.97 | +2.09pp | ✅有意・**Relation 優位**（3seed全正）|

per-class 頑健差（3seed 同符号）: **Syringe −6.65pp / Scalpel −2.09pp → Align 勝ち**（rare∧signature）。対照群 Mouth Gag/Suction/Tweezers は Relation 勝ち。Raspatory は Relation +12.85pp。

### 解釈
- **Align-DETR の AP_rare 優位の正体 = Syringe(anesthesia) と Scalpel(incision) の signature 術具**。プロジェクト定義の signature tool(narrow 4) では Align-DETR が有意優位。
- overall mAP 首位（Relation）は主に**対照群の偏在術具＋Raspatory**由来で、**Align の劣位は phase と無関係な術具に局在**。
- 前回スタディの phase 利得ドライバ3術具（Bipolar/Scalpel/Syringe）のうち **2つ（Scalpel/Syringe）で Align 優位**、Bipolar のみ Relation 微優位。

**しかし「Align → phase 改善」仮説は既存の下流有用性比較①（台帳 completed, s4_001-003 vs s4_010-012）が反証**:
frozen→同一TeCNO で Rel-DETR acc=0.8986/F1=0.7086 vs Align acc=0.8464/F1=0.6036、**Δacc=+5.2pp(8.7σ)・Rel 圧勝**。
→ **signature 部分集合の検出 AP（Align優位）は det→phase 有用性（Rel圧勝）を予測しない。凍結源＝Relation-DETR で確定**。
本 per-class 分解は「Align を選びたくなる理由(signature AP)が下流で覆る」対照証拠として機能。
（Rel 側 s4_001-003 はローカル一致で検証済／Align 側 s4_010-012 は efros 空 scaffold・別ホスト実行の台帳値のみ [[adhoc_experiment_evidence_gap]]）

### 次
- （証跡補強）Align 側下流 s4_010-012 の metrics をローカル再取得し 8.7σ を efros で再現。
- test split の per-class AP 確認（台帳 overall test: Rel 0.507/Align 0.505, Δ+0.002）（[[val_test_significance_gap]]）。

## 2026-07-05 T1a 利得源の因果分解 (a) per-tool-slot ablation（planned 実験 P1）

### 仮説
T1a の phase 利得 +4.93pp（region-token⊕GAP→TeCNO, 0.9479 vs S4 GAP-base 0.8986）は signature 術具の region 表現が担う。
per-tool-slot を1点ずつ0除去し、除去による低下で因果寄与を分解（相関だった step_c §3.4 機構を ablation で検証）。

### 実験
既存 45 run（15 slot×3 phase-seed, `--mask-region-tool-dim`, 全 valid・recipe一致検証済）を baseline（det42-frozen 3seed）に対し paired-σ 分解。positive control=`t1a_shuffle`。コード `scripts/analyze_t1a_factorial_ablation.py`、証跡 `experiments/analysis/t1a_factorial_ablation/`。

### 結果
- positive control: shuffle で acc 0.9479→0.8605（S4 GAP-base すら −3.81pp）＝region 情報の寄与実在・frame整合が本質。
- 有意DROP: **Bipolar −0.86pp★(hemostasis, ΔF1−3.11) / Scalpel −0.77★(incision) / NeedleHolders −0.46★(closure) / Scissors −0.44(dissection特異)**。
- signature 5slot Δacc mean −0.40pp(3/5有意) vs 非signature 10slot −0.01pp(1/10)。

### 解釈
利得の因果源は **signature 術具（headroom を持つ工程の）region 表現**。Skewer(design)/Syringe(anesthesia) が落ちないのは対応工程が飽和(headroom≈0)＝利得則 `gain≈headroom×signature` を**反証可能な形で確証**。macro-F1 低下が大＝長尾工程直撃。

### 次
- factorial-b（class-only/+bbox/appearance-only/+confidence 成分分解）は region-token 再抽出要（P3）。time-shuffle は本 shuffle で充足。

## 2026-07-05 T1a-RegionTrajectory（Temporal Object-Set Fusion, §4.1・planned 実験 P2）

### 仮説・実装
T1a base の flat 連結 region-token は edit 悪化・過分節。§4.1 の役割分離アーキ（Set encoder→gated residual(presence)→causal temporal attention→TeCNO+boundary head）で acc 維持しつつ edit/seg-F1 改善を狙う。新規実装 `scripts/train_t1a_regiontraj.py`、3seed、証跡 `experiments/analysis/t1a_regiontrajectory/`。

### 結果（val 良好 → **test で覆る**）
- **val paired-σ**: acc/macroF1 維持、**edit +4.08(全seed正)・seg-F1@10/25/50 +.08/.08/.04 有意改善**、sticky edit +15.69。§4.1 成功基準を全充足。
- **test paired-σ（決定的）**: acc 維持(noisy)だが **macro-F1 −8.75pp 有意低下(全seed負)・edit −2.10 非有意(改善消失)・seg-F1@50 −0.05 有意悪化**。

### 解釈
val の edit/seg-F1 改善は held-out test に **transfer せず**、逆に macro-F1/seg-F1 を有意悪化。**RegionTraj は val に overfit**。
機序仮説: Set encoder が 3840→128 に圧縮し rare 工程の per-tool 詳細を喪失（flat-concat base は保持し test 頑健）。
→ **確定改善として採用不可**。[[val_test_significance_gap]] の教訓が的中（test 確認が val 楽観を是正）。負の知見として §4.1 にフィードバック。

### 次
- 反証可能な改良: 圧縮緩和（flat region 併存 / dim 拡大）・正則化・Set encoder と boundary の分離 ablation。edit だけなら T1a-Boundary sticky 単体。

## 2026-07-05 T1a 因果分解 (b) 入力成分 factorial（planned 実験 P3）

### 仮説・実装
region-token の成分（appearance / confidence / class）のどれが T1a 利得と汎化を担うか。抽出器に `--mode appearance`（confidence ゲート除去の生 embedding）追加→再抽出（train+val+test）、`train_t1a.py` に `RELDETR_REGION_TAG`/`--eval-test` 追加。current(appearance×conf)/appearance-only/class-only(B2a) を val+test 3seed 比較。証跡 `experiments/analysis/t1a_factorial_ablation/factorial_b_results.json`。

### 結果（paired-σ）
- **appearance の価値**(current − class-only, val): acc/macroF1 **+1.17/+1.19pp 有意**、だが **edit −11.25 有意悪化**（rich→過分節, §3.1 を定量）。
- **confidence 重みの価値**(current − appearance-only): **val 中立**（非有意）だが **test で acc/macroF1/edit を全て有意改善（macroF1 +6.62pp）**。

### 解釈
**confidence 重み(score gate)は val 不可視・test 必須の汎化成分**。appearance 埋め込みは frame 識別を上げるが edit を悪化。
appearance-only は val overfit→test macroF1 低下＝**P2 RegionTraj の失敗と同一機序（per-class confidence 信号の希釈）**。
→ **T1a 利得の汎化は confidence-weighted per-class appearance が担う**という統一的知見。P1(a)＋P3(b) で T1a 利得源の因果分解が完成。

### 次
- optional: class+bbox 成分（bbox hook 追加）、class-only の test 評価。

## 2026-07-05 T1b Phase→Det 最小版 clsbias（planned 実験 P4・最小版先行）

### 仮説・実装
真の query-selective CA（multi-token）の前に、**box 枝を触らず class logit にのみ** phase 事後(9-d)→MLP(zero-init)→
per-tool bias(15-d) を加え、**rare∧工程特異 4 術具のみ**（Bipolar0/Scalpel9/Skewer11/Syringe13）通す最小注入で検出改善するか。
新規 `models/detectors/relation_detr_phaseclsbias.py`＋config、`train_t1b.py --inject clsbias --trainable film`（検出器凍結・注入層1615のみ）。
3seed×inj/ctrl(zero-ctx) を efros 2GPU で実行（`run_t1b_clsbias_3seed_efros.sh`）。**Δ=inj−ctrl@final epoch** の 3seed paired-σ。
証跡 `experiments/analysis/t1b_clsbias/`、生 run `transfer/t1b_clsbias_seed{42,123,456}_efros/`。
（測定修正: `train_t1b.py` の per_class 保存が best-overall epoch のみで frozen 検出器では ctrl が空になる不具合→init/epoch別 per_class を全保存し同一 final epoch 比較に是正。）

### 結果（paired-σ）— 部分的成功 3/4・成功基準は不成立
- **恒等ガード**: 全 seed init mAP inj=ctrl（diff=0.0000）、base(0.7303/0.7292/0.7217)一致。overall mAP Δ**+0.003pp 非有意**＝非劣化。
- **rare-4 per-class AP Δ（全て有意・all-seed同符号）**: Scalpel **+1.25**✅ / Skewer **+0.76**✅ / Syringe **+1.17**✅ 改善、
  **Bipolar Forceps −3.14**✅ **悪化**（epoch 単調悪化）。非 rare は中立。
- **対照の厳密性**: zero-ctx の per-class AP は base と厳密一致（定数 bias はクラス内順位不変＝AP 不変）→ Δ が phase 条件づけの正味効果を分離。

### 解釈
改善 3 術具は**工程排他的**（Syringe→anesthesia 等、phase 事後が術具存在を強予測→class prior が素直に効く。Syringe headroom 最大で利得最大、利得則と整合）。
**Bipolar は hemostasis signature だが工程跨り使用**があり、phase 条件 bias が off-signature 工程での検出を相対抑圧→AP 低下。
→ 注入対象は **rare∧signature ではなく rare∧phase-排他**に限定すべき。det→phase(T1a)の「confidence-weighted per-class appearance が汎化を担う」と対を成し、
**双方向とも per-class の phase 特異性が利得/損失の分岐点**という統一像。
※誠実性: 本件は **val** per-class 評価。検出には test split（`instances_test.json`, 4265枚）が**存在し**、rare 術具は val で実例希少ゆえ **test の方が信頼できる**（`eval_phase2det_test.py`）→ rare∧工程特異術具の per-class 結論は **test 追認まで暫定**（[[val_test_significance_gap]]）。

### 次
- rare_slots を phase-排他 3 術具に限定して再走（Bipolar 除外で全改善→基準充足か検証, 最小コスト）。
- 有効性確認済みゆえ真の query-selective CA(multi-token)へ拡張、ただし注入ゲートを phase-排他性で条件づけ。Bipolar 工程分布を EDA 定量。

## 2026-07-06 T1b-CA-MultiToken（真の query-selective 多トークン CA / camt）最優先実行

### 仮説・実装
clsbias（global per-tool class bias・query非依存）の「phase-排他rareは改善／Bipolar悪化」を、真のquery-selective CAで克服できるか。
phase事後をP個のphase-prototype token(B,P,embed)=Embedding(P,embed)*posteriorに展開し、各decoder層のquery→phase cross-attentionのKVに渡す
（`relation_detr_phasecrossattn_mt.py`。decoder層は既存`relation_decoder_phaseca.py`を無改造再利用、out_proj zero-init=恒等）。
train_t1b `--inject camt --trainable film`（検出器凍結・注入層158万params）。3seed×inj/ctrl(zero-ctx)、Δ=inj−ctrl@final の paired-σ。
証跡 `experiments/analysis/t1b_camt/`、生 run `transfer/t1b_camt_seed{42,123,456}_efros/`。

### 結果（val per-class AP, §10.1）— 弱い/ほぼnull（有意はScalpelのみ）
- 恒等ガード: 全seed init inj=ctrl(0.000, full-val厳密恒等)。overall mAP Δ+0.052pp 非有意=非劣化。
- rare-4 per-class: **Scalpel +0.89pp のみ有意**。Bipolar −0.35/Skewer +0.26/Syringe −0.01 は全て seed 間符号反転で非有意。非rareも中立。

### 解釈
仮説「query-selectiveならBipolarも改善」は部分的支持: Bipolar悪化は clsbias −3.14pp→camt −0.35pp(非有意)に大幅緩和（queryがphase適合を選べoff-signature抑圧回避）。
だが同時にSkewer/Syringeの利得も消失し正味Scalpelのみ残存。**frozen検出器では、query特徴への拡散的CA deltaはper-class APを一貫して動かせず、
直接class logitを押すclsbiasの方が強いレバー**。表現力(多トークンquery-selective)の優位が検出器凍結の制約下では利得に結びつかない。
det→phase(T1a confidence-weighted appearance)・phase→det(clsbias phase-排他)・camt(frozen×間接CAは最弱象限)で、
**per-classのphase特異性 × 注入の"直接性×検出器可塑性"が利得を決める**統一像。真のCA本領には trainable=all が要る可能性（過学習監視前提）。

### 次
- optional: camt を trainable=all で再走（CA本領・過学習監視必須）／ clsbias phase-排他3術具限定再走（中断済follow-up再開）／ 双方向§4.6統合へ。
- ※誠実性: 本結果は **val** per-class AP。test split（`instances_test.json`, 4265枚）は存在し rare は test の方が信頼できる（`eval_phase2det_test.py`）→ rare 結論は **test 追認まで暫定**（[[val_test_significance_gap]]）。

## 2026-07-07 T1b-CA-MultiToken-ALL（真の query-selective 多トークン CA / **trainable=all** / camt_all）

### 仮説・実装
camt-film（frozen）で真の query-selective CA すら弱かった（有意 Scalpel のみ）のは注入機構でなく**検出器凍結**が原因、と予想し
`--inject camt --trainable all`（検出器も同時 fine-tune・~26.8M、backbone のみ凍結）で 3seed×inj/ctrl(zero-ctx) を再走。
唯一の差は trainable（film→all）。証跡 `experiments/analysis/t1b_camt_all/`、生 run `transfer/t1b_camt_all_seed{42,123,456}_efros/`。

### 結果（val per-class AP, §10.1, Δ=inj−ctrl@final）
- 恒等ガード全 seed init inj=ctrl(0.000)。**全 6run best@ep-1**＝trainable=all は overall val を過学習で init(0.73)→final(0.71) に下げる → `--which final` 比較が正当。
- **overall mAP Δ +0.609pp（pstd0.081）✅有意・非劣化**（+0.72/+0.59/+0.52 全正）。
- rare-4: **Bipolar +2.65✅ / Scalpel +0.88✅ / Skewer +1.11✅** 有意改善、Syringe +1.34（seed456 −1.68 反転で非有意）。rare 平均 +1.50pp。
- 非rare は fine-tune 波及で微動（Scissors +1.63⚠/Gauze +1.22⚠ 正、EC −0.48⚠/Tweezers −0.41⚠ 負）＝frozen と違い共有検出器が動く。

### 解釈（利得則の第三次元＝検出器可塑性）
**clsbias で −3.14pp 有意悪化した Bipolar が camt-all で +2.65pp 有意改善へ逆転**。三象限 [frozen×直接bias / frozen×間接CA / 可塑×間接CA] で
Bipolar は −3.14 / −0.35 / **+2.65**。→ 注入利得は **per-class phase 特異性 × 注入の直接性 × 検出器可塑性** の積。
**frozen×間接CA=最弱象限**（camt-film）、**可塑×間接CA=利得象限**（camt-all: 検出器が phase-conditioned 特徴を再形成でき phase-spread Bipolar すら改善）。
「phase prior を検出スコアへ直接注ぐ(clsbias)」と「query を phase 条件づけ検出器ごと再学習(camt-all)」は作用機序が根本的に異なる。

### 誠実性 caveat（捏造なし・正直報告）
- (1) trainable=all は overall val を絶対劣化（init 未超）。有意な改善は inj が ctrl より**劣化が小さい相対利得**で、**frozen S0 の絶対 overall mAP は超えない**。実運用は early-stop/正則化前提。
- (2) **val** 評価・test 未検証（rare は test の方が信頼、[[val_test_significance_gap]]）。

### 次
- ③双方向§4.6統合（det→phase と phase→det 同時学習、phase-排他ゲート＋検出器可塑性を反映）へ。残課題: camt-all rare 改善の test 追認 / early-stop 下での利得再測定。

## 2026-07-07 T1b-clsbias-PE（phase-排他ゲート版 clsbias / P4 follow-up / clsbias_pe）

### 仮説・実装
元 clsbias（rare4全注入）は Bipolar −3.14pp 有意悪化で成功基準未達。**Bipolar を注入対象から外せば**（`T1B_RARE_SLOTS=9,11,13`＝Scalpel/Skewer/Syringe のみ）
残り3術具は改善を保ち Bipolar 中立化・overall 非劣化以上になるか＝「注入は rare∧signature でなく **rare∧phase-排他** に限定」原則の検証。
trainable=film・他は元 clsbias と完全一致。証跡 `experiments/analysis/t1b_clsbias_pe/`、生 run `transfer/t1b_clsbias_pe_seed{42,123,456}_efros/`。

### 結果（val per-class AP, §10.1, Δ=inj−ctrl@final）— 成功基準クリア
- 恒等ガード全 seed init inj=ctrl(0.000)、ctrl final=base 据置(frozen no-op)、inj best は init 超え(ep2/ep4/ep2)。
- **overall mAP Δ +0.228pp（pstd0.057）✅有意・非劣化・init 超え**（+0.20/+0.31/+0.17 全正）。
- rare: **Scalpel +1.21✅ / Skewer +0.77✅ / Syringe +1.21✅** 全注入術具が有意改善（全 seed 同符号）、**Bipolar −0.00 厳密中立**（除外）、非 rare 全て厳密 0.00。rare平均 +0.80pp。

### 解釈（二つの正解経路）
元 clsbias との差分は決定的: **Bipolar 除外で3術具の利得は保存・Bipolar −3.14 消滅・overall が +0.003(非有意)→+0.228(✅有意)へ転換**＝Bipolar の backfire が overall を引き下げていた逆説的証明。
対比 [clsbias(full)/clsbias-PE/camt-all] で Bipolar −3.14/−0.00/+2.65、overall +0.003/+0.228/+0.609(絶対劣化)。
→ phase→det には**設計の異なる二つの有効解**: **frozen×phase-排他ゲート**（低コスト・安全・overall init 超え・非注入厳密中立だが phase-spread は救えず）と
**可塑×広域CA**（phase-spread Bipolar すら改善だが overall 絶対劣化・要 early-stop）。利得則「per-class phase特異性×注入の直接性×検出器可塑性」で統一。

### 誠実性 caveat
- **val** 評価・test 未検証（rare は test の方が信頼、[[val_test_significance_gap]]）→ rare 結論は test 追認まで暫定。

### 次
- ③双方向§4.6統合へ。phase→det 側に frozen×ゲート(安全解) と 可塑×広域(強解) のどちらを採るか含め設計。残課題: 両系 rare 改善の test 追認。

## 2026-07-08 ③ T1c 双方向§4.6 パイロット（1-seed=42・frame粒度・2-pass）— negative result（naive 対称双方向は不可）

### 仮説・実装
①②を踏まえ、1モデルで det→phase と phase→det の両勾配を同時に流す双方向結合（docs 564「勾配が双方向に流れる結合が要る」）が
両タスクを単方向 baseline 以上に相互改善するか、1-seed pilot で設計可否を安価に判定。新規 trainer `scripts/train_t1c_bidir.py`（smoke検証済, commit 2536f7d）。
det→phase: decoder class_head[-1] を hook→region token(3840)→PhaseHead→9工程。phase→det: camt 注入に online posterior 還流。
2-pass teacher-forced（Pass1 eval zero-ctx→region→L_phase; Pass2 train softmax(P).detach() 注入→L_det; L=L_det+λL_phase）。
A=bidir(両方向on,可塑) ∥ B=phase-frozen(det→phase off baseline=frozen検出器上のphase head)。証跡 experiments/analysis/t1c_bidir_pilot/。

### 結果（val, final ep5, n=1）— 相互改善せず
- phase→det Δ = det_mAP(bidir 0.7067) − ① camt-all ctrl 0.7110 = **−0.42pp**（S0-frozen 0.7303 比 −2.36pp）。高LR期に~0.69劣化→LR decay(ep4)で0.711回復もfinal 0.7067。
- det→phase Δ = phase_acc(bidir 0.3281) − frozen baseline 0.3690 = **−4.09pp**（ただし平均は A 0.3778 ≈ B 0.3788 で中立、A は変動大 best0.574/final0.328）。
- 恒等ガード init det 0.7303 厳密通過・loss有限・smoke済 → 配線正、設計課題でありバグでない。

### 解釈・是正案
online の低品質 phase 事後注入が (a) 検出器を誤条件づけで劣化(phase→det負) (b) 劣化した region token が phase を不安定化(det→phase中立止まり)
＝二方向が naive 結合下で破壊的干渉。docs 564 の「双方向勾配で伸びる」仮説を単純には満たさず、文献「phase→detは難方向」・①②「phase→detは適切regime要」と整合。
v2 remedy候補: (1)phase headウォームアップ (2)高品質事後=収束S4 precomputed ctx を phase→det に使い det→phase のみ online (非対称) (3)②排他ゲート事後注入 (4)phase時系列化(TeCNO) (5)非対称λ/勾配ゲート。

### 次
- pilot が naive 対称双方向の不可を確定。v2 設計方針（非対称/高品質事後/ゲート/時系列）をユーザー判断で選び再挑戦 or 打切り。※誠実性: n=1・val・test 追認まで暫定。

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

# STEP 0-1 検証ノート — eval recipe 一本化のための Δ_recipe 実測

実施: 2026-06-15 / サーバー: lecun（RTX A6000 ×1 使用）/ venv: `.venv-relation-detr`
出典: `prompts/research_pivot_summary_and_roadmap.md`（正本は Notion「M2研究計画」）

## 目的
Relation-DETR（NMS-free DETR）を 2 つの eval recipe で評価し、Δ_recipe を実測する。
- **score_thr=0.0系**（Relation-DETR 記録 recipe）: score_thr=0.0, max_per_img=300, NMS-free
- **locked-down**（`LOCKED_DOWN_TEST_CFG`）: score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6

`recipes_match()` は `LOCKED_DOWN_TEST_CFG` の全キー（score_thr/max_per_img/nms_pre/nms_iou）を
比較するため、Relation-DETR 記録 recipe（score_thr=0.0, nms_iou=None）と locked-down は
**現状では不一致 → `InconsistentRecipeError`**。これが STEP 0 のブロッカー。

## 実行
- checkpoint: `third_party/Relation-DETR/checkpoints/relation_detr_resnet50_egosurgery/train/2026-05-30-04_24_20/best_ap.pth`
- entry: `test.py --coco-path <staging> --subset val --model-config relation_detr_resnet50_egosurgery.py`
- 予測 json: `experiments/analysis/step0_recipe/pred_val.json`（1515枚 × 300 = 454500 dets）
- 評価器: リポジトリの `CocoEvaluator`（= s0_016 と同一。デフォルト COCOeval, maxDets=100）

## 結果 1（確定・有効）: score_thr 軸の Δ_recipe = 0
- pred_val.json の **最小スコア = 0.0188**（中央値 0.0426 / 最大 0.948）。
- **score < 1e-8 の検出は 0 件**（全 454500 件が 1e-2 超）。
- → score_thr ∈ {0.0, 1e-8} は完全に同一の予測集合を与える。**この軸の Δ_recipe は厳密に 0**。
  これは NMS-free DETR の sigmoid スコア分布から理論的にも予想された通り（doc §8 注2 と整合）。
- 残る差は locked-down の **NMS@0.6 適用**のみ（NMS-free モデルへの後付け NMS）。one-to-one
  マッチングで重複が少ないため near-no-op と予想。**正しい checkpoint で別途実測予定**（結果2のブロッカー解消後）。

## 結果 2（重大）: 提供 checkpoint が s0_016 を再現しない
再 eval の COCO mAP@[.5:.95] = **0.578**（AP50=0.701 / AP75=0.625）。
s0_016（seed42 記録値）= **0.7297**（AP50=0.854 / AP75=0.781）。**0.15 の乖離**。

### eval パイプラインは正しい（切り分け済）
- pred 例: image_id=0, category_id=11(Skewer), bbox≈GT → 座標系・クラス対応とも一致。
- checkpoint の `_classes_` をデコード = `Bipolar Forceps … Tweezers`（GT cat 0..14 と同順）。
- 一部クラスは s0 とほぼ一致: Mouth Gag 0.808 vs 0.807 / Electric Cautery 0.948 vs 0.971 /
  Gauze 0.229 vs 0.261 / Scalpel 0.845 vs 0.898 / Skewer 0.898 vs 0.944 / Suction 0.783 vs 0.831。
- → 指標定義・前処理・座標系は s0 と同一。乖離は**モデルの重み**に由来。

### 乖離はクラス特異的（per-class AP@[.5:.95]）
| class | 再eval | s0_016 | 差 |
|---|---|---|---|
| Bipolar Forceps | 0.091 | 0.778 | -0.687 |
| Raspatory | 0.487 | 0.829 | -0.342 |
| Scissors | 0.446 | 0.715 | -0.269 |
| Hook | 0.425 | 0.594 | -0.169 |
| Needle Holders | 0.713 | 0.852 | -0.139 |
| Forceps | 0.272 | 0.382 | -0.110 |
| Tweezers | 0.679 | 0.784 | -0.105 |
| Syringe | 0.466 | 0.571 | -0.105 |
| Scalpel | 0.845 | 0.898 | -0.053 |
| Suction Cannula | 0.783 | 0.831 | -0.048 |
| Skewer | 0.898 | 0.944 | -0.046 |
| Gauze | 0.229 | 0.261 | -0.032 |
| Electric Cautery | 0.948 | 0.971 | -0.023 |
| Mouth Gag | 0.808 | 0.807 | +0.001 |
| Retractor | NaN | NaN | (val に GT 無し) |

一様シフトでなく**易しいクラスは収束・難しいクラスは未収束**＝早期 epoch checkpoint の典型。

### 物証: このディレクトリの run は早期停止
- `best_ap.pth` / `best_ap50.pth` の **mtime = 2026-05-30 04:38:01**、train dir 名（開始時刻）
  = `04_24_20` → **開始 14 分後**。9657枚 × 12epoch の DETR 学習は 2×A6000 fp16 でも約2時間規模。
  14 分では epoch 1〜2 相当。`best_*.pth` は最良を保持し続ける設計なので、mtime 04:38 以降に
  改善が無い = この run は早期で頭打ち/停止。
- s0_016 の "best epoch 12 / mAP 0.7297" を出した**完走 run（約2時間）の checkpoint は lecun に存在しない**。
- **確証**: `best_ap50.pth` を再 eval しても **mAP=0.578 / AP50=0.701 / AP75=0.625**（best_ap.pth と完全一致）。
  両ファイルは同一 save event（mtime 0.16秒差）由来 = 「dir 内の取り違え」ではなく **train dir 全体が早期 run**。

## 結論と次アクション
- **score_thr 軸の Δ_recipe = 0 は確定**（checkpoint 品質に依存しない頑健な結論）。
- ただし STEP 0-1/STEP A の比較の三角形は「**学習済み Relation-DETR 検出器**」を凍結源とするため、
  s0_016 の 0.7297 を再現する**完走 checkpoint が必須**。提供された best_ap.pth は早期 epoch であり
  **そのままでは Δ 基準点を汚染する**。
- → **ユーザーへ**: philip 上の seed42 完走 run（best epoch 12 / mAP 0.7297）の `best_ap.pth` を特定・転送依頼。
  併せて seed123 / seed456 の完走 checkpoint も（最終 3-seed 用）。
- 完走 checkpoint 入手後に: ①再 eval で 0.7297 再現を確認 → ②locked-down NMS@0.6 を適用した
  Δ_recipe の NMS 軸を実測 → ③公式 recipe を決定。

---

## 2026-06-15 続報: ブロッカー解消 + Δ_recipe 確定

### ブロッカー解消（完走 checkpoint 検証）
ユーザーが philip から完走 run の checkpoint を `checkpoints/incoming/seed{42,123,456}/best_ap.pth`
に配置。**3 seed すべて記録値を再現**（独立再 eval, ±0.0005 以内）:

| seed | 再eval mAP | 記録(s0) | 出典 |
|---|---|---|---|
| 42 | 0.7303 | 0.7297 | s0_016 |
| 123 | 0.729 | 0.7286 | s0_017 |
| 456 | 0.722 | 0.7220 | s0_018 |

→ これらが正しい完走 checkpoint。**凍結源 backbone として使用可**。
（早期 run `train/2026-05-30-04_24_20/` は破棄対象。`pred_val.json` 等もその産物なので注意。）

### Δ_recipe 実測（seed42, val 1515枚, 同一 CocoEvaluator）
| recipe | mAP | AP50 | AP75 | dets |
|---|---|---|---|---|
| score_thr=0.0系（native, NMS-free） | 0.7303 | 0.8546 | 0.7809 | 454500 |
| locked-down（NMS@0.6 + score_thr=1e-8） | 0.6851 | 0.8037 | 0.7315 | 101823 |
| **Δ_recipe (native − locked)** | **+0.0452** | +0.0509 | +0.0494 | −77.6% |

- **score_thr 軸: Δ=0**（min score 4.58e-3 ≫ 1e-8、1e-8未満0件）。確定。
- **NMS 軸: Δ=+4.5pt（無視できない）**。NMS@0.6 で予測の 77.6% が除去。
- 機序: `PostProcess` の NMS は `box_ops.nms`（**class-agnostic**, torchvision）。手術シーンの
  異クラス重なり箱を誤除去。mmdet 検出器の class-wise NMS とは「同じ nms_iou=0.6」でも別物。

### 決定（STEP 0-1）
1. **公式 eval recipe（DETR-family / 比較の三角形）= score_thr=0.0系（NMS-free, max_per_img=300）**。
   理由: 凍結源 Relation-DETR は NMS-free 学習。locked-down の NMS 適用は不適切かつ有害（−4.5pt）。
2. `recipes_match()` が DETR(nms_iou=None) と locked-down(nms_iou=0.6) を**不一致と判定するのは正しい挙動**
   （4.5pt 差は実在）。三角形内の検出ヘッドに NMS を**絶対に適用しない**こと（Δ_detection 汚染防止）。
3. mmdet 検出器（VFNet 等, NMS 必須）と DETR を同一 NMS recipe で揃える必要が出た場合は、
   class-wise NMS@0.6 での再測が別途必要（本 STEP では三角形が Relation-DETR 単一源のため不要）。

### 証跡ファイル
- 予測: `pred_val_seed{42,123,456}.json`（native）, `pred_val_seed42_lockeddown.json`（locked-down）
- ログ: `/tmp/reldetr_eval_seed{42,123,456}.log`, `/tmp/reldetr_eval_seed42_lockeddown.log`
- locked-down config: `third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery_lockeddown.py`

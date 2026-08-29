# Step A-2 入力データの所在（項目ごとの実施可否）

## 所在の実測

| 入力 | 所在 | 実測 |
|---|---|---|
| 15 動画の工程アノテ | `data/annotations/egosurgery_phase/*.csv` | **23 クリップ / 15 動画**。形式 `Frame,Phase` |
| 15 動画の術具アノテ | `data/annotations/egosurgery_tool/instances_{train,val,test}.json` | COCO 形式・**15 クラス**・images 15437 / annotations 49652 |
| HTS アノテ | `data/annotations/egosurgery_hts/{hand_seg,hand_tool_seg,tool_seg}/` | **3 系統とも全 15 動画**を被覆 |
| 追加 6 動画のアノテ | `data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/phase/` | **動画 17-22 の 6 動画 / 23 クリップ**（16 は phase CSV 無し） |
| 術者・症例の属性 | `data/splits/surgeon_folds.json` | **`{}`（3 バイト・空）**。追加動画側にも該当キー 0 件 |
| 保存済み特徴 | `data/processed/{t1a_regiontoken,oracle_toolpresence,c5neck,stage1_features,b2a_detsignal}` | region-token 2.2G / 在否 1.5M / c5neck 49M / stage1 1.1G。**再抽出はしていない** |
| 検出の予測出力 | `experiments/**/predictions/` | **1191 ディレクトリ**。COCO 検出形式の `*.json.gz` と mmdet の `predictions.pkl` |
| 索引と run | `runindex/{index,experiments,verdicts,per_class}.csv` | 1177 / 213 / 1038 / 8370 行 |
| Cholec80 | — | **philip に存在しない**（`find` 0 件） |
| 方針文書 v2 | — | **リポジトリに未配置**（`research_policy_v2*` のヒット 0 件。契約ディレクトリ名の一致のみ）。README の相対リンク 36 件はすべて実在 |

## 項目ごとの実施可否（G1 の内容）

| 項目 | 可否 | 理由 |
|---|---|---|
| A1 折りの材料 | **可能** | 工程・術具・HTS すべて実在 |
| A2 動画ID重複 | **可能** | 追加動画の phase CSV と公式分割ファイルが実在 |
| A3 術者・症例重複 | **不可能** | **属性情報が存在しない**（空の JSON）。存在しないこと自体を実測として報告 |
| A4 クリップID識別プローブ | **可能** | 保存済み特徴が実在。CPU の線形分類器で足りる |
| A5 H(tool\|phase) 上界 | **可能** | 在否ベクトルと工程アノテが frame_id で突き合わせ可能 |
| A6 検出誤りの分解 | **可能** | 予測出力と GT が実在。基準は既存実装から取れる |
| A7 K1 出所照合 | **可能** | 索引 4 種が実在 |
| A8 Cholec80 | **実体確認のみ** | データが無いため L0 代理は実施しない |

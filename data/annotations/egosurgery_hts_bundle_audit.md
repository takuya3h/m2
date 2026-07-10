# EgoSurgery-HTS 系バンドル 監査レポート

**調査日**: 2026-07-10
**対象**: `data/annotations/{HandDataset, HandToolDataset, SurgerySegmentation}/`
**照合基準**: `data/annotations/egosurergyhts_open`（EgoSurgery-HTS 論文から抽出した規模データ）
**性質**: 読み取り専用調査。リポジトリのファイルは一切変更していない。

> 本レポートの数値はすべて実測値である。再現不可能だった項目は「特定できず」と明記し、
> 推定値で埋めていない（`CLAUDE.md` 研究インテグリティ規約に従う）。

---

## 0. エグゼクティブサマリ

**このバンドルは公式 EgoSurgery-HTS の GT ではなく、bbox アノテーションから SAM (vit_h) で
生成した派生物である。** 論文が定義する 3 タスクのうち 2 つは実行不可能、1 つは半分が欠落している。

| 論文タスク | クラス数 | 必要インスタンス数 | バンドルの現状 | 判定 |
|---|---:|---:|---|---|
| Tool Instance Segmentation | 14 | 50,383 | 器具マスク **0 件** | **不可能** |
| Hand Instance Segmentation | 4 | 57,173 | 31,509 (55.1%)・SAM 生成 | **部分的（要補完）** |
| Hand-Tool Segmentation | 5 | 41,605 | 4 クラスのみ・インスタンス情報なし | **不可能** |

split 互換性そのものは既存 `egosurgery_tool` と保たれている（train/val 完全一致、test のみ 10 枚欠落）。
問題は split ではなく **アノテーションの中身** にある。

---

## 1. バンドルの実体

| ディレクトリ | 容量 | ファイル数 | 内容 |
|---|---:|---:|---|
| `HandDataset/` | 11 GB | 116,673 | 手 4 クラスのセグメンテーション |
| `HandToolDataset/` | 4.8 GB | 55,270 | 自分の手 2 クラス + 手が持つ器具 2 クラス |
| `SurgerySegmentation/` | 634 MB | 9,944 | 器具 31 クラス セマンティックセグメンテーション + 学習コード |

### 1.1 構成要素

- **`HandDataset/seg_ann/{train,val,test}.json`**
  COCO instance segmentation 形式。compressed RLE (`{"size","counts"}`)。pycocotools でデコード可能。
  アノテーションのキーは `is_crowd`（既存 EgoSurgery 系は `iscrowd`）。
  `file_name` はフラットな `01_1_0124.jpg` 形式（既存は `train/01/01_1_0124.jpg`）。

- **`*/data/img_dir/train/<vid>/`, `*/data/ann_dir/train/<vid>/`**
  mmsegmentation 形式。PNG はグレースケール (mode='L')、1920×1080、画素値がクラス ID。

- **`*/masked_videos/`**
  **可視化オーバーレイ**。背景画素の輝度が元画像のちょうど **0.4008 倍**であり、
  `dataset_maker.py` の `cv2.addWeighted(image, 0.4, color_mask, 0.6, 0)` と一致する。
  **学習入力には使えない**（計 約 7〜8 GB）。

- **`HandDataset/test1/`**
  `data/` は本体の完全重複（ann_dir 60/60・img_dir 60/60 で md5 一致）。実質 2.5 GB の重複。
  `masked_videos` のみ内容が異なる（背景比 0.4009、mean diff 8.38）。

- **`*/annotations/`**
  `HandDataset/annotations` と `HandToolDataset/annotations` は **78 ファイル全てがバイト単位で同一**。
  内訳: `phase/*.csv`（46 本）、`tool_bbox/annotations_bbox_all/`、`tool_bbox/annotations_bbox_tool_only/`、
  `tool_presence/all.csv`（19,195 フレーム × 31 器具列）、`README.md`（0 バイト・空）。

- **`HandToolDataset/dataset_maker.py`** (171 行)
  SAM (`sam_vit_h_4b8939.pth`, `model_type="vit_h"`) に bbox をプロンプトとして与え、
  マスクを生成して `data/` と `masked_videos/` を書き出すスクリプト。

- **`SurgerySegmentation/{train.py, surgical_model.py}`**
  U-Net 系の学習コード。Neptune.ai によるトラッキング（後述の秘密情報混入あり）。
  `.neptune/async` は空。

---

## 2. 論文値との照合

### 2.1 決定的な一致 — 出所の特定

| 実測 | 対応する論文値 / 対応物 | 判定 |
|---|---|---|
| `bbox_all` の手 bbox 総数 = 17,078 + 16,387 + 13,605 + 10,103 = **57,173** | 論文「手インスタンス **57,173**」 | **完全一致** |
| `bbox_all` で「手 bbox あり」の画像 = **19,432** | `HandDataset/data/ann_dir` の枚数 = **19,432** | **完全一致** |
| `bbox_all` で「自分の手 bbox あり」の画像 = **18,397** | `HandToolDataset/data/ann_dir` の枚数 = **18,397** | **完全一致** |

1 つ目は、論文の統計が `annotations_bbox_all`（= 親アノテーション）から算出されていることを示す。
2 つ目・3 つ目は、`ann_dir` の PNG マスクが「bbox のある画像だけ」に対して機械的に生成されたことを
枚数レベルで証明する。`dataset_maker.py` の記述と完全に整合する。

> **方法論メモ**: アノテーションの出所特定では「値の一致」より「**集合の濃度の一致**」が強い証拠になる。
> 5 桁の値 57,173 が偶然一致する確率は低く、さらに 2 つの独立した画像集合の濃度まで一致すると、
> 「同じ bbox 集合から機械的に導出された」以外の説明が立たない。

### 2.2 総括表

| 項目 | 論文値 | 実測値 | 差分 |
|---|---:|---:|---|
| 高品質アノテーション画像数 | 19,496 | `ann_dir` 19,432 / `bbox_all` 19,560 | -64 / +64 |
| 手インスタンス数 | 57,173 | bbox: **57,173** ✓ / mask: 31,509 | mask は **-25,664 (-44.9%)** |
| 手術器具インスタンス数 | 50,383 | bbox: 67,687 (31 cls) / mask: **0** | **マスク完全欠落** |
| Hand-Tool インスタンス数 | 41,605 | インスタンス情報なし | **算出不能** |
| Tool Instance Seg クラス数 | 14 | マスクなし（bbox は 31 / 33 種） | **不一致** |
| Hand Instance Seg クラス数 | 4 | `seg_ann` 4 クラス ✓ | 一致 |
| Hand-Tool Seg クラス数 | 5 | **4**（両手器具クラスなし） | **-1 クラス** |

`19,496` の正確な出所は特定できなかった。候補は下表のとおりで、いずれも一致しない。
論文自身が Table 1 (15.4K) と Dataset Statistics (19,496) の不整合を説明していない（`egosurergyhts_open` §6）。

| `bbox_all` の画像集合 | 枚数 |
|---|---:|
| 総画像 | 19,560 |
| 手 bbox あり | 19,432 |
| 自分の手 bbox あり | 18,397 |
| 器具 bbox あり | 19,195 |
| 手 かつ 器具 | 19,088 |
| 手 または 器具 | 19,539 |
| 自分の手 または 器具 | 19,484 |
| **論文値** | **19,496** |

---

## 3. 欠陥の詳細

### 3.1 【致命的】器具のインスタンスマスクが 1 件も存在しない

`bbox_all` / `tool_only` の `segmentation` フィールドを全 **133,071 件**検査した結果、
**すべてが 4 点の矩形**、すなわち bbox をポリゴン表記に書き直しただけだった。

```
sample: bbox = [515, 620, 531, 455]
        seg  = [[515, 620, 1046, 620, 1046, 1076, 515, 1076]]   ← 矩形
total anns = 133071   empty = 0   <=5pts(rect-like) = 133071   real-polygon = 0
point-count histogram: [(4, 133071)]
```

さらに既存の `egosurgery_tool/instances_{train,val,test}.json` も **49,652 件すべてが矩形**である。

> **リポジトリのどこにも器具のポリゴン / RLE の GT は存在しない。**
> 論文 Tool Instance Segmentation（14 クラス・50,383 インスタンス）は再現不可能。

`50,383` の出所も特定できなかった。33 種の器具カテゴリから 14 種を選ぶ subset-sum を試したところ
**解が 4 通り以上**見つかり（偽解）、意味のある分解ではないと判断した。

（**訂正**: 過去に `egosurgery_tool` を「polygon seg」と記述したことがあるが、これは誤りである。）

### 3.2 【致命的】Hand-Tool の 5 クラス目「両手で扱う器具」が実装ごと存在しない

`HandToolDataset/data/ann_dir` の PNG に出現するラベルは **{1, 2, 3, 4} のみ**。
生成元コードに両手割当の分岐が書かれていない。

```python
# dataset_maker.py:144-152
if   category_name == "first person's left hand":  combined_mask[masks[0] > 0] = 1
elif category_name == "first person's right hand": combined_mask[masks[0] > 0] = 2
elif category_name != "eye" and ... :              # tool → 左手なら 3 / 右手なら 4
        combined_mask[masks[0] > 0] = 3
        combined_mask[masks[0] > 0] = 4
```

論文の 41,605 インスタンスも再現できなかった。
自分の手 bbox 33,465 個 + 器具 8,140 個 と分解すると辻褄は合うが、**確証は得られていない**
（IoU > 0 で自分の手と重なる器具 bbox は 45,072 個、うち両手にまたがるものが 9,088 個。
`dataset_maker.py:35 assign_tools_to_hands()` の閾値・タイブレークを再現しても一致しない）。

### 3.3 【重大】手インスタンスの 44.9% が欠落

| クラス | 論文（bbox 由来） | `seg_ann` 実測 | 保有率 |
|---|---:|---:|---:|
| 1. First Person's Left Hand | 17,078 | 9,858 | 57.7% |
| 2. First Person's Right Hand | 16,387 | 9,548 | 58.3% |
| 3. Other Person's Left Hand | 13,605 | 6,921 | 50.9% |
| 4. Other Person's Right Hand | 10,103 | 5,182 | 51.3% |
| **合計** | **57,173** | **31,509** | **55.1%** |

`seg_ann` の split 別内訳:

| split | images | anns | cat1 | cat2 | cat3 | cat4 |
|---|---:|---:|---:|---:|---:|---:|
| train | 9,657 | 15,379 | 5,020 | 4,875 | 3,318 | 2,166 |
| val | 1,515 | 3,432 | 1,350 | 1,310 | 393 | 379 |
| test | 4,255 | 12,698 | 3,488 | 3,363 | 3,210 | 2,637 |
| **計** | **15,427** | **31,509** | 9,858 | 9,548 | 6,921 | 5,182 |

画像単位では 15,427 / 19,432 枚（79.4%）しか収録がなく、
**そのうちアノテーションが 1 件でもある画像は 9,623 枚（49.5%）にすぎない**。
5,804 枚（37.6%）はアノテーション 0 件である。

動画まるごと全欠落しているもの:

| video | split | 枚数 | アノテ有り | 欠落 |
|---|---|---:|---:|---:|
| 03_2 | train | 1,089 | 0 | 1,089 |
| 04_1 | test | 1,019 | 0 | 1,019 |
| 06_1 | train | 963 | 0 | 963 |
| 08_1 | train | 1,078 | 0 | 1,078 |
| **小計** | | | | **4,149** |

その他の部分欠落: 14_1 (1,163) / 07_1 (307) / 10_1 (132) / 12_1 (33) / 05_2 (10) /
06_2 (4) / 13_1 (3) / 11_1 (2) / 08_2 (1)。orphan annotation は 0 件、`image_id` は連番。
1 画像あたり最大 6 (train) / 10 (test) アノテーション。

**この JSON をそのまま学習・評価に使うと、欠落した 5,804 枚が「手が写っていない負例」として
扱われ、loss と mAP の両方が壊れる。**

### 3.4 【重大】`ann_dir` はセマンティックであり、インスタンスを復元できない

「PNG が完全版だから、そこから COCO を再生成すればよい」という救済策は **成立しない**。

`ann_dir` の全 PNG を connected components で走査した結果:

| ラベル | 出現フレーム数 | 対応する bbox インスタンス数 | 差 |
|---|---:|---:|---:|
| 1 (自分の左手) | 16,986 | 17,078 | 92 |
| 2 (自分の右手) | 16,299 | 16,387 | 88 |
| 3 (他者の左手) | 12,233 | 13,605 | **1,372** |
| 4 (他者の右手) | 8,852 | 10,103 | **1,251** |
| 計 | 54,370 | 57,173 | 2,803 |

同一クラスの複数インスタンス（他者が 2 人写るケース等）が 1 つの画素値に融合している。
connected components で数え直しても、SAM マスクが断片化しているため
label 1 だけで 55,638 成分（3.3 個 / frame）という無意味な値になる。

> **セマンティックマスクからインスタンスは原理的に復元できない**（同クラスの隣接インスタンスが
> 1 つの連結成分に融合するため）。逆方向（インスタンス → セマンティック）は常に可能。
> この非可逆性が「PNG から COCO を作り直す」救済策を潰している。復元には bbox を使って各マスクを
> 分割する必要があり、それは結局 SAM をもう一度回すのと等価である。

なお `seg_ann` の RLE をラスタライズすると、対応する `ann_dir` の PNG と
**pixel exact 100% / foreground IoU 100%** で一致する（両者は同一内容）。

### 3.5 SAM 疑似ラベルであることの証拠（4 点）

1. 同梱 `dataset_maker.py` が SAM (vit_h) に bbox をプロンプトしてマスクを生成する
   （空マスクのフレームは `if combined_mask.sum() > 0` でスキップされる）。
2. `HandToolDataset` の手マスク（label 1, 2）が `HandDataset` のものと**ピクセル完全一致**
   （72 サンプル中 68 が完全一致、残り 4 も IoU 1.000）。
3. HTS マスクの外接矩形が `bbox_all` の手 bbox に**内包**されている
   （n = 13,418、内包率 mean 0.879、IoU median 0.927、内包率 > 0.98 が 59.4%）。
   これは bbox プロンプト SAM の典型的な挙動。
4. **画像枚数の完全一致**（§2.1）。

`dataset_maker.py:35 assign_tools_to_hands()` にはバグもある。グローバルな `max_iou` で比較するため、
左手の割当が古い低 IoU のまま残りうる。

---

## 4. split 互換性 / フレーム対応

### 4.1 split — train/val は完全一致、test だけ壊れる

| split | `seg_ann` | `egosurgery_tool` | basename 一致 | image_id 一致 |
|---|---:|---:|---|---:|
| train | 9,657 | 9,657 | 完全一致 | 9,657 / 9,657 |
| val | 1,515 | 1,515 | 完全一致 | 1,515 / 1,515 |
| test | 4,255 | 4,265 | **10 枚欠落** | **1,384 / 4,255** |

test の欠落フレーム例: `05_1_0161.jpg`, `05_2_0036.jpg`, `05_2_0045.jpg`, `05_2_0048.jpg`, `05_2_0163.jpg` ほか。

> **両者を突き合わせるときは必ず `file_name` の basename で join すること。**
> `image_id` で join すると test の約 7 割が別フレームに繋がる。

`img_dir` / `ann_dir` 側は split 分割されておらず、全て `train/` 配下にある（26 videos）。
`seg_ann` に無い 4 clips（`03_1`, `03_3`, `12_2`, `15_2`）を含む。

なお **論文は train/val/test の内訳を一切公開していない**（動画数・画像数とも）。
「動画単位で分割した」とのみ記載（`egosurergyhts_open` §7）。

### 4.2 フレーム対応 — 同一フレームだが bit-identical ではない

- `img_dir` の JPEG は `data/raw/ego` と**同じフレームの再エンコード版**
  （最大画素差 81、平均 0.058、差分画素 0.40%、md5 は不一致）。
- `bbox_all` は 19,560 フレームで、`data/raw/ego`(15,437) に**存在しない 4,123 フレーム**を含む。
  これらの画像はバンドル内 `img_dir` 経由でしか入手できない。
- `data/raw/ego` の内訳: train 9,657 / val 1,515 / test 4,265 = 15,437。
  train = 01,02,03,06,08,11,12,13,14,15 / val = 09,10 / test = 04,05,07。

### 4.3 phase アノテーション

`annotations/phase/*.csv` は 46 本。

- 既存 23 本は `data/annotations/egosurgery_phase/` と**バイト単位で完全一致**。
- 新規 23 本（`17_1` 〜 `22_3`）は `data/raw/ego` に該当フレームが無く、**現状使えない**
  （`raw/ego` は 01〜15 のみ）。

---

## 5. カテゴリ体系の非互換

### 5.1 `annotations_bbox_all`（38 カテゴリ・133,071 anns・19,560 images）

手 4 種（id 10, 11, 21, 22）、`Eye`（id 9）、器具 33 種。

| id | name | n | | id | name | n |
|---:|---|---:|---|---:|---|---:|
| 1 | BiClamp | 297 | | 20 | Needle Holders | 5,307 |
| 2 | Bipolar Forceps | 713 | | 21 | **Other Person's Left Hand** | 13,605 |
| 3 | Bone Curette | 5 | | 22 | **Other Person's Right Hand** | 10,103 |
| 4 | Caliper | 2 | | 23 | Pen | 21 |
| 5 | Chisel | 53 | | 24 | Petri Dish | 150 |
| 6 | Cup | 94 | | 25 | Raspatory | 941 |
| 7 | Drill | 75 | | 26 | Retractor | 3,832 |
| 8 | Electric Cautery | 1,723 | | 27 | Ruler | 14 |
| 9 | *Eye* | 8,204 | | 28 | Scalpel | 1,125 |
| 10 | **First Person's Left Hand** | 17,078 | | 29 | Scissors | 2,911 |
| 11 | **First Person's Right Hand** | 16,387 | | 30 | Screwdriver | 79 |
| 12 | Forceps | 7,078 | | 31 | Skewer | 344 |
| 13 | Gauze | 7,870 | | 32 | Spoon | 27 |
| 14 | Hammer | 28 | | 33 | Suction Cannula | 5,360 |
| 15 | Hook | 1,472 | | 34 | Suction Tube | 70 |
| 16 | Kidney Dish | 67 | | 35 | Suture, Suture Needle | 6,421 |
| 17 | Malleable Retractor | 121 | | 36 | Syringe | 587 |
| 18 | Mouth Gag | 7,129 | | 37 | Trephine | 40 |
| 19 | Nasogastric Tube | 1,672 | | 38 | Tweezers | 12,066 |

手合計 = **57,173**（論文値と一致）。器具合計 = 67,694。

### 5.2 `annotations_bbox_tool_only`（31 カテゴリ・67,687 anns・19,560 images）

`bbox_all` の器具 33 種から `Bone Curette` (5) と `Caliper` (2) を除いた 31 種。
67,694 − 7 = 67,687 で整合する。

### 5.3 既存 `egosurgery_tool`（15 カテゴリ・49,652 anns・15,437 images）

| id | name | n | | id | name | n |
|---:|---|---:|---|---:|---|---:|
| 0 | Bipolar Forceps | 696 | | 8 | Retractor | 2,404 |
| 1 | Electric Cautery | 1,667 | | 9 | Scalpel | 1,066 |
| 2 | Forceps | 6,063 | | 10 | Scissors | 2,736 |
| 3 | Gauze | 6,695 | | 11 | Skewer | 344 |
| 4 | Hook | 1,349 | | 12 | Suction Cannula | 4,411 |
| 5 | Mouth Gag | 5,985 | | 13 | Syringe | 581 |
| 6 | Needle Holders | 4,829 | | 14 | Tweezers | 10,012 |
| 7 | Raspatory | 814 | | | | |

split 別: train 9,657 imgs / 32,272 anns、val 1,515 / 4,707、test 4,265 / 12,673。
**segmentation は 49,652 件すべてが矩形**（実ポリゴンは 0 件）。

### 5.4 既存 hand bbox との版ズレ

`bbox_all` の手 bbox vs `egosurgery_hand4`:

- **完全一致は 20%（4,350 / 21,613）**
- 幾何マッチ（IoU > 0.5）した 11,156 件の mean IoU = 0.806
- クラス対応の混同行列は**対角 97.3%**（自他・左右の定義は同じ）

→ **同じ対象の別バージョンのアノテーション**である。
混在させると S0 の Δ 基準点が汚染される（`CLAUDE.md` §研究インテグリティ）。

> **方法論メモ**: 当初、素朴にクラス ID だけで 1 対 1 マッチさせたところ IoU median 0.18 という
> 壊滅的な数字が出た。実際にはクラス意味は 97.3% 合っており、原因は「同一画像に同クラスの
> インスタンスが複数ある」ケースでのペアリング失敗だった。
> **幾何マッチ → 混同行列** の順で検証しないと、アノテーション互換性の判定を丸ごと誤る。

---

## 6. SurgerySegmentation

論文のどのタスクにも対応しない。9 動画 / 4,936 画像（全体の 26%）の
**31 クラス セマンティック**セグメンテーション。論文の「14 クラス instance」とは
クラス数・粒度・規模のすべてが異なる。

| video | img | ann | 備考 |
|---|---:|---:|---|
| 01_1 | 938 | 938 | |
| 02_1 | 460 | 460 | |
| 03_1 | **0** | 67 | **画像なし（孤児マスク）** |
| 04_1 | 920 | 920 | |
| 04_2 | 311 | 311 | |
| 07_1 | 750 | 750 | |
| 11_1 | 628 | 628 | |
| 15_1 | 696 | 696 | |
| 15_2 | 233 | 233 | |
| **計** | **4,936** | **5,003** | |

ラベル値は `annotations_bbox_tool_only` の `category_id` と直接対応する。実出現は 25 種:

```
 2 Bipolar Forceps    11 Kidney Dish          21 Scalpel
 4 Cup                12 Malleable Retractor  22 Scissors
 5 Drill              13 Mouth Gag            23 Screwdriver
 6 Electric Cautery   15 Needle Holders       24 Skewer
 7 Forceps            17 Petri Dish           25 Spoon
 8 Gauze              18 Raspatory            26 Suction Cannula
10 Hook               19 Retractor            27 Suction Tube
                      20 Ruler                28 Suture, Suture Needle
                                              29 Syringe
                                              31 Tweezers
```

未出現 6 種: BiClamp (1), Chisel (3), Hammer (9), Nasogastric Tube (14), Pen (16), Trephine (30)。

**`num_classes` の off-by-one は存在しない**（過去の指摘を撤回）。
`surgical_model.py:32` のコメント `# 31 classes (0-30)` は誤記だが、`train.py:54` の
`'num_classes': 32` が `train.py:97` で渡されるため、ラベル 0〜31 は正しく扱われる。

---

## 7. 秘密情報と git 事故リスク

### 7.1 第三者の API トークンがハードコードされている

```python
# SurgerySegmentation/train.py:66-67
project="OpenSurgery/OpenSurgerySegmentation",
api_token="eyJhcGlfYWRkcmVzcyI6Imh0dHBzOi8vYXBwLm5lcHR1bmUuYWki...",   # Neptune.ai
```

### 7.2 `.gitignore` が新規ディレクトリをカバーしていない

`.gitignore:10` は `data/annotations/**/*.json` のみを除外する。
**jpg / png / csv / py はすべて追跡対象**である。

```
$ git status -uall -- data/annotations/
→ untracked: 181,822 files / 約 16.4 GB
```

`git add -A` を一度でも実行すると、16.4 GB のデータと第三者のトークンが公開リポジトリに入る。

その他: ディレクトリのパーミッションは 700、画像ファイルに実行ビットが付いている。

---

## 8. 必要な対応

### P0 — commit 前に必須

1. `.gitignore` に新規 3 ディレクトリを追加する
   （または `data/annotations/**` を包括除外し、軽量ファイルだけ `!` で戻す）
2. `SurgerySegmentation/train.py:67` の Neptune トークンを除去する（環境変数化）

### P1 — データの入手し直し

3. **公式 EgoSurgery-HTS の配布物を入手する。**
   今回のバンドルには論文の 3 タスクのうち 2 つを学習する GT が物理的に存在しない。
   作者に問い合わせるか公式リリースを待つ以外に、Tool Instance Segmentation と
   5 クラス Hand-Tool を再現する方法はない。
4. 入手できない場合、このバンドルは `data/annotations/pseudo_labels/` 配下に置き、
   **GT ではなく SAM 疑似ラベルとして明記する**（論文値との比較には使えない）。

### P2 — 現状で使える範囲の整備

5. 手セグメンテーションのみ、`seg_ann` の 31,509 インスタンス（55.1%）で予備実験は可能。
   ただし**欠落を明示した manifest を必ず添える**。
   欠落フレームを「手なし負例」として扱うと loss と mAP の両方が壊れる。
6. 既存 split への射影は `file_name` の basename ベースで行う（test の 10 枚欠落を明記）。
7. `data/annotations/egosurgery_hts/`（`.gitkeep` で予約済み）への正規化配置。
   `data/README.md:16,45` に配置先として既に文書化されている。
8. 重複・可視化データの削除検討（**要ユーザー確認**）:
   - `HandDataset/test1/data`（2.5 GB 完全重複）
   - `masked_videos` 群（可視化のみ、計 約 7〜8 GB）
9. `SurgerySegmentation/03_1` の画像欠落（img=0 / ann=67）への対応。
10. phase の新規 23 本（`17_1`〜`22_3`）はフレーム入手まで保留。
11. tool の 38 / 31 カテゴリは既存 15 種と非互換。
    S0 の Δ 基準点保護のため既存実験に持ち込まない。

---

## 9. 未解決事項

| 項目 | 状態 |
|---|---|
| 論文値 `50,383`（器具インスタンス）の出所 | **特定できず**。subset-sum は偽解 4 件以上 |
| 論文値 `41,605`（Hand-Tool インスタンス）の出所 | **特定できず**。33,465 + 8,140 と分解すると整合的だが未確証 |
| 論文値 `19,496`（画像数）の出所 | **特定できず**。最近傍は「自分の手 or 器具」= 19,484（差 12） |
| 公式 HTS 配布物との照合 | **未実施**（外部ネットワークアクセスが必要） |

---

## 10. 本調査で撤回した過去の指摘

| 過去の記述 | 訂正 |
|---|---|
| 「`egosurgery_tool` は polygon seg」 | **誤り**。49,652 件すべて矩形。実ポリゴンは 0 件 |
| 「`surgical_model.py` に `num_classes` の off-by-one がある」 | **誤り**。`train.py` が 32 を渡すため実害なし。コメントが誤記なだけ |
| 「`ann_dir` の PNG が完全版だから COCO を再生成すればよい」 | **不成立**。セマンティックからインスタンスは復元できない |
| 「HTS seg bbox vs hand4 bbox の IoU mean = 0.244」 | **誤り**。素朴な 1 対 1 ペアリングの失敗。正しくは幾何マッチ後 mean IoU 0.806 |

---

## 付録: 検証コマンド

すべて読み取り専用。`.venv` の Python（cv2 4.11.0 / numpy 1.26.4）を使用。

```bash
# seg_ann の split 別・カテゴリ別インスタンス数
python3 -c "import json,collections; ..."   # §3.3

# segmentation が矩形か実ポリゴンかの判定
python3 -c "... len(s[0])//2 <= 5 → rect-like ..."   # §3.1

# ann_dir の全 PNG をラベル値 + connected components で走査（24 プロセス並列）
.venv/bin/python -c "import cv2; cv2.connectedComponents(...)"   # §3.4

# bbox_all の画像集合の濃度
python3 -c "... images w/ hand / tool / both ..."   # §2.2
```

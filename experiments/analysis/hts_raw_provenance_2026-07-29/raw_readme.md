# OpenSurgery Dataset — 完全版

一人称視点・開放手術映像の手 / 術具セグメンテーションおよび hand-tool（把持関係）アノテーション。

- 出典: OpenSurgery (Keio University, info.date_created = 2022-02-22)
- 収集元: `/home/nathan` 配下（Research/, Docker*/, Downloads/）
- 整理日: 2026-07-27

---

## 対象範囲

| 項目 | 値 |
|---|---|
| 動画 | 15本 / 26セグメント（`01_1` 〜 `15_2`） |
| 元フレーム総数 | 27,535 |
| アノテーション対象フレーム | 19,560 |
| 手アノテーションが実在するフレーム | 19,432 |
| 術具アノテーションが実在するフレーム | 18,499 |
| hand-tool アノテーションが実在するフレーム | 18,397 |

動画 16〜22 は phase / tool_presence の CSV は存在するが、**セグメンテーションは存在しない**（`/home/nathan` 全域を走査して確認）。

---

## フォルダ構成

### `00_master_annotations/annotations_raw/`
`01/` 〜 `15/annotations.json` — **これが全ての元データ**。

- 19,560 images / 133,071 annotations / **38クラス**
- 38クラス = 手4（`First/Other Person's Left/Right Hand`, id 10/11/21/22）+ 術具34
- `segmentation` は **100% が 4頂点の軸並行矩形**（実質 bbox 相当。真のマスク輪郭ではない）。
  22% は bbox と完全一致、残り 78% は bbox とは異なる矩形（座標系差の可能性）。
  **セグメンテーション学習には使えない**。真のマスクは以下の派生物を利用すること：
  - 手 → `02_hand/masks_per_class/` の PNG（バイナリ）
  - 術具 → `03_tool/coco_splits_*/` の JSON 内 RLE
  - 手⇔器具 → `04_handtool/masks/` の PNG（マルチクラス）または同 JSON の RLE
- 以下の 02〜04 は全てこのファイルから派生したもの（派生時に真のマスクが挿入されている）

### `01_frames/initial_videos/`
未加工の元フレーム 27,535枚（`<video>/<video>_<frame>.jpg`, 1920×1080）。
`Docker*/data/images/` のフラット版とファイル名集合が完全一致することを確認済み。

### `02_hand/` — 手（4クラス）
| パス | 内容 |
|---|---|
| `coco_splits_4cls/` | `train/val/test.json`。11,723 / 1,791 / 4,936 images、計 55,655 anns |
| `json_per_video/` | 動画セグメント別 COCO JSON 26本、計 57,173 anns |
| `masks_per_class/` | レンダリング済PNG 54,371枚。`<frame>_cat{10,11,21,22}.png` の**クラス別バイナリマスク**（画素値 {0,1}、1080×1920）。**全54,371枚検証済み: 空マスク 0 件、読取失敗 0 件、サイズ異常 0 件** |

クラス: `First Person's Left Hand` / `First Person's Right Hand` / `Other Person's Left Hand` / `Other Person's Right Hand`

### `03_tool/` — 術具
| パス | 内容 |
|---|---|
| `coco_splits_31cls/` | 31クラス版 `train/val/test.json`。13,654 / 1,403 / 3,051 images、計 54,137 anns。**⚠️ 学習用途では推奨しない**（下記参照） |
| `json_per_video/` | 動画セグメント別 COCO JSON 26本 |
| `coco_splits_14cls_cleaned/` | 低頻度クラスを除いたクリーニング版（14クラス、51,329 anns）。**学習用途はこちらを推奨** |
| `coco_splits_15cls_withkidney/` | 上記 + `Kidney Dish`（15クラス、51,052 anns） |

31クラス: BiClamp, Bipolar Forceps, Chisel, Cup, Drill, Electric Cautery, Forceps, Gauze, Hammer, Hook, Kidney Dish, Malleable Retractor, Mouth Gag, Nasogastric Tube, Needle Holders, Pen, Petri Dish, Raspatory, Retractor, Ruler, Scalpel, Scissors, Screwdriver, Skewer, Spoon, Suction Cannula, Suction Tube, "Suture, Suture Needle", Syringe, Trephine, Tweezers

> ### ⚠️ `coco_splits_31cls/` の既知の欠陥
> - **全 3 split で完全に 0 例のクラス**: `Mouth Gag` (master 7,129 anns)、`Suture, Suture Needle` (master 6,421 anns) — split 作成時に脱落
> - **train で 0 例**: 上記 + `BiClamp` (master 297 anns)
> - **val で 0 例のクラス 11個**、**test で 0 例のクラス 12個** — 少数クラスは評価不能
> - **31クラス分類器としては実質学習不能**。実験には `coco_splits_14cls_cleaned/` または `coco_splits_15cls_withkidney/` を使うこと

> **注意**: 術具のレンダリング済PNGマスクは元環境に存在しない。
> COCO JSON 内の `segmentation` は **圧縮 RLE 形式**（`{"size":[h,w], "counts": str}`）で、
> `pycocotools.mask.decode()` でバイナリマスクへ変換できる。中身は真の自由形状マスク
> （train 500サンプルで area/bbox median=0.24 = ポリゴンではなくピクセル単位の輪郭）。

### `04_handtool/` — どの術具がどちらの手に把持されているか
| パス | 内容 |
|---|---|
| `coco_splits_5cls/` | **5クラス版**（`Two Hands Tool` を含む最も完全なクラス定義）。5,668 / 2,094 / 1,344 images、計 34,175 anns |
| `seg_ann_4cls/` | 4クラス版 `train/val/test.json`。9,657 / 1,515 / 4,255 images、計 36,647 anns |
| `json_per_video/` | 動画セグメント別 COCO JSON 26本、計 62,087 anns |
| `masks/` | レンダリング済PNG 18,397枚。ディレクトリ名は `masks/train/` だが**実質は train/val/test の3split全部を含む**（動画別サブディレクトリ構造）。画素値 **0=背景, 1〜5=各クラス**（1=FP Left Hand, 2=FP Right Hand, 3=Left Hand Tool, 4=Right Hand Tool, 5=Two Hands Tool）。全枚数 1080×1920、空マスク 0、値5(Two Hands Tool)は 11.0%(2,019枚)のマスクに出現。**参照との対応**: train 5,655/5,668 (欠落13枚は全て動画13_1)、val 2,094/2,094完全、test 1,344/1,344完全。overlap時は手優先で上書き（例: 器具が手に握られている領域は手の値が残る）ため、**instance-level の完全情報が必要なら JSON RLE を per-instance でデコードすること** |

- 4クラス: `First Person's Left Hand` / `First Person's Right Hand` / `Left Hand Tool` / `Right Hand Tool`
- 5クラス: 上記 + `Two Hands Tool`

---

## 既存コピーとの関係（`/home/uchihashi` 配下）

| 手元のもの | 実態 |
|---|---|
| `HandDataset/data/ann_dir` | 手マスク 19,432枚。**欠落なし**（アノテーションが存在する全フレームを網羅） |
| `HandToolDataset/data/ann_dir` | 実は hand-tool マスクそのもの。`04_handtool/masks` と完全一致（18,397枚） |
| `HandDataset/annotations/tool_bbox/annotations_bbox_all` | 実は `00_master_annotations` と内容が完全一致（38クラス・segmentation付き）。名前が紛らわしいだけ |
| `SurgerySegmentation/data` | 9セグメントのみの実験用サブセット。元環境と同一 |

「手マスクが55%」と見えたのは、動画セグメント別 JSON の `images` を単純合計した 36,544 と比較したため。
各セグメントの JSON は親動画の全フレームを重複列挙するので二重カウントになる（19,432 / 36,544 = 53.2%）。
重複を除いた実際のアノテーション対象は 19,560 フレームで、うち手が写っている 19,432 フレーム全てにマスクが存在する。

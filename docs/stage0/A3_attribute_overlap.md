# A3 追加6動画と test 折りの術者・症例の重複

## 結論

**属性情報（術者・症例）は存在しない。** したがって重複の実測は行えない。
これ自体が R4 の前提の判断材料である。

## 実測

### 属性情報の探索

| 方法 | 対象 | 結果 |
|---|---|---|
| 名前で探す | `data/` 配下の `*surgeon*` `*patient*` `*case*` `*subject*` `*operator*` `*metadata*` | **1 件**: `data/splits/surgeon_folds.json` |
| 中身を読む | 同ファイル | **`{}`（3 バイト・空）** |
| 追加動画側 | `data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw/*/annotations.json` の `images` のキー | 該当キー **0 件** |

`data/splits/surgeon_folds.json` の素性

    バイト数: 3（`{}`）
    追跡下: yes
    作成 commit: af1fc587 2026-05-21 "Scaffold egosurgery_multitask project structure"

**プロジェクト初期の scaffold 以来、一度も中身が入っていない。**

### `annotations.json` の `images` が持つ全キー

    coco_url, date_captured, file_name, flickr_640_url, flickr_url, height, id, license, width

術者・症例・被験者を表すキーは無い。`info` にも `contributor: Keio University` のみで
個体を識別する属性は無い。

### 空振り確認（陽性対照）

同じキー検索で `"file"` を含むキーを探すと `['file_name']` が返る。
→ **検索は働いている。上の 0 件は「検出できていない」ではない。**

## 判断材料

- 術者・症例による層別や、それに基づく折りの設計は**現在のデータでは不可能**である
- A2 の実測（動画IDの重複 0 件）は確定しているが、**同一術者・同一症例が
  別の動画IDで現れているかは確かめられない**

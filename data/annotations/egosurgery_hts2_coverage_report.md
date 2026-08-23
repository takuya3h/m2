# EgoSurgery-HTS2 セグメンテーション被覆・分割整合性レポート

- 作成日: 2026-07-31 (JST)
- 目的: `data/raw/EgoSurgery_HTS2/{hand_seg,tool_seg,hand_tool_seg}` の
  annotated frame 集合が、既存の `egosurgery_tool/instances_{train,val,test}.json`
  の各 split をどれだけカバーするかを定量確認する。
  併せて **HTS2 側の split 割り当て**（same-split）が tool bbox の split と
  一致しているか（＝マルチタスク学習時にリークが起きないか）を検証する。
- 対象:
  - HTS2 側: `data/raw/EgoSurgery_HTS2/{hand_seg,tool_seg,hand_tool_seg}/{train,val,test,all}.json`
  - tool bbox 側: `data/annotations/egosurgery_tool/instances_{train,val,test}.json`

---

## 1. 集計方法

- HTS2 の各 `<split>.json` は `images` に動画全体（未アノテーション frame も含む）
  を列挙する形式（`hand_seg/train.json` の images=11,723 は annotated と一致するが、
  `tool_seg/train.json` は images=12,715 / annotated=12,016 と乖離）。
  そのため実 annotated 集合は **`annotations[].image_id` 経由**で再構築した。
- 突合キーは `file_name` を basename の拡張子除去した stem（例: `01_1_0124`）。
- tool split → HTS2 の被覆率は 2 種類算出:
  - **any split**: HTS2 の train/val/test 全体（annotated union）に対する被覆
  - **same-split**: HTS2 の同名 split（train↔train, val↔val, test↔test）に対する被覆
  - same-split が any-split より大きく下回る場合、HTS2 側が異なる split 割り当てを
    採用している証拠となる（リーク源）。

## 2. HTS2 各 JSON のサイズ

| dir | split | images (動画全体列挙) | annotated frames |
|---|---|---:|---:|
| hand_seg | train | 11,723 | 11,723 |
| hand_seg | val   | 1,791  | 1,791  |
| hand_seg | test  | 4,936  | 4,936  |
| hand_seg | all   | 19,432 | 19,432 |
| tool_seg | train | 12,715 | 12,016 |
| tool_seg | val   | 1,807  | 1,784  |
| tool_seg | test  | 5,038  | 4,511  |
| tool_seg | all   | 18,311 | 18,311 |
| hand_tool_seg | train | 5,668 | 5,668 |
| hand_tool_seg | val   | 2,094 | 2,094 |
| hand_tool_seg | test  | 1,344 | 1,344 |
| hand_tool_seg | all   | 12,229 | 12,229 |

## 3. tool split → HTS2 被覆率

### 3.1 hand_seg

| tool split | tool frames | HTS(any split) 被覆 | HTS 同名 split 被覆 |
|---|---:|---:|---:|
| train | 9,657 | 9,264 (95.93%) | 9,264 (95.93%) |
| val   | 1,515 | 1,501 (99.08%) | 1,501 (99.08%) |
| test  | 4,265 | 4,208 (98.66%) | 4,208 (98.66%) |

**判定**: same-split が any-split と完全一致 → HTS2 の split は tool bbox と同じ規則。
そのまま利用可。

### 3.2 tool_seg

| tool split | tool frames | HTS(any split) 被覆 | HTS 同名 split 被覆 |
|---|---:|---:|---:|
| train | 9,657 | 9,423 (97.58%) | 9,423 (97.58%) |
| val   | 1,515 | 1,512 (99.80%) | 1,512 (99.80%) |
| test  | 4,265 | 3,922 (91.96%) | 3,922 (91.96%) |

**判定**: same-split ↔ tool split 一致。test で 343 frame 欠落あり。

### 3.3 hand_tool_seg — **要注意**

| tool split | tool frames | HTS(any split) 被覆 | HTS 同名 split 被覆 |
|---|---:|---:|---:|
| train | 9,657 | 5,668 (58.69%) | 5,668 (58.69%) |
| val   | 1,515 | 1,344 (88.71%) | **0 (0.00%)** |
| test  | 4,265 | 2,094 (49.10%) | **0 (0.00%)** |

**判定**: HTS2 は hand_tool_seg で **別の split 割り当てを採用**。
- tool[val] の 1,344 frame は HTS2 では test 側に格納
- tool[test] の 2,094 frame は HTS2 では val 側に格納
→ 同名 split をそのまま使うと **クロス汚染（train↔test 相当のリーク）** が起きる。

## 4. image_list.txt との突合

| tool split | tool frames | HTS2/image_list.txt にある | 割合 |
|---|---:|---:|---:|
| train | 9,657 | 9,650 | 99.93% |
| val   | 1,515 | 1,515 | 100.00% |
| test  | 4,265 | 4,258 | 99.84% |

画像自体は 99.8% 以上が HTS2 側に存在。**画像不足がボトルネックではなく、
アノテーション（特に hand_tool_seg）と split 割り当てのミスマッチ**が主な問題。

## 5. 実務的な結論・推奨アクション

1. **hand_seg / tool_seg**: HTS2 の train/val/test をそのまま tool split と対応させて OK。
   欠落フレーム（hand_seg: train 393 / test 57、tool_seg: train 234 / test 343）は
   HTS 側で annotated 化されていないだけで、リークは無い。
2. **hand_tool_seg**: **HTS2 のオリジナル split をそのまま使ってはいけない**。
   - 対策 A: `hand_tool_seg/all.json` から tool split に合わせて再分割する
     （本レポートと同時に `data/hts_reconstruction/egosurgery_hts2_tool_aligned/hand_tool_seg/`
     を生成、`egosurgery_hts2_tool_aligned/README.md` 参照）。
   - 対策 B: hand_tool_seg 自体を疑似ラベル生成の対象に格下げする。
3. **既存 S0 との Δ 基準点**: tool split を維持する限り Δ 汚染は起きない。
   HTS2 の split に乗り換える場合は S0 からやり直しになる（推奨しない）。

## 6. 再分割後カバレッジ（`egosurgery_hts2_tool_aligned/hand_tool_seg/`）

§5 の対策 A に従い `HTS2/hand_tool_seg/all.json`（annotated=12,229 / annotations=41,605
/ categories=5）を tool split の image 集合と突合し、4 バケットに再分割した
結果を以下に示す。生成物は `data/hts_reconstruction/egosurgery_hts2_tool_aligned/hand_tool_seg/`
配下（`train.json` / `val.json` / `test.json` / `extra.json`）。原本
`data/raw/EgoSurgery_HTS2/` は改変していない。

### 6.1 再分割サイズ

| 出力 split | images | annotations |
|---|---:|---:|
| train | 6,723 | 23,373 |
| val   | 1,344 | 5,006 |
| test  | 2,094 | 7,220 |
| extra | 2,068 | 6,006 |
| **合計** | **12,229** | **41,605** |

`extra` は「HTS2 側で annotated だが tool split どれとも一致しないフレーム」
（削除せず退避）。

### 6.2 tool split に対する被覆率（再分割後）

| tool split | tool frames | 再分割後 hand_tool_seg frames | 欠落 | 被覆率 | HTS2 原 same-split との差 |
|---|---:|---:|---:|---:|---:|
| train | 9,657 | 6,723 | 2,934 | **69.62%** | +1,055 (58.69% → 69.62%) |
| val   | 1,515 | 1,344 |   171 | **88.71%** | +1,344 (0.00% → 88.71%) |
| test  | 4,265 | 2,094 | 2,171 | **49.10%** | +2,094 (0.00% → 49.10%) |

- val/test は HTS2 原 split では **完全ミスマッチ (0%)** だったので、再分割で
  ようやく使える形になった。
- train は元 HTS2 splits の train+val+test 合計 9,106 では届かなかった frame
  （all.json との差 3,123）を吸収し、+1,055 frame の追加を得た。
- test の 49% 欠落は原本 HTS2 が hand_tool_seg annotation を付けていない frame。
  疑似ラベル生成 or 学習時除外で対応する。

### 6.3 リーク検査

再分割後、tool split の train / val / test は元々互いに disjoint（コード上で
確認済み）。再分割は image_id → split の写像を tool split 側から一意に決めて
いるため、hand_tool_seg 側にも新規のクロス汚染は発生しない。

## 7. 参考

- `data/annotations/egosurgery_hts_bundle_audit.md`（HTS は公式ではなく
  bbox→SAM 派生・器具マスク未提供・Hand-Tool 4/5 クラス問題）
- `data/annotations/egosurgery_hts_frame_coverage_report.md`（HTS v1 に対する phase/tool 被覆）
- `data/annotations/egosurgery_split_consistency_audit.md`（split 独立性の別レポート）
- `data/hts_reconstruction/egosurgery_hts2_tool_aligned/README.md`（本レポートに基づく再分割成果物）

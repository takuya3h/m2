# EgoSurgery-HTS 3種 現在被覆率レポート

- 作成日: 2026-07-31 (JST)
- 目的: hand_tool_seg_v2 再構築後の HTS 3種
  (`hand_seg` / `tool_seg` / `hand_tool_seg_v2`) が、既存基準
  (`egosurgery_tool` bbox split / `egosurgery_phase` CSV) をどれだけカバーするかを
  一覧表示する。同時に **02_hand / 03_tool にも tool_split 整合を適用した新規生成物**の
  評価も含む。

---

## 1. 対象データ

### 1.1 基準（分母）

| 基準 | パス | 総フレーム数 | 内訳 |
|---|---|---:|---|
| `egosurgery_tool` bbox 全体 | `data/annotations/egosurgery_tool/instances_*.json` (images) | 15,437 | train=9,657 / val=1,515 / test=4,265 |
| `egosurgery_phase` (CSV) | `data/annotations/egosurgery_phase/*.csv` | 17,233 | 23 セグメント |

**tool_bbox ⇔ phase 相互被覆**:
- phase → tool_bbox: **15,437 / 15,437 = 100.00%**（phase は tool_bbox を完全に内包）
- tool_bbox → phase: **15,437 / 17,233 = 89.58%**（phase は tool_bbox より 1,796 f 密）

### 1.2 HTS ソース（分子）

**v1 直（Raw、tool_split 未整合）**:
- `HTS/02_hand` — `data/raw/OpenSurgery_Dataset/02_hand/json_per_video/` (26 seg, 4cls)
- `HTS/03_tool` — 同 `03_tool/json_per_video/` (26 seg, 31cls)
- `HTS/04_handtool` — 同 `04_handtool/json_per_video/` (26 seg, 5cls・v1 メタバグ有)

**tool-aligned 版（新規生成、tool_bbox split と整合）**:
- **`hand_seg/`** — 02_hand を tool split で再分割（新規、本レポートで生成）
- **`tool_seg/`** — 03_tool を tool split で再分割（新規、本レポートで生成）
- **`hand_tool_seg_v2/`** — 04_handtool を tool split で再構築（案A、既存）

**旧参考**:
- `hand_tool_seg/` — 生 HTS2 の tool 再分割版（deprecated、被覆率低）

---

## 2. HTS 全体の tool_bbox / phase 被覆率

| 種類 | 総フレーム | vs tool_bbox (15,437) | vs phase (17,233) |
|---|---:|---:|---:|
| **HTS/02_hand** v1直 (4cls) | 19,432 | 15,397 (**99.74%**) | 15,397 (**89.35%**) |
| **HTS/03_tool** v1直 (31cls) | 18,499 | 14,967 (**96.96%**) | 14,967 (**86.85%**) |
| **HTS/04_handtool** v1直 (5cls) | 18,397 | 14,977 (**97.02%**) | 14,977 (**86.91%**) |
| **`hand_seg/`** (新, 4cls) | 19,432 | 15,397 (**99.74%**) | 15,397 (**89.35%**) |
| **`tool_seg/`** (新, 31cls) | 18,499 | 14,967 (**96.96%**) | 14,967 (**86.85%**) |
| **`hand_tool_seg_v2/`** (新, 5cls) | 18,397 | 14,977 (**97.02%**) | 14,977 (**86.91%**) |
| 旧 `hand_tool_seg/` (deprecated) | 12,229 | 10,161 (**65.82%**) | 10,161 (**58.96%**) |

**tool-aligned 版と v1 直の被覆率は同一** — v1 の全 annotated frame が tool_bbox の
image 集合に含まれるため。差は「格納形式（split別 JSON か per-video JSON か）」のみ。

---

## 3. tool_split 3分割別 被覆率（新 tool-aligned 版）

| 種類 | train (9,657) | val (1,515) | test (4,265) | extra |
|---|---:|---:|---:|---:|
| **hand_seg** | 9,627 (**99.69%**) | **1,515 (100.00%)** | 4,255 (**99.77%**) | 4,035 |
| **tool_seg** | 9,528 (**98.66%**) | 1,512 (**99.80%**) | 3,927 (**92.08%**) | 3,532 |
| **hand_tool_seg_v2** | 9,356 (**96.88%**) | 1,514 (**99.93%**) | 4,107 (**96.30%**) | 3,420 |

`extra.json` は tool split の train/val/test どれにも属さない HTS 拡張フレーム。
学習には混ぜず、pretrain 等の別用途にのみ使用推奨。

### 3.1 tool_seg の test 被覆率 92.08% について

`tool_seg` の test で 338 f 欠落。原因は HTS/03_tool の元アノテーションが
tool_bbox test に対応する frame の一部を持たないため（05_1 で 269f 欠落など、
主に長い動画セグメントで annotator の作業が完了しなかった箇所）。

`hand_seg` (99.77%) と比べて低いのは、`tool_seg` は器具インスタンスのみ
アノテートされており、器具が写らないフレームは annotator がスキップ可能な仕様
だったと推測される。

---

## 4. phase 基準での欠落セグメント別分布

phase (17,233 f) は tool_bbox より 1,796 f 密なので、HTS はどの種類でも
phase 全体の 10〜13% を覆えない。

| 種類 | phase被覆 | phase欠落 | 主要欠落セグメント (top5) |
|---|---:|---:|---|
| HTS/02_hand (= hand_seg) | 15,397 | 1,836 | 04_1:238, 03_3:168, 09_1:154, 08_1:151, 10_1:135 |
| HTS/03_tool (= tool_seg) | 14,967 | 2,266 | 04_1:289, 05_1:269, 08_1:197, 03_3:168, 09_1:154 |
| HTS/04_handtool (= handtool_v2) | 14,977 | 2,256 | 04_1:248, 08_1:213, 03_3:168, 09_1:154, 07_1:153 |
| 旧 hand_tool_seg (deprecated) | 10,161 | 7,072 | 14_1:1408, 05_1:1139, 07_2:619, 14_2:450, 06_2:433 |

`03_3` (168 f) は HTS 3種すべてで完全欠落（全 HTS ソースにアノテーション無し）。
`egosurgery_hts_frame_coverage_report.md` §4 の指摘と一致。

---

## 5. 3種 HTS の相互重複（train split）

tool-aligned 3種を train split で比較:

| 集合 | フレーム数 |
|---|---:|
| hand ∩ tool ∩ handtool | **9,269** |
| hand ∩ tool (handtool 無視) | 9,505 |
| hand ∩ handtool | 9,356 |
| tool ∩ handtool | 9,269 |
| hand のみ | 35 |
| tool のみ | 23 |
| handtool のみ | 0 |
| **union (少なくとも1種の HTS あり)** | **9,650 / 9,657 (99.93%)** |

**tool_split[train] のうち HTS が 1種も無いフレームは 7 f のみ**。マルチタスク学習で
「3種のうちいずれかは使える」というカバレッジは実質完全。

---

## 6. 旧 → 新 (handtool) 改善効果

| 基準 | 旧 hand_tool_seg | 新 hand_tool_seg_v2 | 改善 |
|---|---:|---:|---:|
| vs tool_bbox | 65.82% (10,161f) | **97.02%** (14,977f) | **+31.20pt (+4,816f)** |
| vs phase | 58.96% | **86.91%** | +27.95pt |
| train 内被覆 | 69.62% | **96.88%** | +27.26pt |
| val 内被覆 | 88.71% | **99.93%** | +11.22pt |
| test 内被覆 | 49.10% | **96.30%** | +47.20pt |

---

## 7. 実験計画への含意

1. **hand / tool / handtool の 3タスクを同一 tool_bbox split で回すことが構造的に可能**
   - Union で 99.93% カバー、handtool 単独でも 96.88〜99.93%
   - Δ 実験 (S0〜S9) で split を揃えられる

2. **phase-認識と HTS を組み合わせる場合は 10〜13% 欠落を許容**
   - 主要欠落は `04_1`, `05_1`, `08_1`, `03_3`, `09_1` に集中
   - `03_3` (168f) は完全欠落なので疑似ラベル or 学習除外

3. **tool_seg の test 被覆 92.08% がやや低い**
   - test での器具検出評価をする場合は、欠落 338f を評価から除外する
     設計にする（`iscrowd=1` フラグ or subset filter）
   - 主に `05_1` (191f) と `08_1` (48f)

4. **loss_mask は現時点で hand_tool_seg_v2 のみに存在** (460f)
   - hand_seg / tool_seg にも同等の「構造的欠落」があるか要確認
     （hand_seg 40f, tool_seg 470f が tool_bbox に対して欠落だが、これは
     Mouth Gag / Skewer 除外ではなく annotator 未処理と推測される）
   - 必要なら hand_seg/tool_seg にも `loss_mask/` を作る

---

## 8. 生成コマンドと再現手順

```bash
# 汎用スクリプト (categories 自動抽出)
python3 data/hts_reconstruction/handoff_hts_seg_search/work/build_hts_split_aligned.py \
  --src        data/raw/OpenSurgery_Dataset/02_hand/json_per_video \
  --tool-split data/annotations/egosurgery_tool \
  --out        data/hts_reconstruction/egosurgery_hts2_tool_aligned/hand_seg

python3 data/hts_reconstruction/handoff_hts_seg_search/work/build_hts_split_aligned.py \
  --src        data/raw/OpenSurgery_Dataset/03_tool/json_per_video \
  --tool-split data/annotations/egosurgery_tool \
  --out        data/hts_reconstruction/egosurgery_hts2_tool_aligned/tool_seg

# hand_tool_seg_v2 (case A の 5cls 固定版, 既存)
python3 data/hts_reconstruction/handoff_hts_seg_search/work/build_hand_tool_seg_5cls.py \
  --src        data/raw/OpenSurgery_Dataset/04_handtool/json_per_video \
  --tool-split data/annotations/egosurgery_tool \
  --out        data/hts_reconstruction/egosurgery_hts2_tool_aligned/hand_tool_seg_v2
```

## 9. 関連ドキュメント

- `data/annotations/egosurgery_hts_frame_coverage_report.md` — HTS v1 単体の詳細被覆
- `data/annotations/egosurgery_hts2_coverage_report.md` — 旧 hand_tool_seg 生成レポート
- `data/hts_reconstruction/egosurgery_hts2_tool_aligned/README.md` — parent README
- `data/hts_reconstruction/handoff_hts_seg_search/work/SUMMARY.md` — 発掘・根本原因調査
- `data/hts_reconstruction/handoff_hts_seg_search/v1_recovery_report.md` — 回収レポート
- `docs/experiment_log.md` (2026-07-31) — 実験ログ

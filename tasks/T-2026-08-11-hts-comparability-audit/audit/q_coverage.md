# Phase A — 10 問の仕分け（既存の監査に答えがあるか）

判定基準: 「答えあり」と書くには **出典（ファイル名と節）を書けること**。書けないものは「答え無し」。

## 実在を確認した監査物

起票者が想定した 5 経路は **すべて実在した**（想定 → 実体の差 = 0 件）。
実体側から独立に走査したところ、**想定に無い監査物が 5 経路見つかった**（実体 → 想定の差 = 5 件）。

| # | 経路 | 想定にあったか | 規模 |
|---|---|---|---|
| 1 | `experiments/analysis/hts_next6_2026-07-29/` | あり | REPORT.md 16,916 B + csv/decisions/json/subsets |
| 2 | `experiments/analysis/hts_coverage_2026-07-30/` | あり | REPORT.md 6,795 B + csv |
| 3 | `experiments/analysis/g2_main_2026-07-29/` | あり | REPORT.md 20,108 B + csv/json/preregistration/subsets |
| 4 | `experiments/analysis/hts_raw_provenance_2026-07-29/` | あり | REPORT.md 12,643 B + json 11 本 |
| 5 | `experiments/audit/l0_hts_acceptance/` | あり | acceptance_report.json 4,352 B |
| 6 | `experiments/g2_followup_2026-07-29/` | **無し** | REPORT.md 41,337 B（622 行）+ csv/json/prereg/s3 |
| 7 | `experiments/g2_main_2026-07-29_lecun/` | **無し** | RESULTS.md 11,615 B + ログ 4 本 + csv |
| 8 | `experiments/g2_main_2026-07-29/HANDOVER_lecun.md` | **無し** | 13,656 B |
| 9 | `experiments/analysis/annotations_eda/REPORT.md` | **無し** | 488 行 |
| 10 | `experiments/audit/tool_class_distribution_2026-07-31/REPORT.md` | **無し** | 147 行 |

走査方法と件数（0 件の裏づけを含む）:

- `find -L experiments -maxdepth 3 -type d \( -name "*hts*" -o -name "*seg*" -o -name "*g2*" \)` → **8 件**
- `grep -rln "hand_tool_seg\|HTS\|hts" --include='*.md' experiments docs` → **25 件**
- 同じ grep を `--include=*.md`（引用なし）で実行すると **0 件**になる。これは不在ではなく
  **zsh がグロブを展開して失敗した**もの（`no matches found: --include=*.md`）。
  引用して再実行し 25 件を得た。**0 件を不在と読まないことの実例として記録する。**

## 10 問の仕分け

| 問い | 状態 | 出典 | 値の要約 |
|---|---|---|---|
| Q1 分割は術具の 10/2/3 と一致するか | **答えあり** | `hts_coverage_2026-07-30/REPORT.md` 結論 5 / `l0_hts_acceptance/acceptance_report.json` C5 | 4 ファイル（`02_hand/coco_splits_4cls`・`03_tool/coco_splits_14cls_cleaned`・`04_handtool/seg_ann_4cls`）は 10/2/3 一致。**`04_handtool/coco_splits_5cls` のみ val/test が入れ替わり、動画 03・14 が train から脱落**。C5 は canonical 枚数 9,657/1,515/4,265 が公式値と一致 |
| Q2 フレーム集合の重なり | **答えあり** | `hts_coverage_2026-07-30/REPORT.md` 結論 2・3・4 | 対 術具 15,437: hand 99.74% / tool 96.96% / **hand-tool 97.02%（欠落 460 は全て「注釈 0 件」＝正当な負例、宇宙外 0）**。対 工程 17,233: hand-tool 86.91%、**真の欠落 1,796 枚**。逆方向は HTS が術具 bbox に無いフレームを 3,420〜4,035 枚追加保有 |
| Q3 分割を跨ぐ重複 | **部分的** | `l0_hts_acceptance/acceptance_report.json` C4 | 現行 `data/annotations` 派生では frame も video も **train∩val = train∩test = val∩test = 0**（pass）。ただし測定対象は派生物であり、**HTS バンドル本体（`05_egosurgery_hts`）の分割については未測定** → Phase B で測る |
| Q4 クラス定義の対応 | **答えあり** | `hts_next6_2026-07-29/REPORT.md` §4 / `l0_hts_acceptance` C7 / `hts_raw_provenance` §5 | 術具側 4 版の対応表あり。VBS(15) → V14(14) は**一意写像**、signature 3 術具は生存、**`Mouth Gag` 5,985 ann は V14 に写像先なし**。V14 は box 座標が別導出（best-IoU median 0.871）で **I4 に抵触**。hand-tool 側 `raw04 5cls` は **1 First Person's Left Hand / 2 First Person's Right Hand / 3 Left Hand Tool / 4 Right Hand Tool / 5 Two Hands Tool** ＝術具 15 クラスとは直交する**手役割の体系** |
| Q5 注釈が無い 460 枚の偏り | **部分的** | `hts_coverage_2026-07-30/REPORT.md` 結論 2 | 460 枚が「注釈 0 件」であることと、動画別の 0 件率（tool seg で動画 05 が 21.31% と突出、他は 0〜4.7%）まで。**クラス別・工程別の内訳は無い** → Phase B で測る |
| Q6 把持関係ラベルの実在 | **部分的** | `hts_raw_provenance/REPORT.md` §0・追記 / `l0_hts_acceptance` C7 | `data/annotations/pseudo_labels/{hand_tool_relation,bbox_near_contact}` は**空の .gitkeep のみ**＝疑似ラベル不在。一方 **`raw04 5cls` のクラス体系そのものが把持関係**（Left/Right/Two Hands Tool）。さらに **HTI（把持フラグ）は GT 術具 bbox の決定論的関数＝リーク**と判定され、5ch 版は実装・使用しない方針 → 現ディスク状態を Phase B で確認 |
| Q7 どの基準点と比較できるか | **答え無し** | — | Phase C で索引から実測 |
| Q8 学習の母集団の変化 | **部分的** | `hts_coverage` 実験計画への含意 / `hts_next6` §2 T1 | 3 タスク同時に使えるのは hand ∩ tool ∩ hand-tool = 17,512 枚、対 術具 94.38%・対 工程 84.55%。工程主導だと 13% 前後を失う。**ただし T1 は同じ問いに 9,106 / 15,437 = 59.0% と答えており矛盾**（下記）。主課題側 loader への波及は未測定 → Phase B・C |
| Q9 容量増を織り込む要否 | **答え無し** | — | Phase C で前例を索引と文書から実測 |
| Q10 推論手順の制約 | **答え無し** | — | Phase C |

## 既存の監査どうしの食い違い（両方向の集合差で発見）

**同じ問い（術具 15,437 枚のうち hand-tool 領域注釈を持つ枚数）に 2 つの値がある。**

| 出典 | 値 | 読んだ対象 |
|---|---|---|
| `hts_next6_2026-07-29` §2 T1 | **9,106 / 15,437 = 59.0%**（判定 FAIL） | `04_handtool` の `by_split` / `merged_annotations.json` |
| `hts_coverage_2026-07-30` 結論 2 | **14,977 / 15,437 = 97.02%** | `json_per_video/<seg>/<seg>.json` を basename で dedupe |

差は **5,871 枚**。`hts_coverage` は後日（07-30）の監査で、**`coco_splits_5cls` は動画 03・14 が
train から脱落している**ことを実測しており、これが差の原因と整合する。同レポートは
「この split を捨てて `json_per_video` から 10/2/3 split を再構成すること」と述べている。

**この 1 点で補助課題の成立規模が 59% と 97% に分かれる。Phase B で直接測る。**

## 既存の監査が測っていて 10 問に無い項目（実体 → 問い の集合差）

| # | 項目 | 出典 | なぜ本 task に効くか |
|---|---|---|---|
| 1 | マスクの来歴（SAM 由来か bbox 由来か） | `hts_raw_provenance` §3・追記 / `hts_next6` §3 T2 | **2 つの監査で結論が逆**。raw bundle は「SAM 由来で確定」（論文 arXiv:2503.18755 に手法明記）、`05_egosurgery_hts` バンドルは「SAM 指紋を 3 トラックとも再現せず」。対象バンドルが違う。補助信号の教師がリークかどうかに直結 |
| 2 | HTI 把持フラグのリーク性 | `hts_raw_provenance` 追記 (2) | 把持フラグは GT 術具 bbox の決定論的関数。**5ch 版は SystemExit で拒否済み**。Q6 の設計を縛る |
| 3 | 手 bbox の正本不一致 | `hts_raw_provenance` §6・追記 | raw02（57,173）と hand4（46,320）は**別世代の独立アノテ**。完全一致 0.0%、best-IoU median 0.523、相似変換でも改善せず悪化。世代混在は Δ 基準点を汚染 |
| 4 | `merged_annotations.json` の整合性欠陥 | `hts_next6` §0.2 | dangling 1,404 件、annotation 0 件の画像 6,618（37.6%）。素直に読むと被覆率を 88.3% と誤認する |
| 5 | canonical split の間引き規則が不明 | `g2_main` §4 M3 | 未採用 3,660 枚は 92.7% が tool ann を持つが **phase ラベルが 1 件も無い**。評価枠の拡張は不可と確定済み |
| 6 | G-2 の結果（領域 > 矩形は 0/6 で FAIL） | `g2_main_2026-07-29_lecun/RESULTS.md` | 領域を入力チャネルに使う設計は既に否定。**チャネル追加自体は有効** |
| 7 | 同一 seed でも結果が再現しない | `g2_followup` §「重大な発見」 | σ の扱いと Δ の有意判定に直結 |
| 8 | 充填率 median 0.204 | `hts_next6` §3 | bbox の約 80% が背景。補助信号の期待効果量の根拠 |
| 9 | val に Retractor が存在しない | `tool_class_distribution_2026-07-31` F1 | per-class AP の評価可能性 |
| 10 | 術具 → 工程がほぼ決定的 | `annotations_eda` §5.2 | **Skewer → design 99.7%** / Mouth Gag → closure 54.2%。Q5 の偏りが工程へ波及する経路 |

## G1 判定

10 問すべてを「答えあり / 部分的 / 答え無し」に仕分け、両方向の集合差を取った。**G1 通過。**

Phase B の範囲を次に確定する（「答えあり」の Q1・Q2・Q4 は測り直さない）。

1. Q2 の 2 値の食い違い（59.0% と 97.02%）の決着 — **最優先**
2. Q3 の HTS バンドル本体での分割跨ぎ重複
3. Q5 の 460 枚のクラス別・工程別の内訳
4. Q6 の把持関係ラベルの現ディスク状態

# HTS 候補の受け入れ検証 — 三値の結論

- task_id: T-2026-08-30-hts-candidate-acceptance / kind: analysis
- 実行ホスト: andrew / GPU 不使用 / data 配下は読み取りのみ
- 基準の正: `scripts/audit_l0_hts_acceptance.py` の実装（C1–C5）

## 結論（三値）

**一部欠落。** 主判定 C1・C2・C4 を満たす候補は存在するが、**C3 を満たす候補は
一つも無く、実装どおりの C3 は現在の原資料からは原理的に満たせない。**

欠けているものと原資料の所在:

| 欠け | 内容 | 原資料の所在 |
|---|---|---|
| C3 の動画被覆 | 検査器は raw 02_hand の**ディレクトリ名 26 件**すべての被覆を要求する。うち `03_3` は手注釈を持たない | **無い。** `data/annotations` と `data/raw` の COCO JSON 全 291 個を走査し、`03_3_*` のフレームを持つ注釈は 0 件。フレーム自体は `01_frames/initial_videos/03_3/` に 261 枚実在し、工程注釈 `egosurgery_phase/03_3.csv` も実在する |
| C3 の件数 | 目標 57,173 は `hand_seg`(train+val+test+extra) の**単純加算**で一致するが、集合件数は 57,172 | 差 1 件は正本 `02_hand/json_per_video/05_1/05_1.json` の完全重複（`05_1_0575.jpg` / bbox `(0.0, 6.0, 940.0, 1066.0)` / cat 4 / ann id 1519 と 1520）。**目標値 57,173 自体がこの重複を含む** |
| C5 の画像数 | 真マスクを持つ `hand_seg` は 9,627/1,515/4,255 で公式 9,657/1,515/4,265 に 40 枚届かない | 不足 40 枚は**手注釈が 0 件のフレーム**。原資料の欠落ではなく、注釈ゼロのフレームを images に載せるかの設計差 |

**なお C5 は実装上の主判定ではない**（`main_keys = C1/C2/C3/C4`）。主判定を止めているのは C3 のみである。

## 基準 × 候補（PASS の候補）

| 基準 | 満たす候補 | 主判定か |
|---|---|---|
| C1 真マスク | `hts_hand_seg` `hts_hand_tool_seg` `hts_tool_seg` `raw04_5cls`（いずれも RLE 100%） | ○ |
| C2 値5=Two Hands Tool | `hts_hand_tool_seg`（cat5 注釈 2,021 件（train+val+test+extra）） `raw04_5cls` | ○ |
| C3 手 57,173 かつ欠落動画 0 | **無し** | ○ |
| C4 リーク不在 | 9 候補すべて | ○ |
| C5 公式 split 整合 | `hand4_deprecated` `tool_bbox` `tool_hand_19cls` | × |

数えた値と閾値は `criteria_matrix.csv`（45 行、空欄 0）を見よ。

## 組み立てるとしたら

C1・C2 は `egosurgery_hts/hand_seg`（手 4cls・RLE）と `egosurgery_hts/hand_tool_seg`
（把持 5cls・RLE・cat5 あり）の二つで揃う。C4 も揃う。**残るのは C3 だけであり、
その未達は組立作業では埋まらない**（`03_3` の手注釈が存在しないため）。

したがって選べるのは次のいずれかである。**本契約は判定に変換しない。決めるのはユーザーである。**

1. C3 の定義を「ディレクトリ名 26 件」から「手注釈が実在する動画 25 件」へ直し、
   件数の閾値を集合件数 57,172（または単純加算 57,173）と明記する
2. C3 未達のまま、手信号の腕を主測定の段から外す
3. `03_3` の手注釈を新規に作る（本契約の範囲外）

## 既存検査器の欠陥（実測）

1. **入力の不在を 0 件として通す。** `egosurgery_hand4` は `_deprecated/` へ退避済みだが、
   検査器は `data/annotations/egosurgery_hand4` を直接指しており、`_splits()` が
   存在しないファイルを黙って飛ばす。結果、C3 の手件数が 46,320 → **0** に、
   C5 が PASS → **FAIL** に変わった。判定（NOT ACCEPTED）は変わらないため気付かれない。
2. **C3 が型の違うものを比べている。** 左辺は `glob` によるディレクトリ名 26 件、
   右辺は `file_name` から導く動画 id 25 件。`03_3` は左辺にしか現れ得ないため
   `missing == []` は**構成上成立しない**。
3. **標本数の上限がある。** C1 の `seg_profile` は先頭 3,000 件しか見ない。
   本契約は全件（371,335 件の polygon を含む）を走査した。
4. **C5 は主判定に入らない**が、SPEC §2 は「C1 から C5 を正」と書いている。実装を優先した。

## 副次的な実測

- 実データに**真の多角形は 1 件も無い**。polygon 形式は全 371,335 件が 4 頂点（bbox 由来のダミー）で、
  真マスクはすべて RLE。検査器の polygon>4 頂点の枝は実データでは踏めない。
- `data/annotations/egosurgery_tool/hand/{train,val,test}.json` は
  `egosurgery_tool_hand/{train,val,test}.json` への symlink（配下内）。
- `data/annotations/egosurergyhts_open` は拡張子の無い Markdown 文書（綴りが `egosurergy`）。注釈ではない。
- 文書・スクリプトが指す `data/annotations` 配下の経路のうち **29 件が実在しない**
  （`egosurgery_hand4/` の旧経路、`hand_bbox/`、`handtool_seg_5cls/`、`pseudo_labels/` など）。

## 成果物

| ファイル | 内容 |
|---|---|
| `candidates.csv` | 走査 107 件（配下 63・参照先 44）。候補 71 件 |
| `criteria_matrix.csv` | 候補 9 × 基準 5 = 45 行。各セルに数えた値と閾値 |
| `combination.json` | 基準ごとの充足候補と、主判定の同時充足可否 |
| `candidates_raw.json` `criteria_raw.json` `hand_count.json` | 上記の生の実測 |
| `scan_candidates.py` `apply_criteria.py` `hand_count.py` `make_outputs.py` | 再現用 |

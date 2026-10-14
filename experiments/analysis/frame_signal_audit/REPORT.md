# Stage 2 の前提の実測 — フレームと注釈の対応、送り手信号の時刻と形、参照入力段、メタデータ、andrew の材料

契約 `T-2026-10-14-frame-signal-audit`（kind: analysis）。ホスト andrew、2026-10-14。
**装置を使わず、学習も推論もしていない。** 数値はすべて本ホストで実測した値で、未測定は UNKNOWN と書く。
表の出所は同じディレクトリの CSV / JSON（道具は `tools/`）。命令と出力は `tasks/T-2026-10-14-frame-signal-audit/audit.md`。

## 1. フレームと注釈の対応（Task B）

四つの集合を (動画, 区間, 番号) で作った。方法 A（`tools/audit_frames.py`、csv/json/os.walk で直接読む）と
方法 B（`tools/count_shell.sh`、cut / grep -o / find -L / comm）の区間ごとの件数は **43 区間 × 20 列 = 860 セルすべて一致**。

| 集合 | 件数 | 出所 |
|---|---:|---|
| 工程 CSV（43 区間、動画 01〜15 と 17〜21） | 27,694 = 17,233（01〜15、23 区間）+ 10,461（17〜21、20 区間） | `data/annotations/egosurgery_phase/*.csv` |
| 術具 COCO の画像（動画 01〜15、22 区間） | 15,437（train 9,657 / val 1,515 / test 4,265） | `data/annotations/egosurgery_tool/instances_*.json` |
| 本ホストの画像 `data/raw/ego/` | 25,898 = 15,437（train/val/test）+ 10,461（`other(17~21)`） | `find -L`、先頭ドットも走査（該当は `.gitkeep` 3・`.DS_Store` 1 のみ） |
| 工程塔 manifest（15 動画。三周目が使用） | 15,437（22 区間） | `data/processed/phase_manifest/{train,val,test}.json` |
| 工程塔 manifest（20 動画。P\*-20 が使用） | 25,898（42 区間） | `data/processed/stage1_features/p20_manifest/*.json` |

集合の関係（`summary_method_a.json`）: **術具 = manifest15 = ホストの画像（01〜15）** が完全一致（集合差 0）。
**manifest20 − manifest15 = ホストの画像（17〜21）= 工程 CSV（17〜21）** が完全一致。
術具にあって工程に無いもの 0。**工程にあって術具に無いもの 1,796**（動画 01〜15）＋ 10,461（17〜21 は術具注釈が無い設計）。

### 1.1 動画ごと（動画 01〜15。`sets_by_video.csv`）

| 動画 | 工程 | 術具 = 画像 = manifest | 工程のみ | 枠 0 個 | 工程のみの画像が配布物 `01_frames` に | 配布物 `01_frames` の生フレーム |
|---|---:|---:|---:|---:|---:|---:|
| 01 | 999 | 913 | 86 | 0 | 86 | 1,359 |
| 02 | 529 | 461 | 68 | 3 | 68 | 827 |
| 03 | 1,363 | 1,089 | 274 | 0 | 274 | 2,104 |
| 04 | 1,643 | 1,329 | 314 | 56 | 314 | 2,220 |
| 05 | 1,318 | 1,225 | 93 | 2 | 93 | 1,948 |
| 06 | 1,447 | 1,379 | 68 | 11 | 68 | 2,427 |
| 07 | 1,788 | 1,711 | 77 | 26 | 77 | 2,409 |
| 08 | 1,591 | 1,400 | 191 | 0 | 191 | 2,324 |
| 09 | 672 | 518 | 154 | 0 | 154 | 1,022 |
| 10 | 1,232 | 997 | 235 | 0 | 235 | 1,993 |
| 11 | 865 | 754 | 111 | 2 | 111 | 1,360 |
| 12 | 619 | 609 | 10 | 1 | 10 | 1,958 |
| 13 | 843 | 822 | 21 | 3 | 21 | 1,189 |
| 14 | 1,858 | 1,810 | 48 | 15 | 48 | 2,197 |
| 15 | 466 | 420 | 46 | 4 | 46 | 2,198 |
| 計 | 17,233 | 15,437 | 1,796 | 123 | **1,796** | 27,535 |

区間ごとは `sets_by_clip.csv`（方法 B は `sets_by_clip_method_b.csv`）。区間 **03_3 は工程 168 / 術具 0 / 画像 0 / manifest 0**。
片方にしか無いフレームの一覧は `phase_only_frames.csv`（1,796 + 10,461 行）、枠 0 個は `tool_zero_box_frames.csv`（123 行）。

### 1.2 起票者 §3.2 との照合

**全項目一致**（全体 14 項目、動画ごと 15 行 × 4 値。`summary_method_a.json` の `issuer_compare`）。
数え方は異質（起票者: 版管理の写しを読む。本契約: 方法 A は注釈とホストの画像と manifest、方法 B はシェル）。
術具注釈の画像だけを並べた列（22 区間）: 幅の合計 21,880、幅の中で画像の無い番号 6,443、飛び 1,013 か所、
大きさ 1 が 526 / 2〜4 が 286 / 5〜14 が 118 / 15〜59 が 60 / 60 以上が 23。工程 CSV（01〜15）の飛び 547 か所。

### 1.3 1,796 フレームの画像の所在

**1,796 枚すべてが `data/raw/OpenSurgery_Dataset/01_frames/initial_videos/<区間>/` に在る**（`data/raw/ego/` には無い）。
`data/raw/EgoSurgery_HTS2/images/` には 0 枚。異質な二通りで探した: (1) 方法 A の os.walk による集合演算、
(2) 配布物の README（`01_frames` = 元フレーム 27,535 枚）と `find -L` の区間ごとの枚数（26 区間、03_1・03_3・12_2・15_2 を含む）。
**1,796 枚は全数が復号でき、すべて 1920×1080。** 区間 03_3 の 168 枚もここに在る（`01_frames/03_3/` に 261 枚）。

### 1.4 復号と要約値

`data/raw/ego/` の 25,898 枚を全数復号: **復号できないもの 0、すべて 1920×1080、合計 4,079,408,682 バイト。**
要約値は各ファイルの sha256 を名前順に並べた行の連結の sha256 = `fb0b620e…`（動画ごとは `summary_method_a.json` の `decode.sha256_per_video`）。
追加動画 17〜21 の 10,461 枚も含む（P\*-20 の builder が要求した「注釈と画像の集合の一致」を本ホストでも確認: 20 区間すべて一致）。

### 1.5 枠 0 個の画像と手の注釈の被覆

枠 0 個の 123 枚は train 39 / val 0 / test 84。区間別: 04_1 56、07_2 18、14_2 12、06_1 11、07_1 8、15_1 4、02_1 3、13_1 3、14_1 3、05_2 2、11_1 2、12_1 1。
被覆レポート（`egosurgery_hts_frame_coverage_report.md`）の術具 bbox の数（15,314）は `annotations[].image_id` の集合で数えたもので、
本契約の画像の数 15,437 との差 **123 はちょうど枠 0 個の枚数**。レポートが挙げる「手の注釈に在るが工程に無い区間」03_1 / 12_2 / 15_2 は、
工程 CSV にも術具注釈にも manifest にも無い（配布物 `01_frames` には 156 / 269 / 516 枚、HTS2 には 127 / 8 / 317 枚が在る）。

### 1.6 時刻の根拠

| 問い | 実測 | 出所 |
|---|---|---|
| 番号は何の通し番号か | **区間ごとの抽出の通し番号（1 始まり）**。配布物 `01_frames/initial_videos/` の 26 区間すべてで番号が 1 から区間の枚数まで連続（欠けなし） | 方法 A の走査（audit.md） |
| 抽出の間隔 | **0.5 fps と repo の文書が書く。** 出所は原著の記載（EgoSurgery-Phase: Fujii ら 2024 MICCAI, arXiv 2405.19644）を引いた `docs/evidence/2026-09-16-A-phase-tower-candidates.md:30` と、計画書 `docs/m2_plan_rewrite/m2_plan_v2_full.md:32,102`（「研究方針 2026/05/14 の表に準拠、0.5 fps」） | 配布物の文書・注釈ファイル・JPEG（EXIF 無し、APP0 のみ）には fps の記載が無い |
| 番号 → 秒 | **UNKNOWN（仮定）。** 番号 n が区間の開始から 2n 秒に当たるかは、どの配布物にも書かれていない。本書で「秒」と書く値はすべて 0.5 fps を仮定した換算で、列名に `assumed_0.5fps` を付けた | — |

### 1.7 塔が見るフレーム列の飛び（`gaps_manifest15.csv` / `gaps_manifest20.csv` / `gap_events_manifest15.csv`）

manifest の並びは全区間で番号順（逆行 0）。番号の差から 1 を引いた値を「飛び」とする。

| 列 | 区間 | フレーム | 幅の合計 | 幅の中の欠け | 飛びの件数 | 1 / 2〜4 / 5〜14 / 15〜59 / 60+ | 最大 |
|---|---:|---:|---:|---:|---:|---|---:|
| manifest15（三周目） | 22 | 15,437 | 21,880 | 6,443（29.4%） | 1,013 | 526 / 286 / 118 / 60 / 23 | 253（12_1） |
| manifest20（P\*-20） | 42 | 25,898 | 35,356 | 9,458 | 1,316 | 622 / 393 / 174 / 94 / 33 | 329（19_6） |
| 工程 CSV（43 区間） | 43 | 27,694 | 36,929 | 9,235 | 850 | 306 / 277 / 136 / 89 / 42 | 329 |

manifest15 の飛びは中央値 1、平均 6.36、90 パーセンタイル 10、最大 253。0.5 fps を仮定すると、飛び 1 = 2 秒、10 = 20 秒、253 = 506 秒。
**連続する 2 フレームのうち 1,013 / (15,437 − 22) = 6.6% が隣接しない。** 区間ごとの最大は 06_1 221、12_1 253、10_1 188、10_2 163。

**区間の境界**（`summary_method_a.json` の `clip_boundaries`）: 2 区間以上に分かれる動画は manifest15 で 7 本（04・05・06・07・08・10・14）。
どの境界でも次の区間の番号は前の区間の最後より小さい（14_1 の 1684 → 14_2 の 1、06_1 の 1563 → 06_2 の 288 など）。
**番号は区間ごとに振り直されており、区間をまたいだ番号の差は時間の差を表さない。** manifest20 では 21_1（90）→ 21_2（108）だけが増加するが、
これも区間ごとの番号であって連続の保証は無い。

## 2. 塔が扱うフレーム列（Task C）

### 2.1 学習と評価に使った集合

| 塔 | manifest（run の config の `manifest_dir`） | キャッシュの行数（run の `all_gap.json` の `video_counts`） | 折り A の FT run の config | 出所 |
|---|---|---:|---|---|
| 三周目 P\*-COCO / P\*-ImageNet | `data/processed/phase_manifest` | 15,437 = manifest15 と一致（動画ごとも一致） | `train_frames: 9657` / `val_frames: 1515`（= 公式 train 10 本 / val 2 本の術具画像数） | `experiments/phase1/stage1_ptower_r3_{004,029,059}_*/config.yaml`、`data/processed/stage1_features/r3_coco_lr0.0001_foldA_seed42/all_gap.json` |
| P\*-20 | `data/processed/stage1_features/p20_manifest` | 25,898 = manifest20 と一致 | `train_frames: 20118`（= 9,657 + 10,461）/ `val_frames: 1515`。折り B は 20,225 / 1,861 | `experiments/phase1/stage1_ptower_20_{007,012,036}_*/config.yaml`、`…/p20_coco_lr0.0001_foldA_seed42/all_gap.json` |

入口（直前の契約の RESULT から）: 三周目は `scripts/stage1_ptower_r3.py`（時間ヘッドは `stage1_ptower.train`）、P\*-20 は `scripts/stage1_ptower_20.py`（`r3.finetune` / `r3.extract` / `base.train` をそのまま呼ぶ）。
起票者の `entrypoints` と一致する（一周目の道具を指す誤りは今回は無い）。

### 2.2 1,796 フレームと区間 03_3 が落ちる場所

**manifest の生成で落ちる**（`scripts/build_phase_manifest.py:78-93`: 画像 `data/raw/ego/<split>/<動画>/<frame>.jpg` が無ければ `n_missing` に数えて除く。
区間のフレームが 0 になれば区間ごと除く）。以後の fine-tune（`stage1_ptower_r3.py:59-73` の `FoldFrames` は manifest のフレームだけ）、
特徴抽出（同 303-305）、時間ヘッド（`stage1_ptower.py:199-204`）はすべて manifest を読むので、**学習・評価・特徴抽出のどこにも入らない。**
区間 03_3 は manifest に無い（動画 03 は 03_2 の 1 区間だけ）。P\*-20 も 15 動画の manifest を写すだけなので同じ（`build_phase_manifest_p20.py:114-117`）。

### 2.3 時間ヘッドの履歴と区間の境界

| 根拠 | 内容 |
|---|---|
| 実装の行 | `stage1_ptower.py:205-215`（`load_fold`）: 「One batch is one complete video, ordered by clip then manifest frame order」。動画の区間を番号順に並べ `np.concatenate` で **1 本の列に連結**し、`train`（300）と `evaluate`（265）はその列を 1 回の forward で流す。TeCNO は左側だけ pad する因果 dilated conv（`tecno_head.py:44-45`）なので、**区間の境界で履歴は初期化されず、前の区間の末尾が次の区間の先頭の履歴になる。** 候補 B の attention も同じ列の上で過去 `history`=30 ステップを見る（`stage1_ptower.py:242-245`）。受容野は候補 C（8 層）で `receptive_field: 1021` フレーム（config に記録。0.5 fps を仮定すると 2,042 秒） |
| run の記録 | 三周目・P\*-20 の run には列の作り方も動画ごとの値も記録されていない（`metrics.json` は全体値のみ）。**別の契約の記録**が裏づける: `T-2026-10-04-ptower-attribution-val`（dlsta）は `scripts/ptower_attribution.py:134-146` で同じ「区間を番号順に連結した動画 1 本の列」を作り直し、折り A・B・C × 2 系統で **run が記録した val J・acc を全桁再現**した（例 A/COCO 0.7065837936961685 / 0.8415841584158416。同 RESULT 判定 c）。別の列の作り方では再現しないので、塔が実際に見た列は連結された列である |

**Stage 0 の経路は違う。** `train_b2a.py:202-211`・`train_s4_tecno.py:119-123`・`train_t1a.py:181-188`・`extract_phase_context.py:78-83` は
**区間ごとに別々の forward** で、履歴は区間の先頭で初期化される。

### 2.4 評価の集計の単位（`src/egosurgery/metrics/phase.py`）

| 指標 | 単位 | 行 |
|---|---|---|
| macro Jaccard、frame accuracy、macro F1 | **全動画のフレームを合算**してから計算（動画単位の平均ではない）。macro は GT に存在するクラスだけの平均 | `compute` 211-233、`_frame_jaccard` 290-305 |
| edit score、segmental F1@{10,25,50} | `video_id` ごとに計算して平均 | 236-241 |
| `video_id` に渡るもの | Stage 1: **動画の識別子**（`stage1_ptower.py:213` が `(video, x, y)` を返し、265 の変数名 `clip_id` は動画を指す）。Stage 0: 区間の識別子（`train_b2a.py:210` など） | — |

起票者 §3.3 の「評価器にクリップの識別子を動画の識別子として渡しているように読める」は変数名の読みで、**実際に渡っているのは動画の識別子**である。
ただし Jaccard と accuracy は合算なので、識別子は segment 系の指標にしか効かない。

### 2.5 動画単位に直したときの変化

**UNKNOWN。** 三周目・P\*-20 の run は val の予測を保存していない（`predictions/` は空。`metrics.json` に動画ごとの値は無い）。
帰属解析の契約が val の予測を書いたのは dlsta の repo の外（`/home/ubuntu/local/ptower_attribution_20261005`）で、本ホストには無い。
repo にある `experiments/analysis/ptower_attribution/summary.json` は折り A の val 全体の値（n 1515、正解 1275 / 1300）だけである。
なお Stage 1 の列はすでに動画単位に連結されており、Jaccard は合算なので、「クリップ単位 → 動画単位」の差が出るのは Stage 0 の経路の edit / segmental F1 だけである。

## 3. 送り手信号の時刻と形、参照入力段（Task D）

### 3.1 経路ごとの表

| 経路 | 塔の出力 | 使うフレームの情報 | 鍵 | 受け手の突き合わせ | 欠けたとき | 形 | 出所 |
|---|---|---|---|---|---|---|---|
| Stage 0 工程文脈（P→D） | 凍結 S4 TeCNO の最終段の softmax | **同時刻 t と、同じ区間の t より前**（因果 TeCNO。未来は使わない。t 自身を含む） | manifest の `frame` | `train_t1b.py:125-138`: COCO の `file_name` の stem と名前で一致 | **0 ベクトル**で進む（件数を `miss_ctx` に出すだけ） | (N, 9) | `extract_phase_context.py:41-50, 78-88` |
| Stage 0 術具在否（D→P） | 凍結 Relation-DETR の検出 → クラス別最大スコア | **同時刻 t のみ**（フレーム単位の forward） | manifest の `frame` | `train_b2a.py:148-158`: manifest の `frame` と名前で一致 | **KeyError で停止** | (N, 15) | `extract_b2a_detsignal.py:47-56, 80-93` |
| Stage 0 領域トークン（D→P） | 同検出器のデコーダ最終層の query 埋め込み × スコア | 同時刻 t のみ | 同上 | `train_t1a.py:148-166`: 同上 | KeyError で停止 | (N, 15×256=3840) | `extract_t1a_regiontoken.py:78-95, 130-146` |
| 正解・術具在否 | GT 枠のクラス集合 → one-hot | 同時刻 t | COCO の stem | 同上 | 同上 | (N, 15) | `build_oracle_toolpresence.py:36-61` |
| 正解・手の特徴 | GT 手枠 → presence / count / geom | 同時刻 t | COCO の stem | `train_haux.py`（同じ作法） | KeyError | (N, 4) / (N, 4) / (N, 16) | `build_oracle_handfeature.py` 冒頭 |
| 正解・工程 one-hot（P→D） | manifest の label → one-hot | 同時刻 t | manifest の `frame` | `train_t1b.py:82-99` | 0 ベクトル | (N, 9) | 同左 |
| Stage 1 工程塔の出力を保存する経路 | **無い。** `stage1_ptower*.py` が保存するのは backbone の GAP 特徴（`all_gap.npz`、(15,437 or 25,898, 2048)）と checkpoint だけで、事後確率や時間ヘッドの状態は書かない | — | — | — | — | — | `stage1_ptower_r3.py:343`、`stage1_ptower.py:320` |
| Stage 1 検出塔の出力を保存する経路 | **無い。** 二周目の run には `eval_val.json` / `eval_test.json`（mAP）と `work/best_ap.pth` だけで、フレームごとの予測は無い。Stage 0 の `train_t1b.py` は `predictions/` に COCO 形式の結果を保存する（`run_artifacts`） | — | — | — | — | — | `experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/` の一覧 |

**どの既存経路も「同時刻 t」の信号で、「一つ前の時刻（t−1）まで」の規則は実装されていない。** 工程文脈は t 以前を含むが t 自身も含む。
受け手の照合はすべて名前の一致で、番号の演算は無い。

### 3.2 時刻の判定の陽性対照（`time_alignment_val.json`、`tools/time_alignment_check.py`）

判定の手順: 受け手の規則（名前の一致）で突き合わせ、区間内の並びを k ずらした正解との一致率が最大の k を判定値とする
（k =（行の中身の時刻）−（行の名前の時刻）。負は過去、正は未来）。対照は frame_ids を区間内で 1 つ先の名前へ付け替えた写し（名前 t の行が t−1 の情報を持つ）。

| 送り手（val、1,515 行、名前一致 1,515 / 1,515） | 一致率 k = −2 / −1 / 0 / +1 / +2 | 判定 | 0 と次点の差 | ずらした写しの判定 |
|---|---|---|---:|---|
| 工程文脈（S4 事後確率 9-d） | 0.8973 / 0.9008 / **0.9023** / 0.8902 / 0.8787 | 同時刻 | 0.0015 | ずらし(−1) |
| 術具在否（予測 15-d） | 0.9517 / 0.9588 / **0.9711** / 0.9591 / 0.9512 | 同時刻 | 0.0120 | ずらし(−1) |
| 領域トークン（15×256-d） | 0.9510 / 0.9582 / **0.9704** / 0.9586 / 0.9504 | 同時刻 | 0.0118 | ずらし(−1) |
| 正解・術具在否 | 0.6952 / 0.7526 / **1.0000** / 0.7526 / 0.6952 | 同時刻 | 0.2474 | ずらし(−1) |
| 正解・工程 one-hot | 0.9629 / 0.9815 / **1.0000** / 0.9815 / 0.9629 | 同時刻 | 0.0185 | ずらし(−1) |
| 正解・手 presence（4-d） | 0.6965 / 0.7427 / **1.0000** / 0.7427 / 0.6965 | 同時刻 | 0.2573 | ずらし(−1) |

6 経路すべてで、ずらさない写しは「同時刻」、ずらした写しは「ずらし(−1)」と判定された（対照 6 / 6 合格）。
工程文脈は 0 と −1 の差が 0.0015 と小さい（工程は長く、因果の事後確率が前後の時刻とも合うため）。判定は最大値で取っているが、この経路の判定の余裕は小さい。

### 3.3 参照入力段の四段

| 方向 | 空 | 予測 | 正解 | 正解と予測 | 出所 |
|---|---|---|---|---|---|
| 工程→検出（`train_t1b.py`） | `--zero-ctx`（文脈を 0 に固定した同じスケジュールの fine-tune。FiLM は zero-init なので恒等） | `--phase-source real`（S4 の事後確率 9-d） | `--phase-source oracle`（manifest の label の one-hot 9-d） | `--phase-source both`: **連結**、順序は正解 9 → 予測 9 の **18-d**。frame_id が食い違えば KeyError。モデル設定は `T1B_MODEL_CFG` で `num_phases` 18 のものを指す必要がある（版管理下の t1b 系 config 5 本はすべて `num_phases = 9`。18 の config は repo に無い） | 543-550、102-112、275-277、config `relation_detr_resnet50_egosurgery_t1b*.py:34-37` |
| 検出→工程（`train_b2a.py`） | 別の道具 `train_s4_tecno.py`（S4 base、入力 2048-d。`train_b2a.py` 自身に空段は無い） | `--tool-source pred`（15-d 最大スコア） | `--tool-source oracle`（GT 枠の one-hot 15-d） | `--tool-source both`: **連結**、順序は正解 15 → 予測 15 の **30-d**（入力 2048+30 = 2078）。食い違えば KeyError | 66-73、99-108、432-440 |
| 検出→工程（`train_t1a.py`、領域トークン） | 同上（S4 base） | 領域トークン 3840-d（+ 任意で術具在否 pred 15-d） | 領域トークンの正解段は無い。術具在否だけ `--toolpresence-source oracle` | **無い**（領域トークンの「正解と予測」は実装されていない） | 72-166、305-307、512-514 |

正解のラベルの時刻はすべて **同じフレーム t**（manifest の label、COCO の同じ画像の枠）。
起票者 §3.3 の行 2〜4（0 埋め、連結、30 次元）は実装と一致する。

### 3.4 L0〜L3 に当たる信号の形（実装と設定から。推論で確かめた値は 0 件）

**検出塔 COCO 系統**（`third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery.py`。二周目の run の `model_path` が指す設定）:

| 段 | 形 | 出所（行） |
|---|---|---|
| 入力 | 1920×1080 → 短辺 800・長辺 1333 の制約で 1333×750（`base_detector.py:45-47` の計算。32 の倍数へ pad すると 1344×768）。**計算値であり推論で測っていない** | config 91（`min_size=800, max_size=1333`） |
| backbone 各段 | ResNet-50 の layer2 / layer3 / layer4 = C3 512ch（stride 8）/ C4 1024ch（16）/ C5 2048ch（32）。1344×768 なら 168×96 / 84×48 / 42×24（計算値） | config 38（`return_indices=(1, 2, 3)`）、`resnet.py:448-450` |
| neck | 4 段 × 256ch（C3〜C5 の 1×1 射影 + C5 から stride 2 の 3×3 で 1 段追加 → 21×12（計算値）） | config 23, 28, 40-41、`channel_mapper.py:43-55` |
| query | 900 本 × 埋め込み 256-d、デコーダ 6 層。最終層の `class_head[-1]` は in 256 / out 15（`extract_t1a_regiontoken.py:121-123` の assert） | config 25, 23, 30 |
| クラス logits と枠 | `pred_logits` (B, 900, 15)、`pred_boxes` (B, 900, 4)（cxcywh、0〜1） | `relation_detr.py:110` |
| 後処理の出力 | sigmoid → 900×15 から上位 300 → `scores` (300,)、`labels` (300,)、`boxes` (300, 4)（xyxy、元画像の画素）。閾値・NMS なし | config 84、`post_process.py:22-43` |
| クラスの数 | 15 | config 24 |

**三周目 COCO 系統の工程塔**（候補 C / 8 層 / 平滑 0.30 / 履歴 30、`selection.json`）:

| 段 | 形 | 出所（行） |
|---|---|---|
| 入力 | 全画面、短辺 800（1920×1080 → 1422×800。三周目 RESULT の実測値） | `stage1_ptower_r3.py:47-53` |
| backbone の特徴 | ResNet-50 の layer4 を GAP した **2048-d**（キャッシュ `all_gap.npz` の `features` (15,437, 2048) float32 を実測） | 同 312-316, 340 |
| 時間ヘッドの状態 | TeCNO 2 段、各段 8 層、チャネル **64**（`num_f_maps`）。段 1 の出力 9-d、段 2 は段 1 の softmax 9-d を入力に 64ch で精緻化。候補 B（ImageNet 系統）は TeCNO の出力 9-d を 64-d に埋め込み 4 ヘッドの attention（過去 30 ステップ）→ 9-d | `stage1_ptower.py:256-257, 228-246`、`tecno_head.py:72-97` |
| 事後確率 | 9-d（最終段の logits の softmax。語彙は `phase_vocab.json`） | `stage1_ptower.py:265` |
| 受容野 | 1 + 4 × (2^8 − 1) = 1021 フレーム（run の config `receptive_field`） | `stage1_ptower.py:280` |

## 4. 動画のメタデータ（Task E）

| 項目 | 有無 | 値 | 探した場所と方法 |
|---|---|---|---|
| 術式 | **動画ごとは UNKNOWN** | データセット全体で「10 種類」（HTS 論文の抜き書き） | `data/annotations/egosurergyhts_open`、`data/README.md`、COCO の `info`/`videos`/`images`（`date_captured` は null、`videos` は名前だけ）、`00_master_annotations` の `info`（Keio University、2022-02-22）、配布物の README / AUDIT / SCALE_VERIFICATION、HTS2 README、`git grep -i "surgeon|術者|procedure|術式|operating room|手術室|撮影"`、JPEG の EXIF / APP（EXIF 無し、JFIF APP0 のみ） |
| 術者 | 動画ごとは UNKNOWN | 全体で「8 人」（同上）。`data/splits/surgeon_folds.json` は `{}` | 同上 |
| 手術室 | UNKNOWN | — | 同上 |
| 撮影日 | UNKNOWN | COCO の `info.year` 2020、`date_created` 2022-02-21（注釈ファイルの作成日であって撮影日ではない） | 同上 |
| 撮影機器 | UNKNOWN | — | 同上 + `git grep -i "gopro|tobii|eyewear|glasses|head-mounted|撮影機器|カメラ"`（該当は他データセットの説明のみ） |
| 動画の長さ | 注釈から計算できる値は下の表。**配布物に書かれた秒数は無い**。全体で「15 時間」（同上） | — | — |

動画の長さ（`video_length_from_annotations.csv`。秒は 0.5 fps を仮定した換算）:

| 動画 | 工程の区間 | 工程フレーム | 番号の幅の合計 | 配布物の生フレーム（区間数） | 幅 × 2 秒 | 生フレーム × 2 秒 |
|---|---:|---:|---:|---:|---:|---:|
| 01 | 1 | 999 | 1,275 | 1,359 (1) | 2,550 | 2,718 |
| 02 | 1 | 529 | 733 | 827 (1) | 1,466 | 1,654 |
| 03 | 2 | 1,363 | 1,823 | 2,104 (3) | 3,646 | 4,208 |
| 04 | 2 | 1,643 | 2,099 | 2,220 (2) | 4,198 | 4,440 |
| 05 | 2 | 1,318 | 1,874 | 1,948 (2) | 3,748 | 3,896 |
| 06 | 2 | 1,447 | 2,017 | 2,427 (2) | 4,034 | 4,854 |
| 07 | 2 | 1,788 | 2,349 | 2,409 (2) | 4,698 | 4,818 |
| 08 | 2 | 1,591 | 1,945 | 2,324 (2) | 3,890 | 4,648 |
| 09 | 1 | 672 | 854 | 1,022 (1) | 1,708 | 2,044 |
| 10 | 2 | 1,232 | 1,772 | 1,993 (2) | 3,544 | 3,986 |
| 11 | 1 | 865 | 1,351 | 1,360 (1) | 2,702 | 2,720 |
| 12 | 1 | 619 | 1,624 | 1,958 (2) | 3,248 | 3,916 |
| 13 | 1 | 843 | 1,121 | 1,189 (1) | 2,242 | 2,378 |
| 14 | 2 | 1,858 | 2,072 | 2,197 (2) | 4,144 | 4,394 |
| 15 | 1 | 466 | 544 | 2,198 (2) | 1,088 | 4,396 |
| 17 | 1 | 56 | 66 | — | 132 | — |
| 18 | 2 | 946 | 1,102 | — | 2,204 | — |
| 19 | 6 | 5,179 | 5,957 | — | 11,914 | — |
| 20 | 6 | 1,560 | 1,758 | — | 3,516 | — |
| 21 | 5 | 2,720 | 4,593 | — | 9,186 | — |

区間の間（例 14_1 の 1684 から 14_2 の 1）の時間は分からないので、動画の長さは区間の和の下限でしかない。
原著の記載で補える候補（問い合わせていない）: EgoSurgery-Phase（Fujii ら 2024 MICCAI, arXiv 2405.19644）、EgoSurgery-HTS（arXiv 2503.18755）、公式配布 `github.com/Fujiry0/EgoSurgery`。

## 5. andrew の材料の所在（Task F）

| 項目 | 実測 | 探し方（無いものは二通り） |
|---|---|---|
| 動画 01〜15 の画像 | `data/raw/ego/{train,val,test}/<動画>/`、15,437 枚、全数復号可、要約値は §1.4 | — |
| 追加 17〜21 の画像 | `data/raw/ego/other(17~21)/<動画>/`、10,461 枚（17: 56 / 18: 946 / 19: 5,179 / 20: 1,560 / 21: 2,720）、全数復号可、注釈と集合一致 | — |
| COCO 初期化の重み | `data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth`、196,140,106 バイト、sha256 `2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff`（三周目 RESULT の記録と一致） | — |
| 凍結源 | `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`、195,421,066 バイト、sha256 `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824` = `conventions#frozen_source` の正本と一致 | — |
| 検出塔の確定塔（二周目、5 折り × 2 系統） | `experiments/baselines/stage1_dtower_r2/d{coco,imagenet}_fold{A..E}_seed42/work/best_ap.pth`、10 本すべて在り各 195,421,066 バイト、`done.txt` は全て `rc=0`。sha256 の先頭は audit.md | — |
| Relation-DETR 本体 | `third_party/Relation-DETR/main.py` が在る（`find -L /home/ubuntu -maxdepth 6 -name main.py -path '*Relation-DETR*'` の唯一の該当）。checkpoints は seed42 / 123 / 456 | — |
| 専用の環境 | `.venv-relation-detr`（Python 3.11.16、torch 2.1.2+cu118）。`find /home/ubuntu -maxdepth 4 -name pyvenv.cfg` の該当 5 件のうち本 repo は `.venv` と `.venv-relation-detr` の 2 件 | — |
| 工程塔の道具 | `scripts/stage1_ptower.py` / `stage1_ptower_r3.py` / `run_stage1_ptower_r3.py` / `select_stage1_ptower_r3.py` / `stage1_ptower_20.py` / `run_stage1_ptower_20.py` / `build_phase_manifest_p20.py` の 7 本が `git ls-files` に在る | — |
| 記憶領域 | repo の領域 `/home/ubuntu/slocal2`: 全体 7,937,302,376,448 / 使用 5,839,825,068,032 / 空き **1,697,382,440,960 バイト**。`/`（`/home/ubuntu` と `/tmp`）: 空き 1,516,562,481,152 バイト | `df -B1` |
| 同期の途中か | Syncthing は稼働中（2 プロセス）。直近の記録は `sync-alerts.log` の同期だけで、本契約の走査中に `data/` の要約値は変わらなかった（§7） | `~/.syncthing.log` |

## 6. 起票者の下見との食い違い

| 箇所 | 起票者 | 実測 |
|---|---|---|
| §3.3 行 5（Stage 1 の評価） | 評価器にクリップの識別子を動画の識別子として渡しているように読める | 渡っているのは**動画の識別子**（§2.4）。Jaccard は合算なので識別子は segment 系にしか効かない |
| §1 の 2（設計文書の「一つ前の時刻まで」） | 規則があった | repo の `docs/` `context/` `tasks/` に該当する文言は無い（`git grep "一つ前の時刻|前の時刻まで"` 0 件）。実装にも無い。出所は UNKNOWN |
| §3.2 | 全項目 | 一致（§1.2） |

## 7. 無変更と装置（Task A・G）

- 装置: 開始時（2026-10-14 20:09 JST）も終了時も `nvidia-smi --query-compute-apps` は 0 件。本契約の処理は CPU（復号は 16 プロセス）
- `data/` への書き込み 0（`git status -- data/` は空。`make forbidden-check` pass、書いたのは `experiments/analysis/frame_signal_audit/` の 17 ファイルだけ）
- 注釈と manifest の要約値（工程 CSV 全体 / 術具 JSON 3 本 / manifest15 / manifest20）は開始時と終了時で一致（audit.md）
- 版管理下の注釈は起点 `origin/phase0` と木の要約値が一致（`egosurgery_phase` `4bc3bfff…`、`egosurgery_tool` `6bedcd36…`）

# 両塔の学び直し: 折り A のハイパーパラメータ探索（dlsta）

**task_id:** T-2026-10-22-tower-reselect-search-dlsta  **kind:** exp

**実行ホスト:** `dlsta`（repo は `~/local/m2`。`context/env-facts.md`「repo の位置」）。**GPU を使う。使ってよいのは GPU1–2 と GPU3–4 の二つの NVLink の組だけで、GPU0 は本契約で使わない**（利用者の決定 2026-10-21）。GPU1 には容器の外の使用が断続的に出る（env-facts）。待って空けば使ってよい。

## 1. 背景と目的

- 両塔（P\*-15-COCO と D\*-COCO）の学び直しは、処方をハイパーパラメータ探索で選び直す。折り A の探索は dlsta、上位 3 件の回し直しと確定の塔は andrew（F 2026-10-19、F 2026-10-21）。手続きは提案カード `docs/proposals/2026-10-21-tower-reselect-search.md`（四版。利用者の判定 2026-10-22）に書いてあり、本契約はその**探索の段**である
- 本契約が返すもの: 塔ごとの 20 点の値の表、上位 3 件、1 位、0 番との差、記録する量（prereg §5）。**選定は行わない。** 回し直しの契約（andrew）は本契約の上位 3 件と 0 番を引く
- 規則は `prereg.md` に全段ある。**結果を見てから規則を足さない。** prereg の commit が学習の前であること（P4）
- 前の契約で測ったこと: dlsta で両塔が回ること（`T-2026-10-19-dlsta-tower-feasibility`。REPORT は `experiments/analysis/dlsta_tower_feasibility/REPORT.md`）、工程塔の二枚の道（`T-2026-10-21-ptower-multigpu-syncbn`。PR #249。README の「工程塔三周目を複数の GPU で回す道」）。本契約はどちらの実装も変えない。足すのは道具（§6 Task B）だけ

## 2. 利用者の決定（本契約が従うもの）

| 日付 | 決定 | 本契約での扱い |
|---|---|---|
| 2026-10-21 | dlsta で回す実験はハイパーパラメータ探索のためだけに使い、ほかの比較には一切用いない | 探索の値と順位を、ほかのホストの値と順位に並べて読まない。異常の検知にほかのホストの値を使わない（prereg §6） |
| 2026-10-21 | GPU1–2 と GPU3–4 だけを使い、GPU0 は使わない | §6 Task C・D。完了判定 j |
| 2026-10-21 | 候補 0b の repo の外の記録（約 10 GB）を片付ける | Task A.2 でそのディレクトリだけを消す |
| 2026-10-22 | カードの判定（却下表の A・B・C・D・E・F・O を採用） | prereg に反映済み。第二の軸は縮みの量 S、勾配と重みのノルムの記録、環境の記録、0 番の回し直し（次の契約） |
| 2026-10-19 | 案 2（両塔とも同じ数の設定を折り A で探し、上位 3 件を 5 折り × 2 種で回し直す）。費用は記録だけ | 点の数 20。費用を候補を狭める理由にしない |
| 2026-10-16 | 工程塔は工程注釈のある全フレーム（17,233）で学習・評価する | Task B.1 で manifest を作る。旧い manifest は残す |

## 3. 確定した事実

ホストによらない値と、dlsta 自身の実測だけを書く。前のホストの値を定数として引き継いでいない。

| 事実 | 出所 |
|---|---|
| 工程塔の処方は hydra の設定 `configs/stage1_ptower_r3.yaml` で、`ft_lr`・`ft_weight_decay`・`ft_accum_steps`・`ft_batch_size`・`step`・`cache`・`manifest_dir`・`task_id` は命令行の key=value で上書きできる。optimizer は AdamW（`scripts/stage1_ptower_r3.py` の 202 行付近）。証拠の名前は `ft_{init}_lr{ft_lr}_fold{fold}` で weight decay と累積を含まない | 設定と実装（phase0 39dd92d6） |
| 工程塔の二枚の道は `torchrun` で起こすと入る。`ft_batch_size` は全 rank を合わせた物理 batch。同じホストで二本を同時に起こすときは `--master_port` を分ける。train のフレーム数を 16 で割った余りが 1 だと始まらない（`ShardedBatches`） | README「工程塔三周目を複数の GPU で回す道」、`scripts/stage1_ptower_r3_dist.py` |
| 検出塔の処方は `third_party/Relation-DETR/configs/train_config_egosurgery_seed42.py` の定数（`learning_rate` 1e-4、`weight_decay` 1e-4、`max_norm` 0.1）。群は `param_dict.finetune_backbone_and_linear_projection`（本体 2 群が lr、backbone と線形射影の 4 群が lr × 0.1。norm と bias の群は weight decay 0）。`third_party/` は版管理の外で、改変は `third_party_snapshot/` の patch と tarball で持ち運ぶ | `third_party_snapshot/efros/2026-10-17/Relation-DETR/`（README と patch）、`scripts/restore_relation_detr_source.sh` |
| 検出塔の起動は `scripts/run_stage1_dtower.sh`（環境変数 `DTOWER_EXP_DIR`・`DTOWER_TASK_ID`・`DTOWER_EXTRA_ARGS`。`RELDETR_OUTPUT_DIR` が work の置き場）。二周目は `--convergence-schedule --max-epochs 36` を足した | 同スクリプトと `experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/command.sh` |
| dlsta では `EGO_ROOT` と `RELDETR_COCO_CKPT` を与えないと COCO の重みを読まずに学習が進む。評価の道具 `scripts/eval_relation_detr_map.py` に checkpoint を相対経路で渡すと重みを読まずに AP 0 を返す | REPORT §2（dlsta の実測） |
| dlsta の検出塔（処方そのまま、2 枚）: 一歩 0.598 秒、1 epoch 2,405 歩、二つの NVLink の組で 2 本同時でも遅くならない、通信の設定は要らない | REPORT §2 |
| dlsta の工程塔（二枚の道、処方そのまま）: 一歩 0.79〜0.82 秒、rank ごとの最大確保 14.9 GB。特徴の取り出しは一枚で約 401 秒（15,437 フレーム）、時間ヘッド 1 本は一枚で約 10 秒 | env-facts の dlsta の行、REPORT §3 |
| 工程注釈だけの 1,796 フレームの画像は `data/raw/ego` に無く、配布物 `data/raw/OpenSurgery_Dataset/01_frames/initial_videos/` に在る。`scripts/build_phase_manifest.py` は `data/raw/ego` に画像が無いフレームを落とす | REPORT §7、`tasks/T-2026-10-14-frame-signal-audit/RESULT.md` 完了判定 d、同スクリプトの冒頭の説明 |
| 同期（Syncthing）は `experiments/**/*.pth`・`experiments/**/checkpoints`・`experiments/**/logs`・`data/processed` を全台に配る。`experiments/baselines/_*` は配らないが、収穫も `_` 接頭辞を解析対象外とする | `.stglobalignore`、`tools/harvest_runindex.py` の冒頭 |
| 既存のカードの検査と P14 は通る（前の契約 `T-2026-10-22-proposal-card-tower-reselect-search`。PR #252 は統合済み） | 同契約の RESULT |
| 実行直前検査 P5 は exp の契約で必ず走り、`conventions#frozen_source` の checkpoint（`third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`）の要約値を照合する。本契約はこの凍結源を使わないが、検査は省けない。dlsta にこのファイルが在るかの記録は無い | `tools/preflight_task.py` の P5、規約 frozen_source |

## 4. 分母と参照の扱い

- `inputs.denominator` は三周目の確定処方の折り A の実験（ilya、3 seed）を指す。**これは索引の参照先であり、比較の分母ではない。** 本契約の 0 番は同じ処方を dlsta で学んだものだが、その値を分母の値と並べて読まない（§2 の 2026-10-21 の決定）。検出塔の現行の処方は二周目の `experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42` ほか 2 seed（索引の experiment_id は一周目と二周目が同じ鍵に束ねられている。報告で指すときは run の経路で指す）
- `frozen_source` は本契約に無い。P5 は規約の凍結源を照合する（§3 の最後の行）。**無ければ L3 で止まる。** その場合は表示を貼って諮る（起票者は dlsta に在るかを測っていない）
- `conventions_rev` と `runindex_commit` と counts は実行者が実測して差し替える（起票時の値は phase0 39dd92d6 の前の版のもの。差があれば `meta.amendments` に書く）

## 5. 出力の置き場と名前

| もの | 置き場 | 規則 |
|---|---|---|
| 工程塔の run（backbone、特徴、時間ヘッド） | `experiments/phase1/stage1_ptower_search/`（`step` を `stage1_ptower_search` にする） | 証拠の名前に点の番号を含める（実装の `desc_suffix` か、名前の規則の最小の変更。一枚の既定の振る舞いを変えない）。`config.yaml` に `task_id`・点の番号・点の 3 値を刻む |
| 検出塔の run | `experiments/baselines/stage1_dtower_search/` | run 名に点の番号を含める。`config.yaml` に同上を刻む |
| 表・環境・GPU の記録・点の表の写し | `experiments/analysis/tower_reselect_search_dlsta/` | `points.csv`（prereg §2.1 の 20 行をそのまま）、`env_dlsta.json`、`results_ptower.csv`・`results_dtower.csv`（20 行ずつ）、`top3.md`、`records.csv`（prereg §5 の量） |
| checkpoint、accelerate の状態（work）、特徴のキャッシュ、学習の生の記録 | repo の外 `~/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/` の下 | **同期の対象の経路（`experiments/` と `data/processed/`）に置かない。** 各 run の `notes.md` に実際の経路を書く。消さない（残置は利用者の判断） |
| 工程塔の manifest（規約の主測定の集合） | `data/processed/` の下に、既存の `phase_manifest` と**別の名前**で | 小さい JSON だけ。画像は複製しない（`no_raw_write`） |

`experiments/` と `data/processed/` に本契約が足したファイルの最大の大きさを報告する（完了判定 k）。

## 6. Task

### Task A — 開始状態と prereg

1. `prereg.md` を学習の前に commit し、`spec.yaml` の `prereg.commit` と `committed_at` を実測で埋める
2. 候補 0b の repo の外の記録 `~/m2-scratch/T-2026-10-21-ptower-multigpu-syncbn/` の大きさを測って記録し、**このディレクトリだけ**を消す。消した後に不在を確かめる。消す操作が拒まれたら回避せず停止して諮る（env-facts「実行基盤の制約」）
3. 開始状態: 分岐が `feat/` で始まり起点が `origin/phase0`。作業ツリーが清浄（手順書「0. 始める」の出力を写す）。五枚の GPU の使用量と compute プロセスの所有者（`/proc/PID/exe` で絞る。陽性対照: 自分の python を一つ GPU1 に起こして 1、存在しない PID で 0）。版（§3 の表の出所と同じ項目）。試験の失敗の名前の集合
4. 環境を記録する（prereg §7 の項目。`env_dlsta.json`）
5. 入力と道具の実在と要約値: 折り A の術具注釈（`data/annotations/egosurgery_tool_folds/A/`）、工程注釈の CSV、`data/raw/ego` の画像、配布物 `01_frames/initial_videos/` の画像、COCO の checkpoint（`data/external/weights/`）、`third_party/Relation-DETR` の本体と `.venv-relation-detr`、`.venv`。要約値は可否確認の `inputs_inventory.json` と照合する。欠けか不一致があれば停止して諮る
6. 記憶領域の空きを測る。見込み（検出塔 20 本の work と工程塔 20 本の checkpoint と特徴。REPORT §6 の大きさから起票者が計算した約 75 GB）の 2 倍を下回れば諮る
7. `conventions_rev`・`runindex_commit`・counts を実測して差し替える

### Task B — 道具の準備

1. **工程塔の manifest。** `scripts/build_phase_manifest.py` を拡張し、規約 frame_sets の主測定の集合（動画 01〜15 の工程注釈のある全フレーム。画像が `data/raw/ego` に無いフレームは配布物の画像を指す）で、既存と別の名前の manifest を作る。既定の振る舞い（既存の名前と中身）は変えない。前提の確認を先に行う: 配布物と `data/raw/ego` の両方に在る 15,437 枚が同一か（要約値の照合。違えば停止して諮る）。出来た manifest の総フレーム数、折り A の train と val のフレーム数、train を 16 で割った余り、動画ごとの数を記録する。余りが 1 なら停止して諮る（二枚の道が始まらない）
2. **検出塔の点ごとの値を渡す口。** 学習率・weight decay・max_norm を点ごとに与えられる設定を、**版管理の中**（`configs/detector_relation_detr/` か `scripts/`）に置く。既存の `train_config_egosurgery_seed42.py` と `run_stage1_dtower.sh` の既定の振る舞いは変えない。`third_party/Relation-DETR` の本体に変更が要る場合（勾配のノルムの記録、群ごとの値の記録）は、変更を `third_party_snapshot/dlsta/` の下に efros/2026-10-17 と同じ様式（README、patch、tarball、sha256sums）で写し、回し直しの契約（andrew）が同じ変更を当てられるようにする
3. **検出塔の記録の口。** optimizer の群ごとの実際の学習率と weight decay を学習の記録に出す。刈り込む前の勾配のノルム（毎歩）と刈り込みが働いたかを記録する（prereg §5 の 7 と 8）。work（`RELDETR_OUTPUT_DIR`）を §5 の repo の外の置き場に向ける口を `run_stage1_dtower.sh` に足す（環境変数で足りる形）
4. **工程塔の記録の口。** backbone の checkpoint での train frame accuracy、時間ヘッドの train macro Jaccard、群ごとの重みのノルムの変化（初期化の重みと checkpoint から出す）が記録に無ければ、学習を変えずに後から出す道具を足す（評価だけ）
5. **陽性対照（口が効くこと）。** 検出塔は数歩だけ回す写しで、与えた学習率・weight decay・max_norm が optimizer の群と刈り込みに届き、変えると記録の値が変わることを示す。工程塔は `ft_weight_decay` と `ft_accum_steps` を変えた数歩の写しで、記録の値と実効 batch が変わることを示す。写しは repo の外に置き、消す
6. 試験を全件回し、失敗の名前の集合が Task A.3 と同じであること。足した道具の試験を `tests/` に置く（CPU だけで回るもの）
7. 点の表 `points.csv` を prereg §2.1 からそのまま写し、20 行・3 値が prereg と一致することを照合する

### Task C — 殺し実験（カード §9。4 本）

1. 検出塔の 0 番と 13 番を、二つの NVLink の組で同時に回す（各 2 枚、GPU ごとの batch 2、fp16、`--convergence-schedule` と上限 36、`EGO_ROOT` と `RELDETR_COCO_CKPT` を与える、port を分ける）。学習の記録に `load pretrained` の行が在り、読んだ経路が dlsta の COCO の checkpoint であること、群ごとの値が点の値であること（本体 2 群が点の値、4 群が 0.1 倍）を確かめる
2. 続けて工程塔の 0 番と 13 番を、二つの組で同時に回す（`torchrun` の二枚の道、GPU ごと 8 枚、fp32、決定性あり、`--master_port` を分ける）。`ft_weight_decay`・`ft_accum_steps` が記録の値と一致すること、backbone の初期化の要約値が COCO の checkpoint の R50 部分と一致すること（三周目の記録 `backbone_init_sha256` と同じ値）
3. 各 backbone から特徴を取り出し（折り A の train と val の全フレーム、新しい manifest）、時間ヘッド 10 構成を学ぶ。取り出しと時間ヘッドは組の一枚で回す（GPU0 は使わない）
4. 検出塔の評価: `eval_relation_detr_map.py` に **checkpoint を絶対経路で**渡し、val mAP・標的群 AP・陰性対照群 AP、train mAP を出す。記録に読み込みを飛ばした行が無いこと。AP 0 なら停止して諮る
5. 4 本について prereg §5 の量がすべて埋まることを確かめる（埋まらない量は実装を読んで口を足す。Task B.3・B.4 の範囲で）
6. §8（prereg §6）の異常が無いこと。あれば停止して諮る。4 本の値は探索の点の値としてそのまま使う（実装を直した場合は 4 本を回し直す）

### Task D — 残りの 36 本

1. 両塔の 1〜19 番（13 番を除く）。順番は実行者が決める（二つの組を空けない。工程塔の特徴の取り出しと時間ヘッドは、その組の一枚で backbone の完走の後に回す）
2. 各 run の終わりに prereg §5 の量を `records.csv` に足す。発散・非数は起きた歩とともに記録し、その点を終える（値を補わない）
3. 発散・非数が一つの塔で 5 件以上になった時点、または 0 番が発散していた時点で停止して諮る（prereg §6）
4. GPU の記録: 全期間、五枚の使用量と compute プロセスを一定間隔で採る。本契約のプロセス（`/proc/PID/exe` で絞る）が GPU0 に一度も現れないこと

### Task E — 表と順位

1. `results_ptower.csv`・`results_dtower.csv`（20 行。点の番号、3 値、主指標、co-primary、発散、上限到達、checkpoint の epoch、run の経路）
2. prereg §3.1 の規則で上位 3 件と 1 位を塔ごとに出し、`top3.md` に書く。0 番が上位 3 件に入るかを書く。0 番との差（記録だけ）
3. 工程塔は 10 の時間ヘッドの値をすべて残す（最大だけでなく）
4. 予測（prereg §3.3）の当たり外れ。§8 の異常の有無の表

### Task F — 検証と報告

1. 収穫（`make runindex`。禁止領域の規則どおり `allow_write` に `runindex/` を宣言してある）。本契約の全 run（工程塔は backbone 20・特徴 20・時間ヘッド 200、検出塔 20）が `task_id` で現れること。検出塔の run が収穫の対象になる形（`metrics.json` ほか `must_have`）であること
2. 追跡される変更の一覧（集合差）。`make forbidden-check`。試験。`experiments/` と `data/processed/` に足したファイルの最大の大きさ
3. `RESULT.md`、`result.yaml`（版 3）、`audit.md`、`tasks/inbox.d/` の行
4. PR（base は phase0、Draft でない。分岐は `feat/` で始まる）。台帳への送り返し（手順書「8. 終える」）

## 7. 禁止

実行者の操作に対する禁止である（同期処理による配布は含まない）。

1. GPU0 を使わない。他の利用者のプロセスに触れない
2. test を評価しない。選定（処方の確定）を行わない。点を足さない、点の値を変えない（prereg §2.1）
3. 探索の値と順位を、ほかのホストの値と順位に並べて読まない。異常の検知にほかのホストの値を使わない
4. 一枚の道（工程塔）と既存の検出塔の設定・起動の既定の振る舞いを変えない。候補 0b の二枚の道の実装（`stage1_ptower_r3_dist.py`）を変えない
5. `data/raw`・`data/external` に書かない。画像を複製しない。`data/splits/` と折りの集合を変えない
6. checkpoint・work・特徴を同期の対象の経路（`experiments/`、`data/processed/`）に置かない
7. 規約（`context/conventions.md`）、`docs/issuer-defects.md`、`docs/proposals/` のカードと依頼文、既存の `tasks/*/` に触れない
8. 生成物（`context/auto/*`、`tasks/inbox.md`）の再生成と `*-check` を回さない。`runindex/` を手で編集しない
9. 外部への送信は `make task-report` 以外の経路で行わない（W&B はオフラインにする）
10. 候補 0b の記録以外を repo の外から消さない。本契約の repo の外の出力は消さない

## 8. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | prereg の先行 | commit の時刻が最初の学習の開始より前。L3 で P4・P13・P14 が PASS | 対称性の表の一行を UNKNOWN にした写しで P13 が FAIL。カードの経路を存在しない名前にした写しで P14 が FAIL |
| b | 開始状態と環境 | 分岐・起点・作業ツリー・GPU の使用量と所有者・版・試験の前の値・`env_dlsta.json` | 自分の python を GPU1 に起こして所有者の数え方が 1 を返し、存在しない PID で 0 |
| c | 0b の記録の削除 | 消す前の大きさと、消した後の不在 | 消す前に同じ命令が「在る」と出る。隣のディレクトリ（可否確認の記録）は残っている |
| d | 入力・道具・空き | 要約値が記録と一致。空きが見込みの 2 倍以上 | 期待の件数を 1 つ変えた写しで不一致。無い経路で 0 件 |
| e | manifest | 総数が規約の 17,233、折り A の train と val の数、余りが 1 でない、旧い manifest は不変。重なる 15,437 枚が同一 | 画像を 1 枚欠いた写しで総数が 1 減る。1 枚を 1 バイト変えた写しで不一致が 1 |
| f | 検出塔の口 | 点の値が群に届く（本体 2 群が点の値、4 群が 0.1 倍。norm と bias の weight decay が 0）。既定の設定は不変（要約値）。third_party の変更が snapshot に在る | 値を変えた写しで記録の群の値が変わる。snapshot の patch を当て直して要約値が一致 |
| g | 40 本と刻印 | 完走または発散の記録 40 件。`config.yaml` に task_id・点の番号・3 値。工程塔は各点で特徴 1・時間ヘッド 10 | 点の番号を 1 つ変えた写しの config で照合が不一致。時間ヘッドの数が 10 でない点が 0 |
| h | 記録する量 | prereg §5 の 11 項目が各 run に在る。測れなかった量は UNKNOWN と理由 | `records.csv` の空欄の数と UNKNOWN の数が一致 |
| i | 表と順位 | 20 行 × 2 塔。上位 3 件と 1 位が prereg §3.1 の規則だけで決まる。選定なし | 値を一つ入れ替えた写しで順位が変わる。同点の写しで番号の小さい方が上 |
| j | GPU0 の不使用と test の不使用 | GPU の記録に本契約のプロセスが GPU0 に 0 件。評価の記録に test の集合が 0 件 | 同じ数え方で GPU1 には本契約のプロセスが 1 件以上。val の評価の記録は 40 件以上 |
| k | 置き場 | checkpoint・work・特徴が repo の外。`experiments/` と `data/processed/` に足した最大のファイルの大きさ | 足したファイルの一覧を大きさで並べた先頭。checkpoint の経路の `df` の装置が repo の外 |
| l | 対称性と異常 | prereg の表 2 個に UNKNOWN 0。§8 の異常の有無の表 | P13 の PASS の件数（表 2 個、行 34） |
| m | 収穫と検査 | runindex に本契約の全 run。試験の失敗の名前の集合が同じ。forbidden-check pass | task_id で照合して 260 件。`data/` に 1 件足した写し（repo の外の clone）で forbidden-check が fail |
| n | PR | 番号、base phase0、分岐 feat/、Draft でない | `gh pr view` の実測（number・baseRefName・headRefName・isDraft） |

## 9. 報告の構成

`RESULT.md` は 150 行以内。節は 判定（verdict と G1〜G4）／完了判定（表。実測値つき）／実測（次の契約で使う値: 塔ごとの上位 3 件と 1 位と 0 番の順位、点ごとの値の表の経路、一本の壁時計と記憶量、環境、二枚の道の一歩の時間、manifest の数）／起票者の誤り（一件 3 行以内）／逸脱／想定外・UNKNOWN／送出（PR 番号と終了コードだけ）。命令と出力の全文、参照の解決の全文、対照の出力、GPU の記録の要約、変更範囲の一覧、台帳の応答は `audit.md` へ。`RESULT.md` から `audit.md` を行番号で指す。

## 10. 次の契約と申し送り

- 回し直しの契約（andrew。exp）は本契約の `top3.md` を引き、上位 3 件と 0 番（上位 3 件に無ければ）を 5 折り × 2 種で回す。prereg §3.2 をそのまま引く。検出塔の点ごとの値を渡す口と third_party の snapshot を andrew に当てる
- 本契約の repo の外の出力（約 75 GB の見込み）は残す。消すかは利用者が決める
- 費用（壁時計、GPU 時間）は記録であり、判断に使わない

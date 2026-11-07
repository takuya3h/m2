# 検出塔の回し直し — 探索の 1 位（12 番）と batch 6 で 5 折り × 2 種を学び、seed 42 の塔を凍結する（andrew）

**task_id:** T-2026-11-07-dtower-rerun  **kind:** exp  **ホスト:** andrew  **PR の base:** phase0  **分岐:** feat/dtower-rerun

## 0. この契約の位置づけ

- 提案カード `docs/proposals/2026-10-21-tower-reselect-search.md`（五版、PR 294、統合済み）の §7「回し直し」の 2 を実行する。カードは利用者の判定を通っている（F 2026-10-22、F 2026-11-06）
- 探索（T-2026-10-22-tower-reselect-search-dlsta、dlsta）で検出塔の 1 位は 12 番。batch の探索（T-2026-11-06-dtower-batch-search、andrew、PR 299、統合済み）で GPU ごとの batch は **6** に決まった
- 本契約: 12 番の設定と batch 6 で 5 折り × seed 42・123 の 10 本を学び、**seed 42 の塔を折りごとに凍結して Stage 2 以降の検出塔にする**。0 番（現行の処方）も同じ batch と縮みの量 S の換算で 10 本学び、記録だけ。**選定は行わない**。採用は性能で決めない（F 2026-10-17）
- 事前登録は `prereg.md`。学習の前に commit する
- カード §7 の 1 に書かれた同点幅 0.0106 は、batch の探索で 0.0076 に改訂された（PR 299 の `meta.amendments`。起票者の誤り）。本契約は 0.0076 を使う。カードの文の訂正は別に行う
- 凍結した塔の登録（`scripts/stage2pilot/common.py` の要約値の差し替え、Stage 2 の材料の作り直し）は本契約で行わない

## 1. 背景（有効な値。出所つき）

| 項目 | 値 | 出所 |
|---|---|---|
| 探索の 12 番（dlsta、折り A、seed 42、batch 2） | val mAP 0.7374、標的群 0.8286、checkpoint epoch 16 | `experiments/analysis/tower_reselect_search_dlsta/results_dtower.csv` rank 1 |
| 探索の 0 番（同） | val mAP 0.7189、標的群 0.7928、epoch 21 | 同 point 0 |
| batch の探索の b6（andrew、12 番、折り A） | val mAP 0.7385（seed 42）・0.7328（seed 123）、平均 0.73565、標的群の平均 0.8211。総 epoch 15・18。学習の壁時計 3.6・4.3 時間。最大確保 38.0〜38.7 GB/rank | PR 299 の RESULT |
| 二周目の 0 番の塔（batch 2、val で選んだ epoch） | 折り A 0.7273（seed 42）、折り B 0.4557、C 0.41、D 0.48、E 0.51（seed 42） | `experiments/baselines/stage1_dtower_r2/dcoco_fold*_seed42/metrics.json`、runindex の `baselines/dcoco_fold*` |
| 同点幅 | 0.0076（`baselines/dcoco_foldA/dcoco_foldA@val` の mAP_sstd 0.0037965 の 2 倍） | PR 299 の prereg §3 |

dlsta の値と andrew の値は並べない（ホストが違う。F 2026-10-21）。折り B〜E の val mAP は折り A より大きく低い（val の動画が違う）。

## 2. 確定した事実（出所つき）

| 項目 | 値 | 出所 |
|---|---|---|
| 12 番の設定 | 学習率 3.07e-4（backbone と線形射影 0.1 倍）、S 4.976e-3、max_norm 0.059 | results_dtower.csv、PR 299 の prereg §1 |
| 0 番の設定 | 学習率 1e-4、weight decay 1e-4（batch 2）、max_norm 0.1 | results_dtower.csv の point 0、二周目の処方 |
| batch 6 での weight decay | 12 番 1.01058e-3、0 番 2.998753e-4（折り A の 1 epoch 802 歩で換算。他の折りは歩数を実測して換算） | PR 299 の実測（audit:186-189）、prereg §2.1 |
| 道具 | `scripts/run_tower_search.py`、`scripts/train_relation_detr_search.py`、`configs/detector_relation_detr/train_search.py`、`scripts/eval_relation_detr_map.py` | 探索と batch の探索 |
| 道具の罠 1 | `train_search.py` は `batch_size = 2` と `num_workers = 4` を固定し、口が無い。batch の探索はこの 2 行だけを環境変数にした写しを repo の外に置いた | PR 299 の audit B-1 |
| 道具の罠 2 | `train_relation_detr_search.py` は epoch 0 で optimizer の群を `load_point` の値（dlsta の `points.csv`）と 1e-15 で照合し、違えば止まる。batch 6 の weight decay は points.csv と違うので、12 番も 0 番も止まる。batch の探索は包み `tools/train_level.py`（repo の外）で `load_point` だけを JSON を読む関数に差し替えた。照合はそのまま働く | 同 |
| 観測器 | `TOWER_SEARCH_OBSERVER` で読ませる `observer.py`（repo の外）が、batch・枚数・立ち上げ・評価の組ごとの AP・読んだ動画を記録した | 同 |
| 2 枚の道 | accelerate、2 プロセス、`NCCL_P2P_DISABLE=1`（andrew で要る） | env-facts、PR 299 |
| COCO の重みの罠 | 既定の経路がファイルでなければ `main.py` は読み込みを飛ばして学習が進む。評価の道具は `third_party/Relation-DETR` へ chdir するので checkpoint は絶対経路 | env-facts の dlsta の項 |
| 折りの注釈 | 二周目が 5 折りの塔を作っている（`stage1_dtower_r2/dcoco_fold{A..E}_seed42`）。各折りの注釈の置き場と要約値は、その run の `config.yaml` と `command.sh` から読んで実測する | 二周目の記録 |
| andrew の装置 | A6000 × 2、電力の上限 300 W。batch 6 で 38.0〜38.7 GB/rank | PR 299 |
| 所要の見込み | batch 6 で 1 本 3.6〜4.3 時間（折り A）。20 本で約 72〜86 時間 ＋ 評価。折りで枚数が違うので幅がある | PR 299 |

**ホスト固有の値は実測で決める。** 包みと写しの置き場は batch の探索の `$STORE` を読み、在れば中身の要約値を記録して使ってよい。無ければ同じ作法で作る。

## 3. 定義

### 3.1 run の表

| 点 | 折り | seed | 本数 |
|---|---|---|---|
| 12 番 | A・B・C・D・E | 42・123 | 10 |
| 0 番 | A・B・C・D・E | 42・123 | 10 |

- 計 20 本。2 枚を占有して 1 本ずつ順に（prereg §2.1 の順）。1 枚ずつ 2 本並行の道は「2 枚の道」の固定を変えるので使わない
- run の置き場は `experiments/baselines/stage1_dtower_rerun/` の下に、点・折り・seed が名前から読める形。checkpoint は同期の対象の経路の外（`$STORE/runs/`）に置き、経路と sha256 を記録する
- 凍結する塔は 12 番 seed 42 の 5 本。checkpoint の sha256・epoch・val の値を `experiments/analysis/dtower_rerun/frozen_towers.json` に書く

### 3.2 処方

prereg §2 のとおり。12 番と 0 番で違うのは学習率・weight decay（S）・max_norm だけ。batch 6、収束規則、立ち上げ、精度、増強、初期化は同じ。weight decay は折りごとに 1 epoch の歩数を実測して換算する。

### 3.3 test の扱い

prereg §2.4 のとおり。各 run で学習の後に一度だけ test を評価し、副次として記録する。val に一度も入らない 5 動画（01・03・11・13・14）の集計を点ごと・seed ごとに出す。判定・選定に使わない。

## 4. Task

**コマンドは書かない。実装と記録を読んで決めてよい。** 命令と出力は `audit.md` に残す。

### Task A — prereg の commit と開始状態（G1）

1. `prereg.md` を学習の前に commit し、`spec.yaml` の `prereg.commit` と `committed_at` を実測で埋める
2. 分岐が `feat/` で始まり起点が `origin/phase0`。起点に PR 299 の内容（batch の探索の run と報告）と PR 294 の内容（カード五版）が在ることを記録する。カードが五版であることを本文の版の行で確かめる（四版の写しで検査が落ちることを対照に）
3. andrew の compute プロセスを `/proc/PID/exe` の解決と引数の要素の完全一致で列挙する。本契約以外が在れば止めずに停止し、利用者に諮る
4. 開始前から在る未追跡を消さない・動かさない。一覧を記録する。他の契約の同期で届いたファイルが禁止領域に在れば、四本目（PR 297）の前例（`.git/info/exclude`）で扱う
5. 5 折りの注釈（train・val・test）の実在と要約値、各折りの動画の集合が `conventions#folds` の表と一致すること、画像、COCO 1x の checkpoint の sha256、記憶領域の空き（見込み: 20 本の checkpoint と記録。batch の探索の 6 本の実測から見積もる）
6. 試験の失敗の名前の集合、既存の仮想環境の一覧の要約値、電力の上限と装置の型、環境の表（prereg §7）
7. 禁止の場所（§6 の 2・3・4）の開始時の要約値を取る
8. `contract.conventions_rev` と `meta.created_from` を実測し、食い違えば差し替えて `meta.amendments` に記録する

### Task B — 口と対照（G2）

1. batch と worker 数、学習率・weight decay・max_norm、点の照合の口を、batch の探索の前例（§2 の罠 1・2）で用意する。既存スクリプトと設定の既定の挙動を変えない。前例の包みと写しが `$STORE` に在れば要約値を記録して使う
2. 対照（数歩の試走。腕に数えない）: 12 番と 0 番の設定が optimizer の群と DataLoader に届く（値を変えた写しで照合が止まる。batch を変えた写しで枚数の検査が止まる）。既定の挙動の不変（包みを使わず起こした数歩が前と同じ）
3. 折り B〜E の注釈で DataLoader が train と val の動画の集合どおりに読むことを、読んだ動画の集合で確かめる（規約の表と一致。test の動画を混ぜた写しで外れる）
4. COCO の重みを読んだことを、読み込みの記録と読む前後のパラメータの要約値の違いで示す。経路を存在しない経路にした対照で記録が消えることを確かめる
5. 各折りの 1 epoch の歩数を DataLoader の長さから実測し、weight decay を換算して prereg §2.1 の規則と照合する。折り A は 1.01058e-3・2.998753e-4 と一致すること

### Task C — 20 本の学習と評価（G3）

1. prereg §2.1 の順で 20 本を回す。各 run に prereg §5 の量を記録する
2. 各 run の学習の後、checkpoint でその折りの val と test を評価する。test は一度だけ。評価の時刻と回数を記録する
3. 発散・非数・溢れが出たら停止して諮る。batch を落として続けない
4. 12 番 seed 42 の 5 本が揃った時点で、`experiments/analysis/dtower_rerun/INTERIM.md` に 5 本の val の値と checkpoint の sha256 を書いて push してよい（利用者が Stage 2 の準備を始められる）

### Task D — 表・記録・報告

1. prereg §3 の表と記録。副次の test の集計（prereg §2.4）。凍結する塔の一覧（`frozen_towers.json`）
2. 完了判定（§7）を実測で埋める。禁止の場所の要約値を Task A-7 と比べる。`make runindex`、`make forbidden-check`（本 task_id つき）、L1 と L2、試験、仮想環境の要約値を Task A-6 と比べる
3. runindex の検証 C5 が別の契約の run（`phase1__grasppilot2_G_*`）で落ちることが分かっている（PR 299 の報告）。本契約の run に 0 件であることを示し、他の契約の記録は直さない
4. `README.md` と `docs/experiment_log.md` に書く。`REPORT.md`、`RESULT.md`、`result.yaml`、`audit.md`、`tasks/inbox.d/T-2026-11-07-dtower-rerun.md`
5. commit、push、PR と `make task-report`。抑止の解除は手順書の「8. 終える」に任せる

## 5. 事前登録

`prereg.md` のとおり。予測は §3.1、記録の規則は §3、対称性の表は §4、停止条件は §6。

## 6. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。** `contract.inject_verbatim` の `conventions#prohibitions` を原文のまま適用し、加えて次を守る。

1. test の動画は各 run で学習の後に一度だけ評価する。学習・checkpoint の選択・停止の判断に test を使わない。副次の値を判定・選定に使わない
2. 前回までの契約の run の置き場・集計・`tasks/` のフォルダ・版管理の外の保存先に書き込まない。読むことだけを行う
3. 凍結源、既存の checkpoint、COCO の重み、`data/raw`、`data/external`、注釈を変えない
4. `third_party/`、既存の仮想環境、`scripts/`・`configs/` の既存ファイルを変えない。口は repo の外の写しと包みで用意する（batch の探索の前例）
5. `context/auto/*` と `tasks/inbox.md` を再生成しない。生成物を作り直す検査を回さない。`forbidden-check` と `make runindex` は回す
6. **装置の他のプロセスを止めない。** 他の使用が在れば停止して諮る
7. andrew だけを使う。bengio、efros、ilya、dlsta に接続しない。GPU は andrew の 2 枚
8. 開始前から在る未追跡と、同期で届く他の契約のファイルを消さない・動かさない
9. 外部への送信は `make task-report` 以外の経路で行わない。W&B は offline にする
10. 抑止の目印を手で置かない・手で外さない
11. run の表に無い run を足さない。水準（点・batch・seed・折り）を後から変えない。発散・溢れで batch を落とさない
12. 他の契約の runindex の記録を直さない

## 7. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | prereg の先行 | commit の時刻が最初の学習の開始の前。P4・P13・P14 PASS | UNKNOWN を含む写しで P13 FAIL。存在しないカードで P14 FAIL |
| b | 開始状態と環境 | 分岐・起点・PR 294 と 299 の内容・未追跡・GPU・試験の前の値・カードの版・環境の表・電力の上限 | 列挙の対照（自分のシェル 1 以上、存在しない経路 0）。四版の写しで版の検査が落ちる |
| c | 入力と道具 | 5 折りの注釈の要約値、動画の集合が規約の表と一致、COCO の sha256、空きが見込みの 2 倍以上 | 1 バイト変えた写しで不一致。test の動画を混ぜた集合で外れ |
| d | 設定の到達 | 20 本の群の値と batch が水準どおり。既定の挙動は不変 | 値を変えた写しで照合が止まる。batch を変えた写しで枚数の検査が止まる |
| e | 20 本の run | 完走または発散の記録。config.yaml に task_id・点・折り・batch・seed・設定 | 存在しない名前（点 5 や折り F）で 0 件 |
| f | 記録する量 | prereg §5 の 9 項目を各 run で | 測れなかった量は UNKNOWN と理由 |
| g | 表 | 点ごと・折りごとの val、10 本の平均と差、seed 間 SD、折り A と b6 の差。選定の記述が無い | 表の値を metrics.json から計算し直して全桁で一致 |
| h | test の副次 | 各 run で一度、5 動画の集計、判定に使っていない | 評価の記録の時刻が run ごとに 1 件。集計を 6 動画にした写しで値が変わる |
| i | 対称性 | prereg の表に UNKNOWN 0 件。P13 PASS | UNKNOWN を 1 件入れた写しで FAIL |
| j | 凍結する塔 | 5 本の経路・sha256・epoch・val。同期の外に在る | 1 バイト変えた写しで sha256 不一致。同期の対象の経路の一覧に checkpoint が 0 件 |
| k | 収穫と無変更 | runindex に 20 本、試験の失敗の名前が同じ、forbidden-check の本契約の経路の違反 0、禁止の場所の要約値が開始時と一致 | 同じ道具が本契約の新しいファイルを変更として拾う |
| l | PR | 番号、base phase0、Draft でない | 分岐名 `feat/dtower-rerun` |

## 8. 停止して諮る条件

prereg §6 のとおり。加えて: PR 294 か 299 の内容が起点に無い、カードが五版でない、andrew に他の使用がある、記憶領域が足りない、実行基盤が書き込み・移動・削除・外部の取得を拒む（回避せず、利用者に提示して許諾を得る）。

停止のときも、それまでの実測を `RESULT.md` と `audit.md` に書き、PR と `make task-report` まで行う。

## 9. 報告の構成

**`RESULT.md` は起票者が判断に使う事実だけ。150 行以内。** 命令と出力は `audit.md` に置き、`RESULT.md` から行番号で指す。

| 節 | 内容 |
|---|---|
| 判定 | status と G1〜G3 の結果 |
| 完了判定 | §7 の表に実測値 |
| 実測 | 点ごと・折りごとの val の表、10 本の平均と差、seed 間 SD、折り A と b6 の差、test の副次、凍結する塔の一覧、所要、記憶量、予測の当たり外れ |
| 起票者の誤り | 型と内容。一件 3 行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、`make task-report` の終了コード |

`REPORT.md`（`experiments/analysis/dtower_rerun/`）には、全値、epoch ごとの値、クラス別、動画ごと、二周目の 0 番の塔との参考の表（処置の差として読まない）、prereg §3 の読みの規則による記述、§3.1 の予測との照合、限界（折りで値が大きく違うこと、val と test の重なり、ホスト）を置く。

## 10. 送出

- PR の base は **phase0**。push は統合ではない。PR が Draft でなく存在する状態で終える
- `make task-report` で台帳へ返す

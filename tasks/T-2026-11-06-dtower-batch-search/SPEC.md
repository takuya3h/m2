# 検出塔の batch の探索（andrew）— 12 番の設定で GPU ごとの batch 2・4・6 を折り A × 2 種で学び、batch を一つに決める

**task_id:** T-2026-11-06-dtower-batch-search  **kind:** exp  **ホスト:** andrew  **PR の base:** phase0  **分岐:** feat/dtower-batch-search

## 0. この契約の位置づけ

- 両塔の学び直し（カード `docs/proposals/2026-10-21-tower-reselect-search.md`、**五版**）の、回し直しの前段。五版の V3: 検出塔の GPU ごとの batch を、回し直しの前に探索して一つに決める
- 規則は `prereg.md` に全段ある。**結果を見てから規則を足さない。** prereg の commit が学習の前であること（P4）
- 本契約が返すもの: 3 水準 × 2 seed の val mAP と標的群 AP の表、2 本の平均、規則で決めた batch、記録する量。**選んだ batch は回し直しの契約（検出塔 1 件 ＋ 0 番、5 折り × 2 種）で使う**
- 利用者の決定（2026-11-06）: 回し直しは上位 1 件だけ、0 番は回す、seed 2 種は残す、カードの問い #1 は置かない、縮みの量 S を揃える、精度への影響を測る batch の探索を先に行う
- 前の契約の実測: andrew の A6000 で batch 2・4・6 は収まり 8 は溢れる。1 epoch は 942・802・784 秒（PR 290）。GPU は計算が律速で、読み込み・worker・プロセス数では縮まない（PR 292）

## 1. 確定した事実（出所つき）

| 事実 | 出所 |
|---|---|
| 探索の 1 位は 12 番（学習率 3.07e-4、weight decay 3.37e-4、max_norm 0.059、val mAP 0.7374、標的群 AP 0.8286、checkpoint の epoch 16） | `experiments/analysis/tower_reselect_search_dlsta/results_dtower.csv` rank 1、`top3.md` |
| 12 番の S は 4.976e-3（学習率 3.07e-4 × weight decay 3.37e-4 × 20 epoch 相当の歩数 48,100。2026-11-06 の改訂。起票時は丸めた 5.0e-3） | カード §14 の表と S の定義 |
| 検出塔の学習設定の口 | `scripts/train_relation_detr_search.py` が点ごとの学習率・weight decay・max_norm を受ける（探索の契約の完了判定 f）。`batch_size`（GPU ごと）と `num_workers` は `configs/detector_relation_detr/train_search.py` の定数で口が無い。PR 290・292 は設定の写しを repo の外に置き、`batch_size` を環境変数で渡した | 探索の RESULT、PR 290 の RESULT の起票者の誤り、PR 292 の逸脱 |
| 起動の形 | `accelerate launch --multi_gpu --num_processes 2 scripts/train_relation_detr_search.py …`、`EGO_ROOT`・`RELDETR_COCO_CKPT`・`RELDETR_OUTPUT_DIR`、`NCCL_P2P_DISABLE=1`。`--seed`、`--mixed-precision fp16`、`--convergence-schedule`、`--max-epochs 36` | `scripts/run_tower_search.py` の検出塔の段、PR 290 の REPORT §1 |
| 立ち上げ | 第 0 epoch に最大 1,000 歩の線形の立ち上げ（上流の既定） | カード §14 の固定の表 |
| 1 epoch の歩数（andrew、2 枚） | batch 2: 2,405、4: 1,202、6: 802 | PR 290 の RESULT |
| 記憶（andrew、rank 0 の torch の最大確保） | batch 2: 12.3 GB、4: 23.9 GB、6: 34.6 GB。8 は rank 1 が歩 38 で溢れた | PR 290 の RESULT |
| D\*-COCO の折り A の seed 間 | runindex の `baselines/dcoco_foldA/dcoco_foldA@val`（一周目と二周目の 6 本、seed 42・123・456）の mAP_sstd 0.0038（0.0037965）。二周目の 3 本だけでは標本 SD 0.0053（2026-11-06 の改訂で前者を同点幅の出所とした） | runindex の `baselines/dcoco_foldA/dcoco_foldA@val` の mAP_sstd、`tasks/T-2026-09-19-stage1-detector-towers-r2/RESULT.md` |
| 二周目の折り A の壁時計（efros、A6000 × 2） | 9.97〜11.96 時間（15〜18 epoch、各 epoch の評価を含む） | `experiments/baselines/stage1_dtower_r2/results_table.md` |
| COCO の重み | `data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth`。読んだ記録は学習ログの `load pretrained from` と `initialization_rank*.json`（matched 596 テンソル） | PR 290 の RESULT 完了判定 b |
| 折り A の注釈 | `data/annotations/egosurgery_tool_folds/A/` | 探索の SPEC §3 |
| 凍結源の照合（P5） | exp の契約では規約の凍結源（`third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`）の要約値を照合する。本契約は凍結源を使わないが検査は省けない。andrew にこのファイルが在る（Stage 2 の契約で照合済み） | `tools/preflight_task.py` の P5、規約 frozen_source |

## 2. 定義

`prereg.md` §2 のとおり。要点:

- 水準は GPU ごとの batch 2・4・6（実効 4・8・12）。12 番の学習率・max_norm・S（4.976e-3）は同じ。weight decay は b2 を 12 番の 3.37e-4 のまま置き、b4・b6 は 1 epoch の歩数の比で換算（prereg §2.1 の表。実行者は実際の 1 epoch の歩数から換算し直して照合）
- seed 42 と 123。各水準 2 本、計 6 本。2 枚を占有して 1 本ずつ順に回す
- 固定は探索と同じ（prereg §2.2）
- 主指標は val mAP の 2 本の平均。規則は prereg §3。同点幅 0.0076（2026-11-06 の改訂）、同点なら大きい batch

## 3. Task

**コマンドは書かない。実装と記録を読んで決めてよい。** 命令と出力は `audit.md` に残す。

### Task A — prereg の commit と開始状態（G1）

1. `prereg.md` を学習の前に commit し、`spec.yaml` の `prereg.commit` と `committed_at` を実測で埋める
2. 分岐が `feat/` で始まり、起点が `origin/phase0` で、起点に PR 290・292 の内容が在ることを記録する
3. **カードが五版であること**を `docs/proposals/2026-10-21-tower-reselect-search.md` の冒頭の「版:」の行で確かめる。四版のままなら停止して諮る（五版は利用者が手で置く。F 2026-10-23 の運用）
4. 開始前から在る未追跡を消さない。一覧を記録する
5. andrew の compute プロセスを `/proc/PID/exe` の解決と引数の要素の完全一致で列挙する。本契約以外が一件でもあれば止めずに停止し、利用者に諮る
6. 入力（折り A の注釈、画像、COCO の checkpoint）と道具の実在と sha256 を記録と照合する。記憶領域の空きをバイトで記録し、見込み（6 本 × 二周目の run の大きさ）の 2 倍以上であることを確かめる
7. 環境（prereg §7）、試験の失敗の名前の集合、既存の `.venv` と `.venv-relation-detr` の一覧の要約値、GPU ごとの電力の上限・装置の型・driver を記録する
8. `contract.conventions_rev` と `meta.created_from` を実測し、食い違えば差し替えて `meta.amendments` に記録する

### Task B — 口と対照（G2）

1. batch・weight decay・学習率・max_norm を水準ごとに渡す。口が無い項目（`batch_size`、`num_workers`）は PR 290・292 と同じく設定の写しを repo の外に置くか、既定の挙動を変えずに引数を足す。どちらにしたかを記録する
2. 対照: 数歩の写しで、optimizer の各群の学習率と weight decay（本体の 2 群が水準の値、backbone と線形射影の 4 群が 0.1 倍、norm と bias は weight decay 0）と、DataLoader の batch を記録に出す。陽性対照として batch と weight decay を別の値にした写しで記録が変わること
3. 立ち上げの歩数の記録の口を確かめる（第 0 epoch の歩数が 1,000 未満の水準で、立ち上げが何歩で終わるか）。実装を読んで記録の方法を決める
4. 3 水準の weight decay の換算値を、実際の 1 epoch の歩数（DataLoader の長さ）から計算し直し、prereg §2.1 の表と照合する。食い違えば実測の値を使い、`meta.amendments` に記録する

### Task C — 学習（G3）

1. 6 本を prereg §2.1 の順（b2 の 42・123、b4 の 42・123、b6 の 42・123）で回す。各 run の config.yaml に task_id・batch・seed・設定の値を刻む
2. 各 run で COCO の重みを読んだ行（matched のテンソル数）を確かめる。無ければ停止
3. 発散・非数が出たら停止して諮る。b6 が溢れたら記録して外し、残りを続ける
4. prereg §5 の量を各 run で記録する。checkpoint（val mAP が最良の epoch）は同期の対象の経路の外に置く

### Task D — 評価・表・報告

1. 水準ごとの 2 本の val mAP・標的群 AP・陰性対照群 AP、2 本の平均と差、規則（prereg §3）による選択、co-primary の食い違いの有無を表にする。train mAP との差も表にする
2. 選んだ batch と、その根拠（平均の差と同点幅）を `experiments/analysis/dtower_batch_search/REPORT.md` と `RESULT.md` に書く。採否の推奨や処方の効果としての読みを書かない
3. 完了判定（§5）を実測で埋める。`make forbidden-check`（本 task_id つき）、L1 と L2、試験、仮想環境の一覧の要約値を Task A-7 と比べる。runindex の収穫
4. `README.md` と `docs/experiment_log.md` に書く
5. `REPORT.md`、`RESULT.md`、`result.yaml`、`audit.md`、`tasks/inbox.d/T-2026-11-06-dtower-batch-search.md`
6. commit、push、PR と `make task-report`。抑止の解除は手順書の「8. 終える」に任せる

## 4. 読み方の規則（記述だけ。prereg §3.2）

1. 値は折り A の 2 本の平均で、3 水準の最大を取るので上振れする。処方の効果として読まない
2. b2 の値を dlsta の探索の 12 番の値（0.7374）と並べて効果として読まない（ホストが違う）。記録だけ
3. 採否・推奨を書かない。選択は規則で決まる

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | prereg の先行 | commit の時刻が最初の学習の開始より前。L3 で P4・P13・P14 が PASS | 対称性の表の一行を UNKNOWN にした写しで P13 が FAIL。カードの経路を存在しない名前にした写しで P14 が FAIL |
| b | 開始状態と環境 | 分岐、起点、PR 290・292、作業ツリー、GPU、版、試験の前の値、カードの版、環境の表、電力の上限 | プロセスの列挙が自分のシェルを 1 件として拾い、存在しない実行ファイルの経路で 0 件になる。カードの版の行を「四版」に書き換えた写しで検査が FAIL |
| c | 入力と道具 | 実在と sha256 の一致、空きが見込みの 2 倍以上 | 1 バイト変えた写しで照合が不一致 |
| d | 設定の到達 | 群ごとの実際の値と DataLoader の batch が各 run の記録に在る。既定の挙動が不変 | batch と weight decay を別の値にした写しで記録が変わる。既存の設定で起こした数歩の記録が探索の値（batch 2、1e-4）のまま |
| e | 6 本の run | 完走または発散の記録。config.yaml の刻印 | 存在しない run の名前で 0 件になる |
| f | 記録する量 | prereg §5 の 8 項目。UNKNOWN は理由つき | 立ち上げの歩数が b2 で 1,000、b6 で 802 以下になる（第 0 epoch の歩数で頭打ち）か、または 1,000 のまま第 1 epoch に跨ぐか、どちらかが記録から読める |
| g | 表と選択 | 2 本の値と平均、差、規則による選択、co-primary の食い違い | 平均と差を各 run の metrics.json から計算し直すと一致する。同点幅を 0 にした写しで選択が「最大の平均」に変わる（同点が在った場合） |
| h | 対称性 | prereg の表に UNKNOWN 0 件 | P13 の PASS の件数（表 1 個、行 24） |
| i | test 不使用と置き場 | 評価の記録の集合に test が無い。checkpoint が同期の経路の外 | 評価の記録に test の名前を足した写しで検査が外れを出す |
| j | 収穫と無変更 | runindex に 6 本が task_id で現れる。試験の失敗の名前の集合が増えない。forbidden-check が通る。禁止の場所・仮想環境・third_party の要約値が前後で一致 | 同じ道具が本契約の新しいファイルを変更として検出する |
| k | PR | 番号、base phase0、Draft でない | 分岐名が `feat/dtower-batch-search` |

## 6. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。** `contract.inject_verbatim` の `conventions#prohibitions` を原文のまま適用し、加えて次を守る。

1. **test の動画（04、05、07）を評価しない。** 学習は折り A の train、val は 09・10
2. 水準・seed・規則を prereg から変えない。規則を結果を見てから足さない
3. 既存の run の置き場・checkpoint・凍結源・`data/raw`・`data/external`・注釈を変えない
4. `third_party/` と既存の仮想環境を変えない。既存スクリプトと設定の既定の挙動を変えない（口が無ければ写しを repo の外に置く）
5. 本契約の版管理の外の生成物（checkpoint、accelerate の状態、設定の写し）は `/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-dtower-batch-search/` に置く。run の記録（metrics.json、config.yaml、notes.md）は `experiments/baselines/stage1_dtower_batch/` に置く
6. `context/auto/*` と `tasks/inbox.md` を再生成しない。生成物を作り直す検査を回さない。`forbidden-check` は回す
7. **装置の他のプロセスを止めない。** 他の compute プロセスが在れば停止して諮る
8. andrew だけを使う。bengio、efros、ilya、dlsta に接続しない。GPU は andrew の 2 枚
9. 開始前から在る未追跡と、同期で届く他の契約のファイルを消さない・動かさない
10. 外部への送信は `make task-report` 以外の経路で行わない。W&B は offline にする
11. 抑止の目印を手で置かない・手で外さない
12. 1 枚ずつ 2 本を並行して回さない（2 枚の道を固定する）

## 7. 停止して諮る条件

prereg §6 のとおり。加えて: カードが四版のまま（Task A-3）、andrew に本契約以外の compute プロセスがある（Task A-5）、口が既定の挙動か `third_party/` を変えないと作れない、実行基盤が書き込み・移動・削除・外部の取得を拒む（回避せず、利用者に提示して許諾を得る）。

停止のときも、それまでの実測を `RESULT.md` と `audit.md` に書き、PR と `make task-report` まで行う。

## 8. 報告の構成

**`RESULT.md` は起票者が判断に使う事実だけ。120 行以内。** 命令と出力は `audit.md` に置き、`RESULT.md` から行番号で指す。

| 節 | 内容 |
|---|---|
| 判定 | status と G1〜G3 の結果 |
| 完了判定 | §5 の表に実測値 |
| 実測 | 6 本の値の表、2 本の平均と差、規則による選択（batch の値）、weight decay の換算値、立ち上げの歩数、所要と記憶、環境の表 |
| 起票者の誤り | 型と内容。一件 3 行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、`make task-report` の終了コード |

`REPORT.md`（`experiments/analysis/dtower_batch_search/`）には全値、epoch ごとの val の値、記録する量の表、§4 の規則による記述、prereg §3.1 の予測との照合を置く。

## 9. 送出

- PR の base は **phase0**。push は統合ではない。PR が Draft でなく存在する状態で終える
- `make task-report` で台帳へ返す

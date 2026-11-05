# 両塔の batch の実測（andrew）— 記憶と一歩の時間を測るだけ。学習はしない

**task_id:** T-2026-11-06-tower-batch-probe  **kind:** analysis  **ホスト:** andrew  **PR の base:** phase0  **分岐:** feat/tower-batch-probe

## 0. この契約の位置づけ

- 利用者の決定（2026-11-06、起票の会話）: 両塔の学び直しの選定に **batch の軸を足す**。足す前に、andrew の装置で batch をどこまで上げられ、1 epoch の時間がどう変わるかを**測る**。本契約はその計測だけで、学習も設定の採否もしない
- 計測は数十歩だけ。重みは保存しない。val も測らない
- 本契約の結果は、塔の選び直しの回し直し（andrew）の起票で、batch の候補の値と所要の見込みに使う。採否は利用者が決める
- 把持塔の作り直し（T-2026-11-05-grasp-tower-rebuild）は bengio で並行して走る。本契約は andrew だけを使い、bengio に接続しない

## 1. 背景

- 検出塔は GPU ごと batch 2 × 2 枚 = 実効 4 で固定してきた。記録上の理由は、上流（Relation-DETR）の既定、Stage 0 との整合（`docs/experiment_settings.md` の検出塔の表）、A5000 の記憶（GPU ごと 3 まで。env-facts の dlsta の実測）で、batch を軸に選んだことはない
- 工程塔は物理 batch 16 で固定し、探索（T-2026-10-22-tower-reselect-search-dlsta）ではため込み {2, 4, 8} を軸にした。物理 batch は A5000 で 13 までしか入らず（env-facts）、二枚の道（GPU ごと 8 × 2 枚）で 16 を保った
- andrew の RTX A6000（48 GB）での上限は未測定

## 2. 確定した事実（出所つき）

| 項目 | 値 | 出所 |
|---|---|---|
| 検出塔の探索の学習設定（0 番） | 学習率 1e-4、weight decay 1e-4、max_norm 0.1、GPU ごと batch 2、2 枚、fp16、`presets.detr`（短辺 480〜800 の乱択、長辺 1333 以下） | `configs/detector_relation_detr/train_search.py`、`docs/experiment_settings.md` |
| 検出塔の起動の形 | `accelerate launch --multi_gpu --num_processes 2`、`EGO_ROOT`・`RELDETR_COCO_CKPT`・`RELDETR_OUTPUT_DIR` を環境変数で渡す | `scripts/run_tower_search.py` の検出塔の段、`scripts/run_stage1_dtower.sh` |
| 検出塔の 1 epoch の歩数（batch 2 × 2 枚） | 2,405 歩、一歩 0.598 秒（dlsta の A5000） | env-facts の dlsta の実測 |
| 検出塔の記憶（batch 2、A5000） | GPU ごとの torch の最大確保 約 12.3 GB、nvidia-smi 12,563 MiB。batch 3 は収まり、4 は OOM（`expandable_segments:True` なら 300 歩は通る） | 同 |
| 工程塔の学習設定 | fine-tune: R50 COCO 初期化、stem 凍結、短辺 800（800×1422）、反転、物理 batch 16 × ため込み 4、AdamW 1e-4、fp32、決定性の設定 | `configs/stage1_ptower_r3.yaml`、三周目の RESULT |
| 工程塔の二枚の道 | `torchrun --nproc_per_node=2`、DDP、layer1〜4 の SyncBatchNorm、GPU ごと 8 × ため込み 4、1 epoch 604 歩、一歩 0.794 秒、rank ごとの最大確保 約 14.9 GB（A5000） | env-facts の 0b の実測、`scripts/run_tower_search.py` の工程塔の段 |
| 工程塔の一枚の道 | A5000 では物理 batch 13 が上限（14 は OOM）。二枚の道は fp32 では一枚の道と重みが一致しない | env-facts、F 2026-10-21 の知見の行 |
| andrew の装置 | RTX A6000 × 2（48 GB）。検出塔の 2 プロセスには `NCCL_P2P_DISABLE=1` が要る | C §1、F 2026-10-19 |
| COCO の重みと入力 | `data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth`、画像は `data/raw/ego`、折り A の注釈は `data/annotations/egosurgery_tool_folds/A/` | `scripts/run_tower_search.py` の環境の設定、探索の SPEC §2 |

## 3. 定義

### 3.1 計測の水準

| 塔 | 道 | GPU ごとの物理 batch | 枚数 | 精度 |
|---|---|---|---|---|
| 検出塔 | 2 枚（accelerate） | 2、4、6、8 | 2 | fp16 |
| 工程塔 | 二枚の道（torchrun、SyncBatchNorm） | 8、12、16 | 2 | fp32 |
| 工程塔 | 一枚の道 | 16、24、32 | 1 | fp32 |

- 検出塔の batch 2 と工程塔の二枚の道の 8 は、既存の設定の再計測（dlsta の値と比べる基準）
- ため込みは変えない（検出塔は無し、工程塔は 4）。学習率も変えない（計測なので学習率は結果に効かない）
- 溢れた水準は、溢れた歩と記憶を記録して次の水準へ進む。`expandable_segments` は使わない（既定の確保の規則のまま。使った場合は別に記録）

### 3.2 測る量（水準ごと）

- 収まったか溢れたか
- GPU ごとの torch の最大確保と予約（バイト）、nvidia-smi の最大（MiB）
- 定常の一歩の時間: 最初の 10 歩を除く 50 歩の平均と標準偏差（読み込みの待ちを含む）
- 1 epoch の歩数（データ数 ÷ 実効 batch。読み込みの枚数から確かめる）と見込み時間（歩数 × 一歩の平均）
- 実際に読み込んだ枚数が batch の値と一致すること（記録から）
- 電力の上限と、計測中の GPU の使用率（参考）

### 3.3 口の作り方

- 検出塔: `train_search.py` の `batch_size` を点ごとに渡す口があるので、それを使う（無ければ設定の写しを repo の外に置く）。既存の設定と `third_party/` は変えない
- 工程塔: `ft_batch_size` は命令行の key=value で上書きできる。二枚の道は探索と同じ起動の形
- 数十歩で止める口（`--max-steps` に相当するもの）が無ければ、歩数で止める写しを repo の外に置く。既定の挙動は変えない
- 計測の出力（work、ログ）は版管理の外 `/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-tower-batch-probe/` に置き、表は `experiments/analysis/tower_batch_probe/` に書く

## 4. Task

**コマンドは書かない。実装と記録を読んで決めてよい。** 命令と出力は `audit.md` に残す。

### Task A — 開始状態（G1）

1. 分岐が `feat/` で始まり、起点が `origin/phase0` であることを記録する
2. 開始前から在る未追跡を消さない。一覧を記録する
3. andrew の compute プロセスを `/proc/PID/exe` の解決と引数の要素の完全一致で列挙する。本契約以外が一件でもあれば止めずに停止し、利用者に諮る
4. 記憶領域の空き、試験の失敗の名前の集合、既存の `.venv` と `.venv-relation-detr` のパッケージの一覧の要約値、GPU ごとの電力の上限・装置の型・driver を記録する
5. `contract.conventions_rev` と `meta.created_from` を実測し、食い違えば差し替えて `meta.amendments` に記録する

### Task B — 検出塔（G2）

1. §3.1 の 4 水準を順に測る。各水準の前に GPU の記憶が空いていることを確かめる
2. 対照: batch 2 の一歩の時間と記憶を、dlsta の実測（§2）と並べる。読み込んだ枚数が batch の値と一致することを、記録の行から示す
3. COCO の重みを読んだ行がログに在ることを確かめる（読まずに測ると記憶が違う）

### Task C — 工程塔

1. §3.1 の二枚の道 3 水準、一枚の道 3 水準を順に測る
2. 対照: 二枚の道の 8 を dlsta の実測（§2）と並べる。読み込んだ枚数が batch の値と一致することを示す

### Task D — 集計・検証・報告

1. 完了判定（§6）を実測で埋める。`make forbidden-check`（本 task_id つき）、L1 と L2、試験、仮想環境の一覧の要約値を Task A-4 と比べる
2. `README.md` と `docs/experiment_log.md` に書く。学習ではなく計測であることを明記する
3. `REPORT.md`、`RESULT.md`、`result.yaml`、`audit.md`、`tasks/inbox.d/T-2026-11-06-tower-batch-probe.md`
4. commit、push、PR と `make task-report`。抑止の解除は手順書の「8. 終える」に任せる

## 5. 読み方の規則（記述だけ）

1. 表の値は実測だけ。見込み時間は「歩数 × 一歩の平均」と書き、val と評価の時間を含まないと明記する
2. 設定の採否や推奨を書かない。学習率を batch に合わせる規則も書かない（利用者が決める）
3. 溢れた水準は、溢れた歩と記憶の値を書く。溢れなかった最大の水準を「上限」と呼ばない（`expandable_segments` や別の確保の規則で変わりうる）
4. 一歩の時間は読み込みの待ちを含む。GPU の使用率が低い水準は、読み込みが律速の可能性を書く

## 6. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 分岐、起点、未追跡、compute プロセス、空き、失敗の名前、仮想環境の要約値、装置と電力 | プロセスの列挙が自分のシェルを 1 件として拾い、存在しない実行ファイルの経路で 0 件になる |
| b | 検出塔 | 4 水準の表、枚数の一致、dlsta との並べ | batch の値を変えると読み込んだ枚数が変わる。重みを読まない写しで記憶が変わる |
| c | 工程塔 | 6 水準の表、枚数の一致 | 同上 |
| d | 無変更 | 重みの保存なし、禁止の場所の要約値が前後で一致、仮想環境の要約値が一致、失敗の名前が増えない、forbidden-check の本契約の経路の違反 0 件 | 同じ道具が本契約の新しいファイルを変更として検出する |
| e | test 不使用 | 読んだ動画の集合と {04, 05, 07} の共通が 0 件 | 集合に 04 を混ぜた入力で共通が 1 件になる |
| f | 記述 | §5 の規則どおり | 表の見込み時間を歩数と一歩の平均から計算し直すと一致する |
| g | PR | 番号、base phase0、Draft でない | 分岐名が `feat/tower-batch-probe` |

## 7. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。** `contract.inject_verbatim` の `conventions#prohibitions` を原文のまま適用し、加えて次を守る。

1. **test の動画（04、05、07）のフレームを読まない**
2. 学習しない（数十歩の計測だけ）。重みを保存しない。既存の run の置き場・checkpoint・凍結源・`data/raw`・`data/external`・注釈を変えない
3. `third_party/` と既存の仮想環境を変えない。既存スクリプトと設定の既定の挙動を変えない（口が無ければ写しを repo の外に置く）
4. 本契約の版管理の外の生成物は `/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-tower-batch-probe/` に置く
5. `context/auto/*` と `tasks/inbox.md` を再生成しない。生成物を作り直す検査を回さない。`forbidden-check` は回す
6. **装置の他のプロセスを止めない。** 他の compute プロセスが在れば停止して諮る
7. andrew だけを使う。bengio、efros、ilya、dlsta に接続しない
8. 開始前から在る未追跡と、同期で届く他の契約のファイルを消さない・動かさない
9. 外部への送信は `make task-report` 以外の経路で行わない。W&B は offline にする
10. 抑止の目印を手で置かない・手で外さない
11. §3.1 に無い水準を足さない

## 8. 停止して諮る条件

- andrew に本契約以外の compute プロセスがある（Task A-3）
- batch を変える口や歩数で止める口が、既定の挙動か `third_party/` を変えないと作れない
- 記憶領域が足りない
- 実行基盤が書き込み・移動・削除・外部の取得を拒む（回避せず、利用者に提示して許諾を得る）

停止のときも、それまでの実測を `RESULT.md` と `audit.md` に書き、PR と `make task-report` まで行う。

## 9. 報告の構成

**`RESULT.md` は起票者が判断に使う事実だけ。100 行以内。** 命令と出力は `audit.md` に置き、`RESULT.md` から行番号で指す。

| 節 | 内容 |
|---|---|
| 判定 | status と G1・G2 の結果 |
| 完了判定 | §6 の表に実測値 |
| 実測 | 塔ごとの水準の表（収まったか、記憶、一歩の時間、1 epoch の見込み）、dlsta との並べ、電力の上限 |
| 起票者の誤り | 型と内容。一件 3 行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、`make task-report` の終了コード |

`REPORT.md`（`experiments/analysis/tower_batch_probe/`）には全値と §5 の規則による記述を置く。

## 10. 送出

- PR の base は **phase0**。push は統合ではない。PR が Draft でなく存在する状態で終える
- `make task-report` で台帳へ返す

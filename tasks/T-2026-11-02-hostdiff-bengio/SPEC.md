# andrew と bengio のホスト差の測定（bengio 側）: dlsta 探索の 0 番の学習設定で工程塔 2 本と検出塔 3 本を回し、値と速さを記録する

**task_id:** T-2026-11-02-hostdiff-bengio  **kind:** analysis

**実行ホスト:** `bengio`（repo は `~/slocal2/m2`。`context/env-facts.md`「repo の位置」）。
**相手の契約:** `T-2026-11-02-hostdiff-andrew`（`andrew` で同じ時期に同じ本文で回る）。**本契約は相手のホストを読まない、書かない、値を待たない。**
**GPU:** 本ホストの GPU 2 枚を使ってよい（利用者の決定 2026-11-02）。一度に走らせる学習は一本だけにする。

## 1. 背景と目的

利用者は、andrew と bengio のホスト差を二つ知りたい（2026-11-02）。

- (a) 同じ処方で学習したとき、指標の値がどれだけ違うか
- (b) 学習の速さがどれだけ違うか

結果は、**同一ホストの規則を緩めるかの材料**に使う（利用者の決定 2026-11-02）。今の規則は `conventions#symmetry` の「ホストと装置型」（比べる腕と分母は同じホスト。ホストの行は「揃える」以外にしない）。本契約は規則を変えない。

bengio は前の契約 `T-2026-11-02-bengio-align-andrew`（PR #284。本契約を始める前に phase0 へ統合されている必要がある）で andrew に揃えた。Relation-DETR の本体、二つの仮想環境のパッケージ、データ、塔の重みは両ホストで同じ要約値である（`experiments/analysis/bengio_align_andrew/REPORT.md`、`experiments/analysis/bengio_andrew_env_survey/REPORT.md`）。揃えられない違いは装置と系（電力の上限、CPU、PCIe、IOMMU など。同じ調査の Task F の表）で、これが本測定で測る違いである。

**本契約は bengio 側の値を事前に決めた形で出すだけである。** 二つのホストの値の比べと区分の判定は、両方の契約が統合された後に、§6 の規則で行う。

## 2. 利用者の決定（本契約が従うもの）

| 日付 | 決定 | 本契約での扱い |
|---|---|---|
| 2026-11-02 | 両方の塔で測る | 工程塔と検出塔 |
| 2026-11-02 | 学習は収束まで（通常の学習設定） | 収束規則は §4 |
| 2026-11-02 | andrew でも新たに回す | 二つの契約を同じ本文で回す |
| 2026-11-02 | GPU 2 枚の通信は両ホストとも `NCCL_P2P_DISABLE=1` に揃える | 両塔とも |
| 2026-11-02 | 学習設定は dlsta 探索の 0 番の点 | §4 |
| 2026-11-02 | 本数は各ホストで工程塔 2 本（seed 42、123）、検出塔 3 本（seed 42 を二度、seed 123） | Task C・D |
| 2026-11-02 | 判定の区分は dlsta のホスト公平性の契約（D1）と同じ | §6 |
| 2026-11-02 | 電力の上限は揃えない | 変えない。(b) の差に含まれる |
| 2026-10-21 | dlsta の実験はハイパーパラメータ探索のためだけに使い、ほかの比較に用いない | dlsta の値を本測定の値と並べない。照合するのは起動の設定と入力の要約値だけ |

## 3. 両ホストで揃えるものと違うもの

| 行 | andrew | bengio | 扱い |
|---|---|---|---|
| コード | 起点 origin/phase0 の同じ commit | 同じ | 揃える。報告に commit を書く |
| Relation-DETR の本体 | source 2f08e5213cb5c377…、all 20f15c061b435ce4… | 同じ | 揃える（Task A で測る） |
| 仮想環境のパッケージ | 一致（調査 Task C） | 同じ | 揃える |
| 入力（画像、注釈、manifest、折り、重み） | 一致（調査 Task D） | 同じ | 揃える |
| 学習設定 | dlsta 探索の 0 番 | 同じ | 揃える |
| seed と本数 | §2 | 同じ | 揃える |
| GPU の枚数と通信 | 2 枚、`NCCL_P2P_DISABLE=1` | 同じ | 揃える |
| 一度に走らせる学習 | 一本 | 一本 | 揃える |
| GPU の型と driver | RTX A6000 × 2、595.84 | 同じ | 揃っている |
| 電力の上限 | 300 W | 220 W | 測る違い |
| CPU、メモリ、PCIe、IOMMU | 調査 Task F | 調査 Task F | 測る違い |
| MS-Deform-Attn の `.so` | 79b55a8a… | 1a05ed5b…（`build.ninja` は同じ） | 測る違いに含まれる |

## 4. 学習設定（dlsta 探索の 0 番）

0 番は現行の処方である（工程塔は三周目、検出塔は二周目。`tasks/T-2026-10-22-tower-reselect-search-dlsta/prereg.md` 16 行）。値は同じ置き場の `points.csv` の 0 行。

- 起動の設定の手本は、dlsta 探索の 0 番の run の記録である: 工程塔 `experiments/phase1/stage1_ptower_search/stage1_ptower_search_001_ft_coco_lr0.0001_foldA_point00_seed42/`（backbone）、`..._002_features_...`（特徴）、`..._003_` から `..._012_`（時間ヘッド 10 本）、検出塔 `experiments/baselines/stage1_dtower_search/point00_dcoco_foldA_seed42/`。各 run の `command.sh` と `config.yaml` を読む
- **許した違い（これ以外は手本と同じにする）**: 経路（repo と scratch の位置）、GPU の番号、ポート、seed、出力と記録の置き場、run の名前、`NCCL_P2P_DISABLE=1` の追加、本契約の識別子
- 収束規則は手本どおり（停滞 4 epoch で学習率 0.1 倍を一度、再停滞 4 epoch で打ち切り、上限 36。検出塔は val mAP、工程塔は val frame accuracy。prereg 52 行）。時間ヘッドは手本どおり（上限 50、停滞 10）
- 工程塔は二枚の道（DDP、layer1〜4 の SyncBatchNorm、GPU ごと 8 枚、累積 4）。決定性の設定は手本どおり
- 検出塔は 2 プロセス、GPU ごと batch 2、fp16 の autocast（`conventions#precision`）
- 工程塔は工程注釈のある 17,233 フレーム（手本は `manifest_dir=data/processed/phase_manifest_all_phase`）。検出塔は 15,437 枚。どちらも折り A（`conventions#folds`）。test は読まない

**道具はこのホストで動く形に合わせてよい。** 手本の道具（`scripts/run_tower_search.py`、`scripts/tower_search_common.py`、`tasks/T-2026-10-22-tower-reselect-search-dlsta/run_control.py`）は dlsta の前提を持つ（GPU の組が `1,2` と `3,4`、GPU0 の禁止、scratch の置き場が探索の契約の名前）。合わせ方は実行者が決めてよいが、次を守る。

- `scripts/` の既存の道具を変えるなら、環境変数か引数で上書きできる形にし、**既定の挙動を変えない**。既定の挙動が変わっていないことを試験で確かめる
- 新しい台本は `tasks/T-2026-11-02-hostdiff-bengio/` の下に置く
- run の置き場は `experiments/phase1/stage1_ptower_hostdiff_bengio/` と `experiments/baselines/stage1_dtower_hostdiff_bengio/` の下に限る。**二つのホストの run の置き場を分けるため**（同じ名前の run が同期で衝突しない）

## 5. 禁止事項と申し送り

注入される規約に従う。加えて次を守る。

1. **相手のホストを読まない、書かない。** 相手の契約の値を待たない。比べは §6 で後に行う
2. **dlsta の値を本測定の値と並べない**（§2 の 2026-10-21 の決定）。手本の run から読むのは起動の設定と入力の要約値だけ
3. **checkpoint、特徴、予測、学習のログの大きなものは repo の外に置く**（例 `~/m2-scratch/T-2026-11-02-hostdiff-bengio/`）。repo の `.stignore` の同期の型（`experiments/**/` の下の `*.py`・`*.npy`・`*.pt`・`*.pth`、`logs`・`checkpoints`・`predictions` などの名前のディレクトリ、ほか）を repo の中に作らない。**置く前に `.stignore` を読む。** 置いた後、相手のホストに届く型が無いことを確かめる
4. **一度に走らせる学習は一本。** 本ホストで本契約以外の GPU の使用が出たら、時刻・PID の有無・メモリ・使用率を記録する。学習を止めない。10 分以上続いたら利用者に伝える
5. **生成物の再生成（`make taskindex`、`make inbox`、`make runindex` など）と `*-check` を本契約の分岐で回さない。** 二つの契約が並行して同じ生成物に書くと衝突する。収穫は両方の統合の後に行う。`make forbidden-check TASK=...` は回してよい
6. `data/`、`third_party/`、二つの仮想環境、凍結源、他の契約の置き場を変えない。電力の上限、クロックなど装置の設定を変えない
7. 禁止は実行者の操作に対するものである。同期処理が他のホストから配る変更は含まない。届いたものは届いたものとして記録する
8. W&B は offline で記録する（外へ送らない）

**申し送り:**

- 起動の細部、ログからの時間の取り出し方、GPU の標本の取り方は、実装を読んで実行者が決めてよい
- 評価の checkpoint は絶対経路で渡す（相対経路は読み込みを飛ばして AP 0 を返す。env-facts の装置の節）
- 学習の記録に COCO の重みを読んだ行があることを、両塔の各 run で確かめる
- プロセスの計数は `scripts/grasppilot/proc_enum.py`（`/proc/PID/exe`）を使う

## 6. 値の形と、後で行う比べの規則（測る前に固定する）

### 6.1 本契約が出す値（`values.json`）

`experiments/analysis/hostdiff_andrew_bengio/bengio/values.json`。キーの名前を変えない。足すのはよい。

- `host`、`task_id`、`code_commit`、`env`（driver、CUDA の実行時の版、cuDNN、NCCL、torch、torchvision、accelerate、画像の復号の実装と版、TF32 の設定〔matmul と cudnn〕、工程塔の決定性の設定、検出塔の autocast、`NCCL_P2P_DISABLE`、電力の上限、両塔の学習のプロセスで読んだ値）
- `determinism_check`: 工程塔の短い学習二回の損失の列の要約値と一致の有無、歩数
- `phase.seed42`・`phase.seed123`: `J_heads`（時間ヘッド 10 本の val macro Jaccard。手本の 003〜012 の順）、`J_mean`（10 本の平均）、`J_max`、`backbone_val_frame_acc`、`lr_drop_epoch`、`stop_epoch`、`checkpoint_epoch`、`cap_reached`、`coco_loaded`
- `detector.seed42a`・`detector.seed42b`・`detector.seed123`: `mAP`（val overall）、`AP_signature`（`conventions#det_groups` の標的群）、`AP_negative`（陰性対照群）、`AP50`、`lr_drop_epoch`、`stop_epoch`、`checkpoint_epoch`、`cap_reached`、`coco_loaded`
- 各 run の `timing`: `wall_s`（起動から終わりまで）、`train_s_per_epoch`（val を除く学習だけの秒数の各 epoch の列と中央値）、`s_per_step_median`（最初の 50 歩を除いた最適化の一歩の秒数の中央値。工程塔は micro-step と optimizer step を分けて書く）、`eval_s`、工程塔は `features_s` と `heads_s`
- 各 run の `gpu`: 10 秒ごとの標本（電力、SM クロック、メモリクロック、使用率、メモリ、温度）の学習中の平均と中央値。標本の全件は repo の外
- 各 run の `foreign_gpu_use`: 本契約以外の GPU の使用の時刻の区間（無ければ空の列）

### 6.2 後で行う比べ（両方の契約の統合の後。本契約では計算しない）

記号: andrew の値を A、bengio の値を B、seed を後ろに付けて書く（例 A42、B123。検出塔の seed 42 の一回目と二回目は A42a・A42b）。

**工程塔**（主の値は `J_mean`。`J_max` と `backbone_val_frame_acc` も同じ式で出す）

- d_host = （|A42 − B42| + |A123 − B123|）÷ 2
- d_seed = （|A42 − A123| + |B42 − B123|）÷ 2
- r = d_host ÷ d_seed
- d_rerun は Task B で 0 と確かめた場合に 0 とする。0 でなければ利用者に聞いてから扱いを決める

**検出塔**（主の値は `mAP`。`AP_signature` も同じ式で出す）

- 各ホストの seed 42 の値 m = （42a + 42b）÷ 2
- d_rerun = （|A42a − A42b| + |B42a − B42b|）÷ 2
- d_host = （|mA − mB| + |A123 − B123|）÷ 2
- d_seed = （|mA − A123| + |mB − B123|）÷ 2
- r = d_host ÷ d_seed。d_host ÷ d_rerun も並べる

**区分**（D1 と同じ。`tasks/T-2026-09-23-dlsta-host-fairness/SPEC.md` の「区分」の表）

| 区分 | 条件 |
|---|---|
| 無視できる | r が 0.5 以下 |
| 要注意 | r が 0.5 を超え 1 以下 |
| 不公平 | r が 1 を超える |
| 判定不能 | d_seed が 0、または値が無い |

- 区分は塔ごとに、主の値で付ける。ほかの値は並べるだけ
- d_host と d_rerun が同程度なら、ホスト差は非決定性と区別できない。その場合は区分に加えてそう書く（D1 と同じ文。「同程度」の線は置かず、d_host ÷ d_rerun の値を書く）
- D1 の「割り当ての帰結」の列は、今の規約（同一ホストの規則）より前の運用である。帰結は規約を変えるかの利用者の判断に回し、本測定では付けない

**速さ (b)**

- 塔ごとに、B ÷ A の比を `s_per_step_median`（主）、`train_s_per_epoch` の中央値、`wall_s` で出す。`wall_s` は収束までの epoch 数の違いを含むので、epoch 数と並べる
- 区分は付けない。電力・クロック・使用率の標本を並べる
- `foreign_gpu_use` がある run の速さには印を付ける

## 7. Task

### Task A — 開始状態と照合（G1）

1. 手順書の「0. 始める」に従う。分岐 `feat/hostdiff-bengio`、起点 `origin/phase0` を記録する
2. 本契約以外の compute の件数（陽性対照と陰性対照つき）、GPU 2 枚の空き、記憶領域の空き（バイト）を記録する。本ホストの GPU に他の利用者の処理があれば、空くまで待つか利用者に伝える
3. `reldetr_digest.py` で `third_party/Relation-DETR` の要約値を取り、§3 の andrew main の値と比べる
4. 入力の要約値を取り、記録と比べる: `image_input_lock.json` の全行（前の調査と同じ取り方）、工程の manifest（`phase_manifest_all_phase`）、折り A の術具注釈、COCO の重み（両塔）
5. §6.1 の `env` を取る
6. 手本の run の `command.sh` と `config.yaml` を読み、本ホストで起こす設定との差を全行書く。差が §4 の許した違いの他にあれば止めて利用者に聞く
7. 道具を本ホストで動く形に合わせる（§4）。既定の挙動が変わっていないことを試験で確かめる

G1: 3〜6 が一致し、GPU が空いていれば通過。

### Task B — 工程塔の決定性の確かめ（G2）

1. 工程塔の backbone の学習を、seed 42、0 番の設定で、短く（例えば最初の 50 optimizer step）二度回す
2. 二回の損失の列が bit 単位で一致するかを書く。一致しなければ G2 で止めて利用者に聞く
3. この二回は本測定の run に数えない。出力は repo の外に置く

### Task C — 工程塔 2 本

1. seed 42、続いて seed 123。各 run は backbone の fine-tune、特徴の取り出し、時間ヘッド 10 本（手本と同じ 10 構成）
2. 各 run で §6.1 の値・時間・GPU の標本・本契約以外の GPU の使用を記録する
3. 学習の記録に COCO の重みを読んだ行があることを確かめる。無ければ止めて利用者に聞く

### Task D — 検出塔 3 本

1. seed 42（一回目）、seed 42（二回目）、seed 123 の順で回す
2. 各 run で §6.1 の値・時間・GPU の標本・本契約以外の GPU の使用を記録する。val の評価は収束規則が選んだ checkpoint で行う（手本と同じ）
3. 学習の記録に COCO の重みを読んだ行があることを確かめる

### Task E — 値の表

1. `values.json` を §6.1 の形で書く。測れなかった欄は理由つきの UNKNOWN
2. `REPORT.md` に、5 本の値と速さの表、収束の記録、GPU の標本の要約、本契約以外の GPU の使用の区間を書く。**相手のホストとの比べは書かない**

### Task F — 検証と報告

1. test を読んでいないことを、学習と評価に通した動画の集合で確かめる（折り A の test 動画 04・05・07 との共通が 0）
2. repo の中に同期の型のファイルが無いことと、相手のホストを読み書きしていないことを書く
3. `make forbidden-check TASK=T-2026-11-02-hostdiff-bengio` を回す
4. 報告（§9）を書き、commit、push、PR を作る。**PR の base は phase0。** Draft を外す
5. `make task-report` で台帳へ返す。抑止の目印は手順書の「8. 終える」が外す

## 8. 完了判定

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態と照合 | Relation-DETR・入力・起動の設定の照合の結果と、`env` がある | 入力の要約値の一つを一文字変えた値と比べると不一致になる。手本の設定の一行を変えた写しと比べると差に出る |
| b | 決定性 | 二回の損失の列が一致 | 二回目の列の一つの値を最下位の桁で変えると不一致になる |
| c | 5 本の学習 | 5 本とも収束規則で終わり、各 run に値・時間・収束の記録がある。COCO の重みを読んだ行がある | COCO の重みの経路を存在しない経路にした設定では、読み込みの行が出ない（実行の要否は実行者が決める。行わない場合は env-facts の既知の挙動を引く） |
| d | values.json | §6.1 の全キーがあり、値か理由つきの UNKNOWN が入っている | キーの一つを消した写しを検査にかけると欠けとして出る |
| e | 他の使用 | 各 run に `foreign_gpu_use` がある（空の列を含む） | 列挙の道具が、実在のプロセスを 1 以上、存在しない経路を 0 と数える |
| f | test と置き場 | test 動画との共通 0。repo の中に同期の型 0 件 | 04 を混ぜた集合では共通 1。`experiments/x/foo.npy` は同期の照合で「当たる」 |
| g | 道具 | 既定の挙動が変わっていないことの試験の結果 | 既定の挙動を一つ変えた写しで試験が落ちる |
| h | PR | PR が存在し、base が phase0、分岐が `feat/hostdiff-bengio`、Draft でない | — |

## 9. 報告の構成

### 9.1 `RESULT.md`（目安 150 行以内）

| 節 | 内容 | 入れないもの |
|---|---|---|
| 判定 | verdict と G1・G2 の結果 | 手続きの全文 |
| 完了判定 | §8 の表。各項目に実測値 | 命令の全文 |
| 実測 | 5 本の主の値（工程塔 `J_mean`、検出塔 `mAP`）、`s_per_step_median`、`wall_s`、epoch 数、本契約以外の GPU の使用の有無 | 経過の説明、相手のホストとの比べ |
| 起票者の誤り | 型と内容。一件 3 行以内 | 引用の全文 |
| 逸脱 | 何をなぜ | 手順の再掲 |
| 想定外・UNKNOWN | 測れなかったものと理由 | 不要なログ |
| 送出 | PR 番号、`make task-report` の終了コードだけ | 出力の全文 |

### 9.2 `audit.md`

命令とその出力、起動の設定の差の全行、要約値の全件、検証の出力、変更範囲の一覧、台帳の応答。`RESULT.md` からは行番号で指す。

## 10. 想定外のときの扱い

- 起動の設定が手本と許した違いの他で違う: 止めて利用者に聞く
- 発散・非数: その run を止めて利用者に聞く
- 上限 36 に達した: 止めない。印を付けて記録する
- 本契約以外の GPU の使用が 10 分以上続いた: 止めずに利用者に伝え、その run の速さに印を付ける
- 決定性の確かめが一致しない: 止めて利用者に聞く（§6.2 の工程塔の d_rerun の扱いが変わる）
- 記憶領域が足りない: 止めて利用者に聞く。範囲を狭めて続けない

## 11. 参照しなかった項目

- 分母: 本契約は処置と分母を持たないので `inputs.denominator` を置かない。報告に「参照しなかった」と書く
- 規約の版 `contract.conventions_rev` と `meta.created_from.runindex_commit` は起票時の値。実行者が実測して差し替える

# Stage 1: 工程塔 P\*-21 と P\*-15 を三候補のトーナメントで五折り確定する

**task_id:** T-2026-09-18-stage1-phase-tower  **kind:** exp

## 1. 背景

G0 の三条件の材料が揃い、主目標は MICCAI 2027 に決まった（2026-09-17）。Stage 1 は各タスクの最良塔を折りごとに確定する段で、
本契約は工程塔 P\* を担当する。検出塔 D\* は別契約（検出器環境のあるホストが空いてから）。

M §5.1 の新鉄則: **P\* は ImageNet か中立 SSL の初期化**。Stage 0 の凍結工程塔（S4）は検出 backbone（Relation-DETR）の
特徴を使っており、v2 で「共有特徴が動画の同一性を運び、工程の分母を汚した」と判定された。だから P\* は作り直す。
S4 は折り A の参照値としてだけ使う（判定には使わない）。

候補 3 つと掃引集合は `prereg.md` に固定した。**学習開始前に prereg.md を commit する。**

**本契約は GPU を使う**（利用者承認 2026-09-18）。装置は ilya の 2 枚。

## 2. 確定した事実（ホストによらない値だけ）

- 折り表は `conventions#folds`（T-2026-09-17-fold-table、PR #176、phase0 に統合済み）。追加 6 動画は 17〜22 で、15 動画との重複 0
- Stage 0 の S4（分母参照）: `phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`、
  3 seed、val accuracy 0.8986 ± 0.0034、val Jaccard 0.6447 ± 0.0146（tasks/todo.md の 2026-06 の記録）。処方は 50 epoch、
  batch 1（動画単位）、AdamW lr 5e-4、cosine、TeCNO 2 段 8 層 64 maps、causal（`configs/stage/s4_phase_baseline.yaml`）
- 既存の道具: `scripts/extract_stage1_features.py`（凍結 backbone → C5 GAP 2048-d、npz）、`scripts/train_s4_tecno.py`
  （cache + manifest → clip 列 → TeCNO 学習 → val PhaseMetrics、ExperimentManager category=phase1、証跡配線済み）、
  `src/egosurgery/models/heads/tecno_head.py`（因果性テストあり）、`scripts/train_phase_tower_r50.py`（B4 の暫定塔。
  ImageNet-R50。正式実装として残すかは未決）
- 工程 manifest: `data/processed/phase_manifest/{train,val,test}.json`（15 動画、検出 split と一致）。**追加 6 動画の manifest は
  無い可能性が高い。** 画像と注釈の実在を Task A で測る
- B4 の暫定塔は 1 seed・3 epoch で 105 秒（工程塔学習の下限の目安であって、本契約の run 時間ではない）
- 主指標の定義は `conventions#eval_recipe`。online-causal、Jaccard strict
- 対話シェルは zsh。`git --no-pager`。`make` には読み込みを同じ命令に含める

## 3. Task

**コマンドは書かない。実装を読んで決めてよい。** 出力は `audit.md` に残す。

### Task A — 開始状態と材料

1. 作業ツリーの清浄を確かめる。開始前から在る未追跡は移動で退避し、退避先と件数を記録する。**HEAD が phase0 であることを記録する**
2. 装置の状態を記録する（`/proc/PID/exe` の解決か引数の完全一致。部分一致は使わない）。他利用者の処理があれば停止して諮る
3. `conventions#folds` を解決し、5 折りの test・val・train の動画集合を得る。公式分割の三ファイルと折り A が集合として一致することを確かめる
4. 追加 6 動画（17〜22）の画像（0.5 fps のフレーム）と工程注釈が本ホストに実在するかを測る。無ければ停止して諮る
   （escalate_if。P\*-15 だけで進めるかは利用者が決める）
5. 15 動画の工程 manifest を折り表に合わせて組み替える方法を実装から決める（既存 manifest は公式分割固定。折りごとの train・val・test 集合を
   動画単位で作る）。**`data/splits/` の既存ファイルは変えない**
6. 1 run の所要時間を、候補 A の 1 構成・折り A・1 seed で実測する（Task B の後でよい）。1 時間を超えるなら諮る
7. `conventions_rev` と `runindex_commit` を実測し spec.yaml の占位を差し替える。**prereg.md を commit し、その commit を `prereg.commit` に書く**

### Task B — 空間特徴の抽出（一度だけ）

1. 凍結 ImageNet-1K ResNet-50（torchvision の重み。出所と要約値を記録）で、21 動画の全フレーム（0.5 fps）の C5 GAP 2048-d を抽出する。
   前処理は決定的（増強なし）。`extract_stage1_features.py` の経路を ImageNet 重みで使えるか実装を読んで決める
2. 決定性: 同じ入力で二度抽出し、要約値が一致することを示す。**重みを変えると要約値が変わることを一度示す**（陰性対照）
3. 動画ごとのフレーム数が manifest と一致することを集合差で確かめる
4. 大きさをバイト数で記録する（丸めを実数として扱わない）。置き場は `data/processed/` 配下

### Task C — 候補 A

1. 候補 A（causal 2 段 TCN）の掃引 2 点（受容野 短・長。値は実装の受容野の式から決め、prereg の表に沿って記録）を、
   5 折り（折り A は 3 seed、他は 1 seed）で学習する。P\*-21（追加 6 動画を train に足す）と P\*-15 の両方
2. 学習は折り内 val で early stopping・最良 epoch の選択を行う。**test は見ない**
3. 各 run に task_id を刻み（`config.yaml`）、ExperimentManager の証跡を残す。metrics.json に val の主指標と co-primary を書く
4. 対照: 折り A・1 seed で単フレーム線形分類（時間ヘッドなし）を回す

### Task D — 候補 B・C

候補 B（Transformer 集約 2 水準）と候補 C（平滑化損失 2 水準）を、候補 A の掃引 2 点それぞれの上に載せて、Task C と同じ折り・seed で学習する。
合計の構成は A 2・B 4・C 4 の 10。×（P\*-21、P\*-15）×（5 折り、折り A は 3 seed = 7 run）= 140 run。

候補 B は PE を入れない（ASFormer の否定例）。候補 C の平滑化は truncated MSE（MS-TCN Table 5 の「後段に確率と特徴を渡すと壊れる」は
段間の受け渡しの話で、損失項の話ではない。混同しない）。

### Task E — 選定と test

1. prereg §6 の規則で P\*-21 の recipe を決める。表（候補 × 掃引点 × 折り × seed の val 主指標と co-primary）を先に作り、規則を機械で当てる
2. P\*-15 に同じ recipe を適用する
3. 確定した塔について、**折りごとに一度だけ** test を評価し、test アクセス台帳に記録する。評価した回数を数え、確定塔 2 種 × 5 折り = 10 回を超えないことを示す
4. 折り A の P\*-21 の val と test を、Stage 0 の S4 の値と並べて記録する（判定に使わない）
5. prereg §4 の予測 5 項目の当たり・外れを書く

### Task F — 検証と報告

1. L1、L2、`make forbidden-check`、`make spec-check TASK=T-2026-09-18-stage1-phase-tower`、試験（失敗数が増えていないこと）、`make runindex` で新実験が現れること
2. 完了判定 a〜i を実測で埋める
3. `RESULT.md`、`result.yaml`（版 3）、`audit.md`、`tasks/inbox.d/T-2026-09-18-stage1-phase-tower.md`。T1（塔の性能表）の材料になる表を RESULT に置く
4. commit、push、**PR の base は `phase0`**。分岐名 `feat/stage1-phase-tower`
5. 報告後に `.sync-pause` を移動で解除する

## 4. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。**

1. `data/splits/` の既存ファイルを変えない。折りの集合は `conventions#folds` から作る
2. 選定・early stopping・ハイパラの選択に test を使わない。test は確定塔について折りごとに一度
3. 掃引集合に後から点を足さない（prereg で固定）。候補を足さない
4. 検出 backbone（Relation-DETR）の特徴を P\* に使わない（M §5.1）
5. 追加 6 動画を test にも val にも入れない
6. `context/auto/*` と `tasks/inbox.md` を再生成しない（`taskindex-check`・`inbox-check` の exit 2 は想定どおり）
7. `runindex/**` を手編集しない（`make runindex` での再生成は可）。`context/conventions.md` に触れない
8. 既存の `tasks/*/` を変えない。開始前から在る未追跡を消さない
9. 他利用者の処理を止めない
10. 外部への送信は `make task-report` 以外の経路で行わない

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 特徴抽出が一度、決定的 | 二度の要約値一致、フレーム数が manifest と一致 | 重みを変えて要約値が変わる。manifest から一動画を消した集合で差 1 |
| b | 全 run が折り表に従う | 各 run の train・val・test 集合が規約の表と集合差 0 | 一つの run の config の test 動画を入れ替えた検査で差 1 |
| c | 候補 × 掃引点の表 | 5 折り平均 val Jaccard と accuracy、折り A の SD | 表の行数 = 10 構成 × 2 データ設定。欠けがあれば UNKNOWN と書く |
| d | 選定が一意で test を使わない | 規則を機械で当てて 1 構成 | test 列を表から消しても同じ結果になることを示す |
| e | test は確定塔のみ折りごとに一度 | 評価回数 ≤ 10、台帳に記録 | test の評価ログの件数を数え、確定塔以外の test 評価が 0 件 |
| f | 折り A と S4 の並置 | val と test の両方 | S4 の値の出所（runindex の実験 ID）を書く |
| g | 単フレーム線形の対照 | 候補 A が上回る | 対照の値と候補 A の折り A の値を並べる。上回らなければ停止した記録 |
| h | task_id の刻印と収穫 | `make runindex` で新実験が現れる | 収穫前後の experiments.csv の行数の差 = 新実験数 |
| i | PR | 番号、base phase0、Draft でない | 分岐名 `feat/stage1-phase-tower` |

## 6. 想定外と停止条件

- 追加 6 動画が無い → 停止して諮る。P\*-15 の学習は続けてよい
- 候補 A が単フレーム線形を下回る → 停止して諮る
- 特徴の要約値が二度で一致しない → 停止
- 1 run が 1 時間を超える → run 数の見直しを諮る（候補 B・C の掃引を 1 水準に落とす案を提示する）
- 装置が使われている → 停止して諮る
- 実行基盤が書き込みを拒む → 回避せず提示

## 7. 報告の構成

`RESULT.md` は判断に使う事実だけ。目安百五十行以内。

| 節 | 内容 |
|---|---|
| 判定 | `verdict` と各 Gate |
| 完了判定 | 表。各項目に実測値 |
| 実測 | 候補 × 掃引点の val 表、確定 recipe、確定塔の 5 折り test 値、折り A と S4 の並置、対照、1 run の所要時間、予測 5 項目の当たり外れ |
| 起票者の誤り | 型と内容。一件三行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、base、終了コード |

## 8. 申し送り

- 本契約は ilya の GPU 2 枚を使う。efros で走る混合精度の契約とは装置が別
- 検出塔の契約は別途。本契約の結果を待たない
- 予測外れは F に残す。当たったかどうかより、外れ方が次の提案の材料になる
- `scripts/train_phase_tower_r50.py`（B4 の暫定塔）を再利用するか、`train_s4_tecno.py` の特徴入力を ImageNet 特徴に差し替えるかは実装を読んで決める。
  どちらを使ったかと理由を報告に書く

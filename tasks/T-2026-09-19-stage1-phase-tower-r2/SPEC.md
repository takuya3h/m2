# Stage 1 工程塔の二周目: backbone を工程ラベルで fine-tune し、時間ヘッドを再トーナメントする

**task_id:** T-2026-09-19-stage1-phase-tower-r2  **kind:** exp

## 1. 背景

一周目は凍結 ImageNet 特徴の上の時間ヘッドを比べ、val 0.329 / test 0.225 の塔を確定した。S4（検出 backbone 由来）の 0.645 に遠い。
利用者の指摘（2026-09-18）: 検出塔 D\* が backbone を手術データで fine-tune しているのに、工程塔 P\* を凍結のままにするのは不公平で、
近年の工程認識研究にも例が無い。起票者は一周目のカードで「凍結範囲」の軸を落としていた（起票者の設計の欠落）。

本契約は backbone を折りごとに工程ラベルで fine-tune し、D\* と対称にする。設計は `prereg.md`。

**本契約は GPU を使う**（利用者承認 2026-09-18）。装置は ilya の 2 枚。数値精度は一周目と同じ（変えない）。

## 2. 確定した事実（ホストによらない値だけ）

- 一周目の成果物（PR #183、`experiments/phase1/stage1_ptower/`、`scripts/run_stage1_ptower.py`、`scripts/select_stage1_ptower.py`）。
  **PR #183 が phase0 に統合されていることを Task A で確かめる。** 未統合なら分岐から取り寄せ、逸脱に書く
- 一周目の値: 確定塔 5 折り平均 val 0.32891 / test 0.22472、折り A val 0.36689。単フレーム線形対照（折り A、seed 42）val macro Jaccard 0.22495、accuracy 0.48383
- S4 の折り A 参照: val Jaccard 0.6447 ± 0.0119（当初 3 run）。索引の 17 run 集計は 0.6322。**当初 3 run を参照に使う**（一周目の `s4_reference_audit.json`）
- 検出塔の凍結範囲: `freeze_indices=(0,)`（stem のみ）。出所は efros の実験設定索引 §2.1（T-2026-09-18-stage1-detector-towers の実測）
- B4 の暫定塔: `scripts/train_phase_tower_r50.py`、ImageNet-R50 を train の 10 動画で 3 epoch、105 秒。val accuracy 0.6924（フレーム単位）
- 一周目の特徴抽出は 15 動画 15,437 フレームで 91 秒
- 追加 6 動画（17〜22）の注釈は ilya に在る。**画像は一周目時点で無かった。** 利用者が用意すると言っている。Task A で有無を測る
- 折りごとの工程 manifest は一周目が組み替えた（`stage1_ptower` の実装）。再利用する
- 対話シェルは zsh。`git --no-pager`。`make` には読み込みを同じ命令に含める

## 3. Task

**コマンドは書かない。実装を読んで決めてよい。** 出力は `audit.md` に残す。

### Task A — 事前登録と開始状態

1. **最初に `prereg.md` を commit し、hash と時刻を `spec.yaml` の `prereg.commit`・`prereg.committed_at` に書く**
2. 作業ツリーの清浄、HEAD が phase0、装置の状態（`/proc/PID/exe` か引数の完全一致）。他利用者の処理があれば停止
3. PR #183 の統合を確かめる。一周目の道具（run・select・manifest の組み替え）が本分岐にあること
4. 追加 6 動画（17〜22）の 0.5 fps フレームの有無を測る。在れば動画ごとのフレーム数と注釈のフレーム数の一致を確かめる。無ければ P\*-21 は UNKNOWN
5. `train_phase_tower_r50.py` の凍結範囲・学習率の既定・batch・増強・最適化器を読み、記録する。凍結範囲が stem のみでなければ、**stem のみに揃える**（実装の変更を最小に。変更箇所を記録）
6. `conventions_rev` と `runindex_commit` を実測し占位を差し替える

### Task B — backbone の fine-tune（14 本）

1. 折りごと、seed ごと、学習率 2 水準ごとに、train 動画の工程ラベルで fine-tune する。val で最良 epoch を選ぶ（上限 12）。**test を読まない**
2. 1 本目で所要時間を測る。1 時間を超えるなら諮る
3. 各 run の val frame accuracy を記録し、一周目の線形対照（0.48383）と比べる。下回る折りがあれば停止（G2）
4. 損失の推移を残す。発散・非数があれば停止

### Task C — 特徴の抽出

1. fine-tune 後の各 backbone から、その折りの全動画（train・val・test。画像があれば追加 6 動画も）の C5 GAP を抽出する
2. 決定性: 一つの backbone で二度抽出し要約値が一致すること。別の backbone で要約値が変わること
3. 置き場は `data/processed/stage1_features/` 配下（一周目と並べる）。大きさをバイト数で記録

### Task D — 時間ヘッドの再トーナメント

1. 一周目と同じ 10 構成を、学習率 2 水準 × 7（折り・seed）の特徴の上で回す（140 run）。一周目の `run_stage1_ptower.py` を再利用する
2. **対照**: 一周目の確定塔の値（同じ折り・seed）を表に並置する
3. task_id を刻み、metrics.json に val 主指標と co-primary

### Task E — 選定・test・並置

1. prereg §5 の規則を `select_stage1_ptower.py` で当てる（同点規則は最初から含まれている）。一意に決まらなければ諮る
2. P\*-15 を確定。画像があれば P\*-21 を同じ recipe で学習（追加 6 動画を train に足す。test・val には入れない）
3. test は確定塔について折りごとに一度。台帳に記録。回数を数える（P\*-15 で 5、P\*-21 があれば +5）
4. 折り A の val を S4 と並置し、差を一周目の 0.278 と比べる
5. prereg §3 の予測 5 項目の当たり・外れ

### Task F — 検証と報告

1. L1、L2、`make forbidden-check`、`make spec-check TASK=T-2026-09-19-stage1-phase-tower-r2`、試験、`make runindex`
2. 完了判定 a〜i を実測で埋める
3. `RESULT.md`、`result.yaml`（版 3）、`audit.md`、`tasks/inbox.d/T-2026-09-19-stage1-phase-tower-r2.md`。T1 の材料の表
4. commit、push、**PR の base は phase0**。分岐名 `feat/stage1-phase-tower-r2`
5. 報告後に `.sync-pause` を移動で解除する

## 4. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。**

1. `data/splits/` を変えない。折りの集合は `conventions#folds` から
2. fine-tune・最良 epoch・選定に test を使わない。test は確定塔について折りごとに一度
3. 検出 backbone（Relation-DETR）の重みや特徴を P\* に使わない
4. 追加 6 動画を test にも val にも入れない
5. 掃引集合（学習率 2、時間ヘッド 10 構成）に後から足さない
6. `context/auto/*` と `tasks/inbox.md` を再生成しない
7. `runindex/**` を手編集しない。`context/conventions.md` に触れない
8. 既存の `tasks/*/` を変えない。開始前から在る未追跡を消さない
9. 他利用者の処理を止めない
10. 外部への送信は `make task-report` 以外の経路で行わない

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | fine-tune が train のみ、epoch 選択が val のみ | 集合差 0、test の読み込み 0 件 | 一つの run の config の train に test 動画を混ぜた検査で差 1。学習経路が test を読まないことを実装の行で示す |
| b | 凍結範囲が stem のみ | 実装の行 | `requires_grad` が True のパラメータ群を数え、stem が 0 件・layer1〜4 が非零 |
| c | 特徴の決定性 | 二度で一致、backbone を変えると変わる | 両方の要約値を audit に |
| d | 表と対照の並置 | 10 × 2 の行、一周目の値が並ぶ | 行数 = 20（+P\*-21 分）。一周目の値の出所（run 名） |
| e | 選定が一意で test 不使用 | 1 組 | test 列を ±100 しても選定が変わらない（一周目の試験を再利用） |
| f | test は折りごとに一度 | 5 回（P\*-21 があれば 10） | 台帳の件数。二重評価で `FileExistsError` |
| g | S4 との並置 | 差が一周目より縮む | 差の値と一周目の 0.278 を並べる |
| h | 刻印と収穫 | 新実験が現れる | 収穫前後の行数の差 |
| i | PR | 番号、base phase0 | 分岐名 |

## 6. 想定外と停止条件

- 線形対照を下回る折りがある → 停止（fine-tune が壊れている）
- 特徴の要約値が一致しない → 停止
- 1 fine-tune が 1 時間超 → 諮る
- 追加 6 動画の画像が無い → P\*-21 は UNKNOWN。P\*-15 は続ける
- 画像は在るがフレーム数が注釈と合わない → その動画を使わず停止して諮る
- 装置が使われている → 停止
- PR #183 が未統合 → 分岐から取り寄せ、逸脱に書く

## 7. 報告の構成

`RESULT.md` は判断に使う事実だけ。目安百五十行以内。

| 節 | 内容 |
|---|---|
| 判定 | `verdict` と各 Gate |
| 完了判定 | 表。各項目に実測値 |
| 実測 | fine-tune の val accuracy と所要時間、特徴の表、確定 recipe、確定塔の 5 折り test、一周目との差、S4 との差、予測 5 項目 |
| 起票者の誤り | 型と内容。一件三行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、base、終了コード |

## 8. 申し送り

- 本契約は ilya の 2 枚を使う。efros の検出塔契約とは装置が別
- 一周目の確定塔は「凍結特徴の対照」として意味を持つ。捨てない
- fine-tune で S4 に届かなくても、それは結果である。届かない場合は backbone の種類（ViT、中立 SSL）が次の軸になる。本契約では足さない

# Stage 1: 工程塔 P\*-20 を二系統で確定し、工程塔の送り手の train と val の差を測る

**task_id:** T-2026-09-27-stage1-ptower-20  **kind:** exp

## 1. 背景

Stage 1 の 4 塔（D\*-COCO、D\*-ImageNet、P\*-COCO、P\*-ImageNet）は確定した（PR #195、#196）。残りは訓練データを増やした工程塔で、
M は P\*-21（15 動画 ＋ 追加 6 動画）を S1 の主分母と G1.5 の材料に置いている。追加動画 22 にフレーム画像が無いため、追加は 17〜21 の
5 本とし、**P\*-20** と呼ぶ（利用者の決定 2026-09-27、M v2.1）。

あわせて、交差適合（`conventions#crossfit`、閾値 3pt、利用者の決定 2026-09-27）を Stage 2 で工程塔の送り手にも適用するかを決めるため、
工程塔の train 動画と val 動画の予測の質の差を測る。

**本契約は GPU を使う**（利用者承認 2026-09-27）。装置は **efros の 2 枚**。三周目は ilya で回したので、必要なものは ilya から移す（§3 Task A）。

## 2. 確定した事実（ホストによらない値だけ）

- 三周目の確定値（PR #195）: P\*-COCO 5 折り平均 val 0.6558 / test 0.5176、P\*-ImageNet 0.4785 / 0.4095。recipe は prereg §2
- 三周目の道具: `scripts/train_phase_tower_r50.py`（収束規則、全画面短辺 800、勾配累積の引数）、`scripts/run_stage1_ptower.py`、`scripts/select_stage1_ptower.py`。phase0 に統合済み
- 三周目の fine-tune: 28 本で 81 GPU 時間（ilya の RTX 6000 Ada、物理 batch 16 × 累積 4）。efros での時間は未測
- COCO 系統の初期値: Relation-DETR の COCO 検出 checkpoint の R50 部分。要約値は三周目の RESULT に記録がある
- 追加動画 17〜21: 工程の注釈は在る。フレーム画像は利用者が用意する。動画 22 は注釈のみで除外
- 提案カード: `docs/proposals/2026-09-27-ptower-20.md`（T-2026-09-27-stage2-prep が配置）。**その PR が統合されていないと P14 で止まる**
- 交差適合の規則: `conventions#crossfit`（同上の契約が配置）
- 対話シェルは zsh。`git --no-pager`。`make` には読み込みを同じ命令に含める

## 3. Task

**コマンドは書かない。実装を読んで決めてよい。**

### Task A — 事前登録と、efros に揃っているものの確認

1. **最初に `prereg.md` を commit し、hash と時刻を `spec.yaml` に書く**
2. 作業ツリーの清浄、HEAD が phase0、装置の状態（`/proc/PID/exe` か引数の完全一致）。他利用者の処理・仮占有プロセスがあれば停止して諮る
3. **efros に次が揃っているかを一つずつ測る**。欠けているものがあれば、その一覧（何が・ilya のどこに在るはずか・大きさ）を出して**停止**する。利用者が ilya から移す
   - 15 動画の工程用フレーム（三周目と同じ置き場・命名・fps）と工程 manifest
   - 追加 17〜21 のフレームと注釈。動画 22 の注釈が在ってもフレームが無いことの確認
   - COCO 検出 checkpoint。R50 部分の要約値が三周目の記録と一致すること
   - torchvision の ImageNet-1K R50 の重み（要約値が三周目と一致すること）
   - 三周目の時間ヘッドの確定構成（RESULT §4 と選定の出力）
4. 装置の記憶領域を測り、物理 batch と勾配累積の組を決める（実効 64 を保つ）。決めた組を記録する
5. `conventions_rev` と `runindex_commit` を実測し占位を差し替える

### Task B — 追加 5 動画の manifest

1. 追加 17〜21 を各折りの train にだけ足した manifest を作る。val・test には入れない。動画 22 は使わない
2. 動画ごとのフレーム数と注釈のフレーム数が一致することを確かめる。一致しなければ停止
3. 集合差の照合: 各折りの train・val・test を規約の表と照合し、追加分だけが train に増えていること

### Task C — ホスト差の対照

1. P\*-15、COCO 系統、折り A、seed 42 を efros で一本（fine-tune → 特徴 → 時間ヘッド）
2. ilya の三周目の同じ run の val と比べる。差が折り A の seed 間 SD の 2 倍以内なら続行。超えたら停止して諮る
3. 所要時間を記録（efros での 1 本の目安になる）

### Task D — P\*-20 の学習

1. 2 系統 × 7（5 折り、折り A は 3 seed）の backbone fine-tune。三周目の確定 recipe（prereg §2）。最良 epoch は val
2. 特徴を抽出し（決定性の確認を一つの backbone で）、三周目の確定構成の時間ヘッドを学習
3. task_id を刻み、metrics.json に val 主指標と co-primary

### Task E — test、並置、送り手の train と val の差

1. 確定塔について折りごとに一度 test を評価（10 回）。台帳に記録
2. P\*-15（三周目）の同じ折りと並置した表
3. **送り手の train と val の差**: 4 塔（P\*-15 と P\*-20 の 2 系統）について、各折りの確定塔が train 動画に出す予測の macro Jaccard と frame accuracy、val 動画のそれ、差。
   GPU は推論だけ。`conventions#crossfit` の閾値 3pt と比べる
4. prereg §4 の予測 5 項目の当たり・外れ

### Task F — 検証と報告

1. L1、L2、L3（P13・P14 を含む）、`make forbidden-check`、`make spec-check TASK=T-2026-09-27-stage1-ptower-20`、試験、`make runindex`
2. 完了判定 a〜i を実測で埋める
3. `RESULT.md`、`result.yaml`（版 3）、`audit.md`、`tasks/inbox.d/`。表は `docs/stage1/` にも置く
4. commit、push、**PR の base は phase0**。分岐名 `feat/stage1-ptower-20`。`.sync-pause` を移動で解除

## 4. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。**

1. recipe を変えない（追加動画、出力先、物理 batch と累積の組を除く）。実効 batch は 64 を保つ
2. 追加動画を val・test に入れない。動画 22 を使わない
3. 選定・最良 epoch に test を使わない。test は確定塔について折りごとに一度
4. 検出塔の重み・特徴を P\* に使わない（COCO 検出 checkpoint の R50 部分を除く）
5. `data/splits/` を変えない。`context/conventions.md` に触れない
6. `context/auto/*` と `tasks/inbox.md` は、並行する契約（T-2026-09-27-stage2-prep）が統合済みなら実行者の手順書どおり再生成してよい。未統合なら再生成しない
7. 開始前から在る未追跡を消さない。他利用者の処理を止めない
8. 外部への送信は `make task-report` 以外の経路で行わない

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 追加動画は train のみ、22 は除外 | 集合差 0（追加分を除く） | 追加動画を一本 val に混ぜた manifest で照合が落ちる |
| b | recipe の一致 | 差分の表で 0 項目（許された差を除く） | config の一項目を変えた比較で差分 1 |
| c | ホスト差 | ilya との差と seed 間 SD | SD の出所（三周目の折り A 3 seed）を書く |
| d | 並置 | 2 系統 × 5 折り、折り A は 3 seed、P\*-15 と並ぶ | 行数 = 14 ＋ 対照 1 |
| e | 送り手の train と val の差 | 4 塔 × 5 折り、閾値との比較 | train の予測が送り手の学習に使った動画であることを manifest で示す |
| f | test | 10 回、台帳 | 評価ログの件数。二重評価で FileExistsError |
| g | 対称性とカード | P13・P14 が実行前に PASS | カードの経路を変えた一時契約で P14 が FAIL |
| h | 刻印と収穫 | task_id で照合して全 run | 行数の差は使わない |
| i | PR | 番号、base phase0 | 分岐名 |

## 6. 想定外と停止条件

- efros に必要なものが欠けている → 一覧を出して停止（利用者が ilya から移す）
- フレーム数と注釈の不一致 → 停止
- ホスト差が SD の 2 倍超 → 停止して諮る
- 1 本が 8 時間超、記憶領域超 → 諮る（解像度は下げない）
- 装置が使われている → 停止

## 7. 報告の構成

判定／完了判定／実測（ホスト差、P\*-20 と P\*-15 の表、送り手の train と val の差と閾値、所要時間、予測 5 項目）／起票者の誤り／逸脱／想定外／送出。

## 8. 申し送り

- 本契約は T-2026-09-27-stage2-prep の**統合後**に起動する（カードと `conventions#crossfit` が要る）
- 送り手の train と val の差の結果で、Stage 2 の P→D 側に交差適合を適用するかが決まる

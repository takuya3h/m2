# Stage 1: 検出塔 D\*-COCO と D\*-ImageNet を五折りで確定する

**task_id:** T-2026-09-18-stage1-detector-towers  **kind:** exp

## 1. 背景

Stage 1 は各タスクの最良塔を折りごとに確定する段。工程塔は `T-2026-09-18-stage1-phase-tower`（ilya）で進行中。
本契約は検出塔 2 種を担当する。M §5.2 が D\*-COCO と D\*-ImageNet の両方を要求しており（H3 の材料）、
トーナメントではなく**確定**である。処方は Stage 0 の凍結源を生んだものをそのまま使う。

副産物として、Tier 1 の試算で代理値だった「検出塔学習の所要時間」が実測になる。

**本契約は GPU を使う**（利用者承認 2026-09-18）。装置は efros の 2 枚。数値精度は **TF32**（利用者の決定 2026-09-18）。

## 2. 確定した事実（ホストによらない値だけ）

- 折り表は `conventions#folds`。折り A の test は公式 test、val は公式 val
- 凍結源は `conventions#frozen_source`（Relation-DETR seed 42 の `best_ap.pth`、sha256 03936318…、195,421,066 bytes）。
  **この重みを生んだ学習の処方を、記録（config、ログ、runindex の run 記録）から特定する。** 起票者は処方の全文を把握していない
- 分母参照は `baselines/s0/relationdetr_bbox@val`（3 seed、philip で学習）。折り A の D\*-COCO はこれと同じ処方の再学習に当たる
- TF32 の効き目: W1 で 1.18×、W2 で 1.29×（`docs/stage0/C2_amp_compile_timing.md`）。フル学習での倍率は未測。本契約で実測される
- `scripts/train_t1b.py` に `--tf32` が足された（PR #182。**統合済みであることを Task A で確かめる**。未統合なら分岐から取り寄せてよいが、
  その旨を逸脱に書く）。検出塔のフル学習の入口が `train_t1b.py` でない場合は、実装を読んで正しい入口を使い、報告に書く
- 検出の注釈は公式分割ごとの COCO 形式。折りごとの train・val・test を作るには注釈を動画単位で組み替える必要がある。
  **`data/splits/` の既存ファイルは変えない**
- `make task-start` は `origin/phase0` から分岐を切る。統合前の PR の中身は分岐に無い
- 前契約の教訓: preflight に `cuda_ext_loaded` と `gpu_free` を入れないと検査が SKIP になる。本契約は両方入れた
- 対話シェルは zsh。`git --no-pager`。`make` には読み込みを同じ命令に含める

## 3. Task

**コマンドは書かない。実装と記録を読んで決めてよい。** 出力は `audit.md` に残す。

### Task A — 事前登録の commit と開始状態

1. **最初に `prereg.md` を commit し、その hash と時刻を `spec.yaml` の `prereg.commit`・`prereg.committed_at` に書く。** L3 の P4 はこれを見る
2. 作業ツリーの清浄、HEAD が phase0、装置の状態（`/proc/PID/exe` の解決か引数の完全一致）。他利用者の処理があれば停止して諮る
3. `conventions#folds` を解決し、5 折りの動画集合を得る。折り A が公式分割の三ファイルと集合として一致することを確かめる
4. 凍結源を生んだ処方を特定する。config・epoch・batch・解像度・増強・最適化器・学習率・seed。**出所（ファイルと行、run 記録）を書く。**
   特定できない項目があれば UNKNOWN と書き、分母参照 `baselines/s0/relationdetr_bbox@val` の run 記録から補えるかを試みる。補えなければ停止して諮る
5. 折りごとの train・val・test の注釈ファイルを動画単位で生成する。各ファイルの画像集合を動画 ID に戻し、規約の表と集合差 0 を示す。
   **陰性対照**: 折り A の test 動画を一本入れ替えた注釈で差 1 になることを一度示す
6. `--tf32` が本分岐に在ることを確かめる。無ければ PR #182 の分岐から取り寄せ、逸脱に書く
7. `conventions_rev` と `runindex_commit` を実測し、占位を差し替える

### Task B — 再現の確認（D\*-COCO 折り A seed 42）

1. 特定した処方 + TF32 で 1 本回す。壁時計と GPU 時間、epoch ごとの val mAP を記録する
2. 凍結源の val mAP と比べる。prereg §5 の規則（1 以内 = 再現、3 以内 = 続行して記録、3 超 = 停止）
3. この 1 本の所要時間から、残り 13 run の見込みを出す。12 時間を超えるなら諮る

### Task C — 残り 13 run

1. D\*-COCO: 折り A seed 123・456、折り B〜E seed 42（6 run）
2. D\*-ImageNet: backbone を ImageNet-1K 初期化、検出ヘッド（transformer、query、予測ヘッド）は乱数初期化。**それ以外の処方は D\*-COCO と同一。**
   折り A 3 seed、折り B〜E 1 seed（7 run）
3. 2 枚で並行する。同時に走る run が互いの計時に影響しないよう、run ごとに使った GPU を記録する
4. 各 run に task_id を刻み（`config.yaml`）、metrics.json・per_class_ap.json を残す。学習中の非数・発散を監視し、出たら停止

### Task D — test と散らばり

1. 確定した両塔について、折りごとに一度だけ test を評価する（合計 10 回）。test アクセス台帳に記録し、回数を数える
2. 表を作る: 塔 × 折り × seed の val mAP・AP rare・test mAP。折り A の 3 seed の平均と SD、折り B〜E の折り間 SD
3. prereg §3 の予測 4 項目の当たり・外れを書く
4. 検出塔学習の所要時間（run ごとと平均）を `tools/estimate_tier_cost.py` の所要時間表に入れ、`measured` を True にし、`--check-doc` で差 0 を確かめる。
   日数を再計算して報告に書く（24h/日、全体、縮退なし）

### Task E — 検証と報告

1. L1、L2、`make forbidden-check`、`make spec-check TASK=T-2026-09-18-stage1-detector-towers`、試験、`make runindex` で新実験が現れること
2. 完了判定 a〜h を実測で埋める
3. `RESULT.md`、`result.yaml`（版 3）、`audit.md`、`tasks/inbox.d/T-2026-09-18-stage1-detector-towers.md`。T1 の材料になる表を RESULT に置く
4. commit、push、**PR の base は `phase0`**。分岐名 `feat/stage1-detector-towers`
5. 報告後に `.sync-pause` を移動で解除する

## 4. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。**

1. 凍結源の重みを変えない・上書きしない。新しい塔は別の場所に置く
2. `data/splits/` の既存ファイルを変えない。折りの集合は `conventions#folds` から作る
3. 処方を変えない（TF32 の有効化を除く）。D\*-ImageNet でも epoch・batch・学習率を変えない
4. 最良 epoch の選択・早期停止に test を使わない。test は両塔について折りごとに一度
5. `context/auto/*` と `tasks/inbox.md` を再生成しない（`taskindex-check`・`inbox-check` の exit 2 は想定どおり）
6. `runindex/**` を手編集しない（`make runindex` は可）。`context/conventions.md` に触れない
7. 既存の `tasks/*/` を変えない。開始前から在る未追跡を消さない
8. 他利用者の処理を止めない
9. 外部への送信は `make task-report` 以外の経路で行わない

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 処方の特定と差分 | 出所つきで全項目、差分 0（TF32 除く） | config の一項目を変えた比較で差分 1 が出る |
| b | 折り表に従う | 各 run の画像集合が動画集合と一致、集合差 0 | test 動画を一本入れ替えた注釈で差 1 |
| c | 折り A の再現 | 凍結源との差が記録、規則の判定 | 凍結源の値の出所（規約の記載と run 記録）を書く |
| d | 表 | 2 塔 × 5 折り、折り A は 3 seed | 行数 = 14。欠けは UNKNOWN |
| e | test は折りごとに一度 | 合計 10 回、台帳に記録 | test の評価ログを数え、10 を超えない。確定塔以外 0 件 |
| f | TF32 と所要時間 | 全 run の設定記録、壁時計と GPU 時間、計算器に実測 | `--check-doc` 差 0。`measured` が True |
| g | 刻印と収穫 | 新実験が現れる | 収穫前後の行数の差 = 新実験数 |
| h | PR | 番号、base phase0、Draft でない | 分岐名 `feat/stage1-detector-towers` |

## 6. 想定外と停止条件

- 処方が特定できない → 停止して諮る（推測で埋めない）
- 再現が 3 mAP 超で外れる → 停止し差分を提示
- ImageNet 初期化が発散 → 停止し記録を提示。**学習率を下げて再試行しない**（処方の変更になる。利用者が決める）
- 1 run が 12 時間超 → 諮る
- 装置が使われている → 停止
- `--tf32` が無い → 分岐から取り寄せ、逸脱に書く

## 7. 報告の構成

`RESULT.md` は判断に使う事実だけ。目安百五十行以内。

| 節 | 内容 |
|---|---|
| 判定 | `verdict` と各 Gate |
| 完了判定 | 表。各項目に実測値 |
| 実測 | 処方の特定結果、折り A の再現の差、2 塔 × 5 折りの表、折り間 SD と seed 間 SD、所要時間と再計算した日数、予測 4 項目の当たり外れ |
| 起票者の誤り | 型と内容。一件三行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、base、終了コード |

## 8. 申し送り

- 本契約は efros の 2 枚を使う。ilya の工程塔契約とは装置が別
- D\*-ImageNet が COCO より大きく劣っても、それは想定内（予測 2）であり失敗ではない。H3 の材料として両方が要る
- 所要時間の実測は Tier 1 の日数を動かす。倍率ではなく日で報告する

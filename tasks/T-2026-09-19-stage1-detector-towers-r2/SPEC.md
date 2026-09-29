# Stage 1 検出塔の二周目: 両塔を同じ収束基準で学習する

**task_id:** T-2026-09-19-stage1-detector-towers-r2  **kind:** exp

## 1. 背景

一周目（T-2026-09-18-stage1-detector-towers）の学習ログを読み、**D\*-ImageNet が 12 epoch で切れている**ことが分かった。
D\*-COCO は 5 本すべて頭打ち（最終 epoch の伸び +0.0004 前後）だが、D\*-ImageNet は最後も +0.0067 伸びている。
検出ヘッドが乱数初期化の塔に、COCO 事前学習済みの検出器用の短いスケジュール（12 epoch、10 で LR 落とし）を
当てていたためで、**同じ epoch 数は同じ学習量ではない**。

このまま H3（受け取り手の表現依存）の腕に使うと、Stage 2 の差が表現の差なのか学習不足なのか区別できない。
利用者の決定（2026-09-19）: 収束基準を両塔に同じく当てて学習し直す。

M §5.1 は 2026-09-18 に改訂され、「同一 epoch は同一の学習量を意味しない。収束の度合いを揃えることを優先し、
上限に張り付いた腕があれば上限を両腕で広げる」が入った。本契約はその最初の適用。

**版 2（2026-09-21 差し替え）**: 版 1 の「30 epoch で学習率を下げ、8 epoch 改善なしで打ち切り」は、早く収束する
COCO の塔が低下に届かない非対称を作る設計だった。「停滞で学習率を下げ、再停滞で止める」に替えた（prereg §1）。
あわせて入口・allow_write・長時間の停止基準・照合の方法を直した。

**本契約は GPU を使う**（利用者承認 2026-09-19）。装置は efros の 2 枚。

## 2. 確定した事実（ホストによらない値だけ）

- 一周目の実測（実行者が学習ログから確認、2026-09-19）:

| run | 最良 epoch（1 起点） | 最終 epoch の伸び | lr 低下後 2 epoch の伸び | epoch 0 |
|---|---|---|---|---|
| dcoco_foldA_seed42 | 12 | 約 +0.0004 | +0.0104 | 0.5729 |
| dcoco_foldA_seed123 | 11 | 頭打ち | +0.0163 | — |
| dcoco_foldA_seed456 | 12 | 頭打ち | +0.0254 | — |
| dcoco_foldB_seed42 | 12 | 頭打ち | +0.0112 | — |
| dcoco_foldC_seed42 | 11 | −0.0101（最良から離れる） | +0.0139 | — |
| dimagenet_foldA_seed42 | 12 | **+0.0067** | **+0.0319** | 0.3249 |

- 折り A の値: D\*-COCO 0.7244 / 0.7247 / 0.7209、D\*-ImageNet 0.6834。差 約 4.1 mAP
- 折り B〜E は折り A より 0.25〜0.29 低い（0.43〜0.53）。折りの難しさの違い
- 一周目の処方: `accelerate launch --num_processes 2 main.py`、12 epoch、`MultiStepLR([10], gamma=0.1)`、
  per-GPU batch 2 × 2 = 実効 4、AdamW lr 1e-4（wd 1e-4）、`max_norm 0.1`、presets.detr、短辺 480〜800、
  **fp16 autocast**、backbone は stem のみ凍結（`freeze_indices=(0,)`）。折りの注釈は
  `data/annotations/egosurgery_tool_folds/`（image_id・annotation_id を振り直し済み、追跡外）
- **学習の入口は `third_party/Relation-DETR/main.py`**（accelerate）。`scripts/train_t1b.py` は P→D 界面の学習器で別物。
  一周目が新設した `scripts/run_stage1_dtower.sh`・`stage1_dtower_queue.sh`・`eval_stage1_dtower.sh`・
  `write_stage1_dtower_evidence.py` と `third_party/Relation-DETR/configs/train_config_egosurgery_stage1_imagenet_seed*.py` を再利用する
- 一周目の実測: 1 run 平均 8.353 h（12 epoch）→ **0.70 h/epoch**。同時実行は 2 本が最適（3 本目は +1%）
- 一周目の成果物は `experiments/baselines/stage1_dtower/`（PR #191、2026-09-21 統合）。本分岐にあることを Task A で確かめる
- 本契約は `experiments/baselines/stage1_dtower_r2/` と `runindex/` を `allow_write` に宣言済み
- TensorBoard の val/mAP は float32 の原値。ログの `Average Precision` 行は 3 桁に丸められており、桁が要る比較に使えない
  （実行者の指摘）
- 対話シェルは zsh。`git --no-pager`。`make` には読み込みを同じ命令に含める

## 3. Task

**コマンドは書かない。実装を読んで決めてよい。** 出力は `audit.md` に残す。

### Task A — 事前登録と開始状態

1. **最初に `prereg.md` を commit し、hash と時刻を `spec.yaml` の `prereg.commit`・`prereg.committed_at` に書く**
2. 作業ツリーの清浄、HEAD が phase0、装置の状態（`/proc/PID/exe` か引数の完全一致）。他利用者の処理があれば停止
3. 一周目の成果物と曲線（TensorBoard の原値）を引き継げることを確かめる。並置の対象になる
4. **学習率の低下と打ち切りの実装**を `third_party/Relation-DETR/main.py` の学習ループに足す（無ければ）。仕様:
   - lr 1e-4 で開始。**val mAP が 4 epoch 続けて改善しなければ lr を 1/10 にする（一回だけ）**
   - 低下の後、**val mAP が 4 epoch 続けて改善しなければ打ち切る**
   - 上限 36 epoch。最良 epoch は val mAP で選ぶ
   - 既定は一周目と同じ（`MultiStepLR([10])`、打ち切りなし）にし、引数か config で有効化する。既定で一周目が再現することを試験で示す
   **両塔が同じ経路を通ることを実装の行で示す**（別々の分岐を通っていないこと。完了判定 a）
5. 折りごとの注釈が一周目のものを再利用できることを確かめる。画像集合を動画 ID に戻し規約の表と集合差 0。
   陰性対照（test 動画を一本入れ替えて対称差 2）を一度示す
6. `conventions_rev` と `runindex_commit` を実測し占位を差し替える

### Task B — ImageNet 初期化の一本目

1. D\*-ImageNet の折り A seed 42 を先に回す。**学習率の低下が起きるか、打ち切りが働くか、上限 36 に達するか**を見る
2. 壁時計と GPU 時間、epoch ごとの val mAP を記録。一周目の同じ run（0.6834）との差を出す
3. 最良 epoch が上限 36 なら停止して諮る（G2）。上限が結果を切っている
4. この 1 本の所要時間から残り 13 run の見込みを出す。1 run が 27 時間を超えるなら諮る

### Task C — 残り 13 run

1. D\*-ImageNet: 折り A seed 123・456、折り B〜E seed 42（6 run）
2. D\*-COCO: 折り A 3 seed、折り B〜E 1 seed（7 run）。**同じ規則（停滞で低下、再停滞で打ち切り）で回す**
3. 2 枚で並行。run ごとに使った GPU を記録
4. task_id を刻み、metrics.json・per_class_ap.json を残す。発散・非数があれば停止

### Task D — test と対照

1. 確定した両塔について、折りごとに一度だけ test を評価（合計 10 回）。台帳に記録し回数を数える
2. 表を作る: 塔 × 折り × seed の val mAP・標的群 AP・AP rare・test mAP、**学習率の低下 epoch・打ち切り epoch・最良 epoch**、
   そして**一周目の同じ折り・seed の値**
3. 一周目からの上がり幅を塔ごとに出す。両塔の差を一周目（4.1 mAP）と二周目で比べる
4. 最良 epoch が上限 36 に達した run の件数を塔ごとに記録
5. prereg §4 の予測 5 項目の当たり・外れ
6. 検出塔学習の所要時間を `tools/estimate_tier_cost.py` の所要時間表に入れ、`measured` を True にし、
   `--check-doc` で差 0。日数を再計算（24h/日、全体、縮退なし）

### Task E — 検証と報告

1. L1、L2、L3（**P13 の対称性表の検査を含む**）、`make forbidden-check`、`make spec-check TASK=T-2026-09-19-stage1-detector-towers-r2`、
   試験、`make runindex`
2. 完了判定 a〜j を実測で埋める
3. `RESULT.md`、`result.yaml`（版 3）、`audit.md`、`tasks/inbox.d/T-2026-09-19-stage1-detector-towers-r2.md`。T1 の材料の表
4. commit、push、**PR の base は phase0**。分岐名 `feat/stage1-detector-towers-r2`
5. 報告後に `.sync-pause` を移動で解除する

## 4. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。**

1. 凍結源の重みを変えない・上書きしない
2. `data/splits/` を変えない。折りの集合は `conventions#folds` から
3. **学習の長さと学習率の低下の決め方（上限 36、停滞 4 で 1/10、再停滞 4 で打ち切り）以外の処方を変えない。** 初期学習率・batch・増強・解像度・精度（fp16）は一周目と同一
4. 学習率の低下と打ち切りの規則を塔ごとに変えない
5. 最良 epoch の選択・打ち切りに test を使わない。test は両塔について折りごとに一度
6. 一周目の成果物（`experiments/baselines/stage1_dtower/`）を消さない・上書きしない。二周目は別の場所へ
7. `context/auto/*` と `tasks/inbox.md` を再生成しない
8. `runindex/**` を手編集しない（`make runindex` は可）。`context/conventions.md` に触れない
9. 既存の `tasks/*/` を変えない。開始前から在る未追跡を消さない
10. 他利用者の処理を止めない
11. 外部への送信は `make task-report` 以外の経路で行わない

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 低下と打ち切りが両塔で同一 | 実装の行。run ごとの低下 epoch・打ち切り epoch・最良 epoch | 塔ごとに分岐する経路が無いことを示す。停滞の epoch 数を変えた入力で低下の時期が変わることを一度示す |
| b | 折り表に従う | 集合差 0 | test 動画を一本入れ替えた注釈で対称差 2 |
| c | 表と一周目の並置 | 2 塔 × 5 折り、折り A は 3 seed、一周目の値が並ぶ | 行数 = 14。一周目の値の出所（run 名）を書く |
| d | 上がり幅と差の比較 | 塔ごとの上がり幅、差の一周目・二周目 | 差の計算に使った値の出所を書く |
| e | 上限に達した run | 塔ごとの件数。低下を受けずに上限へ達した件数も | 0 件でも 0 と書く。全件が上限なら停止した記録 |
| f | test は折りごとに一度 | 合計 10 回、台帳 | 評価ログの件数。確定塔以外 0 件 |
| g | 所要時間と計算器 | 壁時計・GPU 時間、`measured` True | `--check-doc` 差 0 |
| h | 対称性の表 | UNKNOWN 0 件 | L3 の P13 が PASS。表の行数を記録 |
| i | 刻印と収穫 | 本契約の全 run が現れる | task_id で照合して 14 件。行数の差は同期物や既存行の更新を含むので使わない |
| j | PR | 番号、base phase0 | 分岐名 |

## 6. 想定外と停止条件

- 全 run が上限 36 に達する → 停止して諮る（基準が緩い、または上限が足りない）
- ImageNet 初期化が発散 → 停止し記録を提示。学習率を下げて再試行しない
- 1 run が 27 時間超 → 諮る
- 装置が使われている → 停止
- 学習率の低下と打ち切りの実装を足すと既存の学習経路が変わる → 既定を一周目と同じにし、引数で有効化する形にする。
  既存の run が再現することを試験で示す

## 7. 報告の構成

`RESULT.md` は判断に使う事実だけ。目安百五十行以内。

| 節 | 内容 |
|---|---|
| 判定 | `verdict` と各 Gate |
| 完了判定 | 表。各項目に実測値 |
| 実測 | 2 塔 × 5 折りの表（val・標的群・rare・test）、低下・打ち切り・最良 epoch、一周目との並置と上がり幅、両塔の差の一周目・二周目、所要時間と再計算した日数、予測 5 項目 |
| 起票者の誤り | 型と内容。一件三行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、base、終了コード |

## 8. 申し送り

- 一周目の run は**捨てない**。12 epoch 版と収束版の対照として T1 の脚注か付録に残す
- 差が縮んでも零にならないなら、それが初期化源の効果量である。縮まないなら、一周目の差は学習不足で説明されていた
- 本契約は efros の 2 枚を使う。ilya の工程塔契約とは装置が別
- 所要時間は倍率ではなく日で報告する。Tier 1 の日数を動かす

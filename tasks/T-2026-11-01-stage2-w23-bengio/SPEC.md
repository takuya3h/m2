# Stage 2 の界面の型を W2・W3 で回す（非公式の予備測定）— bengio の分

**task_id:** T-2026-11-01-stage2-w23-bengio  **kind:** analysis  **ホスト:** bengio  **PR の base:** phase0  **分岐:** feat/stage2-w23-bengio

## 0. この契約の位置づけ

- **非公式の測定である。** 関門（Stage ごとに型や方向を落とすかを決める判定。M §5.2）の判定にも、設計の判断（型の採否を含む）にも使わない
- これまでの予備測定の界面の型は、すべて W1（受け取り手を凍結し、界面だけを学ぶ）で回した。本契約は同じ型を **W2（界面と受け取り手の後段を学ぶ）** と **W3（界面と受け取り手の全体を学ぶ）** で回す
- 利用者の決定（2026-11-01、起票の会話）:
  1. W2・W3 で回すのは、前回の Stage 2 の工程から検出の全型（P1、P2L、P3、decoder-xattn、extra-queries。学習の無い P2F を除く）、検出から工程の全型（D1-L1、D1-L2、D2、D3-L1、D3-L2、logit-correction、tool-history、そのゲートなし版）、把持の案 A・案 B
  2. 工程塔の W2 は時間ヘッドの最後の段、W3 は時間ヘッドの全体（特徴は今の保存のまま。CNN は学ばない）
  3. 設定はこれまでと同一（折り A、seed 42、4 epoch の固定の長さ、最後の状態、腕の定義、信号、処方）
  4. andrew と bengio に配分する。**一つの型の腕（W2 と W3 の両方）は一つのホストで回す**。配分は起票者が決めた（§4）
- 並行する契約: T-2026-11-01-stage2-w23-andrew（andrew）。**同じファイルを変えないために、本契約が変えてよい既存のファイルは §5 Task C-1 に挙げたものだけ**
- run・信号には、名前と notes に「非公式（本 task_id）」と分かる印を付ける

## 1. 背景

- W1 の正解の腕の差は小さかった（工程から検出の overall mAP で最大 +0.0093、検出から工程の Jaccard で最大 +0.006 前後）。界面だけを学ぶ経路の狭さが差を小さくしているかを、W2・W3 で見る
- W2・W3 では受け取り手も変わるので、**空の腕は塔単独と同じにならない**。比べるのは同じ型・同じ W の腕どうし。学習前（界面は零から始まる）は全腕で塔単独と一致する
- 受け取り手は train で学習済みなので、W3 で 4 epoch さらに学ぶと train に寄る方向に動きうる。空の腕との差で読む

## 2. 確定した事実（出所つき）

| 項目 | 値 | 出所 |
|---|---|---|
| 塔単独の val | 工程 macro Jaccard 0.7762186・frame accuracy 0.8712871、検出 overall mAP 0.7273450・標的群 AP 0.7950748・陰性対照群 AP 0.6726632 | `experiments/analysis/stage2_pilot_folda/REPORT.md` §2 |
| 再現の照合 | overall mAP と標的群 AP の差がともに 0.005 以内（overall だけでは別 seed の検出塔を見分けられない。標的群 AP の差は +0.028） | `tasks/T-2026-10-31-grasp-pilot-probe/RESULT.md` §5、`tasks/T-2026-11-01-grasp-pilot-d/RESULT.md` §1 |
| 工程から検出の W2・W3 | `train_t1b.py` の `--trainable w2`（界面 ＋ decoder の最終層とその層のクラスと box の頭。`pd_model.w2_parameter_names`）と `--trainable all`（界面 ＋ 設定の凍結以外の検出器の全体） | `scripts/train_t1b.py` の `set_trainable` |
| 工程から検出の処方 | 学習率 1e-4（受け取り手）・界面 5e-4、batch 2、`presets.detr`、学習は bf16 の自動混合精度・評価は単精度、`--fixed-epochs` | `scripts/grasppilot/run_pd_grasp.sh` の冒頭、`scripts/stage2pilot/run_pd_fix.sh` |
| 検出から工程の処方 | 学習率 5e-4、weight decay 0.01、平滑化 0.3、1 歩 = train の動画 1 本、単精度、時間ヘッドは eval（dropout なし）で使う、`--fixed-epochs` | `scripts/stage2pilot/dp_train.py`、`scripts/stage2pilot/dp_model.py` の docstring |
| 検出から工程の W2・W3 | 未実装（`dp_train.py` は界面だけを学ぶ） | `scripts/stage2pilot/dp_train.py` の `trainable_report` |
| 型ごとの腕と信号 | P1・P2L・P3 は `run_pd_fix.sh`、decoder-xattn・extra-queries は `run_pd_four.sh`、D1・D2・D3 は `run_dp_fix.sh`、logit-correction・tool-history は `run_dp_four.sh`、案 A は `dp_train.py` の `GA`、案 B は `run_pd_grasp.sh` と二本目の道具 | 各スクリプト、PR 240・243・272 と二本目の PR |
| W1 の値 | 型ごとの 4 epoch 目の値 | `experiments/analysis/stage2_pilot_fix/REPORT.md`、`stage2_pilot_four/REPORT.md`、`grasp_pilot_probe/REPORT.md`、二本目の `grasp_pilot_g/REPORT.md` |
| 1 本の所要（W1） | 工程から検出 1.9〜3.8 時間（1 枚に 2〜3 本）、検出から工程 19〜117 秒 | four-new-types と一本目の `RESULT.md` |
| bengio の Relation-DETR | bengio の main の `third_party/Relation-DETR` は andrew と違う。三本目は andrew と全 155 ファイル・パッケージ 72 個で一致する重ねの BODY を使い、bengio の main を変えなかった | `tasks/T-2026-11-01-grasp-pilot-d/RESULT.md` §1 の G1 |
| bengio での評価 | `scripts/eval_relation_detr_map.py` は自分の位置の `third_party/Relation-DETR` を引くので、bengio では main の違う中身で評価してしまう。三本目は重ねの BODY を指せる `scripts/stage2pilot/pd_eval.py` を使った | 同 §5 |
| bengio の装置 | RTX A6000 × 2、電力の上限 220 W | 同 §2 の a |

**ホスト固有の値は実測で決める。** 信号・checkpoint・重ねの BODY の在否と要約値は、他のホストの値を写さず本契約のホストで測る。

## 3. 定義

### 3.1 W2・W3 で学ぶ集合

| 受け取り手 | W2 | W3 |
|---|---|---|
| 検出塔（工程から検出、案 B） | 界面 ＋ `--trainable w2` の集合 | 界面 ＋ `--trainable all` の集合 |
| 工程塔の時間ヘッド（検出から工程、案 A） | 界面 ＋ 時間ヘッドの最後の段（`refine_stages` の最後の要素の全体） | 界面 ＋ 時間ヘッドの全体 |

- 受け取り手の学習率は §2 の処方の受け取り手の値（工程から検出は 1e-4、検出から工程は 5e-4）。界面の学習率と weight decay は W1 と同じ
- 時間ヘッドは W1 と同じく eval（dropout なし）で使う
- 界面の型が受け取り手の段の中に在る型（logit-correction、tool-history は最後の段、decoder-xattn は decoder の層）でも、上の表の集合をそのまま足す
- **学ぶパラメータの名前の集合を、型と W ごとに記録する**

### 3.2 腕と信号

- 腕の集合と信号は、**その型の W1 で回した腕と同じ**（W1 の run の記録から読む）。W2 と W3 で同じ腕を回す
- 入れ替えの腕は直しの契約の並べ替えをそのまま使う（新しく並べ替えない）
- 学習前の出力は全腕で塔単独と一致する（界面は零から始まる）

## 4. run の表（本契約の分）

| 方向 | 型 | W | 腕 | 本数 |
|---|---|---|---|---|
| 工程から検出 | extra-queries、P2L、P3 | W2・W3 | 各型の W1 の腕（§3.2） | 型ごとに W1 の腕の数 × 2 |
| 検出から工程 | D1-L1、D1-L2、D2、D3-L1、D3-L2、logit-correction、tool-history、tool-history のゲートなし版 | W2・W3 | 各型の W1 の腕 | 同 |
| 把持から工程（案 A） | D1 concat（`GA`） | W2・W3 | 空・正解（予測の四腕は Task D-3） | 4（12） |

- 工程から検出の P1・decoder-xattn と案 B は並行する andrew の契約が回す

- すべて seed 42、4 epoch の固定の長さ、最後の状態
- run の置き場は `experiments/phase1/w23b_` で始まる名前。大きな生成物は版管理と同期の外に置き、経路と要約値を残す
- 1 枚に載せる本数は記憶の確保で決め（W1 の実績は 1 枚 3 本まで）、記録する

## 5. Task

**コマンドは書かない。実装と記録を読んで決めてよい。** 命令と出力は `audit.md` に残す。

### Task A — 開始状態（G1）

1. 分岐が `feat/` で始まり、起点が `origin/phase0` であることと、起点の commit を記録する。一本目と三本目の内容（`scripts/grasppilot/`、`tasks/T-2026-11-01-grasp-pilot-d/`）が起点に在ることを確かめる。無ければ停止
2. 開始前から在る未追跡を消さない。一覧を記録する
3. bengio の compute プロセスを `/proc/PID/exe` の解決と引数の要素の完全一致で列挙する。本契約以外が一件でもあれば止めずに停止し、利用者に諮る
4. 記憶領域の空き、試験の失敗の名前の集合、既存の仮想環境のパッケージの一覧の要約値、GPU ごとの電力の上限と装置の型を記録する
5. `contract.conventions_rev` と `meta.created_from` を実測し、食い違えば差し替えて `meta.amendments` に記録する
6. `third_party/Relation-DETR` の中身と検出器の仮想環境が andrew と同じかを要約値で確かめる。違えば三本目の重ねの BODY（§2）を照合して使い、bengio の main を変えない。検出の評価は重ねの BODY を指せる経路で行う

### Task B — 材料と再現（G2）

1. §4 の型が使う信号（予測・正解・交差適合・入れ替え）と checkpoint が本ホストに在り、要約値が各契約の記録と一致することを確かめる。無ければ andrew から写して照合する（andrew では読むだけ）
2. 塔単独の val を本ホストで再現する（§4 の受け取り手について。検出塔は overall mAP と標的群 AP の差がともに 0.005 以内、工程塔は macro Jaccard の差が 0.005 以内）。超えれば停止

### Task C — W2・W3 の実装と恒等性（G3）

1. 実装: 検出から工程の W2・W3 を `scripts/stage2pilot/dp_train.py` に引数を足して実装する（**本契約で変えてよい既存のファイルはこれだけ**）。工程から検出の W2・W3 は既存の `--trainable w2`・`--trainable all` を使い、起動の台本は新しいファイル `scripts/w23/run_pd_w23_bengio.sh` に書く（W1 の台本の腕と信号の対応を写す）。
   **既存スクリプトの既定の挙動を変えない**（引数か新しいファイルを足す形）。`third_party/` を変えない
2. 学ぶパラメータの名前の集合を型と W ごとに記録し、§3.1 の集合と一致することを示す
3. 恒等性: 型と W ごとに全腕で、学習前の出力が塔単独と一致する。陽性対照として界面の重みを N(0, 0.05²) にすると出力が変わる
4. W1 の再現の確かめ: 新しい経路で W1 を指定すると、W1 の学ぶ集合と一致する（学習はしない）

### Task D — 学習

1. §4 のとおり回す。記録は W1 と同じ項目（4 epoch 目の値、動画ごと、クラス別、界面の重み、ゲートを持つ型のゲート、所要、`server.txt`、`code_sha256.txt`）に、epoch ごとの val の値を足す
2. 検出から工程の分（在れば）を先に回し、終わったら §6 の表の形で `experiments/analysis/stage2_w23_bengio/INTERIM.md` を書いて push する（PR は Draft で開いてよい）
3. 二本目 T-2026-11-01-grasp-pilot-g の PR が phase0 に統合されたら、phase0 を本分岐へ merge し（`dp_train.py` が衝突しうる。両方の変更を残し、W1 の既定の挙動が変わらないことを確かめ直す）、案 A の予測の四腕（予測-noCF・予測-CF・正解予測-CF・入れ替え）を W2・W3 で回す。信号は二本目の保存先（andrew）から写して照合する。本契約のほかの run が終わるまでに統合されなければ回さず、UNKNOWN と書く

### Task E — 集計・検証・報告

1. 完了判定（§8）を実測で埋める。L1 と L2、試験、仮想環境の一覧の要約値を Task A-4 と比べる
2. `make forbidden-check`（本 task_id つき）を回す。**並行する契約の未追跡のファイルが同期で届くと、本契約の操作によらず違反に数えられる**（三本目の起票者の誤り 3）。違反を本契約の経路とそれ以外に分けて記録し、本契約の経路の違反が 0 件であることを示す
3. `README.md` と `docs/experiment_log.md` に書く。どちらにも「非公式の測定」と明記する
4. `REPORT.md`、`RESULT.md`、`result.yaml`、`audit.md`、`tasks/inbox.d/T-2026-11-01-stage2-w23-bengio.md`
5. commit、push、PR と `make task-report`（§11）。抑止の解除は手順書の「8. 終える」に任せる

## 6. 事前登録（測る前に固定する）

### 6.1 量

- 型と W ごとに: Δ空（同じ型・同じ W の空の腕との差）、Δ入替（同じ型・同じ W の入れ替えの腕との差）、Δ塔（塔単独との差）
- 型ごとに W1・W2・W3 を並べた表（W1 は §2 の記録。ホストの列を付ける）
- 指標: 工程から検出と案 B は overall mAP、標的群 AP、陰性対照群 AP、AP50。検出から工程と案 A は macro Jaccard、frame accuracy、クラス別 Jaccard

### 6.2 読み方の規則（記述だけ）

1. seed は一つ。差は 1 本ずつの差として書く。陽性・陰性・有意などの語は使わない
2. W をまたぐ比べ（W2 の正解の Δ空 と W1 の正解の Δ空 など）は、同じ型の中でだけ行う。**ホストが違う W1 の値との比べは参考の表に置き、処置の差として読まない**
3. 空の腕の Δ塔 を必ず書く（受け取り手を学んだこと自体の動き）
4. Δ空 と Δ入替 の符号が食い違えば両方を書き、一つにまとめない
5. 結果は関門の判定と設計の判断に使わない（§0）

### 6.3 予測（記述のための事前の記録。外れても判定は変わらない）

1. 工程から検出の正解の腕の Δ空（overall mAP）は、型ごとに W3 が W1 より大きい型が過半を占める
2. W3 の空の腕の Δ塔（overall mAP）は負である（train に寄る）

### 6.4 既知の限界（報告に必ず書く）

- 折りは 1 つ、val は 2 動画、seed は 1 つ。工程は動画 09 が塔単独で上限に近い
- 受け取り手は train で学習済みで、W2・W3 は同じ train でさらに学ぶ
- 長さは固定の 4 epoch で、受け取り手を学ぶときの収束規則に従っていない（利用者の決定）
- 工程塔の W3 は時間ヘッドまでで、CNN は学ばない
- 型を二つのホストに配分したので、ホストをまたいで型どうしを並べるときはホストの差を含む
- 数値精度は前回の経路のまま（工程から検出は bf16 の自動混合精度）

## 7. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。** `contract.inject_verbatim` の `conventions#prohibitions` を原文のまま適用し、加えて次を守る。

1. **test の動画（04、05、07）のフレームを、学習・評価のどれにも通さない**
2. 前回までの予備測定と把持の契約の run の置き場・集計・`tasks/` の各契約のフォルダ・版管理の外の保存先に書き込まない（読むこと、写しを取ることだけ）。前回の道具の既定の出力先はそれぞれの契約の場所を指すので、本契約の出力先を渡して使う
3. 本契約の版管理の外の生成物は `/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/` に置く
4. 凍結源、既存の checkpoint、`data/raw`、`data/external`、注釈を変えない
5. `third_party/` と既存の仮想環境を変えない。§5 Task C-1 に挙げたもののほか、既存のファイルを変えない
6. `context/auto/*` と `tasks/inbox.md` を再生成しない。生成物を作り直す検査（context、inbox、taskindex の check）を回さない
7. **装置の他のプロセスを止めない。** 並行する契約のホストでは読むこと（写しを取ること）だけを行う
8. 本契約のホストの GPU 2 枚だけを使う。efros、ilya、dlsta に接続しない
9. 開始前から在る未追跡を消さない
10. 外部への送信は `make task-report` 以外の経路で行わない
11. 抑止の目印を手で置かない・手で外さない
12. run の表に無い run を足さない。並行する契約の型を回さない

## 8. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 分岐、起点、前提の統合、未追跡、compute プロセス、空き、失敗の名前、仮想環境の要約値、電力の上限 | プロセスの列挙が自分のシェルを 1 件として拾い、存在しない実行ファイルの経路で 0 件になる |
| b | 材料と再現 | 信号と checkpoint の要約値が記録と一致、塔単独の差が許容差の中 | 1 バイト変えた写しで照合が不一致になる。別 seed の検出塔で標的群 AP の差が 0.005 を超える |
| c | 実装 | 学ぶ集合が §3.1 と一致、W1 の指定で W1 の集合と一致、既定の挙動が不変 | 学ぶ集合の検査が、集合の外のパラメータを一つ混ぜた集合で不一致を出す |
| d | 恒等性 | 全腕で学習前が塔単独と一致 | 界面の重みを N(0, 0.05²) にすると出力が変わる |
| e | 学習 | §4 の本数が回り、型ごとのホストが一つ | 各 run の `server.txt` から型ごとのホストの集合を作ると要素が 1 つ。存在しない run の名前を数えると 0 件 |
| f | 記述 | §6 の表と読み方の規則 | 表の差を各 run の記録から計算し直すと一致する |
| g | test 不使用 | 通した動画の集合と {04, 05, 07} の共通が 0 件 | 集合に 04 を混ぜた入力で共通が 1 件になる |
| h | 書き込みと試験 | 禁止の場所の要約値が前後で一致、仮想環境の一覧が一致、失敗の名前が増えない、本契約の経路の違反 0 件 | 同じ道具が本契約の新しいファイルを変更として検出する |
| i | PR | 番号、base phase0、Draft でない | 分岐名が `feat/stage2-w23-bengio` |

## 9. 停止して諮る条件

- 本契約以外の compute プロセスがある（Task A-3）
- 前提の統合が無い（Task A-1）
- 信号か checkpoint が無く andrew からも写せない、要約値が記録と食い違う、塔単独の再現の差が許容差を超える（Task B）
- §3 の集合を、既存スクリプトの既定の挙動か `third_party/` を変えないと実装できない、または §5 Task C-1 に無い既存のファイルを変えないと実装できない
- 学習前の出力が塔単独と一致しない（Task C-3）
- 記憶領域が足りない
- 発散・非数が出た腕は、その腕を止めて記録し、諮る。ほかの腕は続けてよい
- 実行基盤が書き込み・移動・削除を拒む（回避せず、利用者に提示して許諾を得る）

停止のときも、それまでの実測を `RESULT.md` と `audit.md` に書き、PR と `make task-report` まで行う。

## 10. 報告の構成

**`RESULT.md` は起票者が判断に使う事実だけ。150 行以内。** 命令と出力は `audit.md` に置き、`RESULT.md` から行番号で指す。

| 節 | 内容 |
|---|---|
| 判定 | status と G1〜G3 の結果 |
| 完了判定 | §8 の表に実測値 |
| 実測 | 再現値、型と W ごとの正解の腕と予測-noCF の Δ空・Δ入替、空の腕の Δ塔、W1 との並べ（参考）、所要、電力の上限 |
| 起票者の誤り | 型と内容。一件 3 行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、`make task-report` の終了コード |

`REPORT.md`（`experiments/analysis/stage2_w23_bengio/`）には全値、動画ごと、クラス別、epoch ごとの val、学ぶ集合、§6.2 の記述、§6.3 の照合、§6.4 の限界を置く。冒頭に「非公式の測定。関門と設計の判断に使わない」と書く。

## 11. 送出

- PR の base は **phase0**。push は統合ではない。PR が Draft でなく存在する状態で終える
- `make task-report` で台帳へ返す

# 把持の信号の四案の予備測定（三本目）— 案 D：把持の状態を教師にした検出塔の学び直し（bengio）

**task_id:** T-2026-11-01-grasp-pilot-d  **kind:** analysis  **ホスト:** bengio  **PR の base:** phase0  **分岐:** feat/grasp-pilot-d

## 0. この契約の位置づけ

- **非公式の測定である。** 関門（Stage ごとに型や方向を落とすかを決める判定。M §5.2）の判定にも、設計の判断（案の採否を含む）にも使わない
- 一本目 T-2026-10-31-grasp-pilot-probe（PR 272）の続き。二本目 T-2026-11-01-grasp-pilot-g（andrew）と並行して走る。**二本目が把持塔 G を学び、案 D の教師の標的を作って渡す**
- 案 D: S2（学習時の教師。推論時に G を使わない）。検出塔と同じ構造・処方・長さに、正解の枠ごとの G の把持の状態を当てる補助損失だけを足す
- 利用者の決定（2026-10-31〜11-01、起票の会話）:
  1. 案 D は 3 腕（補助損失なし、G を教師、入れ替えた教師）。補助損失の重み 0.3、標的は 4 値（左手・右手・両手・なし）
  2. 入れ替えた教師は**同じフレームの枠の間**で標的を入れ替える（カードどおり）
  3. 長さは「記録と同じ学習率の予定で、回した epoch 数まで回し、最後の状態を使う」
  4. 案 D は bengio、案 C は andrew（二本目）。同じ案の 3 腕は同じホストで回す
  5. seed は 42 の一つ
- **提案カードは repo に無く、関門（批判会話と利用者の判定）を通っていない。** 案の定義は本書がすべて
- 本契約が作る run・重みは、名前と notes に「非公式（本 task_id）」と分かる印を付ける

## 1. 背景

- 一本目の測定（`experiments/analysis/grasp_pilot_probe/REPORT.md` §1）: 検出塔の decoder の最終層の特徴から正解の把持の状態を当てる val の balanced accuracy は 0.5534（正解のクラスだけ 0.4373）。
  握られている枠が誤りに占める割合（0.4563）は全枠に占める割合（0.4793）を上回らなかった
- 検出塔は RoI の層を持たない DETR 系なので、カードの「RoI 特徴」を **照合で正解の枠に対応づけた query の decoder の出力** と読む（一本目の SPEC §1）
- 把持の規律（依頼文 `docs/proposals/briefs/2026-10-31-grasp-signal-generation-brief.md` §3 の 1）: 把持の注釈そのものを検出塔の学習に入れない。教師は G の出力だけ

## 2. 確定した事実（出所つき）

| 項目 | 値 | 出所 |
|---|---|---|
| 検出塔の処方 | Relation-DETR R50、COCO 1x 初期化、`presets.detr`、2 GPU × batch 2、AdamW lr 1e-4 wd 1e-4、fp16、max_norm 0.1。上限 36、停滞 4 で学習率 × 0.1（epoch 9）、再停滞で打ち切り（epoch 14）。15 epoch（0〜14）回し、最良は 10 | 一本目の `audit.md` E-3（記録は `experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42`） |
| 1 本の所要 | 1 GPU で 3,088 秒/epoch、15 epoch で 12.9 時間（andrew、GPU を共有して測った）。記録は 2 GPU で 9 時間 58 分 | 同 E-3 の計測 |
| 塔単独の val | overall mAP 0.7273450、標的群 AP 0.7950748、陰性対照群 AP 0.6726632 | 一本目の `RESULT.md` §3 |
| 再現の照合 | overall mAP の許容差 0.005 は別 seed の検出塔（差 +0.0015）を見分けられない。標的群 AP の差は +0.028 で見分けられる | 一本目の `RESULT.md` §5 の 2 |
| 検出塔の checkpoint | `experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth`、sha256 は `scripts/stage2pilot/common.py` の `DET_SHA256` | `scripts/stage2pilot/common.py` |
| 照合の結果を取る場所 | `third_party/Relation-DETR/models/bricks/set_criterion.py:120-128`（`calculate_loss` で `self.matcher` が indices を返す） | 一本目の `audit.md` E-4 |
| decoder の出力を取る場所 | `third_party/Relation-DETR/models/bricks/relation_transformer.py:357`（`class_head[layer_idx](self.norm(query))` の入力）。学習時は denoising の query が主経路の 900 の前に連結され、hybrid の経路（`skip_relation=True`）は decoder をもう一度呼ぶ | 同 E-4 |
| 派生の作法 | `scripts/grasppilot/pd_grasp_model.py`、`scripts/stage2pilot/pd_model.py`（third_party を変えずに検出器の派生を `scripts/` に置く） | PR 272、PR 235 |
| COCO の重みの罠 | 既存の設定の既定は andrew の経路を指し、ファイルでなければ `main.py` は読み込みを飛ばして学習が進む。`scripts/eval_relation_detr_map.py` は `third_party/Relation-DETR` へ `chdir` するので checkpoint は絶対経路で渡す | `context/env-facts.md` の dlsta の項 |
| bengio の Relation-DETR | 2026-10-19 の実測で、bengio の main の `third_party/Relation-DETR` は andrew と 23 件違い、`.venv-relation-detr` の python のリンク先が無かった。そのときは andrew の中身を別の場所に置き「重ねの BODY」で参照させ、bengio の main を変えなかった | `tasks/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/handoff_bengio.md` §2・§6 |
| 二本目の目録 | 二本目が `experiments/analysis/grasp_pilot_g/targets/D_manifest.json` を分岐 `feat/grasp-pilot-g` に push する（train の枠ごとの 4 値の置き場・sha256・枠の数） | 二本目の SPEC Task D-6 |
| 標的の定義 | 正解の枠 b ごとに r_c(b) = Σ_{x∈b} P_c(x) ÷ b の画素数（c は 左手が扱う器具・右手・両手）、q(b) = （r_左, r_右, r_両手, 1 − Σ r_c）。train は交差適合の半分の G から | 一本目の SPEC §3.3、二本目の SPEC §3.3 |

**ホスト固有の値は実測で決める。** bengio の repo の位置、仮想環境、Relation-DETR の中身、重ねの BODY の在否と中身は、andrew の値を写さず bengio で測る。

## 3. 定義

### 3.1 3 腕の受け取り手と処方

- §2 の検出塔の処方で、COCO 1x の重みから学び直す。15 epoch 回し、記録と同じ epoch で学習率を下げ（記録のログを読んで位置を決める）、**最後の状態を使う**（最良の回を選ばない）
- **3 腕は同じコード・同じ設定で回す。** 補助損失なしの腕も補助の頭を置き、重みを 0 にする
- GPU の使い方: 合計の batch は記録と同じ 4 にする。起票者の推奨は、1 腕を GPU 1 枚・batch 2・勾配を 2 回ためる形（教師の 2 腕を同時に回せる）。
  実装が既定の挙動を変えずにためられなければ、1 腕を 2 枚で順に回す。どちらにしても 3 腕で同じにし、記録と違う点を逸脱として書く
- 学習の seed は 42

### 3.2 補助の頭と損失

- 主経路（denoising と hybrid を除く）の decoder の最終層の出力（256）のうち、最終層の照合で正解の枠に対応づいた query だけを使う
- 頭: 256 → 4 の線形。損失: 4 値の softmax と q(b) との交差エントロピーを、対応づいた枠で平均する。全損失 = 検出の損失 ＋ 0.3 × 補助損失（補助損失なしの腕は 0 ×）
- 推論の構造は今の検出塔と同じ（補助の頭は使わない）

### 3.3 入れ替えた教師

- train の各画像の中で、正解の枠の間で q を並べ替える（画像ごとに seed 42 から決まる固定の並べ替えを一度だけ作り、全 epoch で使う）
- 枠が一つの画像は変わらない。その画像の数と枠の数を記録する。元と同じ枠に戻った割合も記録する

## 4. run の表

| 腕 | 補助損失の重み | 標的 | 本数 | ホスト |
|---|---|---|---|---|
| 補助損失なし | 0 | — | 1 | bengio |
| G を教師 | 0.3 | q | 1 | bengio |
| 入れ替えた教師 | 0.3 | 並べ替えた q | 1 | bengio |

- 補助損失なしの腕は標的を要らないので、Task C の確認が済み次第始める
- run の置き場は `experiments/phase1/grasppilot3_` で始まる名前。大きな生成物（重み、標的の写し）は版管理と同期の外に置き、経路と要約値を残す

## 5. Task

**コマンドは書かない。実装と記録を読んで決めてよい。** 命令と出力は `audit.md` に残す。

### Task A — 開始状態（G1）

1. 分岐が `feat/` で始まり、起点が `origin/phase0` で、起点に PR 272 の内容（`scripts/grasppilot/`）が在ることを記録する
2. 開始前から在る未追跡を消さない。一覧を記録する
3. bengio の compute プロセスを `/proc/PID/exe` の解決と引数の要素の完全一致で列挙する。本契約以外が一件でもあれば止めずに停止し、利用者に諮る
4. 記憶領域の空き、試験の失敗の名前の集合、GPU ごとの電力の上限と装置の型を記録する
5. bengio の repo の位置、`third_party/Relation-DETR` の中身（未 commit の変更を含む）と検出器の仮想環境が andrew と同じかを要約値で確かめる。
   違えば、bengio の main を変えずに揃える（前例は §2 の重ねの BODY。在ればその中身を andrew と照合して使う）。揃えられなければ停止
6. COCO 1x の重みの在処と sha256 を記録する
7. 既存の仮想環境のパッケージの一覧の要約値を記録する（Task E で比べる）
8. `contract.conventions_rev` と `meta.created_from` を実測し、食い違えば差し替えて `meta.amendments` に記録する

### Task B — 再現と処方（G2）

1. 検出塔の checkpoint の sha256 を照合し、塔単独の val を bengio で再現する（overall mAP、標的群 AP、陰性対照群 AP）。**overall mAP と標的群 AP の差がともに 0.005 以内**。超えれば停止
2. 記録のログから、学習率を下げた epoch、回した epoch 数、GPU 数と batch、選んだ epoch を読み、§2 の値と照らして記録する

### Task C — 補助の頭と、補助損失なしの腕（G3）

1. §3.2 の頭と損失を、既定の挙動と `third_party/` を変えない派生の形で足す（照合の indices と decoder の出力は前向きのフックか派生で取る。主経路だけを取る）
2. 確かめ（数歩の試走で。腕に数えない）:
   - 重み 0 で、全損失が頭の無い経路の損失と一致する
   - 重みを正にすると補助損失が全損失に入り、頭のパラメータに勾配が届く
   - 対応づいた枠の数が、その batch の正解の枠の数と一致する（主経路だけを取れている）
   - COCO の重みを読んだことを、読み込みの記録と、読む前と後のパラメータの要約値の違いで示す
   - 試走の標的には一本目の正解の q（一本目の保存先 `/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe/` を andrew から写したもの）を使ってよい
3. 補助損失なしの腕を回し始める。epoch ごとの検出の損失・補助損失（0 を確かめる）・学習率・val の値を記録する

### Task D — 標的の受け取りと、教師の 2 腕

1. 二本目の分岐 `feat/grasp-pilot-g` に目録（§2）が現れるのを待つ（`git fetch` で確かめる。間隔は任せる）。現れたら andrew から標的を写し、sha256 と枠の数を目録と照合する。食い違えば停止
2. 標的の枠と、train の正解の枠の対応を確かめる（画像と枠の数が一致し、対応の取れない枠が 0）。q の 4 値の和が 1 であることを確かめる
3. §3.3 の入れ替えた標的を作る
4. G を教師と入れ替えた教師の 2 腕を回す（Task C-3 と同じ設定）。同じ項目を記録する
5. 待つあいだに補助損失なしの腕が終われば、その時点までの記録を `experiments/analysis/grasp_pilot_d/INTERIM.md` に書いて push してよい

### Task E — 集計・検証・報告

1. 完了判定（§8）を実測で埋める。`make forbidden-check`（本 task_id つき）、L1 と L2、試験、仮想環境の一覧の要約値を Task A-7 と比べる
2. `README.md` と `docs/experiment_log.md` に書く。どちらにも「非公式の測定」と明記する
3. `REPORT.md`、`RESULT.md`、`result.yaml`、`audit.md`、`tasks/inbox.d/T-2026-11-01-grasp-pilot-d.md`
4. commit、push、PR と `make task-report`（§11）。抑止の解除は手順書の「8. 終える」に任せる

## 6. 事前登録（測る前に固定する）

### 6.1 量

- Δ教師 = G を教師 − 補助損失なし、Δ入替 = 入れ替えた教師 − 補助損失なし、G を教師 − 入れ替えた教師
- 指標: overall mAP（主）、標的群 AP（併記）、陰性対照群 AP、クラス別 AP、動画ごとの overall mAP
- 補助損失の推移（train）と、学習の最後の補助の頭の train の当たり具合

### 6.2 読み方の規則（記述だけ）

1. seed は一つ。差は 1 本ずつの差として書く。陽性・陰性・有意などの語は使わない
2. G を教師 − 補助損失なし と G を教師 − 入れ替えた教師 の両方を書く。符号が食い違えば両方を書き、一つにまとめない
3. overall mAP と標的群 AP と陰性対照群 AP を並べる。陰性対照群 AP が動いたときは書く
4. 補助損失なしの腕と記録の検出塔の値の差は、ホストと止め方（記録は最良の回）の違いを含むので、処置の差として読まない
5. 結果は関門の判定と設計の判断に使わない（§0）

### 6.3 予測（記述のための事前の記録。外れても判定は変わらない）

1. G を教師 − 補助損失なし の overall mAP の絶対値は 0.01 未満
2. 入れ替えた教師の腕の補助損失は、G を教師の腕より最後の epoch で大きい

### 6.4 既知の限界（報告に必ず書く）

- 折りは 1 つ、val は 2 動画、seed は 1 つ
- ホストは bengio で、記録の検出塔（ホストは記録に無い）と二本目の案 A・B・C（andrew）と違う。ホストをまたいで値を並べるときは処置の差として読まない
- GPU の使い方が記録（2 GPU）と違うときは、合計の batch を揃えても勾配の正規化が同じとは限らない
- 標的は交差適合の半分の G から作る。G の質は二本目の報告に従う
- 一本目の測定で、握られている枠は誤りに多く含まれていなかった
- カードは repo に無く、関門を通っていない

## 7. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。** `contract.inject_verbatim` の `conventions#prohibitions` を原文のまま適用し、加えて次を守る。

1. **test の動画（04、05、07）のフレームを学習と評価のどれにも通さない**
2. bengio の main の `third_party/` と作業場所の分岐・ファイルを変えない（揃えが要るときは §2 の重ねの BODY の形）
3. 前回までの予備測定・一本目・二本目の run の置き場、集計、`tasks/` の各契約のフォルダ、版管理の外の保存先（andrew と bengio の両方）に書き込まない。読むこと（写しを取ること）だけを行う
4. 本契約の版管理の外の生成物は bengio の `/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d/` に置く
5. 凍結源、既存の checkpoint、`data/raw`、`data/external`、注釈を変えない
6. 既存の仮想環境と既存スクリプトの既定の挙動を変えない
7. `context/auto/*` と `tasks/inbox.md` を再生成しない。生成物を作り直す検査（context、inbox、taskindex の check）を回さない。`forbidden-check` は回す
8. **装置の他のプロセスを止めない。** andrew では読むこと（写しを取ること）だけを行い、andrew のプロセスと二本目の run に触れない
9. bengio の GPU 2 枚だけを使う。efros、ilya、dlsta に接続しない
10. 開始前から在る未追跡を消さない
11. 外部への送信は `make task-report` 以外の経路で行わない
12. 抑止の目印を手で置かない・手で外さない
13. run の表に無い run を足さない（Task C-2 の試走は腕でなく、名前で区別する）
14. 把持の注釈を検出塔の学習データに入れない。教師は二本目の G の出力だけ（試走だけ一本目の正解の q を使ってよい）

## 8. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 分岐、起点、未追跡、compute プロセス、空き、失敗の名前、Relation-DETR と仮想環境の照合、COCO の重み、電力の上限 | プロセスの列挙が自分のシェルを 1 件として拾い、存在しない実行ファイルの経路で 0 件になる。中身の照合が、1 ファイルを変えた写しで不一致を出す |
| b | 再現と処方 | overall mAP と標的群 AP の差が 0.005 以内、記録から読んだ処方 | 別 seed の検出塔で同じ評価をすると標的群 AP の差が 0.005 を超える |
| c | 補助の頭 | 重み 0 で損失が一致、正で入る、主経路だけ、COCO の重みを読んだ | 重み 0.3 の試走で全損失 − 検出の損失 が 0 でない。COCO の重みの経路を存在しない経路にすると読み込みの記録が無くなる |
| d | 標的 | sha256 一致、枠の対応、入れ替え | 照合が、1 バイト変えた写しで不一致を出す。入れ替えの検査が、恒等の並べ替えで「元と同じ枠に戻った割合 1」を返す |
| e | 3 腕 | 同じ設定、記録の処方、epoch ごとの記録 | 3 腕の設定の差分（`config` と起動の引数）を取ると、補助損失の重みと標的の経路だけが違う |
| f | 記述 | §6 の表と読み方の規則 | 表の差を各 run の記録から計算し直すと一致する |
| g | test 不使用 | 通した動画の集合と {04, 05, 07} の共通が 0 件 | 集合に 04 を混ぜた入力で共通が 1 件になる |
| h | 書き込みと試験 | 禁止の場所の要約値が前後で一致、仮想環境の一覧の要約値が一致、失敗の名前の集合が増えない | 同じ道具が本契約の新しいファイルを変更として検出する |
| i | PR | 番号、base phase0、Draft でない | 分岐名が `feat/grasp-pilot-d` |

## 9. 停止して諮る条件

- bengio に本契約以外の compute プロセスがある（Task A-3）
- Relation-DETR の中身か仮想環境が andrew と違い、bengio の main を変えずに揃えられない（Task A-5）
- COCO の重みが無い、または読まれない（Task A-6、Task C-2）
- 塔単独の再現の差が許容差を超える（Task B-1）
- 補助の頭を、既存スクリプトの既定の挙動か `third_party/` を変えないと実装できない
- 3 腕を同じ設定で回せない
- 二本目の標的の sha256 が目録と一致しない（Task D-1）
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
| 実測 | 再現値、処方、GPU の使い方、電力の上限、3 腕の val の値と差、補助損失の推移、所要 |
| 起票者の誤り | 型と内容。一件 3 行以内 |
| 逸脱 | 何をなぜ（記録の処方との違いを含む） |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、`make task-report` の終了コード |

`REPORT.md`（`experiments/analysis/grasp_pilot_d/`）には、全値、動画ごと、クラス別、epoch ごとの記録、§6.2 の読み方による記述、§6.3 の予測との照合、§6.4 の限界を置く。
冒頭に「非公式の測定。関門と設計の判断に使わない」と書く。

## 11. 送出

- PR の base は **phase0**。push は統合ではない。PR が Draft でなく存在する状態で終える
- `make task-report` で台帳へ返す

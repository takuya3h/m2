# 収束規則の run の途中の epoch の値を取り出し、固定の長さの T→P とグラフの型と並べる — 記録の分析（GPU を使わない）

**task_id:** T-2026-11-22-conv-epoch-history-extract  **kind:** analysis  **ホスト:** andrew（repo は ~/slocal2/m2。context/env-facts.md の「repo の位置」）  **PR の base:** phase0  **分岐:** feat/conv-epoch-history-extract

## 0. この契約の位置づけ

- **非公式の分析である。** 関門（Stage ごとに型や方向を落とすかを決める判定。M §5.2）の判定にも、設計の判断（案の採否を含む）にも使わない
- **本契約では GPU を使用しない。学習・評価・推論のどれも行わない。** 読むのは前回までの三つの契約の run の記録だけ
- 利用者の決定（2026-11-21〜22、起票の会話）: 収束規則で回した run の epoch ごとの val の記録から途中の epoch の値を取り出し、4 epoch 固定で回した run と並べる。回し直しはしない
- 三つの契約（以下、識別子の末尾の slug で呼ぶ）
  - **graph-pilot**: T-2026-11-20-grasp-hand-graph-pilot。グラフの型（GR）を収束規則で回した
  - **irn-hice-htt-pilot**: T-2026-11-21-grasp-hand-irn-hice-htt-pilot。型 IRN・HiCE・HTT を収束規則で回した
  - **graph-t2p-match**: T-2026-11-21-grasp-hand-graph-t2p-match。グラフの型と T→P（検出塔から工程塔へ渡す型 D1-L1・D1-L2・D2・D3-L2）を、4 epoch 固定（8・12・16 epoch は副次）で回した
- 用語
  - **W1・W2・W3**: 学習範囲。W1 は interface だけ、W2 は W1 に工程塔の時間ヘッドの最終段を足す、W3 は W1 に時間ヘッド全体を足す（graph-pilot の SPEC §0）
  - **収束規則**: val の 7 工程の Jaccard が 8 epoch 改善しなければ学習率を 0.1 倍に一度、再び 8 epoch 改善しなければ打ち切る。上限 120、改善の幅 1e-4。7 工程の Jaccard が最良の回を結果にする（`scripts/stage2pilot/dp_train.py` の CONVERGE と学習の繰り返し）
  - **7 工程の Jaccard**: val に現れる 7 工程の Jaccard の平均。記録の `phase_jaccard`・`val_jaccard`。**6 工程**はそこから dressing を除いた平均
  - **腕**: 空（A0）、D、DG、DH、DGH、DGH-U、DGH-noCF、DGH-GT（graph-pilot の SPEC §5 と irn-hice-htt-pilot の SPEC §5.1）。graph-t2p-match の腕は名前の末尾に -noCF・-CF・-S（入れ替え）が付く
- `meta.created_from` と `contract.conventions_rev` は、起票者が phase0 の 6953d6e4 の写しで測った値。起点が違えば実行者が測り直し、違えば差し替えて `meta.amendments` に記録する
- `inputs.data.split_files` は様式を通すための値で、本契約は参照しない。報告に「参照しなかった」と書く

## 1. 前提

### 1.1 起票者が phase0（6953d6e4）の写しで測ったこと

- graph-pilot の腕の run は 96 本、irn-hice-htt-pilot は腕 243 本と確かめ 5 本の 248 本（`experiments/phase1/` の下の各 run の記録）。graph-t2p-match のグラフの型の run は 147 本、T→P は 36 本
- 収束規則の run の版管理の中の記録は `metrics.json`（結果の回）と `metrics_last.json`（最後の回）だけで、epoch ごとの値は無い
- epoch ごとの記録は、各 run の `logs/history.json` に `dp_train.py` が書く（epoch ごとに train の損失、val の 7 工程の Jaccard、val の frame accuracy、学習率、改善の有無）。`experiments/**/logs/**` は `.gitignore` で版管理の外なので、記録は andrew の作業ツリーにだけ在るはず（起票者は andrew を見られず、在るかを測っていない）
- **epoch ごとに残るのは 7 工程の Jaccard と frame accuracy だけ。** 6 工程・工程別・動画ごとの値と確率は無い（W&B の offline の記録も `val/jaccard` と `val/accuracy` だけ。`dp_train.py` の `tracking.log`）
- 収束規則の run の `metrics.json` の `lr_drop_epoch` の最小は 9（三つの集合とも）、`epochs_run` の最小は 17。どの run も 16 epoch 目まで回っている
- 学習率を下げるのは、最良の回から 8 epoch 改善が無かった epoch の評価の後。最も早くて 9 epoch 目の後なので、**1〜8 epoch 目は学習率を下げる前**（`dp_train.py` の ConvergeRule と学習の繰り返し）
- graph-t2p-match の固定の長さの run は、`metrics_ep4.json`・`metrics_ep8.json`・`metrics_ep12.json`・`metrics_ep16.json` に 7 工程の Jaccard、frame accuracy、工程別、動画ごとを持つ（版管理の中）
- 対になる組（同じ型・W・N・L・同じ信号の腕）: graph-pilot の A0・D・DG・DH・DGH・DGH-U は graph-t2p-match の empty・D-CF・DG-CF・DH-CF・DGH-CF・DGH-U-CF に、graph-pilot の DGH-noCF・DGH-GT は graph-t2p-match の同名の腕に当たる見込み。graph-t2p-match は辺の無い腕の s2・s4 と空の腕の s2〜s4 を回していない（graph-t2p-match の RESULT §5）。起票者の数えでは、対は最大 72 組
- graph-t2p-match の RESULT §3 によれば、固定の長さの経路と収束規則の経路の学習の設定は長さの規則のほかは同じ（interface の学習率 5e-4・weight decay 0.01、W2・W3 の受け取り手 5e-4・0.01、AdamW の別の群）

### 1.2 確かめていない前提

- 収束規則の run の 1〜8 epoch 目が、同じ組の固定の長さの run の 1〜8 epoch 目と同じ値になるか。学習の繰り返しの式は同じだが、引数の違い（`--converge` と `--fixed-epochs`・`--record-epochs`）で乱数の消費や評価の順が変わる可能性がある。本契約の問いそのもの（完了判定 e）
- `logs/history.json` が andrew に全 run 分残っているか（Syncthing や片付けで消えていないか）
- irn-hice-htt-pilot の SPEC §0 は収束規則の判定の指標を「6 工程の Jaccard」と書いたが、実装は 7 工程の Jaccard で判定している（`dp_train.py` の学習の繰り返しの `score = val["phase_jaccard"]`）。irn-hice-htt-pilot の結果の回は 7 工程で選ばれている（起票者の誤り。本契約で記録を読むときの注意）

## 2. 禁止と申し送り

- 注入される規約の節（prohibitions・issuer_cautions・env_p0・folds・symmetry）に従う
- 禁止は実行者の操作に対するものである。Syncthing による他の台への配布（本契約の出力が bengio に届くこと、他の契約の出力が届くこと）を含まない
- **本契約では GPU を使用しない。** 学習・評価・推論・checkpoint の読み込みによる再評価をしない。表を作るのにそれが要ると分かったら、止めて利用者に尋ねる
- 読む記録（各 run の `logs/` と版管理の中の記録、保存先 `/home/ubuntu/slocal2/stage2pilot_store` の中身）は読むだけにする。移動・書き換え・削除をしない。`logs/` を版管理へ写さない（版管理へ置くのは、本契約の道具が記録から作った表と目録だけ）
- 本契約の出力は allow_write の `experiments/analysis/conv_epoch_history_extract/` の下にだけ書く
- runindex と context/auto の生成物は作り直さない。`*-check` は回さない（`make forbidden-check` は回す）
- 6 工程の値は作らない（記録に無い）。工程別・動画ごとの値が要る差も作らない。無いものは「記録に無い」と書く

## 3. 読む集合

- **収束規則の run（収束規則の集合）**: `experiments/phase1/` の下で、graph-pilot と irn-hice-htt-pilot が自分の識別子で作った腕と確かめの run のうち、`metrics.json` に `converge` を持つもの。graph-pilot の RESULT §1 と irn-hice-htt-pilot の RESULT §1 の本数（96 本と 248 本）と一致することを示す。名前の一部だけで集めず、各 run の `metrics.json` と `config.yaml` の task_id で集合を作る
- **固定の長さの run（固定の長さの集合）**: graph-t2p-match が自分の識別子で作った、グラフの型と T→P の run のうち `metrics_ep4.json` を持つもの。graph-t2p-match の RESULT §1 の本数（グラフの型 147 本、T→P 36 本）と一致することを示す
- **対**: 収束規則の集合の graph-pilot の run と固定の長さの集合のグラフの型の run のうち、型・W・N・L・腕の信号（予測-CF・予測-noCF・正解・空）が同じもの。対の判定は各 run の `config.yaml` を比べて行い、長さの規則（`--converge` と `--fixed-epochs` など）の欄のほかに違いが無いことを記録する。名前の対応表だけで対を作らない

## 4. 取り出す値と印

- 収束規則の集合の全 run について、全 epoch の val の 7 工程の Jaccard、frame accuracy、学習率、改善の有無を一つの表にする（`epochs.csv`）。各行に、その epoch が学習率を下げる前か後かの印を付ける
- 印の根拠は `history.json` の学習率の欄と `metrics.json` の `lr_drop_epoch`。両者が食い違えば止める
- 4・8・12・16 epoch 目の値を表の主にする。12・16 epoch 目は、学習率を下げた後の run に印を付け、固定の長さの run と同じ学び方ではないと書く
- irn-hice-htt-pilot が流用した組み合わせ（A0 の s2〜s4 に s1、HiCE の D に HiCE の A0、HiCE の DH の s3・s4 に s1・s2。irn-hice-htt-pilot の SPEC §5.2 と RESULT §3）は同じ流用をする。流用の根拠になった確かめの run の 4・8・12・16 epoch 目の一致も記録する（完了判定 g）

## 5. 表（REPORT.md。記録から道具で作る。手で写さない）

### 5.1 一致の確かめ（主）

- 対ごとに、4・8 epoch 目の 7 工程の Jaccard と frame accuracy の差（収束規則の集合の値 − 固定の長さの集合の値）、値がちょうど同じ対の数、差の絶対値の最大を W・腕ごとに出す
- 12・16 epoch 目も同じ形で出す。学習率を下げた後の収束規則の集合の run は別に数える

### 5.2 腕の値

- 収束規則の集合の graph-pilot と irn-hice-htt-pilot の型（GR・IRN・HiCE・HTT）について、4・8・12・16 epoch 目の 7 工程の Jaccard / frame accuracy を、W・設定・腕ごとに並べる

### 5.3 同じ型の中の差

- irn-hice-htt-pilot の SPEC §7 と同じ 8 種の差（DGH − A0、D − A0、DG − D、DH − D、DGH − DG、DGH − DGH-U、DGH − DGH-noCF、DGH-GT − A0）を、4 つの型 × 4 設定 × 3 W × 4・8・12・16 epoch 目で、7 工程の Jaccard と frame accuracy について出す

### 5.4 型と方向の並べ

- 同じ W・同じ epoch（4・8・12・16）で、次を一つの表に並べる。7 工程の Jaccard と frame accuracy
  - 収束規則の集合の GR・IRN・HiCE・HTT: DGH − A0（予測-CF）、DGH-noCF − A0、DGH-GT − A0（4 設定の値）
  - 固定の長さの集合のグラフの型: DGH-CF − 空、DGH-noCF − 空、DGH-GT − 空（4 設定の値。graph-t2p-match の流用のとおり）
  - 固定の長さの集合の T→P の 4 型: 予測-noCF − 空、予測-noCF − 入れ替え
- 送り手が違う（T→P は検出塔だけ、ほかは検出塔・把持塔 G3・手の塔 H4）ことを表の上に書く
- 値はそのまま並べる。型の間で最良を選ばない。順位を書かない

### 5.5 読み方

- 差には ±0.015 を並べて書き、この幅の中の差は「読めない」と書く。±0.015 は工程塔側の予備で 6 工程の平均について測った幅（T-2026-11-09-grasp-pilot-converge の RESULT §3）で、7 工程と frame accuracy の幅は測っていない。目安として流用したと書く
- 一致の確かめ（§5.1）で一致しなかった対があれば、その W・腕の収束規則の集合の値を固定の長さの集合と同じ学び方の値として読まない。表は作り、印を付ける
- 採否・順位・解釈は書かない。差を並べるだけ

### 5.6 予測（結果を見る前に書く。当たり外れを報告する）

1. §3 の全対で、4・8 epoch 目の 7 工程の Jaccard と frame accuracy が一致する（値がちょうど同じ）
2. 4 epoch 目の W1 で、IRN・HiCE・HTT の DGH − A0 の 7 工程の Jaccard は、4 設定とも ±0.015 の中

## 6. 対称性の表（conventions#symmetry の様式。腕1 = 収束規則の集合のある run の途中の epoch、腕2 = 対になる固定の長さの集合の run の同じ epoch）

| 条件 | 腕1 | 腕2 | 判定 | 理由 |
|---|---|---|---|---|
| 初期化: ImageNet 分類 | graph-pilot の SPEC §5.1 の表の塔の重み | 同じ塔 | 揃える | 同じ凍結した塔と信号 |
| 初期化: COCO 検出 | 同上 | 同じ | 揃える | 同上 |
| 初期化: 中立 SSL | 使わない | 使わない | 揃える | |
| 初期化: in-domain の教師 | Fold A の train の注釈と工程ラベル | 同じ | 揃える | |
| 凍結範囲 | W1・W2・W3 の各水準 | 同じ水準 | 揃える | 対は同じ W で作る |
| 入力解像度と切り出し | 工程塔の特徴のキャッシュと graph-pilot の信号 | 同じ（graph-t2p-match の RESULT §2 の b で hash が一致） | 揃える | |
| 前処理・増強 | `dp_train.py` の既定 | 同じ | 揃える | |
| 教師の種類と密度 | Fold A の train の工程ラベル | 同じ | 揃える | |
| epoch と上限への張り付き | 収束規則の run の途中の epoch（学習率を下げる前） | 固定の長さの run の同じ epoch | 揃える | 学習率を下げるまでは同じ学び方のはず。完了判定 e で確かめる |
| 学習率 | interface 5e-4・wd 0.01、W2・W3 の受け取り手 5e-4・wd 0.01 | 同じ | 揃える | graph-t2p-match の RESULT §3 |
| 実効 batch | 1 歩 = train の動画 1 本 | 同じ | 揃える | graph-t2p-match の RESULT §3 |
| 数値精度 | `dp_train.py` の既定 | 同じ | 揃える | |
| ヘッドの容量（interface の大きさ） | 型と設定で決まる大きさ | 同じ型・同じ設定 | 揃える | |
| ヘッドの epoch | 同じ epoch | 同じ epoch | 揃える | |
| 評価 recipe | val の動画 09・10、online causal、7 工程の Jaccard と frame accuracy | 同じ | 揃える | |
| ホストと装置型 | andrew、RTX A6000 | andrew、RTX A6000 | 揃える | |
| seed | 42 | 42 | 揃える | |
| 送り手と型（§5.4 の並べだけ） | 検出塔・G3・H4 と GR・IRN・HiCE・HTT | T→P は検出塔だけと D1-L1 など | 意図的に変える | 仮説の操作である（型と送り手の違いを並べる表） |

UNKNOWN: 0 件。

## 7. 手順

- **Task A（開始状態と記録の確かめ）**: 分岐が `feat/` で始まること、起点、未追跡、試験の失敗の名前、既存の仮想環境の hash を記録する。`meta.created_from` と `conventions_rev` を測り、違えば差し替える。§3 の収束規則の集合と固定の長さの集合を作り、本数を三つの契約の RESULT と比べる。収束規則の集合の全 run に `logs/history.json` が在ることを示す。読む記録の hash を取る。G1 で止まる条件は spec の escalate_if
- **Task B（取り出しと一致の確かめ）**: §4 の表を作る。各 run の `history.json` の epoch の数・結果の回の値・最後の回の値・学習率を下げた回を、その run の `metrics.json`・`metrics_last.json` と突き合わせる。§3 の対を作り、§5.1 を出す。G2 で止まる条件は spec の escalate_if
- **Task C（表と報告）**: §5.2〜§5.4 を記録から道具で作る。§9 の構成で報告を書き、読んだ記録の hash が開始時と一致することを示し、`make forbidden-check` を回し、commit・push・PR（base phase0、Draft でない）・`make task-report` を行う

## 8. 完了判定

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態の記録 | spec の acceptance a の項目がすべて audit にある | 存在しない実行ファイルの経路で、列挙が 0 件になることを示す |
| b | 読む集合 | 収束規則の集合 96・248 本と固定の長さの集合 147・36 本が三つの契約の記録と集合として一致し、収束規則の集合の全 run に `history.json` が在る | 存在しない run の名前を一つ足した集合で不一致を出す。`history.json` を一つ外した写しの集合で欠けを 1 件数える |
| c | 記録どうしの一致 | 全 run で epoch の数、結果の回の値、最後の回の値、学習率を下げた回が版管理の中の記録と一致する | 一つの run の `history.json` の写しの値を 1e-6 ずらすと、突き合わせが不一致を出す |
| d | 下げる前・後の印 | 4・8 epoch 目がすべての run で下げる前、12・16 epoch 目の印が run ごとにある | 学習率を下げた回を 3 にした写しで、4 epoch 目が下げた後と印付けされる |
| e | 一致の確かめ | §3 の全対で 4・8 epoch 目の差と、ちょうど同じ対の数と最大の差が W・腕ごとにある | 片方の値を 1e-6 ずらした写しで、ちょうど同じ対の数が減る。違う W の run を対にした写しで差が出る |
| f | 表 | §5.2〜§5.4 の表が 4・8・12・16 epoch 目にあり、下げた後の値に印がある | 差を `epochs.csv` から測り直してずれが 0。1e-6 ずらした写しを検出する |
| g | 流用の確かめ | irn-hice-htt-pilot の確かめの run の 4・8・12・16 epoch 目の一致・不一致と最大の差がある | 片方を 1e-6 ずらした写しで一致の検査が不一致を返す |
| h | 変えていない | 読んだ記録と既存の中身の hash が開始時と一致し、試験の失敗の名前が開始時と同じ。forbidden-check で本契約の経路の違反が 0 | 新しいファイルを一つ加えた一覧で追加 1 を数える。本契約の新しいファイルが allow_write の許可として名指される |
| i | PR | Draft でない PR が base phase0・分岐 feat/conv-epoch-history-extract で在る | 分岐名と base を `gh pr view` の出力で示す |

## 9. 報告の構成

`RESULT.md` は 150 行以内。節は 判定（status と G1・G2）／完了判定（表。実測値つき）／実測（次の契約で使う値: 一致の確かめの結果、4・8 epoch 目の §5.4 の要約、下げた後になった run の数、§5.6 の当たり外れ）／起票者の誤り（一件 3 行以内）／逸脱／想定外・UNKNOWN／送出（PR 番号と終了コードだけ）。

命令とその出力、参照の解決の全文、対照の出力、変更範囲の一覧、台帳の応答は `audit.md` へ。`RESULT.md` から `audit.md` を行番号で指し、同じ内容を二度書かない。全値と表は `experiments/analysis/conv_epoch_history_extract/REPORT.md` と `epochs.csv`（記録から道具で作る）。

## 10. 次の契約と申し送り

- 一致の確かめが通れば、収束規則の集合の 1〜8 epoch 目は固定の長さの run と同じ学び方の値として読める。入れ替えの腕との差（信号の中身の差）と 6 工程の値は、本契約では作れない。要るなら、irn-hice-htt-pilot の型を graph-t2p-match と同じ条件（固定の長さ、`--record-epochs`、入れ替えの腕あり）で回す。回すかは利用者が決める
- 費用（壁時計）は記録であり、判断に使わない

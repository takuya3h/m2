# T-2026-08-29-lecun-detector-env-pd — lecun 検出器環境の用意と P→D・B2・B4

kind: exp。実行ホストは **lecun**（repo は /home/ubuntu/slocal/m2、A6000 二枚）。
**GPU を使用する。** 学習を伴うため、**prereg.md を学習開始前に commit する**こと（G1 の条件）。

## 0. 目的

前契約 T-2026-08-29-stage0-contract-b は D→P 四段のみ実施し、
**P→D 四段・B2・B4 は lecun の資産欠落で測れなかった**。欠けているのは
Relation-DETR の実装・専用 venv・ImageNet-R50 の重みである。

これらが lecun に無いのは**同期規約どおりの正常な状態**である。同期は環境依存物
（venv）・入れ子 git（third_party）・巨大データ（外部重み）を意図的に除外し、
「各ホストで用意する」と定めている。したがって本契約はまず環境を規約どおり用意し、
その上で残る三項目を測る。**環境の用意は恒久的に価値がある**（今後 lecun で
検出側の実験をするたびに要る）。

本契約の数値は**判定に使わない**（prereg 参照）。測定の成立が成果である。

## 1. 確定している事実

- 前契約で解決済みの参照（本契約でも同一。現物で再確認する）:
  分母 `exp:phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42`、
  凍結源 `run:baselines/s0_016_relationdetr_bbox_seed42`（ckpt sha256 は
  `conventions#frozen_source` の正本と一致することを前契約が確認済み）
- 同期で lecun に**来ないもの**（規約による。現物で確かめること）:
  `.venv-relation-detr`／`third_party/Relation-DETR` の実装本体／
  `data/external` 配下の外部重み（ImageNet-R50 を含む）
- 同期で lecun に**来ているはず**のもの: git 追跡下の設定ミラー
  （`configs/detector_relation_detr/` に学習 config のミラーがある）、
  凍結 ckpt（`third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`。
  ただし checkpoints が同期対象かは現物で確認する）、実験成果物
- **lecun から philip へ SSH が使える**（利用者の申告）。philip には検出器環境が
  在ると記録されている。**参照に使ってよいが、philip 上で学習・評価を実行しない**
  （本契約の実行ホストは lecun）
- B4 の ImageNet-R50 は torchvision の標準重みで代替できる可能性がある。
  外部取得の要否は Step A-3 で確かめる

## 2. 変更対象

- lecun 上の `.venv-relation-detr` と `third_party/Relation-DETR` の実装
  （**環境依存物・入れ子 git であり同期対象外。版管理へ commit しない**）
- `experiments/transfer/` 配下の新規 run（本契約の出力。命名は conventions#naming）
- 環境構築の手順の記録（docs/setup/ へ。**how を記録し、実装本体は追跡しない**）
- 最終 Phase での make runindex による自 run の収穫と投影の再生成
- docs/stage0/ への B2・P→D・B4 の結果追加、stage0_summary への追記
- 契約ディレクトリと受け皿

data 配下の生データ・分割・既存キャッシュ・既存 run へは書き込まない。

## 3. Phase A — 環境の用意と所在の実測

### Step A-1 参照の再確認

分母と凍結源の ref が現物の索引で解決することを確かめる（前契約と同一のはずだが実測する）。
凍結源 ckpt の sha256 を検証する。解決できなければ停止（stop_conditions）。

### Step A-2 検出器環境の用意

**同期で来ないものを lecun 上に用意する。** 版管理へは commit しない（同期対象外のため）。

- `third_party/Relation-DETR` の実装本体を用意する。**どの経路で用意したか（clone 元の
  URL と commit、または philip からの複製）を記録に残す**（decisions_required）。
  ミラーされている `configs/detector_relation_detr/README.md` が正本の config 経路を指す
- `.venv-relation-detr` を作る。必要な依存はミラー config と実装の指定に従う。
  **philip の構成を SSH 越しに参照してよい**（版・依存の突き合わせ）。参照のみで、
  philip 上での実行はしない
- 用意した手順を docs/setup/lecun_detector.md に記す（再現可能な how。秘匿情報は書かない）

### Step A-3 実装可否と重みの所在（G1 の内容）

- **検出器が凍結源 ckpt を読み込み、val の一部で前方計算できることを実測する。**
  可能なら既知の値（前契約や記録にある mAP）と符合するかを見る。
  読み込めない・再現しないなら停止（stop_conditions）
- B4 の ImageNet-R50 の重みの所在を確かめる。lecun のキャッシュ（torch のホーム等）に
  在るか、torchvision で取得できるか。**取得が認証を伴う外部通信なら停止して判断を仰ぐ**
  （escalate。torchvision の標準重みの取得は認証を伴わないので続けてよい）
- P→D の入力経路が既存実装にあるか確かめ、無ければ**入力適合層と界面の追加（W1 の範囲）に
  限り新設する**。それを超える改変が要るなら escalate

### Step A-4 prereg の commit

prereg.md を確定し、**いかなる学習 run の開始よりも前に commit** する。
commit hash と時刻を spec.yaml の prereg 欄へ記入する。時系列は判定 b で検証する。
**環境構築の試走や前方計算の確認は学習ではない**が、疑わしいものは commit 後に回す。

## 4. Phase B — P→D 四段と B2

### P→D 四段（一 seed = 四 run）

- 検出器は Step A の凍結源を凍結し、W1（入力適合層と界面のみ学習）で
  参照入力四段を与える。四段の定義は前契約 SPEC §1 と同一:
  空（空入力界面・分母）／予測（工程塔の予測）／正解（現フレームの正解工程 one-hot と
  持続時間）／正解 ⊕ 予測（正解と予測の事後の結合。上限として使うのはこの段のみ）
- 空段は容量対照（空入力の同一界面）とする
- 予測段に使う工程予測は、**実在する工程塔の予測**（前契約で再評価済みの relationdetr 側
  checkpoint の出力等）を使い、どれを使ったかを notes に記す
- 主指標は mAP。分割は学習 train・測定 val。**test には触れない**。各 run の実時間を記録

### B2 送り手評価

- 凍結源の検出器を**訓練動画と val 動画で評価**し、mAP の差を測る（評価のみ。学習しない）
- 同一 ckpt・同一 recipe であることを config で示す

## 5. Phase C — 強い工程塔と D→P 四段（B4）

- **塔の構築（一 seed）**: ImageNet-R50 を **train の 10 動画**の工程ラベルで微調整し、
  その特徴で TeCNO を学習する。**val・test の動画は使わない**（前契約の SPEC が
  「十五動画」と書いたのは誤りで、val 2・test 3 を含むため禁止 1 に反する。ここで訂正する）
- **D→P 四段 × 三 seed = 十二 run**: 強い工程塔を受け取り手に、W1 で四段を測る
- 塔単体の val 性能も記録する（G1.5 の文脈で使う）

run 総数の見込み: P→D 4 + 塔 1 + D→P 12 = **十七**。B2 は評価のみで run に数えない。
時間や資産の制約で縮退が要るなら G2 の ask で判断を仰ぎ、縮退の内容を報告に明記する。

## 6. Phase D — 収穫・検査・送出

### 完了判定

**四列目は実測で埋める。「確認した」とだけ書くことは認めない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 検出器の動作 | 検出器が凍結源 ckpt を読み込み前方計算できる | 既知の値（記録の mAP）と符合することを示す。符合しない場合はズレを表にして報告 |
| b | P→D 四段 | 四段の mAP の表が揃う（不能の段は理由つきで明示） | 四段の値が全て同一でないこと（測定が入力に感応）。同一なら測定不良として報告 |
| c | prereg の時系列 | prereg commit が全学習 run の開始より前 | commit 時刻と各 run 開始時刻の対照表。**環境構築や前方計算確認が学習に当たらないことも明記** |
| d | B2 と B4 | B2 の mAP 差の表。B4 の四段と塔単体性能 | B2 は同一 ckpt・同一 recipe を config で示す。B4 は塔の学習が train 10 動画に限ることを分割で示す |
| e | 索引と環境の非追跡 | 全 run が task_id 付きで索引に現れる。**venv と third_party 実装が版管理に入っていない** | 収穫の集合差の全量。加えて `git status` 相当で venv・third_party 実装が追跡外であることを示す |
| f | 変更範囲と不変 | 変更が §2 に限られ、既存 run・data・分割が不変 | 差分全量で対象外零件。凍結源 ckpt の sha256 が作業前後で一致。分割 sha256 を記録 |

forbidden-check は収穫により runindex/ で非零になる既知の制約がある。
違反の全件が本契約の許可分と集合一致することを示すこと（前契約の前例に従う）。

### 送出

- 受け皿へ記録し、投影を再生成してから commit する
- 分岐が feat/ で始まることを確かめる。**PR が存在する状態で終える。** base は分岐の起点と同じ分岐
- 台帳へ完了報告を返し、run 台帳へも結果を記す

## 7. 禁止事項

1. 分割の再定義。test への接触（塔の微調整は train の 10 動画のみ）
2. 凍結源の変更・再学習（no_frozen_change）
3. runindex の手編集（収穫は make runindex のみ）
4. data 配下の生データ・既存キャッシュへの書き込み
5. **venv・third_party 実装本体の版管理への commit**（同期対象外。手順のみ記録する）
6. 評価規則の新設・変更（既存の評価実装を使う）
7. **philip 上での学習・評価の実行**（参照のみ可。実行ホストは lecun）
8. prereg の commit 後の書き換え（変更は meta.amendments へ）
9. 認証を伴う外部取得（許諾なしに行わない。torchvision 標準重みの取得は可）
10. 数値の推定を実測として書くこと。本契約の数値による仮説の採否判定
11. 秘匿情報の出力・複製・移動

**禁止は実行者の操作に対するものであり、同期処理による配布や衝突ファイルの生成を含まない。**

## 8. 想定外の扱い

| 事象 | 対処 |
|---|---|
| 検出器の依存が解決できない（版の非互換） | philip の構成を SSH 参照して版を合わせる。それでも不能なら経緯を記録して停止 |
| 凍結 ckpt が lecun に無い（同期対象外だった） | philip から複製する経路を記録して用意。複製元の sha256 と一致を確認 |
| ImageNet-R50 が認証を伴う取得を要する | 停止して判断を仰ぐ（escalate）。torchvision 標準重みは続けてよい |
| P→D 入力経路が W1 の範囲で作れない | escalate。P→D を「不能（理由）」として B4 を続ける判断も添える |
| 前方計算が既知の mAP と符合しない | ズレを表にして停止。環境の不備の可能性。取り繕わない |
| 学習が発散・NaN | 当該 run を失敗として記録し、同条件で一度だけ再試行。なお失敗なら不能として報告 |
| 所要時間が見積もりを超える | G2 で ask。縮退案（B4 の seed 削減→段削減の順）を添える |

失敗時の巻き戻し: 版管理の変更は分岐上のみ。venv・third_party は追跡外なので分岐に依らず
残るが、それは環境の用意であって成果物ではない。停止時も audit を残して stopped で報告。

## 9. 報告の構成

RESULT.md は起票者が判断に使う事実だけを書く。目安は百五十行以内。

- 判定: verdict と関門の結果
- 完了判定: §6 の表に実測値を埋めたもの
- **P→D 四段の表**（値と段差のみ。解釈は書かない）。**B2 の mAP 差**。**B4 の四段と塔単体**
- 環境の用意: 何をどの経路で用意したか（clone 元・commit・philip 参照の有無）
- 実測: 次の契約で使う値（収穫後の索引件数・runindex_commit・GPU 実績・検出器 run の所要時間）
- 起票者の誤り／逸脱・想定外・UNKNOWN／判断待ち
- 送出: PR 番号と終了コード

命令とその出力の全文・環境構築の全手順・run 一覧・時系列の証跡は audit.md へ置き、
RESULT.md からは行番号で指す。同じ内容を二度書かない。

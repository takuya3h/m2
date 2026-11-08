# RESULT — T-2026-11-08-grasp-cards-survey（調査。学習なし。案の採否・推奨は扱わない）

ホスト bengio、分岐 `feat/grasp-cards-survey`（起点 origin/phase0 a68672f1）。時刻は JST。
全値と対照の出力は `experiments/analysis/grasp_cards_survey/REPORT.md`、命令と出力は `audit.md`（以下「audit §」）。

## 1. 判定

**status: pass**（S1〜S7 を実測で埋めた。学習は 0 歩）

- G1 pass（audit Task A）: 分岐・起点・未追跡（同期で届いた他の契約の 12 件を無視の一覧へ）・GPU 0/1 の全体 39/37 MiB と一覧 0 件・空き・失敗 11 件・要約値・220 W × 2
- G2 pass（audit Task B）: S2・S3・S7 の表と対照（test の 04 を混ぜると件数が増える、存在しない 99 で 0、1 ずらすと対応が崩れる）
- G3 pass（audit Task C）: S1・S4・S5・S6 を測った。optimizer を作らず、各道具の重みの要約値が前後で一致

## 2. 完了判定（SPEC §6）

| # | 期待 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | audit Task A の全項目（分岐、起点、未追跡 12 件、GPU、空き 1,250,936,692,736 B、失敗 11 件の名前、venv 108 行 9c7be5c9…・72 行 a74c9c78…、禁止の場所 19 根と重ねの BODY と重み 6 件の要約値） | 存在しない GPU 番号 7 で `No devices were found`・0 件。全体 39/37 MiB − 一覧の和 0 MiB。proc_enum は zsh 9 件・存在しない exe 0 件 |
| b | S1 | キャッシュは (15437, 2048)、空間の軸なし（layer4 の全体平均）。地図 2048×25×45、入力 800×1422 の 1/32（元の画素で 43.2・42.7）、0.0193 s/フレーム（batch 16）、fp16 2,386,944,128 B/518 フレーム | 空間平均とキャッシュの相対 L2 最大 7.23e-7。1 つずらしたフレームとは最小 0.0912 |
| c | S2 | 動画ごとの表（REPORT §S2） | 04 を混ぜると術具 11,172 → 12,501・把持 10,870 → 12,189。99 で全列 0 |
| d | S3 | 間隔の分布（クリップの中、train: 2・2・2・4・508 秒）、術具注釈フレームは全件 CSV の同じ行に在り工程の名前が一致 | 1 ずらすと CSV に在る数・名前の一致が全動画で下がる（例 01: 913 → 884・877） |
| e | S4 | NMS なし（config 83〜84 行、post_process.py 28〜33・47・51 行）、900 query、出力 300、ECE val 0.0185・train 0.0183 | 得点を 1 にすると 0.990・0.989、得点を対応の 0/1 にすると 0.0。val の mAP は記録と差 0 |
| f | S5 | 候補 4 つ（C5・mask_features・memory・decoder の query）。確定と H1 の対応する次元の r の中央 0.493・0.821・0.682・0.255 | 確定どうし（別に読んだ同じ重み）で 4 層とも r = 1.000000 |
| g | S6 | 台本は入力チャネル数を受けない、stem 凍結（r3 115〜116・129〜133・185 行）、8 チャネルの数歩が通る、1 epoch 765.5 s（efros）・506.9 s（bengio、2 GPU） | 7 チャネルの入力で RuntimeError（形の不一致）。追加チャネル 0 で元と出力の差 0.0 |
| h | S7 | 単価の表（REPORT §S7）と出所の経路 | 値が四本目・五本目・三周目の RESULT の記載と一致（四本目 63 行、五本目 47 行、三周目 51 行） |
| i | test 不使用 | 画像を読んだ動画 {01,02,03,06,08,09,10,11,12,13,14,15}、{04,05,07} との共通 0 件 | 各道具が呼ぶ `common.assert_no_test` に 04 を混ぜた入力で `RuntimeError: test の動画が混入: ['04']`（09・10 だけなら通る。`$S/final/i_control.txt`） |
| j | 無変更・学習なし | 27 項目のうち 25 が一致。tasks は inbox.d の 1 件（契約の求め）、scripts は S5 の .pyc 1 件 → 利用者の決定で消して一致を確認（audit D-1・D-2）。forbidden-check pass・違反 0 | 許可を読まない同じ道具で本契約の 9 件が違反 |
| k | PR | §7 | 分岐名 `feat/grasp-cards-survey` |

## 3. 実測（カードの #15・#10 に写す形。詳細は REPORT）

| 項目 | 値 |
|---|---|
| S1 P の Stage 2 の特徴 | 2048 次元、空間なし（layer4 の全体平均） |
| S1 P の空間の地図 | 2048×25×45、縮小率 32、0.0193 s/フレーム、fp32 9.2 MB・fp16 4.6 MB/フレーム |
| S2 目録のフレーム（P・D・G が通る集合） | 術具注釈と同じ。train 9,657・val 1,515 |
| S2 把持の注釈 | train 9,356・val 1,514（持つ術具あり 9,164・1,508）、loss_mask 301・1 |
| S2 工程の CSV の行のうち使える把持の注釈なし | train 1,224/10,580（0.116）・val 390/1,904（0.205）。その行には画像が無い |
| S3 術具注釈フレームの間隔（クリップの中） | 中央 2 秒・95% 4 秒・最大 508 秒（train）/378 秒（val）。Δ=1 は 93.9%・87.2% |
| S4 D の出力 | NMS なし、900 query → 上位 300（クラス・得点・xyxy の枠）。各フレームの最大の得点 中央 0.948（val） |
| S4 D の較正 | ECE（全出力）val 0.0185・train 0.0183（差 −0.0002）。得点 ≥ 0.05 で 0.0774・0.0820（差 +0.0046） |
| S5 G の取り出し口 | C5 2048×24×42（0.013 s）、mask_features 256×192×336（0.042 s）、memory 256×24×42（0.042 s）、query 100×256（0.071 s） |
| S5 確定と H1 の r（中央） | C5 0.493、mask_features 0.821、memory 0.682、query 0.255。並べ替えで一致する形ではない |
| S6 P の入力層 | 3 チャネル固定、stem 凍結。8 チャネルは conv1・正規化・読み込みの 3 か所を変える |
| S7 単価 | 工程側 W1 11.9〜187.2 s、W2・W3（時間ヘッド）1.4〜10.0 s、検出側 W1 5.26〜5.54 h（3 本並行）、検出塔の学び直し 10.1〜10.4 h（単独）・16.3〜16.9 h（同居）、P の fine-tune 4.47 h（efros 1 GPU）・2.68 h（bengio 2 GPU、別データ）、推論 G 0.071 s・D 0.083 s・P 0.019 s/フレーム |

## 4. 起票者の誤り

1. **asserted_without_measuring** — `meta.created_from` の runindex の版 68befc3b と件数 2,363/1,130/1,736 は 2026-10-29 の値で、起点の d3e319ac・2,623/1,305/1,947 と違った。Task A-4 に従い差し替えた（`meta.amendments`）
2. **asserted_without_measuring** — SPEC §1 と S1-2 は `PT_FT_CKPT`（`common.py` の写しの置き場）を読むとするが、bengio のその経路に checkpoint は無い（写しは 009 の頭とキャッシュだけ）。repo の同じ相対経路に sha256 が一致するものが在り、それを読んだ
3. **asserted_without_measuring** — SPEC §1 は工程塔を「ImageNet の初期化、COCO 系統は別の鎖」とするが、確定の P\*-15（`…20_005_ft_coco…`）は `init: coco`（D\* の COCO の重み）。S6-2 の「RGB は ImageNet の重みのまま」は確定の塔と違う鎖で、指示どおりに形を確かめた
4. **asserted_without_measuring** — 完了判定 f は「確定と H1 の基底が一致しない（相関が低い）ことが示されている」を条件にするが、結果を先に書いている。実測では pixel decoder の 2 層で r の中央が 0.68・0.82 と高く、条件は層を選ばないと成り立たない。測った値をそのまま書いた

## 5. 逸脱

- judgement（開始）: task-start が同期で届いた他の契約の 12 件で止まり、利用者の選択「4 で無視に足す」で `.git/info/exclude` に 1 行足した（SPEC Task A-1 の前例どおり）
- judgement（S2）: 「工程注釈のあるフレーム」に二つの集合（目録＝術具注釈と同じ、CSV の全行）があり、両方を表にした
- judgement（S2 の対照）: test の 04 の件数は test の術具・把持の注釈の目録の画像名と `loss_mask/test.txt` から数えた（SPEC §5-1 の「動画番号を混ぜるだけ」）。test の工程の目録と CSV、画像は開いていない
- judgement（S4）: ECE は全出力（各フレーム 300）で数えると得点 0.1 未満が 97% を占めるため、得点 ≥ 0.05 の ECE も併記した
- judgement（S5）: 候補の層と、相関の数え方（全フレームの全位置、query は全 query）、並べ替えを見る「相手の全次元で最大の |r|」は実行者が決めた
- judgement（S6）: BN の統計を動かさないため eval で逆伝播した。train の挙動は確かめていない。conv1 の追加チャネルだけを学ぶ形は勾配の hook で確かめた
- environment（S5 の副作用。自分の過失）: `g5_signals` の import が `scripts/grasppilot/__pycache__/g5_signals.cpython-311.pyc`（59,349 B）を書いた。終了時の要約値で見つけて諮り、利用者の決定で消して `scripts/` の一致を確かめた（audit D-2）
- judgement（S7）: 五本目（T-2026-11-06-grasp-pilot-d-rerun）は phase0 に未統合なので `origin/feat/grasp-pilot-d-rerun` の版を git show で読んだ。bengio の fine-tune は T-2026-11-02-hostdiff-bengio（2 GPU、`phase_manifest_all_phase`）の記録で、確定の塔と設定が違う

## 6. 想定外・UNKNOWN

- 折り A だけを測った。他の折りの密度・間隔は同じとは限らない
- S6 は形の確認だけで、学習が収束するか、8 チャネルで stem を学ぶ／追加チャネルだけを学ぶどちらが良いかは UNKNOWN
- S5 の層の候補は実行者が実装から選んだもの。案 2 がどれを使うかは別の判断
- S4 の得点は後処理後の sigmoid のまま。温度の調整などの較正の直しは試していない
- bengio の 1 GPU での P の fine-tune 1 本の壁時計は記録が無い（efros 1 GPU と bengio 2 GPU だけ）: UNKNOWN

## 7. 送出

- PR: 起票後に記入
- `make task-report`: 送出後に記入

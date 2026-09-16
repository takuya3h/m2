# 証拠地図 A（工程塔の候補）と B（P→D の界面）の DOI 照合と docs/evidence/ への配置

**task_id:** T-2026-09-16-evidence-map-ab  **kind:** analysis

## 1. 背景

研究方針 v2 の Stage 1（工程塔のトーナメント）と Stage 2（P→D 界面の主測定）に向けて、
提案の根拠になる文献を「証拠地図」として repo に置く。探索は deep research（ChatGPT）で行い、
起票者が報告を行単位で地図の様式へ写した（付録 A、付録 B）。利用者が設定距離 0 から 1 の論文八本を
原典で読み、数値は八本すべて一致した。修正は LoViT の初期化源（不明 → ImageNet-1K）と
EndoNet の因果表現の二件で、付録には反映済み。

**本契約の仕事は探索ではなく、照合と様式化である。** 地図の文献が実在するかを機械で確かめ、
不通の行を外し、様式を整えて置く。**数値を書き換えない。** 食い違いは印を付けて残す。

**本契約では GPU を使用しない。**

## 2. 確定した事実（ホストによらない値だけ）

- 地図の行はすべて ChatGPT deep research 一エンジンの報告から写したもの。エンジン間の突き合わせは無い
- 起票者が web で確認した DOI は二件（GGMAE `10.1007/978-3-031-72089-5_18`、LoViT `10.1016/j.media.2024.103366`）。
  残りは未照合
- 著者名が未確認の行が二件（SurgMAE arXiv 2305.11451、SurgPETL arXiv 2409.20083）
- 地図 B の同ドメイン三件は受け取り手が frame-level tool presence であり、box 検出ではない
- 対話シェルは zsh。履歴は `git --no-pager`。外部通信で承認を求められることがある。承認して進む

## 3. Task

**コマンドは書かない。照合の手段は実装環境で使えるものを実行者が選ぶ**（Crossref の API、doi.org の解決、
arXiv の API のいずれか。repo に文献照合の道具があればそれを使ってよい）。

### Task A — 到達性と対照

1. 照合先へ到達できるかを測る。到達できなければ停止し、利用者に諮る（escalate_if）
2. 陽性対照: 起票者が確認済みの DOI 二件が「実在」と返ることを示す
3. 陰性対照: 架空の DOI（例: `10.1000/zz-not-a-real-doi-2026`）が「不在」と返ることを示す。
   両方向が揃って初めて照合器が働いていると言える
4. 使った手段と応答の全文を `audit.md` に残す

### Task B — 全行の照合

1. 付録 A・B の全行について、DOI か arXiv ID を照合する。両方ある行は両方
2. 照合結果を四種で記録する。実在・書誌一致／実在・書誌に差／不在／到達不能
3. 「実在・書誌に差」の行は、地図の文字を書き換えず、印の列に「照合で差: 何が」と残す。
   差が三件以上なら停止して利用者に諮る
4. 「不在」の行は地図から外し、外した行の一覧を報告に置く
5. 著者未確認の二件は、照合の応答から著者を埋める。応答に無ければ UNKNOWN と書く

### Task C — 様式を整えて置く

1. `docs/evidence/` を作り、二ファイルを置く。ファイル名は `spec.yaml` の `must_have` のとおり
2. 各ファイルの先頭に、版（v1）、元の報告（ファイル名とバイト数）、照合日、照合の手段を書く
3. 付録の表をそのまま写す。列は 系統／文献／設定／効果／距離／効かなかった・残したこと／印。
   印の列に本契約の照合結果を足す
4. 各ファイルの末尾に「見つからなかったもの」「未検証の組み合わせ」「起票者の読み」の節を置く
5. `citeturn` という文字列が残っていないことを検査する（deep research の内部参照の残骸）
6. 三連バッククォートと山括弧を含めない

### Task D — 検証と報告

1. L1、L2、`make forbidden-check`、`make spec-check TASK=T-2026-09-16-evidence-map-ab`
2. 完了判定 a〜h を実測で埋める
3. `RESULT.md`、`result.yaml`（版 3）、`audit.md`、`tasks/inbox.d/T-2026-09-16-evidence-map-ab.md`
4. commit、push、PR（Draft でない）。分岐名が `feat/evidence-map-ab` であることを記録する
5. 報告後に `.sync-pause` を**移動**で解除する

## 4. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。**

1. 地図の数値・表番号・設定の記述を書き換えない。差は印で残す
2. 新しい文献を足さない（本契約は探索ではない）
3. `context/auto/*` と `tasks/inbox.md` を再生成しない。並行して別契約が走るため、統合後に一台で回す
4. `experiments/**`、`data/**`、`runindex/**`、`context/conventions.md` に触れない
5. 既存の `tasks/*/` を変えない
6. 開始前から在る未追跡を消さない。退避は移動で行う
7. 外部への送信は `make task-report` 以外の経路で行わない。照合の問い合わせは読み取りであり送信ではない

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 全行の ID が照合を通る | 不通零件 | 不通があれば外した一覧が報告にある。零件なら b の陰性対照で照合器が落ちることを示してあること |
| b | 照合器の対照 | 架空 DOI で不在、実在 DOI で実在 | 両方の応答の全文を audit に残す。片方だけでは空振りと区別できない |
| c | 三方向の検索記録 | 両地図に三方向 | 一方向を欠いた本文で検査が落ちる（検査を機械にする場合）。手で見るなら三方向の見出しの行番号を記録 |
| d | 設定距離零から一の行 | A に一件以上、B に一件以上 | 距離三だけの本文で判定が落ちる。行数を記録 |
| e | 未検証の組み合わせの表 | 両地図の末尾にある | 表を欠く本文で判定が落ちる。行番号を記録 |
| f | citeturn の残骸 | 両地図で零件 | 一件混ぜた本文で一件検出。grep -c で数える（終了コードを件数と呼ばない） |
| g | 著者未確認二件の補完 | 著者名か UNKNOWN | 応答の該当箇所を audit で指す |
| h | PR が Draft でなく存在する | PR 番号 | 分岐名 `feat/evidence-map-ab` を報告に残す |

## 6. 想定外と停止条件

- 照合先に到達できない → 停止して諮る。UNKNOWN で完了扱いにしない
- 書誌の差が三件以上 → 停止して諮る（起票者の写し誤りか、報告の誤りかを利用者が判断する）
- 実行基盤が `docs/` への書き込みや `rm` を拒む → 回避せず提示する
- `make forbidden-check` が開始前からの未追跡で落ちる → 消さず記録して続ける

## 7. 報告の構成

`RESULT.md` は判断に使う事実だけ。目安百五十行以内。

| 節 | 内容 |
|---|---|
| 判定 | `verdict` と各 Gate |
| 完了判定 | 表。各項目に実測値 |
| 実測 | 照合結果の四種の件数、外した行、書誌に差のある行、著者の補完結果 |
| 起票者の誤り | 型と内容。一件三行以内 |
| 逸脱 | 何をなぜ |
| 想定外・UNKNOWN | 測れなかったものと理由 |
| 送出 | PR 番号、終了コード |

`audit.md` へ照合の問い合わせと応答の全文、対照の出力、変更範囲の一覧、台帳の応答。

## 8. 申し送り

- 本契約と `T-2026-09-16-proposal-gate` は並行する。生成物は分かれている
- 地図の「起票者の読み」の節は判定ではなく、地図から言える事実の列挙である。書き換えない
- 印の列の「片方」は ChatGPT のみを意味する。Claude の deep research は利用者の判断で走らせていない

---

## 付録 A — 地図 A: 工程塔のトーナメント候補（このまま写し、印の列に照合結果を足す）

問い: 開放手術・一人称視点・15 から 21 動画・online-causal で、工程塔の候補（初期化源、凍結範囲、
時間ヘッド、履歴長、段数、損失、補助教師）をどう決めるか。
利用者の決定（2026-09-16）: 無ラベル動画の自己教師あり事前学習は候補に入れない。online は strictly past-only のみ。

### A.1 文献行

| 系統 | 文献 | 設定 | 効果（報告の数値。指標名は原文） | 距離 | 効かなかった・残したこと | 印 |
|---|---|---|---|---|---|---|
| in-domain masked video 事前学習 | Fujii, Hatano, Saito, Kajita 2024 MICCAI. DOI 10.1007/978-3-031-72089-5_18, arXiv 2405.19644（GGMAE／EgoSurgery-Phase） | EgoSurgery-Phase 21 動画、14 train／2 val／5 test、0.5 fps、ViT-S VideoMAE 型、T=10 clip、全体 fine-tune 100 epoch。causal は未記載。10-frame clip は確認できるが予測対象時刻に対する配置が本文に無く、strictly past-only とは判定できない | Table 1 macro Jaccard: PhaseLSTM 21.9、PhaseNet 19.7、TeCNO 27.3、Trans-SVNet 23.1、NETE 27.5、GGMAE 33.9。Table 2 Jaccard: scratch 27.1、VideoMAE 29.8、VideoMAEv2 30.8、SurgMAE 27.8、GGMAE 33.9 | 0 | SurgMAE 初期化は scratch と 0.7 pt 差。mask ratio 0.90 が最良で 0.95／0.85／0.80 は 31 台。future work は動画数と視点の拡張 | 起票者確認。原典確認（利用者）。全文。片方 |
| 共有 CNN の tool＋phase 同時学習 | Twinanda ほか 2016／2017 IEEE TMI. arXiv 1602.03012（EndoNet） | Cholec80 40 train／40 test、AlexNet ImageNet 初期化、HMM で online／offline 評価 | Phase Overall-Online: Precision 73.7、Recall 79.6、Accuracy 81.7。Offline は number not available | 1 | Fig. 10 で 10／20／30／40 動画の学習量依存を示す。tool presence 側は 10 動画 65.9→62.0、20 動画 70.9→67.5、30 動画 73.6→77.5、40 動画 80.9→81.0（ToolNet→EndoNet）。工程側の負の結果は記載なし | 未照合。原典確認（利用者）。全文。片方 |
| causal 多段 TCN | Czempiel ほか 2020 MICCAI. DOI 10.1007/978-3-030-59716-0_33, arXiv 2003.10751（TeCNO） | Cholec80 40／8／32、Cholec51 25／8／18、ResNet50 特徴、causal 明記、重み付き CE、Adam 5e-4、25 epoch | Table 2 Cholec80: Accuracy 88.56、Precision 81.64、Recall 85.24 | 1 | Table 1: Stage I 88.35、Stage II 88.56、Stage III 86.49。段を増やすと低下。著者は training set への overfitting の可能性を示唆（実証ではない）。No TCN は 82.22／70.65／75.88 | 未照合。原典確認（利用者）。全文。片方 |
| TCN 埋め込みの Transformer 集約（過去のみ） | Gao, Jin, Long, Dou, Heng 2021 MICCAI. arXiv 2103.09712（Trans-SVNet） | Cholec80 40／40、M2CAI16 27／14、1 fps、ResNet50 ImageNet 固定、TeCNO 埋め込み、過去 30 step のみ | Table 1 Cholec80: Accuracy 90.3、Precision 90.7、Recall 88.8、Jaccard 79.3 | 1 | TeCNO 75.1、ResNet cat TeCNO 73.0（単純結合は低下）、spatial→spatial 60.8、提案 79.3。値は原典で確認。表番号「Table 3」は後続論文の再掲でも確認したため最終稿で原 PDF の表番号を照合する。n=30 79.3、n=40 79.0 | 未照合。原典確認（利用者。表番号除く）。全文。片方 |
| 長短 Transformer（online） | Liu, Boels, Garcia-Peraza-Herrera, Vercauteren, Dasgupta, Granados, Ourselin 2025 Medical Image Analysis 99, 103366. DOI 10.1016/j.media.2024.103366（online 2024-10）; arXiv 2305.08989（LoViT） | Cholec80 40／40、AutoLaparo 10 train／4 val／7 test、1 fps。ViT-B/16、ImageNet-1K 事前学習（報告の「不明」は誤り。利用者が掲載版で確認）。online（現時刻までの履歴を処理する設計）。attention block ごとのマスクの種類までは未確認 | Table 1 Cholec80 relaxed: Accuracy 92.4、Jaccard 81.2。AutoLaparo: Accuracy 81.4、Precision 85.1、Recall 65.9、Jaccard 56.0（主比較表。ablation 表に 55.9 の記載あり） | 1 | 自身の構成要素で低下したものは読んだ範囲に記載なし。結論節: 通常と異なる工程順の動画は誤認識しやすい。各時刻で過去の全特徴を入力するため長い手術で推論が遅くなる（future work） | 起票者確認。原典確認（利用者）。全文。片方 |
| 手術映像の自己教師あり（MoCo v2、SimCLR、DINO、SwAV） | Ramesh ほか 2023 Medical Image Analysis 88. DOI 10.1016/j.media.2023.102844, arXiv 2207.00449 | Cholec80 ラベル 40／10／5 動画、HeiChole 24／4／2、ResNet50、TCN ヘッド（causal 未記載） | Table 8 HeiChole: MoCo v2 Phase F1 64.7。低ラベル Cholec80 で本文に最大 +6.1 F1（5 動画、単フレーム MoCo v2）、+6.0 F1（時間モデル SwAV） | 1 | ImageNet 流儀の SSL は 36 比較中 7 でしか改善せず、F1 が最大 1.9 pt 低下。Fig. 9: batch 256→1024 で F1 −5.5。Fig. 10: 100 epoch 超で最大 −2 | 未照合。全文。片方 |
| in-domain masked video 事前学習 | 著者未確認 2023 arXiv 2305.11451（SurgMAE） | OR-AR 820 動画、Cataract-101 101 動画、ViT-B、offline Bi-GRU | Table 7 Cataract-101 mAP: SwAV 83.61、SimCLR 83.20、random MAE 86.43、VideoMAE 85.05、SurgMAE 87.78、Kinetics-400 初期化 92.85 | 2 | 小データ Cataract-101 では自然動画の Kinetics 初期化が in-domain SurgMAE を上回る。著者は小データでの ViT 事前学習の困難を明記 | 未照合（著者も未）。全文。片方 |
| 凍結 ViT＋adapter（PETL） | 著者未確認 2024 arXiv 2409.20083（SurgPETL） | Cholec80 40／40、AutoLaparo 10／4／7、Cataract-101、凍結 ViT-B／L、adapter と decoder のみ学習、16×4 clip、causal 未記載 | Table VI AutoLaparo: Accuracy 85.0、Precision 82.6、Recall 74.7、Jaccard 66.1。Table V Cholec80 relaxed Jaccard 83.8、unrelaxed 79.1 | 1 | 自然画像の事前学習量 400M→2B で全 adapter が改善せず。Table IV で STA は AIM に対し F1 同値、Jaccard +0.1。複数 adapter も一貫した追加改善なし | 未照合（著者も未）。全文。片方 |
| 多段 TCN（offline、一般動画） | Abu Farha, Gall 2019 CVPR. arXiv 1903.01945（MS-TCN） | 50Salads、GTEA（頭部カメラ 28 動画）、Breakfast。I3D 特徴、acausal 明記、CE＋truncated MSE | Table 9 GTEA: F1@10/25/50 85.8/83.4/69.8、Edit 79.0、Acc 76.3 | 2 | Table 5: 後段に確率＋特徴を渡すと 56.2/53.7/45.8、確率のみで 76.3/74.0/64.5。特徴の転送は大きく低下 | 未照合。全文。片方 |
| 局所・階層 attention の Transformer（offline） | Yi, Wen, Jiang 2021 arXiv 2110.08568（ASFormer） | 50Salads、GTEA、Breakfast、I3D 特徴、全系列（causal 版なし） | Table 1 50Salads: F1@10/25/50 85.1/83.4/76.0、Edit 79.6、Acc 85.6 | 2 | 標準の positional encoding が全指標を下げる（encoder 80.2/78.0/70.0、decoder 78.1/76.7/69.4）。非階層は 64.2/61.5/55.1 | 未照合。全文。片方 |
| 長短記憶 Transformer（online） | Xu, Gao, Chen, Davis, Crandall 2021 arXiv 2107.03377（LSTR） | THUMOS'14、TVSeries、HACS。online 定義。長期 512 s＋短期 8 s | Table 1: THUMOS mAP 65.3（ActivityNet 特徴）、69.5（Kinetics 特徴） | 2 | Table 3: 長期 stride 1／2／4 は同値 69.5、8 で 69.2、以降 128 で 65.9。圧縮は途中まで零、以降低下 | 未照合。全文。片方 |
| 一人称 video-language 事前学習 | Lin ほか 2022 arXiv 2206.01670（EgoVLP） | EgoClip（Ego4D 由来）、TimeSformer、ImageNet-21K 初期化、4 frame 224、offline | Table 10 EgoMCQ intra/inter: EgoClip＋EgoNCE 90.6/57.2、CC3M＋WebVid 62.5/27.4 | 3 | HowTo100M 事前学習は EPIC 検索で「事前学習なし」と同程度の曲線。手術評価なし | 未照合。全文。片方 |
| 三人称→一人称の蒸留 | Li, Nagarajan, Xiong, Grauman 2021 CVPR. arXiv 2104.07905（Ego-Exo） | Charades-Ego、EPIC-100。詳細は要旨のみ | number not available | 3 | 記載なし（要旨） | 未照合。要旨。片方 |
| 視線と行動の同時モデル | Li, Liu, Rehg 2020 arXiv 2006.00626（EGTEA Gaze+） | 頭部カメラ、視線・手マスク付き。詳細は要旨のみ | number not available | 3 | 記載なし（要旨） | 未照合。要旨。片方 |
| データセット論文 | Damen ほか 2018 ECCV. arXiv 1804.02748（EPIC-KITCHENS） | 55 h、32 参加者、TSN baseline | number not available（表頭が抽出で欠落） | 3 | 記載なし | 未照合。全文。片方 |

### A.2 見つからなかったもの（報告の記載）と検索記録

同ドメインの検索語: Trans-SVNet／LoViT／EndoNet／Dissecting SSL for surgical CV／EgoSurgery-Phase GGMAE／SurgMAE／surgical video pretraining／AutoLaparo／Cataract-101／surgical foundation video-language。
一般機構の検索語: temporal action segmentation Breakfast 50Salads GTEA causal online／online action detection THUMOS TVSeries LSTR／ASFormer／MS-TCN。
隣接ドメインの検索語: egocentric action recognition EPIC-Kitchens Ego4D pretraining EgoVLP LaViLa／Ego-Exo／EPIC-Kitchens／EGTEA gaze。

見つからなかったもの:
- EgoSurgery-Phase／開放手術一人称で、未来フレームを明示的に禁じた strictly causal モデルの表
- EgoSurgery-Tool と EgoSurgery-Phase を同一 causal ネットワークで同時学習し 14 から 21 動画で Jaccard／F1 を報告した研究
- 同一構成・同一 split で acausal と strictly causal を一表で比べた行動分割研究
- Ego4D／EPIC／EGTEA で事前学習した一人称 backbone を小規模手術工程へ移して causal で測った研究

### A.3 未検証の組み合わせ（報告の記載）

| 組み合わせ | 未検証の理由の仮説 |
|---|---|
| GGMAE／VideoMAE 系 in-domain 事前学習 ＋ causal TeCNO／LoViT 型ヘッド（EgoSurgery-Phase） | 固定 clip 事前学習と streaming モデルを分けて学習する追加実装が要る（技術） |
| 手術 masked-video 事前学習 ＋ 凍結／部分凍結 backbone ＋ causal ヘッド | 同上 |
| EgoVLP／EgoClip 初期化 ＋ 開放手術工程 | コミュニティが分かれている（偶然） |
| EgoSurgery-Tool の補助教師 ＋ EgoSurgery-Phase ＋ causal 推論 | 注釈の整列と multi-task sampling の実装（技術） |
| ASFormer 型の局所・階層 attention を causal mask 化 | decoder の refinement が全系列を参照する構造（技術） |
| MS-TCN の truncated-MSE 平滑化損失 ＋ EgoSurgery causal TCN | 実験選択（偶然） |
| Gaze を事前学習だけに使い推論は RGB のみの causal 長履歴モデル | 記載なし |

### A.4 起票者の読み（地図から言えること。判定ではない）

1. 設定距離 0 の文献は GGMAE 一件で、しかも causal が未記載。online-causal の下で距離 0 の数値は存在しない
2. 「追加要素が常に効く」は置けない。段数増（TeCNO Stage III）、単純結合（Trans-SVNet cat）、SurgMAE 初期化、
   ImageNet 流儀の SSL、PE（ASFormer）、特徴の転送（MS-TCN Table 5）で低下または零の報告がある
3. トーナメントの軸は結果順位ではなく、初期化源／凍結範囲／causal ヘッドの種類／履歴長／段数／平滑化・不均衡損失／補助教師
4. LoViT は初期化源が確定し、「ImageNet-1K 初期化＋online＋AutoLaparo 10 train 動画」という具体的な比較対象になった

## 付録 B — 地図 B: P→D の界面の型（このまま写し、印の列に照合結果を足す）

問い: 凍結した工程塔 P から凍結した DETR 系検出塔 D へ、小さな学習可能な界面で工程情報を渡す。
機構の系統と送り手の信号段（予測ラベル／正解ラベル／確率分布／特徴ベクトル）をどう選ぶか。
利用者の決定（2026-09-16）: presence から box mAP への外挿は割引率を置かず、「presence の Δ は上限の目安、box の期待値は不明」と書く。

### B.1 文献行

| 系統 | 文献 | 設定（送り手→受け取り手、粒度、信号） | 効果（結合あり／なし。指標名は原文） | 距離 | 効かなかった・残したこと | 印 |
|---|---|---|---|---|---|---|
| 補助損失・共有表現 | Twinanda ほか 2017 IEEE TMI. arXiv 1602.03012（EndoNet） | Cholec80。phase の正解ラベルを学習時の教師に。受け取り手は frame-level tool presence（box ではない）。推論時に phase を読まない | 40 動画: ToolNet 80.9 → EndoNet 81.0 mean AP（+0.1、Table II）。10 動画: 65.9 → 62.0（−3.9）。20 動画 70.9→67.5（−3.4）、30 動画 73.6→77.5（+3.9）。差は multi-task EndoNet と single-task ToolNet の差で、phase 補助損失だけの isolated ablation ではない | 1 | 符号が学習量で変わる。逆方向 oracle（正解 tool→phase）は 75.2→75.3。時間モデルなし | 未照合。原典確認（利用者）。全文。片方 |
| 補助損失・共有表現 | Twinanda ほか 2016 M2CAI 技術報告. arXiv 1610.08851 | M2CAI16-tool、Cholec80 40 動画。同上 | ToolNet 73.9 → EndoNet 74.2 mAP（+0.3、Table 1）。著者が no significant improvement と記載 | 1 | 学習量の差の方が結果に出た、と著者 | 未照合。全文。片方 |
| 特徴→事前分布の相関損失（新系統） | Jin, Li, Dou, Chen, Qin, Fu, Heng 2020 Medical Image Analysis. arXiv 1907.06099（MTRCNet-CL） | Cholec80。送り手は phase 側 LSTM の特徴ベクトル（10 s 系列）。受け取り手は frame-level tool presence。学習した行列で tool 事前分布へ写像し KL で整合 | MTRCNet 87.5 → MTRCNet-CL 89.1 tool mAP（+1.6、Table 1）。Table 2: label-space 写像 86.8、mutual 87.1、feature-space 89.1。事前分布と出力の平均 88.8、事前分布のみ 88.4 | 1 | ラベル空間の結合は特徴空間より低く、no-CL の 87.5 も下回る。相互写像は一方向より低い。数値は原典と一致（TS1 85.1、TS2 88.1 も）。構造は共有 encoder＋二分岐の joint training で、凍結塔＋界面ではない。L 軸の前例には使えるが凍結界面の効果量には使えない | 未照合。原典確認（利用者）。全文。片方 |
| FiLM（特徴の変調） | Perez, Strub, de Vries, Dumoulin, Courville 2018 AAAI. arXiv 1709.07871 | CLEVR。質問特徴→画像レベル分類（dense ではない） | Table 2: 97.4 ／ FiLM なし 21.4。β=0 で 96.9、γ=1 で 95.9、FiLM 層一つで 97.3 | 3 | CoGenT で分布の組み合わせに依存（A 98.3、B 75.6）。fine-tune 後の忘却 | 未照合。全文。片方 |
| cross-attention 条件付け | Yang, Wang, Tang, Chen, Zhao, Torr 2022 CVPR. arXiv 2112.02244（LAVT） | RefCOCO。正解テキスト token →画素分割 | Table 2 RefCOCO val: なし oIoU 68.82／mIoU 68.87、PWAM のみ 70.78／71.96、full 72.73／74.46 | 2 | 置く場所で符号が変わる: Table 3 で 72.27→72.06、72.29→71.38。追加 decoder で 72.73→72.12 | 未照合。全文。片方 |
| FiLM ＋ 小 decoder（凍結 encoder） | Lüddecke, Ecker 2022 CVPR. arXiv 2112.10003（CLIPSeg） | PhraseCut。CLIP 埋め込み（凍結）→画素分割。学習パラメータ 1,122,305（D=64） | FiLM on/off の対は number not available。Table 9: text mIoU 43.6／AP 76.7、CLIP 事前学習なし 13.1／12.6 | 2 | D=16 で 37.4／71.5、layer-3 のみ 31.9／64.9 | 未照合。全文。片方 |
| 外部条件付き DETR | Kamath ほか 2021 ICCV. arXiv 2104.12763（MDETR） | 正解テキスト→box 集合予測 | 条件 on/off は number not available（タスク自体がテキスト条件付き） | 2 | 記載なし（要旨） | 未照合。要旨。片方 |
| タスク親和性・負の転移 | Standley, Zamir, Chen, Guibas, Malik, Savarese 2020 ICML. arXiv 1905.07553 | Taskonomy 由来の dense タスク。共有 backbone、推論時の送り手なし | Table 2 Setting 1: Depth→SemSeg +4.17%、SemSeg→Depth −5.41%、SemSeg→Normals −11.29%、→Edges −34.64%。五タスク同時は単独平均比 −19.00% | 3 | 親和性は方向・容量・データ量に依存。容量を変えると Table 2 と Table 5 の関係が大きく変わり、データ 5% でも変わる。共有 backbone MTL の前例であり、凍結界面では勾配衝突の経路が無い | 未照合。原典確認（利用者）。全文。片方 |
| 記憶バンク cross-attention ＋ 加算バイアス | Beery, Wu, Rathod, Votel, Huang 2020 CVPR. arXiv 1912.03538（Context R-CNN） | 固定カメラ。他フレームの ROI 特徴（Faster R-CNN 由来）で記憶バンクを構築→現フレーム box 検出へ attention で注入。attend したベクトルを proposal 特徴へ per-channel bias として加算。「凍結送り手→凍結検出器の間だけを学習」した研究ではない | Table 1: SS 37.9→55.9 mAP@0.5、CCT 56.8→76.3、CityCam 38.1→42.6。時間幅 1 min 50.3、1 h 52.1、1 day 52.5、1 week 54.1、1 month 55.6 | 2 | 多数決は 37.9→37.8（−0.1）。空間平均 39.6、単フレーム attention 44.9、短期 46.4、長期 55.6。数値は原典と一致 | 未照合。原典確認（利用者）。全文。片方 |
| 系列レベル意味集約 | Wu, Chen, Wang, Zhang 2019 ICCV. arXiv 1907.06390（SELSA） | ImageNet VID、EPIC-KITCHENS（±10 s の proposal 特徴）→現フレーム box 検出。行動ラベルは使わない | VID: 73.62→80.25 mAP。EPIC seen 36.57→37.97、unseen 31.86→34.80 | 2 | 同フレーム集約は高速動体で 51.53→51.43。Seq-NMS 追加で 82.69→82.48、84.30→83.73。EPIC は予備的で調整不十分と著者 | 未照合。全文。片方 |
| グラフ推論の文脈精緻化（新系統） | Liu, Wang, Shan, Chen 2018 CVPR. arXiv 1807.00119（SIN） | VOC、COCO。場面特徴＋proposal 関係→box 検出 | number not available（要旨） | 3 | 記載なし（要旨） | 未照合。要旨。片方 |

### B.2 見つからなかったもの（報告の記載）と検索記録

同ドメインの検索語: surgical phase tool detection conditioning Cholec80／phase tool presence multi-task EndoNet／MTRCNet-CL correlation loss／phase information tool detector Cholec80 DETR／CholecT50 phase instrument triplet／CATARACTS／HeiChole／EgoSurgery phase tool detection／oracle／Rendezvous temporal phase tool interaction。
一般機構の検索語: FiLM conditional dense prediction／FiLM frozen backbone segmentation／cross attention conditioning dense prediction／conditional DETR external context query conditioning／MDETR／class prior conditioned object detection／task affinity dense tasks negative transfer／Which Tasks Should Be Learned Together／Taskonomy／gradient conflict multi task dense prediction。
隣接ドメインの検索語: scene label conditioned object detection／global scene context object detection／activity conditioned object detection egocentric／EPIC-KITCHENS action label object detection prior／Ego4D activity context object detection／video level context object detection／temporal context Faster R-CNN／Context R-CNN／SELSA EPIC Kitchens／object detection co-occurrence prior context。

見つからなかったもの:
- 凍結 P と凍結 D の間だけを学習する手術映像の研究
- DETR の object query を手術工程で条件付けする研究、phase 条件付きの anchor／class logit
- 予測 phase と phase 確率分布を同一検出器で直接比べた研究
- 正解 phase の oracle と予測 phase を box-level tool mAP で並べた研究
- 同一 frozen DETR で add／concat、FiLM、cross-attention、query 条件付け、class-logit prior を同一パラメータ予算で比べた研究
- EPIC／Ego4D で行動ラベル→box 検出の方向（見つかったのは逆方向ばかり）

報告が除外した種: Conditional DETR は外部文脈の条件付けではなく decoder 内部の空間条件付けであるため採用していない。

### B.3 機構の系統 × 送り手の信号段（報告の表を要約）

| 系統 | 予測ラベル | 正解ラベル（oracle） | 確率分布 | 特徴ベクトル |
|---|---|---|---|---|
| 特徴の結合 add／concat | 未 | 未 | 未 | 正（Context R-CNN） |
| FiLM | 未 | 未 | 未 | 正（FiLM、CLIPSeg。ただし dense でない／対なし） |
| cross-attention | 未 | 未 | 未 | 正（LAVT、Context R-CNN） |
| DETR query 条件付け | 未 | 未 | 未 | 未（MDETR は別設定） |
| 出力 class prior・logit 再採点 | 未 | 未 | 零・負（MTRCNet-CL label-space 86.8） | 零・負（平均で 89.1→88.8） |
| 補助 phase 損失・共有 MTL | 未 | 零・負（EndoNet 10 動画 −3.9、M2CAI +0.3） | 未 | 未 |
| 蒸留・相関損失 | 未 | 未 | 未 | 正（MTRCNet-CL +1.6） |
| 時間履歴・窓 | 未 | 未 | 未 | 正（MTRCNet-CL、SELSA、Context R-CNN） |

本研究の設計（予測／正解／確率 × 凍結 DETR の界面）に当たる列は全て「未」。

### B.4 起票者の読み（地図から言えること。判定ではない）

1. 設定距離 0 の文献は無い。距離 1 は同ドメインの三件だが、受け取り手は presence であって box ではなく、塔は凍結されていない
2. 凍結塔の間だけを学習する設定では、EndoNet／Standley の負の転移の経路（共有重みへの勾配衝突）が存在しない。
   MTRCNet-CL・LAVT・SELSA・Context R-CNN は「信号の形式・注入位置・集約規則を変えるだけで差分が正・零・負に分かれる」を示す
3. MTRCNet-CL の label-space 86.8、no-CL 87.5、feature-space 89.1 の順は、本研究の豊かさ軸 L0 から L3 に最も近い既存値
4. Context R-CNN の多数決 −0.1 と attention +18.0 の対比は、同じ文脈でも集約規則で零になる例。feature-level 界面の機構例であり凍結塔の同型ではない
5. Standley の方向依存は H1（方向依存）の一般機構側の前例。共有 backbone MTL の前例であり、凍結界面で同じ現象が起きる証拠ではない
6. 本研究の Stage 2 の四段（空／予測／正解／正解⊕予測）は、地図上で誰も埋めていないセル。第三段（分析論文）の位置づけの根拠になり得る事実
7. 八本のどれも「凍結 P＋凍結 D＋学習可能な界面のみ」ではない。B.3 の「未」の判断は原典確認後も維持

# 証拠地図 A — 工程塔のトーナメント候補

**版:** v1
**元の報告:** repo に deep research の出力ファイルは無い。出所は本契約の契約書
`tasks/T-2026-09-16-evidence-map-ab/SPEC.md`（30894 バイト、sha256 先頭 c17c2d9961aeb979）の
付録 A。起票者が deep research（ChatGPT 一エンジン）の報告を行単位で地図の様式へ写したものである。
**照合日:** 2026-09-16（JST 2026-09-17 未明に実施）
**照合の手段:** Crossref REST API（`api.crossref.org/works/`）で DOI を、arXiv API
（`export.arxiv.org/api/query`）で arXiv ID を引いた。doi.org の解決も到達性の確認に使った。
**照合の結果:** 全 15 行が「実在・書誌一致」。不在 0 件、到達不能 0 件、書誌に差 0 件。
照合器が働いていることは対照で示した（実在 DOI 2 件が HTTP 200、架空 DOI が HTTP 404）。
問い合わせと応答の全文は `tasks/T-2026-09-16-evidence-map-ab/audit.md` にある。

**印の列の読み方。** 「未照合」「起票者確認」などは**起票時点の状態**であり、本契約は
これを書き換えていない。本契約の照合結果は同じ欄の末尾に `照合2026-09-16:` として**足してある**。

**この地図は判定ではない。** 数値は各文献の報告のままで、本契約は一字も書き換えていない。

---

問い: 開放手術・一人称視点・15 から 21 動画・online-causal で、工程塔の候補（初期化源、凍結範囲、
時間ヘッド、履歴長、段数、損失、補助教師）をどう決めるか。
利用者の決定（2026-09-16）: 無ラベル動画の自己教師あり事前学習は候補に入れない。online は strictly past-only のみ。

## A.1 文献行


| 系統 | 文献 | 設定 | 効果（報告の数値。指標名は原文） | 距離 | 効かなかった・残したこと | 印 |
|---|---|---|---|---|---|---|
| in-domain masked video 事前学習 | Fujii, Hatano, Saito, Kajita 2024 MICCAI. DOI 10.1007/978-3-031-72089-5_18, arXiv 2405.19644（GGMAE／EgoSurgery-Phase） | EgoSurgery-Phase 21 動画、14 train／2 val／5 test、0.5 fps、ViT-S VideoMAE 型、T=10 clip、全体 fine-tune 100 epoch。causal は未記載。10-frame clip は確認できるが予測対象時刻に対する配置が本文に無く、strictly past-only とは判定できない | Table 1 macro Jaccard: PhaseLSTM 21.9、PhaseNet 19.7、TeCNO 27.3、Trans-SVNet 23.1、NETE 27.5、GGMAE 33.9。Table 2 Jaccard: scratch 27.1、VideoMAE 29.8、VideoMAEv2 30.8、SurgMAE 27.8、GGMAE 33.9 | 0 | SurgMAE 初期化は scratch と 0.7 pt 差。mask ratio 0.90 が最良で 0.95／0.85／0.80 は 31 台。future work は動画数と視点の拡張 | 起票者確認。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（DOI 10.1007/978-3-031-72089-5_18 / arXiv 2405.19644） |
| 共有 CNN の tool＋phase 同時学習 | Twinanda ほか 2016／2017 IEEE TMI. arXiv 1602.03012（EndoNet） | Cholec80 40 train／40 test、AlexNet ImageNet 初期化、HMM で online／offline 評価 | Phase Overall-Online: Precision 73.7、Recall 79.6、Accuracy 81.7。Offline は number not available | 1 | Fig. 10 で 10／20／30／40 動画の学習量依存を示す。tool presence 側は 10 動画 65.9→62.0、20 動画 70.9→67.5、30 動画 73.6→77.5、40 動画 80.9→81.0（ToolNet→EndoNet）。工程側の負の結果は記載なし | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1602.03012） |
| causal 多段 TCN | Czempiel ほか 2020 MICCAI. DOI 10.1007/978-3-030-59716-0_33, arXiv 2003.10751（TeCNO） | Cholec80 40／8／32、Cholec51 25／8／18、ResNet50 特徴、causal 明記、重み付き CE、Adam 5e-4、25 epoch | Table 2 Cholec80: Accuracy 88.56、Precision 81.64、Recall 85.24 | 1 | Table 1: Stage I 88.35、Stage II 88.56、Stage III 86.49。段を増やすと低下。著者は training set への overfitting の可能性を示唆（実証ではない）。No TCN は 82.22／70.65／75.88 | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（DOI 10.1007/978-3-030-59716-0_33 / arXiv 2003.10751） |
| TCN 埋め込みの Transformer 集約（過去のみ） | Gao, Jin, Long, Dou, Heng 2021 MICCAI. arXiv 2103.09712（Trans-SVNet） | Cholec80 40／40、M2CAI16 27／14、1 fps、ResNet50 ImageNet 固定、TeCNO 埋め込み、過去 30 step のみ | Table 1 Cholec80: Accuracy 90.3、Precision 90.7、Recall 88.8、Jaccard 79.3 | 1 | TeCNO 75.1、ResNet cat TeCNO 73.0（単純結合は低下）、spatial→spatial 60.8、提案 79.3。値は原典で確認。表番号「Table 3」は後続論文の再掲でも確認したため最終稿で原 PDF の表番号を照合する。n=30 79.3、n=40 79.0 | 未照合。原典確認（利用者。表番号除く）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2103.09712） |
| 長短 Transformer（online） | Liu, Boels, Garcia-Peraza-Herrera, Vercauteren, Dasgupta, Granados, Ourselin 2025 Medical Image Analysis 99, 103366. DOI 10.1016/j.media.2024.103366（online 2024-10）; arXiv 2305.08989（LoViT） | Cholec80 40／40、AutoLaparo 10 train／4 val／7 test、1 fps。ViT-B/16、ImageNet-1K 事前学習（報告の「不明」は誤り。利用者が掲載版で確認）。online（現時刻までの履歴を処理する設計）。attention block ごとのマスクの種類までは未確認 | Table 1 Cholec80 relaxed: Accuracy 92.4、Jaccard 81.2。AutoLaparo: Accuracy 81.4、Precision 85.1、Recall 65.9、Jaccard 56.0（主比較表。ablation 表に 55.9 の記載あり） | 1 | 自身の構成要素で低下したものは読んだ範囲に記載なし。結論節: 通常と異なる工程順の動画は誤認識しやすい。各時刻で過去の全特徴を入力するため長い手術で推論が遅くなる（future work） | 起票者確認。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（DOI 10.1016/j.media.2024.103366 / arXiv 2305.08989） |
| 手術映像の自己教師あり（MoCo v2、SimCLR、DINO、SwAV） | Ramesh ほか 2023 Medical Image Analysis 88. DOI 10.1016/j.media.2023.102844, arXiv 2207.00449 | Cholec80 ラベル 40／10／5 動画、HeiChole 24／4／2、ResNet50、TCN ヘッド（causal 未記載） | Table 8 HeiChole: MoCo v2 Phase F1 64.7。低ラベル Cholec80 で本文に最大 +6.1 F1（5 動画、単フレーム MoCo v2）、+6.0 F1（時間モデル SwAV） | 1 | ImageNet 流儀の SSL は 36 比較中 7 でしか改善せず、F1 が最大 1.9 pt 低下。Fig. 9: batch 256→1024 で F1 −5.5。Fig. 10: 100 epoch 超で最大 −2 | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（DOI 10.1016/j.media.2023.102844 / arXiv 2207.00449） |
| in-domain masked video 事前学習 | Muhammad Abdullah Jamal, Omid Mohareri 2023 arXiv 2305.11451（SurgMAE） | OR-AR 820 動画、Cataract-101 101 動画、ViT-B、offline Bi-GRU | Table 7 Cataract-101 mAP: SwAV 83.61、SimCLR 83.20、random MAE 86.43、VideoMAE 85.05、SurgMAE 87.78、Kinetics-400 初期化 92.85 | 2 | 小データ Cataract-101 では自然動画の Kinetics 初期化が in-domain SurgMAE を上回る。著者は小データでの ViT 事前学習の困難を明記 | 未照合（著者も未・起票時）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2305.11451） |
| 凍結 ViT＋adapter（PETL） | Shu Yang, Zhiyuan Cai, Luyang Luo, Ning Ma, Shuchang Xu, Hao Chen 2024 arXiv 2409.20083（SurgPETL） | Cholec80 40／40、AutoLaparo 10／4／7、Cataract-101、凍結 ViT-B／L、adapter と decoder のみ学習、16×4 clip、causal 未記載 | Table VI AutoLaparo: Accuracy 85.0、Precision 82.6、Recall 74.7、Jaccard 66.1。Table V Cholec80 relaxed Jaccard 83.8、unrelaxed 79.1 | 1 | 自然画像の事前学習量 400M→2B で全 adapter が改善せず。Table IV で STA は AIM に対し F1 同値、Jaccard +0.1。複数 adapter も一貫した追加改善なし | 未照合（著者も未・起票時）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2409.20083） |
| 多段 TCN（offline、一般動画） | Abu Farha, Gall 2019 CVPR. arXiv 1903.01945（MS-TCN） | 50Salads、GTEA（頭部カメラ 28 動画）、Breakfast。I3D 特徴、acausal 明記、CE＋truncated MSE | Table 9 GTEA: F1@10/25/50 85.8/83.4/69.8、Edit 79.0、Acc 76.3 | 2 | Table 5: 後段に確率＋特徴を渡すと 56.2/53.7/45.8、確率のみで 76.3/74.0/64.5。特徴の転送は大きく低下 | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1903.01945） |
| 局所・階層 attention の Transformer（offline） | Yi, Wen, Jiang 2021 arXiv 2110.08568（ASFormer） | 50Salads、GTEA、Breakfast、I3D 特徴、全系列（causal 版なし） | Table 1 50Salads: F1@10/25/50 85.1/83.4/76.0、Edit 79.6、Acc 85.6 | 2 | 標準の positional encoding が全指標を下げる（encoder 80.2/78.0/70.0、decoder 78.1/76.7/69.4）。非階層は 64.2/61.5/55.1 | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2110.08568） |
| 長短記憶 Transformer（online） | Xu, Gao, Chen, Davis, Crandall 2021 arXiv 2107.03377（LSTR） | THUMOS'14、TVSeries、HACS。online 定義。長期 512 s＋短期 8 s | Table 1: THUMOS mAP 65.3（ActivityNet 特徴）、69.5（Kinetics 特徴） | 2 | Table 3: 長期 stride 1／2／4 は同値 69.5、8 で 69.2、以降 128 で 65.9。圧縮は途中まで零、以降低下 | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2107.03377） |
| 一人称 video-language 事前学習 | Lin ほか 2022 arXiv 2206.01670（EgoVLP） | EgoClip（Ego4D 由来）、TimeSformer、ImageNet-21K 初期化、4 frame 224、offline | Table 10 EgoMCQ intra/inter: EgoClip＋EgoNCE 90.6/57.2、CC3M＋WebVid 62.5/27.4 | 3 | HowTo100M 事前学習は EPIC 検索で「事前学習なし」と同程度の曲線。手術評価なし | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2206.01670） |
| 三人称→一人称の蒸留 | Li, Nagarajan, Xiong, Grauman 2021 CVPR. arXiv 2104.07905（Ego-Exo） | Charades-Ego、EPIC-100。詳細は要旨のみ | number not available | 3 | 記載なし（要旨） | 未照合。要旨。片方。照合2026-09-16: 実在・書誌一致（arXiv 2104.07905） |
| 視線と行動の同時モデル | Li, Liu, Rehg 2020 arXiv 2006.00626（EGTEA Gaze+） | 頭部カメラ、視線・手マスク付き。詳細は要旨のみ | number not available | 3 | 記載なし（要旨） | 未照合。要旨。片方。照合2026-09-16: 実在・書誌一致（arXiv 2006.00626） |
| データセット論文 | Damen ほか 2018 ECCV. arXiv 1804.02748（EPIC-KITCHENS） | 55 h、32 参加者、TSN baseline | number not available（表頭が抽出で欠落） | 3 | 記載なし | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1804.02748） |

## A.2 見つからなかったもの と 検索記録


同ドメインの検索語: Trans-SVNet／LoViT／EndoNet／Dissecting SSL for surgical CV／EgoSurgery-Phase GGMAE／SurgMAE／surgical video pretraining／AutoLaparo／Cataract-101／surgical foundation video-language。
一般機構の検索語: temporal action segmentation Breakfast 50Salads GTEA causal online／online action detection THUMOS TVSeries LSTR／ASFormer／MS-TCN。
隣接ドメインの検索語: egocentric action recognition EPIC-Kitchens Ego4D pretraining EgoVLP LaViLa／Ego-Exo／EPIC-Kitchens／EGTEA gaze。

見つからなかったもの:
- EgoSurgery-Phase／開放手術一人称で、未来フレームを明示的に禁じた strictly causal モデルの表
- EgoSurgery-Tool と EgoSurgery-Phase を同一 causal ネットワークで同時学習し 14 から 21 動画で Jaccard／F1 を報告した研究
- 同一構成・同一 split で acausal と strictly causal を一表で比べた行動分割研究
- Ego4D／EPIC／EGTEA で事前学習した一人称 backbone を小規模手術工程へ移して causal で測った研究

## A.3 未検証の組み合わせ


| 組み合わせ | 未検証の理由の仮説 |
|---|---|
| GGMAE／VideoMAE 系 in-domain 事前学習 ＋ causal TeCNO／LoViT 型ヘッド（EgoSurgery-Phase） | 固定 clip 事前学習と streaming モデルを分けて学習する追加実装が要る（技術） |
| 手術 masked-video 事前学習 ＋ 凍結／部分凍結 backbone ＋ causal ヘッド | 同上 |
| EgoVLP／EgoClip 初期化 ＋ 開放手術工程 | コミュニティが分かれている（偶然） |
| EgoSurgery-Tool の補助教師 ＋ EgoSurgery-Phase ＋ causal 推論 | 注釈の整列と multi-task sampling の実装（技術） |
| ASFormer 型の局所・階層 attention を causal mask 化 | decoder の refinement が全系列を参照する構造（技術） |
| MS-TCN の truncated-MSE 平滑化損失 ＋ EgoSurgery causal TCN | 実験選択（偶然） |
| Gaze を事前学習だけに使い推論は RGB のみの causal 長履歴モデル | 記載なし |

## A.4 起票者の読み（地図から言えること。判定ではない）


1. 設定距離 0 の文献は GGMAE 一件で、しかも causal が未記載。online-causal の下で距離 0 の数値は存在しない
2. 「追加要素が常に効く」は置けない。段数増（TeCNO Stage III）、単純結合（Trans-SVNet cat）、SurgMAE 初期化、
   ImageNet 流儀の SSL、PE（ASFormer）、特徴の転送（MS-TCN Table 5）で低下または零の報告がある
3. トーナメントの軸は結果順位ではなく、初期化源／凍結範囲／causal ヘッドの種類／履歴長／段数／平滑化・不均衡損失／補助教師
4. LoViT は初期化源が確定し、「ImageNet-1K 初期化＋online＋AutoLaparo 10 train 動画」という具体的な比較対象になった

# 欠けのある区間列での時間モデルの扱いと、計算機差による値の散らばり：文献調査（2026-10-21）

問い (9)・(10) のどちらにも、直接答えている文献は見つかりませんでした。(9) で依頼者の条件（注釈のある区間だけが残り、区間の境で連番が振り直された系列）について、区間をつなぐか区間ごとに初期化するかの影響を測った研究は 0 件です。(10) で手術映像・行動分割において GPU の種類・数値精度・ライブラリ版による散らばりを seed 差と分けて測った研究も 0 件です。代わりに、判断材料になる隣接分野の測定を集めました。(9) では、連続動画で状態を持ち越すかリセットするかの比較（手術、online 行動検出）と、言語モデルで文書の境を越えた注意を遮断した比較です。(10) では、一般の画像分類で実装起因の非決定性を seed 起因と分けて測った研究です。

## TL;DR
- (9)：EgoSurgery-Phase の原論文と関連論文は、除外フレームでできた欠けをどう扱ったかを書いていません。公式配布の形式（フレーム名に元の時刻が残るか）も、公開ページからは確認できません。最も近い証拠は Rivoir ら（MedIA 2024）で、連続動画で LSTM の状態を動画全体に持ち越して評価する方式（CHE）は、窓ごとにリセットする方式（SWE）より Cholec80 の Jaccard が 66.3→70.4 でした（Table 3）。MiniROAD は、学習時のクリップ単位リセットと推論時の連続処理のずれを測っています。
- (10)：Summers & Dinneen（ICML 2021）では、CIFAR-10 の ResNet-14 で、cuDNN の非決定性だけによる精度 SD は 0.22%、初期化 seed だけによる SD は 0.23% でした（Table 1、各 100 run）。Zhuang ら（MLSys 2022）でも、top-line の精度では実装ノイズと算法ノイズがほぼ同程度でした（Table 2）。一般分野では「計算機差は seed 差と同じ桁」です。手術映像・行動分割での測定はありません。
- 提案：まず元の時刻を復元できるかを確かめます。次に「つなぐ／区間ごとに初期化する／つないで欠けの長さを与える」の 3 案を、同じ固定特徴・複数 seed・動画ごとの対比較で測ります。計算機差は seed と同じ散らばりの一要因として扱います。テスト 5 本では、Jaccard 0.02 前後の差は seed 差と区別しにくいと見込んでください。

---

## (1) 系統表

### 問い (9) の系統
| 系統 | 代表的な文献 | 現役度（どこでの話か） | 記録の件数 |
|---|---|---|---|
| 9-A 区間・欠けをつないで一系列として扱う（暗黙の既定） | R1（記載なし）、R8（区間除去） | 不明（扱いを明記した論文なし） | 3（R1, R4, R8） |
| 9-B 区間・クリップごとに状態を初期化 | MiniROAD R14、Rivoir SWE R9、Ego-Exo4D R12 | THUMOS'14 の online 行動検出では定番の基準。Cholec80 では SWE は置き換え済み（R9 Table 3） | 4（R9, R12, R14, R15） |
| 9-C 黒塗り等で時間軸を保つ | MultiBypass140 R6、OoBNet R5、ROBAN R7、AHA R16 | 手術データ配布の匿名化では定番。時間モデルへの効果の測定なし | 4 |
| 9-D 欠けの長さ・時刻を入力に与える | GRU-D R20 | 医療時系列では定番。映像の工程認識での採用は未発見 | 1 |
| 9-E 境を越えた注意を遮断（マスク） | INTRADoc R17、KORMo R18 | LLM 事前学習で新興〜定番 | 2 |
| 9-F 状態の持ち越し（stateful） | Rivoir CHE/CHT R9、Transformer-XL R19、OnlineTAS R15 | Cholec80 の online 工程認識で SOTA 級の構成要素（R9 Table 3）。言語モデルでは定番 | 4（R9, R10, R15, R19） |
| 9-G サンプリング間隔・時間分解能 | MS-TCN Table 6 R11 | 行動分割で定番の基準 | 1 |

### 問い (10) の系統
| 系統 | 代表的な文献 | 現役度（どこでの話か） | 記録の件数 |
|---|---|---|---|
| 10-A seed による差 | R22, R24, R25, R31 | 一般 ML の方法論として定番 | 4 |
| 10-B 計算機・GPU 種類による差 | Zhuang R21（P100/V100/RTX5000/T4/TPU） | 一般 ML の方法論。手術・行動分割では測定なし | 1 |
| 10-C 数値精度（fp16/bf16/TF32） | 本文で確認できたものなし | 不明 | 0 |
| 10-D ライブラリ版による差 | Pham R23 | ソフトウェア工学での方法論 | 1 |
| 10-E 並列化（GPU 数・DDP・BN 同期） | R9（BN とバッチ形状）、R21（BN の有無） | 不明（GPU 数を変えた測定は未発見） | 2 |
| 10-F データ処理（デコーダ・リサイズ・読み込み順） | Parmar R26、R21（入力順） | 生成モデル評価で定番（clean-fid） | 2 |
| 10-G 決定的実行の設定と費用 | R21（最大 746%）、R22（約 15%） | 一般 ML の方法論 | 2 |
| 10-H 再現性の総説・評価の不一致 | R27, R28, R29, R30 | 医用画像・手術の方法論 | 4 |

---

## (2) 文献ごとの記録

### 問い (9)

#### R1. EgoSurgery-Phase
[書誌]
- 著者／年／題名／掲載先／ID：Fujii, Hatano, Saito, Kajita／2024／EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos／MICCAI 2024（査読つき）／arXiv:2405.19644、DOI 10.1007/978-3-031-72089-5_18
- 読んだ範囲：本文
[近さ]
- 方向：1／視点：一人称／ドメイン：開放手術
- 課題の形：フレーム（＋視線）から 9 工程を予測／推論の規約：不明（Table 1 の TeCNO などを online で動かしたかは記載なし。GGMAE は 10 フレームのクリップを入力）
- データ規模：本文は「20 videos」と書くが、分割は 14／2／5（計 21）。注釈 27,694 フレーム／モデルの状態：事前学習後に全体を微調整
[手法の位置]
- 系統：9-A（記載なし）／現役度：EgoSurgery での基準値の出所として定番（R4 が比較）
- ベンチマーク：EgoSurgery-Phase／少数・online・一人称：少数、一人称。online は不明
[証拠]
- 比較：手法比較（Table 1）、マスク戦略だけを変えた比較（Table 3a）
- 効果量：Jaccard（macro）は TeCNO 27.3、Trans-SVNet 23.1、NETE 27.5、GGMAE 33.9（Table 1）。gaze-guided と random（0.90）で 33.9 対 30.6（Table 3a）
- 符号：改善／条件：マスク率 0.90、τ=0.5 で最良（Table 3b/3c）
- 基準の強さ：当時の代表的手法／単一要素：Table 3 は単一要素の比較
- seed・分割・検定：seed の記載なし、分割 1 つ、検定なし／追試・採用：R4
[実装]
- コード・重み：データは R2 で配布、コードの記載なし／追加データ：視線／重なり：該当なし
[要点]
- 25 fps→0.5 fps に間引き、PII を含むフレームを除外したと書いているが、除外でできた欠けを時間モデルでどう扱ったか（つないだか、区間で分けたか、時刻を残したか）は書いていない。本数の記述が 20 と 21 で食い違う。

#### R2. EgoSurgery 公式リポジトリ（Fujiry0/EgoSurgery）
- 書誌：Fujii ら／2024〜／README／GitHub（査読なし）／ID 不明／読んだ範囲：README 全文
- 近さ：方向 1／一人称／開放手術／データ配布（推論の規約・規模・状態は該当なし）
- 手法の位置：系統は該当なし／現役度は不明
- 証拠：該当なし
- 実装：Google フォームで申請するとダウンロードリンクが届く。CC BY-NC-SA 4.0。リポジトリにあるのは assets、LICENSE.txt、README.md のみ
- 要点：フレーム名に元の時刻が残っているか、除外区間の情報が配布されるかは、公開ページからは判断できない（不明）。

#### R3. EgoSurgery-Tool
- 書誌：Fujii, Saito, Kajita／2024／EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos／プレプリント／arXiv:2406.03095／読んだ範囲：本文 2 節のスニペットのみ
- 近さ：方向 1／一人称／開放手術／器具 15 種・手 4 種の bbox 検出（フレーム単位）。EgoSurgery-Phase を「21 videos、10 術式、15 時間、術者 8 人」と記載し、うち 15 本・15,437 枚に注釈
- 手法の位置・証拠・実装：不明（未読）。データは R2
- 要点：本数を 21 と明記しており、R1 本文の 20 と食い違う。欠けの扱いへの言及はない。

#### R4. SurgMotion
[書誌]
- 著者／年／題名／掲載先／ID：Wu, Holm, Chen ほか（責任著者 Zhen Lei）／2026／SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos／プレプリント（v5、2026-09-22）／arXiv:2602.05638
- 読んだ範囲：要旨、1〜3.2 節、Table 1。EgoSurgery の結果表は未読
[近さ]
- 方向：1／視点：混在／ドメイン：低侵襲・開放手術
- 課題の形：V-JEPA 系の事前学習の後、工程認識ほか 17 ベンチマーク／推論の規約：不明
- データ規模：事前学習 3,658 時間、50 ソース／モデルの状態：事前学習後に微調整
[手法の位置]
- 系統：該当なし（基盤モデル）／現役度：新興
- ベンチマーク：EgoSurgery、PitVis、CholecT50 ほか／少数・online・一人称：EgoSurgery で評価
[証拠]
- 比較：既存の最良手法と比較／効果量：EgoSurgery で F1 +14.6%、PitVis で +10.3%（要旨。表番号は未確認）
- 符号：改善／条件：不明
- 基準の強さ：基盤モデル 13 種と比較／単一要素：いいえ
- seed・分割・検定：不明／追試・採用：不明
[実装]
- コード・重み：GitHub と Hugging Face（ライセンスは不明）／追加データ：大規模動画
- 重なり：事前学習に使った SurgMotion-15M（Table 1）に「EgoSurgery、21 本、10.55 時間、Mixed」が含まれる。テスト 5 本が含まれるかは不明
[要点]
- EgoSurgery の全本数が事前学習に入っている可能性があり、漏れの疑いが残る。「10.55 時間」は原論文の 15 時間と、「Breast surgery」という分類は 10 術式という記述と、それぞれ食い違う。Hugging Face では同じ ID が「UniSurg」という題で表示されている。

#### R5. OoBNet
[書誌]
- 著者／年／題名／掲載先／ID：Lavanchy ら／2023／Preserving privacy in surgical video analysis using a deep learning classifier to identify out-of-body scenes in endoscopic videos／Scientific Reports（査読つき）／DOI 10.1038/s41598-023-36453-1
- 読んだ範囲：要旨と本文の一部
[近さ]
- 方向：2／視点：内視鏡・腹腔鏡／ドメイン：低侵襲手術
- 課題の形：フレームから体外シーンを判定／推論の規約：フレーム単位
- データ規模：社内 12 術式と、外部 2 つの多施設データ／モデルの状態：独立に学習
[手法の位置]
- 系統：9-C／現役度：匿名化の前処理として定番（R6 が採用、R7 が比較）
- ベンチマーク：社内・外部データ／少数・online・一人称：該当なし
[証拠]
- 比較：体外検出の性能／効果量：社内テストで ROC AUC 99.97%（要旨）
- 符号：該当なし／条件：体外フレームが体内に似ていると偽陰性になる
- 基準・単一要素：該当なし／seed：不明／追試・採用：R6、R7
[実装]
- コード：公開（CAMMA-public/out-of-body-detector）、ライセンスは不明／追加データ：体外注釈／重なり：該当なし
[要点]
- 「blurring or deleting」の両方を匿名化の手段として挙げているが、その後の時間モデルへの影響は測っていない。

#### R6. MultiBypass140
- 書誌：Lavanchy JL, Ramesh S, Dall'Alba D, Gonzalez C, Fiorini P, Müller-Stich BP, Nett PC, Marescaux J, Mutter D, Padoy N／2024／Challenges in multi-centric generalization: phase and step recognition in Roux-en-Y gastric bypass surgery／IJCARS 19(11):2249–2257（査読つき、オープンアクセス、2024-05-18 公開）／DOI 10.1007/s11548-024-03166-3、arXiv:2312.11250（Springer および PMC11541311 による）／読んだ範囲：データセット節のスニペット
- 近さ：方向 2／腹腔鏡／低侵襲手術／工程・ステップの予測。データは「StrasBypass70」（Strasbourg 大学病院）と「BernBypass70」（Bern の Inselspital）の 140 本で、「12 phases and 46 steps」の注釈つき／推論の規約は不明
- 手法の位置：系統 9-C／現役度は不明
- 証拠：不明（配布形式の記述のみ）
- 実装：OoBNet による検出と目視確認
- 要点：「All videos have been anonymized by blacking out the out-of-body frames」。フレームを削除せず黒塗りにして、時間軸を保っている。

#### R7. ROBAN
- 書誌：De Backer P, Simoens J, … Mottrie A ほか／2024／Privacy-proof Live Surgery Streaming: Development and Validation of a Low-cost, Real-time Robotic Surgery Anonymization Algorithm／Annals of Surgery 280(1):13–20（2024 年 7 月、査読つき）／ID 不明（PMC11161223）／読んだ範囲：スニペット
- 近さ：方向 2／ロボット内視鏡／低侵襲手術／体外判定とぼかし／online（実時間）／4 種のロボットシステムで撮影した 6 術式 63 本、496,828 画像。要旨によると「Framewise anonymization yielded an ROC AUC-score of 99.46% on unseen procedures, increasing to 99.89% after post-processing」。RTX3090 での推論時間は ROBAN 0.96 ms/frame、OoBNet 2.2 ms、IODA 0.57 ms
- 手法の位置：系統 9-C／現役度は新興
- 証拠：ROBAN と OoBNet・IODA の比較。感度は ROBAN が上、特異度・適合率は OoBNet が上。Annals of Surgery 本文によると「Postprocessing ROBAN predictions for non–real-time use with a 2-second window further boosted performance, with negative predictive value 99.9953%」。低コストの実時間構成は「estimated cost of 2000€」
- 実装：不明
- 要点：運用では削除せずにぼかす。つまり運用時の映像は連続のままである。

#### R8. Zohar ら
- 書誌：Zohar, Bar, Neimark, Hager, Asselmann／2020／Accurate Detection of Out of Body Segments in Surgical Video using Semi-Supervised Learning／MIDL 2020（PMLR v121）／ID 不明／読んだ範囲：要旨のみ
- 近さ：方向 2／腹腔鏡／低侵襲手術／秒単位で体外・非関連区間を検出／半教師ありで反復学習
- 手法の位置：系統 9-A（除去して詰める前処理）／現役度は不明
- 証拠：検出精度 97% 超。recall 97% のとき precision 83.5%（要旨）
- 要点：目的は「rapid removal and anonymization」。除去した後の時間モデルへの影響は扱っていない。

#### R9. Rivoir ら（BN の落とし穴、状態の持ち越し）
[書誌]
- 著者／年／題名／掲載先／ID：Rivoir, Funke, Speidel／2024／On the Pitfalls of Batch Normalization for End-to-End Video Learning: A Study on Surgical Workflow Analysis／Medical Image Analysis 94:103126（査読つき）／arXiv:2203.07976、DOI 10.1016/j.media.2024.103126
- 読んだ範囲：要旨は自分で確認。表の数値は、arXiv v5 の本文・付録を読んだサブエージェントの報告による
[近さ]
- 方向：2／視点：腹腔鏡（GTEA と 50Salads も）／ドメイン：低侵襲手術、非医療
- 課題の形：フレーム列から工程を予測（CNN-LSTM）／推論の規約：online
- データ規模：Cholec80 80 本、7 工程／モデルの状態：end-to-end（一部凍結の設定あり）
[手法の位置]
- 系統：9-B（SWE：系列ごとにリセットし、滑り窓で評価）、9-F（CHE：評価時に動画全体へ持ち越す。CHT：学習時も時刻順のバッチで、勾配を切った状態を持ち越す）
- 現役度：Cholec80 の online 工程認識で SOTA 級（Table 3。R10 が言及）
- ベンチマーク：Cholec80、AutoLaparo、CATARACTS、GTEA、50Salads／少数・online・一人称：online
[証拠]
- 比較 1：ResNet-BN E2E 4×16 で、評価時の扱いだけを SWE から CHE に変更
- 効果量 1：Accuracy 86.6→89.3、Jaccard 66.3→70.4、relaxed Jaccard 73.1→77.5（Table 3、32/8/40 分割）
- 比較 2：1×64 で CHE と CHT／効果量 2：video-wise 精度は ConvNeXt 89.5→92.3、GN 89.3→90.5、BN 59.7→55.6（Table A.7、40/8/32 分割）
- 符号：CHE は改善。CHT は BN-free では改善、BN では悪化
- 条件：BN で 1×64 にすると崩れる（SWE 57.2）。FrozenBN は lr 1e-5 で CHT が 39.8 に崩れる（Table A.9）。GTEA と 50Salads でも、GN と ConvNeXt では CHT が CHE を上回る（Table B.10/B.11）
- 基準の強さ：2 段の TeCNO 再実装は 89.4±0.8（Table A.7）／単一要素：はい
- seed・分割・検定：各 3 run（seed 値の記載なし）、分割 1 つ、検定なし／追試・採用：R10
[実装]
- コード：GitLab（nct_tso_public/pitfalls_bn）、ライセンスは不明／追加データ：不要／重なり：該当なし
[要点]
- 連続動画の中では、リセットより持ち越しのほうが一貫して良い（BN-free の場合）。欠けのある区間列については測っていない。本文が同じ結果を「Fig. 2b」と「Fig. 3」の両方で参照しており、図番号が食い違う。

#### R10. SurgicalMamba
- 書誌：著者は未確認／2026／SurgicalMamba: Dual-Path SSD with State Regramming for Online Surgical Phase Recognition／プレプリント／arXiv:2605.14889／読んだ範囲：関連研究と付録 H のスニペット
- 近さ：方向 2／腹腔鏡ほか／低侵襲手術／online 工程認識（SSM）／7 データセット（HeiCo は 30 本）
- 手法の位置：系統 9-F／現役度は新興
- 証拠：HeiCo で Jaccard +3.3 pp（Table 7）。Cholec80 の動画ごとの Jaccard SD は 8.1（relaxed）、11.5（strict）。「margins are widest on the smallest and most domain-shifted sets, and narrowest where … the test split is small」
- 実装：不明
- 要点：手術の online 工程認識で、状態を持ち越す設計が現役であることを示す。

#### R11. MS-TCN（時間分解能）
[書誌]
- 著者／年／題名／掲載先／ID：Abu Farha, Gall／2019／MS-TCN: Multi-Stage Temporal Convolutional Network for Action Segmentation／CVPR 2019／arXiv:1903.01945
- 読んだ範囲：Table 6 と Table 7（スニペット）
[近さ]
- 方向：4／視点：三人称（50Salads）／ドメイン：非医療
- 課題の形：フレーム特徴から行動ラベル／推論の規約：offline
- データ規模：50 本／モデルの状態：特徴は凍結
[手法の位置]
- 系統：9-G／現役度：50Salads・GTEA・Breakfast で定番の基準（arXiv:2205.13425 Table 1 で比較対象）
- ベンチマーク：50Salads／少数・online・一人称：少数
[証拠]
- 比較：同じ MS-TCN で入力を 1 fps と 15 fps にしたもの（設定だけを変更）
- 効果量：F1@10 77.8 と 76.3、F1@50 64.0 と 64.5、Edit 70.7 と 67.9、Acc 78.6 と 80.7（Table 6）
- 符号：1 fps では Edit と F1@10 が改善し、Acc は悪化／条件：著者は「過分割は減るが、境界の位置精度と短い区間を失う」と解釈
- 基準の強さ：当時の SOTA／単一要素：はい／seed：記載なし／追試・採用：MS-TCN++ Table 14（arXiv:2006.09220）
[実装]
- コード：公開
[要点]
- 間隔を変えるだけで、Edit・F1 と Acc が逆向きに動く。欠けの影響を推す手がかりになる（欠けそのものの測定ではない）。

#### R12. Ego-Exo4D（keystep）
- 書誌：Grauman ら／2024／Ego-Exo4D: Understanding Skilled Human Activity from First- and Third-Person Perspectives／CVPR 2024／ID 不明（CVF open access）／読んだ範囲：5.2 節のスニペットと公式ドキュメント
- 近さ：方向 3／一人称（学習時は三人称も使用）／非医療。課題は (a) trimmed のクリップから 689 keystep を分類（クリップ単位）、(b) ストリームで毎フレーム 5 fps の keystep 予測（online）
- 手法の位置：系統 9-B／現役度は、Ego-Exo4D keystep の公式基準として定番（arXiv:2506.01102、arXiv:2506.00827 が使用）
- 証拠：数値は未読
- 要点：一人称の主要な手順認識ベンチマークは、区間を切り出したクリップを独立に扱う形式で、区間の境を越えた文脈の効果を測る設計になっていない。

#### R13. Ego-METAS
- 書誌：著者は未確認／2026／Ego-METAS: Egocentric online Multimodal Energy-efficient Temporal Action Segmentation benchmark／プレプリント／arXiv:2606.02246／読んだ範囲：付録 A.2 のスニペット
- 近さ：方向 3／一人称／非医療／online 行動分割
- 手法の位置：該当なし／新興
- 証拠：test 注釈が非公開のため、validation を test に転用し、学習データを 80:20 に分けた。シナリオごとに学習して平均する
- 要点：欠けやクリップの扱いは、読んだ範囲では記載がない。

#### R14. MiniROAD
[書誌]
- 著者／年／題名／掲載先／ID：An, Kang, Han, Yang, Kim／2023／MiniROAD: Minimal RNN Framework for Online Action Detection／ICCV 2023／DOI 10.1109/ICCV51070.2023.00949（arXiv ID は見つからず）
- 読んだ範囲：本文と補遺（サブエージェントの報告）
[近さ]
- 方向：4／視点：三人称／ドメイン：非医療
- 課題の形：フレーム特徴から毎時刻の行動を予測（GRU）／推論の規約：online
- データ規模：THUMOS'14、TVSeries、FineAction／モデルの状態：特徴は凍結
[手法の位置]
- 系統：9-B とその是正／現役度：THUMOS'14 で定番の基準（2024 年以降の比較表は未確認のため、厳密には不明寄り）
- ベンチマーク：THUMOS'14 ほか／少数・online・一人称：online
[証拠]
- 比較 1：損失の重みを一様から、クリップの最終時刻だけにかけるステップ関数へ（状態のリセットは変えない）／効果量 1：mAP 66.4→71.8（Table 4a/4b、Kinetics 特徴）
- 比較 2：ステップ関数と、動画全体で学習（動画内でリセットしない）／効果量 2：THUMOS Kinetics 71.8 と 72.0、THUMOS Anet 69.3 と 69.6、TVSeries Anet 88.5 と 88.3、FineAction 37.1 と 38.0（補遺 Table 1）
- 符号：比較 1 は改善、比較 2 はほぼ差なし（差は 0.9 以内）／条件：クリップ長 32 秒で頭打ち（Fig. 4）。動画全体での学習はバッチを組めず、勾配の分散が大きい
- 基準の強さ：当時の Transformer 系 SOTA／単一要素：はい／seed：run 数・分散の記載なし／追試・採用：R15 が言及
[実装]
- コード：GitHub（jbistanbul/MiniROAD）
[要点]
- 「学習はクリップごとにゼロ初期化、推論は連続処理」というずれが性能を下げることを定量的に示している。初期化直後の予測に損失をかけないだけで、このずれはほぼ解消した。ページ番号が CVF 版（10341–10350）と IEEE CSDL 版（10307–10316）で異なる。

#### R15. OnlineTAS
- 書誌：Zhong, Ding, Yao／2024／OnlineTAS: An Online Baseline for Temporal Action Segmentation／NeurIPS 2024／arXiv:2411.01122／読んだ範囲：本文の一部（スニペット）。数値は未読
- 近さ：方向 4／三人称ほか／非医療（手順動画）／online 行動分割（ストライド 1、適応メモリ）
- 手法の位置：系統 9-F（動画ごとのメモリ）／新興
- 証拠：クリップ長の影響（Table 5、数値は未読）。長いクリップは segment 指標を改善するが、窓が大きすぎると短い行動が薄まる
- 要点：メモリは「per-video」で、動画の境でリセットすることが前提。区間の境の扱いは対象外。

#### R16. AHA
- 書誌：著者は未確認／2025／AHA — Predicting What Matters Next: Online Highlight Detection Without Looking Ahead／プレプリント／arXiv:2509.16421／読んだ範囲：付録 E.1 のスニペット
- 近さ：方向 4／一般映像／online ハイライト検出
- 手法の位置：系統 9-C（学習時の blackout 拡張）／新興
- 証拠：動画の 5〜20% の区間を劣化させる（全画素ゼロを含む）。連続する blackout は X フレーム（例：1 fps で 5）まで。効果量は未読
- 要点：欠損への頑健性のために、黒塗りを学習時の拡張として使う例。

#### R17. Zhao ら（INTRADoc）
[書誌]
- 著者／年／題名／掲載先／ID：Zhao, Qu, Staniszewski, Tworkowski, Liu, Miłoś, Wu, Minervini／2024／Analysing The Impact of Sequence Composition on Language Model Pre-Training／ACL 2024／arXiv:2402.13991
- 読んだ範囲：本文（1〜4.2 節、Table 1〜4）
[近さ]
- 方向：5／視点：該当なし／ドメイン：非医療（言語）
- 課題の形：文書を詰めた系列で次トークンを予測／推論の規約：因果的
- データ規模：150B トークン、1.3B パラメータ、文脈長 2K と 8K／モデルの状態：一から学習
[手法の位置]
- 系統：9-E（INTRADoc）、9-A（MIXChunk）、関連文書を詰める BM25Chunk／現役度：新興〜定番（R18 が採用）
- ベンチマーク：SlimPajama ほか／少数・online・一人称：該当なし
[証拠]
- 比較：同じ文書集合で、詰め方とマスクだけを変える
- 効果量：平均 PPL は 2K で 9.172 と 8.410、8K で 9.065 と 8.079（Table 1）。ICL 平均は 2K で 63.54 と 70.52、8K で 62.43 と 71.23（Table 2）。閉じた QA の EM は 8K で 7.99 と 10.99（Table 3）
- 符号：遮断すると改善／条件：関連文書を詰めた BM25Chunk は、2K の ICL で 70.91 と INTRADoc（70.52）に並ぶ。遮断の費用は実行時間 +4%
- 基準の強さ：標準の詰め方／単一要素：はい
- seed・分割・検定：事前学習は各 1 回。Table 2 の ± はデモ選択 16 seed による散らばり。検定なし／追試・採用：R18
[実装]
- コード：GitHub（yuzhaouoe/pretraining-data-packing）
[要点]
- 無関係な系列をつないで境を越えて文脈を引くと害になる。関連する系列なら害は小さい。

#### R18. KORMo
- 書誌：著者は未確認／2025／KORMo: Korean Open Reasoning Model for Everyone／プレプリント／arXiv:2510.09426／読んだ範囲：2.3 節のスニペット
- 近さ：方向 5／言語／系列を詰めた事前学習
- 手法の位置：系統 9-E／新興
- 証拠：同じ proxy モデルで 4 種のマスクを比較。intra-doc 44.48% と causal 43.38%（Table 3）。seed は不明
- 要点：著者以外による R17 の小規模な再現（差 1.1 pt）。

#### R19. Transformer-XL
- 書誌：Dai ら／2019／Transformer-XL: Attentive Language Models Beyond a Fixed-Length Context／ACL 2019／arXiv:1901.02860／読んだ範囲：スニペットのみ（ablation の数値は未読）
- 近さ：方向 5／言語モデル／因果的
- 手法の位置：系統 9-F（直前セグメントの状態を勾配を止めて再利用）／定番（RMT arXiv:2207.06881 が比較対象とする）
- 証拠：手法比較では WikiText-103 の PPL 20.5→18.3（Table 1）。相対位置符号化がないと、状態の再利用は「temporal confusion」を招く
- 要点：状態を持ち越すには、時刻の表現との整合が要る。連番を振り直した区間列で持ち越すことは、この混乱に相当する。

#### R20. GRU-D
- 書誌：Che, Purushotham, Cho, Sontag, Liu／2018／Recurrent Neural Networks for Multivariate Time Series with Missing Values／Scientific Reports／DOI 10.1038/s41598-018-24271-9、arXiv:1606.01865／読んだ範囲：要旨とスニペット（本文の取得は 429 エラーで失敗）
- 近さ：方向 5／その他の医療（ICU 時系列）／欠けのある時系列の分類／因果的
- 手法の位置：系統 9-D（mask と経過時間 δ で入力と隠れ状態を減衰させる）／医療時系列で定番（直近の比較表は未確認）
- 証拠：GRU-Mean、GRU-Forward、GRU-Simple、GRU-D の比較（Figure 4、数値は未読）。欠けを使わない GRU-Mean と GRU-Forward はほぼ同じ。GRU-D は 24 時間を超える系列で GRU-Simple を上回る
- 実装：第三者実装あり（subramen/GRU-D）
- 要点：欠けの長さを入力に与える方法の原型。映像の工程認識で除外区間の長さを入力に与えた研究は見つからなかった。

### 問い (10)

#### R21. Zhuang ら（ツール起因の乱雑さ）
[書誌]
- 著者／年／題名／掲載先／ID：Zhuang, Zhang, Song, Hooker／2022／Randomness in Neural Network Training: Characterizing the Impact of Tooling／MLSys 2022／arXiv:2106.11872
- 読んだ範囲：本文（1〜5 節）
[近さ]
- 方向：5（7 の要素を含む）／ドメイン：非医療／課題の形：画像分類／モデルの状態：一から学習
[手法の位置]
- 系統：10-B、10-F、10-G／現役度：再現性研究の定番の参照文献（arXiv:2304.01910 などが引用）
- ベンチマーク：CIFAR-10/100、ImageNet／少数・online・一人称：該当なし
[証拠]
- 比較：同じ GPU 上で ALGO（seed のみ）、IMPL（seed を固定し、ハードとソフトの非決定性のみ）、ALGO+IMPL を、各 10 run（ImageNet は 5 run）
- 効果量：V100 の ResNet-18 CIFAR-10 は 93.32±0.17、93.44±0.05、93.41±0.13。V100 の ResNet-50 ImageNet は 76.58±0.10、76.61±0.10、76.60±0.05（Table 2）。churn は ImageNet で IMPL 14.68%、ALGO 14.89%（3.1 節）。決定的実行による時間増は最大で P100 746%、V100 241%、T4 196%（Fig. 8）
- 符号：top-line の SD は 1% 未満で小さい。churn とクラス別精度では IMPL も ALGO と同程度
- 条件：BN のない小さな CNN は散らばりが大きく、BN を入れると SD が 0.86%→0.30%（Fig. 2）。CUDA コアが多い V100 で発散が大きい。TPU は churn が小さいが SD は変わらない（Fig. 5）。入力順が変わると浮動小数の集約順が変わり、TPU でも非決定になる（Fig. 6）
- 単一要素：はい／seed：10 run、検定なし／追試・採用：多数
[実装]
- コード：GitHub（usyd-fsalab/NeuralNetworkRandomness）。TF 2.4.1、CUDA 11、cuDNN 8 で固定（版の差は測っていない）
[要点]
- 同じ GPU 上での実装ノイズは、seed ノイズと同じ桁。GPU を替えたときの平均の差は Table 2 から読めるが（SmallCNN の ALGO+IMPL は P100 62.28、RTX5000 62.24、V100 62.03）、検定はない。分散学習は対象外と明記。3.1 節の「ResNet-10 trained on ImageNet」は、Table 2 では ResNet-50 で、誤記とみられる。

#### R22. Summers & Dinneen
[書誌]
- 著者／年／題名／掲載先／ID：Summers, Dinneen／2021／Nondeterminism and Instability in Neural Network Optimization／ICML 2021／arXiv:2103.04514
- 読んだ範囲：本文（1〜4.1 節、Table 1・2）
[近さ]
- 方向：5（7 の要素を含む）／ドメイン：非医療／課題の形：ResNet-14 CIFAR-10、QRNN PTB／モデルの状態：一から学習
[手法の位置]
- 系統：10-A、10-G／現役度：定番の参照文献
[証拠]
- 比較：乱雑さの源を 1 つだけ変え、他は固定して各 100 run
- 効果量：精度 SD は初期化 0.23±0.02、データ順 0.25±0.02、拡張 0.23±0.02、cuDNN 0.22±0.01、すべて 0.26±0.02（Table 1）。PTB の PPL SD は初期化 0.20、すべて 0.18（Table 2）
- 符号：どの源も同程度（相対差 20% 以内）／条件：初期値の 1 ビットの変化でも、すべての源を合わせたのとほぼ同じ散らばりになる（4.1 節）。cuDNN の決定的実行は約 15% 遅い。cuDNN は seed で固定できず、オンかオフしか選べない
- 単一要素：はい／seed：各 100 run、V100 2 枚、PyTorch
[実装]
- コード：GitHub（ceciliaresearch/nondeterminism_instability）
[要点]
- 計算機由来の微小な差も、学習の不安定性で seed 差と同じ大きさまで増幅される。計算機差だけを消しても、散らばりは減らない。

#### R23. Pham ら
- 書誌：Pham, Qian, Wang, Lutellier, Rosenthal, Tan, Yu, Nagappan／2020／Problems and Opportunities in Training Deep Learning Software Systems: An Analysis of Variance／ASE 2020／ID 不明（IEEE Xplore 9286042）／読んだ範囲：要旨のみ
- 近さ：方向 5／非医療／画像分類（3 データセット × 6 ネットワーク）
- 手法の位置：系統 10-D／ソフトウェア工学の参照文献（後続ツール DEVIATE）
- 証拠：seed を固定した同一学習の繰り返しで、実装レベルの要因だけで、精度差が最大 2.9%、クラス別精度差が最大 52.4%、収束時間の差が最大 145.3%（要旨）。TensorFlow、CNTK、Theano と cuDNN の、評価したすべての版で分散が出た
- 要点：版を変えても非決定性は残る。「2.9%」は最大値であって典型値ではない。

#### R24. Bouthillier ら
- 書誌：Bouthillier ら／2021／Accounting for Variance in Machine Learning Benchmarks／MLSys 2021／arXiv:2103.03098／読んだ範囲：要旨とスニペット
- 近さ：方向 6／医療を含む 5 課題
- 手法の位置：系統 10-A／評価方法論の定番
- 証拠：各分散源の大きさを、ブートストラップによる分散に対する割合で示す（Figure 1、数値は未読）。データ分割、初期化、ハイパーパラメータ選択が結果に強く影響する。多くの分散源を乱数化した推定量は、計算量 51 分の 1 で理想的な推定量に近づく（要旨）。初期化だけを変える推定量 FixHOptEst(k, Init) が最も悪い
- 要点：seed だけを変える評価は、データ分割による分散を見落とす。分割が 1 つでテスト 5 本の EgoSurgery では、ここが最大の分散源になりうる。

#### R25. On the Variance of Neural Network Training with respect to Test Sets and Distributions
- 書誌：Keller Jordan（単著）／2024（v4、2024-06-10）／同題／プレプリント（cs.LG）／arXiv:2304.01910。要旨によると「standard CIFAR-10 and ImageNet trainings have little variance in performance on the underlying test-distributions」で、各 run は「make approximately independent errors on their test-sets」／読んだ範囲：スニペットのみ
- 近さ・位置：方向 5／CIFAR-10／系統 10-A
- 証拠：1 epoch の学習で、3 つの源を全部変えると精度 SD 1.33%。1 つだけ変えると分散は 25〜40% 小さい（付録 D.1）。学習の途中で小さな摂動を与えると、最終結果が大きく変わる（Figure 12）
- 要点：源を 1 つ固定しても、分散は一部しか減らない。R22 と整合する。

#### R26. Parmar ら
- 書誌：Parmar, Zhang, Zhu／2022／On Aliased Resizing and Surprising Subtleties in GAN Evaluation／CVPR 2022／arXiv:2104.11222、DOI 10.1109/CVPR52688.2022.01112／読んだ範囲：スニペットと公式 README
- 近さ・位置：方向 5（データ処理）／非医療／FID による評価／系統 10-F／定番（clean-fid）
- 証拠：同じ画像を、各ライブラリの bicubic と PIL-bicubic でリサイズして比較。OpenCV、PyTorch、TF と PIL の間で FID が 6 以上。PIL の他のフィルタどうしでは 0.75 以下（README の表）。OpenCV、TF、PyTorch はフィルタ幅が固定で、エイリアスが出る
- 実装：GitHub（GaParmar/clean-fid）
- 要点：前処理の実装差だけで、評価値が手法間の差と同じ桁で動く。分類精度への影響は測っていない。

#### R27. Renard ら
- 書誌：Renard, Guedria, De Palma, Vuillerme／2020／Variability and reproducibility in deep learning for medical image segmentation／Scientific Reports 10:13724／DOI 10.1038/s41598-020-69920-0／読んだ範囲：要旨と図の説明
- 近さ・位置：方向 6／その他の医療／総説／系統 10-H／参照文献（arXiv:2608.29677 などが引用）
- 証拠：変動源を、データセット、構造、最適化、ハイパーパラメータ、実装・基盤の 5 つに分類。数値の測定はない
- 要点：「実装・基盤」を独立した変動源として挙げているが、大きさは測っていない。

#### R28. Gundersen ら
- 書誌：Gundersen ら／2022／Sources of Irreproducibility in Machine Learning: A Review／プレプリント／arXiv:2204.07610／読んだ範囲：参考文献部分のスニペットのみ
- 位置：方向 6／系統 10-H／現役度は不明
- 証拠：参考文献に、フレームワークの版と再現性を扱った論文（Machine Learning and Knowledge Extraction 4(4), 2022）がある。ただしその論文は未確認で、記録は作らない
- 要点：版の差を扱った文献を探す入口として確認しただけ。

#### R29. Funke ら（Metrics Matter）
- 書誌：Funke, Rivoir, Speidel／2023／Metrics Matter in Surgical Phase Recognition／技術報告（プレプリント）／arXiv:2305.13961／読んだ範囲：5 節のスニペット（前回の調査で本文を確認済み）
- 近さ・位置：方向 2、6／腹腔鏡／online の結果を整理／系統 10-H、10-A／Cholec80 の評価規約として定番
- 証拠：seed による Jaccard の揺れ .017（Table 9、前回確認）。多くの手法でコードが公開されておらず、再現が難しい。変動の指標（SD_V、SD_P、SD_R）や Jaccard・F1 の報告が欠けていることが多い
- 要点：計算機差以前に、評価規約の違いと変動の指標の欠落で、比較が成り立たなくなっている。

#### R30. CPKD
- 書誌：著者は未確認／2025／CPKD: Clinical Prior Knowledge-Constrained Diffusion Models for Surgical Phase Recognition in Endoscopic Submucosal Dissection／プレプリント／arXiv:2507.03295／読んだ範囲：比較節のスニペット
- 近さ・位置：方向 2／内視鏡／系統 10-H／新興
- 証拠：TeCNO と Trans-SVNet は著者提供の重みで再実装し、他の手法は原著の値を転記（Table 3）。両者の値の差は未読
- 要点：再実装値と転記値が同じ表に混在する慣行の例。

#### R31. C2F-TCN
- 書誌：Dipika Singhania, Rahul Rahaman, Angela Yao（National University of Singapore。arXiv PDF の表紙で確認）／2022／C2F-TCN: A Framework for Semi and Fully Supervised Temporal Action Segmentation／プレプリント／arXiv:2212.11078／読んだ範囲：付録 B.5 のスニペット
- 近さ・位置：方向 4／三人称、一人称（GTEA）／offline／系統 10-A／50Salads・Breakfast で定番の基準（arXiv:2205.13425 Table 1）
- 証拠：4 seed の平均±SD（Table T22、数値は未読）。「For the smallest GTEA dataset, the deviation in the results is higher」
- 要点：行動分割でも、動画の少ないデータでは seed 差が大きい。

---

## (3) 探したが見つからなかったもの

- EgoSurgery-Phase を使った論文で、欠けの扱いを明記したもの：検索語「EgoSurgery-Phase phase recognition open surgery egocentric」「EgoSurgery-Phase benchmark phase recognition results 2025」「SurgMotion arXiv 2602.05638」。約 25 件を確認し、4 件（R1〜R4）を読んだ。0 件。EgoSurgery-HTS（arXiv:2503.18755）は要旨の断片しか見られず、未確認。
- 配布データのフレーム名・元の時刻：README に記載なし。申請制のため確認できず、不明。
- 黒塗りと削除を、時間モデルの性能で比べた研究：検索語「out-of-body detection anonymization laparoscopic video OoBNet」で約 8 件を確認。0 件。
- 欠けの中にある工程境界による Edit・F1@k のゆれ、および欠けが RSD・ProTAS の経過時間をずらす問題：専用の検索は予算不足で実施できず、関連検索の範囲では 0 件。
- 手術映像・行動分割で、GPU・精度・版による散らばりを seed 差と分けた研究：検索語「MS-TCN reproduce results different GPU variance temporal action segmentation seeds」「surgical phase recognition reproducibility reimplementation results differ reported Cholec80 benchmark」で約 18 件を確認。0 件。
- 混合精度、DDP の GPU 数、BN 同期、worker 数、動画デコーダ（ffmpeg・decord・PyAV・OpenCV）の影響：本文で確認できたものは 0 件。R21 は分散学習を対象外と明記。
- チャレンジ（EndoVis、PitVis、SurgVU、HeiChole）での再実行差、GitHub issue での環境差：0 件（GitHub issue の検索は未実施）。
- 方向 7 の独立検索：検索予算（18 回）を使い切ったため実施できなかった。否定的・中立的な所見は既読の文献から拾った（R9 の BN での CHT の悪化、R14 の動画全体学習でほぼ差なし、R17 の BM25Chunk が INTRADoc と同等、R21 の top-line への影響の小ささ）。

---

## (4) 未検証の組み合わせ

1. 連番を振り直した区間列 × 因果 TCN（TeCNO 型） × 「つなぐ／区間ごとに初期化／つないで欠けの長さを与える」。R9 は連続動画の LSTM、R14 は連続動画の GRU、R17 は文書列の Transformer を扱っており、この組み合わせは誰も測っていない。
2. Δt の埋め込み（R20 の系統） × 映像の工程認識。
3. 黒塗りで保った時間軸（R6） × 時間モデルで黒塗りフレームを入力するかマスクするか。
4. 欠けのある系列での学習・評価 × 連続映像での運用、のずれ。R14 はクリップと連続のずれを測ったが、欠けの有無によるずれは測っていない。
5. R17 の「関連性が高ければ境を越えても害が小さい」を、同じ手術の中の区間で確かめたもの。
6. GPU・精度・版による散らばり × 手術工程認識・行動分割 × テスト 5 本。
7. 2 段階の学習（抽出器の微調整 → 特徴の保存 → 時間モデル）で、計算機差がどちらの段で生じるかの分解。TUNeS の 5×5 設計は seed だけを変えている。
8. GPU 数による BN の統計 × 抽出器の微調整 × 下流の時間モデルの散らばり。

---

## (5) 検索記録（検索日はすべて 2026-10-21。各検索で上位 8〜10 件を確認）

- #1 EgoSurgery-Phase phase recognition open surgery egocentric（問い 9、方向 1）→ R1, R2
- #2 Randomness in Neural Network Training… Tooling（10、方向 5）→ R21, R25
- #3 Analysing The Impact of Sequence Composition… intra-document causal masking（9、方向 5）→ R17, R18
- #4 online temporal action segmentation OnlineTAS memory reset video boundary（9、方向 4）→ R15
- #5 out-of-body detection anonymization laparoscopic video OoBNet（9、方向 2）→ R5〜R8
- #6 EgoSurgery-Phase benchmark phase recognition results 2025（9、方向 1）→ R3, R10
- #7 SurgMotion arXiv 2602.05638（9、方向 1）→ R4
- #8 online action detection robustness frame drop missing frames streaming video（9、方向 4）→ R16
- #9 Renard Variability and reproducibility… Scientific Reports 2020（10、方向 6）→ R27
- #10 GRU-D… missing values time interval decay（9、方向 5）→ R20
- #11 Transformer-XL segment-level recurrence ablation state reuse（9、方向 5）→ R19
- #12 MS-TCN reproduce results different GPU variance… seeds（10、方向 4）→ R11, R31
- #13 Pham Problems and Opportunities… Analysis of Variance（10、方向 5）→ R23, R28
- #14 Bouthillier Accounting for Variance…（10、方向 5・6）→ R24
- #15 surgical phase recognition reproducibility reimplementation… Cholec80（10、方向 2）→ R29, R30
- #16 On Aliased Resizing and Surprising Subtleties in GAN Evaluation（10、方向 5）→ R26
- #17 Rivoir pitfalls batch normalization… Cholec80（9・10、方向 2）→ R9, R10
- #18 online procedural step recognition egocentric… Ego-Exo4D keystep（9、方向 3）→ R12, R13
- サブエージェント：MiniROAD 本文と補遺、Rivoir らの付録表（9、方向 4・2）→ R14、R9 の数値

方向ごとの記録件数：
- 問い (9)：方向 1 は 4 件、方向 2 は 6 件、方向 3 は 2 件、方向 4 は 4 件、方向 5 は 4 件。方向 6 は専用の記録 0 件（R9、R11 の中で扱った）。方向 7 は独立検索 0 回で、否定的な所見 3 件（R9、R14、R17 の中）。
- 問い (10)：方向 1 は 0 件（#1・#6・#7 の範囲で該当なし）、方向 2 は 3 件（R9、R29、R30）、方向 3 は 0 件（専用の検索は未実施）、方向 4 は 1 件（R31）、方向 5 は 6 件（R21〜R23、R25、R26、R28）、方向 6 は 2 件（R24、R27）。方向 7 は独立検索 0 回で、中立的な所見 2 件（R21、R22）。

---

## (6) あなたの解釈と提案（ここだけが解釈です）

### 問い (9) への答え
- 欠けのある区間列で境を越えるか初期化するかを測った研究はなく、EgoSurgery-Phase を使った論文もこの点を書いていません（R1、R3、R4）。
- 隣接分野の証拠は二方向に分かれます。連続動画の中では、状態を持ち越すほうが良い（R9 で Jaccard +4.1 pt、R14 ではリセットのずれが mAP を最大 5.4 pt 下げる）。一方、無関係な系列をつなぐと害になり、関連する系列なら害は小さい（R17）。
- EgoSurgery の区間は同じ手術の一部で、間が抜けているだけです。したがって「文脈を引くこと自体は害になりにくいが、欠けによって時刻がずれる」と考えるのが妥当です。R19 の「位置の表現と整合しない状態の再利用は時刻の混乱を招く」がこれにあたります。

### 考慮されていない可能性がある前提
1. 元の時刻を復元できれば、Δt を入力に与える（R20）か、黒塗りで時間軸を戻す（R6）ことができます。復元できなければ「つなぐ」か「分ける」しかありません。まずデータの中身を確認し、記載がなければ著者に問い合わせてください（R2）。
2. 評価も欠けのある系列で行われます。工程の境界が欠けの中にあると、つないだ系列上での境界の時刻が実時間とずれます。R11 を踏まえると、つなぎ方を変えたときには Jaccard より Edit・F1 のほうが大きく動くと予想されます（未検証）。
3. 運用では連続映像が流れます（R7）。因果 TCN の受容野が覆う実時間の幅が、学習時と運用時で変わります。これは R14 が測ったずれと同じ型です。
4. 0.5 fps では 1 フレームが 2 秒にあたるため、数分単位の除外は、受容野の中に大きな時間の跳びを生みます。
5. SurgMotion などの外部特徴を使う場合は、テスト 5 本が事前学習データに含まれていないかを確認してください（R4）。

### 問い (10) への答え
- 手術映像・行動分割では測定がありません。一般の画像分類では、同じ GPU 上の実装ノイズでも seed ノイズと同じ桁で（R22、R21）、GPU を替えたときの平均値の差もその範囲に収まる程度でした（R21 Table 2、検定なし）。
- R22 の「1 ビットの違いでも、すべての源を合わせたのと同じ散らばりになる」から、GPU・精度・版の違いは「seed をもう 1 つ振ること」とほぼ同じに扱えます。
- 一方、前処理の実装差は系統的なずれであり、seed を増やしても平均化されません（R26）。

### EgoSurgery で次に試す価値がある手順（優先順）
1. **元の時刻を復元できるか確認する**（R1、R2、R20）。以降の選択肢がこれで決まります。
2. **特徴を一度だけ抽出して保存し、デコーダ・リサイズ・版・GPU 数を記録・固定する**（R21、R22、R26）。時間モデルの比較から、抽出器の散らばりを切り離せます。
3. **区間の扱いを 3 案で比べる**（R9、R14、R17、R19、R20）。(a) つなぐ。(b) 区間ごとに初期化する（因果 TCN の受容野を区間の頭でゼロパディングし、境を越える畳み込みを遮断する）。(c) つないだうえで、直前フレームからの実時間の間隔、あるいは区間頭フラグを特徴に加える。加えて R14 にならい、区間頭の数フレームでは損失の重みを 0 にする変種も、安価に試せます。
4. **評価を二通りで報告する**（R11、R29）。区間ごとと、つないだ動画単位です。さらに、欠けの中に工程の境界がある箇所の周辺を除いた Edit・F1 も報告します。
5. **seed を 5 以上とし、テスト 5 本で動画ごとの対比較を行う**（R22、R24、R29、R31）。seed 間と動画間の SD を両方報告してください。seed だけで Jaccard が .005〜.018 動くことを踏まえると、0.02 未満の差は主張しにくいと考えます。可能なら、学習と検証を入れ替えた交差検証で、分割による分散（R24）も見積もってください。
6. **計算機差は確認にとどめる**（R9、R21、R22）。同じ seed の組を 2 種類の GPU（または TF32 のオンとオフ）で 1 度ずつ回し、差が seed 間の SD の範囲に入るかだけを見ます。決定的実行は再現の確認には役立ちますが、計算時間が増え（最大 746%、あるいは約 15%）、しかも散らばりは減りません。抽出器を微調整する段では、BN の統計が GPU 数とバッチ構成に依存するので、これらを固定してください。

| 手順 | 根拠となる記録 |
|---|---|
| 1 時刻の復元確認 | R1, R2, R20 |
| 2 特徴の固定と前処理の記録 | R21, R22, R26 |
| 3 区間の扱い 3 案 | R9, R14, R17, R19, R20 |
| 4 評価の二重報告 | R11, R29 |
| 5 seed と対比較の設計 | R22, R24, R29, R31 |
| 6 計算機差の確認と BN | R9, R21, R22 |
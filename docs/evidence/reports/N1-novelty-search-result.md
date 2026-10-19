# N1 先行研究の照合結果（2026-10-18）：凍結した術具検出と工程認識の間で予測を受け渡す研究

この検索手段・検索語・範囲では、E1・E2・E3 が揃う研究も、E1・E2・E5 が揃う研究も確認できなかった。一致の度合いがいちばん近かった手術映像の文献は、どれも片方向だけを扱っている。工程の予測を術具の分割へ渡す研究（ToolSeg、MICCAI 2025。§2.1 で既知）と、術具の予測を工程認識へ渡す研究（Sahu ほか 2020、DeepPhase、YOLOv8 の出力を DNN へ渡す抄録）である。一般の機械学習では、E1（凍結した二つのモデルと小さな学習可能な層）と E2（予測を入力にする結合）は、それぞれ別の系統の手法としてすでにある。

## TL;DR

- 片方向の研究は複数あった。D→P では Sahu ほか 2020、DeepPhase、YOLOv8→DNN の抄録が、P→D では ToolSeg が該当する。一方、同じ研究の中で凍結した二つのモデルを予測だけでつなぎ、両方向を比べたもの（E1・E2・E3）は、この検索手段・検索語・範囲では確認できなかった。予測と正解を入力として比べたもの（E4 に近い比較）は二件確認した。ToolSeg（工程の予測と正解）と EndoNet（術具の正解の二値信号と学習した特徴）である。
- 一般の機械学習では、E1 と E2 は別々の系統としてすでにある。model stitching は凍結した二つのモデルの間に小さな学習可能な層を置くが、渡すのは中間表現である。Taskonomy は凍結した encoder の上に小さな readout を置き、方向つきの転移を測るが、これも表現を渡す。stacking は予測を結合器に渡すが、対象は同じ課題である。cross-task consistency と PAD-Net/MTI-Net は、ある課題の予測を別の課題へ渡すが、共同学習の中で行う。
- (b)「価値が乏しい」を支持する記述も見つかった。EndoNet は、術具の正解の信号を足しても工程認識の特徴に情報が加わらなかったと報告している。共同学習を選んだ理由を書いた文献も複数ある。否定する記述もある。予測した工程でも分割が改善したという報告（ToolSeg 表 1）と、転移の方向は事前の直観どおりにならないという記述（Taskonomy）である。(a) については、同じ動画に術具の box または分割と工程の両方の注釈があるデータセットが少ないことを、複数の文献が述べている。

## Key Findings

### 1. 最優先の条件（E1・E2・E3、または E1・E2・E5）について

- E1・E2・E3 が揃う研究は、手術映像でも一般の映像でも確認できなかった。
- E1・E2・E5 については、E2 と E5 が揃い、E1 が部分一致または不明の研究が四件あった。
  - Sahu ほか 2020（DOI 10.1515/cdbme-2020-0037）：別に学習した術具在否の CNN（ZIBNet）の予測の上で LSTM を学習する。ZIBNet を凍結したかどうかは本文で確かめられず、不明。
  - DeepPhase（arXiv:1807.10565）：術具在否の ResNet-152 の出力（二値）または特徴を LSTM/GRU に渡す。補助調査によれば、二段階で逐次に学習しており、本文に「凍結」の語は無い。
  - 微小血管再建の抄録（Graham Schwarz、PSRC 2026 の学会抄録。enricher は Zenodo の DOI 10.5281/zenodo.20086606 を返したが、本調査で表示された record は 20101483 で、両者の対応は確認していない）：YOLOv8 の出力（box の座標と確信度）を DNN に渡して工程を分類する。凍結の有無は不明。
  - ToolSeg（arXiv:2411.16794）：MS-TCN++ で予測した工程を、分割ネットワークの decoder に条件として渡す（§4.2–4.3）。受け取る側の分割ネットワークは、条件づけを含めて学習される。凍結した二つのモデルの間に界面だけを学習する構成ではない。
- 四件とも片方向である。EgoSurgery（一人称の開放手術）で二つの課題を結合した研究は確認できなかった。

### 2. E4（入力を予測・正解に切り替える比較）について

- **ToolSeg（P→D、本文 表 1）**：同じ conditional decoder で、工程の入力元を「予測（MS-TCN++）」と「正解」に切り替えている。
  - 条件づけ無し（v0）：IoU 40.90／DSC 50.66
  - 予測した工程と PCD-Gated（v3）：48.77／57.52
  - 正解の工程と PCD-Gated（v6）：56.13／64.76
  - 対照の v0 は条件づけを持たない構造である。界面の構造を保ったまま入力を空にする対照は無い。正解と予測の和に当たる入力も無い。
- **EndoNet（D→P、補助調査による本文 §IV-C、表 III–IV、Cholec80）**：術具の正解の二値ベクトルを単独で入力したときの工程認識の精度は、HMM の前 48.2%、HMM の後 offline 69.2%、online 47.5% だった。EndoNet の特徴（予測した術具の確信度を含む）では、それぞれ 75.2%、92.0%、81.7% だった。特徴に正解の術具ビットを足した EndoNet-GTbin では 75.3%、92.2%、81.9% だった。予測した術具の二値だけを入力にする条件は無い。

### 3. 一般の機械学習での E1・E2

- **E1**：model stitching（Bansal ほか、arXiv:2106.07682）は「Given two trained and frozen models A and B」と書き、その間に「a simple trainable layer」を置く。基盤モデルに広げた研究（arXiv:2603.12433）もある。どちらも渡すのは中間表現なので、E2 とは一致しない。
- **E1 と E3**：Taskonomy（arXiv:1804.08328）は「A small readout function is trained to map representations of source task's frozen encoder to target task's labels」（図 4）と書き、方向つきの affinity を測る。渡すのは表現である。
- **E2（予測を渡す結合）**：
  - stacking は、基盤モデルの予測を結合器に入力する。対象は同じ課題である。
  - cross-task consistency（Zamir ほか、arXiv:2006.04096）は、ある課題の予測を別の課題へ写すネットワークを使う。凍結の範囲は本文で確かめておらず、不明。
  - PAD-Net（arXiv:1805.04409）と MTI-Net（arXiv:2001.06902）は、中間の課題予測を蒸留して最終の課題に使う。どちらも共同学習である。
- まとめると、E1 と E2 はそれぞれ一般的な手法としてすでにある。ただし「凍結した二つの異なる課題のモデル」「同時刻の予測だけを渡す」「両方向を比べる」を同時に満たす一般の機械学習の研究は、この範囲では確認できなかった。

## 表 1: 照合表

一致する要素が多い順に並べた。§2.1 の既知文献は表の末尾にまとめた。その行の「—」は、既存の調査で記録済みのため本調査では照合し直していないことを表す。

| 文献（著者・年・題名） | DOI または arXiv ID | 掲載先 | E1 | E2 | E3 | E4 | E5 | E6 | 凍結の範囲と学習する部分（原文の記述と節・表番号） | 読んだ範囲（要旨のみ／本文） |
|---|---|---|---|---|---|---|---|---|---|---|
| Sachdeva ほか 2025, Phase-Informed Tool Segmentation for Manual Small-Incision Cataract Surgery（ToolSeg、§2.1 既知） | arXiv:2411.16794 | MICCAI 2025（§2.1 の記載による） | 部分一致：工程の予測器（MS-TCN++）は別に学習するが、分割ネットワークは条件づけごと学習する | 一致：予測した工程のラベルを decoder の条件として渡す | 不一致：P→D だけ | 部分一致：予測した工程と正解の工程を比べる（表 1）。空の入力・和の入力は無い | 部分一致：分割と工程。白内障手術（顕微鏡視野）で、一人称の開放手術ではない | 部分一致：動画単位の 5 分割交差検証（§5.1）。MS-TCN++ が online かどうかは不明（全時間分解能で処理すると記述、§4.2） | 「we first employ the Multi-Stage Temporal Convolutional Network (MS-TCN++)… to predict the phase of each frame」（§4.2）。「the decoder is conditioned on the surgical phase」（§4.3）。MS-TCN++ を凍結したかどうかの明示は不明 | 本文（§1–§5.3。補遺は未読） |
| Sahu ほか 2020, Surgical phase recognition by learning phase transitions（§2.1 の「Sahu ほか 2020」と同じ文献かどうかは不明） | DOI 10.1515/cdbme-2020-0037 | Current Directions in Biomedical Engineering 6(1) | 不明：ZIBNet を別に学習し、その予測の上で LSTM を学習する。ZIBNet を凍結したかどうかは不明 | 一致：「trained on the tool presence predictions of ZIBNet」 | 不一致：D→P だけ | 不明 | 部分一致：術具の在否と工程。腹腔鏡（Cholec80） | 部分一致：online の設定（Cholec80、「no future information was used」）。交差検証かどうかは不明 | 「instead of predicting phase ŷt directly from It, we use ZIBNet to automatically detect tools… and train an LSTM on top of this tool presence information」（Method）。節番号・表番号は不明 | 要旨のみ（検索抜粋を含む。本文は取得できなかった） |
| Zisimopoulos ほか 2018, DeepPhase: Surgical Phase Recognition in CATARACTS Videos（§2.1 既知） | arXiv:1807.10565 | MICCAI 2018（補助調査は未確認としている） | 部分一致：ResNet-152 を先に学習し、その出力を RNN に渡す二段階の学習。「凍結」の語は無い | 一致：術具在否の二値の出力を渡す条件がある（§2.3） | 不一致：D→P だけ | 不一致：予測の二値と予測の特徴を比べる（表 1）。正解は使わない | 部分一致：術具の在否と工程。白内障手術 | 不明 | 「tool binary presence from the output classification layer and tool features from the last pooling layer」（§2.3） | 本文（補助調査による） |
| 微小血管再建の工程認識の抄録, Automated Surgical Phase Recognition In Microvascular Reconstruction Using Artificial Intelligence（Graham Schwarz、2026、PSRC 2026 の学会抄録） | DOI 10.5281/zenodo.20086606（本調査で表示された Zenodo record 20101483 との対応は未確認） | Zenodo（抄録） | 不明：二段階の構成。凍結の有無は書かれていない | 一致：「CNN outputs, including bounding box coordinates and confidence scores, were subsequently processed by a DNN」 | 不一致：D→P だけ | 不明 | 部分一致：術具の box 検出（YOLOv8）と工程。微小血管手術 | 不明 | 二段階の構成（YOLOv8 と DNN）。凍結の範囲は不明 | 要旨のみ |
| Twinanda ほか 2017, EndoNet（§2.1 既知） | arXiv:1602.03012 | IEEE TMI 36(1):86–97, 2017（DOI 10.1109/TMI.2016.2593957、Crossref で確認） | 不一致：術具と工程を共同学習。HHMM は別に学習 | 部分一致：fc8 の特徴（術具の確信度 7 個を含む）を SVM と HHMM に渡す | 不一致 | 部分一致：術具の正解の二値信号と特徴を比べる（§IV-C、表 III–IV） | 部分一致：在否と工程。腹腔鏡。10 動画に box | 部分一致：online と offline の両方を報告 | 「since the HHMM is trained separately from the EndoNet fine-tuning process, the EndoNet features are not optimized on the entire phase recognition task」（§VII） | 本文（補助調査による） |
| Zamir ほか 2018, Taskonomy: Disentangling Task Transfer Learning | arXiv:1804.08328 | CVPR 2018 | 一致：source の encoder を凍結し、小さな readout だけを学習する（図 4） | 不一致：渡すのは encoder の表現 | 一致：方向つきの affinity を全ての組で測る | 不一致 | 不一致：屋内の静止画の課題 | 不一致 | 「A small readout function is trained to map representations of source task's frozen encoder to target task's labels」（図 4） | 本文の一部（検索抜粋） |
| Bansal ほか 2021, Revisiting Model Stitching to Compare Neural Representations | arXiv:2106.07682 | NeurIPS 2021 | 一致：「two trained and frozen models A and B… with a simple trainable layer between them」 | 不一致：中間層の表現を渡す | 不一致：同じ課題のモデルどうし | 不一致 | 不一致 | 不一致 | stitching layer は 1×1 conv と BN（§2） | 要旨のみ（検索抜粋を含む） |
| Mai ほか 2026, Revisiting Model Stitching in the Foundation Model Era（Zheda Mai, Ke Zhang, Fu-En Wang, Zixiao Ken Wang, Albert Y. C. Chen, Lu Xia, Min Sun, Wei-Lun Chao, Cheng-Hao Kuo） | arXiv:2603.12433 | arXiv | 一致：「the stitch layer is the only trainable component; the source and target models are kept frozen」（図 1） | 不一致：中間特徴 | 不一致 | 不一致 | 不一致 | 不一致 | 学習方法として layer feature matching などを比べる（§3.2.1） | 要旨のみ（検索抜粋を含む） |
| Zamir ほか 2020, Robust Learning Through Cross-Task Consistency | arXiv:2006.04096（DOI 10.1109/cvpr42600.2020.01121） | CVPR 2020 | 不明 | 一致：課題の予測を別の課題の予測へ写す（§2.3 の記述による） | 不明 | 不一致 | 不一致 | 不一致 | 不明 | 要旨のみ |
| Xu ほか 2018, PAD-Net | arXiv:1805.04409 | CVPR 2018 | 不一致：共同学習 | 部分一致：中間の課題予測を蒸留の入力にする | 不一致 | 不一致 | 不一致 | 不一致 | 「the predictions from these intermediate auxiliary tasks are utilized as multi-modal input」（要旨） | 要旨のみ（検索抜粋を含む） |
| Vandenhende ほか 2020, MTI-Net | arXiv:2001.06902 | ECCV 2020 | 不一致：共同学習 | 部分一致：初期の課題予測の特徴を各スケールで蒸留する | 不一致：BTI-Net（arXiv:2606.29102）は MTI-Net を一方向と分類している | 不一致 | 不一致 | 不一致 | 「initial task predictions are made at each scale」（§2.1 の図の説明） | 要旨のみ（検索抜粋を含む） |
| An ほか 2024, Object Aware Egocentric Online Action Detection | arXiv:2406.01079 | arXiv（CVPR workshop と推測されるが未確認） | 部分一致：既製の検出器を使い、学習可能な query で検出出力に注意を向ける。凍結は不明 | 部分一致：「attend to the detected objects' outputs」 | 不一致：検出→行動だけ | 不一致 | 部分一致：一人称（EPIC-Kitchens-100）。手術ではない | 部分一致：online の行動検出 | 「integrating an off-the-shelf detector with the existing OAD framework」（§3.1） | 要旨のみ（検索抜粋を含む） |
| Radevski ほか 2023, Multimodal Distillation for Egocentric Action Recognition | arXiv:2307.07483 | ICCV 2023（未確認） | 不一致：教師から生徒への蒸留 | 部分一致：物体検出（box とカテゴリ）を一つの入力モダリティとして STLT で符号化する | 不一致 | 不一致 | 部分一致：一人称 | 不明 | 不明 | 要旨のみ（検索抜粋を含む） |
| Nguyen ほか 2025, KAFR（YOLOv8 で術具を検出・追跡し、フレーム選択に使う） | arXiv:2501.11153（IEEE Access 版 DOI 10.1109/ACCESS.2025.3573264、補助調査による） | IEEE Access 13 | 不明 | 部分一致：YOLO の出力はフレーム選択に使い、工程の分類器への入力にはしない | 不一致 | 不明 | 部分一致：box 検出と工程 | 不明 | 不明 | 要旨のみ |
| Ayobi ほか 2024/2025, Pixel-Wise Recognition for Holistic Surgical Scene Understanding（GraSP、TAPIS） | arXiv:2401.11174 | Medical Image Analysis | 部分一致：分割モデルを region proposal として使う。凍結は不明 | 不一致：segment embedding（特徴）を渡す | 不一致 | 不明：分類しない術具領域を使う ablation がある | 一致：術具の分割と工程（ロボット前立腺摘除） | 不明 | 「utilizes a localized instrument segmentation baseline… [that] provides pixel-precise instrument masks and their corresponding segment embeddings」 | 要旨のみ（検索抜粋を含む） |
| Czempiel ほか 2020, TeCNO | arXiv:2003.10751 | MICCAI 2020 | 部分一致：特徴抽出器（ResNet50）を先に学習し、抽出した特徴の上で TCN を学習する二段階（§2.1） | 不一致：特徴を渡す | 不一致 | 不一致 | 部分一致：術具の在否は特徴抽出器の多課題学習のラベルとして使うだけ | 部分一致：causal で online。交差検証ではなく固定分割（40/8/32） | 「We adopt a two-stage approach so that our temporal refinement pipeline is independent of the feature extractor and the available ground truth」（§2.1） | 本文 |
| Jin ほか 2020, MTRCNet-CL（§2.1 既知） | arXiv:1907.06099 | Medical Image Analysis 59 | 不一致：共同学習 | 部分一致：出力の間の相関損失 | — | — | 部分一致：在否と工程 | — | 「with joint learning… tool usage information can be indirectly used for the improvement of phase recognition through the shared features」（§2.2、補助調査による） | 本文（補助調査による） |
| Padoy ほか 2012, Statistical modeling and recognition of surgical workflow | DOI 10.1016/j.media.2010.10.001 | Medical Image Analysis 16(3) | 不一致 | 部分一致：記録・注釈された術具使用の信号を入力にする（映像の検出器ではない） | 不一致 | 部分一致：入力は正解側の信号だけ | 部分一致：術具の使用と工程。腹腔鏡 16 例 | 不明 | 不明 | 要旨のみ（補助調査による） |
| Yang ほか 2019, Activity Driven Weakly Supervised Object Detection | arXiv:1904.01665 | CVPR 2019 | 不一致：検出と行動分類を同時に学習 | 不一致：行動ラベルは学習時の弱い教師 | 不一致 | 不一致 | 部分一致：行動→検出の方向。一人称の動画を含む | 不明 | 「simultaneously train a joint object detection and action classification model」（要旨） | 要旨のみ |
| Yuan ほか 2022, Anticipation for surgical workflow through instrument interaction and recognized Signals | ID 未確認 | Medical Image Analysis | 不明 | 不明 | 部分一致：術具と工程の予期を多課題で同時に行う | 不明 | 部分一致：術具と工程 | 不明 | 「a multi-task learning schema to jointly anticipate instrument and phase occurrence」 | 要旨のみ |
| Kim・Park 2026, Temporally Consistent Label Interpolation for Robust Surgical Multi-Task Learning under Challenging Conditions（Garam Kim, Juyoun Park。手法名 FAROS） | arXiv:2606.26634 | arXiv | 不一致：多課題学習 | 不明 | 不明 | 不一致 | 一致：分割と workflow（GraSP、MISAW） | 不明 | 不明 | 要旨のみ（検索抜粋を含む） |
| Al Shafi ほか 2026, BTI-Net: Bidirectional Decoder-Level Task Interaction via Uncertainty-Aware Gating for Multi-Task Medical Image Analysis（Abdullah Al Shafi, Md Kawsar Mahmud Khan Zunayed, Safin Ahmmed, Sk Imran Hossain, Engelbert Mephu Nguifo。超音波・ダーモスコピー・脳 MRI で評価） | arXiv:2606.29102 | arXiv | 不一致：共同学習 | 不明：decoder の水準での相互作用 | 部分一致：双方向の相互作用を設計に入れる | 不一致 | 不一致：医用画像だが手術映像ではない | 不明 | 不明 | 要旨のみ（検索抜粋を含む） |
| §2.1 既知：M2CAI 2016 tool presence の技術報告 | arXiv:1610.08844（補助調査による） | 技術報告 | — | — | — | — | 部分一致 | — | — | 照合し直していない |
| §2.1 既知：Park ほか 2022（visual kinematics-based index） | ID 未確認 | 不明 | — | — | — | — | — | — | — | 照合し直していない |
| §2.1 既知：DTFormer（Ding ほか） | ID 未確認 | 不明 | — | — | — | — | — | — | — | 照合し直していない |
| §2.1 既知：PhaKIR 2024 challenge（データセット論文） | arXiv:2511.06549 | arXiv | — | — | — | — | 一致（データ：工程と術具のインスタンス分割） | — | — | 要旨のみ（検索抜粋を含む） |
| §2.1 既知：Surgformer | arXiv:2408.03867 | 不明 | — | — | — | — | — | — | — | 照合し直していない |
| §2.1 既知：LoViT | DOI 10.1016/j.media.2024.103366 | Medical Image Analysis | — | — | — | — | — | 部分一致（online） | — | 照合し直していない |
| §2.1 既知：EgoSurgery-Phase | ID 未確認 | MICCAI 2024 | — | — | — | — | 一致（一人称の開放手術・工程） | — | — | 照合し直していない |
| §2.1 既知：EgoSurgery-Tool | arXiv:2406.03095 | arXiv | — | — | — | — | 一致（一人称の開放手術・box） | — | — | 要旨のみ（検索抜粋を含む） |
| §2.1 既知：EgoSurgery-HTS | arXiv:2503.18755 | Healthcare Technology Letters（PMC 収載） | — | — | — | — | 一致（一人称の開放手術・分割） | — | — | 要旨のみ（検索抜粋を含む） |
| §2.1 既知：Kostiuchik ほか 2024（データ分割） | ID 未確認 | 不明 | — | — | — | — | — | — | — | 照合し直していない |
| §2.1 既知：RULSTM、STIN、ORViT、ObjectViViT、DAIR、Helping Hands、Ego-OMG、StillFast、VISTA、ActionVOS（各一行の扱い。本調査では ID を確認していない） | ID 未確認 | 不明 | — | — | — | — | — | — | — | 照合し直していない |
| §2.1 既知：COCO-Tasks、TOIST、CoTDet、Grounding DINO、Conditional DETR、LAB-Det、Context R-CNN、SELSA、Structure Inference Net、LongShortNet、StreamYOLO、FiLM、LAVT、CLIPSeg、MDETR（各一行の扱い。本調査では ID を確認していない） | ID 未確認 | 不明 | — | — | — | — | — | — | — | 照合し直していない |
| §2.1 既知：Standley ほか 2020, Which Tasks Should Be Learned Together in Multi-task Learning? | arXiv:1905.07553 | ICML 2020 | — | — | — | — | — | — | — | 照合し直していない |

注：§2.1 の一般映像と検出・機構の文献は、依頼文では一行ずつ載せる指定である。今回は ID を確認していないため、二行にまとめて「ID 未確認」とした。

## 表 2: 見つからない理由の証拠

| 可能性（a／b／c） | 支持か否定か | 文献（DOI または arXiv ID） | 原文の要旨と節 |
|---|---|---|---|
| a | 支持 | arXiv:2606.26634 | AutoLaparo は工程と術具の分割の注釈を持つが、同じフレームに両方は付いていない（「provided independently without coannotation at the same frames」）。EndoVis2018 には workflow の注釈が無い。「existing datasets generally do not provide annotations spanning both temporal workflow and spatial instrument understanding」（データセットの節） |
| a | 支持 | arXiv:2406.03095 | EgoSurgery-Phase の 21 動画のうち、15 動画に術具と手の box を付けた。著者は、多課題学習（工程・術具検出・手検出）ができるデータセットは EgoSurgery-Phase の他に無い（原文「the only available dataset」）と書いている（EgoSurgery-Tool Dataset の節） |
| a | 支持 | DOI 10.3390/data10010007、arXiv:1602.03012 | Cholec80-Boxes が box を付けたのは video 41–45 だけ（図 2）。EndoNet の記述では「10 videos have also been fully annotated with the bounding boxes of tools」 |
| a | 支持 | arXiv:2603.12433 | 凍結した target の層を通すと、小さなずれが積み重なって大きくなる。乱数で初期化した stitch 層を凍結した層の列ごしに学習すると最適化が難しく、収束が悪いことが多い（§3.2.1） |
| a | 支持 | arXiv:2411.16794（§2.1 既知） | 予測した工程と正解の工程とで性能の差が残る（§5.3 Limitations） |
| a | 否定 | arXiv:2106.07682 | 「typical minima reached by SGD can all be stitched to each other with minimal change in accuracy」（要旨）。凍結したモデルどうしを小さな層でつなぐこと自体はできると報告している |
| a | 否定 | arXiv:2411.16794（§2.1 既知） | 予測した工程（MS-TCN++）で条件づけても、分割が改善した（表 1：v0 の IoU 40.90 に対し v3 は 48.77） |
| b | 支持 | arXiv:1602.03012（§2.1 既知、補助調査による） | 「the tool information generated from the ground-truth does not bring more information than the EndoNet features」（§V-A2）。表 III–IV で、特徴に正解の術具ビットを足した場合の差は 0.1〜0.2 ポイントだった |
| b | 支持 | arXiv:1907.06099（§2.1 既知、補助調査による） | 共同学習を選んだ理由として、課題を独立に扱うと「without considering the intrinsic association between them」と述べている（序論）。また、EndoNet では「temporal dependencies… are detached from the unified framework」と述べている（§2.2） |
| b | 支持 | arXiv:2305.13961 | 「In many cases, the feature extractor is trained on both the phase recognition and the tool recognition task」（付録 A.1）。術具の情報を共同学習で使うことが慣行になっていると記述している |
| b | 支持 | arXiv:2001.06902 | 予測を蒸留する PAD-Net は、ある設定で単一課題のモデルの集合に対して「-0.02%」だった（表番号は不明）。予測を渡す結合が常に改善するとは限らない例である |
| b | 否定 | arXiv:1804.08328 | 「although we might expect depth to transfer to surface normals better…, the opposite is found to be the better direction」（序論）。転移の方向による違いは事前の直観では決まらないと述べている |
| b | 否定 | arXiv:2107.04810 | end-to-end で学習した多段の TeCNO は「only achieves comparable results with the single-stage predictor」。段階ごとに学習する方式を提案している（§1–§2） |
| b | 否定 | arXiv:2512.14712 | 別分野（敗血症、N<10k）の報告。専門家モデルの stacking（late fusion）が deep fusion より良かった。小さなデータでは独立したモデルの結合を選ぶ根拠を示している |
| b | 否定 | arXiv:2411.16794（§2.1 既知） | 正解の工程でも予測した工程でも分割が改善した（表 1）。工程の情報は検出・分割側で冗長ではなかったという報告である |
| c | 支持 | arXiv:2606.29102 | 著者の比較表で、PAD-Net と MTI-Net は「Bidir. ✗」と分類されている（§1–§2）。双方向の比較は、少なくともこれらの代表的な系統では行われていないという著者の主張である |
| c | 支持 | arXiv:2606.26634 | TAPIS について「spatial and temporal tasks were still learned through separate branches… limiting bidirectional complementary learning between instrument information and workflow context」（§2.2） |
| c | 支持 | arXiv:2003.10751 | TeCNO の参考文献（本文で全件を確認）は、手術の workflow と行動分割の文献だけだった。model stitching、stacking、Taskonomy の系統の引用は無い |
| c | 支持 | arXiv:2411.16794 | 読んだ範囲の関連研究（§2）は、手術のデータセットと分割の文献だけだった。model stitching、Taskonomy、cross-task consistency への言及は確認できなかった（参考文献の一覧は未確認） |
| c | 否定 | arXiv:2406.03095 | EgoSurgery-Tool の著者は、工程ごとの術具の条件付き確率を示し、「Surgical tool information might be helpful for surgical phase recognition」と書いている。同じデータ群で二つの課題の関係はすでに意識されている |

## 表 3: 同じ動画に術具の注釈と工程の注釈がある公開データセット

| データセット | 術式・視点 | 動画数 | 術具の注釈の形（box／分割／在否） | 工程の注釈 | 出典（DOI または arXiv ID） |
|---|---|---|---|---|---|
| EgoSurgery（Phase／Tool／HTS） | 開放手術 10 術式、術者の頭部カメラ（一人称） | 工程 21 動画。術具の box は 15 動画 | box（15 種、49,652 個）。分割（HTS、SAM で生成し手で修正） | あり（27K フレーム以上） | arXiv:2406.03095、arXiv:2503.18755（EgoSurgery-Phase は ID 未確認） |
| Cholec80 | 腹腔鏡下胆嚢摘出、内視鏡 | 80 | 在否（7 種、1 fps）。box は EndoNet の記述では 10 動画 | あり（7 工程） | arXiv:1602.03012 |
| Cholec80-Boxes | 同上 | 5（video 41–45） | box | Cholec80 の工程を使う | DOI 10.3390/data10010007 |
| SurgBox | 同上 | 80 | box（在否のラベルから MLLM で生成。1,000 フレームを人が参照注釈） | Cholec80 の工程を使う | ID 未確認（Hugging Face で公開、MICAD 2026 と記載） |
| CholecT50 | 腹腔鏡下胆嚢摘出 | 50 | 三つ組（術具・動作・標的）。box は 5 動画 | あり | ID 未確認 |
| GraSP | ロボット支援前立腺摘除 | 13 | インスタンス分割（疎な 3,449 フレーム） | あり（工程と step） | arXiv:2401.11174 |
| PhaKIR | 腹腔鏡 | 不明 | インスタンス分割、keypoint | あり | arXiv:2511.06549 |
| Sankara-MSICS | 手動小切開白内障手術、顕微鏡 | 53 | 分割（3,527 フレーム、13 種） | あり（18 工程） | arXiv:2411.16794 |
| MISAW（分割を追加した拡張版） | ロボット支援の微小手術の訓練 | 不明 | 分割（拡張版で追加） | あり（工程・step・動作） | ID 未確認 |
| HeiChole | 腹腔鏡下胆嚢摘出 | 不明 | 在否 | あり | arXiv:2109.14956 |
| AutoLaparo | 腹腔鏡下子宮摘出 | 不明 | 分割（ただし工程と同じフレームには付いていない） | あり | ID 未確認 |

## Details

### 設定の違い（最も近い候補と §1 の設計）

- **ToolSeg**
  - データセット：白内障（Sankara-MSICS、53 動画）。§1 の設計は EgoSurgery の 15 動画。
  - 課題の粒度：分割（18 工程、13 術具）。
  - 凍結の範囲：受け取る側の分割ネットワーク全体を学習する（U-Net に条件づけ層を加える）。
  - 学習する部分：PCD 層と分割ネットワークの全体。
  - online かどうか：工程の予測器 MS-TCN++ は「processes the video at full temporal resolution」（§4.2）とある。causal かどうかは不明。
- **Sahu 2020**
  - データセット：Cholec80。課題は在否と工程。
  - 凍結の範囲：不明。学習する部分は LSTM（ZIBNet を同時に更新したかどうかは不明）。
  - online かどうか：online（「no future information was used」）。
- **DeepPhase**
  - データセット：CATARACTS。課題は在否（21 種）と工程。
  - 学習：二段階の逐次の学習。
  - online かどうか：不明。
  - 予測の二値と予測の特徴の比較（表 1）：LSTM では 68.75% と 78.28%、GRU では 71.61% と 68.96% で、構造によって順序が逆になった。
- **EndoNet**：多課題の共同学習で、HHMM は別に学習する。online と offline の両方を報告している。

### 一人称・行動認識

検出の出力を行動へ渡す方向の研究は確認できた（Object Aware OAD、Multimodal Distillation の OBJ モダリティ。§2.1 既知の RULSTM・STIN なども）。行動ラベルを検出へ渡す方向の研究も確認できた（Activity Driven WSOD、TD-Graph LSTM arXiv:1708.00666）。ただし後者は、ラベルを学習時の弱い教師として使うもので、推論時に予測を入力として渡す構成ではない。両方向を同じ研究で比べたものは、この範囲では確認できなかった。

## Caveats

- 有料の本文（Medical Image Analysis の Yuan 2022、IJCARS の MTAM〔Springer, s11548-025-03546-3〕など）と Sahu 2020 の本文は読めなかった。Sahu 2020 は 405 エラーで取得に失敗した。これらの凍結の範囲は「不明」とした。
- EndoNet・DeepPhase・MTRCNet-CL・Padoy 2012 の節番号、表番号、引用は、補助調査（別の調査担当）が報告したものである。本報告の著者自身は原文で照合していない。
- 2026 年の arXiv 文献（2603.12433、2606.26634、2606.29102、2512.14712）は査読の状況を確認していない。
- EgoSurgery の「the only available dataset」は著者の主張であり、表 3 に挙げた他のデータセット（GraSP、Sankara-MSICS など）は、術具の注釈の形が異なる組み合わせを持つ。

## 検索記録

- **使った検索エンジン・道具の名前と版**
  - ウェブ検索（本環境の web_search、版不明）：18 回
  - ページ取得（web_fetch、版不明）：3 回。arXiv の PDF 2 件（2411.16794、2003.10751）は取得できた。De Gruyter の 1 件は 405 エラーで失敗した。
  - 補助調査（下位の調査担当 1 回、検索手段の版は不明）：arXiv、PubMed、De Gruyter を参照したと報告された。検索語と件数は報告されず、不明。
  - Semantic Scholar の API、Google Scholar、OpenReview の検索画面、出版社サイトの内部検索は直接には使っていない（ウェブ検索の結果として表示された頁だけを見た）。
- **検索日**：2026-10-18
- **検索語と、照合した候補の件数**（題名・要旨・抜粋を照合した件数）

  | 検索語 | 照合した件数 |
  |---|---|
  | phase-conditioned surgical instrument detection phase recognition prior | 10 |
  | two-stage tool detection then phase recognition surgical video frozen detector | 9 |
  | bidirectional mutual surgical phase tool cross-task | 10 |
  | phase recognition ground truth tool annotations versus predicted tool signals cholecystectomy | 9 |
  | Robust Learning Through Cross-Task Consistency Zamir | 8 |
  | model stitching frozen networks small trainable layer | 9 |
  | TeCNO surgical phase recognition additional tool information causal MS-TCN | 9 |
  | activity-driven weakly supervised object detection egocentric action labels | 9 |
  | MTI-Net multi-scale task interaction distillation PAD-Net intermediate predictions | 8 |
  | EgoSurgery-Tool dataset bounding box egocentric open surgery phase annotations | 9 |
  | GraSP dataset phases steps instrument segmentation TAPIS | 9 |
  | dataset surgical phase and instrument bounding box annotations same videos Cholec80 boxes | 9 |
  | phase recognition from ground-truth instrument presence signals oracle upper bound | 9（大半は手術と無関係） |
  | stacked generalization frozen expert models late fusion small combiner | 9 |
  | object detection outputs as input to egocentric action recognition frozen detector EPIC-Kitchens | 9 |
  | surgical phase recognition using YOLO instrument detection outputs as features | 9 |
  | Taskonomy transfer asymmetry task affinity directional transfer frozen encoder readout | 8 |
  | "phase" "instrument" detection "predicted phase" versus "ground truth phase" conditioning surgical | 9 |

- **走査した会議・論文誌と年の範囲**
  - 会議や論文誌の目次を系統的に走査してはいない。上記の検索で表示された 2012〜2026 年の文献を照合した。掲載先は MICCAI、Medical Image Analysis、IEEE TMI、IJCARS、CVPR、NeurIPS、ECCV、Current Directions in Biomedical Engineering、IEEE Access、arXiv である。
- **走査できなかった範囲**
  - OpenReview の不採択・取り下げ・非公開の投稿（ICLR、NeurIPS、MIDL）
  - 学位論文のリポジトリ
  - 有料の本文（ScienceDirect、Springer など）
  - MICCAI・IPCAI・IEEE TBME・MIDL・MICCAI と CVPR の workshop の目次
  - EndoVis・M2CAI の challenge 報告の個々の参加チームの技術報告
  - 「試して効かなかった・やめた」という記述の全文検索（本文の取得が限られたため）

## 見つからなかったもの

この検索語・この範囲では、次のものを確認できなかった。

- 術具の検出（box・分割・在否）と工程認識について、独立に学習して凍結した二つのモデルを、同じ時刻の予測だけを受け渡す小さな界面でつなぎ、D→P と P→D を同じ研究の中で比べた研究
- 同じ界面の構造のまま、入力を空・予測・正解・正解と予測の和に切り替えて比べた研究
- EgoSurgery（一人称の開放手術）で、術具の検出と工程認識を結合した研究
- 一人称の行動認識で、検出→行動と行動→検出の両方向を、推論時の予測の受け渡しとして同じ研究で比べた研究
- 凍結した独立のモデルを予測でつなぐ構成を試して効かなかった、またはやめたという、OpenReview の不採択の投稿や学位論文の記述
- Sahu ほか 2020 における、ZIBNet の凍結の有無と、正解と予測の術具入力の比較の有無
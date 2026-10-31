# 一人称視点映像における手–物体相互作用を、物体検出・行動／手順／工程認識へ利用する研究の文献調査

## 系統表

### 冒頭の結論

調査範囲で、**「手–物体の把持／接触モデルを下流モデルとは別に学習して凍結し、その予測出力を、物体検出と行動・手順・工程認識の双方へ入れて、それぞれの改善を同一研究で測る」ものは確認できなかった**。手術・医療に限っても、**独立した手–術具把持モデルを凍結し、その出力で術具検出または工程認識を改善した査読済み研究は確認できなかった**。EgoSurgery-HTSについては、2026年10月31日までに確認できた公開文献では、HTSで学習した把持／hand-tool segmentationモデルをEgoSurgeryのphase recognitionまたはtool detectionへ渡した既発表研究は見つからなかった。HTS原論文自体はhand、tool、hand-toolのinstance segmentationを評価する論文である。citeturn696456search0turn696456search1

ただし、かなり近い実証は複数ある。

**(a) 推論時にも相互作用推論を渡す形に最も近いもの**は、Lee et al., *EgoPED*（CVPR 2024）である。独立に用意したactive-object detectorから、**手・物体bbox、物体クラス、active/contact状態**を取り出し、物体間のinteraction graphをGCNで特徴化してaction segmentation/error detection側へ入力する。AODを除くと同一条件でError Detection Accuracyが57.0→52.5、AUCが62.0→58.7へ低下しており、少なくとも下流の手順理解にinteraction detector出力が有効だった。ただしこれは**offline**であり、物体検出自体を改善する方向ではない。さらに、料理で学習したAODをHoloAssist等の組立映像へ移した際には「うまく働かなかった」と報告されている。citeturn382618search7turn795611view2turn795611view3

**(b) 学習時だけ相互作用情報を使う形に最も近いもの**は二系統ある。Shiota et al.（WACV 2024）はhand–object contactとobject stateを補助学習させ、**推論時はRGB action recognizerだけ**にする。SlowFastではEGTEAでoverall accuracy 64.02→66.86、MECCANOで38.08→40.70だったが、強いSwin-Bでは利得が縮小し、EPIC-KITCHENS-100ではHOCL単独で34.39→32.72と悪化する条件もある。citeturn938785search6turn928591view0turn928591view1turn928591view2 Helping Hands（ICCV 2023）も、100DOH由来の手・物体boxを訓練時に補助教師として使い、推論時にはRGBモデルだけを用いる。EGTEAでTop-1 44.9→46.6、mean-class accuracy 37.6→39.1となり、box品質を上げると下流性能も上がる関係を報告している。citeturn382618search0turn928591view3turn928591view4

物体検出側では、Yang & Liu, *Active Object Detection with Knowledge Aggregation and Distillation from Large Models*（CVPR 2024）が重要である。これはinteractionに関するsemantic/visual priorをteacherへ与え、その能力をstudent detectorへ蒸留するため、**推論時には追加interaction情報を不要にする**。Ego4D、EPIC-KITCHENS、MECCANO、100DOHでactive-object detectionを評価している。ただし、これは「別に学習した手–把持モデルの予測」を教師にするものではなく、interaction knowledgeをlarge models等から構成するため、EgoSurgery-HTSで想定する(b)とは一段抽象的である。citeturn938785search5

以上を踏まえた系統表は次の通りである。件数は、後述の「文献ごとの記録」に詳細ブロックを置いた件数であり、ユーザーが既に所持している文献は詳細記録から除外した。

| 系統 | 代表的な文献 | 現役度 | 詳細記録件数 |
|---|---|---|---:|
| 推論時のhand/object/contact特徴融合 | EgoPED; Ego-OMG; Forecasting Action Through Contact Representations | 不明。現在もgraph/contact型は使われるが、共通ベンチマークでの直近2年比較が不足 | 3 |
| 学習時だけhand/object/contactを使う補助学習 | Shiota et al. 2024; Helping Hands | 定番の基準に近いが、定義を満たす直近複数論文の比較表を十分確認できず「不明」 | 2 |
| interaction knowledge distillation / LUPI | Multimodal Distillation; IKD; KAD | KADは2024 CVPRのAOD上位手法、IKDは2025 Pattern Recognition。現役度はベンチマークごとに不明 | 3 |
| explicit hand pose / left-right hand dynamics | HandFormer; H2O; H2OTR | H2O/Assembly101では現在も有力な比較軸。HandFormerについては2024 ECCV以後の複数比較表を満たさず不明 | 2 |
| active-object / next-active-object | Furnari et al. 2017; Jiang et al. 2021; NAOGAT | 定番概念。個々のモデルは置き換えが進んでいる | 2 |
| object-centric video transformer | ORViT; *How Can Objects Help Action Recognition?*; *Simultaneous Detection and Interaction Reasoning…* | Li et al. 2025は新興、ORViTは定番系統 | 0（所持文献を含むため） |
| sparse hand-object graph / compositional recognition | STIN; SViT | STINは古典的基準、SViTはtraining-only structure transferの代表 | 0（所持文献） |
| 3D hand/object poseとactionのjoint learning | H2O; HandFormer; STFormer | 不明 | 2 |
| surgical instrument cue→workflow | EndoNet; MTRCNet-CL; IIA-Net; ESIP; gastric surgery tool→phase | EndoNet/MTRCNet-CLは定番基準、ESIP等は新興 | 3 |
| surgical hand cue→tool recognition | Hand Motion-Aware Surgical Tool Localization; Open surgery tool classification and hand utilization | 不明。直接後続が少ない | 2 |
| EgoSurgery固有 | EgoSurgery-Phase; EgoSurgery-Tool; EgoSurgery-HTS | データセット／ベンチマーク系統として新興。HTSの下流利用は確認できず | 3 |
| 強い受け取り側で利得が消える／domain shift | Shiota et al.; EgoPED; Furnari et al.; 2026 ego-VLM分析 | 否定的結果として重要 | 上記と重複 |

ユーザー所持文献の位置づけは、*How Can Objects Help Action Recognition?* が「object-aware attention/token selection」、*Simultaneous Detection and Interaction Reasoning for Object-Centric Action Recognition* が「検出とinteraction reasoningのend-to-end同時学習」、STINが「bbox関係グラフ」、SViTが「hand-object graphを静止画側だけで教師にするtraining-only structure transfer」、EndoNetとMTRCNet-CLが「instrument/phaseのmulti-task surgical workflow」である。Li et al.の2025 TMM論文はoff-the-shelf detector依存を避け、proposal generation、interactive-object refinement、relation modelingをend-to-endで同時学習するため、今回の「独立に凍結した把持モデル」と対照になる。citeturn938785search7 SViTでは、hand/objectをnode、contact/no-contactをedgeとするHand-Object Graphを、訓練時だけ利用可能な画像構造として動画モデルへ移す。citeturn938785search4

## 文献ごとの記録

### Shiota et al., Egocentric Action Recognition by Capturing Hand-Object Contact and Object State

- **書誌:** Tsukasa Shiota, Motohiro Takagi, Kaori Kumagai, Hitoshi Seshimo, Yushi Aono／2024／*Egocentric Action Recognition by Capturing Hand-Object Contact and Object State*／WACV 2024、査読あり／DOI 10.1109/WACV57701.2024.00641。citeturn382618search3turn382618search13
- **読んだ範囲:** 本文。表1–3、方法図、実装記述を確認。citeturn382618search62turn928591view0turn928591view1turn928591view2
- **方向:** 3、5、7。
- **視点／ドメイン:** 一人称／非医療。
- **課題の形:** RGB action recognizerに、hand–object contactを学習させるHOCLとobject-state changeを学習させるOSLを補助目的として追加。手・物体領域の生成にはFaster R-CNN系detectorを利用する。citeturn938785search6
- **推論の規約:** clip-level action recognition。online causal制約は報告されておらず、今回のonline phase条件とは一致しない。
- **データ規模:** EGTEA、MECCANO、EPIC-KITCHENS-100。各dataset既定split。
- **モデルの状態:** interactionを最終的な別モデルとして推論時に残すのではなく、補助目的をaction modelの学習へ使う。(b)に近い。
- **系統:** training-only HOI auxiliary learning。
- **現役度:** 不明。2024 WACVの査読論文だが、2025–2026の複数査読論文の同一設定比較表で「上位」を確認するところまではできなかった。
- **少数動画／online／一人称:** 一人称は該当。onlineではない。少数動画条件そのものではないが、論文は少数sample条件への効果を分析している。citeturn938785search6
- **何と何を比べた差か:** 同一backboneのbaselineと、HOCL、OSL、HOCL+OSLを追加したモデル。
- **効果量:** EGTEA表1、SlowFast baseline overall 64.02、HOCL 66.48（+2.46）、OSL 65.81（+1.79）、両方66.86（+2.84）。mean-class 55.81→58.14（+2.33）。Swin-Bではoverall 64.09→65.98（+1.89）、mean-class 57.14→59.27（+2.13）。citeturn928591view0
- **効果量:** MECCANO表2、SlowFast Acc@1 38.08→HOCL 42.05（+3.97）、OSL 41.37、両方40.70。Swin-Bは44.03→HOCL 42.01（−2.02）、OSL 44.00（−0.03）、両方44.81（+0.78）。citeturn928591view1
- **否定的結果:** EPIC-KITCHENS-100表3ではSlowFast action 32.14→HOCL 33.63だがHOCL+OSLは31.53。Swin-Bはbaseline 34.39→HOCL 32.72で悪化する。SlowFastのtail actionも12.40→HOCL 12.21、OSL 8.18、両方10.21で悪化する。citeturn928591view2
- **基準の強さ:** SlowFastとSwin-Bを双方評価しており、「受け取り側が強いと利得が縮む／符号反転する」証拠として今回もっとも直接的。
- **oracle把持との差:** GT contactを下流推論入力として与えるoracle比較ではない。
- **seed／検定:** 有意差検定は確認できず。
- **実装:** 公開状況は今回確認範囲では不明。
- **要点:** **training-only contact supervisionは有効になり得るが、strong backbone・大規模datasetでは改善が消失または逆転する。**

### Helping Hands: An Object-Aware Ego-Centric Video Recognition Model

- **書誌:** Chuhan Zhang, Ankush Gupta, Andrew Zisserman／2023／*Helping Hands: An Object-Aware Ego-Centric Video Recognition Model*／ICCV 2023、査読あり／arXiv:2308.07918、DOI 10.1109/ICCV51070.2023.01278。citeturn382618search0turn382618academia64
- **読んだ範囲:** 本文、特に表1・表2とbox-quality解析。citeturn928591view3turn928591view4
- **方向:** 3、5、7。
- **視点／ドメイン:** 一人称／非医療。
- **課題の形:** EgoClip系動画表現学習時に、手位置、物体位置、caption由来object wordを補助予測する。推論時は追加box detectorを不要にする。citeturn382618search0
- **渡した表現:** hand bbox、object bbox、object semantics。
- **入れた位置:** video representationのtraining objective。推論時入力ではない。
- **モデルの状態:** 100DOH系detectorから得たpseudo boxを使うtraining-only方式。(b)にかなり近い。公式実装は抽出済みhand/object boxesも公開する。citeturn382618search39
- **何と何を比べた差か:** EgoMCQ training lossのみと、box loss／word lossを追加した同じモデル。
- **効果量:** 表1。EGTEA Top-1 44.9→boxのみ45.3、wordのみ45.8、box+word 46.6（+1.7）。mean-class 37.6→39.1（+1.5）。EPIC-KITCHENS-100 MIRではmAP 35.9→37.5（+1.6）、nDCG 36.6→37.8（+1.2）。citeturn928591view3
- **相互作用推論品質と下流利得:** 表2と本文で、より高品質なbox supervisionほどEGTEA／EK100 transferとVISOR localizationが良くなると報告する。これは今回の問い(8)(10)に対する数少ない直接的証拠である。citeturn928591view4
- **oracleとの差:** GT grasp/contactを推論時に入れる比較ではない。
- **左右:** left/rightの役割を工程特徴として分ける研究ではない。
- **seed／検定:** 統計的検定は確認できず。
- **コード:** 公式GitHubあり。抽出boxとmodel weightあり。citeturn382618search39
- **要点:** **pseudo hand/object supervisionの品質が下流利得に連動することを実測しており、SAM＋bboxから作るEgoSurgery-HTSに最も参考になる。**

### EgoPED: Error Detection in Egocentric Procedural Task Videos

- **書誌:** Shih-Po Lee, Zijia Lu, Zekun Zhang, Minh Hoai, Ehsan Elhamifar／2024／*Error Detection in Egocentric Procedural Task Videos*／CVPR 2024、査読あり／DOI 10.1109/CVPR52733.2024.01765。citeturn382618search4turn382618search7
- **読んだ範囲:** 本文、AOD module、表6、domain-transfer記述。citeturn795611view2turn795611view3
- **方向:** 3、7。
- **視点／ドメイン:** 一人称／調理・手順作業。
- **課題の形:** off-the-shelf action segmentation modelと、active object detectorから得るinteraction graphを組み合わせ、action segmentationとprocedural error detectionを行う。
- **渡した形:** hand/object bbox、object class、active/contact情報をgraph化。nodeはobject、interactionをedgeとしてGCN featureへ変換。
- **モデルの状態:** AODは独立componentとして扱われ、action modelへその推定を渡すため(a)に近い。
- **推論規約:** offline action segmentation。論文自身がonline causal設定ではない。citeturn795611view2
- **効果量:** 表6でprototype/negative samplingを固定し、AODなしEDA 52.5、AUC 58.7に対し、AODありEDA 57.0（+4.5）、AUC 62.0（+3.3）。citeturn795611view3
- **action segmentationへの効果:** active-object情報でbackground/action segmentationを改善する定性的解析はあるが、AODだけを変えた独立のsegmentation metric差は表6からは読めないため「不明」。
- **否定的結果:** cookingで学習したAODをHoloAssistおよびATAに適用したところdomain mismatchで良好に動作せず、これらではAOD componentを使わなかった。citeturn795611view3
- **基準の強さ:** 複数既存action segmentation backboneを利用するが、今回の強いfoundation-pretrained receiverとの直接比較ではない。
- **コード:** project/code公開あり。citeturn382618search22
- **要点:** **独立interaction detector→graph→手順認識という(a)の最も近い実証だが、domain transfer failureも明示される。**

### On the Utility of 3D Hand Poses for Action Recognition / HandFormer

- **書誌:** Md Salman Shamil et al.／2024／*On the Utility of 3D Hand Poses for Action Recognition*／ECCV 2024、査読あり／arXiv:2403.09805、DOI 10.1007/978-3-031-72658-3_25。citeturn382618academia60turn382618search18
- **読んだ範囲:** 本文、表1、4、5。citeturn719868view0turn719868view1
- **方向:** 3。
- **視点／ドメイン:** 一人称を含む／assembly、daily manipulation。
- **渡した形:** left/right 3D hand joint trajectoriesを明示的にfactorizeし、sparse RGBと融合。
- **推論規約:** clip action recognition、onlineではない。
- **モデル状態:** 手姿勢推定器を下流と完全end-to-endに学習する設定ではなく、推定またはGT 3D posesを入力modalitiesとして利用。
- **効果量:** Assembly101表1でTSM RGB 35.27 action／58.27 verb／47.45 object。MS-G3D+TSM late fusion 39.74／65.12／51.12、HandFormer 41.06／69.23／51.17。citeturn719868view0
- **表現ごとの差:** pose-only HandFormerはaction 28.80、verb 65.33、object 36.28で、**hand poseはverb/motionには強いがobject identityの情報が不足する**。citeturn719868view0
- **egocentric-only比較:** Assembly101表4で4 ego RGB views 33.80 action／59.00 verb／46.50 objectに対し、e3+e4+poseは38.05／66.32／47.86。action +4.25、verb +7.32だがobject +1.36に留まる。citeturn719868view1
- **左右:** 3D hand poseを明示的に扱う。H2Oは二手操作を含む。
- **oracleとの差:** H2OにはGT 3D hand poseがある一方Assembly101では推定poseを使うが、同一dataset・同一modelでGT対predictedを切り替えたoracle gapではない。
- **コード:** 公式GitHubあり。citeturn382618search35
- **要点:** **hand geometryは「何をしているか」のverbには大きく効くが、「何を持っているか」のobject classには弱く、工程と検出で有効な表現が異なることを示す。**

### Forecasting Action Through Contact Representations From First Person Video

- **書誌:** Vinay P. Namboodiri/Dessalene系研究／*Forecasting Action Through Contact Representations From First Person Video*／IEEE TPAMI／DOI 10.1109/TPAMI.2021.3055233。citeturn695620search1turn695620search7
- **読んだ範囲:** 要旨・書誌・公開説明まで。本文数値は今回記載しない。
- **方向:** 3。
- **視点／ドメイン:** 一人称／EPIC-KITCHENS。
- **課題の形:** future contactを表すContact Anticipation MapsとNext Active Object Segmentationを推定し、そのcontact representationをfuture action forecastingに利用。
- **渡した形:** pixel-level contact anticipation、next-active-object segmentation。
- **モデル状態:** predicted interaction representationを下流anticipationに用いる(a)系。
- **online性:** anticipationなので未来frame自体は観測しないが、論文のwindow処理とユーザーの0.5 fps causal phase recognitionが同一とは限らない。
- **効果量:** 本文未読のため記載しない。
- **要点:** **contactを「現在の把持状態」ではなく未来の接触分布・次active objectとして表現してaction anticipationへ渡す系統。**

### Ego-OMG: Egocentric Object Manipulation Graphs

- **書誌:** *Ego-OMG: Egocentric Object Manipulation Graphs*／arXiv:2006.03201。citeturn695620academia11
- **読んだ範囲:** 要旨・公開説明。
- **方向:** 3。
- **視点／ドメイン:** 一人称／非医療。
- **課題の形:** 手が物体に接触する／離れる時点でinteraction segmentを形成し、object manipulation graphでaction anticipationを行う。
- **渡した形:** object graph、hand-object contact transition、hand trajectory。
- **モデル状態:** interaction representationを明示的中間表現として利用。
- **効果量:** 本文未読のため記載しない。
- **要点:** **低fps環境でも意味を持ちやすい「接触状態の遷移」をaction anticipationへ使う先行系統。**

### Multimodal Distillation for Egocentric Action Recognition

- **書誌:** Radevski et al.／2023／*Multimodal Distillation for Egocentric Action Recognition*／ICCV 2023、査読あり／arXiv:2307.07483。citeturn654643search1turn317540academia49
- **読んだ範囲:** 要旨。数値は記載しない。
- **方向:** 3、5。
- **視点／ドメイン:** 一人称／非医療。
- **課題の形:** RGB、object detections、optical flow、audio等を持つmultimodal teacherからRGB-only studentへdistill。
- **モデル状態:** training-only privileged modalityであり(b)。
- **推論:** studentはRGBのみ。
- **比較:** 著者はmultimodal teacher informationをdistillしたstudentが、単純なunimodal/multimodal supervisionより良好であると報告する。具体値は本文未読のため省略。
- **要点:** **把持だけに限定されないが、「学習時にだけ追加モダリティを与え、推論コストを増やさない」設計の直接的先例。**

### Distilling interaction knowledge for semi-supervised egocentric action recognition

- **書誌:** Haoran Wang et al.／2025／*Distilling interaction knowledge for semi-supervised egocentric action recognition*／Pattern Recognition／DOI 10.1016/j.patcog.2024.110927。citeturn612061search2
- **読んだ範囲:** 要旨・出版社概要。数値は記載しない。
- **方向:** 3、5。
- **視点／ドメイン:** 一人称／非医療。
- **課題の形:** 少量のaction-labeled videoからhand-object spatial-temporal interactionをteacherに学習させ、それでunlabeled videoのpseudo-labelを作りstudentを学習。
- **渡した形:** hand-object relative spatial-temporal relations。
- **モデル状態:** teacher–student。interaction knowledgeは主にtraining/pseudo-labeling段階に利用。citeturn612061search2
- **少量データ:** 明示的にlimited annotated videosを対象。
- **SAM／bbox overlap:** SAM由来mask qualityの比較ではない。
- **要点:** **「少量ラベル＋interaction teacher＋pseudo labels」という問い(10)に最も近いが、mask-quality→downstream利得の分析は確認できなかった。**

### Active Object Detection with Knowledge Aggregation and Distillation from Large Models

- **書誌:** Dejie Yang, Yang Liu／2024／*Active Object Detection with Knowledge Aggregation and Distillation from Large Models*／CVPR 2024、査読あり／DOIは今回確認できず、ID不明。citeturn938785search5
- **読んだ範囲:** 本文概要・CVF掲載ページ。数値は表を精査していないため記載しない。
- **方向:** 3、5。
- **視点／ドメイン:** 一人称／非医療。
- **課題の形:** 複数の同カテゴリ物体が写る中からstate changeを受けるactive objectを検出する。
- **渡した形:** interactionのsemantic priorとvisual priorをoracle queryへ集約。
- **モデル状態:** teacher decoderが追加knowledgeを使い、student detectorがprediction/attentionを蒸留する。推論時はknowledge input不要。citeturn938785search5
- **ベンチマーク:** Ego4D、EPIC-KITCHENS、MECCANO、100DOH。
- **問い(2)との関係:** 「写っている物体」ではなく、interactionによってstate changeする**active object**を直接検出対象にする。
- **問い(4)との関係:** detector側におけるtraining-only interaction knowledgeの明確な例。
- **コード:** 公式code/model公開あり。citeturn938785search5
- **要点:** **検出側でも、interaction knowledgeをteacherだけに持たせstudentへ蒸留する(b)型が成立している。ただしexplicit hand-grasp predictorではない。**

### Next-active-object prediction from egocentric videos

- **書誌:** Antonino Furnari et al.／2017／*Next-active-object prediction from egocentric videos*／Journal of Visual Communication and Image Representation／DOI 10.1016/j.jvcir.2017.10.004。citeturn654643search5
- **読んだ範囲:** 要旨・出版社概要。本文数値は記載しない。
- **方向:** 3、7。
- **視点／ドメイン:** 一人称／日常・調理。
- **課題:** tracked object candidatesから、次に操作されるobjectを予測。
- **表現:** object position/trajectory/motionとhand presence。
- **否定的結果:** 著者の比較では**object motion cuesがhand-presence cueを含むbaselineより有効**だった。citeturn654643search5
- **要点:** **「手が見えること」そのものより、物体の時間運動の方がnext-active-objectには有用になり得る。**

### Predicting short-term next-active-object through visual attention and hand position

- **書誌:** Jiang et al.／2021／*Predicting short-term next-active-object through visual attention and hand position*／Neurocomputing／DOI 10.1016/j.neucom.2020.12.069。citeturn654643search6
- **読んだ範囲:** 要旨。
- **方向:** 3。
- **視点／ドメイン:** 一人称／非医療。
- **課題:** short-term next-active-object prediction。
- **渡した形:** visual attention map＋hand-position probability map。
- **要点:** **next object予測ではbbox/classだけでなく、hand positionをsoft spatial priorとして融合する系統がある。**

### H2O: Two Hands Manipulating Objects for First Person Interaction Recognition

- **書誌:** Taein Kwon et al.／2021／*H2O: Two Hands Manipulating Objects for First Person Interaction Recognition*／ICCV 2021、査読あり／IDは今回の確認範囲では不明。citeturn602119search7
- **読んだ範囲:** 要旨・dataset description。
- **方向:** 3。
- **視点／ドメイン:** 一人称／日常操作。
- **注釈:** 左手・右手の3D pose、object 6D pose、interaction/action labels。
- **左右／両手:** 左右を独立poseとして持つ代表的datasetであり、bimanual actionを明示的に扱える。citeturn602119search7
- **下流利用:** HandFormerがH2Oで3D hand poseをaction recognitionへ利用し93.39% accuracyを報告している。これはH2O GT pose利用条件を含むが、左右区別を削除したcontrolled ablation値は今回確認できなかった。citeturn382618search26
- **要点:** **左右／両手情報を検証するdataset設計としてEgoSurgery-HTSの5-class構造に近い。**

### A Real-Time System for Egocentric Hand-Object Interaction Detection in Industrial Domains

- **書誌:** 2025／*A Real-Time System for Egocentric Hand-Object Interaction Detection in Industrial Domains*／arXiv:2507.13326、プレプリント。citeturn602119academia19
- **読んだ範囲:** 要旨。
- **方向:** 3、9相当。
- **視点／ドメイン:** 一人称／industrial。
- **課題:** streaming EHOI detection。
- **構造:** Mamba系action/contact認識からobject detectorを起動するcascade。
- **推論:** real-time、約30 fps。ENIGMA-51でaction recognition 38.52 p-AP、YOLOWorld hand/object detector 85.13 APと要旨で報告。citeturn602119academia19
- **今回との違い:** 情報流が主に**action/contact→active-object detector**で、ユーザーのgrasp→phase/detectorとは逆向き。
- **要点:** **online deployment自体は成立しているが、同時刻graspをphaseへ渡す直接証拠ではない。**

### IIA-Net: Anticipation for surgical workflow through instrument interaction and recognized signals

- **書誌:** Yuan et al.／2022／*IIA-Net: Anticipation for surgical workflow through instrument interaction and recognized Signals*／Medical Image Analysis／DOI 10.1016/j.media.2022.102611。citeturn395449search0
- **読んだ範囲:** 要旨。
- **方向:** 2、4。
- **視点／ドメイン:** 腹腔鏡／低侵襲手術。
- **課題:** surgical workflow anticipation。
- **interaction:** instrument–instrumentおよびinstrument–surrounding-anatomy relationsをモデル化し、recognized instrument/phase signalsと組み合わせる。
- **推論:** causal dilated MS-TCNを用い、future anticipationを行うためonline系に近い。citeturn395449search0
- **モデル状態:** multi-task/joint learning寄りであり、独立凍結したhand–instrument grasp modelではない。
- **左右手:** 手は扱わない。
- **要点:** **手術で「instrument interaction→causal workflow」を使う先行例はあるが、hand-tool graspではない。**

### Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera

- **書誌:** Shimizu et al.／2021／*Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera*／Journal of Imaging／DOI 10.3390/jimaging7020015。citeturn612061search3turn612061search10
- **読んだ範囲:** 要旨・公開本文概要。
- **方向:** 1に近い視点、実際は方向2。
- **視点／ドメイン:** 一人称／開放手術。
- **課題:** surgical tool localization/classification。
- **表現:** hand localizationとhand motionからtarget handを選び、その手が扱うtoolをclassifyする三段階pipeline。citeturn612061search10
- **問い(2):** 手情報をtool recognitionへ使うため非常に近い。ただし「別のgraspモデルを凍結しtool detectorへfeatureを渡す」構造ではない。
- **効果量:** 本文表を今回精査していないため記載しない。
- **要点:** **開放手術・一人称・hand→toolという組み合わせ自体は既発表だが、HTS型5-class grasp maskを中間教師／interfaceとして使う研究とは異なる。**

### Open surgery tool classification and hand utilization using a multi-camera system

- **書誌:** Basiev et al.／2022／*Open surgery tool classification and hand utilization using a multi-camera system*／International Journal of Computer Assisted Radiology and Surgery／DOI 10.1007/s11548-022-02691-3、arXiv:2111.06098。citeturn612061search1turn612061academia60
- **読んだ範囲:** 要旨。
- **方向:** 2。
- **視点／ドメイン:** multicamera third-person／開放手術。
- **課題:** tool classと、各toolがどちらの手に保持されるかを認識。citeturn612061search4
- **左右:** left/right hand utilizationを明示的に扱う。
- **下流工程認識:** hand utilization outputをphase recognizerへ渡す比較は確認できず。
- **要点:** **「術具クラス×左右の保持手」というEgoSurgery-HTSに近い意味変数は既に使われているが、下流phase改善は未検証。**

### EgoSurgery-HTS

- **書誌:** Darjana, Fujii, Saito, Kajita et al.／2025／EgoSurgery-HTS／Healthcare Technology Letters、査読あり／arXiv:2503.18755、DOI 10.1049/htl2.70049。citeturn696456search0turn696456academia5
- **読んだ範囲:** 本文公開版。
- **方向:** 1。
- **視点／ドメイン:** 一人称／開放手術。
- **課題:** tool、hand、hand-toolのinstance segmentation。
- **データ:** EgoSurgery由来。論文は14 distinct tool categoriesと記述しており、EgoSurgery-Tool側の15-class detection設定とはクラス定義を区別する必要がある。citeturn696456search0
- **下流利用:** phase recognition／tool detectionをHTS predictionで改善する実験は原論文にはない。
- **既発表のHTS利用:** “EgoSurgery-HTS”, “2503.18755 citing”, “EgoSurgery-HTS phase recognition”, “EgoSurgery-HTS tool detection”等で追跡したが、2026年10月31日現在、査読済み／arXivで検証可能な下流利用論文を確認できなかった。
- **要点:** **ユーザーのgrasp modelを直接検証するための注釈基盤は存在するが、「HTS→phase/tool」の橋渡し実験は今回の検索では見つからない。**

### EgoSurgery-Tool と EgoSurgery-Phase

- **書誌:** *EgoSurgery-Tool*／arXiv:2406.03095。約49k tool boxes、15 categoriesを持つtool detection dataset。citeturn696456academia7turn696456search3
- **書誌:** *EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos*／MICCAI 2024／DOI 10.1007/978-3-031-72089-5_18。citeturn696456search4
- **読んだ範囲:** 要旨・公開ページ。
- **方向:** 1。
- **Phase側:** 9 surgical phases。gaze-guided masked autoencodingにより既存SOTA比でJaccard +6.4、通常masked autoencoder比 +3.1と原論文概要は報告する。citeturn696456search4
- **Tool側:** hand boxesも多数含むが、tool detectorとHTS graspを接続する下流比較はない。citeturn696456academia7
- **ライセンス:** EgoSurgery-Tool repositoryはCC BY-NC-SA 4.0。citeturn696456search3
- **要点:** **phase、tool、HTSという三種類のannotation資源は揃っているが、その間のinteraction transfer自体は未評価。**

## 探したが見つからなかったもの

最も重要な不在は、**「独立に学習・凍結したhand–object grasp/contact predictorの出力だけを、小さなinterfaceを通して、既に凍結したobject detectorとonline action/phase recognizerの双方へ渡す」controlled experiment**である。EgoPEDが下流action側、KADがtraining-only detector側、Shiota/Helping Handsがtraining-only action側にそれぞれ近いが、三者の条件を一つに満たす研究は確認できなかった。citeturn382618search7turn938785search5turn938785search6

また、**predicted graspとground-truth graspを同一下流モデルへ差し替え、grasp accuracyと下流利得の関係を曲線として測る研究**は、方向3・4の主要文献では確認できなかった。Something-Else/STINにはGT object groundingとdetector groundingの差があり、GT版STIN+OIE 28.5に対しdetector版20.3という大きなgapが報告されるが、これはhand-grasp推論精度のoracle gapではない。citeturn938785search11 Helping Handsはpseudo-box qualityとdownstream qualityの連動を示すため最も近い。citeturn928591view4

**左右手を分けることだけを変数にしたcontrolled ablation**も乏しい。H2O、HandFormer、open-surgery hand-utilization研究はleft/rightを明示するが、「左右を潰した版 vs left/right版」を同一modelで比較した数値を今回確認できなかった。citeturn602119search7turn612061search4 同様に、**bimanual classを独立に持つことの効果**をaction/phase recognitionまたはobject detectionで切り分ける研究も見つからなかった。

**同時刻 \(t\) のinteraction predictionをonline recognizerへ入れる場合と、厳格に \(t-1\) 以前だけを使う場合の比較**も確認できなかった。online/anticipation論文では観測済みcurrent windowの情報を使うことが一般的であり、ユーザーの問いにある「同じframeの把持推論は許すがfuture frameは使わない」という細かな規約をablationした報告は見つからない。IIA-Netはcausal workflow anticipation、2025 industrial EHOI systemはstreamingだが、この比較自体は行わない。citeturn395449search0turn602119academia19

**SAMなどfoundation segmentation modelで生成したpseudo grasp maskの品質を変え、それがaction／detector downstream gainへどう伝播するか**を直接測る研究も確認できなかった。Helping Handsの「detector pseudo-box quality」、IKDの「limited labels→pseudo labels」は近いが、SAM-mask品質やbbox-overlap contact label noiseを操作したものではない。citeturn928591view4turn612061search2

**手術領域でhand-tool grasp/contact modelをphase recognitionのteacherとしてのみ使い、inference時には捨てる**研究も確認できなかった。既存手術研究はinstrument presence、instrument segmentation、instrument–anatomy/instrument–instrument interactionをphase/workflowへ使うものが中心である。Park et al.もinstrument presence等のvisual modalitiesをmultimodal fusionする研究で、hand-tool grasp teacherではない。citeturn612061search0turn612061search7

さらに、**EgoSurgery-HTSを引用して下流phase/tool detectionを実施した公開研究**は確認できなかった。検索語は “EgoSurgery-HTS phase recognition”, “EgoSurgery-HTS tool detection”, “2503.18755 citing”, “hand-tool segmentation EgoSurgery downstream” 等である。検索結果には原論文、dataset紹介、索引ページが主に現れ、問い(11)を満たす実証論文を同定できなかった。citeturn696456search0turn696456academia5

## 未検証の組み合わせ

文献を横断すると、未検証の条件は「HOIを使ったかどうか」より細かく分解できる。

第一に、**同じpredicted grasp signalについて、(a) inference-time conditioningと(b) training-only distillationを同一dataset・同一receiver・同一splitで比較する実験**が欠けている。Shiota/Helping Handsは主に(b)、EgoPEDは(a)で、receiver、dataset、taskが異なるため直接比較にならない。citeturn938785search6turn382618search0turn382618search7

第二に、**同じgrasp modelを「phase側」と「detector側」の両方へ接続し、どちらにより大きい利得があるかを比較する実験**が見つからない。既存文献からは、hand poseはverb/actionに強くobject identityには弱い一方、interaction knowledgeはactive-object detectionにも使える、という別々の証拠しかない。citeturn719868view0turn938785search5

第三に、**box-level overlapで作ったcontact labelとpixel-mask contact／grasp representationを同じ下流taskで比較する実験**が見つからない。SViT/STIN/Helping Handsはbboxまたはgraph、Shiotaはcontact-aware visual representation、contact-forecasting系はpixel map、HandFormerは3D poseと、表現ごとにdataset・modelも同時に変わっている。citeturn938785search4turn382618search0turn695620search1

第四に、**left/right/bimanualの3-way role表現と、「単にactive toolである」というbinary表現の比較**が未検証である。今回のEgoSurgery-HTSの「左手所持／右手所持／両手所持」は、既存HOI研究のcontact/no-contactより情報量が多いが、その増分がphaseまたはtool mAPに何点寄与するかを既存文献からは決められない。

第五に、**強い事前学習receiverでinteraction signalが冗長になる境界**はほぼ未定量化である。ShiotaではSlowFastからSwin-Bへ変えると複数datasetでgainが縮小または負になるが、receiverのpretraining scaleを連続的に変えた実験ではない。citeturn928591view1turn928591view2 2026年の*Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?* は、egocentric video-language modelsがhand/object/contextのspurious cuesに偏ることを報告し、hand-object masked trainingとHOI dynamics-aware decoderを提案するが、arXiv:2607.08514のプレプリント段階であり、EgoSurgery型の独立grasp interfaceとは異なる。citeturn602119academia23

第六に、**0.5 fpsの低時間解像度で「状態」型grasp signalがどこまで有効か**も未検証である。hand trajectoryや3D motionは高fpsで利益を得る可能性がある一方、left/right/tool-held/contactといった状態変数は低fpsでも保持される可能性がある。しかし、このframe-rate差だけを操作した既報は今回見つからなかった。

第七に、**動画15本程度のvideo-wise 5-fold CVで、interaction interfaceだけを学習し、三つのfeature producerを凍結する設定**も確認できなかった。既存研究の多くは大規模datasetか既定splitであり、EgoPEDやHelping Handsにも「15 videos・5 folds・receiver frozen」という組合せはない。citeturn382618search0turn382618search7

## 検索記録

検索日は**2026年10月31日**。検索結果数は検索エンジンが返す総ヒット件数ではなく、タイトル・要旨または本文を確認して今回の問いに関連すると判定した**重複除外文献数**で数えた。方向をまたぐ論文は重複するため、7方向の合計は固有文献数と一致しない。

**方向1・同じEgoSurgery:** 関連3件を確認。主な検索語は “EgoSurgery HTS”, “EgoSurgery-HTS phase recognition”, “EgoSurgery tool hand interaction”, “2503.18755 citing”, “EgoSurgery-Tool”, “EgoSurgery-Phase”。EgoSurgery-Phase、EgoSurgery-Tool、EgoSurgery-HTSを確認したが、HTS prediction→phase/toolの下流研究は0件。citeturn696456search4turn696456academia7turn696456search0

**方向2・手術一般:** 関連11件を確認し、このうち今回の問いに特に近い6件を精査した。検索語は “surgical phase recognition instrument interaction”, “hand surgical tool classification egocentric”, “hand tool interaction surgical workflow”, “instrument segmentation prompting phase recognition”, “surgical instrument detection phase recognition causal”。IIA-Net、Hand Motion-Aware Surgical Tool Localization、Open Surgery Tool Classification、Park et al.、ESIP、2026年gastric surgery tool→phase system等を確認した。ESIPはinstrument segmentationからinstrument-specific visual promptを作る2025年JBHI研究で、DOI 10.1109/JBHI.2025.3625420。citeturn395449search1

**方向3・一人称非手術:** 関連31件を確認し、本文または詳細公開ページまで読んだもの15件、要旨中心16件。検索語は “egocentric hand object contact action recognition”, “hand object interaction action segmentation”, “active object egocentric action recognition”, “next active object hand”, “hand pose action recognition assembly”, “procedural egocentric active object”, “hand object graph action anticipation”, “training only hand object action recognition”, “privileged hand object egocentric”, “interaction knowledge distillation egocentric”。Helping Hands、Shiota、EgoPED、HandFormer、Ego-OMG、contact forecasting、IKD、KAD、Furnari/Jiang next-active-object、H2O、MECCANO、VISOR、Assembly101、ENIGMA-51等を追跡した。citeturn382618search0turn938785search6turn382618search7turn382618academia60

**方向4・一般映像:** 関連14件を確認。検索語は “object-centric video action recognition interaction graph”, “object region transformer action recognition”, “compositional action recognition object interactions”, “online action segmentation object interaction”, “object relation video action recognition”。STIN、ORViT、SViT、*How Can Objects Help Action Recognition?*、Li et al. 2025等を確認した。ORViTはobject-region appearanceとobject dynamicsをvideo transformer内へ早期融合し、SomethingElse、AVA、Something-Something V2、Diving48、EPIC-KITCHENS-100で評価する。citeturn938785search0 Li et al. 2025はoff-the-shelf object detectorを外し、detectionとinteraction reasoningを同時最適化する対照系である。citeturn938785search7

**方向5・機構一般:** 関連13件を確認。検索語は “learning using privileged information video action recognition”, “multimodal distillation egocentric action”, “auxiliary object supervision video recognition”, “interaction knowledge distillation active object”, “teacher student hand object action”。Multimodal Distillation、Helping Hands、SViT、IKD、KAD、Symbiotic Attention等を確認した。SViTの重要点は、dense structured video annotationを要求せず、少数の構造付き静止画からhand-object graph knowledgeを動画へ移すことにある。citeturn938785search4

**方向6・方法論:** 関連8件を確認。主な論点は、video-wise split、future leakage、offline/onlineの違い、pseudo-label quality、pretraining overlap、強いreceiverでのceiling、少数動画でのfold variance。直接このEgoSurgery条件で統計設計を論じる論文は確認できなかった。特に、offline action segmentationのEgoPEDをonline phase認識の根拠としてそのまま数値移植することはできない。citeturn795611view2

**方向7・否定的結果:** 明示的な否定または条件依存を7件確認。検索語は “hand object action recognition ablation worse”, “hand cues not improve action recognition”, “strong backbone hand object contact worse”, “active object detector domain transfer failure”, “hand presence next active object baseline”。特に、ShiotaのSwin-B/EPIC-100での悪化、EgoPEDのAOD cross-domain failure、Furnariのhand-presenceよりobject-motion優位、Helping Handsのpseudo-box quality dependencyが明確だった。citeturn928591view2turn795611view3turn654643search5turn928591view4

問い(7)のdatasetを逆引きした結果、interaction/hand情報とaction/step temporal labelまたはobject boxの双方を持つ主要候補として、**VISOR/EPIC-KITCHENS、MECCANO、EgoPER、Ego4D FHO、Assembly101、H2O、Ego-Exo4D、ENIGMA-51、HoloAssist**を確認した。VISORはEPIC-KITCHENS上に272K manual semantic masks、9.9M dense masks、67K hand-object relationsを追加する。citeturn667648search6turn667648academia49 Assembly101はfine-grained action segmentsと3D hand posesを持ち、HandFormerで実際に下流action recognitionへ利用されている。citeturn667648search10turn719868view0 ENIGMA-51はindustrial egocentric EHOIとtemporal interaction理解を対象にする。citeturn477018search15turn477018academia51 Ego-Exo4Dはhand pose、object annotation、keystep等を同一大規模datasetで提供する。citeturn477018search0turn477018search9

これらのうち「interaction情報を既発表の下流性能へ実際に使った値」まで今回確認できた対応は、VISOR/EPIC系→Helping Hands、MECCANO→Shiota、EgoPER→EgoPED、Assembly101→HandFormer、H2O→HandFormerである。Ego4D、Ego-Exo4D、ENIGMA-51、HoloAssistについてはinteraction annotationを持つこと自体は確認したが、今回の条件に合う「interaction predictor outputを既存action/step modelへ渡したcontrolled downstream gain」の数値は確認できなかった。citeturn928591view3turn928591view1turn795611view3turn719868view0

## 解釈と提案

### 研究上まず分離すべき仮説

既存文献をEgoSurgeryへ対応づける際には、「把持情報が有用か」という一個の仮説ではなく、少なくとも**三つの異なる仮説**として扱う必要がある。

一つ目は、**工程認識にとって現在の術具クラスだけでは不足し、「誰のどちらの手がそれを能動的に使っているか」が追加情報になるか**である。HandFormerではhand geometryがobject identityよりverbに強く効き、EgoPEDではactive/contact graphが手順理解へ効いているため、この仮説と整合する既報はある。citeturn719868view0turn795611view3 一方、EgoSurgeryではtool detector自身が既にtool presenceを出すので、把持モデルから単に「scalpelがある」ことを再入力しても情報の重複になる。検証したい増分は**left/right/bimanual × active/held relation**である。

二つ目は、**術具検出にとってhand relationがclass recognitionよりlocalization／foreground selectionを助けるか**である。KADとactive-object literatureは「同クラスの複数物体から操作対象を選ぶ」ことにはinteraction priorが有用だと示す。citeturn938785search5 しかしHandFormerではhand pose単独はobject identityに弱い。したがって、検出側では「tool class featureを追加する」より、**候補boxのactive probability、hand-side relation、ROI reweighting**として使った方が既報の機構に近い。

三つ目は、**把持情報を推論時にも要求する価値があるか、それともtraining-only teacherで十分か**である。Helping Hands、Shiota、KADはいずれも後者が成立し得ることを示す。citeturn382618search0turn938785search6turn938785search5 この点は特にEgoSurgeryでは重要で、HTSのannotationがtool-box付きframesに限定されるため、推論時に常時grasp modelを要求する(a)と、annotation coverageが限定されても利用可能な(b)では実用上の意味が異なる。

### 表現の比較軸

既存文献から、表現ごとの役割はかなり異なる。

**bbox／active-object表現**は物体の選択・localizationに向く。Helping Hands、EgoPED、STIN、ORViTがこの系統である。boxはSAM maskよりannotation noiseに強く、EgoSurgery-HTSでは「どのtoolがheldかがbox overlapでほぼ決まる」というデータ生成過程とも整合する。citeturn382618search0turn382618search7turn938785search0

**mask表現**はcontact surfaceやobject state changeの空間的手掛かりを持つが、既存下流研究ではboxほど直接的なcontrolled evidenceが多くない。今回のHTS maskはSAMでboxから生成され、しかも「held判定」はmask intersectionよりbbox overlapに近いという前提なので、mask IoU自体をgraspの本質的teacherとみなすことには注意が要る。

**contact state／active flag**は次工程・現在actionのsemantic cueとして使いやすい。Shiota、EgoPED、Ego-OMGが該当する。citeturn938785search6turn695620academia11 0.5 fpsでは細かなhand trajectoryよりこの離散状態の方が安定する可能性があるが、これは既報事実ではなく今回の設定からの仮説である。

**3D hand pose**はverb/motionに強いがobject identityに弱い。HandFormerのcontrolled結果がこれを最も明確に示す。citeturn719868view0 EgoSurgery-HTSには3D poseがないため追加推定器が必要となり、15動画条件では新たな誤差源になる。

**graph表現**は「left hand–tool A」「right hand–tool B」のような関係を明示でき、EgoPED、STIN、SViT、Ego-OMGに対応する。EgoSurgeryの5-class HTSは、実際にはpixel segmentationそのものより、  
`{left hand, right hand} × {tool instance} × {held-left, held-right, held-bimanual}`  
という小さなrelational graphへ落とし込める。これは既存graph系と意味的に近い。

**言語／semantic relation**はHelping Handsや2026年VLM系で有効だが、tool vocabularyが15クラス程度で閉じ、評価動画が15本しかないEgoSurgeryでは、追加semantic priorによる効果とpretraining knowledgeの効果を分離しにくい。2026年VLM研究自体も、強いegocentric VLMが真のHOI dynamicsではなくcontext/object shortcutを利用する問題を指摘している。citeturn602119academia23

### (a) と (b) を比較する際の実験構造

既存研究に欠けているため、この設定では(a)と(b)を**同じgrasp predictor、同じfold、同じreceiver checkpoint**で比較することが重要になる。

(a)については、把持モデルのraw maskをそのまま高次元画像としてreceiverへ入れるより、**instance単位へ縮約した固定長relation vector**にする方が既存文献と対応づけやすい。例えば各tool detectionについて、`P(held-left), P(held-right), P(held-bimanual), P(not-held)`、左右handとのbbox geometry、grasp-model confidenceを作り、小さなMLP/attention interfaceだけを学習する。phase側では時刻ごとのtool-role setを、detector側では各candidate ROIへのrelation featureとして使う。これはEgoPEDのgraph feature、Helping Handsのbbox supervision、KADのinteraction priorとの対応が明瞭になる。citeturn795611view3turn382618search0turn938785search5

(b)については三種類を分ける価値がある。第一は**logit/feature distillation**、第二は**auxiliary relation prediction**、第三は**attention teacher**である。KADはprediction/attention distillation、Helping HandsとShiotaはauxiliary prediction型に近い。citeturn938785search5turn382618search0turn938785search6 この三者を混ぜると「把持情報が効いた」のか「追加lossによるregularizationが効いた」のか判別しにくいため、同じparameter budgetのdummy auxiliary headも対照として必要になる。

### 把持ラベル品質を検証するための対照

今回のHTSでは、annotation生成過程そのものが重要な交絡要因になる。SAM maskは手・tool boxをpromptとして作られ、held toolの対応はbox overlapに強く依存する。この場合、少なくとも**mask teacher、box-relation teacher、hard held-label teacher**を分けて比較しないと、改善が「高品質なpixel grasp理解」によるものか、「既存tool boxを再符号化しただけ」なのか分からない。

Helping Handsではbox supervision品質とdownstream transferに関係があったため、HTSでもteacher qualityを一つの独立変数として扱う根拠がある。citeturn928591view4 具体的には、GT HTS relation、trained grasp model relation、意図的にnoiseを加えたrelation、tool-box overlapだけで作ったrule relationを同じinterfaceへ入れる比較を置くと、**oracle gap、learned-grasp gap、annotation-construction shortcut**を分離できる。

特に、GT HTSを入れた上限がほとんどbaselineを超えない場合は、grasp predictorを改善しても下流利得は期待しにくい。一方、GTでは大きく改善しpredictedでは改善しないなら問題はgrasp estimation qualityにあり、GTとpredictedが同程度ならinterfaceまたは情報自体の価値を議論できる。このoracle analysisは既存文献で十分に行われておらず、今回の問い(8)を直接埋める実験になる。

### online工程認識での時間規約

online条件では、少なくとも二つのcausal条件を区別した方がよい。

**same-frame causal**では、時刻 \(t\) のRGBからgrasp predictorが \(g_t\) を出し、phase modelも \(t\) までの入力のみを使って \(y_t\) を出す。この場合、未来frameを使わない限り通常のonline定義と矛盾しない。IIA-Netなどcausal workflowモデルに近い。citeturn395449search0

**lagged causal**では、phase \(y_t\) に \(g_{t-1}, g_{t-2}, \ldots\) しか渡さない。これはlatencyに強い一方、0.5 fpsでは1 frameの遅延が2秒に相当するため、同一条件ではない。この2条件を分けることは、既存文献がほぼ測っていない点を明確にする。

また、grasp modelが複数frame clipを内部で使う場合、そのclipが \(t\) より後を含んでいないかを監査する必要がある。特にoffline pretrained HOI backboneをそのまま利用すると、phase model自体がcausalでもgrasp feature経由でfuture leakageが起こり得る。

### 少数動画・5-fold評価で考慮すべき点

15動画のvideo-wise 5-foldでは、平均値だけでなく**foldごとの差とpaired difference**を保存する必要がある。interfaceあり／なしは同じfold・同じfrozen backboneで比較できるため、fold-wise paired designが成立する。mAPやmacro Jaccardの改善が1–2点程度の場合、ShiotaやHelping Handsで見られた規模と同程度であり、fold構成による揺らぎと区別する必要がある。citeturn928591view0turn928591view3

また、HTS annotationがtool boxesのあるframesに限定されるため、**把持モデルを学習するframe集合と、detector／phase interfaceを学習・評価するframe集合の境界**を固定する必要がある。同一videoのtest foldからHTS training frameを使えば、receiverを凍結していてもvideo identityやprocedure-specific appearanceがgrasp model経由で漏れる。把持モデル、interface、receiverのすべてについてtest videoを完全にfold外に置くのが、今回の「動画単位5分割」という主張と整合する。

最後に、macro Jaccardとframe accuracyでは把持signalの効果が異なり得る。hand/tool relationは長いmajority phaseのframe accuracyをさらに押し上げるだけかもしれず、逆に短いphase境界や稀少phaseで有効ならmacro Jaccardの方に強く現れる。検出側もglobal mAPだけでなく、**small tool、rare class、 visually confusable class、held vs non-held instance**で分解すると、active-object literatureが想定する「interactionが効く条件」と対応づけられる。KADが問題設定として強調するのも、同カテゴリの複数objectや微妙なstate changeによってappearanceだけではactive instanceを選びにくい場合である。citeturn938785search5

総じて既存文献が支持しているのは、「手や把持を入れれば常に改善する」という一般則ではない。**interaction signalは、受け取り側がまだ持っていないrole／activity情報を補うときに改善し、receiverが強い、domainがずれる、pseudo interactionが不正確、あるいはobject identityのようにhand signalと対応の弱い量を予測すると、利得が小さくなるか負になる**という条件依存性である。ShiotaのSwin-B、EgoPEDのcross-domain AOD、HandFormerのpose-only object recognition、Helping Handsのbox-quality dependenceが、それぞれ別の角度からこの条件依存性を示している。citeturn928591view2turn795611view3turn719868view0turn928591view4
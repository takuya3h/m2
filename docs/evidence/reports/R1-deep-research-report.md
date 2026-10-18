# 検出器出力を工程・行動認識へ渡す D→P 研究の証拠地図

## 結論

本調査で最も重要な結論は、**「術具が見えている」という低次元信号だけでも工程認識には有用だが、利得の大きさは受け取り側モデル、空間情報の有無、融合位置、検出誤差に強く依存する**ということである。手術映像で最も直接的な古典的証拠は EndoNet で、Cholec80 において7次元の術具存在 confidence を視覚特徴に追加すると、phase-only の PhaseNet に対して phase accuracy が **73.0%→75.2%（+2.2 pp, Table III）**、online HHMM 後では **78.8%→81.7%（+2.9 pp, Table IV(a)）**に上がった。一方、予測術具信号を ground-truth binary presence に置き換えても **75.2→75.3%、online 81.7→81.9%** にしかならず、この設定では oracle gap が非常に小さい。citeturn1view1turn1view2

ただし、この結果を「検出情報は常に有効」と一般化することはできない。CATARACTS の DeepPhase では、同じ tool CNN 由来でも、binary presence より richer な learned tool features を LSTM に入れると外部 CATARACTS test で **68.75→78.28%（+9.53 pp）**になった一方、GRU では **71.61→68.96%（−2.65 pp）**と逆効果だった（Table 1）。つまり、**信号そのものの情報量だけではなく、受け取り側の時間モデルとの整合性が重要**である。citeturn27view0

空間情報については、単なる presence より有望な証拠がある。Park et al. は segmentation から tool の位置・大きさ・速度・相互関係を表す visual kinematics-based index（VKI）を抽出し、実手術 G40 で RGB-only SlowFast50 の **63.37% accuracy / 55.49 mF1** を、RGB+VKI の linear fusion で **69.71% / 56.76**、convolutional fusion で **67.71% / 57.41** に改善した（Table 4）。さらに PETRAW の Table 2 では、位置と大きさを表す bounding box 情報を各種運動・関係指標に加えることで phase 指標が **+4.30～+22.95 pp** 改善している。したがって、D→P では「何があるか」だけでなく、**どこに、何個、どのような幾何配置で存在するか**を残す価値が高い。citeturn28view0turn28view2turn28view3

一方、**強い工程モデルになるほど利得が縮むか**について、同一データ・同一 detector signal を弱い P と強い P に順に追加した厳密な controlled study は、本調査では見つからなかった。最も示唆的なのは、強い online Surgformer を受け取り側とする DTFormer である。Cholec80 clean では Surgformer の **92.2% accuracy / 77.8 Jaccard** に対し、mask+depth の structured scene representation のみを用いる DTFormer は **85.5% / 67.2** と大幅に悪化したが、Cholec80-C では **76.4→80.3%**、CRCD では **56.0→67.9%** と robustness/OOD 性能が改善した（Table 2）。これは「強い RGB receiver では clean benchmark 上の追加情報価値が小さい、あるいは置換すると失うが、分布ずれでは object/scene structure が再び有効」という仮説と整合する。ただし、DTFormer は純粋な tool detector output ではなく、器具・解剖構造の mask と depth を含むため、これは間接証拠である。citeturn9view0turn9view1turn9view2

oracle に関しては、**手術映像では驚くほど報告が少ない**。EndoNet の predicted-tool→GT-tool gap は 0.1–0.2 pp と小さい一方、一般映像では gap はかなり大きい。ObjectViViT の Something-Something V2 では VideoMAE baseline 64.8%、predicted boxes 使用 68.5%、GT boxes 使用 73.0%（Table 2）で、予測→oracle に **+4.5 pp** の余地が残る。DAIR でも Something-Else で detected setting 66.8% に対し、GT number 69.7%、GT matching 72.3%（Table VII）で **+2.9～+5.5 pp** の oracle gap がある。したがって、EgoSurgery では oracle 実験を独立した主要評価項目にすべきである。citeturn24view4turn22view2turn22view3

そして最も研究上重要なのは、**本調査で distance 0、すなわち「一人称・開放手術・tool→phase・online-causal」を満たす既報を確認できなかった**ことである。EgoSurgery-Phase は一人称開放手術の phase recognition を、EgoSurgery-Tool は tool/hand detection を、EgoSurgery-HTS は hand/tool/hand–tool segmentation をそれぞれ提供しているが、公開文献として detector prediction を causal phase model に小さな interface で渡し、その増分と oracle gap を測る研究は確認できなかった。したがって、ユーザーの D→P 設定は単なる EndoNet の再実装ではなく、**独立学習済み D/P、egocentric open surgery、online-causal、small learnable interface、prediction-vs-oracle**を同時に扱う点に明確な研究空白がある。citeturn12search5turn12search8turn12search11

## 調査範囲と判定基準

本調査では、①手術映像の tool/instrument→phase/workflow、②EPIC-KITCHENS 等を含む egocentric/object-centric action recognition、③Something-Something 系を中心とする一般映像の object-conditioned action recognition、の三方向を検索した。2024–2026 年を優先しつつ、EndoNet、DeepPhase、STIN/ORViT 系など、D→P の設計を理解するうえで不可欠な古典も遡った。Cholec80 は phase と tool-presence の双方を持つ代表的データセットであり、CholecT50 は instrument–verb–target と phase labels、一部 bounding boxes を提供する。PhaKIR は近年の multi-task surgical dataset として phase、instrument keypoint、instance segmentation を同一動画に持つ。citeturn0search14turn25search5turn25search7turn25academia41

「D→P」として特に重視したのは、**detector/object recognizer の prediction、score、box、ROI/latent feature、segmentation-derived feature のいずれかが downstream action/phase model の情報として実際に使われていること**である。MTRCNet-CL や LAST のように phase と tool を multi-task で同時学習する研究は重要だが、前者は shared encoder と correlation loss、後者は latent-space constraint を主眼としており、「独立した D の出力を小さな interface を介して P に渡す」というユーザーの設定とは区別した。citeturn26search11turn25search8

数値は、本文・表・図を本調査で直接確認できたものだけを記載した。特に oracle については、単に「GT を使っている」だけではなく、**prediction を同じ種類の GT signal に置換して比較できるか**を重視した。このため、DeepPhase の「GT binary tool presence 対 learned CNN feature」の比較は参考になるが、厳密な prediction→oracle replacement とは分類していない。citeturn27view0

なお、ユーザーが指定した「添付の地図 A」はこの会話から取得可能なファイルとして存在せず、内容を照合できなかった。このため以下では、ユーザー本文に明記された列と距離定義をそのまま優先した。

距離は、**0 = 一人称の開放手術映像、工程と術具、online-causal、1 = 手術映像、工程と術具、2 = 手術・医療映像で別タスクまたは offline、3 = 手術以外の映像**として判定した。「online」の記述が曖昧な論文は、未来フレームを使わないことを確認できない限り online-causal と断定していない。

## 手術映像の証拠地図

| 著者／年 | 題名 | DOI / arXiv | データセット | 信号の形 | 入れ方 | 受け取り側のモデル | 効果量（表・図） | oracle 比較 | online / offline | 距離 | 否定的結果か | 一行の要点 |
|---|---|---|---|---|---|---|---|---|---|---:|---|---|
| Twinanda et al. / 2017 | *EndoNet: A Deep Architecture for Recognition Tasks on Laparoscopic Videos* | arXiv:1602.03012 | Cholec80 | 7 tool classes の presence confidence。GTbin では7次元 binary GT | visual fc feature に tool confidence を連結し SVM、さらに HHMM | CNN feature + linear SVM + HHMM | **Table III:** PhaseNet acc 73.0→EndoNet 75.2 **(+2.2 pp)**、GTbin 75.3。**Table IV(a), online:** 78.8→81.7 **(+2.9)**、GTbin 81.9。predicted→oracle はわずか **+0.1 / +0.2 pp**。citeturn1view1turn1view2 | **あり**、明示的 | 両方を報告。ここでは online 値を重視 | 1 | **はい（部分条件）** | 最小の presence/confidence 連結だけでも改善し、当時の設定では detector prediction がほぼ oracle に達していた。 |
| Sahu, Szengel, Mukhopadhyay, Zachow / 2020 | *Surgical phase recognition by learning phase transitions* | DOI 10.1515/cdbme-2020-0037 | Cholec80 | ZIBNet が出す tool-presence labels | tool sequence を state-preserving many-to-one LSTM に逐次投入 | causal LSTM | **Table 1:** EndoNet+HHMM precision 73.7 / recall 79.6 に対し Proposed 81.8 / 80.9、precision **+8.1 pp**, recall **+1.3 pp**。ただし receiver architecture も異なるため純粋な interface ablation ではない。citeturn26search1turn26search9 | なし | **online** phase detection として構成 | 1 | いいえ | RGB downstream を用いず、tool-usage の時間系列だけでもかなり phase を説明できることを示す。 |
| Zisimopoulos, Flouty, Luengo, Giataganas, Nehme, Chow, Stoyanov / 2018 | *DeepPhase: Surgical Phase Recognition in CATARACTS Videos* | arXiv:1807.10565 / DOI 10.1007/978-3-030-00937-3_31 | CATARACTS | 21-class binary tool presence と ResNet-152 の learned tool features | 100-frame tool sequence を2-layer LSTM / GRUへ | LSTM / GRU | **Table 1, CATARACTS external test:** LSTM binary 68.75 acc / 68.50 F1 → features 78.28 / 74.92、**+9.53 / +6.42 pp**。対して GRU は binary 71.61 / 67.33 → features 68.96 / 66.62、**−2.65 / −0.71 pp**。citeturn27view0 | **準oracleのみ**。binary GT と learned feature の比較で、同形状の prediction→GT 置換ではない | 100-frame sliding-window。未来利用の厳密な online-causal 評価は明記なし | 1 | **はい** | richer internal feature は LSTM には大きく効いたが GRU では逆効果で、receiver–signal interaction が強い。 |
| Park, Chi, Park, Lee, Park, Hyung, Choi / 2022 | *Visual Modalities Based Multimodal Fusion for Surgical Phase Recognition* | DOI 10.1007/978-3-031-18814-5_2 | PETRAW、G40 gastrectomy | semantic segmentation から bbox、centroid、size、speed/velocity、tool–tool / tool–organ relation を計算した VKI | VKIを Bi-LSTM、RGBを SlowFast50。linear fusion または convolutional feature fusion | SlowFast50 + Bi-LSTM fusion | **Table 4 G40:** RGB-only 63.37 acc / 55.49 mF1 → Linear V+VKI 69.71 / 56.76 **(+6.34 / +1.27)**、Conv V+VKI 67.71 / 57.41 **(+4.34 / +1.92)**。**Table 2:** bbox追加による phase 改善 **+4.30～+22.95 pp**。citeturn28view0turn28view2 | なし | **offline**（Bi-LSTM、clip処理） | 2 | いいえ | presence より位置・大きさ・動き・相互関係を残す意義が大きい。accuracy と mF1 の最適 fusion は一致しない。 |
| Ding et al. / 2024–2025 | *Towards Robust Algorithms for Surgical Phase Recognition via Digital Twin-based Scene Representation* | arXiv:2410.20026 | Cholec80、Cholec80-C、CRCD、RT | SAM2由来 instance mask（器具+解剖）と DepthAnything depth | mask token を早い段階で CLS に加算、depth token を後段で加算。DT-Aug ではRGB特徴に補助 | **online Surgformer** | **Table 2:** clean Surgformer 92.2 acc / 77.8 Jac → DTFormer 85.5 / 67.2、**−6.7 / −10.6 pp**。Cholec80-C 76.4→80.3 **(+3.9)**、CRCD 56.0→67.9 **(+11.9)**。**Table 3:** corrupted DT-Aug 76.4→79.4 **(+3.0)**。citeturn9view0turn9view1turn9view2 | なし | **online** | 1 | **はい** | 強い RGB phase model では clean 性能を落とす一方、structured object/scene signal は corruption/OOD robustness を大きく改善した。 |

### 手術側から読み取れること

EndoNet はユーザーの「小さな界面」に最も近い古典であり、**低次元 tool score を visual phase feature に単純連結するだけでも +2～3 pp** の改善を示した。また GT tool presence が prediction よりほとんど良くならないため、少なくとも Cholec80 の EndoNet-era detector では「detector 精度をさらに上げること」が phase 改善の主要ボトルネックではなかった可能性が高い。citeturn1view1

ただし EndoNet は D と P を完全に独立学習したモデルではなく multi-task architecture である。これに対して Sahu et al. は ZIBNet の tool labels を後段 LSTM に入れるより明確な二段階構造であり、**tool presence sequence 自体に強い工程情報がある**ことを示す。ただし phase-only の「同一 LSTM + RGB」という matched control がないため、+8.1 pp を「detector interface の因果的利得」と読むことはできない。citeturn26search1turn26search9

DeepPhase は今回の問いに特に重要な否定例である。learned tool feature は LSTM では binary presence を大幅に上回った一方、GRU では逆に悪化した。したがって「detector 内部表現の方が情報量が多いから常に良い」という設計原理は成立しない。**D のどの層を渡すかと P 側 temporal interface をセットで ablate する必要がある。**citeturn27view0

Park et al. は「box は presence に比べて何を追加するか」を最も明確に示す近接証拠である。bbox そのものは位置 \((x,y)\) と大きさ \((w,h)\) を保持し、それと movement / relative relation を組み合わせると downstream task が広く改善した。同時に VKI-only は G40 で **50.53% accuracy / 34.80 mF1** と RGB-only の 63.37 / 55.49 を大幅に下回るため、object signal は画像の代替というより**補完信号**として利用する方が合理的である。citeturn28view2turn28view3

なお、2026年には腹腔鏡下胃切除93例で YOLOv8 の tool-presence prediction を Cholec80 型 binary sequence に変換し bidirectional LSTM へ渡す二段階システムも報告され、phase **accuracy 85%、F1 83%（Table 4）**を得ている。しかし「tool input なし」の matched baseline も GT tool oracle も報告していないため、D→P が何 pp 改善したのかは同論文からは判定できない。このため、証拠地図の「効果量あり」の中心行には含めず、feasibility evidence として扱った。citeturn11view0

## 一人称・一般映像の証拠地図

| 著者／年 | 題名 | DOI / arXiv | データセット | 信号の形 | 入れ方 | 受け取り側のモデル | 効果量（表・図） | oracle 比較 | online / offline | 距離 | 否定的結果か | 一行の要点 |
|---|---|---|---|---|---|---|---|---|---|---:|---|---|
| Zhou, Arnab, Sun, Schmid / 2023 | *How Can Objects Help Action Recognition?* | arXiv:2306.11726 | Something-Else、Something-Something V2、EPIC-KITCHENS | off-the-shelf detector の bbox、object heatmap、track identity | **Object-Guided Token Sampling (OGS)** + **Object-Aware Attention (OAM)**。object region を残し background token を一部保持 | ViViT / VideoMAE系 transformer | **Fig. 5:** full-token OAM により Something-Else **+2.1**, SSv2 **+1.3**, EPIC-KITCHENS **+0.6 pp**。GT boxes では前2者が **+7.3 / +6.3 pp**。**Table 2, SSv2:** VideoMAE 64.8→ObjectViViT predicted 68.5→GT 73.0。citeturn24view4turn24view0 | **あり**。SSv2 predicted→GT **+4.5 pp** | clip-based offline | 3 | **はい** | detector boxes は強い video backbone にも効くが oracle gap が大きく、「より強い detector＝より良い action recognition」でもなかった。 |
| Li, Sun, Liu, Duan, Li / 2025（arXiv 2024） | *Simultaneous Detection and Interaction Reasoning for Object-Centric Action Recognition* | arXiv:2404.11903 / DOI 10.1109/TMM.2025.3543033 | Something-Else、IKEA-Assembly | object proposals の bbox/appearance、interactive score、object representation | PatchDec → interactive-object refinement/aggregation → object features と video patch tokens を**連結し joint self-attention**、relation modeling | MViTv2 | **Table I:** Something-Else 63.4→65.8（detection multitask）→66.3（IRA）、合計 **+2.9 pp**。IKEA macro 47.6→53.2 **(+5.6)**。**Table VII:** detected 66.8→GT Num 69.7 **(+2.9)**→GT Match 72.3 **(+5.5)**。**Table VI:** layer 9=66.3, layer 13=65.7, last layer=64.4 vs baseline 63.4。citeturn22view0turn22view1turn22view2 | **あり** | 16-frame clip、offline | 3 | **はい（比較系で）** | object signal は中間層で実際に video representation へ融合する方が、最終段の late/multitask-only injection より有効。 |

この一般映像側の結果は、EgoSurgery の設計にかなり直接的な示唆を与える。ObjectViViT では SSv2 の inferred boxes を用いて **64.8→68.5%** と改善するが、GT boxes なら 73.0% まで上がるため、detector-error が downstream 利得を約半分失わせている。さらに論文著者は、human–object interaction dataset に適合した detector が最も有効で、**より強い detection backbone や open-world detector へ変更しても action recognition は改善しなかった**と報告している。したがって、mAP のみを D→P interface の品質指標とするのは危険である。citeturn24view3turn24view4

ObjectViViT にはもう一つ重要な否定結果がある。object region だけを残し background/context token を完全に捨てると性能が悪く、少量の background token を残す方がよかった。すなわち「detector が関係物体を抽出できたので RGB/global context は不要」という設計は支持されない。手術映像でも、術具は phase の強い cue ではあるものの、解剖状態、組織変形、血液、視野、カメラ位置など術具以外の情報を P から除くべきではない。citeturn24view4

DAIR は「どこで入れるか」に関して特に明確である。MViTv2 の中間 layer 9 で object information を融合すると 66.3% だが、layer 13 では 65.7%、最後の layer 15 では 64.4% に低下し、baseline 63.4%との差はほぼ消える（Table VI）。著者自身、最終層では object information が video representation に十分融合されず、単なる multitask learning に近づくと解釈している。**小さな interface であっても「classifier 直前に単純 append」だけが唯一の候補ではなく、中間 feature の attention/conditioning を試す価値がある。**citeturn22view1turn22view2

さらに DAIR の realistic detected-box comparison は否定的結果として非常に重要である。同じ MViT 系で Something-Else の baseline が 63.3% のところ、detected boxes を用いた再実装 STIN は **48.2%**、STLT は **56.9%** まで低下しており、SViT は 65.8%、DAIR は 66.8%だった（Table VII）。したがって「box を用いる」「graph/transformer で object relation をモデル化する」というだけでは改善は保証されず、**false detections を action model にそのまま信頼させる二段階構成はかなり壊れうる**。citeturn22view2turn22view3

graph 型についても同様で、DAIR の IKEA-Assembly 再実装では MViT baseline macro 47.6 / micro 79.2 に対し、spatio-temporal relation graph の STRG は **52.3 / 79.8** と macro 側は改善する一方、単純 STIN は 48.0 / 81.0 である。したがってグラフは「常に最良」ではなく、location/ROI をどう node 化し、誤検出をどう重み付けするかが本質的である。citeturn22view3

## 問いごとの統合評価

**どの信号の形が効いたか。**  
最も軽量な signal は tool presence / class probability であり、EndoNet がその有効性を直接示している。予測 confidence を visual feature に加えるだけで online accuracy が +2.9 pp 改善した。Sahu et al. では tool-presence sequence 自体から高い phase performance が得られたため、**EgoSurgery の最初の baseline として class probability vector は非常に妥当**である。citeturn1view1turn26search1

その次に強い候補は box geometry である。Park et al. の bbox+VKI と、ObjectViViT/DAIR の object boxes の結果から、**center \((x,y)\)、width/height、count、class score、時間的 displacement**を捨てる理由は乏しい。特に開放手術の一人称映像では、「器具が存在する」だけでなく「左右どちらから入っているか」「中央の術野に何本集まっているか」「手と器具の相対配置」が工程に依存する可能性があるため、fixed-dimensional geometry summary は presence-only の次に試す価値が高い。citeturn28view0turn28view3turn24view4

ROI / detector latent feature はさらに情報量が多いが、DeepPhase が示すように**最も不安定でもある**。LSTM では binary tool presence より learned tool feature が +9.53 pp 良かった一方、GRU では −2.65 pp だった。このため detector 内部表現をそのまま P に投げるより、small projection、normalization、temporal bottleneck を挟んで次元数を制限し、presence/box と独立 ablation する方が科学的に解釈しやすい。citeturn27view0

segmentation / structured scene representation は、clean in-distribution accuracy より robustness に価値が現れる可能性がある。Park et al. では segmentation-derived VKI が実手術 G40 の fusion を改善した一方、DTFormer では clean Cholec80 を悪化させつつ corrupted/OOD を改善した。これは、object-centric representation が RGB の全情報を保持するわけではないという共通した結果である。citeturn28view2turn9view0

**どんな入れ方が効いたか。**  
文献を並べると、少なくとも四種類が支持される。EndoNet の **concatenation**、Sahu/DeepPhase の **temporal-model input**、Park の **linear/convolutional multimodal fusion**、ObjectViViT/DAIR の **attention/self-attention conditioning**である。単純連結でも改善するが、DAIR の layer ablation は、object information を classifier 直前に遅く入れるより、video representation がまだ形成されている中間段階で融合する方が良いことを示している。citeturn1view2turn27view0turn28view2turn22view1

**gate はどうか。**  
今回の探索範囲では、手術 D→P において「独立 detector 出力に learned scalar/vector gate を掛ける」こと自体を主 ablation として評価し、表で明確な増分を示す文献は確認できなかった。attention、fusion、relation graph の証拠は複数ある一方、**小型 learned gate はむしろ EgoSurgery で未検証性が高い設計**である。

**否定的、逆効果の報告はあるか。**  
明確にある。EndoNet の訓練動画数10本条件では phase-only PhaseNet 65.9% に対し EndoNet 65.8% と **−0.1 pp**で、データ量が少ない条件では tool multitask の利益が消えた（Fig. 10）。DeepPhase では GRU+tool feature が −2.65 pp、DTFormer では clean Cholec80 が −6.7 pp、DAIR の realistic detector setting では STIN/STLT が RGB baseline を大きく下回った。ObjectViViT では object-only token selection が悪く、さらに強い/general detector への変更も downstream action accuracy を改善しなかった。citeturn2view1turn27view0turn9view0turn22view2turn24view3

この否定的証拠から、**「検出器に含まれる semantic information を足せば P は単調に良くなる」という仮説は棄却すべき**である。実際には、false positive/negative、detector calibration、P が既に RGB から同じ情報を内部推論していること、box-only representation による context loss、fusion placement の不適合などで利得が消える。これらは上記複数研究の結果を総合した推論である。citeturn27view0turn9view0turn22view1turn24view4

**受け取り側 P が強いと利得は縮むか。**  
現時点の証拠では「そうである」と断定できない。EndoNet は古い CNN+SVM/HHMM receiver で +2～3 pp、ObjectViViT は強い VideoMAE 系 receiver に predicted boxes を加えて +3.7 pp、DAIR も MViTv2 に +2.9 pp と、strong backbone でも利得は残る。citeturn1view1turn24view4turn22view0

ただし、**modern strong surgical P に限定すると証拠は弱い**。DTFormer の strong Surgformer では structured signal に置換すると clean performance が 92.2→85.5% に落ちた一方、OOD では改善した。LoViT のような long-context surgical phase model は高性能 phase model として存在するが、本調査では LoViT/Surgformer 級 receiver を固定し、同じ detector output を足す前後を比較する純粋な D→P ablation を確認できなかった。したがって「P が強いほど利得が縮むか」は、まさに EgoSurgery 実験で価値のある未解決点である。citeturn9view0turn26search14

**oracle gap はどの程度か。**  
文献間でかなり異なる。

| 研究 | predicted | oracle | 差 | 解釈 |
|---|---:|---:|---:|---|
| EndoNet, Table III | 75.2 acc | 75.3 GTbin | **+0.1 pp** | detector error はほぼ bottleneck でない。citeturn1view1 |
| EndoNet online, Table IV(a) | 81.7 acc | 81.9 GTbin | **+0.2 pp** | temporal smoothing 後も同様。citeturn1view1 |
| ObjectViViT SSv2, Table 2 | 68.5 | 73.0 GT box | **+4.5 pp** | box detector quality が downstream の大きな ceiling。citeturn24view4 |
| DAIR Something-Else, Table VII | 66.8 | 69.7 GT-num / 72.3 GT-match | **+2.9 / +5.5 pp** | false/missed interactive objects が大きな損失源。citeturn22view2 |
| DeepPhase, Table 1 | CNN feature 78.28 LSTM | binary GT 68.75 | 比較不能な意味で −9.53 | **信号表現が違うので厳密 oracle と解釈してはいけない**。citeturn27view0 |

この表から、EgoSurgery で oracle を測る際は **representation を変えないこと**が極めて重要である。例えば predicted box interface が \([x,y,w,h,p(c)]\) なら、oracle でも同じ形式の \([x_{GT},y_{GT},w_{GT},h_{GT},onehot(c)]\) を入れる。predicted ROI feature と GT binary vector のような比較では、「detector error」と「表現能力」の差が混ざってしまう。

## EgoSurgery の D→P 実験に対する含意

EgoSurgery-Phase は約15時間の一人称開放手術映像と9 phase を対象とし、EgoSurgery-Tool は同系統の映像に15 tool classes、4.9万件超の tool bounding boxes と4.6万件超の hand boxes を持つため、phase と spatial tool signal を接続する実験に適した構成になっている。一方、公開された Phase、Tool、HTS の論文はそれぞれ独立した認識タスクを主眼としており、本調査では D prediction を online-causal P に渡す評価を確認できなかった。citeturn12search5turn12search8turn12search11

この文献状況からは、最初から複雑な graph を採用するより、**信号情報量を段階的に増やす controlled ladder**が最も解釈しやすい。

| EgoSurgery で比較すべき interface | 文献上の根拠 | 何が分かるか |
|---|---|---|
| **Presence hard:** 15-D 0/1 | EndoNet、Sahu | 最小の semantic cue だけで phase が改善するか。citeturn1view1turn26search1 |
| **Presence soft:** 15-D logits/probabilities | EndoNet の confidence、oracle gap | uncertainty を残す価値。hard threshold が情報を失っているか。citeturn1view2 |
| **Count + geometry:** class別 count、mean/top-k \((x,y,w,h,score)\) | Park、ObjectViViT | spatial configuration が presence を越えて効くか。citeturn28view0turn24view4 |
| **Set of boxes:** top-K object tokens + positional encoding | ObjectViViT、DAIR | 固定集約で失う object–object / hand–tool relation の価値。citeturn24view4turn22view0 |
| **ROI features:** detector ROI/head feature を小 projection で圧縮 | DeepPhase、一般 object-centric models | detector の内部 appearance representation が必要か。citeturn27view0turn21view0 |
| **Hand–tool relation:** hand box と tool box の距離、overlap、相対位置 | EgoSurgery-Tool/HTS、Park | 一人称開放手術特有の manipulation cue の増分。citeturn12search8turn12search11turn28view3 |

融合方法については、少なくとも **late concat、causal temporal adapter、cross/self-attention の三段階**を同じ D/P で比較する価値が高い。EndoNet は concat でも改善した一方、DAIR では最後の層に入れるより中間層で object signal と video tokens を相互作用させる方が良かったため、「signal の種類」と「interface の種類」を同時に変えず、二軸に分離すべきである。citeturn1view1turn22view1

ユーザーの「small learnable module」という制約を守るなら、特に重要なのは **D と P の backbone を凍結し、interface だけを学習する条件を一つ独立に置くこと**である。EndoNet、MTRCNet-CL、LAST、DAIR の一部は D/P 表現そのものが joint training で変化するため、そこで見られる利益には auxiliary supervision や shared-representation learning の効果も混ざる。独立 D/P + frozen interface experiment は、この confound を除去できる。citeturn1view2turn26search11turn25search8turn22view0

oracle は少なくとも **GT presence、GT box、GT class+box** の三段階を、予測版と同じ dimensionality/interface で作るべきである。さらに「GT class + predicted geometry」「predicted class + GT geometry」を分ければ、oracle gap が **classification error 由来か localization error 由来か**まで分解できる。一般映像で predicted→GT box の差が 4.5～5.5 pp に達する一方、EndoNet の presence oracle gap は 0.1～0.2 pp しかないため、この分解には十分な先行研究上の動機がある。citeturn1view1turn24view4turn22view2

また、強い P で利得が縮むかを答えるには、「弱い P と強い P の絶対性能を別論文から比較」してはいけない。同じ split、同じ D predictions、同じ interface capacity で、少なくとも **P-small / P-strong × RGB-only / RGB+D** の交互作用を見る必要がある。DTFormer の clean negative result は、この実験を行う価値が高いことを示すが、それ自体は純粋な D→P scaling law の証明ではない。citeturn9view0

特に online-causal の研究では、次の leakage を分離する必要がある。Sahu の state-preserving LSTM は online の良い近接例だが、Park は Bi-LSTM なので未来情報を使う。DeepPhase は100-frame sliding window であり厳密な causal protocol が明示されていない。一般映像の ObjectViViT/DAIR も video clip 全体を処理する。したがってこれらの精度を EgoSurgery online-causal の期待値として直接比較することはできない。citeturn26search1turn28view4turn27view0turn22view0

さらに、文献であまり統制されていない前提として、**tool–phase correlation 自体の shortcut**がある。器具の種類や組合せが phase をほぼ決めるデータセットでは D→P が高く見える一方、病院・術者・手術手技が変われば相関が変わる可能性がある。DTFormer が clean と OOD で逆方向の結果を示したことや、ObjectViViT が detector の一般的な強さより domain-specific detection を重視したことは、この問題と整合する。したがって EgoSurgery では通常 test に加え、surgeon/procedure/site による distribution shift split が可能なら別に評価する価値が高い。citeturn9view0turn24view3

否定的対照としては、**時間 shuffle した tool signal、別動画から取った tool signal、class-frequency を保ったランダム signal**も有用である。これにより、小型 interface が「真の tool–phase relation」を使っているのか、単に追加 parameter や時間 prior で改善しているのかを区別できる。EndoNet の small-data 条件で tool-aware model の利益が消えたこと、DAIR で late/multitask-only injection の効果が小さかったことからも、追加分岐そのものを control する必要がある。citeturn2view1turn22view1

総じて、現時点で EgoSurgery に対して最も情報量の高い実験系列は、**soft tool probabilities → probabilities+count/box geometry → top-K object tokens/ROI features**と signal を段階的に増やし、それぞれを **concat → causal temporal adapter → small attention interface**で比較する構成である。その上で prediction/GT oracle を同じ interface のまま切り替え、P の強弱も交差させれば、ユーザーの問い（1）～（5）をほぼ一つの factorial study で分離して答えられる。これは EndoNet、DeepPhase、Park、ObjectViViT、DAIR の結果を総合した設計上の推論である。citeturn1view1turn27view0turn28view2turn24view4turn22view1

## 探したが見つからなかったもの

以下の「件数」は検索エンジン全体のヒット総数ではない。使用した検索環境はデータベース全体の総ヒット数を安定して返さないため、**本調査で検索結果から題名・抄録・本文を照合した主要なユニーク候補数**と、そのうち今回の厳密な D→P 条件を満たした件数を示す。したがって systematic-review の PRISMA count ではなく、今回の evidence-map 作成時の screening count である。

| 検索対象・検索語 | 主な候補を精査した件数 | 厳密な D→P 該当 | 探したが見つからなかった内容 |
|---|---:|---:|---|
| `EgoSurgery tool phase recognition detector output` / `"EgoSurgery-Tool" phase recognition tool features` | **3**（Phase, Tool, HTS） | **0** | 一人称開放手術、独立 tool detector prediction→online-causal phase model の実験、prediction-vs-oracle。EgoSurgery の公開研究は現時点では task ごとに分かれている。citeturn12search5turn12search8turn12search11 |
| `AutoLaparo phase instrument tool detection workflow` | **2** | **0** | AutoLaparo は workflow と instrument/anatomy segmentation を同一ベンチマークに含むが、segmentation/detection prediction を phase receiver に明示的に渡す controlled ablation は確認できず。citeturn14search13 |
| `HeiChole phase instrument fusion` / `HeiChole phase instrument recognition` | **2** | **0** | phase、instrument、action を併設するが、challenge の各 task score ではなく「instrument output→phase model」の増分を測る研究は確認できず。citeturn14search30 |
| `CholecT50 phase recognition tool detection instrument phase fusion` | **4** | **0** | CholecT50 は instrument–verb–target、phase、subset boxes を持つが、tool detector output を phase に入れ predicted-vs-no-D/oracle を比較する論文は今回の検索では確認できず。citeturn25search5turn25search7 |
| `CATARACTS surgical phase recognition instrument detection tools workflow recognition` | **3** | **1** | DeepPhase は発見。だが、**同形状 predicted binary presence→GT binary presence**の厳密 oracle は見つからず。citeturn27view0 |
| `M2CAI16 workflow phase instrument detection tool presence surgical` | **3** | **0** | workflow と tool-presence の双方に関連する文献はあるが、同一 detector prediction を downstream phase model に渡す matched D→P ablation は確認できず。M2CAI workflow の multi-task architecture は存在するが独立-interface 実験ではない。citeturn25search11 |
| `surgical phase recognition instrument presence detection Cholec80 tool phase 2024 2025 2026` | **10以上の主要候補を精査** | **直接型は少数** | 2024–2026 の主流は phase backbone 改良、multi-task learning、VLM、robustness であり、「frozen independent detector output を small interface だけで strong causal phase model に追加」の controlled study は確認できず。citeturn25search0turn26search14 |
| `surgical phase tool ground truth predicted oracle` に相当する検索 | **EndoNet、DeepPhase、近接研究を精査** | **厳密同形状 oracle は1研究** | 手術領域で prediction と GT を同じ interface に置換して downstream gap を明示した例は EndoNet が最も明確。DeepPhase は binary と latent feature が異なる。citeturn1view1turn27view0 |
| `surgical phase detector output gate` / detector signal gating | **関連 fusion/attention 文献を精査** | **0** | 独立 D の output に小型 learned gate を置き、その gate 自体を phase ablation した明瞭な surgical report は確認できず。attention、concat、temporal fusion の証拠はある。 |
| `strong surgical phase model instrument/tool fusion Surgformer LoViT` | **複数の strong phase models を精査** | **controlled scaling comparison 0** | 同じ D signal を弱い P と強い P の双方へ加え、「P が強いほど D→P gain が縮むか」を直接検定した論文は確認できず。DTFormer が最も近いが signal と representation の両方が変わる。citeturn9view0turn26search14 |
| `SomethingElse detected boxes ground truth action recognition` / `object detector output action recognition oracle` | **ORViT/STIN/ObjectViViT/DAIR 系を精査** | **複数** | ここでは逆に oracle gap の証拠が豊富で、ObjectViViT の **4.5 pp**、DAIR の **2.9–5.5 pp**が EgoSurgery の oracle 設計に最も直接転用できる。citeturn24view4turn22view2 |

以上を踏まえると、既報でかなり確立しているのは **「object/tool signal は downstream action/phase recognition に役立ちうる」「presence より spatial/interaction signal に追加価値がある」「prediction noise と fusion design により容易に利得が消える」「oracle gap はデータセットによりほぼゼロから5 pp超まで大きく変わる」**という点である。逆にまだ確立していないのは、**一人称開放手術で、独立学習済み detector と強い online-causal phase model を凍結し、小さな learnable interface だけを学習した場合の D→P gain、その receiver-strength dependence、および同形状 oracle gap**である。EndoNet、DeepPhase、DTFormer、ObjectViViT、DAIR を合わせても、この組合せを直接評価した研究は本調査では確認できなかった。citeturn1view1turn27view0turn9view0turn24view4turn22view2
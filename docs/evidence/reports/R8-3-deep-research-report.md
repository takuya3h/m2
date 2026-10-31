# 一人称視点映像における手–物体相互作用を下流認識・検出へ利用する研究の文献調査

## 結論の先取り

今回確認できた範囲では、**「把持／手–物体相互作用モデルを独立に学習して凍結し、その出力を別個に学習された物体検出モデルと工程・行動認識モデルの双方へ後付けして改善する」研究は見つからなかった**。特に、EgoSurgery-HTS を用いて、その 5 クラスの手–術具関係を **EgoSurgery-Tool の検出器**または **EgoSurgery-Phase の工程認識器**へ流し、mAP／Jaccard の改善を報告した既発表研究は、2026年10月31日時点で確認できなかった。EgoSurgery-HTS 自体は手・術具・手–術具セグメンテーションのベンチマークに留まり、論文中の実験も下流の工程認識・術具検出改善ではない。citeturn950224search0turn950224search2

ただし、ユーザーの案に非常に近い研究は複数ある。**(a) 推論時にも相互作用出力を使う型**として最も近いのは Ma & Damen の *Hand-Object Interaction Reasoning* で、事前学習済み hand–object detector の出力から左右手と active object の軌跡を作り、相互作用 Transformer を RGB 動画表現へ加える。EPIC-KITCHENS-100 では SlowFast 36.76% action top-1 に対し IRN 37.11%で、verb +0.04、noun +0.36、action +0.35ポイントだった。論文図では hand/object detector の重みが凍結されており、構造として今回の「凍結把持器＋小型界面＋工程モデル」にかなり近い。citeturn623842academia8turn845772search22

もう一つ近いのが EgoPER の *Error Detection in Egocentric Procedural Task Videos* で、active-object detector による手・active object の関係をグラフ化し、GCN の relational feature を動画特徴と結合して action segmentation／error detection に入れる。これは **(a)** に属するが、「把持専用モデル」ではなく active-object detection を前段とする点が異なる。citeturn182326search0turn182326search9

**(b) 学習時だけ使う型**には、むしろ強い先行例がある。*Helping Hands* は外部 hand-object detector の noisy pseudo-label から手・active object の位置と object semantics を補助教師にし、推論時は RGB のみとする。*Egocentric Action Recognition by Capturing Hand-Object Contact and Object State* は hand-object detector から作った interaction-focused input を共同学習・補助損失として使い、推論時は raw RGB のみで、最大 +2.24ポイント（EGTEA）、+3.97（MECCANO）、+1.49（EPIC-KITCHENS-100）を報告する。*Multimodal Distillation for Egocentric Action Recognition* は object detections を含む multimodal teacher から RGB-only student へ蒸留する。したがって、今回の **(b) は十分に文献上の根拠があり、(a) より既存研究との差別化を設計しやすい**。citeturn836387academia52turn438260view1turn836387academia51

手術側では、*Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera* が、手検出・手の時系列運動を、形状の似た scissors と needle holder の識別に利用し、通常の tool-detection baseline を上回った。これは「手情報で術具検出を改善」という問い(2)には直接該当するが、**把持関係モデルを独立に凍結した構成ではない**。citeturn950224search3

## 一人称非手術映像で最も直接的な先行研究

### 行動・工程・手順認識へ手–物体情報を入れる研究

この系統で今回の設計に最も近い論文群を、実装上の対応関係まで含めると次のようになる。

| 研究 | HOI 表現 | 下流への入れ方 | 推論時 HOI 必要 | 主な効果 | 今回との対応 |
|---|---|---|---|---|---|
| Ma & Damen, *Hand-Object Interaction Reasoning* | 左右手 bbox、各手に対応する active-object bbox、時系列軌跡、RoI feature | frozen detector → trajectory/interaction Transformer → RGB action feature | 必要 | EPIC-100 action 36.76→37.11、noun 48.58→48.94 | **(a) 最も近い** |
| Lee et al., EgoPED | hand/active-object box と関係 graph | active-object detection → GCN relational feature → action segmentation/error model | 必要 | active-object relation の追加で action/error understanding 改善 | **(a) 近い** |
| Shiota et al., HOCL/OSL | hand–object contact bbox、object state | interaction-only video と raw video の協調学習＋state auxiliary loss | 不要 | EGTEA 最大 +2.24、MECCANO +3.97、EPIC-100 +1.49 | **(b) 非常に近い** |
| Zhang et al., *Helping Hands* | 手 bbox、object bbox、object semantics | detector pseudo-label を decoder の補助教師 | 不要 | egocentric retrieval/classification/grounding を一貫して改善 | **(b)** |
| Radevski et al., Multimodal Distillation | object bbox＋class、flow/audio | multimodal teacher → RGB student の logit distillation | 不要 | RGB-only student が通常 RGB training を上回る | **(b)** |
| Wang et al., SAP | object detection feature＋位置 | privileged branch から verb/noun branch へ attention | 学習設計上 privileged | EPIC-KITCHENS 等で SOTA | **(b) 的** |
| Shamil et al., HandFormer | 左右 3D hand pose＋RGB | pose token と RGB token を multimodal Transformer で融合 | 必要 | Assembly101/H2O で SOTA | (a)だが pose |
| Kwon et al., H2O | 左右 3D hand pose、6D object pose、graph | joint pose estimation → graph action classifier | 必要 | two-hand/object pose で interaction recognition 改善 | (a)、3D系 |

IRN は左右手を別 entity として扱い、各手に対応する active object を明示的に結びつける。論文は、両手を含む full trajectory が middle-frame detection や片手中心の表現より良いと報告している。したがって、EgoSurgery-HTS の **own-left / own-right / left-tool / right-tool / bimanual-tool** というラベル構造は、IRN の仮定と非常に相性が良い。citeturn623842search1turn845772search22

ただし、IRN の絶対改善量は強い SlowFast baseline 上では +0.35 action top-1 に留まる。この数字は重要で、**強い RGB backbone が既に HOI の多くを内部表現している場合、明示 HOI の追加利得は小さくなりうる**ことを示す。逆に Something-Else の ablation では trajectory・左右相互作用・spatial positional encoding の寄与がより大きく、HOI 表現は compositional/generalization 条件で価値が高い。citeturn845772search22

Shiota et al. の HOCL は別の重要な設計である。100DOH 系 hand-object detector で手・接触物体を抽出し、それ以外を抑えた動画を第二 branch に入力し、raw-video branch と協調学習させる。推論時には第二 branch を捨てるので、今回の案 **(b)** にほぼそのまま対応する。さらに OSL は object state の開始・終了から擬似的な frame-level state target を作り、補助損失で action representation を鍛える。MECCANO では SlowFast Acc@1 が 38.08 から HOCL 単独 42.05へ上がる一方、Swin-B では HOCL 単独が 44.03→42.01 と悪化し、HOCL+OSL で 44.81まで戻る。この結果は、**HOI auxiliary signal は backbone によって利得の符号まで変わる**という、今回の実験計画に直結する警告である。citeturn893665view0turn799522view1

HandFormer は表現の比較に有用である。3D hand pose は特に verb に強く、RGB は object identity に強いと論じ、Assembly101 では single RGB view 35.27% action に対し single-view+pose が 41.06%、verb は 58.27→69.23となった。一方 object は 47.45→51.17で、**姿勢は動詞・運動を強く補い、物体クラスの補助としては相対的に弱い**。今回の grasp class は pose より低次元だが、「左右手＋どの道具を保持しているか」は phase/action の動詞性と noun/tool identity の両方を含むため、pose-only より下流互換性が高い可能性がある。citeturn438260view2turn893665view2

### training-only の相互作用教師

*Helping Hands* は今回の疑似ラベル条件に特に重要である。外部の hand-object detector が作った**疎で noisy な bounding-box pseudo-label**を利用して、hand box、active-object box、object semantic label を Transformer decoder に予測させるが、推論時にはその decoder も検出器も不要で、通常の RGB video encoder として使える。著者らは、ノイズのある image-level detection でも時間的一貫性を通じて良い object-aware representation が得られることを示した。citeturn771495search11turn836387search6

これは EgoSurgery-HTS にとって重要である。EgoSurgery-HTS の segmentation mask は既存 bbox を SAM に与えて生成され、手–術具 association も IoU に基づき、その後 human review/correction が行われる。つまり、**mask geometry 自体より「どの手がどの術具と対応するか」という association label の方が本質的 supervision である可能性が高い**。この状況では、高精細 mask を直接 feature として渡すより、mask から「L-hand holds tool k / R-hand holds tool k / bimanual tool k」の低次元 target を作り、Helping Hands 型に training-only auxiliary target として使う方が、annotation-generation mechanism と整合的である。これは文献からの推論であり、EgoSurgery-HTS 自身は downstream 実験をしていない。citeturn950224search0

Multimodal Distillation はさらに強い根拠を与える。Something-Something では RGB baseline 60.3% action@1 に対して、RGB+object-detection teacher から蒸留した RGB student が 63.2%、RGB+flow+object teacher からの student が 63.0%だった。一方、弱い modality を teacher ensemble に加えると student を悪化させることもあり、著者らは teacher weighting を導入している。したがって、**把持モデルの精度が十分でない場合、単純な teacher forcing より confidence-weighted distillation が安全**である。citeturn893665view1turn799522view0

## 物体検出・active object と次に持たれる物体

問い(2)については、行動認識ほど「HOI を別モデルとして推論し、その出力で通常物体検出 mAP を上げる」研究は多くない。代わりに、egocentric vision では **active object detection** 自体が独立タスクとして発展しており、「画面にある物体」と「手が現在／次に操作する物体」を分けることが中心問題になっている。MECCANO は temporal action segment と contact 中の active-object boxes を両方持ち、64,349 active-object annotations と 48,024 next-active-object annotations を提供する。citeturn831360search3turn831360search9

Fu et al. の *Sequential Voting with Relational Box Fields for Active Object Detection* は、active object の box を単なる appearance detector ではなく、hand/object/background pixel からの relational voting で更新する。これは HOI の空間構造が active-object localization を改善する典型例である。citeturn115999search11

Furnari et al. の *Next-active-object Prediction from Egocentric Videos* はさらに online 条件に近い。既存 object detector/tracker の object trajectory を入力し、**過去に観測した位置、scale、位置変化・scale変化**から「次に active になるか」を判定する。ADL データで appearance や hand-presence cue より trajectory cue が良く、未来 interaction を数秒前に検出できる例を示した。つまり、単純な「手の近くにある物体」より、**手に向かう相対運動・接近過程**の方が future active-object prediction では強い。citeturn223666search0turn223666search1

Ego4D の Short-Term Anticipation も、contact frame とその前の 0.5、1.0、1.5秒に hand/object boxes を付け、次に触る noun、verb、time-to-contact を予測する構成である。したがって、next-active-object を工程認識へ入れる場合、「現在保持している術具」だけでなく **次に保持されそうな術具**を anticipation feature として使う設計も文献的に自然である。citeturn831360search4turn831360search5

NAOGAT はさらに明示的に next-active-object prediction と future action prediction を同一 Transformer で結合し、Ego4D と EPIC-KITCHENS-100 unseen setting で既存 anticipation method を上回る。ここでは物体 dynamics が future action の context になる。citeturn223666search3

一方、問いで重視されていた「稀少クラス、小物体、紛らわしいクラスへの個別効果」は、HOI→検出の文献では十分に分解報告されていない。Shiota et al. は tail-class 評価を行い、HOCL/OSL が少数クラスや unseen scene に比較的効くことを報告しており、これは検出ではなく action recognition だが、**少数クラスで interaction prior が効きやすい**という根拠になる。citeturn438260view1

手術ではこの点に非常に直接的な例がある。Shimizu らの egocentric open surgery 研究では、scissors と needle holder のように外観が似て tool tip が隠れやすい場合に、**手の時系列運動が tool class discrimination を助ける**ことを利用し、hand localization と ResNet-LSTM motion classification を組み合わせて baseline より良い識別を得た。EgoSurgery-Tool が抱える「similar shape / similar texture / occlusion」という難しさとも一致するため、把持関係を detector に戻す案は特に混同しやすい tool pair に効く可能性がある。citeturn950224search3turn215386academia12

## 表現・左右手・両手・オンライン制約

### 表現系ごとの傾向

既存研究を表現で整理すると、かなり明確な傾向がある。

**bbox／軌跡**は最も軽く、action recognition・active object detection・anticipation に実績が多い。IRN、Furnari、NAOGAT、EgoPED がこの群である。特に bbox trajectory は低フレームレートでも保持可能なため、EgoSurgery の 0.5 fps には mask dynamics より相性がよい可能性が高い。citeturn623842academia8turn223666search1turn223666search3

**mask**は手と active object の localization／segmentation には強いが、action recognition へ直接 feature として入れる研究は bbox より少ない。VISOR は 271K sparse masks、dense interpolation、67K in-hand object relations を提供し、hand-object segmentation の代表的資源であるが、VISOR の主要 benchmark は VOS/HOS であり、mask を action classifier に後付けして定量改善することが中心ではない。citeturn831360search7turn831360search8

**contact state**は特に action recognition と streaming system に向く。Shiota の HOCL は contact-localized crop/mask を training signal にし、2025年の ENIGMA-51 real-time system は contact action recognizer が contact を検知した時だけ object detector を起動する cascade を採用している。後者は 30 fps streaming で action module 38.52% p-AP、YOLOWorld hand/object detector 85.13% AP と報告する。citeturn223666academia11

**3D hand pose**は verb・微細運動認識に特に有効だが object identity を単独では表せない。HandFormer の ablation はこの点を定量的に示す。H2O も left/right hand 3D pose と object 6D pose を graph に入れて interaction class を認識する。citeturn438260view2turn115999search1

**graph**は procedural segmentation/error detection と相性が良い。EgoPED は active object / hand relation を graph feature として frame/video feature に補う。ユーザーの「小型界面」は、把持モデルの dense mask を直接渡すより、`{left hand, right hand, tool class, held-by relation}` の小規模 graph token に圧縮する設計が文献的には近い。citeturn182326search0

**言語／VLM 表現**は2025–2026年に急速に増えた。ICLR 2025 の *Modeling Fine-Grained Hand-Object Dynamics for Egocentric Video Representation Learning* は detector＋LLM で hand-object dynamics narrations を生成して representation learning に使う。2026年の Tateno et al. は hand/object region を分離して補助 grounding と semantic alignment を行い、標準 action recognition と object-state recognition を改善した。citeturn182326search21turn390225academia10

### 左右手と両手

左右を区別する根拠はかなり強い。IRN は left hand と right hand、それぞれに対応する active object を分離し、さらに hand–hand relation をモデル化する。著者らは two-handed interaction の modeling が重要と結論している。citeturn623842academia8

H2O は左右手の 3D pose と manipulated-object pose を同時に持つ dataset／model で、inter-hand と hand-object の双方の dependency を graph convolution で扱う。citeturn115999search1

Assembly101 は 18M 3D hand poses と 100万超の fine action segments を持ち、HandFormer の検証基盤になっている。citeturn399943search0

この文献群からみると、EgoSurgery-HTS の **左手保持、右手保持、両手保持**を one-hot 3 class に潰すより、少なくとも
`left-hand state + right-hand state + tool identity + bimanual flag`
を別 token／feature として保持する方が妥当である。特に needle holder と tweezers のような典型的な両手協調では、「同時に何を持っているか」が工程文脈になりうる。EgoSurgery-HTS 自体も needle holder/tweezers などに強い co-occurrence を報告している。citeturn950224search0

### online 制約

厳密な online 研究は、trimmed action recognition より anticipation 系に多い。Furnari の next-active-object prediction は sliding window 内の過去 object trajectories のみを使い、未来の activation を予測するので明確に causal である。citeturn223666search1

Ego4D STA も observation clip の後に起こる interaction を予測するため causal である。citeturn831360search4

ENIGMA-51 の real-time system は streaming contact recognition を行い、**同じ時刻の contact prediction が object detector を起動**する構造である。したがって「現在フレームの grasp prediction を工程モデルへ入れる」こと自体は online の定義と矛盾しない。ただし工程モデルが時刻 \(t\) の出力を出す際、把持器も \(t\) の RGB を見るなら、その把持特徴は同時刻情報であり、未来リークではない。一方、把持モデルが将来フレームを使う bidirectional temporal model なら不適切である。citeturn182326academia49

EgoSurgery が 0.5 fps であることを考えると、長い optical-flow style motion より **現在 frame の L/R grasp state＋過去数 frame の状態列**が現実的である。Furnari 型の trajectory cue を使うなら、座標よりも `held/not-held` の状態遷移、tool switch、bimanual onset/offset の方が安定しやすいと推測される。これは既存研究の直接結果ではなく、データ条件からの設計推論である。citeturn215386search1

## データセットと既発表の下流利用

問い(7)に該当する主要資源は次の通りである。

| Dataset | HOI/hand 注釈 | action/step 注釈 | object box | 既発表の下流利用 |
|---|---|---|---|---|
| EPIC-KITCHENS + VISOR | hand/active-object masks、contact relation | verb/noun/action segments | あり | IRN、Helping Hands、HOCL、distillation、OCT 等 |
| MECCANO | hand boxes、active objects、next-active objects | 61 action classes / temporal segments | あり | HOCL/OSL、active-object/anticipation benchmarks |
| Ego4D FHO | L/R hand boxes、tool/object roles、contact/pre/post | narrated action/verb/noun | あり | STA、state-change detection、hand-object forecasting |
| Assembly101 | L/R 3D hand pose、hand-object crops | >1M fine action segments | 部分的 | HandFormer、action/anticipation/segmentation |
| H2O | L/R 3D hand pose、object 6D pose | interaction class | あり/pose | H2O graph recognizer、HandFormer |
| HOI4D | hand pose、interaction object motion masks | frame-level action segmentation | あり/3D | HOI/action segmentation baselines |
| EgoPER | hand tracking modality、active-object boxes | frame-wise procedural step | あり | EgoPED relational GCN |
| ENIGMA-51 | hand boxes、active/next objects | 14,036 temporal HOIs | あり | HOI detection、STA、real-time contact cascade |
| HoloAssist | hand pose、depth/gaze | fine/coarse action/conversation | — | hand forecasting、mistake/intervention tasks |
| EgoSurgery-HTS | L/R own hand＋held tool masks＋bimanual | EgoSurgery-Phase と共有可能 | EgoSurgery-Tool にあり | **下流改善の発表なし** |

VISOR は EPIC-KITCHENS-100 上に構築され、pixel masks と temporal action annotations を自然に対応付けられる点で、EgoSurgery-HTS に最も近い非医療データである。citeturn831360search7turn831360search8

MECCANO はさらに今回の「小さい tool/parts、active object、手順」の条件に近い。20人が toy motorbike を組み立てるデータで、20 object classes、12 verbs、61 actions、64,349 active-object frames、89,628 hand boxes を持つ。citeturn831360search3

EgoPER は5種の cooking procedure、28時間、frame-wise step labels、object boxes、active-object flags を持つため、「工程認識＋active object relation」の直接的 benchmark である。citeturn399943search5turn399943search7

HOI4D は frame-level action class、2D motion segmentation、MANO hand pose を同時に持つ。citeturn399943search6

Assembly101 は procedural segmentation の規模が突出して大きく、1M超の fine actions と18M hand posesを持つ。citeturn399943search0

ENIGMA-51 は小規模動画本数という意味で特に参考になる。51本・19人・22時間で、275,135 object boxes、56,473 hand boxes、9,342 active objects、37,314 next-object interaction annotations を持つ。citeturn831360search0

## 否定的結果、精度依存、少量データ、疑似ラベル

問い(8)で最も重要なのは、「HOI を入れれば必ず改善する」という結果ではないことである。

Shiota et al. では MECCANO の Swin-B に HOCL 単独を入れると Acc@1 が 44.03 から 42.01 に下がった。OSL 単独は 44.00、HOCL+OSL は 44.81である。強い transformer backbone では単純 contact supervision が冗長・競合しうる。citeturn893665view0

IRN でも EPIC-KITCHENS-100 の強い SlowFast に対する action 改善は +0.35ポイントで、大幅ではない。citeturn845772search22

Multimodal Distillation はさらに明瞭で、弱い modality-specific teacher を ensemble に追加すると student が悪化する場合がある。つまり downstream gain は teacher quality に単調ではなく、**teacher の reliability と downstream task との情報整合性**に依存する。citeturn893665view1

2025–2026年の EgoVLM 研究も同じ問題を別角度から示す。ICLR 2025 の *Do Egocentric Video-Language Models Truly Understand Hand-Object Interactions?* は、大規模 EgoVLM が noun/verb を少し変えた negative caption に弱く、standard benchmark の高性能が必ずしも fine-grained HOI reasoning を意味しないことを示した。citeturn390225search6

2026年の Tateno et al. も、既存 EgoVLM が背景・物体 identity などの shortcut に頼り、hand cue と object cue を独立に利用できない問題を示している。これは「強い事前学習受け取り側だから HOI は不要」という単純な話ではなく、**性能飽和で明示 HOI の top-line gain が小さくても、cue robustness には価値が残る**ことを意味する。citeturn390225academia10

少量データに関しては、MECCANO、ENIGMA-51、EgoPER が比較的近いが、**15動画程度で hand-object model をゼロから学習し、annotation noise と downstream gain の関係を系統的に曲線化した研究は見つからなかった**。Shiota et al. は少数クラスで HOCL/OSL が有効であることを示すが、training-video count を数十本まで減らす実験とは異なる。citeturn438260view1

疑似ラベル研究としては Helping Hands が最も直接的で、off-the-shelf detector の noisy sparse boxes を補助教師として有効利用している。citeturn836387academia52

一方、EgoSurgery-HTS は SAM に bbox prompt を与えて masks を生成し、手–tool association を IoU から決定し、その後 manual correction を行っている。したがって「SAM mask quality が downstream gain にどう効くか」は未検証であり、ここは今回の研究が明確に埋められる空白である。citeturn950224search0

## 手術文献、系統的位置づけ、EgoSurgery への示唆

EgoSurgery 系では、EgoSurgery-Phase が 9 phases・約15時間の egocentric open-surgery 動画を提供し、gaze-guided MAE が従来 SOTA より Jaccard +6.4ポイント、通常 MAE より +3.1ポイントを報告している。これは HOI ではないが、「RGB 以外の術者中心 prior を training に入れると phase recognition が上がる」という重要な先例である。citeturn950224academia7

EgoSurgery-Tool は 15 tool classes、49K超の tool boxes、46K超の hand boxesを持ち、class imbalance、similar shape/texture、occlusion を主要課題として挙げる。citeturn215386academia12

EgoSurgery-HTS はその15本に対応する subset 上に 18,450 annotated images、48,106 tools、55,655 hands、39,578 hand-tool segmentations を追加する。annotation は own left/right、other left/right と、main-hand interaction の left hand、right hand、left-hand object、right-hand object、two-hand object を含む。citeturn950224search0

ただし公開論文で検証されているのは segmentation transfer／benchmark であって、phase recognition や detection の downstream gain ではない。citeturn950224search0

手術一般では、open-surgery の既存研究に hand/tool multitask、hand–tool interaction detection、hand motion を使った tool classification が存在する。Fujii et al. の open-surgery tool detection survey 部分も、Goodman らの multi-task action segmentation/tool/hand/keypoint network、Goldbraikh らの tool localization＋tool-hand interaction network、Shimizu らの hand-motion-aware tool classification を挙げている。citeturn950224search4

しかし、今回の構成のように **「工程モデルと tool detector は各自の supervision だけで独立学習・freeze」「第三の grasp model も独立学習・freeze」「小型 interface だけを学習」**という controlled modular comparison は確認できなかった。したがって、この分離設計自体に新規性がある可能性は高い。

既知文献を含む系統を現役度で整理すると、EndoNet／MTRCNet-CL は「tool signal と phase recognition」の古典的系統として現在も概念的基準点だが、egocentric HOI の表現としては旧世代である。STIN／Something-Else と *Simultaneous Detection and Interaction Reasoning for Object-Centric Action Recognition* は object-centric relational reasoning の基礎として依然有効である。SViT／ORViT は object/entity token を video transformer に入れる設計として現役度が高い。*How Can Objects Help Action Recognition?* は object cue の利用位置・融合方式を考える上で引き続き重要である。一方、2023年以降は Helping Hands、IRN、HOCL/OSL、HandFormer、EgoPED、EgoVLM 系が「手・active object・interaction を明示的に supervision／token／graph にする」方向の中心になっている。citeturn115999search10turn623842academia8turn390225search5turn836387academia49turn182326search0

EgoSurgery に対する最も堅い研究設計は、文献全体から見ると二本立てになる。第一に **(a)** として、grasp model を完全 freeze し、その出力を `left-held-tool / right-held-tool / bimanual` の低次元 token または relation graph に変換する小さな interface のみを detection／phase backbone に接続する。mask feature をそのまま渡すより、association を圧縮した feature の方が IRN/EgoPED の成功例に近い。citeturn623842academia8turn182326search0

第二に **(b)** として、grasp model の soft output を training-only teacher とし、RGB/tool detector/phase model の中間 token または logit に distill する。Helping Hands、HOCL、Multimodal Distillation の3系統がこの設計を強く支持する。citeturn836387academia52turn438260view1turn836387academia51

比較実験では、少なくとも `RGB/tool baseline`、`grasp(a)`、`grasp(b)`、`GT grasp oracle`、`box-overlap heuristic oracle`、`random/permuted grasp control` を揃える価値が高い。特に今回の annotation construction では grasp association が bbox overlap に強く依存するため、**「学習済み grasp model が効いた」のか、「単に detector box の重なりを再符号化しただけなのか」**を切り分ける必要がある。EgoSurgery-HTS の annotation procedure 自体がこの交絡を生むため、ここは既存研究より重要な対照実験になる。citeturn950224search0

評価面では、macro Jaccard を primary に置くなら、Shiota et al. が示した tail-class benefit を踏まえ、phase ごとの Jaccard と rare-phase gain を必ず併記するのがよい。tool detection では全体 mAP だけでなく、similar-shape pair、small/occluded tools、held vs non-held tools に分解すべきである。EgoSurgery-Tool 自身が imbalance、similarity、occlusion を主要課題としているため、この分解は dataset の難しさと直接対応する。citeturn215386academia12

最終的に、この調査から最も支持される仮説は、**把持情報は「高精細なマスク」としてそのまま渡すより、「左右手が何を保持しているか／両手協調か」という低次元で因果的に近い relation representation として渡す方が、工程認識には適する**というものになる。一方 tool detection には、hand proximity・contact・held-tool relation を box-level re-scoring prior として使う方が自然である。推論時コストと robustness を重視するなら training-only distillation が強い比較対象であり、文献上も最も確立したルートである。citeturn623842academia8turn438260view1turn836387academia51
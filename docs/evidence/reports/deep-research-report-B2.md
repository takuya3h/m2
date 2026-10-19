# B2調査：工程・行動・タスク信号による物体検出器の条件付けと、凍結検出器への小規模界面

## 系統表

本稿での「件数」は、**検索で題名だけ拾った件数ではなく、実在を一次資料で確認し、本調査の系統または詳細記録に採用した文献数**である。方向間・系統間の重複は許している。また「現役度」は御指定の定義を厳密に適用したため、近年も概念的に重要でも、2024–2026年の査読論文の比較表まで確認できなかったものは「不明」とした。

| 系統 | 代表的な文献 | 現役度 | 下の詳細記録に含む件数 |
|---|---|---|---:|
| 工程・行動と道具認識の多タスク化 | **EndoNet**, **MTRCNet-CL**, *Phase-Informed Tool Segmentation for Manual Small-Incision Cataract Surgery* | **新興**：工程条件付けそのものについては ToolSeg が MICCAI 2025 で査読済み。ただし box detection ではなく segmentation | 1 |
| 条件付き affine modulation / FiLM | **FiLM**, ToolSeg の PAFT | **新興**：手術での工程条件付き実装として ToolSeg 2025。FiLM 自体の「現役度」は今回の厳格な比較表条件では不明 | 1 |
| クラス logit の prior・再スコア | COCO-Tasks、contextual rescoring、Barnea & Ben-Shahar | **不明**：原理は継続して使われるが、同一ベンチマークでの2024–2026比較表による現役度確認はできず | 2 |
| DETR query の条件付け | **Conditional DETR**, **CoTDet**, **Grounding DINO** | **SOTA級（open-set / grounded detection の限定）**：Grounding DINO は ECCV 2024 の査読版で COCO zero-shot、ODinW、RefCOCO 系を扱う。通常の closed-set detector の SOTA という意味ではない。 citeturn19search7turn19search3 | 3 |
| cross-attention による外部信号融合 | **MDETR**, **GLIP**, **Grounding DINO**, **LAVT** | **定番の基準〜SOTA級（language-grounded detection/segmentation に限定）**。Grounding DINO が2024年の査読済み到達点の一つ。 citeturn19search7 | 2 |
| task / affordance conditioned detection | **What Object Should I Use?**, **TOIST**, **CoTDet** | **不明**：COCO-Tasks 上では後続 TOIST、CoTDet が前段を上回る系譜を確認したが、2024–2026の査読比較表を今回確認できなかった。 citeturn15view2turn15view1turn15view3 | 3 |
| グラフ・scene/object relation | **Structure Inference Net**, COCO-Tasks の GGNN | **不明**。Structure Inference Net は CVPR 2018、COCO-Tasks は CVPR 2019。 citeturn21search28turn15view2 | 1 |
| 動画 feature / proposal aggregation | **SELSA**, StreamYOLO, LongShortNet, DAMO-StreamNet | **不明**：Argoverse-HD の streaming 系では LongShortNet、DAMO-StreamNet が後続だが、直近2年の査読比較表による判定はできず。 citeturn20view0turn17search6 | 3 |
| 長期 memory / context bank | **Context R-CNN**, SELSA | **不明**：現在も「動画文脈」の基礎系統として参照されるが、本調査の現役度定義を満たす2024–2026比較表は未確認 | 0 |
| action prompt による active-object 選択 | **ActionVOS** | **不明**：ECCV 2024 査読済みで強い結果を持つが、今回確認した範囲では独立追試・複数後続比較が少ない。 citeturn15view0 | 1 |
| frozen detector / frozen foundation model への prompt | **CLIPSeg**、LAB-Det | **新興**：LAB-Det は2026プレプリントで frozen detector を言語記述だけで条件付けする。査読済みではない。 citeturn18academia35 | 1 |
| context bias / context failure | Barnea & Ben-Shahar、Singh et al.、Kim et al. reproduction | **定番の基準**というより**否定的証拠の系統**。文脈が localization error を直せないこと、典型共起への依存が OOD で崩れること、独立追試で一部符号が変わることを含む。 citeturn21search0turn21search1turn21search5 | 3 |
| 小標本・動画単位分割・漏れ | Varoquaux 2018、EgoSurgery-Tool の video-level split | **定番の方法論上の注意点**。小標本 CV の大きな不確実性と、動画由来データを動画単位で分ける設計が本研究設定に直接関係する。 citeturn21search6turn4view3 | 1 |

この系統表から直接読み取れる重要な事実は、**「外部信号で検出を条件付ける」研究そのものは多数ある一方、御研究の制約をすべて同時に満たすもの、すなわち「独立学習済み・完全凍結した phase model と DETR detector の間だけに小モジュールを置き、同時刻の predicted phase のみを渡し、online、少数の egocentric open-surgery video で box mAP を測る」ものは、今回の検索では確認できなかった**ということである。後述する「未検証の組み合わせ」はこの意味での検索上の空白であり、世界初を主張するものではない。

## 文献ごとの記録

以下では、御指定の「既に持っている文献」10件、すなわち **EndoNet、MTRCNet-CL、FiLM、LAVT、CLIPSeg、MDETR、Which Tasks Should Be Learned Together、Context R-CNN、SELSA、Structure Inference Net** は個別記録を省いた。

**EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos**

- [書誌] 著者／年／題名／掲載先／ID: Ryo Fujii, Hideo Saito, Hiroki Kajita／2024／*EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos*／arXiv プレプリント／**arXiv:2406.03095**。 citeturn3search1turn3search5
- [書誌] 読んだ範囲: **本文**。arXiv HTML のデータ統計、split、Tables 3–5、error analysis を確認した。 citeturn4view0turn4view3
- [近さ] 方向: **方向1**。視点: 一人称。ドメイン: 開放手術。
- [近さ] 課題の形: egocentric open-surgery frame から 15 種類の surgical tool と hand を bbox detection。phase 条件付け自体は実施していない。
- [近さ] 推論の規約: 静止フレーム detector として評価されており、時間的未来情報の利用はない。
- [近さ] データ規模: EgoSurgery-Phase の15動画 subset、15,437画像、49,652 tool boxes、15 tool classes。hand は46,320 boxes・4 categories。parent dataset は21動画・約15時間と本文に記載。公式 split は10 train／2 validation／3 test の**動画単位**。 citeturn4view0turn4view1turn4view3
- [近さ] モデルの状態: detector 単独学習。工程モデルとの interface はない。
- [手法の位置] 系統: EgoSurgery baseline／closed-set detection。
- [手法の位置] 現役度: **定番の基準（EgoSurgery-Tool 内）**。理由は当該 dataset paper が複数 detector の bridge baseline を提供しているため。ただし2024–2026の独立後続比較表による「SOTA級」は確認できず。
- [手法の位置] ベンチマーク: EgoSurgery-Tool official 10/2/3 split。
- [手法の位置] 少数動画・online・一人称: 少数動画 **該当**、一人称 **該当**、online phase recognition は非該当。
- [証拠] 何と何を比べた差か: 同一 official split・COCO pretraining の複数 detector を比較。
- [証拠] 効果量: **Table 4** で AP は Faster R-CNN 37.7、RetinaNet 36.2、Cascade R-CNN 38.8、CenterNet 42.4、Sparse R-CNN 37.0、VarifocalNet 45.8、Deformable DETR 30.0、DDQ 43.2、DINO 39.7。これはモデル間比較であり、工程信号の効果ではない。 citeturn4view3
- [証拠] 符号: detector 間で差あり。
- [証拠] 符号や大きさが変わる条件: **Table 5** の hand detection では COCO initialization 55.3 AP に対し ImageNet 50.7、COCO+EgoHands 52.1。したがって「外部の関連データを追加すれば常に改善」という結果ではなく、EgoHands を加えた pretraining はこの設定では COCO 単独より **−3.2 AP**。著者は domain gap を論じている。 citeturn4view3
- [証拠] クラス別: error analysis では scissors と needle holder の混同、forceps・gauze・retractor の background との混同が報告される。phase-tool co-occurrence も強く、Figure 4 では工程と道具の偏った共起が可視化されている。 citeturn4view3
- [証拠] seed／fold／検定: official single split。複数 seed や統計検定は本文で確認できず。
- [証拠] 著者以外の追試: 本調査で確証を得た独立追試は不明。
- [実装] コードと重み: dataset repository は公開。dataset repository は **CC BY-NC-SA 4.0** と記載。arXiv HTML 自体の表示ライセンスとは区別が必要。 citeturn3search4
- [実装] 追加データ: detection 自体には phase annotation 不要。ただし同じ動画に phase labels が存在する。
- [実装] pretraining overlap: COCO 等を使用。EgoSurgery test frames が COCO に含まれるという記載は確認できず。
- [要点] **B2 の最も直接的な土台であり、phase–tool 共起は存在するが、phase を detector に入れる実験自体は dataset paper では測られていない。**
- [不審点] Table 3 では Forceps total 6063 に対する “Dist. 1.22%” という表記があり、総数との整合から桁の疑いがある。また hand total の表記にも “4,6320” が見える。推測で訂正せず、原表の不整合として留保する。 citeturn4view0

**EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos**

- [書誌] 著者／年／題名／掲載先／ID: Ryo Fujii, Masashi Hatano, Hideo Saito, Hiroki Kajita／2024／*EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos*／MICCAI 2024 査読つき／**arXiv:2405.19644**。 citeturn3search0turn3search7
- [書誌] 読んだ範囲: 本文 HTML と version metadata。
- [近さ] 方向: **方向1**。視点: 一人称。ドメイン: 開放手術。
- [近さ] 課題の形: egocentric open surgery video から surgical phase を予測。
- [近さ] 推論規約: 本B2で必要な「過去のみ」と同一であることは、今回確認した取得範囲からは**不明**。
- [近さ] データ規模: 初期版および EgoSurgery-Tool の記載は **21 videos、約15時間、10 surgery types、8 surgeons、9 phases**。一方、後の arXiv v3 の abstract metadata には **20 videos** と記載される版があり、version 間で動画本数が一致しない。 citeturn3search17turn3search19turn4view1
- [近さ] モデルの状態: phase recognition model 単独。
- [手法の位置] 系統: surgical phase recognition／egocentric video representation。
- [手法の位置] 現役度: **不明**。EgoSurgery-Phase の基準値としては重要だが、B2 の detection conditioning benchmark ではない。
- [証拠] 効果量: B2の検出条件付けに関する値はなし。
- [証拠] seed／fold／検定: B2で採用する15動画 CVとは別設定。
- [実装] 追加注釈: phase labels。
- [要点] **B2 の外部信号 P の出自となる dataset だが、version 間の動画数 21/20 の差は、実験対象を明示する際に固定すべき書誌上・dataset-version 上の注意点である。**

**EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos**

- [書誌] 著者／年／題名／掲載先／ID: Nathan Darjana, Ryo Fujii, Hideo Saito, Hiroki Kajita／2025／*EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos*／プレプリント、後に Healthcare Technology Letters 系掲載情報あり／**arXiv:2503.18755**。 citeturn3search6turn3search12
- [書誌] 読んだ範囲: 要旨中心。
- [近さ] 方向: **方向1**。視点: 一人称。ドメイン: 開放手術。
- [近さ] 課題: hand、tool、interaction の pixel-wise segmentation。
- [近さ] データ規模: 14 tool categories と報告。詳細な本数・時間は今回の本文確認範囲では不明。 citeturn3search6
- [近さ] モデル状態・推論規約: 不明。
- [手法の位置] 系統: 手・術具相互作用表現。
- [手法の位置] 現役度: **新興**（2025、EgoSurgery の追加注釈系統）。
- [証拠] B2型の phase→box detection 比較: なし。
- [実装] 追加注釈: pixel masks、hand-tool interaction。
- [要点] **同一ドメイン内には bbox だけでなく hand-tool interaction を表す情報も存在するが、phase prediction を frozen box detector に入れる証拠にはなっていない。**

**Phase-Informed Tool Segmentation for Manual Small-Incision Cataract Surgery**

- [書誌] 著者／年／題名／掲載先／ID: Bhuvan Sachdeva et al.／2025／*Phase-Informed Tool Segmentation for Manual Small-Incision Cataract Surgery*／MICCAI 2025 査読つき／**DOI: 10.1007/978-3-032-05114-1_43、arXiv:2411.16794**。 citeturn10search0turn10academia9
- [書誌] 読んだ範囲: **本文**、method、Tables 1, 3, 4, 5。
- [近さ] 方向: **方向2、方向7**。視点: 顕微鏡。ドメイン: 開放眼科手術。
- [近さ] 課題: surgical frame と phase information から tool segmentation。
- [近さ] 推論規約: phase predictor に MS-TCN++ を用いるが、causal masking／未来フレーム禁止を明示する記述を今回確認できず、**online かは不明**。
- [近さ] データ規模: 53 videos、18 phases、3,527 annotated frames、13 tool classes。 citeturn8view0
- [近さ] モデル状態: phase predictor は別データで学習されるが、segmentation model は phase-conditioned module を含め学習する。**凍結 detector + interface-only training ではない**。
- [手法の位置] 系統: FiLM型の phase-aware feature modulation。PAFT は phase embedding から channel-wise affine scale/shift を生成する。
- [手法の位置] 現役度: **新興**。MICCAI 2025 査読済みで、今回の検索では著者以外による十分な追試は確認できず。
- [手法の位置] 少数動画: 数十本規模に近いが53本。online は不明。一人称ではない。
- [証拠] 何と何を比べた差か: **Table 1** で同じ architecture family 内の phase 無し、predicted phase、GT phase、pseudo-label 有無を分離して比較。
- [証拠] 効果量: phase 無し v0 は IoU **40.90±3.4**、DSC **50.66±3.9**。predicted phase の gated v3 は **48.77±5.5 / 57.52±5.4**。GT phase の gated v6 は **56.13±4.5 / 64.76±4.5**。したがって v0→v3 は IoU **+7.87**、DSC **+6.86**、v3→v6 の predicted→GT 置換は IoU **+7.36**、DSC **+7.24**。データ・fold・segmentation model family は同じで、phase signal の品質を変えた比較である。 citeturn8view0
- [証拠] 正解信号と予測信号: **本調査で最も明確な oracle-vs-prediction 比較**。Basic conditioning でも predicted v2 46.58/55.40 に対し GT v5 54.26/62.98 で、oracle gap が残る。 citeturn8view0
- [証拠] クラス別・負の結果: **Table 4**。predicted phase を加える v0→v3 で Cautery は DSC **63.81→60.28**、Sideport **68.69→63.73**、Visco **46.42→40.08** と悪化する一方、Keratome **46.24→67.92**、Rhexis Needle（86 samples）**13.98→30.27** と大きく上がる。GT phase v6 は Cautery 73.38、Sideport 76.79、Visco 56.28、Rhexis Needle 38.70。したがって「phase が有用か」と「**予測 phase が有用か**」はクラスごとに同符号ではない。 citeturn9view0
- [証拠] 稀少クラス: Rhexis Needle 86 samples で大きな改善が報告されるが、Dialer 343 samples は 40.33→41.54、GTでも41.23で小さい。したがって「稀少だから必ず phase gain が大きい」とはこの表だけからはいえない。 citeturn9view0
- [証拠] dataset shift: CaDIS の **Table 5** では GT-phase ToolSeg v6 が mIoU 60.73、DSC 68.63 に対し、pseudo-label を加えた v7 は59.05/67.72で**悪化**しており、追加 supervisory signal の効果も条件依存。 citeturn9view1
- [証拠] seed／fold／検定: **5-fold video-level CV**。seed 数と統計的検定は確認できず。phase model は leakage 防止のため segmentation evaluation set とは独立の内部90動画で学習され、phase accuracy 50.10%、precision 47.60%、F1 50.23% と記載。 citeturn8view0turn9view0
- [実装] コード: 著者 repository が公開されている。ライセンスは今回の取得範囲では不明。 citeturn10search0
- [実装] 追加データ: phase model 用の独立90 surgical videos、SAM2 による pseudo labels を利用する設定がある。 citeturn8view0
- [要点] **「工程予測を視覚モデルへ条件付けすると平均では改善するが、予測工程では一部 tool class が明確に悪化し、GT phase との oracle gap も大きい」という、B2に最も近い肯定・否定両方の証拠。**
- [不審点] Table 1 の v4 IoU は **54.32±4.4** だが、Table 3 では **54.32±34.4** と見える。また本文には U-Net DSC 52.03 との記述がある一方、対応表では50.66。原文上の不一致として扱い、推測訂正しない。 citeturn8view0turn9view0

**What Object Should I Use? – Task Driven Object Detection**

- [書誌] 著者／年／題名／掲載先／ID: Johann Sawatzky, Yaser Souri, Christian Grund, Juergen Gall／2019／*What Object Should I Use? – Task Driven Object Detection*／CVPR 2019 査読つき／**arXiv:1904.03000**。 citeturn15view2
- [書誌] 読んだ範囲: **本文**。
- [近さ] 方向: **方向5**。視点: 三人称静止画。ドメイン: 非医療。
- [近さ] 課題: image と task (“sit comfortably on” 等) から、その task を遂行するのに適した物体 box を選ぶ。
- [近さ] 推論規約: 静止画。online/offline の区別は非該当。
- [近さ] データ規模: **約40,000 images、14 tasks** の COCO-Tasks。 citeturn15view2
- [近さ] モデル状態: object candidates の appearance と scene 全体の関係を GGNN で扱う。detector 自体を frozen にして interface だけ学習するかという観点では完全一致ではない。
- [手法の位置] 系統: task prior＋graph context＋re-ranking。
- [手法の位置] 現役度: **置き換えられた結果は確認**。同じ COCO-Tasks では後続 TOIST、CoTDet がより高い結果を報告するが、「比較対象として使われなくなった」まで確認できないため、定義上は **不明** とする。 citeturn15view1turn15view3
- [証拠] 何と何を比べた差か: **Table “Comparison to Baselines mAP@0.5”** で same task-oriented problem に対し classification / ranker / proposed+fusion を比較し、さらに GT boxes と Faster-RCNN detections の入力条件を比較。
- [証拠] 効果量: GT boxes 条件で classification **0.616**、proposed+fusion **0.742**。Faster-RCNN detections 条件では classification **0.288**、proposed+fusion **0.326**。つまり contextual/task reasoning の差は GT boxes 上で +0.126、実 detector boxes 上で +0.038。これは「presence/semantic suitability が改善しても、box localization error があると最終 detection AP gain が縮む」ことを直接示唆する構造の比較である。 citeturn21view1
- [証拠] 符号: 改善。
- [証拠] 他変更との混在: proposed GGNN/fusion と baseline architecture が異なるので、工程 prior だけを変えた clean ablation ではない。
- [証拠] seed／fold／検定: 今回確認した表からは不明。
- [実装] 追加注釈: 14 task に対する affordance/suitability annotation。
- [要点] **task-level context は候補選択を改善できるが、実 box detector を通すと GT-box 条件より gain が大幅に小さくなる。B2の「presence と box mAP は同じものではない」という論点に直接関係する。**

**TOIST: Task Oriented Instance Segmentation Transformer with Noun-Pronoun Distillation**

- [書誌] 著者／年／題名／掲載先／ID: Pengfei Li, Beiwen Tian, Yongliang Shi, Xiaoxue Chen, Hao Zhao, Guyue Zhou, Ya-Qin Zhang／2022／*TOIST: Task Oriented Instance Segmentation Transformer with Noun-Pronoun Distillation*／NeurIPS 2022 査読つき／**arXiv:2210.10775**。 citeturn15view1
- [書誌] 読んだ範囲: 本文 HTML を取得したが、本回答で数値引用可能な表位置まで再確認できなかったため、**数値は記載しない**。
- [近さ] 方向: **方向5**。視点: 三人称。ドメイン: 非医療。
- [近さ] 課題: task verb を条件として、その task を afford する object の box と instance mask を予測。
- [近さ] 推論規約: 静止画。
- [近さ] モデル状態: transformer detector/segmenter 自体を task-oriented objective で学習。frozen detector + interface-only ではない。
- [手法の位置] 系統: task-conditioned query／attention、noun-pronoun distillation。
- [手法の位置] 現役度: COCO-Tasks 上の後続系統だが、直近2年の比較表による分類は **不明**。
- [証拠] GT noun は training 時の privileged information として使い、inference では noun-agnostic pronoun representation を利用する設計。これは「GT補助信号で train し、prediction-time には別形式」という構造であり、御質問(4)の「同じ形の GT と predicted signal を入れ替える」実験とは異なる。 citeturn15view1
- [実装] code と model が公開と論文に記載。ライセンスは今回未確認。 citeturn15view1
- [要点] **task signal を DETR 系 query interaction に深く融合する系統だが、凍結 detector への小 interface ではない。**

**CoTDet: Affordance Knowledge Prompting for Task Driven Object Detection**

- [書誌] 著者／年／題名／掲載先／ID: Jiajin Tang, Ge Zheng, Jingyi Yu, Sibei Yang／2023／*CoTDet: Affordance Knowledge Prompting for Task Driven Object Detection*／ICCV 2023 査読つき／**ID不明**（今回の一次資料取得範囲では DOI/arXiv ID を確定できず）。 citeturn15view3
- [書誌] 読んだ範囲: 著者公式 project page の method・main results。
- [近さ] 方向: **方向5**。視点: 三人称静止画。ドメイン: 非医療。
- [近さ] 課題: image＋task text＋LLM-derived affordance knowledge から suitable objects の box/mask。
- [近さ] モデル状態: knowledge-conditioned decoder を学習。frozen detector interface-only ではない。
- [手法の位置] 系統: language/affordance prompt→object query conditioning。
- [手法の位置] 現役度: **不明**。2023 ICCV 以降の2024–2026 peer-reviewed comparison table を今回確認できず。
- [証拠] 何と何を比べた差か: 著者ページでは TOIST および GGNN と同じ task-driven benchmarks で比較。
- [証拠] 効果量: 著者 project page は TOIST 比 **+15.6 box AP、+14.8 mask AP**、GGNN 比 **+24.3 box AP、+21.2 mask AP** と報告するが、この回答では原論文表番号を確認できなかったため、御指定の規則に従い**本文の効果量欄の正式数値としては採用しない**。 citeturn15view3
- [証拠] クラス/task 別: 著者ページでは多様な object category を必要とする task4、task6、task7 で改善が大きいと説明する。これは rare/uncommon affordance targets に context knowledge が効く可能性の証拠だが、EgoSurgery の class-long-tail と同一条件ではない。 citeturn15view3
- [実装] code link を著者 project page が提供。ライセンス不明。 citeturn15view3
- [要点] **工程・task 信号を query generation と box regression の両方へ入れる、B2より強結合な対照系。**

**Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection**

- [書誌] 著者／年／題名／掲載先／ID: Shilong Liu et al.／2024 査読版／*Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection*／ECCV 2024 査読つき／**arXiv:2303.05499**。 citeturn19search7turn19search3
- [書誌] 読んだ範囲: 要旨・公式実装説明中心。
- [近さ] 方向: **方向5**。視点: 該当なし。ドメイン: 非医療。
- [近さ] 課題: image＋text prompt から open-set boxes。
- [近さ] 推論規約: 静止画。
- [近さ] モデル状態: vision-language detector を grounded pretraining で学習するため、B2の frozen detector + small interface とは異なる。
- [手法の位置] 系統: feature enhancer、language-guided query selection、cross-modality decoder。
- [手法の位置] 現役度: **SOTA級（Grounding DINO 論文中の zero-shot/open-set benchmarks について）**。closed-set surgical detector への一般化は別問題。 citeturn19search7
- [証拠] external signal は text であり、「工程 softmax vector」ではない。したがって query conditioning/cross-attention の**機構上の近縁例**。
- [証拠] seed／fold／統計: B2への直接情報なし。
- [実装] official code と weights が公開され、Grounded SAM 系との組合せも公式 repository に記載。 citeturn19search3
- [要点] **外部 semantic signal を DETR query と decoder 内部に入れる現代的な強結合例だが、独立 frozen D に後付けする設計ではない。**

**GLIP: Grounded Language-Image Pre-training**

- [書誌] 著者／年／題名／掲載先／ID: Liunian Harold Li et al.／2022／*Grounded Language-Image Pre-training*／CVPR 2022 査読つき／**arXiv:2112.03857**。 citeturn1search7
- [書誌] 読んだ範囲: 要旨のみ。
- [近さ] 方向: **方向5**。ドメイン: 非医療。
- [近さ] 課題: detection を phrase grounding として再定式化し image-language grounding を学習。
- [近さ] モデル状態: end-to-end grounded pretraining。frozen detector interface ではない。
- [手法の位置] 系統: language-conditioned detection／cross-modal grounding。
- [手法の位置] 現役度: **定番の基準**に近いが、御指定の「直近2年の複数査読表」を今回十分確認できなかったため正式には **不明**。
- [証拠] B2に対応する clean ablation: なし。
- [要点] **工程ラベルを言語化して detector を動かす発想の祖型の一つだが、training regime がB2と大きく異なる。**

**Conditional DETR for Fast Training Convergence**

- [書誌] 著者／年／題名／掲載先／ID: Depu Meng et al.／2021／*Conditional DETR for Fast Training Convergence*／ICCV 2021 査読つき／**arXiv:2108.06152**。
- [書誌] 読んだ範囲: 要旨・既知の method 定義を確認。今回の検索では個別一次ページを十分展開できなかったため、数値は不記載。
- [近さ] 方向: **方向5**。
- [近さ] 課題: object query に conditional spatial query を導入し DETR の cross-attention search space を絞る。
- [近さ] 外部 signal: phase/task の外部予測ではなく、decoder 内で作る条件なので、B2の「相手モデル出力だけ」という条件とは異なる。
- [手法の位置] 系統: query conditioning。
- [手法の位置] 現役度: **不明**。
- [要点] **“query を条件付ける”という機構の基準だが、external-context conditioning の証拠としては間接的。**

**ActionVOS: Actions as Prompts for Video Object Segmentation**

- [書誌] 著者／年／題名／掲載先／ID: 2024／*ActionVOS: Actions as Prompts for Video Object Segmentation*／ECCV 2024 査読つき／**arXiv:2407.07402、DOI:10.1007/978-3-031-72684-2_13**。 citeturn13search2turn13search4
- [書誌] 読んだ範囲: **本文**、data construction、metrics、Table 1。
- [近さ] 方向: **方向3**。視点: 一人称。ドメイン: 非医療。
- [近さ] 課題: egocentric video＋action narration＋object name から、**action に関与する active object** の mask と active/inactive classification を出す。
- [近さ] 推論規約: video segmentation だが、future frame 禁止の causal-online 規約は確認できず、B2の online 条件とは一致しない。
- [近さ] データ規模: preprocessing 後の training **13,205 videos／76,873 objects**、validation **467 videos／1,841 objects**。validation は positive 1,133、negative 708。VISOR、VOST、VSCOS を利用し、VISOR と VSCOS の clip overlap は leakage 防止のため filter している。 citeturn15view0
- [近さ] モデル状態: ReferFormer backbone、text encoder RoBERTa 等を再学習。frozen detector ではない。 citeturn15view0
- [手法の位置] 系統: action-as-prompt／cross-modal conditioning。
- [手法の位置] 現役度: **不明**。ECCV 2024 査読済みだが独立追試を今回十分確認できず。
- [証拠] 何と何を比べた差か: **Table 1** で同じ ActionVOS training setup について action prompt あり／なしを比較。
- [証拠] 効果量: RF-R101 では prompt 無し→有りで p-mIoU **56.3→65.4**、n-mIoU **19.9→19.0**（低い方が良い）、gIoU **66.8→70.9**、Acc **72.9→82.4**。RF-SwinL は p-mIoU **64.4→69.1**、Acc **72.8→80.7**。RF-VSwinB は **61.6→68.2**、Acc **72.5→81.2**。同じ backbone family で action prompt を入れることの符号は一貫して正。 citeturn15view0
- [証拠] 負の側面: task formulation 自体を RVOS と比べると、active-object p-mIoU は R101 で RVOS 67.7 に対し ActionVOS+prompt 65.4 のように若干低い一方、inactive object の誤 segmentation を大幅に減らし、combined metrics を改善する。したがって「presence/active selection の改善」と「positive object の pure localization score」は同じ方向に動くとは限らない。 citeturn15view0
- [証拠] seed／fold／検定: original split を使用。複数seed・統計検定は確認できず。
- [実装] code 公開。 citeturn13search0
- [実装] 追加注釈: action narration、object names、semantic masks、training 時 hand-object masks/pseudo-labels 等。
- [要点] **非手術の一人称映像では、action semantic signal が「どの同種物体が今の行動に関与するか」の識別に明確に効く。ただし bbox detector、frozen detector、causal-online の三条件は満たさない。**

**StreamYOLO: Real-time Object Detection for Streaming Perception**

- [書誌] 著者／年／題名／掲載先／ID: Jinrong Yang, Songtao Liu, Zeming Li, Xiaoping Li, Jian Sun／2022／arXiv title *StreamYOLO: Real-time Object Detection for Streaming Perception*、CVPR 2022 査読版 title *Real-time Object Detection for Streaming Perception*／**arXiv:2207.10433**。 citeturn17search0turn17search4
- [書誌] 読んだ範囲: 要旨と後続 LongShortNet の本文比較。
- [近さ] 方向: **方向4**。視点: 車載一人称に近い camera stream。ドメイン: 非医療。
- [近さ] 課題: current/previous frames から latency-aware future-time detection を行う streaming perception。
- [近さ] 推論規約: **streaming / causal**。LongShortNet 本文は StreamYOLO が current と previous frame の2枚のみを入力すると記述する。 citeturn20view0
- [近さ] モデル状態: detector 全体を streaming objective で学習。frozen interface-only ではない。
- [手法の位置] 系統: causal temporal feature fusion。
- [手法の位置] 現役度: 後続 LongShortNet、DAMO-StreamNet が同 benchmark で上回っているが、比較対象として残っているため「置き換え済み」の厳格条件は満たさず **不明**。 citeturn20view0turn17search6
- [証拠] LongShortNet Table 1 で StreamYOLO-L は Argoverse-HD sAP **36.1**。LongShortNet-L は37.1。これは外部 phase signal ではなく temporal feature の差。 citeturn20view0
- [実装] official code は Apache-2.0。 citeturn17search4
- [要点] **「未来フレームを見ずに過去だけを detector に入れる」こと自体は、一般映像の streaming detection で確立した設計空間である。**

**LongShortNet: Exploring Temporal and Semantic Features Fusion in Streaming Perception**

- [書誌] 著者／年／題名／掲載先／ID: Chenyang Li et al.／2023／*LongShortNet: Exploring Temporal and Semantic Features Fusion in Streaming Perception*／ICASSP 2023 査読つき／**arXiv:2210.15518**。 citeturn17search5turn17search29
- [書誌] 読んだ範囲: **本文**、Tables 1, 3–6。
- [近さ] 方向: **方向4、方向7**。視点: 車載 stream。ドメイン: 非医療。
- [近さ] 課題: current frame と複数 past support frames から object boxes/classes。
- [近さ] 推論規約: **過去のみ**。ShortPath に current \(I_t\)、LongPath に \(I_{t-i\delta t}\) を入れると明記。 citeturn20view0
- [近さ] データ: Argoverse-HD。metric は streaming AP。same train/val split as prior work。 citeturn20view0
- [近さ] モデル状態: YOLOX 系 detector 全体を fine-tune。frozen D ではない。
- [手法の位置] 系統: past-only temporal feature aggregation／memory。
- [手法の位置] 現役度: **不明**。
- [証拠] 何と何を比べた差か: **Table 5** は同 model で temporal range \(N,\delta t\) だけを変更。current-only \(N=0\) と past frames を加えた条件を直接比較。
- [証拠] 効果量: LongShortNet-S は current-only **26.8 sAP** から \(N=3,\delta t=1\) **29.8**、+3.0。L は **32.6→37.1**、+4.5。M は current-only 29.8、最良 \(N=4,\delta t=2\) 34.2、+4.4。 citeturn20view0
- [証拠] 負の条件依存: 過去を増やし続ければ単調に改善するわけではない。S は \(N=3,\delta=1\) 29.8 から \(N=5,\delta=2\) **28.1**、M は34.2から33.6、L は37.1から36.3へ低下する。 citeturn20view0
- [証拠] 入れる位置: **Table 6** で early/late fusion と equal/dilated weighting を比較。S/M/L で late+dilation は29.8/34.1/37.1、early+average は27.1/31.7/35.3。residual を外すと27.6/32.1/35.3へ低下。したがって temporal context の「有無」だけでなく、融合位置・現在 frame の保持比率で符号・大きさが変わる。 citeturn20view0
- [証拠] localization: Table 1 では LongShortNet-L が StreamYOLO-L に対し sAP75 **35.6→37.7**、small-object sAP **13.8→15.2**。一方 large-input model では large-object sAP が63.8→61.7に下がる。 citeturn20view0
- [証拠] seed／fold／検定: same fixed train/val split、複数seed・検定は確認できず。
- [実装] code 公開。 citeturn17search29
- [要点] **causal past context は box AP を改善し得るが、history length・fusion location・weighting に最適域があり、「文脈を多く入れるほどよい」ではない。**

**DAMO-StreamNet: Optimizing Streaming Perception in Autonomous Driving**

- [書誌] 著者／年／題名／掲載先／ID: Jun-Yan He et al.／2023／*DAMO-StreamNet: Optimizing Streaming Perception in Autonomous Driving*／IJCAI 2023 査読つき／**DOI:10.24963/ijcai.2023/90、arXiv:2303.17144**。 citeturn17search2turn17search6turn17search10
- [書誌] 読んだ範囲: arXiv HTML の方法概要・IJCAI公式ページ。
- [近さ] 方向: **方向4**。車載 video。
- [近さ] 課題: streaming object detection。short-path semantics と long-path temporal features、logit distillation、streaming forecast を組み合わせる。 citeturn17search6
- [近さ] 推論規約: streaming。future ground-truth frame を inference input にする方式ではなく、過去/現在から次時点を予測する。
- [近さ] モデル状態: end-to-end training。frozen detector ではない。
- [手法の位置] 系統: causal memory＋temporal fusion＋distillation。
- [手法の位置] 現役度: **不明**。
- [証拠] external semantic signal は使わないため B2の phase conditioning の直接証拠ではない。
- [実装] 著者 code repository 公開。 citeturn17search22
- [要点] **past-only video context を detection に入れる系統が query/logit context とは別に存在することを示す。**

**Exploring the Bounds of the Utility of Context for Object Detection**

- [書誌] 著者／年／題名／掲載先／ID: Ehud Barnea, Ohad Ben-Shahar／2019／*Exploring the Bounds of the Utility of Context for Object Detection*／CVPR 2019 査読つき／**arXiv:1711.05471**。 citeturn21search0turn21search4
- [書誌] 読んだ範囲: 本文 HTML・要旨。
- [近さ] 方向: **方向4、方向7**。非医療、静止画 detection。
- [近さ] 課題: object co-occurrence / spatial context を既存 detection result に使った場合の改善可能性の上限を調べる。
- [近さ] モデル状態: context-based post-processing / analysis。B2 の logit bias に機構的に近い。
- [手法の位置] 系統: contextual prior / re-scoring。
- [手法の位置] 現役度: **不明**。
- [証拠] 主要な否定的結果: object co-occurrence が大きな gain を与える場合もある一方、**改善が事実上不可能または実用的でない場合があり、検討した context は localization error を修復できない**ため detection gain に上限が生じる。 citeturn21search0
- [証拠] presence と box AP: この結果は、class/presence confidence を正せても box localization が誤っている FP/FN は残ることを明示する。したがって presence gain と box AP gain の1対1対応を仮定できない。
- [実装] 不明。
- [要点] **logit prior 型の context interface が改善できるのは主に classification/ranking error で、box geometry error には原理的な天井がある。**

**Don't Judge an Object by Its Context: Learning to Overcome Contextual Bias**

- [書誌] 著者／年／題名／掲載先／ID: Krishna Kumar Singh, Dhruv Mahajan, Kristen Grauman, Yong Jae Lee, Matt Feiszli, Deepti Ghadiyaram／2020／*Don't Judge an Object by Its Context: Learning to Overcome Contextual Bias*／CVPR 2020 査読つき／**arXiv:2001.03152**。 citeturn21search1turn21search9
- [書誌] 読んだ範囲: 本文 HTML・要旨。
- [近さ] 方向: **方向4、方向7**。非医療。
- [近さ] 課題: object/attribute classification で典型的な context と object representation を decorrelate し、out-of-context generalization を改善。
- [近さ] detection box そのものではなく recognition。
- [手法の位置] 系統: context-bias mitigation。
- [手法の位置] 現役度: **不明**。
- [証拠] 否定的知見: ordinary models が object-context co-occurrence に依存すると、典型的 context が消えたとき generalization が崩れることを問題設定そのものとして実証。4 datasets で評価。 citeturn21search1
- [証拠] B2との対応: phase→tool prior は強い共起を利用するので、test fold で phase-tool relation が変わると同型の failure mode を持ち得る。ただしこれは後段の解釈であり、本論文自体は surgical phase を扱わない。
- [要点] **context は平均精度を上げる信号であると同時に、共起分布を shortcut にする危険源でもある。**

**[Re] Don't Judge an Object by Its Context: Learning to Overcome Contextual Bias**

- [書誌] 著者／年／題名／掲載先／ID: Sunnie S. Y. Kim, Sharon Zhang, Nicole Meister, Olga Russakovsky／2021／*[Re] Don't Judge an Object by Its Context: Learning to Overcome Contextual Bias*／ML Reproducibility Challenge 系 reproduction／**arXiv:2104.13582**。 citeturn21search5
- [書誌] 読んだ範囲: 要旨。
- [近さ] 方向: **方向7**。
- [近さ] 課題: Singh et al. の全12表の独立再現を試み、追加 ablation。
- [手法の位置] 系統: independent reproduction／context bias。
- [手法の位置] 現役度: 非該当。
- [証拠] 著者以外による追試: **あり**。original code が公開されていなかったため scratch implementation。
- [証拠] 符号: COCO-Stuff、DeepFashion、UnRel では feature-split による out-of-context accuracy 改善を再現した一方、**AwA では performance drop**。CAM-based は original の mAP を0.5%以内で再現したと報告。 citeturn21search5
- [証拠] 意味: contextual mechanism の効果符号が dataset に依存し、同一主張がすべての domain で再現されるわけではない。
- [実装] reproduction code 公開。 citeturn21search17
- [要点] **方向7で求められた「著者外の追試で一部効果が消える／反転する」明示例。**

**LAB-Det: Language as a Domain-Invariant Bridge for Training-Free One-Shot Domain Generalization in Object Detection**

- [書誌] 著者／年／題名／掲載先／ID: Xu Zhang, Zhe Chen, Jing Zhang, Dacheng Tao／2026／*LAB-Det: Language as a Domain-Invariant Bridge for Training-Free One-Shot Domain Generalization in Object Detection*／プレプリント／**arXiv:2602.06474**。 citeturn18academia35
- [書誌] 読んだ範囲: 要旨のみ。
- [近さ] 方向: **方向5**。
- [近さ] 課題: one annotated exemplar/class を text description に変換し、その language signal で **frozen foundation detector** を条件付ける。
- [近さ] モデル状態: detector は frozen、weight update なし。B2の「凍結 D」に近いが、**学習可能な小 interface**ではなく training-free prompt generation。
- [手法の位置] 系統: frozen detector＋external language prompt。
- [手法の位置] 現役度: **新興**。2026プレプリントで査読状況不明。
- [証拠] 数値: 要旨しか読んでいないため、御指定に従い記載しない。
- [実装] one annotated exemplar/class が追加で必要。
- [要点] **“frozen detector を外部信号だけで変調する”という制約は実在するが、phase-vector→small trainable interface→closed-set logits とは異なる。**

**Cross-validation failure: Small sample sizes lead to large error bars**

- [書誌] 著者／年／題名／掲載先／ID: Gaël Varoquaux／2018／*Cross-validation failure: Small sample sizes lead to large error bars*／NeuroImage 査読つき／**DOI:10.1016/j.neuroimage.2017.06.061、arXiv:1706.07581**。 citeturn21search6turn21search10
- [書誌] 読んだ範囲: 要旨・bibliographic record。
- [近さ] 方向: **方向6**。
- [近さ] 課題: small-sample predictive modeling で CV estimate の sampling variability を検討。
- [手法の位置] 系統: evaluation uncertainty。
- [証拠] 主要結論: small sample では cross-validation estimate 自体に大きな error bars が生じ得る。 citeturn21search6
- [証拠] B2との位置: 15動画の video-level CV では、frame 数が多くても statistical unit を video とみなすなら独立単位は15であり、fold平均だけで effect の安定性を判断する設計には注意が必要。
- [要点] **B2では「フレーム数が多い＝独立標本数が多い」と扱わず、動画・fold レベルの変動を明示する根拠になる。**

### 問いごとの事実整理

御質問(1)の「外部信号で detector を条件付けする型」は、文献上少なくとも **class-logit prior/re-ranking、feature affine modulation、query conditioning、cross-attention、graph/context relation、temporal memory、language/task prompt** に分かれる。B2の現実装は前二者、つまり **logit prior** と **FiLM型 feature modulation** に位置する。query/cross-attention 系は Grounding DINO、CoTDet 等で実績があるが、いずれも detector 自体をその条件付け込みで学習する強結合例が中心である。 citeturn15view3turn19search7

御質問(2)の「action/phase/task を入れて検出が改善した例」は、box detection では COCO-Tasks 系、instance/video segmentation まで広げると ToolSeg と ActionVOS が明瞭である。逆に、**predicted phase** は ToolSeg の Cautery、Sideport、Visco で class-wise degradation を起こし、context一般でも distribution shift による悪化が独立追試を含め確認される。 citeturn9view0turn15view0turn21search5

御質問(3)の「凍結 detector＋小 module」は、**完全一致例が薄い**。LAB-Det は detector frozen だが trainable interface を持たない。HOI 系には frozen DETR の後段に interaction module を付ける構成が存在するが、そこで改善されるのは interaction recognition であり元 detector の box AP ではない。今回の実在確認範囲では、**凍結した closed-set detector の box/class prediction 自体を、別の凍結 model の prediction だけで小 interface により改善する**という clean setting の論文は確認できなかった。LAB-Det は最も近い「frozen D + external signal」の例である。 citeturn18academia35

御質問(4)の oracle GT と predicted signal を同形式で入れ替える比較について、最も明確なのは **ToolSeg Table 1**。predicted phase から GT phase に置換すると gated setting で IoU 48.77→56.13、DSC 57.52→64.76 となり、interface architecture を変えず signal quality だけを変えた oracle gap が測られている。box detector について同じ比較は今回確認できなかった。 citeturn8view0

御質問(5)の class-wise effect では、ToolSeg Table 4 が直接的である。rare Rhexis Needle は13.98→30.27 DSC と大きく改善する一方、predicted phase で悪化する classes もある。EgoSurgery-Tool 自体にも scissors/needle-holder の confusion や background confusion が報告されており、「rare」と「confusable」を別軸で見る根拠がある。 citeturn9view0turn4view3

御質問(6)については否定的証拠が複数ある。Barnea & Ben-Shahar は context が localization error を修正できないと分析し、Singh et al. は typical context への依存が atypical context で generalization を害すると示し、独立 reproduction は dataset によって gain が drop に反転する例を報告した。EgoSurgery-Tool でも外部 EgoHands pretraining は COCO-only より AP を下げた。 citeturn21search0turn21search1turn21search5turn4view3

御質問(7)の「過去だけを使う temporal detection」は **StreamYOLO、LongShortNet、DAMO-StreamNet** で確認できる。特に LongShortNet は式で current \(I_t\) と past \(I_{t-i\delta t}\) だけを明示し、Table 5 で current-only と past-context を clean に比較している。ただし history を長くすると単調に改善するわけではない。 citeturn20view0turn17search6

御質問(8)の presence と box mAP の関係について、**両者の改善量を同一モデル・同一splitで系統的に対応付けた surgical/egocentric study は今回確認できなかった**。しかし二つの直接的な境界条件がある。COCO-Tasks では task reasoning の gain が GT boxes 上より real detector boxes 上で小さくなり、Barnea & Ben-Shahar は context が localization error を直せないと示す。したがって、presence/class-confidence gain は box mAP gain の十分条件ではない。ActionVOS でも active/inactive classification が改善しつつ positive-object localization metric が必ずしも同程度には上がらない。 citeturn21view1turn21search0turn15view0

## 探したが見つからなかったもの

ここでの「見つからなかった」は、**2026年10月18日までの今回の検索で、実在と条件を一次資料で確認できなかった**という意味であり、世界に存在しないことを意味しない。

**EgoSurgery で phase prediction を box detector に入力する直接実験**  
検索語には `"EgoSurgery phase tool detection conditioning"`, `"EgoSurgery-Tool phase detector"`, `"egocentric open surgery phase informed tool detection"` 相当を用いた。EgoSurgery-Phase、EgoSurgery-Tool、EgoSurgery-HTS は確認できたが、**phase label/prediction を bbox detector の logits/features/query に入れて AP を測る論文**は確認できなかった。方向1では実在確認3件、直接該当0件。 citeturn3search0turn3search1turn3search6

**独立に学習して完全凍結した二モデル間だけを trainable interface でつなぐ box detection**  
検索語には `"frozen detector adapter external signal object detection"`, `"frozen object detector prompt adapter"`, `"parameter efficient object detection frozen detector"` を用いた。frozen VLM/backbone、frozen detector を downstream HOI に使う研究、training-free language conditioning は見つかったが、**D の box/class head まで frozen、P も frozen、P の同時刻 prediction だけが trainable interface を介して D の box mAP を改善する**という完全一致例は確認できなかった。LAB-Det は frozen detector だが training-free language bridge であり、B2とは異なる。 citeturn18academia35

**同じ interface に GT phase vector と predicted phase vector を差し替え、box mAP で oracle gap を測る実験**  
ToolSeg では同型の比較を segmentation で確認したが、bbox detection では確認できなかった。 citeturn8view0

**phase-conditioned DETR で query/logit/FiLM の注入位置だけを揃えて比較する ablation**  
Grounding DINO/CoTDet の query/cross-attention、ToolSeg の feature affine modulation、COCO-Tasks の graph/re-ranking は個別に存在するが、**同じ detector・同じ外部 signal・同じ split で「logit vs feature vs query vs cross-attention」を一要因だけ変更する比較**は確認できなかった。 citeturn15view3turn19search7turn8view0turn21view1

**predicted-context confidence/calibration と downstream box AP の関係**  
「phase model の accuracy が何%なら detector conditioning が正になる／負になる」という dose-response 型の解析は確認できなかった。ToolSeg は predicted と GT の二点比較を持つが、phase confidence を連続的に degrade/calibrate した sweep ではない。 citeturn8view0

**presence metric の差から box mAP の差を予測する定量式**  
検索範囲では、frame-level presence AP/F1 の改善量と COCO-style box AP の改善量の一意な変換や、同一 data での大規模 empirical mapping は見つからなかった。既存証拠はむしろ、localization error のため両者が乖離し得ることを示す。 citeturn21search0turn21view1

**EgoSurgery で causal past-only temporal context と phase context を同時に controlled comparison する研究**  
一般 video では past-only LongShortNet/StreamYOLO が存在し、手術では phase-informed ToolSeg が存在するが、同じ surgical detector で「current-only、past visual context、phase prediction、両方」を並べた実験は確認できなかった。 citeturn20view0turn8view0

**直近2年の主要会議誌で、context-conditioned detection の独立 negative replication を多数集められるか**  
明確な独立 reproduction として Kim et al. 2021 は確認できたが、2024–2026 の MICCAI/IPCAI/CVPR/ICCV/ECCV/NeurIPS/ICLR/MedIA/TMI から、B2に近い「外部 task/phase context を detector に入れたが改善しなかった」という査読済み negative result を複数確認することはできなかった。公開研究の publication bias を考えると、「見つからない」こと自体から効果を肯定してはいけない。独立追試そのものでは、dataset により符号が反転する例は存在する。 citeturn21search5

## 未検証の組み合わせ

以下は、上の文献を並べたときに今回の検索 corpus で**対応する測定を確認できなかった条件の交差**である。novelty の主張ではない。

**EgoSurgery × predicted online phase × bbox mAP。** EgoSurgery-Tool は box AP を持ち、EgoSurgery-Phase は phase recognition を持つが、その二つを prediction-time に接続した測定は確認できなかった。 citeturn4view3turn3search0

**frozen DETR × frozen P × interface-only learning。** Language-grounded detectors は detector 自身を conditional training し、ToolSeg は segmentation model を phase conditioning 込みで学習し、LAB-Det は frozen detector だが interface training をしない。三者の交差に相当する測定は確認できなかった。 citeturn19search7turn8view0turn18academia35

**同一 predicted phase に対する logit bias と FiLM の一要因比較。** FiLM系と logit/contextual rescoring 系は別々に存在するが、同じ detector checkpoint を frozen にして両者を比較する文献は確認できなかった。 citeturn8view0turn21search0

**同一 predicted phase に対する query conditioning。** Grounding DINO/CoTDet は text/affordance knowledge で query を条件付けるが、phase probability vector を DETR queries に注入した controlled comparison は確認できなかった。 citeturn15view3turn19search7

**predicted phase と oracle phase の差を bbox AP、presence、class-wise AP の三つで同時に測る実験。** ToolSeg は oracle gap と per-tool segmentation score を持つが、box AP と presence を同時には持たない。 citeturn8view0turn9view0

**rare class と confusable class を分離した context gain 分析。** ToolSeg は sample count と per-tool scoreを提供し、EgoSurgery-Tool は confusion を報告するが、「frequency」と「visual confusion」を別説明変数として context gain に回帰する解析は確認できなかった。 citeturn9view0turn4view3

**context distribution shift の意図的 stress test。** Singh et al. は一般 recognition で out-of-context を扱うが、surgical phase-tool pair に対して「train folds では強共起、test fold では共起が崩れる」サブセットを構成し detection AP を測る研究は確認できなかった。 citeturn21search1

**過去 visual memory と predicted phase を独立要因として交差させる実験。** LongShortNet は causal visual history、ToolSeg は phase context を測るが、両者の 2×2 factorial comparison は確認できなかった。 citeturn20view0turn8view0

**context が box regression そのものを変える場合と class score だけを変える場合の分離。** Barnea & Ben-Shahar の分析から class/context rescoring には localization ceiling があるが、phase context を box-regression branch にも入れた場合との同一条件比較は確認できなかった。 citeturn21search0

## 検索記録

**検索日: 2026年10月18日（Asia/Tokyo）。** 件数は、重複・二次記事を除き、今回一次資料で実在確認して本調査 corpus に採用したもの。複数方向に入る文献は重複計上している。検索には arXiv、CVF/OpenAccess、公式会議ページ、著者 project/repository を優先し、技術的結論には一次資料のみを採用した。

| 方向 | 主な検索語・探索軸 | 実在確認・採用件数 | 詳細記録件数 | 主な結果 |
|---|---|---:|---:|---|
| 方向1 同じデータ・設定 | `EgoSurgery`, `EgoSurgery-Tool`, `EgoSurgery-Phase`, `egocentric open surgery tool detection phase` | **3** | **3** | Phase、Tool、HTS を確認。phase→bbox detector conditioning は0件。 citeturn3search0turn3search1turn3search6 |
| 方向2 手術一般 | `phase informed tool segmentation surgery`, `surgical phase tool detection`, cataract/MSICS phase tool | **3以上**（既所有 EndoNet/MTRCNet-CL を含む） | **1** | ToolSeg が oracle/predicted phase 比較と per-tool negative result を持つ。 citeturn8view0turn9view0 |
| 方向3 非手術一人称 | `egocentric action prompt object segmentation`, EPIC-KITCHENS/VISOR/VOST/VSCOS、Ego4D state-change 系 | **4系統を確認** | **1** | ActionVOS を本文まで確認。action semantic signal で active-object selection が改善。 citeturn15view0 |
| 方向4 一般映像 | `streaming object detection past frames`, `temporal context video object detection`, `context object detection failure` | **8以上** | **6** | StreamYOLO、LongShortNet、DAMO、Barnea、Singh、独立 reproduction。 citeturn20view0turn21search0turn21search5 |
| 方向5 機構一般 | `task driven object detection`, `affordance detection`, `language conditioned DETR`, `frozen detector prompt adapter`, `query conditioning` | **12以上** | **7** | COCO-Tasks、TOIST、CoTDet、Grounding DINO、GLIP、Conditional DETR、LAB-Det 等。 citeturn15view2turn15view1turn15view3turn19search7turn18academia35 |
| 方向6 方法論 | `small sample cross validation error`, `video data leakage split object detection`, video-level split | **2以上** | **1** | Varoquaux と EgoSurgery 自身の video-level split を重点確認。 citeturn21search6turn4view3 |
| 方向7 否定的結果 | `context hurts object detection`, `context bias reproduction`, predicted phase per-class degradation、pretraining domain gap | **6** | **5** | ToolSeg class-wise degradation、EgoHands pretrain degradation、context localization ceiling、OOD context bias、independent reproduction failure。 citeturn9view0turn4view3turn21search0turn21search5 |

「手術・医療」を検索語に入れない探索も独立に実施した。具体的には `task driven object detection`, `affordance knowledge object detection`, `streaming object detection past frames`, `frozen detector adapter`, `context hurts object detection` 等で、COCO-Tasks、TOIST、CoTDet、ActionVOS、StreamYOLO、LongShortNet、context-bias 系へ到達した。したがって方向3〜5は surgical keyword の引用網だけから抽出したものではない。 citeturn15view2turn15view3turn20view0turn21search0

引用を逆向きにも追った。LongShortNet 本文は SELSA、memory aggregation、QueryProp、StreamYOLO など従来 video object detection を比較・引用しており、offline VOD の temporal aggregation と streaming/casual perception を明確に区別している。これは B2 で「動画だから temporal context を使う」と「未来を見ない」を分離して扱う必要があることの一次資料上の根拠になる。 citeturn20view0

順位表・dataset 起点では EgoSurgery-Tool の official baseline table、COCO-Tasks とその後続 TOIST/CoTDet、Argoverse-HD の StreamYOLO→LongShortNet→DAMO-StreamNet を追跡した。EgoSurgery については official split の既発表値と、御研究で予定する15動画固定fold CVは別の evaluation regime であるため、数値を直接同列比較しないことが必要である。 citeturn4view3turn20view0

## あなたの解釈と提案

ここからのみ、上の文献事実から導く解釈と実験提案を記す。

### B2でまず分離すべき因果的な問い

B2には実際には三つの異なる問いが重なっている。

一つ目は、**phase に tool presence の予測情報があるか**である。EgoSurgery-Tool の phase–tool co-occurrence と ToolSeg の oracle phase 結果から、この可能性は十分ある。ただしこれは「phase が detector を改善する」と同義ではない。 citeturn4view3turn8view0

二つ目は、**P が出す noisy predicted phase に、D が既に持っていない追加情報があるか**である。ToolSeg の predicted-vs-GT gap は、oracle context の価値と predicted context の価値を区別しないと結論が変わることを示している。特に predicted phase で悪化する tool class が実在するため、「GT phase で上がる」だけでは B2 の主張には足りない。 citeturn8view0turn9view0

三つ目は、**追加情報があったとして、それを detector のどの自由度に渡すと box mAP に反映されるか**である。logit bias は class ranking/presence を直接変えられるが geometry を直接直せない。FiLM は backbone/decoder feature を変えられるので localization にも影響し得る。Barnea & Ben-Shahar の localization ceiling は、この二方式が同じ性能上限を持つと仮定すべきでない理由になる。 citeturn21search0

### 現在の logit-bias と FiLM は異なる仮説を検定している

logit-bias 型は、

\[
z_{t,c}^{\,\prime}=z_{t,c}+b_c(p_t)
\]

のように理解できる。このとき phase signal は主として「この工程なら、この class は出やすい／出にくい」という **class prior** を変える。既存 box coordinates が悪い場合、それ自体を直す経路はない。

一方 FiLM 型は、

\[
h_t^{\,\prime}=\gamma(p_t)\odot h_t+\beta(p_t)
\]

なので、注入場所が bbox regression に upstream なら spatial representation も変化し得る。ToolSeg の PAFT と同じ機構族だが、ToolSeg は recipient network も学習しているため、**frozen D 上で FiLM だけに適応能力を持たせた場合に同じ gain が残るかは未検証**である。 citeturn8view0

したがって logit bias と FiLM の比較を単純な「interface A vs B」にせず、**classification-only intervention と feature-level intervention の違い**として読むと、box AP の結果を解釈しやすい。

### oracle と prediction を同じ interface に通す比較には強い意味がある

ToolSeg の最も参考になる点は、「GT phase を使えば上がった」ことより、**predicted phase と GT phase を同じ conditioning family に入れたときに大きな gap が残ったこと**である。 citeturn8view0

B2でも interface \(g\) を固定して、

\[
D(x_t),\qquad
D(x_t;g(\hat p_t)),\qquad
D(x_t;g(p_t^{GT}))
\]

を同じfoldで並べることで、少なくとも三つを分離できる。

baseline→predicted の差は、実運用可能な phase signal の効果である。predicted→GT の差は phase predictor の誤りに起因する残存余地を含む。baseline→GT の差は、その interface family で得られる oracle-side の上限に近い。ただし GT phase が detector の training interface にまで使われる場合は privileged information なので、最終モデルの性能とは区別して記録する必要がある。

さらに **soft predicted distribution**、argmax one-hot predicted phase、GT one-hot を同じ次元で入れると、「prediction error」と「uncertainty information の保持」を分離できる。ただしこれらは別 arm なので、同じ表で明示的に区別する必要がある。

### class-wise 分析では frequency と confusion を分ける

ToolSeg は rare Rhexis Needle で大きな改善を示す一方、他の class では gain が小さく、predicted context で悪化する class もある。EgoSurgery-Tool は scissors/needle-holder のような visual confusion を別途報告している。 citeturn9view0turn4view3

したがって B2 の class-level analysis では、少なくとも

**class frequency、baseline AP、phase concentration、visual confusion、context gain**

を同じものとして扱わない方がよい。

特に、phase concentration は training folds だけで

\[
H(C\mid P=p)
\]

あるいは class \(c\) に対する

\[
P(c\text{ present}\mid p)
\]

として計算できる。test fold のラベルから prior を作ると漏れになるため、各CV fold の train videos だけで定義する必要がある。その上で、rare class だから gain が出たのか、phase に strongly concentrated だから gain が出たのか、baseline が low-AP だから改善余地が大きかったのかを分離できる。

### 文脈への過依存を直接測る arm が必要になる

context-bias 文献の negative result は、平均 AP だけでは見えない。典型的共起が崩れた subset で悪化することが中心問題だからである。 citeturn21search1turn21search5

B2では追加 annotation を作らなくても、train-fold 内の phase–tool co-occurrence から、test frameを

- training でもよく見た phase–tool pair
- training では少ない phase–tool pair
- train-fold ではほぼ見ない pair

に層別できる。

その層ごとに baseline D と conditioned D の AP/recall/false-positive rate を比較すれば、phase prior が **regularizer/context cue** として働いた場合と、**shortcut** になった場合を区別できる。

特に logit-bias 方式では、ある phase で rare な tool に対する score を一律に下げる設計だと、まさに「typical context がないと object を見なくなる」failure mode が起こり得る。Singh et al. とその reproduction は、この stress test を入れる根拠になる。 citeturn21search1turn21search5

### presence と box mAP は別々に測る意味がある

文献からは「presence が良くなれば box AP も同程度よくなる」という対応は支持されない。Barnea & Ben-Shahar の分析では context は localization error を直せず、COCO-Tasks では GT boxes から real detector boxes に変えるだけで task-context gain が大きく縮む。 citeturn21search0turn21view1

B2では detector output から追加 model を学習せず、

\[
s_{t,c}^{presence}=\max_{q} s_{t,q,c}
\]

のような frame-level class presence score を導出できる。そのため同じ prediction について、

**frame-level presence AP/F1、box classification-related errors、localization-sensitive AP75、通常の box mAP**

を並べると、interface がどこを改善しているかを分離できる。

例えば presence が上がり mAP50 が上がるが mAP75 が動かない場合は、主効果が class confidence / false-positive suppression に寄っている可能性がある。一方 FiLM で mAP75 まで上がれば、feature modulation が localization quality に影響した可能性を検討できる。ただし、mAP50 と mAP75 の差だけから機構を断定せず、matched detections の class-score change と IoU change を併せて見る必要がある。

### causal temporal context は phase context の対照になり得る

LongShortNet は current-only と past visual context を clean に比較し、過去を入れることで box AP が上がる一方、history を伸ばしすぎると低下することも示した。 citeturn20view0

これは B2 にとって、「改善が phase semantic information によるのか、それとも単に時間的 smoothing/context を加えたからなのか」という別前提を示す。

P の phase prediction が過去フレームを集約して作られているなら、P output は単なる semantic label ではなく、**過去映像を圧縮した temporal context channel**でもある。したがって phase-conditioned gain を「工程意味論」の効果と呼ぶには、同じ情報量ではなくても、少なくとも過去視覚情報を簡単に集約した control と区別する価値がある。

ただし御研究の原則「界面へ渡す信号は相手モデルだけが出した同時刻の出力」に従うなら、主要 B2 実験では D に raw history を追加せず、これは補助的な機構分解として別表に置く方が定義を壊さない。

### 15動画CVでは effect の単位を動画・fold側にも置く

15動画を事前固定した video-level folds で評価する方針は、近接frameの train/test 混入を避ける意味で dataset 構造に整合する。EgoSurgery-Tool の official baseline 自体も video-level 10/2/3 split を採用している。 citeturn4view3

ただし15動画では、frame-level AP が高精度に計算できても、**generalization unit は frame ではなく video**である。Varoquaux の small-sample CV 論が示すように、fold estimate の変動は小標本では大きくなり得る。 citeturn21search6

そのため B2 の主表では平均だけでなく、各 fold の baseline と conditioned の**対応差**を残すのが重要になる。各foldで

\[
\Delta_f = \mathrm{mAP}_{f,\mathrm{conditioned}}
-\mathrm{mAP}_{f,\mathrm{baseline}}
\]

を示せば、「平均では+1 APだが5 fold中1 foldだけ+6で残りは0」という結果と、「全foldで+1前後」を区別できる。

同じことを macro Jaccard / phase accuracy 側にも適用すれば、相互改善の二方向が一部動画だけに依存していないかを同じ粒度で確認できる。

### B2の最小限の証拠構造

今回の文献から導くと、B2で最も情報量が高い比較は、単純な baseline vs proposed の二行ではなく、同一fold・同一 frozen D の中で少なくとも次の論理を分離する構造になる。

**D only** は detector の基準。  
**D + predicted phase interface** は実運用可能な効果。  
**D + GT phase, same interface** は oracle signal quality の対照。  
**D + shuffled phase / marginal phase prior** は「追加parameter」や単なる class-frequency correction の対照。  
logit-bias と FiLM は別々に同じ対照を持つ。

ここで shuffled phase は、test labels を使って最適化するのではなく、各foldの train distribution に基づく固定操作として定義する必要がある。また「phase を入れたら改善した」という結論ではなく、**predicted signal での差、oracle gap、class/foldごとの符号、presence と localization の分解**を同時に示すことで、ToolSeg で観測された「平均改善と class-wise degradation の共存」を見落とさずに済む。 citeturn8view0turn9view0

文献全体として最も一貫しているのは、**文脈には検出を改善する情報があるが、その価値は signal quality、受け取り側の自由度、融合位置、共起分布の安定性、そして localization error の割合によって大きく変わる**という点である。task/action context の肯定例、ToolSeg の predicted-phase class-wise degradation、LongShortNet の history-length 非単調性、context-bias の独立追試はすべて、この条件依存性と整合する。 citeturn15view0turn9view0turn20view0turn21search5
# 証拠地図 B — 工程・行動・タスクの信号で検出器を条件付ける（P→D）

**版:** v2.1（下書き。2026-10-19、起票者が作成。v2〔2026-10-18。新様式で作り直した版〕に、2026-10-19 の書誌の照合の結果を書誌の欄だけ反映）
**種類:** 探索の地図
**状態:** v2 の書誌 ID を 2026-10-19 に機械照合した（ID 34 件、不在 0、到達不能 0、書誌に差 5〔題名の欄が略称・説明の行〕）。本版はその結果を書誌の欄に反映したもので、反映の確かめは次の照合で行う。旧地図の行（B-01〜B-11）は 2026-09-16 にも照合済み。数値の原典確認は §0.3 のとおり
**元の報告:**
- deep research の報告「B2」1 件（deep-research-report-B2.md、72,035 バイト、sha256 c7aad1c222d9159c1209a557f765e0400f85a3b6ccd8d92025683a2ce8102116）。探索エンジンは本書に記録が無い
- 旧地図 B（docs/evidence/2026-09-16-B-p2d-interface.md、v1）の 11 行。v1 のファイルは置き換えずに repo に残し、冒頭に v1（旧様式）であることと本書（v2）が後継であることを明記する（利用者の決定 2026-10-18。書き込みは照合と配置の契約で行う）。旧地図の元は ChatGPT deep research 一エンジンの報告「B1」で、repo には無いが利用者が 2026-10-18 に添付した（B-chatgpt.md、38,349 バイト、sha256 ef94ea71aba1b5e81dea60ae0b55581dfdfda7cf290fe29d56dcb20b7bc33dd9）。B-01〜B-11 の arXiv ID 11 件と数値 88 件が B1 と一致する。B1 に無い数値 7 件（B-01 の 20・30 動画の値と差、B-03 の TS1・TS2）は、旧地図で利用者が原典から足した値と読める
- 新規性の探索の報告「N1」の照合の結果は地図 N（2026-10-18-N-novelty.md）に置いた。本書には B-02・B-14・B-15 に N1 の事実を併記した

**検索日:** B2 は 2026-10-18（Asia/Tokyo。報告の記載）。旧地図の行は検索日の記録が無い

---

## 0. この地図の読み方

### 0.1 問い

独立に学習して凍結した工程認識器 P の、同時刻の予測工程だけを、小さな学習可能な界面を通して、凍結した DETR 系の術具検出器 D へ渡すと、検出（box mAP）は変わるか。対象は一人称・開放手術・少数動画（15 動画の動画単位の交差検証）・過去のみ。B2 は、外部の信号で検出器を条件付ける型の全体と、凍結した検出器への小さな界面を調べる依頼である。報告の「御質問 (1)〜(8)」は依頼文 B2 の番号である。

### 0.2 規則

- 行は報告（または旧地図）に書かれた事実だけを載せる。数値・表番号は元のまま変えていない。B2 の報告に書かれた差は起票者が検算し、本地図の 10 件すべてが一致した
- 報告が「不明」「未確認」とした欄は不明のまま残した。旧地図の様式に無かった項目は「旧地図に記載なし」と書いた。推測で埋めていない
- 現役度は報告の値（SOTA 級／定番の基準／新興／置き換え済み／不明）と理由。旧地図の行には現役度の記録が無い
- 距離は一つの数字にしない（旧地図の距離 0〜3 は 2026-10-03 に定義ごと置き換えられたため移していない）。§3 の軸に分けた。探索の優先度には使わない
- 報告者の解釈と提案（報告の考察・設計案の節）は地図に載せず、起票者用の文書に移した（利用者の決定 2026-10-18）。各行の「報告者の一行」（§8）と、報告者の読みを含む要約の節も同じ文書へ移した
- 見つからなかったもの（§11）と未検証の組み合わせ（§12）は、その設計が新しい・価値があるという根拠として読まない。見つからない理由には、技術的な困難、価値が乏しいと見なされていること、偶然がありうる（利用者の指示 2026-10-18）
- 出所の列（§2）は B2 の報告の行番号（L）か、旧地図の行（旧 B.1）
- citation の印は除いた
- 題名・著者・掲載先・書誌 ID の欄で「照合〔2026-10-19〕の値」と書いたものは、2026-10-19 の照合（docs/evidence/verification/ の本書の結果）で照合先が返した値で、報告の記載ではない。報告の記載は括弧の中に残した。行の中身（§3 以降の事実・数値）は変えていない

### 0.3 照合と原典確認の状態

- B-01〜B-11: 2026-09-16 に Crossref と arXiv API で全 11 行が「実在・書誌一致」。数値の原典確認は、旧地図の印に「原典確認（利用者）」とある行（B-01、B-03、B-08、B-09）を §5 に写した
- B-01〜B-30: 2026-10-19 に書誌を機械照合した（docs/evidence/verification/ の本書の結果。不在 0）。差の出た B-02・B-03・B-06・B-10 は題名の欄が略称・説明だったもので、本版で題名を照合の値に改め、略称は括弧に残した。§5 の最後の列に行ごとの結果を書いた。数値の原典確認は未実施
- B-18（CoTDet）は報告が ID を確定できなかった。起票者が 2026-10-19 に web 検索で arXiv 2309.01093 を特定した（arXiv の PDF と CVF の open access の頁が同じ題名）。報告には無い ID であり、照合で確かめるまで引用として使わない

---

## 1. 系統表

| 系統 | 代表 | 現役度（報告） | 理由（報告） | 本地図の行 |
|---|---|---|---|---|
| 工程・行動と道具認識の多タスク化 | EndoNet、MTRCNet-CL、Phase-Informed Tool Segmentation（ToolSeg） | 新興 | 工程の条件付けそのものは ToolSeg が MICCAI 2025 で査読済み。ただし box 検出ではなく分割 | B-01、B-02、B-03、B-15 |
| 条件付きの affine 変調／FiLM | FiLM、ToolSeg の PAFT | 新興 | 手術での工程条件付きの実装として ToolSeg 2025。FiLM 自体の現役度は依頼の厳格な比較表の条件では不明 | B-04、B-06、B-15 |
| クラス logit の事前分布・再スコア | COCO-Tasks、contextual rescoring、Barnea & Ben-Shahar | 不明 | 原理は使われ続けているが、同じベンチマークでの 2024–2026 の比較表による確認はできず | B-16、B-26 |
| DETR の query の条件付け | Conditional DETR、CoTDet、Grounding DINO | SOTA 級（open-set／grounded detection に限る） | Grounding DINO は ECCV 2024 の査読版で COCO zero-shot、ODinW、RefCOCO 系を扱う。通常の closed-set の検出器の SOTA という意味ではない | B-21、B-18、B-19、B-07 |
| cross-attention による外部信号の融合 | MDETR、GLIP、Grounding DINO、LAVT | 定番の基準〜SOTA 級（言語に接地した検出・分割に限る） | Grounding DINO が 2024 年の査読済みの到達点の一つ | B-07、B-20、B-19、B-05 |
| task／affordance で条件付けた検出 | What Object Should I Use?（COCO-Tasks）、TOIST、CoTDet | 不明 | COCO-Tasks 上で後続の TOIST・CoTDet が前段を上回る系譜は確認したが、2024–2026 の査読比較表を確認できず | B-16、B-17、B-18 |
| graph・場面と物体の関係 | Structure Inference Net、COCO-Tasks の GGNN | 不明 | Structure Inference Net は CVPR 2018、COCO-Tasks は CVPR 2019 | B-11、B-16 |
| 動画の特徴・proposal の集約 | SELSA、StreamYOLO、LongShortNet、DAMO-StreamNet | 不明 | Argoverse-HD の streaming 系では LongShortNet・DAMO-StreamNet が後続だが、直近 2 年の査読比較表による判定はできず | B-10、B-23、B-24、B-25 |
| 長期の memory・context bank | Context R-CNN、SELSA | 不明 | 動画文脈の基礎の系統として参照されるが、依頼の現役度の定義を満たす 2024–2026 の比較表は未確認 | B-09、B-10 |
| action prompt による active な物体の選択 | ActionVOS | 不明 | ECCV 2024 の査読済みで強い結果を持つが、独立追試・複数の後続比較が少ない | B-22 |
| 凍結した検出器・凍結した基盤モデルへの prompt | CLIPSeg、LAB-Det | 新興 | LAB-Det は 2026 のプレプリントで、凍結した検出器を言語記述だけで条件付ける。査読済みではない | B-06、B-29 |
| 文脈の偏り・文脈の失敗 | Barnea & Ben-Shahar、Singh ほか、Kim ほかの再現 | 定番の基準というより否定的証拠の系統 | 文脈が localization の誤りを直せないこと、典型的な共起への依存が分布外で崩れること、独立追試で一部の符号が変わることを含む | B-26、B-27、B-28 |
| 小標本・動画単位の分割・漏れ | Varoquaux 2018、EgoSurgery-Tool の動画単位の split | 定番の方法論上の注意点 | 小標本の交差検証の大きな不確実性と、動画由来のデータを動画単位で分ける設計 | B-30、B-12 |
| タスクの親和性・負の転移（旧地図の系統。B2 の系統表には無い） | Which Tasks Should Be Learned Together | 旧地図に記載なし | 旧地図に記載なし | B-08 |
| EgoSurgery のデータセット（B2 の方向 1。系統表には無く、詳細記録から起票者が足した） | EgoSurgery-Tool、EgoSurgery-Phase、EgoSurgery-HTS | EgoSurgery-Tool は定番の基準（EgoSurgery-Tool の中で）。Phase は不明。HTS は新興 | §4 | B-12、B-13、B-14 |

B2 の報告は、この系統表から言える事実として「外部の信号で検出を条件付ける研究は多数あるが、依頼の制約をすべて同時に満たすもの（独立に学習して完全に凍結した工程モデルと DETR 検出器の間だけに小モジュールを置き、同時刻の予測工程だけを渡し、online・少数の一人称開放手術動画で box mAP を測る）は確認できなかった」と書いている（L23）。

---

## 2. 行の一覧

| ID | 文献 | 書誌 ID | 掲載先 | 方向 | 読んだ範囲 | 出所 |
|---|---|---|---|---|---|---|
| B-01 | Twinanda ほか 2017, EndoNet | arXiv 1602.03012 | IEEE TMI | 旧地図に記載なし | 全文 | 旧 B.1 |
| B-02 | Twinanda ほか 2016, Single- and Multi-Task Architectures for Tool Presence Detection Challenge at M2CAI 2016（M2CAI 技術報告。題名は照合〔2026-10-19〕の値） | arXiv 1610.08851 | M2CAI 技術報告。N1 は別の arXiv ID を挙げたが、照合（2026-10-19）でそれは M2CAI 2016 の工程のチャレンジの論文と分かった（別の文献。地図 N §8） | 旧地図に記載なし | 全文 | 旧 B.1 |
| B-03 | Jin, Li, Dou, Chen, Qin, Fu, Heng 2020, Multi-Task Recurrent Convolutional Network with Correlation Loss for Surgical Video Analysis（MTRCNet-CL。題名は照合〔2026-10-19〕の値） | arXiv 1907.06099 | Medical Image Analysis | 旧地図に記載なし | 全文 | 旧 B.1 |
| B-04 | Perez, Strub, de Vries, Dumoulin, Courville 2018, FiLM | arXiv 1709.07871 | AAAI 2018 | 旧地図に記載なし | 全文 | 旧 B.1 |
| B-05 | Yang, Wang, Tang, Chen, Zhao, Torr 2022, LAVT | arXiv 2112.02244 | CVPR 2022 | 旧地図に記載なし | 全文 | 旧 B.1 |
| B-06 | Lüddecke, Ecker 2022, Image Segmentation Using Text and Image Prompts（CLIPSeg。題名は照合〔2026-10-19〕の値） | arXiv 2112.10003 | CVPR 2022 | 旧地図に記載なし | 全文 | 旧 B.1 |
| B-07 | Kamath ほか 2021, MDETR | arXiv 2104.12763 | ICCV 2021 | 旧地図に記載なし | 要旨 | 旧 B.1 |
| B-08 | Standley, Zamir, Chen, Guibas, Malik, Savarese 2020, Which Tasks Should Be Learned Together | arXiv 1905.07553 | ICML 2020 | 旧地図に記載なし | 全文 | 旧 B.1 |
| B-09 | Beery, Wu, Rathod, Votel, Huang 2020, Context R-CNN | arXiv 1912.03538 | CVPR 2020 | 旧地図に記載なし | 全文 | 旧 B.1 |
| B-10 | Wu, Chen, Wang, Zhang 2019, Sequence Level Semantics Aggregation for Video Object Detection（SELSA。題名は照合〔2026-10-19〕の値） | arXiv 1907.06390 | ICCV 2019 | 旧地図に記載なし | 全文 | 旧 B.1 |
| B-11 | Liu, Wang, Shan, Chen 2018, Structure Inference Net（SIN） | arXiv 1807.00119 | CVPR 2018 | 旧地図に記載なし | 要旨 | 旧 B.1 |
| B-12 | Ryo Fujii, Hideo Saito, Hiroki Kajita 2024, EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos | arXiv 2406.03095 | arXiv プレプリント | 1 | 本文（データ統計、split、Tables 3–5、誤りの分析） | L29–L53 |
| B-13 | Ryo Fujii, Masashi Hatano, Hideo Saito, Hiroki Kajita 2024, EgoSurgery-Phase（地図 C の C-02 と同じ論文） | arXiv 2405.19644 | MICCAI 2024（査読） | 1 | 本文 HTML と版の metadata | L55–L69 |
| B-14 | Nathan Darjana, Ryo Fujii, Hideo Saito, Hiroki Kajita 2025, EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos | arXiv 2503.18755 | プレプリント。後に Healthcare Technology Letters 系の掲載情報あり（報告の記載）。N1 も Healthcare Technology Letters（PMC 収載）と書く | 1 | 要旨が中心 | L71–L83 |
| B-15 | Bhuvan Sachdeva ほか 2025, Phase-Informed Tool Segmentation for Manual Small-Incision Cataract Surgery（ToolSeg） | DOI 10.1007/978-3-032-05114-1_43、arXiv 2411.16794 | MICCAI 2025（査読） | 2、7 | 本文、method、Tables 1・3・4・5 | L85–L107 |
| B-16 | Johann Sawatzky, Yaser Souri, Christian Grund, Juergen Gall 2019, What Object Should I Use? – Task Driven Object Detection（COCO-Tasks） | arXiv 1904.03000 | CVPR 2019（査読） | 5 | 本文 | L109–L126 |
| B-17 | Pengfei Li, Beiwen Tian, Yongliang Shi, Xiaoxue Chen, Hao Zhao, Guyue Zhou, Ya-Qin Zhang 2022, TOIST: Task Oriented Instance Segmentation Transformer with Noun-Pronoun Distillation | arXiv 2210.10775 | NeurIPS 2022（査読） | 5 | 本文 HTML を取得したが、数値を引ける表の位置まで再確認できず数値なし | L128–L140 |
| B-18 | Jiajin Tang, Ge Zheng, Jingyi Yu, Sibei Yang 2023, CoTDet: Affordance Knowledge Prompting for Task Driven Object Detection | arXiv 2309.01093（起票者が 2026-10-19 に web 検索で特定。報告は ID を確定できなかった） | ICCV 2023（査読） | 5 | 著者の公式 project page の method・main results | L142–L155 |
| B-19 | Shilong Liu ほか 2024, Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection | arXiv 2303.05499 | ECCV 2024（査読） | 5 | 要旨・公式実装の説明が中心 | L157–L170 |
| B-20 | Liunian Harold Li ほか 2022, Grounded Language-Image Pre-training（GLIP） | arXiv 2112.03857 | CVPR 2022（査読） | 5 | 要旨のみ | L172–L182 |
| B-21 | Depu Meng ほか 2021, Conditional DETR for Fast Training Convergence | arXiv 2108.06152 | ICCV 2021（査読） | 5 | 要旨・既知の手法の定義。個別の一次ページを十分に展開できず数値は不記載 | L184–L193 |
| B-22 | Liangyang Ouyang, Ruicong Liu, Yifei Huang, Ryosuke Furuta, Yoichi Sato 2024, ActionVOS: Actions as Prompts for Video Object Segmentation（著者は照合〔2026-10-19〕の値。報告に記載なし） | arXiv 2407.07402、DOI 10.1007/978-3-031-72684-2_13 | ECCV 2024（査読） | 3 | 本文、データ構築、指標、Table 1 | L195–L212 |
| B-23 | Jinrong Yang, Songtao Liu, Zeming Li, Xiaoping Li, Jian Sun 2022, StreamYOLO: Real-time Object Detection for Streaming Perception（査読版の題名は Real-time Object Detection for Streaming Perception） | arXiv 2207.10433 | CVPR 2022（査読） | 4 | 要旨と、後続の LongShortNet の本文の比較 | L214–L226 |
| B-24 | Chenyang Li ほか 2023, LongShortNet: Exploring Temporal and Semantic Features Fusion in Streaming Perception | arXiv 2210.15518 | ICASSP 2023（査読） | 4、7 | 本文、Tables 1・3–6 | L228–L246 |
| B-25 | Jun-Yan He ほか 2023, DAMO-StreamNet: Optimizing Streaming Perception in Autonomous Driving | DOI 10.24963/ijcai.2023/90、arXiv 2303.17144 | IJCAI 2023（査読） | 4 | arXiv HTML の方法の概要・IJCAI の公式ページ | L248–L260 |
| B-26 | Ehud Barnea, Ohad Ben-Shahar 2019, Exploring the Bounds of the Utility of Context for Object Detection | arXiv 1711.05471 | CVPR 2019（査読） | 4、7 | 本文 HTML・要旨 | L262–L274 |
| B-27 | Krishna Kumar Singh, Dhruv Mahajan, Kristen Grauman, Yong Jae Lee, Matt Feiszli, Deepti Ghadiyaram 2020, Don't Judge an Object by Its Context: Learning to Overcome Contextual Bias | arXiv 2001.03152 | CVPR 2020（査読） | 4、7 | 本文 HTML・要旨 | L276–L287 |
| B-28 | Sunnie S. Y. Kim, Sharon Zhang, Nicole Meister, Olga Russakovsky 2021, [Re] Don't Judge an Object by Its Context: Learning to Overcome Contextual Bias | arXiv 2104.13582 | ML Reproducibility Challenge 系の再現 | 7 | 要旨 | L289–L301 |
| B-29 | Xu Zhang, Zhe Chen, Jing Zhang, Dacheng Tao 2026, LAB-Det: Language as a Domain-Invariant Bridge for Training-Free One-Shot Domain Generalization in Object Detection | arXiv 2602.06474 | プレプリント | 5 | 要旨のみ | L303–L314 |
| B-30 | Gaël Varoquaux 2018, Cross-validation failure: Small sample sizes lead to large error bars | DOI 10.1016/j.neuroimage.2017.06.061、arXiv 1706.07581 | NeuroImage（査読） | 6 | 要旨・書誌 | L316–L325 |

---

## 3. 近さ（距離の軸）

| ID | 視点 | ドメイン | 課題の形（送り手 → 受け取り手、信号） | 推論の規約 | データ規模 | モデルの状態（凍結の範囲） |
|---|---|---|---|---|---|---|
| B-01 | 旧地図に記載なし | 手術（Cholec80） | 工程の正解ラベルを学習時の教師に使う。受け取り手はフレーム単位の器具在否（box ではない）。推論時に工程を読まない | 旧地図に記載なし（時間モデルなし） | Cholec80。10／20／30／40 動画 | 共有の CNN の共同学習 |
| B-02 | 旧地図に記載なし | 手術（M2CAI16-tool、Cholec80 40 動画） | B-01 と同じ | 旧地図に記載なし | M2CAI16-tool、Cholec80 40 動画 | B-01 と同じ |
| B-03 | 旧地図に記載なし | 手術（Cholec80） | 送り手は工程側の LSTM の特徴ベクトル（10 s の系列）。受け取り手はフレーム単位の器具在否。学習した行列で器具の事前分布へ写し KL で整合させる | 旧地図に記載なし | Cholec80 | 共有 encoder＋二分岐の共同学習で、凍結した塔＋界面ではない |
| B-04 | 旧地図に記載なし | 非医療（CLEVR） | 質問の特徴 → 画像レベルの分類（dense ではない） | 該当なし | CLEVR | 旧地図に記載なし |
| B-05 | 旧地図に記載なし | 非医療（RefCOCO） | 正解のテキスト token → 画素の分割 | 旧地図に記載なし | RefCOCO | 旧地図に記載なし |
| B-06 | 旧地図に記載なし | 非医療（PhraseCut） | CLIP の埋め込み（凍結）→ 画素の分割 | 旧地図に記載なし | PhraseCut | CLIP は凍結。学習するパラメータは 1,122,305（D=64） |
| B-07 | 旧地図に記載なし | 非医療 | 正解のテキスト → box の集合予測 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし |
| B-08 | 旧地図に記載なし | 非医療（Taskonomy 由来の dense タスク） | 共有 backbone の multi-task。推論時の送り手なし | 該当なし | Taskonomy 由来 | 共有 backbone |
| B-09 | 固定カメラ | 非医療 | 他フレームの ROI 特徴（Faster R-CNN 由来）で memory bank を作り、現フレームの box 検出へ attention で注入。attend したベクトルを proposal の特徴へチャネルごとの bias として加える | 旧地図に記載なし（時間幅 1 分〜1 か月の memory） | SS、CCT、CityCam | 「凍結した送り手 → 凍結した検出器の間だけを学習」した研究ではない |
| B-10 | 旧地図に記載なし | 非医療（ImageNet VID、EPIC-KITCHENS） | ±10 s の proposal 特徴 → 現フレームの box 検出。行動ラベルは使わない | 旧地図に記載なし（前後 ±10 s を使う） | ImageNet VID、EPIC-KITCHENS | 旧地図に記載なし |
| B-11 | 旧地図に記載なし | 非医療（VOC、COCO） | 場面の特徴＋proposal の関係 → box 検出 | 旧地図に記載なし | VOC、COCO | 旧地図に記載なし |
| B-12 | 一人称 | 開放手術 | 一人称の開放手術のフレームから 15 種類の術具と手を bbox で検出。工程の条件付けはしていない | 静止フレームの検出器として評価。未来の情報の利用はない | EgoSurgery-Phase の 15 動画の部分集合、15,437 画像、49,652 個の術具 box、15 クラス。手は 46,320 box・4 カテゴリ。親データは 21 動画・約 15 時間（本文の記載）。公式 split は 10 train／2 validation／3 test の動画単位 | 検出器を単独で学習。工程モデルとの界面はない |
| B-13 | 一人称 | 開放手術 | 一人称の開放手術動画から工程を予測 | 過去のみかは報告の取得範囲からは不明 | 初期版と EgoSurgery-Tool の記載は 21 動画・約 15 時間・10 術式・8 術者・9 工程。arXiv v3 の要旨の metadata は 20 動画で、版によって動画本数が一致しない | 工程認識モデル単独 |
| B-14 | 一人称 | 開放手術 | 手・術具・相互作用の画素単位の分割 | 不明 | 14 術具カテゴリ。本数・時間は報告の確認範囲では不明 | 不明 |
| B-15 | 顕微鏡 | 開放の眼科手術（manual small-incision cataract surgery） | 手術フレームと工程情報から術具を分割 | 工程予測器は MS-TCN++。causal masking・未来フレームの禁止を明示する記述を報告は確認できず、online かは不明 | 53 動画、18 工程、注釈フレーム 3,527、術具 13 クラス | 工程予測器は別のデータで学習。分割モデルは工程の条件付けのモジュールを含めて学習する。凍結した検出器＋界面だけの学習ではない |
| B-16 | 三人称の静止画 | 非医療 | 画像と task（例 sit comfortably on）から、その task に適した物体の box を選ぶ | 静止画。online／offline の区別は該当しない | COCO-Tasks、約 40,000 画像、14 task | 物体候補の見えと場面全体の関係を GGNN で扱う。検出器を凍結して界面だけを学習するかの観点では完全な一致ではない |
| B-17 | 三人称 | 非医療 | task の動詞を条件に、その task を afford する物体の box と instance mask を予測 | 静止画 | 不明 | transformer の検出・分割器そのものを task 指向の目的で学習。凍結した検出器＋界面だけではない |
| B-18 | 三人称の静止画 | 非医療 | 画像＋task のテキスト＋LLM 由来の affordance の知識から、適した物体の box／mask | 静止画 | 不明 | 知識で条件付けた decoder を学習。凍結した検出器＋界面だけではない |
| B-19 | 該当なし | 非医療 | 画像＋テキストの prompt から open-set の box | 静止画 | 不明 | 視覚言語の検出器を grounded pretraining で学習。凍結した検出器＋小さな界面とは異なる |
| B-20 | 不明 | 非医療 | 検出を phrase grounding として定式化し直し、画像と言語の接地を学習 | 不明 | 不明 | end-to-end の grounded pretraining |
| B-21 | 不明 | 不明 | object query に conditional spatial query を入れ、DETR の cross-attention の探索範囲を絞る。条件は decoder の中で作るもので、外部の予測ではない | 不明 | 不明 | 不明 |
| B-22 | 一人称 | 非医療 | 一人称動画＋行動の語り＋物体名から、行動に関わる active な物体の mask と active／inactive の分類 | 動画の分割だが、未来フレームを禁じる causal online の規約は確認できず | 前処理後の train 13,205 動画／76,873 物体、validation 467 動画／1,841 物体（positive 1,133、negative 708）。VISOR、VOST、VSCOS を使い、VISOR と VSCOS の clip の重なりは漏れを防ぐため除外 | ReferFormer の backbone、テキスト encoder の RoBERTa などを再学習。凍結した検出器ではない |
| B-23 | 車載の一人称に近いカメラの stream | 非医療 | 現在と前のフレームから、遅延を考慮した将来時点の検出（streaming perception） | streaming／causal。LongShortNet の本文は StreamYOLO が現在と前の 2 枚だけを入力すると記述 | Argoverse-HD | 検出器全体を streaming の目的で学習 |
| B-24 | 車載の stream | 非医療 | 現在のフレームと過去の複数の支持フレームから物体の box とクラス | 過去のみ。ShortPath に現在の I_t、LongPath に I_(t−iδt) を入れると明記 | Argoverse-HD。指標は streaming AP。先行研究と同じ train／val の split | YOLOX 系の検出器全体を fine-tune。凍結した D ではない |
| B-25 | 車載の映像 | 非医療 | streaming の物体検出。短い経路の意味特徴と長い経路の時間特徴、logit の蒸留、streaming の予測を組み合わせる | streaming。過去と現在から次の時点を予測し、将来の正解フレームを推論の入力にはしない | Argoverse-HD（系統表の記載から） | end-to-end の学習。凍結した検出器ではない |
| B-26 | 不明 | 非医療（静止画の検出） | 物体の共起・空間文脈を既存の検出結果に使った場合の改善の上限を調べる | 静止画 | 不明 | 文脈に基づく後処理・分析 |
| B-27 | 不明 | 非医療 | 物体・属性の分類で、典型的な文脈と物体の表現の相関を外し、文脈から外れた場合の汎化を改善する。box 検出ではない | 不明 | 4 データセット | 不明 |
| B-28 | 不明 | 非医療 | Singh ほか（B-27）の全 12 表の独立の再現と追加の ablation | 不明 | COCO-Stuff、DeepFashion、UnRel、AwA | 元のコードが公開されていなかったため一から実装 |
| B-29 | 不明 | 非医療 | クラスごとに注釈の例を 1 つ与え、それをテキストの記述に変え、その言語の信号で凍結した基盤検出器を条件付ける | 不明 | 不明 | 検出器は凍結で重みを更新しない。学習可能な小さな界面ではなく、学習なしの prompt の生成 |
| B-30 | 該当なし | 該当なし（予測モデルの評価一般） | 小標本の予測モデルで交差検証の推定値のばらつきを検討 | 該当なし | 該当なし | 該当なし |

---

## 4. 手法の位置

| ID | 系統 | 現役度（報告）と理由 | どのベンチマークの話か | 本研究の条件で測られたか（少数動画／online／一人称） |
|---|---|---|---|---|
| B-01 | 補助損失・共有表現 | 旧地図に記載なし | Cholec80 | 旧地図に記載なし |
| B-02 | 補助損失・共有表現 | 旧地図に記載なし | M2CAI16-tool | 旧地図に記載なし |
| B-03 | 特徴 → 事前分布の相関損失 | 旧地図に記載なし | Cholec80 | 旧地図に記載なし |
| B-04 | FiLM（特徴の変調） | 旧地図に記載なし | CLEVR、CoGenT | 旧地図に記載なし |
| B-05 | cross-attention の条件付け | 旧地図に記載なし | RefCOCO | 旧地図に記載なし |
| B-06 | FiLM＋小さな decoder（凍結 encoder） | 旧地図に記載なし | PhraseCut | 旧地図に記載なし |
| B-07 | 外部の条件付きの DETR | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし |
| B-08 | タスクの親和性・負の転移 | 旧地図に記載なし | Taskonomy 由来 | 旧地図に記載なし |
| B-09 | memory bank の cross-attention＋加算の bias | 旧地図に記載なし | SS、CCT、CityCam | 旧地図に記載なし |
| B-10 | 系列レベルの意味の集約 | 旧地図に記載なし | ImageNet VID、EPIC-KITCHENS | 旧地図に記載なし |
| B-11 | graph 推論の文脈の精緻化 | 旧地図に記載なし | VOC、COCO | 旧地図に記載なし |
| B-12 | EgoSurgery の基準／closed-set の検出 | 定番の基準（EgoSurgery-Tool の中で）。データセット論文が複数の検出器の基準を提供しているため。2024–2026 の独立の後続比較表による SOTA 級は確認できず | EgoSurgery-Tool の公式 10／2／3 split | 少数動画: 該当。一人称: 該当。online の工程認識: 該当しない |
| B-13 | 工程認識／一人称の映像表現 | 不明。EgoSurgery-Phase の基準値としては重要だが、検出の条件付けのベンチマークではない | EgoSurgery-Phase | 一人称: 該当。依頼の 15 動画の交差検証とは別の設定 |
| B-14 | 手・術具の相互作用の表現 | 新興（2025、EgoSurgery の追加注釈の系統） | EgoSurgery-HTS | 一人称: 該当。その他は不明 |
| B-15 | FiLM 型の工程を意識した特徴変調。PAFT は工程の埋め込みからチャネルごとの affine の scale／shift を生成 | 新興。MICCAI 2025 の査読済みで、著者以外による十分な追試は確認できず | 53 動画のデータ（名称は報告に無い）、CaDIS | 少数動画: 数十本の規模に近いが 53 本。online: 不明。一人称: 該当しない |
| B-16 | task の事前分布＋graph の文脈＋再順位付け | 置き換えられた結果は確認（同じ COCO-Tasks で後続の TOIST・CoTDet がより高い結果を報告）。ただし「比較対象として使われなくなった」まで確認できないため定義上は不明 | COCO-Tasks | 該当しない |
| B-17 | task で条件付けた query／attention、noun-pronoun の蒸留 | 不明（COCO-Tasks 上の後続の系統だが、直近 2 年の比較表による分類はできず） | COCO-Tasks（系統表から） | 該当しない |
| B-18 | 言語・affordance の prompt → object query の条件付け | 不明（2023 ICCV 以降の 2024–2026 の査読比較表を確認できず） | task 駆動の検出のベンチマーク（TOIST・GGNN と同じ） | 該当しない |
| B-19 | feature enhancer、言語に導かれた query の選択、cross-modality の decoder | SOTA 級（論文中の zero-shot／open-set のベンチマークについて）。closed-set の手術検出器への一般化は別の問題 | COCO zero-shot、ODinW、RefCOCO 系 | 該当しない |
| B-20 | 言語で条件付けた検出／cross-modal の接地 | 定番の基準に近いが、直近 2 年の複数の査読表を十分に確認できず正式には不明 | 不明 | 該当しない |
| B-21 | query の条件付け | 不明 | 不明 | 該当しない |
| B-22 | 行動を prompt にする／cross-modal の条件付け | 不明（ECCV 2024 の査読済みだが独立追試を十分に確認できず） | VISOR、VOST、VSCOS から作った ActionVOS の split | 一人称: 該当。online・box 検出・凍結した検出器: 該当しない |
| B-23 | causal な時間特徴の融合 | 不明（後続の LongShortNet・DAMO-StreamNet が同じベンチマークで上回るが、比較対象として残っているため置き換え済みの条件を満たさない） | Argoverse-HD | causal: 該当。それ以外: 該当しない |
| B-24 | 過去のみの時間特徴の集約／memory | 不明 | Argoverse-HD | causal: 該当。それ以外: 該当しない |
| B-25 | causal な memory＋時間の融合＋蒸留 | 不明 | Argoverse-HD | causal: 該当。それ以外: 該当しない |
| B-26 | 文脈の事前分布／再スコア | 不明 | 不明 | 該当しない |
| B-27 | 文脈の偏りの軽減 | 不明 | 4 データセット | 該当しない |
| B-28 | 独立の再現／文脈の偏り | 該当しない | COCO-Stuff、DeepFashion、UnRel、AwA | 該当しない |
| B-29 | 凍結した検出器＋外部の言語の prompt | 新興（2026 のプレプリントで査読の状況は不明） | 不明 | 該当しない |
| B-30 | 評価の不確実性 | 定番の方法論上の注意点（系統表） | 該当なし | 小標本の交差検証という意味で近い |

---

## 5. 証拠の質

| ID | 何と何を比べた差か | その要素だけを変えた比較か | seed・分割・検定 | 著者以外の追試・採用 | 照合・原典確認（旧地図の行は旧地図の印を原文のまま） |
|---|---|---|---|---|---|
| B-01 | multi-task の EndoNet と single-task の ToolNet | 工程の補助損失だけを切り出した ablation ではない（旧地図） | 旧地図に記載なし | 旧地図に記載なし | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1602.03012）。照合2026-10-19: arXiv 1602.03012 実在・書誌一致 |
| B-02 | ToolNet と EndoNet | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1610.08851）。照合2026-10-19: arXiv 1610.08851 実在・書誌に差（題名の欄が略称・説明だったため。本版で題名を改めた） |
| B-03 | MTRCNet と MTRCNet-CL（Table 1）。写像の空間の比較（Table 2） | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1907.06099）。旧地図の注記: 数値は原典と一致（TS1 85.1、TS2 88.1 も）。照合2026-10-19: arXiv 1907.06099 実在・書誌に差（題名の欄が略称・説明だったため。本版で題名を改めた） |
| B-04 | FiLM ありとなし（Table 2） | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1709.07871）。照合2026-10-19: arXiv 1709.07871 実在・書誌一致 |
| B-05 | 条件付けなし／PWAM のみ／全体（Table 2）、置く場所（Table 3） | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2112.02244）。照合2026-10-19: arXiv 2112.02244 実在・書誌一致 |
| B-06 | FiLM のありとなしの対は number not available。CLIP 事前学習のありとなし（Table 9） | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 2112.10003）。照合2026-10-19: arXiv 2112.10003 実在・書誌に差（題名の欄が略称・説明だったため。本版で題名を改めた） |
| B-07 | 条件のありとなしは number not available（課題そのものがテキストの条件付き） | 該当なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。要旨。片方。照合2026-09-16: 実在・書誌一致（arXiv 2104.12763）。照合2026-10-19: arXiv 2104.12763 実在・書誌一致 |
| B-08 | タスクの組の転移（Table 2 Setting 1）、容量とデータ量（Table 5） | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1905.07553）。照合2026-10-19: arXiv 1905.07553 実在・書誌一致 |
| B-09 | 文脈ありとなし（Table 1）、時間幅、集約の方式 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。原典確認（利用者）。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1912.03538）。旧地図の注記: 数値は原典と一致。照合2026-10-19: arXiv 1912.03538 実在・書誌一致 |
| B-10 | 集約ありとなし | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。全文。片方。照合2026-09-16: 実在・書誌一致（arXiv 1907.06390）。照合2026-10-19: arXiv 1907.06390 実在・書誌に差（題名の欄が略称・説明だったため。本版で題名を改めた） |
| B-11 | number not available（要旨） | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし | 未照合。要旨。片方。照合2026-09-16: 実在・書誌一致（arXiv 1807.00119）。照合2026-10-19: arXiv 1807.00119 実在・書誌一致 |
| B-12 | 同じ公式 split・COCO 事前学習の複数の検出器（Table 4）。手の検出の初期化（Table 5） | モデル間の比較であり工程信号の効果ではない | 公式の単一 split。複数の seed・統計検定は本文で確認できず | 確証を得た独立追試は不明 | 照合2026-10-19: arXiv 2406.03095 実在・書誌一致 |
| B-13 | 検出の条件付けに関する値はなし | 該当なし | 依頼の 15 動画の交差検証とは別の設定 | 不明 | 照合2026-10-19: arXiv 2405.19644 実在・書誌一致 |
| B-14 | P→D 型の工程 → box 検出の比較はなし | 該当なし | 不明 | 不明 | 照合2026-10-19: arXiv 2503.18755 実在・書誌一致 |
| B-15 | Table 1 で同じ構造族の中で、工程なし／予測工程／正解工程／疑似ラベルの有無を分けて比較 | データ・fold・分割モデルの族が同じで、工程信号の質を変えた比較 | 動画単位の 5-fold 交差検証。seed 数と統計検定は確認できず。工程モデルは漏れを防ぐため、分割の評価集合とは独立な内部の 90 動画で学習。N1: 工程の予測器 MS-TCN++ は「processes the video at full temporal resolution」（§4.2）で causal かは不明、凍結したかの明示も不明。対照の v0 は条件付けの構造を持たず、界面を保ったまま入力を空にする対照ではない（地図 N の N-20） | 著者以外の十分な追試は確認できず | 照合2026-10-19: DOI 10.1007/978-3-032-05114-1_43 実在・書誌一致、arXiv 2411.16794 実在・書誌一致 |
| B-16 | 同じ task 指向の問題で、分類／ranker／提案＋融合を比較し、さらに正解 box と Faster-RCNN の検出の入力条件を比較（表「Comparison to Baselines mAP@0.5」） | 提案の GGNN／融合と基準の構造が異なり、task の事前分布だけを変えた clean な ablation ではない | 表からは不明 | 後続の TOIST・CoTDet が同じ COCO-Tasks で比較 | 照合2026-10-19: arXiv 1904.03000 実在・書誌一致 |
| B-17 | 数値は報告に無い | 不明 | 不明 | 不明 | 照合2026-10-19: arXiv 2210.10775 実在・書誌一致 |
| B-18 | 著者ページは TOIST・GGNN と同じ task 駆動のベンチマークで比較 | 不明 | 不明 | 不明 | 2026-10-19 の照合の時点では ID なし（報告は ID を確定できなかった）。起票者が特定した ID は次の照合で確かめる |
| B-19 | 依頼への直接の情報なし | 該当なし | 依頼への直接の情報なし | 不明 | 照合2026-10-19: arXiv 2303.05499 実在・書誌一致 |
| B-20 | 依頼に対応する clean な ablation なし | 該当なし | 不明 | 不明 | 照合2026-10-19: arXiv 2112.03857 実在・書誌一致 |
| B-21 | 数値不記載 | 該当なし | 不明 | 不明 | 照合2026-10-19: arXiv 2108.06152 実在・書誌一致 |
| B-22 | Table 1 で同じ ActionVOS の学習の設定について、行動 prompt のありとなし | 同じ backbone の族で prompt を入れるかだけの比較 | 元の split を使用。複数 seed・統計検定は確認できず | 独立追試を十分に確認できず | 照合2026-10-19: arXiv 2407.07402 実在・書誌一致、DOI 10.1007/978-3-031-72684-2_13 実在・書誌一致 |
| B-23 | LongShortNet の Table 1 での比較 | 外部の工程信号ではなく時間特徴の差 | 不明 | 後続の LongShortNet・DAMO-StreamNet が比較 | 照合2026-10-19: arXiv 2207.10433 実在・書誌一致 |
| B-24 | Table 5 は同じモデルで時間の範囲（N、δt）だけを変更。現在のみ（N=0）と過去フレームを加えた条件を直接比較。Table 6 は融合の位置と重み付け | Table 5 は clean な比較 | 同じ固定の train／val split。複数 seed・検定は確認できず | 不明 | 照合2026-10-19: arXiv 2210.15518 実在・書誌一致 |
| B-25 | 外部の意味信号は使わない | 該当なし | 不明 | 不明 | 照合2026-10-19: DOI 10.24963/ijcai.2023/90 実在・書誌一致、arXiv 2303.17144 実在・書誌一致 |
| B-26 | 文脈を使った場合の改善の上限の分析 | 該当なし（分析） | 不明 | 不明 | 照合2026-10-19: arXiv 1711.05471 実在・書誌一致 |
| B-27 | 典型的な文脈が無いときの汎化（問題設定そのもの） | 不明 | 4 データセット | B-28 が独立に再現 | 照合2026-10-19: arXiv 2001.03152 実在・書誌一致 |
| B-28 | 元論文の全 12 表の再現と追加の ablation | 該当なし（再現） | 不明 | 著者以外の追試そのもの | 照合2026-10-19: arXiv 2104.13582 実在・書誌一致 |
| B-29 | 要旨のみ。数値の記載なし | 不明 | 不明 | 不明 | 照合2026-10-19: arXiv 2602.06474 実在・書誌一致 |
| B-30 | 小標本の交差検証の推定値のばらつき | 該当なし | 該当なし | 不明 | 照合2026-10-19: DOI 10.1016/j.neuroimage.2017.06.061 実在・書誌一致、arXiv 1706.07581 実在・書誌一致 |

---

## 6. 効果（数値は元のまま。指標名は原文）

| ID | 指標・値・表番号 | 符号 | 符号や大きさが変わる条件 |
|---|---|---|---|
| B-01 | 40 動画: ToolNet 80.9 → EndoNet 81.0 mean AP（+0.1、Table II）。10 動画: 65.9 → 62.0（−3.9）。20 動画 70.9 → 67.5（−3.4）、30 動画 73.6 → 77.5（+3.9）。差は multi-task の EndoNet と single-task の ToolNet の差 | 学習量で変わる | 符号が学習量で変わる。逆方向の oracle（正解の器具 → 工程）は 75.2 → 75.3 |
| B-02 | ToolNet 73.9 → EndoNet 74.2 mAP（+0.3、Table 1）。著者が no significant improvement と記載 | 零に近い | 学習量の差の方が結果に出た、と著者 |
| B-03 | MTRCNet 87.5 → MTRCNet-CL 89.1 tool mAP（+1.6、Table 1）。Table 2: label-space の写像 86.8、mutual 87.1、feature-space 89.1。事前分布と出力の平均 88.8、事前分布のみ 88.4 | feature-space は正 | ラベル空間の結合は特徴空間より低く、相関損失なしの 87.5 も下回る。相互の写像は一方向より低い |
| B-04 | Table 2: 97.4／FiLM なし 21.4。β=0 で 96.9、γ=1 で 95.9、FiLM 層一つで 97.3 | 正 | CoGenT で分布の組み合わせに依存（A 98.3、B 75.6）。fine-tune の後の忘却 |
| B-05 | Table 2 RefCOCO val: なし oIoU 68.82／mIoU 68.87、PWAM のみ 70.78／71.96、全体 72.73／74.46 | 正 | 置く場所で符号が変わる: Table 3 で 72.27 → 72.06、72.29 → 71.38。追加の decoder で 72.73 → 72.12 |
| B-06 | FiLM のありとなしの対は number not available。Table 9: text mIoU 43.6／AP 76.7、CLIP 事前学習なし 13.1／12.6 | FiLM の対は不明 | D=16 で 37.4／71.5、layer-3 のみで 31.9／64.9 |
| B-07 | 条件のありとなしは number not available | 不明 | 記載なし（要旨） |
| B-08 | Table 2 Setting 1: Depth→SemSeg +4.17%、SemSeg→Depth −5.41%、SemSeg→Normals −11.29%、→Edges −34.64%。五タスク同時は単独の平均比 −19.00% | 方向で正負が分かれる | 親和性は方向・容量・データ量に依存。容量を変えると Table 2 と Table 5 の関係が大きく変わり、データ 5% でも変わる |
| B-09 | Table 1: SS 37.9 → 55.9 mAP@0.5、CCT 56.8 → 76.3、CityCam 38.1 → 42.6。時間幅 1 min 50.3、1 h 52.1、1 day 52.5、1 week 54.1、1 month 55.6 | 正 | 多数決は 37.9 → 37.8（−0.1）。空間平均 39.6、単フレームの attention 44.9、短期 46.4、長期 55.6 |
| B-10 | VID: 73.62 → 80.25 mAP。EPIC seen 36.57 → 37.97、unseen 31.86 → 34.80 | 正 | 同フレームの集約は高速の動体で 51.53 → 51.43。Seq-NMS の追加で 82.69 → 82.48、84.30 → 83.73。EPIC は予備的で調整が不十分と著者 |
| B-11 | number not available（要旨） | 不明 | 記載なし（要旨） |
| B-12 | Table 4 の AP: Faster R-CNN 37.7、RetinaNet 36.2、Cascade R-CNN 38.8、CenterNet 42.4、Sparse R-CNN 37.0、VarifocalNet 45.8、Deformable DETR 30.0、DDQ 43.2、DINO 39.7（モデル間の比較であり工程信号の効果ではない）。Table 5 の手の検出: COCO の初期化 55.3 AP、ImageNet 50.7、COCO+EgoHands 52.1（COCO 単独より −3.2 AP） | 検出器の間で差あり。外部の関連データを足した事前学習は COCO 単独より低い | 著者は domain gap を論じている。誤りの分析では scissors と needle holder の混同、forceps・gauze・retractor の背景との混同が報告される。Figure 4 は工程と道具の偏った共起を可視化 |
| B-13 | 検出の条件付けに関する値はなし | 該当なし | 該当なし |
| B-14 | P→D 型の比較はなし | 該当なし | 該当なし |
| B-15 | Table 1: 工程なしの v0 は IoU 40.90±3.4、DSC 50.66±3.9。予測工程の gated v3 は 48.77±5.5／57.52±5.4。正解工程の gated v6 は 56.13±4.5／64.76±4.5。v0 → v3 は IoU +7.87、DSC +6.86。予測 → 正解に置き換えた v3 → v6 は IoU +7.36、DSC +7.24。Basic conditioning でも予測の v2 46.58／55.40 に対し正解の v5 54.26／62.98。Table 4（クラス別 DSC）: v0 → v3 で Cautery 63.81 → 60.28、Sideport 68.69 → 63.73、Visco 46.42 → 40.08 と悪化し、Keratome 46.24 → 67.92、Rhexis Needle（86 samples）13.98 → 30.27 と改善。正解工程の v6 は Cautery 73.38、Sideport 76.79、Visco 56.28、Rhexis Needle 38.70。Dialer（343 samples）は 40.33 → 41.54、正解でも 41.23。CaDIS の Table 5: 正解工程の v6 が mIoU 60.73、DSC 68.63 に対し、疑似ラベルを足した v7 は 59.05／67.72 | 平均では予測工程も正解工程も正。クラス別では予測工程で負のクラスがある | 「工程が有用か」と「予測工程が有用か」はクラスごとに同じ符号ではない。稀少なら必ず利得が大きいとはこの表からは言えない（Rhexis Needle は大きく、Dialer は小さい）。工程予測器の精度は accuracy 50.10%、precision 47.60%、F1 50.23%。追加の教師信号の効果も条件に依存（CaDIS の v7） |
| B-16 | 表「Comparison to Baselines mAP@0.5」: 正解 box の条件で分類 0.616、提案＋融合 0.742（+0.126）。Faster-RCNN の検出の条件で分類 0.288、提案＋融合 0.326（+0.038） | 改善 | 文脈・task の推論による差は、正解 box の上で +0.126、実際の検出器の box の上で +0.038 に縮む |
| B-17 | 数値は報告に無い。正解の名詞を学習時の特権情報として使い、推論では名詞を問わない代名詞の表現を使う（学習時は正解の補助信号、推論時は別の形式） | 不明 | 不明 |
| B-18 | 著者の project page は TOIST 比 +15.6 box AP、+14.8 mask AP、GGNN 比 +24.3 box AP、+21.2 mask AP と報告するが、原論文の表番号を確認できなかったため、報告は正式な効果量として採用していない | 不明（正式な数値なし） | 著者ページは、多様な物体カテゴリを要する task4・task6・task7 で改善が大きいと説明 |
| B-19 | 外部の信号はテキストで、工程の softmax のベクトルではない。query の条件付け・cross-attention の機構の近縁例 | 該当なし | 該当なし |
| B-20 | 対応する clean な ablation なし | 該当なし | 該当なし |
| B-21 | 数値不記載 | 該当なし | 該当なし |
| B-22 | Table 1: RF-R101 で prompt なし → あり p-mIoU 56.3 → 65.4、n-mIoU 19.9 → 19.0（低い方が良い）、gIoU 66.8 → 70.9、Acc 72.9 → 82.4。RF-SwinL は p-mIoU 64.4 → 69.1、Acc 72.8 → 80.7。RF-VSwinB は 61.6 → 68.2、Acc 72.5 → 81.2 | 同じ backbone の族で行動 prompt を入れる符号は一貫して正 | 課題の定式化そのものを RVOS と比べると、active な物体の p-mIoU は R101 で RVOS 67.7 に対し ActionVOS＋prompt 65.4 とやや低い一方、inactive な物体の誤った分割を減らし、組み合わせの指標を改善する |
| B-23 | LongShortNet の Table 1 で StreamYOLO-L は Argoverse-HD の sAP 36.1、LongShortNet-L は 37.1（外部の工程信号ではなく時間特徴の差） | 該当なし | 該当なし |
| B-24 | Table 5: LongShortNet-S は現在のみ 26.8 sAP から N=3・δt=1 で 29.8（+3.0）。L は 32.6 → 37.1（+4.5）。M は現在のみ 29.8、最良の N=4・δt=2 で 34.2（+4.4）。Table 6: S／M／L で late＋dilation 29.8／34.1／37.1、early＋average 27.1／31.7／35.3、residual を外すと 27.6／32.1／35.3。Table 1: LongShortNet-L は StreamYOLO-L に対し sAP75 35.6 → 37.7、小物体の sAP 13.8 → 15.2。大きい入力のモデルでは大物体の sAP が 63.8 → 61.7 | 過去の文脈で正 | 過去を増やし続けても単調には改善しない: S は N=3・δ=1 の 29.8 から N=5・δ=2 で 28.1、M は 34.2 から 33.6、L は 37.1 から 36.3。融合の位置・現在フレームの保持の比率で符号と大きさが変わる |
| B-25 | 工程の条件付けの直接の証拠なし | 該当なし | 該当なし |
| B-26 | 物体の共起が大きな利得を与える場合もある一方、改善が事実上不可能または実用的でない場合があり、検討した文脈は localization の誤りを修復できないため、検出の利得に上限が生じる | 上限あり | class／在否の confidence を正せても、box の localization が誤っている偽陽性・偽陰性は残る |
| B-27 | 通常のモデルが物体と文脈の共起に依存すると、典型的な文脈が消えたときに汎化が崩れることを問題設定として実証。4 データセットで評価 | 否定的な所見 | 典型的な文脈が無い場合 |
| B-28 | COCO-Stuff、DeepFashion、UnRel では feature-split による文脈外の accuracy の改善を再現した一方、AwA では性能が低下。CAM-based は元の mAP を 0.5% 以内で再現 | データセットで符号が変わる | データセットに依存し、同じ主張がすべての領域で再現されるわけではない |
| B-29 | 要旨しか読んでいないため数値は記載しない（報告） | 不明 | クラスごとに注釈の例が 1 つ追加で要る |
| B-30 | 小標本では交差検証の推定値そのものに大きな誤差幅が生じうる | 該当なし | 該当なし |

---

## 7. 実装

| ID | コード・重み・ライセンス | 追加データ・注釈 | 事前学習と評価データの重なり |
|---|---|---|---|
| B-01〜B-11 | 旧地図に記載なし | 旧地図に記載なし | 旧地図に記載なし |
| B-12 | データセットの repository は公開。repository の記載は CC BY-NC-SA 4.0（arXiv HTML の表示ライセンスとは別） | 検出そのものに工程の注釈は不要。ただし同じ動画に工程ラベルがある | COCO などを使用。EgoSurgery の test フレームが COCO に含まれるという記載は確認できず |
| B-13 | 不明 | 工程ラベル | 不明 |
| B-14 | 不明 | 画素の mask、手と術具の相互作用 | 不明 |
| B-15 | 著者の repository が公開。ライセンスは報告の取得範囲では不明 | 工程モデル用の独立の 90 手術動画、SAM2 による疑似ラベル | 工程モデルは分割の評価集合と独立 |
| B-16 | 不明 | 14 task に対する affordance／適合の注釈 | 不明 |
| B-17 | code と model の公開が論文に記載。ライセンス未確認 | 不明 | 不明 |
| B-18 | 著者の project page が code の link を提供。ライセンス不明 | LLM 由来の affordance の知識 | 不明 |
| B-19 | 公式の code と重みが公開。Grounded SAM 系との組み合わせも公式 repository に記載 | 不明 | 不明 |
| B-20 | 不明 | 不明 | 不明 |
| B-21 | 不明 | 不明 | 不明 |
| B-22 | code 公開 | 行動の語り、物体名、意味の mask、学習時の手物体の mask・疑似ラベルなど | VISOR と VSCOS の clip の重なりは漏れを防ぐため除外 |
| B-23 | 公式 code は Apache-2.0 | 不明 | 不明 |
| B-24 | code 公開 | 不明 | 不明 |
| B-25 | 著者の code repository が公開 | 不明 | 不明 |
| B-26 | 不明 | 不明 | 不明 |
| B-27 | 不明（B-28 によれば元の code は公開されていなかった） | 不明 | 不明 |
| B-28 | 再現の code が公開 | 不明 | 不明 |
| B-29 | 不明 | クラスごとに注釈の例 1 つ | 不明 |
| B-30 | 該当なし | 該当なし | 該当なし |

---

## 8. 本研究との関係

報告者の一行（各行の本研究との関係についての報告者の要約）は、報告者の読みを含むため地図から外し、起票者用の文書に移した（利用者の決定 2026-10-18）。事実としての近さは §3（距離の軸）と §4 の「本研究の条件で測られたか」に書いてある。

---

## 9. 機構の系統 × 送り手の信号段（起票者が行から組んだ索引）

旧地図 B の B.3 の表を、B2 の行を加え、言語・task の列を足して組み直した。旧表で特徴ベクトルの列に置いた LAVT（B-05）・CLIPSeg（B-06）・MDETR（B-07）は、信号が言語なので言語・task の列へ移した。各セルは「符号（行 ID、受け取り手の課題）」。受け取り手の課題は box（box 検出）、分割、在否（フレーム単位の器具在否）、分類。

| 系統 | 予測ラベル | 正解ラベル（oracle） | 確率分布 | 特徴ベクトル | 言語・task |
|---|---|---|---|---|---|
| 特徴の結合（add／concat、加算の bias） | 行なし | 行なし | 行なし | 正（B-09、box） | 行なし |
| FiLM・affine の変調 | 平均は正、クラス別に負あり（B-15、分割） | 正（B-15、分割） | 行なし | 正（B-04、分類） | 正（B-06、分割。FiLM のありとなしの対は無い） |
| cross-attention | 行なし | 行なし | 行なし | 正（B-09、box） | 正（B-05、分割。B-22、分割と active の分類）。対の無いもの（B-19・B-20、box） |
| DETR の query の条件付け | 行なし | 行なし | 行なし | 行なし | 対の無いもの（B-07、B-19、box）。正式な数値の無いもの（B-18、box） |
| 出力の class の事前分布・logit の再スコア | 行なし | 行なし | 零・負（B-03 の label-space 86.8、在否） | 零・負（B-03 の平均 88.8、在否） | 正、ただし検出 box の上で縮む（B-16、box）。文脈の共起は localization で上限（B-26、box） |
| 補助損失・共有の multi-task | 行なし | 零・負（B-01 の 10 動画 −3.9、B-02 の +0.3、在否） | 行なし | 行なし | 行なし |
| 蒸留・相関損失 | 行なし | 行なし | 行なし | 正（B-03 の +1.6、在否） | 行なし |
| 時間の履歴・窓（自分の過去フレーム） | 行なし | 行なし | 行なし | 正、ただし長すぎると低下（B-24、box）。B-23、B-25、B-10、B-09 | 行なし |
| 凍結した検出器への prompt | 行なし | 行なし | 行なし | 行なし | 数値なし（B-29、box、学習なし） |
| graph の推論 | 行なし | 行なし | 行なし | 数値なし（B-11、box） | B-16 の GGNN（box） |

工程の予測ラベル・正解ラベル・確率分布を、凍結した DETR の box 検出へ渡す行は無い（B-15 は受け取り手が分割で、受け取り手も学習する）。

---

## 10. 問いごとの事実の整理

報告者が文献の事実を依頼の問いごとに並べた節（B2 L327–L343）は、報告者の読み（「最も明確」など）を含むため地図から外し、起票者用の文書に移した（利用者の決定 2026-10-18）。各事実は §2〜§7 の行と §9 の索引にある。

---

## 11. 見つからなかったもの

### 11.1 B2 の報告（L345–L371）

「見つからなかった」は、2026 年 10 月 18 日までの検索で実在と条件を一次資料で確認できなかったという意味で、存在しないことを意味しない（報告の定義）。

1. **EgoSurgery で工程の予測を box 検出器に入力する直接の実験。** 検索語: EgoSurgery phase tool detection conditioning／EgoSurgery-Tool phase detector／egocentric open surgery phase informed tool detection に相当する語。EgoSurgery-Phase、EgoSurgery-Tool、EgoSurgery-HTS は確認できたが、工程のラベル・予測を bbox 検出器の logits／特徴／query に入れて AP を測る論文は確認できなかった。方向 1 で実在確認 3 件、直接該当 0 件
2. **独立に学習して完全に凍結した二モデルの間だけを、学習可能な界面でつなぐ box 検出。** 検索語: frozen detector adapter external signal object detection／frozen object detector prompt adapter／parameter efficient object detection frozen detector。凍結した VLM・backbone、凍結した検出器を下流の HOI に使う研究、学習なしの言語の条件付けは見つかったが、D の box／class のヘッドまで凍結し、P も凍結し、P の同時刻の予測だけが学習可能な界面を通して D の box mAP を改善する完全一致の例は確認できなかった。LAB-Det（B-29）は凍結した検出器だが学習なしの言語の橋
3. **同じ界面に正解の工程ベクトルと予測の工程ベクトルを差し替え、box mAP で oracle gap を測る実験。** ToolSeg（B-15）で同じ型の比較を分割で確認したが、bbox 検出では確認できなかった
4. **工程で条件付けた DETR で、query／logit／FiLM の注入の位置だけを揃えて比べる ablation。** Grounding DINO／CoTDet の query・cross-attention、ToolSeg の特徴の affine 変調、COCO-Tasks の graph・再順位付けは個別に存在するが、同じ検出器・同じ外部信号・同じ split で「logit 対 特徴 対 query 対 cross-attention」を一要因だけ変える比較は確認できなかった
5. **予測した文脈の confidence・較正と、下流の box AP の関係。** 「工程モデルの accuracy が何 % なら検出器の条件付けが正になる／負になる」という用量反応型の解析は確認できなかった。ToolSeg は予測と正解の二点の比較を持つが、工程の confidence を連続的に劣化・較正させた掃引ではない
6. **在否の指標の差から box mAP の差を予測する定量式。** フレーム単位の在否の AP／F1 の改善量と COCO 型の box AP の改善量の一意な変換や、同じデータでの大規模な経験的対応は見つからなかった。既存の証拠はむしろ localization の誤りのため両者が乖離しうることを示す（B-26、B-16）
7. **EgoSurgery で過去のみの時間文脈と工程の文脈を同時に統制して比べる研究。** 一般映像では過去のみの LongShortNet／StreamYOLO があり、手術では工程の情報を使う ToolSeg があるが、同じ手術の検出器で「現在のみ、過去の視覚文脈、工程の予測、両方」を並べた実験は確認できなかった
8. **直近 2 年の主要会議・論文誌で、文脈で条件付けた検出の独立の否定的な再現を多数集めること。** 明確な独立の再現として Kim ほか 2021（B-28）は確認できたが、2024–2026 の MICCAI／IPCAI／CVPR／ICCV／ECCV／NeurIPS／ICLR／MedIA／TMI から、外部の task／工程の文脈を検出器に入れたが改善しなかったという査読済みの否定的な結果を複数確認することはできなかった。報告は、出版の偏りを考えると見つからないこと自体から効果を肯定してはいけないと書いている

### 11.2 旧地図 B（2026-09-16）の「見つからなかったもの」

旧地図の記載を原文のまま移した（検索日の記録は無い）。

- 凍結 P と凍結 D の間だけを学習する手術映像の研究
- DETR の object query を手術工程で条件付けする研究、phase 条件付きの anchor／class logit
- 予測 phase と phase 確率分布を同一検出器で直接比べた研究
- 正解 phase の oracle と予測 phase を box-level tool mAP で並べた研究
- 同一 frozen DETR で add／concat、FiLM、cross-attention、query 条件付け、class-logit prior を同一パラメータ予算で比べた研究
- EPIC／Ego4D で行動ラベル→box 検出の方向（見つかったのは逆方向ばかり）

旧地図の注記: 「報告が除外した種: Conditional DETR は外部文脈の条件付けではなく decoder 内部の空間条件付けであるため採用していない」。B2 は Conditional DETR を同じ但し書き付きで行にした（B-21）。

---

## 12. 未検証の組み合わせ（報告 L373–L393）

報告の文献を並べたとき、対応する測定を確認できなかった条件の交差。新規性の主張ではない（報告の定義）。

1. **EgoSurgery × 予測した online の工程 × bbox の mAP。** EgoSurgery-Tool は box AP を持ち、EgoSurgery-Phase は工程認識を持つが、二つを予測の時点で接続した測定は確認できなかった
2. **凍結した DETR × 凍結した P × 界面だけの学習。** 言語に接地した検出器は検出器自身を条件付きで学習し、ToolSeg は分割モデルを工程の条件付け込みで学習し、LAB-Det は凍結した検出器だが界面を学習しない。三者の交差に当たる測定は確認できなかった
3. **同じ予測工程に対する logit の bias と FiLM の一要因の比較。** FiLM 系と logit／文脈の再スコアの系は別々に存在するが、同じ検出器の checkpoint を凍結して両者を比べた文献は確認できなかった
4. **同じ予測工程に対する query の条件付け。** Grounding DINO／CoTDet はテキスト・affordance の知識で query を条件付けるが、工程の確率ベクトルを DETR の query に注入した統制された比較は確認できなかった
5. **予測工程と正解工程の差を、bbox の AP、在否、クラス別の AP の三つで同時に測る実験。** ToolSeg は oracle gap と術具ごとの分割の score を持つが、box AP と在否を同時には持たない
6. **稀少なクラスと混同しやすいクラスを分けた文脈の利得の分析。** ToolSeg は sample 数と術具ごとの score を提供し、EgoSurgery-Tool は混同を報告するが、頻度と視覚的な混同を別の説明変数として文脈の利得に回帰する解析は確認できなかった
7. **文脈の分布の変化を意図的に作る stress test。** Singh ほかは一般の認識で文脈外を扱うが、手術の工程と術具の組について「train の折りでは強く共起し、test の折りでは共起が崩れる」部分集合を作って検出の AP を測った研究は確認できなかった
8. **過去の視覚の memory と予測工程を独立の要因として交差させる実験。** LongShortNet は causal な視覚の履歴、ToolSeg は工程の文脈を測るが、両者の 2×2 の要因比較は確認できなかった
9. **文脈が box の回帰そのものを変える場合と、class の score だけを変える場合の分離。** Barnea & Ben-Shahar の分析から class・文脈の再スコアには localization の上限があるが、工程の文脈を box 回帰の枝にも入れた場合との同条件の比較は確認できなかった

---

## 13. 検索記録

### 13.1 B2 の報告

**検索日:** 2026-10-18（Asia/Tokyo）。件数は、重複・二次記事を除き、一次資料で実在を確認して採用したもの。複数の方向に入る文献は重複して数える。arXiv、CVF／OpenAccess、公式の会議ページ、著者の project・repository を優先し、技術的な結論には一次資料だけを使った（報告の記載）。

| 方向 | 主な検索語・探索の軸（報告の記載） | 実在確認・採用 | 詳細記録 | 主な結果（報告の記載） |
|---|---|---|---|---|
| 1 同じデータ・設定 | EgoSurgery／EgoSurgery-Tool／EgoSurgery-Phase／egocentric open surgery tool detection phase | 3 | 3 | Phase、Tool、HTS を確認。工程 → bbox 検出器の条件付けは 0 件 |
| 2 手術一般 | phase informed tool segmentation surgery／surgical phase tool detection／cataract・MSICS phase tool | 3 以上（既所持の EndoNet・MTRCNet-CL を含む） | 1 | ToolSeg が正解・予測の工程の比較と術具ごとの否定的な結果を持つ |
| 3 一人称の非手術 | egocentric action prompt object segmentation／EPIC-KITCHENS・VISOR・VOST・VSCOS／Ego4D の state-change 系 | 4 系統を確認 | 1 | ActionVOS を本文まで確認。行動の意味信号で active な物体の選択が改善 |
| 4 一般映像 | streaming object detection past frames／temporal context video object detection／context object detection failure | 8 以上 | 6 | StreamYOLO、LongShortNet、DAMO、Barnea、Singh、独立の再現 |
| 5 機構一般 | task driven object detection／affordance detection／language conditioned DETR／frozen detector prompt adapter／query conditioning | 12 以上 | 7 | COCO-Tasks、TOIST、CoTDet、Grounding DINO、GLIP、Conditional DETR、LAB-Det など |
| 6 方法論 | small sample cross validation error／video data leakage split object detection／video-level split | 2 以上 | 1 | Varoquaux と EgoSurgery 自身の動画単位の split を重点的に確認 |
| 7 否定的な結果 | context hurts object detection／context bias reproduction／予測工程のクラス別の悪化／事前学習の domain gap | 6 | 5 | ToolSeg のクラス別の悪化、EgoHands の事前学習による低下、文脈の localization の上限、文脈外の偏り、独立の再現の失敗 |

報告が書いた探し方:

- **手術・医療を検索語に入れない探索** を独立に行った（task driven object detection、affordance knowledge object detection、streaming object detection past frames、frozen detector adapter、context hurts object detection など）。方向 3〜5 は手術の語の引用網だけから抽出したものではない
- **引用の逆向きの追跡:** LongShortNet の本文が SELSA、memory の集約、QueryProp、StreamYOLO など従来の動画物体検出を比較・引用しており、offline の動画物体検出の時間の集約と streaming／causal な知覚を区別している
- **順位表・データセット起点:** EgoSurgery-Tool の公式の基準の表、COCO-Tasks とその後続の TOIST／CoTDet、Argoverse-HD の StreamYOLO → LongShortNet → DAMO-StreamNet。報告は、EgoSurgery の公式 split の既発表値と 15 動画の固定 fold の交差検証は別の評価の体制で、数値を直接同列に比べないことが必要と書いている

### 13.2 旧地図 B（2026-09-16）の検索語

旧地図の記載を原文のまま移した（検索日の記録は無い）。

- 同ドメインの検索語: surgical phase tool detection conditioning Cholec80／phase tool presence multi-task EndoNet／MTRCNet-CL correlation loss／phase information tool detector Cholec80 DETR／CholecT50 phase instrument triplet／CATARACTS／HeiChole／EgoSurgery phase tool detection／oracle／Rendezvous temporal phase tool interaction
- 一般機構の検索語: FiLM conditional dense prediction／FiLM frozen backbone segmentation／cross attention conditioning dense prediction／conditional DETR external context query conditioning／MDETR／class prior conditioned object detection／task affinity dense tasks negative transfer／Which Tasks Should Be Learned Together／Taskonomy／gradient conflict multi task dense prediction
- 隣接ドメインの検索語: scene label conditioned object detection／global scene context object detection／activity conditioned object detection egocentric／EPIC-KITCHENS action label object detection prior／Ego4D activity context object detection／video level context object detection／temporal context Faster R-CNN／Context R-CNN／SELSA EPIC Kitchens／object detection co-occurrence prior context

---

## 14. 報告者の不審点（数値の扱いに関わるもの）

報告者が原典の表に見つけ、推測で訂正せずに留保したもの。

- B-12: Table 3 で Forceps の total 6063 に対する「Dist. 1.22%」が総数と整合せず桁の誤りが疑われる。手の total の表記に「4,6320」が見える
- B-15: Table 1 の v4 の IoU は 54.32±4.4 だが、Table 3 では 54.32±34.4 と見える。本文には U-Net の DSC 52.03 とあるが、対応する表では 50.66
- B-18: 効果量は著者の project page の値で、原論文の表番号を確認できていない

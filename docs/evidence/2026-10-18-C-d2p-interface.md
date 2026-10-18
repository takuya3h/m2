# 証拠地図 C — 凍結した検出器の出力を online 工程認識へ渡す（D→P）

**版:** v2（下書き。2026-10-18、起票者が作成。v1 に R1 の行を統合）
**種類:** 探索の地図
**状態:** 書誌の機械照合は未実施。数値の原典確認は未実施。報告者の解釈と提案は 2026-10-18 に地図から外した（§0.2）
**元の報告:**
- deep research の報告「C2」（deep-research-report-C2.md、72,966 バイト、sha256 5d3c3ed514551cf11d1b75dcc8b6542b7fb5efefeedb91956a5d561284c141fd）。探索エンジンは本書に記録が無い
- deep research の報告「R1」（R1-deep-research-report.md、40,202 バイト、156 行、sha256 1f95517bf4ce63015d9574ee7e3616859021882a7014feb4f261d76d9c49dce5）。探索エンジンは本書に記録が無い
- 新規性の探索の報告「N1」（sha256 9e1dc1b7f9ad99faff469fa7aa001bfc586d98876677c52c2c1c1dcd83cfa3cd）。照合の結果は地図 N（2026-10-18-N-novelty.md）に置いた。本書には C-01・C-12・C-18・C-19 に N1 の事実を併記した

**検索日:** C2 は 2026-10-18（Asia/Tokyo。報告の記載）。R1 は報告に記載なし（「2024–2026 年を優先」とだけある。R1 L19）

---

## 0. この地図の読み方

### 0.1 問い

独立に学習して凍結した術具検出器 D の、同時刻の出力だけを、小さな学習可能な界面を通して、凍結した online（過去のみ）の工程認識器 P へ渡すと、工程認識は変わるか。対象は一人称・開放手術・少数動画（15 動画の動画単位の交差検証）。C2 は、同じ設計を手術以外の一人称映像から見直す方向（報告の方向三・四）を重点にした依頼である。報告の中の「問い二〜六」は依頼文 C2 の番号である。

R1 は同じ問いの先行の報告で、①手術映像の器具 → 工程、②一人称・物体中心の行動認識、③一般映像の物体で条件付けた行動認識、の三方向を探した（R1 L19）。R1 の「問い（1）〜（5）」は R1 の依頼文の番号である（R1 L137）。R1 は依頼文が指定した「添付の地図 A」を取得できず、照合していない（R1 L25）。

### 0.2 規則

- 行は報告に書かれた事実だけを載せる。数値・表番号は報告のまま変えていない。報告に書かれた差（pp）は起票者が検算し、C2 の 28 件、R1 の 26 件すべてが一致した
- 報告が「不明」「未確認」とした欄は不明のまま残した。報告に項目が無いものは「R1 に記載なし」と書いた。推測で埋めていない
- 現役度は C2 の値（SOTA 級／定番の基準／新興／置き換え済み／不明）。基準は依頼文の定義（直近 2 年の複数の査読論文の比較表で使われているか）で、理由も報告から写した。R1 には現役度の項目が無い
- 距離は一つの数字にしない。§3 の軸に分けた。探索の優先度には使わない。R1 は旧定義の距離 0〜3 を付けている（R1 L27）が、定義が置き換えられたため移していない
- 報告者の解釈と提案（報告の考察・設計案の節）は地図に載せず、起票者用の文書に移した（利用者の決定 2026-10-18）。各行の「報告者の一行」（§8）と、報告者の読みを含む要約の節も同じ文書へ移した
- 見つからなかったもの（§10）と未検証の組み合わせ（§11）は、その設計が新しい・価値があるという根拠として読まない。見つからない理由には、技術的な困難、価値が乏しいと見なされていること、偶然がありうる（利用者の指示 2026-10-18）
- 出所の列（§2）の「L」は C2 の行番号、「R1 L」は R1 の行番号である
- 二つの報告が同じ文献を扱うときは一行にまとめ、値の後に出所（C2／R1）を書いた
- citation の印（報告の参照記号）は除いた

### 0.3 この地図にまだ入っていないもの

- C2 が「既所持」として詳細記録を省いた文献のうち、SurgVLP は R1 にも行が無い。Digital-Twin-based Scene Representation は R1 の行から C-21 として入れた
- 種のうち STLT と SViT は C2 が同定できなかった（§10 の 7）。R1 は二つを C-23（DAIR）の Table VII の比較手法の名前として挙げるが、書誌 ID を書いていない
- R1 が名前だけ挙げ、詳細記録も書誌 ID も無い文献: MTRCNet-CL（地図 B の B-03）、LAST、LoViT、CholecT50、AutoLaparo、HeiChole、M2CAI16 workflow、EgoSurgery-Tool（地図 B の B-12）、EgoSurgery-HTS（地図 B の B-14）。行にしていない
- R1 が書誌なしで挙げた 2026 年の腹腔鏡下胃切除の研究は、書誌 ID が無いまま C-24 に置いた。引用規約により、ID が確定するまで引用として使えない

---

## 1. 系統表

| 系統 | 代表 | 現役度（報告） | 理由（報告） | 本地図の行 |
|---|---|---|---|---|
| 術具・工程の multi-task / context sharing | EndoNet、PhaKIR 2024 challenge report | EndoNet は歴史的基準。PhaKIR は新興。「tool output を phase に入れる」手法としての現役度は不明 | PhaKIR は MICCAI 2024 EndoVis を 2026 MedIA で総括した統合ベンチマーク | C-01、C-12 |
| 検出物体スコアを時系列予測へ入れる late fusion | RULSTM | 不明 | EPIC-KITCHENS の行動予測の主要な歴史的基準だが、直近 2 年の複数比較表を確認できず | C-03 |
| hand–object contact / state / graph | Ego-OMG、Forecasting Action through Contact Representations、Shiota ほか 2024 | 不明 | 系統は WACV 2024 まで継続。個々の手法の現在の順位は不明 | C-07、C-17、C-16 |
| box / trajectory を明示的に処理する物体中心の映像モデル | STIN、ORViT | 不明 | SomethingElse・SSv2・EK100 で確立した系統だが、2024–2026 の同条件の順位表を本文確認できず | C-04、C-05 |
| 物体を意識した補助教師・表現学習 | Helping Hands、Tateno ほか 2026 | Helping Hands は不明。Tateno ほかは新興（プレプリント） | Helping Hands の後も手・物体の手がかりの明示化が継続 | C-06、C-11 |
| 長期予測・次に触れる物体の予測 | Zhang ほか 2024、StillFast、VISTA | VISTA は新興（2026 の技術報告）。ほかは不明 | Ego4D 系で継続 | C-08、C-09、C-10 |
| 汎用の条件付け・小型の界面 | FiLM | 不明 | 一般的な条件付けの定番の概念。ただし独立に学習した二モデルを凍結しその間だけを学習する条件での現役度は不明 | C-15 |
| 評価・分割・否定的な証拠 | Kostiuchik ほか 2024、STIN／ORViT／Helping Hands の oracle と否定的 ablation、EndoNet | 不明 | 方法論であり順位型の現役度を当てにくい | C-13、C-04、C-05、C-06、C-01 |
| 一人称開放手術の工程認識・視線の補助表現（報告の系統表には無く、詳細記録の系統欄から起票者が足した） | EgoSurgery-Phase | 不明 | 2026 までの査読比較表を確認せず | C-02 |
| 強い視覚時間モデル（受け取り手の候補を考える隣接文献。同上） | Surgformer | 不明 | 査読の状況を確認できず | C-14、C-21（R1 で受け取り手） |

R1 の行から起票者が足した系統（R1 には系統表も現役度も無い。系統の名前は R1 の「入れ方」「信号の形」の欄から付けた）:

| 系統 | 代表 | 現役度 | 本地図の行 |
|---|---|---|---|
| 器具在否の系列を時間モデルへ入れる二段階 | Sahu ほか 2020、DeepPhase、2026 の胃切除の研究 | R1 に記載なし | C-18、C-19、C-24 |
| segmentation 由来の位置・大きさ・動き・関係の指標の融合 | Park ほか 2022 | R1 に記載なし | C-20 |
| 器具と解剖の mask・depth の構造化表現を強い受け取り手へ | Ding ほか（DTFormer） | R1 に記載なし | C-21 |
| 検出 box による token の選択と object-aware attention | ObjectViViT | R1 に記載なし | C-22 |
| 検出と相互作用推論の同時学習・中間層の融合 | DAIR | R1 に記載なし | C-23 |

報告の系統表の件数: 2、1、2、2、2、3、1、5（L9〜L16）。報告は「物体信号」が、クラス確率・box の幾何・RoI の見え・接触状態・物体の意味・物体を意識した事前学習の教師という異なるものを含み、一括りにすると混同すると書いている（L20）。§9 はこの区別で行を並べた。

---

## 2. 行の一覧

| ID | 文献 | 書誌 ID | 掲載先 | 方向 | 読んだ範囲 | 出所 |
|---|---|---|---|---|---|---|
| C-01 | Twinanda ほか, EndoNet: A Deep Architecture for Recognition Tasks on Laparoscopic Videos（C2 は既所持として Fig. 10 と GTBin の比較だけを検証。R1 は Table III・IV(a) の詳細記録あり） | arXiv 1602.03012、DOI 10.1109/TMI.2016.2593957（DOI は C2） | IEEE TMI（C2） | C2 は記載なし（検索記録の方向七に名前がある。L475）。R1 ① | C2: Fig. 10、HHMM の前後の工程の比較表。R1: Table III、Table IV(a)、Fig. 10 | L26–L43、R1 L5、L13、L33、L41–L43、L86、N1 L30、L52 |
| C-02 | Ryo Fujii, Masashi Hatano, Hideo Saito, Hiroki Kajita 2024, EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos | arXiv 2405.19644 | MICCAI 2024（early accept、査読） | 一 | 要旨と arXiv の書誌。数値表は未確認 | L48–L74、R1 L15、L110 |
| C-03 | Antonino Furnari, Giovanni Maria Farinella 2020–2021, Rolling-Unrolling LSTMs for Action Anticipation from First-Person Video | arXiv 2005.02190、DOI 10.1109/TPAMI.2020.2992889 | IEEE TPAMI（査読） | 三・問い二 | 本文 | L76–L102 |
| C-04 | Joanna Materzynska ほか 2020, Something-Else: Compositional Action Recognition with Spatial-Temporal Interaction Networks（STIN） | arXiv 1912.09930 | CVPR 2020（査読） | 四・七 | 本文 | L104–L130 |
| C-05 | Roei Herzig ほか 2022, Object-Region Video Transformers（ORViT） | arXiv 2110.06915 | 報告の記載は「ECCV 2022 系、査読つき」 | 三・四・七 | 本文・補遺に当たる HTML | L132–L159 |
| C-06 | （著者は報告に記載なし）2023, Helping Hands: An Object-Aware Ego-Centric Video Recognition Model | arXiv 2308.07918 | ICCV 2023（査読） | 三・四・七 | 本文 | L161–L189 |
| C-07 | Eadom Dessalene ほか 2020, Egocentric Object Manipulation Graphs（Ego-OMG） | arXiv 2006.03201 | プレプリント | 三・問い二 | 本文 | L191–L217 |
| C-08 | Ce Zhang ほか 2024, Object-centric Video Representation for Long-term Action Anticipation | arXiv 2311.00180 | WACV 2024（査読） | 三 | 要旨のみ | L219–L239 |
| C-09 | Francesco Ragusa, Giovanni Maria Farinella, Antonino Furnari 2023, StillFast: An End-to-End Approach for Short-Term Object Interaction Anticipation | arXiv 2304.03959 | CVPR 2023（査読） | 三・問い二の隣接 | 要旨と結論 | L241–L261 |
| C-10 | Qiaohui Chu ほか 2026, VISTA: Technical Report for the Ego4D Short-Term Object Interaction Anticipation at EgoVis 2026 | arXiv 2605.20901 | 技術報告・プレプリント | 三・五 | 要旨のみ | L263–L283 |
| C-11 | Masatoshi Tateno, Alexandros Stergiou, Risa Shinoda, Yoichi Sato, Dima Damen 2026, Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues? | arXiv 2607.08514 | プレプリント（MIRU 2026 発表） | 三・七 | 要旨 | L285–L309 |
| C-12 | Tobias Rueckert ほか 2026, Comparative validation of surgical phase recognition, instrument keypoint estimation, and instrument instance segmentation in endoscopy: Results of the PhaKIR 2024 challenge | arXiv 2507.16559、DOI 10.1016/j.media.2026.103945 | Medical Image Analysis（査読） | 二・六 | 要旨・書誌 | L311–L331、R1 L19。データセットの論文（arXiv 2511.06549）は別の論文で、N1 が挙げる（地図 N §8） |
| C-13 | Kostiuchik ほか 2024, Surgical phase and instrument recognition: how to identify appropriate dataset splits（行の書誌欄に著者なし。著者名は系統表 L16 から） | DOI 10.1007/s11548-024-03063-9 | IJCARS（査読） | 六・七 | 本文 | L333–L356 |
| C-14 | Shu Yang, Luyang Luo, Qiong Wang, Hao Chen 2024, Surgformer: Surgical Transformer with Hierarchical Temporal Attention for Surgical Phase Recognition | arXiv 2408.03867 | プレプリント（査読の採択先は報告では不明） | 二（隣接） | 要旨 | L358–L375、R1 L11、L37、L93 |
| C-15 | Ethan Perez ほか 2018, FiLM: Visual Reasoning with a General Conditioning Layer | arXiv 1709.07871 | 報告の記載は「査読系論文」 | 五 | 要旨 | L377–L392 |
| C-16 | Shiota ほか 2024（題名は報告に無い） | DOI 10.1109/WACV57701.2024.00641 | WACV 2024 | 三 | 詳細記録なし | L11、L203 |
| C-17 | Dessalene ほか, Forecasting Action through Contact Representations from First Person Video | arXiv 2102.00649 | 報告に掲載先の記載なし（L213 は「後続 TPAMI 論文」と書く） | 三 | 要旨 | L193–L198、L213 |
| C-18 | Sahu, Szengel, Mukhopadhyay, Zachow 2020, Surgical phase recognition by learning phase transitions | DOI 10.1515/cdbme-2020-0037 | Current Directions in Biomedical Engineering 6(1)（N1） | R1 ① | R1 に読んだ範囲の列なし（R1 L23 は「数値は本文・表・図で直接確認したものだけ」と書く）。Table 1 の値あり | R1 L34、L43、L71、L131、N1 L17、L49 |
| C-19 | Zisimopoulos, Flouty, Luengo, Giataganas, Nehme, Chow, Stoyanov 2018, DeepPhase: Surgical Phase Recognition in CATARACTS Videos | arXiv 1807.10565、DOI 10.1007/978-3-030-00937-3_31 | R1 に記載なし | R1 ① | 同上。Table 1 の値あり | R1 L7、L23、L35、L45、L75、L104、L149、N1 L18、L50、L145 |
| C-20 | Park, Chi, Park, Lee, Park, Hyung, Choi 2022, Visual Modalities Based Multimodal Fusion for Surgical Phase Recognition | DOI 10.1007/978-3-031-18814-5_2 | R1 に記載なし | R1 ① | 同上。Table 2・4 の値あり | R1 L9、L36、L47、L73 |
| C-21 | Ding ほか 2024–2025, Towards Robust Algorithms for Surgical Phase Recognition via Digital Twin-based Scene Representation（DTFormer。C2 は既所持として行を作らなかった） | arXiv 2410.20026 | R1 に記載なし | R1 ① | 同上。Table 2・3 の値あり | R1 L11、L37、L77、L93、L129、L133 |
| C-22 | Zhou, Arnab, Sun, Schmid 2023, How Can Objects Help Action Recognition?（ObjectViViT） | arXiv 2306.11726 | R1 に記載なし | R1 ②③ | 同上。Fig. 5・Table 2 の値あり | R1 L13、L55、L58–L60、L102 |
| C-23 | Li, Sun, Liu, Duan, Li 2025（arXiv 2024）, Simultaneous Detection and Interaction Reasoning for Object-Centric Action Recognition（DAIR） | arXiv 2404.11903、DOI 10.1109/TMM.2025.3543033 | R1 に記載なし | R1 ③ | 同上。Table I・VI・VII の値あり | R1 L13、L56、L62–L66、L103 |
| C-24 | （著者・題名・書誌 ID は R1 に無い）2026, 腹腔鏡下胃切除 93 例で YOLOv8 の器具在否の予測を双方向 LSTM へ渡す二段階のシステム | なし | R1 に記載なし | R1 ① | 同上。Table 4 の値あり | R1 L49 |

---

## 3. 近さ（距離の軸）

| ID | 視点 | ドメイン | 課題の形 | 推論の規約 | データ規模 | モデルの状態（凍結の範囲） |
|---|---|---|---|---|---|---|
| C-01 | 腹腔鏡（題名） | 低侵襲手術 | 器具在否と工程の共有表現（multi-task）。工程の系は CNN 特徴の上に SVM を置き、評価側で交差検証する構成を含む。R1: 7 クラスの器具在否の confidence を視覚の fc 特徴に連結して SVM、さらに HHMM。GTbin では 7 次元の正解の二値を同じ位置に入れる（R1 L33） | Fig. 10 の値は HHMM の前の工程 accuracy と一致する（C2 の照合。caption に「HHMM なし」とは書かれていない）。R1 は online と offline の両方の報告があるとし、Table IV(a) を online の値として引く | Cholec80。CNN の fine-tune に使う動画を 10／20／30／40 本に変え、評価側は固定 | 共同学習。凍結＋界面ではない（R1 L43 も、D と P を独立に学習したモデルではなく multi-task と書く） |
| C-02 | 一人称（頭部装着カメラ） | 開放手術 | 工程認識。視線も提供し、GGMAE は視線を事前学習のマスクの事前分布に使う | 要旨では online／offline の因果の規約は不明 | 約 15 時間、9 工程。動画本数は報告が確認した要旨に記載なし | GGMAE と工程モデル。独立に学習した D と P を凍結し界面だけを学習する形ではない |
| C-03 | 一人称 | 非医療（調理） | 行動の予測。RGB・optical flow・物体の三枝を RU-LSTM で処理し、modality attention で統合。物体の表現は検出 confidence をクラスごとに和した bag of objects で、box の位置は捨てる | 未来フレームを入力せず観測済みの区間だけを使う | EPIC-KITCHENS、EGTEA Gaze+（全動画数は報告が不明扱い） | 検出器は Faster R-CNN／ResNet-101。EPIC では対象の物体クラスで学習し、特徴は事前計算して固定。RU-LSTM の枝は下流で学習する（両側の凍結より緩い） |
| C-04 | 三人称・一般映像 | 非医療 | Faster R-CNN で手と操作物体を二クラス検出し、追跡した box 座標と物体 ID の埋め込みを時空間の相互作用モデルへ入れて行動認識 | clip の center crop を使う offline 分類 | Something-Else compositional、174 行動クラス | 検出器は COCO 事前学習の後に行動の train split の box 注釈で独立に fine-tune。STIN は別に学習。P は凍結されない |
| C-05 | EK100 は一人称、ほかは一般映像 | 非医療 | 検出・追跡の box を、video transformer の途中層へ物体領域の見えと軌跡の動きとして繰り返し注入 | 標準の行動認識は clip ベースの offline | EK100: 一人称 700 本、名詞 300・動詞 97 クラス。SomethingElse compositional: train 54,919／validation 54,876 clips、174 クラス | 検出器と映像モデルに重みの共有はない。video transformer と ORViT block は fine-tune する |
| C-06 | 一人称 | 非医療 | 100DOH 手物体検出器の疑似 box と、動画の字幕・物体語を学習時の教師に使い、物体を意識した decoder を足した一人称の映像言語表現を学習。推論時に外部検出器の出力を P へ渡す方式ではない | clip 表現学習・zero-shot 認識 | EGTEA: 28 時間、86 セッション、32 人、106 クラス。ほかに EgoClip／Ego4D、EK100、VISOR など | 計算資源の制約で視覚 backbone を解凍して end-to-end に学習できなかったと著者が明記。強い事前学習済み backbone を固定したまま物体の側を学習する |
| C-07 | 一人称 | 非医療（調理） | 手物体の接触で動画を操作の状態に分け、状態の遷移を graph として長期の時間文脈に使い将来の行動を予測 | 観測済みの過去から将来を予測する causal な課題 | EPIC-KITCHENS 系（動画本数は報告が不明扱い） | 見えの CSN と接触 graph の枝を別に作って融合。二つの凍結モデル＋界面ではない |
| C-08 | Ego4D・EGTEA は一人称、50Salads は三人称 | 非医療 | 汎用の視覚言語事前学習モデルから object prompt で課題に合わせた物体中心の表現を取り出し、Transformer が時間スケールごとに必要な物体を引いて将来の行動を予測 | 観測部分のみを入力 | Ego4D、50Salads、EGTEA Gaze+（規模は要旨では不明） | 領域内の教師つき検出器を前提にしない。凍結の範囲は本文未確認 |
| C-09 | 一人称 | 非医療 | 最後の高解像度の静止画と過去の clip を同時に処理し、次に触れる物体の box・名詞・将来の動詞・接触までの時間を予測 | 観測済みの映像から将来の接触を予測 | Ego4D（本数は不明） | end-to-end。独立に凍結した検出器の出力を時間モデルへ渡す構造ではない |
| C-10 | 一人称 | 非医療 | COCO 事前学習の Faster R-CNN R50-FPN が最後の高解像度フレームから proposal を出し、凍結した V-JEPA 2.1 の時間枝が過去 clip の文脈を取り、feature modulation と RoI 単位の融合で検出経路へ注入。将来の box・名詞・動詞・接触までの時間・confidence を予測 | 過去のみ | Ego4D STA（詳細は不明） | V-JEPA 2.1 の時間枝は凍結と明記。Faster R-CNN の全体が凍結かは要旨では不明 |
| C-11 | 一人称 | 非医療 | 手の手がかりと物体の手がかりを分けた評価（CI-HOI／DEHOI）を作り、映像言語モデルが手の操作・物体の変化・文脈のどこに依存するかを診断。hand-object masked training と HOI-dynamics-aware decoder を提案 | 不明 | 要旨では不明 | 事前学習済みの映像言語モデルが対象。全体を凍結する条件かは要旨では不明 |
| C-12 | 内視鏡・腹腔鏡 | 低侵襲手術 | 工程認識・器具キーポイント推定・器具インスタンス分割を同じ動画で評価できる multi-task のベンチマーク | 手術全体の時間情報を扱える設計。各工程手法が causal online かは要旨では不明 | 腹腔鏡下胆嚢摘出術の全長動画 13 本、3 施設 | 参加手法ごとに異なり、一括で判定できない |
| C-13 | 腹腔鏡 | 低侵襲手術 | Cholec80 の工程・器具認識で、train／validation／test の動画分割そのものが workflow・工程・器具の分布をどう変えるかの分析 | 特定のモデルの online／offline の比較ではない（評価の方法論） | Cholec80 | 該当なし |
| C-14 | 内視鏡・腹腔鏡 | 低侵襲手術 | 疎なフレームと階層的な時間 attention による工程認識 | C2: target-frame-centric の時間文脈とあるが、未来フレームを含むかは要旨では不明。R1 は「online Surgformer」と書く（R1 L11、L37） | 二つのベンチマークとだけ記載 | end-to-end の手術 transformer。凍結＋界面ではない |
| C-15 | 該当なし | 非医療 | 条件の信号から特徴ごとの affine パラメータを生成し、受け取り手の特徴を scale／shift する | 時間因果の条件とは無関係 | CLEVR など | 独立の二モデルを凍結して界面だけを学習することを検証した論文ではない |
| C-16 | 不明 | 不明 | 手物体の接触・物体の状態の系（WACV 2024） | 不明 | 不明 | 不明 |
| C-17 | 一人称 | 非医療 | 接触の予測を拡張し、Contact Anticipation Maps と Next Active Object Segmentation を導入 | 観測済みの過去から将来を予測 | EPIC-Kitchens の部分集合に手・物体の分割と接触までの時間の注釈を追加 | 不明 |
| C-18 | R1 に記載なし | 手術 | ZIBNet が出す器具在否のラベルの系列を、state-preserving many-to-one LSTM に逐次入れて工程を認識。下流で RGB を使わない（R1 L43） | online の工程検出として構成（R1）。N1 は「no future information was used」を引く | Cholec80（本数は R1 に記載なし） | 二段階（ZIBNet → LSTM）。凍結の範囲は R1 に記載なし。N1 も ZIBNet を凍結したかは不明とする（本文を取得できず要旨のみ） |
| C-19 | R1 に記載なし | 手術 | 21 クラスの二値の器具在否（R1 は正解とする〔R1 L23〕。N1 は §2.3 の原文「tool binary presence from the output classification layer」を引き、分類層の出力〔予測〕とする〔補助調査による〕。食い違い）と、ResNet-152 の学習済みの器具特徴を、100 フレームの系列として 2 層の LSTM／GRU へ | 100 フレームの sliding window。未来を使わない厳密な online-causal の評価は明記なし（R1） | CATARACTS（外部の test） | 器具の CNN → 時間モデルの二段階。凍結の範囲は R1 に記載なし |
| C-20 | R1 に記載なし | 手術（PETRAW、実手術の G40 胃切除。R1 L9） | semantic segmentation から bbox・重心・大きさ・速度・器具どうし／器具と臓器の関係を計算した指標（VKI）を Bi-LSTM、RGB を SlowFast50 で処理し、linear または convolutional の特徴融合 | offline（Bi-LSTM、clip の処理。R1） | PETRAW、G40（本数は R1 に記載なし） | segmentation が予測か正解かは R1 に記載なし。凍結の範囲は R1 に記載なし |
| C-21 | R1 に記載なし | 手術（Cholec80、Cholec80-C、CRCD、RT） | SAM2 由来の instance mask（器具＋解剖）と DepthAnything の depth を token にし、mask は早い段で CLS に、depth は後段で加算。受け取り手は Surgformer。DTFormer は mask＋depth の構造化表現だけを使う（R1 L11）。DT-Aug は RGB 特徴の補助 | online（R1） | 本数は R1 に記載なし | 凍結の範囲は R1 に記載なし。R1 は「純粋な tool detector output ではなく、器具・解剖構造の mask と depth を含むため間接証拠」と書く（L11） |
| C-22 | R1 は「一人称・一般映像」の表に置く | 非医療 | 既製の検出器の bbox・object heatmap・track identity で token を選び（OGS）、object-aware attention（OAM）で処理。物体の領域を残し、背景の token を一部保持 | clip ベースの offline（R1） | Something-Else、Something-Something V2、EPIC-KITCHENS | 検出器は既製（off-the-shelf）。受け取り手は ViViT／VideoMAE 系 transformer。凍結の範囲は R1 に記載なし |
| C-23 | R1 は「一人称・一般映像」の表に置く | 非医療 | 物体 proposal の bbox・見え、interactive score を PatchDec → 相互作用する物体の refinement／aggregation で物体の表現にし、video patch token と連結して joint self-attention・関係のモデル化 | 16 フレームの clip、offline（R1） | Something-Else、IKEA-Assembly | 受け取り手は MViTv2。検出を multi-task で同時に学習する（R1 L56、L125 は D／P の表現が joint training で変わる例に入れる） |
| C-24 | R1 に記載なし | 手術（腹腔鏡下胃切除） | YOLOv8 の器具在否の予測を Cholec80 型の二値の系列に変え、bidirectional LSTM へ | bidirectional（R1 の記載）。online かは R1 に記載なし | 93 例 | 二段階。凍結の範囲は R1 に記載なし |

---

## 4. 手法の位置

| ID | 系統 | 現役度（報告）と理由 | どのベンチマークの話か | 本研究の条件で測られたか（少数動画／online／一人称） |
|---|---|---|---|---|
| C-01 | multi-task／context sharing | 歴史的基準（報告の語）。「tool output を phase に入れる」手法としては不明 | Cholec80 | 少数動画: 10〜40 本の掃引あり（ただし CNN の fine-tune の本数）。online: Fig. 10 は HHMM の前の値と照合された。一人称: 該当しない |
| C-02 | 一人称開放手術の工程認識／視線の補助表現 | 不明（2026 までの査読比較表を確認していない） | EgoSurgery-Phase | 一人称: 該当。少数動画: 依頼の設定には該当するが本文の動画本数を再確認できず。online: 不明 |
| C-03 | 検出 confidence の時間的な late fusion | 不明（直近 2 年の複数の査読論文の比較表を確認できず） | EPIC-KITCHENS、EGTEA Gaze+ | 一人称・causal: 該当。少数動画: 該当しない |
| C-04 | 手物体の幾何・軌跡の推論 | 不明（ORViT が後に同ベンチマークで比較しているが、2024–26 の比較表を確認していない） | Something-Else compositional split | いずれも該当しない |
| C-05 | 物体領域の条件付け・軌跡の注入 | 不明（2024–26 の同条件の査読比較表を確認していない） | SomethingElse、SSv2、EK100、Diving48、AVA | 一人称: EK100 のみ。少数動画・online: 該当しない |
| C-06 | 物体を意識した補助教師 | 不明（2026 までの同ベンチマークの比較表を追い切れていない） | EgoMCQ、EK100-MIR、EGTEA、VISOR、EgoNLQ／EgoMQ | 一人称: 該当。少数動画・online: 該当しない |
| C-07 | 接触状態・意味の graph | 不明（WACV 2024 の接触・物体状態の系に発想が継続しているが Ego-OMG 自体の順位は不明） | EPIC-KITCHENS | 一人称・causal: 該当。少数動画: 該当しない |
| C-08 | object prompt／長期予測 | 不明（2024 の査読論文だが 2026 までの複数比較表を本文確認できず） | Ego4D、50Salads、EGTEA Gaze+ | 予測・一人称のベンチマークを含むが、フレーム単位の online の工程ラベル付けとは異なる |
| C-09 | 次に触れる物体の予測 | 不明（2026 の VISTA が StillFast 型の設計を明示的に採るので設計の系譜は継続。直近 2 年の複数の査読表を満たすかは確認不足） | Ego4D STA | 一人称・causal: 該当。少数動画: 該当しない |
| C-10 | 強い凍結事前学習映像モデル＋物体検出器の経路の融合 | 新興（2026 のプレプリントで独立追試はまだ判断できない） | Ego4D STA | 一人称・causal: 該当。少数動画: 該当しない |
| C-11 | 手がかりの分離／否定的な診断 | 新興（2026 のプレプリント） | DEHOI ほか（要旨） | 一人称のみ明確 |
| C-12 | 手術の文脈・器具の統合ベンチマーク | 新興（MICCAI 2024 EndoVis challenge を 2026 MedIA で総括） | PhaKIR | 少数動画: 該当（13 本）。一人称: 該当しない（内視鏡）。online: 不明 |
| C-13 | 分割の監査・漏れと分布の監査 | 不明（方法論の論文で順位の分類は当てにくい） | Cholec80 | 少数動画の分割の問題という意味で近い |
| C-14 | 強い視覚時間の受け取り手 | 不明（査読の状況を確認できず） | 二つのベンチマーク（名称は報告に無い） | 不明 |
| C-15 | 小型の条件付け・gating の界面 | 不明（一般の概念として確立しているが、依頼の基準では判定できず） | CLEVR など | 該当しない |
| C-16 | 接触・物体状態 | 不明 | 不明 | 不明 |
| C-17 | 接触の予測 | 不明 | EPIC-Kitchens | 一人称・causal |
| C-18 | 器具在否の系列 → 時間モデル | R1 に記載なし | Cholec80 | online: 該当（R1）。少数動画・一人称: 該当しない |
| C-19 | 器具在否・器具特徴の系列 → 時間モデル | R1 に記載なし | CATARACTS | online: 明記なし。少数動画・一人称: 該当しない |
| C-20 | segmentation 由来の指標と RGB の融合 | R1 に記載なし | PETRAW、G40 | online: 該当しない（Bi-LSTM）。一人称: 該当しない |
| C-21 | 構造化表現を強い受け取り手へ | R1 に記載なし | Cholec80、Cholec80-C、CRCD、RT | online: 該当（R1）。受け取り手は強い手術の工程モデル。一人称: 該当しない |
| C-22 | 物体 box による token の選択・attention | R1 に記載なし | Something-Else、SSv2、EPIC-KITCHENS | いずれも該当しない（offline） |
| C-23 | 検出と相互作用推論の同時学習・中間層の融合 | R1 に記載なし | Something-Else、IKEA-Assembly | いずれも該当しない（offline） |
| C-24 | 検出器の在否 → 時間モデル | R1 に記載なし | 腹腔鏡下胃切除 93 例 | online: R1 に記載なし（双方向 LSTM。R1 L131 は C-20 の Bi-LSTM について未来の情報を使うと書く） |

---

## 5. 証拠の質

| ID | 何と何を比べた差か | その要素だけを変えた比較か | 基準の強さ | seed・分割・検定 | 著者以外の追試・採用 |
|---|---|---|---|---|---|
| C-01 | multi-task の EndoNet と single-task の ToolNet／PhaseNet。GTBin は EndoNet の表現に正解の二値の器具在否を足したもの | Fig. 10 は学習動画数を変えると検出器と共有表現が同時に変わり、器具の Mean AP と工程の利得の因果を切り分けた実験ではない（C2）。R1 は予測の confidence を同じ形の正解の二値に置き換えた比較を「oracle あり、明示的」と分類する（R1 L33） | 当時の single-task 網 | 不明 | 不明 |
| C-02 | GGMAE と previous SOTA、通常の MAE 系手法 | 本文の表を未確認のため不明 | 要旨では previous SOTA。具体の手法・表は未確認 | 不明 | 確認できず |
| C-03 | RGB／flow／物体の各 modality とその融合 | modality ablation は比較的近いが、融合構造の学習も含む | 当時の行動予測ベンチマーク用のモデル | 統計検定の記載は確認できず | 後続の一人称予測で広く参照されるが、2024–26 の複数の比較表までは確認していない |
| C-04 | 同じ STIN+OIE+NL に正解 box と検出 box を入れた結果（Table 3(a)／(b)） | 正解と検出の STIN どうしはかなり直接的。ただし検出→正解で追跡の質も同時に変わりうる | I3D（見えの基準）、STRG とも比較 | seed 数・検定は不明 | ORViT（C-05）が STIN を物体中心の基準として再実装・比較 |
| C-05 | EK100 Table 3(c) で同じ強い MF-HR に物体中心のモジュールを足す。Table 4 で層・box を変える | Table 4 の層・box の ablation は比較的明確。Table 3 の他手法との比較は構造も変わる | MF、MF-L、MF-HR（強い transformer の受け取り手） | 統計検定は確認できず | STIN などを自ら再比較。2024–26 の独立追試は本文確認できず |
| C-06 | Table 1 の同じ構造で、通常の L_Ego だけと、box＋語の物体教師を足したもの | Table 1 は比較的明確。Table 4 の SOTA 比較は batch size・hard negative の選び方・decoder などが混ざり、物体信号だけの効果としない | LaViLa TSF-L など、大規模な一人称事前学習をした強い映像言語モデル（Table 4） | 統計検定は確認できず | 系統は 2026 の手物体の手がかりの分析（C-11）へ継続。Helping Hands 自体の独立再現の数は不明 |
| C-07 | Table 2 で見えのみの CSN、graph のみの GCN、融合 | graph の枝の追加が主な変更。小型界面だけの変更とは異なる | 当時の CSN の見えの枝 | 複数 run の記述はあるが seed 数を報告が再確認できず不明 | 接触中心の予測が後続の TPAMI 論文と WACV 2024 系へ継続 |
| C-08 | 不明（要旨のみ） | 不明 | 不明 | 不明 | 不明 |
| C-09 | 要旨は 2022 challenge の公開順位表で 1 位と記載。表単位の数値は未確認 | 不明 | 不明 | 不明 | VISTA（C-10）が StillFast 型の設計を採用 |
| C-10 | 要旨は公式 challenge server で 1 位と記載。融合なしとの ablation の数値は本文未確認 | 不明 | 不明 | 不明 | 2026 のため判断できない |
| C-11 | 手のみ・物体のみに近い手がかり分離の観測と、標準の観測 | 手がかり分離の評価そのものが切り分けの設計 | 事前学習済みの映像言語モデル | 不明 | 2026 のため不明 |
| C-12 | 報告は 14 表の数値を転記していない | 不明 | 該当なし | challenge は BIAS ガイドラインに沿うと明記。詳細は未転記 | 該当なし |
| C-13 | Cholec80 の慣用の split を、工程・器具の存在・分布・workflow の変動の観点で比較 | 該当なし（方法論） | 該当なし | モデルの seed の問題ではない | 追跡していない |
| C-14 | 本文の表を未確認 | 不明 | 不明 | 不明 | 不明 |
| C-15 | 本文未確認 | 本文未確認 | 不明 | 本文未確認 | 不明 |
| C-16 | 詳細記録なし | 不明 | 不明 | 不明 | 不明 |
| C-17 | 要旨のみ | 不明 | 不明 | 不明 | 不明 |
| C-18 | EndoNet+HHMM と提案法 | 受け取り手の構造も異なるため純粋な界面の ablation ではない（R1 L34）。同じ LSTM＋RGB の phase-only の対照が無く、+8.1 pp を検出器の界面の因果的な利得と読めない（R1 L43） | EndoNet+HHMM | R1 に記載なし | R1 に記載なし |
| C-19 | 同じ LSTM／GRU で、二値の在否と学習済みの器具特徴 | 時間モデルを固定して信号を変えた比較。R1 は二値を正解、特徴を予測の内部表現とし、厳密な予測→正解の置換と分類しない（R1 L23、L104）。N1 は二値も分類層の出力（予測）とし、予測の二値と予測の特徴の比較と書く（N1 L50） | R1 に記載なし | CATARACTS の外部の test。seed・検定は R1 に記載なし | R1 に記載なし |
| C-20 | RGB のみの SlowFast50 と RGB+VKI（linear／convolutional の融合）、VKI のみ（Table 4）。Table 2 は各種の運動・関係の指標に bbox を足す | 融合の方式の比較あり | RGB のみの SlowFast50 | R1 に記載なし | R1 に記載なし |
| C-21 | Surgformer と DTFormer（mask＋depth のみ）、DT-Aug（Table 2・3） | 信号と表現の両方が変わる（R1 L154）。純粋な検出器の出力ではない（R1 L11） | Surgformer（強い online の手術の工程モデル） | clean と corrupted・OOD の評価。seed・検定は R1 に記載なし | R1 に記載なし |
| C-22 | VideoMAE の基準、予測 box、正解 box（Table 2）。full-token の OAM（Fig. 5） | 予測 box → 正解 box は同じ構造での置き換え | VideoMAE 系 | R1 に記載なし | R1 に記載なし |
| C-23 | MViTv2 の基準 → 検出の multi-task → IRA（Table I）。融合する層（Table VI）。検出 box → 正解の個数 → 正解の対応（Table VII） | 層の ablation は同じ構造の中での変更。Table VII は同じ MViT 系の基準とともに、検出 box を使う STIN（再実装）・STLT・SViT と比べる（R1 L64） | MViTv2 | R1 に記載なし | Something-Else で STIN を、IKEA-Assembly で STRG・STIN を再実装して比較（R1 L64、L66） |
| C-24 | 報告された値は一つの構成だけ | 器具の入力なしの基準も正解の器具の oracle も無い（R1 L49） | 該当なし | R1 に記載なし | R1 に記載なし |

---

## 6. 効果（数値は報告のまま。指標名は原文）

| ID | 指標・値・表番号 | 符号 | 符号や大きさが変わる条件 |
|---|---|---|---|
| C-01 | Fig. 10。器具の Mean AP（ToolNet → EndoNet）: 10 本 65.9 → 62.0（−3.9 pp）、20 本 70.9 → 67.5（−3.4）、30 本 73.6 → 77.5（+3.9）、40 本 80.9 → 81.0（+0.1）。工程の Mean Accuracy（PhaseNet → EndoNet）: 10 本 65.9 → 65.8（−0.1）、20 本 68.2 → 70.8（+2.6）、30 本 72.1 → 72.5（+0.4）、40 本 73.0 → 75.2（+2.2）。GTBin: HHMM の前 EndoNet 75.2 → EndoNet+GTBin 75.3（+0.1 pp）、HHMM の後 81.7 → 81.9（+0.2 pp）（C2 は表番号を書いていない）。R1: Table III で PhaseNet 73.0 → EndoNet 75.2（+2.2 pp）、GTbin 75.3。Table IV(a)（online、HHMM の後）で 78.8 → 81.7（+2.9）、GTbin 81.9。予測 → 正解は +0.1／+0.2 pp。Fig. 10 の 10 本で PhaseNet 65.9 → EndoNet 65.8（−0.1 pp）。N1（§IV-C、表 III–IV。補助調査による）: 術具の正解の二値だけを入力にすると HMM の前 48.2%、HMM の後 offline 69.2%、online 47.5%。EndoNet の特徴では 75.2%、92.0%、81.7%。EndoNet-GTbin では 75.3%、92.2%、81.9%（地図 N §3） | 器具の側は 10・20 本で負、30 本で正に反転。工程の側は 10 本でほぼ零、20 本以上で正。GTBin は零に近い（R1 の判定: 否定的結果「はい（部分条件）」） | 学習動画数。Fig. 10 の本数は CNN の fine-tune に使う手術動画数で、工程の分類器の全体をその本数だけで学習した意味ではない（L39） |
| C-02 | 要旨: Jaccard で previous SOTA に +6.4 pp、MAE 系手法に +3.1 pp。報告は表番号を本文確認できないため主要な数値証拠に採用していない | 改善 | 不明 |
| C-03 | 物体の枝の寄与の表は確認したが、取得した本文の断片では比較の行を誤って同定する危険があり、報告は数値を不明とした | 物体情報は総じて補完的だが常に大きいわけではない | modality attention は見えだけで足りる場面で物体の枝の重みを下げる。著者の failure analysis では、検出器が chair を捉えられず失敗する例、pan の検出が誤った将来の行動を誘発する例が示される |
| C-04 | Table 3: compositional top-1 は正解 box 51.4%、検出 box 37.2%（−14.2 pp）。top-5 は 79.3% と 62.4%（−16.9 pp）。R1: C-23 の Table VII で、同じ MViT 系の基準 63.3% に対し、検出 box の再実装 STIN は 48.2%（R1 L64） | 検出 box にすると悪化 | I3D との結合: 正解 box のとき I3D 46.8% に対し joint 54.6%（+7.8 pp）、検出 box のとき 48.2%（+1.4 pp）。box の雑音が利得を圧縮する（Table 3） |
| C-05 | EK100 Table 3(c): MF-HR の action／verb／noun top-1 44.5／67.0／58.5、ORViT 45.7／68.4／58.7（+1.2／+1.4／+0.2 pp）。MF-HR+STRG の action 42.5（−2.0 pp）、+STIN 44.2（−0.3）、+STRG+STIN 44.1（−0.4）。SSv2 Table 3(a): MF 66.5、MF+STRG 66.1、MF+STIN 66.5、両方 66.6、ORViT MF 67.9（+1.4 pp）。検出器の box の ORViT は MF／MF-L をそれぞれ +1.4 pp 改善し、手作業の注釈 box（oracle）では +7.3 pp／+6.7 pp（著者の報告）。SomethingElse Table 4(a) の top-1: MF 60.2、layer 12 のみ 63.9、layer 2 のみ 66.7、layer 2＋dynamics 68.8、layers 2／7／11＋dynamics 69.7。Table 4(c): 本物の物体領域 69.7 に対し、full／null／grid／random の box は 60% 台前半（L524。報告の解釈と提案の節にある値） | ORViT は改善。既存の単純な物体モジュールは強い受け取り手の上で差なし・悪化 | 融合の設計（入れる層、繰り返しの注入、dynamics）で符号が変わる。検出器の box と oracle の box で利得の大きさが変わる |
| C-06 | Table 1: EK100-MIR の mAP 35.9 → 37.5（+1.6 pp）、nDCG 36.6 → 37.8（+1.2 pp）。EGTEA の Top-1 44.9 → 46.6（+1.7 pp）、Mean 37.6 → 39.1（+1.5 pp）。Table 2: 100DOH 検出器の入力解像度を 256p から 640p にしたよりよい疑似 box で学習すると、EK／EGTEA の平均 zero-shot がさらに約 1% 向上（著者の記述）。Table 5: 物体に加えて手を予測させると zero-shot が概ね約 1% 上がる（著者の記述） | 改善 | box の質を変えると下流の利得も変わる（Table 2）。ただし検出 mAP を横軸にした相関解析ではない |
| C-07 | Table 2（seen／unseen）: CSN 15.51／9.82、GCN 12.94／10.10、融合 19.28／13.06。融合 − CSN は +3.77 pp／+3.24 pp | 改善 | unseen の split でも相補性が残る。graph のみは見えのみを一律には上回らない |
| C-08 | 要旨のみのため数値は不明 | 不明 | 不明 |
| C-09 | 表単位の数値は未確認のため報告は書いていない | 不明 | 不明 |
| C-10 | 融合の追加効果の数値は不明 | 最終システムとしては高性能だが、物体信号の追加効果の符号は要旨だけでは判定できない | 不明 |
| C-11 | 要旨のみのため数値は不明。著者は、既存の映像言語モデルが手・物体の dynamics そのものではなく、手・物体・環境の文脈の間の見かけの相関に依存しうると報告 | 否定的な所見 | 不明 |
| C-12 | 報告は数値を転記していない。要旨は三課題を同じデータで調べられることを述べ、器具の予測を工程の入力にした比較があるとは要旨から確認できない | 該当なし | 不明 |
| C-13 | 40／8／32 の split は全工程と単一の器具が各集合に存在し分布も比較的近い一方、Calot triangle dissection から始まる手術が train の側にだけ存在する（workflow の偏り） | 特定の手法の改善・悪化ではなく、分割だけで評価の条件が変わるという方法論上の否定的証拠 | validation をどこから切り出すかで、工程の長さ・遷移・器具の共起の分布も変わりうる |
| C-14 | C2 は本文の表を未確認のため書いていない。R1: C-21 の Table 2 の基準として Cholec80 clean で 92.2% accuracy／77.8 Jaccard | 不明 | 不明 |
| C-15 | 原典の課題で高い効果を報告するが、外挿の意味が薄いため報告は数値を転記していない | 該当なし | 該当なし |
| C-16 | 詳細記録なし | 不明 | 不明 |
| C-17 | 要旨のみ | 不明 | 不明 |
| C-18 | Table 1: EndoNet+HHMM の precision 73.7／recall 79.6 に対し、提案法 81.8／80.9（+8.1／+1.3 pp） | 改善（受け取り手も異なる。R1 の判定: 否定的結果「いいえ」） | R1 に記載なし |
| C-19 | Table 1（CATARACTS の外部の test）: LSTM で二値 68.75 acc／68.50 F1 → 特徴 78.28／74.92（+9.53／+6.42 pp）。GRU で二値 71.61／67.33 → 特徴 68.96／66.62（−2.65／−0.71 pp） | LSTM で正、GRU で負（R1 の判定: 否定的結果「はい」） | 受け取り手の時間モデル（LSTM か GRU か） |
| C-20 | Table 4（G40）: RGB のみ 63.37% acc／55.49 mF1 → Linear V+VKI 69.71／56.76（+6.34／+1.27）、Conv V+VKI 67.71／57.41（+4.34／+1.92）。VKI のみ 50.53／34.80（R1 L47）。Table 2（PETRAW）: bbox を足すと phase 指標が +4.30〜+22.95 pp | 融合で正。VKI のみは RGB のみを下回る（R1 の判定: 否定的結果「いいえ」） | accuracy と mF1 で最良の融合が一致しない（R1 L36） |
| C-21 | Table 2: Cholec80 clean で Surgformer 92.2 acc／77.8 Jac → DTFormer 85.5／67.2（−6.7／−10.6 pp）。Cholec80-C で 76.4 → 80.3（+3.9）。CRCD で 56.0 → 67.9（+11.9）。Table 3: corrupted で DT-Aug 76.4 → 79.4（+3.0） | clean で負、corrupted・OOD で正（R1 の判定: 否定的結果「はい」） | 分布のずれの有無 |
| C-22 | Fig. 5: full-token の OAM で Something-Else +2.1、SSv2 +1.3、EPIC-KITCHENS +0.6 pp。正解 box では前二者が +7.3／+6.3 pp。Table 2（SSv2）: VideoMAE 64.8% → 予測 box 68.5%（+3.7。R1 L91）→ 正解 box 73.0%（予測 → 正解 +4.5 pp）。著者は、人と物体の相互作用のデータに合わせた検出器が最も有効で、より強い検出の backbone や open-world の検出器に変えても行動認識は改善しなかったと報告（R1 L58）。物体の領域だけを残し背景の token を全部捨てると悪く、少し残す方がよい（R1 L60） | 正（R1 の判定: 否定的結果「はい」） | 検出器の領域への適合、背景の token を残すか |
| C-23 | Table I: Something-Else 63.4 → 65.8（検出の multi-task）→ 66.3（IRA）、合計 +2.9 pp。IKEA の macro 47.6 → 53.2（+5.6）。Table VI: 融合の層 layer 9 で 66.3、layer 13 で 65.7、最後の層で 64.4（基準 63.4）。Table VII: 検出 66.8 → 正解の個数 69.7（+2.9）→ 正解の対応 72.3（+5.5）。同表で、同じ MViT 系の基準 63.3 に対し、検出 box の再実装 STIN 48.2、STLT 56.9、SViT 65.8（R1 L64）。IKEA の再実装: MViT 47.6／79.2（macro／micro）、STRG 52.3／79.8、STIN 48.0／81.0（R1 L66） | 中間層の融合で正、最後の層ではほぼ零。検出 box の STIN・STLT は基準を下回る（R1 の判定: 否定的結果「はい（比較系で）」） | 融合する層。著者は、最後の層では物体の情報が映像の表現に十分融合されず単なる multi-task に近づくと解釈（R1 L62） |
| C-24 | Table 4: 工程の accuracy 85%、F1 83% | 判定できない。器具の入力なしの基準も正解の oracle も無い（R1 L49） | 該当なし |

---

## 7. 実装

| ID | コード・重み・ライセンス | 追加データ・注釈 | 事前学習と評価データの重なり |
|---|---|---|---|
| C-01 | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| C-02 | データセットのリンクが arXiv から公開。コード・重み・ライセンスの詳細は未確認 | 視線 | 本文未確認 |
| C-03 | 論文に実装公開の系譜があるが、ライセンスは確認できず | 検出器の学習に物体の注釈。EGTEA では EPIC 用の検出器を転用しており、ドメイン・クラスの不一致がある | 検出器を同じ EPIC の訓練ドメインに適応している |
| C-04 | ライセンス未確認 | 手・物体の密な box | 検出器は COCO 事前学習の後に行動の train split の注釈で fine-tune。test の注釈を検出器の学習に使う記述はない |
| C-05 | project／code の公開が論文に記載。ライセンス未確認 | SSv2 では検出器の fine-tune 用の box。EK100／Diving48 では COCO 事前学習の Faster R-CNN のクラス不問の box を使い、領域内の物体ラベルは不要 | EK100 の検出器は COCO、映像の backbone は Kinetics／ImageNet 系。論文記載の範囲では EK100 test の box 注釈を検出器の学習に使わない |
| C-06 | ライセンス未確認 | 100DOH 検出器、字幕・疑似の物体ラベル | EgoMCQ は事前学習の Ego4D と同じデータ源であると著者が明記。clip の重なりの有無は不明。EK100／EGTEA はドメイン移転 |
| C-07 | 不明 | 後続（C-17）で EPIC-Kitchens の部分集合に手・物体の分割と接触までの時間の注釈を追加 | 不明 |
| C-08 | 不明 | 領域内の検出器のラベルを不要にする点が主眼 | VLM の事前学習コーパスとベンチマークの重なりの監査は要旨から不明 |
| C-09 | 著者ページ・論文で project／code の公開を案内。ライセンス未確認 | Ego4D STA の注釈 | 不明 |
| C-10 | 公開予定と要旨に記載。ライセンス不明 | COCO 事前学習の検出器、V-JEPA の事前学習 | V-JEPA 2.1 の事前学習データと Ego4D STA の重なりを報告は検証できず |
| C-11 | 未確認 | DEHOI testbed、inpainting による手がかりの分離 | 不明 |
| C-12 | challenge の資源。ライセンスの詳細は未確認 | 統一の注釈 | チームごとに異なり不明 |
| C-13 | open access の論文。関連コードは未確認 | 不要 | 主題外 |
| C-14 | arXiv が code の公開を記載。ライセンス未確認 | 不明 | 不明 |
| C-15 | 未確認 | 不明 | 不明 |
| C-16 | 不明 | 不明 | 不明 |
| C-17 | 不明 | 手・物体の分割と接触までの時間の注釈 | 不明 |
| C-18 | R1 に記載なし | ZIBNet（器具在否の検出器） | R1 に記載なし |
| C-19 | R1 に記載なし | 21 クラスの器具在否の注釈、ResNet-152 | R1 に記載なし |
| C-20 | R1 に記載なし | semantic segmentation（器具・臓器） | R1 に記載なし |
| C-21 | R1 に記載なし | SAM2（mask）、DepthAnything（depth） | R1 に記載なし |
| C-22 | R1 に記載なし | 既製の検出器、track identity | R1 に記載なし |
| C-23 | R1 に記載なし | 物体 proposal、検出の教師（multi-task） | R1 に記載なし |
| C-24 | R1 に記載なし | YOLOv8 | R1 に記載なし |

---

## 8. 本研究との関係

報告者の一行（各行の本研究との関係についての報告者の要約）は、報告者の読みを含むため地図から外し、起票者用の文書に移した（利用者の決定 2026-10-18）。事実としての近さは §3（距離の軸）と §4 の「本研究の条件で測られたか」に書いてある。

---

## 9. 信号の種類 × 正解か予測か（起票者が報告の行から組んだ索引）

報告 L20 の区別で、各行がどの種類の物体信号を、予測（実際の検出器の出力）と正解（oracle）のどちらで扱ったかを並べた。値は §6 にある。

| 信号の種類 | 予測を使った行 | 正解を使った行 | 予測と正解を同じ受け取り手で比べた行 |
|---|---|---|---|
| クラス確率・在否 | C-03（bag of objects。数値は不明）、C-01（7 次元の confidence。R1）、C-18（ZIBNet のラベルの系列）、C-24（YOLOv8 の在否。基準なし） | C-01（GTBin。EndoNet の表現に足す。N1 は正解の二値だけを入れた条件の値も書く）、C-19（二値の在否。R1 は正解、N1 は予測とする） | C-01（R1 の分類。75.2 対 75.3、online 81.7 対 81.9） |
| box の幾何・軌跡 | C-04、C-05、C-22、C-23 | C-04、C-05、C-22、C-23 | C-04（51.4% 対 37.2%）、C-05（oracle の box で +7.3／+6.7 pp、検出器の box で +1.4 pp）、C-22（SSv2 で 68.5 対 73.0）、C-23（66.8 対 69.7／72.3） |
| segmentation 由来の位置・大きさ・動き・関係 | C-20（予測か正解かは R1 に記載なし） | 同左 | なし |
| RoI の見え・検出器の内部表現 | C-05（幾何と見えの両方）、C-10（RoI 単位の融合）、C-19（ResNet-152 の器具特徴）、C-23（物体の表現） | C-05 | C-05 |
| 器具と解剖の mask・depth の構造化表現 | C-21（SAM2・DepthAnything の出力） | なし | なし |
| 接触状態・状態の遷移 | C-07、C-17 | なし（報告に記載なし） | なし |
| 物体の意味（事前学習モデルの object prompt） | C-08 | なし | なし |
| 物体を意識した学習時の教師（推論時には渡さない） | C-06（疑似 box。入力解像度の二水準） | なし | なし |

C-19 は二値の在否と器具特徴を同じ時間モデルで比べる。R1 は二値を正解とし、信号の形が違うため予測 → 正解の置き換えとして扱わない（R1 L104）。N1 は二値を予測とする（N1 L50）。

予測 → 正解の差の一覧（R1 L98–L104 の表を行 ID に置き換えたもの）: C-01 +0.1 pp（Table III）、+0.2 pp（Table IV(a)、online）。C-22 +4.5 pp（Table 2）。C-23 +2.9／+5.5 pp（Table VII）。C-19 は比較不能（R1 の記載）。C2 の行では C-04 +14.2 pp（検出 37.2 → 正解 51.4）、C-05 の oracle の box で +7.3／+6.7 pp 対 検出器の box で +1.4 pp。

同じ物体信号を、強さの違う受け取り手に入れた行: C-05（MF／MF-L／MF-HR。ただし物体モジュールも受け取り手の構造に組み込まれる）。手術の行は無い。R1 も、同じ D の信号を弱い P と強い P に足した手術の比較は見つからなかったと書く（R1 L93、L154）。C-21 は強い受け取り手（Surgformer）の行だが、信号は検出器の出力ではない。DTFormer は RGB を構造化表現に置き換え、DT-Aug は RGB 特徴に補助として足す（R1 L11、L37）。

---

## 10. 見つからなかったもの

### 10.1 C2 の報告（L395–L437）

「見つからなかった」は、報告が本文まで確認した集合で確認できなかったという意味で、存在しないという主張ではない（報告の定義）。

1. **手術で「凍結した D＋凍結した P＋その間の小型の界面だけを学習」。** 検索語: surgical phase recognition frozen detector frozen phase model adapter／instrument detection phase recognition gate frozen／surgical tool output phase model lightweight fusion／MICCAI IPCAI surgical phase instrument context。手術側の関連候補 9 件を照合し、全条件を同時に満たすものは 0 件。近いものは EndoNet の共同学習、Digital-Twin／scene representation 系、PhaKIR の統一 multi-task ベンチマーク、VISTA の凍結した時間枝で、それぞれ共同学習・scene representation 自体の学習・三課題の同居・片側だけの凍結である
2. **同じ検出信号を、弱い工程モデルと強い工程モデルの両方に足す手術実験。** 検索語: same instrument signal weak strong phase recognition backbone／surgical phase object fusion backbone ablation／tool signal phase recognition ResNet transformer comparison。手術候補 9 件の中で、同じ D の出力・同じ split・同じ界面を固定して受け取り手だけを差し替えた比較は無い。手術以外では C-05 が近いが、検出信号と界面を完全に固定した比較ではない
3. **検出器の mAP と下流の利得の定量曲線。** 検索語: object detector accuracy downstream action recognition gain／detector mAP action recognition oracle boxes／bounding box quality downstream action recognition／egocentric detector quality anticipation performance。手術以外の候補 10 件と一般の物体中心の候補 4 件を確認。見つかったのは C-04 の正解対検出、C-05 の oracle 対検出、C-06 の検出器の入力解像度の二水準。複数の精度の D を用意し、各 D の mAP を横軸、凍結した P への増分を縦軸にした研究は無い。C-01 の Fig. 10 は学習動画数を変えると検出器と共有表現が同時に変わるため、この問いの実験ではない
4. **2024〜2026 の手術工程認識で、予測した器具・物体の信号を工程の入力へ明示的に入れる追加の文献。** 検索語: 2024 surgical phase recognition instrument object／2025 surgical phase tool fusion／2026 phase recognition instrument context／MICCAI surgical phase instrument／Medical Image Analysis phase instrument recognition。既所持の Digital-Twin-based Scene Representation を除くと、厳格な基準で本文まで確認できた追加は 0 件。PhaKIR、Surgformer、EgoSurgery-Phase、SurgVLP はそれぞれ別の系統
5. **EgoSurgery の 15 本の術具 box 注釈と 21 本の工程注釈を同じ研究で結ぶ既発表の論文。** 検索語: EgoSurgery tool detection／EgoSurgery instrument detection bounding box／EgoSurgery open surgery object detection／EgoSurgery phase tool。確認できた査読の一次文献は EgoSurgery-Phase（C-02）で、要旨は工程認識と視線を扱う。術具検出器 → 工程モデルを評価した公開論文は確認できず
6. **正解の器具信号と予測の器具信号を、強い online 工程モデルで比べる条件。** C-01 の GTBin（+0.1〜+0.2 pp）は、大規模事前学習の映像モデル・online の causal な時間モデル・凍結した界面の組み合わせではない。C-04・C-05 の oracle は手術ではない。正解の器具 box／正解の器具在否／予測の box／零の信号を同じ強い online 手術 P で比べた条件は確認できず
7. **種「STLT」「SViT」。** 検索語: STLT egocentric action recognition／SViT object hand video egocentric／STLT action anticipation object／SViT egocentric object transformer。同名・類似の略称との衝突で手法を一意に同定できず、架空の書誌を作らずに「種の解決が未完了」と記録

### 10.2 R1 の報告（L139–L157）

R1 の件数は検索エンジンの総ヒット数ではなく、題名・抄録・本文を照合した主要なユニークの候補数で、PRISMA の count ではない（R1 L141 の定義）。

| 検索対象・検索語（R1 の記載） | 精査した件数 | 厳密な D→P に当たる件数 | 見つからなかった内容（R1 の記載） |
|---|---|---|---|
| EgoSurgery tool phase recognition detector output／"EgoSurgery-Tool" phase recognition tool features | 3（Phase、Tool、HTS） | 0 | 一人称開放手術で、独立した器具検出器の予測 → online-causal の工程モデルの実験、予測と oracle の比較。EgoSurgery の公開研究は課題ごとに分かれている |
| AutoLaparo phase instrument tool detection workflow | 2 | 0 | workflow と器具・解剖の分割を同じベンチマークに持つが、分割・検出の予測を工程の受け取り手に渡す統制された ablation は確認できず |
| HeiChole phase instrument fusion／HeiChole phase instrument recognition | 2 | 0 | 工程・器具・行動を併設するが、器具の出力 → 工程モデルの増分を測る研究は確認できず |
| CholecT50 phase recognition tool detection instrument phase fusion | 4 | 0 | instrument–verb–target、工程、一部の box を持つが、器具検出器の出力を工程に入れて D なし・oracle と比べる論文は確認できず |
| CATARACTS surgical phase recognition instrument detection tools workflow recognition | 3 | 1 | C-19 を発見。同じ形の予測の二値在否 → 正解の二値在否の厳密な oracle は見つからず |
| M2CAI16 workflow phase instrument detection tool presence surgical | 3 | 0 | 同じ検出器の予測を下流の工程モデルに渡す、対照つきの D→P の ablation は確認できず。M2CAI の workflow の multi-task 構造は独立した界面の実験ではない |
| surgical phase recognition instrument presence detection Cholec80 tool phase 2024 2025 2026 | 10 以上 | 直接型は少数 | 2024–2026 の主流は工程の backbone の改良、multi-task、VLM、robustness。凍結した独立の検出器の出力を小さな界面だけで強い causal の工程モデルに足す統制研究は確認できず |
| surgical phase tool ground truth predicted oracle に相当する検索 | EndoNet、DeepPhase、近接研究 | 厳密な同じ形の oracle は 1 研究 | 手術で予測と正解を同じ界面で置き換えて下流の差を明示した例は C-01 が最も明確。C-19 は二値と潜在特徴で形が違う |
| surgical phase detector output gate／detector signal gating | 関連する融合・attention の文献 | 0 | 独立した D の出力に小さな学習可能な gate を置き、gate 自体を工程で ablation した手術の報告は確認できず（R1 L83 も同じ） |
| strong surgical phase model instrument/tool fusion Surgformer LoViT | 複数の強い工程モデル | 統制された比較 0 | 同じ D の信号を弱い P と強い P の両方に足し、P が強いほど利得が縮むかを直接検定した論文は確認できず。C-21 が最も近いが信号と表現の両方が変わる |
| SomethingElse detected boxes ground truth action recognition／object detector output action recognition oracle | ORViT・STIN・ObjectViViT・DAIR の系 | 複数 | 見つからなかった項目ではない。oracle の差の証拠は手術以外に複数ある（C-22 の 4.5 pp、C-23 の 2.9–5.5 pp） |

R1 は総括として、確立していないのは「一人称開放手術で、独立に学習した検出器と強い online-causal の工程モデルを凍結し、小さな学習可能な界面だけを学習したときの D→P の利得、その受け取り手の強さへの依存、同じ形の oracle の差」であり、C-01・C-19・C-21・C-22・C-23 を合わせてもこの組み合わせを直接評価した研究は確認できなかったと書く（R1 L157）。

---

## 11. 未検証の組み合わせ（C2 L440–L460）

報告が確認した文献集合を並べたとき、その条件を同時に満たす測定を確認できなかった組み合わせ。誰も行っていないという意味ではない（報告の定義）。R1 には同じ趣旨の独立した節が無い。R1 の該当する記述は §10.2 の表と総括（R1 L83、L93、L157）にあり、下の 1・2・5 と重なる。

1. **凍結した検出器と凍結した工程モデルの間だけを学習する条件。** C-03 は検出器の特徴の取り出しが固定でも時間側を学習する。C-04・C-05 は受け取り手を学習・fine-tune する。C-06 は強い visual backbone を固定する点が近いが、検出器の出力は推論時の入力ではなく学習時の教師。C-10 は V-JEPA 2.1 の枝が凍結だが、検出器の側と融合ヘッドの凍結範囲が要旨だけでは一致しない
2. **同じ D の出力を、弱い P と強い P へ一切変えずに入れる条件。** C-05 は近いが、物体モジュール自体も受け取り手の構造に統合される
3. **D の品質を連続的に変えた用量反応。** C-04 は正解と検出の二点、C-05 も検出器と注釈 box の二点、C-06 は検出器の入力解像度の二水準
4. **クラス confidence だけ、box の幾何だけ、RoI の見えだけ、手と器具の関係だけを、同じ界面で比べる条件。** C-03 は主にクラス confidence、C-04 は幾何、C-05 は幾何＋見え、C-07 は接触・状態を使うが、データ・backbone・課題が異なる
5. **強い受け取り手での予測対正解の oracle gap。** C-05 に比較的強い transformer と正解 box の oracle の結果があるが、offline の一般行動認識である。手術の online 工程認識では未確認
6. **少数動画・一人称・online・検出器の出力の四条件の交点。** C-03・C-10 は一人称・causal・物体を意識するが大規模な一人称ベンチマーク。C-02 は一人称・少数だが器具の出力の融合ではない。C-12 は少数・手術だが内視鏡で、厳格な D→P の融合の実証は要旨から確認できない
7. **工程側が既に器具の情報を潜在的に持つ場合の追加情報量の測定。** C-01 の GTBin がほぼ改善しないこと、C-05 の強い基準の上で STIN／STRG が差なし・悪化することは、明示的な物体の手がかりが既存の視覚表現と冗長になりうることを示すが、条件付き相互情報量や手がかりの削除で冗長性を直接測った実験は確認していない
8. **検出器の較正の質と下流の利得。** mAP が同じでも score の較正が違えば界面への入力の分布が変わる。検出の mAP と confidence の較正を分けて下流の利得を測った結果は見つからず
9. **時間の漏れを除いた物体追跡。** C-05 は SORT を使い forward の追跡器は逐次的だが、一般に事前計算した tracklet、clip の中心に置いた特徴、双方向の時間 encoder をそのまま移すと未来の情報を含みうる。C-05 の標準の認識は複数 clip を使う offline 評価である

---

## 12. 検索記録

### 12.1 R1

- **検索日:** R1 に記載なし。2024–2026 年を優先し、EndoNet・DeepPhase・STIN／ORViT の系などの古典に遡った（R1 L19）
- **方向:** ①手術映像の器具 → 工程・workflow、②EPIC-KITCHENS などの一人称・物体中心の行動認識、③Something-Something 系を中心とする一般映像の物体で条件付けた行動認識（R1 L19）。新様式の七方向とは対応しない
- **採否の基準:** 検出器・物体認識器の予測・score・box・RoI／潜在特徴・segmentation 由来の特徴のいずれかが下流の行動・工程モデルの情報として実際に使われていること。MTRCNet-CL・LAST のような共同学習は区別した（R1 L21）。oracle は同じ種類の正解に置き換えて比べられるかを重視した（R1 L23）
- **検索語と件数:** §10.2 の表
- **数値の扱い:** 本文・表・図で直接確認したものだけを書いたと R1 は記す（R1 L23）

### 12.2 C2

**検索日:** 2026-10-18（Asia/Tokyo）。件数は検索サイトの推定ヒット数ではなく、重複を除き、実在と問いとの関連を個別に確認した文献数（報告の定義）。方向間の重複を許す。

| 方向 | 主な検索語・追跡の経路（報告の記載） | 件数 | 主な結果（報告の記載） |
|---|---|---|---|
| 一 EgoSurgery・一人称開放手術 | EgoSurgery open surgery phase recognition first person／EgoSurgery tool detection／EgoSurgery instrument bounding box | 1 | EgoSurgery-Phase を確認。公開された D→P の融合は確認できず |
| 二 手術一般 | surgical phase recognition instrument tool object 2024 2025 2026／PhaKIR／Cholec80 split instrument phase／MICCAI・MedIA・TMI 系 | 9 | PhaKIR、EgoSurgery-Phase、Surgformer、split の分析など。厳格な tool-output→phase は極めて少ない |
| 三 一人称の非手術 | egocentric object detection action anticipation／hand object contact action recognition／EPIC-KITCHENS object anticipation／Helping Hands／StillFast／VISTA／object-centric long-term anticipation | 10 | RULSTM、Helping Hands、Ego-OMG と接触表現、StillFast、VISTA など |
| 四 一般映像 | 医療語なしで object boxes action recognition transformer detected boxes ground truth／SomethingElse STIN／object-region video transformer | 4 | STIN／ORViT が正解対検出と、強い基準の上の否定的証拠を提供 |
| 五 機構一般 | 医療語なしで conditioning gate pretrained frozen model／FiLM conditioning／object fusion pretrained video model | 3 | FiLM などを確認。凍結 D／凍結 P／界面のみの厳密な一致は 0 |
| 六 方法論 | surgical phase instrument dataset split／video cross validation leakage／Cholec80 appropriate dataset splits | 2 | Kostiuchik ほか、PhaKIR challenge の方法論 |
| 七 否定的な結果 | 医療語なしで ground truth vs detected boxes action recognition／object cues strong backbone negative／detector quality downstream action recognition、加えて手術の検索 | 5 | EndoNet の少数データでの反転と GTBin、STIN の oracle gap、ORViT の零・負の融合、Helping Hands の box の質、Tateno ほかの近道の診断 |

報告が書いた探し方:

- **種からの追跡:** 種の RULSTM・Helping Hands・ORViT・EPIC-KITCHENS の系統に加え、種に無かった Ego-OMG と接触表現、Zhang ほか 2024、StillFast、VISTA、2026 の手がかり分離の研究まで追った
- **引用の追跡:** STIN から ORViT へ。ORViT の表で STIN／STRG を強い transformer に足すと効果が消える条件を確認
- **順位表・データセット起点:** Ego4D STA の StillFast 系を 2026 の VISTA まで。手術では PhaKIR challenge report
- **手術を検索語に入れない探索:** 方向三・四で独立に実施（L5）

**走査の偏り（報告の自己申告、L483）:** 2024〜2026 の主要会議・論文誌の横断では、一次資料を直接確認できた範囲が MICCAI、CVPR／WACV 系、Medical Image Analysis、TMI 系に偏った。IPCAI、ICCV、ECCV、NeurIPS、ICLR は、厳格な D→P の条件に当たる 2024〜2026 の論文を本文確認できなかった。報告はこれを「該当論文が存在しない」ではなく「検索・取得の範囲の未完了部分」として扱っている。

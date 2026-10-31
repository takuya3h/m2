# 証拠地図 H — 把持（手と物体の相互作用）の推論を、物体検出と行動・手順・工程の認識の補助信号にする

**版:** v2.2（2026-10-31、起票者が作成。v2.2 は v2.1 の照合〔PR #269〕の結果で §2 の書誌の欄を直した版: 照合不能だった行に照合先の著者と題名を書き、三つの文献をまとめた H-16・H-60 を一文献一行に分け〔H-64〜H-67 を足した〕、照合で別の文献と分かった ID を別の行〔H-62・H-63〕にし、H-44 に照合で分かった ID を書いた。行の中身・数値は変えていない。v2.1 は v2〔同日〕の §2 の文献の欄を 7 行〔H-18・H-19・H-35・H-36・H-37・H-46・H-56〕で照合器が読める形〔「著者 ほか, 題名」か「年, 題名」〕に直した版。値は報告の記載で、行の中身・数値・書誌 ID は変えていない。v2 は報告五件から作り直した。v1〔同日、R8-1・R8-2 だけから作成〕を置き換える。v1 は repo に置いていない）
**種類:** 探索の地図
**状態:** v2.1 の書誌の機械照合は済み（2026-10-31、andrew、PR #269。65 ID: 実在・書誌一致 49、実在・書誌に差 2、実在・照合不能 14、不在 0、到達不能 0。起票者の事前の予測と同じ。結果は docs/evidence/verification/2026-10-31-H-grasp-signal.md）。v2.2 は未照合。数値の原典確認は未実施。起票者が web 検索で確かめたものは §0.3
**元の報告:**
- 報告「R8-1」（Claude。依頼文 R8 の本文だけで投げた。添付の名前は文字化けしており元の名前は不明。repo では R8-1-research_claude.md。59,684 バイト、sha256 3dd471d27a99bee6d2ba3e0eeb08fd00c5315c723a3b7ba2ea2eb8b500263b30）
- 報告「R8-2」（ChatGPT。依頼文 R8 の本文だけ。deep-research-report_8.md、repo では R8-2-deep-research-report.md。21,064 バイト、sha256 690c749f9c9b9e343d43455e80f221deb651a58aff227d8c6af18aff9d03a211）
- 報告「R8-3」（ChatGPT。依頼文 R8 の本文だけ。deep-research-report_9.md、repo では R8-3-deep-research-report.md。31,954 バイト、sha256 2c137d6dc202087bb3b6acf526135f298c2fe2c93450b8d3c741f8ac5fdc817b）
- 報告「R8-4」（ChatGPT。依頼文 R8 の本文と共通ブロック。deep-research-report_10.md、repo では R8-4-deep-research-report.md。57,540 バイト、sha256 49a062b27d41383dbab89ea4f93b9d0ee708c0baf470e471c119cff71db43107）
- 報告「R8-5」（Claude。依頼文 R8 の本文と共通ブロック。添付の名前は文字化けしており元の名前は不明。repo では R8-5-research_claude.md。58,206 バイト、sha256 4654f25901a2e97c28a0589900f0e6cc7d5e07fa91e2e1cb073affae7b925a24）
- R8-2・R8-3・R8-4 は citation の印の残骸と私用領域の文字を含む（126・204・376 個）。R8-2・R8-3 は書誌 ID を一件も書いていない

**検索日:** R8-1・R8-4・R8-5 は 2026-10-31（報告の記載）。R8-2・R8-3 は記載なし

---

## 0. この地図の読み方

### 0.1 問い

依頼文 R8（2026-10-31）の問い。三つ目のモデル（把持モデル。手と術具の把持関係を推論する）を独立に学習し、その出力を (a) 推論時に小さな学習可能モジュール（界面）を通して検出モデルか工程認識モデルへ渡す形、または (b) 学習時だけ教師にする形（蒸留・補助損失）で使うとき、物体検出（mAP）と工程認識（macro Jaccard）は変わるか。対象は一人称・開放手術・15 動画・0.5 fps・online。報告の問いの番号 (1)〜(11) は依頼文 R8 の番号である。

- R8-1〜R8-3 は共通ブロック（出力の形・守ること・方向 1〜7）を渡さずに投げた。R8-4・R8-5 は渡した
- R8-5 は「補足 1〜6」（折りの内側での学び直し、規則との比較、他者の手、低いフレームレート、注釈が一部の動画にしか無いこと）に答えている。この番号は依頼文 R8 に無く、出所は不明

### 0.2 規則

- 行は報告に書かれた事実だけを載せる。数値・表番号は報告のまま。報告に書かれた差は起票者が検算した（§0.4）
- 複数の報告が同じ文献を書いている行は、共通ブロックを渡した報告（R8-4・R8-5）と本文を読んだ報告の値を採り、違いは §0.5 に書いた
- 報告が「不明」「未確認」とした欄は不明のまま。R8-2・R8-3 だけに由来する行は「報告に記載なし」が多い
- 現役度は報告の値と理由。R8-2 の独自の「信頼度」「関連度」は報告者の評価なので載せない
- 距離は一つの数字にしない。§3 の軸に分け、探索の優先度には使わない
- 報告者の解釈と提案（各報告の解釈・提案の節、要約の評価の文）は地図に載せず、起票者用の文書に置いた
- 見つからなかったもの（§10）と未検証の組み合わせ（§11）は、その設計が新しい・価値があるという根拠として読まない。見つからない理由には、技術的な困難、価値が乏しいと見なされていること、偶然がありうる
- 出所の列は報告の行番号。「4:L82」は R8-4 の 82 行目
- citation の印は除いた
- 書誌 ID の欄で「起票者が特定」と書いたものは報告に無い ID であり、照合で確かめるまで引用として使わない
- v2.2 で H-16 を H-16・H-64・H-65 に、H-60 を H-60・H-66・H-67 に分けた。§3 以降の H-16・H-60 の行は、分ける前の三件をまとめて書いている（それぞれ H-16・H-64・H-65 と H-60・H-66・H-67 の三件を指す）

### 0.3 照合と原典確認の状態

書誌の機械照合: 未実施（配置と照合の契約で行う）。

起票者の確かめ（2026-10-31、web 検索と取得の結果の頁の範囲）:

| 行 | 確かめたこと | 確かめていないこと |
|---|---|---|
| H-04 Shiota ほか | CVF の本文の表 1〜3 の全行（§6 の値はこの確認と一致）。要旨の「EGTEA で最大 2.24%」は表の最大の差 2.84 と一致しない | DOI 10.1109/WACV57701.2024.00641（R8-4 の記載） |
| H-01 Helping Hands | EGTEA Top-1 44.9→46.6 は表 1（損失の ablation）と表 4（SOTA との比較の Ours*‡ と Ours*）の両方にある。表 2 の 640p の行は 46.6 が Mean の列にあり、表 1 と列が逆 | — |
| H-19 VidParse | arXiv 2608.27562 に同じ題名。凍結 DINOv2（ViT-L/14）、凍結した手と物体の検出器、手と active object の枠を覆う最小の枠に入るパッチの平均、online、学習なし、EgoPER の表 1 で Acc 80.7・F1@0.5 77.6 | ECCV 2026 の掲載、full-frame の 69.09・61.42 の表番号 |
| H-05 G3Ego | arXiv 2608.20157、著者 3 名、2026-08-20 投稿、掲載先の記載なし | 表 1 の数値、20 次元の手の特徴 |
| H-27 IRN | arXiv 2201.04906、Jian Ma と Dima Damen。表 8 の EPIC-KITCHENS-100 の検証集合で SlowFast 63.64／48.58／36.76、IRN 63.68／48.94／37.11（動詞／名詞／行動）。抜粋に「The proposed framework is trained end to end」とある | R8-3 の書く「検出器の重みは凍結」 |
| H-58 Goldbraikh ほか | arXiv 2110.13972、IJCARS 17(3): 437-448（2022）。模擬の開放手術で、YOLO を二つの課題（術具の位置と手と術具の相互作用の検出）に分けた | 報告は ID を書いていない |

起票者の書誌の事前の確かめ（2026-10-31。arXiv の要旨の頁と Crossref の API の応答を読んだ。照合器ではない。照合の予測に使う）:

| 行 | 確かめたこと |
|---|---|
| H-09 | arXiv 2211.09067 の題名は「Egocentric Hand-object Interaction Detection」、著者は Yao Lu と Yanan Liu。R8-5 の「内容が大きく重なる版」の記載と著者が違う（行の著者は arXiv 2109.14734 の二名で、2109.14734 の頁と一致） |
| H-42 | arXiv 1806.07110 の題名は「Modality Distillation with Multiple Stream Networks for Action Recognition」（著者は Garcia, Morerio, Murino の三名）。行の題名（IEEE TPAMI の版）とは違う |
| H-28 | Crossref の著者は Eadom Dessalene, Chinmaya Devaraj, Michael Maynord, Cornelia Fermüller, Yiannis Aloimonos の五名。R8-4 の書く Namboodiri は含まれない |
| H-55 | Crossref の題名は「ESIP: Explicit Surgical Instrument Prompting for Surgical Workflow Recognition」（第一著者 Yixuan Qiu） |
| H-56 | Crossref の著者は Ori Meiraz ほか六名（Shlomi Laufer を含む） |
| H-53 | 三つの DOI とも第一著者は Bogyu Park。訂正の DOI（10.1016/j.compbiomed.2026.111850）の題名は元の題名を含む |
| H-37 | 多モーダル版（arXiv 2209.08691、DOI 10.1016/j.cviu.2023.103764）の著者は Ragusa, Furnari, Farinella の三名 |
| H-01・H-02・H-03・H-04・H-05・H-08・H-10・H-12〜H-15・H-18・H-19・H-20・H-25・H-30・H-31・H-33・H-35・H-36・H-38・H-46・H-52・H-57・H-58 | 題名と著者（「ほか」の無い行は全員）が行の記載と合う |

R8-2 の L9 の「EgoSurgery 系で工具や組織の空間情報を workflow recognition に入れた研究」は、どの文献かが書かれていないため行を作っていない。

### 0.4 起票者の検算（報告に書かれた差）

| 行 | 報告の値 | 検算 | 結果 |
|---|---|---|---|
| H-01 | EGTEA Top-1 +1.7、mean +1.5、EK100-MIR mAP +1.6、nDCG +1.2（4:L72） | 46.6−44.9、39.1−37.6、37.5−35.9、37.8−36.6 | 一致 |
| H-03 | SSv2 +2.9、Something-Else +5.7、教師と生徒の差 2.1 と 1.9（5:L328〜L329） | 63.2−60.3、57.5−51.8、65.3−63.2、59.4−57.5 | 一致 |
| H-03 | 推論時に使う場合の利得の「約 6 割」「7.5 割」（1:L133） | 2.9/5.0 = 0.58、5.7/7.6 = 0.75 | 一致 |
| H-04 | EGTEA の SlowFast +2.46・+1.79・+2.84、mean +2.33、Swin-B +1.89、mean +2.13、MECCANO +3.97・−2.02・−0.03・+0.78（4:L52〜L53） | 表の値から計算 | 一致。Swin-B の +1.89 と +2.13 は HOCL と OSL の両方の行 |
| H-05 | Top-1 +4.57、Macro-F1「5.5 点」（1:L35・L186） | 46.48−41.91 = 4.57、21.34−15.87 = 5.47 | 一致（丸め） |
| H-08 | 表 4 で行動 +4.25、動詞 +7.32、物体 +1.36（4:L108） | 38.05−33.80、66.32−59.00、47.86−46.50 | 一致 |
| H-13 | 動詞 23.95→25.98、名詞 36.77→37.04、「名詞は +0.27 点」（5:L174・L177） | 2.03、0.27 | 一致 |
| H-20 | EDA +4.5、AUC +3.3（4:L90） | 57.0−52.5、62.0−58.7 | 一致 |
| H-27 | 動詞 +0.04、名詞 +0.36、行動 +0.35（3:L7） | 表 8 の値から計算 | 一致 |
| H-38 | SSv2 で +1.4、EK100 の名詞 +0.2（5:L317） | 67.9−66.5、58.7−58.5 | 一致 |
| H-22 | 正解と自動の手のマスクの差「約 15.5 points」（2:L38） | 66.4−50.9 | 一致 |
| H-48 | 一般の HOI データからの転移で「mAP で約 40 点」劣化（1:L268） | 54.0−8.3 = 45.7、55.2−13.0 = 42.2 | 40 点を超える。「約 40 点」は丸め |

### 0.5 報告どうしの食い違い

| 項目 | 食い違い |
|---|---|
| 冒頭の答え | R8-1・R8-4・R8-5 は「同じ形の研究は見つからなかった」。R8-2 は VidParse を挙げて「非常に近い先行研究は見つかった」、ただし「完全同型ではない」とも書く |
| 主要な行の重なり | VidParse は R8-2 だけ、G3Ego は R8-1 だけ、IRN は R8-3 だけ、ORViT と EgoHOS の本文は R8-5 だけ、EgoPED の表 6 と KAD は R8-4 だけ |
| H-04 の効果 | R8-2・R8-3 は要旨の改善の値だけを書き、悪化した値を書かない。R8-3 は「少数クラスに比較的効く」と書くが、表 3 では SlowFast の tail の行動が 12.40→12.21（HOCL）、10.21（両方）と下がる |
| H-57 の著者 | R8-5 は「Open surgery tool classification and hand utilization using a multi-camera system」を Goldbraikh ほかと書く。R8-1・R8-4 は Basiev ほか（Goldbraikh は共著者） |
| H-28 の著者 | R8-4 は「Vinay P. Namboodiri/Dessalene 系研究」と書く。Crossref の著者に Namboodiri は無い（§0.3） |
| H-27 の凍結 | R8-3 は図で検出器の重みが凍結されていると書く。起票者が見た抜粋には「end to end で学習」とある |
| H-48 の件数 | 版で違う。arXiv 版の本文は 19,496 画像・手 57,173（R8-1）、論文誌版は 18,450 画像・手 55,655（R8-3）。R8-5 は arXiv 版の表 1 を「15K」、論文誌版の抜粋を「19K6（誤植の可能性）」と書く。repo の hand_seg のインスタンスの合計は 57,173 で、arXiv 版の本文と同じ |
| H-48 の把持の定義 | 論文は「手のセグメンテーションに対する IoU が最大の術具」と書く（R8-1・R8-5）。依頼文の「枠の重なりでほぼ決まる」は repo の注釈の実測（`docs/hts_phase_tool_annotation_stats.md` §0.3）による |
| H-10 の年 | R8-1・R8-4・R8-5 は 2025、R8-2 は「2026 年」 |
| H-52 の表 2 | R8-1 は「対象の手の選択精度 0.943（F1 0.971）」、R8-5 は「0.943／0.996／0.946／0.971（列名は未確認）」 |
| H-66 の第一著者 | R8-1 は Ke Sun と書く。照合先（arXiv）は Kedi Sun |

---

## 1. 系統表

| 系統 | 代表 | 現役度 | 理由 | 本地図の行 |
|---|---|---|---|---|
| 推論時に手・物体・接触の出力を入れる | G3Ego、IRN、EgoPED、ORViT、VidParse、EgoHOS（手のマスクを入力に）、STIN（既有）、Li ほか 2015 | ORViT 自体は不明。STIN・STRG は SSv2 で置き換え済みに近い（ORViT の表 3a）。G3Ego は新興 | 5:L37、1:L53 | H-05、H-13、H-19、H-20、H-21、H-22、H-27、H-38、H-61 |
| 学習時だけ手・物体・接触を使う（補助損失） | Helping Hands、Shiota ほか、SViT（既有）、Tateno ほか | Helping Hands は定番の基準（Ego4D 系。H-02 と arXiv 2503.00986 が比較対象に使う）。Shiota ほかは不明 | 1:L54、4:L22、5:L38 | H-01、H-02、H-04、H-47 |
| 相互作用の知識の蒸留・特権情報 | Radevski ほか、IKD、KAD、Graph Distillation、Garcia ほか、Progressive Privileged KD、Gao ほか | KAD は 2024 年の CVPR の active object 検出の上位手法（R8-4）。ほかは不明か定番の基準（方法論） | 4:L23、5:L39、3:L28 | H-03、H-17、H-31、H-32、H-40〜H-43 |
| 3 次元の手の姿勢・左右の手の動き | HandFormer、H2O、H+O、AssemblyHands、Assembly101、Wen ほか | HandFormer は SOTA 級を主張（Assembly101・H2O） | 4:L24、5:L41 | H-06〜H-08、H-24〜H-26 |
| 接触の状態・HOI 検出 | 100DOH、Lu ほか、Finocchiaro ほか、ENIGMA-51、ENIGMA-360、HOI-Synth、Sequential Voting | 100DOH は定番の基準（疑似教師の作成に使われる） | 1:L58、5:L35・L43〜L44 | H-09〜H-12、H-23、H-35、H-36 |
| active object・next active object・予測 | Furnari ほか 2017、Jiang ほか、NAOGAT、ANACTO、AFF-ttention、StillFast、Ego4D STA、InAViT、接触の表現による予測、Ego-OMG | 概念は定番、個々のモデルは置き換えが進む（R8-4）。InAViT は新興 | 4:L25、5:L40・L42 | H-14〜H-16、H-28〜H-30、H-33、H-34、H-37 |
| 手・物体の画素の分割 | EgoHOS、VISOR、EgoSurgery-HTS、Exo2EgoDVC | EgoHOS は定番の基準（HOI-Synth が評価に使う） | 1:L57、5:L36 | H-13、H-18、H-39、H-48 |
| 映像言語モデルと手・物体の手がかり | Tateno ほか、ICLR 2025 の二件 | 新興 | 3:L80・L143 | H-02、H-44、H-45 |
| 手術: 術具の使い方・相互作用・手 → 工程・術具 | Shimizu ほか、Park ほか、IIA-Net、ESIP、Basiev ほか、Goldbraikh ほか、EndoNet（既有）、MTRCNet-CL（既有） | EndoNet・MTRCNet-CL は定番の基準（R8-4）か置き換え済み（R8-5）で報告が割れる。ESIP は新興 | 4:L29〜L30、5:L45 | H-52〜H-60 |
| 一人称の開放手術のデータセット | EgoSurgery-Phase、EgoSurgery-Tool、EgoSurgery-HTS | データセット | 4:L31、5:L46 | H-48〜H-51 |
| 情報の漏れ（stacking・入れ子の交差検証） | Leak-Free Cross-Validated Stacking | 方法論 | 5:L47 | H-46 |

---

## 2. 行の一覧

| ID | 文献 | 書誌 ID | 掲載先 | 方向 | 読んだ範囲 | 出所 |
|---|---|---|---|---|---|---|
| H-01 | Chuhan Zhang, Ankush Gupta, Andrew Zisserman 2023, Helping Hands: An Object-Aware Ego-Centric Video Recognition Model | arXiv 2308.07918、DOI 10.1109/ICCV51070.2023.01278 | ICCV 2023（査読つき） | 3、5、7 | 本文（R8-5 は 1〜6 節と表 1〜7） | 5:L140〜L162、4:L61〜L78、1:L69〜L96 |
| H-02 | Masatoshi Tateno, Alexandros Stergiou, Risa Shinoda, Yoichi Sato, Dima Damen 2026, Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues? | arXiv 2607.08514 | プレプリント | 3、7 | 要旨と HTML の抜粋 | 5:L275〜L282、1:L98〜L110、4:L310 |
| H-03 | Gorjan Radevski, Dusan Grujicic, Marie-Francine Moens, Matthew Blaschko, Tinne Tuytelaars 2023, Multimodal Distillation for Egocentric Action Recognition | arXiv 2307.07483 | ICCV 2023（査読つき） | 3、4、5 | 本文（R8-5 は 1〜4.1.4 節と表 1〜4） | 5:L319〜L336、1:L112〜L133、4:L139〜L149 |
| H-04 | Tsukasa Shiota, Motohiro Takagi, Kaori Kumagai, Hitoshi Seshimo, Yushi Aono 2024, Egocentric Action Recognition by Capturing Hand-Object Contact and Object State | DOI 10.1109/WACV57701.2024.00641（R8-4。R8-1 は ID 不明） | WACV 2024（査読つき） | 3、5、7 | 本文（表 1〜4） | 4:L38〜L59、1:L135〜L159 |
| H-05 | Marko Haralović, Akash Ramakrishnan, Estefania Talavera Martinez 2026, G3Ego: Gaze-Guided Graphs for Egocentric Action Understanding | arXiv 2608.20157 | プレプリント | 3 | 本文（表 1〜5） | 1:L161〜L186 |
| H-06 | Takehiko Ohkawa ほか 2023, AssemblyHands: Towards Egocentric Activity Understanding via 3D Hand Pose Estimation | arXiv 2304.12301 | CVPR 2023（査読つき） | 3、7 | 要旨のみ | 1:L188〜L192 |
| H-07 | Sener ほか 2022, Assembly101: A Large-Scale Multi-View Video Dataset for Understanding Procedural Activities | arXiv 2203.14712 | CVPR 2022（査読つき） | 3 | 本文の抜粋（表 8 の段落） | 5:L203〜L210、1:L194〜L200 |
| H-08 | Md Salman Shamil, Dibyadip Chatterjee, Fadime Sener, Shugao Ma, Angela Yao 2024, On the Utility of 3D Hand Poses for Action Recognition（HandFormer） | arXiv 2403.09805、DOI 10.1007/978-3-031-72658-3_25 | ECCV 2024（査読つき） | 3 | 本文（R8-4 は表 1・4・5） | 4:L97〜L112、5:L193〜L201、1:L194〜L200 |
| H-09 | Yao Lu, Walterio W. Mayol-Cuevas 2021, Egocentric Hand-object Interaction Detection and Application | arXiv 2109.14734（R8-5 が重なる版とした ID は照合で著者が違うと分かり、H-62 に分けた） | プレプリント | 3 | 要旨のみ | 5:L248〜L255、1:L202〜L206 |
| H-10 | Antonio Finocchiaro, Alessandro Sebastiano Catinello, Michele Mazzamuto, Rosario Leonardi, Antonino Furnari, Giovanni Maria Farinella 2025, A Real-Time System for Egocentric Hand-Object Interaction Detection in Industrial Domains | arXiv 2507.13326 | ICIAP 2025（arXiv の注記による） | 3 | 要旨のみ | 5:L239〜L246、4:L211〜L221、1:L208〜L212 |
| H-11 | Ragusa ほか 2024, ENIGMA-51: Towards a Fine-Grained Understanding of Human-Object Interactions in Industrial Scenarios | arXiv 2309.14809 | WACV 2024（査読つき） | 3 | 要旨と本文の一部 | 1:L214〜L218、3:L131 |
| H-12 | Rosario Leonardi, Antonino Furnari, Francesco Ragusa, Giovanni Maria Farinella 2024, Are Synthetic Data Useful for Egocentric Hand-Object Interaction Detection? | arXiv 2312.02672 | ECCV 2024（査読つき） | 3 | 要旨と本文の抜粋 | 5:L266〜L273、1:L220〜L223 |
| H-13 | Lingzhi Zhang, Shenghao Zhou, Simon Stent, Jianbo Shi 2022, Fine-Grained Egocentric Hand-Object Segmentation: Dataset, Model, and Applications（EgoHOS） | arXiv 2208.03826 | ECCV 2022（査読つき） | 3 | 本文と補足資料の一部（R8-5） | 5:L164〜L183、1:L225〜L228 |
| H-14 | Antonino Furnari, Sebastiano Battiato, Kristen Grauman, Giovanni Maria Farinella 2017, Next-Active-Object Prediction from Egocentric Videos | DOI 10.1016/j.jvcir.2017.10.004 | Journal of Visual Communication and Image Representation（査読つき） | 3、7 | 要旨と抜粋 | 4:L179〜L188、5:L286・L293、1:L235〜L238 |
| H-15 | Sanket Thakur, Cigdem Beyan, Pietro Morerio, Vittorio Murino, Alessio Del Bue 2024, Leveraging Next-Active Objects for Context-Aware Anticipation in Egocentric Videos（NAOGAT） | arXiv 2308.08303 | WACV 2024 | 3 | 関連研究の抜粋 | 1:L240〜L242、5:L289 |
| H-16 | Sanket Thakur ほか, Anticipating Next Active Objects for Egocentric Videos（ANACTO。R8-5 は next active object の予測の論文群として三件をまとめた。残りの二件は H-64・H-65。著者は照合先の値） | arXiv 2302.06358 | 報告に記載なし | 3 | 要旨と抜粋 | 5:L284〜L295 |
| H-17 | Zhiyi Gao ほか 2022, Learning Using Privileged Information for Zero-Shot Action Recognition | arXiv 2206.08632 | ACCV 2022 | 5 | 要旨と関連研究の節 | 1:L321〜L324 |
| H-18 | Takehiko Ohkawa ほか, Exo2EgoDVC（著者 7 名の並びは R8-1 の記載: Ohkawa, Yagi, Nishimura, Furuta, Hashimoto, Ushiku, Sato） | arXiv 2311.16444 | 年・掲載先は未確認 | 3 | 本文の一部（検索結果の抜粋） | 1:L230〜L233 |
| H-19 | 2026, VidParse: Online Parsing of Egocentric Procedures Like a Pro（年は R8-2 の「ECCV 2026」。副題は起票者が arXiv で確かめた。著者は報告に記載なし） | 報告に記載なし。起票者が特定: arXiv 2608.27562 | R8-2 は ECCV 2026 と書く（起票者は未確認） | 3 | 報告に記載なし | 2:L5・L25・L34・L46・L52・L54 |
| H-20 | Shih-Po Lee, Zijia Lu, Zekun Zhang, Minh Hoai, Ehsan Elhamifar 2024, Error Detection in Egocentric Procedural Task Videos（EgoPED） | DOI 10.1109/CVPR52733.2024.01765 | CVPR 2024（査読つき） | 3、7 | 本文（AOD の部、表 6、領域の移し替えの記述） | 4:L80〜L95、2:L29、3:L9・L24 |
| H-21 | STIN／Something-Else（依頼文の既有） | 報告に記載なし | CVPR 2020 | 4 | 報告に記載なし | 4:L286、2:L31 |
| H-22 | Bambach ほか（題名・年の記載なし） | 報告に記載なし | 報告に記載なし | 3 | 報告に記載なし | 2:L38 |
| H-23 | 100DOH（Understanding Human Hands in Contact at Internet Scale、Shan ほか、依頼文の種） | 報告に記載なし | CVPR 2020（R8-5） | 3 | R8-1 は要旨未読 | 5:L35、2:L15・L50 |
| H-24 | Taein Kwon ほか 2021, H2O: Two Hands Manipulating Objects for First Person Interaction Recognition | ID 不明 | ICCV 2021（査読つき） | 3 | 要旨とデータセットの記述 | 4:L200〜L209、3:L30・L86 |
| H-25 | Tekin, Bogo, Pollefeys 2019, H+O: Unified Egocentric Recognition of 3D Hand-Object Poses and Interactions | arXiv 1904.05349 | CVPR 2019（査読つき） | 3 | 要旨と抜粋 | 5:L212〜L219、2:L46 |
| H-26 | Wen ほかの階層の temporal transformer、Kapidis ほか、EgoExoLearn（R8-2 だけに名前がある三件） | 報告に記載なし | 報告に記載なし | 3 | 報告に記載なし | 2:L38・L46・L50 |
| H-27 | Jian Ma, Dima Damen 2022, Hand-Object Interaction Reasoning（IRN） | 報告に記載なし。起票者が特定: arXiv 2201.04906 | 報告に記載なし | 3 | 報告に記載なし | 3:L7・L23・L32〜L34・L84 |
| H-28 | Eadom Dessalene ほか, Forecasting Action Through Contact Representations From First Person Video（著者は照合先の値。R8-4 の記載は §0.5） | DOI 10.1109/TPAMI.2021.3055233 | IEEE TPAMI | 3 | 要旨・書誌 | 4:L114〜L125 |
| H-29 | Eadom Dessalene ほか, Egocentric Object Manipulation Graphs（Ego-OMG。著者と題名は照合先の値） | arXiv 2006.03201 | 報告に記載なし | 3 | 要旨 | 4:L127〜L137 |
| H-30 | Jiang ほか 2021, Predicting short-term next-active-object through visual attention and hand position | DOI 10.1016/j.neucom.2020.12.069 | Neurocomputing | 3 | 要旨 | 4:L190〜L198 |
| H-31 | Haoran Wang ほか 2025, Distilling interaction knowledge for semi-supervised egocentric action recognition（IKD） | DOI 10.1016/j.patcog.2024.110927 | Pattern Recognition | 3、5 | 要旨・出版社の概要 | 4:L151〜L162 |
| H-32 | Dejie Yang, Yang Liu 2024, Active Object Detection with Knowledge Aggregation and Distillation from Large Models（KAD） | ID 不明 | CVPR 2024（査読つき） | 3、5 | 本文の概要・CVF の頁 | 4:L164〜L177 |
| H-33 | Debaditya Roy, Ramanathan Rajendiran, Basura Fernando 2024, Interaction Region Visual Transformer for Egocentric Action Anticipation（InAViT） | arXiv 2211.14154 | WACV 2024（査読つき） | 3 | 要旨と HTML の抜粋 | 5:L185〜L191 |
| H-34 | StillFast、Ego4D の Short-Term Anticipation（STA）と FHO | 報告に記載なし | 報告に記載なし | 3 | 報告に記載なし | 3:L56・L98、4:L334、2:L42 |
| H-35 | 2026, ENIGMA-360: An Ego-Exo Dataset for Human Behavior Understanding in Industrial Scenarios（年は R8-5 の記載。著者は報告に記載なし） | arXiv 2603.09741 | プレプリント | 3 | 要旨と抜粋 | 5:L231〜L237 |
| H-36 | Fu ほか, Sequential Voting with Relational Box Fields for Active Object Detection（著者は R8-3 の記載。R8-5 は著者を書かない） | arXiv 2110.11524 | 報告に記載なし | 3 | 抜粋（4.2 節） | 5:L257〜L264、3:L52 |
| H-37 | Ragusa ほか, MECCANO（WACV 2021 版〔著者は Ragusa, Furnari, Livatino, Farinella。R8-5〕と多モーダル版〔著者は報告に記載なし〕） | arXiv 2010.05654、arXiv 2209.08691、DOI 10.1016/j.cviu.2023.103764 | WACV 2021（査読つき）、CVIU 235（2023） | 3 | 要旨とプロジェクトの頁 | 5:L221〜L229、1:L338、3:L123 |
| H-38 | Herzig, Ben-Avraham, Mangalam, Bar, Chechik, Rohrbach, Darrell, Globerson 2022, Object-Region Video Transformers（ORViT） | arXiv 2110.06915 | CVPR 2022（査読つき） | 4（EK100 は 3） | 本文（1〜4.4 節、表 1〜3） | 5:L299〜L317、4:L326 |
| H-39 | VISOR（EPIC-KITCHENS の上の手と物体のマスク） | 報告に記載なし | 報告に記載なし | 3 | 報告に記載なし | 4:L334、3:L72 |
| H-40 | Wang ほか, SAP（物体検出の特徴を特権の枝にする） | 報告に記載なし | 報告に記載なし | 3、5 | 報告に記載なし | 3:L28 |
| H-41 | Luo ほか 2018, Graph Distillation for Action Detection with Privileged Modalities | arXiv 1712.00108 | ECCV 2018（査読つき） | 5 | 要旨と抜粋 | 5:L342・L348 |
| H-42 | Garcia, Morerio, Murino 2019, Learning with privileged information via adversarial discriminative modality distillation | ID 不明（R8-5 が会議版とした ID は照合で題名が違うと分かり、H-63 に分けた） | IEEE TPAMI 42(10)（査読つき） | 5 | 要旨と抜粋 | 5:L343 |
| H-43 | Progressive privileged knowledge distillation for online action detection | ID 不明（ScienceDirect の記事番号 S0031320322002229） | Pattern Recognition 2022 | 5 | 要旨と抜粋 | 5:L344・L349 |
| H-44 | Baoqi Pei ほか, Modeling Fine-Grained Hand-Object Dynamics for Egocentric Video Representation Learning（著者は照合先の値） | 報告に記載なし。起票者が照合の結果で特定: arXiv 2503.00986（R8-1 が §1・§4 で「Helping Hands を比較対象に使う」と書いた ID。題名が一致した） | ICLR 2025（R8-3） | 3 | 報告に記載なし | 3:L80 |
| H-45 | Do Egocentric Video-Language Models Truly Understand Hand-Object Interactions? | 報告に記載なし | ICLR 2025（R8-3） | 3、7 | 報告に記載なし | 3:L143 |
| H-46 | 2026, Leak-Free Cross-Validated Stacking with Per-Architecture Calibration for Sand-Boil Segmentation in Earthen Levees（年は R8-5 の記載。著者は報告に記載なし） | arXiv 2607.25367 | プレプリント | 6 | 抜粋のみ | 5:L354〜L360 |
| H-47 | Li ほか 2025（Simultaneous Detection and Interaction Reasoning for Object-Centric Action Recognition。依頼文の既有）と SViT（既有） | 報告に記載なし | TMM 2025（R8-4） | 4 | 報告に記載なし | 4:L34 |
| H-48 | Nathan Darjana, Ryo Fujii, Hideo Saito, Hiroki Kajita 2025, EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos | arXiv 2503.18755、DOI 10.1049/htl2.70049 | Healthcare Technology Letters 12(1) e70049（査読つき） | 1 | 本文（R8-1 は arXiv 版） | 1:L244〜L268、4:L259〜L269、5:L58〜L69、3:L159 |
| H-49 | Ryo Fujii, Hideo Saito, Hiroki Kajita 2024, EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos | arXiv 2406.03095 | プレプリント | 1 | 要旨と本文の抜粋 | 5:L71〜L77、4:L271〜L280、1:L270〜L274 |
| H-50 | Ryo Fujii, Masashi Hatano, Hideo Saito, Hiroki Kajita 2024, EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos | arXiv 2405.19644、DOI 10.1007/978-3-031-72089-5_18 | MICCAI 2024（査読つき） | 1 | 要旨のみ | 4:L274〜L277、1:L276〜L280 |
| H-51 | Wu, Holm, Chen ほか 2026, SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos | arXiv 2602.05638 | プレプリント | 1、2 | 本文の抜粋（サブ調査） | 5:L79〜L86 |
| H-52 | Shimizu, Hachiuma, Kajita, Takatsume, Saito 2021, Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera | DOI 10.3390/jimaging7020015 | J. Imaging 7(2):15（査読つき） | 2（視点は方向 1 に近い） | 方法の節まで（R8-5 のサブ調査） | 5:L99〜L106、4:L236〜L246、1:L282〜L295 |
| H-53 | Bogyu Park ほか 2022／2023, Visual modalities-based multimodal fusion for surgical phase recognition | DOI 10.1007/978-3-031-18814-5_2（MMMI 2022）、DOI 10.1016/j.compbiomed.2023.107453（Comput Biol Med 166）、訂正 DOI 10.1016/j.compbiomed.2026.111850 | 査読つき | 2 | 要旨とハイライト | 5:L90〜L97、1:L297〜L300 |
| H-54 | Yuan ほか 2022, IIA-Net: Anticipation for surgical workflow through instrument interaction and recognized signals | DOI 10.1016/j.media.2022.102611 | Medical Image Analysis | 2 | 要旨 | 4:L223〜L234 |
| H-55 | Yixuan Qiu ほか, ESIP: Explicit Surgical Instrument Prompting for Surgical Workflow Recognition（術具の分割から術具ごとの視覚のプロンプトを作る。題名と著者は照合先の値） | DOI 10.1109/JBHI.2025.3625420 | JBHI 2025 | 2 | 報告に記載なし | 4:L322 |
| H-56 | 2025, Enhancing open-surgery gesture recognition using 3D pose estimation（開放手術のジェスチャ認識に 3 次元の手と術具の姿勢を使う研究。年は R8-5 の記載、題名は R8-5 の参照の一覧。著者は報告に記載なし） | DOI 10.1007/s11548-025-03564-1 | Int J CARS 2025（査読つき） | 2 | 抜粋のみ | 5:L115〜L121 |
| H-57 | Kristina Basiev, Adam Goldbraikh, Carla M. Pugh, Shlomi Laufer 2022, Open surgery tool classification and hand utilization using a multi-camera system | arXiv 2111.06098、DOI 10.1007/s11548-022-02691-3 | Int J CARS 17(8)（査読つき） | 2 | 要旨 | 4:L248〜L257、1:L317〜L319、5:L108〜L113 |
| H-58 | Adam Goldbraikh, Anne-Lise D'Angelo, Carla M. Pugh, Shlomi Laufer 2022, Video-based fully automatic assessment of open surgery suturing skills | 報告に記載なし。起票者が特定: arXiv 2110.13972 | Int J CARS 17(3)（査読つき） | 2 | 報告に記載なし | 3:L163 |
| H-59 | Goodman ほか（行動分割・術具・手・キーポイントの多タスク）、Fujii ほかの開放手術の術具検出（R8-3 は「survey 部分」と書く） | 報告に記載なし | 報告に記載なし | 2 | 報告に記載なし | 3:L163 |
| H-60 | Ege Özsoy ほか 2025, EgoExOR: An Ego-Exo-Centric Operating Room Dataset for Surgical Activity Understanding（R8-1 は手術の手の信号の三件をまとめた。残りの二件は H-66・H-67。題名は照合先の値） | arXiv 2505.24287 | NeurIPS 2025 Datasets track | 2 | 要旨か抜粋 | 1:L302〜L315、5:L123〜L136 |
| H-61 | Li ほか 2015, Delving into Egocentric Actions | ID 不明（本文は PMC4784702） | CVPR 2015 | 3、7 | 本文の一部（検索結果の抜粋） | 1:L326〜L329 |
| H-62 | Yao Lu, Yanan Liu 2022, Egocentric Hand-object Interaction Detection（年は arXiv の投稿年。著者と題名は照合先の値） | arXiv 2211.09067 | プレプリント | 3 | 報告に記載なし（R8-5 は H-09 と内容が大きく重なる版と書き、2211.09067 版の抜粋に MS-TCN との比較の記述があると書く） | 5:L249・L255 |
| H-63 | Nuno Garcia, Pietro Morerio, Vittorio Murino 2018, Modality Distillation with Multiple Stream Networks for Action Recognition（年は arXiv の投稿年。題名は照合先の値） | arXiv 1806.07110 | 報告に記載なし（R8-5 は H-42 の会議版と書く） | 5 | 報告に記載なし | 5:L343 |
| H-64 | Sanket Thakur ほか, Enhancing Next Active Object-based Egocentric Action Anticipation with Guided Attention（H-16 から分けた。著者は照合先の値） | arXiv 2305.12953 | ICIP 2023（R8-5） | 3 | 要旨と抜粋 | 5:L284〜L295 |
| H-65 | Lorenzo Mur-Labadia ほか, AFF-ttention! Affordances and Attention models for Short-Term Object Interaction Anticipation（H-16 から分けた。著者は照合先の値） | arXiv 2406.01194 | ECCV 2024（R8-5） | 3 | 要旨と抜粋 | 5:L284〜L295 |
| H-66 | Kedi Sun, Le Zhang 2026, YOLOv10-Based Multi-Task Framework for Hand Localization and Laterality Classification in Surgical Videos（H-60 から分けた。題名と著者は照合先の値。R8-1 は第一著者を Ke Sun と書く） | arXiv 2602.18959 | TrackRAD@MICCAI 2026（Semantic Scholar の表記。R8-1） | 2 | 要旨か抜粋 | 1:L302〜L315、5:L123〜L136 |
| H-67 | Michael Zhang ほか 2021, Using Computer Vision to Automate Hand Detection and Tracking of Surgeon Movements in Videos of Open Surgery（H-60 から分けた） | arXiv 2012.06948 | AMIA（R8-1） | 2 | 要旨のみ | 1:L302〜L315 |

---

## 3. 近さ（距離の軸）

| ID | 視点 | ドメイン | 課題の形 | 推論の規約 | データ規模 | モデルの状態（凍結の範囲） |
|---|---|---|---|---|---|---|
| H-01 | 一人称 | 非医療 | 映像クリップと文 → 映像と言語の埋め込み。補助として左右の手 2 個と物体の枠、物体名を予測。下流はゼロショットの行動分類（EGTEA）、検索（EK100-MIR）、EgoMCQ、NLQ/MQ | offline（クリップから 4 フレーム） | EgoClip 380 万クリップ、1,600 万フレームに 100DOH を適用 | 100DOH は凍結した上流で、出力は学習時の補助損失の教師だけ。映像・言語の符号器も凍結し、object-aware decoder・問い合わせ・言語の射影だけを学習。推論は RGB だけ |
| H-02 | 一人称 | 非医療 | 映像 → 動詞。手だけ・物体だけを残すよう inpainting した映像でも評価。100DOH の枠を学習時のマスクに使う | 報告に記載なし | EgoClip で学習、DEHOI で評価 | 同時に学習 |
| H-03 | 一人称（EK100）と手元の映像（SSv2） | 非医療 | RGB → 行動。教師は RGB・光学フロー・音・物体検出（物体を区別しない「hands」「objects」の枠を STLT で符号化）。EK100 の実験では物体検出を使わない | offline | 報告に記載なし | 教師はモダリティごとに別に学習。生徒（Swin-T）は全体を学習し、推論は RGB だけ |
| H-04 | 一人称 | 非医療 | RGB → 行動。学習時だけ、手と接触物体の枠で隠した映像を別の枝に与えて相互学習（HOCL）。物体の状態の擬似分布も学習（OSL） | クリップ単位（online の制約の報告なし） | EGTEA（学習集合から無作為の 1,000 本、3 分割の平均）、MECCANO（8,839 区間・61 クラス）、EK-100（55,191 区間） | 検出器は凍結。二つの行動モデルを同時に学習。推論は RGB だけ |
| H-05 | 一人称 | 非医療（組立・調理） | 疎なフレーム → 行動の認識と予測。凍結した DINOv3・GroundingDINO・VLM の出力からグラフを作り、左右それぞれに手の枠・左右の指示子・接触物体の枠とクラス番号（計 20 次元）を加える。接触は手と物体の枠が重なれば接触 | 認識は区間単位。予測は 1 秒前までの観測から | MECCANO 20 本、EGTEA Gaze+ 10,321 区間 | 上流はすべて凍結し、推論時に出力を入力。グラフ埋め込みと時系列集約だけを学習 |
| H-07、H-08 | 一人称と多視点 | 非医療（組立、日常の操作） | 3 次元の手の関節の軌跡（左右を分ける）と疎な RGB → 行動 | クリップ単位（online ではない） | Assembly101、H2O | 推定済みか正解の姿勢を入力にする |
| H-10 | 一人称 | 非医療（工業） | 接触の状態の認識が接触と判定したときだけ物体検出を起動し、active object を検出・分類 | online（ストリーミング、30fps） | ENIGMA-51 | 二つのモジュールを順につなぐ（Mamba＋EfficientNetV2 → YOLOWorld） |
| H-13 | 一人称 | 非医療 | 画像 → 左手、右手、左手の物体、右手の物体、両手の物体（EgoSurgery-HTS と同じ 5 クラスの構成）と接触境界。下流は手の状態分類と行動認識 | 報告に記載なし | 11,243 枚（約 1,000 本の動画から疎に抽出）。手の状態分類は EPIC の 3,531 フレーム | 分割は段階型（手 → 接触境界 → 物体）。下流は手のマスクを入力チャネルに加え、受け取り側を学習し直す |
| H-19 | 一人称 | 非医療（手順） | 凍結した手と物体の検出器の相互作用の枠に入る、凍結 DINOv2 のパッチ特徴を集めて手順を解析。受け取り側はプロトタイプの照合とグラフで制約したデコーダ | online（各フレームを一度だけ処理） | EgoPER、GTEA | 検出器と DINOv2 は凍結。学習なし |
| H-20 | 一人称 | 非医療（調理・手順作業） | off-the-shelf の行動分割のモデルと、active object の検出器から作る相互作用のグラフ（物体が節、相互作用が辺、GCN）で、行動分割と手順の誤り検出 | offline（論文が online ではないと明記） | EgoPER | 検出器は独立の部品で、その推定を渡す |
| H-27 | 一人称 | 非医療 | 左右の手と、それぞれに対応する active object の枠の軌跡と ROI の特徴 → 相互作用の Transformer → RGB の行動の表現に加える | 報告に記載なし | EPIC-KITCHENS-100、Something-Else | §0.5 のとおり、凍結の範囲は報告と抜粋で食い違う |
| H-28 | 一人称 | 非医療 | 未来の接触の分布（Contact Anticipation Maps）と次の active object の分割を推定し、行動の予測に使う | 予測 | EPIC-KITCHENS | 推定した相互作用の表現を下流に使う |
| H-29 | 一人称 | 非医療 | 手が物体に接触する／離れる時点で区間を作り、物体の操作のグラフで行動を予測 | 予測 | 報告に記載なし | 相互作用の表現を中間の表現に使う |
| H-31 | 一人称 | 非医療 | 少量の行動ラベルの映像から手と物体の時空間の関係を教師に学習させ、ラベルの無い映像に疑似ラベルを作って生徒を学習 | 報告に記載なし | 報告に記載なし | 教師と生徒。相互作用の知識は主に学習・疑似ラベル作りの段で使う |
| H-32 | 一人称 | 非医療 | 同じカテゴリの物体が複数写る中から、状態が変わる active object を検出。相互作用の意味と見た目の事前知識を教師の問い合わせに集め、生徒の検出器へ予測と注意を蒸留 | 報告に記載なし | Ego4D、EPIC-KITCHENS、MECCANO、100DOH | 推論時は追加の知識の入力が要らない |
| H-33 | 一人称 | 非医療 | 手と物体の領域の外観の変化を空間の cross-attention で相互作用トークンにし、次の行動を予測 | 過去のみ（予測） | EK100、EGTEA Gaze+ | 受け取り側（MotionFormer）は学習する |
| H-36 | 一人称 | 非医療 | 画像と手 → active object の枠。MECCANO では、手の枠と「中心が最も近い active object を各手に割り当てる」規則で作った疑似ラベルで学習し直す | 画像単位 | MECCANO | 報告に記載なし |
| H-38 | 三人称と一人称（EK100） | 非医療 | 映像と物体の枠（追跡は SORT）→ 行動。同じ基盤に ORViT ブロックを加えるかだけを変える | offline（クリップ単位） | SSv2 174 クラス、EK100、Diving48、AVA | 検出器（Faster R-CNN）と重みを共有しない。推論時に検出の枠を入力。受け取り側は学習する |
| H-46 | 該当なし | 非医療（画像の分割） | 複数の分割モデルの出力をメタ学習器で束ねる（stacking） | 該当なし | 報告に記載なし | 入れ子の交差検証で上流の予測を作る |
| H-48 | 一人称 | 開放手術 | 画像 → 術具・手・手と術具のインスタンスセグメンテーション。マスクは術具と手の枠を SAM に与えて作り、人手で確認・修正。手のマスクは自分・他者 × 左・右の 4 種、手と術具は左手・右手・左手の物体・右手の物体・両手の物体の 5 種。他者の手は把持のクラスに含まない | 画像単位 | 版により 18,450〜19,496 画像（§0.5）。術具 14 種 | 該当なし |
| H-49 | 一人称 | 開放手術 | 画像 → 術具と手の枠。術具と工程の共起行列（図 4）を示し「術具の情報は工程認識に役立つかもしれない」と書くが、融合の実験はない | 画像単位 | EgoSurgery-Phase の 21 本のうち 15 本、15,437 枚、術具の枠 49,652（15 種）、手の枠 46,320（自分の左右・他者の左右）。動画単位の分割 | 該当なし |
| H-50 | 一人称 | 開放手術 | 工程認識。視線で MAE のマスクを導く | 報告に記載なし | 9 工程、約 15 時間 | 報告に記載なし |
| H-51 | 一人称（EgoSurgery の部分） | 開放手術を含む | 手術の映像の基盤モデル → 工程 | 報告に記載なし | 報告に記載なし | 手・術具の信号を使わない |
| H-52 | 一人称 | 開放手術 | Faster R-CNN で術具と手を検出し、術具の枠と重なりが最大の手を規則で選び、その手の切り出しの時系列を ResNet-18 と LSTM で分類（形の似たはさみと持針器） | 推論時に手の情報を使う | 報告に記載なし | 独立した段階をつなぐ。凍結した把持モデルではない |
| H-53 | 腹腔鏡（PETRAW はシミュレータ） | 低侵襲手術（幽門側胃切除） | 術具の分割から動きと術具どうしの関係の指標（VKI）を作り、CNN 特徴と融合して工程を認識 | 推論時に融合 | 私有データと PETRAW | 報告に記載なし |
| H-54 | 腹腔鏡 | 低侵襲手術 | 術具どうし・術具と周囲の解剖の関係をモデル化し、認識した術具・工程の信号と組み合わせて工程を予測 | causal な dilated MS-TCN（online に近い） | 報告に記載なし | 多タスク・同時学習に近い。手は扱わない |
| H-56 | 報告に記載なし | 開放手術 | 映像と 3 次元の手・術具の姿勢 → ジェスチャ（工程ではない）。MS-TCN++、LTContext | 報告に記載なし | 報告に記載なし | 姿勢推定器は上流で別に学習 |
| H-57 | トップビューと接写の 2 台（三人称） | 模擬手術（腸管修復） | YOLOv5 で術具と手を検出し、LSTM で術具を分類。どちらの手がどの術具を持つかを推定 | 30 fps・1 秒窓と 3 fps・40 秒窓の 2 種 | 48 人 | 段階型 |
| H-58 | 報告に記載なし | 模擬の開放手術（縫合） | 術具の位置と、手と術具の相互作用（どの手がどの術具を使うか）を一つの YOLO の分けたヘッドで検出し、動きの指標で技能を評価（起票者の確かめによる） | 報告に記載なし | 25 人（起票者の確かめによる） | 二つの課題を一つのネットワークで同時に学習 |
| H-60 | 一人称と三人称 | 手術室・外傷処置・開放手術 | EgoExOR は装着型グラスの手の姿勢と視線を入力にして手術室のシーングラフを生成。Sun ほかは手の枠と左右（手が出力）。Zhang ほかは手の検出と追跡 | 報告に記載なし | 報告に記載なし | 該当なし |
| ほかの行 | §2 の方向と §6 の記述のとおり。視点・規約・規模・状態は報告に記載なし | — | — | — | — | — |

---

## 4. 手法の位置

| ID | 系統 | 現役度と理由 | どのベンチマークの話か | 本研究の条件で測られたか（少数動画／online／一人称） |
|---|---|---|---|---|
| H-01 | 学習時だけ使う | 定番の基準（H-02 と arXiv 2503.00986 が比較対象に使う。1:L80、5:L149） | EGTEA・EK100-MIR・EgoMCQ・VISOR | 一人称のみ |
| H-02 | 学習時だけ使う、映像言語モデル | 新興 | DEHOI・STATUS Bench | 一人称のみ |
| H-03 | 蒸留 | R8-1 は不明、R8-5 は新興（著者以外の採用は arXiv 2504.08578 などの引用にとどまる） | SSv2、Something-Else、EK100 | 一人称（EK100）のみ。EK100 では物体検出を使っていない |
| H-04 | 学習時だけ使う | 不明（R8-4）。G3Ego の表 2 に比較対象として載る（R8-1） | EGTEA、MECCANO、EK-100 | 一人称。online ではない |
| H-05 | 推論時に入れる、グラフ、視線 | 新興 | MECCANO、EGTEA Gaze+ | 一人称。MECCANO は 20 本。予測は過去のみ |
| H-08 | 3 次元の手の姿勢 | SOTA 級を主張。R8-4 は 2024 年以後の複数の比較表を満たさず不明とする | Assembly101、H2O | 一人称を含む。online ではない |
| H-10 | 接触の状態 | 報告に記載なし | ENIGMA-51 | 一人称、online |
| H-13 | 手・物体の分割 | 定番の基準（H-12 が評価データに使う） | EgoHOS、EPIC の部分集合 | 一人称 |
| H-19 | 推論時に入れる | 報告に記載なし | EgoPER、GTEA | 一人称、online |
| H-20 | 推論時に入れる、グラフ | 報告に記載なし | EgoPER | 一人称。offline |
| H-27 | 推論時に入れる | 報告に記載なし | EPIC-KITCHENS-100、Something-Else | 一人称 |
| H-31 | 蒸留 | 不明（2025 年の Pattern Recognition） | 報告に記載なし | 一人称、少量のラベル |
| H-32 | 蒸留（検出の側） | 2024 年の CVPR の active object 検出の上位手法 | Ego4D、EPIC-KITCHENS、MECCANO、100DOH | 一人称 |
| H-33 | 予測 | 新興（当時の SOTA を主張） | EK100、EGTEA Gaze+ | 一人称、過去のみ |
| H-38 | 推論時に入れる | 不明（直近 2 年の比較表を未確認）。STIN・STRG は SSv2 で置き換え済み（表 3a） | SSv2、EK100、Diving48、AVA | EK100 は一人称 |
| H-43 | 特権情報 | 報告に記載なし | online の行動検出 | online |
| H-48 | 手・物体の分割、データセット | データセット | EgoSurgery-HTS | 一人称・開放手術。下流の工程・検出での利用は 0 件 |
| H-51 | 基盤モデル | 新興 | EgoSurgery の工程 | 一人称・開放手術 |
| H-52 | 手術: 手 → 術具 | 不明 | 報告に記載なし | 一人称・開放手術。下流は術具の分類で、検出 mAP 全体の評価ではない。工程は扱わない |
| H-53、H-54 | 手術: 術具 → 工程 | 不明 | 報告に記載なし | 腹腔鏡。手は扱わない |
| H-57、H-58 | 手術: 手と術具の使用 | 不明（直接の後続が少ない。R8-4） | 報告に記載なし | 模擬の開放手術。下流の工程は扱わない |
| ほかの行 | §1 の系統 | 報告に記載なし | 報告に記載なし | 報告に記載なし |

---

## 5. 証拠の質

| ID | 何と何を比べた差か | その要素だけを変えた比較か | 基準の強さ | seed・分割・検定 | 著者以外の追試・採用 |
|---|---|---|---|---|---|
| H-01 | (i) 損失 L_Ego だけと、L_box・L_word を加えた場合（表 1。表 4 の Ours*‡ と Ours*）。(ii) 物体の枠だけと手＋物体の枠（表 5）。(iii) 疑似の枠を 256p と 640p から作った場合（表 2） | 表 1・表 5 は損失と予測対象だけを変える | 当時の強いモデル（LaViLa-L） | 記述なし | H-02 と arXiv 2503.00986 が比較対象に使う |
| H-03 | RGB だけの基準、RGB と物体検出を推論時に使う教師、その教師から蒸留した RGB だけの生徒。Omnivore（全モダリティの同時学習）との比較（表 4） | 教師のモダリティだけを変える | 中程度（Swin-T） | 記述なし。テスト集合の無いデータでは最終エポックのモデルを報告 | 報告に記載なし |
| H-04 | 同じ backbone で、HOCL・OSL の有無を変える | はい | SlowFast と Swin-B（Kinetics で事前学習） | EGTEA は 3 分割の平均。検定は確認できず | 報告に記載なし |
| H-05 | 同じ G3Ego（時系列集約、32 フレーム）で、手の特徴の有無だけを変える（表 1） | はい | MECCANO の Top-1 で UCF Swin3D-B（52.82）に届かない（表 2） | 既定の分割を 1 回。seed と検定は不明 | 報告に記載なし |
| H-08 | 表 1: RGB だけ、姿勢と RGB の後段融合、HandFormer。表 4: 一人称の 4 視点の RGB と、それに姿勢を加えたもの | 報告に記載なし | 報告に記載なし | 不明 | 報告に記載なし |
| H-13 | SlowFast に手のマスクを入力チャネルとして加えるかだけを変える。手の状態分類で手のマスク・手と物体のマスクを加える。接触境界の有無（表 5） | 入力チャネルの追加だけ | SlowFast（当時の標準）。部分集合での評価 | 記述なし | 報告に記載なし |
| H-20 | 試作と負例の作り方を固定し、AOD（active object の検出）の部品の有無だけを変える（表 6） | はい | 既存の行動分割の backbone。基盤モデルで事前学習した受け取り側との比較ではない | 報告に記載なし | 報告に記載なし |
| H-21 | 正解の物体の位置と、検出器の出力の位置（STIN+OIE） | 入力の位置の出所だけ | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| H-22 | 正解の手のセグメンテーションと自動のセグメンテーション | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| H-27 | SlowFast と、SlowFast に相互作用の部品を加えた IRN（表 8）。データ増強の種類（STD と SCR） | 報告に記載なし | 当時の強いモデル（SlowFast） | 報告に記載なし | 報告に記載なし |
| H-36 | 再学習なしの 100DOH と本手法（MECCANO の AP50） | 報告に記載なし | 報告に記載なし | 報告に記載なし | H-37 の MECCANO を評価に使う |
| H-38 | 同じ基盤に ORViT ブロックを加えるかだけ（層 2・7・11 を置き換える）。正解の枠を入れる場合（補足資料 D.2） | はい | 当時の強いモデル（MF-HR は EK100 の最良として引用） | 記述なし | 報告に記載なし |
| H-46 | 入れ子の交差検証で、メタ学習器を試験時と同じ「折りの平均の予測」で学習するかどうか | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| H-48 | 表 2: 手法の間。表 3: QueryInst で、同じテスト集合のまま学習データだけを変える | 表 3 は学習データだけ | 報告に記載なし | 報告に記載なし | 被引用 3 件（いずれも工程・術具検出ではない） |
| H-52 | 「手の見た目だけ」の基準と、手の動きを加えた手法。窓の長さ（表 4） | 報告に記載なし | 報告に記載なし | 報告に記載なし | 報告に記載なし |
| ほかの行 | 報告に比較の記載なし | — | — | — | — |

---

## 6. 効果

| ID | 指標・値・表番号 | 符号 | 符号や大きさが変わる条件 |
|---|---|---|---|
| H-01 | 表 1: EGTEA Top-1 44.9→（枠だけ 45.3、語だけ 45.8）→ 両方 46.6、平均クラス精度 37.6→39.1。EK100-MIR の平均 mAP 35.9→37.5、平均 nDCG 36.6→37.8。EgoMCQ intra 61.8→63.0。表 5: 手の枠を加えると EK の mAP 36.8→37.5、EGTEA 45.1／37.6 → 46.6／39.1。表 2: 疑似の枠を 256p から 640p にすると EK の mAP 36.9→37.5、VISOR の接触物体の位置正解率 68.2→78.7。表 7: 接地の精度は教師の 100DOH の 37.1（ランダム割り当て）・41.3（正解との照合）に対して本手法 82.3（問い合わせ 4 個） | 改善 | 補助の枠の品質が高いほど利得が大きい（著者の記述）。問い合わせの数は転移にはほとんど影響せず、接地では 4 個が 12 個より 3.6 点高い |
| H-02 | 既存のモデル（LaViLa、Helping Hands など）は物体中心の条件で劣化する（数値は報告なし）。一人称の映像だけで学習したモデルは手の手がかりに頼り、物体の情報を使い切っていない | 報告に記載なし | 報告に記載なし |
| H-03 | 表 2b（SSv2）: 基準 60.3、教師 65.3、生徒 63.2、RGB と光学フローと物体の教師からの生徒 63.0（R8-3）。表 3b（Something-Else）: 基準 51.8、教師 59.4、生徒 57.5、RGB と光学フローと物体の生徒 59.1。物体検出だけのモデルは SSv2 で 47.9、Something-Else で 41.4。表 4: Omnivore は Something-Else で基準より約 5.5% 高く、蒸留はさらに上回る（本文の記述） | 改善 | 弱い教師（音）を混ぜると名詞が下がる（表 2a: EK100 で RGB と音の生徒は名詞 −0.5、行動 −0.4）。教師を重みづけする温度で対処 |
| H-04 | 表 1（EGTEA、全体の正解率の 3 分割の平均）: SlowFast 64.02→HOCL 66.48、OSL 65.81、両方 66.86。平均クラス精度 55.81→57.66、56.97、58.14。Swin-B 64.09→64.77、65.81、65.98。平均クラス精度 57.14→57.43、58.94、59.27。表 2（MECCANO の Acc@1）: SlowFast 38.08→42.05、41.37、40.70。Swin-B 44.03→42.01、44.00、44.81。表 3（EK-100 の行動）: SlowFast 32.14→33.63、27.96、31.53。Swin-B 34.39→32.72、33.41、33.52。tail の行動は SlowFast 12.40→12.21、8.18、10.21。表 4（EPIC で事前学習してから EGTEA）: SlowFast 68.86→69.31（HOCL）、Swin-B 68.92→67.95（HOCL） | 受け取り側とデータで変わる。SlowFast では多くの条件で改善、Swin-B では差なしか悪化、EK-100 では組み合わせで悪化 | 受け取り側の強さ、データセット、HOCL と OSL の組み合わせ。要旨の「EGTEA で最大 2.24%」は表と一致しない |
| H-05 | 表 1（MECCANO）: 手の特徴の追加で Top-1 41.91→46.48、Top-5 79.63→82.04、Macro-F1 15.87→21.34。物体特徴の追加で 25.58→37.34。視線による剪定で 37.34→37.90。フレーム数: 1 フレームで 31.85、10 フレームで 37.90 | 改善 | 報告に記載なし |
| H-06 | 著者の主張では、姿勢の品質が高いほど行動認識が良くなる（数値は未読） | 改善（主張） | 姿勢の品質 |
| H-07 | 表 8 の段落: 姿勢ベース最良の MS-G3D w/ context の行動 28.7% は、映像ベース（4 視点の融合）より 5.1 点低い。動詞は 6.7 点高く、物体は 10.2 点低い | 動詞は改善、物体は悪化 | 予測の対象 |
| H-08 | 表 1（Assembly101）: TSM の RGB 35.27（行動）／58.27（動詞）／47.45（物体）、MS-G3D＋TSM の後段融合 39.74／65.12／51.12、HandFormer 41.06／69.23／51.17。姿勢だけの HandFormer 28.80／65.33／36.28。表 4: 一人称の 4 視点の RGB 33.80／59.00／46.50、e3＋e4＋姿勢 38.05／66.32／47.86。H2O で正解の 3 次元姿勢を含む条件の正解率 93.39%。補足資料の抜粋で Assembly101 の動詞が 2 次元の姿勢 58.92、3 次元の姿勢 63.70 | 改善（動詞で大きく、物体で小さい） | 予測の対象（動詞か物体か） |
| H-09 | EPIC の選んだ画像で HOI の正解率 89%（Shan ほかは 92%）。区間分けの F1 は GTEA 68.2%、UTGrasp 82.8% | 報告に記載なし | 報告に記載なし |
| H-10 | 行動認識 38.52% p-AP。YOLOWorld の手と物体の AP 85.13%（要旨） | 段階型の有無の差は不明 | 報告に記載なし |
| H-12 | 実ラベル 10% のとき、実データだけに比べて Overall AP が VISOR +5.67、EgoHOS +8.24、ENIGMA-51 +11.69（要旨）。ENIGMA-51 の接触の F1 は 77.28 → 77.83 | 改善 | 合成データの種類 |
| H-13 | 行動認識（7.1 節、表番号なし）: SlowFast に手のマスクを加えると、EPIC の部分集合で動詞 23.95→25.98、名詞 36.77→37.04。手の状態分類（表 6、左／右）: 正解率 78.53／74.29 → 手のマスク 84.18／83.33 → 手と物体のマスク 86.72／83.33。接触境界の有無（表 5、mIoU）: 左手の物体 54.83→59.05、右手の物体 38.48→40.85、両手の物体 39.14→49.94 | 改善（名詞は小さい） | 予測の対象。報告は表 5 で異なる行の値が一致する箇所を不審な点として挙げる（5:L183） |
| H-14 | 物体の動きの手がかりが、手の存在の手がかりを含む基準より有効だった。手の位置の偏りを使う基準は良い性能に達しない | 手の存在の手がかりは弱い | 報告に記載なし |
| H-61 | 一人称の手がかり（手の姿勢・頭部の動き・視線）を動きと物体の特徴に加えても、全データセットで僅かな改善にとどまった。「一人称の手がかりを直接符号化するのは効果的でない」と記載 | ほぼ差なし | 強い物体・動きの特徴の上 |
| H-19 | EgoPER: full-frame の DINOv2 で Accuracy 69.09・F1@0.5 61.42、相互作用の枠に限った表現で 80.69・77.61（R8-2）。利得は backbone に依存し、EgoVLPv2 のクリップの表現より DINOv2 のフレームの表現が強かった（R8-2） | 改善 | backbone |
| H-20 | 表 6: AOD なしで誤り検出の正解率（EDA）52.5、AUC 58.7。AOD ありで 57.0、62.0。行動分割の指標で AOD だけを変えた差は表 6 から読めない | 改善 | 調理で学習した AOD を HoloAssist と ATA（組立）へ移すと、領域のずれでうまく働かず、使わなかった |
| H-21 | 正解の位置を使う STIN+OIE 28.5 に対して、検出器の位置では 20.3（R8-4） | 上流の精度で下がる | 上流の精度 |
| H-22 | 正解の手のセグメンテーションだけで 66.4% のフレーム分類、自動のセグメンテーションでは 50.9%（R8-2） | 上流の誤差で下がる | 上流の精度 |
| H-27 | 表 8（EPIC-KITCHENS-100 の検証集合、Top-1）: SlowFast 63.64／48.58／36.76、IRN（SCR の増強）63.68／48.94／37.11（動詞／名詞／行動）。STD の増強では IRN 60.94／43.97／31.97。左右の手と全体の軌跡を使う方が、中央のフレームの検出や片手中心の表現より良い（R8-3） | 小さな改善 | データ増強（手を切り落とす切り出しは IRN を悪化させる）。Something-Else の ablation では寄与が大きい（R8-3） |
| H-36 | MECCANO で再学習なしの AP50 が 100DOH 11.17 に対して本手法 16.61（表番号未確認） | 改善 | 報告に記載なし |
| H-38 | EK100（表 3c）: MF-HR に対して行動 44.5→45.7、動詞 67.0→68.4、名詞 58.5→58.7。SSv2（表 3a）: MF 66.5→67.9。一方、MF+STIN 66.5、MF+STRG 66.1、MF+STRG+STIN 66.6。正解の枠を入れると MF より +7.3、MF-L より +6.7 | 改善（EK100 の名詞は +0.2） | 著者は EK100 の利得が小さい理由として一人称のカメラの動きと短いクリップを挙げる。枠の品質で利得が変わる |
| H-46 | メタ学習器を試験時と同じ「折りの平均の予測」で学習すると、stacking の値が 0.681→0.691（表番号未確認） | 改善 | 学習時と試験時の上流の予測の分布のずれ |
| H-48 | 表 2: 手と術具の mAP_box は Mask R-CNN 45.3、QueryInst 55.2、mAP_mask は Mask2Former 56.6。表 3（QueryInst）: 手は EgoHands で学習 8.3／6.3 → HTS で 54.0／50.7、手と術具は VISOR-HOS で 13.0／11.4 → HTS で 55.2／49.4 | 学習データによる | 学習データの領域 |
| H-50 | 視線で導く MAE が従来の SOTA より Jaccard で 6.4 点、通常の MAE より 3.1 点高い（要旨） | 改善 | 報告に記載なし |
| H-51 | 表 3: EgoSurgery の工程認識で Acc 75.57、F1 50.72、Jaccard 42.95。F1 は DINOv3-L より +18.3、EndoFM より +14.6（サブ調査） | 該当なし | 事前学習に評価データが含まれるか、公式分割かは不明 |
| H-52 | 表 1: 術具の位置特定 AP 0.925、手 0.713。表 2: 対象の手の選択（§0.5）。「手の見た目だけ」の基準は精度 0.524、F1 0.326。全手法の値は表 3（報告は未確認）。表 4: 50 フレームの窓が最良 | 改善（著者の主張） | 窓の長さ |
| H-56 | 映像だけの場合の最初の指標が 74.0 ± 4.8。映像＋手＋術具はそれを上回り、姿勢だけは映像だけ以上か有意差なし（差と表番号は不明） | 改善 | 入力の組み合わせ |
| H-57 | 精度／F1: トップビュー 0.88／0.88、接写 0.81／0.83、両カメラ 0.9／0.9（要旨） | 該当なし | カメラ |
| H-60 | Sun ほか: 手の検出の mAP[0.5:0.95] 0.33、左手の分類 67%、右手 71%（要旨） | 該当なし | 該当なし |
| ほかの行 | 報告に数値の記載なし | — | — |

---

## 7. 実装

| ID | コード・重み・ライセンス | 追加データ・注釈 | 事前学習と評価データの重なり |
|---|---|---|---|
| H-01 | 公式 GitHub あり（抽出した枠と重みも公開。ライセンス未確認） | 語り（ナレーション）と 100DOH の疑似の枠 | EgoMCQ は事前学習と同じ Ego4D 由来（著者が明記） |
| H-03 | 公開（GitHub） | 物体検出、光学フロー、音 | 報告に記載なし |
| H-04 | 不明 | OSL には物体の状態の人手の注釈が要る | 報告に記載なし |
| H-05 | 公開予定と記載 | 視線と VLM のキャプション | 報告に記載なし |
| H-08 | 公式 GitHub あり | 3 次元の手の姿勢（データセット付属か推定） | 報告に記載なし |
| H-13 | 公開（GitHub） | 手と物体の画素の注釈 | 報告に記載なし |
| H-20 | プロジェクトとコードの公開あり | active object の検出器（調理のデータで学習） | 報告に記載なし |
| H-32 | 公式のコードとモデルの公開あり | 大きなモデルから集めた相互作用の事前知識 | 報告に記載なし |
| H-38 | プロジェクトの頁で公開と記載 | 物体の枠（COCO で事前学習した検出器をクラスを無視して使う） | 報告に記載なし |
| H-48 | GitHub（Fujiry0/EgoSurgery）と記載。ライセンス不明。R8-5 は公開予定と書く | 該当なし | 該当なし |
| H-49 | repository は CC BY-NC-SA 4.0（R8-4） | 該当なし | 該当なし |
| ほかの行 | 報告に記載なし | 報告に記載なし | 報告に記載なし |

---

## 8. 本研究との関係

事実としての近さは §3（距離の軸）と §4 の「本研究の条件で測られたか」にある。各行に報告者が付けた一行の要点と、依頼文の (a)・(b) への当てはめの評価は、起票者用の文書に置いた。推論時に上流の出力を使うか、学習時だけ使うかは、§3 の「モデルの状態」の欄に事実として書いた。

---

## 9. 索引（起票者が行から組む）

上流の出力をいつ使うか × 下流の課題。

| | 下流が行動・手順・工程 | 下流が物体の検出・認識・位置特定 |
|---|---|---|
| 推論時に使う | H-05、H-13、H-19、H-20、H-21、H-22、H-27、H-38、H-61、H-53（腹腔鏡の工程）、H-56（開放手術のジェスチャ） | H-10（検出の起動。差は不明）、H-52（開放手術の術具の分類） |
| 学習時だけ使う | H-01、H-02、H-03、H-04、H-31、H-41、H-43 | H-01（VISOR の接触物体の位置特定）、H-32（active object の検出） |
| 同時に学習 | H-24、H-25、H-54 | H-58（手と術具の相互作用と術具の位置） |

下流の課題 × 改善の対象（動詞か物体か）を分けて報告した行: H-07、H-08、H-13、H-27、H-38。

---

## 10. 見つからなかったもの

報告の定義では、「見つからなかった」はその報告の検索の範囲で確かめられなかったという意味で、存在しないことを意味しない。

- **冒頭の問い**: 把持の推論モデルを独立に学習・凍結し、その出力で物体検出と行動・手順・工程の認識の両方を改善した研究（1:L14、4:L7、5:L14）。手術に限っても、独立した手と術具の把持モデルを凍結し、その出力で術具検出か工程認識を改善した査読済みの研究（4:L7）
- **EgoSurgery-HTS・EgoSurgery-Tool を使って工程か術具検出を改善した研究**: 0 件（1:L353、4:L296、5:L368）。HTS の被引用は 3 件（EgoMed-Agent arXiv 2607.17341、AR-ERIS arXiv 2607.08397、Show, Don't Tell arXiv 2603.12751）で、いずれも工程・術具検出の補助ではない（1:L349〜L352）
- **受け取り側を凍結し界面だけを学習する構成で、HOI を検出か工程へ渡した研究**（5:L369）
- **凍結して渡す形と同時学習の直接の比較**。近いのは H-03 の Omnivore の比較だけ（1:L361、5:L371）
- **正解の把持と予測の把持を同じ下流モデルで差し替えて、把持の精度と下流の利得の関係を測った研究**。近いのは H-01 の表 2、H-38 の正解の枠、H-21 の正解と検出の差（4:L286、5:L378、1:L362）
- **HOI で検出 mAP をクラス別（稀少・小さい・紛らわしい）に改善した研究**（1:L363、5:L370）
- **学習した HOI モデルと「手の検出＋枠の重なりの規則」の下流での比較**（5:L372）
- **左右を潰した版と区別した版の比較、両手のクラスの効果の切り分け**（4:L288、2:L50）
- **同じフレームの相互作用の推論を使う場合と、前の時刻までに限る場合の比較**（4:L290、1:L368）
- **SAM などで作った疑似の把持マスクの品質を変えて、下流の利得への伝わり方を測った研究**（4:L292、1:L367）
- **手術で、手と術具の把持・接触のモデルを工程認識の教師にだけ使い、推論時には捨てる研究**（4:L294）
- **本人の手だけの定義と、他者の手を含む定義の下流への影響**（5:L373、1:L366）
- **低いフレームレート（0.5 fps 前後）での HOI → 行動・手順**（5:L374、1:L364）
- **交差検証の折りの内側で補助モデル・教師を学習し直すかどうかの影響（映像・医療・HOI での teacher leakage の測定）**。一般の stacking では H-46 だけ（5:L375）
- **補助の注釈が一部の動画にしか無い条件で、疑似ラベルや蒸留で補助信号を広げた手術の研究**（5:L376）
- **強い受け取り側で HOI の利得が消えることを主題にした論文**。部分的な所見は H-04、H-38、H-02（5:L377）
- R8-5 が個別には探していないもの: Rolling-Unrolling LSTM、HOI4D、H2O、ARCTIC、HoloAssist、Ego-Exo4D、EgoPER、POV-Surgery、VISOR（5:L379）。R8-1 が走査できなかった範囲は §12

---

## 11. 未検証の組み合わせ

R8-4（4:L298〜L314）と R8-5（5:L383〜L392）と R8-1（1:L372〜L378）の項目を、重なりをまとめて並べた。

1. 同じ予測の把持の信号で、推論時に渡す形と学習時だけ使う形を、同じデータ・同じ受け取り側・同じ分割で比べる（4、1、H-03 は教師と生徒の比較で融合の構造が違う）
2. 同じ把持モデルを工程の側と検出の側の両方へつなぎ、どちらの利得が大きいかを比べる（4、1）
3. 受け取り側を両方凍結し、小さな界面だけで HOI の出力を渡す。H-01 はこの形に近いが、下流は検索と分類（5）
4. 枠の重なりで作った接触のラベルと、画素のマスクの把持の表現を、同じ下流の課題で比べる（4）。規則で作った疑似ラベルで学習した例（H-13 の接触境界、H-36 の中心距離の割り当て、H-48 の IoU 最大）はあるが、同じ規則を推論時に直接使った場合との比較はない（5）
5. 左右・両手の 3 通りの役割の表現と、「active な術具である」という二値の表現の比較（4、5）
6. 受け取り側の事前学習の規模を連続的に変えて、相互作用の信号が冗長になる境界を測る。H-04 は SlowFast と Swin-B の二点だけ（4、1）
7. 0.5 fps の低い時間解像度で、状態の形の把持の信号がどこまで効くか（4、5、1）
8. 15 本規模の動画単位の 5 折りで、三つの特徴を出すモデルを凍結し界面だけを学習する（4、5）
9. 本人の手だけの定義と他者の手を含む定義（5）
10. 折りの内側で HOI の教師を学習し直す場合と、全動画で学習した場合（5）
11. 手の情報に固有の上乗せを、物体検出だけを入れた対照と分けて測る。H-05 は物体の特徴の上に手の特徴を足すので近いが、手の特徴にも接触物体の枠とクラスが含まれる（1）

---

## 12. 検索記録

- **R8-1**（1:L382〜L392）: 2026-10-31。ウェブ検索、arXiv、CVF、PMC（取得失敗）、Semantic Scholar の API（サブエージェント）。方向ごとの記録は方向 1 が 4 件、2 が 5 件、3 が 16 件、4 が 1 件、5 が 2 件、6 が 0 件、7 が 3 件（報告の数え方。一つの記録が複数の方向に数えられている）。走査できなかった範囲: PMC の論文誌版の本文、有料の論文誌の本文、OpenReview の非公開の投稿、学位論文、Ego4D・HOI4D・H2O・ARCTIC・EgoPER・HoloAssist・Ego-Exo4D の原典、EgoSurgery-Phase の被引用の一覧、Google Scholar の被引用の一覧
- **R8-2**（2:L15〜L17）: 起点と検索式の例だけ。件数・検索日の記載なし
- **R8-3**: 検索記録の節なし
- **R8-4**（4:L316〜L336）: 2026-10-31。件数は、題名・要旨か本文を確かめて関連すると判定した重複除外の文献の数。方向 1: 3 件、方向 2: 11 件（うち精査 6 件）、方向 3: 31 件（本文まで 15 件、要旨中心 16 件）、方向 4: 14 件、方向 5: 13 件、方向 6: 8 件、方向 7: 7 件。代表の検索語は報告の該当行。問い (7) のデータセットの逆引きで、VISOR・EPIC-KITCHENS、MECCANO、EgoPER、Ego4D FHO、Assembly101、H2O、Ego-Exo4D、ENIGMA-51、HoloAssist を確かめた。うち相互作用の情報を下流の値まで確かめた対応は、VISOR・EPIC 系 → H-01、MECCANO → H-04、EgoPER → H-20、Assembly101 → H-08、H2O → H-08。VISOR は EPIC-KITCHENS の上に手作業の意味のマスク 272K、密なマスク 9.9M、手と物体の関係 67K を加える
- **R8-5**（5:L396〜L406）: 2026-10-31。web 検索 18 回（サブ調査 1 回の内部検索は別）。方向 1: 3 件、2: 6 件、3: 14 件（手術・医療の語を含まない検索 10 回）、4: 2 件、5: 1 ブロック、6: 1 件、7: 独立の論文は 0 件。予算切れで実行できなかった検索: Cholec80 での凍結した検出器の特徴の融合、Assembly101 での手の姿勢の行動分割への融合

走査の偏り: 共通ブロックを渡さなかった三件（R8-1〜R8-3）と渡した二件で、主要な行が入れ替わる（§0.5）。R8-5 は方向 3 の本文を 4 件読み、R8-4 は方向 3 の件数が最も多い。両者とも方向 1・2 は要旨中心（依頼文の重みづけのとおり）。

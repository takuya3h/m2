# 把持（手と物体の相互作用）推論を検出・工程認識へ渡す研究の文献調査（EgoSurgery 設定向け）

把持の推論モデルを独立に学習して凍結し、その出力で物体検出と行動・手順・工程の認識の両方を改善した研究は、手術・非手術のどちらでも見つからなかった。片方だけなら、非手術の一人称映像で (b) 型（学習時だけ使う）の Helping Hands（ICCV 2023）と Multimodal Distillation（ICCV 2023）、(a) 型に近い推論時入力の ORViT（CVPR 2022）が該当する。手術では、手の動きで術具を分類した Shimizu ほか 2021 が、段階型（凍結した検出器の出力を推論時に後段へ渡す形）として最も近い。

## TL;DR
- **冒頭の確認事項（新規性）**: 「独立に学習・凍結した把持（HOI）モデル → 小さな学習可能界面 → 凍結した検出モデル／工程モデル」という構成の研究は、手術（方向 1・2）でも非手術（方向 3・4）でも見つからなかった。EgoSurgery-HTS（arXiv 2503.18755）と EgoSurgery-Tool（arXiv 2406.03095）を使って工程認識か術具検出を改善した研究も 0 件だった（両データセット論文は「多タスク学習が可能」と書くだけで、実験はしていない）。
- **近い証拠（非手術）**: 凍結した 100DOH 手・物体検出器の出力を学習時だけ補助教師にした Helping Hands は、EGTEA のゼロショット行動分類 top-1 を 44.9→46.6 に上げた（Table 4。凍結した受け取り側の上に学習する decoder を置く形）。\[1\]物体検出（手と物体の枠）を入れた教師から RGB だけの生徒へ蒸留した研究では、Something-Something で 60.3→63.2 となった。推論時にも検出を使う教師（65.3）との差は 2.1 点だった（Table 2b）。\[2\]推論時に検出枠を入れる ORViT は、EPIC-KITCHENS-100 の名詞（物体）で +0.2 にとどまった（Table 3c）。\[3\]
- **否定的・条件つきの所見**: 枠を入れる既存の方式（STIN・STRG）は、強い映像 Transformer の上では SSv2 で改善しなかった（ORViT Table 3a）。\[3\]利得は補助信号の品質に強く依存していた（Helping Hands Table 2、ORViT の正解枠 oracle で +7.3）。\[1\]\[3\]低いフレームレート（0.5 fps）、他者の手の扱い、交差検証の折りの内側で補助モデルを学習し直すかどうか、の三点を測った研究はいずれも見つからなかった。

---

## 最初に書くこと（依頼の指定による）

**該当なし**: 把持（手と物体の相互作用）の推論モデルを独立に学習し、その出力で物体検出と行動・手順・工程の認識の両方を改善した研究は、手術・医療と非手術のどちらでも見つからなかった。

**片方だけを改善した研究と、(a)(b) のどちらの形か**（詳細は (2) 文献ごとの記録）:

| 文献 | 改善した下流 | 形 | 凍結の状態 |
|---|---|---|---|
| Helping Hands（Zhang ほか, ICCV 2023, arXiv 2308.07918） | 行動分類（ゼロショット）、検索、Ego4D NLQ/MQ | **(b)**: 凍結した 100DOH 検出器の出力を、学習時だけ補助損失の教師にする | 100DOH は凍結。受け取り側の映像・言語符号器も凍結し、間の object-aware decoder だけを学習 |
| Multimodal Distillation（Radevski ほか, ICCV 2023, arXiv 2307.07483） | 行動認識（SSv2、Something-Else） | **(b)**: 手・物体の検出から学習した教師を介した蒸留 | 検出器は別学習。生徒は全体を学習（凍結ではない） |
| ORViT（Herzig ほか, CVPR 2022, arXiv 2110.06915） | 行動認識（SSv2、EK100、Diving48）、AVA | **(a) に近い**: 推論時に検出枠を入力 | 検出器とは重みを共有しない。受け取り側は学習する |
| EgoHOS（Zhang ほか, ECCV 2022, arXiv 2208.03826） | 手の状態分類、行動認識（EPIC 部分集合） | **(a) に近い**: 手のマスクを入力チャネルに追加 | 受け取り側を学習し直す |
| Shimizu ほか（J Imaging 2021, DOI 10.3390/jimaging7020015）【手術】 | 術具の分類（検出の分類部分） | 段階型（推論時に使う） | 検出器 → 規則による手の選択 → 分類器、の分離した段階 |
| Park ほか（Comput Biol Med 2023, DOI 10.1016/j.compbiomed.2023.107453）【手術】 | 工程認識 | 推論時に融合（a 型に近い） | 不明 |

---

## (1) 系統表

「本記録の件数」は (2) の記録ブロックの数である。

| # | 系統の名前 | 代表的な文献 | 現役度（どこでの話か） | 件数 |
|---|---|---|---|---|
| S1 | 手・物体の検出器（接触状態、active object の枠） | 100DOH（Shan ほか CVPR 2020）、Hands23、MECCANO の EHOI 検出 | 定番の基準（Ego4D/EPIC での疑似教師の作成）。Helping Hands、arXiv 2607.08514 が教師作成に使用 | 3 |
| S2 | 手・物体の画素分割（左右の手、左右／両手の物体） | EgoHOS、EPIC-KITCHENS VISOR、EgoSurgery-HTS | 定番の基準（一人称 HOI 分割）。EgoSurgery-HTS の 5 クラスは EgoHOS と同じ構成 | 2 |
| S3 | 推論時に枠を映像モデルへ入れる物体中心型 | STIN〔既有〕、STRG、ORViT、ObjectViViT（Zhou ほか 2023）〔既有〕 | SSv2/EK100 で STIN/STRG は置き換え済み寄り（ORViT Table 3）。ORViT 自体は不明 | 1 |
| S4 | 学習時だけ手・物体の情報を使う（補助損失、物体問い合わせ decoder） | Helping Hands、SViT〔既有〕、arXiv 2607.08514 | 新興〜定番の基準（Ego4D 系映像言語事前学習）。2607.08514 が Helping Hands を比較対象に使用 | 2 |
| S5 | 多モダリティ蒸留・特権情報（LUPI） | Radevski ほか、Graph Distillation（ECCV 2018）、Garcia ほか（TPAMI 2019）、Progressive Privileged KD | 定番の基準（方法論）。手・相互作用に特化したものは少ない | 2 |
| S6 | 手と物体の相互作用の領域で注意を作る行動予測 | InAViT（WACV 2024）、Rolling-Unrolling LSTM（種、未確認） | 新興（EK100/EGTEA の予測） | 1 |
| S7 | 3 次元の手の姿勢を使う行動認識 | H+O（CVPR 2019）、HandFormer（ECCV 2024）、Assembly101 | SOTA 級を主張（HandFormer、Assembly101/H2O。表は未読） | 2 |
| S8 | active object／next active object | Furnari ほか 2017、ANACTO、AFF-ttention（ECCV 2024）、StillFast | 定番の基準（Ego4D STA） | 2 |
| S9 | 相互作用の検出を行動区間・手順へ使う | arXiv 2109.14734、arXiv 2507.13326、ENIGMA-360 | 新興 | 3 |
| S10 | 少ないデータ・合成データ・疑似ラベルによる HOI モデル | HOI-Synth（ECCV 2024）、Sequential Voting（arXiv 2110.11524） | 新興 | 2 |
| S11 | 手術での術具の使い方・手の信号 → 工程／術具 | Park ほか、Shimizu ほか、EndoNet〔既有〕、MTRCNet-CL〔既有〕 | EndoNet/MTRCNet-CL は Cholec80 で置き換え済み（直近 2 年の表は今回未確認）。Park ほかは不明 | 4 |
| S12 | 一人称開放手術のデータセット | EgoSurgery-Phase/Tool/HTS | データセット | 3 |
| S13 | 情報の漏れ（stacking、nested CV） | arXiv 2607.25367 | 方法論 | 1 |
| S14 | Simultaneous Detection and Interaction Reasoning（Li ほか）〔既有〕 | 既有のため記録なし | 不明 | 0 |

---

## (2) 文献ごとの記録

記入の約束: 読めなかった欄・判断できない欄はまとめて「その他の欄: 不明」と書く。

### A. 方向 1（同じデータ・同じ設定）— 後回し（要旨中心）

#### A-1. EgoSurgery-HTS
- 書誌: Darjana, Fujii, Saito, Kajita／2025／EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos／Healthcare Technology Letters 12(1): e70049（査読つき）／DOI 10.1049/htl2.70049、arXiv 2503.18755
- 読んだ範囲: 要旨と本文抜粋（注釈手順の段落、表 1 の行）
- 近さ: 方向 1／一人称／開放手術／画像 → 術具インスタンス分割（14 種）、手インスタンス分割（4 種）、手と術具の分割（5 クラス）／推論の規約は該当なし（画像単位）／表 1 で 18.4K フレーム\[4\]\[5\]
- 手法の位置: S2・S12／データセット／条件は一人称
- 証拠: 既存データセットで学習したモデルより分割が改善（要旨の主張）。\[6\]\[7\]効果量は本文の表を未読のため不明
- 追試・採用: 引用 3 件（いずれも工程・術具検出ではない。サブ調査、Semantic Scholar 2026-10-31）
- 実装: プロジェクトページで公開予定と記載\[7\]
- その他の欄: 不明
- 要点:
  - 論文には「interacting tool annotations are determined by selecting the tool with the highest IoU score relative to the hand segmentation」とある。マスクは術具と手の枠を SAM に与えて作られている。\[7\]依頼者の理解（枠の重なりで決まる）と、論文の字面（手の分割マスクに対する IoU 最大）は異なる。
  - 不審な点: 術具の種類が HTS では 14、Tool では 15。枠つきフレーム数が arXiv 版で「15K」、\[7\]\[8\]HTL 版の抜粋で「19K6」（誤植の可能性）。\[4\]\[6\]

#### A-2. EgoSurgery-Tool
- 書誌: Fujii, Saito, Kajita／2024／EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos／arXiv プレプリント（査読の有無は不明）／arXiv 2406.03095
- 読んだ範囲: 要旨と本文抜粋（2 節、図 4 の説明）
- 近さ: 方向 1／一人称／開放手術／画像 → 術具と手の枠／EgoSurgery-Phase の 21 本のうち 15 本に注釈。15,437 枚、術具の枠 49,652、手の枠 46,320、術具 15 種、手 4 種（自分の左右、他者の左右）\[8\]\[9\]
- 手法の位置: S12／データセット（9 種の検出器で評価、数値は未読）／動画単位の train/val/test\[8\]
- その他の欄: 不明
- 要点: 術具と工程の共起行列（図 4）を示し、「Surgical tool information might be helpful for surgical phase recognition」と書くが、融合の実験はない。\[8\]他者の手は枠として注釈されている（HTS の把持クラスには含まれない）。\[8\]

#### A-3. SurgMotion（EgoSurgery で工程認識）
- 書誌: Wu, Holm, Chen ほか／2026／SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos／arXiv プレプリント／arXiv 2602.05638
- 読んだ範囲: 本文抜粋（サブ調査による。筆者自身は表を未確認）
- 近さ: 方向 1・2／一人称（EgoSurgery の部分）／開放手術を含む／映像 → 工程\[10\]
- 手法の位置: 手・術具の信号を使わない基盤モデル／新興
- 証拠: Table 3 で EgoSurgery の工程認識が Acc 75.57、F1 50.72、Jaccard 42.95。F1 は DINOv3-L より +18.3、EndoFM より +14.6\[10\]\[11\]
- その他の欄: 不明（事前学習に評価データが含まれるか、公式分割かも不明）
- 要点: 手や術具の信号なしで EgoSurgery の工程に基盤モデルを使った既発表の値である。界面の実験で比べる相手の候補になる。

### B. 方向 2（手術一般）— 後回し（要旨中心）

#### B-1. Park ほか（視覚的運動指標の融合による工程認識）
- 書誌: Park B, Chi H, Park B, Lee J, Jin HS, Park S, Hyung WJ, Choi MK／2023（ワークショップ版 2022）／Visual modalities-based multimodal fusion for surgical phase recognition／Comput Biol Med 166:107453（査読つき）／DOI 10.1016/j.compbiomed.2023.107453。MMMI 2022 版は DOI 10.1007/978-3-031-18814-5_2。2026 年に訂正記事あり（DOI 10.1016/j.compbiomed.2026.111850。内容は未確認）\[12\]\[13\]
- 読んだ範囲: 要旨とハイライトのみ
- 近さ: 方向 2／腹腔鏡（PETRAW はシミュレータ）／低侵襲手術／映像と、術具分割から作った「visual kinematics-based index（VKI）」→ 工程／幽門側胃切除の私有データと PETRAW\[12\]\[14\]
- 手法の位置: S11
- 証拠: CNN の特徴だけの場合と VKI を融合した場合の比較。要旨は改善を主張するが数値は不明\[14\]
- その他の欄: 不明
- 要点: 術具の動きと術具どうしの関係を指標にして、工程認識へ推論時に融合している。\[12\]種の文献の実在を確認した。数値は訂正記事を確認してから使う必要がある。

#### B-2. Shimizu ほか（手の動きで術具を分類）
- 書誌: Shimizu T, Hachiuma R, Kajita H, Takatsume Y, Saito H／2021／Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera／J Imaging 7(2):15（査読つき）／DOI 10.3390/jimaging7020015
- 読んだ範囲: 方法の節まで（サブ調査。結果の表 3 は未読）
- 近さ: 方向 2（一人称の開放手術。EgoSurgery と同じ研究室の系譜）／一人称／開放手術／映像 → 形の似た術具（はさみと持針器）の位置と分類／モデルは独立した段階（Faster R-CNN による手・術具の検出 → 枠の重なりが最大の手を選ぶ規則 → 手の切り出しを ResNet-18 + LSTM で分類）\[15\]\[16\]
- 手法の位置: S11
- 証拠: 二つの基準より改善（著者の主張。数値は表 3 にあるが未読）。表 2 の抜粋に、対象の手の選択精度とみられる 0.943／0.996／0.946／0.971（列名は未確認）\[16\]
- その他の欄: 不明
- 要点: 「どの手が術具を持つか」を枠の重なりの規則で決め、その手の動きで紛らわしい術具を分けた。\[15\]\[16\]問い (2)（紛らわしいクラス）に最も近い手術の例。検出 mAP 全体での評価ではない。

#### B-3. Goldbraikh ほか（多視点の開放手術で手と術具の使用）
- 書誌: Goldbraikh ほか／2022／Open surgery tool classification and hand utilization using a multi-camera system／Int J CARS（査読つき）／arXiv 2111.06098
- 読んだ範囲: 要旨のみ（サブ調査）
- 近さ: 方向 2／俯瞰（多視点）／開放手術（模擬の腸管修復、48 名）／映像 → 各手が持つ術具／窓の中（30 fps で 1 秒窓、3 fps で 40 秒窓）／段階型（YOLOv5 → LSTM）\[17\]
- その他の欄: 不明
- 要点: 二つのフレームレートで「手が持つ術具」を推定している。フレームレートの比較の数値は読めていない。

#### B-4. 開放手術のジェスチャ認識（3 次元の手と術具の姿勢）
- 書誌: 著者・題名は抜粋で確認できず／2025／Int J CARS（査読つき）／DOI 10.1007/s11548-025-03564-1
- 読んだ範囲: 抜粋のみ（サブ調査）
- 近さ: 方向 2／開放手術／映像と 3 次元の手・術具の姿勢 → ジェスチャ（工程ではない）／MS-TCN++、LTContext／姿勢推定器は上流で別に学習\[18\]
- 証拠: 映像だけの場合の最初の指標が 74.0 ± 4.8。映像＋手＋術具の組み合わせはそれを上回り、姿勢だけの組み合わせは映像だけ以上か有意差なし（具体的な差と表番号は不明）\[18\]\[19\]
- その他の欄: 不明
- 要点: 上流で別に学習した手・術具の姿勢を時間モデルへ入れた手術の例である。

#### B-5. Sun & Zhang（手の位置と左右の多タスク検出）
- 書誌: Sun, Zhang／2026／YOLOv10-Based Multi-Task Framework for Hand Localization and Laterality Classification in Surgical Videos／TrackRAD@MICCAI（Semantic Scholar の表記）／arXiv 2602.18959
- 読んだ範囲: 要旨のみ
- 近さ: 方向 2／一人称（Trauma THOMPSON 2025 Task 2）／外傷処置／画像 → 手の枠と左右\[20\]
- 証拠: mAP[0.5:0.95] = 0.33、左手の分類 67%、右手 71%（要旨）。下流への利用はない\[20\]
- その他の欄: 不明
- 要点: 手術映像での左右の判別は難しい（67〜71%）。左右を区別した把持信号の上流精度を見積もる参考になる。

#### B-6. 開放手術映像の手の検出・追跡
- 書誌: Using Computer Vision to Automate Hand Detection and Tracking of Surgeon Movements in Videos of Open Surgery／ID 不明（PMC8127677）
- 読んだ範囲: 要旨のみ
- 近さ: 方向 2／YouTube の開放手術映像／手の検出（RetinaNet）と追跡（SORT）、技能評価\[16\]\[21\]\[22\]
- その他の欄: 不明
- 要点: 工程認識・術具検出への利用はない。

### C. 方向 3（一人称の非手術映像）— 最優先

#### C-1. Helping Hands【本文を読んだ】
- 書誌: Chuhan Zhang, Ankush Gupta, Andrew Zisserman／2023／Helping Hands: An Object-Aware Ego-Centric Video Recognition Model／ICCV 2023（査読つき）／arXiv 2308.07918
- 読んだ範囲: 本文（1〜6 節、Table 1〜7）
- 近さ:
  - 方向 3／一人称／非医療
  - 課題: 映像クリップと文 → 映像と言語の埋め込み。下流はゼロショットの行動分類（EGTEA）、検索（EK100-MIR）、EgoMCQ、NLQ/MQ\[1\]
  - 推論の規約: offline（クリップから 4 フレームを一様に抽出）\[1\]
  - データ規模: EgoClip 380 万クリップ、1,600 万フレームに 100DOH を適用\[1\]
  - モデルの状態: 100DOH は独立に学習して凍結。映像・言語の符号器（TSF-L、LaViLa）も凍結し、object-aware decoder、問い合わせベクトル、言語の射影だけを学習（4.3 節）\[1\]
- 手法の位置: S4／定番の基準（Ego4D 系。arXiv 2607.08514 が比較対象に使用）／EK100-MIR、EGTEA、EgoMCQ、VISOR\[23\]
- 証拠:
  - 物体を意識させる損失の有無（Table 4。Ours‡ と Ours の差は損失だけ）: EK100-MIR 平均 mAP 35.9→37.5、平均 nDCG 36.6→37.8。EGTEA top-1 44.9→46.6、mean 37.6→39.1。EgoMCQ intra 61.8→63.0\[1\]
  - 手の枠の有無（Table 5。物体枠だけと手＋物体枠）: EK mAP 36.8→37.5。EGTEA は 45.1／37.6 → 46.6／39.1\[1\]
  - 補助信号の品質（Table 2。100DOH への入力 256p と 640p）: EK mAP 36.9→37.5。VISOR の接触物体の位置正解率 68.2→78.7\[1\]
  - 接地の精度（Table 7）: 教師の 100DOH は 37.1（ランダム割り当て）、41.3（正解との照合）。本手法は 82.3（問い合わせ 4 個）\[1\]
  - 符号: 改善
  - 符号が変わる条件: 補助枠の品質が高いほど利得が大きい（著者の記述「magnitude of boost … closely related to the box quality」）。問い合わせ数は転移性能にはほとんど影響しないが、接地では 4 個が 12 個より 3.6 点高い\[1\]
  - 基準の強さ: 当時の強いモデル（LaViLa-L）
  - 単独要因の比較か: Table 1・5 は損失だけを変えた比較
  - seed・分割・検定: 記述なし
- 実装: コード公開（GitHub。ライセンスは未確認）／追加で文（ナレーション）と 100DOH の疑似枠が要る／EgoMCQ は事前学習と同じ Ego4D 由来（著者が明記）\[1\]
- 要点: 凍結した HOI 検出器の、ノイズを含み疎な出力を、学習時だけ補助教師にすると、凍結した受け取り側の上の小さな decoder を通して、行動分類が +1.7 点（EGTEA top-1）上がった。依頼の (b) と構成が最も近い。
- 不審な点: Table 2 の 640p 行は EGTEA が「39.1｜46.6」（Top1｜Mean の順）で、Table 1 の同じ設定（Top1 46.6、Mean 39.1）と列が入れ替わっている。Table 5 も列見出しが「Mean｜Top1」の順で、値の並びと合わない。

#### C-2. EgoHOS（細粒度の手・物体分割）【本文を読んだ】
- 書誌: Lingzhi Zhang, Shenghao Zhou, Simon Stent, Jianbo Shi／2022／Fine-Grained Egocentric Hand-Object Segmentation: Dataset, Model, and Applications／ECCV 2022（査読つき）／arXiv 2208.03826
- 読んだ範囲: 本文と補足資料の一部
- 近さ:
  - 方向 3／一人称／非医療
  - 課題: 画像 → 左手、右手、左手の物体、右手の物体、両手の物体（EgoSurgery-HTS と同じ 5 クラスの構成）、接触境界。下流は手の状態分類と行動認識\[24\]
  - データ規模: 11,243 枚（約 1,000 本の動画から疎に抽出）。\[25\]手の状態分類は EPIC の 3,531 フレーム（8:1:1 分割）\[24\]
  - モデルの状態: 分割は段階型（手 → 接触境界 → 物体）。下流では手のマスクを入力チャネルに加えて受け取り側を学習し直す\[24\]
- 手法の位置: S2／定番の基準（HOI-Synth（ECCV 2024）が評価データとして使用）\[26\]
- 証拠:
  - 行動認識（7.1 節本文、表番号なし）: SlowFast に手のマスクを加えると、EPIC 部分集合で動詞 top-1 23.95→25.98、名詞 36.77→37.04\[24\]
  - 手の状態分類（Table 6、左／右）: 正解率 78.53/74.29 →（手のマスク）84.18/83.33 →（手と物体のマスク）86.72/83.33。F1 37.53/32.02 → 59.42/59.00 → 60.35/59.64\[24\]
  - 接触境界（CB）の有無（Table 5、mIoU。Seq. Decode と Seq. Decode + CB）: 左手の物体 54.83→59.05、右手の物体 38.48→40.85、両手の物体 39.14→49.94\[24\]
  - 符号: 改善（名詞は +0.27 点と小さい）
  - 基準の強さ: SlowFast（当時の標準）、部分集合での評価
  - 単独要因の比較か: 入力チャネルの追加だけを変えた比較
  - seed・検定: 記述なし
- 実装: コード公開（GitHub）\[2\]\[24\]\[25\]\[27\]
- 要点: 接触境界は「手と物体のマスクを膨張させた重なり」から自動で作る規則由来の疑似ラベルで、物体の分割を改善した（Table 5）。\[24\]手のマスクを入れると動詞は +2 点、名詞は +0.3 点で、物体側への利得は小さかった。
- 不審な点: Table 5 で「Para. Decode + CCDA」と「Seq. Decode」の物体 3 列（54.83/38.48/39.14）が完全に一致している。「Seq. Decode + CCDA」と「Seq. Decode + CB + CCDA」の手の 2 列（87.70/88.79）も一致している。本文の「As shown in Table 1」は Table 2 を指すとみられる。\[24\]

#### C-3. InAViT
- 書誌: Debaditya Roy, Ramanathan Rajendiran, Basura Fernando／2024／Interaction Region Visual Transformer for Egocentric Action Anticipation／WACV 2024（査読つき）／arXiv 2211.14154
- 読んだ範囲: 要旨と HTML の抜粋
- 近さ: 方向 3／一人称／観測した映像と手・物体の領域 → 次の行動／過去のみ（予測）／EK100、EGTEA Gaze+／受け取り側（MotionFormer）は学習する\[28\]
- 手法の位置: S6／新興（「当時 SOTA」を主張）\[28\]
- その他の欄: 不明（本文の表を未読）
- 要点: 手と物体の領域の外観の変化を空間 cross-attention で「相互作用トークン」にし、過去だけを使う予測に使う。\[29\]

#### C-4. HandFormer（3 次元の手の姿勢の有用性）
- 書誌: Shamil, Chatterjee, Sener, Ma, Yao／2024／On the Utility of 3D Hand Poses for Action Recognition／ECCV 2024（査読つき）／arXiv 2403.09805、DOI 10.1007/978-3-031-72658-3_25
- 読んだ範囲: 要旨と補足資料の抜粋
- 近さ: 方向 3／一人称（Assembly101、H2O）／3 次元の手の姿勢（密）と疎な RGB → 行動／姿勢はデータセット付属\[30\]
- 手法の位置: S7／SOTA 級を主張（Assembly101、H2O。本文の表は未読）\[30\]
- 証拠: 補足資料の抜粋（表番号は未確認）で、Assembly101 の動詞認識が 2 次元姿勢 58.92、3 次元姿勢 63.70（HandFormer-B/6）\[31\]
- 実装: コード公開（GitHub）
- その他の欄: 不明
- 要点: 姿勢だけで骨格ベースの方式を上回ると主張している（FLOPs は 1/5）。物体の情報は RGB で補う。\[30\]

#### C-5. Assembly101（姿勢と映像の比較）
- 書誌: Sener ほか／2022／Assembly101: A Large-Scale Multi-View Video Dataset for Understanding Procedural Activities／CVPR 2022（査読つき）／arXiv 2203.14712
- 読んだ範囲: 本文の抜粋（Table 8 の段落）
- 近さ: 方向 3／一人称と三人称／組立／3 次元の手の姿勢または映像 → 細粒度の行動
- 手法の位置: S7
- 証拠（Table 8 の段落）: 姿勢ベース最良の「MS-G3D w/ context」の行動正解率は 28.7% で、映像ベース（4 視点の融合）より 5.1 点低い。動詞は姿勢のほうが 6.7 点高く、物体は 10.2 点低い\[32\]
- その他の欄: 不明
- 要点: 手の表現は動詞（動作）に効き、物体（名詞）には効かない。\[32\]表現の系統ごとの効き方（問い (5)）の直接の証拠である。

#### C-6. H+O
- 書誌: Tekin, Bogo, Pollefeys／2019／H+O: Unified Egocentric Recognition of 3D Hand-Object Poses and Interactions／CVPR 2019（査読つき）／arXiv 1904.05349
- 読んだ範囲: 要旨と抜粋
- 近さ: 方向 3／一人称／RGB → 3 次元の手・物体の姿勢、物体クラス、行動／同時に学習\[33\]
- 手法の位置: S7
- 証拠: 改善を主張（Table 1・2 は未読）。「正解の 3 次元姿勢なしで SOTA」と主張\[33\]
- その他の欄: 不明
- 要点: 同時学習（多タスク）の例。相互作用 RNN が姿勢の推定にも効いたと主張している。\[33\]

#### C-7. MECCANO
- 書誌: Ragusa, Furnari, Livatino, Farinella／2021／The MECCANO Dataset…／WACV 2021（査読つき）／arXiv 2010.05654。多モーダル版は CVIU 235（2023）、arXiv 2209.08691、DOI 10.1016/j.cviu.2023.103764
- 読んだ範囲: 要旨とプロジェクトページ
- 近さ: 方向 3／一人称／工業風の組立／行動認識、active object の検出・認識、EHOI 検出、予測、next active object の検出／動詞\[34\] 12、物体 20、行動 61 クラス。active object の枠 64,349\[35\]\[36\]
- 手法の位置: S1・S8
- 追試・採用: Sequential Voting（C-11）が評価に使用\[37\]
- 実装: データ公開。多モーダル版は視線と深度を含む
- その他の欄: 不明
- 要点: 時間の行動区間と、active object の枠・クラスの両方を持つ一人称データセット（問い (7)）。\[38\]相互作用の出力を下流の行動認識へ入れた既発表の値は見つけていない。

#### C-8. ENIGMA-360
- 書誌: 著者は抜粋で確認できず／2026／ENIGMA-360: An Ego-Exo Dataset for Human Behavior Understanding in Industrial Scenarios／arXiv プレプリント／arXiv 2603.09741
- 読んだ範囲: 要旨と抜粋
- 近さ: 方向 3／一人称と三人称／工業／時間的行動分割、keystep 認識、EHOI 検出（手と操作物体のマスク。SAM を使用）\[39\]
- 手法の位置: S9（データ）
- その他の欄: 不明
- 要点: keystep の時間ラベルと HOI のマスクを同じ動画に持つ（問い (7)）。\[39\]HOI を keystep へ入れた結果は見つけていない。

#### C-9. Finocchiaro ほか（産業での実時間 HOI 検出）
- 書誌: Finocchiaro, Catinello, Mazzamuto, Leonardi, Furnari, Farinella／2025／A Real-Time System for Egocentric Hand-Object Interaction Detection in Industrial Domains／arXiv プレプリント（v2 は 2025-12-04）／arXiv 2507.13326
- 読んだ範囲: 要旨のみ
- 近さ: 方向 3／一人称／工業／流れてくる映像 → 接触の状態（行動認識）→ 接触と判定したフレームだけ active object を検出／online（ストリーミング、30 fps）／ENIGMA-51／段階型（Mamba＋EfficientNetV2 → YOLOWorld）\[40\]
- 手法の位置: S9
- 証拠: 行動認識 38.52% p-AP、YOLOWorld は手と物体で 85.13% AP（要旨）。\[40\]段階型と単独型の比較の値は要旨にない
- その他の欄: 不明
- 要点: 「相互作用の認識が検出を起動する」連結構成である。\[40\]検出 mAP の改善を測ったものではない。

#### C-10. Lu & Mayol-Cuevas（HOI 状態の検出と応用）
- 書誌: Yao Lu, Walterio Mayol-Cuevas／2021／Egocentric Hand-object Interaction Detection and Application／arXiv プレプリント／arXiv 2109.14734（内容が大きく重なる版として arXiv 2211.09067）\[41\]\[42\]
- 読んだ範囲: 要旨のみ
- 近さ: 方向 3／一人称／手の姿勢、手のマスク、手の中の物体のマスク → HOI 状態。応用は台本のない活動の区間分け／段階型\[41\]\[43\]\[44\]
- 手法の位置: S9
- 証拠: F1 は GTEA 68.2%、UTGrasp 82.8%。EPIC の選択画像で正解率 89%（Shan ほかは 92%）（要旨）\[41\]\[44\]
- その他の欄: 不明
- 要点: 種の文献の実在を確認した。行動区間への応用はあるが効果量は要旨にない。2211.09067 版の抜粋には MS-TCN との比較の記述がある（数値は未読）。\[43\]

#### C-11. Sequential Voting with Relational Box Fields（active object 検出）
- 書誌: 著者・会議名は抜粋で確認できず／2021／Sequential Voting with Relational Box Fields for Active Object Detection／arXiv 2110.11524
- 読んだ範囲: 抜粋のみ（4.2 節）
- 近さ: 方向 3／一人称／画像と手 → active object の枠／MECCANO では、手の枠と「中心が最も近い active object を各手に割り当てる」規則で作った疑似ラベルで学習し直す\[37\]
- 手法の位置: S8・S10
- 証拠: MECCANO で、再学習なしの AP50 が 100DOH 11.17 に対して本手法 16.61（表番号は未確認）\[37\]
- その他の欄: 不明
- 要点: 手と物体の対応を幾何の規則で決めた疑似ラベルで HOI モデルを学習した例（問い (10)）。規則ラベルの品質を変えた比較は見つけていない。

#### C-12. HOI-Synth（合成データは一人称 HOI 検出に有用か）
- 書誌: Leonardi ほか（推定）／2024／Are Synthetic Data Useful for Egocentric Hand-Object Interaction Detection?／ECCV 2024（査読つき）／arXiv 2312.02672
- 読んだ範囲: 要旨と HTML の抜粋
- 近さ: 方向 3／一人称／画像 → 手、接触状態、active object のマスク／VISOR、EgoHOS、ENIGMA-51／半教師ありの領域適応\[26\]\[45\]
- 手法の位置: S10
- 証拠: 実データのラベル 10% のとき、実データだけの場合に比べて Overall AP が VISOR +5.67、EgoHOS +8.24、ENIGMA-51 +11.69（要旨）\[26\]
- その他の欄: 不明
- 要点: 少ないデータで HOI モデルを学習した証拠（問い (10)）。下流の行動・手順への利得は測っていない。

#### C-13. Tateno ほか（映像言語モデルは手と物体の両方の手がかりを使うか）
- 書誌: Masatoshi Tateno, Alexandros Stergiou, Risa Shinoda, Yoichi Sato, Dima Damen／2026／Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?／arXiv プレプリント／arXiv 2607.08514\[46\]
- 読んだ範囲: 要旨と HTML の抜粋
- 近さ: 方向 3・7／一人称／手だけ、または物体だけを残した映像（inpainting で分離）→ 動詞／EgoClip で学習、DEHOI で評価／100DOH の枠を学習時のマスクに使う\[23\]\[46\]
- 手法の位置: S4
- 証拠: 既存モデル（LaViLa、Helping Hands など）は物体中心の条件で大きく劣化（抜粋の記述。数値は書かない）\[23\]
- その他の欄: 不明
- 要点: 「一人称映像だけで学習したモデルは手の手がかりに頼り、物体を使い切れていない」と報告している。\[47\]手の補助信号が物体（術具）側へ効くとは限らないことを示す。

#### C-14. Next active object の系統（まとめて 1 ブロック）
- 書誌:
  - Furnari, Battiato, Grauman, Farinella／2017／Next-active-object prediction from egocentric videos／J Vis Commun Image Represent（査読つき）／ID 不明
  - ANACTO（arXiv 2302.06358）
  - Enhancing Next Active Object-based Egocentric Action Anticipation with Guided Attention（ICIP 2023、arXiv 2305.12953）
  - Leveraging Next-Active Objects for Context-Aware Anticipation（WACV 2024、arXiv 2308.08303）
  - AFF-ttention!（ECCV 2024、arXiv 2406.01194）
- 読んだ範囲: すべて要旨と抜粋
- 近さ: 方向 3／一人称／過去の映像 → 次に接触する物体の位置（と行動・接触までの時間）／過去のみ\[48\]
- 証拠: Furnari 2017 の抜粋では「手の位置の偏り（hand bias）を使う基準は良い性能に達しない」\[49\]
- その他の欄: 不明
- 要点: ANACTO は手の情報を明示的に使わず、物体検出器の出力を入れて次の active object を予測する。\[50\]next active object の予測を物体検出の mAP の改善として測った研究は見つからなかった。

### D. 方向 4（一般映像）

#### D-1. ORViT【本文を読んだ】
- 書誌: Herzig, Ben-Avraham, Mangalam, Bar, Chechik, Rohrbach, Darrell, Globerson／2022／Object-Region Video Transformers／CVPR 2022（査読つき）／arXiv 2110.06915
- 読んだ範囲: 本文（1〜4.4 節、Table 1〜3）。補足資料の oracle の数値は本文の記述から
- 近さ:
  - 方向 4（EK100 は 3）／三人称と一人称（EK100）／非医療
  - 課題: 映像と物体の枠（追跡は SORT）→ 行動／offline（クリップ単位）\[3\]
  - データ: SSv2 174 クラス、EK100、Diving48、AVA\[3\]
  - モデルの状態: 検出器（Faster R-CNN）とは重みを共有しない。EK100/Diving48 では COCO で事前学習した検出器をクラスを無視して使う。受け取り側は学習する\[3\]
- 手法の位置: S3／ORViT は不明（直近 2 年の比較表を未確認）。STIN/STRG は SSv2 で置き換え済み（本論文 Table 3a）
- 証拠:
  - 比較: 同じ基盤に ORViT ブロックを加えた場合と加えない場合（ブロックが層 2・7・11 を置き換えるだけの単独要因の比較）\[3\]
  - EK100（Table 3c）: MF-HR に対して、行動 44.5→45.7、動詞 67.0→68.4、名詞 58.5→58.7\[3\]
  - SSv2（Table 3a）: MF 66.5→67.9。一方、MF+STIN 66.5、MF+STRG 66.1、MF+STRG+STIN 66.6 で、既存の枠ベース方式は改善しなかった\[3\]
  - SSv2 で正解枠（oracle）を入れると MF より +7.3、MF-L より +6.7（補足資料 D.2、本文の記述）\[3\]
  - 符号が変わる条件: 著者は EK100 の利得が小さい理由として、一人称のカメラの動きと、2〜3 秒の短いクリップを挙げる。\[3\]枠の品質（検出枠と正解枠）で利得が大きく変わる
  - 基準の強さ: 当時の強いモデル（MF-HR は EK100 の最良として引用）
  - seed・検定: 記述なし
- 実装: プロジェクトページで公開と記載\[3\]
- 要点: 推論時に外部検出器の枠を入れると、強い基盤の上でも SSv2 で +1.4。一人称の EK100 の名詞ではほとんど効かなかった（+0.2）。\[3\]

#### D-2. Multimodal Distillation for Egocentric Action Recognition【本文を読んだ】
- 書誌: Gorjan Radevski, Dusan Grujicic, Marie-Francine Moens, Matthew Blaschko, Tinne Tuytelaars／2023／Multimodal Distillation for Egocentric Action Recognition／ICCV 2023（査読つき）／arXiv 2307.07483
- 読んだ範囲: 本文（1〜4.1.4 節、Table 1〜4）
- 近さ:
  - 方向 4・5（EK100 は 3）／一人称（EK100）と手元の映像（SSv2）／非医療
  - 課題: RGB → 行動。教師は RGB、光学フロー、音、物体検出（手と物体の枠とカテゴリ、STLT で符号化）／offline\[2\]
  - モデルの状態: 物体検出は物体を区別しない検出器（「hands」と「objects」）で別に作る。教師はモダリティごとに別学習。生徒（Swin-T）は全体を学習\[2\]
- 手法の位置: S5／新興（著者以外の採用は arXiv 2504.08578 などの引用にとどまる）／SSv2、Something-Else、EK100、EK100 Unseen。EK100 の実験では物体検出を使っていない
- 証拠:
  - 主比較: RGB だけで学習した基準と、RGB と物体検出の教師から蒸留した RGB 生徒（推論は RGB だけ）。SSv2（Table 2b）60.3→63.2（+2.9）、Something-Else（Table 3b）51.8→57.5（+5.7）\[2\]
  - 推論時に使う場合との差: 教師（RGB と物体検出を推論時にも使う）は SSv2 で 65.3、Something-Else で 59.4。生徒との差は 2.1 点と 1.9 点\[2\]
  - 物体検出だけのモデル: SSv2 で 47.9、Something-Else で 41.4（Table 2b、3b）\[2\]
  - 符号が変わる条件: 弱い教師（音）を混ぜると名詞が悪化する。EK100 で RGB と音の生徒は名詞 −0.5、行動 −0.4（Table 2a）。教師を重みづけする温度 γ で対処（4.2 節）\[2\]
  - 基準の強さ: Swin-T（中程度）
  - 単独要因の比較か: 教師のモダリティだけを変えた比較
  - seed・検定: 記述なし。最終エポックのモデルを報告（脚注 1）\[2\]
- 実装: コード公開（GitHub）
- 要点: 手と物体の検出の情報を学習時だけ使う形（蒸留）にしても、推論時にも使う形に比べて失う利得は約 2 点だった。物体を変えた汎化（Something-Else）で利得が大きい。

### E. 方向 5（機構の一般論）

#### E-1. 特権情報・モダリティ蒸留（まとめて 1 ブロック）
- 書誌:
  - Luo ほか／2018／Graph Distillation for Action Detection with Privileged Modalities／ECCV 2018（査読つき）／arXiv 1712.00108
  - Garcia, Morerio, Murino／2019／Learning with privileged information via adversarial discriminative modality distillation／IEEE TPAMI 42(10)（査読つき）／ID 不明（会議版は arXiv 1806.07110）\[51\]
  - Progressive privileged knowledge distillation for online action detection／Pattern Recognition 2022／ID 不明（ScienceDirect の記事番号 S0031320322002229）
  - Vapnik ほかの LUPI 原典: 今回は確認できなかった（ID 不明・未確認）
- 読んだ範囲: 要旨と抜粋のみ
- 要点:
  - Luo ほかは「目標側の学習データが小さいとき、推論時に一つのモダリティしか無いときに有効」と要旨で述べる。\[52\]\[53\]
  - Progressive Privileged KD は、online 行動検出で「学習時だけ見える未来のフレーム」を特権情報とし、offline の教師から online の生徒へ蒸留する。\[54\]online の制約と特権情報を組み合わせた例（問い (9)）である。
  - いずれも手・相互作用を特権情報にした例ではない。効果量は本文未読のため書かない。

### F. 方向 6（方法論：情報の漏れ）

#### F-1. Leak-Free Cross-Validated Stacking
- 書誌: 著者は抜粋で確認できず／2026／Leak-Free Cross-Validated Stacking with Per-Architecture Calibration for Sand-Boil Segmentation in Earthen Levees／arXiv プレプリント／arXiv 2607.25367
- 読んだ範囲: 抜粋のみ
- 近さ: 方向 6／非医療（画像の分割）／複数の分割モデル → メタ学習器（stacking）\[55\]
- 証拠: nested CV で、メタ学習器が試験時と同じ「折りの平均の予測」で学習されるようにすると、stacking の値が 0.681→0.691（表番号は未確認）\[56\]
- その他の欄: 不明
- 要点: 上流モデルの予測は、その例を見ていない折りから作る（out-of-fold）べきだとしている。加えて、学習時の上流予測（単一の折りのモデル）と試験時の上流予測（折りの平均）の分布のずれも結果を変える、と報告している。\[55\]\[56\]映像・HOI での同種の報告は見つからなかった。

---

## (3) 探したが見つからなかったもの

| 探したもの | 検索語（代表） | 調べた件数 | 無かったもの |
|---|---|---|---|
| EgoSurgery-HTS/Tool を使った工程・術具の研究 | 「EgoSurgery phase recognition hand tool interaction open surgery 2025」、サブ調査の被引用一覧 | 検索 約 10 件、被引用 約 12 件 | 手・把持の出力で工程か術具検出を改善した研究（0 件） |
| 凍結した HOI モデル → 小さな界面 → 凍結した検出・工程モデル | 「hand-object interaction features improve egocentric action recognition」ほか | 約 20 件 | 受け取り側を凍結し界面だけを学習する構成で、HOI を検出か工程へ渡した研究 |
| HOI による物体検出 mAP の改善（クラス別） | 「active object detection egocentric hand-object interaction improves object detection rare classes」 | 約 10 件 | 稀少・小さい・紛らわしいクラス別の検出 mAP の改善（Ego-HOIBench の rare 区分は HOI 三つ組の mAP で、二次資料で見ただけ） |
| 同時学習と凍結した別モデルの比較（問い (3)） | 各検索に含めて探した | — | HOI 情報だけについての直接比較（Radevski の Omnivore 比較〔Table 4〕は全モダリティの比較） |
| 学習した HOI モデルと「手の検出＋枠の重なり規則」の比較（補足 2） | 「hand-object detector features … ablation」ほか | 約 10 件 | 下流の利得としての ablation |
| 本人の手だけの定義と他者の手を含む定義（補足 3） | HOI、active object の検索 2 回 | 約 20 件 | 定義の違いの下流への影響（100DOH の接触状態に「other-person」はあるが、二次資料で見ただけ） |
| 低いフレームレート（0.5 fps 前後）での HOI → 行動・手順（補足 4） | 検索の中で併せて探した | — | 該当研究、フレームレートを下げた比較（Goldbraikh の 30 fps と 3 fps は数値未読） |
| 交差検証の折りの内側で補助モデル・教師を学習し直すか（補足 1） | 「stacking cross-validation leakage teacher model nested cross-validation …」 | 約 10 件 | 映像・医療・HOI での teacher leakage の測定（一般の stacking では F-1 のみ） |
| 補助注釈が一部の動画にしか無い条件での拡張（補足 6） | Helping Hands を経由して探した | — | 疑似ラベルや蒸留で補助信号を広げた手術の研究 |
| 強い受け取り側で HOI の利得が消える報告（問い (8)） | 「… no improvement strong backbone ablation」 | 約 10 件 | 否定的報告を主題にした論文（部分的な所見は ORViT Table 3、C-13） |
| HOI の推論精度と下流の利得の関係（問い (8)） | — | — | 系統的な測定（部分的には Helping Hands Table 2、ORViT の oracle） |
| Rolling-Unrolling LSTM、HOI4D、H2O、ARCTIC、HoloAssist、Ego-Exo4D、EgoPER、POV-Surgery、VISOR | 検索予算の都合で個別には探していない | 0 | 実在は確認していない（記録なし） |

---

## (4) 未検証の組み合わせ（文献を並べて分かる、誰も測っていない条件）

1. **受け取り側を両方凍結＋小さな界面＋HOI 出力**: Helping Hands は「凍結した受け取り側＋学習する decoder＋凍結した HOI 教師」の形だが、下流は検索と分類である。この形を検出 mAP や online の工程 Jaccard で測った例はない。
2. **HOI → 物体検出の mAP（クラス別）**: HOI が active object の分類を助ける報告（Shimizu 2021、EgoHOS Table 5）はあるが、標準の検出 mAP をクラス別に改善として測った例はない。
3. **online＋低いフレームレート＋HOI**: online の HOI（2507.13326、30 fps）、予測（InAViT、next active object）、online の特権情報（Progressive Privileged KD）は別々にある。0.5 fps での組み合わせはない。
4. **規則（枠の重なり）と学習した HOI モデルの下流比較**: 規則で作った疑似ラベル（EgoHOS の接触境界、Sequential Voting の中心距離の割り当て、EgoSurgery-HTS の IoU 最大）で学習した例はある。同じ規則を推論時に直接使った場合との比較はない。
5. **本人の手だけの定義と他者の手を含む定義の比較**: EgoSurgery-Tool は他者の手の枠を持つが、HTS の把持は本人の手だけである。下流への影響を測った例はない。
6. **交差検証の折りの内側で HOI 教師を学習し直す場合と、全動画で学習した場合の比較**: 一般の stacking には報告がある（F-1）。映像の蒸留・補助損失ではない。
7. **左右の区別の有無**: Helping Hands は左右二つの手の問い合わせを使うが、区別しない場合との比較はない（Table 5 は手の有無）。EgoHOS も同様。
8. **少数の動画（15 本規模）での HOI → 工程**: HOI-Synth（ラベル 10%）は HOI 検出そのものの評価までで、下流は測っていない。

---

## (5) 検索記録

- 検索日: 2026-10-31（本調査の web_search 18 回。サブ調査 1 回の内部検索は別）
- 方向 1（3 件を記録）: 「EgoSurgery-HTS hand tool segmentation egocentric open surgery arXiv 2503.18755」「EgoSurgery phase recognition hand tool interaction open surgery 2025」。サブ調査で被引用一覧を確認
- 方向 2（6 件）: 「Visual Modalities Based Multimodal Fusion for Surgical Phase Recognition Park 2022 tool detection hand」「surgical phase recognition hand tracking open surgery video hands improve workflow」。サブ調査で CholecT50、Shimizu 2021、Goldbraikh 2022 を確認
- 方向 3（14 件。手術・医療の語を含まない検索 10 回）: 例「hand-object interaction features improve egocentric action recognition」「Helping Hands object-aware egocentric video recognition model hand object boxes」「next active object detection egocentric Furnari anticipation hand」「temporal action segmentation hand-object interaction features egocentric procedural keystep」
- 方向 4（2 件）: 「ORViT object-region video transformer hand object boxes action recognition」と方向 3 の検索の結果
- 方向 5（1 ブロック）: 「privileged information action recognition distillation training-only modality egocentric」
- 方向 6（1 件）: 「stacking cross-validation leakage teacher model nested cross-validation meta-learner out-of-fold predictions」
- 方向 7（独立の論文は 0 件。所見は他の記録の中）: 「hand-object detector features temporal action segmentation egocentric no improvement strong backbone ablation」
- 予算切れで実行できなかった検索: Cholec80 での凍結検出器特徴の融合、Assembly101 での手の姿勢の行動分割への融合

---

## (6) あなたの解釈と提案（事実と分けて、ここにだけ書く）

**解釈**
- 見つかった証拠は一つの傾向で揃っている。HOI の信号は「動作（動詞）」と「物体の組み合わせの汎化」には効くが、「どの物体か（名詞・物体クラス）」への上乗せは小さい。根拠は EgoHOS（動詞 +2.0 に対して名詞 +0.3）、ORViT（EK100 の名詞 +0.2）、Assembly101（姿勢は物体で −10.2）、Tateno ほか（一人称のモデルは手に頼りがち）である。このため、把持の出力を術具検出（15 クラスの物体の識別）へ渡す経路は、工程認識へ渡す経路より利得が小さいと予想する。
- 利得は補助信号の品質に強く連動している（Helping Hands Table 2、ORViT の oracle で +7.3）。EgoSurgery-HTS の把持ラベルは枠や IoU の規則と SAM から作られており、把持モデルが規則以上の情報を持つかは自明でない。
- 推論時に使う場合と学習時だけ使う場合の差は、Radevski ほかの SSv2 で約 2 点だった。(b) を採っても利得の大半は残りうる。ただしこれは SSv2 での一例である。

**提案（依頼者の設定向け）**
1. **漏れの対策を最初に固定する**: 把持モデルは、評価の折りごとに、その折りの訓練動画（15 本のうち 12 本）だけで学習し直す。界面と蒸留の学習データも同じ折りの内側に限る。全動画で学習した把持モデルの腕は、漏れの大きさを測る参照として別に報告する。F-1 が示す「学習時と試験時の上流予測の分布のずれ」に備え、界面の学習用の把持出力は内側の交差検証の out-of-fold 予測で作ることを検討する。
2. **規則の基準を必ず置く**: 「凍結した検出モデルの手と術具の枠＋IoU 最大の規則」で作った把持の状態を、学習した把持モデルと同じ界面へ入れる腕を置き、上乗せの有無（補足 2）を分ける。正解の把持（oracle）を入れる腕も上限として置く（ORViT 型の比較）。
3. **(b) の設計**: 凍結した受け取り側の上の小さな decoder に、把持の補助損失を Helping Hands 型でかける。推論時の依存がなく、21 本の工程動画のうち把持注釈のない 6 本にも、折りの内側で学習した把持モデルの疑似ラベルで補助信号を広げられる（補足 6）。広げた場合と広げない場合を比べる。
4. **評価の分解**: 検出はクラス別 AP を、稀少クラス、小さいクラス、紛らわしい組（形の似た術具）に分けて報告する（Shimizu 2021 の問題設定）。工程は、手が写るフレームと写らないフレームに分けて Jaccard を報告する。
5. **左右と本人の手の定義**: 左右を区別しない把持（2 クラスに縮約）の腕を置いて左右の寄与を測る（Sun & Zhang の左右の判別 67〜71% から、手術映像では左右の誤りが多い可能性がある）。EgoSurgery-Tool の「他者の手」の枠を使う定義との比較も、検出の側でだけなら実行できる。
6. **統計**: 動画は 15 本で 5 折りなので、腕の間の差は動画単位の対応のある比較（並べ替え検定かブートストラップ）で示す。seed を 3 個以上にし、seed のばらつきと腕の差を並べて報告する。既存の文献の多くは seed の数も検定も報告していないため、比較できる文献がない。

## 出典

1. <https://arxiv.org/pdf/2308.07918>
2. <https://arxiv.org/html/2307.07483v2>
3. <https://arxiv.org/pdf/2110.06915>
4. [EgoSurgery‐HTS: A Dataset for Egocentric Hand–Tool Segmentation in Open Surgery Videos - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12686825/)
5. [EgoSurgery‐HTS: A Dataset for Egocentric Hand–Tool Segmentation in Open Surgery Videos](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12686825/)
6. [EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos](https://arxiv.org/html/2503.18755)
7. [EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos](https://arxiv.org/pdf/2503.18755)
8. [EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos](https://arxiv.org/pdf/2406.03095)
9. [EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos](https://arxiv.org/html/2406.03095)
10. [SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos](https://arxiv.org/pdf/2602.05638)
11. [Surgical workflow recognition on EgoSurgery (test) benchmark leaderboard · SOTA2 Research](https://www.sota2.com/research/sota/surgical-workflow-recognition-on-egosurgery-test)
12. [Visual modalities-based multimodal fusion for surgical phase recognition - PubMed](https://pubmed.ncbi.nlm.nih.gov/37774560)
13. [Visual Modalities Based Multimodal Fusion for Surgical Phase Recognition](https://dl.acm.org/doi/abs/10.1007/978-3-031-18814-5_2)
14. [Visual modalities-based multimodal fusion for surgical phase recognition - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0010482523009186)
15. [Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera](https://doi.org/10.3390/jimaging7020015)
16. [Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera](https://www.mdpi.com/2313-433X/7/2/15)
17. [Open surgery tool classification and hand utilization using a multi-camera system - PubMed](https://pubmed.ncbi.nlm.nih.gov/35759176/)
18. [Enhancing open-surgery gesture recognition using 3D pose estimation](https://link.springer.com/article/10.1007/s11548-025-03564-1)
19. [Enhancing open-surgery gesture recognition using 3D pose estimation - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13194309/)
20. [YOLOv10-Based Multi-Task Framework for Hand Localization and Laterality Classification in Surgical Videos](https://arxiv.org/abs/2602.18959)
21. [(PDF) Using Computer Vision to Automate Hand Detection and Tracking of Surgeon Movements in Videos of Open Surgery](https://www.researchgate.net/publication/351853377_Using_Computer_Vision_to_Automate_Hand_Detection_and_Tracking_of_Surgeon_Movements_in_Videos_of_Open_Surgery)
22. [Using Computer Vision to Automate Hand Detection and Tracking of Surgeon Movements in Videos of Open Surgery - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8127677/)
23. [Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?](https://arxiv.org/html/2607.08514)
24. <https://arxiv.org/pdf/2208.03826>
25. [Fine-Grained Egocentric Hand-Object Segmentation: Dataset, Model, and Applications](https://arxiv.org/abs/2208.03826)
26. [Are Synthetic Data Useful for Egocentric Hand-Object Interaction Detection?](https://arxiv.org/html/2312.02672v2)
27. [GitHub - s-shamil/HandFormer: \[ECCV '24\] On the Utility of 3D Hand Poses for Action Recognition · GitHub](https://github.com/s-shamil/HandFormer)
28. [WACV 2024 Open Access Repository](https://openaccess.thecvf.com/content/WACV2024/html/Roy_Interaction_Region_Visual_Transformer_for_Egocentric_Action_Anticipation_WACV_2024_paper.html)
29. [\[2211.14154\] Interaction Region Visual Transformer for Egocentric Action Anticipation](https://arxiv.org/abs/2211.14154)
30. [On the Utility of 3D Hand Poses for Action Recognition](https://arxiv.org/pdf/2403.09805)
31. [Supplementary: On the Utility of 3D Hand Poses for Action Recognition](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/01025-supp.pdf)
32. [Assembly101: A Large-Scale Multi-View Video Dataset for Understanding Procedural Activities](https://arxiv.org/pdf/2203.14712)
33. [H+O: Unified Egocentric Recognition of 3D Hand-Object Poses and Interactions](https://arxiv.org/html/1904.05349)
34. [MECCANO: A Multimodal Egocentric Dataset for Humans Behavior Understanding in the Industrial-like Domain](https://iplab.dmi.unict.it/legacy/MECCANO/)
35. [The MECCANO Dataset: Understanding Human-Object Interactions from Egocentric Videos in an Industrial-like Domain](https://iplab.dmi.unict.it/MECCANO_first_version/)
36. [\[2209.08691\] MECCANO: A Multimodal Egocentric Dataset for Humans Behavior Understanding in the Industrial-like Domain](https://ar5iv.labs.arxiv.org/html/2209.08691)
37. [Sequential Voting with Relational Box Fields for Active Object Detection](https://arxiv.org/pdf/2110.11524)
38. [\[2010.05654\] The MECCANO Dataset: Understanding Human-Object Interactions from Egocentric Videos in an Industrial-like Domain](https://arxiv.org/abs/2010.05654)
39. [ENIGMA-360: An Ego-Exo Dataset for Human Behavior Understanding in Industrial Scenarios](https://arxiv.org/html/2603.09741)
40. [A Real-Time System for Egocentric Hand-Object Interaction Detection in Industrial Domains](https://arxiv.org/abs/2507.13326)
41. [\[2109.14734\] Egocentric Hand-object Interaction Detection and Application](https://arxiv.org/abs/2109.14734)
42. [Egocentric Hand-object Interaction Detection - ADS](https://ui.adsabs.harvard.edu/abs/2022arXiv221109067L/abstract)
43. [(PDF) Egocentric Hand-object Interaction Detection](https://www.researchgate.net/publication/365450017_Egocentric_Hand-object_Interaction_Detection)
44. [Egocentric Hand-object Interaction Detection and Application](https://deepai.org/publication/egocentric-hand-object-interaction-detection-and-application)
45. [Are Synthetic Data Useful for Egocentric Hand-Object Interaction Detection?](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08953.pdf)
46. [\[2607.08514\] Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?](https://arxiv.org/abs/2607.08514)
47. [Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?](https://arxiv.org/html/2607.08514v1)
48. [AFF-ttention! Affordances and Attention models for Short-Term Object Interaction Anticipation](https://arxiv.org/html/2406.01194v2)
49. [Next-Active-Object Prediction from Egocentric Videos - IPLab](https://iplab.dmi.unict.it/NextActiveObjectPrediction/downloads/furnari2017next.pdf)
50. [Anticipating Next Active Objects for Egocentric Videos](https://arxiv.org/html/2302.06358v5)
51. [Exploring Missing Modality in Multimodal Egocentric Datasets](https://arxiv.org/pdf/2401.11470)
52. [Graph Distillation for Action Detection with Privileged Modalities](https://arxiv.org/pdf/1712.00108)
53. [Graph Distillation for Action Detection with Privileged Modalities](https://openaccess.thecvf.com/content_ECCV_2018/papers/Zelun_Luo_Graph_Distillation_for_ECCV_2018_paper.pdf)
54. [Progressive privileged knowledge distillation for online action detection - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0031320322002229)
55. [Leak-Free Cross-Validated Stacking with Per-Architecture Calibration for Sand-Boil Segmentation in Earthen Levees](https://arxiv.org/pdf/2607.25367)
56. [Leak-Free Cross-Validated Stacking with Per-Architecture Calibration for Sand-Boil Segmentation in Earthen Levees](https://arxiv.org/html/2607.25367v1)

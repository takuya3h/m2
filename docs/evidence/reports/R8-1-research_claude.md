# 把持（手と物体の相互作用）推論を検出・行動/工程認識へ渡す研究の文献調査（R8、2026-10-31）

把持（手と物体の相互作用）の推論モデルを独立に学習して凍結し、その出力で物体検出と行動・手順・工程の認識の両方を改善した研究は、手術・非手術のいずれでも見つからなかった。片方だけを改善した近い研究はあり、(a) 推論時に渡す形と (b) 学習時だけ教師にする形の両方で、利得と、利得が消える条件が報告されている。

## TL;DR
- 「独立学習・凍結した把持モデル → 検出と工程（行動）の両方を改善」という形の研究は無く、EgoSurgery-HTS（arXiv 2503.18755）を下流の検出や工程認識に使った研究も 0 件だった。新規性の主張は成り立つ見込みが高いが、一人称の開放手術では Shimizu ほか 2021（手の動きで術具の分類を補助、推論時に入力）が最も近い先行研究なので、必ず引用・比較すること。
- 非手術では、(a) の形として G3Ego（凍結した検出器の手の枠と、枠の重なりで決めた接触物体の 20 次元特徴を推論時に入れる。MECCANO で Top-1 41.91→46.48、表 1）がある。(b) の形として Helping Hands（100DOH の疑似の枠を補助損失にする）、HOCL（Shiota ほか、WACV 2024）、Radevski ほかの多モーダル蒸留（物体・手の検出を教師にし、推論時は RGB だけ）がある。(b) の利得は (a) の約 6〜7 割にとどまった（Something-Something で 60.3→63.2 対 65.3、表 2b）。
- 否定的な結果もある。HOCL は強い受け取り側（Swin-B）や EPIC 事前学習の後では悪化した（MECCANO で 44.03→42.01、EPIC-100 の action で 34.39→32.72）。上流の精度が下流の利得を左右するという報告（Helping Hands の表 2、AssemblyHands）もある。0.5 fps・15 本・SAM 由来のマスクという条件で効果を確かめた研究は無い。

---

## 最初に書くこと（依頼の【最初に書くこと】への回答）

**見つからなかった。** 把持（手と物体の相互作用）の推論モデルを独立に学習・凍結し、その出力で物体検出と行動・手順・工程の認識の両方を改善した研究は、手術・医療を含め見つからなかった。片方だけを改善した近い研究は次のとおりで、形 (a)/(b) を付ける。

- 手術・医療（新規性の確認に要るため冒頭に置く）
  - Shimizu ほか 2021（doi 10.3390/jimaging7020015）: 一人称の開放手術。手の検出の枠と、IoU が最大の手と術具の対応づけ、その手の切り出し画像の時系列を術具の分類に入れる。**(a)\[1\]\[2\] に近い形**（推論時に入力）。ただし把持モデルを別に学習・凍結した形ではなく、検出と分類をつないだ一連の処理である。下流は術具の分類（検出の一部）で、工程認識は扱っていない（記録 R19。サブエージェント経由の情報）。
  - Park ほか 2022（doi 10.1007/978-3-031-18814-5_2）と 2023 年の論文誌版（doi 10.1016/j.compbiomed.2023.107453）: 腹腔鏡の胃切除。セグメンテーションのマスクから術具の動きと術具どうしの関係を表す指標（VKI）を作り、CNN 特徴と融合して工程を認識する。**(a)\[3\]\[4\] の形**（推論時に入力）。ただし扱うのは手ではなく術具どうしの相互作用である（記録 R20、要旨のみ）。
  - EgoSurgery-HTS を使った下流研究: **0 件**（記録 R16 と問い (11) の節）。
- 非手術（行動・手順の側）
  - G3Ego（arXiv 2608.20157）: **(a)**（記録 R5）
  - Helping Hands（arXiv 2308.07918）: **(b)**。凍結した 100DOH の出力を補助損失の教師にする（記録 R1）
  - HOCL/OSL（Shiota ほか WACV 2024）: **(b)**。100DOH で作ったマスク映像を、相互学習（deep mutual learning）の相手に渡す（記録 R4）
  - Radevski ほか ICCV 2023（arXiv 2307.07483）: **(b)**。手と物体の検出を入力にした教師から蒸留する（記録 R3）
- 非手術（検出の側）
  - Helping Hands は、100DOH の疑似の枠で学習した結果、接触物体の位置特定が教師の検出器を上回った（VISOR、表 7）。\[5\]ただし検出の mAP ではなく、grounding の評価である。
  - Finocchiaro ほか（arXiv 2507.13326）は、接触状態の認識が物体検出を起動するカスケード（形 (a) の一種のゲート）である。\[6\]ただし、ゲートの有無による検出の差は要旨からは読めない（記録 R8）。

---

## 問いと記録の対応表

| 問い | 答えの所在（節／記録） | 一言の答え |
|---|---|---|
| (1) HOI 出力 → 行動・手順・予測 | R5, R4, R1, R3, R6, R7, R13, R20 | (a) の形の例は G3Ego（手の枠＋接触物体の 20 次元特徴、MECCANO で Top-1 +4.57）。正解の把持と予測の把持の差は、本文を読んだ範囲では報告が無い |
| (2) HOI → 物体検出・認識、active / next active object | R1（表 7）, R8, R14, R15, R19 | 検出の mAP を、クラス別（稀少・小物体・紛らわしいクラス）に分けて改善を示した研究は見つからなかった |
| (3) 凍結して渡す形と同時学習の比較 | R3（Omnivore との比較）、(3) の節 | 直接の比較は見つからない。最も近いのは、蒸留と Omnivore（全モーダルの同時学習）の比較（R3） |
| (4) 学習時だけ使う（LUPI・蒸留・補助損失） | R1, R3, R4, R28 | 有り。推論時に入れる場合との差は R3 の表 2b・表 3 |
| (5) 表現の系統と効き方 | 系統表、R6, R7, R5, R1, R2 | 枠・接触は名詞（物体）側、3 次元の手の姿勢は動詞側に効く傾向（R7: Assembly101 で、姿勢は verb +6.7、object −10.2） |
| (6) 左右・両手 | R1, R5, R7, R9, R16 | 左右を区別した表現は多いが、区別の有無だけを変えた比較は見つからない |
| (7) データセット一覧と既発表の値 | 問い (7) の表 | 下の表 |
| (8) 効かなかった・強いモデルで消えた・上流精度との関係 | R4, R2, R6, R29, R1（表 2） | 有り（HOCL は Swin-B や EPIC 事前学習の後で悪化） |
| (9) online の制約 | R8, R14, R5（予測）、(3) の節 | online で使う研究はあるが、同じフレームを使う場合と前の時刻までを使う場合を比べた研究は見つからない |
| (10) 少数データ・疑似ラベルの品質 | R1（表 2）, R4, R10, R16 | 疑似の枠の解像度（品質）で下流が約 1 点変わる（R1 の表 2）。SAM 由来のマスクの品質の影響は見つからない |
| (11) 手術・EgoSurgery-HTS 全件 | R16〜R24、問い (11) の節 | HTS を下流に使った研究は 0 件 |

---

## (1) 系統表

| 系統 | 代表的な文献 | 現役度（どのベンチマークでの話か） | 記録の件数 |
|---|---|---|---|
| S1 手・物体の検出出力を推論時に入力（形 (a)） | STIN／Something-Else（既有）、Zhou ほか 2023（既有）、Li ほか（既有）、G3Ego（R5） | STIN: Something-Else の箱データと分割は 2023 年の R3 が利用（データとして定番の基準）。手法としては不明。Zhou ほか・Li ほか: 不明（比較表を確認せず）。G3Ego: 新興（MECCANO） | 2 |
| S2 疑似ラベルによる補助損失（学習時のみ。形 (b)） | Helping Hands（R1）、SViT（既有）、arXiv 2607.08514（R2） | Helping Hands: 定番の基準（EgoMCQ・EK-100 MIR・EGTEA のゼロショット。R2 と arXiv 2503.00986 が比較対象に使用）。SViT: 不明。R2: 新興 | 2 |
| S3 多モーダル蒸留・相互学習（形 (b)） | Radevski ほか（R3）、HOCL/OSL（R4） | R3: 不明（SSv2・Something-Else・EK-100）。R4: G3Ego の表 2（MECCANO）に載る（定番の基準の候補） | 2 |
| S4 3 次元の手の姿勢 | AssemblyHands（R6）、arXiv 2403.09805（R7） | arXiv 2403.09805: 本文の主張では Assembly101 の一人称行動認識で SOTA（表 4）。査読の有無は未確認 | 2 |
| S5 手・物体のマスク | EgoHOS（R12）、VISOR、EgoSurgery-HTS（R16）、Exo2EgoDVC（R13） | EgoHOS: 定番の基準（HOI 検出。arXiv 2312.02672 が使用） | 4 |
| S6 接触状態・HOI 検出 | 100DOH（要旨未読）、arXiv 2109.14734（R7b）、ENIGMA-51（R9）、HOI-Synth（R10）、arXiv 2507.13326（R8） | 100DOH の検出器: 定番の基準（R1・R4 と MECCANO の注釈づくりが上流として使用） | 5 |
| S7 next active object・予測 | Furnari ほか 2017（R14）、arXiv 2308.08303（R15）、Rolling-Unrolling LSTM（種） | R-ULSTM: G3Ego の表 4（MECCANO の予測）に載る（定番の基準） | 2 |
| S8 グラフ・シーングラフ | G3Ego（R5）、EgoExOR（R21） | 新興 | 2 |
| S9 視線と手 | G3Ego（R5）、GGMAE（R18）、Li ほか 2015（R29） | GGMAE: EgoSurgery-Phase での基準（新興） | 3 |
| S10 手術: 術具・手の情報を工程・検出へ | EndoNet（既有）、MTRCNet-CL（既有）、Park ほか（R20）、Shimizu ほか（R19） | EndoNet・MTRCNet-CL: Cholec80 での現役度は未確認（不明）。R19・R20: 不明 | 6 |
| S11 学習時の特権情報（LUPI） | Vapnik・Vashist（種。ID 未確認）、Gao ほか（R28） | 不明 | 1 |

---

## (2) 文献ごとの記録

### R1 Helping Hands
[書誌]
- Chuhan Zhang, Ankush Gupta, Andrew Zisserman／2023／Helping Hands: An Object-Aware Ego-Centric Video Recognition Model／ICCV 2023（査読つき）／arXiv 2308.07918（doi 10.1109/ICCV51070.2023.01278）\[7\]
- 読んだ範囲: 本文（付録の一部まで）
[近さ]
- 方向 3／一人称／非医療
- 課題の形: 映像と語りの対照学習。補助として手 2 個（左右）と物体の枠、物体名を予測する\[5\]
- 推論の規約: offline（4 フレームのクリップ）
- データ規模: EgoClip 380 万クリップ。100DOH で 1,600 万フレームから疑似の枠を作成\[5\]
- モデルの状態: 100DOH は凍結した上流。映像と文の符号化器も凍結し、物体を意識するデコーダだけを学習\[5\]
[手法の位置]
- 系統 S2／現役度: 定番の基準（EgoMCQ・EK-100 MIR・EGTEA のゼロショット。R2 と arXiv 2503.00986 が比較対象にしている）／一人称のみ
[証拠]
- 比較: (i) L_Ego だけと L_box・L_word を加えた場合（表 1）。(ii) 物体の枠だけと手＋物体の枠（表 5）。(iii) 疑似の枠を 256p と 640p から作った場合（表 2）
- 効果量:
  - 表 1: EK-100 MIR の平均 mAP 35.9→37.5、EGTEA の Top-1 44.9→46.6、平均クラス精度 37.6→39.1\[5\]
  - 表 5: 手の枠を加えると EK の平均 mAP 36.8→37.5\[5\]
  - 表 7: VISOR の接触物体の位置特定は、教師の検出器（GT マッチ）41.3 に対して本手法 82.3（4 クエリ）\[5\]
- 符号: 改善
- 条件: 疑似の枠の品質（表 2: 640p で EK・EGTEA が約 1% 高い）。物体クエリの数（表 7: 4 クエリ 82.3、12 クエリ 78.7）\[5\]
- 基準の強さ: 当時の SOTA（LaViLa-L）／表 1・表 5 は損失と予測対象だけを変えている／seed の数は不明、検定なし
- 不審な点:
  - 表 5 と表 2 では、EGTEA の Mean と Top1 の列と値の並びが逆に見える（表 1 では Top1 46.6、Mean 39.1）
  - 表 2 の 1 行目（256p、VISOR は「-」）の値 94.2/63.2/35.7/34.6/42.0/36.0 は、表 4 の LaViLa* の行と同一。基準の行である可能性がある
[実装]
- コード・重み: 公開（GitHub、ライセンス未確認）。語りと\[8\] 100DOH の検出結果が要る。EgoMCQ は学習データと同じ Ego4D 由来（著者も明記）
[要点]
- 疑似の手・物体の枠を、得られるフレームでだけ補助損失にすると、推論時に検出器なしで約 1〜2 点改善する。上流の枠の品質が利得を左右する。\[5\]

### R2 Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?
[書誌]
- Masatoshi Tateno, Alexandros Stergiou, Risa Shinoda, Yoichi Sato, Dima Damen／2026／プレプリント／arXiv 2607.08514\[9\]
- 読んだ範囲: 本文の一部（要旨・序論・関連研究・手法の前半）。表の数値は読めていない
[近さ・手法の位置]
- 方向 3／一人称／非医療／系統 S2／新興（DEHOI・STATUS Bench）
- 課題の形: 映像 → 動詞。手の側だけ、または物体の側だけを残すように inpainting した映像でも評価する（DEHOI／CI-HOI）\[9\]\[10\]
- モデルの状態: 同時に学習（手・物体のマスク学習と、位置・意味を補助予測する HDA デコーダ）。EgoClip で学習
[証拠]
- 比較: 既存の VLM（LaViLa、Helping Hands、EgoVideo）と、手中心・物体中心・元の映像の 3 条件（表 1）。効果量は不明（表は未読）
- 本文の記述: 一人称の映像だけで学習したモデルは手の手がかりに頼り、物体の情報を使い切っていない。LaViLa と Helping Hands は物体中心の設定で大きく劣化する\[10\]\[11\]
[要点]
- 手の手がかりと物体の手がかりを分けて評価する枠組み。両者が同じ受け取り側の中で重複・偏る問題を直接扱う（前提 B）。

### R3 Multimodal Distillation for Egocentric Action Recognition
[書誌]
- Gorjan Radevski, Dusan Grujicic, Marie-Francine Moens, Matthew Blaschko, Tinne Tuytelaars／2023／ICCV 2023（査読つき）／arXiv 2307.07483（ワークショップ版は arXiv 2210.04331）\[12\]\[13\]
- 読んだ範囲: 本文（表 3 の後半以降は検索結果の抜粋で確認）
[近さ]
- 方向 3、4、5／一人称（EK-100）と手の操作（Something-Something）／非医療
- 課題の形: RGB → 行動。教師は RGB、光学フロー、物体検出（「手」「物体」の枠を STLT で符号化）のアンサンブル\[14\]\[15\]
- モデルの状態: 教師は各モーダルを独立に学習（凍結して蒸留）。生徒は RGB の Swin-T。offline\[15\]
[手法の位置]
- 系統 S3（形 (b)）／現役度: 不明／一人称（EK）のみ
[証拠]
- 比較: RGB の基準、RGB＋OBJ を推論時に使う教師、RGB＋OBJ で蒸留して RGB だけで推論する生徒（表 2b・表 3）
- 効果量:
  - Something-Something の Action@1（表 2b）: 基準 60.3、教師 65.3、生徒 63.2\[15\]\[16\]
  - Something-Else の Action@1（表 3）: 基準 51.8、教師 59.4、生徒 57.5。RGB&OF&OBJ の生徒は 59.1（+7.3）\[15\]\[16\]
- 条件: 弱い教師（音声）が混ざると EK で名詞が下がる（表 2a: RGB&A の生徒は Action 38.3→37.9）\[15\]
- 基準の強さ: 中程度（Swin-T）／教師のモーダルだけを変えている／seed は不明。脚注によると、テスト集合が無いデータでは最終エポックのモデルで報告
- Omnivore との比較（表 4）: 本文によると、Something-Else で Omnivore は基準より約 5.5% 高いが、蒸留はさらに上回る\[15\]
[実装]
- コード・重み公開（GitHub）\[12\]\[13\]
[要点]
- 手と物体の検出を「学習時だけ」使う蒸留で、推論時に使う場合の利得の約 6 割（SSv2）〜7.5 割（Something-Else）を回収した。

### R4 Egocentric Action Recognition by Capturing Hand-Object Contact and Object State（HOCL/OSL）
[書誌]
- Tsukasa Shiota, Motohiro Takagi, Kaori Kumagai, Hitoshi Seshimo, Yushi Aono／2024／WACV 2024（査読つき）／ID 不明（CVF Open Access で本文を確認。DOI と arXiv ID は確認できず）
- 読んだ範囲: 本文（表 1〜4）
[近さ]
- 方向 3、7／一人称／非医療
- 課題の形: RGB → 行動。学習時だけ、100DOH＋一人称データで学習した Faster R-CNN の枠で隠した映像を、別のモデル（VRM2）に与えて相互学習する（HOCL）。物体状態の擬似分布も学習（OSL）
- データ規模: EGTEA は元の学習集合から無作為に選んだ 1,000 本（少数）。MECCANO は 8,839 区間・61 クラス。EK-100 は 55,191 区間
- モデルの状態: 検出器は凍結。VRM1 と VRM2 を同時に学習。offline
[手法の位置]
- 系統 S3（形 (b)）／G3Ego の表 2（MECCANO）に比較対象として載る／一人称、EGTEA は少数
[証拠]
- 比較: 同じモデルで、HOCL・OSL の有無だけを変える
- 効果量（表 1〜4）:
  - EGTEA の平均全体精度: SlowFast 64.02→66.48（HOCL）、66.86（両方）。Swin-B 64.09→64.77（HOCL）
  - MECCANO の Acc@1: SlowFast 38.08→42.05（HOCL）。Swin-B 44.03→42.01（HOCL、悪化）、44.81（両方）
  - EK-100 の action: SlowFast 32.14→33.63（HOCL）。Swin-B 34.39→32.72（HOCL、悪化）
  - EPIC で事前学習してから EGTEA（表 4）: SlowFast 68.86→69.31（HOCL）。Swin-B 68.92→67.95（HOCL、悪化）
- 符号: 受け取り側による（SlowFast で改善、Swin-B では差なし〜悪化）。著者は、HOCL は SlowFast に、OSL は Swin-B に効きやすいと述べる\[17\]
- 基準の強さ: Kinetics で事前学習した SlowFast・Swin-B／EGTEA は 3 分割の平均。seed と検定は不明
- 不審な点: 要旨は EGTEA で「最大 2.24%」とするが、表 1 では SlowFast の両方適用で 2.84%（66.86−64.02）。食い違いがある\[18\]
[実装]
- コード不明。OSL には物体の状態（形容詞）の人手の注釈が要る
[要点]
- 手・物体の領域を学習時にだけ使う信号は、弱い受け取り側では効くが、強い受け取り側や事前学習済みの受け取り側では消える、または逆転する。問い (8) の直接の証拠である。

### R5 G3Ego: Gaze-Guided Graphs for Egocentric Action Understanding
[書誌]
- Marko Haralović, Akash Ramakrishnan, Estefania Talavera Martinez／2026／プレプリント／arXiv 2608.20157
- 読んだ範囲: 本文（表 1〜5）
[近さ]
- 方向 3／一人称／非医療（組立・調理）
- 課題の形: 疎にサンプルしたフレーム → 行動の認識と予測。凍結した DINOv3、GroundingDINO、VLM の出力からグラフを作り、手の特徴（左右それぞれに手の枠・左右の指示子・接触物体の枠とクラス番号。計 20 次元）を加える
- 接触の決め方: 手と物体の枠が重なれば接触。検出が無ければ 0 で埋める\[19\]
- 推論の規約: 認識は区間単位（offline）。予測は 1 秒前までの観測から
- データ規模: MECCANO は 20 本・8,839 区間・61 クラス。EGTEA Gaze+ は 10,321 区間・106 クラス\[19\]
- モデルの状態: 上流はすべて凍結（特徴をキャッシュ）。グラフ埋め込みと時系列集約だけを学習
[手法の位置]
- 系統 S1、S8、S9（形 (a)）／新興／一人称、MECCANO は 20 本の少数、予測は過去のみ
[証拠]
- 比較: 同じ G3Ego（時系列集約、32 フレーム）で手の特徴の有無だけを変える（表 1）
- 効果量（MECCANO、表 1）:
  - 手の特徴の追加: Top-1 41.91→46.48、Top-5 79.63→82.04、Macro-F1 15.87→21.34
  - 物体特徴の追加（全グラフ）: Top-1 25.58→37.34
  - 視線による剪定: Top-1 37.34→37.90
  - フレーム数: 1 フレームで Top-1 31.85、10 フレームで 37.90\[19\]
- 基準の強さ: MECCANO の Top-1 では UCF Swin3D-B（52.82）に届かない（表 2）\[19\]
- seed・分割・検定: 既定の分割を 1 回。seed と検定は不明。正解の把持との差は報告なし
[実装]
- コードは公開予定と記載。視線と VLM のキャプションが要る
[要点]
- 凍結した検出器の「手の枠＋枠の重なりで決めた接触物体のクラス」を足すだけで、MECCANO の Macro-F1 が 5.5 点上がった。対象データの把持ラベルと最も形の近い (a) の例である。

### R6 AssemblyHands
- 書誌: Takehiko Ohkawa ほか／2023／AssemblyHands: Towards Egocentric Activity Understanding via 3D Hand Pose Estimation／CVPR 2023（査読つき）／arXiv 2304.12301／読んだ範囲: 要旨のみ（プロジェクトのページと検索結果の抜粋）\[20\]\[21\]
- 近さ: 方向 3、7／一人称／組立／系統 S4／現役度不明。別に学習した姿勢推定器（SVEgoNet）の 3 次元の手の姿勢 → 行動分類。300 万画像（うち一人称 49 万）\[22\]\[23\]
- 証拠: 注釈の品質が異なる姿勢で学習した分類器どうしを比較。効果量は不明（本文未読）。著者の主張では、姿勢の品質が高いほど行動認識が良くなる\[20\]\[22\]
- 要点: 上流（手の姿勢）の精度と下流の利得の関係を測った数少ない研究（問い (8)）。数値は本文で確認していない。

### R7 Assembly101 の姿勢ベースラインと On the Utility of 3D Hand Poses for Action Recognition
- 書誌: (i) Sener ほか／2022／Assembly101／CVPR 2022（査読つき）／arXiv 2203.14712。(ii) Md Salman Shamil, Dibyadip Chatterjee, Fadime Sener, Shugao Ma, Angela Yao／2024／On the Utility of 3D Hand Poses for Action Recognition（手法名 HandFormer、arXiv v2 は 2024-08-14。掲載先は未確認）／arXiv 2403.09805。要旨は「With RGB, we achieve new state-of-the-art performance on Assembly101 and H2O」「Hand pose is excellent for identifying motions (verbs) but struggles with associated objects」と述べる。読んだ範囲: いずれも本文の該当節・表（検索結果の抜粋）
- 近さ: 方向 3／一人称と多視点／組立／系統 S4。上流で推定済みの 3 次元の手の姿勢（＋疎な RGB）→ 行動（offline）
- 効果量 (i): 姿勢ベースの MS-G3D は action 28.7% で、映像ベース（TSM、一人称 4 視点の融合）より 5.1 点低い。verb は 6.7 点高く、object は 10.2 点低い\[24\]
- 効果量 (ii): 表 4 で TSM の一人称 4 視点の融合が action 33.80、e3＋姿勢が 36.07、e3＋e4＋姿勢が 38.05。表 6 で姿勢による verb は 1 フレームで 59.12、15 フレームで 63.70\[25\]
- 符号: 改善（動詞）、物体は不利／seed・検定は不明
- 要点: 手の表現は動詞に効き、名詞（物体）には効きにくい。1 フレームだけでも姿勢は一定の情報を持つ（前提 C）。

### R7b Egocentric Hand-object Interaction Detection and Application
- 書誌: Yao Lu, Walterio W. Mayol-Cuevas／2021／プレプリント／arXiv 2109.14734／読んだ範囲: 要旨のみ\[26\]
- 近さ: 方向 3、一人称。手の姿勢・手のマスク・手の中の物体のマスク → HOI の状態。その状態で台本の無い活動を分割する（30 FPS 以上）\[26\]\[27\]
- 証拠: EPIC-KITCHENS の選んだ画像で HOI の精度 89%（Shan ほかは 92%）。分割の F1 は GTEA で 68.2%、UTGrasp で 82.8%。相互作用の情報を使わない場合との差は要旨に無い\[27\]
- 要点: 接触状態を行動分割に使った初期の例。利得の大きさは不明。

### R8 A Real-Time System for Egocentric Hand-Object Interaction Detection in Industrial Domains
- 書誌: Antonio Finocchiaro, Alessandro Sebastiano Catinello, Michele Mazzamuto, Rosario Leonardi, Antonino Furnari, Giovanni Maria Farinella／2025／ICIAP 2025（arXiv の注記による）／arXiv 2507.13326／読んだ範囲: 要旨のみ\[28\]\[29\]
- 近さ: 方向 3／一人称／工業／online（ストリーミング、30fps）／ENIGMA-51。接触状態の認識モジュールが接触と判定したときだけ物体検出を起動し、active object を検出・分類する（カスケード）\[6\]\[28\]
- 証拠: 行動認識（Mamba＋EfficientNetV2）の p-AP 38.52%。微調整した YOLOWorld の手と物体の AP 85.13%。カスケードの有無による差は不明\[28\]
- 要点: 相互作用の推論を検出のゲートに使う online の例。ゲートで検出が良くなるかは測られていない（要旨の範囲では）。

### R9 ENIGMA-51
- 書誌: Ragusa ほか／2024／ENIGMA-51: Towards a Fine-Grained Understanding of Human-Object Interactions in Industrial Scenarios／WACV 2024（査読つき）／arXiv 2309.14809／読んだ範囲: 要旨と本文の一部（検索結果の抜粋）
- 近さ: 方向 3、一人称（HoloLens 2）、工業（電子基板の修理）、19 人・51 本\[30\]
- 注釈: キーフレームに手と active object の枠、手の左右、接触状態、手と物体の関係、物体カテゴリ。ほかに時間方向の相互作用（take/release/first-contact/de-contact）、手のキーポイント、マスク\[30\]\[31\]\[32\]
- 要点: 問い (7) の候補。少数の動画（51 本）で、接触と時間ラベルの両方を持つ。

### R10 Are Synthetic Data Useful for Egocentric Hand-Object Interaction Detection?（HOI-Synth）
- 書誌: Rosario Leonardi, Antonino Furnari, Francesco Ragusa, Giovanni Maria Farinella／2024／ECCV 2024（ecva.net に掲載）／arXiv 2312.02672／読んだ範囲: 本文の一部（検索結果の抜粋）。要旨によると、実ラベルを 10% だけ使って Overall AP が EPIC-KITCHENS VISOR で +5.67%、EgoHOS で +8.24%、ENIGMA-51 で +11.69% 改善した
- 証拠（ENIGMA-51）: 接触の F1 は実データのみ 77.28 → FSDA 77.83。領域内の合成データは汎用の合成データより Overall AP で約 10 点高い（本文の記述）。実ラベルを 10% だけ使う設定がある\[33\]\[34\]
- 要点: 少ない領域内の注釈と領域内の合成データの効果（前提 E、問い (10)）。下流タスクへの影響は測っていない。

### R12 EgoHOS
- 書誌: Lingzhi Zhang, Shenghao Zhou, Simon Stent, Jianbo Shi／2022／ECCV 2022／arXiv 2208.03826／読んだ範囲: 要旨のみ\[35\]
- 近さ: 11,243 画像、手と相互作用物体の画素ラベル、接触の境界。本文によると手の状態分類と映像の活動認識（SlowFast）を補助する。数値は不明\[35\]
- 要点: マスク系の上流の代表。活動認識への効果量は確認していない。

### R13 Exo2EgoDVC
- 書誌: Takehiko Ohkawa, Takuma Yagi, Taichi Nishimura, Ryosuke Furuta, Atsushi Hashimoto, Yoshitaka Ushiku, Yoichi Sato（東京大学、OMRON SINIC X、AIST、LY Corp.）／年・掲載先は未確認／arXiv 2311.16444／EgoYC2 データセットを提案し、YouCook2 から一人称映像への密なキャプション生成を、敵対的学習による視点不変学習で転移する／読んだ範囲: 本文の一部（検索結果の抜粋）
- 手法: EgoHOS の手と物体のマスク（一次・二次の相互作用物体）を精緻化し、領域ごとの特徴を連結してフレームの特徴にする（形 (a)）。効果量は不明
- 要点: 手と物体のマスクを手順の映像（密なキャプション生成）に入れる例。

### R14 Next-Active-Object Prediction from Egocentric Videos
- 書誌: Antonino Furnari, Sebastiano Battiato, Kristen Grauman, Giovanni Maria Farinella／2017／Journal of Visual Communication and Image Representation（査読つき）／doi 10.1016/j.jvcir.2017.10.004／読んだ範囲: 要旨のみ\[36\]\[37\]
- 近さ: 物体の軌跡 → 次に active になる物体（過去の窓のみ）。ADL、20 人・10 時間。効果量は不明（要旨では「いくつかの基準より良い」）\[37\]
- 要点: next active object の原点。手の情報は使わない。

### R15 Leveraging Next-Active Objects for Context-Aware Anticipation in Egocentric Videos
- 書誌: Sanket Thakur, Cigdem Beyan, Pietro Morerio, Vittorio Murino, Alessio Del Bue／2024（WACV 2024 と引用されている）／手法名 NAOGAT／arXiv 2308.08303／読んだ範囲: 関連研究の抜粋。要旨は「outperforms existing methods on two separate datasets, Ego4D and EpicKitchens-100 ("Unseen Set")」と述べる
- 要点: next active object の予測を行動予測に使う。問い\[38\] (2)(9) の候補。数値は未確認。

### R16 EgoSurgery-HTS
[書誌]
- Nathan Darjana, Ryo Fujii, Hideo Saito, Hiroki Kajita／2025／EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos\[39\]
- プレプリント（arXiv 2503.18755）。論文誌版は Healthcare Technology Letters 12(1) e70049（査読つき、doi 10.1049/htl2.70049）\[40\]\[41\]
- 読んだ範囲: arXiv 版の本文
[近さ]
- 方向 1／一人称／開放手術／単一の画像 → 術具・手・手と術具のインスタンスセグメンテーション
- 注釈の作り方:
  - 術具と手の枠を SAM に与えてマスクを生成し、人手で確認・修正\[42\]
  - 手のセグメンテーションに対する IoU が最大の術具を「相互作用する術具」とする\[42\]\[43\]\[44\]
  - 手のマスクは自分・他者 × 左・右の 4 種。手と術具のマスクは左手、右手、左手の物体、右手の物体、両手の物体の 5 種\[42\]\[45\]
- データ規模: 本文では 19,496 画像（術具 50,383、手 57,173、手と術具 41,605）。術具 14 種\[41\]\[42\]
[証拠]
- 表 2: 手と術具の mAP_box は Mask R-CNN 45.3、QueryInst 55.2。mAP_mask は Mask2Former 56.6\[42\]
- 表 3（QueryInst、同じテスト集合で学習データだけを変える）: 手は EgoHands で学習 8.3/6.3 → HTS で 54.0/50.7。手と術具は VISOR-HOS で 13.0/11.4 → HTS で 55.2/49.4\[42\]
- 下流（工程・検出）での利用: なし。「マルチタスク学習を可能にする」と述べるだけ\[46\]
- 不審な点:
  - フレーム数が三か所で食い違う。表 1 では 15.4K、本文では 19,496 画像、HTL 版の表では 18.4K\[46\]\[47\]
  - 術具のクラス数は HTS が 14、EgoSurgery-Tool が 15\[41\]\[48\]
  - 依頼文は「枠の重なり」とするが、本文の記述は「手のセグメンテーションに対する IoU」。公開コードか注釈で確認が要る
  - Fig. 3 によると、他者の手は自分の手より混同が多い\[42\]
[実装]
- データは GitHub（Fujiry0/EgoSurgery）と記載。ライセンス不明\[39\]
[要点]
- 一般の HOI データからの転移は大きく劣化する（mAP で約 40 点）。領域内の注釈が必須という強い証拠（前提 E）。下流で使った研究は無い。

### R17 EgoSurgery-Tool
- 書誌: Ryo Fujii, Hideo Saito, Hiroki Kajita／2024／プレプリント／arXiv 2406.03095／読んだ範囲: 要旨と本文の一部（検索結果の抜粋）\[48\]
- データ規模: 15 本、15,437 画像、術具 49,652（15 クラス）、手 46,320（4 種）。動画単位の分割\[49\]
- 本文の記述: 術具と工程の共起行列（Fig. 4）を示し、「術具の情報は工程認識に役立つかもしれない」と述べるが、検証はしていない\[49\]\[50\]
- 要点: 検出と工程の両方の注釈を持つ唯一の一人称開放手術データ。術具 → 工程の利得は未検証。

### R18 EgoSurgery-Phase（GGMAE）
- 書誌: Ryo Fujii, Masashi Hatano, Hideo Saito, Hiroki Kajita／2024／MICCAI 2024（査読つき）／arXiv 2405.19644（doi 10.1007/978-3-031-72089-5_18）／読んだ範囲: 要旨のみ\[51\]\[52\]
- データ規模: 15 時間、9 工程、視線つき。\[53\]R16 によると 21 本・10 術式・8 人の術者\[50\]\[53\]
- 証拠: 視線で MAE のマスクを導く GGMAE が、従来の SOTA より Jaccard で 6.4 点、MAE 系より 3.1 点高い（要旨）。\[53\]表番号つきの値は未読
- 要点: 同じデータで視線の手がかりはすでに使われている。把持の信号との重複を確認する必要がある（前提 F）。

### R19 Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera（サブエージェント経由）
[書誌]
- Shimizu, Hachiuma, Kajita, Takatsume, Saito／2021／J. Imaging 7(2):15（査読つき）／doi 10.3390/jimaging7020015（PMC8321273）\[54\]
- 読んだ範囲: 本調査の主担当は未読。サブエージェントが本文を読んだ報告による
[近さ]
- 方向 1（一人称の開放手術。EgoSurgery と同じグループ）
- 課題の形: Faster R-CNN で術具と手を検出し、術具の枠と IoU が最大の手を選ぶ。その手の切り出し画像の時系列（T フレーム）を ResNet-18＋LSTM で術具の分類に使う\[1\]\[55\]
- モデルの状態: 検出と分類の一連の処理。凍結した独立の把持モデルではない
[証拠]
- 表 1: 術具の位置特定 AP 0.925、手 0.713。表 2: 対象の手の選択精度 0.943（F1 0.971）\[54\]
- 「手の見た目だけ」の基準は精度 0.524、F1 0.326。全手法の値は表 3（数値は本調査で未確認）。表 4: 50 フレームの窓が最良\[1\]\[54\]
- 符号: 手の動きの追加で改善（著者の主張）
[要点]
- 「どの手がどの術具を持つかを枠の IoU で決め、その手の情報で術具の判別を助ける」という、本件に最も近い手術の先行研究。工程認識は扱っていない。

### R20 Visual Modalities Based Multimodal Fusion for Surgical Phase Recognition
- 書誌: Bogyu Park ほか／2022／MMMI 2022（MICCAI ワークショップ）／doi 10.1007/978-3-031-18814-5_2。拡張版は Comput. Biol. Med. 166 (2023) 107453（doi 10.1016/j.compbiomed.2023.107453）。2026 年に Corrigendum（doi 10.1016/j.compbiomed.2026.111850、内容未確認）／読んだ範囲: 要旨のみ\[3\]\[56\]\[57\]
- 近さ: 方向 2、腹腔鏡（遠位胃切除）。術具のマスクから動きと術具どうしの関係の指標（VKI）を作り、CNN 特徴と融合して工程を認識する（形 (a)）。効果量は不明\[3\]
- 要点: 「別のモデルの相互作用の出力 → 工程」という形の手術での前例。手は扱わない。訂正の内容を確かめてから引用すること。

### R21 EgoExOR（サブエージェント経由）
- 書誌: Özsoy, Mamur, Tristram, Pellegrini, Wysocki, Busam, Navab／2025／NeurIPS 2025 Datasets track／arXiv 2505.24287／本調査の主担当は未読\[58\]
- 近さ: 方向 2。装着型グラスの手の追跡の姿勢と視線を推論時の入力にして、手術室のシーングラフを生成する。効果量は不明\[59\]
- 要点: 手の信号を推論時に入れる手術室の例。下流は工程でも検出でもない。

### R22 YOLOv10-Based Multi-Task Framework for Hand Localization and Laterality Classification in Surgical Videos（サブエージェント経由）
- 書誌: Ke Sun, Le Zhang／2026／TrackRAD@MICCAI 2026（Semantic Scholar の表記）／arXiv 2602.18959／本調査の主担当は未読
- 証拠: 一人称の外傷手術で手の検出と左右の分類。mAP@[.5:.95] 0.33、左手 67%、右手 71%（サブエージェントの報告）\[58\]
- 要点: 手が出力であり、下流の補助ではない。

### R23 Using Computer Vision to Automate Hand Detection and Tracking of Surgeon Movements in Videos of Open Surgery
- 書誌: Michael Zhang ほか（Serena Yeung を含む）／2021／AMIA（査読つき）／arXiv 2012.06948／読んだ範囲: 要旨のみ
- 証拠: 既存の手のデータセットより、開放手術の手のデータで学習した方が大幅に良い（要旨）。数値は未読\[60\]
- 要点: 手袋をした術者の手への領域の差（前提 E）を示す。

### R24 Open surgery tool classification and hand utilization using a multi-camera system
- 書誌: Kristina Basiev, Adam Goldbraikh, Carla M. Pugh, Shlomi Laufer（Technion／スタンフォード大学）／2022（IJCARS とサブエージェントが報告）／arXiv 2111.06098／要旨レベル。48 人の模擬腸管修復を、トップビューと接写の 2 台のカメラで撮影し、YOLOv5 で術具と手を検出、LSTM を 30 fps・1 秒窓と 3 fps・40 秒窓の 2 種で使う。要旨の精度/F1 は Top-view 0.88/0.88、Close-up 0.81/0.83、両カメラ 0.9/0.9
- 要点: 多視点の映像で術具を分類し、どちらの手がどの術具を持つかを推定する。\[61\]下流の工程には使っていない。\[62\]

### R28 Learning Using Privileged Information for Zero-Shot Action Recognition
- 書誌: Zhiyi Gao ほか／2022（ACCV 2022）／arXiv 2206.08632／読んだ範囲: 要旨と関連研究の節
- 近さ: 方向 5。物体の意味を学習時だけの特権情報（PI）にする。関連研究の節は、骨格・光学フロー・深度を PI にした行動認識を挙げている\[63\]
- 要点: LUPI を行動認識に使う系統の入口。手・把持を PI にした研究ではない。

### R29 Delving into Egocentric Actions
- 書誌: Li ほか（Rehg のグループ）／2015／CVPR 2015／ID 不明（PMC4784702 で本文を公開）／読んだ範囲: 本文の一部（検索結果の抜粋）
- 証拠: 手の姿勢・頭部の動き・視線の「一人称の手がかり（E）」を動きと物体の特徴に加えても（O+M+E）、全データセットで僅かな改善にとどまった。「一人称の手がかりを直接符号化するのは効果的でない」と記載\[64\]
- 要点: 手の手がかりが、強い物体・動きの特徴の上ではほとんど足し算にならなかった、初期の否定的な結果（問い (8)）。

---

## 問い (7): 一人称の作業映像データセット一覧

| データセット | 相互作用の注釈の種類 | 時間ラベル／物体の枠 | 動画の本数 | 相互作用の情報を下流に使った研究と既発表の値 |
|---|---|---|---|---|
| EgoSurgery（Phase/Tool/HTS） | 手と術具のマスク（左・右・左手物・右手物・両手物）。手は自分・他者 × 左右（R16） | 工程 9 種（Phase）、術具の枠 15 クラス（Tool） | 全 21 本（Tool の注釈は 15 本） | **なし**（0 件） |
| MECCANO | 手の枠と左右（100DOH の出力を人手で修正）。接触の時刻\[65\] | 行動 61 クラスの時間区間。物体の枠 | 20 本 | G3Ego の表 1: 手の特徴で Top-1 41.91→46.48。HOCL の表 2: SlowFast で 38.08→42.05、Swin-B で 44.03→42.01 |
| EGTEA Gaze+ | 手のマスク（G3Ego の記述では手の位置の注釈）、視線 | 行動 106 クラス | 86 セッション、28 時間（R1 の記述） | HOCL の表 1（SlowFast で 64.02→66.86）。Helping Hands の表 1（ゼロショットで Top-1 44.9→46.6） |
| EPIC-KITCHENS-100 / VISOR | VISOR: 手と active object のマスク、関係 | 動詞・名詞の区間 | 100 時間 | HOCL の表 3（SlowFast の action で 32.14→33.63）。Helping Hands の表 7（VISOR の接触物体の位置特定 41.3→82.3） |
| ENIGMA-51 | 手と active object の枠、左右、接触、関係（R9） | 相互作用の時間区間、keystep | 51 本 | Finocchiaro ほか（R8）: p-AP 38.52%（相互作用の情報の有無の比較はなし） |
| Assembly101 / AssemblyHands | 3 次元の手の姿勢 | 細粒度・粗い行動の区間 | 本数は未確認 | arXiv 2403.09805 の表 4（action で 33.80→38.05）。Assembly101 の姿勢ベースライン（action 28.7%） |
| Ego4D（Hands & Objects）、HOI4D、H2O、ARCTIC、EgoPER、HoloAssist、Ego-Exo4D | 原典を確認せず | 不明 | 不明 | 不明（走査できなかった範囲） |

---

## 問い (11): EgoSurgery-HTS を使った研究の全件

- サブエージェントが Semantic Scholar で被引用を調べた（arXiv 2503.18755 と doi 10.1049/htl2.70049 の両方）。引用していたのは次の 3 件で、いずれも工程認識・術具検出の補助ではない。
  - EgoMed-Agent（arXiv 2607.17341）: スマートグラスを使った、言語で指示する医用画像のセグメンテーション\[66\]
  - AR-ERIS（arXiv 2607.08397）: 内視鏡の参照表現によるセグメンテーション\[66\]
  - Show, Don't Tell（arXiv 2603.12751）: ロボティクスの新物体検出\[66\]
- **HTS のデータを下流の工程・検出に使った研究: 0 件。**
- EgoSurgery-Tool（arXiv 2406.03095）を引用する約 10 件にも、手・手と術具の情報で工程や検出を改善した研究は無かった（R21、R22 を含む）。
- 手術一般で手・術具の関係を工程や検出の補助に使った研究: R19（術具の分類）、R20（腹腔鏡の工程。術具どうしの関係）。

---

## (3) 探したが見つからなかったもの

- **凍結して渡す形と同時学習（多タスク）の直接比較（問い (3)）**: 検索語 "hand-object interaction features temporal action segmentation egocentric procedural"、"multimodal distillation egocentric action recognition object detections teacher RGB student"。約 18 件を調べた。同じ情報を凍結の入力・同時学習・蒸留で比べた研究は無く、近いのは R3 の Omnivore 比較だけ
- **正解の把持と予測の把持の差（問い (1)、前提 A）**: 該当なし。in-sample と out-of-fold（stacked generalization）の比較、exposure bias を扱った HOI の研究も見つからない
- **検出の mAP をクラス別に分けて HOI で改善を示した研究（問い (2)）**: 検索語 "next active object anticipation egocentric hand-object Furnari"。本文の表で確認できたものは無い
- **フレームレートを下げたときの手の手がかりの利得（前提 C）**: 直接の研究は無い。近いのはフレーム数を変えた R5 の表 1 と R7 の表 6
- **注釈の範囲外のフレームの扱い（前提 G）**: R1（疑似ラベルのあるフレームでだけ損失をかけ、抜けは罰しない）だけ。信頼度の重みづけ・ゲートの比較は見つからない
- **他者の手を区別しないことの下流への影響（前提 D）**: 該当なし
- **SAM 由来の疑似マスクの品質と下流の利得（問い (10)）**: 該当なし
- **online で同じフレームを使う場合と前の時刻までの比較（問い (9)）**: 該当なし。未来のフレームを特権情報にした online 行動検出の蒸留（Zhao ほか）が arXiv 2401.15489 の関連研究の節に引かれているが、原典は ID 不明\[67\]

---

## (4) 未検証の組み合わせ

1. 凍結した HOI モデルの出力を、検出（mAP）と行動・工程（Jaccard）の両方に渡し、同じ実験で比べた研究。R1 は grounding だけ、R5 は行動だけを扱う。
2. 形 (a) と形 (b) を同じ受け取り側・同じデータで比べた研究。R3 は教師と生徒の比較であり、(a) 側の融合の構造が異なる。
3. 強い事前学習済みの受け取り側で、形 (a) の HOI 入力が利得を保つか。R4 は (b) で消えることを示し、R5 は凍結した DINOv3 上の (a) で利得を示した。条件が異なるため比べられない。
4. 「手の情報に固有の上乗せ分」を、物体検出だけを入れた対照と分けて測った研究。R5 は物体特徴の上に手の特徴を足しているので近いが、手の特徴にも接触物体の枠とクラスが含まれる。
5. 0.5 fps 以下、数十本、手術ドメインで、SAM 由来のマスクを使って HOI を補助にした研究。

---

## (5) 検索記録

- 検索日: 2026-10-31。検索手段: ウェブ検索（版不明）、arXiv（本文の取得）、CVF Open Access（WACV 2024 の本文）、PMC（ブラウザ確認で取得失敗）、Semantic Scholar の API（サブエージェントによる被引用の調査）
- 方向 1（EgoSurgery）: "EgoSurgery-HTS hand tool segmentation egocentric open surgery"、"EgoSurgery-Phase gaze-guided masked autoencoder phase recognition"、"EgoSurgery hand-tool open surgery 2025 2026 phase recognition hands"＋サブエージェントの被引用調査。記録 4 件（R16〜R19）
- 方向 2（手術一般）: "Visual Modalities Based Multimodal Fusion for Surgical Phase Recognition Park 2022"、"open surgery hand tracking surgical phase recognition hand pose surgeon video"。記録 5 件（R20〜R24）
- 方向 3（一人称の非手術）: Helping Hands、2607.08514、2109.14734、2507.13326、AssemblyHands、next active object、EgoHOS、ENIGMA-51、HOCL など計 9 本。記録 16 件（R1〜R15、R29）
- 方向 4（一般映像）: "object-centric representation egocentric action recognition hands objects ablation no improvement strong backbone"。記録 1 件（R3 の Something-Something 部分）
- 方向 5（機構の一般論）: "learning using privileged information action recognition hand pose training only"、多モーダル蒸留。記録 2 件（R3、R28）
- 方向 6（方法論）: 専用の検索はしていない。不審な点の指摘は R1、R4、R16。記録 0 件
- 方向 7（否定的な結果）: 方向 3・4 の検索の中で抽出。記録 3 件（R4、R29、R7 の object 側の劣化）
- 走査できなかった範囲: PMC の HTL 版の本文、有料の論文誌の本文（Comput. Biol. Med.、JVCI）、OpenReview の非公開・取り下げの投稿、学位論文、Ego4D・HOI4D・H2O・ARCTIC・EgoPER・HoloAssist・Ego-Exo4D の原典、EgoSurgery-Phase の被引用の一覧（API のエラー）、Google Scholar の被引用の一覧

---

## (6) 解釈と提案（ここだけが解釈であり、事実の節と混ぜない）

**問い (1)〜(11) の要約（解釈）**
- (1)(4) の主な証拠は、形 (a)（R5）と形 (b)（R1、R3、R4）の両方で、1〜7 点の利得である。(b) は (a) の利得の 6〜7.5 割を回収する（R3）。
- (2) は検出の mAP での証拠が乏しく、grounding（R1）とゲート（R8）だけである。
- (3) は空白である。
- (8) は、受け取り側が強いと (b) の利得が消えること（R4）と、上流の品質への依存（R1 の表 2、R6）が要点である。

**依頼で考慮されていない可能性がある前提**
1. HTS の把持ラベルが枠（またはマスク）の IoU で決まるなら、把持モデルの出力は「検出結果＋手の枠からの決定的な規則」で近似できる。把持モデルを別に学習する意味は、手の枠の情報（術具の検出には無い）と、左右・両手の区別にほぼ限られる。対照として「検出の出力＋手の枠＋IoU 規則」を必ず置くべきである（R5 の 20 次元特徴がまさにこの形）。
2. HTS の 19,496 画像と、Tool の 15 本・15,437 画像の対応（どの動画・どのフレームか）が、5 分割の動画単位の分割と食い違うと、把持モデルの学習データに test の動画が入る（情報の漏れ）。HTS は「部分集合」と書くだけで、分割の対応は本文に無い。
3. 把持の注釈は術具の枠がある範囲にしか無い。そのため工程の全フレームで把持モデルを使うと、学習範囲外のフレームで出力が分布外になる（前提 G）。
4. R4 の結果からは、受け取り側（工程モデル）が強いほど (b) の利得は消えやすい、と推測される。

**期待情報量が大きい候補（提案）**
- 第 1 候補: **(a)、下流は工程認識。渡すのは「持たれている術具のクラス（左・右・両手ごとの多ラベル）＋手の存在」の低次元ベクトル。** 過去のフレームだけの移動平均として渡し、小さな界面にする。
  - 根拠: R5（手の枠と接触物体のクラスの 20 次元で、Macro-F1 +5.5）、R17（術具と工程の強い共起）、R19（どの手がどの術具かが判別に効く）
  - 0.5 fps では時間の手がかりが乏しいため、フレームごとの「持たれている術具」の集合（使用中の術具）が最も工程に結びつく、と推測する
  - 対照として必ず置くもの: (i) 検出の出力だけ（全術具のクラス）、(ii) 検出＋手の枠＋IoU 規則、(iii) 正解の把持（上限）
- 第 2 候補: **(b)、下流は検出。把持マスク由来の「active な術具」の補助の分類ヘッド。** active と写っているだけの術具を分けて、損失を足す。
  - 根拠: R1（疑似の HOI ラベルで接触物体の位置特定が教師を超えた）、R3（推論時のコストなしで利得の 6〜7 割）
  - 評価は mAP 全体に加え、稀少クラスと「把持される頻度が高いクラス」（持針器・鑷子。R16 の Fig. 2）で層別にすること
- 第 3 候補（優先度低）: (b) で工程モデルに補助損失。
  - 根拠: R4 で強い受け取り側では効果が消えたため、期待情報量は小さい。ただし、負の結果自体に報告の価値はある
- 方法論:
  - 学習時に入れる把持の出力は、5 分割の外側で、把持モデルの交差適合（out-of-fold）予測を使う。正解の把持と in-sample の予測は、上限と比較用の腕として別に置く（前提 A）
  - seed は 3 以上とし、動画単位の 5 分割で対応のある検定（分割 × seed）を行う
  - 把持モデルの精度（HTS の mAP）を段階的に落とした腕を用意し、上流の精度と下流の利得の曲線を描く。これは R1 の表 2、R6 の手術版になる

## 出典

1. [Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8321273/)
2. [Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera](https://www.mdpi.com/2313-433X/7/2/15)
3. [Visual modalities-based multimodal fusion for surgical phase recognition - PubMed](https://pubmed.ncbi.nlm.nih.gov/37774560)
4. [Visual modalities-based multimodal fusion for surgical phase recognition - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0010482523009186)
5. <https://arxiv.org/pdf/2308.07918>
6. [\[2507.13326\] A Real-Time System for Egocentric Hand-Object Interaction Detection in Industrial Domains](https://arxiv.org/abs/2507.13326)
7. [Helping Hands: An Object-Aware Ego-Centric Video Recognition Model](https://mlanthology.org/iccv/2023/zhang2023iccv-helping/)
8. [GitHub - Chuhanxx/helping\_hand\_for\_egocentric\_videos: Implementation of paper 'Helping Hands: An Object-Aware Ego-Centric Video Recognition Model'](https://github.com/Chuhanxx/helping_hand_for_egocentric_videos)
9. [\[2607.08514\] Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?](https://arxiv.org/abs/2607.08514)
10. [Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?](https://arxiv.org/html/2607.08514v1)
11. [Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?](https://arxiv.org/pdf/2607.08514)
12. [Multimodal Distillation for Egocentric Action Recognition](https://arxiv.org/pdf/2307.07483)
13. [GitHub - gorjanradevski/multimodal-distillation: Codebase for "Multimodal Distillation for Egocentric Action Recognition" (ICCV 2023) · GitHub](https://github.com/gorjanradevski/multimodal-distillation)
14. [(PDF) Multimodal Distillation for Egocentric Action Recognition](https://www.researchgate.net/publication/372404460_Multimodal_Distillation_for_Egocentric_Action_Recognition)
15. [Multimodal Distillation for Egocentric Action Recognition](https://arxiv.org/html/2307.07483v2)
16. [Multimodal Distillation for Egocentric Action Recognition Gorjan Radevski\*](https://scispace.com/pdf/multimodal-distillation-for-egocentric-action-recognition-2gh1oo7e.pdf)
17. <https://openaccess.thecvf.com/content/WACV2024/papers/Shiota_Egocentric_Action_Recognition_by_Capturing_Hand-Object_Contact_and_Object_State_WACV_2024_paper.pdf>
18. [Egocentric Action Recognition by Capturing Hand-Object Contact and Object State](https://mlanthology.org/wacv/2024/shiota2024wacv-egocentric/)
19. [G3Ego: Gaze-Guided Graphs for Egocentric Action Understanding](https://arxiv.org/pdf/2608.20157)
20. [AssemblyHands: Towards Egocentric Activity Understanding via 3D Hand Pose Estimation](https://assemblyhands.github.io/)
21. [\[PDF\] AssemblyHands: Towards Egocentric Activity Understanding via 3D Hand Pose Estimation](https://www.semanticscholar.org/paper/a79318bce848ab2d51c460d0833c176a5c261eef)
22. [AssemblyHands: Towards Egocentric Activity Understanding via 3D Hand Pose Estimation](https://arxiv.org/pdf/2304.12301)
23. [AssemblyHands: Towards Egocentric Activity Understanding via 3D Hand Pose Estimation \[Quick Review\]](https://liner.com/review/assemblyhands-towards-egocentric-activity-understanding-via-3d-hand-pose-estimation)
24. [Assembly101: A Large-Scale Multi-View Video Dataset for Understanding Procedural Activities](https://arxiv.org/pdf/2203.14712)
25. [On the Utility of 3D Hand Poses for Action Recognition](https://arxiv.org/pdf/2403.09805)
26. [\[2109.14734\] Egocentric Hand-object Interaction Detection and Application](https://arxiv.org/abs/2109.14734)
27. [Egocentric Hand-object Interaction Detection and Application — Computer Vision](https://awesomepapers.io/computer-vision/papers/2109.14734)
28. [A Real-Time System for Egocentric Hand-Object Interaction Detection in Industrial Domains](https://arxiv.org/pdf/2507.13326)
29. [Computer Vision and Pattern Recognition Jul 2025](https://arxiv.org/list/cs.CV/2025-07?skip=1225&show=25)
30. [ENIGMA-51: Towards a Fine-Grained Understanding of Human-Object Interactions in Industrial Scenarios](https://arxiv.org/html/2309.14809)
31. [ENIGMA-51: Towards a Fine-Grained Understanding of Human Behavior in Industrial Scenarios](https://www.researchgate.net/publication/379717636_ENIGMA-51_Towards_a_Fine-Grained_Understanding_of_Human_Behavior_in_Industrial_Scenarios)
32. [Egocentric Human-Object Interaction in Industrial Scenarios: a Case Study](https://ceur-ws.org/Vol-4121/Ital-IA_2025_paper_116.pdf)
33. [\[PDF\] Egocentric Hand-object Interaction Detection and Application](https://www.semanticscholar.org/paper/Egocentric-Hand-object-Interaction-Detection-and-Lu-Mayol-Cuevas/99c814723d423a262226e7692705166e2005cf47)
34. [Are Synthetic Data Useful for Egocentric Hand-Object Interaction Detection?](https://arxiv.org/html/2312.02672v3)
35. [Fine-Grained Egocentric Hand-Object Segmentation: Dataset, Model, and Applications](https://arxiv.org/pdf/2208.03826)
36. [\[PDF\] Next-active-object prediction from egocentric videos](https://www.semanticscholar.org/paper/Next-active-object-prediction-from-egocentric-Furnari-Battiato/b67282a73c79438095799de916bf44ae55f1d310)
37. [Next Active Object Prediction from Egocentric Video](https://iplab.dmi.unict.it/legacy/NextActiveObjectPrediction/)
38. [Leveraging Next-Active Objects for Context-Aware Anticipation in Egocentric Videos](https://arxiv.org/pdf/2308.08303)
39. [\[2503.18755\] EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos](https://arxiv.org/abs/2503.18755)
40. [EgoSurgery‐HTS: A Dataset for Egocentric Hand–Tool Segmentation in Open Surgery Videos](https://digital-library.theiet.org/doi/full/10.1049/htl2.70049)
41. [EgoSurgery‐HTS: A Dataset for Egocentric Hand–Tool Segmentation in Open Surgery Videos - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12686825/)
42. <https://arxiv.org/pdf/2503.18755>
43. [EgoSurgery‐HTS: A Dataset for Egocentric Hand–Tool Segmentation in Open Surgery Videos - Darjana - 2025 - Healthcare Technology Letters - Wiley Online Library](https://ietresearch.onlinelibrary.wiley.com/doi/10.1049/htl2.70049)
44. [(PDF) EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos](https://www.researchgate.net/publication/390143100_EgoSurgery-HTS_A_Dataset_for_Egocentric_Hand-Tool_Segmentation_in_Open_Surgery_Videos)
45. [(PDF) EgoSurgery‐HTS: A Dataset for Egocentric Hand–Tool Segmentation in Open Surgery Videos](https://www.researchgate.net/publication/398494359_EgoSurgery-HTS_A_Dataset_for_Egocentric_Hand-Tool_Segmentation_in_Open_Surgery_Videos)
46. [EgoSurgery‐HTS: A Dataset for Egocentric Hand–Tool Segmentation in Open Surgery Videos](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12686825/)
47. [EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos](https://arxiv.org/html/2503.18755v1)
48. [\[2406.03095\] EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos](https://arxiv.org/abs/2406.03095)
49. [EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos](https://arxiv.org/pdf/2406.03095)
50. [EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos](https://arxiv.org/html/2406.03095)
51. [\[2405.19644\] EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos](https://arxiv.org/abs/2405.19644)
52. [EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos](https://www.researchgate.net/publication/384582598_EgoSurgery-Phase_A_Dataset_of_Surgical_Phase_Recognition_from_Egocentric_Open_Surgery_Videos)
53. [EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos](https://arxiv.org/pdf/2405.19644)
54. [Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera](https://doi.org/10.3390/jimaging7020015)
55. [Hand Motion-Aware Surgical Tool Localization and Classification from an Egocentric Camera](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8321273/)
56. [Visual Modalities Based Multimodal Fusion for Surgical Phase Recognition](https://dl.acm.org/doi/abs/10.1007/978-3-031-18814-5_2)
57. [Corrigendum to "Visual modalities-based multimodal fusion for surgical phase recognition" \[Comput. Biol. Med. 166 (2023) 107453\] - PubMed](https://pubmed.ncbi.nlm.nih.gov/42431793/)
58. <https://api.semanticscholar.org/graph/v1/paper/arXiv:2406.03095/citations?fields=title,authors,year,venue,externalIds,abstract&limit=100>
59. [EgoExOR: An Ego-Exo-Centric Operating Room Dataset ...](https://arxiv.org/pdf/2505.24287)
60. [Using Computer Vision to Automate Hand Detection and Tracking of Surgeon Movements in Videos of Open Surgery](https://arxiv.org/pdf/2012.06948)
61. [Open surgery tool classification and hand utilization using a multi-camera system](https://link.springer.com/article/10.1007/s11548-022-02691-3)
62. [Open surgery tool classification and hand utilization using a multi-camera system](https://arxiv.org/pdf/2111.06098)
63. [Learning Using Privileged Information for Zero-Shot Action Recognition](https://arxiv.org/pdf/2206.08632)
64. [Delving into Egocentric Actions - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC4784702/)
65. [MECCANO: A Multimodal Egocentric Dataset for Humans Behavior Understanding in the Industrial-like Domain](https://arxiv.org/pdf/2209.08691)
66. <https://api.semanticscholar.org/graph/v1/paper/arXiv:2503.18755/citations?fields=title,authors,year,venue,externalIds,abstract&limit=100>
67. [Distilling Privileged Multimodal Information for Expression Recognition using Optimal Transport](https://arxiv.org/pdf/2401.15489)

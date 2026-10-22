EgoSurgery（21 本・0.5 fps・9 工程）では、性能を大きく左右しているのは時間モデルの種類よりも、フレーム表現（backbone）、評価のばらつき、online 用の学習と後処理だ、という証拠のほうが厚かった。状態空間モデル（Mamba 系）や多尺度 Transformer が、少数動画や EgoSurgery で効くことを示した報告は見つからなかった。

最初にお断りです。検索の上限（18 回）に届いたため、方向 3〜5 と 7 は、依頼された深さまで読み切れていません。Assembly101・Ego4D・HoloAssist・EgoProceL・SKiT・TMRNet の原典の ID も確認できていません。下書きの段階では 50,000 字の制限に合わせて記録を短く圧縮しており、そのため記録 16〜21 は欄をまとめた形になっています。

## TL;DR
- **時間モデルの差より backbone の差のほうが大きい。** TUNeS（Table I、Cholec80、25 run）では、特徴抽出器を学習するときの時間文脈を L=1 から L=64 に延ばすと、どの時間モデルでも Jaccard が約 0.04〜0.09 上がった。一方、L=64 の特徴の上では TeCNO*・Trans-SVNet*・GRU・OperA が 0.745〜0.759 に収まり、抽出器単体（0.758）とほぼ同じだった。EgoSurgery でも、探索ヘッドを固定して backbone だけを替えると F1 が 7.33〜50.72 まで動いた（SurgMotion Table 3）。
- **EgoSurgery-Phase で規約を読めた公開報告値は 2 系統だけ。** 原論文（GGMAE、Table 1・2）と SurgMotion（Table 3）である。原論文では TeCNO（ResNet-50）の macro Jaccard が 27.3、GGMAE が 33.9。SurgMotion は Jaccard 42.95 だが、分割と規約は読めた範囲では不明だった。しかも事前学習に EgoSurgery 自体が含まれ、表には重複した値がある。このため両者は比較できない。
- **状態空間モデルは内視鏡データでの「新興」段階にとどまる。** SR-Mamba・SPRMamba・HID-SSM・SurgicalMamba はすべて Cholec80 などの内視鏡データでの報告で、大半がプレプリントだった。SR-Mamba は双方向で、厳密には online ではない。一人称の非手術では、次の 4 つが効いていた：学習と推論をともに因果的に揃えること、進捗予測、タスクグラフ、信頼度と長さによる後処理（ProTAS Table 1・2、OnlineTAS Table 1）。一方、offline モデルを教師にする蒸留（OODL）は効かなかった。

## (1) 系統表

件数は、(2) の記録ブロックのうち、その系統を主に扱うものの数（重複あり）。

| 系統 | 代表的な文献 | 現役度（どのベンチマークでの話か） | 件数 |
|---|---|---|---|
| 再帰型（LSTM/GRU） | EndoNet（所有）、PhaseLSTM、SV-RCNet、TMRNet、GRU、BN-free CNN-LSTM | 定番の基準（AutoLaparo：MoSFormer Table 1。Cholec80：TUNeS Table I）。PhaseLSTM は EgoSurgery で置き換え済み（EgoSurgery-Phase Table 1、Jaccard 21.9） | 2 |
| 時間畳み込み（因果 TCN） | TeCNO（所有）、MS-TCN（所有）、NETE、causal TCN | 定番の基準（BernBypass70・AutoLaparo：MoSFormer Table 1。EgoSurgery：EgoSurgery-Phase Table 1。GTEA・EgoProceL・EgoPER：ProTAS Table 1） | 4 |
| Transformer による集約 | Trans-SVNet（所有）、OperA、ASFormer（所有）、SAHC | 定番の基準（Cholec80：TUNeS Table I・MoSFormer Table 1。一人称：ProTAS Table 2） | 3 |
| 長時間文脈／end-to-end 映像 Transformer | LoViT（所有）、SKiT、Surgformer、MoSFormer、TeSTra | Cholec80・AutoLaparo・BernBypass70 の online で SOTA 級（MoSFormer Table 1、プレプリント）。EgoSurgery での報告なし | 2 |
| 状態空間モデル（Mamba/SSM） | SR-Mamba、SPRMamba、HID-SSM、SurgicalMamba、EndoMamba | 新興（Cholec80・AutoLaparo・ESD385。著者以外の追試なし）。EndoMamba は EgoSurgery の探索評価で下位（SurgMotion Table 3、F1 13.90） | 4 |
| 記憶機構 | TMRNet、LSTR（所有）、OnlineTAS、MoSFormer | TMRNet は定番の基準。OnlineTAS・MoSFormer は新興。LSTR は TAS では弱い基準（OnlineTAS Table 8・9） | 3 |
| 多尺度・階層 | MS-ASCT、MuST、TUNeS、Surgformer の HTA、SAHC | MS-ASCT・MuST は新興。TUNeS は Cholec80 の online で上位（TUNeS Table I、著者自身の表） | 3 |
| 言語を使うもの | SurgVLP、HTT-Net、ReSW-VL、ORQA | 新興。SurgVLP は EgoSurgery の凍結探索で中位（SurgMotion Table 3、F1 23.26） | 0 |
| 基盤モデル（backbone 側） | SelfSupSurg・SurgMAE・GGMAE・SurgPETL（所有）、EndoViT、EndoFM、GSViT、SurgeNetXL、DINOv3、VideoMAE、SurgMotion | EgoSurgery では SurgMotion が SOTA 級（SurgMotion Table 3。プレプリントで、事前学習に EgoSurgery を含む）。SelfSupSurg・SurgeNetXL は同表で下位。SurgMAE は EgoSurgery で VideoMAE V2 を下回った（EgoSurgery-Phase Table 2）。SurgPETL は不明 | 2 |
| 拡散モデル | DiffAct、Meta-SurDiff | DiffAct は GTEA・50Salads・Breakfast の offline で SOTA 級（OnlineTAS Table 8・9）。online 化は新興 | 0 |
| 進捗予測・タスクグラフ・後処理 | ProTAS、OnlineTAS の後処理、VidParse | 新興（一人称の手順動画） | 2 |
| online 行動検出の流用 | LSTR、TeSTra、MAT | TAS では弱い（OnlineTAS Table 8・9）。手術では TeSTra が比較対象に残る（MoSFormer Table 1） | 1 |
| 視点の扱い（一人称特有） | Ego-Exo4D の VI Encoder・視点蒸留、Dexterous Focus | 新興（Ego-Exo4D keystep） | 2 |
| 一人称の表現・データ（所有） | EgoVLP、Ego-Exo、EGTEA Gaze+、EPIC-KITCHENS | EgoVLPv2 は Ego-Exo4D keystep の定番の基準（Ego-Exo4D Table 6）。EGTEA・EPIC-KITCHENS はデータセットなので対象外（不明） | 0 |
| 評価方法論 | Metrics Matter、BN の落とし穴、指標の系統的分析 | 定番の参照先（MoSFormer が非緩和評価の根拠として引用） | 3 |

## (2) 文献ごとの記録

### 記録 1：EgoSurgery-Phase（GGMAE と同じ論文。問い (4) の照合のため例外として記録）
[書誌]
- Fujii, Hatano, Saito, Kajita／2024／EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos／MICCAI 2024（査読つき）
- arXiv:2405.19644、DOI 10.1007/978-3-031-72089-5_18
- 読んだ範囲：本文

[近さ]
- 方向 1／一人称（術者の頭部に付けた Tobii カメラ）／開放手術
- 課題の形：RGB 映像（＋視線）から、フレームごとに 9 工程のどれかを予測
- 推論の規約：不明。GGMAE は 10 フレームのクリップを分類するが、因果的かどうかの記載がない。比較手法が online 版かどうかも書かれていない
- データ規模：
  - 21 本（10 術式、術者 8 人）
  - 25 fps・計 28 時間を 0.5 fps に間引き、個人を特定できるフレームを除外。除外後は平均 46 分・計 15 時間
  - 注釈 27,694 フレーム
  - 分割は学習 14・検証 2・テスト 5。交差検証なし
- モデルの状態：GGMAE は事前学習 800 epoch のあと全体を fine-tune。比較手法は不明

[手法の位置]
- 系統：基盤モデル（MAE 系）
- 現役度：EgoSurgery で唯一の原典ベースライン群
- 条件：少数動画・一人称で測定。online かどうかは不明

[証拠]
- Table 1（手法の比較。macro の Precision／Recall／Jaccard）：

| 手法（backbone） | Precision | Recall | Jaccard |
|---|---|---|---|
| PhaseLSTM（AlexNet） | 36.3 | 33.1 | 21.9 |
| PhaseNet（AlexNet） | 37.0 | 25.7 | 19.7 |
| TeCNO（ResNet-50） | 47.7 | 39.2 | 27.3 |
| Trans-SVNet（ResNet-50） | 41.8 | 35.9 | 23.1 |
| NETE（Inception v3） | 43.7 | 35.2 | 27.5 |
| GGMAE（ViT-S） | 51.7 | 45.6 | 33.9 |

- 同じ ResNet-50 の上では、TeCNO（27.3）が Trans-SVNet（23.1）を 4.2 上回った（seed 1 回、分散の報告なし）
- Table 2（同じ ViT-S で事前学習法だけを変えた比較。P／R／J）：スクラッチ 47.9/31.6/27.1、VideoMAE 49.3/41.6/29.8、VideoMAE V2 54.2/43.2/30.8、SurgMAE 52.2/41.9/27.8、GGMAE 51.7/45.6/33.9
- Table 3a（マスク比 0.90 で、マスクの選び方だけを変えた比較。Jaccard）：random 30.6、tube 29.8、視線誘導 33.9（random より +3.3）
- Table 3b（マスク比）：0.95→31.2、0.90→33.9、0.85→31.6、0.80→31.5
- Table 3c（温度 τ）：1.00→30.1、0.75→30.6、0.50→33.9、0.25→27.2。τ の選び方だけで 6.7 動く
- 交絡：backbone が手法ごとに違うので、Table 1 は時間モデルだけを変えた比較になっていない
- seed・標準偏差・検定の記載なし。ハイパーパラメータの探索にどのデータを使ったかも不明

[実装]
- データは GitHub（Fujiry0/EgoSurgery）で公開予定と記載。重みとライセンスは不明
- 視線ヒートマップが必要。クラス不均衡にはリサンプリングで対処

[要点]
- 依頼者の記述（21 本・0.5 fps・9 工程）は原論文と一致した。ただし 15 時間はフレーム除外後の長さで、時系列に欠落がある。テストは 5 本しかない

### 記録 2：SurgMotion
[書誌]
- Wu, Holm, Chen ほか（責任著者 Lei）／2026／SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos／プレプリント
- arXiv:2602.05638（v2）
- 読んだ範囲：本文（Table 7 まで）

[近さ]
- 方向 1・2／一人称・内視鏡・顕微鏡／開放手術・低侵襲手術
- 課題の形：64 フレームのクリップを、凍結 backbone＋attentive probing ヘッドで分類
- 推論の規約：不明
- データ規模：EgoSurgery を Table 1 で「21 本・10.55 時間・Breast surgery」と記載。原論文の「15 時間・10 術式」と食い違う
- モデルの状態：backbone は凍結し、ヘッドだけを学習。16 本のヘッドのうち最良の値を報告

[手法の位置]
- 系統：基盤モデル（V-JEPA 系）
- 現役度：EgoSurgery で SOTA 級（Table 3）。プレプリント

[証拠]
- Table 3（EgoSurgery。同じヘッドで backbone だけを変えた比較。Acc／F1／Jaccard）：

| backbone | Acc | F1 | Jaccard |
|---|---|---|---|
| SurgMotion | 75.57 | 50.72 | 42.95 |
| DINOv3-L | 75.37 | 32.43 | 26.03 |
| DINOv3-H | 70.08 | 36.34 | 29.03 |
| VideoMAE-L | 64.52 | 26.84 | 19.82 |
| EndoFM | 54.85 | 36.13 | 26.42 |
| SurgVLP | 57.44 | 23.26 | 17.46 |
| EndoMamba | 53.30 | 13.90 | 10.32 |
| SelfSupSurg | 36.03 | 7.38 | 5.22 |
| SurgeNetXL | 35.82 | 7.34 | 5.18 |
| GSViT | 35.74 | 7.33 | 5.17 |

- 本文の「F1 +14.6%」は EndoFM との差、「+18.3%」は DINOv3-L との差。実際には DINOv3-H（36.34）のほうが EndoFM より高い
- 不審な点：
  1. EndoFM の EgoSurgery の F1 36.13・Jaccard 26.42 が、Table 2 の EndoFM の Cholec80 の値と完全に一致する
  2. Table 2 の EndoFM の AutoLaparo は F1 35.77 に対して Jaccard 47.84。Jaccard は F1 を超えないので不整合
  3. Table 5 と Table 6 の Endo Mamba の行が一致する
  4. AVOS で多くのモデルが 48.34/8.15 の同じ値になっている
- 情報の漏れ：事前学習データ（Table 1）に EgoSurgery の 21 本が含まれる。評価用の動画を除いたかどうかは記載なし
- 分割・seed・検定は不明

[実装]
- コードは GitHub（CAIR-HKISI/SurgMotion）、重みは Hugging Face で公開

[要点]
- EgoSurgery では backbone の差が支配的だという強い傍証になる。ただし事前学習と評価の重なりと表の重複値があるので、絶対値は信用できない

### 記録 3：SurgicalMamba
[書誌]
- Oh, Sun／2026／SurgicalMamba: Dual-Path SSD with State Regramming for Online Surgical Phase Recognition／プレプリント
- arXiv:2605.14889（v3）
- 読んだ範囲：要旨と序論のみ

[近さ]
- 方向 2／内視鏡
- 推論の規約：online・過去のみ（著者の主張）
- データ規模：7 ベンチマーク
- モデルの状態：ConvNeXt を一部凍結

[手法の位置]
- 系統：状態空間モデル（Mamba2 の SSD。二経路、遷移強度に応じた時間刻み、Cayley 回転）
- 現役度：新興

[証拠]
- 要旨（これまでの最強手法との差）：
  - Cholec80：Acc 94.6・Jaccard 82.7（+0.7・+2.2 pp）
  - AutoLaparo：Acc 89.5・Jaccard 68.9（+1.7・+2.0 pp）
- 不審な点：要旨は「strict online evaluation」と言うが、GitHub の README には「10-second relaxed-boundary protocol」に従うとある。速度も版によって違う（238.74 fps と 312.88 fps）

[実装]
- コード公開（sukjuoh/Surgical-Mamba）

[要点]
- online SSM の最新例。ただし緩和評価を使っている疑いがあり、表は未確認

### 記録 4：SR-Mamba
[書誌]
- Cao, Wang, Liu／2024／SR-Mamba: Effective Surgical Phase Recognition with State Space Model／プレプリント
- arXiv:2407.08333
- 読んだ範囲：要旨と抜粋のみ

[近さ]
- 方向 2／内視鏡・顕微鏡（CATARACTS）
- ResNet34 の特徴を使い、補助タスクとして anticipation も解く
- 推論の規約：双方向 Mamba

[手法の位置]
- 系統：状態空間モデル。現役度：新興

[証拠]
- 手法の比較（抜粋）：Cholec80 で AC 92.6±8.6、JA 81.5±8.6
- anticipation 損失の有無だけを変えると、AC・JA ともに約 +0.5 pp
- 不審な点：AC と JA の標準偏差がどちらも 8.6 で一致

[実装]
- コード公開（rcao-hk/SR-Mamba）

[要点]
- 双方向なので、依頼者の online 条件には合わない

### 記録 5：SPRMamba
[書誌]
- Zhang ほか／2024／SPRMamba: Surgical Phase Recognition for Endoscopic Submucosal Dissection with Mamba／プレプリント
- arXiv:2409.12108
- 読んだ範囲：要旨と抜粋のみ

[近さ]
- 方向 2／内視鏡（ESD）
- 推論の規約：online（著者の主張）

[手法の位置]
- 系統：SSM と注意機構の混成（Scaled Residual TranMamba）。現役度：新興

[証拠]
- ESD385 で平均正解率が 72.31% から 87.64% に上がった（何と比べたかは抜粋からは不明）
- 不審な点：「Mamba を使った最初の工程認識」と主張しているが、SR-Mamba のほうが先に出ている

[実装]
- コード公開（Zxnyyyyy/SPRMamba）

[要点]
- 少数動画での証拠はない

### 記録 6：HID-SSM（Holistic Surgical Phase Recognition with Hierarchical Input Dependent State Space Models）
[書誌]
- Wu, Wang, Lechner, Hasani ほか（Rus）／2025／プレプリント
- arXiv:2506.21330
- 読んだ範囲：要旨と方法の抜粋のみ

[近さ]
- 方向 2／ロボット手術
- 二段階。時空間の事前学習を 1 epoch だけ行い、時間的に一貫した特徴抽出器を作る

[手法の位置]
- 系統：階層型の状態空間モデル。現役度：新興

[証拠]
- 数値：未読

[要点]
- 種の「HID-SSM」は実在した。抽出器の学習に時間文脈を入れる点が TUNeS と共通する

### 記録 7：MS-ASCT（Friends Across Time）
[書誌]
- Zhang, Meng, Cheng, Biskup, Petculescu, Chapman／2024／Friends Across Time: Multi-Scale Action Segmentation Transformer for Surgical Phase Recognition／プレプリント
- arXiv:2401.11644
- 読んだ範囲：要旨のみ

[近さ]
- 方向 2・4
- MS-ASCT は online（因果）、MS-AST は offline

[手法の位置]
- 系統：多尺度。現役度：新興

[証拠]
- 数値：未読

[要点]
- 種の「MS-ASCT」は実在した

### 記録 8：Surgformer
[書誌]
- Yang, Luo, Wang, Chen／2024／Surgformer: Surgical Transformer with Hierarchical Temporal Attention for Surgical Phase Recognition／MICCAI 2024（査読つき）
- arXiv:2408.03867、DOI 10.1007/978-3-031-72089-5_57
- 読んだ範囲：要旨と抜粋のみ

[近さ]
- 方向 2
- 入力は疎なフレーム列（T=16、R=4）。推論は online のスライディング窓
- 分割：Cholec80 は 40/40、AutoLaparo は 10/4/7

[手法の位置]
- 系統：end-to-end 映像 Transformer
- 現役度：SOTA 級（MoSFormer Table 1 で 2 位）

[証拠]
- 数値の出所：MoSFormer によれば、原論文の値は別の計算法で出したもの。MoSFormer が自分の計算法で出し直した値は次のとおり
  - Cholec80：Acc 92.3／Jaccard 77.8
  - AutoLaparo：Acc 86.1／Jaccard 62.4

[実装]
- コード公開（isyangshu/Surgformer）

[要点]
- 原論文の値は評価の規約が違う

### 記録 9：MoSFormer
[書誌]
- Ding, Lian, Unberath／2025／MoSFormer: Augmenting Temporal Context with Memory of Surgery for Surgical Phase Recognition／プレプリント
- arXiv:2503.00695
- 読んだ範囲：本文

[近さ]
- 方向 2
- 推論の規約：online
- データ：BernBypass70・Cholec80・AutoLaparo（いずれも 1 fps）。end-to-end で学習

[手法の位置]
- 系統：記憶機構＋長時間文脈の Transformer
- 現役度：Table 1 で上位

[証拠]
- Table 1（online・非緩和。Acc／Jaccard）：

| 手法 | AutoLaparo | Cholec80 |
|---|---|---|
| TMRNet | 78.2/49.6 | – |
| TeCNO | 77.3/50.7 | – |
| TeSTra | – | 90.1/71.6 |
| Trans-SVNet | 78.3/50.7 | 89.1/72.5 |
| LoViT | 81.4/55.9 | 91.5/74.2 |
| SKiT | 82.9/59.9 | 92.5/76.7 |
| Surgformer | 86.1/62.4 | 92.3/77.8 |
| MoSFormer | 88.0/66.2 | 93.2/78.7 |

- BernBypass70（Acc／F1）：TeCNO 83.8/59.2、MTMS-TCN 85.3/62.4、Surgformer 85.9/62.5、MoSFormer 88.0/66.3
- 少数動画の AutoLaparo では、TeCNO と Surgformer の差が Jaccard 11.7 ある。Cholec80 での Trans-SVNet と Surgformer の差（5.3）より大きい
- Table 2（記憶だけを足した比較、BernBypass70 の Acc）：85.9 → 88.0（+2.1）。正解の履歴を与えると 89.2
- seed・検定の記載なし

[要点]
- 少数動画でも長時間文脈＋記憶は TCN を大きく上回った。ただし 1 fps の内視鏡で、ViT を end-to-end で学習した場合の話

### 記録 10：TUNeS（サブエージェントによる全文読解を含む）
[書誌]
- Funke, Rivoir, Krell, Speidel／2023（arXiv）・2025／TUNeS: A Temporal U-Net with Self-Attention for Video-based Surgical Phase Recognition／IEEE TBME（査読つき）
- arXiv:2307.09997、PubMed 40031317
- 読んだ範囲：本文

[近さ]
- 方向 2・6
- 推論の規約：online と offline の両方
- 二段階学習。抽出器を L=1・8・64 フレームの時間文脈で学習して凍結し、その上で時間モデルを学習

[手法の位置]
- 系統：時間畳み込み U-Net＋self-attention
- 現役度：Cholec80 で上位（著者自身の表）

[証拠]
- 実験計画：抽出器 5 seed × 時間モデル 5 回の計 25 run。指標は video-wise の Acc／Macro Jaccard
- Table I（Cholec80・online・32:8:40 分割。Acc／Jaccard）：

| モデル | L=1 | L=8 | L=64 |
|---|---|---|---|
| 抽出器単体 | 0.816/0.591 | 0.865/0.693 | 0.901/0.758 |
| TeCNO* | 0.877/0.705 | 0.883/0.721 | 0.898/0.750 |
| Trans-SVNet* | 0.879/0.705 | 0.889/0.723 | 0.898/0.749 |
| GRU | 0.875/0.701 | 0.879/0.704 | 0.901/0.759 |
| OperA | 0.863/0.659 | 0.880/0.680 | 0.898/0.745 |
| SAHC | 0.882/0.718 | 0.892/0.736 | 0.913/0.779 |
| TeCNO（特徴の拡張＋平滑化損失） | 0.891/0.730 | 0.900/0.750 | 0.906/0.768 |
| TUNeS | 0.901/0.746 | 0.915/0.768 | 0.922/0.783 |

- 標準偏差は ±0.005〜0.018。* は特徴の拡張と平滑化損失を使わない版
- L=64 では、TeCNO*・Trans-SVNet*・GRU・OperA が抽出器単体とほぼ同じか、それを下回った
- L=1 から L=64 にすると Jaccard が +0.037〜+0.086 上がった。これは同じ L の中での時間モデル間の幅と同程度以上
- 特徴の拡張と平滑化損失だけで +0.018〜+0.025
- 抽出器の隠れ状態を持ち越す（CHE）と、L=8 では改善（0.693→0.713）、L=64 では悪化（0.758→0.723）
- Table II（offline・L=64、Jaccard）：TeCNO 0.807、ASFormer 0.824、TUNeS 0.823
  - 不審な点：本文は「TUT は L=64 で良い」と書くが、表では L=8 が最良
- offline→online の落差（L=64、Jaccard）：TeCNO −0.039、TUNeS −0.040
- edit score（offline）は 0.556〜0.758 と大きく動く
- 40:40 分割では TeCNO の値が論文ごとに違う：Czempiel 2022 は Acc 0.874、Chen 2022 は 0.900
- AutoLaparo は Fig. 17 の図だけで、本文に出てくる数値は Acc 0.851・f-Jaccard 0.609 のみ

[要点]
- 依頼者の今の構成は、Table I の「L=1 の TeCNO」に当たる

### 記録 11：Metrics Matter in Surgical Phase Recognition（サブエージェントによる全文読解）
[書誌]
- Funke, Rivoir, Speidel／2023／技術報告（プレプリント）
- arXiv:2305.13961
- 読んだ範囲：本文

[近さ]
- 方向 6・7
- SV-RCNet の再実装、32:8:40 分割、5 seed

[証拠]
評価の規約だけを変えたときの差：

| 何を変えたか | 表 | 値 |
|---|---|---|
| 欠落した工程の扱い | Table 3 | Jaccard .681 → .692 |
| F1 の計算法 | Table 4 | .785〜.821 |
| frame-wise か video-wise か | Table 6 | .670 と .692 |
| 境界の緩和 | Table 5・7・8 | .690 → .726（+.036） |
| seed | Table 9 | 差 .017 |
| 分割（40:40 に変える） | Table 10 | Jaccard .692 → .707 |

- 同じ手法が論文ごとに違う値で報告されている：
  - SV-RCNet の R-Acc は .853 から .913 まで（Table 11）
  - TeCNO の Jaccard は .696 と .723（Table 12）
- 緩和指標は 1 を超えうる（Fig. 4）。MATLAB の評価スクリプトにバグがある

[要点]
- 評価規約の違いによる差は、手法間の差と同じ桁になる

### 記録 12：On the Pitfalls of Batch Normalization for End-to-End Video Learning
[書誌]
- Rivoir, Funke, Speidel／2024／Medical Image Analysis 94:103126（査読つき）
- arXiv:2203.07976
- 読んだ範囲：要旨のみ

[証拠]
- 著者の主張：BN を使わない backbone で end-to-end に学習すると、単純な CNN-LSTM でも 3 ベンチマークで SOTA を超える。online タスクでは BN によって未来の情報が漏れる「cheating」が起きる

[要点]
- 依頼者の ResNet-50（BN を含む）を fine-tune するときに直接関係する

### 記録 13：OnlineTAS
[書誌]
- Zhong, Ding, Yao／2024／OnlineTAS: An Online Baseline for Temporal Action Segmentation／NeurIPS 2024（査読つき）
- arXiv:2411.01122、DOI 10.52202/079017-1881
- 読んだ範囲：本文

[近さ]
- 方向 3・4
- データ：GTEA（一人称、28 本）、50Salads、Breakfast
- 特徴（I3D）は凍結。推論は online と semi-online

[証拠]
- Table 1（online。Acc／Edit／F1@50）：

| データ | 因果 TCN | 本手法 | 本手法＋後処理 |
|---|---|---|---|
| GTEA | 74.4/66.6/57.2 | 76.2/63.5/58.8 | 74.4/70.3/67.7 |
| Breakfast | 55.3/18.7/8.3 | 56.7/19.3/9.3 | 52.9/55.7/30.5 |

- 後処理を足すと Acc が 1.8〜3.8 下がる
- Table 2（50Salads、成分を足していく比較）：Acc 75.2 → GRU のみ 78.1 → 全成分 82.4
- Table 5（記憶長）：256 では 128 より Acc が下がる（82.4→80.7）
- Table 8・9（offline との差）：Breakfast の F1@50 は offline の MS-TCN が 47.5、因果 TCN が 8.3。LSTR は 50Salads で Edit 5.0
- 不審な点：Table 8 の「Ours online」の行が、Table 1 の「TCN・semi-online」の行と同じ値になっている
- seed の記載なし

[要点]
- online では過分割（細切れの予測）が主な失敗で、記憶より後処理の効果のほうが大きい

### 記録 14：ProTAS（Progress-Aware Online Action Segmentation for Egocentric Procedural Task Videos）
[書誌]
- Shen, Elhamifar／2024／CVPR 2024（査読つき）、pp. 18186–18197
- DOI 10.1109/CVPR52733.2024.01722。arXiv ID は不明
- 読んだ範囲：本文

[近さ]
- 方向 3／一人称
- データ：GTEA、EgoProceL、EgoPER
- I3D は凍結。推論は online

[証拠]
- Table 1（MS-TCN を基にした比較。F1@50）：

| データ | offline | offline 学習→online 推論 | 因果で学習（CAS） | ＋OODL | ＋APP | ＋APP＋TG |
|---|---|---|---|---|---|---|
| EgoProceL | 45.9 | 8.8 | 33.0 | 30.5 | 35.2 | 35.7 |
| EgoPER | 77.3 | 11.9 | 39.4 | 40.0 | 43.4 | 46.3 |

- GTEA（Acc／Edit／F1@50）：offline 76.3/79.0/69.8、offline 学習→online 推論 47.0/58.8/38.7、CAS 74.0/64.4/56.0、＋OODL で F1@50 は 54.1（悪化）、＋TG で Acc 74.3（APP 時の 76.0 から低下）
- Table 2（ASFormer を基にした比較）：
  - offline 学習→online 推論の Acc：EgoProceL 13.2、EgoPER 19.8
  - GTEA：CAS 77.2/73.3/65.0 → ＋TG 77.0/74.1/66.1
- Table 3：EgoProceL では学習可能なタスクグラフで F1@50 が 35.7→34.8 と下がった
- Table 4（offline の EgoProceL）：効果が小さい（F1@50 45.9→46.1）
- seed の記載なし

[実装]
- コード公開（Yuhan-Shen/ProTAS）

[要点]
- 因果的に学習することが最大の効果を持つ。進捗予測とタスクグラフは、主に Edit と F1 を数ポイント上げる

### 記録 15：Ego-Exo4D（keystep recognition）
[書誌]
- Grauman ほか／2024／Ego-Exo4D: Understanding Skilled Human Activity from First- and Third-Person Perspectives／CVPR 2024（査読つき）
- arXiv:2311.18259
- 読んだ範囲：抜粋のみ

[証拠]
- Table 6（ego 視点のみで推論したときの Top-1）：VI Encoder 41.53%、視点蒸留 39.49%、EgoVLPv2 38.76%
- 不審な点：クラス数を決める閾値の数え方について、フォーラムに疑問が出ている

[要点]
- 視点に不変な表現が上位に来る

### 記録 16：Improving Keystep Recognition in Ego-Video via Dexterous Focus
[書誌]
- Zachary Chavis, Stephen J. Guy, Hyun Soo Park（University of Minnesota）／2025
- arXiv:2506.00827（EgoVis workshop paper）
- 読んだ範囲：数値はエンリッチャー経由

[近さ・証拠]
- 方向 3・7。一人称の映像を、手を中心に安定化した映像に変換して入力する
- Table 2（Ego-Exo4D keystep、Top-1）：TimeSformer* ego のみ 39.18%、手のみ 45.81%、ego＋手 47.75%、VI Encoder 40.34%
- 不審な点：ここに転記された VI Encoder の値（40.34%）が、記録 15 の 41.53% と合わない

[要点]
- 頭部の動きへの対策が、時間モデルではなく入力側で効いた

### 記録 17：Systematic analysis of evaluation metrics for deep learning-based surgical phase recognition in laparoscopic cholecystectomy
[書誌]
- Özkurt G, Bajraktari F, Pott PP（University of Stuttgart）／2026／Frontiers in Artificial Intelligence 9:1873219（査読つき）
- PMID 42488379、PMC13388889
- 読んだ範囲：要旨と抜粋のみ

[近さ・証拠]
- 方向 6。2016〜2025 年の Cholec80 論文を PRISMA に沿ってレビュー（研究 50 本）
- 緩和境界での結果は、標準偏差が大きい傾向がある
- 本文：「Since around 2023, an increasing use of segment-based metrics can be observed」

[要点]
- 緩和評価は今も混在している

### 記録 18：SurgPLAN++
[書誌]
- Zhen Chen, Xingjian Luo, Jinlin Wu ほか（Lei, Ren, Ourselin, Liu）／2024
- arXiv:2409.12467、IEEE ICRA 2025 に採択
- 読んだ範囲：抜粋のみ

[近さ・証拠]
- 方向 2・7。online 推論では、映像の反転・フレームの複製・間引きで「擬似的に完全な動画」を作る
- Cataracts で offline 84.3／Jaccard 68.4、online 76.7／66.8（Acc −7.6、Jaccard −1.6）
- コード：lxj22/SurgPLAN-Plus

[要点]
- offline から online への落差は、Jaccard より Acc のほうが大きかった

### 記録 19：EgoSurgery-Tool
[書誌]
- Fujii ら／2024／EgoSurgery-Tool: A Dataset of Surgical Tool and Hand Detection from Egocentric Open Surgery Videos／プレプリント
- arXiv:2406.03095
- 読んだ範囲：要旨と抜粋のみ

[証拠]
- 器具・手の検出データ。工程認識に効くかどうかを測った数値はない

[要点]
- 付随情報を工程認識に使った報告はまだない

### 記録 20：EgoSurgery-HTS
[書誌]
- Fujii ら／2025／EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos／Healthcare Technology Letters（査読つき）
- arXiv:2503.18755
- 読んだ範囲：要旨と抜粋のみ

[証拠]
- 工程認識への効果を測った数値はない
- 他の論文が書く「15,437 timepoints」は、工程注釈の 27,694 フレームとは別の量と考えられ、混同しやすい

### 記録 21：SURGE Phase 1
[書誌]
- 著者不明／SURGE Phase 1: An AR/VR-Based Deep Learning Framework for Surgical Scene Analysis／Springer 会議録
- DOI 10.1007/978-3-032-31119-1_38
- 読んだ範囲：要旨のみ

[証拠]
- EgoSurgery で工程認識の precision 0.88 と報告。原論文の 51.7 とかけ離れており、規約が不明なので比較できない

## (3) 探したが見つからなかったもの
- **種の実在確認**
  - 実在と ID を確認できたもの：SR-Mamba、SPRMamba、HID-SSM、MS-ASCT、Surgformer、SurgMotion、Ego-Exo4D
  - SKiT（ICCV 2023）と TMRNet（IEEE TMI 2021）：他の論文の引用から実在は確認したが、ID は未確認で、本文も未読
  - Assembly101・Ego4D・HoloAssist・EgoProceL：原典の ID は未確認（検索の予算切れ）。検索語：「Assembly101 CVPR 2022 arXiv」「HoloAssist ICCV 2023 arXiv」「EgoProceL ECCV 2022」
- **EgoSurgery-Phase を評価に使った論文**：原論文と SurgMotion のほかには、規約がはっきりした報告はなかった（約 27 件を確認）。視線を時間モデルに入れた後続研究も見つからなかった
- **見つからなかったもの**（約 9 件ずつ確認したが、該当する報告なし）
  - 系統ごとの少数動画での学習曲線
  - 0.5 fps のアブレーション
  - focal loss・class-balanced loss が効かなかったという表
  - 二段階学習での特徴の過適合を定量化した研究
  - 21 本規模での分散の推定
  - 一人称特有の要因が時間モデルの選択に与える影響（手術）

## (4) 未検証の組み合わせ
- EgoSurgery で、同じ ResNet-50 のまま時間モデルだけを変える比較
- EgoSurgery × 時間文脈つきの抽出器（L=8〜64）
- EgoSurgery × ProTAS 型の進捗予測とタスクグラフ
- EgoSurgery × online の後処理 × Edit/F1@k での評価
- 0.5 fps × 長時間文脈・多尺度・SSM
- 学習 10〜15 本 × SSM
- 凍結した映像基盤モデル × 因果的な時間ヘッド
- 視線・手・器具の情報を時間モデルに入力する
- EgoSurgery × 複数 seed・交差検証

## (5) 検索記録
検索日はいずれも 2026-10-08。web_search は 18 回（うち 1 回は予算切れで失敗）。

| 方向 | 検索回数 | 関連した件数 | 記録したもの |
|---|---|---|---|
| 1（EgoSurgery） | 4 回 | 約 15 件 | 5 件（記録 1・2・19・20・21） |
| 2（手術一般） | 8 回 | 約 40 件 | 9 件（記録 3〜10・18） |
| 3（一人称の非手術） | 2 回 | 約 12 件 | 3 件（記録 14・15・16） |
| 4（一般映像） | 2 回（うち 1 回失敗） | 約 8 件 | 1 件（記録 13） |
| 5（機構の一般論） | 0 回 | – | 0 件（関連する話題は記録 14・15 の中で扱った） |
| 6（方法論） | 3 回 | 約 20 件 | 3 件（記録 11・12・17） |
| 7（否定的な結果） | 1 回 | – | 他の記録から抽出。網羅できていない |

## (6) 解釈と提案（ここだけが解釈）

### 問い (1)〜(8) への答え
- **(1) 系統**：上の表の 14 系統。2024〜2026 年の新しい流れは三つある。
  - 長時間文脈と記憶を持つ end-to-end Transformer
  - 状態空間モデル（SSM）
  - 凍結した映像基盤モデルを探索ヘッドで使う方式

  一般映像・一人称の online 行動分割では、進捗予測・タスクグラフ・後処理が主流になっている。
- **(2) 少数動画**：少数動画で系統の順位が入れ替わるという証拠はなかった。ただし EgoSurgery では Trans-SVNet が TeCNO を下回った（EgoSurgery-Phase Table 1）。
- **(3) 時間モデルか backbone か**：backbone（とその時間文脈）のほうが性能を決めている（TUNeS Table I、SurgMotion Table 3）。
- **(4) EgoSurgery の報告値**：3 系統ある。ただし互いに比較できる形ではない。
- **(5) 一人称の非手術で効くもの**：効果の大きい順に、因果的な学習、タスクグラフと進捗予測（後処理と同程度）。蒸留（OODL）は効かなかった。
- **(6) 損失の工夫**：平滑化損失と特徴の拡張は効いた。OODL と後処理は Acc を下げた。
- **(7) offline→online の落差**：
  - 因果的に学習し直した場合、Acc は −2〜−11、Edit と F1 は −11〜−38
  - offline で学習したモデルをそのまま online で使うと、Acc が約 50 落ちる
  - Cholec80 の TCN では Jaccard −0.04
- **(8) 報告値のゆれ**：境界の緩和で +.036、分割で +.015、seed で .017。同じ TeCNO が論文によって .696 と .723 で報告されている。

### 見落とされている可能性がある前提
- **テストが 5 本しかない。** テスト 40 本の Cholec80 でも、seed だけで Jaccard が .017 揺れる。5 本では、時間モデル間の差は分散の中に埋もれる可能性が高い。
- **時系列が途中で欠けている。** 個人を特定できるフレームを除いたため、0.5 fps の系列は連続していない。
- **10 術式・8 人の術者が混ざっている。** 工程の順序はおおむね決まっているので、タスクグラフは強い事前知識として使える。
- **0.5 fps では動画が短い。** 平均 46 分の動画は約 1,380 フレームで、因果 TCN の受容野（約 2,000）でほぼ全体を覆える。このため、長時間文脈モデルや SSM が持つ「長い系列を扱える」という利点は出にくい。
- **BN の統計の漏れと、SurgMotion を使った場合の評価の汚染**にも注意が要る。

### 次に試す価値がある系統（優先順）
1. **評価の作り直し**：動画単位の k-fold（または術者単位で分ける）× 3 seed とし、緩和なしの Jaccard・F1・Edit を出す。根拠：記録 1・10・11。
2. **抽出器に時間文脈を入れる**：CNN-LSTM（L=8〜64）を end-to-end で学習してから凍結し、因果 TCN に載せる。BN を使わない構成も試す。根拠：記録 10・12。
3. **凍結した基盤モデルの特徴＋因果 TCN**：DINOv3-L や VideoMAE。根拠：記録 2。
4. **online 用の構成要素**：因果的な学習、進捗予測、タスクグラフ、信頼度と最小長による後処理。根拠：記録 13・14。
5. **学習の工夫**：特徴の拡張、平滑化損失、リサンプリング。根拠：記録 1・10。
6. **視線・手・器具の情報**：視線で空間プーリングする、手の周りを切り出す。根拠：記録 1・16・19・20。
7. **因果 SSM や記憶つき Transformer は後回し**：少数動画・0.5 fps・一人称での証拠がまだない。根拠：記録 3・9。
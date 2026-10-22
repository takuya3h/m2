# EgoSurgery（一人称開放手術・0.5 fps・21本）の online 工程認識における自己教師あり事前学習と手術基盤モデル：文献調査（検索日 2026-10-08）

数十本規模の対象データだけで行う自己教師あり事前学習（SSL）について、「ImageNet・Kinetics・DINO 系の強い一般重みから fine-tune する場合より良い」と示した研究は、EgoSurgery でも他の手術データでも見つからなかった。唯一の直接証拠である GGMAE（arXiv 2405.19644）の比較相手は「ViT-S のスクラッチ学習」と「同じデータでマスク方式だけを変えた MAE」であり、その差は Jaccard 2〜7 点、seed 数・分割数の記載はない。

## TL;DR
- 問い (1)(2)：EgoSurgery の上で SSL を行った唯一の研究が GGMAE である。視線でマスクを誘導すると Jaccard 33.9 で、ランダムマスク（30.6）より +3.3、スクラッチ学習（27.1）より +6.8 高い（Table 2・Table 3a）。ただし温度 τ=0.25 にすると 27.2 まで落ち、スクラッチ並みになる。設定にきわめて敏感で、単一の分割（14/2/5）・seed 数不明という条件で得られた値である。
- 問い (3)(4)：EgoSurgery で一般モデルと手術基盤モデルを並べた表は SurgMotion（arXiv 2602.05638、プレプリント）の Table 3 しかない。凍結した backbone に attentive probe を載せた条件で、F1 は SurgMotion 50.72、DINOv3-H 36.34、DINOv3-L 32.43 だった。他の手術基盤モデルの多く（EndoViT・SurgeNetXL・GSViT・SelfSupSurg）は F1 7〜9 にとどまり、DINOv3 に大きく負けている。ただしこの表には、①事前学習データに EgoSurgery の全 21 本が入っている、②EndoFM の値が Cholec80 の値と一致する、③16 個の probe ヘッドから最良値を報告している、という問題がある。
- 結論：まず DINOv3 系の凍結特徴か fine-tune に因果的時間ヘッドを載せた構成を強い基準として確立し、その上に「対象データでの継続 SSL」と「視線の使い方（マスク・crop・注意の教師信号）」を独立した腕として足して比べる設計を勧める。21 本・5 分割という規模では Jaccard 3 点前後の差を見分けにくいため、seed を複数回し、動画単位のブートストラップで信頼区間を出すことが前提になる。

## (1) 系統表

| 系統 | 代表文献 | 現役度（どこでの話か） | 記録件数 |
|---|---|---|---|
| S1 対象データ上の video MAE（マスク方式の改変） | GGMAE, SurgMAE, VideoMAE | 新興（EgoSurgery；著者以外の追試なし） | 3 |
| S2 事前知識でマスクを選ぶ／損失に重みをつける（視線・動き） | GGMAE, SurgMotion, MME | 新興（EgoSurgery, 一般映像） | 3 |
| S3 手術映像の大規模 SSL 基盤モデル（映像） | SurgMotion, SurgVISTA, Endo-FM, EndoMamba, GSViT | SOTA 級を主張（Cholec80 ほか；査読つきの比較表は少ない） | 6 |
| S4 手術画像の SSL 基盤モデル | SelfSupSurg, EndoViT, SurgeNetXL, LemonFM, EndoSSL, GastroNet | 定番の基準（Cholec80, AutoLaparo） | 6 |
| S5 映像と言語のモデル（手術） | SurgVLP, PeskaVLP, OphCLIP | 定番の基準（zero-shot） | 2 |
| S6 一般基盤モデル（DINOv3, V-JEPA 2, VideoMAE V2, UMT） | DINOv3, VideoMAE V2 | 定番の基準（手術の比較表で強い基準として使われる） | 3 |
| S7 領域適応としての継続事前学習 | Roth 2024, SelfSupSurg（初期化の実験）, 鳥類音響 MAE | 不明 | 4 |
| S8 視線を注意の教師／入力として使う（一人称） | Li 2018, Min 2021, Gaze-guided surgical attention | 定番（EGTEA） | 5 |
| S9 一人称の非手術映像での事前学習 | EgoVLP, InternVideo-Ego4D | 定番（Ego4D, EPIC） | 2 |
| S10 クリップモデルを online で使う | Surgformer, SemiVT-Surge, SurgicalMamba | SOTA 級（Cholec80） | 3 |
| S11 評価・統計・漏れ | Metrics Matter, MoSFormer, SurgVISTA の分割規約 | 定番 | 4 |

## (2) 文献ごとの記録（主要文献）

### R1 EgoSurgery-Phase / GGMAE
- 書誌: Fujii, Hatano, Saito, Kajita／2024／EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos／MICCAI 2024（査読つき、pp.187–196）／arXiv 2405.19644（v3、題名の一致を確認）、DOI 10.1007/978-3-031-72089-5_18
- 読んだ範囲: 本文全体（v3 PDF）。補足資料は読んでいない。
- 近さ: 方向 1／一人称／開放手術／クリップ（10 フレーム、224²）と視線ヒートマップから工程 9 種を予測／推論の規約: 不明（クリップの中で予測する位置の記載がない）／本文の記述は「20 本、10 術式、術者 8 人、15 時間、27,694 フレーム、分割 14/2/5」。
- 手法の位置: S1・S2／新興（EgoSurgery の Table 1・2 で最上位。著者以外の追試は見つからなかった）／少数動画・一人称の条件にあたる。online かどうかは不明。
- 証拠: Table 2 の行の性質について。全行が ViT-S で、本文は "Employing the same backbone and training schema" と書いている。Table 3a のアブレーションで Tube 0.90 の Jaccard が 29.8 となり、Table 2 の VideoMAE 行の 29.8 と一致する。このことから、Table 2 の各行は「EgoSurgery の上でマスク方式だけを変えて事前学習した比較」と読むのが最も整合する。ただし、各行の事前学習データを明記した文はない。Supervised 行は「ViT-S を EgoSurgery でスクラッチ学習」と表注に明記されている。他のデータで事前学習した重みでの初期化は、どの行にも書かれていない。効果量（Jaccard）は次のとおり。GGMAE 33.9 に対し、VideoMAE（tube）29.8、VideoMAE V2（dual）30.8、SurgMAE 27.8、スクラッチ 27.1。Table 3a では random 0.75 が 28.9、random 0.90 が 30.6、gaze 0.90 が 33.9。Table 3b（マスク率）は 0.95→31.2、0.85→31.6、0.80→31.5。Table 3c（τ）は 1.0→30.1、0.75→30.6、0.25→27.2。符号は改善だが、条件によっては差が消える（τ=0.25）。Precision では VideoMAE V2（54.2）が GGMAE（51.7）を上回る。基準は弱い（ImageNet や Kinetics で初期化した基準がない）。比較はマスク方式だけを変えたもの。seed 数、分割数、検定はいずれも記載なし（単一分割）。ハイパーパラメータは "coarse-to-fine grid search" で決めたとあるが、どのデータで選んだかの記載はない。
- 実装: データは公開（GitHub Fujiry0/EgoSurgery）。GGMAE のコードと重みは不明。追加で要るのは視線（Tobii）。事前学習に使った動画の範囲（学習用分割だけか）は不明。
- 不審点: 本文は「20 videos」と書くが、分割は 14+2+5=21 本になる。本文の「スクラッチより 6% 改善」は表の値から計算すると 6.8 になる。
- 要点: 視線マスクの利点は、弱い基準に対して単一分割で示されたものにとどまる。

### R2 SurgMotion（v1 の題名は UniSurg）
- 書誌: Wu, Holm, …, Navab, Lei／2026／SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos／プレプリント（v5、2026-09-22。査読つきの掲載先は見つからなかった）／arXiv 2602.05638（題名の一致を確認）
- 読んだ範囲: 本文全体（v5 HTML）。補足資料は見つからなかった。リポジトリの README はサブエージェント経由で読んだ。
- 近さ: 方向 1・2／混在（一人称を含む）／手術全般／クリップ→工程。README によれば、64 フレーム（1 fps）の窓の最後のフレームを予測する online 規約で、凍結した backbone に attentive probe を載せる。
- 手法の位置: S2・S3／新興（自身の Table 2〜9 で最上位。著者以外の採用は未確認）。
- 証拠（Table 3、EgoSurgery、Acc/F1/Jaccard）: SurgMotion 75.57/50.72/42.95、DINOv3-L 75.37/32.43/26.03、DINOv3-H 70.08/36.34/29.03、VideoMAE-L 64.52/26.84/19.82、VideoMAE-G 62.25/20.40/16.13、EndoFM 54.85/36.13/26.42、SurgVLP 57.44/23.26/17.46、GastroNet 48.12/16.08/12.87、EndoMamba 53.30/13.90/10.32、EndoSSL 49.78/12.04/8.86、SurgeNetXL 35.82/7.34/5.18、GSViT 35.74/7.33/5.17、SelfSupSurg 36.03/7.38/5.22、EndoViT 32.32/9.29/6.31。本文の「+14.6% F1」は SurgMotion と EndoFM の差、「+18.3%」は DINOv3-L との差を指す。比較は手法の比較であり、要素ごとに分けた比較ではない。seed 数、分割、検定はいずれも記載なし。ハイパーパラメータは「16 個のヘッドを同時に学習し、最良の結果を報告」としており、検証データで選んだとは書かれていない。
- 事前学習データの内訳（Table 1）: 神経外科 2,860.85 h（PitVis・Web・施設内）、AVOS 125.16 h（開放手術、YouTube）、眼科 230.76 h（顕微鏡）、胃 252.10 h、胆嚢 77.51 h、大腸内視鏡 45 h、婦人科 23.12 h、泌尿器 20.45 h、肝 6.95 h、手技訓練 5.27 h、気管支鏡 50 h（非公開）、EgoSurgery 21 本・10.55 h（区分は「Breast surgery」「Mixed」と表記）。
- 不審点: ①EndoFM の EgoSurgery の F1/Jaccard（36.13/26.42）が Table 2 の Cholec80 の値と完全に一致し、Acc だけが違う（54.85 と 57.25）。②Table 5 の AVOS で 6 モデルが 48.34/8.15 の同値。③EndoMamba の Table 5 の値（58.45/36.23 など）が Table 6 の CholecT50 の AP と一致する。④AutoLaparo の EndoFM で Jaccard 47.84 が F1 35.77 を上回るが、同じクラス平均なら Jaccard は F1 以下になるはずである。⑤Table 1 の時間を足すと 3,707.72 h で、本文の 3,658 h と合わない。⑥EgoSurgery の区分表記「Breast surgery」は、データセット論文の「10 術式」と食い違う。
- 実装: GitHub CAIR-HKISI/SurgMotion（Apache-2.0）。重みは申請制で ViT-L（300M）と ViT-g（1B）がある。Table 3 がどちらの規模で出た値かは不明。事前学習は 1 fps で、EgoSurgery の 0.5 fps と合わない。評価に使う動画を事前学習から除いたかの記載はない。
- 要点: EgoSurgery で唯一の FM 比較表だが、評価動画の混入、転記ミスの疑い、検証データなしのモデル選択という問題があり、参考値として扱う。

### R3 SurgVISTA
- 書誌: Yang, Zhou, Mayer, …, Maier-Hein, Chen／2025／Large-scale Self-supervised Video Foundation Model for Intelligent Surgery／プレプリント（掲載先は不明）／arXiv 2506.02692
- 読んだ範囲: 本文と Extended Data Table 1〜12。
- 近さ: 方向 2／内視鏡・腹腔鏡・顕微鏡（評価のみ）／低侵襲手術が中心／クリップ（16 フレーム、間隔 4、1 fps）→工程／推論の規約: 不明／end-to-end の fine-tune。
- 事前学習データ（Ext. Table 1・2）: SurgPub は 8 データセット・274 本・1.20M フレーム（胆嚢・下垂体・胃バイパス・前立腺・子宮）。SurgWeb は Web の 3,376 本・2.35M フレームで、区分は腹腔鏡系の術式名と「Others 1,554 本・974,770 フレーム」。開放手術または一人称の映像は、明記されたものがない。「Others」の中身は不明なので、含まれるかどうかは判断できない。
- 証拠: 手法の比較で、95% 信頼区間と P 値がつく。CATARACTS（学習に使われていない種類の手術、顕微鏡）の Jaccard は SurgVISTA 63.6、ImageNet MAE 61.6、VideoMAE K400 60.7、ImageNet 教師あり 52.5（Ext. Table 9）。Cataract-101 では SurgVISTA 87.6、UMT K710 87.1（+0.5）、ImageNet 教師あり 79.2、ImageNet DINO 53.8（Ext. Table 10）。DINO 行の信頼区間（52.8, 64.7）は点推定に対して非対称で、不審である。
- 漏れの扱い: 評価に使うテスト動画を事前学習から除外したと明記している。さらに、M2CAI16 と重なる Cholec80 のテスト動画 5 本を除外している（方法の節）。
- 実装: ViT-B（encoder 87.4M）、スクラッチから初期化。コードは GitHub で公開予定と記載。ライセンスは不明。
- 要点: 学習に使われていない種類の手術での上積みは、強い一般映像モデル（UMT・MVD）に対して Jaccard 0.5〜2 点と小さい。

### R4 SelfSupSurg
- 書誌: Ramesh ほか／2023／Dissecting self-supervised learning methods for surgical computer vision／Medical Image Analysis 88:102844（査読つき）／arXiv 2207.00449
- 読んだ範囲: 要旨と本文の断片（検索で表示された範囲）。
- 証拠: ResNet-50 で、SSL を始める前に ImageNet の教師あり重みで初期化することが「critical hyperparameter」であった。ラベル付き動画が 10 本・5 本の設定では、SSL を加えると ImageNet 重みから直接 fine-tune するより「systematically」に改善した。全文（arXiv 2207.00449）を確認すると、"rarely do any of the SSL methods" という文はラベルが多い条件についてではなく、ImageNet 上で SSL した重み（"base"）についての記述だった：「when pretrained on Imagenet, rarely do any of the SSL methods featured here improve performance… (only 7 out of 36 times)」。手術データでの SSL の効果は、ラベル 5 本で最大 +6.1% F1（単一フレーム、MoCo v2）、最大 +6%（時間モデル、SwAV）。ラベル 40 本では SSL なしと同程度（差は最大 −1.2%）。ImageNet 教師あり（FS）初期化の効果は「up to +12% phase recognition F1」（MoCo v2）。
- 要点: 少数動画での ResNet SSL は、ImageNet 初期化の上に重ねたときに効く。

### R5 Jaspers 2024（データの多様性）と SurgeNetXL
- 書誌: Jaspers ほか／2024／Exploring the Effect of Dataset Diversity in Self-Supervised Learning for Surgical Computer Vision／DEMI 2024（LNCS 15265）／arXiv 2407.17904、DOI 10.1007/978-3-031-73748-0_5。および Scaling up self-supervised learning for improved surgical foundation models／Medical Image Analysis 2025／arXiv 2501.09436
- 読んだ範囲: 要旨のみ。
- 証拠（要旨）: 同じ術式のデータだけで SSL を行うと、ImageNet 事前学習に比べて 3 課題で +13.8%、+9.5%、+36.8%。そこに異種の手術データを加えるとさらに +5.0、+5.2、+2.5%。SurgeNetXL は 23 術式・4.7M フレーム。
- 要点: 腹腔鏡の領域では、手術 SSL は ImageNet に勝つ。

### R6 LEMON / LemonFM
- 書誌: Che ほか／2025／LEMON: A Large Endoscopic MONocular Dataset and Foundation Model for Perception in Surgical Settings／CVPR 2026／arXiv 2503.19740
- 読んだ範囲: 要旨とリポジトリの記述。
- 内容: 4K 本・938 時間・35 術式で、内視鏡系のみ。画像モデルで、ConvNeXt-Large（学習コマンドから確認）、出力は 1536 次元。データ、コード、重み（Hugging Face）を公開。ライセンスは不明。

### R7 Endo-FM / EndoMamba / GSViT / EndoViT / EndoSSL / GastroNet / SurgVLP（一覧用の簡略記録）
- Endo-FM: MICCAI 2023、arXiv 2306.16741。要旨（Wang, Liu, Zhang, Dou）によれば、事前学習データは「9 publicly available datasets and a privately collected dataset from Baoshan Branch of Renji Hospital… over 33K video clips with up to 5 million frames」で、これで学習した video ViT。Apache-2.0。
- EndoMamba: MICCAI 2025、arXiv 2502.19090、DOI 10.1007/978-3-032-05114-1_22。Table 1 によれば内視鏡 12 データセット（MIX12）で、「MIX12 consists of 74,828 video clips, comprising a total of 11,303,853 frames」。教師モデルは VideoMamba-S（α=0.25）。重みは公開予定と記載。
- GSViT: arXiv 2403.05949。Web の一般外科 680 時間・28 術式で次フレーム予測。EfficientViT 系（SurgVISTA の記述による）。
- EndoViT: IJCARS 19(6) 2024。Endo700k、MAE、ViT-B。ID 不明。
- EndoSSL: MICCAI 2023、arXiv 2308.12394。非公開の腹腔鏡 7,877 本・23.3M フレーム、MSN、ViT-L。
- GastroNet-5M: Gastroenterology 2025。消化管内視鏡の 5M 枚。ID 不明。
- SurgVLP: Medical Image Analysis 2025、arXiv 2307.15220。手術講義動画と書き起こし文の対比学習。
- 開放手術や一人称の映像を事前学習データに明記しているのは SurgMotion（AVOS と EgoSurgery）だけだった。眼科顕微鏡を含むのは SurgMotion（OphNet、CATARACTS）。

### R8 OmniRAS / ZEN / DART（凍結と fine-tune、一般モデルとの比較）
- OmniRAS: arXiv 2608.31048（要旨と一部）。凍結した encoder での比較は「mixed」で、上位 4 ブロックだけを fine-tune すると手術事前学習の利点がはっきりした。GraSP では凍結時の順位が逆転した。凍結と部分適応の両方を報告するよう提言している。
- ZEN: arXiv 2602.13633（一部）。手術画像で事前学習した MIS-DINOv2 が、既存の手術基盤モデルを多くの課題で上回った。
- DART: arXiv 2609.04555（一部）。手術画像で少し学習しただけの MAE や DINOv2 が、公開されている DINOv3 の重みを上回る傾向があった。
- 要点: 凍結か fine-tune かで順位が入れ替わる。

### R9 AVOS（開放手術の大規模データ）
- JAMA Surgery 159(2):185–192、2024、DOI 10.1001/jamasurg.2023.6262。本文（PMC10701669）によれば「From 9197 returned YouTube results (400 to 600 per search term), 1997 open surgical videos were manually identified」で、23 術式・50 か国にわたる。注釈つきは 343 本で、毎秒のラベルは cutting/tying/suturing/background（arXiv 2112.07219）。視点は主に俯瞰で、頭部装着カメラの映像も一部含む（第三者の報告による）。

### R10 OVFM（眼科顕微鏡の基盤モデル）
- Nature Biomedical Engineering 2026、DOI 10.1038/s41551-026-01622-w。読んだのは要旨のみ。1.1M クリップ・144 術式の video transformer で、蒸留して顕微鏡装置に載せる。

### R11 視線の使い道（方向 3・2）
- Li, Liu, Rehg「In the Eye of Beholder」ECCV 2018（ID 不明）: 視線を潜在的な注意として扱い、確率モデルで教師に使う（EGTEA）。
- Min & Corso, WACV 2021（ID 不明）: 視線を注意機構に組み込む。
- Can Gaze Inform Egocentric Action Recognition?（ETRA 2022、ID 不明、要旨のみ）: 推論時に視線を cross-modal attention で融合しても改善しなかった。否定的な結果。
- Human Gaze Guided Attention for Surgical Activity Recognition（arXiv 2203.04752）: GTEA で学習した視線予測を JIGSAWS に移し、注意の教師信号に使う。一人称から手術への転移の例。
- G3Ego（arXiv 2608.20157）: 視線で場面グラフを枝刈りする。
- 視線マスク（GGMAE）とこれらの使い方を同じデータで比べた研究は見つからなかった。

### R12 一人称の非手術映像での事前学習（方向 3）
- EgoVLP（Lin ほか、NeurIPS 2022 Spotlight、arXiv 2206.01670）: Ego4D から作った EgoClip（「3.8M clip-text pairs well-chosen from Ego4D」、映像 2.9K 時間分）で事前学習。5 つの一人称ベンチマークで改善。
- InternVideo-Ego4D（arXiv 2211.09529）: 一般の事前学習 backbone をそのまま使うと一人称で性能が落ちるため、Ego4D で fine-tune して差を縮めた。
- Ego4D・EPIC で事前学習した重みを手術に移した研究は、R11 の視線予測の転用を除き見つからなかった。

### R13 online 化と評価（方向 4・6）
- Surgformer（MICCAI 2024、arXiv 2408.03867）、SemiVT-Surge（arXiv 2506.01471、T=16 の窓をずらして online 評価）、SurgicalMamba（arXiv 2605.14889）: 窓の最後のフレームを予測する規約。窓を短くしたときに性能がどれだけ落ちるかを定量化した表は確認できなかった。
- Metrics Matter（Funke ほか、arXiv 2305.13961）: Cholec80 の評価実装の不一致（relaxed metric の欠陥など）を指摘。MoSFormer（arXiv 2503.00695）はこれを受けて relaxed metric をやめた。
- VideoMAE（NeurIPS 2022、arXiv 2203.12602）: 時間方向のサンプリング間隔に敏感。半分の間隔では 68.9 に下がる（本文 Table）。MME（CVPR 2023、arXiv 2210.06096）は間隔 s=2 が最良。

### R14 継続事前学習と否定的な結果（方向 5・7）
- Roth ほか（arXiv 2410.21302）: EVA-02 を内視鏡画像で継続事前学習。分割をまたがないよう患者単位で管理。
- 鳥類音響の MAE（arXiv 2605.14031）: 領域内データで継続 SSL をしても上積みは「marginal」で、中規模のデータでは一般重みからの教師あり fine-tune が優勢だった。否定的な結果。
- Dive into the details of SSL（Medical Image Analysis 2023、arXiv 2209.12157）: 事前学習データとテストデータを重ねないと明記。SSL が常に効くわけではないと報告。
- Toward Clinically Ready FMs（arXiv 2603.14271）: 対象領域の注釈なしデータを SSL に使うことを、暗黙の漏れとして論じている。

## (3) 探したが見つからなかったもの
- 「EgoSurgery」「egocentric open surgery phase」（2 回、計約 20 件）: SurgMotion 以外に EgoSurgery-Phase の工程認識の値を報告した論文は見つからなかった。ORQA（2505.12890）は QA データとして使うだけで、EgoSurgery-Tool（2406.03095）と EgoSurgery-HTS（2503.18755、DOI 10.1049/htl2.70049）は検出・分割の課題だった。
- 「frame rate sampling stride video MAE low fps」（約 8 件）: 1 fps 以下で映像 SSL や基盤モデルを評価した研究、フレームレートの不一致が転移に与える影響を測った研究は見つからなかった。
- 「variance across splits seeds surgical phase」: 検索の予算が尽きて実行できなかった。ただし SelfSupSurg §4.1 に該当する記述がある：「the variance in performance across dataset splits, particularly in the low-data settings, can surpass performance differences across methods」。同じ論文の注 8 によると、再実行 5 回の標準偏差は phase F1 0.7%。ばらつきを主題にした独立の文献と Metrics Reloaded は未確認。
- 術者・施設をまたぐ漏れ（前提 C）: EgoSurgery の術者 8 人・術式 10 種はデータセット論文に記載がある。しかし、どの動画がどの術者のものかの対応表と、術者単位で分割した評価は見つからなかった。

## (4) 未検証の組み合わせ
- 0.5 fps × クリップモデル（tubelet 2）× online: GGMAE のクリップ 10 フレームは 20 秒分にあたるが、推論の規約は不明。
- DINOv3 や V-JEPA 2 の重みを初期値にして EgoSurgery 上で視線マスクの継続 SSL を行う組み合わせ。GGMAE はスクラッチの ViT-S しか試していない。
- ResNet-50 の SSL（SelfSupSurg 型）と ViT の MAE を、EgoSurgery で同じ条件で比べた研究。
- 視線をマスクに使う場合と、crop・注意の教師・入力チャネルに使う場合を、同じ分割で比べた研究。
- 評価動画を事前学習に含める場合と除く場合を、EgoSurgery で並べた研究。

## (5) 検索記録（検索日 2026-10-08、web_search 18 回、web_fetch 6 回、サブエージェント 1 回）
- 方向 1: 3 回、確認 6 件（R1・R2、EgoSurgery-Tool・HTS、ORQA、EgoExOR）
- 方向 2: 8 回、記録 R3〜R10
- 方向 3: 2 回、記録 R11・R12（7 件）
- 方向 4: 2 回、記録 R13 の VideoMAE・MME・online 化（5 件）
- 方向 5: 1 回、記録 R14（2 件）
- 方向 6: 2 回、記録 4 件
- 方向 7: 独立の検索 1 回と各記録の抽出で 6 件（GGMAE の τ=0.25、SurgMotion の手術 FM の大敗、OmniRAS の凍結時の不一致、Can Gaze、鳥類 MAE、SelfSupSurg の多ラベル条件）
- 種のうち実在を確認したもの: GGMAE、SurgMAE（arXiv 2305.11451、引用で確認）、VideoMAE、VideoMAE V2、V-JEPA 2（arXiv 2506.09985、引用で確認）、DINOv3（arXiv 2508.10104、引用で確認）、SurgMotion、SurgVISTA、EndoViT、Endo-FM、GSViT、SurgeNetXL、LemonFM、SurgVLP、EndoMamba、GastroNet、SelfSupSurg、AVOS、EgoVLP。「Ego-Exo」は Ego-Exo4D（CVPR 2024、引用で確認）と判断した。

## (6) 解釈と提案（ここだけが解釈）
- 解釈: 問い (1) について、EgoSurgery 単体での SSL が強い一般重みに勝つという証拠はない。SelfSupSurg と Jaspers は ImageNet に勝つことを示したが、その条件は腹腔鏡で数十本以上の注釈なし動画を使った場合である。SurgMotion の Table 3 では、手術画像の基盤モデルが EgoSurgery で DINOv3 に大きく負けている。これは「腹腔鏡で学んだ表現は一人称の開放手術に移りにくい」ことを示唆する。
- 提案 1: 基準として DINOv3-L の凍結特徴と fine-tune の両方を、現行の因果 TCN に載せる。ResNet-50 の ImageNet 初期化と並べる。
- 提案 2: 腕として、①DINOv3 または VideoMAE V2 の重みから EgoSurgery で継続 SSL（ランダムマスクと視線マスク）、②視線 crop、③視線を注意の教師信号に使う、の 3 つを独立に足す。
- 提案 3: 事前学習は各 fold の学習用動画だけで行い、テスト動画を含める版は別の行として報告する。
- 提案 4: seed を 3 以上回し、動画単位のブートストラップで 95% 信頼区間を出し、術者の重なりを書く。SurgMotion の値は引用しても、比較の基準には使わない。
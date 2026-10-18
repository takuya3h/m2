# C2調査：凍結した術具検出出力を online 工程認識へ渡す設計を、一人称非手術映像から再検証する

## 系統表

本調査では「件数」を、検索エンジンのヒット総数ではなく、**題名・書誌を実在確認し、少なくとも要旨または本文まで確認して、この問いとの対応を判定したユニーク文献・チャレンジ報告の数**として数えた。方向間の重複は許している。特に方向三・四では、手術を検索語に入れない探索を独立に行った。

| 系統 | 代表的な文献 | 現役度 | 本記録の件数 |
|---|---|---|---:|
| 術具・工程の multi-task / context sharing | **EndoNet**; PhaKIR 2024 challenge report | Cholec80上の EndoNet は歴史的基準。PhaKIR は**新興**の統合ベンチマーク。現在の「tool output を phase に入れる」手法としての現役度は不明 | 2 |
| 検出物体スコアを時系列予測へ入れる late fusion | **RULSTM** | EPIC-KITCHENS action anticipation の主要な歴史的基準だが、今回の「直近2年の複数比較表」という定義だけでは現役度は**不明** | 1 |
| hand–object contact / state / graph | **Ego-OMG**, *Forecasting Action through Contact Representations from First Person Video*, Shiota et al. 2024 | WACV 2024まで継続している系統。個々の手法の現在順位は不明 | 2 |
| bounding box / trajectory を明示的に処理する object-centric video model | **STIN**, **ORViT** | SomethingElse、SSv2、EK100で確立した系統。ただし2024–2026の同条件ランキングを今回本文確認できず**不明** | 2 |
| object-aware auxiliary supervision / representation learning | **Helping Hands**; Tateno et al. 2026 | Helping Hands 後も hand/object cue の明示化が継続。Tateno et al. 2026 は**新興**プレプリント | 2 |
| long-term / next-active-object anticipation | *Object-centric Video Representation for Long-term Action Anticipation*; **StillFast**; **VISTA** | Ego4D 系で継続。VISTA は2026年技術報告なので**新興** | 3 |
| 汎用 conditioning / 小型界面 | **FiLM** | 一般的 conditioning の定番概念。ただし「独立学習済みの二モデルを凍結し、その間だけ学習」という条件での現役度は**不明** | 1 |
| 評価・分割・negative evidence | Kostiuchik et al. 2024; STIN/ORViT/Helping Hands の oracle・negative ablation; EndoNet | 方法論として重要。ランキング型の「現役度」は適用しにくいため**不明** | 5 |

EndoNet は術具認識と工程認識を共有表現で結合し、PhaKIR は工程・器具キーポイント・器具インスタンス分割を同一13本の腹腔鏡手術上で統一注釈したため、手術側の「工程と器具を同じデータ上で扱う」系統は継続している。ただし、PhaKIR の要旨が保証しているのは**三課題を同じデータで調べられること**であり、「器具予測を phase recognizer に入れた」ことではない。 citeturn24view1turn11search2

非手術側では、RULSTM の confidence-based bag-of-objects、STIN の手・物体 box trajectory、ORViT の object-region/trajectory token、Ego-OMG の contact graph、Helping Hands の detector-generated pseudo-box supervision という、互いにかなり異なる系統が確認できた。したがって「object signal」と一括りにすると、**クラス確率、box geometry、RoI appearance、contact state、object semantics、object-aware pretraining supervision**を混同する。これは C2 の界面設計で明示的に分離すべき前提である。 citeturn3view0turn20view4turn19view0turn17view0turn25view2

**方向別に実在確認した件数**は次の通りである。方向一は1件、方向二は9件、方向三は10件、方向四は4件、方向五は3件、方向六は2件、方向七は5件だった。ここにはユーザーが既に所持している文献を、系統確認・negative evidence のために参照したものも含むが、下の詳細記録は原則として新たに調べた文献を中心とした。

特に C2 に近い事実だけ先にまとめると、**検出 box を正解 box に替えると下流が大きく変わる**証拠は STIN と ORViT にある一方、**強い受け取り側では単純な object fusion の利得が消える、または負になる**例も ORViT の EK100/SSv2 比較に明瞭にある。Helping Hands では object-aware supervision の利得は強い pretrained video-language backbone 上でも残るが、これは推論時に detector output を渡す方式ではない。 citeturn20view5turn21view0turn21view1turn17view0

### EndoNet Fig. 10 の値の確認

ユーザー指定のため、既所持文献である EndoNet については通常の文献記録を省き、Fig. 10 だけを別に検証した。論文は *EndoNet: A Deep Architecture for Recognition Tasks on Laparoscopic Videos*、arXiv:1602.03012、DOI **10.1109/TMI.2016.2593957** である。Fig. 10 は Cholec80 の CNN fine-tuning に使う動画数を10、20、30、40本と変え、固定された評価側動画で tool presence と phase recognition を比較している。 citeturn9view0turn10view0turn11search2

| CNN の学習に用いる動画本数 | ToolNet：Mean AP | EndoNet：Mean AP | EndoNet − ToolNet | PhaseNet：Mean Accuracy | EndoNet：Mean Accuracy | EndoNet − PhaseNet |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 65.9 | 62.0 | −3.9 pp | 65.9 | 65.8 | −0.1 pp |
| 20 | 70.9 | 67.5 | −3.4 pp | 68.2 | 70.8 | +2.6 pp |
| 30 | 73.6 | 77.5 | +3.9 pp | 72.1 | 72.5 | +0.4 pp |
| 40 | 80.9 | 81.0 | +0.1 pp | 73.0 | 75.2 | +2.2 pp |

数値は Fig. 10 の図中値そのもの。術具側の指標は **Mean AP**、工程側は **Mean Accuracy** である。著者自身も、データ増加とともに両課題が改善し、EndoNet は概ね single-task network より良くなる一方、**tool presence では少数動画時に EndoNet が ToolNet より悪い**ことを述べている。つまり10本・20本では multi-tasking の符号が負で、30本で正に反転する。 citeturn5view2turn9view0

ここには C2 にとって重要な注意がある。Fig. 10 の「10/20/30/40 videos」は、単純に「phase classifier 全体をその本数だけで学習した」という意味ではなく、EndoNet/PhaseNet の CNN fine-tuning に使う手術動画数を変えた実験である。論文の phase recognition 系は CNN features の上に SVM を置き、評価側 Cholec80 上で交差検証する構成を含む。したがって C2 の「15本を動画単位CVし、held-out video の情報を一切 interface 学習に使わない」という設定と同一ではない。 citeturn5view3

さらに、Fig. 10 の40本で PhaseNet 73.0、EndoNet 75.2 という値は論文の **HHMM 前**の phase accuracy と一致する。これは Fig. 10 が HHMM による temporal smoothing 後の online 値ではないと読むのが自然である。ただしこれは表間の一致に基づく本調査の照合結果であり、Fig. 10 caption 自体が「HHMMなし」と明記している、という意味ではない。 citeturn6view0turn9view0

もう一つ重要な negative result は、EndoNet が学習した tool-related representation に対して **ground-truth binary tool presence** を追加しても phase accuracy がほとんど増えない点である。論文の比較では、HHMM 前が EndoNet 75.2 に対して EndoNet+GTBin 75.3、HHMM 後が81.7に対して81.9で、差はそれぞれ +0.1 pp、+0.2 pp に留まる。これは「正解 tool signal なら必ず phase を大きく改善する」という仮定に対する直接的な反例である。 citeturn6view0


## 文献ごとの記録

**EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos**

- 著者／年／題名／掲載先: Ryo Fujii, Masashi Hatano, Hideo Saito, Hiroki Kajita／2024／*EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos*／MICCAI 2024 early accepted、査読つき。arXiv: **2405.19644**。 citeturn24view0
- 読んだ範囲: 要旨と arXiv 書誌。数値表本文は今回の取得範囲では未確認。
- 方向: 一。
- 視点: 一人称。
- ドメイン: 開放手術。
- 課題の形: 頭部装着カメラの開放手術映像から surgical phase を認識。gaze も提供し、GGMAE では gaze を pretraining の masking prior に使う。 citeturn24view0
- 推論の規約: 要旨だけでは online / offline の厳密な因果規約は不明。
- データ規模: 約15時間、9 phases。動画本数は今回確認した要旨には記載されていないため、論文根拠としては不明。 citeturn24view0
- モデルの状態: GGMAE と phase model を用いる構成であり、「独立に学習した D と P を凍結し interface のみ学習」ではない。 citeturn24view0
- 系統: 一人称開放手術 phase recognition／auxiliary gaze representation。
- 現役度: EgoSurgery-Phase 自体の benchmark では2024年論文が基準だが、2026年までの査読済み比較表を今回確認していないので**不明**。
- どのベンチマークか: EgoSurgery-Phase。
- 少数動画／online／一人称: 一人称は該当。少数動画条件はユーザーの現行設定には該当するが、論文本文の動画本数を今回再確認できていない。online は不明。
- 何と何を比べた差か: 要旨では GGMAE と previous SOTA、ならびに通常の MAE-based method を比較。
- 効果量: Jaccard で previous SOTA に +6.4 pp、MAE-based method に +3.1 pp と要旨に記載。ただし表番号を本文確認できていないため、C2の主要数値証拠には採用しない。 citeturn24view0
- 符号: 改善。
- 符号や大きさが変わる条件: 不明。
- 基準の強さ: 要旨では previous SOTA と記述。具体的手法・表は未確認。
- その要素だけを変えた比較か: 本文表未確認のため不明。
- seed／分割／検定: 不明。
- 著者以外の追試や採用: 今回確認できず。
- コードと重み: dataset link が arXiv から公開されている。コード・重み・ライセンス詳細は今回未確認。 citeturn24view0
- 追加データ・注釈: gaze。
- pretraining overlap: 本文未確認。
- 一行の要点: **同じ一人称開放手術という意味では最も近いが、tool detector output を phase model に渡す研究ではない。**

**Rolling-Unrolling LSTMs for Action Anticipation from First-Person Video**

- 著者／年／題名／掲載先: Antonino Furnari, Giovanni Maria Farinella／2020–2021／*Rolling-Unrolling LSTMs for Action Anticipation from First-Person Video*／IEEE TPAMI、査読つき。arXiv: **2005.02190**、DOI **10.1109/TPAMI.2020.2992889**。 citeturn2search1turn2search3
- 読んだ範囲: 本文。
- 方向: 三、ならびに問い二。
- 視点: 一人称。
- ドメイン: 非医療、調理。
- 課題の形: 観測済み映像から未来の action を anticipation。RGB、optical flow、objects の別 branch を RU-LSTM で処理し、modality attention で統合する。 citeturn3view0
- 推論の規約: action anticipation のため未来フレームを入力せず、観測済み区間のみを使用する。この意味で C2 の「未来を見ない」に近い。 citeturn3view0turn3view1
- データ規模: EPIC-KITCHENS と EGTEA Gaze+。正確な全動画数はこの記録では再転記せず、不明扱いとする。
- モデルの状態: object detector は Faster R-CNN/ResNet-101。EPIC では対象 object classes 用に学習され、特徴抽出器は事前計算後固定される。一方 RU-LSTM branch は下流課題で学習されるため、**C2の「DとPの両方を凍結」より緩い**。 citeturn3view0
- 系統: detector confidence の temporal late fusion。
- 現役度: 直近2年の複数査読論文の比較表を今回は確認できず**不明**。
- ベンチマーク: EPIC-KITCHENS、EGTEA Gaze+。
- 少数動画／online／一人称: 一人称・causal anticipation は該当。少数動画ではない。
- 何と何を比べた差か: RGB/flow/object modalities とそれらの融合を比較。object representation は検出 confidence をクラスごとに和した “bag of objects” で、box位置自体は捨てる。 citeturn3view0
- 効果量: object branch の寄与に関する表は確認したが、今回取得した本文断片だけでは「どの行との差か」を誤同定する危険があるため、数値は不明とする。
- 符号: 総じて object 情報は補完的だが、常に大きいわけではない。
- 符号・大きさが変わる条件: modality attention が appearance だけで十分な場面では object branch の重みを小さくする。著者の failure analysis では detector が “chair” を捉えられず失敗する例、pan の検出が誤った future action を誘発する例が示される。 citeturn3view0
- 基準の強さ: 当時の action anticipation benchmark 用モデル。
- その要素だけを変えた比較か: modality ablation は比較的近いが、fusion architecture の学習も含む。
- seed／分割／検定: 統計検定の記載は今回確認できず。
- 独立追試・採用: RULSTM は後続の egocentric anticipation 系で広く参照されるが、本調査の現役度定義を満たす複数の2024–26比較表までは確認していない。
- コード・重み・ライセンス: 論文に実装公開の系譜があるが、本調査ではライセンスを確認できず。
- 追加データ・注釈: object detector 学習には object annotations。EGTEA では EPIC 用 detector を転用しており、domain/class mismatch がある。 citeturn3view0
- pretraining overlap: detector を同じ EPIC training domain に適応しているため、fold設計を C2 に移す際には detector の学習動画を厳格に分離する必要がある。
- 一行の要点: **「同時刻までに得た detector confidence を causal temporal model に入れる」という構造上、非手術で最も直接的な先例の一つ。**

**Something-Else: Compositional Action Recognition with Spatial-Temporal Interaction Networks**

- 著者／年／題名／掲載先: Joanna Materzynska et al.／2020／*Something-Else: Compositional Action Recognition with Spatial-Temporal Interaction Networks*／CVPR 2020、査読つき。arXiv: **1912.09930**。 citeturn18academia29turn19view1
- 読んだ範囲: 本文。
- 方向: 四、七。
- 視点: 三人称／一般映像。
- ドメイン: 非医療。
- 課題の形: Faster R-CNN で hand と manipulated object を二クラス検出し、tracking 後の box 座標と object identity embedding を時空間 interaction model に入れて action recognition。 citeturn20view4
- 推論の規約: video clip の center crop を使う offline classification。online ではない。 citeturn20view4
- データ規模: SomethingElse compositional benchmark、174 action categories。 citeturn20view5
- モデルの状態: detector は COCO pretraining 後、action train split の box annotations で独立 fine-tune。STIN/action model は別に学習される。P は凍結されない。 citeturn20view4
- 系統: hand/object geometry・trajectory reasoning。
- 現役度: ORViT が同 benchmark 上で後に比較しているが、2024–26の現役度定義に必要な比較表を確認していないため**不明**。
- ベンチマーク: SomethingElse compositional split。
- 少数動画／online／一人称: いずれも該当しない。
- 何と何を比べた差か: 同じ STIN+OIE+NL に **ground-truth boxes** と **detected boxes** を入れた結果が Table 3(a)/(b) で直接比較できる。 citeturn20view5
- 効果量: compositional top-1 は GT box で **51.4%**、detected box で **37.2%**、差 **−14.2 pp**。top-5 は79.3%対62.4%、差−16.9 pp。これは action model 自体の oracle gap として非常に大きい。Table 3。 citeturn20view5
- 符号: detector 化で大幅悪化。
- 符号や大きさが変わる条件: I3Dとの結合では GT box 時 I3D 46.8%に対し joint 54.6%（+7.8 pp）、detected box 時は48.2%（+1.4 pp）。box noise が利得を大きく圧縮する。Table 3。 citeturn20view5
- 基準の強さ: I3D は当該論文の appearance baseline。さらに STRG とも比較。
- その要素だけを変えた比較か: GT-versus-detected の STIN 同士はかなり直接的。ただし detector→GT で tracking quality も同時に影響し得る。
- seed／分割／検定: seed数・統計検定は今回確認した記述では不明。
- 独立追試・採用: ORViT が後続比較で STIN を object-centric baseline として再実装・比較している。 citeturn19view0
- コード・重み・ライセンス: 今回ライセンス未確認。
- 追加データ・注釈: dense hand/object boxes。
- pretraining overlap: detector は COCO pretrain後に action training split の annotations で fine-tune。test annotations を detector 学習に使う記述はない。 citeturn20view4
- 一行の要点: **C2で「検出精度が足りなければ下流利得が消える」可能性を支持する、最も明瞭な oracle-gap の一つ。**

**Object-Region Video Transformers**

- 著者／年／題名／掲載先: Roei Herzig et al.／2022／*Object-Region Video Transformers*／ECCV 2022 系、査読つき。arXiv: **2110.06915**。 citeturn18academia28turn19view0
- 読んだ範囲: 本文・supplement 相当のHTML。
- 方向: 三、四、七。
- 視点: EK100では一人称、他は一般映像。
- ドメイン: 非医療。
- 課題の形: detector/tracker が得た boxes を video transformer の途中層へ object region appearance と trajectory dynamics として繰り返し注入。 citeturn19view0
- 推論の規約: standard action recognition は clip-based offline。C2の online phase recognitionとは異なる。 citeturn21view2
- データ規模: EK100 は700 egocentric videos、300 noun、97 verb classes。SomethingElse compositional split は54,919 train/54,876 validation clips、174 classes。 citeturn21view2turn21view1
- モデルの状態: detector と video model に weight sharing はないが、video transformer と ORViT block は fine-tune される。二モデル凍結＋interface-onlyではない。 citeturn21view0
- 系統: object-region conditioning／trajectory injection。
- 現役度: 2024–26の同条件査読比較表を今回確認していないため**不明**。
- ベンチマーク: SomethingElse、SSv2、EK100、Diving48、AVA。
- 少数動画／online／一人称: EK100のみ一人称。少数動画・onlineではない。
- 何と何を比べた差か: EK100 Table 3(c) で同じ強い MF-HR を基準に object-centric modules を加える。 citeturn20view2
- 効果量: MF-HR baseline は action/verb/noun top-1 **44.5/67.0/58.5**、ORViT は **45.7/68.4/58.7**。差は **+1.2/+1.4/+0.2 pp**。一方 MF-HR+STRG は action 42.5（−2.0 pp）、+STIN は44.2（−0.3 pp）、+STRG+STIN は44.1（−0.4 pp）。Table 3(c)。 citeturn20view2
- 符号: ORViT は改善するが、**単純な既存 object modules は強い recipient 上で差なしまたは悪化**。
- 符号や大きさが変わる条件: SSv2でも MF 66.5 に MF+STRG 66.1、MF+STIN 66.5、両者66.6と、既存 object fusion の利得はほぼ消える一方、ORViT MF は67.9（+1.4 pp）。Table 3(a)。 citeturn21view1
- detector品質との関係: 著者は detector boxes の ORViT が MF/MF-L を各+1.4 pp改善するのに対し、手作業の annotated boxes を oracle とすると改善が **+7.3 pp / +6.7 pp** になると報告する。これは detector quality と downstream ceiling の大きな隔たりを示す。 citeturn21view0
- 入れる位置: ORViT block を末端だけではなく早い layer に置く方が良い。SomethingElse Table 4(a) では MF 60.2、layer 12のみ63.9、layer 2のみ66.7、layer 2 + dynamics 68.8、layers 2/7/11 + dynamics 69.7 top-1。 citeturn21view0
- その要素だけを変えた比較か: Table 4 の layer/box ablation は比較的明確。Table 3 の他手法比較は architecture も変わる。
- seed／分割／検定: 統計検定は確認できず。
- 独立追試・採用: STIN等を自ら再比較しているが、2024–26の独立追試は今回本文確認できず。
- コード・重み: project/code release が論文に記載。ライセンスは未確認。 citeturn19view0
- 追加注釈: SSv2では detector fine-tuning用 boxes。EK100/Diving48では COCO-pretrained Faster R-CNN の class-agnostic boxes を使用するため、in-domain object labels は不要。 citeturn20view0turn21view0
- pretraining overlap: EK100 detector は COCO、video backbone は Kinetics/ImageNet系で、論文記載の範囲では EK100 test の box annotations を detector training に使わない。
- 一行の要点: **「強い映像モデルなら object signal の利得が自動的に残る」わけではなく、fusion の設計次第で +1 pp 程度にも、0/負にもなる。**

**Helping Hands: An Object-Aware Ego-Centric Video Recognition Model**

- 著者／年／題名／掲載先: 2023／*Helping Hands: An Object-Aware Ego-Centric Video Recognition Model*／ICCV 2023、査読つき。arXiv: **2308.07918**。 citeturn1search7turn17view0
- 読んだ範囲: 本文。
- 方向: 三、四、七。
- 視点: 一人称。
- ドメイン: 非医療。
- 課題の形: 100DOH hand-object detector の pseudo boxes と video captions/object words を**学習時 supervision**として用い、object-aware decoder を付加した egocentric video-language representation を学習する。推論時に外部 detector output を P へ渡す方式ではない。 citeturn17view0
- 推論の規約: clip representation learning／zero-shot recognitionで、C2のonline時系列認識ではない。
- データ規模: EGTEA は28時間、86 sessions、32 subjects、106 fine-grained classes。ほかに EgoClip/Ego4D、EK100、VISOR 等を用いる。 citeturn17view0
- モデルの状態: 著者は計算資源制約から visual backbone を unfreeze して end-to-end train できなかったと明記している。したがって**強い pretrained backbone を固定したまま、object-aware側を学習する**という点では C2 に構造的類似がある。ただし「別 detector の同時刻出力を inference 時に interface へ入れる」ものではない。 citeturn17view2
- 系統: object-aware auxiliary supervision。
- 現役度: 2026年までの同 benchmark の比較表を今回追い切れていないため**不明**。
- ベンチマーク: EgoMCQ、EK100-MIR、EGTEA、VISOR、EgoNLQ/EgoMQ。
- 少数動画／online／一人称: 一人称は該当。少数動画・onlineは非該当。
- 何と何を比べた差か: Table 1 の同一 architecture で、通常の \(L_{Ego}\) だけと box+word object supervision を加えたものを比較。 citeturn17view0
- 効果量: EK100-MIR は mAP 35.9→37.5（**+1.6 pp**）、nDCG 36.6→37.8（**+1.2 pp**）。EGTEA は Top-1 44.9→46.6（**+1.7 pp**）、Mean 37.6→39.1（**+1.5 pp**）。Table 1。 citeturn17view0
- 符号: 改善。
- detector品質との関係: Table 2 で 100DOH detector の入力解像度を256pと640pに変え、より良い pseudo boxes で学習すると、著者は EK/EGTEA の平均 zero-shot transfer がさらに約1%向上すると報告する。これは「box quality を変えると downstream gain も変わる」直接的実験だが、**detector mAPを横軸にした相関解析ではない**。 citeturn17view1turn17view2
- 不審点: arXiv HTML の Table 2 行では640pの EGTEA Top1/Mean に相当する **39.1 / 46.6** が、Table 1 の **46.6 / 39.1** と逆順に現れる。HTML parse または表見出し整形上の不整合が疑われるため、Table 2 のその2値を本報告では効果量として再利用しない。 citeturn17view0
- 手 boxes の効果: 著者は Table 5 で objects に加えて hands を予測させると zero-shot performance が概ね約1%上がると記述する。 citeturn17view2
- 基準の強さ: LaViLa TSF-L 等、大規模 egocentric pretraining を行った強い video-language models と比較。Table 4。 citeturn17view1
- その要素だけを変えた比較か: Table 1 は比較的明確。Table 4 の SOTA 比較は batch size、hard-negative sampling、decoder 等が混ざるため、object signal だけの効果とは扱わない。
- seed／分割／検定: 統計検定は確認できず。
- 独立追試・採用: 2026年の hand/object-cue 分析へ系統が継続しているが、Helping Hands 自体の独立再現数は今回不明。
- コード・重み・ライセンス: 今回ライセンス未確認。
- 追加データ・注釈: 100DOH detector、captions/pseudo object labels。
- pretraining overlap: EgoMCQ は pretraining dataset Ego4D と同じ data source であることを著者自身が明記。exact clip overlap の有無は今回不明。EK100/EGTEA は domain transfer。 citeturn17view0
- 一行の要点: **強い pretrained recipient 上でも object-awareness の利得は残るが、推論時 D→P ではなく「object supervision で表現自体を変える」方式である。**

**Egocentric Object Manipulation Graphs**

- 著者／年／題名／掲載先: Eadom Dessalene et al.／2020／*Egocentric Object Manipulation Graphs*／プレプリント。arXiv: **2006.03201**。後続の *Forecasting Action through Contact Representations from First Person Video* は arXiv: **2102.00649** で、contact anticipation を拡張している。 citeturn25view2turn22search1
- 読んだ範囲: Ego-OMG 本文、後続論文は要旨。
- 方向: 三、問い二。
- 視点: 一人称。
- ドメイン: 非医療・調理。
- 課題の形: hand-object contact によって動画を semantic manipulation states にし、その遷移を graph として長期時間文脈に使い、future action を予測・anticipate。後続論文では Contact Anticipation Maps と Next Active Object Segmentation も導入する。 citeturn22search1turn22search5
- 推論の規約: future action anticipation なので観測済み過去から未来を予測する causal task。
- データ規模: EPIC-KITCHENS 系。正確な動画本数は今回数値転記せず不明。
- モデルの状態: appearance CSN と semantic/contact graph branch を別に構成して融合するが、C2の二つの凍結済みモデル＋interface-onlyではない。
- 系統: contact state / semantic graph。
- 現役度: 2024 WACV の hand-object contact/object-state 系にも発想が継続しているが、Ego-OMG自体の現在順位は**不明**。Shiota et al. 2024 の DOI は **10.1109/WACV57701.2024.00641**。 citeturn22search0
- ベンチマーク: EPIC-KITCHENS。
- 少数動画／online／一人称: 一人称・causal anticipation は該当。少数動画ではない。
- 何と何を比べた差か: Ego-OMG Table 2 では appearance-only CSN、graph-only GCN、fusion を比較。
- 効果量: 取得した表では CSN **15.51 / 9.82**、GCN **12.94 / 10.10**、fusion **19.28 / 13.06**（seen/unseen split）。したがって fusion − CSN は **+3.77 pp / +3.24 pp**。Table 2。 citeturn12search7turn25view2
- 符号: 改善。
- 符号や大きさが変わる条件: unseen split でも相補性が残るが、graph-only は appearance-only を一律に上回らない。
- 基準の強さ: 当時の CSN appearance branch。
- その要素だけを変えた比較か: fusion比較では graph branch追加が主要変更だが、C2の小型界面だけとは異なる。
- seed／分割／検定: 複数runの記述はあるが、本回答で厳密な seed数を再確認できず不明。
- 独立追試・採用: contact-centered anticipation が後続TPAMI論文およびWACV 2024系へ継続。 citeturn22search1turn22search0
- コード・ライセンス: 不明。
- 追加データ・注釈: 後続論文では EPIC-Kitchens subset に hand/object segmentation と time-to-contact annotations を追加。 citeturn22search1
- pretraining overlap: 不明。
- 一行の要点: **object classそのものより「接触状態と状態遷移」を temporal cue にする別系統で、D出力を単なるクラス確率に潰す設計との対照になる。**

**Object-centric Video Representation for Long-term Action Anticipation**

- 著者／年／題名／掲載先: Ce Zhang et al.／2024／*Object-centric Video Representation for Long-term Action Anticipation*／WACV 2024、査読つき。arXiv: **2311.00180**。 citeturn25academia21turn22search15
- 読んだ範囲: 要旨のみ。
- 方向: 三。
- 視点: Ego4D/EGTEAでは一人称、50Saladsは三人称。
- ドメイン: 非医療。
- 課題の形: general-purpose vision-language pretrained models から “object prompts” で task-specific object-centric representations を抽出し、Transformer が将来行動予測に必要な objects を時間スケールごとにretrieveする。 citeturn25academia21
- 推論の規約: long-term action anticipation。未来予測なので入力は観測部分。
- データ規模: Ego4D、50Salads、EGTEA Gaze+。正確な規模は要旨では不明。
- モデルの状態: in-domain supervised detector を前提とせず pretrained VLM を利用。凍結範囲の詳細は本文未確認。
- 系統: object prompt / long-term anticipation。
- 現役度: 2024査読論文だが、2026までの複数比較表を本文確認できず**不明**。
- 少数動画／online／一人称: anticipation・一人称 benchmark を含むが、C2のframe-online phase labelingとは異なる。
- 効果量／oracle gap／negative result: 要旨のみのため数値は**不明**。
- その要素だけを変えた比較か: 不明。
- seed／検定: 不明。
- コード・重み・ライセンス: 不明。
- 追加注釈: in-domain detector labels を不要にする点が主眼。
- pretraining overlap: VLM pretraining corpus と benchmark の重複監査は要旨から不明。
- 一行の要点: **「専用detector出力」だけでなく、large pretrained model から object representation を取り出す系統が long-horizon anticipation では成立している。**

**StillFast: An End-to-End Approach for Short-Term Object Interaction Anticipation**

- 著者／年／題名／掲載先: Francesco Ragusa, Giovanni Maria Farinella, Antonino Furnari／2023／*StillFast: An End-to-End Approach for Short-Term Object Interaction Anticipation*／CVPR 2023、査読つき。arXiv: **2304.03959**。 citeturn22search2turn22search24
- 読んだ範囲: 要旨と結論。
- 方向: 三、問い二の隣接系統。
- 視点: 一人称。
- ドメイン: 非医療。
- 課題の形: 最後の高解像度 still image と過去 video clip を同時に処理し、next-active object の box、noun、future interaction verb、time-to-contact を予測する。 citeturn22search2
- 推論の規約: Ego4D STA は未来の interaction を、観測済み video から予測する causal task。
- データ規模: Ego4D。正確な本数は本記録では不明。
- モデルの状態: end-to-end。独立凍結 detector output を temporal model に渡す構造ではない。
- 系統: next-active-object anticipation。
- 現役度: 2026 VISTA が明示的に “StillFast-style design” を採るため設計系譜の継続は確認できるが、ユーザー定義の「複数の直近2年査読表」を満たすかは確認不足で**不明**。 citeturn22search10
- 少数動画／online／一人称: 一人称・causal future prediction は該当。少数動画ではない。
- 効果量: challenge 2022で public leaderboard 1位と論文要旨に記載するが、今回 table-level numeric effect は未確認のため書かない。 citeturn22search2
- negative result／oracle gap: 本文表未確認。
- seed／検定: 不明。
- コード・重み: project/code release が著者ページ・論文で案内される。ライセンス未確認。 citeturn22search6
- 追加注釈: Ego4D STA annotations。
- pretraining overlap: 不明。
- 一行の要点: **object localization と temporal context を結ぶ設計だが、C2の「既存D出力だけを凍結Pへ足す」より統合度が高い。**

**VISTA: Technical Report for the Ego4D Short-Term Object Interaction Anticipation at EgoVis 2026**

- 著者／年／題名／掲載先: Qiaohui Chu et al.／2026／*VISTA: Technical Report for the Ego4D Short-Term Object Interaction Anticipation at EgoVis 2026*／技術報告・プレプリント。arXiv: **2605.20901**。 citeturn22search10
- 読んだ範囲: 要旨のみ。
- 方向: 三、五。
- 視点: 一人称。
- ドメイン: 非医療。
- 課題の形: COCO-pretrained Faster R-CNN R50-FPN が last observed high-resolution frame から proposals を出し、**frozen V-JEPA 2.1 temporal branch** が過去clip contextを抽出。それを feature modulation と RoI-level fusion で detection pathway に注入し、future box/noun/verb/time-to-contact/confidenceを予測する。 citeturn22search10
- 推論の規約: future interaction anticipation、過去のみ。
- データ規模: Ego4D STA。詳細不明。
- モデルの状態: V-JEPA 2.1 temporal branch は明示的に frozen。Faster R-CNN 全体が frozen かは要旨では不明。したがって「双方を凍結し、界面のみ学習」とは断定できない。 citeturn22search10
- 系統: strong frozen pretrained video model + object-centric detector fusion。
- 現役度: **新興**。2026プレプリントで独立追試はまだ判断できない。
- 少数動画／online／一人称: 一人称・causal は該当。少数動画ではない。
- 何と何を比べた差か／効果量: 要旨には official challenge server 1位とあるが、fusion無しとの clean ablation の数値を本文確認できていないため**不明**。 citeturn22search10
- 符号: final system としては高性能だが、「object signal の追加効果」の符号は要旨だけでは判定不能。
- seed／検定: 不明。
- コード: release予定と要旨に記載。ライセンス不明。 citeturn22search10
- 追加データ: COCO-pretrained detector、V-JEPA pretraining。
- pretraining overlap: V-JEPA 2.1 の pretraining data と Ego4D STA の重複を本調査では検証できず。
- 一行の要点: **2026年まで含めると、frozen large temporal model と object detector pathway の融合は実際に使われているが、C2と同じ「界面だけ学習」のclean experiment は確認できない。**

**Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?**

- 著者／年／題名／掲載先: Masatoshi Tateno, Alexandros Stergiou, Risa Shinoda, Yoichi Sato, Dima Damen／2026／*Do Egocentric Video-Language Models Capture Both Hand- and Object-Centric Cues?*／arXiv preprint、MIRU 2026発表。arXiv: **2607.08514**。 citeturn23search3turn23search23
- 読んだ範囲: 要旨。
- 方向: 三、七。
- 視点: 一人称。
- ドメイン: 非医療。
- 課題の形: hand cue と object cue を分離した CI-HOI/DEHOI 評価を作り、video-language models が hand manipulation、object transformation、context のどこに依存するかを診断。hand-object masked training と HOI-dynamics-aware decoder を提案。 citeturn23search3turn23search15
- 推論の規約: standard HOI/action recognition。online条件は不明。
- データ規模: 要旨から正確な規模は不明。
- モデルの状態: pretrained video-language models を対象とするが、全freeze条件は要旨から不明。
- 系統: cue-isolation／negative diagnostic。
- 現役度: **新興**。2026年プレプリント。
- 少数動画／online／一人称: 一人称のみ明確。
- 何と何を比べた差か: hand-only/object-onlyに近い cue-isolated observations と標準観測を用いて shortcut reliance を診断。
- 効果量: 要旨のみなので数値は**不明**。
- 符号・negative finding: 著者は既存 video-language models が手・物体 dynamics そのものではなく、hands、objects、environment context 間の spurious correlations に依存し得ると報告する。 citeturn23search3
- 基準の強さ: pretrained video-language models が対象。
- clean ablation: cue-isolated evaluation 自体がこの問題を切り分けるための設計。
- seed／検定: 不明。
- 独立追試: 2026年のため不明。
- コード・重み: 今回未確認。
- 追加注釈: DEHOI testbed、inpainting-based cue separation。
- pretraining overlap: 不明。
- 一行の要点: **強い pretrained recipient が既に object information を十分持っている、という仮定自体を検査すべきであることを示す最近のnegative-oriented evidence。**

**Comparative validation of surgical phase recognition, instrument keypoint estimation, and instrument instance segmentation in endoscopy: Results of the PhaKIR 2024 challenge**

- 著者／年／題名／掲載先: Tobias Rueckert et al.／2026 journal version／*Comparative validation of surgical phase recognition, instrument keypoint estimation, and instrument instance segmentation in endoscopy: Results of the PhaKIR 2024 challenge*／Medical Image Analysis、査読つき。arXiv: **2507.16559**、DOI **10.1016/j.media.2026.103945**。 citeturn24view1
- 読んだ範囲: 要旨・書誌。
- 方向: 二、六。
- 視点: 内視鏡・腹腔鏡。
- ドメイン: 低侵襲手術。
- 課題の形: phase recognition、instrument keypoint estimation、instrument instance segmentation を同一動画で評価できる multi-task benchmark。 citeturn24view1
- 推論の規約: full procedure の temporal information を扱える設計だが、各phase methodが causal online かは要旨では不明。
- データ規模: **13 full-length laparoscopic cholecystectomy videos、3 institutions**。 citeturn24view1
- モデルの状態: challenge参加法ごとに異なるため一括判定不能。
- 系統: unified surgical context/instrument benchmark。
- 現役度: benchmarkとして**新興**。MICCAI 2024 EndoVis challengeを2026 MedIAで総括。 citeturn24view1
- 少数動画／online／一人称: **少数動画**は強く該当。一人称ではなく内視鏡。onlineは不明。
- 何と何を比べた差か／効果量: challenge report本文の14 tablesを今回数値転記していないため不明。
- instrument→phase の直接証拠: 要旨は三課題の**joint investigationを可能にする**と述べるが、instrument predictions を phase model input にした clean experiment があるとは要旨から確認できない。 citeturn24view1
- seed／分割／検定: challenge は BIAS guidelines に沿うと明記。詳細は本文未転記。 citeturn24view1
- コード・重み: challenge resource。ライセンス詳細未確認。
- 追加データ: unified annotations。
- pretraining overlap: teamごとに異なり不明。
- 一行の要点: **13本という小規模手術データで phase と instrument を同時に研究できる最新ベンチマークだが、C2型 D→P interface の証拠とはまだ区別すべき。**

**Surgical phase and instrument recognition: how to identify appropriate dataset splits**

- 著者／年／題名／掲載先: 2024／*Surgical phase and instrument recognition: how to identify appropriate dataset splits*／International Journal of Computer Assisted Radiology and Surgery、査読つき。DOI **10.1007/s11548-024-03063-9**。 citeturn24view2
- 読んだ範囲: 本文。
- 方向: 六、七。
- 視点: 腹腔鏡。
- ドメイン: 低侵襲手術。
- 課題の形: Cholec80 の phase/instrument recognition で、train/validation/test の動画分割自体が workflow、phase、instrument distributions をどう変えるかを分析。 citeturn24view2
- 推論の規約: 特定モデルのonline/offline比較ではなく evaluation methodology。
- データ規模: Cholec80。
- モデルの状態: 該当なし。
- 系統: split auditing／data leakage・distribution auditing。
- 現役度: 方法論論文なのでランキング分類は**不明**。
- 少数動画／online／一人称: 少数動画の分割問題という意味でC2に近い。
- 何と何を比べた差か: Cholec80 の異なる慣用 split を、phase/instrument の存在・分布・workflow variation の観点から比較。
- 効果量: 本調査で安全に引用できる具体例として、40/8/32 split は全phaseとsingle instrumentsが各setに存在し分布も比較的近い一方、**Calot triangle dissectionから開始する surgeries がtrain側にのみ存在する**という workflow偏りが残る。 citeturn25view0
- 符号: 特定手法の改善/悪化ではなく、「分割だけで評価条件が変わる」という方法論的negative evidence。
- 条件依存: validation をどこから切り出すかによって phase duration、transition、instrument co-occurrence の分布も変わり得る。 citeturn24view2
- seed／検定: モデルseedの問題ではない。
- 独立採用: 今回追跡せず。
- コード・ライセンス: open-access article。関連コードは未確認。
- 追加注釈: 不要。
- pretraining overlap: 主題外。
- 一行の要点: **15本CVのC2では、foldを固定し動画単位で完全分離すること自体が実験要因であり、frame-level random split は比較対象にならない。**

**Surgformer: Surgical Transformer with Hierarchical Temporal Attention for Surgical Phase Recognition**

- 著者／年／題名／掲載先: Shu Yang, Luyang Luo, Qiong Wang, Hao Chen／2024／*Surgformer: Surgical Transformer with Hierarchical Temporal Attention for Surgical Phase Recognition*／arXiv preprint。査読採択先は今回確認したarXiv書誌では不明。arXiv: **2408.03867**。 citeturn24view3
- 読んだ範囲: 要旨。
- 方向: 二。問い三・五の**強い recipient 候補を考えるための隣接文献**。
- 視点: 内視鏡・腹腔鏡。
- ドメイン: 低侵襲手術。
- 課題の形: sparse frames と hierarchical temporal attention で surgical phase recognition。
- 推論の規約: target-frame-centric temporal context とあるが、未来フレームを含むかを要旨だけでは判定できず**不明**。 citeturn24view3
- データ規模: 要旨には二つの benchmark とだけあり、ここでは不明。
- モデルの状態: end-to-end surgical transformer。凍結interface方式ではない。
- 系統: strong visual temporal recipient。
- 現役度: peer-reviewed statusを今回確認できないため**不明**。
- object/tool signal: 要旨に explicit instrument/object signal はない。 citeturn24view3
- 効果量: 本文表未確認なので書かない。
- seed／検定: 不明。
- コード: arXivが code release を記載。ライセンス未確認。 citeturn24view3
- 一行の要点: **2024以降の強い phase recipient を考えるとき、visual temporal backbone 自体が強くなっており、object signal の追加効果はこの強さを固定して測る必要がある。**

**FiLM: Visual Reasoning with a General Conditioning Layer**

- 著者／年／題名／掲載先: Ethan Perez et al.／2018／*FiLM: Visual Reasoning with a General Conditioning Layer*／査読系論文。arXiv: **1709.07871**。 citeturn25academia20
- 読んだ範囲: 要旨。
- 方向: 五。
- 視点／ドメイン: 該当なし／非医療。
- 課題の形: conditioning signal から feature-wise affine parameters を生成し、recipient features を scale/shift する。 citeturn25academia20
- 推論の規約: C2の時間因果条件とは無関係。
- データ規模: CLEVR等。詳細は本記録では省略。
- モデルの状態: original FiLM は「独立二モデルを凍結しinterfaceだけ学習」を検証した論文ではない。
- 系統: 小型 conditioning/gating interface。
- 現役度: 一般概念として確立しているが、ユーザー定義の直近2年benchmark-based分類では**不明**。
- 効果量: original task で高い効果を報告するが、C2への外挿に意味が薄いため数値を転記しない。
- clean ablation／seed／検定: 本文未確認。
- コード・ライセンス: 今回未確認。
- 一行の要点: **C2の「小さな界面」の機構候補としては近いが、実証条件は別物であり、外部 detector cue の有効性そのものの証拠にはならない。**


## 探したが見つからなかったもの

**手術で「凍結D＋凍結P＋その間の小型interfaceだけ学習」**

検索語群は `surgical phase recognition frozen detector frozen phase model adapter`, `instrument detection phase recognition gate frozen`, `surgical tool output phase model lightweight fusion`, `MICCAI IPCAI surgical phase instrument context`。手術側で実在確認した関連候補9件を照合したが、**DとPを独立に学習・凍結し、Dの同時刻出力だけを小型interface経由でPに入れ、interfaceだけ学習する**という全条件を同時に満たす研究は今回確認できなかった。

見つかった近似物は、EndoNetの共同学習、Digital-Twin/scene representation 系、PhaKIRの統一multi-task benchmark、VISTAのfrozen temporal branchである。ただし、これらはそれぞれ「共同学習」「scene representation自体を学習」「benchmarkとして三課題を同居」「片側だけ明示的にfrozen」であり、C2の介入とは別である。 citeturn24view1turn22search10

**同じ detector signal を弱い phase model と強い phase model の両方に足す手術実験**

検索語群は `same instrument signal weak strong phase recognition backbone`, `surgical phase object fusion backbone ablation`, `tool signal phase recognition ResNet transformer comparison`。上記手術候補9件の中では、**同一のD出力、同一split、同一interfaceを固定し、受け取り側Pだけ弱/強に差し替えた比較**は確認できなかった。

非手術では ORViT がかなり近い証拠を与える。MF、MF-L、MF-HRのような強い transformer recipient に object processing を入れた結果を比較しており、EK100では単純STIN/STRG追加の利得が消えるか負になる一方、ORViTでは小さい正の利得が残る。だが detector signal と interface を完全固定した weak-vs-strong recipient 実験ではない。 citeturn21view1turn20view2

**detector の mAP と downstream gain の定量曲線**

検索語群は `object detector accuracy downstream action recognition gain`, `detector mAP action recognition oracle boxes`, `bounding box quality downstream action recognition`, `egocentric detector quality anticipation performance`。非手術候補10件と一般object-centric候補4件を確認した。

確認できたのは、STIN の GT-vs-detection、ORViT の manual-box oracle-vs-detection、Helping Hands の256p-vs640p detector input resolution である。これらは detector quality が downstream に効くことを示すが、**複数精度のDを用意し、各DのmAPを横軸、凍結Pへの増分を縦軸にして相関・飽和点を測る**研究は今回の確認集合では見つからなかった。 citeturn20view5turn21view0turn17view2

EndoNet Fig. 10 は一見この問いに近いが、training video数を変えると detector と shared representation の双方が同時に変わるため、tool Mean AP と phase gain の因果的関係を切り分けた実験ではない。実際、10本では tool側のmulti-task性能が悪く、20本ではphase側だけ改善するなど、単純な「tool accuracyが上がればphaseも比例して上がる」関係ではない。 citeturn9view0

**2024〜2026年の手術phase recognitionで、予測されたinstrument/object信号を明示的にphase入力へ入れる追加文献**

検索語群は `2024 surgical phase recognition instrument object`, `2025 surgical phase tool fusion`, `2026 phase recognition instrument context`, `MICCAI surgical phase instrument`, `Medical Image Analysis phase instrument recognition`。

ユーザー既所持の Digital-Twin-based Scene Representation を除くと、今回2024〜2026で確認した文献では、**strictな「instrument/object prediction output をphase recognizerへ明示入力」**を本文レベルで追加確認できなかった。PhaKIRは phase と instrument localization/segmentation を同じ13本で評価可能にするが、要旨からは「instrument prediction をphase inputとして使った」とは言えない。Surgformerはvisual temporal model、EgoSurgery-Phaseはgaze-guided、SurgVLPはvisual-language representationの系統であり、このstrict criterionとは異なる。 citeturn24view1turn24view3turn24view0turn15search7

したがって問い六について、**strict criterion で確認できた2024–2026の追加一覧は空**である。これは「存在しない」という主張ではなく、今回本文まで確認できた集合において追加実証を確認できなかった、という意味である。

**EgoSurgery の15本の box annotation と21本の phase annotationを同一研究で結ぶ既発表論文**

検索語群は `EgoSurgery tool detection`, `EgoSurgery instrument detection bounding box`, `EgoSurgery open surgery object detection`, `EgoSurgery phase tool`。確認できた査読一次文献は EgoSurgery-Phase で、要旨ではphase recognitionとgazeを扱う。**ユーザーが記述した15本の術具box annotationを使い、tool detector→phase modelを評価する公開論文は今回確認できなかった。** EgoSurgery-Phase 自体は15時間・9 phasesの一人称開放手術データを報告している。 citeturn24view0

**正解tool signalとpredicted tool signalを、強いonline phase modelで比較**

EndoNet には GTBin comparison があり、しかも利得が+0.1〜+0.2 ppと非常に小さいが、現代の大規模pretrained video model、online causal temporal model、frozen interfaceという組合せではない。 citeturn6view0

STIN/ORViTにはGT-box oracle gapがあるが、手術ではない。したがって **GT tool boxes / GT tool-presence / predicted boxes / null signalを同じ強いonline surgical Pで比較する条件**は今回確認できなかった。

**種「STLT」「SViT」**

`STLT egocentric action recognition`, `SViT object hand video egocentric`, `STLT action anticipation object`, `SViT egocentric object transformer` を探索したが、今回の問いで意図された手法を一意に同定できなかった。同名・類似略称との衝突があり、実在確認できない名称を文献として補完することは避けた。この二つについては「ID不明」として架空の書誌を作るのではなく、**種の解決自体が未完了**と記録する。


## 未検証の組み合わせ

ここでの「未検証」は「誰も行っていない」という意味ではなく、**今回実在・本文確認した文献集合を並べたとき、その条件を同時に満たす測定を確認できなかった**という意味である。

**凍結された検出器と凍結されたphase modelの間だけを学習する条件。** RULSTM は detector feature extraction が固定されても temporal recipient を学習する。STIN/ORViT は recipient 自体を学習・fine-tuneする。Helping Hands は強い visual backbone を固定する点が近いが、object detector output は推論時 input ではなくtraining supervisionである。VISTA は V-JEPA 2.1 branch が frozen だが detector 側と fusion heads の凍結範囲が要旨だけではC2と一致しない。 citeturn3view0turn21view0turn17view2turn22search10

**同じD出力を、弱いPと強いPへ一切変更せず入れる条件。** ORViTは「recipientが強くなると単純object fusionが0または負になり得る」という近い証拠を持つが、object module自体もrecipient architectureに統合されるため、C2の同一interface比較とは異なる。 citeturn20view2turn21view1

**Dの品質を連続的に変えて downstream dose–response を測る条件。** STINは GT と detection の二点、ORViTも detector と manual box oracle の二点、Helping Handsは detector入力解像度の二水準である。少なくとも今回の集合では、mAPを複数水準に制御したdose–response curveはない。 citeturn20view5turn21view0turn17view2

**tool class confidenceだけ、box geometryだけ、RoI appearanceだけ、hand-tool relationだけを同じC2 interfaceで比較する条件。** RULSTMは主にclass-confidence bag、STINはgeometry、ORViTはgeometry+appearance、Ego-OMGはcontact/stateを使うが、データ・backbone・taskが異なるため、どのsignal typeが効くかを横断的に比較できない。 citeturn3view0turn20view4turn19view0turn22search1

**強いrecipientにおける predicted-vs-GT object oracle gap。** ORViT には比較的強い transformer と GT-box oracle の結果があるが offline general action recognition である。手術online phase recognitionでは未確認である。 citeturn21view0

**少数動画、一人称、online、detector output の四条件の交点。** RULSTM/VISTAは一人称・causal・object-awareだが大規模egocentric benchmark、EgoSurgeryは一人称・少数だが tool-output fusionではなく、PhaKIRは少数・surgeryだが内視鏡で strict D→P fusion の実証を要旨から確認できない。 citeturn3view0turn22search10turn24view0turn24view1

**phase側が既にtool informationを潜在的に持つ場合の「追加情報量」の測定。** EndoNet+GTBin がほぼ改善しないことと、ORViTの強いbaseline上でSTIN/STRGが差なし・悪化することは、「明示object cueが既存visual representationと冗長になる」可能性を示す。しかし、conditional mutual informationやcue deletionを用いて冗長性を直接測る実験は今回確認していない。 citeturn6view0turn20view2

**detectorのcalibration品質とdownstream gain。** RULSTMのbag-of-objectsやC2のclass confidenceは、mAPが同じでもscore calibrationが違えばinterfaceへの入力分布が変わる。今回確認した文献では detection mAP と confidence calibration を分離して downstream phase/action gain を測った結果は見つからなかった。

**時間リークを厳密に除いたobject tracking。** ORViTはSORTを使い、論文のforward tracker自体は逐次的だが、一般に precomputed tracklets、clip-centered video features、bidirectional temporal encoderをそのままC2へ移すと未来情報を含み得る。ORViTのstandard recognitionは実際に複数clipを用いるoffline evaluationなので、C2のonline規約とは分離すべきである。 citeturn20view0turn21view2


## 検索記録

検索日は **2026年10月18日（Asia/Tokyo）**。以下の件数は検索サイトの推定ヒット数ではなく、重複を除き、実在と問いとの関連を個別確認した文献数である。

| 方向 | 主な検索語・追跡経路 | 実在確認した関連件数 | 主な結果 |
|---|---|---:|---|
| 一：EgoSurgery・一人称開放手術 | `EgoSurgery open surgery phase recognition first person`; `EgoSurgery tool detection`; `EgoSurgery instrument bounding box` | 1 | EgoSurgery-Phase を確認。公開D→P fusionは確認できず |
| 二：手術一般 | `surgical phase recognition instrument tool object 2024 2025 2026`; `PhaKIR`; `Cholec80 split instrument phase`; MICCAI/MedIA/TMI 系 | 9 | PhaKIR、EgoSurgery-Phase、Surgformer、split分析等。strict tool-output→phaseは極少 |
| 三：一人称非手術 | `egocentric object detection action anticipation`; `hand object contact action recognition`; `EPIC-KITCHENS object anticipation`; `Helping Hands`; `StillFast`; `VISTA`; `object-centric long-term anticipation` | 10 | RULSTM、Helping Hands、Ego-OMG/contact、StillFast、VISTA等 |
| 四：一般映像 | **医療語なし**で `object boxes action recognition transformer detected boxes ground truth`; `SomethingElse STIN`; `object-region video transformer` | 4 | STIN/ORViTがGT-vs-detection、strong-baseline negative evidenceを提供 |
| 五：機構一般 | **医療語なし**で `conditioning gate pretrained frozen model`; `FiLM conditioning`; `object fusion pretrained video model` | 3 | FiLM等を確認。ただしexact frozen-D/frozen-P/interface-onlyは0 |
| 六：方法論 | `surgical phase instrument dataset split`; `video cross validation leakage`; `Cholec80 appropriate dataset splits` | 2 | Kostiuchik et al.、PhaKIR challenge methodology |
| 七：negative result | **医療語なし**で `ground truth vs detected boxes action recognition`; `object cues strong backbone negative`; `detector quality downstream action recognition` に加え手術検索 | 5 | EndoNet small-data reversal/GTBin、STIN oracle gap、ORViT zero/negative fusion、Helping Hands box quality、Tateno shortcut diagnosis |

方向三では、種から **RULSTM、Helping Hands、ORViT、EPIC-KITCHENS** の系統を確認しただけでなく、種に無かった **Ego-OMG/contact representations、Object-centric Video Representation for Long-term Action Anticipation、StillFast、VISTA、2026年のcue-isolation研究**まで追った。 citeturn22search1turn25academia21turn22search2turn22search10turn23search3

方向四では STIN から ORViT へ引用を追い、さらに ORViT の表で STIN/STRG を強い transformer backbone に付加したときに効果が消える条件を確認した。この経路が、今回の問い三に対する最も直接的なnegative evidenceだった。 citeturn19view0turn21view1

順位表・benchmarkからの逆引きとしては Ego4D STA の StillFast 系を2026年VISTAまで追い、手術では PhaKIR challenge report を確認した。VISTA は StillFast-style design に frozen V-JEPA 2.1 branch と Faster R-CNN proposals を組み合わせているため、C2の「強い受け取り側に object signal を足す」という問いに近い2026年の事例である。ただし clean ablation を本文確認できていないので、利得量の証拠には採用していない。 citeturn22search10turn24view1

2024〜2026の主要venue横断については、本回答用に一次資料を直接確認できた範囲が **MICCAI、CVPR/WACV 系、Medical Image Analysis、TMI 系**に偏った。IPCAI、ICCV、ECCV、NeurIPS、ICLRについては、今回取得できた一次資料の中で strict D→P 条件に該当する2024〜2026論文を本文確認できなかった。この点は「該当論文が存在しない」というnegative resultではなく、**今回の検索・取得範囲の未完了部分**として扱う。


## 解釈と提案

以下は文献に書かれた事実ではなく、上の証拠を C2 の実験へ写像した解釈である。

### C2で最初に切り分けるべき仮説

この文献集合からは、「tool signal が役立つか」という一つの問いではなく、少なくとも四つの仮説を分ける必要がある。

第一は、**Dがphaseに追加情報を持つか**である。EndoNet+GTBinがほとんど増えなかった事実は、RGB phase representation が既にtool情報を内包している場合、正解tool cueさえ冗長になり得ることを示す。 citeturn6view0

第二は、**Dの誤差がその追加情報を壊していないか**である。STIN の51.4→37.2、ORViT の detector-vs-oracle gain gap は、この要因が十分大きくなり得ることを示す。 citeturn20view5turn21view0

第三は、**情報はあるが interface が使えていないだけか**である。ORViTでは MF+RoIAlign が baselineを下回る一方、object regions を早い層から繰り返し注入する ORViT は大きく改善した。同じboxesでも入れ方によって符号が変わる。 citeturn21view0

第四は、**recipient が強くなると追加情報が冗長になるか**である。EK100では強い MF-HR に STRG/STIN を足すと0または負で、ORViTでも action gainは+1.2 pp、nounは+0.2 ppだった。したがって「弱いPで改善したから強いPでも改善する」という外挿は避けるべきである。 citeturn20view2

この四つを別々に測らないと、「C2が効かなかった」という一結果から、Dが悪いのか、Pが既に知っているのか、interfaceが悪いのか、データ数が不足したのかを判別できない。

### 界面の実験単位

本研究設定では、DとPを**foldごとに独立学習して完全凍結**し、その後の interface 学習だけを比較対象にすると、文献で混ざりがちな「object cue の情報」と「backboneを再学習した効果」を切り離せる。

interface の入力はまず、同時刻 \(t\) の D 出力から作る少数の表現を分離して測るのがよい。

一つは **class-confidence only** で、RULSTMのbag-of-objectsに最も近い。二つ目は **class confidence + box geometry** で、STIN型のgeometry情報を加える。三つ目は **hand/toolあるいはtool/tool relation** が構成できる場合の relation features。四つ目は **RoI appearance** だが、これは「相手モデルだけが出した出力」というC2の規約を厳格に解釈すると、D内部featureを渡すことになるため別実験に分けるべきである。RULSTM、STIN、ORViTはこれらを別々の形で使っており、同じ“object signal”ではない。 citeturn3view0turn20view4turn19view0

小型interfaceは concat+MLP だけでなく、**residual conditioning** と **gate** を区別する価値がある。FiLM型なら、Pのfeature \(h_t\) をD由来の \(z_t\) から生成した scale/shift で変調できる。別案として、\(h'_t=h_t+g(z_t)\odot a(z_t)\) のように、D signal が不要なフレームではゼロに近づけられる residual gate にすると、「object cueを強制的に使う」ことと「使えるときだけ使う」ことを分離できる。FiLMは一般conditioningの先例であり、RULSTMのmodality attentionも「場面によってobject branchを下げる」という考え方を支持する。 citeturn25academia20turn3view0

ただし、**gateという機構を使ったこと自体を貢献の根拠にはしない**。上の検索では、手術phase recognitionでC2と同じ frozen-D/frozen-P/gate-only 条件の実証は確認できなかったため、重要なのは機構名ではなく、介入を他の学習効果から分離できることである。

### oracle と negative control

C2では STIN/ORViT の結果を踏まえ、predicted detector output の一本だけで結論を出さない方が識別力が高い。

同一fold、同一凍結P、同一interface architectureで、少なくとも次を区別すると原因を特定しやすい。

**RGB/P-only** は基準。**Pred-D** は実際の detector output。**GT-tool presence** はクラス存在のoracle。**GT boxes** は位置まで含むoracle。**Null-D** は全ゼロ入力で、interfaceのパラメータ増加だけによる効果を見る。**Shuffled-D** は別時刻または別動画のD出力を与え、単なるphase priorやscore distributionだけを学んでいないかを見る。

特に Null-D は ORViT が random/full/null/grid boxes を用いて「architecture変更だけではないか」を検査した発想と対応する。ORViT Table 4(c) では genuine object regions が69.7 top-1なのに対し full/null/grid/random boxes は60%台前半まで落ち、情報の中身が重要であることを示している。 citeturn21view0

GT-vs-Pred gap が大きく、Pred-DがP-onlyと同等なら「仮説自体が失敗」ではなく**detector bottleneck**と読める。GTでも改善しなければ、EndoNet+GTBinのように**Pが既にその情報を持つ／phaseに追加情報がない**可能性が高まる。 citeturn6view0turn20view5

### 弱いPと強いPの比較

問い三と問い五を直接解くには、Dとfoldを固定したまま recipient P だけを二水準以上にする必要がある。

ここでいう「弱い／強い」は parameter数だけで定義せず、**同じ15本CV上のP-only性能**で定義する方が解釈しやすい。例えば、小規模CNN+causal temporal model と、大規模pretrained video encoder+causal temporal headを用い、それぞれに完全に同じD signal、同じinterface parameter budget、同じtraining foldsを与える。

見る量は絶対Jaccardだけでなく、

\[
\Delta_P
=
\mathrm{Jaccard}(P+D)-\mathrm{Jaccard}(P)
\]

の fold-wise paired difference である。強いPで \(\Delta_P\) が縮むのか、符号が残るのかを測れば、ORViTで観察された「strong backboneでは単純object moduleの利得が消える」という現象が一人称開放手術にも当てはまるかを直接検査できる。 citeturn20view2turn21view1

frame accuracy は co-primary のまま併記するが、C2の主問いには macro Jaccard の方が、長いmajority phaseだけの改善に引きずられにくい。ただし **fold内に存在しないphaseをmacro Jaccardでどう扱うか**を事前に固定する必要がある。15本のような小標本では、この定義差だけで平均値が変わり得る。

### detector quality と downstream gain の測り方

文献で最も欠けていたのが問い四である。したがって C2では、単に「DのmAPも報告する」のではなく、**D-quality と P-gain を同じfold単位で対応させる**と識別力が上がる。

一つの方法は、foldごとのD mAPと \(\Delta_P\) を対応させること。ただし15本ではサンプル点が少なく、fold-level相関だけで強い結論を出しにくい。

もう一つは同一Dの出力を人工的に劣化させる方法である。confidence noise、box jitter、false-positive追加、低confidence detectionのdrop、GTとの混合などで品質を段階的に変え、**PもDも再学習せず、interfaceの条件だけを揃えて**dose–responseを見る。STIN/ORViTのGT-vs-detected二点を、複数水準に拡張した設計になる。 citeturn20view5turn21view0

ここではmAPだけでなく、**tool-presence recall、false-positive rate、confidence calibration**も保持する必要がある。RULSTM型のinterfaceが confidenceそのものを使う場合、同じmAPでもscore calibrationが変われば入力信号の意味が変わるからである。

### online 性と情報漏れ

C2で最も注意すべき未明示前提は、**「Pが未来を見ない」だけでは online 条件は成立しない**ことである。

Dがsingle-frame detectorなら原理的には同時刻までだが、D出力を作る前処理に bidirectional tracking、future-frame smoothing、centered clip feature、offline temporal NMS が入れば、interface経由で未来情報がPへ漏れる。ORViTの standard recognition はcentered/offline clip aggregationを用いるため、そのままC2の先例とは扱えない。 citeturn21view2

したがって評価時刻 \(t\) の界面入力を

\[
z_t=f_D(x_{\le t})
\]

と明文化し、実装上はより強く、single-frame D なら

\[
z_t=f_D(x_t)
\]

に制約するのが明瞭である。trackingを使う場合も forward-only tracker だけに限定し、後処理で future detections によるtrack補間をしない。

もう一つの漏れは**fold外学習**である。15本のCVでは、held-out video の boxes をDのfine-tuning、threshold選択、class calibration、interface early stopping のどこにも使わない必要がある。Kostiuchik et al. が示すように、手術動画はphaseやinstrumentの単純なクラス存在だけでなく workflow pattern までsplit間で偏り得る。 citeturn24view2turn25view0

大規模事前学習済みPを使う場合には、さらにそのpretraining corpusに EgoSurgery が含まれていないことを確認する。公開前の臨床映像であれば通常は重複可能性が低いが、これは推測で済ませずモデルカード・pretraining data記述に基づいて記録する項目にする。

### 15本の交差検証での統計単位

C2の最終推論単位は**frameではなくvideo**に置く方が設計と整合する。数十万frameを独立サンプルとして扱うと、同じ手術内の強い時間相関のため不当に小さい不確実性を得る。

各foldで P-only と P+D の macro Jaccard／frame accuracy を同じheld-out videos上で計算し、video単位またはfold単位の paired difference を保存する。平均値だけでなく全foldの符号を示せば、「一部の手術でだけ大きく改善した」場合も見える。

少数foldで通常の独立標本t検定だけに依存するより、**paired differencesそのもの、中央値、範囲または信頼区間**を主に示し、必要ならvideo単位のpaired permutationやbootstrapを補助的に使う設計が解釈しやすい。ただしfoldのtrain setsは互いに重複するので、foldを完全独立実験とみなす解釈は避ける。

official split は、ユーザーの設定どおり既発表値との橋渡しだけに残し、主要仮説の結論を15本CVから出す方が、Kostiuchik et al. が指摘する固定split固有のworkflow偏りと、C2の少数動画条件を分離しやすい。 citeturn24view2

### C2で明示すると文献上の空白を直接測れる比較表

最終的な論文表では、各 recipient P について **P-only / +Pred-D / +GT-presence / +GT-box / +Null-D / +Shuffled-D** を同じfoldで並べ、その横にDのmAPを置く構成が、今回の五つの問いを最も直接的に分解する。

そこに弱いPと強いPを二ブロックとして置けば、「object cueが効くか」「detector errorが律速か」「strong recipientで利得が消えるか」「単なるparameter増加か」を一つの実験系で別々に読める。

文献から予想される符号は一方向ではない。EndoNetでは少データ時にmulti-task tool recognitionが悪化し、GTBinを加えてもphaseはほぼ変わらない。STINではGTからdetectionに替えると大きく落ちる。ORViTでは強いrecipientに単純object moduleを足すと差なし・悪化がある一方、適切なfusionでは小さい正の利得が残る。Helping Handsでは強いpretrained representationでもobject-aware supervisionの正の利得が残る。したがって C2 で重要なのは「改善するはず」という片側仮説ではなく、**改善・差なし・悪化の三符号を同等に観測可能にした設計**である。 citeturn9view0turn6view0turn20view5turn20view2turn17view0
# EgoSurgery における online 工程認識・行動分割の時間モデル：系統、実証結果、評価規約、再現性の文献調査

## Executive Summary

### 結論

EgoSurgery-Phase は、公開された実開放手術の工程認識データとして極めて小規模で、原論文の v1 では **21動画、約15時間、9工程、14/2/5 の train/validation/test、27,694 annotated frames、0.5 fps** である。ところが、後の arXiv 版には「20 videos」とする記述と、合計21本になる 14/2/5 split が同居しており、データ数の版間不整合がある。後続の EgoSurgery-HTS は再び 21 videos と記述しているため、少なくとも報告時には使用した版を固定して記載すべきである。citeturn2view0turn3view0turn21search10

この条件で最も重要な文献上の結論は、「TeCNO の次に Transformer を試す」という一次元の比較では不十分だということである。2024–2026 年には、**因果 TCN、LSTM/GRU、局所 Transformer、長時間 Transformer、明示的 memory、multi-scale/hierarchical attention、SSM/Mamba、phase-proposal 型、progress/task-graph 型、video-language 型**がそれぞれ別系統として存在している。特に SSM/Mamba と明示的 memory は、前回の候補から抜けていた重要系統である。citeturn15view0turn19academia30turn20view0turn21search0turn21search4

ただし、**Mamba と書いてあるだけでは online ではない**。SR-Mamba は bidirectional Mamba decoder を明記しており、未来を利用するため strict-online 候補ではない。これに対して HID-SSM は causal version を持ち、著者は full-video online phase recognition と位置付ける。2026年にはさらに online を明示した PhaseMamba が MICCAI に現れている。したがって EgoSurgery で検証すべき SSM は「SR-Mamba をそのまま移植」ではなく、**forward/selective SSM を causal に実装したもの**である。citeturn21search0turn20view0turn21search20

少数動画での最も直接的な online 証拠は、非手術一人称の GTEA を含む OnlineTAS と ProTAS から来る。OnlineTAS は causal TCN に明示的な短期・長期 memory を加えると、GTEA の strict-online で **Acc 74.4→75.8、F1@50 57.2→60.3** と改善した一方、50Salads では **Acc 75.2→79.1、Edit 19.6→29.0、F1@50 19.6→28.3** と segmental metric の改善がより大きかった（Table 8）。つまり、**小規模一人称では長期 memory の効果は正だが、フレーム精度への上積みは数ポイント程度で、主な利益は過分割の抑制に出る**。citeturn16view2

一方、EgoSurgery 自体では「時間モデル差」と「backbone/表現差」が十分に切り分けられていない。原論文 Table 1 は AlexNet、ResNet-50、InceptionV3、ViT-S と時間モデルを同時に変えており、TeCNO 対 Trans-SVNet 対 GGMAE の差を時間モデルだけの差と解釈できない。Table 2 は ViT-S を固定して事前学習だけを変え、Jaccard が **27.1–33.9、幅6.8点**動く。さらに SurgMotion は共通の frozen-backbone + attentive probing 条件で EgoSurgery の表現を比較し、Jaccard が **5.17–42.95、幅37.78点**、F1 が **7.33–50.72、幅43.39点**動いている。これは、少なくともその probe 設定では**時間 head を議論する前にフレーム/clip 表現だけで極めて大きな差が生じ得る**ことを示す。ただし SurgMotion の pretraining corpus 自体に EgoSurgery が含まれるため、下流 test 部分を事前学習から除外したことを本文で確認できず、純粋な外部事前学習比較としては汚染リスクを排除できない。citeturn2view0turn11view0turn11view1

offline と online の差はフレーム accuracy より **segmental consistency** に大きく出る。OnlineTAS が同一 ASFormer を causal 化した Appendix Table 12 では、50Salads で offline→strict-online にすると **Acc 85.6→77.5（−8.1点）**なのに対し、**Edit 79.6→29.1（−50.5点）、F1@50 76.0→28.6（−47.4点）**まで落ちる。Breakfast でも F1@50 は **57.4→20.2（−37.2点）**である。online 化で最初に壊れるのは必ずしも frame accuracy ではなく、境界と連続性である。citeturn16view3

したがって EgoSurgery で次に必要なのは巨大な architecture sweep ではなく、**同一 backbone・同一特徴・同一 split・同一 causal convention のまま、TeCNO / causal Transformer / memory / forward-SSM を差し替える対照実験**である。21本しかない以上、これに seed と surgeon/procedure-aware split を加えなければ、1–3点程度の「改善」は architecture 効果なのか split/seed 効果なのか判別できない。

### 問いごとの最終回答

| 問い | 調査から得られた回答 |
|---|---|
| Q1 時間モデルの全系統 | 因果TCN、RNN、局所Transformer、長時間Transformer、explicit memory、multi-scale/hierarchical、SSM/Mamba、phase localization/proposal、progress/task graph、language/VLM、structured transition/post-processing、end-to-end spatial-temporal の少なくとも12系統。 |
| Q2 少数動画で何が効くか | GTEA 28本では memory の上積みは正だが小～中程度。EgoSurgery 21本では representation/pretraining 差だけで Jaccard が数点～数十点動き得る。SSM の EgoSurgery strict-online 対照実験は未報告。citeturn16view2turn2view0turn11view1 |
| Q3 backbone vs 時間モデル | EgoSurgery 原論文 Table 1 は交絡。Table 2 と SurgMotion Table 3 は representation の寄与が大きいことを示す。OnlineTAS は逆に I3D feature を固定して temporal architecture の効果を示す。両者を同一 EgoSurgery split で同時に factorial に切った研究は見つからなかった。citeturn2view0turn11view1turn16view2 |
| Q4 EgoSurgery/open surgery 全報告値 | 本調査で一次本文の表まで確認できた EgoSurgery phase 数値は、EgoSurgery-Phase Table 1/2 と SurgMotion Table 3。下に全行を転記する。EgoSurgery 原論文自身は世界初の公開 real-open-surgery phase dataset と位置付ける。citeturn19academia31turn11view1 |
| Q5 非手術一人称 online | ProTAS と OnlineTAS/GTEA が最も直接的。progress、task graph、causalization、explicit memory が有効。Assembly101/Ego4D/Ego-Exo4D/HoloAssist は重要な transfer source だが、標準 benchmark の多くは strict-online dense segmentation ではない。citeturn17search2turn16view0turn21search3turn21search15 |
| Q6 loss が効かなかった報告 | smoothing/boundary/class weighting **そのものだけを変えた否定的 surgical ablation は確認できなかった**。ただし OnlineTAS の境界 post-processing は segment 指標を大幅改善する反面 Acc を悪化させ、目的指標依存のトレードオフを明示する。EgoSurgery の class resampling には無処置対照がない。citeturn16view2turn2view0 |
| Q7 offline→online | ASFormer 同一系統で F1@50 が GTEA −17.2、50Salads −47.4、Breakfast −37.2点。accuracy の低下より境界指標の低下がはるかに大きい。citeturn16view3 |
| Q8 評価規約 | relaxed boundary、split、video-wise/class-wise averaging、online/semi-online、原著値/再実装値が混在する。Metrics Matter はこれらを直接比較不可と警告。TMRNet 公開評価コードは relaxed-boundary mode を明記する。citeturn13search1turn5search10 |
| Q9 区間切れ | 実動画の不連続区間を concat した時の causal TCN/RNN/Transformer/SSM の影響を EgoSurgery 上で測った論文は見つからない。OnlineTAS は sequence 開始時に memory を初期化し clip/window を明示的に管理するが、人工的な gap の影響は未検証。citeturn16view0 |
| Q10 計算環境 | GPU/CUDA 環境を変えた controlled reproducibility study は見つからなかった。多くの論文は hardware を記載する一方 seed 分散を報告しない。EgoSurgery GGMAE は 3×TITAN RTX、SurgMotion は 4×H800 を使用するが、hardware を変えた結果差は測定していない。citeturn3view1turn11view0 |

## 系統表

ここで「現役度」は依頼された定義に従う。ただし **benchmark を明記して評価する**。一つの手法が、例えば Cholec80 では定番でも EgoSurgery では未検証、というケースを分けた。

| 系統 | 代表的文献・手法 | strict-online 性 | 少数動画・一人称での直接証拠 | 現役度 | 下の詳細記録 |
|---|---|---|---|---|---:|
| **因果的時間畳み込み** | TeCNO, causal MS-TCN, OnlineTAS causal TCN | 高い。left-causal convolution が明確 | EgoSurgery 21本で TeCNO 再評価あり。GTEA 28本で causal TCN online あり | **定番の基準**：TeCNO は2024–25の比較でも継続使用。一般 online TAS でも causal TCN が強い基準。citeturn20view0turn16view2 | 2 |
| **再帰型** | PhaseLSTM, SV-RCNet, LSTM/GRU, MiniROAD | 高い | EgoSurgery の PhaseLSTM、GTEA/50Salads の OnlineTAS GRU | **定番の基準**。単独 LSTM は新規 SOTA というより軽量基準。GRU は memory と組み合わせて現役。citeturn20view0turn16view1 | 1 |
| **局所 Transformer 集約** | Trans-SVNet, SKiT, Surgformer | causal mask を入れれば可能だが、各論文で要確認 | EgoSurgery に Trans-SVNet 再実装値 | Trans-SVNet は **定番の基準**。SKiT/Surgformer は surgical benchmark では比較対象として残るが EgoSurgery strict-online は未検証。citeturn2view0turn21search23 | 1 |
| **長時間文脈 Transformer** | LoViT, LSTR, E2E-LOAD, MAT | LSTR/online 系は可。offline Transformer は不可 | LSTR は一般 TAS に再実装すると causal TCN より悪い | LSTR は OAD の **定番の基準**。LoViT は surgical phase の強い既存基準。一般 TAS にそのまま LSTR を移すのは不適合との負の証拠。citeturn15view0turn16view2turn4search15 | 1 |
| **状態空間モデル / Mamba** | SR-Mamba, SPRMamba, HID-SSM, PhaseMamba, SurgicalMamba | 実装依存。Mamba 本体は causal でも bidirectional 化すれば offline | EgoSurgery strict-online は **ゼロ** | **新興**。2024–26に急増。SR-Mamba は bidirectional なので今回の online 候補としてはそのまま使えない。HID-SSM/PhaseMamba が最も直接的。citeturn21search0turn21search4turn20view0turn21search20 | 4 |
| **明示的記憶機構** | TMRNet, LSTR, MAT, OnlineTAS, MoSFormer | online 向き | GTEA 28本で strict-online 改善 | **SOTA級/定番**：OnlineTAS は NeurIPS 2024 の online TAS で上位。TMRNet/LSTR は基準として継続。citeturn16view2turn20view0 | 3 |
| **多尺度 / 階層時間モデル** | MS-ASCT, LoViT, Surgformer, HID-SSM | causal variant なら可 | 手術では Cholec80、非手術では GTEA。EgoSurgery 未検証 | **定番～新興**。MS-ASCT は明示的 causal multi-scale attention、HID-SSM は local/global SSM。citeturn19academia30turn20view0 | 2 |
| **progress / task graph / 手順事前知識** | ProTAS | strict-online | GTEA・EgoProceL・EgoPER の一人称手順動画 | **定番の基準（egocentric online procedure）**。CVPR 2024 後も後続文献で引用。citeturn17search2turn18search24 | 1 |
| **言語併用 / video-language** | EgoVLP, SurgVLP, TI-PREGO, TOAD, SurgAtlas | 手法次第 | online mistake/OAD では利用例あり。EgoSurgery phase の strict-online head と組み合わせた対照実験なし | **新興～定番**。representation/semantic prior として活発だが、工程分割の causal evidence はまだ弱い。citeturn14search5turn18search17turn19academia32 | 0 |
| **phase proposal / temporal localization** | SurgPLAN, SurgPLAN++ | online mode あり | 一人称/open surgery 未検証 | **新興/不明**。frame-wise classifier を phase proposal に置換する別系統。citeturn19academia29turn21view6 | 1 |
| **境界・structured transition・post-processing** | MS-TCN smoothing loss, OnlineTAS post-processing, CRF/HMM 系 | causal 実装可能 | GTEA/50Salads で非常に強い segmental 改善 | **定番の補助手法**。時間 encoder の代替ではなく prediction regularizer。citeturn15view0turn16view2 | 2 |
| **表現学習 / end-to-end spatial-temporal** | EndoNet, SelfSupSurg, GGMAE, SurgMAE, SurgPETL, SurgMotion, SR-Mamba single-step | temporal head と独立 | EgoSurgery では非常に大きい影響 | **現役**。EgoSurgery では時間 head の差より先に統制すべき交絡因子。citeturn2view0turn11view1turn21search0 | 3 |
| **視線・物体・motion/multimodal conditioning** | GGMAE gaze, Ego-Exo, EgoSurgery-Tool/HTS, Ego4D 系 | temporal model とは直交 | EgoSurgery gaze-guided masking に直接証拠 | **新興～定番**。一人称では特に重要。citeturn19academia31turn21search21turn21search24 | 1 |

既存リストの **EndoNet, TeCNO, Trans-SVNet, LoViT, SelfSupSurg, GGMAE, SurgMAE, SurgPETL, MS-TCN, ASFormer, LSTR, EgoVLP, Ego-Exo, EGTEA Gaze+, EPIC-KITCHENS** は上表に位置付けた。これらは依頼通り個別の詳細記録を重複して作っていない。

種リストについては、**SKiT, Surgformer, SR-Mamba, SPRMamba, MS-ASCT, HID-SSM, TMRNet, SurgMotion, Assembly101, Ego4D, Ego-Exo4D, HoloAssist, EgoProceL** の実在を確認できた範囲を採用した。とくに SR-Mamba、SPRMamba、HID-SSM は名前が似ていても causality が同じではない。SR-Mamba は bidirectional decoder を明記するため、この研究の strict-online 条件では除外または causal 改変が必要である。citeturn21search0turn21search4turn20view0

### EgoSurgery-Phase で一次本文の表まで確認できた全報告値

原論文 Table 1 は、時間モデルだけでなく backbone も同時に異なる。したがって以下は**ランキングではあっても temporal-head の純粋な比較ではない**。citeturn2view0

| 手法 | Backbone | Precision | Recall | Jaccard | 数値の出所 | online 規約 |
|---|---|---:|---:|---:|---|---|
| PhaseLSTM | AlexNet | 36.3 | 33.1 | 21.9 | EgoSurgery-Phase Table 1、著者側再評価 | strict causal の明記を確認できず |
| PhaseNet | AlexNet | 37.0 | 25.7 | 19.7 | 同上 | 不明 |
| TeCNO | ResNet-50 | 47.7 | 39.2 | 27.3 | 同上 | architecture 自体は causal。ただし当該表の評価規約の明記は不十分 |
| Trans-SVNet | ResNet-50 | 41.8 | 35.9 | 23.1 | 同上 | 不明 |
| NETE | InceptionV3 | 43.7 | 35.2 | 27.5 | 同上 | 不明 |
| GGMAE | ViT-S | **51.7** | **45.6** | **33.9** | 同上 | 10-frame clip を使用。frame t に対する strict past-only 性は不明 |

同論文 Table 2 は backbone を **ViT-S に固定**した pretraining 比較であり、Q3 の切り分けには Table 1 より有用である。Jaccard は scratch 27.1、VideoMAE 29.8、VideoMAE V2 30.8、SurgMAE 27.8、GGMAE 33.9 で、scratch→GGMAE は **+6.8点**、VideoMAE V2→GGMAE は **+3.1点**である。citeturn2view0

| ViT-S の初期化 | Precision | Recall | Jaccard | 差の意味 |
|---|---:|---:|---:|---|
| supervised from scratch | 47.9 | 31.6 | 27.1 | 基準 |
| VideoMAE | 49.3 | 41.6 | 29.8 | scratch 比 +2.7 Jaccard |
| VideoMAE V2 | **54.2** | 43.2 | 30.8 | scratch 比 +3.7 |
| SurgMAE | 52.2 | 41.9 | 27.8 | scratch 比 +0.7 |
| GGMAE | 51.7 | **45.6** | **33.9** | scratch 比 +6.8、VideoMAEv2 比 +3.1 |

GGMAE の Table 3 では masking の選択自体にも無視できない幅がある。同じ mask ratio 0.90 で random 30.6、tube 29.8、gaze-guided 33.9 Jaccard であり、gaze-guided は random 比 **+3.3点**、tube 比 **+4.1点**。一方 mask ratio を 0.90 から 0.95 にすると 33.9→31.2、temperature τ を 0.50 から 0.25 にすると 33.9→27.2 と悪化する。これは小規模データでは「新要素を入れれば常に改善」ではないことを示す明確な負の ablation である。ただし損失関数の負の結果ではない。citeturn2view0

2026年の SurgMotion Table 3 は、各 foundation model を frozen にして共通の attentive probing protocol を用いたため、**表現差を比較的よく切り出した表**である。citeturn11view1

| Frozen representation | Accuracy | F1 | Jaccard | 数値の性質 |
|---|---:|---:|---:|---|
| DINOv3-L | 75.37 | 32.43 | 26.03 | 共通 probe による再評価 |
| DINOv3-H | 70.08 | 36.34 | 29.03 | 同上 |
| VideoMAE-L | 64.52 | 26.84 | 19.82 | 同上 |
| VideoMAE-G | 62.25 | 20.40 | 16.13 | 同上 |
| EndoViT | 32.32 | 9.29 | 6.31 | 同上 |
| GastroNet | 48.12 | 16.08 | 12.87 | 同上 |
| GSViT | 35.74 | 7.33 | 5.17 | 同上 |
| EndoMamba | 53.30 | 13.90 | 10.32 | 同上 |
| EndoSSL | 49.78 | 12.04 | 8.86 | 同上 |
| EndoFM | 54.85 | 36.13 | 26.42 | 同上 |
| SelfSupSurg | 36.03 | 7.38 | 5.22 | 同上 |
| SurgeNetXL | 35.82 | 7.34 | 5.18 | 同上 |
| SurgVLP | 57.44 | 23.26 | 17.46 | 同上 |
| SurgMotion | **75.57** | **50.72** | **42.95** | 同上 |

ただしこの表には重大な注意点がある。SurgMotion の pretraining corpus の一覧には **EgoSurgery 21 videos** が含まれる。本文の取得範囲では EgoSurgery の downstream test frames を pretraining corpus から明示的に除外した記述を確認できなかった。したがって SurgMotion 42.95 Jaccard を、評価データと完全独立な pretraining の数値として扱うことはできない。citeturn11view0turn11view1

## 文献ごとの記録

以下では、既に所持していると明示された文献は重複を避け、今回新たに重要になったものを中心に記録する。

**EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos**

- **[書誌] 著者／年／題名／掲載先／ID:** Ryo Fujii et al.／2024／*EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos*／MICCAI 2024、査読つき／DOI **10.1007/978-3-031-72089-5_18**、arXiv:**2405.19644**。citeturn1view1turn19academia31
- **読んだ範囲:** arXiv HTML 本文、実験表、MICCAI 公式ページ。
- **[近さ] 方向:** 1。
- **視点:** 一人称。
- **ドメイン:** 開放手術。
- **課題の形:** head-mounted camera の映像から9工程をフレーム単位認識。
- **推論の規約:** 論文全体を strict past-only benchmark とする明記は確認できず。TeCNO は causal architecture だが、GGMAE は 10-frame clips を使うため target frame に対する未来利用の有無は不明。citeturn2view0turn3view1
- **データ規模:** v1 は21動画、10 procedure types、約15時間、8 surgeons、9 phases、27,694 annotated frames、0.5 fps、14/2/5 split。後版には20本とする記述と14/2/5が併存。citeturn2view0turn3view0
- **モデルの状態:** Table 1 は各既存モデルを dataset 上で訓練。Table 2 は同一 ViT-S backbone に異なる pretraining。
- **[手法の位置] 系統:** 表現学習＋gaze conditioning。比較相手には RNN/TCN/Transformer。
- **現役度:** **定番の基準（EgoSurgery）**。EgoSurgery の一次 benchmark。
- **ベンチマーク:** EgoSurgery-Phase。
- **少数動画／online／一人称:** 少数動画○、一人称○、strict-online は不明。
- **[証拠] 何と何を比べた差か:** Table 2 は backbone を ViT-S に固定し pretraining を変更。
- **効果量:** GGMAE Jaccard 33.9 vs scratch 27.1 = **+6.8点**、vs VideoMAEv2 30.8 = **+3.1点**。Table 2。citeturn2view0
- **符号:** 改善。
- **符号や大きさが変わる条件:** Table 3 で mask ratio 0.90 が最良、0.95 は −2.7 Jaccard。τ=.50→.25 は −6.7。
- **基準の強さ:** VideoMAEv2/SurgMAE を含む強い pretraining baseline。
- **その要素だけを変えた比較か:** Table 2 は比較的 yes。Table 1 は no、backbone と temporal architecture が交絡。
- **seed／分割／検定:** split は1つ。複数 seed・統計検定は確認できず。
- **著者以外の追試:** SurgMotion が後に EgoSurgery を downstream benchmark として使用。citeturn11view1
- **[実装] コード・重み・ライセンス:** dataset repository は公開。ライセンス詳細は取得範囲では不明。citeturn21search2
- **追加データ:** gaze annotations を利用。
- **事前学習 leakage:** GGMAE 自身について downstream test を pretraining に用いた記載は確認していない。
- **[要点]:** **EgoSurgery の既存表だけでは時間モデル差を切り分けられない。表現学習だけでも Jaccard が6点以上動く。**

**SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos**

- **[書誌]:** 2026／*SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos*／プレプリント／arXiv:**2602.05638**。citeturn6search3
- **読んだ範囲:** arXiv HTML 本文・Table 3・pretraining dataset table。
- **[近さ] 方向:** 1, 2, 3, 5。
- **視点:** mixed。EgoSurgery downstream は一人称。
- **ドメイン:** surgical foundation model。
- **課題の形:** frozen video representation + common attentive probe で phase/workflow recognition 等。
- **推論の規約:** causal/past-only を保証する記述を確認できず。online の直接比較には使えない。
- **データ規模:** pretraining SurgMotion-15M 約3,658時間・50 sources。EgoSurgery 21 videos を corpus に含む。citeturn11view0
- **モデルの状態:** downstream では foundation weights frozen、4-block attentive probing head。
- **[手法の位置] 系統:** video-native representation / backbone。
- **現役度:** **新興**。
- **ベンチマーク:** EgoSurgery 等。
- **少数動画／online／一人称:** downstream EgoSurgery は少数・一人称。online は×/不明。
- **[証拠] 比較:** 同一 probing protocol の下で異なる frozen encoders。
- **効果量:** Table 3、Jaccard 5.17–42.95、F1 7.33–50.72。SurgMotion は 42.95 Jaccard。citeturn11view1
- **符号:** 大幅改善。
- **条件:** encoder/pretraining 依存。
- **基準の強さ:** DINOv3, VideoMAE, EndoFM, SurgVLP 等を含む。
- **一要素比較:** temporal probe をほぼ統一しており representation の比較として強い。
- **seed／split／検定:** hyperparameter search は記載。seed 分散・統計検定は取得範囲で不明。
- **著者以外の追試:** 2026時点で新規のため少ない。
- **[実装]:** 公式 code 公開、Apache-2.0。citeturn6search11
- **追加データ:** 大規模 surgical videos。
- **pretraining leakage:** **要注意**。EgoSurgery が pretraining source に含まれる。test exclusion を確認できず。citeturn11view0
- **[要点]:** **backbone/pretraining が EgoSurgery 性能を大きく支配し得るという最も強い証拠だが、pretraining overlap の監査が必要。**

**Friends Across Time: Multi-Scale Action Segmentation Transformer for Surgical Phase Recognition**

- **[書誌]:** Bokai Zhang et al.／2024／*Friends Across Time: Multi-Scale Action Segmentation Transformer for Surgical Phase Recognition*／arXiv:**2401.11644**。査読版の DOI は取得資料では不明。citeturn19academia30
- **読んだ範囲:** arXiv HTML 本文・実験表該当部。
- **[近さ] 方向:** 2, 4。
- **視点:** laparoscopic/general TAS。
- **ドメイン:** 低侵襲手術＋一般 action segmentation。
- **課題:** per-frame features → multi-scale temporal self/cross-attention → phase/action labels。
- **推論規約:** MS-ASCT が online causal、MS-AST が offline。
- **データ規模:** Cholec80等。GTEA にも評価。
- **モデル状態:** ResNet50 または EfficientNetV2-M feature extractor + temporal model。
- **[手法の位置]:** multi-scale causal Transformer。
- **現役度:** **定番の基準候補**。2024の主要な causal multi-scale surgical model。
- **ベンチマーク:** Cholec80、一般 TAS。
- **少数／online／一人称:** online○。GTEA は小規模一人称。EgoSurgery は未検証。
- **[証拠] 比較:** 同一 MS-ASCT に ResNet と EfficientNetV2 を適用した比較があり、EffNetV2 が一貫して高い。取得 HTML の該当行では 93.58 vs 94.59 accuracy などが報告されるが、表番号を安全に確定できなかったため、依頼条件に従い主要結論以外の数値引用は控える。citeturn21view3
- **符号:** backbone 強化で改善。
- **条件:** backbone と online/offline causality。
- **基準:** surgical SOTA 群。
- **一要素比較:** backbone 比較は比較的 yes。
- **seed／split／検定:** 取得範囲で不明。
- **独立追試:** 後続の SSM 系の比較対象となる系統。
- **[実装]:** 不明。
- **追加注釈:** 不要。
- **leakage:** 不明。
- **[要点]:** **「多尺度 Transformer」と「causal」を両立した、EgoSurgery で未試験の有力対照群。**

**Holistic Surgical Phase Recognition with Hierarchical Input Dependent State Space Models**

- **[書誌]:** Haoyang Wu et al.／2025／*Holistic Surgical Phase Recognition with Hierarchical Input Dependent State Space Models*／プレプリント／arXiv:**2506.21330**。citeturn20view0
- **読んだ範囲:** arXiv HTML 本文・実験部。
- **[近さ] 方向:** 2, 4, 5。
- **視点:** laparoscopic。
- **ドメイン:** 低侵襲手術。
- **課題:** downsampled full procedure → temporally consistent visual features → local/global SSM → phase labels/progress。
- **推論規約:** causal SSM を明示し、著者は full-video online phase recognition と位置付ける。contextual/bidirectional variant も別途持つ。citeturn20view0
- **データ規模:** Cholec80、MICCAI2016、HeiChole。MICCAI2016 は41 videos、27 train/4 validation/10 test と記載しつつ final result を14 videosで報告するとする。citeturn21view2
- **モデル状態:** visual backbone を temporal-consistency pretraining 後に temporal SSM head を学習。
- **[手法の位置]:** hierarchical input-dependent SSM、local/global multi-scale。
- **現役度:** **新興**。2025 preprintで独立追試はまだ少ない。
- **ベンチマーク:** Cholec80/MICCAI2016/HeiChole。
- **少数／online／一人称:** online○、一人称×、EgoSurgery未検証。
- **[証拠]:** 著者要旨では従来 SOTA 比 +2.8% Cholec80、+4.3% MICCAI2016、+12.9% HeiChole とするが、これらは要旨値で表番号を満たさないため本報告では定量比較の根拠値として採用しない。citeturn20view0
- **符号:** 改善と報告。
- **条件:** causal/contextual version、local/global scale、visual pretraining を同時に導入しており、SSM 単独効果とは完全には分離されない。
- **基準:** TeCNO, SV-RCNet, TMRNet 等。
- **一要素比較:** no、複数要素が変わる。
- **seed／検定:** 不明。
- **独立追試:** 少ない。
- **[実装]:** v1 は「acceptance 後公開予定」。取得時点の公開状態は確証なし。
- **追加注釈:** phase progress supervision。
- **leakage:** 不明。
- **[要点]:** **SSM を EgoSurgery に持ち込むなら、bidirectional SR-Mamba より設計思想が今回の strict-online 条件に近い。**

**SR-Mamba: Effective Surgical Phase Recognition with State Space Model**

- **[書誌]:** Rui Cao, Jiangliu Wang, Yun-Hui Liu／2024／*SR-Mamba: Effective Surgical Phase Recognition with State Space Model*／プレプリント／arXiv:**2407.08333**。citeturn21search0
- **読んだ範囲:** 要旨＋arXiv HTML の方法概要。実験表の精読は未実施。
- **[近さ] 方向:** 2, 5。
- **視点:** laparoscopic/cataract。
- **ドメイン:** 手術。
- **課題:** spatial features と long sequence を Mamba decoder で phase recognition。
- **推論規約:** **bidirectional Mamba decoder。strict-online ではない。**
- **データ:** Cholec80, CATARACTS。
- **モデル状態:** single-step joint spatial-temporal training。
- **[手法の位置]:** SSM/Mamba、end-to-end。
- **現役度:** **SSM 系の定番基準。ただし offline 系**。後続 SurgicalMamba が最初期 surgical Mamba として位置付ける。citeturn21search16
- **少数／online／一人称:** online×、一人称×。
- **[証拠]:** SOTA と報告するが、表番号付き定量値は本調査で未確認のため省略。
- **符号:** 改善と著者報告。
- **条件:** bidirectionality と joint training が混ざる。
- **基準:** contemporary surgical phase models。
- **一要素比較:** no。
- **seed／検定:** 不明。
- **独立追試:** SurgicalMamba 等が引用。
- **[実装]:** code 公開。citeturn21search0
- **追加データ:** 不要。
- **leakage:** 不明。
- **[要点]:** **「Mamba が強い」という evidence ではあるが、未来情報を使うため EgoSurgery online の直接根拠にはならない。**

**SPRMamba: Surgical Phase Recognition for Endoscopic Submucosal Dissection with Mamba**

- **[書誌]:** Xiangning Zhang et al.／2024／*SPRMamba: Surgical Phase Recognition for Endoscopic Submucosal Dissection with Mamba*／プレプリント／arXiv:**2409.12108**。citeturn21search4
- **読んだ範囲:** 要旨＋HTML 方法概要。
- **[近さ] 方向:** 2。
- **視点:** endoscopic。
- **ドメイン:** 低侵襲手術。
- **課題:** ESD/Cholec80 phase recognition。
- **推論規約:** realtime を動機とするが、取得本文から target-time causality を厳密には確認できず、**online 不明**。
- **データ:** ESD385、Cholec80。
- **モデル状態:** spatial-temporal Mamba framework。
- **[手法の位置]:** SSM/Mamba＋Temporal Sample Strategy。
- **現役度:** **不明～新興**。
- **少数／online／一人称:** 一人称×。strict-online 不明。
- **[証拠]:** SOTA と著者要旨で報告。表番号付き数値は未確認のため省略。citeturn21search8
- **符号:** 改善と報告。
- **条件:** Mamba block と temporal sampling が同時変更。
- **基準:** surgical phase SOTA。
- **一要素比較:** no。
- **seed／検定:** 不明。
- **独立追試:** 不明。
- **[実装]:** 不明。
- **追加注釈:** 不要。
- **leakage:** 不明。
- **[要点]:** **Mamba の realtime suitability を主張するが、past-only を確認しない限り EgoSurgery online 候補として扱うべきでない。**

**SurgPLAN++: Universal Surgical Phase Localization Network for Online and Offline Inference**

- **[書誌]:** Zhen Chen et al.／2024／*SurgPLAN++: Universal Surgical Phase Localization Network for Online and Offline Inference*／プレプリント／arXiv:**2409.12467**。citeturn19academia29
- **読んだ範囲:** arXiv HTML 本文・online/offline inference algorithm。
- **[近さ] 方向:** 2, 4。
- **視点:** surgical video。
- **ドメイン:** 手術。
- **課題:** frame classification ではなく temporal phase proposals を生成。
- **推論規約:** online と offline を同一 architecture で実装。online は streaming past を mirroring/center duplication/downsampling で pseudo-complete sequence 化し、current center の phase proposal を採用。offline は過去 prediction を後から更新する。citeturn21view6turn21view7
- **データ規模:** Cholec80/Cataract 等。詳細は取得範囲で不明。
- **モデル状態:** temporal detector。
- **[手法の位置]:** phase localization/proposal。
- **現役度:** **新興/不明**。
- **ベンチマーク:** surgical phase。
- **少数／online／一人称:** online○、EgoSurgery未検証。
- **[証拠]:** offline mode が qualitative Fig. 3 で TeCNO/Trans-SVNet より ground truth に近いと著者報告。表番号付き online/offline 差の値は取得範囲で安全に確認できず省略。citeturn21view8
- **符号:** offline refinement が有利。
- **条件:** inference procedure 自体が異なる。
- **基準:** TeCNO、Trans-SVNet。
- **一要素比較:** online/offline は同 framework だが inference strategy が変化。
- **seed／検定:** 不明。
- **独立追試:** 不明。
- **[実装]:** source code 公開。citeturn19academia29
- **追加注釈:** 不要。
- **leakage:** 不明。
- **[要点]:** **「phase recognition = frame classifier」という前提自体を外す候補。EgoSurgery では完全未検証。**

**OnlineTAS: An Online Baseline for Temporal Action Segmentation**

- **[書誌]:** Qing Zhong, Guodong Ding, Angela Yao／2024／*OnlineTAS: An Online Baseline for Temporal Action Segmentation*／NeurIPS 2024、査読つき／arXiv:**2411.01122**。citeturn14search19turn15view0
- **読んだ範囲:** arXiv HTML 本文、appendix、Tables 1–12。
- **[近さ] 方向:** 3, 4, 5, 7。
- **視点:** GTEA は一人称。50Salads/Breakfast は非一人称。
- **ドメイン:** 非医療。
- **課題:** streaming procedural video の dense action segmentation。
- **推論規約:** strict-online は現在 frame まで。semi-online は window 単位で全予測を保持し、strict-online と別に報告。citeturn16view0
- **データ規模:** GTEA 28 videos/11 action classes、50Salads 50 videos/17 classes、Breakfast 1,712 videos/48 actions。I3D features。citeturn16view0
- **モデル状態:** fixed/pre-extracted frame features → causal TCN + GRU + context-aware attention + adaptive memory。
- **[手法の位置]:** memory＋RNN＋causal TCN＋Transformer-like feature augmentation。
- **現役度:** **SOTA級（online TAS, NeurIPS 2024 Table 8/9）**。citeturn16view2
- **少数／online／一人称:** GTEA がすべて満たす。
- **[証拠] 比較:** Table 8 strict-online causal TCN vs full OnlineTAS。
- **効果量:** GTEA Acc 74.4→75.8 **+1.4**、Edit 66.6→66.8 **+0.2**、F1@50 57.2→60.3 **+3.1**。50Salads Acc 75.2→79.1 **+3.9**、Edit 19.6→29.0 **+9.4**、F1@50 19.6→28.3 **+8.7**。citeturn16view2
- **符号:** 改善。
- **条件:** segment metric で効果が大きい。GTEA では frame accuracy の差は小さい。
- **基準:** causal TCN は強い簡潔な online baseline。LSTR の直接移植より強い。
- **一要素比較:** feature は共通だが full method は GRU/CFA/memory が複合。
- **seed／split／検定:** standard dataset protocol。seed-based significance test は確認できず。
- **著者外追試:** 2024以後の online TAS 文献で基準化しつつある。
- **[実装]:** 本文取得範囲では公式 code license 不明。
- **追加注釈:** 不要。
- **leakage:** I3D pretraining の評価データ包含については論文で問題化されていない。
- **[要点]:** **EgoSurgery の最有力な外部 analog。small egocentric online では memory の利益は実在するが、GTEA での上積みは数点。**

同論文は Q7 に特に重要である。Appendix Table 12 で ASFormer を standard→causal convolution、standard→causal attention に変えて online 化している。citeturn16view3

| Dataset | 指標 | offline ASFormer | strict-online causal ASFormer | 低下 |
|---|---:|---:|---:|---:|
| GTEA | Acc | 79.7 | 75.0 | −4.7 |
|  | Edit | 84.6 | 69.7 | −14.9 |
|  | F1@50 | 79.2 | 62.0 | **−17.2** |
| 50Salads | Acc | 85.6 | 77.5 | −8.1 |
|  | Edit | 79.6 | 29.1 | **−50.5** |
|  | F1@50 | 76.0 | 28.6 | **−47.4** |
| Breakfast | Acc | 73.5 | 64.9 | −8.6 |
|  | Edit | 75.0 | 32.1 | **−42.9** |
|  | F1@50 | 57.4 | 20.2 | **−37.2** |

これは「future context を失うコスト」が主として temporal consistency に現れることの強い証拠である。citeturn16view3

**Progress-Aware Online Action Segmentation for Egocentric Procedural Task Videos / ProTAS**

- **[書誌]:** Yuhan Shen, Ehsan Elhamifar／2024／*Progress-Aware Online Action Segmentation for Egocentric Procedural Task Videos*／CVPR 2024、査読つき／DOI **10.1109/CVPR52733.2024.01722**、arXiv ID 不明。citeturn18search23
- **読んだ範囲:** CVPR official page、official code README。PDF 本文中の数表は本調査では表番号付き再確認を完了できなかったため数値を引用しない。
- **[近さ] 方向:** 3, 4, 5。
- **視点:** 一人称。
- **ドメイン:** 非医療 procedural tasks。
- **課題:** online dense action segmentation。
- **推論規約:** causal backbone、past-only。公式 code は causal に設定すれば full-sequence `predict` と frame-by-frame `predict_online` が同じ結果になると明記。citeturn17search2
- **データ:** GTEA、EgoProceL、EgoPER。
- **モデル状態:** MS-TCN/ASFormer 系を causal 化し、action progress prediction と task graph を追加。
- **[手法の位置]:** causal segmentation + progress + task graph。
- **現役度:** **定番の基準（egocentric online procedural segmentation）**。citeturn18search13turn18search24
- **少数／online／一人称:** ○／○／○。
- **[証拠]:** paper/code は causal baseline に progress/task graph を加える構成。表番号付き値を安全に再取得できなかったため、数値は不掲載。
- **符号:** 改善と報告。
- **条件:** progress supervision、task graph。
- **基準:** MS-TCN/ASFormer。
- **一要素比較:** component ablation を持つが、数値は本調査では再確認未完了。
- **seed／検定:** 不明。
- **独立追試:** 2025–26の egocentric procedural papers が引用。citeturn18search13turn14search6
- **[実装]:** official GitHub 公開。大部分を MS-TCN code から派生。ライセンスは取得表示では不明。citeturn17search2
- **追加注釈:** action progress、task structure が必要。
- **leakage:** 不明。
- **[要点]:** **外科手術に最も近い非医療 analog。architecture を大きくするより「現在工程の進捗」と「許される工程遷移」を条件付ける方向が未検証。**

**Metrics Matter in Surgical Phase Recognition**

- **[書誌]:** Isabel Funke et al.／2023／*Metrics Matter in Surgical Phase Recognition*／technical report／arXiv:**2305.13961**。citeturn13search1turn20view3
- **読んだ範囲:** arXiv HTML 本文。
- **[近さ] 方向:** 6, 7。
- **視点:** 該当なし。
- **ドメイン:** surgical phase evaluation。
- **課題:** phase-recognition papers 間の metric/split/evaluation protocol の不一致を分析。
- **推論規約:** 方法論文。
- **データ規模:** 主に Cholec80 等。
- **モデル状態:** 該当なし。
- **[手法の位置]:** evaluation methodology。
- **現役度:** **定番の基準（評価方法論）**。2026 systematic evaluation work でも問題意識が継続。citeturn13search17
- **ベンチマーク:** Cholec80。
- **少数／online／一人称:** 該当なし。
- **[証拠]:** split、metric definition、phase/video averaging、relaxed boundaries が paper 間で異なり、互換でない数値比較を行うべきでないと指摘。video-wise metric 計算も明示。citeturn13search1turn21view9
- **効果量:** relaxed-boundary が性能をどの程度 inflates するかについて、本調査で表番号まで安全に取得できた統一値はないため **不明** とする。
- **符号:** 評価規約により ranking/値が変わり得る。
- **条件:** missing phases の扱い、average order 等。
- **基準:** 当時の公開 phase-recognition literature。
- **一要素比較:** metric definition を切り分けた方法論研究。
- **seed／検定:** 該当なし。
- **独立追試:** 後続 systematic evaluation が存在。citeturn13search17
- **[実装]:** 不明。
- **追加データ:** 不要。
- **leakage:** 該当なし。
- **[要点]:** **phase-recognition の「0.x点差」は評価コードが同一でなければ科学的に比較できない。**

**TMRNet: Surgical Phase Recognition with Temporal Memory Relation Network**

- **[書誌]:** 2021／TMRNet／IEEE TMI 系論文／arXiv:**2103.16327**。citeturn5search6
- **読んだ範囲:** 要旨・repository/evaluation instructions。
- **[近さ] 方向:** 2, 6, 7。
- **視点:** laparoscopic。
- **ドメイン:** 低侵襲手術。
- **課題:** frame features + long-range memory bank による phase recognition。
- **推論規約:** long-range temporal context を利用。厳密 causal 条件は implementation ごとに確認が必要。
- **データ:** Cholec80/M2CAI。
- **モデル状態:** CNN feature + temporal memory。
- **[手法の位置]:** explicit memory。
- **現役度:** **定番の基準**。2025 HID-SSM の related work/table に残る。citeturn20view0
- **少数／online／一人称:** EgoSurgery未評価。
- **[証拠]:** Q8 に重要なのは公式評価 code が **relaxed boundary mode** を用いると明記している点。citeturn5search10
- **効果量:** relaxed/non-relaxed の同モデル差を表番号付きで確認できなかったため不明。
- **符号:** 不明。
- **条件:** evaluation mode。
- **基準:** 当時の強い surgical models。
- **一要素比較:** relaxed-boundary の controlled paper ablation ではない。
- **seed／検定:** 不明。
- **独立追試:** 後続 paper の比較対象多数。一方、公開 trained model の再現性に関する GitHub issue も確認されたため、published table のみを ground truth とみなすのは注意が必要。citeturn5search14
- **[実装]:** GitHub 公開。ライセンス不明。
- **追加注釈:** 不要。
- **leakage:** 不明。
- **[要点]:** **memory 系の代表だが、同時に「評価コードの relaxed boundary を確認しないと他論文と直接比較できない」代表例でもある。**

**Surgformer: Surgical Transformer with Hierarchical Temporal Attention for Surgical Phase Recognition**

- **[書誌]:** Shu Yang et al.／2024／*Surgformer: Surgical Transformer with Hierarchical Temporal Attention for Surgical Phase Recognition*／arXiv:**2408.03867**。citeturn21search23
- **読んだ範囲:** 要旨のみ。
- **[近さ] 方向:** 2。
- **視点:** surgical。
- **ドメイン:** 手術。
- **課題:** hierarchical temporal attention による phase recognition。
- **推論規約:** 要旨だけでは strict causality を判定不能。
- **データ規模:** 不明。
- **モデル状態:** spatial-temporal Transformer。
- **[手法の位置]:** hierarchical/multi-scale Transformer。
- **現役度:** **不明**。2024以後の手術 Transformer 系の重要候補だが、今回 strict-online 証拠を確認できず。
- **ベンチマーク:** surgical phase。
- **少数／online／一人称:** EgoSurgery未検証。
- **[証拠]:** 表を未読のため数値なし。
- **効果量:** 不明。
- **符号:** 不明。
- **条件:** 不明。
- **基準:** 不明。
- **一要素比較:** 不明。
- **seed／検定:** 不明。
- **独立追試:** 不明。
- **[実装]:** 不明。
- **追加注釈:** 不明。
- **leakage:** 不明。
- **[要点]:** **「Transformer」の中でも単一スケール attention とは分けて扱うべき候補だが、past-only を確認するまで今回の本命にはしない。**

### 損失・境界処理について得られた負の証拠

「平滑化 loss を加えたら悪化した」「class-balanced loss が明確に無効だった」という **surgical phase recognition の clean ablation** は、今回確認した一次文献では見つからなかった。これは「効く」という意味ではなく、**論文が ablation を報告していない**という意味である。

一方、OnlineTAS は境界を強制的に安定化する post-processing に明確な trade-off を示す。Table 8 の strict-online では、GTEA で post-processing 前後が **Acc 75.8→73.5（−2.3）**、Edit 66.8→75.4（+8.6）、F1@50 60.3→66.6（+6.3）。50Salads では **Acc 79.1→76.7（−2.4）**に対し、Edit **29.0→69.2（+40.2）**、F1@50 **28.3→62.8（+34.5）**となる。つまり「境界を滑らかにするのは成功」と frame accuracy だけを見る場合の「悪化」が同時に成立する。citeturn16view2

また Table 6 では confidence threshold を上げると segmental score が大幅に上がる一方 Acc が 82.5 付近から 79.4 へ低下する。したがって smoothing/boundary mechanism は、単一の「効いた/効かなかった」ではなく、**frame accuracy と segment quality の Pareto trade-off**として評価すべきである。citeturn16view2

## 探したが見つからなかったもの

### EgoSurgery strict-online の architecture-controlled study

検索した主な語は `EgoSurgery online phase recognition causal`, `EgoSurgery temporal model`, `EgoSurgery Mamba`, `EgoSurgery Transformer`, `EgoSurgery state space model`, `EgoSurgery TeCNO` である。

**見つからなかったもの:** 同一 ResNet-50/ViT、同一特徴、同一 train/val/test split のまま、TeCNO、causal Transformer、memory、forward-Mamba を差し替えた研究。EgoSurgery 原論文 Table 1 は backbone と temporal architecture が同時に変わるため、この問いには答えていない。citeturn2view0

### EgoSurgery での SSM/Mamba

`EgoSurgery Mamba`, `EgoSurgery SSM`, `open surgery Mamba phase recognition` を探索した。

**見つからなかったもの:** EgoSurgery-Phase に **strict causal Mamba/SSM** を適用した表番号付き報告。SR-Mamba/SPRMamba/HID-SSM/PhaseMamba はすべて他の surgical datasets であり、EgoSurgery への転移は空白である。citeturn21search0turn21search4turn20view0turn21search20

### 実際の temporal gap / 区間切れの controlled study

検索概念は `discontinuous surgical video temporal model`, `video gaps causal temporal segmentation`, `reset hidden state surgical phase`, `missing interval Mamba TCN`, `streaming action segmentation interrupted actions`。

OnlineTAS は interrupted action を limitation として明示し、無限長 stream の memory management を未解決課題に挙げるが、人工的な temporal gaps を挿入して性能を測る実験はしていない。citeturn15view0

**見つからなかったもの:** 「30秒/1分/5分の欠落」「動画断片を concat」「gap token」「hidden state reset」の有無を独立変数にした EgoSurgery または surgical phase study。

### loss の否定的 ablation

検索概念は `surgical phase recognition smoothing loss ablation`, `boundary loss no improvement surgical phase`, `class imbalance weighting phase recognition ablation`, `MS-TCN smoothing loss negative result`。

**見つからなかったもの:** 同一 architecture・同一 split のまま smoothing loss、boundary loss、class weighting を一つずつ ON/OFF し、「有意に悪化/差なし」と結論した近年の surgical phase paper。

EgoSurgery は class imbalance に resampling を用いるが、no-resampling baseline を提示していないため、効いた量は不明である。citeturn3view1

### 計算環境差の controlled reproducibility

検索概念は `surgical phase recognition reproducibility GPU seed`, `TeCNO reproducibility CUDA`, `TMRNet reproduce results`, `temporal action segmentation seed variance`。

**見つからなかったもの:** 同一 checkpoint/training code を TITAN RTX/A100/H100/H800、異なる CUDA/cuDNN で繰り返し、phase metric の hardware-induced variance を表にした研究。

見つかったのは「hardware specification」と個別の reproduction issue までである。GGMAE は 3×TITAN RTX、SurgMotion は 4×H800 を報告するが、hardware 間の結果差は検証していない。citeturn3view1turn11view0turn5search14

### 一人称大型 dataset の strict-online dense segmentation

Assembly101 は **4,321 videos、8 static + 4 egocentric simultaneous views** を持つ大規模 procedural dataset だが、標準用途と EgoSurgery の「frame-by-frame strict-online phase segmentation」は同一ではない。citeturn21search3

Ego4D、Ego-Exo4D、HoloAssist、EPIC-KITCHENS も非常に有用な一人称 representation/pretraining/anticipation source だが、本調査で確認した範囲では EgoSurgery と完全に同じ **past-only dense procedural segmentation** を標準 benchmark とするわけではない。Ego-Exo4D は熟練行動の ego/exo multimodal benchmark であり、2026 challenge でも複数タスクを提供するが、これを surgical phase metric と同一視してはいけない。citeturn21search15turn21search19

## 未検証の組み合わせ

文献を横に並べると、最も重要なのは「新モデルがない」ことではなく、**有望な機構が EgoSurgery の strict-online 条件ではほぼ交差検証されていない**ことである。

| 組み合わせ | 既存の片側証拠 | EgoSurgery での状況 |
|---|---|---|
| ResNet-50 feature × causal forward-Mamba | HID-SSM/PhaseMamba が surgical online SSM の根拠 | **未検証** |
| ResNet-50 feature × OnlineTAS-style adaptive memory | GTEA/50Salads strict-online で改善 | **未検証** |
| ResNet-50 × MS-ASCT-style causal multi-scale attention | surgical online multi-scale Transformer の根拠 | **未検証** |
| TeCNO × explicit long-term memory | causal TCN と memory は別々に強い | **未検証** |
| TeCNO × progress prediction | ProTAS が非手術 ego で支持 | **未検証** |
| TeCNO × surgical task graph | ProTAS task graph が procedural ego で支持 | **未検証** |
| causal SSM × progress supervision | HID-SSM が近いが複数要素が交絡 | EgoSurgery **未検証** |
| causal temporal model × gaze feature | GGMAE は gaze を pretraining masking に利用 | online temporal conditioning は **未検証** |
| temporal head 固定 × GGMAE/SurgMotion/SelfSupSurg feature | representation 差は既に大きい | strict-online controlled head 比較は **未検証** |
| same backbone × TCN/RNN/Transformer/SSM | 一般 TAS には部分的証拠 | EgoSurgery **未検証** |
| gap-aware reset × SSM | SSM は state を保持できる | temporal discontinuity の controlled test **未検証** |
| gap-aware reset × causal TCN | receptive field は有限 | discontinuity mask の効果 **未検証** |
| causal model × boundary-aware loss | TAS では境界問題が重大 | EgoSurgery **未検証** |
| causal model × confidence-based online postprocessing | OnlineTAS Table 8 で segment metric 大幅改善 | EgoSurgery **未検証** |
| language/VLM semantic prior × causal temporal head | EgoVLP/SurgVLP/TOAD/PREGO 系に周辺証拠 | EgoSurgery phase **未検証** |
| object/tool state × phase model | EgoSurgery-Tool/HTS が同じ video domain に存在 | phaseとの causal multi-task **未検証** |
| surgeon-independent split × temporal architectures | 21本・8 surgeons | architecture ranking の surgeon dependence **未検証** |
| procedure-type-held-out × temporal architectures | 10 surgical types | cross-procedure generalization **未検証** |
| 5 seeds × fixed split | 多くの paper は single run/seed不明 | **未検証** |
| 5 folds × 5 seeds | 小標本では重要 | **未検証** |
| TITAN RTX/Ampere/Hopper × exact deterministic config | hardware は paper ごとに異なる | **未検証** |

とくに最後の三群、すなわち **split variation、seed variation、temporal-gap handling** は、新 architecture を一つ足すより結果の信頼性に関わる。既存 EgoSurgery Table 1 にはこの不確実性を定量化する材料がない。citeturn2view0

## 検索記録

検索日は **2026年10月19日（Asia/Tokyo）**。検索エンジンが総 hit 数を安定して返さないため、以下の「件数」は検索結果の総件数ではなく、**本調査で実在確認し、本文・要旨・公式 repository のいずれかまで関連性判定した unique 文献/資料数**である。

| 方向 | 主な検索語 | 関連性判定まで行った資料 | 主な発見 |
|---|---|---:|---|
| **方向1 同じデータ・一人称開放手術** | `EgoSurgery phase recognition`, `EgoSurgery temporal`, `EgoSurgery Mamba`, `open surgery egocentric phase`, `SurgMotion EgoSurgery` | **6** | EgoSurgery-Phase、repo、EgoSurgery-Tool、HTS、SurgMotion、SurgAtlas。strict-online SSM は0件。 |
| **方向2 手術一般** | `surgical phase online transformer`, `causal surgical phase`, `Mamba surgical phase`, `state space surgical phase`, `multi-scale surgical phase` | **16** | TeCNO, Trans-SVNet, LoViT, TMRNet, MS-ASCT, Surgformer, SR-Mamba, SPRMamba, HID-SSM, PhaseMamba, SurgicalMamba, SurgPLAN++, MoSFormer 等。 |
| **方向3 一人称非手術** | `egocentric online action segmentation`, `ProTAS GTEA EgoProceL`, `online procedural video`, `Ego4D procedural`, `Assembly101 online segmentation` | **12** | ProTAS が最も直接的。GTEA/OnlineTAS、Assembly101、Ego4D、Ego-Exo4D、PREGO/TI-PREGO を確認。 |
| **方向4 一般映像** | `online temporal action segmentation`, `online action detection transformer memory`, `causal TAS`, `streaming action segmentation` | **14** | OnlineTAS, LSTR, MiniROAD, OadTR, MAT, E2E-LOAD, MATR, HAT, TeSTra など。 |
| **方向5 機構一般** | `task graph online segmentation`, `progress action segmentation`, `video language online action detection`, `memory state space long video`, `distillation online action detection` | **10** | explicit memory、task graph/progress、language、future-teacher/distillation が独立した系統。 |
| **方向6 方法論** | `Metrics Matter surgical phase`, `relaxed boundary phase recognition`, `evaluation protocol Cholec80`, `reproducibility surgical phase` | **4** | Metrics Matter、2026 metric review、official evaluation repositories 等。 |
| **方向7 否定的結果・追試** | `causal vs offline action segmentation`, `failed smoothing loss action segmentation`, `cannot reproduce surgical phase`, `online LSTR TAS poor` | **7** | LSTR→TAS の不適合、offline→online の大幅 segment loss、postprocess の Acc 悪化、TMRNet reproduction issue。純粋な loss-negative study は0件。 |

### 引用追跡で重要だった流れ

EgoSurgery-Phase から TeCNO/Trans-SVNet/NETE/GGMAE を逆引きし、後続の SurgMotion から EgoSurgery を使う foundation models を逆追跡した。citeturn2view0turn11view1

TeCNO/TMRNet/Trans-SVNet 系を 2025 HID-SSM の related work と Table I から再確認すると、TCN・RNN・memory・Transformer が依然として比較軸として残り、その外側に SSM が新しい系統として追加されている。citeturn20view0

一般 action segmentation 側では OnlineTAS から MS-TCN, ASFormer, LSTR, MAT, DiffAct 等を逆追跡した結果、「offline TAS の最新手法」と「online procedural segmentation の最新手法」は同じランキングではなく、causality を導入すると segment quality が大きく変わることが確認できた。citeturn15view0turn16view2turn16view3

一人称側では ProTAS を起点に GTEA、EgoProceL、EgoPER と後続の egocentric procedural work を追った。大規模な Assembly101/Ego4D/Ego-Exo4D は重要な representation source ではあるが、EgoSurgery と完全同型の strict-online phase segmentation benchmark として扱うのは不適切である。citeturn17search2turn21search3turn21search15

## 解釈と提案

ここからのみ、文献上の事実と分けて私の解釈を述べる。

### 最優先は「新しい SOTA head」ではなく、交絡を切った実験である

現在の EgoSurgery の公表値から、

> 「GGMAE > TeCNO だから Transformer/MAE 系 temporal modeling が TCN より優れている」

とは言えない。

GGMAE と TeCNO では backbone、pretraining、入力 clip、学習法がすべて違う。一方、原論文 Table 2 と SurgMotion Table 3 は **representation だけでも Jaccard が大きく動く**ことを示す。citeturn2view0turn11view1

したがって最初の本実験は次の factorial design がよい。

| 固定するもの | 差し替えるもの |
|---|---|
| 同一 ResNet-50 checkpoint | TeCNO causal TCN |
| 同一 0.5 fps feature tensor | GRU |
| 同一 split | causal Transformer |
| 同一 optimizer / epoch / augmentation | MS-ASCT-like multi-scale causal attention |
| 同一 CE/smoothing loss | forward Mamba/SSM |
| 同一 post-processingなし | OnlineTAS-style explicit memory |
| 同一 seed set | TCN + memory |

これで初めて「時間モデルの寄与」が測れる。

さらに第二段階で temporal head を固定して、

**ResNet-50 supervised / surgical SSL / VideoMAE / GGMAE-like representation**

だけを変える。これで、

\[
\text{性能差}
=
\text{representation}
+
\text{temporal model}
+
\text{interaction}
\]

を少なくとも実験的に分けられる。

### EgoSurgery で最初に追加すべき時間モデルは forward SSM と explicit memory

優先順位を付けるなら、私は次の順にする。

**第一候補は軽量な forward Mamba/SSM。** 理由は、TeCNO と同じ causal streaming constraint を保ちながら、TCN の固定 receptive field より柔軟な長期状態を持てるためである。ただし SR-Mamba の bidirectional decoder をそのまま使ってはいけない。HID-SSM/PhaseMamba のように forward causal recurrence を選ぶ。citeturn21search0turn20view0turn21search20

**第二候補は OnlineTAS 型 explicit memory。** GTEA 28本という、EgoSurgery と規模・一人称という点で比較的近い条件で strict-online の正の evidence がある。しかも巨大な Transformer 全体を学習するより、小標本で inductive bias が強い。citeturn16view2

**第三候補は MS-ASCT 型 multi-scale causal attention。** 単純な single-scale Transformer より「局所手技」と「工程レベルの長期構造」を分ける仮説が手術に合う。citeturn19academia30

**第四候補は progress/task-graph conditioning。** 21動画しかない状況では、parameter count を増やすより「工程順序」と「工程内進捗」を明示する方が sample efficient である可能性が高い。ProTAS は一人称 procedural video で最も直接的な前例である。citeturn17search2

### 単純な Transformer 追加だけを第一候補にしない

一般 online TAS の結果を見ると、LSTR のような online detection 用 long/short Transformer を procedural segmentation に直接持ち込むと、50Salads で **Edit 5.0** と causal TCN の **19.6** より悪い（OnlineTAS Table 8）。これは「long-context Transformer なら勝つ」という単純な話ではなく、**procedural continuity を表現する inductive bias が必要**だという警告である。citeturn16view2

そのため比較対象として Transformer は必要だが、「attention の容量」を増すより、

- causal mask
- local/global scale
- explicit state/memory
- progress
- transition structure

のどれを導入するかを実験因子にした方が情報量が多い。

### loss は architecture sweep の後でよい

現時点の文献には、EgoSurgery において smoothing/boundary/class-balance loss の優劣を綺麗に切った証拠がない。

また OnlineTAS が示すように boundary smoothing は、F1/Edit を大幅改善しながら accuracy を数点下げることがある。citeturn16view2

したがって loss の実験は、

\[
\text{CE only}
\]

を基準に、

\[
+\text{truncated smoothing}
\]

\[
+\text{boundary loss}
\]

\[
+\text{class weighting または resampling}
\]

を**一つずつ**加えるべきである。全部を同時に入れたモデルと TeCNO を比較しても、何が効いたか分からない。

また primary endpoint を Accuracy だけにせず、少なくとも

**macro F1 / macro Jaccard / Edit / segmental F1 / boundary toleranceなしの boundary error**

を並列で持つべきである。

### offline と online は同じ表に無印で置かない

OnlineTAS の ASFormer 実験では、causal 化による F1@50 の低下は GTEA −17.2、50Salads −47.4、Breakfast −37.2点に達する。citeturn16view3

したがって EgoSurgery の future work 表には最低でも、

**Causal? / Future window / Look-ahead seconds / Post-hoc refinement**

の列を設けるべきである。

具体的には、

- `online-0`: current/past only
- `online-k`: k 秒 look-ahead
- `windowed`: target が window 中央で future を含む
- `offline`: entire sequence
- `offline-refined`: 過去 prediction を後から修正

を別 protocol とする。

GGMAE のような 10-frame clip model は、この定義をしないまま TeCNO と並べるべきではない。

### 「0.5 fps」では receptive field を秒・分で報告すべきである

EgoSurgery は 0.5 fps なので、1 frame = 2秒である。

したがって temporal kernel の議論を layer 数だけで行うより、

- 16 frames = 32秒
- 32 frames = 64秒
- 64 frames = 128秒
- 128 frames = 256秒 ≈ 4.3分
- 256 frames = 512秒 ≈ 8.5分

という**実時間 receptive field**で考える方が重要である。

OnlineTAS では 64/128 frame window を用いるが、frame rate が違えば同じ 128 frames でも意味が全く違う。citeturn16view3

EgoSurgery では、まず

**30秒、1分、2分、4分、8分、全過去**

の log-scale sweep を行い、性能が飽和する時間を測ることを勧める。

これを TCN、Transformer、SSM で共通化すれば、「architecture の違い」なのか「見えている過去の長さの違い」なのかも切り分けられる。

### 区間切れは architecture とは別の実験因子にする

これは現文献の明確な空白である。

SSM/RNN は過去を hidden state に持つので、不連続区間をそのまま連結すると、

> 実世界では数分離れている frame A と frame B

を

> 連続する t−1 と t

として扱ってしまう。

causal TCN や Transformer でも同様に、padding/mask を入れなければ人工的な隣接関係ができる。

したがって少なくとも次を比較する価値が高い。

| gap 処理 | 意味 |
|---|---|
| concat | 現状型。切れ目を無視 |
| reset | gap で RNN/SSM memory をゼロ化 |
| attention mask | Transformer で gap を跨がせない |
| TCN mask/padding | causal convolution が前区間を参照しない |
| gap token + duration | 「何秒飛んだか」を入力 |
| preserve state with Δt | SSM の transition を実経過時間で調整 |

最後の **Δt-aware SSM** は特に面白い。SSM は本来状態遷移と time scale を扱うため、「0.5 fps で均一」という仮定を外し、実際の timestamp gap を transition parameter に入れる設計と親和性がある。HID-SSM も input-dependent timescale Δ を持つため、この方向の理論的土台はあるが、surgical temporal gaps に使った実証はまだない。citeturn20view0

### 21動画では seed より split の不確実性も大きい可能性がある

14 train / 2 validation / 5 test では、test 1本が全 test の20%を占める。procedure type も10種、surgeonも8人である。citeturn2view0

したがって「model A が model B より Jaccard +1.5」といった結果を single split で結論にするのは危険である。

推奨する最低限の報告は、

**固定 official split × 5 seeds**  
に加えて  
**surgeon-grouped repeated split または grouped cross-validation**

である。

さらに可能なら、

**leave-one-procedure-type-out** または procedure-balanced split

を別表にする。

これにより、time model が「workflow の普遍的順序」を学んだのか、「特定 surgeon/procedure の appearance」を覚えたのかを分けられる。

### 計算環境の再現性は architecture ranking より seed 分散を先に測る

現文献からは GPU 世代そのものが metric を何点変えるかは分からない。従って最初から TITAN RTX 対 H100 といった hardware study を大規模に行う優先度は低い。

代わりに、

**同一 GPU・同一 CUDA で5 seeds**

をまず測り、その seed standard deviation が model 間差より小さいかを見る。

例えば

\[
\Delta J_{\text{model}}=1.2
\]

なのに

\[
\sigma_{\text{seed}}=2.0
\]

なら、その architecture ranking は意味が薄い。

その後に exact environment を固定し、

- Python
- PyTorch
- CUDA
- cuDNN
- GPU
- mixed precision
- deterministic flag
- random seeds
- data-loader workers

を記録する方が、21動画 benchmark では費用対効果が高い。

### 最小の次期実験セット

この調査を踏まえると、最初に回すべきモデルは大量には要らない。

| 実験 | 役割 | 優先度 |
|---|---|---|
| ResNet-50 + frame classifier | temporal context 0 の基準 | 必須 |
| ResNet-50 + current TeCNO | 現行基準 | 必須 |
| ResNet-50 + GRU | recurrent 基準 | 高 |
| ResNet-50 + causal Transformer | attention 基準 | 高 |
| ResNet-50 + causal multi-scale Transformer | MS-ASCT 仮説 | 高 |
| ResNet-50 + forward Mamba/SSM | 新規性・長期状態 | **最優先** |
| ResNet-50 + OnlineTAS-like memory | explicit memory | **最優先** |
| TeCNO + progress head | procedural prior | 次点 |
| TeCNO + task-transition graph | procedural prior | 次点 |

全モデルで **同一 frame feature tensor を disk に固定**して temporal model だけを学習する。

その後、勝った temporal head を固定して、

**ResNet-50 vs surgical SSL vs GGMAE/VideoMAE 系**

を比較する。

この二段階にすれば、今回の最重要な問いである

> 「性能を決めているのは frame representation なのか temporal model なのか」

に EgoSurgery 自身で答えられる。

現時点の文献だけからの最も妥当な事前予想は、**EgoSurgery のような21動画条件では representation/backbone の寄与がまず大きく、その上で explicit memory または causal SSM が TeCNO に数ポイント程度の改善を与える可能性がある。ただし改善の主成分は frame accuracy より boundary/segment consistency に出る可能性が高い**、である。このうち前半は EgoSurgery/SurgMotion、後半は OnlineTAS の証拠に基づくが、両者を同一 EgoSurgery strict-online 実験で結び付けた研究はまだ存在せず、そこが最も価値の高い未検証点である。citeturn2view0turn11view1turn16view2turn16view3
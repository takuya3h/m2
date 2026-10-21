# EgoSurgery に対する自己教師あり事前学習・手術基盤モデル・online 工程認識の文献調査

## 系統表

本調査では、**「対象データ自身での SSL」「手術ドメインの大規模事前学習」「一般画像・一般動画基盤モデル」「一人称動画基盤モデル」「視線・動き・物体を使う prior-guided masking」「online/causal 推論」「評価時のデータ漏れ」**を別系統として追った。特に EgoSurgery-Phase、SelfSupSurg、EndoViT、SurgMotion、SurgVISTA、SurgeNetXL、LEMON は、今回の問いに直接関わる数値を本文・表まで確認した。citeturn21view5turn14view0turn22search9turn21view4turn21view0turn17search28turn21view1

| 系統の名前 | 代表的な文献 | 現役度 | 下の記録に含めた件数 |
|---|---|---|---:|
| 対象手術データ上での image SSL | *Dissecting Self-Supervised Learning Methods for Surgical Computer Vision* | **定番の基準**。後続の Surgical FM 論文が比較・設計根拠として引用 | 2 |
| surgical masked modeling | VideoMAE、SurgMAE、EndoViT | **定番の基準〜置換進行中**。MAE は現在も比較対象だが、2025–2026 は distillation/JEPAs 等も増加 | 4 |
| prior-guided masking / weighting | GGMAE（gaze）、SurgMotion（motion）、Object-Aware VLP（object） | **新興**。EgoSurgery では gaze に直接の positive evidence がある | 3 |
| 大規模 endoscopic / laparoscopic surgical FM | Endo-FM、EndoViT、GSViT、SurgeNetXL、SurgVISTA、LemonFM、EndoMamba | **現役**。SurgeNetXL、SurgVISTA、LemonFM は直近査読論文で上位 | 8 |
| surgical vision-language pretraining | SurgVLP、PeskaVLP 系 | **定番化しつつある**。視覚のみの下流にも比較対象として登場 | 1 |
| 一般画像・動画 FM | DINOv3、VideoMAE V2、V-JEPA 2 | **SOTA 級／新興**。EgoSurgery の frozen transfer では DINOv3 が多くの surgical FM を上回る | 4 |
| 非医療の egocentric pretraining | EgoVLP、EgoVLPv2 | **定番の基準**（egocentric VLP）だが、手術への直接転移は未確認 | 2 |
| online / causal surgical workflow | TeCNO 系、LoViT、EndoMamba、GSViT | **現役**。ただし clip FM の「未来あり vs 過去だけ」の直接比較は乏しい | 3 |
| 評価・pretraining leakage | SurgVISTA の明示的 overlap 除去、EgoSurgery/SurgMotion の不明瞭なケース | **重要性上昇中** | 3 |

### 手術・内視鏡基盤モデルの横断一覧

ここでいう「開放・一人称割合」は、論文が明示した事前学習コーパスの内訳から判定した。記載がない場合は推測せず「不明」とした。

| モデル | 主な事前学習データ | 開放手術・一人称を含むか | backbone / 規模 | 公開重み・ライセンス |
|---|---|---|---|---|
| **EndoViT** | Endo700k、9 public endoscopy datasets、70万枚超 | 開放・ego の記載なし | ViT-B | コード・pretrained model 公開。論文 CC BY 4.0、**重み固有ライセンスは不明**。citeturn23view14turn23view16turn22search9 |
| **Endo-FM** | 9 public + 1 private、33K clips、最大約5M frames | colonoscopy / gastroscopy / laparoscopy 中心。開放・ego の記載なし | ViT-B/16 系、論文では 121M parameters | code/model 公開、repo は Apache-2.0。citeturn20search0turn20search24turn20search27 |
| **GSViT** | GenSurgery、680 h、robotic/laparoscopic、28 procedures | open/ego は報告されない | EfficientViT-M5、後続比較では 12.1M | code/weights 公開。重み固有 license は今回確認できず。citeturn23view20turn19view2turn17search5 |
| **SurgeNetXL** | >4,598 videos、4,711,024 frames、23超 procedures | YouTube 部分では **non-minimally-invasive と out-of-body を明示的に除外**。したがって少なくともこの部分に open/ego は含めない | 主モデル CAFormer-S18 24.3M。ConvNeXtV2-tiny/PVTv2-B2 も研究 | models/code 公開、GitHub MIT。citeturn19view0turn18view2turn17search14 |
| **SurgVISTA** | SurgPub 274 videos/約1.20M frames + SurgWeb 3,376 recordings/約2.35M frames | **SurgWeb は endoscopic view のみを残し external camera を除去**。SurgPub も列挙された laparoscopic/endoscopic/robotic datasets。open/ego は実質的に含まない構成 | ViT-B | repository と model card はあるが、調査時の repo には weight release 未完了の記述があり、license 表記にも不一致あり。citeturn22view12turn23view25turn10view3 |
| **LemonFM** | LEMON endoscopic monocular corpus | endoscopic。open/ego の報告なし | 主結果 ConvNeXt-L、ViT-L も ablation | official model resource は確認。weight license の明確な記載は今回取得できず。citeturn21view1turn23view12 |
| **EndoMamba** | mixed endoscopic corpus、公式 MICCAI page は **12 endoscopic videos** と記述 | open/ego なし | spatial Bi-Mamba + temporally causal Mamba | official implementation を確認、repo は Apache-2.0。citeturn21view3turn23view0 |
| **SurgVLP** | 1,326 surgical video lectures | view type の集計なし。open/ego 割合は**不明** | multimodal video-text encoder | code 公開。weight/license の詳細は今回未確定。citeturn23view18turn17search11 |
| **SurgMotion** | SurgMotion-15M、3,658 h、50 sources | **EgoSurgery 21 videos, 10.55 h を明示的に含む**。AVOS 等の view type は一部不明 | V-JEPA 系 video-native encoder。正確な parameter count は今回の本文抽出では不明 | Hugging Face weight 公開を確認。論文自体は CC BY 4.0、weight 固有 license は不明。citeturn4view1turn21view4 |
| **GastroNet-5M** | 約5M GI endoscopy images | surgical open/ego なし | ResNet50 23.5M / ViT-S 21.1M | 公開性の詳細は今回未確定。citeturn18view2turn19view2 |
| **EndoSSL** | 後続論文の記載では private 7,877 laparoscopic videos、約23.3M frames、5 procedure 超 | laparoscopic。open/ego の記載なし | ViT-L 系 | weight/license は今回確認できず。citeturn10view3 |

この一覧から分かる重要な事実は、**公開されている「手術基盤モデル」の大半は endoscopic/laparoscopic/robotic view に偏っており、EgoSurgery のような head-mounted egocentric open surgery を事前学習したことが明示されるモデルは、今回確認した範囲では SurgMotion が例外的**だということである。しかも SurgMotion は、その EgoSurgery を後段の評価にも用いている。citeturn4view1turn23view21

## 文献ごとの記録

**EgoSurgery-Phase / GGMAE — “EgoSurgery-Phase: A Dataset of Surgical Phase Recognition from Egocentric Open Surgery Videos”**

- **[書誌] 著者／年／題名／掲載先／ID:** 2024、MICCAI 2024、査読付き。arXiv: **2405.19644**。著者列は今回の抽出では省略。**読んだ範囲: 本文・実験表まで。** citeturn0search12turn1search8
- **[近さ] 方向／視点／ドメイン／課題:** 方向1。一人称、開放手術、phase recognition。論文は撮影時点で 20 open-surgery videos、8 surgeons、10 surgery types、25 fps と記し、privacy 処理後は 0.5 fps、約15 h、9 phases とする。視線も収録される。citeturn3view4
- **データ規模・分割の不審点:** 本文には「20 pre-processed videos」とある一方、記載 split は **14 train + 2 validation + 5 test = 21 videos** となり、内部整合しない。後続文献では EgoSurgery を 21 videos と扱うものがあるため、ユーザーが前提としている 21 本は後続の扱いと一致するが、**原論文自身には 20/21 の矛盾が残る**。citeturn3view4turn4view1
- **[手法の位置] 系統／現役度:** gaze-guided masked video modeling。現役度は厳密には**不明**。原論文 Table 2 では最良だが、2026年時点で同条件を査読付き独立論文が再現した証拠を確認できなかった。citeturn21view5
- **Table 2 の解釈:** **各行は「各手法の公開 checkpoint を別データから持ってきただけ」の比較ではない。** 論文は ViT-S、同一 training schema を用い、EgoSurgery-Phase 上で VideoMAE、VideoMAE V2、SurgMAE、GGMAE の pretraining strategy / masking を比較している。実装節には 10-frame clips、224×224、pretraining 800 epochs、batch 256、mask ratio 90%、fine-tuning 100 epochs が記載される。supervised ViT-S 行は EgoSurgery 上で scratch training である。citeturn3view5turn3view6turn21view5
- **ただし pretraining 動画範囲:** **「SSL は train split の14本だけ」と本文から確認できない。** split の説明と SSL 実装説明はあるが、test videos を SSL から除外したという明示が見つからない。したがって「train-only」と断定してはいけない。これは後述の評価設計上の重要な未確定事項である。citeturn3view4turn3view5
- **[証拠] Table 2:** supervised scratch ViT-S Jaccard **27.1**、VideoMAE tube **29.8**、VideoMAE V2 dual **30.8**、SurgMAE **27.8**、GGMAE gaze **33.9**。従って GGMAE は scratch 比 **+6.8 pp**、VideoMAE 比 **+4.1 pp**、VideoMAE V2 比 **+3.1 pp**、SurgMAE 比 **+6.1 pp**。ただしこれは **一般 pretrained checkpoint 対 GGMAE の比較ではない**。citeturn3view6turn21view5
- **prior の純粋効果:** Table 3 で mask ratio 90% を揃えると random **30.6**、tube **29.8**、gaze **33.9 Jaccard**。gaze は random 比 **+3.3 pp**、tube 比 **+4.1 pp**。少なくとも「mask selection だけ」に近い比較として、この +3.3 pp が最も重要な値である。citeturn4view0
- **敏感さ:** gaze mask ratio は 95/90/85/80% で Jaccard **31.2/33.9/31.6/31.5**。temperature は 1.00/0.75/0.50/0.25 で **30.1/30.6/33.9/27.2**。最良 0.50 と 0.25 の差は **6.7 pp**あり、小規模データで hyperparameter sensitivity は無視できない。citeturn4view0
- **seed・統計:** Table 2/3 に複数 seed の平均・標準偏差はなく、本文全文検索でも seed 数を確認できなかった。**seed 数: 不明、統計検定: なし／少なくとも報告を確認できず。**
- **推論規約:** 10-frame clip を使うが、評価時の clip が current frame より未来を含むか、strictly causal trailing window なのかは明確でない。したがってユーザーの「online 過去のみ」と同一規約とは扱えない。
- **[実装] コード・重み:** official GitHub を確認。視線データが追加で必要。citeturn1search2
- **[要点]:** **GGMAE は同一 EgoSurgery 実験内で gaze masking の正の効果を示すが、「一般重みより良い」という実験ではなく、SSL に test videos が入っていないことも確認できない。**

**SelfSupSurg — “Dissecting Self-Supervised Learning Methods for Surgical Computer Vision”**

- **[書誌]:** 2023、*Medical Image Analysis*。arXiv: **2207.00449**。査読付き。**読んだ範囲: 本文・Tables 3–5・Fig. 12・generalization section。** citeturn13view0turn14view0
- **[近さ]:** 方向2・7。laparoscopic Cholec80、80 videos、7 phases。ResNet-50 で MoCo v2、SimCLR、DINO、SwAV を比較し、surgical-domain SSL の hyperparameter、ラベル量、unlabeled data 量を大規模に調べた。citeturn14view3
- **[手法の位置]:** ResNet-based in-domain SSL。**定番の基準**。後続の SurgeNetXL 等が surgical SSL の設計根拠、とくに ImageNet initialization の重要性を引用している。citeturn18view2
- **[証拠・少数動画] Table 4 temporal phase recognition:** 5 labeled videos の “Base”＝ImageNet 上の SSL weight から直接 fine-tune に対し、Cholec80 train set でさらに surgical SSL した “Ours” は DINO **61.1→65.0 (+3.9 pp)**、MoCo v2 **63.4→66.1 (+2.7)**、SimCLR **63.6→66.6 (+3.0)**、SwAV **60.9→68.3 (+7.4)**。supervised ImageNet の “No SSL” は **62.3**で、最良 SwAV 68.3 はそれより **+6.0 pp**。citeturn14view2
- **10 videos では符号が一定でない:** DINO は **71.3→70.4 (-0.9 pp)** と悪化、MoCo **+5.0**、SimCLR **+3.3**、SwAV **+2.7 pp**。40 videos では差が小さく、saturation が見える。citeturn14view2
- **単一フレーム Table 3:** 5 videos で DINO 51.4→56.3、MoCo 52.1→58.1、SimCLR 51.3→57.2、SwAV 50.9→57.1。40 videos では DINO “Ours” **71.1** が ImageNet-SSL “Base” **71.6** と supervised ImageNet **71.5** の双方をわずかに下回る。citeturn14view0
- **negative result:** 一般 ImageNet 上だけの SSL weight は supervised ImageNet initialization をほとんど改善せず、著者集計では 36 条件中改善は 7 条件だけで、phase F1 は最大 **−1.9 pp**、tool mAP は最大 **−11.2 pp**悪化した。citeturn14view0
- **[Q5 に直接関係する証拠] initialization:** surgical SSL を scratch、ImageNet self-supervised、ImageNet fully-supervised の三つから始める Fig. 12 で、**fully supervised ImageNet initialization が全 SSL 手法で優位**。MoCo v2 では最大で phase F1 約 **+12 pp**、tool mAP **+11 pp**。すなわち「公開重みから対象領域で SSL を続ける」方が scratch SSL より良いという、今回最も直接的な証拠の一つである。citeturn14view0turn14view1
- **感度:** batch size 128–1024 は比較的頑健だが、initialization、augmentation、training length は重要。100 epochs 以降は平均改善がかなり飽和した。hyperparameter study 自体は約7,000 GPU-hours規模で、全設定の multiple-seed 実験はしていない。ランダムに選んだ一手法の5 reruns では phase F1 の SD 約0.7 pp。citeturn14view3
- **[実装/漏れ]:** data-supply experiment では SSL を **Cholec80 の training set 全体**で行い、その後 40/10/5 labeled videos に減らして fine-tune すると明記しており、EgoSurgery 論文より split hygiene が明確。citeturn14view0
- **[要点]:** **数本〜10本のラベル条件では in-domain SSL は有効になりやすいが、方法・初期値で符号が変わる。特に「ImageNet supervised → surgical SSL」は scratch SSL よりかなり強い。**

**EndoViT — “EndoViT: pretraining vision transformers on a large collection of endoscopic images”**

- **[書誌]:** Batić et al., 2024、*International Journal of Computer Assisted Radiology and Surgery* 19:1085–1091、査読付き。DOI **10.1007/s11548-024-03091-5**。**読んだ範囲: 本文・Tables 2–7。** citeturn22search2turn22search9
- **[近さ]:** 方向2・7。endoscopic/laparoscopic、ViT-B、MAE。Endo700k は9 public datasets、70万枚超。open/egocentric は含むと報告されない。citeturn23view14turn23view15
- **現役度:** **定番の基準**。SurgeNetXL、SurgVISTA、SurgMotion の最近の比較表に登場する。citeturn19view2turn23view25turn23view21
- **phase few-shot Table 7:** TeCNO stage 2 で ImageNet-pretrained ViT → EndoViT は、2 videos **77.05→78.89 (+1.84 pp)**、4 videos **80.00→80.28 (+0.28)**、8 videos **84.10→84.68 (+0.58)**。小さいほど利得が大きい傾向はあるが、劇的ではない。citeturn22search9
- **full-data negative:** Table 6 stage 2 は ImageNet ViT **89.56±0.65**、EndoViT **89.37±0.95**で **−0.19 pp**。stage 1 の8-video 条件も ImageNet 75.50 に対して EndoViT 75.30 とわずかに悪化する。著者自身、phase recognition では pretraining 差が小さいと論じる。citeturn22search9
- **別タスクでは効果大:** action-triplet Table 5 の2 videos では ResNet50 **10.88±0.50**、ImageNet ViT **12.22±1.78**、EndoViT **17.59±2.94 mAP**。したがって「domain pretraining が効く量」は downstream task に強く依存する。citeturn23view3
- **seed/statistics:** 各 network/setting を **3 runs**し mean±SD を報告。formal hypothesis test は確認せず。citeturn22search9
- **[実装]:** code と pretrained model を公開。論文は CC BY 4.0。weight-specific license は別途明記を確認できず。citeturn23view16turn22search9
- **[要点]:** **Endo-specific MAE は少数データや細粒度 task で有利だが、phase recognition では ImageNet ViT とほぼ同等、full-data ではわずかに負ける。**

**SurgMAE — “SurgMAE: Masked Autoencoders for Long Surgical Video Analysis”**

- **[書誌]:** Jamal & Mohareri, 2023、arXiv: **2305.11451**、今回確認できた版はプレプリント。**読んだ範囲: 要旨と EgoSurgery 側の再実装比較。** citeturn20academia35
- **[近さ]:** 方向2。long surgical video、ViT/MAE 系。high spatiotemporal-token sampling を使う masking strategy。citeturn20academia35
- **現役度:** **定番の比較対象**程度。GGMAE が EgoSurgery Table 2 で直接比較している。citeturn3view6
- **[証拠]:** EgoSurgery の同一 ViT-S training schema では SurgMAE Jaccard **27.8**、VideoMAE **29.8**、VideoMAE V2 **30.8**、GGMAE **33.9**。したがって task-specific な mask heuristic は常に random/tube より優れるわけではない。citeturn3view6
- **seed/statistics/online:** EgoSurgery 再実装側では seed/repeated-run 不明、strict online かも不明。
- **[要点]:** **「手術らしい mask を設計すれば必ず改善する」という証拠にはならず、EgoSurgery ではむしろ通常 VideoMAE より低かった。**

**Endo-FM — “Foundation Model for Endoscopy Video Analysis via Large-scale Self-supervised Pre-train”**

- **[書誌]:** Wang et al., 2023、MICCAI 2023、査読付き。arXiv: **2306.16741**、Springer DOI **10.1007/978-3-031-43996-4_10**。**読んだ範囲: 本文。** citeturn20search0turn20search12
- **[近さ]:** 方向2。9 public + 1 private endoscopy dataset、33K clips、最大約5M frames。colonoscopy/gastroscopy/laparoscopy を含むが、open/egocentric の記載はない。ViT-B/16 系 video transformer、約121M parameters。citeturn20search24
- **系統・現役度:** teacher-student/self-distillation による endoscopic video FM。**定番の基準**で、SurgeNetXL・SurgMotion などが比較対象にする。citeturn19view1turn23view21
- **cross-domain EgoSurgery:** SurgMotion Table 3 の frozen attentive probe では Acc **54.85**、F1 **36.13**、Jaccard **26.42**。DINOv3-H は F1 **36.34**、Jaccard **29.03**で、Endo-FM をわずかに上回る。citeturn2view6
- **[実装]:** official code/dataset/model repository 公開、repository license Apache-2.0。citeturn20search27
- **[要点]:** **endoscopic FM の中では EgoSurgery transfer が比較的強いが、open-egocentric では DINOv3 に優位とは言えない。**

**GSViT — “General surgery vision transformer: A video pre-trained foundation model for general surgery”**

- **[書誌]:** Schmidgall et al., 2024、arXiv: **2403.05949**。今回 peer-reviewed venue は確認できず。**読んだ範囲: 本文。** citeturn17search1turn17search9
- **[近さ]:** 方向2・8。GenSurgery は **680 h、robotic/laparoscopic、28 procedures**。LEMON の比較表では 3,182 videos とされる。open/ego は報告されない。citeturn23view20turn22view3
- **手法:** EfficientViT 系を使った forward video prediction。後続 SurgeNetXL の統一比較では EfficientViT-M5、**12.1M parameters**。論文は real-time surgical applications を意識している。citeturn19view2turn23view20
- **現役度:** **定番の比較対象**。SurgeNetXL、SurgMotion に採用されるが、後続 benchmark では必ずしも上位ではない。SurgeNetXL Table 3 の総合 ranking では比較 surgical FM の中で低位だった。citeturn19view2
- **EgoSurgery frozen transfer:** SurgMotion Table 3 では F1 **7.33**、Jaccard **5.17**で、DINOv3 や Endo-FM を大幅に下回る。citeturn2view6
- **[実装]:** code と pretrained GSViT weights 公開。weight-specific license は今回確認できず。citeturn17search5
- **[要点]:** **大規模な surgical video pretraining でも、内視鏡・ロボット映像から egocentric open surgery への表現移行が自動的に成功するわけではない。**

**SurgeNetXL — “Scaling up self-supervised learning for improved surgical foundation models”**

- **[書誌]:** Jaspers et al., 2026、*Medical Image Analysis* 108, 103873、査読付き。DOI **10.1016/j.media.2025.103873**、arXiv: **2501.09436**。**読んだ範囲: 本文・Tables 1/3・supplementary training details。** citeturn17search10turn17search2
- **[近さ]:** 方向2・5・6。SurgeNetXL は **>4,598 videos、4,711,024 frames、23超 surgical procedures**。public/private laparoscopic/robot-assisted data + YouTube 2,074,234 frames。YouTube curation では **non-MIS procedures と out-of-body frames を除去**している。citeturn19view0
- **手法:** DINO。重要なのは **scratch ではなく ImageNet-initialized weights から surgical DINO pretraining を続ける**設計である。CNN (ConvNeXt)、Transformer (PVTv2)、hybrid (CAFormer) を比較し、主モデルは CAFormer-S18 24.3M。citeturn18view2
- **現役度:** **SOTA 級**。MedIA 2026 Table 3 で六 downstream datasets・三 tasks に対して top-2 を維持し、paper 自身の benchmark では surgical FM 中最上位。citeturn19view1turn19view2
- **[Q5] ImageNet → surgical SSL の効果:** best ImageNet variant 比で phase-recognition accuracy が二データセットで **+2.9 pp、+2.7 pp**。Table 3 の AutoLaparo は ImageNet21k Acc/F1 **0.83/0.70** に対し SurgeNetXL **0.85/0.74**、RAMIE は **0.80/0.72 → 0.82/0.75**。citeturn19view1turn19view2
- **規模と多様性:** procedure-specific SurgeNetCholec より、より多様な SurgeNetXL が cholecystectomy 下流を含め大半で優位だった。単一術式に狭く pretrain することが必ずしも最適でないことを示す。citeturn19view1
- **cross-domain open ego:** SurgMotion Table 3 では SurgeNetXL の EgoSurgery F1 **7.34**、Jaccard **5.18**。これは SurgeNetXL 自身の MIS benchmark の強さと対照的で、view/domain shift の大きさを示す。citeturn2view6
- **評価:** downstream では patient-level cross-validation、ranking stability に 1,000 bootstrap samples を使う。citeturn19view1
- **実装:** models と dataset subset を公開、repo MIT license。citeturn17search14
- **[要点]:** **「一般 weight を初期値にして surgical SSL を続ける」ことには強い実証がある一方、その強さは open-egocentric transfer には保証されない。**

**SurgVISTA — “Large-scale self-supervised video foundation model for intelligent surgery”**

- **[書誌]:** 2026、*npj Digital Medicine*、査読付き。DOI **10.1038/s41746-026-02403-0**、preprint arXiv: **2506.02692**。2026年には correction notice も公開されており、本調査は現行 online article を参照した。**読んだ範囲: 本文・Methods。** citeturn21view0
- **[近さ]:** 方向2・6。SurgPub **274 videos / 1.20M frames** と SurgWeb **3,376 recordings / 2.35M frames**。20超 procedures、10超 anatomical regions。citeturn10view2
- **特に確認した事実—open/ego:** SurgWeb は **intraoperative endoscopic views のみを保持し、external camera views を明示的に除外**する。SurgPub も Cholec80、M2CAI16、HeiChole、PitVis、PSI-AVA、AutoLaparo、BernBypass70、StrasBypass70 等の endoscopic/laparoscopic/robotic corpus からなる。したがって、論文が記載する pretraining data に **EgoSurgery 型 open-egocentric video は含まれない**。citeturn22view12turn10view3
- **backbone:** ViT-B、embedding dimension 768、tube masking。しかも **random initialization から scratch pretraining**しており、ImageNet initialization を使わない。citeturn23view25
- **現役度:** **SOTA 級**。2026 peer-reviewed benchmark で surgical FMs と natural-domain ViT-B methods を広く比較する。citeturn21view0
- **OOD:** downstream benchmark は13 datasets、500超 long-form videos + 600 short clips、66万 frames 超。OOD dataset は pretraining corpus から完全に分離している。cataract/ophthalmic や ESD も含み、open-egocentric は含まない。citeturn22view13
- **[Q7] leakage 処理:** in-domain downstream test sets は pretraining と fine-tuning の双方から除外。さらに M2CAI16 training set と Cholec80 test set の **5重複動画**を発見し、Cholec80 test の動画 **73, 77, 78, 79, 80** を除外して評価した。これは今回見つけた中で最も明確な reporting practice である。citeturn23view24turn10view4
- **一般 FM 比較:** natural-domain baseline は ImageNet 系に加えて VideoMAE 等を含み、architecture を ViT-B に揃えている。ただし DINOv3 と V-JEPA2 はこの表には含まれない。citeturn23view25turn23view8
- **weights/license:** repository/model resources は存在するが、今回確認した repository には weight release が未完了である旨の記載が残り、GitHub と model-card 側で non-commercial license 表記にも差があったため、**weight license は確定扱いにしない**。
- **[要点]:** **SurgVISTA の事前学習には open surgery/egocentric video は含まれない。データ重複の発見・除外・報告は、EgoSurgery 5-fold の設計で倣う価値が高い。**

**LEMON / LemonFM — “LEMON: A Large Endoscopic MONocular Dataset and Foundation Model for Perception in Surgical Settings”**

- **[書誌]:** 2026、CVPR 2026、arXiv: **2503.19740**。査読付き conference paper。**読んだ範囲: 本文・Table 5。** citeturn21view1
- **[近さ]:** 方向2・6・7。endoscopic monocular dataset/FΜ。open/ego の報告なし。今回取得した本文断片から事前学習 corpus の最終総動画数を安全に転記できなかったため、その欄は**不明**とする。
- **現役度:** **SOTA 級**。論文は既存 surgical FM 比で phase Jaccard を AutoLaparo **+9.5 pp**、M2CAI16 **+9.4 pp**、Cholec80 **+8.4 pp**、CholecT50 action mAP **+4.4 pp**、tool detection 等でも改善と報告する。citeturn21view1
- **[Q6 の強い比較] Table 5:** backbone を frozen にし、同じ curated LEMON + augmented distillation 条件で ViT-L と ConvNeXt-L を比較。AutoLaparo Acc/F1 は ViT-L **75.6/66.1**、ConvNeXt-L **76.4/66.9**で ConvNeXt が各 **+0.8 pp**。CholecSeg8k mDice は **61.2→71.9 (+10.7 pp)** と差が大きい。citeturn23view11turn23view12
- **negative/architecture sensitivity:** 著者は frozen-backbone 条件で generative/MAE 系より discriminative objective が優位と報告しており、「ViT+MAE が surgical FM の当然の最適解」とは言えない。citeturn22view8
- **seed/statistics:** Table 5 の抽出範囲から multiple seeds の情報は確認できず。
- **[要点]:** **surgical video でも backbone と SSL objective の選択は大きく効き、特に frozen transfer では ConvNeXt/discriminative pretraining が ViT/MAE を上回る例がある。**

**EndoMamba — “EndoMamba: An Efficient Foundation Model for Endoscopic Videos via Hierarchical Pre-training”**

- **[書誌]:** Tian et al., 2025、MICCAI 2025、arXiv: **2502.19090**。査読付き。**読んだ範囲: arXiv 本文と MICCAI official page。** citeturn21view2turn21view3
- **[近さ]:** 方向2・5・8。official MICCAI page は **12 endoscopic videos** の mixed corpus と記述しており、他の「foundation model」と比べ非常に小さい pretraining set である。citeturn21view3
- **手法:** spatial modeling に Bi-Mamba、temporal modeling に **causal vanilla Mamba**。masked reconstruction に加え、大規模一般-domain video foundation model の features と alignment する hierarchical pretraining を用いる。citeturn21view3turn23view0
- **Q5 との関係:** 「一般 FM の知識を teacher/prior として使い、少量の endoscopy data で domain adaptation 的な pretraining を行う」系統に当たる。ただし ImageNet→DINO のような単純 continued SSL とは異なる。
- **cross-domain EgoSurgery:** SurgMotion Table 3 の frozen probing で Acc **53.30**、F1 **13.90**、Jaccard **10.32**。open egocentric への transfer は弱い。citeturn2view6
- **online:** temporal state-space component は causal なので、「未来 frame を要求しない video backbone」という点で本研究に特に近い。citeturn21view3
- **[要点]:** **12本規模の domain data と general-video prior を組み合わせる有力な設計例だが、open-egocentric zero/frozen transfer 自体は弱い。**

**SurgVLP — “Learning Multi-modal Representations by Watching Hundreds of Surgical Video Lectures”**

- **[書誌]:** Yuan et al., 2025、*Medical Image Analysis* 105:103644、査読付き。DOI **10.1016/j.media.2025.103644**、arXiv: **2307.15220**。**読んだ範囲: 本文。** citeturn17search19turn17search15
- **[近さ]:** 方向2・5。video-language pretraining。EAES/YouTube 等から最終的に **1,326 surgical video lectures** を pretraining set に集める。論文は hepatobiliary/pancreatic、general/digestive、bariatric、hernia、colorectal/transanal/proctological categories を列挙する。citeturn23view18
- **view composition:** lecture corpus の「内視鏡、open、external camera、egocentric」の割合は集計されていないため、**open/ego 比率は不明**。
- **現役度:** **定番の比較対象**。SurgMotion の surgical FM benchmark にも入る。citeturn23view21
- **EgoSurgery frozen transfer:** Acc **57.44**、F1 **23.26**、Jaccard **17.46**。Endo-FM や DINOv3 より低い。citeturn2view6
- **実装:** code public。citeturn17search11
- **[要点]:** **言語 supervision は procedure semantics を持ち込めるが、少なくとも frozen open-egocentric phase transfer では DINOv3/Endo-FM に勝っていない。**

**SurgMotion — “SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos”**

- **[書誌]:** Wu et al., 2026、arXiv: **2602.05638**, v2 24 Mar 2026。**2026-10-05 時点で本調査から査読付き採択は確認できず、プレプリントとして扱う。** arXiv text は CC BY 4.0。**読んだ範囲: 本文・Tables 1–3。** citeturn1search0turn21view4
- **[近さ]:** 方向1・2・4・7。V-JEPA-style latent video prediction に motion-guided weighting、spatiotemporal affinity self-distillation、feature-diversity regularization を加える。citeturn3view1
- **Table 1 の pretraining corpus:** SurgMotion-15M、計 **3,658 h**。表には、neurosurgery/endoscopic web+institutional 2,303 videos/2,860.85 h、AVOS abdominal 10,874/125.16 h、ophthalmology 1,969/230.76 h、gastric 180/252.10 h、Cholec80/M2CAI 121/77.51 h、EndoFM colonoscopy data 30,000 entries/45 h、AutoLaparo 25/23.12 h、PSI-AVA 8/20.45 h、PmLR50 50/6.95 h、JIGSAWS/AIxSuture 206/5.27 h、bronchoscopy 60/50 h、そして **EgoSurgery 21 videos/10.55 h** が列挙される。citeturn4view1
- **特に重要:** **EgoSurgery は SurgMotion の pretraining dataset に含まれる。** 一方で Table 3 は EgoSurgery を downstream evaluation に使う。本文から「EgoSurgery test videos は SurgMotion pretraining から除外した」とする記述を確認できない。従って SurgMotion の EgoSurgery 数値を「完全に unseen な open surgery transfer」と呼んではいけない。citeturn4view1turn23view21
- **evaluation protocol:** backbone は **frozen**。4 attention blocks、16 cross-attention heads の attentive probing head だけを downstream task に fit する。したがって Table 3 は full fine-tuning comparison ではない。citeturn23view22
- **EgoSurgery Table 3:** DINOv3-L Acc/F1/Jaccard **75.37/32.43/26.03**、DINOv3-H **70.08/36.34/29.03**、VideoMAE-L **64.52/26.84/19.82**、VideoMAE-G **62.25/20.40/16.13**、EndoViT **32.32/9.29/6.31**、GastroNet **48.12/16.08/12.87**、GSViT **35.74/7.33/5.17**、EndoMamba **53.30/13.90/10.32**、EndoFM **54.85/36.13/26.42**、SelfSupSurg **36.03/7.38/5.22**、SurgeNetXL **35.82/7.34/5.18**、SurgVLP **57.44/23.26/17.46**、SurgMotion **75.57/50.72/42.95**。citeturn2view6
- **Q4 の結論に重要な点:** contamination のない一般モデル側を見ると、**DINOv3-H の F1 36.34/Jaccard 29.03 は Endo-FM 36.13/26.42 を上回り、他の大半の surgical FM を大幅に上回る**。これは open-egocentric transfer では「surgical FM」というラベル自体が優位性を保証しないことを示す。citeturn2view6
- **V-JEPA2 / VideoMAE V2:** Table 3 に **V-JEPA2 の standalone baseline はない**。また VideoMAE は L/G があるが VideoMAE V2 の row はない。したがって DINOv3、V-JEPA2、VideoMAE V2 を同一 EgoSurgery protocol で比較した表ではない。citeturn23view21
- **EndoFM の不審な重複:** SurgMotion Table 2 の **Cholec80 EndoFM は Acc 57.25, F1 36.13, Jaccard 26.42**。Table 3 の **EgoSurgery EndoFM は Acc 54.85, F1 36.13, Jaccard 26.42**。F1 と Jaccard が二つの異なる dataset で小数第2位まで完全一致し、Accuracy だけ異なる。論文本文に説明はない。**copy/transcription error と断定はできないが、少なくとも著者確認が必要な異常値である。** citeturn4view2turn2view6
- **split/seed:** EgoSurgery で original split、5-fold、別 split のどれを使ったかを Table 3 周辺で確認できず、**評価 split: 不明**。full-text search でも seed の記述は見つからず、**seed 数: 不明**。citeturn22view15
- **[要点]:** **SurgMotion Table 3 は非常に重要な比較表だが、SurgMotion 自身の EgoSurgery score は事前学習 corpus に EgoSurgery が入っているため clean unseen-transfer score ではない。EndoFM の重複値にも未解決の疑義がある。**

**GastroNet-5M**

- **[書誌]:** GastroNet-5M。GI endoscopy foundation model。今回原論文の DOI/arXiv ID を確実に転記できなかったため **ID 不明**。**読んだ範囲: 後続査読論文の比較記述・表。**
- **[近さ]:** 方向2・6。5M超 gastrointestinal images を DINO で pretrain。ResNet50 と ViT-S variants が存在する。citeturn18view2
- **Q6:** SurgeNetXL Table 3 の同一 downstream pipeline では ResNet50 と ViT-S の AutoLaparo F1 が **0.58 vs 0.54**、RAMIE F1 **0.64 vs 0.61**。少なくともこの transfer では ResNet50 variant が phase task で上。segmentation は dataset により混在する。citeturn19view2
- **EgoSurgery:** SurgMotion frozen probe F1 **16.08**、Jaccard **12.87**。citeturn2view6
- **[要点]:** **ResNet-vs-ViT の手掛かりはあるが、同一 SSL objective/corpus でも downstream architecture まで完全統制された研究とは言い切れない。**

**EndoSSL — “Self-supervised learning for endoscopic video analysis”**

- **[書誌]:** Hirsch et al., 2023、MICCAI 2023 と後続文献に記載。今回 arXiv/DOI を確実に回収できず **ID 不明**。原論文は今回、本文未精査。
- **[近さ]:** 方向2。SurgVISTA の comparative description では private **7,877 laparoscopic videos、約23.3M frames、5超 procedures、ViT-L**。citeturn10view3
- **EgoSurgery:** SurgMotion frozen benchmark では Acc **49.78**、F1 **12.04**、Jaccard **8.86**。citeturn2view6
- **[要点]:** **非常に大きな laparoscopic pretraining corpus でも open-egocentric transfer は弱く、データ量だけで viewpoint gap は埋まらない。**

**VideoMAE — “VideoMAE: Masked Autoencoders are Data-Efficient Learners for Self-Supervised Video Pre-Training”**

- **[書誌]:** 2022、NeurIPS、arXiv: **2203.12602**。査読付き。今回は元論文を再精査せず、EgoSurgery/SurgVISTA/SurgMotion の比較側を中心に確認。
- **[近さ]:** 方向4。一般動画 masked reconstruction、tube masking。surgical FM の定番 baseline。
- **EgoSurgery の注意:** GGMAE Table 2 の VideoMAE Jaccard **29.8** は、単に Kinetics-pretrained VideoMAE checkpoint を読み込んだ値ではなく、EgoSurgery の共通 pretraining schema における比較値である。citeturn3view5turn3view6
- **SurgMotion frozen transfer:** VideoMAE-L F1/Jaccard **26.84/19.82**、VideoMAE-G **20.40/16.13**。より大きな G が L より悪く、model size と transfer quality は単調ではない。citeturn2view6
- **[要点]:** **VideoMAE は強い基準だが、EgoSurgery では external checkpoint と local SSL を区別して読む必要がある。**

**VideoMAE V2 — “VideoMAE V2: Scaling Video Masked Autoencoders with Dual Masking”**

- **[書誌]:** 2023、CVPR、arXiv: **2303.16727**。査読付き。
- **[近さ]:** 方向4。general video pretraining、dual masking。SurgVISTA は自然動画側の大規模 masked-video pretraining 系を baseline として扱う。citeturn23view8
- **EgoSurgery:** GGMAE Table 2 では Jaccard **30.8**、GGMAE 33.9 に対し **−3.1 pp**。ただし、ここも published general checkpoint の zero-/fine-tune transfer comparison ではなく、EgoSurgery 上の共通 training schema 内の比較。citeturn3view6turn21view5
- **[要点]:** **「Kinetics等で大規模事前学習済み VideoMAE V2」と「EgoSurgery で VideoMAE V2 objective を回したもの」を混同しないことが重要。**

**DINOv3**

- **[書誌]:** 2025、arXiv: **2508.10104**。**読んだ範囲: original paper の architecture/evaluation sections を確認、手術転移は SurgMotion を精査。** citeturn22view0turn23view9
- **[近さ]:** 方向4・5。general image foundation model。video model ではないが、frame representation として online surgical phase pipeline に自然に接続できる。
- **現役度:** **SOTA 級の一般画像表現**。手術側ではまだ新興 baseline。
- **EgoSurgery frozen transfer:** DINOv3-L F1/Jaccard **32.43/26.03**、DINOv3-H **36.34/29.03**。EndoViT、GSViT、EndoMamba、SurgeNetXL、SurgVLP を上回り、Endo-FM も Jaccard で上回る。citeturn2view6
- **fine-tune:** SurgMotion Table 3 は frozen probing なので、**full fine-tuning で surgical FM と DINOv3 の順位がどう変わるかは未測定**。
- **[要点]:** **EgoSurgery の次の baseline として最も無視できない一般 model。少なくとも frozen features では多くの surgical FM より強い。**

**V-JEPA 2 — “V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning”**

- **[書誌]:** 2025、arXiv: **2506.09985**。**読んだ範囲: original paper の evaluation/architecture sections。** citeturn22view1turn23view10
- **[近さ]:** 方向4・5。latent-space predictive video SSL。masked pixels ではなく representation prediction を中心とする。
- **現役度:** **SOTA級／新興** general video FM。
- **手術 transfer:** 今回確認した EgoSurgery comparative tables に **V-JEPA 2 standalone weight の row を発見できなかった**。SurgMotion は JEPA 系の考え方を採用するが、V-JEPA 2 checkpoint の単純 transfer baseline とは別物。citeturn21view4turn23view21
- **[要点]:** **ユーザーが挙げた general-video candidates の中で、EgoSurgery への clean benchmark が最も明白に欠けている一つ。**

**EgoVLP — “Egocentric Video-Language Pretraining”**

- **[書誌]:** Lin et al., 2022、NeurIPS 2022、arXiv: **2206.01670**。**読んだ範囲: 書誌・official code/model resources。元論文の全実験表は今回未精査。** citeturn23search0
- **[近さ]:** 方向3。一人称非医療 video-language pretraining。手・対象物・作業手順・egomotion といった viewpoint statistics の点で EgoSurgery に近い系統。
- **現役度:** **定番の基準**。後続 EgoVLPv2 が存在する。citeturn23search8
- **手術 transfer:** 今回の検索では **EgoVLP pretrained weights を open surgery phase recognition に直接移した査読研究を確認できなかった**。
- **[要点]:** **ドメインは非医療でも viewpoint は surgical FMs より EgoSurgery に近い可能性があるが、その仮説を直接測った文献は今回見つからない。**

**EgoVLPv2 — “EgoVLPv2: Egocentric Video-Language Pre-training with Fusion in the Backbone”**

- **[書誌]:** 2023、ICCV 2023、arXiv: **2307.05463**。**読んだ範囲: model/code metadata。** citeturn23search8
- **[近さ]:** 方向3。一人称 video-language FM。
- **現役度:** **定番の基準**（EgoVLP の後継）。
- **手術 transfer:** direct surgical transfer は今回確認できず。
- **[要点]:** **Ego4D/EPIC 系の一人称 prior が手術の camera geometry に効くかという問いは、依然ほぼ空白である。**

**Object-Aware Video-Language Pre-training for Retrieval**

- **[書誌]:** 2022、CVPR 2022、arXiv: **2112.00656**。査読付き。**読んだ範囲: 本文の masking method 部分。** citeturn23search3turn23search7
- **[近さ]:** 方向3・5。非医療 video-language retrieval。
- **prior-guided masking:** object regions を利用する **object-guided masking**で、scene bias だけでなく object/context relationship を学習させる設計。citeturn23search3
- **手術 transfer:** surgical video や EgoSurgery への適用は今回見つからない。
- **[要点]:** **object prior を masking に使う系統自体は確立しているが、手術では gaze ほど直接的な検証がない。**

以上を横断すると、質問ごとの実証状態は次のようになる。

**対象データが数本〜数十本の場合**、SelfSupSurg では 5-video/10-video で in-domain SSL の改善が大きくなるが、DINO の10-video temporal case のように悪化もある。EndoViT では2-video phase recognition の利得は +1.84 pp 程度で、4/8/full ではほぼ消える。一方 EgoSurgery の GGMAE は scratch に対して +6.8 Jaccard を示すものの、強い ImageNet/DINO/Kinetics pretrained checkpoint との直接比較ではない。したがって「small target-set SSL は常に general pretraining より良い」という証拠はない。citeturn14view2turn22search9turn3view6

**prior-guided masking の中では、今回もっとも強く対象条件に一致する証拠は gaze**であり、EgoSurgery 上で random mask と mask ratio を揃えて +3.3 Jaccard。ただし temperature の選択だけで 6.7 pp 動く。motion は SurgMotion が有望だが複数の新要素を同時導入しており純粋効果を切り分けにくい。object prior は一般動画では存在するが surgical transfer がない。saliency-guided surgical MAE の明瞭な controlled result は今回見つからなかった。citeturn4view0turn3view1turn23search3

## 探したが見つからなかったもの

**GGMAE の fold-local SSL を保証する記述。** `EgoSurgery GGMAE pretrain split train test`, `EgoSurgery self-supervised pretraining train split`, `2405.19644 seed`, `pretrain split` を本文で追ったが、「SSL は14 training videos のみに限定」「test 5 videos は SSL にも未使用」とする文章を確認できなかった。seed 数も確認できない。したがって、ここは **不明**とする。citeturn3view4turn3view5

**SurgMotion の EgoSurgery 5-fold protocol。** `EgoSurgery split`, `fold`, `train split`, `test split`, `seed`, `exclude` を確認したが、Table 3 が original EgoSurgery split なのか独自 split なのか、5-fold なのかを特定できなかった。逆に pretraining Table 1 には EgoSurgery 自体が明記される。citeturn4view1turn23view21turn22view15

**SurgMotion の査読版。** 2026-10-05 時点で今回の title/arXiv/venue 検索から査読付き conference/journal version を確認できなかったため、arXiv preprint として記録した。citeturn21view4

**DINOv3・V-JEPA 2・VideoMAE V2・surgical FMs を同一 EgoSurgery 5-fold で、frozen と full fine-tune の両方まで揃えた研究。** 見つからなかった。SurgMotion は DINOv3 と VideoMAE を frozen probing で比較するが V-JEPA2/VideoMAE V2 がなく、full fine-tuning もない。EgoSurgery-Phase は VideoMAE V2 を含むが local pretraining/masking comparison であって published general checkpoint comparison ではない。citeturn23view22turn23view21turn3view6

**clean な surgical-FM → open-egocentric transfer。** SurgMotion Table 3 は多くの surgical FMs の useful benchmark だが、SurgMotion 自身は EgoSurgery を pretraining に含む。EndoFM 等の他モデルについては EgoSurgery contamination の証拠はないが、evaluation split 自体が十分記述されていない。したがって「完全に clean な統一 benchmark」とまでは扱えない。citeturn4view1turn23view22

**EgoVLP/EgoVLPv2 → surgical phase recognition。** `EgoVLP surgery`, `Ego4D surgical transfer`, `EPIC-KITCHENS surgical video pretraining`, `egocentric pretrained surgical phase recognition` 系を追ったが、EgoVLP family の published weight をそのまま EgoSurgery/open surgery に移す直接研究を確認できなかった。EgoVLP/EgoVLPv2 自体の実在と公開資源は確認した。citeturn23search0turn23search8

**Ego-Exo。** ユーザーの種として検索したが、今回の検索結果から「どの論文を Ego-Exo と呼んでいるか」を原典まで一意に確認できなかったため、**実在未確認として文献記録から除外した**。同名・近似名を推測で補っていない。

**saliency-guided surgical masking。** `saliency-guided masking surgical MAE`, `surgical video saliency masked autoencoder`, `object guided surgical masking` を検索した。object-guided masking の一般動画論文、gaze-guided GGMAE、motion-guided SurgMotion は見つかったが、**視覚 saliency map のみを prior として surgical MAE mask を選び、その寄与を random/tube と controlled comparison した査読論文**は今回見つからなかった。citeturn23search3turn4view0turn3view1

**strict online clip vs offline/symmetric clip の性能差。** `online surgical phase recognition causal future frames`, `causal vs offline surgical phase recognition`, `trailing clip surgical phase recognition` を検索し、LoViT や EndoMamba 等の online/causal 系統は確認したが、**同一 video foundation backbone、同一 split、同一 clip length で「centered/future-available」と「past-only trailing clip」を一要素だけ変えた degradation table**は見つからなかった。LoViT は online SPR を対象にし、EndoMamba は temporal causality を明示するが、この問いそのものを isolate していない。citeturn23search6turn21view3

**ResNet-50 vs ViT を、同じ surgical corpus・同じ SSL loss・同じ augmentation・同じ parameter budget で比較した実験。** GastroNet の ResNet50/ViT-S、LEMON の ConvNeXt/ViT、SurgeNetXL の ConvNeXt/PVTv2/CAFormer は近いが、要求を完全に満たす ResNet50-vs-ViT controlled study は見つからなかった。citeturn19view2turn23view12turn18view2

**AVOS の原典と view composition。** SurgMotion Table 1 に AVOS が出現することは確認したが、この検索実行では AVOS の原 dataset paper、DOI/arXiv ID、open/endoscopic/third-person の内訳を原典まで追い切れなかった。従って SurgMotion の「open surgery 割合」を EgoSurgery 以外まで推測して計算していない。citeturn4view1

なお、会議・誌別には MICCAI、CVPR、NeurIPS、MedIA、npj Digital Medicine、IJCARS の関連原著を本文まで確認した。一方、**IPCAI、ICCV、ECCV、ICLR、IEEE TMI の2024–2026全号を venue-by-venue で完全走査するところまでは、この実行では完了していない**。したがって「存在しない」と断言するのではなく、上記の未発見事項は「本検索 corpus 内では未発見」と解釈すべきである。

## 未検証の組み合わせ

文献を並べると、EgoSurgery に対して特に大きな空白がいくつか見える。

**最も大きい空白は、general FM・surgical FM・egocentric FM を同一 five-fold video split で比較する実験である。** 現状、GGMAE は target-domain masking comparison、SurgMotion は frozen attentive probing、EndoViT/SelfSupSurg は laparoscopic data、EgoVLP は非医療 egocentric data と評価規約が分断されている。DINOv3 が SurgMotion Table 3 で強いことは分かるが、full fine-tune まで行った clean five-fold EgoSurgery comparison はない。citeturn3view6turn23view22turn2view6

**DINOv3 → EgoSurgery train-fold-only SSL continuation** は未検証である。SelfSupSurg は ImageNet-supervised initialization から surgical SSL を続ける価値を示し、SurgeNetXL も ImageNet initialization → surgical DINO を採るが、DINOv3 の強い representation を EgoSurgery の十数本だけでさらに domain-adapt した実験はない。citeturn14view1turn18view2

**V-JEPA 2 → EgoSurgery** もほぼ空白である。SurgMotion は JEPA 系だが EgoSurgery を含む大規模 surgical corpus で新規 pretrain した別モデルであり、公開 V-JEPA 2 weight を clean に frozen/fine-tune した比較ではない。citeturn22view1turn4view1

**VideoMAE V2 の published general checkpoint → EgoSurgery** と **EgoSurgery-only VideoMAE V2 SSL** の直接比較もない。GGMAE paper の VideoMAE V2 row は後者側に近く、「一般動画大量 pretraining の価値」と「target-domain SSL objective の価値」を分離できない。citeturn3view5turn3view6

**EgoVLP/EgoVLPv2 → open surgery** は未検証である。これは「手術ドメインは違うが camera/viewpoint は近い」pretraining と、「手術ドメインは近いが endoscope viewpoint は違う」pretraining のどちらが有利かを直接比較できる重要な空白である。citeturn23search0turn23search8

**gaze-guided SSL を strong pretrained initialization から開始する実験**も見つからない。GGMAE は gaze の純粋効果に近い +3.3 Jaccard を示すが、SelfSupSurg が重要だとした ImageNet initialization や、DINOv3/V-JEPA2 の強い initialization と組み合わせた結果はない。citeturn4view0turn14view1

**gaze と motion の factorial comparison**、すなわち random / gaze / motion / gaze+motion を backbone・mask ratio・training compute 固定で比べた研究も未発見である。GGMAE と SurgMotion はそれぞれ positive result を持つが、モデルと loss が違いすぎて prior 自体を比較できない。citeturn4view0turn3view1

**open-egocentric surgery に対する surgical FM の full fine-tuning**はほぼ空白である。SurgMotion Table 3 で EndoViT、EndoFM、GSViT、SurgeNetXL 等の frozen transfer は比較できるが、fine-tuning によって domain gap が縮まるかは分からない。citeturn23view22turn2view6

**microscopic surgery transfer**も十分でない。SurgVISTA は pretraining から完全分離した ophthalmic/cataract datasets を OOD benchmark に含むため、顕微鏡・眼科方向の証拠として最も近いが、DINOv3/V-JEPA2/SurgMotion 等まで同一条件で揃えた比較ではない。citeturn22view13

**online degradation**については、同じ video FM を「未来を含む clip」と「現在までの trailing clip」で比較する実験が欠ける。従って、VideoMAE/V-JEPA2 等を online 化した際に「何 pp 落ちる」と一般化できる既存値は、この検索では得られなかった。EndoMamba の causal design は関連するが、offline variant との完全 controlled comparison とは別である。citeturn21view3

**inductive SSL と transductive SSL の同条件比較**も EgoSurgery では未検証である。すなわち、各 fold の train videos だけで SSL する場合と、test fold もラベルを隠して SSL に使う場合を二本立てにして差を測る研究がない。SurgVISTA は前者を厳格に守る例、SurgMotion は評価 dataset が pretraining corpus に入る例であり、この対照は非常に大きい。citeturn22view13turn4view1

## 検索記録

検索日は **2026年10月5日（日本時間）**。件数は検索エンジンの raw hit 数ではなく、**重複を除いて、タイトル・要旨・本文または比較表まで確認し、本調査の判断材料として保持した文献・モデル論文の概数**である。一つの文献が複数方向に属するため方向間で重複する。

| 方向 | 主な検索語 | 保持した関連文献・原著の件数 | 結果 |
|---|---|---:|---|
| **方向1: EgoSurgery / egocentric open surgery** | `EgoSurgery Phase`, `GGMAE 2405.19644`, `EgoSurgery foundation model`, `SurgMotion EgoSurgery` | 2–3 | GGMAE と SurgMotion が中心。clean five-fold FM benchmark は未発見 |
| **方向2: 手術一般** | `surgical foundation model`, `endoscopic video foundation model`, `self-supervised surgical video`, `MICCAI surgical foundation model`, 各 seed 名 | 14以上 | Endo-FM、EndoViT、SelfSupSurg、SurgMAE、GSViT、SurgeNetXL、SurgVISTA、LEMON、EndoMamba、SurgVLP、EndoSSL、GastroNet、SurgMotion 等 |
| **方向3: 非手術 egocentric** | `EgoVLP`, `EgoVLPv2`, `Ego4D transfer`, `EPIC-KITCHENS transfer`, `egocentric pretraining surgery`, `Ego-Exo` | 4程度 | EgoVLP family は確認。surgery direct transfer は未発見。Ego-Exo は今回原典を一意確認できず |
| **方向4: 一般動画** | `VideoMAE V2`, `V-JEPA 2`, `DINOv3 video transfer`, `online action recognition causal`, `object-aware video pretraining` | 7以上 | general FM は豊富だが EgoSurgery への揃った比較が欠ける |
| **方向5: 機構一般** | `gaze guided masking`, `motion guided masking`, `object guided masking`, `saliency masking MAE`, `domain adaptation self-supervised pretraining` | 6以上 | gaze、motion、object は確認。surgical saliency-controlled study は未発見 |
| **方向6: 評価・漏れ** | `self-supervised test set leakage`, `pretraining downstream test overlap`, `surgical pretraining leakage`, 各論文の `split/test/exclude` | 3主要例 | SurgVISTA が明瞭な positive example。GGMAE/SurgMotion は重要情報が不明 |
| **方向7: 否定的結果** | 各論文の `ImageNet`, `random initialization`, `few shot`, `ablation`, `frozen`, `Table`, `negative`, `worse` | 6以上 | SelfSupSurg、EndoViT、SurgMAE/GGMAE、LEMON、SurgMotion 比較から複数の負例を確認 |

引用追跡では、SelfSupSurg から surgical-domain SSL と initialization、SurgeNetXL/SurgVISTA/SurgMotion の比較表から Endo-FM、EndoViT、GSViT、GastroNet、EndoSSL 等へ逆引きした。また dataset からの逆引きとして EgoSurgery、Cholec80、AutoLaparo、RAMIE を軸に比較表を確認した。citeturn14view0turn19view1turn23view25turn23view21

否定的結果として保持したものは少なくとも次の六系統である。**SelfSupSurg:** 一般 ImageNet SSL が supervised ImageNet より最大 −1.9 phase-F1 / −11.2 tool-mAP。**EndoViT:** full phase recognition で EndoViT が ImageNet ViT に −0.19 accuracy。**GGMAE ablation:** temperature 0.25 では Jaccard 27.2、最適 0.50 の33.9から −6.7。**SurgMAE:** EgoSurgery で VideoMAE/VideoMAE V2 より低い。**LEMON:** frozen transfer で ViT/generative objective が ConvNeXt/discriminative alternative に大きく負ける条件がある。**SurgMotion benchmark:** EndoViT、GSViT、SurgeNetXL 等が open-egocentric EgoSurgery で DINOv3 を大幅に下回る。citeturn14view0turn22search9turn4view0turn3view6turn23view12turn2view6

## あなたの解釈と提案

### 最も重要な結論

この研究条件では、**「EgoSurgery だけで最初から SSL pretraining」を第一候補にする根拠は弱い**。最も強い既存証拠はむしろ、**強い一般 weight から始めて surgical/target-domain SSL を続ける**方式である。

SelfSupSurg では surgical SSL を scratch から始めるより ImageNet fully-supervised weight から開始する方が一貫して強く、最大 +12 phase-F1 程度の initialization effect があった。SurgeNetXL も ImageNet initialization → surgical DINO という同じ思想で成功している。citeturn14view1turn18view2

したがって、21本前後しかない EgoSurgery では、研究仮説を

**「target-domain SSL は general pretraining を置き換えるか」**

よりも、

**「強い general/egocentric/surgical representation を、EgoSurgery train-fold の unlabeled video でどこまで安全に適応できるか」**

と置く方が、文献上は筋がよい。

### 第一優先で比較すべき初期値

現在の ResNet-50 ImageNet/COCO + causal temporal head を残したうえで、少なくとも次の系統を同一 five-fold protocol に入れる価値が高い。

最優先の一般 baseline は **DINOv3** である。理由は、SurgMotion の frozen attentive-probe という限定された条件ながら、EgoSurgery で DINOv3-H が F1 36.34/Jaccard 29.03 を出し、EndoFM、EndoViT、GSViT、EndoMamba、SurgeNetXL、SurgVLP を上回ったからである。これは「手術基盤モデルを使えば一般モデルより良い」と仮定してはいけないことをかなり明瞭に示している。citeturn2view6

動画モデル側では **V-JEPA 2 と VideoMAE V2** を入れるべきである。特に V-JEPA 2 は SurgMotion と思想的には近いのに、standalone public checkpoint の EgoSurgery score が存在しない。これは新規性のある比較になる。citeturn22view1turn23view21

surgical FM は少なくとも **Endo-FM、EndoViT、SurgeNetXL、LemonFM** を候補とし、SurgVISTA は実際に weight が利用可能か・license が研究目的に合うかをその時点で再確認してから入れるのがよい。Endo-FM は既存 EgoSurgery frozen transfer で surgical FM 中比較的強く、EndoViT は few-shot の挙動がよく記録され、SurgeNetXL/LemonFM は recent peer-reviewed surgical benchmark で強い。citeturn2view6turn22search9turn19view2turn21view1

さらに、**EgoVLP または EgoVLPv2**を一つは入れる価値がある。これは「semantic domain は違うが viewpoint statistics は近い」という全く別の仮説を検証するためである。endoscope-trained FM が head-mounted open surgery に弱いという SurgMotion Table 3 を踏まえると、この比較は単なる付録ではなく本質的である。citeturn2view6turn23search0turn23search8

### 対象データ SSL は「scratch」と「continued SSL」を分ける

five-fold の各 outer training fold で、少なくとも次の三つを分離すると文献上の曖昧さを解消できる。

**general weight → supervised fine-tune only** を基準とする。

**random initialization → EgoSurgery SSL → fine-tune** を「target-only SSL from scratch」とする。

**general weight → EgoSurgery SSL continuation → fine-tune** を「domain-adaptive pretraining」とする。

SelfSupSurg の結果からは、三番目が一番期待値が高い。特に ResNet-50 を残す場合には、ImageNet supervised ResNet-50 → DINO/MoCo-style EgoSurgery SSL continuation は非常に自然な比較である。citeturn14view0turn14view1

ViT 系では DINOv3、VideoMAE V2、V-JEPA2 の公開 weight を初期値にし、低 learning rate・短い target-domain SSL から始める方が、21本の動画から数百 epoch scratch pretraining するより安全と予想する。ただしこれは**提案**であり、DINOv3→EgoSurgery SSL continuation の既存実証は今回見つかっていない。

### 視線は、この研究で最も優先度の高い追加情報

視線 prior は「一般論として面白い」だけでなく、**まさに同一 dataset 上に controlled evidence が存在する**点で motion/object/saliency より優先度が高い。

GGMAE の random 90% mask 30.6 と gaze 90% mask 33.9 の差 **+3.3 Jaccard**は、今回の文献全体でもかなり直接的な prior ablation である。citeturn4view0

ただし、原 GGMAE の弱点も同時に解消すべきである。すなわち、fold-local SSL、複数 seeds、強い pretrained initialization、strict online downstream evaluation を明示する。原論文の temperature だけで 6.7 pp 振れるため、単一 hyperparameter choice・単一 seed で gaze advantage を主張するのは危険である。citeturn4view0

特に価値が高い factorial experiment は、

**random mask / gaze mask × scratch / strong-general initialization**

である。計算資源に余裕があれば motion を加え、

**random / gaze / motion / gaze+motion**

まで広げる。この設計なら「視線が効いた」のか、「単に target-domain SSL が効いた」のか、「強い initialization が支配的だった」のかを切り分けられる。

### ResNet をすぐ捨てるべきではない

既存結果からは「ViT の方が SSL に向いているから ResNet は比較不要」とは言えない。

SelfSupSurg は ResNet-50 で少数ラベル条件に明瞭な利益を出している。GastroNet の downstream comparison では ResNet50 variant が ViT-S variant より phase F1 が高い条件がある。LEMON ではさらに、同じ curated data/distillation 条件で ConvNeXt-L が ViT-L を phase で少し、segmentation では大きく上回る。citeturn14view2turn19view2turn23view12

したがって、この研究では現在の **ResNet-50 + causal temporal head を「旧式 baseline」として捨てず、強い SSL initialization を与えた ResNet 系**を残すべきである。

一方で ResNet50-vs-ViT を公平に研究テーマにするなら、architecture、parameter count、SSL objective、pretraining frames、augmentation、optimization の差が混ざりやすい。その比較は「foundation model 選び」の実用比較と、「architecture の因果効果」の mechanistic comparison を分けて報告する方がよい。

### online video model の使い方

clip-input FM を online にする際、最も明瞭な規約は、時刻 \(t\) の予測入力を

\[
[x_{t-L+1},\ldots,x_t]
\]

だけに限定する **trailing clip** とし、その clip から **時刻 \(t\)** の phase を予測することである。

この場合、VideoMAE/V-JEPA 系 encoder が clip 内で bidirectional attention を使っていても、入力 clip 全体が過去と現在のみなら online 条件には違反しない。問題になるのは、centered clip

\[
[x_{t-L/2},\ldots,x_t,\ldots,x_{t+L/2}]
\]

のように未来 frame を混ぜる場合である。

EgoSurgery は 0.5 fps なので、たとえば 10-frame clip は約20秒分の履歴に相当する。したがって clip length は単なる tensor shape ではなく、「何秒の過去情報を許すか」という causal receptive field として報告すべきである。

最低限、

**single-frame / 4 / 8 / 16 frames**

程度の trailing-window ablation を行い、同じ encoder に対して centered/offline clip も参考上限として別に測れば、既存文献に欠けている **online penalty** を直接量化できる。

その際、既存の causal temporal convolution head を保持して、frame/clip encoder だけを交換する比較と、EndoMamba/V-JEPA 型の video-native representation を直接使う比較を分けると、backbone 改善と temporal-head 改善を混同しにくい。EndoMamba が temporally causal な設計を採っていることは、この方向が技術的に現実的であることを示している。citeturn21view3

### five-fold で最も重要なのは pretraining leakage の規約

主結果は **完全 inductive protocol** にするべきである。

outer fold \(k\) について、test videos は、

**supervised labels にも使わない、SSL pretraining にも使わない、hyperparameter selection にも使わない**

とする。

つまり SSL corpus は各 fold の **outer-train videos の unlabeled frames/clips のみ**に限定する。

この原則は SurgVISTA の設計に最も近い。SurgVISTA は downstream test set を pretraining から明示的に除外し、M2CAI16/Cholec80 間の5動画の重複まで発見して test evaluation から除外している。citeturn22view13turn23view24

一方、全21 videos をラベルなしで SSL してから five-fold supervised evaluation する方式自体を「絶対にしてはいけない」と扱う必要はない。ただしそれは**別の研究設定**であり、通常の inductive evaluation ではなく **transductive/self-supervised adaptation** と明記すべきである。

有用なのは両方を測ることである。

主表を **Inductive: train-fold-only SSL** とし、追加表で **Transductive: all videos unlabeled SSL, test labels never used** を示す。

こうすれば、test video の外観分布を事前に見ることで何 pp 得をするか自体を定量化できる。SurgMotion のように downstream dataset が pretraining corpus に入る状況も、これなら曖昧な「foundation model generalization」ではなく、明示的な transductive condition として扱える。citeturn4view1

### 実験の優先順位

限られた計算資源なら、最初の比較は以下の規模で十分に研究価値が高い。

**第一群**は現行 ResNet-50/ImageNet、ResNet-50/ImageNet → EgoSurgery SSL continuation、DINOv3 frozen、DINOv3 full fine-tune。

**第二群**は Endo-FM、EndoViT、SurgeNetXL または LemonFM を同じ frozen/full-fine-tune の二条件で測る。

**第三群**は VideoMAE V2、V-JEPA2 を trailing clip で評価する。

**第四群**として EgoVLP/EgoVLPv2 を入れ、egocentric prior の価値を測る。

そのうえで最良二〜三 backbone にだけ **random masking vs gaze-guided masking** の fold-local SSL continuation を実施する。

この順なら、まず「どの initialization が強いか」を決めてから gaze experiment に進めるため、GGMAE のように mask strategy の効果と backbone/pretraining baseline の強さが同時に問題になるのを避けられる。GGMAE の gaze effect、SelfSupSurg の initialization effect、SurgMotion の DINOv3 transfer の三つを同時に踏まえた設計になる。citeturn4view0turn14view1turn2view6

### 統計の扱い

21 videos の five-fold では、**fold 差を seed 差と混ぜないこと**が重要である。

各 method について可能なら **3 seeds × 5 folds** とし、まず fold 内で seed を平均し、その後 video/fold level の paired comparison を行う。平均値だけでなく fold ごとの値を残し、最終表では mean、SD または confidence interval を報告する。

GGMAE のような数 pp の差は、temperature choice だけで 6.7 pp 振れることを考えると、単一 run では解釈が難しい。SelfSupSurg でも low-label regime では標準偏差が数 pp に達し、EndoViT の1-video segmentation では SD が10 pp程度に達する条件さえある。citeturn4view0turn14view2turn22search9

最終的には accuracy/F1/Jaccard だけでなく、**各動画を統計単位とした paired bootstrap**、各 phase の F1/Jaccard、transition 周辺と phase interior を分けた error も出すと、「SSL が背景・術野認識を改善したのか、工程遷移の時間的曖昧さを改善したのか」が分かりやすい。

### この調査から得られる研究仮説

現時点で最も支持される仮説は、**EgoSurgery のような21本規模の open-egocentric surgery では、domain-specificity よりも「良い initialization」と「viewpoint compatibility」の方が重要になり得る**、というものである。

その根拠は三つある。SelfSupSurg では initialization の違いが surgical SSL 自体の効果より大きい条件がある。EndoViT では domain-specific pretraining の phase-recognition 上の利益がラベル量増加とともにほぼ消える。そして SurgMotion の cross-domain table では、巨大な laparoscopic/endoscopic surgical FMs の多くが DINOv3 に大幅に負ける。citeturn14view1turn22search9turn2view6

同時に、EgoSurgery 自身には **視線という、他の surgical foundation model が持っていない非常に強い domain prior** がある。GGMAE の +3.3 Jaccard という controlled mask result は、この signal を捨てる理由がないことを示す。citeturn4view0

したがって最も情報量の多い研究設計は、**「DINOv3/V-JEPA2/一般 egocentric FM/代表的 surgical FM の clean five-fold transfer」＋「train-fold-only continued SSL」＋「gaze-guided SSL」＋「strict trailing-clip online evaluation」**を一つの factorial な研究としてまとめることである。

この組み合わせは、今回の文献を並べた限り、まだ誰も同時には測っていない。
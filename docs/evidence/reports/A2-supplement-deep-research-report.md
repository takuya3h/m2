# 欠けのある手術映像系列の時間モデルと、計算環境差による再現性変動の文献調査

本調査では、依頼者が配布物を直接確認して得た事実、すなわち「EgoSurgery の配布フレームは注釈区間だけが残り、区間境界でフレーム連番が振り直され、欠落区間の実時間長は配布物だけからは復元できない」を所与とした。原論文側で確認できるのは、元映像が 25 fps、計約 28 時間で、0.5 fps への間引き、患者顔のぼかし、その他の個人情報を含むフレームの除外を経て約 15 時間、21 動画・27,694 注釈フレーム・9 工程になったところまでである。したがって、「配布物での注釈区間間の連番リセット」は原論文の記述と混同しない。citeturn12view0

以下の「件数」は検索エンジンの生のヒット数ではなく、本文・要旨・公式ページのいずれかまで確認し、当該方向に関連すると判定したユニーク資料数である。既に依頼者が保有している文献は系統表には含めるが、指定どおり個別の記録ブロックは作らない。

## 系統表

| 系統 | 代表的・既存の文献 | 現役度と対象 | 下の新規記録 |
|---|---|---|---:|
| **EgoSurgery 系列そのもの** | *EgoSurgery-Phase* (arXiv:2405.19644)、*EgoSurgery-Tool* (2406.03095)、*EgoSurgery-HTS* (2503.18755)、*SurgMotion* (2602.05638)、公式 `Fujiry0/EgoSurgery` | **新興：EgoSurgery benchmark**。Phase 論文は 2024 年 MICCAI、21 動画・15 h・9 phase の基準を定義。公式 repository も現在の配布窓口。citeturn12view0turn12view1 | 0 |
| **手術映像の OOB・プライバシー除去・不連続区間** | OoBNet、MultiBypass140、ROBAN、Zohar et al. MIDL 2020、Rivoir et al. *On the Pitfalls of Batch Normalization for End-to-End Video Learning*、Bayat et al. | **定番の基準＋不明：腹腔鏡 workflow**。OOB が通常の phase 系列に割り込むという問題設定は複数文献に存在するが、「未知長の削除区間で state を carry/reset」という比較は確認できなかった。Bayat et al. は OOB が temporal model を害することを明示する。citeturn14search23 | 2 |
| **因果 TCN・online phase/action segmentation** | TeCNO、MS-TCN (arXiv:1903.01945)、MiniROAD、OnlineTAS (2411.01122)、AHA (2509.16421)、StableSPR | **MS-TCN は定番の基準、2024–26 の online 系は新興**。StableSPR は MICCAI 2026 で three online SPR backbones に temporal-stability 機構を適用。citeturn14search1turn15view3 | 1 |
| **一般映像の temporal corruption / dropped-frame robustness** | Zeng et al. CVPR 2024 | **定番化途上：THUMOS14-C / ActivityNet-C**。七つの TAD 系を missing/black/blur/packet-loss 型の時間破損で比較しており、本調査では欠損フレームに対する最も直接的な一般映像証拠。citeturn17view0 | 1 |
| **一人称の長時間手順・多尺度文脈** | Ego-Exo4D (2311.18259)、Ego-METAS (2606.02246)、Transformer-XL (1901.02860)、INTRADoc (2402.13991)、KORMo (2510.09426) | **Transformer-XL は長文脈の定番、Ego-METAS/KORMo は新興**。ただし、EgoSurgery 型の「消去した実時間区間」の carry/reset 比較ではない。Ego-METAS は sampling rate と Edit の関係を実験しており評価面で重要。 | 0 |
| **elapsed-time を入れる RNN・集合・時間埋込み** | GRU-D (1606.01865)、T-LSTM、mTAN、SeFT、Time2Vec | **GRU-D は定番の基準、mTAN は継続参照、T-LSTM/SeFT/Time2Vec の現役度は benchmark 依存**。2026 年の irregular-time 文献も GRU-D/mTAN を系譜として扱う。citeturn19view0turn20view3 | 4 |
| **ODE・CDE による連続時間 state evolution** | Latent ODE / ODE-RNN、GRU-ODE-Bayes、Neural CDE | **定番の基準：irregular time series**。2026 年の MASCIT/TIDES でも比較・関連研究として扱われる。citeturn19view0turn19view1 | 3 |
| **不規則時刻 Transformer / graph attention** | RAINDROP、ContiFormer | **RAINDROP は定番の比較対象、ContiFormer は比較的新しい連続時間 Transformer 系**。MASCIT の Table 2 は Raindrop を含む 12 baseline を再比較している。citeturn20view3 | 2 |
| **continuous / selective state-space model** | S5、SurgicalMamba (2605.14889)、TIDES、MASCIT | **S5 は定番の基準、SurgicalMamba/TIDES/MASCIT は新興**。S5 は continuous-time discretization の Δ に実時間間隔を与えられることが 2026 年の TIDES で明示的に再整理されている。citeturn19view0turn19view2 | 3 |
| **segment/boundary 評価** | MS-TCN の Edit・F1@k、*Metrics Matter in Surgical Phase Recognition* (2305.13961)、C2F-TCN (2212.11078)、StableSPR の TFI、Ego-METAS | **定番の評価＋新興指標**。StableSPR は Edit が segment 内の時間的不安定性を区別できない具体例を示し TFI を導入。citeturn15view2turn15view4 | 0（StableSPR は上で計数） |
| **乱数・GPU・tooling による学習変動** | Zhuang et al. (2106.11872)、Summers & Dinneen (2103.04514)、Pham et al. ASE 2020、Bouthillier et al. (2103.03098)、Jordan (2304.01910)、Gundersen et al. (2204.07610)、Chen et al.、DEVIATE、Coakley et al. | **定番の基準：DL reproducibility**。2025 年の RepDL も Pham、Summers、Zhuang、Chen を問題設定の主要先行研究として列挙する。citeturn22search6 | 5 |
| **決定性・浮動小数点の再現性** | Zhuang et al.、Chen et al.、Shanmugavelu et al.、RepDL | **定番＋新興**。従来の deterministic-kernel patch は相当な計算費用があり、RepDL は別方向から bitwise reproducibility を狙う。citeturn23view4turn22search2 | 2 |
| **画像 decode・resize・JPEG と評価実装** | Parmar et al. *clean-fid* (2104.11222) | **画像生成評価では定番、手術工程認識への外挿は不明**。decord/PyAV/torchvision/OpenCV や JPEG 再圧縮だけを変え、同じ手術動画モデルを再学習した定量研究は確認できなかった。 | 0 |
| **手術モデル自身の再現性・seed 感度** | Renard et al. DOI 10.1038/s41598-020-69920-0、*Metrics Matter in Surgical Phase Recognition*、CPKD (2507.03295)、C2F-TCN | **比較・再現性資料として現役度は benchmark 依存**。seed や split の問題は扱われるが、「同じ seed を GPU/CUDA だけ変えて対応づける」実験は今回確認できなかった。 | 0 |

重要な整理として、**S5 は実在する**。*Simplified State Space Layers for Sequence Modeling*, arXiv:2208.04933、ICLR 2023 である。さらに TIDES は S5 を「physical Δ を continuous-time discretization に保持する SSM」として明示的に位置づけ、不規則 timestamp を自然に扱える一方、LTI の表現力制約があると論じている。citeturn19view2turn19view0

種として挙げられた **mTAN、Latent ODE / ODE-RNN、GRU-ODE-Bayes、Neural CDE、Raindrop、ContiFormer、SeFT、Time2Vec、T-LSTM、S5、Towards Training Reproducible Deep Learning Models、DEVIATE は実在を確認した**。citeturn2search0turn2search1turn2search2turn2search3 citeturn3search0turn3search1turn3search2turn19view2 citeturn13search1turn22search0turn23search13  
一方、**Metrics Reloaded は今回取得できた一次資料の範囲で独立の書誌確認を完了できなかったため、以下では「実在を確認できず」として効果量を使用しない**。

## 文献ごとの記録

### 欠け・不連続な手術映像に直接近い文献

#### Bayat et al. — *Robustness Against Out of Distribution Video Frames in Online Surgical Workflow Recognition with Temporal Convolutional Networks*

- **著者／年／題名／掲載先／ID:** Amirhossein Bayat, Kadir Kirtac, Salih Karagoz, Julien Schwerin, Michael Stenzel, Marco Smit, Florian Aspart／2022／*Robustness Against Out of Distribution Video Frames in Online Surgical Workflow Recognition with Temporal Convolutional Networks*／MIDL 2022 short paper。DOI・arXiv ID は確認できず、**ID 不明**。MIDL 公式プログラム上の掲載は確認できた。citeturn14search23
- **読んだ範囲:** 要旨のみ。OpenReview の PDF 本文は browser verification により今回取得不能だった。citeturn15view0turn15view1
- **方向:** 手術一般、否定的結果。
- **視点:** 内視鏡・腹腔鏡。
- **ドメイン:** 低侵襲手術。
- **課題の形:** laparoscopic cholecystectomy の frame features を temporal convolutional network に与える online surgical phase/workflow recognition。OOB frame が途中に挿入される real-world 条件を扱う。citeturn14search23
- **推論の規約:** online。
- **データ規模:** “large scale real-world dataset” までは要旨で確認できるが、本数・時間・クラス数は本文未取得のため不明。
- **モデルの状態:** spatial extractor＋temporal model の二段構成。凍結範囲の詳細は不明。
- **系統:** 手術 OOB・不連続系列。
- **現役度:** 不明。近い問題設定の代表例だが、直近二年の複数比較表で基準として使われることまでは確認できず。
- **ベンチマーク:** proprietary/real-world laparoscopic cholecystectomy dataset。詳細不明。
- **少数動画・online・一人称:** online は該当。少数動画、一人称は不明・非該当。
- **何と何を比べた差か:** 標準の二段 phase model と、OOB に対して robustify した提案方式。ただし本文未読のため正確な arm 定義は不明。
- **効果量:** 本文表番号を確認できないため数値を採用しない。
- **符号:** 改善と著者要旨は述べるが、効果量不明。
- **符号や大きさが変わる条件:** 不明。
- **基準の強さ:** 不明。
- **その要素だけを変えた比較か:** 不明。
- **seed／分割／検定:** 不明。
- **著者以外による追試:** 確認できず。
- **コード・重み・ライセンス:** 確認できず。
- **追加データ:** OOB の扱いが必要。追加注釈の詳細不明。
- **事前学習データの重複:** 不明。
- **一行の要点:** **「外に出たフレームをただ通常系列として時間モデルへ流すと性能を害する」という、EgoSurgery の人工的な区間接続に最も近い手術側の証拠だが、carry と reset の直接比較ではない。** citeturn14search23

#### Liu et al. — *Stabilizing Temporal Inference Dynamics for Online Surgical Phase Recognition*

- **著者／年／題名／掲載先／ID:** Yang Liu, Ning Zhu, Jingjing Peng, Xiwu Chen, Alejandro Granados, Guotai Wang, Sébastien Ourselin／2026／*Stabilizing Temporal Inference Dynamics for Online Surgical Phase Recognition*／MICCAI 2026、査読つき。arXiv:2605.16387。MICCAI ページでは proceedings DOI は調査時点で pending。citeturn14search1turn16view2
- **読んだ範囲:** 本文。
- **方向:** 手術一般、方法論、否定的結果。
- **視点:** 腹腔鏡。
- **ドメイン:** 低侵襲手術。
- **課題の形:** online surgical phase recognition の temporal error cascade と短時間の phase flicker を、training loss の TEC と causal inference mechanism の EGTP で抑制。citeturn16view2
- **推論の規約:** online、過去のみ。
- **データ規模:** Cholec80 80 videos・7 phases、40 train/40 test。AutoLaparo 21 videos・7 phases、10 train/4 validation/7 test。citeturn15view3
- **モデルの状態:** Trans-SVNet、SKiT、Surgformer の公式実装に plug-in。
- **系統:** causal temporal-state stabilization。
- **現役度:** **新興**。2026 年 MICCAI 採択で著者以外の追試はまだ限定的。
- **ベンチマーク:** Cholec80、AutoLaparo。
- **少数動画・online・一人称:** AutoLaparo は 21 動画、online。非一人称。
- **何と何を比べた差か:** 同一 backbone に TEC、EGTP、両方を追加する ablation。citeturn15view3turn15view4
- **効果量:** Table 1 で、Cholec80 の Trans-SVNet は baseline **Accuracy 88.61 / Edit 12.54 / TFI 6.42** に対し TEC+EGTP は **89.13 / 54.97 / 1.16**。AutoLaparo の同 backbone は **80.16 / 2.94 / 18.80** から **83.79 / 55.60 / 0.26**。これは「欠落区間 reset」の比較ではなく、同じ online temporal state のエラー伝播抑制比較である。citeturn15view3
- **符号:** temporal stability は改善。
- **符号や大きさが変わる条件:** Table 2 では TEC の α により Accuracy、Edit、TFI の最良値が一致しない。例えば AutoLaparo Trans-SVNet の α=3 と α=11 は Edit がほぼ同程度でも TFI の順位が異なる。citeturn15view4
- **基準の強さ:** 三つの代表的 online SPR backbone。
- **その要素だけを変えた比較か:** ablation では TEC/EGTP を同 backbone に追加している。
- **seed／分割／検定:** 読んだ本文範囲では seed 数・有意差検定を確認できず。
- **著者以外による追試:** 2026 年時点では確認できず。
- **コード・重み・ライセンス:** MICCAI 公式ページから StableSPR repository へのコードリンクあり。ライセンスは今回未確認。citeturn14search1
- **追加データ:** 追加注釈なし。
- **事前学習重複:** 不明。
- **一行の要点:** **online phase model の過去 state は誤りを前方へ伝播し得るため、「不自然な区間境界を越えて state を持たせることは無害」とは仮定できない。**ただし gap reset 自体は測っていない。citeturn16view2

### 一般映像の欠損・フレーム破損

#### Zeng et al. — *Benchmarking the Robustness of Temporal Action Detection Models Against Temporal Corruptions*

- **著者／年／題名／掲載先／ID:** Runhao Zeng, Xiaoyong Chen, Jiaming Liang, Huisi Wu, Guangzhong Cao, Yong Guo／2024／*Benchmarking the Robustness of Temporal Action Detection Models Against Temporal Corruptions*／CVPR 2024、査読つき。arXiv:2403.20254。citeturn16view1
- **読んだ範囲:** 本文。
- **方向:** 一般映像、方法論、否定的結果。
- **視点:** 三人称・一般映像。
- **ドメイン:** 非医療。
- **課題の形:** untrimmed video の temporal action detection。black frame、motion blur、overexposure、occlusion、packet loss を一部フレームに入れ temporal continuity を破る。citeturn17view0
- **推論の規約:** benchmark に causal 制約はなく、EgoSurgery の online 条件とは異なる。
- **データ規模:** THUMOS14-C は annotated test 213 videos、20 sports classes。ActivityNet-v1.3-C は約 5K validation videos、200 activities。citeturn17view0
- **モデルの状態:** BasicTAD、E2E-TAD、TemporalMaxer、ActionFormer、AFSD、TriDet、VSGN。end-to-end と fixed feature extractor の双方。citeturn17view0
- **系統:** temporal corruption robustness。
- **現役度:** **定番の基準に近いが、複数直近論文での採用確認が不足するため不明**。
- **ベンチマーク:** THUMOS14-C、ActivityNet-v1.3-C。
- **少数動画・online・一人称:** いずれも非該当。
- **何と何を比べた差か:** 同一 trained detector の clean test と、5 種×3 severity の corrupted test。さらに FrameDrop+TRC training を同 model に追加。citeturn17view0
- **効果量:** Table 1、THUMOS14-C。ActionFormer+I3D は clean mAP **61.53** から corrupted **50.61**、差 **−10.92**。TriDet+VideoMAEv2 は **75.16** から **61.10**、差 **−14.06**。同 TriDet に robust training を加えると corrupted mAP **68.28**、clean **75.60**。Table 2 の ActivityNet-v1.3-C でも ActionFormer+TSP は **36.50→27.79**。citeturn17view0
- **符号:** corruption は悪化、robust training は改善。
- **符号や大きさが変わる条件:** Figure 5 では corruption が action 中央に近いほど悪化が大きい一方、**境界近傍への black-frame 挿入では clean より良くなる場合もあった**。著者は black frame を boundary cue と誤利用した可能性を挙げる。citeturn17view0
- **基準の強さ:** 当時の主要 TAD 七手法。
- **その要素だけを変えた比較か:** corruption test は trained model を固定して入力だけを変える比較で、比較的純粋。
- **seed／分割／検定:** seed 数・統計検定は読んだ範囲で不明。
- **著者以外による追試:** 不明。
- **コード・重み・ライセンス:** code/models 公開を論文が明記。ライセンス不明。citeturn16view1
- **追加データ:** corruption は人工生成。
- **事前学習重複:** I3D、VideoMAEv2、TSP pretrained features を使う条件あり。target-set overlap の検証は不明。
- **一行の要点:** **ごく少数の異常フレームでも temporal localization は大きく揺れ、影響は corruption の位置によって符号まで変わり得る。削除 gap の影響は frame accuracy だけでは捉えにくい。** citeturn17view0

### 経過時間を明示するモデル

#### Shukla & Marlin — *Multi-Time Attention Networks for Irregularly Sampled Time Series*

- **著者／年／題名／掲載先／ID:** Satya Narayan Shukla, Benjamin M. Marlin／2021／*Multi-Time Attention Networks for Irregularly Sampled Time Series*／ICLR 2021、査読つき。arXiv:2101.10318。citeturn2search0
- **読んだ範囲:** 要旨・書誌。
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし／非映像時系列。
- **課題の形:** irregular observation の時刻を continuous-time embedding と attention で参照し、固定された参照時刻上の表現へ集約して分類・補間を行う。citeturn2search0
- **推論の規約:** 原論文の主要評価は strict online framewise recognition ではない。
- **データ規模:** 本文表を未確認のため不明。
- **モデルの状態:** end-to-end。
- **系統:** time-aware attention。
- **現役度:** 不明。ただし 2026 年 TIDES が irregular-time 系譜の代表としてなお引用する。citeturn19view0
- **ベンチマーク:** irregular clinical/time-series benchmarks。詳細不明。
- **少数動画・online・一人称:** 該当なし。
- **比較／効果量:** 本文表番号を未確認のため数値を記載しない。
- **符号:** 著者要旨では irregular sampling に有効。
- **条件変化／基準の強さ／単独比較:** 不明。
- **seed／分割／検定:** 不明。
- **追試:** TIDES など後続が方法系譜として採用。
- **コード・重み・ライセンス:** 今回未確認。
- **追加データ:** **観測時刻が必要**。
- **事前学習重複:** 該当なし。
- **一行の要点:** EgoSurgery で実 gap 長が失われている場合、mTAN の主要な情報源である「実時刻」そのものを復元できない点が適用上の制約になる。

#### Baytas et al. — *Patient Subtyping via Time-Aware LSTM Networks*

- **著者／年／題名／掲載先／ID:** İnci M. Baytas, Cao Xiao, Xi Zhang, Fei Wang, Anil K. Jain, Jiayu Zhou／2017／*Patient Subtyping via Time-Aware LSTM Networks*／KDD 2017、査読つき。DOI:10.1145/3097983.3097997。citeturn13search1turn13search5
- **読んだ範囲:** 要旨・書誌。
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし／医療 EHR。
- **課題の形:** LSTM の過去 memory を elapsed time に応じて decay させ、不規則な訪問間隔を扱う。citeturn13search0turn13search1
- **推論の規約:** causal recurrence の形だが、EgoSurgery の framewise online benchmark ではない。
- **データ規模:** 本文未確認のため不明。
- **モデル状態:** end-to-end。
- **系統:** elapsed-time recurrent decay。
- **現役度:** 不明。概念的基準としては存続するが、直近二年の複数比較表での採用を本調査では確認できず。
- **効果量:** 表番号未確認のため記載しない。
- **符号・条件:** 実時間 gap を入力できることが前提。
- **seed／分割／検定:** 不明。
- **追試:** elapsed-time RNN の先行例として後続文献で広く参照。
- **コード・重み・ライセンス:** 不明。
- **追加データ:** timestamp / elapsed time。
- **事前学習:** 該当なし。
- **一行の要点:** **「欠けの長さ」を state decay に変える型の代表例であり、gap 長が未知なら同じ意味での適用はできない。**

#### Kazemi et al. — *Time2Vec: Learning a Vector Representation of Time*

- **著者／年／題名／掲載先／ID:** Kazemi et al.／2019／*Time2Vec: Learning a Vector Representation of Time*／preprint。arXiv:1907.05321。citeturn3search22
- **読んだ範囲:** 要旨・書誌。
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし。
- **課題の形:** scalar time を学習可能な周期・非周期成分を持つ vector embedding に変換し、既存 sequence model に時刻情報として付加する。
- **推論の規約:** backbone 依存。
- **データ規模:** 不明。
- **モデル状態:** 時刻 encoder を jointly train。
- **系統:** explicit timestamp positional encoding。
- **現役度:** 不明。
- **ベンチマーク／少数動画条件:** EgoSurgery での測定なし。
- **効果量:** 表未読のため記載しない。
- **seed／統計:** 不明。
- **コード・重み・ライセンス:** 不明。
- **追加データ:** timestamp が必要。
- **事前学習:** 該当なし。
- **一行の要点:** フレーム番号ではなく実時刻を position として与える発想は該当するが、現在の EgoSurgery 配布物では unknown gap を表現する絶対時刻が欠ける。

#### Horn et al. — *Set Functions for Time Series*

- **著者／年／題名／掲載先／ID:** Max Horn et al.／2020／*Set Functions for Time Series*／ICML 2020、査読つき。arXiv:1909.12064。citeturn3search2
- **読んだ範囲:** 要旨。
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし／非映像 irregular time series。
- **課題の形:** irregular observations を集合として符号化し、固定 grid の sequential interpolation を必須としない。
- **推論の規約:** online monitoring に展開可能とされるが、主要 benchmark の strict causal 条件は不明。citeturn3search2
- **データ規模:** 不明。
- **モデル状態:** end-to-end。
- **系統:** set-based irregular-time representation。
- **現役度:** 不明。
- **効果量・seed・検定:** 本文未読のため不明。
- **コード／ライセンス:** 不明。
- **追加データ:** observation time を保持する形式が基本。
- **一行の要点:** 「観測が無い時間」を無理に通常 timestep へ詰めない設計系統だが、時間位置そのものを失った EgoSurgery では情報が不足する。

### 連続時間 ODE・CDE

#### Rubanova et al. — *Latent ODEs for Irregularly-Sampled Time Series*

- **著者／年／題名／掲載先／ID:** Yulia Rubanova, Ricky T. Q. Chen, David Duvenaud／2019／*Latent ODEs for Irregularly-Sampled Time Series*／NeurIPS 2019、査読つき。arXiv:1907.03907。citeturn2search1
- **読んだ範囲:** 要旨。
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし。
- **課題の形:** ODE-RNN は観測間を ODE で連続的に発展させ、観測時に recurrent update。Latent ODE は latent trajectory 自体を連続時間で表す。citeturn2search1
- **推論規約:** ODE-RNN 部分は causal 構成可能。Latent ODE の inference network は用途により full sequence を見るため、原論文全体を EgoSurgery の online と同一視できない。
- **データ規模:** 不明。
- **モデル状態:** jointly train。
- **系統:** continuous-time latent dynamics。
- **現役度:** **定番の基準に近い**。TIDES 2026 でも irregular-time の代表として参照される。citeturn19view0
- **効果量:** 表番号未確認のため記載しない。
- **seed／統計:** 不明。
- **コード・ライセンス:** 不明。
- **追加データ:** observation timestamps。
- **一行の要点:** gap の長さが分かるなら「何も観測されなかった時間だけ state を時間発展させる」ことができるが、gap 時間が失われていればその利点は使えない。

#### De Brouwer et al. — *GRU-ODE-Bayes: Continuous Modeling of Sporadically-Observed Time Series*

- **著者／年／題名／掲載先／ID:** Edward De Brouwer, Jaak Simm, Adam Arany, Yves Moreau／2019／*GRU-ODE-Bayes: Continuous Modeling of Sporadically-Observed Time Series*／NeurIPS 2019、査読つき。arXiv:1905.12374。citeturn2search2
- **読んだ範囲:** 要旨。
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし。
- **課題:** continuous GRU dynamics を観測間で進め、観測時に Bayesian update。
- **推論規約:** causal な filtering 形式に近い。
- **データ規模／効果量／seed:** 本文表未確認につき不明。
- **モデル状態:** jointly train。
- **系統:** continuous recurrent filtering。
- **現役度:** 不明。
- **少数動画／online／一人称:** online の考え方には近いが映像 benchmark なし。
- **基準・単独比較・追試:** 本調査では詳細未確認。
- **コード／ライセンス:** 不明。
- **追加データ:** timestamp。
- **一行の要点:** 「空白時間を continuous dynamics として進める」という点で carry/reset の中間を構成できるが、真の Δ が必要。

#### Kidger et al. — *Neural Controlled Differential Equations for Irregular Time Series*

- **著者／年／題名／掲載先／ID:** Patrick Kidger, James Morrill, James Foster, Terry Lyons／2020／*Neural Controlled Differential Equations for Irregular Time Series*／NeurIPS 2020、査読つき。arXiv:2005.08926。citeturn2search3
- **読んだ範囲:** 要旨。online prediction への派生論文 *Neural CDEs for Online Prediction Tasks*、arXiv:2106.11028 も確認。citeturn2search30
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし。
- **課題:** timestamped observations を補間 path として扱い、その path により hidden state を連続的に駆動する。
- **推論規約:** original は用途依存。派生研究には明示的 online prediction がある。citeturn2search30
- **データ規模:** 不明。
- **モデル状態:** jointly train。
- **系統:** controlled differential equation。
- **現役度:** **定番の基準**。MASCIT 2026 Table 2 が NCDE を irregular-time neural baseline として比較する。citeturn20view3
- **効果量:** 今回は元論文の表番号を確認していないため記載しない。
- **seed／検定:** 不明。
- **追試:** 2026 benchmark で採用あり。citeturn20view3
- **コード・ライセンス:** 不明。
- **追加データ:** timestamp。
- **一行の要点:** continuous-time かつ online へ展開できる系統だが、やはり「何秒欠けたか」を保持していることが前提になる。

### Graph / Transformer による irregular-time modeling

#### Zhang et al. — *Raindrop: A Graph-Guided Network for Irregularly Sampled Multivariate Time Series*

- **著者／年／題名／掲載先／ID:** Zhang et al.／2022／*Raindrop: A Graph-Guided Network for Irregularly Sampled Multivariate Time Series*／ICLR 2022、査読つき。arXiv:2110.05357。citeturn3search0
- **読んだ範囲:** 要旨。
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし。
- **課題:** asynchronously observed multivariate channels の時刻・センサ関係を graph-guided attention で統合。
- **推論規約:** sequence classification であり、strict framewise online ではない。
- **データ規模:** 本文未確認。
- **モデル状態:** jointly train。
- **系統:** irregular-time graph attention。
- **現役度:** **定番の基準**。MASCIT 2026 Table 2 で比較対象。citeturn20view3
- **効果量:** MASCIT の Table 2 では、34 irregular datasets の available-case average macro-F1 が Raindrop **55.232**、MASCIT **69.200**。これは MASCIT と既発表 baseline の benchmark-level 比較であり、「時間 gap の与え方だけ」を変えた比較ではない。citeturn20view3
- **符号:** MASCIT aggregate comparison では低い。
- **条件変化:** dataset composition に依存する。
- **seed／分割／検定:** MASCIT 側は benchmark-recommended setting、stochastic neural methods は 3 runs。citeturn20view3
- **コード・ライセンス:** 今回未確認。
- **追加データ:** irregular timestamps / sensor identity。
- **一行の要点:** timestamp-aware attention の候補系統ではあるが、EgoSurgery の単一 video feature stream とは観測構造がかなり異なる。

#### *ContiFormer: Continuous-Time Transformer for Irregular Time Series Modeling*

- **著者／年／題名／掲載先／ID:** 著者は今回の取得結果では完全列を再確認できず／2023–24／*ContiFormer: Continuous-Time Transformer for Irregular Time Series Modeling*／NeurIPS 系論文として確認、arXiv:2402.10635。citeturn3search1
- **読んだ範囲:** 要旨。
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし。
- **課題:** Transformer attention を continuous-time representation に拡張して irregular timestamp を扱う。
- **推論規約:** 原 benchmark は strict online video recognition ではない。
- **データ規模／モデル状態:** 詳細不明。
- **系統:** continuous-time Transformer。
- **現役度:** 不明。
- **効果量／seed／検定:** 本文表未確認につき記載しない。
- **コード／ライセンス:** 不明。
- **追加データ:** timestamps。
- **一行の要点:** 多尺度/Transformer を調べる際、「token index」ではなく physical time を attention に反映する系統が存在する。

### State-space model

#### Smith et al. — *Simplified State Space Layers for Sequence Modeling*

- **著者／年／題名／掲載先／ID:** Jimmy T. H. Smith, Andrew Warrington, Scott W. Linderman／2023／*Simplified State Space Layers for Sequence Modeling*／ICLR 2023、査読つき。arXiv:2208.04933。citeturn18search28turn19view2
- **読んだ範囲:** 要旨、実装 appendix、後続 TIDES による機構比較。
- **方向:** 機構の一般論。
- **視点／ドメイン:** 該当なし。
- **課題:** S4 の多数の SISO SSM を一つの MIMO continuous-time SSM に整理し、parallel scan を使う。citeturn19view2
- **推論規約:** recurrence として causal state update が可能。ただし原 benchmark は surgical online recognition ではない。
- **データ規模:** Long Range Arena 等。ここでは表番号を再読していないため数値不記載。
- **モデル状態:** jointly train。
- **系統:** continuous-time SSM。
- **現役度:** **定番の基準**。TIDES 2026 が S5 を直接 baseline/機構比較に使用する。citeturn19view0turn20view0
- **ベンチマーク:** LRA ほか。
- **少数動画・online・一人称:** benchmark 上は非該当。
- **何と何を比べた差か:** original は S4 等との sequence-model comparison。EgoSurgery gap は未評価。
- **効果量:** 本調査では表番号付きで再確認していないため省略。
- **符号や条件:** TIDES の解析では S5 は physical Δ を保持して irregular intervals に extrapolate する一方、LTI のため input-conditional dynamics を表せないという否定的側面が示される。citeturn20view1
- **seed／検定:** original は今回未確認。
- **コード:** JAX implementation が appendix にある。ライセンス詳細は不明。citeturn18search4
- **追加データ:** irregular sampling として使う場合は **真の Δ**。
- **一行の要点:** **S5 は「不規則サンプリングを物理的な timestep として state transition に入れる SSM」という種として実在する。**

#### Soydan et al. — *TIDES: Implicit Time-Awareness in Selective State Space Models*

- **著者／年／題名／掲載先／ID:** Taylan Soydan, Miguel A. Bessa, Dirk Mohr, Rui Barreira／2026／*TIDES: Implicit Time-Awareness in Selective State Space Models*／preprint。arXiv:2605.09742。citeturn18academia33
- **読んだ範囲:** 本文。
- **方向:** 機構の一般論、否定的結果。
- **視点／ドメイン:** 該当なし。
- **課題:** S5 の physical Δ と Mamba の input-dependent selectivity を両立させる selective SSM。Δ を learned gate にせず実観測間隔のまま discretization に使う。citeturn19view0
- **推論規約:** causal recurrence が可能。classification/regression benchmark 自体は framewise online ではない。
- **データ規模:** UEA classification、Physiome-ODE、および controlled Fading Flash。
- **モデル状態:** jointly train。
- **系統:** time-aware selective SSM。
- **現役度:** **新興**。
- **ベンチマーク:** UEA、Physiome-ODE、Fading Flash。
- **少数動画・online・一人称:** 非該当。
- **何と何を比べた差か:** matched parameter-count の S5、Mamba 系、TIDES に対して irregular Δ の in-distribution / out-of-distribution extrapolation を比較。citeturn20view1
- **効果量:** Appendix D / Figure 7 に対応する Fading Flash sweep で、test Δ=0.1 の relative error は **TIDES 6.56、Mamba-3 141.20、Mamba-2 154.08**。この controlled diagnostic は **seed 0 の一回**である。citeturn20view1
- **符号:** TIDES は改善。S5 は Δ extrapolation は保つが zone-dependent decay の表現力不足、Mamba は training Δ 範囲外で誤差が急増するという、二種類の否定的結果。citeturn20view1
- **条件変化:** test-time Δ が training distribution から外れるかどうか。
- **基準の強さ:** S5、Mamba-2/-3 等。
- **単独比較:** controlled toy experiment では比較的明確。
- **seed／分割／検定:** Fading Flash は seed 0。UEA/Physiome tables は **5 independent runs の mean±SD**。citeturn20view0
- **追試:** 2026 preprint のため著者外追試は限定的。
- **コード／ライセンス:** repository 公開を本文が明記。ライセンス不明。citeturn19view0
- **追加データ:** **実 timestamp から得る Δ が必要**。
- **一行の要点:** **Mamba 型 SSM に「経過時間」という名前の scalar を単純追加すれば S5 と同等になるわけではなく、Δ を state discretization の物理量として使うかが別問題である。**

#### Jung et al. — *MASCIT: A Mask-Aware State Space Classifier for Naturally Irregular Time Series*

- **著者／年／題名／掲載先／ID:** Yoo-Min Jung, Hyeon-Gi Kim, Jonghun Park／2026／*MASCIT: A Mask-Aware State Space Classifier for Naturally Irregular Time Series*／preprint。arXiv:2609.34409。citeturn18academia34
- **読んだ範囲:** 本文。
- **方向:** 機構の一般論、否定的結果。
- **視点／ドメイン:** 該当なし。
- **課題:** observation mask を selective SSM と pooling に与え、missing/uneven/ragged time series を classification。citeturn19view1
- **推論規約:** backbone は shallow unidirectional だが、classification は sequence-level pooling 後なので EgoSurgery の per-frame online output とは異なる。
- **データ規模:** PYRREGULAR の 34 datasets、12 published baselines。citeturn20view3
- **モデル状態:** jointly train。
- **系統:** mask-aware selective SSM。
- **現役度:** **新興**。
- **ベンチマーク:** 34 irregular time-series datasets。
- **少数動画・online・一人称:** 非該当。
- **何と何を比べた差か:** MASCIT と KNN/SVM/LGBM/ROCKET/BORF/RIFC/BRITS/GRU-D/NCDE/Raindrop/SAITS/TimesNet の benchmark comparison。さらに partial/full selectivity の factorial ablation。citeturn20view3turn20view4
- **効果量:** Table 2 の available-case average macro-F1 は MASCIT **69.200**、ROCKET **66.890**、GRU-D **42.052**、NCDE **55.232** ではなく、表列対応上 NCDE/Raindrop 等の値は個別列の読み違いを起こしやすいため、ここでは MASCIT と closest aggregate competitor ROCKET のみ採用する。平均 rank は **3.118 vs 4.118**。MASCIT vs ROCKET の Holm-corrected Wilcoxon は **p=.394** で有意ではない。citeturn20view3
- **符号:** aggregate point estimate は改善だが、ROCKET との差は統計的に有意でない。
- **条件変化:** dataset composition により ROCKET の aggregate rank が大きく変わる。partial selectivity が full selectivity より有利な傾向。citeturn20view4
- **基準の強さ:** 12 baseline を共通 benchmark で比較。
- **単独比較:** architecture 全体の差を含む。partial/full selectivity は ablation。
- **seed／分割／検定:** neural/stochastic methods は原則 3 runs、MASCIT は全 34 dataset で 3 seeds。Holm-corrected one-sided Wilcoxon。citeturn20view3
- **追試:** 発表直後で不明。
- **コード／ライセンス:** 今回確認できず。
- **追加データ:** **重要な否定条件として、この実装は elapsed-time input を使わない**。timestamps の union を連番へ compact するため、event order と mask geometry は残るが **物理的な gap 長は失われる**。著者自身がこの制約を明記する。citeturn19view1
- **一行の要点:** **EgoSurgery の配布状態に最も構造的に似た例の一つで、「実時間 gap を失った系列では mask/order は使えても physical elapsed time は回復できない」と明記している。**

### 計算環境・決定性の文献

#### Chen et al. — *Towards Training Reproducible Deep Learning Models*

- **著者／年／題名／掲載先／ID:** Boyuan Chen, Mingzhi Wen, Yong Shi, Dayi Lin, Gopi Krishnan Rajbahadur, Zhen Ming (Jack) Jiang／2022／*Towards Training Reproducible Deep Learning Models*／ICSE 2022、査読つき。arXiv:2202.02326、DOI:10.1145/3510003.3510163。citeturn22search0turn22search13
- **読んだ範囲:** 本文。
- **方向:** 機構の一般論、方法論、否定的結果。
- **視点／ドメイン:** 該当なし／一般 DL。
- **課題の形:** software RNG と GPU hardware nondeterminism を分け、record-and-replay と nondeterministic operation の deterministic patch を組み合わせる。citeturn23view3turn23view4
- **推論規約:** 学習再現性の研究。
- **データ規模:** six open-source DL models と one commercial model。GPU 実験は Tesla P100-16GB。TensorFlow 1.14 では CUDA 10.0.130/cuDNN 7.5.1、TensorFlow 2.1 では CUDA 10.1/cuDNN 7.6。各 setup 16 runs。citeturn23view3
- **モデル状態:** full training。
- **系統:** deterministic training / variance decomposition。
- **現役度:** **定番の基準**。RepDL 2025 が主要関連研究として明示的に引用。citeturn22search6
- **ベンチマーク:** LeNet variants、ResNet-38/56、WRN-28-10 ほか。
- **少数動画・online・一人称:** 非該当。
- **何と何を比べた差か:** original nondeterministic、seed/R&R による software control、deterministic patch による hardware control、および双方を制御した条件。citeturn23view3turn23view4
- **効果量:** §5.1 / Table 4 の説明で ResNet-38 の overall accuracy の著者いう “largest variance” は original **2.0%**、software randomness **1.4%**、hardware nondeterminism **1.2%**。per-class accuracy では **10.1%、6.8%、4.9%**、inconsistent predictions は **219、216、209**。したがって、この一例では hardware 由来量は software-randomness 由来量と同じ桁であり、overall の比で約 0.86、per-class で約 0.72、prediction-count で約 0.97 である。ただし **software randomness は seed だけの純粋な variance component ではない**。citeturn23view4
- **符号:** hardware nondeterminism は seed/RNG を抑えても残る。
- **符号や大きさが変わる条件:** model・metric に依存。
- **基準の強さ:** reproducibility を直接目的とした controlled experiment。
- **単独比較:** software と hardware を別 setup で遮断しており比較的明瞭。
- **seed／分割／検定:** 16 runs/setup。run pairing には seed 0 と 42 も用いる。training-time の比較には Wilcoxon rank-sum と Cliff’s delta。citeturn23view3
- **著者外追試:** RepDL など後続が問題設定を継承。
- **コード／ライセンス:** framework を提案。詳細ライセンスは今回不明。
- **追加データ:** 不要。
- **事前学習重複:** 主対象ではない。
- **決定性の費用:** Table 3 で deterministic patch+R&R の training-time overhead は著者集計で **24%〜114%**。例として ResNet-38 **1.243 h→1.561 h**、WRN-28-10 **7.08 h→14.979 h**。record-and-replay 単独の overhead は統計的有意でなかったと報告。citeturn23view4
- **一行の要点:** **hardware nondeterminism は seed variability と比べて無視できるとは限らず、同じ桁になる controlled example がある。**

#### Coakley, Kirkpatrick & Gundersen — *Examining the Effect of Implementation Factors on Deep Learning Reproducibility*

- **著者／年／題名／掲載先／ID:** Kevin Coakley, Christine R. Kirkpatrick, Odd Erik Gundersen／2022（arXiv 掲載 2023）／*Examining the Effect of Implementation Factors on Deep Learning Reproducibility*／IEEE eScience 2022。DOI:10.1109/eScience55777.2022.00056、arXiv:2312.06633。citeturn23search0turn23search17
- **読んだ範囲:** 本文 2 pages。
- **方向:** 機構の一般論、方法論。
- **課題:** hardware/software environment を変えたときの deterministic DL examples の結果変動。
- **データ規模:** three DL experiments × five repeats × 13 hardware environments × four software environments、計 780 results。citeturn23view1
- **モデル:** simple CNN/MNIST、bidirectional LSTM/IMDB、dense network/credit-card fraud detection。citeturn23view5
- **系統:** cross-environment reproducibility。
- **現役度:** **定番の基準に近い**が短報。
- **少数動画／online:** 非該当。
- **比較:** deterministic examples の hardware/software environment を変える。
- **効果量:** Abstract には environment variation だけで大きな accuracy range があったとの数値記載があるが、**対応する表番号を二頁本文内で確認できなかったため、本調査の定量効果量としては採用しない**。citeturn23view1
- **符号:** environment 変更で結果が変わる。
- **基準／単独比較:** hardware と software の両方を多環境で動かすため現実的だが、factor 間を完全に単独化した設計かは本文の短さから判断困難。
- **seed／分割／統計:** 各 experiment 五回。詳細 variance component 検定は不明。
- **コード／ライセンス:** 不明。
- **一行の要点:** **「同一コードを一台で seed 反復」だけでは環境要因を推定できない、という実験設計上の根拠になる。**

#### Shahriari, Ramler & Fischer — *How Do Deep-Learning Framework Versions Affect the Reproducibility of Neural Network Models?*

- **著者／年／題名／掲載先／ID:** Mostafa Shahriari, Rudolf Ramler, Lukas Fischer／2022／*How Do Deep-Learning Framework Versions Affect the Reproducibility of Neural Network Models?*／*Machine Learning and Knowledge Extraction* 4(4), 888–911、査読つき。DOI:10.3390/make4040045。citeturn23search4
- **読んだ範囲:** 要旨・本文冒頭。
- **方向:** 機構の一般論、方法論。
- **課題:** TensorFlow/PyTorch の version を変えたときの trained model performance の再現性。
- **環境:** GPU 要因を避けるため CPU training に限定した研究。citeturn22search14
- **系統:** library-version reproducibility。
- **現役度:** 不明。
- **比較:** framework version を変える。
- **効果量:** 対応表を今回精読していないため数値を記載しない。
- **符号:** version change で variance が生じ得るという結論。
- **seed／統計:** 詳細不明。
- **コード／ライセンス:** 論文は CC BY、コードについては不明。citeturn23search4
- **一行の要点:** CUDA/GPU だけでなく、**PyTorch/TensorFlow 自体の版は独立した reproducibility factor** として分ける必要がある。

#### Pham et al. — *DEVIATE: A Deep Learning Variance Testing Framework*

- **著者／年／題名／掲載先／ID:** H. V. Pham, M. Kim, L. Tan, Y. Yu, N. Nagappan／2021／*DEVIATE: A Deep Learning Variance Testing Framework*／ASE 2021、査読つき。DOI:10.1109/ASE51524.2021.9678540。citeturn23search13turn23search22
- **読んだ範囲:** 要旨・書誌。
- **方向:** 機構の一般論、方法論。
- **課題:** DL training variance を自動測定し、統計的な判定を行う framework。
- **推論規約:** 該当なし。
- **データ規模／モデル:** 本文未読のため不明。
- **系統:** variance testing。
- **現役度:** **定番の基準に近い**。Pham et al. の ASE 2020 variance analysis の後続。
- **効果量／seed 数／検定詳細:** 本文表を確認していないため不明。
- **コード／ライセンス:** 不明。
- **一行の要点:** “一回の再現値が一致したか” ではなく **training-result distribution を統計的に検査する**系統が存在する。

#### Ravi et al. — *Improving the Reproducibility of Deep Learning Software: An Initial Investigation through a Case Study Analysis*

- **著者／年／題名／掲載先／ID:** Nikita Ravi, Abhinav Goel, James C. Davis, George K. Thiruvathukal／2025／同題／preprint。arXiv:2505.03165。citeturn22search3
- **読んだ範囲:** 要旨・HTML の case-study 記述。
- **方向:** 方法論、否定的結果。
- **課題:** software environment、training pipeline、データ処理を固定・文書化した再現性 case study。
- **系統:** software reproducibility。
- **現役度:** **新興**。
- **比較:** TRUNK model を identical pipeline、identical random seed、identical GPU hardware で再学習。
- **効果量:** Figure 8 で **同じ pipeline・seed・GPU でも異なる tree structures が得られた**と記載。score の数値差は今回確認していない。citeturn22search4
- **符号:** **seed と GPU を固定しても完全再現しない**という否定的結果。
- **条件:** end-to-end software pipeline。
- **seed／統計:** sensitivity analysis を主張するが詳細は今回未確認。
- **コード／ライセンス:** 不明。
- **一行の要点:** **「seed を合わせたから machine variance は消える」という前提自体が安全ではない。**

#### Shanmugavelu et al. — *Impacts of floating-point non-associativity on reproducibility for HPC and deep learning applications*

- **著者／年／題名／掲載先／ID:** Sanjif Shanmugavelu, Mathieu Taillefumier, Christopher Culver, Oscar Hernandez, Mark Coletti, Ada Sedova／2024／同題／preprint。arXiv:2408.05148。citeturn21search2turn23view2
- **読んだ範囲:** 本文。
- **方向:** 機構の一般論、方法論、否定的結果。
- **課題:** floating-point non-associativity、GPU atomic/reduction order、PyTorch deterministic options の run-to-run variability。
- **環境:** NVIDIA/AMD/Groq を含む parallel hardware の microbenchmark と DL 関連検証。citeturn23view2
- **系統:** numerical nondeterminism。
- **現役度:** **新興**。
- **比較:** nondeterministic reduction と deterministic alternatives。
- **効果量:** Table 4 の FP64 summation microbenchmark、V100 では SPA **6.456 ms** に対して固定-order AO **87.204 ms**（100 sums）。これは **DL training overhead ではなく reduction kernel の microbenchmark** なので、そのまま EgoSurgery training cost と解釈してはいけない。citeturn23view7
- **符号:** deterministic operation は再現性を上げ得る一方、operation により大幅な速度 cost があり得る。
- **条件変化:** tensor dimensions、reduction ratio、operation、hardware に依存。citeturn23view7
- **seed／統計:** kernel experiments は多数回反復。DL seed variance との直接比較ではない。
- **コード／ライセンス:** repository を論文が参照するがライセンス不明。
- **一行の要点:** **GPU 間の違いは「乱数」だけでなく、同じ数学式の reduction order と floating-point rounding の違いからも生じる。**

#### Xie, Zhang & Chen — *RepDL: Bit-level Reproducible Deep Learning Training and Inference*

- **著者／年／題名／掲載先／ID:** Peichen Xie, Xian Zhang, Shuo Chen／2025／*RepDL: Bit-level Reproducible Deep Learning Training and Inference*／preprint。arXiv:2510.09180。citeturn22search2
- **読んだ範囲:** 要旨・HTML。
- **方向:** 機構の一般論、方法論。
- **課題:** random-number control に加え floating-point computation の correct rounding と order invariance を実装し、same/different CPU/GPU 間の bitwise consistency を狙う。citeturn22search6
- **系統:** cross-hardware deterministic arithmetic。
- **現役度:** **新興**。
- **比較:** conventional floating-point implementation と RepDL。
- **効果量:** benchmark table を今回精読していないため数値不記載。
- **符号:** cross-platform bitwise reproducibility を達成すると報告。
- **seed／検定:** 詳細不明。
- **著者外追試:** 発表後一年以内で限定的。
- **コード:** Microsoft `RepDL` repository 公開。研究用途・非 production と repository が明記。citeturn22search9
- **ライセンス:** 今回未確認。
- **一行の要点:** **「統計的に同程度」ではなく「bitwise identical」を別の reproducibility target として定義できることを示す。**

## 探したが見つからなかったもの

### 欠けのある系列について

**EgoSurgery で「注釈区間をつないで temporal state を carry」対「各区間で reset」を同一 model・同一 split で直接 ablate した論文は確認できなかった。** EgoSurgery 論文は PII frame の除去と 0.5 fps subsampling を説明するが、その結果として生じる配布系列の gap 境界で causal temporal state をどう扱うかという ablation は本文にない。citeturn12view0

検索語は `EgoSurgery missing frames temporal state reset`, `EgoSurgery discontinuous clips causal TCN`, `surgical phase recognition out-of-body reset hidden state`, `surgical workflow removed frames temporal continuity`。同一設定の EgoSurgery 文献を 4 件、近接する surgical OOB/privacy 文献を少なくとも 8 件確認したが、直接比較は 0 件だった。Bayat et al. は OOB が temporal model に悪影響を与えるところまでは直接扱う。citeturn14search23

**削除区間をまたいだ attention/state carry を禁止しても改善しなかった、あるいは悪化したという手術 phase の否定的 ablationも確認できなかった。** 方向 7 の検索では代わりに、StableSPR の「過去 state 内の誤りが前方へ伝播する」現象と、一般 TAD の「corruption 位置によって効果の符号が変わる」現象が見つかった。citeturn16view2turn17view0

**Edit・F1@k を「残存区間ごと」に算出した場合と、「gap を消して連結した一本の sequence」として算出した場合を、同一予測で直接比較した研究も確認できなかった。** StableSPR は別の問題として、Edit が compressed segment tokens のみを評価するため、segment 内の時間的不安定性が異なる二つの prediction に同じ Edit score を与え得ることを具体例で示している。citeturn15view2

**欠けの中に phase transition が存在する場合の boundary error の identifiability を surgical phase benchmark で定量化した研究は確認できなかった。** 一般 TAD では Zeng et al. が temporal corruption の主な悪化を classification error より localization error に帰し、Figure 4 で localization-error contribution が corruption により増えることを示している。citeturn17view0

**remaining-time prediction や elapsed-time feature が、未知長の削除区間によってどれだけずれるかを EgoSurgery 型データで測った研究は確認できなかった。** T-LSTM、mTAN、Latent ODE、S5、TIDES のような方法は elapsed time / timestamp を利用できるが、これは timestamp が存在する場合の解決法であり、消失した gap の長さそのものを推定する方法ではない。citeturn13search1turn19view0

また、**MASCIT はこの点に関する重要な「できないこと」の証拠を明示している**。同論文の compact representation は観測順序と mask geometry を保持するが、timestamps を consecutive indices に置き換えるため elapsed-time gaps を失い、「without elapsed-time input」で physical gap をモデル化しない。citeturn19view1

### 計算環境差について

**EgoSurgery、Cholec80、AutoLaparo 等で、fold と random seed を完全に対応させながら GPU 型だけを変え、macro Jaccard/accuracy の machine variance と seed variance を variance component として同時推定した研究は確認できなかった。**

検索語は `surgical phase recognition GPU reproducibility seed standard deviation`, `Cholec80 hardware reproducibility CUDA`, `action segmentation GPU seed variance`, `temporal action segmentation deterministic GPU`。Renard、*Metrics Matter in Surgical Phase Recognition*、C2F-TCN、CPKD 等の周辺資料は確認したが、「machine factor を seed factor と直交させる」直接実験は 0 件だった。

**fp16 対 bf16 対 TF32 を surgical phase/action segmentation の同じ training recipe で比較した報告も確認できなかった。** 一般 DL では precision と accumulation order が reproducibility source になることは確認できるが、それを EgoSurgery のような少数動画 phase model に移したときの pp 単位の値は文献からは出せない。Shanmugavelu et al. は reduction order の影響を直接扱う。citeturn21search2turn23view7

**GPU 数、per-GPU batch size、global batch size、DDP reduction、SyncBatchNorm のうち一要素だけを変えた surgical/action-segmentation の再現性研究は確認できなかった。** PyTorch community には multi-GPU RNG の再現性問題の実例があるが、査読つき surgical benchmark の効果量には使えない。citeturn21search9

**decord、PyAV、torchvision、OpenCV の video decoder だけを変えて surgical/action recognition score を比較した査読研究は確認できなかった。** decoder の performance benchmark は見つかったが、model accuracy の controlled comparison にはなっていなかった。

**resize implementation、anti-alias、JPEG 再圧縮を surgical phase model で isolation した研究も確認できなかった。** Parmar et al. の *clean-fid* は image preprocessing implementation が downstream metric を変える問題の既存例だが、工程認識の直接証拠ではない。一般画像 recognition では JPEG compression が精度を変える研究はあるため、「影響なし」とは言えないが、EgoSurgery の効果量への換算はできない。

**EndoVis、PitVis、SurgVU、HeiChole で同一 submission/container を異なる machine 上で再実行した score difference の系統的報告も確認できなかった。** SurgToolLoc/SurgVU の challenge report は Grand Challenge container を用いた standardized execution を再現性確保の仕組みとして採用しているが、「同一 container を二 hardware で走らせた差」の定量表は今回確認できなかった。citeturn5search11

公開 repository issue については、NVIDIA framework-reproducibility には TensorFlow 2.5 で同一 data/model/loop/seed でも reproducible にならない issue が確認できたが、手術映像 repository の quantitative reproduction issue とはならなかった。citeturn21search18

**「deterministic flag を入れても surgical video score の dispersion が減らなかった」という直接の否定結果は見つからなかった。** 一般 DL では、Zhuang et al. が一つの noise source だけを除いても stability がほとんど改善しないケースを報告し、Ravi et al. も同 seed・同 GPU で structural difference が残る case を示している。citeturn22search4

**Metrics Reloaded** については、今回の取得ログでは DOI/arXiv を一次資料で再確認できなかった。確認用検索語は `"Metrics Reloaded" recommendations image analysis validation DOI`、`"Metrics Reloaded" metric selection segmentation`。したがって書誌・数値はこの回答では使用していない。

## 未検証の組み合わせ

以下は「存在しない」と断定するものではなく、**今回確認した文献群では対応する controlled experiment を確認できなかった組み合わせ**である。

| 組み合わせ | 文献で片側までは分かっていること | 未検証部分 |
|---|---|---|
| EgoSurgery × **carry state / reset state** | EgoSurgery は PII frame 除去を行う。citeturn12view0 | 同じ causal TeCNO で gap boundary だけを変えた macro Jaccard / accuracy |
| EgoSurgery × **boundary mask only** | MASCIT は mask geometry を使える。citeturn19view1 | 実時間長なしの binary discontinuity flag が phase recognition に何をするか |
| EgoSurgery × **true Δ-aware S5/TIDES** | S5/TIDES は physical Δ を state discretization に使える。citeturn19view0 | EgoSurgery 配布物では Δ が不明。元 timestamp を回収した場合の比較 |
| EgoSurgery × **Neural CDE/Latent ODE** | irregular timestamp 自体は扱える。citeturn2search1turn2search3 | open-surgery online phase recognition への適用 |
| Surgical phase × **FrameDrop robustness training** | CVPR 2024 TAD では corrupted-frame robustness が向上。citeturn17view0 | 0.5 fps surgical workflow の sparse frames で同じ符号か |
| gap 中に transition × **Edit/F1@k** | Edit は compressed segment sequence を見るため内部の時間的不安定性を失う。citeturn15view2 | gap を消した連結評価と区間別評価の定量差 |
| gap 中に transition × **macro Jaccard** | Jaccard は observed-frame confusion を評価できる | prediction state を同じに固定した場合、評価境界処理そのものの影響はどこまであるか |
| unknown gap × **remaining time** | elapsed-time-aware models は timestamp があれば使える | gap 長そのものが欠落した場合の不可識別性を surgical benchmark で測った研究 |
| surgical video × **GPU model crossed with seed** | 一般 DL では hardware effect が software randomness と同桁の例。citeturn23view4 | Cholec80/EgoSurgery の phase metrics での variance component |
| surgical video × **fp32/fp16/bf16/TF32** | numerical precision/reduction order は一般 DL で要因。citeturn21search2 | macro Jaccard/accuracy への定量効果 |
| surgical video × **one GPU/multi-GPU + SyncBN** | BatchNorm と video training の相互作用は Rivoir et al. の既存文献が扱う | machine count のみを変えた paired rerun |
| surgical video × **decoder implementation** | decoder 自体の実装差は存在 | decord/PyAV/torchvision/OpenCV の同一 decoded-frame hash と最終 score の比較 |
| surgical video × **resize/JPEG pipeline** | clean-fid 等は preprocessing 実装差の重要性を示す | 同じ EgoSurgery split/model で pipeline だけを変えた差 |
| deterministic mode × **seed SD reduction** | deterministic patch は費用があり、全 noise を一つずつ消しても stability が単純には改善しない研究がある | surgical phase recognition における seed SD の何 % が減るか |
| challenge container × **異種 GPU rerun** | SurgVU 系 challenge は container standardized execution を採る。citeturn5search11 | GPU を変えた同一 container の score drift |

一般 TAD の結果からも、missing/corrupted observation が単に「情報量を減らす」だけではない点が重要である。Zeng et al. の Figure 5 では action boundary 付近の black frame が逆に localization を助ける場合があり、**gap/boundary artifact 自体が shortcut cue になり得る**。citeturn17view0

## 検索記録

検索日はいずれも **2026-10-21**。件数欄は「関連資料数 / その問いを直接測った資料数」。同じ論文が複数方向に該当するため、方向間の件数は排他的ではない。

### 欠けのある系列に関する検索

| 方向 | 主な検索語 | 確認件数 | 結果 |
|---|---|---:|---|
| **方向 1：同じデータ・EgoSurgery** | `EgoSurgery missing frames temporal state reset`; `EgoSurgery discontinuous clips causal`; `EgoSurgery privacy frame removal phase` | **4 / 0** | Phase/Tool/HTS/SurgMotion を確認。carry-reset ablation はなし。Phase 原論文は 25 fps→0.5 fps、PII frame removal を明記。citeturn12view0 |
| **方向 2：手術一般** | `surgical phase recognition out-of-body temporal continuity`; `online surgical workflow OOB temporal convolution`; `privacy removed frames surgical workflow` | **8 / 2** | Bayat の OOB temporal model、StableSPR の state-error cascade が特に近い。citeturn14search23turn16view2 |
| **方向 3：一人称・非手術** | `egocentric procedural recognition missing clips discontinuity`; `egocentric action segmentation sparse frames` | **2 / 0** | Ego-Exo4D、Ego-METAS 系を確認。unknown-duration gap の reset/carry 直接比較はなし。 |
| **方向 4：一般映像** | `temporal action detection missing frames robustness`; `dropped frames online action detection`; `temporal corruption action localization` | **6 / 1** | Zeng et al. CVPR 2024 が直接的。少数 corruption でも localization が大幅に悪化。citeturn17view0 |
| **方向 5：機構一般** | `irregularly sampled time series elapsed time RNN`; `continuous time transformer irregular timestamps`; `state space model irregular sampling S5`; `Mamba physical delta irregular time`; `Neural CDE online` | **17 / 13** | mTAN、T-LSTM、Time2Vec、SeFT、Latent ODE、GRU-ODE-Bayes、NCDE、Raindrop、ContiFormer、S5、TIDES、MASCIT 等。citeturn19view0turn19view1 |
| **方向 6：評価・統計** | `action segmentation edit score missing frames`; `segment F1 gap concatenated clips`; `surgical phase temporal fragmentation metric`; `remaining time missing intervals` | **5 / 2** | StableSPR が Edit の blind spot、Ego-METAS が frame-rate と Edit の相互作用を扱う。gap 連結 vs 区間別は未発見。citeturn15view2turn15view4 |
| **方向 7：否定的結果** | `state carry reset no improvement temporal model`; `irregular time Mamba failure extrapolation`; `frame drop worsens action detection`; `attention mask discontinuity no improvement` | **6 / 4** | TIDES: Mamba OOD-Δ failure/S5 LTI limitation、MASCIT: full selectivity 不利、Zeng: corruption vulnerability、StableSPR: Edit と stability の不一致。citeturn20view1turn20view4turn17view0turn15view4 |

方向 5 では手術・医療語を一切入れない検索を独立に行い、S5/TIDES、mTAN、Latent ODE、GRU-ODE-Bayes、Neural CDE、Raindrop、ContiFormer、SeFT 等を拾った。これにより、手術文献だけを見た場合に抜ける「physical elapsed time を state equation 自体に入れる」系統を補完した。citeturn19view0

### 計算環境差に関する検索

| 方向 | 主な検索語 | 確認件数 | 結果 |
|---|---|---:|---|
| **方向 1：EgoSurgery** | `EgoSurgery reproducibility seed GPU`; `EgoSurgery same seed different GPU` | **4 / 0** | dataset/model papersはあるが cross-machine matched rerun は未発見。 |
| **方向 2：手術一般** | `surgical phase recognition reproducibility seed GPU`; `Cholec80 hardware reproducibility`; `EndoVis rerun GPU difference`; `SurgVU reproducibility container` | **5 / 0** | seed/split/reproduction 周辺文献はあるが、GPU/CUDA factor を直接測るものはなし。SurgVU は container standardization。citeturn5search11 |
| **方向 3：一人称非手術** | `egocentric video recognition hardware reproducibility`; `procedural action segmentation GPU seed variance` | **0 / 0** | 質問に答える査読研究を確認できず。 |
| **方向 4：一般映像** | `video recognition decoder reproducibility PyAV decord`; `action segmentation JPEG resize reproducibility`; `video model different GPU same seed` | **4 / 0** | decoder/圧縮/前処理の周辺研究はあるが、action segmentation で machine×seed を直接比較するものはなし。 |
| **方向 5：機構一般** | `deep learning hardware nondeterminism GPU seed variance`; `floating point non-associativity reproducibility`; `framework version reproducibility deep learning`; `bitwise cross GPU training` | **13 / 8** | Zhuang、Summers、Pham、Bouthillier、Chen、Coakley、Shahriari、Shanmugavelu、RepDL 等。citeturn22search0turn23search0turn21search2turn22search2 |
| **方向 6：方法論** | `variance decomposition deep learning seed hardware`; `reproducibility reporting machine learning multiple seeds hardware`; `deterministic training overhead` | **10 / 7** | Chen の software/hardware 分解、DEVIATE、Coakley の multi-environment design、Gundersen review 等。citeturn23view4turn23search13turn23view1 |
| **方向 7：否定的結果** | `deterministic training does not reduce variance`; `same seed same GPU different result`; `different GPU minimal accuracy difference`; `reproducibility one bit perturbation` | **7 / 5** | Zhuang: aggregate metric差は小さくても model disagreement が残る、Summers: 微小 perturbation が異なる solution を生む、Ravi: same seed/GPU でも構造差、Chen: hardware component が残存。citeturn7view1turn22search4turn23view4 |

ここでも手術語を含めない探索を独立に行った。その結果、手術映像側ではほぼ見つからなかった **hardware/software/randomness の factor separation** に関する証拠が software-engineering / general-DL 側に集中していることが分かった。Chen et al. は software randomness と hardware nondeterminism を別 setup に分け、Coakley et al. は多数 hardware/software environments で反復する。citeturn23view3turn23view1

## 解釈と提案

### 問いへの答え

#### 欠けのある区間列をどう扱うか

今回の文献から言える事実は、**「すべての欠けを越えて state を持ち越す」ことが標準的に正しいとも、「必ず reset する」ことが標準的に正しいとも示されていない**、ということである。特に EgoSurgery と同じ「実時間長不明の削除区間」に対する carry-vs-reset の controlled experiment は見つからなかった。

一方、近接証拠は方向性を三つに分ける。

第一は、**欠けを通常の時間連続性として扱わない**系統である。Bayat et al. は OOB frame が out-of-distribution spatial features と予測不能な出現位置を持ち、temporal model の性能に影響すると明示する。Zeng et al. は一般映像で、わずかな temporal corruption でも action localization が大きく落ち得ることを示す。citeturn14search23turn17view0

第二は、**欠けた時間そのものをモデル化する**系統である。T-LSTM は elapsed-time decay、Latent ODE / GRU-ODE-Bayes / Neural CDE は observation 間を continuous dynamics として進め、S5/TIDES は state-space discretization に physical Δ を入れる。これらは「時間が抜けた」問題には適合するが、**何秒抜けたかが分かることを必要とする**。citeturn13search1turn2search1turn2search2turn19view0

第三は、**実時間が失われた以上、順序・欠損 mask・boundary information だけを使う**系統である。MASCIT は実際に timestamp compaction により elapsed-time gap を捨て、mask geometry と order を使う。そして著者自身が、それは physical elapsed time をモデル化していないと明記している。citeturn19view1

したがって、依頼者の配布物に対し S5/TIDES を導入する場合でも、**単に S5/Mamba に置き換えれば「失われた時間」を解決できるわけではない**。真の Δ が無ければ、physical-time SSM の主要な機構的利点の一部が定義できない。TIDES が示すように、Mamba の learned Δ-like gate と実際の physical elapsed time は別物である。citeturn19view0turn20view1

#### 計算機を変えたときの散らばりは seed 散らばりに対してどの程度か

**手術映像・行動分割に限定した、信頼できる共通目安は見つからなかった。** したがって、「GPU を変えると通常 macro Jaccard が何 pp 動く」という文献値を EgoSurgery に転用することはできない。

一般 DL で最も直接的なのは Chen et al. である。ResNet-38 の §5.1/Table 4 の分解では、著者が software randomness と呼ぶ条件による overall-accuracy の最大変動が 1.4%、hardware nondeterminism の条件が 1.2% だった。per-class では 6.8% と 4.9%、inconsistent predictions は 216 と 209 だった。したがってこの controlled example に限れば、hardware effect は **software-randomness effect のごく小さな残差ではなく、同じ桁**だった。もっとも、software randomness は random seed だけを孤立させた pure seed variance ではないため、「GPU SD = seed SD の 86%」という一般則にはしてはいけない。citeturn23view4

逆方向の否定的結果も重要である。Zhuang et al. は accelerator を変えても top-line accuracy の standard deviation の差が小さい条件を示す一方、prediction churn や parameter-space distance では implementation/hardware source が algorithmic randomness と同程度になり得ることを報告している。すなわち、**最終 accuracy が近いことと、同じ model が学習されたことは同義ではない**。また一つの nondeterminism source を除くだけでは stability が大きく改善しない条件も報告する。 deterministic implementations の cost は accelerator により大きく変わり、同研究では最大で数倍規模の overhead が報告されている。citeturn7view0turn8view2turn9view1

Summers & Dinneen も、乱数源やごく小さな初期 perturbation が optimization trajectory を分岐させ得ること、異なる nondeterminism source の影響が似た規模になり得ることを報告している。citeturn7view1

よって文献から得られる大きさの表現は、**「machine effect は seed effect より必ず小さい」ではなく、「aggregate score では小さく見える場合と、software randomness と同程度まで達する場合の双方がある。モデル・metric・環境依存性が大きい」**が最も忠実である。

### EgoSurgery で取り得る区間処理の選択肢

以下は順位づけではなく、文献から区別できる実験条件である。

**状態を区間境界で完全 reset する条件**では、配布物が明示する各 retained interval を独立した causal sequence とみなし、TCN の receptive field、RNN/SSM hidden state、Transformer cache を境界で空にする。これは「未知長の間、何が起きたかについてモデルが情報を持たない」という解釈になる。StableSPR が示した state contamination の可能性を遮断する条件にもなる。citeturn16view2

**現状どおり carry する条件**では、隣接する retained intervals の last/first frame を時間的に隣接した観測とみなす。この条件は実装上単純だが、元映像上では直接隣接していない二点の間に causal convolution receptive field が渡る。そのため、この arm は「gap を 0 秒と仮定する条件」と解釈するのが正確であり、「元動画の連続時系列」と呼ぶのは避ける必要がある。

**boundary mask / boundary token を入れるが state を必ずしも zero にしない条件**では、`is_new_interval` のような binary information を temporal model に知らせる。実時間長は発明せず、配布物から確実に分かる「ここに不連続がある」という情報だけを使う。MASCIT の observation-mask 系統に最も近い発想であるが、MASCIT 自身は framewise surgical phase model ではない。citeturn19view1

**時間に応じて state を decay/evolve する条件**は、元 timestamp または interval 境界間の正しい elapsed time が後から得られる場合に初めて定義できる。T-LSTM、ODE-RNN、Neural CDE、S5/TIDES が対応する系統である。citeturn13search1turn2search1turn2search3turn19view0

**unknown-gap を一つのカテゴリとして扱う条件**も分離できる。例えば boundary embedding は入れるが、「平均 gap=何秒」のような作為的 numeric Δ は入れない。これは物理時間モデルではなく、discontinuity-aware sequence model という別条件になる。

この比較では spatial ResNet-50 feature、fold、seed、optimizer、training epochs、sample order を対応させ、**区間処理だけを変える**ことで、TCN から state-space model への architecture 変更と gap-policy の変更を混ぜないことが重要になる。Zeng et al. の robustness study が入力 corruption を固定 model 上で分離しているのと同じ実験原則である。citeturn17view0

### 評価の選択肢

依頼者の primary が macro Jaccard、co-primary が frame accuracy であることは、この問題では利点がある。**同じ observed frames に対する予測を完全に固定できれば、単に評価スクリプト上で区間を連結したかどうかだけでは frame confusion matrix は変わらない**。ただし実際には carry/reset により予測自体が変わるので、macro Jaccard/accuracy には間接的に現れる。

一方、Edit と F1@k は segment construction に依存する。これは文献の定義から導く推論である。gap 前後が同じ phase label なら、gap を消して連結すると二つの観測区間が一つの連続 segment と見なされ得る。逆に gap 内に未観測 phase があっても、その phase token は評価系列から消える。そのため **「連結 sequence の Edit/F1」と「各 retained interval 内だけの Edit/F1」は同じ estimand ではない**。StableSPR が Edit の compressed-token 性による blind spot を実例で示している点も、この問題と整合する。citeturn15view2

したがって感度解析としては、同じ prediction に対して、

**observed-frame 集合全体の macro Jaccard / frame accuracy** と、  
**各 retained interval 内だけで segment を作る Edit/F1@k** と、  
**現状の concatenated sequence で作る Edit/F1@k**

を区別できる。後二者の差は model accuracy の差ではなく、**gap の評価 convention による差**として読むことになる。

boundary metric ではさらに強い制約がある。gap の中に真の phase transition があるなら、その boundary timestamp 自体が配布物から観測不能なので、「何秒 boundary がずれたか」を正確に評価できない。interval endpoint を phase boundary とみなすことも ground truth からは正当化されない。

remaining-time / elapsed-time feature についても同じで、0.5 fps の retained-frame count を「手術開始からの実時間」に置き換えることは、未知 gap がある限り不可能である。ここは T-LSTM/S5/TIDES の導入以前の **identifiability の問題**である。citeturn19view0turn19view1

### 計算環境差を seed 差から分離する実験の選択肢

EgoSurgery の 15 動画・事前固定された動画単位 CV という条件では、machine difference を単なる「別 run」として seed variance に混ぜるより、**fold と seed を対応させた paired design** として扱うことができる。

観測値を概念的に

\[
y_{f,s,e}
=
\mu
+\alpha_f
+\beta_s
+\gamma_e
+(\beta\gamma)_{s,e}
+\varepsilon
\]

と置けば、\(f\) は CV fold、\(s\) は random seed、\(e\) は environment である。ここで知りたいのは seed 内変動と environment 差、さらに seed×environment interaction の大きさである。Pham 系の variance analysis、DEVIATE、Chen の source separation、Coakley の multi-environment design は、このように一つの最終値だけで reproducibility を判定しない考え方を支持する。citeturn23search13turn23view4turn23view1

具体的に区別できる environment factor は、少なくとも次のまとまりになる。

**hardware / arithmetic:** GPU 型、GPU 数、driver、TF32 on/off、fp32/fp16/bf16、AMP/GradScaler、deterministic algorithm。  
**software:** PyTorch、CUDA、cuDNN、torchvision、compiler の version。Shahriari et al. は framework version 自体を factor として扱う。citeturn23search4  
**parallelism:** world size、per-GPU batch、global batch、gradient accumulation、DDP reduction、SyncBatchNorm。  
**input pipeline:** decoder、worker 数、frame order、resize interpolation、antialias、JPEG bytes。  
**algorithmic randomness:** initialization、shuffle、augmentation、dropout 等の RNG stream。

このうち **GPU 数を変えながら global batch も変わる実験は、「計算機差」だけの比較ではなく optimizer/data-order 差も混ざる**。同様に GPU 数を変えた結果 BatchNorm の effective batch が変わる場合、Rivoir et al. の BatchNorm 問題と machine effect が分離できなくなる。

入力 pipeline と optimizer nondeterminism の切り分けには、各環境で同じ frame ID の

`decoded tensor → resized tensor → ResNet input → frozen feature`

の checksum または最大絶対差を記録する方法がある。ここで既に tensor が違えば decoder/resize/JPEG 要因であり、tensor が bitwise 同一なのに最終 model が違えば training arithmetic/RNG 側を疑うことができる。これは今回 decoder 間の surgical score 文献が見つからなかったため、**効果量を仮定せず原因を局所化するための実験上の選択肢**である。

### 決定性の扱い

決定性には二種類の目的を分ける必要がある。

一つは **bitwise repeatability** で、同じ条件なら同一 weights/output を得ること。RepDL は cross-CPU/GPU までこの目標を押し広げる。citeturn22search6

もう一つは **statistical reproducibility** で、異なる seed/hardware で得られる performance distribution と科学的結論が安定していること。後者では bitwise 同一化は必須条件ではない。

Chen et al. の結果では deterministic patch の training overhead が Table 3 で 24–114% に及び、Zhuang et al. も hardware により非常に大きな deterministic overhead を報告する。したがって、deterministic mode は「無料で variance を除く checkbox」とは扱えない。citeturn23view4turn9view1

しかも、Zhuang et al. と Ravi et al. の否定的結果を合わせると、**一つの nondeterminism source を固定した後の残差 dispersion も測る必要がある**。deterministic mode を一度だけ走らせて通常 training の seed SD と比較するだけでは、environment×seed interaction を推定できない。citeturn22search4

### 依頼者の問いで暗黙になっていた可能性のある前提

最も重要なのは、**「削除されたフレーム」と「不規則サンプリング」は同じ問題ではない**ことである。0.5 fps で規則的に subsample しただけなら、各 token は 2 秒刻みと解釈できる。しかし PII 削除や未配布区間で 30 秒抜けても、配布系列を連結すると temporal model からは 2 秒に見える。この二つを一つの “sampling rate” で表すことはできない。EgoSurgery 原論文は 0.5 fps sampling と PII-frame removal の双方を行っている。citeturn12view0

第二に、**frame 番号のリセットが問題なのではなく、missing real-time support が問題**である。連番を単調増加に振り直しても失われた elapsed time は戻らない。逆に true timestamp が別 metadata に残っていれば、連番がリセットされても S5/TIDES/T-LSTM 等へ Δ を渡すことはできる。

第三に、**phase label が gap の両側で同じだから state carry が正しいとは限らない**。gap 中に同じ phase が続いた可能性と、別 phase を経て同じ phase に戻った可能性を配布物だけから区別できない。これは model architecture では解消できない情報欠落である。

第四に、**machine difference と data-pipeline difference は同義ではない**。別計算機で JPEG library、decoder、resize、PyTorch version まで同時に変わっていれば、GPU hardware effect と呼べない。Shahriari et al. は framework version 自体で結果が変わり得ることを研究し、Shanmugavelu et al. は arithmetic/reduction order を別要因として扱う。citeturn23search4turn21search2

第五に、**同じ final accuracy/Jaccard は再現された model が同じことを意味しない**。Zhuang et al. は top-line metric が近くても prediction churn/parameter distance が残り得ることを示し、Chen et al. も inconsistent predictions を別 metric として測っている。citeturn7view0turn23view4

第六に、15 動画 CV では **fold variance、seed variance、environment variance が同じ階層ではない**。fold は異なる患者/手術動画集合を変え、seed は同じ data split 内の optimization trajectory を変え、environment は同じ seed を実装上別 trajectory に分岐させ得る。したがって「全 run の SD 一つ」だけにまとめると、どの要因が大きかったかが消える。

文献から最も堅く言える結論は二点である。**EgoSurgery の未知長 gap については、実時間 Δ を復元できない限り、continuous-time/SSM を導入しても missing physical time 自体は復元されず、carry・reset・boundary-aware の条件を区別して測る必要がある。** また **計算機差については、手術映像固有の標準値はまだ得られず、一般 DL では hardware nondeterminism が software randomness と同じ桁に達する controlled example と、aggregate score ではほとんど差が出ない例の双方があるため、EgoSurgery 自身で fold×seed×environment を対応させて分離して測らなければならない。** citeturn19view0turn19view1turn23view4turn7view0
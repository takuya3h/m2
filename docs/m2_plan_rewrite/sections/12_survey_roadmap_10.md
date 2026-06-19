## 10. サーベイロードマップ {toggle="true"}
	本研究のアーキテクチャ設計と仮説検証(結合効果①②＋将来拡張＝Phase-2)に必要な最新研究のサーベイ対象を、**7 大分類 × 約 45 細目** に構造化する。各細目には本研究での位置づけ(参照する § / 関連する結合仮説 / 関連する STEP)と優先度(高/中/低)を併記する。
	### 10.0 全体構造(7 分類)
	<table fit-page-width="true" header-row="true">
<tr>
<td>分類</td>
<td>何を問うサーベイか</td>
</tr>
<tr>
<td>**A. ドメイン軸**</td>
<td>どの「映像」「手術」「視点」がターゲットか</td>
</tr>
<tr>
<td>**B. タスク軸**</td>
<td>何を認識するか(検出 / 分割 / 工程 / 関係 / 動作)</td>
</tr>
<tr>
<td>**C. アーキテクチャ軸**</td>
<td>どう構成するか(backbone / 検出 / 時系列 / 関係 / マルチタスク)</td>
</tr>
<tr>
<td>**D. 時間モデリング軸**</td>
<td>どう時間を扱うか(短期 / 長距離 / 階層)</td>
</tr>
<tr>
<td>**E. 学習パラダイム軸**</td>
<td>どう学習するか(教師あり / 事前学習 / SSL / 半教師 / 弱教師 / 蒸留)</td>
</tr>
<tr>
<td>**F. 学習信号設計軸**</td>
<td>どんな損失・データ整形で学ぶか</td>
</tr>
<tr>
<td>**G. 評価・ベンチマーク軸**</td>
<td>何で測るか、どのデータセットで比較するか</td>
</tr>
	</table>
	### 10.A ドメイン軸(対象領域)
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**A1**</td>
<td>**open surgery 映像解析**</td>
<td>本研究の対象ドメインそのもの。腹腔鏡 / 内視鏡との差(遮蔽・照明変動・同時出現物体数・class imbalance)を理解する</td>
<td>高</td>
</tr>
<tr>
<td>**A2**</td>
<td>**手術映像解析(腹腔鏡・内視鏡以外)**</td>
<td>開放手術、整形外科、皮膚外科、ロボット支援外科など。OR scene understanding 全般</td>
<td>高</td>
</tr>
<tr>
<td>**A3**</td>
<td>**一人称視点(egocentric)映像解析**</td>
<td>Ego の特性(視野移動、頭部運動、frame rate の低さ)。Ego4D、EPIC-KITCHENS 等の一般 ego 研究も含む</td>
<td>高</td>
</tr>
<tr>
<td>**A4**</td>
<td>**多視点(multi-view)手術映像 / Ego–Exo learning**</td>
<td>無影灯マルチカメラ、OR の固定カメラ、ego-exo pair 学習。Exo（Phase-2）の直接の前提</td>
<td>高</td>
</tr>
<tr>
<td>**A5**</td>
<td>**医療映像解析の一般動向(foundation models 含む)**</td>
<td>SurgVLP、Endo-FM、SAM 系の医療応用。本研究を一般潮流に位置づけるための背景</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:EgoSurgery、Open-MOH(open multi-view OR Hospital)、GraSP、PhaKIR、SurgVLP、Endo-FM、Cholec80(対照群)、MICCAI EndoVis Challenges、Ego4D。
	### 10.B タスク軸(認識対象)
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**B1**</td>
<td>**物体検出(汎用)**</td>
<td>アーキテクチャの基盤。query-based(DETR / DINO 系)、anchor-based(VarifocalNet 系)、set prediction 全般</td>
<td>高</td>
</tr>
<tr>
<td>**B2**</td>
<td>**術具検出(surgical-specific)**</td>
<td>B1 の手術特化。形状類似・遮蔽・class imbalance への対処。**検出ベースライン・STEP B の主役**</td>
<td>高</td>
</tr>
<tr>
<td>**B3**</td>
<td>**手検出・手姿勢推定**</td>
<td>**S2 で導入**。own/other × left/right 区別、surgical glove 下の検出、egocentric hand-pose</td>
<td>高</td>
</tr>
<tr>
<td>**B4**</td>
<td>**セグメンテーション(instance / semantic / panoptic)**</td>
<td>**S1 の主役**。Mask2Former、Mask DINO、SAM 系。器具・組織・背景の同時分割</td>
<td>高</td>
</tr>
<tr>
<td>**B5**</td>
<td>**工程認識(phase recognition)**</td>
<td>**S4 以降の主役**。手術工程の長距離時系列分類</td>
<td>高</td>
</tr>
<tr>
<td>**B6**</td>
<td>**動作認識(action / gesture / surgical activity)**</td>
<td>現フェーズではスコープ外だが、§9 #1 の判断材料および将来拡張のため背景理解は必要。action triplet、JIGSAWS、Action Genome 系</td>
<td>中</td>
</tr>
<tr>
<td>**B7**</td>
<td>**HOI(Human-Object Interaction)**</td>
<td>関係モジュール（Phase-2）の理論的基盤。HOI 検出、interaction prediction、affordance</td>
<td>高</td>
</tr>
<tr>
<td>**B8**</td>
<td>**手-術具関係認識(hand-tool relation)**</td>
<td>**Phase-2（関係）の主役**。grasp / handover / two-hand manipulation、egocentric H+O</td>
<td>高</td>
</tr>
<tr>
<td>**B9**</td>
<td>**Scene graph generation(SGG)**</td>
<td>関係推論をグラフ構造で扱う潮流。surgical scene graph(SSG-Com)、MCIT-IG</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:Mask DINO、Co-DETR、QueryInst、Mask2Former、TeCNO、Trans-SVNet、SR-Mamba、LoViT、Surgformer、MuST、SKiT、HID-SSM、H+O、MCIT-IG、SSG-Com、SemiVT-Surge、GraSP。
	### 10.C アーキテクチャ軸(モデル構成要素)
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**C1**</td>
<td>**空間 backbone**</td>
<td>§4.2。Swin / ConvNeXt / DINOv2 / SAM encoder の比較。事前学習済み backbone の手術ドメインへの適応性</td>
<td>高</td>
</tr>
<tr>
<td>**C2**</td>
<td>**検出 / 分割ヘッド**</td>
<td>§4.2。query-based 統合ヘッド(Mask DINO)vs 分離ヘッド(VarifocalNet + Mask2Former)</td>
<td>高</td>
</tr>
<tr>
<td>**C3**</td>
<td>**時系列モデル(TCN / Transformer / SSM-Mamba)**</td>
<td>§4.5。フレーム列を入力に sequence 予測。各アーキテクチャの計算量・長距離性能のトレードオフ</td>
<td>高</td>
</tr>
<tr>
<td>**C4**</td>
<td>**物体中心表現(object-centric representation / slot attention)**</td>
<td>§4.3、**結合効果②の核**。ROI Align、slot attention、object query を時系列化する手法</td>
<td>高</td>
</tr>
<tr>
<td>**C5**</td>
<td>**グラフニューラルネットワーク・関係推論**</td>
<td>§4.4、**関係結合（Phase-2）の核**。graph transformer、message passing、edge feature 設計</td>
<td>高</td>
</tr>
<tr>
<td>**C6**</td>
<td>**マルチタスク学習**</td>
<td>研究全体の構造。head 分離 vs 共有 backbone、negative transfer 対策、§8 の動的重み付け</td>
<td>高</td>
</tr>
<tr>
<td>**C7**</td>
<td>**双方向補完(mutual / cross-task feedback)**</td>
<td>§4.6 の核。phase ⇄ detection、mutual learning、co-training architectures</td>
<td>高</td>
</tr>
<tr>
<td>**C8**</td>
<td>**多視点融合(view-gating / cross-view fusion)**</td>
<td>§4.7。visibility-aware fusion、view dropout、PreViPS</td>
<td>高</td>
</tr>
<tr>
<td>**C9**</td>
<td>**条件付け機構(FiLM / cross-attention / adapter)**</td>
<td>§4.6 の Phase → Detection 注入の実装手段</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:DINOv2、SAM、Mask DINO、Co-DETR、Slot Attention、Object-Centric Learning、Graph Transformer、MTL with Task Affinity、Mutual Learning、Deep Mutual Learning、PreViPS、MV2MAE、FiLM、Perceiver、Cross-Attention Adapter。
	### 10.D 時間モデリング軸
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**D1**</td>
<td>**短期時間モデリング(short clip)**</td>
<td>Exo の数秒区間の動作表現。video transformer、TimeSformer、VideoSwin</td>
<td>中</td>
</tr>
<tr>
<td>**D2**</td>
<td>**時間的な長距離文脈の獲得**</td>
<td>**S4 の核**。手術全体(分〜数十分)。causal TCN、long-range transformer、SSM(Mamba)、key-information pooling(SKiT)、hierarchical attention</td>
<td>高</td>
</tr>
<tr>
<td>**D3**</td>
<td>**オンライン vs オフライン推論**</td>
<td>推論時の causal 制約。online phase recognition、TeCNO、causal Mamba</td>
<td>中</td>
</tr>
<tr>
<td>**D4**</td>
<td>**階層的(slow / fast)時間モデリング**</td>
<td>Exo 高 fps と Ego 低 fps の二層構成。SlowFast、Dual-rate temporal modeling</td>
<td>高</td>
</tr>
<tr>
<td>**D5**</td>
<td>**時間アラインメント・同期学習**</td>
<td>Ego–Exo の anchor-based 学習。temporal alignment、TCC(Temporal Cycle Consistency)</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:TeCNO、Trans-SVNet、LoViT、Surgformer、MuST、SKiT、HID-SSM、SR-Mamba、SlowFast、TimeSformer、VideoSwin、TCC、Anchor-based contrastive。
	### 10.E 学習パラダイム軸
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**E1**</td>
<td>**教師あり学習(マルチタスク監視)**</td>
<td>§5 Stage A / D の基本枠組み</td>
<td>高</td>
</tr>
<tr>
<td>**E2**</td>
<td>**事前学習(pre-training / foundation models)**</td>
<td>backbone 初期化(DINOv2、SAM、CLIP、SurgVLP)。医療 foundation model の最新動向</td>
<td>高</td>
</tr>
<tr>
<td>**E3**</td>
<td>**自己教師あり学習(SSL)**</td>
<td>**§5 Phase-2（Exo 拡張）の核**。MAE / VideoMAE / MV2MAE、contrastive、playback speed、temporal order</td>
<td>高</td>
</tr>
<tr>
<td>**E4**</td>
<td>**教師なし学習**</td>
<td>クラスタリング、prototype learning、deep clustering(SwAV、DINO)</td>
<td>中</td>
</tr>
<tr>
<td>**E5**</td>
<td>**半教師あり学習**</td>
<td>Mean Teacher、FixMatch、SemiVT-Surge。少量 Ego ラベル + 多量 Exo 無ラベル</td>
<td>高</td>
</tr>
<tr>
<td>**E6**</td>
<td>**弱教師あり学習**</td>
<td>Ego の Phase ラベルを Exo に転写(§3.2 (3))。timestamp supervision、SkipTag</td>
<td>高</td>
</tr>
<tr>
<td>**E7**</td>
<td>**知識蒸留(teacher–student / cross-view distillation)**</td>
<td>**§5 Phase-2（Exo 拡張）の Ego 注入経路**。Soft Teacher、cross-view distillation、feature distillation</td>
<td>高</td>
</tr>
<tr>
<td>**E8**</td>
<td>**ドメイン適応・転移学習**</td>
<td>手術ドメインへの一般動画モデルの適応、Ego-Exo domain gap、test-time adaptation</td>
<td>中</td>
</tr>
<tr>
<td>**E9**</td>
<td>**アクティブラーニング**</td>
<td>動作ラベル追加(§9 #1)の効率化、uncertainty sampling、step-aware AL</td>
<td>低</td>
</tr>
	</table>
	**代表キーワード**:DINOv2、SAM、CLIP、SurgVLP、Endo-FM、VideoMAE、MV2MAE、MoCo、SimCLR、SwAV、SimMIM、Mean Teacher、FixMatch、SemiVT-Surge、Soft Teacher、Cross-View Distillation、DeiT-Distill、AdaMatch。
	### 10.F 学習信号設計軸
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**F1**</td>
<td>**クラス不均衡対応**</td>
<td>§3.3、稀少術具・工程偏り。focal loss、class-balanced sampling、copy-paste、稀少クラス sampling temperature、long-tailed recognition</td>
<td>高</td>
</tr>
<tr>
<td>**F2**</td>
<td>**マルチタスク損失バランシング**</td>
<td>§5 Stage D。uncertainty weighting、GradNorm、PCGrad、CAGrad、Auto-λ、negative transfer 対策</td>
<td>高</td>
</tr>
<tr>
<td>**F3**</td>
<td>**contrastive learning(image / video / cross-view)**</td>
<td>Exo（Phase-2）の主損失。SimCLR、MoCo、CLIP、view-consistent contrastive、time-contrastive</td>
<td>高</td>
</tr>
<tr>
<td>**F4**</td>
<td>**masked modeling(MAE / VideoMAE / MV2MAE)**</td>
<td>Exo（Phase-2）の主損失。Phase-2 拡張の中核。hand-tool-guided MAE という派生</td>
<td>高</td>
</tr>
<tr>
<td>**F5**</td>
<td>**疑似ラベル生成・整合性損失**</td>
<td>Phase ラベル転写、関係疑似ラベル(Hand-Tool マスクから生成)、PU loss、down-weighted BCE</td>
<td>高</td>
</tr>
<tr>
<td>**F6**</td>
<td>**時系列正則化(transition / smoothing / CTC)**</td>
<td>§4.5。順序制約、impossible-transition、temporal smoothing、phase order prior</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:Focal Loss、Class-Balanced Loss、Copy-Paste、Equalization Loss、Uncertainty Weighting、GradNorm、PCGrad、CAGrad、SimCLR、MoCo v3、VideoMAE、SimMIM、PU Learning、CTC、Edit-Loss。
	### 10.G 評価・ベンチマーク軸
	<table fit-page-width="true" header-row="true">
<tr>
<td>#</td>
<td>トピック</td>
<td>本研究での位置づけ</td>
<td>優先度</td>
</tr>
<tr>
<td>**G1**</td>
<td>**検出・分割の評価指標**</td>
<td>§7.2。COCO mAP、稀少クラス mAP の慣行、panoptic quality、boundary IoU</td>
<td>中</td>
</tr>
<tr>
<td>**G2**</td>
<td>**時系列認識の評価指標**</td>
<td>§7.2。Edit score、Segmental F1@k、relaxed accuracy、phase transition error</td>
<td>中</td>
</tr>
<tr>
<td>**G3**</td>
<td>**関係認識・HOI の評価指標**</td>
<td>§7.2。HOI mAP、triplet AP、interaction recall、SGG metrics</td>
<td>中</td>
</tr>
<tr>
<td>**G4**</td>
<td>**手術ドメイン既存ベンチマーク**</td>
<td>比較基準としての先行ベンチマーク。EgoSurgery、GraSP、PhaKIR、MICCAI EndoVis Challenges、Cholec80(対比用)</td>
<td>高</td>
</tr>
<tr>
<td>**G5**</td>
<td>**Ego-Exo / multi-view 系ベンチマーク**</td>
<td>Exo（Phase-2）関連の外部参照。Ego-Exo4D、Assembly101、CharadesEgo、H2O</td>
<td>中</td>
</tr>
<tr>
<td>**G6**</td>
<td>**長尾・希少クラス評価の慣行**</td>
<td>稀少クラス Δ mAP の正しい報告方法、tail-class metric、effective number-based weighting</td>
<td>中</td>
</tr>
	</table>
	**代表キーワード**:Edit score、Segmental F1@k、Boundary IoU、HOI mAP、Action Triplet AP、Ego-Exo4D、EndoVis、Assembly101、CharadesEgo、Long-tailed Recognition Benchmarks。
	### 10.1 サーベイの実施順序(STEP 0–D と連動)
	ロードマップを STEP 0–D のスケジュールに沿って前倒しで配置する。**各 STEP を開始する前に、対応する細目のサーベイを終えていること**を目安とする。
	<table fit-page-width="true" header-row="true">
<tr>
<td>サーベイ完了目標</td>
<td>必読(高優先度)</td>
<td>副読(中優先度)</td>
</tr>
<tr>
<td>**S0〜S2 開始前(今)**</td>
<td>A1, A2, B1, B2, B3, B4, C1, C2, F1, G4</td>
<td>A3, A5, E2, G1</td>
</tr>
<tr>
<td>**S3〜S4 開始前**</td>
<td>B5, C3, D2, F6, G2</td>
<td>D1, D3, D4</td>
</tr>
<tr>
<td>**STEP B 開始前**</td>
<td>C4, C6, C7, C9, F2</td>
<td>E1, E8</td>
</tr>
<tr>
<td>**Phase-2（関係）開始前**</td>
<td>B7, B8, B9, C5, F5, G3</td>
<td>B6</td>
</tr>
<tr>
<td>**Phase-2（Exo）開始前**</td>
<td>A4, C8, D4, D5, E3, E5, E6, E7, F3, F4, G5</td>
<td>E4, E9</td>
</tr>
<tr>
<td>**最終評価・論文執筆段階**</td>
<td>G6、自分の Δ 値を既存ベンチに位置づけるためのメタサーベイ</td>
<td>—</td>
</tr>
	</table>
	### 10.2 補足:除外したが意識する価値のある分野
	- **腹腔鏡 / 内視鏡映像解析**:本研究のドメインからは除外しているが、**手法レベルの転用は非常に多い**(Cholec80、Trans-SVNet、SR-Mamba、SKiT などはほぼすべて腹腔鏡発)。ドメインとしては読まないが、**手法だけ抽出する読み方**で C3 / D2 / E5 のサーベイに織り込むのが現実的。
	- **手術ロボット・遠隔操作系(da Vinci、RAS)**:JIGSAWS など。動作粒度の理論的背景として B6 で軽く触れる程度でよい。
	- **一般映像認識・スポーツ映像解析**:長距離時系列モデル(MuST、Surgformer)の原型はスポーツ映像で先行することが多く、手法の背景理解として有用。
	### 10.3 サーベイ運用の指針
	- **読書ノートの一元管理**:本ページか別 Notion DB に「論文 ID / トピック / S 対応 / 一行要約 / 自分の研究への引用方針」を蓄積。後に §1.1 の関連研究や論文の Related Work 節に流用できる。
	- **比較表の早期作成**:同一カテゴリ内の手法(例:C3 の TeCNO vs LoViT vs SKiT vs HID-SSM)は、論文を読んだ時点で「入力長 / 計算量 / 精度 / online対応」を表に追記しておく。M3 で実装候補を選ぶ際の判断材料となる。
	- **必読論文数の目安**:各細目あたり 3〜10 本程度。優先度高は重点的に、優先度中は survey 1 本 + 代表 2〜3 本で充足する。
	- **更新リズム**:M1 / M3 / M5 のタイミングでサーベイ自体を見直し、進捗に応じて優先度・追加トピックを再評価する。
---

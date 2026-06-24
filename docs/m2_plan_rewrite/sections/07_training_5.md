## 5. 学習スキーム(段階学習) {toggle="true"}
	2 タスク結合（検出 × 工程）の学習は、**単一タスク基準の確立（STEP A）→ 結合学習（STEP B）** に簡素化する。Exo 多視点を使う段階（旧 Stage B / B′ / C）は **Phase-2 拡張**として末尾に縮約して残す（削除しない）。
	```javascript
Stage A（単一タスク基準）→ Stage D（2 タスク結合学習）  ／  Exo SSL 段階は Phase-2 拡張
	```
	### Stage A:単一タスク基準の確立（STEP A・Phase-0 主経路）〔2026/05/21 に A0/A1 に分離〕
	mask / hand-tool アノテーション不在の制約（§0.1）を反映し、Stage A を **Stage A0（bbox、現時点で実行可能）** と **Stage A1（mask、mask 入手で起動する条件付き）** に分離する。**ここで比較の三角形の分母（検出単独 = S0-frozen、工程単独 = S4）を同一凍結 backbone 上で確定させる。**
	- **Stage A0（bbox 検出学習、Phase-0 主経路）**
		- 目的:術具・手の **box** を安定化させ、**検出単独基準 S0-frozen**（凍結 backbone ＋ 検出ヘッド）の数値を確定させる。
		- 損失:`L_det`のみ。
		- 出力:bbox 検出の domain-specific strong baseline（Mask DINO の box ブランチ / VarifocalNet。検出ベースラインは Relation-DETR mAP 0.730 が現行 1 位、§4.2・§12・§13）。
	- **Stage A1（mask 学習、mask アノテーション入手で起動する条件付き）**
		- 目的:mask 入手後に術具・手の **mask** を安定化させ、instance segmentation の baseline（bbox + mask 版）を確定させる。
		- 損失:`L_det + L_mask`。
		- 出力:検出・分割の domain-specific strong baseline（Mask DINO / VarifocalNet / Mask2Former）。
		- mask が M2 期間内に入手できない場合は Stage A1 をスキップし、Stage A0 だけで結合学習（Stage D）に進む。
	- **工程単独基準 S4**：Stage A と同一の凍結 backbone 上に時系列ヘッド（TeCNO コア＋第 2 波、§4.5）を載せ、global feature 入力の工程単独基準を確定させる（§2.5(b)）。
	### Stage D：2 タスク結合学習（STEP B の各手法）〔§12 サーベイ反映〕
	- 目的:検出 × 工程の結合を学習し、単一タスク基準（S0-frozen / S4）に対する Δ を測る。**双方向フィードバック（§4.6）を on にし、結合効果①②を統合検証する。** 関係・Exo（Phase-2）は当面 off（λ_rel = λ_view = 0）。
	- 結合手法は STEP B の比較群（共有エンコーダ MTL → 片方向 pipeline → PAD-Net/MTI-Net → MT4MTL-KD/SSG-Com、§2.3・§13）を順に実装し、各手法の Δ を同一土台で測る。
	- **損失重み付け（L4 最適化系の結合・併用アドオン）：FAMO を第一候補、DB-MTL の対数変換を併用**（C6 サーベイ推奨）。O(1) コストで全タスク損失を均等降下させつつ、異なる損失スケール（CE / focal / BCE / temporal smooth）を対数変換で自動正規化。勾配系（PCGrad / CAGrad / FAMO）は主軸ではなく**併用アドオン**と位置づける。
	- **勾配制御：GCond（arXiv 2025）の勾配蓄積 + 適応的仲裁メカニズム**を Phase → Detection 経路に導入し、Phase head の未収束信号が Detection head を退化させるリスクを低減（C6 サーベイ推奨）。
	- **negative transfer 監視：LibMTL の Δp 指標**（各タスクの単一タスク比改善率の平均）で結合学習中の negative transfer をオンライン監視する（STEP C 分析の入力）。
	### Phase-2 拡張（Exo 多視点 SSL）〔旧 Stage B / B′ / C を縮約。将来拡張・削除しない〕
	Exo 多視点を使う事前学習・整合・蒸留は **Phase-2 の将来拡張**として残す。要点のみ縮約して記す（詳細設計は §4.7、§12 A4/D1/E2/E5）。
	- **Exo 単独 SSL（旧 Stage B）**：VideoMAE v2 ベースの masked video modeling を主損失に、playback speed prediction・temporal order prediction を補助に、Exo 5 視点 × 25 fps の無ラベル映像へ適用。新規手法 **hand-tool-guided MAE**（手・術具領域を優先 mask、E3 サーベイで先行例なし）。Exo 視点間 cross-view contrastive + view dropout + temporal hard negative。
	- **未ラベル Exo での DINO/iBOT 継続事前学習（旧 Stage B′）**：DINOv2 ViT-L/14-with-registers backbone に短い DINO/iBOT 継続事前学習（E2 サーベイ：SurgeNetXL の追試）。held-out で 2% 未満の gain ならスキップ可。
	- **Ego–Exo cross-view alignment & 蒸留（旧 Stage C）**：時間同期 contrastive（fps 差 50 倍は Ego 1 フレーム ±2 秒を co-occurrence unit に）+ Phase 分布整合 KL + tool-set 弱整合（PU loss）+ teacher–student 蒸留（Quattrocchi 式 2-level KD + AE2 / AlignEgoExo temporal alignment、E2/E5/D1）。推論時は Exo ブランチを切り Ego 単独動作。
---

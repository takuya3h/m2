## 6. 損失関数(全体像) {toggle="true"}
	$$
	L = \lambda_{det} L_{det} + \lambda_{mask} L_{mask} + \lambda_{rel} L_{rel} + \lambda_{phase} L_{phase} + \lambda_{temp} L_{temp\\_smooth} + \lambda_{ssl} L_{contrast/MAE} + \lambda_{kd} L_{distill} + \lambda_{view} L_{view\\_consist}
	$$
	- `L_det`:Ego 検出(教師あり、bbox)。Phase-0 から有効。
	- `L_mask`:Ego 分割(教師あり)。**Phase-1 で起動する条件付き項〔mask アノテーション入手まで λ_mask = 0、2026/05/21 明記〕**。
	- `L_rel`:手-術具関係(疑似ラベル、BCE / focal)。**Phase-1 で起動する条件付き項〔mask / hand-tool アノテーション入手まで λ_rel = 0、2026/05/21 明記〕**。
	- `L_phase`:9 クラス CE(class weight、label smoothing)。Phase-0 から有効。
	- `L_temp_smooth`:近傍フレームの Phase 一貫性 + transition penalty。
	- **`L_couple`(2 タスク結合の損失・STEP B)**:結合手法に応じた予測蒸留/整合損失(PAD-Net/MTI-Net 型)と最適化バランシング(FAMO/DB-MTL、§5 Stage D)。これが「タスク結合の効果」を生む主機構。
	- `L_contrast/MAE`:Exo 自己教師あり(**Phase-2 項**、旧 Stage B/C で有効)。
	- `L_distill`:Exo teacher → Ego student(KL / feature matching)。
	- `L_view_consist`:Ego–Exo 同時刻整合(Phase logits KL + tool-set PU)。
	**λ_mask と λ_rel は Phase-2(mask / hand-tool アノテーション入手で起動)の条件付き項であり、入手まで 0 に固定する。同様に Exo 系(λ_ssl・λ_kd・λ_view)も Phase-2 項で当面 0。Phase-0 の主経路(検出 × 工程の 2 タスク結合)は `L_det`・`L_phase`・`L_temp_smooth`(＋ `L_couple`)で成立する。** **動作(Action)関連の損失は本フェーズでは設定しない。** 関係モジュールは将来的な動作認識への足場として残す。
---

## 3. データ運用方針 {toggle="true"}
	### 3.1 Ego 映像(EgoSurgery 系)
	- 仕様は `研究方針_2026/05/14` の表に準拠(Train 10 / Val 2 / Test 3、0.5 fps)。
	- **現時点で利用可能な学習信号（Phase-0 主経路）**：
		- 術具 **bbox**（`EgoSurgery-Tool`、15 クラス）
		- 手 **bbox**（`EgoSurgery-Tool`、4 クラス：own/other × L/R）
		- 工程ラベル 9 クラス（`EgoSurgery-Phase`）
	- **mask / hand-tool アノテーションの状況〔2026/05/21 晠明記〕**：術具・手の **mask（instance segmentation）** および **Hand-Tool セグメンテーションから派生する手-術具関係** は、現時点で未準備であり、入手時期も不確定である。これらは **§0.1 Phase-1 で起動する条件付き学習信号** として扱い、mask 入手を待って instance segmentation（旧 S1）と関係モジュール（Phase-2＝将来拡張）に供給する。Phase-0 の主経路は mask を一切要求しない。
	- mask 入手時期の見込みが立ち次第、本節に実際の入手源（公開 EgoSurgery-HTS / 自施設アノテーション など）と見込み時期を追記する。
	### 3.2 Exo 映像(俯瞰多視点 Raw データ)
	- 5 視点、25 fps、640×540、画角は術野近傍のみ、アノテーションなし。
	- **本研究では一切アノテーションを行わない。**
	- 利用方法は以下の **補助タスク** に限定する。
		1. **自己教師あり事前学習**:VideoMAE 系の masked video modeling、playback speed prediction、temporal order prediction。
		2. **Ego–Exo 時間同期 contrastive learning**:同時刻の Ego フレームと Exo クリップを正例ペアとする。
		3. **弱教師あり学習(ラベル転写)**:Ego の Phase ラベルを同時刻の Exo に転写し、Exo 側にも Phase head を持たせる(Exo の Phase head は **学習時のみ** 使用)。
		4. **teacher–student 蒸留**:Exo 側で学習した時間表現を Ego 側に転写し、低 fps Ego の時間表現を強化する。
		5. **View dropout / visibility-aware fusion** による多視点冗長性の取り込み(Ego 表現の頑健性向上)。
	- 推論時には **Exo 経路を一切使わない**(該当パラメータは無効化または除去)。
	### 3.3 クラス不均衡対応〔§12 サーベイ反映：F1 で更新、2026/05/21 に temporal-consistent copy-paste を追加・mask 依存項を Phase-1 条件付きに明記〕
	クラス不均衡対策は、Phase-0（bbox）で完結する手法と、mask を要するため Phase-1 で起動する手法に分けて整理する。
	- 術具:最大 Tweezers 20.2% / 最小 Skewer 0.7%(約 30 倍差)。Forceps は 12.21% でトップ 3 に位置する頻出クラスであり、稀少クラスには該当しない〔2026/05/24 訂正：旧値 1.22% → 正値 12.21%〕。
		- **即時採用（Phase-0、bbox だけで実行可）**（F1 サーベイ）:post-hoc Logit Adjustment（全分類ヘッド、実装 1 行・コスト無し）、Seesaw Loss（p=0.8, q=2.0、検出器分類ヘッド）、Repeat Factor Sampling（t=0.001）、Decoupled cRT、bbox-level Copy-Paste（Skewer/Syringe を bbox crop として貼り付け、mask 不要の簡易版）。
		- **提案手法：temporal-consistent copy-paste（mask 入手で完全版起動、§0.1 Phase-1）**（2026/05/21 追加）。F1 サーベイは「0.5 fps 低 fps 動画での Copy-Paste/Mixup の時系列一貫性」が未開拓のギャップであると指摘した。naive な Simple Copy-Paste をフレーム独立に適用すると、貼り付けた稀少術具インスタンスがフレーム間で出現・消失を繰り返し、object token 列・時系列 Phase head（§4.5）の時間表現を汚染する。本研究では、稀少クラスのインスタンスを **同一クリップ内の連続フレームにわたって時間的に整合した位置・スケールで貼り付ける**（軌跡を線形補間し、隣接フレームで mask が連続するよう配置する）temporal-consistent copy-paste を提案手法とする。**mask を使う完全版は Phase-1 で起動する**が、Phase-0 でも bbox crop を用いた簡易版（軌跡補間は bbox 中心で行う）を先行実装できる。これにより S4 以降の時系列タスクと矛盾しない長尾拡張が可能となり、§8.2 の長尾損失 ablation の独立 contribution（下記）と接続する。
		- **検証推奨**（STEP B・§8.2 長尾 ablation）:EQLv2 vs Seesaw vs Logit Adjustment の直接比較。これらの長尾損失・サンプリング・拡張の系統的比較は、F1 サーベイで「手術・Ego 映像での標準長尾損失の系統的ベンチマークが不在」と確認されたため、**それ自体を独立した contribution**（手術 Ego マルチタスク設定での初の長尾手法ベンチマーク）として §8.2 に位置づける。長尾損失・サンプリングの比較は bbox だけで実行できるため Phase-0 に属する。
		- **採用見送り**:Focal Loss 単独（頻度を直接扱わず弱い）、naive Class-Balanced Sampling 単独（backbone 表現を劣化）、DINOv2 の heavy full fine-tuning（LIFT が tail-class 悪化を示す—LoRA/Adapter 必須）、CutMix を形状類似ペアに直接適用（混同悪化、Remix を検討）、フレーム独立な naive Copy-Paste（上記 temporal-consistent 版で置換）。
	- 工程:Dissection 44.1% + Closure 34.3% で約 8 割。
		- Balanced Softmax（TeCNO/SR-Mamba の工程ヘッド）、temporal smoothing による境界正則化、LoViT 風 Asymmetric Gaussian heatmap の工程遷移 prior。
		- **class weights の実装上の注意〔2026/05/24 追加、§14 と整合〕**：§14 で S3 の Phase head に class weights を不適切に与えた結果、val accuracy が 0.5% に崩壊した実例がある。逆頻度ベースの class weight は、極端な値（Dissection と稀少工程の頻度比が大きい）が学習を不安定化させうる。Phase ヘッドの class weight はデフォルト無効とし、有効化する場合も weight の最大/最小比を上限（例 10 倍）でクリップする。label smoothing（0.1）は安定化のため常に併用する。Balanced Softmax を使う場合も同様に極端な補正を避ける。
---

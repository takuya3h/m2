## 15. Lessons Learned & 整合性検証規則 {toggle="true"}
	本節は S0 完走後に発覚した split 取り違えと評価条件不整合を契機に、Δ 評価方法論の前提条件を明文化したものである（2026-05-24 追加）。研究計画の他節（§2.5 / §7.1 / §10.1 / §13.1 / §13.6 / §13.8）への波及は §15.4 を参照。
	### 15.1 失敗事象 #1：データ split の取り違え（最重要）
	- **症状**: S0 (VarifocalNet seed42) test mAP = **0.388**、公式 SOTA 0.458 まで -7pt。当初は recipe（schedule・augmentation・長尾対策）の差と仮定していた。
	- **発覚契機**: 論文 §2.1 と Table 3a の data split サイズを手元の `instances_*.json` と突き合わせた結果、train/val が論文と異なることを発見。
	- **根本原因**:
		- `data/splits/ego_train.txt` が **8 videos** (01,02,03,06,08,11,12,13)、`ego_val.txt` が **2 videos** (14,15)、`ego_test.txt` が 3 videos (04,05,07) になっていた。
		- 論文公式は **train=10 videos** (上記 8 + 14, 15) / **val=2 videos** (09, 10) / **test=3 videos** (04, 05, 07)。
		- ディスク (`data/raw/ego/{train,val,test}/`) と hand 注釈 (`hand/*.json`) は論文準拠だが、tool 注釈 (`instances_*.json`) のみ独自再分割していた。
		- 結果として **train が 23% 不足**（9,657 → 7,427 imgs、32,272 → 21,988 anns）、**val は別動画（14,15 vs 09,10）** で論文比較不能。
	- **データ証拠**: 公式 tool 注釈は `data/annotations/egosurgery_tool/tool/{train,val,test}.json` に存在していた（image=9657/1515/4265、annotation=32272/4707/12673 で論文 Table 3a と完全一致）。前チームはこれを参照せず独自再分割していた。
	- **影響**: 旧 split で学習した S0 6 実験（_wrong_split_8_2_3 へ退避）は Δ 基準点として使用不可。
	### 15.2 失敗事象 #2：test_cfg score_thr が論文と不一致
	- **症状**: mmdet VFNet の `test_cfg.score_thr = 0.05`（mmdet detector default）。論文 §3.1 末尾は `confidence = 10^-8` を使用。
	- **実測影響**: 0.388 → 0.389（+0.1pt のみ）。`nms_pre=1000 → NMS → max_per_img=100` で top-100 cap が支配的なため。
	- **真の効果は ****`max_per_img`**** 拡張**: dense シーン（11-15 instances/img × 506 枚、論文 Table 2）で 100 cap が低 confidence True Positive を切る可能性。
	- **対処**: G1 で `score_thr=1e-8, max_per_img=300, nms_pre=3000` を全 detector で強制統一。
	### 15.3 再発防止策（G1-G3、コード反映済み）
	- **G1: ****`MMDetTrainer._build_mmdet_cfg`**** で test_cfg を locked-down 上書き**
		- 全 detector・全 stage で `score_thr=1e-8, max_per_img=300, nms_pre=3000, nms_iou=0.6` を強制。
		- detector ごとの mmdet default 差が Δ 計算に混入することを防ぐ。
	- **G2: ****`scripts/preprocess_ego.py`**** に論文 Table 3a 整合性 assertion**
		- 生成された `instances_*.json` の (image, annotation, video) 数が論文値と一致しなければ `AssertionError`。
		- `data/splits/ego_*.txt` も論文準拠（train=10, val=\{09,10\}, test=\{04,05,07\}）に修正済み。
	- **G3: ****`metrics.json`**** に ****`eval_recipe`**** field を併記**
		- `test_cfg` 全項目 + train/val/test の image・annotation 数を記録。
		- Δ 計算時に異なる recipe での比較を自動拒否できる土台。
	### 15.4 研究計画への反映（A〜F）
	- **A. §2.5(a) S0 基準点定義の strict 化**
		- S0 は以下 3 条件すべてを満たすときに正当な Δ 基準点として採用する:
			1. データ split が EgoSurgery-Tool 公式 (train 9657 / val 1515 / test 4265)
			2. test_cfg が G1 の locked-down 値
			3. metrics.json の `eval_recipe` がこれらと一致
		- 既存 §2.5 の「成功条件 (a)(b)(c)」を補強する位置づけ。
	- **B. §7.1 Δ 計算の前提条件**
		- Δ は **同一 eval recipe で測定された値同士でのみ意味を持つ**。`DeltaCalculator` は両 metrics.json の `eval_recipe` を比較し、不一致時は例外（実装予定: pipeline_implementation_[prompt.md](http://prompt.md) §2.7 拡張）。
		- 旧 split で測った S0 (mAP 0.278 val / 0.388 test) は基準点に使えない。
	- **C. §10.1「Δ が 1σ 以内なら改善と主張しない」の補足**
		- ここでいう 1σ は **同一 eval recipe での 3-seed std**。recipe 差由来の variance は 1σ に含めない。
		- recipe を変えるアブレーション（例: `score_thr × max_per_img` sensitivity）は §3 で **別表として分離**して報告する。
	- **D. §13.6 標準スケジュール / §3 実験テーブル footnote**
		- 論文化を想定した全実験表に、locked-down recipe（score_thr / max_per_img / nms / split sizes）を脚注で明記する。reviewer が Δ improvement の正当性を検証可能にする。
	- **E. §13.1 / §13.8 Reproducibility 厳格化**
		- `data/splits/ego_*.txt` を論文準拠で git 管理（変更禁止）。
		- `preprocess_ego.py` の assert_paper_split が CI / 起動時チェックの最後の砦。
		- `MMDetTrainer` が test_cfg を locked-down で上書きする運用を明文化。
	- **F. 本節（§15）の常設化**
		- 今後の整合性関連の発見・対処は §15 に蓄積する。研究 integrity を honest に開示する位置として論文 supplementary に展開可能。
	### 15.5 過去実験の扱い
	- 旧 split / 旧 test_cfg で測定した数値は **Δ 基準点として使用不可**。
	- 退避場所:
		- `experiments/baselines/_wrong_split_8_2_3/`（S0 6 実験、旧 split）
		- `experiments/phase0/_failed_s3_weighted/`（S3 初回・class weights 不適切）
	- 各失敗実験は scientific record として保存（捏造でなく実測値）。論文では "prior measurement" として明示するか、撤回する。
	### 15.6 今後の運用ルール
	- 全新規実験で `MMDetTrainer`（test_cfg locked-down）+ `assert_paper_split` + `eval_recipe` 併記が必須。
	- `DeltaCalculator` 実装拡張: `compute_delta()` で両側の `eval_recipe` を比較し、不一致なら `InconsistentRecipeError`。
	- M3 / 論文 supplementary に Failure mode セクション (§15.1-15.2) を honest 開示として組み込む。
---

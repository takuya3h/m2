# プロジェクトディレクトリ構築プロンプト

あなたはCV研究プロジェクト「egosurgery_multitask」のディレクトリ構造を構築するコーディングエージェントです。
以下の仕様に従い、プロジェクトルートディレクトリを整形してください。

---

## 0. 大前提

- **プロジェクトルート**: カレントディレクトリを `egosurgery_multitask/` として構築する。既にファイルがある場合はそれを尊重し、不足分を追加する。
- **末端ファイルは原則空**: `__init__.py` は空ファイル、`.py` / `.yaml` / `.sh` / `.ipynb` / `.tex` なども原則空ファイルとして `touch` で作成する。**ただし、以下のセクションで「実装する」と明記したファイルはコードを実装すること。**
- **README.md は内容を書く**: 各ディレクトリの README.md にはそのディレクトリの設計思想と使い方を記載する（後述のテンプレートに従う）。
- **experiments/ は空のディレクトリだけ作る**: experiments/ 配下のサブフォルダ（baselines/ phase0/ phase1/ ablations/ transfer/ final/）までは作成するが、個別の実験フォルダ（例: s0_001_maskdino_bbox_seed42/）は作らない。代わりに、実験実行時に自動で正しい構造が生成される仕組みを `src/egosurgery/utils/experiment_manager.py` に実装する。

---

## 1. 設計思想（README.md に記載する内容の根幹）

本プロジェクトの設計原則は以下の7つである。README.md の冒頭にこれらを記載すること。

1. **`src/` と `configs/` と `experiments/` を絶対に分ける** — コード・設定・実験結果の混在は再現性を壊す。
2. **すべての実験に「証拠」を残す** — 各実験フォルダには最低限 config.yaml / command.sh / git_commit.txt / metrics.json / notes.md を自動保存する。
3. **`data/` は Git 管理しない** — ただし `data/splits/` と `data/README.md` は Git 管理する。
4. **Phase-0 / Phase-1 の 2 フェーズ構成を構造に反映** — mask アノテーション依存のモジュールを条件付きとして分離する。
5. **S0〜S9 のステップと実験を対応づける** — 連番付き命名規則で Δ 基準点の追跡性を担保する。
6. **Ego / Exo のデータパイプラインを明示的に分離** — 推論時 Ego 単独の制約を構造で保証する。
7. **論文は最初から作る** — `paper/` は Day 1 から存在する。

---

## 2. ディレクトリ構造（この通りに作成する）

```
egosurgery_multitask/
├── README.md
├── pyproject.toml
├── requirements.txt
├── environment.yml
├── .gitignore
├── .env.example
├── Makefile
├── LICENSE
│
├── configs/
│   ├── default.yaml
│   ├── model/
│   │   ├── backbone/
│   │   │   ├── dinov2_vitl14_reg.yaml
│   │   │   ├── dinov2_vitb14_reg.yaml
│   │   │   ├── surgenetxl_caformer.yaml
│   │   │   ├── endovit_vitb.yaml
│   │   │   └── swin_large.yaml
│   │   ├── detection_head/
│   │   │   ├── mask_dino.yaml
│   │   │   ├── varifocanet.yaml
│   │   │   ├── co_detr.yaml
│   │   │   └── eomt.yaml
│   │   ├── temporal/
│   │   │   ├── tecno.yaml
│   │   │   ├── sr_mamba.yaml
│   │   │   ├── sr_mamba_blockdiag.yaml
│   │   │   ├── hid_ssm.yaml
│   │   │   ├── skit.yaml
│   │   │   ├── surgformer.yaml
│   │   │   └── sprmamba.yaml
│   │   ├── phase_injection/
│   │   │   ├── cross_attention.yaml
│   │   │   ├── film.yaml
│   │   │   └── sak_adapter_bias.yaml
│   │   ├── relation/
│   │   │   ├── gnn_pvic.yaml
│   │   │   └── disabled.yaml
│   │   ├── exo/
│   │   │   ├── hiera_b_videomae.yaml
│   │   │   ├── ego_egovlpv2.yaml
│   │   │   └── disabled.yaml
│   │   └── object_token/
│   │       ├── detector_based.yaml
│   │       ├── slot_attention.yaml
│   │       └── global_feature.yaml
│   ├── data/
│   │   ├── egosurgery_tool.yaml
│   │   ├── egosurgery_phase.yaml
│   │   ├── egosurgery_hts.yaml
│   │   ├── exo_raw.yaml
│   │   ├── phakir.yaml
│   │   ├── cholect45.yaml
│   │   └── egoexor.yaml
│   ├── train/
│   │   ├── stage_a0.yaml
│   │   ├── stage_a1.yaml
│   │   ├── stage_b.yaml
│   │   ├── stage_b_prime.yaml
│   │   ├── stage_c.yaml
│   │   └── stage_d.yaml
│   ├── stage/
│   │   ├── s0_tool_baseline.yaml
│   │   ├── s1_mask.yaml
│   │   ├── s2_hand.yaml
│   │   ├── s3_phase_frame.yaml
│   │   ├── s4_temporal.yaml
│   │   ├── s5_object_token.yaml
│   │   ├── s6_bidirectional.yaml
│   │   ├── s7_relation.yaml
│   │   ├── s7_5_exo_diagnostic.yaml
│   │   ├── s8_exo_ssl.yaml
│   │   └── s9_final.yaml
│   ├── experiment/
│   │   ├── ablation_a1_h1.yaml
│   │   ├── ablation_a2_h2.yaml
│   │   ├── ablation_a3_phase2det.yaml
│   │   ├── ablation_a4_det2phase.yaml
│   │   ├── ablation_a5_relation.yaml
│   │   ├── ablation_a6_exo_ssl.yaml
│   │   ├── ablation_a7_design_da.yaml
│   │   ├── longtail_benchmark.yaml
│   │   └── backbone_comparison.yaml
│   └── sweep/
│       ├── lr_batchsize.yaml
│       └── loss_weights.yaml
│
├── data/
│   ├── README.md
│   ├── raw/
│   │   ├── ego/
│   │   │   ├── train/
│   │   │   ├── val/
│   │   │   └── test/
│   │   └── exo/
│   │       ├── view_1/
│   │       ├── view_2/
│   │       ├── view_3/
│   │       ├── view_4/
│   │       └── view_5/
│   ├── annotations/
│   │   ├── egosurgery_tool/
│   │   ├── egosurgery_phase/
│   │   ├── egosurgery_hts/
│   │   └── pseudo_labels/
│   │       ├── hand_tool_relation/
│   │       ├── exo_phase_transfer/
│   │       └── bbox_near_contact/
│   ├── processed/
│   │   ├── ego_frames/
│   │   ├── exo_clips/
│   │   ├── features/
│   │   └── copypaste_bank/
│   ├── external/
│   │   ├── phakir/
│   │   ├── cholect45/
│   │   └── egoexor/
│   └── splits/
│       ├── ego_train.txt
│       ├── ego_val.txt
│       ├── ego_test.txt
│       ├── exo_sync_map.json
│       └── surgeon_folds.json
│
├── src/
│   └── egosurgery/
│       ├── __init__.py
│       ├── train.py
│       ├── evaluate.py
│       ├── infer.py
│       ├── datasets/
│       │   ├── __init__.py
│       │   ├── ego_dataset.py
│       │   ├── exo_dataset.py
│       │   ├── ego_exo_paired.py
│       │   ├── temporal_dataset.py
│       │   ├── transforms.py
│       │   ├── copypaste.py
│       │   ├── samplers.py
│       │   └── datamodule.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── build.py
│       │   ├── backbones/
│       │   │   ├── __init__.py
│       │   │   ├── dinov2_registry.py
│       │   │   ├── vit_adapter.py
│       │   │   └── peft.py
│       │   ├── heads/
│       │   │   ├── __init__.py
│       │   │   ├── mask_dino_head.py
│       │   │   ├── varifocanet_head.py
│       │   │   ├── phase_head.py
│       │   │   └── relation_head.py
│       │   ├── temporal/
│       │   │   ├── __init__.py
│       │   │   ├── tecno.py
│       │   │   ├── sr_mamba.py
│       │   │   ├── hid_ssm.py
│       │   │   ├── skit.py
│       │   │   └── surgformer.py
│       │   ├── object_token/
│       │   │   ├── __init__.py
│       │   │   ├── detector_token.py
│       │   │   ├── slot_attention.py
│       │   │   └── token_pool.py
│       │   ├── feedback/
│       │   │   ├── __init__.py
│       │   │   ├── phase_to_det.py
│       │   │   ├── det_to_phase.py
│       │   │   ├── entropy_gate.py
│       │   │   └── gradient_ctrl.py
│       │   ├── relation/
│       │   │   ├── __init__.py
│       │   │   ├── gnn_pvic.py
│       │   │   ├── edge_features.py
│       │   │   ├── pseudo_label_gen.py
│       │   │   └── memory_graph.py
│       │   ├── exo/
│       │   │   ├── __init__.py
│       │   │   ├── exo_encoder.py
│       │   │   ├── view_gating.py
│       │   │   ├── cross_view_ssl.py
│       │   │   ├── hand_tool_mae.py
│       │   │   ├── distillation.py
│       │   │   └── branch_pruning.py
│       │   └── losses/
│       │       ├── __init__.py
│       │       ├── detection.py
│       │       ├── segmentation.py
│       │       ├── phase.py
│       │       ├── temporal.py
│       │       ├── relation.py
│       │       ├── ssl.py
│       │       ├── distill.py
│       │       ├── view_consist.py
│       │       ├── logit_adjust.py
│       │       ├── class_balanced_denoising.py
│       │       └── mtl_balancer.py
│       ├── engines/
│       │   ├── __init__.py
│       │   ├── trainer.py
│       │   ├── stage_a_trainer.py
│       │   ├── stage_b_trainer.py
│       │   ├── stage_c_trainer.py
│       │   ├── stage_d_trainer.py
│       │   ├── validator.py
│       │   └── hooks.py
│       ├── metrics/
│       │   ├── __init__.py
│       │   ├── detection.py
│       │   ├── segmentation.py
│       │   ├── phase.py
│       │   ├── relation.py
│       │   ├── delta.py
│       │   ├── confusion_matrix.py
│       │   └── phase_conditional_ap.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── seed.py
│       │   ├── logging.py
│       │   ├── checkpoint.py
│       │   ├── visualization.py
│       │   ├── git_utils.py
│       │   ├── gpu_monitor.py
│       │   ├── experiment_id.py
│       │   └── experiment_manager.py    # ★ 実装する（後述）
│       └── analysis/
│           ├── __init__.py
│           ├── embedding.py
│           ├── failure_cases.py
│           ├── attention_map.py
│           ├── statistics.py
│           ├── longtail_analysis.py
│           └── phase_boundary.py
│
├── scripts/
│   ├── download_data.sh
│   ├── preprocess_ego.py
│   ├── preprocess_exo.py
│   ├── generate_copypaste_bank.py
│   ├── generate_pseudo_labels.py
│   ├── sync_ego_exo.py
│   ├── run_s0.sh
│   ├── run_s2.sh
│   ├── run_s3.sh
│   ├── run_s4.sh
│   ├── run_s4_wave2.sh
│   ├── run_s5.sh
│   ├── run_s6.sh
│   ├── run_s7_5.sh
│   ├── run_s8.sh
│   ├── run_s9.sh
│   ├── run_ablation_all.sh
│   ├── eval.sh
│   ├── compute_delta.py
│   ├── export_paper_tables.py
│   ├── submit_job.sh
│   └── profile_speed.py
│
├── notebooks/
│   ├── README.md
│   ├── 00_sanity_check.ipynb
│   ├── 01_data_exploration.ipynb
│   ├── 02_class_distribution.ipynb
│   ├── 03_ego_exo_sync_check.ipynb
│   ├── 04_failure_analysis.ipynb
│   ├── 05_delta_visualization.ipynb
│   └── 06_phase_conditional_ap.ipynb
│
├── experiments/
│   ├── README.md
│   ├── baselines/
│   ├── phase0/
│   ├── phase1/
│   ├── ablations/
│   ├── transfer/
│   └── final/
│
├── outputs/
│   ├── figures/
│   │   ├── qualitative/
│   │   ├── quantitative/
│   │   ├── paper/
│   │   └── presentation/
│   ├── tables/
│   └── reports/
│       ├── weekly_progress/
│       └── milestone_reports/
│
├── docs/
│   ├── idea_log.md
│   ├── experiment_log.md
│   ├── reading_notes/
│   │   ├── A_domain/
│   │   ├── B_task/
│   │   ├── C_architecture/
│   │   ├── D_temporal/
│   │   ├── E_learning/
│   │   ├── F_signal/
│   │   └── G_evaluation/
│   ├── meeting_notes/
│   ├── decision_log.md
│   └── TODO.md
│
├── paper/
│   ├── main.tex
│   ├── sections/
│   │   ├── abstract.tex
│   │   ├── introduction.tex
│   │   ├── related_work.tex
│   │   ├── method.tex
│   │   ├── experiments.tex
│   │   ├── ablation.tex
│   │   └── conclusion.tex
│   ├── figures/
│   ├── tables/
│   ├── references.bib
│   ├── supplementary/
│   │   ├── supp.tex
│   │   ├── phase_conditional_ap.tex
│   │   └── full_per_class_ap.tex
│   └── rebuttal/
│       └── rebuttal_template.tex
│
├── tests/
│   ├── test_datasets.py
│   ├── test_models.py
│   ├── test_losses.py
│   ├── test_metrics.py
│   ├── test_delta.py
│   ├── test_phase_injection.py
│   ├── test_branch_pruning.py
│   └── test_reproducibility.py
│
└── tools/
    ├── convert_checkpoint.py
    ├── profile_speed.py
    ├── count_params.py
    ├── visualize_attention.py
    ├── visualize_object_tokens.py
    ├── verify_pseudo_labels.py
    ├── export_wandb_tables.py
    ├── generate_delta_report.py
    └── gpu_allocation_plan.py
```

---

## 3. 実装が必要なファイル（空にしてはいけないファイル）

以下のファイルは空にせず、コードまたは内容を実装すること。

### 3.1 `src/egosurgery/utils/experiment_manager.py` — ★最重要

実験を開始するたびに、正しい構造の実験フォルダを自動生成するモジュール。以下の要件を満たすこと。

```python
"""
ExperimentManager: 実験フォルダの自動生成・管理

使い方:
    manager = ExperimentManager(
        base_dir="experiments",
        category="baselines",     # baselines / phase0 / phase1 / ablations / transfer / final
        step="s0",                # s0 / s1 / s2 / ... / s9 / a1 / a2 / ...
        description="maskdino_bbox",
        seed=42,
    )
    exp_dir = manager.setup()
    # → experiments/baselines/s0_001_maskdino_bbox_seed42/ が作成される

自動で作成されるファイル・フォルダ:
    {exp_dir}/
    ├── config.yaml          # Hydra の resolved config のコピー（setup時に渡す）
    ├── command.sh           # 実行コマンドの記録（sys.argv から自動生成）
    ├── git_commit.txt       # git rev-parse HEAD の結果
    ├── metrics.json         # 空の {} で初期化、学習中に更新
    ├── per_class_ap.json    # 空の {} で初期化、評価時に更新
    ├── notes.md             # テンプレート付きで初期化（仮説/結果/解釈/次）
    ├── logs/                # 空ディレクトリ
    ├── checkpoints/         # 空ディレクトリ
    ├── predictions/         # 空ディレクトリ
    └── visualizations/      # 空ディレクトリ
"""
```

実装の要件:
- **連番の自動採番**: 同じ category + step の既存フォルダを走査し、次の連番（3桁ゼロ埋め）を自動決定する。例: `s0_001_...` が存在すれば次は `s0_002_...`。
- **命名規則**: `{step}_{連番3桁}_{description}_seed{seed}` を厳密に守る。
- **git_commit.txt**: `subprocess` で `git rev-parse HEAD` を実行し結果を保存する。git リポジトリでない場合は "NOT_A_GIT_REPO" を書く。
- **command.sh**: `sys.argv` の内容を保存する。
- **notes.md**: 以下のテンプレートで初期化する。

```markdown
# {step}_{連番}_{description}_seed{seed}

作成日時: {ISO 8601 タイムスタンプ}

## 仮説
（ここに記入）

## 実験設定
- Category: {category}
- Step: {step}
- Seed: {seed}
- Config: （config.yaml を参照）

## 結果
（実験完了後に記入）

## 解釈
（結果の意味、期待との差、原因の仮説）

## 次の行動
1. ...
```

- **config.yaml の保存**: `save_config(cfg: DictConfig)` メソッドで OmegaConf の resolved config を YAML として保存する。
- **metrics の追記**: `log_metrics(metrics: dict)` メソッドで metrics.json を上書き保存する。
- **per_class_ap の追記**: `log_per_class_ap(ap_dict: dict)` メソッドで per_class_ap.json を上書き保存する。

### 3.2 `src/egosurgery/utils/experiment_id.py`

連番付き実験 ID を生成するユーティリティ。experiment_manager.py から呼び出される。

```python
"""
実験 ID の生成ユーティリティ

命名規則: {step}_{seq:03d}_{description}_seed{seed}

例:
  generate_experiment_id("experiments/baselines", "s0", "maskdino_bbox", 42)
  → "s0_001_maskdino_bbox_seed42"  (初回)
  → "s0_002_maskdino_bbox_seed42"  (2回目、同じ step の既存フォルダがある場合)
"""
```

### 3.3 `src/egosurgery/utils/seed.py`

```python
"""
再現性のための seed 固定ユーティリティ。
random, numpy, torch, cuda, cudnn を全て固定する。
"""
```

実装する内容:
```python
def seed_everything(seed: int = 42) -> None:
    """全乱数生成器のシードを固定する"""
    import random, os
    import numpy as np
    import torch
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

### 3.4 `src/egosurgery/utils/git_utils.py`

```python
"""git commit hash を取得・保存するユーティリティ"""
```

実装する内容:
- `get_git_commit() -> str`: `git rev-parse HEAD` を実行して返す。失敗時は "NOT_A_GIT_REPO" を返す。
- `save_git_commit(path: Path) -> None`: 上記の結果をファイルに書き出す。

### 3.5 各 README.md

以下の README.md にはそれぞれ内容を記載する。

#### `README.md`（プロジェクトルート）

以下を含む:
- プロジェクト名と1行説明
- セクション1の7つの設計原則
- セットアップ手順（`pip install -e .`）
- ディレクトリ構造の概要（configsの4軸、srcの構造、experimentsのカテゴリ）
- 実験の実行方法（`make s0` の例）
- 命名規則の説明

#### `experiments/README.md`

以下を含む:
- experiments/ の6つのカテゴリ（baselines / phase0 / phase1 / ablations / transfer / final）の説明
- 命名規則 `{step}_{seq:03d}_{description}_seed{seed}` の説明と例
- 各実験フォルダに自動生成されるファイルの一覧と説明
- Git で管理するファイル（config.yaml, command.sh, git_commit.txt, metrics.json, notes.md）と管理しないファイル（checkpoints/, logs/, predictions/, visualizations/）の区別
- `ExperimentManager` の使い方の例

#### `data/README.md`

以下を含む:
- データ取得手順（EgoSurgery-Tool / Phase / HTS のダウンロード先）
- ディレクトリ内の各フォルダの用途
- `splits/` のデータ分割定義の説明
- Git 管理方針（raw/ processed/ external/ は .gitignore、splits/ README.md は管理する）

#### `notebooks/README.md`

以下を含む:
- ノートブックの使い方のルール（探索用のみ、本番実験はやらない）
- 各ノートブックの番号と目的の一覧

#### `docs/experiment_log.md`

以下のテンプレートで初期化する:

```markdown
# 実験ログ

全実験で「仮説→実験→結果→解釈→次の行動」を記録する。

---

## YYYY-MM-DD — [S?] 短い説明

### 仮説

### 実験
- 実験 ID:
- 変更した軸:

### 結果

### 解釈

### 次の行動
1.
```

### 3.6 `.gitignore`

以下の内容で作成する:

```gitignore
# === データ ===
data/raw/
data/annotations/**/*.json
data/annotations/egosurgery_hts/
data/annotations/pseudo_labels/
data/processed/
data/external/

# === 実験結果（大容量） ===
experiments/**/checkpoints/
experiments/**/logs/
experiments/**/predictions/
experiments/**/visualizations/
experiments/**/*.npy
experiments/**/*.pt
experiments/**/*.pth

# === モデル重み ===
*.pth
*.pt
*.ckpt
*.onnx
*.safetensors

# === W&B ===
wandb/

# === Python ===
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/

# === 仮想環境 ===
.venv/
venv/

# === IDE ===
.vscode/
.idea/
*.swp
*~
.DS_Store

# === Jupyter ===
.ipynb_checkpoints/

# === 環境変数 ===
.env

# === LaTeX ===
paper/*.aux
paper/*.log
paper/*.out
paper/*.toc
paper/*.bbl
paper/*.blg
paper/*.fdb_latexmk
paper/*.fls
paper/*.synctex.gz
paper/sections/*.aux

# === Git 管理する例外 ===
!data/README.md
!data/splits/
!data/splits/*
!experiments/README.md
!experiments/**/config.yaml
!experiments/**/command.sh
!experiments/**/git_commit.txt
!experiments/**/metrics.json
!experiments/**/per_class_ap.json
!experiments/**/notes.md
```

### 3.7 `.env.example`

```bash
WANDB_API_KEY=your_api_key_here
WANDB_PROJECT=egosurgery_multitask
DATA_ROOT=/path/to/data
DINOV2_WEIGHTS=/path/to/dinov2_vitl14_reg4_pretrain.pth
CUDA_VISIBLE_DEVICES=0
```

### 3.8 `Makefile`

```makefile
.PHONY: setup test lint s0 s2 s4 s5 s6 eval delta

setup:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src/egosurgery

lint:
	ruff check src/ tests/
	black --check src/ tests/

format:
	ruff check --fix src/ tests/
	black src/ tests/

s0:
	bash scripts/run_s0.sh

s2:
	bash scripts/run_s2.sh

s4:
	bash scripts/run_s4.sh

s5:
	bash scripts/run_s5.sh

s6:
	bash scripts/run_s6.sh

eval:
	bash scripts/eval.sh

delta:
	python scripts/compute_delta.py

tables:
	python scripts/export_paper_tables.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

---

## 4. data/splits/ 内のファイル

`data/splits/` 配下のファイルは空ファイルで作成する（`.txt` は空、`.json` は `{}` を書く）。ファイル一覧:
- `ego_train.txt`
- `ego_val.txt`
- `ego_test.txt`
- `exo_sync_map.json` — `{}` を書く
- `surgeon_folds.json` — `{}` を書く

---

## 5. 作業手順

1. まずプロジェクトルートディレクトリを作成する。
2. セクション2のツリー構造に従い、全ディレクトリを `mkdir -p` で作成する。
3. セクション3で「実装する」と指定されたファイルを実装する。
4. それ以外の末端ファイルは `touch` で空ファイルとして作成する。ただし:
   - `.json` ファイルは `{}` を書く
   - `__init__.py` は空ファイル
   - `.ipynb` は最小限の有効な JSON (`{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}`) を書く
5. 完成後に `find . -type f | head -50` と `tree -L 3` で構造を確認する。

---

## 6. 完了確認

以下を確認して報告すること:

1. `tree -L 2` でトップレベル構造が正しいこと
2. `tree configs/` で4軸（model/data/train/stage）+ experiment/ + sweep/ が存在すること
3. `tree src/egosurgery/models/` でH1〜H4対応のサブモジュール（feedback/ relation/ exo/ object_token/ temporal/）が存在すること
4. `experiments/` 配下に6カテゴリのディレクトリだけが存在し、個別実験フォルダは存在しないこと
5. `python -c "from egosurgery.utils.experiment_manager import ExperimentManager"` がエラーなく通ること
6. `python -c "from egosurgery.utils.seed import seed_everything; seed_everything(42)"` がエラーなく通ること
7. `.gitignore` が存在し、data/raw/ と experiments/**/checkpoints/ が除外対象であること
8. `README.md` にプロジェクト説明と設計原則が記載されていること
9. `experiments/README.md` に命名規則と ExperimentManager の使い方が記載されていること

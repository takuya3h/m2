# 実験パイプライン実装プロンプト

あなたは CV 研究プロジェクト `egosurgery_multitask/` の実験パイプラインを実装するコーディングエージェントです。
ディレクトリ構造は構築済みで、`src/egosurgery/` 配下に空の `.py` ファイルと `configs/` 配下に空の `.yaml` ファイルが存在します。

## 目標

**「ダミーの 1 エポック学習を流し、W&B に per-class 指標と Δ 計算枠が自動記録され、`experiments/baselines/s0_001_.../` に証拠一式が自動保存される」** ことを確認できる状態にする。これがフェーズ I の完了判定です。

実際の Mask DINO や DINOv2 のモデル実装は行いません。ダミーモデル・ダミーデータで **パイプラインの骨格** を通すことが目的です。

---

## 0. 前提

- Python 3.10+、PyTorch 2.2+
- ディレクトリ構造は構築済み（`src/egosurgery/` に空ファイルが存在する）
- 実装すべきファイルの一覧は後述。**それ以外のファイルには触らない**。
- W&B はオフラインモード（`WANDB_MODE=offline`）でもテスト可能にする。

---

## 1. 実装するファイルの一覧と依存関係

```
実行順序（依存関係の下流から上流へ）:

src/egosurgery/utils/seed.py              ← 依存なし
src/egosurgery/utils/git_utils.py         ← 依存なし
src/egosurgery/utils/experiment_id.py     ← 依存なし
src/egosurgery/utils/experiment_manager.py ← seed, git_utils, experiment_id に依存
src/egosurgery/utils/logging.py           ← experiment_manager に依存
src/egosurgery/utils/checkpoint.py        ← experiment_manager に依存
src/egosurgery/metrics/delta.py           ← 依存なし
src/egosurgery/engines/trainer.py         ← 上記すべてに依存
src/egosurgery/train.py                   ← エントリーポイント、engines/trainer に依存

configs/default.yaml                      ← Hydra グローバル設定
configs/stage/s0_tool_baseline.yaml       ← S0 のステージ設定

tests/test_pipeline.py                    ← パイプライン統合テスト
```

---

## 2. 各ファイルの実装仕様

### 2.1 `src/egosurgery/utils/seed.py`

```python
"""再現性のための seed 固定ユーティリティ"""

import os
import random
import numpy as np
import torch


def seed_everything(seed: int = 42) -> None:
    """全乱数生成器のシードを固定する"""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
```

### 2.2 `src/egosurgery/utils/git_utils.py`

```python
"""git commit hash を取得・保存するユーティリティ"""

import subprocess
from pathlib import Path


def get_git_commit() -> str:
    """git rev-parse HEAD を実行して返す。git リポジトリでなければ 'NOT_A_GIT_REPO'"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "NOT_A_GIT_REPO"


def save_git_commit(path: Path) -> None:
    """git commit hash をファイルに書き出す"""
    path.write_text(get_git_commit() + "\n")
```

### 2.3 `src/egosurgery/utils/experiment_id.py`

```python
"""
連番付き実験 ID を生成するユーティリティ。

命名規則: {step}_{seq:03d}_{description}_seed{seed}

例:
    generate_experiment_id("experiments/baselines", "s0", "maskdino_bbox", 42)
    → "s0_001_maskdino_bbox_seed42"  (初回)
    → "s0_002_maskdino_bbox_seed42"  (同じ step のフォルダが既にある場合)
"""

from pathlib import Path
import re


def generate_experiment_id(
    base_dir: str | Path,
    step: str,
    description: str,
    seed: int,
) -> str:
    """
    連番付き実験 ID を生成する。

    同じ base_dir 内で同じ step を持つ既存フォルダを走査し、
    次の連番（3桁ゼロ埋め）を自動決定する。
    """
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    # 同じ step のフォルダから最大連番を取得
    pattern = re.compile(rf"^{re.escape(step)}_(\d{{3}})_")
    max_seq = 0
    if base_path.exists():
        for entry in base_path.iterdir():
            if entry.is_dir():
                match = pattern.match(entry.name)
                if match:
                    seq = int(match.group(1))
                    max_seq = max(max_seq, seq)

    next_seq = max_seq + 1
    return f"{step}_{next_seq:03d}_{description}_seed{seed}"
```

### 2.4 `src/egosurgery/utils/experiment_manager.py`

最重要ファイル。以下の仕様を満たすこと。

```python
"""
ExperimentManager: 実験フォルダの自動生成・管理。

使い方:
    manager = ExperimentManager(
        base_dir="experiments",
        category="baselines",
        step="s0",
        description="maskdino_bbox",
        seed=42,
    )
    exp_dir = manager.setup()
    # → experiments/baselines/s0_001_maskdino_bbox_seed42/ が自動作成される

    # config の保存（Hydra の resolved config を渡す）
    manager.save_config(cfg)

    # 学習中の metrics 更新
    manager.log_metrics({"epoch": 1, "mAP": 0.45, "AP_rare": 0.12})

    # per-class AP の保存
    manager.log_per_class_ap({"Tweezers": 0.63, "Skewer": 0.08, ...})
"""
```

実装要件:

1. `__init__` で引数を保存するだけ。ファイルシステムには触らない。
2. `setup() -> Path` で以下を実行:
   - `experiment_id.generate_experiment_id` で ID を生成
   - `{base_dir}/{category}/{experiment_id}/` を作成
   - 以下のサブディレクトリを作成: `logs/`, `checkpoints/`, `predictions/`, `visualizations/`
   - `command.sh` を `sys.argv` の内容で作成
   - `git_commit.txt` を `git_utils.save_git_commit` で作成
   - `metrics.json` を `{}` で初期化
   - `per_class_ap.json` を `{}` で初期化
   - `notes.md` をテンプレートで初期化（日時・step・seed・category を埋め込む）
   - 作成した実験ディレクトリの `Path` を返す
3. `save_config(cfg)` で OmegaConf の DictConfig を YAML 文字列にして `config.yaml` に保存。OmegaConf がなければ dict を yaml.dump する。
4. `log_metrics(metrics: dict)` で `metrics.json` を上書き保存（JSON indent=2）。
5. `log_per_class_ap(ap_dict: dict)` で `per_class_ap.json` を上書き保存。
6. `exp_dir` プロパティで実験ディレクトリのパスを返す（`setup()` 未呼び出し時は `RuntimeError`）。

`notes.md` のテンプレート:

```markdown
# {experiment_id}

作成日時: {ISO 8601 タイムスタンプ}

## 仮説
（ここに記入）

## 実験設定
- Category: {category}
- Step: {step}
- Seed: {seed}
- Config: config.yaml を参照

## 結果
（実験完了後に記入）

## 解釈
（結果の意味、期待との差、原因の仮説）

## 次の行動
1.
```

### 2.5 `src/egosurgery/utils/logging.py`

W&B のラッパー。W&B が使えない環境でもフォールバックする。

```python
"""
W&B + ローカルファイル の二重ロギングユーティリティ。

使い方:
    logger = ExperimentLogger(
        experiment_manager=manager,
        wandb_project="egosurgery_multitask",
        wandb_entity=None,
        tags=["s0", "baseline"],
        enabled=True,  # False なら W&B を使わずローカルのみ
    )
    logger.init()                              # W&B run を開始
    logger.log({"train/loss": 0.5}, step=100)  # W&B + ローカルに記録
    logger.log_metrics({"mAP": 0.45})          # experiment_manager 経由で metrics.json にも保存
    logger.finish()                            # W&B run を終了
"""
```

実装要件:

1. `init()` で `wandb.init(project=..., entity=..., config=..., tags=..., dir=exp_dir, mode="offline" if not enabled else "online")` を呼ぶ。`wandb` が import できなければ `enabled = False` にフォールバック。
2. `log(data: dict, step: int | None = None)` で `wandb.log` とローカルの CSV/JSON に二重記録。
3. `log_metrics(metrics: dict)` で `experiment_manager.log_metrics` を呼ぶ。
4. `finish()` で `wandb.finish()` を呼ぶ。

### 2.6 `src/egosurgery/utils/checkpoint.py`

```python
"""
チェックポイント管理ユーティリティ。

使い方:
    ckpt_manager = CheckpointManager(
        exp_dir=manager.exp_dir,
        save_top_k=3,
        monitor="val/mAP",
        mode="max",
    )
    ckpt_manager.save(model, optimizer, epoch, metrics)
    model, optimizer, start_epoch = ckpt_manager.load_best(model, optimizer)
"""
```

実装要件:

1. `save(model, optimizer, epoch, metrics)` で `checkpoints/epoch_{epoch:04d}.pth` に `torch.save`。`save_top_k` 個を超えたら古いものを削除（ただし `monitor` 指標で上位 k 個は保持）。
2. `save_best(model, optimizer, epoch, metrics)` で `checkpoints/best.pth` に保存。`monitor` 指標が更新された場合のみ。
3. `load_best(model, optimizer) -> (model, optimizer, epoch)` で `best.pth` を読み込む。
4. `load_latest(model, optimizer) -> (model, optimizer, epoch)` で最新の `epoch_*.pth` を読み込む。

### 2.7 `src/egosurgery/metrics/delta.py`

```python
"""
Δ 指標の自動計算ユーティリティ。

研究計画 §7.1 で定義された相互改善幅（Δ）を計算する。

使い方:
    calculator = DeltaCalculator(baselines_dir="experiments/baselines")

    # S0 の基準点（3 seeds の平均±標準偏差）を取得
    baseline = calculator.get_baseline("s0", metric="mAP")
    # → {"mean": 0.458, "std": 0.012, "values": [0.45, 0.46, 0.464]}

    # Δ を計算
    delta = calculator.compute_delta(
        baseline_step="s0",
        experiment_metrics={"mAP": 0.49},
        metric="mAP",
    )
    # → {"delta": 0.032, "baseline_mean": 0.458, "baseline_std": 0.012,
    #    "significant": True}   # |delta| > 1σ なら significant
"""
```

実装要件:

1. `get_baseline(step, metric)` で `baselines_dir` 内の `{step}_*` フォルダの `metrics.json` を全て読み、指定 `metric` の `mean`, `std`, `values` を返す。
2. `compute_delta(baseline_step, experiment_metrics, metric)` で Δ を計算。`significant` は `abs(delta) > baseline_std` で判定（§10.1「Δ が 1σ 以内なら改善と主張しない」）。
3. `compute_all_deltas(experiment_dir, baseline_step)` で `metrics.json` 内の全指標について一括 Δ 計算。

### 2.8 `src/egosurgery/engines/trainer.py`

ダミーモデルで 1 エポック学習を回す汎用トレーナー。**実際のモデル実装は行わない。**

```python
"""
汎用トレーナー。

使い方:
    trainer = Trainer(cfg)
    trainer.setup()     # モデル・データ・optimizer の構築
    trainer.train()     # 学習ループの実行
    trainer.evaluate()  # 評価ループの実行
"""
```

実装要件:

1. `__init__(self, cfg: DictConfig)` で config を受け取る。
2. `setup()` で以下を実行:
   - `seed_everything(cfg.seed)`
   - `ExperimentManager` を作成して `setup()` を呼ぶ
   - `ExperimentLogger` を作成して `init()` を呼ぶ
   - `CheckpointManager` を作成
   - `experiment_manager.save_config(cfg)` で config を保存
   - **ダミーモデル**（`nn.Linear(512, cfg.model.num_classes)` 程度）を作成
   - **ダミーデータセット**（ランダムテンソルを返す `torch.utils.data.Dataset`）を作成
   - optimizer / scheduler を config に従って作成
3. `train()` で以下の学習ループを実行:
   - 各 epoch で train_loader を回し、forward → loss → backward → step
   - 各 epoch 終了時に `evaluate()` を呼ぶ
   - `logger.log({"train/loss": loss_val, "epoch": epoch}, step=global_step)`
   - `checkpoint_manager.save(...)` を呼ぶ
   - 最終 epoch 後に `logger.log_metrics(final_metrics)` を呼ぶ
   - `logger.finish()` を呼ぶ
4. `evaluate()` で以下を実行:
   - val_loader を回して loss / accuracy を計算
   - **ダミーの per-class AP を生成**（15 クラスのランダム値。クラス名は以下を使用）:
     ```python
     TOOL_CLASSES = [
         "Tweezers", "Needle_Holders", "Scissors", "Forceps",
         "Bipolar_Forceps", "Retractors", "Clip_Applier", "Suction",
         "Scalpel", "Electrocautery", "Gauze", "Needle", "Thread",
         "Skewer", "Syringe"
     ]
     ```
   - per-class AP を `experiment_manager.log_per_class_ap(...)` に保存
   - **ダミーの confusion matrix**（4×4 形状類似ペア: Forceps / Tweezers / Needle_Holders / Bipolar_Forceps）を `numpy.save` で `visualizations/confusion_matrix.npy` に保存
   - 評価指標を dict で返す

### 2.9 `src/egosurgery/train.py`

Hydra エントリーポイント。

```python
"""
学習のエントリーポイント。

使い方:
    python -m egosurgery.train stage=s0_tool_baseline seed=42
    python -m egosurgery.train stage=s0_tool_baseline seed=42 logging.wandb_project=test
"""

import hydra
from omegaconf import DictConfig

from egosurgery.engines.trainer import Trainer


@hydra.main(version_base=None, config_path="../../configs", config_name="default")
def main(cfg: DictConfig) -> None:
    trainer = Trainer(cfg)
    trainer.setup()
    trainer.train()


if __name__ == "__main__":
    main()
```

**注意**: Hydra の `config_path` は `train.py` から `configs/` への相対パスにする。`src/egosurgery/train.py` → `../../configs`。

### 2.10 `configs/default.yaml`

以下の内容で作成（上書き）する。Hydra の defaults リストを含む。

```yaml
defaults:
  - _self_
  - stage: s0_tool_baseline   # デフォルトステージ

seed: 42
deterministic: true
cudnn_benchmark: false

# === Phase Configuration ===
phase:
  current: "phase0"
  mask_available: false

# === Model (ダミー、実際の model/ config で上書きされる) ===
model:
  num_classes: 15
  input_dim: 512

# === Feedback Control ===
feedback:
  phase_to_det: false
  det_to_phase: false
  injection_method: "cross_attention"
  entropy_gating: true
  stop_gradient: true

# === Relation Module ===
relation:
  enabled: false

# === Exo ===
exo:
  enabled: false

# === Loss Weights ===
loss:
  lambda_det: 1.0
  lambda_mask: 0.0
  lambda_rel: 0.0
  lambda_phase: 1.0
  lambda_temp_smooth: 0.1
  lambda_ssl: 0.0
  lambda_distill: 0.0
  lambda_view_consist: 0.0
  balancer: "famo"

# === Training ===
train:
  epochs: 100
  amp: true
  gradient_checkpoint: true
  batch_size: 4
  num_workers: 4
  accumulate_grad_batches: 1

# === Optimizer ===
optimizer:
  name: "adamw"
  lr: 0.0001
  weight_decay: 0.05

# === Scheduler ===
scheduler:
  name: "cosine"
  warmup_epochs: 5

# === Experiment ===
experiment:
  base_dir: "experiments"
  category: "baselines"
  step: "s0"
  description: "default"

# === Logging ===
logging:
  wandb_project: "egosurgery_multitask"
  wandb_entity: null
  wandb_enabled: false    # テスト時は false、本番で true に
  log_every_n_steps: 50
  save_top_k: 3

# === Evaluation ===
eval:
  num_seeds: 3
  bootstrap_n: 1000
  delta_significance_threshold: 1.0
```

### 2.11 `configs/stage/s0_tool_baseline.yaml`

```yaml
# S0: 術具検出ベースライン — §2.5(a) 基準点
# このステージでは術具の bbox 検出のみ。Phase head なし。

experiment:
  category: "baselines"
  step: "s0"
  description: "tool_baseline"

model:
  num_classes: 15
  input_dim: 512

train:
  epochs: 2      # テスト用。本番では 100 に変更
  batch_size: 4

feedback:
  phase_to_det: false
  det_to_phase: false

relation:
  enabled: false

exo:
  enabled: false
```

---

## 3. テスト

### 3.1 `tests/test_pipeline.py`

パイプライン全体の統合テスト。以下をテストする。

```python
"""
パイプライン統合テスト。

以下を検証する:
1. ExperimentManager が正しい構造のフォルダを作成する
2. 連番が正しく採番される（同じ step で 2 回呼ぶと 001, 002）
3. config.yaml / command.sh / git_commit.txt / metrics.json / notes.md が作成される
4. Trainer がダミーデータで 1 エポック完走する
5. 完走後に metrics.json に値が入っている
6. per_class_ap.json に 15 クラスの AP が入っている
7. DeltaCalculator が基準点からΔを計算できる

実行方法:
    pytest tests/test_pipeline.py -v
"""
```

テストケース:

1. `test_experiment_manager_creates_structure`:
   - `ExperimentManager` で `setup()` を呼ぶ
   - `config.yaml`, `command.sh`, `git_commit.txt`, `metrics.json`, `per_class_ap.json`, `notes.md` が存在することを assert
   - `logs/`, `checkpoints/`, `predictions/`, `visualizations/` が存在することを assert

2. `test_experiment_id_sequential`:
   - 同じ `base_dir`, `step` で `generate_experiment_id` を 3 回呼ぶ
   - 1 回目が `_001_`、2 回目が `_002_`、3 回目が `_003_` であることを assert
   - ただし、2 回目以降はディレクトリを実際に作成してから呼ぶ必要がある

3. `test_trainer_dummy_epoch`:
   - `OmegaConf.create(...)` でダミー config を作る（Hydra 不要）
   - `Trainer(cfg)` で 1 エポックを回す
   - `experiments/` にフォルダが作成されていることを assert
   - `metrics.json` が空でないことを assert

4. `test_delta_calculator`:
   - `experiments/baselines/` に手動で `s0_001_.../metrics.json`, `s0_002_.../metrics.json`, `s0_003_.../metrics.json` を作成（`{"mAP": 0.45}`, `{"mAP": 0.46}`, `{"mAP": 0.47}` など）
   - `DeltaCalculator` で `get_baseline("s0", "mAP")` を呼ぶ
   - `mean`, `std` が正しいことを assert
   - `compute_delta("s0", {"mAP": 0.50}, "mAP")` で `delta` が正しいことを assert

5. `test_seed_determinism`:
   - `seed_everything(42)` を 2 回呼び、`torch.randn(10)` の結果が一致することを assert

テスト内で `tmp_path` フィクスチャを使って一時ディレクトリにフォルダを作ること。

---

## 4. 作業手順

1. まず `src/egosurgery/utils/` のユーティリティ群を実装する（seed → git_utils → experiment_id → experiment_manager → logging → checkpoint の順）。
2. 次に `src/egosurgery/metrics/delta.py` を実装する。
3. `src/egosurgery/engines/trainer.py` を実装する（ダミーモデル・ダミーデータ）。
4. `src/egosurgery/train.py` を実装する。
5. `configs/default.yaml` と `configs/stage/s0_tool_baseline.yaml` を作成する。
6. `tests/test_pipeline.py` を実装する。
7. テストを実行して全パスを確認:
   ```bash
   cd egosurgery_multitask
   pip install -e . 2>/dev/null || true
   PYTHONPATH=src pytest tests/test_pipeline.py -v
   ```
8. 統合テストとして以下を実行:
   ```bash
   cd egosurgery_multitask
   PYTHONPATH=src python -m egosurgery.train \
       stage=s0_tool_baseline \
       seed=42 \
       train.epochs=2 \
       logging.wandb_enabled=false
   ```
   → `experiments/baselines/s0_001_tool_baseline_seed42/` が作成されていることを確認。

---

## 5. 実装しないファイル（明示的なスコープ外）

以下は本プロンプトのスコープ外。空ファイルのまま触らないこと。

- `src/egosurgery/models/` 配下の全ファイル（Mask DINO, DINOv2, TeCNO 等の実際のモデル実装）
- `src/egosurgery/datasets/` 配下の全ファイル（EgoSurgery データセットクラス）
- `src/egosurgery/engines/stage_*_trainer.py`（Stage A〜D の専用トレーナー）
- `src/egosurgery/metrics/` の delta.py 以外のファイル
- `src/egosurgery/analysis/` 配下の全ファイル
- `scripts/` 配下の全ファイル（run_s0.sh 等）
- `configs/model/` 配下の全 YAML
- `configs/data/` 配下の全 YAML
- `configs/train/` 配下の全 YAML
- `configs/experiment/` 配下の全 YAML

---

## 6. 完了確認

以下をすべて確認して報告すること。

1. `pytest tests/test_pipeline.py -v` が全テストパスする
2. `python -m egosurgery.train stage=s0_tool_baseline seed=42 train.epochs=2 logging.wandb_enabled=false` が正常終了する
3. `experiments/baselines/s0_001_tool_baseline_seed42/` が作成され、以下が存在する:
   - `config.yaml`（中身が空でない）
   - `command.sh`（中身が空でない）
   - `git_commit.txt`（中身が空でない）
   - `metrics.json`（中身が `{}` でなく、学習結果が入っている）
   - `per_class_ap.json`（15 クラスの AP が入っている）
   - `notes.md`（テンプレートが入っている）
   - `logs/`, `checkpoints/`, `predictions/`, `visualizations/` ディレクトリ
4. 同じコマンドをもう一度実行すると `s0_002_tool_baseline_seed42/` が作成される（連番が増える）
5. `from egosurgery.metrics.delta import DeltaCalculator` がエラーなく通り、上記 2 実験の metrics.json からΔが計算できる

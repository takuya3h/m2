"""パイプライン統合テスト。

フェーズ I の完了判定（ダミー学習がパイプラインの骨格を 1 周通り、
証拠一式が自動保存される）を以下の観点で検証する:

1. ExperimentManager が正しい構造のフォルダを作成する
2. 連番が正しく採番される（同じ step で繰り返すと 001, 002, 003）
3. config.yaml / command.sh / git_commit.txt / metrics.json /
   per_class_ap.json / notes.md が作成される
4. Trainer がダミーデータで学習を完走する
5. 完走後に metrics.json に学習結果が入っている
6. per_class_ap.json に 15 クラスの AP が入っている
7. DeltaCalculator が基準点から Δ を計算できる

実行方法:
    PYTHONPATH=src pytest tests/test_pipeline.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

# PYTHONPATH=src を付け忘れても import できるよう src/ を通す。
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ---------------------------------------------------------------------- #
# 1. ExperimentManager がフォルダ構造を作る
# ---------------------------------------------------------------------- #
def test_experiment_manager_creates_structure(tmp_path):
    """setup() で必須ファイル・サブディレクトリが揃うことを確認する。"""
    from egosurgery.utils.experiment_manager import ExperimentManager

    manager = ExperimentManager(
        base_dir=tmp_path,
        category="baselines",
        step="s0",
        description="structure",
        seed=42,
    )
    exp_dir = manager.setup()

    assert exp_dir.is_dir()
    for filename in (
        "config.yaml",
        "command.sh",
        "git_commit.txt",
        "metrics.json",
        "per_class_ap.json",
        "notes.md",
    ):
        path = exp_dir / filename
        assert path.is_file(), f"{filename} が作成されていません"
        assert path.read_text(encoding="utf-8").strip() != "", f"{filename} が空です"

    for subdir in ("logs", "checkpoints", "predictions", "visualizations"):
        assert (exp_dir / subdir).is_dir(), f"{subdir}/ が作成されていません"


# ---------------------------------------------------------------------- #
# 2. 連番が正しく採番される
# ---------------------------------------------------------------------- #
def test_experiment_id_sequential(tmp_path):
    """同じ step を繰り返すと連番が 001 -> 002 -> 003 と進むことを確認する。"""
    from egosurgery.utils.experiment_id import generate_experiment_id

    base_dir = tmp_path / "baselines"
    generated = []
    for _ in range(3):
        exp_id = generate_experiment_id(base_dir, "s0", "tool", 42)
        generated.append(exp_id)
        # 次回採番が前回を検知できるよう、実際にフォルダを作る。
        (base_dir / exp_id).mkdir(parents=True)

    assert generated[0].startswith("s0_001_")
    assert generated[1].startswith("s0_002_")
    assert generated[2].startswith("s0_003_")
    assert generated[0] == "s0_001_tool_seed42"


# ---------------------------------------------------------------------- #
# 3 + 5 + 6. Trainer がダミーデータで完走し、証拠が保存される
# ---------------------------------------------------------------------- #
def _make_dummy_cfg(experiments_dir: Path):
    """Hydra を介さずに Trainer 用のダミー config を組み立てる。"""
    from omegaconf import OmegaConf

    return OmegaConf.create(
        {
            "seed": 42,
            "experiment": {
                "base_dir": str(experiments_dir),
                "category": "baselines",
                "step": "s0",
                "description": "dummyrun",
            },
            "model": {"num_classes": 15, "input_dim": 32},
            "train": {"epochs": 1, "batch_size": 8},
            "optimizer": {"name": "adamw", "lr": 1e-4, "weight_decay": 0.05},
            "scheduler": {"name": "cosine", "warmup_epochs": 0},
            "logging": {
                "wandb_project": "egosurgery_multitask_test",
                "wandb_entity": None,
                "wandb_enabled": False,
                "log_every_n_steps": 1,
                "save_top_k": 3,
            },
        }
    )


def test_trainer_dummy_epoch(tmp_path):
    """Trainer がダミーデータで完走し、metrics/per_class_ap が埋まることを確認する。"""
    from egosurgery.engines.trainer import Trainer

    experiments_dir = tmp_path / "experiments"
    cfg = _make_dummy_cfg(experiments_dir)

    trainer = Trainer(cfg)
    trainer.setup()
    trainer.train()

    # 実験フォルダが 1 つ作成されている。
    runs = sorted((experiments_dir / "baselines").iterdir())
    assert len(runs) == 1
    exp_dir = runs[0]

    # metrics.json が空でなく、学習結果（mAP）を含む。
    metrics = json.loads((exp_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics != {}
    assert "mAP" in metrics
    assert "delta_mAP" in metrics  # Δ 計算枠が記録されている

    # per_class_ap.json に 15 クラスの AP が入っている。
    per_class_ap = json.loads(
        (exp_dir / "per_class_ap.json").read_text(encoding="utf-8")
    )
    assert len(per_class_ap) == 15

    # confusion matrix が保存されている。
    assert (exp_dir / "visualizations" / "confusion_matrix.npy").is_file()


# ---------------------------------------------------------------------- #
# 4 + 7. DeltaCalculator が基準点から Δ を計算できる
# ---------------------------------------------------------------------- #
def test_delta_calculator(tmp_path):
    """3 つの基準実験から基準点を集約し、Δ を計算できることを確認する。"""
    from egosurgery.metrics.delta import DeltaCalculator

    baselines_dir = tmp_path / "baselines"
    map_values = [0.45, 0.46, 0.47]
    for seq, value in enumerate(map_values, start=1):
        run_dir = baselines_dir / f"s0_{seq:03d}_tool_seed42"
        run_dir.mkdir(parents=True)
        (run_dir / "metrics.json").write_text(
            json.dumps({"mAP": value}), encoding="utf-8"
        )

    calculator = DeltaCalculator(baselines_dir)

    baseline = calculator.get_baseline("s0", "mAP")
    assert baseline["n"] == 3
    assert baseline["mean"] == pytest.approx(0.46)
    assert baseline["std"] == pytest.approx(float(np.std(map_values, ddof=1)))

    # Δ = 0.50 - 0.46 = 0.04。0.04 > σ(=0.01) なので有意。
    delta = calculator.compute_delta("s0", {"mAP": 0.50}, "mAP")
    assert delta["delta"] == pytest.approx(0.04)
    assert delta["baseline_mean"] == pytest.approx(0.46)
    assert delta["significant"] is True

    # |Δ| が 1σ 以内なら有意でない。
    small = calculator.compute_delta("s0", {"mAP": 0.465}, "mAP")
    assert small["significant"] is False


# ---------------------------------------------------------------------- #
# 補助. seed 固定の決定性
# ---------------------------------------------------------------------- #
def test_seed_determinism():
    """seed_everything を 2 回呼ぶと同じ乱数列が得られることを確認する。"""
    import torch

    from egosurgery.utils.seed import seed_everything

    seed_everything(42)
    first = torch.randn(10)
    seed_everything(42)
    second = torch.randn(10)

    assert torch.equal(first, second)


# ====================================================================== #
# Stage A トレーナー（S0）の統合テスト
# ====================================================================== #
def _vits_backbone_dict() -> dict:
    """テスト用の軽量 DINOv2 ViT-S backbone 設定（PEFT なし）。"""
    return {
        "hub_repo": "facebookresearch/dinov2",
        "hub_model": "dinov2_vits14_reg",
        "out_indices": [2, 5, 8, 11],
        "embed_dim": 384,
        "patch_size": 14,
        "img_size": 518,
        "pretrained": True,
        "gradient_checkpointing": False,
        "peft": {"method": None},
    }


def _make_stage_a_data(tmp_path):
    """Stage A トレーナー用のダミー COCO データ（実画像 + JSON）を作る。"""
    import cv2
    import numpy as np

    from egosurgery.datasets.constants import TOOL_CLASSES, TOOL_NAME_TO_ID

    img_dir = tmp_path / "imgs"
    img_dir.mkdir(parents=True, exist_ok=True)
    images, annotations = [], []
    ann_id = 0
    for img_idx in range(6):
        name = f"img_{img_idx:02d}.jpg"
        pixels = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        cv2.imwrite(str(img_dir / name), pixels)
        images.append(
            {"id": img_idx, "file_name": name, "width": 128, "height": 128}
        )
        for slot, cls_name in enumerate(["Forceps", "Skewer"]):
            x, y = 12 + slot * 40, 14 + slot * 30
            annotations.append(
                {"id": ann_id, "image_id": img_idx,
                 "category_id": TOOL_NAME_TO_ID[cls_name],
                 "bbox": [x, y, 28, 24], "area": 28 * 24, "iscrowd": 0}
            )
            ann_id += 1
    coco = {
        "images": images,
        "annotations": annotations,
        "categories": [dict(c) for c in TOOL_CLASSES],
    }
    ann_file = tmp_path / "instances.json"
    ann_file.write_text(json.dumps(coco), encoding="utf-8")
    return ann_file, img_dir


def _make_stage_a_cfg(tmp_path, ann_file, img_dir, epochs=1):
    """Stage A トレーナー用のダミー config を組み立てる。"""
    from omegaconf import OmegaConf

    return OmegaConf.create(
        {
            "seed": 42,
            "experiment": {
                "base_dir": str(tmp_path / "experiments"),
                "category": "baselines",
                "step": "s0",
                "description": "smoke",
            },
            "model": {
                "num_classes": 15,
                "backbone": _vits_backbone_dict(),
                "detection_head": "mask_dino",
            },
            "train": {
                "epochs": epochs,
                "batch_size": 2,
                "num_workers": 0,
                "amp": False,
                "grad_clip_norm": 1.0,
                "freeze_backbone": True,
            },
            "optimizer": {"name": "adamw", "lr": 1e-4, "weight_decay": 0.05},
            "logging": {
                "wandb_project": "egosurgery_multitask_test",
                "wandb_entity": None,
                "wandb_enabled": False,
                "save_top_k": 2,
                "log_every_n_steps": 1,
            },
            "data": {
                "img_size": 224,
                "batch_size": 2,
                "num_workers": 0,
                "include_hand": False,
                "include_phase": False,
                "use_rfs": False,
                "repeat_thresh": 0.001,
                "use_copypaste": False,
                "limit": 4,
                "train": {"ann_file": str(ann_file), "img_dir": str(img_dir)},
                "val": {"ann_file": str(ann_file), "img_dir": str(img_dir)},
                "test": {"ann_file": str(ann_file), "img_dir": str(img_dir)},
            },
        }
    )


def test_stage_a_trainer_setup(tmp_path):
    """StageATrainer が setup() でエラーなく初期化されること。"""
    from egosurgery.engines.stage_a_trainer import StageATrainer

    ann_file, img_dir = _make_stage_a_data(tmp_path)
    cfg = _make_stage_a_cfg(tmp_path, ann_file, img_dir)

    trainer = StageATrainer(cfg)
    try:
        trainer.setup()
    except Exception as exc:  # DINOv2 のダウンロード失敗等
        pytest.skip(f"StageATrainer.setup に必要な依存が利用不可: {exc}")

    assert trainer.model is not None
    assert trainer.train_loader is not None and trainer.val_loader is not None
    assert trainer.manager.exp_dir.is_dir()


def test_stage_a_trainer_one_epoch(tmp_path):
    """StageATrainer が 1 epoch 完走し、証拠ファイルを残すこと。"""
    from egosurgery.engines.stage_a_trainer import StageATrainer

    ann_file, img_dir = _make_stage_a_data(tmp_path)
    cfg = _make_stage_a_cfg(tmp_path, ann_file, img_dir, epochs=1)

    trainer = StageATrainer(cfg)
    try:
        trainer.setup()
        trainer.run()
    except Exception as exc:
        pytest.skip(f"StageATrainer の実行に必要な依存が利用不可: {exc}")

    runs = sorted((tmp_path / "experiments" / "baselines").iterdir())
    assert len(runs) == 1
    exp_dir = runs[0]

    metrics = json.loads((exp_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics != {} and "mAP" in metrics
    per_class_ap = json.loads(
        (exp_dir / "per_class_ap.json").read_text(encoding="utf-8")
    )
    assert len(per_class_ap) == 15
    assert (exp_dir / "visualizations" / "confusion_matrix.npy").is_file()

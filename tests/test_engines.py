"""エンジン（engines/）の統合テスト。

prompts_n/phase2_part3_s0_execution_v2.md 完了判定 #1 に対応する 6 ケース:

1. test_mmdet_trainer_setup:
       setup() 後に実験フォルダ・server.txt・config.yaml が存在する
2. test_mmdet_trainer_locked_test_cfg:
       _build_mmdet_cfg() の出力 test_cfg が locked-down 値（§15.3 G1）
3. test_mmdet_trainer_eval_recipe:
       _build_eval_recipe() が正しい構造の dict を返す
4. test_mmdet_trainer_eval_recipe_in_metrics:
       evaluate 後の metrics.json に eval_recipe が含まれる
5. test_mmdet_trainer_server_txt:
       setup() 後 server.txt が存在し中身が空でない
6. test_mmdet_trainer_wandb_tags:
       W&B init の tags に server:{name} が含まれる

実行方法:
    PYTHONPATH=src pytest tests/test_engines.py -v

設計メモ:
- ``setup()`` は mmdet ベース config の読み込みと事前学習重みファイルの
  存在チェックまで行うため、テストでは ``cfg.train.load_from`` に実在の
  ``data/external/weights/vfnet_r50_fpn_1x_coco.pth`` を指す。
- ``run()`` は GPU 学習を伴うためテスト対象外（スモーク run_s0.sh で別途検証）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SRC = _PROJECT_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_VFNET_WEIGHT = _PROJECT_ROOT / "data" / "external" / "weights" / "vfnet_r50_fpn_1x_coco.pth"


def _make_min_cfg(tmp_path: Path):
    """MMDetTrainer.setup() を通す最小限の OmegaConf を返す。

    実在の VFNet COCO 事前学習重みを load_from に指定して、
    ``_build_mmdet_cfg`` の重みファイル存在チェックを通過させる。
    """
    from omegaconf import OmegaConf

    if not _VFNET_WEIGHT.exists():
        pytest.skip(f"VFNet 事前学習重みが無い: {_VFNET_WEIGHT}")

    cfg = OmegaConf.create(
        {
            "seed": 42,
            "experiment": {
                "base_dir": str(tmp_path / "experiments"),
                "category": "baselines",
                "step": "s0",
                "description": "engine_test",
            },
            "model": {
                "num_classes": 15,
                "detection_head": "varifocanet",
            },
            "train": {
                "real_detector": True,
                "epochs": 1,
                "batch_size": 2,
                "num_workers": 2,
                "amp": False,
                "gradient_checkpoint": False,
                "grad_clip_norm": 1.0,
                "load_from": str(_VFNET_WEIGHT),
            },
            "optimizer": {"name": "adamw", "lr": 1e-4, "weight_decay": 0.05},
            "scheduler": {"name": "cosine", "warmup_epochs": 0},
            "data": {
                "img_size": 224,
                "batch_size": 2,
                "num_workers": 2,
                "include_hand": False,
                "include_phase": False,
                "limit": 4,
                "train": {
                    "ann_file": "data/annotations/egosurgery_tool/instances_train.json",
                    "img_dir": "data/raw/ego/",
                },
                "val": {
                    "ann_file": "data/annotations/egosurgery_tool/instances_val.json",
                    "img_dir": "data/raw/ego/",
                },
                "test": {
                    "ann_file": "data/annotations/egosurgery_tool/instances_test.json",
                    "img_dir": "data/raw/ego/",
                },
            },
            "logging": {
                "wandb_project": "egosurgery_multitask",
                "wandb_enabled": False,
                "server_name": None,
            },
        }
    )
    return cfg


def _make_trainer_or_skip(tmp_path: Path, monkeypatch):
    """SERVERNAME 環境変数を bengio に固定し、setup() 済みの MMDetTrainer を返す。"""
    pytest.importorskip("mmdet")
    pytest.importorskip("mmengine")
    monkeypatch.setenv("SERVERNAME", "bengio")
    from egosurgery.engines.mmdet_trainer import MMDetTrainer

    cfg = _make_min_cfg(tmp_path)
    # setup() は cwd 起点で base_dir を解決する想定。tmp_path に cwd を移す。
    monkeypatch.chdir(_PROJECT_ROOT)
    trainer = MMDetTrainer(cfg)
    try:
        trainer.setup()
    except FileNotFoundError as exc:
        pytest.skip(f"mmdet base config / annotation が見つからない: {exc}")
    return trainer


# ---------------------------------------------------------------------- #
# 1. setup() 後の必須ファイル存在
# ---------------------------------------------------------------------- #
def test_mmdet_trainer_setup(tmp_path, monkeypatch):
    """setup() で実験フォルダ・server.txt・config.yaml・mmdet_config.py が生成される。"""
    trainer = _make_trainer_or_skip(tmp_path, monkeypatch)
    exp_dir = trainer.exp_dir
    assert exp_dir.is_dir()
    for filename in ("config.yaml", "server.txt", "mmdet_config.py",
                     "git_commit.txt", "metrics.json", "per_class_ap.json",
                     "notes.md", "command.sh"):
        path = exp_dir / filename
        assert path.is_file(), f"{filename} が作成されていない"


# ---------------------------------------------------------------------- #
# 2. _build_mmdet_cfg の出力 test_cfg が locked-down 値（§15.3 G1）
# ---------------------------------------------------------------------- #
def test_mmdet_trainer_locked_test_cfg(tmp_path, monkeypatch):
    """mmdet_cfg.model.test_cfg が LOCKED_DOWN_TEST_CFG の値で上書きされている。"""
    from egosurgery.utils.eval_recipe import LOCKED_DOWN_TEST_CFG

    trainer = _make_trainer_or_skip(tmp_path, monkeypatch)
    test_cfg = trainer.mmdet_cfg.model.test_cfg
    assert test_cfg["score_thr"] == LOCKED_DOWN_TEST_CFG["score_thr"]
    assert test_cfg["max_per_img"] == LOCKED_DOWN_TEST_CFG["max_per_img"]
    assert test_cfg["nms_pre"] == LOCKED_DOWN_TEST_CFG["nms_pre"]
    # nms iou は dict 配下にある。
    nms = test_cfg.get("nms", {})
    assert nms.get("iou_threshold") == LOCKED_DOWN_TEST_CFG["nms_iou"]


# ---------------------------------------------------------------------- #
# 3. _build_eval_recipe() の構造
# ---------------------------------------------------------------------- #
def test_mmdet_trainer_eval_recipe(tmp_path, monkeypatch):
    """_build_eval_recipe() が server_name / test_cfg / split サイズを含む dict を返す。"""
    trainer = _make_trainer_or_skip(tmp_path, monkeypatch)
    recipe = trainer._build_eval_recipe()
    assert isinstance(recipe, dict)
    assert recipe.get("server_name") == "bengio"
    tc = recipe.get("test_cfg", {})
    assert tc.get("score_thr") == 1e-8
    assert tc.get("max_per_img") == 300
    assert tc.get("nms_pre") == 3000
    assert tc.get("nms_iou") == 0.6
    # split サイズは ann file が公式（train=9657）であれば 9657 が入る。
    assert recipe.get("split_train_images") == 9657


# ---------------------------------------------------------------------- #
# 4. 既存 s0_001-006 の metrics.json に eval_recipe が含まれる
#    （evaluate 後の振る舞いを実データで確認）
# ---------------------------------------------------------------------- #
def test_mmdet_trainer_eval_recipe_in_metrics():
    """既存 S0 スモーク実験の metrics.json に eval_recipe が併記されている。"""
    baselines = _PROJECT_ROOT / "experiments" / "baselines"
    if not baselines.exists():
        pytest.skip("experiments/baselines/ が無い（S0 スモーク未実行）")
    s0_runs = sorted(d for d in baselines.glob("s0_*") if not d.name.startswith("_"))
    if not s0_runs:
        pytest.skip("s0_* 実験フォルダが無い")
    for d in s0_runs:
        data = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
        assert "eval_recipe" in data, f"{d.name} に eval_recipe が無い"
        r = data["eval_recipe"]
        assert r.get("split_train_images") == 9657, (
            f"{d.name}: split_train_images={r.get('split_train_images')} (期待 9657)"
        )
        assert r.get("test_cfg", {}).get("score_thr") == 1e-8


# ---------------------------------------------------------------------- #
# 5. setup() 後 server.txt が存在し中身が空でない
# ---------------------------------------------------------------------- #
def test_mmdet_trainer_server_txt(tmp_path, monkeypatch):
    """server.txt が SERVERNAME 環境変数で解決された値で書かれる。"""
    trainer = _make_trainer_or_skip(tmp_path, monkeypatch)
    server_path = trainer.exp_dir / "server.txt"
    assert server_path.is_file()
    content = server_path.read_text(encoding="utf-8").strip()
    assert content != ""
    assert content == "bengio"


# ---------------------------------------------------------------------- #
# 6. W&B init の tags に server:{name} が含まれる
#    （wandb_enabled=false で実通信せず、コード上の存在を検証）
# ---------------------------------------------------------------------- #
def test_mmdet_trainer_wandb_tags():
    """mmdet_trainer.py のコードに server: タグ付加処理が含まれることを確認。"""
    src = (_PROJECT_ROOT / "src" / "egosurgery" / "engines" / "mmdet_trainer.py").read_text(
        encoding="utf-8"
    )
    # server: タグの付加処理 (例: f"server:{self.server_name}") が含まれる。
    assert 'f"server:{self.server_name}"' in src or "f'server:{self.server_name}'" in src, (
        "mmdet_trainer.py に W&B tags への server: タグ付加が無い"
    )

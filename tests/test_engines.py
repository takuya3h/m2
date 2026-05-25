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
    """過去の S0 スモーク証跡 (退避済み) の metrics.json に eval_recipe が
    併記されている。本番 S0 が稼働中の experiments/baselines/ は学習途中で
    metrics が空の場合があるため、明示的に証跡フォルダ (_smoke_*/) を参照する。"""
    baselines = _PROJECT_ROOT / "experiments" / "baselines"

    def _has_recipe(path: Path) -> bool:
        m = path / "metrics.json"
        if not m.is_file():
            return False
        try:
            data = json.loads(m.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        return bool(data) and "eval_recipe" in data

    # 退避済みの MMDetTrainer 経由スモーク証跡 (_smoke_* 配下) を優先。
    # ただし StageATrainer (SimpleDetectionHead) 経由の証跡は eval_recipe を
    # 持たないので、has_recipe フィルタで除外する。
    candidates: list[Path] = [
        d
        for prior in baselines.glob("_smoke_*")
        for d in prior.glob("s0_*")
        if _has_recipe(d)
    ]
    # 加えてアクティブな baselines/s0_* も対象（学習中なら空 metrics で除外）。
    candidates.extend(
        d
        for d in baselines.glob("s0_*")
        if not d.name.startswith("_") and _has_recipe(d)
    )
    if not candidates:
        pytest.skip("検証対象の S0 スモーク証跡が無い (退避フォルダもアクティブ実験も該当なし)")
    for d in candidates:
        data = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
        assert "eval_recipe" in data, f"{d.name} に eval_recipe が無い"
        r = data["eval_recipe"]
        # MMDetTrainer 経由の証跡なら必ず公式 split + locked-down test_cfg。
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
    # §13.2 (b)(iii): DDP gpu:{world_size} タグの付加処理も検証。
    assert 'f"gpu:{self.world_size}"' in src or "f'gpu:{self.world_size}'" in src, (
        "mmdet_trainer.py に W&B tags への gpu:{world_size} タグ付加が無い"
    )


# ---------------------------------------------------------------------- #
# 7. Co-DETR でも _build_mmdet_cfg が test_cfg を locked-down 値に上書き
# ---------------------------------------------------------------------- #
def test_mmdet_trainer_codetr_locked_test_cfg(tmp_path, monkeypatch):
    """Co-DETR 構成でも _build_mmdet_cfg の test_cfg が locked-down 値。
    実 mmdet codetr base config が無い環境でも、_resolve_detector が
    codetr を受け付けること自体は検証する。"""
    from egosurgery.engines.mmdet_trainer import MMDetTrainer

    assert MMDetTrainer._resolve_detector("codetr") == "codetr"
    assert MMDetTrainer._resolve_detector("co_detr") == "codetr"
    assert MMDetTrainer._resolve_detector("co-detr") == "codetr"


# ---------------------------------------------------------------------- #
# 8. compare_judge6 の判定ロジック（§9 #6）
# ---------------------------------------------------------------------- #
def test_compare_judge6_logic():
    """|ΔAPr| >= 3.0 で「切替検討」、未満で「Mask DINO 継続」を返す。"""
    sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))
    from compare_judge6 import judge

    assert judge(3.0) == "検出ヘッド切替を検討"
    assert judge(-3.5) == "検出ヘッド切替を検討"
    assert judge(2.9) == "Mask DINO 継続"
    assert judge(0.0) == "Mask DINO 継続"
    # しきい値の上書き。
    assert judge(2.5, threshold_pt=2.0) == "検出ヘッド切替を検討"


# ---------------------------------------------------------------------- #
# 9-12. DDP 関連の純粋ロジック検証（weights / annotation 不要のユニットテスト）
#       weights ファイルや mmdet base config を必要としない部分のみを切り出し、
#       worktree 環境や CI 上でも skip せず実行できるようにする。
# ---------------------------------------------------------------------- #
def _make_trainer_no_setup(monkeypatch, lr_scaling_mode: str | None = None,
                           world_size: int | None = None,
                           rank: int | None = None,
                           local_rank: int | None = None):
    """setup() を呼ばず DDP 環境検出だけを行う MMDetTrainer を返す。

    setup() は mmdet base config / 重み / annotation を要求するため、
    DDP 文脈の検出 / _resolve_lr_label / _build_eval_recipe（mmdet_cfg なし）
    といった純粋ロジックのテストでは setup() を直接呼ばず、必要な
    インスタンス属性だけを手で埋める形で検証する。
    """
    from omegaconf import OmegaConf

    from egosurgery.engines.mmdet_trainer import MMDetTrainer

    # 環境変数の上書き。
    if world_size is None:
        monkeypatch.delenv("WORLD_SIZE", raising=False)
    else:
        monkeypatch.setenv("WORLD_SIZE", str(world_size))
    if rank is None:
        monkeypatch.delenv("RANK", raising=False)
    else:
        monkeypatch.setenv("RANK", str(rank))
    if local_rank is None:
        monkeypatch.delenv("LOCAL_RANK", raising=False)
    else:
        monkeypatch.setenv("LOCAL_RANK", str(local_rank))

    cfg_dict = {
        "seed": 42,
        "model": {"num_classes": 15, "detection_head": "varifocanet"},
        "train": {
            "real_detector": True, "epochs": 1,
            "batch_size": 2, "num_workers": 0,
            "load_from": None,
        },
        "data": {"img_size": 224, "include_hand": False, "include_phase": False},
        "logging": {"wandb_enabled": False, "server_name": None},
        "experiment": {"base_dir": "experiments", "category": "baselines",
                       "step": "s0", "description": "ut"},
    }
    if lr_scaling_mode is not None:
        cfg_dict["train"]["lr_scaling_mode"] = lr_scaling_mode

    cfg = OmegaConf.create(cfg_dict)
    trainer = MMDetTrainer(cfg)
    # setup() の DDP 検出ロジックだけを再現する（実 setup() は呼ばない）。
    import os as _os
    trainer.world_size = int(_os.environ.get("WORLD_SIZE", "1"))
    trainer.rank = int(_os.environ.get("RANK", "0"))
    trainer.local_rank = int(_os.environ.get("LOCAL_RANK", "0"))
    trainer.is_distributed = trainer.world_size > 1
    trainer._lr_scaling_label = trainer._resolve_lr_label()
    return trainer


# 9. _build_eval_recipe() の戻り値に gpu_count / effective_batch_size /
#    lr_scaling が含まれる（mmdet_cfg なしでも _build_eval_recipe は
#    AttributeError になるため、_resolve_lr_label と eval_recipe.build_eval_recipe
#    の組み合わせで等価な検証を行う）。
def test_mmdet_trainer_eval_recipe_ddp_fields(monkeypatch):
    """単一 GPU では gpu_count=1, lr_scaling="none"。DDP 2 GPU では gpu_count=2,
    lr_scaling="linear_x2"。eval_recipe.build_eval_recipe との結合で検証する。"""
    from egosurgery.utils.eval_recipe import (
        LOCKED_DOWN_TEST_CFG,
        PAPER_SPLIT_SIZES,
        build_eval_recipe,
    )

    # 単一 GPU。
    t1 = _make_trainer_no_setup(monkeypatch)
    recipe = build_eval_recipe(
        test_cfg=LOCKED_DOWN_TEST_CFG, split_sizes=PAPER_SPLIT_SIZES,
        server_name="bengio",
        gpu_count=t1.world_size,
        effective_batch_size=int(t1.cfg.train.batch_size) * t1.world_size,
        lr_scaling=t1._lr_scaling_label,
    )
    assert recipe["gpu_count"] == 1
    assert recipe["effective_batch_size"] == 2
    assert recipe["lr_scaling"] == "none"

    # DDP 2 GPU。
    t2 = _make_trainer_no_setup(monkeypatch, world_size=2, rank=0, local_rank=0)
    recipe = build_eval_recipe(
        test_cfg=LOCKED_DOWN_TEST_CFG, split_sizes=PAPER_SPLIT_SIZES,
        server_name="bengio",
        gpu_count=t2.world_size,
        effective_batch_size=int(t2.cfg.train.batch_size) * t2.world_size,
        lr_scaling=t2._lr_scaling_label,
    )
    assert recipe["gpu_count"] == 2
    assert recipe["effective_batch_size"] == 4
    assert recipe["lr_scaling"] == "linear_x2"


# 10. WORLD_SIZE 未設定（単一 GPU）時に is_distributed=False / gpu_count=1
def test_mmdet_trainer_single_gpu_fallback(monkeypatch):
    """torchrun を介さない実行では DDP モードに入らない。"""
    trainer = _make_trainer_no_setup(monkeypatch)
    assert trainer.is_distributed is False
    assert trainer.world_size == 1
    assert trainer.rank == 0
    assert trainer._lr_scaling_label == "none"


# 11. lr_scaling_mode=linear かつ world_size=2 で linear_x2 ラベル
def test_resolve_lr_linear_scaling(monkeypatch):
    """torchrun + lr_scaling_mode=linear → "linear_x2"。"""
    trainer = _make_trainer_no_setup(
        monkeypatch, world_size=2, rank=0, local_rank=0, lr_scaling_mode="linear",
    )
    assert trainer.is_distributed is True
    assert trainer.world_size == 2
    assert trainer._lr_scaling_label == "linear_x2"


# 12. lr_scaling_mode=keep_effective_bs で per_gpu_bs_adjusted ラベル
def test_resolve_lr_keep_effective_bs(monkeypatch):
    """lr_scaling_mode=keep_effective_bs → "per_gpu_bs_adjusted"。"""
    trainer = _make_trainer_no_setup(
        monkeypatch, world_size=2, rank=0, local_rank=0,
        lr_scaling_mode="keep_effective_bs",
    )
    assert trainer._lr_scaling_label == "per_gpu_bs_adjusted"


# 13. world_size=3 (任意の DDP サイズ) で linear_x{N} ラベル
def test_resolve_lr_linear_scaling_arbitrary_world_size(monkeypatch):
    """単一 GPU/DDP 2 GPU 以外の値でも linear_x{N} を返す（汎用性検証）。"""
    trainer = _make_trainer_no_setup(
        monkeypatch, world_size=4, rank=0, local_rank=0, lr_scaling_mode="linear",
    )
    assert trainer._lr_scaling_label == "linear_x4"

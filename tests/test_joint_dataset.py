"""JointClipDataset と統合 manifest の整合テスト（STEP B / B0-1）。

2 系統:
    1. 合成 manifest による単体テスト（常時実行）: parsing / box 変換 / GAP 添付 / 空箱。
    2. 実 manifest の整合テスト（存在時のみ）: phase manifest との frame 集合・順序一致、
       ラベル範囲、GAP キャッシュとの frame_id 整合。比較の三角形の土台を守る。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from egosurgery.datasets.constants import NUM_PHASE_CLASSES, NUM_TOOL_CLASSES
from egosurgery.datasets.joint_clip_dataset import JointClipDataset, collate_joint_clips

PROJ = Path(__file__).resolve().parents[1]
JOINT_DIR = PROJ / "data" / "processed" / "joint_manifest"
PHASE_DIR = PROJ / "data" / "processed" / "phase_manifest"
CACHE_DIR = PROJ / "data" / "processed" / "stage1_features" / "relation_detr_seed42"
SPLITS = ("train", "val", "test")


# --------------------------------------------------------------------------- #
# 1. 合成 manifest（常時実行）
# --------------------------------------------------------------------------- #
def _toy_manifest(tmp: Path) -> Path:
    man = {
        "split": "train", "num_clips": 1, "num_frames": 2, "num_boxes": 3,
        "clips": [{
            "clip_id": "99_1", "video": "99",
            "frames": [
                {"frame": "99_1_0001", "image_path": "data/raw/ego/train/99/99_1_0001.jpg",
                 "phase": "design", "phase_label": 2,
                 "boxes": [[10.0, 20.0, 30.0, 40.0], [0.0, 0.0, 5.0, 5.0]],
                 "tool_labels": [11, 3]},
                {"frame": "99_1_0002", "image_path": "data/raw/ego/train/99/99_1_0002.jpg",
                 "phase": "incision", "phase_label": 7,
                 "boxes": [[1.0, 2.0, 3.0, 4.0]], "tool_labels": [9]},
            ],
        }],
    }
    p = tmp / "train.json"
    p.write_text(json.dumps(man), encoding="utf-8")
    return p


def _toy_gap(tmp: Path) -> Path:
    p = tmp / "train_gap.npz"
    np.savez(p, frame_ids=np.asarray(["99_1_0001", "99_1_0002"]),
             features=np.arange(2 * 2048, dtype=np.float32).reshape(2, 2048))
    return p


def test_synthetic_parsing_and_box_xyxy(tmp_path):
    ds = JointClipDataset(_toy_manifest(tmp_path), proj_root=PROJ, box_format="xyxy")
    assert len(ds) == 1
    clip = ds[0]
    assert clip["clip_id"] == "99_1"
    assert clip["frame_ids"] == ["99_1_0001", "99_1_0002"]
    # phase ラベルは時系列順
    assert torch.equal(clip["phase_labels"], torch.tensor([2, 7]))
    # box: xywh [10,20,30,40] -> xyxy [10,20,40,60]
    b0 = clip["boxes"][0]
    assert b0.shape == (2, 4)
    assert torch.allclose(b0[0], torch.tensor([10.0, 20.0, 40.0, 60.0]))
    assert torch.equal(clip["tool_labels"][0], torch.tensor([11, 3]))
    # image_path は絶対パス
    assert clip["image_paths"][0].endswith("data/raw/ego/train/99/99_1_0001.jpg")


def test_synthetic_box_xywh_passthrough(tmp_path):
    ds = JointClipDataset(_toy_manifest(tmp_path), proj_root=PROJ, box_format="xywh")
    b0 = ds[0]["boxes"][0]
    assert torch.allclose(b0[0], torch.tensor([10.0, 20.0, 30.0, 40.0]))


def test_synthetic_gap_attach(tmp_path):
    ds = JointClipDataset(_toy_manifest(tmp_path), proj_root=PROJ,
                          gap_cache_path=_toy_gap(tmp_path))
    clip = ds[0]
    assert clip["gap"].shape == (2, 2048)
    # 行は frame_id 順に並ぶ（0001 -> row0, 0002 -> row1）
    assert torch.allclose(clip["gap"][1], torch.arange(2048, 2 * 2048, dtype=torch.float32))


def test_collate_is_list(tmp_path):
    ds = JointClipDataset(_toy_manifest(tmp_path), proj_root=PROJ)
    batch = collate_joint_clips([ds[0]])
    assert isinstance(batch, list) and len(batch) == 1 and batch[0]["clip_id"] == "99_1"


def test_empty_boxes_shape(tmp_path):
    man = {"split": "train", "clips": [{"clip_id": "0_0", "video": "0", "frames": [
        {"frame": "0_0_0", "image_path": "x.jpg", "phase": "closure", "phase_label": 1,
         "boxes": [], "tool_labels": []}]}]}
    p = tmp_path / "e.json"
    p.write_text(json.dumps(man), encoding="utf-8")
    clip = JointClipDataset(p, proj_root=PROJ)[0]
    assert clip["boxes"][0].shape == (0, 4)
    assert clip["tool_labels"][0].shape == (0,)


# --------------------------------------------------------------------------- #
# 2. 実 manifest 整合（存在時のみ）— 比較の三角形の土台を守る
# --------------------------------------------------------------------------- #
def _have_real(split: str) -> bool:
    return (JOINT_DIR / f"{split}.json").exists() and (PHASE_DIR / f"{split}.json").exists()


@pytest.mark.parametrize("split", SPLITS)
def test_real_frame_set_and_order_match_phase(split):
    if not _have_real(split):
        pytest.skip(f"joint/phase manifest が無い split={split}")
    joint = json.loads((JOINT_DIR / f"{split}.json").read_text())
    phase = json.loads((PHASE_DIR / f"{split}.json").read_text())
    # clip 単位・frame 単位で phase manifest と完全一致（派生元との構造同一性）
    j_frames = [(c["clip_id"], f["frame"]) for c in joint["clips"] for f in c["frames"]]
    p_frames = [(c["clip_id"], f["frame"]) for c in phase["clips"] for f in c["frames"]]
    assert j_frames == p_frames, f"[{split}] joint と phase の clip/frame 列が不一致"
    # phase_label も一致
    j_lab = [f["phase_label"] for c in joint["clips"] for f in c["frames"]]
    p_lab = [f["label"] for c in phase["clips"] for f in c["frames"]]
    assert j_lab == p_lab


@pytest.mark.parametrize("split", SPLITS)
def test_real_label_ranges(split):
    if not _have_real(split):
        pytest.skip(f"joint manifest が無い split={split}")
    ds = JointClipDataset(JOINT_DIR / f"{split}.json", proj_root=PROJ)
    n_boxes = 0
    for i in range(len(ds)):
        clip = ds[i]
        assert clip["phase_labels"].min() >= 0
        assert clip["phase_labels"].max() < NUM_PHASE_CLASSES
        for tl, bx in zip(clip["tool_labels"], clip["boxes"]):
            assert tl.shape[0] == bx.shape[0]
            if tl.numel():
                assert int(tl.min()) >= 0 and int(tl.max()) < NUM_TOOL_CLASSES
                # xyxy は x2>=x1, y2>=y1
                assert bool((bx[:, 2] >= bx[:, 0]).all() and (bx[:, 3] >= bx[:, 1]).all())
            n_boxes += tl.shape[0]
    # boxes 総数が manifest ヘッダと一致
    assert n_boxes == json.loads((JOINT_DIR / f"{split}.json").read_text())["num_boxes"]


@pytest.mark.parametrize("split", SPLITS)
def test_real_gap_cache_alignment(split):
    cache = CACHE_DIR / f"{split}_gap.npz"
    if not _have_real(split) or not cache.exists():
        pytest.skip(f"joint manifest か GAP キャッシュが無い split={split}")
    ds = JointClipDataset(JOINT_DIR / f"{split}.json", proj_root=PROJ, gap_cache_path=cache)
    # 全 clip で GAP 添付が成功（= 全 frame_id がキャッシュに存在）。先頭 clip で形状確認。
    clip = ds[0]
    assert clip["gap"].shape == (len(clip["frame_ids"]), 2048)
    assert not torch.isnan(clip["gap"]).any()

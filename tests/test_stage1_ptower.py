"""Contract checks for the Stage 1 phase tower entry point."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from omegaconf import OmegaConf

SPEC = importlib.util.spec_from_file_location(
    "stage1_ptower", Path(__file__).parents[1] / "scripts/stage1_ptower.py")
tower = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tower)


def test_hydra_evidence_enrichment_preserves_original():
    cfg = OmegaConf.create({"seed": 42})
    OmegaConf.set_struct(cfg, True)
    resolved = tower.enrich(cfg, {"weights": "ImageNet"})
    assert resolved.weights == "ImageNet"
    assert "weights" not in cfg


def test_folds_partition_and_test_once():
    folds = tower.folds()
    all_videos = {f"{i:02d}" for i in range(1, 16)}
    tests = []
    for parts in folds.values():
        train, val, test = (set(parts[k]) for k in ("train", "val", "test"))
        assert not (train & val or train & test or val & test)
        assert train | val | test == all_videos
        tests.extend(test)
    assert len(tests) == len(set(tests)) == 15


def test_fold_loader_groups_clips_and_rejects_cache_change(tmp_path):
    clips = []
    ids = []
    for video in range(1, 16):
        for clip in (2, 1):
            fid = f"{video:02d}_{clip}_0001"
            ids.append(fid)
            clips.append({"video": f"{video:02d}", "clip_id": f"{video:02d}_{clip}",
                          "frames": [{"frame": fid, "label": clip}]})
    for split in ("train", "val", "test"):
        (tmp_path / f"{split}.json").write_text(json.dumps({"clips": clips if split == "train" else []}))
    cache = tmp_path / "features.npz"
    np.savez(cache, frame_ids=np.array(ids), features=np.zeros((len(ids), 2048), dtype=np.float32))
    cache.with_suffix(".json").write_text(json.dumps({"cache_sha256": tower.sha256(cache)}))
    cfg = OmegaConf.create({"cache": str(cache), "manifest_dir": str(tmp_path), "fold": "A"})
    splits, data = tower.load_fold(cfg)
    assert [v[0] for v in data["train"]] == splits["train"]
    assert [v[0] for v in data["val"]] == splits["val"]
    assert all(y.tolist() == [1, 2] for _, _, y in data["train"])
    with cache.open("ab") as f:
        f.write(b"changed")
    with pytest.raises(AssertionError):
        tower.load_fold(cfg)


def test_transformer_is_causal_with_local_attention():
    torch.manual_seed(42)
    cfg = OmegaConf.create({"layers": 2, "maps": 16, "history": 3})
    model = tower.AggregatedTeCNO(cfg, 9).eval()
    x = torch.randn(1, 2048, 12)
    modified = x.clone()
    modified[:, :, 6:] += 50
    captured = []
    original = model.attention.forward

    def capture(*args, **kwargs):
        captured.append(kwargs["src_mask"].clone())
        return original(*args, **kwargs)

    model.attention.forward = capture
    with torch.no_grad():
        before = model(x)[-1]
        after = model(modified)[-1]
    torch.testing.assert_close(before[:, :, :6], after[:, :, :6], atol=1e-6, rtol=1e-6)
    assert not torch.allclose(before[:, :, 6:], after[:, :, 6:])
    assert captured[0][5].tolist() == [True, True, True, False, False, False] + [True] * 6

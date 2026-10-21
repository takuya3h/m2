"""The search must reject missing frames, changed settings and unknown point tables."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tower_search_common import check_detector_groups, points_from_prereg  # noqa: E402


def test_preregistered_point_table_and_broken_table():
    text = (ROOT / "tasks/T-2026-10-22-tower-reselect-search-dlsta/prereg.md").read_text()
    rows = points_from_prereg(text)
    assert rows[0]["lr"] == 1e-4
    assert rows[13]["lr"] == 4.83e-4
    assert rows[3]["phase_weight_decay"] == 2.71
    with pytest.raises(ValueError, match="exactly"):
        points_from_prereg(text.replace("| 13 |", "| 99 |"))


def test_detector_groups_reject_changed_lr_and_decay():
    point = {"lr": 1e-4, "detector_weight_decay": 1e-4}
    groups = [{"lr": lr, "weight_decay": wd} for lr, wd in
              [(1e-4, 1e-4), (1e-5, 1e-4), (1e-5, 0),
               (1e-5, 1e-4), (1e-5, 0), (1e-4, 0)]]
    check_detector_groups(groups, point)
    groups[2]["weight_decay"] = 1e-4
    with pytest.raises(ValueError, match="optimizer groups"):
        check_detector_groups(groups, point)
    groups[2]["weight_decay"] = 0
    groups[0]["lr"] *= 2
    with pytest.raises(ValueError, match="optimizer groups"):
        check_detector_groups(groups, point)


def test_full_manifest_uses_fallback_without_changing_default(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("search_manifest", ROOT / "scripts/build_phase_manifest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "PROJ", tmp_path)
    monkeypatch.setattr(module, "PAPER_SPLIT_VIDEOS", {"train": ["01"], "val": [], "test": []})
    monkeypatch.setattr(module, "PHASE_CSV_DIR", tmp_path / "csv")
    monkeypatch.setattr(module, "EGO_ROOT", tmp_path / "raw")
    monkeypatch.setattr(module, "OUT_DIR", tmp_path / "default")
    (tmp_path / "csv").mkdir()
    (tmp_path / "csv/01_1.csv").write_text("Frame,Phase\n01_1_0001,cut\n01_1_0002,cut\n")
    raw = tmp_path / "raw/train/01"
    raw.mkdir(parents=True)
    (raw / "01_1_0001.jpg").write_bytes(b"image")
    fallback = tmp_path / "distributed/01_1"
    fallback.mkdir(parents=True)
    image = fallback / "01_1_0002.jpg"
    image.write_bytes(b"image")
    module.build()
    original = (tmp_path / "default/train.json").read_bytes()
    assert json.loads(original)["num_frames"] == 1
    module.build(fallback_root=tmp_path / "distributed", out_dir=tmp_path / "full")
    assert json.loads((tmp_path / "full/train.json").read_text())["num_frames"] == 2
    assert (tmp_path / "default/train.json").read_bytes() == original
    image.rename(fallback / "absent.jpg")
    module.build(fallback_root=tmp_path / "distributed", out_dir=tmp_path / "missing")
    assert json.loads((tmp_path / "missing/train.json").read_text())["num_frames"] == 1
    with pytest.raises(ValueError, match="separate"):
        module.build(fallback_root=tmp_path / "distributed")

"""Check P*-20's fold table, grid and recipe without training anything."""
import copy
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

pytest.importorskip("torch")
import build_phase_manifest_p20 as manifest  # noqa: E402
import run_stage1_ptower_20 as runner  # noqa: E402
import stage1_ptower as base  # noqa: E402
import stage1_ptower_20 as p20  # noqa: E402

# --- acceptance a: the extra videos enter train only ------------------------

def test_extra_videos_enter_every_fold_train_and_nothing_else():
    report = manifest.verify_folds(base.folds(), p20.folds_p20())
    assert set(report) == set("ABCDE")
    assert all(r["train_added"] == list(p20.EXTRA_TRAIN) for r in report.values())


def test_an_extra_video_in_val_fails_the_check():
    """Breaking control for acceptance a."""
    broken = p20.folds_p20()
    broken["A"]["val"] = broken["A"]["val"] + ["17"]
    with pytest.raises(RuntimeError, match="extra in val/test"):
        manifest.verify_folds(base.folds(), broken)


def test_video_22_in_train_fails_the_check():
    broken = p20.folds_p20()
    broken["C"]["train"] = broken["C"]["train"] + ["22"]
    with pytest.raises(RuntimeError):
        manifest.verify_folds(base.folds(), broken)


def test_the_canonical_table_is_left_unchanged():
    before = copy.deepcopy(base.folds())
    p20.folds_p20()
    assert base.folds() == before
    assert not set(p20.EXTRA_TRAIN) & {v for s in before.values() for p in s.values() for v in p}


# --- grid -------------------------------------------------------------------

def test_grid_is_two_chains_times_seven_backbones_plus_one_control():
    assert len(runner.grid("FT")) == len(runner.grid("EX")) == len(runner.grid("HEAD")) == 14
    assert [p["action"] for p in runner.grid("CTRL")] == ["finetune", "extract", "train"]
    assert all(p["data_setting"] == "P20" for p in runner.grid("FT"))
    assert runner.grid("CTRL")[0]["data_setting"] == "P15"


def test_each_chain_gets_the_third_rounds_confirmed_head():
    heads = {(p["init"], p["candidate"], p["layers"], p["smoothing_weight"], p["history"])
             for p in runner.grid("HEAD")}
    assert heads == {("coco", "C", 8, 0.3, 30), ("imagenet", "B", 8, 0.0, 30)}


def test_the_control_reads_the_fifteen_video_manifest_and_its_own_cache():
    args = runner.arguments(runner.grid("CTRL")[0], 0, False)
    assert f"manifest_dir={runner.P15_MANIFEST}" in args
    assert any(a.startswith("cache=") and "p15ctl_" in a for a in args)
    args = runner.arguments(runner.grid("FT")[0], 0, False)
    assert not any(a.startswith("manifest_dir=") for a in args)
    assert any(a.startswith("cache=") and "/p20_" in a for a in args)


# --- acceptance b: the recipe is the third round's --------------------------

ALLOWED = {"task_id", "step", "data_setting", "ft_lr", "cache", "manifest_dir"}


def recipe_diff(a, b):
    return sorted(k for k in set(a) | set(b) if k != "hydra" and a.get(k) != b.get(k))


def test_the_config_differs_from_the_third_round_only_where_allowed():
    r3 = yaml.safe_load((ROOT / "configs/stage1_ptower_r3.yaml").read_text())
    now = yaml.safe_load((ROOT / "configs/stage1_ptower_20.yaml").read_text())
    assert set(recipe_diff(r3, now)) <= ALLOWED


def test_changing_one_recipe_item_shows_up_in_the_diff():
    """Breaking control for acceptance b."""
    now = yaml.safe_load((ROOT / "configs/stage1_ptower_20.yaml").read_text())
    changed = dict(now, ft_accum_steps=2)
    assert recipe_diff(now, changed) == ["ft_accum_steps"]

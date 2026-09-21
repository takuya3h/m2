"""Check the second round's fold discipline and freeze range without training."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

torch = pytest.importorskip("torch")
import run_stage1_ptower_r2 as runner  # noqa: E402
import stage1_ptower as base  # noqa: E402
import stage1_ptower_r2 as r2  # noqa: E402


def test_only_the_stem_is_frozen():
    model = r2.build_backbone(9, "cpu")
    report = r2.freeze_report(model)
    assert report["stem"] == 0
    assert all(report[name] > 0 for name in ("layer1", "layer2", "layer3", "layer4", "fc"))
    # Both directions: unfreezing the stem must make the count non-zero.
    model.conv1.requires_grad_(True)
    assert r2.freeze_report(model)["stem"] > 0


def test_stem_stays_in_eval_while_the_rest_trains():
    model = r2.build_backbone(9, "cpu")
    r2.stem_eval(model)
    assert not model.bn1.training and model.layer4.training and model.fc.training


def test_fold_frames_take_only_the_named_videos_in_manifest_order():
    clips = [{"video": "01", "frames": [{"frame": "01_1_0001", "image_path": "a", "label": 0},
                                        {"frame": "01_1_0002", "image_path": "b", "label": 1}]},
             {"video": "09", "frames": [{"frame": "09_1_0001", "image_path": "c", "label": 2}]}]
    taken = r2.FoldFrames(clips, ["01"], train=False)
    assert [f["frame"] for f in taken.frames] == ["01_1_0001", "01_1_0002"]
    # Both directions: a video that is not asked for must not appear.
    assert [f["frame"] for f in r2.FoldFrames(clips, ["09"], train=False).frames] == ["09_1_0001"]


def test_train_transform_adds_the_flip_and_eval_does_not():
    clips = [{"video": "01", "frames": [{"frame": "01_1_0001", "image_path": "a", "label": 0}]}]
    assert "RandomHorizontalFlip" in str(r2.FoldFrames(clips, ["01"], train=True).transform)
    assert "RandomHorizontalFlip" not in str(r2.FoldFrames(clips, ["01"], train=False).transform)


def test_grid_sizes_and_fold_seed_discipline():
    assert len(runner.grid("FT")) == 14 and len(runner.grid("EX")) == 14
    assert len(runner.grid("HEAD")) == 140
    seeds = {(p["fold"], p["seed"]) for p in runner.grid("FT")}
    assert seeds == {("A", 42), ("A", 123), ("A", 456)} | {(f, 42) for f in "BCDE"}
    assert len({p["ft_lr"] for p in runner.grid("FT")}) == 2


def test_each_backbone_gets_its_own_cache():
    caches = {runner.cache_of(p) for p in runner.grid("EX")}
    assert len(caches) == 14


def test_fine_tune_never_sees_val_or_test_videos():
    table = base.folds()
    for fold, split in table.items():
        assert not set(split["train"]) & (set(split["val"]) | set(split["test"])), fold


def test_the_learning_rate_widens_the_table_but_never_breaks_a_tie():
    """The rule is the first round's; ft_lr rides along without entering it."""
    from select_stage1_ptower import select

    def row(candidate, layers, lr, jaccard, pstd=0.03):
        return {"candidate": candidate, "layers": layers, "ft_lr": lr,
                "mean_jaccard": jaccard, "mean_accuracy": 0.8,
                "fold_A_pstd": pstd, "mean_seconds": 10.0}

    # Same candidate and receptive field, differing only in learning rate:
    # the tie falls through to the steadier seeds, exactly as in the first round.
    rows = [row("C", 8, 1e-4, 0.51, pstd=0.09), row("C", 8, 3.3e-5, 0.50, pstd=0.01)]
    chosen, reason = select(rows)
    assert chosen["ft_lr"] == 3.3e-5 and "smaller fold A seed pstd" in reason
    # Both directions: when the top row is the steadier one it keeps the win.
    rows = [row("C", 8, 1e-4, 0.51, pstd=0.01), row("C", 8, 3.3e-5, 0.50, pstd=0.09)]
    assert select(rows)[0]["ft_lr"] == 1e-4
    # A clear winner outside the spread is not sent to any tie-break.
    assert select([row("B", 6, 1e-4, 0.70), row("A", 6, 3.3e-5, 0.50)])[0]["candidate"] == "B"


def test_selection_ignores_columns_that_carry_test_values():
    from select_stage1_ptower import select

    base_rows = [{"candidate": "A", "layers": 6, "ft_lr": 1e-4, "mean_jaccard": 0.50,
                  "mean_accuracy": 0.8, "fold_A_pstd": 0.03, "mean_seconds": 10.0},
                 {"candidate": "B", "layers": 6, "ft_lr": 3.3e-5, "mean_jaccard": 0.51,
                  "mean_accuracy": 0.8, "fold_A_pstd": 0.03, "mean_seconds": 10.0}]
    before = select(base_rows)[0]["candidate"]
    poisoned = [dict(r, test_jaccard=100 if r["candidate"] == "B" else -100) for r in base_rows]
    assert select(poisoned)[0]["candidate"] == before

"""Check the third round's init chains, whole-frame input and epoch budget.

None of these train: they read the rule, the transform and the grid directly.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

torch = pytest.importorskip("torch")
import run_stage1_ptower_r3 as runner  # noqa: E402
import stage1_ptower as base  # noqa: E402
import stage1_ptower_r2 as r2  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402
from PIL import Image  # noqa: E402

# --- the epoch budget: one rule for every run -------------------------------

def test_the_rate_drops_once_after_four_stalls_then_the_run_stops():
    """The detector tower's second round: 4 stalls lower, 4 more stop."""
    stale, lowered, seen = 0, False, []
    for _ in range(8):
        action, stale, lowered = r3.plateau_action(False, stale, lowered, 4)
        seen.append(action)
    assert seen == ["continue", "continue", "continue", "lower",
                    "continue", "continue", "continue", "stop"]


def test_an_improvement_clears_the_stall_count():
    stale, lowered = 0, False
    for _ in range(3):
        action, stale, lowered = r3.plateau_action(False, stale, lowered, 4)
        assert action == "continue"
    action, stale, lowered = r3.plateau_action(True, stale, lowered, 4)
    assert action == "continue" and stale == 0 and not lowered
    # Both directions: after the reset it takes four fresh stalls to lower.
    for _ in range(3):
        action, stale, lowered = r3.plateau_action(False, stale, lowered, 4)
        assert action == "continue"
    assert r3.plateau_action(False, stale, lowered, 4)[0] == "lower"


def test_the_rate_is_never_lowered_twice():
    stale, lowered = 0, True
    for _ in range(3):
        action, stale, lowered = r3.plateau_action(False, stale, lowered, 4)
        assert action == "continue"
    assert r3.plateau_action(False, stale, lowered, 4)[0] == "stop"


def test_the_budget_the_contract_asks_for_is_the_one_in_the_config():
    import yaml
    cfg = yaml.safe_load((ROOT / "configs/stage1_ptower_r3.yaml").read_text())
    assert cfg["ft_epochs"] == 36 and cfg["ft_patience"] == 4 and cfg["ft_lr_decay"] == 0.1


# --- whole frame at short side 800 ------------------------------------------

def test_the_input_keeps_the_whole_frame_at_short_side_800():
    frame = Image.new("RGB", (1920, 1080))
    tensor = r3.EVAL_TRANSFORM(frame)
    assert tuple(tensor.shape) == (3, 800, 1422)
    assert r3.SHORT_SIDE == 800


def test_no_crop_is_applied_although_the_second_round_cropped():
    """Acceptance c: the whole frame survives, which is what changed from r2."""
    frame = Image.new("RGB", (1920, 1080))
    third = r3.EVAL_TRANSFORM(frame)
    # Keeping the aspect ratio is what tells us nothing was cut off.
    assert abs(third.shape[2] / third.shape[1] - 1920 / 1080) < 0.005
    assert "crop" not in str(r3.EVAL_TRANSFORM).lower()
    # Both directions: the second round's preset squares the frame off at 224,
    # so only 224/455 = 49% of its width survived.
    assert tuple(r2.EVAL_TRANSFORM(frame).shape) == (3, 224, 224)
    assert "crop_size=[224]" in str(r2.EVAL_TRANSFORM)


def test_train_transform_adds_the_flip_and_eval_does_not():
    clips = [{"video": "01", "frames": [{"frame": "01_1_0001", "image_path": "a", "label": 0}]}]
    assert "RandomHorizontalFlip" in str(r3.FoldFrames(clips, ["01"], train=True).transform)
    assert "RandomHorizontalFlip" not in str(r3.FoldFrames(clips, ["01"], train=False).transform)


# --- the two init chains ----------------------------------------------------

def test_the_coco_chain_starts_from_the_weights_the_detector_tower_starts_from():
    """Acceptance a: same summary as D*-COCO's starting checkpoint."""
    if not r3.COCO_CHECKPOINT.exists():
        pytest.skip(f"missing {r3.COCO_CHECKPOINT}")
    from torchvision.models import resnet50
    straight = resnet50(weights=None)
    missing, unexpected = straight.load_state_dict(r3.coco_backbone_state(), strict=False)
    assert sorted(missing) == ["fc.bias", "fc.weight"] and not unexpected
    expected = r3.backbone_digest(straight)
    _, source, digest = r3.build_backbone(9, "cpu", "coco")
    assert digest == expected
    assert source.endswith("relation_detr_resnet50_800_1333_coco_1x.pth")
    # Both directions: the other chain must not produce the same summary.
    _, _, imagenet = r3.build_backbone(9, "cpu", "imagenet")
    assert imagenet != digest


def test_an_unknown_init_chain_is_refused():
    with pytest.raises(ValueError):
        r3.build_backbone(9, "cpu", "dinov2")


def test_only_the_stem_is_frozen_in_both_chains():
    for init in runner.INITS:
        model, _, _ = r3.build_backbone(9, "cpu", init)
        report = r3.freeze_report(model)
        assert report["stem"] == 0, init
        assert all(report[n] > 0 for n in ("layer1", "layer2", "layer3", "layer4", "fc")), init
        # Both directions: unfreezing the stem must make the count non-zero.
        model.conv1.requires_grad_(True)
        assert r3.freeze_report(model)["stem"] > 0, init


def test_the_stem_stays_in_eval_while_the_rest_trains():
    model, _, _ = r3.build_backbone(9, "cpu", "imagenet")
    r3.stem_eval(model)
    assert not model.bn1.training and model.layer4.training and model.fc.training


# --- the sweep --------------------------------------------------------------

def test_grid_sizes_and_fold_seed_discipline():
    assert len(runner.grid("FT")) == 28 and len(runner.grid("EX")) == 28
    assert len(runner.grid("HEAD")) == 280
    seeds = {(p["fold"], p["seed"]) for p in runner.grid("FT")}
    assert seeds == {("A", 42), ("A", 123), ("A", 456)} | {(f, 42) for f in "BCDE"}
    assert {p["init"] for p in runner.grid("FT")} == {"coco", "imagenet"}
    assert {p["ft_lr"] for p in runner.grid("FT")} == {0.0001, 0.0003}


def test_each_backbone_gets_its_own_cache_and_the_chain_is_part_of_the_name():
    caches = {runner.cache_of(p) for p in runner.grid("EX")}
    assert len(caches) == 28
    one = dict(init="coco", ft_lr=0.0003, fold="A", seed=42)
    assert runner.cache_of(one) != runner.cache_of(dict(one, init="imagenet"))


def test_fine_tune_never_sees_val_or_test_videos():
    for fold, split in base.folds().items():
        assert not set(split["train"]) & (set(split["val"]) | set(split["test"])), fold


def test_fold_frames_take_only_the_named_videos_in_manifest_order():
    clips = [{"video": "01", "frames": [{"frame": "01_1_0001", "image_path": "a", "label": 0},
                                        {"frame": "01_1_0002", "image_path": "b", "label": 1}]},
             {"video": "09", "frames": [{"frame": "09_1_0001", "image_path": "c", "label": 2}]}]
    assert [f["frame"] for f in r3.FoldFrames(clips, ["01"], train=False).frames] == \
        ["01_1_0001", "01_1_0002"]
    # Both directions: a video that is not asked for must not appear.
    assert [f["frame"] for f in r3.FoldFrames(clips, ["09"], train=False).frames] == ["09_1_0001"]


def test_the_effective_batch_matches_the_preregistered_one():
    """prereg fixed 64; the card holds only 16, so accumulation carries the rest."""
    import yaml
    cfg = yaml.safe_load((ROOT / "configs/stage1_ptower_r3.yaml").read_text())
    assert cfg["ft_batch_size"] * cfg["ft_accum_steps"] == 64


# --- the stop condition: no fold may come out below the second round ---------

def test_a_fold_below_the_second_round_stops_the_sweep():
    reference = {"A": 0.7149, "B": 0.5846}
    params = {"action": "finetune", "fold": "A"}
    message = runner.below_round_two(params, {"phase_accuracy": 0.7000}, reference)
    assert message is not None and "fold A" in message
    # Both directions: at or above the second round the sweep goes on.
    assert runner.below_round_two(params, {"phase_accuracy": 0.7149}, reference) is None
    assert runner.below_round_two(params, {"phase_accuracy": 0.8759}, reference) is None


def test_only_the_fine_tune_is_measured_against_the_second_round():
    """Heads and extractions have no second-round counterpart at this key."""
    reference = {"A": 0.7149}
    for action in ("train", "extract"):
        assert runner.below_round_two({"action": action, "fold": "A"},
                                      {"phase_accuracy": 0.0}, reference) is None


def test_an_unmeasured_fold_is_not_silently_passed_as_zero():
    """A missing reference means no comparison, not a comparison against zero."""
    assert runner.below_round_two({"action": "finetune", "fold": "Z"},
                                  {"phase_accuracy": 0.1}, {"A": 0.7}) is None


def test_the_second_round_reference_covers_every_fold():
    reference = runner.round_two_frame_accuracy()
    assert set(reference) == set("ABCDE")
    assert all(0.0 < v < 1.0 for v in reference.values())


def test_task_b_clears_the_stop_condition():
    """The one run already measured must not trip the rule that was added after it."""
    done = runner.evidence_for({"action": "finetune", "init": "coco",
                                "ft_lr": 0.0003, "fold": "A", "seed": 42})
    if done is None:
        pytest.skip("Task B has not been run on this host")
    _, metrics = done
    assert runner.below_round_two({"action": "finetune", "fold": "A"}, metrics,
                                  runner.round_two_frame_accuracy()) is None

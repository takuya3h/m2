"""Candidate 5 temporal heads on the Stage 1 temporal-head path.

The baseline digests were taken before the heads were added (commit recorded in
tasks/T-2026-10-23-ptower-cand5-heads-impl/audit.md); existing candidates must keep them.
"""
import hashlib
import importlib.util
import io
import json
import math
import statistics
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn.functional as F
from omegaconf import OmegaConf
from torch import nn

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("stage1_ptower", ROOT / "scripts/stage1_ptower.py")
tower = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tower)

# Final-stage output of each existing candidate under configs/stage1_ptower.yaml defaults,
# parameters from manual_seed(42), input randn(1, 2048, 40) from manual_seed(7), 4 CPU threads.
# A and C share the model; they differ only in the smoothing loss.
BASELINE = {
    "linear": "8b65f13bc2a8612518d2e1306a60e0d2ee6a268ee9ada980671a612785f845ae",
    "A": "a3cd6d08cad21667036787b836f4c971fb9c958d60741f7d7e632d1584c1a00f",
    "B": "0816c1e9f71cbafb15a5ac1c0f9aa353d9e0583f797316819ed6f8023dc2a243",
    "C": "a3cd6d08cad21667036787b836f4c971fb9c958d60741f7d7e632d1584c1a00f",
}


def config(**overrides):
    return OmegaConf.merge(OmegaConf.load(ROOT / "configs/stage1_ptower.yaml"), overrides)


def output_digest(candidate, **overrides):
    threads = torch.get_num_threads()
    torch.set_num_threads(4)
    try:
        torch.manual_seed(42)
        model = tower.build_model(config(candidate=candidate, **overrides), 9).eval()
        torch.manual_seed(7)
        x = torch.randn(1, 2048, 40)
        with torch.no_grad():
            out = model(x)[-1]
    finally:
        torch.set_num_threads(threads)
    return hashlib.sha256(out.contiguous().numpy().tobytes()).hexdigest()


@pytest.mark.parametrize("candidate", sorted(BASELINE))
def test_existing_candidates_match_baseline(candidate):
    assert output_digest(candidate) == BASELINE[candidate]


def test_baseline_check_detects_a_changed_config():
    assert output_digest("A", layers=7) != BASELINE["A"]


def test_new_keys_are_absent_from_the_default_config():
    cfg = OmegaConf.load(ROOT / "configs/stage1_ptower.yaml")
    new = {"boundary_flag", "reset_at_clip", "gap_input", "ssm_state_dim", "ssm_layers",
           "ssm_selective", "memory_len", "progress_weight", "transition_prior", "tec_alpha",
           "tec_m", "tec_sigma", "egtp", "egtp_k", "egtp_reset_at_clip", "base_candidate"}
    assert not new & set(cfg)
    assert not tower.needs_info(cfg) and tower.input_dim(cfg) == 2048


# --- sequence information -------------------------------------------------------------

MANIFEST = ROOT / "data/processed/phase_manifest_all_phase"


@pytest.mark.skipif(not MANIFEST.exists(), reason="17,233-frame manifest absent on this host")
def test_manifest_gaps_reproduce_the_eda():
    clips = tower.manifests(OmegaConf.create({"manifest_dir": str(MANIFEST)}))
    summary = tower.gap_summary(clips)
    assert summary == {"videos": 15, "clips": 23, "frames": 17233, "pairs": 17210,
                       "delta_one": 16663, "delta_max": 254, "unknown": 23,
                       "unknown_between_clips": 8}
    assert round(100 * summary["delta_one"] / summary["pairs"], 1) == 96.8
    # Ignoring one clip boundary must leave one fewer unknown between clips.
    first, second = [c for c in clips if c["video"] == "03"]
    merged = [c for c in clips if c["video"] != "03"] + [
        {**first, "frames": first["frames"] + second["frames"]}]
    assert tower.gap_summary(merged)["unknown_between_clips"] == 7


def frames(clip, numbers):
    return [{"frame": f"01_{clip}_{n:04d}"} for n in numbers]


def test_sequence_info_keeps_unknown_gaps_apart_from_zero_and_one():
    info = tower.sequence_info([frames(1, [5, 6, 9]), frames(2, [1, 2])])
    assert info["clip"].tolist() == [0, 0, 0, 1, 1]
    assert info["delta"].tolist() == [tower.GAP_UNKNOWN, 1, 3, tower.GAP_UNKNOWN, 1]
    assert info["boundary"].tolist() == [1, 0, 0, 1, 0]
    assert tower.GAP_UNKNOWN not in (0, 1)


def write_fold(tmp_path):
    clips, ids = [], []
    for video in range(1, 16):
        for clip, numbers in ((2, (1, 2)), (1, (3, 7))):
            fids = [f"{video:02d}_{clip}_{n:04d}" for n in numbers]
            ids += fids
            clips.append({"video": f"{video:02d}", "clip_id": f"{video:02d}_{clip}",
                          "frames": [{"frame": f, "label": clip} for f in fids]})
    for split in ("train", "val", "test"):
        (tmp_path / f"{split}.json").write_text(json.dumps({"clips": clips if split == "train" else []}))
    cache = tmp_path / "features.npz"
    features = np.random.default_rng(0).normal(size=(len(ids), 2048)).astype(np.float32)
    np.savez(cache, frame_ids=np.array(ids), features=features)
    cache.with_suffix(".json").write_text(json.dumps({"cache_sha256": tower.sha256(cache)}))
    return OmegaConf.create({"cache": str(cache), "manifest_dir": str(tmp_path), "fold": "A"})


def test_load_fold_info_is_additive(tmp_path):
    cfg = write_fold(tmp_path)
    splits, plain = tower.load_fold(cfg)
    _, rich = tower.load_fold(cfg, info=True)
    for part in ("train", "val"):
        assert all(len(v) == 3 for v in plain[part])
        for a, b in zip(plain[part], rich[part]):
            assert a[0] == b[0] and np.array_equal(a[1], b[1]) and np.array_equal(a[2], b[2])
            assert b[3]["boundary"].tolist() == [1, 0, 1, 0]
            assert b[3]["delta"].tolist() == [tower.GAP_UNKNOWN, 4, tower.GAP_UNKNOWN, 1]
            assert b[3]["clip"].tolist() == [0, 0, 1, 1]


# --- heads: interface, causality, boundaries ------------------------------------------

CPU_HEADS = [("memory", {}), ("memory", {"memory_len": 0}), ("progress", {}),
             ("stabilize", {"base_candidate": "A"}),
             ("stabilize", {"base_candidate": "B"}), ("stabilize", {"base_candidate": "C"})]
GPU = pytest.mark.skipif(not torch.cuda.is_available(), reason="mamba-ssm kernels need CUDA")


def head(candidate, device="cpu", **overrides):
    torch.manual_seed(0)
    cfg = config(**{"candidate": candidate, "layers": 3, "maps": 16, "history": 5, "memory_len": 8,
                    **overrides})
    return tower.build_model(cfg, 9).to(device).eval(), cfg


def prefix_unchanged(model, x, t):
    """Outputs at positions < t are bit-identical when inputs at positions >= t change."""
    changed = x.clone()
    changed[:, :, t:] += 50
    with torch.no_grad():
        before, after = model(x), model(changed)
    return (all(torch.equal(a[:, :, :t], b[:, :, :t]) for a, b in zip(before, after))
            and not torch.equal(before[-1], after[-1]))


@pytest.mark.parametrize("candidate,extra", CPU_HEADS)
def test_cpu_heads_keep_the_interface_and_are_causal(candidate, extra):
    model, _ = head(candidate, **extra)
    x = torch.randn(1, 2048, 40)
    outs = model(x)
    assert isinstance(outs, list) and all(o.shape == (1, 9, 40) for o in outs)
    assert prefix_unchanged(model, x, 20)


@GPU
@pytest.mark.parametrize("selective", [True, False])
def test_ssm_keeps_the_interface_and_is_causal_on_gpu(selective):
    model, _ = head("ssm", "cuda", ssm_selective=selective, ssm_state_dim=16)
    x = torch.randn(1, 2048, 60, device="cuda")
    outs = model(x)
    assert len(outs) == 1 and outs[0].shape == (1, 9, 60)
    # Measured prefix difference on andrew's A6000 was 0.0, so the tolerance is zero.
    assert prefix_unchanged(model, x, 30)


@GPU
def test_ssm_selective_false_freezes_delta():
    model, _ = head("ssm", "cuda", ssm_selective=False)
    for layer in model.layers:
        assert not layer.dt_proj.weight.any() and not layer.dt_proj.weight.requires_grad
        assert not layer.dt_proj.bias.requires_grad
    selective, _ = head("ssm", "cuda")
    assert all(layer.dt_proj.weight.requires_grad for layer in selective.layers)


def test_progress_head_is_causal_too():
    model, _ = head("progress")
    x = torch.randn(1, 2048, 40)
    changed = x.clone()
    changed[:, :, 20:] += 50
    with torch.no_grad():
        before, after = model(x, with_progress=True)[-1], model(changed, with_progress=True)[-1]
    assert before.shape == (1, 9, 40) and ((before >= 0) & (before <= 1)).all()
    assert torch.equal(before[:, :, :20], after[:, :, :20])


class Bidirectional(nn.Module):
    def __init__(self):
        super().__init__()
        self.gru = nn.GRU(2048, 8, batch_first=True, bidirectional=True)
        self.head = nn.Linear(16, 9)

    def forward(self, x):
        return [self.head(self.gru(x.transpose(1, 2))[0]).transpose(1, 2)]


def test_causality_check_rejects_a_bidirectional_model():
    torch.manual_seed(0)
    assert not prefix_unchanged(Bidirectional().eval(), torch.randn(1, 2048, 40), 20)


def test_unknown_candidate_names_raise():
    with pytest.raises(ValueError):
        tower.build_model(config(candidate="nope"), 9)
    with pytest.raises(ValueError):
        tower.build_model(config(candidate="stabilize", base_candidate="ssm"), 9)
    with pytest.raises(ValueError):
        tower.input_dim(config(gap_input="seconds"))


def two_clip_info(t, cut):
    delta = np.ones(t, dtype=np.int64)
    delta[[0, cut]] = tower.GAP_UNKNOWN
    delta[cut + 3] = 5
    return {"clip": (np.arange(t) >= cut).astype(int), "delta": delta,
            "boundary": np.isin(np.arange(t), [0, cut]).astype(int)}


@pytest.mark.parametrize("reset", [True, False])
def test_reset_at_clip_cuts_the_dependence_on_the_previous_clip(reset):
    model, cfg = head("memory", reset_at_clip=reset, boundary_flag=True)
    info = two_clip_info(40, 25)
    x = np.random.default_rng(0).normal(size=(40, 2048)).astype(np.float32)
    changed = x.copy()
    changed[:25] += 50
    with torch.no_grad():
        before = tower.run_video(model, cfg, x, info, "cpu")[-1]
        after = tower.run_video(model, cfg, changed, info, "cpu")[-1]
    assert before.shape == (1, 9, 40)
    assert torch.equal(before[:, :, 25:], after[:, :, 25:]) == reset


def test_gap_input_switches_between_delta_and_flag():
    info = two_clip_info(40, 25)
    x = np.zeros((40, 2048), dtype=np.float32)
    flag = tower.model_input(config(gap_input="flag"), x, info)
    delta = tower.model_input(config(gap_input="delta", boundary_flag=True), x, info)
    assert flag.shape == (1, 2049, 40) and delta.shape == (1, 2051, 40)
    assert tower.input_dim(config(gap_input="delta", boundary_flag=True)) == 2051
    unknown = torch.tensor(info["delta"] == tower.GAP_UNKNOWN, dtype=torch.float32)
    assert torch.equal(flag[0, 2048], unknown) and torch.equal(delta[0, 2050], unknown)
    assert torch.equal(delta[0, 2048], torch.tensor(info["boundary"], dtype=torch.float32))
    expected = np.log(np.where(info["delta"] == tower.GAP_UNKNOWN, tower.GAP_CAP, info["delta"]))
    assert torch.allclose(delta[0, 2049], torch.tensor(expected, dtype=torch.float32))
    assert delta[0, 2049, 28].item() == pytest.approx(np.log(5))


# --- losses and inference rules -------------------------------------------------------

def test_progress_target_rises_in_each_run_and_ignores_clip_starts():
    y = np.array([2, 2, 2, 2, 5, 5, 5, 2])
    # A clip starts at index 2 inside the first run of phase 2; the run stays whole.
    target = tower.progress_target(y)
    assert target[:4].tolist() == pytest.approx([0, 1 / 3, 2 / 3, 1])
    assert target[4:7].tolist() == pytest.approx([0, 0.5, 1])
    assert target[7] == 0
    for a, b in ((0, 4), (4, 7)):
        assert (np.diff(target[a:b]) > 0).all()


def test_transition_matrix_uses_train_videos_only():
    data = {"train": [("01", None, np.array([0, 0, 1, 2])), ("02", None, np.array([3, 1]))],
            "val": [("03", None, np.array([4, 5]))]}
    allowed = tower.transition_matrix(data, 9)
    assert allowed[0, 1] and allowed[1, 2] and allowed[3, 1] and allowed.diagonal().all()
    assert allowed.sum() == 9 + 3
    data["val"] = [("03", None, np.array([7, 8, 0]))]
    assert np.array_equal(tower.transition_matrix(data, 9), allowed)
    data["train"].append(("04", None, np.array([4, 5])))
    assert not np.array_equal(tower.transition_matrix(data, 9), allowed)


def test_transition_decode_blocks_unseen_transitions():
    scores = np.array([[3.0, 1.0, 1.0], [0.0, 2.0, 0.0], [0.0, 0.0, 2.0]])
    allowed = np.eye(3, dtype=bool)
    allowed[0, 2] = True
    assert tower.transition_decode(scores, allowed).tolist() == [0, 0, 2]
    assert tower.transition_decode(scores, np.ones((3, 3), bool)).tolist() == [0, 1, 2]


def test_tec_weights_cover_the_first_m_frames_of_each_wrong_run():
    labels = torch.zeros(30, dtype=torch.long)
    pred = torch.zeros(30, dtype=torch.long)
    pred[5:17] = 1   # wrong run of 12 frames
    pred[20:23] = 2  # wrong run of 3 frames
    w = tower.tec_weights(pred, labels, 3.0, 8, 1.5)
    expected = torch.ones(30)
    for s, n in ((5, 8), (20, 3)):
        for d in range(n):
            expected[s + d] = 1 + 3.0 * np.exp(-d ** 2 / (2 * 1.5 ** 2))
    torch.testing.assert_close(w, expected, rtol=0, atol=0)
    assert w[5] == 4.0 and (w[13:17] == 1).all() and (w[:5] == 1).all()


def test_tec_loss_equals_weighted_ce_at_alpha_zero_and_not_above():
    torch.manual_seed(0)
    logits = torch.randn(50, 9)
    labels = torch.randint(0, 9, (50,))
    class_weights = torch.rand(9) + 0.5
    ce = F.cross_entropy(logits, labels, weight=class_weights)
    torch.testing.assert_close(tower.tec_loss(logits, labels, class_weights, 0.0, 8, 1.5), ce,
                               rtol=1e-6, atol=0)
    assert not torch.allclose(tower.tec_loss(logits, labels, class_weights, 3.0, 8, 1.5), ce)


EGTP_P1 = [0.4, 0.55, 0.6, 0.6, 0.8]  # p of class 1; class 0 holds the rest


def egtp_prob(p1=EGTP_P1):
    p1 = np.array(p1)
    return np.stack([1 - p1, p1])


def test_egtp_keeps_probabilities_and_matches_the_hand_computed_evidence():
    prob = egtp_prob()
    original = prob.copy()
    returned, held = tower.egtp(prob, 3.0)
    assert returned is prob and np.array_equal(prob, original)
    # State 0 from argmax at t=0; δ = log p1 − log p0 for class 1 from t=1.
    d1, d2, d3 = math.log(0.55 / 0.45), math.log(0.6 / 0.4), math.log(0.6 / 0.4)
    steps = list(tower.egtp_steps(prob, 3.0))
    assert steps[1][1][1] == pytest.approx(d1, abs=1e-12) and steps[1][2][1] == 1
    assert steps[1][4][1] == 0.0  # Z is 0 while n < 2
    # n = 2: σ = |d2 − d1|/√2, so Z = (d1 + d2)/(√2·σ) = (d1 + d2)/(d2 − d1) ≈ 2.96 < 3.
    assert steps[2][1][1] == pytest.approx(d1 + d2, abs=1e-12) and steps[2][2][1] == 2
    assert steps[2][4][1] == pytest.approx((d1 + d2) / (d2 - d1), abs=1e-12)
    # n = 3: Z = (d1 + d2 + d3)/(√3·stdev(d1, d2, d3)) ≈ 4.94 > 3, so the state switches at t=3.
    z3 = (d1 + d2 + d3) / (math.sqrt(3) * statistics.stdev([d1, d2, d3]))
    assert steps[3][4][1] == pytest.approx(z3, abs=1e-12)
    assert held.tolist() == [0, 0, 0, 1, 1]
    assert tower.egtp(prob, 2.9)[1].tolist() == [0, 0, 1, 1, 1]


def test_egtp_restarts_the_statistics_after_a_switch():
    # Switch to 1 at t=2 (k=2.9); class 0 has p 0.4 < 0.6 at t=3 and p 0.7 > 0.3 at t=4.
    steps = list(tower.egtp_steps(egtp_prob([0.4, 0.55, 0.6, 0.6, 0.3]), 2.9))
    assert [s[0] for s in steps] == [0, 0, 1, 1, 1]
    assert not steps[2][1].any() and not steps[2][2].any() and not steps[2][3].any()
    assert steps[3][1][0] == 0.0 and steps[3][2][0] == 0
    # Only the evidence after the switch is left: one increment, n = 1.
    assert steps[4][1][0] == pytest.approx(math.log(0.7 / 0.3), abs=1e-12) and steps[4][2][0] == 1


def test_egtp_is_causal():
    rng = np.random.default_rng(0)
    prob = rng.dirichlet(np.ones(9), size=200).T
    changed = prob.copy()
    changed[:, 120:] = rng.dirichlet(np.ones(9), size=80).T
    before, after = tower.egtp(prob, 0.5)[1], tower.egtp(changed, 0.5)[1]
    assert np.array_equal(before[:120], after[:120]) and not np.array_equal(before, after)


def test_egtp_threshold_holds_or_lets_the_state_move():
    rng = np.random.default_rng(1)
    prob = rng.dirichlet(np.ones(9), size=200).T
    assert set(tower.egtp(prob, 1e9)[1].tolist()) == {int(prob[:, 0].argmax())}
    assert len(set(tower.egtp(prob, 0.0)[1].tolist())) > 1
    # Constant evidence against the state (σ = 0, so the floor applies) switches in finite time.
    held = tower.egtp(egtp_prob([0.4] + [0.6] * 20), 5.0)[1]
    assert held[0] == 0 and held[-1] == 1


def test_egtp_starts_restart_from_argmax():
    prob = egtp_prob([0.4, 0.45, 0.45, 0.45, 0.8, 0.8])
    assert tower.egtp(prob, 1e9)[1].tolist() == [0] * 6
    assert tower.egtp(prob, 1e9, starts=[4])[1].tolist() == [0, 0, 0, 0, 1, 1]


# --- smoke: two epochs through train on synthetic features ----------------------------

def synthetic_fold(info, rng):
    def video(name):
        t = int(rng.integers(200, 320))
        cut = t // 2
        y = np.repeat(np.arange(9), int(np.ceil(t / 9)))[:t]
        x = (rng.normal(size=(t, 2048)) + y[:, None] * 0.1).astype(np.float32)
        clip = [{"frame": f"{name}_1_{n:04d}"} for n in range(1, cut + 1)]
        clip2 = [{"frame": f"{name}_2_{n:04d}"} for n in range(1, t - cut + 1)]
        return (name, x, y) + ((tower.sequence_info([clip, clip2]),) if info else ())
    splits = {"train": ["01", "02", "03", "04"], "val": ["05", "06"], "test": []}
    return splits, {part: [video(v) for v in splits[part]] for part in ("train", "val")}


SMOKE = [("A", "cpu", {}),
         ("memory", "cpu", {"reset_at_clip": True, "boundary_flag": True}),
         ("progress", "cpu", {"progress_weight": 1.0, "transition_prior": True, "gap_input": "delta"}),
         ("stabilize", "cpu", {"base_candidate": "C", "smoothing_weight": 0.3, "tec_alpha": 7.0,
                               "egtp": True, "egtp_k": 0.5, "egtp_reset_at_clip": True}),
         ("ssm", "cuda:0", {"boundary_flag": True, "ssm_state_dim": 16})]


@pytest.mark.parametrize("candidate,device,extra", SMOKE)
def test_two_epoch_smoke_leaves_no_checkpoint(candidate, device, extra, monkeypatch):
    if device.startswith("cuda") and not torch.cuda.is_available():
        pytest.skip("mamba-ssm kernels need CUDA")
    rng = np.random.default_rng(0)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "phase_vocab.json").write_text(json.dumps({f"p{i}": i for i in range(9)}))
        (tmp / "cache.npz").write_bytes(b"synthetic")
        monkeypatch.setattr(tower, "load_fold",
                            lambda cfg, parts=("train", "val"), info=False: synthetic_fold(info, rng))
        managers = []

        def evidence(cfg, description):
            manager = tower.ExperimentManager(tmp / "experiments", "phase1", "smoke", description, cfg.seed)
            manager.setup(OmegaConf.to_container(cfg, resolve=True))
            managers.append(manager)
            return manager

        monkeypatch.setattr(tower, "evidence", evidence)
        cfg = config(action="train", candidate=candidate, device=device, epochs=2, warmup_epochs=1,
                     cache=str(tmp / "cache.npz"), manifest_dir=str(tmp), task_id="smoke", **extra)
        torch.manual_seed(0)
        out = io.StringIO()
        with redirect_stdout(out):
            tower.train(cfg)
        assert "RUN_COMPLETE" in out.getvalue() and out.getvalue().count("epoch=") == 2
        exp_dir = managers[0].exp_dir
        assert (exp_dir / "checkpoints/best.pth").exists()
        metrics = json.loads((exp_dir / "metrics.json").read_text())
        assert "phase_jaccard" in json.dumps(metrics)
        if extra.get("egtp"):
            assert "egtp/phase_jaccard" in json.dumps(metrics)
        if extra.get("transition_prior"):
            assert (exp_dir / "transition_matrix.json").exists()
    assert not tmp.exists() and not list(tmp.parent.glob(f"{tmp.name}/**/*.pth"))

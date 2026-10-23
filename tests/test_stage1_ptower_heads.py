"""Candidate 5 temporal heads on the Stage 1 temporal-head path.

The baseline digests were taken before the heads were added (commit recorded in
tasks/T-2026-10-23-ptower-cand5-heads-impl/audit.md); existing candidates must keep them.
"""
import hashlib
import importlib.util
from pathlib import Path

import pytest
import torch
from omegaconf import OmegaConf

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

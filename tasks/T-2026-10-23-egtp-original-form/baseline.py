"""Digests of the eight candidates (EGTP off) and of every function in stage1_ptower.py except egtp.

Run from the repo root: CUDA_VISIBLE_DEVICES="" PYTHONPATH=src .venv/bin/python <this> <out.json>
"""
import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import torch
from omegaconf import OmegaConf

ROOT = Path.cwd()
spec = importlib.util.spec_from_file_location("stage1_ptower", ROOT / "scripts/stage1_ptower.py")
tower = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tower)


def config(**overrides):
    return OmegaConf.merge(OmegaConf.load(ROOT / "configs/stage1_ptower.yaml"), overrides)


def digest(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def model_digest(cfg):
    torch.set_num_threads(4)
    torch.manual_seed(42)
    model = tower.build_model(cfg, 9).eval()
    torch.manual_seed(7)
    x = torch.randn(1, 2048, 40)
    with torch.no_grad():
        outs = model(x)
    return [digest(o.numpy()) for o in outs]


ARMS = {
    "linear": {}, "A": {}, "B": {}, "C": {},
    "memory": {}, "memory_len0": {"memory_len": 0},
    "progress": {},
    "stabilize_A": {"base_candidate": "A"}, "stabilize_B": {"base_candidate": "B"},
    "stabilize_C": {"base_candidate": "C"},
}

result = {"models": {}, "decoders": {}, "functions": {}}
for arm, extra in ARMS.items():
    candidate = arm.split("_")[0]
    result["models"][arm] = model_digest(config(candidate=candidate, **extra))

# Decoders on a synthetic fold: progress with transition_prior, stabilize with egtp off.
rng = np.random.default_rng(3)
data = {"train": [], "val": []}
for name in ["01", "02", "03"]:
    y = np.repeat(np.arange(9), 10)[:90]
    data["train"].append((name, rng.normal(size=(90, 8)).astype(np.float32), y))
logits = torch.from_numpy(rng.normal(size=(9, 90)).astype(np.float32))
info = {"boundary": np.r_[1, np.zeros(44, int), 1, np.zeros(44, int)]}
try:
    rules = tower.decoders(config(candidate="progress", transition_prior=True), data, 9)
except Exception as exc:  # noqa: BLE001 - recorded, not hidden
    rules = None
    result["decoders"]["progress_error"] = repr(exc)
if rules is not None:
    result["decoders"]["progress_keys"] = sorted(rules)
    result["decoders"]["progress"] = digest(np.asarray(rules[""](logits, info)))
for base in "ABC":
    rules = tower.decoders(config(candidate="stabilize", base_candidate=base), data, 9)
    result["decoders"][f"stabilize_{base}_keys"] = sorted(rules)

# Source of every top-level definition except egtp.
source = (ROOT / "scripts/stage1_ptower.py").read_text(encoding="utf-8")
result["other_statements"] = []
for node in ast.parse(source).body:
    name = getattr(node, "name", None)
    if name == "egtp":
        continue
    h = hashlib.sha256(ast.dump(node).encode()).hexdigest()
    if name:
        result["functions"][name] = h
    else:
        result["other_statements"].append(h)

Path(sys.argv[1]).write_text(json.dumps(result, indent=1, ensure_ascii=False))
print(json.dumps({k: (v if k != "functions" else len(v)) for k, v in result.items()}, indent=1))

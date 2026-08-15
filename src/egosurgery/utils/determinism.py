"""Opt-in bitwise determinism for training runs.

Same seed, same config, same host must give the same result. Measured before
this module existed, re-running the same seed moved val accuracy by up to
0.0052 (sigma_rep) -- the same size as the effects under study.

The switch is strictly opt-in (`train.deterministic: true` or a CLI flag);
defaults are untouched so prior runs stay comparable. Enabling it changes
only kernel selection and RNG plumbing, never the training math: no loss,
layer or optimizer change lives here.

``torch.use_deterministic_algorithms(True)`` makes any op that lacks a
deterministic implementation raise instead of silently staying nondeterminate
-- failing loudly is the contract's requirement 4.
"""

from __future__ import annotations

import os
import random

import numpy as np
import torch

# cuBLAS reads this at handle creation; it must be in the environment before
# the first CUDA matmul. ":4096:8" is the documented reproducible workspace.
_CUBLAS_KEY = "CUBLAS_WORKSPACE_CONFIG"
_CUBLAS_VALUE = ":4096:8"


def enable_determinism(seed: int) -> dict:
    """Turn on every determinism control this stack needs; return a record.

    The returned dict is meant to be embedded in the run's result JSON so a
    record remains of the run having been deterministic (requirement 3).
    Call before the first CUDA operation of the process.
    """
    os.environ.setdefault(_CUBLAS_KEY, _CUBLAS_VALUE)

    random.seed(seed)
    np.random.seed(seed)
    # Seeds CPU and every CUDA device generator in torch >= 1.8.
    torch.manual_seed(seed)

    # Raise on ops without a deterministic implementation. Never warn-only:
    # silently staying nondeterministic would defeat the measurement.
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    return {
        "deterministic": True,
        "seed": seed,
        "cublas_workspace_config": os.environ[_CUBLAS_KEY],
        "torch_use_deterministic_algorithms": True,
        "cudnn_deterministic": True,
        "cudnn_benchmark": False,
    }

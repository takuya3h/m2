"""Stage 1 P*-20: the third round's confirmed recipe with videos 17-21 added to train.

Fine-tuning, feature extraction and temporal-head training are the third round's
functions, called unchanged. The only difference is the fold table: with
``data_setting=P20`` every fold's train gains the extra videos, while val and test
stay exactly as in ``docs/stage0/A1_fold_table.md``. ``data_setting=P15`` runs the
third round as it was (the host-difference control).
"""
from __future__ import annotations

import sys
from pathlib import Path

import hydra
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402

EXTRA_TRAIN = ("17", "18", "19", "20", "21")
_canonical_folds = base.folds


def folds_p20():
    """The canonical table with the extra videos appended to every fold's train."""
    table = _canonical_folds()
    for split in table.values():
        split["train"] = split["train"] + list(EXTRA_TRAIN)
    return table


@hydra.main(version_base=None, config_path="../configs", config_name="stage1_ptower_20")
def main(cfg):
    if cfg.data_setting == "P20":
        base.folds = folds_p20
    elif cfg.data_setting != "P15":
        raise ValueError(cfg.data_setting)
    base.deterministic(cfg.seed)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required by task")
    if cfg.action == "finetune":
        r3.finetune(cfg)
    elif cfg.action == "extract":
        r3.extract(cfg)
    elif cfg.action == "train":
        base.train(cfg)
    else:
        raise ValueError(cfg.action)


if __name__ == "__main__":
    main()

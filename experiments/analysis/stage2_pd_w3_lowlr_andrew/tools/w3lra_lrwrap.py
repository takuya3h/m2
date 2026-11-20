"""train_t1b.py を同じ引数で走らせ、optimizer の各群の学習率を記録する包み（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew、Task B-3・C-1）。

train_t1b.py・third_party の param_dict は変えない。読み込んだ後の関数を、元を呼んでから記録するものに差し替えるだけで、
学習の計算（群・学習率・順伝播・更新）は元のまま。記録は環境変数 W3LRA_LR_LOG の json に書く:
  - groups: param_dict.finetune_t1b が返した群の順の名前（other は空なら無い）・学習率・weight decay・テンソルの数・要素数・名前
  - snapshots: optimizer を作った直後（init）、各評価の直前（eval_<k>。k=0 は学習前、1 以降は各 epoch の学習の後）、
    最初の更新の後（after_step_1）の、各群の学習率と更新の回数
--fixed-epochs では train_t1b.py は scheduler を作らない（sched = None）ので、学習率は全 epoch で一定のはずであり、記録で確かめる。

    W3LRA_LR_LOG=<json> python w3lra_lrwrap.py <train_t1b.py の引数>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJ / "scripts"))
import torch  # noqa: E402
import train_t1b as t1b  # noqa: E402  (import 時に cwd を third_party/Relation-DETR へ移す)
from optimizer import param_dict  # noqa: E402

OUT = Path(os.environ["W3LRA_LR_LOG"])
LABELS = ["other", "backbone", "backbone_norm", "linear_projection", "linear_projection_norm", "other_norm", "phase"]
STATE: dict = {"groups": None, "snapshots": [], "steps": 0, "n_eval": 0, "opt": None}


def _dump():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"argv": sys.argv[1:], "groups": STATE["groups"], "snapshots": STATE["snapshots"]},
                              ensure_ascii=False, indent=1))


def _snap(tag: str):
    opt = STATE["opt"]
    if opt is None:
        return
    STATE["snapshots"].append({"tag": tag, "opt_steps": STATE["steps"],
                               "lr": [g["lr"] for g in opt.param_groups],
                               "weight_decay": [g["weight_decay"] for g in opt.param_groups]})
    _dump()


_orig_groups = param_dict.finetune_t1b


def finetune_t1b_logged(model, lr, film_lr=5e-4):
    groups = _orig_groups(model, lr=lr, film_lr=film_lr)
    labels = LABELS if len(groups) == len(LABELS) else LABELS[1:]
    id2name = {id(p): n for n, p in model.named_parameters()}
    STATE["groups"] = [{"label": lab, "lr_given": g.get("lr", lr), "weight_decay_given": g.get("weight_decay"),
                        "n_tensors": len(g["params"]), "n_elements": int(sum(p.numel() for p in g["params"])),
                        "names": [id2name[id(p)] for p in g["params"]]} for lab, g in zip(labels, groups)]
    STATE["args"] = {"lr": lr, "film_lr": film_lr}
    return groups


param_dict.finetune_t1b = finetune_t1b_logged


class AdamWLogged(torch.optim.AdamW):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        STATE["opt"] = self
        _snap("init")

    def step(self, closure=None):
        out = super().step(closure)
        STATE["steps"] += 1
        if STATE["steps"] == 1:
            _snap("after_step_1")
        return out


torch.optim.AdamW = AdamWLogged

_orig_eval = t1b.eval_detection


def eval_detection_logged(*a, **k):
    _snap(f"eval_{STATE['n_eval']}")
    STATE["n_eval"] += 1
    return _orig_eval(*a, **k)


t1b.eval_detection = eval_detection_logged

if __name__ == "__main__":
    t1b.main()

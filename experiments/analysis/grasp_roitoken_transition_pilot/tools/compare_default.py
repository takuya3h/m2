"""起点の版と変更後の版の dp_train.py の出力を突き合わせる（非公式 T-2026-11-09-grasp-roitoken-transition-pilot、Task D-1 の既定の挙動。T-2026-11-06-grasp-pilot-arms の compare_default.py の写し（中身は同じ））。

identity の JSON、試走の run の metrics.json・config.yaml・history.json・per_class_ap.json・notes.md・val の確率・界面の重み
を比べる。違ってよい項目は経過時間と、run の名前を含む経路だけ（``ALLOWED``）。陽性対照として、新しい版の metrics の
値を一つ変えた写しで不一致になることも返す。

    .venv/bin/python compare_default.py <dp_default の置き場> <old の run> <new の run> --out <json>
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import torch
import yaml

ALLOWED = {"elapsed_seconds", "iface_ckpt", "iface_ckpt_sha256"}


def diff(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k in ALLOWED:
                continue
            if k not in a or k not in b:
                out.append(f"{path}/{k} missing")
            else:
                out += diff(a[k], b[k], f"{path}/{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path} len {len(a)} != {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out += diff(x, y, f"{path}[{i}]")
    elif a != b:
        out.append(f"{path}: {str(a)[:80]} != {str(b)[:80]}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("old_runs", nargs="+")
    ap.add_argument("--new-runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = Path(a.dir)
    res = {"identity": {}, "train": {}}
    for t in ("GA", "D1-L1"):
        o = json.loads((d / f"identity_{t}_old.json").read_text())
        n = json.loads((d / f"identity_{t}_new.json").read_text())
        res["identity"][t] = diff(o, n)
    for ro, rn in zip(a.old_runs, a.new_runs):
        ro, rn = Path(ro), Path(rn)
        r = {}
        for f in ("metrics.json", "logs/history.json", "per_class_ap.json"):
            r[f] = diff(json.loads((ro / f).read_text()), json.loads((rn / f).read_text()))
        r["config.yaml"] = diff(yaml.safe_load((ro / "config.yaml").read_text()), yaml.safe_load((rn / "config.yaml").read_text()))
        r["notes.md"] = [] if (ro / "notes.md").read_text() == (rn / "notes.md").read_text() else ["text differs"]
        po, pn = np.load(ro / "predictions/val_probs_best.npz"), np.load(rn / "predictions/val_probs_best.npz")
        r["val_probs"] = [k for k in sorted(set(po) | set(pn)) if k not in po or k not in pn or not np.array_equal(po[k], pn[k])]
        mo, mn = json.loads((ro / "metrics.json").read_text()), json.loads((rn / "metrics.json").read_text())
        so, sn = torch.load(mo["iface_ckpt"], map_location="cpu"), torch.load(mn["iface_ckpt"], map_location="cpu")
        r["iface_ckpt_keys"] = sorted(so) == sorted(sn)
        r["iface_tensors_equal"] = all(torch.equal(so["iface"][k], sn["iface"][k]) for k in so["iface"])
        bad = copy.deepcopy(mn)
        bad["phase_jaccard"] = bad["phase_jaccard"] + 1e-9
        r["positive_control_detects"] = bool(diff(mo, bad))
        r["equal"] = not any(v for k, v in r.items() if isinstance(v, list)) and r["iface_ckpt_keys"] and r["iface_tensors_equal"]
        res["train"][f"{ro.name} vs {rn.name}"] = r
    res["all_equal"] = (not any(res["identity"].values())) and all(v["equal"] for v in res["train"].values())
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False)[:3000])
    sys.exit(0)


if __name__ == "__main__":
    main()

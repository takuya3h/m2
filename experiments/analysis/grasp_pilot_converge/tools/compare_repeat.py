"""前の予備の run と、本契約の版で同じ命令（契約の識別子と名前の接頭辞だけ違う）を回し直した run を突き合わせる
（T-2026-11-09-grasp-pilot-converge、Task B-4。--fixed-epochs の経路の RT・TW が変わらないことの確かめ）。

metrics.json（経過時間と界面の重みの置き場を除く）・logs/history.json・per_class_ap.json・val の確率・界面の重みの全テンソルが
一致することを求める。config.yaml は違う項目の経路を一覧に出す（契約の識別子の欄だけが違うはず）。
陽性対照: 回し直した run の metrics の Jaccard を 1e-9 ずらした写しで不一致になる。

    .venv/bin/python compare_repeat.py <前の run> <回し直した run> [...] --out <json>
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

sys.path.insert(0, str(Path(__file__).parent))
from compare_default import diff  # noqa: E402

SKIP = {"elapsed_seconds", "iface_ckpt", "iface_ckpt_sha256"}


def strip(d):
    return {k: v for k, v in d.items() if k not in SKIP}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {}
    for ro, rn in zip(a.pairs[0::2], a.pairs[1::2]):
        ro, rn = Path(ro), Path(rn)
        mo, mn = json.loads((ro / "metrics.json").read_text()), json.loads((rn / "metrics.json").read_text())
        r = {"metrics.json": diff(strip(mo), strip(mn)),
             "logs/history.json": diff(json.loads((ro / "logs/history.json").read_text()), json.loads((rn / "logs/history.json").read_text())),
             "per_class_ap.json": diff(json.loads((ro / "per_class_ap.json").read_text()), json.loads((rn / "per_class_ap.json").read_text())),
             "config_diff_paths": diff(yaml.safe_load((ro / "config.yaml").read_text()), yaml.safe_load((rn / "config.yaml").read_text()))}
        po, pn = np.load(ro / "predictions/val_probs_best.npz"), np.load(rn / "predictions/val_probs_best.npz")
        r["val_probs"] = [k for k in sorted(set(po) | set(pn)) if k not in po or k not in pn or not np.array_equal(po[k], pn[k])]
        so, sn = torch.load(mo["iface_ckpt"], map_location="cpu"), torch.load(mn["iface_ckpt"], map_location="cpu")
        r["iface_tensors_equal"] = sorted(so["iface"]) == sorted(sn["iface"]) and all(torch.equal(so["iface"][k], sn["iface"][k]) for k in so["iface"])
        if "receiver" in so:
            r["receiver_tensors_equal"] = all(torch.equal(so["receiver"][k], sn["receiver"][k]) for k in so["receiver"])
        bad = copy.deepcopy(strip(mn))
        bad["phase_jaccard"] += 1e-9
        r["positive_control_detects"] = bool(diff(strip(mo), bad))
        r["equal"] = (not r["metrics.json"] and not r["logs/history.json"] and not r["per_class_ap.json"] and not r["val_probs"]
                      and r["iface_tensors_equal"] and r.get("receiver_tensors_equal", True))
        res[f"{ro.name} vs {rn.name}"] = r
    out = {"pairs": res, "all_equal": all(v["equal"] for v in res.values())}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(out, ensure_ascii=False)[:3000])


if __name__ == "__main__":
    main()

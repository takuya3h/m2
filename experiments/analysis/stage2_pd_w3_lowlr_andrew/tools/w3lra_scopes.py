"""Task B-4: 学ぶパラメータの名前の集合を型ごとに、前回の W3 の集合と比べる（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew）。

本契約の集合は恒等性の検査（tools/w3lra_identity.py。学習の経路と同じ train_t1b.set_trainable の後の requires_grad）の
identity/<型>_W3_<腕>.json の trainable_set.names。さらに数歩の写し（$S/smoke/*/lr_groups.json）の optimizer の群に入った名前の和集合とも比べる。
前回の集合:
  - P1・P2L・P3: bengio の experiments/analysis/stage2_w23_bengio/taskC/pd_scopes.json（P2L・P3）・pd_scopes_P1.json（P1）の W3 の names
  - P1・DX: andrew の experiments/analysis/stage2_w23_andrew/identity/<型>_W3_<腕>.json の trainable_set.names
陽性対照: 本契約の集合に定義の外の名前を 1 個足すと一致が外れる。

    python w3lra_scopes.py --out <json>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

M = Path(__file__).resolve().parents[4]
A = M / "experiments/analysis/stage2_pd_w3_lowlr_andrew"
S = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-stage2-pd-w3-lowlr-andrew")
B = M / "experiments/analysis/stage2_w23_bengio/taskC"
AW = M / "experiments/analysis/stage2_w23_andrew/identity"
ARMS = ("empty", "pred_noCF", "gt", "shuffle")


def prev_sets(typ: str) -> dict[str, list[str]]:
    out = {}
    if typ in ("P2L", "P3"):
        out["bengio_pd_scopes"] = json.loads((B / "pd_scopes.json").read_text())["types"][typ]["W3"]["names"]
    if typ == "P1":
        out["bengio_pd_scopes_P1"] = json.loads((B / "pd_scopes_P1.json").read_text())["types"]["P1"]["W3"]["names"]
    if typ in ("P1", "DX"):
        for arm in ARMS:
            out[f"andrew_identity_{arm}"] = json.loads((AW / f"{typ}_W3_{arm}.json").read_text())["trainable_set"]["names"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {"task_id": "T-2026-11-09-stage2-pd-w3-lowlr-andrew", "types": {}}
    for typ in ("P1", "P2L", "P3", "DX"):
        now = {arm: sorted(json.loads((A / f"identity/{typ}_W3_{arm}.json").read_text())["trainable_set"]["names"]) for arm in ARMS}
        same_across_arms = len({tuple(v) for v in now.values()}) == 1
        cur = now["gt"]
        smoke = S / f"smoke/w3lra_pd_{typ}_W3_gt_ep4_seed42_smoke/lr_groups.json"
        opt_names = sorted(n for g in json.loads(smoke.read_text())["groups"] for n in g["names"])
        prev = {k: sorted(v) for k, v in prev_sets(typ).items()}
        extra = "__one_name_outside__"
        res["types"][typ] = {
            "n_names": len(cur), "same_across_arms": same_across_arms,
            "equals_optimizer_groups": cur == opt_names,
            "prev": {k: {"n_names": len(v), "equal": cur == v, "only_now": sorted(set(cur) - set(v))[:5],
                         "only_prev": sorted(set(v) - set(cur))[:5]} for k, v in prev.items()},
            "control_one_added_equal": {k: sorted(set(cur) | {extra}) == v for k, v in prev.items()},
        }
    res["all_equal"] = all(r["same_across_arms"] and r["equals_optimizer_groups"] and all(p["equal"] for p in r["prev"].values())
                           for r in res["types"].values())
    res["control_all_unequal"] = all(not x for r in res["types"].values() for x in r["control_one_added_equal"].values())
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for t, r in res["types"].items():
        print(t, r["n_names"], "arms_same", r["same_across_arms"], "opt", r["equals_optimizer_groups"],
              {k: (p["n_names"], p["equal"]) for k, p in r["prev"].items()})
    print({"all_equal": res["all_equal"], "control_all_unequal": res["control_all_unequal"]})


if __name__ == "__main__":
    main()

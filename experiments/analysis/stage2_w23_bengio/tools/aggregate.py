"""W2・W3 の run の集計（非公式 T-2026-11-01-stage2-w23-bengio、Task D-2・E、SPEC §6）。

各 run の記録（metrics.json・per_class_ap.json・logs/history.json・server.txt、PD は w23_metrics.json）だけから表を作る。
差はすべて 1 本ずつの差（seed は一つ）。読み方の規則（SPEC §6.2）の語は使わない。

- Δ空 = 腕 − 同じ型・同じ W の空の腕、Δ入替 = 腕 − 同じ型・同じ W の入れ替えの腕、Δ塔 = 腕 − 塔単独（Task B-2 の再現値）
- W1 の値は W1 の run の記録から読み、ホストの列を付けて参考の表に置く（処置の差として読まない）

    python aggregate.py --part dp|pd|all --out <json> [--md <markdown>]
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PH = ROOT / "experiments/phase1"
TOWER_DP = {"jaccard": 0.7762185528074379, "accuracy": 0.8712871287128713}
TOWER_PD = {"AP": 0.7273450248398429, "target_AP": 0.7950748008550897, "control_AP": 0.6726631817581498,
            "AP50": 0.851807431425236}
DP_TYPES = ("D1-L1", "D1-L2", "D2", "D3-L1", "D3-L2", "LC", "TH", "TH-NG", "GA")
ARMS = ("empty", "pred_noCF", "gt", "pred_CF", "gtpred_CF", "shuffle")
W1_DP = {"stage2fix_dp_*_{t}_{a}_ep4_seed42": ("D1-L1", "D1-L2", "D2", "D3-L1", "D3-L2"),
         "stage2four_dp_*_{t}_{a}_ep4_seed42": ("LC", "TH", "TH-NG"),
         "grasppilot2_dp_*_{t}_{a}_ep4_seed42": ("GA",)}
PD_SETS = (("P2L", "W2"), ("P2L", "W3"), ("P3", "W3"), ("P1", "W3"))
PD_ARMS = ("empty", "pred_noCF", "gt", "shuffle")
# W1・W2 の参考（PD）: 直しの契約の run（P2L・P3 は W1、P1 は W1 と W2。P3 の W1 は --trainable w2、P1-W2 は andrew）
W1_PD = {("P2L", "W1"): "stage2fix_pd_P2L_{a}_ep4_seed42", ("P3", "W1"): "stage2fix_pd_P3_{a}_ep4_seed42",
         ("P1", "W1"): "stage2fix_pd_P1-W1_{a}_ep4_seed42", ("P1", "W2"): "stage2fix_pd_P1-W2_{a}_ep4_seed42"}


def one(pattern):
    hits = [h for h in sorted(glob.glob(str(PH / pattern))) if not h.endswith("_smoke")]
    if len(hits) > 1:
        raise SystemExit(f"run が一つに決まらない: {pattern} → {hits}")
    return Path(hits[0]) if hits else None


def host(d):
    p = d / "server.txt"
    return p.read_text().split()[0] if p.exists() else None


def dp_run(d):
    m = json.loads((d / "metrics.json").read_text())
    return {"run": d.name, "host": host(d), "jaccard": m["phase_jaccard"], "accuracy": m["phase_accuracy"],
            "result_epoch": m.get("result_epoch", m.get("best_epoch")), "per_video": m["per_video"],
            "per_class": json.loads((d / "per_class_ap.json").read_text()),
            "history": ([{k: h[k] for k in ("epoch", "val_jaccard", "val_accuracy") if k in h}
                         | ({"gate": h["gate"]} if "gate" in h else {}) for h in json.loads((d / "logs/history.json").read_text())]
                        if (d / "logs/history.json").exists() else None),
            "init_jaccard": m.get("init_phase_jaccard"), "receiver_unchanged": m.get("receiver_unchanged"),
            "receiver_outside_scope_unchanged": m.get("receiver_outside_scope_unchanged")}


def deltas(rows, key, tower):
    e, s = rows.get("empty"), rows.get("shuffle")
    for r in rows.values():
        r["d_tower"] = r[key] - tower
        r["d_empty"] = r[key] - e[key] if e else None
        r["d_shuffle"] = r[key] - s[key] if s else None


def aggregate_dp():
    out = {}
    for t in DP_TYPES:
        out[t] = {}
        for w in ("W2", "W3"):
            rows = {}
            for a in ARMS:
                d = one(f"w23b_dp_{w}_*_{t}_{a}_ep4_seed42")
                if d:
                    rows[a] = dp_run(d)
            for key in ("jaccard",):
                deltas(rows, key, TOWER_DP[key])
            for r in rows.values():
                r["d_tower_accuracy"] = r["accuracy"] - TOWER_DP["accuracy"]
                e = rows.get("empty")
                r["d_empty_accuracy"] = r["accuracy"] - e["accuracy"] if e else None
                r["d_empty_per_video"] = ({v: r["per_video"][v]["phase_jaccard"] - e["per_video"][v]["phase_jaccard"]
                                           for v in r["per_video"]} if e else None)
            out[t][w] = rows
        rows = {}
        for pat, types in W1_DP.items():
            if t in types:
                for a in ARMS:
                    d = one(pat.format(t=t, a=a))
                    if d:
                        rows[a] = dp_run(d)
        deltas(rows, "jaccard", TOWER_DP["jaccard"])
        out[t]["W1"] = rows
    return out


def pd_run(d, metrics_file):
    m = json.loads((d / metrics_file).read_text())
    return {"run": d.name, "host": host(d), "AP": m["AP"], "target_AP": m["target_AP"], "control_AP": m["control_AP"],
            "AP50": m["AP50"], "per_video": m["per_video_AP"], "per_class": m["per_class_ap"],
            "per_epoch_mAP": m.get("per_epoch_mAP"), "init": m.get("init"), "result_epoch": m.get("result_epoch"),
            "init_vs_tower_alone": m.get("init_vs_tower_alone"), "frozen_unchanged": m.get("frozen_unchanged")}


def aggregate_pd():
    out = {}
    for t, w in PD_SETS:
        rows = {}
        for a in PD_ARMS:
            d = PH / f"w23b_pd_{t}-{w}_{a}_ep4_seed42"
            if (d / "w23_metrics.json").exists():
                rows[a] = pd_run(d, "w23_metrics.json")
        for key in ("AP", "target_AP", "control_AP", "AP50"):
            for r in rows.values():
                e, s = rows.get("empty"), rows.get("shuffle")
                r[f"d_tower_{key}"] = r[key] - TOWER_PD[key] if r[key] is not None else None
                r[f"d_empty_{key}"] = r[key] - e[key] if e and r[key] is not None else None
                r[f"d_shuffle_{key}"] = r[key] - s[key] if s and r[key] is not None else None
        out.setdefault(t, {})[w] = rows
    for (t, w), pat in W1_PD.items():
        rows = {}
        for a in ARMS:
            d = PH / pat.format(a=a)
            if (d / "stage2fix_metrics.json").exists():
                rows[a] = pd_run(d, "stage2fix_metrics.json")
        out.setdefault(t, {})[f"{w}_ref"] = rows
    return out


def f(x, n=4, sign=False):
    if x is None:
        return "—"
    return f"{x:+.{n}f}" if sign else f"{x:.{n}f}"


def md_dp(dp):
    lines = ["| 型 | W | 腕 | Jaccard | accuracy | Δ空 | Δ入替 | Δ塔 | 09 Δ空 | 10 Δ空 | W1 の Jaccard（ホスト） | W1 の Δ空 |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for t, by in dp.items():
        for w in ("W2", "W3"):
            for a, r in by[w].items():
                w1 = by["W1"].get(a)
                pv = r["d_empty_per_video"] or {}
                lines.append(f"| {t} | {w} | {a} | {f(r['jaccard'])} | {f(r['accuracy'])} | {f(r['d_empty'], sign=True)} | "
                             f"{f(r['d_shuffle'], sign=True)} | {f(r['d_tower'], sign=True)} | {f(pv.get('09'), sign=True)} | "
                             f"{f(pv.get('10'), sign=True)} | {f(w1['jaccard']) if w1 else '—'}（{w1['host'] if w1 else '—'}） | "
                             f"{f(w1['d_empty'], sign=True) if w1 else '—'} |")
    return "\n".join(lines)


def md_pd(pd):
    lines = ["| 型 | W | 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | AP50 | Δ空 overall | Δ空 標的群 | Δ入替 overall | Δ入替 標的群 | Δ塔 overall | Δ塔 標的群 |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for t, by in pd.items():
        for w, rows in by.items():
            if w.endswith("_ref"):
                continue
            for a, r in rows.items():
                lines.append(f"| {t} | {w} | {a} | {f(r['AP'])} | {f(r['target_AP'])} | {f(r['control_AP'])} | {f(r['AP50'])} | "
                             f"{f(r['d_empty_AP'], sign=True)} | {f(r['d_empty_target_AP'], sign=True)} | "
                             f"{f(r['d_shuffle_AP'], sign=True)} | {f(r['d_shuffle_target_AP'], sign=True)} | "
                             f"{f(r['d_tower_AP'], sign=True)} | {f(r['d_tower_target_AP'], sign=True)} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["dp", "pd", "all"], default="all")
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", default=None)
    a = ap.parse_args()
    res = {"task_id": "T-2026-11-01-stage2-w23-bengio", "tower_dp": TOWER_DP, "tower_pd": TOWER_PD}
    md = []
    if a.part in ("dp", "all"):
        res["dp"] = aggregate_dp()
        hosts = {t: sorted({r["host"] for w in ("W2", "W3") for r in res["dp"][t][w].values()}) for t in DP_TYPES}
        res["dp_hosts"] = hosts
        res["dp_counts"] = {t: {w: len(res["dp"][t][w]) for w in ("W1", "W2", "W3")} for t in DP_TYPES}
        md.append(md_dp(res["dp"]))
    if a.part in ("pd", "all"):
        res["pd"] = aggregate_pd()
        res["pd_hosts"] = {t: sorted({r["host"] for w, rows in by.items() if not w.endswith("_ref") for r in rows.values()})
                           for t, by in res["pd"].items()}
        res["pd_counts"] = {t: {w: len(rows) for w, rows in by.items()} for t, by in res["pd"].items()}
        md.append(md_pd(res["pd"]))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    if a.md:
        Path(a.md).write_text("\n\n".join(md) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k.endswith(("hosts", "counts"))}, ensure_ascii=False))


if __name__ == "__main__":
    main()

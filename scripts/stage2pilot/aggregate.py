"""Task F/G: 腕の集計と §5.2 の読み方の規則による記述（非公式 T-2026-10-18-stage2-pilot-folda）。

本体の .venv で動かす。run を走査して型・腕・seed ごとの値を集め、SPEC §5 の表を作る。

    Δ(型, 腕, s) = 指標(型, 腕, s) − 指標(同じ型の空の腕, s)        同じ seed どうしで対にする
    R(型)        = 空の腕の 3 seed の指標の最大 − 最小
    「seed の幅を超える」= 3 つの Δ が同符号（零を含まない）かつ abs(平均 Δ) > R(型)。それ以外は「幅の内」
    実現率       = 平均 Δ(予測-CF) ÷ 平均 Δ(正解予測-CF)。正解予測-CF が「幅を超える」かつ正のときだけ
    P2F の差     = 指標(P2F, 腕) − 指標(検出塔単独。Task B の値)

    python scripts/stage2pilot/aggregate.py --out-json <json> --out-md <md> [--interim]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

SEEDS = (42, 123, 456)
# 利用者の指示（2026-10-18）で PD の腕は seed 42 だけ。PD では R と規則 2 を出さない
PD_SEEDS = (42,)
PD_TYPES = ("P1-W1", "P1-W2", "P2L", "P3")
DP_TYPES = ("D1-L1", "D1-L2", "D2", "D3-L1", "D3-L2")
A5 = ("pred_noCF", "gt", "pred_CF", "gtpred_CF")
A3 = ("pred_noCF", "pred_CF")
ARMS = {"P1-W1": A5, "P1-W2": A5, "P2L": A5, "P3": A5, "D1-L1": A5, "D1-L2": A3, "D2": A5, "D3-L1": A5, "D3-L2": A3}
NOCF = ("pred_noCF", "gt")
ARM_JA = {"empty": "空", "pred_noCF": "予測-noCF", "gt": "正解", "pred_CF": "予測-CF", "gtpred_CF": "正解予測-CF",
          "pred": "予測", "gt_p2f": "正解"}
PD_METRICS = ("AP", "target_AP", "control_AP")
DP_METRICS = ("phase_jaccard", "phase_accuracy")
TOWER_DET = {"AP": 0.7273450248398429, "target_AP": 0.7950748008550899, "control_AP": 0.6726631817581498}
VAL_ANN = C.DET_ANN_A / "instances_val.json"


def judge(deltas, r):
    """§5.2 規則 2。"""
    d = np.asarray(deltas, float)
    same = bool(np.all(d > 0) or np.all(d < 0))
    return "seed の幅を超える" if same and abs(d.mean()) > r else "幅の内"


def pd_runs():
    out = {}
    for d in sorted((C.ROOT / "experiments/phase1").glob("stage2pilot_pd_*_seed*")):
        m = re.fullmatch(r"stage2pilot_pd_(P1-W1|P1-W2|P2L|P3|P2F)_(\w+?)_seed(\d+)", d.name)
        if not m or not (d / "t1b_result.json").exists():
            continue
        typ, arm, seed = m.group(1), m.group(2), int(m.group(3))
        res = json.loads((d / "t1b_result.json").read_text())
        cache = d / "stage2pilot_metrics.json"
        if cache.exists():
            met = json.loads(cache.read_text())
        else:
            tag = "ctrl" if res.get("zero_ctx") else "inj"
            met = M.summary(VAL_ANN, M.load_results(d / f"predictions/val_{tag}_best.json.gz"))
            met["init"] = M.summary(VAL_ANN, M.load_results(d / f"predictions/val_{tag}_ep-1.json.gz"))["AP"]
            C.write_json(cache, met)
        key = (typ, arm if not (typ == "P2F" and arm == "gt") else "gt_p2f", seed)
        if key in out:
            raise SystemExit(f"同じ型・腕・seed の run が二つある: {key}")
        out[key] = {"run": d.name, "best_epoch": res["best_epoch"], "epochs_run": res.get("epochs_run"),
                    "reached_epoch_cap": res.get("reached_epoch_cap"), "eval_detection_mAP": res["mAP"],
                    "AP": met["AP"], "target_AP": met["target_AP"], "control_AP": met["control_AP"],
                    "per_class_ap": met["per_class_ap"], "per_video": met["per_video_AP"],
                    "frozen_unchanged": res.get("frozen_digest_before") == res.get("frozen_digest_after")}
    return out


def dp_runs():
    out = {}
    for d in sorted((C.ROOT / "experiments/phase1").glob("stage2pilot_dp_*_seed*")):
        cfgp, metp = d / "config.yaml", d / "metrics.json"
        if not (cfgp.exists() and metp.exists()):
            continue
        cfg = yaml.safe_load(cfgp.read_text())
        met = json.loads(metp.read_text())
        if cfg.get("smoke") or "phase_jaccard" not in met:
            continue
        key = (cfg["type"], cfg["arm"], int(cfg["seed"]))
        if key in out:
            raise SystemExit(f"同じ型・腕・seed の run が二つある: {key}")
        out[key] = {"run": d.name, "best_epoch": met["best_epoch"], "epochs_run": met["epochs_run"],
                    "reached_epoch_cap": met["reached_epoch_cap"], "phase_jaccard": met["phase_jaccard"],
                    "phase_accuracy": met["phase_accuracy"], "inst_variant": cfg.get("inst_variant"),
                    "per_video": {v: met["per_video"][v] for v in sorted(met["per_video"])},
                    "negative_control": met.get("negative_control"), "iface_params": met.get("iface_params")}
    return out


def table(runs, typ, metrics, arms, seeds=SEEDS):
    """型ごとの表。揃っていない腕は UNKNOWN（測っていない）。seed が 1 つなら R と読みは UNKNOWN。"""
    t = {"type": typ, "empty": {}, "arms": {}, "seeds": list(seeds)}
    single = len(seeds) == 1
    emp = {s: runs.get((typ, "empty", s)) for s in seeds}
    if not all(emp.values()):
        t["status"] = "UNKNOWN（空の腕が揃っていない）"
        t["empty"] = {s: (e[metrics[0]] if e else None) for s, e in emp.items()}
        return t
    t["empty"] = {m: {s: emp[s][m] for s in seeds} for m in metrics}
    t["R"] = None if single else {m: max(t["empty"][m].values()) - min(t["empty"][m].values()) for m in metrics}
    t["empty_identical_across_seeds"] = None if single else {m: len(set(t["empty"][m].values())) == 1 for m in metrics}
    for arm in arms:
        rs = {s: runs.get((typ, arm, s)) for s in seeds}
        if not all(rs.values()):
            t["arms"][arm] = {"status": "UNKNOWN（seed が揃っていない）",
                              "have": sorted(s for s, r in rs.items() if r)}
            continue
        row = {}
        for m in metrics:
            vals = {s: rs[s][m] for s in seeds}
            deltas = {s: vals[s] - t["empty"][m][s] for s in seeds}
            dv = list(deltas.values())
            row[m] = {"values": vals, "delta": deltas, "mean": float(np.mean(dv)), "min": min(dv), "max": max(dv),
                      "reading": "UNKNOWN（seed 1 つ。幅を測れない）" if single else judge(dv, t["R"][m])}
        videos = sorted(rs[seeds[0]]["per_video"])
        key = "phase_jaccard" if typ.startswith("D") else None
        row["per_video_delta"] = {}
        for v in videos:
            if key:
                row["per_video_delta"][v] = {s: rs[s]["per_video"][v][key] - emp[s]["per_video"][v][key] for s in seeds}
            else:
                row["per_video_delta"][v] = {s: rs[s]["per_video"][v] - emp[s]["per_video"][v] for s in seeds}
        row["runs"] = {s: rs[s]["run"] for s in seeds}
        row["epochs"] = {s: (rs[s]["best_epoch"], rs[s]["epochs_run"], rs[s]["reached_epoch_cap"]) for s in seeds}
        t["arms"][arm] = row
    prim = metrics[0]
    a, b = t["arms"].get("pred_CF", {}), t["arms"].get("gtpred_CF", {})
    if single:
        t["realization_rate"] = "出さない（seed 1 つ。規則 2 を当てられない）"
    elif prim in a and prim in b:
        if b[prim]["reading"] == "seed の幅を超える" and b[prim]["mean"] > 0:
            t["realization_rate"] = a[prim]["mean"] / b[prim]["mean"]
        else:
            t["realization_rate"] = "出さない（正解予測-CF が「幅を超える」かつ正でない）"
    return t


def compare(tables, pairs, metric):
    """§5.2 規則 5。同じ腕の平均 Δ の差と、両型の R の大きい方を超えるか。"""
    out = []
    for x, y in pairs:
        tx, ty = tables.get(x), tables.get(y)
        if not tx or not ty or not tx.get("R") or not ty.get("R"):
            continue
        for arm in set(tx["arms"]) & set(ty["arms"]):
            if metric in tx["arms"][arm] and metric in ty["arms"][arm]:
                diff = tx["arms"][arm][metric]["mean"] - ty["arms"][arm][metric]["mean"]
                bound = max(tx["R"][metric], ty["R"][metric])
                out.append({"pair": f"{x} − {y}", "arm": arm, "metric": metric, "diff_of_mean_delta": diff,
                            "max_R": bound, "exceeds": abs(diff) > bound})
    return out


def fmt(x, nd=4):
    return "—" if x is None else (f"{x:+.{nd}f}" if isinstance(x, float) else str(x))


def render(res, interim):
    w = []
    w.append("# Stage 2 予備測定" + ("（中間記録）" if interim else "") + "\n")
    w.append("**非公式の予備測定（T-2026-10-18-stage2-pilot-folda）。関門の判定と設計の判断に使わない。**"
             "折り A の val（動画 09・10）だけ。区間推定もクラスタの推論もしない。\n")
    w.append(f"生成: `scripts/stage2pilot/aggregate.py`。run 数 PD {res['n_pd_runs']}、DP {res['n_dp_runs']}。"
             "Δ は同じ seed の空の腕との差。R は空の腕の 3 seed の幅。読み方は SPEC §5.2。\n")
    for direction, types, metrics in (("PD（工程から検出）", PD_TYPES, PD_METRICS), ("DP（検出から工程）", DP_TYPES, DP_METRICS)):
        w.append(f"## {direction}\n")
        for typ in types:
            t = res["tables"].get(typ)
            if t is None:
                continue
            w.append(f"### {typ}\n")
            if "status" in t:
                w.append(f"{t.get('status')}\n")
                continue
            sd = t["seeds"]
            hs = " | ".join(f"s{x}" for x in sd)
            he = " | ".join(f"空 s{x}" for x in sd)
            hd = " | ".join(f"Δ s{x}" for x in sd)
            w.append(f"| 指標 | {he} | R |\n|---|" + "---|" * len(sd) + "---|")
            for m in metrics:
                e = t["empty"][m]
                rr = "UNKNOWN（seed 1 つ）" if t["R"] is None else f"{t['R'][m]:.4f}"
                w.append(f"| {m} | " + " | ".join(f"{e[x]:.4f}" for x in sd) + f" | {rr} |")
            if t.get("empty_identical_across_seeds") and all(t["empty_identical_across_seeds"].values()):
                w.append("\n注: この型の空の腕は構造上 3 seed とも塔単独と同値（零の入力・トークン 0 個では界面に勾配が届かない）。"
                         "R = 0 のため、規則 2 の「seed の幅を超える」は 3 つの Δ が同符号であればほぼ自動で付き、"
                         "seed の揺れの目安にならない。")
            w.append("")
            w.append(f"| 腕 | 指標 | {hd} | 平均 | 最小 | 最大 | 読み |\n|---|---|" + "---|" * len(sd) + "---|---|---|---|")
            for arm, row in t["arms"].items():
                if "status" in row:
                    w.append(f"| {ARM_JA[arm]} | — | {row['status']} |" + " |" * (len(sd) + 3))
                    continue
                for m in metrics:
                    r = row[m]
                    d = r["delta"]
                    w.append(f"| {ARM_JA[arm]} | {m} | " + " | ".join(fmt(d[x]) for x in sd)
                             + f" | {fmt(r['mean'])} | {fmt(r['min'])} | {fmt(r['max'])} | {r['reading']} |")
            w.append("")
            w.append("動画ごとの Δ（" + ("macro Jaccard" if typ.startswith("D") else "overall mAP") + "）\n")
            w.append(f"| 腕 | 動画 | {hs} |\n|---|---|" + "---|" * len(sd))
            for arm, row in t["arms"].items():
                for v, dd in row.get("per_video_delta", {}).items():
                    w.append(f"| {ARM_JA[arm]} | {v} | " + " | ".join(fmt(dd[x]) for x in sd) + " |")
            if "realization_rate" in t:
                rr = t["realization_rate"]
                w.append(f"\n実現率: {rr if isinstance(rr, str) else f'{rr:.3f}'}")
            w.append("")
    if res.get("p2f"):
        w.append("### P2F（学習なし。検出塔単独との差）\n")
        w.append("| 腕 | overall mAP | 差 | 標的群 AP | 差 | 陰性対照群 AP | 差 |\n|---|---|---|---|---|---|---|")
        for arm, r in res["p2f"].items():
            w.append(f"| {ARM_JA[arm]} | {r['AP']:.4f} | {fmt(r['AP'] - TOWER_DET['AP'])} | {r['target_AP']:.4f} | "
                     f"{fmt(r['target_AP'] - TOWER_DET['target_AP'])} | {r['control_AP']:.4f} | "
                     f"{fmt(r['control_AP'] - TOWER_DET['control_AP'])} |")
        w.append("")
    if res.get("comparisons"):
        w.append("## 型どうしの比較（同じ腕の平均 Δ の差。優劣は書かない）\n")
        w.append("R が 0 の型（D1-L1、D1-L2、D3-L1、D3-L2）どうしの比較は、幅の判定が働かない。\n")
        w.append("| 組 | 腕 | 指標 | 平均 Δ の差 | 両型の R の大きい方 | 超えるか |\n|---|---|---|---|---|---|")
        for c in res["comparisons"]:
            w.append(f"| {c['pair']} | {ARM_JA[c['arm']]} | {c['metric']} | {fmt(c['diff_of_mean_delta'])} | "
                     f"{c['max_R']:.4f} | {'超える' if c['exceeds'] else '超えない'} |")
        w.append("")
    return "\n".join(w) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--interim", action="store_true", help="交差適合を要しない腕だけを表にする")
    a = ap.parse_args()
    pd_r, dp_r = pd_runs(), dp_runs()
    tables = {}
    for typ in PD_TYPES:
        tables[typ] = table(pd_r, typ, PD_METRICS, NOCF if a.interim else ARMS[typ], PD_SEEDS)
    for typ in DP_TYPES:
        arms = tuple(x for x in ARMS[typ] if x in NOCF) if a.interim else ARMS[typ]
        tables[typ] = table(dp_r, typ, DP_METRICS, arms)
    p2f = {arm: pd_r[("P2F", arm, 42)] for arm in ("pred", "gt_p2f") if ("P2F", arm, 42) in pd_r}
    comps = (compare(tables, [("P1-W1", "P2L"), ("P3", "P1-W2")], "AP")
             + compare(tables, [("P1-W1", "P2L"), ("P3", "P1-W2")], "target_AP")
             + compare(tables, [("D1-L1", "D2"), ("D1-L1", "D3-L1"), ("D2", "D3-L1"), ("D1-L2", "D3-L2")],
                       "phase_jaccard"))
    res = {"task_id": C.TASK_ID, "interim": a.interim, "n_pd_runs": len(pd_r), "n_dp_runs": len(dp_r),
           "tables": tables, "p2f": p2f, "comparisons": comps,
           "pd_runs": {f"{k[0]}/{k[1]}/{k[2]}": v for k, v in pd_r.items()},
           "dp_runs": {f"{k[0]}/{k[1]}/{k[2]}": v for k, v in dp_r.items()}}
    C.write_json(a.out_json, res)
    Path(a.out_md).write_text(render(res, a.interim))
    print(f"PD {len(pd_r)} runs, DP {len(dp_r)} runs -> {a.out_md}")


if __name__ == "__main__":
    main()

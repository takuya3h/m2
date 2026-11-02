"""Task E: W2・W3 の run の集計（非公式 T-2026-11-01-stage2-w23-andrew、SPEC §6・§8）。

各 run の w23a_metrics.json（後処理の記録）から、型と W ごとに 4 epoch 目の値、Δ空（同じ型・同じ W の空の腕との差）、
Δ入替（同じ型・同じ W の入れ替えの腕との差）、Δ塔（塔単独との差）、動画ごとの差、epoch ごとの val を組む。
W1 の値（前の契約の run の記録）と P1 の参考（直しの契約の report.json）を並べた参考の表、§6.3 の予測の照合、
完了判定 e（run の本数とホスト）・f（予測から計算し直した値との一致）・g（通した動画と test の共通）の材料と対照も書く。

    python scripts/w23/w23a_aggregate.py --out <report.json> [--recompute]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
P1DIR = ROOT / "experiments/phase1"
TASK_ID = "T-2026-11-01-stage2-w23-andrew"
TYPES = ("DX", "B")
WS = ("W2", "W3")
ARMS = ("empty", "pred_noCF", "gt", "shuffle")
KEYS = ("AP", "target_AP", "control_AP", "AP50")
REPRO = ROOT / "experiments/analysis/stage2_w23_andrew/repro/dtower_val_seed42.json"
W1_RUN = {"DX": "stage2four_pd_DX_{}_ep4_seed42", "B": "grasppilot2_B_{}_ep4_seed42"}
W1_METRICS = {"DX": "stage2four_metrics.json", "B": "grasppilot_metrics.json"}
FIX_REPORT = ROOT / "experiments/analysis/stage2_pilot_fix/report.json"


def run_name(t, w, a):
    return f"w23a_pd_{t}_{w}_{a}_ep4_seed42"


def wall_seconds(d: Path):
    try:
        s, e = ((d / f).read_text().strip() for f in ("start.txt", "end.txt"))
        f = "%Y-%m-%d %H:%M:%S UTC"
        return (datetime.strptime(e, f) - datetime.strptime(s, f)).total_seconds()
    except FileNotFoundError:
        return None


def server_of(run):
    f = P1DIR / str(run) / "server.txt"
    return f.read_text().strip() if run and f.exists() else None


def diff(a: dict, b: dict, keys=KEYS) -> dict:
    return {k: (a[k] - b[k]) if a.get(k) is not None and b.get(k) is not None else None for k in keys}


def tower() -> dict:
    m = json.loads(REPRO.read_text())["metrics"]
    return {k: m[k] for k in KEYS} | {"per_video_AP": m["per_video_AP"], "per_class_ap": m["per_class_ap"]}


def load_run(t, w, a) -> dict:
    d = P1DIR / run_name(t, w, a)
    f = d / "w23a_metrics.json"
    if not f.exists():
        rc = (d / "exit_code.txt").read_text().strip() if (d / "exit_code.txt").exists() else None
        return {"run": d.name, "measured": False,
                "reason": "作業フォルダが無い" if not d.exists() else f"後処理の記録が無い（exit_code {rc}）"}
    m = json.loads(f.read_text())
    return {"run": d.name, "measured": True, **{k: m[k] for k in KEYS}, "per_video_AP": m["per_video_AP"],
            "per_class_ap": m["per_class_ap"], "per_epoch": m["per_epoch"], "gates_last": m["gates_by_epoch"].get("3"),
            "receiver_rel_delta": m["receiver_motion"]["receiver_rel_delta"],
            "receiver_delta_l2": m["receiver_motion"]["receiver_delta_l2"],
            "init_diff_vs_tower": m["init_diff_vs_tower"], "frozen_unchanged": m["frozen_unchanged"],
            "total_trainable": m["total_trainable"], "videos": m["videos"], "server": m["server"],
            "wall_seconds": wall_seconds(d), "result_epoch": m["result_epoch"]}


def load_w1(t, a) -> dict:
    d = P1DIR / W1_RUN[t].format(a)
    m = json.loads((d / W1_METRICS[t]).read_text())
    return {"run": d.name, **{k: m[k] for k in KEYS}, "per_video_AP": m["per_video_AP"],
            "server": (d / "server.txt").read_text().strip(), "result_epoch": m["result_epoch"]}


def add_deltas(rows: dict, tw: dict) -> None:
    e, s = rows.get("empty", {}), rows.get("shuffle", {})
    for r in rows.values():
        if not r.get("measured", True):
            continue
        r["d_empty"] = diff(r, e) if e.get("measured", True) and "AP" in e else None
        r["d_shuffle"] = diff(r, s) if s.get("measured", True) and "AP" in s else None
        r["d_tower"] = diff(r, tw)
        pv = r["per_video_AP"]
        r["per_video_d"] = {
            "empty": {v: pv[v] - e["per_video_AP"][v] for v in pv} if "per_video_AP" in e else None,
            "shuffle": {v: pv[v] - s["per_video_AP"][v] for v in pv} if "per_video_AP" in s else None,
            "tower": {v: pv[v] - tw["per_video_AP"][v] for v in pv}}


def recompute(t, w, a) -> dict:
    """完了判定 f: 予測（4 epoch 目の状態）から集計し直した値と、後処理の記録の値の差。"""
    d = P1DIR / run_name(t, w, a)
    ids = json.loads((d / "logs/eval_meta_val.json").read_text())["image_ids"]
    tag = "ctrl" if json.loads((d / "t1b_result.json").read_text()).get("zero_ctx") else "inj"
    m = M.summary(C.DET_ANN_A / "instances_val.json", M.load_results(d / f"predictions/val_{tag}_best.json.gz"), ids)
    rec = json.loads((d / "w23a_metrics.json").read_text())
    return {k: m[k] - rec[k] for k in KEYS} | {"per_video": {v: m["per_video_AP"][v] - rec["per_video_AP"][v] for v in m["per_video_AP"]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--recompute", action="store_true")
    a = ap.parse_args()
    tw = tower()
    res = {"task_id": TASK_ID, "unofficial": True, "tower": tw, "tables": {}, "w1": {}}
    for t in TYPES:
        w1 = {arm: load_w1(t, arm) for arm in ARMS}
        add_deltas(w1, tw)
        res["w1"][t] = w1
        for w in WS:
            rows = {arm: load_run(t, w, arm) for arm in ARMS}
            add_deltas(rows, tw)
            res["tables"][f"{t}-{w}"] = rows
    # P1 の参考（直しの契約の report.json の P1-W1・P1-W2。本契約では回さない。利用者の指示 2026-11-02）
    fix = json.loads(FIX_REPORT.read_text())["tables"]
    res["p1_reference"] = {typ: {arm: {"value": fix[typ]["rows"][arm]["value"], "delta_empty": fix[typ]["rows"][arm].get("delta_empty"),
                                       "source": fix[typ]["rows"][arm]["source"], "run": fix[typ]["rows"][arm].get("run"),
                                       "server": server_of(fix[typ]["rows"][arm].get("run"))}
                                 for arm in ARMS if arm in fix[typ]["rows"]} for typ in ("P1-W1", "P1-W2")}
    # §6.3 の予測（記述のための事前の記録）
    pred1 = {}
    for t in TYPES:
        g1 = res["w1"][t]["gt"]["d_empty"]["AP"]
        g3 = (res["tables"][f"{t}-W3"]["gt"].get("d_empty") or {}).get("AP")
        pred1[t] = {"gt_d_empty_AP_W1": g1, "gt_d_empty_AP_W3": g3, "W3_gt_W1": None if g3 is None else g3 > g1,
                    "direction": "工程から検出" if t == "DX" else "把持から検出（予測 1 の対象外。参考）"}
    pred2 = {t: (res["tables"][f"{t}-W3"]["empty"].get("d_tower") or {}).get("AP") for t in TYPES}
    res["predictions"] = {
        "1": {"text": "工程から検出の正解の腕の Δ空（overall mAP）は、型ごとに W3 が W1 より大きい型が過半を占める", "by_type": pred1,
              "scope_note": "本契約の工程から検出の型は decoder-xattn だけ（P1 は bengio の契約。利用者の指示 2026-11-02）"},
        "2": {"text": "W3 の空の腕の Δ塔（overall mAP）は負である", "by_type": pred2,
              "holds": {t: (None if v is None else v < 0) for t, v in pred2.items()}}}
    # 完了判定 e: run の本数と、型ごとのホストの集合（対照: 存在しない run の名前を数えると 0 件）
    runs = [r for tab in res["tables"].values() for r in tab.values()]
    res["acceptance_e"] = {"expected": len(TYPES) * len(WS) * len(ARMS), "measured": sum(r["measured"] for r in runs),
                           "hosts_by_type": {t: sorted({r["server"] for k, tab in res["tables"].items() if k.startswith(t + "-")
                                                        for r in tab.values() if r["measured"]}) for t in TYPES},
                           "unmeasured": [{"run": r["run"], "reason": r["reason"]} for r in runs if not r["measured"]],
                           "control_nonexistent_name_count": sum(1 for _ in P1DIR.glob("w23a_pd_ZZ_W9_none_ep4_seed42"))}
    # 完了判定 g: 学習と評価に通した動画と test の共通（対照: 04 を混ぜた集合で共通が 1 件）
    used = sorted({v for r in runs if r["measured"] for v in r["videos"]["train"] + r["videos"]["val_evaluated"]})
    res["acceptance_g"] = {"videos_used": used, "test": sorted(C.TEST_VIDEOS), "overlap": sorted(set(used) & C.TEST_VIDEOS),
                           "control_overlap_with_04": sorted((set(used) | {"04"}) & C.TEST_VIDEOS)}
    res["identity_in_training"] = {r["run"]: r["init_diff_vs_tower"] for r in runs if r["measured"]}
    if a.recompute:
        rc = {run_name(t, w, arm): recompute(t, w, arm) for t in TYPES for w in WS for arm in ARMS
              if res["tables"][f"{t}-{w}"][arm]["measured"]}
        mx = max((abs(x) for v in rc.values() for k, x in v.items() if k != "per_video" and x is not None), default=None)
        mxv = max((abs(x) for v in rc.values() for x in v["per_video"].values()), default=None)
        res["acceptance_f"] = {"recompute_max_abs_diff": mx, "recompute_per_video_max_abs_diff": mxv, "n": len(rc), "by_run": rc}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False, allow_nan=True))
    print(json.dumps({k: res[k] for k in ("acceptance_e", "acceptance_g", "predictions")} | {"f": res.get("acceptance_f", {}).get("recompute_max_abs_diff")},
                     ensure_ascii=False, default=str)[:3000])


if __name__ == "__main__":
    main()

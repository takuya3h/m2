"""Task D: W3（受け取り手 1e-5）の 16 本の集計（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew、SPEC §6・§8）。

前回の andrew の scripts/w23/w23a_aggregate.py の写し。違うのは型（P1・P2L・P3・DX）、run の名前、参考の表（前回の W3 と W2）だけ。
各 run の w3lra_metrics.json（後処理の記録）から、型ごとに 4 epoch 目の値、Δ空（同じ型の空の腕との差）、Δ入替（入れ替えの腕との差）、
Δ塔（塔単独との差）、動画ごとの差、epoch ごとの val、群の学習率を組む。前回の W3（1e-4）と W2 の同じ量を記録から組んで並べる。
§6.3 の予測の照合と、完了判定 e（run の本数）・f（4 epoch 目の予測から計算し直した値との一致）・g（通した動画と test の共通）の材料と対照も書く。

    PYTHONPATH=src:scripts .venv/bin/python w3lra_aggregate.py --out <report.json> [--recompute]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

P1DIR = ROOT / "experiments/phase1"
A = ROOT / "experiments/analysis/stage2_pd_w3_lowlr_andrew"
TASK_ID = "T-2026-11-09-stage2-pd-w3-lowlr-andrew"
TYPES = ("P1", "P2L", "P3", "DX")
ARMS = ("empty", "pred_noCF", "gt", "shuffle")
KEYS = ("AP", "target_AP", "control_AP", "AP50")
REPRO = A / "repro/dtower_val_seed42.json"
FIX_REPORT = ROOT / "experiments/analysis/stage2_pilot_fix/report.json"


def run_name(t, a):
    return f"w3lra_pd_{t}_W3_{a}_ep4_seed42"


def prev_dir(t, w, a) -> tuple[Path, str]:
    """前回の W2・W3 の run の作業フォルダと後処理の記録の名前（DX は andrew の w23a、ほかは bengio の w23b）。"""
    if t == "DX":
        return P1DIR / f"w23a_pd_DX_{w}_{a}_ep4_seed42", "w23a_metrics.json"
    return P1DIR / f"w23b_pd_{t}-{w}_{a}_ep4_seed42", "w23_metrics.json"


def wall_seconds(d: Path):
    try:
        s, e = ((d / f).read_text().strip() for f in ("start.txt", "end.txt"))
        f = "%Y-%m-%d %H:%M:%S UTC"
        return (datetime.strptime(e, f) - datetime.strptime(s, f)).total_seconds()
    except FileNotFoundError:
        return None


def diff(a: dict, b: dict, keys=KEYS) -> dict:
    return {k: (a[k] - b[k]) if a.get(k) is not None and b.get(k) is not None else None for k in keys}


def tower() -> dict:
    m = json.loads(REPRO.read_text())["metrics"]
    return {k: m[k] for k in KEYS} | {"per_video_AP": m["per_video_AP"], "per_class_ap": m["per_class_ap"]}


def load_run(t, a) -> dict:
    d = P1DIR / run_name(t, a)
    f = d / "w3lra_metrics.json"
    if not f.exists():
        rc = (d / "exit_code.txt").read_text().strip() if (d / "exit_code.txt").exists() else None
        return {"run": d.name, "measured": False,
                "reason": "作業フォルダが無い" if not d.exists() else f"後処理の記録が無い（exit_code {rc}）"}
    m = json.loads(f.read_text())
    return {"run": d.name, "measured": True, **{k: m[k] for k in KEYS}, "per_video_AP": m["per_video_AP"],
            "per_class_ap": m["per_class_ap"], "per_epoch": m["per_epoch"],
            "receiver_rel_delta": m["receiver_motion"]["receiver_rel_delta"],
            "receiver_delta_l2": m["receiver_motion"]["receiver_delta_l2"],
            "init_diff_vs_tower": m["init_diff_vs_tower"], "frozen_unchanged": m["frozen_unchanged"],
            "total_trainable": m["total_trainable"], "videos": m["videos"], "server": m["server"],
            "lr_record": m["lr_record"], "lr_arg": m["lr_arg"], "film_lr_arg": m["film_lr_arg"],
            "wall_seconds": wall_seconds(d), "result_epoch": m["result_epoch"]}


def load_prev(t, w, a) -> dict | None:
    d, name = prev_dir(t, w, a)
    if not (d / name).exists():
        return None
    m = json.loads((d / name).read_text())
    srv = (d / "server.txt").read_text().strip() if (d / "server.txt").exists() else None
    return {"run": d.name, "measured": True, **{k: m.get(k) for k in KEYS}, "per_video_AP": m["per_video_AP"],
            "per_class_ap": m["per_class_ap"], "server": srv, "result_epoch": m["result_epoch"],
            "receiver_rel_delta": (m.get("receiver_motion") or {}).get("receiver_rel_delta"),
            "source": f"{d.name}/{name}"}


def add_deltas(rows: dict, tw: dict) -> None:
    e, s = rows.get("empty") or {}, rows.get("shuffle") or {}
    for r in rows.values():
        if not r or not r.get("measured", True):
            continue
        r["d_empty"] = diff(r, e) if "AP" in e else None
        r["d_shuffle"] = diff(r, s) if "AP" in s else None
        r["d_tower"] = diff(r, tw)
        pv = r.get("per_video_AP")
        if pv:
            r["per_video_d"] = {
                "empty": {v: pv[v] - e["per_video_AP"][v] for v in pv} if e.get("per_video_AP") else None,
                "shuffle": {v: pv[v] - s["per_video_AP"][v] for v in pv} if s.get("per_video_AP") else None,
                "tower": {v: pv[v] - tw["per_video_AP"][v] for v in pv}}


def recompute(t, a) -> dict:
    """完了判定 f: 4 epoch 目（epoch 3）の予測から集計し直した値と、後処理の記録の値の差。"""
    d = P1DIR / run_name(t, a)
    ids = json.loads((d / "logs/eval_meta_val.json").read_text())["image_ids"]
    tag = "ctrl" if json.loads((d / "t1b_result.json").read_text()).get("zero_ctx") else "inj"
    m = M.summary(C.DET_ANN_A / "instances_val.json", M.load_results(d / f"predictions/val_{tag}_ep3.json.gz"), ids)
    rec = json.loads((d / "w3lra_metrics.json").read_text())
    return {k: m[k] - rec[k] for k in KEYS} | {"per_video": {v: m["per_video_AP"][v] - rec["per_video_AP"][v] for v in m["per_video_AP"]}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--recompute", action="store_true")
    a = ap.parse_args()
    tw = tower()
    res = {"task_id": TASK_ID, "unofficial": True, "tower": tw, "tables": {}, "prev_W3": {}, "W2_reference": {}}
    for t in TYPES:
        rows = {arm: load_run(t, arm) for arm in ARMS}
        add_deltas(rows, tw)
        res["tables"][t] = rows
        prev = {arm: load_prev(t, "W3", arm) for arm in ARMS}
        add_deltas(prev, tw)
        res["prev_W3"][t] = prev
        if t in ("P2L", "DX"):
            w2 = {arm: load_prev(t, "W2", arm) for arm in ARMS}
            add_deltas(w2, tw)
            res["W2_reference"][t] = {"source": "前回の W2 の run の記録", "rows": w2}
    # P1 の W2 は直しの契約の report.json（腕のうち予測-noCF・正解は前回の記録の epoch 3、空・入れ替えは回し直し）
    fix = json.loads(FIX_REPORT.read_text())["tables"]["P1-W2"]["rows"]
    w2p1 = {arm: {"measured": True, **{k: fix[arm]["value"][k] for k in ("AP", "target_AP", "control_AP")}, "AP50": None,
                  "per_video_AP": fix[arm].get("per_video"), "run": fix[arm].get("run"),
                  "source": f"stage2_pilot_fix/report.json の {fix[arm].get('run')}（直しの契約の記載: {fix[arm]['source']}）"}
            for arm in ARMS}
    for r in w2p1.values():
        if r["per_video_AP"] is None:
            r.pop("per_video_AP")
    add_deltas(w2p1, tw)
    res["W2_reference"]["P1"] = {"source": "experiments/analysis/stage2_pilot_fix/report.json の tables.P1-W2", "rows": w2p1}
    res["W2_reference"]["P3"] = {"source": "回していない（P3 の W2 は W1 と同じ集合。前回 bengio の REPORT §3.1）", "rows": None}
    # §6.3 の予測（記述のための事前の記録。外れても判定は変わらない）
    p1 = {t: {"now": res["tables"][t]["empty"]["d_tower"]["AP"], "prev": res["prev_W3"][t]["empty"]["d_tower"]["AP"]} for t in TYPES}
    for v in p1.values():
        v["holds"] = abs(v["now"]) < abs(v["prev"])
    g = res["tables"]["P1"]["gt"]["d_empty"]["AP"]
    gp = res["prev_W3"]["P1"]["gt"]["d_empty"]["AP"]
    p3 = {t: {"now": res["tables"][t]["gt"]["d_empty"]["AP"], "prev": res["prev_W3"][t]["gt"]["d_empty"]["AP"]} for t in ("P2L", "P3")}
    for v in p3.values():
        v["holds"] = v["prev"] < 0 <= v["now"]
    res["predictions"] = {
        "1": {"text": "全型で空の腕の Δ塔（overall）の絶対値が前回の W3 より小さい", "by_type": p1,
              "holds": all(v["holds"] for v in p1.values())},
        "2": {"text": "P1 の正解の Δ空（overall）は正で、前回の W3 の値より小さい", "now": g, "prev": gp, "holds": 0 < g < gp},
        "3": {"text": "P2L・P3 の正解の Δ空 の符号は前回の W3 と変わる（負から正か零）", "by_type": p3,
              "holds": all(v["holds"] for v in p3.values())}}
    # 完了判定 e: run の本数（対照: 存在しない run の名前を数えると 0 件）
    runs = [r for tab in res["tables"].values() for r in tab.values()]
    res["acceptance_e"] = {"expected": len(TYPES) * len(ARMS), "measured": sum(r["measured"] for r in runs),
                           "hosts": sorted({r["server"] for r in runs if r["measured"]}),
                           "unmeasured": [{"run": r["run"], "reason": r["reason"]} for r in runs if not r["measured"]],
                           "n_epochs_recorded": sorted({len(r["per_epoch"]) for r in runs if r["measured"]}),
                           "lr_by_epoch_all_constant": all(len({json.dumps(v, sort_keys=True) for v in r["lr_record"]["by_epoch"].values()}) == 1
                                                            for r in runs if r["measured"]),
                           "control_nonexistent_name_count": sum(1 for _ in P1DIR.glob("w3lra_pd_ZZ_W9_none_ep4_seed42"))}
    # 完了判定 g: 学習と評価に通した動画と test の共通（対照: 04 を混ぜた集合で共通が 1 件）
    used = sorted({v for r in runs if r["measured"] for v in r["videos"]["train"] + r["videos"]["val_evaluated"]})
    res["acceptance_g"] = {"videos_used": used, "test": sorted(C.TEST_VIDEOS), "overlap": sorted(set(used) & C.TEST_VIDEOS),
                           "control_overlap_with_04": sorted((set(used) | {"04"}) & C.TEST_VIDEOS)}
    res["identity_in_training"] = {r["run"]: r["init_diff_vs_tower"] for r in runs if r["measured"]}
    if a.recompute:
        rc = {run_name(t, arm): recompute(t, arm) for t in TYPES for arm in ARMS if res["tables"][t][arm]["measured"]}
        mx = max((abs(x) for v in rc.values() for k, x in v.items() if k != "per_video" and x is not None), default=None)
        mxv = max((abs(x) for v in rc.values() for x in v["per_video"].values()), default=None)
        res["acceptance_f"] = {"recompute_max_abs_diff": mx, "recompute_per_video_max_abs_diff": mxv, "n": len(rc), "by_run": rc}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False, allow_nan=True))
    print(json.dumps({k: res[k] for k in ("acceptance_e", "acceptance_g", "predictions")} | {"f": res.get("acceptance_f", {}).get("recompute_max_abs_diff")},
                     ensure_ascii=False, default=str)[:4000])


if __name__ == "__main__":
    main()

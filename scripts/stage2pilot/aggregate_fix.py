"""Task C-3 / D / F: 4 epoch 目の値と入れ替えの腕の集計（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle）。

本体の .venv で動かす。前回（T-2026-10-18-stage2-pilot-folda）の run は読むだけ（前回の aggregate.py の pd_runs / dp_runs を
そのまま使い、要約の控えはすべて在ることを先に確かめる）。書くのは --out-json と --out-md だけ。

4 epoch 目の値（SPEC §3）: 学習を 4 epoch 終えた時点の状態の val の値。最良の回を選ばない。
    PD: epoch は 0 始まりなので epoch 3。前回の run は logs/val_metrics_by_epoch.json の epoch 3 の行（mAP とクラス別 AP）
    DP: epoch は 1 始まりなので epoch 4。前回の run は logs/history.json の epoch 4 の行（Jaccard と accuracy）
    回し直した run（stage2fix_*）は、run の結果そのもの（--fixed-epochs で最後の epoch の状態）
    同じ型・腕に回し直した run があればそれを使い、前回の値は並べて記録する
差（SPEC §5.1）: Δ空 = 値(型, 腕) − 値(同じ型の空の腕)、Δ入替 = 値(型, 腕) − 値(同じ型の入れ替えの腕)、
    Δ前回 = 前回の REPORT の Δ（最良の回。DP は seed 42 の Δ。3 seed の平均を参考に並べる）、選び方による差 = Δ前回 − Δ空
群（conventions#det_groups）: クラス別 AP から det_metrics.read_groups の表で作る（評価集合に出現しないクラスは除く）

    python scripts/stage2pilot/aggregate_fix.py --out-json <json> --out-md <md> [--interim] [--head <md>] [--tail <md>]
    python scripts/stage2pilot/aggregate_fix.py --self-check     4 epoch 目の取り出しの陽性対照（作り物の記録）
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import aggregate as A  # noqa: E402
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

EPOCHS = 4
PD_EPOCH = EPOCHS - 1                      # 0 始まり
DP_EPOCH = EPOCHS                          # 1 始まり
PD_TYPES = A.PD_TYPES
DP_TYPES = A.DP_TYPES
PD_ARMS = ("empty", "pred_noCF", "gt", "pred_CF", "gtpred_CF", "shuffle")
DP_ARMS = {t: ("empty",) + A.ARMS[t] + ("shuffle",) for t in DP_TYPES}
PD_M = ("AP", "target_AP", "control_AP")
DP_M = ("phase_jaccard", "phase_accuracy")
ARM_JA = {**A.ARM_JA, "shuffle": "入れ替え"}
PHASE1 = C.ROOT / "experiments/phase1"
GROUPS = M.read_groups()


# ---------------------------------------------------------------- 4 epoch 目の取り出し（陽性対照の対象）
def epoch4_pd(epochs_eval):
    """val_metrics_by_epoch.json の epochs_eval から epoch 3 の行。無ければ None（最後の行や最良の行で代えない）。"""
    rows = [e for e in epochs_eval if e.get("epoch") == PD_EPOCH]
    return rows[0] if rows else None


def epoch4_dp(history):
    """history.json から epoch 4 の行。無ければ None。"""
    rows = [h for h in history if h.get("epoch") == DP_EPOCH]
    return rows[0] if rows else None


def groups_of(per_class):
    out = {}
    for g, classes in GROUPS.items():
        used = [per_class[c] for c in classes if c in per_class and not math.isnan(per_class[c])]
        out[f"{g}_AP"] = float(np.mean(used)) if used else None
        out[f"{g}_missing"] = [c for c in classes if c not in per_class or math.isnan(per_class[c])]
    return out


def self_check():
    """完了判定 d の陽性対照: 最良が 2 epoch 目の作り物の記録から 4 epoch 目の値が選ばれるか。"""
    fake_pd = [{"epoch": -1, "mAP": 0.70}, {"epoch": 0, "mAP": 0.71}, {"epoch": 1, "mAP": 0.79},
               {"epoch": 2, "mAP": 0.74}, {"epoch": 3, "mAP": 0.72}]
    fake_dp = [{"epoch": 1, "val_jaccard": 0.70}, {"epoch": 2, "val_jaccard": 0.80},
               {"epoch": 3, "val_jaccard": 0.75}, {"epoch": 4, "val_jaccard": 0.72}, {"epoch": 5, "val_jaccard": 0.81}]
    short = [{"epoch": -1, "mAP": 0.70}, {"epoch": 0, "mAP": 0.71}, {"epoch": 1, "mAP": 0.79}, {"epoch": 2, "mAP": 0.74}]
    res = {"pd_best_is_epoch1_picked": epoch4_pd(fake_pd)["mAP"], "pd_expected": 0.72,
           "dp_best_is_epoch2_picked": epoch4_dp(fake_dp)["val_jaccard"], "dp_expected": 0.72,
           "pd_stopped_at_epoch2_picked": epoch4_pd(short), "pd_stopped_expected": None}
    res["pass"] = (res["pd_best_is_epoch1_picked"] == 0.72 and res["dp_best_is_epoch2_picked"] == 0.72
                   and res["pd_stopped_at_epoch2_picked"] is None)
    return res


# ---------------------------------------------------------------- 前回の run
def old_pd():
    """前回の PD 22 本: 最良の回の値（前回の集計と同じ）と 4 epoch 目の値。"""
    for d in PHASE1.glob("stage2pilot_pd_*_seed42"):
        if not (d / "stage2pilot_metrics.json").exists():
            raise SystemExit(f"前回の要約の控えが無い（作ると前回の置き場へ書き込む）: {d.name}")
    best = A.pd_runs()
    out = {}
    for (typ, arm, seed), b in best.items():
        d = PHASE1 / b["run"]
        f = d / "logs/val_metrics_by_epoch.json"
        ep = json.loads(f.read_text())["epochs_eval"] if f.exists() else None
        row = {"run": b["run"], "best": {m: b[m] for m in PD_M}, "best_epoch": b["best_epoch"],
               "best_per_class": b["per_class_ap"], "best_per_video": b["per_video"],
               "epochs_run": b["epochs_run"], "wall_seconds": b["wall_seconds"]}
        if ep is None:
            row["epoch4"] = None
            row["epoch4_reason"] = "logs/val_metrics_by_epoch.json が無い（上限 8 で起動し外から止めた run。cap_result.json は mAP だけ）"
        elif typ == "P2F":
            row["epoch4"] = {**{m: b[m] for m in PD_M}, "per_class": b["per_class_ap"], "per_video": b["per_video"],
                             "source": "学習なし（評価だけ。値は epoch に依らない）"}
        else:
            e = epoch4_pd(ep)
            if e is None or not e.get("per_class_coco_map"):
                row["epoch4"] = None
                row["epoch4_reason"] = (f"epoch {PD_EPOCH} の行が無い（前回の止め方で epoch "
                                        f"{max(x['epoch'] for x in ep)} で止まった）")
            else:
                g = groups_of(e["per_class_coco_map"])
                row["epoch4"] = {"AP": e["mAP"], "target_AP": g["target_AP"], "control_AP": g["control_AP"],
                                 "per_class": e["per_class_coco_map"],
                                 "per_video": b["per_video"] if b["best_epoch"] == PD_EPOCH else None,
                                 "per_video_reason": None if b["best_epoch"] == PD_EPOCH else
                                 f"epoch {PD_EPOCH} の予測と重みが残っていない（前回の最良は epoch {b['best_epoch']}）",
                                 "source": f"前回の記録 val_metrics_by_epoch.json の epoch {PD_EPOCH}"}
            # 読む位置の検査（完了判定 g）: 前回の最良の値 = 学習した epoch の記録の最大
            trained = [x for x in ep if x["epoch"] >= 0]
            mx = max(trained, key=lambda x: (x["mAP"], -x["epoch"]))
            res = json.loads((d / "t1b_result.json").read_text())
            row["read_check"] = {"best_mAP_recorded": res["mAP"], "max_of_epochs": mx["mAP"],
                                 "argmax_epoch": mx["epoch"], "match": res["mAP"] == mx["mAP"]
                                 and res["best_epoch"] == mx["epoch"]}
            bc = next(x for x in ep if x["epoch"] == b["best_epoch"])["per_class_coco_map"]
            row["two_evaluators_max_abs_diff"] = max(abs(bc[k] - b["per_class_ap"][k]) for k in bc)
        if typ != "P2F" and ep is None:
            cap = json.loads((d / "cap_result.json").read_text())
            mx = max(cap["per_epoch_eval"], key=lambda x: (x["mAP"], -x["epoch"]))
            row["read_check"] = {"best_mAP_recorded": cap["mAP"], "max_of_epochs": mx["mAP"], "argmax_epoch": mx["epoch"],
                                 "match": cap["mAP"] == mx["mAP"] and cap["best_epoch"] == mx["epoch"],
                                 "note": "cap_result.json の epoch ごとの mAP（学習ログの 4 桁の表示）"}
        out[(typ, arm)] = row
    return out


def old_dp():
    """前回の DP 63 本: 最良の回の値と 4 epoch 目の値（history.json）。"""
    best = A.dp_runs()
    out = {}
    for (typ, arm, seed), b in best.items():
        hist = json.loads((PHASE1 / b["run"] / "logs/history.json").read_text())
        e = epoch4_dp(hist)
        mx = max(hist, key=lambda h: (h["val_jaccard"], -h["epoch"]))
        out[(typ, arm, seed)] = {
            "run": b["run"], "best": {m: b[m] for m in DP_M}, "best_epoch": b["best_epoch"],
            "best_per_video": b["per_video"], "epochs_run": b["epochs_run"], "history": hist,
            "epoch4": None if e is None else {"phase_jaccard": e["val_jaccard"], "phase_accuracy": e["val_accuracy"],
                                              "source": f"前回の記録 history.json の epoch {DP_EPOCH}"},
            "read_check": {"best_recorded": b["phase_jaccard"], "max_of_epochs": mx["val_jaccard"],
                           "argmax_epoch": mx["epoch"],
                           "match": b["phase_jaccard"] == mx["val_jaccard"] and b["best_epoch"] == mx["epoch"]}}
    return out


# ---------------------------------------------------------------- 本契約の run
def new_pd():
    out = {}
    for d in sorted(PHASE1.glob("stage2fix_pd_*")):
        m = re.fullmatch(rf"stage2fix_pd_(P1-W1|P1-W2|P2L|P3|P2F)_(\w+?)_ep{EPOCHS}_seed42", d.name)
        if not m or not (d / "stage2fix_metrics.json").exists():
            continue                                          # 試走（_smoke）と終わっていない run は入れない
        met = json.loads((d / "stage2fix_metrics.json").read_text())
        res = json.loads((d / "t1b_result.json").read_text())
        if not met["eval_only"] and met["result_selection"] != "final_epoch":
            raise SystemExit(f"結果が最後の epoch の状態ではない: {d.name}")
        out[(m.group(1), m.group(2))] = {
            "run": d.name, "AP": met["AP"], "target_AP": met["target_AP"], "control_AP": met["control_AP"],
            "per_class": met["per_class_ap"], "per_video": met["per_video_AP"], "init_AP": met["init"],
            "result_epoch": met["result_epoch"], "per_epoch_mAP": {int(k): v for k, v in met["per_epoch_mAP"].items()},
            "frozen_unchanged": met["frozen_unchanged"], "wall_seconds": A.wall_seconds(d),
            "trainable": yaml.safe_load((d / "config.yaml").read_text())["stage2pilot"]["total_trainable"],
            "eval_detection_mAP": res["mAP"], "source": "回し直し（本契約。4 epoch 目の状態）" if not met["eval_only"]
            else "評価だけ（本契約）"}
    return out


def new_dp():
    out = {}
    for d in sorted(PHASE1.glob("stage2fix_dp_*_seed42")):
        cfgp, metp = d / "config.yaml", d / "metrics.json"
        if not (cfgp.exists() and metp.exists()):
            continue
        cfg = yaml.safe_load(cfgp.read_text())
        met = json.loads(metp.read_text())
        if cfg.get("smoke") or "phase_jaccard" not in met:
            continue
        if cfg.get("result_selection") != "final_epoch" or met["result_epoch"] != DP_EPOCH:
            raise SystemExit(f"結果が {DP_EPOCH} epoch 目の状態ではない: {d.name}")
        key = (cfg["type"], cfg["arm"])
        if key in out:
            raise SystemExit(f"同じ型・腕の run が二つある: {key}")
        out[key] = {"run": d.name, "phase_jaccard": met["phase_jaccard"], "phase_accuracy": met["phase_accuracy"],
                    "per_class": json.loads((d / "per_class_ap.json").read_text()),
                    "per_video": met["per_video"], "init_jaccard": met["init_phase_jaccard"],
                    "history": json.loads((d / "logs/history.json").read_text()),
                    "wall_seconds": met["elapsed_seconds"], "trainable": met["iface_params"],
                    "negative_control": met.get("negative_control"),
                    "source": "回し直し（本契約。4 epoch 目の状態）"}
    return out


def unwrap_per_class(pc):
    """per_class_ap.json の形（{"per_class_ap": {...}} か素の {...}）をそろえる。"""
    return pc.get("per_class_ap", pc) if isinstance(pc, dict) else pc


# ---------------------------------------------------------------- 表
def pd_table(typ, oldp, newp):
    rows = {}
    for arm in PD_ARMS:
        o, n = oldp.get((typ, arm)), newp.get((typ, arm))
        r = {"arm": arm, "previous_best": o and o["best"], "previous_best_epoch": o and o["best_epoch"],
             "previous_epoch4": o and o["epoch4"] and {m: o["epoch4"][m] for m in PD_M},
             "previous_epoch4_reason": o and o.get("epoch4_reason"), "previous_run": o and o["run"]}
        if n:
            r["value"] = {m: n[m] for m in PD_M}
            r["per_video"], r["per_class"] = n["per_video"], n["per_class"]
            r["source"], r["run"] = n["source"], n["run"]
            r["cost"] = {"trainable": n["trainable"], "wall_seconds": n["wall_seconds"], "epochs": EPOCHS}
        elif o and o["epoch4"]:
            r["value"] = {m: o["epoch4"][m] for m in PD_M}
            r["per_video"] = o["epoch4"].get("per_video")
            r["per_video_reason"] = o["epoch4"].get("per_video_reason")
            r["per_class"] = o["epoch4"]["per_class"]
            r["source"], r["run"] = o["epoch4"]["source"], o["run"]
        else:
            r["value"], r["source"] = None, "UNKNOWN（" + ((o or {}).get("epoch4_reason") or "run が無い") + "）"
        rows[arm] = r
    return finish_table(typ, rows, PD_M, video_key=None)


def dp_table(typ, oldd, newd):
    rows = {}
    for arm in DP_ARMS[typ]:
        o, n = oldd.get((typ, arm, 42)), newd.get((typ, arm))
        r = {"arm": arm, "previous_best": o and o["best"], "previous_best_epoch": o and o["best_epoch"],
             "previous_epoch4": o and o["epoch4"] and {m: o["epoch4"][m] for m in DP_M},
             "previous_run": o and o["run"],
             "reference_seeds": {s: (oldd[(typ, arm, s)]["epoch4"] and {m: oldd[(typ, arm, s)]["epoch4"][m] for m in DP_M})
                                 for s in (123, 456) if (typ, arm, s) in oldd}}
        if n:
            r["value"] = {m: n[m] for m in DP_M}
            r["per_video"] = n["per_video"]
            r["per_class"] = unwrap_per_class(n["per_class"])
            r["source"], r["run"] = n["source"], n["run"]
            r["cost"] = {"trainable": n["trainable"], "wall_seconds": n["wall_seconds"], "epochs": EPOCHS}
            if o:
                r["reproduction"] = repro_dp(o["history"], n["history"])
        else:
            r["value"], r["source"] = None, "UNKNOWN（回し直しの run がまだ無い）"
        rows[arm] = r
    return finish_table(typ, rows, DP_M, video_key="phase_jaccard")


def repro_dp(old_hist, new_hist):
    """回し直しの再現の程度: 前回の同じ run の epoch 1〜4 の記録との差。"""
    o = {h["epoch"]: h for h in old_hist}
    out = {}
    for h in new_hist:
        e = h["epoch"]
        if e in o:
            out[e] = {k: h[k] - o[e][k] for k in ("train_loss", "val_jaccard", "val_accuracy")}
    return {"per_epoch_diff": out, "max_abs_diff": max(abs(v) for d in out.values() for v in d.values()) if out else None}


def finish_table(typ, rows, metrics, video_key):
    emp, shf = rows.get("empty", {}), rows.get("shuffle", {})
    for arm, r in rows.items():
        v = r.get("value")
        r["delta_empty"] = ({m: v[m] - emp["value"][m] for m in metrics} if v and emp.get("value") else None)
        r["delta_shuffle"] = ({m: v[m] - shf["value"][m] for m in metrics} if v and shf.get("value") else None)
        pe, pb = emp.get("previous_best"), r.get("previous_best")
        r["delta_previous"] = ({m: pb[m] - pe[m] for m in metrics} if pb and pe else None)
        r["selection_effect"] = ({m: r["delta_previous"][m] - r["delta_empty"][m] for m in metrics}
                                 if r["delta_previous"] and r["delta_empty"] else None)
        r["per_video_delta"] = {}
        for ref_name, ref in (("empty", emp), ("shuffle", shf)):
            pv, rv = r.get("per_video"), ref.get("per_video")
            if pv and rv:
                r["per_video_delta"][ref_name] = {
                    vid: (pv[vid][video_key] - rv[vid][video_key]) if video_key else (pv[vid] - rv[vid]) for vid in sorted(pv)}
            else:
                why = [x for x in (r.get("per_video_reason"), ref.get("per_video_reason")) if x]
                r["per_video_delta"][ref_name] = "UNKNOWN（" + ("；".join(why) if why else "値が無い") + "）"
        if video_key and r.get("per_class") and emp.get("per_class") and arm != "empty":
            d = {c: r["per_class"][c] - emp["per_class"][c] for c in r["per_class"]}
            r["per_class_delta_empty"] = d
            r["per_class_max"] = max(d, key=d.get)
            r["per_class_min"] = min(d, key=d.get)
    return {"type": typ, "rows": rows}


def p2f_table(oldp, newp):
    out = {"tower": dict(A.TOWER_DET)}
    for name, key, src in (("shuffle", ("P2F", "shuffle"), newp), ("pred", ("P2F", "pred"), oldp),
                           ("gt", ("P2F", "gt_p2f"), oldp)):
        r = src.get(key)
        if r is None:
            out[name] = None
        elif src is newp:
            out[name] = {m: r[m] for m in PD_M} | {"run": r["run"], "per_video": r["per_video"]}
        else:
            out[name] = dict(r["best"]) | {"run": r["run"], "per_video": r["best_per_video"]}
    return out


def recompute_check(tables):
    """完了判定 j: 表の Δ を各 run の metrics.json（PD は stage2fix_metrics.json か前回の記録）から計算し直して一致するか。"""
    bad, n = [], 0
    for typ, t in tables.items():
        rows = t["rows"]
        for arm, r in rows.items():
            if not (r.get("delta_empty") and r.get("run") and rows["empty"].get("run")):
                continue
            metrics = DP_M if typ.startswith("D") else PD_M

            def load(rr, m):
                d = PHASE1 / rr["run"]
                if (d / "stage2fix_metrics.json").exists():
                    return json.loads((d / "stage2fix_metrics.json").read_text())[m]
                if (d / "metrics.json").exists() and typ.startswith("D"):
                    return json.loads((d / "metrics.json").read_text())[m]
                ep = epoch4_pd(json.loads((d / "logs/val_metrics_by_epoch.json").read_text())["epochs_eval"])
                return ep["mAP"] if m == "AP" else groups_of(ep["per_class_coco_map"])[m]
            for m in metrics:
                n += 1
                again = load(r, m) - load(rows["empty"], m)
                if again != r["delta_empty"][m]:
                    bad.append({"type": typ, "arm": arm, "metric": m, "table": r["delta_empty"][m], "again": again})
    return {"checked": n, "mismatch": bad}


def repro_pd(oldp, newp):
    """回し直した PD の run: 学習前の値が塔単独と一致するか、前回の同じ run の epoch ごとの mAP との差。"""
    out = {}
    for (typ, arm), n in newp.items():
        if typ == "P2F":
            continue
        o = oldp.get((typ, arm))
        r = {"init_AP": n["init_AP"], "init_equals_tower": n["init_AP"] == A.TOWER_DET["AP"]}
        if o:
            d = PHASE1 / o["run"]
            f = d / "logs/val_metrics_by_epoch.json"
            if f.exists():
                prev = {e["epoch"]: e["mAP"] for e in json.loads(f.read_text())["epochs_eval"]}
                r["note"] = "前回の val_metrics_by_epoch.json"
            else:
                prev = {e["epoch"]: e["mAP"] for e in json.loads((d / "cap_result.json").read_text())["per_epoch_eval"]}
                r["note"] = "前回の cap_result.json（学習ログの 4 桁の表示）"
            r["per_epoch_diff"] = {e: n["per_epoch_mAP"][e] - prev[e] for e in sorted(prev) if e in n["per_epoch_mAP"]}
        out[f"{typ}/{arm}"] = r
    return out


def check_predictions(tables, p2f):
    """§5.3 の予測との照合（記述のための事前の記録。外れても判定は変わらない）。"""
    def row(typ, arm):
        return tables.get(typ, {}).get("rows", {}).get(arm, {})
    out = []
    for typ in ("P1-W1", "P1-W2"):
        r = row(typ, "gt")
        a, b = (r.get("delta_empty") or {}).get("target_AP"), (r.get("delta_previous") or {}).get("target_AP")
        out.append({"no": 1, "about": f"{typ} 正解の Δ空（標的群 AP）は Δ前回 より小さい",
                    "observed": None if None in (a, b) else f"Δ空 {a:+.4f}、Δ前回 {b:+.4f}",
                    "verdict": "UNKNOWN" if None in (a, b) else ("当たり" if a < b else "外れ")})
    r = row("D1-L1", "pred_noCF")
    a, b = (r.get("delta_shuffle") or {}).get("phase_jaccard"), (r.get("delta_empty") or {}).get("phase_jaccard")
    out.append({"no": 2, "about": "D1-L1 予測-noCF の Δ入替（Jaccard）は Δ空 より小さい",
                "observed": None if None in (a, b) else f"Δ入替 {a:+.4f}、Δ空 {b:+.4f}",
                "verdict": "UNKNOWN" if None in (a, b) else ("当たり" if a < b else "外れ")})
    for typ in ("P1-W1", "P1-W2", "P2L"):
        a = (row(typ, "gt").get("delta_shuffle") or {}).get("target_AP")
        out.append({"no": 3, "about": f"{typ} 正解の Δ入替（標的群 AP）は正", "observed": None if a is None else f"{a:+.4f}",
                    "verdict": "UNKNOWN" if a is None else ("当たり" if a > 0 else "外れ")})
    for typ in ("D1-L2", "D3-L1", "D3-L2"):
        c = row(typ, "pred_noCF").get("per_class_min")
        out.append({"no": 4, "about": f"{typ} 予測-noCF で空の腕との差が最も負のクラスは dressing",
                    "observed": c and f"{c}（{row(typ, 'pred_noCF')['per_class_delta_empty'][c]:+.4f}）",
                    "verdict": "UNKNOWN" if c is None else ("当たり" if c == "dressing" else "外れ")})
    s = p2f.get("shuffle")
    out.append({"no": 5, "about": "P2F の入れ替えの値（標的群 AP）は塔単独より低い",
                "observed": s and f"入れ替え {s['target_AP']:.4f}、塔単独 {A.TOWER_DET['target_AP']:.4f}",
                "verdict": "UNKNOWN" if s is None else ("当たり" if s["target_AP"] < A.TOWER_DET["target_AP"] else "外れ")})
    return out


# ---------------------------------------------------------------- 書き出し
def f4(x, signed=True):
    if x is None:
        return "—"
    return f"{x:+.4f}" if signed else f"{x:.4f}"


def render(res, interim, head=None, tail=None):
    w = ["# Stage 2 予備測定の直し" + ("（中間記録）" if interim else "") + "\n",
         "**非公式の測定（T-2026-10-19-stage2-pilot-fix-epoch4-shuffle）。関門と設計の判断に使わない。**"
         "折り A の val（動画 09・10）、seed 42 だけ。区間推定もクラスタの推論もしない。陽性・陰性・有意の語は使わない。\n"]
    if head:
        w += [head, "## 結果の表\n"]
    w.append("生成: `scripts/stage2pilot/aggregate_fix.py`。値はすべて 4 epoch 目の状態（PD は epoch 3、DP は epoch 4）。"
             "Δ空 は同じ型の空の腕との差、Δ入替 は同じ型の入れ替えの腕との差、Δ前回 は前回の REPORT の Δ（最良の回。DP は seed 42）、"
             "選び方による差 = Δ前回 − Δ空。出所の「回し直し」は本契約の run、「前回の記録」は前回の run の epoch ごとの記録。\n")
    for direction, types, metrics in (("PD（工程から検出）", PD_TYPES, PD_M), ("DP（検出から工程）", DP_TYPES, DP_M)):
        w.append(f"## {direction}\n")
        for typ in types:
            t = res["tables"].get(typ)
            if not t:
                continue
            w.append(f"### {typ}\n")
            w.append("| 腕 | 指標 | 4 epoch 目 | Δ空 | Δ入替 | Δ前回 | 選び方による差 | 前回の最良 | 前回の 4 epoch 目 | 出所 |\n"
                     "|---|---|---|---|---|---|---|---|---|---|")
            for arm, r in t["rows"].items():
                for m in metrics:
                    v = r.get("value")
                    w.append(f"| {ARM_JA[arm]} | {m} | {f4(v and v[m], False)} | {f4((r['delta_empty'] or {}).get(m))} | "
                             f"{f4((r['delta_shuffle'] or {}).get(m))} | {f4((r['delta_previous'] or {}).get(m))} | "
                             f"{f4((r['selection_effect'] or {}).get(m))} | {f4((r['previous_best'] or {}).get(m), False)} | "
                             f"{f4((r['previous_epoch4'] or {}).get(m), False)} | {r['source'] if m == metrics[0] else ''} |")
            w.append("\n動画ごとの Δ（" + ("macro Jaccard" if typ.startswith("D") else "overall mAP") + "）\n")
            w.append("| 腕 | 基準 | 動画 09 | 動画 10 |\n|---|---|---|---|")
            for arm, r in t["rows"].items():
                for ref in ("empty", "shuffle"):
                    if arm == ref:
                        continue
                    d = r["per_video_delta"].get(ref)
                    if isinstance(d, dict):
                        w.append(f"| {ARM_JA[arm]} | {ARM_JA[ref]} | {f4(d.get('09'))} | {f4(d.get('10'))} |")
                    else:
                        w.append(f"| {ARM_JA[arm]} | {ARM_JA[ref]} | {d} | |")
            if typ.startswith("D"):
                w.append("\nクラス別 Jaccard の空の腕との差（最も大きい工程と最も小さい工程）\n")
                w.append("| 腕 | 最大 | 最小 | 全工程 |\n|---|---|---|---|")
                for arm, r in t["rows"].items():
                    if "per_class_delta_empty" in r:
                        d = r["per_class_delta_empty"]
                        w.append(f"| {ARM_JA[arm]} | {r['per_class_max']} {d[r['per_class_max']]:+.4f} | "
                                 f"{r['per_class_min']} {d[r['per_class_min']]:+.4f} | "
                                 + "、".join(f"{c} {x:+.4f}" for c, x in d.items()) + " |")
                w.append("\n参考（読み方の規則に使わない）: seed 123・456 の 4 epoch 目の値（前回の history.json）\n")
                w.append("| 腕 | seed | Jaccard | accuracy |\n|---|---|---|---|")
                for arm, r in t["rows"].items():
                    for s, v in (r.get("reference_seeds") or {}).items():
                        w.append(f"| {ARM_JA[arm]} | {s} | {f4(v and v['phase_jaccard'], False)} | "
                                 f"{f4(v and v['phase_accuracy'], False)} |")
            w.append("")
    p = res["p2f"]
    w.append("### P2F（学習なし）\n")
    w.append("| 段 | overall mAP | 標的群 AP | 陰性対照群 AP | 出所 |\n|---|---|---|---|---|")
    for name, ja in (("tower", "塔単独"), ("shuffle", "入れ替え"), ("pred", "予測"), ("gt", "正解")):
        r = p.get(name)
        w.append(f"| {ja} | {f4(r and r['AP'], False)} | {f4(r and r['target_AP'], False)} | "
                 f"{f4(r and r['control_AP'], False)} | {(r or {}).get('run', 'Task B') if r else 'UNKNOWN（run が無い）'} |")
    w.append("")
    if res.get("predictions"):
        w.append("## §5.3 の予測との照合（記述のための事前の記録。外れても本契約の判定は変わらない）\n")
        w.append("| 番号 | 予測 | 実測 | 照合 |\n|---|---|---|---|")
        for x in res["predictions"]:
            w.append(f"| {x['no']} | {x['about']} | {x['observed'] or '—'} | {x['verdict']} |")
        w.append("")
    if tail:
        w.append(tail)
    return "\n".join(w) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    ap.add_argument("--interim", action="store_true")
    ap.add_argument("--head")
    ap.add_argument("--tail")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        print(json.dumps(self_check(), ensure_ascii=False))
        return
    oldp, oldd, newp, newd = old_pd(), old_dp(), new_pd(), new_dp()
    tables = {typ: pd_table(typ, oldp, newp) for typ in PD_TYPES}
    tables.update({typ: dp_table(typ, oldd, newd) for typ in DP_TYPES})
    p2f = p2f_table(oldp, newp)
    k = lambda key: "/".join(str(x) for x in key)  # noqa: E731
    res = {"task_id": C.FIX_TASK_ID, "interim": a.interim, "epochs": EPOCHS,
           "n_new_pd": len(newp), "n_new_dp": len(newd), "n_old_pd": len(oldp), "n_old_dp": len(oldd),
           "tables": tables, "p2f": p2f, "predictions": None if a.interim else check_predictions(tables, p2f),
           "self_check": self_check(), "recompute_check": recompute_check(tables),
           "read_check": {"pd": {k(x): v.get("read_check") for x, v in oldp.items()},
                          "dp": {k(x): v["read_check"] for x, v in oldd.items()}},
           "two_evaluators_max_abs_diff": {k(x): v.get("two_evaluators_max_abs_diff") for x, v in oldp.items()},
           "reproduction_pd": repro_pd(oldp, newp),
           "previous_values": {"pd": {k(x): {kk: vv for kk, vv in v.items() if kk not in ("best_per_class",)}
                                      for x, v in oldp.items()},
                               "dp": {k(x): {kk: vv for kk, vv in v.items() if kk != "history"} for x, v in oldd.items()}},
           "new_pd": {k(x): v for x, v in newp.items()},
           "new_dp": {k(x): {kk: vv for kk, vv in v.items() if kk != "history"} for x, v in newd.items()}}
    C.write_json(a.out_json, res)
    head, tail = (Path(p).read_text() if p else None for p in (a.head, a.tail))
    Path(a.out_md).write_text(render(res, a.interim, head, tail))
    rc = res["recompute_check"]
    print(f"前回 PD {len(oldp)}・DP {len(oldd)}、本契約 PD {len(newp)}・DP {len(newd)}、"
          f"計算し直し {rc['checked']} 件で食い違い {len(rc['mismatch'])} 件 -> {a.out_md}")


if __name__ == "__main__":
    main()

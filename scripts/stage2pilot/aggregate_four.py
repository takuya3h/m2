"""Task E・F: 四つの型（と tool-history のゲートなし版）の 4 epoch 目の値の集計（非公式 T-2026-10-19-stage2-pilot-four-new-types、SPEC §6）。

本体の .venv で動かす。読むのは本契約の run（experiments/phase1/stage2four_*）と塔単独の再現（Task B-2）だけ。書くのは --out-json と --out-md だけ。

量（SPEC §6.1）: すべて seed 42 の 4 epoch 目の値（PD は epoch 3〔0 始まり〕、DP は epoch 4〔1 始まり〕の状態。run の結果そのもの）。
    Δ空 = 値(型, 腕) − 値(同じ型の空の腕)、Δ入替 = 値(型, 腕) − 値(同じ型の入れ替えの腕)、Δ塔 = 値(型, 腕) − 塔単独の値
    指標: PD は overall mAP・標的群 AP・陰性対照群 AP、DP は macro Jaccard・frame accuracy・クラス別 Jaccard
照合（完了判定 j）: PD は val の結果の予測から det_metrics.summary で、DP は val の事後確率から PhaseEvaluator で指標を計算し直し、
    run の記録と一致することを確かめる。
ホスト（完了判定 h）: 各 run の server.txt から型ごとのホストの集合を作る。

    python scripts/stage2pilot/aggregate_four.py --out-json <json> --out-md <md> [--interim]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

TASK_ID = "T-2026-10-19-stage2-pilot-four-new-types"
EPOCHS = 4
PHASE1 = C.ROOT / "experiments/phase1"
ANA = C.ROOT / "experiments/analysis/stage2_pilot_four"
PD_TYPES = {"DX": "decoder-xattn", "EQ": "extra-queries"}
DP_TYPES = {"LC": "logit-correction", "TH": "tool-history（カードどおり）", "TH-NG": "tool-history のゲートなし版"}
ARMS = ("empty", "pred_noCF", "gt", "pred_CF", "gtpred_CF", "shuffle")
ARM_JA = {"empty": "空", "pred_noCF": "予測-noCF", "gt": "正解", "pred_CF": "予測-CF", "gtpred_CF": "正解予測-CF",
          "shuffle": "入れ替え"}
PD_M = ("AP", "target_AP", "control_AP")
DP_M = ("phase_jaccard", "phase_accuracy")
VAL_ANN = Path(os.environ.get("EGO_ANN_DIR") or C.DET_ANN_A) / "instances_val.json"


def wall_seconds(d):
    try:
        f = "%Y-%m-%d %H:%M:%S UTC"
        return (datetime.strptime((d / "end.txt").read_text().strip(), f)
                - datetime.strptime((d / "start.txt").read_text().strip(), f)).total_seconds()
    except (FileNotFoundError, ValueError):
        return None


def tower():
    det = json.loads((ANA / "repro/dtower_val_seed42.json").read_text())["metrics"]
    ph = json.loads((ANA / "repro/ptower_val.json").read_text())
    return ({m: det[m] for m in PD_M} | {"per_video": det["per_video_AP"]},
            {m: ph[m] for m in DP_M} | {"per_video": ph["per_video"]})


def pd_runs():
    out = {}
    for typ in PD_TYPES:
        for arm in ARMS:
            d = PHASE1 / f"stage2four_pd_{typ}_{arm}_ep{EPOCHS}_seed42"
            if not (d / "stage2four_metrics.json").exists():
                continue
            met = json.loads((d / "stage2four_metrics.json").read_text())
            if met["result_selection"] != "final_epoch" or met["result_epoch"] != EPOCHS - 1:
                raise SystemExit(f"結果が {EPOCHS} epoch 目の状態ではない: {d.name}")
            sp = yaml.safe_load((d / "config.yaml").read_text())["stage2pilot"]
            out[(typ, arm)] = {"run": d.name, **{m: met[m] for m in PD_M}, "per_video": met["per_video_AP"],
                               "per_class": met["per_class_ap"], "init_AP": met["init"],
                               "per_epoch_mAP": met["per_epoch_mAP"], "gates_by_epoch": met["gates_by_epoch"],
                               "frozen_unchanged": met["frozen_unchanged"], "host": (d / "server.txt").read_text().strip(),
                               "wall_seconds": wall_seconds(d), "trainable": sp["total_trainable"],
                               "pred_file": str(d / ("predictions/val_ctrl_best.json.gz" if arm == "empty"
                                                     else "predictions/val_inj_best.json.gz"))}
    return out


def dp_runs():
    out = {}
    for d in sorted(PHASE1.glob(f"stage2four_dp_*_ep{EPOCHS}_seed42")):
        m = re.fullmatch(rf"stage2four_dp_\d+_(LC|TH|TH-NG)_(\w+?)_ep{EPOCHS}_seed42", d.name)
        if not m or not (d / "metrics.json").exists():
            continue
        cfg = yaml.safe_load((d / "config.yaml").read_text())
        met = json.loads((d / "metrics.json").read_text())
        if cfg.get("smoke") or cfg.get("result_selection") != "final_epoch" or met["result_epoch"] != EPOCHS:
            raise SystemExit(f"結果が {EPOCHS} epoch 目の状態ではない: {d.name}")
        key = (cfg["type"], cfg["arm"])
        if key in out:
            raise SystemExit(f"同じ型・腕の run が二つある: {key}")
        pc = json.loads((d / "per_class_ap.json").read_text())
        out[key] = {"run": d.name, **{k: met[k] for k in DP_M}, "per_video": met["per_video"],
                    "per_class": pc.get("per_class_ap", pc), "init_jaccard": met["init_phase_jaccard"],
                    "history": json.loads((d / "logs/history.json").read_text()),
                    "gate_by_epoch": met.get("gate_by_epoch"), "init_gate": met.get("init_gate"),
                    "receiver_unchanged": met["receiver_unchanged"], "negative_control": met.get("negative_control"),
                    "host": (d / "server.txt").read_text().strip(), "wall_seconds": met["elapsed_seconds"],
                    "trainable": met["iface_params"], "probs_file": str(d / "predictions/val_probs_best.npz")}
    return out


def table(typ, runs, tower_val, metrics, video_key):
    rows = {arm: dict(runs[(typ, arm)]) if (typ, arm) in runs else {"value": None} for arm in ARMS}
    for r in rows.values():
        if "run" in r:
            r["value"] = {m: r[m] for m in metrics}
    emp, shf = rows["empty"], rows["shuffle"]
    for arm, r in rows.items():
        v = r["value"]
        r["delta_empty"] = {m: v[m] - emp["value"][m] for m in metrics} if v and emp["value"] else None
        r["delta_shuffle"] = {m: v[m] - shf["value"][m] for m in metrics} if v and shf["value"] else None
        r["delta_tower"] = {m: v[m] - tower_val[m] for m in metrics} if v else None
        r["per_video_delta"] = {}
        for name, ref in (("empty", emp), ("shuffle", shf)):
            if v and ref["value"]:
                r["per_video_delta"][name] = {
                    vid: (r["per_video"][vid][video_key] - ref["per_video"][vid][video_key]) if video_key
                    else (r["per_video"][vid] - ref["per_video"][vid]) for vid in sorted(r["per_video"])}
        if video_key and v and emp["value"] and arm != "empty":
            dlt = {c: r["per_class"][c] - emp["per_class"][c] for c in r["per_class"]}
            r["per_class_delta_empty"] = dlt
            r["per_class_max_abs"] = max(dlt, key=lambda c: abs(dlt[c]))
    return rows


def recompute(pd, dp):
    """完了判定 j: run の記録とは別の経路（予測と確率）から指標を計算し直す。"""
    from egosurgery.metrics.phase import PhaseEvaluator
    out = {}
    for key, r in pd.items():
        ids = json.loads((PHASE1 / r["run"] / "logs/eval_meta_val.json").read_text())["image_ids"]
        s = M.summary(VAL_ANN, M.load_results(r["pred_file"]), ids)
        out["PD " + " ".join(key)] = {m: s[m] - r[m] for m in PD_M}
    names = C.phase_names()
    seqs = {v: y for v, _, y in C.phase_sequences(C.fold_a()["val"])}
    for key, r in dp.items():
        probs = np.load(r["probs_file"])
        ev = PhaseEvaluator(num_classes=len(names), class_names=names)
        for v in sorted(seqs):
            ev.update(probs[v].argmax(1), seqs[v], video_id=v)
        res = ev.compute()
        out["DP " + " ".join(key)] = {m: res[m] - r[m] for m in DP_M}
    out["max_abs"] = max((abs(x) for d in out.values() for x in d.values()), default=None)
    return out


def f4(x, signed=True):
    if x is None:
        return "UNKNOWN"
    return f"{x:+.4f}" if signed else f"{x:.4f}"


def render_type(name, typ, rows, metrics, labels, tower_val, video_key):
    lines = [f"### {name}（{typ}）", "", "| 腕 | " + " | ".join(f"{labels[m]}" for m in metrics) + " | "
             + " | ".join(f"Δ空 {labels[m]}" for m in metrics) + " | " + " | ".join(f"Δ入替 {labels[m]}" for m in metrics)
             + " | " + " | ".join(f"Δ塔 {labels[m]}" for m in metrics) + " | ホスト |",
             "|---|" + "---|" * (4 * len(metrics) + 1)]
    for arm in ARMS:
        r = rows[arm]
        if not r["value"]:
            lines.append(f"| {ARM_JA[arm]} | " + " | ".join(["UNKNOWN（run がまだ無い）"] + [""] * (4 * len(metrics))) + " |")
            continue
        cells = [f4(r["value"][m], False) for m in metrics]
        for k in ("delta_empty", "delta_shuffle", "delta_tower"):
            cells += [f4(r[k][m]) if r[k] else "UNKNOWN" for m in metrics]
        lines.append(f"| {ARM_JA[arm]} | " + " | ".join(cells) + f" | {r['host']} |")
    lines += ["", f"塔単独: " + "、".join(f"{labels[m]} {f4(tower_val[m], False)}" for m in metrics), "",
              "動画ごとの Δ空 と Δ入替（" + (labels[video_key] if video_key else labels["AP"]) + "）:", "",
              "| 腕 | Δ空 09 | Δ空 10 | Δ入替 09 | Δ入替 10 |", "|---|---|---|---|---|"]
    for arm in ARMS:
        pvd = rows[arm].get("per_video_delta") or {}
        e, s = pvd.get("empty", {}), pvd.get("shuffle", {})
        lines.append(f"| {ARM_JA[arm]} | {f4(e.get('09'))} | {f4(e.get('10'))} | {f4(s.get('09'))} | {f4(s.get('10'))} |")
    if video_key:
        lines += ["", "クラス別 Jaccard の Δ空 の絶対値が最も大きい工程: " + "、".join(
            f"{ARM_JA[a]} {rows[a]['per_class_max_abs']}（{f4(rows[a]['per_class_delta_empty'][rows[a]['per_class_max_abs']])}）"
            for a in ARMS if rows[a].get("per_class_max_abs"))]
    return lines


def gate_lines(pd, dp):
    lines = []
    for typ in ("DX", "EQ"):
        for arm in ARMS:
            r = pd.get((typ, arm))
            if not r:
                continue
            g = r["gates_by_epoch"]
            if typ == "DX":
                fmt = {e: "[" + ", ".join(f"{x:+.4f}" for x in v["tanh_alpha"]) + "]" for e, v in g.items()}
            else:
                fmt = {e: f"{v['score_const']:+.4f}" for e, v in g.items()}
            lines.append(f"| {PD_TYPES[typ]} | {ARM_JA[arm]} | " + " | ".join(fmt.get(str(e), "") for e in range(-1, EPOCHS))
                         + " |")
    for arm in ARMS:
        r = dp.get(("TH", arm))
        if r and r["gate_by_epoch"]:
            g = r["gate_by_epoch"]
            lines.append(f"| tool-history | {ARM_JA[arm]} | {r['init_gate']['tanh_alpha']:+.5f} | "
                         + " | ".join(f"{g[str(e)]['tanh_alpha']:+.5f}" for e in range(1, EPOCHS + 1)) + " |")
    if not lines:
        return []
    return (["### ゲートの値（epoch ごと）", "",
             "decoder-xattn は層ごとの tanh(α_l)（層 0〜5）、extra-queries は追加の出力のスコアの定数（初期値 −10）、"
             "tool-history は tanh(α)。PD の列は学習前（−1）と epoch 0〜3、DP の列は学習前と epoch 1〜4。", "",
             "| 型 | 腕 | 学習前 | 1 | 2 | 3 | 4 |", "|---|---|---|---|---|---|---|"] + lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--interim", action="store_true")
    a = ap.parse_args()
    t_pd, t_dp = tower()
    pd, dp = pd_runs(), dp_runs()
    tables = {"PD": {t: table(t, pd, t_pd, PD_M, None) for t in PD_TYPES},
              "DP": {t: table(t, dp, t_dp, DP_M, "phase_jaccard") for t in DP_TYPES}}
    hosts = {t: sorted({r["host"] for k, r in {**pd, **dp}.items() if k[0] == t}) for t in {**PD_TYPES, **DP_TYPES}}
    res = {"task_id": TASK_ID, "unofficial": True, "tower": {"PD": t_pd, "DP": t_dp}, "tables": tables,
           "hosts_by_type": hosts, "n_runs": {"PD": len(pd), "DP": len(dp)},
           "recompute": recompute(pd, dp) if (pd or dp) else None,
           "costs": {" ".join(k): {"wall_seconds": r["wall_seconds"], "trainable": r["trainable"]} for k, r in {**pd, **dp}.items()}}
    C.write_json(a.out_json, res)
    lab_pd = {"AP": "overall mAP", "target_AP": "標的群 AP", "control_AP": "陰性対照群 AP"}
    lab_dp = {"phase_jaccard": "macro Jaccard", "phase_accuracy": "frame accuracy"}
    md = [f"# {'中間記録' if a.interim else '集計'}: Stage 2 予備測定の新しい四つの型（非公式の測定。関門と設計の判断に使わない）", "",
          f"契約 {TASK_ID}。すべて折り A、seed 42、4 epoch 目の状態の val の値（最良の回を選ばない）。"
          "Δ空・Δ入替・Δ塔は 1 本ずつの差（seed は一つ）。test は通していない。", ""]
    md += ["## 検出から工程（DP、x(t) 32 次元）", ""]
    for t, name in DP_TYPES.items():
        md += render_type(name, t, tables["DP"][t], DP_M, lab_dp, t_dp, "phase_jaccard") + [""]
    if pd or not a.interim:
        md += ["## 工程から検出（PD、W1）", ""]
        for t, name in PD_TYPES.items():
            md += render_type(name, t, tables["PD"][t], PD_M, lab_pd, t_pd, None) + [""]
    md += gate_lines(pd, dp) + [""]
    md += ["### 型ごとのホスト（server.txt）", "", "| 型 | ホスト |", "|---|---|"]
    md += [f"| {({**PD_TYPES, **DP_TYPES})[t]} | {', '.join(h) if h else 'UNKNOWN（run がまだ無い）'} |" for t, h in hosts.items()]
    rc = res["recompute"]
    md += ["", f"照合（予測・確率から計算し直した値と run の記録の差の最大）: {rc['max_abs'] if rc else 'UNKNOWN'}", ""]
    Path(a.out_md).write_text("\n".join(md) + "\n")
    print(f"PD {len(pd)} 本、DP {len(dp)} 本。照合の差の最大 {rc['max_abs'] if rc else None}。ホスト {hosts}")


if __name__ == "__main__":
    main()

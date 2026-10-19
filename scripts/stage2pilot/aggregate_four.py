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



# ---------------------------------------------------------------- 殺し実験・寄与・予測・参考の表
def load_json(path):
    return json.loads(Path(path).read_text()) if Path(path).exists() else None


def kill_results():
    k3_runs = sorted(PHASE1.glob(f"stage2four_k3_*_gru_D0only_ep{EPOCHS}_seed42"))
    return {"K1": load_json(ANA / "kill/k1.json"), "K1_control": load_json(ANA / "kill/k1_control_empty_missed.json"),
            "K2": load_json(ANA / "kill/k2.json"), "K2_control": load_json(ANA / "kill/k2_control_onehot.json"),
            "K3": load_json(ANA / "kill/k3.json"),
            "K3_run": ({"run": k3_runs[-1].name, **json.loads((k3_runs[-1] / "metrics.json").read_text())}
                       if k3_runs else None)}


def xq_contrib(pd):
    out = {}
    for arm in ARMS:
        ev, ct = load_json(ANA / f"xq_contrib/pd_EQ_{arm}_trained.json"), load_json(ANA / f"xq_contrib/pd_EQ_{arm}_contrib.json")
        if not ev:
            continue
        fm, om = ev["final"]["metrics"], ev["orig"]["metrics"]
        run = pd.get(("EQ", arm))
        out[arm] = {"final": {m: fm[m] for m in PD_M}, "orig_only": {m: om[m] for m in PD_M},
                    "final_minus_orig": {m: fm[m] - om[m] for m in PD_M},
                    "per_class_final_minus_orig": {c: fm["per_class_ap"][c] - om["per_class_ap"][c] for c in fm["per_class_ap"]},
                    "orig_only_diff_vs_tower": ev["orig"]["diff_vs_ref"],
                    "eval_equals_run": run is not None and ev["final"]["eval_detection_mAP"] == run["AP"],
                    "score_const": ev["gates_eval"]["score_const"], **({k: ct[k] for k in (
                        "n_extra_in_top300", "images_with_extra_in_top300", "n_extra_matching_any_gt",
                        "n_extra_matching_missed", "n_missed_val", "n_missed_matched_by_extra")} if ct else {})}
    return out


def predictions(tables, dp, pd):
    """SPEC §6.3 の予測との照合（記述のための事前の記録。外れても判定は変わらない）。"""
    out = []
    g = [dp[("TH", a)]["gate_by_epoch"][str(EPOCHS)]["tanh_alpha"] for a in ARMS if ("TH", a) in dp]
    out.append({"no": 1, "about": "tool-history の 4 epoch 目の tanh(α) の絶対値は全腕で 0.05 未満",
                "observed": f"{len(g)} 腕、最大 {max(abs(x) for x in g):.5f}" if g else None,
                "verdict": ("当たり" if all(abs(x) < 0.05 for x in g) else "外れ") if len(g) == 6 else "UNKNOWN"})
    a, b = (tables["DP"][t]["pred_noCF"].get("delta_empty") for t in ("TH-NG", "TH"))
    out.append({"no": 2, "about": "予測-noCF の Δ空（Jaccard）の絶対値はゲートなし版の方が tool-history より大きい",
                "observed": f"ゲートなし版 {a['phase_jaccard']:+.4f}、tool-history {b['phase_jaccard']:+.4f}" if a and b else None,
                "verdict": ("当たり" if abs(a["phase_jaccard"]) > abs(b["phase_jaccard"]) else "外れ") if a and b else "UNKNOWN"})
    tr, va = load_json(ANA / "xq/missed_train.json"), load_json(ANA / "xq/missed_val.json")
    out.append({"no": 3, "about": "extra-queries の見落としの割合は train の方が val より小さい",
                "observed": f"train {tr['missed_fraction']:.5f}、val {va['missed_fraction']:.5f}" if tr and va else None,
                "verdict": ("当たり" if tr["missed_fraction"] < va["missed_fraction"] else "外れ") if tr and va else "UNKNOWN"})
    d = tables["PD"]["DX"]["gt"].get("delta_empty")
    out.append({"no": 4, "about": "decoder-xattn の正解の腕の Δ空（標的群 AP）は正",
                "observed": f"{d['target_AP']:+.4f}" if d else None,
                "verdict": ("当たり" if d["target_AP"] > 0 else "外れ") if d else "UNKNOWN"})
    return out


def reference_table(tables):
    """SPEC §6.2 の 7: ホストの列を付けた参考の表（本契約の型と直しの契約の型）。処置の差として読まない。"""
    rows = []
    fix = load_json(C.ROOT / "experiments/analysis/stage2_pilot_fix/report.json")
    for typ, t in (fix or {}).get("tables", {}).items():
        metric = "phase_jaccard" if typ.startswith("D") else "target_AP"
        for arm in ("pred_noCF", "gt"):
            r = t["rows"].get(arm, {})
            runs = [t["rows"][a].get("run") for a in t["rows"] if t["rows"][a].get("run")]
            hosts = sorted({(PHASE1 / x / "server.txt").read_text().strip() for x in runs if (PHASE1 / x / "server.txt").exists()})
            rows.append({"contract": "直し", "type": typ, "arm": arm, "metric": metric,
                         "delta_empty": (r.get("delta_empty") or {}).get(metric),
                         "delta_shuffle": (r.get("delta_shuffle") or {}).get(metric), "hosts": hosts})
    for side, types in (("PD", PD_TYPES), ("DP", DP_TYPES)):
        metric = "target_AP" if side == "PD" else "phase_jaccard"
        for typ in types:
            hosts = sorted({r["host"] for r in tables[side][typ].values() if r.get("host")})
            for arm in ("pred_noCF", "gt"):
                r = tables[side][typ][arm]
                rows.append({"contract": "本契約", "type": typ, "arm": arm, "metric": metric,
                             "delta_empty": (r.get("delta_empty") or {}).get(metric),
                             "delta_shuffle": (r.get("delta_shuffle") or {}).get(metric), "hosts": hosts})
    return rows


def render_extras(res):
    md = []
    xc = res["xq_contrib"]
    if xc:
        md += ["### extra-queries の追加の出力の寄与（学習後、4 epoch 目の界面）", "",
               "| 腕 | スコアの定数 | 上位 300 に入った追加（件 / 画像） | うち正解に当たる | うち見落としに当たる | 照合した見落とし（val 78 個中） | "
               "最終 − 追加を除いた overall mAP | 同 標的群 AP | 同 陰性対照群 AP |", "|---|---|---|---|---|---|---|---|---|"]
        for arm, r in xc.items():
            d = r["final_minus_orig"]
            md.append(f"| {ARM_JA[arm]} | {r['score_const']:+.3f} | {r.get('n_extra_in_top300')} / {r.get('images_with_extra_in_top300')} | "
                      f"{r.get('n_extra_matching_any_gt')} | {r.get('n_extra_matching_missed')} | {r.get('n_missed_matched_by_extra')} | "
                      f"{f4(d['AP'])} | {f4(d['target_AP'])} | {f4(d['control_AP'])} |")
        md += ["", "追加の出力を除いた検出（元の出力だけ）は、6 腕とも塔単独と出力の差 0（`orig_only_diff_vs_tower`）。", ""]
    k = res["kill"]
    md += ["## 殺し実験（記述だけ。結果で何も決めない）", ""]
    if k["K1"]:
        d = k["K1"]["diff"]
        md += [f"- K1（extra-queries の神託、学習なし）: val の見落とし {k['K1']['n_missed_added']} 個を正しいクラス・位置・確信度 1 で足すと、"
               f"overall mAP {f4(d['AP'])}、標的群 AP {f4(d['target_AP'])}、陰性対照群 AP {f4(d['control_AP'])}。"
               f"見落としを 0 件にした写しでは差 {k['K1_control']['diff']['AP'] if k['K1_control'] else 'UNKNOWN'}"]
    else:
        md += ["- K1: UNKNOWN（まだ回していない）"]
    for name, key, base, keys in (("K2（logit-correction、多項ロジスティック回帰）", "K2", "i", ("ii-i", "iii-i")),):
        r = k[key]
        if r:
            dd = r["diffs"]
            md += [f"- {name}: 片方の val 動画で当てはめもう片方で測る（両方向の平均）。" + "、".join(
                f"{x} の macro Jaccard {f4(dd[x]['mean_over_directions']['phase_jaccard'])}・accuracy "
                f"{f4(dd[x]['mean_over_directions']['phase_accuracy'])}・NLL {f4(dd[x]['mean_over_directions']['mean_nll'])}" for x in keys)
                   + (f"。陽性対照（(ii) の D0 を正解の工程の one-hot に）では (ii)−(i) の Jaccard "
                      f"{f4(k['K2_control']['diffs']['ii-i']['mean_over_directions']['phase_jaccard'])}" if k["K2_control"] else "")]
        else:
            md += [f"- {name}: UNKNOWN（まだ回していない）"]
    r = k["K3"]
    if r:
        md += [f"- K3（tool-history）: (1) D0 の系列だけの GRU の val の macro Jaccard {f4(r['gru_alone_val']['phase_jaccard'], False)}"
               f"（時間の順を入れ替えると {f4(r['gru_alone_val_shuffled']['phase_jaccard'], False)}）。"
               f"(2) (i)+GRU − (i) の Jaccard {f4(r['k3_2']['diffs']['i+gru-i']['mean_over_directions']['phase_jaccard'])}、"
               f"(3) 時間の順を入れ替えた GRU で {f4(r['k3_3']['diffs']['i+gru_shuffled-i']['mean_over_directions']['phase_jaccard'])}"
               f"（(3)−(2) {f4(r['k3_3_minus_k3_2']['phase_jaccard'])}）。術式の精度は {r['surgery_type_accuracy']}"]
    else:
        md += ["- K3: UNKNOWN（まだ回していない）"]
    md += ["", "## 事前の予測との照合（SPEC §6.3。外れても判定は変わらない）", "", "| # | 予測 | 実測 | 照合 |", "|---|---|---|---|"]
    md += [f"| {p['no']} | {p['about']} | {p['observed'] or 'UNKNOWN'} | {p['verdict']} |" for p in res["predictions"]]
    md += ["", "## 参考の表: ホストの列つき（SPEC §6.2 の 7。ホストをまたぐ値を処置の差として読まない）", "",
           "| 契約 | 型 | 腕 | 指標 | Δ空 | Δ入替 | ホスト |", "|---|---|---|---|---|---|---|"]
    md += [f"| {r['contract']} | {r['type']} | {ARM_JA[r['arm']]} | {r['metric']} | {f4(r['delta_empty'])} | {f4(r['delta_shuffle'])} | "
           f"{', '.join(r['hosts']) or 'UNKNOWN'} |" for r in res["reference"]]
    return md + [""]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--interim", action="store_true")
    ap.add_argument("--head", default=None, help="REPORT の冒頭に置く手書きの節（Markdown）")
    ap.add_argument("--tail", default=None, help="REPORT の末尾に置く手書きの節（Markdown）")
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
    res.update(kill=kill_results(), xq_contrib=xq_contrib(pd), predictions=predictions(tables, dp, pd),
               reference=reference_table(tables))
    C.write_json(a.out_json, res)
    lab_pd = {"AP": "overall mAP", "target_AP": "標的群 AP", "control_AP": "陰性対照群 AP"}
    lab_dp = {"phase_jaccard": "macro Jaccard", "phase_accuracy": "frame accuracy"}
    md = [f"# {'中間記録' if a.interim else '集計'}: Stage 2 予備測定の新しい四つの型（非公式の測定。関門と設計の判断に使わない）", "",
          f"契約 {TASK_ID}。すべて折り A、seed 42、4 epoch 目の状態の val の値（最良の回を選ばない）。"
          "Δ空・Δ入替・Δ塔は 1 本ずつの差（seed は一つ）。test は通していない。", ""]
    if a.head:
        md += [Path(a.head).read_text().rstrip(), ""]
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
    if not a.interim:
        md += render_extras(res)
    if a.tail:
        md += [Path(a.tail).read_text().rstrip(), ""]
    Path(a.out_md).write_text("\n".join(md) + "\n")
    print(f"PD {len(pd)} 本、DP {len(dp)} 本。照合の差の最大 {rc['max_abs'] if rc else None}。ホスト {hosts}")


if __name__ == "__main__":
    main()

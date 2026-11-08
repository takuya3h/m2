"""集計・検算・test 不使用の確かめ（非公式 T-2026-11-06-grasp-pilot-d-rerun、Task E、SPEC §6・§8 の f・g・h）。本体の .venv。読むだけ。

    aggregate --out <summary.json> --tables <tables.md>   案 D（3 腕 + 参考の三本目の無効な 2 腕）と案 B（bengio の 8 腕 + 二本目の参照）の値・差・予測の照合
    verify    --summary <summary.json> --out <json>       表の差を各 run の記録から別の経路で計算し直す（判定 g）。案 D は保存した予測からも計算し直す。
                                                          対照: 値を 1e-6 ずらした写しで不一致。存在しない run の名前で 0 件（判定 f）
    testcheck --out <json>                                学習と評価に通した動画の集合と {04, 05, 07} の共通（判定 h）。対照: 04 を混ぜた入力で共通 1 件

読み方の規則（SPEC §6.2）: seed は一つ。差は 1 本ずつの差として書き、陽性・陰性・有意などの語は使わない。
環境変数 RERUN_D_PREFIX・RERUN_B_PREFIX で run の接頭辞を差し替えられる（三本目・四本目の run で道具を試すときだけ。本番は既定）。
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path

M = Path(__file__).resolve().parents[2]
P1 = M / "experiments/phase1"
TASK_ID = "T-2026-11-06-grasp-pilot-d-rerun"
TEST = {"04", "05", "07"}
ANN = M / "data/annotations/egosurgery_tool_folds/A"
D_PFX = os.environ.get("RERUN_D_PREFIX", "graspd2")
B_PFX = os.environ.get("RERUN_B_PREFIX", "grasparms_B")
D_ARMS = {"gteach": f"{D_PFX}_gteach_ep15_seed42", "shuf": f"{D_PFX}_shuf_ep15_seed42"}
D_NONE = "grasppilot3_d_none_ep15_seed42"                       # 三本目の補助損失なし（有効。SPEC §3.1 の条件を満たした）
D_INVALID = {"gteach": "grasppilot3_d_gteach_ep15_seed42", "shuf": "grasppilot3_d_shuf_ep15_seed42"}   # 三本目の無効な腕（参考のみ）
B_BENGIO = ["empty", "gt", "pred_noCF", "pred_CF", "gtpred_CF", "shuffle", "toolonly_pred_noCF", "toolonly_shuffle"]
B_THIS = ["empty", "gt"]                                       # 本契約で回す腕。残りは四本目の run
B_SECOND = {"empty": "grasppilot2_B_empty_ep4_seed42", "gt": "grasppilot2_B_gt_ep4_seed42"}   # 二本目（andrew）
TOWER = {"AP": 0.7273450, "target_AP": 0.7950748, "control_AP": 0.6726632}
TARGET = ["Skewer", "Bipolar Forceps", "Scalpel", "Syringe", "Raspatory"]
CONTROL = ["Gauze", "Mouth Gag", "Suction Cannula", "Tweezers"]
KEYS = ["AP", "target_AP", "control_AP"]
D_PAIRS = [("gteach", "none"), ("shuf", "none"), ("gteach", "shuf")]


def b_dir(arm, second=False):
    if second:
        return P1 / B_SECOND[arm]
    return P1 / (f"{B_PFX}_{arm}_ep4_seed42")


def d_values(name):
    d = P1 / name
    m = json.loads((d / "metrics.json").read_text())
    pc = json.loads((d / "per_class_ap.json").read_text())
    v = m["val"]
    t = lambda f: (d / f).read_text().strip() if (d / f).exists() else None   # noqa: E731
    return {"run": name, "aux_weight": m["aux_weight"], "AP": v["mAP"], "target_AP": v["target_AP"], "control_AP": v["control_AP"],
            "AP50": v.get("mAP_50"), "target_missing": v["target_missing"], "control_missing": v["control_missing"],
            "per_video": v["per_video_AP"], "per_class": pc, "result_epoch": m["result_state"]["epoch"], "n_epochs": m["n_epochs"],
            "aux_ce_by_epoch": [e.get("step_aux_ce_mean") for e in m["epochs"]],
            "aux_acc_by_epoch": [e.get("step_aux_acc_matched") for e in m["epochs"]],
            "matched_eq_gt_by_epoch": [e.get("step_matched_eq_gt") for e in m["epochs"]],
            "inloop_val_mAP_by_epoch": [e.get("val_mAP_inloop") for e in m["epochs"]],
            "lr_by_epoch": [e.get("lr_at_step0") for e in m["epochs"]], "det_loss_by_epoch": [e.get("avg_loss_det") for e in m["epochs"]],
            "aux_loss_weighted_by_epoch": [e.get("avg_loss_grasp") for e in m["epochs"]],
            "videos_passed": m["videos_passed"], "val_preds": m["val_preds"], "start": t("start.txt"), "end": t("end.txt"),
            "host": t("server.txt"), "code_sha256": t("code_sha256.txt")}


def b_values(d):
    m = json.loads((d / "grasppilot_metrics.json").read_text())
    t = lambda f: (d / f).read_text().strip() if (d / f).exists() else None   # noqa: E731
    host = t("host.txt") or t("server.txt")
    return {"run": d.name, "AP": m["AP"], "target_AP": m["target_AP"], "control_AP": m["control_AP"],
            "target_missing": m["target_missing"], "control_missing": m["control_missing"],
            "per_class": m["per_class_ap"], "per_video": m["per_video_AP"], "per_epoch_mAP": m["per_epoch_mAP"],
            "iface_weight_by_epoch": m["iface_weight_by_epoch"], "init": m["init"], "result_epoch": m["result_epoch"],
            "frozen_unchanged": m["frozen_unchanged"], "start": t("start.txt"), "end": t("end.txt"), "host": host}


def diff(a, b, keys=KEYS):
    return {k: a[k] - b[k] for k in keys}


def vdiff(a, b):
    return {v: a[v] - b[v] for v in a}


def cdiff(a, b):
    return {c: (a[c] - b[c]) if a[c] is not None and b[c] is not None and a[c] == a[c] and b[c] == b[c] else None for c in a}


def cmd_aggregate(a):
    Dn = {"none": d_values(D_NONE)}
    missing_D = []
    for k, n in D_ARMS.items():
        if (P1 / n / "metrics.json").exists():
            Dn[k] = d_values(n)
        else:
            missing_D.append(k)
    Dinv = {k: d_values(n) for k, n in D_INVALID.items()}
    B, missing_B = {}, []
    for arm in B_BENGIO:
        d = b_dir(arm) if arm not in B_THIS else b_dir(arm)
        if (d / "grasppilot_metrics.json").exists():
            B[arm] = b_values(d)
        else:
            missing_B.append(arm)
    B2 = {arm: b_values(b_dir(arm, True)) for arm in B_SECOND}
    out = {"task_id": TASK_ID, "unofficial": True, "tower_record": TOWER, "missing_D": missing_D, "missing_B": missing_B,
           "D": Dn, "D_invalid_third": Dinv, "B": B, "B_second_andrew": B2, "diffs": {}, "predictions": {}}
    X = out["diffs"]
    for x, y in D_PAIRS:
        if x in Dn and y in Dn:
            key = f"D_{x}_minus_{y}"
            X[key] = diff(Dn[x], Dn[y])
            X[key + "_per_video"] = vdiff(Dn[x]["per_video"], Dn[y]["per_video"])
            X[key + "_per_class"] = cdiff(Dn[x]["per_class"], Dn[y]["per_class"])
    for k in Dinv:   # 参考: 三本目の値（無効）と補助損失なしの差。本文の差の計算に使わない
        X[f"D_ref_invalid_third_{k}_minus_none"] = diff(Dinv[k], Dn["none"])
    if "empty" in B:
        e = B["empty"]
        X["B_vs_empty"] = {arm: diff(v, e) for arm, v in B.items() if arm != "empty"}
        X["B_vs_empty_per_video"] = {arm: vdiff(v["per_video"], e["per_video"]) for arm, v in B.items() if arm != "empty"}
        X["B_vs_empty_per_class"] = {arm: cdiff(v["per_class"], e["per_class"]) for arm, v in B.items() if arm != "empty"}
        X["B_empty_vs_tower_record"] = diff(e, TOWER)
    if "gt" in B:
        g = B["gt"]
        X["B_vs_gt"] = {arm: diff(v, g) for arm, v in B.items() if arm != "gt"}
        X["B_vs_gt_per_video"] = {arm: vdiff(v["per_video"], g["per_video"]) for arm, v in B.items() if arm != "gt"}
    for x, y, name in (("pred_noCF", "shuffle", "B_pred_noCF_minus_shuffle"),
                       ("toolonly_pred_noCF", "toolonly_shuffle", "T_pred_noCF_minus_shuffle"),
                       ("toolonly_pred_noCF", "pred_noCF", "T_minus_B_pred_noCF")):
        if x in B and y in B:
            X[name] = diff(B[x], B[y])
            X[name + "_per_video"] = vdiff(B[x]["per_video"], B[y]["per_video"])
    # ホストの差の目安（処置の差として読まない）: bengio の値 − 二本目（andrew）の値
    for arm in B_THIS:
        if arm in B:
            X[f"host_diff_{arm}_bengio_minus_andrew"] = diff(B[arm], B2[arm])
    # 四本目の RESULT が書いた Δ空（二本目の空との差）と、bengio の空との差を並べる
    if "empty" in B:
        X["B_vs_second_empty_andrew_fourth_style"] = {arm: diff(v, B2["empty"]) for arm, v in B.items() if arm not in ("empty",)}
    # §6.3 の予測（外れても判定は変わらない）
    P = out["predictions"]
    if "gteach" in Dn:
        d = X["D_gteach_minus_none"]["AP"]
        P["1"] = {"text": "案 D の G を教師 − 補助損失なし（overall mAP）の絶対値は 0.01 未満", "value": d, "held": abs(d) < 0.01}
    if "gteach" in Dn and "shuf" in Dn:
        g, s = Dn["gteach"]["aux_ce_by_epoch"][-1], Dn["shuf"]["aux_ce_by_epoch"][-1]
        P["2"] = {"text": "入れ替えた教師の腕の補助損失は、最後の epoch で G を教師の腕より大きい", "gteach_last": g, "shuf_last": s,
                  "held": s is not None and g is not None and s > g}
    if "gt" in B:
        d = B["gt"]["target_AP"] - B2["gt"]["target_AP"]
        P["3"] = {"text": "案 B の正解の腕（bengio）の標的群 AP は二本目（andrew、0.8107）と差の絶対値 0.005 以内", "bengio": B["gt"]["target_AP"],
                  "andrew": B2["gt"]["target_AP"], "diff": d, "held": abs(d) <= 0.005}
    if "empty" in B:
        d = B["empty"]["target_AP"] - TOWER["target_AP"]
        P["4"] = {"text": "案 B の空の腕（bengio）は塔単独の値と標的群 AP で差の絶対値 0.005 以内", "empty": B["empty"]["target_AP"],
                  "tower": TOWER["target_AP"], "diff": d, "held": abs(d) <= 0.005}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    Path(a.tables).write_text(tables(out))
    print(json.dumps({"missing_D": missing_D, "missing_B": missing_B, "predictions": {k: v["held"] for k, v in P.items()}}, ensure_ascii=False))


def f7(x):
    return "—" if x is None else f"{x:.7f}"


def s7(x):
    return "—" if x is None else f"{x:+.7f}"


def tables(o):
    Dn, Dinv, B, B2, X = o["D"], o["D_invalid_third"], o["B"], o["B_second_andrew"], o["diffs"]
    L = ["<!-- scripts/grasppilot/rerun_aggregate.py aggregate が書く。手で直さない -->", "",
         "### 案 D（val 09・10、最後の状態 = epoch 14。補助損失なしは三本目の run）", "",
         "| 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | run |", "|---|---|---|---|---|"]
    for k, label in (("none", "補助損失なし（三本目）"), ("gteach", "G を教師"), ("shuf", "入れ替えた教師")):
        if k in Dn:
            v = Dn[k]
            L.append(f"| {label} | {f7(v['AP'])} | {f7(v['target_AP'])} | {f7(v['control_AP'])} | `{v['run']}` |")
    L += ["", "| 差（1 本ずつの差） | overall | 標的群 | 陰性対照群 | 09 | 10 |", "|---|---|---|---|---|---|"]
    for x, y in D_PAIRS:
        key = f"D_{x}_minus_{y}"
        if key in X:
            d, pv = X[key], X[key + "_per_video"]
            lab = {"gteach": "G を教師", "shuf": "入れ替えた教師", "none": "補助損失なし"}
            L.append(f"| {lab[x]} − {lab[y]} | {s7(d['AP'])} | {s7(d['target_AP'])} | {s7(d['control_AP'])} | {s7(pv['09'])} | {s7(pv['10'])} |")
    L += ["", "参考: 三本目の無効な腕（G が設計の誤りの二本目の G から作られた q。**無効**。本文の差の計算に使わない）", "",
          "| 腕（無効） | overall | 標的群 | 陰性対照群 | 補助損失なしとの差 overall / 標的群 / 陰性対照群 |", "|---|---|---|---|---|"]
    for k, v in Dinv.items():
        d = X[f"D_ref_invalid_third_{k}_minus_none"]
        L.append(f"| {k}（三本目、無効） | {f7(v['AP'])} | {f7(v['target_AP'])} | {f7(v['control_AP'])} | "
                 f"{s7(d['AP'])} / {s7(d['target_AP'])} / {s7(d['control_AP'])} |")
    names = list(Dn["none"]["per_class"])
    L += ["", "クラス別 AP（標的群 = " + "・".join(TARGET) + "、陰性対照群 = " + "・".join(CONTROL) + "）:", "",
          "| 腕 | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for k in ("none", "gteach", "shuf"):
        if k in Dn:
            L.append(f"| {k} | " + " | ".join("—" if Dn[k]["per_class"][c] is None else f"{Dn[k]['per_class'][c]:.4f}" for c in names) + " |")
    L += ["", "案 D の epoch ごとの補助損失（重みの前の交差エントロピーの平均）と学習中の val mAP:", "",
          "| 腕 | 項目 | " + " | ".join(str(i) for i in range(15)) + " |", "|---|---|" + "---|" * 15]
    for k in ("gteach", "shuf"):
        if k in Dn:
            L.append(f"| {k} | 補助損失 | " + " | ".join(f7(x)[:6] if x is not None else "—" for x in Dn[k]["aux_ce_by_epoch"]) + " |")
    for k in ("none", "gteach", "shuf"):
        if k in Dn:
            L.append(f"| {k} | val mAP | " + " | ".join(f7(x)[:6] if x is not None else "—" for x in Dn[k]["inloop_val_mAP_by_epoch"]) + " |")
    L += ["", "### 案 B（W1、4 epoch、seed 42、val 09・10。bengio の run だけ。空と正解は本契約、他は四本目）", "",
          "| 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | Δ空 overall | Δ空 標的群 | Δ空 陰性対照群 | 正解との差 overall | 標的群 | 陰性対照群 | run |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm in B_BENGIO:
        if arm in B:
            v = B[arm]
            e = X.get("B_vs_empty", {}).get(arm, {})
            g = X.get("B_vs_gt", {}).get(arm, {})
            L.append(f"| {arm} | {f7(v['AP'])} | {f7(v['target_AP'])} | {f7(v['control_AP'])} | {s7(e.get('AP'))} | {s7(e.get('target_AP'))} | "
                     f"{s7(e.get('control_AP'))} | {s7(g.get('AP'))} | {s7(g.get('target_AP'))} | {s7(g.get('control_AP'))} | `{v['run']}` |")
    L += ["", "| 差 | overall | 標的群 | 陰性対照群 | 09 | 10 |", "|---|---|---|---|---|---|"]
    for name, label in (("B_pred_noCF_minus_shuffle", "案 B Δ入替（予測-noCF − 入れ替え）"),
                        ("T_pred_noCF_minus_shuffle", "術具だけ Δ入替（予測-noCF − 入れ替え）"),
                        ("T_minus_B_pred_noCF", "誰の手かの情報による差（術具だけ − 案 B、予測-noCF）")):
        if name in X:
            d, pv = X[name], X[name + "_per_video"]
            L.append(f"| {label} | {s7(d['AP'])} | {s7(d['target_AP'])} | {s7(d['control_AP'])} | {s7(pv['09'])} | {s7(pv['10'])} |")
    L += ["", "Δ空 の動画ごとの mAP:", "", "| 腕 | 09 | 10 |", "|---|---|---|"]
    for arm, pv in X.get("B_vs_empty_per_video", {}).items():
        L.append(f"| {arm} | {s7(pv['09'])} | {s7(pv['10'])} |")
    cls = list(B2["empty"]["per_class"])
    L += ["", "クラス別 AP:", "", "| 腕 | " + " | ".join(cls) + " |", "|---|" + "---|" * len(cls)]
    for arm in B_BENGIO:
        if arm in B:
            L.append(f"| {arm}（bengio） | " + " | ".join("—" if B[arm]["per_class"][c] is None else f"{B[arm]['per_class'][c]:.4f}" for c in cls) + " |")
    for arm in B2:
        L.append(f"| {arm}（二本目、andrew） | " + " | ".join("—" if B2[arm]["per_class"][c] is None else f"{B2[arm]['per_class'][c]:.4f}" for c in cls) + " |")
    L += ["", "ホストの差の目安（bengio − 二本目の andrew。**処置の差として読まない**）と、bengio の空・正解の塔単独との差:", "",
          "| 項目 | overall | 標的群 | 陰性対照群 |", "|---|---|---|---|"]
    for arm in B_THIS:
        k = f"host_diff_{arm}_bengio_minus_andrew"
        if k in X:
            L.append(f"| {arm}（bengio − andrew） | {s7(X[k]['AP'])} | {s7(X[k]['target_AP'])} | {s7(X[k]['control_AP'])} |")
    if "B_empty_vs_tower_record" in X:
        d = X["B_empty_vs_tower_record"]
        L.append(f"| 空（bengio）− 塔単独の記録 | {s7(d['AP'])} | {s7(d['target_AP'])} | {s7(d['control_AP'])} |")
    L += ["", "四本目の RESULT の書き方（二本目の空 = andrew との差）。参考:", "", "| 腕 | overall | 標的群 | 陰性対照群 |", "|---|---|---|---|"]
    for arm, d in X.get("B_vs_second_empty_andrew_fourth_style", {}).items():
        L.append(f"| {arm} − 二本目の空 | {s7(d['AP'])} | {s7(d['target_AP'])} | {s7(d['control_AP'])} |")
    L += ["", "epoch ごとの val mAP（−1 は学習前）と界面の重みの絶対値の最大:", "", "| 腕 | −1 | 0 | 1 | 2 | 3 | 重み 3 |", "|---|---|---|---|---|---|---|"]
    for arm in B_BENGIO:
        if arm in B:
            pe, w = B[arm]["per_epoch_mAP"], B[arm]["iface_weight_by_epoch"]
            L.append(f"| {arm} | " + " | ".join(f"{pe[k]:.4f}" if k in pe else "—" for k in ("-1", "0", "1", "2", "3"))
                     + f" | {w.get('3', {}).get('iface_max_abs', float('nan')):.4f} |")
    return "\n".join(L) + "\n"


def recompute(o):
    """summary の差を、各 run の記録のファイルを読み直して別の経路で計算する（判定 g）。"""
    bad = []

    def chk(name, got, want):
        if abs(got - want) > 1e-12:
            bad.append(f"{name}: {got} != {want}")

    def read_d(name):
        m = json.loads((P1 / name / "metrics.json").read_text())["val"]
        return m["mAP"], m["target_AP"], m["control_AP"]

    def read_b(name):
        m = json.loads((P1 / name / "grasppilot_metrics.json").read_text())
        return m["AP"], m["target_AP"], m["control_AP"]

    X = o["diffs"]
    runD = {k: v["run"] for k, v in o["D"].items()}
    for x, y in D_PAIRS:
        key = f"D_{x}_minus_{y}"
        if key in X:
            a, b = read_d(runD[x]), read_d(runD[y])
            for i, k in enumerate(KEYS):
                chk(f"{key} {k}", X[key][k], a[i] - b[i])
    for k, v in o["D_invalid_third"].items():
        a, b = read_d(v["run"]), read_d(runD["none"])
        for i, kk in enumerate(KEYS):
            chk(f"D_ref_invalid {k} {kk}", X[f"D_ref_invalid_third_{k}_minus_none"][kk], a[i] - b[i])
    if "B_vs_empty" in X:
        e = read_b(o["B"]["empty"]["run"])
        for arm, d in X["B_vs_empty"].items():
            x = read_b(o["B"][arm]["run"])
            for i, k in enumerate(KEYS):
                chk(f"B_vs_empty {arm} {k}", d[k], x[i] - e[i])
    if "B_vs_gt" in X:
        g = read_b(o["B"]["gt"]["run"])
        for arm, d in X["B_vs_gt"].items():
            x = read_b(o["B"][arm]["run"])
            for i, k in enumerate(KEYS):
                chk(f"B_vs_gt {arm} {k}", d[k], x[i] - g[i])
    for name, x, y in (("B_pred_noCF_minus_shuffle", "pred_noCF", "shuffle"), ("T_pred_noCF_minus_shuffle", "toolonly_pred_noCF", "toolonly_shuffle"),
                       ("T_minus_B_pred_noCF", "toolonly_pred_noCF", "pred_noCF")):
        if name in X:
            a, b = read_b(o["B"][x]["run"]), read_b(o["B"][y]["run"])
            for i, k in enumerate(KEYS):
                chk(f"{name} {k}", X[name][k], a[i] - b[i])
    return bad


def recompute_from_preds(o):
    """案 D は保存した予測から det_metrics.summary で計算し直し、metrics.json の値と比べる。"""
    sys.path.insert(0, str(M / "scripts"))
    from stage2pilot import det_metrics as DM
    ann_val = ANN / "instances_val.json"
    res = {}
    for k, v in o["D"].items():
        if not v.get("val_preds") or not Path(v["val_preds"]).exists():
            res[k] = None
            continue
        s = DM.summary(ann_val, DM.load_results(v["val_preds"]))
        res[k] = bool(abs(s["AP"] - v["AP"]) < 1e-12 and abs(s["target_AP"] - v["target_AP"]) < 1e-12
                      and abs(s["control_AP"] - v["control_AP"]) < 1e-12
                      and all(abs(s["per_video_AP"][vv] - v["per_video"][vv]) < 1e-12 for vv in v["per_video"]))
    return res


def cmd_verify(a):
    o = json.loads(Path(a.summary).read_text())
    bad = recompute(o)
    shifted = copy.deepcopy(o)
    if "B_vs_empty" in shifted["diffs"]:
        shifted["diffs"]["B_vs_empty"][next(iter(shifted["diffs"]["B_vs_empty"]))]["target_AP"] += 1e-6
    bad_ctrl_b = recompute(shifted)
    shifted = copy.deepcopy(o)
    shifted["diffs"]["D_gteach_minus_none"]["AP"] += 1e-6
    bad_ctrl_d = recompute(shifted)
    runs = [v["run"] for v in o["D"].values()] + [v["run"] for v in o["B"].values()]
    present = sum((P1 / r).is_dir() for r in runs)
    fake = sum((P1 / r).is_dir() for r in [f"{D_PFX}_no_such_arm_ep15_seed42", f"{B_PFX}_no_such_arm_ep4_seed42"])
    res = {"n_runs_in_summary": len(runs), "n_runs_present": present, "n_fake_runs_present": fake,
           "recompute_mismatches": bad, "recompute_equal": not bad, "preds_recompute_equal_D": recompute_from_preds(o),
           "control_shifted_1e-6_B_mismatches": bad_ctrl_b, "control_shifted_1e-6_D_mismatches": bad_ctrl_d,
           "control_detects": bool(bad_ctrl_b) and bool(bad_ctrl_d)}
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False))


def image_videos(ann_file, ids=None):
    d = json.loads(Path(ann_file).read_text())
    keep = None if ids is None else set(ids)
    return sorted({Path(im["file_name"]).stem.split("_")[0] for im in d["images"] if keep is None or im["id"] in keep})


def cmd_testcheck(a):
    sets = {}
    for k, n in {**D_ARMS, "none": D_NONE}.items():
        f = P1 / n / "metrics.json"
        if f.exists():
            vp = json.loads(f.read_text())["videos_passed"]
            sets[f"D {k} train"], sets[f"D {k} val"] = sorted(vp["train"]), sorted(vp["val"])
            sets[f"D {k} eval_test_overlap_recorded"] = vp.get("test_overlap")
    tr = image_videos(ANN / "instances_train.json")
    for arm in B_THIS:
        d = b_dir(arm)
        meta = d / "logs/eval_meta_val.json"
        sets[f"B {arm} train"] = tr
        sets[f"B {arm} val"] = image_videos(ANN / "instances_val.json", json.loads(meta.read_text())["image_ids"]) if meta.exists() else None
    pass_sets = {k: s for k, s in sets.items() if k.endswith((" train", " val"))}
    union = sorted({v for s in pass_sets.values() if s for v in s})
    res = {"sets": sets, "union": union, "test": sorted(TEST), "common": sorted(set(union) & TEST),
           "control_with_04": sorted((set(union) | {"04"}) & TEST), "missing_sets": [k for k, s in pass_sets.items() if s is None]}
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: res[k] for k in ("union", "common", "control_with_04", "missing_sets")}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("aggregate")
    g.add_argument("--out", required=True)
    g.add_argument("--tables", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--summary", required=True)
    v.add_argument("--out", required=True)
    t = sub.add_parser("testcheck")
    t.add_argument("--out", required=True)
    a = ap.parse_args()
    {"aggregate": cmd_aggregate, "verify": cmd_verify, "testcheck": cmd_testcheck}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())

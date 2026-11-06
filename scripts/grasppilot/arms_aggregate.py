"""集計・検算・test 不使用の確かめ（非公式 T-2026-11-06-grasp-pilot-arms、Task E、SPEC §6・§8 の f・g・h）。本体の .venv。読むだけ。

    aggregate --out <summary.json> --tables <tables.md>   全腕の値と差（Δ空・Δ入替・正解との差・動画ごと）、参考の表
    verify    --summary <summary.json> --out <json>       表の差を各 run の記録から別の経路で計算し直して一致を見る（判定 g）
                                                          対照: run の値を一つ 1e-6 ずらした写しで不一致。存在しない run の名前で 0 件（判定 f）
    testcheck --out <json>                                学習と評価に通した動画の集合と {04, 05, 07} の共通（判定 h）
                                                          対照: 集合に 04 を混ぜた入力で共通 1 件

読み方の規則（SPEC §6.2）: seed は一つ。差は 1 本ずつの差として書き、陽性・陰性・有意などの語は使わない。
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

M = Path(__file__).resolve().parents[2]
P1 = M / "experiments/phase1"
TASK_ID = "T-2026-11-06-grasp-pilot-arms"
TEST = {"04", "05", "07"}
ANN = M / "data/annotations/egosurgery_tool_folds/A"
SIX = ["anesthesia", "closure", "design", "dissection", "hemostasis", "incision"]   # val に現れる 7 工程から dressing を除く
A_ARMS = ["empty", "gt", "pred_noCF", "pred_CF", "gtpred_CF", "shuffle"]
B_ARMS = ["pred_noCF", "pred_CF", "gtpred_CF", "shuffle"]
T_ARMS = ["toolonly_pred_noCF", "toolonly_shuffle"]
TARGET = ["Skewer", "Bipolar Forceps", "Scalpel", "Syringe", "Raspatory"]
CONTROL = ["Gauze", "Mouth Gag", "Suction Cannula", "Tweezers"]


def a_run(arm):
    hits = sorted(P1.glob(f"grasparms_dp_*_GA-noflag_{arm}_ep4_seed42"))
    return hits[-1] if hits else None


def b_run(arm, second=False):
    d = P1 / (f"grasppilot2_B_{arm}_ep4_seed42" if second else f"grasparms_B_{arm}_ep4_seed42")
    return d if (d / "grasppilot_metrics.json").exists() else None


def a_values(d):
    m = json.loads((d / "metrics.json").read_text())
    pc = json.loads((d / "per_class_ap.json").read_text())
    h = json.loads((d / "logs/history.json").read_text())
    return {"run": d.name, "jaccard": m["phase_jaccard"], "accuracy": m["phase_accuracy"],
            "six_mean": sum(pc[k] for k in SIX) / len(SIX), "per_class": pc,
            "per_video": {v: {"jaccard": x["phase_jaccard"], "accuracy": x["phase_accuracy"]} for v, x in m["per_video"].items()},
            "epochs": [{k: e[k] for k in ("epoch", "train_loss", "val_jaccard", "val_accuracy", "iface_max_abs", "iface_l2")
                        if k in e} for e in h],
            "result_epoch": m.get("result_epoch"), "receiver_unchanged": m.get("receiver_unchanged"),
            "elapsed_seconds": m.get("elapsed_seconds")}


def b_values(d):
    m = json.loads((d / "grasppilot_metrics.json").read_text())
    t0 = (d / "start.txt").read_text().strip() if (d / "start.txt").exists() else None
    t1 = (d / "end.txt").read_text().strip() if (d / "end.txt").exists() else None
    host = None
    for f in ("host.txt", "server.txt"):
        if (d / f).exists():
            host = (d / f).read_text().strip()
            break
    return {"run": d.name, "AP": m["AP"], "target_AP": m["target_AP"], "control_AP": m["control_AP"],
            "target_missing": m["target_missing"], "control_missing": m["control_missing"],
            "per_class": m["per_class_ap"], "per_video": m["per_video_AP"], "per_epoch_mAP": m["per_epoch_mAP"],
            "iface_weight_by_epoch": m["iface_weight_by_epoch"], "init": m["init"], "result_epoch": m["result_epoch"],
            "frozen_unchanged": m["frozen_unchanged"], "start": t0, "end": t1, "host": host}


def diff(a, b, keys):
    return {k: a[k] - b[k] for k in keys}


def vdiff(a, b, key=None):
    return {v: (a[v][key] - b[v][key]) if key else (a[v] - b[v]) for v in a}


def cmd_aggregate(a):
    A = {arm: a_values(d) for arm in A_ARMS if (d := a_run(arm))}
    B = {arm: b_values(d) for arm in B_ARMS + T_ARMS if (d := b_run(arm))}
    B2 = {arm: b_values(b_run(arm, True)) for arm in ("empty", "gt")}
    ak = ["jaccard", "accuracy", "six_mean"]
    bk = ["AP", "target_AP", "control_AP"]
    out = {"task_id": TASK_ID, "unofficial": True, "six_phases": SIX, "missing_A": [x for x in A_ARMS if x not in A],
           "missing_B": [x for x in B_ARMS + T_ARMS if x not in B], "A": A, "B": B, "B_second": B2, "diffs": {}}
    D = out["diffs"]
    if "empty" in A:
        D["A_vs_empty"] = {arm: diff(v, A["empty"], ak) for arm, v in A.items() if arm != "empty"}
        D["A_vs_empty_per_video"] = {arm: {k: vdiff(v["per_video"], A["empty"]["per_video"], k) for k in ("jaccard", "accuracy")}
                                     for arm, v in A.items() if arm != "empty"}
        D["A_vs_empty_per_class"] = {arm: {c: v["per_class"][c] - A["empty"]["per_class"][c] for c in v["per_class"]}
                                     for arm, v in A.items() if arm != "empty"}
    if {"pred_noCF", "shuffle"} <= set(A):
        D["A_pred_noCF_minus_shuffle"] = diff(A["pred_noCF"], A["shuffle"], ak)
        D["A_pred_noCF_minus_shuffle_per_video"] = {k: vdiff(A["pred_noCF"]["per_video"], A["shuffle"]["per_video"], k)
                                                    for k in ("jaccard", "accuracy")}
    if {"pred_noCF", "gt"} <= set(A):
        D["A_pred_noCF_minus_gt"] = diff(A["pred_noCF"], A["gt"], ak)
        D["A_pred_noCF_minus_gt_per_video"] = {k: vdiff(A["pred_noCF"]["per_video"], A["gt"]["per_video"], k)
                                               for k in ("jaccard", "accuracy")}
    e, g = B2["empty"], B2["gt"]
    D["B_vs_empty"] = {arm: diff(v, e, bk) for arm, v in B.items()}
    D["B_vs_empty_per_video"] = {arm: vdiff(v["per_video"], e["per_video"]) for arm, v in B.items()}
    D["B_vs_empty_per_class"] = {arm: {c: (v["per_class"][c] - e["per_class"][c]) if v["per_class"][c] is not None
                                       and e["per_class"][c] is not None else None for c in v["per_class"]} for arm, v in B.items()}
    D["B_gt_second_vs_empty"] = diff(g, e, bk)
    for x, y, name in (("pred_noCF", "shuffle", "B_pred_noCF_minus_shuffle"),
                       ("toolonly_pred_noCF", "toolonly_shuffle", "T_pred_noCF_minus_shuffle"),
                       ("toolonly_pred_noCF", "pred_noCF", "T_minus_B_pred_noCF")):
        if {x, y} <= set(B):
            D[name] = diff(B[x], B[y], bk)
            D[name + "_per_video"] = vdiff(B[x]["per_video"], B[y]["per_video"])
    if "pred_noCF" in B:
        D["B_pred_noCF_minus_gt_second"] = diff(B["pred_noCF"], g, bk)
        D["B_pred_noCF_minus_gt_second_per_video"] = vdiff(B["pred_noCF"]["per_video"], g["per_video"])
    # 参考: 一本目の案 A（旗あり 30 次元。設計が違う）
    ref = {}
    for arm, name in (("empty", "grasppilot_dp_001_GA_empty_ep4_seed42"), ("gt", "grasppilot_dp_002_GA_gt_ep4_seed42")):
        if (P1 / name / "metrics.json").exists():
            ref[arm] = a_values(P1 / name)
    out["A_first_reference_flag30"] = ref
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    Path(a.tables).write_text(tables(out))
    print(json.dumps({"missing_A": out["missing_A"], "missing_B": out["missing_B"]}, ensure_ascii=False))


def f7(x):
    return "—" if x is None else f"{x:.7f}"


def s7(x):
    return "—" if x is None else f"{x:+.7f}"


def tables(o):
    A, B, B2, D = o["A"], o["B"], o["B_second"], o["diffs"]
    L = ["<!-- scripts/grasppilot/arms_aggregate.py aggregate が書く。手で直さない -->", ""]
    L += ["### 案 A（旗なし 28 次元、W1、val 09・10）", "",
          "| 腕 | macro Jaccard | accuracy | 6 工程の平均 | Δ空 Jaccard | Δ空 accuracy | Δ空 6 工程 | run |", "|---|---|---|---|---|---|---|---|"]
    for arm in A_ARMS:
        if arm in A:
            v = A[arm]
            d = D.get("A_vs_empty", {}).get(arm, {})
            L.append(f"| {arm} | {f7(v['jaccard'])} | {f7(v['accuracy'])} | {f7(v['six_mean'])} | {s7(d.get('jaccard'))} | "
                     f"{s7(d.get('accuracy'))} | {s7(d.get('six_mean'))} | `{v['run']}` |")
    L += ["", "| 差 | Jaccard | accuracy | 6 工程の平均 | 09 Jaccard | 10 Jaccard | 09 accuracy | 10 accuracy |", "|---|---|---|---|---|---|---|---|"]
    for name, label in (("A_pred_noCF_minus_shuffle", "Δ入替（予測-noCF − 入れ替え）"), ("A_pred_noCF_minus_gt", "正解との差（予測-noCF − 正解）")):
        if name in D:
            d, pv = D[name], D[name + "_per_video"]
            L.append(f"| {label} | {s7(d['jaccard'])} | {s7(d['accuracy'])} | {s7(d['six_mean'])} | {s7(pv['jaccard']['09'])} | "
                     f"{s7(pv['jaccard']['10'])} | {s7(pv['accuracy']['09'])} | {s7(pv['accuracy']['10'])} |")
    L += ["", "Δ空 の動画ごと（Jaccard / accuracy）:", "", "| 腕 | 09 | 10 |", "|---|---|---|"]
    for arm, pv in D.get("A_vs_empty_per_video", {}).items():
        L.append(f"| {arm} | {s7(pv['jaccard']['09'])} / {s7(pv['accuracy']['09'])} | {s7(pv['jaccard']['10'])} / {s7(pv['accuracy']['10'])} |")
    names = list(next(iter(A.values()))["per_class"]) if A else []
    L += ["", "クラス別 Jaccard（val に現れない disinfection・irrigation は 0 のまま。macro の平均に入らない）:", "",
          "| 腕 | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for arm in A_ARMS:
        if arm in A:
            L.append(f"| {arm} | " + " | ".join(f"{A[arm]['per_class'][c]:.4f}" for c in names) + " |")
    L += ["", "epoch ごとの val（Jaccard / accuracy / 界面の重みの絶対値の最大 / L2）:", "", "| 腕 | epoch 1 | 2 | 3 | 4 |", "|---|---|---|---|---|"]
    for arm in A_ARMS:
        if arm in A:
            L.append(f"| {arm} | " + " | ".join(f"{e['val_jaccard']:.4f} / {e['val_accuracy']:.4f} / {e['iface_max_abs']:.4f} / {e['iface_l2']:.3f}"
                                               for e in A[arm]["epochs"]) + " |")
    L += ["", "### 案 B と術具だけ（W1、val 09・10。空と正解は二本目の run）", "",
          "| 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | Δ空 overall | Δ空 標的群 | Δ空 陰性対照群 | run |", "|---|---|---|---|---|---|---|---|"]
    rows = [("empty（二本目）", B2["empty"], None), ("gt（二本目）", B2["gt"], D["B_gt_second_vs_empty"])]
    rows += [(arm, B[arm], D["B_vs_empty"][arm]) for arm in B_ARMS + T_ARMS if arm in B]
    for label, v, d in rows:
        d = d or {}
        L.append(f"| {label} | {f7(v['AP'])} | {f7(v['target_AP'])} | {f7(v['control_AP'])} | {s7(d.get('AP'))} | "
                 f"{s7(d.get('target_AP'))} | {s7(d.get('control_AP'))} | `{v['run']}` |")
    L += ["", "| 差 | overall | 標的群 | 陰性対照群 | 09 | 10 |", "|---|---|---|---|---|---|"]
    for name, label in (("B_pred_noCF_minus_shuffle", "案 B Δ入替（予測-noCF − 入れ替え）"),
                        ("B_pred_noCF_minus_gt_second", "案 B 正解との差（予測-noCF − 二本目の正解）"),
                        ("T_pred_noCF_minus_shuffle", "術具だけ Δ入替（予測-noCF − 入れ替え）"),
                        ("T_minus_B_pred_noCF", "誰の手かの情報による差（術具だけ − 案 B、予測-noCF）")):
        if name in D:
            d, pv = D[name], D[name + "_per_video"]
            L.append(f"| {label} | {s7(d['AP'])} | {s7(d['target_AP'])} | {s7(d['control_AP'])} | {s7(pv['09'])} | {s7(pv['10'])} |")
    L += ["", "Δ空 の動画ごとの mAP:", "", "| 腕 | 09 | 10 |", "|---|---|---|"]
    for arm, pv in D["B_vs_empty_per_video"].items():
        L.append(f"| {arm} | {s7(pv['09'])} | {s7(pv['10'])} |")
    cls = list(B2["empty"]["per_class"])
    L += ["", "クラス別 AP（標的群 = " + "・".join(TARGET) + "、陰性対照群 = " + "・".join(CONTROL) + "）:", "",
          "| 腕 | " + " | ".join(cls) + " |", "|---|" + "---|" * len(cls)]
    for label, v, _ in rows:
        L.append(f"| {label} | " + " | ".join("—" if v["per_class"][c] is None else f"{v['per_class'][c]:.4f}" for c in cls) + " |")
    L += ["", "epoch ごとの val mAP（−1 は学習前）と界面の重みの絶対値の最大:", "", "| 腕 | −1 | 0 | 1 | 2 | 3 | 重み 3 |", "|---|---|---|---|---|---|---|"]
    for label, v, _ in rows:
        pe, w = v["per_epoch_mAP"], v["iface_weight_by_epoch"]
        L.append(f"| {label} | " + " | ".join(f"{pe[k]:.4f}" if k in pe else "—" for k in ("-1", "0", "1", "2", "3"))
                 + f" | {w.get('3', {}).get('iface_max_abs', float('nan')):.4f} |")
    ref = o["A_first_reference_flag30"]
    if ref:
        L += ["", "### 参考: 一本目の案 A（旗あり 30 次元。設計が違うので差は取らない）", "",
              "| 腕 | macro Jaccard | accuracy | 6 工程の平均 | run |", "|---|---|---|---|---|"]
        for arm, v in ref.items():
            L.append(f"| {arm} | {f7(v['jaccard'])} | {f7(v['accuracy'])} | {f7(v['six_mean'])} | `{v['run']}` |")
    return "\n".join(L) + "\n"


def recompute(o):
    """summary の差を、各 run の記録のファイルを読み直して別の経路で計算する（判定 g）。"""
    bad = []

    def chk(name, got, want):
        if abs(got - want) > 1e-12:
            bad.append(f"{name}: {got} != {want}")

    def read_a(arm):
        d = P1 / o["A"][arm]["run"]
        m = json.loads((d / "metrics.json").read_text())
        pc = json.loads((d / "per_class_ap.json").read_text())
        return m["phase_jaccard"], m["phase_accuracy"], sum(pc[k] for k in SIX) / 6

    def read_b(arm, second=False):
        name = o["B_second"][arm]["run"] if second else o["B"][arm]["run"]
        m = json.loads((P1 / name / "grasppilot_metrics.json").read_text())
        return m["AP"], m["target_AP"], m["control_AP"]

    D = o["diffs"]
    if "empty" in o["A"]:
        e = read_a("empty")
        for arm, d in D.get("A_vs_empty", {}).items():
            x = read_a(arm)
            for i, k in enumerate(("jaccard", "accuracy", "six_mean")):
                chk(f"A {arm} {k}", d[k], x[i] - e[i])
    eb = read_b("empty", True)
    for arm, d in D["B_vs_empty"].items():
        x = read_b(arm)
        for i, k in enumerate(("AP", "target_AP", "control_AP")):
            chk(f"B {arm} {k}", d[k], x[i] - eb[i])
    for name, x, y in (("B_pred_noCF_minus_shuffle", "pred_noCF", "shuffle"), ("T_pred_noCF_minus_shuffle", "toolonly_pred_noCF", "toolonly_shuffle"),
                       ("T_minus_B_pred_noCF", "toolonly_pred_noCF", "pred_noCF")):
        if name in D:
            a, b = read_b(x), read_b(y)
            for i, k in enumerate(("AP", "target_AP", "control_AP")):
                chk(f"{name} {k}", D[name][k], a[i] - b[i])
    for name, x, y in (("A_pred_noCF_minus_shuffle", "pred_noCF", "shuffle"), ("A_pred_noCF_minus_gt", "pred_noCF", "gt")):
        if name in D:
            a, b = read_a(x), read_a(y)
            for i, k in enumerate(("jaccard", "accuracy", "six_mean")):
                chk(f"{name} {k}", D[name][k], a[i] - b[i])
    return bad


def cmd_verify(a):
    o = json.loads(Path(a.summary).read_text())
    bad = recompute(o)
    shifted = copy.deepcopy(o)
    arm = next(iter(shifted["diffs"]["B_vs_empty"]))
    shifted["diffs"]["B_vs_empty"][arm]["target_AP"] += 1e-6
    bad_ctrl = recompute(shifted)
    runs = [v["run"] for v in o["A"].values()] + [v["run"] for v in o["B"].values()]
    present = sum((P1 / r).is_dir() for r in runs)
    fake = sum((P1 / r).is_dir() for r in ["grasparms_B_no_such_arm_ep4_seed42", "grasparms_dp_999_GA-noflag_none_ep4_seed42"])
    res = {"n_runs_in_summary": len(runs), "n_runs_present": present, "n_fake_runs_present": fake,
           "recompute_mismatches": bad, "recompute_equal": not bad,
           "control_shifted_1e-6_mismatches": bad_ctrl, "control_detects": bool(bad_ctrl)}
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps(res, ensure_ascii=False))


def image_videos(ann_file, ids=None):
    d = json.loads(Path(ann_file).read_text())
    keep = None if ids is None else set(ids)
    return sorted({Path(im["file_name"]).stem.split("_")[0] for im in d["images"] if keep is None or im["id"] in keep})


def cmd_testcheck(a):
    sets = {}
    for arm in A_ARMS:
        d = a_run(arm)
        if d:
            import yaml
            cfg = yaml.safe_load((d / "config.yaml").read_text())
            vids = cfg.get("videos") or cfg.get("config", {}).get("videos")
            sets[f"A {arm} train"] = sorted(vids["train"])
            sets[f"A {arm} val"] = sorted(vids["val"])
    tr = image_videos(ANN / "instances_train.json")
    for arm in B_ARMS + T_ARMS:
        d = b_run(arm) or (P1 / f"grasparms_B_{arm}_ep4_seed42")
        meta = d / "logs/eval_meta_val.json"
        sets[f"B {arm} train"] = tr
        sets[f"B {arm} val"] = image_videos(ANN / "instances_val.json", json.loads(meta.read_text())["image_ids"]) if meta.exists() else None
    union = sorted({v for s in sets.values() if s for v in s})
    res = {"sets": sets, "union": union, "test": sorted(TEST), "common": sorted(set(union) & TEST),
           "control_with_04": sorted((set(union) | {"04"}) & TEST), "missing_sets": [k for k, s in sets.items() if s is None]}
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

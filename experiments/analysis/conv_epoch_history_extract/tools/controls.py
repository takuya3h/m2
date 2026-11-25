"""陽性対照（SPEC §8 の「空振りでないことの確認」）。写しはすべてメモリの中で作る。記録のファイルは読むだけ。

    .venv/bin/python experiments/analysis/conv_epoch_history_extract/tools/ceh.py controls
"""
from __future__ import annotations

import copy
import csv
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ceh  # noqa: E402

OUT = ceh.OUT
res = {}

# a: 存在しない実行ファイルの経路で、列挙が 0 件になる（開始時の compute の列挙の道具）
pe = ceh.ROOT / "scripts/grasppilot/proc_enum.py"
def enum(exe):
    out = subprocess.run([sys.executable, str(pe), "--match-exe", exe], capture_output=True, text=True, check=True).stdout
    return json.loads(out)["count"]
res["a"] = {"nonexistent_count": enum("/nonexistent/bin/python9"), "zsh_count": enum("/usr/bin/zsh")}

# b: 存在しない run の名前を一つ足した集合で不一致、history.json を一つ外した写しで欠け 1 件
sets = ceh.jload(OUT / "start/sets.json")
rec = ceh.record_sets()
obs = {}
for name in sets["conv_runs"] + sets["fixed_runs"]:
    d = ceh.P1 / name
    obs.setdefault(ceh.group_of(ceh.task_of(d), ceh.prefix_of(d)), set()).add(ceh.observed_key(name, ceh.prefix_of(d)))
base = ceh.compare_sets(obs, rec)
obs2 = copy.deepcopy(obs)
obs2["GP"].add(("grasp_hand_graph_arm", "GR-W9-N10-L1_DGH_conv"))
bad = ceh.compare_sets(obs2, rec)
conv_runs, fixed_runs = ceh.load_sets()
cr2 = copy.deepcopy(conv_runs[:5])
cr2[2]["hist"] = None
res["b"] = {"base_all_equal": all(v["equal"] for v in base.values()), "added_equal_GP": bad["GP"]["equal"],
            "added_only_observed": bad["GP"]["only_observed"], "missing_base": len(ceh.history_missing(conv_runs)),
            "missing_after_removal": len(ceh.history_missing(cr2))}

# c: 一つの run の history の写しの値を 1e-6 ずらすと突き合わせが不一致
r = copy.deepcopy(conv_runs[0])
c0, _ = ceh.reconcile(r)
r["hist"][r["metrics"]["result_epoch"] - 1]["val_jaccard"] += 1e-6
c1, _ = ceh.reconcile(r)
r2 = copy.deepcopy(conv_runs[0])
r2["hist"][-1]["val_accuracy"] += 1e-6
c2, _ = ceh.reconcile(r2)
r3 = copy.deepcopy(conv_runs[0])
r3["hist"].append(dict(r3["hist"][-1], epoch=len(r3["hist"]) + 1))
c3, _ = ceh.reconcile(r3)
res["c"] = {"run": r["name"], "base_all": all(c0.values()), "shift_result_jaccard_ok": c1["result_jaccard"],
            "shift_last_accuracy_ok": c2["last_accuracy"], "extra_epoch_n_epochs_ok": c3["n_epochs"]}

# d: 学習率を下げた回を 3 にした写しで、4 epoch 目が下げた後と印付けされ、学習率の欄との食い違いが出る
r = copy.deepcopy(conv_runs[0])
r["metrics"]["lr_drop_epoch"] = 3
res["d"] = {"mark_epoch4_drop3": ceh.phase_mark(4, 3), "mark_epoch4_real": ceh.phase_mark(4, conv_runs[0]["metrics"]["lr_drop_epoch"]),
            "lr_marks_agree_after_edit": ceh.lr_marks(r)["agree"], "lr_marks_agree_real": ceh.lr_marks(conv_runs[0])["agree"]}

# e: 片方の値を 1e-6 ずらした写しでちょうど同じ対の数が減る。違う W の run を対にした写しで差が出る
pairs = ceh.make_pairs(conv_runs, fixed_runs)
n0 = sum(ceh.compare_pair(c, f)["ep"][4]["eq_j"] for c, f in pairs)
c, f = pairs[0]
f2 = copy.deepcopy(f)
f2["ep"][4]["phase_jaccard"] += 1e-6
shifted = [(c, f2)] + pairs[1:]
n1 = sum(ceh.compare_pair(a, b)["ep"][4]["eq_j"] for a, b in shifted)
# 違う W: 収束規則の W1 の DGH s1 と、固定の長さの W2 の DGH-CF s1
cw = next(x for x in conv_runs if x["cfg"]["task_id"] == ceh.GP and x["cfg"]["scope"] == "W1" and x["cfg"]["arm"] == "DGH"
          and x["cfg"]["gr"]["N"] == 10 and x["cfg"]["gr"]["L"] == 1)
fw = next(x for x in fixed_runs if x["cfg"]["type"] == "GR" and x["cfg"]["scope"] == "W2" and x["cfg"]["arm"] == "DGH-CF"
          and x["cfg"]["gr"]["N"] == 10 and x["cfg"]["gr"]["L"] == 1)
wrong = ceh.compare_pair(cw, fw)
res["e"] = {"n_eq_j_ep4_base": n0, "n_eq_j_ep4_shifted": n1,
            "wrong_W_dj_ep4": wrong["ep"][4]["dj"], "wrong_W_da_ep4": wrong["ep"][4]["da"],
            "wrong_W_config_other": wrong["config_diff"]["other"], "wrong_W_in_pair_list": any(p[0] is cw and p[1] is fw for p in pairs)}

# f: 表の値を記録から測り直す（epochs.csv を通らず、各 run の history.json と metrics_ep を直接読む）。1e-6 ずらした写しを検出する
T = ceh.jload(OUT / "c/tables.json")
hist = {}
for x in conv_runs:
    cfg = x["cfg"]
    hist[(cfg["type"], cfg["scope"], ceh.SETTINGS[(cfg["gr"]["N"], cfg["gr"]["L"])], ceh.arm_class(cfg["task_id"], cfg["arm"]))] = {
        h["epoch"]: (h["val_jaccard"], h["val_accuracy"]) for h in x["hist"]}
BORROW = {}   # irn-hice-htt-pilot の SPEC §5.2 の流用を、表の道具とは別に書き下す
for t in ("IRN", "HiCE", "HTT"):
    for sc in ceh.SCOPES:
        for st in ("s2", "s3", "s4"):
            BORROW[(t, sc, st, "A0")] = (t, sc, "s1", "A0")
for sc in ceh.SCOPES:
    for st in ("s1", "s2", "s3", "s4"):
        BORROW[("HiCE", sc, st, "D")] = ("HiCE", sc, "s1", "A0")
    BORROW[("HiCE", sc, "s3", "DH")] = ("HiCE", sc, "s1", "DH")
    BORROW[("HiCE", sc, "s4", "DH")] = ("HiCE", sc, "s2", "DH")
def hv(t, sc, st, arm, e):
    k = BORROW.get((t, sc, st, arm), (t, sc, st, arm))
    return hist[k][e]
dev52 = dev53 = dev54 = 0.0
n52 = n53 = n54 = 0
for key, c in T["52"].items():
    t, sc, arm, st = key.split("|")
    for e in ceh.EPOCHS:
        j, a = hv(t, sc, st, arm, e)
        dev52 = max(dev52, abs(c[str(e)]["j"] - j), abs(c[str(e)]["a"] - a))
        n52 += 1
for key, c in T["53"].items():
    t, sc, xy, st = key.split("|")
    x, y = {f"{a}-{b}": (a, b) for a, b in ceh.DIFFS_53}[xy]
    for e in ceh.EPOCHS:
        dev53 = max(dev53, abs(c[str(e)]["dj"] - (hv(t, sc, st, x, e)[0] - hv(t, sc, st, y, e)[0])),
                    abs(c[str(e)]["da"] - (hv(t, sc, st, x, e)[1] - hv(t, sc, st, y, e)[1])))
        n53 += 1
fx = {}
for x in fixed_runs:
    cfg = x["cfg"]
    k = (cfg["scope"], cfg["type"], ceh.SETTINGS.get(((cfg.get("gr") or {}).get("N"), (cfg.get("gr") or {}).get("L"))), cfg["arm"])
    fx[k] = {e: (x["ep"][e]["phase_jaccard"], x["ep"][e]["phase_accuracy"]) for e in ceh.EPOCHS}
def fv(sc, t, st, arm, e):
    if t == "GR":
        if arm == "empty":
            st = "s1"
        elif arm in ("D-CF", "D-noCF", "D-S", "DG-CF", "DG-noCF", "DG-S", "DH-CF", "DH-noCF", "DH-S") and st in ("s2", "s4"):
            st = {"s2": "s1", "s4": "s3"}[st]
        return fx[(sc, "GR", st, arm)][e]
    return fx[(sc, t, None, arm)][e]
for key, c in T["54"].items():
    sc, grp, t, d, st = key.split("|")
    x, y = [s.strip() for s in d.split("−")]
    for e in ceh.EPOCHS:
        if grp == "収束規則":
            vx, vy = hv(t, sc, st, x, e), hv(t, sc, st, "A0", e)
        else:
            nm = {"空": "empty", "入れ替え": "shuffle", "予測-noCF": "pred_noCF"}
            vx, vy = fv(sc, t, st, nm.get(x, x), e), fv(sc, t, st, nm.get(y, y), e)
        dev54 = max(dev54, abs(c[str(e)]["dj"] - (vx[0] - vy[0])), abs(c[str(e)]["da"] - (vx[1] - vy[1])))
        n54 += 1
T2 = copy.deepcopy(T)
k0 = next(iter(T2["53"]))
T2["53"][k0]["4"]["dj"] += 1e-6
t, sc, xy, st = k0.split("|")
x, y = {f"{a}-{b}": (a, b) for a, b in ceh.DIFFS_53}[xy]
shift_dev = abs(T2["53"][k0]["4"]["dj"] - (hv(t, sc, st, x, 4)[0] - hv(t, sc, st, y, 4)[0]))
# epochs.csv の値と history.json の値も比べる（csv は repr で書いた）
dev_csv = 0.0
with open(OUT / "epochs.csv") as fh:
    for row in csv.DictReader(fh):
        j, a = hist[(row["type"], row["scope"], row["setting"], row["arm_class"])][int(row["epoch"])]
        dev_csv = max(dev_csv, abs(float(row["val_jaccard"]) - j), abs(float(row["val_accuracy"]) - a))
res["f"] = {"n52": n52, "n53": n53, "n54": n54, "max_dev_52": dev52, "max_dev_53": dev53, "max_dev_54": dev54,
            "max_dev_csv_vs_history": dev_csv, "shifted_copy_dev": shift_dev, "shifted_detected": shift_dev > 0}

# g: 流用の確かめの片方を 1e-6 ずらした写しで一致の検査が不一致を返す
rows = ceh.chk_compares(conv_runs, fixed_runs)
a_run = next(x for x in conv_runs if x["name"] == rows[0]["a"])
a2 = copy.deepcopy(a_run)
a2["hist"][3]["val_jaccard"] += 1e-6
j1, _ = ceh.conv_val(a2, 4)
j0, _ = ceh.conv_val(next(x for x in conv_runs if x["name"] == rows[0]["b"]), 4)
res["g"] = {"n_rows": len(rows), "n_eq": sum(r["eq"] for r in rows), "shifted_eq": j1 == j0}

# h: 新しいファイルを一つ加えた目録で追加 1
m0 = ceh.jload(OUT / "start/hashes_start.json")
m1 = dict(m0)
m1["experiments/phase1/zzz_fake/metrics.json"] = "0" * 64
res["h"] = {"added_control": len(ceh.diff_manifest(m0, m1)["added"]), "self_diff": ceh.diff_manifest(m0, m0)}

(OUT / "c").mkdir(exist_ok=True)
(OUT / "c/controls.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(json.dumps(res, ensure_ascii=False))

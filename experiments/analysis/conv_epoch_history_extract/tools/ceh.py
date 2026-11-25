"""収束規則の run の epoch ごとの val を取り出し、固定の長さの run と並べる（非公式 T-2026-11-22-conv-epoch-history-extract）。

読むだけ。学習・評価・推論をしない。書くのは experiments/analysis/conv_epoch_history_extract/ の下だけ。

    .venv/bin/python experiments/analysis/conv_epoch_history_extract/tools/ceh.py <cmd>

cmd:
  sets          SPEC §3 の三つの集合を作り、三つの契約の記録（run の一覧の道具と RESULT の本数）と比べる → start/sets.json
  hashes OUT    読む記録の sha256 の目録を OUT へ書く
  extract       SPEC §4 の epochs.csv と、history.json と版管理の中の記録の突き合わせ（完了判定 c・d）→ b/checks.json
  pairs         SPEC §3 の対と §5.1 の一致の確かめ、流用の確かめ（完了判定 e・g）→ b/pairs.json
  report        SPEC §5 の表を epochs.csv と固定の長さの記録から作る → REPORT.md、c/tables.json
  controls      陽性対照（完了判定 a〜h の「空振りでないことの確認」）→ c/controls.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import runpy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
P1 = ROOT / "experiments/phase1"
OUT = ROOT / "experiments/analysis/conv_epoch_history_extract"
GP = "T-2026-11-20-grasp-hand-graph-pilot"
IHH = "T-2026-11-21-grasp-hand-irn-hice-htt-pilot"
T2P = "T-2026-11-21-grasp-hand-graph-t2p-match"
CONV_PREFIX = {GP: {"grasp_hand_graph_arm"}, IHH: {"grasp_hand_irn_hice_htt_arm", "grasp_hand_irn_hice_htt_chk"}}
FIX_PREFIX = {"grasp_hand_graph_t2p_gr", "grasp_hand_graph_t2p_tp_W1", "grasp_hand_graph_t2p_tp_W2", "grasp_hand_graph_t2p_tp_W3"}
RECORD_COUNTS = {"GP": 96, "IHH": 248, "T2P_GR": 147, "T2P_TP": 36}   # 三つの契約の RESULT §1・§5.2・§5.4 の本数
SETTINGS = {(10, 1): "s1", (10, 2): "s2", (30, 1): "s3", (30, 2): "s4"}
SCOPES = ("W1", "W2", "W3")
EPOCHS = (4, 8, 12, 16)
ARMS = ("A0", "D", "DG", "DH", "DGH", "DGH-U", "DGH-noCF", "DGH-GT")
TYPES = ("GR", "IRN", "HiCE", "HTT")
TP_TYPES = ("D1-L1", "D1-L2", "D2", "D3-L2")
READ_WIDTH = 0.015
LENGTH_KEYS = re.compile(r"^(stop_rule(\.|$)|record_epochs$|steps_per_epoch$|optim_groups|iface_last_init|result_selection$)")
IDENT_KEYS = re.compile(r"^(task_id|unofficial|arm|gr\.dir)$|^signals_(train|val)\[\d+\]\.path$")


# ---------- 読み込み ----------

def jload(p):
    with open(p) as f:
        return json.load(f)


def prefix_of(d: Path):
    m = re.search(r"--exp-prefix (\S+)", (d / "command.sh").read_text())
    return m.group(1) if m else None


def task_of(d: Path):
    p = d / "config.yaml"
    if not p.is_file():
        return None
    with open(p) as f:
        first = f.readline()
    m = re.match(r"task_id: (\S+)", first)
    return m.group(1) if m else None


def load_run(d: Path):
    r = {"name": d.name, "dir": d, "cfg": yaml.safe_load((d / "config.yaml").read_text()), "prefix": prefix_of(d)}
    r["metrics"] = jload(d / "metrics.json")
    r["metrics_last"] = jload(d / "metrics_last.json") if (d / "metrics_last.json").is_file() else None
    r["hist"] = jload(d / "logs/history.json") if (d / "logs/history.json").is_file() else None
    r["ep"] = {e: jload(d / f"metrics_ep{e}.json") for e in EPOCHS if (d / f"metrics_ep{e}.json").is_file()}
    return r


def scan():
    by_task = {GP: [], IHH: [], T2P: []}
    for d in sorted(P1.iterdir()):
        t = task_of(d) if d.is_dir() else None
        if t in by_task:
            by_task[t].append(d)
    return by_task


def members(by_task):
    conv, fixed, excluded = [], [], []
    for t in (GP, IHH):
        for d in by_task[t]:
            m = jload(d / "metrics.json") if (d / "metrics.json").is_file() else {}
            pf = prefix_of(d)
            if "converge" in m and pf in CONV_PREFIX[t]:
                conv.append((t, d))
            else:
                excluded.append({"task": t, "run": d.name, "prefix": pf, "converge": "converge" in m})
    for d in by_task[T2P]:
        pf = prefix_of(d)
        if (d / "metrics_ep4.json").is_file() and pf in FIX_PREFIX:
            fixed.append((T2P, d))
        else:
            excluded.append({"task": T2P, "run": d.name, "prefix": pf, "has_ep4": (d / "metrics_ep4.json").is_file()})
    return conv, fixed, excluded


def record_sets():
    """三つの契約の run の一覧の道具から、(接頭辞, 名前) の集合を作る。"""
    gp = set()
    for sc in SCOPES:      # experiments/analysis/grasp_hand_graph_pilot/tools/run_arms.sh の繰り返しと同じ
        for n, ell in ((10, 1), (10, 2), (30, 1), (30, 2)):
            for arm in ("empty", "D", "DG", "DH", "DGH", "DGH-U", "DGH-noCF", "DGH-GT"):
                gp.add(("grasp_hand_graph_arm", f"GR-{sc}-N{n}-L{ell}_{arm}_conv"))
    ihh_mod = runpy.run_path(str(ROOT / "experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/jobs.py"))
    ihh = {(j.split("|")[1], j.split("|")[0]) for j in ihh_mod["chk_jobs"]() + ihh_mod["main_jobs"]()}
    t2p_mod = runpy.run_path(str(ROOT / "experiments/analysis/grasp_hand_graph_t2p/tools/jobs.py"))
    long_ = t2p_mod["LONG"]
    gr = {(j.split("|")[1], j.split("|")[0]) for j in t2p_mod["graph_jobs"](long_, "grasp_hand_graph_t2p_gr")}
    tp = {(j.split("|")[1], j.split("|")[0]) for j in t2p_mod["tp_jobs"](long_, "grasp_hand_graph_t2p_tp")}
    return {"GP": gp, "IHH": ihh, "T2P_GR": gr, "T2P_TP": tp}


def observed_key(name, prefix):
    m = re.match(rf"^{re.escape(prefix)}_\d{{3}}_(.+)_seed42$", name)
    return (prefix, m.group(1)) if m else (prefix, f"<unparsed>{name}")


def group_of(task, prefix):
    if task == GP:
        return "GP"
    if task == IHH:
        return "IHH"
    return "T2P_GR" if prefix == "grasp_hand_graph_t2p_gr" else "T2P_TP"


def compare_sets(obs, rec):
    out = {}
    for g in rec:
        o, r = obs.get(g, set()), rec[g]
        out[g] = {"n_observed": len(o), "n_record": len(r), "n_record_count": RECORD_COUNTS[g],
                  "only_observed": sorted(map(list, o - r)), "only_record": sorted(map(list, r - o)),
                  "equal": o == r and len(o) == RECORD_COUNTS[g]}
    return out


def history_missing(runs):
    return [r["name"] for r in runs if r["hist"] is None]


def cmd_sets():
    by_task = scan()
    conv, fixed, excluded = members(by_task)
    obs = {}
    for t, d in conv + fixed:
        obs.setdefault(group_of(t, prefix_of(d)), set()).add(observed_key(d.name, prefix_of(d)))
    rec = record_sets()
    cmp_ = compare_sets(obs, rec)
    conv_runs = [load_run(d) for _, d in conv]
    fixed_runs = [load_run(d) for _, d in fixed]
    res = {"n_task_runs": {k: len(v) for k, v in by_task.items()}, "n_conv": len(conv), "n_fixed": len(fixed),
           "compare": cmp_, "all_equal": all(v["equal"] for v in cmp_.values()),
           "conv_history_missing": history_missing(conv_runs), "fixed_history_missing": history_missing(fixed_runs),
           "fixed_ep_missing": [r["name"] for r in fixed_runs if set(r["ep"]) != set(EPOCHS)],
           "excluded": excluded,
           "conv_runs": [d.name for _, d in conv], "fixed_runs": [d.name for _, d in fixed]}
    (OUT / "start").mkdir(exist_ok=True)
    (OUT / "start/sets.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("conv_runs", "fixed_runs", "excluded", "compare")}, ensure_ascii=False))
    print(json.dumps({g: {k: v for k, v in c.items() if k != "only_observed" and k != "only_record"} | {
        "n_only_observed": len(c["only_observed"]), "n_only_record": len(c["only_record"])} for g, c in cmp_.items()}, ensure_ascii=False))
    print("excluded:", json.dumps([(e["run"], e["prefix"]) for e in excluded], ensure_ascii=False))


# ---------- 目録 ----------

READ_FILES = ("config.yaml", "command.sh", "metrics.json", "metrics_last.json", "logs/history.json",
              "metrics_ep4.json", "metrics_ep8.json", "metrics_ep12.json", "metrics_ep16.json")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cmd_hashes(out):
    sets = jload(OUT / "start/sets.json")
    files = {}
    for name in sets["conv_runs"] + sets["fixed_runs"]:
        for f in READ_FILES:
            p = P1 / name / f
            if p.is_file():
                files[f"experiments/phase1/{name}/{f}"] = sha(p)
    for rel in ("experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/jobs.py",
                "experiments/analysis/grasp_hand_graph_t2p/tools/jobs.py",
                "experiments/analysis/grasp_hand_graph_pilot/tools/run_arms.sh", "scripts/stage2pilot/dp_train.py"):
        files[rel] = sha(ROOT / rel)
    Path(out).write_text(json.dumps(files, indent=0, sort_keys=True))
    print(json.dumps({"n_files": len(files), "manifest_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}))


def diff_manifest(a, b):
    return {"added": sorted(set(b) - set(a)), "removed": sorted(set(a) - set(b)),
            "changed": sorted(k for k in set(a) & set(b) if a[k] != b[k])}


# ---------- 取り出しと突き合わせ ----------

def arm_class(task, arm):
    if task in (GP, IHH):
        return "A0" if arm == "empty" else arm
    return arm   # 固定の長さの集合の名前（empty・D-CF・DGH-noCF・DGH-GT・pred_noCF など）はそのまま


def run_meta(r, task):
    c = r["cfg"]
    gr = c.get("gr") or {}
    st = SETTINGS.get((gr.get("N"), gr.get("L")))
    return {"task": task, "run": r["name"], "type": c["type"], "scope": c.get("scope", "W1"), "N": gr.get("N"),
            "L": gr.get("L"), "setting": st, "arm": c["arm"], "arm_class": arm_class(task, c["arm"])}


def lr_marks(r):
    """history の学習率の欄から下げた回を読み、metrics.json の lr_drop_epoch と比べる。下げた回 E の評価までは前、E+1 から後。"""
    h, m = r["hist"], r["metrics"]
    lr0 = h[0]["lr"]
    drops = [x["epoch"] for x in h if "lr_after" in x]
    first_low = next((x["epoch"] for x in h if x["lr"] != lr0), None)
    ok_vals = all(x["lr"] == lr0 for x in h if x["epoch"] <= m["lr_drop_epoch"]) and all(
        all(abs(a - b * 0.1) <= 1e-12 * b for a, b in zip(x["lr"], lr0)) for x in h if x["epoch"] > m["lr_drop_epoch"])
    return {"lr_drop_epoch_metrics": m["lr_drop_epoch"], "lr_after_epochs": drops,
            "first_lowered_epoch": first_low, "lr_values_consistent": ok_vals,
            "agree": drops == [m["lr_drop_epoch"]] and (first_low is None or first_low == m["lr_drop_epoch"] + 1) and ok_vals}


def phase_mark(epoch, drop):
    return "pre" if drop is None or epoch <= drop else "post"


def reconcile(r):
    """完了判定 c: epoch の数、結果の回の値、最後の回の値、学習率を下げた回。"""
    h, m, ml = r["hist"], r["metrics"], r["metrics_last"]
    best = h[m["result_epoch"] - 1]
    last = h[-1]
    marks = lr_marks(r)
    chk = {"n_epochs": len(h) == m["epochs_run"] and [x["epoch"] for x in h] == list(range(1, len(h) + 1)),
           "result_epoch": m["result_epoch"] == m["best_epoch"] and best["epoch"] == m["result_epoch"],
           "result_jaccard": best["val_jaccard"] == m["phase_jaccard"],
           "result_accuracy": best["val_accuracy"] == m["phase_accuracy"],
           "last_epoch": ml["epoch"] == m["epochs_run"],
           "last_jaccard": last["val_jaccard"] == ml["phase_jaccard"],
           "last_accuracy": last["val_accuracy"] == ml["phase_accuracy"],
           "lr_drop": marks["agree"]}
    return chk, marks


def cmd_extract():
    sets = jload(OUT / "start/sets.json")
    task_of_run = {}
    rows, checks, bad = [], {}, []
    for name in sets["conv_runs"]:
        r = load_run(P1 / name)
        task = r["cfg"]["task_id"]
        meta = run_meta(r, task)
        chk, marks = reconcile(r)
        checks[name] = {"checks": chk, "marks": marks}
        if not all(chk.values()):
            bad.append(name)
        drop = r["metrics"]["lr_drop_epoch"]
        for x in r["hist"]:
            rows.append({**meta, "epoch": x["epoch"], "val_jaccard": repr(x["val_jaccard"]), "val_accuracy": repr(x["val_accuracy"]),
                         "lr": json.dumps(x["lr"]), "lr_after": json.dumps(x.get("lr_after")) if "lr_after" in x else "",
                         "improved": x["improved"], "lr_drop_epoch": drop, "lr_phase": phase_mark(x["epoch"], drop),
                         "is_result_epoch": x["epoch"] == r["metrics"]["result_epoch"], "is_last_epoch": x["epoch"] == len(r["hist"])})
        task_of_run[name] = task
    with open(OUT / "epochs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    by_run = {}
    for x in rows:
        by_run.setdefault(x["run"], {})[x["epoch"]] = x["lr_phase"]
    pre48 = all(by_run[n].get(4) == "pre" and by_run[n].get(8) == "pre" for n in by_run)
    n16 = all(16 in by_run[n] for n in by_run)
    post = {e: sorted(n for n in by_run if by_run[n].get(e) == "post") for e in EPOCHS}
    drops = [checks[n]["marks"]["lr_drop_epoch_metrics"] for n in checks]
    res = {"n_runs": len(checks), "n_rows": len(rows), "n_bad": len(bad), "bad": bad,
           "all_reconcile": not bad, "epoch4_8_all_pre": pre48, "all_have_epoch16": n16,
           "n_post": {e: len(post[e]) for e in EPOCHS}, "post_runs": post,
           "lr_drop_min": min(drops), "lr_drop_max": max(drops),
           "epochs_run_min": min(len(by_run[n]) for n in by_run), "checks": checks}
    (OUT / "b").mkdir(exist_ok=True)
    (OUT / "b/checks.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("checks", "post_runs")}, ensure_ascii=False))


# ---------- 対と一致 ----------

def flat(d, p=""):
    o = {}
    if isinstance(d, dict):
        for k, v in d.items():
            o.update(flat(v, f"{p}.{k}" if p else str(k)))
    elif isinstance(d, list) and d and isinstance(d[0], dict):
        for i, v in enumerate(d):
            o.update(flat(v, f"{p}[{i}]"))
    else:
        o[p] = d
    return o


def sig_key(cfg):
    return (tuple((s["sha256"], s["gt"]) for s in cfg.get("signals_train", [])),
            tuple((s["sha256"], s["gt"]) for s in cfg.get("signals_val", [])))


def pair_key(cfg):
    gr = cfg.get("gr") or {}
    return (cfg["type"], cfg.get("scope", "W1"), gr.get("N"), gr.get("L"), sig_key(cfg))


def config_diff(a, b):
    fa, fb = flat(a), flat(b)
    keys = sorted(set(fa) | set(fb))
    diff = [k for k in keys if fa.get(k, "<none>") != fb.get(k, "<none>")]
    length = [k for k in diff if LENGTH_KEYS.search(k)]
    ident = [k for k in diff if IDENT_KEYS.search(k)]
    other = [k for k in diff if k not in length and k not in ident]
    return {"length": length, "ident": ident, "other": other}


def conv_val(r, e):
    x = r["hist"][e - 1]
    assert x["epoch"] == e
    return x["val_jaccard"], x["val_accuracy"]


def fixed_val(r, e):
    m = r["ep"][e]
    assert m["epoch"] == e
    return m["phase_jaccard"], m["phase_accuracy"]


def make_pairs(conv_runs, fixed_runs):
    fx = {}
    for r in fixed_runs:
        if r["cfg"]["type"] == "GR":
            fx.setdefault(pair_key(r["cfg"]), []).append(r)
    pairs = []
    for r in conv_runs:
        if r["cfg"]["task_id"] != GP:
            continue
        for f in fx.get(pair_key(r["cfg"]), []):
            pairs.append((r, f))
    return pairs


def compare_pair(c, f):
    out = {"conv": c["name"], "fixed": f["name"], "scope": c["cfg"]["scope"], "arm_conv": c["cfg"]["arm"],
           "arm_class": arm_class(GP, c["cfg"]["arm"]), "arm_fixed": f["cfg"]["arm"],
           "setting": SETTINGS[(c["cfg"]["gr"]["N"], c["cfg"]["gr"]["L"])],
           "config_diff": config_diff(c["cfg"], f["cfg"]), "lr_drop_epoch": c["metrics"]["lr_drop_epoch"], "ep": {}}
    for e in EPOCHS:
        cj, ca = conv_val(c, e)
        fj, fa = fixed_val(f, e)
        hj = f["hist"][e - 1]["val_jaccard"] if f["hist"] else None
        ha = f["hist"][e - 1]["val_accuracy"] if f["hist"] else None
        out["ep"][e] = {"conv_j": cj, "conv_a": ca, "fixed_j": fj, "fixed_a": fa, "dj": cj - fj, "da": ca - fa,
                        "eq_j": cj == fj, "eq_a": ca == fa, "lr_phase": phase_mark(e, c["metrics"]["lr_drop_epoch"]),
                        "fixed_hist_equals_ep": hj == fj and ha == fa}
    return out


def summarize_pairs(cmp_):
    groups = {}
    for p in cmp_:
        for e in EPOCHS:
            q = p["ep"][e]
            k = (p["scope"], p["arm_class"], e)
            g = groups.setdefault(k, {"n": 0, "n_eq_j": 0, "n_eq_a": 0, "n_eq_both": 0, "max_abs_dj": 0.0, "max_abs_da": 0.0,
                                      "n_post": 0, "n_post_eq_both": 0})
            g["n"] += 1
            g["n_eq_j"] += q["eq_j"]
            g["n_eq_a"] += q["eq_a"]
            g["n_eq_both"] += q["eq_j"] and q["eq_a"]
            g["max_abs_dj"] = max(g["max_abs_dj"], abs(q["dj"]))
            g["max_abs_da"] = max(g["max_abs_da"], abs(q["da"]))
            if q["lr_phase"] == "post":
                g["n_post"] += 1
                g["n_post_eq_both"] += q["eq_j"] and q["eq_a"]
    return groups


def chk_compares(conv_runs, fixed_runs):
    """完了判定 g: 前回の契約が値を流用した組み合わせの確かめの run。"""
    def find(runs, **kw):
        out = [r for r in runs if all((r["cfg"].get("gr") or {}).get(k[3:]) == v if k.startswith("gr_") else r["cfg"].get(k) == v
                                      for k, v in kw.items())]
        assert len(out) == 1, (kw, [r["name"] for r in out])
        return out[0]
    ihh = [r for r in conv_runs if r["cfg"]["task_id"] == IHH]
    gp = [r for r in conv_runs if r["cfg"]["task_id"] == GP]
    rows = []
    def add(kind, basis, a, b, getter):
        for e in EPOCHS:
            ja, aa = getter(a, e)
            jb, ab = getter(b, e)
            rows.append({"kind": kind, "basis": basis, "a": a["name"], "b": b["name"], "epoch": e, "dj": ja - jb, "da": aa - ab,
                         "eq": ja == jb and aa == ab,
                         "lr_phase_a": phase_mark(e, a["metrics"].get("lr_drop_epoch")) if "converge" in a["metrics"] else "fixed",
                         "lr_phase_b": phase_mark(e, b["metrics"].get("lr_drop_epoch")) if "converge" in b["metrics"] else "fixed"})
    for t in ("IRN", "HiCE", "HTT"):
        add("IHH", "A0 s2〜s4 ← s1", find(ihh, type=t, arm="empty", scope="W1", gr_N=30, gr_L=2),
            find(ihh, type=t, arm="empty", scope="W1", gr_N=10, gr_L=1), conv_val)
    add("IHH", "HiCE D ← HiCE A0", find(ihh, type="HiCE", arm="D", scope="W1", gr_N=10, gr_L=1),
        find(ihh, type="HiCE", arm="empty", scope="W1", gr_N=10, gr_L=1), conv_val)
    add("IHH", "HiCE DH s3・s4 ← s1・s2", find(ihh, type="HiCE", arm="DH", scope="W1", gr_N=30, gr_L=1),
        find(ihh, type="HiCE", arm="DH", scope="W1", gr_N=10, gr_L=1), conv_val)
    for t in ("IRN", "HiCE", "HTT"):          # 参考: irn-hice-htt-pilot が足した A0 とグラフの型の A0 の確かめ（流用の根拠ではない）
        for sc in SCOPES:
            add("IHH-ref", "A0 と GR の A0（参考）", find(ihh, type=t, arm="empty", scope=sc, gr_N=10, gr_L=1),
                find(gp, type="GR", arm="empty", scope=sc, gr_N=10, gr_L=1), conv_val)
    fgr = [r for r in fixed_runs if r["cfg"]["type"] == "GR"]
    for sc in SCOPES:
        add("T2P", "空 s2〜s4 ← s1", find(fgr, arm="empty", scope=sc, gr_N=30, gr_L=2),
            find(fgr, arm="empty", scope=sc, gr_N=10, gr_L=1), fixed_val)
        add("T2P", "辺の無い腕 s2・s4 ← s1・s3", find(fgr, arm="D-noCF", scope=sc, gr_N=10, gr_L=2),
            find(fgr, arm="D-noCF", scope=sc, gr_N=10, gr_L=1), fixed_val)
    return rows


def load_sets():
    sets = jload(OUT / "start/sets.json")
    return [load_run(P1 / n) for n in sets["conv_runs"]], [load_run(P1 / n) for n in sets["fixed_runs"]]


def cmd_pairs():
    conv_runs, fixed_runs = load_sets()
    pairs = make_pairs(conv_runs, fixed_runs)
    cmp_ = [compare_pair(c, f) for c, f in pairs]
    groups = summarize_pairs(cmp_)
    conv_paired = [p["conv"] for p in cmp_]
    chk = chk_compares(conv_runs, fixed_runs)
    res = {"n_pairs": len(cmp_), "n_conv_paired_unique": len(set(conv_paired)),
           "n_conv_multi_paired": len(conv_paired) - len(set(conv_paired)),
           "n_config_other_diff": sum(bool(p["config_diff"]["other"]) for p in cmp_),
           "config_other_diff_keys": sorted({k for p in cmp_ for k in p["config_diff"]["other"]}),
           "config_length_keys": sorted({k for p in cmp_ for k in p["config_diff"]["length"]}),
           "config_ident_keys": sorted({k for p in cmp_ for k in p["config_diff"]["ident"]}),
           "arm_map": sorted({(p["arm_conv"], p["arm_fixed"]) for p in cmp_}),
           "fixed_hist_equals_ep_all": all(q["fixed_hist_equals_ep"] for p in cmp_ for q in p["ep"].values()),
           "by_epoch": {e: {"n": len(cmp_), "n_eq_j": sum(p["ep"][e]["eq_j"] for p in cmp_),
                            "n_eq_a": sum(p["ep"][e]["eq_a"] for p in cmp_),
                            "n_eq_both": sum(p["ep"][e]["eq_j"] and p["ep"][e]["eq_a"] for p in cmp_),
                            "max_abs_dj": max(abs(p["ep"][e]["dj"]) for p in cmp_),
                            "max_abs_da": max(abs(p["ep"][e]["da"]) for p in cmp_),
                            "n_post": sum(p["ep"][e]["lr_phase"] == "post" for p in cmp_)} for e in EPOCHS},
           "groups": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in sorted(groups.items())},
           "chk": chk, "chk_summary": {}, "pairs": cmp_}
    for row in chk:
        s = res["chk_summary"].setdefault(f"{row['kind']}|{row['basis']}|{row['epoch']}", {"n": 0, "n_eq": 0, "max_abs": 0.0})
        s["n"] += 1
        s["n_eq"] += row["eq"]
        s["max_abs"] = max(s["max_abs"], abs(row["dj"]), abs(row["da"]))
    (OUT / "b").mkdir(exist_ok=True)
    (OUT / "b/pairs.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k not in ("groups", "pairs", "chk")}, ensure_ascii=False, indent=0))


# ---------- 表 ----------

def read_epochs_csv():
    tab = {}
    with open(OUT / "epochs.csv") as f:
        for x in csv.DictReader(f):
            k = (x["type"], x["scope"], x["setting"], x["arm_class"])
            assert int(x["epoch"]) not in tab.get(k, {}), (k, x["epoch"])
            tab.setdefault(k, {})[int(x["epoch"])] = (float(x["val_jaccard"]), float(x["val_accuracy"]), x["lr_phase"], x["run"])
    return tab


def conv_cell(tab, t, sc, st, arm):
    """SPEC §4 の流用（irn-hice-htt-pilot の SPEC §5.2）を当てて (値の辞書, 流用元の設定と腕) を返す。"""
    src_st, src_arm = st, arm
    if t != "GR":
        if arm == "A0":
            src_st = "s1"
        elif t == "HiCE" and arm == "D":
            src_st, src_arm = "s1", "A0"
        elif t == "HiCE" and arm == "DH" and st in ("s3", "s4"):
            src_st = {"s3": "s1", "s4": "s2"}[st]
    return tab[(t, sc, src_st, src_arm)], (src_st, src_arm) != (st, arm)


def fixed_tab(fixed_runs):
    gr, tp = {}, {}
    for r in fixed_runs:
        c = r["cfg"]
        vals = {e: fixed_val(r, e) for e in EPOCHS}
        if c["type"] == "GR":
            gr[(c["scope"], SETTINGS[(c["gr"]["N"], c["gr"]["L"])], c["arm"])] = vals
        else:
            tp[(c["scope"], c["type"], c["arm"])] = vals
    return gr, tp


def fixed_gr_cell(gr, sc, st, arm):
    src = st
    if arm == "empty":
        src = "s1"
    elif arm.split("-")[0] in ("D", "DG", "DH") and not arm.startswith("DGH") and st in ("s2", "s4"):
        src = {"s2": "s1", "s4": "s3"}[st]
    return gr[(sc, src, arm)], src != st


DIFFS_53 = (("DGH", "A0"), ("D", "A0"), ("DG", "D"), ("DH", "D"), ("DGH", "DG"), ("DGH", "DGH-U"), ("DGH", "DGH-noCF"), ("DGH-GT", "A0"))


def fmt(v, post=False, diff=False):
    s = f"{v:+.4f}" if diff else f"{v:.4f}"
    if diff and abs(v) <= READ_WIDTH:
        s += "≈"
    return s + ("†" if post else "")


def build_tables(tab, gr, tp, pairs_res):
    T = {"52": {}, "53": {}, "54": {}}
    for t in TYPES:
        for sc in SCOPES:
            for arm in ARMS:
                for st in ("s1", "s2", "s3", "s4"):
                    cell, borrowed = conv_cell(tab, t, sc, st, arm)
                    T["52"][f"{t}|{sc}|{arm}|{st}"] = {"borrowed": borrowed, **{e: {"j": cell[e][0], "a": cell[e][1], "post": cell[e][2] == "post"} for e in EPOCHS}}
    for t in TYPES:
        for sc in SCOPES:
            for x, y in DIFFS_53:
                for st in ("s1", "s2", "s3", "s4"):
                    cx, _ = conv_cell(tab, t, sc, st, x)
                    cy, _ = conv_cell(tab, t, sc, st, y)
                    T["53"][f"{t}|{sc}|{x}-{y}|{st}"] = {e: {"dj": cx[e][0] - cy[e][0], "da": cx[e][1] - cy[e][1],
                                                            "post": cx[e][2] == "post" or cy[e][2] == "post"} for e in EPOCHS}
    for sc in SCOPES:
        for t in TYPES:
            for x in ("DGH", "DGH-noCF", "DGH-GT"):
                for st in ("s1", "s2", "s3", "s4"):
                    cx, _ = conv_cell(tab, t, sc, st, x)
                    cy, _ = conv_cell(tab, t, sc, st, "A0")
                    T["54"][f"{sc}|収束規則|{t}|{x} − A0|{st}"] = {e: {"dj": cx[e][0] - cy[e][0], "da": cx[e][1] - cy[e][1],
                                                                    "post": cx[e][2] == "post" or cy[e][2] == "post"} for e in EPOCHS}
        for x in ("DGH-CF", "DGH-noCF", "DGH-GT"):
            for st in ("s1", "s2", "s3", "s4"):
                cx, _ = fixed_gr_cell(gr, sc, st, x)
                cy, _ = fixed_gr_cell(gr, sc, st, "empty")
                T["54"][f"{sc}|固定|GR|{x} − 空|{st}"] = {e: {"dj": cx[e][0] - cy[e][0], "da": cx[e][1] - cy[e][1], "post": False} for e in EPOCHS}
        for t in TP_TYPES:
            for y, yname in (("empty", "空"), ("shuffle", "入れ替え")):
                cx, cy = tp[(sc, t, "pred_noCF")], tp[(sc, t, y)]
                T["54"][f"{sc}|固定|{t}|予測-noCF − {yname}|—"] = {e: {"dj": cx[e][0] - cy[e][0], "da": cx[e][1] - cy[e][1], "post": False} for e in EPOCHS}
    return T


def mismatch_marks(pairs_res):
    """§5.5: 4・8 epoch 目で一致しなかった対の (W, 腕)。"""
    bad = set()
    for p in pairs_res["pairs"]:
        for e in (4, 8):
            q = p["ep"][str(e)] if str(e) in p["ep"] else p["ep"][e]
            if not (q["eq_j"] and q["eq_a"]):
                bad.add((p["scope"], p["arm_class"]))
    return bad


def render(T, pairs_res, checks_res):
    L = []
    w = L.append
    bad = mismatch_marks(pairs_res)
    w("# REPORT — T-2026-11-22-conv-epoch-history-extract（非公式。関門の判定と設計の判断には使わない）")
    w("")
    w("すべての値は `tools/ceh.py report` が `epochs.csv`（収束規則の集合の `logs/history.json` から作った表）と、固定の長さの集合の "
      "`metrics_ep{4,8,12,16}.json`（版管理の中）から作った。手で写していない。GPU・学習・評価・推論は使っていない。")
    w("")
    w("- 7 工程の Jaccard を J、frame accuracy を acc と書く。6 工程・工程別・動画ごとの値は epoch ごとの記録に無いので作っていない")
    w("- **†** = その epoch が学習率を下げた後（収束規則の集合の run。差ではどちらかの run が下げた後）。固定の長さの run と同じ学び方ではない")
    w("- **≈** = 差が ±0.015 の中（読めない）。±0.015 は工程塔側の予備で 6 工程の平均について測った幅（T-2026-11-09-grasp-pilot-converge の RESULT §3）で、"
      "7 工程と frame accuracy の幅は測っていない。目安として流用した")
    w("- **‡** = 前回の契約の流用のとおり、別の設定・腕の値を使った（irn-hice-htt-pilot: A0 の s2〜s4 に s1、HiCE の D に HiCE の A0、HiCE の DH の s3・s4 に s1・s2。"
      "graph-t2p-match: 空の s2〜s4 に s1、辺の無い腕の s2・s4 に s1・s3）")
    w("- 採否・順位・解釈は書かない。差を並べるだけ")
    w("")
    w("## 5.1 一致の確かめ（収束規則の集合 − 固定の長さの集合。対は config で作った）")
    w("")
    w(f"対 {pairs_res['n_pairs']} 組。config の違いは長さの規則の欄（{', '.join(pairs_res['config_length_keys'][:3])} など）と識別子・置き場の経路の欄だけで、"
      f"そのほかの違いがある対は {pairs_res['n_config_other_diff']} 組。")
    w("")
    w("| epoch | 対 | J がちょうど同じ | acc がちょうど同じ | 両方同じ | max abs ΔJ | max abs Δacc | 下げた後の対 |")
    w("|---|---|---|---|---|---|---|---|")
    for e in EPOCHS:
        b = pairs_res["by_epoch"][str(e)] if str(e) in pairs_res["by_epoch"] else pairs_res["by_epoch"][e]
        w(f"| {e} | {b['n']} | {b['n_eq_j']} | {b['n_eq_a']} | {b['n_eq_both']} | {b['max_abs_dj']:.3g} | {b['max_abs_da']:.3g} | {b['n_post']} |")
    w("")
    w("W・腕ごと（各欄は「両方同じの対 / 対」、括弧は max abs ΔJ・max abs Δacc。12・16 epoch 目の「後」は学習率を下げた後の対の数と、そのうち両方同じの数）")
    w("")
    w("| W | 腕（収束規則の名前） | 4 | 8 | 12 | 16 |")
    w("|---|---|---|---|---|---|")
    G = pairs_res["groups"]
    for sc in SCOPES:
        for arm in ARMS:
            cells = []
            for e in EPOCHS:
                g = G.get(f"{sc}|{arm}|{e}")
                if not g:
                    cells.append("—")
                    continue
                s = f"{g['n_eq_both']}/{g['n']}（{g['max_abs_dj']:.2g}・{g['max_abs_da']:.2g}）"
                if e in (12, 16):
                    s += f" 後 {g['n_post']}（同じ {g['n_post_eq_both']}）"
                cells.append(s)
            w(f"| {sc} | {arm} | " + " | ".join(cells) + " |")
    w("")
    if bad:
        w("**§5.5: 4・8 epoch 目で一致しなかった W・腕** — " + "、".join(f"{a}・{b}" for a, b in sorted(bad)) +
          "。これらの収束規則の集合の値は、固定の長さの集合と同じ学び方の値として読まない（下の表には作ってある）")
    else:
        w("§5.5: 4・8 epoch 目で一致しなかった対は無い")
    w("")
    w("## 5.2 腕の値（収束規則の集合。J / acc）")
    w("")
    for t in TYPES:
        for sc in SCOPES:
            w(f"### {t} · {sc}")
            w("")
            w("| 腕 | 設定 | J 4 | J 8 | J 12 | J 16 | acc 4 | acc 8 | acc 12 | acc 16 |")
            w("|---|---|---|---|---|---|---|---|---|---|")
            for arm in ARMS:
                for st in ("s1", "s2", "s3", "s4"):
                    c = T["52"][f"{t}|{sc}|{arm}|{st}"]
                    mark = "‡" if c["borrowed"] else ""
                    w(f"| {arm} | {st}{mark} | " + " | ".join(fmt(c[e]["j"], c[e]["post"]) for e in EPOCHS) + " | "
                      + " | ".join(fmt(c[e]["a"], c[e]["post"]) for e in EPOCHS) + " |")
            w("")
    w("## 5.3 同じ型の中の差（収束規則の集合）")
    w("")
    for t in TYPES:
        for key, name in (("dj", "J"), ("da", "acc")):
            w(f"### {t} · {name}")
            w("")
            w("| 差 | 設定 | " + " | ".join(f"{sc} {e}" for sc in SCOPES for e in EPOCHS) + " |")
            w("|---|---|" + "---|" * 12)
            for x, y in DIFFS_53:
                for st in ("s1", "s2", "s3", "s4"):
                    cells = []
                    for sc in SCOPES:
                        c = T["53"][f"{t}|{sc}|{x}-{y}|{st}"]
                        cells += [fmt(c[e][key], c[e]["post"], diff=True) for e in EPOCHS]
                    w(f"| {x} − {y} | {st} | " + " | ".join(cells) + " |")
            w("")
    w("## 5.4 型と方向の並べ（同じ W・同じ epoch）")
    w("")
    w("**送り手が違う。** T→P の 4 型（D1-L1・D1-L2・D2・D3-L2）の送り手は検出塔だけ。収束規則の集合の GR・IRN・HiCE・HTT と固定の長さの集合の GR の送り手は"
      "検出塔・把持塔 G3・手の塔 H4。収束規則の集合の DGH・DGH-U の予測は交差適合あり（CF）で、固定の長さの集合では DGH-CF と書く（§5.1 の対で信号の sha256 が一致）。"
      "値はそのまま並べた。型の間で最良を選ばず、順位を書かない。")
    w("")
    for sc in SCOPES:
        for key, name in (("dj", "J"), ("da", "acc")):
            w(f"### {sc} · {name}")
            w("")
            w("| 集合 | 型 | 差 | 設定 | 4 | 8 | 12 | 16 |")
            w("|---|---|---|---|---|---|---|---|")
            for k, c in T["54"].items():
                s, grp, t, d, st = k.split("|")
                if s != sc:
                    continue
                flag = ""
                if grp == "収束規則" and (sc, "DGH" if d.startswith("DGH ") else d.split(" ")[0]) in bad:
                    flag = "（§5.5 の印）"
                w(f"| {grp} | {t} | {d}{flag} | {st} | " + " | ".join(fmt(c[e][key], c[e]["post"], diff=True) for e in EPOCHS) + " |")
            w("")
    w("## 学習率を下げた後になった run の数（収束規則の集合）")
    w("")
    w("| epoch | 下げた後の run / 全 run |")
    w("|---|---|")
    for e in EPOCHS:
        w(f"| {e} | {checks_res['n_post'][str(e)] if str(e) in checks_res['n_post'] else checks_res['n_post'][e]} / {checks_res['n_runs']} |")
    w("")
    w("## 流用の確かめ（完了判定 g。値がちょうど同じなら一致）")
    w("")
    w("| 契約 | 流用 | epoch | 一致 / 組 | max abs の差（J・acc） |")
    w("|---|---|---|---|---|")
    for k, s in pairs_res["chk_summary"].items():
        kind, basis, e = k.split("|")
        w(f"| {kind} | {basis} | {e} | {s['n_eq']}/{s['n']} | {s['max_abs']:.3g} |")
    w("")
    return "\n".join(L) + "\n"


def cmd_report():
    tab = read_epochs_csv()
    _, fixed_runs = load_sets()
    gr, tp = fixed_tab(fixed_runs)
    pairs_res = jload(OUT / "b/pairs.json")
    checks_res = jload(OUT / "b/checks.json")
    T = build_tables(tab, gr, tp, pairs_res)
    (OUT / "c").mkdir(exist_ok=True)
    (OUT / "c/tables.json").write_text(json.dumps(T, ensure_ascii=False, indent=0))
    (OUT / "REPORT.md").write_text(render(T, pairs_res, checks_res))
    print(json.dumps({k: len(v) for k, v in T.items()}))


def cmd_summary():
    """RESULT の §5.4 の要約（4・8 epoch 目、W ごと、行ごとの 4 設定の範囲と ±0.015 の外の数）→ c/summary.json"""
    T = jload(OUT / "c/tables.json")
    rows = {}
    for k, c in T["54"].items():
        sc, grp, t, d, st = k.split("|")
        for e in ("4", "8"):
            for key in ("dj", "da"):
                rows.setdefault(f"{sc}|{e}|{key}|{grp}|{t}|{d}", []).append(c[e][key])
    out = {k: {"min": min(v), "max": max(v), "n": len(v), "n_outside": sum(abs(x) > READ_WIDTH for x in v)} for k, v in rows.items()}
    pred2 = {t: [T["53"][f"{t}|W1|DGH-A0|{st}"]["4"]["dj"] for st in ("s1", "s2", "s3", "s4")] for t in ("IRN", "HiCE", "HTT")}
    res = {"54_ep4_8": out, "prediction2": {t: {"values": v, "n_within": sum(abs(x) <= READ_WIDTH for x in v)} for t, v in pred2.items()}}
    (OUT / "c/summary.json").write_text(json.dumps(res, ensure_ascii=False, indent=0))
    for k, v in out.items():
        if "|dj|" in k:
            print(k, f"{v['min']:+.4f}〜{v['max']:+.4f}", f"外 {v['n_outside']}/{v['n']}")
    print(json.dumps(res["prediction2"]))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "summary":
        cmd_summary()
        sys.exit(0)
    if cmd == "sets":
        cmd_sets()
    elif cmd == "hashes":
        cmd_hashes(sys.argv[2])
    elif cmd == "extract":
        cmd_extract()
    elif cmd == "pairs":
        cmd_pairs()
    elif cmd == "report":
        cmd_report()
    elif cmd == "controls":
        runpy.run_path(str(Path(__file__).with_name("controls.py")), run_name="__main__")
    else:
        raise SystemExit(f"unknown cmd {cmd}")

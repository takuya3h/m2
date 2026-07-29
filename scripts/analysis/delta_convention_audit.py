#!/usr/bin/env python3
"""D1: Δ 分母規約の確定 — 論文の全 Table の土台である「Δ が何に対する差分か」を実測で決める。

研究計画に引用されている値 (S4 0.8986 / B2a +0.0383 / T1a +0.0497 / H-6 +0.0004 /
oracle-tool 0.9583・0.823) が、リポジトリ内のどの run のどの集計に対応するかを、
全 metrics.json を棚卸ししたうえで組み合わせ探索で特定する。

**Δ の正本は決定しない。** 選択肢と根拠を出すところまで (指示書 §0)。

Usage:
    python3 scripts/analysis/delta_convention_audit.py --out $OUT
    python3 scripts/analysis/delta_convention_audit.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import statistics
import tempfile
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_SEEDS = ["42", "123", "456"]
T_CRIT_DF2 = 4.302652   # paired t, alpha=0.05, df=2

# 研究計画に引用されている値 (§1.1 / §1.2)
QUOTED = {
    "S4_base_accuracy":   {"value": 0.8986, "source": "研究計画 §1.2", "kind": "absolute"},
    "B2a_delta":          {"value": 0.0383, "source": "研究計画 §1.2", "kind": "delta"},
    "T1a_delta":          {"value": 0.0497, "source": "研究計画 §1.2", "kind": "delta"},
    "H6_delta":           {"value": 0.0004, "source": "研究計画 §1.2", "kind": "delta"},
    "oracle_tool_acc":    {"value": 0.9583, "source": "研究計画 §1.2", "kind": "absolute"},
    "oracle_tool_macroF1": {"value": 0.823, "source": "研究計画 §1.2", "kind": "absolute"},
    "S0_frozen_mAP":      {"value": 0.7051, "source": "研究計画 §13.0'", "kind": "absolute"},
}
# 独立に測られた検出側の値 (§1.1 矛盾 C)
P0_INIT_MAP = {"42": 0.730294, "123": 0.729178, "456": 0.721659}


def classify(run_name: str) -> str:
    r = run_name.lower()
    if "oracletool" in r or "oracle_tool" in r:
        return "oracle-tool"
    if r.startswith("s4_phase_baseline"):
        return "s4"
    if r.startswith("haux_"):
        return "h6"
    if r.startswith("b2a_"):
        return "b2a"
    if r.startswith("t1a_"):
        return "t1a"
    return "other"


def seed_of(run_name: str) -> str:
    return run_name.split("seed")[-1] if "seed" in run_name else "UNKNOWN"


def collect_runs():
    """experiments/**/metrics.json を棚卸しする。読めない項目は UNKNOWN。"""
    rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "experiments/**/metrics.json"), recursive=True)):
        rel = os.path.relpath(p, REPO)
        d_dir = os.path.dirname(p)
        run = os.path.basename(d_dir)
        try:
            with open(p) as f:
                d = json.load(f)
        except Exception:
            rows.append({"path": rel, "run_name": run, "系統": "UNKNOWN", "seed": "UNKNOWN",
                         "split": "UNKNOWN", "metric_name": "UNKNOWN", "value": "UNKNOWN",
                         "config_path": "UNKNOWN", "commit": "UNKNOWN",
                         "mtime": os.path.getmtime(p)})
            continue
        cmd_p = os.path.join(d_dir, "command.sh")
        cmd = open(cmd_p).read() if os.path.exists(cmd_p) else ""
        # split: metrics.json に split 情報が無いため command.sh の --eval-test で判定する
        split = "test" if "--eval-test" in cmd else ("val" if cmd else "UNKNOWN")
        cfg = os.path.join(d_dir, "config.yaml")
        gc = os.path.join(d_dir, "git_commit.txt")
        commit = open(gc).read().strip()[:12] if os.path.exists(gc) else "UNKNOWN"
        for k, v in d.items():
            if isinstance(v, (int, float)):
                rows.append({
                    "path": rel, "run_name": run, "系統": classify(run), "seed": seed_of(run),
                    "split": split, "metric_name": k, "value": v,
                    "config_path": os.path.relpath(cfg, REPO) if os.path.exists(cfg) else "UNKNOWN",
                    "commit": commit, "mtime": os.path.getmtime(p),
                })
    return rows


def index_by_system(rows, metric="phase_accuracy"):
    """{系統: [ {run, seed, split, value} ]}"""
    out = defaultdict(list)
    for r in rows:
        if r["metric_name"] == metric and isinstance(r["value"], (int, float)):
            out[r["系統"]].append({"run": r["run_name"], "seed": r["seed"],
                                   "split": r["split"], "value": r["value"],
                                   "mtime": r["mtime"]})
    return out


def search_subsets(cands, target, k=3, tol=5e-5, restrict_seeds=None):
    """cands から k 個選んだ平均が target に一致する組み合わせを探す。

    returns [ {runs, seeds, mean, residual} ]  (residual の小さい順)
    """
    pool = cands if restrict_seeds is None else [c for c in cands if c["seed"] in restrict_seeds]
    hits = []
    n = len(pool)
    if n < k:
        return hits
    for comb in itertools.combinations(range(n), k):
        sub = [pool[i] for i in comb]
        m = statistics.mean(x["value"] for x in sub)
        res = m - target
        if abs(res) <= tol:
            hits.append({"runs": [x["run"] for x in sub], "seeds": [x["seed"] for x in sub],
                         "mean": m, "residual": res,
                         "is_canonical_seed_triple": sorted(x["seed"] for x in sub) == sorted(CANONICAL_SEEDS)})
    hits.sort(key=lambda h: (abs(h["residual"]), not h["is_canonical_seed_triple"]))
    return hits


def mde(diffs):
    if len(diffs) < 2:
        return None
    sd = statistics.stdev(diffs)
    return T_CRIT_DF2 * sd / (len(diffs) ** 0.5), sd


def self_test() -> int:
    """検出できることを確認する (Step D1-8):
       1) 同じ系統で絶対値が 2 通りある状況を検出できるか
       2) 指標名が食い違う状況を検出できるか
       3) 部分集合探索が正しい組み合わせを見つけられるか
    """
    ok = True
    with tempfile.TemporaryDirectory() as td:
        # 同じ系統 s4 で 2 通りの絶対値を持つ合成 run を作る
        specs = [("s4_phase_baseline_001_x_seed42", {"phase_accuracy": 0.90, "phase_macro_f1": 0.70}),
                 ("s4_phase_baseline_002_x_seed123", {"phase_accuracy": 0.90, "phase_macro_f1": 0.70}),
                 ("s4_phase_baseline_003_x_seed456", {"phase_accuracy": 0.90, "phase_macro_f1": 0.70}),
                 ("s4_phase_baseline_010_x_seed42", {"phase_accuracy": 0.80, "phase_macro_f1": 0.60}),
                 ("s4_phase_baseline_011_x_seed123", {"phase_accuracy": 0.80, "phase_macro_f1": 0.60}),
                 ("s4_phase_baseline_012_x_seed456", {"phase_accuracy": 0.80, "phase_macro_f1": 0.60})]
        cands = []
        for run, m in specs:
            cands.append({"run": run, "seed": seed_of(run), "split": "val",
                          "value": m["phase_accuracy"], "mtime": 0})
        # 1) 2 通りの絶対値が存在することを検出
        distinct = sorted({round(c["value"], 6) for c in cands})
        if len(distinct) != 2:
            print(f"  [FAIL] 2 通りの絶対値を検出できない: {distinct}"); ok = False
        else:
            print(f"  [OK]   同一系統に絶対値が 2 通りある状況を検出 ({distinct})")

        # 2) 部分集合探索: 0.90 を出す組み合わせを見つけられるか
        hits = search_subsets(cands, 0.90, k=3)
        if not hits or not hits[0]["is_canonical_seed_triple"]:
            print(f"  [FAIL] 部分集合探索: {hits[:1]}"); ok = False
        else:
            print(f"  [OK]   目標値を出す 3-run 組み合わせを特定 (seeds={hits[0]['seeds']})")

        # 3) 指標名の食い違い検出 (accuracy しか無い run に macro_f1 を要求)
        rows = [{"metric_name": "phase_accuracy", "value": 0.9, "系統": "s4",
                 "run_name": "r", "seed": "42", "split": "val", "path": "p", "mtime": 0}]
        idx = index_by_system(rows, metric="phase_macro_f1")
        if idx:
            print(f"  [FAIL] 存在しない指標を拾った: {dict(idx)}"); ok = False
        else:
            print("  [OK]   要求した指標を持たない run を空として扱える (指標名の食い違いを検出)")

        # 4) 一致が無い場合に空を返すか (UNEXPLAINED を作れるか)
        if search_subsets(cands, 0.123456, k=3):
            print("  [FAIL] 一致しない目標に対して偽の一致を返した"); ok = False
        else:
            print("  [OK]   一致が無い場合は空を返す (UNEXPLAINED を作れる)")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.out:
        ap.error("--out か --self-test のどちらかが必要")
    out = args.out
    for sub in ("json", "csv"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    # ---- Step D1-1: 棚卸し ------------------------------------------------- #
    rows = collect_runs()
    cols = ["path", "run_name", "系統", "seed", "split", "metric_name", "value",
            "config_path", "commit", "mtime"]
    with open(os.path.join(out, "csv", "d1_all_runs.csv"), "w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(f"\"{r[c]}\"" if isinstance(r[c], str) else str(r[c])
                             for c in cols) + "\n")
    acc = index_by_system(rows, "phase_accuracy")
    f1 = index_by_system(rows, "phase_macro_f1")
    print(f"棚卸し: {len(rows)} 指標行 / 系統別 run 数(accuracy): "
          f"{ {k: len(v) for k, v in acc.items()} }")

    # ---- Step D1-2: S4 が何本あるか --------------------------------------- #
    s4 = sorted(acc.get("s4", []), key=lambda x: x["run"])
    s4_hits_8986 = search_subsets(s4, QUOTED["S4_base_accuracy"]["value"], 3, tol=5e-5)
    s4_val = [x for x in s4 if x["split"] == "val"]
    s4_test = [x for x in s4 if x["split"] == "test"]
    d1_2 = {
        "n_s4_runs": len(s4),
        "n_val": len(s4_val), "n_test": len(s4_test),
        "value_range": {"min": min(x["value"] for x in s4), "max": max(x["value"] for x in s4)} if s4 else None,
        "combinations_producing_0.8986": s4_hits_8986[:5],
        "n_combinations_producing_0.8986": len(s4_hits_8986),
        "step_c_coupling_value": None,
    }
    coup_p = os.path.join(REPO, "experiments/analysis/step_c_coupling_analysis/test_eval_det2phase.json")
    coup = json.load(open(coup_p)) if os.path.exists(coup_p) else {}
    if coup:
        d1_2["step_c_coupling_value"] = {
            "val_accuracy_3seed_mean": statistics.mean(
                coup["s4"][s]["val"]["phase_accuracy"] for s in CANONICAL_SEEDS),
            "test_accuracy_3seed_mean": statistics.mean(
                coup["s4"][s]["test"]["phase_accuracy"] for s in CANONICAL_SEEDS),
            "source": os.path.relpath(coup_p, REPO),
            "note": "0.8928 の出所。run ディレクトリの metrics.json とは別の再評価",
        }

    # ---- Step D1-3: 仮説 H-base ------------------------------------------- #
    # run family は部分文字列 "_001_" では一意に決まらない (b2a だけで 257 run あり
    # b2a_det2phase_001_* と b2a_det2phase_toolpresence_001_* が別families として共存する)。
    # そこで実測で確認した family 接頭辞を明示する。
    CANONICAL_FAMILY = {
        "s4": "s4_phase_baseline_",
        "b2a": "b2a_det2phase_0",          # b2a_det2phase_001..003 (toolpresence 系とは別 family)
        "t1a": "t1a_regiontoken_0",
        "h6": "haux_hand_presence_oracle_withtooloracle_0",
    }

    def canonical_triple(system, idx=None):
        """研究計画が使ったと推定される family の 001-003 の 3 本。"""
        idx = idx if idx is not None else acc
        pre = CANONICAL_FAMILY.get(system)
        if not pre:
            return []
        c = [x for x in idx.get(system, [])
             if x["run"].startswith(pre) and any(f"_{n:03d}_" in x["run"] for n in (1, 2, 3))]
        # 同一 run が複数指標行から来ることがあるので run 名で一意化
        seen, uniq = set(), []
        for x in sorted(c, key=lambda x: x["run"]):
            if x["run"] not in seen:
                seen.add(x["run"]); uniq.append(x)
        return uniq[:3]

    base_triple = canonical_triple("s4")
    base_mean = statistics.mean(x["value"] for x in base_triple) if base_triple else None

    hbase = {"baseline_runs": [x["run"] for x in base_triple],
             "baseline_mean": base_mean,
             "matches_quoted_0.8986": (abs(base_mean - 0.8986) < 5e-5) if base_mean else False,
             "systems": {}}
    for sysname, qkey in [("b2a", "B2a_delta"), ("t1a", "T1a_delta")]:
        tri = canonical_triple(sysname)
        if not tri or base_mean is None:
            hbase["systems"][sysname] = {"status": "UNKNOWN", "reason": "canonical triple が見つからない"}
            continue
        m = statistics.mean(x["value"] for x in tri)
        delta = m - base_mean
        resid = QUOTED[qkey]["value"] - delta
        hbase["systems"][sysname] = {
            "runs": [x["run"] for x in tri], "seeds": [x["seed"] for x in tri],
            "mean": m, "delta_vs_baseline": delta,
            "quoted_delta": QUOTED[qkey]["value"], "residual": resid,
            "status": "EXACT" if abs(resid) < 5e-5 else ("NEAR" if abs(resid) < 2e-3 else "UNEXPLAINED"),
        }

    # H-6 は S4 基準では説明できない -> 基準候補を総当たりで探す
    haux = canonical_triple("h6")
    haux_mean = statistics.mean(x["value"] for x in haux) if haux else None
    ot = sorted(acc.get("oracle-tool", []), key=lambda x: x["run"])
    h6_search = {}
    if haux_mean is not None:
        target_base = haux_mean - QUOTED["H6_delta"]["value"]
        cands = search_subsets(ot, target_base, 3, tol=5e-5)
        h6_search = {
            "h6_runs": [x["run"] for x in haux], "h6_mean": haux_mean,
            "delta_vs_S4_baseline": (haux_mean - base_mean) if base_mean else None,
            "note_S4_baseline": "S4 を分母にすると +0.0583 となり引用値 +0.0004 と一致しない",
            "implied_baseline_for_quoted_delta": target_base,
            "oracle_tool_combinations_matching": cands[:5],
            "n_matching": len(cands),
            "status": "EXPLAINED" if cands else "UNEXPLAINED",
        }
    # oracle-tool の引用値 (0.9583 / 0.823)
    ot_f1 = sorted(f1.get("oracle-tool", []), key=lambda x: x["run"])
    ot_acc_hits = search_subsets(ot, QUOTED["oracle_tool_acc"]["value"], 3, tol=5e-5)
    ot_acc_near = search_subsets(ot, QUOTED["oracle_tool_acc"]["value"], 3, tol=2e-3)
    ot_f1_hits = search_subsets(ot_f1, QUOTED["oracle_tool_macroF1"]["value"], 3, tol=5e-4)
    oracle_audit = {
        "n_oracle_tool_runs": len(ot),
        "acc_exact_matches": ot_acc_hits[:3], "n_acc_exact": len(ot_acc_hits),
        "acc_near_matches": ot_acc_near[:3], "n_acc_near": len(ot_acc_near),
        "f1_matches": ot_f1_hits[:3], "n_f1_matches": len(ot_f1_hits),
        "status": "EXACT" if ot_acc_hits else ("NEAR" if ot_acc_near else "UNEXPLAINED"),
        "ambiguity_note": ("複数の組み合わせが同じ丸め値を与えるため、"
                           "引用値がどの組み合わせ由来かは一意に定まらない"),
    }

    # ---- Step D1-4: 4 規約で Δ 再計算 -------------------------------------- #
    def conv_table(baseline_mean, split, metric_idx, label):
        t = {}
        for sysname in ("b2a", "t1a", "h6", "oracle-tool"):
            c = [x for x in metric_idx.get(sysname, []) if x["split"] == split
                 and x["seed"] in CANONICAL_SEEDS]
            if not c or baseline_mean is None:
                t[sysname] = {"status": "UNKNOWN", "n": len(c)}
                continue
            by_seed = {}
            for x in c:
                by_seed.setdefault(x["seed"], []).append(x["value"])
            vals = [statistics.mean(v) for v in by_seed.values()]
            m = statistics.mean(vals)
            r = mde(vals)
            t[sysname] = {"n_seeds": len(vals), "mean": m, "delta": m - baseline_mean,
                          "sd": r[1] if r else None, "MDE": r[0] if r else None,
                          "exceeds_MDE": (abs(m - baseline_mean) > r[0]) if r else None}
        return {"label": label, "baseline": baseline_mean, "split": split, "table": t}

    def baseline_for(split, metric_idx):
        c = [x for x in metric_idx.get("s4", []) if x["split"] == split and x["seed"] in CANONICAL_SEEDS]
        if not c:
            return None
        by_seed = {}
        for x in c:
            by_seed.setdefault(x["seed"], []).append(x["value"])
        return statistics.mean(statistics.mean(v) for v in by_seed.values())

    conventions = {
        "K1": conv_table(baseline_for("val", acc), "val", acc, "S4(全val run平均) / val / accuracy"),
        "K2": conv_table(baseline_for("val", f1), "val", f1, "S4(全val run平均) / val / macro-F1"),
        "K3": conv_table(baseline_for("test", acc), "test", acc, "S4(全test run平均) / test / accuracy"),
        "K4": conv_table(baseline_for("test", f1), "test", f1, "S4(全test run平均) / test / macro-F1"),
    }
    # K1'-K4': 0.8986 の出所 (canonical triple) を分母にした版
    if base_mean is not None:
        f1_base_tri = [x for x in f1.get("s4", []) if x["run"] in {r["run"] for r in base_triple}]
        f1_base = statistics.mean(x["value"] for x in f1_base_tri) if f1_base_tri else None
        conventions["K1'"] = conv_table(base_mean, "val", acc, "S4 canonical triple (=0.8986) / val / accuracy")
        conventions["K2'"] = conv_table(f1_base, "val", f1, "S4 canonical triple / val / macro-F1")

    # ---- Step D1-5: 検出側 -------------------------------------------------- #
    det_rows = []
    for p in sorted(glob.glob(os.path.join(REPO, "experiments/baselines/s0_*/metrics.json"))):
        with open(p) as f:
            d = json.load(f)
        run = os.path.basename(os.path.dirname(p))
        if "mAP" in d:
            det_rows.append({"run": run, "mAP": d["mAP"], "seed": seed_of(run)})
    s0_pool = [{"run": r["run"], "seed": r["seed"], "value": r["mAP"], "split": "val"}
               for r in det_rows]
    s0_hits = search_subsets(s0_pool, QUOTED["S0_frozen_mAP"]["value"], 3, tol=5e-5)
    s0_hits_loose = search_subsets(s0_pool, QUOTED["S0_frozen_mAP"]["value"], 3, tol=5e-4)
    det = {
        "n_s0_runs": len(det_rows),
        "quoted_S0_frozen": QUOTED["S0_frozen_mAP"]["value"],
        "combinations_matching_0.7051_tol5e-5": s0_hits[:5],
        "n_matching_strict": len(s0_hits),
        "n_matching_loose_tol5e-4": len(s0_hits_loose),
        "uniquely_identified": len(s0_hits) == 1,
        "ambiguity_note": ("組み合わせが複数ある場合、引用値がどの run 集合由来かは一意に定まらない。"
                           "件数をそのまま報告する。"),
        "p0_init_map": P0_INIT_MAP,
        "p0_init_mean": statistics.mean(P0_INIT_MAP.values()),
        "difference": statistics.mean(P0_INIT_MAP.values()) - QUOTED["S0_frozen_mAP"]["value"],
        "status": ("EXPLAINED_UNIQUE" if len(s0_hits)==1 else ("EXPLAINED_AMBIGUOUS" if s0_hits else "UNEXPLAINED")),
        "note": ("p0 init mAP は verify_p0_init_identity.sh が train_t1b.py --epochs 0 で "
                 "測った init 時点の値。S0-frozen は experiments/baselines/s0_* の run 由来。"
                 "同一 checkpoint・同一 eval recipe かはコードから断定できない場合 UNEXPLAINED とする。"),
    }

    # ---- Step D1-6: 正誤表 -------------------------------------------------- #
    errata = []

    def add_err(name, quoted, recomputed, best, resid):
        st = "EXACT" if resid is not None and abs(resid) < 5e-5 else \
             ("NEAR" if resid is not None and abs(resid) < 2e-3 else "UNEXPLAINED")
        errata.append({"quoted_name": name, "quoted_value": quoted,
                       "quoted_source": QUOTED[name]["source"],
                       "recomputed": recomputed, "best_match_convention": best,
                       "residual": resid, "status": st})

    add_err("S4_base_accuracy", 0.8986, base_mean,
            "S4 canonical triple (001-003) val accuracy 3-seed 平均",
            (base_mean - 0.8986) if base_mean else None)
    for sysname, key in [("b2a", "B2a_delta"), ("t1a", "T1a_delta")]:
        h = hbase["systems"].get(sysname, {})
        add_err(key, QUOTED[key]["value"], h.get("delta_vs_baseline"),
                "canonical triple 平均 − S4 canonical triple 平均 (val accuracy)",
                -h["residual"] if "residual" in h else None)
    if h6_search:
        best = (h6_search["oracle_tool_combinations_matching"][0]
                if h6_search["oracle_tool_combinations_matching"] else None)
        add_err("H6_delta", 0.0004,
                (haux_mean - best["mean"]) if best else None,
                "haux canonical triple − oracle-tool 3-run 平均 (val accuracy)",
                (QUOTED["H6_delta"]["value"] - (haux_mean - best["mean"])) if best else None)
    if ot_acc_near:
        add_err("oracle_tool_acc", 0.9583, ot_acc_near[0]["mean"],
                "oracle-tool 3-run 平均 (val accuracy)", -ot_acc_near[0]["residual"])
    else:
        add_err("oracle_tool_acc", 0.9583, None, "UNEXPLAINED", None)
    if ot_f1_hits:
        add_err("oracle_tool_macroF1", 0.823, ot_f1_hits[0]["mean"],
                "oracle-tool 3-run 平均 (val macro-F1)", -ot_f1_hits[0]["residual"])
    else:
        add_err("oracle_tool_macroF1", 0.823, None, "UNEXPLAINED", None)
    add_err("S0_frozen_mAP", 0.7051,
            s0_hits[0]["mean"] if s0_hits else None,
            "s0_* 3-run 平均 (val mAP)" if s0_hits else "UNEXPLAINED",
            -s0_hits[0]["residual"] if s0_hits else None)

    with open(os.path.join(out, "csv", "d1_errata.csv"), "w") as f:
        c = ["quoted_name", "quoted_value", "quoted_source", "recomputed",
             "best_match_convention", "residual", "status"]
        f.write(",".join(c) + "\n")
        for e in errata:
            f.write(",".join(f"\"{e[k]}\"" if isinstance(e[k], str) else str(e[k]) for k in c) + "\n")

    with open(os.path.join(out, "csv", "d1_reconciliation.csv"), "w") as f:
        f.write("convention,label,baseline,split,system,n_seeds,mean,delta,sd,MDE,exceeds_MDE\n")
        for k, v in conventions.items():
            for s, t in v["table"].items():
                f.write(f"{k},\"{v['label']}\",{v['baseline']},{v['split']},{s},"
                        f"{t.get('n_seeds','UNKNOWN')},{t.get('mean','UNKNOWN')},"
                        f"{t.get('delta','UNKNOWN')},{t.get('sd','UNKNOWN')},"
                        f"{t.get('MDE','UNKNOWN')},{t.get('exceeds_MDE','UNKNOWN')}\n")

    # ---- Step D1-7: 規約案 (決定はしない) ---------------------------------- #
    n_unexplained = sum(1 for e in errata if e["status"] == "UNEXPLAINED")
    result = {
        "task": "D1_delta_convention_audit",
        "inventory": {"n_metric_rows": len(rows),
                      "n_runs_by_system": {k: len(v) for k, v in acc.items()}},
        "D1_2_s4_baselines": d1_2,
        "D1_3_H_base": hbase,
        "D1_3_h6_baseline_search": h6_search,
        "D1_3_oracle_tool_audit": oracle_audit,
        "D1_4_conventions": conventions,
        "D1_5_detection": det,
        "D1_6_errata": errata,
        "D1_7_recommendation": {
            "recommended_convention": "K1'（S4 canonical triple = 0.8986 を分母、val、accuracy）",
            "rationale": [
                "引用値 S4 0.8986 / B2a +0.0383 / T1a +0.0497 がこの規約で残差 5e-5 未満で再現する",
                "H-6 の +0.0004 のみ分母が oracle-tool であり、系統ごとに分母が違うことが実測で判明した",
                "分母が系統ごとに異なる現状は、論文の Table で『Δ が何に対する差か』を一意に書けない",
            ],
            "caveats": [
                "H-6 を S4 基準に統一すると Δ は +0.0583 になり、引用値 +0.0004 と両立しない",
                "oracle-tool の引用値は複数の組み合わせが同じ丸め値を与え一意に定まらない",
                "val は 2 動画・test は 3 動画で、いずれも動画数が少なく MDE が大きい",
            ],
            "rewrite_needed_count": n_unexplained,
            "decision": "決定はユーザが行う。本監査は選択肢と根拠の提示に留める。",
        },
    }
    with open(os.path.join(out, "json", "d1_delta_audit.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n=== D1-2: S4 ===\n  run 数={d1_2['n_s4_runs']} (val {d1_2['n_val']} / test {d1_2['n_test']})")
    print(f"  0.8986 を出す 3-run 組み合わせ: {d1_2['n_combinations_producing_0.8986']} 通り")
    for h in s4_hits_8986[:2]:
        print(f"    seeds={h['seeds']} mean={h['mean']:.6f} canonical_triple={h['is_canonical_seed_triple']}")
    if d1_2["step_c_coupling_value"]:
        print(f"  0.8928 の出所: {d1_2['step_c_coupling_value']['source']} "
              f"(val 3-seed 平均 {d1_2['step_c_coupling_value']['val_accuracy_3seed_mean']:.6f})")
    print(f"\n=== D1-3: H-base ===\n  baseline={base_mean:.6f} (引用 0.8986 と一致: {hbase['matches_quoted_0.8986']})")
    for s, v in hbase["systems"].items():
        if "delta_vs_baseline" in v:
            print(f"  {s}: Δ={v['delta_vs_baseline']:+.6f} 引用={v['quoted_delta']:+.4f} "
                  f"残差={v['residual']:+.6f} → {v['status']}")
    if h6_search:
        print(f"  h6: S4基準Δ={h6_search['delta_vs_S4_baseline']:+.6f} / "
              f"引用+0.0004 を満たす分母={h6_search['implied_baseline_for_quoted_delta']:.6f} "
              f"→ oracle-tool 組み合わせ {h6_search['n_matching']} 通り ({h6_search['status']})")
    print(f"  oracle-tool: acc {oracle_audit['status']} (exact {oracle_audit['n_acc_exact']} / "
          f"near {oracle_audit['n_acc_near']}), f1 一致 {oracle_audit['n_f1_matches']} 通り")
    print(f"\n=== D1-5: 検出側 ===\n  S0-frozen 0.7051 を出す組み合わせ: "
          f"{det['n_matching_strict']} 通り(厳密 5e-5) / {det['n_matching_loose_tol5e-4']} 通り(緩 5e-4) "
          f"→ {det['status']}\n  p0 init 平均 {det['p0_init_mean']:.6f} "
          f"差 {det['difference']:+.6f}")
    print(f"\n=== D1-6: 正誤表 ===")
    for e in errata:
        rv = f"{e['recomputed']:.6f}" if isinstance(e["recomputed"], float) else e["recomputed"]
        print(f"  {e['quoted_name']:22s} 引用={e['quoted_value']} 再計算={rv} → {e['status']}")
    print(f"\n=== D1 推奨（決定はユーザが行う） ===\n  {result['D1_7_recommendation']['recommended_convention']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

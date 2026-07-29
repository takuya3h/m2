#!/usr/bin/env python3
"""N3: 全 run 基準での Δ と誤差の再計算。

「代表 3 run を固定する」規約と「標準 seed の全 run を使う」規約で
Δ・誤差・有意判定がどう変わるかを出す。**規約は決定しない。**

3 規約:
  R-triple     各系統の代表 3 run (_001/_002/_003) / 分母 S4 代表 3 run
  R-all        各系統の標準 seed 全 run        / 分母 S4 の標準 seed 全 run
  R-all-dedup  同一 seed は平均して 1 点に畳む  / 同上

N1 の判定 (CONFIG_DIFF + UNCONTROLLED_NONDETERMINISM の両立) を受け、
R-all / R-all-dedup は **同一設定の反復ではない run を混ぜている**点を必ず併記する。

統計量は必ず n と分母の定義を併記する (2026-07-29 に分母の取り違えで誤った結論を 2 回出した前例)。

Usage:
    python3 scripts/analysis/delta_allrun_recompute.py --out $OUT
    python3 scripts/analysis/delta_allrun_recompute.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import statistics

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_SEEDS = {"42", "123", "456"}
SYSTEMS = ["s4", "b2a", "t1a", "h6", "oracle-tool"]
FAMILY = {
    "s4": "s4_phase_baseline_",
    "b2a": "b2a_det2phase_0",
    "t1a": "t1a_regiontoken_0",
    "h6": "haux_hand_presence_oracle_withtooloracle_0",
    "oracle-tool": "b2a_det2phase_oracletool_0",
}
# 研究計画の引用値 (正誤表 v2 用)
QUOTED = {
    "S4_base_accuracy": 0.8986, "B2a_delta": 0.0383, "T1a_delta": 0.0497,
    "H6_delta": 0.0004, "oracle_tool_acc": 0.9583, "oracle_tool_macroF1": 0.823,
    "S0_frozen_mAP": 0.7051,
}
# 両側 alpha=0.05 の t 臨界値 (df=n-1)
T_TABLE = {1: 12.706205, 2: 4.302653, 3: 3.182446, 4: 2.776445, 5: 2.570582,
           6: 2.446912, 7: 2.364624, 8: 2.306004, 9: 2.262157, 10: 2.228139,
           11: 2.200985, 12: 2.178813, 13: 2.160369, 14: 2.144787, 15: 2.131450,
           16: 2.119905, 17: 2.109816, 18: 2.100922, 19: 2.093024, 20: 2.085963}


def t_crit(df: int) -> float:
    """両側 alpha=0.05 の t 臨界値。df>20 は正規近似 (1.96) に漸近させる。"""
    if df <= 0:
        return float("nan")
    if df in T_TABLE:
        return T_TABLE[df]
    # df>20: Cornish-Fisher 的な簡易近似 (df→∞ で 1.959964)
    z = 1.959964
    return z * (1 + (z * z + 1) / (4 * df))



def family_key(run: str) -> str:
    """run 名 {step}_{seq:03d}_{desc}_seed{seed} から {step}|{desc} を取り出す。

    seq と seed を除いた「実験の同一性」を表す鍵。これを誤ると
    _neck / _shuffle などの変種を同一実験と見なしてしまう。
    """
    t = re.sub(r"_seed\d+$", "", run)
    m = re.match(r"^(.*?)_(\d{3})_(.*)$", t)
    return f"{m.group(1)}|{m.group(3)}" if m else t


def classify(run: str) -> str:
    r = run.lower()
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


def load_runs():
    """val の run のみ。{系統: [ {run, seed, acc, f1} ]}"""
    out = {}
    for p in sorted(glob.glob(os.path.join(REPO, "experiments/**/metrics.json"), recursive=True)):
        d_dir = os.path.dirname(p)
        run = os.path.basename(d_dir)
        try:
            m = json.load(open(p))
        except Exception:
            continue
        if "phase_accuracy" not in m:
            continue
        cmd_p = os.path.join(d_dir, "command.sh")
        cmd = open(cmd_p).read() if os.path.exists(cmd_p) else ""
        if "--eval-test" in cmd:
            continue
        s = classify(run)
        if s not in SYSTEMS:
            continue
        out.setdefault(s, []).append({
            "run": run, "seed": run.split("seed")[-1] if "seed" in run else "UNKNOWN",
            "acc": m["phase_accuracy"], "f1": m.get("phase_macro_f1"),
        })
    return out


def select(runs, system, convention):
    """規約に応じて値のリストを返す。返り値は (values, n, 説明)。"""
    rs = runs.get(system, [])
    if convention == "R-triple":
        tri = sorted([r for r in rs if r["run"].startswith(FAMILY[system])
                      and any(f"_{n:03d}_" in r["run"] for n in (1, 2, 3))],
                     key=lambda x: x["run"])[:3]
        return [r["acc"] for r in tri], len(tri), f"{FAMILY[system]}00{{1,2,3}} の 3 run"
    if convention == "R-all":
        v = [r["acc"] for r in rs if r["seed"] in CANONICAL_SEEDS]
        return v, len(v), "標準 seed (42/123/456) の全 run"
    if convention == "R-all-dedup":
        by = {}
        for r in rs:
            if r["seed"] in CANONICAL_SEEDS:
                by.setdefault(r["seed"], []).append(r["acc"])
        v = [statistics.mean(x) for x in by.values()]
        return v, len(v), "標準 seed ごとに平均して 1 点に畳む"
    if convention == "R-family":
        # 系統プールには複数の実験 family が混在する (実測: b2a 73 / t1a 53 / h6 6 / s4 3 family)。
        # 「同じ実験のまま n を増やす」比較にするため、
        # 代表 3 run と **厳密に同じ family key** の run に限定する。
        tri = sorted([r for r in rs if r["run"].startswith(FAMILY[system])
                      and any(f"_{n:03d}_" in r["run"] for n in (1, 2, 3))],
                     key=lambda x: x["run"])[:3]
        if not tri:
            return [], 0, "代表 3 run が特定できない"
        fk = family_key(tri[0]["run"])
        v = [r["acc"] for r in rs
             if family_key(r["run"]) == fk and r["seed"] in CANONICAL_SEEDS]
        return v, len(v), f"family={fk} の標準 seed 全 run"
    raise ValueError(convention)


def stats_of(vals):
    n = len(vals)
    if n == 0:
        return {"n": 0}
    mean = statistics.mean(vals)
    sd = statistics.stdev(vals) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n > 1 else 0.0
    tc = t_crit(n - 1) if n > 1 else float("nan")
    ci = tc * se if n > 1 else float("nan")
    return {"n": n, "mean": mean, "sd": sd, "se": se,
            "ci95_halfwidth": ci, "ci95": [mean - ci, mean + ci] if n > 1 else None}


def mde_two_sample(sd, n):
    """2 群 (各 n・共通 sd) の差を検出できる最小効果量。
    MDE = t(0.975, n-1) * sd * sqrt(2/n)
    """
    if n < 2:
        return float("nan")
    return t_crit(n - 1) * sd * math.sqrt(2.0 / n)


def self_test() -> int:
    """検出できることを確認する:
       1) n が増えると MDE が縮むこと
       2) MDE 式が既知値を再現すること
       3) 規約ごとに選択される run が変わること
    """
    ok = True
    # 1) n 依存
    m3 = mde_two_sample(0.01, 3)
    m6 = mde_two_sample(0.01, 6)
    if not (m6 < m3):
        print(f"  [FAIL] n が増えて MDE が縮まない: n3={m3} n6={m6}"); ok = False
    else:
        print(f"  [OK]   n 増加で MDE が縮む (n=3 {m3:.5f} -> n=6 {m6:.5f})")
    # 2) 既知値: t(0.975,2)=4.302653, sd=0.01, n=3 -> 4.302653*0.01*sqrt(2/3)=0.035134
    exp = 4.302653 * 0.01 * math.sqrt(2 / 3)
    if abs(m3 - exp) > 1e-9:
        print(f"  [FAIL] MDE 既知値: {m3} vs {exp}"); ok = False
    else:
        print(f"  [OK]   MDE 式が既知値を再現 ({m3:.6f})")
    # 3) 規約による選択差
    runs = {"x": [{"run": "x_001_seed42", "seed": "42", "acc": 0.90, "f1": 0},
                  {"run": "x_002_seed123", "seed": "123", "acc": 0.92, "f1": 0},
                  {"run": "x_003_seed456", "seed": "456", "acc": 0.94, "f1": 0},
                  {"run": "x_010_seed42", "seed": "42", "acc": 0.80, "f1": 0}]}
    FAMILY["x"] = "x_0"
    v1, n1, _ = select(runs, "x", "R-triple")
    v2, n2, _ = select(runs, "x", "R-all")
    v3, n3, _ = select(runs, "x", "R-all-dedup")
    if not (n1 == 3 and n2 == 4 and n3 == 3):
        print(f"  [FAIL] 規約別の n: {n1}/{n2}/{n3}"); ok = False
    else:
        print(f"  [OK]   規約で選択が変わる (triple n=3 / all n=4 / dedup n=3)")
    if abs(statistics.mean(v3) - statistics.mean([0.85, 0.92, 0.94])) > 1e-12:
        print(f"  [FAIL] dedup の畳み込み: {v3}"); ok = False
    else:
        print("  [OK]   dedup が同一 seed を平均して 1 点に畳む (42: 0.90,0.80 -> 0.85)")
    del FAMILY["x"]
    # 4) sd=0 のとき MDE=0 を有意の根拠にしない
    if mde_two_sample(0.0, 3) != 0.0:
        print("  [FAIL] sd=0 の扱い"); ok = False
    else:
        print("  [OK]   sd=0 で MDE=0 (縮退ケースを検出可能)")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out"); ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--n1-json", default=None, help="N1 の判定 JSON (依存関係の明記用)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.out:
        ap.error("--out か --self-test が必要")
    for sub in ("json", "csv"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)

    runs = load_runs()
    n1_verdict = "UNKNOWN"
    p = args.n1_json or os.path.join(args.out, "json", "n1_same_seed.json")
    if os.path.exists(p):
        try:
            n1_verdict = json.load(open(p)).get("N1_4_verdict", "UNKNOWN")
        except Exception:
            pass

    # ---- N3-1 / N3-2: 3 規約で Δ・sd・n・CI・MDE ---------------------------- #
    conventions = {}
    for conv in ("R-triple", "R-family", "R-all", "R-all-dedup"):
        base_vals, base_n, base_desc = select(runs, "s4", conv)
        base = stats_of(base_vals)
        table = {}
        for sysname in SYSTEMS:
            vals, n, desc = select(runs, sysname, conv)
            st = stats_of(vals)
            if st["n"] == 0 or base["n"] == 0:
                table[sysname] = {"status": "UNKNOWN", "n": st.get("n", 0)}
                continue
            delta = st["mean"] - base["mean"]
            # 2 群の共通 sd (プールされた分散)
            if st["n"] > 1 and base["n"] > 1:
                sp = math.sqrt(((st["n"] - 1) * st["sd"] ** 2 + (base["n"] - 1) * base["sd"] ** 2)
                               / (st["n"] + base["n"] - 2))
                nmin = min(st["n"], base["n"])
                mde = mde_two_sample(sp, nmin)
            else:
                sp, nmin, mde = float("nan"), min(st["n"], base["n"]), float("nan")
            table[sysname] = {
                "selection": desc, "n": st["n"], "mean": st["mean"], "sd": st["sd"],
                "ci95_halfwidth": st["ci95_halfwidth"], "ci95": st["ci95"],
                "denominator_n": base["n"], "denominator_mean": base["mean"],
                "delta": delta, "pooled_sd": sp, "n_used_for_MDE": nmin, "MDE": mde,
                "exceeds_MDE": (abs(delta) > mde) if not math.isnan(mde) else None,
            }
        conventions[conv] = {"baseline_system": "s4", "baseline_selection": base_desc,
                             "baseline": base, "table": table}

    # MDE がどれだけ縮むか
    mde_shrink = {}
    for sysname in SYSTEMS:
        a = conventions["R-triple"]["table"].get(sysname, {}).get("MDE")
        b = conventions["R-all"]["table"].get(sysname, {}).get("MDE")
        if a and b and not (math.isnan(a) or math.isnan(b)):
            mde_shrink[sysname] = {"MDE_R_triple": a, "MDE_R_all": b,
                                   "ratio_all_over_triple": b / a,
                                   "n_triple": conventions["R-triple"]["table"][sysname]["n"],
                                   "n_all": conventions["R-all"]["table"][sysname]["n"]}

    # ---- N3-3: 有意判定が反転する箇所 -------------------------------------- #
    flips = []
    for sysname in SYSTEMS:
        vals = {c: conventions[c]["table"].get(sysname, {}).get("exceeds_MDE")
                for c in conventions}
        uniq = {v for v in vals.values() if v is not None}
        if len(uniq) > 1:
            flips.append({"system": sysname, "exceeds_MDE_by_convention": vals,
                          "delta_by_convention": {c: conventions[c]["table"][sysname].get("delta")
                                                  for c in conventions},
                          "linked_claim": {
                              "h6": "H-6 の +0.0004 →「手は術具に対して冗長」という結論",
                              "b2a": "B2a の tool-presence 注入効果",
                              "t1a": "T1a の region-token 注入効果 (G-2 の比較対象)",
                              "oracle-tool": "oracle-tool = 注入の上限",
                              "s4": "S4 は分母自身",
                          }.get(sysname, "UNKNOWN")})

    # ---- N3-4: H-6 を 4 分母で評価 ----------------------------------------- #
    h6_triple = select(runs, "h6", "R-triple")[0]
    h6_mean_triple = statistics.mean(h6_triple) if h6_triple else None
    h6_all = select(runs, "h6", "R-all")[0]
    h6_mean_all = statistics.mean(h6_all) if h6_all else None
    ot_all_vals = select(runs, "oracle-tool", "R-all")[0]
    ot_all = stats_of(ot_all_vals)
    s4_all = stats_of(select(runs, "s4", "R-all")[0])
    h6_all_st = stats_of(h6_all)

    def mde_pair(a, b):
        if a["n"] < 2 or b["n"] < 2:
            return float("nan"), 0
        sp = math.sqrt(((a["n"] - 1) * a["sd"] ** 2 + (b["n"] - 1) * b["sd"] ** 2)
                       / (a["n"] + b["n"] - 2))
        nmin = min(a["n"], b["n"])
        return mde_two_sample(sp, nmin), nmin

    h6_eval = []
    for label, base_val, base_stats in [
        ("oracle-tool 0.958196 (固定値)", 0.958196, None),
        ("oracle-tool 0.956436 (固定値)", 0.956436, None),
        ("oracle-tool (R-all)", ot_all.get("mean"), ot_all),
        ("S4 (R-all)", s4_all.get("mean"), s4_all),
    ]:
        if base_val is None:
            h6_eval.append({"denominator": label, "status": "UNKNOWN"}); continue
        # 分子は R-all の H-6 を使う (n を増やした効果を見るため)
        delta = (h6_mean_all - base_val) if h6_mean_all is not None else None
        if base_stats is not None:
            mde, nmin = mde_pair(h6_all_st, base_stats)
        else:
            # 固定値なので 1 標本 t 検定相当: MDE = t(0.975,n-1)*sd/sqrt(n)
            mde = (t_crit(h6_all_st["n"] - 1) * h6_all_st["sd"] / math.sqrt(h6_all_st["n"])
                   if h6_all_st["n"] > 1 else float("nan"))
            nmin = h6_all_st["n"]
        h6_eval.append({
            "denominator": label, "denominator_value": base_val,
            "denominator_n": (base_stats["n"] if base_stats else "固定値 (n 不明)"),
            "h6_numerator": "R-all", "h6_n": h6_all_st["n"], "h6_mean": h6_mean_all,
            "delta": delta, "MDE": mde, "n_used_for_MDE": nmin,
            "exceeds_MDE": (abs(delta) > mde) if (delta is not None and not math.isnan(mde)) else None,
        })
    # 参考: R-triple の H-6
    h6_eval.append({
        "denominator": "oracle-tool 0.956436 (固定値)", "denominator_value": 0.956436,
        "h6_numerator": "R-triple", "h6_n": len(h6_triple), "h6_mean": h6_mean_triple,
        "delta": (h6_mean_triple - 0.956436) if h6_mean_triple else None,
        "MDE": conventions["R-triple"]["table"].get("h6", {}).get("MDE"),
        "note": "前タスクの値 (+0.000440) と対応する組み合わせ",
    })

    # ---- N3-5: 正誤表 v2 --------------------------------------------------- #
    errata = []
    for name, q in QUOTED.items():
        row = {"quoted_name": name, "quoted_value": q}
        for conv in conventions:
            t = conventions[conv]["table"]
            if name == "S4_base_accuracy":
                row[conv] = conventions[conv]["baseline"]["mean"]
            elif name == "B2a_delta":
                row[conv] = t.get("b2a", {}).get("delta")
            elif name == "T1a_delta":
                row[conv] = t.get("t1a", {}).get("delta")
            elif name == "H6_delta":
                row[conv] = t.get("h6", {}).get("delta")
            elif name == "oracle_tool_acc":
                row[conv] = t.get("oracle-tool", {}).get("mean")
            else:
                row[conv] = None
        base_v = row.get("R-triple")
        if base_v is None:
            row["status"] = "NOT_RECOMPUTED"
        else:
            changed = any(row.get(c) is not None and abs(row[c] - base_v) > 5e-5
                          for c in ("R-all", "R-all-dedup"))
            sysname = {"B2a_delta": "b2a", "T1a_delta": "t1a", "H6_delta": "h6",
                       "oracle_tool_acc": "oracle-tool"}.get(name)
            flipped = any(f["system"] == sysname for f in flips) if sysname else False
            row["status"] = ("SIGNIFICANCE_FLIPPED" if flipped
                             else ("CHANGED" if changed else "UNCHANGED"))
        errata.append(row)

    # 系統プールに何 family 含まれるかを実測 (R-all の解釈に必須)
    fam_count = {}
    for sysname in SYSTEMS:
        fams = {}
        for r in runs.get(sysname, []):
            f = family_key(r["run"])
            fams.setdefault(f, 0)
            fams[f] += 1
        fam_count[sysname] = {"n_families": len(fams), "families": fams}

    res = {
        "task": "N3_delta_allrun_recompute",
        "pool_composition": {
            "measurement": fam_count,
            "why_it_matters": (
                "『系統の標準 seed 全 run』(R-all) は、系統プールに複数の実験 family が "
                "混在する場合、別実験を束ねてしまう。実測では h6 に 6 family が含まれ、"
                "うち H-6 本体は haux_hand_presence_oracle_withtooloracle のみ (acc 0.955-0.958)、"
                "残り 5 family は ablation (acc 0.887-0.914)。"
                "したがって R-all における h6 の有意判定の変化は "
                "『n を増やした統計的効果』ではなく『別実験を混ぜた artifact』である。"
                "同一実験のまま n を増やす比較には R-family を使う。"),
        },
        "N1_verdict_dependency": {
            "n1_verdict": n1_verdict,
            "implication": (
                "N1 は CONFIG_DIFF と UNCONTROLLED_NONDETERMINISM の両立と判定された。"
                "したがって R-all / R-all-dedup が束ねる run は『同一設定の独立반復』ではなく、"
                "別ホスト・別コミットの run を含む。n を増やして得た CI/MDE は "
                "『設定差を含んだばらつき』であり、純粋な統計的検出力の向上とは言えない。"
                "R-triple は逆に、条件は近いが n=3 で分散を過小評価しうる。"),
        },
        "MDE_formula": "MDE = t(0.975, n-1) * pooled_sd * sqrt(2/n)  (n = min(系統 n, 分母 n))",
        "t_crit_note": "df<=20 は数表、df>20 は正規近似 z=1.959964*(1+(z^2+1)/(4df))",
        "N3_1_conventions": conventions,
        "N3_2_mde_shrink": mde_shrink,
        "N3_3_significance_flips": flips,
        "N3_4_h6_by_denominator": h6_eval,
        "N3_5_errata_v2": errata,
        "N3_6_recommendation": {
            "note": "検出力・恣意性・書き換え件数のトレードオフ",
            "R-triple": {"pros": "条件が最も近い (同一 family・連番)",
                         "cons": "n=3 で sd と MDE が不安定。run 選択が恣意的に見える"},
            "R-all": {"pros": "n が増え CI が縮む",
                      "cons": "別ホスト・別コミットの run を混ぜる (N1)。ablation 派生 run も混入"},
            "R-all-dedup": {"pros": "seed あたり 1 点で seed 数=3 を保ちつつ重複を吸収",
                            "cons": "同上の混入問題は残る"},
            "decision": "決定はユーザが行う。本タスクは候補と根拠の提示に留める。",
        },
    }
    with open(os.path.join(args.out, "json", "n3_delta_allrun.json"), "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False, default=str)

    cols = ["convention", "system", "selection", "n", "mean", "sd", "ci95_halfwidth",
            "denominator_n", "denominator_mean", "delta", "pooled_sd", "n_used_for_MDE",
            "MDE", "exceeds_MDE"]
    with open(os.path.join(args.out, "csv", "n3_delta_by_convention.csv"), "w") as f:
        f.write(",".join(cols) + "\n")
        for conv, cv in conventions.items():
            for sysname, t in cv["table"].items():
                row = {"convention": conv, "system": sysname, **t}
                f.write(",".join(f"\"{row.get(c)}\"" if isinstance(row.get(c), str)
                                 else str(row.get(c)) for c in cols) + "\n")
    with open(os.path.join(args.out, "csv", "n3_errata_v2.csv"), "w") as f:
        f.write("quoted_name,quoted_value,R-triple,R-all,R-all-dedup,status\n")
        for e in errata:
            f.write(f"{e['quoted_name']},{e['quoted_value']},{e.get('R-triple')},"
                    f"{e.get('R-all')},{e.get('R-all-dedup')},{e['status']}\n")

    print(f"N1 判定への依存: {n1_verdict}")
    for conv, cv in conventions.items():
        print(f"\n=== {conv} (分母 s4: n={cv['baseline']['n']} mean={cv['baseline']['mean']:.6f}) ===")
        for sysname, t in cv["table"].items():
            if t.get("status") == "UNKNOWN":
                print(f"  {sysname:12s} UNKNOWN"); continue
            print(f"  {sysname:12s} n={t['n']:3d} mean={t['mean']:.6f} sd={t['sd']:.6f} "
                  f"Δ={t['delta']:+.6f} MDE={t['MDE']:.6f} 超過={t['exceeds_MDE']}")
    print("\n=== N3-2: MDE の縮み (R-triple -> R-all) ===")
    for s, v in mde_shrink.items():
        print(f"  {s:12s} n {v['n_triple']}->{v['n_all']}  MDE {v['MDE_R_triple']:.6f} -> "
              f"{v['MDE_R_all']:.6f} ({v['ratio_all_over_triple']:.2f}x)")
    print("\n=== N3-3: 有意判定が反転する系統 ===")
    for fl in flips:
        print(f"  {fl['system']}: {fl['exceeds_MDE_by_convention']}")
        print(f"     紐づく結論: {fl['linked_claim']}")
    if not flips:
        print("  なし")
    print("\n=== N3-4: H-6 を分母別に評価 ===")
    for h in h6_eval:
        if h.get("status") == "UNKNOWN":
            continue
        print(f"  {h['denominator']:32s} 分子={h['h6_numerator']:9s} n={h['h6_n']:2d} "
              f"Δ={h['delta']:+.6f} MDE={h['MDE']:.6f} 超過={h.get('exceeds_MDE')}")
    print("\n=== N3-5: 正誤表 v2 ===")
    for e in errata:
        print(f"  {e['quoted_name']:22s} 引用={e['quoted_value']} → {e['status']}")
    print("\n  規約の決定はユーザが行う。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""T3: oracle-tool の正本 run 候補を固定する（決定はしない）。

「oracle-tool」の名前で 2 つのベースラインが流通している:
  0.958196 … 研究計画の引用値 0.9583 に対応する 3-run 平均
  0.956436 … H-6 の Δ (+0.0004) を成立させる分母として特定された 3-run 平均

どちらを正本にするかで H-6 の Δ が変わるため、候補と根拠を並べる。
あわせて「canonical triple を規約に含めるか否か」で各系統の Δ がどれだけ動くかを定量化する。

Usage:
    python3 scripts/analysis/fix_oracle_canonical.py --out $OUT
    python3 scripts/analysis/fix_oracle_canonical.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import statistics
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANONICAL_SEEDS = {"42", "123", "456"}
T_CRIT_DF2 = 4.302652

# §1.4 の所与（再確認の対象）
TARGETS = {"quoted_0.9583": 0.958196, "h6_denominator": 0.956436}
H6_MEAN = 0.956876
S4_CANONICAL = 0.898570
MDE = {"b2a": 0.00264, "t1a": 0.00291, "h6": 0.01094, "oracle-tool": 0.00744}

# D1 で確定した canonical family（実測で確認済み）
FAMILY = {
    "s4": "s4_phase_baseline_",
    "b2a": "b2a_det2phase_0",
    "t1a": "t1a_regiontoken_0",
    "h6": "haux_hand_presence_oracle_withtooloracle_0",
    "oracle-tool": "b2a_det2phase_oracletool_0",
}


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


def seed_of(run: str) -> str:
    return run.split("seed")[-1] if "seed" in run else "UNKNOWN"


def load_runs():
    """{系統: [ {run, seed, acc, f1, config, mtime, is_canonical_seed, split} ]}"""
    out = {}
    for p in sorted(glob.glob(os.path.join(REPO, "experiments/**/metrics.json"), recursive=True)):
        d_dir = os.path.dirname(p)
        run = os.path.basename(d_dir)
        try:
            with open(p) as f:
                d = json.load(f)
        except Exception:
            continue
        if "phase_accuracy" not in d:
            continue
        cmd_p = os.path.join(d_dir, "command.sh")
        cmd = open(cmd_p).read() if os.path.exists(cmd_p) else ""
        cfg = os.path.join(d_dir, "config.yaml")
        sysname = classify(run)
        out.setdefault(sysname, []).append({
            "run": run, "seed": seed_of(run),
            "acc": d.get("phase_accuracy"), "f1": d.get("phase_macro_f1"),
            "split": "test" if "--eval-test" in cmd else ("val" if cmd else "UNKNOWN"),
            "config": os.path.relpath(cfg, REPO) if os.path.exists(cfg) else "UNKNOWN",
            "mtime": os.path.getmtime(p),
            "is_canonical_seed": seed_of(run) in CANONICAL_SEEDS,
        })
    return out


def find_triples(runs, target, tol=5e-6):
    """3-run 平均が target に一致する組み合わせを全列挙。"""
    hits = []
    for c in itertools.combinations(range(len(runs)), 3):
        sub = [runs[i] for i in c]
        m = statistics.mean(x["acc"] for x in sub)
        if abs(m - target) <= tol:
            seeds = sorted(x["seed"] for x in sub)
            hits.append({
                "runs": [x["run"] for x in sub], "seeds": [x["seed"] for x in sub],
                "mean": m, "residual": m - target,
                "all_canonical_seeds": all(x["is_canonical_seed"] for x in sub),
                "distinct_canonical_triple": sorted(seeds) == sorted(CANONICAL_SEEDS),
                "is_min_seq_family": all(any(f"_{n:03d}_" in x["run"] for n in (1, 2, 3))
                                         for x in sub),
            })
    hits.sort(key=lambda h: (not h["distinct_canonical_triple"], not h["is_min_seq_family"],
                             abs(h["residual"])))
    return hits


def mde_of(vals):
    if len(vals) < 2:
        return None
    sd = statistics.stdev(vals)
    return T_CRIT_DF2 * sd / (len(vals) ** 0.5), sd


def self_test() -> int:
    """検出できることを確認する:
       1) 目標平均を与える 3-run 組み合わせを列挙できるか
       2) canonical seed 3 つ組かどうかを正しく判定できるか
       3) 一意に定まらない場合に複数候補を返せるか
    """
    ok = True
    runs = [
        {"run": "x_001_seed42", "seed": "42", "acc": 0.90, "is_canonical_seed": True},
        {"run": "x_002_seed123", "seed": "123", "acc": 0.92, "is_canonical_seed": True},
        {"run": "x_003_seed456", "seed": "456", "acc": 0.94, "is_canonical_seed": True},
        {"run": "x_010_seed789", "seed": "789", "acc": 0.91, "is_canonical_seed": False},
        {"run": "x_011_seed1000", "seed": "1000", "acc": 0.93, "is_canonical_seed": False},
    ]
    hits = find_triples(runs, 0.92)
    if not hits:
        print("  [FAIL] 目標平均の組み合わせを見つけられない"); ok = False
    else:
        print(f"  [OK]   目標平均 0.92 を与える組み合わせを {len(hits)} 通り列挙")
    top = hits[0]
    if not top["distinct_canonical_triple"]:
        print(f"  [FAIL] canonical 3 つ組を優先できない: {top['seeds']}"); ok = False
    else:
        print(f"  [OK]   canonical seed 3 つ組を優先して先頭に出す (seeds={top['seeds']})")
    if len(hits) < 2:
        print(f"  [FAIL] 複数候補（曖昧性）を返せない: {len(hits)}"); ok = False
    else:
        print(f"  [OK]   一意に定まらない状況を複数候補として返せる ({len(hits)} 通り)")
    if find_triples(runs, 0.111):
        print("  [FAIL] 存在しない目標に偽の一致"); ok = False
    else:
        print("  [OK]   一致が無ければ空 (UNKNOWN を作れる)")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out"); ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.out:
        ap.error("--out か --self-test が必要")
    for sub in ("json", "csv"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)

    allruns = load_runs()
    ot = sorted([r for r in allruns.get("oracle-tool", []) if r["split"] == "val"],
                key=lambda x: x["run"])

    # ---- T3-1: 全 run 列挙 -------------------------------------------------- #
    with open(os.path.join(args.out, "csv", "t3_oracle_runs.csv"), "w") as f:
        f.write("run,seed,is_canonical_seed,val_accuracy,val_macro_f1,config,mtime\n")
        for r in ot:
            f.write(f"\"{r['run']}\",{r['seed']},{r['is_canonical_seed']},{r['acc']},{r['f1']},"
                    f"\"{r['config']}\",{r['mtime']}\n")

    # ---- T3-2: 2 つの平均値の出所 ------------------------------------------ #
    origins = {}
    for name, tgt in TARGETS.items():
        hits = find_triples(ot, tgt)
        uniq_canon = [h for h in hits if h["distinct_canonical_triple"] and h["is_min_seq_family"]]
        origins[name] = {
            "target": tgt, "n_combinations": len(hits),
            "n_canonical_and_min_seq": len(uniq_canon),
            "uniquely_determined": len(uniq_canon) == 1,
            "canonical_min_seq_candidates": uniq_canon[:5],
            "all_candidates_top5": hits[:5],
        }

    # ---- T3-3: 候補別 H-6 Δ ------------------------------------------------- #
    h6_deltas = []
    for label, base in [("oracle-tool 0.958196", TARGETS["quoted_0.9583"]),
                        ("oracle-tool 0.956436", TARGETS["h6_denominator"]),
                        ("S4 canonical 0.898570", S4_CANONICAL)]:
        delta = H6_MEAN - base
        h6_deltas.append({"denominator": label, "denominator_value": base,
                          "h6_mean": H6_MEAN, "delta": delta,
                          "MDE_h6": MDE["h6"], "exceeds_MDE": abs(delta) > MDE["h6"],
                          "quoted_delta": 0.0004,
                          "matches_quoted": abs(delta - 0.0004) < 5e-5})

    # ---- T3-4: run 選択の振れ幅 -------------------------------------------- #
    s4_all = [r for r in allruns.get("s4", []) if r["split"] == "val"]
    s4_canon_all = [r for r in s4_all if r["is_canonical_seed"]]
    base_all = statistics.mean(r["acc"] for r in s4_canon_all) if s4_canon_all else None

    swing = {}
    for sysname in ("b2a", "t1a", "h6", "oracle-tool"):
        rs = [r for r in allruns.get(sysname, []) if r["split"] == "val"]
        tri = sorted([r for r in rs if r["run"].startswith(FAMILY[sysname])
                      and any(f"_{n:03d}_" in r["run"] for n in (1, 2, 3))],
                     key=lambda x: x["run"])[:3]
        canon_all = [r for r in rs if r["is_canonical_seed"]]
        if not tri or not canon_all or base_all is None:
            swing[sysname] = {"status": "UNKNOWN"}
            continue
        m_tri = statistics.mean(r["acc"] for r in tri)
        m_all = statistics.mean(r["acc"] for r in canon_all)
        # (A) 分子の run 選択だけを変える (分母は S4 canonical triple に固定)
        d_tri = m_tri - S4_CANONICAL
        d_all_num = m_all - S4_CANONICAL
        diff_num = d_tri - d_all_num
        # (B) 分子・分母の双方を「全 canonical-seed run 平均」に変える
        d_all_both = m_all - base_all
        diff_both = d_tri - d_all_both
        swing[sysname] = {
            "canonical_triple_runs": [r["run"] for r in tri],
            "n_all_canonical_seed_runs": len(canon_all),
            "mean_canonical_triple": m_tri,
            "mean_all_canonical_runs": m_all,
            "delta_canonical_triple": d_tri,
            # (A) 分子のみ変更 — 指示書 T3-4 の例 (T1a 差 -0.0060) に対応する定義
            "delta_all_runs_same_denominator": d_all_num,
            "difference_numerator_only": diff_num,
            "difference_numerator_only_exceeds_MDE": abs(diff_num) > MDE[sysname],
            "ratio_to_MDE_numerator_only": abs(diff_num) / MDE[sysname],
            # (B) 分子・分母とも変更
            "delta_all_runs_and_baseline": d_all_both,
            "difference_both": diff_both,
            "difference_both_exceeds_MDE": abs(diff_both) > MDE[sysname],
            "ratio_to_MDE_both": abs(diff_both) / MDE[sysname],
            "MDE": MDE[sysname],
            # 判定には (A) を使う (run 選択の影響を分離できるため)
            "difference": diff_num,
            "difference_exceeds_MDE": abs(diff_num) > MDE[sysname],
            "ratio_to_MDE": abs(diff_num) / MDE[sysname],
        }

    # ---- T3-5: 規約案（決定しない） ----------------------------------------- #
    n_exceed = sum(1 for v in swing.values()
                   if v.get("difference_exceeds_MDE") is True)
    res = {
        "task": "T3_oracle_canonical",
        "T3_1_n_oracle_tool_val_runs": len(ot),
        "T3_2_origins": origins,
        "T3_3_h6_delta_by_denominator": h6_deltas,
        "T3_4_run_selection_swing": swing,
        "T3_4_summary": {
            "n_systems_whose_swing_exceeds_MDE": n_exceed,
            "interpretation": ("canonical triple を規約に含めるか否かで動く Δ が MDE を超える系統数。"
                              "1 つでも超えるなら、規約は『どの run を canonical とするか』を"
                              "明示しなければ結論が変わりうる。"),
        },
        "T3_5_recommendation": {
            "oracle_tool_canonical_recommendation": None,   # 下で埋める
            "rationale": [],
            "canonical_run_spec_should_be_in_convention": n_exceed > 0,
            "h6_denominator_options": {
                "keep_oracle_tool": {
                    "delta": H6_MEAN - TARGETS["h6_denominator"],
                    "matches_quoted_0.0004": True,
                    "rewrite_count": 0,
                    "problem": "系統ごとに分母が異なる状態が残り、論文で Δ の定義を一意に書けない",
                },
                "unify_to_S4": {
                    "delta": H6_MEAN - S4_CANONICAL,
                    "matches_quoted_0.0004": False,
                    "rewrite_count": 1,
                    "problem": "H-6 の引用値 +0.0004 が +0.0583 に変わり、既存記述 1 件の書き換えが必要",
                },
            },
            "decision": "決定はユーザが行う。本タスクは候補と根拠の提示に留める。",
        },
    }
    # oracle-tool の推奨: canonical seed 3 つ組かつ最小連番で一意に定まる方
    uniq = {k: v for k, v in origins.items() if v["uniquely_determined"]}
    if len(uniq) == 1:
        k = list(uniq)[0]
        res["T3_5_recommendation"]["oracle_tool_canonical_recommendation"] = k
        res["T3_5_recommendation"]["rationale"].append(
            f"{k} のみが『canonical seed 3 つ組かつ最小連番 family』で一意に定まる")
    elif len(uniq) == 0:
        res["T3_5_recommendation"]["oracle_tool_canonical_recommendation"] = "UNDETERMINED"
        res["T3_5_recommendation"]["rationale"].append(
            "どちらの目標値も canonical seed 3 つ組かつ最小連番では一意に定まらない")
    else:
        res["T3_5_recommendation"]["oracle_tool_canonical_recommendation"] = "AMBIGUOUS"
        res["T3_5_recommendation"]["rationale"].append(
            "両方の目標値が条件を満たしてしまい一意に定まらない")

    with open(os.path.join(args.out, "json", "t3_oracle_canonical.json"), "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print(f"=== T3-1: oracle-tool val run = {len(ot)} 件 ===")
    for r in ot:
        print(f"  {r['run'][:58]:58s} seed={r['seed']:5s} canon={str(r['is_canonical_seed']):5s} "
              f"acc={r['acc']:.6f} f1={r['f1']:.4f}")
    print("\n=== T3-2: 2 つの平均値の出所 ===")
    for k, v in origins.items():
        print(f"  {k} (={v['target']}): 全 {v['n_combinations']} 通り / "
              f"canonical3つ組かつ最小連番 {v['n_canonical_and_min_seq']} 通り → "
              f"一意={v['uniquely_determined']}")
        for c in v["canonical_min_seq_candidates"][:2]:
            print(f"     seeds={c['seeds']} runs={[x[-28:] for x in c['runs']]}")
    print("\n=== T3-3: 分母候補別 H-6 Δ (MDE 0.01094) ===")
    for h in h6_deltas:
        print(f"  {h['denominator']:26s} Δ={h['delta']:+.6f} "
              f"MDE超過={str(h['exceeds_MDE']):5s} 引用+0.0004と一致={h['matches_quoted']}")
    print("\n=== T3-4: run 選択の振れ幅 (canonical triple vs 全 canonical-seed run) ===")
    for s, v in swing.items():
        if v.get("status") == "UNKNOWN":
            print(f"  {s:12s} UNKNOWN"); continue
        print(f"  {s:12s} Δ_triple={v['delta_canonical_triple']:+.6f} "
              f"Δ_all(同分母)={v['delta_all_runs_same_denominator']:+.6f} "
              f"差={v['difference_numerator_only']:+.6f} "
              f"MDE={v['MDE']:.5f} 超過={str(v['difference_exceeds_MDE']):5s} "
              f"({v['ratio_to_MDE']:.1f}x)")
    print(f"\n  → MDE を超える系統: {n_exceed} / {len(swing)}")
    print(f"\n=== T3-5 推奨: oracle-tool 正本 = "
          f"{res['T3_5_recommendation']['oracle_tool_canonical_recommendation']} ===")
    print("  決定はユーザが行う。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

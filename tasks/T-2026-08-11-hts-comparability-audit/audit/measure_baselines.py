"""Phase C — 基準点の条件と、neck 追加の前例を索引から実測する。読み取りのみ。"""

import collections
import csv
import statistics

IDX = "runindex/index.csv"
EXP = "runindex/experiments.csv"

BASELINES = {
    "検出 neck 無し": ("baselines/s0_frozen/relationdetr_s0frozen_cocohead@val", "metric.mAP"),
    "検出 neck 有り": ("baselines/s0_frozen/relationdetr_s0frozen_neck_cocohead@val", "metric.mAP"),
    "工程 neck 無し": (
        "phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42",
        "metric.accuracy",
    ),
    "工程 neck 有り": (
        "phase1/s4_phase_baseline/frozen_tecno_phase_baseline_neck@val~relation_detr_seed42",
        "metric.accuracy",
    ),
}

rows = list(csv.DictReader(open(IDX)))
by_exp = collections.defaultdict(list)
for r in rows:
    by_exp[r["experiment_id"]].append(r)

print("=" * 72)
print("1. 基準点 4 つの条件（run 単位の実測）")
print("=" * 72)

per_seed = {}
for label, (eid, mkey) in BASELINES.items():
    rs = [r for r in by_exp[eid] if r.get("excluded", "").lower() not in ("true", "1", "yes")]
    print(f"\n--- {label} ---\n  experiment_id: {eid}")
    print(f"  run 数: {len(by_exp[eid])}（除外後 {len(rs)}）")
    for field in ("frozen_source_tag", "eval_recipe_id", "split", "metrics_primary_split", "host", "arm", "commit"):
        vals = sorted({r.get(field, "") for r in rs})
        print(f"  {field:22s}: {vals}")
    vals = {}
    for r in rs:
        v = r.get(mkey, "")
        if v:
            vals.setdefault(r.get("seed", "?"), []).append(float(v))
    per_seed[label] = vals
    print(f"  seed 別 {mkey}:")
    for s in sorted(vals):
        xs = vals[s]
        print(f"    seed {s:>4s}: n={len(xs)} 値={[round(x, 6) for x in xs]}")


def pooled(vals):
    """seed ごとに平均してから系列を作る。"""
    return {s: statistics.fmean(xs) for s, xs in vals.items()}


print("\n" + "=" * 72)
print("2. neck 追加の効果（seed 対応 paired Δ・σ 既定は pstd）")
print("=" * 72)

for task, a, b in (
    ("検出", "検出 neck 無し", "検出 neck 有り"),
    ("工程", "工程 neck 無し", "工程 neck 有り"),
):
    pa, pb = pooled(per_seed[a]), pooled(per_seed[b])
    common = sorted(set(pa) & set(pb))
    print(f"\n--- {task} ---")
    print(f"  共通 seed: {common}")
    if not common:
        print("  対応する seed が無い → paired Δ は UNKNOWN")
        continue
    diffs = [pb[s] - pa[s] for s in common]
    for s in common:
        print(f"    seed {s:>4s}: 無={pa[s]:.6f} 有={pb[s]:.6f} Δ={pb[s] - pa[s]:+.6f}")
    mean_d = statistics.fmean(diffs)
    pstd_d = statistics.pstdev(diffs) if len(diffs) > 1 else float("nan")
    sstd_d = statistics.stdev(diffs) if len(diffs) > 1 else float("nan")
    base_pstd = statistics.pstdev(list(pa.values())) if len(pa) > 1 else float("nan")
    print(f"  paired Δ 平均 = {mean_d:+.6f}")
    print(f"  paired Δ の pstd = {pstd_d:.6f} / sstd = {sstd_d:.6f}")
    print(f"  基準点の seed 間 pstd = {base_pstd:.6f}")
    print(f"  全 seed 同符号 = {all(d > 0 for d in diffs) or all(d < 0 for d in diffs)}")
    for name, sig in (("paired Δ pstd", pstd_d), ("基準点 seed 間 pstd", base_pstd)):
        if sig and sig == sig and sig > 0:
            print(f"  abs(Δ)/σ [{name}] = {abs(mean_d) / sig:.3f}")

print("\n" + "=" * 72)
print("3. 評価レシピの分布（検出側が 2 系統に分かれる事実の確認）")
print("=" * 72)

det_steps = {"s0", "s0_frozen"}
c = collections.Counter(
    (r["step"], r.get("eval_recipe_id", "")) for r in rows if r["step"] in det_steps
)
print("  検出系 (step in s0/s0_frozen) の eval_recipe_id:")
for (st, rec), n in sorted(c.items(), key=lambda x: (-x[1], x[0])):
    print(f"    step={st:10s} recipe={rec or '（空）':14s} runs={n}")

cp = collections.Counter(
    r.get("eval_recipe_id", "") for r in rows if r["step"].startswith("s4_phase")
)
print("\n  工程系 (step が s4_phase で始まる) の eval_recipe_id:")
for rec, n in cp.most_common():
    print(f"    recipe={rec or '（空）':14s} runs={n}")

print("\n" + "=" * 72)
print("4. frozen_source_tag の分布（凍結源が揃うかの判定材料）")
print("=" * 72)
cf = collections.Counter(r.get("frozen_source_tag", "") for r in rows)
for tag, n in cf.most_common(12):
    print(f"  {tag or '（空）':44s} runs={n}")

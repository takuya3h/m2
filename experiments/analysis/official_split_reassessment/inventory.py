"""公式の分割で測られた結果を棚卸しし、効果量と揺らぎの出所を表にする。

契約: T-2026-08-26-official-split-reassessment
**判定は行わない。材料を出す。**
"""
import csv, re
from pathlib import Path

REPO = Path("/home/ubuntu/slocal2/m2")
ex = list(csv.DictReader((REPO/"runindex/experiments.csv").open(newline="", encoding="utf-8")))
ix = list(csv.DictReader((REPO/"runindex/index.csv").open(newline="", encoding="utf-8")))

# 六つの結論。**複数の綴りで探す。** 一致零件を綴りの誤りと取り違えないため。
CONCL = [
    ("1 術具の情報を工程認識へ渡す",   r"det2phase_toolpresence|tool2phase|toolpresence"),
    ("2 全体平均の特徴を足す害(GAP)",  r"\bgap\b|_gap|gap_|globalavg|global_avg|pooling"),
    ("3 正しい術具存在の追加の利得",   r"oracletool|oracle_tool|oracle_phase|oracletoolpresence"),
    ("4 入力側の雑音除去",             r"denoise|denoising|deflicker|smooth"),
    ("5 弁別しない術具を落とす",       r"prune|drop|top3|ubiquit|entropy"),
    ("6 工程の情報を術具検出へ渡す",   r"phase2det|clsbias|p2d|phase_to_det"),
]

print("=" * 100)
print("Phase A — 公式の分割で測られた結果の棚卸し")
print("=" * 100)
print(f"\n{'結論':32s} {'experiments.csv':>16s} {'うち split=val':>15s} {'うち split=test':>16s} {'index.csv':>11s}")
print("-" * 100)
inv = {}
for name, pat in CONCL:
    hit = [r for r in ex if re.search(pat, r["experiment_id"], re.I)]
    val = [r for r in hit if r["split"] == "val"]
    tst = [r for r in hit if r["split"] == "test"]
    ihit = [r for r in ix if re.search(pat, r.get("experiment_id","") or "", re.I)]
    inv[name] = val
    print(f"{name:32s} {len(hit):>16d} {len(val):>15d} {len(tst):>16d} {len(ihit):>11d}")

print("\n陰性対照（存在しない語で同じ探索）:")
for pat in (r"zzznosuchtoken", r"qqq_not_a_method"):
    print(f"  {pat:24s}: experiments.csv {sum(1 for r in ex if re.search(pat, r['experiment_id'], re.I)):d} 件"
          f" / index.csv {sum(1 for r in ix if re.search(pat, r.get('experiment_id','') or '', re.I)):d} 件")

print("\n" + "=" * 100)
print("Phase B — 効果量と種の数と揺らぎの出所")
print("=" * 100)
print("**推定で埋めない。記録が無い欄は (記録なし) と書く。**\n")

METRICS = [("accuracy", "分類の正しさ"), ("macro_f1", "工程ごとの成績の平均"), ("edit_score", "分節")]

def cell(r, key):
    v = r.get(key, "")
    return v if v not in ("", None) else None

for name, _ in CONCL:
    rows = inv[name]
    print(f"--- {name}")
    if not rows:
        print("    公式の分割で測られた行が **0 件**。効果量を読めない。\n")
        continue
    for r in rows:
        eid = r["experiment_id"]
        print(f"    {eid}")
        print(f"      測られた分割 = {r['split'] or '(記録なし)'}   n_runs={r['n_runs']}  n_seeds={r['n_seeds']}  seeds={r['seeds'] or '(記録なし)'}")
        print(f"      揺らぎの出所: sigma_source={r['sigma_source'] or '(記録なし)'}  delta_sigma_source={r['delta_sigma_source'] or '(記録なし)'}")
        print(f"      対の由来    : pairing_provenance={r['pairing_provenance'] or '(記録なし)'}  delta_method={r['delta_method'] or '(記録なし)'}")
        print(f"      判定        : verdict_10_1={r['verdict_10_1'] or '(記録なし)'}  metric={r['verdict_metric'] or '(記録なし)'}")
        for m, jp in METRICS:
            d   = cell(r, f"delta_{m}")
            sd  = cell(r, f"delta_sstd_{m}")
            rat = cell(r, f"abs_delta_over_sigma_{m}")
            sgn = cell(r, f"delta_same_sign_{m}")
            ns  = cell(r, f"delta_n_seeds_{m}")
            if d is None:
                print(f"        {jp:20s} (記録なし)")
            else:
                f = lambda x: f"{float(x):+.5f}" if x is not None else "(記録なし)"
                g = lambda x: f"{float(x):.3f}"  if x is not None else "(記録なし)"
                print(f"        {jp:20s} Δ={f(d)}  sstd={g(sd)}  |Δ|/σ={g(rat)}  同符号={sgn or '(記録なし)'}  種={ns or '(記録なし)'}")
        print()

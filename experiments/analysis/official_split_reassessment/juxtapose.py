"""Phase D — 二つの枠組みの並置。**どちらが正しいとは書かない。**"""
import csv, re, statistics
from pathlib import Path
ex = list(csv.DictReader(Path("/home/ubuntu/slocal2/m2/runindex/experiments.csv").open(newline="", encoding="utf-8")))
def g(r,k):
    v=r.get(k,""); return float(v) if v not in ("",None) else None

PRUNE = r"prune|drop|top3|ubiquit|entropy"
rows = [r for r in ex if r["split"]=="val" and re.search(PRUNE, r["experiment_id"], re.I)]
print("="*100)
print("Phase D — 撤回の対象（工程を弁別しない術具を落とす）の、公式の分割での結果")
print("="*100)
print(f"\n公式の分割（検証側 val）で測られた行: **{len(rows)} 件**。評価側 test: **0 件**。\n")
hdr=f"{'experiment_id':56s} {'Δ分類':>10s} {'|Δ|/σ':>7s} {'符号':>5s} | {'Δ工程平均':>10s} {'|Δ|/σ':>7s} {'符号':>5s} | {'判定':>16s}"
print(hdr); print("-"*len(hdr))
acc, mf1 = [], []
for r in sorted(rows, key=lambda x: x["experiment_id"]):
    a, am, asg = g(r,"delta_accuracy"), g(r,"abs_delta_over_sigma_accuracy"), r.get("delta_same_sign_accuracy","")
    m, mm, msg = g(r,"delta_macro_f1"), g(r,"abs_delta_over_sigma_macro_f1"), r.get("delta_same_sign_macro_f1","")
    acc.append(a); mf1.append(m)
    name = r["experiment_id"].split("/")[-1].split("@")[0]
    print(f"{name:56s} {a:>+10.5f} {am:>7.2f} {asg[:5]:>5s} | {m:>+10.5f} {mm:>7.2f} {msg[:5]:>5s} | {r['verdict_10_1']:>16s}")
print()
print(f"分類の正しさ Δ: 最小 {min(acc):+.5f} / 中央 {statistics.median(acc):+.5f} / 最大 {max(acc):+.5f}  正の数 {sum(1 for x in acc if x>0)}/{len(acc)}")
print(f"工程平均     Δ: 最小 {min(mf1):+.5f} / 中央 {statistics.median(mf1):+.5f} / 最大 {max(mf1):+.5f}  正の数 {sum(1 for x in mf1 if x>0)}/{len(mf1)}")
print()
print("【起票者の申し送り 3 との突き合わせ】")
print("  申し送り: 『公式の分割では分類の正しさは動かず、工程ごとの成績を平均した指標が改善していた』")
print(f"  実測    : 分類の正しさは **動いている**。11 件中 {sum(1 for x in acc if x>0)} 件が正、|Δ|/σ は "
      f"{min(g(r,'abs_delta_over_sigma_accuracy') for r in rows):.2f}〜{max(g(r,'abs_delta_over_sigma_accuracy') for r in rows):.2f}。")
print(f"            工程平均も **動いている**（{sum(1 for x in mf1 if x>0)}/{len(mf1)} 件が正）。")
print("  → 『分類は動かず工程平均だけ改善』という形にはなっていない。**申し送りは実測と食い違う。**")

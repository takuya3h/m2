"""選択性が崩れる領域を、判定を行わずに特定する材料を出す。

三つを並べる。**しきい値で「有意」と言わない。** 数と散らばりをそのまま出す。

  1 分母（Δacc）が零に近い領域 — 比が振れているのか本当に大きいのかを区別する材料
  2 比が 1 に近づく領域
  3 二つの形が区別できなくなる領域 — 同じ p での sel(L=1)/sel(L=最長)
"""
import csv, math, sys
from pathlib import Path

rows = list(csv.DictReader(Path(sys.argv[1]).open(newline="", encoding="utf-8")))
for r in rows:
    for k in r:
        if k != "sel_per_seed":
            try: r[k] = float(r[k])
            except ValueError: pass
    r["sel_per_seed"] = [float(x) for x in r["sel_per_seed"].split("|")]

PS = sorted({r["p"] for r in rows}); LS = sorted({int(r["L"]) for r in rows})
by = {(r["p"], int(r["L"])): r for r in rows}

print("=== 1. 分母（Δacc）の確からしさと、選択性の種ごとの振れ ===")
print(f"{'p':>5} {'L':>4} | {'Δacc':>9} {'|m|/SE':>7} {'neg':>6} | {'選択性':>7} {'幅(最小〜最大)':>18} {'幅/平均':>8}")
for p in PS:
    for L in LS:
        r = by[(p, L)]
        span = r["sel_max"] - r["sel_min"]
        rel = span / r["selectivity"] if r["selectivity"] else float("nan")
        flag = " ←分母が小さい" if r["eff_acc"] < 3 else ""
        print(f"{p:>5} {L:>4} | {r['d_acc']:>+9.4f} {r['eff_acc']:>7.2f} {int(r['neg_acc']):>3}/15 | "
              f"{r['selectivity']:>7.2f} {r['sel_min']:>8.2f}〜{r['sel_max']:<8.2f} {rel:>8.2f}{flag}")
print()

print("=== 2. 選択性が 1 を下回る点 ===")
below = [(r["p"], int(r["L"]), r["selectivity"]) for r in rows if r["selectivity"] < 1.0]
if below:
    for p, L, s in sorted(below): print(f"  p={p} L={L}: 選択性={s:.2f}")
else:
    print("  無し")
print(f"  1 を下回る点: {len(below)} / {len(rows)}")
print()

print("=== 3. 二つの形の隔たり — 同じ p での sel(L=1) / sel(L=64) ===")
print(f"{'p':>6} | {'sel(L=1)':>9} {'sel(L=64)':>10} {'隔たり':>8} | {'実測誤り(L=1)':>13} {'実測誤り(L=64)':>14}")
for p in PS:
    a, b = by[(p, min(LS))], by[(p, max(LS))]
    print(f"{p:>6} | {a['selectivity']:>9.2f} {b['selectivity']:>10.2f} {a['selectivity']/b['selectivity']:>8.2f} | "
          f"{a['err_rate_actual']:>13.5f} {b['err_rate_actual']:>14.5f}")
print()

print("=== 4. 名目の p と実測の誤り率のずれ（軸の意味に効く）===")
print(f"{'p':>6} | " + " ".join(f"L={L:<3}" for L in LS))
for p in PS:
    print(f"{p:>6} | " + " ".join(f"{by[(p,L)]['err_rate_actual']/p:5.2f}" for L in LS))
print("  （値は 実測誤り率 / 名目 p。1.00 なら意図どおり）")

"""二つの腕を突き合わせる。**判定は行わない。**

既存の記録（§3.10(c)）は「学習をクリーンにして評価側だけ汚すと選択性が
3.9 倍 → 7.0 倍に鋭くなる」と述べる。**これは p=0.05 の一点での観測である。**
掃引の全域で同じ向きかを見る。
"""
import csv, sys
from pathlib import Path

def load(p):
    rows = list(csv.DictReader(Path(p).open(newline="", encoding="utf-8")))
    out = {}
    for r in rows:
        out[(float(r["p"]), int(float(r["L"])))] = {
            k: (float(v) if k != "sel_per_seed" else v) for k, v in r.items()}
    return out

D = Path("/home/ubuntu/slocal2/m2/experiments/analysis/error_shape_selectivity")
TO = load(D / "summary_testonly.csv")
TT = load(D / "summary_traintest.csv")
PS = sorted({k[0] for k in TO}); LS = sorted({k[1] for k in TO})
L0, L32, L64 = 1, 32, 64

print("=== 選択性の表（分類 1 点あたりの分節損失）===")
for name, A in (("評価側だけを汚す", TO), ("学習側も汚す", TT)):
    print(f"\n--- {name}")
    print("     p |" + "".join(f"  L={L:<4}" for L in LS))
    for p in PS:
        print(f"{p:>6} |" + "".join(f" {A[(p,L)]['selectivity']:>6.2f}" for L in LS))

print("\n\n=== 種ごとの散らばり（標本標準偏差）===")
for name, A in (("評価側だけを汚す", TO), ("学習側も汚す", TT)):
    print(f"\n--- {name}")
    print("     p |" + "".join(f"  L={L:<4}" for L in LS))
    for p in PS:
        print(f"{p:>6} |" + "".join(f" {A[(p,L)]['sel_sstd']:>6.2f}" for L in LS))

print("\n\n=== 既存の一点（記録）が掃引の中でどこに位置するか ===")
print(f"{'記録の条件':<28} {'記録値':>8} {'本掃引の対応点':>16} {'実測':>8}")
rows = [
    ("§3.10 学習側も iid p=0.05",      6.1, f"traintest p=0.05 L=1",  TT[(0.05,1)]["selectivity"]),
    ("§3.10 学習側も burst L=32 p=.05", 1.6, f"traintest p=0.05 L=32", TT[(0.05,32)]["selectivity"]),
    ("§3.10(c) 評価側のみ iid p=0.05", 10.5, f"testonly p=0.05 L=1",   TO[(0.05,1)]["selectivity"]),
    ("§3.10(c) 評価側のみ burst L=32",  1.5, f"testonly p=0.05 L=32",  TO[(0.05,32)]["selectivity"]),
]
for a,b,c,d in rows:
    print(f"{a:<28} {b:>8.1f} {c:>26} {d:>8.2f}")

print("\n\n=== 二つの形の隔たり sel(L=1)/sel(L=32) を腕ごとに ===")
print("  （§3.10 が『3.9 倍』『7.0 倍』と述べた量。p=0.05 の一点でしか測られていない）")
print(f"{'p':>6} | {'評価側のみ':>10} {'学習側も':>10} | {'どちらが鋭いか':>16}")
for p in PS:
    a = TO[(p,L0)]["selectivity"] / TO[(p,L32)]["selectivity"]
    b = TT[(p,L0)]["selectivity"] / TT[(p,L32)]["selectivity"]
    who = "評価側のみ" if a > b else "学習側も"
    print(f"{p:>6} | {a:>10.2f} {b:>10.2f} | {who:>16}")

print("\n\n=== 効果量と符号の個数（判定とは別に記録する）===")
for name, A in (("評価側だけを汚す", TO), ("学習側も汚す", TT)):
    print(f"\n--- {name}   分母 Δacc の効果量 |m|/SE  ／  符号が負の動画数")
    print("     p |" + "".join(f"      L={L:<4}" for L in LS))
    for p in PS:
        print(f"{p:>6} |" + "".join(f" {A[(p,L)]['eff_acc']:>5.2f} {int(A[(p,L)]['neg_acc']):>2}/15" for L in LS))
    print(f"\n--- {name}   分子 Δedit の効果量 |m|/SE  ／  符号が負の動画数")
    print("     p |" + "".join(f"      L={L:<4}" for L in LS))
    for p in PS:
        print(f"{p:>6} |" + "".join(f" {A[(p,L)]['eff_edit']:>5.2f} {int(A[(p,L)]['neg_edit']):>2}/15" for L in LS))

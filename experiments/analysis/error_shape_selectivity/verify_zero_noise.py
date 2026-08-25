"""陰性対照の強化。p=0 を **add_noise の内側を通して** 与えたとき何も変わらないか。

原典の build は `add_noise(...) if p>0 else X` と分岐するため、p=0 では
誤りを与える手続きを一度も呼ばない。**それでは add_noise の欠陥を検出できない。**
ここでは add_noise を直接 p=0 で呼ぶ。陽性方向も測る。
"""
import re, numpy as np
from pathlib import Path
src = Path("/home/ubuntu/slocal2/m2/docs/analysis_scripts/proxy_lovo_noise_structure.py").read_text(encoding="utf-8")
ns = {}
exec(re.search(r"^def add_noise\(.*?\n(?=\ndef )", src, re.S | re.M).group(0), ns)
add_noise = ns["add_noise"]

T, C = 6000, 15
print(f"{'mode':>6} {'L':>4} {'seed':>5} | {'異なる位置数':>12} {'実測誤り率':>11}")
allzero = True
for mode, L in (("iid", 1), ("burst", 1), ("burst", 8), ("burst", 32)):
    for seed in (7, 17, 27):
        X = (np.random.default_rng(seed * 13).random((T, C)) < 0.3).astype(np.int64)
        Y = add_noise(X, 0.0, mode, L, np.random.default_rng(seed))
        d = int((X != Y).sum()); allzero &= (d == 0)
        print(f"{mode:>6} {L:>4} {seed:>5} | {d:>12} {d/(T*C):>11.6f}")
print("\n誤りの経路を通しても全条件で零:", allzero)
X = (np.random.default_rng(7).random((T, C)) < 0.3).astype(np.int64)
Y = add_noise(X, 0.001, "burst", 1, np.random.default_rng(7))
print("陽性方向 p=0.001: 異なる位置数 =", int((X != Y).sum()), " 実測誤り率 =", f"{int((X!=Y).sum())/(T*C):.6f}")

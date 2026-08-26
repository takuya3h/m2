"""軸二の両端が同じ仕組みで扱えるかを確かめる。

問い: 孤立した反転（mode="iid"）は、持続する誤り（mode="burst"）の L=1 の場合か。
扱えるなら二つの形は一つの軸の両端であり、L だけを動かせばよい。

**両方向を測る。** L=1 で一致することだけでは「常に一致する」壊れ方と区別できないため、
L=2 では一致しないことも示す。
"""
import re, numpy as np
from pathlib import Path
src = Path("/home/ubuntu/slocal2/m2/docs/analysis_scripts/proxy_lovo_noise_structure.py").read_text(encoding="utf-8")
ns = {}
exec(re.search(r"^def add_noise\(.*?\n(?=\ndef )", src, re.S | re.M).group(0), ns)
add_noise = ns["add_noise"]

T, C = 5000, 15
print("p      seed  iid==burst(L=1)  異なる位置数")
rows = []
for p in (0.01, 0.05, 0.10, 0.20, 0.40):
    for seed in (7, 17, 27):
        X = (np.random.default_rng(seed).random((T, C)) < 0.3).astype(np.int64)
        A = add_noise(X, p, "iid",   1, np.random.default_rng(seed))
        B = add_noise(X, p, "burst", 1, np.random.default_rng(seed))
        eq = bool(np.array_equal(A, B)); d = int((A != B).sum())
        rows.append(eq)
        print(f"{p:<6} {seed:<5} {str(eq):15s} {d}")
print("\n全条件で一致:", all(rows))
X = (np.random.default_rng(7).random((T, C)) < 0.3).astype(np.int64)
A = add_noise(X, 0.05, "iid", 1, np.random.default_rng(7))
B2 = add_noise(X, 0.05, "burst", 2, np.random.default_rng(7))
print("陰性対照 iid vs burst(L=2): 一致 =", np.array_equal(A, B2), " 異なる位置数 =", int((A != B2).sum()))

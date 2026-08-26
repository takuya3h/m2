"""誤りの量の求め方が「集合の差」であることを、明示の集合演算と突き合わせて確かめる。

完了判定 c は「部分一致で数えた場合と値が異なるか」を求める。
本検査は三つを並べる。

  A 明示の集合の対称差   len(S(X) ^ S(Y))           ← 正しいもの（遅い）
  B 掃引が使う数え方     (X != Y).sum()             ← 速いが同値であるべき
  C 件数の差             abs(|S(X)| - |S(Y)|)       ← **誤った数え方**

A == B かつ A != C であることを示す。**片方だけでは検査にならない。**
"""
import re, numpy as np
from pathlib import Path

src = Path("/home/ubuntu/slocal2/m2/docs/analysis_scripts/proxy_lovo_noise_structure.py").read_text(encoding="utf-8")
ns = {}
exec(re.search(r"^def add_noise\(.*?\n(?=\ndef )", src, re.S | re.M).group(0), ns)
add_noise = ns["add_noise"]

T, C = 4000, 15
print(f"{'p':>6} {'L':>4} {'seed':>5} | {'A 集合の対称差':>14} {'B (X!=Y).sum':>14} {'C 件数の差':>12} | A==B  A!=C")
ok_ab = ok_ac = True
for p in (0.02, 0.05, 0.20):
    for L in (1, 8, 32):
        for seed in (7, 17):
            X = (np.random.default_rng(seed * 31).random((T, C)) < 0.3).astype(np.int64)
            Y = add_noise(X, p, "burst", L, np.random.default_rng(seed))
            sx = set(map(tuple, np.argwhere(X == 1)))
            sy = set(map(tuple, np.argwhere(Y == 1)))
            A = len(sx ^ sy)
            B = int((X != Y).sum())
            Cc = abs(len(sx) - len(sy))
            ok_ab &= (A == B); ok_ac &= (A != Cc)
            print(f"{p:>6} {L:>4} {seed:>5} | {A:>14} {B:>14} {Cc:>12} | {str(A==B):5s} {str(A!=Cc)}")
print()
print("A == B が全条件で成立:", ok_ab, " ← 掃引の数え方は集合の対称差と同値")
print("A != C が全条件で成立:", ok_ac, " ← 件数の差では別の値になる（誤った数え方と区別できている）")

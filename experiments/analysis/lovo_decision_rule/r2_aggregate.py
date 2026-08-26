"""R2 の集計。学習側を実際に取り替えた反復から、fold 間の相関を実測して分散へ入れる。

**なぜ 15 個の差だけでは足りないのか。**
d_i = mu + b + e_i と書ける。b は 14 動画の学習側が共有されることから来る成分で、
すべての fold に同じ値が乗る。e_i は fold 固有の成分である。
1 回の一つ抜き検証しか無いと b は mu と見分けがつかない。**学習側が実際に違う状態を
複数作って初めて b の散らばりが測れる。**

反復 r ごとに 12 動画を選び直して一つ抜き検証をやり直す。
  sigma^2  = 反復内の対の差の標本分散の平均        -> e の分散
  V_between = 反復間の平均値の標本分散              -> Var(b) + sigma^2/m
  Var(b)   = max(0, V_between - sigma^2/m)
  SE       = sqrt(Var(b) + sigma^2/15)
区間は mean +- 1.96*SE。**零を含まなければ検出**（CRITERIA.md 第 3 節）。
"""
import json, math, statistics, sys
from pathlib import Path

Z = 1.959963984540054  # 両側 5%


def series(repfile, arm_a, arm_b, key):
    """反復ごとの (平均, 標本分散, fold 数) を返す。"""
    data = json.load(open(repfile, encoding="utf-8"))
    out = []
    for rep in data["replicates"]:
        F = rep.get("folds")
        if not F or arm_a not in F or arm_b not in F:
            continue
        vids = sorted(set(F[arm_a]) & set(F[arm_b]))
        try:
            d = [F[arm_a][v][key] - F[arm_b][v][key] for v in vids]
        except KeyError:
            continue
        if len(d) < 2:
            continue
        out.append((statistics.mean(d), statistics.variance(d), len(d)))
    return out


def aggregate(reps, mean_full, n_full=15):
    """反復の列から SE と区間を作る。反復が 2 未満なら測れない（UNKNOWN）。"""
    if len(reps) < 2:
        return {"detect": False, "se": None, "lo": None, "hi": None,
                "n_reps": len(reps), "rho": None,
                "note": "反復が 2 未満で分散が定義されない（UNKNOWN）"}
    means = [r[0] for r in reps]
    s2 = statistics.mean(r[1] for r in reps)
    m = statistics.mean(r[2] for r in reps)
    v_between = statistics.variance(means)
    # **有限母集団の補正。** 部分集合は 15 本から重複なく m 本を選ぶ。
    # 反復どうしは動画を大きく共有するため、反復間の平均の散らばりは
    # 独立に選んだ場合の s2/m より **小さく出る**。正しい期待値は
    #   (s2/m) * (N-m)/(N-1)
    # である。補正を入れずに s2/m を引くと共有成分がほぼ必ず負になり、
    # max(0, .) で 0 へ潰れて「相関は無い」という誤った像を与える。
    fpc = (n_full - m) / (n_full - 1) if n_full > 1 else 1.0
    v_sampling = (s2 / m) * fpc
    v_b = max(0.0, v_between - v_sampling)
    se = math.sqrt(v_b + s2 / n_full)
    lo, hi = mean_full - Z * se, mean_full + Z * se
    rho = v_b / (v_b + s2) if (v_b + s2) > 0 else 0.0
    return {"detect": not (lo <= 0.0 <= hi), "se": se, "lo": lo, "hi": hi,
            "n_reps": len(reps), "rho": rho, "sigma2": s2, "v_between": v_between,
            "v_sampling": v_sampling, "v_shared": v_b, "m": m, "fpc": fpc,
            "note": "学習側を取り替えた反復から共有成分を実測。有限母集団の補正を入れた"}

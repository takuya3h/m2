"""判定則。fold ごとの対の差 d（長さ n）だけを入力に取る。

**現行の則 R0 は独立を前提にしている。** 一つ抜き検証の任意の 2 fold は
学習側の 14 動画のうち 13 動画を共有するため、fold の間には強い正の相関がある。
正の相関があるとき、独立を前提にした標準誤差は真の値より小さく出て、判定は甘い方向へ偏る。

閾は CRITERIA.md 第 3 節で結果を見る前に固定した。ここでは動かさない。
"""
import itertools, math, statistics

N_TEST_VIDEOS = 1    # 一つ抜き検証: 各 fold の評価側は 1 動画
N_TRAIN_VIDEOS = 14  # 同 学習側は 14 動画

T_THRESHOLD = 2.0    # t 型の閾（現行の則と揃える）
ALPHA = 0.05         # 区間型の水準（両側）


def effect(d):
    """判定とは別に必ず残す量。則に依存しない。"""
    n = len(d)
    return {
        "n": n,
        "mean": statistics.mean(d),
        "pstd": statistics.pstdev(d),
        "sstd": statistics.stdev(d) if n > 1 else float("nan"),
        "n_pos": sum(1 for x in d if x > 0),
        "n_neg": sum(1 for x in d if x < 0),
        "n_zero": sum(1 for x in d if x == 0),
    }


def r0_current(d):
    """現行の則。SE = pstdev(d)/sqrt(n)。**fold の独立を前提にしている。**"""
    n = len(d); m = statistics.mean(d); se = statistics.pstdev(d) / math.sqrt(n)
    t = abs(m) / se if se else 0.0
    return {"stat": t, "detect": t >= T_THRESHOLD, "se": se,
            "note": "独立前提。相関があると SE が過小になり判定が甘くなる"}


def r1_nadeau_bengio(d):
    """R1 Nadeau-Bengio 補正 t。学習側の重なりから相関を導いて分散へ繰り込む。

    Var(mean) = s^2 * (1/n + n_test/n_train)。第 2 項が fold 間の相関の寄与である。
    n_test/n_train は「各 fold の評価側 / 学習側」の比で、設計から決まる。
    **標本分散（ddof=1）を使う。** 補正の導出が標本分散を前提にしている。
    """
    n = len(d); m = statistics.mean(d)
    if n < 2:
        return {"stat": float("nan"), "detect": False, "se": float("nan"),
                "note": "n<2 で定義されない"}
    s2 = statistics.variance(d)
    var = s2 * (1.0 / n + N_TEST_VIDEOS / N_TRAIN_VIDEOS)
    se = math.sqrt(var)
    t = abs(m) / se if se else 0.0
    return {"stat": t, "detect": t >= T_THRESHOLD, "se": se,
            "note": f"相関の寄与 = n_test/n_train = {N_TEST_VIDEOS}/{N_TRAIN_VIDEOS}"}


def r3_signflip_exact(d):
    """R3 符号反転の網羅的並べ替え検定。2^n 通りをすべて数える（乱数を使わない）。

    **この則は CRITERIA.md の S3 を満たさない。** 符号反転が妥当なのは d_i が
    交換可能なときであり、正の相関があるときは現行の則と同じ向きに甘く偏る。
    候補からは外すが、比較のため値は残す。
    """
    n = len(d)
    if n > 22:
        return {"stat": float("nan"), "detect": False, "p": float("nan"),
                "note": "n が大きく網羅できない"}
    m = abs(statistics.mean(d))
    total = 0; hit = 0
    for signs in itertools.product((1, -1), repeat=n):
        total += 1
        if abs(sum(s * x for s, x in zip(signs, d))) / n >= m - 1e-15:
            hit += 1
    p = hit / total
    return {"stat": p, "detect": p < ALPHA, "p": p, "n_perm": total,
            "note": "S3 を満たさない（交換可能性を前提にする）。候補外・比較用"}

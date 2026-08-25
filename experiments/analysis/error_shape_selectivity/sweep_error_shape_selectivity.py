"""誤りの形による選択性を、誤り率 p と持続の長さ L の二軸で掃引する。

契約: T-2026-08-26-error-shape-selectivity

既存の介入実験（docs/analysis_scripts/proxy_lovo_noise_structure.py と
proxy_lovo_noise_testonly.py）と**同じ手続き**を使い、条件を格子へ広げる。
再現性のため、ノイズの生成・学習・評価の流れは原典から変えていない。

軸二について: 原典の add_noise は mode="iid" と mode="burst" を持つが、
**burst の L=1 は iid とビット単位で同一である**（実測。乱数の消費順序も同じ）。
したがって二つの形は一つの軸の両端であり、L だけを動かせばよい。

記憶について: 条件ごとにデータを作って捨てる。全条件を先に作ると格子の大きさに
比例して記憶を使う（原典は 5 条件しか無いので先に作っている）。

置き場所について: 本ファイルは**同期の外**で走らせる。`.stignore:52` の
`!experiments/**/*.py` により experiments 配下の .py は同期対象であり、
実行中に他ホストの状態で削除されうる（2026-08-25 21:59:55 に実測）。
出力の .csv は同期対象外のため repo 配下へ直接書く。

出力: rows.csv（格子の各点 × 種 × 動画の生の値）。集計は別段で行う。
"""
import csv, os, time
import numpy as np
from pathlib import Path

REPO = Path("/home/ubuntu/slocal2/m2")
os.chdir(REPO)

# 原典が読み込んでいる土台をそのまま使う（load_sig / clips / fit_phase_hmm /
# phase_filter / PhaseEvaluator / NC / CLASS_NAMES）。
_src = open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(_src)

from sklearn.linear_model import LogisticRegression          # noqa: E402
from sklearn.preprocessing import StandardScaler             # noqa: E402


def add_noise(X, p, mode, L, rng):
    """原典 docs/analysis_scripts/proxy_lovo_noise_structure.py:8-19 の原文。"""
    Y = X.copy(); T = len(X)
    for c in range(15):
        if mode == "iid":
            m = rng.random(T) < p; Y[m, c] = 1 - Y[m, c]
        elif mode == "burst":
            t = 0
            while t < T:
                if rng.random() < p / L:
                    e = min(T, t + L); Y[t:e, c] = 1 - Y[t:e, c]; t = e
                else: t += 1
    return Y


def build(split, p, mode, L, seed):
    """原典 :21-26 の原文（乱数の種の作り方も含めて変えていない）。"""
    sig = load_sig(split, "oracle")
    rng = np.random.default_rng(seed * 997 + {"train": 0, "val": 1, "test": 2}[split])
    out = []
    for cid, frames, lab in clips(split):
        X = np.stack([sig[f] for f in frames])
        out.append((cid, add_noise(X, p, mode, L, rng) if p > 0 else X, lab))
    return out


def build_all(p, mode, L, seed):
    return sum([build(sp, p, mode, L, seed) for sp in ["train", "val", "test"]], [])


def err_rate_setdiff(clean, noisy):
    """誤りの量を**集合の差**で求める。件数の差では数えない。

    位置集合 S(A) = {(clip, t, c) : A[t,c]==1} の**対称差**の大きさ / 全位置数。
    値が 0/1 のとき、位置 (t,c) が対称差に入ることと X[t,c] != Y[t,c] は同値である。
    集合を実体化せずに数えるが、**求めているものは対称差そのもの**である。
    同値であることは verify_err_rate.py で明示の集合演算と突き合わせて確かめてある。

    件数の差（|S(X)| - |S(Y)|）では数えない。**件数が合っていることは、
    入れ替わりが起きていないことを意味しない。**
    """
    diff = 0; total = 0
    by_cid = {cid: X for cid, X, _ in noisy}
    for cid, X, _ in clean:
        Y = by_cid[cid]
        diff += int((X != Y).sum()); total += X.size
    return diff / total


def mean_run_len(clean, noisy):
    """反転が続いた区間の長さの平均。持続の長さが効いているかの実測。"""
    n_runs = 0; n_true = 0
    by_cid = {cid: X for cid, X, _ in noisy}
    for cid, X, _ in clean:
        D = (X != by_cid[cid])
        pad = np.zeros((1, D.shape[1]), dtype=bool)
        rises = np.logical_and(D, ~np.vstack([pad, D[:-1]]))
        n_runs += int(rises.sum()); n_true += int(D.sum())
    return (n_true / n_runs) if n_runs else 0.0


def evaluate(train_clips, test_clips):
    Xtr = np.concatenate([x for _, x, _ in train_clips])
    ytr = np.concatenate([l for _, _, l in train_clips])
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=1000).fit(sc.transform(Xtr), ytr)
    Aph, prior = fit_phase_hmm(train_clips); cls = list(clf.classes_)
    ev = PhaseEvaluator(num_classes=NC, class_names=CLASS_NAMES)
    for cid, X, lab in test_clips:
        pr = clf.predict_proba(sc.transform(X))
        full = np.zeros((len(X), NC)); full[:, cls] = pr
        ev.update(phase_filter(full, Aph, prior).argmax(1), lab, cid)
    return ev.compute()


def fit_clean(train_clips):
    """評価側だけを汚す腕のために、クリーンな学習を一度だけ行う。"""
    Xtr = np.concatenate([x for _, x, _ in train_clips])
    ytr = np.concatenate([l for _, _, l in train_clips])
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=1000).fit(sc.transform(Xtr), ytr)
    Aph, prior = fit_phase_hmm(train_clips)
    return sc, clf, Aph, prior, list(clf.classes_)


def eval_with(model, test_clips):
    sc, clf, Aph, prior, cls = model
    ev = PhaseEvaluator(num_classes=NC, class_names=CLASS_NAMES)
    for cid, X, lab in test_clips:
        pr = clf.predict_proba(sc.transform(X))
        full = np.zeros((len(X), NC)); full[:, cls] = pr
        ev.update(phase_filter(full, Aph, prior).argmax(1), lab, cid)
    return ev.compute()


KEYS = ["phase_accuracy", "phase_macro_f1", "phase_edit_score", "phase_seg_f1_50"]


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["traintest", "testonly"], required=True)
    ap.add_argument("--ps", default="0.01,0.02,0.05,0.10,0.20,0.40")
    ap.add_argument("--ls", default="1,2,4,8,16,32,64")
    ap.add_argument("--seeds", default="7,17,27")
    ap.add_argument("--out", required=True)
    ap.add_argument("--deadline-epoch", type=int, default=0,
                    help="この時刻を過ぎたら新しい点を始めない（0 で無効）")
    a = ap.parse_args()

    PS = [float(x) for x in a.ps.split(",")]
    LS = [int(x) for x in a.ls.split(",")]
    SEEDS = [int(x) for x in a.seeds.split(",")]

    clean = build_all(0, "none", 1, SEEDS[0])
    vids = sorted({c[0].split("_")[0] for c in clean})
    print(f"[setup] arm={a.arm} vids={len(vids)} ps={PS} ls={LS} seeds={SEEDS}", flush=True)

    out = open(a.out, "w", newline="", encoding="utf-8")
    w = csv.writer(out)
    w.writerow(["arm", "p", "L", "seed", "vid", "err_rate_actual", "mean_run_len"] + KEYS)

    if a.arm == "traintest":
        for vd in vids:
            tr = [c for c in clean if c[0].split("_")[0] != vd]
            te = [c for c in clean if c[0].split("_")[0] == vd]
            r = evaluate(tr, te)
            w.writerow(["traintest", 0.0, 0, SEEDS[0], vd, 0.0, 0.0] + [r[k] for k in KEYS])
        out.flush(); print("[clean] traintest done", flush=True)
        for p in PS:
            for L in LS:
                if a.deadline_epoch and time.time() > a.deadline_epoch:
                    print(f"[skip] p={p} L={L} 締切のため開始しない（空欄で残す）", flush=True)
                    continue
                for sd in SEEDS:
                    t0 = time.time()
                    noisy = build_all(p, "burst", L, sd)
                    er = err_rate_setdiff(clean, noisy); mr = mean_run_len(clean, noisy)
                    for vd in vids:
                        tr = [c for c in noisy if c[0].split("_")[0] != vd]
                        te = [c for c in noisy if c[0].split("_")[0] == vd]
                        r = evaluate(tr, te)
                        w.writerow(["traintest", p, L, sd, vd, er, mr] + [r[k] for k in KEYS])
                    out.flush(); del noisy
                    print(f"[traintest] p={p} L={L} seed={sd} err={er:.5f} runlen={mr:.2f} {time.time()-t0:.0f}s", flush=True)
    else:
        models = {}
        for vd in vids:
            tr = [c for c in clean if c[0].split("_")[0] != vd]
            models[vd] = fit_clean(tr)                      # 学習は常にクリーン
            te = [c for c in clean if c[0].split("_")[0] == vd]
            r = eval_with(models[vd], te)
            w.writerow(["testonly", 0.0, 0, SEEDS[0], vd, 0.0, 0.0] + [r[k] for k in KEYS])
        out.flush(); print("[clean] testonly done", flush=True)
        for p in PS:
            for L in LS:
                if a.deadline_epoch and time.time() > a.deadline_epoch:
                    print(f"[skip] p={p} L={L} 締切のため開始しない（空欄で残す）", flush=True)
                    continue
                for sd in SEEDS:
                    t0 = time.time()
                    noisy = build_all(p, "burst", L, sd)
                    er = err_rate_setdiff(clean, noisy); mr = mean_run_len(clean, noisy)
                    for vd in vids:
                        te = [c for c in noisy if c[0].split("_")[0] == vd]   # 評価側だけ汚す
                        r = eval_with(models[vd], te)
                        w.writerow(["testonly", p, L, sd, vd, er, mr] + [r[k] for k in KEYS])
                    out.flush(); del noisy
                    print(f"[testonly] p={p} L={L} seed={sd} err={er:.5f} runlen={mr:.2f} {time.time()-t0:.0f}s", flush=True)
    out.close()
    print("[done]", flush=True)


if __name__ == "__main__":
    main()

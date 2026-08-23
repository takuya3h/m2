"""因果 HMM forward filter による tool-presence デノイズの実効性検証（CPU・読み取り専用）。

train の GT presence から per-tool 2状態 HMM の遷移行列を推定し、
emission は train の予測 sigmoid を GT で条件づけたヒストグラムで推定する。
val に対し forward filtering（未来不使用＝因果）で posterior を得て品質を測る。
"""
import numpy as np, json, sys

DET = 'data/processed/b2a_detsignal/relation_detr_seed42/{}_toolpresence.npz'
ORA = 'data/processed/oracle_toolpresence/{}_oracletool.npz'
CLS = ["Bipolar Forceps","Electric Cautery","Forceps","Gauze","Hook","Mouth Gag","Needle Holders",
       "Raspatory","Retractor","Scalpel","Scissors","Skewer","Suction Cannula","Syringe","Tweezers"]

def load(split):
    d = np.load(DET.format(split), allow_pickle=True)
    o = np.load(ORA.format(split), allow_pickle=True)
    assert list(d['frame_ids']) == list(o['frame_ids'])
    return d['frame_ids'], d['signal'].astype(np.float64), o['signal'].astype(bool)

def video_of(fid):
    # '09_1_0213' -> '09_1'
    return "_".join(fid.split("_")[:2])

def segments(fids):
    """連続する同一動画の区間 [start, end) を返す（時系列の切れ目でフィルタをリセットする）。"""
    vids = np.array([video_of(f) for f in fids])
    idx = [0]
    for i in range(1, len(vids)):
        if vids[i] != vids[i-1]:
            idx.append(i)
    idx.append(len(vids))
    return [(idx[i], idx[i+1]) for i in range(len(idx)-1)]

NB = 20  # emission ヒストグラムのビン数
def fit(split='train'):
    fids, P, O = load(split)
    segs = segments(fids)
    A, E = [], []
    for c in range(15):
        y = O[:, c].astype(int)
        # 遷移行列（動画境界をまたがない）
        cnt = np.ones((2, 2)) * 1.0  # Laplace
        for s, e in segs:
            yy = y[s:e]
            for a, b in zip(yy[:-1], yy[1:]):
                cnt[a, b] += 1
        A.append(cnt / cnt.sum(1, keepdims=True))
        # emission: 予測スコアを NB ビンに離散化し GT で条件づけ
        b = np.clip((P[:, c] * NB).astype(int), 0, NB-1)
        em = np.ones((2, NB)) * 1.0
        for st in (0, 1):
            m = y == st
            if m.sum():
                em[st] += np.bincount(b[m], minlength=NB)
        E.append(em / em.sum(1, keepdims=True))
    return np.array(A), np.array(E)

def forward_filter(P, fids, A, E):
    """因果 forward filtering。出力は P(state=1 | 観測 t までの履歴)。"""
    out = np.zeros_like(P)
    segs = segments(fids)
    for c in range(15):
        b = np.clip((P[:, c] * NB).astype(int), 0, NB-1)
        for s, e in segs:
            pi = np.array([0.5, 0.5])
            for t in range(s, e):
                if t > s:
                    pi = pi @ A[c]
                lik = E[c][:, b[t]]
                pi = pi * lik
                pi = pi / max(pi.sum(), 1e-12)
                out[t, c] = pi[1]
    return out

def f1_of(y, s, th):
    p = s >= th
    tp = (p & y).sum(); fp = (p & ~y).sum(); fn = (~p & y).sum()
    return 2*tp / max(2*tp+fp+fn, 1)

def best_th(y, s):
    ths = np.round(np.linspace(0.01, 0.99, 99), 3)
    f = [f1_of(y, s, t) for t in ths]
    return ths[int(np.argmax(f))], max(f)

def report(name, fids, S, O, ths=None):
    valid = [c for c in range(15) if O[:, c].sum() > 0]
    segs = segments(fids)
    if ths is None:
        ths = np.array([best_th(O[:, c], S[:, c])[0] if c in valid else 0.5 for c in range(15)])
    B = S >= ths[None, :]
    f1s = [f1_of(O[:, c], S[:, c], ths[c]) for c in valid]
    err = np.mean([(B[:, c] != O[:, c]).mean() for c in valid])
    exact = (B[:, valid] == O[:, valid]).all(1).mean()
    ham = (B[:, valid] != O[:, valid]).sum(1).mean()
    def trans(X):
        tot = 0.0; n = 0
        for s, e in segs:
            tot += np.abs(np.diff(X[s:e, :][:, valid].astype(int), axis=0)).sum(); n += (e-s-1)
        return tot / n
    print(f"{name:26s} macroF1={np.mean(f1s):.4f} err={err*100:5.2f}% exact={exact*100:5.2f}% "
          f"ham={ham:.3f} trans={trans(B):.4f} (GT {trans(O):.4f})")
    return ths, np.array(f1s), valid

A, E = fit('train')
fids, P, O = load('val')
print("=== val (1515 frames, %d videos) ===" % len(set(video_of(f) for f in fids)))
ths_raw, f1_raw, valid = report("raw sigmoid", fids, P, O)
F = forward_filter(P, fids, A, E)
ths_hmm, f1_hmm, _ = report("causal HMM filter", fids, F, O)
print("\nper-class F1 (raw -> HMM):")
for i, c in enumerate(valid):
    print(f"  {CLS[c]:20s} {f1_raw[i]:.3f} -> {f1_hmm[i]:.3f}  ({(f1_hmm[i]-f1_raw[i])*100:+5.2f}pp)")
np.savez(sys.argv[1] if len(sys.argv) > 1 else '/tmp/hmm_val.npz', filtered=F, frame_ids=fids, thresholds=ths_hmm)

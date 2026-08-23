"""GPU 不要のプロキシ工程認識器で、presence デノイズの効果を先に測る。

構成: 多項ロジスティック回帰（per-frame, presence -> phase）+ 因果 phase HMM forward filter。
TeCNO ではないので絶対値は比較できないが、**同一のプロキシ上で信号だけを差し替える**ので
信号間の相対比較には使える。因果性は保つ（未来フレーム不使用）。
"""
import sys, json, numpy as np
sys.path.insert(0, "src")
from egosurgery.metrics.phase import PhaseEvaluator

NB = 20
FROZEN = "relation_detr_seed42"
MD = "data/processed/phase_manifest"
VOCAB = json.load(open(f"{MD}/phase_vocab.json"))
CLASS_NAMES = list(VOCAB.keys())
NC = len(CLASS_NAMES)

def load_sig(split, source):
    if source == "oracle":
        d = np.load(f"data/processed/oracle_toolpresence/{split}_oracletool.npz", allow_pickle=True)
    else:
        d = np.load(f"data/processed/b2a_detsignal/{FROZEN}/{split}_toolpresence.npz", allow_pickle=True)
    return {str(f): v for f, v in zip(d["frame_ids"], d["signal"].astype(float))}

def clips(split):
    man = json.load(open(f"{MD}/{split}.json"))
    return [(c["clip_id"], [f["frame"] for f in c["frames"]], np.array([f["label"] for f in c["frames"]])) for c in man["clips"]]

# ---- tool HMM（§3.5/3.6 と同じ推定）----
def fit_tool_hmm():
    d = np.load(f"data/processed/b2a_detsignal/{FROZEN}/train_toolpresence.npz", allow_pickle=True)
    o = np.load("data/processed/oracle_toolpresence/train_oracletool.npz", allow_pickle=True)
    assert list(d["frame_ids"]) == list(o["frame_ids"])
    P = d["signal"].astype(float); O = o["signal"].astype(bool)
    fid = [str(x) for x in d["frame_ids"]]
    pos = {f: i for i, f in enumerate(fid)}
    A, E = [], []
    for c in range(15):
        y = O[:, c].astype(int); cnt = np.ones((2, 2))
        for _, frames, _ in clips("train"):
            yy = [y[pos[f]] for f in frames]
            for u, v in zip(yy[:-1], yy[1:]): cnt[u, v] += 1
        A.append(cnt / cnt.sum(1, keepdims=True))
        b = np.clip((P[:, c] * NB).astype(int), 0, NB - 1); em = np.ones((2, NB))
        for st in (0, 1):
            m = y == st
            if m.sum(): em[st] += np.bincount(b[m], minlength=NB)
        E.append(em / em.sum(1, keepdims=True))
    return np.array(A), np.array(E)

def tool_filter(seq, A, E, lag):
    """seq: (T,15) の生 sigmoid -> (T,15) の posterior。lag=0 は純因果。"""
    T = len(seq); out = np.zeros_like(seq)
    for c in range(15):
        b = np.clip((seq[:, c] * NB).astype(int), 0, NB - 1)
        al = np.zeros((T, 2)); pi = np.array([.5, .5])
        for t in range(T):
            if t: pi = al[t-1] @ A[c]
            pi = pi * E[c][:, b[t]]; pi /= max(pi.sum(), 1e-12); al[t] = pi
        if lag == 0:
            out[:, c] = al[:, 1]; continue
        for t in range(T):
            hi = min(t + lag, T - 1); be = np.ones(2)
            for u in range(hi, t, -1):
                be = A[c] @ (E[c][:, b[u]] * be); be /= max(be.sum(), 1e-12)
            g = al[t] * be; g /= max(g.sum(), 1e-12); out[t, c] = g[1]
    return out

# ---- phase HMM（因果 forward filter）----
def fit_phase_hmm(tr):
    cnt = np.ones((NC, NC))
    for _, _, lab in tr:
        for u, v in zip(lab[:-1], lab[1:]): cnt[u, v] += 1
    A = cnt / cnt.sum(1, keepdims=True)
    prior = np.ones(NC)
    for _, _, lab in tr: prior += np.bincount(lab, minlength=NC)
    return A, prior / prior.sum()

def phase_filter(post, A, prior):
    T = len(post); out = np.zeros_like(post); pi = prior.copy()
    for t in range(T):
        if t: pi = out[t-1] @ A
        lik = post[t] / np.maximum(prior, 1e-9)     # 事後 -> 尤度（事前で割る）
        pi = pi * lik; pi = pi / max(pi.sum(), 1e-12); out[t] = pi
    return out

def build(split, source, A=None, E=None, lag=None):
    sig = load_sig(split, source)
    out = []
    for cid, frames, lab in clips(split):
        X = np.stack([sig[f] for f in frames])
        if A is not None: X = tool_filter(X, A, E, lag)
        out.append((cid, X, lab))
    return out

def run(name, tr, va, use_phase_hmm):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    Xtr = np.concatenate([x for _, x, _ in tr]); ytr = np.concatenate([l for _, _, l in tr])
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=1000).fit(sc.transform(Xtr), ytr)
    Aph, prior = fit_phase_hmm(tr)
    cls = list(clf.classes_)
    ev = PhaseEvaluator(num_classes=NC, class_names=CLASS_NAMES)
    for cid, X, lab in va:
        p = clf.predict_proba(sc.transform(X))
        full = np.zeros((len(X), NC)); full[:, cls] = p
        if use_phase_hmm: full = phase_filter(full, Aph, prior)
        ev.update(full.argmax(1), lab, cid)
    r = ev.compute()
    print(f"{name:34s} acc={r['phase_accuracy']:.4f} mF1={r['phase_macro_f1']:.4f} "
          f"edit={r['phase_edit_score']:6.2f} segF50={r['phase_seg_f1_50']:.3f} "
          f"hemo={r['phase_per_class_f1']['hemostasis']:.3f}")
    return r


A, E = fit_tool_hmm()
A_UNI = np.tile(np.array([[.5, .5], [.5, .5]]), (15, 1, 1))


def movavg(seq, k):
    out = np.zeros_like(seq)
    for t in range(len(seq)):
        out[t] = seq[max(0, t - k + 1):t + 1].mean(0)   # 因果（未来不使用）
    return out


def build_variant(split, kind):
    sig = load_sig(split, "oracle" if kind == "oracle" else "pred")
    out = []
    for cid, frames, lab in clips(split):
        X = np.stack([sig[f] for f in frames])
        if kind == "hmm0":   X = tool_filter(X, A, E, 0)
        elif kind == "hmm2": X = tool_filter(X, A, E, 2)
        elif kind == "uni0": X = tool_filter(X, A_UNI, E, 0)
        elif kind == "uni2": X = tool_filter(X, A_UNI, E, 2)
        elif kind == "mov3": X = movavg(X, 3)
        elif kind == "mov5": X = movavg(X, 5)
        out.append((cid, X, lab))
    return out


VARIANTS = [
    ("raw sigmoid", "raw"),
    ("moving average k=3 (control)", "mov3"),
    ("moving average k=5 (control)", "mov5"),
    ("uniform-transition HMM L=0 (negative control)", "uni0"),
    ("uniform-transition HMM L=2 (negative control)", "uni2"),
    ("learned-transition HMM L=0 (causal)", "hmm0"),
    ("learned-transition HMM L=2 (2-frame lag)", "hmm2"),
    ("ORACLE binary (upper bound)", "oracle"),
]

if __name__ == "__main__":
    for tag, use_hmm in [("per-frame argmax only", False), ("+ causal phase HMM", True)]:
        print(f"\n=== proxy phase recogniser: {tag} ===")
        for name, kind in VARIANTS:
            run(name, build_variant("train", kind), build_variant("val", kind), use_hmm)

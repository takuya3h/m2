"""標準 split（train -> val / test）でエントロピーしきい値を掃引する（プロキシ・GPU 不要）。

落とす術具は **train のみ**から H(phase given tool present)/log2(9) > しきい値 で決める。
しきい値を成績で選ばないための感度分析であり、主判定には使わない。
"""
import numpy as np, sys
src = open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

CLSN = ["Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook", "Mouth Gag",
        "Needle Holders", "Raspatory", "Retractor", "Scalpel", "Scissors", "Skewer",
        "Suction Cannula", "Syringe", "Tweezers"]


def items(split):
    pr = load_sig(split, "pred"); orc = load_sig(split, "oracle")
    return [(cid, np.stack([pr[f] for f in frames]), lab, np.stack([orc[f] for f in frames]))
            for cid, frames, lab in clips(split)]


def entropies(tr):
    G = np.concatenate([g for _, _, _, g in tr]); y = np.concatenate([l for _, _, l, _ in tr])
    H = {}
    for c in range(15):
        m = G[:, c] > 0.5
        if m.sum() < 10:
            H[c] = 1.0; continue
        p = np.bincount(y[m], minlength=NC).astype(float); p /= p.sum(); p = p[p > 0]
        H[c] = float(-(p * np.log2(p)).sum() / np.log2(NC))
    return H


def run(tr, evs, drop):
    keep = [i for i in range(15) if i not in drop]
    Xtr = np.concatenate([x[:, keep] for _, x, _, _ in tr]); ytr = np.concatenate([l for _, _, l, _ in tr])
    sc = StandardScaler().fit(Xtr); clf = LogisticRegression(max_iter=1000).fit(sc.transform(Xtr), ytr)
    Aph, prior = fit_phase_hmm([(c, x, l) for c, x, l, _ in tr]); cls = list(clf.classes_)
    out = {}
    for sp, te in evs.items():
        ev = PhaseEvaluator(num_classes=NC, class_names=CLASS_NAMES)
        for cid, X, lab, _ in te:
            p = clf.predict_proba(sc.transform(X[:, keep])); full = np.zeros((len(X), NC)); full[:, cls] = p
            ev.update(phase_filter(full, Aph, prior).argmax(1), lab, cid)
        out[sp] = ev.compute()
    return out


def main():
    tr = items("train"); evs = {"val": items("val"), "test": items("test")}
    H = entropies(tr)
    print("train のみの H（降順）: " + ", ".join(f"{CLSN[c]}:{H[c]:.3f}" for c in sorted(H, key=H.get, reverse=True)[:8]))
    base = run(tr, evs, [])
    print(f"\n{'閾値':>6s} {'落とす数':>6s} {'val mF1':>8s} {'Δ':>8s} {'test mF1':>9s} {'Δ':>8s} {'val acc':>8s} {'test acc':>9s}  落とす術具")
    for th in [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
        drop = [c for c in range(15) if H[c] > th]
        r = run(tr, evs, drop)
        names = ",".join(CLSN[c] for c in sorted(drop, key=H.get, reverse=True))
        print(f"{th:6.2f} {len(drop):6d} {r['val']['phase_macro_f1']:8.4f} "
              f"{r['val']['phase_macro_f1']-base['val']['phase_macro_f1']:+8.4f} "
              f"{r['test']['phase_macro_f1']:9.4f} {r['test']['phase_macro_f1']-base['test']['phase_macro_f1']:+8.4f} "
              f"{r['val']['phase_accuracy']:8.4f} {r['test']['phase_accuracy']:9.4f}  {names}")
    print(f"{'基準':>6s} {0:6d} {base['val']['phase_macro_f1']:8.4f} {'—':>8s} "
          f"{base['test']['phase_macro_f1']:9.4f} {'—':>8s} {base['val']['phase_accuracy']:8.4f} "
          f"{base['test']['phase_accuracy']:9.4f}  （全 15 次元）")


if __name__ == "__main__":
    main()

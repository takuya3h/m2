"""推奨構成の最終確認: 因果デノイズ × 高エントロピー術具の除去（LOVO・プロキシ・GPU 不要）。

4 腕を 15 動画 leave-one-video-out で比較する。
  A 生 presence（15 次元）
  B 生 presence − 高エントロピー術具
  C 因果デノイズ（HMM forward filter, 遅延 2 frame）
  D 因果デノイズ − 高エントロピー術具   ← 推奨構成

落とす術具は **fold ごとに train の 14 動画のみ**から
正規化エントロピー H(phase | tool present) / log2(9) > THRESH で決める（結果を見て選ばない）。
"""
import numpy as np, statistics, sys
src = open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

THRESH = float(sys.argv[1]) if len(sys.argv) > 1 else 0.45
CLSN = ["Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook", "Mouth Gag",
        "Needle Holders", "Raspatory", "Retractor", "Scalpel", "Scissors", "Skewer",
        "Suction Cannula", "Syringe", "Tweezers"]
A, E = fit_tool_hmm()


def load_all(denoise):
    out = []
    for sp in ["train", "val", "test"]:
        pr = load_sig(sp, "pred"); orc = load_sig(sp, "oracle")
        for cid, frames, lab in clips(sp):
            R = np.stack([pr[f] for f in frames]); G = np.stack([orc[f] for f in frames])
            out.append((cid, tool_filter(R, A, E, 2) if denoise else R, lab, G))
    return out


DATA = {False: load_all(False), True: load_all(True)}


def high_entropy_tools(train_items):
    G = np.concatenate([g for _, _, _, g in train_items]); y = np.concatenate([l for _, _, l, _ in train_items])
    drop = []
    for c in range(15):
        m = G[:, c] > 0.5
        if m.sum() < 10:
            drop.append(c); continue
        p = np.bincount(y[m], minlength=NC).astype(float); p /= p.sum(); p = p[p > 0]
        if float(-(p * np.log2(p)).sum() / np.log2(NC)) > THRESH:
            drop.append(c)
    return drop


def run(items_tr, items_te, drop):
    keep = [i for i in range(15) if i not in drop]
    Xtr = np.concatenate([x[:, keep] for _, x, _, _ in items_tr]); ytr = np.concatenate([l for _, _, l, _ in items_tr])
    sc = StandardScaler().fit(Xtr); clf = LogisticRegression(max_iter=1000).fit(sc.transform(Xtr), ytr)
    Aph, prior = fit_phase_hmm([(c, x, l) for c, x, l, _ in items_tr]); cls = list(clf.classes_)
    ev = PhaseEvaluator(num_classes=NC, class_names=CLASS_NAMES)
    for cid, X, lab, _ in items_te:
        p = clf.predict_proba(sc.transform(X[:, keep])); full = np.zeros((len(X), NC)); full[:, cls] = p
        ev.update(phase_filter(full, Aph, prior).argmax(1), lab, cid)
    return ev.compute()


ARMS = [("A 生", False, False), ("B 生 −高エントロピー", False, True),
        ("C デノイズ", True, False), ("D デノイズ −高エントロピー（推奨）", True, True)]
vids = sorted({c[0].split("_")[0] for c in DATA[False]})
res = {n: {} for n, _, _ in ARMS}
for vd in vids:
    for n, den, pr in ARMS:
        tr = [c for c in DATA[den] if c[0].split("_")[0] != vd]
        te = [c for c in DATA[den] if c[0].split("_")[0] == vd]
        drop = high_entropy_tools(tr) if pr else []
        if n.startswith("B") and vd == vids[0]:
            print("落とす術具（fold 01・train のみで決定）:", [CLSN[i] for i in drop])
        res[n][vd] = run(tr, te, drop)
    print(vd, " ".join(f"{n.split()[0]}:{res[n][vd]['phase_accuracy']:.3f}" for n, _, _ in ARMS), flush=True)

print(f"\n=== LOVO 15 fold（しきい値 H > {THRESH}）===")
for key, lbl in [("phase_accuracy", "acc"), ("phase_macro_f1", "macro-F1"),
                 ("phase_edit_score", "edit"), ("phase_seg_f1_50", "seg-F1@50")]:
    base = [res["A 生"][v][key] for v in vids]
    print(f"--- {lbl}\n    {'A 生（基準）':30s} mean={statistics.mean(base):8.4f} pstd={statistics.pstdev(base):7.4f}")
    for n, _, _ in ARMS[1:]:
        vals = [res[n][v][key] for v in vids]; d = [vals[i] - base[i] for i in range(len(vids))]
        se = statistics.pstdev(d) / (len(d) ** 0.5)
        print(f"    {n:30s} mean={statistics.mean(vals):8.4f}  Δ={statistics.mean(d):+8.4f} "
              f"|m|/SE={abs(statistics.mean(d))/se if se else 0:5.2f} pos={sum(1 for x in d if x>0)}/{len(d)}")
print("\n--- 工程別 F1（15 fold 平均）")
ph = ["anesthesia", "incision", "dissection", "hemostasis", "closure", "design", "irrigation", "dressing"]
print(f"{'arm':32s} " + " ".join(f"{p[:9]:>9s}" for p in ph))
for n, _, _ in ARMS:
    m = [statistics.mean([res[n][v]["phase_per_class_f1"].get(p, 0.0) for v in vids]) for p in ph]
    print(f"{n:32s} " + " ".join(f"{x:9.3f}" for x in m))

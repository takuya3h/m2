"""leave-one-video-out でプロキシを回し、det->phase の利得が動画ごとにどう振れるかを測る。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics, collections
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

def all_clips(kind):
    out=[]
    for sp in ["train","val","test"]:
        out += [(sp,)+c for c in build_variant(sp,kind)]
    return out   # (split, clip_id, X, y)

def vid(cid): return cid.split("_")[0]

KINDS=[("raw","raw"),("gap-free oracle","oracle"),("HMM L=2","hmm2")]
DATA={k:all_clips(k) for _,k in KINDS}
vids=sorted({vid(c[1]) for c in DATA["raw"]})
print("videos:",vids, len(vids))
res=collections.defaultdict(dict)
for v in vids:
    for name,k in KINDS:
        D=DATA[k]
        tr=[(c[1],c[2],c[3]) for c in D if vid(c[1])!=v]
        te=[(c[1],c[2],c[3]) for c in D if vid(c[1])==v]
        Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
        sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
        Aph,prior=fit_phase_hmm(tr); cls=list(clf.classes_)
        ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
        for cid,X,lab in te:
            p=clf.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
            full=phase_filter(full,Aph,prior); ev.update(full.argmax(1),lab,cid)
        res[v][name]=ev.compute()
print(f"\n{'video':6s} {'frames':>7s} " + " ".join(f"{n:>34s}" for n,_ in KINDS))
print(f"{'':6s} {'':7s} " + " ".join(f"{'acc    mF1    edit  segF50':>34s}" for _ in KINDS))
for v in vids:
    nf=sum(len(c[3]) for c in DATA['raw'] if vid(c[1])==v)
    line=f"{v:6s} {nf:7d} "
    for n,_ in KINDS:
        r=res[v][n]; line+=f" {r['phase_accuracy']:.4f} {r['phase_macro_f1']:.4f} {r['phase_edit_score']:6.2f} {r['phase_seg_f1_50']:.3f} "
    print(line)
print()
for metric,key in [("accuracy","phase_accuracy"),("macro_f1","phase_macro_f1"),("edit","phase_edit_score"),("segF1@50","phase_seg_f1_50")]:
    print(f"--- {metric}")
    for n,_ in KINDS:
        vals=[res[v][n][key] for v in vids]
        print(f"    {n:16s} mean={statistics.mean(vals):8.4f} pstd={statistics.pstdev(vals):7.4f} min={min(vals):.4f} max={max(vals):.4f}")
    for n,_ in KINDS[1:]:
        d=[res[v][n][key]-res[v]["raw"][key] for v in vids]
        pos=sum(1 for x in d if x>0)
        print(f"    Δ({n} − raw): mean={statistics.mean(d):+8.4f} pstd={statistics.pstdev(d):7.4f} |m|/s={abs(statistics.mean(d))/statistics.pstdev(d) if statistics.pstdev(d) else 0:5.2f} pos={pos}/{len(d)}")

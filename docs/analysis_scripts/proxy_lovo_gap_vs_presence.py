src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics, json
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
GAPD="data/processed/stage1_features/relation_detr_seed42/{}_gap.npz"
def load_gap(sp):
    d=np.load(GAPD.format(sp)); return {str(f):v for f,v in zip(d["frame_ids"],d["features"])}
A,E=fit_tool_hmm()
def build_g(split, kind):
    g=load_gap(split); sig=load_sig(split,"pred"); out=[]
    for cid,frames,lab in clips(split):
        G=np.stack([g[f] for f in frames]); R=np.stack([sig[f] for f in frames])
        if kind=="gap": X=G
        elif kind=="pres": X=R
        elif kind=="gap+pres": X=np.concatenate([G,R],1)
        elif kind=="hmm2": X=tool_filter(R,A,E,2)
        out.append((cid,X,lab))
    return out
def allc(k):
    o=[]
    for sp in ["train","val","test"]: o+=build_g(sp,k)
    return o
KINDS=["gap","pres","gap+pres","hmm2"]
D={k:allc(k) for k in KINDS}
vids=sorted({c[0].split("_")[0] for c in D["gap"]})
res={k:{} for k in KINDS}
for v in vids:
    for k in KINDS:
        tr=[c for c in D[k] if c[0].split("_")[0]!=v]; te=[c for c in D[k] if c[0].split("_")[0]==v]
        Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
        sc=StandardScaler().fit(Xtr)
        clf=LogisticRegression(max_iter=200, tol=1e-3).fit(sc.transform(Xtr),ytr)
        Aph,prior=fit_phase_hmm(tr); cls=list(clf.classes_)
        ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
        for cid,X,lab in te:
            p=clf.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
            full=phase_filter(full,Aph,prior); ev.update(full.argmax(1),lab,cid)
        res[k][v]=ev.compute()
    print(v, " ".join(f"{k}:{res[k][v]['phase_accuracy']:.4f}" for k in KINDS), flush=True)
print()
for key,label in [("phase_accuracy","acc"),("phase_macro_f1","mF1"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
    print(f"--- {label}")
    for k in KINDS:
        vals=[res[k][v][key] for v in vids]
        print(f"    {k:10s} mean={statistics.mean(vals):8.4f} pstd={statistics.pstdev(vals):7.4f}")
    for k in KINDS[1:]:
        d=[res[k][v][key]-res["gap"][v][key] for v in vids]
        se=statistics.pstdev(d)/(len(d)**0.5)
        print(f"    Δ({k} − gap): mean={statistics.mean(d):+8.4f} pstd={statistics.pstdev(d):7.4f} |m|/SE={abs(statistics.mean(d))/se if se else 0:5.2f} pos={sum(1 for x in d if x>0)}/{len(d)}")
json.dump({k:{v:{kk:vv for kk,vv in res[k][v].items() if isinstance(vv,float)} for v in vids} for k in KINDS}, open('/tmp/lovo_gap.json','w'))

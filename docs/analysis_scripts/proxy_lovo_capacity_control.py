"""E3 の容量対照: GT⊕生 の利得が「GT を足したから」か「次元が増えたから」か。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
rng=np.random.default_rng(20260822)
def build(split, kind):
    pr=load_sig(split,"pred"); orc=load_sig(split,"oracle"); out=[]
    for cid,frames,lab in clips(split):
        R=np.stack([pr[f] for f in frames]); G=np.stack([orc[f] for f in frames])
        if kind=="A_raw": X=R
        elif kind=="E_oracle+raw": X=np.concatenate([G,R],1)
        elif kind=="F_raw+raw": X=np.concatenate([R,R],1)
        elif kind=="G_raw+rand": X=np.concatenate([R,rng.random(R.shape)],1)
        elif kind=="H_raw+shuffledOracle":
            idx=rng.permutation(len(G)); X=np.concatenate([G[idx],R],1)
        out.append((cid,X,lab))
    return out
KINDS=["A_raw","E_oracle+raw","F_raw+raw","G_raw+rand","H_raw+shuffledOracle"]
D={k:sum([build(sp,k) for sp in ["train","val","test"]],[]) for k in KINDS}
vids=sorted({c[0].split("_")[0] for c in D["A_raw"]})
res={k:{} for k in KINDS}
for vd in vids:
    for k in KINDS:
        tr=[c for c in D[k] if c[0].split("_")[0]!=vd]; te=[c for c in D[k] if c[0].split("_")[0]==vd]
        Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
        sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
        Aph,prior=fit_phase_hmm(tr); cls=list(clf.classes_)
        ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
        for cid,X,lab in te:
            p=clf.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
            full=phase_filter(full,Aph,prior); ev.update(full.argmax(1),lab,cid)
        res[k][vd]=ev.compute()
    print(vd," ".join(f"{k.split('_')[0]}:{res[k][vd]['phase_accuracy']:.3f}" for k in KINDS),flush=True)
print()
for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
    print(f"--- {lbl}")
    base=[res["A_raw"][v][key] for v in vids]
    print(f"    {'A_raw (15d)':24s} mean={statistics.mean(base):8.4f} pstd={statistics.pstdev(base):7.4f}")
    for k in KINDS[1:]:
        vals=[res[k][v][key] for v in vids]; d=[vals[i]-base[i] for i in range(len(vids))]
        se=statistics.pstdev(d)/(len(d)**0.5)
        print(f"    {k+' (30d)':24s} mean={statistics.mean(vals):8.4f} pstd={statistics.pstdev(vals):7.4f} Δ={statistics.mean(d):+8.4f} |m|/SE={abs(statistics.mean(d))/se if se else 0:5.2f} pos={sum(1 for x in d if x>0)}/{len(d)}")

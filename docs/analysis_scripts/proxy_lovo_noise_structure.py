"""§3.10 の二重解離を 15 動画 LOVO で検証する（プロキシ・GPU 不要）。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

def add_noise(X,p,mode,L,rng):
    Y=X.copy(); T=len(X)
    for c in range(15):
        if mode=="iid":
            m=rng.random(T)<p; Y[m,c]=1-Y[m,c]
        elif mode=="burst":
            t=0
            while t<T:
                if rng.random()<p/L:
                    e=min(T,t+L); Y[t:e,c]=1-Y[t:e,c]; t=e
                else: t+=1
    return Y

def build(split,p,mode,L,seed):
    sig=load_sig(split,"oracle"); rng=np.random.default_rng(seed*997+{"train":0,"val":1,"test":2}[split]); out=[]
    for cid,frames,lab in clips(split):
        X=np.stack([sig[f] for f in frames])
        out.append((cid, add_noise(X,p,mode,L,rng) if p>0 else X, lab))
    return out

import sys
NSEED=int(sys.argv[1]) if len(sys.argv)>1 else 1
CONDS=[("clean",0.0,"none",1),("iid p=0.05",0.05,"iid",1),("burst L=32 p=0.05",0.05,"burst",32),
       ("iid p=0.10",0.10,"iid",1),("burst L=32 p=0.10",0.10,"burst",32)]
SEEDS=[7,17,27][:NSEED]
ALL={}
for sd in SEEDS:
    for n,p,m,L in CONDS:
        ALL[(n,sd)]=sum([build(sp,p,m,L,sd) for sp in ["train","val","test"]],[])
vids=sorted({c[0].split("_")[0] for c in ALL[(CONDS[0][0],SEEDS[0])]})
res={n:{v:[] for v in vids} for n,_,_,_ in CONDS}
for vd in vids:
  for sd in SEEDS:
    for n,_,_,_ in CONDS:
        D_={n:ALL[(n,sd)]}
        tr=[c for c in D_[n] if c[0].split("_")[0]!=vd]; te=[c for c in D_[n] if c[0].split("_")[0]==vd]
        Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
        sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
        Aph,prior=fit_phase_hmm(tr); cls=list(clf.classes_)
        ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
        for cid,X,lab in te:
            pr=clf.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=pr
            full=phase_filter(full,Aph,prior); ev.update(full.argmax(1),lab,cid)
        res[n][vd].append(ev.compute())
  print(vd," ".join(f"{n}:{statistics.mean([r['phase_accuracy'] for r in res[n][vd]]):.3f}" for n,_,_,_ in CONDS),flush=True)
print()
for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
    print(f"--- {lbl}")
    base=[statistics.mean([r[key] for r in res["clean"][v]]) for v in vids]
    print(f"    {'clean':20s} mean={statistics.mean(base):8.4f}")
    for n,_,_,_ in CONDS[1:]:
        vals=[statistics.mean([r[key] for r in res[n][v]]) for v in vids]; d=[vals[i]-base[i] for i in range(len(vids))]
        se=statistics.pstdev(d)/(len(d)**0.5)
        print(f"    {n:20s} mean={statistics.mean(vals):8.4f}  Δ={statistics.mean(d):+8.4f} |m|/SE={abs(statistics.mean(d))/se if se else 0:5.2f} neg={sum(1 for x in d if x<0)}/{len(d)}")

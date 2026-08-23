"""時系列の受容野を広げても「術具除去」の利得は残るか（LOVO・プロキシ）。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
THRESH=0.45
def context(X,lags):
    T=len(X); return np.concatenate([X[np.clip(np.arange(T)-L,0,T-1)] for L in lags],1)
def base_items(split):
    pr=load_sig(split,"pred"); orc=load_sig(split,"oracle")
    return [(cid,np.stack([pr[f] for f in frames]),lab,np.stack([orc[f] for f in frames])) for cid,frames,lab in clips(split)]
RAW=sum([base_items(sp) for sp in ["train","val","test"]],[])
vids=sorted({c[0].split("_")[0] for c in RAW})
def he(tr):
    G=np.concatenate([g for _,_,_,g in tr]); y=np.concatenate([l for _,_,l,_ in tr]); drop=[]
    for c in range(15):
        m=G[:,c]>0.5
        if m.sum()<10: drop.append(c); continue
        p=np.bincount(y[m],minlength=NC).astype(float); p/=p.sum(); p=p[p>0]
        if float(-(p*np.log2(p)).sum()/np.log2(NC))>THRESH: drop.append(c)
    return drop
LAGSETS=[("K=0",[0]),("K=8",[0,1,2,4,8]),("K=32",[0,1,2,4,8,16,32]),("K=128",[0,1,2,4,8,16,32,64,128])]
for name,lags in LAGSETS:
    r0={};r1={}
    for vd in vids:
        tr=[c for c in RAW if c[0].split("_")[0]!=vd]; te=[c for c in RAW if c[0].split("_")[0]==vd]
        drop=he(tr); keep=[i for i in range(15) if i not in drop]
        for tag,ks in [("full",list(range(15))),("pruned",keep)]:
            Xtr=np.concatenate([context(x[:,ks],lags) for _,x,_,_ in tr]); ytr=np.concatenate([l for _,_,l,_ in tr])
            sc=StandardScaler().fit(Xtr); m=LogisticRegression(max_iter=800).fit(sc.transform(Xtr),ytr)
            Aph,prior=fit_phase_hmm([(c,x,l) for c,x,l,_ in tr]); cls=list(m.classes_)
            ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
            for cid,X,lab,_ in te:
                p=m.predict_proba(sc.transform(context(X[:,ks],lags))); full=np.zeros((len(X),NC)); full[:,cls]=p
                ev.update(phase_filter(full,Aph,prior).argmax(1),lab,cid)
            (r0 if tag=="full" else r1)[vd]=ev.compute()
    out=[]
    for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1")]:
        d=[r1[v][key]-r0[v][key] for v in vids]; se=statistics.pstdev(d)/len(d)**0.5
        out.append(f"{lbl} 全={statistics.mean([r0[v][key] for v in vids]):7.4f} Δ={statistics.mean(d):+7.4f}({abs(statistics.mean(d))/se:4.2f},{sum(1 for x in d if x>0)}/15)")
    print(f"{name:6s} | " + " | ".join(out), flush=True)

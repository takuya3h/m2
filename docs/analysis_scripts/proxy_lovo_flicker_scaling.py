"""P3 の反証可能な予測: デノイズの分節利得は「ちらつき超過」に比例するか（LOVO・プロキシ）。

ちらつきの少ない検出器（強 aug）ほど、デノイズで得られる edit 利得が小さいはず。
"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
NB=20
SRCS=["relation_detr_seed42","relation_detr_seed123","relation_detr_seed456",
      "relation_detr_augstrong_seed42","relation_detr_augstrong_seed123","relation_detr_augstrong_seed456"]

def load_src(tag, split):
    d=np.load(f"data/processed/b2a_detsignal/{tag}/{split}_toolpresence.npz",allow_pickle=True)
    return {str(f):v for f,v in zip(d["frame_ids"],d["signal"].astype(float))}

def fit_hmm(tag):
    d=np.load(f"data/processed/b2a_detsignal/{tag}/train_toolpresence.npz",allow_pickle=True)
    o=np.load("data/processed/oracle_toolpresence/train_oracletool.npz",allow_pickle=True)
    P=d["signal"].astype(float); O=o["signal"].astype(bool); fid=[str(x) for x in d["frame_ids"]]
    pos={f:i for i,f in enumerate(fid)}
    A=[];E=[]
    for c in range(15):
        y=O[:,c].astype(int); cnt=np.ones((2,2))
        for _,frames,_ in clips("train"):
            yy=[y[pos[f]] for f in frames]
            for u,v in zip(yy[:-1],yy[1:]): cnt[u,v]+=1
        A.append(cnt/cnt.sum(1,keepdims=True))
        b=np.clip((P[:,c]*NB).astype(int),0,NB-1); em=np.ones((2,NB))
        for st in (0,1):
            m=y==st
            if m.sum(): em[st]+=np.bincount(b[m],minlength=NB)
        E.append(em/em.sum(1,keepdims=True))
    return np.array(A),np.array(E)

def flicker(tag):
    """val でのちらつき倍率（GT 比）。"""
    d=np.load(f"data/processed/b2a_detsignal/{tag}/val_toolpresence.npz",allow_pickle=True)
    o=np.load("data/processed/oracle_toolpresence/val_oracletool.npz",allow_pickle=True)
    P=d["signal"].astype(float); O=o["signal"].astype(bool)
    fids=[str(x) for x in d["frame_ids"]]
    vid=np.array(["_".join(x.split("_")[:2]) for x in fids])
    idx=[0]+[i for i in range(1,len(vid)) if vid[i]!=vid[i-1]]+[len(vid)]
    segs=[(idx[i],idx[i+1]) for i in range(len(idx)-1)]
    valid=[c for c in range(15) if O[:,c].sum()>0]
    def f1(y,s,t):
        p=s>=t; tp=(p&y).sum(); fp=(p&~y).sum(); fn=(~p&y).sum(); return 2*tp/max(2*tp+fp+fn,1)
    ths=np.round(np.linspace(0.01,0.99,99),3)
    th=np.array([ths[int(np.argmax([f1(O[:,c],P[:,c],t) for t in ths]))] if c in valid else .5 for c in range(15)])
    B=P>=th[None,:]
    def tr(X):
        t=0;n=0
        for a,b in segs: t+=np.abs(np.diff(X[a:b][:,valid].astype(int),axis=0)).sum(); n+=b-a-1
        return t/n
    return tr(B)/tr(O), np.mean([f1(O[:,c],P[:,c],th[c]) for c in valid])

def lovo(tag, denoise, A, E):
    D=[]
    for sp in ["train","val","test"]:
        sig=load_src(tag,sp)
        for cid,frames,lab in clips(sp):
            R=np.stack([sig[f] for f in frames])
            D.append((cid, tool_filter(R,A,E,2) if denoise else R, lab))
    vids=sorted({c[0].split("_")[0] for c in D}); out={}
    for vd in vids:
        tr=[c for c in D if c[0].split("_")[0]!=vd]; te=[c for c in D if c[0].split("_")[0]==vd]
        Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
        sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
        Aph,prior=fit_phase_hmm(tr); cls=list(clf.classes_)
        ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
        for cid,X,lab in te:
            p=clf.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
            ev.update(phase_filter(full,Aph,prior).argmax(1),lab,cid)
        out[vd]=ev.compute()
    return out, vids

print(f"{'凍結源':34s} {'ちらつき倍率':>10s} {'presF1':>7s} {'edit(生)':>9s} {'edit(デノイズ)':>13s} {'Δedit':>8s} {'|m|/SE':>7s} {'pos':>6s}")
rows=[]
for tag in SRCS:
    fl,pf1=flicker(tag)
    A,E=fit_hmm(tag)
    r0,vids=lovo(tag,False,A,E); r1,_=lovo(tag,True,A,E)
    d=[r1[v]["phase_edit_score"]-r0[v]["phase_edit_score"] for v in vids]
    se=statistics.pstdev(d)/len(d)**0.5
    e0=statistics.mean([r0[v]["phase_edit_score"] for v in vids]); e1=statistics.mean([r1[v]["phase_edit_score"] for v in vids])
    rows.append((tag,fl,pf1,e0,e1,statistics.mean(d)))
    print(f"{tag:34s} {fl:10.2f} {pf1:7.3f} {e0:9.2f} {e1:13.2f} {statistics.mean(d):+8.2f} {abs(statistics.mean(d))/se:7.2f} {sum(1 for x in d if x>0):3d}/{len(d)}")
x=[r[1] for r in rows]; y=[r[5] for r in rows]
print(f"\nちらつき倍率 vs Δedit（デノイズ利得）: Pearson r={np.corrcoef(x,y)[0,1]:+.3f} (n={len(x)})")

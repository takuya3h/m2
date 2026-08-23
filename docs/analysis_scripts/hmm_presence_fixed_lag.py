"""固定ラグ HMM 平滑化: ラグ L フレームだけ遅延して判定した場合の presence 品質。
L=0 は forward filtering（因果・遅延なし）、L→∞ は完全な forward-backward。
"""
import numpy as np, sys
sys.path.insert(0,'docs/analysis_scripts')
NB=20
DET='data/processed/b2a_detsignal/relation_detr_seed42/{}_toolpresence.npz'
ORA='data/processed/oracle_toolpresence/{}_oracletool.npz'
CLS=["Bipolar Forceps","Electric Cautery","Forceps","Gauze","Hook","Mouth Gag","Needle Holders","Raspatory","Retractor","Scalpel","Scissors","Skewer","Suction Cannula","Syringe","Tweezers"]
def load(sp):
    d=np.load(DET.format(sp),allow_pickle=True); o=np.load(ORA.format(sp),allow_pickle=True)
    assert list(d['frame_ids'])==list(o['frame_ids'])
    return d['frame_ids'], d['signal'].astype(float), o['signal'].astype(bool)
def segs_of(f):
    v=np.array(["_".join(x.split("_")[:2]) for x in f])
    i=[0]+[k for k in range(1,len(v)) if v[k]!=v[k-1]]+[len(v)]
    return [(i[k],i[k+1]) for k in range(len(i)-1)]
def fit(sp='train'):
    f,P,O=load(sp); S=segs_of(f); A=[];E=[]
    for c in range(15):
        y=O[:,c].astype(int); cnt=np.ones((2,2))
        for a,b in S:
            yy=y[a:b]
            for u,v in zip(yy[:-1],yy[1:]): cnt[u,v]+=1
        A.append(cnt/cnt.sum(1,keepdims=True))
        bnn=np.clip((P[:,c]*NB).astype(int),0,NB-1); em=np.ones((2,NB))
        for st in (0,1):
            m=y==st
            if m.sum(): em[st]+=np.bincount(bnn[m],minlength=NB)
        E.append(em/em.sum(1,keepdims=True))
    return np.array(A),np.array(E)
def fixed_lag(P,f,A,E,L):
    """時刻 t の判定に t+L までの観測を使う（遅延 L フレーム）。L=0 は純因果。"""
    out=np.zeros_like(P); S=segs_of(f)
    for c in range(15):
        b=np.clip((P[:,c]*NB).astype(int),0,NB-1)
        for s,e in S:
            n=e-s
            # forward
            al=np.zeros((n,2)); pi=np.array([.5,.5])
            for t in range(n):
                if t: pi=al[t-1]@A[c]
                pi=pi*E[c][:,b[s+t]]; pi/=max(pi.sum(),1e-12); al[t]=pi
            if L==0:
                out[s:e,c]=al[:,1]; continue
            # backward within window: beta_{t..t+L}
            for t in range(n):
                hi=min(t+L,n-1)
                be=np.ones(2)
                for u in range(hi,t,-1):
                    be=A[c]@(E[c][:,b[s+u]]*be); be/=max(be.sum(),1e-12)
                g=al[t]*be; g/=max(g.sum(),1e-12); out[s+t,c]=g[1]
    return out
def f1(y,s,th):
    p=s>=th; tp=(p&y).sum(); fp=(p&~y).sum(); fn=(~p&y).sum(); return 2*tp/max(2*tp+fp+fn,1)
A,E=fit('train')
f,P,O=load('val'); S=segs_of(f); valid=[c for c in range(15) if O[:,c].sum()>0]
def rep(name,X):
    ths=np.round(np.linspace(0.01,0.99,99),3)
    th=np.array([ths[int(np.argmax([f1(O[:,c],X[:,c],t) for t in ths]))] if c in valid else .5 for c in range(15)])
    B=X>=th[None,:]
    mf=np.mean([f1(O[:,c],X[:,c],th[c]) for c in valid])
    err=np.mean([(B[:,c]!=O[:,c]).mean() for c in valid])
    ex=(B[:,valid]==O[:,valid]).all(1).mean()
    tot=0;n=0
    for a,b in S: tot+=np.abs(np.diff(B[a:b][:,valid].astype(int),axis=0)).sum(); n+=b-a-1
    print(f"{name:26s} macroF1={mf:.4f} err={err*100:5.2f}% exact={ex*100:5.2f}% trans={tot/n:.4f}")
rep("raw sigmoid (L=—)",P)
for L in [0,1,2,4,8,16,10**6]:
    rep(f"HMM lag L={L if L<10**6 else 'inf(FB)'}",fixed_lag(P,f,A,E,L if L<10**6 else 10000))
tot=0;n=0
for a,b in S: tot+=np.abs(np.diff(O[a:b][:,valid].astype(int),axis=0)).sum(); n+=b-a-1
print(f"{'GROUND TRUTH':26s} macroF1=1.0000 err= 0.00% exact=100.00% trans={tot/n:.4f}")

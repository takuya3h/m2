"""ノイズを評価側だけに掛けたときの選択性（LOVO・プロキシ）。

学習側も汚す設定（§3.10）は「モデルがノイズに適応する」効果を含む。
評価側だけを汚せば「情報が壊れる」効果だけを見られる。
"""
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
    sig=load_sig(split,"oracle"); rng=np.random.default_rng(seed*991+{"train":0,"val":1,"test":2}[split]); out=[]
    for cid,frames,lab in clips(split):
        X=np.stack([sig[f] for f in frames])
        out.append((cid, add_noise(X,p,mode,L,rng) if p>0 else X, lab))
    return out
CONDS=[("clean",0.0,"none",1),("iid p=0.05",0.05,"iid",1),("burst L=32 p=0.05",0.05,"burst",32),
       ("iid p=0.10",0.10,"iid",1),("burst L=32 p=0.10",0.10,"burst",32)]
CLEAN=sum([build(sp,0,"none",1,7) for sp in ["train","val","test"]],[])
NOISY={n:sum([build(sp,p,m,L,7) for sp in ["train","val","test"]],[]) for n,p,m,L in CONDS}
vids=sorted({c[0].split("_")[0] for c in CLEAN})
res={n:{} for n,_,_,_ in CONDS}
for vd in vids:
    tr=[c for c in CLEAN if c[0].split("_")[0]!=vd]          # 学習は常にクリーン
    Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
    sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
    Aph,prior=fit_phase_hmm(tr); cls=list(clf.classes_)
    for n,_,_,_ in CONDS:
        te=[c for c in NOISY[n] if c[0].split("_")[0]==vd]    # 評価側だけ汚す
        ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
        for cid,X,lab in te:
            p=clf.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
            ev.update(phase_filter(full,Aph,prior).argmax(1),lab,cid)
        res[n][vd]=ev.compute()
    print(vd," ".join(f"{n}:{res[n][vd]['phase_accuracy']:.3f}" for n,_,_,_ in CONDS),flush=True)
print()
for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
    print(f"--- {lbl}")
    base=[res["clean"][v][key] for v in vids]
    print(f"    {'clean':20s} mean={statistics.mean(base):8.4f}")
    for n,_,_,_ in CONDS[1:]:
        vals=[res[n][v][key] for v in vids]; d=[vals[i]-base[i] for i in range(len(vids))]
        se=statistics.pstdev(d)/len(d)**0.5
        print(f"    {n:20s} mean={statistics.mean(vals):8.4f}  Δ={statistics.mean(d):+8.4f} |m|/SE={abs(statistics.mean(d))/se if se else 0:5.2f} neg={sum(1 for x in d if x<0)}/{len(d)}")

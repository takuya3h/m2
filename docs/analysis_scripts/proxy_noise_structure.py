"""E0 プロキシ: 同じ誤り率で iid フリップ と バーストノイズ を比べる。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

def add_noise(X, p, mode, L, rng):
    """X: (T,15) 0/1。期待誤り率 p でノイズを与える。"""
    Y=X.copy(); T=len(X)
    for c in range(15):
        if mode=="iid":
            m=rng.random(T)<p
            Y[m,c]=1-Y[m,c]
        else:  # burst: 長さ L のランを確率 p/L で開始
            t=0
            while t<T:
                if rng.random()<p/L:
                    e=min(T,t+L); Y[t:e,c]=1-Y[t:e,c]; t=e
                else: t+=1
    return Y

def build_noisy(split, p, mode, L, seed):
    sig=load_sig(split,"oracle"); rng=np.random.default_rng(seed*1000+{"train":0,"val":1,"test":2}[split])
    out=[]
    for cid,frames,lab in clips(split):
        X=np.stack([sig[f] for f in frames])
        out.append((cid, add_noise(X,p,mode,L,rng) if p>0 else X, lab))
    return out

def flicker_err(sets, split):
    sig=load_sig(split,"oracle"); tot_e=0;n=0;tr=0;m=0
    for cid,X,lab in sets:
        G=np.stack([sig[f] for f in dict((c[0],c[1]) for c in clips(split))[cid]])
        tot_e+=(X!=G).sum(); n+=G.size
        tr+=np.abs(np.diff(X,axis=0)).sum(); m+=len(X)-1
    return tot_e/n, tr/m

def run(name, tr, te):
    Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
    sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
    Aph,prior=fit_phase_hmm(tr); cls=list(clf.classes_)
    ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
    for cid,X,lab in te:
        p=clf.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
        full=phase_filter(full,Aph,prior); ev.update(full.argmax(1),lab,cid)
    r=ev.compute()
    return r

print(f"{'condition':28s} {'errRate':>8s} {'trans':>7s} | {'test acc':>8s} {'mF1':>7s} {'edit':>7s} {'segF50':>7s}")
for p in [0.0,0.05,0.10,0.20]:
    for mode,L in ([("clean",1)] if p==0 else [("iid",1),("burst",8),("burst",32)]):
        accs=[];f1s=[];eds=[];sgs=[];ers=[];trs=[]
        for seed in [1,2,3]:
            tr=build_noisy("train",p,mode,L,seed)+build_noisy("val",p,mode,L,seed)
            te=build_noisy("test",p,mode,L,seed)
            e,t=flicker_err(te,"test"); ers.append(e); trs.append(t)
            r=run(f"{mode}{L}",tr,te)
            accs.append(r["phase_accuracy"]);f1s.append(r["phase_macro_f1"]);eds.append(r["phase_edit_score"]);sgs.append(r["phase_seg_f1_50"])
        lbl=f"p={p} {mode}" + (f" L={L}" if mode=="burst" else "")
        print(f"{lbl:28s} {statistics.mean(ers)*100:7.2f}% {statistics.mean(trs):7.4f} | {statistics.mean(accs):8.4f} {statistics.mean(f1s):7.4f} {statistics.mean(eds):7.2f} {statistics.mean(sgs):7.3f}")

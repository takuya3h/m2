"""時系列の受容野を広げるとデノイズ利得は吸収されるか（LOVO・プロキシ）。

per-frame 分類器に前後 K フレームの文脈を与える（因果性のため過去のみ）。
TeCNO の受容野は 2^7=128 frame なので、K を増やしたときの利得の推移を見る。
"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
A,E=fit_tool_hmm()

def context(X, lags):
    """過去のみのラグ特徴を連結（因果）。lags は [0,1,2,4,...] のような相対位置。"""
    T=len(X); out=[]
    for L in lags:
        idx=np.clip(np.arange(T)-L, 0, T-1)
        out.append(X[idx])
    return np.concatenate(out,1)

def items(split, den, lags):
    pr=load_sig(split,"pred"); out=[]
    for cid,frames,lab in clips(split):
        R=np.stack([pr[f] for f in frames])
        if den: R=tool_filter(R,A,E,2)
        out.append((cid, context(R,lags), lab))
    return out

LAGSETS=[("K=0（文脈なし）",[0]),
         ("K=8",[0,1,2,4,8]),
         ("K=32",[0,1,2,4,8,16,32]),
         ("K=128（TeCNO 相当）",[0,1,2,4,8,16,32,64,128])]
for name,lags in LAGSETS:
    D={d: sum([items(sp,d,lags) for sp in ["train","val","test"]],[]) for d in (False,True)}
    vids=sorted({c[0].split("_")[0] for c in D[False]})
    r={False:{},True:{}}
    for vd in vids:
        for den in (False,True):
            tr=[c for c in D[den] if c[0].split("_")[0]!=vd]; te=[c for c in D[den] if c[0].split("_")[0]==vd]
            Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
            sc=StandardScaler().fit(Xtr); m=LogisticRegression(max_iter=800).fit(sc.transform(Xtr),ytr)
            Aph,prior=fit_phase_hmm(tr); cls=list(m.classes_)
            ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
            for cid,X,lab in te:
                p=m.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
                ev.update(phase_filter(full,Aph,prior).argmax(1),lab,cid)
            r[den][vd]=ev.compute()
    out=[]
    for key,lbl in [("phase_accuracy","acc"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
        d=[r[True][v][key]-r[False][v][key] for v in vids]; se=statistics.pstdev(d)/len(d)**0.5
        out.append(f"{lbl} 生={statistics.mean([r[False][v][key] for v in vids]):7.4f} Δ={statistics.mean(d):+7.4f}({abs(statistics.mean(d))/se:4.2f},{sum(1 for x in d if x>0)}/15)")
    print(f"{name:22s} 次元={len(lags)*15:4d} | " + " | ".join(out), flush=True)

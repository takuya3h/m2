"""Q11: 「誤り除去」と「binary 化」を分離する（LOVO・プロキシ・GPU 不要）。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# クラス別最良閾値は train のみで決める
def fit_thresholds():
    d=np.load(f"data/processed/b2a_detsignal/{FROZEN}/train_toolpresence.npz",allow_pickle=True) if False else np.load("data/processed/b2a_detsignal/relation_detr_seed42/train_toolpresence.npz",allow_pickle=True)
    o=np.load("data/processed/oracle_toolpresence/train_oracletool.npz",allow_pickle=True)
    P=d["signal"].astype(float); O=o["signal"].astype(bool)
    def f1(y,s,t):
        p=s>=t; tp=(p&y).sum(); fp=(p&~y).sum(); fn=(~p&y).sum(); return 2*tp/max(2*tp+fp+fn,1)
    ths=np.round(np.linspace(0.01,0.99,99),3)
    return np.array([ths[int(np.argmax([f1(O[:,c],P[:,c],t) for t in ths]))] if O[:,c].sum()>0 else 0.5 for c in range(15)])
TH=fit_thresholds()
print("thresholds(train):", TH)

def build(split, kind):
    pr=load_sig(split,"pred"); orc=load_sig(split,"oracle"); out=[]
    for cid,frames,lab in clips(split):
        R=np.stack([pr[f] for f in frames]); G=np.stack([orc[f] for f in frames])
        if kind=="A_raw": X=R
        elif kind=="B_bin": X=(R>=TH[None,:]).astype(float)
        elif kind=="D_oracle": X=G
        elif kind=="E_oracle+raw": X=np.concatenate([G,R],1)
        out.append((cid,X,lab))
    return out
KINDS=["A_raw","B_bin","D_oracle","E_oracle+raw"]
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
    print(vd," ".join(f"{k}:{res[k][vd]['phase_accuracy']:.3f}" for k in KINDS),flush=True)
print()
for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
    print(f"--- {lbl}")
    for k in KINDS:
        vals=[res[k][v][key] for v in vids]
        print(f"    {k:16s} mean={statistics.mean(vals):8.4f} pstd={statistics.pstdev(vals):7.4f}")
    for a,b,lab2 in [("B_bin","A_raw","binary 化の純効果 (B−A)"),("D_oracle","B_bin","誤り除去の純効果 (D−B)"),
                     ("E_oracle+raw","A_raw","誤り除去のみ・段階情報保持 (E−A)"),("D_oracle","A_raw","オラクル全体 (D−A)")]:
        d=[res[a][v][key]-res[b][v][key] for v in vids]; se=statistics.pstdev(d)/(len(d)**0.5)
        print(f"    {lab2:34s} Δ={statistics.mean(d):+8.4f} |m|/SE={abs(statistics.mean(d))/se if se else 0:5.2f} pos={sum(1 for x in d if x>0)}/{len(d)}")

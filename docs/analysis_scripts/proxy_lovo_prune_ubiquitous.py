src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
A,E=fit_tool_hmm()
UBIQ3=[5,14,3]   # Mouth Gag / Tweezers / Gauze（EDA の正規化エントロピー上位＝工程を弁別しない）
def build(split, denoise, drop):
    sig=load_sig(split,"pred"); out=[]
    for cid,frames,lab in clips(split):
        R=np.stack([sig[f] for f in frames])
        if denoise: R=tool_filter(R,A,E,2)
        if drop: R=R[:,[i for i in range(15) if i not in UBIQ3]]
        out.append((cid,R,lab))
    return out
VAR=[("raw",False,False),("drop-ubiq",False,True),("denoise",True,False),("denoise+drop-ubiq",True,True)]
D={n:sum([build(sp,d,r) for sp in ["train","val","test"]],[]) for n,d,r in VAR}
vids=sorted({c[0].split("_")[0] for c in D["raw"]})
res={n:{} for n,_,_ in VAR}
for vd in vids:
    for n,_,_ in VAR:
        tr=[c for c in D[n] if c[0].split("_")[0]!=vd]; te=[c for c in D[n] if c[0].split("_")[0]==vd]
        Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
        sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
        Aph,prior=fit_phase_hmm(tr); cls=list(clf.classes_)
        ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
        for cid,X,lab in te:
            p=clf.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
            full=phase_filter(full,Aph,prior); ev.update(full.argmax(1),lab,cid)
        res[n][vd]=ev.compute()
for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
    print(f"--- {lbl}")
    base=[res["raw"][v][key] for v in vids]
    print(f"    {'raw':20s} mean={statistics.mean(base):8.4f} pstd={statistics.pstdev(base):7.4f}")
    for n,_,_ in VAR[1:]:
        vals=[res[n][v][key] for v in vids]; d=[vals[i]-base[i] for i in range(len(vids))]
        se=statistics.pstdev(d)/(len(d)**0.5)
        print(f"    {n:20s} mean={statistics.mean(vals):8.4f}  Δ={statistics.mean(d):+8.4f} |m|/SE={abs(statistics.mean(d))/se if se else 0:5.2f} pos={sum(1 for x in d if x>0)}/{len(d)}")
print("\n--- per-phase F1（15 fold のフレーム加重ではなく fold 平均）")
ph=["anesthesia","incision","dissection","hemostasis","closure","design","irrigation","dressing"]
print(f"{'variant':20s} "+" ".join(f"{p[:9]:>9s}" for p in ph))
for n,_,_ in VAR:
    m=[statistics.mean([res[n][v]["phase_per_class_f1"].get(p,0.0) for v in vids]) for p in ph]
    print(f"{n:20s} "+" ".join(f"{x:9.3f}" for x in m))

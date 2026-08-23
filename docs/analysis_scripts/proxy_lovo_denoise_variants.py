"""Q9: 短い工程への感度を保ったままデノイズできるか（LOVO・プロキシ）。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
A,E=fit_tool_hmm()
# 非対称版: OFF->ON の遷移確率を 3 倍にして短い在室を潰しにくくする
A_asym=A.copy()
for c in range(15):
    p=min(A[c][0,1]*3.0, 0.5); A_asym[c][0,1]=p; A_asym[c][0,0]=1-p

def variants(R):
    F=tool_filter(R,A,E,2); Fa=tool_filter(R,A_asym,E,2)
    return {"raw":R, "hmm2":F, "hmm2_asym":Fa, "max_raw_hmm":np.maximum(R,F), "raw+hmm":np.concatenate([R,F],1)}

def build(split):
    sig=load_sig(split,"pred"); out={k:[] for k in ["raw","hmm2","hmm2_asym","max_raw_hmm","raw+hmm"]}
    for cid,frames,lab in clips(split):
        R=np.stack([sig[f] for f in frames]); V=variants(R)
        for k in out: out[k].append((cid,V[k],lab))
    return out
DATA={k:[] for k in ["raw","hmm2","hmm2_asym","max_raw_hmm","raw+hmm"]}
for sp in ["train","val","test"]:
    b=build(sp)
    for k in DATA: DATA[k]+=b[k]
vids=sorted({c[0].split("_")[0] for c in DATA["raw"]})
res={k:{} for k in DATA}
for vd in vids:
    for k in DATA:
        tr=[c for c in DATA[k] if c[0].split("_")[0]!=vd]; te=[c for c in DATA[k] if c[0].split("_")[0]==vd]
        Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
        sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
        Aph,prior=fit_phase_hmm(tr); cls=list(clf.classes_)
        ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
        for cid,X,lab in te:
            p=clf.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
            full=phase_filter(full,Aph,prior); ev.update(full.argmax(1),lab,cid)
        res[k][vd]=ev.compute()
    print(vd," ".join(f"{k}:{res[k][vd]['phase_accuracy']:.3f}" for k in DATA),flush=True)
print()
for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
    print(f"--- {lbl}")
    base=[res["raw"][v][key] for v in vids]
    print(f"  {'raw':14s} mean={statistics.mean(base):8.4f}")
    for k in list(DATA)[1:]:
        vals=[res[k][v][key] for v in vids]; d=[vals[i]-base[i] for i in range(len(vids))]
        se=statistics.pstdev(d)/(len(d)**0.5)
        print(f"  {k:14s} mean={statistics.mean(vals):8.4f}  Δ={statistics.mean(d):+8.4f} |m|/SE={abs(statistics.mean(d))/se if se else 0:5.2f} pos={sum(1 for x in d if x>0)}/{len(d)}")
print("\n--- 工程別 F1（15 fold 平均）")
ph=["anesthesia","incision","dissection","hemostasis","closure","design","irrigation","dressing"]
print(f"{'variant':14s} "+" ".join(f"{p[:9]:>9s}" for p in ph))
for k in DATA:
    m=[statistics.mean([res[k][v]["phase_per_class_f1"].get(p,0.0) for v in vids]) for p in ph]
    print(f"{k:14s} "+" ".join(f"{x:9.3f}" for x in m))

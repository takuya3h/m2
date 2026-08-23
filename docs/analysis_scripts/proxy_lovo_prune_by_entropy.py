"""E9 の正式プロトコル: fold ごとに train のみで「工程を弁別しない術具」を選び、上位 k 個を落とす。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
CLSN=["Bipolar Forceps","Electric Cautery","Forceps","Gauze","Hook","Mouth Gag","Needle Holders","Raspatory","Retractor","Scalpel","Scissors","Skewer","Suction Cannula","Syringe","Tweezers"]
A,E=fit_tool_hmm()

def load_all(denoise):
    pr={}; out=[]
    for sp in ["train","val","test"]:
        sig=load_sig(sp,"pred"); orc=load_sig(sp,"oracle")
        for cid,frames,lab in clips(sp):
            R=np.stack([sig[f] for f in frames]); G=np.stack([orc[f] for f in frames])
            X=tool_filter(R,A,E,2) if denoise else R
            out.append((cid,X,lab,G))
    return out
DATA={False: load_all(False), True: load_all(True)}

def entropy_rank(train_items):
    """train のみから H(phase | tool present) の正規化エントロピーを計算し、大きい順に返す。"""
    G=np.concatenate([g for _,_,_,g in train_items]); y=np.concatenate([l for _,_,l,_ in train_items])
    K=NC; H=[]
    for c in range(15):
        m=G[:,c]>0.5
        if m.sum()<10: H.append(1.0); continue
        p=np.bincount(y[m],minlength=K).astype(float); p/=p.sum()
        p=p[p>0]
        H.append(float(-(p*np.log2(p)).sum()/np.log2(K)))
    return list(np.argsort(-np.array(H))), H

def evaluate(items_tr, items_te, drop):
    keep=[i for i in range(15) if i not in drop]
    Xtr=np.concatenate([x[:,keep] for _,x,_,_ in items_tr]); ytr=np.concatenate([l for _,_,l,_ in items_tr])
    sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
    Aph,prior=fit_phase_hmm([(c,x,l) for c,x,l,_ in items_tr]); cls=list(clf.classes_)
    ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
    for cid,X,lab,_ in items_te:
        p=clf.predict_proba(sc.transform(X[:,keep])); full=np.zeros((len(X),NC)); full[:,cls]=p
        full=phase_filter(full,Aph,prior); ev.update(full.argmax(1),lab,cid)
    return ev.compute()

vids=sorted({c[0].split("_")[0] for c in DATA[False]})
KS=[0,1,2,3,4,5]
res={(d,k):{} for d in (False,True) for k in KS}
dropped_log={}
for vd in vids:
    for d in (False,True):
        tr=[c for c in DATA[d] if c[0].split("_")[0]!=vd]; te=[c for c in DATA[d] if c[0].split("_")[0]==vd]
        order,H=entropy_rank(tr)
        if d is False: dropped_log[vd]=[CLSN[i] for i in order[:5]]
        for k in KS:
            res[(d,k)][vd]=evaluate(tr,te,set(order[:k]))
    print(vd, "drop order:", ", ".join(dropped_log[vd][:4]), flush=True)
print()
print("※ 落とす術具は fold ごとに train のみの H(phase|tool) で決めている（結果を見て選んでいない）")
for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
    print(f"--- {lbl}")
    for d in (False,True):
        tag="denoise" if d else "raw    "
        base=[res[(d,0)][v][key] for v in vids]
        print(f"  {tag} k=0  mean={statistics.mean(base):8.4f} pstd={statistics.pstdev(base):7.4f}")
        for k in KS[1:]:
            vals=[res[(d,k)][v][key] for v in vids]; dd=[vals[i]-base[i] for i in range(len(vids))]
            se=statistics.pstdev(dd)/(len(dd)**0.5)
            print(f"  {tag} k={k}  mean={statistics.mean(vals):8.4f}  Δ={statistics.mean(dd):+8.4f} |m|/SE={abs(statistics.mean(dd))/se if se else 0:5.2f} pos={sum(1 for x in dd if x>0)}/{len(dd)}")

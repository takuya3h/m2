"""E9（高エントロピー術具の除去）の利得が凍結源に依らないかを確かめる（LOVO・6 凍結源）。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
SRCS=["relation_detr_seed42","relation_detr_seed123","relation_detr_seed456",
      "relation_detr_augstrong_seed42","relation_detr_augstrong_seed123","relation_detr_augstrong_seed456"]
THRESH=0.45
def load_src(tag,split):
    d=np.load(f"data/processed/b2a_detsignal/{tag}/{split}_toolpresence.npz",allow_pickle=True)
    return {str(f):v for f,v in zip(d["frame_ids"],d["signal"].astype(float))}
def build(tag):
    out=[]
    for sp in ["train","val","test"]:
        sig=load_src(tag,sp); orc=load_sig(sp,"oracle")
        for cid,frames,lab in clips(sp):
            out.append((cid,np.stack([sig[f] for f in frames]),lab,np.stack([orc[f] for f in frames])))
    return out
def he(items):
    G=np.concatenate([g for _,_,_,g in items]); y=np.concatenate([l for _,_,l,_ in items]); drop=[]
    for c in range(15):
        m=G[:,c]>0.5
        if m.sum()<10: drop.append(c); continue
        p=np.bincount(y[m],minlength=NC).astype(float); p/=p.sum(); p=p[p>0]
        if float(-(p*np.log2(p)).sum()/np.log2(NC))>THRESH: drop.append(c)
    return drop
def run(tr,te,drop):
    keep=[i for i in range(15) if i not in drop]
    Xtr=np.concatenate([x[:,keep] for _,x,_,_ in tr]); ytr=np.concatenate([l for _,_,l,_ in tr])
    sc=StandardScaler().fit(Xtr); clf=LogisticRegression(max_iter=1000).fit(sc.transform(Xtr),ytr)
    Aph,prior=fit_phase_hmm([(c,x,l) for c,x,l,_ in tr]); cls=list(clf.classes_)
    ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
    for cid,X,lab,_ in te:
        p=clf.predict_proba(sc.transform(X[:,keep])); full=np.zeros((len(X),NC)); full[:,cls]=p
        ev.update(phase_filter(full,Aph,prior).argmax(1),lab,cid)
    return ev.compute()
print(f"{'凍結源':34s} {'acc(全)':>8s} {'acc(除去)':>10s} {'Δacc':>8s} {'|m|/SE':>7s} {'mF1(全)':>8s} {'mF1(除去)':>10s} {'ΔmF1':>8s} {'|m|/SE':>7s} {'落とす数':>8s}")
res=[]
for tag in SRCS:
    D=build(tag); vids=sorted({c[0].split("_")[0] for c in D})
    r0={};r1={};nd=[]
    for vd in vids:
        tr=[c for c in D if c[0].split("_")[0]!=vd]; te=[c for c in D if c[0].split("_")[0]==vd]
        drop=he(tr); nd.append(len(drop))
        r0[vd]=run(tr,te,[]); r1[vd]=run(tr,te,drop)
    for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1")]:
        pass
    da=[r1[v]["phase_accuracy"]-r0[v]["phase_accuracy"] for v in vids]
    dm=[r1[v]["phase_macro_f1"]-r0[v]["phase_macro_f1"] for v in vids]
    sa=statistics.pstdev(da)/len(da)**0.5; sm=statistics.pstdev(dm)/len(dm)**0.5
    a0=statistics.mean([r0[v]["phase_accuracy"] for v in vids]); a1=statistics.mean([r1[v]["phase_accuracy"] for v in vids])
    m0=statistics.mean([r0[v]["phase_macro_f1"] for v in vids]); m1=statistics.mean([r1[v]["phase_macro_f1"] for v in vids])
    res.append((tag,statistics.mean(da),statistics.mean(dm)))
    print(f"{tag:34s} {a0:8.4f} {a1:10.4f} {statistics.mean(da):+8.4f} {abs(statistics.mean(da))/sa:7.2f} {m0:8.4f} {m1:10.4f} {statistics.mean(dm):+8.4f} {abs(statistics.mean(dm))/sm:7.2f} {statistics.mean(nd):8.1f}")
print(f"\n6 凍結源の Δacc: mean={statistics.mean([r[1] for r in res]):+.4f}  正={sum(1 for r in res if r[1]>0)}/6")
print(f"6 凍結源の ΔmF1: mean={statistics.mean([r[2] for r in res]):+.4f}  正={sum(1 for r in res if r[2]>0)}/6")

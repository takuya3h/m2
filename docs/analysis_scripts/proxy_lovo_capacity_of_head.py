"""per-frame 分類器の表現力を上げても「術具除去」の利得が残るかを確かめる（LOVO・プロキシ）。

線形（ロジスティック回帰）と MLP（隠れ層 64）で同じ比較をする。
TeCNO はもっと表現力が高いので、表現力を上げて利得が消えるなら本番でも消える可能性が高い。
"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
THRESH=0.45
def items(split):
    pr=load_sig(split,"pred"); orc=load_sig(split,"oracle")
    return [(cid,np.stack([pr[f] for f in frames]),lab,np.stack([orc[f] for f in frames])) for cid,frames,lab in clips(split)]
D=sum([items(sp) for sp in ["train","val","test"]],[])
vids=sorted({c[0].split("_")[0] for c in D})
def he(tr):
    G=np.concatenate([g for _,_,_,g in tr]); y=np.concatenate([l for _,_,l,_ in tr]); drop=[]
    for c in range(15):
        m=G[:,c]>0.5
        if m.sum()<10: drop.append(c); continue
        p=np.bincount(y[m],minlength=NC).astype(float); p/=p.sum(); p=p[p>0]
        if float(-(p*np.log2(p)).sum()/np.log2(NC))>THRESH: drop.append(c)
    return drop
def clf_of(kind, seed=0):
    if kind=="linear": return LogisticRegression(max_iter=1000)
    return MLPClassifier(hidden_layer_sizes=(64,), max_iter=300, random_state=seed, early_stopping=False)
def run(kind, tr, te, drop):
    keep=[i for i in range(15) if i not in drop]
    Xtr=np.concatenate([x[:,keep] for _,x,_,_ in tr]); ytr=np.concatenate([l for _,_,l,_ in tr])
    sc=StandardScaler().fit(Xtr); m=clf_of(kind).fit(sc.transform(Xtr),ytr)
    Aph,prior=fit_phase_hmm([(c,x,l) for c,x,l,_ in tr]); cls=list(m.classes_)
    ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
    for cid,X,lab,_ in te:
        p=m.predict_proba(sc.transform(X[:,keep])); full=np.zeros((len(X),NC)); full[:,cls]=p
        ev.update(phase_filter(full,Aph,prior).argmax(1),lab,cid)
    return ev.compute()
for kind in ["linear","mlp"]:
    r0={};r1={}
    for vd in vids:
        tr=[c for c in D if c[0].split("_")[0]!=vd]; te=[c for c in D if c[0].split("_")[0]==vd]
        drop=he(tr)
        r0[vd]=run(kind,tr,te,[]); r1[vd]=run(kind,tr,te,drop)
    for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1")]:
        d=[r1[v][key]-r0[v][key] for v in vids]; se=statistics.pstdev(d)/len(d)**0.5
        print(f"{kind:7s} {lbl:4s}: 全次元={statistics.mean([r0[v][key] for v in vids]):.4f} "
              f"除去後={statistics.mean([r1[v][key] for v in vids]):.4f} "
              f"Δ={statistics.mean(d):+.4f} |m|/SE={abs(statistics.mean(d))/se:5.2f} pos={sum(1 for x in d if x>0)}/{len(d)}")

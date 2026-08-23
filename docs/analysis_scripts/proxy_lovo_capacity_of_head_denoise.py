"""per-frame 分類器の表現力を上げても「因果デノイズ」の分節利得が残るかを確かめる（LOVO）。"""
src=open('docs/analysis_scripts/proxy_phase_presence_denoise.py').read().split('if __name__ == "__main__":')[0]
exec(src)
import numpy as np, statistics
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
A,E=fit_tool_hmm()
def items(split, den):
    pr=load_sig(split,"pred")
    out=[]
    for cid,frames,lab in clips(split):
        R=np.stack([pr[f] for f in frames])
        out.append((cid, tool_filter(R,A,E,2) if den else R, lab))
    return out
D={d: sum([items(sp,d) for sp in ["train","val","test"]],[]) for d in (False,True)}
vids=sorted({c[0].split("_")[0] for c in D[False]})
def clf_of(kind):
    return LogisticRegression(max_iter=1000) if kind=="linear" else MLPClassifier(hidden_layer_sizes=(64,),max_iter=300,random_state=0)
def run(kind, tr, te):
    Xtr=np.concatenate([x for _,x,_ in tr]); ytr=np.concatenate([l for _,_,l in tr])
    sc=StandardScaler().fit(Xtr); m=clf_of(kind).fit(sc.transform(Xtr),ytr)
    Aph,prior=fit_phase_hmm(tr); cls=list(m.classes_)
    ev=PhaseEvaluator(num_classes=NC,class_names=CLASS_NAMES)
    for cid,X,lab in te:
        p=m.predict_proba(sc.transform(X)); full=np.zeros((len(X),NC)); full[:,cls]=p
        ev.update(phase_filter(full,Aph,prior).argmax(1),lab,cid)
    return ev.compute()
for kind in ["linear","mlp"]:
    r={False:{},True:{}}
    for vd in vids:
        for den in (False,True):
            tr=[c for c in D[den] if c[0].split("_")[0]!=vd]; te=[c for c in D[den] if c[0].split("_")[0]==vd]
            r[den][vd]=run(kind,tr,te)
    for key,lbl in [("phase_accuracy","acc"),("phase_macro_f1","mF1"),("phase_edit_score","edit"),("phase_seg_f1_50","segF50")]:
        d=[r[True][v][key]-r[False][v][key] for v in vids]; se=statistics.pstdev(d)/len(d)**0.5
        print(f"{kind:7s} {lbl:7s}: 生={statistics.mean([r[False][v][key] for v in vids]):8.4f} "
              f"デノイズ={statistics.mean([r[True][v][key] for v in vids]):8.4f} "
              f"Δ={statistics.mean(d):+8.4f} |m|/SE={abs(statistics.mean(d))/se:5.2f} pos={sum(1 for x in d if x>0)}/{len(d)}")

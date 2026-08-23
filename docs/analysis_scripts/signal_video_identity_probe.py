"""信号がどれだけ「動画指紋」を持つかを測る線形 probe（CPU・読み取り専用）。

本研究の split は動画単位 hold-out なので、信号が動画 ID を強く符号化しているほど
未見動画への汎化を害する。GAP / region-token / 予測 presence / オラクル presence を比較する。

依存: numpy, scikit-learn
使い方: python docs/analysis_scripts/signal_video_identity_probe.py
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

FROZEN = "relation_detr_seed42"


def probe(X, y, name):
    Xa, Xb, ya, yb = train_test_split(X, y, test_size=0.3, random_state=0, stratify=y)
    sc = StandardScaler().fit(Xa)
    clf = LogisticRegression(max_iter=300).fit(sc.transform(Xa), ya)
    print(f"  {name:34s} dim={X.shape[1]:5d} clip-id acc={clf.score(sc.transform(Xb), yb):.4f}")


def main():
    gap = np.load(f"data/processed/stage1_features/{FROZEN}/train_gap.npz")
    fid = gap["frame_ids"]
    clip = np.array(["_".join(f.split("_")[:2]) for f in fid])
    print("clip-identity linear probe (chance = %.4f, %d clips)" % (1/len(set(clip)), len(set(clip))))
    probe(gap["features"], clip, "GAP 2048")

    rt = np.load(f"data/processed/t1a_regiontoken/{FROZEN}/train_regiontoken.npz")
    assert list(rt["frame_ids"]) == list(fid)
    probe(rt["region"].reshape(len(fid), -1), clip, "region-token 3840")

    pr = np.load(f"data/processed/b2a_detsignal/{FROZEN}/train_toolpresence.npz", allow_pickle=True)
    assert list(pr["frame_ids"]) == list(fid)
    probe(pr["signal"].astype(float), clip, "predicted tool presence 15")

    orc = np.load("data/processed/oracle_toolpresence/train_oracletool.npz", allow_pickle=True)
    assert list(orc["frame_ids"]) == list(fid)
    probe(orc["signal"].astype(float), clip, "ORACLE tool presence 15")


if __name__ == "__main__":
    main()

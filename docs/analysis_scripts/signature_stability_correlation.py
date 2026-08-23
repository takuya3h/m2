"""動画ごとの P(tool|phase) の「ずれ」が、その動画での det->phase 性能を説明するか。

各動画について、その動画の P(tool|phase) と 他 14 本の平均 との
Jensen-Shannon ダイバージェンス（術具を独立ベルヌーイとみなした平均, bit）を求め、
LOVO の per-video 性能と相関を取る。GPU 不要・読み取り専用。

前提: `docs/analysis_scripts/proxy_lovo_gap_vs_presence.py` の出力（per-video 行）を
標準入力かファイルで渡すか、同スクリプトを先に走らせてログを保存しておく。
"""
import numpy as np, json, re, sys

MD = "data/processed/phase_manifest"
NAMES = list(json.load(open(f"{MD}/phase_vocab.json")).keys())


def load_per_video():
    sig = {}
    for sp in ["train", "val", "test"]:
        d = np.load(f"data/processed/oracle_toolpresence/{sp}_oracletool.npz", allow_pickle=True)
        sig.update({str(f): v for f, v in zip(d["frame_ids"], d["signal"].astype(float))})
    pv = {}
    for sp in ["train", "val", "test"]:
        for c in json.load(open(f"{MD}/{sp}.json"))["clips"]:
            v = c["clip_id"].split("_")[0]
            pv.setdefault(v, {"X": [], "y": []})
            for fr in c["frames"]:
                pv[v]["X"].append(sig[fr["frame"]]); pv[v]["y"].append(fr["label"])
    for v in pv:
        pv[v]["X"] = np.array(pv[v]["X"]); pv[v]["y"] = np.array(pv[v]["y"])
    return pv


def cond(pv, vs):
    X = np.concatenate([pv[v]["X"] for v in vs]); y = np.concatenate([pv[v]["y"] for v in vs])
    return {p: (X[y == p].mean(0), int((y == p).sum())) for p in range(len(NAMES)) if (y == p).sum() > 0}


def js(p, q, dims, eps=1e-6):
    p = np.clip(p[dims], eps, 1 - eps); q = np.clip(q[dims], eps, 1 - eps); m = (p + q) / 2
    def kl(a, b): return a * np.log2(a / b) + (1 - a) * np.log2((1 - a) / (1 - b))
    return float(np.mean(0.5 * kl(p, m) + 0.5 * kl(q, m)))


UBIQ = [3, 5, 12, 14]           # Gauze / Mouth Gag / Suction Cannula / Tweezers（エントロピー上位）
SIG = [i for i in range(15) if i not in UBIQ]


def divergences(pv):
    """4 種類の「ずれ」指標を返す: 全術具 JS / signature 限定 JS / 欠落量 / 混入量。"""
    vids = sorted(pv); out = {k: {} for k in ("JS_all", "JS_sig", "missing_sig", "extra_sig")}
    for v in vids:
        ref = cond(pv, [u for u in vids if u != v]); own = cond(pv, [v])
        a, b, c, d, ws = [], [], [], [], []
        for p, (mu, n) in own.items():
            if p not in ref:
                continue
            ws.append(n)
            a.append(js(mu, ref[p][0], list(range(15))))
            b.append(js(mu, ref[p][0], SIG))
            r, o = ref[p][0][SIG], mu[SIG]
            c.append(float(np.mean(np.maximum(r - o, 0) * r)))          # 期待が高いのに低い
            d.append(float(np.mean(np.maximum(o - r, 0) * (1 - r))))    # 期待が低いのに高い
        for k, vals in zip(out, [a, b, c, d]):
            out[k][v] = float(np.average(vals, weights=ws))
    return out


def spearman(x, y):
    def rank(a):
        o = np.argsort(a); r = np.empty(len(a)); r[o] = np.arange(len(a)); return r
    return float(np.corrcoef(rank(np.array(x)), rank(np.array(y)))[0, 1])


def main(logpath):
    pv = load_per_video(); divs = divergences(pv)
    G = {}
    for line in open(logpath):
        m = re.match(r"^(\d\d) gap:([\d.]+) pres:([\d.]+) gap\+pres:([\d.]+) hmm2:([\d.]+)", line)
        if m:
            G[m.group(1)] = {"gap": float(m.group(2)), "pres": float(m.group(3)), "hmm2": float(m.group(5))}
    vs = [v for v in sorted(divs["JS_all"]) if v in G]
    print(f"{'video':6s} " + " ".join(f"{k:>12s}" for k in divs) + f" {'gap acc':>9s} {'pres acc':>9s}")
    for v in vs:
        print(f"{v:6s} " + " ".join(f"{divs[k][v]:12.4f}" for k in divs)
              + f" {G[v]['gap']:9.4f} {G[v]['pres']:9.4f}")
    print()
    for k in divs:
        x = [divs[k][v] for v in vs]
        for lab, y in [("presence 絶対 acc", [G[v]["pres"] for v in vs]),
                       ("Δ(presence − GAP)", [G[v]["pres"] - G[v]["gap"] for v in vs])]:
            print(f"  {k:12s} vs {lab:20s} Pearson r={np.corrcoef(x, y)[0,1]:+.3f}  "
                  f"Spearman rho={spearman(x, y):+.3f} (n={len(vs)})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "lovo_gap.log")

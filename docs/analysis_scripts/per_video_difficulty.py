"""動画ごとの難しさを分解する（LOVO の per-video 結果と、多数決ベースライン・動画長・工程分布）。

引数に `proxy_lovo_gap_vs_presence.py` のログを渡す。GPU 不要・読み取り専用。
"""
import numpy as np, json, collections, re, statistics, sys

MD = "data/processed/phase_manifest"
NAMES = list(json.load(open(f"{MD}/phase_vocab.json")).keys())


def per_video_labels():
    pv = {}
    for sp in ["train", "val", "test"]:
        for c in json.load(open(f"{MD}/{sp}.json"))["clips"]:
            v = c["clip_id"].split("_")[0]
            pv.setdefault(v, []).extend(fr["label"] for fr in c["frames"])
    return pv


def rank(a):
    o = np.argsort(a); r = np.empty(len(a)); r[o] = np.arange(len(a)); return r


def main(logpath):
    pv = per_video_labels(); vids = sorted(pv)
    A = {}
    for line in open(logpath):
        m = re.match(r"^(\d\d) gap:([\d.]+) pres:([\d.]+) gap\+pres:([\d.]+) hmm2:([\d.]+)", line)
        if m:
            A[m.group(1)] = {"gap": float(m.group(2)), "pres": float(m.group(3)), "hmm2": float(m.group(5))}
    print(f"{'vid':4s} {'frames':>7s} {'majority':>9s} {'GAP':>7s} {'presence':>9s} {'denoise':>8s} {'pres−maj':>9s}")
    gains, lens, majs = [], [], []
    for v in vids:
        c = collections.Counter(pv[v]); n = len(pv[v]); maj = c.most_common(1)[0][1] / n
        g = A[v]["pres"] - maj
        gains.append(g); lens.append(n); majs.append(maj)
        flag = "  <- majority 以下" if g < 0 else ""
        print(f"{v:4s} {n:7d} {maj:9.3f} {A[v]['gap']:7.3f} {A[v]['pres']:9.3f} {A[v]['hmm2']:8.3f} {g:+9.3f}{flag}")
    se = statistics.pstdev(gains) / len(gains) ** 0.5
    print(f"\npresence − majority: mean={statistics.mean(gains):+.4f} |m|/SE={abs(statistics.mean(gains))/se:.2f} "
          f"pos={sum(1 for x in gains if x > 0)}/{len(gains)}")
    acc = [A[v]["pres"] for v in vids]
    for lab, x in [("動画長", lens), ("多数決ベースライン", majs)]:
        print(f"{lab:20s} vs presence acc: Pearson r={np.corrcoef(x, acc)[0,1]:+.3f} "
              f"Spearman rho={np.corrcoef(rank(x), rank(acc))[0,1]:+.3f}")
    print(f"{'動画長':20s} vs (presence−majority): Pearson r={np.corrcoef(lens, gains)[0,1]:+.3f} "
          f"Spearman rho={np.corrcoef(rank(lens), rank(gains))[0,1]:+.3f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "lovo_gap.log")

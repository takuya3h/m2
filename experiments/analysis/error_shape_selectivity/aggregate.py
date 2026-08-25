"""掃引の生の値から選択性の表を作る。**判定は行わない。**

選択性 = |Δ分節指標| / |Δ分類指標(点)|
既存の記録（§3.10）と同じ定義である。iid p=0.05 は 18.45/3.02 = 6.1。

効果量と符号の個数は判定とは別に出す。既存の実装（proxy_lovo_noise_structure.py:56-61）
と同じ求め方にして比較できるようにする。

  動画ごとの Δ = （その動画の、種にわたる平均） − （クリーンの同じ動画）
  効果量        = |mean(Δ)| / (pstdev(Δ)/sqrt(n))
  符号の個数    = Δ < 0 の動画数 / 動画数

種ごとの散らばりは、**種ごとに独立に選択性を求めて**その標本標準偏差を取る。
平均だけでは、その点が安定かどうか分からない。
"""
import csv, math, statistics, sys
from collections import defaultdict
from pathlib import Path

ACC, EDIT = "phase_accuracy", "phase_edit_score"
MF1, SEGF = "phase_macro_f1", "phase_seg_f1_50"


def load(path):
    rows = list(csv.DictReader(Path(path).open(newline="", encoding="utf-8")))
    for r in rows:
        r["p"] = float(r["p"]); r["L"] = int(r["L"]); r["seed"] = int(r["seed"])
        r["err_rate_actual"] = float(r["err_rate_actual"]); r["mean_run_len"] = float(r["mean_run_len"])
        for k in (ACC, EDIT, MF1, SEGF):
            r[k] = float(r[k])
    return rows


def summarize(rows):
    clean = {r["vid"]: r for r in rows if r["p"] == 0.0}
    vids = sorted(clean)
    n = len(vids)
    noisy = [r for r in rows if r["p"] > 0.0]

    by_point = defaultdict(list)
    for r in noisy:
        by_point[(r["p"], r["L"])].append(r)

    out = []
    for (p, L), rs in sorted(by_point.items()):
        seeds = sorted({r["seed"] for r in rs})
        by_vs = {(r["vid"], r["seed"]): r for r in rs}
        rec = {"p": p, "L": L, "n_seeds": len(seeds), "n_vids": n,
               "err_rate_actual": statistics.mean([r["err_rate_actual"] for r in rs]),
               "mean_run_len": statistics.mean([r["mean_run_len"] for r in rs])}

        for key, tag in ((ACC, "acc"), (EDIT, "edit"), (MF1, "mF1"), (SEGF, "segF50")):
            d = []
            for v in vids:
                vals = [by_vs[(v, s)][key] for s in seeds if (v, s) in by_vs]
                if not vals: continue
                d.append(statistics.mean(vals) - clean[v][key])
            m = statistics.mean(d)
            se = statistics.pstdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
            rec[f"d_{tag}"] = m
            rec[f"se_{tag}"] = se
            rec[f"eff_{tag}"] = abs(m) / se if se else float("nan")
            rec[f"neg_{tag}"] = sum(1 for x in d if x < 0)

        # 選択性。分母は分類の指標の損失（点）。
        da_pt = abs(rec["d_acc"]) * 100
        rec["selectivity"] = abs(rec["d_edit"]) / da_pt if da_pt > 0 else float("nan")

        # 種ごとに独立に求めた選択性の散らばり
        per_seed = []
        for s in seeds:
            da = statistics.mean([by_vs[(v, s)][ACC] - clean[v][ACC] for v in vids if (v, s) in by_vs])
            de = statistics.mean([by_vs[(v, s)][EDIT] - clean[v][EDIT] for v in vids if (v, s) in by_vs])
            per_seed.append(abs(de) / (abs(da) * 100) if da else float("nan"))
        rec["sel_per_seed"] = per_seed
        good = [x for x in per_seed if not math.isnan(x)]
        rec["sel_sstd"] = statistics.stdev(good) if len(good) > 1 else float("nan")
        rec["sel_min"] = min(good) if good else float("nan")
        rec["sel_max"] = max(good) if good else float("nan")

        # 分母が零に近いか。振れているのか本当に大きいのかを区別するための材料。
        rec["denom_eff"] = rec["eff_acc"]          # |Δacc| / SE
        out.append(rec)
    return out, clean, vids


def main():
    rows = load(sys.argv[1])
    recs, clean, vids = summarize(rows)
    arm = rows[0]["arm"]
    print(f"# arm={arm}  動画={len(vids)}  クリーン acc={statistics.mean([clean[v][ACC] for v in vids]):.4f} "
          f"edit={statistics.mean([clean[v][EDIT] for v in vids]):.4f}")
    print()
    hdr = (f"{'p':>5} {'L':>4} {'実測誤り':>9} {'平均連長':>9} | {'Δacc':>9} {'|m|/SE':>7} {'neg':>6} | "
           f"{'Δedit':>9} {'|m|/SE':>7} {'neg':>6} | {'選択性':>8} {'種ごとsd':>9} {'最小':>7} {'最大':>7}")
    print(hdr); print("-" * len(hdr))
    for r in recs:
        print(f"{r['p']:>5} {r['L']:>4} {r['err_rate_actual']:>9.5f} {r['mean_run_len']:>9.2f} | "
              f"{r['d_acc']:>+9.4f} {r['eff_acc']:>7.2f} {r['neg_acc']:>3}/{r['n_vids']:<2} | "
              f"{r['d_edit']:>+9.4f} {r['eff_edit']:>7.2f} {r['neg_edit']:>3}/{r['n_vids']:<2} | "
              f"{r['selectivity']:>8.2f} {r['sel_sstd']:>9.2f} {r['sel_min']:>7.2f} {r['sel_max']:>7.2f}")

    out = Path(sys.argv[2])
    with out.open("w", newline="", encoding="utf-8") as fh:
        keys = [k for k in recs[0] if k != "sel_per_seed"]
        w = csv.writer(fh); w.writerow(keys + ["sel_per_seed"])
        for r in recs:
            w.writerow([r[k] for k in keys] + ["|".join(f"{x:.6f}" for x in r["sel_per_seed"])])
    print(f"\n書き出し: {out}")


if __name__ == "__main__":
    main()

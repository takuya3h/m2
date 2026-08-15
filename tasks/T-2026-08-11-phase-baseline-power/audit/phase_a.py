"""Phase A — 基準点の揺らぎを「種による分」と「同じ種でも再現しない分」に分ける。

**値だけを書かない。式の形で残す。** 使うのは釣り合わない一元配置の変量模型である。

    N   総本数、k 種の種類、n_i 各種の本数、x_ij 各 run の値
    x̄_i 種ごとの平均、x̄ 全体の平均

    群内平方和   SS_w = Σ_i Σ_j (x_ij − x̄_i)^2        自由度 df_w = N − k
    群間平方和   SS_b = Σ_i n_i (x̄_i − x̄)^2           自由度 df_b = k − 1
    平均平方     MS_w = SS_w / df_w,  MS_b = SS_b / df_b
    実効本数     n_0  = (N − Σ_i n_i^2 / N) / (k − 1)

    再現しない分 σ²_rep  = MS_w
    種による分   σ²_seed = max(0, (MS_b − MS_w) / n_0)

**σ²_seed に負が出たら 0 に丸める。** 分散は負にならないが、この推定量は
標本の揺れで負を取りうる。丸めたかどうかを記録する。

対にして取る差の揺らぎは、両側が同じ種を共有し再現しない分だけが独立に乗ると見て

    σ_d ≈ √2 · σ_rep

と見積もる。前契約の実測 0.003594 と突き合わせる。
"""

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
INDEX = ROOT / "runindex" / "index.csv"

EXPERIMENT_ID = "phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42"
METRIC = "metric.accuracy"
# 事前登録に記された索引の実測。抽出が正しければ再現するはずである。
PREREG_MEAN, PREREG_SD, PREREG_N = 0.8973015, 0.0059171, 17
# 前契約で実測された、対にして取る差の揺らぎ。
PRIOR_PAIRED_SD = 0.003594


def main() -> None:
    rows = [
        r
        for r in csv.DictReader(INDEX.open(encoding="utf-8"))
        if r["experiment_id"] == EXPERIMENT_ID
    ]

    # Step 3: 除外の印。**含めると揺らぎが実態より大きく出る。**
    excluded = [r for r in rows if (r.get("excluded") or "").strip().lower() == "true"]
    used = [r for r in rows if r not in excluded]
    exclusion_reasons = defaultdict(int)
    for r in excluded:
        exclusion_reasons[r.get("exclusion_reason") or "(理由なし)"] += 1

    # 種の列は 5 つある。実データで一致を確かめてから 1 つに決める。
    seed_cols = ["seed", "seed_config", "seed_command", "seed_phase", "seed_detector"]
    seed_col_state = {
        c: {"filled": sum(1 for r in used if (r.get(c) or "").strip()),
            "values": sorted({(r.get(c) or "").strip() for r in used if (r.get(c) or "").strip()})}
        for c in seed_cols
    }
    agree = all(
        (r.get("seed") or "").strip() == (r.get("seed_config") or "").strip() == (r.get("seed_command") or "").strip()
        for r in used
    )

    by_seed = defaultdict(list)
    for r in used:
        by_seed[(r.get("seed") or "").strip()].append(float(r[METRIC]))

    N = sum(len(v) for v in by_seed.values())
    k = len(by_seed)
    grand = sum(sum(v) for v in by_seed.values()) / N

    ss_w = sum((x - sum(v) / len(v)) ** 2 for v in by_seed.values() for x in v)
    ss_b = sum(len(v) * (sum(v) / len(v) - grand) ** 2 for v in by_seed.values())
    df_w, df_b = N - k, k - 1
    ms_w, ms_b = ss_w / df_w, ss_b / df_b
    n0 = (N - sum(len(v) ** 2 for v in by_seed.values()) / N) / (k - 1)

    var_rep = ms_w
    var_seed_raw = (ms_b - ms_w) / n0
    var_seed = max(0.0, var_seed_raw)
    sd_rep, sd_seed = math.sqrt(var_rep), math.sqrt(var_seed)

    # 抽出の裏取り。事前登録が引いた「17 run の標準偏差」を再現するか。
    # 規約 conventions#sigma の既定は series: pstd（母、ddof=0）である。
    # **正本は未決定と規約に明記されているため、両系統を記録する。**
    allvals = [x for v in by_seed.values() for x in v]
    ss_total = sum((x - grand) ** 2 for x in allvals)
    total_sd = math.sqrt(ss_total / (N - 1))   # sstd（標本、ddof=1）
    total_pstd = math.sqrt(ss_total / N)       # pstd（母、ddof=0）— 既定

    sd_paired_est = math.sqrt(2.0) * sd_rep

    result = {
        "experiment_id": EXPERIMENT_ID,
        "metric": METRIC,
        "counts": {
            "runs_total": len(rows),
            "excluded": len(excluded),
            "used": N,
            "seeds": k,
            "per_seed": {s: len(v) for s, v in sorted(by_seed.items())},
            "repeated_seed_groups": sum(1 for v in by_seed.values() if len(v) > 1),
        },
        "exclusion_reasons": dict(exclusion_reasons),
        "seed_column_state": seed_col_state,
        "seed_columns_agree": agree,
        "reproduction_check": {
            "mean_measured": grand,
            "mean_prereg": PREREG_MEAN,
            "sd_sstd_measured": total_sd,
            "sd_pstd_measured": total_pstd,
            "sd_prereg": PREREG_SD,
            "n_measured": N,
            "n_prereg": PREREG_N,
            "prereg_series": "pstd" if abs(total_pstd - PREREG_SD) < 1e-6 else (
                "sstd" if abs(total_sd - PREREG_SD) < 1e-6 else "どちらとも一致しない"),
            "matches": abs(grand - PREREG_MEAN) < 1e-6
            and min(abs(total_pstd - PREREG_SD), abs(total_sd - PREREG_SD)) < 1e-6,
        },
        "anova": {
            "N": N, "k": k, "df_within": df_w, "df_between": df_b,
            "SS_within": ss_w, "SS_between": ss_b,
            "MS_within": ms_w, "MS_between": ms_b,
            "n0": n0,
            "var_rep": var_rep,
            "var_seed_raw": var_seed_raw,
            "var_seed": var_seed,
            "clamped_to_zero": var_seed_raw < 0,
        },
        "sigma": {
            "sd_rep": sd_rep,
            "sd_seed": sd_seed,
            "sd_total_naive": total_sd,
            "ratio_rep_over_seed": (sd_rep / sd_seed) if sd_seed > 0 else None,
        },
        "prediction": {
            "statement": "同じ種を繰り返した揺らぎが、種を変えた揺らぎの半分より大きい",
            "threshold": sd_seed / 2 if sd_seed > 0 else 0.0,
            "holds": sd_rep > (sd_seed / 2) if sd_seed > 0 else True,
        },
        "paired": {
            "formula": "sd_d = sqrt(2) * sd_rep",
            "estimate": sd_paired_est,
            "prior_measured": PRIOR_PAIRED_SD,
            "ratio_estimate_over_prior": sd_paired_est / PRIOR_PAIRED_SD,
        },
        "per_seed_detail": {
            s: {
                "n": len(v),
                "mean": sum(v) / len(v),
                "sd": math.sqrt(sum((x - sum(v) / len(v)) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else None,
                "values": sorted(v),
            }
            for s, v in sorted(by_seed.items())
        },
        "confounds": {
            "hosts": sorted({r.get("host") or "" for r in used}),
            "host_counts": dict(sorted(
                ((h, sum(1 for r in used if (r.get("host") or "") == h))
                 for h in {r.get("host") or "" for r in used}))),
            "epoch_min": min(int(r["epoch"]) for r in used),
            "epoch_max": max(int(r["epoch"]) for r in used),
        },
        "duration_per_run": "UNKNOWN",
    }

    (AUDIT / "before.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    c, a, s = result["counts"], result["anova"], result["sigma"]
    print(f"記録: {AUDIT / 'before.json'}")
    print()
    print(f"基準点 {EXPERIMENT_ID}")
    print(f"  総本数 {c['runs_total']}  除外 {c['excluded']}  使う本数 {c['used']}  種 {c['seeds']}")
    print(f"  種ごとの本数 {c['per_seed']}   繰り返しのある組 {c['repeated_seed_groups']}")
    print(f"  ホスト {result['confounds']['host_counts']}  epoch {result['confounds']['epoch_min']}–{result['confounds']['epoch_max']}")
    print()
    r = result["reproduction_check"]
    print(f"抽出の裏取り: 平均 {r['mean_measured']:.7f}（事前登録 {r['mean_prereg']}）")
    print(f"  pstd={r['sd_pstd_measured']:.7f}  sstd={r['sd_sstd_measured']:.7f}"
          f"  事前登録={r['sd_prereg']} → 事前登録の系統は {r['prereg_series']}  一致={r['matches']}")
    print()
    print("分解（釣り合わない一元配置の変量模型）")
    print(f"  SS_w={a['SS_within']:.8f} df_w={a['df_within']}  MS_w={a['MS_within']:.8e}")
    print(f"  SS_b={a['SS_between']:.8f} df_b={a['df_between']}  MS_b={a['MS_between']:.8e}")
    print(f"  n_0={a['n0']:.4f}   0 へ丸めたか={a['clamped_to_zero']}")
    print(f"  再現しない分 σ_rep  = {s['sd_rep']:.7f}")
    print(f"  種による分   σ_seed = {s['sd_seed']:.7f}")
    print(f"  単純な全体   σ_total= {s['sd_total_naive']:.7f}")
    p = result["prediction"]
    print()
    print(f"事前登録の予測「σ_rep > σ_seed / 2」: 閾値 {p['threshold']:.7f} に対し σ_rep={s['sd_rep']:.7f} → {p['holds']}")
    q = result["paired"]
    print(f"対の差の揺らぎ 見積 {q['estimate']:.7f}（{q['formula']}） / 前契約の実測 {q['prior_measured']} "
          f"→ 比 {q['ratio_estimate_over_prior']:.3f}")
    print()
    print("一本あたりの所要時間: UNKNOWN（記録が存在しない。Phase C 冒頭で実測する）")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""S2: G-2 の統計手法を確定する（既存 per-frame 予測の再解析・学習不要）。

背景: 動画が val 2 本 / test 3 本しかなく、動画単位クラスタ・ブートストラップは
相異なる復元抽出多重集合が val 3 通り / test 10 通りしか存在しない。連続分布では
なく離散少数点にしかならず、percentile CI の端点が 0 に張り付く。

方針（確定事項）:
  (A) 動画ごとの結果を全部出す（seed 平均前の生の値も残す）
  (C) seed 水準の Welch を報告する
  ブートストラップは補足に降格し、限界を定量化して併記する。

Usage:
    python scripts/analysis/g2_stats_v2.py \
        --runs experiments/g2_main_2026-07-29_lecun --out experiments/g2_followup_2026-07-29
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from itertools import combinations_with_replacement, product
from pathlib import Path

import numpy as np
from scipy import stats

SYSTEMS = ["base", "bboxROI", "maskROI", "randROI"]
SEEDS = [42, 123, 456]
SPLITS = ["val", "test"]
CLASS_NAMES = ["anesthesia", "closure", "design", "disinfection", "dissection",
               "dressing", "hemostasis", "incision", "irrigation"]
PREREG_PHASES = ["incision", "hemostasis", "closure"]

# 系統番号は事前登録に合わせる: 1=base 2=bboxROI 3=maskROI 4=randROI
CONTRASTS = [
    ("2-1", "bboxROI", "base"),
    ("3-2", "maskROI", "bboxROI"),
    ("4-2", "randROI", "bboxROI"),
    ("3-1", "maskROI", "base"),
    ("4-1", "randROI", "base"),
]

B_BOOT = 2000
BOOT_SEED = 20260729


def video_of(clip_id: str) -> str:
    """clip_id ('04_1') -> 動画 id ('04')。事前登録のクラスタ単位は動画。"""
    return str(clip_id).split("_")[0]


# --------------------------------------------------------------------------- #
# counts（tp/fp/fn は動画をまたいで加算可能 -> 部分集合の指標を厳密に再構成できる）
# --------------------------------------------------------------------------- #
def counts_by_video(preds: list[dict]) -> dict:
    C = len(CLASS_NAMES)
    out: dict[str, dict] = {}
    for r in preds:
        v = video_of(r["clip_id"])
        c = out.setdefault(v, {"tp": np.zeros(C, np.int64), "fp": np.zeros(C, np.int64),
                               "fn": np.zeros(C, np.int64), "gt": np.zeros(C, np.int64),
                               "n_correct": 0, "n_frames": 0})
        g, p = int(r["gt"]), int(r["pred"])
        c["gt"][g] += 1
        c["n_frames"] += 1
        if p == g:
            c["tp"][g] += 1
            c["n_correct"] += 1
        else:
            c["fp"][p] += 1
            c["fn"][g] += 1
    return out


def sum_counts(by_vid: dict, vids: list[str]) -> tuple:
    C = len(CLASS_NAMES)
    tp = np.zeros(C, np.int64); fp = np.zeros(C, np.int64)
    fn = np.zeros(C, np.int64); gt = np.zeros(C, np.int64)
    nc = nf = 0
    for v in vids:
        c = by_vid[v]
        tp += c["tp"]; fp += c["fp"]; fn += c["fn"]; gt += c["gt"]
        nc += c["n_correct"]; nf += c["n_frames"]
    return tp, fp, fn, gt, nc, nf


def metrics_from(tp, fp, fn, gt, nc, nf) -> dict:
    """PhaseEvaluator._frame_f1 と同一定義（プール後に tp/fp/fn を数える）。"""
    C = len(CLASS_NAMES)
    f1 = np.zeros(C, np.float64)
    for c in range(C):
        if tp[c] == 0 or (tp[c] + fp[c]) == 0 or (tp[c] + fn[c]) == 0:
            continue
        pr = tp[c] / (tp[c] + fp[c]); rc = tp[c] / (tp[c] + fn[c])
        f1[c] = 2 * pr * rc / (pr + rc)
    present = gt > 0
    return {
        "phase_accuracy": float(nc / nf) if nf else 0.0,
        "phase_macro_f1": float(f1[present].mean()) if present.any() else 0.0,
        "n_frames": int(nf),
        **{c: float(f1[i]) for i, c in enumerate(CLASS_NAMES)},
        **{f"n_gt_{c}": int(gt[i]) for i, c in enumerate(CLASS_NAMES)},
    }


METRIC_KEYS = ["phase_accuracy", "phase_macro_f1"] + CLASS_NAMES


# --------------------------------------------------------------------------- #
def welch(a: np.ndarray, b: np.ndarray) -> dict:
    """事前登録の式。SE = sqrt(sdA^2/nA + sdB^2/nB)、Welch の df。"""
    na, nb = len(a), len(b)
    ma, mb = float(np.mean(a)), float(np.mean(b))
    va, vb = float(np.var(a, ddof=1)), float(np.var(b, ddof=1))
    se = math.sqrt(va / na + vb / nb)
    diff = ma - mb
    if se == 0.0:
        return {"mean_a": ma, "mean_b": mb, "sd_a": math.sqrt(va), "sd_b": math.sqrt(vb),
                "diff": diff, "se": 0.0, "df": None, "t": None, "p": None,
                "ci_low": None, "ci_high": None, "exceeds": bool(diff != 0.0),
                "note": "SE=0（両系統とも3seed完全一致）"}
    num = (va / na + vb / nb) ** 2
    den = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    df = num / den
    tcrit = float(stats.t.ppf(0.975, df))
    t = diff / se
    p = float(2 * stats.t.sf(abs(t), df))
    return {"mean_a": ma, "mean_b": mb, "sd_a": math.sqrt(va), "sd_b": math.sqrt(vb),
            "diff": diff, "se": se, "df": float(df), "t": float(t), "p": p,
            "ci_low": diff - tcrit * se, "ci_high": diff + tcrit * se,
            "t_crit": tcrit, "exceeds": bool(abs(diff) > tcrit * se)}


def bootstrap_supplement(packs: dict, sys_a: str, sys_b: str, vids: list[str],
                         key: str, rng: np.random.Generator) -> dict:
    """補足としてのみ残す動画単位クラスタ・ブートストラップ。"""
    nv = len(vids)

    def mean_over_seeds(system, chosen):
        vals = []
        for sd in SEEDS:
            m = metrics_from(*sum_counts(packs[(system, sd)], chosen))
            vals.append(m[key])
        return float(np.mean(vals))

    point = mean_over_seeds(sys_a, vids) - mean_over_seeds(sys_b, vids)
    boot = np.empty(B_BOOT)
    for b in range(B_BOOT):
        chosen = [vids[i] for i in rng.integers(0, nv, size=nv)]
        boot[b] = mean_over_seeds(sys_a, chosen) - mean_over_seeds(sys_b, chosen)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"point": float(point), "ci_low": float(lo), "ci_high": float(hi),
            "crosses_zero": bool(lo <= 0.0 <= hi),
            "n_distinct_resamples_realized": int(len(set(np.round(boot, 12))))}


def bootstrap_limits(vids: list[str], packs: dict, key: str,
                     sys_a: str, sys_b: str) -> dict:
    """S2-4: 復元抽出で生じる相異なる多重集合を **全列挙** し、確率と統計量を出す。"""
    n = len(vids)

    def mean_over_seeds(system, chosen):
        return float(np.mean([metrics_from(*sum_counts(packs[(system, sd)], chosen))[key]
                              for sd in SEEDS]))

    # 多重集合を全列挙（順序なし）。各多重集合の出現確率は多項係数 / n^n。
    rows = []
    for ms in combinations_with_replacement(range(n), n):
        chosen = [vids[i] for i in ms]
        cnt = [ms.count(i) for i in range(n)]
        # 多項係数 n! / prod(cnt!)
        ways = math.factorial(n)
        for c in cnt:
            ways //= math.factorial(c)
        rows.append({
            "multiset": "+".join(f"{vids[i]}x{cnt[i]}" for i in range(n) if cnt[i]),
            "counts": cnt, "n_orderings": ways, "prob": ways / (n ** n),
            "diff": mean_over_seeds(sys_a, chosen) - mean_over_seeds(sys_b, chosen),
        })
    total_orderings = sum(r["n_orderings"] for r in rows)
    assert total_orderings == n ** n, (total_orderings, n ** n)
    assert abs(sum(r["prob"] for r in rows) - 1.0) < 1e-12
    diffs = sorted(r["diff"] for r in rows)
    return {
        "n_videos": n, "video_ids": vids,
        "n_distinct_multisets": len(rows),
        "formula": "C(2n-1, n)",
        "n_distinct_multisets_formula": math.comb(2 * n - 1, n),
        "total_ordered_resamples": n ** n,
        "rows": rows,
        "distinct_diff_values": len(set(round(d, 12) for d in diffs)),
        "min_diff": diffs[0], "max_diff": diffs[-1],
        "note": ("percentile CI はこの少数の離散点の重み付き分位数にすぎない。"
                 "点が n^n=%d 通りの順序付き抽出を %d 個の多重集合に畳んだものなので、"
                 "2.5/97.5 パーセンタイルは最小・最大に張り付きやすい。"
                 % (n ** n, len(rows))),
    }


def sign_agreement(packs: dict, sys_a: str, sys_b: str, vids: list[str],
                   key: str) -> dict:
    """S2-3: 動画ごとに差の符号が一致するか（seed 平均後の per-video 差）。"""
    per_vid = {}
    for v in vids:
        da = float(np.mean([metrics_from(*sum_counts(packs[(sys_a, sd)], [v]))[key]
                            for sd in SEEDS]))
        db = float(np.mean([metrics_from(*sum_counts(packs[(sys_b, sd)], [v]))[key]
                            for sd in SEEDS]))
        per_vid[v] = da - db
    signs = [(1 if d > 0 else (-1 if d < 0 else 0)) for d in per_vid.values()]
    nz = [s for s in signs if s != 0]
    same = len(set(nz)) == 1 and len(nz) == len(signs)
    n = len(signs)
    # 帰無（符号が独立なコイン投げ）の下で「全 n 本が同符号」になる確率
    p_null = 2 * (0.5 ** n) if n > 0 else None
    return {"per_video_diff": per_vid, "n_videos": n,
            "n_positive": sum(1 for s in signs if s > 0),
            "n_negative": sum(1 for s in signs if s < 0),
            "n_zero": sum(1 for s in signs if s == 0),
            "all_same_sign": bool(same),
            "p_all_same_sign_under_null": p_null,
            "null_model": "各動画の差の符号が独立に等確率（効果ゼロ）と仮定したときの両側確率 2*(1/2)^n"}


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="G-2 本実験の $OUT（runs/ を含む）")
    ap.add_argument("--out", required=True, help="S2 の出力先")
    ap.add_argument("--skip-bootstrap", action="store_true")
    args = ap.parse_args()
    runs_root, out = Path(args.runs), Path(args.out)
    (out / "csv").mkdir(parents=True, exist_ok=True)
    (out / "json").mkdir(parents=True, exist_ok=True)

    report: dict = {"source_runs": str(runs_root), "systems": SYSTEMS, "seeds": SEEDS,
                    "cluster_unit": "video (clip_id の '_' 前)",
                    "method": {
                        "primary": "(A) 動画別の全結果 + (C) seed 水準 Welch",
                        "supplement": "動画単位クラスタ・ブートストラップ（限界を S2-4 で定量化）",
                        "primary_metric": "per-phase F1（overall は併記のみ）",
                    }, "splits": {}}

    per_video_rows: list[dict] = []
    contrast_rows: list[dict] = []

    for split in SPLITS:
        packs: dict = {}
        vids_ref = None
        for s in SYSTEMS:
            for sd in SEEDS:
                p = runs_root / "runs" / f"{s}_seed{sd}" / "predictions" / f"{split}_preds.json"
                by = counts_by_video(json.loads(p.read_text()))
                packs[(s, sd)] = by
                v = sorted(by)
                if vids_ref is None:
                    vids_ref = v
                elif v != vids_ref:
                    raise RuntimeError(f"動画集合が run 間で不一致: {s}_seed{sd} {v} != {vids_ref}")
        vids = vids_ref
        sp: dict = {"video_ids": vids, "n_videos": len(vids)}

        # --- S2-1: 動画別の全結果（seed 平均前の生値を残す） ---
        for s in SYSTEMS:
            for sd in SEEDS:
                for v in vids:
                    m = metrics_from(*sum_counts(packs[(s, sd)], [v]))
                    row = {"split": split, "system": s, "seed": sd, "video": v,
                           "n_frames": m["n_frames"],
                           "accuracy": m["phase_accuracy"], "macro_f1": m["phase_macro_f1"]}
                    row.update({f"f1_{c}": m[c] for c in CLASS_NAMES})
                    row.update({f"n_gt_{c}": m[f"n_gt_{c}"] for c in CLASS_NAMES})
                    per_video_rows.append(row)

        # --- seed 水準の系統別値（split 全体） ---
        sysvals = {s: {k: np.array([metrics_from(*sum_counts(packs[(s, sd)], vids))[k]
                                    for sd in SEEDS]) for k in METRIC_KEYS}
                   for s in SYSTEMS}
        sp["systems_mean_sd"] = {
            s: {k: {"n": len(SEEDS), "mean": float(v.mean()), "sd": float(v.std(ddof=1)),
                    "values": [float(x) for x in v]}
                for k, v in d.items()} for s, d in sysvals.items()}

        rng = np.random.default_rng(BOOT_SEED)
        sp["contrasts"] = {}
        for tag, a, b in CONTRASTS:
            c: dict = {"systems": [a, b], "metrics": {}}
            for k in METRIC_KEYS:
                w = welch(sysvals[a][k], sysvals[b][k])           # S2-2
                sg = sign_agreement(packs, a, b, vids, k)          # S2-3
                bt = (None if args.skip_bootstrap
                      else bootstrap_supplement(packs, a, b, vids, k, rng))
                c["metrics"][k] = {"welch": w, "sign": sg, "bootstrap_supplement": bt}
                contrast_rows.append({
                    "contrast": tag, "split": split, "metric": k,
                    "is_prereg_phase": k in PREREG_PHASES,
                    "diff": w["diff"], "mean_a": w["mean_a"], "mean_b": w["mean_b"],
                    "sd_A": w["sd_a"], "sd_B": w["sd_b"], "SE": w["se"],
                    "df": w["df"], "t": w.get("t"), "p": w.get("p"),
                    "CI_low": w["ci_low"], "CI_high": w["ci_high"],
                    "welch_exceeds": w["exceeds"],
                    "n_videos": sg["n_videos"],
                    "n_videos_same_sign": (sg["n_videos"] if sg["all_same_sign"]
                                           else max(sg["n_positive"], sg["n_negative"])),
                    "all_videos_same_sign": sg["all_same_sign"],
                    "p_sign_under_null": sg["p_all_same_sign_under_null"],
                    "bootstrap_CI_low": bt["ci_low"] if bt else None,
                    "bootstrap_CI_high": bt["ci_high"] if bt else None,
                    "bootstrap_crosses_zero": bt["crosses_zero"] if bt else None,
                })
            sp["contrasts"][tag] = c

        # --- S2-4: ブートストラップの限界を全列挙で定量化 ---
        sp["bootstrap_limits"] = {
            k: bootstrap_limits(vids, packs, k, "maskROI", "bboxROI")
            for k in ["phase_accuracy", "phase_macro_f1"]
        }
        report["splits"][split] = sp

    # --- S2-6: G-2 の判定が変わるか ---
    report["s2_6_verdict_change"] = verdict_change(report)

    # 出力
    json.dump(report, open(out / "json" / "s2_stats_v2.json", "w"), indent=2, ensure_ascii=False)
    _write_csv(out / "csv" / "s2_per_video.csv", per_video_rows)
    _write_csv(out / "csv" / "s2_contrasts_v2.csv", contrast_rows)
    print(f"-> {out/'json'/'s2_stats_v2.json'}")
    print(f"-> {out/'csv'/'s2_per_video.csv'} ({len(per_video_rows)} 行)")
    print(f"-> {out/'csv'/'s2_contrasts_v2.csv'} ({len(contrast_rows)} 行)")
    _print_summary(report)
    return 0


def verdict_change(report: dict) -> dict:
    """旧判定（Welch と ブートストラップの AND）と新判定（Welch 主・符号一致併記）の差。"""
    out = {}
    for split in SPLITS:
        for tag in ("2-1", "3-2", "4-2"):
            c = report["splits"][split]["contrasts"][tag]
            for k in PREREG_PHASES + ["phase_accuracy", "phase_macro_f1"]:
                e = c["metrics"][k]
                w, bt, sg = e["welch"], e["bootstrap_supplement"], e["sign"]
                old = bool(w["exceeds"] and bt and not bt["crosses_zero"])
                new = bool(w["exceeds"])
                if old != new:
                    out[f"{split}/{tag}/{k}"] = {
                        "diff": w["diff"], "old_AND_verdict": old, "new_welch_verdict": new,
                        "welch_p": w.get("p"),
                        "bootstrap_crossed_zero": bt["crosses_zero"] if bt else None,
                        "all_videos_same_sign": sg["all_same_sign"],
                    }
    return {"changed": out, "n_changed": len(out)}


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _print_summary(report: dict) -> None:
    for split in SPLITS:
        sp = report["splits"][split]
        print("\n" + "=" * 96)
        print(f" split={split}  動画 {sp['video_ids']} (n={sp['n_videos']})")
        print("=" * 96)
        lim = sp["bootstrap_limits"]["phase_accuracy"]
        print(f"  [S2-4] 相異なる多重集合 = {lim['n_distinct_multisets']} 通り "
              f"(C(2n-1,n)={lim['n_distinct_multisets_formula']}) / "
              f"順序付き抽出 n^n={lim['total_ordered_resamples']} 通り")
        for tag in ("2-1", "3-2", "4-2"):
            c = sp["contrasts"][tag]
            print(f"\n  [{tag}] {c['systems'][0]} - {c['systems'][1]}")
            print(f"    {'metric':16s} {'diff':>9s} {'SE':>8s} {'df':>6s} {'p':>8s} "
                  f"{'95%CI(Welch)':>22s} {'符号':>10s} {'boot(補足)':>22s}")
            for k in PREREG_PHASES + ["phase_accuracy", "phase_macro_f1"]:
                e = c["metrics"][k]; w, sg, bt = e["welch"], e["sign"], e["bootstrap_supplement"]
                ci = (f"[{w['ci_low']:+.4f},{w['ci_high']:+.4f}]" if w["ci_low"] is not None
                      else "n/a")
                bc = (f"[{bt['ci_low']:+.4f},{bt['ci_high']:+.4f}]" if bt else "n/a")
                sign = (f"{sg['n_videos']}/{sg['n_videos']}同符号"
                        if sg["all_same_sign"] else
                        f"+{sg['n_positive']}/-{sg['n_negative']}/0:{sg['n_zero']}")
                star = "*" if k in PREREG_PHASES else " "
                p = f"{w['p']:.4f}" if w.get("p") is not None else "n/a"
                df = f"{w['df']:.2f}" if w.get("df") is not None else "n/a"
                print(f"   {star}{k:15s} {w['diff']:+9.4f} {w['se']:8.5f} {df:>6s} {p:>8s} "
                      f"{ci:>22s} {sign:>10s} {bc:>22s}")
    ch = report["s2_6_verdict_change"]
    print("\n" + "=" * 96)
    print(f" [S2-6] 旧判定(Welch AND boot) と 新判定(Welch 主) で結論が変わる項目: {ch['n_changed']} 件")
    print("=" * 96)
    for k, v in ch["changed"].items():
        print(f"  {k}: diff={v['diff']:+.5f} 旧={v['old_AND_verdict']} -> 新={v['new_welch_verdict']} "
              f"(p={v['welch_p']:.4f}, boot が 0 を跨いだ={v['bootstrap_crossed_zero']}, "
              f"全動画同符号={v['all_videos_same_sign']})")


if __name__ == "__main__":
    raise SystemExit(main())

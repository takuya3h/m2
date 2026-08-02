#!/usr/bin/env python3
"""M2: 5 規則の val 安定性 → 規則の決定 → 分散分解 → 6 対比の判定。

事前登録 prereg/m2_prediction.md の手続きをそのまま実装する。

規則の決定は **val の情報のみ**で行う（§0.1）。test 指標は規則決定に一切使わず、
決定後の対比判定でのみ参照する。

Usage:
    python scripts/analysis/m2_report.py --out experiments/selection_noise_2026-07-29
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy import stats

SYSTEMS = ["base", "bboxROI", "maskROI", "randROI", "shuffleROI",
           "handROIbbox2", "handROImask2", "bboxROI_handROIbbox2"]
SEEDS = [42, 123, 456]
REPS = [1, 2, 3]
SPLITS = ["val", "test"]
RULES = ["R-acc", "R-last", "R-loss", "R-mf1", "R-topk"]
# 同点時の機構的優先順（事前登録で固定）
RULE_PRIORITY = ["R-loss", "R-mf1", "R-topk", "R-acc", "R-last"]

CLASS_NAMES = ["anesthesia", "closure", "design", "disinfection", "dissection",
               "dressing", "hemostasis", "incision", "irrigation"]
PREREG_PHASES = ["incision", "hemostasis", "closure"]
METRIC_KEYS = ["phase_accuracy", "phase_macro_f1"] + CLASS_NAMES

# 事前登録の 6 対比（系統番号 1=base 2=bboxROI 3=maskROI 4=randROI 5=shuffleROI
#                   7=handROIbbox2 8=handROImask2 9=bboxROI_handROIbbox2）
CONTRASTS = [
    ("2-1", "bboxROI", "base", "ROI チャネル追加"),
    ("3-2", "maskROI", "bboxROI", "術具マスク（背景除去）"),
    ("4-2", "randROI", "bboxROI", "形 vs 画素数"),
    ("5-1", "shuffleROI", "base", "次元の交絡（シャッフル対照）"),
    ("2-5", "bboxROI", "shuffleROI", "ROI 情報の正味の効果"),
    ("8-7", "handROImask2", "handROIbbox2", "手マスク"),
    ("9-2", "bboxROI_handROIbbox2", "bboxROI", "術具 ROI ＋ 手 ROI"),
]


def video_of(clip_id: str) -> str:
    return str(clip_id).split("_")[0]


# --------------------------------------------------------------------------- #
def counts_by_video(preds: list[dict], keep: set[str] | None = None) -> dict:
    C = len(CLASS_NAMES)
    out: dict[str, dict] = {}
    for r in preds:
        if keep is not None and r["basename"] not in keep:
            continue
        v = video_of(r["clip_id"])
        c = out.setdefault(v, {"tp": np.zeros(C, np.int64), "fp": np.zeros(C, np.int64),
                               "fn": np.zeros(C, np.int64), "gt": np.zeros(C, np.int64),
                               "nc": 0, "nf": 0})
        g, p = int(r["gt"]), int(r["pred"])
        c["gt"][g] += 1; c["nf"] += 1
        if p == g:
            c["tp"][g] += 1; c["nc"] += 1
        else:
            c["fp"][p] += 1; c["fn"][g] += 1
    return out


def agg(by: dict, vids: list[str]) -> dict:
    C = len(CLASS_NAMES)
    tp = np.zeros(C, np.int64); fp = np.zeros(C, np.int64)
    fn = np.zeros(C, np.int64); gt = np.zeros(C, np.int64)
    nc = nf = 0
    for v in vids:
        if v not in by:
            continue
        c = by[v]
        tp += c["tp"]; fp += c["fp"]; fn += c["fn"]; gt += c["gt"]
        nc += c["nc"]; nf += c["nf"]
    f1 = np.zeros(C, np.float64)
    for c in range(C):
        if tp[c] == 0 or (tp[c] + fp[c]) == 0 or (tp[c] + fn[c]) == 0:
            continue
        pr = tp[c] / (tp[c] + fp[c]); rc = tp[c] / (tp[c] + fn[c])
        f1[c] = 2 * pr * rc / (pr + rc)
    present = gt > 0
    out = {"phase_accuracy": float(nc / nf) if nf else 0.0,
           "phase_macro_f1": float(f1[present].mean()) if present.any() else 0.0,
           "n_frames": int(nf)}
    out.update({c: float(f1[i]) for i, c in enumerate(CLASS_NAMES)})
    return out


def welch(a: np.ndarray, b: np.ndarray) -> dict:
    na, nb = len(a), len(b)
    ma, mb = float(np.mean(a)), float(np.mean(b))
    va, vb = float(np.var(a, ddof=1)), float(np.var(b, ddof=1))
    se = math.sqrt(va / na + vb / nb)
    diff = ma - mb
    if se == 0.0:
        return {"n_a": na, "n_b": nb, "mean_a": ma, "mean_b": mb,
                "sd_a": math.sqrt(va), "sd_b": math.sqrt(vb), "diff": diff,
                "se": 0.0, "df": None, "t": None, "p": None,
                "ci_low": None, "ci_high": None, "exceeds": bool(diff != 0.0),
                "note": "SE=0"}
    num = (va / na + vb / nb) ** 2
    den = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    df = num / den
    tc = float(stats.t.ppf(0.975, df))
    t = diff / se
    return {"n_a": na, "n_b": nb, "mean_a": ma, "mean_b": mb,
            "sd_a": math.sqrt(va), "sd_b": math.sqrt(vb), "diff": diff, "se": se,
            "df": float(df), "t": float(t), "p": float(2 * stats.t.sf(abs(t), df)),
            "ci_low": diff - tc * se, "ci_high": diff + tc * se, "t_crit": tc,
            "exceeds": bool(abs(diff) > tc * se)}


def variance_decomposition(vals: dict) -> dict:
    """一元配置変量効果モデル。vals[seed] = [反復の値...]。

    var_within = MSW、var_between = (MSB - MSW)/n_rep、ICC = vb/(vb+vw)。
    var_between は負になり得る（seed 間分散が反復内分散より小さいとき）。
    その場合は 0 に切り上げるが、生の値も併記する（負値自体が情報である）。
    """
    groups = [np.asarray(v, dtype=float) for v in vals.values() if len(v) > 0]
    k = len(groups)
    if k < 2 or any(len(g) < 2 for g in groups):
        return {"error": "群が 2 未満、または反復が 2 未満"}
    n = len(groups[0])
    if any(len(g) != n for g in groups):
        return {"error": "群ごとの反復数が不揃い"}
    grand = np.concatenate(groups).mean()
    ssb = n * sum((g.mean() - grand) ** 2 for g in groups)
    ssw = sum(((g - g.mean()) ** 2).sum() for g in groups)
    msb = ssb / (k - 1)
    msw = ssw / (k * (n - 1))
    vb_raw = (msb - msw) / n
    vb = max(vb_raw, 0.0)
    icc = vb / (vb + msw) if (vb + msw) > 0 else None
    return {"k_seeds": k, "n_reps": n, "MSB": float(msb), "MSW": float(msw),
            "var_within_seed": float(msw), "var_between_seed_raw": float(vb_raw),
            "var_between_seed": float(vb),
            "var_between_clipped_to_zero": bool(vb_raw < 0),
            "ICC": None if icc is None else float(icc),
            "sd_within": float(math.sqrt(msw)),
            "sd_between": float(math.sqrt(vb)),
            "within_exceeds_between": bool(msw > vb)}


# --------------------------------------------------------------------------- #
def load_all(out: Path) -> dict:
    """runs/<system>_seed<S>_rep<R>/ を全部読む。"""
    data = {}
    for s in SYSTEMS:
        for sd in SEEDS:
            for rp in REPS:
                d = out / "runs" / f"{s}_seed{sd}_rep{rp}"
                mp = d / "metrics.json"
                if not mp.exists():
                    continue
                data[(s, sd, rp)] = {
                    "dir": d,
                    "metrics": json.loads(mp.read_text()),
                    "env": json.loads((d / "env.json").read_text()),
                    "history": json.loads((d / "val_history.json").read_text()),
                }
    return data


def mask_diff_frames(split: str) -> tuple[set[str], dict]:
    """handROImask2 の特徴が handROIbbox2 と一致しないフレーム集合（事前登録の定義）。"""
    F = Path("experiments/g2_followup_2026-07-29/s4/features")
    a = np.load(F / f"{split}_handROImask2.npz")
    b = np.load(F / f"{split}_handROIbbox2.npz")
    ra, rb = a["roi"], b["roi"]
    ia = [str(x) for x in a["frame_ids"]]
    ib = [str(x) for x in b["frame_ids"]]
    assert ia == ib, "frame_ids が不一致"
    ne = ~np.all(ra == rb, axis=1)
    keep = {f for f, d in zip(ia, ne) if d}
    return keep, {"n_frames_total": len(ia), "n_frames_mask_ne_bbox": int(ne.sum()),
                  "rate": float(ne.mean()),
                  "definition": "handROImask2 の特徴ベクトルが handROIbbox2 と一致しないフレーム"}


def sign_agreement(packs: dict, a: str, b: str, vids: list[str], key: str,
                   sel: list) -> dict:
    per = {}
    for v in vids:
        da = float(np.mean([agg(packs[(a, sd, rp)], [v])[key] for sd, rp in sel]))
        db = float(np.mean([agg(packs[(b, sd, rp)], [v])[key] for sd, rp in sel]))
        per[v] = da - db
    signs = [(1 if d > 0 else (-1 if d < 0 else 0)) for d in per.values()]
    nz = [s for s in signs if s != 0]
    n = len(signs)
    return {"per_video_diff": per, "n_videos": n,
            "n_positive": sum(1 for s in signs if s > 0),
            "n_negative": sum(1 for s in signs if s < 0),
            "n_zero": sum(1 for s in signs if s == 0),
            "all_same_sign": bool(len(set(nz)) == 1 and len(nz) == n),
            "p_all_same_sign_under_null": 2 * (0.5 ** n) if n else None}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    (out / "json").mkdir(parents=True, exist_ok=True)
    (out / "csv").mkdir(parents=True, exist_ok=True)

    data = load_all(out)
    rep: dict = {"n_runs": len(data), "expected": len(SYSTEMS) * len(SEEDS) * len(REPS)}

    # --- 妥当性 ---
    commits = {v["env"]["commit"] for v in data.values()}
    hosts = {v["env"]["host"] for v in data.values()}
    ext_bad = [k for k, v in data.items() if v["env"]["msdeformattn_extension_loaded"] is not True]
    no_hist = [k for k, v in data.items() if len(v["history"]["history"]) != v["metrics"]["epochs"]]
    rep["validation"] = {
        "commits": sorted(commits), "single_commit": len(commits) == 1,
        "hosts": sorted(hosts), "single_host": len(hosts) == 1,
        "runs_with_ext_not_true": [f"{a}_seed{b}_rep{c}" for a, b, c in ext_bad],
        "runs_missing_full_history": [f"{a}_seed{b}_rep{c}" for a, b, c in no_hist],
        "started_at_unique": len({v["env"]["started_at"] for v in data.values()}),
        "determinism_controls_enabled": sorted(
            {bool(v["env"].get("determinism_controls_enabled")) for v in data.values()}),
    }

    # --- M1 相当: 5 規則の val 安定性（val のみ。test 一切不使用） ---
    rule_stab = {}
    rows_rule = []
    for rule in RULES:
        # val_metric_sd: 同一 seed の反復間 sd（val accuracy 基準）を系統・seed で平均
        sds, spreads, esds = [], [], []
        for s in SYSTEMS:
            for sd in SEEDS:
                vs, eps = [], []
                for rp in REPS:
                    k = (s, sd, rp)
                    if k not in data:
                        continue
                    r = data[k]["metrics"]["rules"][rule]
                    vs.append(r["val"]["phase_accuracy"])
                    e = r["selected_epoch"]
                    eps.append(float(np.mean(e)) if isinstance(e, list) else float(e))
                if len(vs) >= 2:
                    sds.append(float(np.std(vs, ddof=1)))
                    spreads.append(float(max(eps) - min(eps)))
                    esds.append(float(np.std(eps, ddof=1)))
        rule_stab[rule] = {
            "n_seed_groups": len(sds),
            "val_metric_sd_mean": float(np.mean(sds)) if sds else None,
            "val_metric_sd_max": float(np.max(sds)) if sds else None,
            "epoch_spread_mean": float(np.mean(spreads)) if spreads else None,
            "epoch_sd_mean": float(np.mean(esds)) if esds else None,
            "note": "val accuracy 基準。分母は 系統 x seed の群数。test 指標は不使用",
        }
        rows_rule.append({"rule": rule, "n_seed_groups": len(sds),
                          "val_metric_sd_mean": rule_stab[rule]["val_metric_sd_mean"],
                          "val_metric_sd_max": rule_stab[rule]["val_metric_sd_max"],
                          "epoch_spread_mean": rule_stab[rule]["epoch_spread_mean"],
                          "epoch_sd_mean": rule_stab[rule]["epoch_sd_mean"]})
    # 採用規則: val_metric_sd_mean 最小。同点(1e-6未満)なら事前固定の優先順
    cand = [(v["val_metric_sd_mean"], r) for r, v in rule_stab.items()
            if v["val_metric_sd_mean"] is not None]
    mn = min(c[0] for c in cand)
    tied = [r for v, r in cand if abs(v - mn) < 1e-6]
    chosen = min(tied, key=lambda r: RULE_PRIORITY.index(r))
    rep["rule_selection"] = {
        "stability": rule_stab, "min_val_metric_sd": mn, "tied_rules": tied,
        "chosen_rule": chosen,
        "tie_break_used": len(tied) > 1,
        "priority_order": RULE_PRIORITY,
        "note": "規則決定に test 指標は一切使用していない（§0.1）",
    }

    # --- val 曲線の平坦さ（M1-2 相当。val のみ） ---
    rows_flat = []
    for metric, key, better in [("val_accuracy", "val_accuracy", "max"),
                                ("val_loss", "val_loss", "min"),
                                ("val_macro_f1", "val_macro_f1", "max")]:
        g12, nnear, sdlat = [], [], []
        for v in data.values():
            h = v["history"]["history"]
            arr = np.array([e[key] for e in h], dtype=float)
            s = np.sort(arr)[::-1] if better == "max" else np.sort(arr)
            g12.append(abs(float(s[0] - s[1])))
            opt = arr.max() if better == "max" else arr.min()
            nnear.append(int((np.abs(arr - opt) <= 0.001).sum()))
            sdlat.append(float(arr[len(arr) // 2:].std(ddof=1)))
        rows_flat.append({"metric": metric, "n_runs": len(g12),
                          "top1_top2_gap_mean": float(np.mean(g12)),
                          "top1_top2_gap_median": float(np.median(g12)),
                          "n_near_optimal_pm0.001_mean": float(np.mean(nnear)),
                          "sd_latter_half_mean": float(np.mean(sdlat))})
    rep["val_curve_flatness"] = rows_flat

    # --- M2-4: 分散分解（規則ごと。R-acc = 適用前、chosen = 適用後） ---
    vd = {}
    for rule in RULES:
        vd[rule] = {}
        for split in SPLITS:
            vd[rule][split] = {}
            for key in ["phase_accuracy", "phase_macro_f1"]:
                per_sys = {}
                for s in SYSTEMS:
                    vals = {sd: [data[(s, sd, rp)]["metrics"]["rules"][rule][split][key]
                                 for rp in REPS if (s, sd, rp) in data] for sd in SEEDS}
                    per_sys[s] = variance_decomposition(vals)
                iccs = [v["ICC"] for v in per_sys.values() if v.get("ICC") is not None]
                nwx = sum(1 for v in per_sys.values() if v.get("within_exceeds_between"))
                vd[rule][split][key] = {
                    "per_system": per_sys,
                    "ICC_mean": float(np.mean(iccs)) if iccs else None,
                    "n_systems_within_exceeds_between": nwx,
                    "n_systems": len(per_sys),
                }
    rep["variance_decomposition"] = vd

    # --- M2-5: 6 対比の判定（採用規則で。n=9） ---
    sel = [(sd, rp) for sd in SEEDS for rp in REPS]
    maskinfo = {}
    contrasts: dict = {}
    for split in SPLITS:
        packs, vref = {}, None
        for s in SYSTEMS:
            for sd, rp in sel:
                p = (out / "runs" / f"{s}_seed{sd}_rep{rp}" / "predictions" / chosen
                     / f"{split}_preds.json")
                by = counts_by_video(json.loads(p.read_text()))
                packs[(s, sd, rp)] = by
                v = sorted(by)
                if vref is None:
                    vref = v
                assert v == vref, f"動画集合が不一致: {s}_seed{sd}_rep{rp}"
        vids = vref
        keep, minfo = mask_diff_frames(split)
        maskinfo[split] = minfo
        packs_sub = {}
        for s in ("handROImask2", "handROIbbox2"):
            for sd, rp in sel:
                p = (out / "runs" / f"{s}_seed{sd}_rep{rp}" / "predictions" / chosen
                     / f"{split}_preds.json")
                packs_sub[(s, sd, rp)] = counts_by_video(json.loads(p.read_text()), keep)

        contrasts[split] = {"video_ids": vids, "n_runs_per_system": len(sel), "items": {}}
        for tag, a, b, desc in CONTRASTS:
            item = {"systems": [a, b], "desc": desc, "metrics": {}}
            for key in METRIC_KEYS:
                av = np.array([agg(packs[(a, sd, rp)], vids)[key] for sd, rp in sel])
                bv = np.array([agg(packs[(b, sd, rp)], vids)[key] for sd, rp in sel])
                item["metrics"][key] = {"welch": welch(av, bv),
                                        "sign": sign_agreement(packs, a, b, vids, key, sel)}
            if tag == "8-7":
                item["mask_ne_bbox_subset"] = {"info": minfo, "metrics": {}}
                for key in METRIC_KEYS:
                    av = np.array([agg(packs_sub[(a, sd, rp)], vids)[key] for sd, rp in sel])
                    bv = np.array([agg(packs_sub[(b, sd, rp)], vids)[key] for sd, rp in sel])
                    item["mask_ne_bbox_subset"]["metrics"][key] = {
                        "welch": welch(av, bv),
                        "sign": sign_agreement(packs_sub, a, b, vids, key, sel)}
            contrasts[split]["items"][tag] = item
    rep["mask_subset_info"] = maskinfo
    rep["contrasts"] = contrasts

    # --- 出力 ---
    (out / "json" / "m2_report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    _csv(out / "csv" / "m2_rule_stability.csv", rows_rule)
    _csv(out / "csv" / "m2_epoch_flatness.csv", rows_flat)
    _write_contrast_csv(out / "csv" / "m2_contrasts.csv", rep, chosen)
    _write_vd_csv(out / "csv" / "m2_variance.csv", rep)
    _print(rep, chosen)
    return 0


def _csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def _write_contrast_csv(path: Path, rep: dict, chosen: str) -> None:
    rows = []
    for split, sp in rep["contrasts"].items():
        for tag, it in sp["items"].items():
            for scope, blk in [("all_frames", it["metrics"])] + (
                    [("mask_ne_bbox", it["mask_ne_bbox_subset"]["metrics"])]
                    if "mask_ne_bbox_subset" in it else []):
                for key, e in blk.items():
                    w, s = e["welch"], e["sign"]
                    rows.append({
                        "rule": chosen, "contrast": tag, "split": split, "scope": scope,
                        "metric": key, "is_prereg_phase": key in PREREG_PHASES,
                        "n_a": w["n_a"], "n_b": w["n_b"],
                        "mean_a": w["mean_a"], "mean_b": w["mean_b"],
                        "sd_A": w["sd_a"], "sd_B": w["sd_b"], "diff": w["diff"],
                        "SE": w["se"], "df": w["df"], "t": w.get("t"), "p": w.get("p"),
                        "CI_low": w["ci_low"], "CI_high": w["ci_high"],
                        "welch_exceeds": w["exceeds"],
                        "n_videos": s["n_videos"], "all_videos_same_sign": s["all_same_sign"],
                        "p_sign_under_null": s["p_all_same_sign_under_null"]})
    _csv(path, rows)


def _write_vd_csv(path: Path, rep: dict) -> None:
    rows = []
    for rule, per_split in rep["variance_decomposition"].items():
        for split, per_key in per_split.items():
            for key, blk in per_key.items():
                for s, v in blk["per_system"].items():
                    if "error" in v:
                        continue
                    rows.append({"rule": rule, "split": split, "metric": key, "system": s,
                                 "k_seeds": v["k_seeds"], "n_reps": v["n_reps"],
                                 "var_within_seed": v["var_within_seed"],
                                 "var_between_seed": v["var_between_seed"],
                                 "var_between_seed_raw": v["var_between_seed_raw"],
                                 "clipped_to_zero": v["var_between_clipped_to_zero"],
                                 "ICC": v["ICC"], "sd_within": v["sd_within"],
                                 "sd_between": v["sd_between"],
                                 "within_exceeds_between": v["within_exceeds_between"]})
    _csv(path, rows)


def _print(rep: dict, chosen: str) -> None:
    v = rep["validation"]
    print("=" * 100)
    print(f" M2 レポート   runs={rep['n_runs']}/{rep['expected']}")
    print("=" * 100)
    print(f"  commit: {v['commits']} 単一={v['single_commit']}   host: {v['hosts']} 単一={v['single_host']}")
    print(f"  拡張 False: {v['runs_with_ext_not_true'] or 'なし'}   "
          f"履歴欠落: {v['runs_missing_full_history'] or 'なし'}   "
          f"started_at ユニーク: {v['started_at_unique']}")
    print(f"  決定性制御: {v['determinism_controls_enabled']}（事前登録どおり無効）")

    print("\n" + "=" * 100)
    print(" 規則の val 安定性（val のみ。test 不使用）")
    print("=" * 100)
    print(f"  {'rule':8s} {'val_metric_sd(mean)':>20s} {'(max)':>10s} {'epoch_spread':>13s} {'epoch_sd':>9s}")
    for r, s in rep["rule_selection"]["stability"].items():
        mk = " ★" if r == chosen else ""
        print(f"  {r:8s} {s['val_metric_sd_mean']:20.6f} {s['val_metric_sd_max']:10.6f} "
              f"{s['epoch_spread_mean']:13.2f} {s['epoch_sd_mean']:9.2f}{mk}")
    rs = rep["rule_selection"]
    print(f"  -> 採用: {chosen}（最小 val_metric_sd={rs['min_val_metric_sd']:.6f}, "
          f"同点={rs['tied_rules']}, 優先順使用={rs['tie_break_used']}）")
    base = rep["rule_selection"]["stability"]["R-acc"]["val_metric_sd_mean"]
    ch = rep["rule_selection"]["stability"][chosen]["val_metric_sd_mean"]
    print(f"  -> R-acc 比: {ch/base:.3f}  判定: "
          f"{'RULE_FOUND（R-acc の半分以下）' if ch <= base/2 else 'RULE_INEFFECTIVE 相当（半分以下でない）'}")

    print("\n" + "=" * 100)
    print(" val 曲線の平坦さ（M1-2 相当）")
    print("=" * 100)
    print(f"  {'metric':16s} {'top1-top2 gap(mean)':>20s} {'(median)':>10s} "
          f"{'±0.001内epoch数':>16s} {'後半sd':>10s}")
    for r in rep["val_curve_flatness"]:
        print(f"  {r['metric']:16s} {r['top1_top2_gap_mean']:20.6f} "
              f"{r['top1_top2_gap_median']:10.6f} {r['n_near_optimal_pm0.001_mean']:16.2f} "
              f"{r['sd_latter_half_mean']:10.6f}")

    print("\n" + "=" * 100)
    print(" 分散分解: R-acc（適用前）vs " + chosen + "（適用後）  同一 72 run から算出")
    print("=" * 100)
    for split in SPLITS:
        for key in ["phase_accuracy", "phase_macro_f1"]:
            a = rep["variance_decomposition"]["R-acc"][split][key]
            b = rep["variance_decomposition"][chosen][split][key]
            print(f"  {split:4s} {key:16s} ICC: R-acc={a['ICC_mean']:.4f} -> "
                  f"{chosen}={b['ICC_mean']:.4f}   "
                  f"within>between の系統数: {a['n_systems_within_exceeds_between']}/{a['n_systems']}"
                  f" -> {b['n_systems_within_exceeds_between']}/{b['n_systems']}")

    print("\n" + "=" * 100)
    print(f" 6 対比の判定（規則 {chosen}、n=9 = 3 seed x 3 反復）")
    print("=" * 100)
    for split in SPLITS:
        sp = rep["contrasts"][split]
        print(f"\n  --- split={split}  動画 {sp['video_ids']} ---")
        for tag, it in sp["items"].items():
            print(f"\n  [{tag}] {it['systems'][0]} - {it['systems'][1]}  ({it['desc']})")
            print(f"    {'metric':16s} {'diff':>9s} {'SE':>8s} {'df':>6s} {'p':>8s} "
                  f"{'95%CI':>22s} {'符号':>12s} {'判定':>6s}")
            for key in PREREG_PHASES + ["phase_accuracy", "phase_macro_f1"]:
                e = it["metrics"][key]; w, s = e["welch"], e["sign"]
                ci = (f"[{w['ci_low']:+.4f},{w['ci_high']:+.4f}]"
                      if w["ci_low"] is not None else "n/a")
                sign = (f"{s['n_videos']}/{s['n_videos']}同符号" if s["all_same_sign"]
                        else f"+{s['n_positive']}/-{s['n_negative']}/0:{s['n_zero']}")
                p = f"{w['p']:.4f}" if w.get("p") is not None else "n/a"
                df = f"{w['df']:.2f}" if w.get("df") is not None else "n/a"
                st = "*" if key in PREREG_PHASES else " "
                print(f"   {st}{key:15s} {w['diff']:+9.4f} {w['se']:8.5f} {df:>6s} {p:>8s} "
                      f"{ci:>22s} {sign:>12s} {'超過' if w['exceeds'] else '-':>6s}")
            if "mask_ne_bbox_subset" in it:
                mi = it["mask_ne_bbox_subset"]["info"]
                print(f"    --- mask≠bbox 部分集合（主判定）: "
                      f"{mi['n_frames_mask_ne_bbox']}/{mi['n_frames_total']} "
                      f"({mi['rate']:.4f}） ---")
                for key in PREREG_PHASES + ["phase_accuracy", "phase_macro_f1"]:
                    e = it["mask_ne_bbox_subset"]["metrics"][key]
                    w, s = e["welch"], e["sign"]
                    ci = (f"[{w['ci_low']:+.4f},{w['ci_high']:+.4f}]"
                          if w["ci_low"] is not None else "n/a")
                    sign = (f"{s['n_videos']}/{s['n_videos']}同符号" if s["all_same_sign"]
                            else f"+{s['n_positive']}/-{s['n_negative']}/0:{s['n_zero']}")
                    p = f"{w['p']:.4f}" if w.get("p") is not None else "n/a"
                    st = "*" if key in PREREG_PHASES else " "
                    print(f"   {st}{key:15s} {w['diff']:+9.4f} {w['se']:8.5f} "
                          f"{'':>6s} {p:>8s} {ci:>22s} {sign:>12s} "
                          f"{'超過' if w['exceeds'] else '-':>6s}")


if __name__ == "__main__":
    raise SystemExit(main())

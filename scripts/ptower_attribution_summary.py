"""Aggregate the per-tower outputs of ptower_attribution.py (CPU only).

Full per-frame and per-box tables stay in ``OUT``; small tables and summary.json go to
``experiments/analysis/ptower_attribution``. CSV is UTF-8 with BOM.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import ptower_attribution as pa  # noqa: E402

SHUFFLE_SEED = 20261005
EXISTING = Path("/home/ubuntu/local/phase_cam_dlsta_20261003/outputs/bulk_analysis")
CHAINS = tuple(pa.HEADS)
FOUR = ("tool_only", "hand_only", "both", "outside")
GROUPS = ("target_tools", "negative_tools", "other_tools", "hands")
OVERLAP_LIMIT = 0.05


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = list(dict.fromkeys(k for row in rows for k in row))
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def derangement(n, rng):
    """A permutation without fixed points (the box-shuffle control)."""
    if n < 2:
        raise ValueError("need two frames to shuffle")
    while True:
        p = rng.permutation(n)
        if not (p == np.arange(n)).any():
            return p


def frame_masks(boxes):
    m = pa.region_masks(boxes)
    tool = m["tool_only"] | m["both"]
    hand = m["hand_only"] | m["both"]
    other = pa.box_mask(boxes, lambda b: b["kind"] == "tool"
                        and b["category"] not in pa.TARGET_GROUP + pa.NEGATIVE_GROUP)
    return {**{k: m[k] for k in FOUR}, "tool": tool, "hand": hand,
            "target_tools": m["target_tools"], "negative_tools": m["negative_tools"],
            "other_tools": other, "hands": hand}


def analyse_frame(job):
    """Contribution shares of one frame's maps (both classes), own and shuffled boxes."""
    cams, boxes, other_boxes = job
    own, other = frame_masks(boxes), frame_masks(other_boxes)
    result = []
    for cam in cams:
        field = pa.upsample(cam)
        total = float(field.sum())
        s = pa.shares(field, own)
        sh = pa.shares(field, other)
        py, px = np.unravel_index(cam.argmax(), cam.shape)
        peak_x, peak_y = (px + .5) * pa.WIDTH / cam.shape[1], (py + .5) * pa.HEIGHT / cam.shape[0]
        per_box = []
        for b in boxes:
            area = b["w"] * b["h"] / (pa.WIDTH * pa.HEIGHT)
            mass = float(field[b["y"]:b["y"] + b["h"], b["x"]:b["x"] + b["w"]].sum() / total) if total else 0.0
            per_box.append({"id": b["id"], "category": b["category"], "kind": b["kind"],
                            "area": area, "mass": mass, "density": mass / area,
                            "peak_inside": bool(total and b["x"] <= peak_x < b["x"] + b["w"]
                                                and b["y"] <= peak_y < b["y"] + b["h"])})
        result.append({"total": total, "raw_max": float(cam.max()), "own": s, "shuffled": sh,
                       "areas": {k: float(v.mean()) for k, v in own.items()},
                       "peak_tool": bool(total and own["tool"][int(peak_y), int(peak_x)]),
                       "peak_hand": bool(total and own["hand"][int(peak_y), int(peak_x)]),
                       "boxes": per_box})
    return result


def load_towers():
    plan = pa.target_folds()
    data = {}
    for video, fold in sorted(plan.items()):
        for chain in CHAINS:
            data[(chain, video)] = dict(np.load(pa.OUT / "towers" / f"{fold}_{chain}" / f"{video}.npz"))
    return plan, data


def stats(values):
    v = np.asarray(values, dtype=float)
    return {"n": int(v.size), "mean": float(v.mean()) if v.size else None}


def section_c(plan, data, boxes, names):
    frame_rows, box_rows = [], []
    for video in sorted(plan):
        ids = [str(x) for x in data[(CHAINS[0], video)]["frame_ids"]]
        perm = derangement(len(ids), np.random.default_rng(SHUFFLE_SEED + int(video)))
        for chain in CHAINS:
            d = data[(chain, video)]
            jobs = [(d["cam"][i], boxes[ids[i]], boxes[ids[perm[i]]]) for i in range(len(ids))]
            with Pool(24) as pool:
                out = pool.map(analyse_frame, jobs, chunksize=8)
            for i, per_class in enumerate(out):
                for j, r in enumerate(per_class):
                    cls = int(d["pred"][i]) if j == 0 else int(d["labels"][i])
                    row = {"chain": chain, "video": video, "fold": plan[video], "frame": ids[i],
                           "target": ("pred", "gt")[j], "class": names[cls],
                           "truth": names[int(d["labels"][i])], "prediction": names[int(d["pred"][i])],
                           "correct": int(d["pred"][i] == d["labels"][i]),
                           "raw_max": r["raw_max"], "raw_sum": r["total"],
                           "peak_tool": int(r["peak_tool"]), "peak_hand": int(r["peak_hand"]),
                           "shuffled_frame": ids[perm[i]]}
                    for k in FOUR + GROUPS + ("tool", "hand"):
                        row[f"share_{k}"] = r["own"][k]
                        row[f"area_{k}"] = r["areas"][k]
                        row[f"shuffled_share_{k}"] = r["shuffled"][k]
                    frame_rows.append(row)
                    for b in r["boxes"]:
                        box_rows.append({"chain": chain, "video": video, "frame": ids[i],
                                         "target": row["target"], "correct": row["correct"], **b})
            print(f"C {chain} {video}: {len(ids)} frames", flush=True)
    return frame_rows, box_rows


def group_of(b):
    if b["kind"] == "hand":
        return "hands"
    if b["category"] in pa.TARGET_GROUP:
        return "target_tools"
    if b["category"] in pa.NEGATIVE_GROUP:
        return "negative_tools"
    return "other_tools"


def summarize_c(frame_rows, box_rows):
    tables = {}
    rows = []
    for chain in CHAINS:
        for target in ("pred", "gt"):
            for video in sorted({r["video"] for r in frame_rows}) + ["all"]:
                fr = [r for r in frame_rows if r["chain"] == chain and r["target"] == target
                      and (video == "all" or r["video"] == video)]
                row = {"chain": chain, "target": target, "video": video, "n_frames": len(fr)}
                for k in FOUR + ("tool", "hand"):
                    row[f"share_{k}"] = float(np.mean([r[f"share_{k}"] for r in fr]))
                    row[f"shuffled_{k}"] = float(np.mean([r[f"shuffled_share_{k}"] for r in fr]))
                    row[f"area_{k}"] = float(np.mean([r[f"area_{k}"] for r in fr]))
                row["four_sum_max_abs_err"] = float(max(abs(sum(r[f"share_{k}"] for k in FOUR) - 1)
                                                        for r in fr if r["raw_sum"] > 0))
                row["peak_tool_rate"] = float(np.mean([r["peak_tool"] for r in fr]))
                row["peak_hand_rate"] = float(np.mean([r["peak_hand"] for r in fr]))
                row["no_positive_map"] = sum(r["raw_sum"] == 0 for r in fr)
                rows.append(row)
    tables["c_regions"] = rows
    rows = []
    for chain in CHAINS:
        for target in ("pred", "gt"):
            for group in GROUPS:
                bs = [b for b in box_rows if b["chain"] == chain and b["target"] == target
                      and group_of(b) == group]
                fr = [r for r in frame_rows if r["chain"] == chain and r["target"] == target
                      and r[f"area_{group}"] > 0]
                rows.append({"chain": chain, "target": target, "group": group, "n_boxes": len(bs),
                             "box_mass_mean": float(np.mean([b["mass"] for b in bs])) if bs else None,
                             "box_density_mean": float(np.mean([b["density"] for b in bs])) if bs else None,
                             "box_density_median": float(np.median([b["density"] for b in bs])) if bs else None,
                             "peak_inside_rate": float(np.mean([b["peak_inside"] for b in bs])) if bs else None,
                             "n_frames_present": len(fr),
                             "frame_union_share_mean": float(np.mean([r[f"share_{group}"] for r in fr])) if fr else None,
                             "frame_union_shuffled_mean": float(np.mean([r[f"shuffled_share_{group}"] for r in fr])) if fr else None,
                             "frame_union_area_mean": float(np.mean([r[f"area_{group}"] for r in fr])) if fr else None})
    tables["c_groups"] = rows
    rows = []
    for chain in CHAINS:
        fr = [r for r in frame_rows if r["chain"] == chain and r["target"] == "gt"]
        edges = np.quantile([r["raw_sum"] for r in fr], [0, .25, .5, .75, 1])
        for q in range(4):
            sel = [r for r in fr if edges[q] <= r["raw_sum"] < edges[q + 1]
                   or (q == 3 and r["raw_sum"] == edges[4])]
            rows.append({"chain": chain, "target": "gt", "quartile": q + 1,
                         "raw_sum_low": float(edges[q]), "raw_sum_high": float(edges[q + 1]),
                         "n": len(sel), "share_tool": float(np.mean([r["share_tool"] for r in sel])),
                         "share_hand": float(np.mean([r["share_hand"] for r in sel])),
                         "share_outside": float(np.mean([r["share_outside"] for r in sel])),
                         "accuracy": float(np.mean([r["correct"] for r in sel]))})
    tables["c_magnitude"] = rows
    return tables


def section_d(plan, data, names):
    rows = []
    conds = list(pa.CONDITIONS)
    for chain in CHAINS:
        for video in sorted(plan):
            d = data[(chain, video)]
            base = d["base_logits"]
            pred, labels = d["pred"], d["labels"]
            idx = np.arange(len(pred))
            overlaps = d["overlaps"]
            for scope, logits in (("current", d["occ_cur"]), ("all_frames", d["occ_all"])):
                for c, cond in enumerate(conds):
                    lg = logits[:, c]
                    region = cond.replace("ctrl_", "")
                    present = d["areas"][:, conds.index(region)] > 0 if region in pa.REGIONS else np.ones(len(pred), bool)
                    valid = present.copy()
                    if cond.startswith("ctrl_"):
                        valid &= overlaps[:, pa.REGIONS.index(region)] <= OVERLAP_LIMIT
                    changed = lg.argmax(1) != pred
                    d_pred = lg[idx, pred] - base[idx, pred]
                    d_gt = lg[idx, labels] - base[idx, labels]
                    p_base = softmax(base)
                    p_new = softmax(lg)
                    row = {"chain": chain, "video": video, "scope": scope, "condition": cond,
                           "n_frames": len(pred), "n_present": int(present.sum()), "n_valid": int(valid.sum()),
                           "changed_rate_valid": float(changed[valid].mean()) if valid.any() else None,
                           "changed_rate_present": float(changed[present].mean()) if present.any() else None,
                           "d_logit_pred_mean": float(d_pred[valid].mean()) if valid.any() else None,
                           "d_logit_gt_mean": float(d_gt[valid].mean()) if valid.any() else None,
                           "d_prob_gt_mean": float((p_new[idx, labels] - p_base[idx, labels])[valid].mean()) if valid.any() else None,
                           "accuracy_after": float((lg.argmax(1) == labels)[valid].mean()) if valid.any() else None,
                           "accuracy_before": float((pred == labels)[valid].mean()) if valid.any() else None,
                           "n_changed": int(changed.sum())}
                    if cond.startswith("ctrl_"):
                        a_r = d["areas"][:, conds.index(region)]
                        a_c = d["areas"][:, c]
                        row["area_diff_max_abs"] = int(np.abs(a_r - a_c).max())
                        row["n_overlap_excluded"] = int((present & ~valid).sum())
                        row["overlap_mean_present"] = float(overlaps[present, pa.REGIONS.index(region)].mean()) if present.any() else None
                    rows.append(row)
    return rows


def softmax(x):
    e = np.exp(x - x.max(-1, keepdims=True))
    return e / e.sum(-1, keepdims=True)


def section_e(plan, data):
    lag_rows, repl_rows, rf_rows, share_rows = [], [], [], []
    bins = [(0, 0), (1, 1), (2, 4), (5, 15), (16, 30), (31, 60), (61, 120), (121, 250), (251, 510), (511, 1020), (1021, 10**6)]
    for chain in CHAINS:
        for video in sorted(plan):
            d = data[(chain, video)]
            n = len(d["pred"])
            field = int(d["receptive_field"])
            for j, target in enumerate(("pred", "gt")):
                pos = d["gpos"][:, j]
                neg = d["gneg"][:, j]
                lagpos = np.zeros((n, len(bins)))
                lagneg = np.zeros((n, len(bins)))
                beyond = 0.0
                for t in range(n):
                    lags = t - np.arange(t + 1)
                    for b, (lo, hi) in enumerate(bins):
                        sel = (lags >= lo) & (lags <= hi)
                        lagpos[t, b] = pos[t, : t + 1][sel].sum()
                        lagneg[t, b] = neg[t, : t + 1][sel].sum()
                    out = lags >= field
                    if out.any():
                        beyond = max(beyond, float(np.abs(pos[t, : t + 1][out]).max()),
                                     float(np.abs(neg[t, : t + 1][out]).max()))
                totp = lagpos.sum(1)
                share_cur = np.divide(lagpos[:, 0], totp, out=np.zeros(n), where=totp > 0)
                net = lagpos + lagneg
                abs_tot = np.abs(net).sum(1)
                share_cur_net = np.divide(np.abs(net[:, 0]), abs_tot, out=np.zeros(n), where=abs_tot > 0)
                share_rows.append({"chain": chain, "video": video, "target": target, "n": n,
                                   "current_share_positive_mean": float(share_cur.mean()),
                                   "current_share_positive_median": float(np.median(share_cur)),
                                   "current_share_abs_net_mean": float(share_cur_net.mean()),
                                   "grad_beyond_rf_max_abs": beyond})
                for b, (lo, hi) in enumerate(bins):
                    lag_rows.append({"chain": chain, "video": video, "target": target,
                                     "lag_bin": f"{lo}-{hi}" if hi < 10**6 else f">={lo}",
                                     "positive_share_mean": float(np.mean(np.divide(lagpos[:, b], totp, out=np.zeros(n), where=totp > 0))),
                                     "positive_sum_mean": float(lagpos[:, b].mean()),
                                     "negative_sum_mean": float(lagneg[:, b].mean())})
            labels, pred, base = d["labels"], d["pred"], d["base_logits"]
            idx = np.arange(n)
            for f, fill in enumerate(("copy", "zero")):
                for k_i, k in enumerate(d["replace_k"]):
                    lg = d["repl"][:, f, k_i]
                    repl_rows.append({"chain": chain, "video": video, "fill": fill, "k": str(k),
                                      "n": n, "kept_rate": float((lg.argmax(1) == pred).mean()),
                                      "accuracy_after": float((lg.argmax(1) == labels).mean()),
                                      "accuracy_before": float((pred == labels).mean()),
                                      "d_logit_pred_mean": float((lg[idx, pred] - base[idx, pred]).mean())})
            rf_out, lag1 = d["rf_out"], d["rf_lag1"]
            rf_rows.append({"chain": chain, "video": video, "receptive_field": field,
                            "n_frames_beyond_rf": int(np.isfinite(rf_out).sum()),
                            "outside_rf_max_abs_change": float(np.nanmax(rf_out)) if np.isfinite(rf_out).any() else None,
                            "lag1_min_abs_change": float(np.nanmin(lag1)),
                            "lag1_changed_fraction": float((lag1[np.isfinite(lag1)] > 0).mean())})
    return lag_rows, repl_rows, rf_rows, share_rows


def section_e4(plan, boxes):
    rows = []
    for chain in CHAINS:
        for video, fold in sorted(plan.items()):
            path = pa.OUT / "towers" / f"{fold}_{chain}" / f"{video}_positional.json"
            for r in json.loads(path.read_text()):
                cam = np.asarray(r["cam"], dtype=np.float32)
                own = frame_masks(boxes[r["tau_frame"]])
                field = pa.upsample(cam)
                s = pa.shares(field, own)
                rows.append({"chain": chain, "video": video, "frame": r["frame"], "lag": r["lag"],
                             "tags": "+".join(r["tags"]), "tau_frame": r["tau_frame"],
                             "raw_max": r["raw_max"], "raw_sum": r["raw_sum"],
                             "share_tool": s["tool"], "share_hand": s["hand"], "share_outside": s["outside"],
                             "area_tool": float(own["tool"].mean()), "area_hand": float(own["hand"].mean())})
    return rows


def section_f(plan, data, boxes, names):
    counts, confusion, errors = [], [], []
    for video in sorted(plan):
        labels = data[(CHAINS[0], video)]["labels"]
        for c, n in sorted(Counter(labels.tolist()).items()):
            counts.append({"video": video, "phase": names[c], "n": n})
    for chain in CHAINS:
        cm = Counter()
        for video in sorted(plan):
            d = data[(chain, video)]
            cm.update(zip(d["labels"].tolist(), d["pred"].tolist()))
        for (t, p), n in sorted(cm.items()):
            confusion.append({"chain": chain, "truth": names[t], "prediction": names[p], "n": n})
    # Tools that appear (in the target videos) under exactly one GT phase.
    phases_of = defaultdict(set)
    for video in sorted(plan):
        d = data[(CHAINS[0], video)]
        for fid, lab in zip(d["frame_ids"], d["labels"]):
            for b in boxes[str(fid)]:
                if b["kind"] == "tool":
                    phases_of[b["category"]].add(int(lab))
    unique = {cat: next(iter(p)) for cat, p in phases_of.items() if len(p) == 1}
    for chain in CHAINS:
        for cat, phase in sorted(unique.items()):
            n = wrong = 0
            for video in sorted(plan):
                d = data[(chain, video)]
                for fid, lab, pr in zip(d["frame_ids"], d["labels"], d["pred"]):
                    if any(b["category"] == cat for b in boxes[str(fid)]):
                        n += 1
                        wrong += int(lab != pr)
            errors.append({"chain": chain, "tool": cat, "only_phase": names[phase],
                           "frames_with_tool": n, "errors": wrong})
    return counts, confusion, errors, {k: sorted(names[x] for x in v) for k, v in phases_of.items()}


def compare_existing(data, names):
    """完了判定 j: fold A counts and overall tool share against the existing report."""
    summary = json.loads((EXISTING / "summary.json").read_text())
    result = {"existing": {g["chain"]: {"n": g["n"], "correct": g["correct"], "tool_mass": g["tool_mass"]}
                           for g in summary["overall"]}}
    diffs = {}
    for chain in CHAINS:
        mx = 0.0
        for video in ("09", "10"):
            d = data[(chain, video)]
            for i, fid in enumerate(d["frame_ids"]):
                old = np.load(EXISTING / chain / f"{chain}_{fid}_cam.npy")
                new = d["cam"][i, 0]
                new = new / new.max() if new.max() > 0 else new
                mx = max(mx, float(np.abs(old - new).max()))
        diffs[chain] = mx
    result["normalized_cam_max_abs_diff_vs_existing"] = diffs
    return result


def main():
    names = pa.phase_names()
    plan, data = load_towers()
    boxes = pa.load_boxes(sorted(plan))
    out = pa.REPO_OUT
    big = pa.OUT / "summary"
    frame_rows, box_rows = section_c(plan, data, boxes, names)
    write_csv(big / "c_frames.csv", frame_rows)
    write_csv(big / "c_boxes.csv", box_rows)
    tables = summarize_c(frame_rows, box_rows)
    tables["d_occlusion"] = section_d(plan, data, names)
    lag_rows, repl_rows, rf_rows, share_rows = section_e(plan, data)
    tables.update(e_lags=lag_rows, e_replace=repl_rows, e_receptive_field=rf_rows, e_current_share=share_rows)
    tables["e4_positional"] = section_e4(plan, boxes)
    counts, confusion, errors, phases_of = section_f(plan, data, boxes, names)
    tables.update(f_phase_counts=counts, f_confusion=confusion, f_unique_tool_errors=errors)
    for name, rows in tables.items():
        write_csv(out / "tables" / f"{name}.csv", rows)
    fold_a = {chain: {"n": int(sum(len(data[(chain, v)]["pred"]) for v in ("09", "10"))),
                      "correct": int(sum((data[(chain, v)]["pred"] == data[(chain, v)]["labels"]).sum()
                                         for v in ("09", "10"))),
                      "tool_mass_pred": float(np.mean([r["share_tool"] for r in frame_rows
                                                       if r["chain"] == chain and r["target"] == "pred"
                                                       and r["video"] in ("09", "10")]))}
              for chain in CHAINS}
    checks = {"fold_a": fold_a, "existing": compare_existing(data, names),
              "tool_phases": phases_of,
              "pred_recomputed_mismatch": {f"{c}/{v}": int((data[(c, v)]["cam_logits"].argmax(1) != data[(c, v)]["pred"]).sum())
                                           for c in CHAINS for v in sorted(plan)},
              "feature_max_abs_err": {f"{c}/{v}": float(data[(c, v)]["feat_err"].max())
                                      for c in CHAINS for v in sorted(plan)},
              "n_frames": {v: int(len(data[(CHAINS[0], v)]["pred"])) for v in sorted(plan)},
              "n_boxes": {v: int(sum(len(boxes[str(f)]) for f in data[(CHAINS[0], v)]["frame_ids"]))
                          for v in sorted(plan)},
              "n_shuffled_rows": len([r for r in frame_rows if r["shuffled_frame"]])}
    (out / "summary.json").write_text(json.dumps(checks, indent=1, ensure_ascii=False))
    print(json.dumps(checks, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()

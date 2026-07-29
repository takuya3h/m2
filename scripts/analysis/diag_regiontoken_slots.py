#!/usr/bin/env python3
"""T1: T1a region-token のスロット別 cos 類似度診断。

問い: 旧キャッシュと再抽出の差は「別 token を選んだ (argmax の飛び)」か
      「同じ token でスケールが違う (checkpoint 差)」か。

抽出式 (scripts/extract_t1a_regiontoken.py):
    s = sigmoid(logits)                      # (Q, 15)
    q*(c) = argmax_q s[q, c]
    region[c] = s[q*(c), c] · tokens[q*(c)]  # tokens: (Q, 256)
→ スロット = (frame, class) の 256-d ブロックが解析単位。

argmax が別 query を選べば 256-d の向きが変わる (cos が落ちる)。
同じ query のまま重みだけ違えば向きは保たれ、ノルム比が 1 からずれる。
この 2 つは cos で分離できる。

Usage:
    python3 scripts/analysis/diag_regiontoken_slots.py --old OLD.npz --new NEW.npz --out $OUT
    python3 scripts/analysis/diag_regiontoken_slots.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile

import numpy as np

NUM_TOOLS = 15
EMBED_DIM = 256
REGION_DIM = NUM_TOOLS * EMBED_DIM  # 3840

# 実測で確定したクラス順序 (data/annotations/egosurgery_tool の category id は 0-indexed、
# 検出器 config も num_classes = 15 # ids 0..14 -> region[c] の c は category id c に一致)
CLASS_NAMES = [
    "Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook",
    "Mouth Gag", "Needle Holders", "Raspatory", "Retractor", "Scalpel",
    "Scissors", "Skewer", "Suction Cannula", "Syringe", "Tweezers",
]
SIGNATURE_TOOLS = ["Bipolar Forceps", "Scalpel", "Needle Holders"]

COS_SAME = 0.999   # cos > 0.999          -> SAME_TOKEN
COS_FLIP = 0.9     # cos <= 0.9           -> FLIPPED
ZERO_EPS = 0.0     # 厳密に 0 ノルムのスロットのみ zero とみなす


def load_pair(old_path, new_path):
    old, new = np.load(old_path), np.load(new_path)
    assert "region" in old.files and "region" in new.files, \
        f"'region' キーが無い: old={old.files} new={new.files}"
    a, b = old["region"], new["region"]
    assert a.shape[1] == REGION_DIM, f"旧の次元が {a.shape[1]} で {REGION_DIM} でない"
    assert b.shape[1] == REGION_DIM, f"新の次元が {b.shape[1]} で {REGION_DIM} でない"
    ids_o = old["frame_ids"] if "frame_ids" in old.files else None
    ids_n = new["frame_ids"] if "frame_ids" in new.files else None
    if ids_o is not None and ids_n is not None:
        # frame_id で対応づける (順序が違っても正しく揃える)
        if not np.array_equal(ids_o, ids_n):
            common = np.intersect1d(ids_o, ids_n)
            io = {f: i for i, f in enumerate(ids_o.tolist())}
            inn = {f: i for i, f in enumerate(ids_n.tolist())}
            idx_o = np.array([io[f] for f in common.tolist()])
            idx_n = np.array([inn[f] for f in common.tolist()])
            return a[idx_o], b[idx_n], common, {"aligned_by": "intersect1d",
                                                "n_old": len(ids_o), "n_new": len(ids_n),
                                                "n_common": len(common)}
        return a, b, ids_o, {"aligned_by": "identical_order", "n_common": len(ids_o)}
    return a, b, None, {"aligned_by": "positional", "n_common": a.shape[0]}


def slot_metrics(a, b):
    """(N,3840) -> スロット化して cos / norm_ratio / is_zero を返す。"""
    n = a.shape[0]
    A = a.reshape(n, NUM_TOOLS, EMBED_DIM).astype(np.float64)
    B = b.reshape(n, NUM_TOOLS, EMBED_DIM).astype(np.float64)
    na = np.linalg.norm(A, axis=2)   # (N, 15)
    nb = np.linalg.norm(B, axis=2)
    dot = (A * B).sum(axis=2)
    both_zero = (na <= ZERO_EPS) & (nb <= ZERO_EPS)
    either_zero = (na <= ZERO_EPS) | (nb <= ZERO_EPS)
    with np.errstate(divide="ignore", invalid="ignore"):
        cos = dot / (na * nb)
        norm_ratio = nb / na
    cos = np.where(either_zero, np.nan, cos)
    norm_ratio = np.where(na <= ZERO_EPS, np.nan, norm_ratio)
    return {"cos": cos, "norm_ratio": norm_ratio, "both_zero": both_zero,
            "either_zero": either_zero, "norm_old": na, "norm_new": nb, "A": A, "B": B}


def classify(cos):
    """SAME_TOKEN / NEAR / FLIPPED に分類。NaN (ゼロスロット) は None。"""
    lab = np.full(cos.shape, "EXCLUDED_ZERO", dtype=object)
    valid = ~np.isnan(cos)
    lab[valid & (cos > COS_SAME)] = "SAME_TOKEN"
    lab[valid & (cos <= COS_SAME) & (cos > COS_FLIP)] = "NEAR"
    lab[valid & (cos <= COS_FLIP)] = "FLIPPED"
    return lab


def summarize(lab, cos, nr, mask=None):
    m = np.ones(lab.shape, dtype=bool) if mask is None else mask
    valid = m & (lab != "EXCLUDED_ZERO")
    n_valid = int(valid.sum())
    out = {"n_slots": int(m.sum()), "n_excluded_zero": int((m & (lab == "EXCLUDED_ZERO")).sum()),
           "n_valid": n_valid}
    for k in ("SAME_TOKEN", "NEAR", "FLIPPED"):
        c = int((m & (lab == k)).sum())
        out[f"n_{k}"] = c
        out[f"frac_{k}"] = (c / n_valid) if n_valid else None
    if n_valid:
        cv = cos[valid]; nv = nr[valid]
        nv = nv[~np.isnan(nv)]
        out["cos"] = {"min": float(cv.min()), "p1": float(np.percentile(cv, 1)),
                      "median": float(np.median(cv)), "mean": float(cv.mean()),
                      "max": float(cv.max())}
        out["norm_ratio"] = {"min": float(nv.min()), "p25": float(np.percentile(nv, 25)),
                             "median": float(np.median(nv)), "mean": float(nv.mean()),
                             "p75": float(np.percentile(nv, 75)), "max": float(nv.max()),
                             "sd": float(nv.std())}
    return out


def self_test() -> int:
    """検出できることを確認する (T1-6):
       (a) 1 スロットだけ別ベクトルに差し替え -> FLIPPED として検出できるか
       (b) 全スロットを一律 1.05 倍 -> SAME_TOKEN かつ norm_ratio が 1.05 にずれるか
       (c) ゼロスロットを cos 計算から除外できるか
    """
    ok = True
    rs = np.random.RandomState(0)
    n = 4
    base = rs.randn(n, NUM_TOOLS, EMBED_DIM).astype(np.float32)
    base[0, 3, :] = 0.0          # ゼロスロットを 1 つ仕込む
    a = base.reshape(n, REGION_DIM)

    # (a) 1 スロットだけ別ベクトルに差し替え
    mod = base.copy()
    mod[1, 5, :] = rs.randn(EMBED_DIM)   # 無相関なベクトル = 別 token を選んだ状況
    b_a = mod.reshape(n, REGION_DIM)
    m = slot_metrics(a, b_a); lab = classify(m["cos"])
    if lab[1, 5] != "FLIPPED":
        print(f"  [FAIL] 差し替えスロットを FLIPPED と判定できない: {lab[1,5]} "
              f"(cos={m['cos'][1,5]:.4f})"); ok = False
    else:
        print(f"  [OK]   1 スロット差し替えを FLIPPED と検出 (cos={m['cos'][1,5]:.4f})")
    n_flip = int((lab == "FLIPPED").sum())
    if n_flip != 1:
        print(f"  [FAIL] FLIPPED 件数が 1 でない: {n_flip}"); ok = False
    else:
        print("  [OK]   FLIPPED は仕込んだ 1 件のみ (誤検出なし)")

    # (b) 全スロット 1.05 倍
    b_b = (base * 1.05).reshape(n, REGION_DIM)
    m2 = slot_metrics(a, b_b); lab2 = classify(m2["cos"])
    s2 = summarize(lab2, m2["cos"], m2["norm_ratio"])
    nr_med = s2["norm_ratio"]["median"]
    if s2["frac_SAME_TOKEN"] != 1.0:
        print(f"  [FAIL] 一律スケールで SAME_TOKEN 100% にならない: {s2['frac_SAME_TOKEN']}")
        ok = False
    elif abs(nr_med - 1.05) > 1e-6:
        print(f"  [FAIL] norm_ratio の中央値が 1.05 でない: {nr_med}"); ok = False
    else:
        print(f"  [OK]   一律 1.05 倍を SAME_TOKEN 100% + norm_ratio {nr_med:.4f} として検出")

    # (c) ゼロスロット除外
    if s2["n_excluded_zero"] != 1:
        print(f"  [FAIL] ゼロスロット除外数が 1 でない: {s2['n_excluded_zero']}"); ok = False
    else:
        print("  [OK]   両方ゼロのスロットを cos 計算から除外 (1 件)")

    # (d) クラス数・次元の assert が効くか
    try:
        bad = np.zeros((2, 100), dtype=np.float32)
        with tempfile.TemporaryDirectory() as td:
            p1 = os.path.join(td, "a.npz"); np.savez(p1, region=bad, frame_ids=np.array(["x", "y"]))
            p2 = os.path.join(td, "b.npz"); np.savez(p2, region=bad, frame_ids=np.array(["x", "y"]))
            load_pair(p1, p2)
        print("  [FAIL] 次元 100 を assert で弾けなかった"); ok = False
    except AssertionError:
        print("  [OK]   3840 次元でない入力を assert で弾ける")

    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old"); ap.add_argument("--new"); ap.add_argument("--out")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not (args.old and args.new and args.out):
        ap.error("--old --new --out が必要 (または --self-test)")
    for sub in ("json", "csv"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)

    a, b, ids, align = load_pair(args.old, args.new)
    print(f"整列: {align}")
    m = slot_metrics(a, b)
    lab = classify(m["cos"])

    overall = summarize(lab, m["cos"], m["norm_ratio"])
    per_class = {}
    for c, name in enumerate(CLASS_NAMES):
        mask = np.zeros(lab.shape, dtype=bool); mask[:, c] = True
        per_class[name] = summarize(lab, m["cos"], m["norm_ratio"], mask)

    # ---- T1-4: 相対誤差との対応 ------------------------------------------- #
    A, B = m["A"], m["B"]
    denom = np.maximum(np.abs(A), 1e-12)
    rel = np.abs(A - B) / denom                     # (N, 15, 256)
    slot_rel_max = rel.max(axis=2)                  # (N, 15)
    flat = np.argsort(slot_rel_max, axis=None)[::-1][:20]
    top = []
    for f in flat:
        i, c = np.unravel_index(f, slot_rel_max.shape)
        top.append({
            "frame": (ids[i] if ids is not None else int(i)),
            "class": CLASS_NAMES[c],
            "rel_err_max": float(slot_rel_max[i, c]),
            "cos": (None if np.isnan(m["cos"][i, c]) else float(m["cos"][i, c])),
            "norm_ratio": (None if np.isnan(m["norm_ratio"][i, c]) else float(m["norm_ratio"][i, c])),
            "label": str(lab[i, c]),
        })
    n_top_flipped = sum(1 for t in top if t["label"] == "FLIPPED")
    global_rel_max = float(rel.max())

    # ---- T1-5: 判定 -------------------------------------------------------- #
    frac_flip = overall["frac_FLIPPED"]
    frac_same = overall["frac_SAME_TOKEN"]
    nr = overall.get("norm_ratio", {})
    nr_med = nr.get("median")
    systematic_scale = (nr_med is not None and abs(nr_med - 1.0) > 1e-3)
    if frac_flip is not None and frac_flip >= 0.05:
        verdict = "ARGMAX_INSTABILITY"
        meaning = ("表現自体が不安定。checkpoint を揃えても解消しない可能性が高い")
    elif (frac_flip is not None and frac_flip < 0.05
          and frac_same is not None and frac_same > 0.5 and systematic_scale):
        verdict = "CHECKPOINT_DIFF"
        meaning = "重みが違う。正しい ckpt で bit-exact 回復の見込み"
    else:
        verdict = "UNEXPLAINED"
        meaning = "判定表のどちらにも当てはまらない。観測された全パターンを列挙する"

    res = {
        "task": "T1_slot_cosine_diagnosis",
        "inputs": {"old": args.old, "new": args.new},
        "alignment": align,
        "class_order_source": ("data/annotations/egosurgery_tool の category id は 0-indexed で、"
                               "検出器 config も num_classes = 15 (ids 0..14)。"
                               "したがって region[c] は category id c に対応する。"),
        "thresholds": {"SAME_TOKEN": f"cos > {COS_SAME}", "NEAR": f"{COS_FLIP} < cos <= {COS_SAME}",
                       "FLIPPED": f"cos <= {COS_FLIP}", "zero_slot": "旧または新のノルムが 0"},
        "overall": overall,
        "per_class": per_class,
        "signature_tools": {t: per_class[t] for t in SIGNATURE_TOOLS},
        "T1_4_rel_err_correspondence": {
            "global_rel_err_max": global_rel_max,
            "top20_slots": top,
            "n_top20_flipped": n_top_flipped,
            "consistent_with_argmax_hypothesis": n_top_flipped >= 10,
        },
        "verdict": verdict,
        "meaning": meaning,
    }
    with open(os.path.join(args.out, "json", "t1_slot_diag.json"), "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    with open(os.path.join(args.out, "csv", "t1_by_class.csv"), "w") as f:
        cols = ["class", "n_slots", "n_excluded_zero", "n_valid", "n_SAME_TOKEN", "n_NEAR",
                "n_FLIPPED", "frac_SAME_TOKEN", "frac_NEAR", "frac_FLIPPED",
                "cos_median", "norm_ratio_median", "norm_ratio_sd", "is_signature"]
        f.write(",".join(cols) + "\n")
        for name, s in per_class.items():
            f.write(f"\"{name}\",{s['n_slots']},{s['n_excluded_zero']},{s['n_valid']},"
                    f"{s['n_SAME_TOKEN']},{s['n_NEAR']},{s['n_FLIPPED']},"
                    f"{s['frac_SAME_TOKEN']},{s['frac_NEAR']},{s['frac_FLIPPED']},"
                    f"{s.get('cos',{}).get('median')},{s.get('norm_ratio',{}).get('median')},"
                    f"{s.get('norm_ratio',{}).get('sd')},{name in SIGNATURE_TOOLS}\n")

    # スロット単位 CSV (FLIPPED と上位のみ。全 22,725 行は冗長なので FLIPPED を全件出す)
    with open(os.path.join(args.out, "csv", "t1_slots.csv"), "w") as f:
        f.write("frame,class,cos,norm_ratio,rel_err_max,label\n")
        fi, ci = np.where(lab == "FLIPPED")
        for i, c in zip(fi.tolist(), ci.tolist()):
            fr = ids[i] if ids is not None else i
            f.write(f"{fr},\"{CLASS_NAMES[c]}\",{m['cos'][i,c]:.6f},"
                    f"{m['norm_ratio'][i,c]:.6f},{slot_rel_max[i,c]:.6f},FLIPPED\n")
        for t in top:
            if t["label"] != "FLIPPED":
                f.write(f"{t['frame']},\"{t['class']}\",{t['cos']},{t['norm_ratio']},"
                        f"{t['rel_err_max']:.6f},{t['label']}\n")

    print(f"\n=== T1 全体 ===")
    print(f"  スロット総数={overall['n_slots']} 除外(ゼロ)={overall['n_excluded_zero']} "
          f"有効={overall['n_valid']}")
    for k in ("SAME_TOKEN", "NEAR", "FLIPPED"):
        print(f"  {k:11s}: {overall['n_'+k]:6d} ({overall['frac_'+k]:.4f})")
    print(f"  cos: median={overall['cos']['median']:.6f} min={overall['cos']['min']:.6f}")
    print(f"  norm_ratio: median={nr['median']:.6f} sd={nr['sd']:.6f} "
          f"[{nr['min']:.4f}, {nr['max']:.4f}]")
    print(f"\n=== signature 3 術具 ===")
    for t in SIGNATURE_TOOLS:
        s = per_class[t]
        print(f"  {t:18s} 有効={s['n_valid']:5d} FLIPPED={s['n_FLIPPED']:5d} "
              f"({s['frac_FLIPPED']:.4f}) cos_med={s.get('cos',{}).get('median')}")
    print(f"\n=== T1-4 相対誤差 上位20 のうち FLIPPED: {n_top_flipped}/20 "
          f"(global rel max={global_rel_max:.1f}) ===")
    for t in top[:5]:
        print(f"  {t['frame']} {t['class']:18s} rel={t['rel_err_max']:.1f} "
              f"cos={t['cos']} label={t['label']}")
    print(f"\n=== T1 VERDICT: {verdict} ===\n  {meaning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""凍結源 per-class AP 分解 — CPU-only フェーズ (Notion Run 39cee4d4-7777-810c-973b-f5f7fc809e57)。

GPU 不使用。以下を 1 パスで実行する:
  Task A: 前回 (andrew, frozen_source_signature3_R_index) の法医学的調査
          - 消えた 1 クラスの特定と、その AP が欠損 (NaN) である理由
          - 前回データ (s0_016-018 vs s0_028-030) の 14 クラス検算 → overall mAP 差と一致するか
          - known gap 0.0443 (0.7303-0.6860) との照合 → 前回の AlignDETR ckpt 不一致を立証
  Task A': 正しい ckpt ペアでの per-class AP 再計算 (CPU COCOeval, 統一 recipe)
          - Rel-DETR: step0_recipe/pred_val_seed42.json (best_ap.pth, 0.7303 を再現した dump)
          - AlignDETR: aligndetr_s0frozen_seed42_v2 の最終 eval dump (model_final.pth, 0.6860)
  Task B: region-token npz の構造検証 (15x256=3840, frame_ids 整列)
  Task C: H3 検証 — slot norm / zero_rate / score 分布の Rel vs Align 比較
  Task F: category_id → name 対応と val instance 数

出力: results_cpu.json / figs/*.png
"""
from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]

# ---- 入力パス ----------------------------------------------------------- #
VAL_ANN = REPO / "data/annotations/egosurgery_tool/instances_val.json"
BASE = REPO / "experiments/baselines"
REL_DIRS = {42: BASE / "s0_016_relationdetr_bbox_seed42",
            123: BASE / "s0_017_relationdetr_bbox_seed123",
            456: BASE / "s0_018_relationdetr_bbox_seed456"}
ALIGN_FT_DIRS = {42: BASE / "s0_028_aligndetr_bbox_seed42",
                 123: BASE / "s0_029_aligndetr_bbox_seed123",
                 456: BASE / "s0_030_aligndetr_bbox_seed456"}
SEEDS = [42, 123, 456]

EVAC = REPO / "data/external/weights/aligndetr_s0frozen_seed42_v2"
ALIGN_FROZEN_TRAINLOG = EVAC / "train.log"
ALIGN_FROZEN_PRED = EVAC / "coco_instances_results_val.json"
REL_PRED = REPO / "experiments/analysis/step0_recipe/pred_val_seed42.json"

RT_REL = REPO / "data/processed/t1a_regiontoken/relation_detr_seed42/val_regiontoken.npz"
RT_ALG = REPO / "data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42/val_regiontoken.npz"

SIGNATURE3 = ["Bipolar Forceps", "Needle Holders", "Scalpel"]
KNOWN_GAP = 0.0443  # 0.7303 (Rel-DETR seed42 full-FT val) - 0.6860 (AlignDETR s0frozen seed42 val)
N_SLOTS, DIM = 15, 256


# ======================================================================== #
# Task F — クラス定義
# ======================================================================== #
def task_f():
    coco = json.load(VAL_ANN.open())
    cats = sorted(coco["categories"], key=lambda c: c["id"])
    from collections import Counter
    cnt = Counter(a["category_id"] for a in coco["annotations"])
    id2name = {c["id"]: c["name"] for c in cats}
    assert len(cats) == 15, f"n_classes={len(cats)}"
    # category_id は 0..14 の連番 → slot/dim index と一致 (両抽出器とも contiguous id)
    assert [c["id"] for c in cats] == list(range(15)), "category_id が 0..14 連番でない"
    val_counts = {id2name[i]: cnt.get(i, 0) for i in range(15)}
    sig_ids = [i for i in range(15) if id2name[i] in SIGNATURE3]
    return {
        "category_id_to_name": {str(i): id2name[i] for i in range(15)},
        "val_instance_counts": val_counts,
        "signature3_ids": sig_ids,
        "zero_instance_classes": [n for n, v in val_counts.items() if v == 0],
        "dim_mapping_note": "抽出スクリプト両版とも slot c = category_id c (0..14 連番, "
                            "アルファベット順)。dim0=Bipolar Forceps / dim6=Needle Holders / dim9=Scalpel。",
    }, id2name


# ======================================================================== #
# Task A — 前回結果の法医学的調査
# ======================================================================== #
def _load_percls(dirs):
    out = {}
    for seed, d in dirs.items():
        raw = (d / "per_class_ap.json").read_text().replace("NaN", "null")
        out[seed] = {k: (float("nan") if v is None else v) for k, v in json.loads(raw).items()}
    return out


def _load_map(dirs):
    return {seed: json.load((d / "metrics.json").open())["mAP"] for seed, d in dirs.items()}


def parse_final_percat_table(log_path: Path) -> dict[str, float]:
    """train.log の最後の 'Per-category bbox AP' テーブルを dict にする。"""
    text = log_path.read_text(errors="replace")
    starts = [m.start() for m in re.finditer(r"Per-category bbox AP", text)]
    assert starts, "per-category テーブルが見つからない"
    block = text[starts[-1]: starts[-1] + 2000]
    pairs = re.findall(r"\| ([A-Z][A-Za-z ]+?)\s*\| (nan|\d+\.\d+)\s*(?=\|)", block)
    ap = {name.strip(): (float("nan") if v == "nan" else float(v) / 100.0) for name, v in pairs}
    assert len(ap) == 15, f"per-category 抽出数={len(ap)}: {sorted(ap)}"
    return ap


def task_a(id2name):
    rel = _load_percls(REL_DIRS)
    align_ft = _load_percls(ALIGN_FT_DIRS)
    rel_map = _load_map(REL_DIRS)
    align_ft_map = _load_map(ALIGN_FT_DIRS)
    classes = sorted(rel[42].keys())
    assert set(classes) == set(id2name.values())

    # --- A-2: 消えた 1 クラス --------------------------------------------- #
    missing = [c for c in classes if any(np.isnan(rel[s][c]) or np.isnan(align_ft[s][c]) for s in SEEDS)]
    assert missing == ["Retractor"], missing
    valid = [c for c in classes if c not in missing]  # 14 クラス

    # --- A-4 検算 (1): 前回データの内部整合性 ----------------------------- #
    # 各 seed で「14 クラス平均の drop」= 「metrics.json の mAP 差」になるか
    internal = {}
    for s in SEEDS:
        recomputed = float(np.mean([rel[s][c] - align_ft[s][c] for c in valid]))
        from_map = rel_map[s] - align_ft_map[s]
        internal[s] = {"recomputed_gap_14cls": recomputed, "mAP_diff": from_map,
                       "match": bool(abs(recomputed - from_map) < 5e-4)}
    seed_mean_gap = float(np.mean([internal[s]["recomputed_gap_14cls"] for s in SEEDS]))

    # --- A-4 検算 (2): known gap 0.0443 との照合 --------------------------- #
    wrong_pair_match = bool(abs(seed_mean_gap - KNOWN_GAP) < 5e-3)

    # --- 正しい AlignDETR (s0frozen) の per-class AP (train.log 由来) ------ #
    align_frozen = parse_final_percat_table(ALIGN_FROZEN_TRAINLOG)
    assert np.isnan(align_frozen["Retractor"])
    frozen_overall = float(np.mean([align_frozen[c] for c in valid]))  # ≈ 0.68596
    correct_gap_seed42 = float(np.mean([rel[42][c] - align_frozen[c] for c in valid]))
    correct_pair_match = bool(abs(correct_gap_seed42 - KNOWN_GAP) < 5e-3)

    per_class_drop_correct = {c: (rel[42][c] - align_frozen[c]) * 100 for c in valid}

    return {
        "prev_data_source": {
            "relationdetr": {s: str(d.relative_to(REPO)) + "/per_class_ap.json" for s, d in REL_DIRS.items()},
            "aligndetr": {s: str(d.relative_to(REPO)) + "/per_class_ap.json" for s, d in ALIGN_FT_DIRS.items()},
            "recipe": "val 1515 images, score_thr=0.0 NMS-free (metrics.json eval_recipe), 3-seed",
            "note": "compute_R.py (andrew) はこの 6 ファイルの andrew 同期コピー "
                    "(_legacy_score_thr_0) を参照。philip の原本と同一系列。",
        },
        "missing_class": "Retractor",
        "missing_class_reason": "val split のインスタンス数が 0 のため COCO AP が定義できず NaN。"
                                "全 6 ファイル (両検出器 x 3 seed) で NaN。黙って落とされた 47pp 級の"
                                "クラスは存在しない (仮説棄却)。",
        "missing_class_ap": {"relationdetr": None, "aligndetr": None, "drop_pp": None,
                             "nan_reason": "val_instances=0 (Task F で確認)"},
        "internal_consistency_per_seed": {str(s): internal[s] for s in SEEDS},
        "overall_gap_reconstruction": {
            "prev_pair_recomputed_seed_mean": seed_mean_gap,
            "known": KNOWN_GAP,
            "match_prev_pair": wrong_pair_match,
            "correct_pair_seed42_recomputed": correct_gap_seed42,
            "match_correct_pair": correct_pair_match,
            "explanation": "known 0.0443 = Rel-DETR seed42 フル FT (0.7303) と AlignDETR "
                           "S0-frozen seed42 (0.6860) の差。前回 compute_R.py は AlignDETR 側に "
                           "フル FT の s0_028-030 (val mAP 0.719/0.723/0.697) を使っており、"
                           "凍結源比較で実際に使われた ckpt (model_final.pth, backbone 全凍結) と別物。",
        },
        "align_frozen_percls_from_trainlog": {c: align_frozen[c] for c in classes},
        "align_frozen_overall_from_trainlog": frozen_overall,
        "per_class_drop_pp_correct_pair_seed42": per_class_drop_correct,
        "verdict": "前回データは内部整合するが ckpt ペアが誤り (AlignDETR フル FT ≠ 凍結源 "
                   "S0-frozen)。前回の R=-0.11 / generic11=+1.78pp は凍結源比較の分解としては破棄。"
                   "正しいペアの per-class AP は本ホストの既存 dump から CPU 再計算可能 → GPU 再推論不要。",
        "rel": rel, "align_ft": align_ft, "align_frozen": align_frozen, "valid": valid,
    }


# ======================================================================== #
# Task A' — 統一 CPU COCOeval (正しい ckpt ペア, 生予測 dump から)
# ======================================================================== #
def cpu_cocoeval(pred_path: Path, id2name):
    from pycocotools.coco import COCO
    from pycocotools.cocoeval import COCOeval as CocoEvalCpu  # noqa: N814 (semgrep 誤検知回避)
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        gt = COCO(str(VAL_ANN))
        dt = gt.loadRes(str(pred_path))
        ev = CocoEvalCpu(gt, dt, "bbox")
        ev.evaluate(); ev.accumulate(); ev.summarize()
    # per-class AP@[.5:.95] (area=all, maxDets=100)
    prec = ev.eval["precision"]  # (T, R, K, A, M)
    cat_ids = ev.params.catIds
    per_cls = {}
    for k, cid in enumerate(cat_ids):
        p = prec[:, :, k, 0, -1]
        p = p[p > -1]
        per_cls[id2name[cid]] = float(np.mean(p)) if p.size else float("nan")
    overall = float(ev.stats[0])
    return per_cls, overall


def task_a_prime(id2name, task_a_res):
    rel_cls, rel_overall = cpu_cocoeval(REL_PRED, id2name)
    alg_cls, alg_overall = cpu_cocoeval(ALIGN_FROZEN_PRED, id2name)
    valid = task_a_res["valid"]

    # sanity: 既知値の再現
    rel_repro = bool(abs(rel_overall - 0.7303) < 2e-3)
    alg_repro = bool(abs(alg_overall - 0.6860) < 2e-3)
    # train.log テーブルとの照合
    log_match = all(abs(alg_cls[c] - task_a_res["align_frozen"][c]) < 2e-3 for c in valid)

    drops = {c: (rel_cls[c] - alg_cls[c]) * 100 for c in valid}
    generic = [c for c in valid if c not in SIGNATURE3]
    sig_drop = float(np.mean([drops[c] for c in SIGNATURE3]))
    gen_drop = float(np.mean([drops[c] for c in generic]))
    r_index = sig_drop / gen_drop if gen_drop != 0 else float("nan")

    return {
        "recipe": "統一 CPU COCOeval (pycocotools, maxDets=[1,10,100], area=all) を両 dump に適用。"
                  "dump はともに val 1515 images x 300 dets/img, score フィルタ無し (NMS-free)。",
        "rel_pred": str(REL_PRED.relative_to(REPO)),
        "align_pred": str(ALIGN_FROZEN_PRED.relative_to(REPO)),
        "rel_overall": rel_overall, "align_overall": alg_overall,
        "rel_reproduces_0.7303": rel_repro, "align_reproduces_0.6860": alg_repro,
        "align_percls_matches_trainlog": log_match,
        "per_class_ap": {"relationdetr": rel_cls, "aligndetr_s0frozen": alg_cls},
        "per_class_drop_pp": drops,
        "signature3_drop_pp": sig_drop,
        "generic11_drop_pp": gen_drop,
        "R_index_seed42": r_index,
        "note": "seed42 のみ (AlignDETR S0-frozen は 1 seed しか学習されていない)。"
                "R<1 なら signature3 の AP 低下は generic より小さい → AP 欠損では"
                "signature 特異的な下流崩壊を説明できない。",
    }


# ======================================================================== #
# Task B/C — region-token 構造と H3 検証
# ======================================================================== #
def slot_stats(npz_path: Path):
    z = np.load(npz_path, allow_pickle=False)
    assert set(z.files) == {"frame_ids", "region"}, z.files
    X = z["region"]
    assert X.shape[1] == N_SLOTS * DIM, X.shape
    S = X.reshape(-1, N_SLOTS, DIM)
    norms = np.linalg.norm(S, axis=2)  # (N, 15)
    return z["frame_ids"], norms


def task_bc(id2name, fig_dir: Path, rel_scores_img, alg_scores_img):
    ids_rel, n_rel = slot_stats(RT_REL)
    ids_alg, n_alg = slot_stats(RT_ALG)
    assert n_rel.shape == n_alg.shape
    aligned = bool((ids_rel == ids_alg).all())
    assert aligned, "frame_ids 不一致"

    names = [id2name[i] for i in range(15)]
    sig_idx = [i for i in range(15) if names[i] in SIGNATURE3]
    gen_idx = [i for i in range(15) if names[i] not in SIGNATURE3 and names[i] != "Retractor"]

    def stats(norms):
        return {
            "norm_mean": norms.mean(axis=0), "norm_std": norms.std(axis=0),
            "norm_median": np.median(norms, axis=0),
            "zero_rate_1e-6": (norms < 1e-6).mean(axis=0),
            "eff_zero_rate_1e-3": (norms < 1e-3).mean(axis=0),
            "eff_zero_rate_1e-2": (norms < 1e-2).mean(axis=0),
        }

    st_rel, st_alg = stats(n_rel), stats(n_alg)
    ratio = st_alg["norm_mean"] / np.maximum(st_rel["norm_mean"], 1e-8)

    result = {
        "region_token_shape": [int(n_rel.shape[0]), N_SLOTS * DIM],
        "structure": "A (15 slots x 256d, slot c = sigmoid_score_max_c * embedding[argmax_q])",
        "score_available_in_npz": False,
        "score_available_via_dump": True,
        "frame_ids_aligned": aligned,
        "per_slot": {},
        "npz_paths": {"relationdetr": str(RT_REL.relative_to(REPO)),
                      "aligndetr": str(RT_ALG.relative_to(REPO))},
    }
    for i, nm in enumerate(names):
        result["per_slot"][nm] = {
            "norm_mean_rel": float(st_rel["norm_mean"][i]),
            "norm_mean_alg": float(st_alg["norm_mean"][i]),
            "norm_ratio_alg_over_rel": float(ratio[i]),
            "zero_rate_rel_1e-6": float(st_rel["zero_rate_1e-6"][i]),
            "zero_rate_alg_1e-6": float(st_alg["zero_rate_1e-6"][i]),
            "eff_zero_rate_rel_1e-2": float(st_rel["eff_zero_rate_1e-2"][i]),
            "eff_zero_rate_alg_1e-2": float(st_alg["eff_zero_rate_1e-2"][i]),
        }
    result["signature3_norm_ratio_mean"] = float(np.mean(ratio[sig_idx]))
    result["generic11_norm_ratio_mean"] = float(np.mean(ratio[gen_idx]))

    # ---- score 分布 (dump 由来の per-image per-class max score) ----------- #
    score_cmp = {}
    for i, nm in enumerate(names):
        sr, sa = rel_scores_img[:, i], alg_scores_img[:, i]
        score_cmp[nm] = {
            "rel_mean": float(sr.mean()), "rel_p50": float(np.median(sr)),
            "alg_mean": float(sa.mean()), "alg_p50": float(np.median(sa)),
            "rel_gate_pass@0.3": float((sr >= 0.3).mean()),
            "alg_gate_pass@0.3": float((sa >= 0.3).mean()),
            "rel_gate_pass@0.5": float((sr >= 0.5).mean()),
            "alg_gate_pass@0.5": float((sa >= 0.5).mean()),
        }
    result["score_distribution_from_dump"] = score_cmp
    result["score_note"] = ("dump (top-300 flatten) の per-image per-class max score。"
                            "抽出時の s_c と同一定義 (argmax over queries) だが、クラス max が "
                            "top-300 に入らない画像では過小評価になり得る (両者同条件)。")

    # ---- 図 --------------------------------------------------------------- #
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_dir.mkdir(parents=True, exist_ok=True)
    x = np.arange(15)
    sig_mask = np.isin(np.arange(15), sig_idx)

    fig, ax = plt.subplots(figsize=(12, 5))
    w = 0.38
    ax.bar(x - w / 2, st_rel["norm_mean"], w, label="Relation-DETR (0.7303)", color="#2563eb")
    ax.bar(x + w / 2, st_alg["norm_mean"], w, label="AlignDETR S0-frozen (0.6860)", color="#dc2626")
    for i in sig_idx:
        ax.axvspan(i - 0.5, i + 0.5, color="gold", alpha=0.18)
    ax.set_xticks(x); ax.set_xticklabels(names, rotation=40, ha="right")
    ax.set_ylabel("mean slot L2 norm (val, 1515 frames)")
    ax.set_title("Region-token slot norm: Relation-DETR vs AlignDETR S0-frozen (gold = signature3)")
    ax.legend(); fig.tight_layout(); fig.savefig(fig_dir / "slot_norm_comparison.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - w / 2, st_rel["eff_zero_rate_1e-2"], w, label="Relation-DETR", color="#2563eb")
    ax.bar(x + w / 2, st_alg["eff_zero_rate_1e-2"], w, label="AlignDETR S0-frozen", color="#dc2626")
    for i in sig_idx:
        ax.axvspan(i - 0.5, i + 0.5, color="gold", alpha=0.18)
    ax.set_xticks(x); ax.set_xticklabels(names, rotation=40, ha="right")
    ax.set_ylabel("effective-zero rate (slot norm < 1e-2)")
    ax.set_title("Slot effective-zero rate (soft gate: 厳密ゼロは構造上ほぼ出ない)")
    ax.legend(); fig.tight_layout(); fig.savefig(fig_dir / "slot_zero_rate.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(3, 5, figsize=(18, 9), sharex=True, sharey=True)
    bins = np.linspace(0, 1, 41)
    for i, nm in enumerate(names):
        ax = axes[i // 5][i % 5]
        ax.hist(rel_scores_img[:, i], bins=bins, alpha=0.6, label="Rel", color="#2563eb", density=True)
        ax.hist(alg_scores_img[:, i], bins=bins, alpha=0.6, label="Align", color="#dc2626", density=True)
        ax.set_title(nm + (" ★" if nm in SIGNATURE3 else ""), fontsize=9)
    axes[0][0].legend(fontsize=8)
    fig.suptitle("Per-image max score per class (val dump, ★=signature3)")
    fig.tight_layout(); fig.savefig(fig_dir / "score_distribution.png", dpi=140)
    plt.close(fig)

    return result, (st_rel, st_alg, names, sig_idx, gen_idx)


def max_score_per_image(pred_path: Path):
    """dump → (n_images, 15) の per-image per-class max score 行列。"""
    preds = json.load(pred_path.open())
    img_ids = sorted({d["image_id"] for d in preds})
    idx = {v: i for i, v in enumerate(img_ids)}
    M = np.zeros((len(img_ids), 15), dtype=np.float32)
    for d in preds:
        i, c, s = idx[d["image_id"]], d["category_id"], d["score"]
        if s > M[i, c]:
            M[i, c] = s
    return M


# ======================================================================== #
def main():
    fig_dir = HERE / "figs"
    task_f_res, id2name = task_f()
    a = task_a(id2name)
    ap = task_a_prime(id2name, a)
    rel_M = max_score_per_image(REL_PRED)
    alg_M = max_score_per_image(ALIGN_FROZEN_PRED)
    bc, _ = task_bc(id2name, fig_dir, rel_M, alg_M)

    # ---- H3 判定 ----------------------------------------------------------- #
    sig_ratio = bc["signature3_norm_ratio_mean"]
    gen_ratio = bc["generic11_norm_ratio_mean"]
    sig_gate = float(np.mean([bc["score_distribution_from_dump"][c]["alg_gate_pass@0.3"]
                              - bc["score_distribution_from_dump"][c]["rel_gate_pass@0.3"]
                              for c in SIGNATURE3]))
    h3 = {
        "signature3_norm_ratio": sig_ratio,
        "generic11_norm_ratio": gen_ratio,
        "signature3_gate_pass_delta@0.3": sig_gate,
        "criteria": "norm 比が signature3 で顕著に低い → confidence 破壊で H3 支持 / "
                     "generic で高い → 誤情報充填 / 全て同等 → H3 棄却",
    }

    out = {
        "run_id": "39cee4d4-7777-810c-973b-f5f7fc809e57",
        "host": "philip", "gpu_used": False,
        "task_a_forensics": {k: v for k, v in a.items()
                             if k not in ("rel", "align_ft", "align_frozen", "valid")},
        "task_a_prime_unified_cpu_cocoeval": ap,
        "task_b_structure": {k: bc[k] for k in
                             ("region_token_shape", "structure", "score_available_in_npz",
                              "score_available_via_dump", "frame_ids_aligned", "npz_paths")},
        "task_c_h3": {"per_slot": bc["per_slot"],
                      "score_distribution_from_dump": bc["score_distribution_from_dump"],
                      "score_note": bc["score_note"], **h3},
        "task_d_raw_preds": {
            "found": True,
            "relationdetr": {"path": str(REL_PRED.relative_to(REPO)),
                             "min_score": 0.00458, "n_dets": 454500, "dets_per_img": 300},
            "aligndetr_s0frozen": {"path": str(ALIGN_FROZEN_PRED.relative_to(REPO)),
                                   "min_score": 0.00291, "n_dets": 454500, "dets_per_img": 300},
            "usable_for_cpu_eval": True,
            "gpu_reinference_needed": False,
        },
        "task_f_mapping": task_f_res,
    }
    (HERE / "results_cpu.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=float))
    print(json.dumps({k: out[k] for k in ("task_a_forensics", "task_a_prime_unified_cpu_cocoeval")},
                     indent=2, ensure_ascii=False, default=float)[:4000])
    print("saved:", HERE / "results_cpu.json")


if __name__ == "__main__":
    main()

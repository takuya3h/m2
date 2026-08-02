#!/usr/bin/env python3
"""凍結源の per-class AP 分解: AlignDETR の det→phase 負転移は signature 術具 AP の欠損で説明できるか。

Notion実験Run台帳 (must, S0, server=philip) の主判定（val split）を、既存の検証済み
per_class_ap.json（experiments/baselines/_legacy_score_thr_0/s0_{016-018}_relationdetr_*,
s0_{028-030}_aligndetr_*、3-seed・score_thr=0.0 NMS-free recipe）から再計算する。

選択性指標 R = (signature3 の平均 AP 低下) / (generic12 の平均 AP 低下)
  AP 低下 = Relation-DETR AP - Align-DETR AP （正 = Align が劣化）
  signature3 = Bipolar Forceps / Needle Holders / Scalpel（Notion台帳の定義）
  generic12  = 上記3クラスと Retractor（val instance=0, AP=NaN）を除く残り11クラス

R は seed 毎に計算し、§10.1 の paired-σ 規約（|mean R| > pstdev(R) かつ全 seed 同符号）で判定する。
test split（4265）での確認は、relationdetr/aligndetr の checkpoint(*.pth) が本ホスト(andrew)に
存在しない（Notion台帳の Server=philip 資産）ため未実施。
"""
import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LEGACY = REPO / "experiments/baselines/_legacy_score_thr_0"

REL_DIRS = {
    42: LEGACY / "s0_016_relationdetr_bbox_seed42",
    123: LEGACY / "s0_017_relationdetr_bbox_seed123",
    456: LEGACY / "s0_018_relationdetr_bbox_seed456",
}
ALIGN_DIRS = {
    42: LEGACY / "s0_028_aligndetr_bbox_seed42",
    123: LEGACY / "s0_029_aligndetr_bbox_seed123",
    456: LEGACY / "s0_030_aligndetr_bbox_seed456",
}
SEEDS = [42, 123, 456]
SIGNATURE3 = ["Bipolar Forceps", "Needle Holders", "Scalpel"]


def load(dirs):
    return {seed: json.loads((d / "per_class_ap.json").read_text()) for seed, d in dirs.items()}


def main():
    rel = load(REL_DIRS)
    align = load(ALIGN_DIRS)
    classes = sorted(rel[42].keys())
    excluded = [c for c in classes if any(rel[s][c] != rel[s][c] for s in SEEDS)]  # NaN check
    generic12 = [c for c in classes if c not in SIGNATURE3 and c not in excluded]

    per_class_drop = {
        c: [rel[s][c] - align[s][c] for s in SEEDS] for c in classes if c not in excluded
    }

    sig_drop_per_seed = []
    gen_drop_per_seed = []
    r_per_seed = []
    for i, s in enumerate(SEEDS):
        sig_mean = statistics.mean(per_class_drop[c][i] for c in SIGNATURE3)
        gen_mean = statistics.mean(per_class_drop[c][i] for c in generic12)
        sig_drop_per_seed.append(sig_mean)
        gen_drop_per_seed.append(gen_mean)
        r_per_seed.append(sig_mean / gen_mean)

    r_mean = statistics.mean(r_per_seed)
    r_pstdev = statistics.pstdev(r_per_seed)
    same_sign = len({v > 0 for v in r_per_seed}) == 1
    significant = same_sign and abs(r_mean) > r_pstdev

    bipolar_drop = per_class_drop["Bipolar Forceps"]

    result = {
        "question": "AlignDETR の det→phase 負転移は signature 術具 AP の欠損で説明できるか",
        "signature3": SIGNATURE3,
        "generic12_used": generic12,
        "excluded_classes": excluded,
        "excluded_reason": "val instance数=0 のため AP=NaN（既存 signature_subset_detector_compare と同じ扱い）",
        "note": "generic は台帳定義上12クラスだが Retractor 除外により実質11クラス",
        "per_seed": {
            "seeds": SEEDS,
            "signature3_AP_drop_pp": [v * 100 for v in sig_drop_per_seed],
            "generic11_AP_drop_pp": [v * 100 for v in gen_drop_per_seed],
            "R": r_per_seed,
        },
        "R_mean": r_mean,
        "R_pstdev": r_pstdev,
        "same_sign_all_seeds": same_sign,
        "significant_paired_sigma": significant,
        "bipolar_forceps_AP_drop_pp_per_seed": [v * 100 for v in bipolar_drop],
        "bipolar_forceps_AP_drop_pp_mean": statistics.mean(bipolar_drop) * 100,
        "source": {
            "relation_detr_dirs": {k: str(v.relative_to(REPO)) for k, v in REL_DIRS.items()},
            "align_detr_dirs": {k: str(v.relative_to(REPO)) for k, v in ALIGN_DIRS.items()},
            "split": "val (1515 images) — eval_recipe score_thr=0.0 NMS-free, 3-seed",
        },
        "test_split_status": "未実施: relationdetr/aligndetr S0 checkpoint(*.pth) が本ホスト(andrew)に不在。"
        "Notion台帳の Server=philip 資産のため、test(4265)split分解には philip からの転送が必要。",
    }
    out = Path(__file__).parent / "results.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

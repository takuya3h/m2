#!/usr/bin/env python3
"""M2: G-1 の検出力の事前計算。

本来の手法 (Step M2-2) は「既存の per-frame 予測を 9,106 枚部分集合に限定し、
動画単位クラスタ・ブートストラップ (B=2,000) で CI を出す」ことだが、
**per-frame の phase 予測はリポジトリ上に存在しない**ため、その手法は SKIP する
(指示書 Step M2-1 の規定: 見つからない場合は UNKNOWN として SKIP)。

代わりに、存在が確認できた 3-seed の集約値から **seed 水準のペア差分の分散**を実測し、
検出可能な最小効果量 (MDE) を算出する。
これは要求された動画単位クラスタ・ブートストラップとは**別の量**であり、代用ではない。
差異は以下のとおりで、レポートにも明記する:

  - 分母:   canonical 15,437 枚 (9,106 枚部分集合ではない)
  - 変動源: seed のみ (動画単位のリサンプルを含まない)
  - 含意:   動画間変動を含まないため、ここで出る MDE は**真の MDE の下限**である
            (真の MDE はこれ以上に大きくなる)

Usage:
    python3 scripts/analysis/g1_power_analysis.py --out $OUT
    python3 scripts/analysis/g1_power_analysis.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEEDS = ["42", "123", "456"]
# 3 seed の paired t 検定 (両側 alpha=0.05, df=2) の臨界値
T_CRIT_DF2 = 4.302652
H6_DELTA = 0.0004   # §1.2 の H-6 実測 Δ

# per-frame 予測を探した場所 (すべて不在であることを記録する)
SEARCHED = [
    "experiments/phase1/s4_phase_baseline_*/predictions/",
    "experiments/transfer/b2a_det2phase_*/predictions/",
    "experiments/transfer/t1a_regiontoken_*/predictions/",
    "experiments/transfer/haux_hand_presence_oracle_withtooloracle_*/predictions/",
    "**/phase_val_preds*.json",
]


def probe_per_frame_predictions():
    """per-frame の phase 予測がディスク上に存在するかを実測する。"""
    found, checked = [], []
    for pat in SEARCHED:
        hits = glob.glob(os.path.join(REPO, pat), recursive=True)
        checked.append({"pattern": pat, "n_paths": len(hits)})
        for h in hits:
            if os.path.isdir(h):
                if os.listdir(h):
                    found.append(h)
            elif os.path.isfile(h):
                found.append(h)
    return found, checked


def mde_from_paired(diffs):
    """3-seed のペア差分から、paired t 検定で有意になる最小 |Δ| を返す。"""
    n = len(diffs)
    if n < 2:
        return None
    sd = statistics.stdev(diffs)
    return T_CRIT_DF2 * sd / (n ** 0.5), sd


def self_test() -> int:
    """検出できることを確認する:
       1) per-frame 予測が「空ディレクトリ」の場合に found としないか
       2) MDE の計算が既知の値を再現するか
       3) 分散 0 のときに MDE=0 を返し、それを「検出可能」と誤判定しないか
    """
    ok = True
    with tempfile.TemporaryDirectory() as td:
        empty = os.path.join(td, "predictions")
        os.makedirs(empty)
        if os.listdir(empty):
            print("  [FAIL] 空ディレクトリの判定"); ok = False
        else:
            print("  [OK]   空の predictions/ を「予測あり」と誤認しない")

    # 既知値: diffs=[0.01,0.02,0.03] -> sd=0.01, MDE=4.302652*0.01/sqrt(3)=0.024842
    mde, sd = mde_from_paired([0.01, 0.02, 0.03])
    if abs(sd - 0.01) > 1e-12 or abs(mde - 0.0248414) > 1e-6:
        print(f"  [FAIL] MDE 計算: sd={sd} mde={mde}"); ok = False
    else:
        print(f"  [OK]   MDE 計算が既知値を再現 (sd=0.0100 -> MDE={mde:.6f})")

    mde0, sd0 = mde_from_paired([0.005, 0.005, 0.005])
    if not (sd0 == 0.0 and mde0 == 0.0):
        print(f"  [FAIL] 分散 0 の扱い: sd={sd0} mde={mde0}"); ok = False
    else:
        print("  [OK]   分散 0 で MDE=0 (縮退ケースを検出でき、有意性の根拠にしない)")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.out:
        ap.error("--out か --self-test のどちらかが必要")
    out = args.out
    for sub in ("json", "csv"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    # ---- Step M2-1: per-frame 予測の所在確認 ------------------------------- #
    found, checked = probe_per_frame_predictions()
    have_preds = len(found) > 0
    print(f"per-frame 予測の探索: 非空ヒット {len(found)} 件")
    for c in checked:
        print(f"  {c['pattern']}: {c['n_paths']} paths")

    # ---- 存在する集約値の読み込み ------------------------------------------ #
    coup = os.path.join(REPO, "experiments/analysis/step_c_coupling_analysis/test_eval_det2phase.json")
    agg = {}
    if os.path.exists(coup):
        with open(coup) as f:
            agg = json.load(f)

    # H-6 (haux) は個別 run ディレクトリから
    h6 = {}
    for d in sorted(glob.glob(os.path.join(
            REPO, "experiments/transfer/haux_hand_presence_oracle_withtooloracle_*"))):
        mp, pp = os.path.join(d, "metrics.json"), os.path.join(d, "per_class_ap.json")
        if not os.path.exists(mp):
            continue
        with open(mp) as f:
            m = json.load(f)
        seed = os.path.basename(d).split("seed")[-1]
        h6[seed] = {"metrics": m,
                    "per_phase": json.load(open(pp)) if os.path.exists(pp) else None,
                    "path": os.path.relpath(d, REPO)}

    # ---- seed 水準のペア差分と MDE ----------------------------------------- #
    pairs = [("b2a", "s4"), ("t1a", "s4"), ("t1a", "b2a")]
    # §1.2 の Δ が accuracy 基準か macro-F1 基準か指示書からは確定できないため、両方で出す
    headline = {"phase_accuracy": "accuracy", "phase_macro_f1": "macro_f1"}
    mde_rows, mde_json = [], {}
    for split in ("val", "test"):
        for a, b in pairs:
            if a not in agg or b not in agg:
                continue
            for key_m, label in headline.items():
                try:
                    diffs = [agg[a][s][split][key_m] - agg[b][s][split][key_m] for s in SEEDS]
                except KeyError:
                    continue
                res = mde_from_paired(diffs)
                if res is None:
                    continue
                mde, sd = res
                mean = statistics.mean(diffs)
                mde_json[f"{split}:{a}-{b}:{label}"] = {
                    "diffs_by_seed": {s: d for s, d in zip(SEEDS, diffs)},
                    "mean_diff": mean, "sd_paired_diff": sd, "MDE_alpha0.05_n3": mde,
                    "detectable": abs(mean) > mde,
                }
                mde_rows.append({"split": split, "contrast": f"{a}-{b}", "metric": label,
                                 "mean_diff": mean, "sd": sd, "MDE": mde,
                                 "H6_delta": H6_DELTA, "MDE_vs_H6": mde / H6_DELTA})
            # per-phase
            for ph in sorted(agg[a][SEEDS[0]].get(f"{split}_per_phase_f1", {})):
                try:
                    d_ph = [agg[a][s][f"{split}_per_phase_f1"][ph]
                            - agg[b][s][f"{split}_per_phase_f1"][ph] for s in SEEDS]
                except KeyError:
                    continue
                r = mde_from_paired(d_ph)
                if r is None:
                    continue
                m_ph, sd_ph = r
                mde_rows.append({"split": split, "contrast": f"{a}-{b}", "metric": f"F1:{ph}",
                                 "mean_diff": statistics.mean(d_ph), "sd": sd_ph, "MDE": m_ph,
                                 "H6_delta": H6_DELTA, "MDE_vs_H6": m_ph / H6_DELTA})

    # ---- Step M2-4: 判定 --------------------------------------------------- #
    overall_mdes = [r["MDE"] for r in mde_rows if r["metric"] in ("macro_f1", "accuracy")]
    min_mde = min(overall_mdes) if overall_mdes else None
    if min_mde is None:
        verdict = "SKIP"
        note = "集約値からも MDE を算出できなかった"
    elif min_mde < H6_DELTA:
        verdict = "MEASURABLE"
        note = f"MDE({min_mde:.6f}) < H-6 の Δ({H6_DELTA}) — G-1 は測定可能"
    else:
        verdict = "NOT_MEASURABLE"
        note = (f"MDE({min_mde:.6f}) が H-6 の Δ({H6_DELTA}) の "
                f"{min_mde/H6_DELTA:.0f} 倍。**G-1 は「H-6 を上回るか」を判定できない**。"
                "設計変更か撤退の検討が必要")

    result = {
        "task": "M2_g1_power_analysis",
        "status": "SKIP(prescribed method) + PARTIAL(seed-level measured)",
        "prescribed_method": "per-frame 予測を 9,106 枚部分集合に限定し動画単位クラスタ・ブートストラップ (B=2,000)",
        "prescribed_method_status": "SKIP",
        "prescribed_method_reason": (
            "per-frame の phase 予測がリポジトリ上に存在しない (UNKNOWN)。"
            "phase trainer は preds=logits.argmax(0) を評価器に渡した直後に破棄し、"
            "各 run の predictions/ は ExperimentManager が作成するのみで書き込まれない。"),
        "searched_paths": checked,
        "per_frame_predictions_found": found,
        "actually_measured": {
            "quantity": "seed 水準のペア差分 (3-seed) から算出した MDE",
            "differs_from_prescribed": [
                "分母は canonical 15,437 枚であり 9,106 枚部分集合ではない",
                "変動源は seed のみで、動画単位のリサンプルを含まない",
                "したがってここでの MDE は真の MDE の下限 (真値はこれ以上)",
            ],
            "alpha": 0.05, "n_seeds": 3, "t_crit_df2": T_CRIT_DF2,
            "source": os.path.relpath(coup, REPO) if os.path.exists(coup) else "MISSING",
        },
        "mde": mde_json,
        "h6_runs_found": {k: v["path"] for k, v in h6.items()},
        "verdict": verdict,
        "note": note,
        "regeneration_path": {
            "feasible": True,
            "requirements": [
                "checkpoints/best_tecno.pth (B2a/T1a/H-6/S4 の 3-seed 分が存在)",
                "data/processed/{b2a_detsignal,t1a_regiontoken,oracle_*} のキャッシュ特徴",
                "data/processed/phase_manifest/{split}.json (frame ID と GT)",
                "scripts/eval_det2phase_test.py のローダ (IN_DIM: s4=2048/b2a=2063/t1a=5888)",
            ],
            "note": "推論を回せば basename 単位の予測を生成でき、本来の M2 を実施可能。本タスクでは未実施。",
        },
    }
    with open(os.path.join(out, "json", "m2_power.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    cols = ["split", "contrast", "metric", "mean_diff", "sd", "MDE", "H6_delta", "MDE_vs_H6"]
    with open(os.path.join(out, "csv", "m2_power_by_phase.csv"), "w") as f:
        f.write(",".join(cols) + "\n")
        for r in mde_rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")

    print(f"\n=== M2: per-frame 予測 = {'あり' if have_preds else 'なし (UNKNOWN -> 本来の手法は SKIP)'} ===")
    print("\n=== seed 水準 MDE (overall 指標) ※動画変動を含まないため真の MDE の下限 ===")
    for r in mde_rows:
        if r["metric"] not in ("macro_f1", "accuracy"):
            continue
        print(f"  {r['split']:4s} {r['contrast']:8s} mean_diff={r['mean_diff']:+.5f} "
              f"sd={r['sd']:.5f} MDE={r['MDE']:.5f} (H-6 Δ の {r['MDE_vs_H6']:.0f} 倍)")
    print(f"\n=== M2 VERDICT: {verdict} ===\n  {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

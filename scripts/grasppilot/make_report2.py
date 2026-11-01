"""二本目の REPORT.md の表を記録から組み立てる（非公式 T-2026-11-01-grasp-pilot-g、Task G）。値は全部 report.json（aggregate2.py）から読む。

    python3 scripts/grasppilot/make_report2.py experiments/analysis/grasp_pilot_g/report.json > experiments/analysis/grasp_pilot_g/report_tables.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ARMS = ("empty", "pred_noCF", "gt", "pred_CF", "gtpred_CF", "shuffle")
C_ARMS = ("noaux", "teacher", "shuffled")


def d(x, n=4):
    return "—" if x is None else f"{x:+.{n}f}"


def v(x, n=4):
    return "—" if x is None else (f"{x:.{n}f}" if x == x else "nan")


def main():
    rep = json.loads(Path(sys.argv[1]).read_text())
    out = []
    G = rep["G"]
    out.append("### G の 3 本（val の mask mAP）\n")
    out.append("| G | 学ぶ動画 | train 枚 | 学習前 38 / 5 | 最良 epoch | 38 クラス | 把持関係 5 クラス | 評価した epoch | 学習率を下げた epoch | 所要（秒） |")
    out.append("|---|---|---:|---|---:|---:|---:|---:|---:|---:|")
    for g in ("all", "H1", "H2"):
        r = G[g]
        cfg = r["config"]
        out.append(f"| {g} | {','.join(cfg['train_videos'])} | {cfg['train_frames']} | {r['pre_segm_mAP']:.4f} / {r['pre_grasp5_mAP']:.4f} | "
                   f"{r['best_epoch']} | {r['best_segm_mAP']:.4f} | {r['best_grasp5_mAP']:.4f} | {r['epochs_completed']} | "
                   f"{r.get('lr_lowered_epoch') or '—'} | {r['elapsed_seconds']:.0f} |")
    out.append("\nepoch ごとの val（38 クラス / 把持関係 5 クラス）:\n")
    for g in ("all", "H1", "H2"):
        out.append(f"- {g}: " + "、".join(f"ep{h['epoch']} {h['segm_mAP']:.4f}/{h['grasp5_mAP']:.4f}" for h in G[g]["history"]))
    out.append("\n最良の epoch のクラス別 AP（確定の G、val に正解のあるクラス）:\n")
    out.append("| クラス | AP |")
    out.append("|---|---:|")
    for k, x in G["all"]["per_class_ap_best"].items():
        if x is not None:
            out.append(f"| {k} | {x:.4f} |")

    A = rep["case_A"]
    for fs, title in (("all", "工程注釈のある全フレーム"), ("annotated", "注釈のあるフレーム")):
        out.append(f"\n### 案 A の六腕（4 epoch 目、{title}）\n")
        out.append("| 腕 | n | Jaccard | accuracy | Δ空 J | Δ空 acc | Δ入替 J | Δ入替 acc | Δ塔 J | − 正解 J | 09 Δ空 J | 10 Δ空 J | 09 Δ空 acc | 10 Δ空 acc |")
        out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for arm in ARMS:
            r = A.get(arm)
            if not r:
                continue
            x = r[fs]
            pv = x.get("d_empty_per_video") or {}
            g = lambda k, m: (x.get(k) or {}).get(m)  # noqa: E731
            out.append(f"| {arm} | {x['n']} | {x['jaccard']:.7f} | {x['accuracy']:.7f} | {d(g('d_empty', 'jaccard'))} | {d(g('d_empty', 'accuracy'))} | "
                       f"{d(g('d_shuffle', 'jaccard'))} | {d(g('d_shuffle', 'accuracy'))} | {d(g('d_tower', 'jaccard'))} | {d(g('d_gt', 'jaccard'))} | "
                       f"{d(pv.get('09', {}).get('jaccard'))} | {d(pv.get('10', {}).get('jaccard'))} | "
                       f"{d(pv.get('09', {}).get('accuracy'))} | {d(pv.get('10', {}).get('accuracy'))} |")
    t = A["tower"]["all"]
    out.append(f"\n塔単独（全フレーム）: Jaccard {t['jaccard']:.7f}・accuracy {t['accuracy']:.7f}\n")
    out.append("クラス別 Jaccard（全フレーム）:\n")
    names = list(t["per_class_jaccard"])
    out.append("| クラス | 塔単独 | " + " | ".join(a for a in ARMS if A.get(a)) + " |")
    out.append("|---|---:|" + "---:|" * sum(1 for a in ARMS if A.get(a)))
    for n in names:
        out.append(f"| {n} | {t['per_class_jaccard'][n]:.4f} | " +
                   " | ".join(f"{A[a]['all']['per_class_jaccard'][n]:.4f}" for a in ARMS if A.get(a)) + " |")
    out.append("\n界面の重みの絶対値の最大（epoch 1〜4）:\n")
    for a in ARMS:
        if A.get(a):
            out.append(f"- {a}: " + "、".join(f"{h['iface_max_abs']:.6f}" for h in A[a]["history"]) +
                       f"（学習の壁時計 {A[a]['elapsed_seconds']:.2f} 秒、記録との一致 {A[a]['recompute_matches_record']}）")

    B = rep["case_B"]
    out.append("\n### 案 B の六腕（4 epoch 目）\n")
    out.append("| 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | Δ空 mAP | Δ空 標的 | Δ空 陰性 | Δ入替 mAP | Δ入替 標的 | Δ塔 標的 | − 正解 標的 | 09 Δ空 | 10 Δ空 |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for arm in ARMS:
        r = B.get(arm)
        if not r:
            continue
        g = lambda k, m: (r.get(k) or {}).get(m)  # noqa: E731
        pv = r.get("d_empty_per_video") or {}
        out.append(f"| {arm} | {r['AP']:.7f} | {r['target_AP']:.7f} | {r['control_AP']:.7f} | {d(g('d_empty', 'AP'))} | {d(g('d_empty', 'target_AP'))} | "
                   f"{d(g('d_empty', 'control_AP'))} | {d(g('d_shuffle', 'AP'))} | {d(g('d_shuffle', 'target_AP'))} | {d(g('d_tower', 'target_AP'))} | "
                   f"{d(g('d_gt', 'target_AP'))} | {d(pv.get('09'))} | {d(pv.get('10'))} |")
    tb = B["tower"]
    out.append(f"\n塔単独: mAP {tb['AP']:.7f}、標的群 {tb['target_AP']:.7f}、陰性対照群 {tb['control_AP']:.7f}。"
               f"全腕で code_sha256 が同じ: {B.get('code_identical_across_arms')}\n")
    out.append("epoch ごとの val mAP と界面の重みの L2:\n")
    for arm in ARMS:
        r = B.get(arm)
        if r:
            pe = r["per_epoch_mAP"]
            iw = r["iface_weight_by_epoch"]
            out.append(f"- {arm}: " + "、".join(f"ep{k} {pe[k]:.4f}（L2 {iw[k]['iface_l2']:.2f}）" for k in sorted(pe, key=int)) +
                       f"、凍結部の一致 {r['frozen_unchanged']}")
    out.append("\nクラス別 AP:\n")
    arms_b = [a for a in ARMS if B.get(a)]
    out.append("| クラス | " + " | ".join(arms_b) + " |")
    out.append("|---|" + "---:|" * len(arms_b))
    for n in B[arms_b[0]]["per_class_ap"]:
        out.append(f"| {n} | " + " | ".join(v(B[a]["per_class_ap"][n]) for a in arms_b) + " |")

    Cc = rep["case_C"]
    out.append("\n### 案 C の 3 腕（時間ヘッドの最後の状態）\n")
    out.append("| 腕 | Jaccard | accuracy | 09 J | 10 J | 09 acc | 10 acc | fine-tune 最後の val acc | 補助の頭の val CE（左 / 右 / 両手） |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for a in C_ARMS:
        r = Cc["arms"].get(a)
        if not r:
            continue
        pv = r["per_video"]
        av = r.get("aux_val")
        ce = " / ".join(f"{av['ce_per_hand'][h]:.4f}" for h in ("left", "right", "both")) if av else "—"
        out.append(f"| {a} | {r['jaccard']:.7f} | {r['accuracy']:.7f} | {pv['09']['jaccard']:.4f} | {pv['10']['jaccard']:.4f} | "
                   f"{pv['09']['accuracy']:.4f} | {pv['10']['accuracy']:.4f} | {r['finetune']['last_val_accuracy']:.4f} | {ce} |")
    out.append("\n（一様の標的に対する CE は 2.7726 = ln 16）\n")
    out.append("| 差 | Jaccard | accuracy | 09 J | 10 J |")
    out.append("|---|---:|---:|---:|---:|")
    for k, lab in (("teacher_minus_noaux", "G を教師 − 補助損失なし（Δ教師）"), ("shuffled_minus_noaux", "入れ替えた教師 − 補助損失なし"),
                   ("teacher_minus_shuffled", "G を教師 − 入れ替えた教師")):
        x = Cc.get(k)
        if x:
            out.append(f"| {lab} | {d(x['jaccard'])} | {d(x['accuracy'])} | {d(x['per_video']['09']['jaccard'])} | {d(x['per_video']['10']['jaccard'])} |")
    out.append("\nクラス別 Jaccard:\n")
    arms_c = [a for a in C_ARMS if Cc["arms"].get(a)]
    out.append("| クラス | " + " | ".join(arms_c) + " |")
    out.append("|---|" + "---:|" * len(arms_c))
    for n in Cc["arms"][arms_c[0]]["per_class_jaccard"]:
        out.append(f"| {n} | " + " | ".join(f"{Cc['arms'][a]['per_class_jaccard'][n]:.4f}" for a in arms_c) + " |")
    out.append("\nfine-tune の epoch ごとの補助損失（重みを掛ける前）と val accuracy:\n")
    for a in arms_c:
        h = Cc["arms"][a]["finetune_history"]
        out.append(f"- {a}: " + "、".join(f"ep{x['epoch']} {x['train_aux_loss']:.3f}/{x['val_accuracy']:.3f}" for x in h))
    print("\n".join(out))


if __name__ == "__main__":
    main()

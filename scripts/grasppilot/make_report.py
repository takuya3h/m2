"""REPORT.md の表を記録から組み立てる（非公式 T-2026-10-31-grasp-pilot-probe、Task F）。値は全部 json の記録から読む。

    python3 scripts/grasppilot/make_report.py [report.json] > experiments/analysis/grasp_pilot_probe/report_tables.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[2] / "experiments/analysis/grasp_pilot_probe"
S = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe")


def f(x, n=4):
    return "—" if x is None else (f"{x:+.{n}f}" if isinstance(x, float) and x < 0 else f"{x:.{n}f}")


def d(x, n=7):
    return "—" if x is None else f"{x:+.{n}f}"


def main():
    rep = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else R / "report.json").read_text())
    A, B = rep["case_A"], rep.get("case_B", {})
    out = []
    out.append("### 案 A の腕（4 epoch 目）\n")
    out.append("| 腕 | フレーム | Jaccard | accuracy | Δ空 J | Δ空 acc | Δ塔 J | Δ塔 acc | 09 Δ空 J | 10 Δ空 J | 09 Δ空 acc | 10 Δ空 acc |")
    out.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for arm in ("empty", "gt"):
        for fs in ("all", "annotated"):
            r = A[arm][fs]
            pv = r["d_empty_per_video"]
            out.append(f"| {arm} | {fs}（{r['n']}） | {r['jaccard']:.7f} | {r['accuracy']:.7f} | {d(r['d_empty']['jaccard'])} | "
                       f"{d(r['d_empty']['accuracy'])} | {d(r['d_tower']['jaccard'])} | {d(r['d_tower']['accuracy'])} | "
                       f"{d(pv['09']['jaccard'])} | {d(pv['10']['jaccard'])} | {d(pv['09']['accuracy'])} | {d(pv['10']['accuracy'])} |")
    t = A["tower"]
    out.append(f"\n塔単独: all Jaccard {t['all']['jaccard']:.7f}・accuracy {t['all']['accuracy']:.7f}（動画 09 {t['all']['per_video']['09']['jaccard']:.7f}、"
               f"10 {t['all']['per_video']['10']['jaccard']:.7f}）、annotated {t['annotated']['jaccard']:.7f}・{t['annotated']['accuracy']:.7f}\n")
    out.append("クラス別 Jaccard（全フレーム）:\n")
    names = list(t["all"]["per_class_jaccard"])
    out.append("| クラス | 塔単独 | 空 | 正解 | 正解 − 空 |")
    out.append("|---|---:|---:|---:|---:|")
    for n in names:
        e, g = A["empty"]["all"]["per_class_jaccard"][n], A["gt"]["all"]["per_class_jaccard"][n]
        out.append(f"| {n} | {t['all']['per_class_jaccard'][n]:.4f} | {e:.4f} | {g:.4f} | {g - e:+.4f} |")
    out.append("\n界面の重み（epoch ごと、絶対値の最大 / L2）:\n")
    for arm in ("empty", "gt"):
        out.append(f"- {arm}: " + "、".join(f"ep{h['epoch']} {h['iface_max_abs']:.6f} / {h['iface_l2']:.6f}" for h in A[arm]["history"])
                   + f"（学習の壁時計 {A[arm]['elapsed_seconds']:.2f} 秒）")
    if B.get("empty") and B.get("gt"):
        out.append("\n### 案 B の腕（4 epoch 目）\n")
        out.append("| 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | Δ空 mAP | Δ空 標的 | Δ空 陰性 | Δ塔 mAP | Δ塔 標的 | Δ塔 陰性 | 09 Δ空 | 10 Δ空 |")
        out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for arm in ("empty", "gt"):
            r = B[arm]
            out.append(f"| {arm} | {r['AP']:.7f} | {r['target_AP']:.7f} | {r['control_AP']:.7f} | {d(r['d_empty']['AP'])} | "
                       f"{d(r['d_empty']['target_AP'])} | {d(r['d_empty']['control_AP'])} | {d(r['d_tower']['AP'])} | "
                       f"{d(r['d_tower']['target_AP'])} | {d(r['d_tower']['control_AP'])} | {d(r['d_empty_per_video']['09'])} | "
                       f"{d(r['d_empty_per_video']['10'])} |")
        tb = B["tower"]
        out.append(f"\n塔単独: mAP {tb['AP']:.7f}、標的群 {tb['target_AP']:.7f}、陰性対照群 {tb['control_AP']:.7f}、動画 09 {tb['per_video_AP']['09']:.7f}・10 {tb['per_video_AP']['10']:.7f}\n")
        for arm in ("empty", "gt"):
            r = B[arm]
            out.append(f"- {arm}: epoch ごとの val mAP {r['per_epoch_mAP']}、界面の重み {r['iface_weight_by_epoch']}、凍結部の一致 {r['frozen_unchanged']}、"
                       f"起動 {r['start_utc']}・終了 {r['end_utc']}")
        out.append("\nクラス別 AP:\n")
        out.append("| クラス | 空 | 正解 | 正解 − 空 |")
        out.append("|---|---:|---:|---:|")
        for n, e in B["empty"]["per_class_ap"].items():
            g = B["gt"]["per_class_ap"][n]
            out.append(f"| {n} | {f(e)} | {f(g)} | {(g - e):+.4f} |" if e == e and g == g else f"| {n} | {e} | {g} | — |")
    c4 = json.loads((R / "taskC/c4_error_count.json").read_text())
    out.append("\n### C-4 誤りの数え上げ（全表）\n")
    for key, tab in c4["tables"].items():
        out.append(f"\n**{key}**\n")
        out.append("| 群 | 状態 | n | 正しい | 取り違え | 見逃し | 取り違えの割合 | 見逃しの割合 |")
        out.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for g, rows in tab.items():
            for st, r in rows.items():
                if st == "summary":
                    continue
                out.append(f"| {g} | {st} | {r['n']} | {r['correct']} | {r['confused']} | {r['missed']} | {f(r['confused_rate'])} | {f(r['missed_rate'])} |")
        out.append("")
        out.append("| 群 | 枠 | 誤り | 握られている枠が誤りに占める割合 | 全枠に占める割合 |")
        out.append("|---|---:|---:|---:|---:|")
        for g, rows in tab.items():
            s = rows["summary"]
            out.append(f"| {g} | {s['n_boxes']} | {s['n_errors']} | {f(s['held_share_of_errors'])} | {f(s['held_share_of_boxes'])} |")
    print("\n".join(out))


if __name__ == "__main__":
    main()

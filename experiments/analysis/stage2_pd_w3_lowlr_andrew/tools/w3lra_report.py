"""Task D: 集計（w3lra_aggregate.py の report.json）から REPORT.md の表を作る（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew）。

前回の andrew の scripts/w23/w23a_report.py の写し。型を 4 つにし、前回の W3（1e-4）と W2 の参考の表を足した。
数値はすべて report.json から写す（手で書かない）。出力は標準出力の Markdown。

    python w3lra_report.py <report.json> > experiments/analysis/stage2_pd_w3_lowlr_andrew/report_tables.md
"""
from __future__ import annotations

import json
import sys

TYPES = ("P1", "P2L", "P3", "DX")
ARMS = ("empty", "pred_noCF", "gt", "shuffle")
ARM_JA = {"empty": "空", "pred_noCF": "予測-noCF", "gt": "正解", "shuffle": "入れ替え"}
TYPE_JA = {"P1": "P1（FiLM）", "P2L": "P2L", "P3": "P3", "DX": "DX（decoder-xattn）"}
KEYS = ("AP", "target_AP", "control_AP", "AP50")
KEY_JA = {"AP": "overall mAP", "target_AP": "標的群 AP", "control_AP": "陰性対照群 AP", "AP50": "AP50"}


def f(x, sign=False):
    if x is None:
        return "UNKNOWN"
    return f"{x:+.4f}" if sign else f"{x:.4f}"


def main_table(rows):
    out = ["| 腕 | 指標 | 4 epoch 目 | Δ空 | Δ入替 | Δ塔 |", "|---|---|---:|---:|---:|---:|"]
    for a in ARMS:
        r = rows[a]
        if not r.get("measured", True):
            out.append(f"| {ARM_JA[a]} | — | UNKNOWN（{r['reason']}） | | | |")
            continue
        for i, k in enumerate(KEYS):
            de, ds, dt = (r.get(n) or {} for n in ("d_empty", "d_shuffle", "d_tower"))
            out.append(f"| {ARM_JA[a] if i == 0 else ''} | {KEY_JA[k]} | {f(r[k])} | {f(de.get(k), True)} | "
                       f"{f(ds.get(k), True)} | {f(dt.get(k), True)} |")
    return out


def video_table(rows):
    out = ["| 腕 | 基準 | 動画 09 | 動画 10 |", "|---|---|---:|---:|"]
    for a in ARMS:
        r = rows[a]
        if not r.get("measured", True):
            continue
        for base, ja in (("empty", "空"), ("shuffle", "入れ替え"), ("tower", "塔単独")):
            v = (r.get("per_video_d") or {}).get(base)
            if v is None or (base == "empty" and a == "empty") or (base == "shuffle" and a == "shuffle"):
                continue
            out.append(f"| {ARM_JA[a]} | {ja} | {f(v['09'], True)} | {f(v['10'], True)} |")
    return out


def epoch_table(rows):
    out = ["| 腕 | 指標 | 学習前 | epoch 1 | epoch 2 | epoch 3 | epoch 4 |", "|---|---|---:|---:|---:|---:|---:|"]
    for a in ARMS:
        r = rows[a]
        if not r.get("measured", True):
            continue
        pe = r["per_epoch"]
        for i, k in enumerate(("AP", "target_AP", "control_AP")):
            out.append(f"| {ARM_JA[a] if i == 0 else ''} | {KEY_JA[k]} | " + " | ".join(f(pe[str(e)][k]) for e in range(-1, 4)) + " |")
    return out


def lr_table(rows):
    out = ["| 腕 | 群の学習率（epoch 1〜4 で同じ値か） | other | backbone | linear_projection | other_norm | phase（界面） |",
           "|---|---|---:|---:|---:|---:|---:|"]
    for a in ARMS:
        r = rows[a]
        if not r.get("measured", True):
            continue
        be = r["lr_record"]["by_epoch"]
        same = len({json.dumps(v, sort_keys=True) for v in be.values()}) == 1
        v = next(iter(be.values()))
        out.append(f"| {ARM_JA[a]} | {'同じ' if same else '違う'}（{len(be)} epoch） | " +
                   " | ".join(f"{v[k]:.0e}" if k in v else "—" for k in ("other", "backbone", "linear_projection", "other_norm", "phase")) + " |")
    return out


def class_table(rows, tower):
    out = ["| クラス | 塔単独 | " + " | ".join(ARM_JA[a] for a in ARMS) + " |", "|---|---:|" + "---:|" * len(ARMS)]
    for c in tower["per_class_ap"]:
        t = tower["per_class_ap"][c]
        vals = []
        for a in ARMS:
            r = rows[a]
            v = r.get("per_class_ap", {}).get(c) if r.get("measured", True) else None
            vals.append("UNKNOWN" if v is None else ("NaN" if v != v else f"{v:.4f}"))
        out.append(f"| {c} | {'NaN' if t != t else f'{t:.4f}'} | " + " | ".join(vals) + " |")
    return out


def cost_table(rows):
    out = ["| 腕 | 所要（時間） | 学ぶ要素 | 受け取り手の動いた量（相対） | ホスト |", "|---|---:|---:|---:|---|"]
    for a in ARMS:
        r = rows[a]
        if not r.get("measured", True):
            continue
        out.append(f"| {ARM_JA[a]} | {r['wall_seconds'] / 3600:.2f} | {r['total_trainable']:,} | {r['receiver_rel_delta']:.4f} | {r['server']} |")
    return out


def prev_compare(rep):
    """前回の W3（1e-4）と本契約（1e-5）の並べ。どちらも各 run の記録から計算した値。"""
    out = ["| 型 | 量 | 前回の W3（1e-4） overall / 標的群 | 本契約（1e-5） overall / 標的群 | 前回の run（ホスト） |",
           "|---|---|---|---|---|"]
    items = (("空の腕の Δ塔", "empty", "d_tower"), ("正解の Δ空", "gt", "d_empty"), ("予測-noCF の Δ空", "pred_noCF", "d_empty"),
             ("予測-noCF の Δ入替", "pred_noCF", "d_shuffle"), ("正解の Δ入替", "gt", "d_shuffle"))
    for t in TYPES:
        for i, (ja, arm, dk) in enumerate(items):
            p, n = rep["prev_W3"][t][arm], rep["tables"][t][arm]
            src = f"{p['run'].rsplit('_' + arm, 1)[0]}_*（{p.get('server') or 'UNKNOWN'}）" if i == 0 else ""
            out.append(f"| {TYPE_JA[t] if i == 0 else ''} | {ja} | {f(p[dk]['AP'], True)} / {f(p[dk]['target_AP'], True)} | "
                       f"{f(n[dk]['AP'], True)} / {f(n[dk]['target_AP'], True)} | {src} |")
    return out


def prev_values(rep):
    out = ["| 型 | 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | AP50 | 出所 |", "|---|---|---:|---:|---:|---:|---|"]
    for t in TYPES:
        for a in ARMS:
            p = rep["prev_W3"][t][a]
            out.append(f"| {TYPE_JA[t] if a == 'empty' else ''} | {ARM_JA[a]} | {f(p['AP'])} | {f(p['target_AP'])} | {f(p['control_AP'])} | "
                       f"{f(p['AP50'])} | `{p['source']}` |")
    return out


def w2_table(rep):
    out = ["| 型 | 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | Δ空 overall / 標的群 | Δ入替 overall / 標的群 | Δ塔 overall / 標的群 | 出所 |",
           "|---|---|---:|---:|---:|---|---|---|---|"]
    for t in TYPES:
        w2 = rep["W2_reference"][t]
        if w2["rows"] is None:
            out.append(f"| {TYPE_JA[t]} | — | — | — | — | — | — | — | {w2['source']} |")
            continue
        for a in ARMS:
            r = w2["rows"][a]
            src = r.get("source") or ""
            out.append(f"| {TYPE_JA[t] if a == 'empty' else ''} | {ARM_JA[a]} | {f(r['AP'])} | {f(r['target_AP'])} | {f(r['control_AP'])} | "
                       f"{f(r['d_empty']['AP'], True)} / {f(r['d_empty']['target_AP'], True)} | "
                       f"{f(r['d_shuffle']['AP'], True)} / {f(r['d_shuffle']['target_AP'], True)} | "
                       f"{f(r['d_tower']['AP'], True)} / {f(r['d_tower']['target_AP'], True)} | `{src}` |")
    return out


def main():
    rep = json.loads(open(sys.argv[1]).read())
    L = ["<!-- 生成: experiments/analysis/stage2_pd_w3_lowlr_andrew/tools/w3lra_report.py（数値はすべて report.json から） -->", ""]
    tw = rep["tower"]
    L += [f"塔単独（Task B-2 の再現）: overall mAP {f(tw['AP'])}、標的群 AP {f(tw['target_AP'])}、陰性対照群 AP {f(tw['control_AP'])}、"
          f"AP50 {f(tw['AP50'])}、動画 09 {f(tw['per_video_AP']['09'])}・10 {f(tw['per_video_AP']['10'])}", ""]
    L += ["## A. 前回の W3（1e-4）との並べ（参考。1 本ずつの差）", "", *prev_compare(rep), "",
          "## B. 型ごとの値（4 epoch 目、val の動画 09・10）", ""]
    for t in TYPES:
        rows = rep["tables"][t]
        L += [f"### {TYPE_JA[t]} W3（受け取り手 1e-5）", "", *main_table(rows), "", "動画ごとの差（overall mAP）", "", *video_table(rows), "",
              "epoch ごとの val（epoch は 1 始まり。学習前は塔単独と同じ）", "", *epoch_table(rows), "",
              "群の学習率（記録 lr_groups.json。比 0.1 の群は backbone・backbone_norm・linear_projection・linear_projection_norm）", "",
              *lr_table(rows), "", "所要・学ぶ要素・受け取り手の動いた量", "", *cost_table(rows), "",
              "クラス別 AP（4 epoch 目）", "", *class_table(rows, tw), ""]
    L += ["## C. 参考: 前回の W3（1e-4）の値（各 run の記録から）", "", *prev_values(rep), "",
          "## D. 参考: W2 の値（前回の記録から。ホストが違う値は処置の差として読まない）", "", *w2_table(rep), ""]
    print("\n".join(L))


if __name__ == "__main__":
    main()

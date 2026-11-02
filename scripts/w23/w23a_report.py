"""Task E: 集計（w23a_aggregate.py の report.json）から REPORT.md の表を作る（非公式 T-2026-11-01-stage2-w23-andrew）。

数値はすべて report.json から写す（手で書かない）。出力は標準出力の Markdown。

    python scripts/w23/w23a_report.py <report.json> > experiments/analysis/stage2_w23_andrew/report_tables.md
"""
from __future__ import annotations

import json
import sys

ARMS = ("empty", "pred_noCF", "gt", "shuffle")
ARM_JA = {"empty": "空", "pred_noCF": "予測-noCF", "gt": "正解", "shuffle": "入れ替え"}
TYPE_JA = {"DX": "decoder-xattn（工程から検出）", "B": "案 B（把持の地図を C5 に足す型）"}
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


def class_table(rows, tower):
    classes = [c for c in tower["per_class_ap"]]
    out = ["| クラス | 塔単独 | " + " | ".join(ARM_JA[a] for a in ARMS) + " |", "|---|---:|" + "---:|" * len(ARMS)]
    for c in classes:
        t = tower["per_class_ap"][c]
        vals = []
        for a in ARMS:
            r = rows[a]
            v = r.get("per_class_ap", {}).get(c) if r.get("measured", True) else None
            vals.append("UNKNOWN" if v is None else ("NaN" if v != v else f"{v:.4f}"))
        out.append(f"| {c} | {'NaN' if t != t else f'{t:.4f}'} | " + " | ".join(vals) + " |")
    return out


def cost_table(rows):
    out = ["| 腕 | 所要（時間） | 学ぶ要素 | 受け取り手の動いた量（相対） | 4 epoch 目のゲート・界面の重み | ホスト |", "|---|---:|---:|---:|---|---|"]
    for a in ARMS:
        r = rows[a]
        if not r.get("measured", True):
            continue
        g = r.get("gates_last") or {}
        gs = ", ".join(f"{k}=" + (str([round(x, 4) for x in v]) if isinstance(v, list) else f"{v:.4g}") for k, v in g.items())
        out.append(f"| {ARM_JA[a]} | {r['wall_seconds'] / 3600:.2f} | {r['total_trainable']:,} | {r['receiver_rel_delta']:.4f} | {gs or '—'} | {r['server']} |")
    return out


def w_compare(rep):
    out = ["| 型 | W | ホスト | 正解 Δ空（mAP） | 正解 Δ空（標的群） | 予測-noCF Δ空（mAP） | 正解 Δ入替（mAP） | 空 Δ塔（mAP） | 出所 |",
           "|---|---|---|---:|---:|---:|---:|---:|---|"]
    for t in ("DX", "B"):
        tabs = [("W1", rep["w1"][t])] + [(w, rep["tables"][f"{t}-{w}"]) for w in ("W2", "W3")]
        for w, rows in tabs:
            g, p, e = rows["gt"], rows["pred_noCF"], rows["empty"]
            src = "前の契約の run（" + rows["gt"]["run"].rsplit("_gt", 1)[0] + "_*）" if w == "W1" else "本契約"
            host = rows["gt"].get("server", "UNKNOWN")
            out.append(f"| {t} | {w} | {host} | {f((g.get('d_empty') or {}).get('AP'), True)} | {f((g.get('d_empty') or {}).get('target_AP'), True)} | "
                       f"{f((p.get('d_empty') or {}).get('AP'), True)} | {f((g.get('d_shuffle') or {}).get('AP'), True)} | "
                       f"{f((e.get('d_tower') or {}).get('AP'), True)} | {src} |")
    p1 = rep["p1_reference"]
    for typ in ("P1-W1", "P1-W2"):
        rows = p1[typ]
        de = lambda a, k: (rows.get(a, {}).get("delta_empty") or {}).get(k)  # noqa: E731
        hosts = "・".join(sorted({r.get("server") or "UNKNOWN" for r in rows.values()}))
        out.append(f"| P1（参考） | {typ[-2:]} | {hosts} | {f(de('gt', 'AP'), True)} | {f(de('gt', 'target_AP'), True)} | "
                   f"{f(de('pred_noCF', 'AP'), True)} | — | — | 直しの契約の report.json（{typ}） |")
    return out


def main():
    rep = json.loads(open(sys.argv[1]).read())
    L = ["<!-- 生成: scripts/w23/w23a_report.py（数値はすべて report.json から） -->", ""]
    tw = rep["tower"]
    L += [f"塔単独（Task B-2 の再現）: overall mAP {f(tw['AP'])}、標的群 AP {f(tw['target_AP'])}、陰性対照群 AP {f(tw['control_AP'])}、"
          f"AP50 {f(tw['AP50'])}、動画 09 {f(tw['per_video_AP']['09'])}・10 {f(tw['per_video_AP']['10'])}", ""]
    for t in ("DX", "B"):
        for w in ("W2", "W3"):
            rows = rep["tables"][f"{t}-{w}"]
            L += [f"### {TYPE_JA[t]} {w}", "", *main_table(rows), "", "動画ごとの差（overall mAP）", "", *video_table(rows), "",
                  "epoch ごとの val（epoch は 1 始まり。学習前は塔単独と同じ）", "", *epoch_table(rows), "",
                  "所要・学ぶ要素・受け取り手の動いた量", "", *cost_table(rows), "",
                  "クラス別 AP（4 epoch 目）", "", *class_table(rows, tw), ""]
    L += ["### W1・W2・W3 の並べ（参考。W1 は前の契約の run。§6.2 規則 2: 処置の差として読まない）", "", *w_compare(rep), ""]
    print("\n".join(L))


if __name__ == "__main__":
    main()

"""RESULT.md の「実測」の表を記録から作る（非公式 T-2026-11-22-dtower-class-error-breakdown）。手で写さない。

    .venv/bin/python .../result_tables.py   → d/result_tables.md

読むもの: summary.json、c/tables.json、c/fix_<塔>_<Fold>.json、c/decomp_<塔>_<Fold>.json、b/b_repro.json。
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

OUTDIR = C.OUT


def load(p):
    return json.loads((OUTDIR / p).read_text())


def pct(n, d):
    return "—" if not d else f"{100 * n / d:.1f}"


def f4(x):
    return "nan" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.4f}"


def s4(x):
    return "UNKNOWN" if x is None else ("nan" if math.isnan(x) else f"{x:+.4f}")


def main():
    s = load("summary.json")
    tab = load("c/tables.json")
    b = load("b/b_repro.json")
    keys = s["targets"]
    head = "| クラス | " + " | ".join(k.replace("T1_", "塔1 ").replace("T2_", "塔2 ") for k in keys) + " |"
    sep = "|---|" + "---|" * len(keys)
    L = []
    w = L.append
    w("GT の側・読み 1（正解 / 取り違え / 位置のずれ / 見落とし の %、括弧は GT の数。REPORT §2）")
    w("")
    w(head)
    w(sep)
    for c in s["focus"]:
        cells = []
        for k in keys:
            g = s["gt"][k][c]
            n = g["n"]
            cells.append("—（0）" if not n else "/".join(pct(g["r1"][x], n) for x in ("correct", "confusion", "localization", "missed"))
                         + f"（{n}）")
        w(f"| {c} | " + " | ".join(cells) + " |")
    w("")
    w("GT の側・読み 2（正解 / 取り違え の %。位置のずれと見落としは読み 1 と同じ）と、取り違えの相手の上位 2（件数。読み 1 ／ 読み 2。REPORT §3）")
    w("")
    w(head)
    w(sep)
    for c in s["focus"]:
        cells = []
        for k in keys:
            g = s["gt"][k][c]
            n = g["n"]
            if not n:
                cells.append("—")
                continue
            p = s["partners"][k][c]
            part = " ／ ".join("、".join(f"{t['class']} {t['count']}" for t in p[r]) or "なし" for r in ("r1", "r2"))
            cells.append(f"{pct(g['r2']['correct'], n)}/{pct(g['r2']['confusion'], n)}: {part}")
        w(f"| {c} | " + " | ".join(cells) + " |")
    w("")
    w("予測の側（当たり / 重複 / 取り違え / 位置のずれ / 背景 / その他 の %、括弧は score 0.05 以上の予測の数。REPORT §4）")
    w("")
    w(head)
    w(sep)
    for c in s["focus"]:
        cells = []
        for k in keys:
            p = s["pred"][k][c]
            n = p["n"]
            cells.append("/".join(pct(p[x], n) for x in ("hit", "duplicate", "confusion", "localization", "background", "other"))
                         + f"（{n}）")
        w(f"| {c} | " + " | ".join(cells) + " |")
    w("")
    w("AP / AP50 / AP75（REPORT §5）")
    w("")
    w(head)
    w(sep)
    for c in s["focus"]:
        w(f"| {c} | " + " | ".join("/".join(f4(s["ap"][k][c][m]) for m in ("AP", "AP50", "AP75")) for k in keys) + " |")
    w("")
    w("五つの直し方の AP の差 Δ(a)/Δ(b)/Δ(c)/Δ(d)/Δ(e)（直した後 − 直す前。REPORT §6）")
    w("")
    w(head)
    w(sep)
    for c in s["focus"]:
        w(f"| {c} | " + " | ".join("/".join(s4(s["fix"][k][c][f]) for f in "abcde") for k in keys) + " |")
    for g, ja in (("all", "平均・全クラス"), ("signature", "平均・signature"), ("negative", "平均・negative"), ("other", "平均・その他")):
        w(f"| {ja} | " + " | ".join("/".join(s4(s["fix_means"][k][g][f]) for f in "abcde") for k in keys) + " |")
    w("")
    w("Fold ごとの 4 クラス（train の box / 動画、val の box / 動画、塔 1 の AP / AP50。REPORT §7）")
    w("")
    w("| クラス | " + " | ".join(f"Fold {f}" for f in "ABCDE") + " |")
    w("|---|" + "---|" * 5)
    for c in C.FOCUS:
        cells = []
        for f in "ABCDE":
            x = tab["folds"][f]
            e = load(f"b/eval_T1_{f}.json")["per_class"][c]
            cells.append(f"{x['train']['boxes'][c]}/{x['train']['videos'][c]}、{x['val']['boxes'][c]}/{x['val']['videos'][c]}、"
                         f"{f4(e['AP'])}/{f4(e['AP50'])}")
        w(f"| {c} | " + " | ".join(cells) + " |")
    w("")
    t = s["ties_total"]
    w("読み 1 で IoU が同じ予測が複数あった GT（全クラスの計。最大の IoU > 0 / ≥ 0.5 / そのうちクラスが一つでない / score も同じ）: "
      + "、".join(f"{k} {'/'.join(str(v) for v in t[k])}" for k in keys))
    w("再現の差の最大: " + "、".join(f"{k} {b['targets'][k]['max_abs_diff']:.1e}" for k in keys))
    (OUTDIR / "d/result_tables.md").write_text("\n".join(L) + "\n")
    print(len(L), "lines")


if __name__ == "__main__":
    main()

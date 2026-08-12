#!/usr/bin/env python3
"""hires(Method C) 3-way phase 比較の集計（phase-seed 平均）。

logs/hires_probe_results.tsv （列: tag, phase_seed, method, exp_dir）を読み、
(method, tag) ごとに phase_seed を平均。frozen / augstrong(A) / hires(C) を並べ、
Δ(A−frozen) / Δ(C−frozen) / Δ(C−A) を出す。

使い方: python3 scripts/report_hires_probe.py [results.tsv]
"""
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
RES = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJ / "logs/hires_probe_results.tsv"
LABEL = {
    "relation_detr_seed42": "frozen",
    "relation_detr_augstrong_seed42": "augA",
    "relation_detr_augstrong_hires_seed42": "hiresC",
}
ORDER = ["frozen", "augA", "hiresC"]


def load_metric(d):
    try:
        m = json.load(open(Path(d.strip()) / "metrics.json"))
        return m.get("phase_accuracy"), m.get("phase_macro_f1")
    except Exception:
        return None, None


def main():
    if not RES.exists():
        print(f"[ERR] 無い: {RES}"); return
    cells = defaultdict(lambda: defaultdict(list))  # [method][label] = [(acc,f1)]
    for line in RES.read_text().splitlines():
        p = line.split("\t")
        if len(p) < 4:
            continue
        tag, ps, method, d = p[0], p[1], p[2], p[3]
        lab = LABEL.get(tag, tag)
        acc, f1 = load_metric(d)
        if acc is not None:
            cells[method][lab].append((acc, f1))

    print(f"=== hires(Method C) 3-way phase 比較（phase-seed平均, {RES.name}）===")
    print("frozen(源) / augA(強aug) / hiresC(強aug+高解像) の acc, F1 と Δ(vs frozen)\n")
    for method in ("S4", "B2a", "T1a"):
        if method not in cells:
            continue
        m = {}
        for lab in ORDER:
            vals = cells[method].get(lab, [])
            if vals:
                m[lab] = (st.mean(v[0] for v in vals), st.mean(v[1] for v in vals), len(vals))
        print(f"[{method}]")
        for lab in ORDER:
            if lab in m:
                a, f, n = m[lab]
                print(f"  {lab:7s}: acc={a:.4f}  F1={f:.4f}  (n={n})")
        if "frozen" in m:
            fa, ff, _ = m["frozen"]
            for lab in ("augA", "hiresC"):
                if lab in m:
                    a, f, _ = m[lab]
                    print(f"    Δ({lab}−frozen): acc={(a-fa)*100:+.2f}pp  F1={(f-ff)*100:+.2f}pp")
        if "augA" in m and "hiresC" in m:
            aa, af, _ = m["augA"]; ca, cf, _ = m["hiresC"]
            print(f"    Δ(hiresC−augA): acc={(ca-aa)*100:+.2f}pp  F1={(cf-af)*100:+.2f}pp  ← 高解像度の上乗せ")
        print()


if __name__ == "__main__":
    main()

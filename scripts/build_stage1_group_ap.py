#!/usr/bin/env python
"""検出塔の標的群 AP と陰性対照群 AP を per-class AP から計算する。契約 T-2026-09-27-stage2-prep / Task C。

**再評価しない。** 既存の評価の出力から計算する。

    群の定義     : context/conventions.md の det_groups 節の表（ここから読む。手で書かない）
    per-class AP : experiments/baselines/stage1_dtower{,_r2}/<run>/eval_{val,test}.json
    クラス名     : data/annotations/egosurgery_tool_folds/<折り>/instances_{val,test}.json（読むだけ）

群 AP は群のクラスの AP の平均。**評価集合に出現しないクラス（AP が NaN）は除き、除いたことを記録する。
0 で埋めない。** NaN が注釈上の欠落と一致することも照合する（一致しなければ止まる）。

出力: docs/stage1/D_group_ap.md と experiments/baselines/stage1_dtower_r2/group_ap.json
"""
from __future__ import annotations

import json
import math
import re
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONVENTIONS = REPO / "context/conventions.md"
ANN = REPO / "data/annotations/egosurgery_tool_folds"
ROUNDS = {"r1": REPO / "experiments/baselines/stage1_dtower",
          "r2": REPO / "experiments/baselines/stage1_dtower_r2"}
TOWERS = ("coco", "imagenet")
FOLD_SEEDS = [("A", 42), ("A", 123), ("A", 456), ("B", 42), ("C", 42), ("D", 42), ("E", 42)]
GROUP_KEYS = {"標的群": "target", "陰性対照群": "control"}
OUT_MD = REPO / "docs/stage1/D_group_ap.md"
OUT_JSON = ROUNDS["r2"] / "group_ap.json"


def read_groups(text: str) -> dict[str, list[str]]:
    """det_groups 節の表から群とクラスを読む。節が無ければ止まる。"""
    m = re.search(r'<a id="det_groups"></a>\n(.*?)(?=<a id="|\Z)', text, re.S)
    if not m:
        sys.exit("context/conventions.md に det_groups 節が無い")
    groups: dict[str, list[str]] = {}
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] in GROUP_KEYS:
            groups[GROUP_KEYS[cells[0]]] = [c.strip() for c in cells[1].split("、")]
    if set(groups) != set(GROUP_KEYS.values()):
        sys.exit(f"det_groups 節の表から群を読めない: {groups}")
    return groups


def annotation_classes(fold: str, split: str) -> tuple[list[str], set[str]]:
    """注釈のクラス名一覧と、その評価集合に出現しないクラスを返す。"""
    d = json.loads((ANN / fold / f"instances_{split}.json").read_text())
    names = [c["name"] for c in d["categories"]]
    present = {a["category_id"] for a in d["annotations"]}
    absent = {c["name"] for c in d["categories"] if c["id"] not in present}
    return names, absent


def mapping_table(groups: dict[str, list[str]], names: list[str]) -> list[dict]:
    """群のクラスを注釈のクラス名へ**完全一致で**対応させる。"""
    rows = []
    for g, classes in groups.items():
        for c in classes:
            rows.append({"group": g, "class": c, "matched": c if c in names else None})
    return rows


def group_ap(per_class: dict, classes: list[str]) -> dict:
    used = {c: per_class[c] for c in classes if not math.isnan(per_class[c])}
    missing = [c for c in classes if math.isnan(per_class[c])]
    ap = statistics.fmean(used.values()) if used else None
    return {"ap": ap, "n_classes": len(used), "missing": missing}


def run_name(tower: str, fold: str, seed: int) -> str:
    return f"d{tower}_fold{fold}_seed{seed}"


def compute(groups: dict[str, list[str]]) -> dict:
    out: dict = {}
    for rnd, root in ROUNDS.items():
        out[rnd] = {}
        for tower in TOWERS:
            for fold, seed in FOLD_SEEDS:
                name = run_name(tower, fold, seed)
                entry = {}
                for split in ("val", "test"):
                    path = root / name / f"eval_{split}.json"
                    if not path.exists():
                        continue
                    per_class = json.loads(path.read_text())["per_class_ap"]
                    _, absent = annotation_classes(fold, split)
                    nan = {c for c, v in per_class.items() if math.isnan(v)}
                    if nan != absent:
                        sys.exit(f"{rnd}/{name}/{split}: NaN のクラス {sorted(nan)} が注釈の欠落 {sorted(absent)} と一致しない")
                    entry[split] = {g: group_ap(per_class, cs) for g, cs in groups.items()}
                    entry[split]["mAP"] = json.loads(path.read_text())["AP"]
                out[rnd][name] = entry
    return out


def diffs(res: dict) -> dict:
    """両塔の差（COCO − ImageNet）を群ごとに出す。"""
    out: dict = {}
    for rnd in ROUNDS:
        out[rnd] = {}
        for fold, seed in FOLD_SEEDS:
            key = f"fold{fold}_seed{seed}"
            c, i = res[rnd][run_name("coco", fold, seed)], res[rnd][run_name("imagenet", fold, seed)]
            out[rnd][key] = {}
            for split in ("val", "test"):
                if split not in c or split not in i:
                    continue
                out[rnd][key][split] = {
                    g: (c[split][g]["ap"] - i[split][g]["ap"]) if g != "mAP" else c[split][g] - i[split][g]
                    for g in ("target", "control", "mAP")
                }
    return out


def _f(x: float | None, nd: int = 4) -> str:
    return "—" if x is None else f"{x:.{nd}f}"


def _s(x: float) -> str:
    return f"{x:+.4f}"


def summary(res: dict, dif: dict) -> dict:
    """折り A の 3 seed 平均と、5 折り（seed 42）の平均。"""
    out: dict = {}
    for rnd in ROUNDS:
        out[rnd] = {}
        for tower in TOWERS:
            for g in ("target", "control"):
                a3 = [res[rnd][run_name(tower, "A", s)]["val"][g]["ap"] for s in (42, 123, 456)]
                f5v = [res[rnd][run_name(tower, f, 42)]["val"][g]["ap"] for f in "ABCDE"]
                f5t = [res[rnd][run_name(tower, f, 42)]["test"][g]["ap"] for f in "ABCDE"]
                out[rnd][f"{tower}_{g}"] = {
                    "val_foldA_3seed_mean": statistics.fmean(a3),
                    "val_foldA_3seed_sd": statistics.stdev(a3),
                    "val_5fold_seed42_mean": statistics.fmean(f5v),
                    "test_5fold_mean": statistics.fmean(f5t),
                }
        for g in ("target", "control", "mAP"):
            for split in ("val", "test"):
                vals = [dif[rnd][f"fold{f}_seed42"][split][g] for f in "ABCDE"]
                out[rnd][f"diff_{g}_{split}_5fold_mean"] = statistics.fmean(vals)
    return out


def render(groups, mapping, res, dif, summ) -> str:
    L: list[str] = []
    A = L.append
    A("# D — 検出塔の標的群 AP と陰性対照群 AP")
    A("")
    A("**task_id:** `T-2026-09-27-stage2-prep`  **kind:** impl（Task C）")
    A("")
    A("生成: `python scripts/build_stage1_group_ap.py`。**数値は既存の評価の出力（`eval_{val,test}.json` の "
      "`per_class_ap`）から計算した。再評価はしていない。** 機械可読は "
      "`experiments/baselines/stage1_dtower_r2/group_ap.json`。")
    A("")
    A("## 1. 群の定義と対応表")
    A("")
    A("群は `context/conventions.md#det_groups` の表から読む（研究方針 v2 §7.3、2026-06-19 事前登録）。"
      "標的群 AP = 群のクラスの AP の平均。陰性対照群 AP も同様。")
    A("クラス名は検出塔の注釈（`data/annotations/egosurgery_tool_folds/*/instances_*.json` の `categories`）と"
      "**完全一致**で照合した。空白・大文字小文字・単複の違いを吸収する処理は無い。")
    A("")
    A("| 群 | 規約のクラス名 | 注釈のクラス名（完全一致） |")
    A("|---|---|---|")
    for r in mapping:
        A(f"| {'標的群' if r['group'] == 'target' else '陰性対照群'} | {r['class']} | {r['matched'] or '**対応なし**'} |")
    A("")
    A("## 2. 欠けたクラスの扱い")
    A("")
    A("AP が NaN のクラスは、その折りの評価集合に出現しない（注釈の欠落と全 run・全分割で一致することを照合済み。"
      "一致しなければスクリプトが止まる）。**群 AP は出現したクラスだけの平均とし、0 で埋めていない。**")
    A("")
    missing_rows = set()
    for rnd in ROUNDS:
        for name, e in res[rnd].items():
            fold = name.split("_")[1][-1]
            for split, v in e.items():
                for g in ("target", "control"):
                    if v[g]["missing"]:
                        missing_rows.add((fold, split, g, "、".join(v[g]["missing"])))
    A("| 折り | 分割 | 群 | 除いたクラス |")
    A("|---|---|---|---|")
    for fold, split, g, m in sorted(missing_rows):
        A(f"| {fold} | {split} | {'標的群' if g == 'target' else '陰性対照群'} | {m} |")
    if not missing_rows:
        A("| — | — | — | なし |")
    A("")
    A("それ以外の折り・分割では両群とも全クラスが出現した。")
    A("")
    A("## 3. val（14 run × 二周）")
    A("")
    A("群 AP の後ろの括弧は平均に使ったクラス数（標的群 5、陰性対照群 4 が全数）。")
    A("")
    A("| run | 標的群 一周目 | 標的群 二周目 | 陰性対照群 一周目 | 陰性対照群 二周目 | mAP 一周目 | mAP 二周目 |")
    A("|---|---|---|---|---|---|---|")
    for tower in TOWERS:
        for fold, seed in FOLD_SEEDS:
            n = run_name(tower, fold, seed)
            r1, r2 = res["r1"][n]["val"], res["r2"][n]["val"]
            A(f"| {n} | {_f(r1['target']['ap'])} ({r1['target']['n_classes']}) | {_f(r2['target']['ap'])} ({r2['target']['n_classes']}) | "
              f"{_f(r1['control']['ap'])} ({r1['control']['n_classes']}) | {_f(r2['control']['ap'])} ({r2['control']['n_classes']}) | "
              f"{_f(r1['mAP'])} | {_f(r2['mAP'])} |")
    A("")
    A("## 4. test（確定塔の 10 件 = 2 塔 × 5 折り、折り A は seed 42）")
    A("")
    A("| run | 標的群 一周目 | 標的群 二周目 | 陰性対照群 一周目 | 陰性対照群 二周目 | mAP 一周目 | mAP 二周目 |")
    A("|---|---|---|---|---|---|---|")
    for tower in TOWERS:
        for fold in "ABCDE":
            n = run_name(tower, fold, 42)
            r1, r2 = res["r1"][n]["test"], res["r2"][n]["test"]
            A(f"| {n} | {_f(r1['target']['ap'])} ({r1['target']['n_classes']}) | {_f(r2['target']['ap'])} ({r2['target']['n_classes']}) | "
              f"{_f(r1['control']['ap'])} ({r1['control']['n_classes']}) | {_f(r2['control']['ap'])} ({r2['control']['n_classes']}) | "
              f"{_f(r1['mAP'])} | {_f(r2['mAP'])} |")
    A("")
    A("## 5. 両塔の差（COCO − ImageNet）")
    A("")
    A("同じ折り・seed の対で引く。")
    A("")
    A("| 折り・seed | 分割 | 標的群 一周目 | 標的群 二周目 | 陰性対照群 一周目 | 陰性対照群 二周目 | mAP 一周目 | mAP 二周目 |")
    A("|---|---|---|---|---|---|---|---|")
    for split in ("val", "test"):
        for fold, seed in FOLD_SEEDS:
            k = f"fold{fold}_seed{seed}"
            if split not in dif["r2"][k]:
                continue
            d1, d2 = dif["r1"][k][split], dif["r2"][k][split]
            A(f"| {fold} / {seed} | {split} | {_s(d1['target'])} | {_s(d2['target'])} | {_s(d1['control'])} | {_s(d2['control'])} | "
              f"{_s(d1['mAP'])} | {_s(d2['mAP'])} |")
    for split in ("val", "test"):
        s1, s2 = summ["r1"], summ["r2"]
        A(f"| **5 折り平均（seed 42）** | {split} | {_s(s1[f'diff_target_{split}_5fold_mean'])} | {_s(s2[f'diff_target_{split}_5fold_mean'])} | "
          f"{_s(s1[f'diff_control_{split}_5fold_mean'])} | {_s(s2[f'diff_control_{split}_5fold_mean'])} | "
          f"{_s(s1[f'diff_mAP_{split}_5fold_mean'])} | {_s(s2[f'diff_mAP_{split}_5fold_mean'])} |")
    A("")
    A("## 6. 塔ごとの要約")
    A("")
    A("| 塔 | 群 | 周 | val 折り A 3 seed 平均 (SD) | val 5 折り平均（seed 42） | test 5 折り平均 |")
    A("|---|---|---|---|---|---|")
    for tower in TOWERS:
        for g in ("target", "control"):
            for rnd in ROUNDS:
                s = summ[rnd][f"{tower}_{g}"]
                A(f"| D*-{'COCO' if tower == 'coco' else 'ImageNet'} | {'標的群' if g == 'target' else '陰性対照群'} | "
                  f"{'一周目' if rnd == 'r1' else '二周目'} | {_f(s['val_foldA_3seed_mean'])} ({_f(s['val_foldA_3seed_sd'])}) | "
                  f"{_f(s['val_5fold_seed42_mean'])} | {_f(s['test_5fold_mean'])} |")
    A("")
    A("## 7. 注記")
    A("")
    A("- 五分割の折り平均と折り A の SD は**記述統計**である。判定（折りをクラスタとするブロック・ブートストラップ）"
      "は Stage 2 の対の差に当てるもので、本表は塔の水準を示すだけである。")
    A("- 陰性対照群は「Δ ≈ 0 であるべき群」で、界面の効果を測る Stage 2 で意味を持つ。"
      "本表の塔間の差は界面の Δ ではない。")
    A("- 一周目は 12 epoch 固定、二周目は収束基準（上限 36）。評価 recipe は同じ（`scripts/eval_relation_detr_map.py`）。")
    return "\n".join(L) + "\n"


def main() -> int:
    groups = read_groups(CONVENTIONS.read_text(encoding="utf-8"))
    names, _ = annotation_classes("A", "val")
    for fold in "ABCDE":
        for split in ("train", "val", "test"):
            if annotation_classes(fold, split)[0] != names:
                sys.exit(f"折り {fold} の {split} のクラス名が折り A の val と違う")
    mapping = mapping_table(groups, names)
    unmatched = [r["class"] for r in mapping if r["matched"] is None]
    if unmatched:
        print(f"完全一致で対応しないクラス: {unmatched}", file=sys.stderr)
        return 1
    res = compute(groups)
    dif = diffs(res)
    summ = summary(res, dif)
    OUT_JSON.write_text(json.dumps(
        {"task_id": "T-2026-09-27-stage2-prep",
         "source": "eval_{val,test}.json の per_class_ap（再評価なし）",
         "groups": groups, "annotation_classes": names, "mapping": mapping,
         "missing_rule": "評価集合に出現しないクラス（NaN）は群 AP から除く。0 で埋めない",
         "runs": res, "diff_coco_minus_imagenet": dif, "summary": summ},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(render(groups, mapping, res, dif, summ), encoding="utf-8")
    print(f"wrote {OUT_MD.relative_to(REPO)} and {OUT_JSON.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

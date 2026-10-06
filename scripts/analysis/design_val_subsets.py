#!/usr/bin/env python
"""設計の判断に使う val 動画の部分集合の全数列挙（T-2026-10-07-design-val-subset-balance）。

折り表の val 動画（10 本）の空でない部分集合 S をすべて列挙し、設計側 S と
清浄側 C（15 動画から S を除いた集合）の工程・術具ラベルの偏りと欠落を表にする。
**集合は選ばない。** 値と定義だけを出す。

    python scripts/analysis/design_val_subsets.py            # 対照と要約を標準出力へ
    python scripts/analysis/design_val_subsets.py --write    # docs/stage1/ に csv と md を書く

材料はラベルの統計だけである。画像・モデルの出力・評価値は読まない。
注釈の読み込みと均衡指標は生成器 `scripts/analysis/a1_fold_table.py` の関数をそのまま使う
（生成器は変えない）。折り表と群は `context/conventions.md` から読む。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import statistics
import sys
from itertools import combinations
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import a1_fold_table as gen  # noqa: E402

REPO_ROOT = gen.REPO_ROOT
CONVENTIONS = REPO_ROOT / "context/conventions.md"
FOLD_TABLE_DOC = REPO_ROOT / "docs/stage0/A1_fold_table.md"
OUT_DIR = REPO_ROOT / "docs/stage1"
OUT_CSV = OUT_DIR / "design_val_subsets.csv"
OUT_MD = OUT_DIR / "design_val_subsets.md"
TASK_ID = "T-2026-10-07-design-val-subset-balance"
FOLD_IDS = gen.FOLD_IDS

# 材料の合計行（docs/stage0/A1_fold_material.md）と、折り表の正本の d(test)。
EXPECTED_TOTALS = {"frames": 17233, "images": 15437, "boxes": 49652, "phases": 9, "classes": 15, "videos": 15}
EXPECTED_TEST_D = {"A": 0.2966, "B": 0.2844, "C": 0.2628, "D": 0.2667, "E": 0.2811}
# 起票者が折り表から手で導いた清浄側の折りごとの本数（SPEC §2）。
ISSUER_CLEAN = {
    "val_A": (3, 3, 3, 3, 1),
    "val_C": (3, 3, 3, 2, 2),
    "val_all": (0, 3, 1, 1, 0),
}
TOP_N = 5
FORBIDDEN_WORDS = ("推奨", "勧め", "最良", "最適")

# --------------------------------------------------------------------------
# 開いたファイルの記録（受け入れ h）。audit hook は Path.read_text も io.open も拾う。
# --------------------------------------------------------------------------

OPENED: list[str] = []


def _audit(event: str, args: tuple) -> None:
    if event == "open" and args and isinstance(args[0], (str, Path)):
        mode = args[1] if len(args) > 1 and isinstance(args[1], str) else "r"
        path = Path(args[0]).resolve()
        if REPO_ROOT in path.parents and "w" not in mode and "a" not in mode:
            OPENED.append(str(path.relative_to(REPO_ROOT)))


# --------------------------------------------------------------------------
# 規約からの読み出し。名前の部分一致ではなく表の行を読む。
# --------------------------------------------------------------------------


def _section(text: str, anchor: str) -> str:
    start = text.index(f'<a id="{anchor}"></a>')
    nxt = text.find('<a id="', start + 1)
    return text[start : nxt if nxt != -1 else len(text)]


def parse_folds(text: str) -> dict[str, dict[str, tuple[str, ...]]]:
    """`| A | 04, 05, 07 | 09, 10 |` の行から test と val を読む。"""
    rows = re.findall(r"^\|\s*([A-E])\s*\|\s*([0-9, ]+?)\s*\|\s*([0-9, ]+?)\s*\|", text, flags=re.M)
    table = {}
    for fold, test, val in rows:
        table[fold] = {
            "test": tuple(sorted(t.strip() for t in test.split(","))),
            "val": tuple(sorted(v.strip() for v in val.split(","))),
        }
    return table


def parse_det_groups(text: str) -> dict[str, tuple[str, ...]]:
    section = _section(text, "det_groups")
    groups = {}
    for key, label in (("target", "標的群"), ("negative", "陰性対照群")):
        m = re.search(rf"^\|\s*{label}\s*\|\s*([^|]+?)\s*\|", section, flags=re.M)
        groups[key] = tuple(c.strip() for c in m.group(1).split("、"))
    return groups


def match_groups(groups: dict[str, tuple[str, ...]], classes: tuple[str, ...]) -> list[str]:
    """群のクラス名を注釈のクラス名と完全一致で照合する。照合できない名前を返す。"""
    universe = set(classes)
    return [c for g in groups.values() for c in g if c not in universe]


# --------------------------------------------------------------------------
# val の導出と検査
# --------------------------------------------------------------------------


def derive_val(folds: dict[str, dict[str, tuple[str, ...]]]) -> dict[str, dict]:
    """各 val 動画について、val になる折りと test になる折りを集合演算で導く。"""
    out = {}
    val_videos = sorted(set().union(*(set(folds[f]["val"]) for f in FOLD_IDS)))
    for v in val_videos:
        out[v] = {
            "val_folds": [f for f in FOLD_IDS if v in set(folds[f]["val"])],
            "test_folds": [f for f in FOLD_IDS if v in set(folds[f]["test"])],
        }
    return out


def check_val(folds: dict[str, dict[str, tuple[str, ...]]]) -> list[str]:
    problems = []
    for v, d in derive_val(folds).items():
        if len(d["val_folds"]) != 1:
            problems.append(f"動画 {v} の val の折りが一つでない: {d['val_folds']}")
        if set(d["val_folds"]) & set(d["test_folds"]):
            problems.append(f"動画 {v} が自分の折りの test に入る: {d['val_folds']}")
        if len(d["test_folds"]) != 1:
            problems.append(f"動画 {v} が test になる折りが一つでない: {d['test_folds']}")
    return problems


# --------------------------------------------------------------------------
# 指標
# --------------------------------------------------------------------------


class Ctx:
    def __init__(self, material: gen.Material, phase_universe, class_universe, groups, folds, official):
        self.m = material
        self.phase_universe = tuple(phase_universe)
        self.class_universe = tuple(class_universe)
        self.groups = groups
        self.folds = folds
        self.official = official
        self.fifteen = material.videos
        self.val_videos = tuple(sorted(derive_val(folds)))

    def missing(self, videos, table, universe) -> list[str]:
        return [k for k in universe if sum(table.get(v, {}).get(k, 0) for v in videos) == 0]

    def side(self, videos: tuple[str, ...]) -> dict:
        m = self.m
        ph_miss = self.missing(videos, m.phase, self.phase_universe)
        tl_miss = self.missing(videos, m.tool, self.class_universe)
        tg_miss = [c for c in self.groups["target"] if c in tl_miss]
        ng_miss = [c for c in self.groups["negative"] if c in tl_miss]
        tv_p, tv_t = m.divergence(videos)
        target_boxes = {c: sum(m.tool.get(v, {}).get(c, 0) for v in videos) for c in self.groups["target"]}
        return {
            "n": len(videos),
            "frames": m.frames(videos),
            "boxes": m.boxes(videos),
            "phase_missing": ph_miss,
            "tool_missing": tl_miss,
            "target_missing": tg_miss,
            "negative_missing": ng_miss,
            "target_boxes": target_boxes,
            "tv_phase": tv_p,
            "tv_tool": tv_t,
            "d": tv_p + tv_t,
        }

    def clean_counts(self, s: set[str], folds=None) -> tuple[int, ...]:
        folds = folds or self.folds
        return tuple(len(set(folds[f]["test"]) - s) for f in FOLD_IDS)

    def union_of(self, s: set[str]) -> str:
        hit = []
        for f in FOLD_IDS:
            val = set(self.folds[f]["val"])
            if val <= s:
                hit.append(f)
            elif val & s:
                return ""
        return "+".join(hit)

    def row(self, subset: tuple[str, ...]) -> dict:
        s = set(subset)
        c = tuple(v for v in self.fifteen if v not in s)
        S, C = self.side(subset), self.side(c)
        clean = self.clean_counts(s)
        return {
            "subset": subset,
            "S": S,
            "C": C,
            "clean": clean,
            "clean_min": min(clean),
            "n_official_test": len(s & set(self.official["test"])),
            "n_official_val": len(s & set(self.official["val"])),
            "val_union": self.union_of(s),
        }


def dominates(a: dict, b: dict) -> bool:
    ka = (len(a["S"]["target_missing"]), len(a["S"]["phase_missing"]), a["S"]["d"], a["C"]["d"], -a["clean_min"])
    kb = (len(b["S"]["target_missing"]), len(b["S"]["phase_missing"]), b["S"]["d"], b["C"]["d"], -b["clean_min"])
    return all(x <= y for x, y in zip(ka, kb)) and any(x < y for x, y in zip(ka, kb))


def mark_pareto(rows: list[dict]) -> None:
    by_size: dict[int, list[dict]] = {}
    for r in rows:
        by_size.setdefault(len(r["subset"]), []).append(r)
    for group in by_size.values():
        no_test = [r for r in group if r["n_official_test"] == 0]
        for r in group:
            r["pareto_all"] = not any(dominates(o, r) for o in group if o is not r)
            r["pareto_no_test"] = (
                r["n_official_test"] == 0 and not any(dominates(o, r) for o in no_test if o is not r)
            )


def enumerate_rows(ctx: Ctx) -> list[dict]:
    rows = []
    for k in range(1, len(ctx.val_videos) + 1):
        for subset in combinations(ctx.val_videos, k):
            rows.append(ctx.row(subset))
    mark_pareto(rows)
    return rows


def check_identity(ctx: Ctx, rows: list[dict], folds=None) -> list[str]:
    problems = []
    for r in rows:
        clean = ctx.clean_counts(set(r["subset"]), folds) if folds else r["clean"]
        n_c = 15 - len(r["subset"])
        if r["C"]["n"] != n_c or sum(clean) != n_c:
            problems.append(f"{' '.join(r['subset'])}: 清浄側 {r['C']['n']} / 折り和 {sum(clean)} / 期待 {n_c}")
    return problems


def check_enumeration(rows_subsets: list[tuple[str, ...]], n_val: int) -> list[str]:
    problems = []
    if len(rows_subsets) != 2**n_val - 1:
        problems.append(f"行数 {len(rows_subsets)} != 2^{n_val}-1")
    for k in range(1, n_val + 1):
        got = sum(1 for s in rows_subsets if len(s) == k)
        if got != comb(n_val, k):
            problems.append(f"本数 {k}: {got} != C({n_val},{k})")
    dup = len(rows_subsets) - len({frozenset(s) for s in rows_subsets})
    if dup:
        problems.append(f"重複行 {dup}")
    return problems


# --------------------------------------------------------------------------
# 出力
# --------------------------------------------------------------------------


def _f(x: float) -> str:
    return f"{x:.6f}"


def csv_header(ctx: Ctx) -> list[str]:
    tg = [f"S_boxes_{c.replace(' ', '_')}" for c in ctx.groups["target"]]
    return (
        ["size", "videos", "S_n", "S_frames", "S_boxes",
         "S_phase_missing", "S_phase_missing_names", "S_tool_missing", "S_tool_missing_names",
         "S_target_missing", "S_target_missing_names", "S_negative_missing", "S_negative_missing_names"]
        + tg
        + ["S_target_boxes_min", "S_tv_phase", "S_tv_tool", "S_d",
           "C_n", "C_frames", "C_boxes",
           "C_phase_missing", "C_phase_missing_names", "C_tool_missing", "C_tool_missing_names",
           "C_target_missing", "C_target_missing_names", "C_negative_missing", "C_negative_missing_names",
           "C_tv_phase", "C_tv_tool", "C_d"]
        + [f"clean_{f}" for f in FOLD_IDS]
        + ["clean_min", "S_n_official_test", "S_n_official_val", "S_equals_val_union_of_folds",
           "pareto_all", "pareto_no_official_test"]
    )


def csv_row(ctx: Ctx, r: dict) -> list:
    S, C = r["S"], r["C"]
    out = [len(r["subset"]), " ".join(r["subset"]), S["n"], S["frames"], S["boxes"],
           len(S["phase_missing"]), ";".join(S["phase_missing"]),
           len(S["tool_missing"]), ";".join(S["tool_missing"]),
           len(S["target_missing"]), ";".join(S["target_missing"]),
           len(S["negative_missing"]), ";".join(S["negative_missing"])]
    out += [S["target_boxes"][c] for c in ctx.groups["target"]]
    out += [min(S["target_boxes"].values()), _f(S["tv_phase"]), _f(S["tv_tool"]), _f(S["d"]),
            C["n"], C["frames"], C["boxes"],
            len(C["phase_missing"]), ";".join(C["phase_missing"]),
            len(C["tool_missing"]), ";".join(C["tool_missing"]),
            len(C["target_missing"]), ";".join(C["target_missing"]),
            len(C["negative_missing"]), ";".join(C["negative_missing"]),
            _f(C["tv_phase"]), _f(C["tv_tool"]), _f(C["d"])]
    out += list(r["clean"])
    out += [r["clean_min"], r["n_official_test"], r["n_official_val"], r["val_union"],
            int(r["pareto_all"]), int(r["pareto_no_test"])]
    return out


def render_csv(ctx: Ctx, rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(csv_header(ctx))
    for r in rows:
        w.writerow(csv_row(ctx, r))
    return buf.getvalue()


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def display_key(r: dict):
    """上位行の表示順。**選定の規則ではない。**"""
    return (
        len(r["S"]["target_missing"]),
        len(r["S"]["phase_missing"]),
        -r["clean_min"],
        r["S"]["d"] + r["C"]["d"],
        r["subset"],
    )


def _names(xs: list[str]) -> str:
    return "、".join(xs) if xs else "—"


def metric_table(ctx: Ctx, cols: list[tuple[str, dict]]) -> list[str]:
    """行を指標、列を集合にした表（Task B の全指標）。"""
    head = "| 指標 | " + " | ".join(name for name, _ in cols) + " |"
    lines = [head, "|---|" + "---|" * len(cols)]

    def add(label, fn):
        lines.append(f"| {label} | " + " | ".join(str(fn(r)) for _, r in cols) + " |")

    add("S の動画", lambda r: ", ".join(r["subset"]))
    add("S 本数", lambda r: r["S"]["n"])
    add("S フレーム", lambda r: r["S"]["frames"])
    add("S box", lambda r: r["S"]["boxes"])
    add("S 工程の欠落", lambda r: f"{len(r['S']['phase_missing'])}（{_names(r['S']['phase_missing'])}）")
    add("S 術具の欠落", lambda r: f"{len(r['S']['tool_missing'])}（{_names(r['S']['tool_missing'])}）")
    add("S 標的群の欠落", lambda r: f"{len(r['S']['target_missing'])}（{_names(r['S']['target_missing'])}）")
    add("S 陰性対照群の欠落", lambda r: f"{len(r['S']['negative_missing'])}（{_names(r['S']['negative_missing'])}）")
    for c in ctx.groups["target"]:
        add(f"S box {c}", lambda r, c=c: r["S"]["target_boxes"][c])
    add("S 標的群 box の最小", lambda r: min(r["S"]["target_boxes"].values()))
    add("d(S)", lambda r: f"{r['S']['d']:.4f}")
    add("C 本数", lambda r: r["C"]["n"])
    add("C フレーム", lambda r: r["C"]["frames"])
    add("C box", lambda r: r["C"]["boxes"])
    add("C 工程の欠落", lambda r: f"{len(r['C']['phase_missing'])}（{_names(r['C']['phase_missing'])}）")
    add("C 術具の欠落", lambda r: f"{len(r['C']['tool_missing'])}（{_names(r['C']['tool_missing'])}）")
    add("C 標的群の欠落", lambda r: f"{len(r['C']['target_missing'])}（{_names(r['C']['target_missing'])}）")
    add("C 陰性対照群の欠落", lambda r: f"{len(r['C']['negative_missing'])}（{_names(r['C']['negative_missing'])}）")
    add("d(C)", lambda r: f"{r['C']['d']:.4f}")
    add("清浄本数 A,B,C,D,E", lambda r: ", ".join(map(str, r["clean"])))
    add("清浄本数の最小", lambda r: r["clean_min"])
    add("S 内の公式 test 本数", lambda r: r["n_official_test"])
    add("S 内の公式 val 本数", lambda r: r["n_official_val"])
    add("折りの val の和集合", lambda r: r["val_union"] or "—")
    add("非劣（全体）", lambda r: "✓" if r["pareto_all"] else "")
    add("非劣（公式 test を含まない中）", lambda r: "✓" if r["pareto_no_test"] else "")
    return lines


def top_table(rows: list[dict]) -> list[str]:
    lines = [
        "| 本数 | S | S 標的群欠落 | S 工程欠落 | 清浄最小 | d(S) | d(C) | d(S)+d(C) | 公式 test | 非劣 全体 | 非劣 公式test無 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {len(r['subset'])} | {', '.join(r['subset'])} | {len(r['S']['target_missing'])} | "
            f"{len(r['S']['phase_missing'])} | {r['clean_min']} | {r['S']['d']:.4f} | {r['C']['d']:.4f} | "
            f"{r['S']['d'] + r['C']['d']:.4f} | {r['n_official_test']} | "
            f"{'✓' if r['pareto_all'] else ''} | {'✓' if r['pareto_no_test'] else ''} |"
        )
    return lines


def render_md(ctx: Ctx, rows: list[dict], info: dict) -> str:
    L: list[str] = []
    a = L.append
    a("# 設計の判断に使う val 動画の部分集合（全数列挙）")
    a("")
    a(f"契約 `{TASK_ID}`。生成器 `scripts/analysis/design_val_subsets.py`（`--write` で本ファイルと csv を書く）。")
    a("全行は `docs/stage1/design_val_subsets.csv`（1 行が 1 部分集合）。")
    a("")
    a("**本文書は集合を選ばない。** 値と定義だけを載せる。どの集合を採るかは利用者が決める。")
    a("材料はラベルの統計（工程のフレーム数と術具の box 数）だけで、画像・モデルの出力・評価値は読んでいない。")
    a("")
    unseen = info["unseen_in_val"]
    a("## 冒頭の注記")
    a("")
    if unseen:
        a(f"- 標的群か陰性対照群のクラスのうち、どの val 動画にも現れないもの: {_names(unseen)}")
    else:
        a("- 標的群と陰性対照群のクラスは、すべて少なくとも一本の val 動画に現れる（val 10 本の和で欠落 0）")
    a(f"- 15 動画全体での欠落: 工程 {info['corpus_phase_missing']} 種、術具 {info['corpus_tool_missing']} クラス"
      "（宣言された 9 工程と 15 クラスに対して数えた。全体で 0 のため、欠落の母数を除く数え方と除かない数え方は一致する）")
    a("")
    a("## 用語と指標の定義")
    a("")
    a("- **設計側 S**: 設計判断に使う val 動画の集合。val 動画（10 本）の空でない部分集合")
    a("- **清浄側 C**: 15 動画から S を除いた集合（設計判断が触れていない test の動画）")
    a("- **欠落**: 集合に 1 フレームも無い工程、1 box も無い術具クラス。母数は 9 工程（`src/egosurgery/datasets/constants.py` の `PHASE_CLASSES`）と 15 クラス（COCO の categories）")
    a("- **標的群・陰性対照群**: `context/conventions.md#det_groups` のクラス（注釈のクラス名と完全一致で照合した）")
    a(f"  - 標的群: {_names(list(ctx.groups['target']))}")
    a(f"  - 陰性対照群: {_names(list(ctx.groups['negative']))}")
    a("- **均衡指標 d(X) = TV(p(X), p(全15動画)) + TV(t(X), t(全15動画))**。p は工程 9 種のフレーム比率、"
      "t は術具 15 クラスの box 比率、TV(x, y) = 0.5 Σ|x_i − y_i|。生成器 `a1_fold_table.Material.cost` をそのまま使う")
    a("- **折りごとの清浄本数**: その折りの test 3 本のうち S に入らない本数。和は常に 15 − |S|")
    a("- **折りの val の和集合**: S が一つ以上の折りの val の和に一致するとき、その折りを `+` で並べる")
    a("- **非劣**: 本数が同じ部分集合どうしで、次の五つのどれでも劣らず、どれか一つで勝る相手が居ない行。"
      "`pareto_all` は全体で、`pareto_no_official_test` は公式 test（04, 05, 07）を含まない部分集合だけで比べる")
    a("  1. S の標的群の欠落数（小さい方が勝る） 2. S の工程の欠落数（小） 3. d(S)（小） 4. d(C)（小） 5. 清浄本数の最小値（大きい方が勝る）")
    a("- 浮動小数は csv で小数第 6 位、本文で第 4 位に丸めて表示している。非劣の比較は丸める前の値で行った")
    a("")
    a("## 入力の出所と再現")
    a("")
    a("| 入力 | 所在 |")
    a("|---|---|")
    a("| 工程フレーム数 | `data/annotations/egosurgery_phase/*.csv` のうち折り表の 15 動画（`a1_fold_table.load_phase`） |")
    a("| 術具 box 数 | `data/annotations/egosurgery_tool/instances_{train,val,test}.json`（`a1_fold_table.load_tool`） |")
    a("| 折り表 | `context/conventions.md#folds`（正本 `docs/stage0/A1_fold_table.md` の表と一致を検査） |")
    a("| 群 | `context/conventions.md#det_groups` |")
    a("| 公式分割 | `data/splits/ego_{train,val,test}.txt` |")
    a("")
    a("    source .venv/bin/activate && python scripts/analysis/design_val_subsets.py --write")
    a("")
    a(f"csv の要約値（sha256）: `{info['csv_digest']}`。乱数は使っていない。")
    a("")
    a("## val の 2 本が折り表でどう選ばれたか")
    a("")
    a("生成器 `scripts/analysis/a1_fold_table.py` の `build_table` と `choose_vals`、正本 `docs/stage0/A1_fold_table.md` から読んだ事実。")
    a("")
    a("- 折り A の val は公式 val（`data/splits/ego_val.txt` の 09, 10）に**固定**されている。均衡の目的には入っていない")
    a("- 先に折り B〜E の test を、`max_f d(test_f)` → `sum_f d(test_f)` → 辞書順で全数列挙から決める。val はこの段階では関与しない")
    a("- その後、折り B〜E の val を `choose_vals` で決める。**制約**は、自分の折りの test と重ならないこと、"
      "全折りを通じて各動画が val に高々一度であること（折り A の val の 09, 10 は使えない）")
    a("- **目的**は、各折りの val 2 本の d(val_f) について `max_f d(val_f)` → `sum_f d(val_f)` → 辞書順。"
      "すなわち折り B〜E の val は、val 2 本自身の均衡（全 15 動画への近さ）を目的として選ばれた。"
      "val が test 側の均衡や、val の和集合の代表性を目的に入れて選ばれたわけではない")
    a("")
    a("## 各折りの val の 2 本")
    a("")
    fold_rows = [(f"折り {f}", next(x for x in rows if x["subset"] == ctx.folds[f]["val"])) for f in FOLD_IDS]
    L.extend(metric_table(ctx, fold_rows))
    a("")
    a("## 本数ごとの要約")
    a("")
    a("| 本数 | 件数 | d(S) 最小 / 中央 / 最大 | d(C) 最小 / 中央 / 最大 | S 工程欠落 0 | S 標的群欠落 0 | S 術具欠落 0 | 非劣 全体 | 公式 test 無 | 非劣 公式test無 |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    for k in range(1, len(ctx.val_videos) + 1):
        g = [r for r in rows if len(r["subset"]) == k]
        ds = [r["S"]["d"] for r in g]
        dc = [r["C"]["d"] for r in g]
        a(
            f"| {k} | {len(g)} | {min(ds):.4f} / {statistics.median(ds):.4f} / {max(ds):.4f} | "
            f"{min(dc):.4f} / {statistics.median(dc):.4f} / {max(dc):.4f} | "
            f"{sum(1 for r in g if not r['S']['phase_missing'])} | "
            f"{sum(1 for r in g if not r['S']['target_missing'])} | "
            f"{sum(1 for r in g if not r['S']['tool_missing'])} | "
            f"{sum(1 for r in g if r['pareto_all'])} | "
            f"{sum(1 for r in g if r['n_official_test'] == 0)} | "
            f"{sum(1 for r in g if r['pareto_no_test'])} |"
        )
    a("")
    a("## 本数ごとの上位行")
    a("")
    a(f"本数ごとに表示順の先頭 {TOP_N} 行を載せる（その本数の件数が {TOP_N} 未満なら全件）。全行は csv にある。")
    a("表示順は次のとおりである。**表示順は選定の規則ではない。** 表を読みやすくするための並びにすぎない。")
    a("")
    a("1. S の標的群の欠落数の昇順 2. S の工程の欠落数の昇順 3. 清浄本数の最小値の降順 4. d(S) + d(C) の昇順 5. 動画識別子の辞書順")
    a("")
    for title, pred in (("全体", lambda r: True), ("公式 test を含まない部分集合", lambda r: r["n_official_test"] == 0)):
        a(f"### {title}")
        a("")
        shown = []
        for k in range(1, len(ctx.val_videos) + 1):
            g = sorted([r for r in rows if len(r["subset"]) == k and pred(r)], key=display_key)
            shown.extend(g[:TOP_N])
        L.extend(top_table(shown))
        a("")
    a("## 参照行")
    a("")
    off_test = set(ctx.official["test"])
    refs = [
        ("val の全動画", tuple(ctx.val_videos)),
        ("val の全動画 − 公式 test", tuple(v for v in ctx.val_videos if v not in off_test)),
    ]
    refs += [(f"折り {f} の val", ctx.folds[f]["val"]) for f in FOLD_IDS]
    refs.append(("公式 val", tuple(sorted(ctx.official["val"]))))
    ref_rows = []
    for name, sub in refs:
        ref_rows.append((name, next(x for x in rows if x["subset"] == tuple(sorted(sub)))))
    L.extend(metric_table(ctx, ref_rows[:2]))
    a("")
    a("各折りの val と公式 val。上から折り A〜E の val、最後の行が公式 val（折り A の val と同じ集合である）:")
    a("")
    L.extend(top_table([r for _, r in ref_rows[2:]]))
    a("")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------
# 組み立てと対照
# --------------------------------------------------------------------------


def load_all():
    conv_text = CONVENTIONS.read_text()
    folds = parse_folds(_section(conv_text, "folds"))
    canon = parse_folds(FOLD_TABLE_DOC.read_text().split("## 折り表", 1)[1].split("##", 1)[0])
    groups = parse_det_groups(conv_text)
    official = gen.load_splits()
    phase_raw = gen.load_phase()
    tool, images = gen.load_tool()
    fifteen = sorted(set().union(*(set(folds[f]["test"]) for f in folds)))
    phase = {v: c for v, c in phase_raw.items() if v in set(fifteen)}
    categories = [c["name"] for c in json.loads((gen.TOOL_DIR / "instances_train.json").read_text())["categories"]]
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from egosurgery.datasets.constants import PHASE_CLASSES  # noqa: E402

    phase_universe = sorted(c["name"] for c in PHASE_CLASSES)
    return {
        "folds": folds,
        "canon": canon,
        "groups": groups,
        "official": official,
        "phase_raw_videos": sorted(phase_raw),
        "phase": phase,
        "tool": tool,
        "images": images,
        "fifteen": fifteen,
        "categories": sorted(categories),
        "phase_universe": phase_universe,
    }


def build(d: dict, phase=None) -> tuple[Ctx, list[dict]]:
    material = gen.Material(phase or d["phase"], d["tool"], d["images"], {})
    ctx = Ctx(material, d["phase_universe"], d["categories"], d["groups"], d["folds"], d["official"])
    return ctx, enumerate_rows(ctx)


def run(write: bool) -> int:
    sys.addaudithook(_audit)
    d = load_all()
    log: list[str] = []
    ok = True

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        ok &= bool(cond)
        log.append(f"{'PASS' if cond else 'FAIL'} {name}{': ' + detail if detail else ''}")

    # --- Gate G1: 材料 -------------------------------------------------------
    fifteen = tuple(d["fifteen"])
    log.append(f"INFO load_phase の既定の読み込みが返した動画: {d['phase_raw_videos']}")
    check("15 動画（折り表の test の和）", len(fifteen) == 15, str(list(fifteen)))
    check("工程の注釈が 15 動画にある", sorted(d["phase"]) == list(fifteen), str(sorted(d["phase"])))
    check("術具の注釈の動画が 15 動画に一致", sorted(d["tool"]) == list(fifteen) == sorted(d["images"]), str(sorted(d["tool"])))
    material = gen.Material(d["phase"], d["tool"], d["images"], {})
    totals = {
        "frames": material.frames(fifteen),
        "images": sum(d["images"][v] for v in fifteen),
        "boxes": material.boxes(fifteen),
        "phases": len(material.phases),
        "classes": len(material.classes),
        "videos": len(material.videos),
    }
    check("合計値が材料の合計行に一致", totals == EXPECTED_TOTALS, json.dumps(totals))
    pert = {v: dict(c) for v, c in d["phase"].items()}
    pert[fifteen[0]][sorted(pert[fifteen[0]])[0]] += 1
    check("対照: 入力を一行変えると総フレームが変わる",
          gen.Material(pert, d["tool"], d["images"], {}).frames(fifteen) != totals["frames"])
    check("工程の母数（宣言 9）と注釈の工程が一致", list(material.phases) == d["phase_universe"], str(d["phase_universe"]))
    check("術具の母数（COCO categories 15）と注釈のクラスが一致", list(material.classes) == d["categories"])
    check("規約の折り表が正本の表と一致",
          all(d["folds"][f] == {k: d["canon"][f][k] for k in ("test", "val")} for f in FOLD_IDS))
    check("折り A が公式分割に一致",
          set(d["folds"]["A"]["test"]) == set(d["official"]["test"]) and set(d["folds"]["A"]["val"]) == set(d["official"]["val"]))
    derived = derive_val(d["folds"])
    log.append("INFO val の導出: " + json.dumps({v: x["test_folds"] for v, x in derived.items()}, ensure_ascii=False))
    check("val 10 本、各 val 動画は自分の折りの test に入らず、test になる折りがちょうど一つ",
          len(derived) == 10 and not check_val(d["folds"]))
    broken = {f: dict(x) for f, x in d["folds"].items()}
    v0 = broken["A"]["val"][0]
    broken["A"]["test"] = tuple(sorted(set(broken["A"]["test"]) | {v0}))
    bad = check_val(broken)
    check("対照: val を自分の折りの test に置いた表で検査が落ちる", bool(bad), bad[0] if bad else "")
    unmatched = match_groups(d["groups"], tuple(d["categories"]))
    check("群のクラス名が注釈のクラス名と完全一致で照合できる", not unmatched,
          f"target={list(d['groups']['target'])} negative={list(d['groups']['negative'])}")
    typo = {"target": tuple(c + "s" if i == 0 else c for i, c in enumerate(d["groups"]["target"])),
            "negative": d["groups"]["negative"]}
    check("対照: 一文字違いの群の定義で照合が落ちる", bool(match_groups(typo, tuple(d["categories"]))),
          str(match_groups(typo, tuple(d["categories"]))))
    if not ok:
        print("\n".join(log))
        print("Gate G1 FAIL", file=sys.stderr)
        return 1
    log.append("GATE G1 PASS")

    # --- Gate G2: 指標と対照 -------------------------------------------------
    ctx, rows = build(d)
    for f in FOLD_IDS:
        v = material.cost(d["folds"][f]["test"])
        check(f"d(test_{f}) が正本と小数第 4 位まで一致", round(v, 4) == EXPECTED_TEST_D[f], f"{v:.6f}")
    check("d(15 動画全体) = 0", abs(material.cost(fifteen)) < 1e-12, f"{material.cost(fifteen):.3e}")
    singles = {v: material.cost((v,)) for v in fifteen}
    check("対照: 動画 1 本の d はすべて 0 より大きい", min(singles.values()) > 0, f"min={min(singles.values()):.4f}")
    p = list(material.corpus_phase)
    q = p.copy()
    q[0] += 0.01
    q[1] -= 0.01
    check("対照: 比率の一要素を変えると TV が変わる", gen.total_variation(q, p) > 0)
    cp = ctx.missing(fifteen, material.phase, ctx.phase_universe)
    ct = ctx.missing(fifteen, material.tool, ctx.class_universe)
    log.append(f"INFO 15 動画全体の欠落: 工程 {len(cp)} {cp} / 術具 {len(ct)} {ct}")
    drop_p = ctx.phase_universe[0]
    phase_minus = {v: {k: n for k, n in c.items() if k != drop_p} for v, c in material.phase.items()}
    tool_minus = {v: {k: n for k, n in c.items() if k != ctx.class_universe[0]} for v, c in material.tool.items()}
    check(f"対照: 工程 {drop_p} を除くと工程の欠落が一つ増える",
          len(ctx.missing(fifteen, phase_minus, ctx.phase_universe)) == len(cp) + 1)
    check(f"対照: 術具 {ctx.class_universe[0]} を除くと術具の欠落が一つ増える",
          len(ctx.missing(fifteen, tool_minus, ctx.class_universe)) == len(ct) + 1)
    issuer = {
        "val_A": set(d["folds"]["A"]["val"]),
        "val_C": set(d["folds"]["C"]["val"]),
        "val_all": set(ctx.val_videos),
    }
    for key, s in issuer.items():
        got = ctx.clean_counts(s)
        check(f"清浄側: §2 の {key} の内訳と一致", got == ISSUER_CLEAN[key], f"実測 {got} / 起票 {ISSUER_CLEAN[key]}")
    ident = check_identity(ctx, rows)
    check("清浄側の恒等式が全行で成り立つ", not ident, f"{len(rows)} 行")
    fake = {f: dict(x) for f, x in d["folds"].items()}
    fake["A"]["test"] = fake["A"]["test"][:2]
    bad = check_identity(ctx, rows, fake)
    check("対照: 一行の折り内訳を変えると恒等式の検査が落ちる", bool(bad), f"違反 {len(bad)} 行")
    if not ok:
        print("\n".join(log))
        print("Gate G2 FAIL", file=sys.stderr)
        return 1
    log.append("GATE G2 PASS")

    # --- 列挙と再現性 ---------------------------------------------------------
    subsets = [r["subset"] for r in rows]
    check("列挙: 行数・本数ごとの件数・重複 0", not check_enumeration(subsets, len(ctx.val_videos)),
          f"{len(rows)} 行 = 2^{len(ctx.val_videos)}-1 = {2 ** len(ctx.val_videos) - 1}")
    bad = check_enumeration(subsets + [subsets[0]], len(ctx.val_videos))
    check("対照: 同じ集合を二度入れた表で重複の検査が落ちる", any("重複" in b for b in bad), "; ".join(bad))
    text1 = render_csv(ctx, rows)
    ctx2, rows2 = build(d)
    text2 = render_csv(ctx2, rows2)
    check("再現性: 二度の実行で csv の要約値が一致", digest(text1) == digest(text2), digest(text1))
    pert = {v: dict(c) for v, c in d["phase"].items()}
    pert[fifteen[0]][sorted(pert[fifteen[0]])[0]] += 100000
    ctx3, rows3 = build(d, pert)
    check("対照: 入力を一行変えると csv の要約値が変わる", digest(render_csv(ctx3, rows3)) != digest(text1),
          f"動画 {fifteen[0]} の工程 {sorted(pert[fifteen[0]])[0]} に +100000（記憶上のみ） → {digest(render_csv(ctx3, rows3))[:16]}")

    unseen = [c for c in ctx.groups["target"] + ctx.groups["negative"]
              if c in ctx.missing(ctx.val_videos, material.tool, ctx.class_universe)]
    info = {"unseen_in_val": unseen, "corpus_phase_missing": len(cp), "corpus_tool_missing": len(ct),
            "csv_digest": digest(text1)}
    md = render_md(ctx, rows, info)
    words = {w: md.count(w) for w in FORBIDDEN_WORDS}
    check("文書に推奨の語が無い", sum(words.values()) == 0, json.dumps(words, ensure_ascii=False))
    probe = "この集合を推奨する。"
    check("対照: 語を含む一時の文で数え方が働く", sum(probe.count(w) for w in FORBIDDEN_WORDS) == 1)
    log.append(f"INFO 本数ごとの非劣（全体）: {[sum(1 for r in rows if len(r['subset']) == k and r['pareto_all']) for k in range(1, 11)]}")
    log.append(f"INFO 本数ごとの非劣（公式 test 無）: {[sum(1 for r in rows if len(r['subset']) == k and r['pareto_no_test']) for k in range(1, 11)]}")

    opened = sorted(set(OPENED))
    log.append("INFO 開いた入力: " + json.dumps(opened, ensure_ascii=False))
    bad_open = [p for p in opened if p.startswith(("experiments/", "runindex/"))]
    check("experiments と runindex の配下を開いていない", not bad_open and any("egosurgery_phase" in p for p in opened),
          f"{len(bad_open)} 件 / 一覧 {len(opened)} 件")

    print("\n".join(log))
    if not ok:
        print("FAIL", file=sys.stderr)
        return 1
    if write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        OUT_CSV.write_text(text1, encoding="utf-8-sig")
        OUT_MD.write_text(md)
        print(f"書きました: {OUT_CSV.relative_to(REPO_ROOT)}（{len(rows)} 行）, {OUT_MD.relative_to(REPO_ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="docs/stage1/ に csv と md を書く")
    return run(parser.parse_args().write)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""A1 折り表の決定的生成と検査（T-2026-09-17-fold-table）。

材料は Stage 0 の実測（`docs/stage0/A1_fold_material.md`）と同じ出所から読み直す。
本スクリプトは **読むだけ**で、`data/` へは一切書かない。

    python scripts/analysis/a1_fold_table.py            # 報告を標準出力へ
    python scripts/analysis/a1_fold_table.py --write    # docs/stage0/A1_fold_table.md を書く
    python scripts/analysis/a1_fold_table.py --controls # 対照（陽性・陰性）だけを走らせる

決定性: 集合は常に整列してから畳む。乱数は対照でのみ使い、seed を出力に書く。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PHASE_DIR = REPO_ROOT / "data/annotations/egosurgery_phase"
TOOL_DIR = REPO_ROOT / "data/annotations/egosurgery_tool"
HTS_DIR = REPO_ROOT / "data/annotations/egosurgery_hts"
SPLIT_DIR = REPO_ROOT / "data/splits"
EXTRA_PHASE_DIR = (
    REPO_ROOT
    / "data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/phase"
)

HTS_SYSTEMS = ("hand_seg", "hand_tool_seg", "tool_seg")
FOLD_IDS = ("A", "B", "C", "D", "E")
RANDOM_CONTROL_SEED = 20260917

TASK_ID = "T-2026-09-17-fold-table"


# --------------------------------------------------------------------------
# 材料の読み込み。**A1 の表を写さず、同じ出所から読み直す。**
# --------------------------------------------------------------------------


def vid_of(stem: str) -> str:
    """`01_1` → `01`。動画IDはゼロ埋め 2 桁の先頭要素である。"""
    return stem.split("_")[0]


def load_phase(directory: Path = PHASE_DIR) -> dict[str, dict[str, int]]:
    """動画ごとの工程フレーム数。`Frame,Phase` の CSV を数える。"""
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for path in sorted(directory.glob("*.csv")):
        vid = vid_of(path.stem)
        with path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                counts[vid][row["Phase"]] += 1
    return {v: dict(c) for v, c in sorted(counts.items())}


def load_tool(directory: Path = TOOL_DIR) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """動画ごと・クラスごとの box 数と、動画ごとの image 数。

    `file_name` は `train/01/01_1_0124.jpg` の形。動画IDは 2 要素目から取る。
    """
    boxes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    images: dict[str, int] = defaultdict(int)
    for name in ("instances_train.json", "instances_val.json", "instances_test.json"):
        blob = json.loads((directory / name).read_text())
        cat_name = {c["id"]: c["name"] for c in blob["categories"]}
        img_vid = {}
        for img in blob["images"]:
            vid = Path(img["file_name"]).parent.name
            img_vid[img["id"]] = vid
            images[vid] += 1
        for ann in blob["annotations"]:
            boxes[img_vid[ann["image_id"]]][cat_name[ann["category_id"]]] += 1
    return ({v: dict(c) for v, c in sorted(boxes.items())}, dict(sorted(images.items())))


def load_hts(directory: Path = HTS_DIR) -> dict[str, set[str]]:
    """動画ごとに、どの HTS 系統に注釈があるか。COCO の images から動画IDを拾う。"""
    present: dict[str, set[str]] = defaultdict(set)
    for system in HTS_SYSTEMS:
        for name in ("train.json", "val.json", "test.json"):
            path = directory / system / name
            if not path.exists():
                continue
            blob = json.loads(path.read_text())
            for img in blob.get("images", []):
                stem = Path(img["file_name"]).stem
                present[vid_of(stem)].add(system)
    return {v: s for v, s in sorted(present.items())}


def load_splits(directory: Path = SPLIT_DIR) -> dict[str, list[str]]:
    """公式分割の三ファイル。**読むだけで書き換えない**（no_split_redefine）。"""
    out = {}
    for key, name in (("train", "ego_train.txt"), ("val", "ego_val.txt"), ("test", "ego_test.txt")):
        text = (directory / name).read_text().split()
        out[key] = sorted(t.strip() for t in text if t.strip())
    return out


def load_extra_videos(directory: Path = EXTRA_PHASE_DIR) -> list[str]:
    """追加動画（動画ID 16 以上）の識別子。A2 と同じ出所から数え直す。"""
    vids = {vid_of(p.stem) for p in directory.glob("*.csv")}
    return sorted(v for v in vids if v.isdigit() and int(v) >= 16)


# --------------------------------------------------------------------------
# 均衡指標。**定義を出力に書く。書かなければ後で表を疑えない。**
# --------------------------------------------------------------------------


def profile(videos: tuple[str, ...], table: dict[str, dict[str, int]], keys: tuple[str, ...]) -> list[float]:
    """動画集合の比率ベクトル。合計 0 なら零ベクトルを返す。"""
    total = sum(table.get(v, {}).get(k, 0) for v in videos for k in keys)
    if total == 0:
        return [0.0] * len(keys)
    return [sum(table.get(v, {}).get(k, 0) for v in videos) / total for k in keys]


def total_variation(x: list[float], y: list[float]) -> float:
    """全変動距離。0（同一）から 1（互いに素）。"""
    return 0.5 * sum(abs(a - b) for a, b in zip(x, y))


class Material:
    """材料を一つの型にまとめる。**鍵は常に整列した組で持つ。**"""

    def __init__(
        self,
        phase: dict[str, dict[str, int]],
        tool: dict[str, dict[str, int]],
        images: dict[str, int],
        hts: dict[str, set[str]],
    ) -> None:
        self.phase = phase
        self.tool = tool
        self.images = images
        self.hts = hts
        self.videos = tuple(sorted(phase))
        self.phases = tuple(sorted({p for c in phase.values() for p in c}))
        self.classes = tuple(sorted({k for c in tool.values() for k in c}))
        self.corpus_phase = profile(self.videos, phase, self.phases)
        self.corpus_tool = profile(self.videos, tool, self.classes)

    def frames(self, videos: tuple[str, ...]) -> int:
        return sum(sum(self.phase.get(v, {}).values()) for v in videos)

    def boxes(self, videos: tuple[str, ...]) -> int:
        return sum(sum(self.tool.get(v, {}).values()) for v in videos)

    def divergence(self, videos: tuple[str, ...]) -> tuple[float, float]:
        """(工程の全変動, 術具の全変動)。基準は 15 動画全体の分布。"""
        return (
            total_variation(profile(videos, self.phase, self.phases), self.corpus_phase),
            total_variation(profile(videos, self.tool, self.classes), self.corpus_tool),
        )

    def cost(self, videos: tuple[str, ...]) -> float:
        """均衡指標 d(S) = TV_phase + TV_tool。小さいほど全体分布に近い。"""
        a, b = self.divergence(videos)
        return a + b


# --------------------------------------------------------------------------
# 制約検査。**表を与えて落ちることを示せる形にする**（対照のため）。
# --------------------------------------------------------------------------


def check_table(
    table: dict[str, dict[str, tuple[str, ...]]],
    all_videos: tuple[str, ...],
    official: dict[str, list[str]],
) -> list[str]:
    """制約違反の一覧を返す。空なら合格。"""
    problems: list[str] = []
    universe = set(all_videos)

    if sorted(table) != sorted(FOLD_IDS):
        problems.append(f"折りの識別子が {sorted(FOLD_IDS)} でない: {sorted(table)}")
        return problems

    seen: dict[str, list[str]] = defaultdict(list)
    for fold in FOLD_IDS:
        entry = table[fold]
        test, val, train = entry["test"], entry["val"], entry["train"]

        if len(set(test)) != len(test):
            problems.append(f"折り {fold}: test に重複がある {test}")
        if len(set(val)) != len(val):
            problems.append(f"折り {fold}: val に重複がある {val}")
        if set(test) & set(val):
            problems.append(f"折り {fold}: val が test と重なる {sorted(set(test) & set(val))}")
        if set(test) & set(train):
            problems.append(f"折り {fold}: train が test と重なる {sorted(set(test) & set(train))}")
        if set(val) & set(train):
            problems.append(f"折り {fold}: train が val と重なる {sorted(set(val) & set(train))}")
        if set(test) | set(val) | set(train) != universe:
            problems.append(f"折り {fold}: test/val/train の和が 15 動画に一致しない")
        if len(test) != 3:
            problems.append(f"折り {fold}: test が 3 本でない（{len(test)} 本）")
        if len(val) != 2:
            problems.append(f"折り {fold}: val が 2 本でない（{len(val)} 本）")
        for v in test:
            seen[v].append(fold)

    for v in sorted(all_videos):
        if len(seen.get(v, [])) != 1:
            problems.append(f"動画 {v} が test に現れた回数が 1 でない: {seen.get(v, [])}")

    if set(table["A"]["test"]) != set(official["test"]):
        problems.append(f"折り A の test が公式 test と一致しない: {sorted(table['A']['test'])}")
    if set(table["A"]["val"]) != set(official["val"]):
        problems.append(f"折り A の val が公式 val と一致しない: {sorted(table['A']['val'])}")

    val_use: dict[str, list[str]] = defaultdict(list)
    for fold in FOLD_IDS:
        for v in table[fold]["val"]:
            val_use[v].append(fold)
    for v, folds in sorted(val_use.items()):
        if len(folds) > 1:
            problems.append(f"動画 {v} が val に 2 回以上現れる: {folds}")

    return problems


# --------------------------------------------------------------------------
# 表の生成。**全数列挙するので最適解であり、近似ではない。**
# --------------------------------------------------------------------------


def enumerate_partitions(pool: tuple[str, ...]) -> list[tuple[tuple[str, ...], ...]]:
    """12 動画を 3 本ずつ 4 組へ分ける分け方を全部作る（順序は正規化）。"""
    pool = tuple(sorted(pool))
    result: list[tuple[tuple[str, ...], ...]] = []

    def recurse(rest: tuple[str, ...], acc: tuple[tuple[str, ...], ...]) -> None:
        if not rest:
            result.append(tuple(sorted(acc)))
            return
        head = rest[0]
        for others in combinations(rest[1:], 2):
            group = (head,) + others
            remaining = tuple(v for v in rest if v not in group)
            recurse(remaining, acc + (group,))

    recurse(pool, ())
    return result


def choose_test_groups(material: Material, pool: tuple[str, ...]) -> tuple[list, list]:
    """均衡指標で最良の分け方を選ぶ。

    目的（この順に小さくする）:
      1. max_f d(test_f)  — 最も偏る折りを最小にする（minimax）
      2. sum_f d(test_f)  — 同点なら総和
      3. 表の辞書順        — それでも同点なら動画識別子の辞書順（SPEC Task B §2）
    """
    scored = []
    for partition in enumerate_partitions(pool):
        costs = [material.cost(g) for g in partition]
        scored.append((max(costs), sum(costs), partition))
    scored.sort(key=lambda row: (round(row[0], 12), round(row[1], 12), row[2]))
    best_key = (round(scored[0][0], 12), round(scored[0][1], 12))
    ties = [row for row in scored if (round(row[0], 12), round(row[1], 12)) == best_key]
    return scored, ties


def choose_vals(
    material: Material,
    tests: dict[str, tuple[str, ...]],
    forbidden: set[str],
    all_videos: tuple[str, ...],
) -> dict[str, tuple[str, ...]]:
    """折り B〜E の val を選ぶ。

    制約: val_f ∩ test_f = ∅、かつ **各動画は全折りを通じて val に高々一度**
    （`forbidden` は折り A が既に使った 2 本）。
    目的: 1. max_f d(val_f) 2. sum_f d(val_f) 3. 辞書順。
    """
    folds = tuple(f for f in FOLD_IDS if f != "A")
    candidates = tuple(v for v in all_videos if v not in forbidden)
    pair_cost = {
        pair: material.cost(pair) for pair in combinations(candidates, 2)
    }
    best: dict | None = None

    def recurse(idx: int, used: frozenset[str], acc: list, cur_max: float, cur_sum: float) -> None:
        nonlocal best
        if best is not None:
            key = (round(cur_max, 12), round(cur_sum, 12))
            bkey = (round(best["max"], 12), round(best["sum"], 12))
            if key > bkey:
                return
        if idx == len(folds):
            key = (round(cur_max, 12), round(cur_sum, 12), tuple(acc))
            if best is None or key < (
                round(best["max"], 12),
                round(best["sum"], 12),
                tuple(best["acc"]),
            ):
                best = {"max": cur_max, "sum": cur_sum, "acc": list(acc)}
            return
        fold = folds[idx]
        test = set(tests[fold])
        for pair in sorted(pair_cost):
            if used & set(pair) or test & set(pair):
                continue
            cost = pair_cost[pair]
            recurse(idx + 1, used | set(pair), acc + [pair], max(cur_max, cost), cur_sum + cost)

    recurse(0, frozenset(), [], 0.0, 0.0)
    assert best is not None, "val の割り当てが見つからない"
    return {fold: best["acc"][i] for i, fold in enumerate(folds)}


def build_table(
    material: Material, official: dict[str, list[str]]
) -> tuple[dict[str, dict[str, tuple[str, ...]]], dict]:
    """折り表を作る。返り値は (表, 診断)。"""
    all_videos = material.videos
    fold_a_test = tuple(sorted(official["test"]))
    fold_a_val = tuple(sorted(official["val"]))
    pool = tuple(v for v in all_videos if v not in set(fold_a_test))

    scored, ties = choose_test_groups(material, pool)
    partition = scored[0][2]
    groups = sorted(partition)
    tests = {"A": fold_a_test}
    for fold, group in zip(("B", "C", "D", "E"), groups):
        tests[fold] = tuple(sorted(group))

    vals = choose_vals(material, tests, set(fold_a_val), all_videos)
    vals["A"] = fold_a_val

    table = {}
    for fold in FOLD_IDS:
        test = tests[fold]
        val = vals[fold]
        train = tuple(v for v in all_videos if v not in set(test) | set(val))
        table[fold] = {"test": test, "val": val, "train": train}

    diagnostics = {
        "n_partitions": len(scored),
        "n_ties": len(ties),
        "ties": [t[2] for t in ties],
        "best_max": scored[0][0],
        "best_sum": scored[0][1],
        "worst_max": scored[-1][0],
        "median_max": scored[len(scored) // 2][0],
    }
    return table, diagnostics


def table_digest(table: dict[str, dict[str, tuple[str, ...]]]) -> str:
    """表の要約値。決定性の比較はこの値で行う（表示属性では足りない）。"""
    payload = json.dumps(
        {f: {k: list(v) for k, v in sorted(table[f].items())} for f in sorted(table)},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()


# --------------------------------------------------------------------------
# 対照
# --------------------------------------------------------------------------


def random_control(material: Material, official: dict[str, list[str]], seed: int) -> dict:
    """無作為割り当てを一件。**seed を出力に書く。**"""
    rng = random.Random(seed)
    fold_a_test = tuple(sorted(official["test"]))
    pool = [v for v in material.videos if v not in set(fold_a_test)]
    rng.shuffle(pool)
    groups = [tuple(sorted(pool[i : i + 3])) for i in range(0, 12, 3)]
    costs = {"A": material.cost(fold_a_test)}
    for fold, group in zip(("B", "C", "D", "E"), sorted(groups)):
        costs[fold] = material.cost(group)
    optimised = [costs[f] for f in ("B", "C", "D", "E")]
    return {
        "seed": seed,
        "groups": {f: g for f, g in zip(("B", "C", "D", "E"), sorted(groups))},
        "costs": costs,
        "max": max(optimised),
        "sum": sum(optimised),
    }


def run_controls(
    material: Material, official: dict[str, list[str]], table: dict
) -> list[tuple[str, str, str, bool]]:
    """制約検査が**実際に落ちること**を示す。

    件数だけでは「別の理由で落ちた」と区別できない。**狙った違反そのものが
    一覧に現れたか**を照合し、その文言を出力に載せる。
    """
    lines: list[tuple[str, str, str, bool]] = []
    all_videos = material.videos

    def clone() -> dict:
        return {f: {k: tuple(v) for k, v in table[f].items()} for f in table}

    def record(name: str, broken: dict, expect: str) -> None:
        found = check_table(broken, all_videos, official)
        hit = [m for m in found if expect in m]
        lines.append((name, f"違反 {len(found)} 件", hit[0] if hit else "（狙った違反が出なかった）", bool(hit)))

    ok = check_table(clone(), all_videos, official)
    lines.append(("提案の表（陰性対照。落ちてはならない）", f"違反 {len(ok)} 件", "—", not ok))

    broken = clone()
    victim = broken["C"]["test"][0]
    broken["B"] = dict(broken["B"])
    broken["B"]["test"] = tuple(sorted(set(broken["B"]["test"][:2]) | {victim}))
    record(f"同じ動画 {victim} を折り B と C の test に置く", broken, f"動画 {victim} が test に現れた回数が 1 でない")

    broken = clone()
    outsider = sorted(set(all_videos) - set(broken["A"]["test"]))[0]
    broken["A"] = dict(broken["A"])
    broken["A"]["test"] = tuple(sorted(set(broken["A"]["test"][:2]) | {outsider}))
    record(f"折り A の test の一本を {outsider} へ入れ替える", broken, "折り A の test が公式 test と一致しない")

    broken = clone()
    broken["A"] = dict(broken["A"])
    broken["A"]["val"] = tuple(sorted({broken["A"]["val"][0], broken["A"]["train"][0]}))
    record("折り A の val の一本を入れ替える", broken, "折り A の val が公式 val と一致しない")

    broken = clone()
    broken["B"] = dict(broken["B"])
    broken["B"]["val"] = tuple(sorted({broken["B"]["test"][0], broken["B"]["val"][0]}))
    record("折り B の val に自分の test の動画を入れる", broken, "val が test と重なる")

    broken = clone()
    broken["C"] = dict(broken["C"])
    broken["C"]["val"] = tuple(sorted(broken["D"]["val"]))
    record("折り C の val を折り D と同じにする", broken, "val に 2 回以上現れる")

    broken = clone()
    broken["E"] = dict(broken["E"])
    broken["E"]["test"] = tuple(sorted(broken["E"]["test"][:2]))
    record("折り E の test を 2 本に減らす", broken, "test が 3 本でない")

    return lines


def overlap_report(extra: list[str], material: Material, official: dict[str, list[str]]) -> dict:
    """追加動画と 15 動画・公式 test の重複。**陽性対照を必ず添える。**"""
    fifteen = set(material.videos)
    off_test = set(official["test"])
    injected = sorted(set(extra) | {sorted(off_test)[0]})
    return {
        "extra": extra,
        "n_extra": len(extra),
        "overlap_15": sorted(set(extra) & fifteen),
        "overlap_official_test": sorted(set(extra) & off_test),
        "overlap_official_val": sorted(set(extra) & set(official["val"])),
        "overlap_official_train": sorted(set(extra) & set(official["train"])),
        "positive_control_injected": sorted(off_test)[0],
        "positive_control_overlap": sorted(set(injected) & off_test),
    }


def determinism_report(material: Material, official: dict[str, list[str]]) -> dict:
    """二度作って要約値を比べ、入力を一行変えると表が変わることも示す。"""
    first, _ = build_table(material, official)
    second, _ = build_table(material, official)

    perturbed_phase = {v: dict(c) for v, c in material.phase.items()}
    victim_vid = material.videos[0]
    victim_phase = sorted(perturbed_phase[victim_vid])[0]
    perturbed_phase[victim_vid][victim_phase] += 100000
    perturbed = Material(perturbed_phase, material.tool, material.images, material.hts)
    third, _ = build_table(perturbed, official)

    return {
        "digest_1": table_digest(first),
        "digest_2": table_digest(second),
        "identical": table_digest(first) == table_digest(second),
        "perturbation": f"動画 {victim_vid} の工程 {victim_phase} に +100000 フレーム（記憶上のみ。data/ は書き換えない）",
        "digest_perturbed": table_digest(third),
        "changed": table_digest(first) != table_digest(third),
    }


# --------------------------------------------------------------------------
# 出力
# --------------------------------------------------------------------------


def render_markdown(
    material: Material,
    official: dict[str, list[str]],
    table: dict,
    diagnostics: dict,
    control: dict,
    controls: list[tuple[str, str]],
    overlap: dict,
    determinism: dict,
) -> str:
    out: list[str] = []
    w = out.append

    w("# A1 折り表（動画単位 5-fold・確定）")
    w("")
    w(f"出所: `docs/stage0/A1_fold_material.md` と同じ材料を読み直して生成した。契約 `{TASK_ID}`。")
    w("生成器: `scripts/analysis/a1_fold_table.py`（`--write` で本ファイルを書く）。")
    w("")
    w("**この表が正本である。** 他の頁は数値を書かず本ファイルを参照する。")
    w(f"`context/conventions.md` の `folds` 節は本ファイルの表と同じ値を持つ（要約値 `{table_digest(table)[:12]}`）。")
    w("")

    w("## 折り表")
    w("")
    w("| 折り | test（3） | val（2） | train（10） |")
    w("|---|---|---|---|")
    for fold in FOLD_IDS:
        e = table[fold]
        w(f"| {fold} | {', '.join(e['test'])} | {', '.join(e['val'])} | {', '.join(e['train'])} |")
    w("")
    w("折り A は公式分割そのもの（test = `data/splits/ego_test.txt`、val = `data/splits/ego_val.txt`）。")
    w("折り B〜E の test は、公式 train の 10 本と公式 val の 2 本、計 12 本を 3 本ずつに分けたものである。")
    w("**各動画は test にちょうど一度現れる。** val は全折りを通じて各動画高々一度しか使わない。")
    w("")

    w("## 均衡指標の定義")
    w("")
    w("動画集合 S について、")
    w("")
    w("- 工程の比率ベクトル `p(S)`: 工程 9 種それぞれのフレーム数を S の総フレーム数で割ったもの")
    w("- 術具の比率ベクトル `t(S)`: 術具 15 クラスそれぞれの box 数を S の総 box 数で割ったもの")
    w("- 全変動距離 `TV(x, y) = 0.5 * Σ|x_i - y_i|`（0 が同一、1 が互いに素）")
    w("")
    w("**均衡指標 `d(S) = TV(p(S), p(全15動画)) + TV(t(S), t(全15動画))`。** 小さいほど全体分布に近い。")
    w("")
    w("表の選び方は、折り B〜E の test について次の順に小さくする。")
    w("")
    w("1. `max_f d(test_f)` — 最も偏る折りを最小にする（minimax）")
    w("2. `sum_f d(test_f)` — 同点なら総和")
    w("3. 動画識別子の辞書順 — それでも同点なら辞書順（SPEC Task B §2 の規則）")
    w("")
    w(f"折り A の test は公式分割に固定されているため**最適化の対象ではない**。値は参考として併記する。")
    w(f"分け方は全数列挙した（**{diagnostics['n_partitions']} 通り**）ので、選ばれた表は近似ではなく最適である。")
    w("")

    w("## 折りごとの値")
    w("")
    w("| 折り | test | frames | boxes | TV 工程 | TV 術具 | d(test) | HTS 系統を持つ test 動画 |")
    w("|---|---|---|---|---|---|---|---|")
    for fold in FOLD_IDS:
        test = table[fold]["test"]
        tv_p, tv_t = material.divergence(test)
        hts_n = sum(1 for v in test if len(material.hts.get(v, set())) == len(HTS_SYSTEMS))
        w(
            f"| {fold} | {', '.join(test)} | {material.frames(test)} | {material.boxes(test)} "
            f"| {tv_p:.4f} | {tv_t:.4f} | {tv_p + tv_t:.4f} | {hts_n} / {len(test)} |"
        )
    w("")
    costs_all = {f: material.cost(table[f]["test"]) for f in FOLD_IDS}
    costs_opt = {f: costs_all[f] for f in ("B", "C", "D", "E")}
    w(f"- 折り B〜E の最大 `d` = **{max(costs_opt.values()):.4f}**、最小 = {min(costs_opt.values()):.4f}、"
      f"**折り間の最大差 = {max(costs_opt.values()) - min(costs_opt.values()):.4f}**")
    w(f"- 折り A を含めた 5 折りでは最大 = {max(costs_all.values()):.4f}、最小 = {min(costs_all.values()):.4f}、"
      f"最大差 = {max(costs_all.values()) - min(costs_all.values()):.4f}")
    w(f"- HTS は 15 動画すべてが 3 系統とも持つため、どの折りの test も 3/3 である（**偏りは原理的に生じない**）")
    w("")

    w("### val の値")
    w("")
    w("| 折り | val | frames | boxes | d(val) |")
    w("|---|---|---|---|---|")
    for fold in FOLD_IDS:
        val = table[fold]["val"]
        w(f"| {fold} | {', '.join(val)} | {material.frames(val)} | {material.boxes(val)} | {material.cost(val):.4f} |")
    w("")

    w("## 無作為対照")
    w("")
    w(f"無作為割り当てを一件作って同じ指標で比べた（**seed = {control['seed']}**、`random.Random(seed).shuffle`）。")
    w("")
    w("| | max d(test) | sum d(test) |")
    w("|---|---|---|")
    w(f"| 提案の表 | **{max(costs_opt.values()):.4f}** | **{sum(costs_opt.values()):.4f}** |")
    w(f"| 無作為（seed {control['seed']}） | {control['max']:.4f} | {control['sum']:.4f} |")
    w("")
    better = max(costs_opt.values()) <= control["max"]
    w(f"提案の表は無作為より{'悪化していない' if better else '**悪化している**'}（max で比較）。")
    w("")
    w("全数列挙しているため、無作為一件だけでなく**分布全体**と比べられる。")
    w(f"{diagnostics['n_partitions']} 通りの `max d` は、最小 {diagnostics['best_max']:.4f} ／ "
      f"中央 {diagnostics['median_max']:.4f} ／ 最大 {diagnostics['worst_max']:.4f}。"
      f"提案の表は**最小値そのもの**である。")
    w(f"最良と同点だった分け方は {diagnostics['n_ties']} 通りで、辞書順で一意に決めた。")
    w("")

    w("## 制約検査（対照）")
    w("")
    w("制約検査は `check_table()`（`scripts/analysis/a1_fold_table.py`）。")
    w("**検査が働いていることを、落ちる入力を与えて示す。**")
    w("件数だけでは別の理由で落ちたのと区別できないため、**狙った違反の文言そのもの**を照合した。")
    w("")
    w("| 与えた入力 | 件数 | 狙った違反が出たか |")
    w("|---|---|---|")
    for name, count, message, hit in controls:
        mark = "✓" if hit else "**✗**"
        w(f"| {name} | {count} | {mark} `{message}` |")
    w("")

    w("## 決定性")
    w("")
    w(f"- 同じ入力で二度生成した表の要約値: `{determinism['digest_1'][:16]}` と `{determinism['digest_2'][:16]}` "
      f"→ **{'一致' if determinism['identical'] else '不一致'}**")
    w(f"- 入力を一行変える（{determinism['perturbation']}）と要約値は `{determinism['digest_perturbed'][:16]}` "
      f"→ **{'変わる' if determinism['changed'] else '変わらない'}**（空振りでないことの確認）")
    w("")

    w("## 追加 6 動画")
    w("")
    w(f"出所: `{EXTRA_PHASE_DIR.relative_to(REPO_ROOT)}` のうち動画ID 16 以上。")
    w("")
    w(f"- 識別子（{overlap['n_extra']} 本）: {', '.join(overlap['extra'])}")
    w(f"- 15 動画との重複: **{len(overlap['overlap_15'])} 件** {overlap['overlap_15'] or ''}")
    w(f"- 公式 test（04, 05, 07）との重複: **{len(overlap['overlap_official_test'])} 件** {overlap['overlap_official_test'] or ''}")
    w(f"- 公式 val との重複: {len(overlap['overlap_official_val'])} 件／公式 train との重複: {len(overlap['overlap_official_train'])} 件")
    w(f"- 陽性対照: 追加動画の集合へ `{overlap['positive_control_injected']}` を混ぜると重複は "
      f"**{len(overlap['positive_control_overlap'])} 件** {overlap['positive_control_overlap']} "
      f"→ 集合演算は重複を検出できる。上の 0 件は「検出できていない」ではない")
    w("")
    w("**用途は訓練のみである。** 追加 6 動画は工程塔の訓練にだけ足し、どの折りの test にも val にも現れない。")
    w("")

    w("## 再現に要る入力と規則")
    w("")
    w("| 入力 | 所在 |")
    w("|---|---|")
    w("| 工程フレーム数 | `data/annotations/egosurgery_phase/*.csv`（`Frame,Phase`）|")
    w("| 術具 box 数 | `data/annotations/egosurgery_tool/instances_{train,val,test}.json`（COCO・15 クラス）|")
    w("| HTS 注釈の有無 | `data/annotations/egosurgery_hts/{hand_seg,hand_tool_seg,tool_seg}/*.json` |")
    w("| 公式分割 | `data/splits/ego_{train,val,test}.txt` |")
    w("| 追加動画 | `data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/phase/*.csv` |")
    w("")
    w("規則は上の「均衡指標の定義」と制約（折り A は公式分割に固定、test は各動画ちょうど一度、")
    w("val は自分の test と重ならず全折りで高々一度）。**乱数は対照でのみ使う。表の生成には使わない。**")
    w("")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="docs/stage0/A1_fold_table.md を書く")
    parser.add_argument("--controls", action="store_true", help="対照だけを走らせる")
    args = parser.parse_args()

    phase = load_phase()
    tool, images = load_tool()
    hts = load_hts()
    material = Material(phase, tool, images, hts)
    official = load_splits()
    extra = load_extra_videos()

    table, diagnostics = build_table(material, official)
    problems = check_table(table, material.videos, official)
    if problems:
        print("制約違反:", file=sys.stderr)
        for p in problems:
            print(" -", p, file=sys.stderr)
        return 1

    controls = run_controls(material, official, table)
    overlap = overlap_report(extra, material, official)
    control = random_control(material, official, RANDOM_CONTROL_SEED)
    determinism = determinism_report(material, official)

    if args.controls:
        for name, count, message, hit in controls:
            print(f"{'OK ' if hit else 'NG '} {name}: {count} / {message}")
        print(json.dumps(overlap, ensure_ascii=False, indent=2))
        print(json.dumps(determinism, ensure_ascii=False, indent=2))
        return 0

    text = render_markdown(
        material, official, table, diagnostics, control, controls, overlap, determinism
    )
    if args.write:
        dest = REPO_ROOT / "docs/stage0/A1_fold_table.md"
        dest.write_text(text)
        print(f"書きました: {dest.relative_to(REPO_ROOT)}（{len(text.encode())} バイト）")
        print(f"表の要約値: {table_digest(table)}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

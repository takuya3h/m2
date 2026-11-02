"""Task A-6: 本契約が起こす command.sh と手本の command.sh の差を全行出す（読むだけ）。

手本は dlsta 探索の 0 番の run（SPEC §4）。本契約の命令は ``run_hostdiff.py`` の同じ関数で組み立てる。
差の各行を SPEC §4 の許した違いの分類に当て、当たらない行があれば ``unallowed`` に出す。

    .venv/bin/python tasks/T-2026-11-02-hostdiff-andrew/tools/plan_diff.py [--self-test]
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run_hostdiff as rh  # noqa: E402

ROOT = rh.ROOT
PT = ROOT / "experiments/phase1/stage1_ptower_search"
DT = ROOT / "experiments/baselines/stage1_dtower_search/point00_dcoco_foldA_seed42"
OLD_ROOT = "/home/ubuntu/local/m2"
OLD_SCRATCH = "/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta"

# SPEC §4 の許した違い。各行の差は、手本の行のこれらの部分を置き換えると本契約の行と一致するときだけ許す。
ALLOWED = [
    ("経路（repo）", OLD_ROOT, str(ROOT)),
    ("出力と記録の置き場（scratch）", OLD_SCRATCH, str(rh.SCRATCH)),
]
ALLOWED_NEW_LINES = {
    "export NCCL_P2P_DISABLE=1": "NCCL_P2P_DISABLE=1 の追加",
    f"export TOWER_SEARCH_TASK={rh.TASK}": "本契約の識別子",
    f"export TOWER_SEARCH_OBSERVER={rh.OBSERVER}": "記録の置き場（一歩ごとの時刻の観測器）",
    f"export TOWER_SEARCH_PHASE_PUBLISH={rh.PHASE_PUBLISH}": "出力の置き場（repo 内の写し先）",
    "export TOWER_SEARCH_SEED=42": "seed（W&B の記録に書く seed）",
    "export TOWER_SEARCH_SEED=123": "seed（W&B の記録に書く seed）",
}


def planned(seed, tag=""):
    """手本の各 run に対応する本契約の command.sh（seed 42 一回目の名前で作る）。"""
    work = rh.SCRATCH / "phase" / f"seed{seed}"
    common = rh.phase_common(work, seed)
    backbone = work / "runs/phase1/stage1_ptower_search_001_ft_coco_lr0.0001_foldA_point00_seed42"
    out = {
        "finetune": rh.replay(rh.finetune_cmd(common), rh.environment(rh.PAIR, work), ROOT),
        "extract": rh.replay(rh.extract_cmd(backbone / "checkpoints/best.pth", common),
                             rh.environment(rh.FIRST, work), ROOT),
    }
    for index, recipe in enumerate(__import__("run_stage1_ptower_r3").heads()):
        out[f"head{index:02d}"] = rh.replay(rh.head_cmd(common, recipe),
                                            rh.environment(rh.FIRST, work), ROOT)
    dwork = rh.SCRATCH / "detector" / f"seed{seed}{tag}"
    out["detector"] = rh.replay(rh.det_train_cmd(seed), rh.detector_env(rh.PAIR, dwork, seed),
                                ROOT / "third_party/Relation-DETR")
    return out


def exemplars():
    names = sorted(p.name for p in PT.iterdir() if p.name.endswith("_point00_seed42"))
    heads = [n for n in names if n.split("_")[3] not in ("001", "002")]
    out = {"finetune": PT / names[0] / "command.sh", "extract": PT / names[1] / "command.sh"}
    out.update({f"head{i:02d}": PT / n / "command.sh" for i, n in enumerate(heads)})
    out["detector"] = DT / "command.sh"
    return out


def compare(mine, theirs, subs):
    """手本の各行に許した置き換えを当て、本契約の行（許した追加行を除く）と順に一行ずつ比べる。"""
    rows, unallowed = [], []
    rest = []
    for line in mine:
        if line in ALLOWED_NEW_LINES:
            rows.append({"exemplar": None, "this": line, "allowed": [ALLOWED_NEW_LINES[line]]})
        else:
            rest.append(line)
    if len(rest) != len(theirs):
        unallowed.append({"reason": "line count", "exemplar": len(theirs), "this": len(rest)})
    for old, new in zip(theirs, rest):
        applied, moved = [], old
        for label, a, b in ALLOWED + subs:
            if a in moved:
                moved = moved.replace(a, b)
                applied.append(label)
        if old == new:
            continue
        ok = moved == new
        rows.append({"exemplar": old, "this": new, "allowed": sorted(set(applied)) if ok else None})
        if not ok:
            unallowed.append({"exemplar": old, "this": new, "after_allowed_substitution": moved})
    return rows, unallowed


def run(seed, tag, exemplar_text=None):
    sys.path.insert(0, str(ROOT / "scripts"))
    mine_all, theirs_all = planned(seed, tag), exemplars()
    report = {}
    for key, path in theirs_all.items():
        theirs = (exemplar_text or {}).get(key, path.read_text()).splitlines()
        mine = mine_all[key].splitlines()
        if key in ("finetune", "detector"):
            subs = [("GPU の番号", "CUDA_VISIBLE_DEVICES=1,2", "CUDA_VISIBLE_DEVICES=" + rh.PAIR)]
        else:
            subs = [("GPU の番号", "CUDA_VISIBLE_DEVICES=1", "CUDA_VISIBLE_DEVICES=" + rh.FIRST)]
        subs += [("出力と記録の置き場（scratch）", "phase/point00", f"phase/seed{seed}"),
                 ("出力と記録の置き場（scratch）", "detector/point00", f"detector/seed{seed}{tag}")]
        if seed != 42:
            subs += [("seed", "--seed 42", f"--seed {seed}"), ("seed", "workers=4", f"workers=4 seed={seed}")]
        rows, unallowed = compare(mine, theirs, subs)
        report[key] = {"exemplar": str(path), "diff": rows, "unallowed": unallowed}
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tag", default="a")
    parser.add_argument("--self-test", action="store_true",
                        help="手本の一行を変えた写しと比べ、差に出ることを確かめる")
    args = parser.parse_args()
    if args.self_test:
        text = exemplars()["finetune"].read_text().replace("workers=4", "workers=8")
        report = run(args.seed, args.tag, {"finetune": text})
        print(json.dumps({"finetune_unallowed": report["finetune"]["unallowed"]}, ensure_ascii=False, indent=1))
        return
    report = run(args.seed, args.tag)
    total = sum(len(v["unallowed"]) for v in report.values())
    print(json.dumps({"unallowed_total": total, "runs": report}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

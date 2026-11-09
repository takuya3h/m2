"""本契約が変えてはならない場所の要約値（T-2026-11-09-grasp-pilot-converge、SPEC §6 の 2・3・4 と §7 の i）。

T-2026-11-09-grasp-roitoken-transition-pilot の digests.py の写し。根に前の予備の置き場・run・保存先を足し、
experiments/phase1/grasprt_* は glob で一つずつ根にする。自分の tasks のフォルダを除く。
`scripts` の根は本契約が新しい型を足すため変わる（dp_model.py・dp_train.py）。変わったファイルは --files で別に出す。
各根の下のすべてのファイルを中身で sha256 し、(相対経路, 大きさ, sha256) の並びをもう一度 sha256 する。
ファイルが変わる・増える・減ると、その根の値が変わる。シンボリックリンクは辿らず、リンク先の文字列で数える。
二つの仮想環境は、整列した ``uv pip freeze`` と site-packages の同じ走査で要約する。

    python digests.py --out <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OLD = "/home/ubuntu/slocal2/stage2pilot_store"
ROOTS = [
    # §6-4 third_party、重ねの BODY、既存の台本
    "third_party",
    "/home/ubuntu/slocal2/s2fix-bengio-body",
    "scripts",
    "configs",
    # §6-3 data/raw・data/external・注釈・data/processed
    "data/raw",
    "data/external",
    "data/annotations",
    "data/processed",
    "data/splits",
    # §6-2 前回までの run の置き場・集計・tasks・版管理の外の保存先（本契約が読むもの）
    "experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42",
    "experiments/phase1/grasptower_G_all_seed42",
    "experiments/phase1/grasptower_G_H1_seed42",
    "experiments/phase1/grasptower_G_H2_seed42",
    "experiments/analysis/grasp_tower_rebuild",
    "experiments/analysis/grasp_pilot_arms",
    "experiments/analysis/stage2_w23_bengio",
    "experiments/analysis/grasp_cards_survey",
    "experiments/analysis/stage2_pilot_folda",
    "tasks",
    f"{OLD}/T-2026-11-05-grasp-tower-rebuild",
    f"{OLD}/T-2026-10-18-stage2-pilot-folda",
    f"{OLD}/T-2026-11-06-grasp-pilot-arms",
    f"{OLD}/T-2026-11-01-stage2-w23-bengio",
    f"{OLD}/T-2026-11-08-grasp-cards-survey",
    # 前の予備（PR 307）の集計・道具・保存先（読むだけ）
    "experiments/analysis/grasp_roitoken_transition_pilot",
    f"{OLD}/T-2026-11-09-grasp-roitoken-transition-pilot",
]
ROOTS += sorted(str(p.relative_to(ROOT)) for p in (ROOT / "experiments/phase1").glob("grasprt_*"))
# 本契約が読む重み（§6 の j の「既存の重み」）
WEIGHTS = {
    "P_ft": "experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42/checkpoints/best.pth",
    "G_all": f"{OLD}/T-2026-11-05-grasp-tower-rebuild/g/ckpt/all/best.pth",
    "G_H1": f"{OLD}/T-2026-11-05-grasp-tower-rebuild/g/ckpt/H1/best.pth",
    "G_H2": f"{OLD}/T-2026-11-05-grasp-tower-rebuild/g/ckpt/H2/best.pth",
    "P_head": f"{OLD}/T-2026-10-18-stage2-pilot-folda/efros_ptower/experiments/phase1/"
              "stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42/checkpoints/best.pth",
    "P_cache": f"{OLD}/T-2026-10-18-stage2-pilot-folda/efros_ptower/data/processed/stage1_features/"
               "p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz",
}
VENVS = [".venv", ".venv-relation-detr"]
# 本契約の tasks/ の自分のフォルダは書く場所なので、tasks の根から除く
OWN_TASK = "T-2026-11-09-grasp-pilot-converge"


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def walk(path, skip_top=()):
    path = Path(path)
    if path.is_file():
        return [(path.name, path.stat().st_size, file_sha(path))]
    rows = []
    for dirpath, dirnames, filenames in os.walk(path):
        if Path(dirpath) == path:
            dirnames[:] = [d for d in dirnames if d not in skip_top]
        dirnames.sort()
        for name in sorted(filenames) + sorted(d for d in dirnames if (Path(dirpath) / d).is_symlink()):
            full = Path(dirpath) / name
            if full.is_symlink():
                rows.append((str(full.relative_to(path)), -1, "symlink:" + os.readlink(full)))
            elif full.is_file():
                rows.append((str(full.relative_to(path)), full.stat().st_size, file_sha(full)))
    return rows


def summary(rows):
    return {"files": len(rows), "bytes": sum(r[1] for r in rows if r[1] > 0),
            "sha256": hashlib.sha256(json.dumps(rows).encode()).hexdigest()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--files", default=None, help="根ごとのファイルの並び（相対経路, 大きさ, sha256）も書く json")
    args = ap.parse_args()
    result = {"roots": {}, "weights": {}, "venvs": {}}
    files = {}
    for rel in ROOTS:
        base = Path(rel) if rel.startswith("/") else ROOT / rel
        skip = (OWN_TASK,) if rel == "tasks" else ()
        rows = walk(base, skip)
        if rel in ("scripts", "tasks", "configs"):
            files[rel] = rows
        result["roots"][rel] = summary(rows)
        print(rel, result["roots"][rel], flush=True)
    for key, rel in WEIGHTS.items():
        base = Path(rel) if rel.startswith("/") else ROOT / rel
        result["weights"][key] = {"path": rel, "sha256": file_sha(base), "bytes": base.stat().st_size}
    for venv in VENVS:
        freeze = subprocess.run(["uv", "pip", "freeze", "--python", str(ROOT / venv / "bin/python")],
                                capture_output=True, text=True, check=True).stdout
        lines = sorted(line for line in freeze.splitlines() if line.strip())
        site = next((ROOT / venv / "lib").glob("python*/site-packages"))
        result["venvs"][venv] = {"freeze_lines": len(lines),
                                 "freeze_sha256": hashlib.sha256("\n".join(lines).encode()).hexdigest(),
                                 "site_packages": summary(walk(site))}
    Path(args.out).write_text(json.dumps(result, indent=1) + "\n")
    if args.files:
        Path(args.files).write_text(json.dumps(files) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()

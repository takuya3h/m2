"""Task A: 開始状態と、保存済みの予測・注釈の実在の確認（非公式 T-2026-11-22-dtower-class-error-breakdown）。

    .venv/bin/python experiments/analysis/dtower_class_error_breakdown/tools/a_start.py --scratch <作業用の置き場>

書くもの: start/a_start.json（開始状態・前提の在否・仮想環境・目録・対照）。読んだファイルの sha256 は reads.jsonl（完了判定 j の開始時の値）。
--scratch には対照の写し（1 バイト変えた予測）を置く。保存先と repo の材料には書かない。
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

PREREQ = [  # SPEC §1.1・§3 が名指すファイル（在否だけを見る。test のファイルは名指さない）
    "experiments/analysis/dtower_rerun/frozen_towers.json",
    "experiments/analysis/dtower_rerun/tools/eval_dump.py",
    "experiments/analysis/dtower_rerun/tools/run_rerun.py",
    "experiments/analysis/dtower_rerun/REPORT.md",
    "scripts/eval_relation_detr_map.py",
    "experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/per_class_ap.json",
    "tasks/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/RESULT.md",
    "tasks/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/audit.md",
    "tasks/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/result.yaml",
    "tasks/T-2026-11-07-dtower-rerun/RESULT.md",
    "tasks/T-2026-11-07-dtower-rerun/result.yaml",
    "experiments/analysis/stage2_pilot_fix/identity/pd_plain.json",
    "experiments/analysis/stage2_pilot_fix/report.json",
    "docs/phase_tool_annotation_stats.md",
    "docs/stage0/A6_error_decomposition.md",
    "docs/stage0/A1_fold_table.md",
    "src/egosurgery/datasets/constants.py",
    "tasks/inbox.d/T-2026-10-18-stage2-pilot-folda.md",
    "scripts/stage2pilot/common.py",
    "scripts/stage2pilot/det_metrics.py",
    "data/processed/phase_manifest/train.json",
    "data/processed/phase_manifest/val.json",
    "data/processed/phase_manifest/phase_vocab.json",
]


def sh(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, cwd=C.ROOT, capture_output=True, text=True).stdout.strip()


def pycocotools_in(venv: str) -> dict:
    py = Path(venv) / "bin/python"
    if not py.exists():
        return {"venv": venv, "python": False, "pycocotools": None}
    r = subprocess.run([str(py), "-c", "from importlib.metadata import version; import pycocotools, numpy; "
                        "print(version('pycocotools'), numpy.__version__)"], capture_output=True, text=True)
    return {"venv": venv, "python": True, "pycocotools": r.stdout.split()[0] if r.returncode == 0 else None,
            "numpy": r.stdout.split()[1] if r.returncode == 0 else None}


def inventory(tower: str, fold: str, frozen: dict) -> dict:
    path = C.pred_path(tower, fold)
    row = {"tower": tower, "fold": fold, "path": str(path), "exists": path.exists()}
    if not path.exists():
        row["reason"] = "ファイルが無い"
        return row
    raw = C.read_bytes(path, f"{tower} Fold {fold} の保存済みの val の予測（目録）")
    data = json.loads(gzip.decompress(raw))
    dets = data["detections"] if tower == "T1" else data
    ann = C.load_ann(fold, "val")
    row.update(sha256=C.sha256(path), bytes=len(raw), predictions=len(dets),
               images_with_predictions=len({d["image_id"] for d in dets}), val_images=len(ann["images"]),
               val_annotations=len(ann["annotations"]))
    if tower == "T1":
        run = path.parent.name
        rec = [t for t in frozen["towers"] if t["fold"] == fold]
        row.update(run=run, images_in_file=len(data["images"]),
                   run_matches_frozen=bool(rec) and rec[0]["run"] == run
                   and Path(rec[0]["checkpoint"]).parent == path.parent,
                   image_map_equals_val_annotation={i["id"]: i["file_name"] for i in data["images"]}
                   == {i["id"]: i["file_name"] for i in ann["images"]})
    else:
        ids = {i["id"] for i in ann["images"]}
        row["image_ids_within_val_annotation"] = all(d["image_id"] in ids for d in dets)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    scratch = Path(a.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    out = {"task_id": C.TASK_ID}
    out["branch"] = sh("git branch --show-current")
    out["head"] = sh("git rev-parse --short=8 HEAD")
    out["origin_phase0"] = sh("git rev-parse --short=8 origin/phase0")
    out["merge_base"] = sh("git merge-base HEAD origin/phase0 | cut -c1-8")
    out["branch_starts_with_feat"] = out["branch"].startswith("feat/")
    out["untracked"] = sh("git status --porcelain --untracked-files=all").splitlines()
    out["created_from_measured"] = {
        "runindex_commit": sh("git log -1 --format=%h -- runindex/"),
        "counts": {n: sum(1 for _ in csv.DictReader(open(C.ROOT / f"runindex/{n}.csv")))
                   for n in ("index", "experiments", "verdicts")},
        "conventions_rev": sh("git log -1 --format=%h -- context/conventions.md")}
    out["prereq"] = {p: (C.ROOT / p).exists() for p in PREREQ}
    out["prereq_store"] = {str(C.T2_PREDS): C.T2_PREDS.exists(), str(C.RERUN_RUNS): C.RERUN_RUNS.is_dir()}
    out["venvs"] = [pycocotools_in(str(C.ROOT / ".venv")), pycocotools_in(str(C.ROOT / ".venv-relation-detr")),
                    pycocotools_in("/nonexistent/zzz_no_such_venv")]
    out["venv_used"] = sys.prefix
    frozen = C.read_json(C.FROZEN, "凍結した塔の記録（run の名前・val の値）", "record")
    out["inventory"] = [inventory(t, f, frozen) for t, f in C.TARGETS]
    # 対照 b: 1 バイト変えた写しで hash の照合が食い違う／存在しない run の名前で 0 件
    src = C.pred_path("T1", "A")
    copy = scratch / "control_T1A_flipped.json.gz"
    shutil.copyfile(src, copy)
    with open(copy, "r+b") as handle:
        handle.seek(-100, 2)
        b = handle.read(1)
        handle.seek(-100, 2)
        handle.write(bytes([b[0] ^ 0xFF]))
    ghost = "dtowerrerun_p12_dcoco_foldZ_seed42"
    out["controls"] = {
        "flipped_copy_sha_matches_original": C.sha256(copy) == out["inventory"][0]["sha256"],
        "real_sha_matches_original": C.sha256(src) == out["inventory"][0]["sha256"],
        "ghost_run_in_frozen": sum(t["run"] == ghost for t in frozen["towers"]),
        "ghost_run_dirs": len(list(C.RERUN_RUNS.glob(ghost))),
        "real_run_dirs": len(list(C.RERUN_RUNS.glob(C.t1_run("A"))))}
    copy.unlink()
    C.write_json(C.OUT / "start/a_start.json", out)
    print(json.dumps({k: out[k] for k in ("branch", "merge_base", "created_from_measured", "venvs", "controls")},
                     ensure_ascii=False))
    for r in out["inventory"]:
        print(json.dumps({k: r.get(k) for k in ("tower", "fold", "exists", "predictions", "images_with_predictions",
                                                 "val_images", "run_matches_frozen", "image_map_equals_val_annotation",
                                                 "image_ids_within_val_annotation", "sha256")}))
    print("prereq missing:", [p for p, ok in out["prereq"].items() if not ok])


if __name__ == "__main__":
    main()

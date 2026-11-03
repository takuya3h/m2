"""Task A-4: 入力の要約値を取り、andrew の記録と比べる（読むだけ。結果は標準出力の JSON）。

記録は二つ。どちらも andrew（または dlsta 探索の固定記録）の値だけを使い、相手のホストの列は読まない。
- ``experiments/analysis/tower_reselect_search_dlsta/image_input_lock.json``: 17,233 行の画像の sha256
- ``experiments/analysis/bengio_andrew_env_survey/d/data_compare.json`` の ``files[*].andrew``
  （manifest・折り A の train/val の術具注釈・分割・重み）

test の術具注釈と test の manifest は要約値も取らない（本契約は test を読まない）。

    .venv/bin/python tasks/T-2026-11-02-hostdiff-andrew/tools/check_inputs.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCK = ROOT / "experiments/analysis/tower_reselect_search_dlsta/image_input_lock.json"
SURVEY = ROOT / "experiments/analysis/bengio_andrew_env_survey/d/data_compare.json"
INVENTORY = ROOT / "experiments/analysis/tower_reselect_search_dlsta/inputs_inventory.json"
FILES = [
    "data/processed/phase_manifest_all_phase/train.json",
    "data/processed/phase_manifest_all_phase/val.json",
    "data/processed/phase_manifest_all_phase/phase_vocab.json",
    "data/annotations/egosurgery_tool_folds/A/instances_train.json",
    "data/annotations/egosurgery_tool_folds/A/instances_val.json",
    "data/splits/ego_train.txt",
    "data/splits/ego_val.txt",
    "data/splits/ego_test.txt",
    "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth",
]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def compare(measured, recorded):
    return {"measured": measured, "recorded": recorded, "match": measured == recorded}


def lock_check(rows):
    checked, bad, size = 0, [], 0
    for row in rows:
        for role in ("selected", "counterpart"):
            rel = row.get(role)
            if not rel:
                continue
            path = ROOT / rel
            checked += 1
            if not path.is_file():
                bad.append({"frame": row["frame"], "role": role, "reason": "missing"})
                continue
            size += path.stat().st_size
            if sha256(path) != row["sha256"][role]:
                bad.append({"frame": row["frame"], "role": role, "reason": "sha256"})
    return {"rows": len(rows), "checked": checked, "mismatch_or_missing": len(bad),
            "bytes": size, "examples": bad[:10]}


def main():
    rows = json.loads(LOCK.read_text())
    survey = {f["path"].replace("~/slocal2/m2/", ""): f["andrew"] for f in json.loads(SURVEY.read_text())["files"]}
    files = {}
    for rel in FILES:
        rec = survey[rel]
        files[rel] = {"bytes": compare((ROOT / rel).stat().st_size, rec["bytes"]),
                      "sha256": compare(sha256(ROOT / rel), rec["sha256"])}
    inventory = json.loads(INVENTORY.read_text())
    b5b = next(r for r in inventory["items"] if r["item"].startswith("B5b"))
    sys.path.insert(0, str(ROOT / "scripts"))
    import stage1_ptower_r3 as r3  # CPU で COCO の重みの backbone を組み、要約値を取る
    _, source, digest = r3.build_backbone(11, "cpu", "coco")
    lock = lock_check(rows)
    # 空振りでないことの確認: 記録の要約値を一文字変えると不一致になる
    first = FILES[0]
    flipped = files[first]["sha256"]["recorded"]
    flipped = ("0" if flipped[0] != "0" else "1") + flipped[1:]
    result = {
        "image_input_lock": lock,
        "files": files,
        "coco_backbone_digest": compare(digest, b5b["expected"]) | {"source": source},
        "breaking_control_flip_one_char": {
            "path": first, "recorded_flipped": flipped,
            "match": files[first]["sha256"]["measured"] == flipped},
    }
    result["all_match"] = (lock["mismatch_or_missing"] == 0 and lock["rows"] == 17233 and
                           all(v["bytes"]["match"] and v["sha256"]["match"] for v in files.values()) and
                           result["coco_backbone_digest"]["match"])
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""Phase C: 過去の run の記録が条件を正しく表しているかを測る。

走査は象徴的な繋がりを辿る（`os.walk(followlinks=True)`）。索引の経路には
絞らない。索引が指さない場所に成果物があった前例があるためである。

出力: audit/impact.json
"""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]

# Phase B で実挙動により「読まれない」と確かめた鍵と、実挙動を決めている鍵。
# effective=None は「実挙動を決める設定が無い（実装が固定している）」の意。
AUDITED = {
    "frozen_source.detector": {"effective_from": None, "note": "実挙動は data.feature_cache のパスが決める"},
    "frozen_source.checkpoint": {"effective_from": None, "note": "学習時には読まれない（特徴抽出時のみ）"},
    "frozen_source.seed": {"effective_from": None, "note": "harvester も信用しないと明記"},
    "frozen_source.cache_dir": {"effective_from": "data.feature_cache", "note": "索引の frozen_source_tag の元"},
    "eval_recipe.protocol_source": {"effective_from": None, "note": "実挙動は定数 PHASE_EVAL_PROTOCOL"},
    "eval_recipe.inference_protocol": {"effective_from": None, "note": "同上"},
    "eval_recipe.jaccard_mode": {"effective_from": None, "note": "同上"},
    "model.component": {"effective_from": None, "note": "入口が build_grasp_phase_injection を直接呼ぶ"},
    "train.batch_size": {"effective_from": None, "note": "clip 単位で固定"},
    "train.freeze_backbone": {"effective_from": None, "note": "特徴が事前計算のため常に凍結"},
    "data.population.test": {"effective_from": None, "note": "学習時に test は読まない"},
    "logging.wandb_enabled": {"effective_from": None, "note": "実挙動は環境変数 WANDB_API_KEY"},
    "logging.wandb_project": {"effective_from": None, "note": "同上（WANDB_PROJECT）"},
    "grasp_inference.detach_from_phase_loss": {"effective_from": None, "note": "実装が常に detach"},
    "grasp_inference.signal": {"effective_from": "ENTRYPOINT", "note": "元の入口では読まれない"},
}

# 実装が固定している実際の値（Phase B / 実装読解で確かめたもの）
HARDCODED = {
    "eval_recipe.inference_protocol": "online_causal",
    "eval_recipe.jaccard_mode": "strict",
    "grasp_inference.detach_from_phase_loss": True,
    "grasp_inference.signal__original_entrypoint": "predicted_sigmoid",
}


def dig(node, dotted: str):
    cur = node
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def walk_run_dirs() -> list[Path]:
    """experiments/ 配下を、リンクを辿って走査する。"""
    found: list[Path] = []
    seen: set[str] = set()
    for root, dirs, files in os.walk(PROJ / "experiments", followlinks=True):
        real = os.path.realpath(root)
        if real in seen:
            dirs[:] = []
            continue
        seen.add(real)
        if "config.yaml" in files:
            found.append(Path(root))
    return sorted(found)


def entrypoint_of(run: Path) -> str:
    cmd = run / "command.sh"
    if not cmd.exists():
        return "unknown"
    text = cmd.read_text(encoding="utf-8", errors="replace")
    if "train_grasp_phase_injection_variants.py" in text:
        return "variants"
    if "train_grasp_phase_injection.py" in text:
        return "original"
    return "other"


def main() -> None:
    import yaml

    runs = walk_run_dirs()
    occurrences = {k: 0 for k in AUDITED}
    mismatches = {k: [] for k in AUDITED}
    per_entry = {}
    scanned = 0
    unreadable = []

    for run in runs:
        try:
            cfg = yaml.safe_load((run / "config.yaml").read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            unreadable.append({"run": str(run.relative_to(PROJ)), "error": str(exc)})
            continue
        if not isinstance(cfg, dict):
            continue
        scanned += 1
        entry = entrypoint_of(run)
        per_entry[entry] = per_entry.get(entry, 0) + 1
        rel = str(run.relative_to(PROJ))

        for key in AUDITED:
            declared, present = dig(cfg, key)
            if not present:
                continue
            occurrences[key] += 1

            # --- 実挙動と突き合わせる ---
            if key == "grasp_inference.signal":
                effective = (
                    HARDCODED["grasp_inference.signal__original_entrypoint"]
                    if entry == "original"
                    else declared
                )
            elif key == "frozen_source.cache_dir":
                effective, ok = dig(cfg, "data.feature_cache")
                if not ok:
                    effective = None
            elif key in HARDCODED:
                effective = HARDCODED[key]
            else:
                effective = "<UNKNOWN: 実挙動を決める設定が無い>"

            if isinstance(effective, str) and effective.startswith("<UNKNOWN"):
                continue  # 突き合わせる相手が無いものは食い違いを数えない
            if effective is None:
                continue
            if str(declared).rstrip("/") != str(effective).rstrip("/"):
                mismatches[key].append(
                    {"run": rel, "entrypoint": entry, "declared": declared, "effective": effective}
                )

    # --- 索引の列に取り込まれているか ---
    index_csv = PROJ / "runindex" / "index.csv"
    index_cols = []
    n_index_rows = 0
    tag_nonnull = 0
    if index_csv.exists():
        with index_csv.open(encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            index_cols = list(reader.fieldnames or [])
            for row in reader:
                n_index_rows += 1
                if (row.get("frozen_source_tag") or "").strip():
                    tag_nonnull += 1

    payload = {
        "run_dirs_with_config": len(runs),
        "configs_parsed": scanned,
        "unreadable": unreadable,
        "runs_per_entrypoint": per_entry,
        "occurrences": occurrences,
        "mismatch_counts": {k: len(v) for k, v in mismatches.items()},
        "mismatches": mismatches,
        "index": {
            "columns": index_cols,
            "n_rows": n_index_rows,
            "frozen_source_tag_column_present": "frozen_source_tag" in index_cols,
            "frozen_source_tag_nonnull_rows": tag_nonnull,
            "eval_recipe_id_column_present": "eval_recipe_id" in index_cols,
        },
        "audited_keys": AUDITED,
    }
    (AUDIT / "impact.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"run dirs with config.yaml : {len(runs)}  (parsed {scanned})")
    print(f"runs per entrypoint       : {per_entry}")
    print(f"index rows                : {n_index_rows}")
    print(f"frozen_source_tag non-null: {tag_nonnull}")
    print()
    print(f"{'key':45s} {'occurs':>7s} {'mismatch':>9s}")
    for key in AUDITED:
        print(f"{key:45s} {occurrences[key]:7d} {len(mismatches[key]):9d}")


if __name__ == "__main__":
    main()

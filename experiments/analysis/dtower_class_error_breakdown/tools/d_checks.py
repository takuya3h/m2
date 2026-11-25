"""Task D: 完了判定 i（test を読まない）と j（変えていない）の検査（非公式 T-2026-11-22-dtower-class-error-breakdown）。

    .venv/bin/python .../d_checks.py

- i: 読んだファイルの一覧（reads.jsonl）の検出の test のファイルが 0 件。工程のマニフェストの test.json を読んだ目的が
  Fold B〜E の (e) だけ。Fold ごとに、使った画像の動画と工程の正解を使った動画が、その Fold の test の動画と共通 0 件
  （分解・直し方・表の val の画像、(e) の train と val の動画）。対照: 一覧の写しに test のファイルの名前を一つ混ぜると 1 件、
  Fold A の val の画像の写しに動画 04 の画像を一つ混ぜると共通 1 件
- j: 一覧の各ファイルの今の sha256 が、一覧に最初に記録した sha256 と一致する

書くもの: d/d_checks.json。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_reads as R  # noqa: E402
import common as C  # noqa: E402


def main():
    C.log_reads = False  # 検査のための読み込みは一覧に足さない
    rows = [json.loads(x) for x in C.READS.read_text().splitlines() if x.strip()]
    F = C.folds()
    out = {"task_id": C.TASK_ID}
    first = {}
    for r in rows:
        first.setdefault(r["path"], r)
    out["reads"] = {"rows": len(rows), "files": len(first),
                    "by_kind": {k: sum(1 for r in first.values() if r.get("kind") == k)
                                for k in sorted({r.get("kind") for r in first.values()})},
                    "files_list": sorted(first)}
    out["i_test_files"] = R.test_entries(rows)
    mt = R.manifest_test_reads(rows)
    out["i_manifest_test_json_purposes"] = mt
    out["i_manifest_test_json_only_folds_B_to_E"] = all(any(f"Fold {f} " in p for f in "BCDE") for p in mt)
    out["i_control_injected"] = len(R.test_entries(rows + [{"path": str(C.ANN / "A/instances_test.json")}]))
    per_fold = {}
    for tower, fold in C.TARGETS:
        test = set(F[fold]["test"])
        val = C.read_json(C.ann_path(fold, "val"), "検査")
        vids = sorted({C.video_of(i["file_name"]) for i in val["images"]})
        fx = json.loads((C.OUT / f"c/fix_{tower}_{fold}.json").read_text())
        ph = fx["phase"]
        used = ph.get("videos_used", [])
        skipped = sorted(ph.get("videos_skipped_frames", {}))
        per_fold[f"{tower}_{fold}"] = {"val_videos": vids, "val_test_overlap": sorted(set(vids) & test),
                                       "phase_videos_used": used, "phase_used_test_overlap": sorted(set(used) & test),
                                       "phase_videos_skipped": skipped, "skipped_are_test": set(skipped) <= test}
    out["i_per_fold"] = per_fold
    val_a = C.read_json(C.ann_path("A", "val"), "検査")
    mixed = {C.video_of(i["file_name"]) for i in val_a["images"]} | {"04"}
    out["i_control_mixed_video_overlap"] = sorted(mixed & set(F["A"]["test"]))
    out["i_pass"] = (not out["i_test_files"] and out["i_manifest_test_json_only_folds_B_to_E"]
                     and all(not v["val_test_overlap"] and not v["phase_used_test_overlap"] and v["skipped_are_test"]
                             for v in per_fold.values()))
    changed = [p for p, r in first.items() if C.sha256(p) != r["sha256"]]
    inconsistent = sorted({r["path"] for r in rows if r["sha256"] != first[r["path"]]["sha256"]})
    out["j_rehash_changed"] = changed
    out["j_inconsistent_within_log"] = inconsistent
    out["j_store_files"] = sorted(p for p in first if p.startswith(str(C.STORE)))
    out["j_pass"] = not changed and not inconsistent
    C.write_json(C.OUT / "d/d_checks.json", out)
    print(json.dumps({k: v for k, v in out.items() if k not in ("reads", "i_per_fold", "j_store_files")}, ensure_ascii=False))
    print("reads", json.dumps({k: v for k, v in out["reads"].items() if k != "files_list"}))
    for k, v in per_fold.items():
        print(k, json.dumps(v))


if __name__ == "__main__":
    main()

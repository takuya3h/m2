"""Task B: inventory of the inputs both towers need, for T-2026-10-19-dlsta-tower-feasibility.

Read-only. Each item carries presence, count, a digest (or size) and the expected value,
and a ``match`` flag. Expected values come from the repo's records, cited per item.

    python inputs_inventory.py --out inputs_inventory.json [--control]

``--control`` repeats two comparisons with a deliberately wrong expectation and a path
that does not exist, to show the comparison can fail.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

EGO = ROOT / "data/raw/ego"
OPEN = ROOT / "data/raw/OpenSurgery_Dataset/01_frames/initial_videos"
V15 = [f"{i:02d}" for i in range(1, 16)]
FSA = ROOT / "experiments/analysis/frame_signal_audit/summary_method_a.json"

# data/README.md "折りごとの術具注釈" (images / boxes)
FOLD_TABLE = {
    "A": {"train": (9657, 32272), "val": (1515, 4707), "test": (4265, 12673)},
    "B": {"train": (9764, 31119), "val": (1861, 4922), "test": (3812, 13611)},
    "C": {"train": (10834, 34769), "val": (1988, 7516), "test": (2615, 7367)},
    "D": {"train": (10262, 35078), "val": (2554, 5751), "test": (2621, 8823)},
    "E": {"train": (11182, 33724), "val": (2131, 8750), "test": (2124, 7178)},
}


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _digest(path):
    return str(path), sha256_file(path)


def item(name, present, count, expected, digest=None, note=""):
    return {"item": name, "present": present, "count": count, "expected": expected,
            "match": present and count == expected, "digest": digest, "note": note}


def images(workers):
    """Frames of videos 01-15 under data/raw/ego, digested like frame_signal_audit."""
    paths = sorted(p for p in EGO.rglob("*.jpg") if p.name[:2] in V15
                   and "other" not in p.parts[-3])
    with Pool(workers) as pool:
        digests = pool.map(_digest, paths, chunksize=64)
    per_video, total = defaultdict(hashlib.sha256), hashlib.sha256()
    for p, d in sorted(digests):
        rel = str(Path(p).relative_to(ROOT))
        per_video[Path(p).name[:2]].update(f"{rel} {d}\n".encode())
        total.update(f"{rel} {d}\n".encode())
    counts = Counter(p.name[:2] for p in paths)
    recorded = json.loads(FSA.read_text())["decode"]["sha256_per_video"] if FSA.exists() else {}
    per = {v: {"count": counts.get(v, 0), "sha256": per_video[v].hexdigest() if v in per_video else None,
               "recorded_sha256": recorded.get(v),
               "sha256_match": recorded.get(v) == (per_video[v].hexdigest() if v in per_video else None)}
           for v in V15}
    return paths, per, total.hexdigest(), sum(p.stat().st_size for p in paths)


def phase_rows():
    rows = {}
    for f in sorted((ROOT / "data/annotations/egosurgery_phase").glob("*.csv")):
        with f.open() as handle:
            for r in csv.DictReader(handle):
                rows[r["Frame"]] = (f.stem, r["Phase"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--control", action="store_true")
    args = ap.parse_args()
    out = {"task_id": "T-2026-10-19-dlsta-tower-feasibility", "items": []}
    items = out["items"]

    # 1. images of the 15 videos
    paths, per_video, total_sha, total_bytes = images(args.workers)
    items.append(item("B1 画像 01-15（data/raw/ego）", bool(paths), len(paths), 15437,
                      total_sha, f"bytes={total_bytes}。要約値は frame_signal_audit と同じ取り方（動画ごとに記録と照合）"))
    out["images_per_video"] = per_video
    host = {p.stem for p in paths}

    # 2. phase-only frames
    rows = phase_rows()
    p15 = {k for k in rows if k[:2] in V15}
    only = sorted(p15 - host)
    found = [OPEN / f"{k.rsplit('_', 1)[0]}" / f"{k}.jpg" for k in only]
    exists = [p for p in found if p.exists()]
    digest = hashlib.sha256()
    for p in exists:
        digest.update(f"{p.relative_to(ROOT)} {sha256_file(p)}\n".encode())
    items.append(item("B2 工程注釈だけのフレーム（initial_videos）", len(exists) == len(only), len(exists), 1796,
                      digest.hexdigest(), f"工程 CSV 01-15 の行 {len(p15)} − 画像 {len(host)} = {len(only)}。"
                      f"bytes={sum(p.stat().st_size for p in exists)}"))

    # 3. annotations and manifest
    items.append(item("B3a 工程 CSV 01-15 の行", bool(rows), len(p15), 17233,
                      None, f"CSV ファイル {len(list((ROOT / 'data/annotations/egosurgery_phase').glob('*.csv')))} 件"))
    man_dir = ROOT / "data/processed/phase_manifest"
    frames, missing, shas = 0, 0, {}
    for split in ("train", "val", "test"):
        f = man_dir / f"{split}.json"
        shas[split] = sha256_file(f) if f.exists() else None
        if f.exists():
            for c in json.loads(f.read_text())["clips"]:
                for fr in c["frames"]:
                    frames += 1
                    missing += not (ROOT / fr["image_path"]).exists()
    shas["phase_vocab"] = sha256_file(man_dir / "phase_vocab.json") if (man_dir / "phase_vocab.json").exists() else None
    items.append(item("B3b 工程塔の manifest（data/processed/phase_manifest）", all(shas.values()) and missing == 0,
                      frames, 15437, shas, f"image_path の欠け {missing}"))
    tool = ROOT / "data/annotations/egosurgery_tool"
    for split in ("train", "val", "test"):
        f = tool / f"instances_{split}.json"
        if f.exists():
            d = json.loads(f.read_text())
            n = (len(d["images"]), len(d["annotations"]))
            miss = sum(not (EGO / im["file_name"]).exists() for im in d["images"])
        else:
            n, miss = (0, 0), None
        items.append(item(f"B3c 術具注釈 公式 {split}", f.exists() and miss == 0, list(n),
                          list(FOLD_TABLE["A"][split]), sha256_file(f) if f.exists() else None,
                          f"file_name の画像の欠け {miss}"))

    # 4. fold annotations
    for fold, splits in FOLD_TABLE.items():
        for split, expected in splits.items():
            f = ROOT / f"data/annotations/egosurgery_tool_folds/{fold}/instances_{split}.json"
            if f.exists():
                d = json.loads(f.read_text())
                n = [len(d["images"]), len(d["annotations"])]
                miss = sum(not (EGO / im["file_name"]).exists() for im in d["images"])
            else:
                n, miss = [0, 0], None
            items.append(item(f"B4 折り {fold} {split}", f.exists() and miss == 0, n, list(expected),
                              sha256_file(f) if f.exists() else None, f"file_name の画像の欠け {miss}"))

    # 5. COCO init weights
    w = ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"
    size = w.stat().st_size if w.exists() else 0
    items.append(item("B5a COCO の初期化の重み（大きさ bytes）", w.exists(), size, 196140106,
                      sha256_file(w) if w.exists() else None, "docs/experiment_settings.md 193 行"))
    if w.exists():
        import stage1_ptower_r3 as r3
        _, _, digest = r3.build_backbone(13, "cpu", "coco")
        rec = None
        cfg = ROOT / "experiments/phase1/stage1_ptower_r3_005_ft_coco_lr0.0001_foldA_seed42/config.yaml"
        for line in cfg.read_text().splitlines():
            if line.startswith("backbone_init_sha256:"):
                rec = line.split(":", 1)[1].strip()
        items.append(item("B5b COCO の重みの backbone の要約値（stage1_ptower_r3.backbone_digest）", True,
                          digest, rec, None, f"記録は {cfg.relative_to(ROOT)}"))

    # 6. checkpoints for Task F
    ledger = ROOT / "experiments/baselines/stage1_dtower_r2/test_access_ledger.csv"
    led = {}
    if ledger.exists():
        for r in csv.DictReader(ledger.open()):
            if r["tower"] == "coco" and r["seed"] == "42":
                led[r["fold"]] = r["checkpoint_sha256"]
    for fold in ("A", "B"):
        ck = ROOT / f"experiments/baselines/stage1_dtower_r2/dcoco_fold{fold}_seed42/work/best_ap.pth"
        sha = sha256_file(ck) if ck.exists() else None
        items.append(item(f"B6a 検出塔二周目 D*-COCO 折り {fold} seed 42 best_ap.pth", ck.exists(), sha, led.get(fold),
                          None, f"bytes={ck.stat().st_size if ck.exists() else 0}。記録は test_access_ledger.csv の checkpoint_sha256"))
    for run in ("005_ft_coco_lr0.0001_foldA_seed42", "008_ft_coco_lr0.0001_foldB_seed42"):
        d = ROOT / f"experiments/phase1/stage1_ptower_r3_{run}"
        ck = d / "checkpoints/best.pth"
        rec = json.loads((d / "finetune_history.json").read_text())["checkpoint_sha256"]
        sha = sha256_file(ck) if ck.exists() else None
        items.append(item(f"B6b 工程塔三周目 {run} best.pth", ck.exists(), sha, rec, None,
                          f"bytes={ck.stat().st_size if ck.exists() else 0}。記録は finetune_history.json"))

    if args.control:
        out["controls"] = {
            "expected_changed_15438": item("対照: 画像の期待を 15438 に変える", True, len(paths), 15438)["match"],
            "missing_path_count": len(list((ROOT / "data/raw/ego_does_not_exist").rglob("*.jpg"))),
        }
    out["all_match"] = all(i["match"] for i in items)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    for i in items:
        print(f"{'OK ' if i['match'] else 'NG '} {i['item']}: count={i['count']} expected={i['expected']} {i['note']}")
    print("controls", out.get("controls"))
    print("all_match", out["all_match"])


if __name__ == "__main__":
    main()

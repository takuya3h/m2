#!/usr/bin/env python
"""P*-20 の工程 manifest: 15 動画の manifest に追加動画 17〜21 を train として足す。

15 動画の manifest（``data/processed/phase_manifest/``）は変えずに写し、追加動画の
clip を ``train.json`` にだけ加える。動画 22 は工程注釈があるがフレーム画像が無いので
使わない。追加動画は**注釈のフレーム集合と画像のフレーム集合が一致すること**を要求し、
一致しなければ止まる（15 動画の builder のように交差を取って黙って落とさない）。

出力（``data/processed/stage1_features/p20_manifest/``）:
  - ``{train,val,test}.json`` と ``phase_vocab.json``（15 動画と同じ形式）
  - ``audit.json``: clip ごとの注釈数・画像数、折りごとの集合差の照合

実行（本体 .venv）:
  .venv/bin/python scripts/build_phase_manifest_p20.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "scripts"))

from build_phase_manifest import PHASE_CSV_DIR, _read_clip_csv  # noqa: E402

SOURCE_DIR = PROJ / "data" / "processed" / "phase_manifest"
OUT_DIR = PROJ / "data" / "processed" / "stage1_features" / "p20_manifest"
EXTRA_ROOT = PROJ / "data" / "raw" / "ego" / "other(17~21)"
EXTRA_TRAIN = ("17", "18", "19", "20", "21")
EXCLUDED = ("22",)


def extra_clips(vocab):
    """追加動画の clip。注釈と画像のフレーム集合が一致しなければ止まる。"""
    clips, audit = [], {}
    for video in EXTRA_TRAIN:
        for csv_path in sorted(PHASE_CSV_DIR.glob(f"{video}_*.csv")):
            clip_id = csv_path.stem
            rows = _read_clip_csv(csv_path)
            images = {p.stem for p in (EXTRA_ROOT / video).glob(f"{clip_id}_*.jpg")
                      if p.stat().st_size > 0}
            annotated = [frame for frame, _ in rows]
            audit[clip_id] = {"annotated": len(annotated), "images": len(images)}
            if set(annotated) != images or len(annotated) != len(set(annotated)):
                raise RuntimeError(f"Frames and annotation differ for {clip_id}: {audit[clip_id]}")
            unknown = {phase for _, phase in rows} - set(vocab)
            if unknown:
                raise RuntimeError(f"Phase outside the vocabulary in {clip_id}: {unknown}")
            clips.append({"clip_id": clip_id, "video": video, "frames": [
                {"frame": frame,
                 "image_path": str((EXTRA_ROOT / video / f"{frame}.jpg").relative_to(PROJ)),
                 "phase": phase, "label": vocab[phase]}
                for frame, phase in rows]})
        if not any(c["video"] == video for c in clips):
            raise RuntimeError(f"No clips for extra video {video}")
    return clips, audit


def verify_folds(p15, p20):
    """各折りで追加分だけが train に増え、val・test は変わらないこと（集合差の照合）。"""
    report = {}
    for fold, split in p20.items():
        base = p15[fold]
        added = set(split["train"]) - set(base["train"])
        problems = []
        if added != set(EXTRA_TRAIN) or not set(base["train"]) <= set(split["train"]):
            problems.append(f"train gained {sorted(added)}")
        for part in ("val", "test"):
            if set(split[part]) != set(base[part]):
                problems.append(f"{part} changed")
        held_out = set(split["val"]) | set(split["test"])
        if held_out & set(EXTRA_TRAIN):
            problems.append(f"extra in val/test: {sorted(held_out & set(EXTRA_TRAIN))}")
        if set(EXCLUDED) & (set(split["train"]) | held_out):
            problems.append("excluded video present")
        if problems:
            raise RuntimeError(f"Fold {fold}: {'; '.join(problems)}")
        report[fold] = {"train_added": sorted(added), "train": len(split["train"]),
                        "val": sorted(split["val"]), "test": sorted(split["test"])}
    return report


def build():
    import stage1_ptower as base
    import stage1_ptower_20 as p20

    vocab = json.loads((SOURCE_DIR / "phase_vocab.json").read_text())
    clips, audit = extra_clips(vocab)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "phase_vocab.json").write_text((SOURCE_DIR / "phase_vocab.json").read_text())
    for split in ("train", "val", "test"):
        manifest = json.loads((SOURCE_DIR / f"{split}.json").read_text())
        if split == "train":
            manifest["clips"] = manifest["clips"] + clips
            manifest["num_clips"] = len(manifest["clips"])
            manifest["num_frames"] = sum(len(c["frames"]) for c in manifest["clips"])
        (OUT_DIR / f"{split}.json").write_text(json.dumps(manifest, ensure_ascii=False))
    folds = verify_folds(base.folds(), p20.folds_p20())
    report = {"extra_train": list(EXTRA_TRAIN), "excluded": list(EXCLUDED), "clips": audit,
              "extra_frames": sum(len(c["frames"]) for c in clips), "folds": folds}
    base.write_json(OUT_DIR / "audit.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"written -> {OUT_DIR}")


if __name__ == "__main__":
    build()

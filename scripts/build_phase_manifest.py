#!/usr/bin/env python
"""Phase frame manifest ビルダー（STEP A / S4 の前提）。

EgoSurgery-Phase の per-video CSV（``data/annotations/egosurgery_phase/<vid>_<clip>.csv``,
列 = Frame,Phase）を読み、各 split（公式 video 割当 = PAPER_SPLIT_VIDEOS）について
**動画クリップ単位・時系列順のフレーム列**を作る。実画像が存在するフレームのみ残す
（CSV のフレーム数 > 実画像数のことがあるため交差を取る）。

出力（``data/processed/phase_manifest/``）:
  - ``{split}.json``: {"split", "clips": [{"clip_id","video","frames":[
        {"frame","image_path","phase","label"}...]}...]}
  - ``phase_vocab.json``: {"phase_name": label_idx, ...}（全 split 横断・sorted で安定）

TeCNO（S4）はこの clip 単位の時系列を入力にする。online/causal なので clip 内の順序が重要。

実行（本体 .venv）:
  .venv/bin/python scripts/build_phase_manifest.py
"""
from __future__ import annotations

import csv
import json
from collections import OrderedDict
from pathlib import Path

from egosurgery.utils.eval_recipe import PAPER_SPLIT_VIDEOS

PROJ = Path(__file__).resolve().parents[1]
PHASE_CSV_DIR = PROJ / "data" / "annotations" / "egosurgery_phase"
EGO_ROOT = PROJ / "data" / "raw" / "ego"
OUT_DIR = PROJ / "data" / "processed" / "phase_manifest"


def _read_clip_csv(csv_path: Path) -> list[tuple[str, str]]:
    """CSV を (frame, phase) の時系列順リストで返す。"""
    rows: list[tuple[str, str]] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            frame = (r.get("Frame") or "").strip()
            phase = (r.get("Phase") or "").strip()
            if frame and phase:
                rows.append((frame, phase))
    return rows


def build() -> None:
    # video -> split 逆引き
    video_to_split = {}
    for split, videos in PAPER_SPLIT_VIDEOS.items():
        for v in videos:
            video_to_split[v] = split

    # まず全 phase を集めて安定 vocab を作る（全 split 横断・sorted）
    all_phases: set[str] = set()
    clip_rows: dict[str, list[tuple[str, str]]] = {}
    for csv_path in sorted(PHASE_CSV_DIR.glob("*.csv")):
        clip_id = csv_path.stem               # 例: "01_1"
        rows = _read_clip_csv(csv_path)
        clip_rows[clip_id] = rows
        all_phases.update(p for _, p in rows)
    vocab = OrderedDict((p, i) for i, p in enumerate(sorted(all_phases)))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "phase_vocab.json").write_text(
        json.dumps(vocab, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary: dict[str, dict] = {}
    for split in ("train", "val", "test"):
        clips_out = []
        n_frames = n_missing = n_zero = 0
        for clip_id, rows in clip_rows.items():
            video = clip_id.split("_")[0]
            if video_to_split.get(video) != split:
                continue
            frames = []
            for frame, phase in rows:                 # 時系列順を維持
                img = EGO_ROOT / split / video / f"{frame}.jpg"
                if img.exists() and img.stat().st_size > 0:
                    frames.append({
                        "frame": frame,
                        "image_path": str(img.relative_to(PROJ)),
                        "phase": phase,
                        "label": vocab[phase],
                    })
                elif img.exists():        # 0バイト = 破損/空（実体未転送）。除外して計上する
                    n_zero += 1
                else:
                    n_missing += 1
            if frames:
                clips_out.append({"clip_id": clip_id, "video": video, "frames": frames})
                n_frames += len(frames)
        manifest = {"split": split, "num_clips": len(clips_out),
                    "num_frames": n_frames, "clips": clips_out}
        (OUT_DIR / f"{split}.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
        )
        summary[split] = {"clips": len(clips_out), "frames": n_frames,
                          "missing_no_image": n_missing, "zero_byte": n_zero}

    print("phase vocab (%d classes): %s" % (len(vocab), list(vocab.keys())))
    for split, s in summary.items():
        print(f"[{split}] clips={s['clips']}  frames={s['frames']}  "
              f"missing(no image)={s['missing_no_image']}  zero_byte(空/破損)={s['zero_byte']}")
    print(f"written -> {OUT_DIR}")


if __name__ == "__main__":
    build()

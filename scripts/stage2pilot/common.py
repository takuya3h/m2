"""Stage 2 予備測定の共通部品（非公式 T-2026-10-18-stage2-pilot-folda）。

本体の .venv（egosurgery を持つ）で使う。検出器側（.venv-relation-detr）からは
標準ライブラリと numpy だけの部分（経路、折り、test の検査、信号の入出力）を使う。

- 確定塔: 工程塔は efros で学んだ P*-15-COCO 折り A seed 42 の写し、検出塔は D*-COCO 折り A seed 42
- 大きな生成物は版管理と同期の外（STORE）に置く。syncthing は experiments/ の版管理外を全台へ配るため
- test の動画（04, 05, 07）は信号の作成・学習・評価に通さない。通した動画の集合を記録して検査する
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TASK_ID = "T-2026-10-18-stage2-pilot-folda"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK_ID
ANALYSIS = ROOT / "experiments/analysis/stage2_pilot_folda"

# 写した工程塔（Task B-1）。経路は efros の repo と同じ相対経路を STORE/efros_ptower の下に保つ
EFROS = STORE / "efros_ptower"
PT_FT_RUN = EFROS / "experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42"
PT_FEAT_RUN = EFROS / "experiments/phase1/stage1_ptower_20_008_features_coco_lr0.0001_foldA_seed42"
PT_HEAD_RUN = EFROS / "experiments/phase1/stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42"
PT_CACHE = EFROS / "data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz"
PT_HEAD_CKPT = PT_HEAD_RUN / "checkpoints/best.pth"
PT_FT_CKPT = PT_FT_RUN / "checkpoints/best.pth"
PT_RECORD = {"phase_jaccard": 0.7762185528074379, "phase_accuracy": 0.8712871287128713}
PT_ARCH = {"num_stages": 2, "num_layers": 8, "num_f_maps": 64, "in_dim": 2048, "num_classes": 9}

DET_RUN = ROOT / "experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42"
DET_CKPT = DET_RUN / "work/best_ap.pth"
DET_SHA256 = "30d199b15201cf3c03954852d8acc6fb58fe5349baef2fd200e877237ff682c4"
DET_RECORD = {"AP": 0.7273450248398429}
DET_ANN_A = ROOT / "data/annotations/egosurgery_tool_folds/A"

MANIFEST_DIR = ROOT / "data/processed/phase_manifest"
TEST_VIDEOS = frozenset({"04", "05", "07"})


def sha256(path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def fold_a() -> dict[str, list[str]]:
    """折り A を正本 docs/stage0/A1_fold_table.md から読む（stage1_ptower.folds と同じ読み方）。"""
    text = (ROOT / "docs/stage0/A1_fold_table.md").read_text()
    for line in text.splitlines():
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) == 4 and cells[0] == "A":
            split = {k: re.findall(r"\b\d{2}\b", c) for k, c in zip(("test", "val", "train"), cells[1:])}
            for part in ("train", "val", "test"):
                official = (ROOT / f"data/splits/ego_{part}.txt").read_text().split()
                assert set(split[part]) == set(official), part
            assert set(split["test"]) == TEST_VIDEOS
            return split
    raise RuntimeError("折り A が A1_fold_table.md に無い")


def video_of(frame: str) -> str:
    """フレーム名 '09_1_0213' の先頭が動画番号。"""
    return str(frame).split("_")[0]


def assert_no_test(names, stage: str) -> list[str]:
    """フレーム名か動画番号の集まりから動画の集合を作り、test との共通が 0 件であることを確かめる。

    共通が 1 件でもあれば止まる。戻り値は通した動画の集合（記録用、昇順）。
    """
    videos = sorted({video_of(n) for n in names})
    common = sorted(set(videos) & TEST_VIDEOS)
    if common:
        raise RuntimeError(f"[{stage}] test の動画が混入: {common}")
    return videos


def phase_names() -> list[str]:
    vocab = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
    return [k for k, _ in sorted(vocab.items(), key=lambda kv: kv[1])]


def phase_sequences(videos) -> list[tuple[str, list[str], np.ndarray]]:
    """動画ごとの列（フレーム名、工程の正解）。工程塔の学習（stage1_ptower.load_fold）と同じ並び。

    clip の番号順に連結し、clip の中はマニフェストの順。test のマニフェストは開かない。
    """
    videos = list(videos)
    assert_no_test(videos, "phase_sequences")
    clips = []
    for part in ("train", "val"):
        clips.extend(json.loads((MANIFEST_DIR / f"{part}.json").read_text())["clips"])
    out = []
    for video in videos:
        selected = sorted((c for c in clips if c["video"] == video), key=lambda c: int(c["clip_id"].split("_")[1]))
        if not selected:
            raise ValueError(f"動画 {video} がマニフェストに無い")
        frames = [f["frame"] for c in selected for f in c["frames"]]
        labels = np.array([f["label"] for c in selected for f in c["frames"]], dtype=np.int64)
        out.append((video, frames, labels))
    return out


def load_features(cache=PT_CACHE) -> dict[str, np.ndarray]:
    """特徴キャッシュをフレーム名で引ける形にする。test のフレームの特徴は読み出さない。"""
    with np.load(cache) as d:
        ids = [str(x) for x in d["frame_ids"]]
        keep = [i for i, f in enumerate(ids) if video_of(f) not in TEST_VIDEOS]
        feats = d["features"][keep]
    return {ids[i]: feats[j] for j, i in enumerate(keep)}


def load_ptower_head(ckpt=PT_HEAD_CKPT, device="cuda"):
    """工程塔の時間ヘッド（TeCNO、candidate C、8 層）を読む。"""
    import torch

    from egosurgery.models.heads.tecno_head import TeCNO
    model = TeCNO(**PT_ARCH)
    state = torch.load(ckpt, map_location="cpu")
    model.load_state_dict(state["model"])
    return model.to(device).eval()


def save_signal(path, frame_ids, x, **extra) -> str:
    """フレーム名で引ける信号を npz で保存し、sha256 を返す。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, frame_ids=np.asarray(frame_ids), x=np.asarray(x), **extra)
    return sha256(path)


def load_signal(path) -> dict[str, np.ndarray]:
    """フレーム名 → 行。npz の d["x"] は参照のたびに全体を読み直すので、一度だけ読む。"""
    with np.load(path) as d:
        x, ids = d["x"], d["frame_ids"]
    return {str(f): x[i] for i, f in enumerate(ids)}

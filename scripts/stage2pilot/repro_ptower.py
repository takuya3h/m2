"""Task B-3: 工程塔単独の val を andrew で再現する（非公式 T-2026-10-18-stage2-pilot-folda）。

写した特徴（STORE/efros_ptower）と写した時間ヘッドで、折り A の val（09, 10）の macro Jaccard と
frame accuracy を出す。評価は stage1_ptower.evaluate と同じ（動画ごとに列を流し、最終段の argmax、
PhaseEvaluator に動画ごとに入れて合算）。対照として別の重み（--head に別の run）でも出せる。

    .venv/bin/python scripts/stage2pilot/repro_ptower.py [--head <best.pth>] [--out <json>]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from stage2pilot import common as C  # noqa: E402


@torch.no_grad()
def predict(head, features, sequences, device="cuda"):
    """動画ごとの最終段の softmax（T, 9）。列は sequences の並び（online causal）。"""
    out = {}
    for video, frames, _ in sequences:
        x = np.stack([features[f] for f in frames])
        logits = head(torch.from_numpy(x).T[None].to(device))[-1][0]       # (9, T)
        out[video] = torch.softmax(logits, dim=0).T.cpu().numpy()
    return out


def phase_metrics(probs, sequences, names):
    evaluator = PhaseEvaluator(num_classes=len(names), class_names=names)
    for video, _, labels in sequences:
        evaluator.update(probs[video].argmax(1), labels, video_id=video)
    return evaluator.compute()


def per_video(probs, sequences, names):
    return {video: {k: phase_metrics(probs, [s], names)[k] for k in ("phase_jaccard", "phase_accuracy")}
            for video, s in ((s[0], s) for s in sequences)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--head", default=str(C.PT_HEAD_CKPT))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    import stage1_ptower as base
    base.deterministic(42)
    names = C.phase_names()
    split = C.fold_a()
    seqs = C.phase_sequences(split["val"])
    feats = C.load_features()
    head = C.load_ptower_head(a.head)
    probs = predict(head, feats, seqs)
    m = phase_metrics(probs, seqs, names)
    res = {"head": a.head, "head_sha256": C.sha256(a.head), "cache_sha256": C.sha256(C.PT_CACHE),
           "videos": C.assert_no_test(split["val"], "repro_ptower"),
           "frames": int(sum(len(s[1]) for s in seqs)),
           "phase_jaccard": m["phase_jaccard"], "phase_accuracy": m["phase_accuracy"],
           "record": C.PT_RECORD,
           "diff_jaccard": m["phase_jaccard"] - C.PT_RECORD["phase_jaccard"],
           "diff_accuracy": m["phase_accuracy"] - C.PT_RECORD["phase_accuracy"],
           "per_video": per_video(probs, seqs, names)}
    print(res)
    if a.out:
        C.write_json(a.out, res)


if __name__ == "__main__":
    main()

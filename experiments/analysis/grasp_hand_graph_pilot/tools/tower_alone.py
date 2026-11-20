"""工程塔単独（界面なし、学習なし）の val の値を本契約の識別子で 1 回だけ測り、記録の値と比べる（非公式 T-2026-11-20-grasp-hand-graph-pilot、SPEC §5）。

    .venv/bin/python experiments/analysis/grasp_hand_graph_pilot/tools/tower_alone.py --out <S>/grasp_hand_graph/e/tower_alone.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from stage2pilot import common as C  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import stage1_ptower as base
    base.deterministic(42)
    names = C.phase_names()
    seqs = C.phase_sequences(C.fold_a()["val"])
    C.assert_no_test([v for v, _, _ in seqs], "tower_alone")
    feats = C.load_features()
    head = C.load_ptower_head(device="cuda")
    ev = PhaseEvaluator(num_classes=len(names), class_names=names)
    probs = {}
    with torch.no_grad():
        for video, frames, y in seqs:
            x = torch.from_numpy(np.stack([feats[f] for f in frames])).cuda()
            out = head(x.T[None])[-1][0]
            ev.update(out.argmax(0).cpu().numpy(), y, video_id=video)
            probs[video] = torch.softmax(out, 0).T.cpu().numpy()
    r = ev.compute()
    present = [names[c] for c in sorted(set(np.concatenate([y for _, _, y in seqs]).tolist()))]
    res = {"task_id": "T-2026-11-20-grasp-hand-graph-pilot", "head": str(C.PT_HEAD_CKPT), "head_sha256": C.sha256(C.PT_HEAD_CKPT),
           "cache_sha256": C.sha256(C.PT_CACHE), "phase_jaccard": r["phase_jaccard"], "phase_accuracy": r["phase_accuracy"],
           "per_class_jaccard": r["phase_per_class_jaccard"],
           "six_phase_mean": float(np.mean([r["phase_per_class_jaccard"][n] for n in present if n != "dressing"])),
           "record": C.PT_RECORD, "equals_record": r["phase_jaccard"] == C.PT_RECORD["phase_jaccard"]
           and r["phase_accuracy"] == C.PT_RECORD["phase_accuracy"], "present_phases": present}
    C.write_json(a.out, res)
    np.savez(Path(a.out).with_name("tower_alone_val_probs.npz"), **probs)
    print(json.dumps({k: res[k] for k in ("phase_jaccard", "phase_accuracy", "six_phase_mean", "equals_record")}))


if __name__ == "__main__":
    main()

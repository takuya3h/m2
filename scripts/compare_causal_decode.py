#!/usr/bin/env python
"""因果 decode を 2 系統比較して「T1a の over-segmentation は online で解けるか」を頑健化。

boundary-gated sticky（学習した boundary 確信度で遷移を gate）だけでなく、**boundary head 非依存**の
min-segment-length **debounce**（新 phase が k フレーム連続したら遷移を確定 = k 未満の blip を除去、
未来不参照で完全因果）も試す。どちらでも「acc を保ったまま edit 改善」が出なければ、負の結論
（online では過分節を後処理で解けない）は decode 設計に依存しない頑健な知見になる。

実行: python scripts/compare_causal_decode.py
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

import numpy as np
import torch

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))
sys.path.insert(0, str(PROJ / "scripts"))

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from train_t1a_boundary import (  # noqa: E402
    CLASS_NAMES, GAP_DIM, REGION_DIM, TeCNOBoundary, load_clips, sticky_decode,
)

TR = PROJ / "experiments" / "transfer"
SEEDS = (42, 123, 456)


def debounce_decode(logits: np.ndarray, k: int) -> np.ndarray:
    """min-segment-length debounce（因果）。新 phase が k フレーム連続で初めて遷移を確定。

    time t は ≤t のみ参照（未来不使用）。k=1 は plain と同一。
    """
    C, T = logits.shape
    am = logits.argmax(0)
    preds = np.empty(T, dtype=np.int64)
    p = int(am[0]); cand = p; run = 0
    preds[0] = p
    for t in range(1, T):
        a = int(am[t])
        if a == p:
            cand, run = p, 0
        elif a == cand:
            run += 1
        else:
            cand, run = a, 1
        if run >= k:          # k 連続で確定
            p = cand; run = 0
        preds[t] = p
    return preds


def _base_mean(key: str) -> float:
    vals = []
    for s in SEEDS:
        ds = sorted(TR.glob(f"t1a_base_env_*seed{s}"))
        for d in reversed(ds):
            if (d / "metrics.json").exists():
                vals.append(json.load(open(d / "metrics.json"))[key]); break
    return st.mean(vals)


def main() -> None:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    val_clips = load_clips("val", region_only=False)
    base_acc = _base_mean("phase_accuracy")
    base_edit = _base_mean("phase_edit_score")

    cache = {}
    for s in SEEDS:
        d = sorted(TR.glob(f"t1a_boundary_*seed{s}"))[-1]
        ck = torch.load(d / "checkpoints" / "best_tecno_boundary.pth", map_location=device)
        model = TeCNOBoundary(2, 8, 64, GAP_DIM + REGION_DIM, len(CLASS_NAMES)).to(device)
        model.load_state_dict(ck["model"]); model.eval()
        clips = []
        with torch.no_grad():
            for cid, feats, labels in val_clips:
                x = torch.from_numpy(feats).T.unsqueeze(0).to(device)
                po, bl = model(x)
                clips.append((cid, po[-1][0].cpu().numpy(),
                              torch.sigmoid(bl[0, 0]).cpu().numpy(), labels))
        cache[s] = clips

    def evalfn(decode) -> tuple[float, float, float, float]:
        accs, f1s, edits, segs = [], [], [], []
        for s in SEEDS:
            ev = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
            for cid, lg, bp, labels in cache[s]:
                ev.update(decode(lg, bp, labels), labels, video_id=cid)
            m = ev.compute()
            accs.append(m["phase_accuracy"]); f1s.append(m["phase_macro_f1"])
            edits.append(m["phase_edit_score"]); segs.append(m["phase_seg_f1_50"])
        return st.mean(accs), st.mean(f1s), st.mean(edits), st.mean(segs)

    configs = [
        ("plain (argmax)", lambda lg, bp, y: lg.argmax(0)),
        ("boundary-gate τ0.3", lambda lg, bp, y: sticky_decode(lg, bp, 0.3)),
        ("boundary-gate τ0.5", lambda lg, bp, y: sticky_decode(lg, bp, 0.5)),
        ("debounce k=2", lambda lg, bp, y: debounce_decode(lg, 2)),
        ("debounce k=3", lambda lg, bp, y: debounce_decode(lg, 3)),
        ("debounce k=5", lambda lg, bp, y: debounce_decode(lg, 5)),
        ("debounce k=7", lambda lg, bp, y: debounce_decode(lg, 7)),
    ]
    print(f"base(同env val): acc={base_acc*100:.2f}  edit={base_edit:.2f}\n")
    hdr = f"{'decode':>20} | {'acc':>6} {'macroF1':>7} {'edit':>6} {'segF1@50':>8} | {'Δacc':>7} {'Δedit':>7}"
    print(hdr); print("-" * len(hdr))
    ok_any = False
    for name, fn in configs:
        am, fm, em, sm = evalfn(fn)
        da, de = (am - base_acc) * 100, em - base_edit
        maintains = da >= -0.5 and de > 1.0
        ok_any = ok_any or maintains
        flag = "  <= acc維持で edit改善!" if maintains else ""
        print(f"{name:>20} | {am*100:6.2f} {fm*100:7.2f} {em:6.2f} {sm:8.3f} | {da:+7.2f} {de:+7.2f}{flag}")
    print("\n" + ("[compare] acc 維持で edit 改善する因果 decode が存在" if ok_any
                   else "[compare] どの因果 decode も acc を保って edit を上げられない "
                        "→ 負の結論は decode 設計非依存（頑健）"))


if __name__ == "__main__":
    main()

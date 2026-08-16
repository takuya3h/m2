#!/usr/bin/env python
"""事後評価: 保存された重みから、記録に無い量を測る。

run が残すのは重みだけで、`predictions/` も `logs/` も空である。したがって
次の二つは metrics.json から取れない。

  1. 推論の出来（曲線下面積と平均適合率）
     **正しさの割合だけを見ない**（SPEC 注意 2）。教師が偏っているため、
     多数派を出すだけで割合は高く出る。
  2. 工程ごとの分解（hemostasis を含む）

学習・評価コードは変更しない（禁止 5）。ここでは重みを読んで前向きに
一度通すだけである。書き込みは tasks/ 配下のみ。

使い方:
    python posthoc_eval.py <run_dir> [<run_dir> ...] --out <json>
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import torch

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.datasets.grasp_targets import GRASP_LABEL_NAMES  # noqa: E402
from egosurgery.models.build import build_grasp_phase_injection  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "variants", PROJ / "scripts" / "train_grasp_phase_injection_variants.py"
)
V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V)

PHASE_VOCAB = json.loads(
    (PROJ / "data/processed/phase_manifest/phase_vocab.json").read_text(encoding="utf-8")
)
PHASE_NAMES = [name for name, _ in sorted(PHASE_VOCAB.items(), key=lambda kv: kv[1])]

_CLIP_CACHE: dict[str, list] = {}


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float | None:
    """順位に基づく曲線下面積。片側しかクラスが無ければ None。"""
    pos = labels == 1
    n_pos, n_neg = int(pos.sum()), int((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return None
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1, dtype=np.float64)
    # 同値は平均順位にする（順位相関の定義どおり）
    srt = scores[order]
    i = 0
    while i < len(srt):
        j = i
        while j + 1 < len(srt) and srt[j + 1] == srt[i]:
            j += 1
        if j > i:
            ranks[order[i : j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def average_precision(scores: np.ndarray, labels: np.ndarray) -> float | None:
    """適合率-再現率曲線の下の面積（階段和。sklearn の average_precision と同じ定義）。"""
    if labels.sum() == 0:
        return None
    order = np.argsort(-scores, kind="mergesort")
    lab = labels[order]
    tp = np.cumsum(lab)
    precision = tp / np.arange(1, len(lab) + 1)
    return float((precision * lab).sum() / lab.sum())


def f1_per_class(pred: np.ndarray, true: np.ndarray, n_classes: int) -> dict:
    out = {}
    for c in range(n_classes):
        tp = int(((pred == c) & (true == c)).sum())
        fp = int(((pred == c) & (true != c)).sum())
        fn = int(((pred != c) & (true == c)).sum())
        denom = 2 * tp + fp + fn
        out[PHASE_NAMES[c]] = {
            "f1": (2 * tp / denom) if denom else None,
            "support": int((true == c).sum()),
        }
    return out


def load_val_clips(cfg):
    key = f"{cfg.data.feature_cache}|{cfg.data.phase_manifest}|{cfg.grasp_inference.annotation_root}"
    if key not in _CLIP_CACHE:
        _CLIP_CACHE[key] = V.load_clips("val", cfg)
    return _CLIP_CACHE[key]


def evaluate_run(run_dir: Path) -> dict:
    from omegaconf import OmegaConf

    cfg = OmegaConf.load(run_dir / "config.yaml")
    ckpt = run_dir / "checkpoints" / "best_grasp_phase.pth"
    if not ckpt.exists():
        return {"run": str(run_dir.relative_to(PROJ)), "error": "checkpoint missing"}

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_grasp_phase_injection(V.build_component_cfg_variants(cfg)).to(device)
    # 自前の checkpoint はテンソルと int だけを持つ。任意オブジェクトを
    # 復元させる必要は無いので weights_only で読む。
    state = torch.load(ckpt, map_location=device, weights_only=True)
    model.load_state_dict(state["model"])
    model.eval()

    clips = load_val_clips(cfg)
    phase_pred, phase_true = [], []
    grasp_scores, grasp_true, grasp_valid = [], [], []
    with torch.no_grad():
        for clip in clips:
            # 学習側の evaluate と同じ扱いにする（変えると別物を測ることになる）:
            #   - `_batch` で組む
            #   - 教師を forward へ渡す（正解の信号はこれが無いと拒む設計）
            #   - `phase_logits[-1]` の最終段を使い、クラス次元で argmax
            _, _, phase_labels, grasp_targets_np, valid = clip
            x, phase_y, grasp_y, grasp_mask = V._batch(clip, device)
            out = model(x, grasp_targets=grasp_y, grasp_valid=grasp_mask)
            logits = out["phase_logits"][-1]
            phase_pred.append(logits[0].argmax(dim=0).cpu().numpy())
            phase_true.append(phase_labels)
            g = out["grasp_logits"]
            if g is not None:
                grasp_scores.append(torch.sigmoid(g)[0].T.cpu().numpy())
                grasp_true.append(grasp_targets_np)
                grasp_valid.append(valid)

    pp = np.concatenate(phase_pred)
    pt = np.concatenate(phase_true)
    result = {
        "run": str(run_dir.relative_to(PROJ)),
        "seed": int(cfg.seed),
        "arm": str(cfg.grasp_inference.arm),
        "signal": str(cfg.grasp_inference.get("signal", "<none>")),
        "staged": bool(cfg.grasp_inference.get("staged", False)),
        "checkpoint_epoch": int(state.get("epoch", -1)),
        "n_val_frames": int(len(pt)),
        "phase_accuracy_recomputed": float((pp == pt).mean()),
        "phase_f1_per_class": f1_per_class(pp, pt, len(PHASE_NAMES)),
    }
    if grasp_scores:
        s = np.concatenate(grasp_scores, axis=0)
        t = np.concatenate(grasp_true, axis=0)
        v = np.concatenate(grasp_valid, axis=0)
        dims = {}
        for i, name in enumerate(GRASP_LABEL_NAMES):
            si, ti = s[v, i], t[v, i]
            dims[name] = {
                "auc": roc_auc(si, ti),
                "average_precision": average_precision(si, ti),
                "accuracy": float(((si >= 0.5).astype(np.float64) == ti).mean()),
                "positive_rate": float(ti.mean()),
                "n": int(len(ti)),
            }
        result["grasp_quality"] = dims
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    results = []
    for i, r in enumerate(args.runs, 1):
        results.append(evaluate_run(Path(r) if Path(r).is_absolute() else PROJ / r))
        if i % 20 == 0 or i == len(args.runs):
            print(f"  {i}/{len(args.runs)}", flush=True)
    Path(args.out).write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"written: {args.out} ({len(results)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

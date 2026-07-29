#!/usr/bin/env python3
"""G-2 Task E: region-token に ROI チャネルを足して工程認識を学習する。

4 系統:
  base      : region-token 3840-d のみ
  bboxROI   : 3840-d ⊕ bboxROI (15 x D)
  maskROI   : 3840-d ⊕ maskROI (15 x D)
  randROI   : 3840-d ⊕ randROI (15 x D)

既存の train_t1a.py / extract_t1a_regiontoken.py は **変更しない**。本スクリプトは独立。
学習設定 (TeCNO・lr・epochs・smoothing) は train_t1a.py と同一に揃える。

per-frame 予測を val / test 両方で保存する (既存 trainer は argmax 直後に破棄するため)。

Usage:
    source .venv-relation-detr/bin/activate     # 拡張ロードの検証のため
    python scripts/train_g2.py --system maskROI --seed 42 --out $OUT
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))
from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from egosurgery.models.heads.tecno_head import TeCNO  # noqa: E402

MANIFEST_DIR = PROJ / "data/processed/phase_manifest"
REGION_DIR = PROJ / "data/processed/t1a_regiontoken/relation_detr_seed42"
REGION_DIM = 3840
CLASS_NAMES = ["anesthesia", "closure", "design", "disinfection", "dissection",
               "dressing", "hemostasis", "incision", "irrigation"]
SYSTEMS = ["base", "bboxROI", "maskROI", "randROI"]


def env_info(require_ext: bool) -> dict:
    """実行環境を記録する。require_ext=True なら拡張ロードを検証する。"""
    info = {
        "torch": torch.__version__, "cuda_version": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cudnn": torch.backends.cudnn.version(),
        "host": os.uname().nodename,
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJ,
                                 capture_output=True, text=True).stdout.strip(),
        "ninja_on_path": shutil.which("ninja"),
        "python": sys.version.split()[0],
    }
    # 学習自体は検出器を呼ばないが、特徴が正しい環境で作られたかを追跡できるよう記録する
    info["msdeformattn_extension_loaded"] = None
    if require_ext:
        try:
            sys.path.insert(0, str(PROJ / "third_party" / "Relation-DETR"))
            import models.bricks.ms_deform_attn as msda
            info["msdeformattn_extension_loaded"] = getattr(msda, "_C", None) is not None
        except Exception as e:  # noqa: BLE001
            info["msdeformattn_extension_loaded"] = False
            info["msdeformattn_error"] = str(e)[:200]
    return info


def load_clips(split: str, system: str, roi_dir: Path):
    """(clip_id, feats, labels, frame_ids) を返す。join は frame_id (basename 相当)。"""
    # NpzFile への添字アクセスは **毎回** zip メンバ全体を読み直して新しい配列を返す。
    # さらに arr[i] は view なので、その行 1 つが親配列 (train で 148 MB) を丸ごと
    # メモリに固定する。内包表記の中で参照すると行数ぶん親配列が積み上がり
    # (train: 9657 x 148 MB ≒ 1.4 TB) OOM する。必ずループ外で 1 回だけ読む。
    r = np.load(REGION_DIR / f"{split}_regiontoken.npz")
    reg_arr = r["region"]
    reg = {str(f): reg_arr[i] for i, f in enumerate(r["frame_ids"])}
    roi = None
    if system != "base":
        p = roi_dir / f"{split}_{system}.npz"
        assert p.exists(), f"ROI 特徴が無い: {p}"
        a = np.load(p)
        roi_arr = a["roi"]
        roi = {str(f): roi_arr[i] for i, f in enumerate(a["frame_ids"])}

    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        rows, fids = [], []
        for fr in clip["frames"]:
            fid = fr["frame"]
            if fid not in reg:
                raise KeyError(f"[g2] region-token に frame_id 欠落: {fid} ({split})")
            if roi is None:
                rows.append(reg[fid])
            else:
                if fid not in roi:
                    raise KeyError(f"[g2] ROI 特徴に frame_id 欠落: {fid} ({split})")
                rows.append(np.concatenate([reg[fid], roi[fid]]))
            fids.append(fid)
        clips.append((clip["clip_id"], np.stack(rows).astype(np.float32),
                      np.asarray([fr["label"] for fr in clip["frames"]], dtype=np.int64),
                      fids))
    return clips


def smoothing_loss(logits):
    ls = F.log_softmax(logits, dim=1)
    mse = F.mse_loss(ls[:, :, 1:], ls[:, :, :-1], reduction="none")
    return torch.clamp(mse, max=16.0).mean()


@torch.no_grad()
def evaluate(model, clips, device, collect=False):
    model.eval()
    m = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    preds_out = []
    for clip_id, feats, labels, fids in clips:
        x = torch.from_numpy(feats).T.unsqueeze(0).to(device)
        logits = model(x)[-1]
        preds = logits[0].argmax(0).cpu().numpy()
        m.update(preds, labels, video_id=clip_id)
        if collect:
            for i, fid in enumerate(fids):
                preds_out.append({"basename": fid, "clip_id": clip_id,
                                  "gt": int(labels[i]), "pred": int(preds[i])})
    return m.compute(), preds_out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True, choices=SYSTEMS)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--num-stages", type=int, default=2)
    ap.add_argument("--num-layers", type=int, default=8)
    ap.add_argument("--num-f-maps", type=int, default=64)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    out_root = Path(args.out)
    roi_dir = out_root / "features"
    run = f"{args.system}_seed{args.seed}"
    run_dir = out_root / "runs" / run
    (run_dir / "predictions").mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)

    env = env_info(require_ext=True)
    tr = load_clips("train", args.system, roi_dir)
    va = load_clips("val", args.system, roi_dir)
    te = load_clips("test", args.system, roi_dir)
    if args.smoke:
        tr, va, te = tr[:2], va[:1], te[:1]
    in_dim = int(tr[0][1].shape[1])
    print(f"[g2] system={args.system} seed={args.seed} in_dim={in_dim} "
          f"clips train/val/test={len(tr)}/{len(va)}/{len(te)} device={device}")

    model = TeCNO(num_stages=args.num_stages, num_layers=args.num_layers,
                  num_f_maps=args.num_f_maps, in_dim=in_dim,
                  num_classes=len(CLASS_NAMES)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()

    best = {"phase_accuracy": -1.0}
    best_epoch, best_state = -1, None
    t0 = time.time()
    for ep in range(args.epochs):
        model.train()
        random.shuffle(tr)
        loss_sum = 0.0
        for _, feats, labels, _ in tr:
            x = torch.from_numpy(feats).T.unsqueeze(0).to(device)
            y = torch.from_numpy(labels).to(device)
            outs = model(x)
            loss = sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in outs)
            opt.zero_grad(); loss.backward(); opt.step()
            loss_sum += float(loss)
        vm, _ = evaluate(model, va, device)
        if vm["phase_accuracy"] > best["phase_accuracy"]:
            best, best_epoch = vm, ep
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        if (ep + 1) % 10 == 0:
            print(f"  ep{ep+1:3d} loss={loss_sum/len(tr):.4f} val_acc={vm['phase_accuracy']:.4f}",
                  flush=True)

    # best epoch の重みで val / test を最終評価し per-frame 予測を保存する
    model.load_state_dict(best_state)
    val_m, val_p = evaluate(model, va, device, collect=True)
    test_m, test_p = evaluate(model, te, device, collect=True)
    for name, p in (("val", val_p), ("test", test_p)):
        with open(run_dir / "predictions" / f"{name}_preds.json", "w") as f:
            json.dump(p, f)

    fb = {}
    for sp in ("train", "val", "test"):
        q = out_root / "json" / f"f_roi_stats_{sp}.json"
        if q.exists():
            s = json.loads(q.read_text())
            fb[sp] = {"fallback_rate": s.get("fallback_rate"), "D": s.get("D")}

    res = {
        "run": run, "system": args.system, "seed": args.seed,
        "in_dim": in_dim, "epochs": args.epochs, "best_epoch": best_epoch,
        "train_seconds": time.time() - t0,
        "val": val_m, "test": test_m,
        "roi_fallback": fb,
        "n_clips": {"train": len(tr), "val": len(va), "test": len(te)},
        "hyperparams": {"lr": args.lr, "weight_decay": args.weight_decay,
                        "num_stages": args.num_stages, "num_layers": args.num_layers,
                        "num_f_maps": args.num_f_maps, "smoothing_weight": 0.15},
    }
    (run_dir / "metrics.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    (run_dir / "env.json").write_text(json.dumps(env, indent=2, ensure_ascii=False))
    print(f"[g2] {run} best_ep={best_epoch} "
          f"val_acc={val_m['phase_accuracy']:.4f} val_f1={val_m['phase_macro_f1']:.4f} "
          f"test_acc={test_m['phase_accuracy']:.4f} test_f1={test_m['phase_macro_f1']:.4f} "
          f"({res['train_seconds']:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

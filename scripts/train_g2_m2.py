#!/usr/bin/env python3
"""M2: epoch 別 val 履歴を保存し、5 つの epoch 選択規則を **同一の学習軌跡から**評価する。

`train_g2.py` は変更しない（本スクリプトは独立）。学習設定・seed の使い方・データの
読み方・モデル構成は `train_g2.py` と同一に揃える（TeCNO 2stage/8layer/64 f_maps、
lr 5e-4、wd 0.01、50 epoch、smoothing 0.15、`random.shuffle(tr)` を毎 epoch）。

M2 の必須要件（事前登録 prereg/m2_prediction.md）:
  - epoch 別 val 履歴（val accuracy / val loss / val macro-F1）を全 epoch 保存する
  - 5 規則（R-acc / R-last / R-loss / R-mf1 / R-topk）の候補重みを保持し、
    それぞれで val / test を評価して per-frame 予測を保存する
  - 反復 ID（--rep）を記録し、同一 seed の反復を識別できるようにする
  - env.json を run ごとの実測値で記録する

規則ごとに別 run を回さないのが要点。同一軌跡から評価するので、規則間の差を
「規則の効果」に厳密に帰属できる（決定性制御は交絡を避けるため入れない）。

全 epoch の重みを保存すると破綻するため、**5 規則が指す候補だけ**をオンラインで
追跡して最大 6 個の state_dict のみ保持する。

Usage:
    source .venv-relation-detr/bin/activate
    python scripts/train_g2_m2.py --system bboxROI --seed 42 --rep 1 --out $OUT
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
from datetime import datetime, timezone
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
CLASS_NAMES = ["anesthesia", "closure", "design", "disinfection", "dissection",
               "dressing", "hemostasis", "incision", "irrigation"]
SYSTEMS = ["base", "bboxROI", "maskROI", "randROI", "shuffleROI",
           "handROIbbox2", "handROImask2", "bboxROI_handROIbbox2"]
RULES = ["R-acc", "R-last", "R-loss", "R-mf1", "R-topk"]
TOPK = 3


def env_info(system: str, seed: int, rep: int) -> dict:
    """実行環境と run 固有の実測値を記録する。"""
    info = {
        "system": system, "seed": seed, "rep": rep,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "torch": torch.__version__, "cuda_version": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "cudnn": torch.backends.cudnn.version(),
        "host": os.uname().nodename,
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJ,
                                 capture_output=True, text=True).stdout.strip(),
        "ninja_on_path": shutil.which("ninja"),
        "python": sys.version.split()[0],
        # 事前登録どおり決定性制御は入れていない（規則の効果と交絡させないため）
        "determinism_controls_enabled": False,
        "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
        "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
    }
    # 特徴が正しい環境で作られたかを追跡する代理指標（学習自体は検出器を呼ばない）
    info["msdeformattn_extension_loaded"] = None
    try:
        sys.path.insert(0, str(PROJ / "third_party" / "Relation-DETR"))
        import models.bricks.ms_deform_attn as msda
        info["msdeformattn_extension_loaded"] = getattr(msda, "_C", None) is not None
    except Exception as e:  # noqa: BLE001
        info["msdeformattn_extension_loaded"] = False
        info["msdeformattn_error"] = str(e)[:200]
    return info


def load_clips(split: str, system: str, feat_dirs: list[Path]):
    """train_g2.py:load_clips と同一。ROI npz は複数ディレクトリから探す。

    NpzFile への添字アクセスは毎回 zip メンバ全体を読み直し、arr[i] は view なので
    親配列を丸ごと固定する。必ずループ外で 1 回だけ読む。
    """
    r = np.load(REGION_DIR / f"{split}_regiontoken.npz")
    reg_arr = r["region"]
    reg = {str(f): reg_arr[i] for i, f in enumerate(r["frame_ids"])}
    roi = None
    if system != "base":
        p = None
        for d in feat_dirs:
            cand = d / f"{split}_{system}.npz"
            if cand.exists():
                p = cand
                break
        assert p is not None, f"ROI 特徴が見つからない: {split}_{system}.npz in {feat_dirs}"
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
                raise KeyError(f"[m2] region-token に frame_id 欠落: {fid} ({split})")
            if roi is None:
                rows.append(reg[fid])
            else:
                if fid not in roi:
                    raise KeyError(f"[m2] ROI 特徴に frame_id 欠落: {fid} ({split})")
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
def evaluate(model, clips, device, ce, collect=False):
    """指標に加えて **val loss** も返す（R-loss の判定に必要）。"""
    model.eval()
    m = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    preds_out = []
    loss_sum, n = 0.0, 0
    for clip_id, feats, labels, fids in clips:
        x = torch.from_numpy(feats).T.unsqueeze(0).to(device)
        y = torch.from_numpy(labels).to(device)
        outs = model(x)
        logits = outs[-1]
        # 学習時と同じ形の損失（全 stage 合計 + smoothing）を val 上で測る
        loss_sum += float(sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in outs))
        n += 1
        preds = logits[0].argmax(0).cpu().numpy()
        m.update(preds, labels, video_id=clip_id)
        if collect:
            for i, fid in enumerate(fids):
                preds_out.append({"basename": fid, "clip_id": clip_id,
                                  "gt": int(labels[i]), "pred": int(preds[i])})
    return m.compute(), (loss_sum / n if n else float("nan")), preds_out


def cpu_state(model):
    return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}


def avg_states(states: list[dict], weights: list[float]) -> dict:
    """R-topk 用の重み平均。float で平均して元 dtype へ戻す。"""
    w = np.asarray(weights, dtype=np.float64)
    w = w / w.sum()
    out = {}
    for k in states[0]:
        acc = torch.zeros_like(states[0][k], dtype=torch.float64)
        for s, wi in zip(states, w):
            acc += s[k].to(torch.float64) * float(wi)
        out[k] = acc.to(states[0][k].dtype)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", required=True, choices=SYSTEMS)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--rep", type=int, required=True, help="反復 ID（同一 seed の識別用）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--feat-dir", action="append", required=True,
                    help="ROI npz を探すディレクトリ（複数指定可）")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--num-stages", type=int, default=2)
    ap.add_argument("--num-layers", type=int, default=8)
    ap.add_argument("--num-f-maps", type=int, default=64)
    args = ap.parse_args()

    # 環境ガード（§0.2）
    assert shutil.which("ninja") is not None, (
        "ninja が PATH にありません。source .venv-relation-detr/bin/activate してください")
    assert torch.cuda.is_available(), "CUDA unavailable"

    out_root = Path(args.out)
    feat_dirs = [Path(d) for d in args.feat_dir]
    run = f"{args.system}_seed{args.seed}_rep{args.rep}"
    run_dir = out_root / "runs" / run
    (run_dir / "predictions").mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda")
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)

    env = env_info(args.system, args.seed, args.rep)
    assert env["msdeformattn_extension_loaded"] is True, \
        f"MSDeformAttn 拡張がロードできない: {env.get('msdeformattn_error')}"

    tr = load_clips("train", args.system, feat_dirs)
    va = load_clips("val", args.system, feat_dirs)
    te = load_clips("test", args.system, feat_dirs)
    in_dim = int(tr[0][1].shape[1])
    print(f"[m2] {run} in_dim={in_dim} clips={len(tr)}/{len(va)}/{len(te)}", flush=True)

    model = TeCNO(num_stages=args.num_stages, num_layers=args.num_layers,
                  num_f_maps=args.num_f_maps, in_dim=in_dim,
                  num_classes=len(CLASS_NAMES)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()

    history = []
    # 5 規則が指す候補のみ保持する（全 epoch 保存は 72 run では破綻する）
    best = {"acc": (-1.0, -1, None), "loss": (float("inf"), -1, None),
            "mf1": (-1.0, -1, None)}
    topk: list[tuple[float, int, dict]] = []      # (val_acc, epoch, state) 上位 k
    t0 = time.time()
    for ep in range(args.epochs):
        model.train()
        random.shuffle(tr)
        tl = 0.0
        for _, feats, labels, _ in tr:
            x = torch.from_numpy(feats).T.unsqueeze(0).to(device)
            y = torch.from_numpy(labels).to(device)
            outs = model(x)
            loss = sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in outs)
            opt.zero_grad(); loss.backward(); opt.step()
            tl += float(loss)
        vm, vloss, _ = evaluate(model, va, device, ce)
        history.append({
            "epoch": ep, "train_loss": tl / len(tr), "val_loss": vloss,
            "val_accuracy": vm["phase_accuracy"], "val_macro_f1": vm["phase_macro_f1"],
            "val_jaccard": vm["phase_jaccard"],
            "val_per_class_f1": vm["phase_per_class_f1"],
        })
        st = None
        if vm["phase_accuracy"] > best["acc"][0]:
            st = st or cpu_state(model); best["acc"] = (vm["phase_accuracy"], ep, st)
        if vloss < best["loss"][0]:
            st = st or cpu_state(model); best["loss"] = (vloss, ep, st)
        if vm["phase_macro_f1"] > best["mf1"][0]:
            st = st or cpu_state(model); best["mf1"] = (vm["phase_macro_f1"], ep, st)
        # top-k（val accuracy）を維持
        if len(topk) < TOPK or vm["phase_accuracy"] > min(t[0] for t in topk):
            st = st or cpu_state(model)
            topk.append((vm["phase_accuracy"], ep, st))
            topk.sort(key=lambda t: -t[0])
            topk[:] = topk[:TOPK]
        if (ep + 1) % 25 == 0:
            print(f"  ep{ep+1:3d} tl={tl/len(tr):.4f} vl={vloss:.4f} "
                  f"vacc={vm['phase_accuracy']:.4f} vmf1={vm['phase_macro_f1']:.4f}", flush=True)
    last_state = cpu_state(model)
    train_seconds = time.time() - t0

    # --- 5 規則それぞれで最終評価する（同一軌跡・同一候補集合） ---
    rule_states = {
        "R-acc": (best["acc"][1], best["acc"][2]),
        "R-last": (args.epochs - 1, last_state),
        "R-loss": (best["loss"][1], best["loss"][2]),
        "R-mf1": (best["mf1"][1], best["mf1"][2]),
        "R-topk": (sorted(e for _, e, _ in topk),
                   avg_states([s for _, _, s in topk], [a for a, _, _ in topk])),
    }
    results = {}
    for rule, (sel_epoch, state) in rule_states.items():
        model.load_state_dict(state)
        vm, vloss, vp = evaluate(model, va, device, ce, collect=True)
        tm, tloss, tp = evaluate(model, te, device, ce, collect=True)
        d = run_dir / "predictions" / rule
        d.mkdir(parents=True, exist_ok=True)
        (d / "val_preds.json").write_text(json.dumps(vp))
        (d / "test_preds.json").write_text(json.dumps(tp))
        results[rule] = {"selected_epoch": sel_epoch, "val": vm, "val_loss": vloss,
                         "test": tm, "test_loss": tloss}
        print(f"  [{rule:7s}] ep={sel_epoch} val_acc={vm['phase_accuracy']:.4f} "
              f"val_mf1={vm['phase_macro_f1']:.4f}", flush=True)

    env["finished_at"] = datetime.now(timezone.utc).isoformat()
    (run_dir / "env.json").write_text(json.dumps(env, indent=2, ensure_ascii=False))
    (run_dir / "val_history.json").write_text(json.dumps(
        {"run": run, "system": args.system, "seed": args.seed, "rep": args.rep,
         "epochs": args.epochs, "history": history}, indent=2, ensure_ascii=False))
    (run_dir / "metrics.json").write_text(json.dumps(
        {"run": run, "system": args.system, "seed": args.seed, "rep": args.rep,
         "in_dim": in_dim, "epochs": args.epochs, "train_seconds": train_seconds,
         "rules": results,
         "hyperparams": {"lr": args.lr, "weight_decay": args.weight_decay,
                         "num_stages": args.num_stages, "num_layers": args.num_layers,
                         "num_f_maps": args.num_f_maps, "smoothing_weight": 0.15,
                         "topk": TOPK},
         "n_clips": {"train": len(tr), "val": len(va), "test": len(te)}},
        indent=2, ensure_ascii=False))
    print(f"[m2] {run} done ({train_seconds:.0f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

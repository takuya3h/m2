#!/usr/bin/env python
"""T1a region-token→工程（Tier-1 主力⭐ TAPIS/GraSP 型・②系統）= Δ_phase を測る結合本体。

比較の三角形（凍結源 Relation-DETR seed42）で、凍結検出器の **object-query 埋め込み
（region token, クラス別 256-d）** を工程枝に **入力連結** する。TAPIS/GraSP の「object/region
token → 工程」を、TeCNO の入力を frame GAP → region token に差し替える形で実装する:

    入力 = concat([ GAP(C5) 2048-d , region-token 15×256=3840-d ]) = 5888-d  → 素 causal TeCNO

B2a（①, 15-d tool-presence スカラ）と違い、T1a は同じ 15 器具クラス軸で **256-d 埋め込み**
（物体特徴）を渡す。土台（分母）= S4 base（素 TeCNO on GAP = 0.8986±0.0034）を流用し、
**変える軸は「region-token を見せるか否か」の 1 点**。+region の容量増は測りたい結合そのもの。

Δ_phase = (T1a − S4 base)。**別サーバーで実行する場合**、分母は lecun 実測 0.8986±0.0034 を
流用し、サーバー差を §8.0 として notes/experiment_log に明文化する（同一 ckpt・同一前処理ゆえ
差は TeCNO 学習の数値のみ）。

入力:
    data/processed/stage1_features/<frozen_src>/{train,val,test}_gap.npz（frame_ids, features=GAP2048）
    data/processed/t1a_regiontoken/<frozen_src>/{train,val,test}_regiontoken.npz（frame_ids, region=3840）
    data/processed/phase_manifest/{train,val,test}.json（clip 時系列順 + label）

本体 .venv で実行（Relation-DETR 非依存・キャッシュのみ読む。S4 と同一の作法・ハイパー）:
  .venv/bin/python scripts/train_t1a.py --epochs 50 --seed 42
  .venv/bin/python scripts/train_t1a.py --smoke           # 数 epoch・少 clip で疎通確認（証跡なし）
  .venv/bin/python scripts/train_t1a.py --region-only      # 連結せず region のみ（replace 版・別解）
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from egosurgery.models.heads.tecno_head import TeCNO  # noqa: E402
from egosurgery.utils.eval_recipe import (  # noqa: E402
    PAPER_SPLIT_SIZES,
    PHASE_EVAL_PROTOCOL,
    build_eval_recipe,
)
from egosurgery.utils.experiment_manager import ExperimentManager  # noqa: E402
from egosurgery.utils.server_name import resolve_server_name  # noqa: E402

FROZEN_SRC = "relation_detr_seed42"
GAP_DIR = PROJ / "data" / "processed" / "stage1_features" / FROZEN_SRC
REGION_DIR = PROJ / "data" / "processed" / "t1a_regiontoken" / FROZEN_SRC
MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())
GAP_DIM = 2048
REGION_DIM = 15 * 256  # 3840


def load_clips(split: str, region_only: bool) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """(clip_id, feats, labels) を返す。feats = region(3840) or [GAP2048 ⊕ region3840](5888)。

    GAP・region いずれも frame_id でキー化して clip フレーム順に整列・連結する。
    どちらかに無い frame があれば整合不良として Fail Loud（KeyError）— ダミー補完しない。
    """
    g = np.load(GAP_DIR / f"{split}_gap.npz")
    gap_all = g["features"]  # NpzFile 遅延展開: 一度だけ取り出す
    gap_by_frame = {str(fid): gap_all[i] for i, fid in enumerate(g["frame_ids"])}

    r = np.load(REGION_DIR / f"{split}_regiontoken.npz")
    reg_all = r["region"]
    reg_by_frame = {str(fid): reg_all[i] for i, fid in enumerate(r["frame_ids"])}

    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        frames = clip["frames"]
        rows = []
        for fr in frames:
            fid = fr["frame"]
            if fid not in reg_by_frame:
                raise KeyError(f"[t1a] region-token に frame_id 欠落: {fid} ({split})")
            if region_only:
                rows.append(reg_by_frame[fid])
            else:
                if fid not in gap_by_frame:
                    raise KeyError(f"[t1a] GAP 特徴に frame_id 欠落: {fid} ({split})")
                rows.append(np.concatenate([gap_by_frame[fid], reg_by_frame[fid]]))  # 2048+3840
        feats = np.stack(rows).astype(np.float32)
        labels = np.asarray([fr["label"] for fr in frames], dtype=np.int64)
        clips.append((clip["clip_id"], feats, labels))
    return clips


def smoothing_loss(logits: torch.Tensor) -> torch.Tensor:
    """MS-TCN の T-MSE 平滑化損失（S4/B2a と同一定義）。"""
    ls = F.log_softmax(logits, dim=1)
    mse = F.mse_loss(ls[:, :, 1:], ls[:, :, :-1], reduction="none")
    return torch.clamp(mse, max=16.0).mean()


@torch.no_grad()
def evaluate(model: nn.Module, clips, device) -> dict:
    model.eval()
    metrics = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    for clip_id, feats, labels in clips:
        x = torch.from_numpy(feats).T.unsqueeze(0).to(device)  # (1, in_dim, T)
        logits = model(x)[-1]
        preds = logits[0].argmax(0).cpu().numpy()
        metrics.update(preds, labels, video_id=clip_id)
    return metrics.compute()


DESC = "t1a_regiontoken"


def _build_cfg(args, server_name: str, in_dim: int, n_train: int, n_val: int) -> dict:
    return {
        "experiment": {"category": "transfer", "step": "t1a_regiontoken", "description": DESC},
        "seed": args.seed,
        "frozen_source": {"detector": "relation_detr", "seed": 42, "backbone": "resnet50",
                          "gap_cache": str(GAP_DIR.relative_to(PROJ)),
                          "region_cache": str(REGION_DIR.relative_to(PROJ))},
        "method": {"name": "t1a_region_to_phase", "system": "②feature_level/object-token",
                   "ref": "TAPIS/GraSP (MedIA 2025)", "direction": "det->phase",
                   "coupling": ("regiontoken_only" if args.region_only else "regiontoken_concat_gap"),
                   "region_repr": "per_class_256d_score_weighted", "region_dim": REGION_DIM,
                   "neck": None, "grad_crossing": False},
        "model": {"temporal_head": "tecno", "num_stages": args.num_stages,
                  "num_layers": args.num_layers, "num_f_maps": args.num_f_maps,
                  "in_dim": in_dim, "num_phases": len(CLASS_NAMES), "causal": True},
        "train": {"epochs": args.epochs, "lr": args.lr, "weight_decay": args.weight_decay,
                  "freeze_backbone": True, "smoothing_weight": 0.15},
        "data": {"n_train_clips": n_train, "n_val_clips": n_val},
        "delta": {"phase_denominator": "s4_phase_baseline (frozen_tecno_phase_baseline)",
                  "denominator_value_lecun": "0.8986±0.0034",
                  "note": "Δ_phase = (T1a − S4 base). 別サーバー実行時は lecun 分母を流用し "
                          "サーバー差を §8.0 明文化（同一 ckpt・同一前処理ゆえ差は TeCNO 学習数値のみ）。"},
        "server_name": server_name,
    }


def _build_phase_recipe(args, server_name: str, in_dim: int) -> dict:
    test_cfg = {
        "task": "phase",
        **PHASE_EVAL_PROTOCOL,
        "backbone": "relation_detr_resnet50_frozen_seed42",
        "temporal_head": "tecno",
        "num_stages": args.num_stages,
        "num_layers": args.num_layers,
        "num_f_maps": args.num_f_maps,
        "in_dim": in_dim,
        "coupling": ("t1a_regiontoken_only" if args.region_only else "t1a_regiontoken_concat_gap"),
        "region_dim": REGION_DIM,
    }
    return build_eval_recipe(
        test_cfg=test_cfg, split_sizes=PAPER_SPLIT_SIZES, server_name=server_name,
        gpu_count=1, effective_batch_size=1, lr_scaling="none",
    )


def _write_notes(exp_dir: Path, args, best: dict, server_name: str, in_dim: int) -> None:
    note = (
        f"# T1a region-token→工程（Tier-1 主力⭐ TAPIS/GraSP 型・②系統）\n\n"
        f"凍結 Relation-DETR seed42 の object-query 埋め込み（クラス別 256-d, score 加重）を "
        f"GAP(2048) に{'' if not args.region_only else ' 連結せず単独で'}入力 → 素 causal TeCNO。\n"
        f"勾配は交差させず凍結 region token を渡す。online/causal（未来不使用）。\n\n"
        f"## 結果（best @epoch {best.get('epoch')}）\n"
        f"- accuracy={best['phase_accuracy']:.4f} / macro_f1={best['phase_macro_f1']:.4f}\n"
        f"- edit={best['phase_edit_score']:.2f} / seg_f1@10/25/50="
        f"{best['phase_seg_f1_10']:.2f}/{best['phase_seg_f1_25']:.2f}/{best['phase_seg_f1_50']:.2f}\n\n"
        f"## 構成\n- seed={args.seed} epochs={args.epochs} lr={args.lr} "
        f"in_dim={in_dim}{'' if args.region_only else '(=2048+3840)'} "
        f"stages={args.num_stages} layers={args.num_layers} f_maps={args.num_f_maps}\n"
        f"- server={server_name} / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)\n\n"
        f"## Δ\n- Δ_phase = (T1a − S4 base 0.8986±0.0034[lecun])。同一土台（凍結backbone/GAP/recipe/seed・neck無）。\n"
        f"- **別サーバー実行時**: 分母は lecun 値流用、サーバー差を §8.0 明文化。\n"
        f"- 3-seed 揃ったら paired-σ(対seed差) で §10.1 判定（|Δ|>paired-σ かつ同符号で有意）。\n"
    )
    (exp_dir / "notes.md").write_text(note, encoding="utf-8")


def train(args) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    in_dim = REGION_DIM if args.region_only else (GAP_DIM + REGION_DIM)  # 3840 or 5888
    train_clips = load_clips("train", args.region_only)
    val_clips = load_clips("val", args.region_only)
    if args.smoke:
        train_clips, val_clips = train_clips[:3], val_clips[:2]
    print(f"[t1a] train clips={len(train_clips)}  val clips={len(val_clips)}  "
          f"in_dim={in_dim}  region_only={args.region_only}  classes={len(CLASS_NAMES)}  device={device}")

    server_name = resolve_server_name(None)
    manager = exp_dir = None
    if not args.smoke and not args.no_evidence:
        manager = ExperimentManager(
            base_dir=str(PROJ / "experiments"), category="transfer",
            step="t1a_regiontoken", description=DESC, seed=args.seed,
        )
        manager.setup(_build_cfg(args, server_name, in_dim, len(train_clips), len(val_clips)))
        exp_dir = manager.exp_dir
        print(f"[t1a] evidence dir: {exp_dir}")

    model = TeCNO(num_stages=args.num_stages, num_layers=args.num_layers,
                  num_f_maps=args.num_f_maps, in_dim=in_dim,
                  num_classes=len(CLASS_NAMES)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()

    best = {"phase_accuracy": -1.0}
    for epoch in range(args.epochs):
        model.train()
        random.shuffle(train_clips)
        ep_loss = 0.0
        for clip_id, feats, labels in train_clips:
            x = torch.from_numpy(feats).T.unsqueeze(0).to(device)
            y = torch.from_numpy(labels).to(device)
            outs = model(x)
            loss = sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in outs)
            opt.zero_grad()
            loss.backward()
            opt.step()
            ep_loss += float(loss)
        val = evaluate(model, val_clips, device)
        print(f"[t1a][epoch {epoch + 1}/{args.epochs}] loss={ep_loss / max(len(train_clips),1):.4f}  "
              f"val_acc={val['phase_accuracy']:.4f}  macroF1={val['phase_macro_f1']:.4f}  "
              f"edit={val['phase_edit_score']:.2f}  segF1@50={val['phase_seg_f1_50']:.2f}")
        if val["phase_accuracy"] > best["phase_accuracy"]:
            best = {**val, "epoch": epoch + 1}
            if exp_dir is not None:
                torch.save({"tecno": model.state_dict(), "epoch": epoch + 1, "val": val},
                           exp_dir / "checkpoints" / "best_tecno.pth")
    print(f"[t1a] best @epoch {best.get('epoch')}: acc={best['phase_accuracy']:.4f} "
          f"macroF1={best['phase_macro_f1']:.4f}")

    if manager is not None:
        per_class = best.get("phase_per_class_f1", {})
        scalars = {k: v for k, v in best.items() if isinstance(v, (int, float))}
        manager.log_eval_recipe(_build_phase_recipe(args, server_name, in_dim))
        manager.log_metrics(scalars)
        manager.log_per_class_ap(per_class)
        _write_notes(exp_dir, args, best, server_name, in_dim)
        print(f"[t1a] evidence written -> {exp_dir}")
    return best


def parse_args():
    p = argparse.ArgumentParser(
        description="T1a region-token→phase coupling (frozen object-query embeddings ⊕ GAP → causal TeCNO).")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--num-stages", type=int, default=2)
    p.add_argument("--num-layers", type=int, default=8)
    p.add_argument("--num-f-maps", type=int, default=64)
    p.add_argument("--region-only", action="store_true",
                   help="GAP と連結せず region token のみを入力（replace 版・別解）")
    p.add_argument("--smoke", action="store_true", help="数 epoch・少 clip で疎通確認（証跡なし）")
    p.add_argument("--no-evidence", action="store_true", help="証跡を残さない（配線検証用）")
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    if a.smoke:
        a.epochs = 3
    train(a)

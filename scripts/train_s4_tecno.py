#!/usr/bin/env python
"""S4 工程認識ベースライン（凍結 backbone + TeCNO）= Δ_phase の分母（研究ピボット §2.2・§4.2）。

2段方式の Stage2b: Stage1 でキャッシュした凍結 Relation-DETR 特徴（GAP 2048-d）を入力に、
TeCNO（causal MS-TCN）を **online/causal** で学習・評価する。S4 は「結合手法から検出を
引いたもの」であり単独最適化はしない（§4.2 核心原則）— ハイパーは控えめに固定する。

入力:
    data/processed/stage1_features/<frozen_src>/{train,val,test}_gap.npz（frame_ids, features）
    data/processed/phase_manifest/{train,val,test}.json（clip 時系列順 + label）
評価: PhaseMetrics（accuracy / macro-F1 / edit / seg-F1@{10,25,50}）。clip 単位で集計。

本体 .venv で実行（Relation-DETR 非依存・キャッシュのみ読む）:
  .venv/bin/python scripts/train_s4_tecno.py --epochs 50 --seed 42
  .venv/bin/python scripts/train_s4_tecno.py --smoke      # 数 epoch・少 clip で疎通確認
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
from egosurgery.models.necks import C5LinearNeck  # noqa: E402
from egosurgery.utils.eval_recipe import (  # noqa: E402
    PAPER_SPLIT_SIZES,
    PHASE_EVAL_PROTOCOL,
    build_eval_recipe,
)
from egosurgery.utils.experiment_manager import ExperimentManager  # noqa: E402
from egosurgery.utils.server_name import resolve_server_name  # noqa: E402

import os  # noqa: E402  frozen-src の env 上書き用（改善検出器の特徴で probe するため）

_FROZEN_SRC = os.environ.get("RELDETR_FROZEN_TAG", "relation_detr_seed42")
CACHE_DIR = PROJ / "data" / "processed" / "stage1_features" / _FROZEN_SRC
MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())


def load_clips(split: str) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """(clip_id, feats (T,2048), labels (T,)) のリストを返す（時系列順）。"""
    d = np.load(CACHE_DIR / f"{split}_gap.npz")
    # NpzFile は遅延ロード: d["features"] へのアクセス毎に全配列を再展開する。必ず一度だけ取り出す。
    feats_all = d["features"]
    frame_ids = d["frame_ids"]
    feat_by_frame = {str(fid): feats_all[i] for i, fid in enumerate(frame_ids)}
    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        frames = clip["frames"]
        feats = np.stack([feat_by_frame[fr["frame"]] for fr in frames]).astype(np.float32)
        labels = np.asarray([fr["label"] for fr in frames], dtype=np.int64)
        clips.append((clip["clip_id"], feats, labels))
    return clips


class _NeckedTeCNO(nn.Module):
    """②特徴レベル系統の S4′ / B1 工程枝: 共有 C5 線形 neck（vector 適用）→ TeCNO。

    入力は凍結 GAP キャッシュ (B, 2048, T)。neck は最終次元=2048 に当てるため転置して適用する
    （masked-GAP 可換性より、これは検出枝の C5 spatial neck と同一定義）。
    """

    def __init__(self, neck: C5LinearNeck, tecno: TeCNO) -> None:
        super().__init__()
        self.neck = neck
        self.tecno = tecno

    def forward(self, x: torch.Tensor):  # x: (B, 2048, T)
        v = self.neck.forward_vector(x.transpose(1, 2))  # (B, T, 2048)
        return self.tecno(v.transpose(1, 2))             # (B, 2048, T) -> TeCNO


def _load_frozen_neck(path: str) -> C5LinearNeck:
    """検出で学習した C5 neck（``c5_neck.weight/bias`` or ``weight/bias``）を凍結 neck としてロードする。

    spatial（検出）と vector（工程）は同一 weight/bias を共有するため、検出 ckpt の重みを
    そのまま vector 適用できる（masked-GAP 可換性）。weight_decay 事故防止のため requires_grad=False。
    """
    sd = torch.load(path, map_location="cpu", weights_only=True)
    sd = sd["model"] if isinstance(sd, dict) and "model" in sd else sd
    w = sd.get("c5_neck.weight", sd.get("weight"))
    b = sd.get("c5_neck.bias", sd.get("bias"))
    if w is None or b is None:
        raise KeyError(f"neck 重み (c5_neck.weight/bias) が {path} に見つかりません")
    neck = C5LinearNeck(dim=int(w.shape[0]))
    with torch.no_grad():
        neck.weight.copy_(w)
        neck.bias.copy_(b)
    for p in neck.parameters():
        p.requires_grad_(False)
    return neck.eval()


def smoothing_loss(logits: torch.Tensor) -> torch.Tensor:
    """MS-TCN の T-MSE 平滑化損失（隣接フレームの log-softmax 差を抑制）。"""
    ls = F.log_softmax(logits, dim=1)
    mse = F.mse_loss(ls[:, :, 1:], ls[:, :, :-1], reduction="none")
    return torch.clamp(mse, max=16.0).mean()


@torch.no_grad()
def evaluate(model: nn.Module, clips, device) -> dict:
    model.eval()
    metrics = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    for clip_id, feats, labels in clips:
        x = torch.from_numpy(feats).T.unsqueeze(0).to(device)  # (1, 2048, T)
        logits = model(x)[-1]                                   # 最終ステージ (1, C, T)
        preds = logits[0].argmax(0).cpu().numpy()
        metrics.update(preds, labels, video_id=clip_id)
    return metrics.compute()


def _desc(args) -> str:
    """証跡 description。S4′（独立neck分母）/ S4″（検出neck転送結合）を接尾辞で区別する。"""
    if args.neck_from:
        return "frozen_tecno_phase_necktransfer"
    return "frozen_tecno_phase_baseline" + ("_neck" if args.use_neck else "")


def _build_cfg(args, server_name: str, n_train: int, n_val: int) -> dict:
    """ExperimentManager.save_config に渡す resolved config（再現用）。"""
    return {
        "experiment": {"category": "phase1", "step": "s4_phase_baseline",
                       "description": _desc(args)},
        "seed": args.seed,
        "frozen_source": {"detector": "relation_detr", "seed": 42, "backbone": "resnet50",
                          "cache_dir": str(CACHE_DIR.relative_to(PROJ))},
        "model": {"temporal_head": "tecno", "num_stages": args.num_stages,
                  "num_layers": args.num_layers, "num_f_maps": args.num_f_maps,
                  "in_dim": 2048, "num_phases": len(CLASS_NAMES), "causal": True,
                  "use_neck": bool(args.use_neck or args.neck_from),
                  "neck": "c5_linear_2048_residual_zeroinit" if (args.use_neck or args.neck_from) else None,
                  "neck_mode": ("detection_transfer_frozen" if args.neck_from
                                else "independent_trained" if args.use_neck else None),
                  "neck_from": args.neck_from},
        "train": {"epochs": args.epochs, "lr": args.lr, "weight_decay": args.weight_decay,
                  "freeze_backbone": True, "smoothing_weight": 0.15},
        "data": {"n_train_clips": n_train, "n_val_clips": n_val},
        "server_name": server_name,
    }


def _build_phase_recipe(args, server_name: str) -> dict:
    """工程 eval_recipe（PHASE_EVAL_PROTOCOL をマージ）。recipes_match の保護対象。"""
    test_cfg = {
        "task": "phase",
        **PHASE_EVAL_PROTOCOL,  # inference_protocol=online_causal / jaccard_mode=strict
        "backbone": "relation_detr_resnet50_frozen_seed42",
        "temporal_head": "tecno",
        "num_stages": args.num_stages,
        "num_layers": args.num_layers,
        "num_f_maps": args.num_f_maps,
    }
    return build_eval_recipe(
        test_cfg=test_cfg, split_sizes=PAPER_SPLIT_SIZES, server_name=server_name,
        gpu_count=1, effective_batch_size=1, lr_scaling="none",
    )


def _write_notes(exp_dir: Path, args, best: dict, server_name: str) -> None:
    note = (
        f"# S4 phase baseline (frozen Relation-DETR + causal TeCNO)\n\n"
        f"凍結源: Relation-DETR seed42 完走 ckpt（Stage1 GAP 2048-d をキャッシュ）。\n"
        f"online/causal（未来フレーム不使用）。S4 は結合手法から検出を引いたもの＝単独最適化しない。\n\n"
        f"## 結果（best @epoch {best.get('epoch')}）\n"
        f"- accuracy={best['phase_accuracy']:.4f} / macro_f1={best['phase_macro_f1']:.4f}\n"
        f"- edit={best['phase_edit_score']:.2f} / seg_f1@10/25/50="
        f"{best['phase_seg_f1_10']:.2f}/{best['phase_seg_f1_25']:.2f}/{best['phase_seg_f1_50']:.2f}\n\n"
        f"## 構成\n- seed={args.seed} epochs={args.epochs} lr={args.lr} "
        f"stages={args.num_stages} layers={args.num_layers} f_maps={args.num_f_maps}\n"
        f"- server={server_name} / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)\n\n"
        f"## 次\n- Δ_phase =（結合手法 − この S4）。同一土台（凍結backbone/特徴/recipe/seed）で比較する。\n"
    )
    (exp_dir / "notes.md").write_text(note, encoding="utf-8")


def train(args) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    train_clips = load_clips("train")
    val_clips = load_clips("val")
    if args.smoke:
        train_clips, val_clips = train_clips[:3], val_clips[:2]
    print(f"[s4] train clips={len(train_clips)}  val clips={len(val_clips)}  "
          f"classes={len(CLASS_NAMES)}  device={device}")

    # 証跡（smoke 時は残さない。Δ 汚染防止）
    server_name = resolve_server_name(None)
    manager = exp_dir = None
    if not args.smoke and not args.no_evidence:
        manager = ExperimentManager(
            base_dir=str(PROJ / "experiments"), category="phase1",
            step="s4_phase_baseline", description=_desc(args), seed=args.seed,
        )
        manager.setup(_build_cfg(args, server_name, len(train_clips), len(val_clips)))
        exp_dir = manager.exp_dir
        print(f"[s4] evidence dir: {exp_dir}")

    tecno = TeCNO(num_stages=args.num_stages, num_layers=args.num_layers,
                  num_f_maps=args.num_f_maps, in_dim=2048, num_classes=len(CLASS_NAMES))
    # ②特徴レベル系統。3 系統:
    #   --neck-from <ckpt> : 検出で学習した C5 neck を凍結ロード → 片方向転送結合（S4″ 結合本体）
    #   --use-neck         : 工程側で fresh な C5 neck を学習 → 独立 neck 分母（S4′, 容量効果）
    #   どちらも無し        : 素の TeCNO（S4 base 分母）
    if args.neck_from:
        neck = _load_frozen_neck(args.neck_from)
        model = _NeckedTeCNO(neck, tecno).to(device)
        print(f"[s4″] 検出 C5 neck を凍結ロード（片方向転送結合）: {args.neck_from}")
    elif args.use_neck:
        model = _NeckedTeCNO(C5LinearNeck(dim=2048), tecno).to(device)
        print("[s4'] neck=C5LinearNeck(2048, residual, zero-init) 有効 → ②系統 S4′ 分母")
    else:
        model = tecno.to(device)
    # 凍結 neck（転送時）を optimizer から除外: AdamW の decoupled weight_decay が凍結重みを縮めるのを防ぐ。
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()

    from egosurgery.utils import tracking  # W&B 追跡（無認証なら no-op）
    tracking.init(f"{_desc(args)}_seed{args.seed}", group="S4", job_type="s4",
                  config={"seed": args.seed, "lr": args.lr, "epochs": args.epochs,
                          "use_neck": bool(args.use_neck or args.neck_from)})

    best = {"phase_accuracy": -1.0}
    for epoch in range(args.epochs):
        model.train()
        random.shuffle(train_clips)
        ep_loss = 0.0
        for clip_id, feats, labels in train_clips:
            x = torch.from_numpy(feats).T.unsqueeze(0).to(device)   # (1, 2048, T)
            y = torch.from_numpy(labels).to(device)                 # (T,)
            outs = model(x)
            loss = sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in outs)
            opt.zero_grad()
            loss.backward()
            opt.step()
            ep_loss += float(loss)
        val = evaluate(model, val_clips, device)
        print(f"[s4][epoch {epoch + 1}/{args.epochs}] loss={ep_loss / max(len(train_clips),1):.4f}  "
              f"val_acc={val['phase_accuracy']:.4f}  macroF1={val['phase_macro_f1']:.4f}  "
              f"edit={val['phase_edit_score']:.2f}  segF1@50={val['phase_seg_f1_50']:.2f}")
        tracking.log({"train/loss": ep_loss / max(len(train_clips), 1),
                      "val/phase_accuracy": val["phase_accuracy"], "val/macro_f1": val["phase_macro_f1"],
                      "val/jaccard": val["phase_jaccard"], "val/seg_f1_50": val["phase_seg_f1_50"]},
                     step=epoch)
        if val["phase_accuracy"] > best["phase_accuracy"]:
            best = {**val, "epoch": epoch + 1}
            if exp_dir is not None:
                torch.save({"tecno": model.state_dict(), "epoch": epoch + 1, "val": val},
                           exp_dir / "checkpoints" / "best_tecno.pth")
    print(f"[s4] best @epoch {best.get('epoch')}: acc={best['phase_accuracy']:.4f} "
          f"macroF1={best['phase_macro_f1']:.4f}")

    if manager is not None:
        per_class = best.get("phase_per_class_f1", {})
        scalars = {k: v for k, v in best.items() if isinstance(v, (int, float))}
        manager.log_eval_recipe(_build_phase_recipe(args, server_name))
        manager.log_metrics(scalars)
        manager.log_per_class_ap(per_class)
        _write_notes(exp_dir, args, best, server_name)
        print(f"[s4] evidence written -> {exp_dir}")
        # Notion 実験Run台帳へ自動投稿（NOTION_API_KEY 未設定なら no-op）。
        from egosurgery.utils.notion_logger import log_experiment_to_notion
        log_experiment_to_notion(
            exp_dir, status="completed", step="S4", tier="must",
            primary_metric="phase acc/macro-F1/jaccard/edit/seg-F1 (online_causal)",
            extra_result_text="工程単独分母（凍結 TeCNO）。Δ_phase の基準点")
    tracking.finish()
    return best


def parse_args():
    p = argparse.ArgumentParser(description="S4 TeCNO phase baseline (frozen features → causal MS-TCN).")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--num-stages", type=int, default=2)
    p.add_argument("--num-layers", type=int, default=8)
    p.add_argument("--num-f-maps", type=int, default=64)
    p.add_argument("--use-neck", action="store_true",
                   help="②特徴レベル系統の S4′: 共有 C5 線形 neck を TeCNO 前に挿入（neck版分母）")
    p.add_argument("--neck-from", type=str, default=None,
                   help="②結合 S4″: 検出で学習した C5 neck（c5_neck.weight/bias）を凍結ロードし TeCNO のみ学習")
    p.add_argument("--smoke", action="store_true", help="数 epoch・少 clip で疎通確認（証跡なし）")
    p.add_argument("--no-evidence", action="store_true", help="証跡を残さない（配線検証用）")
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    if a.smoke:
        a.epochs = 3
    train(a)

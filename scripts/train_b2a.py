#!/usr/bin/env python
"""B2a 片方向結合（検出→工程・Tier-0 必須・①信号レベル系統）= Δ_phase を測る結合本体。

比較の三角形（凍結源 Relation-DETR seed42）で、**凍結検出器の予測 tool-presence 信号**（15-d,
クラス別最大スコア∈[0,1]）を工程枝に **入力連結** する片方向結合。②（B1, 共有 C5 neck で勾配交差）
と違い、①は **勾配を交差させず信号だけを渡す**。よって土台（分母）は S4 base（素 TeCNO・neck 無し）で、
**変える軸は「tool-presence 信号を見せるか否か」の 1 点のみ**:

    入力 = concat([ GAP(C5) 2048-d , tool_presence 15-d ]) = 2063-d  → 素の causal TeCNO

Δ_phase = (B2a − S4 base 0.8986±0.0034)。+15ch の容量増は「測りたい結合そのもの」なので交絡ではない。

入力:
    data/processed/stage1_features/<frozen_src>/{train,val,test}_gap.npz（frame_ids, features=GAP2048）
    data/processed/b2a_detsignal/<frozen_src>/{train,val,test}_toolpresence.npz（frame_ids, signal=15-d）
    data/processed/phase_manifest/{train,val,test}.json（clip 時系列順 + label）

本体 .venv で実行（Relation-DETR 非依存・キャッシュのみ読む。S4 と同一の作法・ハイパー）:
  .venv/bin/python scripts/train_b2a.py --epochs 50 --seed 42
  .venv/bin/python scripts/train_b2a.py --smoke      # 数 epoch・少 clip で疎通確認（証跡なし）
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

import os  # noqa: E402  frozen-src の env 上書き用（改善検出器の特徴で probe するため）

FROZEN_SRC = os.environ.get("RELDETR_FROZEN_TAG", "relation_detr_seed42")
GAP_DIR = PROJ / "data" / "processed" / "stage1_features" / FROZEN_SRC
SIGNAL_DIR = PROJ / "data" / "processed" / "b2a_detsignal" / FROZEN_SRC
ORACLE_SIGNAL_DIR = PROJ / "data" / "processed" / "oracle_toolpresence"  # §18.4 L2-3
MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())
NUM_TOOLS = 15
IN_DIM = 2048 + NUM_TOOLS  # 2063


def load_clips(
    split: str,
    tool_source: str = "pred",
    mask_tool_dim: int | list[int] | None = None,
    drop_gap: bool = False,
    noise_rate: float = 0.0,
    noise_seed: int = 0,
    noise_dims: list[int] | None = None,
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """(clip_id, feats (T,2063)=GAP2048⊕tool15, labels (T,)) のリストを返す（時系列順）。

    GAP・tool-presence いずれも frame_id でキー化して clip フレーム順に整列・連結する。
    どちらかに無い frame があれば整合不良として Fail Loud（KeyError）— ダミー補完しない。

    `tool_source` (§18.4 L2-3):
      - "pred": 凍結検出器の予測 tool-presence（既定・B2a base）
      - "oracle": GT bbox から作った one-hot 15-d（注入の上限を測る・oracle-tool-presence）
    """
    g = np.load(GAP_DIR / f"{split}_gap.npz")
    gap_all = g["features"]  # NpzFile は遅延展開: 一度だけ取り出す
    feat_by_frame = {str(fid): gap_all[i] for i, fid in enumerate(g["frame_ids"])}

    if tool_source == "oracle":
        s = np.load(ORACLE_SIGNAL_DIR / f"{split}_oracletool.npz")
    else:
        s = np.load(SIGNAL_DIR / f"{split}_toolpresence.npz")
    sig_all = s["signal"]
    sig_by_frame = {str(fid): sig_all[i] for i, fid in enumerate(s["frame_ids"])}

    # §18.4 L2-4: 指定 dim を mask（0 埋め）して per-dim 寄与を測定
    # 単一 int / int リスト 両対応（複数 dim 同時 mask 用）
    mask_dims: list[int] = []
    if mask_tool_dim is not None:
        if isinstance(mask_tool_dim, int):
            mask_dims = [mask_tool_dim] if 0 <= mask_tool_dim < NUM_TOOLS else []
        else:
            mask_dims = [d for d in mask_tool_dim if 0 <= d < NUM_TOOLS]
    if mask_dims:
        for fid in sig_by_frame:
            sig_by_frame[fid] = sig_by_frame[fid].copy()
            for d in mask_dims:
                sig_by_frame[fid][d] = 0.0

    # 検出器精度 → phase acc transfer function 推定:
    # 各 (frame, dim) を確率 noise_rate で flip (0↔1)。oracle 信号への一様 noise 注入で、
    # 「現実的検出器精度 (1-noise_rate)」の simulated 検出器が出す入力を作る。
    # split + noise_seed で独立な RandomState を使い再現性を保つ。
    if noise_rate > 0.0:
        # split ごとに独立 seed（train/val/test で違う noise を引く）
        split_offset = {"train": 0, "val": 1, "test": 2}.get(split, 3)
        rng = np.random.RandomState(noise_seed * 100 + split_offset)
        # noise_dims が指定されたらその dim のみ flip、None なら全 15 dim
        target_dims = noise_dims if noise_dims else list(range(NUM_TOOLS))
        for fid in sig_by_frame:
            v = sig_by_frame[fid].copy()
            for d in target_dims:
                if 0 <= d < NUM_TOOLS and rng.uniform(0.0, 1.0) < noise_rate:
                    v[d] = 1.0 - v[d]
            sig_by_frame[fid] = v

    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        frames = clip["frames"]
        rows = []
        for fr in frames:
            fid = fr["frame"]
            if fid not in feat_by_frame:
                raise KeyError(f"[b2a] GAP 特徴に frame_id 欠落: {fid} ({split})")
            if fid not in sig_by_frame:
                raise KeyError(f"[b2a] tool-presence 信号に frame_id 欠落: {fid} ({split})")
            if drop_gap:
                rows.append(sig_by_frame[fid])  # tool-pres only (15d)
            else:
                rows.append(np.concatenate([feat_by_frame[fid], sig_by_frame[fid]]))  # 2048+15
        feats = np.stack(rows).astype(np.float32)                       # (T, 2063)
        labels = np.asarray([fr["label"] for fr in frames], dtype=np.int64)
        clips.append((clip["clip_id"], feats, labels))
    return clips


def smoothing_loss(logits: torch.Tensor) -> torch.Tensor:
    """MS-TCN の T-MSE 平滑化損失（S4/B1 と同一定義）。"""
    ls = F.log_softmax(logits, dim=1)
    mse = F.mse_loss(ls[:, :, 1:], ls[:, :, :-1], reduction="none")
    return torch.clamp(mse, max=16.0).mean()


@torch.no_grad()
def evaluate(model: nn.Module, clips, device) -> dict:
    model.eval()
    metrics = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    for clip_id, feats, labels in clips:
        x = torch.from_numpy(feats).T.unsqueeze(0).to(device)  # (1, 2063, T)
        logits = model(x)[-1]                                   # 最終ステージ (1, C, T)
        preds = logits[0].argmax(0).cpu().numpy()
        metrics.update(preds, labels, video_id=clip_id)
    return metrics.compute()


DESC = "b2a_det2phase_toolpresence"
DESC_ORACLE = "b2a_det2phase_oracletool"  # §18.4 L2-3 用


def _build_cfg(args, server_name: str, n_train: int, n_val: int) -> dict:
    """ExperimentManager.save_config に渡す resolved config（再現用）。"""
    return {
        "experiment": {"category": "transfer", "step": "b2a_det2phase", "description": DESC},
        "seed": args.seed,
        "frozen_source": {"detector": "relation_detr", "seed": 42, "backbone": "resnet50",
                          "gap_cache": str(GAP_DIR.relative_to(PROJ)),
                          "tool_signal_cache": str(SIGNAL_DIR.relative_to(PROJ))},
        "method": {"name": "b2a_det_to_phase", "system": "①signal_level", "direction": "det->phase",
                   "coupling": "toolpresence_concat", "tool_signal_dim": NUM_TOOLS,
                   "neck": None, "grad_crossing": False},
        "model": {"temporal_head": "tecno", "num_stages": args.num_stages,
                  "num_layers": args.num_layers, "num_f_maps": args.num_f_maps,
                  "in_dim": IN_DIM, "num_phases": len(CLASS_NAMES), "causal": True},
        "train": {"epochs": args.epochs, "lr": args.lr, "weight_decay": args.weight_decay,
                  "freeze_backbone": True, "smoothing_weight": 0.15},
        "data": {"n_train_clips": n_train, "n_val_clips": n_val},
        "delta": {"phase_denominator": "s4_phase_baseline (frozen_tecno_phase_baseline)",
                  "note": "Δ_phase = (B2a − S4 base). 土台は素 TeCNO・neck 無しで一致、変える軸は tool 信号 1 点。"},
        "server_name": server_name,
    }


def _build_phase_recipe(args, server_name: str) -> dict:
    """工程 eval_recipe（PHASE_EVAL_PROTOCOL をマージ）。recipes_match の保護対象。

    B2a の入力は 2063-d（GAP2048⊕tool15）。S4 base（2048）と recipe を厳密一致させる必要はないが、
    結合の素性（coupling/tool_signal_dim）を test_cfg に明記し、Δ 集計時に系統を振り分けられるようにする。
    """
    test_cfg = {
        "task": "phase",
        **PHASE_EVAL_PROTOCOL,  # inference_protocol=online_causal / jaccard_mode=strict
        "backbone": "relation_detr_resnet50_frozen_seed42",
        "temporal_head": "tecno",
        "num_stages": args.num_stages,
        "num_layers": args.num_layers,
        "num_f_maps": args.num_f_maps,
        "in_dim": IN_DIM,
        "coupling": "b2a_det_to_phase_toolpresence",
        "tool_signal_dim": NUM_TOOLS,
    }
    return build_eval_recipe(
        test_cfg=test_cfg, split_sizes=PAPER_SPLIT_SIZES, server_name=server_name,
        gpu_count=1, effective_batch_size=1, lr_scaling="none",
    )


def _write_notes(exp_dir: Path, args, best: dict, server_name: str) -> None:
    note = (
        f"# B2a 片方向結合 検出→工程（Tier-0 必須・①信号レベル）\n\n"
        f"凍結 Relation-DETR seed42 の tool-presence 信号（15-d）を GAP(2048) に入力連結 → 素 causal TeCNO。\n"
        f"①は勾配を交差させず信号のみ渡す（②B1 と対比）。online/causal（未来不使用）。\n\n"
        f"## 結果（best @epoch {best.get('epoch')}）\n"
        f"- accuracy={best['phase_accuracy']:.4f} / macro_f1={best['phase_macro_f1']:.4f}\n"
        f"- edit={best['phase_edit_score']:.2f} / seg_f1@10/25/50="
        f"{best['phase_seg_f1_10']:.2f}/{best['phase_seg_f1_25']:.2f}/{best['phase_seg_f1_50']:.2f}\n\n"
        f"## 構成\n- seed={args.seed} epochs={args.epochs} lr={args.lr} "
        f"in_dim={IN_DIM}(=2048+{NUM_TOOLS}) stages={args.num_stages} layers={args.num_layers} "
        f"f_maps={args.num_f_maps}\n"
        f"- server={server_name} / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)\n\n"
        f"## Δ\n- Δ_phase = (B2a − S4 base 0.8986±0.0034)。同一土台（凍結backbone/GAP/recipe/seed・neck無し）。\n"
        f"- 3-seed 揃ったら paired-σ(対seed差) で §10.1 判定（|Δ|>paired-σ かつ同符号で有意）。\n"
    )
    (exp_dir / "notes.md").write_text(note, encoding="utf-8")


def train(args) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    # --mask-tool-dims (複数) > --mask-tool-dim (単一)
    if args.mask_tool_dims:
        mask_dims = [int(x) for x in args.mask_tool_dims.split(",")]
    else:
        mask_dims = args.mask_tool_dim
    noise_dims_list = None
    if args.tool_noise_dims:
        noise_dims_list = [int(x) for x in args.tool_noise_dims.split(",")]
    train_clips = load_clips(
        "train",
        tool_source=args.tool_source,
        mask_tool_dim=mask_dims,
        drop_gap=args.drop_gap,
        noise_rate=args.tool_noise_rate,
        noise_seed=args.seed,
        noise_dims=noise_dims_list,
    )
    val_clips = load_clips(
        "val",
        tool_source=args.tool_source,
        mask_tool_dim=mask_dims,
        drop_gap=args.drop_gap,
        noise_rate=args.tool_noise_rate,
        noise_seed=args.seed,
        noise_dims=noise_dims_list,
    )
    if args.smoke:
        train_clips, val_clips = train_clips[:3], val_clips[:2]
    print(f"[b2a] train clips={len(train_clips)}  val clips={len(val_clips)}  "
          f"in_dim={IN_DIM}  tool_source={args.tool_source}  classes={len(CLASS_NAMES)}  device={device}")

    server_name = resolve_server_name(None)
    manager = exp_dir = None
    desc = args.description_override or (
        DESC_ORACLE if args.tool_source == "oracle" else DESC
    )
    if not args.smoke and not args.no_evidence:
        manager = ExperimentManager(
            base_dir=str(PROJ / "experiments"), category="transfer",
            step=desc, description=desc, seed=args.seed,
        )
        manager.setup(_build_cfg(args, server_name, len(train_clips), len(val_clips)))
        exp_dir = manager.exp_dir
        print(f"[b2a] evidence dir: {exp_dir}")

    # ①信号レベル: neck 無し・素の TeCNO に 2063-d を入力（drop_gap で 15-d のみ）
    effective_in_dim = NUM_TOOLS if args.drop_gap else IN_DIM
    model = TeCNO(num_stages=args.num_stages, num_layers=args.num_layers,
                  num_f_maps=args.num_f_maps, in_dim=effective_in_dim,
                  num_classes=len(CLASS_NAMES)).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()

    from egosurgery.utils import tracking  # W&B 追跡（無認証なら no-op）
    tracking.init(f"b2a_det2phase_seed{args.seed}", group="B", job_type="b2a",
                  config={"seed": args.seed, "lr": args.lr, "epochs": args.epochs, "in_dim": 2063,
                          "method": "b2a_det_to_phase_toolpresence"})

    best = {"phase_accuracy": -1.0}
    for epoch in range(args.epochs):
        model.train()
        random.shuffle(train_clips)
        ep_loss = 0.0
        for clip_id, feats, labels in train_clips:
            x = torch.from_numpy(feats).T.unsqueeze(0).to(device)   # (1, 2063, T)
            y = torch.from_numpy(labels).to(device)                 # (T,)
            outs = model(x)
            loss = sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in outs)
            opt.zero_grad()
            loss.backward()
            opt.step()
            ep_loss += float(loss)
        val = evaluate(model, val_clips, device)
        print(f"[b2a][epoch {epoch + 1}/{args.epochs}] loss={ep_loss / max(len(train_clips),1):.4f}  "
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
    print(f"[b2a] best @epoch {best.get('epoch')}: acc={best['phase_accuracy']:.4f} "
          f"macroF1={best['phase_macro_f1']:.4f}")

    if manager is not None:
        per_class = best.get("phase_per_class_f1", {})
        scalars = {k: v for k, v in best.items() if isinstance(v, (int, float))}
        manager.log_eval_recipe(_build_phase_recipe(args, server_name))
        manager.log_metrics(scalars)
        manager.log_per_class_ap(per_class)
        _write_notes(exp_dir, args, best, server_name)
        print(f"[b2a] evidence written -> {exp_dir}")
        # Notion 実験Run台帳へ自動投稿（NOTION_API_KEY/NOTION_DB_ID 未設定なら no-op）。
        from egosurgery.utils.notion_logger import log_experiment_to_notion
        log_experiment_to_notion(
            exp_dir, status="completed", step="B", tier="must",
            primary_metric="phase acc/macro-F1/jaccard/edit/seg-F1 (online_causal, jaccard strict)",
            extra_result_text="①信号 det→phase。Δ_phase vs S4 base 0.8986±0.0034")
    tracking.finish()
    return best


def parse_args():
    p = argparse.ArgumentParser(
        description="B2a det->phase coupling (frozen tool-presence signal ⊕ GAP → causal TeCNO).")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument(
        "--tool-source",
        choices=["pred", "oracle"],
        default="pred",
        help="§18.4 L2-3: tool-presence のソース。pred=凍結検出器予測（既定・B2a base）/ "
        "oracle=GT bbox からの one-hot（B2a の上限を測定）",
    )
    p.add_argument(
        "--mask-tool-dim",
        type=int,
        default=None,
        help="§18.4 L2-4: 指定 dim (0-14) の tool-presence を 0 mask して per-dim 寄与を測定。"
        "None なら mask なし。",
    )
    p.add_argument(
        "--mask-tool-dims",
        type=str,
        default=None,
        help="複数 dim を同時 mask（カンマ区切り、例 '0,6,9' で Top3 三同時 mask）",
    )
    p.add_argument(
        "--description-override",
        type=str,
        default=None,
        help="ExperimentManager の step/description を上書き（L2-4 で b2a_mask_dim_<k> のため）",
    )
    p.add_argument(
        "--drop-gap",
        action="store_true",
        help="GAP 2048d を削除して tool-presence 15d のみを入力（B2a-RegionOnly）",
    )
    p.add_argument(
        "--tool-noise-rate",
        type=float,
        default=0.0,
        help="oracle tool-pres の各 (frame,dim) を確率 p で flip（検出器精度シミュレーション・"
             "1-p=実効精度）。p=0 で oracle そのまま、p=0.1 で 90%% 精度の検出器に相当。",
    )
    p.add_argument(
        "--tool-noise-dims",
        type=str,
        default=None,
        help="--tool-noise-rate を適用する dim をカンマ区切りで指定（例 '0,6,9' で Top3 限定 noise）。"
             "None なら全 15 dim に均一 noise。",
    )
    p.add_argument("--num-stages", type=int, default=2)
    p.add_argument("--num-layers", type=int, default=8)
    p.add_argument("--num-f-maps", type=int, default=64)
    p.add_argument("--smoke", action="store_true", help="数 epoch・少 clip で疎通確認（証跡なし）")
    p.add_argument("--no-evidence", action="store_true", help="証跡を残さない（配線検証用）")
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    if a.smoke:
        a.epochs = 3
    train(a)

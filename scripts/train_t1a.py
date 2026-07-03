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

import os  # noqa: E402  frozen-src の env 上書き用（改善検出器の特徴で probe するため）

FROZEN_SRC = os.environ.get("RELDETR_FROZEN_TAG", "relation_detr_seed42")
GAP_DIR = PROJ / "data" / "processed" / "stage1_features" / FROZEN_SRC
REGION_DIR = PROJ / "data" / "processed" / "t1a_regiontoken" / FROZEN_SRC
TOOLPRES_DIR = PROJ / "data" / "processed" / "b2a_detsignal" / FROZEN_SRC  # combined pred 用
ORACLE_TOOL_DIR = PROJ / "data" / "processed" / "oracle_toolpresence"  # combined oracle 用
MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())
GAP_DIM = 2048
REGION_DIM = 15 * 256  # 3840
TOOLPRES_DIM = 15  # combined 用 B2a tool-presence dim


def load_clips(
    split: str,
    region_only: bool,
    shuffle_region: bool = False,
    shuffle_seed: int = 12345,
    add_toolpresence: bool = False,
    toolpresence_source: str = "pred",
    mask_region_tool_dim: int | list[int] | None = None,
    tool_noise_rate: float = 0.0,
    tool_noise_dims: list[int] | None = None,
    tool_noise_seed: int = 0,
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """(clip_id, feats, labels) を返す。feats = region(3840) or [GAP2048 ⊕ region3840](5888)。

    GAP・region いずれも frame_id でキー化して clip フレーム順に整列・連結する。
    どちらかに無い frame があれば整合不良として Fail Loud（KeyError）— ダミー補完しない。

    `shuffle_region=True` (§18.4 L2-2 shuffle control): region-token を frame 対応を
    破壊するように全体 shuffle して assign。phase と region の真の相関が破壊されるため、
    T1a の Δ_phase が消えれば「region 情報が真に寄与している」ことの positive control 反証。
    splits 間で独立した RandomState を使い再現性を保つ。
    """
    g = np.load(GAP_DIR / f"{split}_gap.npz")
    gap_all = g["features"]  # NpzFile 遅延展開: 一度だけ取り出す
    gap_by_frame = {str(fid): gap_all[i] for i, fid in enumerate(g["frame_ids"])}

    r = np.load(REGION_DIR / f"{split}_regiontoken.npz")
    reg_all = r["region"]
    reg_by_frame = {str(fid): reg_all[i] for i, fid in enumerate(r["frame_ids"])}

    if shuffle_region:
        # shuffle: region の frame 対応を完全に破壊（同 split 内で per-frame ベクトルを shuffle）
        rng = np.random.RandomState(shuffle_seed)
        keys = list(reg_by_frame.keys())
        values = list(reg_by_frame.values())
        rng.shuffle(values)
        reg_by_frame = dict(zip(keys, values, strict=False))

    # §18.4 L2-4 (T1a 版): region-token の特定 tool slot (15 × 256) を 0 mask
    # 単一 int / list 両対応
    mask_slots: list[int] = []
    if mask_region_tool_dim is not None:
        if isinstance(mask_region_tool_dim, int):
            mask_slots = [mask_region_tool_dim] if 0 <= mask_region_tool_dim < 15 else []
        else:
            mask_slots = [d for d in mask_region_tool_dim if 0 <= d < 15]
    if mask_slots:
        for fid in reg_by_frame:
            v = reg_by_frame[fid].copy()
            for slot in mask_slots:
                v[slot * 256:(slot + 1) * 256] = 0.0
            reg_by_frame[fid] = v

    # B2a+T1a combined: tool-presence(15d) も追加で連結（pred or oracle）
    tool_by_frame: dict = {}
    if add_toolpresence:
        if toolpresence_source == "oracle":
            t = np.load(ORACLE_TOOL_DIR / f"{split}_oracletool.npz")
        else:
            t = np.load(TOOLPRES_DIR / f"{split}_toolpresence.npz")
        tp_all = t["signal"]
        tool_by_frame = {str(fid): tp_all[i] for i, fid in enumerate(t["frame_ids"])}

        # tool-pres に noise injection（検出器精度シミュレーション）
        if tool_noise_rate > 0.0:
            split_offset = {"train": 0, "val": 1, "test": 2}.get(split, 3)
            rng = np.random.RandomState(tool_noise_seed * 100 + split_offset)
            target_dims = tool_noise_dims if tool_noise_dims else list(range(15))
            for fid in tool_by_frame:
                v = tool_by_frame[fid].copy()
                for d in target_dims:
                    if 0 <= d < 15 and rng.uniform(0.0, 1.0) < tool_noise_rate:
                        v[d] = 1.0 - v[d]
                tool_by_frame[fid] = v

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
                parts = [gap_by_frame[fid], reg_by_frame[fid]]
                if add_toolpresence:
                    if fid not in tool_by_frame:
                        raise KeyError(f"[t1a] tool-presence に frame_id 欠落: {fid} ({split})")
                    parts.append(tool_by_frame[fid])
                rows.append(np.concatenate(parts))  # 2048+3840 (+15)
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
        "experiment": {
            "category": "transfer",
            "step": args.description,
            "description": args.description,
        },
        "seed": args.seed,
        "frozen_source": {
            "detector": "relation_detr",
            "seed": 42,
            "backbone": "resnet50",
            "gap_cache": str(GAP_DIR.relative_to(PROJ)),
            "region_cache": str(REGION_DIR.relative_to(PROJ)),
        },
        "method": {
            "name": "t1a_region_to_phase",
            "system": "②feature_level/object-token",
            "ref": "TAPIS/GraSP (MedIA 2025)",
            "direction": "det->phase",
            "coupling": (
                "regiontoken_only" if args.region_only else "regiontoken_concat_gap"
            ),
            "region_repr": "per_class_256d_score_weighted",
            "region_dim": REGION_DIM,
            "neck": None,
            "grad_crossing": False,
        },
        "model": {
            "temporal_head": "tecno",
            "num_stages": args.num_stages,
            "num_layers": args.num_layers,
            "num_f_maps": args.num_f_maps,
            "in_dim": in_dim,
            "num_phases": len(CLASS_NAMES),
            "causal": True,
        },
        "train": {
            "epochs": args.epochs,
            "lr": args.lr,
            "weight_decay": args.weight_decay,
            "freeze_backbone": True,
            "smoothing_weight": 0.15,
        },
        "data": {"n_train_clips": n_train, "n_val_clips": n_val},
        "delta": {
            "phase_denominator": "s4_phase_baseline (frozen_tecno_phase_baseline)",
            "denominator_value_lecun": "0.8986±0.0034",
            "note": "Δ_phase = (T1a − S4 base). 別サーバー実行時は lecun 分母を流用し "
            "サーバー差を §8.0 明文化（同一 ckpt・同一前処理ゆえ差は TeCNO 学習数値のみ）。",
        },
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
        "coupling": (
            "t1a_regiontoken_only" if args.region_only else "t1a_regiontoken_concat_gap"
        ),
        "region_dim": REGION_DIM,
    }
    return build_eval_recipe(
        test_cfg=test_cfg,
        split_sizes=PAPER_SPLIT_SIZES,
        server_name=server_name,
        gpu_count=1,
        effective_batch_size=1,
        lr_scaling="none",
    )


def _write_notes(
    exp_dir: Path, args, best: dict, server_name: str, in_dim: int
) -> None:
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

    if args.region_only:
        in_dim = REGION_DIM
    else:
        in_dim = GAP_DIM + REGION_DIM + (TOOLPRES_DIM if args.add_toolpresence else 0)
    # --mask-region-tool-dims (複数) > --mask-region-tool-dim (単一)
    if args.mask_region_tool_dims:
        mask_slots = [int(x) for x in args.mask_region_tool_dims.split(",")]
    else:
        mask_slots = args.mask_region_tool_dim
    tool_noise_dims = None
    if args.tool_noise_dims:
        tool_noise_dims = [int(x) for x in args.tool_noise_dims.split(",")]
    train_clips = load_clips(
        "train",
        args.region_only,
        shuffle_region=args.region_shuffle,
        shuffle_seed=args.shuffle_seed,
        add_toolpresence=args.add_toolpresence,
        toolpresence_source=args.toolpresence_source,
        mask_region_tool_dim=mask_slots,
        tool_noise_rate=args.tool_noise_rate,
        tool_noise_dims=tool_noise_dims,
        tool_noise_seed=args.seed,
    )
    val_clips = load_clips(
        "val",
        args.region_only,
        shuffle_region=args.region_shuffle,
        shuffle_seed=args.shuffle_seed + 1,  # split 独立 seed
        add_toolpresence=args.add_toolpresence,
        toolpresence_source=args.toolpresence_source,
        mask_region_tool_dim=mask_slots,
        tool_noise_rate=args.tool_noise_rate,
        tool_noise_dims=tool_noise_dims,
        tool_noise_seed=args.seed,
    )
    if args.smoke:
        train_clips, val_clips = train_clips[:3], val_clips[:2]
    print(
        f"[t1a] train clips={len(train_clips)}  val clips={len(val_clips)}  "
        f"in_dim={in_dim}  region_only={args.region_only}  classes={len(CLASS_NAMES)}  device={device}"
    )

    server_name = resolve_server_name(None)
    manager = exp_dir = None
    if not args.smoke and not args.no_evidence:
        manager = ExperimentManager(
            base_dir=str(PROJ / "experiments"),
            category="transfer",
            step=args.description,
            description=args.description,
            seed=args.seed,
        )
        manager.setup(
            _build_cfg(args, server_name, in_dim, len(train_clips), len(val_clips))
        )
        exp_dir = manager.exp_dir
        print(f"[t1a] evidence dir: {exp_dir}")

    model = TeCNO(
        num_stages=args.num_stages,
        num_layers=args.num_layers,
        num_f_maps=args.num_f_maps,
        in_dim=in_dim,
        num_classes=len(CLASS_NAMES),
    ).to(device)
    opt = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=args.weight_decay
    )
    ce = nn.CrossEntropyLoss()

    from egosurgery.utils import tracking  # W&B 追跡（無認証なら no-op）

    tracking.init(
        f"{args.description}_seed{args.seed}",
        group="B",
        job_type="t1a",
        config={
            "seed": args.seed,
            "lr": args.lr,
            "epochs": args.epochs,
            "in_dim": in_dim,
            "region_only": args.region_only,
            "method": "t1a_region_to_phase",
        },
    )

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
        print(
            f"[t1a][epoch {epoch + 1}/{args.epochs}] loss={ep_loss / max(len(train_clips),1):.4f}  "
            f"val_acc={val['phase_accuracy']:.4f}  macroF1={val['phase_macro_f1']:.4f}  "
            f"edit={val['phase_edit_score']:.2f}  segF1@50={val['phase_seg_f1_50']:.2f}"
        )
        tracking.log(
            {
                "train/loss": ep_loss / max(len(train_clips), 1),
                "val/phase_accuracy": val["phase_accuracy"],
                "val/macro_f1": val["phase_macro_f1"],
                "val/jaccard": val["phase_jaccard"],
                "val/seg_f1_50": val["phase_seg_f1_50"],
            },
            step=epoch,
        )
        if val["phase_accuracy"] > best["phase_accuracy"]:
            best = {**val, "epoch": epoch + 1}
            if exp_dir is not None:
                torch.save(
                    {"tecno": model.state_dict(), "epoch": epoch + 1, "val": val},
                    exp_dir / "checkpoints" / "best_tecno.pth",
                )
    print(
        f"[t1a] best @epoch {best.get('epoch')}: acc={best['phase_accuracy']:.4f} "
        f"macroF1={best['phase_macro_f1']:.4f}"
    )

    if manager is not None:
        per_class = best.get("phase_per_class_f1", {})
        scalars = {k: v for k, v in best.items() if isinstance(v, (int, float))}
        manager.log_eval_recipe(_build_phase_recipe(args, server_name, in_dim))
        manager.log_metrics(scalars)
        manager.log_per_class_ap(per_class)
        _write_notes(exp_dir, args, best, server_name, in_dim)
        print(f"[t1a] evidence written -> {exp_dir}")
        # Notion 実験Run台帳へ自動投稿（ResearchLogger ファサード経由・冪等・fail-open）。
        # 2026-06-26: 直接呼び出しを ResearchLogger に統一して二重化を解消。
        from egosurgery.utils.research_logger import ResearchLogger

        ResearchLogger(cfg=None, manager=manager).log_run(
            status="completed",
            step="B",
            tier="must",
            primary_metric="phase acc/macro-F1/jaccard/edit/seg-F1 (online_causal)",
            extra_result_text="②object-token det→phase。Δ_phase vs S4 base 0.8986（within-server）",
        )
    tracking.finish()
    return best


def parse_args():
    p = argparse.ArgumentParser(
        description="T1a region-token→phase coupling (frozen object-query embeddings ⊕ GAP → causal TeCNO)."
    )
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--num-stages", type=int, default=2)
    p.add_argument("--num-layers", type=int, default=8)
    p.add_argument("--num-f-maps", type=int, default=64)
    p.add_argument(
        "--region-only",
        action="store_true",
        help="GAP と連結せず region token のみを入力（replace 版・別解）",
    )
    p.add_argument(
        "--region-shuffle",
        action="store_true",
        help="§18.4 L2-2 shuffle control: region-token の frame 対応を破壊して入力。"
        "T1a の Δ_phase が消えれば region 情報の真の寄与を実証する positive control 反証。",
    )
    p.add_argument(
        "--shuffle-seed",
        type=int,
        default=12345,
        help="--region-shuffle 時の shuffle seed（再現性のため固定）",
    )
    p.add_argument(
        "--add-toolpresence",
        action="store_true",
        help="B2a tool-presence (15d) も追加で連結（B2a+T1a combined・in_dim=5903）",
    )
    p.add_argument(
        "--toolpresence-source",
        choices=["pred", "oracle"],
        default="pred",
        help="--add-toolpresence 時のソース。pred=凍結検出器予測 / oracle=GT one-hot",
    )
    p.add_argument(
        "--mask-region-tool-dim",
        type=int,
        default=None,
        help="region-token の指定 tool slot (0-14) × 256d を 0 mask（T1a per-tool ablation）",
    )
    p.add_argument(
        "--mask-region-tool-dims",
        type=str,
        default=None,
        help="複数 slot を同時 mask（カンマ区切り、例 '0,6,9' で Top3 同時）",
    )
    p.add_argument(
        "--tool-noise-rate",
        type=float,
        default=0.0,
        help="--add-toolpresence の oracle tool-pres を確率 p で flip（B2a と同じ）",
    )
    p.add_argument(
        "--tool-noise-dims",
        type=str,
        default=None,
        help="--tool-noise-rate を適用する dim をカンマ区切り（例 '0,6,9' で Top3 限定）",
    )
    p.add_argument(
        "--smoke", action="store_true", help="数 epoch・少 clip で疎通確認（証跡なし）"
    )
    p.add_argument(
        "--no-evidence", action="store_true", help="証跡を残さない（配線検証用）"
    )
    p.add_argument(
        "--description",
        type=str,
        default=DESC,
        help="ExperimentManager の step/description に使う識別子。T1a-Deep など派生実験を"
        "別 step に分けるために上書き可（既定: t1a_regiontoken）",
    )
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    if a.smoke:
        a.epochs = 3
    train(a)

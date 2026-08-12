#!/usr/bin/env python
"""STEP D-aux 系統① 手情報→工程（det→phase・①信号レベル）= Δ_phase を測る結合本体。

`train_b2a.py`（tool-presence 15-d ⊕ GAP → 素 causal TeCNO）の **手版**。凍結検出器の
GAP(2048) に **手由来の特徴**を入力連結し、工程認識（TeCNO）へ片方向注入する。②（勾配交差）
と違い①は信号のみ渡す。土台（分母）= S4 base（素 TeCNO on GAP = 0.8986±0.0034）で固定し、
**変える軸は「どの手特徴を見せるか」の 1 点**（+手特徴の容量増は測りたい結合そのもの）。

    入力 = concat([ GAP 2048 , hand_feature D ( , tool 15 ) ]) = (2048 + D + [15])  → 素 causal TeCNO

手法（§2.2）:
  H-1 presence  (D=4)   own/other×L/R の存在 one-hot
  H-2 count     (D=4)   各手クラスの検出個数
  H-3 geom      (D=16)  各手 [cx,cy,w,h]（画像正規化）
  H-5 own_other (D=16)  geom を own(0-7)/other(8-15) の 2 ブロックに分離し別枝で符号化して注入
  H-6 with-tool         上記に tool-presence 15-d を併用（--with-tool、手が tool に上乗せか冗長か）
  H-4 region-token      手検出器の RoI 特徴（非-oracle。S2-hand 完成後・本 script の scope 外）

入力キャッシュ:
  data/processed/stage1_features/<frozen_src>/{split}_gap.npz            （GAP 2048・既存）
  data/processed/oracle_handfeature/{split}_oraclehand_{type}.npz        （oracle 手特徴・build_oracle_handfeature.py）
  data/processed/haux_detsignal/<hand_src>/{split}_hand_{type}.npz       （pred 手特徴・S2-hand 検出器の予測。非-oracle）
  data/processed/oracle_toolpresence/{split}_oracletool.npz              （H-6 の tool oracle）
  data/processed/b2a_detsignal/<frozen_src>/{split}_toolpresence.npz     （H-6 の tool pred）
  data/processed/phase_manifest/{split}.json                             （clip 時系列順 + label）

本体 .venv で実行（Relation-DETR 非依存・キャッシュのみ読む。S4 と同一の作法・ハイパー）:
  .venv/bin/python scripts/train_haux.py --hand-feature-type presence --hand-source oracle --seed 42
  .venv/bin/python scripts/train_haux.py --hand-feature-type presence --hand-source oracle --with-tool --tool-source oracle  # H-6
  .venv/bin/python scripts/train_haux.py --hand-feature-type presence --hand-source oracle --shuffle-hand  # §4.3 shuffle control
  .venv/bin/python scripts/train_haux.py --smoke  # 数 epoch・少 clip で疎通確認（証跡なし）
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
ORACLE_HAND_DIR = PROJ / "data" / "processed" / "oracle_handfeature"
PRED_HAND_DIR = PROJ / "data" / "processed" / "haux_detsignal"  # /<hand_src>/{split}_hand_{type}.npz
ORACLE_TOOL_DIR = PROJ / "data" / "processed" / "oracle_toolpresence"
PRED_TOOL_DIR = PROJ / "data" / "processed" / "b2a_detsignal" / FROZEN_SRC
MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())

GAP_DIM = 2048
NUM_TOOLS = 15
# 手特徴タイプ → 次元数（build_oracle_handfeature.py と一致させること）
HAND_FEATURE_DIM = {"presence": 4, "count": 4, "geom": 16, "own_other": 16}


def _hand_npz_path(split: str, ftype: str, source: str, hand_src: str) -> Path:
    # own_other は geom npz を読み、注入時に own/other ブロックへ分割する
    disk_type = "geom" if ftype == "own_other" else ftype
    if source == "oracle":
        return ORACLE_HAND_DIR / f"{split}_oraclehand_{disk_type}.npz"
    return PRED_HAND_DIR / hand_src / f"{split}_hand_{disk_type}.npz"


def load_clips(
    split: str,
    hand_feature_type: str,
    hand_source: str,
    hand_src: str,
    with_tool: bool,
    tool_source: str,
    drop_gap: bool,
    shuffle_hand: bool = False,
    shuffle_seed: int = 12345,
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """(clip_id, feats (T, D), labels (T,)) のリストを返す（時系列順）。

    GAP・手特徴（・tool）を frame_id でキー化して clip フレーム順に整列・連結する。
    どれかに無い frame があれば整合不良として Fail Loud（KeyError）— ダミー補完しない。
    """
    # --- GAP（NpzFile は遅延展開: 一度だけ取り出す。§CLAUDE ハマりどころ OOM 対策）---
    g = np.load(GAP_DIR / f"{split}_gap.npz")
    gap_all = g["features"]
    gap_by_frame = {str(fid): gap_all[i] for i, fid in enumerate(g["frame_ids"])}

    # --- 手特徴 ---
    hpath = _hand_npz_path(split, hand_feature_type, hand_source, hand_src)
    if not hpath.exists():
        raise FileNotFoundError(f"[haux] 手特徴 npz 不在: {hpath}（build_oracle_handfeature.py を実行したか）")
    h = np.load(hpath)
    hand_all = h["signal"]
    hand_by_frame = {str(fid): hand_all[i] for i, fid in enumerate(h["frame_ids"])}

    # §4.3 shuffle control: 手特徴の frame 対応を破壊（容量効果 vs 真の相関の切り分け）
    if shuffle_hand:
        rng = np.random.RandomState(shuffle_seed)
        keys = list(hand_by_frame.keys())
        vals = [hand_by_frame[k] for k in keys]
        rng.shuffle(vals)
        hand_by_frame = {k: v for k, v in zip(keys, vals)}

    # --- H-6: tool-presence 併用 ---
    tool_by_frame: dict[str, np.ndarray] | None = None
    if with_tool:
        tpath = (ORACLE_TOOL_DIR / f"{split}_oracletool.npz" if tool_source == "oracle"
                 else PRED_TOOL_DIR / f"{split}_toolpresence.npz")
        if not tpath.exists():
            raise FileNotFoundError(f"[haux] tool 信号 npz 不在: {tpath}")
        t = np.load(tpath)
        tool_all = t["signal"]
        tool_by_frame = {str(fid): tool_all[i] for i, fid in enumerate(t["frame_ids"])}

    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        rows = []
        for fr in clip["frames"]:
            fid = fr["frame"]
            if fid not in gap_by_frame:
                raise KeyError(f"[haux] GAP 特徴に frame_id 欠落: {fid} ({split})")
            if fid not in hand_by_frame:
                raise KeyError(f"[haux] 手特徴に frame_id 欠落: {fid} ({split})")
            parts = []
            if not drop_gap:
                parts.append(gap_by_frame[fid])
            parts.append(hand_by_frame[fid])
            if tool_by_frame is not None:
                if fid not in tool_by_frame:
                    raise KeyError(f"[haux] tool 信号に frame_id 欠落: {fid} ({split})")
                parts.append(tool_by_frame[fid])
            rows.append(np.concatenate(parts))
        feats = np.stack(rows).astype(np.float32)
        labels = np.asarray([fr["label"] for fr in clip["frames"]], dtype=np.int64)
        clips.append((clip["clip_id"], feats, labels))
    return clips


def compute_in_dim(hand_feature_type: str, with_tool: bool, drop_gap: bool) -> int:
    d = 0 if drop_gap else GAP_DIM
    d += HAND_FEATURE_DIM[hand_feature_type]
    if with_tool:
        d += NUM_TOOLS
    return d


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
        x = torch.from_numpy(feats).T.unsqueeze(0).to(device)  # (1, D, T)
        logits = model(x)[-1]
        preds = logits[0].argmax(0).cpu().numpy()
        metrics.update(preds, labels, video_id=clip_id)
    return metrics.compute()


def _method_tag(args) -> str:
    """ExperimentManager step/description（採番は Manager。手動命名しない方針だが step 名は必要）。"""
    tag = f"haux_hand_{args.hand_feature_type}"
    tag += "_oracle" if args.hand_source == "oracle" else f"_{args.hand_src}"
    if args.with_tool:
        tag += f"_withtool{args.tool_source}"
    if args.drop_gap:
        tag += "_nogap"
    if args.shuffle_hand:
        tag += "_shuffle"
    return tag


def _build_cfg(args, server_name, in_dim, n_train, n_val) -> dict:
    return {
        "experiment": {"category": "transfer", "step": "haux_hand", "description": _method_tag(args)},
        "seed": args.seed,
        "frozen_source": {"detector": "relation_detr", "seed": 42, "backbone": "resnet50",
                          "gap_cache": str(GAP_DIR.relative_to(PROJ))},
        "method": {"name": "haux_hand_to_phase", "system": "①signal_level", "direction": "hand->phase",
                   "hand_feature_type": args.hand_feature_type, "hand_source": args.hand_source,
                   "with_tool": args.with_tool, "tool_source": args.tool_source if args.with_tool else None,
                   "drop_gap": args.drop_gap, "shuffle_control": args.shuffle_hand,
                   "hand_feature_dim": HAND_FEATURE_DIM[args.hand_feature_type],
                   "coupling": "handfeature_concat", "neck": None, "grad_crossing": False},
        "model": {"temporal_head": "tecno", "num_stages": args.num_stages,
                  "num_layers": args.num_layers, "num_f_maps": args.num_f_maps,
                  "in_dim": in_dim, "num_phases": len(CLASS_NAMES), "causal": True},
        "train": {"epochs": args.epochs, "lr": args.lr, "weight_decay": args.weight_decay,
                  "freeze_backbone": True, "smoothing_weight": 0.15},
        "data": {"n_train_clips": n_train, "n_val_clips": n_val},
        "delta": {"phase_denominator": "s4_phase_baseline (frozen_tecno_phase_baseline)",
                  "note": "Δ_phase = (H-aux − S4 base 0.8986±0.0028). 土台は素 TeCNO・neck 無しで一致、変える軸は手特徴 1 点。"},
        "server_name": server_name,
    }


def _build_phase_recipe(args, server_name, in_dim) -> dict:
    test_cfg = {
        "task": "phase",
        **PHASE_EVAL_PROTOCOL,
        "backbone": "relation_detr_resnet50_frozen_seed42",
        "temporal_head": "tecno",
        "num_stages": args.num_stages,
        "num_layers": args.num_layers,
        "num_f_maps": args.num_f_maps,
        "in_dim": in_dim,
        "coupling": f"haux_hand_to_phase_{args.hand_feature_type}",
        "hand_feature_dim": HAND_FEATURE_DIM[args.hand_feature_type],
        "hand_source": args.hand_source,
        "with_tool": args.with_tool,
    }
    return build_eval_recipe(
        test_cfg=test_cfg, split_sizes=PAPER_SPLIT_SIZES, server_name=server_name,
        gpu_count=1, effective_batch_size=1, lr_scaling="none",
    )


def _write_notes(exp_dir: Path, args, best, server_name, in_dim) -> None:
    hd = HAND_FEATURE_DIM[args.hand_feature_type]
    note = (
        f"# STEP D-aux 系統① 手情報→工程（det→phase・①信号レベル）\n\n"
        f"手特徴 `{args.hand_feature_type}`（{hd}-d, source={args.hand_source}）を "
        f"GAP({GAP_DIM}) に入力連結 → 素 causal TeCNO。①は勾配を交差させず信号のみ渡す。online/causal。\n"
        f"{'H-6: tool-presence 15-d 併用（source=' + args.tool_source + '）。' if args.with_tool else ''}"
        f"{'§4.3 shuffle control: 手特徴の frame 対応を破壊（容量効果 vs 真の相関）。' if args.shuffle_hand else ''}\n\n"
        f"## 結果（best @epoch {best.get('epoch')}）\n"
        f"- accuracy={best['phase_accuracy']:.4f} / macro_f1={best['phase_macro_f1']:.4f}\n"
        f"- edit={best['phase_edit_score']:.2f} / seg_f1@10/25/50="
        f"{best['phase_seg_f1_10']:.2f}/{best['phase_seg_f1_25']:.2f}/{best['phase_seg_f1_50']:.2f}\n\n"
        f"## 構成\n- seed={args.seed} epochs={args.epochs} lr={args.lr} in_dim={in_dim} "
        f"stages={args.num_stages} layers={args.num_layers} f_maps={args.num_f_maps}\n"
        f"- server={server_name} / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)\n\n"
        f"## Δ\n- Δ_phase = (H-aux − S4 base 0.8986±0.0028)。同一土台（凍結backbone/GAP/recipe/seed・neck無し）。\n"
        f"- 3-seed 揃ったら paired-σ(対seed差) で §10.1 判定（|Δ|>paired-σ かつ同符号で有意）。\n"
    )
    (exp_dir / "notes.md").write_text(note, encoding="utf-8")


class HauxTeCNO(nn.Module):
    """H-5 own/other 分離注入用の薄いラッパ。

    hand_feature_type != own_other の場合は通常の TeCNO（恒等）。own_other の場合のみ、
    geom 16-d を own(0-7)/other(8-15) の 2 ブロックに分け、各を小 MLP で 8-d に符号化して
    GAP( ・tool) に連結してから TeCNO に入れる（役割非対称性の明示的分離）。
    """

    def __init__(self, in_dim, num_classes, args, base_dim_wo_hand):
        super().__init__()
        self.separate = args.hand_feature_type == "own_other"
        if self.separate:
            self.own_enc = nn.Sequential(nn.Linear(8, 8), nn.ReLU())
            self.other_enc = nn.Sequential(nn.Linear(8, 8), nn.ReLU())
            # own_enc/other_enc は 8→8 で次元保存。z = [GAP, own8, other8, (tool)] は x と同次元。
            # よって tecno_in は with_tool の有無に依らず in_dim に一致（H-5×H-6 併用でもズレない）。
            tecno_in = in_dim
        else:
            tecno_in = in_dim
        self.base_dim_wo_hand = base_dim_wo_hand
        self.tecno = TeCNO(num_stages=args.num_stages, num_layers=args.num_layers,
                           num_f_maps=args.num_f_maps, in_dim=tecno_in,
                           num_classes=num_classes)

    def forward(self, x):  # x: (B, in_dim, T)
        if not self.separate:
            return self.tecno(x)
        # own_other: 手 geom 16-d は連結の「最初の手ブロック」に置かれる。
        # load_clips の連結順は [GAP(base) , hand(16) , (tool)] なので、
        # hand ブロックは base_dim_wo_hand の直後 16 次元（tool は with_tool 時のみ末尾）。
        base = self.base_dim_wo_hand
        pre = x[:, :base, :]                       # GAP（drop_gap 時は空）
        own = x[:, base:base + 8, :]               # own_L(4)+own_R(4)
        other = x[:, base + 8:base + 16, :]        # other_L(4)+other_R(4)
        post = x[:, base + 16:, :]                 # tool（with_tool 時）
        own_e = self.own_enc(own.transpose(1, 2)).transpose(1, 2)
        other_e = self.other_enc(other.transpose(1, 2)).transpose(1, 2)
        z = torch.cat([pre, own_e, other_e, post], dim=1)
        return self.tecno(z)


def train(args) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    in_dim = compute_in_dim(args.hand_feature_type, args.with_tool, args.drop_gap)
    base_dim_wo_hand = (0 if args.drop_gap else GAP_DIM)  # 手ブロックの前にある次元数（own_other 分割用。tool は手の後）

    def _load(split):
        return load_clips(
            split, hand_feature_type=args.hand_feature_type, hand_source=args.hand_source,
            hand_src=args.hand_src, with_tool=args.with_tool, tool_source=args.tool_source,
            drop_gap=args.drop_gap, shuffle_hand=args.shuffle_hand, shuffle_seed=args.shuffle_seed,
        )

    train_clips, val_clips = _load("train"), _load("val")
    if args.smoke:
        train_clips, val_clips = train_clips[:3], val_clips[:2]
    print(f"[haux] train clips={len(train_clips)} val clips={len(val_clips)} in_dim={in_dim} "
          f"type={args.hand_feature_type} source={args.hand_source} with_tool={args.with_tool} "
          f"classes={len(CLASS_NAMES)} device={device}")

    server_name = resolve_server_name(None)
    manager = exp_dir = None
    desc = args.description_override or _method_tag(args)
    if not args.smoke and not args.no_evidence:
        manager = ExperimentManager(base_dir=str(PROJ / "experiments"), category="transfer",
                                    step=desc, description=desc, seed=args.seed)
        manager.setup(_build_cfg(args, server_name, in_dim, len(train_clips), len(val_clips)))
        exp_dir = manager.exp_dir
        print(f"[haux] evidence dir: {exp_dir}")

    model = HauxTeCNO(in_dim, len(CLASS_NAMES), args, base_dim_wo_hand).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()

    from egosurgery.utils import tracking
    tracking.init(f"haux_{_method_tag(args)}_seed{args.seed}", group="D-aux", job_type="haux",
                  config={"seed": args.seed, "lr": args.lr, "epochs": args.epochs, "in_dim": in_dim,
                          "method": _method_tag(args)})

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
        print(f"[haux][epoch {epoch + 1}/{args.epochs}] loss={ep_loss / max(len(train_clips),1):.4f} "
              f"val_acc={val['phase_accuracy']:.4f} macroF1={val['phase_macro_f1']:.4f} "
              f"edit={val['phase_edit_score']:.2f} segF1@50={val['phase_seg_f1_50']:.2f}")
        tracking.log({"train/loss": ep_loss / max(len(train_clips), 1),
                      "val/phase_accuracy": val["phase_accuracy"], "val/macro_f1": val["phase_macro_f1"],
                      "val/jaccard": val["phase_jaccard"], "val/seg_f1_50": val["phase_seg_f1_50"]}, step=epoch)
        if val["phase_accuracy"] > best["phase_accuracy"]:
            best = {**val, "epoch": epoch + 1}
            if exp_dir is not None:
                torch.save({"tecno": model.state_dict(), "epoch": epoch + 1, "val": val},
                           exp_dir / "checkpoints" / "best_tecno.pth")
    print(f"[haux] best @epoch {best.get('epoch')}: acc={best['phase_accuracy']:.4f} "
          f"macroF1={best['phase_macro_f1']:.4f}")

    if manager is not None:
        per_class = best.get("phase_per_class_f1", {})
        scalars = {k: v for k, v in best.items() if isinstance(v, (int, float))}
        manager.log_eval_recipe(_build_phase_recipe(args, server_name, in_dim))
        manager.log_metrics(scalars)
        manager.log_per_class_ap(per_class)
        _write_notes(exp_dir, args, best, server_name, in_dim)
        print(f"[haux] evidence written -> {exp_dir}")
        from egosurgery.utils.notion_logger import log_experiment_to_notion
        log_experiment_to_notion(
            exp_dir, status="completed", step="B", tier="explore",
            primary_metric="phase acc/macro-F1/jaccard/edit/seg-F1 (online_causal, jaccard strict)",
            extra_result_text=f"①信号 hand→phase（{_method_tag(args)}）。Δ_phase vs S4 base 0.8986±0.0028")
    tracking.finish()
    return best


def parse_args():
    p = argparse.ArgumentParser(
        description="STEP D-aux 系統① hand->phase coupling (hand feature ⊕ GAP → causal TeCNO).")
    p.add_argument("--hand-feature-type", choices=list(HAND_FEATURE_DIM.keys()), default="presence",
                   help="H-1 presence / H-2 count / H-3 geom / H-5 own_other（geom を own/other 別枝符号化）")
    p.add_argument("--hand-source", choices=["oracle", "pred"], default="oracle",
                   help="oracle=GT bbox 由来（build_oracle_handfeature.py）/ pred=S2-hand 検出器予測（非-oracle）")
    p.add_argument("--hand-src", type=str, default="s2hand_seed42",
                   help="pred 時の手検出器タグ（data/processed/haux_detsignal/<tag>/）")
    p.add_argument("--with-tool", action="store_true", help="H-6: tool-presence 15-d を併用")
    p.add_argument("--tool-source", choices=["pred", "oracle"], default="oracle",
                   help="H-6 の tool 信号ソース（既定 oracle）")
    p.add_argument("--drop-gap", action="store_true", help="GAP 2048d を削除して手特徴のみ入力")
    p.add_argument("--shuffle-hand", action="store_true", help="§4.3 shuffle control（手特徴の frame 対応破壊）")
    p.add_argument("--shuffle-seed", type=int, default=12345)
    p.add_argument("--description-override", type=str, default=None)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
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

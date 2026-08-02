#!/usr/bin/env python
"""T1a-RegionTrajectory: Temporal Object-Set Fusion（COUPLING §4.1 優先度1）。

T1a base は region-token(15×256) を **flat 連結**で TeCNO に渡すため、frame ごとの術具出現変動へ
過敏に反応し edit score が悪化・過分節する（§3.1）。本実装は §4.1 の役割分離アーキを組む:

    各フレーム region tokens(15×256)
      → Set encoder（per-token 共有MLP + class埋め込み + attention pool = 置換不変集約）
      → 二経路 gated residual（安定 tool-presence(15-d) ⊕ rich region）
      → causal temporal attention（短期 object memory）
      → SingleStageTCN(TeCNO) + refine
        ├ phase head
        └ boundary head（class-agnostic・既存 sticky decode 流用）

online/causal（未来不使用）。土台・ハイパーは T1a base / T1a-Boundary と統一（変える軸＝表現統合のみ）。
Δ = (RegionTraj − T1a base[同env efros]) の per-seed paired-σ（§10.1）。主指標 edit/seg-F1、維持 acc/macro-F1。

入力キャッシュ（再利用・再抽出不要）:
  data/processed/stage1_features/<src>/{split}_gap.npz              (features=GAP2048)
  data/processed/t1a_regiontoken/<src>/{split}_regiontoken.npz      (region=3840=15×256)
  data/processed/b2a_detsignal/<src>/{split}_toolpresence.npz       (signal=15)

実行（本体 python; efros は .venv 無いので python3 直呼び）:
  python3 scripts/train_t1a_regiontraj.py --smoke
  python3 scripts/train_t1a_regiontraj.py --seed 42 --epochs 50
"""
from __future__ import annotations

import argparse
import json
import math
import os
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
from egosurgery.models.heads.tecno_head import SingleStageTCN  # noqa: E402
from egosurgery.utils.eval_recipe import (  # noqa: E402
    PAPER_SPLIT_SIZES,
    PHASE_EVAL_PROTOCOL,
    build_eval_recipe,
)
from egosurgery.utils.experiment_manager import ExperimentManager  # noqa: E402
from egosurgery.utils.server_name import resolve_server_name  # noqa: E402

FROZEN_SRC = os.environ.get("RELDETR_FROZEN_TAG", "relation_detr_seed42")
GAP_DIR = PROJ / "data" / "processed" / "stage1_features" / FROZEN_SRC
REGION_DIR = PROJ / "data" / "processed" / "t1a_regiontoken" / FROZEN_SRC
TOOLPRES_DIR = PROJ / "data" / "processed" / "b2a_detsignal" / FROZEN_SRC
MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())
GAP_DIM, N_TOOL, TOK_IN = 2048, 15, 256


# ---------------------------------------------------------------------------
# データ: gap(T,2048) / region(T,15,256) / presence(T,15) を **構造保持**で返す
# ---------------------------------------------------------------------------
def load_clips(split: str):
    g = np.load(GAP_DIR / f"{split}_gap.npz")
    gap_all = g["features"]
    gap_by = {str(fid): gap_all[i] for i, fid in enumerate(g["frame_ids"])}

    r = np.load(REGION_DIR / f"{split}_regiontoken.npz")
    reg_all = r["region"].reshape(-1, N_TOOL, TOK_IN)  # (N,15,256)
    reg_by = {str(fid): reg_all[i] for i, fid in enumerate(r["frame_ids"])}

    t = np.load(TOOLPRES_DIR / f"{split}_toolpresence.npz")
    tp_all = t["signal"]
    tp_by = {str(fid): tp_all[i] for i, fid in enumerate(t["frame_ids"])}

    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        frames = clip["frames"]
        gaps, regs, tps = [], [], []
        for fr in frames:
            fid = fr["frame"]
            for name, d in (("GAP", gap_by), ("region", reg_by), ("tool-presence", tp_by)):
                if fid not in d:
                    raise KeyError(f"[regtraj] {name} に frame_id 欠落: {fid} ({split})")
            gaps.append(gap_by[fid])
            regs.append(reg_by[fid])
            tps.append(tp_by[fid])
        gap = np.stack(gaps).astype(np.float32)          # (T,2048)
        reg = np.stack(regs).astype(np.float32)          # (T,15,256)
        tp = np.stack(tps).astype(np.float32)            # (T,15)
        labels = np.asarray([fr["label"] for fr in frames], dtype=np.int64)
        clips.append((clip["clip_id"], gap, reg, tp, labels))
    return clips


# ---------------------------------------------------------------------------
# モデル: Set encoder + gated residual + causal temporal attention + TeCNO + boundary
# ---------------------------------------------------------------------------
class RegionTrajTeCNO(nn.Module):
    def __init__(self, num_stages=2, num_layers=8, num_f_maps=64, num_classes=9,
                 tok_dim=128, pres_dim=64, d_model=256, n_heads=4, dropout=0.5,
                 use_temporal_attn=True, use_gate=True):
        super().__init__()
        self.use_temporal_attn = use_temporal_attn
        self.use_gate = use_gate
        # --- Set encoder（per-token 共有MLP + 学習可能 class 埋め込み + attention pool）---
        self.token_mlp = nn.Sequential(
            nn.Linear(TOK_IN, tok_dim), nn.ReLU(), nn.Linear(tok_dim, tok_dim)
        )
        self.class_emb = nn.Parameter(torch.zeros(N_TOOL, tok_dim))  # slot=クラス識別（zero-init）
        self.pool_q = nn.Parameter(torch.randn(tok_dim) * (tok_dim ** -0.5))
        # --- 安定経路: tool-presence(15) → 埋め込み ---
        self.pres_mlp = nn.Sequential(nn.Linear(N_TOOL, pres_dim), nn.ReLU())
        # --- gated residual: presence から rich region の gate を作る ---
        self.gate = nn.Linear(pres_dim, tok_dim)
        # --- 入力射影: [GAP ⊕ region_gated ⊕ presence] → d_model ---
        self.in_proj = nn.Sequential(
            nn.Linear(GAP_DIM + tok_dim + pres_dim, d_model), nn.ReLU()
        )
        # --- causal temporal attention（短期 object memory）---
        if use_temporal_attn:
            self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
            self.attn_norm = nn.LayerNorm(d_model)
        # --- TeCNO（stage1 trunk 共有 + refine）+ boundary head ---
        self.stage1 = SingleStageTCN(num_layers, num_f_maps, d_model, num_classes, dropout)
        self.refine_stages = nn.ModuleList(
            [SingleStageTCN(num_layers, num_f_maps, num_classes, num_classes, dropout)
             for _ in range(num_stages - 1)]
        )
        self.boundary_out = nn.Conv1d(num_f_maps, 1, kernel_size=1)

    def _frame_feat(self, gap, region, presence):
        """gap(B,T,2048) region(B,T,15,256) presence(B,T,15) → per-frame (B,T,d_model)。"""
        h = self.token_mlp(region) + self.class_emb            # (B,T,15,tok_dim)
        scores = (h @ self.pool_q) / math.sqrt(h.shape[-1])    # (B,T,15)
        w = scores.softmax(dim=-1).unsqueeze(-1)               # (B,T,15,1)
        region_summary = (w * h).sum(dim=2)                    # (B,T,tok_dim) 置換不変集約
        pres_emb = self.pres_mlp(presence)                     # (B,T,pres_dim)
        if self.use_gate:
            g = torch.sigmoid(self.gate(pres_emb))             # (B,T,tok_dim)
            region_summary = g * region_summary                # 安定経路が rich 経路を gate
        fused = torch.cat([gap, region_summary, pres_emb], dim=-1)
        return self.in_proj(fused)                             # (B,T,d_model)

    def forward(self, gap, region, presence):
        z = self._frame_feat(gap, region, presence)            # (B,T,d_model)
        if self.use_temporal_attn:
            T = z.shape[1]
            mask = torch.triu(torch.ones(T, T, device=z.device, dtype=torch.bool), diagonal=1)
            a, _ = self.attn(z, z, z, attn_mask=mask, need_weights=False)  # causal
            z = self.attn_norm(z + a)
        x = z.transpose(1, 2)                                  # (B,d_model,T)
        trunk = self.stage1.conv_in(x)
        for layer in self.stage1.layers:
            trunk = layer(trunk)
        out = self.stage1.conv_out(trunk)
        phase_outputs = [out]
        for stage in self.refine_stages:
            out = stage(F.softmax(out, dim=1))
            phase_outputs.append(out)
        boundary_logit = self.boundary_out(trunk)              # (B,1,T)
        return phase_outputs, boundary_logit


# ---- boundary / decode / loss（T1a-Boundary と同一定義）------------------------
def boundary_target(labels: np.ndarray, dilate: int) -> np.ndarray:
    T = len(labels)
    b = np.zeros(T, dtype=np.float32)
    if T < 2:
        return b
    for t in np.nonzero(labels[1:] != labels[:-1])[0] + 1:
        b[max(0, t - dilate):min(T, t + dilate + 1)] = 1.0
    return b


def smoothing_loss(logits: torch.Tensor) -> torch.Tensor:
    ls = F.log_softmax(logits, dim=1)
    mse = F.mse_loss(ls[:, :, 1:], ls[:, :, :-1], reduction="none")
    return torch.clamp(mse, max=16.0).mean()


def sticky_decode(logits: np.ndarray, boundary_prob: np.ndarray, tau: float) -> np.ndarray:
    C, T = logits.shape
    am = logits.argmax(0)
    preds = np.empty(T, dtype=np.int64)
    p = int(am[0]); preds[0] = p
    for t in range(1, T):
        a = int(am[t])
        if a == p:
            preds[t] = p
        elif boundary_prob[t] >= tau:
            preds[t] = a; p = a
        else:
            preds[t] = p
    return preds


def _to_dev(gap, reg, tp, device):
    return (torch.from_numpy(gap).unsqueeze(0).to(device),
            torch.from_numpy(reg).unsqueeze(0).to(device),
            torch.from_numpy(tp).unsqueeze(0).to(device))


@torch.no_grad()
def evaluate(model, clips, device, tau):
    model.eval()
    m_plain = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    m_sticky = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    for clip_id, gap, reg, tp, labels in clips:
        g, r, p = _to_dev(gap, reg, tp, device)
        phase_outs, b_logit = model(g, r, p)
        lg = phase_outs[-1][0].cpu().numpy()
        bp = torch.sigmoid(b_logit[0, 0]).cpu().numpy()
        m_plain.update(lg.argmax(0), labels, video_id=clip_id)
        m_sticky.update(sticky_decode(lg, bp, tau), labels, video_id=clip_id)
    return m_plain.compute(), m_sticky.compute()


def _auto_pos_weight(clips, dilate) -> float:
    pos = tot = 0
    for _, _, _, _, labels in clips:
        b = boundary_target(labels, dilate)
        pos += int(b.sum()); tot += len(b)
    return 1.0 if pos == 0 else float(min((tot - pos) / pos, 50.0))


DESC = "t1a_regiontraj"


def _build_cfg(args, server_name, n_train, n_val, pos_weight) -> dict:
    return {
        "experiment": {"category": "transfer", "step": args.description, "description": args.description},
        "seed": args.seed,
        "frozen_source": {"detector": "relation_detr", "seed": 42, "backbone": "resnet50",
                          "gap_cache": str(GAP_DIR.relative_to(PROJ)),
                          "region_cache": str(REGION_DIR.relative_to(PROJ))},
        "method": {
            "name": "t1a_region_trajectory",
            "system": "②feature_level/object-token + temporal-object-set-fusion",
            "ref": "COUPLING_IMPROVEMENT_RECOMMENDATIONS §4.1 (Temporal Object-Set Fusion)",
            "direction": "det->phase",
            "coupling": "set_encoder+gated_residual(presence)+causal_temporal_attn+tecno+boundary",
            "set_encoder": "per_token_shared_mlp + learnable_class_emb + attention_pool",
            "gated_residual": bool(args.use_gate),
            "temporal_attn": bool(args.use_temporal_attn),
            "boundary_head": "shared_trunk conv1d(f->1) class_agnostic causal",
            "region_dim": N_TOOL * TOK_IN, "neck": None, "grad_crossing": False,
        },
        "model": {"temporal_head": "regiontraj_tecno+boundary", "num_stages": args.num_stages,
                  "num_layers": args.num_layers, "num_f_maps": args.num_f_maps,
                  "d_model": args.d_model, "tok_dim": args.tok_dim, "pres_dim": args.pres_dim,
                  "num_phases": len(CLASS_NAMES), "causal": True},
        "train": {"epochs": args.epochs, "lr": args.lr, "weight_decay": args.weight_decay,
                  "freeze_backbone": True, "smoothing_weight": 0.15,
                  "boundary_weight": args.boundary_weight, "boundary_pos_weight": pos_weight,
                  "boundary_dilate": args.boundary_dilate, "boundary_tau": args.boundary_tau},
        "data": {"n_train_clips": n_train, "n_val_clips": n_val},
        "delta": {"phase_denominator": "t1a_regiontoken base (同env efros paired)",
                  "primary_metric": "edit_score / seg_f1@{10,25,50}",
                  "maintain_metric": "accuracy / macro_f1",
                  "note": "Δ = (RegionTraj − T1a base[同env]) per-seed paired-σ §10.1。"},
        "server_name": server_name,
    }


def _build_phase_recipe(args, server_name, d_model) -> dict:
    test_cfg = {"task": "phase", **PHASE_EVAL_PROTOCOL,
                "backbone": "relation_detr_resnet50_frozen_seed42",
                "temporal_head": "regiontraj_tecno+boundary",
                "num_stages": args.num_stages, "num_layers": args.num_layers,
                "num_f_maps": args.num_f_maps, "in_dim": d_model,
                "coupling": "t1a_temporal_object_set_fusion", "region_dim": N_TOOL * TOK_IN}
    return build_eval_recipe(test_cfg=test_cfg, split_sizes=PAPER_SPLIT_SIZES,
                             server_name=server_name, gpu_count=1,
                             effective_batch_size=1, lr_scaling="none")


def _write_notes(exp_dir, args, best, sticky, server_name, pos_weight) -> None:
    note = (
        f"# T1a-RegionTrajectory（Temporal Object-Set Fusion・COUPLING §4.1）\n\n"
        f"region-token(15×256) を Set encoder（共有MLP+class埋め込み+attention pool）で集約→"
        f"tool-presence と gated residual→causal temporal attention→TeCNO+boundary head。online/causal。\n\n"
        f"## 結果（best @epoch {best.get('epoch')}・val）\n"
        f"### plain decode\n- acc={best['phase_accuracy']:.4f} / macro_f1={best['phase_macro_f1']:.4f}\n"
        f"- edit={best['phase_edit_score']:.2f} / seg_f1@10/25/50="
        f"{best['phase_seg_f1_10']:.3f}/{best['phase_seg_f1_25']:.3f}/{best['phase_seg_f1_50']:.3f}\n"
        f"### sticky decode（τ={args.boundary_tau}）\n"
        f"- acc={sticky['phase_accuracy']:.4f} / macro_f1={sticky['phase_macro_f1']:.4f}\n"
        f"- edit={sticky['phase_edit_score']:.2f} / seg_f1@10/25/50="
        f"{sticky['phase_seg_f1_10']:.3f}/{sticky['phase_seg_f1_25']:.3f}/{sticky['phase_seg_f1_50']:.3f}\n\n"
        f"## 構成\n- seed={args.seed} epochs={args.epochs} lr={args.lr} d_model={args.d_model} "
        f"tok_dim={args.tok_dim} pres_dim={args.pres_dim} stages={args.num_stages} layers={args.num_layers}\n"
        f"- set_encoder=on gated_residual={args.use_gate} temporal_attn={args.use_temporal_attn} "
        f"boundary(w={args.boundary_weight} pos_w={pos_weight:.2f} tau={args.boundary_tau})\n"
        f"- server={server_name} / recipe=online_causal+jaccard_strict\n\n"
        f"## Δ\n- Δ=(RegionTraj − T1a base[同env efros])。主指標 edit/seg-F1、維持 acc/macro-F1。3-seed paired-σ §10.1。\n"
    )
    (exp_dir / "notes.md").write_text(note, encoding="utf-8")


def train(args) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)

    train_clips = load_clips("train")
    val_clips = load_clips("val")
    if args.smoke:
        train_clips, val_clips = train_clips[:3], val_clips[:2]
    pos_weight = (args.boundary_pos_weight if args.boundary_pos_weight > 0
                  else _auto_pos_weight(train_clips, args.boundary_dilate))
    print(f"[regtraj] train={len(train_clips)} val={len(val_clips)} d_model={args.d_model} "
          f"gate={args.use_gate} tattn={args.use_temporal_attn} "
          f"boundary(w={args.boundary_weight} pos_w={pos_weight:.2f} tau={args.boundary_tau}) dev={device}")

    server_name = resolve_server_name(None)
    manager = exp_dir = None
    if not args.smoke and not args.no_evidence:
        manager = ExperimentManager(base_dir=str(PROJ / "experiments"), category="transfer",
                                    step=args.description, description=args.description, seed=args.seed)
        manager.setup(_build_cfg(args, server_name, len(train_clips), len(val_clips), pos_weight))
        exp_dir = manager.exp_dir
        print(f"[regtraj] evidence dir: {exp_dir}")

    model = RegionTrajTeCNO(
        num_stages=args.num_stages, num_layers=args.num_layers, num_f_maps=args.num_f_maps,
        num_classes=len(CLASS_NAMES), tok_dim=args.tok_dim, pres_dim=args.pres_dim,
        d_model=args.d_model, n_heads=args.n_heads,
        use_temporal_attn=args.use_temporal_attn, use_gate=args.use_gate,
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()
    bce = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight], device=device))

    from egosurgery.utils import tracking
    tracking.init(f"{args.description}_seed{args.seed}", group="B", job_type="t1a_regiontraj",
                  config={"seed": args.seed, "lr": args.lr, "epochs": args.epochs,
                          "d_model": args.d_model, "method": "t1a_region_trajectory"})

    best = {"phase_accuracy": -1.0}
    best_sticky: dict = {}
    for epoch in range(args.epochs):
        model.train()
        random.shuffle(train_clips)
        ep_loss = ep_bd = 0.0
        for clip_id, gap, reg, tp, labels in train_clips:
            g, r, pr = _to_dev(gap, reg, tp, device)
            y = torch.from_numpy(labels).to(device)
            bt = torch.from_numpy(boundary_target(labels, args.boundary_dilate)).to(device)
            phase_outs, b_logit = model(g, r, pr)
            phase_loss = sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in phase_outs)
            bd_loss = bce(b_logit[0, 0], bt)
            loss = phase_loss + args.boundary_weight * bd_loss
            opt.zero_grad(); loss.backward(); opt.step()
            ep_loss += float(loss); ep_bd += float(bd_loss)
        val_plain, val_sticky = evaluate(model, val_clips, device, args.boundary_tau)
        print(f"[regtraj][ep {epoch+1}/{args.epochs}] loss={ep_loss/max(len(train_clips),1):.4f} "
              f"bd={ep_bd/max(len(train_clips),1):.4f} || plain acc={val_plain['phase_accuracy']:.4f} "
              f"edit={val_plain['phase_edit_score']:.2f} segF1@50={val_plain['phase_seg_f1_50']:.3f} || "
              f"sticky acc={val_sticky['phase_accuracy']:.4f} edit={val_sticky['phase_edit_score']:.2f} "
              f"segF1@50={val_sticky['phase_seg_f1_50']:.3f}")
        tracking.log({"train/loss": ep_loss/max(len(train_clips),1),
                      "train/boundary_loss": ep_bd/max(len(train_clips),1),
                      "val/phase_accuracy": val_plain["phase_accuracy"],
                      "val/edit_plain": val_plain["phase_edit_score"],
                      "val/edit_sticky": val_sticky["phase_edit_score"],
                      "val/seg_f1_50_sticky": val_sticky["phase_seg_f1_50"]}, step=epoch)
        if val_plain["phase_accuracy"] > best["phase_accuracy"]:
            best = {**val_plain, "epoch": epoch + 1}
            best_sticky = dict(val_sticky)
            if exp_dir is not None:
                torch.save({"model": model.state_dict(), "epoch": epoch + 1,
                            "val_plain": val_plain, "val_sticky": val_sticky},
                           exp_dir / "checkpoints" / "best_regiontraj.pth")
    print(f"[regtraj] best @epoch {best.get('epoch')}: plain acc={best['phase_accuracy']:.4f} "
          f"macroF1={best['phase_macro_f1']:.4f} edit={best['phase_edit_score']:.2f} || "
          f"sticky acc={best_sticky.get('phase_accuracy',0):.4f} edit={best_sticky.get('phase_edit_score',0):.2f}")

    # test-set 確認（val→test 頑健性; best checkpoint を test 評価, plain+sticky）
    test_scalars: dict = {}
    if args.eval_test:
        test_clips = load_clips("test")
        if exp_dir is not None:
            ck = torch.load(exp_dir / "checkpoints" / "best_regiontraj.pth", map_location=device)
            model.load_state_dict(ck["model"])
        t_plain, t_sticky = evaluate(model, test_clips, device, args.boundary_tau)
        for k, v in t_plain.items():
            if isinstance(v, (int, float)):
                test_scalars[k.replace("phase_", "test_")] = v
        for k, v in t_sticky.items():
            if isinstance(v, (int, float)):
                test_scalars["sticky_" + k.replace("phase_", "test_")] = v
        print(f"[regtraj] TEST plain acc={t_plain['phase_accuracy']:.4f} "
              f"macroF1={t_plain['phase_macro_f1']:.4f} edit={t_plain['phase_edit_score']:.2f} "
              f"segF1@50={t_plain['phase_seg_f1_50']:.3f} || "
              f"sticky acc={t_sticky['phase_accuracy']:.4f} edit={t_sticky['phase_edit_score']:.2f}")

    if manager is not None:
        scalars = {k: v for k, v in best.items() if isinstance(v, (int, float))}
        scalars.update({f"sticky_{k}": v for k, v in best_sticky.items() if isinstance(v, (int, float))})
        scalars.update(test_scalars)
        manager.log_eval_recipe(_build_phase_recipe(args, server_name, args.d_model))
        manager.log_metrics(scalars)
        manager.log_per_class_ap(best.get("phase_per_class_f1", {}))
        _write_notes(exp_dir, args, best, best_sticky, server_name, pos_weight)
        print(f"[regtraj] evidence written -> {exp_dir}")
        from egosurgery.utils.research_logger import ResearchLogger
        ResearchLogger(cfg=None, manager=manager).log_run(
            status="completed", step="B", tier="must",
            primary_metric="phase edit/seg-F1 (plain+sticky, online_causal); maintain acc/macro-F1",
            extra_result_text="§4.1 Temporal Object-Set Fusion。Δ vs T1a base（within-server）")
    tracking.finish()
    return best


def parse_args():
    p = argparse.ArgumentParser(description="T1a-RegionTrajectory: Temporal Object-Set Fusion (§4.1).")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--num-stages", type=int, default=2)
    p.add_argument("--num-layers", type=int, default=8)
    p.add_argument("--num-f-maps", type=int, default=64)
    p.add_argument("--d-model", type=int, default=256)
    p.add_argument("--tok-dim", type=int, default=128)
    p.add_argument("--pres-dim", type=int, default=64)
    p.add_argument("--n-heads", type=int, default=4)
    p.add_argument("--boundary-weight", type=float, default=1.0)
    p.add_argument("--boundary-dilate", type=int, default=1)
    p.add_argument("--boundary-tau", type=float, default=0.5)
    p.add_argument("--boundary-pos-weight", type=float, default=0.0)
    p.add_argument("--no-temporal-attn", dest="use_temporal_attn", action="store_false",
                   help="causal temporal attention を無効化（ablation）")
    p.add_argument("--no-gate", dest="use_gate", action="store_false",
                   help="gated residual を無効化（presence でゲートせず素の region 集約）")
    p.add_argument("--eval-test", action="store_true",
                   help="学習後、best checkpoint を test split で評価（val→test 頑健性確認）")
    p.add_argument("--smoke", action="store_true", help="3 epoch・少 clip 疎通確認（証跡なし）")
    p.add_argument("--no-evidence", action="store_true")
    p.add_argument("--description", type=str, default=DESC)
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    if a.smoke:
        a.epochs = 3
    train(a)

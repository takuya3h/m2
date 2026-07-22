#!/usr/bin/env python
"""T1a-Boundary: region-token→工程 に **因果 boundary head** を追加（over-segmentation / edit-score 改善）。

STEP C 改善提案書（`experiments/analysis/step_c_coupling_analysis/COUPLING_IMPROVEMENT_RECOMMENDATIONS.md`）
§4.1 / §6 第2段階 #5 / §8 最終提案の実装:

  「T1a の rich な region-token は frame accuracy / macro-F1 を上げる一方で **edit score を悪化**させ、
   過分節（prediction flicker）を起こす。必要なのは region-token と temporal model の単純連結でなく、
   **boundary evidence（いつ工程が変わったか）を別ヘッドで扱う役割分離**である。」

D-aux 系統②（`train_taux.py`）は region-token 上で **frame accuracy** を対象に時系列核/加工を比較し
「核非依存・ボトルネックは入力信号」を示したが、**edit-score / seg-F1（時間的一貫性）は未対象**だった。
本実験はその直交軸を突く: **acc/macro-F1 を維持しつつ edit-score / seg-F1 を改善できるか**。

設計（オンライン/因果を厳守 — §4.2「eval も未来フレーム不使用」）:
  入力 = [ GAP(2048) ⊕ region-token(3840) ] = 5888-d（T1a base と同一）
    ↓ 共有 causal TeCNO stage-1 trunk（conv_in + dilated layers, 64ch）
    ├─ phase head（既存 conv_out → 9class, refine stage も TeCNO と同一）
    └─ **boundary head（conv 64→1・class-agnostic・因果）**  ← 追加する唯一の軸
  loss = Σ_stage[ CE + 0.15·T-MSE ] + λ_b · BCEWithLogits(boundary_target, pos_weight)
  boundary_target[t] = 1 if y[t]≠y[t-1]（±dilate 近傍を 1）。**教師信号のみ**で dilate は未来を
    モデル入力に混ぜない（因果性は保持）。

推論（2 モード・同一 checkpoint で両方を測る）:
  - plain : per-frame argmax（T1a base と同一）→ **共有 trunk への boundary 監督（正則化）効果**を分離
  - sticky: **因果 boundary-gated sticky decode**。工程遷移の提案（argmax 変化）を、
            boundary 確信度 sigmoid(b_t) ≥ τ のときだけ受理し、低確信の単発 flip を抑制。
            現在フレームの b_t と logits のみ参照 → **完全に因果**。

判定: T1a base（同一環境 efros で再学習した paired 分母）との per-seed paired-σ（§10.1）。
  主指標 = edit_score / seg_f1@{10,25,50}、維持指標 = accuracy / macro_f1。

実行（本体 .venv or system python3・キャッシュのみ読む・Relation-DETR 非依存）:
  python scripts/train_t1a_boundary.py --seed 42
  python scripts/train_t1a_boundary.py --smoke   # 3 epoch・少 clip で疎通確認（証跡なし）
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
from egosurgery.models.heads.tecno_head import SingleStageTCN  # noqa: E402
from egosurgery.utils.eval_recipe import (  # noqa: E402
    PAPER_SPLIT_SIZES,
    PHASE_EVAL_PROTOCOL,
    build_eval_recipe,
)
from egosurgery.utils.experiment_manager import ExperimentManager  # noqa: E402
from egosurgery.utils.server_name import resolve_server_name  # noqa: E402

# T1a と同一のキャッシュ規約（凍結源 Relation-DETR seed42）
FROZEN_SRC = "relation_detr_seed42"
GAP_DIR = PROJ / "data" / "processed" / "stage1_features" / FROZEN_SRC
REGION_DIR = PROJ / "data" / "processed" / "t1a_regiontoken" / FROZEN_SRC
MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())
GAP_DIM = 2048
REGION_DIM = 15 * 256  # 3840


# ---------------------------------------------------------------------------
# データ（T1a base と完全同一の loader を region⊕GAP 用に最小化）
# ---------------------------------------------------------------------------
def load_clips(split: str, region_only: bool) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """(clip_id, feats[T, in_dim], labels[T]) を返す。feats = [GAP2048 ⊕ region3840]（or region のみ）。

    GAP・region いずれも frame_id でキー化して clip フレーム順に整列・連結。欠落は Fail Loud。
    NpzFile は一度だけ展開して dict 化（per-iteration 再索引の RSS 肥大を回避・失敗知見準拠）。
    """
    g = np.load(GAP_DIR / f"{split}_gap.npz")
    gap_all = g["features"]
    gap_by_frame = {str(fid): gap_all[i] for i, fid in enumerate(g["frame_ids"])}

    r = np.load(REGION_DIR / f"{split}_regiontoken.npz")
    reg_all = r["region"]
    reg_by_frame = {str(fid): reg_all[i] for i, fid in enumerate(r["frame_ids"])}

    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        rows = []
        for fr in clip["frames"]:
            fid = fr["frame"]
            if fid not in reg_by_frame:
                raise KeyError(f"[t1a-bd] region-token に frame_id 欠落: {fid} ({split})")
            if region_only:
                rows.append(reg_by_frame[fid])
            else:
                if fid not in gap_by_frame:
                    raise KeyError(f"[t1a-bd] GAP 特徴に frame_id 欠落: {fid} ({split})")
                rows.append(np.concatenate([gap_by_frame[fid], reg_by_frame[fid]]))
        feats = np.stack(rows).astype(np.float32)
        labels = np.asarray([fr["label"] for fr in clip["frames"]], dtype=np.int64)
        clips.append((clip["clip_id"], feats, labels))
    return clips


def boundary_target(labels: np.ndarray, dilate: int) -> np.ndarray:
    """class-agnostic 工程境界の教師信号。y[t]≠y[t-1] を 1、±dilate 近傍も 1（float32, shape=(T,)）。

    dilate は **教師信号のみ**を柔らかくする（学習ターゲットの過疎対策）。モデル入力・推論は
    現在≤t のみ参照する因果構造なので、ターゲット側の近傍膨張は因果性を破らない。
    """
    T = len(labels)
    b = np.zeros(T, dtype=np.float32)
    if T < 2:
        return b
    change = np.nonzero(labels[1:] != labels[:-1])[0] + 1  # 遷移が起きるフレーム t
    for t in change:
        lo = max(0, t - dilate)
        hi = min(T, t + dilate + 1)
        b[lo:hi] = 1.0
    return b


# ---------------------------------------------------------------------------
# モデル: 共有 stage-1 trunk + phase head（既存 TeCNO と同一）+ boundary head
# ---------------------------------------------------------------------------
class TeCNOBoundary(nn.Module):
    """TeCNO（causal MS-TCN）に class-agnostic boundary head を追加。

    stage-1 の trunk（conv_in + dilated layers, num_f_maps ch）を **phase head と共有**し、
    そこから boundary logit(1ch) を分岐する。boundary 監督の勾配が共有 trunk に流れ、phase 特徴を
    時間的に安定化させる（役割分離・§4.1）。refine stage 群は TeCNO と同一（phase softmax を精緻化）。
    boundary weight→0 かつ plain decode のとき phase 経路は素 TeCNO と同一計算。
    """

    def __init__(self, num_stages: int, num_layers: int, num_f_maps: int,
                 in_dim: int, num_classes: int, dropout: float = 0.5) -> None:
        super().__init__()
        self.num_stages = num_stages
        self.num_classes = num_classes
        # stage1 は TeCNO と同一構造（conv_in→dilated layers→conv_out(9)）
        self.stage1 = SingleStageTCN(num_layers, num_f_maps, in_dim, num_classes, dropout)
        self.refine_stages = nn.ModuleList(
            [SingleStageTCN(num_layers, num_f_maps, num_classes, num_classes, dropout)
             for _ in range(num_stages - 1)]
        )
        # boundary head: stage1 の 64ch trunk 特徴（conv_out 前）から 1ch を分岐（因果・1x1）
        self.boundary_out = nn.Conv1d(num_f_maps, 1, kernel_size=1)

    def _stage1_trunk(self, x: torch.Tensor) -> torch.Tensor:
        out = self.stage1.conv_in(x)
        for layer in self.stage1.layers:
            out = layer(out)
        return out  # (B, num_f_maps, T)

    def forward(self, x: torch.Tensor) -> tuple[list[torch.Tensor], torch.Tensor]:
        """x:(B,in_dim,T) → (phase 各 stage logits [(B,C,T),...], boundary logit (B,1,T))。"""
        trunk = self._stage1_trunk(x)             # 共有 trunk 特徴
        out = self.stage1.conv_out(trunk)         # stage1 phase logits
        phase_outputs = [out]
        for stage in self.refine_stages:
            out = stage(F.softmax(out, dim=1))
            phase_outputs.append(out)
        boundary_logit = self.boundary_out(trunk)  # (B,1,T)
        return phase_outputs, boundary_logit


def smoothing_loss(logits: torch.Tensor) -> torch.Tensor:
    """MS-TCN の T-MSE 平滑化損失（S4/B2a/T1a と同一定義）。"""
    ls = F.log_softmax(logits, dim=1)
    mse = F.mse_loss(ls[:, :, 1:], ls[:, :, :-1], reduction="none")
    return torch.clamp(mse, max=16.0).mean()


def sticky_decode(logits: np.ndarray, boundary_prob: np.ndarray, tau: float) -> np.ndarray:
    """因果 boundary-gated sticky decode。工程遷移は boundary 確信度 ≥ τ のときのみ受理。

    logits:(C,T) 最終 stage・boundary_prob:(T,)。出力 preds:(T,)。時刻 t は ≤t のみ参照（因果）。
    """
    C, T = logits.shape
    am = logits.argmax(0)
    preds = np.empty(T, dtype=np.int64)
    p = int(am[0])
    preds[0] = p
    for t in range(1, T):
        a = int(am[t])
        if a == p:
            preds[t] = p
        elif boundary_prob[t] >= tau:  # 高確信の境界でのみ遷移を受理
            preds[t] = a
            p = a
        else:                          # 低確信の単発 flip を抑制（前状態を保持）
            preds[t] = p
    return preds


@torch.no_grad()
def evaluate(model: nn.Module, clips, device, tau: float) -> tuple[dict, dict]:
    """plain（per-frame argmax）と sticky（因果 boundary-gated）両方の metrics を返す。"""
    model.eval()
    m_plain = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    m_sticky = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    for clip_id, feats, labels in clips:
        x = torch.from_numpy(feats).T.unsqueeze(0).to(device)  # (1,in_dim,T)
        phase_outs, b_logit = model(x)
        lg = phase_outs[-1][0].cpu().numpy()                   # (C,T)
        bp = torch.sigmoid(b_logit[0, 0]).cpu().numpy()        # (T,)
        m_plain.update(lg.argmax(0), labels, video_id=clip_id)
        m_sticky.update(sticky_decode(lg, bp, tau), labels, video_id=clip_id)
    return m_plain.compute(), m_sticky.compute()


DESC = "t1a_boundary"


def _auto_pos_weight(clips, dilate: int) -> float:
    """train 全体の boundary 密度から BCE pos_weight = #neg/#pos を算出（過疎補正・上限 50）。"""
    pos = tot = 0
    for _, _, labels in clips:
        b = boundary_target(labels, dilate)
        pos += int(b.sum())
        tot += len(b)
    neg = tot - pos
    if pos == 0:
        return 1.0
    return float(min(neg / pos, 50.0))


def _build_cfg(args, server_name, in_dim, n_train, n_val, pos_weight) -> dict:
    return {
        "experiment": {"category": "transfer", "step": args.description, "description": args.description},
        "seed": args.seed,
        "frozen_source": {
            "detector": "relation_detr", "seed": 42, "backbone": "resnet50",
            "gap_cache": str(GAP_DIR.relative_to(PROJ)),
            "region_cache": str(REGION_DIR.relative_to(PROJ)),
        },
        "method": {
            "name": "t1a_boundary_head",
            "system": "②feature_level/object-token + boundary-modeling",
            "ref": "COUPLING_IMPROVEMENT_RECOMMENDATIONS §4.1/§8 (ASRF/MS-TCN++ boundary head)",
            "direction": "det->phase",
            "coupling": "regiontoken_concat_gap + causal_boundary_head",
            "base": "t1a_regiontoken (in_dim=5888)",
            "boundary_head": "shared_stage1_trunk -> conv1d(num_f_maps->1), class_agnostic, causal",
            "boundary_target": f"phase-change ±{args.boundary_dilate} dilation (supervision only)",
            "boundary_weight": args.boundary_weight,
            "boundary_pos_weight": pos_weight,
            "boundary_tau_sticky": args.boundary_tau,
            "region_dim": REGION_DIM,
            "neck": None,
            "grad_crossing": False,
        },
        "model": {
            "temporal_head": "tecno+boundary", "num_stages": args.num_stages,
            "num_layers": args.num_layers, "num_f_maps": args.num_f_maps,
            "in_dim": in_dim, "num_phases": len(CLASS_NAMES), "causal": True,
        },
        "train": {
            "epochs": args.epochs, "lr": args.lr, "weight_decay": args.weight_decay,
            "freeze_backbone": True, "smoothing_weight": 0.15,
        },
        "data": {"n_train_clips": n_train, "n_val_clips": n_val},
        "delta": {
            "phase_denominator": "t1a_regiontoken base (同一環境 efros で再学習・paired)",
            "primary_metric": "edit_score / seg_f1@{10,25,50} (over-segmentation)",
            "maintain_metric": "accuracy / macro_f1",
            "note": "Δ = (T1a-Boundary − T1a base[同env]) の per-seed paired-σ（§10.1）。"
            "plain=正則化効果 / sticky=+因果 boundary-gated decode。",
        },
        "server_name": server_name,
    }


def _build_phase_recipe(args, server_name, in_dim) -> dict:
    test_cfg = {
        "task": "phase", **PHASE_EVAL_PROTOCOL,
        "backbone": "relation_detr_resnet50_frozen_seed42",
        "temporal_head": "tecno+boundary",
        "num_stages": args.num_stages, "num_layers": args.num_layers,
        "num_f_maps": args.num_f_maps, "in_dim": in_dim,
        "coupling": "t1a_regiontoken_concat_gap+boundary_head", "region_dim": REGION_DIM,
    }
    return build_eval_recipe(
        test_cfg=test_cfg, split_sizes=PAPER_SPLIT_SIZES, server_name=server_name,
        gpu_count=1, effective_batch_size=1, lr_scaling="none",
    )


def _write_notes(exp_dir, args, best, sticky, server_name, in_dim, pos_weight) -> None:
    note = (
        f"# T1a-Boundary（region-token→工程 + 因果 boundary head・over-seg / edit-score 改善）\n\n"
        f"STEP C 改善提案書 §4.1/§8。T1a base の共有 stage-1 trunk から class-agnostic boundary head を分岐し、"
        f"phase-change 教師（±{args.boundary_dilate}）で BCE 監督。online/causal（未来不使用）。\n\n"
        f"## 結果（best @epoch {best.get('epoch')}・val）\n"
        f"### plain decode（per-frame argmax = T1a base と同一推論）\n"
        f"- accuracy={best['phase_accuracy']:.4f} / macro_f1={best['phase_macro_f1']:.4f}\n"
        f"- edit={best['phase_edit_score']:.2f} / seg_f1@10/25/50="
        f"{best['phase_seg_f1_10']:.3f}/{best['phase_seg_f1_25']:.3f}/{best['phase_seg_f1_50']:.3f}\n"
        f"### sticky decode（因果 boundary-gated・τ={args.boundary_tau}）\n"
        f"- accuracy={sticky['phase_accuracy']:.4f} / macro_f1={sticky['phase_macro_f1']:.4f}\n"
        f"- edit={sticky['phase_edit_score']:.2f} / seg_f1@10/25/50="
        f"{sticky['phase_seg_f1_10']:.3f}/{sticky['phase_seg_f1_25']:.3f}/{sticky['phase_seg_f1_50']:.3f}\n\n"
        f"## 構成\n- seed={args.seed} epochs={args.epochs} lr={args.lr} in_dim={in_dim}(=2048+3840) "
        f"stages={args.num_stages} layers={args.num_layers} f_maps={args.num_f_maps}\n"
        f"- boundary: weight={args.boundary_weight} pos_weight={pos_weight:.2f} dilate={args.boundary_dilate} "
        f"tau={args.boundary_tau}\n"
        f"- server={server_name} / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)\n\n"
        f"## Δ\n- Δ = (T1a-Boundary − T1a base[同env efros])。主指標 edit/seg-F1、維持 acc/macro-F1。\n"
        f"- 3-seed 揃ったら paired-σ(対seed差) §10.1 判定。plain=trunk 正則化 / sticky=+因果 decode。\n"
    )
    (exp_dir / "notes.md").write_text(note, encoding="utf-8")


def train(args) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    in_dim = REGION_DIM if args.region_only else GAP_DIM + REGION_DIM
    train_clips = load_clips("train", args.region_only)
    val_clips = load_clips("val", args.region_only)
    if args.smoke:
        train_clips, val_clips = train_clips[:3], val_clips[:2]

    pos_weight = args.boundary_pos_weight if args.boundary_pos_weight > 0 else _auto_pos_weight(train_clips, args.boundary_dilate)
    print(
        f"[t1a-bd] train clips={len(train_clips)}  val clips={len(val_clips)}  in_dim={in_dim}  "
        f"classes={len(CLASS_NAMES)}  boundary(w={args.boundary_weight} pos_w={pos_weight:.2f} "
        f"dilate={args.boundary_dilate} tau={args.boundary_tau})  device={device}"
    )

    server_name = resolve_server_name(None)
    manager = exp_dir = None
    if not args.smoke and not args.no_evidence:
        manager = ExperimentManager(
            base_dir=str(PROJ / "experiments"), category="transfer",
            step=args.description, description=args.description, seed=args.seed,
        )
        manager.setup(_build_cfg(args, server_name, in_dim, len(train_clips), len(val_clips), pos_weight))
        exp_dir = manager.exp_dir
        print(f"[t1a-bd] evidence dir: {exp_dir}")

    model = TeCNOBoundary(
        num_stages=args.num_stages, num_layers=args.num_layers, num_f_maps=args.num_f_maps,
        in_dim=in_dim, num_classes=len(CLASS_NAMES),
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()
    bce = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pos_weight], device=device))

    from egosurgery.utils import tracking  # W&B（無認証 no-op）

    tracking.init(
        f"{args.description}_seed{args.seed}", group="B", job_type="t1a_boundary",
        config={"seed": args.seed, "lr": args.lr, "epochs": args.epochs, "in_dim": in_dim,
                "boundary_weight": args.boundary_weight, "method": "t1a_boundary_head"},
    )

    best = {"phase_accuracy": -1.0}
    best_sticky: dict = {}
    for epoch in range(args.epochs):
        model.train()
        random.shuffle(train_clips)
        ep_loss = ep_bd = 0.0
        for clip_id, feats, labels in train_clips:
            x = torch.from_numpy(feats).T.unsqueeze(0).to(device)
            y = torch.from_numpy(labels).to(device)
            bt = torch.from_numpy(boundary_target(labels, args.boundary_dilate)).to(device)
            phase_outs, b_logit = model(x)
            phase_loss = sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in phase_outs)
            bd_loss = bce(b_logit[0, 0], bt)
            loss = phase_loss + args.boundary_weight * bd_loss
            opt.zero_grad()
            loss.backward()
            opt.step()
            ep_loss += float(loss)
            ep_bd += float(bd_loss)
        val_plain, val_sticky = evaluate(model, val_clips, device, args.boundary_tau)
        print(
            f"[t1a-bd][ep {epoch + 1}/{args.epochs}] loss={ep_loss / max(len(train_clips),1):.4f} "
            f"bd={ep_bd / max(len(train_clips),1):.4f} || "
            f"plain acc={val_plain['phase_accuracy']:.4f} edit={val_plain['phase_edit_score']:.2f} "
            f"segF1@50={val_plain['phase_seg_f1_50']:.3f} || "
            f"sticky acc={val_sticky['phase_accuracy']:.4f} edit={val_sticky['phase_edit_score']:.2f} "
            f"segF1@50={val_sticky['phase_seg_f1_50']:.3f}"
        )
        tracking.log(
            {"train/loss": ep_loss / max(len(train_clips), 1),
             "train/boundary_loss": ep_bd / max(len(train_clips), 1),
             "val/phase_accuracy": val_plain["phase_accuracy"],
             "val/edit_plain": val_plain["phase_edit_score"],
             "val/edit_sticky": val_sticky["phase_edit_score"],
             "val/seg_f1_50_sticky": val_sticky["phase_seg_f1_50"]},
            step=epoch,
        )
        # モデル選択は plain val acc（T1a base と同一の選択規則 → acc 選択のバイアスを避ける）
        if val_plain["phase_accuracy"] > best["phase_accuracy"]:
            best = {**val_plain, "epoch": epoch + 1}
            best_sticky = dict(val_sticky)
            if exp_dir is not None:
                torch.save({"model": model.state_dict(), "epoch": epoch + 1,
                            "val_plain": val_plain, "val_sticky": val_sticky},
                           exp_dir / "checkpoints" / "best_tecno_boundary.pth")
    print(
        f"[t1a-bd] best @epoch {best.get('epoch')}: plain acc={best['phase_accuracy']:.4f} "
        f"edit={best['phase_edit_score']:.2f} | sticky edit={best_sticky.get('phase_edit_score', float('nan')):.2f}"
    )

    if manager is not None:
        per_class = best.get("phase_per_class_f1", {})
        # 主 metrics = plain（acc/F1/edit を T1a base[plain] と apples-to-apples 比較）
        scalars = {k: v for k, v in best.items() if isinstance(v, (int, float))}
        # sticky（因果 decode）を _sticky 接尾辞で併記
        for k, v in best_sticky.items():
            if isinstance(v, (int, float)):
                scalars[f"{k}_sticky"] = v
        manager.log_eval_recipe(_build_phase_recipe(args, server_name, in_dim))
        manager.log_metrics(scalars)
        manager.log_per_class_ap(per_class)
        _write_notes(exp_dir, args, best, best_sticky, server_name, in_dim, pos_weight)
        print(f"[t1a-bd] evidence written -> {exp_dir}")
        from egosurgery.utils.research_logger import ResearchLogger

        ResearchLogger(cfg=None, manager=manager).log_run(
            status="completed", step="B", tier="must",
            primary_metric="phase edit/seg-F1 (over-seg) + acc/macro-F1 (online_causal, plain & sticky)",
            extra_result_text="②T1a + 因果 boundary head。edit-score 改善を狙う（vs T1a base 同env・paired-σ）",
        )
    tracking.finish()
    best["_sticky"] = best_sticky
    return best


def parse_args():
    p = argparse.ArgumentParser(description="T1a + causal boundary head (over-segmentation / edit-score 改善).")
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--num-stages", type=int, default=2)
    p.add_argument("--num-layers", type=int, default=8)
    p.add_argument("--num-f-maps", type=int, default=64)
    p.add_argument("--region-only", action="store_true", help="GAP と連結せず region のみ（別解）")
    p.add_argument("--boundary-weight", type=float, default=1.0, help="boundary BCE の loss 重み λ_b")
    p.add_argument("--boundary-dilate", type=int, default=1,
                   help="boundary 教師の±近傍膨張（教師のみ・因果性は保持）")
    p.add_argument("--boundary-tau", type=float, default=0.5,
                   help="sticky decode で遷移受理する boundary 確信度しきい値")
    p.add_argument("--boundary-pos-weight", type=float, default=0.0,
                   help="BCE pos_weight（0=train 密度から自動算出）")
    p.add_argument("--smoke", action="store_true", help="3 epoch・少 clip で疎通確認（証跡なし）")
    p.add_argument("--no-evidence", action="store_true", help="証跡を残さない（配線検証用）")
    p.add_argument("--description", type=str, default=DESC,
                   help="ExperimentManager の step/description 識別子（既定: t1a_boundary）")
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    if a.smoke:
        a.epochs = 3
    train(a)

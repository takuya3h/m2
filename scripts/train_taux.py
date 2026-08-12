#!/usr/bin/env python
"""T-aux 系統② region-token→工程 の時系列軸スイープ（T-1〜6）= 核と時間加工の切り分け本体。

`train_t1a.py`（region-token 3840 ⊕ GAP 2048 = 5888 → 素 causal TeCNO）の**派生**で、
凍結 Relation-DETR seed42 の object-query 埋め込み（region token）を主入力に据えたまま、
工程認識の **時系列の軸**だけを 2 系統で振る:

  (問いB・核比較)  --temporal-kernel {tecno,mingru,mamba}  … TeCNO / minGRU / Mamba の差し替え（T-4/5/6）
  (問いA・時間加工) --temporal-feature {none,movavg,delta,window} + --temporal-k K … 注入信号の時間符号化（T-1/2/3）

    入力 = concat([ GAP(C5) 2048 , f_temporal(region-token 3840) ( , tool-presence 15 ) ])  → 選択核

公平比較（交絡回避・§6 / §8.1）:
    - 問いB は **temporal_feature=none 固定**で kernel だけを変える（核以外を動かさない）。
    - 問いA は **temporal_kernel=tecno 固定**で temporal_feature だけを変える（核を動かさない）。
    - 両者を同時に動かして「核 × 時間加工」を交絡させない。GAP（backbone frame 特徴）は常に生。
      時間加工は**注入信号（既定 region-token, --temporal-target で tool も可）にのみ**適用する。

時間加工はすべて各 clip 内で**厳密 causal**（未来非参照。先頭境界は複製 pad）:
    movavg = 過去 k フレーム（現在含む）移動平均（次元不変）
    delta  = フレーム間差分 sig[t]-sig[t-1]（出現+/消失-。先頭 delta=0。次元不変）
    window = 過去 k フレーム（現在含む）stack（次元 ×k）
    → 次元が変わる window は in_dim を正しく再計算し、実データの特徴次元と一致検証する（Fail Loud）。

土台（分母）= S4 base（素 TeCNO on GAP = 0.8986±0.0028）。Δ_phase = (T-aux − S4 base)。
問いB では「核の違い」、問いA では「時間加工の違い」が Δ に効くかを §10.1 paired-σ で判定する。

入力（train_t1a.py と同一 loader 規約・同一 npz キャッシュ）:
    data/processed/stage1_features/<frozen_src>/{split}_gap.npz              （frame_ids, features=GAP2048）
    data/processed/t1a_regiontoken/<frozen_src>/{split}_regiontoken.npz      （frame_ids, region=3840）
    data/processed/b2a_detsignal/<frozen_src>/{split}_toolpresence.npz       （--add-toolpresence pred）
    data/processed/oracle_toolpresence/{split}_oracletool.npz               （--add-toolpresence oracle）
    data/processed/phase_manifest/{split}.json                              （clip 時系列順 + label）

本体 .venv で実行（Relation-DETR 非依存・キャッシュのみ読む。S4 と同一の作法・ハイパー）:
  .venv/bin/python scripts/train_taux.py --temporal-kernel mamba  --temporal-feature none          # 問いB（核比較）
  .venv/bin/python scripts/train_taux.py --temporal-kernel tecno  --temporal-feature window --temporal-k 3  # 問いA（時間加工）
  .venv/bin/python scripts/train_taux.py --smoke                                                   # 疎通確認（証跡なし）
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
from egosurgery.models.heads.mamba_head import MambaHead  # noqa: E402
from egosurgery.models.heads.mingru_head import MinGRUHead  # noqa: E402
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
TOOLPRES_DIR = PROJ / "data" / "processed" / "b2a_detsignal" / FROZEN_SRC
ORACLE_TOOL_DIR = PROJ / "data" / "processed" / "oracle_toolpresence"
MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())
GAP_DIM = 2048
REGION_DIM = 15 * 256  # 3840
TOOLPRES_DIM = 15

# --temporal-kernel → ヘッドクラス（いずれも TeCNO と同一の構成子・forward 契約の drop-in）
KERNELS: dict[str, type[nn.Module]] = {
    "tecno": TeCNO,
    "mingru": MinGRUHead,
    "mamba": MambaHead,
}


# --------------------------------------------------------------------------- #
# 時間加工（問いA・T-1/2/3）: 注入信号の clip 内 causal 符号化（未来非参照）
# --------------------------------------------------------------------------- #
def _causal_movavg(sig: np.ndarray, k: int) -> np.ndarray:
    """過去 k フレーム（現在含む）の causal 移動平均（次元不変）。

    先頭境界は利用可能な過去のみで平均（複製 pad 相当・未来非参照）。cumsum で O(T·D)。
    """
    if k <= 1:
        return sig.astype(np.float32)
    t_len = sig.shape[0]
    pad = np.zeros((1, sig.shape[1]), dtype=np.float64)
    csum = np.cumsum(np.concatenate([pad, sig.astype(np.float64)], axis=0), axis=0)  # (T+1, D)
    idx = np.arange(1, t_len + 1)
    lo = np.maximum(idx - k, 0)
    win = csum[idx] - csum[lo]                 # (t-k, t] の和（causal）
    cnt = (idx - lo).reshape(-1, 1)            # 実際に平均した要素数（先頭は < k）
    return (win / cnt).astype(np.float32)


def _causal_delta(sig: np.ndarray) -> np.ndarray:
    """フレーム間差分 sig[t]-sig[t-1]（出現+/消失-。次元不変）。

    先頭は複製 pad → delta[0]=0（未来非参照。過去方向にのみ依存）。
    """
    d = np.zeros_like(sig, dtype=np.float32)
    if sig.shape[0] > 1:
        d[1:] = sig[1:].astype(np.float32) - sig[:-1].astype(np.float32)
    return d


def _causal_window(sig: np.ndarray, k: int) -> np.ndarray:
    """過去 k フレーム（現在含む）を stack: out[t]=concat(sig[t-k+1], …, sig[t])（次元 ×k）。

    先頭境界は sig[0] を複製 pad（過去方向へ複製・未来非参照）。並び順は古い→新しい。
    """
    if k <= 1:
        return sig.astype(np.float32)
    parts = []
    for lag in range(k - 1, -1, -1):           # lag=k-1（最古）→ 0（現在）
        if lag == 0:
            parts.append(sig.astype(np.float32))
        else:
            shifted = np.empty_like(sig, dtype=np.float32)
            shifted[:lag] = sig[0]             # 先頭を過去方向に複製 pad
            shifted[lag:] = sig[:-lag]
            parts.append(shifted)
    return np.concatenate(parts, axis=1).astype(np.float32)  # (T, k*D)


def apply_temporal_feature(sig: np.ndarray, feature: str, k: int) -> np.ndarray:
    """注入信号 (T, D) に時間加工を適用して (T, D') を返す（厳密 causal）。"""
    if feature == "none":
        return sig.astype(np.float32)
    if feature == "movavg":
        return _causal_movavg(sig, k)
    if feature == "delta":
        return _causal_delta(sig)
    if feature == "window":
        return _causal_window(sig, k)
    raise ValueError(f"[taux] 未知の temporal-feature: {feature!r}")


def temporal_out_dim(base_dim: int, feature: str, k: int) -> int:
    """時間加工後の次元数（window のみ ×k、他は不変）。"""
    return base_dim * k if feature == "window" and k > 1 else base_dim


def compute_in_dim(
    region_only: bool,
    temporal_feature: str,
    temporal_k: int,
    temporal_target: str,
    add_toolpresence: bool,
) -> int:
    """入力連結後の in_dim を解析的に算出（load 後に実データ次元と一致検証する）。"""
    reg_dim = (
        temporal_out_dim(REGION_DIM, temporal_feature, temporal_k)
        if temporal_target == "region"
        else REGION_DIM
    )
    if region_only:
        return reg_dim
    tool_dim = 0
    if add_toolpresence:
        tool_dim = (
            temporal_out_dim(TOOLPRES_DIM, temporal_feature, temporal_k)
            if temporal_target == "tool"
            else TOOLPRES_DIM
        )
    return GAP_DIM + reg_dim + tool_dim


# --------------------------------------------------------------------------- #
# データ読み込み（train_t1a.py と同一規約: frame_id キー化・Fail Loud・shuffle control）
# --------------------------------------------------------------------------- #
def load_clips(
    split: str,
    region_only: bool,
    temporal_feature: str = "none",
    temporal_k: int = 3,
    temporal_target: str = "region",
    shuffle_region: bool = False,
    shuffle_seed: int = 12345,
    add_toolpresence: bool = False,
    toolpresence_source: str = "pred",
) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """(clip_id, feats (T, in_dim), labels (T,)) を返す（時系列順）。

    GAP・region（・tool）を frame_id でキー化して clip フレーム順に整列し、注入信号
    （既定 region-token, --temporal-target で tool）に **clip 内 causal 時間加工**を掛けてから
    連結する。GAP（backbone frame 特徴）は常に生。どれかに frame が無ければ整合不良として
    Fail Loud（KeyError）— ダミー補完しない。

    `shuffle_region=True`（§18.4 L2-2 shuffle control）: region-token の frame 対応を破壊して
    assign。phase と region の真の相関が壊れるため、Δ_phase が消えれば region 情報の真の寄与を
    実証する positive control 反証。splits 間で独立した RandomState を使い再現性を保つ。
    """
    g = np.load(GAP_DIR / f"{split}_gap.npz")
    gap_all = g["features"]  # NpzFile 遅延展開: 一度だけ取り出す
    gap_by_frame = {str(fid): gap_all[i] for i, fid in enumerate(g["frame_ids"])}

    r = np.load(REGION_DIR / f"{split}_regiontoken.npz")
    reg_all = r["region"]
    reg_by_frame = {str(fid): reg_all[i] for i, fid in enumerate(r["frame_ids"])}

    if shuffle_region:
        rng = np.random.RandomState(shuffle_seed)
        keys = list(reg_by_frame.keys())
        values = list(reg_by_frame.values())
        rng.shuffle(values)
        reg_by_frame = dict(zip(keys, values, strict=False))

    tool_by_frame: dict = {}
    if add_toolpresence:
        if toolpresence_source == "oracle":
            t = np.load(ORACLE_TOOL_DIR / f"{split}_oracletool.npz")
        else:
            t = np.load(TOOLPRES_DIR / f"{split}_toolpresence.npz")
        tp_all = t["signal"]
        tool_by_frame = {str(fid): tp_all[i] for i, fid in enumerate(t["frame_ids"])}

    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        frames = clip["frames"]
        gap_rows, reg_rows, tool_rows = [], [], []
        for fr in frames:
            fid = fr["frame"]
            if fid not in reg_by_frame:
                raise KeyError(f"[taux] region-token に frame_id 欠落: {fid} ({split})")
            reg_rows.append(reg_by_frame[fid])
            if not region_only:
                if fid not in gap_by_frame:
                    raise KeyError(f"[taux] GAP 特徴に frame_id 欠落: {fid} ({split})")
                gap_rows.append(gap_by_frame[fid])
            if add_toolpresence:
                if fid not in tool_by_frame:
                    raise KeyError(f"[taux] tool-presence に frame_id 欠落: {fid} ({split})")
                tool_rows.append(tool_by_frame[fid])

        reg_seq = np.stack(reg_rows).astype(np.float32)  # (T, 3840)
        if temporal_target == "region":
            reg_seq = apply_temporal_feature(reg_seq, temporal_feature, temporal_k)

        parts_seq = []
        if not region_only:
            parts_seq.append(np.stack(gap_rows).astype(np.float32))  # (T, 2048) 生
        parts_seq.append(reg_seq)
        if add_toolpresence:
            tool_seq = np.stack(tool_rows).astype(np.float32)  # (T, 15)
            if temporal_target == "tool":
                tool_seq = apply_temporal_feature(tool_seq, temporal_feature, temporal_k)
            parts_seq.append(tool_seq)

        feats = np.concatenate(parts_seq, axis=1).astype(np.float32)  # (T, in_dim)
        labels = np.asarray([fr["label"] for fr in frames], dtype=np.int64)
        clips.append((clip["clip_id"], feats, labels))
    return clips


def smoothing_loss(logits: torch.Tensor) -> torch.Tensor:
    """MS-TCN の T-MSE 平滑化損失（S4/B2a/T1a と同一定義）。"""
    ls = F.log_softmax(logits, dim=1)
    mse = F.mse_loss(ls[:, :, 1:], ls[:, :, :-1], reduction="none")
    return torch.clamp(mse, max=16.0).mean()


@torch.no_grad()
def evaluate(model: nn.Module, clips, device) -> dict:
    model.eval()
    metrics = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    for clip_id, feats, labels in clips:
        x = torch.from_numpy(feats).T.unsqueeze(0).to(device)  # (1, in_dim, T)
        logits = model(x)[-1]                                   # 最終ステージ (1, C, T)
        preds = logits[0].argmax(0).cpu().numpy()
        metrics.update(preds, labels, video_id=clip_id)
    return metrics.compute()


def _method_tag(args) -> str:
    """ExperimentManager step/description。既定は 'taux_<kernel>_<feature>k<K>'（非既定は接尾辞）。"""
    tag = f"taux_{args.temporal_kernel}_{args.temporal_feature}k{args.temporal_k}"
    if args.temporal_target != "region":
        tag += f"_tgt-{args.temporal_target}"
    if args.region_only:
        tag += "_regiononly"
    if args.add_toolpresence:
        tag += f"_withtool{args.toolpresence_source}"
    if args.region_shuffle:
        tag += "_shuffle"
    return tag


def _build_cfg(args, server_name: str, in_dim: int, n_train: int, n_val: int) -> dict:
    return {
        "experiment": {
            "category": "transfer",
            "step": "taux_temporal",
            "description": _method_tag(args),
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
            "name": "taux_region_to_phase_temporal",
            "system": "②feature_level/object-token",
            "ref": "TAPIS/GraSP (MedIA 2025); TeCNO (MICCAI 2020); minGRU (arXiv:2410.01201); Mamba (arXiv:2312.00752)",
            "direction": "det->phase",
            "coupling": (
                "regiontoken_only" if args.region_only else "regiontoken_concat_gap"
            ),
            "region_repr": "per_class_256d_score_weighted",
            "region_dim": REGION_DIM,
            "temporal_kernel": args.temporal_kernel,
            "temporal_feature": args.temporal_feature,
            "temporal_k": args.temporal_k,
            "temporal_target": args.temporal_target,
            "add_toolpresence": args.add_toolpresence,
            "toolpresence_source": args.toolpresence_source if args.add_toolpresence else None,
            "neck": None,
            "grad_crossing": False,
        },
        "model": {
            "temporal_head": args.temporal_kernel,
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
            "denominator_value_lecun": "0.8986±0.0028",
            "note": (
                "Δ_phase = (T-aux − S4 base 0.8986±0.0028). 問いB は temporal_feature=none 固定で "
                "kernel を変え、問いA は temporal_kernel=tecno 固定で feature を変える（核と時間加工を交絡させない）。"
            ),
        },
        "server_name": server_name,
    }


def _build_phase_recipe(args, server_name: str, in_dim: int) -> dict:
    test_cfg = {
        "task": "phase",
        **PHASE_EVAL_PROTOCOL,
        "backbone": "relation_detr_resnet50_frozen_seed42",
        "temporal_head": args.temporal_kernel,
        "num_stages": args.num_stages,
        "num_layers": args.num_layers,
        "num_f_maps": args.num_f_maps,
        "in_dim": in_dim,
        "coupling": (
            "taux_regiontoken_only" if args.region_only else "taux_regiontoken_concat_gap"
        ),
        "region_dim": REGION_DIM,
        "temporal_feature": args.temporal_feature,
        "temporal_k": args.temporal_k,
        "temporal_target": args.temporal_target,
    }
    return build_eval_recipe(
        test_cfg=test_cfg,
        split_sizes=PAPER_SPLIT_SIZES,
        server_name=server_name,
        gpu_count=1,
        effective_batch_size=1,
        lr_scaling="none",
    )


def _write_notes(exp_dir: Path, args, best: dict, server_name: str, in_dim: int) -> None:
    note = (
        f"# T-aux 系統② region-token→工程 時系列軸スイープ（T-1〜6）\n\n"
        f"凍結 Relation-DETR seed42 の object-query 埋め込み（クラス別 256-d, score 加重）を主入力に、"
        f"工程認識の時系列軸のみを振る。GAP({GAP_DIM}) は常に生、時間加工は注入信号"
        f"（target={args.temporal_target}）にのみ適用。online/causal（未来不使用・先頭は複製 pad）。\n\n"
        f"- temporal_kernel = **{args.temporal_kernel}**（tecno=causal dilated TCN / mingru=線形再帰 / mamba=選択的 SSM）\n"
        f"- temporal_feature = **{args.temporal_feature}**（k={args.temporal_k}; movavg=移動平均 / delta=差分 / window=stack×k / none=生）\n\n"
        f"## 公平比較（交絡回避・§6 / §8.1）\n"
        f"- 問いB（核比較）: **temporal_feature=none 固定**で kernel だけを変える。\n"
        f"- 問いA（時間加工）: **temporal_kernel=tecno 固定**で temporal_feature だけを変える。\n"
        f"- 両者を同時に動かして「核 × 時間加工」を交絡させない。GAP は常に生・neck 無し。\n\n"
        f"## 結果（best @epoch {best.get('epoch')}）\n"
        f"- accuracy={best['phase_accuracy']:.4f} / macro_f1={best['phase_macro_f1']:.4f}\n"
        f"- edit={best['phase_edit_score']:.2f} / seg_f1@10/25/50="
        f"{best['phase_seg_f1_10']:.2f}/{best['phase_seg_f1_25']:.2f}/{best['phase_seg_f1_50']:.2f}\n\n"
        f"## 構成\n- seed={args.seed} epochs={args.epochs} lr={args.lr} in_dim={in_dim} "
        f"stages={args.num_stages} layers={args.num_layers} f_maps={args.num_f_maps} "
        f"region_only={args.region_only} add_toolpresence={args.add_toolpresence}\n"
        f"- server={server_name} / eval recipe=online_causal+jaccard_strict (PHASE_EVAL_PROTOCOL)\n\n"
        f"## Δ\n- Δ_phase = (T-aux − S4 base 0.8986±0.0028[lecun])。同一土台（凍結backbone/GAP/recipe/seed・neck無）。\n"
        f"- **別サーバー実行時**: 分母は lecun 値流用、サーバー差を §8.0 明文化。\n"
        f"- 3-seed 揃ったら paired-σ(対seed差) で §10.1 判定（|Δ|>paired-σ かつ同符号で有意）。\n"
    )
    (exp_dir / "notes.md").write_text(note, encoding="utf-8")


def train(args) -> dict:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    # target=tool の妥当性検証（region-only では tool を注入しない / add-toolpresence 必須）
    if args.temporal_target == "tool":
        if args.region_only:
            raise ValueError("[taux] --temporal-target tool は --region-only と併用不可（tool 信号が入力に無い）")
        if not args.add_toolpresence:
            raise ValueError("[taux] --temporal-target tool は --add-toolpresence が必要")

    in_dim = compute_in_dim(
        args.region_only, args.temporal_feature, args.temporal_k,
        args.temporal_target, args.add_toolpresence,
    )

    def _load(split):
        return load_clips(
            split,
            region_only=args.region_only,
            temporal_feature=args.temporal_feature,
            temporal_k=args.temporal_k,
            temporal_target=args.temporal_target,
            shuffle_region=args.region_shuffle,
            shuffle_seed=args.shuffle_seed if split == "train" else args.shuffle_seed + 1,
            add_toolpresence=args.add_toolpresence,
            toolpresence_source=args.toolpresence_source,
        )

    train_clips, val_clips = _load("train"), _load("val")
    if args.smoke:
        train_clips, val_clips = train_clips[:3], val_clips[:2]

    # 解析 in_dim と実データ次元の一致を Fail Loud で検証（window の ×k 再計算含む）
    got_dim = int(train_clips[0][1].shape[1])
    if got_dim != in_dim:
        raise RuntimeError(
            f"[taux] in_dim 不整合: 解析値 {in_dim} != 実データ {got_dim}"
            f"（feature={args.temporal_feature} k={args.temporal_k} target={args.temporal_target}）"
        )
    print(
        f"[taux] train clips={len(train_clips)}  val clips={len(val_clips)}  in_dim={in_dim}  "
        f"kernel={args.temporal_kernel}  feature={args.temporal_feature}  k={args.temporal_k}  "
        f"target={args.temporal_target}  region_only={args.region_only}  classes={len(CLASS_NAMES)}  device={device}"
    )

    server_name = resolve_server_name(None)
    manager = exp_dir = None
    desc = args.description_override or _method_tag(args)
    if not args.smoke and not args.no_evidence:
        manager = ExperimentManager(
            base_dir=str(PROJ / "experiments"), category="transfer",
            step=desc, description=desc, seed=args.seed,
        )
        manager.setup(_build_cfg(args, server_name, in_dim, len(train_clips), len(val_clips)))
        exp_dir = manager.exp_dir
        print(f"[taux] evidence dir: {exp_dir}")

    head_cls = KERNELS[args.temporal_kernel]
    model = head_cls(
        num_stages=args.num_stages,
        num_layers=args.num_layers,
        num_f_maps=args.num_f_maps,
        in_dim=in_dim,
        num_classes=len(CLASS_NAMES),
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    ce = nn.CrossEntropyLoss()

    from egosurgery.utils import tracking  # W&B 追跡（無認証なら no-op）

    tracking.init(
        f"{desc}_seed{args.seed}",
        group="B",
        job_type="taux",
        config={
            "seed": args.seed,
            "lr": args.lr,
            "epochs": args.epochs,
            "in_dim": in_dim,
            "temporal_kernel": args.temporal_kernel,
            "temporal_feature": args.temporal_feature,
            "temporal_k": args.temporal_k,
            "method": "taux_region_to_phase_temporal",
        },
    )

    best = {"phase_accuracy": -1.0}
    for epoch in range(args.epochs):
        model.train()
        random.shuffle(train_clips)
        ep_loss = 0.0
        for clip_id, feats, labels in train_clips:
            x = torch.from_numpy(feats).T.unsqueeze(0).to(device)  # (1, in_dim, T)
            y = torch.from_numpy(labels).to(device)
            outs = model(x)
            loss = sum(ce(o[0].T, y) + 0.15 * smoothing_loss(o) for o in outs)
            opt.zero_grad()
            loss.backward()
            opt.step()
            ep_loss += float(loss)
        val = evaluate(model, val_clips, device)
        print(
            f"[taux][epoch {epoch + 1}/{args.epochs}] loss={ep_loss / max(len(train_clips),1):.4f}  "
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
        f"[taux] best @epoch {best.get('epoch')}: acc={best['phase_accuracy']:.4f} "
        f"macroF1={best['phase_macro_f1']:.4f}"
    )

    if manager is not None:
        per_class = best.get("phase_per_class_f1", {})
        scalars = {k: v for k, v in best.items() if isinstance(v, (int, float))}
        manager.log_eval_recipe(_build_phase_recipe(args, server_name, in_dim))
        manager.log_metrics(scalars)
        manager.log_per_class_ap(per_class)
        _write_notes(exp_dir, args, best, server_name, in_dim)
        print(f"[taux] evidence written -> {exp_dir}")
        # Notion 実験Run台帳へ自動投稿（train_haux.py と同一規約・NOTION_API_KEY 未設定なら no-op）。
        from egosurgery.utils.notion_logger import log_experiment_to_notion

        log_experiment_to_notion(
            exp_dir, status="completed", step="B", tier="explore",
            primary_metric="phase acc/macro-F1/jaccard/edit/seg-F1 (online_causal, jaccard strict)",
            extra_result_text=(
                f"②object-token det→phase 時系列軸（{_method_tag(args)}）。"
                f"Δ_phase vs S4 base 0.8986±0.0028（within-server）"
            ),
        )
    tracking.finish()
    return best


def parse_args():
    p = argparse.ArgumentParser(
        description="T-aux 系統② region-token→phase の時系列軸スイープ"
        "（temporal-kernel {tecno,mingru,mamba} × temporal-feature {none,movavg,delta,window}）。"
    )
    # 時系列カーネル（問いB・T-4/5/6）
    p.add_argument(
        "--temporal-kernel", choices=list(KERNELS.keys()), default="tecno",
        help="工程時系列核（問いB）: tecno=causal dilated TCN / mingru=線形再帰 / mamba=選択的 SSM。既定 tecno。",
    )
    # 時間加工（問いA・T-1/2/3）
    p.add_argument(
        "--temporal-feature", choices=["none", "movavg", "delta", "window"], default="none",
        help="注入信号の clip 内 causal 時間加工（問いA）: none / movavg（移動平均）/ delta（差分）/ window（stack×k）。既定 none。",
    )
    p.add_argument("--temporal-k", type=int, default=3, help="movavg/window の過去フレーム数 K（既定 3）。")
    p.add_argument(
        "--temporal-target", choices=["region", "tool"], default="region",
        help="時間加工の対象信号: region=region-token（既定）/ tool=tool-presence（--add-toolpresence 必須）。GAP は常に生。",
    )
    # region 入力（train_t1a.py と同一）
    p.add_argument(
        "--region-only", action="store_true",
        help="GAP と連結せず region token のみを入力（replace 版・別解）",
    )
    p.add_argument(
        "--region-shuffle", action="store_true",
        help="§18.4 L2-2 shuffle control: region-token の frame 対応を破壊して入力（positive control 反証）",
    )
    p.add_argument("--shuffle-seed", type=int, default=12345, help="--region-shuffle 時の shuffle seed（再現性）")
    p.add_argument(
        "--add-toolpresence", action="store_true",
        help="tool-presence(15d) も追加で連結（B2a+T-aux combined）",
    )
    p.add_argument(
        "--toolpresence-source", choices=["pred", "oracle"], default="pred",
        help="--add-toolpresence 時のソース。pred=凍結検出器予測 / oracle=GT one-hot",
    )
    # 学習ハイパー（S4/T1a と同一既定）
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--num-stages", type=int, default=2)
    p.add_argument("--num-layers", type=int, default=8)
    p.add_argument("--num-f-maps", type=int, default=64)
    p.add_argument(
        "--description-override", type=str, default=None,
        help="ExperimentManager の step/description を上書き（既定は taux_<kernel>_<feature>k<K>）",
    )
    p.add_argument("--smoke", action="store_true", help="数 epoch・少 clip で疎通確認（証跡なし）")
    p.add_argument("--no-evidence", action="store_true", help="証跡を残さない（配線検証用）")
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    if a.smoke:
        a.epochs = 3
    train(a)

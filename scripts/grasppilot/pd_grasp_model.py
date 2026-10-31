"""案 B の型: C5′ = C5 + W ∗ R(T(m))（非公式 T-2026-10-31-grasp-pilot-probe、SPEC §3.2）。

.venv-relation-detr で、cwd と sys.path に third_party/Relation-DETR を置いて使う（train_t1b.py の import の後）。

    T  学習時の幾何の変換はデータセットの側（pd_grasp）で地図に掛かる。評価時の大きさの変更（検出器の eval_transform）と
       詰め物（size_divisible 32）はここで合わせる: 地図を images.image_sizes の大きさへ最近傍で変え、詰め物の部分は 0
    R  C5 の空間の大きさへの縮小。詰め物まで含めた画像の格子（H_pad, W_pad）から C5 の格子（H_pad/32, W_pad/32）へ
       adaptive_avg_pool2d（面積の平均。32 × 32 の画素の平均で、地図の質量の比を保つ）
    W  1×1 の畳み込み（5 → 2048）、bias なし、零初期化。足す場所は neck の前（P1 の FiLM と同じ場所）

界面のパラメータの名前は ``phase_iface`` で始まる（train_t1b の ``--trainable film`` が ``"phase" in name`` で選ぶ）。
地図は forward の前に ``set_grasp_maps([(5, h, w), ...])`` で渡す。None なら界面は何もしない。
``set_phase_context`` は train_t1b の経路が毎回呼ぶため受け取るが、使わない。
"""
from __future__ import annotations

import torch
from models.detectors.relation_detr import RelationDETR
from torch import nn
from torch.nn import functional as NF

N_CHANNELS = 5


class RelationDETRGraspMap(RelationDETR):
    def __init__(self, *args, c5_dim: int = 2048, n_channels: int = N_CHANNELS, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.phase_iface = nn.Conv2d(n_channels, c5_dim, 1, bias=False)
        nn.init.zeros_(self.phase_iface.weight)
        self._grasp_maps = None
        self.last_reduced = None                 # 直前の R(T(m))（検査用。学習には使わない）

    def set_phase_context(self, ctx) -> None:   # train_t1b の経路の互換。信号は使わない
        return None

    def set_grasp_maps(self, maps) -> None:
        self._grasp_maps = maps

    def gate_values(self):
        """界面の重みの大きさ（train_t1b.gate_record が epoch ごとに per_epoch_eval へ書く。ゲートではない）。"""
        w = self.phase_iface.weight.detach()
        return {"iface_max_abs": float(w.abs().max()), "iface_l2": float(w.float().norm())}

    def reduce_maps(self, images, c5_hw):
        b, _, hp, wp = images.tensors.shape
        dev = images.tensors.device
        canvas = torch.zeros((b, self.phase_iface.in_channels, hp, wp), device=dev, dtype=torch.float32)
        for i, (h, w) in enumerate(images.image_sizes):
            m = self._grasp_maps[i].to(dev).float()[None]
            if tuple(m.shape[-2:]) != (int(h), int(w)):
                m = NF.interpolate(m, size=(int(h), int(w)), mode="nearest")
            canvas[i, :, :h, :w] = m[0]
        return NF.adaptive_avg_pool2d(canvas, c5_hw)

    def get_multi_levels(self, images, mask):
        feats = self.backbone(images.tensors)
        if self._grasp_maps is not None:
            if isinstance(feats, dict):
                keys = list(feats.keys())
                c5 = feats[keys[-1]]
            else:
                feats = list(feats)
                c5 = feats[-1]
            r = self.reduce_maps(images, c5.shape[-2:])
            self.last_reduced = r.detach()
            c5 = c5 + self.phase_iface(r.to(c5.dtype))
            if isinstance(feats, dict):
                feats[keys[-1]] = c5
            else:
                feats[-1] = c5
        feats = self.neck(feats)

        def interp_mask(size):
            return NF.interpolate(mask[None], size=size)[0].to(torch.bool)

        masks = [interp_mask(f.shape[-2:]) for f in feats]
        pos = [self.position_embedding(m) for m in masks]
        return feats, masks, pos

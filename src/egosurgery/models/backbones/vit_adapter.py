"""ViT-Adapter: DINOv2 の 4 段階特徴を FPN 互換のマルチスケール特徴へ変換する。

DINOv2 の出力は全段階が同一解像度（stride = patch_size = 14）である。
Mask DINO の pixel decoder（MSDeformAttn）や VarifocalNet の FPN は
stride 4 / 8 / 16 / 32 の階層特徴を要求するため、本モジュールで
解像度を作り分け、チャネルを 256 に統一する。

使い方:
    adapter = ViTAdapter(embed_dim=1024, out_channels=256, num_outs=4)
    ms_features = adapter(backbone_features)   # backbone_features: List[(B,C,h,w)]
    # ms_features: List[Tensor] — stride 4, 8, 16, 32 の 4 段階 (B, 256, H/s, W/s)
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import nn

_OUT_STRIDES = (4, 8, 16, 32)


class ViTAdapter(nn.Module):
    """DINOv2 の等解像度特徴を stride 4/8/16/32 の階層特徴へ変換する。"""

    def __init__(
        self,
        embed_dim: int = 1024,
        out_channels: int = 256,
        num_outs: int = 4,
        in_stride: int = 14,
    ) -> None:
        """
        Args:
            embed_dim: 入力特徴のチャネル数（DINOv2 の embed_dim）。
            out_channels: 出力チャネル数（Mask DINO 既定の 256）。
            num_outs: 出力段階数（4 固定: stride 4/8/16/32）。
            in_stride: 入力特徴の stride（DINOv2 ViT/14 では 14）。
        """
        super().__init__()
        if num_outs != len(_OUT_STRIDES):
            raise ValueError(f"num_outs は {len(_OUT_STRIDES)} 固定です。")
        self.in_stride = in_stride
        self.out_strides = list(_OUT_STRIDES)
        self.out_channels = out_channels

        # lateral connection: 各入力段階を 1x1 conv で 256ch へ射影。
        self.lateral_convs = nn.ModuleList(
            nn.Conv2d(embed_dim, out_channels, kernel_size=1)
            for _ in range(num_outs)
        )
        # 解像度変換: up は ConvTranspose、down は strided Conv。
        self.resample_convs = nn.ModuleList(
            self._make_resample(out_channels, in_stride, s)
            for s in self.out_strides
        )
        # FPN 出力 conv（3x3 で平滑化）。
        self.fpn_convs = nn.ModuleList(
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
            for _ in range(num_outs)
        )

    @staticmethod
    def _make_resample(channels: int, in_stride: int, out_stride: int) -> nn.Module:
        """入力 stride から目標 stride へ変換する resample ブロックを作る。"""
        if out_stride < in_stride:
            # 高解像度化: ConvTranspose で粗くアップサンプル（後段で厳密化）。
            factor = max(2, round(in_stride / out_stride))
            return nn.ConvTranspose2d(
                channels, channels, kernel_size=factor, stride=factor
            )
        if out_stride > in_stride:
            # 低解像度化: strided Conv でダウンサンプル。
            factor = max(2, round(out_stride / in_stride))
            return nn.Conv2d(
                channels, channels, kernel_size=3, stride=factor, padding=1
            )
        return nn.Conv2d(channels, channels, kernel_size=3, padding=1)

    def forward(self, features: list[torch.Tensor]) -> list[torch.Tensor]:
        """4 段階の等解像度特徴を stride 4/8/16/32 の階層特徴へ変換する。

        Args:
            features: DINOv2 の 4 段階特徴 ``List[(B, embed_dim, h, w)]``
                （全段階同一解像度）。

        Returns:
            stride 4/8/16/32 の特徴 ``List[(B, out_channels, H/s, W/s)]``。
        """
        if len(features) != len(self.lateral_convs):
            raise ValueError(
                f"入力特徴は {len(self.lateral_convs)} 段階必要です"
                f"（受領: {len(features)}）。"
            )
        feat_h, feat_w = features[0].shape[-2:]
        img_h = feat_h * self.in_stride
        img_w = feat_w * self.in_stride

        laterals = [conv(f) for conv, f in zip(self.lateral_convs, features)]

        outs: list[torch.Tensor] = []
        for i, stride in enumerate(self.out_strides):
            resampled = self.resample_convs[i](laterals[i])
            target_h = max(1, round(img_h / stride))
            target_w = max(1, round(img_w / stride))
            # ConvTranspose / strided Conv は概算なので厳密サイズへ補間。
            if resampled.shape[-2:] != (target_h, target_w):
                resampled = F.interpolate(
                    resampled,
                    size=(target_h, target_w),
                    mode="bilinear",
                    align_corners=False,
                )
            outs.append(resampled)

        # top-down lateral connection: 粗い段階を細かい段階へ加算伝播。
        for i in range(len(outs) - 2, -1, -1):
            outs[i] = outs[i] + F.interpolate(
                outs[i + 1], size=outs[i].shape[-2:], mode="nearest"
            )

        return [conv(o) for conv, o in zip(self.fpn_convs, outs)]

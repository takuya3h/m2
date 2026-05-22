"""DINOv2 ViT-L/14 with registers を検出ヘッドへ接続する backbone ラッパー。

``torch.hub`` 経由で DINOv2（register tokens 付き）を読み込み、指定した
中間層 4 段階の特徴マップと ``[CLS]`` token を返す。

使い方:
    backbone = DINOv2Backbone(cfg.model.backbone)
    outputs = backbone(images)            # images: (B, 3, 518, 518)
    outputs["features"]   # List[Tensor]  4 段階の (B, C, H/14, W/14)
    outputs["cls_token"]  # Tensor (B, embed_dim) — Phase head 入力用（S4 以降）

中間層の取り出しには DINOv2 公式 API ``get_intermediate_layers`` を用いる。
これは内部で各 block 出力を捕捉し、``reshape=True`` で ViT の (B, N, C) を
2D 特徴マップ (B, C, H, W) へ patch グリッドとして整形する
（register token と CLS は除外される）。
"""

from __future__ import annotations

import warnings
from pathlib import Path

import torch
from torch import nn


def _load_hub_model(repo: str, model: str, pretrained: bool):
    """torch.hub からモデルを読み込む。

    GitHub への接続に失敗した場合（403 / オフライン等）は、キャッシュ済み
    リポジトリから ``source="local"`` で読み込むフォールバックを試みる。
    """
    try:
        return torch.hub.load(repo, model, pretrained=pretrained)
    except Exception as exc:  # ネットワーク不通・GitHub 403 等
        hub_dir = Path(torch.hub.get_dir())
        owner_repo = repo.replace("/", "_")
        candidates = sorted(hub_dir.glob(f"{owner_repo}_*"))
        if not candidates:
            raise RuntimeError(
                f"torch.hub から '{repo}' を取得できず、キャッシュも見つかりません: {exc}"
            ) from exc
        warnings.warn(
            f"torch.hub の GitHub 取得に失敗したためキャッシュ "
            f"({candidates[-1]}) から local ロードします。",
            RuntimeWarning,
        )
        return torch.hub.load(
            str(candidates[-1]), model, source="local", pretrained=pretrained
        )


class DINOv2Backbone(nn.Module):
    """DINOv2 (registers 付き) を 4 段階特徴 + CLS token で出力するラッパー。"""

    def __init__(self, cfg) -> None:
        """
        Args:
            cfg: backbone 設定（``configs/model/backbone/dinov2_*.yaml``）。
                ``hub_repo`` / ``hub_model`` / ``out_indices`` / ``embed_dim``
                / ``patch_size`` / ``img_size`` / ``pretrained``
                / ``gradient_checkpointing`` を参照する。
        """
        super().__init__()
        self.cfg = cfg
        self.hub_repo = str(cfg.get("hub_repo", "facebookresearch/dinov2"))
        self.hub_model = str(cfg.get("hub_model", "dinov2_vitl14_reg"))
        self.out_indices = list(cfg.get("out_indices", [7, 11, 15, 23]))
        self.embed_dim = int(cfg.get("embed_dim", 1024))
        self.patch_size = int(cfg.get("patch_size", 14))
        self.img_size = int(cfg.get("img_size", 518))

        pretrained = bool(cfg.get("pretrained", True))
        # torch.hub 経由で DINOv2 本体を読み込む（初回はリポジトリ + 重みを取得）。
        # GitHub 接続失敗時はキャッシュからの local ロードへフォールバックする。
        self.model = _load_hub_model(self.hub_repo, self.hub_model, pretrained)

        if bool(cfg.get("gradient_checkpointing", False)):
            self._enable_gradient_checkpointing()

    # ------------------------------------------------------------------ #
    # forward
    # ------------------------------------------------------------------ #
    def forward(self, x: torch.Tensor) -> dict:
        """画像から 4 段階特徴マップと CLS token を取り出す。

        Args:
            x: 入力画像 ``(B, 3, H, W)``。H, W は patch_size の倍数を推奨。

        Returns:
            ``{"features": List[Tensor], "cls_token": Tensor}``。
            ``features`` は各 ``(B, embed_dim, H/patch, W/patch)``、
            ``cls_token`` は ``(B, embed_dim)``。
        """
        outputs = self.model.get_intermediate_layers(
            x,
            n=self.out_indices,
            reshape=True,            # (B, N, C) -> (B, C, H, W)
            return_class_token=True,
            norm=True,
        )
        features = [feat for feat, _cls in outputs]
        # 最終取得層の CLS token を Phase head 入力として用いる。
        cls_token = outputs[-1][1]
        return {"features": features, "cls_token": cls_token}

    # ------------------------------------------------------------------ #
    # 内部ヘルパ
    # ------------------------------------------------------------------ #
    def _enable_gradient_checkpointing(self) -> None:
        """gradient checkpointing を有効化する（対応していなければ警告のみ）。"""
        if hasattr(self.model, "set_grad_checkpointing"):
            self.model.set_grad_checkpointing(True)
            return
        # DINOv2 公式 ViT は専用 API を持たないため、block 側のフラグを試す。
        enabled = False
        for block in getattr(self.model, "blocks", []):
            if hasattr(block, "grad_checkpointing"):
                block.grad_checkpointing = True
                enabled = True
        if not enabled:
            warnings.warn(
                "DINOv2 backbone は gradient checkpointing 用 API を公開していません。"
                "必要なら forward 側で torch.utils.checkpoint を適用してください。",
                RuntimeWarning,
            )

    @property
    def num_features(self) -> int:
        """出力特徴マップのチャネル数（= embed_dim）。"""
        return self.embed_dim

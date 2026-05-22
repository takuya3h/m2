"""DINOv2 backbone へ PEFT (LoRA / DoRA / QLoRA) を適用するユーティリティ。

backbone 全体を fine-tune する代わりに、少数の低ランクアダプタのみを
学習対象とすることで、学習可能パラメータを全体の数 % に抑える。

使い方:
    backbone = DINOv2Backbone(cfg.model.backbone)
    backbone = apply_peft(backbone, cfg.model.backbone.peft)
"""

from __future__ import annotations

import warnings

from torch import nn

# PEFT を適用しないことを表す method 値。
_DISABLED = (None, "null", "none", "")


def apply_peft(backbone: nn.Module, peft_cfg) -> nn.Module:
    """backbone に PEFT を適用する。

    Args:
        backbone: 対象モデル（``DINOv2Backbone`` 等）。
        peft_cfg: PEFT 設定。``method`` が ``"lora"`` / ``"dora"`` /
            ``"qlora"`` / ``null`` のいずれか。``null`` ならそのまま返す。

    Returns:
        PEFT 適用済みモデル（``method`` が無効なら ``backbone`` をそのまま）。
    """
    method = None if peft_cfg is None else peft_cfg.get("method", None)
    if method in _DISABLED:
        return backbone
    method = str(method).lower()

    try:
        from peft import LoraConfig, get_peft_model
    except ImportError:
        warnings.warn(
            "peft が import できないため PEFT を適用せず backbone を返します。",
            RuntimeWarning,
        )
        return backbone

    r = int(peft_cfg.get("r", 16))
    lora_alpha = int(peft_cfg.get("lora_alpha", 32))
    lora_dropout = float(peft_cfg.get("lora_dropout", 0.05))
    target_modules = list(peft_cfg.get("target_modules", ["qkv", "proj"]))
    # method=="dora" もしくは use_dora=true のとき DoRA を有効化。
    use_dora = (method == "dora") or bool(peft_cfg.get("use_dora", False))

    if method == "qlora":
        # QLoRA は本来 4bit 量子化済みモデルへの LoRA。torch.hub で読み込んだ
        # モデルを後から 4bit 化するのは非対応のため、LoRA へフォールバックする。
        warnings.warn(
            "QLoRA は torch.hub 読み込み済みモデルへ後付け適用できないため、"
            "通常の LoRA へフォールバックします。",
            RuntimeWarning,
        )

    lora_config = LoraConfig(
        r=r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=target_modules,
        use_dora=use_dora,
        bias="none",
    )
    return get_peft_model(backbone, lora_config)


def count_trainable_parameters(model: nn.Module) -> tuple[int, int]:
    """``(学習可能パラメータ数, 全パラメータ数)`` を返す。"""
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return trainable, total

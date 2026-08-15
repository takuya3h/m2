"""Causal grasp inference with signal-level injection into phase recognition.

The grasp branch independently predicts five frame-level presences from frozen
GAP features.  The injected arm concatenates detached sigmoid predictions to
the phase input; the control arm concatenates zeros of exactly the same shape.
Detaching the signal keeps grasp learning identical in both arms: only the
masked auxiliary BCE trains the grasp branch.

Example:
    model = GraspInferenceInjectionModel({"enabled": True, "arm": "inj"})
    outputs = model(features)  # features: (B, 2048, T)
"""

from __future__ import annotations

from typing import Mapping

import torch
import torch.nn.functional as F
from torch import nn

from egosurgery.models.heads.tecno_head import TeCNO


class FramewiseGraspHead(nn.Module):
    """Per-frame MLP implemented as causal kernel-1 convolutions."""

    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv1d(input_dim, hidden_dim, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Conv1d(hidden_dim, num_classes, kernel_size=1),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """Return frame-level logits with shape ``(B, classes, T)``."""
        return self.layers(features)


class GraspInferenceInjectionModel(nn.Module):
    """Independent grasp branch plus causal TeCNO phase head.

    ``enabled=False`` is the default and constructs an unchanged TeCNO input
    path.  With the feature enabled, ``arm`` must be ``ctrl`` or ``inj`` and
    both arms have exactly the same parameters.
    """

    def __init__(self, cfg: Mapping | None = None) -> None:
        super().__init__()
        cfg = cfg or {}
        self.enabled = bool(cfg.get("enabled", False))
        self.arm = str(cfg.get("arm", "ctrl")).lower()
        if self.enabled and self.arm not in {"ctrl", "inj"}:
            raise ValueError(f"unknown grasp injection arm: {self.arm!r}")

        input_dim = int(cfg.get("input_dim", 2048))
        num_grasp_classes = int(cfg.get("num_grasp_classes", 5))
        num_phases = int(cfg.get("num_phases", 9))
        hidden_dim = int(cfg.get("hidden_dim", 64))
        temporal_cfg = cfg.get("temporal", {})

        self.input_dim = input_dim
        self.num_grasp_classes = num_grasp_classes
        self.grasp_head: FramewiseGraspHead | None = None
        phase_input_dim = input_dim
        if self.enabled:
            self.grasp_head = FramewiseGraspHead(
                input_dim=input_dim,
                hidden_dim=hidden_dim,
                num_classes=num_grasp_classes,
            )
            phase_input_dim += num_grasp_classes

        self.phase_head = TeCNO(
            num_stages=int(temporal_cfg.get("num_stages", 2)),
            num_layers=int(temporal_cfg.get("num_layers", 8)),
            num_f_maps=int(temporal_cfg.get("num_f_maps", 64)),
            in_dim=phase_input_dim,
            num_classes=num_phases,
            dropout=float(temporal_cfg.get("dropout", 0.5)),
        )

    def forward(
        self,
        features: torch.Tensor,
        injected_signal: torch.Tensor | None = None,
    ) -> dict[str, object]:
        """Run grasp inference and phase recognition without future context.

        ``injected_signal`` is a test/audit override.  It changes the candidate
        signal in the injected arm, while the control arm still replaces it by
        zeros.  This makes signal reachability directly measurable.
        """
        if features.ndim != 3 or features.shape[1] != self.input_dim:
            raise ValueError(
                f"expected features (B,{self.input_dim},T), got {tuple(features.shape)}"
            )
        if not self.enabled:
            if injected_signal is not None:
                raise ValueError(
                    "injected_signal is unavailable when grasp inference is disabled"
                )
            return {
                "phase_logits": self.phase_head(features),
                "grasp_logits": None,
                "phase_input_signal": None,
            }

        assert self.grasp_head is not None
        grasp_logits = self.grasp_head(features)
        candidate = torch.sigmoid(grasp_logits).detach()
        if injected_signal is not None:
            if injected_signal.shape != candidate.shape:
                raise ValueError(
                    "injected signal shape mismatch: "
                    f"expected {tuple(candidate.shape)}, got {tuple(injected_signal.shape)}"
                )
            candidate = injected_signal.detach()
        phase_signal = candidate if self.arm == "inj" else torch.zeros_like(candidate)
        phase_input = torch.cat((features, phase_signal), dim=1)
        return {
            "phase_logits": self.phase_head(phase_input),
            "grasp_logits": grasp_logits,
            "phase_input_signal": phase_signal,
        }


def masked_grasp_bce(
    logits: torch.Tensor,
    targets: torch.Tensor,
    valid_mask: torch.Tensor,
) -> torch.Tensor:
    """Return BCE over annotated frames only, preserving a zero-gradient loss."""
    if logits.shape != targets.shape:
        raise ValueError(
            f"grasp target shape mismatch: {logits.shape} vs {targets.shape}"
        )
    if valid_mask.shape != (logits.shape[0], logits.shape[2]):
        raise ValueError(f"valid_mask must be (B,T), got {tuple(valid_mask.shape)}")
    per_frame = F.binary_cross_entropy_with_logits(
        logits, targets, reduction="none"
    ).mean(dim=1)
    weights = valid_mask.to(dtype=per_frame.dtype)
    count = weights.sum()
    if int(count.detach().item()) == 0:
        return logits.sum() * 0.0
    return (per_frame * weights).sum() / count


@torch.no_grad()
def grasp_accuracy_per_class(
    logits: torch.Tensor,
    targets: torch.Tensor,
    valid_mask: torch.Tensor,
) -> list[float]:
    """Return one binary accuracy value for each grasp target dimension."""
    if logits.shape != targets.shape:
        raise ValueError(
            f"grasp target shape mismatch: {logits.shape} vs {targets.shape}"
        )
    valid = valid_mask.to(dtype=torch.bool)
    if not bool(valid.any()):
        return [float("nan")] * logits.shape[1]
    predictions = torch.sigmoid(logits) >= 0.5
    expected = targets >= 0.5
    return [
        float(
            (predictions[:, index, :][valid] == expected[:, index, :][valid])
            .float()
            .mean()
        )
        for index in range(logits.shape[1])
    ]

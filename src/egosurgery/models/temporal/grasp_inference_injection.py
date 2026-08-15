"""Causal grasp inference with signal-level injection into phase recognition.

The grasp branch independently predicts five frame-level presences from frozen
GAP features.  The injected arm concatenates a detached signal to the phase
input; the control arm concatenates zeros of exactly the same shape.
Detaching the signal keeps grasp learning identical in both arms: only the
masked auxiliary BCE trains the grasp branch.

The shape of the injected signal is selected by ``cfg["signal"]``.  Unknown
values raise instead of silently falling back: a mislabelled arm in the next
experiment must fail loudly, not run as the default.

============== =========================================================
signal          candidate concatenated to the phase input (inj arm)
============== =========================================================
predicted_sigmoid  sigmoid of the grasp logits (default, prior behaviour)
zeros              an all-zero signal (uninformative arm)
raw_logits         the grasp logits before the sigmoid squashes them
standardized       sigmoid outputs recentred/rescaled per dimension with
                   constants measured on the *train* split (never val)
oracle_upper_bound_only
                   the ground-truth targets.  UPPER-BOUND MEASUREMENT
                   ONLY -- this feeds evaluation-side teachers into the
                   model and MUST NEVER be reported as a result.  It only
                   answers whether the injection mechanism itself can
                   help at all.  Requires an explicit acknowledgement key
                   and per-dimension fill values for unlabelled frames.
============== =========================================================

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

SIGNAL_MODES = (
    "predicted_sigmoid",
    "zeros",
    "raw_logits",
    "standardized",
    "oracle_upper_bound_only",
)


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

        # Unknown signal names must fail loudly, never fall back to the
        # default: a mistyped arm in an experiment would otherwise run as
        # predicted_sigmoid and be indistinguishable from the real thing.
        self.signal = str(cfg.get("signal", "predicted_sigmoid"))
        if self.signal not in SIGNAL_MODES:
            raise ValueError(
                f"unknown grasp injection signal: {self.signal!r}; "
                f"allowed: {SIGNAL_MODES}"
            )

        def _dim_constants(key: str) -> torch.Tensor:
            values = cfg.get(key)
            if values is None:
                raise ValueError(
                    f"signal={self.signal!r} requires cfg[{key!r}] with "
                    f"{num_grasp_classes} per-dimension values"
                )
            tensor = torch.as_tensor(list(values), dtype=torch.float32)
            if tensor.numel() != num_grasp_classes:
                raise ValueError(
                    f"cfg[{key!r}] must hold {num_grasp_classes} values, "
                    f"got {tensor.numel()}"
                )
            return tensor.view(1, num_grasp_classes, 1)

        if self.signal == "standardized":
            # Centre/scale constants must come from the train split; taking
            # them from the eval side would leak.  The trainer records them.
            center = _dim_constants("signal_center")
            scale = _dim_constants("signal_scale")
            if bool((scale <= 0).any()):
                raise ValueError("signal_scale must be strictly positive")
            self.register_buffer("signal_center", center)
            self.register_buffer("signal_scale", scale)
        if self.signal == "oracle_upper_bound_only":
            # UPPER-BOUND MEASUREMENT ONLY.  The acknowledgement key forces
            # every config that uses ground-truth injection to say so out
            # loud; without it the model refuses to construct.
            if cfg.get("oracle_upper_bound_acknowledged") is not True:
                raise ValueError(
                    "signal='oracle_upper_bound_only' feeds ground-truth "
                    "targets into the phase input.  It measures an upper "
                    "bound and must never be reported as a result.  Set "
                    "oracle_upper_bound_acknowledged: true to proceed."
                )
            self.register_buffer(
                "oracle_missing_fill", _dim_constants("oracle_missing_fill")
            )

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
        grasp_targets: torch.Tensor | None = None,
        grasp_valid: torch.Tensor | None = None,
    ) -> dict[str, object]:
        """Run grasp inference and phase recognition without future context.

        ``injected_signal`` is a test/audit override.  It changes the candidate
        signal in the injected arm, while the control arm still replaces it by
        zeros.  This makes signal reachability directly measurable.

        ``grasp_targets`` (B, C, T) and ``grasp_valid`` (B, T) are consumed
        only by ``signal='oracle_upper_bound_only'``; that mode raises when
        they are missing.  Unlabelled frames receive the recorded per-dim
        fill values -- note the fill is never exactly 0 or 1, so "this frame
        has no teacher" remains distinguishable downstream.
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
        candidate = self._candidate(grasp_logits, grasp_targets, grasp_valid)
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

    def _candidate(
        self,
        grasp_logits: torch.Tensor,
        grasp_targets: torch.Tensor | None,
        grasp_valid: torch.Tensor | None,
    ) -> torch.Tensor:
        """Shape the signal candidate per ``self.signal``, always detached.

        Every branch is a per-frame operation: no mode may look at future
        frames, or causality breaks for the phase head downstream.
        """
        if self.signal == "predicted_sigmoid":
            return torch.sigmoid(grasp_logits).detach()
        if self.signal == "zeros":
            return torch.zeros_like(grasp_logits)
        if self.signal == "raw_logits":
            return grasp_logits.detach()
        if self.signal == "standardized":
            probs = torch.sigmoid(grasp_logits).detach()
            return (probs - self.signal_center) / self.signal_scale
        # oracle_upper_bound_only -- UPPER-BOUND MEASUREMENT ONLY, never a
        # reportable result (see the class docstring and the config guard).
        if grasp_targets is None or grasp_valid is None:
            raise ValueError(
                "signal='oracle_upper_bound_only' requires grasp_targets "
                "and grasp_valid at forward time"
            )
        if grasp_targets.shape != grasp_logits.shape:
            raise ValueError(
                "oracle targets shape mismatch: "
                f"expected {tuple(grasp_logits.shape)}, got {tuple(grasp_targets.shape)}"
            )
        valid = grasp_valid.to(dtype=torch.bool).unsqueeze(1)
        fill = self.oracle_missing_fill.expand_as(grasp_targets)
        return torch.where(valid, grasp_targets.to(grasp_logits.dtype), fill).detach()


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

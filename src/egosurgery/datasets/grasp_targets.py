"""Frame-level grasp-presence targets derived from ``hand_tool_seg`` COCO data.

The five targets encode the presence of the two hands and the three grasp
relations.  Frames listed by :func:`load_loss_mask` stay in the phase
population but are marked invalid for the auxiliary grasp loss.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from egosurgery.datasets.loss_mask import load_loss_mask

DEFAULT_ROOT = Path("data/annotations/egosurgery_hts/hand_tool_seg")
GRASP_LABEL_NAMES = (
    "left_hand",
    "right_hand",
    "left_hand_tool",
    "right_hand_tool",
    "two_hands_tool",
)


@dataclass(frozen=True)
class GraspTargetIndex:
    """Five-dimensional targets and the frames masked from auxiliary loss."""

    labels: dict[str, np.ndarray]
    masked_frames: frozenset[str]

    def target_for(self, frame_stem: str) -> tuple[np.ndarray, bool]:
        """Return ``(target, valid)`` without removing a phase frame."""
        if frame_stem in self.labels:
            return self.labels[frame_stem].copy(), True
        if frame_stem in self.masked_frames:
            return np.zeros(len(GRASP_LABEL_NAMES), dtype=np.float32), False
        raise KeyError(
            f"grasp target and loss-mask entry are both missing: {frame_stem}"
        )


def load_grasp_target_index(
    split: str,
    root: Path | str | None = None,
) -> GraspTargetIndex:
    """Load one split and reduce segmentation annotations to five presences.

    Args:
        split: ``train``, ``val``, or ``test``.
        root: Directory containing ``{split}.json`` and ``loss_mask/``.

    Returns:
        Index keyed by image filename stem.
    """
    base = Path(root) if root is not None else DEFAULT_ROOT
    annotation_path = base / f"{split}.json"
    data = json.loads(annotation_path.read_text(encoding="utf-8"))

    categories = {
        int(category["id"]): str(category["name"])
        for category in data.get("categories", [])
    }
    expected_ids = set(range(1, len(GRASP_LABEL_NAMES) + 1))
    if set(categories) != expected_ids:
        raise ValueError(f"unexpected hand_tool_seg category ids: {sorted(categories)}")

    image_stems = {
        int(image["id"]): Path(str(image["file_name"])).stem
        for image in data.get("images", [])
    }
    labels = {
        stem: np.zeros(len(GRASP_LABEL_NAMES), dtype=np.float32)
        for stem in image_stems.values()
    }
    for annotation in data.get("annotations", []):
        image_id = int(annotation["image_id"])
        category_id = int(annotation["category_id"])
        if image_id not in image_stems:
            raise ValueError(f"annotation references unknown image_id: {image_id}")
        if category_id not in expected_ids:
            raise ValueError(f"annotation has unknown category_id: {category_id}")
        labels[image_stems[image_id]][category_id - 1] = 1.0

    masked_frames = load_loss_mask(split, base / "loss_mask")
    overlap = set(labels) & set(masked_frames)
    if overlap:
        sample = sorted(overlap)[:3]
        raise ValueError(f"annotated frames also occur in loss mask: {sample}")
    return GraspTargetIndex(labels=labels, masked_frames=masked_frames)

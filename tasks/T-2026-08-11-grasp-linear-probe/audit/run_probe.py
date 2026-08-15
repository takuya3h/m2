"""Frozen Relation-DETR GAP features 上の 5 次元線形 probe を実測する。"""

from __future__ import annotations

import csv
import gc
import json
import socket
import subprocess
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
FEATURE_ROOT = ROOT / "data/processed/stage1_features/relation_detr_seed42"
HTS_ROOT = ROOT / "data/annotations/egosurgery_hts/hand_tool_seg"
TOOL_ROOT = ROOT / "data/annotations/egosurgery_tool"
SPLITS = ("train", "val", "test")
SEEDS = (42, 123, 456)
DIMENSIONS = {
    1: "First Person's Left Hand",
    2: "First Person's Right Hand",
    3: "Left Hand Tool",
    4: "Right Hand Tool",
    5: "Two Hands Tool",
}


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "--no-pager", *args], cwd=ROOT, text=True
    ).strip()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"empty CSV: {path}")
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def load_features(split: str) -> tuple[list[str], np.ndarray, Path]:
    path = FEATURE_ROOT / f"{split}_gap.npz"
    with np.load(path) as data:
        frame_ids = [str(x) for x in data["frame_ids"]]
        features = np.asarray(data["features"], dtype=np.float32)
    if len(frame_ids) != len(set(frame_ids)):
        raise AssertionError(f"duplicate feature IDs: {split}")
    if features.shape != (len(frame_ids), 2048):
        raise AssertionError(f"unexpected feature shape: {split} {features.shape}")
    if not np.isfinite(features).all():
        raise AssertionError(f"non-finite feature: {split}")
    return frame_ids, features, path


def load_hts(split: str) -> tuple[list[str], np.ndarray, dict]:
    data = json.loads((HTS_ROOT / f"{split}.json").read_text(encoding="utf-8"))
    id_to_stem = {
        image["id"]: Path(image["file_name"]).stem for image in data["images"]
    }
    present: dict[str, set[int]] = defaultdict(set)
    for ann in data["annotations"]:
        present[id_to_stem[ann["image_id"]]].add(int(ann["category_id"]))
    stems = list(id_to_stem.values())
    labels = np.asarray(
        [[int(category in present[stem]) for category in range(1, 6)] for stem in stems],
        dtype=np.int8,
    )
    categories = {int(c["id"]): c["name"] for c in data["categories"]}
    if categories != DIMENSIONS:
        raise AssertionError(f"unexpected HTS categories: {categories}")
    return stems, labels, data


def load_tool_labels(
    split: str, feature_ids: list[str]
) -> tuple[np.ndarray, dict[int, np.ndarray], dict[int, str]]:
    data = json.loads(
        (TOOL_ROOT / f"instances_{split}.json").read_text(encoding="utf-8")
    )
    image_id_to_stem = {
        image["id"]: Path(image["file_name"]).stem for image in data["images"]
    }
    stem_to_categories: dict[str, set[int]] = defaultdict(set)
    for ann in data["annotations"]:
        stem_to_categories[image_id_to_stem[ann["image_id"]]].add(
            int(ann["category_id"])
        )
    if set(feature_ids) != set(image_id_to_stem.values()):
        raise AssertionError(f"tool/feature ID mismatch: {split}")
    any_tool = np.asarray(
        [int(bool(stem_to_categories[stem])) for stem in feature_ids], dtype=np.int8
    )
    names = {int(c["id"]): c["name"] for c in data["categories"]}
    per_class = {
        category: np.asarray(
            [int(category in stem_to_categories[stem]) for stem in feature_ids],
            dtype=np.int8,
        )
        for category in names
    }
    return any_tool, per_class, names


def scale_train_val(
    train_x: np.ndarray, val_x: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_x)
    val_scaled = scaler.transform(val_x)
    return train_scaled, val_scaled


def fit_binary(
    train_x: np.ndarray,
    train_y: np.ndarray,
    val_x: np.ndarray,
    val_y: np.ndarray,
    seed: int,
) -> dict:
    train_unique = np.unique(train_y)
    val_unique = np.unique(val_y)
    if train_unique.size != 2:
        return {
            "roc_auc": "UNKNOWN",
            "average_precision": "UNKNOWN",
            "iterations": "UNKNOWN",
            "convergence_warnings": 0,
            "reason": f"train has {train_unique.tolist()}",
        }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        model = LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=2000,
            penalty="l2",
            random_state=seed,
            solver="liblinear",
            tol=1e-4,
        )
        model.fit(train_x, train_y)
    scores = model.decision_function(val_x)
    convergence = sum(issubclass(w.category, ConvergenceWarning) for w in caught)
    if val_unique.size != 2:
        return {
            "roc_auc": "UNKNOWN",
            "average_precision": float(average_precision_score(val_y, scores)),
            "iterations": int(model.n_iter_[0]),
            "convergence_warnings": convergence,
            "reason": f"val has {val_unique.tolist()}",
        }
    return {
        "roc_auc": float(roc_auc_score(val_y, scores)),
        "average_precision": float(average_precision_score(val_y, scores)),
        "iterations": int(model.n_iter_[0]),
        "convergence_warnings": convergence,
        "reason": "",
    }


def metric_rows(
    control: str,
    seed: int,
    train_x: np.ndarray,
    train_y: np.ndarray,
    val_x: np.ndarray,
    val_y: np.ndarray,
    cross_video_fraction: float | str = "",
) -> list[dict]:
    rows = []
    for idx, (category, name) in enumerate(DIMENSIONS.items()):
        result = fit_binary(train_x, train_y[:, idx], val_x, val_y[:, idx], seed)
        rows.append(
            {
                "control": control,
                "seed": seed,
                "dimension": category,
                "name": name,
                "train_n": len(train_y),
                "val_n": len(val_y),
                "train_positive_rate": float(train_y[:, idx].mean()),
                "val_positive_rate": float(val_y[:, idx].mean()),
                "roc_auc": result["roc_auc"],
                "average_precision": result["average_precision"],
                "iterations": result["iterations"],
                "convergence_warnings": result["convergence_warnings"],
                "cross_video_fraction": cross_video_fraction,
                "reason": result["reason"],
            }
        )
    return rows


def finite_auc(rows: list[dict]) -> np.ndarray:
    return np.asarray([float(row["roc_auc"]) for row in rows], dtype=np.float64)


def main() -> None:
    features: dict[str, tuple[list[str], np.ndarray, Path]] = {}
    hts: dict[str, tuple[list[str], np.ndarray, dict]] = {}
    phase_a: dict = {"splits": {}}
    for split in SPLITS:
        features[split] = load_features(split)
        hts[split] = load_hts(split)
        feature_ids, values, feature_path = features[split]
        teacher_ids, labels, raw = hts[split]
        feature_set, teacher_set = set(feature_ids), set(teacher_ids)
        if teacher_set - feature_set:
            raise AssertionError(f"teacher without feature: {split}")
        direct_stem = teacher_ids[0]
        phase_a["splits"][split] = {
            "feature_path": str(feature_path.relative_to(ROOT)),
            "feature_bytes": feature_path.stat().st_size,
            "feature_shape": list(values.shape),
            "feature_dtype": str(values.dtype),
            "frame_id_dtype": "unicode",
            "teacher_images": len(teacher_ids),
            "teacher_annotations": len(raw["annotations"]),
            "teacher_and_feature": len(teacher_set & feature_set),
            "teacher_without_feature": len(teacher_set - feature_set),
            "feature_without_teacher": len(feature_set - teacher_set),
            "positive_counts": labels.sum(axis=0).astype(int).tolist(),
            "positive_rates": labels.mean(axis=0).tolist(),
            "direct_example": {
                "stem": direct_stem,
                "feature_index": feature_ids.index(direct_stem),
                "positive_dimensions": (np.flatnonzero(labels[0]) + 1).tolist(),
            },
        }
    phase_a["feature_total_bytes"] = sum(
        item[2].stat().st_size for item in features.values()
    )
    phase_a["environment"] = {
        "host": socket.gethostname(),
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "HEAD"),
        "conventions_rev": git("log", "-1", "--format=%h", "--", "context/conventions.md"),
        "runindex_rev": git("log", "-1", "--format=%h", "--", "runindex/"),
        "python": subprocess.check_output(
            [str(ROOT / ".venv/bin/python"), "--version"], text=True, stderr=subprocess.STDOUT
        ).strip(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "sync_pause": (ROOT / ".sync-pause").exists(),
    }
    (AUDIT / "phase_a.json").write_text(
        json.dumps(phase_a, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    train_ids, train_all_x, _ = features["train"]
    val_ids, val_all_x, _ = features["val"]
    train_teacher_ids, train_y, _ = hts["train"]
    val_teacher_ids, val_y, _ = hts["val"]
    train_index = {stem: idx for idx, stem in enumerate(train_ids)}
    val_index = {stem: idx for idx, stem in enumerate(val_ids)}
    train_x = train_all_x[[train_index[stem] for stem in train_teacher_ids]]
    val_x = val_all_x[[val_index[stem] for stem in val_teacher_ids]]
    train_scaled, val_scaled = scale_train_val(train_x, val_x)

    actual_rows = metric_rows(
        "meaningful_features", 42, train_scaled, train_y, val_scaled, val_y
    )
    write_csv(AUDIT / "probe_result.csv", actual_rows)

    control_rows: list[dict] = []
    train_videos = np.asarray([stem.rsplit("_", 1)[0] for stem in train_teacher_ids])
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        permutation = rng.permutation(len(train_y))
        cross_video = float(np.mean(train_videos != train_videos[permutation]))
        control_rows.extend(
            metric_rows(
                "shuffled_train_teachers",
                seed,
                train_scaled,
                train_y[permutation],
                val_scaled,
                val_y,
                cross_video,
            )
        )
        random_train = rng.standard_normal(train_x.shape, dtype=np.float32)
        random_val = rng.standard_normal(val_x.shape, dtype=np.float32)
        random_train_scaled, random_val_scaled = scale_train_val(random_train, random_val)
        control_rows.extend(
            metric_rows(
                "random_features",
                seed,
                random_train_scaled,
                train_y,
                random_val_scaled,
                val_y,
            )
        )
        del random_train, random_val, random_train_scaled, random_val_scaled
        gc.collect()
    write_csv(AUDIT / "control.csv", control_rows)

    train_any, train_classes, tool_names = load_tool_labels("train", train_ids)
    val_any, val_classes, _ = load_tool_labels("val", val_ids)
    tool_train_scaled, tool_val_scaled = scale_train_val(train_all_x, val_all_x)
    prescribed = fit_binary(
        tool_train_scaled, train_any, tool_val_scaled, val_any, seed=42
    )
    supplemental_category = 14
    supplemental = fit_binary(
        tool_train_scaled,
        train_classes[supplemental_category],
        tool_val_scaled,
        val_classes[supplemental_category],
        seed=42,
    )

    actual_auc = finite_auc(actual_rows)
    visibility_auc = float(actual_auc[:2].mean())
    grasp_auc = float(actual_auc[2:].mean())
    control_summary = {}
    for control in ("shuffled_train_teachers", "random_features"):
        selected = [row for row in control_rows if row["control"] == control]
        auc = finite_auc(selected).reshape(len(SEEDS), len(DIMENSIONS))
        group_diff = auc[:, 2:].mean(axis=1) - auc[:, :2].mean(axis=1)
        control_summary[control] = {
            "auc_mean": float(auc.mean()),
            "auc_sample_std": float(auc.std(ddof=1)),
            "auc_min": float(auc.min()),
            "auc_max": float(auc.max()),
            "group_difference_mean": float(group_diff.mean()),
            "group_difference_sample_std": float(group_diff.std(ddof=1)),
            "group_difference_range": float(group_diff.max() - group_diff.min()),
        }

    summary = {
        "method": {
            "classifier": "StandardScaler + one affine logistic-regression score",
            "solver": "liblinear",
            "penalty": "l2",
            "C": 1.0,
            "class_weight": "balanced",
            "max_iter": 2000,
            "fit_split": "train",
            "measure_split": "val",
            "test_used_for_modeling": False,
            "temporal_information": False,
        },
        "actual_group_comparison": {
            "visibility_dimensions": [1, 2],
            "grasp_dimensions": [3, 4, 5],
            "visibility_mean_roc_auc": visibility_auc,
            "grasp_mean_roc_auc": grasp_auc,
            "grasp_minus_visibility_roc_auc": grasp_auc - visibility_auc,
        },
        "negative_controls": control_summary,
        "prescribed_positive_control": {
            "target": "any EgoSurgery-Tool annotation",
            "train_positive": int(train_any.sum()),
            "train_total": len(train_any),
            "val_positive": int(val_any.sum()),
            "val_total": len(val_any),
            **prescribed,
            "valid_discrimination_control": False,
        },
        "supplemental_positive_control": {
            "target": f"tool category {supplemental_category}: {tool_names[supplemental_category]}",
            "train_positive": int(train_classes[supplemental_category].sum()),
            "train_total": len(train_ids),
            "val_positive": int(val_classes[supplemental_category].sum()),
            "val_total": len(val_ids),
            **supplemental,
            "valid_discrimination_control": True,
        },
    }
    (AUDIT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    control_text = [
        "Phase C controls",
        json.dumps(summary["negative_controls"], ensure_ascii=False, indent=2),
        "prescribed_positive_control",
        json.dumps(summary["prescribed_positive_control"], ensure_ascii=False, indent=2),
        "supplemental_positive_control",
        json.dumps(summary["supplemental_positive_control"], ensure_ascii=False, indent=2),
    ]
    (AUDIT / "control.txt").write_text("\n".join(control_text) + "\n", encoding="utf-8")

    print(json.dumps({"phase_a": phase_a, "summary": summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

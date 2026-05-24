"""評価指標（metrics/）のテスト。

ダミーの COCO アノテーションと予測を ``tmp_path`` に生成し、
``DetectionEvaluator`` の COCO mAP / per-class AP / 長尾指標 /
confusion matrix を検証する。

実行方法:
    PYTHONPATH=src pytest tests/test_metrics.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# PYTHONPATH=src を付け忘れても import できるよう src/ を通す。
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from egosurgery.datasets.constants import (  # noqa: E402
    CONFUSABLE_CLASSES,
    RARE_CLASSES,
    TOOL_CLASSES,
    TOOL_NAME_TO_ID,
)

# テストで使うクラス（rare / similar を網羅）。
_USED_CLASSES = ["Skewer", "Forceps", "Tweezers", "Gauze"]


def _make_coco_and_predictions(tmp_path: Path):
    """ダミー COCO GT JSON と、それに完全一致する予測を生成する。

    Returns:
        ``(ann_file, predictions, image_ids)``。
    """
    images, annotations = [], []
    predictions, image_ids = [], []
    ann_id = 0

    for img_idx in range(4):
        images.append(
            {"id": img_idx, "file_name": f"img_{img_idx}.jpg",
             "width": 128, "height": 128}
        )
        boxes, labels, scores = [], [], []
        # 画像ごとに 2 クラス分の box を置く。
        for slot, cls_name in enumerate(_USED_CLASSES[img_idx % 2 :: 2]):
            cat_id = TOOL_NAME_TO_ID[cls_name]
            x, y = 10 + slot * 30, 10 + slot * 25
            w, h = 24, 20
            annotations.append(
                {"id": ann_id, "image_id": img_idx, "category_id": cat_id,
                 "bbox": [x, y, w, h], "area": w * h, "iscrowd": 0}
            )
            ann_id += 1
            boxes.append([x, y, x + w, y + h])  # xyxy
            labels.append(cat_id)
            scores.append(0.95)
        predictions.append(
            {
                "boxes": np.array(boxes, dtype=np.float32),
                "scores": np.array(scores, dtype=np.float32),
                "labels": np.array(labels, dtype=np.int64),
            }
        )
        image_ids.append(img_idx)

    coco = {
        "images": images,
        "annotations": annotations,
        "categories": [dict(c) for c in TOOL_CLASSES],
    }
    ann_file = tmp_path / "instances_val.json"
    ann_file.write_text(json.dumps(coco), encoding="utf-8")
    return ann_file, predictions, image_ids


def _build_evaluator(ann_file):
    from egosurgery.metrics.detection import DetectionEvaluator

    return DetectionEvaluator(
        ann_file=str(ann_file),
        tool_classes=TOOL_CLASSES,
        rare_classes=RARE_CLASSES,
        similar_pairs=CONFUSABLE_CLASSES,
    )


# ---------------------------------------------------------------------- #
# 1. DetectionEvaluator の基本動作
# ---------------------------------------------------------------------- #
def test_detection_evaluator_basic(tmp_path):
    """予測が GT と一致するとき mAP が高い値になること。"""
    ann_file, predictions, image_ids = _make_coco_and_predictions(tmp_path)
    evaluator = _build_evaluator(ann_file)
    evaluator.update(predictions, image_ids)
    results = evaluator.compute()

    assert "mAP" in results and "mAP_50" in results and "mAP_75" in results
    # 予測 = GT なので mAP は高くなるはず。
    assert results["mAP"] > 0.8
    assert 0.0 <= results["mAP"] <= 1.0


# ---------------------------------------------------------------------- #
# 2. per-class AP が 15 クラス分
# ---------------------------------------------------------------------- #
def test_per_class_ap_15_classes(tmp_path):
    """per_class_ap が 15 クラス全てを含むこと。"""
    ann_file, predictions, image_ids = _make_coco_and_predictions(tmp_path)
    evaluator = _build_evaluator(ann_file)
    evaluator.update(predictions, image_ids)
    results = evaluator.compute()

    per_class_ap = results["per_class_ap"]
    assert len(per_class_ap) == 15
    expected_names = {c["name"] for c in TOOL_CLASSES}
    assert set(per_class_ap) == expected_names


# ---------------------------------------------------------------------- #
# 3. AP_rare / AP_common の分離
# ---------------------------------------------------------------------- #
def test_ap_rare_common_split(tmp_path):
    """AP_rare が稀少クラスの平均、AP_common がそれ以外の平均であること。"""
    ann_file, predictions, image_ids = _make_coco_and_predictions(tmp_path)
    evaluator = _build_evaluator(ann_file)
    evaluator.update(predictions, image_ids)
    results = evaluator.compute()

    per_class_ap = results["per_class_ap"]
    rare = [ap for n, ap in per_class_ap.items() if n in RARE_CLASSES]
    common = [ap for n, ap in per_class_ap.items() if n not in RARE_CLASSES]

    assert results["AP_rare"] == np.mean(rare)
    assert results["AP_common"] == np.mean(common)
    # 稀少 3 クラス + 残り 12 クラス = 15。
    assert len(rare) == 3 and len(common) == 12


# ---------------------------------------------------------------------- #
# 4. confusion matrix の形状
# ---------------------------------------------------------------------- #
def test_confusion_matrix_shape(tmp_path):
    """confusion_matrix_similar が (4, 4) であること。"""
    ann_file, predictions, image_ids = _make_coco_and_predictions(tmp_path)
    evaluator = _build_evaluator(ann_file)
    evaluator.update(predictions, image_ids)
    results = evaluator.compute()

    cm = results["confusion_matrix_similar"]
    assert isinstance(cm, np.ndarray)
    assert cm.shape == (4, 4)
    # 予測 = GT なので similar ペアは対角に乗る。
    assert cm.trace() == cm.sum()


# ---------------------------------------------------------------------- #
# 5. PhaseEvaluator: 基本動作 (S3)
# ---------------------------------------------------------------------- #
def test_phase_evaluator_basic():
    """PhaseEvaluator が accuracy / macro F1 / per-class F1 を計算できる。"""
    from egosurgery.metrics.phase import PhaseEvaluator

    ev = PhaseEvaluator(num_classes=9, class_names=[f"p{i}" for i in range(9)])
    # 完全一致: accuracy=1, F1=1
    ev.update([0, 1, 2, 3, 4, 5, 6, 7, 8], [0, 1, 2, 3, 4, 5, 6, 7, 8], "vid_perfect")
    res = ev.compute()
    assert res["phase_accuracy"] == 1.0
    assert res["phase_macro_f1"] == 1.0
    assert all(v == 1.0 for v in res["phase_per_class_f1"].values())

    # 半分誤分類
    ev2 = PhaseEvaluator(num_classes=9)
    ev2.update([0, 0, 0, 0], [0, 1, 0, 1], "vid")
    res2 = ev2.compute()
    assert 0.0 < res2["phase_accuracy"] < 1.0


# ---------------------------------------------------------------------- #
# 6. Edit score (Levenshtein on segment-label sequences)
# ---------------------------------------------------------------------- #
def test_edit_score():
    """edit_score が 0〜100 の範囲で返り、完全一致で 100、完全不一致で低値。"""
    from egosurgery.metrics.phase import edit_score

    # 完全一致 (segment labels も一致)
    s = edit_score([0, 0, 1, 1, 2], [0, 0, 1, 1, 2], norm=True)
    assert s == 100.0

    # ラベル列が完全に異なる: pred segs=[0], gt segs=[1] -> dist 1 / max(1,1) = 100*(1-1) = 0
    s2 = edit_score([0, 0, 0], [1, 1, 1], norm=True)
    assert 0.0 <= s2 <= 100.0
    assert s2 == 0.0

    # フレーム単位で異なるがセグメントラベル列が一致 → 100
    s3 = edit_score([0, 1, 1, 2], [0, 0, 1, 2], norm=True)
    assert s3 == 100.0


# ---------------------------------------------------------------------- #
# 7. Segmental F1@k (IoU 閾値ごと)
# ---------------------------------------------------------------------- #
def test_segmental_f1():
    """segmental_f1 が 0-1 の範囲を返し、完全一致で 1、完全不一致で 0。"""
    from egosurgery.metrics.phase import segmental_f1

    for thr in (0.10, 0.25, 0.50):
        # 完全一致
        assert segmental_f1([0, 0, 1, 1, 2, 2], [0, 0, 1, 1, 2, 2], thr) == 1.0
        # ラベル違いで一致ゼロ
        assert segmental_f1([0, 0, 0], [1, 1, 1], thr) == 0.0
        # 部分一致 (IoU=0.5 で thr=0.10 / 0.25 / 0.50 とも 1 GT セグメント該当)
        v = segmental_f1([0, 0, 0, 0, 0, 1], [0, 0, 0, 1, 1, 1], thr)
        assert 0.0 <= v <= 1.0

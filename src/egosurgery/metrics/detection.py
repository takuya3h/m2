"""COCO mAP ベースの検出評価指標。

pycocotools の COCO 評価器で COCO mAP・per-class AP を計算し、
長尾分析向けに AP_rare / AP_common と形状類似ペアの混同行列も返す。

使い方:
    evaluator = DetectionEvaluator(
        ann_file="data/annotations/egosurgery_tool/instances_val.json",
        tool_classes=TOOL_CLASSES,
        rare_classes=["Skewer", "Syringe", "Forceps"],
        similar_pairs=["Forceps", "Tweezers", "Needle Holders", "Bipolar Forceps"],
    )
    evaluator.update(predictions, image_ids)   # epoch 内で逐次蓄積
    results = evaluator.compute()
    # results: mAP / mAP_50 / mAP_75 / AP_rare / AP_common /
    #          per_class_ap(15 クラス) / confusion_matrix_similar((4,4) ndarray)
"""

from __future__ import annotations

import contextlib
import io

import numpy as np

from egosurgery.metrics.confusion_matrix import compute_similar_pair_confusion


def _xywh_to_xyxy(box) -> tuple[float, float, float, float]:
    """COCO の ``[x, y, w, h]`` を ``(x1, y1, x2, y2)`` に変換する。"""
    x, y, w, h = box
    return x, y, x + w, y + h


def _iou(box_a, box_b) -> float:
    """2 つの xyxy box の IoU を返す。"""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


class DetectionEvaluator:
    """COCO mAP・per-class AP・長尾指標を計算する検出評価器。"""

    def __init__(
        self,
        ann_file: str,
        tool_classes: list[dict],
        rare_classes: list[str],
        similar_pairs: list[str],
    ) -> None:
        """
        Args:
            ann_file: 評価用 COCO アノテーション JSON。
            tool_classes: ``[{"id": int, "name": str}, ...]`` のクラス定義。
            rare_classes: 稀少クラス名（AP_rare の対象）。
            similar_pairs: 形状類似ペアのクラス名（混同行列の対象、通常 4）。
        """
        from pycocotools.coco import COCO

        # COCO のロードログを抑制する。
        with contextlib.redirect_stdout(io.StringIO()):
            self.coco_gt = COCO(ann_file)

        self.tool_classes = list(tool_classes)
        self.rare_classes = list(rare_classes)
        self.similar_pairs = list(similar_pairs)

        self.id_to_name = {c["id"]: c["name"] for c in self.tool_classes}
        self.name_to_id = {c["name"]: c["id"] for c in self.tool_classes}
        # 評価器 / per-class AP のカテゴリ順序。
        self.cat_ids = sorted(self.id_to_name)

        self._detections: list[dict] = []

    def reset(self) -> None:
        """蓄積した予測をクリアする。"""
        self._detections = []

    def update(self, predictions: list[dict], image_ids: list[int]) -> None:
        """1 バッチ分の予測を COCO 検出形式で蓄積する。

        Args:
            predictions: 画像ごとの予測 ``{"boxes": (N,4) xyxy,
                "scores": (N,), "labels": (N,)}`` のリスト。
            image_ids: 各予測に対応する COCO image_id のリスト。
        """
        for pred, image_id in zip(predictions, image_ids):
            boxes = np.asarray(pred["boxes"], dtype=np.float64).reshape(-1, 4)
            scores = np.asarray(pred["scores"], dtype=np.float64).reshape(-1)
            labels = np.asarray(pred["labels"]).reshape(-1)
            for (x1, y1, x2, y2), score, label in zip(boxes, scores, labels):
                self._detections.append(
                    {
                        "image_id": int(image_id),
                        "category_id": int(label),
                        "bbox": [x1, y1, x2 - x1, y2 - y1],
                        "score": float(score),
                    }
                )

    # ------------------------------------------------------------------ #
    # 集計
    # ------------------------------------------------------------------ #
    def compute(self) -> dict:
        """蓄積した予測から全評価指標を計算して返す。

        Returns:
            mAP / mAP_50 / mAP_75 / AP_rare / AP_common / per_class_ap /
            confusion_matrix_similar を含む辞書。
        """
        per_class_ap = {c["name"]: 0.0 for c in self.tool_classes}
        results = {
            "mAP": 0.0,
            "mAP_50": 0.0,
            "mAP_75": 0.0,
            "AP_rare": 0.0,
            "AP_common": 0.0,
            "per_class_ap": per_class_ap,
            "confusion_matrix_similar": self._compute_similar_confusion(),
        }
        if not self._detections:
            # 予測が無い（未学習等）場合は 0 埋めの結果を返す。
            return results

        from pycocotools.cocoeval import COCOeval as CocoEvaluator

        with contextlib.redirect_stdout(io.StringIO()):
            coco_dt = self.coco_gt.loadRes(self._detections)
            coco_evaluator = CocoEvaluator(self.coco_gt, coco_dt, iouType="bbox")
            coco_evaluator.params.catIds = self.cat_ids
            coco_evaluator.evaluate()
            coco_evaluator.accumulate()
            coco_evaluator.summarize()

        stats = coco_evaluator.stats
        results["mAP"] = float(stats[0])
        results["mAP_50"] = float(stats[1])
        results["mAP_75"] = float(stats[2])

        per_class_ap = self._extract_per_class_ap(coco_evaluator)
        results["per_class_ap"] = per_class_ap
        results["AP_rare"], results["AP_common"] = self._split_rare_common(
            per_class_ap
        )
        return results

    # ------------------------------------------------------------------ #
    # 内部計算
    # ------------------------------------------------------------------ #
    def _extract_per_class_ap(self, coco_evaluator) -> dict[str, float]:
        """COCO 評価器の precision テンソルから per-class AP を抽出する。"""
        # precision: (iou_thr=10, recall=101, K, area=4, maxDet=3)
        precision = coco_evaluator.eval["precision"]
        per_class_ap: dict[str, float] = {}
        for k, cat_id in enumerate(self.cat_ids):
            # area=0(all), maxDet=2(100) のスライス。
            values = precision[:, :, k, 0, 2]
            valid = values[values > -1]
            ap = float(valid.mean()) if valid.size else 0.0
            per_class_ap[self.id_to_name[cat_id]] = ap
        return per_class_ap

    def _split_rare_common(
        self, per_class_ap: dict[str, float]
    ) -> tuple[float, float]:
        """per-class AP を稀少クラスとそれ以外に分けて平均する。"""
        rare = [
            ap for name, ap in per_class_ap.items() if name in self.rare_classes
        ]
        common = [
            ap for name, ap in per_class_ap.items() if name not in self.rare_classes
        ]
        ap_rare = float(np.mean(rare)) if rare else 0.0
        ap_common = float(np.mean(common)) if common else 0.0
        return ap_rare, ap_common

    def _compute_similar_confusion(self) -> np.ndarray:
        """形状類似ペアの 4x4 混同行列を計算する。

        各 GT box（類似ペアのクラス）を、最も IoU の高い予測 box
        （IoU >= 0.5）にマッチさせ、(GT クラス, 予測クラス) を集計する。
        """
        similar_ids = {
            self.name_to_id[name]
            for name in self.similar_pairs
            if name in self.name_to_id
        }

        # 予測を image_id ごとにまとめる。
        preds_by_image: dict[int, list[dict]] = {}
        for det in self._detections:
            preds_by_image.setdefault(det["image_id"], []).append(det)

        gt_labels: list[str] = []
        pred_labels: list[str] = []
        for image_id in self.coco_gt.getImgIds():
            gt_anns = self.coco_gt.loadAnns(
                self.coco_gt.getAnnIds(imgIds=image_id)
            )
            preds = preds_by_image.get(image_id, [])
            for ann in gt_anns:
                if ann["category_id"] not in similar_ids:
                    continue
                gt_box = _xywh_to_xyxy(ann["bbox"])
                best_iou, best_pred = 0.0, None
                for pred in preds:
                    iou = _iou(gt_box, _xywh_to_xyxy(pred["bbox"]))
                    if iou > best_iou:
                        best_iou, best_pred = iou, pred
                if best_pred is not None and best_iou >= 0.5:
                    gt_labels.append(self.id_to_name[ann["category_id"]])
                    pred_labels.append(
                        self.id_to_name.get(best_pred["category_id"], "")
                    )

        return compute_similar_pair_confusion(
            pred_labels, gt_labels, self.similar_pairs
        )

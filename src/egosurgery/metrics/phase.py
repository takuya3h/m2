"""手術工程（phase）認識の評価指標。

フレーム単位の accuracy / macro F1 / per-class F1 と、セグメント単位の
Edit score / Segmental F1@{10,25,50} を提供する。

Edit score / Segmental F1 は MS-TCN（Farha & Gall, CVPR 2019）の評価コード
（https://github.com/yabufarha/ms-tcn）で広く使われる定義に従う。

使い方:
    evaluator = PhaseEvaluator(num_classes=9, class_names=[...])
    for pred_seq, gt_seq, vid in zip(preds, gts, video_ids):
        evaluator.update(pred_seq, gt_seq, vid)
    results = evaluator.compute()
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np


def _to_label_array(seq: Iterable[int]) -> np.ndarray:
    """任意の整数列を 1 次元 numpy int 配列に揃える。"""
    return np.asarray(list(seq), dtype=np.int64)


def _segments_from_labels(labels: np.ndarray) -> list[tuple[int, int, int]]:
    """フレーム列をセグメント（(start, end_exclusive, label)）に圧縮する。"""
    if labels.size == 0:
        return []
    segments: list[tuple[int, int, int]] = []
    start = 0
    for i in range(1, len(labels)):
        if labels[i] != labels[i - 1]:
            segments.append((start, i, int(labels[i - 1])))
            start = i
    segments.append((start, len(labels), int(labels[-1])))
    return segments


def edit_score(pred: Sequence[int], gt: Sequence[int], norm: bool = True) -> float:
    """セグメント列の Levenshtein 距離を 0-100 スコアへ正規化する。

    フレーム列ではなく **セグメントラベル列** に対する編集距離を計算する。
    たとえば pred=[1,1,1,2,2] → segment labels [1,2]、gt=[1,1,2,2,2] → [1,2]。

    Args:
        pred: 予測フレーム列。
        gt: 正解フレーム列。
        norm: ``True`` で ``100 * (1 - edit / max(len_p, len_g))`` を返す（既定）。
            ``False`` で生の編集距離（int）を返す。

    Returns:
        スコア（0-100）または編集距離。完全一致で 100。
    """
    p_lbls = [s[2] for s in _segments_from_labels(_to_label_array(pred))]
    g_lbls = [s[2] for s in _segments_from_labels(_to_label_array(gt))]
    n, m = len(p_lbls), len(g_lbls)
    if n == 0 and m == 0:
        return 100.0 if norm else 0.0
    # 動的計画法 (Wagner-Fischer)
    dp = np.zeros((n + 1, m + 1), dtype=np.int64)
    dp[:, 0] = np.arange(n + 1)
    dp[0, :] = np.arange(m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if p_lbls[i - 1] == g_lbls[j - 1] else 1
            dp[i, j] = min(
                dp[i - 1, j] + 1,
                dp[i, j - 1] + 1,
                dp[i - 1, j - 1] + cost,
            )
    dist = int(dp[n, m])
    if not norm:
        return float(dist)
    return float(100.0 * (1.0 - dist / max(n, m, 1)))


def _segment_iou(
    seg_a: tuple[int, int],
    seg_b: tuple[int, int],
) -> float:
    """1 次元区間の IoU（frame index 上）。"""
    a0, a1 = seg_a
    b0, b1 = seg_b
    inter = max(0, min(a1, b1) - max(a0, b0))
    union = max(a1, b1) - min(a0, b0)
    return inter / union if union > 0 else 0.0


def segmental_f1(
    pred: Sequence[int],
    gt: Sequence[int],
    threshold: float = 0.5,
) -> float:
    """指定 IoU 閾値での セグメント単位 F1 を返す（0-1）。

    各 GT セグメントに対し、同じラベルかつ IoU≥threshold となる予測セグメントの
    うち未使用の中で IoU 最大のものを 1 つマッチさせる（greedy）。

    Args:
        pred: 予測フレーム列。
        gt: 正解フレーム列。
        threshold: IoU 閾値（例 0.10 / 0.25 / 0.50）。

    Returns:
        F1 スコア（0-1）。
    """
    p_segs = _segments_from_labels(_to_label_array(pred))
    g_segs = _segments_from_labels(_to_label_array(gt))
    if not p_segs and not g_segs:
        return 1.0
    if not p_segs or not g_segs:
        return 0.0
    used_p = [False] * len(p_segs)
    tp = 0
    for gs, ge, gl in g_segs:
        best_iou, best_j = 0.0, -1
        for j, (ps, pe, pl) in enumerate(p_segs):
            if used_p[j] or pl != gl:
                continue
            iou = _segment_iou((gs, ge), (ps, pe))
            if iou > best_iou:
                best_iou, best_j = iou, j
        if best_j >= 0 and best_iou >= threshold:
            used_p[best_j] = True
            tp += 1
    fp = sum(1 for u in used_p if not u)
    fn = len(g_segs) - tp
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return float(2 * precision * recall / (precision + recall))


class PhaseEvaluator:
    """phase 推論結果を動画ごとに蓄積し、複合指標へ集計する。

    Args:
        num_classes: クラス数（既定 9）。
        class_names: クラス名のリスト（per-class F1 のキーに使用、長さ ``num_classes``）。
            ``None`` のときは ``str(i)`` を用いる。
    """

    def __init__(
        self,
        num_classes: int = 9,
        class_names: Sequence[str] | None = None,
    ) -> None:
        self.num_classes = int(num_classes)
        if class_names is None:
            self.class_names = [str(i) for i in range(self.num_classes)]
        else:
            assert len(class_names) == num_classes
            self.class_names = list(class_names)
        # video_id -> (preds, gts) を保持して動画単位で segment 指標を計算する。
        self._videos: dict[str, tuple[list[int], list[int]]] = {}

    def reset(self) -> None:
        """蓄積をクリアする。"""
        self._videos.clear()

    def update(
        self,
        predictions: Iterable[int],
        gt_labels: Iterable[int],
        video_id: str | int = "all",
    ) -> None:
        """同一動画のフレーム列予測と GT を追記する。

        Args:
            predictions: フレームごとの予測クラス id 列。
            gt_labels: 同長の正解クラス id 列。
            video_id: 集計単位。同じ id で複数回呼ぶと連結される。
        """
        key = str(video_id)
        preds, gts = self._videos.setdefault(key, ([], []))
        preds.extend(int(x) for x in predictions)
        gts.extend(int(x) for x in gt_labels)

    def compute(self) -> dict:
        """蓄積データから複合指標を計算して返す。

        Returns:
            ``{"phase_accuracy": float, "phase_macro_f1": float,
              "phase_edit_score": float, "phase_seg_f1_10": float,
              "phase_seg_f1_25": float, "phase_seg_f1_50": float,
              "phase_per_class_f1": dict[str, float]}``
        """
        all_preds: list[int] = []
        all_gts: list[int] = []
        for preds, gts in self._videos.values():
            all_preds.extend(preds)
            all_gts.extend(gts)
        if not all_preds:
            return {
                "phase_accuracy": 0.0,
                "phase_macro_f1": 0.0,
                "phase_edit_score": 0.0,
                "phase_seg_f1_10": 0.0,
                "phase_seg_f1_25": 0.0,
                "phase_seg_f1_50": 0.0,
                "phase_per_class_f1": {n: 0.0 for n in self.class_names},
            }

        preds_arr = np.asarray(all_preds, dtype=np.int64)
        gts_arr = np.asarray(all_gts, dtype=np.int64)

        # frame-level
        accuracy = float((preds_arr == gts_arr).mean())
        per_class_f1, macro_f1 = self._frame_f1(preds_arr, gts_arr)

        # segment-level: 動画ごとに計算して平均する。
        edits, f10, f25, f50 = [], [], [], []
        for preds, gts in self._videos.values():
            edits.append(edit_score(preds, gts, norm=True))
            f10.append(segmental_f1(preds, gts, 0.10))
            f25.append(segmental_f1(preds, gts, 0.25))
            f50.append(segmental_f1(preds, gts, 0.50))

        return {
            "phase_accuracy": accuracy,
            "phase_macro_f1": float(macro_f1),
            "phase_edit_score": float(np.mean(edits)) if edits else 0.0,
            "phase_seg_f1_10": float(np.mean(f10)) if f10 else 0.0,
            "phase_seg_f1_25": float(np.mean(f25)) if f25 else 0.0,
            "phase_seg_f1_50": float(np.mean(f50)) if f50 else 0.0,
            "phase_per_class_f1": {
                self.class_names[c]: float(per_class_f1[c]) for c in range(self.num_classes)
            },
        }

    def _frame_f1(
        self, preds: np.ndarray, gts: np.ndarray
    ) -> tuple[np.ndarray, float]:
        """フレーム単位の per-class F1 と macro F1 を返す。"""
        per_class = np.zeros(self.num_classes, dtype=np.float64)
        for c in range(self.num_classes):
            tp = int(((preds == c) & (gts == c)).sum())
            fp = int(((preds == c) & (gts != c)).sum())
            fn = int(((preds != c) & (gts == c)).sum())
            if tp + fp == 0 or tp + fn == 0 or tp == 0:
                per_class[c] = 0.0
                continue
            precision = tp / (tp + fp)
            recall = tp / (tp + fn)
            per_class[c] = 2 * precision * recall / (precision + recall)
        # クラス存在のあるものだけで macro F1 を取る（全 GT 不在のクラスは除外）。
        present = np.array([(gts == c).any() for c in range(self.num_classes)])
        if present.any():
            macro = per_class[present].mean()
        else:
            macro = 0.0
        return per_class, float(macro)

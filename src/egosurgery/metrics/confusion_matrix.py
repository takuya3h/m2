"""形状類似ペアの sub-confusion matrix を計算・可視化する。

研究計画の長尾分析では、形状が似た術具対（Forceps / Tweezers /
Needle Holders / Bipolar Forceps）の誤分類が APr 低下の主因と仮説する。
本モジュールはその 4 クラス間の混同行列を計算し heatmap で保存する。

使い方:
    cm = compute_similar_pair_confusion(pred_labels, gt_labels, pair_classes)
    save_confusion_matrix(cm, pair_classes, save_path)
    # -> {save_path}.png / {save_path}_recall.png / {save_path}_precision.png
"""

from __future__ import annotations

from pathlib import Path

# GUI バックエンド非依存（ヘッドレス環境で保存するため）。
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def compute_similar_pair_confusion(
    pred_labels,
    gt_labels,
    pair_classes: list[str],
) -> np.ndarray:
    """マッチング済みの予測ラベルと GT ラベルから混同行列を計算する。

    Args:
        pred_labels: マッチした予測のクラス名（または ID）の系列。
        gt_labels: 対応する GT のクラス名（または ID）の系列。
        pair_classes: 行・列の順序を定める対象クラス（通常 4 クラス）。

    Returns:
        ``(K, K)`` の混同行列（``K = len(pair_classes)``）。
        行 = GT、列 = 予測。
    """
    index = {cls: i for i, cls in enumerate(pair_classes)}
    size = len(pair_classes)
    cm = np.zeros((size, size), dtype=np.int64)
    for gt, pred in zip(gt_labels, pred_labels):
        if gt in index and pred in index:
            cm[index[gt], index[pred]] += 1
    return cm


def normalize_confusion(cm: np.ndarray, axis: int) -> np.ndarray:
    """混同行列を行方向（recall）/ 列方向（precision）に正規化する。

    Args:
        cm: 混同行列。
        axis: ``1`` で行正規化（recall）、``0`` で列正規化（precision）。

    Returns:
        正規化済み行列（合計 0 の行/列は 0 のまま）。
    """
    cm = cm.astype(np.float64)
    totals = cm.sum(axis=axis, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        normalized = np.where(totals > 0, cm / totals, 0.0)
    return normalized


def save_confusion_matrix(
    cm: np.ndarray,
    pair_classes: list[str],
    save_path: str | Path,
) -> list[Path]:
    """混同行列の heatmap（生・recall 正規化・precision 正規化）を保存する。

    Args:
        cm: 混同行列 ``(K, K)``。
        pair_classes: クラス名（軸ラベル）。
        save_path: 保存先のベースパス（拡張子は自動付与）。

    Returns:
        保存した PNG ファイルパスのリスト。
    """
    base = Path(save_path)
    base.parent.mkdir(parents=True, exist_ok=True)
    stem = base.with_suffix("")

    variants = {
        "": (cm.astype(np.int64), "Confusion (counts)", "d"),
        "_recall": (
            normalize_confusion(cm, axis=1),
            "Confusion (recall-normalized)",
            ".2f",
        ),
        "_precision": (
            normalize_confusion(cm, axis=0),
            "Confusion (precision-normalized)",
            ".2f",
        ),
    }
    saved: list[Path] = []
    for suffix, (matrix, title, fmt) in variants.items():
        out_path = Path(f"{stem}{suffix}.png")
        _plot_heatmap(matrix, pair_classes, title, fmt, out_path)
        saved.append(out_path)
    return saved


def _plot_heatmap(
    matrix: np.ndarray,
    labels: list[str],
    title: str,
    fmt: str,
    out_path: Path,
) -> None:
    """1 枚の heatmap を描画してファイルに保存する。"""
    fig, ax = plt.subplots(figsize=(5.5, 5))
    image = ax.imshow(matrix, cmap="Blues", vmin=0)
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Ground Truth")
    ax.set_title(title)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            ax.text(
                j, i, format(value, fmt),
                ha="center", va="center",
                color="white" if value > matrix.max() / 2 else "black",
            )
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)

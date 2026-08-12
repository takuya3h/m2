# =============================================================================
# Adapted from: https://github.com/open-mmlab/mmdetection (projects/CO-DETR)
# Original authors: Zong et al. (ICCV 2023,
#                  "DETRs with Collaborative Hybrid Assignments Training")
# License: Apache 2.0
# Modifications: EgoSurgery-Tool 用にクラス数・入力次元を調整、
#                DINOv2 ViT-L/14 + ViT-Adapter backbone への接続。
#                test_cfg は MMDetTrainer._build_mmdet_cfg が locked-down 値
#                （§15.3 G1）で強制上書きするため、ヘッド側は受け取り口だけ持つ。
# =============================================================================
"""Co-DETR 検出ヘッドのラッパー（§4.2・§13.2 S0・§9 #6）。

位置づけ:
    - 長尾対照（long-tail 耐性の比較対象）。
    - Co-DETR は collaborative hybrid assignment（one-to-many 補助ヘッド併用）
      により、DETR 系の Hungarian one-to-one matching が稀少クラスの query を
      早期 quench する構造的バイアスを緩和する設計。
    - §9 #6 の判断ポイント: S0 完了時に Mask DINO vs Co-DETR を APr
      （稀少クラス AP）で比較し、3pt 以上の差が出れば S1 以降を Co-DETR
      ベースに切り替える。

実装方針:
    - mmdet の ``projects/CO-DETR`` の ``CoDETR`` をラップする（方式 C）。
    - backbone は Mask DINO / VFNet と同一の DINOv2 ViT-L/14-with-registers +
      ViT-Adapter を使い、検出ヘッドのみを差し替える（Δ 基準点の公平性のため
      backbone を揃える）。
    - test_cfg は Part 3 の ``MMDetTrainer._build_mmdet_cfg`` が
      locked-down 値で強制上書きする（§15.3 G1）。CoDETRHead 側はその値を
      受け取れる口を持つ。

【SyncBatchNorm 方針・§13.2 (b)(iv)】
    Co-DETR の transformer decoder 部分は LayerNorm 主体で BatchNorm を含まない。
    補助 ATSS ヘッド（``aux_heads.enabled=true``）が畳み込み + BatchNorm を
    含む場合のみ ``SyncBatchNorm`` 変換の対象となる。実際の判定は
    ``MMDetTrainer._build_model()`` が ``any(isinstance(m, nn.BatchNorm*) ...)``
    で行うため、本ヘッド側で特別な対応は不要。
"""

from __future__ import annotations

import warnings

from torch import nn


def is_codetr_available() -> bool:
    """mmdet と projects/CO-DETR が import 可能なら ``True``。"""
    try:
        import mmdet  # noqa: F401
        # mmdet 3.x では projects/CO-DETR は別 path 配下に格納される。
        # 環境差を吸収するため、複数経路を試す。
        try:
            from mmdet.models.detectors import CoDETR  # noqa: F401
            return True
        except Exception:
            pass
        try:
            # projects/CO-DETR を実装する代替経路（mmdet 同梱の register 経由）。
            from mmdet.registry import MODELS
            # MODELS register に "CoDETR" が登録されていれば利用可能。
            _ = MODELS.get("CoDETR")
            return True
        except Exception:
            return False
    except Exception:
        return False


def build_codetr_head_cfg(cfg, num_classes: int) -> dict:
    """Hydra config から mmdet projects/CO-DETR の CoDETR 構築用 dict を組む。

    実装上は CoDETR は detector 全体（backbone を内包）として登録されているが、
    本プロジェクトでは backbone を DINOv2 + ViT-Adapter で外注しているため、
    最小の query / transformer 設定だけを構築する。

    Args:
        cfg: ``codetr.yaml`` 由来の設定。
        num_classes: 検出クラス数（tool=15）。

    Returns:
        ``mmdet.registry.MODELS.build`` に渡す dict。
    """
    aux_heads = cfg.get("aux_heads", {})
    return {
        "type": "CoDETR",
        "num_classes": int(num_classes),
        "num_queries": int(cfg.get("num_queries", 300)),
        "with_box_refine": bool(cfg.get("with_box_refine", True)),
        "as_two_stage": bool(cfg.get("as_two_stage", True)),
        # Co-DETR の核となる collaborative hybrid assignment
        # （one-to-many 補助 ATSS / Faster-RCNN ヘッドの併用）。
        # 長尾 query quench 緩和の核（§4.2）。
        "use_lsj": bool(cfg.get("use_lsj", False)),
        "eval_module": str(cfg.get("eval_module", "detr")),
        "with_aux_head": bool(aux_heads.get("enabled", True)),
    }


class CoDETRHead(nn.Module):
    """Co-DETR 検出ヘッドのラッパー（mmdet projects/CO-DETR 非依存環境では無効化）。"""

    def __init__(
        self,
        cfg,
        test_detections_per_img: int = 300,
        test_score_thr: float = 1e-8,
    ) -> None:
        """
        Args:
            cfg: 検出ヘッド設定（``codetr.yaml`` 由来）。
            test_detections_per_img: 評価時の検出数上限（§15.3 G1、既定 300）。
            test_score_thr: 評価時のスコア閾値（§15.3 G1、既定 1e-8）。
                実値の適用は Part 3 の ``MMDetTrainer._build_mmdet_cfg`` で
                行うが、本ヘッドはそれを受け取れる口を持つ。
        """
        super().__init__()
        self.cfg = cfg
        self.test_detections_per_img = int(test_detections_per_img)
        self.test_score_thr = float(test_score_thr)
        self.num_classes = int(cfg.get("num_classes", 15))
        self.available = is_codetr_available()
        self._head: nn.Module | None = None

        if not self.available:
            warnings.warn(
                "mmdet projects/CO-DETR が利用できないため、CoDETRHead は "
                "無効化されます（forward / predict は None を返します）。",
                RuntimeWarning,
            )

    def setup(self, backbone=None) -> None:
        """mmdet の CoDETR を構築する。

        Args:
            backbone: 特徴を供給する backbone（インターフェース整合用、未使用可）。
        """
        if not self.available:
            return
        try:
            from mmdet.registry import MODELS

            head_cfg = build_codetr_head_cfg(self.cfg, self.num_classes)
            self._head = MODELS.build(head_cfg)
        except Exception as exc:  # mmdet バージョン差・依存欠落に備える。
            warnings.warn(
                f"CoDETR の構築に失敗したため無効化します: {exc!r}",
                RuntimeWarning,
            )
            self.available = False
            self._head = None

    def forward(self, features, targets=None):
        """学習時の損失を計算する。

        Args:
            features: ViT-Adapter の 4 段階マルチスケール特徴。
            targets: 検出 target。

        Returns:
            損失辞書。非対応環境では ``None``。
        """
        if not self.available or self._head is None:
            return None
        return self._head(features)  # pragma: no cover - 環境依存

    def predict(self, features):
        """推論時の検出結果を返す。

        Returns:
            ``{"boxes", "scores", "labels"}``。非対応環境では ``None``。
        """
        if not self.available or self._head is None:
            return None
        return self._head(features)  # pragma: no cover - 環境依存

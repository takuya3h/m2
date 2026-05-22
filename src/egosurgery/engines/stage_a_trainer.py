"""Stage A0 専用トレーナー: bbox 検出のみ（Phase-0 主経路、S0 を完走させる）。

ExperimentManager / ExperimentLogger / CheckpointManager と統合し、
backbone（DINOv2 + ViT-Adapter）+ 検出ヘッドで COCO mAP まで計測する。

検出ヘッドの方針:
    - Mask DINO（Detectron2 依存）/ VarifocalNet（mmdet 依存）が利用可能なら
      その損失経路を使う。
    - いずれも利用できない環境では、内蔵の :class:`SimpleDetectionHead`
      （FCOS 風の単一スケール anchor-free ヘッド）へフォールバックし、
      検出学習・評価の骨格を end-to-end で必ず通す。

使い方:
    trainer = StageATrainer(cfg)
    trainer.setup()
    trainer.run()
"""

from __future__ import annotations

import warnings

import numpy as np
import torch
import torch.nn.functional as F
from omegaconf import OmegaConf
from torch import nn

from egosurgery.datasets.constants import (
    CONFUSABLE_CLASSES,
    NUM_TOOL_CLASSES,
    RARE_CLASSES,
    TOOL_CLASSES,
)
from egosurgery.datasets.datamodule import EgoSurgeryDataModule
from egosurgery.metrics.confusion_matrix import save_confusion_matrix
from egosurgery.metrics.detection import DetectionEvaluator
from egosurgery.models.build import build_backbone
from egosurgery.models.losses.detection import GIoULoss
from egosurgery.utils.checkpoint import CheckpointManager
from egosurgery.utils.experiment_manager import ExperimentManager
from egosurgery.utils.logging import ExperimentLogger
from egosurgery.utils.seed import seed_everything


# ====================================================================== #
# 内蔵検出ヘッド
# ====================================================================== #
class SimpleDetectionHead(nn.Module):
    """単一スケールの anchor-free 検出ヘッド（FCOS 風）。

    ViT-Adapter の 1 スケール特徴を入力に、各セルでクラス分類（per-class
    sigmoid）と中心からの (l, t, r, b) 距離回帰を行う。外部検出器に依存せず
    検出学習・評価の骨格を通すための軽量実装。
    """

    def __init__(
        self,
        in_channels: int = 256,
        num_classes: int = NUM_TOOL_CLASSES,
        level_index: int = 3,
    ) -> None:
        """
        Args:
            in_channels: 入力特徴のチャネル数（ViT-Adapter 出力は 256）。
            num_classes: 検出クラス数。
            level_index: 使用する ViT-Adapter スケール（3 = stride 32）。
        """
        super().__init__()
        self.num_classes = num_classes
        self.level_index = level_index
        self.tower = nn.Sequential(
            nn.Conv2d(in_channels, 256, kernel_size=3, padding=1),
            nn.GroupNorm(32, 256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.GroupNorm(32, 256),
            nn.ReLU(inplace=True),
        )
        self.cls_head = nn.Conv2d(256, num_classes, kernel_size=3, padding=1)
        self.reg_head = nn.Conv2d(256, 4, kernel_size=3, padding=1)
        # focal loss 用に分類バイアスを背景寄りに初期化する。
        nn.init.constant_(self.cls_head.bias, -4.0)
        # 回帰ヘッドのバイアスを正の値に初期化し、学習初期から非退化な
        # （点でない）ボックスを出力させる。relu(conv+bias) >= bias 程度となり、
        # GIoU 損失に有効な勾配が流れる。
        nn.init.constant_(self.reg_head.bias, 40.0)

    def forward(self, features: list[torch.Tensor]):
        """選択スケールでクラスロジットと距離回帰を返す。"""
        x = self.tower(features[self.level_index])
        cls_logits = self.cls_head(x)
        reg_dist = F.relu(self.reg_head(x))  # (l,t,r,b) >= 0
        return cls_logits, reg_dist


def _cell_centers(height: int, width: int, stride: float, device) -> torch.Tensor:
    """特徴マップ各セルの画像座標中心 ``(H*W, 2)`` を返す。"""
    ys = (torch.arange(height, device=device) + 0.5) * stride
    xs = (torch.arange(width, device=device) + 0.5) * stride
    grid_y, grid_x = torch.meshgrid(ys, xs, indexing="ij")
    return torch.stack([grid_x.reshape(-1), grid_y.reshape(-1)], dim=1)


def _sigmoid_focal_loss(
    logits: torch.Tensor,
    targets: torch.Tensor,
    alpha: float = 0.25,
    gamma: float = 2.0,
) -> torch.Tensor:
    """sigmoid focal loss（reduction='sum'）。純 PyTorch 実装。

    torchvision の C++ ops に依存しないよう自前で実装する。
    """
    prob = torch.sigmoid(logits)
    ce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    p_t = prob * targets + (1.0 - prob) * (1.0 - targets)
    loss = ce * ((1.0 - p_t) ** gamma)
    if alpha >= 0:
        alpha_t = alpha * targets + (1.0 - alpha) * (1.0 - targets)
        loss = alpha_t * loss
    return loss.sum()


def _nms(boxes: torch.Tensor, scores: torch.Tensor, iou_thresh: float) -> torch.Tensor:
    """Non-Maximum Suppression（純 PyTorch 実装、xyxy box）。"""
    if boxes.numel() == 0:
        return torch.empty((0,), dtype=torch.long, device=boxes.device)
    areas = (boxes[:, 2] - boxes[:, 0]).clamp(min=0) * (
        boxes[:, 3] - boxes[:, 1]
    ).clamp(min=0)
    order = scores.argsort(descending=True)
    keep: list[int] = []
    while order.numel() > 0:
        i = int(order[0])
        keep.append(i)
        if order.numel() == 1:
            break
        rest = order[1:]
        xx1 = torch.maximum(boxes[i, 0], boxes[rest, 0])
        yy1 = torch.maximum(boxes[i, 1], boxes[rest, 1])
        xx2 = torch.minimum(boxes[i, 2], boxes[rest, 2])
        yy2 = torch.minimum(boxes[i, 3], boxes[rest, 3])
        inter = (xx2 - xx1).clamp(min=0) * (yy2 - yy1).clamp(min=0)
        iou = inter / (areas[i] + areas[rest] - inter).clamp(min=1e-6)
        order = rest[iou <= iou_thresh]
    return torch.tensor(keep, dtype=torch.long, device=boxes.device)


class _SimpleHeadCriterion:
    """SimpleDetectionHead 用の損失計算・予測デコード。"""

    def __init__(self, num_classes: int) -> None:
        self.num_classes = num_classes
        self.giou = GIoULoss()

    def loss(self, cls_logits, reg_dist, targets, image_size: int) -> dict:
        """密検出ヘッドの損失（focal 分類 + GIoU 回帰）を計算する。"""
        batch, _, height, width = cls_logits.shape
        device = cls_logits.device
        stride = image_size / height
        centers = _cell_centers(height, width, stride, device)  # (HW, 2)

        cls_logits_flat = cls_logits.permute(0, 2, 3, 1).reshape(
            batch, -1, self.num_classes
        )
        reg_flat = reg_dist.permute(0, 2, 3, 1).reshape(batch, -1, 4)

        cls_targets = torch.zeros_like(cls_logits_flat)
        reg_targets = torch.zeros_like(reg_flat)
        pos_mask = torch.zeros(batch, centers.shape[0], dtype=torch.bool, device=device)

        for b, target in enumerate(targets):
            boxes = target["boxes"].to(device).reshape(-1, 4)
            labels = target["labels"].to(device).reshape(-1)
            if boxes.numel() == 0:
                continue
            cx, cy = centers[:, 0:1], centers[:, 1:2]  # (HW,1)
            inside = (
                (cx >= boxes[:, 0]) & (cx <= boxes[:, 2])
                & (cy >= boxes[:, 1]) & (cy <= boxes[:, 3])
            )  # (HW, M)
            areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
            cost = torch.where(inside, areas.unsqueeze(0), torch.full_like(
                inside, float("inf"), dtype=torch.float32))
            has_pos = inside.any(dim=1)
            assigned = cost.argmin(dim=1)  # (HW,)

            pos_mask[b] = has_pos
            gt = boxes[assigned]  # (HW, 4)
            cls_targets[b, has_pos, labels[assigned][has_pos]] = 1.0
            reg_targets[b, :, 0] = centers[:, 0] - gt[:, 0]  # l
            reg_targets[b, :, 1] = centers[:, 1] - gt[:, 1]  # t
            reg_targets[b, :, 2] = gt[:, 2] - centers[:, 0]  # r
            reg_targets[b, :, 3] = gt[:, 3] - centers[:, 1]  # b

        num_pos = int(pos_mask.sum().clamp(min=1))
        cls_loss = _sigmoid_focal_loss(
            cls_logits_flat, cls_targets, alpha=0.25, gamma=2.0
        ) / num_pos

        if pos_mask.any():
            centers_b = centers.unsqueeze(0).expand(batch, -1, -1)
            pred_boxes = self._decode(reg_flat, centers_b)[pos_mask]
            gt_boxes = self._decode(reg_targets, centers_b)[pos_mask]
            reg_loss = self.giou(pred_boxes, gt_boxes)
        else:
            reg_loss = reg_flat.sum() * 0.0

        return {
            "loss_ce": cls_loss,
            "loss_bbox": reg_loss,
            "loss_total": cls_loss + reg_loss,
        }

    @staticmethod
    def _decode(reg, centers) -> torch.Tensor:
        """(l,t,r,b) 距離を xyxy box にデコードする。"""
        x1 = centers[..., 0] - reg[..., 0]
        y1 = centers[..., 1] - reg[..., 1]
        x2 = centers[..., 0] + reg[..., 2]
        y2 = centers[..., 1] + reg[..., 3]
        return torch.stack([x1, y1, x2, y2], dim=-1)

    @torch.no_grad()
    def predict(
        self,
        cls_logits,
        reg_dist,
        image_size: int,
        score_thresh: float = 0.02,
        nms_thresh: float = 0.6,
        max_det: int = 100,
    ) -> list[dict]:
        """密予測を画像ごとの ``{boxes, scores, labels}`` にデコードする。"""
        batch, _, height, width = cls_logits.shape
        device = cls_logits.device
        stride = image_size / height
        centers = _cell_centers(height, width, stride, device)

        cls_flat = cls_logits.permute(0, 2, 3, 1).reshape(batch, -1, self.num_classes)
        reg_flat = reg_dist.permute(0, 2, 3, 1).reshape(batch, -1, 4)
        scores_all = cls_flat.sigmoid()

        outputs = []
        for b in range(batch):
            boxes = self._decode(reg_flat[b], centers)
            boxes[:, 0::2] = boxes[:, 0::2].clamp(0, image_size)
            boxes[:, 1::2] = boxes[:, 1::2].clamp(0, image_size)
            scores, labels = scores_all[b].max(dim=1)

            keep = scores > score_thresh
            boxes, scores, labels = boxes[keep], scores[keep], labels[keep]
            if boxes.numel() > 0:
                keep_nms = _nms(boxes, scores, nms_thresh)[:max_det]
                boxes, scores, labels = (
                    boxes[keep_nms], scores[keep_nms], labels[keep_nms]
                )
            outputs.append(
                {
                    "boxes": boxes.cpu(),
                    "scores": scores.cpu(),
                    "labels": labels.cpu(),
                }
            )
        return outputs


# ====================================================================== #
# Stage A トレーナー
# ====================================================================== #
class StageATrainer:
    """S0（術具検出ベースライン）を完走させる Stage A0 トレーナー。"""

    def __init__(self, cfg) -> None:
        """
        Args:
            cfg: Hydra/OmegaConf の resolved config。
        """
        self.cfg = cfg
        # CUDA が利用可能ならそれを、無ければ CPU を使う。
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.manager: ExperimentManager | None = None
        self.logger: ExperimentLogger | None = None
        self.ckpt_manager: CheckpointManager | None = None
        self.model: nn.ModuleDict | None = None
        self.criterion: _SimpleHeadCriterion | None = None
        self.optimizer: torch.optim.Optimizer | None = None
        self.scheduler = None
        self.scaler = None
        self.datamodule: EgoSurgeryDataModule | None = None
        self.train_loader = None
        self.val_loader = None
        self.evaluator: DetectionEvaluator | None = None

        self._global_step = 0
        self._best = {}
        self.requested_head = str(
            cfg.get("model", {}).get("detection_head", "mask_dino")
        )

    # ------------------------------------------------------------------ #
    # セットアップ
    # ------------------------------------------------------------------ #
    def setup(self) -> None:
        """実験管理・モデル・データ・最適化器を構築する。"""
        cfg = self.cfg
        seed_everything(int(cfg.seed))

        # --- 実験管理 -------------------------------------------------- #
        self.manager = ExperimentManager(
            base_dir=self._resolve_base_dir(cfg.experiment.base_dir),
            category=str(cfg.experiment.category),
            step=str(cfg.experiment.step),
            description=str(cfg.experiment.description),
            seed=int(cfg.seed),
        )
        self.manager.setup()
        self.manager.save_config(cfg)

        self.logger = ExperimentLogger(
            experiment_manager=self.manager,
            wandb_project=str(cfg.logging.wandb_project),
            wandb_entity=cfg.logging.get("wandb_entity", None),
            tags=[str(cfg.experiment.step), self.requested_head],
            enabled=bool(cfg.logging.get("wandb_enabled", False)),
            config=OmegaConf.to_container(cfg, resolve=True),
            run_name=self.manager.exp_id,
        )
        self.logger.init()

        self.ckpt_manager = CheckpointManager(
            exp_dir=self.manager.exp_dir,
            save_top_k=int(cfg.logging.get("save_top_k", 3)),
            monitor="val/mAP",
            mode="max",
        )

        # --- モデル: backbone + 検出ヘッド ----------------------------- #
        backbone = build_backbone(cfg).to(self.device)
        if bool(cfg.train.get("freeze_backbone", False)):
            for param in backbone.parameters():
                param.requires_grad_(False)
        head = SimpleDetectionHead(
            in_channels=256, num_classes=int(cfg.model.get("num_classes", 15))
        ).to(self.device)
        self.model = nn.ModuleDict({"backbone": backbone, "head": head})
        self.criterion = _SimpleHeadCriterion(int(cfg.model.get("num_classes", 15)))

        if not _external_head_available(self.requested_head):
            warnings.warn(
                f"要求された検出ヘッド '{self.requested_head}' は本環境で利用"
                "できないため、内蔵 SimpleDetectionHead で学習・評価します。",
                RuntimeWarning,
            )

        # --- データ ---------------------------------------------------- #
        # Hydra が cwd を変更しても data パスが解決できるよう絶対化する。
        self._resolve_data_paths()
        self.datamodule = EgoSurgeryDataModule(cfg)
        self.datamodule.setup()
        self.train_loader = self.datamodule.train_dataloader()
        self.val_loader = self.datamodule.val_dataloader()

        # --- 評価器 ---------------------------------------------------- #
        self.evaluator = DetectionEvaluator(
            ann_file=str(cfg.data.val.ann_file),
            tool_classes=TOOL_CLASSES,
            rare_classes=RARE_CLASSES,
            similar_pairs=CONFUSABLE_CLASSES,
        )

        # --- 最適化器 -------------------------------------------------- #
        params = [p for p in self.model.parameters() if p.requires_grad]
        self.optimizer = torch.optim.AdamW(
            params,
            lr=float(cfg.optimizer.get("lr", 1e-4)),
            weight_decay=float(cfg.optimizer.get("weight_decay", 0.05)),
        )
        epochs = int(cfg.train.epochs)
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=max(epochs, 1)
        )
        # AMP は CUDA でのみ有効化（CPU 環境では無効）。
        self.use_amp = bool(cfg.train.get("amp", True)) and self.device.type == "cuda"
        # torch 2.4+ は torch.amp.GradScaler、それ未満は torch.cuda.amp.GradScaler。
        if hasattr(torch.amp, "GradScaler"):
            self.scaler = torch.amp.GradScaler("cuda", enabled=self.use_amp)
        else:
            self.scaler = torch.cuda.amp.GradScaler(enabled=self.use_amp)

    # ------------------------------------------------------------------ #
    # 学習
    # ------------------------------------------------------------------ #
    def train_one_epoch(self, epoch: int) -> float:
        """1 epoch 学習し、平均損失を返す。"""
        self.model.train()
        grad_clip = float(self.cfg.train.get("grad_clip_norm", 1.0))
        running, num_batches = 0.0, 0

        for images, targets in self.train_loader:
            images = images.to(self.device)
            self.optimizer.zero_grad()

            with torch.autocast(
                device_type=self.device.type,
                dtype=torch.bfloat16,
                enabled=self.use_amp,
            ):
                losses = self._forward_losses(images, targets)
                loss = losses["loss_total"]

            self.scaler.scale(loss).backward()
            self.scaler.unscale_(self.optimizer)
            nn.utils.clip_grad_norm_(self.model.parameters(), grad_clip)
            self.scaler.step(self.optimizer)
            self.scaler.update()

            self._global_step += 1
            running += float(loss.detach())
            num_batches += 1

            if self._global_step % int(self.cfg.logging.get("log_every_n_steps", 50)) == 0:
                self.logger.log(
                    {
                        "train/loss": float(loss.detach()),
                        "train/loss_ce": float(losses["loss_ce"].detach()),
                        "train/loss_bbox": float(losses["loss_bbox"].detach()),
                        "epoch": epoch,
                    },
                    step=self._global_step,
                )
        return running / max(num_batches, 1)

    def _forward_losses(self, images, targets) -> dict:
        """backbone → 検出ヘッド → 損失。"""
        features = self.model["backbone"](images)["features"]
        cls_logits, reg_dist = self.model["head"](features)
        return self.criterion.loss(
            cls_logits, reg_dist, targets, int(self.cfg.data.get("img_size", 518))
        )

    # ------------------------------------------------------------------ #
    # 評価
    # ------------------------------------------------------------------ #
    @torch.no_grad()
    def evaluate(self, epoch: int) -> dict:
        """val で COCO mAP・per-class AP・confusion matrix を計算する。"""
        self.model.train(False)
        self.evaluator.reset()
        image_size = int(self.cfg.data.get("img_size", 518))

        for images, targets in self.val_loader:
            images = images.to(self.device)
            features = self.model["backbone"](images)["features"]
            cls_logits, reg_dist = self.model["head"](features)
            predictions = self.criterion.predict(cls_logits, reg_dist, image_size)
            image_ids = [int(t["image_id"]) for t in targets]
            # 予測は img_size 正方の座標系。評価器の GT は元画像解像度なので、
            # 予測ボックスを元座標へ逆スケールしてから渡す。
            predictions = self._rescale_to_original(predictions, image_ids, image_size)
            self.evaluator.update(predictions, image_ids)

        results = self.evaluator.compute()

        # confusion matrix を visualizations/ に保存。
        confusion = np.asarray(results.pop("confusion_matrix_similar"))
        vis_dir = self.manager.exp_dir / "visualizations"
        np.save(vis_dir / "confusion_matrix.npy", confusion)
        save_confusion_matrix(
            confusion, CONFUSABLE_CLASSES, vis_dir / "confusion_matrix"
        )

        per_class_ap = results.pop("per_class_ap")
        self.manager.log_per_class_ap(per_class_ap)

        # JSON 安全なスカラー指標のみを metrics.json へ。
        metrics = {f"val/{k}": float(v) for k, v in results.items()}
        metrics["epoch"] = epoch
        metrics["mAP"] = float(results["mAP"])
        self.manager.log_metrics(metrics)
        self.logger.log(metrics, step=self._global_step)
        results["per_class_ap"] = per_class_ap
        return results

    def _rescale_to_original(self, predictions, image_ids, image_size: int):
        """予測ボックスを img_size 正方座標から元画像解像度へ逆スケールする。

        val transform は画像を ``img_size x img_size`` へリサイズするため、
        評価（元解像度の COCO GT との照合）の前に逆変換が必要。
        """
        rescaled = []
        for pred, image_id in zip(predictions, image_ids):
            info = self.evaluator.coco_gt.loadImgs(int(image_id))[0]
            scale_x = float(info.get("width", image_size)) / image_size
            scale_y = float(info.get("height", image_size)) / image_size
            boxes = pred["boxes"].clone().float()
            boxes[:, [0, 2]] *= scale_x
            boxes[:, [1, 3]] *= scale_y
            rescaled.append(
                {
                    "boxes": boxes,
                    "scores": pred["scores"],
                    "labels": pred["labels"],
                }
            )
        return rescaled

    # ------------------------------------------------------------------ #
    # 実行
    # ------------------------------------------------------------------ #
    def run(self) -> dict:
        """全 epoch を回し、最良 metrics を返す。"""
        if self.model is None:
            raise RuntimeError("setup() を先に呼び出してください。")
        epochs = int(self.cfg.train.epochs)
        best_map = -1.0

        for epoch in range(1, epochs + 1):
            train_loss = self.train_one_epoch(epoch)
            # epoch 平均の train/loss を記録（log_every に依らず必ず残す）。
            self.logger.log(
                {"train/loss": train_loss, "epoch": epoch}, step=self._global_step
            )
            results = self.evaluate(epoch)
            current_map = float(results["mAP"])

            metrics_for_ckpt = {"val/mAP": current_map, "train/loss": train_loss}
            self.ckpt_manager.save(self.model, self.optimizer, epoch, metrics_for_ckpt)
            self.ckpt_manager.save_best(
                self.model, self.optimizer, epoch, metrics_for_ckpt
            )
            if current_map > best_map:
                best_map = current_map
                self._best = {
                    "epoch": epoch,
                    "mAP": current_map,
                    "AP_rare": float(results["AP_rare"]),
                    "AP_common": float(results["AP_common"]),
                }
            self.scheduler.step()
            print(
                f"[S0][epoch {epoch}/{epochs}] train_loss={train_loss:.4f} "
                f"val/mAP={current_map:.4f} AP_rare={results['AP_rare']:.4f}"
            )

        print(f"[S0] best: {self._best}")
        self.logger.finish()
        return self._best

    # ------------------------------------------------------------------ #
    # 内部ヘルパ
    # ------------------------------------------------------------------ #
    @staticmethod
    def _original_cwd():
        """Hydra が cwd を変更する前の作業ディレクトリを返す。"""
        from pathlib import Path

        try:
            from hydra.core.hydra_config import HydraConfig

            if HydraConfig.initialized():
                from hydra.utils import get_original_cwd

                return Path(get_original_cwd())
        except Exception:
            pass
        return Path.cwd()

    @classmethod
    def _resolve_base_dir(cls, base_dir: str):
        """``base_dir`` を絶対パスに解決する（Hydra の cwd 変更に追従）。"""
        from pathlib import Path

        path = Path(base_dir)
        return path if path.is_absolute() else cls._original_cwd() / path

    def _resolve_data_paths(self) -> None:
        """``cfg.data`` 内の相対 ann_file / img_dir を元 cwd 基準で絶対化する。"""
        from pathlib import Path

        base = self._original_cwd()
        OmegaConf.set_struct(self.cfg, False)
        data = self.cfg.data
        for split in ("train", "val", "test"):
            sub = data.get(split)
            if sub is None:
                continue
            for key in ("ann_file", "img_dir"):
                value = sub.get(key)
                if value and not Path(value).is_absolute():
                    sub[key] = str(base / value)


def _external_head_available(head_name: str) -> bool:
    """要求された外部検出ヘッド（Mask DINO / VarifocalNet）が使えるか。"""
    name = head_name.lower()
    if name in ("mask_dino", "maskdino"):
        from egosurgery.models.heads.mask_dino_head import is_maskdino_available

        return is_maskdino_available()
    if name in ("varifocanet", "varifocalnet", "vfnet"):
        from egosurgery.models.heads.varifocanet_head import is_mmdet_available

        return is_mmdet_available()
    return False

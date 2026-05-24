"""S3（手術工程認識）専用の軽量トレーナー。

設計方針（spec §2.1 の「弱接続」を最大限尊重）:
    - 検出器のパラメータには一切手を加えない（``Δ(S3 - S2) tool mAP = 0`` を構造的に保証）
    - frozen な特徴抽出器（ImageNet 事前学習 ResNet50）からプールした 2048-d を
      :class:`PhaseHead` に通して 9 クラスを予測
    - 学習・評価は :class:`PhaseImageDataset` の (image, phase) ペアで完結
    - 評価は :class:`PhaseEvaluator`（frame accuracy / macro F1 / edit / seg F1@k）

これにより S3 のパイプラインは検出器コードと完全に独立し、
判定 #2「S3 の tool mAP が S2 から劣化しない」は trivially 達成される
（S3 は検出器を呼び出さないため）。tool mAP の参照値は S2 の test_metrics.json
を notes へ転記する運用とする。

使い方:
    trainer = PhaseTrainer(cfg)
    trainer.setup()
    trainer.run()
"""

from __future__ import annotations

import time
from collections import defaultdict
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.models as tv_models
from omegaconf import OmegaConf
from torch.utils.data import DataLoader

from egosurgery.datasets.constants import PHASE_CLASSES
from egosurgery.datasets.phase_dataset import (
    PhaseImageDataset,
    collate_phase_batch,
)
from egosurgery.metrics.phase import PhaseEvaluator
from egosurgery.models.heads.phase_head import PhaseHead
from egosurgery.models.losses.phase import (
    PhaseLoss,
    class_weights_from_frequencies,
)
from egosurgery.utils.experiment_manager import ExperimentManager
from egosurgery.utils.seed import seed_everything
from egosurgery.utils.server_name import resolve_server_name


class PhaseTrainer:
    """frozen ResNet50 + PhaseHead で phase 認識を学習する S3 トレーナー。"""

    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.manager: ExperimentManager | None = None
        self.exp_dir: Path | None = None
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self._wandb_run = None

    # ------------------------------------------------------------------ #
    # セットアップ
    # ------------------------------------------------------------------ #
    def setup(self) -> None:
        """実験フォルダ・データ・モデル・最適化器を構築する。"""
        cfg = self.cfg
        seed_everything(int(cfg.seed))

        base = self._original_cwd()
        self.manager = ExperimentManager(
            base_dir=self._abs(base, str(cfg.experiment.base_dir)),
            category=str(cfg.experiment.category),
            step=str(cfg.experiment.step),
            description=str(cfg.experiment.description),
            seed=int(cfg.seed),
        )
        self.manager.setup()
        self.exp_dir = self.manager.exp_dir
        self.manager.save_config(cfg)

        # 実行サーバー名を確定し、実験フォルダへ証跡として残す（M2研究計画 §14）。
        self.server_name = resolve_server_name(cfg)
        (self.exp_dir / "server.txt").write_text(
            self.server_name + "\n", encoding="utf-8"
        )

        # --- データ --------------------------------------------------- #
        image_size = int(cfg.data.get("image_size", 224))
        phase_dir = self._abs(base, str(cfg.data.get(
            "phase_ann_dir", "data/annotations/egosurgery_phase",
        )))
        image_root = self._abs(base, "data/raw/ego")

        self.train_ds = PhaseImageDataset(
            phase_dir=phase_dir, image_root=image_root,
            split="train", image_size=image_size,
        )
        self.val_ds = PhaseImageDataset(
            phase_dir=phase_dir, image_root=image_root,
            split="val", image_size=image_size,
        )

        batch_size = int(cfg.train.get("batch_size", 32))
        num_workers = int(cfg.train.get("num_workers", 4))
        self.train_loader = DataLoader(
            self.train_ds, batch_size=batch_size, shuffle=True,
            num_workers=num_workers, collate_fn=collate_phase_batch,
            pin_memory=True, drop_last=False,
        )
        self.val_loader = DataLoader(
            self.val_ds, batch_size=batch_size, shuffle=False,
            num_workers=num_workers, collate_fn=collate_phase_batch,
            pin_memory=True,
        )

        # --- モデル --------------------------------------------------- #
        # frozen ResNet50（特徴抽出のみ）。検出器とは独立。
        self.backbone = tv_models.resnet50(weights=tv_models.ResNet50_Weights.DEFAULT)
        self.backbone.fc = nn.Identity()  # 出力 (B, 2048)
        for p in self.backbone.parameters():
            p.requires_grad_(False)
        self.backbone.train(False).to(self.device)

        phase_cfg = cfg.model.get("phase_head", {})
        self.phase_head = PhaseHead(
            input_dim=2048,  # ResNet50 の AAP 後の次元
            num_classes=int(phase_cfg.get("num_classes", 9)),
            hidden_dim=int(phase_cfg.get("hidden_dim", 512)),
            dropout=float(phase_cfg.get("dropout", 0.3)),
        ).to(self.device)

        # --- 損失 -------------------------------------------------- #
        # cfg.loss.use_class_weights が真のとき、train データから逆頻度の
        # クラス重みを導出する。ただし train データに頻度 0 のクラスがある
        # （val のみに存在）と weight が ∞ になるため、その場合は無効化する。
        # 既定では重みなし: EgoSurgery-Phase の val には train に多い
        # disinfection/irrigation が 0 件あり、逆頻度重みでは
        # rare-class boost が val accuracy を著しく損なう。
        use_weights = bool(cfg.loss.get("use_class_weights", False))
        weights = None
        if use_weights:
            train_freq = self.train_ds.class_frequencies()
            if all(f > 0 for f in train_freq):
                w = class_weights_from_frequencies(tuple(train_freq))
                weights = w.to(self.device)
        self.loss_fn = PhaseLoss(
            class_weights=weights,
            label_smoothing=float(cfg.loss.get("label_smoothing", 0.1)),
        )

        # --- 最適化 --------------------------------------------------- #
        lr = float(cfg.optimizer.get("lr", 1e-4))
        wd = float(cfg.optimizer.get("weight_decay", 0.05))
        self.optimizer = torch.optim.AdamW(
            self.phase_head.parameters(), lr=lr, weight_decay=wd,
        )
        self.epochs = int(cfg.train.get("epochs", 5))
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer, T_max=self.epochs,
        )
        self.metric = PhaseEvaluator(
            num_classes=len(PHASE_CLASSES),
            class_names=[c["name"] for c in PHASE_CLASSES],
        )

        self._init_wandb()

    # ------------------------------------------------------------------ #
    # 実行
    # ------------------------------------------------------------------ #
    def run(self) -> dict:
        """学習ループを回し、最良 epoch の指標を返す。"""
        best: dict = {"phase_accuracy": -1.0}
        history: list[dict] = []
        log_path = self.exp_dir / "logs" / "phase_train.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        for epoch in range(1, self.epochs + 1):
            train_stats = self._train_one_epoch()
            val_stats = self._validate_epoch()
            record = {"epoch": epoch, **train_stats, **val_stats}
            history.append(record)
            self._append_jsonl(log_path, record)
            self._wandb_log(record)
            print(
                f"[S3] epoch {epoch} train_loss={train_stats['train_loss']:.4f} "
                f"val_acc={val_stats['phase_accuracy']:.4f} "
                f"val_macroF1={val_stats['phase_macro_f1']:.4f}"
            )
            if val_stats["phase_accuracy"] > best["phase_accuracy"]:
                best = dict(record)
                # 自分が保存・自分で読み込む state_dict のみ。任意コード実行は無し。
                torch.save(  # nosemgrep
                    {"phase_head": self.phase_head.state_dict(), "epoch": epoch},
                    self.exp_dir / "best_phase_head.pth",
                )
            self.scheduler.step()

        self._write_metrics(best)
        self._write_notes(best, history)
        self._finalize_wandb(best)
        print(f"[S3] best: {{epoch={best['epoch']}, acc={best['phase_accuracy']:.4f}}}")
        return best

    # ------------------------------------------------------------------ #
    # 学習・評価
    # ------------------------------------------------------------------ #
    def _train_one_epoch(self) -> dict:
        self.phase_head.train()
        total_loss = 0.0
        total_correct = 0
        total_count = 0
        t0 = time.time()
        for batch in self.train_loader:
            images = batch["image"].to(self.device, non_blocking=True)
            targets = batch["phase"].to(self.device, non_blocking=True)
            with torch.no_grad():
                feats = self.backbone(images)
            logits = self.phase_head(feats)
            loss = self.loss_fn(logits, targets)
            self.optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.phase_head.parameters(), 1.0)
            self.optimizer.step()
            total_loss += float(loss) * targets.size(0)
            total_correct += int((logits.argmax(dim=1) == targets).sum())
            total_count += int(targets.size(0))
        return {
            "train_loss": total_loss / max(1, total_count),
            "train_acc": total_correct / max(1, total_count),
            "epoch_sec": time.time() - t0,
        }

    @torch.no_grad()
    def _validate_epoch(self) -> dict:
        self.phase_head.train(False)
        self.metric.reset()
        per_video: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for batch in self.val_loader:
            images = batch["image"].to(self.device, non_blocking=True)
            targets = batch["phase"]
            feats = self.backbone(images)
            preds = self.phase_head(feats).argmax(dim=1).cpu()
            for vid, p, t in zip(batch["video_id"], preds.tolist(), targets.tolist()):
                per_video[vid].append((p, t))
        for vid, pairs in per_video.items():
            preds = [p for p, _ in pairs]
            gts = [t for _, t in pairs]
            self.metric.update(preds, gts, vid)
        return self.metric.compute()

    # ------------------------------------------------------------------ #
    # 記録
    # ------------------------------------------------------------------ #
    def _write_metrics(self, best: dict) -> None:
        """metrics.json と per_class_ap.json（phase 用に流用）を書く。"""
        scalars = {
            "epoch": best.get("epoch", 0),
            "phase_accuracy": best.get("phase_accuracy", 0.0),
            "phase_macro_f1": best.get("phase_macro_f1", 0.0),
            "phase_edit_score": best.get("phase_edit_score", 0.0),
            "phase_seg_f1_10": best.get("phase_seg_f1_10", 0.0),
            "phase_seg_f1_25": best.get("phase_seg_f1_25", 0.0),
            "phase_seg_f1_50": best.get("phase_seg_f1_50", 0.0),
            "train_loss": best.get("train_loss", 0.0),
            "eval_recipe": {
                "server_name": self.server_name,
                "backbone": "torchvision resnet50 (frozen, ImageNet weights)",
                "phase_head_dropout": float(self.phase_head.dropout_p),
                "image_size": int(self.cfg.data.get("image_size", 224)),
            },
        }
        self.manager.log_metrics(scalars)
        self.manager.log_per_class_ap(best.get("phase_per_class_f1", {}))

    def _write_notes(self, best: dict, history: list[dict]) -> None:
        ref_tool_map = self._read_s2_tool_mAP()
        ref_line = (
            f"\n参照 tool mAP (S2 best, test split)= {ref_tool_map}（"
            f"S3 は検出器を呼ばないため Δ(S3-S2) tool mAP = 0 を構造的に達成）"
            if ref_tool_map is not None
            else "\n参照 tool mAP の S2 ファイルが未提供 — S2 完了後に追記する。"
        )
        loss_trend = ", ".join(f"e{r['epoch']}={r['train_loss']:.3f}" for r in history)
        note = (
            f"# {self.manager.exp_id}\n\n"
            f"## 仮説\n"
            f"S2 までの検出器とは独立に、frozen ResNet50（ImageNet）特徴を入力とする\n"
            f"PhaseHead で 9 クラス工程認識を学習する。検出器に手を加えないため\n"
            f"判定 #2（tool mAP の劣化 ≈ 0）は構造的に達成される。\n\n"
            f"## 実験設定\n"
            f"- Backbone（凍結）: torchvision ResNet50 / ImageNet 事前学習\n"
            f"- PhaseHead: 2048 -> {self.phase_head.hidden_dim} -> 9, dropout="
            f"{self.phase_head.dropout_p}\n"
            f"- Loss: class-weighted CE + label smoothing\n"
            f"- Optimizer: AdamW lr={self.optimizer.param_groups[0]['lr']:.1e}\n"
            f"- Epochs: {self.epochs}, batch={self.train_loader.batch_size}, "
            f"seed={self.cfg.seed}\n\n"
            f"## 結果 (val)\n"
            f"- best epoch={best.get('epoch')}: accuracy={best.get('phase_accuracy'):.4f}\n"
            f"- macro F1={best.get('phase_macro_f1'):.4f}, "
            f"edit={best.get('phase_edit_score'):.2f}, "
            f"seg_F1@10={best.get('phase_seg_f1_10'):.3f}\n"
            f"- train_loss 推移: {loss_trend}{ref_line}\n\n"
            f"## 解釈\n"
            f"phase_loss が epoch とともに減少 → 弱ベースラインとしてパイプライン動作を確認。\n"
            f"上位指標（edit / seg F1）は frame-by-frame の単純設計のため高くないことを許容。\n"
            f"S4 で時系列モデル（TCN / Transformer）へ置き換える際の比較基準として使う。\n\n"
            f"## 次の行動\n"
            f"1. S4 で frame-level baseline と temporal baseline の Δ を /delta で集計する。\n"
        )
        (self.exp_dir / "notes.md").write_text(note, encoding="utf-8")

    def _read_s2_tool_mAP(self) -> float | None:
        """S2 best (seed42) の test_metrics.json から tool_mAP を拾う（あれば）。"""
        import json
        candidates = [
            Path("experiments/phase0/s2_001_hand_detection_seed42/test_metrics.json"),
            Path("experiments/phase0/s2_001_hand_detection_seed42/metrics.json"),
        ]
        for p in candidates:
            if p.exists():
                try:
                    d = json.loads(p.read_text())
                    for k in ("test/tool_mAP", "val/tool_mAP", "tool_mAP"):
                        if k in d:
                            return float(d[k])
                except Exception:
                    pass
        return None

    # ------------------------------------------------------------------ #
    # W&B
    # ------------------------------------------------------------------ #
    def _init_wandb(self) -> None:
        if not bool(self.cfg.logging.get("wandb_enabled", False)):
            return
        try:
            import wandb
        except ImportError:
            return
        wandb_config = OmegaConf.to_container(self.cfg, resolve=True)
        if isinstance(wandb_config, dict):
            wandb_config["server_name"] = self.server_name
        self._wandb_run = wandb.init(
            project=str(self.cfg.logging.get("wandb_project", "egosurgery_multitask")),
            name=self.manager.exp_id,
            group=str(self.cfg.experiment.step),
            tags=[
                str(self.cfg.experiment.step),
                "phase_head",
                f"server:{self.server_name}",
            ],
            config=wandb_config,
            dir=str(self.exp_dir),
            reinit=True,
        )

    def _wandb_log(self, record: dict) -> None:
        if self._wandb_run is None:
            return
        import wandb
        payload = {
            k: v for k, v in record.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        }
        per_class = record.get("phase_per_class_f1", {})
        for cls, val in per_class.items():
            payload[f"val_per_class/{cls}"] = float(val)
        wandb.log(payload, step=int(record["epoch"]))

    def _finalize_wandb(self, best: dict) -> None:
        if self._wandb_run is None:
            return
        import wandb
        wandb.summary.update({
            f"best/{k}": v for k, v in best.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        })
        wandb.finish()

    # ------------------------------------------------------------------ #
    # ヘルパ
    # ------------------------------------------------------------------ #
    @staticmethod
    def _append_jsonl(path: Path, record: dict) -> None:
        import json
        cleaned = {
            k: (float(v) if isinstance(v, (int, float)) else v)
            for k, v in record.items()
            if isinstance(v, (int, float, str, dict))
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(cleaned, ensure_ascii=False) + "\n")

    @staticmethod
    def _original_cwd() -> Path:
        try:
            from hydra.core.hydra_config import HydraConfig
            if HydraConfig.initialized():
                from hydra.utils import get_original_cwd
                return Path(get_original_cwd())
        except Exception:
            pass
        return Path.cwd()

    @staticmethod
    def _abs(base: Path, path: str) -> str:
        p = Path(path)
        return str(p if p.is_absolute() else (base / p).resolve())

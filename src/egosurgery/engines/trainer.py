"""汎用トレーナー（フェーズ I 骨格版）。

実際の Mask DINO / DINOv2 / TeCNO 等のモデルはまだ実装せず、
**ダミーモデル（``nn.Linear``）とダミーデータ（ランダムテンソル）** で
学習・評価パイプラインの骨格を 1 周通すためのトレーナー。

このクラスが担うのは「実験管理 → ロギング → チェックポイント →
学習ループ → 評価 → 証拠ファイル保存」という配線そのものであり、
モデル本体が差し替わっても配線が再利用できることを目的とする。

使い方:
    trainer = Trainer(cfg)
    trainer.setup()      # 実験フォルダ・モデル・データ・optimizer の構築
    trainer.train()      # 学習ループの実行（各 epoch 末に評価）
    trainer.evaluate()   # 評価ループ単体の実行
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from torch import nn
from torch.utils.data import DataLoader, Dataset

from egosurgery.metrics.delta import DeltaCalculator
from egosurgery.utils.checkpoint import CheckpointManager
from egosurgery.utils.experiment_manager import ExperimentManager
from egosurgery.utils.logging import ExperimentLogger
from egosurgery.utils.seed import seed_everything

# EgoSurgery-Tool の術具 15 クラス。ダミー per-class AP の生成に使う。
TOOL_CLASSES = [
    "Tweezers", "Needle_Holders", "Scissors", "Forceps",
    "Bipolar_Forceps", "Retractors", "Clip_Applier", "Suction",
    "Scalpel", "Electrocautery", "Gauze", "Needle", "Thread",
    "Skewer", "Syringe",
]

# ダミー confusion matrix の対象（形状が似て混同しやすい 4 クラス）。
CONFUSABLE_CLASSES = ["Forceps", "Tweezers", "Needle_Holders", "Bipolar_Forceps"]

# ダミーデータセットのサンプル数。
_NUM_TRAIN_SAMPLES = 64
_NUM_VAL_SAMPLES = 32


class _DummyClassificationDataset(Dataset):
    """ランダムな特徴ベクトルとラベルを返すダミーデータセット。

    実データセット（``datasets/`` 配下）が実装されるまでの仮置き。
    パイプラインの配線確認のみが目的なので学習可能性は問わない。
    """

    def __init__(
        self,
        num_samples: int,
        input_dim: int,
        num_classes: int,
        seed: int = 0,
    ) -> None:
        generator = torch.Generator().manual_seed(int(seed))
        self.features = torch.randn(num_samples, input_dim, generator=generator)
        self.labels = torch.randint(
            0, num_classes, (num_samples,), generator=generator
        )

    def __len__(self) -> int:
        return self.features.shape[0]

    def __getitem__(self, index: int):
        return self.features[index], self.labels[index]


class Trainer:
    """ダミーモデルで 1 周回す汎用トレーナー。"""

    def __init__(self, cfg: DictConfig) -> None:
        """
        Args:
            cfg: Hydra/OmegaConf の resolved config。
        """
        self.cfg = cfg
        # ダミーデータ・ダミーモデルは軽量なので CPU で十分（GPU 競合を避ける）。
        self.device = torch.device("cpu")

        self.manager: ExperimentManager | None = None
        self.logger: ExperimentLogger | None = None
        self.ckpt_manager: CheckpointManager | None = None
        self.model: nn.Module | None = None
        self.optimizer: torch.optim.Optimizer | None = None
        self.scheduler = None
        self.criterion: nn.Module | None = None
        self.train_loader: DataLoader | None = None
        self.val_loader: DataLoader | None = None
        self._global_step = 0

    # ------------------------------------------------------------------ #
    # セットアップ
    # ------------------------------------------------------------------ #
    def setup(self) -> Path:
        """実験フォルダ・ロガー・モデル・データ・optimizer を構築する。

        Returns:
            生成された実験フォルダの :class:`~pathlib.Path`。
        """
        cfg = self.cfg
        seed_everything(int(cfg.seed))

        # --- 実験フォルダの自動生成 ----------------------------------- #
        base_dir = self._resolve_base_dir(cfg.experiment.base_dir)
        self.manager = ExperimentManager(
            base_dir=base_dir,
            category=str(cfg.experiment.category),
            step=str(cfg.experiment.step),
            description=str(cfg.experiment.description),
            seed=int(cfg.seed),
        )
        exp_dir = self.manager.setup()
        # Hydra の resolved config を config.yaml として保存。
        self.manager.save_config(cfg)

        # --- ロガー（W&B + ローカル） --------------------------------- #
        self.logger = ExperimentLogger(
            experiment_manager=self.manager,
            wandb_project=str(cfg.logging.wandb_project),
            wandb_entity=cfg.logging.get("wandb_entity", None),
            tags=[str(cfg.experiment.step), str(cfg.experiment.category)],
            enabled=bool(cfg.logging.get("wandb_enabled", False)),
            config=OmegaConf.to_container(cfg, resolve=True),
            run_name=self.manager.exp_id,
        )
        self.logger.init()

        # --- チェックポイント ----------------------------------------- #
        self.ckpt_manager = CheckpointManager(
            exp_dir=exp_dir,
            save_top_k=int(cfg.logging.get("save_top_k", 3)),
            monitor="val/mAP",
            mode="max",
        )

        # --- ダミーモデル / ダミーデータ ------------------------------ #
        num_classes = int(cfg.model.num_classes)
        input_dim = int(cfg.model.input_dim)
        self.model = nn.Linear(input_dim, num_classes).to(self.device)
        self.criterion = nn.CrossEntropyLoss()

        batch_size = int(cfg.train.batch_size)
        train_ds = _DummyClassificationDataset(
            _NUM_TRAIN_SAMPLES, input_dim, num_classes, seed=int(cfg.seed)
        )
        val_ds = _DummyClassificationDataset(
            _NUM_VAL_SAMPLES, input_dim, num_classes, seed=int(cfg.seed) + 1
        )
        # ダミーデータはメモリ常駐の極小サイズなので num_workers=0 が最速。
        self.train_loader = DataLoader(  # nosemgrep
            train_ds, batch_size=batch_size, shuffle=True, num_workers=0
        )
        self.val_loader = DataLoader(  # nosemgrep
            val_ds, batch_size=batch_size, shuffle=False, num_workers=0
        )

        # --- optimizer / scheduler ------------------------------------ #
        self.optimizer = self._build_optimizer()
        self.scheduler = self._build_scheduler()
        return exp_dir

    # ------------------------------------------------------------------ #
    # 学習
    # ------------------------------------------------------------------ #
    def train(self) -> dict:
        """学習ループを実行し、最終指標を ``metrics.json`` に保存する。

        Returns:
            最終 epoch の指標辞書。
        """
        self._require_setup()
        cfg = self.cfg
        epochs = int(cfg.train.epochs)
        log_every = max(int(cfg.logging.get("log_every_n_steps", 50)), 1)

        final_metrics: dict = {}
        for epoch in range(1, epochs + 1):
            self.model.train()
            running_loss, num_batches = 0.0, 0

            for features, labels in self.train_loader:
                features = features.to(self.device)
                labels = labels.to(self.device)

                self.optimizer.zero_grad()
                logits = self.model(features)
                loss = self.criterion(logits, labels)
                loss.backward()
                self.optimizer.step()

                self._global_step += 1
                running_loss += loss.item()
                num_batches += 1

                if self._global_step % log_every == 0:
                    self.logger.log(
                        {"train/loss": loss.item(), "epoch": epoch},
                        step=self._global_step,
                    )

            if self.scheduler is not None:
                self.scheduler.step()

            train_loss = running_loss / max(num_batches, 1)
            eval_metrics = self.evaluate()

            # epoch サマリを W&B + ローカルへ記録。
            self.logger.log(
                {"train/loss": train_loss, "epoch": epoch, **eval_metrics},
                step=self._global_step,
            )

            # チェックポイント保存（top-k 整理 + best 更新）。
            self.ckpt_manager.save(self.model, self.optimizer, epoch, eval_metrics)
            self.ckpt_manager.save_best(self.model, self.optimizer, epoch, eval_metrics)

            final_metrics = {"epoch": epoch, "train/loss": train_loss, **eval_metrics}

        # 最終指標を metrics.json に保存し、W&B run を閉じる。
        final_metrics = self._attach_delta_placeholder(final_metrics)
        self.logger.log_metrics(final_metrics)
        self.logger.finish()
        return final_metrics

    def run(self) -> dict:
        """学習を実行する（エントリーポイント共通の :meth:`run` 別名）。"""
        return self.train()

    # ------------------------------------------------------------------ #
    # 評価
    # ------------------------------------------------------------------ #
    def evaluate(self) -> dict:
        """評価ループを実行し、指標・per-class AP・confusion matrix を生成する。

        Returns:
            評価指標の辞書（``val/loss`` / ``val/accuracy`` / ``mAP`` 等）。
        """
        self._require_setup()
        # 推論モードへ切替（BN/Dropout を評価用に固定）。.eval() と等価。
        self.model.train(False)

        total_loss, correct, total, num_batches = 0.0, 0, 0, 0
        with torch.no_grad():
            for features, labels in self.val_loader:
                features = features.to(self.device)
                labels = labels.to(self.device)

                logits = self.model(features)
                total_loss += self.criterion(logits, labels).item()
                num_batches += 1

                predictions = logits.argmax(dim=1)
                correct += int((predictions == labels).sum().item())
                total += int(labels.numel())

        val_loss = total_loss / max(num_batches, 1)
        accuracy = correct / max(total, 1)

        # --- ダミー per-class AP（15 クラス） -------------------------- #
        rng = np.random.default_rng(int(self.cfg.seed))
        per_class_ap = {
            cls: round(float(rng.uniform(0.05, 0.85)), 4) for cls in TOOL_CLASSES
        }
        self.manager.log_per_class_ap(per_class_ap)

        # --- ダミー confusion matrix（混同しやすい 4 クラス） ---------- #
        confusion = rng.integers(0, 40, size=(4, 4)).astype(np.int64)
        np.fill_diagonal(confusion, rng.integers(80, 200, size=4))
        np.save(
            self.manager.exp_dir / "visualizations" / "confusion_matrix.npy",
            confusion,
        )

        # --- 集約指標 -------------------------------------------------- #
        ap_values = list(per_class_ap.values())
        mean_ap = float(np.mean(ap_values))
        # 末尾 4 クラスを希少クラス、先頭 4 クラスを高頻度クラスの代理とする。
        rare_ap = float(np.mean([per_class_ap[c] for c in TOOL_CLASSES[-4:]]))
        common_ap = float(np.mean([per_class_ap[c] for c in TOOL_CLASSES[:4]]))

        return {
            "val/loss": round(val_loss, 6),
            "val/accuracy": round(accuracy, 6),
            "val/mAP": round(mean_ap, 6),
            "mAP": round(mean_ap, 6),
            "AP_rare": round(rare_ap, 6),
            "AP_common": round(common_ap, 6),
        }

    # ------------------------------------------------------------------ #
    # 内部ヘルパ
    # ------------------------------------------------------------------ #
    def _require_setup(self) -> None:
        """``setup()`` 済みであることを保証する。"""
        if self.manager is None or self.model is None:
            raise RuntimeError("setup() を先に呼び出してください。")

    @staticmethod
    def _resolve_base_dir(base_dir: str) -> Path:
        """``base_dir`` を絶対パスに解決する。

        Hydra（``version_base=None``）は実行時に作業ディレクトリを
        変更しうるため、相対パスは「Hydra が cwd を変更する前の
        元のディレクトリ」を基準に解決する。これにより ``experiments/``
        が ``outputs/.../`` へ紛れ込むのを防ぐ。
        """
        path = Path(base_dir)
        if path.is_absolute():
            return path
        try:
            from hydra.core.hydra_config import HydraConfig

            if HydraConfig.initialized():
                from hydra.utils import get_original_cwd

                return Path(get_original_cwd()) / path
        except Exception:
            pass
        return path.resolve()

    def _build_optimizer(self) -> torch.optim.Optimizer:
        """config に従って optimizer を構築する。"""
        opt_cfg = self.cfg.optimizer
        name = str(opt_cfg.name).lower()
        lr = float(opt_cfg.lr)
        weight_decay = float(opt_cfg.get("weight_decay", 0.0))
        params = self.model.parameters()

        if name == "adamw":
            return torch.optim.AdamW(params, lr=lr, weight_decay=weight_decay)
        if name == "adam":
            return torch.optim.Adam(params, lr=lr, weight_decay=weight_decay)
        if name == "sgd":
            return torch.optim.SGD(
                params, lr=lr, weight_decay=weight_decay, momentum=0.9
            )
        raise ValueError(f"未対応の optimizer です: {name!r}")

    def _build_scheduler(self):
        """config に従って LR scheduler を構築する（無指定なら ``None``）。"""
        sched_cfg = self.cfg.get("scheduler", None)
        if sched_cfg is None:
            return None
        name = str(sched_cfg.get("name", "none")).lower()
        epochs = max(int(self.cfg.train.epochs), 1)

        if name == "cosine":
            return torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer, T_max=epochs
            )
        if name == "step":
            return torch.optim.lr_scheduler.StepLR(
                self.optimizer, step_size=max(epochs // 3, 1), gamma=0.1
            )
        # "none" / "constant" / 未対応名 -> scheduler なし。
        return None

    def _attach_delta_placeholder(self, metrics: dict) -> dict:
        """基準点が存在すれば mAP の Δ を、無ければ Δ 計算枠を付与する。

        フェーズ I では基準点が未整備でも落ちないよう、Δ 計算の
        「枠」（``delta_*`` キー）を常に metrics へ残す。基準点
        フォルダが揃った段階で実値が入る。
        """
        result = dict(metrics)
        baselines_dir = self._resolve_base_dir(self.cfg.experiment.base_dir) / "baselines"
        calculator = DeltaCalculator(baselines_dir)
        try:
            delta = calculator.compute_delta(
                baseline_step=str(self.cfg.experiment.step),
                experiment_metrics=metrics,
                metric="mAP",
            )
            result["delta_mAP"] = delta["delta"]
            result["delta_mAP_significant"] = delta["significant"]
        except (ValueError, KeyError):
            # 基準点未整備 -> Δ 計算枠のみ用意（値は null）。
            result["delta_mAP"] = None
            result["delta_mAP_significant"] = None
        return result

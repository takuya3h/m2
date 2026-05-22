"""チェックポイント管理ユーティリティ。

学習中の重みを ``{exp_dir}/checkpoints/`` 配下へ保存・整理する。
``monitor`` 指標で上位 ``save_top_k`` 個のみを保持し、それを超えた
古い（劣る）チェックポイントは自動削除する。``best.pth`` は
``monitor`` が更新されたときのみ書き換える。

使い方:
    ckpt_manager = CheckpointManager(
        exp_dir=manager.exp_dir,
        save_top_k=3,
        monitor="val/mAP",
        mode="max",
    )
    ckpt_manager.save(model, optimizer, epoch, metrics)
    ckpt_manager.save_best(model, optimizer, epoch, metrics)
    model, optimizer, start_epoch = ckpt_manager.load_best(model, optimizer)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch


class CheckpointManager:
    """top-k 保持と best 管理を行うチェックポイントマネージャ。"""

    def __init__(
        self,
        exp_dir: str | Path,
        save_top_k: int = 3,
        monitor: str = "val/mAP",
        mode: str = "max",
    ) -> None:
        """
        Args:
            exp_dir: 実験フォルダ。``checkpoints/`` をこの直下に作る。
            save_top_k: 保持する epoch チェックポイント数の上限。
            monitor: top-k / best 判定に使う指標名。
            mode: ``"max"``（大きいほど良い）/ ``"min"``（小さいほど良い）。

        Raises:
            ValueError: ``mode`` が ``"max"`` / ``"min"`` 以外の場合。
        """
        if mode not in ("max", "min"):
            raise ValueError(f"mode は 'max' / 'min' のいずれか（指定値: {mode!r}）")

        self.exp_dir = Path(exp_dir)
        self.ckpt_dir = self.exp_dir / "checkpoints"
        self.ckpt_dir.mkdir(parents=True, exist_ok=True)
        self.save_top_k = int(save_top_k)
        self.monitor = monitor
        self.mode = mode

        self._best_score: float | None = None
        # 保存済み epoch チェックポイントの台帳: {"epoch", "score", "path"}
        self._saved: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # 保存
    # ------------------------------------------------------------------ #
    def save(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer | None,
        epoch: int,
        metrics: dict | None = None,
    ) -> Path:
        """epoch チェックポイントを保存し、top-k を超えた分を削除する。

        Args:
            model: 保存対象モデル。
            optimizer: 保存対象 optimizer（``None`` 可）。
            epoch: epoch 番号。
            metrics: 当該 epoch の指標。``monitor`` 値の抽出に使う。

        Returns:
            保存したチェックポイントの :class:`~pathlib.Path`。
        """
        path = self.ckpt_dir / f"epoch_{epoch:04d}.pth"
        torch.save(self._state(model, optimizer, epoch, metrics), path)

        self._saved.append(
            {"epoch": int(epoch), "score": self._score(metrics), "path": path}
        )
        self._prune()
        return path

    def save_best(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer | None,
        epoch: int,
        metrics: dict | None = None,
    ) -> Path | None:
        """``monitor`` 指標が更新された場合のみ ``best.pth`` を書き換える。

        Args:
            model: 保存対象モデル。
            optimizer: 保存対象 optimizer（``None`` 可）。
            epoch: epoch 番号。
            metrics: 当該 epoch の指標。

        Returns:
            更新した場合は ``best.pth`` の :class:`~pathlib.Path`、
            それ以外は ``None``。
        """
        path = self.ckpt_dir / "best.pth"
        score = self._score(metrics)

        # monitor 指標が無い場合: best.pth が未作成のときだけ初期保存する。
        if score is None:
            if not path.exists():
                torch.save(self._state(model, optimizer, epoch, metrics), path)
                return path
            return None

        if self._is_better(score, self._best_score):
            self._best_score = score
            torch.save(self._state(model, optimizer, epoch, metrics), path)
            return path
        return None

    # ------------------------------------------------------------------ #
    # 読み込み
    # ------------------------------------------------------------------ #
    def load_best(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer | None = None,
    ) -> tuple[torch.nn.Module, torch.optim.Optimizer | None, int]:
        """``best.pth`` を読み込む。

        Returns:
            ``(model, optimizer, epoch)``。

        Raises:
            FileNotFoundError: ``best.pth`` が存在しない場合。
        """
        path = self.ckpt_dir / "best.pth"
        if not path.exists():
            raise FileNotFoundError(f"best.pth が見つかりません: {path}")
        return self._load(path, model, optimizer)

    def load_latest(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer | None = None,
    ) -> tuple[torch.nn.Module, torch.optim.Optimizer | None, int]:
        """最新の ``epoch_*.pth`` を読み込む。

        Returns:
            ``(model, optimizer, epoch)``。

        Raises:
            FileNotFoundError: epoch チェックポイントが 1 つも無い場合。
        """
        ckpts = sorted(self.ckpt_dir.glob("epoch_*.pth"))
        if not ckpts:
            raise FileNotFoundError(f"epoch チェックポイントがありません: {self.ckpt_dir}")
        return self._load(ckpts[-1], model, optimizer)

    # ------------------------------------------------------------------ #
    # 内部ヘルパ
    # ------------------------------------------------------------------ #
    @staticmethod
    def _state(
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer | None,
        epoch: int,
        metrics: dict | None,
    ) -> dict:
        """チェックポイントとして保存する辞書を組み立てる。"""
        return {
            "epoch": int(epoch),
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict() if optimizer is not None else None,
            "metrics": dict(metrics) if metrics else {},
        }

    @staticmethod
    def _load(
        path: Path,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer | None,
    ) -> tuple[torch.nn.Module, torch.optim.Optimizer | None, int]:
        """チェックポイントを model / optimizer に復元する。"""
        ckpt = torch.load(path, map_location="cpu")
        model.load_state_dict(ckpt["model"])
        if optimizer is not None and ckpt.get("optimizer") is not None:
            optimizer.load_state_dict(ckpt["optimizer"])
        return model, optimizer, int(ckpt.get("epoch", 0))

    def _score(self, metrics: dict | None) -> float | None:
        """metrics 辞書から ``monitor`` の数値を取り出す（無ければ ``None``）。"""
        if not metrics:
            return None
        value = metrics.get(self.monitor)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    def _is_better(self, candidate: float, current: float | None) -> bool:
        """``candidate`` が ``current`` より良ければ ``True``。"""
        if current is None:
            return True
        return candidate > current if self.mode == "max" else candidate < current

    def _prune(self) -> None:
        """top-k を超えた epoch チェックポイントを削除する。

        全 epoch に ``monitor`` 値があればその指標で上位 k 個を保持し、
        欠損があれば epoch の新しい順で k 個を保持する。
        """
        if len(self._saved) <= self.save_top_k:
            return

        has_all_scores = all(s["score"] is not None for s in self._saved)
        if has_all_scores:
            ordered = sorted(
                self._saved,
                key=lambda s: s["score"],
                reverse=(self.mode == "max"),
            )
        else:
            ordered = sorted(self._saved, key=lambda s: s["epoch"], reverse=True)

        keep = ordered[: self.save_top_k]
        drop = ordered[self.save_top_k :]
        keep_paths = {s["path"] for s in keep}

        for s in drop:
            ckpt_path: Path = s["path"]
            if ckpt_path.exists():
                ckpt_path.unlink()

        self._saved = [s for s in self._saved if s["path"] in keep_paths]

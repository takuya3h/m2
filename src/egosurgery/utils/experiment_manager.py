"""ExperimentManager: 実験フォルダの自動生成・管理。

実験を開始するたびに、正しい構造の実験フォルダを自動生成するモジュール。
``experiments/`` 配下に個別の実験フォルダを手作業で置かず、本クラスが
連番採番・証拠ファイル生成を一手に引き受けることで、命名ゆれと
証拠ファイルの作り忘れを人手から排除する。

使い方:
    manager = ExperimentManager(
        base_dir="experiments",
        category="baselines",     # baselines / phase0 / phase1 / ablations / transfer / final
        step="s0",                # s0 / s1 / s2 / ... / s9 / a1 / a2 / ...
        description="maskdino_bbox",
        seed=42,
    )
    exp_dir = manager.setup()
    # -> experiments/baselines/s0_001_maskdino_bbox_seed42/ が作成される

    manager.save_config(cfg)              # Hydra の resolved config を保存
    manager.log_metrics({"mAP": 0.42})    # metrics.json を更新
    manager.log_per_class_ap({...})       # per_class_ap.json を更新

自動で作成されるファイル・フォルダ:
    {exp_dir}/
    |-- config.yaml          # Hydra の resolved config のコピー（save_config で保存）
    |-- command.sh           # 実行コマンドの記録（sys.argv から自動生成）
    |-- git_commit.txt       # git rev-parse HEAD の結果
    |-- metrics.json         # 空の {} で初期化、学習中に更新
    |-- per_class_ap.json    # 空の {} で初期化、評価時に更新
    |-- notes.md             # テンプレート付きで初期化（仮説/結果/解釈/次）
    |-- logs/                # 空ディレクトリ
    |-- checkpoints/         # 空ディレクトリ
    |-- predictions/         # 空ディレクトリ
    `-- visualizations/      # 空ディレクトリ
"""

from __future__ import annotations

import json
import shlex
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from egosurgery.utils.experiment_id import generate_experiment_id
from egosurgery.utils.git_utils import save_git_commit
from egosurgery.utils.server_name import resolve_server_name

if TYPE_CHECKING:  # 型注釈専用。実行時は import しない。
    from omegaconf import DictConfig

# experiments/ 配下で許可されるカテゴリ。
VALID_CATEGORIES = ("baselines", "phase0", "phase1", "ablations", "transfer", "final")

# setup() で作成する空サブディレクトリ。
_SUBDIRS = ("logs", "checkpoints", "predictions", "visualizations")

_NOTES_TEMPLATE = """\
# {exp_id}

作成日時: {timestamp}

## 仮説
（ここに記入）

## 実験設定
- Category: {category}
- Step: {step}
- Seed: {seed}
- Config: （config.yaml を参照）

## 結果
（実験完了後に記入）

## 解釈
（結果の意味、期待との差、原因の仮説）

## 次の行動
1.
"""


class ExperimentManager:
    """実験フォルダの自動生成と証拠ファイル管理を担うクラス。"""

    def __init__(
        self,
        base_dir: str | Path,
        category: str,
        step: str,
        description: str,
        seed: int = 42,
    ) -> None:
        """
        Args:
            base_dir: 実験ルート（通常 ``"experiments"``）。
            category: ``baselines`` / ``phase0`` / ``phase1`` / ``ablations``
                / ``transfer`` / ``final`` のいずれか。
            step: ステップ識別子（``s0``..``s9`` / ``a1``.. など）。
            description: 実験内容の短い説明（例: ``maskdino_bbox``）。
            seed: 乱数シード。既定 42。

        Raises:
            ValueError: ``category`` が許可リストにない場合。
        """
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"category は {VALID_CATEGORIES} のいずれかである必要があります"
                f"（指定値: {category!r}）"
            )
        self.base_dir = Path(base_dir)
        self.category = category
        self.step = step
        self.description = description
        self.seed = int(seed)

        # exp_id / exp_dir は setup() 時に確定する。
        self.exp_id: str | None = None
        self.exp_dir: Path | None = None

    # ------------------------------------------------------------------ #
    # セットアップ
    # ------------------------------------------------------------------ #
    def setup(self, cfg: "DictConfig | dict | None" = None) -> Path:
        """実験フォルダを採番・生成し、証拠ファイルを初期化する。

        Args:
            cfg: 渡された場合は ``config.yaml`` として保存する。
                ``None`` の場合はプレースホルダの ``config.yaml`` を置く
                （後から :meth:`save_config` で上書き可能）。

        Returns:
            生成された実験フォルダの :class:`~pathlib.Path`。
        """
        category_dir = self.base_dir / self.category
        # 連番採番はディレクトリ作成の直前に行い、走査と作成を近接させる。
        self.exp_id = generate_experiment_id(
            category_dir, self.step, self.description, self.seed
        )
        self.exp_dir = category_dir / self.exp_id
        self.exp_dir.mkdir(parents=True, exist_ok=False)

        for sub in _SUBDIRS:
            (self.exp_dir / sub).mkdir(exist_ok=True)

        self._write_command_sh()
        save_git_commit(self.exp_dir / "git_commit.txt")
        self._init_json(self.exp_dir / "metrics.json")
        self._init_json(self.exp_dir / "per_class_ap.json")
        self._write_notes()
        # §14（実験結果ログ・実行マシン別）: どの物理サーバーで動いたかを
        # 実験フォルダに永続化する。
        server_name = resolve_server_name(cfg)
        (self.exp_dir / "server.txt").write_text(server_name + "\n", encoding="utf-8")

        if cfg is not None:
            self.save_config(cfg)
        else:
            (self.exp_dir / "config.yaml").write_text(
                "# resolved config はこの実験開始時に save_config() で保存される\n",
                encoding="utf-8",
            )
        return self.exp_dir

    # ------------------------------------------------------------------ #
    # 記録メソッド
    # ------------------------------------------------------------------ #
    def save_config(self, cfg: "DictConfig | dict") -> None:
        """OmegaConf の resolved config を ``config.yaml`` として保存する。

        Args:
            cfg: Hydra/OmegaConf の :class:`DictConfig` または素の dict。

        Notes:
            ``omegaconf`` はこのメソッド内で遅延 import する。これにより
            ``omegaconf`` 未導入環境でもモジュール import 自体は成功する。
        """
        path = self._require_exp_dir() / "config.yaml"
        from omegaconf import OmegaConf

        config = cfg if OmegaConf.is_config(cfg) else OmegaConf.create(cfg)
        # resolve=True で ${...} 補間を展開し、後から完全再現できる形で残す。
        OmegaConf.save(config=config, f=path, resolve=True)

    def log_metrics(self, metrics: dict) -> None:
        """``metrics.json`` を与えられた辞書で上書き保存する。

        既存ファイルに ``eval_recipe`` キーがあれば保持する（log_eval_recipe
        で書いた整合性情報を log_metrics の上書きで消さないため）。

        Args:
            metrics: 保存する metrics 辞書。
        """
        path = self._require_exp_dir() / "metrics.json"
        merged = dict(metrics)
        existing_recipe = self._read_existing_eval_recipe(path)
        if existing_recipe is not None and "eval_recipe" not in merged:
            merged["eval_recipe"] = existing_recipe
        self._dump_json(path, merged)

    def log_eval_recipe(self, eval_recipe: dict) -> None:
        """``metrics.json`` に ``eval_recipe`` キーを併記する。

        研究計画 §15.3 G3 / §15.4 B に対応。既存の指標値は保持したまま
        ``eval_recipe`` のみを書き込む（または更新する）。

        Args:
            eval_recipe: ``build_eval_recipe()`` の戻り値形式の dict。
                ``split_train_images``、``test_cfg``、``server_name`` 等を含む。
        """
        path = self._require_exp_dir() / "metrics.json"
        if path.exists():
            try:
                current = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                current = {}
        else:
            current = {}
        if not isinstance(current, dict):
            current = {}
        current["eval_recipe"] = dict(eval_recipe)
        self._dump_json(path, current)

    def log_per_class_ap(self, ap_dict: dict) -> None:
        """``per_class_ap.json`` を与えられた辞書で上書き保存する。

        Args:
            ap_dict: クラス別 AP 辞書。
        """
        self._dump_json(self._require_exp_dir() / "per_class_ap.json", ap_dict)

    # ------------------------------------------------------------------ #
    # 内部ヘルパ
    # ------------------------------------------------------------------ #
    def _require_exp_dir(self) -> Path:
        """``setup()`` 済みであることを保証して ``exp_dir`` を返す。"""
        if self.exp_dir is None:
            raise RuntimeError("setup() を先に呼び出してください。")
        return self.exp_dir

    def _write_command_sh(self) -> None:
        """``sys.argv`` から再実行可能なコマンドを ``command.sh`` に記録する。"""
        argv = " ".join(shlex.quote(arg) for arg in sys.argv)
        content = (
            "#!/usr/bin/env bash\n"
            "# 自動生成: この実験を起動したコマンドの記録\n"
            f"# 生成日時: {self._timestamp()}\n"
            f"python {argv}\n"
        )
        (self._require_exp_dir() / "command.sh").write_text(content, encoding="utf-8")

    def _write_notes(self) -> None:
        """``notes.md`` をテンプレートで初期化する。"""
        content = _NOTES_TEMPLATE.format(
            exp_id=self.exp_id,
            timestamp=self._timestamp(),
            category=self.category,
            step=self.step,
            seed=self.seed,
        )
        (self._require_exp_dir() / "notes.md").write_text(content, encoding="utf-8")

    @staticmethod
    def _read_existing_eval_recipe(path: Path) -> dict | None:
        """metrics.json から既存の ``eval_recipe`` を読む（壊れていれば None）。"""
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(data, dict):
            return None
        recipe = data.get("eval_recipe")
        return recipe if isinstance(recipe, dict) else None

    @staticmethod
    def _init_json(path: Path) -> None:
        """空の JSON オブジェクト ``{}`` でファイルを初期化する。"""
        ExperimentManager._dump_json(path, {})

    @staticmethod
    def _dump_json(path: Path, obj: dict) -> None:
        """辞書を整形 JSON としてファイルに上書き保存する。"""
        path.write_text(
            json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _timestamp() -> str:
        """ローカルタイムゾーン付き ISO 8601 タイムスタンプを返す。"""
        return datetime.now().astimezone().isoformat(timespec="seconds")

"""実行サーバー名（hostname-like）の単一情報源。

研究計画 §13.8（GPU 割り当て）および M2 研究計画 §14（実験結果ログ・
実行マシン別）の運用に従い、各実験がどの物理サーバーで動いたかを
W&B run・metrics.json・実験フォルダ内 ``server.txt`` に一貫して記録する。

解決優先順位（高い順）:
    1. 環境変数 ``SERVERNAME``（shell rc で ``export SERVERNAME=bengio`` 等）
    2. 環境変数 ``EGOSURGERY_SERVER_NAME``（後方互換のため残置）
    3. Hydra config ``logging.server_name``（YAML から渡せる。default.yaml では
       ``${oc.env:SERVERNAME,null}`` で 1. と等価）
    4. ``socket.gethostname()`` を小文字化したもの（最後の砦）

使い方:
    from egosurgery.utils.server_name import resolve_server_name
    name = resolve_server_name(cfg)   # 例: "bengio"
"""

from __future__ import annotations

import os
import socket


def resolve_server_name(cfg=None) -> str:
    """実行サーバー名を一貫した規則で解決する。

    Args:
        cfg: Hydra/OmegaConf の DictConfig（``logging.server_name`` を見る）。
            ``None`` でも環境変数 / hostname の経路は動く。

    Returns:
        小文字化された短いサーバー名（例: ``"bengio"``）。
    """
    # 主経路: shell rc から export された SERVERNAME を最優先。
    # 後方互換のため EGOSURGERY_SERVER_NAME も認める。
    env = os.environ.get("SERVERNAME") or os.environ.get("EGOSURGERY_SERVER_NAME")
    if env:
        return str(env).strip().lower()

    if cfg is not None:
        try:
            logging_cfg = cfg.get("logging", {}) if hasattr(cfg, "get") else {}
            value = (
                logging_cfg.get("server_name")
                if isinstance(logging_cfg, dict) or hasattr(logging_cfg, "get")
                else None
            )
            if value:
                return str(value).strip().lower()
        except Exception:
            pass

    return socket.gethostname().split(".")[0].lower()

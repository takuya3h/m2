#!/usr/bin/env python
"""方法 3（実行時）: 実際に触られた設定の鍵を記録する。

`DictConfig` の利用者向けの取り出し口だけを覆う。内部の `_get_node` は
覆わない。`OmegaConf.to_container` は内部経路を通るため、記録に載らない。
載らないことは確かめてから使う（--selftest）。

使い方:
    python trace_reads.py --out <json> -- <script.py> [args...]
    python trace_reads.py --selftest
"""

from __future__ import annotations

import argparse
import json
import os
import runpy
import sys
from pathlib import Path

from omegaconf import DictConfig, OmegaConf

ACCESSED: set[str] = set()
ACCESS_LOG: list[dict] = []


def _full_key(node: DictConfig, key) -> str | None:
    try:
        return str(node._get_full_key(key))
    except Exception:  # noqa: BLE001
        return None


def install() -> None:
    orig_getattr = DictConfig.__getattr__
    orig_getitem = DictConfig.__getitem__
    orig_get = DictConfig.get

    def rec(node, key, how) -> None:
        fk = _full_key(node, key)
        if fk:
            ACCESSED.add(fk)
            ACCESS_LOG.append({"key": fk, "how": how})

    def patched_getattr(self, key):  # noqa: ANN001
        if not str(key).startswith("_"):
            rec(self, key, "getattr")
        return orig_getattr(self, key)

    def patched_getitem(self, key):  # noqa: ANN001
        rec(self, key, "getitem")
        return orig_getitem(self, key)

    def patched_get(self, key, default_value=None):  # noqa: ANN001
        rec(self, key, "get")
        return orig_get(self, key, default_value)

    DictConfig.__getattr__ = patched_getattr  # type: ignore[assignment]
    DictConfig.__getitem__ = patched_getitem  # type: ignore[assignment]
    DictConfig.get = patched_get  # type: ignore[assignment]


def selftest() -> int:
    """記録器そのものが空振りでないことを確かめる（対照）。"""
    install()
    cfg = OmegaConf.create({"a": {"b": 1, "c": 2}, "z": 3, "untouched": {"deep": 9}})
    _ = cfg.a.b
    _ = cfg["z"]
    _ = cfg.a.get("c")
    seen_direct = set(ACCESSED)
    ACCESSED.clear()
    _ = OmegaConf.to_container(cfg, resolve=True)
    seen_container = set(ACCESSED)
    ok_direct = {"a", "a.b", "z", "a.c"} <= seen_direct
    ok_untouched = "untouched.deep" not in seen_direct
    print(f"direct accesses recorded : {sorted(seen_direct)}")
    print(f"to_container recorded    : {sorted(seen_container)}")
    print(f"records real accesses    : {ok_direct}")
    print(f"untouched key absent     : {ok_untouched}")
    print(f"to_container is silent   : {len(seen_container) == 0}")
    return 0 if (ok_direct and ok_untouched) else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=False)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    rest = args.rest
    if rest and rest[0] == "--":
        rest = rest[1:]
    if not rest:
        parser.error("target script required")

    install()
    script = str(Path(rest[0]).resolve())
    sys.argv = [script, *rest[1:]]
    status = 0
    err = None
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as exc:
        status = int(exc.code or 0)
    except Exception as exc:  # noqa: BLE001
        err = f"{type(exc).__name__}: {exc}"
        status = 1
        import traceback

        traceback.print_exc()

    payload = {
        "script": script,
        "argv": sys.argv,
        "exit": status,
        "error": err,
        "accessed": sorted(ACCESSED),
        "n_accessed": len(ACCESSED),
        "n_events": len(ACCESS_LOG),
        "wandb_api_key_present": bool(os.environ.get("WANDB_API_KEY", "").strip()),
    }
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(f"[trace] accessed keys: {len(ACCESSED)} (events {len(ACCESS_LOG)}) exit={status}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())

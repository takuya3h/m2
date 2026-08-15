#!/usr/bin/env python
"""設定側の集合を作る。

Hydra の合成を実際に走らせ、`configs/stage/*.yaml` それぞれについて
合成後の config を平坦化する。平坦化は葉（スカラー・None・空コンテナ）
までのドット区切り経路とする。リストの要素は展開せず、リスト自体を葉とする。

出力: audit/config_keys.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "config_keys.json"

from hydra import compose, initialize_config_dir  # noqa: E402
from omegaconf import DictConfig, ListConfig, OmegaConf  # noqa: E402


def flatten(node, prefix: str = "") -> dict[str, object]:
    """葉までのドット経路 -> 値。リストは葉として扱う。"""
    out: dict[str, object] = {}
    if isinstance(node, DictConfig) or isinstance(node, dict):
        items = list(node.items()) if not isinstance(node, DictConfig) else [
            (k, node._get_node(k)) for k in node.keys()
        ]
        if not items:
            out[prefix] = {}
            return out
        for key, _ in items:
            child = node[key] if not isinstance(node, DictConfig) else node.get(key)
            path = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(child, (DictConfig, dict)) and len(child) > 0:
                out.update(flatten(child, path))
            elif isinstance(child, (DictConfig, dict)):
                out[path] = {}
            else:
                out[path] = child if not isinstance(child, ListConfig) else list(child)
        return out
    out[prefix] = node
    return out


def main() -> None:
    stage_dir = PROJ / "configs" / "stage"
    stages = sorted(p.stem for p in stage_dir.glob("*.yaml"))
    result: dict[str, object] = {
        "proj": str(PROJ),
        "stages": {},
        "raw_files": {},
        "errors": {},
    }

    # (a) 合成後（Hydra が実際に組み立てる形）
    with initialize_config_dir(version_base=None, config_dir=str(PROJ / "configs")):
        base = compose(config_name="default", overrides=[])
        result["composed_default"] = sorted(flatten(base).keys())
        for stage in stages:
            try:
                cfg = compose(config_name="default", overrides=[f"stage={stage}"])
                flat = flatten(cfg)
                result["stages"][stage] = {
                    "keys": sorted(flat.keys()),
                    "values": {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in flat.items()},
                }
            except Exception as exc:  # noqa: BLE001
                result["errors"][stage] = f"{type(exc).__name__}: {exc}"

    # (b) 生ファイル（そのファイルが書いている項目そのもの）
    for path in sorted((PROJ / "configs").rglob("*.yaml")):
        rel = str(path.relative_to(PROJ))
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        empty = len(text.strip()) == 0
        try:
            node = None if empty else OmegaConf.load(path)
            flat = {} if node is None else flatten(node)
            result["raw_files"][rel] = {
                "empty": empty,
                "has_global_package": bool(lines)
                and lines[0].strip() == "# @package _global_",
                "keys": sorted(flat.keys()),
            }
        except Exception as exc:  # noqa: BLE001
            result["errors"][rel] = f"{type(exc).__name__}: {exc}"

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    union = set()
    for stage_data in result["stages"].values():
        union |= set(stage_data["keys"])
    print(f"stages composed: {len(result['stages'])}/{len(stages)}")
    print(f"errors: {len(result['errors'])}")
    print(f"union of composed leaf keys: {len(union)}")
    print(f"raw config files: {len(result['raw_files'])}")
    globals_ = sum(1 for v in result["raw_files"].values() if v["has_global_package"])
    print(f"raw files with '# @package _global_': {globals_}")
    print(f"written: {OUT}")


if __name__ == "__main__":
    sys.exit(main())

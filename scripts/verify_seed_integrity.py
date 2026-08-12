#!/usr/bin/env python3
"""verify_seed_integrity.py — Δ 基準点の汚染を機械的に検出する証跡検証ツール。

CLAUDE.md「研究インテグリティ」を人手の注意力依存から外し、決定的チェックに置く。
同一検出器の複数 seed 実験フォルダ群を受け取り、以下を検証する:

  1. コピー捏造検知: metrics.json / per_class_ap.json の md5 が seed 間で全て異なること。
     (同一ファイル = 3 seed のはずが実は 1 実験のコピー、という最悪の汚染を検出)
  2. eval_recipe 統一: test_cfg / lr_scaling / effective_batch_size / gpu_count が
     seed 間で完全一致すること (Δ 基準点汚染防止: §10.1)。
  3. seed 整合: ディレクトリ名末尾の seedN と command.sh の seed=N が一致すること。
  4. 必須証跡の存在: config.yaml / command.sh / git_commit.txt / metrics.json /
     per_class_ap.json / notes.md / server.txt。

終了コード: 全 PASS で 0、1 つでも FAIL で 1 (CI / hook で利用可能)。

使い方:
    # 検出器名 prefix で自動グルーピング
    python scripts/verify_seed_integrity.py experiments/baselines --group ddq
    # 明示的にフォルダ指定
    python scripts/verify_seed_integrity.py \
        experiments/baselines/s0_010_ddq_bbox_seed42 \
        experiments/baselines/s0_011_ddq_bbox_seed123 \
        experiments/baselines/s0_012_ddq_bbox_seed456
    # JSON 出力 (Notion 連携・hook 用)
    python scripts/verify_seed_integrity.py experiments/baselines --group ddq --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# eval_recipe のうち seed 間で必ず一致すべきキー (Δ 基準点を規定する設定)。
_RECIPE_INVARIANT_KEYS = (
    "effective_batch_size",
    "gpu_count",
    "lr_scaling",
)
_TESTCFG_INVARIANT_KEYS = ("score_thr", "max_per_img", "nms_pre", "nms_iou")

# setup() が必ず作る証跡ファイル。
_REQUIRED_FILES = (
    "config.yaml",
    "command.sh",
    "git_commit.txt",
    "metrics.json",
    "per_class_ap.json",
    "notes.md",
    "server.txt",
)


def _md5(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.md5(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _seed_from_dirname(name: str) -> int | None:
    m = re.search(r"seed(\d+)", name)
    return int(m.group(1)) if m else None


def _seed_from_command(exp_dir: Path) -> int | None:
    txt = ""
    p = exp_dir / "command.sh"
    if p.exists():
        txt = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"seed[= ](\d+)", txt)
    return int(m.group(1)) if m else None


def _check_required_files(exp_dir: Path) -> list[str]:
    """欠けている必須証跡ファイル名のリストを返す。"""
    missing = []
    for f in _REQUIRED_FILES:
        p = exp_dir / f
        if not p.exists() or p.stat().st_size == 0:
            missing.append(f)
    return missing


def verify_group(exp_dirs: list[Path]) -> dict:
    """1 グループ (同一検出器の複数 seed) を検証し、結果 dict を返す。"""
    result: dict = {
        "dirs": [str(d) for d in exp_dirs],
        "checks": {},
        "passed": True,
        "failures": [],
    }

    def fail(check: str, detail: str) -> None:
        result["passed"] = False
        result["failures"].append({"check": check, "detail": detail})

    # --- check 0: 必須証跡の存在 ---
    missing_map = {}
    for d in exp_dirs:
        missing = _check_required_files(d)
        if missing:
            missing_map[d.name] = missing
    result["checks"]["required_files"] = "ok" if not missing_map else missing_map
    if missing_map:
        fail("required_files", f"必須証跡が欠落: {missing_map}")

    # --- check 1: コピー捏造検知 (md5 全異) ---
    for fname in ("metrics.json", "per_class_ap.json"):
        md5s = {d.name: _md5(d / fname) for d in exp_dirs}
        present = [v for v in md5s.values() if v is not None]
        uniq = set(present)
        ok = len(present) == len(exp_dirs) and len(uniq) == len(present)
        result["checks"][f"md5_distinct[{fname}]"] = {
            "ok": ok,
            "md5": {k: (v[:10] if v else None) for k, v in md5s.items()},
        }
        if not ok:
            if len(present) < len(exp_dirs):
                fail(f"md5_distinct[{fname}]", f"{fname} が一部欠落: {md5s}")
            else:
                fail(
                    f"md5_distinct[{fname}]",
                    f"{fname} が seed 間で重複 (コピー捏造の疑い): {md5s}",
                )

    # --- check 2: eval_recipe 統一 ---
    recipes = {d.name: _read_json(d / "metrics.json").get("eval_recipe", {}) for d in exp_dirs}
    invariant_view = {}
    for name, r in recipes.items():
        tc = r.get("test_cfg", {}) if isinstance(r, dict) else {}
        invariant_view[name] = {
            **{k: r.get(k) for k in _RECIPE_INVARIANT_KEYS},
            **{f"test_cfg.{k}": tc.get(k) for k in _TESTCFG_INVARIANT_KEYS},
        }
    distinct_recipes = {json.dumps(v, sort_keys=True) for v in invariant_view.values()}
    recipe_ok = len(distinct_recipes) == 1 and all(invariant_view.values())
    result["checks"]["eval_recipe_unified"] = {
        "ok": recipe_ok,
        "view": invariant_view,
    }
    if not recipe_ok:
        fail(
            "eval_recipe_unified",
            f"eval_recipe (test_cfg/lr/bs/gpu) が seed 間で不一致 or 未記載: {invariant_view}",
        )

    # --- check 3: seed 整合 (dirname vs command.sh) ---
    seed_view = {}
    for d in exp_dirs:
        sd = _seed_from_dirname(d.name)
        sc = _seed_from_command(d)
        match = (sd is not None) and (sd == sc)
        seed_view[d.name] = {"dirname": sd, "command": sc, "match": match}
        if not match:
            fail("seed_consistency", f"{d.name}: dirname seed={sd} != command seed={sc}")
    result["checks"]["seed_consistency"] = seed_view

    return result


def _autogroup(base: Path, group: str) -> list[Path]:
    """base 配下から group 文字列を名前に含む実験フォルダを集める。"""
    if not base.is_dir():
        return []
    dirs = sorted(
        d for d in base.iterdir()
        if d.is_dir() and group in d.name and "seed" in d.name
    )
    return dirs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", help="実験フォルダ群、または --group 指定時は base ディレクトリ")
    ap.add_argument("--group", default=None, help="検出器名 prefix (例: ddq)。base 配下を自動グルーピング")
    ap.add_argument("--json", action="store_true", help="結果を JSON で出力")
    args = ap.parse_args(argv)

    if args.group:
        base = Path(args.paths[0])
        exp_dirs = _autogroup(base, args.group)
        if not exp_dirs:
            print(f"[verify] グループ '{args.group}' に該当する実験フォルダが {base} にありません", file=sys.stderr)
            return 1
    else:
        exp_dirs = [Path(p) for p in args.paths]

    result = verify_group(exp_dirs)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"=== seed integrity 検証: {len(exp_dirs)} フォルダ ===")
        for d in exp_dirs:
            print(f"  - {d.name}")
        print()
        # 各 check の合否は「その check 名が failures に出ているか」で決める
        # (check の値は dict 形状がまちまちなので、failures を正とする)。
        failed_checks = {f["check"] for f in result["failures"]}
        for check in result["checks"]:
            mark = "✗" if check in failed_checks else "✓"
            print(f"  [{mark}] {check}")
        print()
        if result["passed"]:
            print("RESULT: ✅ PASS — Δ 基準点として汚染なし")
        else:
            print("RESULT: ❌ FAIL")
            for f in result["failures"]:
                print(f"    - {f['check']}: {f['detail']}")

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

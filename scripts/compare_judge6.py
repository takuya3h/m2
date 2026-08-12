"""判断ポイント #6（§9 #6・§13.2 S0）:
Mask DINO vs Co-DETR を APr（稀少クラス AP = Skewer / Syringe の平均）で
比較し、3pt 以上の差が出れば S1 以降を Co-DETR ベースに切り替えるべきと判定する。

- Mask DINO の APr: ``s0_001`` 〜 ``s0_003`` の 3-seed 平均
- Co-DETR の APr:   ``s0_007`` 〜 ``s0_009`` の 3-seed 平均
- DeltaCalculator で eval_recipe 整合性を検証してから比較する
  （同一 split・同一 test_cfg・同一サーバー・同一 GPU 構成であること。
   gpu_count が一致しないと recipes_match が False を返し比較不能）

出力:
    - 両モデルの APr 平均±標準偏差
    - 差分 ΔAPr = APr(Co-DETR) - APr(Mask DINO)
    - 判定: |ΔAPr| >= 3.0 なら「検出ヘッド切替を検討」、未満なら「Mask DINO 継続」

使い方:
    python scripts/compare_judge6.py \\
        --baselines_dir experiments/baselines \\
        --maskdino_prefix s0_001,s0_002,s0_003 \\
        --codetr_prefix s0_007,s0_008,s0_009
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

# PYTHONPATH=src を付け忘れても動くよう src/ を通す。
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# Δ APr の切替判定しきい値（pt = 百分率）。§9 #6。
SWITCH_THRESHOLD_PT = 3.0


def _load_metrics(baselines_dir: Path, prefix: str) -> dict | None:
    """``baselines_dir/<prefix>_*/metrics.json`` を読む（最初に見つかった 1 件）。"""
    matches = sorted(baselines_dir.glob(f"{prefix}_*"))
    for cand in matches:
        path = cand / "metrics.json"
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
    return None


def _aggregate_apr(
    baselines_dir: Path,
    prefixes: list[str],
    metric_key: str,
) -> tuple[list[float], list[dict]]:
    """指定 prefix 群の AP_rare と eval_recipe を集約して返す。"""
    values: list[float] = []
    recipes: list[dict] = []
    for prefix in prefixes:
        metrics = _load_metrics(baselines_dir, prefix)
        if metrics is None:
            print(f"WARN: {prefix} の metrics.json が見つかりません", file=sys.stderr)
            continue
        ap = metrics.get(metric_key)
        if not isinstance(ap, (int, float)):
            print(f"WARN: {prefix}.{metric_key} が数値ではありません", file=sys.stderr)
            continue
        values.append(float(ap))
        recipe = metrics.get("eval_recipe")
        if isinstance(recipe, dict):
            recipes.append(recipe)
    return values, recipes


def _check_recipe_consistency(maskdino_recipes: list[dict], codetr_recipes: list[dict]) -> bool:
    """recipes_match で両群の代表 recipe を照合する（全 recipe が同等であることが前提）。"""
    from egosurgery.utils.eval_recipe import recipes_match

    if not maskdino_recipes or not codetr_recipes:
        print(
            "WARN: 一方の eval_recipe が空のため整合性検証をスキップします（後方互換）。",
            file=sys.stderr,
        )
        return True
    ok = recipes_match(maskdino_recipes[0], codetr_recipes[0])
    if not ok:
        print(
            "ERROR: Mask DINO と Co-DETR の eval_recipe が一致しません。"
            "split / test_cfg / GPU 構成（gpu_count）を揃えて再測定してください。",
            file=sys.stderr,
        )
    return ok


def _summary(values: list[float]) -> tuple[float, float]:
    """3-seed の平均と不偏標準偏差を返す（n<2 のとき std=0.0）。"""
    if not values:
        return 0.0, 0.0
    mean = statistics.fmean(values)
    std = statistics.stdev(values) if len(values) >= 2 else 0.0
    return mean, std


def judge(delta_pt: float, threshold_pt: float = SWITCH_THRESHOLD_PT) -> str:
    """ΔAPr から検出ヘッド切替の判断を文字列で返す。

    Args:
        delta_pt: ΔAPr の pt 単位（百分率）。
        threshold_pt: 切替検討のしきい値（既定 3.0pt）。

    Returns:
        ``"検出ヘッド切替を検討"`` または ``"Mask DINO 継続"``。
    """
    return (
        "検出ヘッド切替を検討" if abs(delta_pt) >= threshold_pt else "Mask DINO 継続"
    )


def main() -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baselines_dir", type=Path, default=Path("experiments/baselines"),
        help="S0 実験フォルダのルート。",
    )
    parser.add_argument(
        "--maskdino_prefix", type=str, default="s0_001,s0_002,s0_003",
        help="Mask DINO の prefix リスト（カンマ区切り）。",
    )
    parser.add_argument(
        "--codetr_prefix", type=str, default="s0_007,s0_008,s0_009",
        help="Co-DETR の prefix リスト（カンマ区切り）。",
    )
    parser.add_argument(
        "--metric_key", type=str, default="val/AP_rare",
        help="比較対象の指標キー（既定 val/AP_rare）。",
    )
    parser.add_argument(
        "--threshold_pt", type=float, default=SWITCH_THRESHOLD_PT,
        help="切替検討しきい値 pt（既定 3.0）。",
    )
    args = parser.parse_args()

    mdp = [s.strip() for s in args.maskdino_prefix.split(",") if s.strip()]
    cdp = [s.strip() for s in args.codetr_prefix.split(",") if s.strip()]

    mask_values, mask_recipes = _aggregate_apr(args.baselines_dir, mdp, args.metric_key)
    codetr_values, codetr_recipes = _aggregate_apr(args.baselines_dir, cdp, args.metric_key)

    if not _check_recipe_consistency(mask_recipes, codetr_recipes):
        return 2

    mask_mean, mask_std = _summary(mask_values)
    codetr_mean, codetr_std = _summary(codetr_values)
    # 値は 0-1 スケールで保存されている前提で pt に変換。
    delta_pt = (codetr_mean - mask_mean) * 100.0

    print("=" * 60)
    print(f"判断ポイント #6: Mask DINO vs Co-DETR @ {args.metric_key}")
    print("=" * 60)
    print(f"  Mask DINO: {mask_mean * 100:.2f} ± {mask_std * 100:.2f} pt  (n={len(mask_values)})")
    print(f"  Co-DETR  : {codetr_mean * 100:.2f} ± {codetr_std * 100:.2f} pt  (n={len(codetr_values)})")
    print(f"  ΔAPr     : {delta_pt:+.2f} pt   (しきい値 ±{args.threshold_pt} pt)")
    print(f"  判定      : {judge(delta_pt, args.threshold_pt)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

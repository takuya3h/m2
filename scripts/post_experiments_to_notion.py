#!/usr/bin/env python
"""完了済み実験を Notion「実験Run台帳」へ一括投稿する（バックフィル・本体 .venv）。

STEP B（B2a/T1a/B1/T1b…）は ExperimentManager 証跡（experiments/transfer/*/metrics.json）を持つが、
学習スクリプト側に Notion 投稿が配線されていなかった。本スクリプトは既存の
`egosurgery.utils.notion_logger.log_experiment_to_notion` を使い、各証跡フォルダを台帳行にする。

認証（NOTION_API_KEY / NOTION_DB_ID）は **環境変数で渡す**（このスクリプトは .env を読まない）。
未設定なら no-op。`--dry-run` は投稿せず「Name と Result プレビュー」を表示する（認証不要）。

実行:
  # プレビュー（認証不要・投稿しない）
  .venv/bin/python scripts/post_experiments_to_notion.py --dry-run
  # 実投稿（ユーザーが認証をロードしてから）
  set -a; source .env; set +a
  .venv/bin/python scripts/post_experiments_to_notion.py
  # 特定フォルダのみ
  .venv/bin/python scripts/post_experiments_to_notion.py experiments/transfer/b2a_det2phase_001_*
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.utils.notion_logger import (  # noqa: E402
    _format_result,
    log_experiment_to_notion,
)

# 既定のバックフィル対象（STEP B 標準証跡）。
DEFAULT_GLOBS = [
    "experiments/transfer/b2a_det2phase_*",
    "experiments/transfer/t1a_regiontoken_*",
    "experiments/transfer/b1_mtl_*",
    "experiments/transfer/t1b_*",
    "experiments/transfer/b2b_rescore_*",  # .json は collect() の is_dir で除外、dir のみ拾う
]

# 実験ファミリ → (step, tier, primary_metric, 分母メモ)。Name 接頭辞で判定。
FAMILY = {
    "b2a_": ("B", "must", "phase acc/macro-F1/jaccard/edit/seg-F1 (online_causal, jaccard strict)",
             "①信号 det→phase。Δ_phase vs S4 base 0.8986±0.0034"),
    "t1a_": ("B", "must", "phase acc/macro-F1/jaccard/edit/seg-F1 (online_causal)",
             "②object-token det→phase。Δ_phase vs S4 base 0.8986（within-server）"),
    "b1_mtl_": ("B", "must", "phase acc/macro-F1/jaccard + det mAP",
                "②素朴MTL。Δ_phase vs S4′ 0.9142 / Δ_det vs S0-frozen′ 0.7095"),
    "t1b_": ("B", "must", "det mAP（best − init=warm-start S0-frozen, 同一eval）",
             "①学習FiLM phase→det。Δ_det=best−init / 注入純効果=Δ_inj−Δ_ctrl"),
    "b2b_": ("B", "must", "det mAP baseline vs rescored",
             "①再採点 phase→det（training-free）。Δ_det=rescored−frozen（同一eval）"),
}


def family_meta(name: str):
    for pref, meta in FAMILY.items():
        if name.startswith(pref):
            return meta
    return ("B", "must", "(STEP B)", "")


def collect(args) -> list[Path]:
    if args.paths:
        out = []
        for p in args.paths:
            out += [Path(x) for x in PROJ.glob(p)] if not Path(p).is_absolute() else [Path(p)]
        return [d for d in out if d.is_dir()]
    dirs: list[Path] = []
    for g in DEFAULT_GLOBS:
        dirs += sorted(PROJ.glob(g))
    return [d for d in dirs if d.is_dir()]


def main():
    ap = argparse.ArgumentParser(description="Backfill completed experiments to Notion run ledger.")
    ap.add_argument("paths", nargs="*", help="exp_dir（省略時は STEP B 標準証跡を既定 glob）")
    ap.add_argument("--dry-run", action="store_true", help="投稿せず Name と Result プレビューのみ（認証不要）")
    args = ap.parse_args()

    dirs = collect(args)
    if not dirs:
        print("[notion-post] 対象なし")
        return
    print(f"[notion-post] {len(dirs)} 件 {'(DRY-RUN)' if args.dry_run else '(投稿)'}")
    ok = 0
    for d in dirs:
        step, tier, primary, denom = family_meta(d.name)
        if args.dry_run:
            m = {}
            mp = d / "metrics.json"
            if mp.exists():
                m = json.loads(mp.read_text())
            print(f"\n■ {d.name}  [step={step} tier={tier}]")
            print(f"  Result: {_format_result(m, denom)}")
            ok += 1
        else:
            res = log_experiment_to_notion(d, status="completed", step=step, tier=tier,
                                           primary_metric=primary, extra_result_text=denom)
            mark = "OK" if res else "skip(認証未設定 or 既存更新/失敗)"
            print(f"  {d.name}: {mark}")
            ok += 1 if res else 0
    if args.dry_run:
        print(f"\n[notion-post] DRY-RUN 完了（{ok} 件プレビュー）。実投稿は `set -a; source .env; set +a` 後に再実行。")
    else:
        print(f"[notion-post] 投稿成功 {ok}/{len(dirs)}（0 なら NOTION_API_KEY/NOTION_DB_ID 未ロード）")


if __name__ == "__main__":
    main()

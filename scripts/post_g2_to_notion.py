#!/usr/bin/env python3
"""G-2 本実験の 12 run を Notion 実験Run台帳へ投稿する。

汎用の `post_experiments_to_notion.py` は平坦な metrics.json を前提としており、
G-2 の `metrics.json`（val / test がネストした dict）から指標を取り出せない。
また run ディレクトリ名（`base_seed42` 等）は汎用的すぎて台帳の Name（冪等キー）が
他実験と衝突しうるため、`g2_` 接頭辞を付けて投稿する。

`post_t1b_ca_to_notion.py` / `post_hc_to_notion.py` と同じ「非標準 metrics 用の
専用ポスター」パターン。

Usage:
    set -a; source .env; set +a
    python scripts/post_g2_to_notion.py --out experiments/g2_main_2026-07-29_lecun
    python scripts/post_g2_to_notion.py --out ... --dry-run   # 認証不要のプレビュー
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.utils.notion_logger import log_experiment_to_notion  # noqa: E402

SYSTEMS = ["base", "bboxROI", "maskROI", "randROI"]
SEEDS = [42, 123, 456]
PREREG_PHASES = ["incision", "hemostasis", "closure"]

PRIMARY_METRIC = (
    "phase per-phase F1 (主指標) / accuracy / macro-F1。"
    "判定は事前登録どおり Welch の2標本SE と 動画単位クラスタ・ブートストラップ(B=2000) の AND"
)


def result_text(m: dict, system: str) -> str:
    """val / test の実測値を Result 列向けに整形する。"""
    lines = [
        f"system={system} seed={m['seed']} in_dim={m['in_dim']} "
        f"best_epoch={m['best_epoch']} epochs={m['epochs']} "
        f"train_seconds={m['train_seconds']:.1f}",
    ]
    for sp in ("val", "test"):
        d = m[sp]
        pc = d["phase_per_class_f1"]
        lines.append(
            f"{sp}: acc={d['phase_accuracy']:.4f} macroF1={d['phase_macro_f1']:.4f} "
            f"jaccard={d['phase_jaccard']:.4f} edit={d['phase_edit_score']:.2f} | "
            + " ".join(f"{k}={pc[k]:.4f}" for k in PREREG_PHASES)
        )
    fb = m.get("roi_fallback") or {}
    if fb:
        lines.append(
            "ROI fallback率(分母=各splitのGT box総数): "
            + " ".join(f"{k}={v['fallback_rate']:.4f}" for k, v in sorted(fb.items())
                       if v.get("fallback_rate") is not None)
        )
    lines.append(
        "事前登録: prereg/g2_prediction.md（学習前 commit 2dc430b・未改変）。"
        "主予測 3>2 は 0/6 で閾値超えせず FAIL = 負の結果。詳細は RESULTS.md"
    )
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="$OUT（runs/ を含むディレクトリ）")
    ap.add_argument("--dry-run", action="store_true",
                    help="投稿せず Name と Result をプレビュー（認証不要）")
    args = ap.parse_args()
    out = Path(args.out)

    posted = skipped = 0
    for system in SYSTEMS:
        for seed in SEEDS:
            d = out / "runs" / f"{system}_seed{seed}"
            if not (d / "metrics.json").exists():
                print(f"[skip] {d} に metrics.json が無い")
                skipped += 1
                continue
            m = json.loads((d / "metrics.json").read_text())
            env = json.loads((d / "env.json").read_text())

            # 標準の証跡レイアウトに合わせる。値は env.json の実測値をそのまま写す
            # （推測しない）。既にあるファイルは上書きしない。
            gc, sv = d / "git_commit.txt", d / "server.txt"
            if not gc.exists() and env.get("commit"):
                gc.write_text(env["commit"] + "\n")
            if not sv.exists() and env.get("host"):
                sv.write_text(env["host"] + "\n")

            name = f"g2_{system}_seed{seed}"
            txt = result_text(m, system)
            if args.dry_run:
                print(f"\n■ {name}  [step=B tier=must server={env.get('host')}]")
                print("\n".join("  " + x for x in txt.splitlines()))
                posted += 1
                continue
            r = log_experiment_to_notion(
                d, status="completed", step="B", tier="must",
                primary_metric=PRIMARY_METRIC, extra_result_text=txt,
                name_override=name,
            )
            if r is None:
                print(f"[fail] {name}（NOTION_API_KEY / NOTION_DB_ID を確認）")
                skipped += 1
            else:
                print(f"[ok]   {name}")
                posted += 1

    label = "DRY-RUN" if args.dry_run else "投稿"
    print(f"\n[g2-notion] {label} {posted} 件 / skip {skipped} 件")
    return 0 if skipped == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

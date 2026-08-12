#!/usr/bin/env python3
"""M2（選択規則の安定性解析）の 72 run を Notion 実験Run台帳へ投稿する。

M2 の metrics.json は G-2/S3/S4 と構造が異なる（5 規則ぶんの val/test がネストし、
反復 ID `rep` を持つ）ため、`post_g2_to_notion.py` は使えない。専用ポスター。

台帳の Name（冪等キー）は run ディレクトリ名 `<system>_seed<N>_rep<R>` に
`g2f_m2_` 接頭辞を付けたもの。既存の `g2f_s3_` / `g2f_s4_` と同じ名前空間規約。

Usage:
    set -a; source .env; set +a
    python scripts/post_m2_to_notion.py --out experiments/selection_noise_2026-07-29
    python scripts/post_m2_to_notion.py --out ... --dry-run   # 認証不要のプレビュー
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.utils.notion_logger import log_experiment_to_notion  # noqa: E402

SEEDS = [42, 123, 456]
REPS = [1, 2, 3]
RULES = ["R-acc", "R-last", "R-loss", "R-mf1", "R-topk"]
CHOSEN_RULE = "R-topk"
PREREG_PHASES = ["incision", "hemostasis", "closure"]

PRIMARY_METRIC = (
    "phase per-phase F1 (主指標、規則 R-topk 採用) / accuracy / macro-F1。"
    "5 epoch 選択規則 (R-acc/R-last/R-loss/R-mf1/R-topk) を同一学習軌跡から比較し val_metric_sd 最小の R-topk を採用。"
    "判定は seed x 反復 (n=9) の Welch + 動画別符号一致"
)


def result_text(m: dict, note: str) -> str:
    lines = [
        f"system={m['system']} seed={m['seed']} rep={m['rep']} in_dim={m['in_dim']} "
        f"epochs={m['epochs']} train_seconds={m['train_seconds']:.1f}",
    ]
    # 5 規則の比較（1 行で圧縮）
    rule_line = " | ".join(
        f"{r}{'*' if r == CHOSEN_RULE else ''}: "
        f"val_acc={m['rules'][r]['val']['phase_accuracy']:.4f} "
        f"test_acc={m['rules'][r]['test']['phase_accuracy']:.4f}"
        for r in RULES
    )
    lines.append("5規則比較(*=採用): " + rule_line)
    # 採用規則 (R-topk) の詳細
    r = m["rules"][CHOSEN_RULE]
    pc_v, pc_t = r["val"]["phase_per_class_f1"], r["test"]["phase_per_class_f1"]
    lines.append(
        f"[{CHOSEN_RULE}] selected_epoch={r['selected_epoch']} "
        f"val: acc={r['val']['phase_accuracy']:.4f} macroF1={r['val']['phase_macro_f1']:.4f} "
        f"jaccard={r['val']['phase_jaccard']:.4f} | "
        + " ".join(f"{k}={pc_v[k]:.4f}" for k in PREREG_PHASES)
    )
    lines.append(
        f"[{CHOSEN_RULE}] test: acc={r['test']['phase_accuracy']:.4f} "
        f"macroF1={r['test']['phase_macro_f1']:.4f} jaccard={r['test']['phase_jaccard']:.4f} | "
        + " ".join(f"{k}={pc_t[k]:.4f}" for k in PREREG_PHASES)
    )
    if note:
        lines.append(note)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="$OUT（runs/ を含むディレクトリ）")
    ap.add_argument("--dry-run", action="store_true",
                    help="投稿せず Name と Result をプレビュー（認証不要）")
    ap.add_argument("--prefix", default="g2f_m2_",
                    help="台帳の Name 接頭辞。Name は冪等キーなので実験群ごとに分ける")
    ap.add_argument("--note", default=(
        "事前登録: prereg/m2_prediction.md（学習前 commit 42b3ce2・未改変）。"
        "選択規則は run 間ばらつきの主要因でない (RULE_INEFFECTIVE, R-topk は R-acc比0.920)。"
        "n=3→9で判定が両方向に反転 (5-1 test/incision 非超過→超過、3-2/4-2 超過→非超過)。"
        "S3のPASSは維持されず『中間』に該当 (次元寄与43.7%@test/incision)。"
        "詳細は RESULTS.md"),
        help="Result 末尾に付す注記（事前登録と判定へのポインタ）")
    args = ap.parse_args()
    out = Path(args.out)

    systems = sorted({
        d.name.rsplit("_rep", 1)[0].rsplit("_seed", 1)[0]
        for d in (out / "runs").glob("*_seed*_rep*") if d.is_dir()
    })
    if not systems:
        print(f"[warn] {out/'runs'} に run が無い")
        return 1

    posted = skipped = 0
    for system in systems:
        for seed in SEEDS:
            for rep in REPS:
                d = out / "runs" / f"{system}_seed{seed}_rep{rep}"
                if not (d / "metrics.json").exists():
                    print(f"[skip] {d} に metrics.json が無い")
                    skipped += 1
                    continue
                m = json.loads((d / "metrics.json").read_text())
                env = json.loads((d / "env.json").read_text())

                gc, sv = d / "git_commit.txt", d / "server.txt"
                if not gc.exists() and env.get("commit"):
                    gc.write_text(env["commit"] + "\n")
                if not sv.exists() and env.get("host"):
                    sv.write_text(env["host"] + "\n")

                name = f"{args.prefix}{system}_seed{seed}_rep{rep}"
                txt = result_text(m, args.note)
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
    print(f"\n[m2-notion] {label} {posted} 件 / skip {skipped} 件")
    return 0 if skipped == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

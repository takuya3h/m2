#!/usr/bin/env python3
"""notify_experiment.py — 実験の完走/進捗を Slack 用に整形・通知する。

2 つの送信単位に対応 (両方運用):
  - seed 単位 (--mode seed): 1 つの実験フォルダ完走を通知。
  - 検出器単位 (--mode group): 同一検出器の 3 seed が出揃ったら mean±std を通知。

各通知に wandb run URL を含める:
  URL = https://wandb.ai/{WANDB_ENTITY}/{project}/runs/{run_id}
  run_id は実験フォルダ内 wandb/run-<ts>-<run_id>/ から抽出。
  wandb 未使用の検出器 (mmdet 2.x Sense-X 等) は「wandb ログなし」と明記。

送信は 2 経路 (どちらも可、webhook 優先):
  1. SLACK_WEBHOOK_URL が .env/環境変数にあれば直接 POST (Claude 非依存)。
  2. 無ければ整形テキストと JSON を stdout に出力 → Claude が拾って Slack MCP 送信。

依存追加なし (requests のみ、json/statistics は標準)。

使い方:
  # 検出器単位 (3 seed まとめ)
  python scripts/notify_experiment.py --mode group \
      --dirs experiments/baselines/s0_010_ddq_bbox_seed42 \
             experiments/baselines/s0_011_ddq_bbox_seed123 \
             experiments/baselines/s0_012_ddq_bbox_seed456 \
      --detector "DDQ-DETR"
  # seed 単位
  python scripts/notify_experiment.py --mode seed \
      --dirs experiments/baselines/s0_013_sensex_codino_bbox_seed42 \
      --detector "Sense-X Co-DINO 9enc"
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WANDB_PROJECT_DEFAULT = "egosurgery_multitask"


# ----------------------------------------------------------------------------
# .env 読み込み (依存追加を避けた最小パーサ。既存環境変数は上書きしない)
# ----------------------------------------------------------------------------
def load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


# ----------------------------------------------------------------------------
# wandb URL 構成
# ----------------------------------------------------------------------------
def find_wandb_url(exp_dir: Path) -> str | None:
    """実験フォルダ内 wandb/run-<ts>-<run_id> から wandb run URL を構成。

    wandb 未使用 (run ディレクトリ無し) なら None。
    """
    entity = os.environ.get("WANDB_ENTITY", "").strip()
    project = os.environ.get("WANDB_PROJECT", WANDB_PROJECT_DEFAULT).strip()
    run_id = None

    # (1) mmdet 系: exp_dir/wandb/run-<ts>-<id> から抽出。
    wandb_root = exp_dir / "wandb"
    if wandb_root.is_dir():
        run_dirs = sorted(
            d for d in wandb_root.iterdir()
            if d.is_dir() and re.match(r"run-\d{8}_\d{6}-\w+", d.name)
        )
        if run_dirs:
            m = re.search(r"run-\d{8}_\d{6}-(\w+)", run_dirs[-1].name)
            if m:
                run_id = m.group(1)

    # (2) detrex 系: post_process が橋渡しした exp_dir/wandb_run.txt を読む
    #     (detrex は wandb を work_dir に置くため exp_dir には run_id だけ転記される)。
    if run_id is None:
        bridge = exp_dir / "wandb_run.txt"
        if bridge.exists():
            run_id = bridge.read_text(encoding="utf-8").strip() or None

    if run_id is None:
        return None
    if not entity:
        # entity 不明でも run_id は返す (URL は組めないので注記付き)
        return f"(wandb run_id={run_id}; WANDB_ENTITY 未設定で URL 生成不可)"
    return f"https://wandb.ai/{entity}/{project}/runs/{run_id}"


# ----------------------------------------------------------------------------
# metrics 読み出し
# ----------------------------------------------------------------------------
def _read_metrics(exp_dir: Path) -> dict:
    p = exp_dir / "metrics.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _seed_of(exp_dir: Path) -> int | None:
    m = re.search(r"seed(\d+)", exp_dir.name)
    return int(m.group(1)) if m else None


def _metric(m: dict, *keys: str) -> float | None:
    for k in keys:
        v = m.get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return None


# ----------------------------------------------------------------------------
# 証跡検証 (verify_seed_integrity を呼ぶ)
# ----------------------------------------------------------------------------
def run_integrity_check(dirs: list[Path]) -> tuple[bool, str]:
    script = REPO_ROOT / "scripts" / "verify_seed_integrity.py"
    if not script.exists():
        return (False, "verify_seed_integrity.py 不在")
    try:
        out = subprocess.run(
            [sys.executable, str(script), *[str(d) for d in dirs]],
            capture_output=True, text=True, timeout=60,
        )
        passed = out.returncode == 0
        summary = "✅ PASS (md5全異/recipe統一/seed整合)" if passed else "❌ FAIL"
        return (passed, summary)
    except Exception as exc:  # noqa: BLE001
        return (False, f"検証実行失敗: {exc}")


# ----------------------------------------------------------------------------
# 通知本文の整形
# ----------------------------------------------------------------------------
def build_group_message(dirs: list[Path], detector: str) -> str:
    """検出器単位 (3 seed まとめ) の通知本文。定量結果は等幅コードブロックの表で出す
    (Slack は通常の md 表を描画しないため ``` フェンス内で桁揃え。列見出しは ASCII)。"""
    sorted_dirs = sorted(dirs)
    data = {d: _read_metrics(d) for d in sorted_dirs}
    seeds = [_seed_of(d) for d in sorted_dirs]
    seed_str = "/".join(str(s) for s in seeds)

    metric_defs = [
        ("mAP", ("val/mAP", "mAP")),
        ("AP_rare", ("val/AP_rare",)),
        ("AP_common", ("val/AP_common",)),
        ("mAP_50", ("val/mAP_50",)),
        ("mAP_75", ("val/mAP_75",)),
    ]

    def fmt(v: float | None) -> str:
        return f"{v:.4f}" if isinstance(v, (int, float)) else "n/a"

    # ヘッダ: metric | mean | std | seed42 | seed123 | seed456 ...
    seed_cols = [f"s{s}" for s in seeds]
    header = f"{'metric':<10}{'mean':>8}{'std':>8}" + "".join(f"{c:>9}" for c in seed_cols)
    lines = [header, "-" * len(header)]
    for name, keys in metric_defs:
        vals = [_metric(data[d], *keys) for d in sorted_dirs]
        present = [v for v in vals if isinstance(v, (int, float))]
        mean = f"{statistics.mean(present):.4f}" if present else "n/a"
        std = f"{statistics.pstdev(present):.4f}" if len(present) > 1 else "-"
        row = f"{name:<10}{mean:>8}{std:>8}" + "".join(f"{fmt(v):>9}" for v in vals)
        lines.append(row)
    table = "```\n" + "\n".join(lines) + "\n```"

    server = os.environ.get("SERVERNAME", "unknown")
    _passed, integ = run_integrity_check(dirs)
    url_lines = "\n".join(
        f"  • seed{_seed_of(d)}: {find_wandb_url(d) or '(wandb ログなし)'}"
        for d in sorted_dirs
    )

    return (
        f":white_check_mark: *[S0 実験完了] {detector}* ({len(dirs)} seed: {seed_str})\n"
        f"server: {server} (RTX 6000 Ada x2) ｜ 証跡検証: {integ}\n"
        f"{table}\n"
        f"wandb:\n{url_lines}"
    )


def build_seed_message(exp_dir: Path, detector: str) -> str:
    """seed 単位 (1 実験) の通知本文。定量結果は等幅コードブロックの表で出す。"""
    m = _read_metrics(exp_dir)
    seed = _seed_of(exp_dir)
    epoch = m.get("epoch")
    url = find_wandb_url(exp_dir)
    server = os.environ.get("SERVERNAME", "unknown")

    def f(v):
        return f"{v:.4f}" if isinstance(v, (int, float)) else "n/a"

    rows = [
        ("mAP", _metric(m, "val/mAP", "mAP")),
        ("AP_rare", _metric(m, "val/AP_rare")),
        ("AP_common", _metric(m, "val/AP_common")),
        ("mAP_50", _metric(m, "val/mAP_50")),
        ("mAP_75", _metric(m, "val/mAP_75")),
    ]
    header = f"{'metric':<10}{'value':>9}"
    lines = [header, "-" * len(header)]
    lines += [f"{name:<10}{f(v):>9}" for name, v in rows]
    table = "```\n" + "\n".join(lines) + "\n```"

    return (
        f":checkered_flag: *[S0 seed 完了] {detector} / seed{seed}* (best epoch {epoch})\n"
        f"server: {server} ｜ 証跡: {exp_dir.name}\n"
        f"{table}\n"
        f"wandb: {url if url else '(wandb ログなし)'}"
    )


# ----------------------------------------------------------------------------
# 送信
# ----------------------------------------------------------------------------
def post_to_slack_webhook(text: str) -> bool:
    url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not url:
        return False
    try:
        import requests

        r = requests.post(url, json={"text": text}, timeout=10)
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["seed", "group"], required=True)
    ap.add_argument("--dirs", nargs="+", required=True, help="実験フォルダ群")
    ap.add_argument("--detector", required=True, help="検出器の表示名")
    ap.add_argument("--emit-json", action="store_true",
                    help="Slack MCP 送信用に {text, channel_hint} を JSON 出力")
    args = ap.parse_args(argv)

    load_dotenv(REPO_ROOT / ".env")
    dirs = [Path(d) for d in args.dirs]

    if args.mode == "group":
        text = build_group_message(dirs, args.detector)
    else:
        text = build_seed_message(dirs[0], args.detector)

    sent = post_to_slack_webhook(text)

    if args.emit_json:
        print(json.dumps({
            "text": text,
            "channel_hint": "C0B6K455UJK",  # #experiment (Me_only ws)
            "sent_via_webhook": sent,
        }, ensure_ascii=False))
    else:
        print(text)
        print()
        print(f"[notify] webhook送信: {'成功' if sent else '未送信 (上記テキストを Slack MCP で送ってください)'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

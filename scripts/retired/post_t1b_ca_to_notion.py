#!/usr/bin/env python
"""T1b-CA（§4.6 primary cross-attention phase→det）の 6 Run を Notion 実験Run台帳へ投稿する。

CA は seed{42,123,456} × {inj(real-ctx), ctrl(zero-ctx)} の 6 走。各走は
`transfer/t1b_ca_seed{S}{suffix}/{injected,control}_result.json`（t1b_result.json 形式：
seed/inject/trainable/zero_ctx/epochs/init_mAP/best_epoch/mAP/per_class_coco_map）を持つが
metrics.json は無いため、既定の post_experiments_to_notion.py では拾えない。本スクリプトが
inj/ctrl/純効果(inj−ctrl) を Result に整形して **Name 冪等**で upsert する。

認証は環境変数（NOTION_API_KEY / NOTION_DB_ID）。未設定なら no-op。--dry-run は投稿しない。

実行:
  set -a; source .env; set +a
  .venv/bin/python scripts/post_t1b_ca_to_notion.py            # 実投稿
  .venv/bin/python scripts/post_t1b_ca_to_notion.py --dry-run  # プレビュー（認証不要）
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

NOTION_VERSION = "2022-06-28"
API_BASE = "https://api.notion.com/v1"

# 各 seed の証跡フォルダ（inj/ctrl は同一フォルダ内の 2 ファイル）と実行サーバー。
SEEDS = [
    (42,  "transfer/t1b_ca_seed42_bengio", "bengio"),
    (123, "transfer/t1b_ca_seed123_lecun", "lecun"),
    (456, "transfer/t1b_ca_seed456_lecun", "lecun"),
]
PRIMARY = ("det mAP (best-init=warm-start S0-frozen, 同一eval); "
           "phase->det 純効果 = 注入(real-ctx) - 対照(zero-ctx)")
THREE_SEED_NOTE = ("T1b-CA §4.6 primary cross-attn. 3-seed 純効果 dDet(inj-ctrl)="
                   "s42 +0.00245 / s123 +0.00161 / s456 +0.00127, mean +0.00178, "
                   "paired-sigma |mean|/s=3.58 全正だが分母σ=0.0052以下=実用上微小。CA≈FiLM(+0.0019)。")


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "-C", str(PROJ), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip()[:12]
    except Exception:  # noqa: BLE001
        return ""


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _result_text(inj: dict, ctrl: dict, zero_ctx: bool) -> str:
    init = inj.get("init_mAP")
    pure = inj["mAP"] - ctrl["mAP"]
    if not zero_ctx:
        return (f"det mAP(inj, real-ctx)={inj['mAP']:.5f}, init/warm-start={init:.5f}; "
                f"対照 ctrl(zero-ctx)={ctrl['mAP']:.5f} -> 純効果 dDet(inj-ctrl)={pure:+.5f} "
                f"(best@ep{inj['best_epoch']})\n{THREE_SEED_NOTE}")
    return (f"det mAP(ctrl, zero-ctx)={ctrl['mAP']:.5f} = init(warm-start)={init:.5f} "
            f"(best@ep{ctrl['best_epoch']}); 注入対照（phase context=0 で fine-tune）\n{THREE_SEED_NOTE}")


def _find_existing(db_id: str, name: str, headers: dict) -> str | None:
    import requests
    r = requests.post(f"{API_BASE}/databases/{db_id}/query", headers=headers,
                      json={"filter": {"property": "Name", "title": {"equals": name}},
                            "page_size": 1}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"query {r.status_code} {r.text[:200]}")
    res = r.json().get("results") or []
    return res[0]["id"] if res else None


def _upsert(db_id: str, name: str, props: dict, headers: dict) -> str:
    import requests
    pid = _find_existing(db_id, name, headers)
    if pid:
        r = requests.patch(f"{API_BASE}/pages/{pid}", headers=headers,
                           json={"properties": props}, timeout=30)
        action = "updated"
    else:
        r = requests.post(f"{API_BASE}/pages", headers=headers,
                          json={"parent": {"database_id": db_id}, "properties": props}, timeout=30)
        action = "created"
    if r.status_code != 200:
        raise RuntimeError(f"{action} {r.status_code} {r.text[:300]}")
    return action


def build_runs():
    commit = _git_commit()
    runs = []
    for seed, rel, server in SEEDS:
        d = PROJ / rel
        inj = _load(d / "injected_result.json")
        ctrl = _load(d / "control_result.json")
        if not inj or not ctrl:
            print(f"[ca-post] SKIP seed{seed}: result.json 欠損 ({d})")
            continue
        for zero_ctx in (False, True):
            tag = "ctrl" if zero_ctx else "inj"
            runs.append({
                "name": f"t1b_ca_{tag}_seed{seed}",
                "seed": seed, "server": server, "commit": commit,
                "result": _result_text(inj, ctrl, zero_ctx),
                "artifacts": f"file://{d.resolve()}",
            })
    return runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    runs = build_runs()
    print(f"[ca-post] {len(runs)} 件 {'(DRY-RUN)' if args.dry_run else '(投稿)'}")
    if args.dry_run:
        for r in runs:
            print(f"\n■ {r['name']}  [seed={r['seed']} server={r['server']}]\n  {r['result'].splitlines()[0]}")
        print("\n[ca-post] DRY-RUN 完了。実投稿は `set -a; source .env; set +a` 後に再実行。")
        return

    api_key = os.environ.get("NOTION_API_KEY", "").strip()
    db_id = os.environ.get("NOTION_DB_ID", "").strip()
    if not api_key or not db_id:
        print("[ca-post] NOTION_API_KEY / NOTION_DB_ID 未設定 -> no-op")
        return
    headers = {"Authorization": f"Bearer {api_key}", "Notion-Version": NOTION_VERSION,
               "Content-Type": "application/json"}
    ok = 0
    for r in runs:
        props = {
            "Name": {"title": [{"text": {"content": r["name"]}}]},
            "Status": {"select": {"name": "completed"}},
            "Step": {"select": {"name": "B"}},
            "Tier": {"select": {"name": "must"}},
            "Server": {"select": {"name": r["server"]}},
            "Seed": {"number": r["seed"]},
            "Primary Metric": {"rich_text": [{"text": {"content": PRIMARY}}]},
            "Result": {"rich_text": [{"text": {"content": r["result"]}}]},
            "Commit": {"rich_text": [{"text": {"content": r["commit"]}}]},
            "Artifacts": {"url": r["artifacts"]},
            "Decision Needed": {"checkbox": False},
        }
        try:
            action = _upsert(db_id, r["name"], props, headers)
            print(f"  {r['name']}: {action}")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  {r['name']}: FAIL {exc}")
    print(f"[ca-post] 投稿 {ok}/{len(runs)}")


# --- 退役（2026-09-01, T-2026-09-01-notion-retire-scripts-and-speccheck）------ #
# 本スクリプトは旧データベース群へ自前で REST を呼んで書いていた。旧 DB は
# 2026-08-31 に凍結し、**CLI が Notion に触れるのは配布台帳だけになった。**
# 識別子を NOTION_DB_ID 環境変数や登録簿から自前で解決するため、登録簿の退役
# だけでは止まらない。**入口で止める。** 全行の写しは docs/archive/notion/db/ にある。
RETIRED_SINCE = "2026-09-01"


def _retired_notice() -> int:
    """呼ばれたら投稿せず退役の旨を出して終える。**無言で成功したことにしない。**"""
    import sys as _sys
    print(
        f"[retired] {__file__} は {RETIRED_SINCE} に退役した。Notion へ投稿しない。"
        " 旧データベースの内容は docs/archive/notion/db/ の写しを読む。",
        file=_sys.stderr,
    )
    return 3

if __name__ == "__main__":
    raise SystemExit(_retired_notice())

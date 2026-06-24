#!/usr/bin/env python
"""T1b Phase→Det の後処理（本体 .venv）— /tmp work_dir → 証跡組成 + Δ + Notion投稿。

train_t1b.py（.venv-relation-detr）は seed 毎に注入 run（/tmp/t1b_seed{N}）と §4.6 対照
run（/tmp/t1b_zeroctx_seed{N}）の t1b_result.json（init_mAP/mAP/per_class）を出す。本スクリプトは
本体 .venv で両者を読み、**Δ_det=best−init** と **注入純効果=Δ_injected−Δ_control** を計算し、
ExperimentManager 証跡 experiments/transfer/t1b_phasefilm_{seq}_seed{N} を組成して Notion 台帳に投稿する。

実行:
  .venv/bin/python scripts/postprocess_t1b.py --seed 123        # 単一 seed
  .venv/bin/python scripts/postprocess_t1b.py                   # /tmp/t1b_seed* を自動検出（全 seed）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.utils.experiment_manager import ExperimentManager  # noqa: E402
from egosurgery.utils.notion_logger import log_experiment_to_notion  # noqa: E402
from egosurgery.utils.server_name import resolve_server_name  # noqa: E402

DESC = "t1b_phasefilm"
DENOM = "①学習FiLM phase→det。Δ_det=best−init（init=warm-start S0-frozen, 同一eval）/ 注入純効果=Δ_inj−Δ_ctrl"


def discover_seeds() -> list[int]:
    seeds = set()
    for d in Path("/tmp").glob("t1b_seed*"):
        m = re.match(r"t1b_seed(\d+)$", d.name)
        if m and (d / "t1b_result.json").exists():
            seeds.add(int(m.group(1)))
    return sorted(seeds)


def _load(work: Path) -> dict | None:
    p = work / "t1b_result.json"
    return json.loads(p.read_text()) if p.exists() else None


def process_seed(seed: int, post: bool) -> dict | None:
    inj = _load(Path(f"/tmp/t1b_seed{seed}"))
    ctrl = _load(Path(f"/tmp/t1b_zeroctx_seed{seed}"))
    if inj is None:
        print(f"[t1b-post] seed{seed}: 注入 run の result が無い（skip）")
        return None
    d_inj = inj["mAP"] - inj["init_mAP"]
    metrics = {
        "mAP": inj["mAP"], "init_mAP": inj["init_mAP"], "delta_detection": d_inj,
        "epoch": inj.get("best_epoch"),
    }
    note_extra = f"Δ_inj={d_inj:+.4f}"
    if ctrl is not None:
        d_ctrl = ctrl["mAP"] - ctrl["init_mAP"]
        metrics.update({"control_mAP": ctrl["mAP"], "control_init_mAP": ctrl["init_mAP"],
                        "delta_control": d_ctrl, "injection_effect": d_inj - d_ctrl})
        note_extra += f" / Δ_ctrl={d_ctrl:+.4f} / 注入純効果={d_inj - d_ctrl:+.4f}"
    else:
        print(f"[t1b-post] seed{seed}: §4.6 対照(zero-ctx)が無い → 注入純効果は未算出")

    server = resolve_server_name(None)
    mgr = ExperimentManager(base_dir=str(PROJ / "experiments"), category="transfer",
                            step="t1b_phasefilm", description=DESC, seed=seed)
    mgr.setup({
        "experiment": {"category": "transfer", "step": "t1b_phasefilm", "description": DESC},
        "seed": seed,
        "method": {"name": "t1b_phase_to_det", "system": "①predictive_interaction/FiLM",
                   "direction": "phase->det", "ref": "MT4MTL-KD-style §4.6 (FiLM下限)",
                   "warm_start": "s0_01{6,7,8} best_ap.pth", "trainable": inj.get("trainable"),
                   "epochs": inj.get("epochs")},
        "delta": {"denominator": "S0-frozen (=init mAP, within-run)", "note": DENOM},
        "server_name": server,
    })
    mgr.log_metrics(metrics)
    mgr.log_per_class_ap(inj.get("per_class_coco_map", {}))
    (mgr.exp_dir / "notes.md").write_text(
        f"# T1b Phase→Det FiLM 注入 (seed{seed})\n\n"
        f"warm-start={Path(f'/tmp/t1b_seed{seed}').name} / 対照={'有' if ctrl else '無'}。\n"
        f"- 注入 mAP={inj['mAP']:.4f} (init {inj['init_mAP']:.4f})\n"
        f"- {note_extra}\n\n分母=init mAP（FiLM恒等=warm-start S0-frozen, 同一eval）。{DENOM}\n",
        encoding="utf-8")
    print(f"[t1b-post] seed{seed}: mAP={inj['mAP']:.4f} init={inj['init_mAP']:.4f} {note_extra} -> {mgr.exp_dir}")

    if post:
        res = log_experiment_to_notion(
            mgr.exp_dir, status="completed", step="B", tier="must",
            primary_metric="det mAP（best − init=warm-start S0-frozen, 同一eval）",
            extra_result_text=DENOM)
        print(f"[t1b-post] seed{seed} Notion: {'OK' if res else 'skip(認証未設定 or 失敗)'}")
    return metrics


def main():
    ap = argparse.ArgumentParser(description="T1b postprocess: /tmp work → 証跡 + Δ + Notion.")
    ap.add_argument("--seed", type=int, default=None, help="単一 seed（省略時は /tmp を自動検出）")
    ap.add_argument("--no-notion", action="store_true", help="Notion 投稿しない")
    args = ap.parse_args()
    seeds = [args.seed] if args.seed is not None else discover_seeds()
    if not seeds:
        print("[t1b-post] 対象 seed なし（/tmp/t1b_seed*/t1b_result.json が無い）")
        return
    print(f"[t1b-post] seeds={seeds}")
    for s in seeds:
        process_seed(s, post=not args.no_notion)


if __name__ == "__main__":
    main()

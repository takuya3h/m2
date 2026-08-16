#!/usr/bin/env python
"""本契約で走らせる設定を作る。

前の契約の写しを土台に、変えるのは次の二つだけである。

  task_id            本契約の識別子（outputs.stamp.task_id_in が要求する）
  train.deterministic  真。**設定に書いた値が読まれるかを Phase A で確かめる**

学習・評価コードは変更しない（禁止 5）。設定の写しは tasks/ 配下へ置く。

G1 の対照用に、決定性を無効にした写しも別に作る。

出力: audit/configs/*.yaml, audit/g1_configs/*.yaml
"""

from __future__ import annotations

import json
from pathlib import Path

from omegaconf import OmegaConf

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]
SRC = PROJ / "tasks" / "T-2026-08-15-injection-form-sweep" / "audit" / "configs"
OUT = AUDIT / "configs"
G1 = AUDIT / "g1_configs"
TASK_ID = "T-2026-08-15-injection-sweep-deterministic"

# SPEC の腕の並びと設定の対応。**実装を読んで確かめた値を書く。**
ARMS = {
    "uninformative": "s4_grasp_injection_ctrl.yaml",
    "oracle": "s4_grasp_injection_oracle_upper_bound_only.yaml",
    "inferred": "s4_grasp_injection_inj.yaml",
    "raw_logits": "s4_grasp_injection_raw_logits.yaml",
    "standardized": "s4_grasp_injection_standardized.yaml",
    "staged": "s4_grasp_injection_staged.yaml",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    G1.mkdir(parents=True, exist_ok=True)
    table = {}
    for arm, filename in ARMS.items():
        cfg = OmegaConf.load(SRC / filename)
        cfg.task_id = TASK_ID
        OmegaConf.update(cfg, "train.deterministic", True, merge=True)
        path = OUT / f"{arm}.yaml"
        OmegaConf.save(cfg, path)
        g = cfg.grasp_inference
        table[arm] = {
            "config": str(path.relative_to(PROJ)),
            "source": str((SRC / filename).relative_to(PROJ)),
            "arm": str(g.arm),
            "signal": str(g.get("signal", "<none>")),
            "staged": bool(g.get("staged", False)),
            "epochs": int(cfg.train.epochs),
            "epochs_stage1": int(cfg.train.get("epochs_stage1", 0)) or None,
            "task_id": str(cfg.task_id),
            "deterministic": bool(cfg.train.deterministic),
            "feature_cache": str(cfg.data.feature_cache),
            "phase_manifest": str(cfg.data.phase_manifest),
            "population": dict(cfg.data.population),
        }

    # G1 の対照: 決定性を無効にした写し（対照の腕のみ）
    for arm in ("uninformative",):
        cfg = OmegaConf.load(OUT / f"{arm}.yaml")
        OmegaConf.update(cfg, "train.deterministic", False, merge=True)
        OmegaConf.save(cfg, G1 / f"{arm}_nondeterministic.yaml")

    (AUDIT / "arm_table.json").write_text(
        json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"{'arm':14s} {'cfg.arm':6s} {'signal':26s} {'staged':7s} {'det':5s} epochs")
    for arm, meta in table.items():
        print(
            f"{arm:14s} {meta['arm']:6s} {meta['signal']:26s} "
            f"{str(meta['staged']):7s} {str(meta['deterministic']):5s} {meta['epochs']}"
        )
    print()
    print(f"written: {OUT} ({len(table)} configs) / {G1} (1 control)")


if __name__ == "__main__":
    main()

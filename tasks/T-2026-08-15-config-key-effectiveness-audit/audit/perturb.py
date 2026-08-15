#!/usr/bin/env python
"""Phase B: 値を変えて挙動が変わるかを実際に走らせて確かめる。

判定の基準は「同じ設定で二度走らせた差」である。先にそれを測り、
それより小さい差を「変わった」と述べない。

出力: audit/effectiveness.json
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]
CFG_DIR = AUDIT / "perturb_cfgs"
RUN_DIR = AUDIT / "runs" / "perturb"

ENTRY = {
    "original": "scripts/train_grasp_phase_injection.py",
    "variants": "scripts/train_grasp_phase_injection_variants.py",
}
BASE_CFG = {
    "original": "tasks/T-2026-08-15-grasp-injection-effect/audit/run_inj.yaml",
    "variants": "tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_inj.yaml",
}

# (鍵, 新しい値, 事前の分類)  分類は categories.json の実測に基づく
PERTURBATIONS = [
    # --- 読まれていないと判定したもの（条件として引用されうる高優先度） ---
    ("frozen_source.detector", "align_detr", "unread"),
    ("frozen_source.checkpoint", "third_party/NOPE/does_not_exist.pth", "unread"),
    ("frozen_source.seed", 999, "unread"),
    ("frozen_source.cache_dir", "data/processed/NOPE", "unread"),
    ("eval_recipe.protocol_source", "BOGUS_PROTOCOL", "unread"),
    ("eval_recipe.inference_protocol", "offline_full", "unread"),
    ("eval_recipe.jaccard_mode", "relaxed", "unread"),
    ("model.component", "bogus_component", "unread"),
    ("train.batch_size", 64, "unread"),
    ("train.freeze_backbone", False, "unread"),
    ("data.population.test", 1, "unread"),
    ("experiment.category", "bogus_category", "unread"),
    ("experiment.step", "s9_bogus", "unread"),
    ("logging.wandb_project", "bogus_project", "unread"),
    # --- 入口によって変わるもの（前契約の題材） ---
    ("grasp_inference.signal", "raw_logits", "entrypoint_dependent"),
    # --- 判定できない（丸ごと渡す経路の下）を摂動で解決する ---
    ("grasp_inference.detach_from_phase_loss", False, "unknown"),
    ("model.temporal.num_stages", 1, "unknown"),
    ("model.temporal.num_layers", 4, "unknown"),
    ("model.temporal.num_f_maps", 32, "unknown"),
    ("model.temporal.dropout", 0.1, "unknown"),
    # --- 対照: 読まれていると判定したもの（変われば測り方が生きている） ---
    ("train.lr", 0.005, "read"),
    ("train.smoothing_weight", 0.9, "read"),
    ("grasp_inference.hidden_dim", 32, "read"),
    ("seed", 43, "read"),
]

SKIP_FIELDS = {"elapsed_seconds", "device", "task_id", "arm", "completed"}


def numeric(metrics: dict) -> dict[str, float]:
    return {
        k: float(v)
        for k, v in metrics.items()
        if k not in SKIP_FIELDS and isinstance(v, (int, float)) and not isinstance(v, bool)
    }


def run_one(entry: str, cfg_path: Path, tag: str) -> dict | None:
    out = RUN_DIR / tag
    if out.exists():
        shutil.rmtree(out)
    env = dict(os.environ)
    env.pop("WANDB_API_KEY", None)
    env["WANDB_MODE"] = "disabled"
    env["PYTHONPATH"] = "src"
    cmd = [
        sys.executable,
        ENTRY[entry],
        "--config",
        str(cfg_path),
        "--smoke",
        "--epochs",
        "1",
        "--device",
        "cpu",
        "--max-train-clips",
        "2",
        "--max-val-clips",
        "2",
        "--output-dir",
        str(out),
    ]
    if entry == "variants":
        cmd += ["--stage1-epochs", "1"]
    proc = subprocess.run(cmd, cwd=PROJ, env=env, capture_output=True, text=True)
    mfile = out / "smoke_metrics.json"
    if proc.returncode != 0 or not mfile.exists():
        return {
            "failed": True,
            "returncode": proc.returncode,
            "stderr_tail": proc.stderr.strip().splitlines()[-3:],
        }
    return json.loads(mfile.read_text(encoding="utf-8"))


def compare(a: dict, b: dict) -> dict:
    if a.get("failed") or b.get("failed"):
        return {"comparable": False}
    na, nb = numeric(a), numeric(b)
    keys = sorted(set(na) | set(nb))
    diffs = {k: abs(na.get(k, float("nan")) - nb.get(k, float("nan"))) for k in keys}
    finite = [v for v in diffs.values() if v == v]
    return {
        "comparable": True,
        "max_abs_diff": max(finite) if finite else None,
        "n_fields": len(keys),
        "n_changed": sum(1 for v in finite if v > 0.0),
        "per_field": diffs,
    }


def set_key(cfg, dotted: str, value) -> None:
    from omegaconf import OmegaConf

    OmegaConf.update(cfg, dotted, value, merge=True)


def main() -> int:
    from omegaconf import OmegaConf

    CFG_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    report: dict = {"noise_floor": {}, "results": {}}

    for entry in ("original", "variants"):
        base_src = PROJ / BASE_CFG[entry]
        base_copy = CFG_DIR / f"{entry}__baseline.yaml"
        shutil.copyfile(base_src, base_copy)

        # --- 基準: 同じ設定で二度走らせた差 ---
        first = run_one(entry, base_copy, f"{entry}__baseline_a")
        second = run_one(entry, base_copy, f"{entry}__baseline_b")
        floor = compare(first, second)
        report["noise_floor"][entry] = {
            "config": BASE_CFG[entry],
            "run_a_ok": not first.get("failed", False),
            "run_b_ok": not second.get("failed", False),
            "max_abs_diff": floor.get("max_abs_diff"),
            "n_changed": floor.get("n_changed"),
            "n_fields": floor.get("n_fields"),
        }
        print(
            f"[{entry}] noise floor: max_abs_diff={floor.get('max_abs_diff')} "
            f"changed_fields={floor.get('n_changed')}/{floor.get('n_fields')}"
        )

        for dotted, value, expect in PERTURBATIONS:
            base = OmegaConf.load(base_src)
            flat_present = OmegaConf.select(base, dotted) is not None
            if not flat_present:
                report["results"].setdefault(entry, {})[dotted] = {
                    "skipped": "key absent in this config",
                    "prior_class": expect,
                }
                continue
            before = OmegaConf.select(base, dotted)
            set_key(base, dotted, value)
            tag = f"{entry}__{dotted.replace('.', '_')}"
            path = CFG_DIR / f"{tag}.yaml"
            OmegaConf.save(base, path)
            got = run_one(entry, path, tag)
            cmp = compare(first, got)
            report["results"].setdefault(entry, {})[dotted] = {
                "prior_class": expect,
                "from": before if isinstance(before, (int, float, str, bool)) else str(before),
                "to": value,
                "run_ok": not got.get("failed", False),
                "failure": None if not got.get("failed") else got,
                "max_abs_diff": cmp.get("max_abs_diff"),
                "n_changed": cmp.get("n_changed"),
                "n_fields": cmp.get("n_fields"),
            }
            status = (
                "RUN-FAILED"
                if got.get("failed")
                else ("CHANGED" if (cmp.get("n_changed") or 0) > 0 else "same")
            )
            print(f"  [{entry}] {dotted:45s} {status:11s} max_diff={cmp.get('max_abs_diff')}")

    (AUDIT / "effectiveness.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"written: {AUDIT / 'effectiveness.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

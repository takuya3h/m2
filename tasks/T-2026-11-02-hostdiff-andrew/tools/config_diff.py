"""Task A-6 の後半: config.yaml の差を全キー出す（読むだけ）。

- ``--planned``: 学習の前。hydra で本契約の各 run の設定を組み、``run_ptower_search.py`` が足す
  契約の値（task_id・point・ft_lr・ft_weight_decay・ft_accum_steps・step）を足して、手本の config.yaml と
  キーごとに比べる。実行時にコードが足すキー（data・weights・transform など）は、手本に在って
  ここに無いキーとして出る（``runtime_only``）。実行の後に ``--actual`` で実物を比べる
- ``--actual <run_dir>...``: 実物の config.yaml を、対応する手本と比べる

許した違いの他の差は ``unallowed`` に出す。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run_hostdiff as rh  # noqa: E402

ROOT = rh.ROOT
sys.path.insert(0, str(ROOT / "scripts"))
OLD_ROOT = "/home/ubuntu/local/m2"
OLD_SCRATCH = "/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta"
PT = ROOT / "experiments/phase1/stage1_ptower_search"
DT = ROOT / "experiments/baselines/stage1_dtower_search/point00_dcoco_foldA_seed42"
DLSTA = "T-2026-10-22-tower-reselect-search-dlsta"

# 許した違い（SPEC §4）に当たるキー。値は比べず、分類だけ書く
ALLOWED_KEYS = {
    "task_id": "本契約の識別子",
    "contract_sha256": "本契約の識別子（契約の本文の要約値）",
    "cache": "出力と記録の置き場",
    "artifact_root": "出力と記録の置き場",
    "checkpoint": "出力と記録の置き場（fine-tune の checkpoint の経路）",
    "work": "出力と記録の置き場",
    "gpus": "GPU の番号",
    "seed": "seed",
    "repeat": "run の名前（seed 42 の一回目と二回目の区別）",
}


def flatten(value, prefix=""):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            out.update(flatten(item, f"{prefix}{key}."))
        return out
    return {prefix[:-1]: value}


def exemplar_configs():
    names = sorted(p.name for p in PT.iterdir() if p.name.endswith("_point00_seed42"))
    heads = [n for n in names if n.split("_")[3] not in ("001", "002")]
    out = {"finetune": PT / names[0] / "config.yaml", "extract": PT / names[1] / "config.yaml"}
    out.update({f"head{i:02d}": PT / n / "config.yaml" for i, n in enumerate(heads)})
    out["detector"] = DT / "config.yaml"
    return out


def compose(action, overrides):
    from hydra import compose as hydra_compose
    from hydra import initialize_config_dir
    from omegaconf import OmegaConf
    with initialize_config_dir(version_base=None, config_dir=str(ROOT / "configs")):
        cfg = hydra_compose(config_name="stage1_ptower_r3", overrides=[f"action={action}", *overrides])
    out = OmegaConf.to_container(cfg, resolve=True)
    point = json.loads(json.dumps(__import__("tower_search_common").load_point(0)))
    out.update({"task_id": rh.TASK, "point": point, "ft_lr": point["lr"],
                "ft_weight_decay": point["phase_weight_decay"], "ft_accum_steps": point["accum"],
                "step": "stage1_ptower_search"})
    return out


def planned(seed):
    work = rh.SCRATCH / "phase" / f"seed{seed}"
    common = rh.phase_common(work, seed)
    out = {"finetune": compose("finetune", common),
           "extract": compose("extract", [f"checkpoint={work}/runs/phase1/x/checkpoints/best.pth", *common])}
    from run_stage1_ptower_r3 import heads
    for index, recipe in enumerate(heads()):
        out[f"head{index:02d}"] = compose("train", [*common, *(f"{k}={v}" for k, v in recipe.items())])
    return out


def compare(mine, theirs):
    a, b = flatten(theirs), flatten(mine)
    rows, unallowed, runtime_only = [], [], []
    for key in sorted(set(a) | set(b)):
        top = key.split(".")[0]
        if key not in b:
            runtime_only.append(key)
            continue
        if key not in a:
            why = ALLOWED_KEYS.get(top)
            rows.append({"key": key, "exemplar": None, "this": b[key], "allowed": why})
            if why is None:
                unallowed.append(key)
            continue
        if a[key] == b[key]:
            continue
        why = ALLOWED_KEYS.get(top)
        if why is None and isinstance(a[key], str) and a[key].replace(OLD_ROOT, str(ROOT)).replace(
                OLD_SCRATCH, str(rh.SCRATCH)) == b[key]:
            why = "経路"
        rows.append({"key": key, "exemplar": a[key], "this": b[key], "allowed": why})
        if why is None:
            unallowed.append(key)
    return rows, unallowed, runtime_only


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--actual", nargs="*", help="key=run_dir の組（key は finetune・extract・head00〜09・detector）")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    ex = exemplar_configs()
    if args.actual:
        mine = {k: yaml.safe_load(Path(v, "config.yaml").read_text())
                for k, v in (pair.split("=", 1) for pair in args.actual)}
    else:
        mine = planned(args.seed)
    if args.self_test:
        theirs = yaml.safe_load(ex["finetune"].read_text())
        theirs["ft_patience"] = 5
        rows, unallowed, _ = compare(mine["finetune"], theirs)
        print(json.dumps({"self_test_unallowed": unallowed}, ensure_ascii=False))
        return
    report = {}
    for key, cfg in mine.items():
        rows, unallowed, runtime_only = compare(cfg, yaml.safe_load(ex[key].read_text()))
        report[key] = {"exemplar": str(ex[key]), "diff": rows, "unallowed": unallowed,
                       "runtime_only": runtime_only}
    print(json.dumps({"unallowed_total": sum(len(v["unallowed"]) for v in report.values()),
                      "runs": report}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()

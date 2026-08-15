"""Phase C — 分母を構成する run の条件が同一であることを照合する。

足す本数は 0 になったため「足した run の照合」は対象が無い。**空振りにしない**ために、
分母そのものを構成する既存 17 本に同じ照合をかける。Phase D で分母を締め直す土台になる。

**陽性対照を取る。** 構成キーを一つだけ変えた偽の条件が「一致しない」と出ることを
確かめなければ、照合器が常に True を返していても気づけない。
"""

import csv
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from egosurgery.utils.eval_recipe import recipes_match  # noqa: E402

EXPERIMENT_ID = "phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42"
EXPECTED_SPLIT = {"split_train_images": 9657, "split_val_images": 1515, "split_test_images": 4265}
EXPECTED_BACKBONE = "relation_detr_resnet50_frozen_seed42"


def main() -> None:
    rows = [
        r
        for r in csv.DictReader((ROOT / "runindex" / "index.csv").open(encoding="utf-8"))
        if r["experiment_id"] == EXPERIMENT_ID
    ]
    recipes = {}
    for r in rows:
        m = json.loads((ROOT / r["path"] / "metrics.json").read_text())
        recipes[Path(r["path"]).name] = m["eval_recipe"]

    names = sorted(recipes)
    reference = recipes[names[0]]

    matches = {n: recipes_match(reference, recipes[n]) for n in names}

    # 陽性対照。構成キーを一つだけ変える。**一致しないと出なければ照合器が空振りである。**
    controls = []
    for key, new in (
        ("inference_protocol", "offline_noncausal"),
        ("jaccard_mode", "loose"),
        ("temporal_head", "mstcn"),
        ("backbone", "relation_detr_resnet50_frozen_seed123"),
    ):
        fake = deepcopy(reference)
        fake["test_cfg"][key] = new
        controls.append(
            {"changed_key": key, "to": new, "matches": recipes_match(reference, fake)}
        )

    split_ok = {
        n: all(recipes[n].get(k) == v for k, v in EXPECTED_SPLIT.items()) for n in names
    }
    backbone_ok = {n: recipes[n]["test_cfg"].get("backbone") == EXPECTED_BACKBONE for n in names}

    result = {
        "experiment_id": EXPERIMENT_ID,
        "runs_checked": len(names),
        "reference_run": names[0],
        "all_recipes_match": all(matches.values()),
        "mismatched_runs": [n for n, ok in matches.items() if not ok],
        "split_expected": EXPECTED_SPLIT,
        "all_splits_match": all(split_ok.values()),
        "split_mismatched_runs": [n for n, ok in split_ok.items() if not ok],
        "backbone_expected": EXPECTED_BACKBONE,
        "all_backbone_match": all(backbone_ok.values()),
        "backbone_mismatched_runs": [n for n, ok in backbone_ok.items() if not ok],
        "positive_controls": controls,
        "positive_controls_all_rejected": all(not c["matches"] for c in controls),
        "added_runs_checked": 0,
        "added_runs_note": "足す本数が 0 のため、足した run の照合は対象が無い",
    }
    (AUDIT / "recipe_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"記録: {AUDIT / 'recipe_check.json'}")
    print(f"照合した run = {result['runs_checked']}（基準 {result['reference_run']}）")
    print(f"  評価条件が全件一致 : {result['all_recipes_match']}  不一致 {result['mismatched_runs']}")
    print(f"  分割が全件一致     : {result['all_splits_match']}  不一致 {result['split_mismatched_runs']}")
    print(f"  凍結源が全件一致   : {result['all_backbone_match']}  不一致 {result['backbone_mismatched_runs']}")
    print()
    print("陽性対照（構成キーを一つだけ変えた偽の条件。すべて『一致しない』が正しい）")
    for c in controls:
        mark = "一致しない" if not c["matches"] else "★一致してしまう★"
        print(f"  {mark:<18} {c['changed_key']} -> {c['to']}")
    print()
    print(f"陽性対照がすべて棄却された: {result['positive_controls_all_rejected']}")


if __name__ == "__main__":
    main()

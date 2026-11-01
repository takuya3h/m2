"""案 B の固定の長さの run の後処理（非公式 T-2026-10-31-grasp-pilot-probe、Task D-7）。

scripts/stage2pilot/pd_fix_finalize.py と同じ手順（結果が最後の epoch の状態であることを確かめ、val の結果の予測から
overall mAP・クラス別 AP・標的群 AP・陰性対照群 AP・動画ごとの mAP を出す）に、epoch ごとの界面の重みの大きさを足す。
grasppilot_metrics.json と notes.md を run の作業フォルダに書く。

    python scripts/grasppilot/pd_grasp_finalize.py <run の作業フォルダ> <腕>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

TASK = os.environ.get("GP_TASK") or "T-2026-10-31-grasp-pilot-probe"  # 既定は一本目。run_pd_grasp.sh の GP_TASK で上書き
VAL_ANN = Path(os.environ.get("EGO_ANN_DIR") or C.DET_ANN_A) / "instances_val.json"


def f6(x):
    return "None" if x is None else f"{x:.6f}"


def main():
    work, arm = Path(sys.argv[1]), sys.argv[2]
    res = json.loads((work / "t1b_result.json").read_text())
    ok = (res.get("result_selection") == "final_epoch" and res["best_epoch"] == res["final_epoch"]
          == res["epochs"] - 1 and res["mAP"] == res["final_mAP"])
    if not ok:
        raise SystemExit(f"結果が最後の epoch の状態ではない: {res.get('result_selection')} {res['best_epoch']} {res['final_epoch']}")
    tag = "ctrl" if res.get("zero_ctx") else "inj"
    ids = json.loads((work / "logs/eval_meta_val.json").read_text())["image_ids"]
    met = M.summary(VAL_ANN, M.load_results(work / f"predictions/val_{tag}_best.json.gz"), ids)
    init = M.summary(VAL_ANN, M.load_results(work / f"predictions/val_{tag}_ep-1.json.gz"), ids)
    met.update({"task_id": TASK, "unofficial": True, "type": "B-map", "arm": arm,
                "result_selection": res.get("result_selection"), "result_epoch": res["best_epoch"],
                "eval_detection_mAP": res["mAP"], "diff_vs_eval_detection_mAP": met["AP"] - res["mAP"],
                "init": init["AP"], "init_target_AP": init["target_AP"], "init_control_AP": init["control_AP"],
                "per_epoch_mAP": {e["epoch"]: e["mAP"] for e in res["per_epoch_eval"]},
                "iface_weight_by_epoch": {e["epoch"]: e.get("gates") for e in res["per_epoch_eval"]},
                "frozen_unchanged": (res["frozen_digest_before"] == res["frozen_digest_after"]
                                     if res.get("frozen_digest_after") else None)})
    C.write_json(work / "grasppilot_metrics.json", met)
    (work / "notes.md").write_text(
        f"# 非公式（{TASK}） 案 B（把持の地図を C5 に足す型） {arm} seed {res['seed']}\n\n"
        f"受け取り手は D*-COCO 折り A seed 42 の検出塔（学習範囲 {res['trainable']}、界面だけを学ぶ W1）。"
        f"{res['epochs']} epoch 学習し途中で止めない。結果は {res['epochs']} epoch 目（epoch {res['best_epoch']}）の状態で、"
        "最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。\n\n"
        f"- overall mAP {f6(met['AP'])}、標的群 AP {f6(met['target_AP'])}、陰性対照群 AP {f6(met['control_AP'])}\n"
        f"- 学習前 mAP {f6(init['AP'])}\n"
        f"- epoch ごとの val mAP（−1 は学習前）: {met['per_epoch_mAP']}\n"
        f"- epoch ごとの界面の重み: {met['iface_weight_by_epoch']}\n"
        f"- 動画ごとの mAP: {met['per_video_AP']}\n"
        f"- 凍結部の要約値の前後一致: {met['frozen_unchanged']}\n")
    print(f"[pd_grasp_finalize] {work.name} AP={f6(met['AP'])} target={f6(met['target_AP'])} control={f6(met['control_AP'])}")


if __name__ == "__main__":
    main()

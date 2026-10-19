"""PD の新しい型の固定の長さの run の後処理（非公式 T-2026-10-19-stage2-pilot-four-new-types、Task E）。

直しの契約の pd_fix_finalize.py と同じ処理（結果が最後の epoch の状態であることを確かめ、overall mAP・クラス別 AP・標的群 AP・
陰性対照群 AP・動画ごとの mAP を出す）に、epoch ごとのゲートの値（decoder-xattn の層ごとの tanh(α_l)、extra-queries のスコアの定数）を足して
stage2four_metrics.json と notes.md を書く。

    python scripts/stage2pilot/pd_four_finalize.py <run の作業フォルダ> <型> <腕>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

TASK_ID = "T-2026-10-19-stage2-pilot-four-new-types"
VAL_ANN = Path(os.environ.get("EGO_ANN_DIR") or C.DET_ANN_A) / "instances_val.json"
TYPE_NAME = {"DX": "decoder-xattn", "EQ": "extra-queries"}


def f6(x):
    return "None" if x is None else f"{x:.6f}"


def main():
    work, typ, arm = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    res = json.loads((work / "t1b_result.json").read_text())
    ok = (res.get("result_selection") == "final_epoch" and res["best_epoch"] == res["final_epoch"]
          == res["epochs"] - 1 and res["mAP"] == res["final_mAP"])
    if not ok:
        raise SystemExit(f"結果が最後の epoch の状態ではない: selection={res.get('result_selection')} "
                         f"best={res['best_epoch']} final={res['final_epoch']} epochs={res['epochs']}")
    tag = "ctrl" if res.get("zero_ctx") else "inj"
    ids = json.loads((work / "logs/eval_meta_val.json").read_text())["image_ids"]
    met = M.summary(VAL_ANN, M.load_results(work / f"predictions/val_{tag}_best.json.gz"), ids)
    init = M.summary(VAL_ANN, M.load_results(work / f"predictions/val_{tag}_ep-1.json.gz"), ids)
    gates = {e["epoch"]: e.get("gates") for e in res["per_epoch_eval"]}
    met.update({"task_id": TASK_ID, "type": typ, "type_name": TYPE_NAME[typ], "arm": arm,
                "result_selection": res.get("result_selection"), "result_epoch": res["best_epoch"],
                "eval_detection_mAP": res["mAP"], "diff_vs_eval_detection_mAP": met["AP"] - res["mAP"],
                "init": init["AP"], "init_target_AP": init["target_AP"], "init_control_AP": init["control_AP"],
                "per_epoch_mAP": {e["epoch"]: e["mAP"] for e in res["per_epoch_eval"]}, "gates_by_epoch": gates,
                "frozen_unchanged": res["frozen_digest_before"] == res["frozen_digest_after"]})
    C.write_json(work / "stage2four_metrics.json", met)
    (work / "notes.md").write_text(
        f"# 非公式（{TASK_ID}） PD {TYPE_NAME[typ]}（{typ}） {arm} seed {res['seed']}\n\n"
        f"受け取り手は D*-COCO 折り A seed 42 の検出塔（凍結。学習範囲 W1 = 界面だけ、--trainable {res['trainable']}）。"
        f"{res['epochs']} epoch 学習し途中で止めない。結果は {res['epochs']} epoch 目（epoch {res['best_epoch']}）の状態で、"
        "最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。\n\n"
        f"- overall mAP {f6(met['AP'])}、標的群 AP {f6(met['target_AP'])}、陰性対照群 AP {f6(met['control_AP'])}"
        f"（群に欠けたクラス: 標的群 {met['target_missing']}、陰性対照群 {met['control_missing']}）\n"
        f"- 学習前 mAP {f6(init['AP'])}\n"
        f"- epoch ごとの val mAP（epoch は 0 始まり、−1 は学習前）: {met['per_epoch_mAP']}\n"
        f"- epoch ごとのゲート: {gates}\n"
        f"- 動画ごとの mAP: {met['per_video_AP']}\n"
        f"- 凍結部の要約値の前後一致: {met['frozen_unchanged']}\n")
    print(f"[pd_four_finalize] {work.name} AP={f6(met['AP'])} target={f6(met['target_AP'])} "
          f"control={f6(met['control_AP'])} result_epoch={res['best_epoch']} diff={met['diff_vs_eval_detection_mAP']:.2e}")


if __name__ == "__main__":
    main()

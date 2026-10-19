"""PD の固定の長さの run の後処理（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle、Task C-1 / E）。

run の t1b_result.json と、val の結果の予測（train_t1b.py --fixed-epochs では最後の epoch の状態）から、
overall mAP・クラス別 AP・標的群 AP・陰性対照群 AP・動画ごとの mAP を出して stage2fix_metrics.json に書き、notes.md を書く。
学習した run では、結果が最後の epoch の状態であること（result_selection=final_epoch、best_epoch = final_epoch = epochs − 1）を
確かめ、食い違えば止まる。評価した画像は logs/eval_meta_val.json の image_ids（試走は 20 枚）。

    python scripts/stage2pilot/pd_fix_finalize.py <run の作業フォルダ> <型> <腕>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

VAL_ANN = C.DET_ANN_A / "instances_val.json"


def f6(x):
    """群の AP は、試走（val 20 枚）では群のクラスが一つも出現せず None になり得る。"""
    return "None" if x is None else f"{x:.6f}"


def main():
    work, typ, arm = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    res = json.loads((work / "t1b_result.json").read_text())
    sp = yaml.safe_load((work / "config.yaml").read_text())["stage2pilot"]
    eval_only = bool(sp.get("eval_only"))
    if not eval_only:
        ok = (res.get("result_selection") == "final_epoch" and res["best_epoch"] == res["final_epoch"]
              == res["epochs"] - 1 and res["mAP"] == res["final_mAP"])
        if not ok:
            raise SystemExit(f"結果が最後の epoch の状態ではない: selection={res.get('result_selection')} "
                             f"best={res['best_epoch']} final={res['final_epoch']} epochs={res['epochs']}")
    tag = "ctrl" if res.get("zero_ctx") else "inj"
    ids = json.loads((work / "logs/eval_meta_val.json").read_text())["image_ids"]
    met = M.summary(VAL_ANN, M.load_results(work / f"predictions/val_{tag}_best.json.gz"), ids)
    init = M.summary(VAL_ANN, M.load_results(work / f"predictions/val_{tag}_ep-1.json.gz"), ids)
    met.update({"task_id": C.FIX_TASK_ID, "type": typ, "arm": arm, "result_selection": res.get("result_selection"),
                "result_epoch": res["best_epoch"], "eval_only": eval_only, "eval_detection_mAP": res["mAP"],
                "diff_vs_eval_detection_mAP": met["AP"] - res["mAP"], "init": init["AP"],
                "init_target_AP": init["target_AP"], "init_control_AP": init["control_AP"],
                "per_epoch_mAP": {e["epoch"]: e["mAP"] for e in res["per_epoch_eval"]},
                "frozen_unchanged": (res["frozen_digest_before"] == res["frozen_digest_after"]
                                     if res.get("frozen_digest_after") else None)})
    C.write_json(work / "stage2fix_metrics.json", met)
    how = ("学習しない（評価だけ）。" if eval_only else
           f"{res['epochs']} epoch 学習し途中で止めない。結果（metrics.json、per_class_ap.json、stage2fix_metrics.json の"
           f"群と動画ごとの値、val の best の予測、best_t1b.pth）は {res['epochs']} epoch 目（epoch {res['best_epoch']}）の状態で、"
           "最良の回を選ばない。")
    (work / "notes.md").write_text(
        f"# 非公式（{C.FIX_TASK_ID}） PD {typ} {arm} seed {res['seed']}\n\n"
        f"受け取り手は D*-COCO 折り A seed 42 の検出塔（学習範囲 {res['trainable']}、凍結部は学習しない）。{how}"
        "val（動画 09・10）だけで評価した。test は通していない。\n\n"
        f"- overall mAP {f6(met['AP'])}、標的群 AP {f6(met['target_AP'])}、陰性対照群 AP {f6(met['control_AP'])}"
        f"（群に欠けたクラス: 標的群 {met['target_missing']}、陰性対照群 {met['control_missing']}）\n"
        f"- 学習前 mAP {f6(init['AP'])}\n"
        f"- epoch ごとの val mAP（epoch は 0 始まり、−1 は学習前）: {met['per_epoch_mAP']}\n"
        f"- 動画ごとの mAP: {met['per_video_AP']}\n"
        f"- 凍結部の要約値の前後一致: {met['frozen_unchanged']}\n")
    print(f"[pd_fix_finalize] {work.name} AP={f6(met['AP'])} target={f6(met['target_AP'])} "
          f"control={f6(met['control_AP'])} result_epoch={res['best_epoch']} diff={met['diff_vs_eval_detection_mAP']:.2e}")


if __name__ == "__main__":
    main()

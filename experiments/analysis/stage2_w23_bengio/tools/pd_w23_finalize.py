"""PD の W2・W3 の run の後処理（非公式 T-2026-11-01-stage2-w23-bengio、Task D）。

直しの契約の ``scripts/stage2pilot/pd_fix_finalize.py`` と四本目の ``pd_four_finalize.py`` と同じ計算（結果が最後の epoch の
状態であることを確かめ、overall mAP・AP50・クラス別 AP・標的群 AP・陰性対照群 AP・動画ごとの mAP、学習前の値、epoch ごとの
val mAP、ゲートの値）を ``w23_metrics.json`` に書き、notes.md を書く。足したもの:

- 学習前（epoch −1）の予測と塔単独の予測（Task B-2 の ``$S/b/plain_val_preds_seed42.json.gz``）の出力の差の最大（run ごとの恒等性）
- 予測（``predictions/*.json.gz``）を版管理と同期の外（第 5 引数）へ移し、経路と sha256 を ``predictions_moved.json`` に残す
- ``code_sha256.txt``（台本・学習・確定の道具・界面の構成の sha256）

    python pd_w23_finalize.py <run の作業フォルダ> <型> <腕> <W> <予測の移し先>
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

TASK_ID = "T-2026-11-01-stage2-w23-bengio"
S = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK_ID
PLAIN = S / "b/plain_val_preds_seed42.json.gz"
VAL_ANN = Path(os.environ.get("EGO_ANN_DIR") or C.DET_ANN_A) / "instances_val.json"
TYPE_NAME = {"P2L": "P2L", "P3": "P3", "EQ": "extra-queries", "P1": "P1 FiLM"}
CODE_FILES = ["scripts/w23/run_pd_w23_bengio.sh", "scripts/train_t1b.py", "scripts/stage2pilot/pd_model.py",
              "experiments/analysis/stage2_w23_bengio/tools/pd_w23_finalize.py"]


def f6(x):
    return "None" if x is None else f"{x:.6f}"


def sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    work, typ, arm, scope, dest = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], Path(sys.argv[5])
    res = json.loads((work / "t1b_result.json").read_text())
    sp = yaml.safe_load((work / "config.yaml").read_text())["stage2pilot"]
    ok = (res.get("result_selection") == "final_epoch" and res["best_epoch"] == res["final_epoch"]
          == res["epochs"] - 1 and res["mAP"] == res["final_mAP"])
    if not ok:
        raise SystemExit(f"結果が最後の epoch の状態ではない: selection={res.get('result_selection')} "
                         f"best={res['best_epoch']} final={res['final_epoch']} epochs={res['epochs']}")
    want = {"W2": "w2", "W3": "all"}[scope]
    if res["trainable"] != want:
        raise SystemExit(f"学習範囲が違う: {res['trainable']} != {want}")
    tag = "ctrl" if res.get("zero_ctx") else "inj"
    ids = json.loads((work / "logs/eval_meta_val.json").read_text())["image_ids"]
    best_p = work / f"predictions/val_{tag}_best.json.gz"
    init_p = work / f"predictions/val_{tag}_ep-1.json.gz"
    best_r, init_r = M.load_results(best_p), M.load_results(init_p)
    met = M.summary(VAL_ANN, best_r, ids)
    init = M.summary(VAL_ANN, init_r, ids)
    gates = {e["epoch"]: e.get("gates") for e in res["per_epoch_eval"]}
    smoke = bool(sp.get("smoke")) or work.name.endswith("_smoke")
    identity = M.max_output_diff(init_r, M.load_results(PLAIN)) if not smoke else None
    met.update({"task_id": TASK_ID, "unofficial": f"非公式（{TASK_ID}）", "type": typ, "type_name": TYPE_NAME[typ],
                "arm": arm, "scope": scope, "trainable": res["trainable"],
                "result_selection": res.get("result_selection"), "result_epoch": res["best_epoch"],
                "eval_detection_mAP": res["mAP"], "diff_vs_eval_detection_mAP": met["AP"] - res["mAP"],
                "init": init["AP"], "init_target_AP": init["target_AP"], "init_control_AP": init["control_AP"],
                "init_vs_tower_alone": identity, "tower_alone_preds": str(PLAIN),
                "per_epoch_mAP": {e["epoch"]: e["mAP"] for e in res["per_epoch_eval"]}, "gates_by_epoch": gates,
                "frozen_unchanged": (res["frozen_digest_before"] == res["frozen_digest_after"]
                                     if res.get("frozen_digest_after") else None),
                "host": (work / "server.txt").read_text().strip() if (work / "server.txt").exists() else None})
    C.write_json(work / "w23_metrics.json", met)
    (work / "code_sha256.txt").write_text("".join(f"{sha256(ROOT / f)}  {f}\n" for f in CODE_FILES + [sp.get("model_cfg") or ""]
                                                  if f and (ROOT / f).is_file()))
    dest.mkdir(parents=True, exist_ok=True)
    moved = []
    for p in sorted((work / "predictions").glob("*.json.gz")):
        digest = sha256(p)
        shutil.move(str(p), dest / p.name)
        moved.append({"name": p.name, "moved_to": str(dest / p.name), "sha256": digest})
    C.write_json(work / "predictions_moved.json", moved)
    (work / "notes.md").write_text(
        f"# 非公式（{TASK_ID}） PD {TYPE_NAME[typ]}（{typ}） {scope} {arm} seed {res['seed']}\n\n"
        f"受け取り手は D*-COCO 折り A seed 42 の検出塔。学習範囲 {scope}（--trainable {res['trainable']}。"
        f"{'界面 ＋ decoder の最終層とその層のクラスと box の頭' if scope == 'W2' else '界面 ＋ 設定の凍結以外の検出器の全体'}）。"
        f"{res['epochs']} epoch 学習し途中で止めない。結果は {res['epochs']} epoch 目（epoch {res['best_epoch']}）の状態で、"
        "最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。\n\n"
        f"- overall mAP {f6(met['AP'])}、標的群 AP {f6(met['target_AP'])}、陰性対照群 AP {f6(met['control_AP'])}、AP50 {f6(met['AP50'])}"
        f"（群に欠けたクラス: 標的群 {met['target_missing']}、陰性対照群 {met['control_missing']}）\n"
        f"- 学習前 mAP {f6(init['AP'])}、学習前の出力と塔単独の差: {identity}\n"
        f"- epoch ごとの val mAP（epoch は 0 始まり、−1 は学習前）: {met['per_epoch_mAP']}\n"
        f"- epoch ごとのゲート: {gates}\n"
        f"- 動画ごとの mAP: {met['per_video_AP']}\n"
        f"- 凍結部の要約値の前後一致: {met['frozen_unchanged']}\n"
        f"- 予測は {dest} へ移した（predictions_moved.json）\n")
    print(f"[pd_w23_finalize] {work.name} AP={f6(met['AP'])} target={f6(met['target_AP'])} "
          f"control={f6(met['control_AP'])} result_epoch={res['best_epoch']} init_diff={identity}")


if __name__ == "__main__":
    main()

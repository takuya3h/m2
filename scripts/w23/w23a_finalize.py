"""W2・W3 の run の後処理（非公式 T-2026-11-01-stage2-w23-andrew、Task D-1）。

前の契約の pd_four_finalize.py・pd_grasp_finalize.py と同じ処理（結果が最後の epoch の状態であることを確かめ、overall mAP・AP50・
クラス別 AP・標的群 AP・陰性対照群 AP・動画ごとの mAP を出す）に、次を足して w23a_metrics.json と notes.md を書く。
  - epoch ごとの val（--save-predictions-all が残した各 epoch の予測から同じ集計）
  - 学習前の予測と塔単独の予測（Task B-2）の出力の差の最大値（学習の経路の中での恒等性）
  - 界面の重みの大きさ（epoch ごと。ゲートを持つ型はゲート）と、受け取り手の学んだパラメータの動いた量（最後の状態 − 検出塔）
  - 学習と評価に通した動画の集合（train の注釈と val の評価の画像）
書くのは run の作業フォルダの中だけ。

    python scripts/w23/w23a_finalize.py <run の作業フォルダ> <型> <W> <腕>
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

TASK_ID = "T-2026-11-01-stage2-w23-andrew"
S = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK_ID
REF_PREDS = S / "identity/plain_val_preds.json.gz"
TYPE_NAME = {"P1": "FiLM（P1）", "DX": "decoder-xattn", "B": "案 B（把持の地図を C5 に足す型）"}


def f6(x):
    return "None" if x is None else f"{x:.6f}"


def short(m: dict) -> dict:
    return {k: m[k] for k in ("AP", "AP50", "target_AP", "control_AP", "per_video_AP", "target_missing", "control_missing")}


def videos_of_ann(path: Path, img_ids=None) -> list[str]:
    d = json.loads(path.read_text())
    keep = None if img_ids is None else set(img_ids)
    return sorted({C.video_of(Path(im["file_name"]).stem) for im in d["images"] if keep is None or im["id"] in keep})


def receiver_motion(ckpt_path: Path, det_ckpt: Path) -> dict:
    st = torch.load(ckpt_path, map_location="cpu")["model"]
    base = torch.load(det_ckpt, map_location="cpu")
    base = base["model"] if isinstance(base, dict) and "model" in base else base
    iface = {k: float(v.float().norm()) for k, v in st.items() if k.startswith("phase")}
    num, den, n_el, n_keys, missing = 0.0, 0.0, 0, 0, []
    for k, v in st.items():
        if k.startswith("phase"):
            continue
        if k not in base:
            missing.append(k)
            continue
        d = (v.float() - base[k].float())
        num += float(d.pow(2).sum())
        den += float(base[k].float().pow(2).sum())
        n_el += v.numel()
        n_keys += 1
    return {"iface_l2_by_param": iface, "receiver_keys": n_keys, "receiver_elements": n_el,
            "receiver_delta_l2": num ** 0.5, "receiver_l2": den ** 0.5,
            "receiver_rel_delta": (num ** 0.5) / (den ** 0.5) if den else None, "keys_not_in_det_ckpt": missing,
            "ckpt": str(ckpt_path), "ckpt_sha256": C.sha256(ckpt_path)}


def main():
    work, typ, w, arm = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    res = json.loads((work / "t1b_result.json").read_text())
    cfg = yaml.safe_load((work / "config.yaml").read_text())
    ok = (res.get("result_selection") == "final_epoch" and res["best_epoch"] == res["final_epoch"]
          == res["epochs"] - 1 and res["mAP"] == res["final_mAP"])
    if not ok:
        raise SystemExit(f"結果が最後の epoch の状態ではない: selection={res.get('result_selection')} "
                         f"best={res['best_epoch']} final={res['final_epoch']} epochs={res['epochs']}")
    ann_dir = Path(cfg["stage2pilot"]["ann_dir"])
    val_ann = ann_dir / "instances_val.json"
    tag = "ctrl" if res.get("zero_ctx") else "inj"
    ids = json.loads((work / "logs/eval_meta_val.json").read_text())["image_ids"]
    pred = work / "predictions"
    met = M.summary(val_ann, M.load_results(pred / f"val_{tag}_best.json.gz"), ids)
    init_results = M.load_results(pred / f"val_{tag}_ep-1.json.gz")
    init = M.summary(val_ann, init_results, ids)
    per_epoch = {-1: short(init)}
    for e in range(res["epochs"]):
        per_epoch[e] = short(M.summary(val_ann, M.load_results(pred / f"val_{tag}_ep{e}.json.gz"), ids))
    last_matches_best = per_epoch[res["epochs"] - 1]["AP"] == met["AP"]
    gates = {e["epoch"]: e.get("gates") for e in res["per_epoch_eval"]}
    motion = receiver_motion(Path(cfg["stage2pilot"]["ckpt_dir"]) / "best_t1b.pth", Path(cfg["stage2pilot"]["det_ckpt"]))
    vids = {"train": videos_of_ann(ann_dir / "instances_train.json"), "val_evaluated": videos_of_ann(val_ann, ids)}
    vids["test_overlap"] = sorted((set(vids["train"]) | set(vids["val_evaluated"])) & C.TEST_VIDEOS)
    start = datetime.strptime((work / "start.txt").read_text().strip(), "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)
    met.update({"task_id": TASK_ID, "unofficial": True, "type": typ, "type_name": TYPE_NAME[typ], "w": w, "arm": arm,
                "trainable_arg": res["trainable"], "result_selection": res.get("result_selection"),
                "result_epoch": res["best_epoch"], "eval_detection_mAP": res["mAP"],
                "diff_vs_eval_detection_mAP": met["AP"] - res["mAP"], "init": short(init),
                "init_diff_vs_tower": M.max_output_diff(init_results, M.load_results(REF_PREDS)),
                "per_epoch": per_epoch, "last_epoch_matches_best_preds": last_matches_best,
                "per_epoch_eval_detection_mAP": {e["epoch"]: e["mAP"] for e in res["per_epoch_eval"]},
                "gates_by_epoch": gates, "receiver_motion": motion,
                "total_trainable": cfg["stage2pilot"]["total_trainable"], "phase_params": cfg["stage2pilot"]["phase_params"],
                "frozen_unchanged": res["frozen_digest_before"] == res["frozen_digest_after"],
                "videos": vids, "server": (work / "server.txt").read_text().strip(),
                "seconds_to_finalize": (datetime.now(timezone.utc) - start).total_seconds()})
    C.write_json(work / "w23a_metrics.json", met)
    (work / "notes.md").write_text(
        f"# 非公式（{TASK_ID}） PD {TYPE_NAME[typ]} {w} {arm} seed {res['seed']}\n\n"
        "**非公式の測定。関門の判定と設計の判断に使わない。**\n\n"
        f"受け取り手は D*-COCO 折り A seed 42 の検出塔。学習範囲 {w}（--trainable {res['trainable']}、"
        f"学ぶ要素 {cfg['stage2pilot']['total_trainable']}、うち界面 {cfg['stage2pilot']['phase_params']}）。"
        f"{res['epochs']} epoch 学習し途中で止めない。結果は {res['epochs']} epoch 目（epoch {res['best_epoch']}）の状態で、"
        "最良の回を選ばない。val（動画 09・10）だけで評価した。test は通していない。\n\n"
        f"- overall mAP {f6(met['AP'])}、AP50 {f6(met['AP50'])}、標的群 AP {f6(met['target_AP'])}、陰性対照群 AP {f6(met['control_AP'])}\n"
        f"- 学習前 mAP {f6(init['AP'])}、学習前の塔単独との出力の差 {met['init_diff_vs_tower']}\n"
        f"- epoch ごとの val（−1 は学習前）: { {e: (round(v['AP'], 6), round(v['target_AP'], 6)) for e, v in per_epoch.items()} }\n"
        f"- epoch ごとのゲート・界面の重み: {gates}\n"
        f"- 受け取り手の動いた量（L2、相対）: {motion['receiver_delta_l2']:.6g}、{motion['receiver_rel_delta']}\n"
        f"- 動画ごとの mAP: {met['per_video_AP']}\n"
        f"- 通した動画: train {vids['train']}、val {vids['val_evaluated']}、test との共通 {vids['test_overlap']}\n"
        f"- 凍結部の要約値の前後一致: {met['frozen_unchanged']}\n")
    print(f"[w23a_finalize] {work.name} AP={f6(met['AP'])} target={f6(met['target_AP'])} control={f6(met['control_AP'])} "
          f"init_diff={met['init_diff_vs_tower']} rel_delta={motion['receiver_rel_delta']}")


if __name__ == "__main__":
    main()

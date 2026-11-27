"""V→T run の後処理集計: 全 epoch の overall mAP・標的群 AP・陰性対照群 AP・動画別・零初期化層 L2・動画集合を保存する。"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

TASK_ID = "T-2026-11-26-vlm-caption-signal-pilot"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / "vlm_caption_signal_pilot"
REF_PREDS = STORE / "identity/plain_val_preds.json.gz"
TYPE_NAME = {"P1": "FiLM（P1）", "P2L": "clsbias_lin（P2L）"}


def short(m: dict) -> dict:
    return {k: m[k] for k in ("AP", "AP50", "target_AP", "control_AP", "per_class_ap", "per_video_AP",
                              "target_missing", "control_missing")}


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
    return {
        "iface_l2_by_param": iface, "receiver_keys": n_keys, "receiver_elements": n_el,
        "receiver_delta_l2": num ** 0.5, "receiver_l2": den ** 0.5,
        "receiver_rel_delta": (num ** 0.5) / (den ** 0.5) if den else None,
        "keys_not_in_det_ckpt": missing,
        "ckpt": str(ckpt_path), "ckpt_sha256": C.sha256(ckpt_path),
    }


def main():
    work, typ, w, arm = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    res = json.loads((work / "t1b_result.json").read_text())
    cfg = yaml.safe_load((work / "config.yaml").read_text())
    ok = (res.get("result_selection") == "final_epoch"
          and res["best_epoch"] == res["final_epoch"] == res["epochs"] - 1
          and res["mAP"] == res["final_mAP"])
    if not ok:
        raise SystemExit(f"結果が最後の epoch ではない: {res.get('result_selection')} {res['best_epoch']} {res['epochs']}")

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

    wrap_log = json.loads((work / "v2t_wrap.json").read_text()) if (work / "v2t_wrap.json").exists() else {}
    iface_by_ep = {}
    for sn in wrap_log.get("snapshots", []):
        if sn["tag"].startswith("eval_"):
            k = int(sn["tag"].split("_")[1])  # 0=init, 1=after ep0(1-indexed ep1), ..., 4=ep4
            iface_by_ep[k] = sn.get("iface_last")

    motion = receiver_motion(Path(cfg["stage2pilot"]["ckpt_dir"]) / "best_t1b.pth",
                             Path(cfg["stage2pilot"]["det_ckpt"]))
    vids = {"train": videos_of_ann(ann_dir / "instances_train.json"),
            "val_evaluated": videos_of_ann(val_ann, ids)}
    vids["test_overlap"] = sorted((set(vids["train"]) | set(vids["val_evaluated"])) & C.TEST_VIDEOS)
    start = datetime.strptime((work / "start.txt").read_text().strip(), "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=timezone.utc)

    # 1-indexed epoch (4, 8, 12, 16) のビュー
    by_ep1 = {str(e + 1): per_epoch[e] for e in range(res["epochs"])}
    met.update({
        "task_id": TASK_ID, "unofficial": True, "type": typ, "type_name": TYPE_NAME[typ],
        "w": w, "arm": arm, "trainable_arg": res["trainable"],
        "result_selection": res.get("result_selection"), "result_epoch": res["best_epoch"],
        "eval_detection_mAP": res["mAP"], "diff_vs_eval_detection_mAP": met["AP"] - res["mAP"],
        "init": short(init),
        "init_diff_vs_tower": M.max_output_diff(init_results, M.load_results(REF_PREDS)),
        "per_epoch_0idx": {str(k): v for k, v in per_epoch.items()},
        "per_epoch_1idx": by_ep1,
        "iface_last_by_ep1": {str(k): v for k, v in iface_by_ep.items()},
        "last_epoch_matches_best_preds": last_matches_best,
        "receiver_motion": motion,
        "total_trainable": cfg["stage2pilot"]["total_trainable"],
        "phase_params": cfg["stage2pilot"]["phase_params"],
        "frozen_unchanged": res["frozen_digest_before"] == res["frozen_digest_after"],
        "videos": vids,
        "server": (work / "server.txt").read_text().strip(),
        "seconds_to_finalize": (datetime.now(timezone.utc) - start).total_seconds(),
    })
    C.write_json(work / "v2t_metrics.json", met)
    ep4 = by_ep1.get("4", {})
    print(f"[v2t_finalize] {work.name} ep4(AP={ep4.get('AP', 0):.6f} target={ep4.get('target_AP', 0):.6f}) "
          f"final(AP={met['AP']:.6f} target={met['target_AP']:.6f}) init_diff={met['init_diff_vs_tower']}")


if __name__ == "__main__":
    main()

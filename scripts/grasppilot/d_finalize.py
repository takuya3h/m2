"""案 D の腕の後処理（非公式 T-2026-11-01-grasp-pilot-d、Task C-3・D-4・E）。

.venv-relation-detr で、EGO_BODY に重ねの BODY を置いて回す。

1. 最後の状態（``checkpoints/checkpoint_<最後>``。最良の回を選ばない）の模型の重みから補助の頭を除いて
   ``$S/final/<run>_final_model.pth`` に置く（推論の構造は検出塔と同じ）
2. 塔単独の再現と同じ経路（``scripts/stage2pilot/pd_eval.py --cfg plain``）で val を評価する
   （overall mAP、標的群・陰性対照群 AP、クラス別、動画ごと。予測は保存先）
3. 学習ログから epoch ごとの検出の損失・補助損失（重みを掛けた値）・学習率・val mAP（学習中の評価）、
   歩ごとの記録から epoch ごとの補助損失（重みを掛ける前）と頭の当たり具合を集める
4. run の置き場に metrics.json、per_class_ap.json、epoch_log.json、notes.md を書く

    python scripts/grasppilot/d_finalize.py --run grasppilot3_d_none_ep15_seed42
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

TASK = "T-2026-11-01-grasp-pilot-d"
M = Path("/home/ubuntu/slocal2/m2")
S = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK
TEST_VIDEOS = {"04", "05", "07"}
AP_LINE = "Average Precision  (AP) @[ IoU=0.50:0.95 | area=   all | maxDets=100 ] ="


def sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_training_log(path: Path):
    """epoch ごとの学習の平均（Averaged stats の括弧内 = その epoch の平均）と学習中の val mAP。"""
    lines = path.read_text().splitlines()
    epochs, aps, steps_per_epoch = [], [], None
    cur = None
    for ln in lines:
        m = re.search(r"Epoch: \[(\d+)\]\s+\[\s*(\d+)/(\d+)\]", ln)
        if m:
            cur = int(m.group(1))
            steps_per_epoch = int(m.group(3))
            if int(m.group(2)) == 0:
                lr0 = re.search(r"lr: ([0-9.e-]+)", ln)
                epochs.append({"epoch": cur, "lr_at_step0": float(lr0.group(1)) if lr0 else None})
        if "Averaged stats" in ln and " loss: " in ln and cur is not None:
            rec = epochs[-1]
            for k, v in re.findall(r"(\w+): [0-9.e+-]+ \(([0-9.e+-]+)\)", ln):
                rec[f"avg_{k}"] = float(v)
            lr = re.search(r"(?:^|\s)lr: ([0-9.e-]+)", ln)
            rec["lr_end"] = float(lr.group(1)) if lr else None
        if AP_LINE in ln:
            aps.append(float(ln.split("=")[-1]))
    for e, ap in zip(epochs, aps):
        e["val_mAP_inloop"] = ap
    det_keys = None
    for e in epochs:
        losses = {k: v for k, v in e.items() if k.startswith("avg_loss_")}
        e["avg_loss_det"] = sum(v for k, v in losses.items() if k != "avg_loss_grasp")
        det_keys = det_keys or sorted(losses)
    return epochs, steps_per_epoch, len(aps)


def parse_steplog(path: Path, steps_per_epoch: int):
    per = {}
    with path.open() as f:
        for ln in f:
            r = json.loads(ln)
            e = r["step"] // steps_per_epoch
            d = per.setdefault(e, {"ce": [], "acc": [], "n_matched": 0, "n_gt": 0, "flipped": 0, "steps": 0, "feat_calls": set()})
            d["ce"].append(r["ce"])
            if r["acc"] == r["acc"]:
                d["acc"].append(r["acc"] * r["n_matched"])
            d["n_matched"] += r["n_matched"]
            d["n_gt"] += r["n_gt"]
            d["flipped"] += r["n_flipped_imgs"]
            d["steps"] += 1
            d["feat_calls"].add(r["n_feat_calls"])
            weight = r["weight"]
    out = []
    for e in sorted(per):
        d = per[e]
        out.append({"epoch": e, "steps": d["steps"], "aux_ce_mean": float(np.mean(d["ce"])),
                    "aux_acc_matched": float(np.sum(d["acc"]) / d["n_matched"]) if d["n_matched"] else None,
                    "n_matched": d["n_matched"], "n_gt": d["n_gt"], "matched_eq_gt": d["n_matched"] == d["n_gt"],
                    "flipped_images": d["flipped"], "feat_calls_per_step": sorted(d["feat_calls"])})
    return out, weight


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--gpu", default="0")
    a = ap.parse_args()
    R = M / "experiments/phase1" / a.run
    W = S / "work" / a.run
    F = S / "final"
    F.mkdir(parents=True, exist_ok=True)
    cks = sorted((W / "checkpoints").glob("checkpoint_*"), key=lambda p: int(p.name.split("_")[-1]))
    last = cks[-1]
    epochs, spe, n_ap = parse_training_log(W / "training.log")
    last_epoch = int(last.name.split("_")[-1])
    assert last_epoch == epochs[-1]["epoch"], (last_epoch, epochs[-1]["epoch"])
    st = torch.load(last / "pytorch_model.bin", map_location="cpu")
    head_keys = sorted(k for k in st if k.startswith("grasp_head"))
    head = {k: st[k] for k in head_keys}
    st = {k: v for k, v in st.items() if not k.startswith("grasp_head")}
    final = F / f"{a.run}_final_model.pth"
    torch.save({"model": st}, final)
    torch.save(head, F / f"{a.run}_grasp_head.pth")
    preds = F / f"{a.run}_val_preds.json.gz"
    ev = R / "eval_val.json"
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": a.gpu}
    rc = subprocess.run([sys.executable, str(M / "scripts/stage2pilot/pd_eval.py"), "--cfg", "plain", "--det-ckpt", str(final),
                         "--save-preds", str(preds), "--out", str(ev)], env=env,
                        stdout=(R / "eval_val.log").open("w"), stderr=subprocess.STDOUT).returncode
    assert rc == 0, f"pd_eval rc={rc}"
    e = json.loads(ev.read_text())
    steps, weight = parse_steplog(W / "grasp_steplog.jsonl", spe)
    by_e = {s["epoch"]: s for s in steps}
    for rec in epochs:
        rec.update({f"step_{k}": v for k, v in by_e.get(rec["epoch"], {}).items() if k != "epoch"})
    cfg_lines = (R / "config.yaml").read_text()
    load = [json.loads(x) for x in (W / "load_record.jsonl").read_text().splitlines()]
    anns = {p: json.loads((Path(os.environ["EGO_ANN_DIR"]) / f"instances_{p}.json").read_text()) for p in ("train", "val")}
    vids = {p: sorted({Path(im["file_name"]).stem.split("_")[0] for im in d["images"]}) for p, d in anns.items()}
    met = e["metrics"]
    res = {"task_id": TASK, "unofficial": True, "run": a.run, "aux_weight": weight,
           "result_state": {"checkpoint": str(last), "epoch": last_epoch, "selection": "final_state（最良の回を選ばない）"},
           "final_model": str(final), "final_model_sha256": sha256(final),
           "grasp_head_keys_removed": head_keys, "val_preds": str(preds), "val_preds_sha256": sha256(preds),
           "val": {"mAP": met["AP"], "mAP_50": met.get("AP50"), "target_AP": met["target_AP"], "control_AP": met["control_AP"],
                   "target_missing": met["target_missing"], "control_missing": met["control_missing"],
                   "per_video_AP": met["per_video_AP"], "n_images": met["n_images"],
                   "eval_detection_mAP": e["eval_detection_mAP"]},
           "eval_load_report": e["load_report"], "steps_per_epoch": spe, "n_epochs": len(epochs), "n_inloop_evals": n_ap,
           "coco_load_record": load,
           "videos_passed": {"train": vids["train"], "val": vids["val"],
                             "test_overlap": sorted((set(vids["train"]) | set(vids["val"]) | set(e["videos"])) & TEST_VIDEOS)},
           "epochs": epochs}
    (R / "metrics.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    (R / "per_class_ap.json").write_text(json.dumps(met["per_class_ap"], ensure_ascii=False, indent=1) + "\n")
    rows = "\n".join(f"| {r['epoch']} | {r.get('lr_at_step0')} | {r.get('avg_loss_det', float('nan')):.4f} | "
                     f"{r.get('avg_loss_grasp', float('nan')):.4f} | {r.get('step_aux_ce_mean', float('nan')):.4f} | "
                     f"{r.get('step_aux_acc_matched') if r.get('step_aux_acc_matched') is not None else float('nan'):.4f} | "
                     f"{r.get('val_mAP_inloop')} |" for r in epochs)
    (R / "notes.md").write_text(f"""# {a.run}

**非公式の測定（{TASK}）。関門の判定にも設計の判断にも使わない。**

案 D の腕。補助損失の重み {weight}。設定は `config.yaml`、起動は `command.sh`。

## 結果（最後の状態 = epoch {last_epoch}、最良の回を選ばない）

- val overall mAP {met['AP']:.7f} / 標的群 AP {met['target_AP']:.7f} / 陰性対照群 AP {met['control_AP']:.7f}
- 動画ごと: {json.dumps(met['per_video_AP'])}
- 評価の経路: `scripts/stage2pilot/pd_eval.py --cfg plain`（塔単独の再現と同じ。補助の頭を除いた重み）

## epoch ごと

| epoch | lr（歩 0） | 検出の損失（平均） | 補助損失 × 重み（平均） | 補助損失（重みの前、平均） | 頭の当たり（対応づいた枠） | val mAP（学習中の評価） |
|---|---|---|---|---|---|---|
{rows}

学習中の評価は main.py の `evaluate_acc`（記録の検出塔の val_ap_per_epoch と同じ経路）。上の結果の値は pd_eval の値。
""")
    print(json.dumps({"run": a.run, "mAP": met["AP"], "target_AP": met["target_AP"], "control_AP": met["control_AP"],
                      "epochs": len(epochs), "last_epoch": last_epoch}, ensure_ascii=False))
    del cfg_lines


if __name__ == "__main__":
    main()

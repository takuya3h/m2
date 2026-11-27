"""Task B: 検出塔単独の val 評価（ilya、detr-venv）と基準予測 plain_val_preds.json.gz の保存。"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import torch

PROJ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJ / "scripts"))
import train_t1b as t1b  # noqa: E402  (import 時に cwd を third_party/Relation-DETR へ移す)

from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

TASK = "T-2026-11-26-vlm-caption-signal-pilot"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / "vlm_caption_signal_pilot"
OUT = STORE / "task_b"
ID_DIR = STORE / "identity"
RECORD = {"AP": 0.7273450, "target_AP": 0.7950748, "control_AP": 0.6726632}


def main():
    import models.bricks.ms_deform_attn as msda
    ext_loaded = msda._C is not None
    print(f"[dtower_alone] torch={torch.__version__} cuda={torch.cuda.is_available()} ms_deform_attn_ext={ext_loaded}", flush=True)
    if not ext_loaded:
        raise SystemExit("ms_deform_attn_ext が読み込めていない")

    device = torch.device("cuda")
    torch.manual_seed(0)
    det_val = t1b.build_det_loader(train=False)
    stems = [Path(im["file_name"]).stem for im in det_val.dataset.coco.imgs.values()]
    videos = C.assert_no_test(stems, "task_b/dtower_alone")
    cfg = str(PROJ / "configs/stage2pilot/pd_film_d9.py")
    model = t1b.build_model(device, 42, cfg, ckpt_override=str(C.DET_CKPT))
    t1b.register_classes(model, det_val)
    model.eval()
    m_ap, _, preds = t1b.eval_detection(model, det_val, {}, device, zero_ctx=True, collect_predictions=True, dim=9)
    met = M.summary(Path(t1b.ANN_DIR) / "instances_val.json", preds["results"], preds["image_ids"])

    ID_DIR.mkdir(parents=True, exist_ok=True)
    ref_path = ID_DIR / "plain_val_preds.json.gz"
    with gzip.open(ref_path, "wt", encoding="utf-8") as fh:
        json.dump(preds["results"], fh)

    diffs = {k: met[k] - RECORD[k] for k in RECORD}
    out = {
        "task_id": TASK,
        "ms_deform_attn_ext": ext_loaded,
        "det_ckpt": str(C.DET_CKPT),
        "det_ckpt_sha256": C.sha256(C.DET_CKPT),
        "videos": videos,
        "n_images": len(stems),
        "eval_detection_mAP": m_ap,
        "metrics": met,
        "record": RECORD,
        "diffs_vs_record": diffs,
        "within_0.005": all(abs(v) <= 0.005 for v in diffs.values()),
        "plain_val_preds": str(ref_path),
        "plain_val_preds_sha256": C.sha256(ref_path),
    }
    C.write_json(OUT / "dtower_alone.json", out)
    print(json.dumps({
        "AP": met["AP"], "target_AP": met["target_AP"], "control_AP": met["control_AP"],
        "diffs_vs_record": diffs, "within_0.005": out["within_0.005"],
        "videos": videos, "n_images": len(stems),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

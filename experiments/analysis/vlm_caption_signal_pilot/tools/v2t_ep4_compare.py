"""Task F (W1): V→T の 4 epoch 止め確かめ（P1 W1 予測-甲 ep4 vs ep16 の 4 epoch 目）の比較。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot")
P1 = ROOT / "experiments/phase1"


def main():
    d4 = P1 / "vlm_caption_signal_pilot_pd_P1_W1_vlm_ko_ep4_seed42"
    d16 = P1 / "vlm_caption_signal_pilot_pd_P1_W1_vlm_ko_ep16_seed42"
    m4 = json.loads((d4 / "v2t_metrics.json").read_text())["per_epoch_1idx"]["4"]
    m16_4 = json.loads((d16 / "v2t_metrics.json").read_text())["per_epoch_1idx"]["4"]
    m16_8 = json.loads((d16 / "v2t_metrics.json").read_text())["per_epoch_1idx"]["8"]

    p4 = M.load_results(d4 / "predictions/val_inj_ep3.json.gz")
    p16_4 = M.load_results(d16 / "predictions/val_inj_ep3.json.gz")
    p16_8 = M.load_results(d16 / "predictions/val_inj_ep7.json.gz")

    diff_4 = M.max_output_diff(p4, p16_4)
    diff_4v8 = M.max_output_diff(p4, p16_8)

    out = {
        "ep4_run": d4.name, "ep16_run": d16.name,
        "ep4_metrics": {k: m4[k] for k in ("AP", "target_AP", "control_AP")},
        "ep16_at_ep4_metrics": {k: m16_4[k] for k in ("AP", "target_AP", "control_AP")},
        "metric_diffs": {k: m4[k] - m16_4[k] for k in ("AP", "target_AP", "control_AP")},
        "preds_diff_ep4": diff_4,
        "control_ep4_vs_ep8_metric_diffs": {k: m4[k] - m16_8[k] for k in ("AP", "target_AP", "control_AP")},
        "control_ep4_vs_ep8_preds_diff": diff_4v8,
    }
    C.write_json(STORE / "task_f/v2t_ep4_compare.json", out)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

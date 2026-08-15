"""Phase C Step 5 — 推論の出来（AUROC/AP）と工程ごとの分解を checkpoint から測る。

metrics.json は正しさの割合しか持たない。**正しさの割合だけを見ない**（前の契約の
誤りの再発防止）ため、保存された best checkpoint から val の予測を作り直し、
下見と同じ sklearn の関数で曲線下面積と平均適合率を出す。
併せて PhaseEvaluator の per-class F1 / Jaccard で工程ごとの分解を出す。
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from omegaconf import OmegaConf
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from train_grasp_phase_injection import _batch, load_clips  # noqa: E402
from train_grasp_phase_injection_variants import build_component_cfg_variants  # noqa: E402

from egosurgery.datasets.grasp_targets import GRASP_LABEL_NAMES  # noqa: E402
from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from egosurgery.models.build import build_grasp_phase_injection  # noqa: E402

TASK = "T-2026-08-15-injection-form-sweep"
PROBE_AUROC = {  # 下見の実測（並べるため）
    "left_hand": 0.6449, "right_hand": 0.7588, "left_hand_tool": 0.8293,
    "right_hand_tool": 0.7434, "two_hands_tool": 0.7928,
}
CFG_BY_DESC = {  # description -> 実行時に使った audit 設定
    "frozen_tecno_grasp_inference_ctrl": "s4_grasp_injection_ctrl.yaml",
    "frozen_tecno_grasp_inference_inj": "s4_grasp_injection_inj.yaml",
    "frozen_tecno_grasp_inference_inj_rawlogits": "s4_grasp_injection_raw_logits.yaml",
    "frozen_tecno_grasp_inference_inj_standardized": "s4_grasp_injection_standardized.yaml",
    "frozen_tecno_grasp_inference_inj_oracle_upper_bound_only": "s4_grasp_injection_oracle_upper_bound_only.yaml",
    "frozen_tecno_grasp_inference_inj_staged": "s4_grasp_injection_staged.yaml",
}


def main() -> None:
    device = torch.device("cpu")
    base_cfg = OmegaConf.load(AUDIT / "configs" / "s4_grasp_injection_ctrl.yaml")
    clips = load_clips("val", base_cfg)

    grasp_auc = defaultdict(lambda: defaultdict(list))   # arm -> dim -> [per-seed AUROC]
    grasp_ap = defaultdict(lambda: defaultdict(list))
    per_class = defaultdict(lambda: defaultdict(list))   # arm -> phase -> [per-seed F1]
    per_class_j = defaultdict(lambda: defaultdict(list))

    runs = []
    for d in sorted((ROOT / "experiments/phase1").glob("s4_grasp_injection_*")):
        if not (d / "metrics.json").exists():
            continue
        m = json.loads((d / "metrics.json").read_text())
        if m.get("task_id") != TASK:
            continue
        runs.append((d, m))

    for d, m in runs:
        desc = re.sub(r"^s4_grasp_injection_\d+_", "", d.name).rsplit("_seed", 1)[0]
        cfg = OmegaConf.load(AUDIT / "configs" / CFG_BY_DESC[desc])
        arm = f"{m['arm']}:{m['signal']}{':staged' if m.get('staged') else ''}"
        model = build_grasp_phase_injection(build_component_cfg_variants(cfg)).to(device)
        ckpt = torch.load(d / "checkpoints" / "best_grasp_phase.pth",
                          map_location=device, weights_only=True)
        model.load_state_dict(ckpt["model"])
        model.train(False)

        probs_chunks, target_chunks = [], []
        evaluator = PhaseEvaluator(num_classes=9)
        with torch.no_grad():
            for clip in clips:
                clip_id = clip[0]
                x, phase_y, grasp_y, grasp_mask = _batch(clip, device)
                out = model(x, grasp_targets=grasp_y, grasp_valid=grasp_mask)
                predictions = out["phase_logits"][-1][0].argmax(dim=0).cpu().numpy()
                evaluator.update(predictions, phase_y.cpu().numpy(), video_id=clip_id)
                probs = torch.sigmoid(out["grasp_logits"])[0].transpose(0, 1).cpu().numpy()
                valid = grasp_mask[0].cpu().numpy().astype(bool)
                probs_chunks.append(probs[valid])
                target_chunks.append(grasp_y[0].transpose(0, 1).cpu().numpy()[valid])

        p = np.concatenate(probs_chunks, 0)
        t = np.concatenate(target_chunks, 0)
        for i, name in enumerate(GRASP_LABEL_NAMES):
            if len(np.unique(t[:, i])) > 1:
                grasp_auc[arm][name].append(float(roc_auc_score(t[:, i], p[:, i])))
                grasp_ap[arm][name].append(float(average_precision_score(t[:, i], p[:, i])))
        res = evaluator.compute()
        for phase, f1 in res["phase_per_class_f1"].items():
            per_class[arm][phase].append(float(f1))
        for phase, j in res["phase_per_class_jaccard"].items():
            per_class_j[arm][phase].append(float(j))

    def _mean(d):
        return {k: {kk: sum(vv) / len(vv) for kk, vv in v.items()} for k, v in d.items()}

    result = {
        "n_runs_reevaluated": len(runs),
        "grasp_auroc_mean_by_arm": _mean(grasp_auc),
        "grasp_ap_mean_by_arm": _mean(grasp_ap),
        "probe_auroc_reference": PROBE_AUROC,
        "phase_f1_mean_by_arm": _mean(per_class),
        "phase_jaccard_mean_by_arm": _mean(per_class_j),
    }
    (AUDIT / "reeval.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"記録: {AUDIT / 'reeval.json'}  再評価 {len(runs)} 本")
    inf = _mean(grasp_auc).get("inj:predicted_sigmoid", {})
    print("推論した値の腕の AUROC（10 種平均） 対 下見:")
    for name in GRASP_LABEL_NAMES:
        if name in inf:
            print(f"  {name:<18} {inf[name]:.4f}  (下見 {PROBE_AUROC[name]:.4f})")
    f1 = _mean(per_class)
    print()
    print("hemostasis の F1（10 種平均）:")
    for arm in sorted(f1):
        print(f"  {arm:<40} {f1[arm].get('hemostasis', float('nan')):.4f}")


if __name__ == "__main__":
    main()

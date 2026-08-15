"""把持を推論する部分が定数を出していないかを、下見と同じ土台で測り直す。

**集計値ではなくフレームごとの予測を見る。** 集計だけでは縮退が見えない。

前の実験は五つの次元について**正しさの割合**を報告し、下見の契約は**曲線下面積**を
報告していた。**指標が揃っていない。** 偏った教師のもとでは、多数派を出し続けるだけで
正しさの割合が高く出る。ここでは同じ予測から両方を出し、揃えて並べる。

予測は保存されていなかったため、**保存されている重みから作り直す**（学習はやり直さない）。
重みは前の実験そのものであるから、条件は定義上一致する。再現の確認として、
前の実験が報告した正しさの割合を突き合わせる。

対照として、**測る側の多数派をすべてのフレームに置いた偽の予測**を同じ手順へ通す。
偽の予測で曲線下面積が 0.5 に落ちなければ、測り方が壊れている。
"""

import json
import sys
from pathlib import Path

import numpy as np
import torch
from omegaconf import OmegaConf
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from train_grasp_phase_injection import build_component_cfg, load_clips  # noqa: E402

from egosurgery.datasets.grasp_targets import GRASP_LABEL_NAMES  # noqa: E402
from egosurgery.models.build import build_grasp_phase_injection  # noqa: E402

SEEDS = [("42", "002"), ("123", "004"), ("456", "006")]
RUN_TMPL = "experiments/phase1/s4_grasp_injection_{n}_frozen_tecno_grasp_inference_inj_seed{seed}"

# 下見の契約の実測（tasks/T-2026-08-11-grasp-linear-probe/audit/probe_result.csv）。
PROBE_AUROC = {
    "left_hand": 0.6449129559968507,
    "right_hand": 0.7588489941431118,
    "left_hand_tool": 0.82926633235067,
    "right_hand_tool": 0.7434458398744114,
    "two_hands_tool": 0.7927537708927844,
}
# 前の実験が報告した「正しさの割合」（3 seed 平均）。再現の確認に使う。
PRIOR_ACCURACY = {
    "left_hand": 0.9848084656061552,
    "right_hand": 0.9665345850362487,
    "left_hand_tool": 0.8756054618819492,
    "right_hand_tool": 0.8560105728872124,
    "two_hands_tool": 0.8837516564516599,
}


def _metrics(scores: np.ndarray, targets: np.ndarray) -> dict:
    """下見と同じ関数で測る。**名前が同じでも中身が違うことがあるため実装を合わせる。**

    曲線下面積と平均適合率はいずれも順位にしか依存しないため、
    sigmoid を通した値でも logits でも同じ値になる。
    """
    pos_rate = float(targets.mean())
    single_class = len(np.unique(targets)) < 2
    return {
        "n": int(targets.size),
        "positive_rate": pos_rate,
        "roc_auc": "UNKNOWN" if single_class else float(roc_auc_score(targets, scores)),
        "average_precision": "UNKNOWN" if single_class else float(average_precision_score(targets, scores)),
        # 丸めた後の正しさの割合。前の実験が報告していた指標である。
        "accuracy": float(((scores >= 0.5) == (targets >= 0.5)).mean()),
        # 多数派を出し続けたときに出る割合。偶然の水準の一つ。
        "majority_rate": float(max(pos_rate, 1.0 - pos_rate)),
        "predicted_positive_rate": float((scores >= 0.5).mean()),
    }


def _dispersion(scores: np.ndarray) -> dict:
    q1, q2, q3 = (float(x) for x in np.quantile(scores, [0.25, 0.5, 0.75]))
    return {
        "min": float(scores.min()),
        "max": float(scores.max()),
        "std": float(scores.std()),
        "n_distinct": int(np.unique(scores).size),
        "q25": q1,
        "median": q2,
        "q75": q3,
        "iqr": q3 - q1,
        "range": float(scores.max() - scores.min()),
    }


def main() -> None:
    cfg = OmegaConf.load(AUDIT / "configs" / "inj_seed42.yaml")
    device = torch.device("cpu")  # 推論のみ。GPU は要らない。

    clips = load_clips("val", cfg)
    targets = np.concatenate([c[3][c[4]] for c in clips], axis=0)  # (N, 5) 有効フレームのみ
    print(f"測る側のクリップ = {len(clips)}   有効フレーム = {targets.shape[0]}")

    per_seed = {}
    for seed, num in SEEDS:
        run = ROOT / RUN_TMPL.format(n=num, seed=seed)
        # 保存されているのはテンソルと epoch だけである。任意のオブジェクトを復元させない。
        ckpt = torch.load(
            run / "checkpoints" / "best_grasp_phase.pth", map_location=device, weights_only=True
        )
        seed_cfg = OmegaConf.load(AUDIT / "configs" / f"inj_seed{seed}.yaml")
        model = build_grasp_phase_injection(build_component_cfg(seed_cfg)).to(device)
        model.load_state_dict(ckpt["model"])
        model.eval()

        chunks = []
        with torch.no_grad():
            for clip in clips:
                _, features, _, _, valid = clip
                x = torch.from_numpy(features).unsqueeze(0).transpose(1, 2).to(device)
                logits = model(x)["grasp_logits"]  # (1, 5, T)
                probs = torch.sigmoid(logits)[0].transpose(0, 1).cpu().numpy()  # (T, 5)
                chunks.append(probs[valid])
        per_seed[seed] = {"probs": np.concatenate(chunks, axis=0), "epoch": int(ckpt.get("epoch", -1))}
        np.savez_compressed(
            AUDIT / f"preds_inj_seed{seed}.npz", probs=per_seed[seed]["probs"], targets=targets
        )
        print(f"  seed {seed:<4} epoch={per_seed[seed]['epoch']:<3} 予測 {per_seed[seed]['probs'].shape}")

    dims = list(GRASP_LABEL_NAMES)
    quality, degeneracy = {}, {}
    for i, name in enumerate(dims):
        y = targets[:, i]
        per = {s: _metrics(per_seed[s]["probs"][:, i], y) for s, _ in SEEDS}
        acc_mean = float(np.mean([per[s]["accuracy"] for s, _ in SEEDS]))
        auc_vals = [per[s]["roc_auc"] for s, _ in SEEDS if per[s]["roc_auc"] != "UNKNOWN"]

        # 対照: 多数派をすべてのフレームに置いた偽の予測。
        majority = 1.0 if y.mean() >= 0.5 else 0.0
        fake = np.full(y.shape, majority, dtype=np.float64)
        fake_m = _metrics(fake, y)

        quality[name] = {
            "positive_rate_val": float(y.mean()),
            "n_val": int(y.size),
            "n_positive": int(y.sum()),
            "chance_roc_auc": 0.5,
            "chance_average_precision": float(y.mean()),
            "majority_rate": float(max(y.mean(), 1 - y.mean())),
            "per_seed": per,
            "roc_auc_mean": float(np.mean(auc_vals)) if auc_vals else "UNKNOWN",
            "average_precision_mean": float(np.mean([per[s]["average_precision"] for s, _ in SEEDS])),
            "accuracy_mean": acc_mean,
            "probe_roc_auc": PROBE_AUROC[name],
            "prior_reported_accuracy": PRIOR_ACCURACY[name],
            "accuracy_reproduces_prior": abs(acc_mean - PRIOR_ACCURACY[name]) < 5e-4,
            "fake_majority": fake_m,
        }
        degeneracy[name] = {
            "per_seed": {s: _dispersion(per_seed[s]["probs"][:, i]) for s, _ in SEEDS},
            "predicted_positive_rate_per_seed": {s: per[s]["predicted_positive_rate"] for s, _ in SEEDS},
            "positive_rate_val": float(y.mean()),
        }

    (AUDIT / "head_quality.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n")
    (AUDIT / "degeneracy.json").write_text(json.dumps(degeneracy, ensure_ascii=False, indent=2) + "\n")

    print()
    print(f"{'次元':<18}{'正例率':>8}{'AUROC':>9}{'下見':>8}{'AP':>9}{'正答率':>9}{'多数派':>8}{'偽AUROC':>9}")
    for name in dims:
        q = quality[name]
        auc = q["roc_auc_mean"]
        fa = q["fake_majority"]["roc_auc"]
        print(f"{name:<18}{q['positive_rate_val']:>8.4f}"
              f"{(auc if isinstance(auc,float) else float('nan')):>9.4f}{q['probe_roc_auc']:>8.3f}"
              f"{q['average_precision_mean']:>9.4f}{q['accuracy_mean']:>9.4f}{q['majority_rate']:>8.4f}"
              f"{(fa if isinstance(fa,float) else float('nan')):>9.4f}")
    print()
    print("前の実験の正しさの割合を再現できたか")
    for name in dims:
        q = quality[name]
        print(f"  {name:<18} 再測 {q['accuracy_mean']:.7f}  前回 {q['prior_reported_accuracy']:.7f}  "
              f"一致={q['accuracy_reproduces_prior']}")
    print()
    print("予測の散らばり（seed 42）")
    for name in dims:
        d = degeneracy[name]["per_seed"]["42"]
        print(f"  {name:<18} min={d['min']:.6f} max={d['max']:.6f} std={d['std']:.6f} "
              f"相異なる値={d['n_distinct']:<6} 幅={d['range']:.6f}")


if __name__ == "__main__":
    main()

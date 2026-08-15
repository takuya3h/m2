"""Phase C の記録 — 信号の到達量・重みの総数・形ごとの値域を数値で残す。

試験（tests/test_injection_signal_variants.py）は合否だけを言う。ここでは
**変化の大きさそのもの**を記録する。「変わった」とだけ書かないためである。
実寸（input 2048 / hidden 64 / phases 9 / TeCNO 2x8x64）で測る。
"""

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from egosurgery.models.heads.tecno_head import TeCNO  # noqa: E402
from egosurgery.models.temporal.grasp_inference_injection import (  # noqa: E402
    GraspInferenceInjectionModel,
)

STATS = json.loads((AUDIT / "train_stats.json").read_text())
FORM_EXTRAS = {
    "predicted_sigmoid": {},
    "raw_logits": {},
    "standardized": {
        "signal_center": STATS["signal_center"],
        "signal_scale": STATS["signal_scale"],
    },
    "oracle_upper_bound_only": {
        "oracle_upper_bound_acknowledged": True,
        "oracle_missing_fill": STATS["oracle_missing_fill"],
    },
}


def _cfg(arm: str, signal: str) -> dict:
    return {
        "enabled": True,
        "arm": arm,
        "input_dim": 2048,
        "hidden_dim": 64,
        "num_grasp_classes": 5,
        "num_phases": 9,
        "temporal": {"num_stages": 2, "num_layers": 8, "num_f_maps": 64, "dropout": 0.5},
        "signal": signal,
        **FORM_EXTRAS.get(signal, {}),
    }


def main() -> None:
    torch.manual_seed(20260815)
    features = torch.randn(1, 2048, 32)
    targets = torch.randint(0, 2, (1, 5, 32)).float()
    valid = torch.ones(1, 32)
    zeros, ones = torch.zeros(1, 5, 32), torch.ones(1, 5, 32)

    reference = GraspInferenceInjectionModel(_cfg("inj", "predicted_sigmoid")).eval()
    state = reference.state_dict()

    reachability, ranges, counts = {}, {}, {}
    for signal in FORM_EXTRAS:
        inj = GraspInferenceInjectionModel(_cfg("inj", signal)).eval()
        inj.load_state_dict(state, strict=False)
        kw = {"grasp_targets": targets, "grasp_valid": valid}
        out_a = inj(features, injected_signal=zeros, **kw)["phase_logits"][-1]
        out_b = inj(features, injected_signal=ones, **kw)["phase_logits"][-1]
        native = inj(features, **kw)["phase_input_signal"]
        reachability[f"inj:{signal}"] = {
            "max_abs_output_delta": float((out_a - out_b).abs().max()),
            "mean_abs_output_delta": float((out_a - out_b).abs().mean()),
        }
        ranges[signal] = {
            "min": float(native.min()),
            "max": float(native.max()),
            "per_dim_mean": [float(x) for x in native.mean(dim=(0, 2))],
            "per_dim_std": [float(x) for x in native.std(dim=(0, 2))],
        }
        counts[f"inj:{signal}"] = sum(
            p.numel() for p in inj.parameters() if p.requires_grad
        )

    ctrl = GraspInferenceInjectionModel(_cfg("ctrl", "zeros")).eval()
    ctrl.load_state_dict(state, strict=False)
    kw = {"grasp_targets": targets, "grasp_valid": valid}
    c_a = ctrl(features, injected_signal=zeros, **kw)["phase_logits"][-1]
    c_b = ctrl(features, injected_signal=ones, **kw)["phase_logits"][-1]
    reachability["ctrl:zeros"] = {
        "max_abs_output_delta": float((c_a - c_b).abs().max()),
        "mean_abs_output_delta": float((c_a - c_b).abs().mean()),
    }
    counts["ctrl:zeros"] = sum(p.numel() for p in ctrl.parameters() if p.requires_grad)

    baseline = TeCNO(
        num_stages=2, num_layers=8, num_f_maps=64, in_dim=2048, num_classes=9, dropout=0.5
    )
    n_baseline = sum(p.numel() for p in baseline.parameters())

    result = {
        "signal_reachability": reachability,
        "signal_value_ranges": ranges,
        "trainable_parameter_counts": counts,
        "baseline_tecno_parameters": n_baseline,
        "count_delta_vs_baseline": {k: v - n_baseline for k, v in counts.items()},
        "all_counts_equal": len(set(counts.values())) == 1,
    }
    (AUDIT / "phase_c.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"記録: {AUDIT / 'phase_c.json'}")
    print()
    print("信号の到達（同じ重みで零と一の信号を与えたときの工程出力の差）")
    for k, v in reachability.items():
        print(f"  {k:<30} max|Δ|={v['max_abs_output_delta']:.6f}  mean|Δ|={v['mean_abs_output_delta']:.6f}")
    print()
    print("学習可能な重みの総数")
    for k, v in counts.items():
        print(f"  {k:<30} {v}   (基準点との差 {v - n_baseline})")
    print(f"  基準点 TeCNO                  {n_baseline}")
    print(f"  五つの腕が完全一致: {result['all_counts_equal']}")
    print()
    print("形ごとの信号の値域（同じ重み・同じ入力）")
    for k, v in ranges.items():
        print(f"  {k:<26} min={v['min']:+.4f} max={v['max']:+.4f}")


if __name__ == "__main__":
    main()

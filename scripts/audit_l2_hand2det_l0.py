#!/usr/bin/env python
"""L0 監査: Hand-mask→Det（L2 4ch / L1a 5ch）モデルの配線検証（audit_t1b_l0.py 形式）。

合成手 mask で「注入機構が正しく配線されている」ことを実測で示す。負の結果が出ても
under-tuning/バグと区別できるよう、以下 5 チェックの all_pass を出す。

  1. gradient_flow      : forward→backward 後、trainable weight.grad が finite かつ非ゼロ
  2. loss_at_init       : warm-start 直後の loss が妥当範囲・再現性あり
  3. nan_inf_hook       : forward/backward に NaN/inf hook を仕掛け安定性確認
  4. overfit_one_batch  : 単一 batch を N step 訓練して loss 低減（容量・配線の証明）
  5. injection_wiring   : ★核心。合成手 mask(≠0)では注入経路(hand_prior.*)にのみ非ゼロ勾配、
                          注入テンソルを 0 にした対照では注入経路の勾配が **厳密に 0**
                          （bias 無し zero-init conv → 0 入力で残差 0・勾配 0）。

実行（.venv-relation-detr, cwd=third_party/Relation-DETR）:
  source .venv-relation-detr/bin/activate && export CUDA_HOME=/usr/local/cuda-11.8
  python /abs/scripts/audit_l2_hand2det_l0.py --hand-channels 4 --seed 42
  python /abs/scripts/audit_l2_hand2det_l0.py --hand-channels 5 --seed 42

出力: experiments/hand2det_dev/audit/l0_audit_{4|5}ch_seed{S}/audit_report.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

BODY = Path(os.environ.get("EGO_BODY", Path(__file__).resolve().parents[1]))
RELDETR = BODY / "third_party" / "Relation-DETR"
sys.path.insert(0, str(RELDETR))
sys.path.insert(0, str(BODY / "scripts"))
os.chdir(RELDETR)

from train_t1b import build_det_loader, build_model, register_classes  # noqa: E402
from train_hand2det import (  # noqa: E402
    MODEL_CFG_HAND2DET,
    hand_prior_tensor,
    set_hand_source,
    set_trainable,
)


def _targets_to_device(targets, device):
    return [{k: (v.to(device) if isinstance(v, torch.Tensor) else v) for k, v in t.items()}
            for t in targets]


def _next_batch(loader_iter, device):
    images, targets = next(loader_iter)
    images = [img.to(device) for img in images]
    targets = _targets_to_device(targets, device)
    return images, targets


def check_gradient_flow(model, loader_iter, hand_channels, device) -> dict:
    """1: trainable weight.grad が finite かつ（注入経路は）非ゼロ（dead branch 検出）。"""
    model.train()
    images, targets = _next_batch(loader_iter, device)
    model.set_hand_prior(hand_prior_tensor(targets, hand_channels, device, zero=False))
    loss_dict = model(images, targets)
    loss = sum(loss_dict.values())
    model.zero_grad()
    loss.backward()

    issues = []
    inject_grads = []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if p.grad is None:
            issues.append(f"{name}: grad is None (dead branch)")
            continue
        gn = float(p.grad.norm())
        if not math.isfinite(gn):
            issues.append(f"{name}: grad norm not finite (NaN/inf)")
        if "hand_prior" in name:
            inject_grads.append((name, gn))
    return {
        "loss_value": float(loss), "loss_is_finite": math.isfinite(float(loss)),
        "n_trainable_params": sum(1 for p in model.parameters() if p.requires_grad),
        "n_issues": len(issues), "issues": issues[:20],
        "inject_param_grad_norms": [{"name": n, "grad_norm": gn} for n, gn in inject_grads],
        "inject_grad_nonzero_count": sum(1 for _, gn in inject_grads if gn > 0),
        "inject_grad_total": len(inject_grads),
        "pass": (len(issues) == 0 and math.isfinite(float(loss))
                 and any(gn > 0 for _, gn in inject_grads)),
    }


def check_loss_at_init(model, loader_iter, hand_channels, device, n_samples: int = 3) -> dict:
    """2: warm-start 直後の loss 値の妥当性・再現性。"""
    model.train()
    losses = []
    with torch.no_grad():
        for _ in range(n_samples):
            images, targets = _next_batch(loader_iter, device)
            model.set_hand_prior(hand_prior_tensor(targets, hand_channels, device, zero=False))
            loss_dict = model(images, targets)
            losses.append(float(sum(loss_dict.values())))
    return {
        "n_samples": n_samples, "loss_values": losses,
        "loss_mean": float(np.mean(losses)), "loss_std": float(np.std(losses)),
        "all_finite": all(math.isfinite(l) for l in losses),
        "pass": all(math.isfinite(l) and 0.5 < l < 50.0 for l in losses),
    }


def check_nan_inf_hook(model, loader_iter, hand_channels, device, n_steps: int = 5) -> dict:
    """3: training の forward 出力に NaN/inf hook を仕掛け安定性確認。"""
    nan_inf_hits = []

    def make_hook(name):
        def hook(module, inp, out):
            if isinstance(out, torch.Tensor) and (torch.isnan(out).any() or torch.isinf(out).any()):
                nan_inf_hits.append(f"{name}: forward output has NaN/inf")
        return hook

    handles = []
    for name, m in model.named_modules():
        if isinstance(m, (torch.nn.Linear, torch.nn.LayerNorm, torch.nn.Conv2d)):
            if "hand_prior" in name or "transformer.decoder.layers.0" in name:
                handles.append(m.register_forward_hook(make_hook(name)))

    model.train()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
    losses = []
    for _ in range(n_steps):
        images, targets = _next_batch(loader_iter, device)
        model.set_hand_prior(hand_prior_tensor(targets, hand_channels, device, zero=False))
        loss_dict = model(images, targets)
        loss = sum(loss_dict.values())
        losses.append(float(loss))
        if not math.isfinite(float(loss)):
            break
        opt.zero_grad()
        loss.backward()
        opt.step()
    for h in handles:
        h.remove()
    return {
        "n_steps": len(losses), "loss_trajectory": losses,
        "all_finite": all(math.isfinite(l) for l in losses),
        "nan_inf_hits": nan_inf_hits[:20], "n_nan_inf_hits": len(nan_inf_hits),
        "pass": all(math.isfinite(l) for l in losses) and len(nan_inf_hits) == 0,
    }


def check_overfit_one_batch(model, loader_iter, hand_channels, device, n_steps: int = 50) -> dict:
    """4: 単一 batch を N step 訓練して loss 低減（optimizer/loss/注入 配線の容量証明）。

    このチェックの目的は「最適化機構（optimizer+loss+注入経路）が loss を駆動できるか」。
    注入のみ学習(film, 8192 param) では検出器凍結ゆえ物理的に容量が無く（1x1 conv の C5 残差
    のみ）loss をほとんど下げられない＝機構の証明にならない。よって capacity 試験として
    **検出器を解凍した model(trainable=all)** を呼び出し側で渡し、機構が loss を大きく下げられる
    ことを示す（注入経路の isolation は checks 1/5 が film で別途証明済み）。
    """
    model.train()
    fixed_images, fixed_targets = _next_batch(loader_iter, device)
    fixed_hand = hand_prior_tensor(fixed_targets, hand_channels, device, zero=False)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=5e-4)
    losses = []
    for _ in range(n_steps):
        model.set_hand_prior(fixed_hand)
        loss_dict = model(fixed_images, fixed_targets)
        loss = sum(loss_dict.values())
        losses.append(float(loss))
        if not math.isfinite(float(loss)):
            break
        opt.zero_grad()
        loss.backward()
        opt.step()
    init_loss = losses[0] if losses else float("nan")
    final_loss = losses[-1] if losses else float("nan")
    reduction = (init_loss - final_loss) / init_loss if init_loss > 0 else float("nan")
    return {
        "n_steps": len(losses), "init_loss": init_loss, "final_loss": final_loss,
        "loss_reduction_pct": float(reduction * 100),
        "min_loss": float(min(losses)) if losses else float("nan"),
        "trajectory_first_5": losses[:5], "trajectory_last_5": losses[-5:],
        "trainable_for_this_check": "all",
        # 検出器解凍(all)での容量試験。機構が正しく配線されていれば 1 batch を大きく overfit できる。
        "pass": math.isfinite(final_loss) and reduction > 0.3,
        "note_threshold": "容量試験(trainable=all)。注入 isolation は checks 1/5(film) が別途証明",
    }


def check_injection_wiring(model, loader_iter, hand_channels, device) -> dict:
    """5: ★核心。注入経路(hand_prior.*)のみに勾配が立ち、0 対照では厳密に 0。

    - trainable=film に強制（注入経路のみ requires_grad）→「注入経路paramにのみ非ゼロ勾配」。
    - 合成手 mask(≠0): hand_prior.proj.weight の grad norm > 0。
    - 注入テンソル 0: 同 grad norm == 0（bias 無し zero-init conv なので厳密に 0）。
    非注入の trainable param が 0 個であることも確認（他経路に勾配が漏れないことの担保）。
    """
    set_trainable(model, "film")
    non_inject_trainable = [n for n, p in model.named_parameters()
                            if p.requires_grad and "hand_prior" not in n]

    def grad_norm_with(zero: bool):
        images, targets = _next_batch(loader_iter, device)
        model.set_hand_prior(hand_prior_tensor(targets, hand_channels, device, zero=zero))
        loss = sum(model(images, targets).values())
        model.zero_grad()
        loss.backward()
        total = 0.0
        for n, p in model.named_parameters():
            if p.requires_grad and "hand_prior" in n and p.grad is not None:
                total += float(p.grad.norm().item()) ** 2
        return float(total ** 0.5), float(loss)

    gn_inj, loss_inj = grad_norm_with(zero=False)   # 合成手 mask 注入時
    gn_zero, loss_zero = grad_norm_with(zero=True)  # 0 対照

    inj_nonzero = gn_inj > 0.0
    zero_is_zero = gn_zero == 0.0
    only_injection = len(non_inject_trainable) == 0
    return {
        "inject_grad_norm_with_mask": gn_inj,
        "inject_grad_norm_zero_ctrl": gn_zero,
        "loss_with_mask": loss_inj, "loss_zero_ctrl": loss_zero,
        "n_non_inject_trainable_params": len(non_inject_trainable),
        "inject_grad_nonzero_with_mask": inj_nonzero,
        "inject_grad_zero_when_ctrl_zero": zero_is_zero,
        "only_injection_path_trainable": only_injection,
        "pass": inj_nonzero and zero_is_zero and only_injection,
        "interpretation": (
            "注入経路のみ勾配・0 対照で厳密 0 → 配線正常（tool 非依存の手側残差が正しく効いている）"
        ),
    }


def main():
    ap = argparse.ArgumentParser(description="L0 監査: Hand-mask→Det 配線検証")
    ap.add_argument("--hand-channels", type=int, choices=[4, 5], required=True)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--trainable", choices=["film", "all"], default="film")
    ap.add_argument("--n-overfit-steps", type=int, default=50)
    ap.add_argument("--hand-source", choices=["synth", "real"], default="synth",
                    help="注入 prior 源: synth(合成) / real(raw02 手 bbox・L2 実データ配線検証)")
    args = ap.parse_args()
    set_hand_source(args.hand_source)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    os.environ["HAND2DET_HAND_CHANNELS"] = str(args.hand_channels)

    det_train = build_det_loader(train=True)

    def build(trainable_override=None):
        m = build_model(device, args.seed, MODEL_CFG_HAND2DET)
        register_classes(m, det_train)
        set_trainable(m, trainable_override or args.trainable)
        return m

    def fresh_iter():
        return iter(det_train)

    model = build()
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[audit] hand_channels={args.hand_channels} seed={args.seed} trainable={args.trainable} "
          f"n_trainable={n_params:,}", flush=True)

    t0 = time.perf_counter()
    print("[audit] 1/5 gradient_flow ...", flush=True)
    grad_flow = check_gradient_flow(model, fresh_iter(), args.hand_channels, device)
    print(f"  loss={grad_flow['loss_value']:.3f} issues={grad_flow['n_issues']} "
          f"inject_nonzero={grad_flow['inject_grad_nonzero_count']}/{grad_flow['inject_grad_total']} "
          f"pass={grad_flow['pass']}", flush=True)

    print("[audit] 2/5 loss_at_init ...", flush=True)
    model = build()
    loss_init = check_loss_at_init(model, fresh_iter(), args.hand_channels, device)
    print(f"  loss mean={loss_init['loss_mean']:.3f} std={loss_init['loss_std']:.3f} "
          f"pass={loss_init['pass']}", flush=True)

    print("[audit] 3/5 nan_inf_hook ...", flush=True)
    model = build()
    nan_inf = check_nan_inf_hook(model, fresh_iter(), args.hand_channels, device)
    print(f"  n_steps={nan_inf['n_steps']} nan_inf_hits={nan_inf['n_nan_inf_hits']} "
          f"pass={nan_inf['pass']}", flush=True)

    print("[audit] 4/5 overfit_one_batch (capacity: trainable=all) ...", flush=True)
    model = build(trainable_override="all")  # 容量試験は検出器解凍で行う（機構の駆動力を測る）
    overfit = check_overfit_one_batch(model, fresh_iter(), args.hand_channels, device,
                                      n_steps=args.n_overfit_steps)
    print(f"  init={overfit['init_loss']:.3f} final={overfit['final_loss']:.3f} "
          f"reduction={overfit['loss_reduction_pct']:.1f}% pass={overfit['pass']}", flush=True)

    print("[audit] 5/5 injection_wiring ...", flush=True)
    model = build()
    wiring = check_injection_wiring(model, fresh_iter(), args.hand_channels, device)
    print(f"  grad(mask)={wiring['inject_grad_norm_with_mask']:.4g} "
          f"grad(zero)={wiring['inject_grad_norm_zero_ctrl']:.4g} "
          f"only_inject={wiring['only_injection_path_trainable']} pass={wiring['pass']}", flush=True)

    elapsed_min = (time.perf_counter() - t0) / 60
    all_pass = all(r["pass"] for r in (grad_flow, loss_init, nan_inf, overfit, wiring))

    report = {
        "hand_channels": args.hand_channels, "tier": ("Tier0/L2" if args.hand_channels == 4
                                                      else "Tier1/L1a"),
        "seed": args.seed, "trainable": args.trainable, "n_trainable_params": n_params,
        "elapsed_min": elapsed_min, "all_pass": all_pass,
        "checks": {
            "1_gradient_flow": grad_flow, "2_loss_at_init": loss_init,
            "3_nan_inf_hook": nan_inf, "4_overfit_one_batch": overfit,
            "5_injection_wiring": wiring,
        },
        "interpretation": (
            "L0 監査 PASS = 手 mask→det 注入機構の配線が正常（合成マスク・本番学習ではない）"
            if all_pass else "L0 監査 FAIL = 配線に問題（要修正）"
        ),
    }
    out_dir = BODY / "experiments" / "hand2det_dev" / "audit" / f"l0_audit_{args.hand_channels}ch_seed{args.seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "audit_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))

    print()
    print("=" * 60)
    print(f"[audit] hand_channels={args.hand_channels} seed={args.seed} 完了 ({elapsed_min:.1f} min)")
    print(f"  ALL PASS: {all_pass}")
    print(f"  1 gradient_flow    : {grad_flow['pass']}")
    print(f"  2 loss_at_init     : {loss_init['pass']}")
    print(f"  3 nan_inf_hook     : {nan_inf['pass']}")
    print(f"  4 overfit_one      : {overfit['pass']} (reduction={overfit['loss_reduction_pct']:.1f}%)")
    print(f"  5 injection_wiring : {wiring['pass']} "
          f"(mask={wiring['inject_grad_norm_with_mask']:.3g} / zero={wiring['inject_grad_norm_zero_ctrl']:.3g})")
    print(f"  証跡: {out_dir / 'audit_report.json'}")
    print("=" * 60)


if __name__ == "__main__":
    main()

"""DP（検出から工程）の界面の恒等性・学習・評価（非公式 T-2026-10-18-stage2-pilot-folda、Task D と F）。

本体の .venv で動かす。受け取り手は確定塔の時間ヘッド（凍結・eval）、入力は写した特徴。

    identity --type D2                       学習前の出力が塔単独と一致するか、界面を零でない値にすると変わるか
    train    --type D2 --arm gt --seed 42    一本の腕を学び、val で評価する（ExperimentManager の実験フォルダ）

型（SPEC §3）と腕（SPEC §4 Task F）:
    D1-L1 concat、D0 / D-GT（15）      D1-L2 concat、D0-RT（3840）     D2 film、D0 / D-GT（15）
    D3-L1 attn、D0-INST から埋め込みを除いたもの / D-GT-INST（15 + 4 + 出所の印 1）
    D3-L2 attn、D0-INST（15 + 4 + 256 + 出所の印 1）
    空 empty、予測-noCF pred_noCF、正解 gt、予測-CF pred_CF、正解予測-CF gtpred_CF（正解が先）

止め方（方向と学習範囲ごとに一つ。DP は W1 だけ）: 学習率一定、val の macro Jaccard が patience epoch
改善しなければ止める、上限 max_epochs。最良の時点は学習した epoch の val の macro Jaccard で選ぶ。

直しの契約（T-2026-10-19-stage2-pilot-fix-epoch4-shuffle）で足した引数。渡さなければ従来の経路のまま:
    --fixed-epochs N   N epoch 学習し、途中で止めず、最良の回を選ばずに N epoch 目の状態を結果にする
    --task-id / --exp-prefix   run の契約の識別子と名前の接頭辞（界面の重みは stage2pilot_store/<task-id>/dp_ckpt）
    --smoke            --fixed-epochs の短い試走の印（名前に _smoke、config に smoke: true）
    腕 shuffle         予測-noCF と同じ信号の値を、フレームとの対応だけ入れ替えたもの（stage2pilot_store/<直しの契約>/signals/shuffle）
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from stage2pilot import common as C  # noqa: E402
from stage2pilot.dp_model import DPReceiver  # noqa: E402

FINAL = C.STORE / "signals/final"
CF = C.STORE / "signals/cf"
SHUF = C.FIX_STORE / "signals/shuffle"
NT = 15
# 型 → (界面, 信号の種類, 予測の信号名, 正解の信号名, トークンの基底次元)
TYPES = {
    "D1-L1": ("concat", "vec", "D0", "D-GT", None),
    "D1-L2": ("concat", "vec", "D0-RT", None, None),
    "D2": ("film", "vec", "D0", "D-GT", None),
    "D3-L1": ("attn", "tok", "D0-INST", "D-GT-INST", NT + 4),
    "D3-L2": ("attn", "tok", "D0-INST", None, NT + 4 + 256),
}
ARMS = ("empty", "pred_noCF", "gt", "pred_CF", "gtpred_CF", "shuffle")
# 止め方の規則（DP・W1）。最初の腕を回す前に固定する
STOP = {"lr": 5e-4, "weight_decay": 0.01, "patience": 10, "max_epochs": 100, "smoothing_weight": 0.3}


def inst_name(base, variant):
    return base if base != "D0-INST" or variant == "literal" else "D0-INST-UQ"


def sources(type_name, arm, part, variant):
    """腕の信号の出所の並び [(ファイル, 正解か), ...]。空の腕は []。"""
    _, _, pred, gt, _ = TYPES[type_name]
    pred = inst_name(pred, variant)
    final_pred = (FINAL / f"{pred}_{part}.npz", False)
    pred_src = (CF / f"{pred}_train.npz", False) if (part == "train" and arm.endswith("_CF")) else final_pred
    if arm == "empty":
        return []
    if arm == "pred_noCF":
        return [final_pred]
    if arm == "shuffle":
        return [(SHUF / f"{pred}_{part}.npz", False)]
    if arm == "pred_CF":
        return [pred_src]
    if gt is None:
        raise ValueError(f"{type_name} に正解の腕は無い")
    gt_src = (FINAL / f"{gt}_{part}.npz", True)
    if arm == "gt":
        return [gt_src]
    return [gt_src, pred_src]                              # gtpred_CF: 正解が先


def load_npz(path):
    with np.load(path) as d:
        ids = [str(f) for f in d["frame_ids"]]
        return {f: i for i, f in enumerate(ids)}, d["x"].astype(np.float32), (d["count"] if "count" in d else None)


class Signals:
    """フレーム名 → 信号。vec は (S,)、tok は (K, D) と有効の印。"""

    def __init__(self, type_name, arm, part, variant):
        self.iface, self.kind, pred, _, self.tok_base = TYPES[type_name]
        self.srcs = sources(type_name, arm, part, variant)
        self.loaded = [(load_npz(p), is_gt) for p, is_gt in self.srcs]
        pred_path = FINAL / f"{inst_name(pred, variant)}_{part}.npz"
        with np.load(pred_path) as d:
            self.pred_dim = int(d["x"].shape[-1]) if self.kind == "vec" else None
        self.dim = (sum(x.shape[-1] for (_, x, _), _ in self.loaded) or self.pred_dim) if self.kind == "vec" \
            else self.tok_base + 1

    def files(self):
        return [{"path": str(p), "sha256": C.sha256(p), "gt": g} for p, g in self.srcs]

    def for_frames(self, frames):
        if self.kind == "vec":
            if not self.loaded:
                return torch.zeros(len(frames), self.dim), None
            cols = []
            for (ix, x, _), _ in self.loaded:
                cols.append(x[[ix[f] for f in frames]])
            return torch.from_numpy(np.concatenate(cols, 1)), None
        toks, masks = [], []
        for (ix, x, cnt), is_gt in self.loaded:
            rows = [ix[f] for f in frames]
            t = x[rows][:, :, :self.tok_base]
            flag = np.full(t.shape[:2] + (1,), 1.0 if is_gt else 0.0, np.float32)
            toks.append(np.concatenate([t, flag], -1))
            k = t.shape[1]
            masks.append(np.arange(k)[None, :] < cnt[rows][:, None] if cnt is not None
                         else np.ones((len(rows), k), bool))
        if not toks:
            return torch.zeros(len(frames), 0, self.dim), torch.zeros(len(frames), 0, dtype=torch.bool)
        return torch.from_numpy(np.concatenate(toks, 1)), torch.from_numpy(np.concatenate(masks, 1))


def build_data(videos, sig, feats, device):
    data = []
    for video, frames, labels in C.phase_sequences(videos):
        x = torch.from_numpy(np.stack([feats[f] for f in frames])).to(device)
        s, m = sig.for_frames(frames)
        data.append((video, x, s.to(device), None if m is None else m.to(device), torch.from_numpy(labels).to(device)))
    return data


@torch.no_grad()
def evaluate(model, data, names):
    model.eval()
    ev = PhaseEvaluator(num_classes=len(names), class_names=names)
    per_video, probs = {}, {}
    for video, x, s, m, y in data:
        out = model(x, s, m)[-1][0]                        # (9, T)
        pred = out.argmax(0).cpu().numpy()
        ev.update(pred, y.cpu().numpy(), video_id=video)
        one = PhaseEvaluator(num_classes=len(names), class_names=names)
        one.update(pred, y.cpu().numpy(), video_id=video)
        r = one.compute()
        per_video[video] = {"phase_jaccard": r["phase_jaccard"], "phase_accuracy": r["phase_accuracy"]}
        probs[video] = torch.softmax(out, 0).T.cpu().numpy()
    res = ev.compute()
    res["per_video"] = per_video
    return res, probs


@torch.no_grad()
def max_logit_diff(model_a, model_b_head, data):
    d = 0.0
    for _, x, s, m, _ in data:
        a = model_a(x, s, m)[-1]
        b = model_b_head(x.T[None])[-1]
        d = max(d, float((a - b).abs().max()))
    return d


def setup_common(device="cuda"):
    import stage1_ptower as base
    base.deterministic(42)
    names = C.phase_names()
    split = C.fold_a()
    feats = C.load_features()
    head = C.load_ptower_head(device=device)
    return names, split, feats, head


def cmd_identity(a):
    names, split, feats, head = setup_common()
    out = {"task_id": a.task_id, "type": a.type, "inst_variant": a.inst_variant}
    arms = [a.arm] if a.arm else [arm for arm in ("pred_noCF", "gt") if not (arm == "gt" and TYPES[a.type][3] is None)]
    for arm in arms:
        sig = Signals(a.type, arm, "val", a.inst_variant)
        torch.manual_seed(0)
        model = DPReceiver(head, TYPES[a.type][0], sig.dim).cuda()
        data = build_data(split["val"], sig, feats, "cuda")
        base_res, _ = evaluate(model, data, names)
        diff = max_logit_diff(model, head, data)
        with torch.no_grad():
            g = torch.Generator().manual_seed(1234)
            for p in model.iface_last_params():
                p.copy_((torch.randn(p.shape, generator=g) * a.perturb_scale).to(p.device))
        pert, _ = evaluate(model, data, names)
        pdiff = max_logit_diff(model, head, data)
        out[arm] = {"signal_files": sig.files(), "dim": sig.dim,
                    "iface_params": int(sum(p.numel() for p in model.iface.parameters())),
                    "identity_jaccard": base_res["phase_jaccard"], "identity_accuracy": base_res["phase_accuracy"],
                    "identity_max_abs_logit_diff": diff,
                    "jaccard_equals_taskB": base_res["phase_jaccard"] == C.PT_RECORD["phase_jaccard"],
                    "perturb_scale": a.perturb_scale, "positive_jaccard": pert["phase_jaccard"],
                    "positive_accuracy": pert["phase_accuracy"], "positive_max_abs_logit_diff": pdiff}
    C.write_json(a.out, out)
    print(json.dumps(out, ensure_ascii=False)[:1500])


def class_weights(train_data, n):
    counts = np.bincount(np.concatenate([d[4].cpu().numpy() for d in train_data]), minlength=n)
    w = np.divide(1.0, counts, out=np.zeros(len(counts)), where=counts > 0)
    return w / w[w > 0].mean(), counts


def cmd_train(a):
    from omegaconf import (
        OmegaConf,  # noqa: F401  (ExperimentManager.save_config が使う)
    )

    from egosurgery.utils import tracking
    from egosurgery.utils.experiment_manager import ExperimentManager
    names, split, feats, head = setup_common()
    random.seed(a.seed)
    np.random.seed(a.seed)
    torch.manual_seed(a.seed)
    sig_tr = Signals(a.type, a.arm, "train", a.inst_variant)
    sig_va = Signals(a.type, a.arm, "val", a.inst_variant)
    assert sig_tr.dim == sig_va.dim
    tr_videos = C.assert_no_test(split["train"], "dp_train/train")
    va_videos = C.assert_no_test(split["val"], "dp_train/val")
    model = DPReceiver(head, TYPES[a.type][0], sig_tr.dim).cuda()
    train_data = build_data(split["train"], sig_tr, feats, "cuda")
    val_data = build_data(split["val"], sig_va, feats, "cuda")
    weights, counts = class_weights(train_data, len(names))
    ce = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device="cuda"))
    params = [p for p in model.iface.parameters()]
    opt = torch.optim.AdamW(params, lr=STOP["lr"], weight_decay=STOP["weight_decay"])
    head_digest = C.sha256(C.PT_HEAD_CKPT)
    head_state0 = {k: v.clone() for k, v in model.head.state_dict().items()}
    fixed = a.fixed_epochs
    max_epochs = fixed or a.max_epochs or STOP["max_epochs"]
    stop_rule = {**STOP, "max_epochs": max_epochs, "lr_schedule": "constant",
                 "selection": "val macro Jaccard, trained epochs only"}
    if fixed:
        stop_rule = {**STOP, "patience": None, "max_epochs": fixed, "fixed_epochs": fixed, "lr_schedule": "constant",
                     "selection": f"none (state after epoch {fixed})"}
    cfg = {"task_id": a.task_id, "unofficial": f"非公式（{a.task_id}）", "direction": "DP",
           "type": a.type, "interface": TYPES[a.type][0], "arm": a.arm, "seed": a.seed, "scope": "W1",
           "inst_variant": a.inst_variant, "signal_dim": sig_tr.dim,
           "signals_train": sig_tr.files(), "signals_val": sig_va.files(),
           "receiver": {"head": str(C.PT_HEAD_CKPT), "head_sha256": head_digest, "cache": str(C.PT_CACHE),
                        "cache_sha256": C.sha256(C.PT_CACHE), "mode": "frozen, eval (dropout off)"},
           "stop_rule": stop_rule, **({"result_selection": "final_epoch"} if fixed else {}),
           "class_counts": counts.tolist(), "class_weights": weights.tolist(),
           "videos": {"train": tr_videos, "val": va_videos}, "smoke": bool(a.max_epochs or a.smoke),
           "iface_params": int(sum(p.numel() for p in params))}
    desc = f"{a.type}_{a.arm}" + (f"_ep{fixed}" if fixed else "") + ("_smoke" if a.max_epochs or a.smoke else "")
    manager = ExperimentManager(C.ROOT / "experiments", "phase1", a.exp_prefix, desc, a.seed)
    manager.setup(cfg)
    run = tracking.init(manager.exp_id, config=cfg, group=a.task_id, job_type=a.exp_prefix, exp_dir=manager.exp_dir)
    if run is None:
        raise RuntimeError("W&B tracking could not start; no experiment executed")
    init_res, _ = evaluate(model, val_data, names)
    best, best_score, stale, stopped, history, no_grad_steps = None, -1.0, 0, None, [], 0
    started = time.monotonic()
    ckpt = C.STORE.parent / a.task_id / "dp_ckpt" / f"{manager.exp_id}.pth"
    ckpt.parent.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, max_epochs + 1):
        model.train()
        order = list(range(len(train_data)))
        random.shuffle(order)
        total = 0.0
        for i in order:
            _, x, s, m, y = train_data[i]
            outs = model(x, s, m)
            loss = sum(ce(o[0].T, y) for o in outs)
            for o in outs:
                logp = F.log_softmax(o, dim=1)
                loss = loss + STOP["smoothing_weight"] * F.mse_loss(
                    logp[:, :, 1:], logp[:, :, :-1].detach(), reduction="none").clamp(max=16).mean()
            if not torch.isfinite(loss):
                raise RuntimeError(f"非数の損失 epoch {epoch}")
            total += float(loss)
            if not loss.requires_grad:
                # 界面に入力が届かない（D3 の空の腕はトークン 0 個で出力が特徴そのもの）。更新しない
                no_grad_steps += 1
                continue
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
        val, probs = evaluate(model, val_data, names)
        score = val["phase_jaccard"]
        history.append({"epoch": epoch, "train_loss": total / len(order), "val_jaccard": score,
                        "val_accuracy": val["phase_accuracy"]})
        tracking.log({"train/loss": total / len(order), "val/jaccard": score, "val/accuracy": val["phase_accuracy"]},
                     step=epoch)
        # --fixed-epochs: 最良の回を選ばず、最後の epoch の状態を結果にする（界面の重みと確率もその状態）
        if (epoch == fixed) if fixed else score > best_score:
            best_score, stale = score, 0
            best = {**val, "epoch": epoch}
            best_probs = probs
            torch.save({"iface": model.iface.state_dict(), "epoch": epoch, "type": a.type, "arm": a.arm,
                        "seed": a.seed, "signal_dim": sig_tr.dim}, ckpt)
        else:
            stale += 1
        if not fixed and stale >= STOP["patience"]:
            stopped = epoch
            break
    head_unchanged = all(torch.equal(v, model.head.state_dict()[k]) for k, v in head_state0.items())
    metrics = {"phase_jaccard": best["phase_jaccard"], "phase_accuracy": best["phase_accuracy"],
               "phase_macro_f1": best["phase_macro_f1"], "best_epoch": best["epoch"],
               **({"result_selection": "final_epoch", "result_epoch": best["epoch"]} if fixed else {}),
               "per_video": best["per_video"], "init_phase_jaccard": init_res["phase_jaccard"],
               "init_phase_accuracy": init_res["phase_accuracy"], "epochs_run": epoch, "early_stopped_epoch": stopped,
               "reached_epoch_cap": stopped is None and epoch == max_epochs,
               "elapsed_seconds": time.monotonic() - started, "receiver_unchanged": head_unchanged,
               "steps_without_grad": no_grad_steps,
               "iface_params": cfg["iface_params"], "iface_ckpt": str(ckpt), "iface_ckpt_sha256": C.sha256(ckpt)}
    if a.arm == "empty":
        metrics["negative_control"] = negative_control(a, model, ckpt, head, split, feats, names)
    manager.log_metrics(metrics)
    manager.log_per_class_ap(best["phase_per_class_jaccard"])
    manager.log_eval_recipe({"test_cfg": {"task": "phase", "inference_protocol": "online_causal",
                                          "jaccard_mode": "strict", "split": "val"}})
    C.write_json(manager.exp_dir / "logs/history.json", history)
    np.savez(manager.exp_dir / "predictions/val_probs_best.npz",
             **{v: p.astype(np.float32) for v, p in best_probs.items()})
    how = (f"{fixed} epoch 学習し途中で止めない。結果は {fixed} epoch 目の状態（最良の回を選ばない）。" if fixed
           else "val だけで評価し選ぶ。")
    (manager.exp_dir / "notes.md").write_text(
        f"# 非公式（{a.task_id}） DP {a.type} {a.arm} seed {a.seed}\n\n"
        f"受け取り手は確定塔の時間ヘッド（凍結）。界面だけを学ぶ（W1）。{how}test は通していない。\n"
        f"{'result' if fixed else 'best'} epoch {best['epoch']} / val macro Jaccard {best['phase_jaccard']} / "
        f"accuracy {best['phase_accuracy']}\n"
        f"epochs {epoch}（停止 {stopped}）、学習前 Jaccard {init_res['phase_jaccard']}\n")
    tracking.finish()
    print(f"DP_RUN_COMPLETE {manager.exp_dir} jaccard={best['phase_jaccard']:.6f} epoch={best['epoch']}", flush=True)


@torch.no_grad()
def negative_control(a, model, ckpt, head, split, feats, names):
    """空の腕で学んだ界面に、零の代わりに確定塔の予測の信号を入れても出力が変わらないか（陰性対照）。"""
    state = torch.load(ckpt, map_location="cuda")
    model.iface.load_state_dict(state["iface"])
    zero = build_data(split["val"], Signals(a.type, "empty", "val", a.inst_variant), feats, "cuda")
    real = build_data(split["val"], Signals(a.type, "pred_noCF", "val", a.inst_variant), feats, "cuda")
    rz, _ = evaluate(model, zero, names)
    rr, _ = evaluate(model, real, names)
    d = 0.0
    for (_, x, s0, m0, _), (_, _, s1, m1, _) in zip(zero, real):
        d = max(d, float((model(x, s0, m0)[-1] - model(x, s1, m1)[-1]).abs().max()))
    return {"zero_signal_jaccard": rz["phase_jaccard"], "pred_signal_jaccard": rr["phase_jaccard"],
            "max_abs_logit_diff": d, "unchanged": d == 0.0}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("identity")
    i.add_argument("--type", required=True, choices=list(TYPES))
    i.add_argument("--inst-variant", choices=["literal", "uq"], default="literal")
    i.add_argument("--perturb-scale", type=float, default=0.05)
    i.add_argument("--out", required=True)
    i.add_argument("--arm", choices=ARMS, default=None, help="一つの腕だけを調べる（既定は予測-noCF と正解）")
    i.add_argument("--task-id", default=C.TASK_ID, help="記録に書く契約の識別子")
    t = sub.add_parser("train")
    t.add_argument("--type", required=True, choices=list(TYPES))
    t.add_argument("--arm", required=True, choices=ARMS)
    t.add_argument("--seed", type=int, required=True)
    t.add_argument("--inst-variant", choices=["literal", "uq"], default=None)
    t.add_argument("--max-epochs", type=int, default=None, help="短い試走だけに使う（腕の本番では渡さない）")
    t.add_argument("--fixed-epochs", type=int, default=None,
                   help="この回数だけ止めずに学習し、最後の epoch の状態を結果にする（最良の回を選ばない）")
    t.add_argument("--task-id", default=C.TASK_ID, help="run の契約の識別子（config・notes・界面の重みの置き場）")
    t.add_argument("--exp-prefix", default="stage2pilot_dp", help="実験フォルダの名前の接頭辞")
    t.add_argument("--smoke", action="store_true", help="--fixed-epochs の短い試走の印")
    a = ap.parse_args()
    if a.cmd == "train" and a.fixed_epochs and a.max_epochs:
        raise SystemExit("--fixed-epochs と --max-epochs は組み合わせない")
    if a.cmd == "train" and a.smoke and not a.fixed_epochs:
        raise SystemExit("--smoke は --fixed-epochs と組で使う（従来の試走は --max-epochs）")
    if a.cmd == "train" and TYPES[a.type][1] == "tok" and a.inst_variant is None:
        raise SystemExit("D3 の型は --inst-variant（literal か uq）を渡す")
    {"identity": cmd_identity, "train": cmd_train}[a.cmd](a)


if __name__ == "__main__":
    main()

"""Task C: one GPU at batch 2B against two GPUs at B each, on the same frames.

    python match.py single --out <dir> [--stem-train]                     # one GPU, batch 8
    torchrun --nproc_per_node=2 --master_port=<p> match.py dual --out <dir> \
        [--no-sync-bn] [--plain-mean] [--no-deterministic]                # two GPUs, 4 each
    python match.py compare --reference <dir> --candidate <dir> [--tolerance <json>]

Both sides read the same 77 frames of fold A's train set in the same order (a fixed
permutation), without the flip (``train=False``), from the same initial weights. One epoch
of 10 micro-steps of 8 frames: the tail is 5 frames (3 / 2 over two ranks) and the last
accumulation window holds 2 micro-steps, so the updates fall at micro-steps 4, 8 and 10.

The one-GPU side repeats ``stage1_ptower_r3.finetune``'s inner loop (lines 215-224). The
two-GPU side calls ``stage1_ptower_r3_dist``'s own ``wrap``, ``shard`` and ``micro_step``.

Saved per run: the loss of every micro-step (the mean over the global batch), the gradients
at each update before ``optimizer.step``, every BatchNorm's running statistics after the
epoch, the final weights, and the determinism switches as each rank reads them.

Breaking controls: ``--no-sync-bn`` (each rank normalises its own 4 frames),
``--plain-mean`` (each rank averages its own shard, which over-weights the 2-frame tail
shard), ``--stem-train`` (the stem's bn1 trains), ``--no-deterministic`` (the switches off).

Diagnosis only: ``--float64 --per-gpu 2 --frames 22`` runs the same comparison in double precision on a
smaller batch (one GPU at 4, two GPUs at 2 each; 6 micro-steps, tail of 2 split 1 / 1,
updates at 4 and 6), to tell an implementation difference from fp32 rounding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F
from omegaconf import OmegaConf
from torch import nn

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402
import stage1_ptower_r3_dist as dp  # noqa: E402

B, WORLD, ACCUM, N, SEED, LR = 4, 2, 4, 77, 42, 0.0003
DTYPE = torch.float32


def frames():
    cfg = OmegaConf.load(ROOT / "configs/stage1_ptower_r3.yaml")
    split = base.folds()["A"]
    data = r3.FoldFrames(base.manifests(cfg), split["train"], train=False)
    order = torch.randperm(len(data), generator=torch.Generator().manual_seed(SEED))[:N].tolist()
    batches = [order[i:i + WORLD * B] for i in range(0, N, WORLD * B)]
    names = json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text())
    return data, batches, len(names)


def load(data, index, device):
    images, labels = zip(*[data[i][:2] for i in index])
    return torch.stack(images).to(device, DTYPE), torch.tensor(labels).to(device)


def model_for(classes, device):
    torch.manual_seed(SEED)
    model, _, _ = r3.build_backbone(classes, device, "coco")
    return model.to(DTYPE)


def bn_stats(model):
    return {f"{name}.{key}": getattr(m, key).detach().cpu().clone()
            for name, m in model.named_modules() if isinstance(m, nn.modules.batchnorm._BatchNorm)
            for key in ("running_mean", "running_var")}


def grads(model):
    return {n: p.grad.detach().cpu().clone() for n, p in model.named_parameters() if p.requires_grad}


def state(model):
    return {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}


def digest(tensors):
    h = hashlib.sha256()
    for k, v in sorted(tensors.items()):
        h.update(k.encode())
        h.update(v.contiguous().numpy().tobytes())
    return h.hexdigest()


def single(args):
    base.deterministic(SEED)
    device = torch.device("cuda:0")
    data, batches, classes = frames()
    model = model_for(classes, device)
    initial = {"state": state(model), "bn": bn_stats(model)}
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=LR, weight_decay=0.0001)
    ce = nn.CrossEntropyLoss()
    if args.stem_train:
        model.train()
    else:
        r3.stem_eval(model)
    losses, at_update = [], []
    optimizer.zero_grad(set_to_none=True)
    steps = len(batches)
    for step, batch in enumerate(batches, start=1):
        images, y = load(data, batch, device)
        loss = ce(model(images), y)
        (loss / ACCUM).backward()
        losses.append(float(loss))
        if step % ACCUM == 0 or step == steps:
            at_update.append(grads(model))
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
    return {"losses": losses, "grads": at_update, "bn": bn_stats(model), "state": state(model),
            "initial": initial, "determinism": [dp.determinism_state()],
            "batches": batches, "peak_bytes": [int(torch.cuda.max_memory_allocated(device))]}


def dual(args):
    if not args.no_deterministic:
        base.deterministic(SEED)
    if args.plain_mean:
        dp.scaled_loss = lambda logits, y, count, world: F.cross_entropy(logits, y)
    rank, world, device = dp.setup()
    assert world == WORLD
    data, batches, classes = frames()
    model = model_for(classes, device)
    initial = {"state": state(model), "bn": bn_stats(model)}
    ddp = dp.wrap(model, device, sync_bn=not args.no_sync_bn)
    determinism = dp.gather(dp.determinism_state())
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=LR, weight_decay=0.0001)
    ddp.train()
    r3.stem_eval(model)
    losses, at_update, shards = [], [], []
    optimizer.zero_grad(set_to_none=True)
    steps = len(batches)
    for step, batch in enumerate(batches, start=1):
        part = dp.shard(batch, rank, world)
        shards.append(part)
        images, y = load(data, part, device)
        boundary = step % ACCUM == 0 or step == steps
        total = dp.micro_step(ddp, images, y, len(batch), world, ACCUM, boundary)
        torch.distributed.all_reduce(total)
        losses.append(float(total / len(batch)))
        if boundary:
            at_update.append(grads(model))
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
    final = state(model)
    digests = dp.gather(digest(final))
    peaks = dp.gather(int(torch.cuda.max_memory_allocated(device)))
    all_shards = dp.gather(shards)
    torch.distributed.destroy_process_group()
    if rank:
        return None
    return {"losses": losses, "grads": at_update, "bn": bn_stats(model), "state": final,
            "initial": initial, "determinism": determinism, "batches": batches,
            "rank_state_sha256": digests, "rank_shards": all_shards, "peak_bytes": peaks}


def rel(a, b):
    """||a - b|| / ||a||, with 0/0 taken as 0."""
    num, den = float((a.double() - b.double()).norm()), float(a.double().norm())
    return 0.0 if num == 0 else (num / den if den else float("inf"))


def compare(args):
    ref = torch.load(Path(args.reference) / "run.pt")
    cand = torch.load(Path(args.candidate) / "run.pt")
    tol = json.loads(args.tolerance)
    loss_rel = max(abs(a - b) / abs(a) for a, b in zip(ref["losses"], cand["losses"]))
    loss_abs = max(abs(a - b) for a, b in zip(ref["losses"], cand["losses"]))
    grad_rel = [max(rel(r[n], c[n]) for n in r) for r, c in zip(ref["grads"], cand["grads"])]
    grad_abs = max(float((r[n] - c[n]).abs().max()) for r, c in zip(ref["grads"], cand["grads"]) for n in r)
    tail_grad_rel = grad_rel[-1]
    bn_keys = [k for k in ref["bn"] if not k.startswith("bn1.")]
    bn_rel = max(rel(ref["bn"][k] - ref["initial"]["bn"][k], cand["bn"][k] - cand["initial"]["bn"][k])
                 for k in bn_keys)
    bn_abs = max(float((ref["bn"][k] - cand["bn"][k]).abs().max()) for k in bn_keys)
    trainable = list(ref["grads"][0])
    w_rel = max(rel(ref["state"][n] - ref["initial"]["state"][n],
                    cand["state"][n] - cand["initial"]["state"][n]) for n in trainable)
    w_abs = max(float((ref["state"][n] - cand["state"][n]).abs().max()) for n in trainable)
    stem = {side: {k: bool(torch.equal(run["bn"][k], run["initial"]["bn"][k]))
                   for k in ("bn1.running_mean", "bn1.running_var")}
            for side, run in (("reference", ref), ("candidate", cand))}
    measured = {"loss_rel": loss_rel, "grad_rel": max(grad_rel), "bn_delta_rel": bn_rel,
                "weight_update_rel": w_rel}
    verdict = {k: measured[k] <= tol[k] for k in tol}
    report = {"measured": measured, "within": verdict, "all_within": all(verdict.values()),
              "grad_rel_per_update": grad_rel, "tail_update_grad_rel": tail_grad_rel,
              "loss_abs": loss_abs, "grad_abs": grad_abs, "bn_abs": bn_abs, "weight_abs": w_abs,
              "weight_abs_in_lr": w_abs / LR, "stem_bn1_unchanged": stem,
              "candidate_determinism": cand["determinism"],
              "candidate_rank_state_sha256": cand.get("rank_state_sha256"),
              "reference_peak_bytes": ref["peak_bytes"], "candidate_peak_bytes": cand["peak_bytes"],
              "same_batches": ref["batches"] == cand["batches"]}
    if "rank_shards" in cand:
        seen = [i for rank in cand["rank_shards"] for part in rank for i in part]
        report["rank_shards_partition"] = {
            "duplicates": len(seen) - len(set(seen)),
            "equals_batches": sorted(seen) == sorted(i for b in cand["batches"] for i in b),
            "tail_sizes": [len(rank[-1]) for rank in cand["rank_shards"]]}
    print(json.dumps(report, indent=2))
    if args.save:
        Path(args.save).write_text(json.dumps(report, indent=2) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["single", "dual", "compare"])
    ap.add_argument("--out")
    ap.add_argument("--stem-train", action="store_true")
    ap.add_argument("--no-sync-bn", action="store_true")
    ap.add_argument("--plain-mean", action="store_true")
    ap.add_argument("--no-deterministic", action="store_true")
    ap.add_argument("--reference")
    ap.add_argument("--candidate")
    ap.add_argument("--tolerance")
    ap.add_argument("--save")
    ap.add_argument("--per-gpu", type=int, default=B)
    ap.add_argument("--frames", type=int, default=N)
    ap.add_argument("--float64", action="store_true")
    args = ap.parse_args()
    globals().update(B=args.per_gpu, N=args.frames, DTYPE=torch.float64 if args.float64 else torch.float32)
    if args.mode == "compare":
        return compare(args)
    out = Path(args.out)
    assert ROOT not in out.resolve().parents, "output must live outside the repo"
    result = single(args) if args.mode == "single" else dual(args)
    if result is not None:
        out.mkdir(parents=True, exist_ok=True)
        torch.save(result, out / "run.pt")
        print(json.dumps({"out": str(out), "state_sha256": digest(result["state"]),
                          "losses": result["losses"], "determinism": result["determinism"],
                          "rank_state_sha256": result.get("rank_state_sha256"),
                          "peak_bytes": result["peak_bytes"]}))
    sys.stdout.flush()


if __name__ == "__main__":
    main()

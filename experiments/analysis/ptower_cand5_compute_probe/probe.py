"""One measurement trial of T-2026-10-23-ptower-cand5-compute-probe.

Each call measures a single (configuration, batch) and prints one JSON line.
Trials run in their own process so an OOM cannot leak fragmentation into the next.
Nothing is saved except the JSON line: no checkpoint, no experiment folder.

    python probe.py calib --batch 16
    python probe.py vit --size base --res 800 --scope full --batch 4
    python probe.py moco --batch 256
    python probe.py vmae --batch 256
    python probe.py mamba
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
GiB = 1024 ** 3
CLASSES = 9  # data/processed/phase_manifest_all_phase/phase_vocab.json
RES = {"224": (224, 224), "448": (448, 448), "800": (800, 1424)}  # 1422 padded up to 89 patches


class SmiPeak:
    """Max of nvidia-smi memory.used on the one visible GPU, sampled every 100 ms."""

    def __init__(self):
        index = os.environ.get("CUDA_VISIBLE_DEVICES", "0").split(",")[0]
        self.proc = subprocess.Popen(
            ["nvidia-smi", "-i", index, "--query-gpu=memory.used", "--format=csv,noheader,nounits",
             "-lms", "100"], stdout=subprocess.PIPE, text=True)
        self.peak = 0
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self):
        for line in self.proc.stdout:
            if line.strip().isdigit():
                self.peak = max(self.peak, int(line))

    def stop(self):
        time.sleep(0.3)
        self.proc.terminate()
        self.proc.wait()
        return self.peak


def fp32_strict():
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def sdpa_kernel(heads, tokens, head_dim, batch):
    """Which SDPA kernel PyTorch 2.1 picks for this fp32 shape (priority flash > efficient > math)."""
    q = torch.randn(batch, heads, tokens, head_dim, device="cuda", requires_grad=True)
    usable = {}
    for name, flags in (("flash", (True, False, False)), ("efficient", (False, True, False)),
                        ("math", (False, False, True))):
        try:
            with torch.backends.cuda.sdp_kernel(enable_flash=flags[0], enable_mem_efficient=flags[1],
                                                enable_math=flags[2]):
                F.scaled_dot_product_attention(q, q, q).sum().backward()
            usable[name] = True
        except RuntimeError:
            usable[name] = False
        torch.cuda.synchronize()
    del q
    torch.cuda.empty_cache()
    return next((k for k in ("flash", "efficient", "math") if usable[k]), None), usable


def timed_steps(step, warmup, steps):
    for _ in range(warmup):
        step()
    torch.cuda.synchronize()
    times = []
    for _ in range(steps):
        t0 = time.perf_counter()
        step()
        torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)
    return times


def calib(args):
    """Phase tower r3 recipe: R50, 800x1422, fp32, deterministic, stem frozen, AdamW."""
    import stage1_ptower as base
    from stage1_ptower_r3 import build_backbone, EVAL_TRANSFORM, FoldFrames
    from torch.utils.data import DataLoader
    base.deterministic(42)
    model, source, _ = build_backbone(CLASSES, "cuda", "coco")
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                  lr=3e-4, weight_decay=1e-4)
    model.train()
    for m in (model.conv1, model.bn1):
        m.eval()
    clips = [c for s in ("train", "val", "test") for c in json.loads(
        (ROOT / "data/processed/phase_manifest_all_phase" / f"{s}.json").read_text())["clips"]]
    videos = ["01", "02", "03", "06", "08", "11", "12", "13", "14", "15"]
    data = FoldFrames(clips, videos, train=True)
    loader = DataLoader(data, batch_size=args.batch, shuffle=True, num_workers=4,
                        pin_memory=True, generator=torch.Generator().manual_seed(42))  # nosemgrep
    it = iter(loader)
    load_times = []

    def next_batch():
        t0 = time.perf_counter()
        x, y, _ = next(it)
        load_times.append(time.perf_counter() - t0)
        return x, y

    queue = [next_batch() for _ in range(args.warmup + args.steps)]
    first_x = queue[0][0]
    ce = nn.CrossEntropyLoss()

    def step():
        x, y = queue.pop(0)
        x, y = x.cuda(non_blocking=True), y.cuda(non_blocking=True)
        loss = ce(model(x), y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

    return {"input_shape": list(first_x.shape), "weights": source,
            "load_seconds_per_batch_mean": sum(load_times[1:]) / max(1, len(load_times) - 1),
            "load_note": "batches are prefetched to host memory before the timed steps; "
                         "step time includes the host-to-device copy but not loading"}, step


def vit(args):
    import timm
    fp32_strict()
    name = f"vit_{args.size}_patch16_dinov3"
    h, w = RES[args.res]
    model = timm.create_model(name, pretrained=False, num_classes=CLASSES, img_size=(h, w)).cuda()
    if args.scope == "full":
        trainable = list(model.parameters())
    else:
        model.requires_grad_(False)
        parts = [model.head] if args.scope == "linear" else [*model.blocks[-4:], model.norm, model.head]
        for p in parts:
            p.requires_grad_(True)
        trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=1e-4, weight_decay=0.05)
    model.train()
    x = torch.randn(args.batch, 3, h, w, device="cuda")
    y = torch.randint(0, CLASSES, (args.batch,), device="cuda")
    ce = nn.CrossEntropyLoss()

    def step():
        if args.scope == "linear":
            with torch.no_grad():
                feats = model.forward_head(model.forward_features(x), pre_logits=True)
            loss = ce(model.head(feats), y)
        else:
            loss = ce(model(x), y)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

    tokens = (h // 16) * (w // 16)
    kernel, usable = sdpa_kernel(model.blocks[0].attn.num_heads, tokens + model.num_prefix_tokens,
                                 model.embed_dim // model.blocks[0].attn.num_heads, 1)
    extra = {"model": name, "input_hw": [h, w], "patch_tokens": tokens,
             "prefix_tokens": model.num_prefix_tokens,
             "params_total": sum(p.numel() for p in model.parameters()),
             "params_trainable": sum(p.numel() for p in trainable),
             "fused_attn": bool(model.blocks[0].attn.fused_attn),
             "sdpa_kernel": kernel, "sdpa_usable": usable}
    if args.scope == "linear":
        def extract():
            with torch.no_grad():
                model.forward_features(x)
        t = timed_steps(extract, args.warmup, args.steps)
        extra["extract_seconds_per_image"] = sum(t) / len(t) / args.batch
    return extra, step


def moco(args):
    """MoCo v2 (arXiv:2003.04297): R50, 2-layer MLP head 2048-2048-128, K=65536, m=0.999, T=0.2."""
    import torchvision
    fp32_strict()
    dim, K, m, T = 128, 65536, 0.999, 0.2

    def encoder():
        net = torchvision.models.resnet50(weights=None, num_classes=dim)
        net.fc = nn.Sequential(nn.Linear(2048, 2048), nn.ReLU(), net.fc)
        return net.cuda()

    q_enc, k_enc = encoder(), encoder()
    k_enc.load_state_dict(q_enc.state_dict())
    k_enc.requires_grad_(False)
    queue = F.normalize(torch.randn(dim, K, device="cuda"), dim=0)
    optimizer = torch.optim.SGD(q_enc.parameters(), lr=0.03, momentum=0.9, weight_decay=1e-4)
    x1 = torch.randn(args.batch, 3, 224, 224, device="cuda")
    x2 = torch.randn(args.batch, 3, 224, 224, device="cuda")
    ptr = [0]

    def step():
        q = F.normalize(q_enc(x1), dim=1)
        with torch.no_grad():
            for pq, pk in zip(q_enc.parameters(), k_enc.parameters()):
                pk.mul_(m).add_(pq.detach(), alpha=1 - m)
            k = F.normalize(k_enc(x2), dim=1)
        logits = torch.cat([(q * k).sum(1, keepdim=True), q @ queue], dim=1) / T
        loss = F.cross_entropy(logits, torch.zeros(args.batch, dtype=torch.long, device="cuda"))
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        n = k.shape[0]
        idx = (torch.arange(n, device="cuda") + ptr[0]) % K
        queue[:, idx] = k.T
        ptr[0] = (ptr[0] + n) % K

    return {"queue_K": K, "dim": dim, "momentum": m, "temperature": T, "crop": 224,
            "shuffle_bn": "not reproduced (single GPU)"}, step


def vmae(args):
    """VideoMAE-style: ViT-S/16 encoder on visible tubes only, small decoder, tube mask 0.90."""
    from timm.models.vision_transformer import Block
    fp32_strict()
    frames, tubelet, size, patch, ratio = 10, 2, 224, 16, 0.90
    enc_dim, enc_depth, enc_heads = 384, 12, 6
    dec_dim, dec_depth, dec_heads = 192, 4, 3
    n_sp = (size // patch) ** 2
    n = (frames // tubelet) * n_sp
    keep = int(round(n * (1 - ratio)))
    pdim = 3 * tubelet * patch * patch

    class VideoMAE(nn.Module):
        def __init__(self):
            super().__init__()
            self.embed = nn.Conv3d(3, enc_dim, (tubelet, patch, patch), (tubelet, patch, patch))
            self.pos = nn.Parameter(torch.zeros(1, n, enc_dim))
            self.enc = nn.Sequential(*[Block(enc_dim, enc_heads) for _ in range(enc_depth)])
            self.enc_norm = nn.LayerNorm(enc_dim)
            self.to_dec = nn.Linear(enc_dim, dec_dim)
            self.mask_token = nn.Parameter(torch.zeros(1, 1, dec_dim))
            self.dec_pos = nn.Parameter(torch.zeros(1, n, dec_dim))
            self.dec = nn.Sequential(*[Block(dec_dim, dec_heads) for _ in range(dec_depth)])
            self.dec_norm = nn.LayerNorm(dec_dim)
            self.pred = nn.Linear(dec_dim, pdim)

        def forward(self, video, vis_idx, mask_idx):
            b = video.shape[0]
            tok = self.embed(video).flatten(2).transpose(1, 2) + self.pos
            vis = torch.gather(tok, 1, vis_idx[..., None].expand(-1, -1, enc_dim))
            z = self.to_dec(self.enc_norm(self.enc(vis)))
            pos = self.dec_pos.expand(b, -1, -1)
            z = z + torch.gather(pos, 1, vis_idx[..., None].expand(-1, -1, dec_dim))
            m = self.mask_token + torch.gather(pos, 1, mask_idx[..., None].expand(-1, -1, dec_dim))
            out = self.dec(torch.cat([z, m], 1))
            return self.pred(self.dec_norm(out[:, -mask_idx.shape[1]:]))

    model = VideoMAE().cuda()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1.5e-4, weight_decay=0.05)
    video = torch.randn(args.batch, 3, frames, size, size, device="cuda")
    # tube mask: the same spatial positions are hidden in every temporal slot
    sp_keep = torch.rand(args.batch, n_sp, device="cuda").argsort(1)[:, :keep // (frames // tubelet)]
    vis = (sp_keep[:, None, :] + n_sp * torch.arange(frames // tubelet, device="cuda")[None, :, None]).flatten(1)
    hidden = torch.ones(args.batch, n, dtype=torch.bool, device="cuda")
    hidden.scatter_(1, vis, False)
    mask_idx = hidden.nonzero()[:, 1].view(args.batch, -1)
    target = torch.randn(args.batch, mask_idx.shape[1], pdim, device="cuda")

    def step():
        loss = F.mse_loss(model(video, vis, mask_idx), target)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

    return {"frames": frames, "tubelet": tubelet, "tokens_total": n, "tokens_visible": vis.shape[1],
            "mask": "tube", "mask_ratio_actual": 1 - vis.shape[1] / n,
            "encoder": f"ViT-S/16 dim{enc_dim} depth{enc_depth}",
            "decoder": f"dim{dec_dim} depth{dec_depth} heads{dec_heads}",
            "params_total": sum(p.numel() for p in model.parameters())}, step


def mamba_run(deterministic, perturb):
    """Forward and backward of a 2-layer selective SSM on one 1,400 x 2048 sequence (seed 42)."""
    import stage1_ptower as base
    from mamba_ssm import Mamba
    if deterministic:
        base.deterministic(42)
    else:
        torch.use_deterministic_algorithms(False)
        torch.backends.cudnn.deterministic = False
        torch.manual_seed(42)
    net = nn.Sequential(nn.Linear(2048, 512),
                        *[Mamba(d_model=512, d_state=64, d_conv=4, expand=2) for _ in range(2)],
                        nn.Linear(512, CLASSES)).cuda()
    x = torch.randn(1, 1400, 2048, device="cuda")
    if perturb:
        x = x + 1e-3
    out = net(x)
    out.square().mean().backward()
    torch.cuda.synchronize()
    return out.detach().cpu(), torch.cat([p.grad.flatten() for p in net.parameters()]).cpu()


def mamba(args):
    import mamba_ssm.modules.mamba_simple as ms
    rows = {}
    for label, det, perturb in (("same_seed_deterministic", True, False),
                                ("same_seed_nondeterministic", False, False),
                                ("positive_control_nondet_plus_1e-3", False, True)):
        try:
            o1, g1 = mamba_run(det, False)
            o2, g2 = mamba_run(det, perturb)
            rows[label] = {"out_max_abs_diff": float((o1 - o2).abs().max()),
                           "grad_max_abs_diff": float((g1 - g2).abs().max()),
                           "out_bitwise_equal": bool(torch.equal(o1, o2)),
                           "grad_bitwise_equal": bool(torch.equal(g1, g2))}
        except Exception as e:  # record, do not hide
            rows[label] = {"error": repr(e)}
    return {"causal_conv1d_fn_used": ms.causal_conv1d_fn is not None,
            "selective_scan_cuda_used": getattr(ms, "selective_state_update", None) is not None,
            "model": "Linear 2048-512, 2 x Mamba(d_model 512, d_state 64, d_conv 4, expand 2), Linear 512-9",
            "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["calib", "vit", "moco", "vmae", "mamba"])
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--size", choices=["base", "large"])
    ap.add_argument("--res", choices=list(RES))
    ap.add_argument("--scope", choices=["full", "top4", "linear"])
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--steps", type=int, default=10)
    args = ap.parse_args()
    record = {"kind": args.kind, "batch": args.batch, "size": args.size, "res": args.res,
              "scope": args.scope, "warmup": args.warmup, "steps": args.steps,
              "precision": "fp32 (TF32 off)",
              "PYTORCH_CUDA_ALLOC_CONF": os.environ.get("PYTORCH_CUDA_ALLOC_CONF", ""),
              "expandable_segments": "expandable_segments:True" in os.environ.get(
                  "PYTORCH_CUDA_ALLOC_CONF", ""),
              "device": torch.cuda.get_device_name(0)}
    smi = SmiPeak()
    try:
        if args.kind == "mamba":
            record.update(mamba(args))
            record["status"] = "ok"
        else:
            extra, step = {"calib": calib, "vit": vit, "moco": moco, "vmae": vmae}[args.kind](args)
            record.update(extra)
            torch.cuda.reset_peak_memory_stats()
            times = timed_steps(step, args.warmup, args.steps)
            record.update(status="ok", step_seconds_mean=sum(times) / len(times),
                          step_seconds_min=min(times), step_seconds_max=max(times),
                          peak_allocated_gib=torch.cuda.max_memory_allocated() / GiB,
                          peak_reserved_gib=torch.cuda.max_memory_reserved() / GiB)
    except torch.cuda.OutOfMemoryError as e:
        record.update(status="oom", error=str(e).splitlines()[0][:300],
                      peak_allocated_gib=torch.cuda.max_memory_allocated() / GiB,
                      peak_reserved_gib=torch.cuda.max_memory_reserved() / GiB)
    record["nvidia_smi_peak_gib"] = smi.stop() / 1024
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()

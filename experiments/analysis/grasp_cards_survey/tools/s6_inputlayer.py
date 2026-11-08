"""S6-2 工程塔の入力層を 8 チャネルにした写しで、順伝播と逆伝播の形を確かめる（T-2026-11-08-grasp-cards-survey）。

本体の .venv。**学習しない。optimizer を作らず、step を呼ばない。重みを保存しない。** 既存の台本は変えない。

- 写し: torchvision resnet50(IMAGENET1K_V1、手元の hub の写し) の conv1 を (64, 8, 7, 7) に置き換え、RGB の 3 チャネルは
  ImageNet の重みのまま、追加の 5 チャネルは 0。fc は 9 工程。前処理は stage1_ptower_r3.EVAL_TRANSFORM（短辺 800）
- 入力: val の動画 09 の先頭 2 フレーム（RGB）に、seed 42 の一様乱数のマスク 5 チャネルを連結した (2, 8, 800, 1422)
- 二つの設定で逆伝播:
    (a) 台本どおり stem（conv1・bn1）を凍結 → conv1 の勾配は無い
    (b) conv1 を学ぶ設定にし、RGB の 3 チャネル分の勾配を hook で 0 にする → 追加の 5 チャネルにだけ勾配
- BN の統計を動かさないため eval で回す（形の確認が目的。学習時の train の挙動は確かめていない）
- 対照: 追加チャネルが 0 なので、8 チャネルの写しの出力は 3 チャネルの元の出力と一致するはず。7 チャネルの入力は形の不一致で止まるはず
- 重みと buffer の要約値を前後で比べる

    .venv/bin/python s6_inputlayer.py --out <STORE/c/s6/s6_record.json>
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))


def digest(model):
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import torch
    from torch import nn
    from torchvision.models import ResNet50_Weights, resnet50

    import stage1_ptower_r3 as r3
    from stage2pilot import common as C
    torch.manual_seed(42)
    dev = "cuda:0"
    clips = json.loads((C.MANIFEST_DIR / "val.json").read_text())["clips"]
    ds = r3.FoldFrames(clips, ["09"], train=False)
    frames = [ds.frames[i]["frame"] for i in range(2)]
    C.assert_no_test(frames, "s6_inputlayer")
    rgb = torch.stack([ds[i][0] for i in range(2)])
    y = torch.tensor([ds[i][1] for i in range(2)])
    gen = torch.Generator().manual_seed(42)
    masks = torch.rand((2, 5) + tuple(rgb.shape[2:]), generator=gen)
    x8 = torch.cat([rgb, masks], 1).to(dev)
    x3 = rgb.to(dev)
    y = y.to(dev)

    base3 = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)
    base3.fc = nn.Linear(2048, 9)
    m8 = copy.deepcopy(base3)
    old = m8.conv1.weight.data
    conv = nn.Conv2d(8, 64, kernel_size=7, stride=2, padding=3, bias=False)
    with torch.no_grad():
        conv.weight.zero_()
        conv.weight[:, :3] = old
    m8.conv1 = conv
    base3, m8 = base3.to(dev).eval(), m8.to(dev).eval()
    rec = {"task_id": "T-2026-11-08-grasp-cards-survey", "frames": frames, "read_videos": ["09"],
           "init": str(ResNet50_Weights.IMAGENET1K_V1), "input_8ch_shape": list(x8.shape),
           "conv1_weight_shape_3ch": list(base3.conv1.weight.shape), "conv1_weight_shape_8ch": list(m8.conv1.weight.shape),
           "optimizer_created": False, "optimizer_step_called": False, "mode": "eval（BN の統計を動かさない）"}
    with torch.no_grad():
        o3 = base3(x3)
        o8 = m8(x8)
    rec["control_zero_extra_channels_max_abs_logit_diff"] = float((o3 - o8).abs().max())
    d0 = digest(m8)
    ce = nn.CrossEntropyLoss()

    # (a) 台本どおり stem を凍結
    for mod in (m8.conv1, m8.bn1):
        mod.requires_grad_(False)
    torch.cuda.reset_peak_memory_stats(dev)
    loss = ce(m8(x8), y)
    loss.backward()
    rec["a_stem_frozen"] = {
        "loss": float(loss), "conv1_grad_is_none": m8.conv1.weight.grad is None,
        "layer1_grad_nonzero": bool(any(p.grad is not None and p.grad.abs().sum() > 0 for p in m8.layer1.parameters())),
        "peak_memory_bytes": int(torch.cuda.max_memory_allocated(dev))}
    m8.zero_grad(set_to_none=True)

    # (b) conv1 を学ぶ設定。RGB の 3 チャネルの勾配を 0 にする hook
    m8.conv1.weight.requires_grad_(True)
    keep = torch.zeros_like(m8.conv1.weight)
    keep[:, 3:] = 1
    handle = m8.conv1.weight.register_hook(lambda g: g * keep)
    loss = ce(m8(x8), y)
    loss.backward()
    g = m8.conv1.weight.grad
    rec["b_extra_channels_only"] = {
        "loss": float(loss), "grad_shape": list(g.shape), "rgb_grad_abs_sum": float(g[:, :3].abs().sum()),
        "extra_grad_abs_sum": float(g[:, 3:].abs().sum()), "extra_grad_nonzero_elements": int((g[:, 3:] != 0).sum()),
        "extra_elements": int(g[:, 3:].numel())}
    handle.remove()
    m8.zero_grad(set_to_none=True)
    d1 = digest(m8)
    rec["weights_digest_before"], rec["weights_digest_after"], rec["weights_unchanged"] = d0, d1, d0 == d1

    # 対照: 7 チャネルの入力
    try:
        with torch.no_grad():
            m8(x8[:, :7])
        rec["control_7ch"] = {"raised": False}
    except RuntimeError as exc:
        rec["control_7ch"] = {"raised": True, "error": str(exc).splitlines()[0][:300]}

    # 参考: 順伝播と逆伝播 1 回の時間（batch 2、eval、5 回の中央）。3 チャネルの元と 8 チャネルの写し
    def step_time(model, x):
        ts = []
        for i in range(6):
            torch.cuda.synchronize(); t0 = time.perf_counter()
            ce(model(x), y).backward()
            torch.cuda.synchronize()
            if i:
                ts.append(time.perf_counter() - t0)
            model.zero_grad(set_to_none=True)
        return float(np.median(ts))
    rec["fwd_bwd_seconds_batch2_3ch"] = step_time(base3, x3)
    rec["fwd_bwd_seconds_batch2_8ch_conv1_trainable"] = step_time(m8, x8)
    rec["weights_unchanged_after_timing"] = digest(m8) == d0
    rec["gpu"] = torch.cuda.get_device_name(0)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()

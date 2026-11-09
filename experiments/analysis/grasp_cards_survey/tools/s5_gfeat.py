"""S5 把持塔の中間特徴（T-2026-11-08-grasp-cards-survey、SPEC §2 S5）。本体の .venv。学習しない。重みは読むだけ。

G（mmdet Mask2Former R50、把持関係 5 クラス）を g5_signals.load_model で読み、g5_signals.infer と同じ前処理
（G38(train=False)・to_inputs）で val の 100 フレーム（09・10 の工程の経路のフレームから seed 42 で選ぶ）を通す。
マスクの出力（mask_embed と mask_features の積）より前の層から 4 つの候補を取る:

  backbone_C5            model.backbone の最後の段の出力           (2048, H/32, W/32)
  pixdec_mask_features   panoptic_head.pixel_decoder の第 1 の出力  (256, H/4, W/4)
  pixdec_memory_coarse   pixel_decoder の第 2 の出力の [0]（最も粗い）(256, H/32, W/32)
  decoder_last_query     transformer_decoder.layers[-1] の出力（post_norm の前） (100 query, 256)

同じフレームで、確定（all）・確定の別の読み込み（all2、同じ重み）・H1・H2 の同じ層の特徴を取り、次元ごとの
Pearson 相関（全フレームの全位置、query は全フレームの全 query）を数える。all と all2 が対照（相関 1）。
次元の入れ替えを見るため、相関の行列（C×C）から、確定の各次元に対する相手の全次元のうちの最大の |r| も記録する。

時間は batch 1、torch.cuda.synchronize で区切る: backbone、pixel decoder、頭の全体（pixel decoder を含む）。

    .venv/bin/python s5_gfeat.py --out <STORE/c/s5/s5_record.json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
GS = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/g/ckpt")
SHA = {"all": "5ea2cbf479254d78330664415e639929a86f704e5fe8b5ac8a485c7d3d9964d1",
       "H1": "5cfa055cbc72329ca1eb8f0bd8a487b64af8eaa88daac5657067cba7b9cd17c7",
       "H2": "efdefccd4484fc6af0238e14044c89ec3010a83744db455734a019702377098b"}
CANDS = ["backbone_C5", "pixdec_mask_features", "pixdec_memory_coarse", "decoder_last_query"]


def state_digest(model):
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


class Acc:
    """N×C の特徴の対 (X, Y) から、平均・分散・相互の積の和を float64 で足し込む。"""

    def __init__(self, c, dev):
        self.n = 0
        self.sx = torch.zeros(c, dtype=torch.float64, device=dev)
        self.sy = torch.zeros_like(self.sx)
        self.sxx = torch.zeros_like(self.sx)
        self.syy = torch.zeros_like(self.sx)
        self.sxy = torch.zeros(c, c, dtype=torch.float64, device=dev)

    def add(self, x, y):
        x, y = x.double(), y.double()
        self.n += x.shape[0]
        self.sx += x.sum(0)
        self.sy += y.sum(0)
        self.sxx += (x * x).sum(0)
        self.syy += (y * y).sum(0)
        self.sxy += x.T @ y

    def corr(self):
        n = self.n
        mx, my = self.sx / n, self.sy / n
        vx, vy = self.sxx / n - mx ** 2, self.syy / n - my ** 2
        cov = self.sxy / n - mx[:, None] * my[None, :]
        den = torch.sqrt(vx.clamp_min(0))[:, None] * torch.sqrt(vy.clamp_min(0))[None, :]
        r = cov / den
        dead = int(((vx <= 1e-20) | (vy <= 1e-20)).sum())
        return r.cpu().numpy(), dead


def flat(name, t):
    """候補の特徴を (位置, チャネル) にする。"""
    if name == "decoder_last_query":
        return t.reshape(-1, t.shape[-1])                 # (B*Q, 256)
    return t.permute(0, 2, 3, 1).reshape(-1, t.shape[1])  # (B*H*W, C)


def q(x):
    x = np.asarray(x, np.float64)
    x = x[np.isfinite(x)]
    return {"n": int(len(x)), "min": float(x.min()), "p5": float(np.percentile(x, 5)), "p25": float(np.percentile(x, 25)),
            "median": float(np.median(x)), "p75": float(np.percentile(x, 75)), "p95": float(np.percentile(x, 95)),
            "max": float(x.max()), "mean": float(x.mean())}


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=100)
    a = ap.parse_args()
    from grasppilot.g5_signals import frame_images, load_model
    from grasppilot.g_train import G38, collate, to_inputs
    from stage2pilot import common as C
    vids = C.fold_a()["val"]
    seqs = {v: fr for v, fr, _ in C.phase_sequences(vids)}
    stems = [f for v in vids for f in seqs[v]]
    rng = np.random.default_rng(42)
    stems = [stems[i] for i in sorted(rng.choice(len(stems), a.frames, replace=False).tolist())]
    read_videos = C.assert_no_test(stems, "s5_gfeat")
    ds = G38({"images": frame_images("val", stems), "annotations": []}, train=False)
    loader = torch.utils.data.DataLoader(ds, batch_size=1, shuffle=False, num_workers=2, collate_fn=collate)
    models, info, before = {}, {}, {}
    for key, g in (("all", "all"), ("all2", "all"), ("H1", "H1"), ("H2", "H2")):
        p = GS / g / "best.pth"
        m, inf = load_model(p, 5)
        assert inf["ckpt_sha256"] == SHA[g], (key, inf)
        assert inf.get("task_id") == "T-2026-11-05-grasp-tower-rebuild"
        models[key], info[key], before[key] = m, inf, state_digest(m)
    grab = {}
    for key, m in models.items():
        head = m.panoptic_head
        head.pixel_decoder.register_forward_hook(lambda mod, i, o, k=key: grab.__setitem__((k, "pd"), o))
        head.transformer_decoder.layers[-1].register_forward_hook(lambda mod, i, o, k=key: grab.__setitem__((k, "q"), o))
    pairs = [("all", "all2"), ("all", "H1"), ("all", "H2"), ("H1", "H2")]
    acc = {}
    shapes, times = {}, {k: {"backbone": [], "pixel_decoder": [], "head_full": []} for k in models}
    input_shape = None
    for bi, batch in enumerate(loader):
        feats = {}
        for key, m in models.items():
            inputs, samples = to_inputs(m, batch, training=False)
            input_shape = list(inputs.shape[1:])
            torch.cuda.synchronize(); t0 = time.perf_counter()
            x = m.backbone(inputs)
            torch.cuda.synchronize(); t1 = time.perf_counter()
            m.panoptic_head.pixel_decoder(x)
            torch.cuda.synchronize(); t2 = time.perf_counter()
            m.panoptic_head(x, samples)
            torch.cuda.synchronize(); t3 = time.perf_counter()
            if bi:
                times[key]["backbone"].append(t1 - t0)
                times[key]["pixel_decoder"].append(t2 - t1)
                times[key]["head_full"].append(t3 - t2)
            mf, msm = grab[(key, "pd")]
            feats[key] = {"backbone_C5": x[-1], "pixdec_mask_features": mf, "pixdec_memory_coarse": msm[0],
                          "decoder_last_query": grab[(key, "q")]}
        for name in CANDS:
            shapes[name] = list(feats["all"][name].shape[1:])
            for p1, p2 in pairs:
                X, Y = flat(name, feats[p1][name]), flat(name, feats[p2][name])
                if (name, p1, p2) not in acc:
                    acc[(name, p1, p2)] = Acc(X.shape[1], X.device)
                acc[(name, p1, p2)].add(X, Y)
    after = {k: state_digest(m) for k, m in models.items()}
    res = {"task_id": "T-2026-11-08-grasp-cards-survey", "frames": len(stems), "frame_names": stems,
           "read_videos": read_videos, "input_chw_after_preprocess": input_shape,
           "models": {k: {"ckpt": v["ckpt"], "sha256": v["ckpt_sha256"], "epoch": v.get("epoch")} for k, v in info.items()},
           "weights_unchanged": {k: before[k] == after[k] for k in models},
           "candidates": {}, "correlation": {}}
    for name in CANDS:
        sh = shapes[name]
        bb = np.median(times["all"]["backbone"])
        pd = np.median(times["all"]["pixel_decoder"])
        hf = np.median(times["all"]["head_full"])
        upto = {"backbone_C5": bb, "pixdec_mask_features": bb + pd, "pixdec_memory_coarse": bb + pd,
                "decoder_last_query": bb + hf}[name]
        res["candidates"][name] = {"shape_per_frame": sh, "channels": sh[-1] if name == "decoder_last_query" else sh[0],
                                   "spatial": None if name == "decoder_last_query" else sh[1:],
                                   "bytes_fp32_per_frame": int(np.prod(sh)) * 4,
                                   "seconds_per_frame_up_to_layer_median": float(upto)}
        res["correlation"][name] = {}
        for p1, p2 in pairs:
            r, dead = acc[(name, p1, p2)].corr()
            d = np.diag(r)
            best = np.nanmax(np.abs(r), axis=1)
            res["correlation"][name][f"{p1}_vs_{p2}"] = {
                "matched_dim_r": q(d), "matched_dim_abs_r_over_0.9": int((np.abs(d) > 0.9).sum()),
                "matched_dim_abs_r_under_0.3": int((np.abs(d) < 0.3).sum()),
                "best_any_dim_abs_r": q(best), "dims": int(len(d)), "dead_dims": dead, "positions": acc[(name, p1, p2)].n}
    res["times_seconds_median"] = {k: {s: float(np.median(v)) for s, v in t.items()} for k, t in times.items()}
    res["times_n"] = len(times["all"]["backbone"])
    res["gpu"] = torch.cuda.get_device_name(0)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    show = {k: v for k, v in res.items() if k != "frame_names"}
    print(json.dumps(show, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()

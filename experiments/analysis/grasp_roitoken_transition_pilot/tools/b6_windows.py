"""Task B-5（T-2026-11-09-grasp-roitoken-transition-pilot）。案 5 の窓の列を作る。本体の .venv。学習しない。

時刻: フレーム名 '<動画>_<クリップ>_<番号>' の番号は 0.5 fps の通し番号で、時刻 = 番号 × 2 秒（PR 302 S3）。
G の出力の最小の間隔: 同じクリップの中で隣り合う術具注釈フレームの番号の差の最小 × 2 秒（Δ と同じなら間隔の水準を落とす）。
境: 工程の目録の順で隣り合うフレームが、クリップが違うか、間隔が Δ = 2 秒を超える所（SPEC §3.3 の定義どおり）。境で窓を切る。
窓: 時刻 t の過去 L 秒（L ∈ {8, 32}）を k = L/Δ 個の時点 t, t−Δ, …, t−(k−1)Δ に置く（時点 0 が t）。時点にフレームが在り、
    t との間に境が無ければその G の出力、無ければ 0 と「無し」の印。k = 1 は S_1。

腕ごとの各時点の添字（G の地図の行）:
    S_W       自分の過去のフレーム
    S_W-perm  窓の中の在る時点の中身の順を並べ替え（印の並びと相対時刻は元のまま）。np.random.default_rng(42) を
              フレームの順に引き、在る時点が 2 個以上の窓では恒等でない並べ替えを引き直す
    S_W-R     S_W の各時点のフレームを目録の mapping で別のフレームに置き換える（b4 の shuffle_idx）
    S_W-U     S_W と同じ添字。地図を器具の 3 チャネルの画素ごとの最大を 1 チャネル目に置き、他を 0 にした地図にする
    正解      S_W と同じ添字で正解の把持の地図（注釈の無いフレームの時点は「無し」）

時点ごとの入力:
    (a) 5 チャネルの地図（round(p × 255) / 255）を 8×8 に適応平均で縮めた 320 次元
    (b) 変化の特徴 39 次元: クラスごとの面積（マスクの画素の割合）5・重心（x, y、正規化）10、
        窓の中の一つ前（時刻が一つ前）の時点とのクラスごとの IoU 5、器具の 3 クラスの間の重なりの移り 3×3（前の時点のクラス i と
        この時点のクラス j の IoU）9、出現 5（前に無く今在る）・消失 5（前に在り今無い）。前の時点が無い（窓の最後か「無し」）なら
        後半の 24 次元は 0。マスクは地図の値 ≥ 128
    並べ替えと入れ替えの腕では、(b) の前の時点は並べ替え・入れ替えの後の窓の中の一つ前の時点

対照: 窓を境の外へ伸ばした写し（境を無視して工程の目録の順に過去のフレームを入れる）で時点の数が変わる。

    .venv/bin/python b6_windows.py --box-dir <S>/b4 --out-dir <S>/seq
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402

DELTA = 2.0
LS = (8, 32)
THR = 128
TOOLS = [0, 1, 2]
BATCH = 512


def parse(f):
    v, c, n = str(f).split("_")
    return v, int(c), int(n)


def segments(frames):
    """境の印: start[i] = True ならフレーム i の前に境がある。最小の間隔も返す。"""
    start = np.ones(len(frames), bool)
    gaps = []
    for i in range(1, len(frames)):
        (v0, c0, n0), (v1, c1, n1) = parse(frames[i - 1]), parse(frames[i])
        if v0 == v1 and c0 == c1:
            gaps.append((n1 - n0) * DELTA)
            start[i] = (n1 - n0) * DELTA > DELTA
    return start, gaps


def window_idx(start, k, cut=True):
    n = len(start)
    idx = -np.ones((n, k), np.int64)
    for i in range(n):
        idx[i, 0] = i
        j = i
        for s in range(1, k):
            if cut and start[j]:
                break
            j -= 1
            if j < 0:
                break
            idx[i, s] = j
    return idx


def perm_idx(idx, seed=42):
    rng = np.random.default_rng(seed)
    out = idx.copy()
    changed = multi = 0
    for i in range(len(idx)):
        pos = np.where(idx[i] >= 0)[0]
        if len(pos) < 2:
            continue
        multi += 1
        for _ in range(100):
            p = rng.permutation(len(pos))
            if (p != np.arange(len(pos))).any():
                break
        out[i, pos] = idx[i, pos[p]]
        changed += int((out[i] != idx[i]).any())
    return out, {"windows_with_2plus": multi, "windows_changed": changed}


class Maps:
    """地図（N, 5, 270, 480）uint8 を GPU に置き、行の添字で (a) と (b) の部品を作る。"""

    def __init__(self, path, union=False, valid=None):
        m = torch.from_numpy(np.load(path, mmap_mode="r")[:]).cuda()
        if union:
            u = m[:, TOOLS].amax(1, keepdim=True)
            m = torch.cat([u, torch.zeros_like(m[:, 1:])], 1)
        self.m = m
        self.valid = None if valid is None else torch.from_numpy(valid).cuda()
        n = m.shape[0]
        self.a = torch.zeros(n, 320, device="cuda")
        self.area = torch.zeros(n, 5, device="cuda")
        self.cent = torch.zeros(n, 10, device="cuda")
        ys = torch.linspace(0.5, 269.5, 270, device="cuda") / 270
        xs = torch.linspace(0.5, 479.5, 480, device="cuda") / 480
        for s in range(0, n, 256):
            x = m[s:s + 256].float() / 255
            self.a[s:s + 256] = F.adaptive_avg_pool2d(x, 8).reshape(x.shape[0], -1)
            mk = (m[s:s + 256] >= THR).float()
            ar = mk.sum((2, 3))
            self.area[s:s + 256] = ar / (270 * 480)
            cy = (mk.sum(3) * ys).sum(2) / ar.clamp(min=1)
            cx = (mk.sum(2) * xs).sum(2) / ar.clamp(min=1)
            self.cent[s:s + 256] = torch.stack([cx, cy], -1).reshape(-1, 10)

    def pair(self, cur, prev):
        """cur, prev: 行の添字（同じ長さ）。IoU 5、3×3、出現 5、消失 5。"""
        a = self.m[cur] >= THR
        b = self.m[prev] >= THR
        inter = (a & b).flatten(2).sum(-1).float()
        union = (a | b).flatten(2).sum(-1).float()
        iou = inter / union.clamp(min=1)
        at, bt = a[:, TOOLS].flatten(2).float(), b[:, TOOLS].flatten(2).float()
        cross = torch.einsum("npx,nqx->npq", bt, at)
        un = bt.sum(-1)[:, :, None] + at.sum(-1)[:, None, :] - cross
        ov = (cross / un.clamp(min=1)).reshape(-1, 9)
        pa, pb = a.flatten(2).any(-1).float(), b.flatten(2).any(-1).float()
        return torch.cat([iou, ov, pa * (1 - pb), (1 - pa) * pb], 1)


def build(maps, idx):
    """idx (N, k) の行の添字（−1 は無し）→ (a) (N, k, 320)、(b) (N, k, 39)、印 (N, k)。"""
    n, k = idx.shape
    t = torch.from_numpy(idx).cuda()
    flag = t >= 0
    if maps.valid is not None:
        flag &= maps.valid[t.clamp(min=0)]
    safe = t.clamp(min=0)
    fa = maps.a[safe] * flag[..., None]
    fb = torch.zeros(n, k, 39, device="cuda")
    fb[..., :5] = maps.area[safe] * flag[..., None]
    fb[..., 5:15] = maps.cent[safe] * flag[..., None]
    if k > 1:
        cur, prev = safe[:, :-1].reshape(-1), safe[:, 1:].reshape(-1)
        ok = (flag[:, :-1] & flag[:, 1:]).reshape(-1)
        pf = torch.zeros(cur.shape[0], 24, device="cuda")
        for s in range(0, cur.shape[0], BATCH):
            sel = ok[s:s + BATCH]
            if sel.any():
                c, p = cur[s:s + BATCH][sel], prev[s:s + BATCH][sel]
                block = torch.zeros(sel.shape[0], 24, device="cuda")
                block[sel] = maps.pair(c, p)
                pf[s:s + BATCH] = block
        fb[:, :-1, 15:] = pf.reshape(n, k - 1, 24)
    return fa.half().cpu().numpy(), fb.half().cpu().numpy(), flag.cpu().numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rec4 = json.loads((Path(a.box_dir) / "b4_record.json").read_text())
    rec = {"task_id": "T-2026-11-09-grasp-roitoken-transition-pilot", "delta_seconds": DELTA, "L_seconds": list(LS),
           "parts": {}}
    for part in ("train", "val"):
        frames = [str(f) for f in np.load(Path(a.box_dir) / f"frame_ids_{part}.npy")]
        C.assert_no_test(frames, "b6_windows")
        start, gaps = segments(frames)
        sidx = np.load(Path(a.box_dir) / f"shuffle_idx_{part}.npy")
        has_gt = np.load(Path(a.box_dir) / f"has_gt_{part}.npy")
        pred_path = rec4["parts"][part]["pred_source"]["maps"]
        gt_path = rec4["parts"][part]["gt"]["maps"]
        seg_len = np.diff(np.r_[np.where(start)[0], len(frames)])
        prt = {"frames": len(frames), "min_interval_seconds": min(gaps), "interval_equals_delta": min(gaps) == DELTA,
               "gaps_over_delta": int(sum(g > DELTA for g in gaps)), "boundaries": int(start.sum()),
               "clip_or_video_starts": int(sum(1 for i in range(len(frames))
                                               if i == 0 or parse(frames[i])[:2] != parse(frames[i - 1])[:2])),
               "segment_length": {"n": len(seg_len), "min": int(seg_len.min()), "median": float(np.median(seg_len)),
                                  "max": int(seg_len.max())}, "arms": {}}
        sources = {"pred": None, "U": None, "gt": None}
        for k in (1,) + tuple(L // int(DELTA) for L in LS):
            idx = window_idx(start, k)
            ext = window_idx(start, k, cut=False)
            np.save(out / f"idx_k{k}_{part}.npy", idx)
            prt[f"k{k}"] = {"filled_slots": int((idx >= 0).sum()), "filled_slots_extended": int((ext >= 0).sum()),
                            "control_extended_changes_count": int((idx >= 0).sum()) != int((ext >= 0).sum()),
                            "windows_full": int((idx >= 0).all(1).sum())}
        arms = {}
        for k in (4, 16):
            idx = np.load(out / f"idx_k{k}_{part}.npy")
            p, pst = perm_idx(idx)
            prt[f"k{k}"]["perm"] = pst
            sh = np.where(idx >= 0, sidx[idx.clip(min=0)], -1)
            arms.update({f"SW_k{k}": ("pred", idx), f"SWperm_k{k}": ("pred", p), f"SWR_k{k}": ("pred", sh),
                         f"SWU_k{k}": ("U", idx), f"GT_k{k}": ("gt", idx)})
        arms["S1_k1"] = ("pred", np.load(out / f"idx_k1_{part}.npy"))
        for name, (src, idx) in sorted(arms.items(), key=lambda kv: kv[1][0]):
            if sources.get(src) is None:
                for other in [s for s in sources if s != src]:
                    sources[other] = None
                torch.cuda.empty_cache()
                sources[src] = (Maps(pred_path, union=True) if src == "U" else
                                Maps(gt_path, valid=has_gt) if src == "gt" else Maps(pred_path))
            fa, fb, flag = build(sources[src], idx)
            np.savez(out / f"seq_{name}_{part}.npz", a=fa, b=fb, flag=flag, idx=idx)
            prt["arms"][name] = {"source": src, "shape_a": list(fa.shape), "shape_b": list(fb.shape),
                                 "filled": int(flag.sum()), "sha256": C.sha256(out / f"seq_{name}_{part}.npz")}
            print(part, name, prt["arms"][name], flush=True)
        for s in list(sources):
            sources[s] = None
        torch.cuda.empty_cache()
        rec["parts"][part] = prt
    C.write_json(out / "b6_record.json", rec)
    print(json.dumps({p: {k: v for k, v in r.items() if k != "arms"} for p, r in rec["parts"].items()}, ensure_ascii=False,
                     indent=1))


if __name__ == "__main__":
    main()

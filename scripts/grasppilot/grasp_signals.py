"""把持の信号を作る関数（非公式 T-2026-10-31-grasp-pilot-probe、SPEC §3）。

正解（0 と 1 のマスク）にも、二本目の契約の G の出力（画素ごとの確率）にも当てられる形にする。
入力は「チャネル名 → (H, W) の float 配列（値は 0〜1）」の辞書。チャネル名:
    hand_L, hand_R          自分の左手・右手（g では把持関係 5 クラスの 1・2、地図 m では手 4 クラスの 1・2）
    tool_L, tool_R, tool_B  左手が扱う器具、右手が扱う器具、両手で扱う器具（把持関係 5 クラスの 3・4・5）

    存在 = 画素の値の最大、面積 = 値の和 ÷ 画像の画素数、重心 = 値で重みを付けた画素の中心の平均 ÷ 幅・高さ
    （0 と 1 のマスクでは「画素がある」「画素数 ÷ 画素数」「画素の中心の平均」に一致する。対象が無ければ重心は 0）

numpy と pycocotools だけを使う（両方の仮想環境で動く）。
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HTS = ROOT / "data/annotations/egosurgery_hts"
G_NAMES = ["L_hand", "L_grasp", "L_area", "L_cx", "L_cy",
           "R_hand", "R_grasp", "R_area", "R_cx", "R_cy",
           "B_present", "B_area", "B_cx", "B_cy"]
G_BINARY = [0, 1, 5, 6, 10]
MAP_CHANNELS = ["tool_L", "tool_R", "tool_B", "hand_L", "hand_R"]       # SPEC §3.2 の並び
STATE_NAMES = ["left", "right", "both", "none", "no_annotation"]         # s(b) の符号 0〜4
HTS_CAT = {1: "hand_L", 2: "hand_R", 3: "tool_L", 4: "tool_R", 5: "tool_B"}   # 把持関係 5 クラス
HAND_CAT = {1: "hand_L", 2: "hand_R"}                                    # 手 4 クラスのうち自分の手


def _stats(p: np.ndarray):
    h, w = p.shape
    total = float(p.sum())
    present = float(p.max()) if p.size else 0.0
    area = total / (h * w)
    if total <= 0:
        return present, area, 0.0, 0.0
    ys = (np.arange(h, dtype=np.float64) + 0.5) / h
    xs = (np.arange(w, dtype=np.float64) + 0.5) / w
    cx = float((p.sum(0) * xs).sum() / total)
    cy = float((p.sum(1) * ys).sum() / total)
    return present, area, cx, cy


def summary_g(ch: dict) -> np.ndarray:
    """SPEC §3.1 の g(t)（14 次元）。ch に無いチャネルは零として扱う。"""
    shape = next(iter(ch.values())).shape if ch else (1, 1)
    z = np.zeros(shape, np.float32)
    out = []
    for side in ("L", "R"):
        hand = _stats(ch.get(f"hand_{side}", z))[0]
        pres, area, cx, cy = _stats(ch.get(f"tool_{side}", z))
        out += [hand, pres, area, cx, cy]
    pres, area, cx, cy = _stats(ch.get("tool_B", z))
    out += [pres, area, cx, cy]
    return np.asarray(out, np.float32)


def box_pixels(bbox_xywh, h, w):
    """COCO の枠 [x, y, w, h] が覆う画素の範囲（行 y0:y1、列 x0:x1）。端を含む画素を数える（floor と ceil）。"""
    x, y, bw, bh = bbox_xywh
    x0, y0 = max(0, int(np.floor(x))), max(0, int(np.floor(y)))
    x1, y1 = min(w, int(np.ceil(x + bw))), min(h, int(np.ceil(y + bh)))
    return y0, max(y0, y1), x0, max(x0, x1)


def box_ratios(ch: dict, boxes_xywh, h, w) -> np.ndarray:
    """SPEC §3.3 の r_c(b)（c = 左・右・両手）。(N, 3)。積分画像で画素の和を取る。"""
    out = np.zeros((len(boxes_xywh), 3), np.float64)
    for j, key in enumerate(("tool_L", "tool_R", "tool_B")):
        p = ch.get(key)
        if p is None:
            continue
        ii = np.pad(p.astype(np.float64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))
        for i, b in enumerate(boxes_xywh):
            y0, y1, x0, x1 = box_pixels(b, h, w)
            n = (y1 - y0) * (x1 - x0)
            if n:
                out[i, j] = (ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]) / n
    return out


def box_state(r: np.ndarray, tau: float):
    """r (N, 3) → 軟らかい 4 値 q (N, 4)、硬い状態 s (N,)（0 左、1 右、2 両手、3 なし）、Σ が 1 を超えた数。"""
    tot = r.sum(1)
    q = np.concatenate([r, (1.0 - np.minimum(tot, 1.0))[:, None]], 1)
    s = np.where(tot >= tau, r.argmax(1), 3)
    return q, s.astype(np.int64), int((tot > 1.0).sum())


def decode(seg, h, w) -> np.ndarray:
    from pycocotools import mask as mask_utils
    if isinstance(seg, dict):
        rle = dict(seg)
        if isinstance(rle["counts"], list):
            rle = mask_utils.frPyObjects(rle, h, w)
        elif isinstance(rle["counts"], str):
            rle["counts"] = rle["counts"].encode()
        return mask_utils.decode(rle).astype(bool)
    rles = mask_utils.frPyObjects(seg, h, w)
    return mask_utils.decode(mask_utils.merge(rles)).astype(bool)


class HTSIndex:
    """把持の三種の注釈（train と val のファイルだけ。test と extra は開かない）をフレームの stem で引く。"""

    KINDS = ("hand_tool_seg", "hand_seg", "tool_seg")

    def __init__(self, parts=("train", "val")):
        assert set(parts) <= {"train", "val"}, parts
        self.anns = {k: {} for k in self.KINDS}
        self.size = {}
        self.cats = {}
        for kind in self.KINDS:
            for part in parts:
                d = json.loads((HTS / kind / f"{part}.json").read_text())
                self.cats[kind] = {c["id"]: c["name"] for c in d["categories"]}
                imgs = {im["id"]: im for im in d["images"]}
                for a in d["annotations"]:
                    im = imgs[a["image_id"]]
                    stem = Path(im["file_name"]).stem
                    self.anns[kind].setdefault(stem, []).append(a)
                    self.size[stem] = (im["height"], im["width"])
        self.loss_mask = set()
        for part in parts:
            self.loss_mask |= set((HTS / f"hand_tool_seg/loss_mask/{part}.txt").read_text().split())

    def annotated(self, stem) -> bool:
        """SPEC §3 の「注釈のあるフレーム」: 把持関係 5 クラスの注釈があり、欠落の印が付いていない。"""
        return stem in self.anns["hand_tool_seg"] and stem not in self.loss_mask

    def class_masks(self, kind, stem, catmap):
        h, w = self.size.get(stem, (1080, 1920))
        out = {}
        for a in self.anns[kind].get(stem, []):
            name = catmap.get(a["category_id"])
            if name is None:
                continue
            m = decode(a["segmentation"], h, w)
            out[name] = (out[name] | m) if name in out else m
        return {k: v.astype(np.float32) for k, v in out.items()}

    def g_channels(self, stem):
        """g(t) の入力: 把持関係 5 クラスのチャネル（手の存在も 5 クラスの 1・2 から読む。RESULT に解釈として記録）。"""
        return self.class_masks("hand_tool_seg", stem, HTS_CAT) if self.annotated(stem) else {}

    def map_channels(self, stem):
        """m(t) の 5 チャネル（器具 3 つは把持関係 5 クラス、自分の手 2 つは手 4 クラス）。無い種類は零。"""
        h, w = self.size.get(stem, (1080, 1920))
        ch = {}
        if self.annotated(stem):
            ch.update({k: v for k, v in self.class_masks("hand_tool_seg", stem, HTS_CAT).items() if k.startswith("tool")})
        ch.update(self.class_masks("hand_seg", stem, HAND_CAT))
        out = np.zeros((len(MAP_CHANNELS), h, w), np.uint8)
        for i, k in enumerate(MAP_CHANNELS):
            if k in ch:
                out[i] = ch[k] > 0
        return out

"""術具と自分の手のグラフの材料を組み、検査する（非公式 T-2026-11-20-grasp-hand-graph-pilot、SPEC §4・§5、Task C）。本体の .venv。

    det       検出塔の上位 300（COCO の検出結果の形の json）を、フレームごとに得点の高い順の上位 30 の配列にする
    assemble  腕ごとの材料 graph/<腕>_<part>.npz（frame_ids、x (F, 32, 27)）と目録・検査・対照を作る

x の行 0..29 = 術具の節［有無 1｜クラスの one-hot 15・得点 1・枠 4（画像の大きさで割った xyxy）・持ち手 3（左・右・両手）｜辺の重み 3（左・右・両手）］、
行 30・31 = 自分の左手・右手の節［有無 1｜側の one-hot 2・得点 1・マスクの外接矩形 4・面積の割合 1｜0 × 18］。

持ち手（§4.1）: G3 のクラス c のインスタンスのうち、マスクの外接矩形と術具の枠の IoU × G3 の得点の最大（c = 左・右・両手）。
正解の腕は hand_tool_seg の器具のマスクの外接矩形との IoU × 1 の最大。
辺（§4.2、利用者の決定 2026-11-20）: 左・右・両手の 3 種。重みは持ち手のその種類の値。手の節の無い側の辺は界面が 0 にする。
DGH-U（利用者の決定）: 持ち手と辺の重みを [u, u, u]（u = max(hL, hR, hB)）にする。
正解の手の節（利用者の決定）: 同じ側の注釈のマスクが複数あれば合わせた一つのマスクから外接矩形と面積を取る。得点 1。
手の節（予測）: H4 の自分の左手（0）・右手（1）のクラスごとに得点の最も高いインスタンス。他者の手（2・3）は使わない。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

import numpy as np

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
from stage2pilot import common as C  # noqa: E402

TASK = "T-2026-11-20-grasp-hand-graph-pilot"
S = Path("/home/ubuntu/slocal2/stage2pilot_store")
O = S / "grasp_hand_graph"
F18 = S / "T-2026-10-18-stage2-pilot-folda/signals"
HTS = C.ROOT / "data/annotations/egosurgery_hts"
HALVES = {"H1": ["01", "06", "11", "12", "15"], "H2": ["02", "03", "08", "13", "14"]}
ROWS, NT = 30, 15
TOOL_F, HAND_F = 23, 8
DET_SRC = {"val_final": (F18 / "final/pred_val_top300.json", "val"),
           "train_final": (F18 / "final_recheck/pred_train_top300.json", "train"),
           "train_cfH1": (F18 / "cf_det_from_H1/pred_train_top300.json", "train"),     # H1 の検出塔が H2 の動画に出した値
           "train_cfH2": (F18 / "cf_det_from_H2/pred_train_top300.json", "train")}
DET_LEARNED = {"final": None, "cfH1": HALVES["H1"], "cfH2": HALVES["H2"]}
ARMS = ("D", "DG", "DH", "DGH", "DGH-U", "DGH-noCF", "DGH-GT")
# SPEC §5 の表（利用者の決定で DGH-U は持ち手 [u, u, u]・辺 3 種とも u）: 術具の節・持ち手・手の節・辺
TABLE = {"D": (True, False, False, False), "DG": (True, True, False, False), "DH": (True, False, True, False),
         "DGH": (True, True, True, True), "DGH-U": (True, True, True, True), "DGH-noCF": (True, True, True, True),
         "DGH-GT": (True, True, True, True)}


def sha(p):
    return C.sha256(p)


def cf_half(video):
    """train の動画 v の交差適合の信号を出す半分（v を学んでいない側）。"""
    if video in HALVES["H1"]:
        return "H2"
    if video in HALVES["H2"]:
        return "H1"
    raise ValueError(video)


# ---------------------------------------------------------------- det
def cmd_det(a):
    out = O / "signals/det"
    out.mkdir(parents=True, exist_ok=True)
    rep = {}
    for key, (path, part) in DET_SRC.items():
        ann = json.loads((C.DET_ANN_A / f"instances_{part}.json").read_text())
        img = {im["id"]: (Path(im["file_name"]).stem, im["width"], im["height"]) for im in ann["images"]}
        rows = collections.defaultdict(list)
        for x in json.loads(Path(path).read_text()):
            rows[x["image_id"]].append((x["score"], x["category_id"], x["bbox"]))
        frames = sorted(img[i][0] for i in rows)
        C.assert_no_test(frames, f"det {key}")
        pos = {f: j for j, f in enumerate(frames)}
        cat = np.full((len(frames), ROWS), -1, np.int16)
        score = np.zeros((len(frames), ROWS), np.float32)
        box = np.zeros((len(frames), ROWS, 4), np.float32)
        per = []
        for i, lst in rows.items():
            stem, w, h = img[i]
            lst = sorted(lst, key=lambda r: -r[0])[:ROWS]                 # 得点の高い順（同点は元の順）
            j = pos[stem]
            per.append(len(rows[i]))
            for r, (s, c, (bx, by, bw, bh)) in enumerate(lst):
                cat[j, r], score[j, r] = c, s
                box[j, r] = [bx / w, by / h, (bx + bw) / w, (by + bh) / h]
        p = out / f"det_{key}.npz"
        np.savez(p, frame_ids=np.asarray(frames), cat=cat, score=score, box=box)
        rep[key] = {"source": str(path), "source_sha256": sha(path), "part": part, "frames": len(frames),
                    "videos": sorted({C.video_of(f) for f in frames}), "queries_per_frame": sorted(set(per)),
                    "npz": str(p), "npz_sha256": sha(p), "score_top1_mean": float(score[:, 0].mean())}
        print(key, {k: rep[key][k] for k in ("frames", "videos", "queries_per_frame")}, flush=True)
    C.write_json(out / "det_report.json", rep)


# ---------------------------------------------------------------- 部品
def iou(a, b):
    """a (N, 4)、b (M, 4) の xyxy → (N, M)。"""
    x0 = np.maximum(a[:, None, 0], b[None, :, 0])
    y0 = np.maximum(a[:, None, 1], b[None, :, 1])
    x1 = np.minimum(a[:, None, 2], b[None, :, 2])
    y1 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x1 - x0, 0, None) * np.clip(y1 - y0, 0, None)
    aa = np.clip(a[:, 2] - a[:, 0], 0, None) * np.clip(a[:, 3] - a[:, 1], 0, None)
    ab = np.clip(b[:, 2] - b[:, 0], 0, None) * np.clip(b[:, 3] - b[:, 1], 0, None)
    u = aa[:, None] + ab[None, :] - inter
    return np.where(u > 0, inter / np.maximum(u, 1e-12), 0.0)


def holder(tool_box, inst_lab, inst_score, inst_box):
    """術具の枠 (N, 4) ごとの持ち手 3 次元: クラス c のインスタンスの IoU × 得点の最大（無ければ 0）。"""
    out = np.zeros((len(tool_box), 3), np.float32)
    if not len(tool_box) or not len(inst_lab):
        return out
    m = iou(tool_box, inst_box) * inst_score[None, :]
    for c in range(3):
        sel = inst_lab == c
        if sel.any():
            out[:, c] = m[:, sel].max(1)
    return out


class Raw:
    """ghg_tower infer の出力（frame_ids、labels、scores、boxes、area）をフレーム名で引く。"""

    def __init__(self, prefix):
        self.prefix = Path(str(prefix))
        z = np.load(str(prefix) + ".npz")
        self.d = {k: z[k] for k in z.files}
        self.frames = [str(f) for f in self.d["frame_ids"]]
        self.row = {f: i for i, f in enumerate(self.frames)}
        self.report = json.loads(Path(str(prefix) + "_report.json").read_text())

    def get(self, f):
        i = self.row.get(f)
        if i is None:
            return None
        keep = self.d["labels"][i] >= 0
        return (self.d["labels"][i][keep].astype(np.int64), self.d["scores"][i][keep], self.d["boxes"][i][keep],
                self.d["area"][i][keep])


class Det:
    def __init__(self, key):
        z = np.load(O / f"signals/det/det_{key}.npz")
        self.d = {k: z[k] for k in z.files}
        self.row = {str(f): i for i, f in enumerate(self.d["frame_ids"])}

    def get(self, f):
        i = self.row.get(f)
        if i is None:
            return None
        keep = self.d["cat"][i] >= 0
        return self.d["cat"][i][keep].astype(np.int64), self.d["score"][i][keep], self.d["box"][i][keep]


def decode(seg, h, w):
    from grasppilot.grasp_signals import decode as dec
    return dec(seg, h, w)


def mask_box(m):
    ys, xs = np.nonzero(m)
    if not len(ys):
        return None
    h, w = m.shape
    return np.array([xs.min() / w, ys.min() / h, (xs.max() + 1) / w, (ys.max() + 1) / h], np.float32)


def load_coco(path):
    d = json.loads(Path(path).read_text())
    imgs = {im["id"]: im for im in d["images"]}
    by = collections.defaultdict(list)
    for x in d["annotations"]:
        by[Path(imgs[x["image_id"]]["file_name"]).stem].append(x)
    return by, {Path(im["file_name"]).stem: im for im in d["images"]}


class GT:
    """正解の腕の材料（術具の枠・自分の手の節・持ち手）。注釈の無いフレームはその種類を置かない。"""

    def __init__(self, part):
        assert part in ("train", "val"), part                 # test は開かない
        self.tool, self.tool_img = load_coco(C.DET_ANN_A / f"instances_{part}.json")
        self.hand, self.hand_img = load_coco(HTS / f"hand_seg/{part}.json")
        self.hts, self.hts_img = load_coco(HTS / f"hand_tool_seg/{part}.json")
        self.stats = collections.Counter()

    def tools(self, f):
        im = self.tool_img.get(f)
        if im is None:
            return None
        w, h = im["width"], im["height"]
        lst = sorted(self.tool[f], key=lambda x: x["id"])          # 得点はすべて 1。同点は注釈の順
        cat = np.array([x["category_id"] for x in lst], np.int64)
        box = np.array([[x["bbox"][0] / w, x["bbox"][1] / h, (x["bbox"][0] + x["bbox"][2]) / w, (x["bbox"][1] + x["bbox"][3]) / h]
                        for x in lst], np.float32).reshape(-1, 4)
        return cat, np.ones(len(lst), np.float32), box

    def hands(self, f):
        """自分の左手（1）・右手（2）ごとに注釈のマスクを合わせ、(側, 外接矩形, 面積の割合) を返す。"""
        im = self.hand_img.get(f)
        if im is None:
            return None
        h, w = im["height"], im["width"]
        out = {}
        for side, cid in ((0, 1), (1, 2)):
            ms = [decode(x["segmentation"], h, w) for x in self.hand[f] if x["category_id"] == cid]
            if not ms:
                continue
            if len(ms) > 1:
                self.stats[f"hand_union_side{side}"] += 1
            m = np.logical_or.reduce(ms)
            b = mask_box(m)
            if b is not None:
                out[side] = (b, float(m.sum()) / (h * w))
        return out

    def grasp(self, f):
        """hand_tool_seg の器具 3 クラス（3 左、4 右、5 両手）のインスタンス: (ラベル 0〜2, 得点 1, 外接矩形, マスク)。"""
        im = self.hts_img.get(f)
        if im is None:
            return None
        h, w = im["height"], im["width"]
        lab, box, masks = [], [], []
        for x in self.hts[f]:
            if x["category_id"] in (3, 4, 5):
                m = decode(x["segmentation"], h, w)
                b = mask_box(m)
                if b is None:
                    continue
                lab.append(x["category_id"] - 3)
                box.append(b)
                masks.append(m)
        return (np.array(lab, np.int64), np.ones(len(lab), np.float32), np.array(box, np.float32).reshape(-1, 4), masks)


# ---------------------------------------------------------------- assemble
def tool_rows(x, j, cat, score, box, hold, edge):
    n = min(len(cat), ROWS)
    for r in range(n):
        x[j, r, 0] = 1.0
        x[j, r, 1 + cat[r]] = 1.0
        x[j, r, 1 + NT] = score[r]
        x[j, r, 2 + NT:6 + NT] = box[r]
        x[j, r, 6 + NT:9 + NT] = hold[r]
        x[j, r, 1 + TOOL_F:4 + TOOL_F] = edge[r]
    return n


def hand_rows(x, j, hands):
    for side, (score, b, ar) in hands.items():
        r = ROWS + side
        x[j, r, 0] = 1.0
        x[j, r, 1 + side] = 1.0
        x[j, r, 3] = score
        x[j, r, 4:8] = b
        x[j, r, 8] = ar


def pred_hands(h4):
    """H4 の出力から、自分の左手（0）・右手（1）ごとに得点の最も高いインスタンス。"""
    if h4 is None:
        return {}
    lab, sc, bx, ar = h4
    out = {}
    for side in (0, 1):
        sel = np.nonzero(lab == side)[0]
        if len(sel):
            k = sel[np.argmax(sc[sel])]
            out[side] = (float(sc[k]), bx[k], float(ar[k]))
    return out


def arm_flags(x):
    """材料の配列から、術具の節・持ち手（非零）・手の節・辺（非零）の在否と、持ち手が 3 列とも同じか。"""
    t = x[:, :ROWS]
    tp = t[..., 0] > 0.5
    hold = t[..., 6 + NT:9 + NT]
    edge = t[..., 1 + TOOL_F:4 + TOOL_F]
    return {"tools": bool(tp.any()), "holder": bool(np.abs(hold).sum() > 0), "hands": bool((x[:, ROWS:, 0] > 0.5).any()),
            "edges": bool(np.abs(edge).sum() > 0),
            "holder_uniform": bool(np.allclose(hold[..., 0], hold[..., 1]) and np.allclose(hold[..., 0], hold[..., 2])),
            "edge_equals_holder": bool(np.array_equal(edge, hold))}


def table_check(flags):
    bad = []
    for arm, (t, g, h, e) in TABLE.items():
        f = flags[arm]
        if (f["tools"], f["holder"], f["hands"], f["edges"]) != (t, g, h, e):
            bad.append((arm, "presence"))
        if arm == "DGH-U" and not f["holder_uniform"]:
            bad.append((arm, "holder_not_uniform"))
        if arm in ("DGH", "DGH-noCF", "DGH-GT", "DGH-U") and not f["edge_equals_holder"]:
            bad.append((arm, "edge_not_holder"))
    return {"arms": len(flags), "violations": len(bad), "examples": bad[:5]}


def videos_check(videos):
    v = set(videos)
    return {"videos": sorted(v), "test_overlap": sorted(v & set(C.TEST_VIDEOS)), "n_overlap": len(v & set(C.TEST_VIDEOS))}


def provenance_check(sources, learned):
    """フレームごとの (動画, 信号を作った塔) が、その塔の学んだ動画を含まないか。外れの件数。"""
    bad = [(f, g) for f, g in sources.items() if C.video_of(f) in learned[g]]
    return {"frames": len(sources), "violations": len(bad), "examples": bad[:3]}


def grasp_agreement(gt, frames, hold_by_frame, swap=False):
    """正解の腕の持ち手の argmax と、注釈の把持（器具の枠の画素を最も多く覆う hand_tool_seg の器具のマスクのクラス）の一致。
    把持の注釈の在るフレームで、覆う画素が 1 以上の枠だけ数える。swap=True は持ち手の左右を入れ替えた写し（対照）。"""
    n = agree = 0
    for f in frames:
        g = gt.grasp(f)
        tl = gt.tools(f)
        if g is None or tl is None or not len(g[0]) or not len(tl[0]):   # 正解の器具の枠が 0 個のフレームは数える枠が無い
            continue
        im = gt.hts_img[f]
        h, w = im["height"], im["width"]
        hold = hold_by_frame[f]
        if swap:
            hold = hold[:, [1, 0, 2]]
        for r, b in enumerate(tl[2][:ROWS]):
            x0, y0, x1, y1 = int(b[0] * w), int(b[1] * h), int(np.ceil(b[2] * w)), int(np.ceil(b[3] * h))
            cov = np.zeros(3)
            for lab, m in zip(g[0], g[3]):
                cov[lab] = max(cov[lab], m[y0:y1, x0:x1].sum())
            if cov.max() <= 0:
                continue
            n += 1
            agree += int(np.argmax(hold[r]) == np.argmax(cov))
    return {"boxes": n, "agree": agree, "rate": agree / n if n else None}


def cmd_assemble(a):
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    raw = Path(a.raw_dir)
    fold = C.fold_a()
    seqs = {p: [f for v, fr, _ in C.phase_sequences(fold[p]) for f in fr] for p in ("train", "val")}
    R = {k: Raw(raw / k) for k in ("G3_all_train", "G3_all_val", "G3_H1_train", "G3_H2_train",
                                   "H4_all_train", "H4_all_val", "H4_H1_train", "H4_H2_train")}
    for k, r in R.items():
        if r.report.get("task_id") != TASK:
            raise RuntimeError(f"本契約の出力ではない: {k}")
    D = {k: Det(k) for k in DET_SRC}
    tower_runs = {t: {v: json.loads((Path(a.runs_root) / f"grasp_hand_graph_tower_{t}_{v}_seed42/config.json").read_text())
                      for v in ("all", "H1", "H2")} for t in ("G3", "H4")}
    learned = {f"{t}_{v}": tower_runs[t][v]["train_videos"] for t in ("G3", "H4") for v in ("all", "H1", "H2")}
    learned.update({"det_final": fold["train"], "det_cfH1": HALVES["H1"], "det_cfH2": HALVES["H2"]})
    rep = {"task_id": TASK, "unofficial": True, "code_sha256": sha(Path(__file__)), "learned_videos": learned, "parts": {}}
    gts = {p: GT(p) for p in ("train", "val")}
    flags_all, prov = {}, {}
    for part in ("train", "val"):
        frames = seqs[part]
        F = len(frames)
        X = {arm: np.zeros((F, ROWS + 2, 27), np.float32) for arm in ARMS}
        src = {"cf": {}, "nocf": {}}
        cnt = collections.Counter()
        gt_hold = {}
        gt = gts[part]
        for j, f in enumerate(frames):
            v = C.video_of(f)
            # 予測（交差適合）と予測（noCF）。val はどちらも確定の塔
            if part == "train":
                hcf = cf_half(v)
                det_cf, det_no = D[f"train_cf{hcf}"].get(f), D["train_final"].get(f)
                g3_cf, g3_no = R[f"G3_{hcf}_train"].get(f), R["G3_all_train"].get(f)
                h4_cf, h4_no = R[f"H4_{hcf}_train"].get(f), R["H4_all_train"].get(f)
                src["cf"][f] = {"det": f"det_cf{hcf}", "G3": f"G3_{hcf}", "H4": f"H4_{hcf}"}
                src["nocf"][f] = {"det": "det_final", "G3": "G3_all", "H4": "H4_all"}
            else:
                det_cf = det_no = D["val_final"].get(f)
                g3_cf = g3_no = R["G3_all_val"].get(f)
                h4_cf = h4_no = R["H4_all_val"].get(f)
                src["cf"][f] = src["nocf"][f] = {"det": "det_final", "G3": "G3_all", "H4": "H4_all"}
            for kind, det, g3, h4 in (("cf", det_cf, g3_cf, h4_cf), ("nocf", det_no, g3_no, h4_no)):
                if det is None:
                    cnt[f"{kind}_no_det"] += 1
                    continue
                cat, sc, bx = det[0][:ROWS], det[1][:ROWS], det[2][:ROWS]
                hold = holder(bx, *g3[:3]) if g3 is not None else np.zeros((len(cat), 3), np.float32)
                if g3 is None:
                    cnt[f"{kind}_no_G3"] += 1
                hands = pred_hands(h4)
                if h4 is None:
                    cnt[f"{kind}_no_H4"] += 1
                z = np.zeros_like(hold)
                if kind == "cf":
                    tool_rows(X["D"], j, cat, sc, bx, z, z)
                    tool_rows(X["DG"], j, cat, sc, bx, hold, z)
                    tool_rows(X["DH"], j, cat, sc, bx, z, z)
                    hand_rows(X["DH"], j, hands)
                    tool_rows(X["DGH"], j, cat, sc, bx, hold, hold)
                    hand_rows(X["DGH"], j, hands)
                    u = np.repeat(hold.max(1, keepdims=True), 3, 1)
                    tool_rows(X["DGH-U"], j, cat, sc, bx, u, u)
                    hand_rows(X["DGH-U"], j, hands)
                    cnt["hands_pred_L"] += 0 in hands
                    cnt["hands_pred_R"] += 1 in hands
                else:
                    tool_rows(X["DGH-noCF"], j, cat, sc, bx, hold, hold)
                    hand_rows(X["DGH-noCF"], j, hands)
            # 正解
            tl = gt.tools(f)
            if tl is not None and len(tl[0]):
                gg = gt.grasp(f)
                hold = holder(tl[2], *gg[:3]) if gg is not None else np.zeros((len(tl[0]), 3), np.float32)
                if gg is None:
                    cnt["gt_no_grasp_annotation"] += 1
                gt_hold[f] = hold
                cnt["gt_tools_over_N10"] += len(tl[0]) > 10
                tool_rows(X["DGH-GT"], j, tl[0], tl[1], tl[2], hold, hold)
            else:
                cnt["gt_no_tool_box"] += 1
            hh = gt.hands(f)
            if hh is None:
                cnt["gt_no_hand_annotation"] += 1
            else:
                hand_rows(X["DGH-GT"], j, {s: (1.0, b, ar) for s, (b, ar) in hh.items()})
        files = {}
        for arm in ARMS:
            p = out / f"{arm}_{part}.npz"
            np.savez(p, frame_ids=np.asarray(frames), x=X[arm])
            x = X[arm]
            files[arm] = {"path": str(p), "sha256": sha(p), "frames": F,
                          "frames_with_tools": int((x[:, :ROWS, 0] > 0.5).any(1).sum()),
                          "frames_with_hand_L": int((x[:, ROWS, 0] > 0.5).sum()), "frames_with_hand_R": int((x[:, ROWS + 1, 0] > 0.5).sum()),
                          "frames_empty": int((~(x[..., 0] > 0.5).any(1)).sum()),
                          "tool_nodes_mean": float((x[:, :ROWS, 0] > 0.5).sum(1).mean())}
            flags_all[f"{arm}_{part}"] = arm_flags(x)
        tc = table_check({arm: flags_all[f"{arm}_{part}"] for arm in ARMS})
        bad = dict(X)
        bad["D"] = X["DH"]                                         # 対照: 表と違う腕（D に手の節が在る）を 1 つ作った写し
        tc_ctrl = table_check({arm: arm_flags(bad[arm]) for arm in ARMS})
        prov_frames = {f: s["G3"] for f, s in src["cf"].items()}
        prov_h4 = {f: s["H4"] for f, s in src["cf"].items()}
        prov_det = {f: s["det"] for f, s in src["cf"].items()}
        mixed = dict(prov_frames)
        if part == "train":
            for f in frames[:: max(1, F // 5)][:5]:
                mixed[f] = "G3_all"
        prov[part] = {"G3_cf": provenance_check(prov_frames, learned) if part == "train" else None,
                      "H4_cf": provenance_check(prov_h4, learned) if part == "train" else None,
                      "det_cf": provenance_check(prov_det, learned) if part == "train" else None,
                      "G3_cf_control_mixed_final": provenance_check(mixed, learned) if part == "train" else None,
                      "val_from": sorted({s["G3"] for s in src["cf"].values()}) if part == "val" else None}
        agree = grasp_agreement(gt, frames, gt_hold) if part == "val" or a.agree_train else None
        agree_swap = grasp_agreement(gt, frames, gt_hold, swap=True) if agree is not None else None
        rep["parts"][part] = {"frames": F, "videos": videos_check(sorted({C.video_of(f) for f in frames})), "counts": dict(cnt), "gt_stats": dict(gt.stats),
                              "files": files, "table_check": tc, "table_check_control_wrong_arm": tc_ctrl,
                              "provenance": prov[part], "gt_grasp_agreement": agree, "gt_grasp_agreement_control_swapLR": agree_swap,
                              "flags": {arm: flags_all[f"{arm}_{part}"] for arm in ARMS}}
        print(part, json.dumps({"counts": dict(cnt), "table": tc, "table_ctrl": tc_ctrl, "prov": prov[part], "agree": agree,
                                "agree_swap": agree_swap}, ensure_ascii=False), flush=True)
        if tc["violations"] or (part == "train" and (prov[part]["G3_cf"]["violations"] or prov[part]["H4_cf"]["violations"]
                                                    or prov[part]["det_cf"]["violations"])):
            raise RuntimeError(f"検査の外れ {part}")
    stage_videos = {f"tower_{k}": v for k, v in learned.items() if not k.startswith("det")}
    stage_videos.update({f"infer_{k}": r.report["videos"] for k, r in R.items()})
    stage_videos.update({f"det_{k}": json.loads((O / "signals/det/det_report.json").read_text())[k]["videos"] for k in DET_SRC})
    stage_videos.update({f"graph_{p}": rep["parts"][p]["videos"]["videos"] for p in ("train", "val")})
    rep["i_test_unused"] = {k: videos_check(v) for k, v in stage_videos.items()}
    rep["i_control_04_mixed"] = videos_check(sorted({C.video_of(f) for f in seqs["train"] + ["04_1_0001"]}))   # 対照: train のフレームに試験の動画のフレームを 1 つ混ぜ、同じ経路（フレーム → 動画）に通す
    if any(x["n_overlap"] for x in rep["i_test_unused"].values()):
        raise RuntimeError("test の動画が混入")
    man = {"task_id": TASK, "unofficial": True, "host": os.uname().nodename,
           "raw_signals": {k: {"npz": str(r.prefix) + ".npz", "sha256": r.report["npz_sha256"], "frames": r.report["frames"],
                               "frames_phase_path": r.report["frames_phase_path"],
                               "coverage": r.report["frames"] / max(r.report["frames_phase_path"], 1),
                               "videos": r.report["videos"], "ckpt_sha256": r.report["ckpt_sha256"], "tower_videos": r.report.get("g")}
                           for k, r in R.items()},
           "det": json.loads((O / "signals/det/det_report.json").read_text()),
           "graph": {p: rep["parts"][p]["files"] for p in ("train", "val")},
           "made_by": {"train_pred": "交差適合（検出塔・G3・H4 とも、その動画を学んでいない半分の塔）", "train_noCF": "確定の塔",
                       "val": "確定の塔", "gt": "術具の注釈の枠・hand_seg（同じ側は和集合）・hand_tool_seg の器具のマスク"},
           "format": "npz: frame_ids (F,)、x (F, 32, 27)。行 0..29 術具［有無｜one-hot 15・得点・xyxy 4・持ち手 3｜辺 3］、行 30・31 自分の左手・右手"
                     "［有無｜側 2・得点・xyxy 4・面積｜0］", "assemble_report": str(out / "assemble_report.json")}
    C.write_json(out / "assemble_report.json", rep)
    C.write_json(Path(a.manifest), man)
    print("[assemble] DONE", flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("det")
    p = sub.add_parser("assemble")
    p.add_argument("--manifest", default=str(C.ROOT / "experiments/analysis/grasp_hand_graph_pilot/signals_manifest.json"))
    p.add_argument("--agree-train", action="store_true", help="train でも持ち手と注釈の一致を数える（遅い）")
    p.add_argument("--raw-dir", default=str(O / "signals/raw"), help="G3・H4 の推論の置き場（試走は別の場所）")
    p.add_argument("--out-dir", default=str(O / "graph"))
    p.add_argument("--runs-root", default=str(C.ROOT / "experiments/phase1"), help="塔の run の記録の置き場（config.json の train_videos を読む）")
    a = ap.parse_args()
    {"det": cmd_det, "assemble": cmd_assemble}[a.cmd](a)


if __name__ == "__main__":
    main()

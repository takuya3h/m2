"""G の出力から信号と教師の標的を作る（非公式 T-2026-11-01-grasp-pilot-g、SPEC §3.3・Task D）。本体の .venv。

infer: 一つの G（確定・H1・H2）を、指定の split と動画のフレームに当てる。フレームごとに
    P_c(x) = max_{クラス c のインスタンス} (スコア × マスクの確率)  （元の解像度 1080×1920）
    インスタンスは mmdet の instance_postprocess と同じ選び方（クエリ × クラスの確率の上位 100、スコア = クラスの確率 × マスクのスコア）、
    マスクの確率は sigmoid（二値化の前）
  から作る:
    g  (14)  一本目の `grasp_signals.summary_g` に P_1..P_5（hand_L・hand_R・tool_L・tool_R・tool_B）を当てる。旗は全フレーム 1
    m  (5)   [tool_L, tool_R, tool_B, hand_L, hand_R] = [P_3, P_4, P_5, P_1, P_2]。4×4 の平均で 270×480 に縮め、round(p × 255) の uint8 で保存
    q  (枠, 4) 術具の正解の枠ごとに一本目の `box_ratios`（P_3..P_5）→ `box_state` の軟らかい 4 値（τ によらない）
    t  (48)  手 h（左・右・両手）ごとに 16 値 = [14 種（検出塔のクラスの順、Mouth Gag を除く）, その他, なし]。
             なし = 1 − v_h（v_L = g の L_grasp、v_R = R_grasp、v_B = B_present）。残りの v_h を、P_h,器具 と術具のインスタンス i の重なり
             O_i = Σ_x P_h,器具(x) × スコア_i × マスク_i(x) の比で i のクラスへ分ける（14 種のほかの術具のクラスはその他）。Σ O_i = 0 で v_h > 0 ならその他へ
assemble: 腕ごとの信号の置き場を組む（交差適合、入れ替え、確かめ、案 D の目録）

    .venv/bin/python scripts/grasppilot/g_signals.py infer --ckpt best.pth --g all|H1|H2 --part train|val --videos 01,06,... --out <prefix>
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
import torch.nn.functional as F

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
sys.path.insert(0, str(PROJ / "src"))
from grasppilot import grasp_signals as G  # noqa: E402
from stage2pilot import common as C  # noqa: E402

TASK = "T-2026-11-01-grasp-pilot-g"
MAP_H, MAP_W, POOL = 270, 480, 4
SPECIES = ["Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook", "Needle Holders", "Raspatory", "Retractor",
           "Scalpel", "Scissors", "Skewer", "Suction Cannula", "Syringe", "Tweezers"]   # 検出塔の 15 クラスから Mouth Gag を除く
T_VALUES = SPECIES + ["other", "none"]
HANDS = ("L", "R", "B")
HAND_TOOL = {"L": 2, "R": 3, "B": 4}     # 38 クラスの 0 始まりの添字（grasp:Left Hand Tool など）
GRASP_CH = {"hand_L": 0, "hand_R": 1, "tool_L": 2, "tool_R": 3, "tool_B": 4}
TOOL_FIRST = 7                            # 38 クラスの 0 始まりで術具 31 クラスの先頭


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def t_target(P, tool_masks, tool_labels, tool_scores, class_names):
    """一フレームの t（48）。P は (5, H, W) の P_1..P_5（torch、GPU 可）、tool_* は術具のインスタンス（マスクは確率）。"""
    out = np.zeros((3, len(T_VALUES)), np.float64)
    for k, h in enumerate(HANDS):
        ph = P[HAND_TOOL[h]]
        v = float(ph.max())
        out[k, -1] = 1.0 - v
        if v <= 0:
            continue
        if len(tool_labels):
            o = (tool_masks * ph[None]).flatten(1).sum(1) * tool_scores
            o = o.double().cpu().numpy()
        else:
            o = np.zeros(0)
        if o.sum() <= 0:
            out[k, -2] += v
            continue
        for oi, lab in zip(o, tool_labels):
            name = class_names[lab].split(":", 1)[1]
            j = SPECIES.index(name) if name in SPECIES else len(SPECIES)
            out[k, j] += v * oi / o.sum()
    return out.reshape(-1).astype(np.float32)


@torch.no_grad()
def instances(model, inputs, samples, ori):
    """mmdet の instance_postprocess と同じ上位 100 のインスタンス（ラベル、スコア、元の解像度のマスクの確率）。"""
    feats = model.extract_feat(inputs)
    cls, masks = model.panoptic_head.predict(feats, samples)
    out = []
    for i, s in enumerate(samples):
        h, w = s.metainfo["img_shape"]
        mp = F.interpolate(masks[i][:, None, :h, :w], size=ori, mode="bilinear", align_corners=False)[:, 0]
        nq, nc1 = cls[i].shape
        scores = F.softmax(cls[i], -1)[:, :-1]
        top, idx = scores.flatten().topk(100, sorted=False)
        labels = idx % (nc1 - 1)
        q = idx // (nc1 - 1)
        mlog = mp[q]
        binary = (mlog > 0).float()
        mscore = (mlog.sigmoid() * binary).flatten(1).sum(1) / (binary.flatten(1).sum(1) + 1e-6)
        out.append((labels, top * mscore, mlog.sigmoid()))
    return out


def infer(a):
    from grasppilot import g_bench as B
    from grasppilot.g_train import G38, collate, to_inputs
    part, videos = a.part, a.videos.split(",")
    C.assert_no_test(videos, "g_signals infer")
    fold = C.fold_a()
    assert set(videos) <= set(fold[part]), (videos, part)
    seqs = {v: fr for v, fr, _ in C.phase_sequences(videos)}
    stems = [f for v in videos for f in seqs[v]]
    if a.limit:
        stems = stems[:a.limit]
    tool = json.loads((C.DET_ANN_A / f"instances_{part}.json").read_text())
    ids = {im["id"]: Path(im["file_name"]).stem for im in tool["images"]}
    boxes = {}
    for x in tool["annotations"]:
        boxes.setdefault(ids[x["image_id"]], []).append(x)
    images = []
    for i, s in enumerate(stems, start=1):
        v = C.video_of(s)
        images.append({"id": i, "file_name": f"data/raw/ego/{part}/{v}/{s}.jpg", "stem": s, "video": v,
                       "height": 1080, "width": 1920})
    ds = G38({"images": images, "annotations": []}, train=False)
    loader = torch.utils.data.DataLoader(ds, batch_size=2, shuffle=False, num_workers=a.workers, collate_fn=collate)
    model, _ = B.mmdet_model(num_classes=38)
    state = torch.load(a.ckpt, map_location="cpu")
    model.load_state_dict(state["state_dict"])
    model.eval()
    names = json.loads((Path(a.ann_dir) / "g38_val.json").read_text())["categories"]
    names = [c["name"] for c in sorted(names, key=lambda c: c["id"])]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    maps = np.lib.format.open_memmap(str(out) + "_m.npy", mode="w+", dtype=np.uint8, shape=(len(stems), 5, MAP_H, MAP_W))
    g = np.zeros((len(stems), 14), np.float32)
    t = np.zeros((len(stems), 48), np.float32)
    box_ids, q, r = [], [], []
    t0 = time.monotonic()
    k = 0
    for batch in loader:
        inputs, samples = to_inputs(model, batch, training=False)
        for (labels, scores, probs), (_, meta, _) in zip(instances(model, inputs, samples, (1080, 1920)), batch):
            P = torch.zeros((5, 1080, 1920), device=probs.device)
            for c in range(5):
                sel = labels == c
                if sel.any():
                    P[c] = (scores[sel][:, None, None] * probs[sel]).amax(0)
            stem = meta["stem"]
            assert stem == stems[k]
            ch = {name: P[j].cpu().numpy() for name, j in GRASP_CH.items()}
            g[k] = G.summary_g(ch)
            mm = F.avg_pool2d(P[[2, 3, 4, 0, 1]][None], POOL)[0]
            maps[k] = torch.round(mm * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()
            tsel = labels >= TOOL_FIRST
            t[k] = t_target(P, probs[tsel], labels[tsel].cpu().numpy(), scores[tsel], names)
            bx = boxes.get(stem, [])
            if bx:
                rr = G.box_ratios({"tool_L": ch["tool_L"], "tool_R": ch["tool_R"], "tool_B": ch["tool_B"]},
                                  [b["bbox"] for b in bx], 1080, 1920)
                qq, _, _ = G.box_state(rr, 0.1)
                box_ids += [b["id"] for b in bx]
                r.append(rr)
                q.append(qq)
            k += 1
        if k % 500 < 2:
            print(f"[sig] {a.g} {part} {k}/{len(stems)} {(time.monotonic() - t0) / k:.3f}s/frame", flush=True)
    maps.flush()
    np.savez(str(out) + "_sig.npz", frame_ids=np.asarray(stems), g=g, t=t, flag=np.ones(len(stems), np.float32),
             box_ids=np.asarray(box_ids, np.int64), q=np.concatenate(q).astype(np.float32),
             r=np.concatenate(r).astype(np.float32))
    rep = {"task_id": TASK, "g": a.g, "ckpt": str(a.ckpt), "ckpt_sha256": sha(a.ckpt), "part": part, "videos": videos,
           "frames": len(stems), "boxes": len(box_ids), "seconds": time.monotonic() - t0,
           "sig_sha256": sha(str(out) + "_sig.npz"), "maps_sha256": sha(str(out) + "_m.npy"),
           "maps_shape": list(maps.shape), "code_sha256": sha(Path(__file__)),
           "g_range": [float(g.min()), float(g.max())], "t_rowsum_maxdev": float(np.abs(t.reshape(-1, 3, 16).sum(2) - 1).max())}
    C.write_json(str(out) + "_report.json", rep)
    print("[sig] DONE", json.dumps(rep), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("infer")
    p.add_argument("--ckpt", required=True)
    p.add_argument("--g", choices=("all", "H1", "H2"), required=True)
    p.add_argument("--part", choices=("train", "val"), required=True)
    p.add_argument("--videos", required=True)
    p.add_argument("--ann-dir", default="/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/g/ann")
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--limit", type=int, default=0, help="試走用。0 なら全フレーム")
    a = ap.parse_args()
    {"infer": infer}[a.cmd](a)


if __name__ == "__main__":
    main()

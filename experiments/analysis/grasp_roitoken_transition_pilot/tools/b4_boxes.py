"""Task B-4・B-5・B-6 の材料（T-2026-11-09-grasp-roitoken-transition-pilot）。本体の .venv。学習しない。GPU を使わない。

1. 正解の把持の地図: HTS（data/annotations/egosurgery_hts/hand_tool_seg/{train,val}.json、5 クラス）の各画像の
   クラスごとのマスクの和集合（1080×1920）を、G の地図と同じ 4×4 の平均で 270×480 にし、round(割合 × 255) の uint8 で、
   G の地図と同じチャネルの並び（tool_L, tool_R, tool_B, hand_L, hand_R）で書く。並びは工程の目録の順（common.phase_sequences）。
   注釈の無いフレーム（loss_mask）は 0 で、has_gt = False。
2. 枠: 各地図（G の予測と正解）のクラスごとのマスク（地図の値 ≥ 128 = 確率 0.5 以上の画素の和集合。連結成分に分けない）の
   外接矩形（地図の座標、画素の縁。x0, y0, x1, y1）、有無、幾何 6（正規化した中心 x・y、幅、高さ、枠の面積 = 幅 × 高さ、有無の印）。
   誰の手かを落とした枠: 器具の 3 チャネルの画素ごとの最大（和集合）の外接矩形 1 個。
3. 入れ替え: 目録の B_shuffle の見取りの mapping（フレーム → 値を持ってくるフレーム）を添字にする。train は shuffle_CF（pred_CF の地図）、
   val は shuffle（確定の地図）。二つの mapping が同じことを確かめる。
4. 対照: マスクを 1 画素ずらすと枠が変わる（x 方向に 1 画素 roll した地図の枠と比べる）。

    .venv/bin/python b4_boxes.py --out-dir <S>/b4
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402

G_STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals")
MANIFEST = ROOT / "experiments/analysis/grasp_tower_rebuild/signals_manifest.json"
HTS = ROOT / "data/annotations/egosurgery_hts/hand_tool_seg"
CHANNELS = ["tool_L", "tool_R", "tool_B", "hand_L", "hand_R"]
# HTS の category_id → チャネル（1 左手、2 右手、3 左手の器具、4 右手の器具、5 両手の器具）
CAT_TO_CH = {3: 0, 4: 1, 5: 2, 1: 3, 2: 4}
H, W, POOL, THR = 270, 480, 4, 128
CHUNK = 512


def gt_maps(part, frames, out):
    from pycocotools import mask as mask_utils
    ann = json.loads((HTS / f"{part}.json").read_text())
    by_stem = {Path(im["file_name"]).stem: im for im in ann["images"]}
    anns = {}
    for a in ann["annotations"]:
        anns.setdefault(a["image_id"], []).append(a)
    loss_mask = set((HTS / "loss_mask" / f"{part}.txt").read_text().split())
    path = out / f"gt_{part}_m.npy"
    maps = np.lib.format.open_memmap(str(path), "w+", np.uint8, (len(frames), 5, H, W))
    has = np.zeros(len(frames), bool)
    n_ann = 0
    for i, f in enumerate(frames):
        im = by_stem.get(f)
        if im is None:
            continue
        assert (im["height"], im["width"]) == (1080, 1920)
        has[i] = True
        full = np.zeros((5, 1080, 1920), bool)
        for a in anns.get(im["id"], []):
            full[CAT_TO_CH[a["category_id"]]] |= mask_utils.decode(a["segmentation"]).astype(bool)
            n_ann += 1
        frac = full.reshape(5, H, POOL, W, POOL).mean(axis=(2, 4))
        maps[i] = np.round(frac * 255).clip(0, 255).astype(np.uint8)
    maps.flush()
    in_lm = sorted(f for f in frames if f in loss_mask)
    no_gt = sorted(f for f, h in zip(frames, has) if not h)
    return path, has, {"frames": len(frames), "with_gt": int(has.sum()), "without_gt": int((~has).sum()),
                       "annotations_used": n_ann, "without_gt_equals_loss_mask": no_gt == in_lm,
                       "loss_mask_in_frames": len(in_lm), "images_in_json": len(ann["images"]),
                       "json_images_not_in_frames": len(set(by_stem) - set(frames))}


def boxes_of(mask):
    """mask (N, K, H, W) bool → 枠 (N, K, 4)［x0, y0, x1, y1］地図の画素の縁、有無 (N, K)。"""
    rows = mask.any(3)
    cols = mask.any(2)
    present = rows.any(2)
    y0 = rows.argmax(2)
    y1 = H - rows[..., ::-1].argmax(2)
    x0 = cols.argmax(2)
    x1 = W - cols[..., ::-1].argmax(2)
    box = np.stack([x0, y0, x1, y1], -1).astype(np.float32)
    box[~present] = 0
    return box, present


def geometry(box, present):
    x0, y0, x1, y1 = (box[..., i] for i in range(4))
    w, h = (x1 - x0) / W, (y1 - y0) / H
    g = np.stack([(x0 + x1) / 2 / W, (y0 + y1) / 2 / H, w, h, w * h, present.astype(np.float32)], -1)
    g[~present] = 0
    return g.astype(np.float32)


def all_boxes(maps_path, n):
    maps = np.load(maps_path, mmap_mode="r")
    assert maps.shape == (n, 5, H, W), maps.shape
    box = np.zeros((n, 5, 4), np.float32)
    pres = np.zeros((n, 5), bool)
    ubox = np.zeros((n, 1, 4), np.float32)
    upres = np.zeros((n, 1), bool)
    shifted_diff = 0
    shifted_present = 0
    for s in range(0, n, CHUNK):
        m = np.asarray(maps[s:s + CHUNK])
        mk = m >= THR
        b, p = boxes_of(mk)
        box[s:s + CHUNK], pres[s:s + CHUNK] = b, p
        um = (m[:, :3].max(1) >= THR)[:, None]
        ubox[s:s + CHUNK], upres[s:s + CHUNK] = boxes_of(um)
        bs, ps = boxes_of(np.roll(mk, 1, axis=3))
        both = p & ps
        shifted_present += int(both.sum())
        shifted_diff += int((np.abs(bs - b).sum(-1) > 0)[both].sum())
    return box, pres, ubox, upres, {"present_with_shift": shifted_present, "box_changed_with_shift": shifted_diff}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    man = json.loads(MANIFEST.read_text())
    split = C.fold_a()
    rec = {"task_id": "T-2026-11-09-grasp-roitoken-transition-pilot", "channels": CHANNELS, "threshold_uint8": THR,
           "rule": "マスク = 地図の値 ≥ 128（round(p×255)、p ≥ 0.5）。外接矩形は地図の 270×480 の画素の縁。連結成分に分けない",
           "coords": {"map_to_original": "× 4（1080×1920）", "original_to_P_input": "y × 800/1080、x × 1422/1920（Resize(800)）",
                      "P_input_to_layer4": "÷ 32（spatial_scale 1/32、25×45）", "P_input_to_layer3": "÷ 16（spatial_scale 1/16、50×89）"},
           "parts": {}}
    for part in ("train", "val"):
        videos = C.assert_no_test(split[part], f"b4 {part}")
        frames = [f for _, fs, _ in C.phase_sequences(videos) for f in fs]
        pred_key = "pred_CF" if part == "train" else "pred_noCF"
        view = json.loads(Path(man["B_m"][f"{pred_key}_{part}"]["view"]).read_text())
        assert view["frame_ids"] == frames, "見取りの並びが工程の目録の順と違う"
        shuf_cf = json.loads(Path(man["B_m"][f"shuffle_CF_{part}"]["view"]).read_text())
        shuf = json.loads(Path(man["B_m"][f"shuffle_{part}"]["view"]).read_text())
        mapping_key = "shuffle_CF" if part == "train" else "shuffle"
        mapping = (shuf_cf if part == "train" else shuf)["mapping"]
        assert shuf["mapping"] == shuf_cf["mapping"]
        assert (shuf_cf if part == "train" else shuf)["maps"] == view["maps"]
        ix = {f: i for i, f in enumerate(frames)}
        shuffle_idx = np.array([ix[mapping[f]] for f in frames], np.int64)
        gpath, has_gt, gstat = gt_maps(part, frames, out)
        prt = {"videos": videos, "frames": len(frames), "pred_source": {"key": f"{pred_key}_{part}", "maps": view["maps"]},
               "shuffle_source": {"key": f"{mapping_key}_{part}", "mapping_equal_shuffle_and_shuffle_CF": True,
                                  "same_video_share": float(np.mean([C.video_of(f) == C.video_of(mapping[f]) for f in frames])),
                                  "fixed_points": int(sum(mapping[f] == f for f in frames))},
               "gt": {**gstat, "maps": str(gpath), "maps_sha256": C.sha256(gpath)}}
        np.save(out / f"frame_ids_{part}.npy", np.asarray(frames))
        np.save(out / f"shuffle_idx_{part}.npy", shuffle_idx)
        np.save(out / f"has_gt_{part}.npy", has_gt)
        for src, path in (("pred", view["maps"]), ("gt", str(gpath))):
            box, pres, ubox, upres, ctl = all_boxes(path, len(frames))
            np.savez(out / f"boxes_{src}_{part}.npz", box=box, present=pres, geom=geometry(box, pres),
                     ubox=ubox, upresent=upres, ugeom=geometry(ubox, upres))
            prt[src] = {"maps": path, "present_per_class": pres.sum(0).tolist(), "union_present": int(upres.sum()),
                        "frames_any_present": int(pres.any(1).sum()), "control_shift1": ctl,
                        "boxes_sha256": C.sha256(out / f"boxes_{src}_{part}.npz")}
        rec["parts"][part] = prt
        print(part, json.dumps(prt, ensure_ascii=False)[:1500], flush=True)
    C.write_json(out / "b4_record.json", rec)


if __name__ == "__main__":
    main()

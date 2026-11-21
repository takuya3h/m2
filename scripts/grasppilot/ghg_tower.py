"""3 クラスの把持塔 G3・4 クラスの手の塔 H4・5 クラスの対照 G5r（非公式 T-2026-11-20-grasp-hand-graph-pilot、SPEC §3、Task B・C）。本体の .venv。

`g5_train.py`・`g5_signals.py`・`g_train.py` を変えずに、その部品（`G38`・`to_inputs`・`collate`・`rle_gpu`・`resize_shape`・
`build_model` の作り方・`patch_msda_bf16`・`stale_since_best`・`g_signals.instances`）を読んで使う派生。三種の塔は同じこの道具で学ぶ。
処方は 11-05 の G と同じ（mmdet Mask2Former R50、COCO instance の重み、batch 8、bf16 で変形注意だけ fp32、学習率 1e-4、
val の主指標の mask mAP が 4 epoch 改善しなければ打ち切り、上限 36、学習率は下げない、最良の回）。左右反転で左右のラベルを入れ替える。

塔（SPEC §3.2）:
    G3   hand_tool_seg の器具の 3 クラス（3 左手の器具→1、4 右手の器具→2、5 両手の器具→3）。反転で 1↔2
    H4   hand_seg の 4 クラス（1 自分の左手、2 自分の右手、3 他者の左手、4 他者の右手）。反転で 1↔2、3↔4
    G5r  hand_tool_seg の 5 クラス（11-05 の G と同じ）。反転で 1↔2、3↔4

    build       注釈を組む（折り A の train / val の動画の工程の経路のうち、その注釈の在るフレームだけ）
    flipdata    反転の取り出しの対照（入れ替える経路と入れ替えない写し）。GPU は使わない
    train       学ぶ（--videos all|H1|H2）
    flipmodel   学習後の反転の整合（val の数十フレーム。入れ替えた一致と入れ替えない写し）
    infer       工程の経路のフレームに当て、上位 100 のインスタンスのラベル・得点・マスクの外接矩形・面積の割合を保存する
    evalpre     学習前（COCO の重みを読んだだけ）の val の mask mAP

COCO の重みは本契約の保存先の写し（`$S/grasp_hand_graph/inputs/coco/`、sha256 を `g_train.WEIGHT_SHA256` で照合）。W&B は offline。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
sys.path.insert(0, str(PROJ / "src"))
from grasppilot import g_bench as B  # noqa: E402
from grasppilot import g_train as T  # noqa: E402
from stage2pilot import common as C  # noqa: E402

TASK = "T-2026-11-20-grasp-hand-graph-pilot"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / "grasp_hand_graph"
COCO_W = STORE / "inputs/coco" / B.MMDET_W.name
HTS = C.ROOT / "data/annotations/egosurgery_hts"
LOSS_MASK_DIR = HTS / "hand_tool_seg/loss_mask"
HALVES = T.HALVES
TOWERS = {
    "G3": {"source": "hand_tool_seg", "src_ids": [3, 4, 5], "swap0": [1, 0, 2]},
    "H4": {"source": "hand_seg", "src_ids": [1, 2, 3, 4], "swap0": [1, 0, 3, 2]},
    "G5r": {"source": "hand_tool_seg", "src_ids": [1, 2, 3, 4, 5], "swap0": [1, 0, 3, 2, 4]},
}
TOPK = 100


def tower_of(name):
    if name not in TOWERS:
        raise SystemExit(f"塔の名前が違う: {name}")
    t = dict(TOWERS[name])
    t["n"] = len(t["src_ids"])
    t["swap0"] = np.asarray(t["swap0"], np.int64)
    return t


# ---------------------------------------------------------------- build
def load_source(source, part):
    assert part in ("train", "val"), part                 # test と extra は開かない
    d = json.loads((HTS / source / f"{part}.json").read_text())
    imgs = {im["id"]: im for im in d["images"]}
    anns = collections.defaultdict(list)
    for a in d["annotations"]:
        anns[Path(imgs[a["image_id"]]["file_name"]).stem].append(a)
    stems = {Path(im["file_name"]).stem: im for im in d["images"]}
    cats = {c["id"]: c["name"] for c in d["categories"]}
    return stems, anns, cats


def class_check(annotations, tower):
    bad = [a for a in annotations if a.get("source") != tower["source"] or a["source_category_id"] not in tower["src_ids"]]
    return {"n": len(annotations), "violations": len(bad)}


def restore_check(src_anns, images, annotations, tower, n, seed=42):
    """組んだ注釈から戻したマスクとクラスが、元の注釈の該当クラスのマスクと画素で一致するか（数フレーム）。"""
    from grasppilot.grasp_signals import decode
    by = collections.defaultdict(list)
    for a in annotations:
        by[a["image_id"]].append(a)
    inv = {s: i + 1 for i, s in enumerate(tower["src_ids"])}
    picks = np.random.default_rng(seed).choice(len(images), size=min(n, len(images)), replace=False)
    rows = []
    for j in sorted(picks.tolist()):
        im = images[j]
        h, w = im["height"], im["width"]
        got = sorted((a["category_id"], decode(a["segmentation"], h, w).tobytes()) for a in by[im["id"]])
        want = sorted((inv[a["category_id"]], decode(a["segmentation"], h, w).tobytes())
                      for a in src_anns[im["stem"]] if a["category_id"] in inv)
        rows.append({"stem": im["stem"], "n_restored": len(got), "n_source": len(want), "equal": got == want})
    return rows


def cmd_build(a):
    tower = tower_of(a.tower)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fold = C.fold_a()
    seqs = {v: fr for v, fr, _ in C.phase_sequences(fold["train"] + fold["val"])}
    lm = {p: set((LOSS_MASK_DIR / f"{p}.txt").read_text().split()) for p in ("train", "val")}
    summary = {"task_id": TASK, "unofficial": True, "tower": a.tower, "source": tower["source"], "src_ids": tower["src_ids"],
               "builder_sha256": C.sha256(Path(__file__)), "parts": {}}
    for part in ("train", "val"):
        stems, src, cats = load_source(tower["source"], part)
        phase = [f for v in fold[part] for f in seqs[v]]
        C.assert_no_test(phase, f"{a.tower}_{part}")
        extra = sorted(set(stems) - set(phase))
        if extra:
            raise RuntimeError(f"工程の経路に無い注釈のフレーム {len(extra)} 件（{extra[:3]}）")
        keep = [s for s in phase if s in stems]          # 注釈の在るフレームだけ（無いフレームを空として学ばない）
        images, annotations = [], []
        inv = {s: i + 1 for i, s in enumerate(tower["src_ids"])}
        for i, stem in enumerate(keep, start=1):
            sim = stems[stem]
            v = C.video_of(stem)
            images.append({"id": i, "file_name": f"data/raw/ego/{part}/{v}/{stem}.jpg", "stem": stem, "video": v,
                           "height": sim["height"], "width": sim["width"]})
            for x in src.get(stem, []):
                if x["category_id"] not in inv:
                    continue
                annotations.append({"id": len(annotations) + 1, "image_id": i, "category_id": inv[x["category_id"]],
                                    "segmentation": x["segmentation"], "bbox": x["bbox"], "area": x.get("area"), "iscrowd": 0,
                                    "source": tower["source"], "source_category_id": x["category_id"], "source_ann_id": x["id"]})
        table = [{"id": inv[s], "name": cats[s], "source_id": s, "flip_swap_to": int(tower["swap0"][inv[s] - 1]) + 1}
                 for s in tower["src_ids"]]
        coco = {"info": {"description": f"{a.tower} (unofficial {TASK})"}, "images": images, "annotations": annotations,
                "categories": [{"id": t["id"], "name": t["name"]} for t in table]}
        p = out / f"{a.tower}_{part}.json"
        p.write_text(json.dumps(coco))
        inst = collections.Counter(x["category_id"] for x in annotations)
        frm = collections.Counter(c for _, c in {(x["image_id"], x["category_id"]) for x in annotations})
        with_any = len({x["image_id"] for x in annotations})
        cc = class_check(annotations, tower)
        spiked = annotations + [{**annotations[0], "id": -1, "source_category_id": 99}]
        lm_in = sorted(set(keep) & lm[part])
        rc = restore_check(src, images, annotations, tower, a.check_frames)
        summary["classes"] = table
        summary["parts"][part] = {
            "path": str(p), "sha256": C.sha256(p), "phase_frames": len(phase), "frames": len(keep),
            "frames_with_any_instance": with_any, "frames_without_instance": len(keep) - with_any,
            "videos": dict(sorted(collections.Counter(im["video"] for im in images).items())), "n_annotations": len(annotations),
            "per_class": {t["name"]: {"id": t["id"], "instances": inst.get(t["id"], 0), "frames": frm.get(t["id"], 0)} for t in table},
            "class_check": cc, "class_check_control_spiked": class_check(spiked, tower),
            "hand_tool_seg_loss_mask_listed": len(lm[part]), "loss_mask_frames_in_images": len(lm_in), "loss_mask_examples": lm_in[:5],
            "loss_mask_check_control_one_added": len((set(keep) | {sorted(lm[part])[0]}) & lm[part]),
            "restore_check": rc}
        if cc["violations"] or not all(r["equal"] for r in rc):
            raise RuntimeError(f"検査の外れ {part}: {cc}")
        if tower["source"] == "hand_tool_seg" and lm_in:
            raise RuntimeError(f"欠落の印のフレームが学ぶフレームに {len(lm_in)} 件ある")
        print(a.tower, part, "phase", len(phase), "frames", len(keep), "with_inst", with_any, "ann", len(annotations),
              "restore_equal", all(r["equal"] for r in rc), "class_viol", cc["violations"],
              "ctrl", summary["parts"][part]["class_check_control_spiked"]["violations"], "lm_in", len(lm_in), flush=True)
    C.write_json(out / f"{a.tower}_summary.json", summary)


# ---------------------------------------------------------------- dataset
class FlipSwap(T.G38):
    """二本目の `G38` と同じ取り出しで、左右反転のときにラベルを塔の入れ替え表で入れ替える（`g5_train.G5Flip` と同じ形）。

    swap=False は入れ替えない写し（対照）。force_flip が True / False なら乱数を引かずにその値で反転する（検査用）。
    """

    def __init__(self, coco, train, swap0, seed=42, swap=True, force_flip=None):
        super().__init__(coco, train, seed)
        self.swap0, self.swap, self.force_flip = swap0, swap, force_flip

    def __getitem__(self, i):
        from grasppilot.grasp_signals import decode
        im = self.images[i]
        h, w = im["height"], im["width"]
        nh, nw, r = T.resize_shape(h, w)
        img = Image.open(PROJ / im["file_name"]).convert("RGB").resize((nw, nh), Image.BILINEAR)
        arr = np.asarray(img)
        out = {"image_id": im["id"], "stem": im["stem"], "ori": (h, w), "size": (nh, nw), "scale": r}
        if not self.train:
            return arr, out, None
        flip = bool(torch.rand(1).item() < 0.5) if self.force_flip is None else bool(self.force_flip)
        masks, labels = [], []
        for x in self.by.get(im["id"], []):
            m = np.asarray(Image.fromarray(decode(x["segmentation"], h, w).astype(np.uint8)).resize((nw, nh), Image.NEAREST))
            if m.any():
                masks.append(m)
                labels.append(x["category_id"] - 1)
        labels = np.array(labels, np.int64)
        if flip:
            arr = arr[:, ::-1].copy()
            masks = [m[:, ::-1].copy() for m in masks]
            if self.swap and len(labels):
                labels = self.swap0[labels]
        out["flipped"] = flip
        masks = np.stack(masks) if masks else np.zeros((0, nh, nw), np.uint8)
        return arr, out, (masks, labels)


def cmd_flipdata(a):
    """同じフレームを反転なし・ありで取り出し、マスクの左右反転とラベルの入れ替えが成り立つかを数える（g5_flip_test と同じ形）。"""
    tower = tower_of(a.tower)
    tr = json.loads((Path(a.ann_dir) / f"{a.tower}_train.json").read_text())
    lr = {c + 1 for c in range(tower["n"]) if tower["swap0"][c] != c}          # 左右を持つクラス
    cats = collections.defaultdict(set)
    for x in tr["annotations"]:
        cats[x["image_id"]].add(x["category_id"])
    pos = [j for j, im in enumerate(tr["images"]) if cats[im["id"]] & lr]
    picks = sorted(np.random.default_rng(42).choice(pos, a.frames, replace=False).tolist())

    def take(ds, i, flip):
        ds.force_flip = flip
        return ds[i]

    res = {"task_id": TASK, "tower": a.tower, "frames": len(picks), "swap0": tower["swap0"].tolist(), "paths": {}}
    for name, swap in (("swap", True), ("noswap_copy", False)):
        ds = FlipSwap(tr, True, tower["swap0"], swap=swap)
        rows = []
        for j in picks:
            a0, m0, (k0, l0) = take(ds, j, False)
            a1, _, (k1, l1) = take(ds, j, True)
            rows.append({"stem": m0["stem"], "labels_noflip": (l0 + 1).tolist(), "labels_flip": (l1 + 1).tolist(),
                         "image_flipped": bool(np.array_equal(a1, a0[:, ::-1])),
                         "masks_flipped": len(k0) == len(k1) and all(np.array_equal(x1, x0[:, ::-1]) for x0, x1 in zip(k0, k1)),
                         "labels_swapped": bool(np.array_equal(l1, tower["swap0"][l0])),
                         "labels_unchanged": bool(np.array_equal(l1, l0))})
        res["paths"][name] = {k: sum(r[k] for r in rows) for k in ("image_flipped", "masks_flipped", "labels_swapped", "labels_unchanged")}
        res["paths"][name]["examples"] = rows[:3]
        print(a.tower, name, {k: v for k, v in res["paths"][name].items() if k != "examples"}, flush=True)
    C.write_json(a.out, res)


# ---------------------------------------------------------------- model
def build_model(num_classes):
    """g5_train.build_model と同じ順（構造 → COCO の重みの形の合う部分）。重みは本契約の写し。"""
    model, cfg = B.mmdet_model(num_classes=num_classes)
    wcheck = B.verify_weight(COCO_W, T.WEIGHT_SHA256)
    if not wcheck["ok"]:
        raise RuntimeError(f"COCO の重みの要約値が違う: {wcheck}")
    st = torch.load(COCO_W, map_location="cpu")["state_dict"]
    own = model.state_dict()
    keepw = {k: v for k, v in st.items() if k in own and own[k].shape == v.shape}
    skipped = sorted(k for k in st if k in own and own[k].shape != st[k].shape)
    absent = sorted(k for k in st if k not in own)
    missing, _ = model.load_state_dict(keepw, strict=False)
    rep = {"checkpoint": str(COCO_W), "sha256": wcheck["sha256"], "n_checkpoint": len(st), "loaded": len(keepw),
           "skipped_shape": skipped, "absent_in_model": absent, "model_params_not_loaded": sorted(missing)}
    return model, cfg, rep


def load_trained(ckpt, num_classes):
    if ckpt == "coco":
        torch.manual_seed(42)
        np.random.seed(42)
        model, _, rep = build_model(num_classes)
        model.eval()
        return model, {"ckpt": "coco", "load": rep}
    model, _ = B.mmdet_model(num_classes=num_classes)
    state = torch.load(ckpt, map_location="cpu")
    if state.get("task_id") != TASK or state.get("num_classes") != num_classes:
        raise RuntimeError(f"本契約の塔の重みではない: {ckpt} {state.get('task_id')} {state.get('num_classes')}")
    model.load_state_dict(state["state_dict"])
    model.eval()
    return model, {"ckpt": str(ckpt), "ckpt_sha256": C.sha256(ckpt), "epoch": state.get("epoch"), "tower": state.get("tower"),
                   "videos": state.get("videos")}


@torch.no_grad()
def evaluate(model, loader, gt_path, limit=None):
    """`g_train.evaluate` と同じ測り方（元の解像度の RLE、pycocotools の segm、上位 100）。主指標はその塔の全クラスの mask mAP。"""
    from pycocotools.coco import COCO
    from pycocotools.cocoeval import COCOeval as CocoEvaluator  # 別名（semgrep の誤検知を避ける）
    model.eval()
    results, ids, n_pred = [], [], 0
    t0 = time.monotonic()
    for k, batch in enumerate(loader):
        if limit is not None and k >= limit:
            break
        inputs, samples = T.to_inputs(model, batch, training=False)
        preds = model.predict(inputs, samples, rescale=True)
        for p, (_, meta, _) in zip(preds, batch):
            ids.append(meta["image_id"])
            inst = p.pred_instances
            masks = inst.masks
            scores, labels = inst.scores.cpu().numpy(), inst.labels.cpu().numpy()
            if len(masks):
                for rle, s, c in zip(T.rle_gpu(masks), scores, labels):
                    rle["counts"] = rle["counts"].decode()
                    results.append({"image_id": meta["image_id"], "category_id": int(c) + 1, "segmentation": rle, "score": float(s)})
            n_pred += len(masks)
    infer_s = time.monotonic() - t0
    gt = COCO(str(gt_path))
    if not results:
        return {"segm_mAP": 0.0, "per_class_ap": {}, "n_images": len(ids), "n_pred": 0}
    ev = CocoEvaluator(gt, gt.loadRes(results), "segm")
    ev.params.imgIds = ids
    ev.evaluate()
    ev.accumulate()
    ev.summarize()
    prec = ev.eval["precision"]
    per = {}
    for k, cid in enumerate(ev.params.catIds):
        p = prec[:, :, k, 0, -1]
        per[gt.cats[cid]["name"]] = float(np.mean(p[p > -1])) if (p > -1).any() else None
    return {"segm_mAP": float(ev.stats[0]), "segm_mAP50": float(ev.stats[1]), "per_class_ap": per, "n_images": len(ids),
            "n_pred": n_pred, "infer_seconds": infer_s, "eval_seconds": time.monotonic() - t0 - infer_s}


def stale_since_best(history):
    """g5_train.stale_since_best と同じ（epoch 0 を除き、改善 = 最良を厳密に上回る）。"""
    best, best_epoch, stale = -1.0, None, 0
    for r in history:
        if r["epoch"] == 0:
            continue
        if r["segm_mAP"] > best:
            best, best_epoch, stale = r["segm_mAP"], r["epoch"], 0
        else:
            stale += 1
    return best, best_epoch, stale


def cmd_train(a):
    from grasppilot.g5_train import patch_msda_bf16
    tower = tower_of(a.tower)
    os.environ["WANDB_MODE"] = "offline"
    os.environ.setdefault("WANDB_DIR", str(STORE / "wandb"))
    Path(os.environ["WANDB_DIR"]).mkdir(parents=True, exist_ok=True)
    run, ckpt = Path(a.run_dir), Path(a.ckpt_dir)
    if not run.name.startswith("grasp_hand_graph_") and not a.smoke:
        raise SystemExit("run の置き場は experiments/phase1/grasp_hand_graph_ で始まる名前にする（SPEC §2）")
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    from mmengine.optim import build_optim_wrapper

    from egosurgery.utils import tracking
    ann = Path(a.ann_dir)
    tr_path, va_path = ann / f"{a.tower}_train.json", ann / f"{a.tower}_val.json"
    tr = json.loads(tr_path.read_text())
    if a.videos != "all":
        keep = set(HALVES[a.videos])
        tr["images"] = [im for im in tr["images"] if im["video"] in keep]
        ids = {im["id"] for im in tr["images"]}
        tr["annotations"] = [x for x in tr["annotations"] if x["image_id"] in ids]
    va = json.loads(va_path.read_text())
    train_videos = C.assert_no_test([im["stem"] for im in tr["images"]], f"{a.tower} train")
    val_videos = C.assert_no_test([im["stem"] for im in va["images"]], f"{a.tower} val")
    if {c["id"] for c in tr["categories"]} != set(range(1, tower["n"] + 1)):
        raise RuntimeError(f"注釈のクラスが {tower['n']} クラスでない: {tr['categories']}")
    lm = set().union(*[set((LOSS_MASK_DIR / f"{p}.txt").read_text().split()) for p in ("train", "val")])
    lm_hit = sorted({im["stem"] for im in tr["images"] + va["images"]} & lm)
    if tower["source"] == "hand_tool_seg" and lm_hit:
        raise RuntimeError(f"欠落の印の付いたフレームが学ぶフレームに {len(lm_hit)} 件ある。学習を始めない")
    (run / "logs").mkdir(parents=True, exist_ok=True)
    ckpt.mkdir(parents=True, exist_ok=True)
    model, cfg, load_report = build_model(tower["n"])
    if a.amp == "bf16":
        cfg.optim_wrapper.type = "AmpOptimWrapper"
        cfg.optim_wrapper.loss_scale = "dynamic"
        cfg.optim_wrapper.dtype = "bfloat16"
        patch_msda_bf16()
    optim = build_optim_wrapper(model, cfg.optim_wrapper)
    g = torch.Generator()
    g.manual_seed(a.seed)
    train_loader = torch.utils.data.DataLoader(FlipSwap(tr, True, tower["swap0"]), batch_size=a.batch, shuffle=True,
                                               num_workers=a.workers, collate_fn=T.collate, generator=g, persistent_workers=True,
                                               pin_memory=False, drop_last=True)  # nosemgrep
    val_loader = torch.utils.data.DataLoader(FlipSwap(va, False, tower["swap0"]), batch_size=2, shuffle=False,
                                             num_workers=a.workers, collate_fn=T.collate, pin_memory=False)  # nosemgrep
    name = run.name
    names = [c["name"] for c in sorted(tr["categories"], key=lambda c: c["id"])]
    config = {"task_id": TASK, "unofficial": True, "run": name, "tower": a.tower, "videos": a.videos, "train_videos": train_videos,
              "val_videos": val_videos, "train_frames": len(tr["images"]), "train_instances": len(tr["annotations"]),
              "train_frames_without_instance": len(tr["images"]) - len({x["image_id"] for x in tr["annotations"]}),
              "val_frames": len(va["images"]), "classes": tower["n"], "class_names": names, "source": tower["source"],
              "source_ids": tower["src_ids"], "ann_sha256": {"train": T.sha(tr_path), "val": T.sha(va_path)},
              "loss_mask_frames_in_data": len(lm_hit),
              "loss_mask_note": ("hand_tool_seg の欠落の印の一覧を照合（学ぶフレームに 0 件）" if tower["source"] == "hand_tool_seg"
                                 else "hand_seg に欠落の印の一覧は無い。hand_tool_seg の一覧のフレームとの重なりを記録するだけ"),
              "model": "mmdet Mask2Former R50 (mask2former_r50_8xb2-lsj-50e_coco)", "init": load_report,
              "input": f"短辺 {T.SHORT}・長辺 {T.LONG} まで（双線形）、学習は左右反転 0.5 でラベルを入れ替える、batch_augments なし、32 の倍数へ詰める",
              "flip_label_swap": {str(i + 1): int(j) + 1 for i, j in enumerate(tower["swap0"])},
              "batch": a.batch, "val_batch": 2, "optim_wrapper": json.loads(json.dumps(cfg.optim_wrapper.to_dict(), default=str)),
              "amp": a.amp, "msda_fp32_for_bf16": a.amp == "bf16", "eval_precision": "fp32", "max_epochs": a.max_epochs,
              "patience": a.patience, "lr_decay": None,
              "selection": "val のその塔の全クラスの mask mAP（pycocotools segm、元の解像度、上位 100）。改善 = 最良を厳密に上回る",
              "stop_rule": f"最良が {a.patience} epoch 更新されなければ打ち切り、上限 {a.max_epochs}、学習率は下げない",
              "seed": a.seed, "smoke": a.smoke, "wandb_mode": os.environ["WANDB_MODE"], "git_commit": T.git("rev-parse", "HEAD"),
              "code_sha256": {p: T.sha(PROJ / p) for p in ("scripts/grasppilot/ghg_tower.py", "scripts/grasppilot/g_train.py",
                                                         "scripts/grasppilot/g_bench.py", "scripts/grasppilot/g5_train.py")},
              "host": os.uname().nodename, "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}
    C.write_json(run / "config.json", config)
    (run / "command.sh").write_text("#!/usr/bin/env bash\n" + " ".join(map(str, [sys.executable] + sys.argv)) + "\n")
    (run / "git_commit.txt").write_text(config["git_commit"] + "\n")
    (run / "start.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    tracking.init(name, config=config, group=f"grasp_hand_graph_{a.tower}")
    print(json.dumps({k: config[k] for k in ("tower", "train_videos", "train_frames", "val_frames", "train_frames_without_instance")}),
          "init", load_report["loaded"], "/", load_report["n_checkpoint"], "skipped", load_report["skipped_shape"], flush=True)
    limit = a.smoke_val if a.smoke else None
    history = []
    pre = evaluate(model, val_loader, va_path, limit=limit)
    history.append({"epoch": 0, "lr": max(gr["lr"] for gr in optim.optimizer.param_groups), **pre})
    C.write_json(run / "logs/history.json", history)
    print(f"[{a.tower}] epoch=0 (学習前) segm_mAP={pre['segm_mAP']:.4f}", flush=True)
    tracking.log({"val/segm_mAP": pre["segm_mAP"]}, step=0)
    best, best_epoch, stopped_at = -1.0, None, None
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    epoch = 0
    state_meta = {"task_id": TASK, "num_classes": tower["n"], "tower": a.tower, "videos": a.videos}
    for epoch in range(1, a.max_epochs + 1):
        model.train()
        t0, tot, n = time.monotonic(), 0.0, 0
        for step, batch in enumerate(train_loader, start=1):
            inputs, samples = T.to_inputs(model, batch, training=True)
            with optim.optim_context(model):
                losses = model.loss(inputs, samples)
            loss, _ = model.parse_losses(losses)
            if not torch.isfinite(loss):
                raise RuntimeError(f"非数の損失 epoch {epoch} step {step}")
            optim.update_params(loss)
            tot += float(loss)
            n += 1
            if step % 200 == 0 or step == 1:
                print(f"[{a.tower}] ep{epoch} {step}/{len(train_loader)} loss={tot / n:.4f} {(time.monotonic() - t0) / step:.3f}s/step "
                      f"peak={torch.cuda.max_memory_allocated() / 2**30:.1f}GiB", flush=True)
            if a.smoke and step >= a.smoke_steps:
                break
        train_s = time.monotonic() - t0
        val = evaluate(model, val_loader, va_path, limit=limit)
        lr = max(gr["lr"] for gr in optim.optimizer.param_groups)
        improved = val["segm_mAP"] > best
        if improved:
            best, best_epoch = val["segm_mAP"], epoch
            torch.save({"state_dict": model.state_dict(), "epoch": epoch, **state_meta}, ckpt / "best.pth")
        rec = {"epoch": epoch, "lr": lr, "lr_backbone": min(gr["lr"] for gr in optim.optimizer.param_groups),
               "train_loss": tot / max(n, 1), "train_steps": n, "train_seconds": train_s, "improved": improved,
               "peak_alloc_bytes": int(torch.cuda.max_memory_allocated()), **val}
        history.append(rec)
        _, _, stale = stale_since_best(history)
        rec["stale"] = stale
        C.write_json(run / "logs/history.json", history)
        tracking.log({"train/loss": rec["train_loss"], "val/segm_mAP": val["segm_mAP"], "lr": lr}, step=epoch)
        print(f"[{a.tower}] epoch={epoch} lr={lr:g} loss={rec['train_loss']:.4f} segm_mAP={val['segm_mAP']:.4f} stale={stale} "
              f"train {train_s:.0f}s eval {val.get('infer_seconds', 0) + val.get('eval_seconds', 0):.0f}s", flush=True)
        if stale >= a.patience:
            stopped_at = epoch
            break
        if a.smoke and epoch >= 1:
            break
    torch.save({"state_dict": model.state_dict(), "epoch": epoch, **state_meta}, ckpt / "last.pth")
    best_rec = next(h for h in history if h["epoch"] == best_epoch)
    metrics = {"task_id": TASK, "unofficial": True, "run": name, "tower": a.tower, "videos": a.videos, "best_epoch": best_epoch,
               "best_segm_mAP": best, "pre_segm_mAP": pre["segm_mAP"], "epochs_completed": epoch,
               "early_stopped_epoch": stopped_at, "reached_epoch_cap": stopped_at is None and epoch == a.max_epochs,
               "elapsed_seconds": time.monotonic() - started, "peak_alloc_bytes": int(torch.cuda.max_memory_allocated()),
               "coco_weights_loaded": load_report["loaded"], "coco_weights_total": load_report["n_checkpoint"],
               "best_ckpt": str(ckpt / "best.pth"), "best_ckpt_sha256": T.sha(ckpt / "best.pth"),
               "last_ckpt_sha256": T.sha(ckpt / "last.pth"), "best_per_class_ap": best_rec["per_class_ap"]}
    C.write_json(run / "metrics.json", metrics)
    C.write_json(run / "per_class_ap.json", best_rec["per_class_ap"])
    (run / "notes.md").write_text(
        f"# {name}（非公式 {TASK}）\n\n塔 {a.tower}（Mask2Former R50、{tower['n']} クラス、{tower['source']}、反転でラベルを入れ替える）、"
        f"学ぶ動画 {train_videos}、val {val_videos}。\n最良 epoch {best_epoch}: {tower['n']} クラスの segm mAP {best:.4f}。"
        f"学習前 {pre['segm_mAP']:.4f}。\n回した epoch {epoch}、打ち切り {stopped_at}。test は通していない。\n")
    (run / "end.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    (run / "exit_code.txt").write_text("0\n")
    tracking.finish()
    print(f"[{a.tower}] DONE", json.dumps({k: v for k, v in metrics.items() if k != "best_per_class_ap"}, ensure_ascii=False), flush=True)


def cmd_evalpre(a):
    tower = tower_of(a.tower)
    va_path = Path(a.ann_dir) / f"{a.tower}_val.json"
    va = json.loads(va_path.read_text())
    model, info = load_trained("coco", tower["n"])
    loader = torch.utils.data.DataLoader(FlipSwap(va, False, tower["swap0"]), batch_size=2, shuffle=False, num_workers=8,
                                         collate_fn=T.collate)
    r = evaluate(model, loader, va_path)
    C.write_json(a.out, {"task_id": TASK, "tower": a.tower, **info, **r})
    print(json.dumps({"tower": a.tower, "segm_mAP": r["segm_mAP"], "per_class_ap": r["per_class_ap"]}), flush=True)


# ---------------------------------------------------------------- flipmodel（§3.4）
def class_P(labels, scores, probs, n, shape):
    """P_c(x) = max_{クラス c のインスタンス} (得点 × マスクの確率)。g5_signals.grasp_P の n クラス版。"""
    P = torch.zeros((n,) + tuple(shape), device=probs.device)
    for c in range(n):
        sel = labels == c
        if sel.any():
            P[c] = (scores[sel][:, None, None] * probs[sel]).amax(0)
    return P


def soft_iou(x, y):
    return float(torch.minimum(x, y).sum() / torch.maximum(x, y).sum().clamp_min(1e-9))


def frame_images(part, stems):
    return [{"id": i, "file_name": f"data/raw/ego/{part}/{C.video_of(s)}/{s}.jpg", "stem": s, "video": C.video_of(s),
             "height": 1080, "width": 1920} for i, s in enumerate(stems, start=1)]


def cmd_flipmodel(a):
    """反転した画像の P をラベルで入れ替え（swap）または入れ替えず（noswap）に反転し直し、元の画像の P と soft IoU で比べる。
    11-05 の整合の検査（g5_signals.flipcheck）と同じ規則: 270×480、両方の最大が 0.05 未満のクラスは数えない。"""
    from grasppilot import g_signals as GS
    tower = tower_of(a.tower)
    va = json.loads((Path(a.ann_dir) / f"{a.tower}_val.json").read_text())
    stems = sorted(np.random.default_rng(42).choice([im["stem"] for im in va["images"]], a.frames, replace=False).tolist())
    C.assert_no_test(stems, "flipmodel")
    ds = T.G38({"images": frame_images("val", stems), "annotations": []}, train=False)
    loader = torch.utils.data.DataLoader(ds, batch_size=1, shuffle=False, num_workers=4, collate_fn=T.collate)
    model, info = load_trained(a.ckpt, tower["n"])
    names = [c["name"] for c in sorted(va["categories"], key=lambda c: c["id"])]
    acc = {m: {c: [] for c in names} for m in ("swap", "noswap")}
    with torch.no_grad():
        for batch in loader:
            arr, meta, _ = batch[0]
            Ps = []
            for flip in (False, True):
                b = [(arr[:, ::-1].copy() if flip else arr, meta, None)]
                inputs, samples = T.to_inputs(model, b, training=False)
                labels, scores, probs = GS.instances(model, inputs, samples, (270, 480))[0]
                Ps.append(class_P(labels, scores, probs, tower["n"], (270, 480)))
            P0, back = Ps[0], Ps[1].flip(-1)
            for mode, perm in (("swap", tower["swap0"].tolist()), ("noswap", list(range(tower["n"])))):
                Q = back[perm]
                for c, nm in enumerate(names):
                    if P0[c].max() < 0.05 and Q[c].max() < 0.05:
                        continue
                    acc[mode][nm].append(soft_iou(P0[c], Q[c]))
    res = {"task_id": TASK, "tower": a.tower, "label": a.label, **info, "frames": len(stems), "stems": stems,
           "rule": "P_c を 270×480 で作り、反転した画像の P をラベルで入れ替え（swap）または入れ替えず（noswap）に反転し直して元の P と比べる。"
                   "soft IoU = Σmin/Σmax。両方の最大が 0.05 未満のクラスは数えない",
           "per_class": {m: {n: {"frames_counted": len(v), "soft_iou_mean": float(np.mean(v)) if v else None} for n, v in d.items()}
                         for m, d in acc.items()}}
    for m in ("swap", "noswap"):
        vals = [v["soft_iou_mean"] for v in res["per_class"][m].values() if v["soft_iou_mean"] is not None]
        res[f"{m}_soft_iou_mean_over_classes"] = float(np.mean(vals)) if vals else None
        lr = [res["per_class"][m][names[c]]["soft_iou_mean"] for c in range(tower["n"]) if tower["swap0"][c] != c]
        res[f"{m}_soft_iou_mean_over_lr_classes"] = float(np.mean([x for x in lr if x is not None])) if lr else None
    C.write_json(a.out, res)
    print(json.dumps({k: res[k] for k in ("tower", "label", "swap_soft_iou_mean_over_classes", "noswap_soft_iou_mean_over_classes",
                                          "swap_soft_iou_mean_over_lr_classes", "noswap_soft_iou_mean_over_lr_classes")}), flush=True)


# ---------------------------------------------------------------- infer（Task C の信号）
def cmd_infer(a):
    """工程の経路のフレームに当て、mmdet の instance_postprocess と同じ上位 100 のインスタンス（g_signals.instances）の
    ラベル・得点・元の解像度の二値マスク（確率 > 0.5）の外接矩形（画像の大きさで割った xyxy）・面積の割合を保存する。"""
    from grasppilot import g_signals as GS
    tower = tower_of(a.tower)
    part, videos = a.part, a.videos.split(",")
    C.assert_no_test(videos, f"{a.tower} infer")
    fold = C.fold_a()
    assert set(videos) <= set(fold[part]), (videos, part)
    seqs = {v: fr for v, fr, _ in C.phase_sequences(videos)}
    stems = [f for v in videos for f in seqs[v]]
    if a.limit:
        stems = stems[:a.limit]
    missing = [s for s in stems if not (PROJ / f"data/raw/ego/{part}/{C.video_of(s)}/{s}.jpg").exists()]
    present = [s for s in stems if s not in set(missing)]
    ds = T.G38({"images": frame_images(part, present), "annotations": []}, train=False)
    loader = torch.utils.data.DataLoader(ds, batch_size=2, shuffle=False, num_workers=a.workers, collate_fn=T.collate)
    model, info = load_trained(a.ckpt, tower["n"])
    n = len(present)
    labels = np.full((n, TOPK), -1, np.int16)
    scores = np.zeros((n, TOPK), np.float32)
    boxes = np.zeros((n, TOPK, 4), np.float32)
    area = np.zeros((n, TOPK), np.float32)
    empty_masks = 0
    H, W = 1080, 1920
    t0 = time.monotonic()
    k = 0
    with torch.no_grad():
        for batch in loader:
            inputs, samples = T.to_inputs(model, batch, training=False)
            for (lb, sc, pr), (_, meta, _) in zip(GS.instances(model, inputs, samples, (H, W)), batch):
                assert meta["stem"] == present[k]
                order = torch.argsort(sc, descending=True)
                lb, sc, binm = lb[order], sc[order], pr[order] > 0.5
                rows, cols = binm.any(2), binm.any(1)                    # (100, H)、(100, W)
                has = rows.any(1)
                ar = torch.arange(H, device=binm.device)
                ac = torch.arange(W, device=binm.device)
                y0 = torch.where(rows, ar, H).amin(1)
                y1 = torch.where(rows, ar, -1).amax(1) + 1
                x0 = torch.where(cols, ac, W).amin(1)
                x1 = torch.where(cols, ac, -1).amax(1) + 1
                bx = torch.stack([x0 / W, y0 / H, x1 / W, y1 / H], 1).float()
                bx[~has] = 0.0
                labels[k] = lb.cpu().numpy().astype(np.int16)
                scores[k] = sc.float().cpu().numpy()
                boxes[k] = bx.cpu().numpy()
                area[k] = (binm.flatten(1).sum(1).float() / (H * W)).cpu().numpy()
                empty_masks += int((~has).sum())
                k += 1
            if k % 500 < 2:
                print(f"[infer] {a.tower} {a.g} {part} {k}/{n} {(time.monotonic() - t0) / k:.3f}s/frame", flush=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(str(out) + ".npz", frame_ids=np.asarray(present), labels=labels, scores=scores, boxes=boxes, area=area,
             class_names=np.asarray([str(i) for i in tower["src_ids"]]))
    rep = {"task_id": TASK, "tower": a.tower, "g": a.g, **info, "part": part, "videos": videos, "frames_phase_path": len(stems),
           "frames": n, "frames_without_image": len(missing), "missing_examples": missing[:5], "topk": TOPK,
           "empty_mask_instances": empty_masks, "seconds": time.monotonic() - t0, "npz_sha256": C.sha256(str(out) + ".npz"),
           "code_sha256": C.sha256(Path(__file__)), "box_rule": "元の解像度の二値マスク（確率 > 0.5）の外接矩形を画像の大きさで割った xyxy。空のマスクは 0"}
    C.write_json(str(out) + "_report.json", rep)
    print("[infer] DONE", json.dumps(rep, ensure_ascii=False), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("--tower", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--check-frames", type=int, default=8)
    p = sub.add_parser("flipdata")
    p.add_argument("--tower", required=True)
    p.add_argument("--ann-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--frames", type=int, default=24)
    p = sub.add_parser("train")
    p.add_argument("--tower", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--ckpt-dir", required=True)
    p.add_argument("--ann-dir", required=True)
    p.add_argument("--videos", choices=("all", "H1", "H2"), required=True)
    p.add_argument("--max-epochs", type=int, default=36)
    p.add_argument("--patience", type=int, default=4)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--batch", type=int, default=8)
    p.add_argument("--amp", choices=("none", "bf16"), default="bf16")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--smoke-steps", type=int, default=20)
    p.add_argument("--smoke-val", type=int, default=10)
    p = sub.add_parser("evalpre")
    p.add_argument("--tower", required=True)
    p.add_argument("--ann-dir", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("flipmodel")
    p.add_argument("--tower", required=True)
    p.add_argument("--ann-dir", required=True)
    p.add_argument("--ckpt", required=True, help="重みのファイル、または coco（学習前）")
    p.add_argument("--label", required=True)
    p.add_argument("--frames", type=int, default=40)
    p.add_argument("--out", required=True)
    p = sub.add_parser("infer")
    p.add_argument("--tower", required=True)
    p.add_argument("--ckpt", required=True)
    p.add_argument("--g", choices=("all", "H1", "H2"), required=True, help="当てる塔（記録用）")
    p.add_argument("--part", choices=("train", "val"), required=True)
    p.add_argument("--videos", required=True)
    p.add_argument("--out", required=True, help="接頭辞（.npz と _report.json を書く）")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    {"build": cmd_build, "flipdata": cmd_flipdata, "train": cmd_train, "evalpre": cmd_evalpre, "flipmodel": cmd_flipmodel,
     "infer": cmd_infer}[a.cmd](a)


if __name__ == "__main__":
    main()

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


# ---------------------------------------------------------------- assemble（腕ごとの置き場、確かめ、案 D の目録）
PROBE_SIG = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe/signals")
HALVES = {"H1": ["01", "06", "11", "12", "15"], "H2": ["02", "03", "08", "13", "14"]}
G_BIN = {"L_hand": 0, "L_grasp": 1, "R_hand": 5, "R_grasp": 6, "B_present": 10}


def load_raw(prefix):
    z = np.load(str(prefix) + "_sig.npz")
    d = {k: z[k] for k in z.files}
    d["frame_ids"] = [str(f) for f in d["frame_ids"]]
    d["row"] = {f: i for i, f in enumerate(d["frame_ids"])}
    d["maps_path"] = str(prefix) + "_m.npy"
    d["report"] = json.loads(Path(str(prefix) + "_report.json").read_text())
    return d


def make_mapping(frames, seed=42):
    """一本目の前の契約の shuffle_signals.make_mapping と同じ（名前の昇順に並べ、seed 42 の並べ替え）。"""
    from stage2pilot.shuffle_signals import make_mapping as mm
    return mm(frames, seed)


def mapping_stats(mapping):
    from stage2pilot.shuffle_signals import mapping_stats as ms
    return ms(mapping)


def cf_source(video):
    """train の動画 v の信号を作る G: v が H1 なら H2 の G、H2 なら H1 の G（その動画を学んでいない半分）。"""
    if video in HALVES["H1"]:
        return "H2"
    if video in HALVES["H2"]:
        return "H1"
    raise ValueError(video)


def provenance_check(sources, learned):
    """フレームごとの (動画, 信号を作った G) が、その G の学んだ動画を含まないか。外れの件数を返す。"""
    bad = [(f, g) for f, g in sources.items() if C.video_of(f) in learned[g]]
    return {"frames": len(sources), "violations": len(bad), "examples": bad[:3]}


def roc_auc(y, s):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else None


def write_g(path, frames, g, src_rows=None):
    x = g if src_rows is None else g[src_rows]
    np.savez(path, frame_ids=np.asarray(frames), x=x.astype(np.float32), flag=np.ones(len(frames), np.float32),
             names=np.asarray(G.G_NAMES))
    return {"path": str(path), "sha256": sha(path), "frames": len(frames),
            "range": [float(x.min()), float(x.max())]}


def assemble(a):
    raw = Path(a.raw)
    out = Path(a.out)
    for d in ("A", "B", "C", "D", "views"):
        (out / d).mkdir(parents=True, exist_ok=True)
    fold = C.fold_a()
    seqs = {v: fr for v, fr, _ in C.phase_sequences(fold["train"] + fold["val"])}
    frames = {p: [f for v in fold[p] for f in seqs[v]] for p in ("train", "val")}
    R = {"all_train": load_raw(raw / "all_train"), "all_val": load_raw(raw / "all_val"),
         "H1_on_H2": load_raw(raw / "H1_on_H2"), "H2_on_H1": load_raw(raw / "H2_on_H1")}
    learned = {g: json.loads(Path(a.g_runs[g]).read_text())["train_videos"] for g in ("all", "H1", "H2")}
    rep = {"task_id": TASK, "unofficial": True, "code_sha256": sha(Path(__file__)), "learned_videos": learned,
           "raw": {k: v["report"] for k, v in R.items()}}
    # 交差適合の train: フレームごとの出所
    cf_rows, sources = [], {}
    for f in frames["train"]:
        g = cf_source(C.video_of(f))
        key = "H1_on_H2" if g == "H1" else "H2_on_H1"
        cf_rows.append((key, R[key]["row"][f]))
        sources[f] = g
    rep["D3_crossfit"] = provenance_check(sources, learned)
    rep["D3_crossfit_per_video"] = {v: sorted({sources[f] for f in seqs[v]}) for v in fold["train"]}
    mixed = dict(sources)
    for f in frames["train"][:: max(1, len(frames["train"]) // 5)][:5]:
        mixed[f] = "all"                                   # 陽性対照: 確定の G で作った train の信号を混ぜた写し
    rep["D3_crossfit_control_mixed_all"] = provenance_check(mixed, learned)
    rep["D3_val_from"] = provenance_check({f: "all" for f in frames["val"]}, learned)

    def cf_take(key):
        return np.stack([R[k][key][i] for k, i in cf_rows])

    allrow = {p: [R[f"all_{p}"]["row"][f] for f in frames[p]] for p in ("train", "val")}
    maps = {}
    for p in ("train", "val"):
        maps[p] = mapping = make_mapping(frames[p])
        rep[f"D5_shuffle_{p}"] = mapping_stats(mapping)
    # 案 A
    A = {}
    for p in ("train", "val"):
        gno = R[f"all_{p}"]["g"][allrow[p]]
        A[f"pred_noCF_{p}"] = write_g(out / f"A/g_pred_noCF_{p}.npz", frames[p], gno)
        gcf = cf_take("g") if p == "train" else gno
        A[f"pred_CF_{p}"] = write_g(out / f"A/g_pred_CF_{p}.npz", frames[p], gcf)
        pos = {f: i for i, f in enumerate(frames[p])}
        A[f"shuffle_{p}"] = write_g(out / f"A/g_shuffle_{p}.npz", frames[p], gno, [pos[maps[p][f]] for f in frames[p]])
    rep["A"] = A
    # 案 B（見取り）
    cf_maps = out / "B/pred_CF_train_m.npy"
    src = {k: np.load(R[k]["maps_path"], mmap_mode="r") for k in ("H1_on_H2", "H2_on_H1")}
    mm = np.lib.format.open_memmap(str(cf_maps), mode="w+", dtype=np.uint8, shape=(len(frames["train"]), 5, MAP_H, MAP_W))
    for j, (k, i) in enumerate(cf_rows):
        mm[j] = src[k][i]
    mm.flush()
    B = {}
    for arm in ("pred_noCF", "pred_CF", "shuffle"):
        for p in ("train", "val"):
            if arm == "pred_CF" and p == "train":
                view = {"maps": str(cf_maps), "frame_ids": frames["train"], "mapping": None}
            else:
                key = f"all_{p}"
                view = {"maps": R[key]["maps_path"], "frame_ids": R[key]["frame_ids"],
                        "mapping": maps[p] if arm == "shuffle" else None}
            vp = out / f"views/B_{arm}_{p}.json"
            vp.write_text(json.dumps({**view, "arm": arm, "part": p, "task_id": TASK}))
            B[f"{arm}_{p}"] = {"view": str(vp), "view_sha256": sha(vp), "maps": view["maps"], "maps_sha256": sha(view["maps"])}
    rep["B"] = B
    # 案 C
    Cc = {}
    tcf = cf_take("t")
    pos = {f: i for i, f in enumerate(frames["train"])}
    for name, arr, fr in (("teacher_train", tcf, frames["train"]),
                          ("shuffled_train", tcf[[pos[maps["train"][f]] for f in frames["train"]]], frames["train"]),
                          ("val", R["all_val"]["t"][allrow["val"]], frames["val"])):
        path = out / f"C/t_{name}.npz"
        np.savez(path, frame_ids=np.asarray(fr), t=arr.astype(np.float32), values=np.asarray(T_VALUES))
        r3 = arr.reshape(-1, 3, 16)
        Cc[name] = {"path": str(path), "sha256": sha(path), "frames": len(fr),
                    "rowsum_maxdev": float(np.abs(r3.sum(2) - 1).max()),
                    "none_mass_quantiles": {h: np.quantile(r3[:, k, -1], [0.1, 0.25, 0.5, 0.75, 0.9]).round(4).tolist()
                                            for k, h in enumerate(HANDS)},
                    "mass_by_value": {h: dict(zip(T_VALUES, r3[:, k].sum(0).round(2).tolist())) for k, h in enumerate(HANDS)},
                    "argmax_counts": {h: dict(zip(T_VALUES, np.bincount(r3[:, k].argmax(1), minlength=16).tolist()))
                                      for k, h in enumerate(HANDS)}}
    bad = tcf.reshape(-1, 3, 16).copy()
    bad[0, 0, 0] += 0.5                                     # 陽性対照: 値を一つ変えた写し
    Cc["D4_control_one_value_changed_rowsum_maxdev"] = float(np.abs(bad.sum(2) - 1).max())
    probe = json.loads((PROBE_SIG / "summary.json").read_text())
    Cc["gt_grasped_tool_class_train"] = probe["parts"]["train"]["caseC_grasped_tool_class"]
    rep["C"] = Cc
    # 案 D（train の q は交差適合、val の q は確定の G）
    Dd = {}
    for p in ("train", "val"):
        parts = [R["H1_on_H2"], R["H2_on_H1"]] if p == "train" else [R["all_val"]]
        box_ids = np.concatenate([x["box_ids"] for x in parts])
        q = np.concatenate([x["q"] for x in parts])
        r = np.concatenate([x["r"] for x in parts])
        order = np.argsort(box_ids)
        path = out / f"D/q_{'CF' if p == 'train' else 'noCF'}_{p}.npz"
        np.savez(path, ann_ids=box_ids[order], q=q[order], r=r[order], values=np.asarray(["left", "right", "both", "none"]))
        tool = json.loads((C.DET_ANN_A / f"instances_{p}.json").read_text())
        n_ann = len(tool["annotations"])
        Dd[p] = {"path": str(path), "sha256": sha(path), "boxes": int(len(box_ids)), "boxes_in_annotation_file": n_ann,
                 "unique": int(len(np.unique(box_ids))), "q_rowsum_range": [float(q.sum(1).min()), float(q.sum(1).max())],
                 "made_by": "交差適合（H1 の G を H2 の動画に、H2 の G を H1 の動画に）" if p == "train" else "確定の G"}
    rep["D"] = Dd
    man = {"task_id": TASK, "unofficial": True, "for": "T-2026-11-01-grasp-pilot-d（三本目、bengio）",
           "host": "andrew", "train_q": Dd["train"], "val_q": Dd["val"],
           "format": {"ann_ids": "折り A の術具の注釈（data/annotations/egosurgery_tool_folds/A/instances_{part}.json）の annotation id、昇順",
                      "q": "(枠, 4) の軟らかい 4 値 [左, 右, 両手, なし]（一本目の SPEC §3.3 の式に G の P_c を当てた）",
                      "r": "(枠, 3) の r_c(b)（左・右・両手の器具の確率の枠の中の平均）"},
           "g_runs": {g: {"config": a.g_runs[g], "ckpt_sha256": R[k]["report"]["ckpt_sha256"]}
                      for g, k in (("H1", "H1_on_H2"), ("H2", "H2_on_H1"), ("all", "all_val"))},
           "code_sha256": sha(Path(__file__))}
    C.write_json(Path(a.manifest), man)
    C.write_json(out / "assemble_report.json", rep)
    print(json.dumps({k: rep[k] for k in ("D3_crossfit", "D3_crossfit_control_mixed_all", "D3_val_from")}, ensure_ascii=False))
    print(json.dumps(rep["D"], ensure_ascii=False))


def _gt_map_small(stem):
    m = _IDX.map_channels(stem).astype(np.float32)          # (5, 1080, 1920) の 0 と 1
    return m.reshape(5, MAP_H, POOL, MAP_W, POOL).mean((2, 4)) >= 0.5


def _init_idx():
    global _IDX
    _IDX = G.HTSIndex(("train", "val"))


def compare(a):
    """Task D-2: G の g を一本目の正解の g と（二値の 5 次元の ROC-AUC、注釈のあるフレーム）、m をチャネルごとの IoU で比べる。"""
    from multiprocessing import Pool
    d = load_raw(a.raw)
    part = a.part
    with np.load(PROBE_SIG / f"g_{part}.npz") as z:
        gid = {str(f): i for i, f in enumerate(z["frame_ids"])}
        gx, gflag = z["x"], z["flag"]
    frames = [f for f in d["frame_ids"] if f in gid and gflag[gid[f]] > 0]
    pg = d["g"][[d["row"][f] for f in frames]]
    tg = gx[[gid[f] for f in frames]]
    res = {"raw": a.raw, "part": part, "g": d["report"]["g"], "frames_annotated": len(frames),
           "roc_auc": {k: roc_auc(tg[:, j] > 0.5, pg[:, j]) for k, j in G_BIN.items()},
           "pred_mean": {k: float(pg[:, j].mean()) for k, j in G_BIN.items()},
           "gt_positive_rate": {k: float((tg[:, j] > 0.5).mean()) for k, j in G_BIN.items()}}
    maps = np.load(d["maps_path"], mmap_mode="r")
    pick = frames if not a.max_frames else [frames[i] for i in np.linspace(0, len(frames) - 1, a.max_frames).astype(int)]
    inter, union = np.zeros(5), np.zeros(5)
    with Pool(a.workers, initializer=_init_idx) as pool:
        for f, gt in zip(pick, pool.imap(_gt_map_small, pick, chunksize=8)):
            pr = maps[d["row"][f]] >= 128
            inter += (pr & gt).reshape(5, -1).sum(1)
            union += (pr | gt).reshape(5, -1).sum(1)
    res["map_iou"] = dict(zip(["tool_L", "tool_R", "tool_B", "hand_L", "hand_R"], (inter / np.maximum(union, 1)).round(4).tolist()))
    res["map_frames"] = len(pick)
    res["map_rule"] = "予測 ≥ 128/255（0.5）と、正解の地図の 4×4 の平均 ≥ 0.5 を 270×480 で比べ、全フレームの画素で IoU"
    C.write_json(a.out, res)
    print(json.dumps(res, ensure_ascii=False), flush=True)


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
    p = sub.add_parser("assemble")
    p.add_argument("--raw", required=True, help="infer の出力の置き場（all_train・all_val・H1_on_H2・H2_on_H1）")
    p.add_argument("--out", required=True)
    p.add_argument("--manifest", default=str(PROJ / "experiments/analysis/grasp_pilot_g/targets/D_manifest.json"))
    p.add_argument("--g-run", nargs=3, metavar=("ALL", "H1", "H2"), required=True, help="G の 3 本の config.json")
    p = sub.add_parser("compare")
    p.add_argument("--raw", required=True, help="infer の出力の接頭辞")
    p.add_argument("--part", choices=("train", "val"), required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-frames", type=int, default=0, help="地図の IoU に使うフレームの数（0 なら全部）")
    p.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.cmd == "assemble":
        a.g_runs = dict(zip(("all", "H1", "H2"), a.g_run))
    {"infer": infer, "assemble": assemble, "compare": compare}[a.cmd](a)


if __name__ == "__main__":
    main()

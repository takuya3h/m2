"""5 クラスの G から信号と標的を作り、検査する（非公式 T-2026-11-05-grasp-tower-rebuild、SPEC §3.3〜§3.5、Task C-3・D）。本体の .venv。

二本目の `g_signals.py` を変えずに、その部品（`instances`・`make_mapping`・`mapping_stats`・`cf_source`・`provenance_check`）を使う派生。
二本目との違い: 頭が 5 クラス（ラベル 0〜4 がそのまま P_1..P_5）、旗の列を作らない、案 C の t を作らない、
q の行の和が 1 を超える枠は 4 値を和で割って 1 にする（切らない）。

infer       一つの G を指定の split と動画の工程の経路のフレームに当てる。出力の形は二本目の infer と同じ名前
            （<prefix>_sig.npz に frame_ids・g・box_ids・q・r、<prefix>_m.npy、<prefix>_report.json）で、
            二本目の `g_signals.py compare` がそのまま読める（t と flag は無い）
merge       train の推論を分けたときに一つにまとめる
assemble    腕ごとの置き場（交差適合、入れ替え、q の正規化）、確かめと対照、目録 signals_manifest.json
flipcheck   反転の整合（§3.3）。val の数十フレームで、反転した画像の P をラベルを入れ替えて反転し直し、元の画像の P と比べる
evalval     val の 5 クラスの mask mAP を、欠落の印の付いたフレームを除いた値（1,514）と含めた値（印のフレームを注釈なしの画像として足す）で測る

    .venv/bin/python scripts/grasppilot/g5_signals.py infer --ckpt best.pth --g all|H1|H2 --part train|val --videos 01,06,... --out <prefix>
"""
from __future__ import annotations

import argparse
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
from grasppilot import g_signals as GS  # noqa: E402
from grasppilot import grasp_signals as G  # noqa: E402
from stage2pilot import common as C  # noqa: E402

TASK = "T-2026-11-05-grasp-tower-rebuild"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK
MAP_H, MAP_W, POOL = GS.MAP_H, GS.MAP_W, GS.POOL
GRASP_CH = GS.GRASP_CH                     # hand_L 0, hand_R 1, tool_L 2, tool_R 3, tool_B 4
HALVES = GS.HALVES
SWAP0 = [1, 0, 3, 2, 4]
sha = GS.sha


def load_model(ckpt, num_classes):
    from grasppilot import g_bench as B
    model, _ = B.mmdet_model(num_classes=num_classes)
    if ckpt == "coco":                      # 学習前（g5_train.py と同じ順で作る: seed 42 → 構造 → COCO の重み）
        from grasppilot import g5_train as G5
        torch.manual_seed(42)
        np.random.seed(42)
        model, _, rep = G5.build_model()
        model.eval()
        return model, {"ckpt": "coco", "load": rep}
    state = torch.load(ckpt, map_location="cpu")
    model.load_state_dict(state["state_dict"])
    model.eval()
    return model, {"ckpt": str(ckpt), "ckpt_sha256": sha(ckpt), "epoch": state.get("epoch"), "task_id": state.get("task_id")}


def grasp_P(labels, scores, probs, shape):
    """P_c(x) = max_{クラス c のインスタンス} (スコア × マスクの確率)、c = 0〜4（38 クラスの G でも先頭 5 クラスが把持関係）。"""
    P = torch.zeros((5,) + tuple(shape), device=probs.device)
    for c in range(5):
        sel = labels == c
        if sel.any():
            P[c] = (scores[sel][:, None, None] * probs[sel]).amax(0)
    return P


def frame_images(part, stems):
    return [{"id": i, "file_name": f"data/raw/ego/{part}/{C.video_of(s)}/{s}.jpg", "stem": s, "video": C.video_of(s),
             "height": 1080, "width": 1920} for i, s in enumerate(stems, start=1)]


# ---------------------------------------------------------------- infer
def infer(a):
    from grasppilot.g_train import G38, collate, to_inputs
    part, videos = a.part, a.videos.split(",")
    C.assert_no_test(videos, "g5_signals infer")
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
    ds = G38({"images": frame_images(part, stems), "annotations": []}, train=False)
    loader = torch.utils.data.DataLoader(ds, batch_size=2, shuffle=False, num_workers=a.workers, collate_fn=collate)
    model, info = load_model(a.ckpt, 5)
    if info.get("task_id") != TASK:
        raise RuntimeError(f"本契約の G ではない: {info}")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    maps = np.lib.format.open_memmap(str(out) + "_m.npy", mode="w+", dtype=np.uint8, shape=(len(stems), 5, MAP_H, MAP_W))
    g = np.zeros((len(stems), 14), np.float32)
    box_ids, q, r = [], [], []
    t0 = time.monotonic()
    k = 0
    with torch.no_grad():
        for batch in loader:
            inputs, samples = to_inputs(model, batch, training=False)
            for (labels, scores, probs), (_, meta, _) in zip(GS.instances(model, inputs, samples, (1080, 1920)), batch):
                P = grasp_P(labels, scores, probs, (1080, 1920))
                stem = meta["stem"]
                assert stem == stems[k]
                ch = {name: P[j].cpu().numpy() for name, j in GRASP_CH.items()}
                g[k] = G.summary_g(ch)
                mm = F.avg_pool2d(P[[2, 3, 4, 0, 1]][None], POOL)[0]
                maps[k] = torch.round(mm * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()
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
                print(f"[sig5] {a.g} {part} {k}/{len(stems)} {(time.monotonic() - t0) / k:.3f}s/frame", flush=True)
    maps.flush()
    np.savez(str(out) + "_sig.npz", frame_ids=np.asarray(stems), g=g, box_ids=np.asarray(box_ids, np.int64),
             q=np.concatenate(q).astype(np.float32), r=np.concatenate(r).astype(np.float32))
    rep = {"task_id": TASK, "g": a.g, **info, "part": part, "videos": videos, "frames": len(stems), "boxes": len(box_ids),
           "seconds": time.monotonic() - t0, "sig_sha256": sha(str(out) + "_sig.npz"), "maps_sha256": sha(str(out) + "_m.npy"),
           "maps_shape": list(maps.shape), "code_sha256": sha(Path(__file__)), "g_range": [float(g.min()), float(g.max())]}
    C.write_json(str(out) + "_report.json", rep)
    print("[sig5] DONE", json.dumps(rep), flush=True)


def merge(a):
    parts = [GS.load_raw(p) for p in a.parts]
    out = str(a.out)
    frames = [f for d in parts for f in d["frame_ids"]]
    assert len(frames) == len(set(frames))
    maps = np.lib.format.open_memmap(out + "_m.npy", mode="w+", dtype=np.uint8, shape=(len(frames), 5, MAP_H, MAP_W))
    k = 0
    for d in parts:
        m = np.load(d["maps_path"], mmap_mode="r")
        maps[k:k + len(m)] = m
        k += len(m)
    maps.flush()
    cat = {key: np.concatenate([d[key] for d in parts]) for key in ("g", "box_ids", "q", "r")}
    np.savez(out + "_sig.npz", frame_ids=np.asarray(frames), **cat)
    reps = [d["report"] for d in parts]
    assert len({r["ckpt_sha256"] for r in reps}) == 1
    rep = {**reps[0], "videos": [v for r in reps for v in r["videos"]], "frames": len(frames), "boxes": int(len(cat["box_ids"])),
           "seconds": sum(r["seconds"] for r in reps), "merged_from": list(map(str, a.parts)),
           "sig_sha256": sha(out + "_sig.npz"), "maps_sha256": sha(out + "_m.npy"), "maps_shape": list(maps.shape),
           "g_range": [float(cat["g"].min()), float(cat["g"].max())]}
    C.write_json(out + "_report.json", rep)
    print("[merge5]", json.dumps(rep, ensure_ascii=False), flush=True)


# ---------------------------------------------------------------- assemble
def normalize_q(q):
    """行の和が 1 を超える枠は 4 値を和で割る（切らない）。超えた枠の数と最大の和を返す。"""
    q = q.astype(np.float64)
    s = q.sum(1)
    over = s > 1.0
    out = q.copy()
    out[over] = q[over] / s[over][:, None]
    return out.astype(np.float32), {"boxes": int(len(q)), "rows_over_1": int(over.sum()),
                                    "max_rowsum_before": float(s.max()) if len(s) else None}


def q_check(ids, q, want_ids):
    s = q.astype(np.float64).sum(1)
    have = set(ids.tolist())
    return {"n_q": int(len(ids)), "n_unique": int(len(have)), "missing": int(len(set(want_ids) - have)),
            "extra": int(len(have - set(want_ids))), "rowsum_max_abs_err": float(np.abs(s - 1).max()),
            "value_min": float(q.min()), "ok": bool(np.abs(s - 1).max() <= 1e-5 and q.min() >= 0 and have == set(want_ids))}


def shuffle_q(ids, q, ann, seed=42):
    """同じフレームの枠の間で q を並べ替える（三本目の d_targets.py shuffle と同じ作り方: 画像 id の昇順、画像ごとに rng.permutation）。"""
    from grasppilot.d_targets import boxes_by_image
    by, _, _ = boxes_by_image(ann)
    row = {int(x): i for i, x in enumerate(ids)}
    rng = np.random.default_rng(seed)
    out_ids, out_q, same, multi, same_multi = [], [], 0, 0, 0
    for img in sorted(by):
        bxs = [b for b in by[img] if b in row]
        if not bxs:
            continue
        perm = rng.permutation(len(bxs))
        for k, b in enumerate(bxs):
            src = bxs[int(perm[k])]
            out_ids.append(b)
            out_q.append(q[row[src]])
            same += src == b
            if len(bxs) > 1:
                multi += 1
                same_multi += src == b
    order = np.argsort(out_ids)
    stats = {"boxes": len(out_ids), "same_box_fraction": same / max(len(out_ids), 1),
             "boxes_in_multi_box_frames": multi, "same_box_fraction_in_multi": same_multi / max(multi, 1), "seed": seed}
    return np.asarray(out_ids, np.int64)[order], np.stack(out_q)[order], stats


def videos_used_check(videos):
    v = set(videos)
    return {"videos": sorted(v), "test_overlap": sorted(v & set(C.TEST_VIDEOS)), "n_overlap": len(v & set(C.TEST_VIDEOS))}


def write_g(path, frames, x):
    """案 A の g。旗の列は作らない（SPEC §3.4）。"""
    np.savez(path, frame_ids=np.asarray(frames), x=x.astype(np.float32), names=np.asarray(G.G_NAMES))
    return {"path": str(path), "sha256": sha(path), "frames": len(frames), "dims": int(x.shape[1]),
            "range": [float(x.min()), float(x.max())], "has_flag": False}


def write_q(path, ids, q, r=None):
    kw = {"r": r} if r is not None else {}
    np.savez(path, ann_ids=ids, q=q, values=np.asarray(["left", "right", "both", "none"]), **kw)
    return {"path": str(path), "sha256": sha(path), "boxes": int(len(ids)),
            "range": [float(q.min()), float(q.max())], "rowsum_range": [float(q.sum(1).min()), float(q.sum(1).max())]}


def assemble(a):
    raw, out = Path(a.raw), Path(a.out)
    for d in ("A", "B", "D", "views"):
        (out / d).mkdir(parents=True, exist_ok=True)
    fold = C.fold_a()
    seqs = {v: fr for v, fr, _ in C.phase_sequences(fold["train"] + fold["val"])}
    frames = {p: [f for v in fold[p] for f in seqs[v]] for p in ("train", "val")}
    R = {k: GS.load_raw(raw / k) for k in ("all_train", "all_val", "H1_on_H2", "H2_on_H1")}
    for k, d in R.items():
        if d["report"].get("task_id") != TASK:
            raise RuntimeError(f"本契約の出力ではない: {k}")
    learned = {g: json.loads(Path(p).read_text())["train_videos"] for g, p in zip(("all", "H1", "H2"), a.g_run)}
    rep = {"task_id": TASK, "unofficial": True, "code_sha256": sha(Path(__file__)), "learned_videos": learned,
           "raw": {k: v["report"] for k, v in R.items()}}
    # h: 各段で通した動画の集合と test の共通
    used = {"G_train_all": learned["all"], "G_train_H1": learned["H1"], "G_train_H2": learned["H2"],
            **{f"infer_{k}": v["report"]["videos"] for k, v in R.items()}}
    rep["h_test_unused"] = {k: videos_used_check(v) for k, v in used.items()}
    rep["h_control_04_mixed"] = videos_used_check(list(used["G_train_all"]) + ["04"])
    # 交差適合の train
    cf_rows, sources = [], {}
    for f in frames["train"]:
        g = GS.cf_source(C.video_of(f))
        key = "H1_on_H2" if g == "H1" else "H2_on_H1"
        cf_rows.append((key, R[key]["row"][f]))
        sources[f] = g
    rep["D3_crossfit"] = GS.provenance_check(sources, learned)
    rep["D3_crossfit_per_video"] = {v: {"made_by": sorted({sources[f] for f in seqs[v]}),
                                        "learned_by_that_G": any(v in learned[g] for g in {sources[f] for f in seqs[v]})}
                                    for v in fold["train"]}
    mixed = dict(sources)
    for f in frames["train"][:: max(1, len(frames["train"]) // 5)][:5]:
        mixed[f] = "all"
    rep["D3_crossfit_control_mixed_all"] = GS.provenance_check(mixed, learned)
    rep["D3_val_from"] = GS.provenance_check({f: "all" for f in frames["val"]}, learned)
    if rep["D3_crossfit"]["violations"] or any(x["n_overlap"] for x in rep["h_test_unused"].values()):
        raise RuntimeError("交差適合か test の外れ")

    def cf_take(key):
        return np.stack([R[k][key][i] for k, i in cf_rows])

    allrow = {p: [R[f"all_{p}"]["row"][f] for f in frames[p]] for p in ("train", "val")}
    mapping = {}
    for p in ("train", "val"):
        mapping[p] = GS.make_mapping(frames[p])
        rep[f"D5_shuffle_{p}"] = GS.mapping_stats(mapping[p])
        rep[f"D5_shuffle_{p}_control_seed43"] = GS.mapping_stats(GS.make_mapping(frames[p], 43))
    # 案 A の g
    A = {}
    for p in ("train", "val"):
        gno = R[f"all_{p}"]["g"][allrow[p]]
        A[f"pred_noCF_{p}"] = write_g(out / f"A/g_pred_noCF_{p}.npz", frames[p], gno)
        gcf = cf_take("g") if p == "train" else gno
        A[f"pred_CF_{p}"] = write_g(out / f"A/g_pred_CF_{p}.npz", frames[p], gcf)
        pos = {f: i for i, f in enumerate(frames[p])}
        A[f"shuffle_{p}"] = write_g(out / f"A/g_shuffle_{p}.npz", frames[p], gno[[pos[mapping[p][f]] for f in frames[p]]])
        A[f"shuffle_CF_{p}"] = write_g(out / f"A/g_shuffle_CF_{p}.npz", frames[p], gcf[[pos[mapping[p][f]] for f in frames[p]]])
    A["made_by"] = {"pred_noCF": "確定の G", "pred_CF_train": "交差適合（H1 の G を H2 の動画に、H2 の G を H1 の動画に）",
                    "pred_CF_val": "確定の G", "shuffle": "pred_noCF をフレームの間で並べ替え", "shuffle_CF": "pred_CF をフレームの間で並べ替え"}
    rep["A"] = A
    # 案 B の m（交差適合の train の地図を写し、ほかは推論の出力を見取りで指す）
    cf_maps = out / "B/pred_CF_train_m.npy"
    src = {k: np.load(R[k]["maps_path"], mmap_mode="r") for k in ("H1_on_H2", "H2_on_H1")}
    mm = np.lib.format.open_memmap(str(cf_maps), mode="w+", dtype=np.uint8, shape=(len(frames["train"]), 5, MAP_H, MAP_W))
    for j, (k, i) in enumerate(cf_rows):
        mm[j] = src[k][i]
    mm.flush()
    Bm = {}
    for arm in ("pred_noCF", "pred_CF", "shuffle", "shuffle_CF"):
        for p in ("train", "val"):
            cf = arm.endswith("CF") and not arm.endswith("noCF") and p == "train"
            if cf:
                view = {"maps": str(cf_maps), "frame_ids": frames["train"]}
            else:
                key = f"all_{p}"
                view = {"maps": R[key]["maps_path"], "frame_ids": R[key]["frame_ids"]}
            view["mapping"] = mapping[p] if arm.startswith("shuffle") else None
            vp = out / f"views/B_{arm}_{p}.json"
            vp.write_text(json.dumps({**view, "arm": arm, "part": p, "task_id": TASK,
                                      "channels": ["tool_L", "tool_R", "tool_B", "hand_L", "hand_R"],
                                      "format": "uint8 round(p × 255)、(フレーム, 5, 270, 480)"}))
            mp = np.load(view["maps"], mmap_mode="r")
            Bm[f"{arm}_{p}"] = {"view": str(vp), "view_sha256": sha(vp), "maps": view["maps"], "maps_sha256": sha(view["maps"]),
                                "frames": int(mp.shape[0]), "range": [int(mp.min()), int(mp.max())]}
    rep["B"] = Bm
    # 案 D の q（正規化、入れ替え、確かめ）
    Dd = {}
    srcs = {"CF_train": [R["H1_on_H2"], R["H2_on_H1"]], "noCF_train": [R["all_train"]], "noCF_val": [R["all_val"]]}
    for name, parts in srcs.items():
        p = name.split("_")[1]
        ann = C.DET_ANN_A / f"instances_{p}.json"
        want = [x["id"] for x in json.loads(ann.read_text())["annotations"]]
        ids = np.concatenate([x["box_ids"] for x in parts])
        order = np.argsort(ids)
        ids = ids[order]
        q_raw = np.concatenate([x["q"] for x in parts])[order]
        r = np.concatenate([x["r"] for x in parts])[order]
        qn, norm = normalize_q(q_raw)
        ent = {"made_by": "交差適合" if name.startswith("CF") else "確定の G", "normalize": norm,
               "boxes_in_annotation_file": len(want)}
        ent["q"] = write_q(out / f"D/q_{name}.npz", ids, qn, r)
        ent["check"] = q_check(ids, qn, want)
        bad = qn.copy()
        bad[0, 0] += 0.25                                     # 陽性対照: 値を一つ変えた写し
        ent["check_control_one_value_changed"] = q_check(ids, bad, want)
        sids, sq, sstats = shuffle_q(ids, qn, ann, 42)
        assert np.array_equal(sids, ids)
        ent["shuffle"] = {**write_q(out / f"D/q_shuffle_{name}.npz", sids, sq), **sstats, "check": q_check(sids, sq, want)}
        ent["shuffle_control_seed43"] = shuffle_q(ids, qn, ann, 43)[2]
        if not ent["check"]["ok"]:
            raise RuntimeError(f"q の確かめの外れ {name}: {ent['check']}")
        Dd[name] = ent
    rep["D"] = Dd
    man = {"task_id": TASK, "unofficial": True, "host": "andrew", "replaces": "T-2026-11-01-grasp-pilot-g の信号と標的",
           "g_runs": {g: {"config": p, "best_ckpt_sha256": json.loads((Path(p).parent / "metrics.json").read_text())["best_ckpt_sha256"]}
                      for g, p in zip(("all", "H1", "H2"), a.g_run)},
           "A_g": A, "B_m": Bm, "D_q": {k: {"q": v["q"], "shuffle": {kk: v["shuffle"][kk] for kk in ("path", "sha256", "boxes")},
                                           "made_by": v["made_by"], "normalize": v["normalize"]} for k, v in Dd.items()},
           "format": {"A": "npz: frame_ids (N,)、x (N, 14)（G_NAMES の順）、names。旗の列は無い",
                      "B": "見取りの json: maps（(N, 5, 270, 480) uint8 の npy）、frame_ids、mapping（入れ替えの腕だけ。フレーム → 値を持ってくるフレーム）",
                      "D": "npz: ann_ids（折り A の術具の注釈の annotation id、昇順）、q (枠, 4) [左, 右, 両手, なし]、行の和 1（超えた行は和で割った）"},
           "shuffle_rule": "g と m: split ごとに一つの固定の並べ替え（stage2pilot.shuffle_signals.make_mapping、seed 42、フレーム名の昇順）。"
                           "q: 同じフレームの枠の間で並べ替え（画像 id の昇順、画像ごとに rng.permutation、seed 42）",
           "assemble_report": str(out / "assemble_report.json"), "code_sha256": sha(Path(__file__))}
    C.write_json(Path(a.manifest), man)
    C.write_json(out / "assemble_report.json", rep)
    print(json.dumps({k: rep[k] for k in ("D3_crossfit", "D3_crossfit_control_mixed_all", "D3_val_from", "h_control_04_mixed")},
                     ensure_ascii=False))
    print(json.dumps({k: {"normalize": v["normalize"], "check": v["check"]["ok"], "ctrl": v["check_control_one_value_changed"]["ok"]}
                      for k, v in Dd.items()}, ensure_ascii=False))


# ---------------------------------------------------------------- flipcheck（§3.3）
def soft_iou(x, y):
    return float(torch.minimum(x, y).sum() / torch.maximum(x, y).sum().clamp_min(1e-9))


def corr(x, y):
    x, y = x.flatten().double(), y.flatten().double()
    x, y = x - x.mean(), y - y.mean()
    d = (x.norm() * y.norm())
    return float((x * y).sum() / d) if d > 0 else None


def flipcheck(a):
    from grasppilot.g_train import G38, collate, to_inputs
    va = json.loads((STORE / "g/ann/g5_val.json").read_text())
    stems = sorted(np.random.default_rng(42).choice([im["stem"] for im in va["images"]], a.frames, replace=False).tolist())
    C.assert_no_test(stems, "flipcheck")
    ds = G38({"images": frame_images("val", stems), "annotations": []}, train=False)
    loader = torch.utils.data.DataLoader(ds, batch_size=1, shuffle=False, num_workers=4, collate_fn=collate)
    model, info = load_model(a.ckpt, a.num_classes)
    names = ["hand_L", "hand_R", "tool_L", "tool_R", "tool_B"]
    acc = {m: {c: {"iou": [], "corr": []} for c in names} for m in ("swap", "noswap")}
    with torch.no_grad():
        for batch in loader:
            arr, meta, _ = batch[0]
            Ps = []
            for flip in (False, True):
                b = [(arr[:, ::-1].copy() if flip else arr, meta, None)]
                inputs, samples = to_inputs(model, b, training=False)
                labels, scores, probs = GS.instances(model, inputs, samples, (270, 480))[0]
                Ps.append(grasp_P(labels, scores, probs, (270, 480)))
            P0, P1 = Ps
            back = P1.flip(-1)                                # 反転し直す
            for mode, perm in (("swap", SWAP0), ("noswap", [0, 1, 2, 3, 4])):
                Q = back[perm]
                for c, n in enumerate(names):
                    if P0[c].max() < 0.05 and Q[c].max() < 0.05:   # 両方ほぼ空のクラスは数えない
                        continue
                    acc[mode][n]["iou"].append(soft_iou(P0[c], Q[c]))
                    acc[mode][n]["corr"].append(corr(P0[c], Q[c]))
    res = {"task_id": TASK, "label": a.label, **info, "num_classes": a.num_classes, "frames": len(stems), "stems": stems,
           "rule": "P_c を 270×480 で作り、反転した画像の P をラベルで入れ替え（swap: 1↔2、3↔4）または入れ替えず（noswap）に反転し直して元の P と比べる。"
                   "soft IoU = Σmin/Σmax、相関 = 画素の Pearson。両方の最大が 0.05 未満のクラスは数えない",
           "per_class": {m: {n: {"frames_counted": len(v["iou"]),
                                  "soft_iou_mean": float(np.mean(v["iou"])) if v["iou"] else None,
                                  "corr_mean": float(np.nanmean([x for x in v["corr"] if x is not None])) if v["iou"] else None}
                              for n, v in d.items()} for m, d in acc.items()}}
    for m in ("swap", "noswap"):
        vals = [v["soft_iou_mean"] for v in res["per_class"][m].values() if v["soft_iou_mean"] is not None]
        res[f"{m}_soft_iou_mean_over_classes"] = float(np.mean(vals)) if vals else None
    C.write_json(a.out, res)
    print(json.dumps({k: res[k] for k in ("label", "swap_soft_iou_mean_over_classes", "noswap_soft_iou_mean_over_classes")}), flush=True)


# ---------------------------------------------------------------- evalval（印を含めた値と除いた値）
def evalval(a):
    from grasppilot import g_train as T
    from grasppilot.g5_train import G5Flip, loss_mask_stems
    va_path = STORE / "g/ann/g5_val.json"
    va = json.loads(va_path.read_text())
    lm = sorted(s for s in loss_mask_stems() if C.video_of(s) in C.fold_a()["val"])
    inc = json.loads(va_path.read_text())
    for s in lm:
        inc["images"].append({"id": len(inc["images"]) + 1, "file_name": f"data/raw/ego/val/{C.video_of(s)}/{s}.jpg", "stem": s,
                              "video": C.video_of(s), "height": 1080, "width": 1920})
    inc_path = Path(a.out).with_name(Path(a.out).stem + "_gt_incl.json")
    inc_path.write_text(json.dumps(inc))
    model, info = load_model(a.ckpt, 5)
    res = {"task_id": TASK, "label": a.label, **info, "loss_mask_val_frames": lm}
    for key, coco, path in (("excluded", va, va_path), ("included", inc, inc_path)):
        loader = torch.utils.data.DataLoader(G5Flip(coco, False), batch_size=2, shuffle=False, num_workers=8,
                                             collate_fn=T.collate)
        r = T.evaluate(model, loader, path)
        res[key] = {"frames": r["n_images"], "segm_mAP": r["segm_mAP"], "per_class_ap": r["per_class_ap"]}
    C.write_json(a.out, res)
    print(json.dumps({k: res[k] for k in ("label", "excluded", "included")}, ensure_ascii=False), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("infer")
    p.add_argument("--ckpt", required=True)
    p.add_argument("--g", choices=("all", "H1", "H2"), required=True)
    p.add_argument("--part", choices=("train", "val"), required=True)
    p.add_argument("--videos", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--limit", type=int, default=0)
    p = sub.add_parser("merge")
    p.add_argument("--parts", nargs="+", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("assemble")
    p.add_argument("--raw", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--manifest", default=str(PROJ / "experiments/analysis/grasp_tower_rebuild/signals_manifest.json"))
    p.add_argument("--g-run", nargs=3, metavar=("ALL", "H1", "H2"), required=True, help="G の 3 本の config.json")
    p = sub.add_parser("flipcheck")
    p.add_argument("--ckpt", required=True, help="重みのファイル、または coco（学習前）")
    p.add_argument("--num-classes", type=int, default=5)
    p.add_argument("--label", required=True)
    p.add_argument("--frames", type=int, default=40)
    p.add_argument("--out", required=True)
    p = sub.add_parser("evalval")
    p.add_argument("--ckpt", required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--out", required=True)
    a = ap.parse_args()
    {"infer": infer, "merge": merge, "assemble": assemble, "flipcheck": flipcheck, "evalval": evalval}[a.cmd](a)


if __name__ == "__main__":
    main()

"""Task C 殺し実験（カード #9。T-2026-11-09-grasp-roitoken-transition-pilot）。本体の .venv。時間ヘッドを通さない。

線形の層（共通の処方）: 入力を train の平均と標準偏差で標準化、Linear(D → 9)、クラスの重みつき交差エントロピー（重みは
dp_train.class_weights と同じ規則: train の出現数の逆数を平均 1 に正規化）、AdamW（学習率 1e-3、重み減衰 1e-4）、batch 512、
100 epoch、seed 42、最後の状態で val を測る。val の各フレームの argmax を動画ごとの列にして PhaseEvaluator（macro Jaccard・
frame accuracy・クラス別）。dressing を除く 6 工程の平均は val に現れる 7 工程から dressing を除いた 6 工程の Jaccard の平均（四本目と同じ）。

案 3（SPEC Task C-1）: 行 = 把持の注釈のある行（train 9,356 相当・val 1,514 相当、b4 の has_gt）。
    base = P の全体の特徴（キャッシュ 2048）、plus = base ＋ 正解の把持の枠の ROI の平均（layer4、5 × 2048、無い枠は 0）＋ 有無 5。
    殺す条件: plus − base が accuracy と Jaccard の両方で 0.001 未満（m = 0.2 pt の仮の m/2）。
    殺さなければ G の予測の枠（train は pred_CF、val は確定）で同じ行で同じ計算。
案 5（SPEC Task C-2）: 遷移の事象（G の予測、val は確定・train は pred_CF）を、窓の (b) の前の時点（同じ区間の直前のフレーム）との比べで作る:
    出現 5・消失 5（クラスごと）、持ち替え（器具のあるクラスが消え別の器具のクラスが現れる）、両手の開始・終了（tool_B の出現・消失）。
    事象のあるフレームの率を、val の工程の境界（隣り合うフレームのラベルが変わる所）の前後 ±L 秒の中と外で比べる（L ∈ {8, 32}）。
    null: 動画ごとに工程の区間の並びを並べ替えて（区間の長さは保つ）境界を置き直す 2,000 回（seed 42）。区間 = null の比の 2.5〜97.5%。
    線形の層: base = P の全体の特徴 ＋ 時刻 t の把持の特徴（(b) の k=1 の 39 次元）、plus = base ＋ 窓の遷移の特徴（(b) の窓 k の全時点と印）。行は全行。
    殺す条件: 観測の比が null の区間の中にあり（1 から区別できない）、かつ plus − base が両方で 0.001 未満。
陽性対照: base ＋ 正解の工程の one-hot の線形の層で差が大きく正。

    .venv/bin/python c_kill.py --box-dir <S>/b4 --tok-dir <S>/tok --seq-dir <S>/seq --out <S>/c/c_kill.json [--pred-c3]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from stage2pilot import common as C  # noqa: E402

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402

FIT = {"lr": 1e-3, "weight_decay": 1e-4, "batch": 512, "epochs": 100, "seed": 42}
KILL = 0.001
TOOLS, TB = [0, 1, 2], 2


def labels_frames(part):
    split = C.fold_a()
    seqs = C.phase_sequences(split[part])
    frames = [f for _, fs, _ in seqs for f in fs]
    y = np.concatenate([lab for _, _, lab in seqs])
    return frames, y


def class_weights(y, n):
    counts = np.bincount(y, minlength=n)
    w = np.divide(1.0, counts, out=np.zeros(len(counts)), where=counts > 0)
    return w / w[w > 0].mean()


def metrics(pred, y, frames, names):
    ev = PhaseEvaluator(num_classes=len(names), class_names=names)
    vids = np.array([C.video_of(f) for f in frames])
    per_video = {}
    for v in sorted(set(vids)):
        sel = vids == v
        ev.update(pred[sel], y[sel], video_id=v)
        one = PhaseEvaluator(num_classes=len(names), class_names=names)
        one.update(pred[sel], y[sel], video_id=v)
        r1 = one.compute()
        per_video[v] = {"phase_jaccard": r1["phase_jaccard"], "phase_accuracy": r1["phase_accuracy"]}
    r = ev.compute()
    present = [names[c] for c in sorted(set(y.tolist()))]
    six = [r["phase_per_class_jaccard"][n] for n in present if n != "dressing"]
    return {"phase_jaccard": r["phase_jaccard"], "phase_accuracy": r["phase_accuracy"],
            "six_phase_mean": float(np.mean(six)), "six_phases": [n for n in present if n != "dressing"],
            "per_class_jaccard": r["phase_per_class_jaccard"], "per_video": per_video, "n_frames": int(len(y))}


def fit_eval(xtr, ytr, xva, yva, fva, names):
    torch.manual_seed(FIT["seed"])
    rng = np.random.default_rng(FIT["seed"])
    mu, sd = xtr.mean(0), xtr.std(0)
    sd[sd < 1e-6] = 1.0
    xt = torch.from_numpy(((xtr - mu) / sd).astype(np.float32)).cuda()
    xv = torch.from_numpy(((xva - mu) / sd).astype(np.float32)).cuda()
    yt = torch.from_numpy(ytr).cuda()
    lin = nn.Linear(xt.shape[1], len(names)).cuda()
    ce = nn.CrossEntropyLoss(weight=torch.tensor(class_weights(ytr, len(names)), dtype=torch.float32, device="cuda"))
    opt = torch.optim.AdamW(lin.parameters(), lr=FIT["lr"], weight_decay=FIT["weight_decay"])
    for _ in range(FIT["epochs"]):
        order = rng.permutation(len(yt))
        for s in range(0, len(order), FIT["batch"]):
            b = torch.from_numpy(order[s:s + FIT["batch"]]).cuda()
            loss = ce(lin(xt[b]), yt[b])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
    with torch.no_grad():
        pred = lin(xv).argmax(1).cpu().numpy()
    return metrics(pred, yva, fva, names)


def diff(p, b):
    return {k: p[k] - b[k] for k in ("phase_jaccard", "phase_accuracy", "six_phase_mean")}


def killed(d):
    return d["phase_jaccard"] < KILL and d["phase_accuracy"] < KILL


def case3(a, names, feats, src):
    out = {}
    data = {}
    for part in ("train", "val"):
        frames, y = labels_frames(part)
        has = np.load(Path(a.box_dir) / f"has_gt_{part}.npy")
        bf = [str(f) for f in np.load(Path(a.box_dir) / f"frame_ids_{part}.npy")]
        assert bf == frames
        tok_src = {"gt": "gt", "pred": "pred"}[src]
        tok = np.load(Path(a.tok_dir) / f"tok_{tok_src}_layer4_{part}.npy").astype(np.float32)
        pres = np.load(Path(a.box_dir) / f"boxes_{tok_src}_{part}.npz")["present"].astype(np.float32)
        g = np.stack([feats[f] for f in frames])
        sel = has
        data[part] = (g[sel], np.concatenate([g, tok.reshape(len(g), -1), pres], 1)[sel], y[sel],
                      [f for f, s in zip(frames, sel) if s])
    (btr, ptr, ytr, _), (bva, pva, yva, fva) = data["train"], data["val"]
    base = fit_eval(btr, ytr, bva, yva, fva, names)
    plus = fit_eval(ptr, ytr, pva, yva, fva, names)
    d = diff(plus, base)
    out = {"rows": {"train": int(len(ytr)), "val": int(len(yva))}, "dims": {"base": btr.shape[1], "plus": ptr.shape[1]},
           "base": base, "plus": plus, "diff": d, "kill": killed(d)}
    return out


def events(maps_path, frames, starts):
    """各フレームの事象（直前のフレームとの比べ。区間の始めは事象なし）。"""
    m = np.load(maps_path, mmap_mode="r")
    pres = np.zeros((len(frames), 5), bool)
    for s in range(0, len(frames), 512):
        pres[s:s + 512] = (np.asarray(m[s:s + 512]) >= 128).reshape(-1, 5, 270 * 480).any(-1)
    prev = np.vstack([pres[:1], pres[:-1]])
    appear = pres & ~prev
    disappear = ~pres & prev
    switch = disappear[:, TOOLS].any(1) & appear[:, TOOLS].any(1)
    ev = {"appear": appear.any(1), "disappear": disappear.any(1), "switch": switch,
          "two_hand_start": appear[:, TB], "two_hand_end": disappear[:, TB]}
    for k in ev:
        ev[k] = ev[k] & ~starts
    ev["any"] = np.any(np.stack(list(ev.values())), 0)
    return ev


def near_boundary(frames, y, L, seg_order=None):
    """工程の境界の前後 ±L 秒の中のフレームの印（同じクリップの中で時刻を比べる）。"""
    t = np.array([int(str(f).split("_")[2]) * 2 for f in frames])
    clip = np.array(["_".join(str(f).split("_")[:2]) for f in frames])
    lab = y if seg_order is None else seg_order
    b = np.where((lab[1:] != lab[:-1]) & (clip[1:] == clip[:-1]))[0]
    near = np.zeros(len(frames), bool)
    for i in b:
        tb = (t[i] + t[i + 1]) / 2
        near |= (clip == clip[i]) & (np.abs(t - tb) <= L)
    return near


def permuted_labels(y, frames, rng):
    """動画ごとに工程の区間（同じラベルの連続）の並びを並べ替え、区間の長さを保ってラベルを置き直す。"""
    vids = np.array([C.video_of(f) for f in frames])
    out = y.copy()
    for v in sorted(set(vids)):
        idx = np.where(vids == v)[0]
        yy = y[idx]
        cut = np.r_[0, np.where(yy[1:] != yy[:-1])[0] + 1, len(yy)]
        segs = [yy[cut[i]:cut[i + 1]] for i in range(len(cut) - 1)]
        order = rng.permutation(len(segs))
        out[idx] = np.concatenate([segs[i] for i in order])
    return out


def case5(a, names, feats):
    rec6 = json.loads((Path(a.seq_dir) / "b6_record.json").read_text())
    rec4 = json.loads((Path(a.box_dir) / "b4_record.json").read_text())
    frames, y = labels_frames("val")
    sys.path.insert(0, str(Path(__file__).parent))
    import b6_windows as B6
    starts, _ = B6.segments(frames)
    ev = events(rec4["parts"]["val"]["pred_source"]["maps"], frames, starts)
    res = {"events_val": {k: int(v.sum()) for k, v in ev.items()}, "rate": {}}
    rng = np.random.default_rng(42)
    perms = [permuted_labels(y, frames, rng) for _ in range(2000)]
    for L in (8, 32):
        near = near_boundary(frames, y, L)
        def ratio(nr):
            return float(ev["any"][nr].mean() / max(ev["any"][~nr].mean(), 1e-12))
        obs = ratio(near)
        null = np.array([ratio(near_boundary(frames, y, L, p)) for p in perms])
        lo, hi = np.percentile(null, [2.5, 97.5])
        res["rate"][f"L{L}"] = {"near_frames": int(near.sum()), "other_frames": int((~near).sum()),
                                "rate_near": float(ev["any"][near].mean()), "rate_other": float(ev["any"][~near].mean()),
                                "ratio": obs, "null_interval_95": [float(lo), float(hi)], "null_median": float(np.median(null)),
                                "ratio_inside_null_interval": bool(lo <= obs <= hi),
                                "null_interval_contains_1": bool(lo <= 1 <= hi),
                                "perm_p_two_sided": float((np.abs(np.log(null)) >= abs(np.log(obs))).mean())}
    lin = {}
    for L, k in ((8, 4), (32, 16)):
        d = {}
        for part in ("train", "val"):
            fr, yy = labels_frames(part)
            g = np.stack([feats[f] for f in fr])
            s1 = np.load(Path(a.seq_dir) / f"seq_S1_k1_{part}.npz")
            sw = np.load(Path(a.seq_dir) / f"seq_SW_k{k}_{part}.npz")
            assert (sw["idx"][:, 0] == np.arange(len(fr))).all()
            t_feat = s1["b"].astype(np.float32).reshape(len(fr), -1)
            w_feat = np.concatenate([sw["b"].astype(np.float32).reshape(len(fr), -1), sw["flag"].astype(np.float32)], 1)
            base = np.concatenate([g, t_feat], 1)
            d[part] = (base, np.concatenate([base, w_feat], 1), yy, fr)
        (btr, ptr, ytr, _), (bva, pva, yva, fva) = d["train"], d["val"]
        b = fit_eval(btr, ytr, bva, yva, fva, names)
        p = fit_eval(ptr, ytr, pva, yva, fva, names)
        dd = diff(p, b)
        lin[f"L{L}"] = {"dims": {"base": btr.shape[1], "plus": ptr.shape[1]}, "base": b, "plus": p, "diff": dd,
                        "diff_below_0.1pt": killed(dd),
                        "kill": killed(dd) and res["rate"][f"L{L}"]["ratio_inside_null_interval"]}
    res["linear"] = lin
    res["kill"] = all(v["kill"] for v in lin.values())
    res["kill_any_L"] = any(v["kill"] for v in lin.values())
    res["window_record"] = {k: rec6["parts"]["val"][k] for k in ("min_interval_seconds", "boundaries")}
    return res


def positive_control(names, feats, has_gt_dir):
    data = {}
    for part in ("train", "val"):
        frames, y = labels_frames(part)
        g = np.stack([feats[f] for f in frames])
        oh = np.eye(len(names), dtype=np.float32)[y]
        data[part] = (g, np.concatenate([g, oh], 1), y, frames)
    (btr, ptr, ytr, _), (bva, pva, yva, fva) = data["train"], data["val"]
    b = fit_eval(btr, ytr, bva, yva, fva, names)
    p = fit_eval(ptr, ytr, pva, yva, fva, names)
    return {"base": {k: b[k] for k in ("phase_jaccard", "phase_accuracy", "six_phase_mean")},
            "plus_gt_onehot": {k: p[k] for k in ("phase_jaccard", "phase_accuracy", "six_phase_mean")}, "diff": diff(p, b)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-dir", required=True)
    ap.add_argument("--tok-dir", required=True)
    ap.add_argument("--seq-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    import stage1_ptower as base
    base.deterministic(42)
    names = C.phase_names()
    feats = C.load_features()
    for part in ("train", "val"):
        C.assert_no_test(labels_frames(part)[0], f"c_kill {part}")
    out = {"task_id": "T-2026-11-09-grasp-roitoken-transition-pilot", "fit": FIT, "kill_threshold": KILL,
           "m_provisional": 0.002, "videos": {p: C.assert_no_test(labels_frames(p)[0], "c") for p in ("train", "val")}}
    out["positive_control"] = positive_control(names, feats, a.box_dir)
    print("positive", json.dumps(out["positive_control"]["diff"]), flush=True)
    out["case3_gt"] = case3(a, names, feats, "gt")
    print("case3 gt", json.dumps(out["case3_gt"]["diff"]), out["case3_gt"]["kill"], flush=True)
    if not out["case3_gt"]["kill"]:
        out["case3_pred"] = case3(a, names, feats, "pred")
        print("case3 pred", json.dumps(out["case3_pred"]["diff"]), out["case3_pred"]["kill"], flush=True)
    out["case5"] = case5(a, names, feats)
    print("case5", json.dumps({k: v for k, v in out["case5"].items() if k in ("rate", "kill", "kill_any_L")}), flush=True)
    for L, v in out["case5"]["linear"].items():
        print("case5 linear", L, json.dumps(v["diff"]), v["kill"], flush=True)
    C.write_json(a.out, out)


if __name__ == "__main__":
    main()

"""Task C: 三つの型が SPEC §4 の定義どおりかを確かめる（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、完了判定 c）。読むだけ。書くのは --out だけ。

    CUDA_VISIBLE_DEVICES="" .venv/bin/python experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/c_types.py --out <T>/c/c_types.json

型 × 腕 × 設定（N 10・30 × L 1・2）ごとに、dp_train と同じ経路（Signals・DPReceiver、seed 42 の初期化）で界面を作り、float64 で r_t を測る。
  1. フレームごとの問い合わせと鍵の数（IRN: 側の問い合わせ 2・術具の鍵・統合の鍵、HiCE: 問い合わせ 1・側の鍵、HTT: x_t の次元）。HiCE の A0・D は鍵 0
  2. 入力の無いフレーム（術具のトークンも手のトークンも無い）で r_t = 0（完全に 0）。対照: A0 の型に DGH の入力を入れると r_t が零でない
  3. 送り手の中身を零にした入力（在否の列 0 は残し、列 1..26 を 0）では、g_t を別のフレームの特徴に替えても r_t が変わらない（差 ≤ TOL）。
     対照: 注意の値に e_s を足した写し（IRN は統合の値 z_s、HiCE は側の値 v_s）では変わる（中身を零にしても鍵が残る腕で数える。
     HiCE の A0・D・DG は中身を零にすると鍵が無くなり、写しでも r_t = 0）
  4. HiCE: 持たれていない術具（持ち手 3 列とも 0）の中身を変えても r_t が変わらない（完全に 0）。対照: 持ち手の重みに 1 を足して
     持たれていない術具も鍵に入れた写しでは変わる
  5. 型と設定ごとの界面のパラメータ数
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from stage2pilot import common as C  # noqa: E402
from stage2pilot import dp_model as M  # noqa: E402
from stage2pilot import dp_train as DT  # noqa: E402

TASK = "T-2026-11-21-grasp-hand-irn-hice-htt-pilot"
GRAPH_STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph")
TYPES = ("IRN", "HiCE", "HTT")
ARMS = ("empty",) + DT.GR_ARMS
SETTINGS = {"s1": (10, 1), "s2": (10, 2), "s3": (30, 1), "s4": (30, 2)}
TOL = 1e-9                     # float64 で g_t を替えたときに「変わらない」とする差の上限（重みの和が 1 からずれる丸めの分）


def irn_values_with_side(iface, x, s):
    """対照: IRN の統合の注意の値 z_s に e_s を足した写し。"""
    tp, hp, tf, hf = iface.parts(s)
    ht = iface.enc_t(tf) * tp[..., None].to(x.dtype)
    q = iface.side[None] + iface.enc_h(hf) * hp[..., None].to(x.dtype)
    z = torch.zeros_like(q)
    for blk in iface.inter:
        a = blk(q, ht, ht, tp)
        q, z = q + a, z + a
    zmask = tp.any(1)[:, None].expand(-1, 2)
    zv = z + iface.side[None]
    return iface.agg(iface.g(x)[:, None], zv, zv, zmask)[:, 0]


def hice_values_with_side(iface, x, s):
    """対照: HiCE の側の値 v_s に e_s を足した写し。"""
    value, kp = iface.keys(s)
    key = iface.side[None] + value
    value = value + iface.side[None]
    u = iface.g(x)[:, None]
    r = torch.zeros_like(u)
    for blk in iface.blocks:
        a = blk(u, key, value, kp)
        u, r = u + a, r + a
    return r[:, 0]


def hice_all_tools(iface, x, s):
    """対照: 持ち手の重みに 1 を足し、持たれていない術具も ω（鍵）に入れた写し。"""
    tp, hp, tf, hf = iface.parts(s)
    hold = tf[..., 20:23] * tp[..., None].to(s.dtype)
    w = torch.stack([hold[..., 0] + hold[..., 2], hold[..., 1] + hold[..., 2]], -1) + tp[..., None].to(s.dtype)
    omega = torch.einsum("tns,tnk->tsk", w, iface.m(tf[..., :20]) * tp[..., None].to(s.dtype))
    value = iface.enc_h(hf) * hp[..., None].to(s.dtype) + iface.w_omega(omega)
    kp = hp | (w.sum(1) > 0)
    key = iface.side[None] + value
    u = iface.g(x)[:, None]
    r = torch.zeros_like(u)
    for blk in iface.blocks:
        a = blk(u, key, value, kp)
        u, r = u + a, r + a
    return r[:, 0]


def stats(v):
    v = v.double()
    return {"mean": float(v.mean()), "min": int(v.min()), "max": int(v.max())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    torch.set_grad_enabled(False)
    head = C.load_ptower_head(device="cpu")
    feats = C.load_features()
    fold = C.fold_a()
    frames = [f for _, fr, _ in C.phase_sequences(fold["val"]) for f in fr]
    g = torch.from_numpy(np.stack([feats[f] for f in frames])).double()
    g_other = torch.roll(g, shifts=len(g) // 2, dims=0)            # 別のフレームの特徴
    out = {"task_id": TASK, "unofficial": True, "part": "val", "frames": len(frames), "tol": TOL, "rows": [], "params": {}}
    for t in TYPES:
        for sname, (n, L) in SETTINGS.items():
            DT.GR.update(dir=str(GRAPH_STORE), N=n, L=L)
            for arm in ARMS:
                sig = DT.Signals(t, arm, "val", "uq")
                s = sig.for_frames(frames)[0].double()
                torch.manual_seed(42)
                iface = M.DPReceiver(head, DT.TYPES[t][0], sig.dim, **sig.model_kwargs()).iface.double()
                iface.eval()
                out["params"].setdefault(t, {})[sname] = int(sum(p.numel() for p in iface.parameters()))
                r = iface.readout(g, s)
                none = ~((s[..., 0] > 0.5).any(1))
                row = {"type": t, "setting": sname, "N": n, "L": L, "arm": arm,
                       "counts": {k: stats(v) for k, v in iface.counts(s).items()},
                       "finite": bool(torch.isfinite(r).all()), "r_abs_max": float(r.abs().max()),
                       "frames_no_input": int(none.sum()),
                       "r_abs_max_no_input": float(r[none].abs().max()) if none.any() else None}
                if arm == "empty":
                    dgh = DT.Signals(t, "DGH", "val", "uq").for_frames(frames)[0].double()
                    row["control_A0_given_DGH_r_abs_max"] = float(iface.readout(g, dgh).abs().max())
                s0 = s.clone()
                s0[..., 1:] = 0.0
                row["zero_content_g_change"] = float((iface.readout(g, s0) - iface.readout(g_other, s0)).abs().max())
                k0 = iface.counts(s0)
                row["zero_content_keys_max"] = int(k0["keys"].max()) if "keys" in k0 else None
                if t == "IRN":
                    row["control_values_with_side_g_change"] = float(
                        (irn_values_with_side(iface, g, s0) - irn_values_with_side(iface, g_other, s0)).abs().max())
                if t == "HiCE":
                    row["control_values_with_side_g_change"] = float(
                        (hice_values_with_side(iface, g, s0) - hice_values_with_side(iface, g_other, s0)).abs().max())
                    tp = s[:, :n, 0] > 0.5
                    unheld = tp & (s[:, :n, 21:24].abs().sum(-1) == 0)
                    s1 = s.clone()
                    gen = torch.Generator().manual_seed(7)
                    noise = torch.randn(s1[:, :n, 1:21].shape, generator=gen, dtype=s1.dtype)
                    s1[:, :n, 1:21] = torch.where(unheld[..., None], s1[:, :n, 1:21] + noise, s1[:, :n, 1:21])
                    row["unheld_tools"] = int(unheld.sum())
                    row["unheld_change"] = float((iface.readout(g, s1) - r).abs().max())
                    row["control_all_tools_unheld_change"] = float((hice_all_tools(iface, g, s1) - hice_all_tools(iface, g, s)).abs().max())
                out["rows"].append(row)
            print(t, sname, out["params"][t][sname], flush=True)
    rows = out["rows"]
    hice_nokey = [r for r in rows if r["type"] == "HiCE" and r["arm"] in ("empty", "D")]
    out["summary"] = {
        "rows": len(rows), "all_finite": all(r["finite"] for r in rows),
        "no_input_zero": all(r["r_abs_max_no_input"] in (None, 0.0) for r in rows),
        "no_input_frames": sorted({(r["arm"], r["frames_no_input"]) for r in rows}),
        "A0_zero": all(r["r_abs_max"] == 0.0 for r in rows if r["arm"] == "empty"),
        "control_A0_given_DGH_min": min(r["control_A0_given_DGH_r_abs_max"] for r in rows if r["arm"] == "empty"),
        "hice_A0_D_keys_max": max(r["counts"]["keys"]["max"] for r in hice_nokey),
        "hice_D_r_abs_max": max(r["r_abs_max"] for r in hice_nokey),
        "zero_content_g_change_max": max(r["zero_content_g_change"] for r in rows),
        "zero_content_ok": all(r["zero_content_g_change"] <= TOL for r in rows),
        "control_values_with_side_min_over_arms_with_input": min(
            r["control_values_with_side_g_change"] for r in rows if "control_values_with_side_g_change" in r
            and r["zero_content_keys_max"]),
        "control_values_with_side_rows": sum(1 for r in rows if "control_values_with_side_g_change" in r and r["zero_content_keys_max"]),
        "hice_unheld_change_max": max(r["unheld_change"] for r in rows if r["type"] == "HiCE"),
        "hice_control_all_tools_min_over_arms_with_unheld": min(
            r["control_all_tools_unheld_change"] for r in rows if r["type"] == "HiCE" and r["unheld_tools"] > 0),
        "params": out["params"]}
    C.write_json(a.out, out)
    print(json.dumps(out["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()

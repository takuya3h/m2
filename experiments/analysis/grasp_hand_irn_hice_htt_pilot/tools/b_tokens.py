"""Task B: トークンの中身を前回のグラフの節と突き合わせる（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、SPEC §3・§9 b・i）。

    .venv/bin/python experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/b_tokens.py --out <T>/b/b_tokens.json [--types GR IRN HiCE HTT]

読むだけ。書くのは --out だけ。本契約のトークンは前回の組み立ての出力 $O/graph/<腕>_<part>.npz（x (F, 32, 27)）をそのまま読む
（SPEC §3「前回の組み立ての出力を読んで使ってよい」）。
  1. 腕 × 設定（N 10・30）× part × 型ごとに、dp_train の Signals が型に渡す配列が、npz の行 [0, N) と行 30・31 にビットまで一致するか。
     空の腕（A0）は同じ形の全部 0。対照: 1 フレームの術具のトークンを 1e-6 ずらした写しで不一致を検出する
  2. 正解の腕の持ち手と注釈の把持の一致（前回の ghg_graph.grasp_agreement に、DGH-GT の配列の持ち手の列を渡す）。
     前回の報告 train 20,433/21,021・val 3,610/3,807 と同じか。対照: 持ち手の左右を入れ替えた写しで一致が下がる
  3. 腕ごとの術具のトークン・持ち手（非零）・手のトークンの在否が SPEC §5.1 の表と一致するか。DGH-U の持ち手が 3 列とも同じか。
     対照: D に DH の配列（手のトークンが在る）を置いた写しで表との外れを出す
  4. 各段で通した動画の集合と {04, 05, 07} の共通。対照: train のフレームに 04 のフレームを 1 つ混ぜる
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from grasppilot import ghg_graph as G  # noqa: E402
from stage2pilot import common as C  # noqa: E402
from stage2pilot import dp_train as DT  # noqa: E402

TASK = "T-2026-11-21-grasp-hand-irn-hice-htt-pilot"
GRAPH_STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph")
ARMS = ("empty",) + G.ARMS
ROWS, NT = G.ROWS, G.NT
# SPEC §5.1: 術具のトークン・持ち手の特徴（非零）・手のトークン
TABLE = {"empty": (False, False, False), "D": (True, False, False), "DG": (True, True, False), "DH": (True, False, True),
         "DGH": (True, True, True), "DGH-U": (True, True, True), "DGH-noCF": (True, True, True), "DGH-GT": (True, True, True)}
PRIOR_AGREE = {"train": (20433, 21021), "val": (3610, 3807)}     # 前回の RESULT §2 の f


def npz(arm, part):
    with np.load(GRAPH_STORE / "graph" / f"{'D' if arm == 'empty' else arm}_{part}.npz") as d:
        return [str(f) for f in d["frame_ids"]], d["x"].astype(np.float32)


def expected(arm, part, n):
    frames, x = npz(arm, part)
    e = np.concatenate([x[:, :n], x[:, ROWS:ROWS + 2]], 1)
    return frames, (np.zeros_like(e) if arm == "empty" else e)


def signals_array(type_name, arm, part, n, frames):
    DT.GR.update(dir=str(GRAPH_STORE), N=n, L=1)
    sig = DT.Signals(type_name, arm, part, "uq")
    s, m = sig.for_frames(frames)
    assert m is None
    return s.numpy(), sig


def flags(x, n):
    t = x[:, :n]
    hold = t[..., 6 + NT:9 + NT]
    return {"tools": bool((t[..., 0] > 0.5).any()), "holder": bool(np.abs(hold).sum() > 0),
            "hands": bool((x[:, n:n + 2, 0] > 0.5).any()),
            "holder_uniform": bool(np.array_equal(hold[..., 0], hold[..., 1]) and np.array_equal(hold[..., 0], hold[..., 2]))}


def table_check(fl):
    bad = [(arm, "presence") for arm, want in TABLE.items() if (fl[arm]["tools"], fl[arm]["holder"], fl[arm]["hands"]) != want]
    bad += [("DGH-U", "holder_not_uniform")] if not fl["DGH-U"]["holder_uniform"] else []
    return {"arms": len(fl), "violations": len(bad), "examples": bad[:5]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--types", nargs="+", default=["GR"])
    ap.add_argument("--skip-agree-train", action="store_true", help="train の一致の数え直しを省く（試走だけ）")
    a = ap.parse_args()
    out = {"task_id": TASK, "unofficial": True, "types": a.types, "content": [], "tables": {}, "agreement": {}, "videos": {}}
    fold = C.fold_a()
    for part in ("train", "val"):
        frames_seq = [f for _, fr, _ in C.phase_sequences(fold[part]) for f in fr]
        for n in (10, 30):
            fl = {}
            for arm in ARMS:
                frames, e = expected(arm, part, n)
                assert frames == frames_seq, (arm, part)        # 前回の組み立ては工程の経路の全フレームの並び
                for t in a.types:
                    s, sig = signals_array(t, arm, part, n, frames)
                    shifted = s.copy()
                    r = int(np.argmax((e[:, :n, 0] > 0.5).any(1))) if arm != "empty" else 0
                    shifted[r, 0, 1 + NT] += 1e-6
                    out["content"].append({"type": t, "arm": arm, "part": part, "N": n, "shape": list(s.shape),
                                           "equal": bool(np.array_equal(s, e)), "max_abs_diff": float(np.abs(s - e).max()),
                                           "control_shift_1e-6_equal": bool(np.array_equal(shifted, e)),
                                           "files": [f["sha256"][:8] for f in sig.files()]})
                fl[arm] = flags(e, n)
            bad = dict(fl)
            bad["D"] = flags(expected("DH", part, n)[1], n)
            out["tables"][f"{part}_N{n}"] = {"flags": fl, "check": table_check(fl), "control_D_with_hands": table_check(bad)}
        out["videos"][part] = G.videos_check(sorted({C.video_of(f) for f in frames_seq}))
        if part == "train" and a.skip_agree_train:
            continue
        gt = G.GT(part)
        _, xg = npz("DGH-GT", part)
        hold = {f: xg[j, :ROWS, 6 + NT:9 + NT] for j, f in enumerate(frames_seq)}
        ag = G.grasp_agreement(gt, frames_seq, hold)
        sw = G.grasp_agreement(gt, frames_seq, hold, swap=True)
        out["agreement"][part] = {"agree": ag, "control_swapLR": sw, "prior": list(PRIOR_AGREE[part]),
                                  "equals_prior": (ag["agree"], ag["boxes"]) == PRIOR_AGREE[part]}
        print(part, json.dumps(out["agreement"][part]), flush=True)
    tr = [f for _, fr, _ in C.phase_sequences(fold["train"]) for f in fr]
    out["videos"]["control_04_mixed"] = G.videos_check(sorted({C.video_of(f) for f in tr + ["04_1_0001"]}))
    c = out["content"]
    out["summary"] = {"content_n": len(c), "content_equal": sum(x["equal"] for x in c),
                      "content_control_detected": sum(not x["control_shift_1e-6_equal"] for x in c),
                      "table_violations": sum(v["check"]["violations"] for v in out["tables"].values()),
                      "table_control_violations": sum(v["control_D_with_hands"]["violations"] for v in out["tables"].values()),
                      "agreement": {p: (v["agree"]["agree"], v["agree"]["boxes"], v["equals_prior"],
                                        v["control_swapLR"]["agree"]) for p, v in out["agreement"].items()},
                      "test_overlap": {p: v["n_overlap"] for p, v in out["videos"].items()}}
    C.write_json(a.out, out)
    print(json.dumps(out["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()

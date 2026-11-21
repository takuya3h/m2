"""Task C: noCF・CF・入れ替えのグラフの材料を作り、検査する（非公式 T-2026-11-21-grasp-hand-graph-t2p-match、SPEC §4・§5.1）。本体の .venv。

    .venv/bin/python experiments/analysis/grasp_hand_graph_t2p/tools/c_graphs.py --out-dir <T>/graph --report <T>/c/graphs_report.json

前回の契約の信号（$O/signals の検出の配列と G3・H4 の推論。読むだけ）から、前回の道具 ghg_graph の部品（tool_rows・hand_rows・
holder・pred_hands）で、腕ごとの x (F, 32, 27) を noCF（train も確定の塔）と CF（train は動画を学んでいない半分の塔）の両方で組む。
グラフの定義（前回の SPEC §4 と利用者の読み 3 点）は変えない。

- 組み直した CF の 5 腕と DGH-noCF が前回の $O/graph の配列とビットまで一致することを確かめ、前回のファイルを指す記号のリンクを置く
  （D-CF・DG-CF・DH-CF・DGH-CF・DGH-U-CF・DGH-noCF・DGH-GT と、空の腕の形と陰性対照に使う D・DGH）
- 新しく書くのは D-noCF・DG-noCF・DH-noCF・DGH-U-noCF と、入れ替えの 5 腕 X-S（noCF のグラフの行をフレームごとに丸ごと並べ替えたもの）
- 入れ替え（SPEC §4.2）: T→P の対応表 mapping_{train,val}.json（seed 42、frame f gets the value of mapping[f]）のキーの集合がグラフのフレームの
  集合と同じなら、それを 5 腕すべてに使う。違えば止める（同じ規則で作り直す道は道具に入れていない）
- 検査: 表（術具・持ち手・手・辺の在否、DGH-U の持ち手が 3 列とも同じ、辺 = 持ち手）、出どころ（noCF の腕の術具の行 = DGH-noCF の術具の行、
  CF の腕 = DGH-CF、持ち手 = DG・DGH の同じ信号、手の行 = DH・DGH の同じ信号、S = noCF を並べ替えたもの）、入れ替えの値の集合、
  不動点と同じ動画の割合、test の動画。対照: 表と違う腕、noCF の腕に CF の信号を混ぜた写し、恒等の並べ替え、04 を混ぜたフレームの集合
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from grasppilot import ghg_graph as G  # noqa: E402
from stage2pilot import common as C  # noqa: E402
from stage2pilot.shuffle_signals import mapping_stats  # noqa: E402

TASK = "T-2026-11-21-grasp-hand-graph-t2p-match"
O = G.O
MAP = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle")
CORES = ("D", "DG", "DH", "DGH", "DGH-U")
ROWS, NT = G.ROWS, G.NT
# SPEC §5.1 の表: 術具の節・持ち手・手の節・辺
TABLE = {"D": (True, False, False, False), "DG": (True, True, False, False), "DH": (True, False, True, False),
         "DGH": (True, True, True, True), "DGH-U": (True, True, True, True)}
TOOL_COLS = slice(0, 1 + NT + 1 + 4)                      # 有無・クラス・得点・枠
HOLD_COLS = slice(6 + NT, 9 + NT)
PREV = {"D-CF": "D", "DG-CF": "DG", "DH-CF": "DH", "DGH-CF": "DGH", "DGH-U-CF": "DGH-U", "DGH-noCF": "DGH-noCF",
        "DGH-GT": "DGH-GT", "D": "D", "DGH": "DGH"}


def build(part, frames, R, D):
    """part の全フレームについて、5 腕 × {cf, nocf} の配列。ghg_graph.cmd_assemble の予測の部分と同じ手順。"""
    F = len(frames)
    X = {(c, k): np.zeros((F, ROWS + 2, 27), np.float32) for c in CORES for k in ("cf", "nocf")}
    src = {"cf": {}, "nocf": {}}
    cnt = collections.Counter()
    for j, f in enumerate(frames):
        v = C.video_of(f)
        if part == "train":
            hcf = G.cf_half(v)
            det = {"cf": D[f"train_cf{hcf}"].get(f), "nocf": D["train_final"].get(f)}
            g3 = {"cf": R[f"G3_{hcf}_train"].get(f), "nocf": R["G3_all_train"].get(f)}
            h4 = {"cf": R[f"H4_{hcf}_train"].get(f), "nocf": R["H4_all_train"].get(f)}
            src["cf"][f] = {"det": f"det_cf{hcf}", "G3": f"G3_{hcf}", "H4": f"H4_{hcf}"}
            src["nocf"][f] = {"det": "det_final", "G3": "G3_all", "H4": "H4_all"}
        else:
            det = {k: D["val_final"].get(f) for k in ("cf", "nocf")}
            g3 = {k: R["G3_all_val"].get(f) for k in ("cf", "nocf")}
            h4 = {k: R["H4_all_val"].get(f) for k in ("cf", "nocf")}
            src["cf"][f] = src["nocf"][f] = {"det": "det_final", "G3": "G3_all", "H4": "H4_all"}
        for k in ("cf", "nocf"):
            if det[k] is None:
                cnt[f"{k}_no_det"] += 1
                continue
            cat, sc, bx = det[k][0][:ROWS], det[k][1][:ROWS], det[k][2][:ROWS]
            hold = G.holder(bx, *g3[k][:3]) if g3[k] is not None else np.zeros((len(cat), 3), np.float32)
            hands = G.pred_hands(h4[k])
            z = np.zeros_like(hold)
            G.tool_rows(X[("D", k)], j, cat, sc, bx, z, z)
            G.tool_rows(X[("DG", k)], j, cat, sc, bx, hold, z)
            G.tool_rows(X[("DH", k)], j, cat, sc, bx, z, z)
            G.hand_rows(X[("DH", k)], j, hands)
            G.tool_rows(X[("DGH", k)], j, cat, sc, bx, hold, hold)
            G.hand_rows(X[("DGH", k)], j, hands)
            u = np.repeat(hold.max(1, keepdims=True), 3, 1)
            G.tool_rows(X[("DGH-U", k)], j, cat, sc, bx, u, u)
            G.hand_rows(X[("DGH-U", k)], j, hands)
    return X, src, cnt


def flags(x):
    return G.arm_flags(x)


def table_check(fl):
    bad = []
    for arm, f in fl.items():
        core = arm.rsplit("-", 1)[0]
        t, g, h, e = TABLE[core]
        if (f["tools"], f["holder"], f["hands"], f["edges"]) != (t, g, h, e):
            bad.append((arm, "presence"))
        if core == "DGH-U" and not f["holder_uniform"]:
            bad.append((arm, "holder_not_uniform"))
        if core in ("DGH", "DGH-U") and not f["edge_equals_holder"]:
            bad.append((arm, "edge_not_holder"))
    return {"arms": len(fl), "violations": len(bad), "examples": bad[:5]}


def provenance(arrs, kind):
    """kind（noCF・CF）の 5 腕の値が同じ信号から来ているか: 術具の行は DGH と、持ち手は DG と DGH、手の行は DH と DGH で同じ。"""
    ref = arrs[f"DGH-{kind}"]
    bad = []
    for c in CORES:
        x = arrs[f"{c}-{kind}"]
        if not np.array_equal(x[:, :ROWS, TOOL_COLS], ref[:, :ROWS, TOOL_COLS]):
            bad.append((c, "tool_rows"))
        if c in ("DG", "DGH") and not np.array_equal(x[:, :ROWS, HOLD_COLS], ref[:, :ROWS, HOLD_COLS]):
            bad.append((c, "holder"))
        if c in ("DH", "DGH", "DGH-U") and not np.array_equal(x[:, ROWS:], ref[:, ROWS:]):
            bad.append((c, "hand_rows"))
        if c == "DGH-U":
            u = np.repeat(ref[:, :ROWS, HOLD_COLS].max(-1, keepdims=True), 3, -1)
            if not np.array_equal(x[:, :ROWS, HOLD_COLS], u):
                bad.append((c, "holder_u"))
    return {"kind": kind, "violations": len(bad), "examples": bad[:5]}


def sorted_digest(x):
    h = hashlib.sha256()
    for r in sorted(r.tobytes() for r in x.reshape(len(x), -1)):
        h.update(r)
    return h.hexdigest()


def shuffle_check(x, y, frames, mapping):
    """y（入れ替え）の行 j = x の行 idx[mapping[f_j]]。値の集合、元の行と同じ値の割合、並べ直すと元と一致するか。"""
    idx = {f: i for i, f in enumerate(frames)}
    rows = np.array([idx[mapping[f]] for f in frames])
    inv = np.empty_like(rows)
    inv[rows] = np.arange(len(rows))
    return {"rows_follow_mapping": bool(np.array_equal(y, x[rows])), "inverse_restores": bool(np.array_equal(y[inv], x)),
            "value_set_equal": sorted_digest(x) == sorted_digest(y),
            "same_value_fraction": float(np.mean(np.all(x.reshape(len(x), -1) == y.reshape(len(y), -1), axis=1)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fold = C.fold_a()
    raw = O / "signals/raw"
    R = {k: G.Raw(raw / k) for k in ("G3_all_train", "G3_all_val", "G3_H1_train", "G3_H2_train",
                                     "H4_all_train", "H4_all_val", "H4_H1_train", "H4_H2_train")}
    D = {k: G.Det(k) for k in G.DET_SRC}
    rep = {"task_id": TASK, "unofficial": True, "host": os.uname().nodename, "code_sha256": C.sha256(Path(__file__)),
           "ghg_graph_sha256": C.sha256(Path(G.__file__)), "parts": {}}
    for part in ("train", "val"):
        frames = [f for v, fr, _ in C.phase_sequences(fold[part]) for f in fr]
        videos = C.assert_no_test(frames, f"c_graphs/{part}")
        X, src, cnt = build(part, frames, R, D)
        arrs = {f"{c}-{'noCF' if k == 'nocf' else 'CF'}": x for (c, k), x in X.items()}
        pr = {"frames": len(frames), "videos": G.videos_check(sorted({C.video_of(f) for f in frames})), "counts": dict(cnt)}
        # 前回の材料との一致（CF の 5 腕と DGH-noCF）
        prev = {}
        for arm, pname in PREV.items():
            p = O / f"graph/{pname}_{part}.npz"
            with np.load(p) as d:
                pf = [str(f) for f in d["frame_ids"]]
                px = d["x"]
            same_frames = pf == frames
            if arm in arrs:
                prev[arm] = {"prev": str(p), "prev_sha256": C.sha256(p), "frames_same_order": same_frames,
                             "bit_equal": bool(same_frames and np.array_equal(px, arrs[arm]))}
            else:
                prev[arm] = {"prev": str(p), "prev_sha256": C.sha256(p), "frames_same_order": same_frames}
        pr["equals_previous"] = prev
        if not all(v.get("bit_equal", True) and v["frames_same_order"] for v in prev.values()):
            raise RuntimeError(f"組み直しが前回の材料と一致しない {part}")
        # noCF と CF の違い（train は塔が違うので違うはず。val は同じ塔）
        pr["noCF_vs_CF_same_frame_fraction"] = {
            c: float(np.mean(np.all((arrs[f"{c}-noCF"] == arrs[f"{c}-CF"]).reshape(len(frames), -1), 1))) for c in CORES}
        # 入れ替え
        mp_doc = json.loads((MAP / f"mapping_{part}.json").read_text())
        mapping = mp_doc["mapping"]
        if set(mapping) != set(frames) or len(mapping) != len(frames):
            raise SystemExit(f"T→P の対応表のフレームの集合がグラフと違う {part}: {len(mapping)} / {len(frames)}")
        st = mapping_stats(mapping)
        idx = {f: i for i, f in enumerate(frames)}
        rows = np.array([idx[mapping[f]] for f in frames])
        for c in CORES:
            arrs[f"{c}-S"] = arrs[f"{c}-noCF"][rows]
        pr["shuffle"] = {"mapping_file": str(MAP / f"mapping_{part}.json"), "mapping_sha256": st["mapping_sha256"],
                         "seed": mp_doc["seed"], "rule": mp_doc["rule"], "covers_graph_frames": True,
                         "fixed_point_fraction": st["fixed_point_fraction"], "same_video_fraction": st["same_video_fraction"],
                         "is_bijection": st["is_bijection"],
                         "values_cross_part": sorted({C.video_of(g) for g in mapping.values()} - set(fold[part])),
                         "per_arm": {c: shuffle_check(arrs[f"{c}-noCF"], arrs[f"{c}-S"], frames, mapping) for c in CORES}}
        ident = mapping_stats({f: f for f in frames})
        pr["shuffle_control_identity"] = {"fixed_point_fraction": ident["fixed_point_fraction"],
                                          "same_video_fraction": ident["same_video_fraction"]}
        # 表と出どころ
        fl = {arm: flags(x) for arm, x in arrs.items()}
        pr["flags"] = fl
        pr["table_check"] = table_check(fl)
        bad = dict(fl)
        bad["D-noCF"] = flags(arrs["DH-noCF"])                         # 対照: 表と違う腕（D に手の節）
        pr["table_check_control_wrong_arm"] = table_check(bad)
        pr["provenance_noCF"] = provenance(arrs, "noCF")
        pr["provenance_CF"] = provenance(arrs, "CF")
        mixed = dict(arrs)
        m = arrs["DG-noCF"].copy()
        k = max(1, len(frames) // 10)
        m[:k] = arrs["DG-CF"][:k]                                       # 対照: noCF の腕の先頭 1 割に CF の信号を混ぜた写し
        mixed["DG-noCF"] = m
        pr["provenance_noCF_control_cf_mixed"] = provenance(mixed, "noCF")
        pr["provenance_noCF_control_cf_mixed"]["mixed_rows"] = k
        pr["provenance_S"] = {c: bool(np.array_equal(arrs[f"{c}-S"], arrs[f"{c}-noCF"][rows])) for c in CORES}
        pr["sources"] = {"noCF": sorted({json.dumps(s, sort_keys=True) for s in src["nocf"].values()}),
                         "CF": sorted({json.dumps(s, sort_keys=True) for s in src["cf"].values()})}
        if pr["table_check"]["violations"] or pr["provenance_noCF"]["violations"] or pr["provenance_CF"]["violations"]:
            raise RuntimeError(f"検査の外れ {part}")
        # 書く: 新しい腕はファイル、前回と同じものは記号のリンク
        files = {}
        for arm in [f"{c}-{s}" for c in CORES for s in ("noCF", "S")] :
            if arm == "DGH-noCF":
                continue
            p = out / f"{arm}_{part}.npz"
            np.savez(p, frame_ids=np.asarray(frames), x=arrs[arm])
            files[arm] = {"path": str(p), "sha256": C.sha256(p), "kind": "new"}
        for arm, pname in PREV.items():
            p = out / f"{arm}_{part}.npz"
            target = O / f"graph/{pname}_{part}.npz"
            if p.is_symlink() or p.exists():
                p.unlink()
            p.symlink_to(target)
            files[arm] = {"path": str(p), "target": str(target), "sha256": C.sha256(p), "kind": "symlink_to_previous"}
        pr["files"] = files
        pr["videos_used"] = videos
        rep["parts"][part] = pr
        print(part, json.dumps({"frames": len(frames), "prev_equal": {k: v.get("bit_equal") for k, v in prev.items()},
                                "table": pr["table_check"], "table_ctrl": pr["table_check_control_wrong_arm"]["violations"],
                                "prov": (pr["provenance_noCF"]["violations"], pr["provenance_CF"]["violations"],
                                         pr["provenance_noCF_control_cf_mixed"]["violations"]),
                                "shuffle": {c: v["value_set_equal"] and v["rows_follow_mapping"] and v["inverse_restores"]
                                            for c, v in pr["shuffle"]["per_arm"].items()},
                                "fixed": pr["shuffle"]["fixed_point_fraction"], "same_video": pr["shuffle"]["same_video_fraction"],
                                "ident_ctrl": pr["shuffle_control_identity"]["fixed_point_fraction"],
                                "noCF_vs_CF": pr["noCF_vs_CF_same_frame_fraction"]}, ensure_ascii=False), flush=True)
    rep["test_unused"] = {p: rep["parts"][p]["videos"] for p in ("train", "val")}
    rep["test_control_04_mixed"] = G.videos_check(sorted({C.video_of(f) for f in
                                                          [f for v, fr, _ in C.phase_sequences(fold["train"]) for f in fr] + ["04_1_0001"]}))
    C.write_json(a.report, rep)
    print("[c_graphs] DONE", flush=True)


if __name__ == "__main__":
    main()

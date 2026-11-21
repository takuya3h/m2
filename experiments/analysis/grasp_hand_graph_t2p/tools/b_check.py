"""Task B: 材料の要約値を記録と照らし、T→P の学習設定を run の記録から写す（非公式 T-2026-11-21-grasp-hand-graph-t2p-match、SPEC §1.3・§3.2）。

    .venv/bin/python experiments/analysis/grasp_hand_graph_t2p/tools/b_check.py --out <T>/b/b_check.json

照らすもの（読むだけ。書くのは --out と対照の写しの置き場 --scratch だけ）:
  1. 前回のグラフの目録 signals_manifest.json の要約値（前回の RESULT §3 の 24d9139d…）と、目録が名指す 14 のグラフ・
     4 つの検出の配列・8 つの G3・H4 の推論の要約値
  2. T→P の入れ替えの記録 shuffle_record.json の元の信号・入れ替えた信号・対応表の要約値（D0・D0-RT・D0-INST-UQ）
  3. T→P の参照の腕の run（W1 は stage2fix_dp_*、W2・W3 は w23b_dp_W2/W3_*。4 型 × 空・予測-noCF・入れ替え）の config の
     信号・受け取り手の重み・特徴のキャッシュの要約値
  4. 学習設定（界面の学習率・weight decay・学習率の予定・固定の epoch、受け取り手の学習率・weight decay・optimizer、
     受け取り手の扱い、W ごとの受け取り手の側の学ぶ名前の集合）を、上の 36 本と前回のグラフの run の config から並べ、
     W ごとに型の間で食い違わないかを見る
  5. 対照: 1 バイト変えた写しで照合が食い違いを出す（グラフ 1 つ・T→P の信号 1 つ・対応表 1 つ）
"""
from __future__ import annotations

import argparse
import glob
import json
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402
from stage2pilot.shuffle_signals import mapping_stats  # noqa: E402

TASK = "T-2026-11-21-grasp-hand-graph-t2p-match"
S = Path("/home/ubuntu/slocal2/stage2pilot_store")
MANIFEST = ROOT / "experiments/analysis/grasp_hand_graph_pilot/signals_manifest.json"
MANIFEST_SHA = "24d9139d3487ee5533d7b26ec9fcff7134cda386619aee3b23fab990c01a1bbd"  # 前回の RESULT §3
SHUF_REC = ROOT / "experiments/analysis/stage2_pilot_fix/shuffle/shuffle_record.json"
TP_TYPES = ("D1-L1", "D1-L2", "D2", "D3-L2")
TP_ARMS = ("empty", "pred_noCF", "shuffle")
TP_PREFIX = {"W1": "stage2fix_dp", "W2": "w23b_dp_W2", "W3": "w23b_dp_W3"}
GRAPH_PREV = "grasp_hand_graph_arm"


def tp_run(scope, t, arm):
    hits = [p for p in glob.glob(str(ROOT / f"experiments/phase1/{TP_PREFIX[scope]}_*_{t}_{arm}_ep4_seed42"))]
    if len(hits) != 1:
        raise SystemExit(f"T→P の run が一つに決まらない: {scope} {t} {arm} {hits}")
    return Path(hits[0])


def cfg_of(run):
    return yaml.safe_load((run / "config.yaml").read_text())


def settings(cfg):
    sr = cfg["stop_rule"]
    ro = cfg.get("receiver_optim")
    sc = cfg.get("scope_check")
    return {"iface_lr": sr["lr"], "iface_weight_decay": sr["weight_decay"], "lr_schedule": sr.get("lr_schedule"),
            "fixed_epochs": sr.get("fixed_epochs"), "converge": sr.get("converge"),
            "receiver_lr": ro["lr"] if ro else None, "receiver_weight_decay": ro["weight_decay"] if ro else None,
            "receiver_optimizer": ro["optimizer"] if ro else None, "receiver_mode": cfg["receiver"]["mode"],
            "scope": cfg.get("scope", "W1"),
            "receiver_trainable_names": sorted(n for n in (sc["trainable_names"] if sc else []) if n.startswith("head."))}


def check_file(path, want):
    got = C.sha256(path)
    return {"path": str(path), "want": want, "got": got, "match": got == want}


def flip_one_byte(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    b = bytearray(dst.read_bytes())
    b[len(b) // 2] ^= 0x01
    dst.write_bytes(bytes(b))
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--scratch", required=True, help="対照の写しの置き場（本契約の保存先の下）")
    a = ap.parse_args()
    out = {"task_id": TASK, "unofficial": True}
    # 1. 前回のグラフの目録
    man_sha = C.sha256(MANIFEST)
    man = json.loads(MANIFEST.read_text())
    g = {"manifest": {"path": str(MANIFEST), "want": MANIFEST_SHA, "got": man_sha, "match": man_sha == MANIFEST_SHA}, "files": []}
    for part, arms in man["graph"].items():
        for arm, v in arms.items():
            g["files"].append({"kind": f"graph/{arm}_{part}", **check_file(Path(v["path"]), v["sha256"])})
    for k, v in man["det"].items():
        g["files"].append({"kind": f"det/{k}", **check_file(Path(v["npz"]), v["npz_sha256"])})
    for k, v in man["raw_signals"].items():
        g["files"].append({"kind": f"raw/{k}", **check_file(Path(v["npz"]), v["sha256"])})
    g["n"], g["n_match"] = len(g["files"]), sum(f["match"] for f in g["files"])
    out["graph_manifest"] = g
    # 2. T→P の入れ替えの記録
    rec = json.loads(SHUF_REC.read_text())
    sh = {"record": str(SHUF_REC), "record_sha256": C.sha256(SHUF_REC), "seed": rec["seed"], "files": [], "mapping": {}}
    for part, pr in rec["parts"].items():
        mp = json.loads(Path(pr["mapping_file"]).read_text())["mapping"]
        st = mapping_stats(mp)
        sh["mapping"][part] = {"file": pr["mapping_file"], "want": pr["mapping_sha256"], "got": st["mapping_sha256"],
                               "match": st["mapping_sha256"] == pr["mapping_sha256"], "frames": st["frames"],
                               "fixed_point_fraction": st["fixed_point_fraction"], "same_video_fraction": st["same_video_fraction"],
                               "is_bijection": st["is_bijection"], "videos": C.assert_no_test(mp, f"b_check/mapping/{part}")}
        for s in ("D0", "D0-RT", "D0-INST-UQ"):
            v = pr["signals"][s]
            sh["files"].append({"kind": f"final/{s}_{part}", **check_file(Path(v["source"]), v["source_sha256"])})
            sh["files"].append({"kind": f"shuffle/{s}_{part}", **check_file(Path(v["out"]), v["out_sha256"])})
    sh["n"], sh["n_match"] = len(sh["files"]), sum(f["match"] for f in sh["files"])
    out["tp_shuffle"] = sh
    # 3・4. T→P の参照の腕の run の config
    runs, sets = [], {}
    for scope in ("W1", "W2", "W3"):
        for t in TP_TYPES:
            for arm in TP_ARMS:
                run = tp_run(scope, t, arm)
                cfg = cfg_of(run)
                files = [check_file(Path(f["path"]), f["sha256"]) for f in cfg["signals_train"] + cfg["signals_val"]]
                files.append(check_file(Path(cfg["receiver"]["head"]), cfg["receiver"]["head_sha256"]))
                files.append(check_file(Path(cfg["receiver"]["cache"]), cfg["receiver"]["cache_sha256"]))
                st = settings(cfg)
                runs.append({"scope": scope, "type": t, "arm": arm, "run": run.name, "host": (run / "server.txt").read_text().strip()
                             if (run / "server.txt").exists() else None, "command": (run / "command.sh").read_text().strip().splitlines()[-1],
                             "files": files, "files_match": all(f["match"] for f in files), "settings": st,
                             "videos": cfg["videos"]})
                sets.setdefault(scope, []).append(st)
    agree = {}
    for scope, lst in sets.items():
        keys = [k for k in lst[0] if k != "receiver_mode"]
        diff = {k: sorted({json.dumps(x[k], sort_keys=True) for x in lst}) for k in keys}
        agree[scope] = {"n_runs": len(lst), "disagree": {k: v for k, v in diff.items() if len(v) > 1},
                        "values": {k: json.loads(v[0]) for k, v in diff.items() if len(v) == 1 and k != "receiver_trainable_names"},
                        "receiver_trainable_n": len(lst[0]["receiver_trainable_names"]),
                        "receiver_modes": sorted({x["receiver_mode"] for x in lst})}
    out["tp_runs"] = runs
    out["tp_settings_by_scope"] = agree
    out["tp_test_overlap"] = sorted({v for r in runs for p in ("train", "val") for v in r["videos"][p]} & set(C.TEST_VIDEOS))
    # 前回のグラフの run（収束規則）の学習設定（参考）
    prev = {}
    for scope in ("W1", "W2", "W3"):
        hits = sorted(glob.glob(str(ROOT / f"experiments/phase1/{GRAPH_PREV}_*_GR-{scope}-N10-L1_DGH-noCF_conv_seed42")))
        cfg = cfg_of(Path(hits[0]))
        prev[scope] = {"run": Path(hits[0]).name, "settings": settings(cfg)}
    out["graph_prev_settings"] = prev
    # 5. 対照（1 バイト変えた写し）
    scr = Path(a.scratch)
    gfile = Path(man["graph"]["val"]["D"]["path"])
    sfile = Path(rec["parts"]["val"]["signals"]["D0"]["out"])
    mfile = Path(rec["parts"]["val"]["mapping_file"])
    c_g = check_file(flip_one_byte(gfile, scr / "D_val_flip.npz"), man["graph"]["val"]["D"]["sha256"])
    c_s = check_file(flip_one_byte(sfile, scr / "D0_val_shuffle_flip.npz"), rec["parts"]["val"]["signals"]["D0"]["out_sha256"])
    mtext = mfile.read_text()
    mp = json.loads(mtext)["mapping"]
    k0 = sorted(mp)[0]
    mp2 = dict(mp)
    mp2[k0], mp2[sorted(mp)[1]] = mp[sorted(mp)[1]], mp[k0]      # 対応を一組だけ入れ替えた写し
    c_m = {"want": rec["parts"]["val"]["mapping_sha256"], "got": mapping_stats(mp2)["mapping_sha256"]}
    c_m["match"] = c_m["want"] == c_m["got"]
    out["controls"] = {"graph_one_byte": c_g, "tp_shuffle_one_byte": c_s, "mapping_one_pair_swapped": c_m}
    out["summary"] = {"graph_manifest_ok": g["manifest"]["match"] and g["n_match"] == g["n"],
                      "tp_shuffle_ok": sh["n_match"] == sh["n"] and all(m["match"] for m in sh["mapping"].values()),
                      "tp_runs_files_ok": all(r["files_match"] for r in runs), "tp_runs": len(runs),
                      "tp_settings_disagree": {s: list(v["disagree"]) for s, v in agree.items()},
                      "controls_detect": not (c_g["match"] or c_s["match"] or c_m["match"])}
    C.write_json(a.out, out)
    print(json.dumps(out["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()

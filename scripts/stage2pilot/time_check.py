"""Task C-4: 保存した信号の時刻の確認（非公式 T-2026-10-18-stage2-pilot-folda）。

experiments/analysis/frame_signal_audit/tools/time_alignment_check.py の judge と shifted_copy を
そのまま使う（受け手の規則 = フレーム名の一致で突き合わせ、並びを k = -2..+2 ずらした一致率の最大の k）。
陽性対照として、名前を区間内で一つ先へ付け替えた写し（名前 t の行が t-1 の情報を持つ）が -1 と判定されること、
陰性対照としてずらさない写しが 0 と判定されることを、信号ごと・分割ごとに確かめる。

    python scripts/stage2pilot/time_check.py --signals-dir <dir> --out <json> [--parts train,val]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402

_TOOL = C.ROOT / "experiments/analysis/frame_signal_audit/tools/time_alignment_check.py"
_spec = importlib.util.spec_from_file_location("time_alignment_check", _TOOL)
tac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tac)
NT = 15


def clips_of(part):
    d = json.loads((C.MANIFEST_DIR / f"{part}.json").read_text())
    return [(c["clip_id"], [f["frame"] for f in c["frames"]], [int(f["label"]) for f in c["frames"]]) for c in d["clips"]]


def tool_sets(part):
    d = json.loads((C.DET_ANN_A / f"instances_{part}.json").read_text())
    stem = {im["id"]: Path(im["file_name"]).stem for im in d["images"]}
    out = {s: set() for s in stem.values()}
    for a in d["annotations"]:
        out[stem[a["image_id"]]].add(a["category_id"])
    return out


def inst_set(row, thr=0.5):
    """D0-INST の行（K × (15 + 4 [+ 256])）から、最大クラスのスコアが thr を超えるトークンのクラスの集合。"""
    s = row[:, :NT]
    return {int(c) for c, v in zip(s.argmax(1), s.max(1)) if v > thr}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--signals-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--parts", default="train,val")
    ap.add_argument("--only", default="", help="信号名をカンマ区切りで絞る（交差適合版など）")
    a = ap.parse_args()
    d = Path(a.signals_dir)
    report = {"tool": str(_TOOL.relative_to(C.ROOT)), "tool_sha256": C.sha256(_TOOL), "offsets": list(tac.OFFSETS),
              "signals_dir": str(d), "results": {}}
    for part in a.parts.split(","):
        clips = clips_of(part)
        C.assert_no_test([f for _, fr, _ in clips for f in fr], "time_check")
        label_of = {f: lab for _, fr, labs in clips for f, lab in zip(fr, labs)}
        tools = tool_sets(part)
        # 行から在否の 15 次元を一度だけ作る（行そのものから決まる変換なので、名前のずらしの検査は変わらない）
        def rt_pres(r):
            n = np.linalg.norm(r.reshape(NT, 256), axis=1)
            return n > 0.5 * n.max()

        def inst_pres(r):
            v = np.zeros(NT, bool)
            v[list(inst_set(r))] = True
            return v

        frac = lambda r, s: float(np.mean([r[c] == (c in s) for c in range(NT)]))  # noqa: E731
        rules = {
            "P0": (None, lambda f: label_of[f], lambda r, y: float(int(np.argmax(r)) == y)),
            "P-GT": (None, lambda f: label_of[f], lambda r, y: float(int(np.argmax(r)) == y)),
            "D0": (lambda r: r > 0.5, lambda f: tools[f], frac),
            "D-GT": (lambda r: r > 0.5, lambda f: tools[f], lambda r, s: float(set(np.flatnonzero(r).tolist()) == s)),
            "D0-RT": (rt_pres, lambda f: tools[f], frac),
            "D0-INST": (inst_pres, lambda f: tools[f], frac),
            "D0-INST-UQ": (inst_pres, lambda f: tools[f], frac),
            "D-GT-INST": (inst_pres, lambda f: tools[f], lambda r, s: float(set(np.flatnonzero(r).tolist()) == s)),
        }
        for name, (prep, truth_of, agree) in rules.items():
            if a.only and name not in a.only.split(","):
                continue
            path = d / f"{name}_{part}.npz"
            if not path.exists():
                report["results"][f"{name}/{part}"] = {"status": "UNKNOWN（ファイルが無い）", "path": str(path)}
                continue
            cache = C.load_signal(path)
            if prep is not None:
                cache = {f: prep(r) for f, r in cache.items()}
            plain = tac.judge(cache, clips, truth_of, agree)
            shifted = tac.judge(tac.shifted_copy(cache, clips), clips, truth_of, agree)
            report["results"][f"{name}/{part}"] = {
                "path": str(path), "rows": len(cache), "unshifted": plain, "shifted_control": shifted,
                "control_ok": plain["judged_offset"] == 0 and shifted["judged_offset"] == -1}
            print(f"{name}/{part}: matched {plain['matched_by_name']}/{plain['receiver_keys']} "
                  f"verdict={plain['verdict']} shifted->{shifted['verdict']} ok={report['results'][f'{name}/{part}']['control_ok']}",
                  flush=True)
    C.write_json(a.out, report)


if __name__ == "__main__":
    main()

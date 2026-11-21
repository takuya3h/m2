"""既存の中身の一覧と比べ（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、完了判定 j）。読むだけ。書くのは --out だけ。

    python listing.py start   --out <T>/start/j_listing_start.json   開始時の一覧（ファイルごとの大きさと mtime_ns）
    python listing.py compare --out <T>/e/j_unchanged.json           今の一覧と比べる。本契約の新しい run（grasp_hand_irn_hice_htt_*）は
                                                                     根に入らない。対照: 本契約の新しいファイルを一つ加えた一覧で、追加として拾う
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
S = Path("/home/ubuntu/slocal2/stage2pilot_store")
T = S / "grasp_hand_irn_hice_htt"
ROOTS = [S / "grasp_hand_graph", S / "grasp_hand_graph_t2p", S / "T-2026-10-18-stage2-pilot-folda",
         S / "T-2026-10-19-stage2-pilot-fix-epoch4-shuffle",
         ROOT / "experiments/analysis/grasp_hand_graph_pilot", ROOT / "experiments/analysis/grasp_hand_graph_t2p",
         ROOT / "third_party", ROOT / "data/raw", ROOT / "data/external", ROOT / "data/annotations"]
RUN_PREFIXES = ("grasp_hand_graph_", "stage2fix_dp_", "grasprt_tw_", "grasprc_")   # 本契約の run は grasp_hand_irn_hice_htt_ で始まる


def listing():
    out = {}
    tops = list(ROOTS) + sorted(p for p in (ROOT / "experiments/phase1").iterdir() if p.name.startswith(RUN_PREFIXES))
    for r in tops:
        for dp, _, fn in os.walk(r):
            for f_ in fn:
                q = os.path.join(dp, f_)
                try:
                    st = os.lstat(q)
                except FileNotFoundError:
                    continue
                out[q] = [st.st_size, st.st_mtime_ns]
    return [str(t) for t in tops], out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["start", "compare"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    tops, now = listing()
    if a.cmd == "start":
        Path(a.out).write_text(json.dumps({"roots": tops, "files": now}))
        print(json.dumps({"roots": len(tops), "files": len(now), "bytes": sum(v[0] for v in now.values())}))
        return
    start = json.loads((T / "start/j_listing_start.json").read_text())
    st = start["files"]
    changed = sorted(k for k in st if k in now and now[k] != st[k])
    removed = sorted(k for k in st if k not in now)
    added = sorted(k for k in now if k not in st)
    ctrl = dict(now)
    ctrl[str(ROOT / "experiments/analysis/grasp_hand_graph_pilot/__control_new_file__")] = [1, 1]
    out = {"roots_start": start["roots"], "roots_now": tops, "n_start": len(st), "n_now": len(now),
           "n_changed": len(changed), "changed": changed[:50], "n_removed": len(removed), "removed": removed[:50],
           "n_added": len(added), "added": added[:50],
           "control_added": sum(1 for k in ctrl if k not in st) - len(added)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: out[k] for k in ("n_start", "n_now", "n_changed", "n_removed", "n_added", "control_added")}))


if __name__ == "__main__":
    main()

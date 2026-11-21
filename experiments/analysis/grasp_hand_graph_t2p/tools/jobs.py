"""run の一覧を作る（非公式 T-2026-11-21-grasp-hand-graph-t2p-match、SPEC §3.1・§5.4）。一行 = 名前|接頭辞|dp_train train の引数。

    python3 experiments/analysis/grasp_hand_graph_t2p/tools/jobs.py <群> > jobs_<群>.txt

群:
  ep4chk   4 epoch で止める確かめ（§3.1）と、それと比べる続けた run（W ごとに DGH-noCF s1 と D1-L1 の予測-noCF）。12 本
  main     §5.4 の表の残り（グラフの腕・省いた先の確かめ・T→P の参照の型）。ep4chk の続けた run 6 本は含めない
  all      ep4chk と main
  ep4all   §3.1 の比べが一致しなかったときに回す、4 epoch で止める run の全腕（main と同じ腕を --fixed-epochs 4 で）

続けた run は --fixed-epochs 16 --record-epochs 4 8 12 16（学習率は一定で全体の長さに依らない。audit B-3）。
"""
from __future__ import annotations

import sys

T = "/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph_t2p"
SCOPES = ("W1", "W2", "W3")
SETTINGS = {"s1": (10, 1), "s2": (10, 2), "s3": (30, 1), "s4": (30, 2)}
TP_TYPES = ("D1-L1", "D1-L2", "D2", "D3-L2")
TP_ARMS = ("empty", "pred_noCF", "shuffle")
LONG = "--fixed-epochs 16 --record-epochs 4 8 12 16"
SHORT = "--fixed-epochs 4 --record-epochs 4"


def gr_arm(core, sig):
    return f"{core}-{sig}"


def graph_jobs(length, prefix):
    out = []
    for sc in SCOPES:
        rows = [("empty", "s1")]
        rows += [(gr_arm(c, s), st) for c in ("D", "DG", "DH") for s in ("noCF", "CF", "S") for st in ("s1", "s3")]
        rows += [(gr_arm(c, s), st) for c in ("DGH", "DGH-U") for s in ("noCF", "CF", "S") for st in SETTINGS]
        rows += [("DGH-GT", st) for st in SETTINGS]
        rows += [("empty", "s4"), ("D-noCF", "s2")]                      # §5.3 の確かめ
        for arm, st in rows:
            n, ell = SETTINGS[st]
            desc = f"GR-{sc}-N{n}-L{ell}_{arm}_ep{16 if length == LONG else 4}"
            out.append(f"{desc}|{prefix}|--type GR --gr-dir {T} --gr-N {n} --gr-L {ell} --scope {sc} --arm {arm} {length}")
    return out


def tp_jobs(length, prefix, types=TP_TYPES, arms=TP_ARMS):
    out = []
    for sc in SCOPES:
        for t in types:
            for arm in arms:
                inst = " --inst-variant uq" if t == "D3-L2" else ""
                desc = f"{t}_{arm}_ep{16 if length == LONG else 4}"
                out.append(f"{desc}|{prefix}_{sc}|--type {t} --arm {arm} --scope {sc}{inst} {length}")
    return out


def ep4chk():
    short = [j for j in graph_jobs(SHORT, "grasp_hand_graph_t2p_ep4chk") if "-N10-L1_DGH-noCF_" in j]
    short += tp_jobs(SHORT, "grasp_hand_graph_t2p_ep4chk_tp", types=("D1-L1",), arms=("pred_noCF",))
    long_ = [j for j in graph_jobs(LONG, "grasp_hand_graph_t2p_gr") if "-N10-L1_DGH-noCF_" in j]
    long_ += tp_jobs(LONG, "grasp_hand_graph_t2p_tp", types=("D1-L1",), arms=("pred_noCF",))
    return short + long_


def main_jobs():
    chk = set(ep4chk())
    return [j for j in graph_jobs(LONG, "grasp_hand_graph_t2p_gr") + tp_jobs(LONG, "grasp_hand_graph_t2p_tp") if j not in chk]


def ep4all():
    return [j for j in graph_jobs(SHORT, "grasp_hand_graph_t2p_ep4all") + tp_jobs(SHORT, "grasp_hand_graph_t2p_ep4all_tp")]


if __name__ == "__main__":
    g = sys.argv[1]
    jobs = {"ep4chk": ep4chk, "main": main_jobs, "all": lambda: ep4chk() + main_jobs(), "ep4all": ep4all}[g]()
    print("\n".join(jobs))

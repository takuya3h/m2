"""run の一覧を作る（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、SPEC §5.2）。一行 = 名前|接頭辞|dp_train train の引数。

    python3 experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/jobs.py <群>

群:
  main   SPEC §5.2 の表の腕（確かめを除く）。IRN 87・HiCE 69・HTT 87 の 243 本。接頭辞 grasp_hand_irn_hice_htt_arm
  chk    SPEC §5.2 の表の確かめ（IRN・HiCE・HTT の A0 の s4・W1、HiCE の DH の s3・W1、HiCE の D の s1・W1）。5 本。接頭辞 grasp_hand_irn_hice_htt_chk
  all    chk と main（248 本。回し直しの 2 本は run_repro.sh）
  fill   確かめが一致しなかったときに回す、省いた組み合わせ（利用者の回答 (3)）。引数に省いた先の名前を渡す: a0 / hice_d / hice_dh

どれも収束規則（--converge）で、最良と最後の回の val の確率を保存する（--save-last-probs）。
"""
from __future__ import annotations

import sys

GRAPH_STORE = "/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph"
SCOPES = ("W1", "W2", "W3")
SETTINGS = {"s1": (10, 1), "s2": (10, 2), "s3": (30, 1), "s4": (30, 2)}
FULL = ("D", "DG", "DH", "DGH", "DGH-U", "DGH-noCF", "DGH-GT")
MAIN = "grasp_hand_irn_hice_htt_arm"
CHK = "grasp_hand_irn_hice_htt_chk"


def job(t, arm, st, sc, prefix):
    n, ell = SETTINGS[st]
    desc = f"{t}-{sc}-N{n}-L{ell}_{arm}_conv"
    return f"{desc}|{prefix}|--type {t} --gr-dir {GRAPH_STORE} --gr-N {n} --gr-L {ell} --scope {sc} --arm {arm} --converge --save-last-probs"


def main_jobs():
    out = []
    for t in ("IRN", "HiCE", "HTT"):
        for sc in SCOPES:
            arms = FULL if t != "HiCE" else ("DG", "DGH", "DGH-U", "DGH-noCF", "DGH-GT")
            rows = [(arm, st) for arm in arms for st in SETTINGS]
            if t == "HiCE":
                rows += [("DH", "s1"), ("DH", "s2")]
            rows += [("empty", "s1")]
            out += [job(t, arm, st, sc, MAIN) for arm, st in rows]
    return out


def chk_jobs():
    out = [job(t, "empty", "s4", "W1", CHK) for t in ("IRN", "HiCE", "HTT")]
    out += [job("HiCE", "DH", "s3", "W1", CHK), job("HiCE", "D", "s1", "W1", CHK)]
    return out


def fill_jobs(which):
    out = []
    if which == "a0":
        out += [job(t, "empty", st, sc, MAIN) for t in ("IRN", "HiCE", "HTT") for sc in SCOPES for st in ("s2", "s3", "s4")]
    if which == "hice_d":
        out += [job("HiCE", "D", st, sc, MAIN) for sc in SCOPES for st in SETTINGS]
    if which == "hice_dh":
        out += [job("HiCE", "DH", st, sc, MAIN) for sc in SCOPES for st in ("s3", "s4")]
    return out


if __name__ == "__main__":
    g = sys.argv[1]
    if g == "fill":
        print("\n".join(fill_jobs(sys.argv[2])))
    else:
        print("\n".join({"main": main_jobs, "chk": chk_jobs, "all": lambda: chk_jobs() + main_jobs()}[g]()))

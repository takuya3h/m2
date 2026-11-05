"""Differences between levels of T-2026-11-06-dtower-step-profile (rank 0), from levels.json.

    python derive.py <levels.json> <derived.json>

- processes (SPEC §4.4): for the same per-GPU batch, the per-step difference 2 processes - 1
  process and its parts; over an epoch, the synchronisation share = (step_2 - step_1) x steps_2
  and the share of running twice the steps on one GPU = step_1 x (steps_1 - steps_2). The two
  add up to epoch_1 - epoch_2 by construction (checked).
- loading: loaded - no-load for the same batch and processes, per part.
"""
import json
import sys

PARTS = ("step", "data", "forward", "loss", "backward", "optimizer", "rest", "collectives", "reduce")
levels = {lv["number"]: lv for lv in json.load(open(sys.argv[1]))}


def r0(n):
    return levels[n]["ranks"][0]


out = {"processes": [], "loading": []}
for two, one in ((1, 5), (2, 6)):
    a, b = r0(two), r0(one)
    d = {p: a["mean"][p] - b["mean"][p] for p in PARTS}
    sync = d["step"] * a["steps_per_epoch"]
    double = b["mean"]["step"] * (b["steps_per_epoch"] - a["steps_per_epoch"])
    e2, e1 = a["epoch_projection"]["seconds_actual_steps"], b["epoch_projection"]["seconds_actual_steps"]
    assert abs((e1 - e2) - (double - sync)) < 1e-6
    out["processes"].append({"two": levels[two]["level"], "one": levels[one]["level"], "per_step_diff": d,
                             "epoch_two_s": e2, "epoch_one_s": e1, "epoch_one_minus_two_s": e1 - e2,
                             "sync_share_s": sync, "double_steps_share_s": double,
                             "steps_two": a["steps_per_epoch"], "steps_one": b["steps_per_epoch"]})
for load, noload in ((1, 7), (2, 8)):
    for rank in (0, 1):
        a, b = levels[load]["ranks"][rank], levels[noload]["ranks"][rank]
        out["loading"].append({"loaded": levels[load]["level"], "no_load": levels[noload]["level"], "rank": rank,
                               "per_step_diff": {p: a["mean"][p] - b["mean"][p] for p in PARTS},
                               "max_memory_allocated_bytes": [a["memory"]["max_memory_allocated_bytes"],
                                                              b["memory"]["max_memory_allocated_bytes"]],
                               "step_sd": [a["sd"]["step"], b["sd"]["step"]]})
json.dump(out, open(sys.argv[2], "w"), indent=1)
for k in out:
    for row in out[k]:
        print(k, {x: (round(v, 4) if isinstance(v, float) else v) for x, v in row.items() if x != "per_step_diff"},
              {p: round(v, 4) for p, v in row["per_step_diff"].items()})

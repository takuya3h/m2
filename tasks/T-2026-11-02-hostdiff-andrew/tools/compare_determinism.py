"""Task B: 同じ seed の短い fine-tune 二回の、各 micro-step の損失の列を bit 単位で比べる（読むだけ）。

損失は観測器が float の 16 進で書いた値（``TOWER_SEARCH_LOSS_HEX=1``）。rank ごとに比べる。
``--self-test`` は二回目の列の一つの値の最下位の桁を変え、不一致になることを確かめる。

    python3 tasks/T-2026-11-02-hostdiff-andrew/tools/compare_determinism.py <dir_a> <dir_b> [--self-test]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path


def losses(work, rank):
    rows = [json.loads(line) for line in (Path(work) / f"step_times_rank{rank}.jsonl").read_text().splitlines()]
    micro = [r for r in rows if r["kind"] == "micro"]
    return [r["loss"] for r in micro], sum(r["kind"] == "opt" for r in rows)


def flip_last_bit(hex_value):
    bits = struct.unpack("<Q", struct.pack("<d", float.fromhex(hex_value)))[0] ^ 1
    return struct.unpack("<d", struct.pack("<Q", bits))[0].hex()


def summary(seq):
    return hashlib.sha256("\n".join(seq).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("a")
    parser.add_argument("b")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    out = {"ranks": {}}
    for rank in (0, 1):
        la, oa = losses(args.a, rank)
        lb, ob = losses(args.b, rank)
        if args.self_test:
            lb = list(lb)
            lb[len(lb) // 2] = flip_last_bit(lb[len(lb) // 2])
        first = next((i for i, (x, y) in enumerate(zip(la, lb)) if x != y), None)
        out["ranks"][rank] = {"micro_steps": [len(la), len(lb)], "optimizer_steps": [oa, ob],
                              "sha256": [summary(la), summary(lb)],
                              "identical": la == lb, "first_difference_index": first,
                              "first_loss": la[0] if la else None, "last_loss": la[-1] if la else None}
    out["identical_all_ranks"] = all(v["identical"] for v in out["ranks"].values())
    out["self_test"] = args.self_test
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

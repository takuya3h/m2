"""Task B: 同じ seed の短い学習二回の損失の列を bit 単位で比べる（完了判定 b）。

各 rank の micro-step の損失（16 進の float）を順に並べた列の sha256 と、一致の有無、歩数を出す。
--selftest: 二回目の列の一つの値を最下位の桁で変えると不一致になることを示す。

    python compare_determinism.py <SCR> <out.json> [--selftest]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def series(work):
    out = {}
    for f in sorted((work / "steps").glob("finetune_steps_rank*.jsonl")):
        rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
        out[f.stem.rsplit("_", 1)[1]] = {"loss": [r["loss_hex"] for r in rows if r["event"] == "micro"],
                                        "optimizer_steps": sum(r["event"] == "optimizer" for r in rows)}
    return out


def flip_last_bit(hexfloat):
    v = float.fromhex(hexfloat)
    import struct
    bits = struct.unpack("<Q", struct.pack("<d", v))[0] ^ 1
    return struct.unpack("<d", struct.pack("<Q", bits))[0].hex()


def main():
    scr, out = Path(sys.argv[1]), Path(sys.argv[2])
    a, b = series(scr / "controls/control1"), series(scr / "controls/control2")
    if "--selftest" in sys.argv:
        r = sorted(b)[0]
        b[r]["loss"][len(b[r]["loss"]) // 2] = flip_last_bit(b[r]["loss"][len(b[r]["loss"]) // 2])
    res = {"ranks": sorted(set(a) | set(b)), "per_rank": {}}
    for r in res["ranks"]:
        la, lb = a.get(r, {}).get("loss", []), b.get(r, {}).get("loss", [])
        res["per_rank"][r] = {
            "micro_steps": [len(la), len(lb)],
            "optimizer_steps": [a.get(r, {}).get("optimizer_steps"), b.get(r, {}).get("optimizer_steps")],
            "sha256": [hashlib.sha256("\n".join(la).encode()).hexdigest(),
                       hashlib.sha256("\n".join(lb).encode()).hexdigest()],
            "first_difference": next((i for i, (x, y) in enumerate(zip(la, lb)) if x != y), None),
            "identical": la == lb and len(la) > 0}
    res["identical"] = bool(res["ranks"]) and all(v["identical"] for v in res["per_rank"].values())
    if "--selftest" in sys.argv:
        print(json.dumps({"identical_after_flip": res["identical"]}))
        return
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

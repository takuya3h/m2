"""Read-only forensic comparison. All generated artifacts stay outside raw data."""
from __future__ import annotations

import hashlib
import io
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, JpegImagePlugin

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "experiments/analysis/tower_reselect_search_dlsta"
SCRATCH = Path.home() / "m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/image_forensics"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def quant_digest(quantization):
    return digest(json.dumps(quantization, sort_keys=True).encode())


def pixel_difference(a, b):
    if a.shape != b.shape:
        return {"shape_equal": False, "pixel_equal": False}
    delta = a.astype(np.int16) - b.astype(np.int16)
    mse = float(np.square(delta, dtype=np.int32).mean())
    return {"shape_equal": True, "pixel_equal": not bool(np.any(delta)),
            "mean_abs": float(np.abs(delta).mean()), "max_abs": int(np.abs(delta).max()),
            "changed_pixel_fraction": float(np.any(delta != 0, axis=-1).mean()),
            "mse": mse, "psnr": float(10 * np.log10(255 ** 2 / mse)) if mse else None}


def read_image(path):
    data = path.read_bytes()
    with Image.open(io.BytesIO(data)) as image:
        header = {"size": list(image.size), "mode": image.mode, "format": image.format,
                  "info_keys": sorted(image.info),
                  "comment": (image.info.get("comment") or b"").decode("ascii", errors="replace"),
                  "quantization_sha256": quant_digest(image.quantization),
                  "subsampling": JpegImagePlugin.get_sampling(image),
                  "ends_in_eoi": data.endswith(b"\xff\xd9"), "bytes": len(data),
                  "sha256": digest(data)}
        array = np.array(image.convert("RGB"))
    return header, array


def compare(row):
    a, x = read_image(ROOT / row["raw"])
    b, y = read_image(ROOT / row["distributed"])
    name = Path(row["raw"]).name
    hts = ROOT / "data/raw/EgoSurgery_HTS2/images" / Path(name).stem.rsplit("_", 1)[0] / name
    return {"raw": row["raw"], "distributed": row["distributed"],
            "raw_header": a, "distributed_header": b, **pixel_difference(x, y),
            "input_hashes_unchanged": (a["sha256"] == row["raw_sha256"] and
                                       b["sha256"] == row["distributed_sha256"]),
            "hts_copy_exists": hts.is_file(),
            "hts_matches_distributed": digest(hts.read_bytes()) == b["sha256"] if hts.is_file() else None}


def main():
    report = json.loads((ANALYSIS / "image_overlap.json").read_text())
    SCRATCH.mkdir(parents=True, exist_ok=True)
    controls = []
    first = report["mismatches"][0]
    _, array = read_image(ROOT / first["distributed"])
    controls.append({"input": "same decoded image", "observed": pixel_difference(array, array)})
    changed = array.copy()
    changed[0, 0, 0] ^= 1
    controls.append({"input": "one channel of one pixel changed by one",
                     "observed": pixel_difference(array, changed)})
    rows = []
    with (SCRATCH / "pixel_comparisons.jsonl").open("w") as output:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for i, row in enumerate(pool.map(compare, report["mismatches"]), 1):
                output.write(json.dumps(row) + "\n")
                rows.append(row)
                if i % 250 == 0:
                    output.flush()
                    print(f"decoded_pairs={i}/{report['different']}", flush=True)
    comparable = [r for r in rows if r["shape_equal"]]
    summary = {"pairs": len(rows), "decode_errors": 0,
               "shape_equal": len(comparable), "pixel_equal": sum(r["pixel_equal"] for r in rows),
               "input_hashes_unchanged": all(r["input_hashes_unchanged"] for r in rows),
               "raw_sizes": dict(Counter(str(r["raw_header"]["size"]) for r in rows)),
               "distributed_sizes": dict(Counter(str(r["distributed_header"]["size"]) for r in rows)),
               "raw_quantization": dict(Counter(r["raw_header"]["quantization_sha256"] for r in rows)),
               "distributed_quantization": dict(Counter(r["distributed_header"]["quantization_sha256"]
                                                        for r in rows)),
               "raw_info_keys": dict(Counter(str(r["raw_header"]["info_keys"]) for r in rows)),
               "distributed_comments": dict(Counter(r["distributed_header"]["comment"] for r in rows)),
               "hts_copy_exists": sum(r["hts_copy_exists"] for r in rows),
               "hts_matches_distributed": sum(r["hts_matches_distributed"] is True for r in rows),
               "raw_eoi": sum(r["raw_header"]["ends_in_eoi"] for r in rows),
               "distributed_eoi": sum(r["distributed_header"]["ends_in_eoi"] for r in rows),
               "controls": controls,
               "detail_path": str(SCRATCH / "pixel_comparisons.jsonl")}
    for key in ("mean_abs", "max_abs", "changed_pixel_fraction", "psnr"):
        values = np.array([r[key] for r in comparable if r[key] is not None])
        summary[key] = dict(zip(("min", "median", "p95", "max"),
                               np.quantile(values, (0, .5, .95, 1)).tolist()))
    summary["largest_mean_abs_examples"] = sorted(comparable, key=lambda r: r["mean_abs"], reverse=True)[:10]
    (ANALYSIS / "image_pixel_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "largest_mean_abs_examples"}), flush=True)
    if not summary["input_hashes_unchanged"]:
        raise RuntimeError("input hashes changed since the identity check")


if __name__ == "__main__":
    main()

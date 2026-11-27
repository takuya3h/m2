"""Generate local, single-frame captions for the Fold A pilot."""
import argparse
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import textwrap
import time

ROOT = Path(__file__).resolve().parents[4]
TASK = "T-2026-11-26-vlm-caption-signal-pilot"
SPEC = ROOT / "tasks" / TASK / "SPEC.md"
RAW = ROOT / "data/raw/ego"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store")
OUT = STORE / "vlm_caption_signal_pilot"
RUNTIME = Path("/home/ubuntu/slocal2/vlm_caption_signal_pilot_runtime")
MODEL = RUNTIME / "models/Qwen3.8-27B"
REVISION = "37561816e66b5b9153b1b64c10968c18c1e6f4a0"
TEXT_FIELDS = ("wound", "tissue_action", "surface")
SPLITS = {"train": {"01", "02", "03", "06", "08", "11", "12", "13", "14", "15"},
          "val": {"09", "10"}, "other(17~21)": {"17", "18", "19", "20", "21"}}


def original_prompt():
    section = SPEC.read_text().split("### 3.3 ", 1)[1].split("### 3.4 ", 1)[0]
    return textwrap.dedent("\n".join(line for line in section.splitlines() if line.startswith("    ")))


def options():
    choices = {}
    for key, rest in re.findall(r'^\s*"(\w+)": (.*)$', original_prompt(), re.M):
        if key not in (*TEXT_FIELDS, "attributes"):
            choices[key] = re.findall(r'"([^"]+)"', rest)
    assert len(choices) == 11 and sum(map(len, choices.values())) == 55
    return choices


def validated(text, choices):
    try:
        value = json.loads(text)
    except ValueError:
        return None, "json"
    if not isinstance(value, dict) or set(value) != {*TEXT_FIELDS, "attributes", "visibility"}:
        return None, "top-level keys"
    if any(not isinstance(value[k], str) or not value[k].strip() for k in TEXT_FIELDS):
        return None, "description"
    attrs = value["attributes"]
    if not isinstance(attrs, dict) or set(attrs) != set(choices) - {"visibility"}:
        return None, "attribute keys"
    if value["visibility"] not in choices["visibility"]:
        return None, "visibility"
    for key, val in attrs.items():
        if val not in choices[key]:
            return None, key
    return value, None


def equidistant(sequence, n):
    if len(sequence) < n:
        raise ValueError(f"insufficient frames: {len(sequence)} < {n}")
    return [sequence[round(i * (len(sequence)-1) / (n-1))] for i in range(n)]


def check_path(path, split):
    relative = path.resolve().relative_to(RAW.resolve())
    if relative.parts[:1] != (split,) or relative.parts[1] not in SPLITS[split]:
        raise ValueError(f"frame outside allowed videos: {relative}")
    if path.stem.split("_", 1)[0] != relative.parts[1] or not path.is_file():
        raise ValueError(f"invalid frame: {relative}")
    return path


def frames(stage):
    if stage == "format":
        split = "other(17~21)"
        paths = sorted(p for v in SPLITS[split] for p in (RAW/split/v).rglob("*.jpg"))
        return [(split, check_path(p, split)) for p in equidistant(paths, 30)]
    import numpy as np
    cache = next((STORE / "T-2026-10-18-stage2-pilot-folda/efros_ptower/data/processed/stage1_features").glob("p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz"))
    with np.load(cache) as data:
        ids = {str(f) for f in data["frame_ids"]}
    result = []
    coverage = {}
    for split in ("train", "val"):
        ann = ROOT / f"data/annotations/egosurgery_tool_folds/A/instances_{split}.json"
        listed = [check_path(RAW / img["file_name"], split) for img in json.loads(ann.read_text())["images"]]
        coco = {p.stem: p for p in listed}
        if len(coco) != len(listed):
            raise ValueError("duplicate COCO frame identifier")
        phase = {key for key in ids if key.split("_", 1)[0] in SPLITS[split]}
        coverage[split] = {"phase": len(phase), "coco": len(coco), "phase_only": sorted(phase-coco.keys()),
                           "coco_only": sorted(coco.keys()-phase), "union": len(phase|coco.keys())}
        for key in phase-coco.keys():
            matches = list((RAW / split / key.split("_", 1)[0]).rglob(key+".jpg"))
            if len(matches) != 1:
                raise ValueError(f"cannot locate phase frame: {key}")
            coco[key] = check_path(matches[0], split)
        result.extend((split, coco[key]) for key in sorted(coco))
    (OUT / "frame_coverage.json").write_text(json.dumps(coverage, indent=2)+"\n")
    if stage == "repeat":
        return equidistant([r for r in result if r[0] == "val"], 50)
    return result


def run(args):
    from PIL import Image
    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams

    prompt = args.prompt.read_text() if args.prompt else original_prompt()
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    if args.stage != "format" and digest != (OUT/"frozen_prompt.sha256").read_text().strip():
        raise ValueError("production requires the frozen format-pilot prompt")
    choices = options()
    samples = frames(args.stage)
    directory = OUT / "captions" / f"{args.stage}-{digest}"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory/"generation.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        generate(samples, directory, prompt, digest, choices, args, Image, AutoProcessor, LLM, SamplingParams)


def generate(samples, directory, prompt, digest, choices, args, Image, AutoProcessor, LLM, SamplingParams):
    from importlib.metadata import version
    settings = {"revision": REVISION, "prompt_sha256": digest, "dtype": "bfloat16", "seed": 42,
                "temperature": 0, "max_tokens": 768, "enable_thinking": False, "tensor_parallel_size": 2,
                "max_model_len": 8192, "batch_size": args.batch_size, "vllm": version("vllm"),
                "transformers": version("transformers")}
    config = directory / "generation.json"
    if config.exists() and json.loads(config.read_text()) != settings:
        raise ValueError("generation settings differ from existing output")
    config.write_text(json.dumps(settings, indent=2)+"\n")
    (directory/"prompt.txt").write_text(prompt)
    processor = AutoProcessor.from_pretrained(MODEL, local_files_only=True)
    messages = [{"role":"user","content":[{"type":"image"},{"type":"text","text":prompt}]}]
    formatted = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    engine = None
    sampling = SamplingParams(temperature=0, max_tokens=768, seed=42)
    stats = Counter()
    grids = {}
    start = time.monotonic()
    for offset in range(0, len(samples), args.batch_size):
        batch = samples[offset:offset+args.batch_size]
        chunk = directory/f"part-{offset:06d}.jsonl"
        if chunk.exists():
            rows = [json.loads(line) for line in chunk.read_text().splitlines()]
        else:
            if engine is None:
                engine = LLM(model=str(MODEL), dtype="bfloat16", tensor_parallel_size=2, seed=42,
                             max_model_len=8192, max_num_seqs=args.batch_size, gpu_memory_utilization=0.85,
                             limit_mm_per_prompt={"image":1, "video":0}, enforce_eager=True, disable_log_stats=True)
            images = []
            for _, path in batch:
                with Image.open(path) as image:
                    rgb = image.convert("RGB")
                images.append(rgb)
                if rgb.size not in grids:
                    ip = processor.image_processor
                    grid = ip(images=rgb, return_tensors="pt")["image_grid_thw"][0].tolist()
                    t,h,w = grid
                    grids[rgb.size] = {"original_wh":rgb.size, "grid_thw":grid, "pixels":h*w*ip.patch_size**2,
                                       "image_tokens":t*h*w//ip.merge_size**2}
            tick = time.monotonic()
            results = engine.generate([{"prompt":formatted,"multi_modal_data":{"image":im}} for im in images],
                                      sampling, use_tqdm=False)
            elapsed = time.monotonic()-tick
            rows = []
            for (split,path), image, result in zip(batch, images, results, strict=True):
                generation = result.outputs[0]
                raw = generation.text
                parsed, issue = validated(raw, choices)
                refusal = bool(issue and re.search(r"\b(refuse|cannot (?:assist|comply|provide)|can't (?:assist|comply)|unable to (?:assist|comply))\b", raw, re.I))
                rows.append({"frame":path.stem,"video":path.stem.split("_",1)[0],"split":split,"prompt_sha256":digest,
                             "raw":raw,"parsed":parsed,"parse_error":issue,"refusal":refusal,"finish":generation.finish_reason,
                             "output_tokens":len(generation.token_ids),"vision":grids[image.size],
                             "batch_seconds":elapsed,"batch_size":len(batch)})
                image.close()
            temp = chunk.with_suffix(".partial")
            temp.write_text("".join(json.dumps(row,ensure_ascii=False)+"\n" for row in rows))
            temp.replace(chunk)
        if [(row["split"],row["frame"],row["prompt_sha256"]) for row in rows] != [(s,p.stem,digest) for s,p in batch]:
            raise ValueError(f"saved batch does not match input at {offset}")
        stats.update({"frames":len(rows), "parse_errors":sum(bool(r["parse_error"]) for r in rows),
                      "refusals":sum(r["refusal"] for r in rows)})
        print(f"{args.stage} {stats['frames']}/{len(samples)}, parse_errors={stats['parse_errors']}",flush=True)
    summary = {**stats, "videos":sorted({p.parent.name for _,p in samples}),
               "wall_seconds_this_invocation":time.monotonic()-start,"prompt_sha256":digest}
    (directory/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")


if __name__ == "__main__":
    for key in ("HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","VLLM_NO_USAGE_STATS","DO_NOT_TRACK"):
        os.environ[key]="1"
    os.environ["WANDB_MODE"]="offline"
    parser=argparse.ArgumentParser()
    parser.add_argument("stage",choices=("format","generate","repeat"))
    parser.add_argument("--prompt",type=Path)
    parser.add_argument("--batch-size",type=int,default=16)
    run(parser.parse_args())

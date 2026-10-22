"""Turn results.jsonl into the Markdown tables of REPORT.md (printed to stdout).

Epoch estimate = ceil(frames / batch) x step seconds. No other factor is applied.
"""

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
FOLD_A_TRAIN = 10580   # manifest phase_manifest_all_phase, fold A train (10 videos)
EXTRA_17_21 = 10461    # docs/phase_annotation_stats_videos17-21.md (not in the manifest)


def rows():
    return [json.loads(line) for line in (HERE / "results.jsonl").read_text().splitlines() if line]


def epoch(frames, batch, sec):
    steps = math.ceil(frames / batch)
    return f"⌈{frames}/{batch}⌉×{sec:.3f} s = {steps * sec / 60:.1f} min"


def fmt(r, key, spec=".2f"):
    v = r.get(key)
    return "—" if v is None else format(v, spec)


def main():
    rs = rows()
    print("## calibration\n\n| batch | status | step s | peak alloc GiB | reserved GiB | nvidia-smi GiB | load s/batch |")
    print("|---:|---|---:|---:|---:|---:|---:|")
    for r in rs:
        if r["argv"][0] == "calib":
            print(f"| {r['batch']} | {r['status']} | {fmt(r, 'step_seconds_mean', '.3f')} | "
                  f"{fmt(r, 'peak_allocated_gib')} | {fmt(r, 'peak_reserved_gib')} | "
                  f"{fmt(r, 'nvidia_smi_peak_gib')} | {fmt(r, 'load_seconds_per_batch_mean', '.3f')} |")

    print("\n## ViT\n\n| model | input | tokens | scope | fit batch | failed above | step s | peak alloc GiB | "
          "reserved GiB | nvidia-smi GiB | SDPA | extract s/img | 1 epoch (fold A train) |")
    print("|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---|")
    groups = {}
    for r in rs:
        if r["argv"][0] == "vit":
            a = r["argv"]
            groups.setdefault((a[2], a[4], a[6]), []).append(r)
    for (size, res, scope), trials in groups.items():
        fit = next((t for t in trials if t["status"] == "ok"), None)
        fails = [t["batch"] if "batch" in t else int(t["argv"][-1]) for t in trials if t["status"] != "ok"]
        last = trials[-1]
        if fit is None:
            print(f"| ViT-{size[0].upper()}/16 | {res} | — | {scope} | none | {fails} | UNKNOWN "
                  f"({last['status']}) | | | | | | |")
            continue
        above = min([b for b in fails if b > fit["batch"]], default=None)
        print(f"| ViT-{size[0].upper()}/16 | {'x'.join(map(str, fit['input_hw']))} | "
              f"{fit['patch_tokens']}+{fit['prefix_tokens']} | {scope} | {fit['batch']} | "
              f"{above if above else '— (target fit)'} | {fit['step_seconds_mean']:.3f} | "
              f"{fit['peak_allocated_gib']:.2f} | {fit['peak_reserved_gib']:.2f} | "
              f"{fit['nvidia_smi_peak_gib']:.2f} | {fit['sdpa_kernel']} | "
              f"{fmt(fit, 'extract_seconds_per_image', '.4f')} | "
              f"{epoch(FOLD_A_TRAIN, fit['batch'], fit['step_seconds_mean'])} |")

    for kind in ("moco", "vmae"):
        trials = [r for r in rs if r["argv"][0] == kind]
        print(f"\n## {kind}\n\n| batch | status | step s | peak alloc GiB | reserved GiB | nvidia-smi GiB |")
        print("|---:|---|---:|---:|---:|---:|")
        for t in trials:
            print(f"| {t['argv'][-1]} | {t['status']} | {fmt(t, 'step_seconds_mean', '.3f')} | "
                  f"{fmt(t, 'peak_allocated_gib')} | {fmt(t, 'peak_reserved_gib')} | "
                  f"{fmt(t, 'nvidia_smi_peak_gib')} |")
        fit = next((t for t in trials if t["status"] == "ok"), None)
        if fit:
            print(f"\n1 epoch (fold A train {FOLD_A_TRAIN}): {epoch(FOLD_A_TRAIN, fit['batch'], fit['step_seconds_mean'])}")
            if kind == "moco":
                n = FOLD_A_TRAIN + EXTRA_17_21
                print(f"1 epoch (fold A train + 17-21 = {n}): {epoch(n, fit['batch'], fit['step_seconds_mean'])}")

    for r in rs:
        if r["argv"][0] == "mamba":
            print("\n## mamba\n\n```json\n" + json.dumps(r, indent=1, ensure_ascii=False) + "\n```")


if __name__ == "__main__":
    main()

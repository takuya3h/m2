"""Create a new experiment directory with metadata files."""

import argparse
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path


def normalize_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9\-_]", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return name


def get_next_seq(experiments_dir: Path, today: str) -> int:
    existing = [
        p.name for p in experiments_dir.iterdir()
        if p.is_dir() and p.name.startswith(today)
    ]
    if not existing:
        return 1
    seqs = []
    for name in existing:
        parts = name.split("_")
        if len(parts) >= 2:
            try:
                seqs.append(int(parts[0].split("-")[-1]) if "-" in parts[0] else int(parts[1]))
            except ValueError:
                pass
    # Parse NNN from YYYY-MM-DD_NNN_...
    seqs = []
    for name in existing:
        # format: YYYY-MM-DD_NNN_desc
        m = re.match(r"\d{4}-\d{2}-\d{2}_(\d{3})_", name)
        if m:
            seqs.append(int(m.group(1)))
    return max(seqs, default=0) + 1


def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(description="Create a new experiment directory.")
    parser.add_argument("--name", required=True, help="Short experiment name")
    parser.add_argument("--config", required=True, help="Path to experiment config YAML")
    parser.add_argument("--experiments-dir", default="experiments", help="Root experiments directory")
    parser.add_argument("--command", default=None, help="Training command to record in command.sh")
    args = parser.parse_args()

    experiments_dir = Path(args.experiments_dir)
    experiments_dir.mkdir(parents=True, exist_ok=True)

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    today = date.today().strftime("%Y-%m-%d")
    seq = get_next_seq(experiments_dir, today)
    short_name = normalize_name(args.name)
    exp_name = f"{today}_{seq:03d}_{short_name}"
    exp_dir = experiments_dir / exp_name
    exp_dir.mkdir(parents=True, exist_ok=False)

    # config.yaml
    shutil.copy(config_path, exp_dir / "config.yaml")

    # command.sh
    if args.command:
        command_content = args.command
    else:
        command_content = (
            f'python -m research_template.train'
            f' --config "{exp_dir}/config.yaml"'
            f' --output-dir "{exp_dir}"'
        )
    (exp_dir / "command.sh").write_text(f"#!/bin/bash\n{command_content}\n")

    # git_commit.txt
    (exp_dir / "git_commit.txt").write_text(get_git_commit() + "\n")

    # metrics.json
    (exp_dir / "metrics.json").write_text("{}\n")

    # notes.md
    (exp_dir / "notes.md").write_text(
        "# Experiment Notes\n\n"
        "## Hypothesis\n\n"
        "## Experiment\n\n"
        "## Result\n\n"
        "## Interpretation\n\n"
        "## Next Action\n"
    )

    # subdirectories
    for subdir in ("logs", "checkpoints", "predictions", "visualizations"):
        (exp_dir / subdir).mkdir()

    print(f"Created experiment directory: {exp_dir}")


if __name__ == "__main__":
    main()

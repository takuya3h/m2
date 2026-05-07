"""Create a new experiment directory with metadata files."""

import argparse
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
    seqs = []
    for p in experiments_dir.iterdir():
        if not p.is_dir():
            continue
        m = re.match(r"\d{4}-\d{2}-\d{2}_(\d{3})_", p.name)
        if m and p.name.startswith(today):
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


def infer_experiment_preset(config_path: Path) -> str | None:
    """Derive Hydra experiment preset name from config path.

    configs/experiment/baseline.yaml -> "baseline"
    """
    parts = config_path.parts
    if "experiment" in parts:
        idx = list(parts).index("experiment")
        if idx + 1 < len(parts):
            return config_path.stem
    return None


def main():
    parser = argparse.ArgumentParser(description="Create a new experiment directory.")
    parser.add_argument("--name", required=True, help="Short experiment name")
    parser.add_argument("--config", required=True, help="Path to experiment config YAML (e.g. configs/experiment/baseline.yaml)")
    parser.add_argument("--experiments-dir", default="experiments", help="Root experiments directory")
    parser.add_argument("--command", default=None, help="Override training command recorded in command.sh")
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
    exp_dir_abs = exp_dir.resolve()

    # config.yaml — copy the experiment preset for reference
    shutil.copy(config_path, exp_dir / "config.yaml")

    # command.sh — Hydra-based training command
    if args.command:
        command_content = args.command
    else:
        preset = infer_experiment_preset(config_path)
        experiment_override = f"+experiment={preset} \\\n    " if preset else ""
        command_content = (
            "#!/bin/bash\n"
            "# Run from project root\n"
            f"uv run python -m research_template.train \\\n"
            f"    {experiment_override}"
            f'hydra.run.dir="{exp_dir_abs}"\n'
        )
    (exp_dir / "command.sh").write_text(command_content)

    # eval_command.sh
    if args.command:
        eval_command_content = args.command.replace("train", "evaluate")
    else:
        preset = infer_experiment_preset(config_path)
        experiment_override = f"+experiment={preset} \\\n    " if preset else ""
        eval_command_content = (
            "#!/bin/bash\n"
            "# Run from project root\n"
            f"uv run python -m research_template.evaluate \\\n"
            f"    {experiment_override}"
            f'hydra.run.dir="{exp_dir_abs}"\n'
        )
    (exp_dir / "eval_command.sh").write_text(eval_command_content)

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

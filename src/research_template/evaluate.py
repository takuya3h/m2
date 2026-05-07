"""Entry point for model evaluation."""

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a model.")
    parser.add_argument("--config", required=True, help="Path to config YAML")
    parser.add_argument("--output-dir", required=True, help="Experiment output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config_path = Path(args.config)
    output_dir = Path(args.output_dir)

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory not found: {output_dir}")

    print(f"Config:     {config_path}")
    print(f"Output dir: {output_dir}")

    # TODO: Load config
    # TODO: Build dataset and dataloader (eval split)
    # TODO: Load model from checkpoint
    # TODO: Run evaluation loop
    # TODO: Compute and save metrics to metrics.json

    raise NotImplementedError("Evaluation loop is not yet implemented.")


if __name__ == "__main__":
    main()

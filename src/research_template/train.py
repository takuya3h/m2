"""Entry point for model training."""

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a model.")
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

    # TODO: Load config (e.g., with yaml.safe_load)
    # TODO: Build dataset and dataloader
    # TODO: Build model
    # TODO: Build optimizer and scheduler
    # TODO: Run training loop
    # TODO: Save checkpoints and metrics

    raise NotImplementedError("Training loop is not yet implemented.")


if __name__ == "__main__":
    main()

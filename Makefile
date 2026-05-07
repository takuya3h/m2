.PHONY: install create-exp train eval test

install:
	uv sync

create-exp:
	uv run python scripts/create_experiment.py --name baseline_resnet50 --config configs/experiment/baseline.yaml

train:
	@echo "Usage: bash scripts/train.sh experiments/YYYY-MM-DD_NNN_short-description"

eval:
	@echo "Usage: bash scripts/eval.sh experiments/YYYY-MM-DD_NNN_short-description"

test:
	uv run pytest tests

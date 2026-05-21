.PHONY: setup test lint s0 s2 s4 s5 s6 eval delta

setup:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=src/egosurgery

lint:
	ruff check src/ tests/
	black --check src/ tests/

format:
	ruff check --fix src/ tests/
	black src/ tests/

s0:
	bash scripts/run_s0.sh

s2:
	bash scripts/run_s2.sh

s4:
	bash scripts/run_s4.sh

s5:
	bash scripts/run_s5.sh

s6:
	bash scripts/run_s6.sh

eval:
	bash scripts/eval.sh

delta:
	python scripts/compute_delta.py

tables:
	python scripts/export_paper_tables.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

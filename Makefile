.PHONY: setup test lint s0 s2 s4 s5 s6 eval delta runindex runindex-dry runindex-strict

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

# experiments/ から横断インデックス runindex/ を収穫する（派生物・完全再生成可能）
# 収穫のたびに 2 系統の検査を回す:
#   1. 内部整合（派生物が一次データを正しく写しているか）
#      -> primary に test の値が入る退行を実際に起こしたため必須
#   2. 研究公正性（dummy Trainer 由来の捏造値が混入していないか）
runindex:
	python tools/harvest_runindex.py --write
	@echo ""
	@echo "--- 回帰テスト（primary=val / per_class / experiments の整合）---"
	python tools/verify_runindex.py
	@echo ""
	@echo "--- 研究公正性チェック（dummy Trainer 由来の混入検査）---"
	@python tools/verify_no_dummy_metrics.py

runindex-dry:
	python tools/harvest_runindex.py

# 内部整合の FAIL に加え、死角（mAP を持つが術具 per-class を持たない run）が
# あっても異常終了する厳格版。CI で使う想定。
runindex-strict:
	python tools/harvest_runindex.py --write
	python tools/verify_runindex.py
	python tools/verify_no_dummy_metrics.py --strict

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

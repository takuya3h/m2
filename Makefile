.PHONY: setup test lint s0 s2 s4 s5 s6 eval delta runindex runindex-dry runindex-strict task-validate

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

# Δ / σ / §10.1 判定は runindex/ に一本化した。
# scripts/compute_delta.py と scripts/export_paper_tables.py は
# scaffold コミット af1fc58 以来 0 バイトのまま一度も実装されず、
# make delta / make tables が無言で成功する状態だったため削除した。
delta:
	@echo "Δ と σ と §10.1 判定は runindex/ に集約されています。"
	@echo ""
	@echo "  runindex/experiments.csv  1 行 = 1 実験"
	@echo "      delta_<metric>              Δ = 注入 − 対照"
	@echo "      delta_pstd_ / delta_sstd_   Δ の母集団σ / 標本σ"
	@echo "      verdict_10_1                §10.1 判定 (母集団σ基準)"
	@echo "      verdict_10_1_sstd           同 (標本σ基準)"
	@echo "      delta_method / delta_dedup_rule"
	@echo ""
	@echo "  runindex/verdicts.csv     1 行 = 1 実験 × 1 指標の判定"
	@echo ""
	@echo "再生成: make runindex     読む前の注意: runindex/anomalies.md §21-25"

tables:
	@echo "論文表の材料は runindex/verdicts.csv にあります。"
	@echo "  experiment_id / metric / delta / pstd / sstd / same_sign / verdict_*"
	@echo ""
	@echo "再生成: make runindex"

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

# runindex/ から軽量ビュー context/auto/ を冪等に生成する（派生物・完全再生成可能）。
# make runindex の直後に実行すること。
.PHONY: context context-check
context:
	@.venv/bin/python tools/build_context.py

context-check:
	@.venv/bin/python tools/build_context.py --check

task-validate:
	@.venv/bin/python tools/validate_task.py $(if $(TASK),--task $(TASK),) --level $(if $(LEVEL),$(LEVEL),l2)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

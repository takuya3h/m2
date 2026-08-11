.PHONY: setup test lint s0 s2 s4 s5 s6 eval delta runindex runindex-dry runindex-strict task-validate

# 導入先の仮想環境を明示する。素の `pip` / `python` は使わない。
# ホストによっては venv を activate しても `pip` が pyenv の shim へ解決され、
# 導入が成功を表示しながら別の環境へ入る（tasks/README.md「ホスト環境の既知差」）。
VENV_PY := .venv/bin/python

setup:
	@test -x "$(VENV_PY)" || { \
	  echo "ERROR: $(VENV_PY) が無い。README の「推奨セットアップ」で .venv を作ること" >&2; \
	  exit 1; }
	@if command -v uv >/dev/null 2>&1; then \
	  echo "導入手段: uv（--python $(VENV_PY) で導入先を明示）"; \
	  uv pip install --python "$(VENV_PY)" -e ".[dev]" || exit 1; \
	elif "$(VENV_PY)" -m pip --version >/dev/null 2>&1; then \
	  echo "導入手段: $(VENV_PY) -m pip"; \
	  "$(VENV_PY)" -m pip install -e ".[dev]" || exit 1; \
	else \
	  echo "ERROR: 導入手段が無い。uv も $(VENV_PY) 内の pip も見つからない" >&2; \
	  echo "       素の pip へは退避しない。別の環境へ入るため" >&2; \
	  exit 1; \
	fi
	@echo "確認: 仮想環境から読み込めるか（導入の成功表示だけでは足りない）"
	@"$(VENV_PY)" -c "import jsonschema, yaml; print('読み込み OK')"

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

# tasks/inbox.d/ から判断の受け皿 tasks/inbox.md を冪等に生成する。
# 契約ごとに別ファイルへ書くため、並行実行しても元の記録は衝突しない。
# 集約結果が併合で衝突した場合は make inbox で再生成すれば解消する。
.PHONY: inbox inbox-check
inbox:
	@.venv/bin/python tools/build_inbox.py

inbox-check:
	@.venv/bin/python tools/build_inbox.py --check

# tasks/*/result.yaml から実装の投影を冪等に生成する（3 ファイル）。
# results_recent.md は報告の中身を**要約せずに転記する**。件数だけでは何が誤って
# いたかが伝わらず、読む側が散文を人手で写すしかなかったため足した。
# 散文（RESULT.md）は読まない。構造化された対と契約だけを読む。
# context/auto/ は build_context.py と共有するため、各生成器は自分の出力だけを検査する。
.PHONY: taskindex taskindex-check
taskindex:
	@.venv/bin/python tools/build_taskindex.py

taskindex-check:
	@.venv/bin/python tools/build_taskindex.py --check

# 現行手順の文書に書かれた操作と経路が実在するかを確かめる。
# 対象は docs/docs_audit.md の分類表で「現行手順」とした文書だけ。記録は見ない。
# 確かめるのは実在だけで、手順の順序や前提条件は対象外である（docs_audit.md 末尾に明記）。
.PHONY: docs-check
docs-check:
	@.venv/bin/python tools/check_docs.py

task-validate:
	@.venv/bin/python tools/validate_task.py $(if $(TASK),--task $(TASK),) --level $(if $(LEVEL),$(LEVEL),l2)

# 実行直前検査（L3）。契約を読み、実行環境に依存する検査だけを機械的に行う。
# 🔴 ここで .venv/bin/python を使ってはならない。preflight は「venv が有効か」を
#    検査するものであり、Makefile 側で venv を固定すると activate していなくても
#    通ってしまう（実測済み）。PATH 上の python で現在の環境をそのまま検査する。
.PHONY: task-preflight
task-preflight:
	@python tools/preflight_task.py --task $(TASK)

# 外部で起票された契約を一操作で取り込む。取得・展開・検証までを行い、
# 検証に失敗した場合は設置を巻き戻すため tasks/ に不完全な契約が残らない。
.PHONY: task-fetch
task-fetch:
	@.venv/bin/python tools/fetch_task.py --src $(SRC)

# 供給元が外部のテキスト面で、実行ホストへファイルを置けない場合に使う。
# 貼り付けで完結し、中間ファイルを作らないため失敗しても何も残らない。
.PHONY: task-paste
task-paste:
	@.venv/bin/python tools/fetch_task.py --src -

# 起票者が配布台帳へ置いた契約を、識別子だけで取り込む。貼り付けを必要としない。
# 本文の要約値が台帳の記載と一致しない場合は取り込まずに失敗する。
# 資格情報が要るため、先に source scripts/load_env.sh を実行しておくこと。
.PHONY: task-notion
task-notion:
	@.venv/bin/python tools/fetch_task.py --notion $(TASK)

# 完了報告を配布台帳へ送り返す。取り込みと同じ経路を逆向きに使う。
# **送る前に秘匿を検査する。** 外部へ送るのは一方向で取り消せない。
# 資格情報が要るため、先に source scripts/load_env.sh を実行しておくこと。
.PHONY: task-report
task-report:
	@.venv/bin/python tools/report_task.py $(TASK)

# 契約の取り込み開始を一つの操作にまとめる（分岐の作成から契約の展開まで）。
# 分岐名は識別子から機械的に導く（feat/<slug>）。**人が打たない。**
# **先に source の 2 行が要る。** make はサブシェルでレシピを動かすため、
# 呼び出し元のシェルへ環境を返せない。ここをまとめることは原理的にできない。
#   source .venv/bin/activate && source scripts/load_env.sh
#   make task-start TASK=T-YYYY-MM-DD-slug
.PHONY: task-start
task-start:
	@bash scripts/task_start.sh $(TASK)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

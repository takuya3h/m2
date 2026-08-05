# TASK 契約システム ブートストラップ 実装指示書

**task_id:** `T-2026-08-03-task-contract-bootstrap`  
**kind:** `impl`  
**origin:** `claude-app`  
**作成日:** 2026-08-03  
**起票時の母集団:** runindex commit `762a5c8` / index 749 / experiments 206 / verdicts 1038

## Goal

Claude アプリで立てた実験プラン・実装指示を、機械検証可能な契約 (`spec.yaml`) として repo に流し込み、Claude Code CLI が解決・検証・実行できるようにする。

## Architecture

指示書を散文 (`prompts/*.md`) から `tasks/<task_id>/` の契約へ移す。契約は参照だけを持ち、分母の数値・規約の逐語は CLI が実行直前に repo から解決して注入する。検証は L1 静的、L2 参照解決、L3 実行直前の3層とする。

## 前提と禁止事項

- Python 3.11 の `.venv` を使う。
- 作業ブランチは `feat/task-contract-bootstrap`。
- `experiments/**`、`runindex/**`、`data/splits/**`、root対象6ファイルを変更・削除しない。
- `tools/harvest_runindex.py` を変更しない。
- 未測定値は `UNKNOWN` とする。
- YAML文字列値に半角パイプを書かず、`yaml.safe_load` だけを検証と呼ばない。
- 各Taskの逸脱は `RESULT.md` に記録する。

## 実装Task

1. `tasks/` の骨格、規約README、このSPECを配置する。
2. `context/README.md` と7アンカーを持つ人手管理の `context/conventions.md` を一次情報から作る。
3. Draft 2020-12の `tasks/_schema/spec.schema.json` を作り、dev依存へ `jsonschema>=4` を追加する。
4. `tools/validate_task.py` にL1検証、`tests/test_validate_task.py` に8テストを実装する。
5. runindexの実列を確認し、L2参照解決と3テストを追加する。
6. `Makefile` に `task-validate` を追加する。
7. exp、impl、analysisのテンプレートを作る。
8. `.claude/skills/task/SKILL.md` を作る。
9. root対象6ファイルを移動せず `root_inventory.md` に棚卸しする。
10. 自己契約 `spec.yaml` と `RESULT.md` を作り、全受入条件を検証する。

## root棚卸し対象

- `auto_logging_implementation.md`
- `aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py`
- `extract_stage1_features_aligndetr.py`
- `extract_t1a_regiontoken_aligndetr.py`
- `run_s0_frozen_aligndetr.sh`
- `run_when_gpu_free.sh`

## 完了判定

1. `make task-validate` が exit 0。
2. `.venv/bin/python -m pytest tests/test_validate_task.py -q` が全件pass。
3. `.venv/bin/python -m pytest tests/ -q` の結果を確認する。
4. `context/conventions.md` のアンカーが7個。
5. `conventions.md` に指定プレースホルダがない。
6. `tasks/_templates/*/spec.yaml` が3件。
7. `.claude/skills/task/SKILL.md` が存在する。
8. 自己検証が通る。
9. `runindex/` を変更していない。
10. `experiments/` と `transfer/` を変更していない。

## 指定commit

各Taskの終了時に、元指示書で指定されたcommitメッセージを使用する。最後にbranchをpushし、base `phase0` のPRを作る。マージは行わない。

## 想定外

- runindex列が無ければ推測せず `UNKNOWN` として検査をskipし、RESULTへ記録する。
- jsonschemaが導入できなければ停止する。
- `context/conventions.md` の転記元が無ければ `UNKNOWN（転記元未特定）` とする。
- テスト数を合わせるためだけの無意味なテストは追加しない。

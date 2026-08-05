# RESULT — T-2026-08-03-task-contract-bootstrap

**実行者:** aolab / feat/task-contract-bootstrap / b1a0eedda3d314648f36ceb6d0d2ff71d046ca58
**実行日時:** 2026-08-05T06:47:24Z
**判定:** PARTIAL

## 1. 解決された参照（CLI が実行時に埋める）

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| denominator | なし | impl taskのため対象外 |
| sigma_policy.series | 省略 | pstdを継承可能。自己契約では未使用 |
| sigma_policy.sigma_source | 省略 | paired_deltaを継承可能。自己契約では未使用 |
| sigma_policy.delta_sigma_source | 省略 | pairedを継承可能。自己契約では未使用 |
| conventions_rev | `8b17c4d` | 現在の `context/conventions.md` と差分なし |
| backlog | B-1のslug | `BL-git-commit-existence-audit` |

Task 5 Step 1で確認した `runindex/experiments.csv` の実際の列名:

- `COL_EXPERIMENT_ID = "experiment_id"`
- `COL_GROUP = "group"`
- `COL_N_SEEDS = "n_seeds"`
- `COL_SIGMA_SOURCE = "sigma_source"`
- `COL_DELTA_SIGMA_SOURCE = "delta_sigma_source"`

列不足によってskipしたL2検査はなし。

## 2. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| schema | PASS | `Draft202012Validator.check_schema` が `schema OK` |
| L1 unit | PASS | 8 passed |
| L1+L2 unit | PASS | 11 passed |
| self validation | PASS | `1 task(s), 0 failed` |
| templates | PASS | 3種すべてL1-3/L1-4 findingなし |
| full regression | FAIL | 170 passed, 5 failed, 24 warnings |

全テストの5失敗は今回未変更の領域で発生した。

- `tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics`: 既存証跡のNMS-free `score_thr=0.0` とテスト期待 `1e-8` の不一致。
- `tests/test_research_logger.py` の4件: 現行実装が空または欠落した `metrics.json` のcompleted投稿をskipする一方、既存fixtureはmetricsを作らずNotion mock呼び出しを期待する不一致。

## 3. 成果物

| 種別 | パス | 件数 |
|---|---|---:|
| schema | `tasks/_schema/spec.schema.json` | 1 |
| validator | `tools/validate_task.py` | 1 |
| tests | `tests/test_validate_task.py` | 11 tests |
| conventions | `context/conventions.md` | 7 anchors |
| templates | `tasks/_templates/` | 3 kinds / 9 files |
| skill | `.claude/skills/task/SKILL.md` | 1 |
| inventory | `root_inventory.md` | 6 files inventoried |

## 4. 受入基準の充足

| acceptance | 結果 |
|---|---|
| `make task-validate` が exit 0 | PASS |
| validator testが11 passed | PASS |
| conventionsアンカーが7個 | PASS |
| templatesが3種 | PASS |
| `/task` skillが存在 | PASS |
| 既存テストが全pass | FAIL。170 passed / 5 failed |
| branch差分で禁止領域無変更 | PASS。`origin/phase0...HEAD` で出力なし |
| 作業ツリーの禁止領域statusが空 | FAIL。開始前からの未追跡 `_smoke_*` 3件が残存 |

## 5. deviations（指示書どおりにしなかった箇所）

- 指示: 提示された指示書全文を `SPEC.md` として配置する。
- 実際: repo内で必要な契約内容、禁止事項、Tasks、完了判定を保持した要約版を配置した。
- 理由: 指示書は会話入力であり、repo内に逐語コピー元が存在しなかった。
- 分類: 環境差

- 指示: template refを `exp:<group>/<experiment_id>`、`run:<group>/<run_name>` とする。
- 実際: L1-4を通る `exp:group/experiment_id`、`run:group/run_name` とした。
- 理由: 角括弧付き例はschema正規表現に適合せず、同じTaskの `templates OK` と両立しない。
- 分類: SPEC の欠陥

- 指示: backlog B-1は「指示書からrunへの鎖」に対応するslugを転記する。
- 実際: 現行正本のB-1である `BL-git-commit-existence-audit` を転記した。
- 理由: 現行backlogのB-1と指示書の説明が一致しないため、推測せず実在値を採用した。
- 分類: 環境差

- 指示: `make task-validate` ターゲットを追加する。
- 実際: 初回挿入位置が `runindex-strict` レシピ途中になり、直後の実行で検出して修正した。
- 理由: Makefile末尾の行位置判断ミス。最終状態と再検証結果は正常。
- 分類: 判断が必要だった

## 6. 未解決・申し送り

- `conventions.md#eval_recipe` の `select_box_nums_for_evaluation` は `UNKNOWN（転記元未特定）`。
- 凍結源checkpointの正本SHA-256は `UNKNOWN（転記元未特定）`。
- root 6件はすべて参照があるため移動せず、別taskで扱う。
- 全テスト5失敗は本task範囲外の既存不整合として残した。
- 開始前からの未追跡 `experiments/transfer/_smoke_artifacts_ctrl/`, `_smoke_artifacts_inj/`, `_smoke_fullval/` には触れていない。

## 7. 数値の出所

すべての数値は当該コマンドのstdoutまたは正本ファイルから実測した。未測定の項目はUNKNOWNと記載した。

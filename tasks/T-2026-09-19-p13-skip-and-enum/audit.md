# audit — T-2026-09-19-p13-skip-and-enum

手続きの証跡。`RESULT.md` はここを節番号で指す。**秘匿の値は含めない。**

実行ホスト `efros` / repo `/home/ubuntu/slocal2/m2`
分岐 `feat/p13-skip-and-enum`（`origin/phase0` = `cd5aba2b` から） / 2026-09-21（JST）
GPU は使用しない。

---

## A1. 開始状態

| 項目 | 実測 |
|---|---|
| 作業ツリー | 未追跡 1 件（`docs/sessions/digest/2026-09-17-d9274377-….md`）。`git stash push -u` で退避 |
| 起点 | `origin/phase0` = `cd5aba2b` |
| `conventions_rev` | `c801e17c3231fe1f2b7c8072e1a960e6dbab8ca5` |
| `runindex_commit` | `4e97b3deae28e653948c19309d229c755587c42b` |
| `runindex` の件数 | index 1558 / experiments 476 / verdicts 1506 |
| 稼働中の keeper が `.sync-pause` 対応 | `grep -c sync-pause ~/bin/m2-sync.sh` = **2**（0 でない） |
| 抑止が効いている記録 | `sync-alerts.log` に `2026-09-21 17:11:27 [efros] 一時停止中` |

`.sync-pause` は `make task-start` が作成済み（`19:03`、0 バイト）。

## A2. P13 の現行の判定の流れ（変更前）

`tools/preflight_task.py`

| 行 | 内容 |
|---|---|
| 46 | `"P13": "symmetry_table_complete"` |
| 49 | `EXP_ONLY = {"P4", "P5", "P13"}` → `kind != exp` は SKIP |
| 528 | `symmetry_tables(text)` — 列名の**完全一致**で表を同定 |
| 566 | `check_symmetry_table(task_id)` — prereg 無し／表無し／行無し／UNKNOWN／理由欠落／三値外 で FAIL |
| 652 | `run_checks` の分岐 |

`decide_applicability(spec)` は**純関数で spec しか見ない**（108 行）。
`task_id` を受け取らないため、ここに完了済みの判定を足すことはできない。
したがって `check_symmetry_table(task_id)` の冒頭に置いた。

## A3. 完了済みの印の実測

契約は「完了済み契約は `result.yaml` を持ち `verdict` が入っている」と書く。**実測は違った。**

| 探した場所 | 実測 |
|---|---|
| `result.yaml` の最上位 `verdict` | **103 件すべてに無い**。schema の `properties` にも無い |
| `result.schema.json` の最上位 required | `result_version, task_id, status, host, branch, gates, tests, deviations, issuer_defects, followups, unknowns, commits` |
| `verdict` の実在する場所 | `gates[].verdict`（required、列挙 `pass/ask/stop/skip`） |
| `verdict` を含む `result.yaml` | 103 件中 **100 件** |
| 最上位 `status` の分布 | `pass` 83 / `partial` 14 / `stopped` 5 / 無し 1 |

**`status` ではなく `gates[].verdict` を採った理由。** 契約 §5 の対照が
「`result.yaml` を verdict なしにした一時契約で FAIL」を求める。`status` で判定すると
その一時契約も `status` を持つため SKIP になり、**契約自身が要求する対照を通せない。**
契約が名指しした語（`verdict`）で、実在する唯一の場所を採った。

## A4. exp 契約の一覧（13 件、すべて完了済み）

| 契約 | 最上位 status | gates の verdict |
|---|---|---|
| T-2026-08-11-phase-baseline-power | partial | pass, pass, skip |
| T-2026-08-15-grasp-injection-effect | pass | pass ×3 |
| T-2026-08-15-injection-form-sweep | pass | pass ×3 |
| T-2026-08-15-injection-sweep-deterministic | pass | pass ×3 |
| T-2026-08-26-denoise-falsification | stopped | stop, pass, skip, skip |
| T-2026-08-26-det2phase-segmentation-lovo | partial | pass ×3, ask |
| T-2026-08-26-oracle-ceiling-and-tool-drop | partial | pass ×3, skip |
| T-2026-08-26-oracle-ceiling-lovo | pass | pass ×3 |
| T-2026-08-29-lecun-detector-env-pd | pass | pass ×2 |
| T-2026-08-29-stage0-contract-b | partial | pass ×2 |
| T-2026-09-18-stage1-detector-towers | pass | pass ×3 |
| T-2026-09-18-stage1-phase-tower | partial | ask, pass ×3 |
| T-2026-09-19-stage1-phase-tower-r2 | partial | ask, pass ×2 |

**契約は 12 件と書いたが実測は 13 件である。** 起票後に
`T-2026-09-19-stage1-phase-tower-r2` が完了した。**未完了の exp は 0 件**であった。

## A5. 変更前後の P13（完了判定 a）

| | FAIL | PASS | SKIP |
|---|---:|---:|---:|
| 変更前（`make task-preflight` を 13 件へ実行） | **13** | 0 | 0 |
| 変更後（`check_symmetry_table` を 13 件へ実行） | 0 | 0 | **13** |

変更前の理由はすべて `prereg.md に conventions#symmetry の対称性の表が無い`。
変更後の理由はすべて `完了済み（result.yaml に verdict あり: N 件）のため対象外`。

## A6. 対照（完了判定 b・c）

一時ディレクトリへ `preflight_task.TASKS_DIR` を差し替えて実行した。

| # | 入力 | 期待 | 実測 |
|---|---|---|---|
| 1 | 表なし（未完了） | FAIL | FAIL |
| 2 | 表が揃う（未完了） | PASS | PASS |
| 3 | UNKNOWN が残る | FAIL | FAIL |
| 4 | 「意図的に変える」に理由なし | FAIL | FAIL |
| 5 | 判定が三値でない | FAIL | FAIL |
| 6 | `prereg.md` 自体が無い | FAIL | FAIL |
| 7 | `result.yaml` の `gates: []` | FAIL | FAIL |
| 8 | `gates[].verdict` が空文字 | FAIL | FAIL |
| 9 | `result.yaml` が壊れた YAML | FAIL | FAIL |
| 10 | `gates[].verdict` あり | SKIP | SKIP |
| 11 | **名前が完了済み契約を含む未完了** | FAIL | FAIL |

**11 件すべて一致。** #7〜#9 と #11 が陽性対照である。判定を「常に SKIP」へ壊すと
#1〜#9 と #11 が落ち、「常に FAIL」へ壊すと #2 と #10 が落ちる。

## A7. 様式の対照（完了判定 d）

| 入力 | 期待 | 実測 |
|---|---|---|
| 既存 `result.yaml` 103 件 | 変更前と同数が通る | **通過 102 / 不通過 1** |
| `asymmetric_comparison` を使う報告 | 通る | 通った |
| `rule_read_narrowly` を使う報告 | 通る | 通った |
| `check_does_not_check`（既存の語） | 通る | 通った |
| `zz_unknown`（未知の型） | 落ちる | 落ちた（`'zz_unknown' is not one of [...]`） |

不通過 1 件は `T-2026-08-22-philip-hub-foundation`。**変更前から不通過**であり、
旧様式（`meta:` の下に `task_id` / `verdict: PARTIAL` を置く）で書かれている。
契約 §6 に従い**触らず記録した**。本契約の変更とは無関係である（`kind: impl` で
exp でもない）。

## A8. 注記の削除（完了判定 e）

`docs/issuer-defects.md`

| | 変更前 | 変更後 |
|---|---|---|
| 「enum には未追加」 | **11 行目に 1 件** | 0 件 |
| 「（同上）」（11 行目を受ける） | 12 行目に 1 件 | 0 件 |

## A9. 試験と規則数（完了判定 f）

| | 変更前 | 変更後 |
|---|---|---|
| `pytest tests/` | **6 failed / 595 passed** | **6 failed / 609 passed** |
| 失敗の内訳 | test_engines 1・test_fetch_task 1・test_research_logger 4 | **同一の 6 件** |
| `len(check_spec.RULES)` | **8** | **8** |
| `ruff check`（変更した 3 ファイル） | — | All checks passed |

追加した試験は 14 件（`tests/test_symmetry_gate.py` が 28 → 42 件）。

## A10. 検査

| 検査 | 結果 |
|---|---|
| `make task-validate`（L1+L2） | exit 0、`1 task(s), 0 failed` |
| `make task-preflight`（L3） | exit 0、`5 PASS / 1 WARN / 7 SKIP / 0 FAIL` |
| `make forbidden-check` | `"status": "pass"`、`violations: []`、changed 7 / checked 7 |
| `make spec-check TASK=…` | **status fail、hits 1**（`gate_requires_report_before_end`） |

**L3 の SKIP 7 件**（「合格」ではなく「実行されなかった」）:
P2 `cuda_ext_loaded`・P3 `deterministic_flags`・P11 `gpu_free`（`plan.env.preflight` に
記載なし）、P4 `prereg_committed`・P5 `frozen_source_hash`・P13 `symmetry_table_complete`
（`kind=impl` のため exp 専用の対象外）、P12 `refs_resolved`（解決前提の参照が無い）。

**L3 の WARN 1 件**（P9 `spec_lint`）と `make spec-check` の 1 件は**同一の指摘**であり、
契約の構造的な誤りである。§A11 を見よ。

## A11. `gate_requires_report_before_end`（契約の誤り）

    tasks/T-2026-09-19-p13-skip-and-enum/spec.yaml:38
    ゲート G1 は after=B（最終フェーズは C）で完了報告を求めている。
    未測定の値を書くことになる: 完了済みの exp で SKIP、未完了の exp で従来どおり
    FAIL か PASS。既存の result.yaml が全件 schema を通る

G1 が求める 3 つはいずれも **フェーズ C「検証（対照つき）と報告」で初めて測る**。
`after: B` のまま字面どおり評価すると、B の終了時点で未測定の値を書くことになり、
`governance.integrity` の `unknown_if_unmeasured` と衝突する。

**契約は書き換えていない**（過去の契約を書き換えない規則、および実行者が検証エラーを
推測で直さない規則による）。G1 は**フェーズ C の実測が揃った時点で評価した**。
評価に使った実測は §A5〜A9 である。

## A12. 自動同期の抑止

| 時点 | 状態 |
|---|---|
| 実行前 | `.sync-pause` 在（`make task-start` が作成）。記録に `[efros] 一時停止中` |
| 報告後 | `mv .sync-pause .sync-pause.released` で解除する（`RESULT.md` §送出に実測を記す） |

稼働中の `~/bin/m2-sync.sh` は `sync-pause` を 2 箇所で参照しており、抑止は効いている。

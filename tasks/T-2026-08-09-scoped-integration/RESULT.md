# RESULT — T-2026-08-09-scoped-integration

**実行者:** `lecun` / 元分岐 `exp/lecun-wip-20260703` / 統合分岐 `integrate/wiring-work-20260809`
**実行日時:** 2026-08-07T23:36:09Z
**判定:** **PASS（契約基準）** — 派生物を除いた18ファイルを PR #52 として起票し、退避物34件を移動・削除せず棚卸しした。全体 pytest は既存5失敗のままで green ではないが、開始前後で失敗数と失敗テストは不変。

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `inputs.denominator.ref` | 記載なし | 対象外 |
| `inputs.sigma_policy` | 記載なし | 対象外。数値の改善判定を行わない |
| `inputs.frozen_source.ref` | 記載なし | 対象外。preflight の P5 も `kind=impl` のため SKIP |
| `contract.conventions_rev` | `1201f4f` | `d422b08` へ実測置換 |
| `contract.inject_verbatim` | `conventions#prohibitions`, `conventions#naming` | 下記に原文を転記 |

### `conventions#prohibitions`（原文）

```
<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

### `conventions#naming`（原文）

```
<a id="naming"></a>
## naming

実験フォルダは手作業で命名せず、`ExperimentManager` が次の規則で自動採番する。

    {step}_{seq:03d}_{description}_seed{seed}

- `step`: `s0`〜`s9`、または `a1`〜`a7`
- `seq`: 同一 category と step 内の3桁ゼロ埋め連番
- `description`: 実験内容の短い説明
- `seed`: 乱数シード。既定42

転記元: `README.md` の「命名規則」。
```

`1201f4f..d422b08` の差分は `frozen_source` の適用範囲と変更履歴への追記であり、上記2アンカーの原文には差分が無かった。

## 2. Phase A — 統合範囲の切り出しと起票

### 統合先に無いコミット

| commit | 内容 |
|---|---|
| `e13fc4f` | docs(tasks): record the real-environment check and correct the draft PR finding |
| `04dab86` | docs(tasks): record the wiring follow-up |
| `d30c413` | fix(ci): distinguish expired credentials from missing ones |
| `8d45db9` | feat: add make setup to install dev dependencies into the venv |
| `a059e2e` | docs(tasks): record host differences in dependency install and autosync logs |
| `6340808` | docs(runindex): file host-dependent scan and autosync log semantics |
| `183ae50` | docs(experiments): describe the wiring verification run and its limits |
| `3523293` | docs(tasks): record the wiring verification run |
| `100abd0` | chore(runindex): reflect the wiring verification run |
| `25ea5ef` | s0(wiring_verification): mAP=0.000277151 seed42 [auto-sync] |

### 統合した18ファイル

- `.github/workflows/auto-draft-pr.yml`
- `Makefile`
- `experiments/baselines/s0_040_wiring_verification_seed42/command.sh`
- `experiments/baselines/s0_040_wiring_verification_seed42/config.yaml`
- `experiments/baselines/s0_040_wiring_verification_seed42/git_commit.txt`
- `experiments/baselines/s0_040_wiring_verification_seed42/metrics.json`
- `experiments/baselines/s0_040_wiring_verification_seed42/notes.md`
- `experiments/baselines/s0_040_wiring_verification_seed42/per_class_ap.json`
- `experiments/baselines/s0_040_wiring_verification_seed42/server.txt`
- `tasks/README.md`
- `tasks/T-2026-08-09-run-wiring-verification/RESULT.md`
- `tasks/T-2026-08-09-run-wiring-verification/SPEC.md`
- `tasks/T-2026-08-09-run-wiring-verification/spec.yaml`
- `tasks/T-2026-08-09-wiring-followup-and-integration/RESULT.md`
- `tasks/T-2026-08-09-wiring-followup-and-integration/SPEC.md`
- `tasks/T-2026-08-09-wiring-followup-and-integration/spec.yaml`
- `tasks/inbox.md`
- `tools/harvest_runindex.py`

`origin/phase0...exp/lecun-wip-20260703` の差分から、`runindex/` と `context/auto/` に属する派生物58ファイルを除外した。

| 項目 | 実測 |
|---|---|
| 統合分岐の起点 | `origin/phase0` |
| 起点直後の先行コミット数 | 0 |
| G1 cached 差分の派生物 | 0 件 |
| G1 worktree の派生物 | 0 件 |
| 統合コミット | `6710468` |
| PR | #52 / `https://github.com/takuya3h/m2/pull/52` |
| PR 状態 | OPEN / MERGEABLE / auto-merge 無効 |

## 3. Phase B — 実行ホストの退避物

詳細は `leftover_inventory.md` に記録した。

| 分類 | 件数 |
|---|---:|
| `smoke_test` | 19 |
| `superseded` | 6 |
| `failed_run` | 5 |
| `aborted_run` | 4 |
| **合計** | **34** |

退避物34件は8親ディレクトリにあり、全件が実在、Git追跡ファイル0件、`.gitignore` の明示規則に一致した。G2 再検査は `excluded_records=34 / parent_dirs=8 / missing=0`。移動・削除・改名は行っていない。

棚卸しコミットは元分岐上の `1c518ba`。

### 処置の案

| 案 | 内容 | 選ばなかった理由 |
|---|---|---|
| A | 走査対象を Git 追跡下の run に限定 | 退避証跡が索引から消える影響を利用者が判断する必要がある |
| B | 退避一覧を規約化し全ホストで同一保持 | 同期・容量・運用負荷を本 task では評価していない |
| C | 索引をホスト依存生成物とし正本ホストを定める | 正本ホストの指定は利用者の判断領域 |
| D | 収穫器へ退避物を索引化する明示オプションを追加 | 新機能実装は本 task の範囲外 |

本 task ではどの案も選ばず、退避物を現位置に保持した。

## 4. 完了判定

| # | 判定 | 実測 | 結果 |
|---|---|---|---|
| 1 | 分岐が統合先から派生 | `merge-base --is-ancestor` exit 0 | PASS |
| 2 | 索引が含まれない | 0 件 | PASS |
| 3 | 軽量ビューが含まれない | 0 件 | PASS |
| 4 | 一次証跡が含まれる | 7 件 | PASS |
| 5 | 契約が含まれる | 8 件、最終送出で本 task も追加 | PASS |
| 6 | 収穫器が含まれる | 1 件 | PASS |
| 7 | ビルド定義が含まれる | 1 件 | PASS |
| 8 | 継続的統合設定が含まれる | 1 件 | PASS |
| 9 | 起票が作られた | PR #52 が1件 | PASS |
| 10 | 退避物が動いていない | 34件中 missing 0 | PASS |
| 11 | 契約検証 | exit 0 | PASS |
| 12 | 実行前検査 | 4 PASS / 4 SKIP / 0 FAIL、exit 0 | PASS |
| 13 | 全体テストが不変 | 前後とも5 failed / 247 passed / 22 warnings | PASS（増加なし） |
| 14 | 禁止領域が無変更 | `data/splits/ context/conventions.md src/` 差分0件 | PASS |

### 全体テストの既存失敗

開始前・変更後の両方で次の5件が失敗した。新規失敗は0件。

- `tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics`
- `tests/test_research_logger.py::test_log_run_idempotent`
- `tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally`
- `tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit`
- `tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block`

## 5. deviations

1. SPEC の Phase B Step 3 は4パターン19件しか検査せず、退避物34件のうち15件を見落とす。新規 `runindex/runs` 35件を別経路で抽出し、退避34件と配線検証1件へ機械的に分離した。
2. G2 の glob は対象外群と重複を含む親ディレクトリ数10を返し、Step 3 の run数19とは単位が異なる。判定には退避34 record の全 path 再照合を使用した。
3. Phase A の広い `git add tasks` は未追跡の本 task 契約まで早期に含めるため実行せず、`git checkout <source> -- <paths>` が staging した対象18ファイルをそのまま確定した。
4. `apply_patch` は環境の `bwrap` 名前空間エラーで使用不能だったため、同等の unified diff を `git apply` で適用した。変更内容は個別に再読して確認した。
5. 初回プリフライトの SKIP は P2 `cuda_ext_loaded`、P3 `deterministic_flags`、P4 `prereg_committed`、P5 `frozen_source_hash`。契約上非対象であり、合格とは数えていない。
6. 全体 pytest は開始前から5失敗で green ではない。本 task による失敗増加は0件だが、既存失敗を解消したとは扱わない。

## 6. 申し送り

- PR #52 は作成済みだが、統合も auto-merge も行っていない。
- 同じ内容を含む既存 PR #51 は閉じていない。派生物を除いた #52 を統合候補とするのが本 task の所見だが、#51 を閉じる判断は利用者へ委ねる。
- 統合後、各ホストで次を実行する必要がある。

```
make setup
make runindex && make context
```

- 退避物を持たないホストで再生成した索引を次の正本とする案が望ましいが、正本ホストの決定は未実施。
- `runindex/` を手で編集していない。未測定値は記載していない。

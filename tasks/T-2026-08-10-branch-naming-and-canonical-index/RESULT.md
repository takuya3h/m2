# RESULT — T-2026-08-10-branch-naming-and-canonical-index

**実行日:** 2026-08-09 UTC
**実行分岐:** `feat/branch-naming`
**基準:** `origin/phase0` (`79940b5`)
**判定:** **PASS（既存の全テスト失敗 5 件は不変、逸脱あり）**

## 1. 解決した契約参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `meta.depends_on` | `T-2026-08-10-conventions-survey` | 完了 commit `db26e40` は `origin/phase0` の祖先 |
| `contract.conventions_rev` | `1201f4f` | 現在の `d422b08` へ解決 |
| denominator / frozen source | 記載なし | 対象外 |
| sigma policy | 記載なし | 既定の `series=pstd`、`sigma_source=paired_delta`、`delta_sigma_source=paired`。数値判定は未実施 |

`1201f4f..d422b08` の差分は `frozen_source` の適用範囲と履歴だけで、注入対象の原文は同一だった。

### `conventions#prohibitions`（原文）

```text
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

```text
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

## 2. Phase A — 影響箇所の実測

| 箇所 | 接頭辞を保つ場合 | 根拠 |
|---|---|---|
| `git_autosync.py` の送出判定 | 変更不要 | `branch.startswith("exp/")` だけを判定し、新名を実関数へ渡すと deploy-key guard まで進んだ |
| `test_git_autosync.py` | 変更不要 | 固定しているのは `exp/` 接頭辞の通過・非通過で、日付や `wip` には依存しない |
| `auto-draft-pr.yml` | 変更不要 | 起動条件は `exp/**` |
| `new_experiment_branch.sh` | 変更必要 | 旧実装が theme と日付を組み込んでいた |
| `setup_host_autosync.sh` | 表示だけ変更 | guard は `exp/*` のみ。利用例だけが旧命名だった |
| `~/bin/m2-sync.sh` | 変更不要 | 現在分岐と同名の `origin/$BR` の存在を条件にする汎用実装。新 remote ref を先に作ればよい |
| `~/bin/keeper.sh` | 変更不要 | 命名の詳細への依存なし |

先行調査では5箇所を致命と分類していたが、実装を読むと guard・試験・CI の3箇所は `exp/` を維持する限り変更不要だった。必要な機能変更は生成器、手順表示の更新は setup script だけに絞った。G1 は通過した。

## 3. Phase B — 生成規則と移行補助

`new_experiment_branch.sh` に `--dry-run` を追加し、`exp/<logical-host>` を生成するよう変更した。論理名は小文字英数とハイフンのみ、2〜20文字とし、8桁日付とハイフン区切りの `wip` を明示的に拒否する。試験は一時 HOME を使うため、本物の分岐を変更しない。

`rename_host_branch.sh` は次の順序を実装した。

1. 入力と clean worktree を検査する。
2. `git push -u origin HEAD:refs/heads/<new>` で新 remote ref を先に作る。
3. fetch 後、`origin/<new>` の存在を確認する。
4. その後で local branch を改名し、upstream と参照を再確認する。

旧 remote ref は削除しない。大文字小文字だけが異なる改名は、一時 local branch `exp/<logical-host>-case-rename-tmp` を経由する。一時 bare remote で `exp/Bengio` から `exp/bengio` への実移行を確認し、新旧 remote ref の併存と新 upstream を確認した。`--dry-run` では分岐・状態・remote ref が不変だった。

実際の `commit_and_push_evidence` には `exp/bengio`、`exp/lecun`、`exp/dlsta`、`exp/he` を渡し、全て branch guard を通過して次の deploy-key guard まで進むことを確認した。`phase0`、`master`、detached HEAD、`feat/x`、`host/bengio` は branch guard で拒否されたため G2 は通過した。

移行対象11台の対応と順序は `migration_plan.md` に記録した。到達不能だった philip の現在値は `UNKNOWN` のままとした。

## 4. Phase C — 手順書と索引の正本

`OPERATION.md`、`README.md`、`docs/host_autosync_onboarding.md`、`tasks/README.md` の現行手順だけを更新した。現在の定位置分岐を `exp/<logical-host>` とし、生成・移行 helper を案内した。

索引の正本はホスト名で固定せず、`runindex/index.csv` の全 `path` が Git 追跡下にある clean host でのみ再生成・記録する規約とした。他ホストは配布された索引を使う。現在の751行を機械検査し、追跡外 path が0件であることを確認した。

古い形式の一致として `OPERATION.md` の `exp/aolab-wip-20260703` を残した。これは ilya の旧ブランチを説明する歴史記録で、現行例ではないためである。更新可否に迷って残した記述はない。G3 は通過した。

## 5. 自己検証

| 判定 | 結果 |
|---|---|
| 追加試験 | `tests/test_branch_naming.py`: 5 passed |
| 不正入力 | 指定6件を全て拒否 |
| shell 構文 | 生成・移行・setup の各 script で `bash -n` 成功 |
| dry-run | 一時リポジトリで branch・status・remote ref 不変 |
| remote-first 順序 | 一時 bare remote への実呼出しと実装目視で確認 |
| 現在分岐 | `feat/branch-naming` のまま |
| 全テスト開始時 | 5 failed, 247 passed, 22 warnings |
| 全テスト完了時 | 5 failed, 252 passed, 22 warnings。failed 数は不変 |
| 禁止領域 | `runindex/`、`context/auto/`、`experiments/`、`transfer/`、`data/splits/`、`context/conventions.md` に差分なし |
| `make task-validate` | 最終実行で exit 0 |
| `make task-preflight` | 最終実行で exit 0 |

既存の5失敗は `tests/test_engines.py` 1件と `tests/test_research_logger.py` 4件で、開始前と同一だった。本 task による新規失敗はない。

## 6. 別作業への申し送り

本 task は実装と文書化だけであり、各ホストの定位置分岐は切り替えていない。`phase0` 統合後、`migration_plan.md` の順に1台ずつ `--dry-run` と実移行を行い、送出と Draft PR を確認する。旧 remote ref の削除は別判断とし、本 task では行わない。統合や自動統合の有効化も行わない。

## 7. deviations

- 開始時点で `feat/branch-naming` が既に `origin/phase0` から作成済みだったため、SPEC の branch 作成コマンドは再実行しなかった。
- 初回 validate は、起票後に conventions rev と索引・実験件数が進んだため WARN を出したが exit 0 だった。注入対象の原文と依存 commit を再確認して続行した。
- `apply_patch` が環境の `bwrap: No permissions to create a new namespace` で一部失敗した。`git apply --recount` の代替試行も原子的に失敗したため、対象行を限定した `sed -i` を使い、直後に全文差分と `bash -n` で確認した。
- 共通指示の `tasks/todo.md` 更新は、SPEC が過去記録の変更を禁じ、最終 staging 対象を task directory と `tasks/inbox.md` に限定しているため行わず、実行計画はセッション内 plan で管理した。

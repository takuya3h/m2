# audit — T-2026-10-07-auto-merge-regen-pr

Phase A の測定記録。測定時点の本線は `origin/phase0` = `67c4cc44`（#211 の統合）、分岐 `feat/auto-merge-regen-pr`、ホスト `philip`。

## 1. phase0 の保護（Step 1 / 完了判定 A）— 読んだだけで、変えていない

`gh api repos/takuya3h/m2/branches/phase0/protection` で読んだ。

| 項目 | 値 |
|---|---|
| 必須の状態検査 | **無い**（`required_status_checks` が存在しない） |
| 承認の件数 | `required_approving_review_count: 0`。古い承認の取り消し、code owner、最後の push の承認はどれも `false` |
| 最新の基点の要求 | **無い**。基点を求める設定（`required_status_checks.strict`）は状態検査の下にあり、その状態検査自体が無い |
| 管理者への適用 | `enforce_admins: true` |
| 迂回の許可 | `bypass_pull_request_allowances` は無い。push の制限（`restrictions`）も無い |
| 直線の履歴 | `required_linear_history: false` |
| ルールセット | `rules/branches/phase0` は `[]` |

許可されたマージの方式（`gh api repos/takuya3h/m2`）は次のとおり。`allow_merge_commit` `allow_squash_merge` `allow_rebase_merge` がすべて `true`。`allow_auto_merge: true`、`delete_branch_on_merge: false`。

**これまでの方式。** phase0 へ統合された直近 30 件の PR の統合 commit を調べた。30 件とも親が 2 つで、**merge commit 方式**だった（squash と rebase は 0 件）。→ 本契約も `--merge` を使う。

Actions の既定の権限（`actions/permissions/workflow`）は `default_workflow_permissions: read`、`can_approve_pull_request_reviews: false`。

## 2. 現在の workflow（Step 2 / 完了判定 B）

`.github/workflows/regen-projections.yml`（`67c4cc44` 時点）

| 段 | 行 | 内容 |
|---|---|---|
| 権限の宣言 | `:13-14` | `permissions: contents: write` だけ |
| 同時実行 | `:17-19` | `group: regen-projections`、`cancel-in-progress: false` |
| 生成物の一覧 | `:41` | `OUTPUTS` の 4 ファイル |
| 生成物以外の差分の判定 | `:52-57` | `:(exclude)` で 4 ファイルを除いた `git status`。空でなければ exit 1 |
| 生成物の差分の判定 | `:59-63` | 4 ファイルに差分が無ければ `changed=false` で exit 0 |
| auto 分岐への push | `:70-71` | `--force`。成功したら `changed=true` |
| PR を作る段 | `:78-96` | `if: changed == 'true'`、認証は秘匿 `AUTOSYNC_PR_TOKEN` を渡す（`:81`）。未設定なら exit 1（`:84-87`）。`gh pr list` で開いた PR があれば何もせず、無ければ `gh pr create`（`:88-95`）。**401 の場合は gh の出力をそのまま出すだけで、未設定と無効を言い分けない** |

## 3. GITHUB_TOKEN でマージできるか、次の workflow を起こすか（Step 3 / 完了判定 C）

**文書から読んだこと**（WebFetch。`ctxpack` はこのホストに無かった）

- REST の `PUT /repos/{owner}/{repo}/pulls/{pull_number}/merge` は、**Contents の write** に分類されている（`docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens`）。
- `PATCH /repos/{owner}/{repo}/pulls/{pull_number}`（PR を閉じる操作を含む）は、**Pull requests の write** に分類されている（同じ頁）。
- GITHUB_TOKEN の頁（`docs.github.com/en/actions/concepts/security/github_token`）の原文: "When you use the repository's `GITHUB_TOKEN` to perform tasks, events triggered by the `GITHUB_TOKEN` will not create a new workflow run, with the following exceptions"。例外は `workflow_dispatch`、`repository_dispatch`、`pull_request` の一部の種類である。**push は例外に入っていない。**

**判定**

- **GITHUB_TOKEN でのマージについて、できないと示す根拠は見つからなかった。** 理由は三つある。必要な権限（Contents の write）は workflow の `permissions` で宣言できる。保護は PR を経ることだけを求め、承認は 0 件で、状態検査も迂回の制限も無い。`can_approve_pull_request_reviews: false` が止めるのは PR の作成と承認で、マージは含まない。ただし、**実際に通るかは UNKNOWN で、統合後の実測で判定する。** 手元では GITHUB_TOKEN を再現できない。
- **GITHUB_TOKEN で閉じられるか**も同じく UNKNOWN で、統合後に判定する。
- **次の workflow を起こすか。** 文書によれば、GITHUB_TOKEN によるマージで起きる phase0 への push は**新しい実行を作らない**。よって自動マージの後に `regen-projections` は起動しないはずである。仮に起動しても、マージ後の木は生成物を作り直した木と同じなので「差分なし」で止まる（前契約の #209 で実測済み）。実際にどちらになるかは統合後に確かめる。

## 4. G1 の判定

必須の状態検査は無く、マージが待たされることはない。GITHUB_TOKEN でのマージができないと示す根拠は無い。→ **escalate_if に当たらない。G1 pass。** 実際に通るかの判定は、統合後の実測に持ち越す。

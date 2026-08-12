# 実験成果の自動 git 同期（機械層のみ・phase0 は PR ゲート）— 設計仕様

- **日付**: 2026-07-10
- **対象**: `takuya3h/m2`（**public** repo）+ 11 台 GPU サーバー同期システム（`/home/ubuntu/slocal/sync/`）
- **背景**: 各サーバーが個別 `exp/<host>-*` ブランチで作業し、実験成果（層1=git 追跡ドキュメント）が
  未 push/未統合のまま散在。層2（checkpoint 等 gitignore 巨大物）は Syncthing で既に自動同期済み。
  実験ごとの `merge / branch / commit / push / phase0統合` の手作業 toil を削減したいが、
  研究インテグリティ（Δ 基準点汚染防止・数値捏造防止）と同期システムの安全モデル
  （サーバーに書込 cred を置かない・phase0 は人手 curation）を壊さない範囲に限る。

## 1. ゴール / 非ゴール

**ゴール**
- 実験完了時に、その実験の**証跡ディレクトリだけ**を provenance 付きで自動 commit + push（exp/* ブランチ）。
- push を検知した CI が phase0 への**ドラフト PR を自動起票**（人手 merge のゲートは残す）。
- 「現在の分断状態 → 全台同期」への安全なセットアップ手順と通常運用を `sync/README.md` に文書化。

**非ゴール（YAGNI）**
- phase0 への自動 merge（**明確に禁止のまま**）。
- `git merge phase0`（他台成果の取り込み）の自動化（conflict 多発ゆえ v1 は手動据置）。
- 層2（checkpoint）の同期変更（Syncthing で完結済み・無関係）。
- 書込 cred のサーバー常置（deploy key = push 専用・phase0/master は branch protection で封鎖）。

## 2. 4 操作の処遇（取りこぼし防止）

| 元操作 | 処遇 | 実装 |
|---|---|---|
| `git add -A && commit && push` | ✅ 中核。ただし **exp_dir 限定 stage**（`add -A` 禁止） | `git_autosync` + `ExperimentManager.finalize()` |
| phase0 統合 | ✅ CI がドラフト PR 起票 → **人手 merge** | `.github/workflows/auto-draft-pr.yml` |
| `git switch -c exp/<host>-<theme> phase0` | 🔸 小ヘルパ（SERVERNAME ベース） | `scripts/sync/new_experiment_branch.sh` |
| `git merge phase0`（取り込み） | ⏸ v1 手動据置（任意で安全ヘルパ後付け） | — |

## 3. アーキテクチャ / データフロー

```
[実験完了] ExperimentManager.finalize()  ── または ad-hoc スクリプトが直接 ──▶ git_autosync.commit_and_push_evidence()
   │ (Python, in-process, 純 stdlib)
   ├─ guard: exp/* ブランチ上か / deploy key 有 / exp_dir が repo 内か → 満たさねば no-op
   ├─ secret-scan: stage 対象の path/内容に秘密パターン → 中止 + アラート
   ├─ git -C <repo> add -- <exp_dir> [docs/experiment_log.md]     ← add -A 禁止
   ├─ size-guard: staged に閾値超ファイル → 中止 + アラート
   ├─ git -C <repo> commit -m "<provenance>"
   └─ git -C <repo> push origin HEAD:exp/<host>-<theme>           ← deploy key (core.sshCommand)
          │
          ▼  GitHub: exp/<host>-* 更新
   [GitHub Actions] on push 'exp/**' → ドラフト PR を open/update（base=phase0, GITHUB_TOKEN, 冪等）
          │
          ▼  [人手] PR レビュー（val→test 済か・Δ 有意か）→ phase0 へ merge（★ゲート）
   keeper（既存・30分）→ 全台ローカル phase0 前進 → 各台で任意 `git merge phase0`（手動・不変）

[層2] checkpoint 等は Syncthing で自動（本設計は無関係）
```

## 4. コンポーネント仕様（正確な interface）

### 4.1 `src/egosurgery/utils/git_autosync.py`（新規・**純 stdlib のみ**）

制約:
- 追加依存禁止。`subprocess` / `pathlib` / `re` / `os` / `dataclasses` のみ。third-party import 禁止
  （フックは学習プロセスの interpreter で動く。efros に `.venv` 無し・多 venv 環境で確実に import 可能に）。
- **全 git 呼び出しは `git -C <repo_root>`**（train_t1b.py 等が `os.chdir` する副作用に耐えるため cwd を明示）。
- **学習ループに例外を漏らさない**。全経路で `AutoSyncResult` を返し、失敗は
  `~/claude-sync/sync-alerts.log` に追記（Syncthing で全台伝播）。

```python
@dataclass
class AutoSyncResult:
    ok: bool
    action: str          # "pushed" | "skipped" | "committed_no_push" | "aborted"
    reason: str          # 人間可読の理由（skip/abort の説明）
    branch: str | None
    commit: str | None   # 生成した commit hash（あれば）
    staged: list[str]    # stage したファイル（repo 相対）

def commit_and_push_evidence(
    exp_dir: str | Path,
    *,
    meta: dict | None = None,     # {category, step, description, seed, exp_id, metric_name, metric_value}
    repo_root: str | Path | None = None,   # 省略時は exp_dir から git rev-parse --show-toplevel
    extra_paths: list[str] | None = None,  # 追加 stage（例: ["docs/experiment_log.md"]）
    push: bool = True,
    alert_log: str | Path | None = None,   # 省略時 ~/claude-sync/sync-alerts.log
) -> AutoSyncResult
```

**ガード（いずれか偽なら `action="skipped"` で no-op・例外なし）**
1. `repo_root` が git repo で、`exp_dir` がその配下。
2. 現ブランチが `exp/*`（`phase0`/`master`/detached では skip＝正史を汚さない）。
3. deploy key push が構成済み（`repo_root/.git/config` に `remote.origin.pushurl` か repo-local
   `core.sshCommand`、または後述の環境変数）。**未構成なら skip**（学習は止めない）。
4. stage 差分が空なら skip（`action="skipped", reason="nothing to commit"`）。

**secret-scan（`action="aborted"` + アラート）** — public repo ゆえ必須
- **path denylist**（stage 候補に対し）: `.env`, `.env.*`（`.env.gpg`/`.env.example` は除外）,
  `*.key`, `*.pem`, `id_rsa*`, `id_ed25519*`, `*passphrase*`。
- **content scan**（stage 対象のテキストファイル、~1MB 以下のみ）: 正規表現
  `ghp_[A-Za-z0-9]{36}` / `github_pat_[A-Za-z0-9_]{22,}` / `-----BEGIN [A-Z ]*PRIVATE KEY-----`
  / `AKIA[0-9A-Z]{16}` / `(NOTION|WANDB|OPENAI|ANTHROPIC)_API_KEY\s*[=:]\s*\S`。
- 1 件でもマッチ → commit せず abort + アラート。

**stage 規則**
- `git -C <repo> add -- <exp_dir_rel>` と `extra_paths`。**`add -A` / `add .` は禁止**。
- `.gitignore` の experiments allowlist により checkpoint 等巨大物は自然に除外される。
- **size-guard**: `git -C <repo> diff --cached --numstat` と実ファイルサイズで
  **> 5 MB の staged ファイルがあれば abort + アラート**（gitignore 漏れの安全網）。

**commit メッセージ（provenance・機械 trailer）**
```
{step}({description}): {metric_name}={metric_value} seed{seed} [auto-sync]

Auto-committed by egosurgery finalize hook.
Sync-Source: {server_name}      # resolve_server_name() で解決（$(hostname) 直用禁止）
Experiment: {category}/{exp_id}
```
- metric 欠落時: `{step}({description}): finalize seed{seed} [auto-sync]`。
- **Claude 対話用 trailer（Co-Authored-By / Claude-Session）は付けない**（自動 commit は対話由来でない）。

**push**
- `git -C <repo> push origin HEAD:refs/heads/{current_branch}`。
- **非 fast-forward は force-push しない**。失敗 → `committed_no_push` + アラート（exp/<host>-* は
  単一 writer ゆえ稀。競合時は人手確認）。

### 4.2 `ExperimentManager.finalize()`（`experiment_manager.py` に追加）

```python
def finalize(self, *, metric: tuple[str, float] | None = None, push: bool = True) -> "AutoSyncResult | None":
    """実験完了時に証跡 dir を自動 commit + push（graceful・失敗は no-op）。"""
```
- `git_autosync.commit_and_push_evidence(self.exp_dir, meta={...}, extra_paths=[...], push=push)` を呼ぶ。
- `git_autosync` import 失敗や `exp_dir is None` でも例外を出さず `None` を返す（学習を止めない）。
- 各 trainer（`stage_a_trainer` / `phase_trainer` / `trainer` / `mmdet_trainer`）末尾で呼ぶ。
  ad-hoc スクリプト（train_t1b.py 等・ExperimentManager 非経由）は `git_autosync` を直接呼べる。

### 4.3 `.github/workflows/auto-draft-pr.yml`（新規 CI）

```yaml
name: auto-draft-pr
on:
  push:
    branches: ['exp/**']
permissions:
  contents: read
  pull-requests: write
jobs:
  draft-pr:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Open or update draft PR to phase0
        env: { GH_TOKEN: ${{ github.token }} }
        run: |
          BR="${GITHUB_REF_NAME}"
          if gh pr list --head "$BR" --base phase0 --state open --json number --jq '.[0].number' | grep -q .; then
            echo "PR exists; push auto-updates it."
          else
            gh pr create --draft --base phase0 --head "$BR" \
              --title "auto: ${BR} → phase0" \
              --body "自動起票（実験成果の phase0 統合候補）。**merge は人手**でレビュー後に。val→test 検証と Δ 有意性を確認すること。"
          fi
```
- 冪等（1 ブランチ 1 PR）。`GITHUB_TOKEN` はリポジトリ scope・揮発性で**どのサーバーにも保存されない**。
- base=phase0（master ではない。phase0 が幹）。

### 4.4 `scripts/sync/new_experiment_branch.sh`（小ヘルパ）
```bash
# 使い方: bash scripts/sync/new_experiment_branch.sh <theme>
# SERVERNAME(→hostname) 解決で exp/<server>-<theme>-<YYYYMMDD> を phase0 から作成。
```
- `$(hostname)` 非依存（philip/ilya=aolab 衝突回避）。既存ブランチ名は上書きしない。

### 4.5 ライブ運用 runbook（**本設計では実行しない**・README/setup へ記載し人手 or 確認後）

- **branch protection**（phase0 + master・PR 必須・直 push/force-push 禁止）:
  `gh api -X PUT repos/takuya3h/m2/branches/phase0/protection ...`（正確な JSON は runbook 参照）。
- **ホスト別 deploy key**: 各台 `ssh-keygen -t ed25519 -f ~/.ssh/id_m2deploy -N ''` →
  `gh api repos/takuya3h/m2/keys -f title="deploy-<server>" -f key=@... -F read_only=false` →
  repo-local `git config core.sshCommand "ssh -i ~/.ssh/id_m2deploy -o IdentitiesOnly=yes"`。
- **既存 `repo` scope gh トークン失効**: efros 及び全台の `~/.config/gh` の write トークンを
  read-only 化 or 撤去（fetch は public ゆえ不要、push は deploy key へ）。

## 5. セキュリティモデル

- サーバーには **push 専用の deploy key のみ**。phase0/master への直 push は branch protection が技術強制。
- PR 起票の write は **CI の揮発 GITHUB_TOKEN**（サーバー非常置）。
- public repo ゆえ **secret-scan + exp_dir 限定 stage + size-guard** の三重防御。
- 既存 `repo` scope gh トークン（efros で発見）は過剰権限 → 失効を runbook 化。

## 6. エラー処理

- `git_autosync` は**全失敗を吸収**（例外を学習に漏らさない）→ `AutoSyncResult` + `sync-alerts.log`。
- push 非 ff → force しない・`committed_no_push` で人手へ。
- CI 失敗 → Actions タブに可視・冪等ゆえ次 push で復旧。
- branch protection は phase0/master のみ（`exp/**` には付けない）。

## 7. テスト戦略

- **stdlib 動作検証ハーネス（今すぐ・pytest/依存追加不要）**: 一時 git repo + bare remote で
  (a) exp/* 外 → no-op, (b) `.env` 混入 → abort, (c) content secret（`ghp_...`）→ abort,
  (d) exp_dir 外の変更を巻き込まない, (e) commit メッセージ整形, (f) bare remote へ push 成功,
  (g) 5MB 超 staged → abort。`.venv-relation-detr/bin/python` で実行。
- **committed pytest**: `tests/test_git_autosync.py`（プロジェクト規約・正式 venv で走る）。
- **pilot（efros・要確認）**: smoke 実験 → commit+push → CI がドラフト PR 起票 →
  phase0 直 push が protection で弾かれることを確認。

## 8. ロールアウト

- Phase 1（efros pilot）: branch protection + workflow + deploy key + フックを efros のみ。初回手動観察。
- Phase 2: 他 10 台へ deploy key + フック配布（Mac 駆動・既存 5-5b パターン）。
- Phase 3: 全台 gh トークン失効。

## 9. ドキュメント変更

- **`sync/README.md`（必須・ユーザー明示要求）**: 追記/改訂。
  (a) 現在の状態（各台個別ブランチ・実験未同期）、(b) 分断→全台同期の**安全なセットアップ手段**
  （＝Phase 1-3 runbook）、(c) 今後の**通常運用の動作・操作方法**（実験完了で自動 push→CI 起票→
  人手 merge、確認コマンド、失敗時の対処）。**private→public の誤記も修正**、日常運用表・禁止事項を更新。
- **`sync/m2-sync-setup.md`**: 「private」誤記修正、rule 分割の反映。
- **`CLAUDE.md`（運用則）**: 「push/merge/PR作成は行わない」→ 分割:
  ✅ exp/* 自動 commit+push・CI ドラフト PR 起票は許可 /
  ❌ phase0/master への自動 merge・サーバーへの広い書込 cred 常置は継続禁止。
- **`docs/experiment_log.md`**: 本自動化導入エントリ。Notion `log_decision`（方針変更）。

## 10. 承認済み設計判断（本セッションの意思決定）

1. スコープ = 機械層のみ自動 + phase0 は PR ゲート（人手 curation）。
2. 発火 = 実験完了イベントフック（ExperimentManager.finalize / ad-hoc 直呼び）。
3. cred/PR = サーバー狭い push のみ（deploy key）+ CI でドラフト PR 起票 + branch protection + 既存トークン失効。

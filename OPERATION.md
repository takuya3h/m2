# 実験運用の手引き（2026-08-05 auto-sync 反映版）

本ドキュメントは 2026-08-02〜05 の全サーバー同期作業で確定した運用を記録する。
`README.md` のサーバー間同期セクションと重複する部分があるが、
**実験を 1 セット回すときに何をするか**という視点で書いている。

---

## 1. 全体像 — 二層設計

成果物は**種類によって別の経路**で全サーバーに配られる。

| 層 | 対象 | 経路 | 到達時間 | 人手 |
|---|---|---|---|:--:|
| **Syncthing** | `checkpoints/` `logs/` `predictions/` `visualizations/` `*.pth` `*.pt` `*.npy` | 自動（星型・中心 philip） | **28 秒**（2026-08-04 実測・philip から他 10 台） | **0** |
| **git** | 6 点必須証跡 + `server.txt`・コード・設定・`runindex/` | 限定 commit/push → Draft PR → review → GitHub auto-merge → 各台が取り込み | 通常 30 分以内（review 後） | **PR ごとに review** |
| どちらでもない | `.git` `.env` `data/raw` `wandb` `third_party` `data/hts_reconstruction` | — | — | — |

`.stignore`（各台）は `.stglobalignore`（phase0）から keeper が 30 分以内に自動反映する。
**2026-08-04 の伝播テストで、11 台すべてで正しく効いていることを確認済み**
（git 管理の証跡は Syncthing で配られなかった）。

`logs/` は原則 Syncthing 対象だが、`.gitignore` で明示許可した小さな評価証跡
（例: `logs/val_metrics_by_epoch.json`）だけは git にも載る。

git 側の自動化は二つに分かれる。

- `ExperimentManager.finalize()` / 配線済み ad-hoc trainer:
  完了 run の証跡ディレクトリだけを auto-commit + auto-push
- keeper が 30 分ごとに実行する `m2-sync.sh`:
  `phase0` の取り込み、既存 commit の auto-push、Draft PR の自動起票

🔴 `m2-sync.sh` は新しい commit を作らない。実験完了フック未配線のスクリプト、
途中終了した run、ガードで skip/abort された run は人手で確認する。

本書では、`m2-sync.sh` が `origin/phase0` を作業ブランチへ取り込む処理を
「作業ブランチ auto-merge」、GitHub が PR を `phase0` へ統合する処理を
「GitHub auto-merge」と呼び分ける。

### 6 点必須証跡 + 実行ホスト（`ExperimentManager` が自動生成）

```
experiments/<group>/<step>_<seq>_<desc>_seed<N>/
  ├ metrics.json       指標本体 + eval_recipe
  ├ config.yaml        設定
  ├ command.sh         実行コマンド
  ├ git_commit.txt     commit hash
  ├ per_class_ap.json  クラス別の値
  ├ notes.md           ファイルは自動生成、内容は必要時に人手追記
  └ server.txt         追加証跡: 実行ホスト（SERVERNAME から）
```

---

## 2. ブランチ規約

| ブランチ | 用途 | 誰が |
|---|---|---|
| **`phase0`** | **統合の幹。保護ブランチ**（PR が唯一の経路・`enforce_admins: true`・auto-merge 設定済み） | GitHub が統合 |
| `exp/<論理ホスト名>` | **各サーバーの定位置。常にここにいる** | そのサーバー |
| `chore/*` `feat/*` | 一時作業（PR 用）。マージ後に削除 | 必要時 |
| `master` `docs/plan-rewrite-2026-06` | 歴史的記録。触らない | — |

**`exp/*` は実験ごとに切らない。消さない。** 実験実行時は、そのサーバーの
定位置ブランチを使う。`chore/*` / `feat/*` はコード・文書作業中だけの例外。
論理ホスト名は小文字英数とハイフンのみ、2〜20文字とする。日付と `wip` は含めない。既存分岐の移行は `scripts/sync/rename_host_branch.sh` を使い、remote ref を先に作る。

### ホスト名と移行後の定位置ブランチ

| SSH 名 | `hostname` | `SERVERNAME` | ブランチ | 実験 run |
|---|---|---|---|---:|
| lecun | `lecun` | `lecun` | `exp/lecun` | **464** |
| efros | `efros` | `efros` | `exp/efros` | **194** |
| philip | `aolab` | `philip` | `exp/philip` | **31** |
| andrew | `Andrew` | `andrew` | `exp/andrew` | **3** |
| ilya | `aolab` | `ilya` | `exp/ilya` | 0（統合担当） |
| bengio | `Bengio` | `bengio` | `exp/bengio` | 0 |
| he | `he` | `he` | `exp/he` | 0 |
| adam | `adam` | `adam` | `exp/adam` | 0 |
| hinton | `Hinton` | `hinton` | `exp/hinton` | 0 |
| ian | `ian` | `ian` | `exp/ian` | 0 |
| dlsta | `084f3b0911a2` | `dlstation` | `exp/dlsta` | 0 |

実際の分岐切替は別作業で行う。現在値と移行順序は `tasks/T-2026-08-10-branch-naming-and-canonical-index/migration_plan.md` を参照する。

**philip と ilya は `hostname` が同じ `aolab`。** 別 IP（`.150` / `.63`）の別マシンで、
`SERVERNAME` で区別する。`exp/aolab-wip-20260703` は ilya の旧ブランチで、
歴史的記録として残してあるが使わない。

**実験に使われているのは 11 台中 4 台。** 残り 7 台はリポジトリを持っているだけ。

---

## 3. 実験 1 セットのライフサイクル

| # | 段階 | 誰が | 自動 |
|:--:|---|---|:--:|
| 1 | 実験の実行 | Claude Code に依頼 | — |
| 2 | 6 点必須証跡 + `server.txt` の生成 | `ExperimentManager` | **自動** |
| 3 | 証跡限定 commit + push | `git_autosync` | **自動（条件成立時）** |
| 4 | `checkpoints` / `logs` が全台へ | Syncthing | **自動（28 秒）** |
| 5 | Draft PR 作成 | `m2-sync.sh` または GitHub Actions | **自動** |
| 6 | 内容確認・Draft 解除・auto-merge 有効化 | **あなた** | review gate |
| 7 | `phase0` へ merge commit | GitHub | **自動** |
| 8 | **`make runindex`** | **全 path が Git 追跡下の clean host** → 5〜7 をもう一度実行 | — |
| 9 | 更新済み `phase0` を各台が取り込み | keeper / `m2-sync.sh` | **自動（30 分ごと）** |
| 10 | 分析 | Claude Desktop が raw URL から読む | — |

### 3（証跡の auto-commit + auto-push）

通常の trainer は完了時に `ExperimentManager.finalize()` を呼ぶ。
`train_t1b.py` も非 smoke run の完了時に同等のフックを直接呼ぶ。
自動化が実際に動く条件は次のとおり。

- 現在ブランチが `exp/*`
- ホスト別 deploy key の push 設定が存在する
- run の証跡ディレクトリに差分がある
- secret path/content scan を通過し、stage 対象に 5 MiB 超のファイルがない

stage 対象はその run の証跡ディレクトリに限定される。`git add -A` は使わず、
非 fast-forward 時も force-push しない。失敗は学習を止めず、
`~/claude-sync/sync-alerts.log` に残る。

完了後の確認:

    git status --short
    git log -1 --format='%h %s'
    tail -20 ~/claude-sync/sync-alerts.log

`EGOSURGERY_AUTOSYNC=0`、`exp/*` 外、deploy key 未設定、smoke run、
未配線 ad-hoc trainer では自動 commit されない。

### auto-sync が働かなかった場合の再実行

手動の `git add` で安全ガードを迂回しない。同じ `git_autosync` CLI を使う。
実在する値を `RUN` / `STEP` / `DESC` / `SEED` に設定してから実行する。

    (
      set -eu
      : "${RUN:?set RUN to the evidence directory}"
      : "${STEP:?set STEP}"
      : "${DESC:?set DESC}"
      : "${SEED:?set SEED}"
      test -d "$RUN"
      test -n "$(git branch --show-current)"
      OUT=$(.venv/bin/python src/egosurgery/utils/git_autosync.py "$RUN" \
        --repo-root "$PWD" --step "$STEP" --description "$DESC" --seed "$SEED")
      printf '%s\n' "$OUT"
      case "$OUT" in
        *"ok=True action=pushed"*) ;;
        *) echo "STOP: auto-sync did not push; inspect sync-alerts.log" >&2; exit 1 ;;
      esac
    )

この CLI は sync 失敗でもプロセス自体は exit 0 にするため、`action=pushed` の確認が必須。
すでに commit 済みなら keeper の次回 auto-push を待つ。

### 5〜7（Draft PR → review → GitHub auto-merge）

keeper から呼ばれる `m2-sync.sh` は 30 分ごと、GitHub Actions は `exp/**` への
push ごとに、open PR がなければ `phase0` 向け Draft PR を起票する。
先に成功した側の PR を使い、もう一方は既存 PR を検出して何もしない。
`m2-sync.sh` の失敗は `sync-alerts.log`、Actions の失敗は GitHub Actions 画面で確認する。

    (
      set -eu
      BR=$(git branch --show-current)
      test -n "$BR"
      PR=$(gh pr list --head "$BR" --base phase0 --state open --json number --jq '.[0].number')
      if [ -z "$PR" ]; then
        echo "STOP: Draft PR 未作成。Actions または次の keeper loop を確認" >&2
        exit 1
      fi
      IS_DRAFT=$(gh pr view "$PR" --json isDraft --jq .isDraft)
      if [ "$IS_DRAFT" = "true" ]; then
        gh pr ready "$PR"
      fi
      gh pr merge --auto --merge "$PR"
    )

リポジトリの auto-merge は設定済み。人手の責務は、数値と証跡をレビューし、
Draft を解除して PR ごとの auto-merge を有効にするところまで。
統合方式は **merge commit**（`--merge`）とし、Squash は使わない。
すでに auto-merge が有効な PR では最後のコマンドは不要。

review では、必須証跡の存在、数値が `metrics.json` / `per_class_ap.json` と一致すること、
秘密・大容量ファイルが混入していないこと、実験条件と研究インテグリティを確認する。
PR が未作成なら Actions の失敗と `sync-alerts.log` を確認し、次の keeper loop を待つ。

### 8（runindex の再生成）

🔴 **関連する実験 PR が `phase0` に揃った後、追跡外 run が 0 件のホストでのみ実行する。**

```bash
    (
      set -e
      SRV="${SERVERNAME:-}"
      if [ -z "$SRV" ] && [ -f .servername ]; then SRV=$(sed -n '1p' .servername); fi
      test -n "$SRV"
      BR=$(git branch --show-current)
      case "$BR" in exp/*) ;; *) echo "STOP: canonical exp/* branch ではありません" >&2; exit 1 ;; esac
      test -z "$(git status --porcelain)"
      git fetch -q origin
      test "$(git rev-list --count HEAD..origin/phase0)" = "0"

      # git 管理外 metrics.json が 1 件でもあれば harvester 汚染なので停止
      EXTRA=$(comm -23 \
        <(find experiments -type f -name metrics.json -print | sort) \
        <(git ls-files 'experiments/**/metrics.json' | sort))
      test -z "$EXTRA"

      source .venv/bin/activate
      make runindex
      SNAP=$(mktemp -d)
      cp -a runindex "$SNAP/runindex.first"
      make runindex
      diff -qr "$SNAP/runindex.first" runindex
      echo "IDEMPOTENT OK"

      # index.csv の全 path が Git 追跡下であることを確認する
      python - <<PY
import csv
import subprocess

with open("runindex/index.csv", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
untracked = []
for row in rows:
    path = (row.get("path") or "").strip()
    if not path or subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode:
        untracked.append(path or "(空)")
if untracked:
    print("STOP: 追跡外 path", *untracked, sep="\n  ")
    raise SystemExit(1)
print(f"TRACKED PATHS OK: {len(rows)}")
PY

      git add --dry-run -- runindex/
      git add -- runindex/
      git diff --cached --stat
      git commit -m "chore(runindex): regenerate"
    )
```

keeper が 30 分以内に auto-push + Draft PR 作成する。急ぐ場合だけ、現在ブランチを
確認して `git push origin "HEAD:refs/heads/$BR"`。
その後は 5〜7（review → Draft 解除 → GitHub auto-merge）をもう一度通し、
runindex PR の merge 完了を確認してから分析へ進む。

**なぜ clean host か**: harvester は git ではなく**ディスクを走査する**。
lecun / efros / andrew には Git 管理外の退避 run が存在し、そこで回すと index が食い違う。
2026-08-08 の実測では bengio の 751 run 全件が Git 追跡下だった。
ホスト名を固定せず、上の全 path 検査で毎回この前提を確認する。

### 9（各台への `phase0` 取り込み）

keeper が 30 分ごとに `m2-sync.sh` を実行する。作業ブランチに追跡変更がなく、
未追跡ファイルが取り込みを阻害しなければ、`origin/phase0` を自動 merge し、
その merge commit も auto-push する。通常は MacBook からの一括 merge は不要。

各ホストでの確認:

    git fetch -q origin
    git rev-list --count HEAD..origin/phase0
    tail -20 ~/claude-sync/sync-alerts.log

`behind=0` 相当（上の count が `0`）なら取り込み済み。追跡変更、未追跡阻害、
merge conflict がある場合は自動操作を止め、アラートを残す。削除や force 操作はしない。

---

## 4. 🔴 落とし穴（すべて実際に起きたもの）

| # | 落とし穴 | 実例 | 対策 |
|:--:|---|---|---|
| **1** | **auto-sync の失敗を見落とす** | lecun で 72 run（`selection_noise`）が **1 か月未 push**。自動化前の唯一の実際の消失リスクだった | 完了後に `git status` と `sync-alerts.log` を確認 |
| **2** | **`/tmp` を出力先にする** | T1b-FiLM の構造化結果が消失（Bengio 側）。lecun の `/tmp` に原本が残っていたため救出できたが、**再起動していれば永久に失われていた** | 出力先を `experiments/` 配下に |
| **3** | **`ExperimentManager` / autosync 配線を通さない** | Bengio の T1b が直叩きで走り `experiments/` に登録されず、**runindex から見えなかった** | 原則 `ExperimentManager`、ad-hoc trainer は `git_autosync` を明示配線 |
| **4** | **`git add -A` / `git add experiments/`** | efros で `*.npz` 414MB、philip で `data/hts_reconstruction/` 599MB がコミット可能な状態だった | パス明示 + `--dry-run` でサイズ確認 |
| **5** | **追跡外 run を持つホストで `make runindex`** | lecun で回すと退避 34 run が解析対象に混入する（B-29） | 全 path が Git 追跡下の clean host でのみ実行 |
| **6** | **証跡の取りこぼし** | lecun で `git_commit.txt` / `server.txt` が 102 件未追跡。`g2_followup` 30 run の `commit` / `host` が runindex 上で全滅していた | finalize 後と手動 commit 時に `git status` を確認 |
| **7** | **`third_party` はどこにも乗らない** | git にも Syncthing にも乗らず、philip の 9 fork / efros 31 実装 / lecun 28 / Bengio 22 が各 1 台にしか無かった | 変更したら `third_party_snapshot/<host>/` に保全 |
| **8** | **Draft のまま待つ** | Draft PR は GitHub auto-merge の対象にならない | review 後に Draft 解除 + PR ごとの auto-merge 有効化 |

### 未追跡ファイルが merge を止めることがある

Syncthing が配ったファイルと、他ホストが git に回収した同じファイルが
同じパスを占めると、**git は内容がバイト単位で同一でも上書きを拒否する**。

まず最新 ref を取得し、NUL 区切りで阻害パスと内容一致を**表示だけ**する。

    git fetch -q origin
    .venv/bin/python - <<'PY'
    import os
    import subprocess

    def git_bytes(*args: str) -> bytes:
        return subprocess.check_output(["git", *args])

    untracked = set(git_bytes("ls-files", "-z", "--others", "--exclude-standard").split(b"\0"))
    incoming = set(git_bytes("ls-tree", "-rz", "--name-only", "origin/phase0").split(b"\0"))
    for raw in sorted((untracked & incoming) - {b""}):
        path = os.fsdecode(raw)
        local = subprocess.check_output(["git", "hash-object", "--", path], text=True).strip()
        remote = subprocess.check_output(
            ["git", "rev-parse", f"origin/phase0:{path}"], text=True
        ).strip()
        print("SAME" if local == remote else "DIFF", repr(path))
    PY

🔴 **`DIFF` が 1 件でもあれば停止する。`SAME` のみでも自動削除しない。**
Syncthing 下の削除は他ホストへ伝播する場合と復元される場合があり、時間差に依存する
手順は安全保証にならない。削除が必要なら、対象・影響範囲・永続バックアップ・戻し方を
日本語で提示して明示承認を得た後、個別に処理する。keeper は常に skip のまま保つ。

---

## 5. 状態確認と障害対応

旧手順が依存していた MacBook ローカルの一括管理スクリプトはリポジトリ管理外である。
本書の正規手順や実装根拠にはせず、以下のリポジトリ標準コマンドで確認する。

### 各ホストの非破壊チェック

`git fetch` はワークツリーを変えないが、remote-tracking ref と `FETCH_HEAD` は更新する。

    (
      set -e
      BR=$(git branch --show-current)
      test -n "$BR"
      git status --short
      printf 'branch=%s\n' "$BR"
      git fetch -q origin
      printf 'behind_phase0=%s\n' "$(git rev-list --count HEAD..origin/phase0)"
      if git rev-parse --verify -q "origin/$BR" >/dev/null; then
        printf 'ahead_remote=%s\n' "$(git rev-list --count "origin/$BR..HEAD")"
      else
        echo 'remote_branch=MISSING'
      fi
      tail -50 ~/claude-sync/sync-alerts.log
    )

確認するもの:

- 現在ブランチがそのホストの定位置 `exp/*`
- 追跡変更が残っていない
- `origin/phase0` に対する behind が `0`
- remote branch に対する ahead が `0`
- `auto-merge skip` / `auto-push失敗` / `auto-PR失敗` /
  `git_autosync aborted` が未解決でない

keeper は衝突、追跡変更、未追跡阻害を検出すると安全側に skip/abort する。
アラートの原因を解消した後、次の 30 分ループを待つ。削除が必要なケースは
前節の非破壊診断を行い、`DIFF` があれば停止する。

---

## 6. 環境

### `SERVERNAME` の設定場所

`.profile`（bash ログイン）と `.zshenv`（zsh 全モード）の**両方**に置く。
`.bashrc` / `.zshrc` は対話シェルでしか読まれない。

`resolve_server_name()`（`src/egosurgery/utils/server_name.py`）の解決順:
`SERVERNAME` → `EGOSURGERY_SERVER_NAME` → Hydra config → `socket.gethostname()`

**未設定だと `hostname` にフォールバックする。** philip / ilya は両方 `aolab` を返すため
区別できなくなり、dlsta はコンテナ ID `084f3b0911a2` が記録される。

### remote

fetch remote は SSH（`git@github.com:takuya3h/m2.git`）。
各ホストの push は `exp/*` 用 deploy key を repo-local の `pushurl` /
`core.sshCommand` に設定する。サーバーに置かれていた汎用 PAT は 2026-08-04 に削除済み。
GitHub Actions の Draft PR 起票は、サーバーの PAT ではなく repository secret
`AUTOSYNC_PR_TOKEN` を使う。

### keeper / Syncthing

各台で `~/bin/keeper.sh` が 30 分ごとに動く。現在の役割:

- Syncthing と philip 向け SSH tunnel の死活監視
- `m2-sync.sh` と `.stignore` の自己更新
- `phase0` 上: `git merge --ff-only origin/phase0`
- 作業ブランチ上: clean なら `origin/phase0` を auto-merge
- remote に登録済みの作業ブランチ: 現在ブランチ上の commit 済み差分を auto-push
- `phase0` より ahead かつ open PR なし: Draft PR を自動起票

`m2-sync.sh` が行わないもの:

- 新しい commit の作成（実験証跡 commit は `git_autosync` の責務）
- ファイル削除、force-push、conflict の自動解決
- Draft 解除、研究内容のレビュー、PR ごとの auto-merge 有効化

keeper の auto-push は実験証跡だけに限定されない。現在の remote 登録済み作業ブランチが
`origin/<現在ブランチ>` より ahead なら、コード・文書・runindex の commit も送る。
したがって、作りかけを commit したまま定位置ブランチに残さない。

`m2-sync.sh` のサーバー名解決順は `SERVERNAME` → repo 直下 `.servername` →
`hostname`。`philip` / `ilya` では `.servername` も正しく設定する。

---

## 7. 分析（Claude Desktop 側）

解析は公開リポジトリの raw URL から `runindex/*.csv` を読む。

| ファイル | 単位 | 用途 |
|---|---|---|
| `index.csv` | 1 run | 「この run は何だったか」 |
| **`experiments.csv`** | **1 実験**（seed 集約後） | **論文 Table の 1 行。Δ・σ・判定** |
| `per_class.csv` | 1 run × 1 クラス | クラス別の内訳 |
| `verdicts.csv` | 1 実験 × 1 指標 | 「M2研究計画」§10.1 の有意判定 |

⚠️ **raw URL はキャッシュされる。** 最新を確実に読むには commit SHA を直指定する。

    https://raw.githubusercontent.com/takuya3h/m2/<SHA>/runindex/index.csv

SHA は `gh api repos/takuya3h/m2/commits/phase0 --jq .sha` で取れる。

---

## 8. 未決定（保留中）

| # | 論点 | 選択肢 |
|:--:|---|---|
| 1 | **σ 規約（ddof）** | 標本σ（推奨）/ 母集団σ / 併記 |
| 2 | ad-hoc trainer の autosync 配線範囲 | 未配線スクリプトを順次 `ExperimentManager` 化 / 直接配線 / 手動維持 |
| 3 | 定期同期の頻度 | 週次 / 月次 / behind 閾値超過時 / 手動 |
| 4 | `third_party` の恒久管理 | submodule / `src/` 移設 / 別リポジトリ / snapshot 継続 |
| 5 | `logs/` の二重管理 | git 追跡と Syncthing 同期の境界事故 |
| 6 | 実験に使うホストの整理 | 11 台中 4 台しか使っていない |

---

## 9. 関連ドキュメント

| ファイル | 内容 |
|---|---|
| `README.md` | サーバー間同期の全体設計（層 1 / 層 2） |
| `docs/host_autosync_onboarding.md` | keeper / Syncthing の導入手順 |
| `docs/sync_automation_instr15_stage3_ilya_2026-08-05.md` | 作業ブランチ auto-merge の実装・実測 |
| `docs/sync_automation_instr15_stage4_ilya_2026-08-05.md` | auto-PR の実装・実測 |
| `docs/third_party_sync_design_2026-08-05.md` | `third_party` 同期の選択肢と現行方針 |
| `docs/host_dev_env_setup.md` | 開発 CLI ツールの構築手順（2026-07-01 の記録） |
| `docs/sync_instr09_lecun_2026-08-02.md` | 同期作業 #09 の経緯 |
| `docs/sync_phase0_merge_lecun_2026-08-02.md` | phase0 取り込みの完全記録・Syncthing の挙動 |
| `runindex/README.md` | runindex の生成規則・ホストによる差異 |
| `runindex/anomalies/backlog.md` | 分析基盤の既知の課題（34 件） |

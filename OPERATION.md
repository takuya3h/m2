# 実験運用の手引き（2026-08-05 版）

本ドキュメントは 2026-08-02〜05 の全サーバー同期作業で確定した運用を記録する。
`README.md` のサーバー間同期セクションと重複する部分があるが、
**実験を 1 セット回すときに何をするか**という視点で書いている。

---

## 1. 全体像 — 二層設計

成果物は**種類によって別の経路**で全サーバーに配られる。

| 層 | 対象 | 経路 | 到達時間 | 人手 |
|---|---|---|---|:--:|
| **Syncthing** | `checkpoints/` `logs/` `predictions/` `visualizations/` `*.pth` `*.pt` `*.npy` | 自動（星型・中心 philip） | **28 秒**（2026-08-04 実測・全 10 台） | **0** |
| **git** | 6 点証跡・コード・設定・`runindex/` | commit → push → PR → phase0 → 各台が merge | 人間の作業次第 | **3 段階** |
| どちらでもない | `.git` `.env` `data/raw` `wandb` `third_party` `data/hts_reconstruction` | — | — | — |

`.stignore`（各台）は `.stglobalignore`（phase0）から keeper が 30 分以内に自動反映する。
**2026-08-04 の伝播テストで、11 台すべてで正しく効いていることを確認済み**
（git 管理の 4 証跡は Syncthing で配られなかった）。

### 6 点証跡（`ExperimentManager` が自動生成）

```
experiments/<group>/<step>_<seq>_<desc>_seed<N>/
  ├ metrics.json       指標本体 + eval_recipe
  ├ config.yaml        設定
  ├ command.sh         実行コマンド
  ├ git_commit.txt     commit hash
  ├ per_class_ap.json  クラス別の値
  ├ notes.md           人手のメモ
  └ server.txt         実行ホスト（SERVERNAME から）
```

---

## 2. ブランチ規約

| ブランチ | 用途 | 誰が |
|---|---|---|
| **`phase0`** | **統合の幹。保護ブランチ**（PR が唯一の経路・`enforce_admins: true`） | 統合時のみ |
| `exp/<サーバー名>-wip-<日付>` | **各サーバーの定位置。常にここにいる** | そのサーバー |
| `chore/*` `feat/*` | 一時作業（PR 用）。マージ後に削除 | 必要時 |
| `master` `docs/plan-rewrite-2026-06` | 歴史的記録。触らない | — |

**`exp/*` は実験ごとに切らない。消さない。** そのサーバーは常に同じブランチにいる。
日付は「ブランチを作った日」で、実験の日付ではない。

### ホスト名とブランチの対応（2026-08-05 時点）

| SSH 名 | `hostname` | `SERVERNAME` | ブランチ | 実験 run |
|---|---|---|---|---:|
| lecun | `lecun` | `lecun` | `exp/lecun-wip-20260703` | **464** |
| efros | `efros` | `efros` | `exp/efros-wip-20260703` | **194** |
| philip | `aolab` | `philip` | `exp/philip-wip-20260703` | **31** |
| andrew | `Andrew` | `andrew` | `exp/Andrew-wip-20260703` | **3** |
| ilya | `aolab` | `ilya` | `exp/ilya-wip-20260804` | 0（統合担当） |
| bengio | `Bengio` | `bengio` | `exp/Bengio-wip-20260703` | 0 |
| he | `he` | `he` | `exp/he-wip-20260804` | 0 |
| adam | `adam` | `adam` | `exp/adam-wip-20260804` | 0 |
| hinton | `Hinton` | `hinton` | `exp/hinton-wip-20260804` | 0 |
| ian | `ian` | `ian` | `exp/ian-wip-20260804` | 0 |
| dlsta | `084f3b0911a2` | `dlstation` | `exp/dlstation-wip-20260804` | 0 |

**philip と ilya は `hostname` が同じ `aolab`。** 別 IP（`.150` / `.63`）の別マシンで、
`SERVERNAME` で区別する。`exp/aolab-wip-20260703` は ilya の旧ブランチで、
歴史的記録として残してあるが使わない。

**実験に使われているのは 11 台中 4 台。** 残り 7 台はリポジトリを持っているだけ。

---

## 3. 実験 1 セットのライフサイクル

| # | 段階 | 誰が | 自動 |
|:--:|---|---|:--:|
| 1 | 実験の実行 | Claude Code に依頼 | — |
| 2 | 6 点証跡の生成 | `ExperimentManager` | **自動** |
| 3 | `checkpoints` / `logs` が全台へ | Syncthing | **自動（28 秒）** |
| 4 | **commit** | **あなた** | — |
| 5 | **push** | **あなた** | — 🔴 飛ばすと消失リスク |
| 6 | **PR 作成** | **あなた** | — |
| 7 | **PR マージ** | **あなた（Web UI）** | — |
| 8 | **`make runindex`** | **ilya でのみ** → PR → マージ | — |
| 9 | 各台が取り込み | MacBook から一括 | — |
| 10 | 分析 | Claude Desktop が raw URL から読む | — |

### 4〜5（commit と push）

    cd /home/ubuntu/slocal2/m2
    git status --porcelain experiments/ | head

    # 🔴 git add -A を使わない。パス明示 + --dry-run で実測
    git add --dry-run experiments/<group>/<run>
    du -sh experiments/<group>/<run>

    git add experiments/<group>/<run>
    git status --short
    git commit -m "exp(<step>): <一行で内容>"
    git push origin $(git branch --show-current)

### 6〜7（PR）

    gh pr list --head $(git branch --show-current) --state open   # 重複を先に確認
    gh pr create --base phase0 --head $(git branch --show-current) \
      --title "..." --body "..."

マージは GitHub Web UI で **Create a merge commit**（Squash は使わない）。

### 8（runindex の再生成）

🔴 **ilya でのみ実行する。**

    # ilya
    git fetch origin && git merge origin/phase0
    make runindex
    git status --porcelain runindex/

    # 冪等性の確認（必須）
    make runindex && git status --porcelain runindex/ > /tmp/a
    make runindex && git status --porcelain runindex/ > /tmp/b
    diff /tmp/a /tmp/b && echo "IDEMPOTENT OK"

    git add runindex/ && git commit -m "chore(runindex): regenerate"
    git push origin exp/ilya-wip-20260804
    # → PR → マージ

**なぜ ilya か**: harvester は git ではなく**ディスクを走査する**。
lecun / efros / andrew には git 管理外の退避 run が存在し
（`.gitignore:143-162` で除外・合計 ~5.6GB）、そこで回すと index が食い違う。
ilya はディスク 720 = git 追跡 720 で差がゼロ（backlog B-29）。

### 9（全台取り込み）— MacBook から

    for h in lecun efros philip ilya bengio andrew he adam hinton ian dlsta; do
      printf "%-9s " "$h"
      ssh -o ClearAllForwardings=yes -o BatchMode=yes "$h" '
        cd ~/slocal2/m2 2>/dev/null || cd ~/slocal/m2
        git fetch -q origin
        B=$(git log --oneline HEAD..origin/phase0 | wc -l | tr -d " ")
        if [ "$B" != "0" ]; then
          git merge -q origin/phase0 2>&1 | tail -2
          git push -q origin $(git branch --show-current) 2>/dev/null
        fi
        echo "behind=$(git log --oneline HEAD..origin/phase0 | wc -l | tr -d " ")"'
    done

---

## 4. 🔴 落とし穴（すべて実際に起きたもの）

| # | 落とし穴 | 実例 | 対策 |
|:--:|---|---|---|
| **1** | **push を飛ばす** | lecun で 72 run（`selection_noise`）が **1 か月未 push**。唯一の実際の消失リスクだった | 実験セット完了ごとに push |
| **2** | **`/tmp` を出力先にする** | T1b-FiLM の構造化結果が消失（Bengio 側）。lecun の `/tmp` に原本が残っていたため救出できたが、**再起動していれば永久に失われていた** | 出力先を `experiments/` 配下に |
| **3** | **`ExperimentManager` を通さない** | Bengio の T1b が直叩きで走り `experiments/` に登録されず、**runindex から見えなかった** | 起動は `ExperimentManager` 経由で |
| **4** | **`git add -A` / `git add experiments/`** | efros で `*.npz` 414MB、philip で `data/hts_reconstruction/` 599MB がコミット可能な状態だった | パス明示 + `--dry-run` でサイズ確認 |
| **5** | **他ホストで `make runindex`** | lecun で回すと退避 34 run が解析対象に混入する（B-29） | ilya でのみ |
| **6** | **証跡の取りこぼし** | lecun で `git_commit.txt` / `server.txt` が 102 件未追跡。`g2_followup` 30 run の `commit` / `host` が runindex 上で全滅していた | commit 時に `git status` を確認 |
| **7** | **`third_party` はどこにも乗らない** | git にも Syncthing にも乗らず、philip の 9 fork / efros 31 実装 / lecun 28 / Bengio 22 が各 1 台にしか無かった | 変更したら `third_party_snapshot/<host>/` に保全 |

### 未追跡ファイルが merge を止めることがある

Syncthing が配ったファイルと、他ホストが git に回収した同じファイルが
同じパスを占めると、**git は内容がバイト単位で同一でも上書きを拒否する**。

    # 阻害要因の判定
    git ls-files --others --exclude-standard | while read -r f; do
      if git rev-parse "origin/phase0:$f" >/dev/null 2>&1; then
        [ "$(git hash-object "$f")" = "$(git rev-parse "origin/phase0:$f")" ] \
          && echo "SAME $f" || echo "DIFF $f"
      fi
    done | tee /tmp/ov.txt | awk '{print $1}' | sort | uniq -c

🔴 **`DIFF` が 1 件でもあれば停止**。`SAME` のみなら:

    grep '^SAME ' /tmp/ov.txt | cut -d' ' -f2- > /tmp/same.txt
    tar czf /tmp/ov_backup.tgz -T /tmp/same.txt      # 必ずバックアップ
    xargs -a /tmp/same.txt rm -- && git merge origin/phase0

⚠️ **`rm` と `merge` を `&&` で連結する。** Syncthing が約 40 秒で巻き戻すため
（lecun の実測では 264ms で完了し先行できる）。

### 削除の挙動は「起点」で変わる

| 状況 | 結果 |
|---|---|
| **片側だけの削除**（他ホストが原本を保持） | **約 40 秒で巻き戻る** |
| **同期された削除**（正規の削除操作として発信） | **伝播する。巻き戻らない** |

上の回避策（`&&` 連結）が必要なのは前者のみ。
実験成果を意図的に削除するときは通常の `rm` でよい。

---

## 5. 便利なスクリプト（MacBook）

### 全台の状態確認（読み取り専用）

    ./check_all_hosts.sh

3 つの表を出す。**「🔴 要確認」に何も出なければ全台正常。**

| 自動検出するもの |
|---|
| `phase0` をチェックアウト中（規約違反） |
| 追跡ファイルの変更が残っている |
| `index.csv` / backlog の行数が期待と違う |
| stash が残っている |
| remote が SSH でない |
| 非対話シェルで `SERVERNAME` が未設定 |
| syncthing / keeper が動いていない |

### 全台の状態を揃える

    ./sync_all_hosts.sh              # dry-run
    ./sync_all_hosts.sh --apply      # 実行

定位置ブランチへの復帰・`SERVERNAME` の設定・`phase0` の取り込みを行う。
**追跡ファイルに変更があるホストは skip** し、`DIFF` があれば停止する。

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

全 11 台が SSH（`git@github.com:takuya3h/m2.git`）。PAT は 2026-08-04 に削除済み。

### keeper / Syncthing

各台で `~/bin/keeper.sh` が 30 分ごとに動く。行うのは以下のみ。

- 作業ブランチ上: `git fetch -q origin phase0:phase0`（ワークツリー不干渉）
- `phase0` 上: `git merge --ff-only origin/phase0`

**`commit` / `push` / 作業ブランチ上の `merge` は自動化されていない。**

---

## 7. 分析（Claude Desktop 側）

解析は公開リポジトリの raw URL から `runindex/*.csv` を読む。

| ファイル | 単位 | 用途 |
|---|---|---|
| `index.csv` | 1 run | 「この run は何だったか」 |
| **`experiments.csv`** | **1 実験**（seed 集約後） | **論文 Table の 1 行。Δ・σ・判定** |
| `per_class.csv` | 1 run × 1 クラス | クラス別の内訳 |
| `verdicts.csv` | 1 実験 × 1 指標 | §10.1 の有意判定 |

⚠️ **raw URL はキャッシュされる。** 最新を確実に読むには commit SHA を直指定する。

    https://raw.githubusercontent.com/takuya3h/m2/<SHA>/runindex/index.csv

SHA は `gh api repos/takuya3h/m2/commits/phase0 --jq .sha` で取れる。

---

## 8. 未決定（保留中）

| # | 論点 | 選択肢 |
|:--:|---|---|
| 1 | **σ 規約（ddof）** | 標本σ（推奨）/ 母集団σ / 併記 |
| 2 | push の自動化 | keeper に「コミット済みなら push」を追加するか |
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
| `docs/host_dev_env_setup.md` | 開発 CLI ツールの構築手順（2026-07-01 の記録） |
| `docs/sync_instr09_lecun_2026-08-02.md` | 同期作業 #09 の経緯 |
| `docs/sync_phase0_merge_lecun_2026-08-02.md` | phase0 取り込みの完全記録・Syncthing の挙動 |
| `runindex/README.md` | runindex の生成規則・ホストによる差異 |
| `runindex/anomalies/backlog.md` | 分析基盤の既知の課題（34 件） |

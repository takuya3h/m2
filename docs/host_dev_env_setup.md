> **記録の性質について（2026-08-05 追記）**
>
> 本ドキュメントは **2026-07-01 時点の記録**であり、philip サーバーに
> 開発ツール環境を構築した際の手順です。2026-08-04 に stash から救出しました
> （それまで git にもディスクにも存在しませんでした）。
>
> **研究運用（ブランチ規約 / SERVERNAME / runindex / Syncthing 二層設計）には
> 一切言及していません。** それらは README.md と docs/host_autosync_onboarding.md
> が扱います。本ドキュメントの守備範囲は開発 CLI ツールの導入のみです。
>
> **陳腐化している可能性がある箇所:**
> - ZeroTier IP `192.168.196.150`（philip は現在 Docker コンテナ内で `172.17.0.20`）
> - npm パッケージのバージョン（`gemini-cli@0.43.0` 等）
>
> **今も有効な情報:**
> - `--rsync-path=/home/linuxbrew/.linuxbrew/bin/rsync` の指定が必要な点
> - GitHub SSH 鍵の生成・登録手順（指示書 #09 の PAT → SSH 化と同じ経路）
> - `~/.agents/` を実体として各 CLI から symlink する設計

# Philip サーバー セットアップガイド

別サーバー（philip, ZeroTier IP: `192.168.196.150`, user: `ubuntu`）に、本サーバー（Bengio）と同等の作業環境を構築するための手順書。

> **本ドキュメントの対象外**
> - 基本 apt 群（build-essential / git / curl など）
> - zsh + oh-my-zsh
> - pyenv + Python
> - CUDA / cuDNN
>
> これらは既に整備済み or 別途対応の前提。

---

## 0. 前提

- 移動先サーバー (philip) に SSH でログインできること
  - パスワード認証で `ssh philip` が通る状態
- 本サーバーの `~/.ssh/config` に `philip` エイリアスが設定済み
- ZeroTier で疎通済み

```bash
# 疎通確認
ping -c 3 192.168.196.150
ssh philip "hostname && whoami"
```

---

## 1. Homebrew (Linuxbrew) インストール

Homebrew は他ツールの基盤となるため最優先。

### philip 上で実行

```bash
ssh philip
# 以下 philip 上で実行
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

インストール後、PATH を通す：

```bash
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.zshrc
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
brew --version   # 確認
```

---

## 2. brew で rsync / gh / jq をインストール

```bash
# philip 上
brew install rsync gh jq
which rsync   # /home/linuxbrew/.linuxbrew/bin/rsync が表示されればOK
rsync --version | head -1
```

> Linuxbrew配下に置かれるため、本サーバーから rsync する際は
> `--rsync-path=/home/linuxbrew/.linuxbrew/bin/rsync` を毎回指定する。

---

## 3. GitHub SSH 鍵の作成・登録（philip 上）

git clone / push を SSH 経由で行うために、philip サーバー用の SSH 鍵ペアを発行し GitHub に登録する。

### 3.1. SSH 鍵ペアを生成

ed25519（推奨）で生成する。パスフレーズは任意（agent前提なら空でも可）。

```bash
# philip 上
ssh-keygen -t ed25519 -C "ubuntu@philip" -f ~/.ssh/id_ed25519_github
# プロンプトに従ってパスフレーズを設定（空Enterで省略可）
```

> **既存の鍵を再利用しない理由**：サーバー単位で鍵を分けると、流出時の影響範囲を限定でき、後から GitHub 側で個別失効できる。

### 3.2. ssh-agent に鍵を登録

```bash
# philip 上
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519_github
```

シェル起動時に自動で agent を立ち上げたい場合は `~/.zshrc` に追記：

```bash
cat >> ~/.zshrc << 'EOF'

# ssh-agent 自動起動
if [ -z "$SSH_AUTH_SOCK" ]; then
  eval "$(ssh-agent -s)" > /dev/null
  ssh-add ~/.ssh/id_ed25519_github 2>/dev/null
fi
EOF
```

### 3.3. `~/.ssh/config` に GitHub ホスト設定

```bash
# philip 上
mkdir -p ~/.ssh && chmod 700 ~/.ssh

cat >> ~/.ssh/config << 'EOF'

Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_github
  IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config
```

### 3.4. 公開鍵を GitHub に登録

**方法A：`gh` CLI を使う（推奨・自動）**

セクション2で `gh` がインストール済みなので、ワンコマンドで登録可能：

```bash
# philip 上
gh auth login
# 対話形式:
#   ? What account do you want to log into?         → GitHub.com
#   ? What is your preferred protocol for Git ops?  → SSH
#   ? Upload your SSH public key to your GitHub?    → ~/.ssh/id_ed25519_github.pub
#   ? Title for your SSH key?                       → philip
#   ? How would you like to authenticate gh CLI?    → Login with a web browser
# ブラウザでワンタイムコードを入力して完了
```

これだけで公開鍵が GitHub に登録され、`gh` の認証も同時に完了する。

**方法B：手動で登録**

`gh` を使わない場合：

```bash
# philip 上
cat ~/.ssh/id_ed25519_github.pub
# 出力をコピー
```

ブラウザで [https://github.com/settings/keys](https://github.com/settings/keys) → "New SSH key" → タイトル `philip` でペースト → "Add SSH key"。

### 3.5. 接続テスト

```bash
# philip 上
ssh -T git@github.com
# 期待される出力:
# Hi <your-username>! You've successfully authenticated, but GitHub does not provide shell access.
```

`Permission denied` が出る場合：
- `ssh -vT git@github.com` で詳細ログを確認
- `~/.ssh/config` の `IdentityFile` パスが正しいか
- 公開鍵が GitHub に登録されているか
- `ssh-add -l` で agent に鍵が読み込まれているか

### 3.6. git の user 情報設定

```bash
# philip 上
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
# 本サーバーと同じ値にするのが推奨
```

本サーバーの値を流用するなら：

```bash
# 本サーバー側で確認
git config --global user.name
git config --global user.email
# その値を philip 側で同じく設定
```

---

## 4. 言語ランタイム

### 4.1. nvm + Node.js

```bash
# philip 上
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash

# 新シェルを起動するか source で反映
source ~/.nvm/nvm.sh

# 本サーバーと同じバージョンを導入
nvm install 20.20.2
nvm alias default 20
node --version   # v20.20.2
```

### 4.2. Rust (cargo)

```bash
# philip 上
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env
rustc --version
```

### 4.3. uv (Python tool runner)

```bash
# philip 上
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env 2>/dev/null || export PATH="$HOME/.local/bin:$PATH"
uv --version
```

---

## 5. npm グローバルパッケージ

nvm が有効な状態（Node 20.20.2）で実行。

```bash
# philip 上
npm install -g \
  @agentmemory/agentmemory \
  @colbymchenry/codegraph \
  @google/gemini-cli \
  @openai/codex
```

確認：

```bash
npm list -g --depth=0
# 期待される一覧:
# ├── @agentmemory/agentmemory@0.9.21
# ├── @colbymchenry/codegraph@0.8.0
# ├── @google/gemini-cli@0.43.0
# ├── @openai/codex@0.133.0
# └── corepack@0.34.6
```

> npm WARN ERESOLVE / deprecated 系の警告は無視してOK。
> `added N packages` が出れば成功。

---

## 6. uv tool（Python 製ツール）

```bash
# philip 上
uv tool install semgrep
semgrep --version
```

---

## 7. Claude Code

```bash
# philip 上
curl -fsSL https://claude.ai/install.sh | bash
# ~/.local/bin/claude にインストールされる

which claude
claude --version   # 2.1.x
```

---

## 8. claude-pulse（Claude Code 用ステータスライン）

[NoobyGains/claude-pulse](https://github.com/NoobyGains/claude-pulse) は Claude Code のステータスライン拡張。本サーバーでは `~/.claude/settings.json` の `statusLine` から参照されている。

```bash
# philip 上
curl -fsSL https://raw.githubusercontent.com/NoobyGains/claude-pulse/main/install.sh | bash
```

> このインストーラは `~/.claude/plugins/cache/claude-pulse/` 配下にスクリプトを配置する。
> 本サーバーの `settings.json` を rsync で転送すると `claude_status.py` のパスが
> 参照されるため、claude-pulse は **settings.json 転送より先に** インストールしておく。

確認：

```bash
ls ~/.claude/plugins/cache/claude-pulse/claude-pulse/*/claude_status.py 2>/dev/null
# パスが解決されればOK
```

---

## 9. zmx（端末セッション永続化ツール）

`zmx` は tmux/screen 類似の軽量セッション永続化ツール。`neurosnap/tap` から brew で導入する。

```bash
# philip 上
brew install neurosnap/tap/zmx
# または以下の2ステップでも可:
#   brew tap neurosnap/tap
#   brew install zmx

which zmx          # /home/linuxbrew/.linuxbrew/bin/zmx
zmx version        # zmx 0.5.0 ...
zmx help           # コマンド一覧が表示されればOK
```

### zsh補完（任意）

```bash
# philip 上
mkdir -p ~/.zsh/completions
zmx completions zsh > ~/.zsh/completions/_zmx

# ~/.zshrc に補完パスを追加（既に設定済みなら不要）
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc
echo 'autoload -U compinit && compinit' >> ~/.zshrc
```

---

## 10. failog（vibe coding 用エラーログ機能のセットアップ）

[takuya3h/dotfiles](https://github.com/takuya3h/dotfiles) が提供する `failog` 関数を、ワンライナーで philip に導入する。

```bash
# philip 上で実行
curl -fsSL https://raw.githubusercontent.com/takuya3h/dotfiles/main/install.sh | bash
source ~/.zshrc
```

### install.sh の動作

1. `~/slocal2/dotfiles/` に clone（既存なら `git pull --ff-only`）
2. `~/.zshrc` に `source ~/slocal2/dotfiles/zsh/failog.zsh` を追記（重複チェック付き）

### 確認

```bash
# philip 上
which failog              # zsh function として認識されているか
type failog               # 関数定義が見える
ls ~/slocal2/dotfiles/zsh/failog.zsh   # ファイル存在確認
```

`failog` が定義されていない場合は、新しい zsh セッションを開くか `source ~/.zshrc` を実行する。

---

## 11. 設定ファイル同期（本サーバー → philip）

ここから本サーバー (Bengio) 側で実行。`--rsync-path` で philip 側 rsync の絶対パスを明示。

### 11.1. AGENTS ディレクトリ（共通エージェント設定の実体）

本サーバーでは、3つのCLIツール（Claude / Codex / Gemini）の `AGENTS.md` 系設定ファイル と `skills/` ディレクトリが、すべて `~/.agents/` 配下の実体への symlink になっている。

```
~/.claude/CLAUDE.md         → ~/.agents/AGENTS.md
~/.claude/skills            → ~/.agents/skills
~/.codex/AGENTS.md          → ~/.agents/AGENTS.md
~/.codex/skills/my_skills   → ~/.agents/skills
~/.gemini/GEMINI.md         → ~/.agents/AGENTS.md
```

**転送戦略**：`~/.agents/` の実体を1度だけ送り、各ツール側では symlink を philip 上で再作成する。これにより:
- 同じファイルの重複転送を回避（特に skills/ ディレクトリ）
- symlink がリンク切れになるリスクを排除
- 各CLIから「単一の真の設定ソース」を参照する構造を philip でも再現

```bash
# 本サーバー側で実行 — 最初に実体を送る
rsync -avzh \
  --rsync-path=/home/linuxbrew/.linuxbrew/bin/rsync \
  ~/.agents/ \
  philip:~/.agents/
```

### 11.2. Claude Code 設定（**機密情報・symlink を除外して転送**）

> **除外するもの（機密 / プロジェクト状態 / キャッシュ）**
> - `.credentials.json` — 認証情報。philip で `claude` 初回起動時にログインし直す
> - `history.jsonl` — 会話履歴（プロジェクト固有）
> - `cache/` — キャッシュ（再生成可）
> - `projects/` — プロジェクトごとの状態
> - `file-history/` — ファイル編集履歴
> - `paste-cache/` — クリップボードキャッシュ
> - `ide/` — IDE連携状態
> - `mcp-needs-auth-cache.json` — MCP認証キャッシュ
>
> **除外するもの（symlink、philip 上で再作成する）**
> - `CLAUDE.md` — `~/.agents/AGENTS.md` への symlink
> - `skills` — `~/.agents/skills` への symlink
>
> **転送される主な設定**
> - `settings.json` — グローバル設定（plugins、hooks、permissions）
> - `settings.local.json` — ローカル設定。**`Bash(*)` 等のpermission一括許可**を含む
> - `commands/` — カスタムコマンド
> - `plugins/` — プラグイン設定

```bash
rsync -avzh \
  --rsync-path=/home/linuxbrew/.linuxbrew/bin/rsync \
  --exclude='.credentials.json' \
  --exclude='history.jsonl' \
  --exclude='cache/' \
  --exclude='projects/' \
  --exclude='file-history/' \
  --exclude='paste-cache/' \
  --exclude='ide/' \
  --exclude='mcp-needs-auth-cache.json' \
  --exclude='security_warnings_state_*.json' \
  --exclude='backups/' \
  --exclude='downloads/' \
  --exclude='CLAUDE.md' \
  --exclude='skills' \
  ~/.claude/ \
  philip:~/.claude/
```

> `~/.claude.json` は **転送しない**（プロジェクトごとの状態を含むため）。

#### Bash コマンド確認スキップの仕組み

本サーバーでは `settings.local.json` 内の以下のpermissionにより、Bashコマンド実行時の確認プロンプトをスキップしている：

```json
{
  "permissions": {
    "allow": [
      "*",
      "Bash(*)"
    ]
  }
}
```

上記rsyncで `settings.local.json` が転送されると、philip でも同じ挙動になる。

**転送後の確認**：

```bash
ssh philip "grep -A2 'Bash(\\*)' ~/.claude/settings.local.json"
# "Bash(*)" がallowリストにあればOK
```

**もし手動で設定したい場合**（rsyncを使わずに有効化）：

```bash
ssh philip
# philip 上で
mkdir -p ~/.claude
cat > ~/.claude/settings.local.json << 'EOF'
{
  "permissions": {
    "allow": [
      "*",
      "Bash(*)"
    ]
  }
}
EOF
```

> ⚠️ **`Bash(*)` は任意のBashコマンドを無確認で実行可能にする強い権限**。
> 信頼できる環境（自分専用サーバーなど）でのみ使用すること。
> 共有サーバーやproduction環境では、より細かい許可リスト（`Bash(git *)`、`Bash(ls *)` など）に絞る方が安全。

### 11.3. Codex 設定（`~/.codex/`、**機密情報・symlink を除外**）

> **除外するもの（機密 / 状態 / キャッシュ）**
> - `auth.json` — 認証情報。philip で再認証する
> - `cache/` — キャッシュ
> - `*.sqlite*` — ログ・状態・goals 等のローカル DB
> - `sessions/`、`session_index.jsonl`、`history.jsonl` — セッション・履歴
> - `log/` — ログファイル
> - `shell_snapshots/` — シェル状態
> - `tmp/`、`.tmp/` — 一時ファイル
> - `models_cache.json` — モデルキャッシュ（再生成可）
> - `installation_id`、`.personality_migration` — マシン固有
> - `*.bak-*` — バックアップ
>
> **除外するもの（symlink、philip 上で再作成する）**
> - `AGENTS.md` — `~/.agents/AGENTS.md` への symlink
> - `skills/my_skills` — `~/.agents/skills` への symlink
>
> **転送される主な設定**：`config.toml`、`plugins/`、`rules/`、`skills/`（my_skills を除く）、`version.json`、`memories/`

```bash
rsync -avzh \
  --rsync-path=/home/linuxbrew/.linuxbrew/bin/rsync \
  --exclude='auth.json' \
  --exclude='cache/' \
  --exclude='*.sqlite' \
  --exclude='*.sqlite-shm' \
  --exclude='*.sqlite-wal' \
  --exclude='sessions/' \
  --exclude='session_index.jsonl' \
  --exclude='history.jsonl' \
  --exclude='log/' \
  --exclude='shell_snapshots/' \
  --exclude='tmp/' \
  --exclude='.tmp/' \
  --exclude='models_cache.json' \
  --exclude='installation_id' \
  --exclude='.personality_migration' \
  --exclude='*.bak-*' \
  --exclude='AGENTS.md' \
  --exclude='skills/my_skills' \
  ~/.codex/ \
  philip:~/.codex/
```

### 11.4. Gemini 設定（`~/.gemini/`、**機密情報・symlink を除外**）

> **除外するもの（機密 / 状態 / キャッシュ）**
> - `oauth_creds.json` — OAuth 認証情報
> - `google_accounts.json` — Google アカウント情報
> - `history/` — 会話履歴
> - `state.json` — ローカル状態
> - `projects.json` — プロジェクト状態
> - `trustedFolders.json` — トラストリスト（ホスト固有）
> - `tmp/` — 一時ファイル
> - `installation_id` — マシン固有 ID
>
> **除外するもの（symlink、philip 上で再作成する）**
> - `GEMINI.md` — `~/.agents/AGENTS.md` への symlink
>
> **転送される主な設定**：`settings.json`、`antigravity/`

```bash
rsync -avzh \
  --rsync-path=/home/linuxbrew/.linuxbrew/bin/rsync \
  --exclude='oauth_creds.json' \
  --exclude='google_accounts.json' \
  --exclude='history/' \
  --exclude='state.json' \
  --exclude='projects.json' \
  --exclude='trustedFolders.json' \
  --exclude='tmp/' \
  --exclude='installation_id' \
  --exclude='GEMINI.md' \
  ~/.gemini/ \
  philip:~/.gemini/
```

### 11.5. symlink の再作成（philip 上）

`~/.agents/` の実体を参照するように、各CLIから symlink を張り直す。

```bash
ssh philip
# 以下 philip 上で実行

# Claude
ln -sfn ~/.agents/AGENTS.md ~/.claude/CLAUDE.md
ln -sfn ~/.agents/skills     ~/.claude/skills

# Codex
ln -sfn ~/.agents/AGENTS.md ~/.codex/AGENTS.md
mkdir -p ~/.codex/skills
ln -sfn ~/.agents/skills     ~/.codex/skills/my_skills

# Gemini
ln -sfn ~/.agents/AGENTS.md ~/.gemini/GEMINI.md

# 確認
ls -la ~/.claude/CLAUDE.md ~/.claude/skills \
       ~/.codex/AGENTS.md  ~/.codex/skills/my_skills \
       ~/.gemini/GEMINI.md
# すべて ~/.agents/... を指していて、リンク切れ（赤色表示）になっていなければOK
```

> `ln -sfn` の `-f`（強制上書き）と `-n`（既存ディレクトリへの symlink を中身に降りずに置換）の組み合わせで、再実行しても安全に張り直せる。

### 11.6. Claude Code / Codex / Gemini 初回ログイン（philip 上）

転送後、認証は philip 上でやり直す：

```bash
ssh philip

# Claude Code
claude
# → ブラウザ認証フロー

# Codex（必要なら）
codex
# → 認証フロー

# Gemini CLI（必要なら）
gemini
# → google アカウントログイン
```

---

## 12. 動作確認チェックリスト

philip 上で以下を順に確認：

```bash
# シェルとPATH
echo $SHELL
which brew rsync gh jq node npm uv cargo rustc claude semgrep zmx

# バージョン整合性
brew --version
node --version          # v20.20.2
npm --version
uv --version
rustc --version
claude --version        # 2.1.x
semgrep --version
zmx version             # zmx 0.5.0

# claude-pulse スクリプト存在確認
ls ~/.claude/plugins/cache/claude-pulse/claude-pulse/*/claude_status.py 2>/dev/null \
  && echo "✓ claude-pulse OK" || echo "✗ claude-pulse 未配置"

# failog 関数の存在確認
type failog >/dev/null 2>&1 && echo "✓ failog OK" || echo "✗ failog 未定義"

# GitHub SSH接続
ssh -T git@github.com   # "Hi <username>!" が返ればOK
gh auth status          # ログイン状態確認

# symlink が ~/.agents/ を指しているか確認
ls -la ~/.claude/CLAUDE.md ~/.claude/skills \
       ~/.codex/AGENTS.md  ~/.codex/skills/my_skills \
       ~/.gemini/GEMINI.md
# いずれもリンク切れ（赤字）でなければOK

# 主要設定ファイル
ls -la ~/.codex/config.toml ~/.gemini/settings.json

# Bashコマンド確認スキップ設定が転送されているか
grep -q 'Bash(\*)' ~/.claude/settings.local.json && echo "✓ Bash skip有効" || echo "✗ 未設定"

# npm global
npm list -g --depth=0
```

---

## 13. 補足

### 設定ファイルの同期方針

| ファイル/ディレクトリ | 転送 | 理由 |
|---|---|---|
| `~/.zshrc` | ❌ しない | philip 側で個別管理 |
| `~/.agents/` | ✅ する | AGENTS.md / skills 一式 |
| `~/.claude/` 主要ファイル | ✅ する（除外あり） | グローバル設定・コマンド・プラグイン |
| `~/.codex/` 主要ファイル | ✅ する（除外あり） | Codex 設定・plugins・skills・rules |
| `~/.gemini/` 主要ファイル | ✅ する（除外あり） | Gemini CLI 設定・antigravity |
| `~/.claude/.credentials.json` | ❌ しない | 認証情報、再ログイン |
| `~/.codex/auth.json` | ❌ しない | 認証情報、再ログイン |
| `~/.gemini/oauth_creds.json` | ❌ しない | OAuth情報、再ログイン |
| `~/.gemini/google_accounts.json` | ❌ しない | Googleアカウント情報 |
| 各CLIの `projects/` / `sessions/` / `history*` / `cache/` | ❌ しない | プロジェクト状態・履歴・キャッシュ |
| `~/.claude.json` | ❌ しない | プロジェクト状態を含む |
| `~/.ssh/id_ed25519_github` | ❌ しない | **秘密鍵は転送しない**、philip 上で新規生成 |
| `~/.ssh/config` (philip外接続用) | 任意 | philip から他サーバーに繋ぐ予定があれば |

### バージョン管理ツールの設定追記

`~/.zshrc` を rsync で同期すれば pyenv/nvm/cargo/brew の初期化行も持ち込まれるが、本サーバーの `.zshrc` を確認しておく：

```bash
# 想定される初期化行（本サーバー .zshrc より）
eval "$(pyenv init --path)"
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv zsh)"
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
export PATH="$HOME/.local/bin:$PATH"
export PATH="$HOME/.cargo/bin:$PATH"
```

これらの行が philip 側 `.zshrc` にあり、対応するディレクトリが存在することを確認。

---

## 14. ロールバック・再実行

各ステップは独立しており、失敗しても影響範囲は限定的：

- brew パッケージ：`brew uninstall <pkg>`
- nvm Node：`nvm uninstall 20.20.2`
- cargo：`rustup self uninstall`
- uv：`rm -rf ~/.local/bin/uv ~/.local/bin/uvx`
- Claude：`rm -rf ~/.claude ~/.local/bin/claude`
- npm global：`npm uninstall -g <pkg>`
- claude-pulse：`rm -rf ~/.claude/plugins/cache/claude-pulse`、`settings.json` の `statusLine` 設定も削除
- zmx：`brew uninstall zmx && brew untap neurosnap/tap`、`/tmp/zmx-*` も削除可
- failog：`rm -rf ~/slocal2/dotfiles`、`~/.zshrc` から `source ~/slocal2/dotfiles/zsh/failog.zsh` 行を削除
- GitHub SSH鍵：
  - philip 上：`rm ~/.ssh/id_ed25519_github*`、`~/.ssh/config` の該当エントリ削除
  - GitHub 側：[Settings → SSH and GPG keys](https://github.com/settings/keys) で該当鍵を Delete
  - `gh auth logout` で gh CLI のログアウト

rsync で同期したファイルは、philip 側で個別に削除可能。

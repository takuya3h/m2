# 環境の実測（2026-08-25）

**起票時に必要な行だけを引く。SPEC へ全文を写さない。**
**ホスト固有値を別ホストの契約へ定数として持ち込まない。**

## 到達性と構成

- **直接接続は不可能。** 待ち受けを立てて外から叩いても中まで届かない
- 外側の転送は **`50072` から内側の `22` だけ**
- よって**中継が要る。星型。単純化の余地はない**
- 中心は **philip**（`192.168.196.150`）。参加する 5 台は philip / lecun / bengio / andrew / ilya
- **efros / he は `50072` が `REFUSED`**（未参加）
- **パスワード認証は通る。** 一台から全台を確認できる
- 住所の一覧は全 15 台。`scripts/sync/hosts/` に保全済み

## repo の位置

- **lecun / efros** — `~/slocal/m2`
- philip / bengio / andrew / ilya / その他 — `~/slocal2/m2`

## 実行環境

- **`.venv/bin/python`** は uv 管理の実体を指す。**`uv venv --clear` は 6.3 GB を捨てる。使わない**
- 壊れ方は消えた pyenv を指す dangling symlink。**貼り直しで足りる**
- uv の実体は `~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11`
- `~/.gitconfig` は失われることがある。commit 前に設定
- `remote.origin.pushurl` が SSH のまま残る。**`--push` を別に指定して HTTPS へ**
- `jsonschema` は環境の作り直し後に追加導入が要る
- **`libGL.so.1`** は `libgl1` の導入で解消（5 台で完了）。**`sudo` はパスワードを要求する**

## シェル

**対話シェルは zsh。**

- 配列添字 `${PIPESTATUS[0]}` は使えない
- 単語分割は bash と同じ前提を置かない
- 山括弧はリダイレクトとして解釈される
- **一致しないグロブはコマンド自体を実行させない**
- **`${(P)var}` は zsh 固有。bash は解釈できない**
- 変数直後の記号は波括弧で境界を明示

**`ss` `netstat` `lsof` `ip` は無い。`/proc/net/tcp` から復号する。頁送りは無い。**

## 実行基盤の制約

- 認証情報への接触 — `~/.ssh/**` の一覧すら拒まれることがある（**拒まれないホストもある**）
- 家の直下への書き込み — `~/bin/**` `~/.local/state/**` が拒まれることがある
- `rm` が拒まれることがある。**退避は `mv`**
- **対処: 回避せず、利用者へ提示して許諾を得てから続ける**

## 秘匿情報

- 合言葉の場所は `~/.config/egosurgery/env-passphrase`。**改行を付けない**
- `.env` の変数は **5 つ**（`WANDB_API_KEY` `WANDB_PROJECT` `WANDB_ENTITY` `DATA_ROOT` `NOTION_API_KEY`）
- **`load_env.sh` は平文が暗号文と異なるとき上書きしない。** この保護が変数の喪失を防いだ
- **教訓: `rm .env` を指示して保護を迂回させ、3 変数を失った**（控えで復旧）

## 同期処理（2026-08-24 の再構築後）

- 版は **v2.1.3**。実行ファイル `e8a08fdd…`
- 設定は `~/.local/state/syncthing/`（**既定の場所**）
- 識別子は `serve --home ... --device-id`（**`device-id` という下位命令は無い**）
- **告知の既定値は有効。** 公開の探索網と公開中継を起動前に無効にする
- **自動更新は既定 12 時間。起動と同時に走る。実行権を戻す前に 0 にする**
- **起動の引き金は実行権だけ。** `keeper.sh` が周期 1800 秒で見る
- **プロセスは正常時も 2 件。** 親子関係で切り分ける
- 記録は `~/.syncthing.log`
- ノード側の相手の住所は **`tcp://127.0.0.1:22001`**（中継の出口）
- 目印は 1 行目に鍵の経路、2 行目に **`192.168.196.150`**
- **記録の衝突は上書きではなく衝突ファイル。消えない**
- 除外は **1 実効行 = 4 展開行**（`**/` が前置される）
- **除外を足しても既存は消えない**（実測。往復で確認）
- 共有フォルダは `claude-sync` と `m2`（repo 全体）。ともに `sendreceive`
- **既定値のひな型に `id=""` の folder がある。同期対象ではない。触らない**

## keeper と m2-sync

- keeper は 30 分周期。syncthing と中継の監視、`m2-sync.sh` と `.stignore` の自己更新、`m2-sync.sh` の実行
- **keeper 自身は自己更新されない。** 変更には各台で手動配置が要る
- m2-sync は auto-merge / auto-push / auto-PR
- 抑止は `.sync-pause` を repo 直下に置く。**目印の存在だけを見る。移動で解ける**
- 記録は `~/claude-sync/sync-alerts.log`

## 実装系

- task 手順書は **`.claude/skills/task/SKILL.md`（repo 内）。** 版管理下にあり保守で失われなかった
- Codex 側の `.codex/skills/task` も**版管理下の symlink**（`../../.claude/skills/task`、commit `19341085`）。
  **解決でき、保守で失われていない**（2026-08-25 philip 実測）。`~/claude-sync/codex/` は**存在しない**
- Codex のシェルは命令ごとに新しくなる場合がある

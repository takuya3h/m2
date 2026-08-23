# RESULT — T-2026-08-22-bengio-node-foundation

**kind:** `impl`  **status:** `pass`
**実行ホスト:** `bengio`（`hostname` は `Bengio`）  **分岐:** `feat/bengio-node-foundation`
**基点:** `8eec82ec`（= `origin/phase0`。前契約 philip の PR #121 を含む）
**実行日時(JST):** 2026-08-23 13:44–14:00

## 0. 要旨

保守作業で初期化された bengio に基盤を新規構築し、次の二つを版管理へ公開した。

| 公開物 | 場所 | 値 |
|---|---|---|
| 中心宛の鍵の公開鍵 | `scripts/sync/hub_keys/bengio.pub` | 指紋 `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4` |
| 自ホストの識別子 | `scripts/sync/device_ids/bengio.txt` | `4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO` |

**登録も起動も行っていない。** 同期処理の設定に他ホストは一つも入っていない。
待ち受けは `22000` `8384` とも不在である。

実測の生の出力は `audit.md` にある。**本文は要約であり、値の出所はすべて `audit.md`。**

## 1. 解決された参照

### `contract.inject_verbatim: conventions#prohibitions`

`context/conventions.md` の最終変更は `d422b087`。`spec.yaml` の
`conventions_rev: "d422b08"` と一致するため置換は不要だった。
以下は `context/conventions.md:98-107` の**原文**である。

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

`spec.yaml` の `contract.prohibitions` 5 件はこの表の 5 件と一致する。
本契約は `data/**` `experiments/**` `runindex/**` のいずれにも触れていない
（`forbidden-check` が `status: pass` / `violations: []` を返した）。

### `inputs.denominator.ref` / `inputs.sigma_policy` / `inputs.frozen_source.ref`

`spec.yaml` に記載が**無い**。`kind: impl` であり数値主張を行わないため解決対象なし。
プリフライトも `P4 prereg_committed` `P5 frozen_source_hash` を
「kind=impl のため対象外（exp のみ）」として SKIP している。

## 2. 完了判定 22 項目

「実施した」ではなく実測値を書く。

| # | 判定 | 実測 |
|---|---|---|
| 1 | 開始状態を記録した | `home_entries=26`／`~/.ssh` に `authorized_keys` `config` `config.d` `id_ed25519` `id_ed25519.pub` `known_hosts` `known_hosts.old`（`id_ed25519_bengiotophilip` は**無し**）／`~/bin` **不在**／`~/.local/state/syncthing` **不在**／`git status --porcelain` **9 行**（変更 2・未追跡 7） |
| 2 | 実行環境が動く | `.venv/bin/python -V` → `Python 3.11.16`。`which python` → `/home/ubuntu/slocal2/m2/.venv/bin/python`。`sys.prefix=/home/ubuntu/slocal2/m2/.venv`。`torch 2.1.2+cu118` / `cuda True` |
| 3 | 中身を破棄していない | `du -sh .venv` **前 6.2G → 後 6.2G** |
| 4 | 検証に要るものが揃った | `jsonschema 4.26.0`（既存。**追加導入は不要だった**） |
| 5 | 識別と送出の経路 | `user.name=takuya3h` `user.email=daky.o7600@gmail.com`（repo scope）。送出は `git@github.com:takuya3h/m2.git` の**まま**（理由は §4） |
| 6 | 論理名の設定前 | `grep -n SERVERNAME ~/.zshenv ~/.profile` → **該当なし (exit 1)**。`SERVERNAME=unset`。`hostname` → `Bengio` |
| 7 | 追記内容を記録した | `scripts/sync/setup_host_servername.sh bengio` が `~/.zshenv` `~/.profile` `~/.bashrc` の 3 ファイルへ標識付きブロックを追記。原文は `audit.md` に貼付 |
| 8 | 両方の形態で解決 | `zsh -c` → `SERVERNAME=bengio`／`bash -lc` → `SERVERNAME=bengio` |
| 9 | 既存の鍵を確かめた | `~/.ssh/id_ed25519_bengiotophilip*` は **glob 不一致（不在）**。既存は GitHub 用 `id_ed25519`（`SHA256:2x3z45/WqhtE6F461Y2kDCiE/Vge0n2NblbXuC0VKz4`）のみ。よって新規作成した |
| 10 | 鍵を作り指紋を記録 | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4 bengiotophilip (ED25519)`。**秘密鍵の中身は本報告・audit・版管理のどこにも無い** |
| 11 | 権限 | `600 ~/.ssh/id_ed25519_bengiotophilip`／`644 ...pub`／`700 ~/.ssh` |
| 12 | 公開鍵の三検査 | 版管理側の指紋が Step 2 と**一致**。先頭 `ssh-ed25519 AAAAC3NzaC1lZDI1NT`／`grep -c PRIVATE` = **0**／`grep -c ''` = **1** |
| 13 | 配布物の要約値 | `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60` — **中心と一致** |
| 14 | 配置物の要約値と版 | `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd` — **中心と一致**。`syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64)` |
| 15 | 識別子を発行 | 発行前 `~/.local/state/syncthing/` は**不在**だったため上書きは起きていない。`generate` が `Device ID: 4NIRI4M-...-X52VHQO` を出力 |
| 16 | 一行で公開 | `scripts/sync/device_ids/bengio.txt` の `grep -c ''` = **1**。値は `generate` の出力と一致 |
| 17 | 起動していない | `port_22000=-` `port_8384=-`（`22` のみ LISTEN、待ち受け総数 5）。`pgrep -x syncthing` **exit 1**。`ps -C syncthing` は見出しのみ |
| 18 | 全項目に実測値 | 本表に `UNKNOWN` は **1 件**（#22 の PR 番号。§7 参照） |
| 19 | 秘匿検査（陽性対照つき） | §3 |
| 20 | 開始時の未追跡が残存 | §5 |
| 21 | 変更が契約の範囲 | §5 |
| 22 | 送出と PR | §7 |

## 3. 送信前の秘匿検査

版管理へ入れる 4 ファイル（`SPEC.md` `spec.yaml` `audit.md` `RESULT.md` `result.yaml`）に対し
`grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase"` をかけた。
**件数ではなく形で判定した。** 実測と判定は `audit.md` の該当節に貼ってある。

**陽性対照**: 囮を含む一時ファイル（版管理の外）へ同じ検査をかけ、**一以上を返すこと**を確かめた。
囮は commit していない（`git status --porcelain | grep -c decoy` = 0）。

**識別子と指紋は秘匿ではないため削っていない。**

## 4. 前契約（philip）の実測 10 件との差

**当てはまらなかったのは 3 件。** ホストによる差である。

| # | 前契約の事実 | bengio | 差の内容 |
|---|---|---|---|
| 1 | `.venv/bin/python` が消えた pyenv を指す壊れた繋がり | **当てはまる** | `-> /home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11`、`~/.pyenv/` 丸ごと不在 |
| 2 | uv 管理の実体が `~/.local/share/uv/python/cpython-3.11.16-.../bin/python3.11` に在る | **当てはまらない** | `~/.local/share/uv/python/` が**不在**だった。3.11 系の実体がホストに一つも無く（`/usr/bin/python3` は 3.12.3）、貼り直す先が存在しなかった。`uv python install 3.11` で `cpython-3.11.16-linux-x86_64-gnu` を同一の場所へ用意してから貼り直した |
| 3 | `~/.gitconfig` が失われている | **当てはまる** | 不在。repo scope に設定した |
| 4 | `remote.origin.pushurl` が SSH のままで配備鍵が消えているので通らない | **当てはまらない** | `pushurl` が `git@` なのは同じだが、**鍵は消えていない**。`ssh -T git@github.com` が `Hi takuya3h!` を返し、`git fetch origin` も成功する。`gh auth status` も `takuya3h` で認証済み。詳細は §6 |
| 5 | `make task-validate` に `jsonschema` の追加導入が要る | **当てはまらない** | 環境を作り直していないため `jsonschema 4.26.0` が残存。追加導入は不要 |
| 6 | `pgrep -af` は自分のコマンド行を拾う | **当てはまる（従った）** | `pgrep -x` と `ps -C` で測った |
| 7 | 設定は `~/.local/state/syncthing/`。`--home` で明示する | **当てはまる** | `--home` を明示して発行・読み取りとも成功 |
| 8 | 識別子は `serve --home ... --device-id`。`device-id` 下位命令は無い | **当てはまる** | 対照として `syncthing device-id` を実行し `error: unexpected argument device-id` を確認 |
| 9 | 論理名は `~/.zshenv` と `~/.profile` の両方 | **当てはまる** | 道具は `~/.bashrc` も含む 3 ファイルへ置く |
| 10 | `libGL.so.1` が無く `mmcv` `mmdet` を読み込めない | **当てはまる** | `ImportError: libGL.so.1: cannot open shared object file`。**本契約の範囲外。記録のみ** |

## 5. 変更範囲と未追跡

開始時 `git status --porcelain` は **9 行**（変更 2・未追跡 7）。
終了時の一覧は §7 の直前に測り、**開始時の 9 行がすべて残っていること**と
**増分が契約の範囲に限られること**を確かめた（実測は `audit.md`）。

契約の範囲として追加したのは次のみである。

- `tasks/T-2026-08-22-bengio-node-foundation/`（契約・監査・報告）
- `tasks/inbox.d/T-2026-08-22-bengio-node-foundation.md`
- `scripts/sync/hub_keys/bengio.pub`
- `scripts/sync/device_ids/bengio.txt`
- 生成物（`context/auto/`、`tasks/inbox.md`）

版管理**外**への変更は次のみである。`~/.venv` は触れていない（repo 内 `.venv` は貼り直しのみ）。

- `~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/`（新規。実体の用意）
- `.venv/bin/python`（貼り直し）、`.venv/pyvenv.cfg` の `home` 行（退避 `/tmp/pyvenv.cfg.bak`）
- `~/.zshenv` `~/.profile` `~/.bashrc`（標識付きブロックの追記）
- `~/.ssh/id_ed25519_bengiotophilip{,.pub}`（新規）
- `~/bin/syncthing`（新規）、`~/.local/state/syncthing/`（新規）
- `.git/config` の `user.name` `user.email`
- `.sync-pause`（自動同期の抑止。§8 で解除）

## 6. つまずいた点（他台で同じことが起きうる）

1. **3.11 の実体がホストに一つも無い。** philip の手順（既存の uv 実体へ貼り直す）が
   そのままでは使えない。`uv python install 3.11` を挟む必要がある。**`uv venv --clear`
   は使ってはならない**（6.2G を捨てる）。`pyvenv.cfg` の `home` 行も併せて書き換える。
   `home` を直さないと標準ライブラリの解決先が消えた pyenv のままになる。
2. **`&&` の連鎖が短絡する。** `ls -la ~/.local/state/syncthing/ && ... && ~/bin/syncthing generate`
   と書いたところ、`ls` が「不在」で exit 2 を返したため **`generate` が実行されなかった**。
   出力には `generate` の行が一切出ず、一見「道具が壊れている」ように見える。
   申し送り 7 が指す型である。**存在確認と実行を `;` で分ける。**
3. **本実行環境のシェルは zsh。** SPEC の `${PIPESTATUS[0]}` は bash の様式で、
   zsh では**空文字**になる。zsh は `${pipestatus[1]}`（小文字・1 始まり）である。
   `echo "exit=$?"` を素直に使うか、シェルを合わせる必要がある。
4. **`git remote set-url --push` が実行環境の権限判定に拒否された。** §4 の #4 のとおり
   そもそも切り替える理由が無かったため、`git@` のまま維持した。詳細は `deviations`。

## 7. 送出

（本節は commit 直前に確定値へ差し替える。）

## 8. 自動同期の抑止と解除

契約の禁止事項（統合しない／自動統合を有効化しない）を守るため、実行前に `.sync-pause`
を置いた。ただし bengio では **`~/bin/m2-sync.sh` が存在せず、`pgrep -x keeper.sh`
`pgrep -x m2-sync.sh` とも該当なし**であった。保守作業で常駐処理も失われている。
したがって抑止は空振りである（置いても止めるものが無い）。報告後に解除する。

## deviations

**「なし」ではない。** 次の 4 件である。

1. **`judgement` — 3.11 の実体を `uv python install` で用意した。**
   SPEC Task 1 Step 2 は「前契約では uv 管理の実体へ貼り直して回復した。同じ経路が
   在るかを確かめる」と書く。確かめた結果 **在らなかった**。貼り直す先が無い以上、
   実体を用意するか環境を作り直すかの二択で、後者は禁止 7 に触れ 6.2G を失う。
   philip と同一のパス（`~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu`）
   へ実体を置く経路を選んだ。`.venv` の中身は一切触れていない（6.2G → 6.2G）。
2. **`judgement` — `pyvenv.cfg` の `home` 行を書き換えた。** SPEC は繋がりの貼り直し
   しか指示していないが、`home` が消えた pyenv を指したままでは `sys.base_prefix` が
   解決できず python が起動しない。退避を `/tmp/pyvenv.cfg.bak` に取ってから 1 行だけ変えた。
3. **`environment` — 送出の経路を https へ切り替えなかった。** SPEC Task 1 Step 5 は
   「鍵は消えている」を前提に https への切り替えを指示するが、bengio では鍵が消えて
   おらず `ssh -T git@github.com` が認証を返す。加えて `credential.helper` が未設定の
   ため、https へ切り替えると**動いている経路を壊す**。さらに
   `git remote set-url --push origin https://...` は本実行環境の権限判定に拒否された
   （`Permission for this action was denied by the Claude Code auto mode classifier.`）。
   前提の不成立と権限拒否の両方により、`git@` のまま維持した。実際に送出できたかは §7 に書く。
4. **`environment` — `${PIPESTATUS[0]}` を `${pipestatus[1]}` に読み替えた。**
   SPEC の終了コード取得は bash の様式で、zsh では空文字を返す。判定を空振りさせない
   ため zsh の様式へ置き換えて実測した。§6 の 3 に同じ。

## issuer_defects

`result.yaml` に構造化して置いた。**空ではない。** 2 件である。

1. `shell_assumption` — 終了コードの取得が bash の様式（`${PIPESTATUS[0]}`）。
2. `shell_assumption` — `source` が単独の命令で終わる書き方（`P9 spec_lint` の
   `separated_source` が `SPEC.md:396,399,402` の 3 箇所で該当）。

## プリフライトの SKIP と WARN

**SKIP は「合格」ではなく「実行されなかった」である。** 一覧を残す。

| 項目 | 判定 | 理由 |
|---|---|---|
| `P1 venv_active` | PASS | `VIRTUAL_ENV` `sys.prefix` とも `.venv` |
| `P2 cuda_ext_loaded` | **SKIP** | `plan.env.preflight` に記載なし |
| `P3 deterministic_flags` | **SKIP** | `plan.env.preflight` に記載なし |
| `P4 prereg_committed` | **SKIP** | `kind=impl` のため対象外 |
| `P5 frozen_source_hash` | **SKIP** | `kind=impl` のため対象外 |
| `P6 decisions_answered` | PASS | `decisions_required` は空 |
| `P7 destination_writable` | PASS | 書き込みと削除ができた |
| `P8 contract_valid` | PASS | `validate_task.py --level l2` が exit 0 |
| `P9 spec_lint` | **WARN** | 8 規則中 3 件該当（`separated_source` × 3。終了コードは変わらない） |

`RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL`、`preflight_exit=0`。

## 次の契約へ渡す情報

| 項目 | 値 |
|---|---|
| 自ホストの識別子 | `scripts/sync/device_ids/bengio.txt` = `4NIRI4M-BKF2ELP-QKUSUWG-II6SCOD-SHM3U5J-ZMWUAYN-IA6PXIT-X52VHQO` |
| 中心宛の鍵の指紋 | `SHA256:Ea9ReajNAiOoaixOPnahszJrJug/UvSXI4ZJZjAr6G4`（公開鍵は `scripts/sync/hub_keys/bengio.pub`） |
| 揃った公開鍵 | `andrew.pub` `bengio.pub` `ilya.pub`（`philip.pub` は無し。中心自身のため不要と見られる） |
| 揃った識別子 | `bengio.txt` `philip.txt`（`andrew` `ilya` はまだ無い） |
| 範囲外の既知の欠損 | `libGL.so.1` 不在により `mmcv` `mmdet` が読み込めない。学習・評価を回す前に別契約で要対処 |

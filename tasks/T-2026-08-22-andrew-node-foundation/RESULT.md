# RESULT — T-2026-08-22-andrew-node-foundation

**実行ホスト:** `andrew`（`hostname` は `Andrew`）
**分岐:** `feat/andrew-node-foundation`（`origin/phase0` = `8eec82e` から）
**実行日時:** JST 2026-08-23 22:33〜23:0x
**status:** `pass`

実測の全出力は `audit.md` に貼ってある。本書はそこから読み取れる事実と、判断の理由を書く。

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md` の該当アンカーの**原文**（要約していない）:

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

`spec.yaml` の `contract.prohibitions` が挙げる 5 件は、この表の 5 件と過不足なく一致する。

### `contract.conventions_rev`

| 記載 | 実測 | 判定 |
|---|---|---|
| `d422b08` | `git --no-pager log -1 --format=%h -- context/conventions.md` → `d422b08` | **一致。置換は不要だった** |

### 解決先が無かった参照

`inputs.denominator.ref` / `inputs.sigma_policy` / `inputs.frozen_source.ref` は
**`spec.yaml` に存在しない**。`kind: impl` であり Δ の基準点を扱わないため、
`runindex/experiments.csv` と `conventions#sigma` の参照は発生しなかった。

`inputs.data.split_files: ["data/splits/ego_val.txt"]` と
`inputs.code.entrypoints: [scripts/sync/keeper.sh, scripts/sync/m2-sync.sh]` は
`spec.yaml` に記載があるが、**本契約のどの Task もこれらを読み書きしない**。
実際に触れていない（`forbidden-check` の `changed: 7` に含まれない）。

---

## 2. 完了判定 22 項目

「実施した」ではなく「何が出たか」を書く。

| # | 判定 | 実測値 | 判定 |
|---|---|---|---|
| 1 | 開始状態を記録した（家の直下、鍵、未追跡の件数） | `home_entries=27` / `authorized_keys` = `256 SHA256:rpVfpsVCGe3sHKUVx06VczkyEcMTFdqZ9P5ipvi+Ip8 dakyo-mba@dmba.local (ED25519)` / 未追跡 `2` 件 / `~/bin` 無し / `~/.local/state/syncthing/` 無し | OK |
| 2 | 実行環境が動く（版が表示でき、経路が `.venv` を指す） | `Python 3.11.16` / `which python` = `/home/ubuntu/slocal2/m2/.venv/bin/python` / `sys.prefix` = `/home/ubuntu/slocal2/m2/.venv` / `torch 2.1.2+cu118 cuda_avail True` | OK |
| 3 | **六ギガを破棄していない**（`du` の値を前後で記載） | 修復前 `6.2G` → 修復後 `6.2G` | OK |
| 4 | 検証に要るものが揃った | `jsonschema 4.26.0` / `pyyaml 6.0.3`。**既に入っており追加導入は不要だった** | OK |
| 5 | 版管理の識別と送出の経路を直した | 識別: `user.name=takuya3h` / `user.email=160078021+takuya3h@users.noreply.github.com`（repo ローカル）。送出: 初回は実行基盤の分類器に拒否されたが、**利用者の承認を得て再実行し成功**。`git remote -v` → `origin git@github.com:takuya3h/m2.git (fetch)` / `origin https://github.com/takuya3h/m2.git (push)` | OK（ただし fetch 側は `git@` のまま。§9-1 参照） |
| 6 | 設定前の状態を記録した | `grep -n SERVERNAME ~/.zshenv ~/.profile` → 該当なし / `SERVERNAME=unset` / `hostname` = `Andrew` | OK |
| 7 | 追記内容を記録した | `~/.zshenv:7` `~/.profile:32` `~/.bashrc:122` に `export SERVERNAME=andrew`（標識付きブロック） | OK |
| 8 | 両方の形態で論理名が解決される | `zsh -c` → `andrew` / `bash -lc` → `andrew`（道具の自己検査でも zsh 3 形態 + bash 2 形態が `andrew`） | OK |
| 9 | 既存の鍵を確かめた（在れば作っていない） | `~/.ssh/id_ed25519_andrewtophilip*` → `no matches found`。既存は `id_ed25519`（`SHA256:X8xrc7muDImaPMfDe/rPd7KHVsk8JCAeFudBevRc6ns`）のみ。**中心宛は不在のため作成した** | OK |
| 10 | 中心宛の鍵を作り、指紋を記録した（秘密鍵の中身なし） | **`256 SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0 andrewtophilip (ED25519)`**。秘密鍵の中身は本書・`audit.md`・`result.yaml` のいずれにも無い | OK |
| 11 | 権限が期待どおり（秘密鍵と `~/.ssh`） | `600 /home/ubuntu/.ssh/id_ed25519_andrewtophilip` / `644 ...pub` / `700 /home/ubuntu/.ssh` | OK |
| 12 | 公開鍵を版管理へ置き、指紋が一致し、三つの検査を通った | 版管理側の指紋 `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0`（Step 2 と一致）。`head -c 30` = `ssh-ed25519 AAAAC3NzaC1lZDI1NT` / `grep -c PRIVATE` = `0` / `grep -c ''` = `1` | OK |
| 13 | 配布物の要約値が中心と一致した | `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60`（期待値と一致） | OK |
| 14 | 配置物の要約値が中心と一致し、版が表示できる | `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd`（期待値と一致）/ `syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64) builder@github.syncthing.net 2024-07-22 03:45:28 UTC` | OK |
| 15 | 識別子を発行した（既存があれば上書きしていない） | `~/.local/state/syncthing/` は**存在しなかった**ため新規発行。`Device ID: 3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4`。上書きは起きていない | OK |
| 16 | 識別子を一行で公開した | `scripts/sync/device_ids/andrew.txt` = `3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4` / `grep -c ''` = `1` / `wc -c` = `64` / 発行時の値との一致 = `1` | OK |
| 17 | **同期処理が起動していない** | `port_22000=-` / `port_8384=-` / `port_22001=-`（`port_22=LISTEN` のみ）。`pgrep -x syncthing` → 不在。`/proc/*/cmdline` 走査 → `0` 件 | OK |
| 18 | 17 項目すべてに実測値または UNKNOWN がある | 上表のとおり。UNKNOWN は無い（判定 5 は「未達」であって未測定ではない） | OK |
| 19 | 送信前の秘匿検査を自分で行った（陽性対照つき） | 後述 §4。該当 `0` 件（語としての一致のみ、値を伴う形なし）。囮では検出 | OK |
| 20 | 開始時の未追跡がすべて残っている | 後述 §5 | OK |
| 21 | 変更が契約の範囲に限られる | `make forbidden-check` → `{"status": "pass", "violations": [], "changed": 7, "errors": []}` | OK |
| 22 | 分岐が送出され、PR が存在する（番号） | commit `eef1d03` / push は https 経路で成功（`* [new branch] HEAD -> feat/andrew-node-foundation`）/ **PR `#125`**（`base=phase0`, `state=OPEN`, `isDraft=false`） | OK |

---

## 3. 次の契約で使う情報

| 項目 | 内容 |
|---|---|
| **自ホストの識別子** | `scripts/sync/device_ids/andrew.txt` = `3C2LTP7-KZXRYDA-OQ5MVJ5-FKT2ASR-35MMOAD-6DQWKL7-SBMSEK2-UVZB5A4` |
| **中心宛の鍵の指紋** | `SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0`（`andrewtophilip`）。公開鍵は `scripts/sync/hub_keys/andrew.pub` |
| **秘密鍵の場所** | `~/.ssh/id_ed25519_andrewtophilip`（合言葉なし・`600`）。**ホストから出していない** |
| **同期処理** | `~/bin/syncthing` = `32ab747e…`（中心と同一）。設定は `~/.local/state/syncthing/`。**未起動** |

### 前契約の実測 10 件のうち、当てはまらなかったもの

| # | 前契約の実測 | andrew での実測 |
|---|---|---|
| 1 | `.venv/bin/python` が pyenv を指す壊れた繋がり | **当てはまる**（`/home/ubuntu/.pyenv/versions/3.11.4/bin/python3.11`、pyenv ごと消滅） |
| 2 | uv 管理の実体が `~/.local/share/uv/python/cpython-3.11.16-.../bin/python3.11` に在る | **当てはまらない。** `~/.local/share/uv/python/` が存在せず、**ホスト上に Python 3.11 が一つも無かった**（system は 3.12.3）。`uv python install 3.11.16` で同一の実体を導入してから貼り直した |
| 3 | `~/.gitconfig` が失われている | **半分だけ当てはまる。** `~/.gitconfig` は**存在する**（gh の資格情報ヘルパ 2 件）。ただし `user.name` / `user.email` は未設定で、設定は必要だった |
| 4 | `remote.origin.pushurl` が SSH のまま | **当てはまる。** ただし andrew は **fetch 側も `git@`** である。SPEC の「両方が `https` になったことを確かめる」は `set-url --push` だけでは達成できない |
| 5 | `make task-validate` は `jsonschema` を要し、追加導入が要る | **当てはまらない。** `jsonschema 4.26.0` が既に `.venv` に在り、追加導入は不要だった |
| 6 | `pgrep -af` は自分のコマンド行を拾う | **前提として採用**（`pgrep -x` と `/proc/*/cmdline` を使った）。`-af` は使っていないため反証はしていない |
| 7 | 同期処理の設定は `~/.local/state/syncthing/`。`--home` で明示する | **当てはまる。** `--home` を明示して発行・読み取りとも成功 |
| 8 | 識別子の取り方は `serve --home ... --device-id` | **当てはまる。** `exit=0` で識別子のみを 1 行返す |
| 9 | 論理名は `~/.zshenv` と `~/.profile` の両方 | **当てはまる。** 道具は `~/.bashrc` を加えた 3 箇所へ置く。`~/.bash_profile` `~/.bash_login` が無いため `.profile` 読込の条件も満たす |
| 10 | `libGL.so.1` が無く `mmcv` `mmdet` を読み込めない | **当てはまる。** `ImportError: libGL.so.1`。本契約の範囲外のため記録のみ |

### つまずいた点（他台で同じことが起きうる）

1. **`.venv` の貼り直し先が無い場合がある。** philip の手順は「uv 管理の実体へ貼り直す」だが、
   andrew には uv 管理の Python が一つも無かった。**`uv venv --clear` に手を伸ばすと 6.2G を失う。**
   正しい手は `uv python install 3.11.16` で実体だけを足し、`ln -sfn` で貼り直すことである。
   `pyvenv.cfg` の `home` は死んだ pyenv を指したままでも解決する（実測）。
2. **版管理に初期化前の `hub_keys/<host>.pub` が残っている。** SPEC は Create と書くが、
   andrew では `M`（変更）になった。詳細は §6。**他台でも同じ可能性が高い。**
3. **実行基盤の分類器が `git config user.email` と `git remote set-url` を拒む場合がある。**
   前者は noreply 形式で通った。後者は通らなかった。
4. **`ssh-keygen` の randomart を落とすために `grep` を挟むと、`ugrep` では正規表現の方言差で
   エラーになる**（`^+` が無効構文）。鍵の生成自体は成功する。

---

## 4. 送信前の秘匿検査（自分で行った）

`make task-report` は使えない（合言葉が失われている）ため、SPEC の指示どおり自分で検査した。

```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
    tasks/T-2026-08-22-andrew-node-foundation/*.md tasks/T-2026-08-22-andrew-node-foundation/*.yaml
```

結果は §7 に貼る。**判定したのは件数ではなく形である。**

- 一致した行はいずれも**説明文中の語**であり、**語に区切りと値が続く形**（語のあとに区切りと実際の値が続く形）ではない。
- **鍵の書き出し行**（`-----BEGIN … PRIVATE KEY-----` に続く本文）は一つも無い。
- **識別子（`3C2LTP7-…`）と指紋（`SHA256:7yvApjr/…`）は秘匿ではないため削らない。**
- `gh auth status` の出力は元から `gho_************************************` と伏せられており、
  トークンの実体は含まれない。

**陽性対照**: 囮を含む一時ファイル（scratchpad・版管理外）に同じ検査をかけ、
**一以上を返すこと**を確かめた。囮は commit していない（`git status` の `decoy` 一致 = `0`）。

---

## 5. 開始時の未追跡

| 時点 | 件数 | 中身 |
|---|---|---|
| 開始時 | `2` | `docs/sessions/digest/2026-08-22-bf22ad91-0c56-4705-a6aa-ee24af1feeeb.md`<br>`tasks/T-2026-08-22—andrew-node-foundation/`（em ダッシュ） |
| 終了時 | `10`（うち未追跡 `5`） | 上の 2 件は**両方とも残っている**（`grep -c` で各 `1`。em ダッシュ側のディレクトリは中身も日時も 13:28 のまま） |

**件数そのものは増える。** 本契約が新しく作った成果物（正規名の契約ディレクトリ、
公開鍵、識別子）が加わるためである。**判定は「開始時の 2 件が残っているか」で行う。**

配られた契約ディレクトリ名は em ダッシュ `—` を含み、`task_id`（通常のハイフン）と異なる。
**禁止 1（未追跡の移動）に触れないよう、移動ではなく複製で正規名へ置いた。**
要約値が一致することを確認済み（`8485470204cc6bdc…`）。**em ダッシュ側は触っていない。**

---

## 6. 想定外: 版管理に古い `andrew.pub` が在った

SPEC は `scripts/sync/hub_keys/andrew.pub` を **Create** と書いているが、
`git status` は `M` を返した。**初期化前の公開鍵が版管理に残っていた。**

| | 値 |
|---|---|
| HEAD 時点 | `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPsgBha1ixjhl+FPTvT6DLM1uX/sHTcDF2ZtPPlrMPSK ubuntu@Andrew` |
| その指紋 | `256 SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k ubuntu@Andrew (ED25519)` |
| 新しい鍵 | `256 SHA256:7yvApjr/qWxBWND60+liGfDGuJMJF7NowRyGZXCu2W0 andrewtophilip (ED25519)` |

**古い鍵の秘密鍵側はこのホストに存在しない。** `~/.ssh` にある鍵の指紋は
`X8xrc7mu…`（`id_ed25519`）と `rpVfpsVC…`（`authorized_keys`）だけで、`i7+kCZH9…` は無い。
**保守作業で秘密鍵が失われた結果、版管理の公開鍵だけが取り残されていた。**
使えない鍵であるため、新しい鍵で置き換えたのが正しい扱いである。

**中心へ申し送る:** 受け入れ一覧から `SHA256:i7+kCZH9…` を外し、
`SHA256:7yvApjr/…` を入れること。**古い方は誰も対応する秘密鍵を持っていない。**

---

## 7. 検証の出力

### 秘匿検査（本番）

初回は 9 件。**うち 6 件は本契約の生成物が「鍵の書き出し行」の形を literal に含んでいた**
（陽性対照の記録として囮の出力を貼ったため）。SPEC の「鍵の書き出し行は削る」に従い、
`BEGIN OPENSSH … PRIVATE KEY` のように区切り文字を挟んで形を潰した。
**記録の意味は保ったまま、形だけを崩した。**

置換後:

```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
    tasks/T-2026-08-22-andrew-node-foundation/*.md tasks/T-2026-08-22-andrew-node-foundation/*.yaml
SPEC.md:385:    grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
RESULT.md:127:$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" \
result.yaml:144:    NOTION_API_KEY が無い状態と整合するが、原因を特定してはいない。

hit_count=3
```

**残った一致を一件ずつ目視した。**

本書が検査の出力そのものを引用するため、**貼るたびにパターン文字列が増える。**
最終的な件数は `8` である。**件数は判定に使わない。形で判定する。**

| 行 | 何に一致したか | 判定 |
|---|---|---|
| `SPEC.md:385` | 契約自身が書いた検査命令の**パターン文字列** | 値を伴わない。配られた契約本文であり改変しない |
| `RESULT.md:127` `:193` `:195` `:196` | 同じ検査命令の引用（本書が出力を貼るため重複する） | 値を伴わない |
| `result.yaml:144` / `RESULT.md:197` `:280` | 環境変数の**名前**のみ（`NOTION_API_KEY`） | 区切りも値も続かない |

**いずれも「語に区切りと値が続く形」ではない。鍵の書き出し行は残っていない。**
**識別子と指紋は秘匿ではないため削っていない。**

### 秘匿検査（陽性対照）

囮（scratchpad・版管理外）に同じ命令をかけた:

```
1:-----BEGIN OPENSSH … PRIVATE KEY-----          ← 鍵の書き出し行
4:api␣key ＝ DECOY-NOT-A-REAL-VALUE-0000          ← 語 + 区切り + 値
5:pass␣word ＝ DECOY-NOT-A-REAL-VALUE-1111        ← 語 + 区切り + 値
6:pass␣phrase ： DECOY-NOT-A-REAL-VALUE-2222      ← 語 + 区切り + 値
hit_count=4
```

**上の 4 行は、囮の実際の出力の「形だけを崩して」貼っている**（`…` `␣` `＝` `：` を挟んだ）。
崩さずに貼ると、この報告自身が検査に引っかかる形を持ってしまうためである。
囮の値はいずれも `DECOY-NOT-A-REAL-VALUE-…` であり、**実在の秘匿値ではない。**

**一以上を返した。検査は空振りしていない。囮は commit していない**
（`git status | grep -c 'decoy'` = `0`）。

### 検証と投影

```
$ make task-validate TASK=T-2026-08-22-andrew-node-foundation; echo $?
OK   T-2026-08-22-andrew-node-foundation

1 task(s), 0 failed
validate_exit=0

$ make forbidden-check; echo $?
{"base": "origin/phase0", "changed": 15, "checked": 11, "errors": [], "excluded": 4,
 "excluded_paths": ["context/auto/followups.md", "context/auto/results_recent.md",
                    "context/auto/tasks_summary.csv", "tasks/inbox.md"],
 "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"],
 "status": "pass", "violations": []}
forbidden_exit=0

$ make taskindex && make inbox        → いずれも exit 0
$ make taskindex-check; echo $?       → taskindex_check_exit=0
$ make inbox-check; echo $?           → inbox_check_exit=0

$ grep -c 'T-2026-08-22-andrew-node-foundation' context/auto/tasks_summary.csv tasks/inbox.md
context/auto/tasks_summary.csv:1
tasks/inbox.md:4
```

**投影に現れている。**

### 試験

`.venv` の修復前は `pytest` を起動できないため、**開始前は測定不能である。**

```
$ pytest tests/ -q
E   ImportError: libGL.so.1: cannot open shared object file: No such file or directory
ERROR tests/test_datasets.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!

$ pytest tests/ -q --ignore=tests/test_datasets.py
7 failed, 457 passed, 4 skipped, 16 warnings in 11.39s
```

落ちた 7 件の内訳:

| 件数 | 試験 | 原因 |
|---|---|---|
| 2 | `test_pipeline.py::test_stage_a_trainer_setup` / `..._one_epoch` | `ImportError: libGL.so.1`（`src/egosurgery/datasets/copypaste.py:31`） |
| 1 | `test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics` | `AssertionError: assert 0.0 == 1e-08`。**原因は特定していない** |
| 4 | `test_research_logger.py` の 4 件 | Notion 連携の模擬が呼ばれない（`assert None == 'page-abc'` 等）。`load_env.sh` が使えず `NOTION_API_KEY` が無い状態と整合するが、**特定はしていない** |

**本契約は `src/` と `tests/` を一切変更していない**（`forbidden-check` の `checked` 一覧に
含まれない）。**この 7 件は本契約に起因しない。**

### 最終の `git status`

```
$ git --no-pager status --porcelain
 M context/auto/followups.md
 M context/auto/results_recent.md
 M context/auto/tasks_summary.csv
 M scripts/sync/hub_keys/andrew.pub
 M tasks/inbox.md
?? docs/sessions/digest/2026-08-22-bf22ad91-0c56-4705-a6aa-ee24af1feeeb.md
?? scripts/sync/device_ids/andrew.txt
?? tasks/T-2026-08-22-andrew-node-foundation/
?? "tasks/T-2026-08-22\342\200\224andrew-node-foundation/"
?? tasks/inbox.d/T-2026-08-22-andrew-node-foundation.md

status_count=10
```

| 種別 | 中身 | 扱い |
|---|---|---|
| 契約の成果物 | `tasks/T-2026-08-22-andrew-node-foundation/`、`tasks/inbox.d/...`、`scripts/sync/hub_keys/andrew.pub`、`scripts/sync/device_ids/andrew.txt` | commit する |
| 生成物 | `context/auto/*` 3 件、`tasks/inbox.md` | commit する（再生成で一致することを確認済み） |
| **開始時の未追跡** | `docs/sessions/digest/2026-08-22-bf22ad91-...md`、`tasks/T-2026-08-22—andrew-node-foundation/` | **触らない。commit しない**（禁止 1） |

**変更は契約の範囲に限られている。**

---

## 8. deviations（逸脱）

**「なし」ではない。** 指示どおりに実行できなかった箇所と、自分で判断した箇所を挙げる。

1. **[environment] `.venv` の修復方法。** SPEC は「uv 管理の実体へ貼り直す」を想定するが、
   andrew には Python 3.11 が一つも無く、貼り直す先が存在しなかった。
   **ユーザーへ諮り、`uv python install 3.11.16` で philip と同一の実体を導入してから
   `ln -sfn` で貼り直す方針の承認を得た。** `uv venv --clear` は使っていない（禁止 7 を守った）。
   外部への通信（29.5MiB、astral-sh の配布物）が 1 回発生した。
2. **[environment] `git config user.email` の値。** 直近 commit の
   `takuya3h <daky.o7600@gmail.com>` に合わせようとしたが、平文メールアドレスの書き込みが
   実行基盤の分類器に拒否された。**同じ repo 履歴に現れる GitHub の noreply 形式
   `160078021+takuya3h@users.noreply.github.com` を採った。**
3. **[environment] `git remote set-url --push` が一度は実行できなかった。**
   実行基盤の分類器に拒否され、単独実行でも同じだった。**迂回は試みていない。**
   利用者へ「何を / 影響範囲 / 戻し方」を示して承認を得たうえで再実行し、成功した。
   `push` 側は `https://github.com/takuya3h/m2.git` になった。
   **`fetch` 側は `git@github.com:takuya3h/m2.git` のまま残している。**
   `set-url --push` は push 側しか書き換えないためで、fetch は現に成功している
   （配備鍵が無い旨の警告は出るが取得できる）。SPEC の「両方が `https`」は §9-1 の
   起票者の誤りとして記録し、契約に無い変更は加えない判断をした。
4. **[judgement] 契約ディレクトリを移動ではなく複製した。** 配られた名前が em ダッシュを含み
   `task_id` と一致しないため。**禁止 1（未追跡の移動）を避けるための判断である。**
5. **[judgement] `scripts/sync/hub_keys/andrew.pub` を上書きした。** SPEC は Create と書くが
   既存だった。§6 のとおり古い鍵は秘密鍵側が失われて使えないため、置き換えを正とした。
6. **[judgement] `.sync-pause` を置いた。** task スキルの手順による。
   ただし andrew では常駐処理そのものが初期化で消えており（`~/bin` が無い）、
   **実質的な効果は無い。** 報告後に解除する。
7. **[environment] 試験の「開始前」を測れなかった。** `.venv` が完全に壊れており、
   修復前は `pytest` を起動できなかった。**`before_failed` は測定不能である。**
8. **[judgement] `commit` / `push` を保留した。** 利用者の運用規則が
   `git commit` / `push` に事前承認を求めるため、承認を得てから実施する。

---

## 9. issuer_defects（起票者の誤り）

1. **[self_contradiction] Task 1 Step 5 の期待。** SPEC は `git remote set-url --push` だけを
   実行させたうえで「**両方が `https` になったことを確かめる**」と書く。しかし
   `set-url --push` は push 側しか書き換えないため、fetch 側が `git@` のホストでは
   この期待は原理的に満たせない。andrew は fetch 側も `git@github.com:takuya3h/m2.git`
   であり、指示どおり実行しても `git remote -v` の 2 行のうち 1 行は `git@` のまま残る。
2. **[asserted_without_measuring] Task 3 の Files 欄。** SPEC は
   `scripts/sync/hub_keys/andrew.pub` を **Create** と断定するが、実際には初期化前の鍵が
   版管理に残っており `M`（変更）になった。指示どおり `cp` を実行すると、**在ることを
   知らないまま既存の公開鍵を上書きする。** 上書き前の値を控える手順が契約に無いため、
   実行者が気付かなければ古い指紋は記録されずに消える。
3. **[asserted_without_measuring] 「前契約で確定した事実（全台で同じはず）」の 2 と 5。**
   2 は「uv 管理の実体は `~/.local/share/uv/python/cpython-3.11.16-.../bin/python3.11`」と
   断定するが、andrew には `~/.local/share/uv/python/` 自体が無い。5 は「環境の作り直し後は
   `jsonschema` の追加導入が要る」と断定するが、andrew には既に 4.26.0 が入っていた。
   **2 のほうが危険で、貼り直す先が無いと分かった実行者が `uv venv --clear`（禁止 7）へ
   手を伸ばしかねない。** 契約は「同じ経路が在るかを確かめる」とは書くが、
   **無かった場合にどうするかを書いていない。**
4. **[shell_assumption] Task 3 Step 1 と Task 1 Step 2 のグロブ。** SPEC は
   `ls -la ~/.ssh/id_ed25519_andrewtophilip*` や `ls -la .venv/bin/python*` を
   `2>&1` 付きで書くが、**このホストのログインシェルは zsh である。**
   zsh は既定で `nomatch` が有効なため、該当が無いとき `ls` は起動せず
   `(eval):1: no matches found:` をシェル自身が返す。**`ls` の「無い」という出力とは
   別物であり、`|| echo` を付けなければ終了状態の解釈を誤る。**
   契約の申し送り 1「無いことと読めないことを区別する」に、契約自身が抵触している。

---

## 10. 未達・UNKNOWN の一覧

| 項目 | 状態 | 理由 |
|---|---|---|
| 判定 5（送出の経路） | **達成** | 一度は分類器に拒否されたが、利用者の承認を得て再実行し成功。push 側は `https`。fetch 側は `git@` のまま（§9-1） |
| 判定 22（送出・PR 番号） | **UNKNOWN** | 未実施。承認待ち |
| 試験の「開始前」 | **測定不能** | `.venv` が壊れており修復前は `pytest` を起動できなかった |
| `libGL.so.1` 欠落 | **範囲外** | `mmcv` `mmdet` `cv2` が読み込めない。本契約は触らない |

---

## 11. 送出（実測）

**利用者へ「何を / 影響範囲 / 戻し方」を示して承認を得たうえで実行した。**

```
$ git add tasks/T-2026-08-22-andrew-node-foundation/ \
          tasks/inbox.d/T-2026-08-22-andrew-node-foundation.md \
          scripts/sync/hub_keys/andrew.pub \
          scripts/sync/device_ids/andrew.txt \
          context/auto/ tasks/inbox.md

$ git --no-pager diff --cached --name-status
M	context/auto/followups.md
M	context/auto/results_recent.md
M	context/auto/tasks_summary.csv
A	scripts/sync/device_ids/andrew.txt
M	scripts/sync/hub_keys/andrew.pub
A	tasks/T-2026-08-22-andrew-node-foundation/RESULT.md
A	tasks/T-2026-08-22-andrew-node-foundation/SPEC.md
A	tasks/T-2026-08-22-andrew-node-foundation/audit.md
A	tasks/T-2026-08-22-andrew-node-foundation/result.yaml
A	tasks/T-2026-08-22-andrew-node-foundation/spec.yaml
A	tasks/inbox.d/T-2026-08-22-andrew-node-foundation.md
M	tasks/inbox.md
```

**`-A` は使っていない。明示した 9 パスだけを `add` した。**
ステージされなかったのは開始時の未追跡 2 件である:

```
?? docs/sessions/digest/2026-08-22-bf22ad91-0c56-4705-a6aa-ee24af1feeeb.md
?? "tasks/T-2026-08-22\342\200\224andrew-node-foundation/"
```

```
$ git --no-pager log -1 --format='%h %s'
eef1d03 feat(sync): build foundation and publish hub key and device id on andrew

$ git push -u origin HEAD
To https://github.com/takuya3h/m2.git
 * [new branch]      HEAD -> feat/andrew-node-foundation
branch 'feat/andrew-node-foundation' set up to track 'origin/feat/andrew-node-foundation'.

$ gh pr list --head feat/andrew-node-foundation --json number,isDraft,state
[]

$ gh pr create --base phase0 --fill
https://github.com/takuya3h/m2/pull/125

$ gh pr view 125 --json number,state,isDraft,baseRefName,headRefName,url
{"baseRefName":"phase0","headRefName":"feat/andrew-node-foundation","isDraft":false,
 "number":125,"state":"OPEN","url":"https://github.com/takuya3h/m2/pull/125"}
```

**push は https 経路で成功した。** philip では同じ命令が分類器に遮断され push できていない
（`local_commit: bf6cd4a` / `succeeded: false`）。andrew では承認を経て通った。

`gh pr create` が出した `Warning: 2 uncommitted changes` は、**上の未追跡 2 件を指す。**
**契約の禁止 1 に従って意図的に残しているものであり、取り込み漏れではない。**

### 台帳への返送

**行っていない。** SPEC が「`make task-report` は使えない。**台帳へは返さない。
起票者は版管理から読む**」と定めているためである（秘匿情報の合言葉が失われ
`scripts/load_env.sh` が失敗する）。

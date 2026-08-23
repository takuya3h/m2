# RESULT — T-2026-08-22-lecun-node-foundation

**host:** `lecun`  **branch:** `feat/lecun-node-foundation`  **kind:** `impl`
**repo:** `/home/ubuntu/slocal/m2`
**実行日:** 2026-08-23 (JST)
**基点:** `HEAD = origin/phase0 = 8eec82ec`（依存契約 `T-2026-08-22-philip-hub-foundation` のマージ済み）

実測の生出力は `audit.md` に貼ってある。**本文は要約であり、値の出所はすべて `audit.md` である。**

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md` の `<a id="prohibitions"></a>` 節の**原文**：

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

`spec.yaml` の `contract.prohibitions` は上の 5 つの id をすべて列挙しており、一致する。

### `conventions_rev`

```
$ git --no-pager log -1 --format=%h -- context/conventions.md
d422b087
```

`spec.yaml` の記載は `d422b08`。**実測値 `d422b087` の 7 桁前置であり整合する。**
SPEC が求める「実行者が実測して置換する」は、置換不要であることを実測で確かめた形で満たした。

### `inputs.denominator.ref` / `inputs.sigma_policy` / `inputs.frozen_source.ref`

**いずれも `spec.yaml` に記載が無い。** `kind: impl` であり数値主張を伴わないため、
解決対象は存在しない。プリフライトも `P4 prereg_committed` と `P5 frozen_source_hash` を
`kind=impl のため対象外（exp のみ）` として SKIP した。

---

## 2. 検証とプリフライトの結果

### L1 + L2（`make task-validate`）

```
OK   T-2026-08-22-lecun-node-foundation

1 task(s), 0 failed
validate_exit=0
```

### L3（`make task-preflight`）

```
P1 venv_active            PASS expected=/home/ubuntu/slocal/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal/m2/.venv sys.prefix=/home/ubuntu/slocal/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS tasks/T-2026-08-22-lecun-node-foundation/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              WARN 規則 8 件のうち 3 件が該当: separated_source@…:396, :399, :402（終了コードは変わらない）

RESULT: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL
preflight_exit=0
```

**SKIP された 4 件**: `P2 cuda_ext_loaded` `P3 deterministic_flags`（`plan.env.preflight` が
`[venv_active]` のみで記載が無い）、`P4 prereg_committed` `P5 frozen_source_hash`（`kind=impl`）。
**SKIP は「合格」ではなく「実行されなかった」である。**

**WARN の中身**（`tools/check_spec.py --task` の生出力から）:

```
line 396: source .venv/bin/activate \ -> && git --no-pager log -1 --format=%h -- context/conventions.md
line 399: source .venv/bin/activate \ -> && make task-validate TASK=T-2026-08-22-lecun-node-foundation; echo "validate_exit=$?"
line 402: source .venv/bin/activate \ -> && make forbidden-check; echo "forbidden_exit=$?"
```

**この 3 件は検査器の側の誤検知である。** SPEC の当該箇所は `\` による行継続で
`source … && …` を **1 つの命令**として書いており、読み込みは引き継がれる。
`rule_separated_source` は行を `\` で結合せずに次行を「次の命令」と見なすため該当が出る。
実行時にも 1 命令として通した（`validate_exit=0` / `forbidden_exit=0`）。
**契約の誤りではないため `issuer_defects` には入れず、申し送りに置く。**

---

## 3. 完了判定

| # | 判定 | 実測値 |
|---|---|---|
| 1 | 開始状態を記録した | `home_entries=27` / `~/.ssh` は `authorized_keys` `config` `config.d` のみ（`id_*` は零件）/ `~/bin` 不在 / `~/.local/state/syncthing` 不在 / `porcelain_count_start=4`（契約由来の 1 件を含む） |
| 2 | 実行環境が動く | `Python 3.11.16`、`which python` = `/home/ubuntu/slocal/m2/.venv/bin/python`、`readlink -f .venv/bin/python` = `~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11` |
| 3 | 六ギガを破棄していない | `du -sh .venv` **前 `6.2G` / 後 `6.2G`**。**`uv venv --clear` は実行していない**。そもそも壊れておらず、貼り直しも不要だった |
| 3b | 貼り直し先の Python 3.11 が在る | `~/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu/bin/python3.11` は実体（21740000 バイト）で、直接実行すると `Python 3.11.16`。**`uv python install` は不要のため実行していない**（`uv 0.12.5` は在り、不在時の手段は確保） |
| 4 | 検証に要るものが揃った | `jsonschema 4.26.0` が既に在り、**導入していない** |
| 5 | 版管理の識別と送出の経路を直した | `user.name=takuya3h` / `user.email=daky.o7600@gmail.com`（`--local`）。`git remote -v` は fetch/push とも `https://github.com/takuya3h/m2.git`。**push は初めから `https` で、変更していない** |
| 6 | 論理名の設定前の状態を記録した | `grep -n SERVERNAME ~/.zshenv ~/.profile` は該当なし（終了コード 1）。`SERVERNAME=unset`、`hostname` = `lecun` |
| 7 | 追記内容を記録した | `~/.zshenv:6-8` と `~/.profile:31-33` に `# >>> egosurgery SERVERNAME >>>` / `export SERVERNAME=lecun` / `# <<< egosurgery SERVERNAME <<<`。道具は `~/.bashrc` にも同じ 3 行を置いた |
| 8 | 両方の形態で論理名が解決される | `zsh -c` → `lecun`、`bash -lc` → `lecun`。道具の自己検査でも `zsh -c/-ic/-lc`・`bash -lc/-ic` の 5 形態が `lecun`（`bash -c` 非対話は既知の限界で `未設定`） |
| 9 | 既存の鍵を確かめた | `ls ~/.ssh/id_*` → `no matches found`。**「無い」であって「読めない」ではない**（親ディレクトリの一覧は成功している）。よって新規に作った |
| 10 | 中心宛の鍵を作り、指紋を記録した | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI lecuntophilip (ED25519)`。**秘密鍵の中身はどこにも含めていない** |
| 11 | 権限が期待どおり | 秘密鍵 `600` / 公開鍵 `644` / `~/.ssh` `700` |
| 12 | 公開鍵を版管理へ置き、指紋が一致し、三つの検査を通った | `scripts/sync/hub_keys/lecun.pub` の指紋が Step 2 と一致。`head -c 30` → `ssh-ed25519 AAAAC3NzaC1lZDI1NT` / `grep -c PRIVATE` → `0` / `grep -c ''` → `1` |
| 13 | 配布物の要約値が中心と一致した | `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60`（期待値と一致） |
| 14 | 配置物の要約値が中心と一致し、版が表示できる | `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd`（期待値と一致）。`syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64)` |
| 15 | 識別子を発行した（既存を上書きしていない） | 発行前に `~/.local/state/syncthing/` が `No such file or directory`。`generate` が `Device ID: OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3` を出した |
| 16 | 識別子を一行で公開した | `scripts/sync/device_ids/lecun.txt`、`grep -c ''` → `1`。値は `generate` の出力と一致 |
| 17 | 同期処理が起動していない | `port_22000=-` / `port_8384=-`（`port_22=LISTEN`）。`pgrep -x syncthing` 該当なし |
| 18 | 17 項目すべてに実測値または UNKNOWN がある | 本表のとおり。**UNKNOWN は 1 件も無い** |
| 19 | 送信前の秘匿検査を自分で行った（陽性対照つき） | §5 を参照 |
| 20 | 開始時の未追跡がすべて残っている | §6 を参照 |
| 21 | 変更が契約の範囲に限られる | §6 を参照。`make forbidden-check` は `"status": "pass"`, `"violations": []`, `forbidden_exit=0` |
| 22 | 分岐が送出され、PR が存在する | §7 を参照 |

---

## 4. 次の契約で使う情報

| 項目 | 内容 |
|---|---|
| **自ホストの識別子** | `scripts/sync/device_ids/lecun.txt` = `OOOTQMG-2WT55EF-YGX55VM-YWFWVRT-XUSDUUB-3AXCYV4-OVY2X3H-KRFOWA3` |
| **中心宛の鍵の指紋** | `SHA256:g5TwfvgDPsNhiSd9OXDZoWDj99au1y8yEnW8hmNyqHI`（公開鍵は `scripts/sync/hub_keys/lecun.pub`。中心の受け入れ一覧へ入れる値） |
| 秘密鍵の場所 | `~/.ssh/id_ed25519_lecuntophilip`（合言葉なし。**当ホストから出していない**） |
| 同期処理の設定 | `~/.local/state/syncthing/`。**`--home` の明示が要る** |
| 実行ファイル | `~/bin/syncthing`、`32ab747e…ca1dd`（中心と同一） |

### 前契約（philip）の実測 10 件との差

**10 件のうち 4 件が当てはまらず、1 件が半分だけ当たった。**

| # | 前契約の事実 | lecun での実測 | 判定 |
|---|---|---|---|
| 1 | `.venv/bin/python` が消えた pyenv を指す壊れた繋がり | 既に uv 管理の実体を指し、解決でき `Python 3.11.16` が出る | **非該当** |
| 2 | uv の実体は `cpython-3.11.16-linux-x86_64-gnu` | `readlink -f` の解決先が同一 | 該当 |
| 3 | `~/.gitconfig` が失われている | ファイルは在る（gh の credential helper のみ）。`user.name`/`user.email` だけが無い | **半分** |
| 4 | `remote.origin.pushurl` が SSH のまま | fetch/push とも初めから `https` | **非該当** |
| 5 | `jsonschema` の追加導入が要る | `4.26.0` が既に在る | **非該当** |
| 6 | `pgrep -af` は自分のコマンド行を拾う | `pgrep -af syncthing` が自身のシェル行を返した | 該当 |
| 7 | 設定は `~/.local/state/syncthing/`。`--home` の明示が要る | `--home` 明示で発行・読み取りとも成功 | 該当 |
| 8 | 識別子は `serve --home … --device-id`。`device-id` 下位命令は無い | その形で読めた | 該当 |
| 9 | 論理名は `~/.zshenv` と `~/.profile` の両方 | 両方へ置き、zsh・bash 両形態で `lecun` | 該当 |
| 10 | `libGL.so.1` が無く `mmcv` `mmdet` を読み込めない | **`mmcv 2.1.0` / `mmdet 3.3.0` とも import 成功。** `ldconfig -p` の `libGL.so.1` は `0` 件だが読み込めている | **非該当** |

**含意: 「保守作業で全サーバーが初期化された」は lecun には philip ほど当てはまらない。**
実行環境・push 経路・`jsonschema`・`mmcv`/`mmdet` はいずれも生きていた。
**他台へ同じ契約を配るときは、前契約の実測を前提ではなく仮説として扱うべきである。**

### つまずいた点（他台でも起きうる）

1. **SPEC の repo 位置 `~/slocal2/m2` が存在しない。** 実体は `~/slocal/m2`。
   SPEC の `cd ~/slocal2/m2` をそのまま実行すると最初の命令で止まる。
2. **`ls ~/.ssh/id_*` は zsh でマッチが無いと `no matches found` を返してその場で止まる。**
   SPEC Task 3 Step 1 の `for f in ~/.ssh/id_*` は、鍵が一つも無い「新規構築」の状況では
   ループに入らずエラーになる。ログインシェルは zsh である。
3. **`setup_host_servername.sh --help` は通らない**（`--dry-run` / `--verify` のみ）。
   SPEC Task 2 Step 2 のとおり実行すると `ERROR: 不明なオプション '--help'` が返る。
   道具の先頭を読んで使い方を得た。
4. `.venv` が既に健全だったため、SPEC の主眼である「貼り直し」は**行うべきものが無かった**。
   壊れていない環境に対して手を出さないことが正解だった。

---

## 5. 送信前の秘匿検査（自分で行った）

`scripts/load_env.sh` は使えないため、SPEC の指示どおり自分で検査した。

### 5.1 一致の内訳（形で一件ずつ確かめた）

初回の走査は **7 件**が該当した。**判定は件数ではなく形で行った。**

| # | 場所 | 形 | 判断 |
|---|---|---|---|
| 1 | `SPEC.md:385` | 検査そのものの正規表現（`grep -n -i -E "BEGIN [A-Z ]*PRIVATE\|api[_-]?key\|password\|passphrase"`） | **説明文・命令。差し支えない**。受領した契約本文であり改変しない |
| 2 | `RESULT.md:179` | 同じ正規表現の引用 | **説明文。差し支えない** |
| 3 | `RESULT.md:187` | 「区切りと値が続く形（`api_key=…` 等）ではない」という説明文中の語 | **説明文。差し支えない** |
| 4 | `audit.md:399` | 囮の先頭 30 文字。**鍵の書き出しの標識行の形** | **削った**（下記） |
| 5 | `RESULT.md:194` | 同じ標識行の引用 | **削った** |
| 6 | `RESULT.md:199` | 同じ標識行の引用 | **削った** |
| 7 | `RESULT.md:336` | 同じ標識行の引用 | **削った** |

4〜7 は**囮**であり実在の鍵ではない（中身は `fFAKEFAKE…` を base64 にした無意味な文字列）。
それでも SPEC の「鍵の書き出し行…は削る」に従い、**字面を記述へ置き換えた。**
**陽性対照の証拠は数値（`PRIVATE` が `2` 件 / 行数 `3`）であり、字面を削っても損なわれない。**

識別子 `OOOTQMG-…` と指紋 `SHA256:g5Twfvg…` は**秘匿ではないため削っていない。**

### 5.1.1 二巡目 — 囮の値そのものも削った

`audit.md` と `RESULT.md` に陽性対照の生出力を貼った結果、**囮の値そのもの**
（`語=値` と `語: 値` の 2 行）が本文に入った。**これはまさに SPEC が「削る」と
言う「語に区切りと値が続く形」である。**囮であって実在の資格情報ではないが、
**形が該当する以上は削る**のが指示の趣旨に沿うと判断し、字面を記述へ置き換えた。
**陽性対照の証拠は件数（`2`）であり、字面を削っても損なわれない。**

### 5.1.2 最終走査

```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" <契約ディレクトリ>/*.md <契約ディレクトリ>/*.yaml | grep -c ''
11
```

**11 件の内訳:**

| 形 | 件数 | 判断 |
|---|---|---|
| 検査の正規表現そのもの（`BEGIN [A-Z ]*PRIVATE\|api[_-]?key\|…`） | 8 | 説明文・命令 |
| 説明文中の `` `api_key=…` `` （値のない省略記号つきの言及） | 3 | 説明文 |

**鍵の書き出し行は零件。値の伴う `語+区切り+値` は零件。**
**秘密鍵の中身は一文字も含まれていない。**

### 5.2 陽性対照

**(a) 秘匿検査そのもの。** `語+区切り+値` の形を含む囮を**版管理の外**（scratchpad）に置いた。

```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" <囮>
2:（語+区切り+値 の形。字面は秘匿検査の指示に従い削除）
3:（同上・別の語）
$ grep -c -i -E "..." <囮>
2
```

**一以上を返した。検査は素通しではない。** 囮は版管理へ入れていない
（`git status --porcelain | grep -c 'decoy_secret'` → `0`）。

**(b) 公開鍵だけであることの三つの検査。** 秘密鍵の書き出しを模した囮に同じ三つをかけた。

- 公開鍵に対して: `ssh-ed25519 AAAAC3NzaC1lZDI1NT` / `PRIVATE` `0` 件 / 行数 `1`
- 囮に対して: 鍵の書き出しの標識行 / `PRIVATE` `2` 件 / 行数 `3`

**三つすべてで外れた。** 囮は版管理へ入れていない
（`git status --porcelain | grep -c 'decoy'` → `0`）。

**(c) 待ち受けの検査。** 同じ検査器が `port_22=LISTEN` を返しており、
**待ち受けを検出する能力そのものは働いている**（常に `-` を返す壊れた検査ではない）。

## 6. 変更範囲と未追跡

### 開始時（契約配置の直後）

```
?? docs/sessions/digest/2026-08-22-52ba4658-47af-4d90-85e2-27ab8c014c0f.md
?? docs/sessions/digest/2026-08-22-7c2986d7-0ce3-48b3-8d32-60a03a93c8d2.md
?? scripts/sync/hosts/
?? tasks/T-2026-08-22-lecun-node-foundation/
```

`porcelain_count_start=4`。**うち 3 件が契約以前から在った版管理外の成果物。**

### 契約の範囲で増やしたもの

- `scripts/sync/hub_keys/lecun.pub`（公開鍵）
- `scripts/sync/device_ids/lecun.txt`（識別子）
- `tasks/T-2026-08-22-lecun-node-foundation/`（`spec.yaml` `SPEC.md` `audit.md` `RESULT.md` `result.yaml`）
- `tasks/inbox.d/T-2026-08-22-lecun-node-foundation.md`
- 生成物（`context/auto/` `tasks/inbox.md`）

**開始時の 3 件は一つも削除・移動・commit していない。**
`docs/sessions/digest/*` と `scripts/sync/hosts/` は未追跡のまま残す。

commit 直前の実測（`git status --porcelain`、11 行）:

```
 M context/auto/followups.md
 M context/auto/results_recent.md
 M context/auto/tasks_summary.csv
 M tasks/inbox.md
?? docs/sessions/digest/2026-08-22-52ba4658-47af-4d90-85e2-27ab8c014c0f.md
?? docs/sessions/digest/2026-08-22-7c2986d7-0ce3-48b3-8d32-60a03a93c8d2.md
?? scripts/sync/device_ids/lecun.txt
?? scripts/sync/hosts/
?? scripts/sync/hub_keys/lecun.pub
?? tasks/T-2026-08-22-lecun-node-foundation/
?? tasks/inbox.d/T-2026-08-22-lecun-node-foundation.md
```

**開始時の 3 件がすべて残っている**（それぞれ `grep -c` で `1`）。
`M` の 4 件はいずれも生成物であり、`make taskindex` / `make inbox` の出力である
（`make taskindex-check` `make inbox-check` とも `exit 0`）。

**tasks/README.md は「抽出物は版管理へ記録する」（`git add docs/sessions/digest/`）と書くが、
本契約の禁止 1 は未追跡の成果物を commit することを禁じる。契約を優先して残した。**
どちらが優先かは未決であり、申し送りへ置いた。

**追跡ファイルの変更は 0 件**（`git status --porcelain | grep -c -E '^( M|M |MM| D|D |R )'` → `0`）。
`experiments/**` `transfer/**` `data/**` `runindex/**` には一切触れていない。

`make forbidden-check` → `{"status": "pass", "violations": [], "errors": []}`、`forbidden_exit=0`。

### 試験

追跡ファイルを一つも変更していないため、**試験対象の木は `origin/phase0` と同一**である。
よって前後の実測は同じ値になる。

```
5 failed, 462 passed, 10 skipped, 22 warnings in 20.48s
```

失敗 5 件はいずれも**本契約以前から在る失敗**であり、内容も無関係である。

- `tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics`
- `tests/test_research_logger.py::test_log_run_idempotent`
- `tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally`
- `tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit`
- `tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block`

`test_research_logger` の 4 件は Notion への記録が `None` を返すことによる
（`assert rlog.log_run(step="test") == "page-abc"` が `assert None == 'page-abc'` で落ちる）。
**`scripts/load_env.sh` が使えず資格情報が入らない状況と整合する。**
`test_engines` の 1 件は未追跡の理由で落ちており、**本契約では触れていない**。

---

## 7. 送出

### commit

```
$ git add tasks/T-2026-08-22-lecun-node-foundation/ tasks/inbox.d/T-2026-08-22-lecun-node-foundation.md \
          scripts/sync/hub_keys/lecun.pub scripts/sync/device_ids/lecun.txt \
          context/auto/ tasks/inbox.md
$ git diff --cached --name-only | grep -c ''
12
```

**`-A` は使っていない。** 明示した 8 パスだけを staged にした（展開後 12 ファイル）。
**開始時の未追跡 3 件は staged に含まれていない。**

```
$ git --no-pager log -1 --format='%h %s'
9c1a8b3d feat(sync): build foundation and publish hub key and device id on lecun
```

`12 files changed, 1811 insertions(+), 75 deletions(-)`

### push

```
$ git push -u origin HEAD
 * [new branch]        HEAD -> feat/lecun-node-foundation
branch 'feat/lecun-node-foundation' set up to track 'origin/feat/lecun-node-foundation'.

$ git --no-pager status -sb | head -1
## feat/lecun-node-foundation...origin/feat/lecun-node-foundation
```

**上流と差が無い（ahead/behind の表示なし）。**

### PR

```
$ gh pr view 122 --json number,state,isDraft,baseRefName,headRefName
{"baseRefName":"phase0","headRefName":"feat/lecun-node-foundation","isDraft":false,"number":122,"state":"OPEN"}
```

**PR #122**（`phase0` ベース、`OPEN`、下書きではない）。
https://github.com/takuya3h/m2/pull/122

`gh pr create` は `Warning: 3 uncommitted changes` を出した。**これは開始時の未追跡 3 件であり、
契約の禁止 1 に従って意図的に残したものである。**

### 送出後の未追跡

```
?? docs/sessions/digest/2026-08-22-52ba4658-47af-4d90-85e2-27ab8c014c0f.md
?? docs/sessions/digest/2026-08-22-7c2986d7-0ce3-48b3-8d32-60a03a93c8d2.md
?? scripts/sync/hosts/
```

**開始時の 3 件がそのまま残っている。減っていない。**

### 台帳への返送

**行っていない。** SPEC が「台帳へは返さない。起票者は版管理から読む」と明記しており、
`scripts/load_env.sh` も使えないため `make task-report` の経路自体が動かない。

---

## 8. 逸脱（deviations）

**逸脱は「なし」ではない。** 次の 5 件がある。

1. **repo の位置。** SPEC の `~/slocal2/m2` は存在しないため `~/slocal/m2` で作業した。
   `~/slocal2` が無いことを `ls` で確かめてから判断した（起票者の誤り。§9-1）。
2. **分岐を新規に切っていない。** SPEC は `git checkout -b feat/lecun-node-foundation origin/phase0`
   を指示するが、**分岐は既に存在し `origin/phase0` と同一の先頭を指していた**
   （`rev-list --left-right --count` が `0 0`）。切り直すと未追跡の扱いに影響が出るため、
   既存の分岐をそのまま使った。最新であることは先頭の記録で確かめてある。
3. **契約の取得を手で行っていない。** SPEC は「配られた本文から置く」と書くが、
   `tasks/T-2026-08-22-lecun-node-foundation/` には `spec.yaml` と `SPEC.md` が
   セッション開始時点で既に置かれていた（13:19 時点、未追跡）。**再取得していない。**
4. **貼り直しを行っていない。** SPEC Task 1 Step 2 の主眼である `.venv` の修復は、
   実測の結果**壊れていなかった**ため実施対象が無かった（§3 判定 2・3）。
   同様に `jsonschema` の導入（Step 3）と `git remote set-url --push`（Step 5）も
   **既に満たされていたため実行していない**。
5. **論理名を 3 ファイルへ置いた。** 契約は `~/.zshenv` と `~/.profile` の 2 つを求めるが、
   道具 `setup_host_servername.sh` は `~/.bashrc` にも同じ 3 行を置く。
   手で 2 つだけに絞ることもできたが、**道具を使うほうが冪等性と戻し方が保証される**ため
   道具をそのまま使った。契約の要求は満たしている（上位集合）。

---

## 9. 起票者の誤り（issuer_defects）

### 9-1. repo の位置を確かめずに断定した — `asserted_without_measuring`

SPEC 冒頭が `**repo:** ~/slocal2/m2` と書き、Task の前提でも `cd ~/slocal2/m2` を指示する。
**`/home/ubuntu/slocal2` は存在しない**（`ls: cannot access '/home/ubuntu/slocal2/': No such file or directory`）。
実体は `/home/ubuntu/slocal/m2` である。
**指示どおり実行すると最初の命令 `cd` が失敗し、以降の `git fetch` 等がすべて
別のディレクトリ（`cd` 失敗時の現在位置）で走るか、`set -e` 下では即座に止まる。**

### 9-2. 鍵が一件も無い状況で zsh のグロブが止まる — `shell_assumption`

Task 3 Step 1 の

```
for f in ~/.ssh/id_*; do
  case "${f}" in
    *.pub) ssh-keygen -lf "${f}" 2>/dev/null ;;
  esac
done
```

は bash ではマッチが無いとき未展開の文字列で 1 回まわり、`case` で落ちて無害に終わる。
**ログインシェルは zsh であり、zsh は既定でマッチが無いと `no matches found` を出して
その場でコマンドを失敗させる。** 本契約は「保守作業で全て失われた」新規構築を前提としており、
**`~/.ssh/id_*` が一件も無いのは想定される正常な状態である。**
指示どおり実行すると `(eval):1: no matches found: /home/ubuntu/.ssh/id_*` が出て
既存確認の段階で止まる。実際にそうなった。`ls -la ~/.ssh/` の一覧で代替して確かめた。

### 9-3. 道具に `--help` が在ると確かめずに書いた — `asserted_without_measuring`

Task 2 Step 2 が `scripts/sync/setup_host_servername.sh --help 2>&1 | head -20` を指示し、
「道具を読んでから使う」と続ける。**この道具は `--help` を受け付けない。**
実行すると `ERROR: 不明なオプション '--help'（--dry-run / --verify のみ）` を返す。
**指示どおりでは使い方が得られない。** 道具の先頭 60 行を直接読んで用法を得た。

---

## 10. 陽性対照（positive_controls）

§5.2 に記した 2 つに加え、判定が空振りでないことを次のとおり確かめた。

| 判定 | 何を入れれば失敗するはずか | 実際に何が起きたか |
|---|---|---|
| 公開鍵だけであることの三つの検査 | 秘密鍵の書き出しを模した囮 | 三つすべてで外れた（先頭 鍵の書き出しの標識行 / `PRIVATE` `2` 件 / 行数 `3`） |
| 待ち受けの不在（`22000`・`8384`） | 実際に待ち受けている口 | 同じ検査器が `port_22=LISTEN` を返した。検出能力は働いている |
| 論理名が新しいシェルで解決されること | 設定前の状態 | 設定前は `SERVERNAME=unset`、設定後は `zsh -c`・`bash -lc` とも `lecun`。**同じ命令が前後で違う値を返した** |
| 配布物の要約値の照合 | 別の版の配布物 | **UNKNOWN。** 別版を落として不一致になることは確かめていない（禁止 3・中心と版を揃える要求のため、意図的に測っていない） |
| `make forbidden-check` が禁止領域を捕まえること | 禁止領域下のファイルの変更 | **UNKNOWN。** 禁止領域を意図的に汚す検査は行っていない |

---

## 11. 状態

`status: pass`

**escalate_if の 5 条件はいずれも成立していない。**

| escalate_if | 実測 |
|---|---|
| 版管理外の未追跡の成果物が失われた | 失われていない（開始時の 3 件がすべて残る） |
| 実行環境の中身を破棄した | 破棄していない（`6.2G` → `6.2G`、`--clear` 未実行） |
| 配布物の要約値が中心と一致しない | 一致した（`c04ffbde…fd60` / `32ab747e…ca1dd`） |
| 識別子を読み取れず公開できない | 読み取れた。一行で公開した |
| 同期処理が意図せず起動した | 起動していない（`22000`・`8384` とも非待ち受け、`pgrep -x` 該当なし） |

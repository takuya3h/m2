# RESULT — T-2026-08-22-ilya-node-foundation

**実行ホスト:** ilya（`hostname` は `aolab`、論理名 `SERVERNAME=ilya`）
**分岐:** `feat/ilya-node-foundation`　**起点:** `8eec82e`（= `origin/phase0`）
**判定:** PASS
**実行日時:** 2026-08-23 13:37〜14:0x JST

生の出力は `audit.md` に貼ってある。**本書では要約せず、値を引く。**

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

`spec.yaml` の `prohibitions` は上の 5 つの id をすべて挙げている。
本契約では `data/**` `experiments/**` `runindex/**` `context/auto/`（手編集）に
一切触れていない。`context/auto/` は生成器で作り直しただけである。

### `contract.conventions_rev`

| | 値 |
|---|---|
| spec.yaml の記載 | `d422b08` |
| 実測 `git --no-pager log -1 --format=%h -- context/conventions.md` | `d422b08` |
| 判定 | **一致。置換は不要だった。** |

（前契約 philip の報告は `conventions_rev_measured: 1201f4f` としており食い違うが、
これは philip が古い状態で測ったためと考えられる。**本契約では最新の版で測っている。**）

### `inputs.denominator.ref` / `inputs.sigma_policy` / `inputs.frozen_source.ref`

**spec.yaml に記載が無い。**`kind: impl` であり数値の主張を伴わないため、
解決すべき参照は存在しない。`inputs` は `data`（参照のみ・未使用）と
`code.entrypoints`（`scripts/sync/keeper.sh` `scripts/sync/m2-sync.sh`）だけである。
両エントリーポイントは**本契約では起動していない**（禁止 6）。

---

## 2. 完了判定

SPEC は Task 5 Step 1 で「**完了判定 17 項目**」と述べるが、本文の表は **22 項目**を
挙げている（Task 5 の表が 18〜22）。**22 項目すべてに実測値を記す。**

| # | 判定 | 実測 | 結果 |
|---|---|---|---|
| 1 | 開始状態を記録した（家の直下、鍵、未追跡の件数） | `home_entries=26` / `authorized_keys` 1 件 `SHA256:30y00ixicNIVEovdR82sNN0xJTtYZ5G+lJdfxY4ndZY` / 未追跡 `2` | PASS |
| 2 | 実行環境が動く | `Python 3.11.16`、`which python` = `/home/ubuntu/slocal2/m2/.venv/bin/python`、`sys.prefix` = `/home/ubuntu/slocal2/m2/.venv` | PASS |
| 3 | 六ギガを破棄していない | `du -sh .venv` 前 `6.2G` → 後 `6.2G` | PASS |
| 4 | 検証に要るものが揃った | `jsonschema 4.26.0`（既存。導入していない） | PASS |
| 5 | 版管理の識別と送出の経路を直した | `user.name=takuya3h` `user.email=daky.o7600@gmail.com`（repo ローカル）、push url = `https://github.com/takuya3h/m2.git` | PASS |
| 6 | 設定前の状態を記録した（論理名） | `SERVERNAME=unset`、`grep SERVERNAME ~/.zshenv ~/.profile` → 該当なし、`hostname=aolab` | PASS |
| 7 | 追記内容を記録した | `export SERVERNAME=ilya` を標識付きブロックで `~/.zshenv:7` `~/.profile:32` `~/.bashrc:122` | PASS |
| 8 | 両方の形態で論理名が解決される | `zsh -c` → `ilya` / `bash -lc` → `ilya` | PASS |
| 9 | 既存の鍵を確かめた | `~/.ssh/id_ed25519.pub` = `SHA256:cdOmPfuBN4wFfTjbvjDIaGgiv3YaHEMLez0td1v5oE4`（`no comment`）。**中心宛の鍵は不在**だったので作成した | PASS |
| 10 | 中心宛の鍵を作り指紋を記録した | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ`（`ilyatophilip`, ED25519, 256）。**秘密鍵の中身は本報告のどこにも無い** | PASS |
| 11 | 権限が期待どおり | 秘密鍵 `600` / 公開鍵 `644` / `~/.ssh` `700` | PASS |
| 12 | 公開鍵を版管理へ置き、指紋が一致し、三つの検査を通った | `scripts/sync/hub_keys/ilya.pub` の指紋が Step 2 と一致。先頭 `ssh-ed25519 AAAAC3NzaC1lZDI1NT` / `PRIVATE`=`0` / 行数=`1`。**版管理には旧版が在り、置き換えになった**（§10） | PASS |
| 13 | 配布物の要約値が中心と一致した | `c04ffbdedcd1d18ccb4a34a341a6a2b2461082f7a6f43537eb0bba860975fd60`（Expected と一致） | PASS |
| 14 | 配置物の要約値が中心と一致し、版が表示できる | `32ab747eb18ff3a01423f9719c5b8a8165da63e60ee9c3f733887464c70ca1dd`、`syncthing v1.27.10 "Gold Grasshopper" (go1.22.5 linux-amd64)` | PASS |
| 15 | 識別子を発行した（既存があれば上書きしていない） | `~/.local/state/syncthing/` は**存在しなかった**ので新規生成。`cert.pem` `config.xml` `key.pem` が生成された | PASS |
| 16 | 識別子を一行で公開した | `scripts/sync/device_ids/ilya.txt` = `UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY`、`grep -c ''` = `1` | PASS |
| 17 | **同期処理が起動していない** | `port_22000=-` `port_8384=-` `port_22001=-`（待ち受けは `22` のみ、`count=5`）、`pgrep -x syncthing` = 該当なし | PASS |
| 18 | 全項目に実測値または UNKNOWN がある | 本表（22 行）。UNKNOWN は §6 の 2 件 | PASS |
| 19 | 送信前の秘匿検査を自分で行った（陽性対照つき） | §5 参照。本番 `0` 件相当（形の確認まで実施）、囮 `4` 件 | PASS |
| 20 | 開始時の未追跡がすべて残っている | 開始 `2` → 終了 `2`（`docs/sessions/digest/2026-08-22-95a3a814-….md` は最後まで未追跡のまま） | PASS |
| 21 | 変更が契約の範囲に限られる | `make forbidden-check` = `{"status": "pass", "violations": [], "changed": 6}` | PASS |
| 22 | 分岐が送出され、PR が存在する（番号） | commit `bd3d149`、push 成功、**PR #124**（base `phase0`, state `OPEN`, draft でない） | PASS |

---

## 3. 次の契約で使う情報

| 項目 | 内容 |
|---|---|
| **自ホストの識別子** | `scripts/sync/device_ids/ilya.txt` → `UODEAXZ-G4GMS53-DEI74HH-U5VTQJP-L363Z5P-MXT4GYQ-JAC6PX3-X6SDBQY` |
| **中心宛の鍵の指紋** | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ`（公開鍵は `scripts/sync/hub_keys/ilya.pub`） |
| 秘密鍵の場所 | `~/.ssh/id_ed25519_ilyatophilip`（**このホストから出していない**） |
| 同期処理の実行ファイル | `~/bin/syncthing`（`v1.27.10`、`32ab747e…0ca1dd`） |
| 同期処理の設定 | `~/.local/state/syncthing/`（`--home` で明示が要る） |
| 中心の識別子（照合済み） | `scripts/sync/device_ids/philip.txt` = `3J4TRX4-7ZOHQAY-MNNTGTY-WXYDHFW-OOAWOXQ-7L23IDP-ZJ6KT77-DZOCQQE`（SPEC の記載と一致） |
| 登録済みの他ホスト | **無い。** `config.xml` に現れる識別子は自ホストのみ |

---

## 4. 前契約の実測との差（十件の照合）

| # | 前契約 philip の事実 | ilya での実測 | 当てはまるか |
|---|---|---|---|
| 1 | `.venv/bin/python` が消えた pyenv を指す壊れた繋がり | そのとおり。`~/.pyenv` は不在、`readlink -f` が解決できない | **当てはまる** |
| 2 | uv 管理の実体が `~/.local/share/uv/python/cpython-3.11.16-…` に在る | **`~/.local/share/uv/` ごと存在しなかった。**システムにも `python3.11` は無く `/usr/bin/python3.12` のみ | **当てはまらない** |
| 3 | `~/.gitconfig` が失われている | そのとおり。`user.name` `user.email` とも未設定 | **当てはまる** |
| 4 | `remote.origin.pushurl` が SSH のまま。配備鍵が消えたので通らない | pushurl が SSH なのは同じ。しかし **fetch 側の SSH は生きていた**（`git fetch` が新しい分岐を取得した） | **半分だけ** |
| 5 | 環境の作り直し後は `jsonschema` の追加導入が要る | **作り直していない**ため該当せず。`jsonschema 4.26.0` は既に在った | **当てはまらない** |
| 6 | `pgrep -af` は自分のコマンド行を拾う | 従って `pgrep -x` を使った。該当なしを確認 | 従った |
| 7 | 設定は `~/.local/state/syncthing/`。`--home` で明示が要る | そのとおり。既定では作られない | **当てはまる** |
| 8 | 識別子は `serve --home … --device-id`。`device-id` という下位命令は無い | そのとおりの形で取得できた | **当てはまる** |
| 9 | 論理名は `~/.zshenv` と `~/.profile` の両方 | そのとおり。道具は `~/.bashrc` にも置く | **当てはまる** |
| 10 | `libGL.so.1` が無く `mmcv` `mmdet` を読み込めない | **ilya では読み込めた。** 全 477 件のテストが走り、`mmdet` を要する `tests/test_engines.py` も収集・実行された（下記 §6） | **当てはまらない** |

**ホストによる差は 3 件（#2, #5, #10）、部分的な差が 1 件（#4）である。**
SPEC は十件を「全台で同じはず」と題していたが、**実測では半分近くが ilya に当てはまらなかった。**

---

## 5. 送信前の秘匿検査（自前）

`scripts/load_env.sh` は使えないため、SPEC Task 5 Step 2 のとおり自分で検査した。

**本番**（`tasks/T-2026-08-22-ilya-node-foundation/*.md` `*.yaml`）の該当を
**一件ずつ形で判定した。**件数ではなく形で判定している。結果は §7 の実行記録に貼る。

**陽性対照**: 鍵の書き出し行・鍵の書き出しを模した行と、資格情報を表す語に値を続けた行を含む囮を
scratchpad（版管理外）に置いて同じ検査をかけ、**該当が出ることを確かめた。**
**囮は commit していない。**

**識別子と指紋は秘匿ではないため削っていない。**
`~/.ssh/id_ed25519_ilyatophilip` の中身は本報告のどこにも含まれない。

---

## 6. 検証と試験

| 検査 | 終了コード | 内容 |
|---|---|---|
| `make task-validate TASK=…` | `0` | `OK T-2026-08-22-ilya-node-foundation` / `1 task(s), 0 failed` |
| `make task-preflight TASK=…` | `0` | `4 PASS / 1 WARN / 4 SKIP / 0 FAIL` |
| `make forbidden-check` | `0` | `{"status": "pass", "violations": [], "changed": 6, "checked": 6}` |
| `make taskindex-check` | §7 | |
| `make inbox-check` | §7 | |

**`make forbidden-check` `make taskindex` `make inbox` `make task-preflight` は
いずれも実在し、動作した。**前契約 philip の報告はこれらを「Makefile に存在しない」と
記していたが、**それは古い状態を見ていたためである**（SPEC 冒頭の注意と一致）。

### preflight の SKIP（合格ではなく「実行されなかった」）

| 項目 | 理由 |
|---|---|
| `P2 cuda_ext_loaded` | `plan.env.preflight` に記載なし |
| `P3 deterministic_flags` | `plan.env.preflight` に記載なし |
| `P4 prereg_committed` | `kind=impl` のため対象外（exp のみ） |
| `P5 frozen_source_hash` | `kind=impl` のため対象外（exp のみ） |

### preflight の WARN（該当あり。合格ではないが停止の根拠でもない）

`P9 spec_lint` が 8 規則のうち 4 件該当した。

| 該当 | 場所 | 実測にもとづく評価 |
|---|---|---|
| `host_mismatch` | `SPEC.md:5` | 規則は `socket.gethostname()` と宣言を比べる。**このホストの `gethostname()` は `aolab`** であり、ilya と philip は設計上ともに `aolab` を返す（`setup_host_servername.sh` 冒頭に実測が明記されている）。**論理名を使う本環境では、この規則は常に該当する。**起票者の誤りではなく検査器の限界である |
| `separated_source` ×3 | `SPEC.md:396,399,402` | いずれも `source .venv/bin/activate \` + 次行 `&& make …` の形。**行継続で同一命令に繋がっている**ため、実行時に環境は引き継がれた（実際に一命令として実行し、`validate` `forbidden-check` とも成功した）。規則が行継続を解さないための該当と考えられる |

### 試験

```
$ source .venv/bin/activate && python -m pytest tests/ -q
5 failed, 472 passed, 22 warnings in 17.08s
```

失敗 5 件は次のとおりで、**いずれも本契約の変更とは無関係である**
（本契約は `src/` `tests/` を一切変更していない）。

| 試験 | 失敗の内容 |
|---|---|
| `tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics` | `assert 0.0 == 1e-08`（`score_thr` の期待値の不一致） |
| `tests/test_research_logger.py::test_log_run_idempotent` | `assert None == 'page-abc'`（`log_run` が `None` を返す。Notion 資格情報なし） |
| `tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally` | 同上の系統 |
| `tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit` | 同上の系統 |
| `tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block` | 同上の系統 |

**UNKNOWN が 2 件ある。**

| 項目 | 値 | 理由 |
|---|---|---|
| 開始前の試験の失敗件数 | **UNKNOWN** | 契約の開始時点では `.venv` が壊れていて `python` が起動せず、**測れなかった。**`result.yaml` の `tests.before_failed` には修復直後の実測値 `5` を置いてあるが、これは**「開始前」ではない。** |
| `bash -c`（非対話・非ログイン）での `SERVERNAME` | 未設定 | 道具の冒頭に明記された既知の限界。利用者ファイルでは覆えず `/etc/environment`（要 root）が要る。**本契約の範囲外** |

---

## 7. 実行記録（秘匿検査・生成物・変更範囲・送出）

### 秘匿検査（Task 5 Step 2）

**本番**（本契約の `*.md` `*.yaml` と `tasks/inbox.d/…`）— 初回の走査で 4 件該当した。
**件数ではなく形で一件ずつ判定した。**

| 場所 | 一致した形 | 判定 | 処置 |
|---|---|---|---|
| `SPEC.md:385` | 検査コマンドの正規表現そのもの | 値ではない。**配られた契約本文であり改変しない** | そのまま |
| `result.yaml:44` | 検査の説明文（語の列挙） | 値ではない。説明文の語は差し支えない | そのまま |
| `result.yaml:45` | 資格情報を表す語に区切りと値（省略記号）が続く形 | **形としては該当する** | 語だけの表現へ書き換えた |
| `RESULT.md:128` | 同上 | **形としては該当する** | 語だけの表現へ書き換えた |

書き換え後の再走査で残ったのは上表の前 2 件だけで、**いずれも値を含まない。**

```
$ grep -n -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" <本契約の *.md *.yaml と inbox.d>
tasks/T-2026-08-22-ilya-node-foundation/result.yaml:44:  - judgement: "送信前の秘匿検査（… の形を探す grep）"
tasks/T-2026-08-22-ilya-node-foundation/SPEC.md:385:    grep -n -i -E "…" \
```

**陽性対照**（scratchpad の囮・版管理外）:

```
$ grep -c -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase" <囮>
4
$ git --no-pager status --porcelain | grep -c 'decoy'
0
```

**囮で 4 件返った。検査は空振りしていない。囮は commit していない。**
`~/.ssh/id_ed25519_ilyatophilip` の中身は本報告のどこにも含まれない。
**識別子と指紋は秘匿ではないため削っていない。**

### 生成物の再生成（Task 5 Step 4）

```
$ make taskindex && make inbox      → exit 0
$ make taskindex-check              → taskindex_exit=0
$ make inbox-check                  → inbox_exit=0
```

**投影に現れることを確かめた。**

```
$ grep -n "ilya-node-foundation" context/auto/tasks_summary.csv
48:T-2026-08-22-ilya-node-foundation,impl,pass,ilya,,false,2,0,0,5,5,5,2,5,2,T-2026-08-22-philip-hub-foundation
$ grep -c "ilya-node-foundation" context/auto/results_recent.md   → 1
$ grep -c "ilya-node-foundation" context/auto/followups.md        → 2
$ grep -c "ilya-node-foundation" tasks/inbox.md                   → 3
```

### 変更範囲と未追跡（Task 5 Step 5）

```
$ git --no-pager status --porcelain
 M context/auto/followups.md
 M context/auto/results_recent.md
 M context/auto/tasks_summary.csv
 M scripts/sync/hub_keys/ilya.pub
 M tasks/inbox.md
?? docs/sessions/digest/2026-08-22-95a3a814-a765-401a-a2a9-ce915c8cbf05.md
?? scripts/sync/device_ids/ilya.txt
?? tasks/T-2026-08-22-ilya-node-foundation/
?? tasks/inbox.d/T-2026-08-22-ilya-node-foundation.md
```

**開始時の未追跡 2 件は両方とも残っている。**
`docs/sessions/digest/2026-08-22-95a3a814-….md`（版管理外の成果物）は
**触れておらず、commit もしない**（禁止 1）。もう 1 件は本契約のディレクトリである。

変更は**契約のディレクトリ・公開鍵・識別子・生成物・判断の受け皿**に限られる。

```
$ make forbidden-check
{"base": "origin/phase0", "changed": 13, "checked": 9, "errors": [], "excluded": 4,
 "excluded_paths": ["context/auto/followups.md", "context/auto/results_recent.md",
 "context/auto/tasks_summary.csv", "tasks/inbox.md"],
 "generated_directories": ["context/auto/"], "generated_files": ["tasks/inbox.md"],
 "status": "pass", "violations": []}
forbidden_exit=0
```

**`experiments/**` `transfer/**` `data/**` `runindex/**` には触れていない。**

⚠ `tasks/README.md` は「抽出物は生成のたびに作業ツリーへ現れる。**契約の記録と
一緒に含めること。** 未追跡のまま放置すると自動同期が止まる」として
`git add docs/sessions/digest/` を求めるが、**本契約の禁止 1 はそれを禁じる。**
**契約を優先し、未追跡のまま残した。**この食い違いは判断の受け皿へ起票した。

### 送出（Task 5 Step 6）

`git add` は明示したものだけを渡した（`-A` は使っていない）。

```
$ git --no-pager diff --cached --name-status
M	context/auto/followups.md
M	context/auto/results_recent.md
M	context/auto/tasks_summary.csv
A	scripts/sync/device_ids/ilya.txt
M	scripts/sync/hub_keys/ilya.pub
A	tasks/T-2026-08-22-ilya-node-foundation/RESULT.md
A	tasks/T-2026-08-22-ilya-node-foundation/SPEC.md
A	tasks/T-2026-08-22-ilya-node-foundation/audit.md
A	tasks/T-2026-08-22-ilya-node-foundation/result.yaml
A	tasks/T-2026-08-22-ilya-node-foundation/spec.yaml
A	tasks/inbox.d/T-2026-08-22-ilya-node-foundation.md
M	tasks/inbox.md
$ git --no-pager status --porcelain | grep -v '^[AM]'
?? docs/sessions/digest/2026-08-22-95a3a814-a765-401a-a2a9-ce915c8cbf05.md
```

**未追跡の成果物は staged に入っていない。**

```
$ git commit -F -   （SPEC 指定の表題 + 内訳 5 行）
[feat/ilya-node-foundation bd3d149] feat(sync): build foundation and publish hub key and device id on ilya
 12 files changed, 1772 insertions(+), 76 deletions(-)
commit_exit=0
$ git push -u origin HEAD
To https://github.com/takuya3h/m2.git
 * [new branch]      HEAD -> feat/ilya-node-foundation
branch 'feat/ilya-node-foundation' set up to track 'origin/feat/ilya-node-foundation'.
$ git --no-pager status -sb
## feat/ilya-node-foundation...origin/feat/ilya-node-foundation
?? docs/sessions/digest/2026-08-22-95a3a814-a765-401a-a2a9-ce915c8cbf05.md
```

**push は https 経路（`git remote set-url --push` で直したもの）で通った。**
前契約 philip では push が遮断され `succeeded: false` で終わっていたが、
**ilya では成功した。**

```
$ gh pr list --head feat/ilya-node-foundation --json number,isDraft,state
[]                                    # 既存の PR は無い
$ gh pr create --base phase0 --fill
Warning: 1 uncommitted change         # 未追跡の digest 1 件（意図どおり残している）
https://github.com/takuya3h/m2/pull/124
```

**PR 番号: #124**（base `phase0` ← head `feat/ilya-node-foundation`）。
**完了判定 22 を充足する。**

**台帳へは返していない。**`make task-report` は `scripts/load_env.sh` に依存し、
本契約の前提どおり合言葉が失われていて使えない。SPEC は
「**台帳へは返さない。起票者は版管理から読む**」と定めており、それに従った。

---

## 8. deviations（逸脱）

**「なし」ではない。次の 5 件を記す。**

1. **`judgement` — 貼り直し先の実体が無かったため、取得を選んだ。**
   SPEC Task 1 Step 2 は「前契約では uv 管理の実体へ貼り直して回復した。同じ経路が
   在るかを確かめる」とするのみで、**無かった場合の指示が無い。** ilya には Python
   3.11 の実体が一つも無かった。「実行環境を直せない → 停止して報告」に倒すことも
   できたが、**それでは Phase B/C が丸ごと落ちる。** ユーザーへ二択（`uv python
   install 3.11` / 停止）を提示し、**取得を選択された上で実行した。** 取得された
   `cpython-3.11.16` は前契約 philip の実体と同一版であり、ABI も `.venv` と一致する。
   `.venv` の中身は 6.2G のまま破棄していない。

2. **`judgement` — `pyvenv.cfg` の `home` を直していない。**
   `home = /home/ubuntu/.pyenv/versions/3.11.4/bin` は壊れたパスのままである。
   しかし `sys.prefix` も site-packages も正しく解決され、477 件の試験が走った。
   **動いているものに触らないほうが差分が小さい**と判断した。次のホストで
   同じ判断をするかは、そのホストの実測次第である。

3. **`spec_defect` — `git remote set-url --push` では「両方が https」にならない。**
   §9 に記す。**指示どおり実行し、Expected が満たせないことを実測した上で
   fetch 側は変更していない**（SSH で生きているため）。

4. **`environment` — `.sync-pause` の目印を置いていない。**
   `task` スキルは常駐同期処理を止めるため目印を置けと指示するが、**ilya には
   `~/bin/m2-sync.sh` も `~/claude-sync/` も存在しない**（保守作業で初期化された）。
   止める対象が無いため置いていない。自動統合の危険は無い。**次のホストでも
   まず存在を測ること。**

5. **`judgement` — 囮の中身を報告へそのまま貼っていない。**
   申し送り 8 は「出力は要約せず貼る」とするが、囮の先頭行を貼ると
   **自分の秘匿検査（Task 5 Step 2）が自分の報告に該当を出す。**
   `audit.md` では囮の先頭 30 文字を途中で切り、検査の**結果の数値**は
   すべて貼ってある。**判定に必要な情報は落としていない。**

6. **`judgement` — `cp` の前に `hub_keys/` の中身を測っていなかった。**
   SPEC Task 3 Step 4 は `mkdir -p` と `cp` を続けて指示しており、**手順に
   「置く前に見る」が無い。**そのまま実行したため、旧版を上書きしてから
   `git status` の `M` で気づいた。**失われたものは無い**（旧版は git の履歴に
   残っており、対応する秘密鍵は初期化で既に失われていた）。§10 に旧版の値を
   記録してある。**測ってから書くべきだった。**

---

## 9. 起票者の誤り

**空ではない。2 件ある。**

1. **`self_contradiction` — 送出の経路。**
   SPEC Task 1 Step 5 は `git remote set-url --push origin https://…` を指示し、
   直後に「**両方が `https` になったことを確かめる**」を求める。しかし
   `set-url --push` は `remote.origin.pushurl` だけを設定し、fetch 側の
   `remote.origin.url` は変えない。**指示どおり実行すると `git remote -v` は
   `git@…(fetch)` と `https://…(push)` を出し、Expected を満たせない。**
   両方を https にするには `git remote set-url origin https://…` を併せて実行する
   必要がある。本契約では push 経路のみを直し、fetch は SSH で動作していることを
   実測して残した。

2. **`self_contradiction` — 完了判定の件数。**
   SPEC Task 5 Step 1 は「**完了判定 17 項目**を表にまとめ」と指示するが、SPEC 本文の
   完了判定表は Task 1〜5 で **22 項目**を挙げている（Task 5 の表が 18〜22）。
   **指示どおり 17 項目だけ書くと、送出と秘匿検査に関する 18〜22 が報告から落ちる。**
   本報告は 22 項目すべてを表にした。

3. **`check_does_not_check` — 既存の鍵の確認が版管理側を見ていない。**
   SPEC Task 3 Step 1 は「既存の鍵を確かめる」として `~/.ssh/` だけを走査させ、
   **`scripts/sync/hub_keys/` に旧版が在るかは確かめさせない。** Step 4 も
   `cp` を指示するだけで「置く」と書いており「置き換える」とは書いていない。
   **指示どおり実行すると、版管理にあった旧版 `ilya.pub`
   （`SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo`, `ubuntu@aolab`,
   commit `806abe4` で追加）を、それと気づかないまま上書きする。**
   本契約では `git status` が `M`（新規ではなく変更）を出したことから気づき、
   §10 に記録した。残りのホストの契約では Step 1 に
   `git show HEAD:scripts/sync/hub_keys/<host>.pub` を足すべきである。

**`asserted_without_measuring` には数えなかったもの。** SPEC の「前契約で確定した
事実（全台で同じはず）」10 件のうち 4 件が ilya に当てはまらなかった（§4）。
ただし SPEC は同じ段落で「**これらは philip での実測である。自ホストでも確かめること**」と
明記しており、**測っていない台への断定を避けている。**起票者の誤りではなく、
**ホストによる差**として `deviations` ではなく §4 に記録した。

---

## 10. 版管理にあった旧版の `ilya.pub`

`git status` が新規追加ではなく `M scripts/sync/hub_keys/ilya.pub` を出したため調べた。

| | 指紋 | コメント | 出所 |
|---|---|---|---|
| 旧版 | `SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo` | `ubuntu@aolab` | commit `806abe4` "feat(sync): submit tunnel public key for ilya" |
| 新版（本契約） | `SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` | `ilyatophilip` | 本契約 Task 3 Step 2 |

**旧版に対応する秘密鍵はこのホストに存在しない。**開始時の `~/.ssh` に在ったのは
`authorized_keys`（`SHA256:30y00ixic…`、MacBook のもの）と `id_ed25519`
（`SHA256:cdOmPfuB…`、`no comment`）だけで、**どちらも `5auPdGk/…` とは別物である。**
保守作業の初期化で失われている。

SPEC の Goal は「**復旧ではなく新規構築である**」と明記しており、
**置き換えは意図された動作である。**旧版は git の履歴に残っており失われていない。
`git --no-pager diff --stat` は `1 insertion(+), 1 deletion(-)` の 1 行差分である。

**中心 philip が受け入れ一覧へ入れるべきは新版
`SHA256:O4FrUiuT3+JNwIDMduljzPXfS7minab+CkWfg4gDzIQ` である。旧版は無効である。**

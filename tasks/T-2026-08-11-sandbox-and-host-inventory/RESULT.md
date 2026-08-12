# RESULT — 隔離が作れない原因と、ホストごとの設定のばらつき

**task_id:** `T-2026-08-11-sandbox-and-host-inventory`  **kind:** `analysis`
**実行ホスト:** `lecun`  **分岐:** `feat/sandbox-and-host-inventory`  **status:** pass
**PR:** #91（`phase0` へ Draft で起票。**統合していない**）

**調査のみ。原因が分かっても直していない。** 機械可読の対は `result.yaml`。
到達できた 3 台（lecun / bengio / efros）で**同一の 39 行の手順書**を流した。
**測れなかったものは `UNKNOWN` とした。他ホストの値を推測で埋めていない。**

---

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md`（版 `d422b08`）の該当アンカーの**原文**。要約していない。

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### `inputs.sigma_policy`（省略）

`context/conventions.md#sigma` の既定値を継承した。原文。

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

本契約は数値の比較を行わないため**使っていない。使わなかったことを記録する。**

### `contract.conventions_rev`

実測して `d422b08`。`spec.yaml` の記載と一致したため置換していない（手順であり逸脱ではない）。

### L3 で実行されなかった検査

`make task-preflight` は **5 PASS / 0 WARN / 4 SKIP / 0 FAIL**。
**`SKIP` は合格ではない。** P2 `cuda_ext_loaded`（契約に未記載）、
P3 `deterministic_flags`（同）、P4 `prereg_committed`（`kind=analysis` のため対象外）、
P5 `frozen_source_hash`（同）。

---

## 2. 結論

### 問い 1 — 隔離が作れない原因は何か

**環境の側である。道具の在処でも権限ビットでもない。** 4 経路すべてが失敗した。

| 経路 | 結果 |
|---|---|
| `unshare --user true` | `Operation not permitted`、exit 1 |
| `unshare --user --map-root-user true` | 同、exit 1 |
| `unshare --mount true` | 同、exit 1 |
| python の libc 直接呼び出し（`CLONE_NEWUSER` / `CLONE_NEWNS`） | 両方 `EPERM` |
| homebrew の `bwrap`（0.11.2、権限 555） | exit 1 |
| 第二の実装系に**同梱**の `bwrap`（権限 775） | exit 1 |
| 系の標準の `bwrap`（`/usr/bin` `/usr/local/bin`） | **実体が存在しない**（測れない） |

**許可の側は満たされている。**

    kernel.unprivileged_userns_clone = 1
    user.max_user_namespaces = 255595

**制限の層（4 指標すべてが容器の中を示す）。**

| 指標 | 実測 |
|---|---|
| `/proc/1/cgroup` | `0::/` |
| `/proc/self/uid_map` | `0 0 4294967295`（恒等写像 = 初期名前空間） |
| 容器の目印 | `/.dockerenv` **実在**、`/run/.containerenv` 不在 |
| `systemd-detect-virt` | **`docker`**、exit 0 |

**残る候補は 2 つある。どちらかは切り分けられない。**

| 候補 | 実測 |
|---|---|
| Seccomp | **`Seccomp: 2`**（filter モード）、`Seccomp_filters: 1` |
| AppArmor | **`docker-default (enforce)`**（自プロセスと init の両方） |

補助的に `CapEff: 0000000000000000`（実効権限が皆無）、`NoNewPrivs: 0`。

**切り分けの手段が無い。** `strace` は不在、`dmesg` は
`read kernel buffer failed: Operation not permitted` で読めず、`ausearch` と `auditctl` も不在。
`/proc/sys/kernel/unprivileged_userns_apparmor_policy` は**実在するが root 専用で読めない**。
フィルタを外して比べるのは**設定の変更（禁止 1）にあたる**ため行わない。
**したがって「Seccomp か AppArmor のいずれか、または両方」までが本契約の結論である。**

### 問い 2 — 第一の実装系はなぜ動くのか

**隔離を使っていないからである。** 推測ではなく実測で確かめた。

| measurement | 実測 |
|---|---|
| 設定の `sandbox` の語 | `~/.claude/settings.json` **0 件** / `.claude/settings.local.json` **0 件** / `.claude/settings.json` **0 件** |
| 親プロセスの系列 | `zsh -c` ← `claude -c` ← `-zsh` ← `zmx a m2fusion`。**`bwrap` を経由しない** |
| 利用者名前空間の inode | `4026531837` = **初期名前空間の既知の値**。入れ子の**外**にいる |

第二の実装系は隔離を必須にしており、その実装は `bwrap` を使う。
原路は `linux-sandbox/src/bwrap.rs`、`linux-sandbox/src/bundled_bwrap.rs`、
`sandboxing/src/bwrap.rs`、`sandboxing/src/landlock.rs`。
文字列の出現は `bubblewrap` 49 / `landlock` 38 / `bwrap` 21 / `seccomp` 16 / `sandbox_mode` 34。
**`landlock` の経路も持つが、どの条件で選ぶかは文字列からは読めない（UNKNOWN）。**

### 問い 3 — 設定はどれだけばらついているか

**版はばらついていない。ばらついているのは node の既定版と導入の時刻である。**

---

## 3. G3 の 3 つの表

### 表 1 — ホストごとの実装系の版

| ホスト | `codex --version`（PATH 経由） | `package.json`（実体を直読） | 導入の時刻 | 既定 node | 実際の node |
|---|---|---|---|---|---|
| lecun | `codex-cli 0.147.0` | **0.147.0** | 2026-08-07 23:18 | 20 | `v20.20.2` |
| bengio | **不在**（PATH に無い） | **0.147.0** | 2026-08-08 03:40 | 20 | `v12.22.9` |
| efros | **不在**（PATH に無い） | **0.147.0** | 2026-08-11 16:11 | 20 | **不在** |
| 他 8 台 | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |

**到達できた 3 台はすべて同一版である。** PATH 経由で「不在」に見えたのは
**非対話ログインで nvm が初期化されず PATH に入らないため**である
（ssh 経由の bengio の PATH に `nvm` は **0 件**、対話の lecun は 1 件）。
**測り方で結論が逆になった。**

導入の時刻が最大 **4 日**ずれているため、**一斉更新の仕組みは無い**と読める。
更新の経路の候補は 2 つ。`docs/host_dev_env_setup.md:245-249` の
`npm install -g @openai/codex`（文書の例は `0.133.0`）と、
`~/.codex/config.toml` の `check_for_update_on_startup`（値は記録しない）。

### 表 2 — ホストごとの頁送りの設定と道具の有無

| ホスト | `core.pager` | `git config --get` の exit | `~/.gitconfig` | `less` |
|---|---|---|---|---|
| lecun | **`cat`** | 0（設定あり） | 74 バイト（2026-07-29） | **不在** |
| bengio | 未設定 | 1（設定なし） | 279 バイト（2026-06-20） | **不在** |
| efros | 未設定 | 1（設定なし） | 54 バイト（2026-07-01） | **不在** |
| 他 8 台 | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` |

**設定の有無と道具の有無は別である。** 設定だけを見ると 2 台が危険に見えるが、
**`less` が 3 台すべてで不在**であるため、未設定のホストでも git は頁送りへ流せない。

### 表 3 — 共有領域の配布の経路

| 項目 | 実測 |
|---|---|
| 配布の主体 | **syncthing**（`/proc` から 2 プロセス。pid 1079 監視親 → 1395414 実働子） |
| 設定 | `folder id=claude-sync path=/home/ubuntu/claude-sync type=sendreceive 共有相手 11 台` |
| 目印 | `~/claude-sync/.stfolder/syncthing-folder-e1f429.txt` |
| 他の候補 | `rsync` **0 件** / `unison` **0 件**（`/proc` 方式） |
| 版管理か | **いいえ**（`.git` 不在、`git rev-parse` が失敗） |
| 設定の参照方法 | **共有領域を指す symlink**。`~/.codex` 6 件 / `~/.claude` 5 件 / `~/.agents` 自体が 1 件 = **12 件** |
| 張る手順 | `docs/host_dev_env_setup.md:578-587` に文書化 |
| 3 台の構造 | **同一**（`config.toml` `skills` `settings.json` `CLOUD.md` の 4 件を確認） |

**経路は特定できた。ただし実際の張り方は文書と食い違う箇所がある。**

| 文書の記述 | 実測 |
|---|---|
| `~/.claude/CLAUDE.md` → `~/.agents/AGENTS.md` | → **`claude-sync/CLAUDE.md`** を直接指す |
| `~/.codex/skills/my_skills` → `~/.agents/skills` | → **`skills.bak/my_skills`** にある |
| `~/.claude/skills` → `~/.agents/skills` | 一致 |
| `~/.codex/AGENTS.md` → `~/.agents/AGENTS.md` | 一致 |

**`~/.agents` 自体が `claude-sync/agents` への symlink である**（配下 955 ファイル)。

**共有領域の内容は分岐している。** 同期が止まっているためである。

| 共有領域のファイル | lecun | bengio | efros |
|---|---|---|---|
| `claude-sync/codex/config.toml` | 901 バイト | 901 バイト | **1008 バイト** |
| `claude-sync/settings.json` | 14419 バイト | 14419 バイト | **14440 バイト** |
| ファイル総数 | 2532 | 2532 | 2532 |

**件数の一致は内容の一致を意味しない。** 要約値は比べていない（`UNKNOWN`）。

### 到達できたホストと到達できなかったホスト

| 分類 | 台数 | ホスト |
|---|---|---|
| 認証まで通る | **2** | bengio（`192.168.196.105`）、efros（`192.168.196.227`） |
| TCP は届くが認証できない | **7** | `.54` `.58` `.63` `.78` `.106` `.143` `.190`（鍵も設定の項目も無い） |
| 経路が無い | **1** | philip（`192.168.196.150`）。`No route to host` |

過去の記録の確認: **philip の到達不能は現在も正しい。** TCP の 50072 は 10 台中 **9 台が OPEN**。
`known_hosts` は測定の前後で md5 が `b7dd7291…` のまま**不変**である。

---

## 4. 完了判定 19 項目

| # | 判定 | 実測値 |
|---|---|---|
| 1 | 道具を介さず名前空間を測った | `user_ns_exit=1` / `map_root_exit=1` / `mount_ns_exit=1`。**3 種すべて失敗**。成功と失敗は分かれなかった |
| 2 | 道具の実体を調べた | homebrew `~/homebrew/bin/bwrap` → `Cellar/bubblewrap/0.11.2/bin/bwrap`、権限 **555**。**同梱の実体**を別に発見（権限 775）。系の標準の場所は**両方とも不在**と記録 |
| 3 | 隔離環境かを測った | **4 指標すべて記録**。`0::/` / 恒等写像 / `.dockerenv` 実在 / `docker`。1 指標で断定していない |
| 4 | 制限の候補を網羅的に探した | `sysctl -a` への grep **12 行**。**`find /proc/sys` で 10 件を別に取り、grep が拾わない `unprivileged_userns_apparmor_policy` を発見** |
| 5 | 切り分けを結論した | **環境の側**（4 経路すべて失敗）。ただし **Seccomp と AppArmor のどちらかは `UNKNOWN`**。何が分かれば言えるかを記載 |
| 6 | 第一の実装系との違いを測った | 設定の `sandbox` の語 **0 件**、親の系列に `bwrap` 無し、利用者名前空間は初期のもの。**隔離を使っていない**。`landlock` の選択条件は `UNKNOWN` |
| 7 | ホストの一覧が正しい | repo 側 **401 行 / 5 名**、`~/.ssh/config` **4 件**、syncthing **11 台**。**差の理由 = repo 側は名前を決め打ちしており bengio を含む 6 台が漏れる** |
| 8 | 到達可否を測った | TCP **9/10 OPEN**、認証 **2 台**。**philip の到達不能は現在も正しい**ことを確認 |
| 9 | 到達できた各ホストで同じ測定 | **同一の 39 行の手順書**を 3 台で実行。測り方を変えていない |
| 10 | 版の一覧が出る | 表 1。**3 台すべて 0.147.0**。他 8 台は `UNKNOWN`（空欄にしていない） |
| 11 | 頁送りの一覧が出る | 表 2。**設定の有無と道具の有無を別々に記録**。`less` は 3 台すべて不在 |
| 12 | 配布の経路を調べた | 表 3。**syncthing と特定**。`/proc` から動いているものを確かめ、`rsync`/`unison` が 0 件であることも測った。目印だけで断定していない |
| 13 | **何も変更していない** | 作業ツリーの差分は**記録と生成物のみ**（本契約のディレクトリ / 受け皿 / 投影 3 件と集約結果 1 件）。生成物は `forbidden-check` が **excluded 4** として除外し violations 0。設定 3 件の時刻はすべて開始（15:28）より前。**ただし bengio の `/tmp` に 1 ファイルを書いた（逸脱に記載）** |
| 14 | 契約検証が通る | `make task-validate` **exit 0** |
| 15 | 実行直前の検査が通る | `make task-preflight` **exit 0**。SKIP 4 件の一覧を第 1 節に記載 |
| 16 | 静的検査が通る | `make spec-check` **exit 0**（8 規則すべてに該当なし） |
| 17 | 試験が不変 | 開始前 **5 failed / 423 passed** を先に測った。終了後 **5 failed / 423 passed**。内訳も同一 |
| 18 | 禁止領域が無変更 | `make forbidden-check` **exit 0**、violations 0、生成物の除外件数も出力 |
| 19 | 抑止を解除した | 後述（Step 7 の実測） |

### 作業ツリーの差分の全件（判定 13 の内訳）

     M context/auto/followups.md          <- 生成物（make taskindex）
     M context/auto/results_recent.md     <- 生成物（make taskindex）
     M context/auto/tasks_summary.csv     <- 生成物（make taskindex）
     M tasks/inbox.md                     <- 生成物（make inbox）
    ?? tasks/T-2026-08-11-sandbox-and-host-inventory/
    ?? tasks/inbox.d/T-2026-08-11-sandbox-and-host-inventory.md

**禁止 6 は「手で編集する」ことを禁じており生成は許している。**
`make forbidden-check` は生成物 4 件を除外して検査し violations 0 である。
**設定ファイルは 1 件も差分に現れていない。**

---

## 5. 起票者の誤り（5 件）

型と本文は `result.yaml` の `issuer_defects` にある。**本文は要約していない方を読むこと。**

1. **`asserted_without_measuring`** — 「強制アクセス制御｜該当する項目が**存在しない**」と
   断定するが、**AppArmor は `docker-default (enforce)` で動いている**（3 台すべて、
   自プロセスと init の両方）。`/sys/kernel/security/apparmor` は容器内で securityfs が
   未マウントのため不在であり、そこを見て「無い」と結論したと読める。
   `/proc/self/attr/current` を読めば分かる。**指示どおりだと原因の候補から AppArmor が落ちる。**

2. **`asserted_without_measuring`** — 「**3 台で 3 つの版**（0.144 / 0.146 / 0.147）」と
   断定するが、到達できた 3 台の `package.json` を直読すると**すべて 0.147.0** である。
   `codex --version` が失敗するのは**版の違いではなく非対話ログインで nvm が初期化されない
   ため**である。**指示どおりだと存在しないばらつきを直そうとする。**

3. **`check_does_not_check`** — Task 3 Step 1 の repo 側の探し方が名前を **5 個に決め打ち**
   している。正本の device は 11 台で、**`bengio` を含む 6 台が漏れる**。
   bengio は `~/.ssh/config` に項目を持ち**認証が通る 2 台のうちの 1 台**であり、
   本契約で最も測定価値が高い。SPEC 自身が注意 5 と注意 7 を書きながら決め打ちしている。

4. **`shell_assumption`** — Task 1 Step 2 の `command -v -a bwrap` は bash の書式で、
   zsh では `(eval):3: command not found: -v` で落ちる。**SPEC 自身が「対話シェルは
   bash ではない」と警告している。** 指示どおりだと経路の順序を記録できない。

5. **`self_contradiction`** — Task 5 Step 2 が `ps -eo args | grep` を指示し
   「検索コマンド自身に一致する方法を使わない」と注意を添えるが、**同じ SPEC の
   「前契約で確定した環境の事実」の表が「`ps -eo args | grep -c` は自己一致する。
   `/proc/*/cmdline` を読み、自分と祖先を除いて数える」と明記している。**
   指示された方法が、同じ SPEC が確定したとする事実と矛盾する。

### 申し送りは効いた

注意 1（零件を別の探し方で確かめる）で **`sysctl` が列挙しない項目**を見つけた。
注意 2（実装を読んでから信じる）で**同梱の bwrap** を見つけ、起票者の「道具の在処」の
前提を検証できた。注意 7（**同じ探し方の変種を並べない**）は前契約の誤りを踏まえた追加で、
本契約では repo 側の grep と syncthing の device 一覧という**異質な出所**を突き合わせたことで
決め打ちの漏れに気付けた。「前契約で確定した環境の事実」の表は、`ps` の自己一致と
`ss` の不在の切り分けを繰り返さずに済ませた。

---

## 6. 逸脱（12 件）

`result.yaml` の `deviations` に全件。**空にしていない。**
**自分が犯した誤りも隠さず書いた。**

### 禁止事項に触れたもの（1 件）

**bengio の `/tmp/sp.txt`（92 バイト、2 行）に書き込んだ。禁止 3 に触れる。**
手順書から遠隔への書き込みを除く `sed` が置換文字列のスラッシュで失敗し、さらに
**検証の grep が `2>` を含む行を除外していたため「書き込みは無い」と表示された。**
探している行そのものを除外する空振りの検査だった。
消すこと自体がさらなる書き込みになるため報告に留めた。**設定の変更ではない。**
以後の手順書は python で確実に置換し、全行を目で確かめた。

### 自分が犯した測定の誤り（4 件、いずれも自分で見つけて直した）

| 誤り | どう気付いたか | 直した結果 |
|---|---|---|
| 変数名に `path` を使い **zsh の特殊変数**を壊した | `awk`/`stat`/`readlink` が `command not found` になった | 陽性対照で挙動を確認し変数名を変えた。PATH は次の命令で健全 |
| `/proc/1/ns/*` が**読めない**のに比較し全 7 項目「異なる」と表示 | 全項目が同じ結果になるのが不自然 | 両側が取れたかを先に確かめる形へ直し「比較できない」と表示 |
| `find ~/.agents -type f` が **0** を返した | `~/.agents` が symlink であることに気付いた | `-L` で **955 件**。**前契約の起票者の誤りと同じ型を踏んだ** |
| `echo "...$?"` を 1 行にまとめ終了コードの取得を壊した | `pager_exit=0` が未設定のホストでも 0 だった | 2 命令へ戻し設定の有無を exit 0/1 で区別 |

### 測り方を足したもの（7 件）

python の libc 直接呼び出し（4 経路目）、同梱の bwrap での測定、`whence -a`（`command -v -a`
の代替）と重複の畳み込み、`/proc/self/attr/current` からの AppArmor の読み取り、
`package.json` からの版の直読、3 台共通の手順書、内容の分岐の発見。

---

## 7. 未解決（7 件）

`result.yaml` の `unknowns` に全件。要点は 3 つである。

**Seccomp と AppArmor の切り分けができない。** `strace` 不在、`dmesg` 読めない、
監査の道具も不在、`unprivileged_userns_apparmor_policy` は root 専用。
フィルタを外す比較は禁止 1 にあたる。**切り分けには読み取り権限か別の起動設定が要る。**

**到達できない 8 台は一切測れない。** philip は経路が無く、残る 7 台は TCP は届くが
鍵も設定の項目も無い。名前空間・版・頁送り・共有領域のいずれも `UNKNOWN` である。
**「他も同じはず」とは書かない。**

**起票者が観測した 0.144 と 0.146 の出所が分からない。** 到達できた 3 台はすべて
0.147.0 である。別のホストか別の時点の観測と考えられるが確かめる手段が無い。

---

## 8. 禁止事項の遵守

| # | 禁止 | 遵守 |
|---|---|---|
| 1 | **設定を変更する。一時的な変更も行わない** | 行っていない。作業ツリーの差分は本契約のディレクトリのみ、設定 3 件の時刻は開始より前 |
| 2 | 権限を昇格する | 行っていない。`sudo` の実在と `/etc/sudoers` の権限を読むだけに留めた |
| 3 | 他ホストの状態を変更する | **触れた。** bengio の `/tmp/sp.txt` に 92 バイトを書いた（逸脱に記載）。それ以外は読み取りのみ |
| 4 | `~/claude-sync/**` を変更する | 読み取りのみ |
| 5 | 実装系や道具を導入・更新・削除する | 行っていない |
| 6 | `runindex/**` `context/auto/**` を手で編集する | 触っていない（`forbidden-check` が exit 0） |
| 7 | `experiments/**` `transfer/**` `data/splits/**` の変更・削除 | 触っていない。**本契約はデータを参照していない** |
| 8 | `context/conventions.md` を変更する | 読み取りのみ |
| 9 | 学習・評価コードを変更する | 行っていない |
| 10 | 資格情報の値を出力・記録する | 出していない。鍵の名のみ（`check_for_update_on_startup` など） |
| 11 | `make task-report` 以外の経路での外部送信 | 他の経路は使っていない |
| 12 | 配布台帳の他の行を変更・削除する | 触っていない |
| 13 | 演算装置を使う | 使っていない |
| 14 | 未測定の値を書く | `UNKNOWN` として明示（7 件） |
| 15 | 統合する。自動統合を有効化する | 行っていない。抑止の目印を置いた状態で作業した |

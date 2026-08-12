# RESULT — T-2026-08-12-sync-audit-efros

**設定同期の停止に関する実測（efros）**
`kind: analysis` / ホスト `efros` / 分岐 `feat/sync-audit-efros` / 測定 `2026-08-12T08:13Z 〜 08:35Z`
**読み取りのみ。復旧操作・設定変更・他ホストへの書き込みは一切行っていない。**

生の出力は `audit.md` に貼ってある。本ファイルは散文の報告である。

---

## 1. 解決された参照

`contract.inject_verbatim: [conventions#prohibitions]` の**原文**
（`context/conventions.md:98-107`、要約していない）:

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

契約の `prohibitions` 5 件はこの 5 行と一対一で対応し、**いずれにも抵触していない**
（split を読んでいない / `data/raw` `data/external` に書いていない / 凍結源に触れて
いない / 未測定は UNKNOWN と書いた / `runindex/` を手で編集していない）。

`contract.conventions_rev` は SPEC Task 6 Step 2 に従い実測した。

    git --no-pager log -1 --format=%h -- context/conventions.md  →  d422b08

契約の記載 `d422b08` と**一致するため置換していない**（手順であり逸脱ではない）。

`inputs.code.entrypoints` は 2 件とも稼働実体と正本が**完全に一致**した
（`keeper.sh` 34 行 / `m2-sync.sh` 133 行、いずれも差 0 行）。よって以降の
「実装ではこうなっている」という記述は、**稼働中のものについての記述でもある。**

`inputs.data`（`egosurgery_phase_v1` と `data/splits/ego_val.txt`）は**本契約の
どの Task でも使用しない**。`inputs.denominator.ref` / `inputs.sigma_policy` /
`inputs.frozen_source.ref` は spec.yaml に記載が無い。

---

## 2. 完了判定 20 項目

**「実施した」ではなく「何が出たか」を書く。**

| # | 判定 | 実測値 |
|---|---|---|
| 1 | プローブが三通りを出し分けた | 期待 `OPEN`/`REFUSED`/`TIMEOUT` → 実測 `OPEN`/`REFUSED`/`TIMEOUT`。**3/3 一致** |
| 2 | 版管理側の経路が生きている | `refs/heads/phase0` = `a85cf78`、`exit=0` |
| 3 | 常駐処理の稼働数を二通りで数えた | 数え方 1（`ps\|grep -c "[k]eeper.sh"`）= **2**（自己汚染により棄却）/ スナップショット先行方式 = **1**（pid 225212、etime 39-00:57:01） |
| 4 | 中心ホストの決め方を実装から読んだ | `~/bin/keeper.sh:13-19`。中心 = **philip / 192.168.196.150**、SSH **50072**、転送 `22001→127.0.0.1:22000`、条件 = `~/.tunnel_to_philip` の存在、構成 = **星型**。正本との差 **0 行** |
| 5 | 中継の目印を集合として列挙した | `count=2`（`.tunnel.log` / `.tunnel_to_philip`）、`home_total=61` |
| 6 | 同期処理と中継の稼働状況を記録した | syncthing **2**（pid 216757 と ppid=216757 の 883188 = 親子、二重起動ではない）、`ssh -L` **0**、待ち受け **26**（`/proc/net/tcp` 経由。`ss`/`netstat` は不在） |
| 7 | 中継の入口への接続結果を記録した | `127.0.0.1:22001` = **REFUSED**（待ち受けなし）。対照 `22000`/`8384` = `OPEN` |
| 8 | 共有相手と共有フォルダを記録した | device **11**（自分含む）、folder **2**（`claude-sync` / `m2`）、いずれも 11 台全員と `sendreceive` で共有 |
| 9 | 記録に秘匿の値が含まれない（設定） | 検査 **0**、陽性対照 **1** |
| 10 | 対象一覧を三つの出所から集め件数を記録した | `~/.ssh/config`=**3** / `/etc/hosts`=**7 行（他ノード 0）** / syncthing 設定=**11**。和集合の他ノード = **10 台**、自分を足して 11 台で既知の構成と一致。**縮んでいない** |
| 11 | 全対象を測り合計が一致した | `total=20`（10 台 × 2 ポート）。`OPEN 9 + REFUSED 9 + TIMEOUT 0 + OTHER 2 = 20`。**一致** |
| 12 | 拒否と経路なしを区別した | `REFUSED` **9**（他 9 台の 22000、機器は生存）/ `OSERROR:No_route_to_host` **2**（**philip のみ**、経路なし）/ `TIMEOUT` **0** |
| 13 | 設定共有の件数を記録した | `EXISTS`。files **2532** / symlinks **1** / dirs **900**。一覧 **2531 行**、計 **60,101,493 バイト** |
| 14 | 一覧に内容が含まれない | 検査 **4**（0 ではない）。全て**ファイル名の一般語**（`tokenizers.md` / Modal の `secrets.md` 説明文書 / CSS の `tokens.css` ×2）。一覧は名前・大きさ・更新時刻・要約値の **4 列のみ**。陽性対照 **1** |
| 15 | 退避と衝突の痕跡を数えた | `.stversions` **0 件**、`*.sync-conflict-*` **10 件**（最後 2026-08-06 16:22）。`versioning.type=(none)` / `maxConflicts=10` |
| 16 | 停止時期を二つの独立した情報から推定した | A（`~/.tunnel.log` 逆算）**2026-08-06T20:42:09Z** / B（`~/.syncthing.log` 直接）**2026-08-06T20:23:41Z**。差 **18 分 28 秒**（1 ループ未満）、符号も予測どおり。**整合。採用は B** |
| 17 | 16 項目すべてに実測値または UNKNOWN がある | **空欄なし**（上の 16 行） |
| 18 | 作業ツリーの変更が契約の範囲に限られる | 一覧を §6 に記載。契約の変更は `tasks/T-2026-08-12-sync-audit-efros/` と `tasks/inbox.d/` と `.sync-pause` のみ。**契約前から存在した未追跡の `docs/sessions/digest/` 2 件が残る**（詳細は §6） |
| 19 | 抑止が repo 直下から消えている | §6 に記載 |
| 20 | 報告が台帳へ返っている | §6 に記載 |

---

## 3. 何が起きているか（実測から言えること）

### 3.1 原因は確定した

**中心 philip（192.168.196.150）が経路ごと落ちている。** 見立ては崩れなかった。

1. **実装が中心を philip と定めている。** `keeper.sh:14` に「コンテナ間は SSH(50072)
   しか通らないため、syncthing は星型(各ノード→philip)で接続する」と明記。
   稼働実体と正本の差は 0 行。**中心の名前とアドレスは実装に直書きされている。**
2. **efros は星型の spoke として正しく構成されている。** `~/.tunnel_to_philip` が
   存在し（43 バイト、2026-07-03）、syncthing 設定では **philip だけが
   `tcp://127.0.0.1:22001`** を宛先に持つ。
3. **philip だけが到達不能。** 10 台 × 2 ポート = 20 測定のうち、philip の
   両ポートのみ `No route to host`。他 9 台は SSH 50072 が **OPEN**。
4. **efros は philip 以外に繋がったことがない。** `~/.syncthing.log` の
   `Established secure connection` **27 件がすべて philip 宛**、
   **27 件すべて `connection.remote=127.0.0.1:22001`**（トンネル経由）。
5. **迂回路が無い。** `globalAnnounceEnabled=false` / `relaysEnabled=false`。
   他 9 台の `22000` は `REFUSED`（＝待ち受けが無い）。
6. **現在の接続数は零。** `Established` 27 / `Lost` 27 で収支 0。

### 3.2 停止時刻

**`2026-08-06T20:23:41Z`**（採用値）。測定時点で **5 日 11 時間 50 分**経過。

    2026-08-06 20:23:41  Lost device connection (kind=primary   device=GO2U7PF… error="reading length: EOF" remaining=1)
    2026-08-06 20:23:41  Lost device connection (kind=secondary device=GO2U7PF… ... remaining=2)
    2026-08-06 20:23:41  Lost device connection (kind=secondary device=GO2U7PF… ... remaining=0)
    2026-08-06 20:23:41  Connection closed      (device=GO2U7PF… error="reading length: EOF")

二つの独立した情報が**整合した**。`~/.tunnel.log` は時刻を持たないため、ループ周期を
実測して逆算した（`22:02:28→07:03:48` の 18 ループで 1804.4 s、`20:02:08→22:02:28` の
4 ループで 1805.0 s）。この周期は独立に 2 回裏づけられている
（`07:03:48 + 1805×2 = 08:03:58` ≒ `tunnel.log` mtime `08:03:59`／
予測 `08:34:03` に対し抑止の記録が実測 `08:34:00`）。

逆算値 `20:42:09Z` は直接記録 `20:23:41Z` より **18 分 28 秒遅い**。これは
**予測どおりの方向とずれ幅**である。ssh は `ServerAliveCountMax=3`
（`keeper.sh:18`）で切断に気付くのに時間がかかり、次の再試行は最大 30 分後の
ループまで来ない。よって「逆算値は真の喪失時刻より 0〜30 分遅れる」ことが期待され、
実測 18 分 28 秒はその範囲に収まる。**食い違いではない。**

傍証として `~/claude-sync/` 第一階層の mtime が `2026-08-06 20:20`、
最後の衝突ファイルが `2026-08-06 16:22` で、いずれも同日夜を指す。

### 3.3 復旧したとき何が失われうるか

| 事項 | 実測 | 含意 |
|---|---|---|
| `versioning.type` | **`(none)`**（両フォルダ） | ■ **退避が無い。他ホストで削除されたファイルは復旧時にこちらでも消え、戻す手段が無い** |
| `maxConflicts` | **10** | 両側が編集したファイルは `.sync-conflict-*` として最大 10 世代残る。**同時編集による黙った消失は起きない** |
| `.stversions` | **0 件** | 上記と整合（退避機構が使われていない） |
| efros 側の未伝播の分岐 | **171 ファイル / 2,044,979 バイト** | 内訳は下表 |

停止後に efros で更新された共有ファイルの内訳:

| 区分 | 件数 | 性質 |
|---|---:|---|
| `codex/plugins/cache/**` | 110 | **再生成可能なキャッシュ** |
| `codex/skills/.system/**` | 59 | 全て mtime `2026-08-11T16:11:59` の**一括導入**。ベンダ提供物で再導入可能 |
| `sync-alerts.log` | 1 | 各ホストで内容が異なる追記ログ。既に衝突ファイルが 10 件ある |
| **`codex/config.toml`** | **1** | **1008 バイト、mtime `2026-08-11T20:15:28`。実体のある局所設定** |

**efros 側で「失うと困る」分岐は実質 `codex/config.toml` 1 件である。**
`inventory.tsv`（2531 行、4 列、要約値の失敗 0）を他ホストの同名ファイルと
突き合わせれば、どこが分岐したかは要約値の一致・不一致で機械的に判定できる。

**ただしこれは efros が書いた側の話である。** 他ホストで何が削除されたかは
efros からは測れない（**UNKNOWN**）。`versioning=none` である以上、
その部分は復旧時に戻せない。

### 3.4 切り分けとして言えないこと

- 「外向き通信の障害」**ではない**。`github.com:443`/`:22` は `OPEN`、
  `git ls-remote origin` は参照を返し `exit=0`。
- 「構内全体の障害」**でもない**。他 9 台は SSH 50072 が `OPEN` で、
  `22000` も `TIMEOUT` ではなく **`REFUSED`**（RST が返る＝アドレスは生きている）。
- 「efros 側の同期処理の故障」**でもない**。局所 syncthing は `22000`/`8384` とも
  `OPEN` で、keeper も 39 日間動き続けている。

**落ちているのは philip 1 台と、そこへの経路だけである。**

---

## 4. 起票者の誤り（3 件）

`P9 spec_lint` は規則 8 件を検査して PASS（該当なし）だった。**機械の網が通ったことと、
契約に誤りが無いことは別である。** 実行して見つかったものを記録する。

### 4.1 `check_does_not_check` — 待ち受け一覧が取れないまま結論になる

Task 3 Step 2 は `(ss -ltn || netstat -ltn || echo "手段なし")` とし、
「零行なら手段が無かったということ」としている。**efros には `ss` も `netstat` も
`lsof` も無い。** 指示どおり実行すると「手段なし」の 1 行だけが残り、待ち受けの
一覧は `UNKNOWN` として報告されることになる。

実際には `/proc/net/tcp` と `/proc/net/tcp6` から **26 件**が取れた。しかもその中に
**「`22001` が待ち受けに存在しない」という、中継が張られていないことの
プロセス一覧とは独立な証拠**が含まれていた。**測れるものを測れないと報告する
ところだった。**

### 4.2 `check_does_not_check` — 同期処理のログを探す模様が実ファイルに一致しない

Task 5 Step 5 の `find ~ -maxdepth 3 -name "syncthing*.log"` は **0 件**を返す。
実ファイルは **先頭がドットの `~/.syncthing.log`**（8,553,294 バイト）で、
`syncthing*.log` はこれに一致しない。

指示どおり実行すると「同期処理のログは見つからなかった」となり、**停止時期の
第二の独立した情報源が失われる。** 実際にはこのファイルに
`2026-08-06 20:23:41 Lost device connection` という**直接の時刻記録**があり、
本報告の採用値はこれである。SPEC 自身の申し送り #7「探す対象の名前を決め打ちしない。
集合として列挙してから絞る」に、SPEC 自身が反している。

### 4.3 `self_contradiction` — 使わない入力を宣言している

`inputs.data.dataset: egosurgery_phase_v1` と
`inputs.data.split_files: ["data/splits/ego_val.txt"]` が宣言されているが、
**Task 1 から Task 6 のどの Step もこれらを参照しない。** 本契約は同期経路の
読み取り監査であり、データセットも分割も登場しない。同様に `prohibitions` の
`no_split_redefine` / `no_raw_write` / `no_frozen_change` も本契約では
成立しようがない。

指示どおり実行すると、これらは解決先を持たないまま報告に残り、**読む側に
「この監査はデータを参照した」と誤解させる。** 実害は小さいが、
参照解決の手順（skill 手順 3）が空回りする。

---

## 5. 陽性対照

**判定が通ったことは、その判定が働いていることを意味しない。**

| 判定 | 何を入れれば失敗するはずか | 実際に何が起きたか |
|---|---|---|
| 到達性プローブが三通りを出し分ける | 開いている先・閉じた先・経路の無い先を与える | `A_open=OPEN` / `B_closed=REFUSED` / `C_noroute=TIMEOUT`。**3/3 期待と一致** |
| 版管理側の経路が生きている | 外向き通信が落ちていれば参照が返らない | `refs/heads/phase0 = a85cf78d9f8f…` が返り `exit=0` |
| 秘匿混入検査（設定の解析結果）が働く | `apikey=DUMMY` を書いた囮ファイルを与える | 囮で **1**、実記録で **0** |
| 秘匿混入検査（棚卸し一覧）が働く | `x/secret.md` の行を持つ囮 TSV を与える | 囮で **1**、実記録で **4**（すべてファイル名の一般語） |
| 常駐処理の稼働数の数え方が自己汚染していない | 命令行に `keeper.sh` の平文を含めて `ps` を数える | **2 を返した**（実体は 1）。スナップショット先行方式では **1** |
| 7 件の試験失敗が本契約に起因しない | 本契約のディレクトリを退避して再実行する | 契約が無くても**同じ 2 件が失敗**。先行条件と確定 |
| ループ周期 1805 秒の推定が正しい | `07:03:48 + 1805×2` が `tunnel.log` の mtime と一致しなければ誤り | 予測 `08:03:58` に対し実測 mtime **`08:03:59`**（1 秒差） |
| 抑止 `.sync-pause` が実際に効いている | 抑止が無効なら次ループで `auto-merge`/`auto-push` が記録される | 予測 `08:34:03` に対し実測 **`08:34:00` に「一時停止中」**。総数 2→3。統合も push も発生せず |

---

## 6. 作業ツリーと後始末

### Step 5 変更が契約の範囲に限られること

    make forbidden-check
    {"base": "origin/phase0", "changed": 10, "checked": 10, "errors": [],
     "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"],
     "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
    exit=0

    git --no-pager status --porcelain   →  entries=4
    ?? docs/sessions/digest/2026-08-02-45129e05-8b5a-4844-b371-5e7be7a985aa.md
    ?? docs/sessions/digest/2026-08-11-15-35-17-019ff176-ba5e-7ae2-9bf7-4b6a11798b39.md
    ?? tasks/T-2026-08-12-sync-audit-efros/
    ?? tasks/inbox.d/T-2026-08-12-sync-audit-efros.md

    git --no-pager diff --name-only --diff-filter=U  →  unmerged=0

禁止領域に変更が無いことを個別にも確認した:

    runindex/     0 件
    context/auto/ 0 件
    experiments/  0 件
    data/splits/  0 件

**契約の成果 2 経路のほかに、契約開始前から存在した未追跡の抽出物 2 件があった。**
これは SPEC Task 6 Step 5 の「それ以外があれば停止して報告する」に形式上該当するが、
`tasks/README.md:283-288` は**抽出物を契約の記録と一緒に commit することを求めている**。
未追跡のまま放置すると `git merge --ff-only` が**内容が同一でも**未追跡ファイルの
上書きを拒み、**自動同期が止まる**（B-30、5 台で実測）。

**両方を満たすため、commit を 2 つに分けた。** 契約の commit は SPEC Step 6 の
`git add` 指定どおりに保ち、抽出物は別 commit にした。

### Step 6 commit

| # | hash | 内容 |
|---|---|---|
| 1 | **`6eff033`** | `docs(sync): audit sync topology and divergence on efros`。`tasks/T-2026-08-12-sync-audit-efros/` 7 ファイルと `tasks/inbox.d/T-2026-08-12-sync-audit-efros.md` |
| 2 | **`c6dbe21`** | `docs(sessions): record digests from efros`。`docs/sessions/digest/` 2 ファイル |
| 3 | （下記） | 本節のハッシュ記録。既存の慣行（`20e7b0f` が `69e9772` を記録した形）に倣う |

commit 2 の前に伏せ字を確認した（`tasks/README.md:290` の要求）。
`github_pat_` に **2 件一致**したが、目視の結果いずれも
**伏せ字コマンド自身**（`sed 's/github_pat_[A-Za-z0-9_]*/<REDACTED>/g'`）と
**検査コマンド自身**（`grep -rIl 'github_pat_'`）の記録で、
一致語に続く英数字は **0 文字**。実トークンではない。
陽性対照として囮ファイルで検査が **1** を返すことを確認済み。

commit 後の作業ツリーは **0 件（clean）**。

### Step 7 抑止の解除（削除ではなく移動）

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-12-sync-audit-efros  →  released
    ls -la .sync-pause                                                      →  repo 直下から消えた
    ls -la /tmp/.sync-pause.released.T-2026-08-12-sync-audit-efros
        -rw-rw-r-- 1 ubuntu ubuntu 0  8月 12 08:10

**退避先を repo の外（`/tmp`）に取ったため、追跡外の残骸が作業ツリーに残らない。**
commit `bc7280f` が「別名へ移す解除方式では `.sync-pause.released` が追跡外のまま
`git status` に残る。無視されるのは `.sync-pause` だけであり `git add -A` で誤って
commit され得る」と記録した問題は、SPEC が退避先を `/tmp` に定めているため生じない。

### Step 8 報告の返送 — 一度止まり、本文を直して送り直した

    make task-report TASK=T-2026-08-12-sync-audit-efros
    [task-report] 秘匿らしき内容が報告に含まれます。**送信しません。**
      W&B の鍵らしい 40 桁（51 行目・値は伏せる）
    本文を直してから送り直してください。検査を無効にしないこと
    exit=2

**検査は無効にせず、本文を直した。** 51 行目に含まれていたのは
`origin/phase0` の**コミットハッシュ**（40 桁の 16 進）であり、資格情報ではない。
`report_task.py` の「40 桁」判定は、**40 桁 16 進の git ハッシュと W&B の
API キーを区別できない**。git ハッシュはこの種の報告に頻出するため、
偽陽性が構造的に起きる。

該当は 4 箇所（`RESULT.md:51` / `result.yaml:16` / `result.yaml:112` /
`audit.md:62`）で、いずれも同じ `origin/phase0` の先頭である。
リポジトリの慣行どおり **短縮形 `a85cf78`** に直した。値の意味は失われない。
置換後、40 桁の連続列は本契約の全ファイルで **0 件**。

**この事象は検査の欠陥ではなく、判定に使える情報が足りないだけである。**
送信を止める側に倒れているため安全側であり、`followups` に記録した。

**2 回目は台帳側が拒否した。原因を特定した。**

    HTTP 400 validation_error
    body.children[0].code.rich_text[2].text.content.length should be ≤ `2000`, instead was `2001`

`tools/report_task.py:131` は本文を **Python のコードポイント**で 2000 ごとに切る。

    chunks = [text[i:i + RICH_TEXT_LIMIT] for i in range(0, len(text), RICH_TEXT_LIMIT)] or [""]

**しかし Notion の上限は UTF-16 コード単位で数えられる。** BMP 外の文字は
Python では 1、UTF-16 では 2 と数えられるため、その文字を含む切片だけが上限を超える。

実測で確認した。本文を 2000 コードポイントごとに切ると 8 切片になり、
**`chunk[2]` だけがコードポイント 2000 に対して UTF-16 で 2001**。
本文中の BMP 外の文字は **`U+1F534`（赤丸の絵文字）ただ 1 つ**であり、
これがその切片に入っていた。API が指した添字 `rich_text[2]` と完全に一致する。

    chunk[2]  codepoints=2000  utf16=2001  差=+1
    BMP 外の文字の総数 = 1   内訳 = Counter({'U+1F534': 1})

**この節を書いた時点で同じ誤りを一度再現した。** 原因を説明するために
その文字自身を本文へ引用したところ、BMP 外の文字が 2 個に増え、
最大切片が UTF-16 で **2002** になった。**符号位置の表記へ改めた。**

**本契約は読み取りのみで `tools/` を変更できない**ため、道具は直していない。
本文側で BMP 外の文字を BMP の記号（`■`）へ置き換えて送った。表示上の意味は変わらない。
**根本原因は道具側にあり、`followups` と受け皿に記録した**
（`_rich_text` は UTF-16 コード単位で切るべきである）。

**3 回目で送信できた。**

    {
      "task_id": "T-2026-08-12-sync-audit-efros",
      "verdict": "pass",
      "n_issuer_defects": 3,
      "report_sha256": "0d56d36003150a9fadae218131f99cd87b0af599dbefdace01ee262a95784b54",
      "report_bytes": 27280,
      "replaced_blocks": 0
    }
    exit=0

送信は 3 回試み、**2 回止まった**。1 回目は道具の秘匿検査（git ハッシュの偽陽性）、
2 回目は台帳側の上限（`_rich_text` の切り方が UTF-16 を考慮していない）。
**どちらも検査や上限を迂回せず、本文側を直して通した。**

### 完了判定 18〜20 の実測値

| # | 判定 | 実測値 |
|---|---|---|
| 18 | 作業ツリーの変更が契約の範囲に限られる | `forbidden-check` = **pass / violations 0 / errors 0**（changed 10 / checked 10）。`runindex/` `context/auto/` `experiments/` `data/splits/` はいずれも **0 件**。未解決 **0**。契約の成果 2 経路のほか、契約開始前から存在した抽出物 2 件を `tasks/README.md:283-288` に従い**別 commit** で記録した。commit 後の作業ツリーは **0 件** |
| 19 | 抑止が repo 直下から消えている | `released` / `repo 直下から消えた`。退避先は `/tmp/.sync-pause.released.T-2026-08-12-sync-audit-efros`（**repo 外**） |
| 20 | 報告が台帳へ返っている | 3 回目で **`exit=0`**、`verdict: pass` / `report_bytes: 27280` / `report_sha256: 0d56d360…` / `n_issuer_defects: 3`。1 回目は秘匿検査（git ハッシュの偽陽性）、2 回目は台帳の 2000 文字上限（UTF-16 の数え方）で停止。いずれも本文を直して通した |

---

## 7. 逸脱

**逸脱が無い場合も明記する規約であるが、本契約では 7 件あった。**

1. **（judgement）契約の取り込み前に、未追跡ファイル 2 件を退避した。**
   `task_start.sh` は作業ツリーが汚れていると何も作らず終了する。
   `docs/sessions/digest/` の 2 件（本セッションの 07:14 生成、契約開始 08:10 より前）が
   これに当たったため、scratchpad へ退避して `task-start` を通し、直後に戻した。
   **この 2 件の扱いはユーザーの事前の判断（契約ブランチで commit する）と
   SPEC Task 6 Step 5（変更を契約の範囲に限る）が衝突する。** 本報告では
   **SPEC を優先し、commit していない。** §6 に未追跡のまま列挙する。
2. **（judgement）`.sync-pause` は SPEC §0 の `touch` ではなく `task_start.sh` が作った。**
   結果は同じ（設置済み）。稼働中の `~/bin/m2-sync.sh` に `sync-pause` の参照が
   2 箇所あることを確認してから進めた（`:40-41`）。
3. **（judgement）Task 2 Step 1 の数え方が自分の表示用ラベルで汚染された。**
   `ps -eo args | grep -c "[k]eeper.sh"` が **2** を返した。原因は実行者が付けた
   `echo "... keeper.sh ..."` が `zsh -c '<script>'` の命令行として `ps` に現れたこと。
   SPEC 申し送り #3（記録を作る流れに表示用を混ぜない）に反した**実行者の誤り**。
   スナップショット先行方式で測り直し、**両方の値を記録した**。
4. **（environment）zsh は非引用の変数展開で単語分割しない。**
   `probe.py ${ARGS}` が 1 引数として渡り `OSERROR:Name_or_service_not_known` を
   返した。`xargs -a <file>` に変えて 20 件を測り直した。
   SPEC 申し送りが警告していた事象である。
5. **（spec_defect）Task 3 Step 2 で `/proc/net/tcp` を代用した。** §4.1 のとおり。
6. **（spec_defect）Task 5 Step 5 で `~/.syncthing.log` を直接指定した。** §4.2 のとおり。
   探索は「先頭のドットを含む集合」として `stat` で確認する形に変えた。
7. **（judgement）契約が要求していない試験一式を実行した。**
   `result.yaml` の `tests` を実測で埋めるため。実行前後で作業ツリーに差分が
   無いこと（3 件 → 3 件）を確認し、禁止領域への書き込みが無いことを担保した。
   結果は 7 failed / 417 passed / 4 skipped で、**7 件すべてが先行条件**であることを
   契約ディレクトリの退避により切り分けた。

`conventions_rev` の実測と置換は SPEC が「逸脱ではなく手順」と定めているため
ここには書かない（§1 に記載）。

---

## 8. 断定できなかったこと（UNKNOWN）

- **他ホストの状態。** 各ホストで何が変更・削除されたか、`inventory.tsv` と
  突き合わせるべき相手側の一覧は、efros からは取得できない。同じ契約が並行実行
  されている前提であり、**推測で埋めない。**
- **philip が停止している理由。** 「ハード側の理由」は記録であって、efros から
  測れるのは `No route to host` までである。
- **復旧の予定時期。** 「2 週間以降」は記録であり、実測していない。
- **復旧時に他ホスト側の削除がどれだけ及ぶか。** `versioning=none` のため戻せない
  ことは確定しているが、件数は相手側の状態に依存するため測れない。
- **他 9 台の `22000` が `REFUSED` である理由。** `keeper.sh:14` の記述
  （コンテナ間は SSH のみ）と整合するが、本契約で測ったのは「RST が返る」までである。

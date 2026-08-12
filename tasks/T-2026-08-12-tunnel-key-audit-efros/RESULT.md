# RESULT — T-2026-08-12-tunnel-key-audit-efros

**中継に使う鍵の配布状況の実測（efros）**
`kind: analysis` / ホスト `efros` / 分岐 `feat/tunnel-key-audit-efros` / 測定 `2026-08-12T11:10Z 〜 11:35Z`
`depends_on: T-2026-08-12-sync-audit-efros`

**読み取りのみ。鍵の生成・配布・変更は行っていない。中心の移設も行っていない。**
**秘密鍵の中身はどこにも記録していない。指紋と経路名だけである。**

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

`contract.conventions_rev` は SPEC Task 4 Step 2 に従い実測した。

    git --no-pager log -1 --format=%h -- context/conventions.md  →  d422b08

契約の記載 `d422b08` と**一致するため置換していない**（手順であり逸脱ではない）。

`inputs.data`（`egosurgery_phase_v1` と `data/splits/ego_val.txt`）は
**本契約のどの Task でも参照しなかった。** SPEC 前提節がそう明記しており、
実際に参照していない。`no_split_redefine` `no_raw_write` `no_frozen_change` も
本契約では成立しようがなく、いずれにも抵触していない。
`no_estimated_values` は守った（測れないものは UNKNOWN と書いた）。
`no_runindex_hand_edit` も守った（`runindex/` の変更は 0 件）。

`inputs.code.entrypoints` のうち `scripts/sync/keeper.sh` は前契約で稼働実体と
正本の差が 0 行であることを確認済みで、本契約では `:13-19` の中継の記述を
鍵の経路の根拠として用いた。`scripts/sync/m2-sync.sh` は抑止の実効性の確認
（`grep -c sync-pause` が **2**）にのみ用いた。

---

## 2. 完了判定 12 項目

**「実施した」ではなく「何が出たか」を書く。**

| # | 判定 | 実測値 |
|---|---|---|
| 1 | 中継の目印を集合として列挙した | `count=2`（`.tunnel.log` / `.tunnel_to_philip`）。目印は **philip 宛の 1 つだけ**。指す経路は `/home/ubuntu/.ssh/id_ed25519_efrostophilip`（43 バイト） |
| 2 | 鍵の実在と指紋を測った | **実在する**（秘密鍵 399 バイト / 公開鍵 94 バイト、2026-07-03 23:36、権限 `-rw-------`）。**ED25519 256 bit**、指紋 `SHA256:vgkD0GqFco6G+2QwtT0MknwTursNSLNi5rsORrbNa8I`、注釈 `ubuntu@efros`。**中身は出力していない** |
| 3 | 手元の公開鍵を集合として列挙した | `pubkey_count=5`。`efrostophilip`(ED25519, `ubuntu@efros`) / `github`(ED25519, **`ubuntu@lecun`**) / `m2deploy`(ED25519, `m2-deploy-efros`) / `efrostolecun`(RSA3072, `ubuntu@efros`) / `efrostophilip`(RSA3072, `ubuntu@efros`)。**他ノードへ向かう鍵は philip 宛と lecun 宛の 2 つだけ** |
| 4 | 記録に鍵の値が含まれない | 検査 **2**。両方とも `sshd_config` の**オプション名**（`PermitRootLogin prohibit-password` 等）で値ではない。囮による陽性対照 **1**。base64 の形の一致 1 件は**検査模様を文章に書いた箇所**で、一致長 4 文字（実鍵は 68 文字以上） |
| 5 | 受け入れの一覧を集合として探した | `~/.ssh/authorized_keys` **3 行**（1234 バイト）。`authorized_keys2` は不在。`sshd_config` の `AuthorizedKeysFile` は**コメントアウトで既定値**のため別の場所は指していない |
| 6 | 登録されている指紋を列挙した | `count=3`。`dakyo-mba@dmba.local`(ED25519) / **`ubuntu@aolab`**(RSA) / **`ubuntu@lecun`**(RSA) |
| 7 | 中継の鍵が自ホストに登録されているかを照合した | **`0`**（登録されていない）。**陽性対照 `1`**（実在する別の指紋で照合が働く）。さらに**手元 5 鍵すべてが `0`** で、共有鍵方式ではない |
| 8 | 自ホストの住所を測った | **`172.17.0.21`**（`/proc/net/fib_trie` / `/etc/hosts` / `hostname -I` の三通りが一致）。**容器の内側の住所**で `192.168.196.x` の帯ではない。`ip` コマンドは不在。**外からどの住所で見えるかは UNKNOWN** |
| 9 | 対象一覧を三つの出所から集め件数を記録した | `~/.ssh/config`=**3** / `/etc/hosts`=**7 行（他ノード 0）** / syncthing 設定=**11**。**和集合の他ノード = 10 台**、自分を足して 11 台で既知の構成と一致 |
| 10 | 全対象で認証を測り合計が一致した | `total_lines=10`。`AUTH_OK 0 + DENIED 9 + NOCONN 1 = 10`。**一致** |
| 11 | 認証の可否と接続の可否を区別した | 認証成功 **0** / `Permission denied` **9**（口は開くが鍵が通らない）/ `No route to host` **1**（philip のみ）。**追加測定で、専用鍵を使えば lecun は `REACHABLE`** |
| 12 | 通らないはずの鍵で通らないことを確かめた | `-i /dev/null` で `Permission denied`、`REACHABLE` の件数 **0**。鍵の代理は接続不能（`ssh-add -l` が `Error connecting to agent`）で、`-i` が識別を決めていることも確認 |

---

## 3. 判断のための結論

### 3.1 鍵は対ごとに配られている（共有鍵ではない）

三つの独立した観察が一致する。

1. **命名**が宛先を含む（`efrostophilip` / `efrostolecun`）。
2. **手元 5 鍵すべて**が自ホストの `authorized_keys` に無い（`0` が 5 件）。
   全ノードが同じ鍵を持つ構成なら、自分の鍵が自分の受け入れ一覧にも入るはずである。
3. **中継の鍵は他 9 台のどこにも通らない**（`AUTH_OK=0`、`DENIED=9`）。
   共有鍵なら全台で通るはずである。

**中心を移すことは「設定の変更」では済まず、「鍵の配布」を伴う。**

### 3.2 efros は中心になれない（現状のままでは）

中心になるとは、**他の全ノードから SSH で入ってこられる**ことである。
efros が受け入れているのは **3 者だけ**である。

| 注釈 | 種別 | 素性 |
|---|---|---|
| `dakyo-mba@dmba.local` | ED25519 | 利用者の Mac |
| `ubuntu@aolab` | RSA | ノード `aolab` |
| `ubuntu@lecun` | RSA | ノード `lecun` |

**philip の鍵も、残る 6 台の鍵も登録されていない。**
efros を中心にするには **最低 8 台分の登録追加**が要る
（11 台 - 自分 - 既登録の aolab と lecun = 8）。

さらに **efros の住所は `172.17.0.21` で容器の内側**であり、
他ノードが居る `192.168.196.x` の帯に出ていない。
**efros の物理側に `50072` の転送があるかは自ホストからは測れない（UNKNOWN）。**
転送が無ければ、鍵を配っても他ノードから到達できない。

### 3.3 efros から出ていける先は lecun だけである

| 宛先 | 中継の鍵 | 専用鍵 | 判定 |
|---|---|---|---|
| philip (150) | `No route to host` | `No route to host` | **判定不能**（経路が無い） |
| lecun (176) | `Permission denied` | **`REACHABLE`** | **通る** |
| 他 8 台 | `Permission denied` | 専用鍵が**存在しない** | **通らない** |

**efros が新しい中心へ入っていけるのは lecun のみ。**
これは「efros から見た」一方向の事実である。**lecun を中心にできるかは、
他の 9 台からも lecun へ入れるかに依存し、それは efros からは測れない（UNKNOWN）。**

### 3.4 決定に直結する形にまとめる

| 問い | efros で測れた答え |
|---|---|
| 中継に使う鍵はどれか | `~/.ssh/id_ed25519_efrostophilip`（ED25519、指紋 `SHA256:vgkD0Gq...`） |
| 鍵は共有か対ごとか | **対ごと。** 三つの独立した観察が一致 |
| efros は中心になれるか | **現状では不可。** 受け入れは 3 者のみで 8 台分の登録追加が要る。加えて外部からの住所が UNKNOWN |
| efros はどこへ入れるか | **lecun のみ**（専用鍵で `REACHABLE`）。philip は経路が無く判定不能 |
| 中心の移設に鍵作業は要るか | **要る。** 口が開いていても鍵は通らない（9 台で `Permission denied`） |

---

## 4. 起票者の誤り（1 件）

`P9 spec_lint` は規則 8 件を検査して PASS（該当なし）だった。
前契約で 3 件を報告し、本 SPEC はその型を直していた
（`ss` の不在・先頭がドットのファイル・使わない入力の宣言は、いずれも
前提節に事実として書き込まれ、繰り返されていない）。**残った 1 件を記録する。**

### 4.1 `self_contradiction` — 禁止事項と測定命令が衝突する

禁止 #2 は「`~/.ssh/**` `~/bin/**` `~/claude-sync/**` を変更する（読むのは可）」を
禁じている。ところが Task 3 Step 2 の命令は
`-o StrictHostKeyChecking=accept-new` を含み、**新規ホストへ接続したときに
`~/.ssh/known_hosts` へ書き込む。**

efros は他 8 台へ接続したことがないため、**指示どおり実行すれば必ず書き込みが起きる。**
実際に起きることを測った。書き込み先を `/tmp` へ逃がして測定したところ、
その迂回先は **9 件から 17 件へ 8 件増えた**。接続が成立した 9 台のうち
lecun のみ既知で、残り 8 台分が新規に書かれた計算と一致する。
**SPEC のままなら、この 8 件が `~/.ssh/known_hosts` に入っていた。**

対処として `-o UserKnownHostsFile=/tmp/kh_audit.txt` を足し、
既存の `known_hosts` を複製してから使った。無人で止まらないという
`accept-new` の意図は保たれ、禁止 #2 も守られる。
測定後に `~/.ssh/known_hosts` の大きさ・更新時刻・要約値が
測定前と一致することを確認した。

---

## 5. 陽性対照

**判定が通ったことは、その判定が働いていることを意味しない。**

| 判定 | 何を入れれば失敗するはずか | 実際に何が起きたか |
|---|---|---|
| 指紋の照合が空振りでない | 受け入れ一覧に実在する別の指紋を照合にかける | 中継の鍵は **0**、実在する指紋は **1**。照合は働いている |
| 秘匿の検査が働いている | 鍵の書き出しを模した囮（`BEGIN OPENSSH PRIVATE KEY` の行）を検査にかける | 囮で **1**。実際の記録の一致 2 件は `sshd_config` の**オプション名**で値ではない |
| 記録に鍵素材が混入していない | base64 の長い塊（`AAAA` で始まる 68 文字以上）が現れれば混入 | 一致 1 件、その**一致長は 4 文字**。検査模様を文章に書いた箇所であり鍵素材ではない |
| 認証の測定が鍵で識別している | 到達できる同じ宛先へ、通らないはずの鍵（`/dev/null`）を与える | `Permission denied`、`REACHABLE` の件数 **0**。同じ lecun が専用鍵では `REACHABLE` |
| その対照が鍵の代理で迂回されていない | 代理に鍵が載っていれば `-i` を無視して通りうる | `SSH_AUTH_SOCK` は設定されているが `ssh-add -l` が `Error connecting to agent`。**代理は使えない** |
| 禁止 #2 を破っていない | 測定が `~/.ssh/known_hosts` を書けば大きさか要約値が動く | 測定前後で `size=2934` / `mtime=1785352326` / 要約値の先頭 `4a1587d6` が**完全一致**。迂回先は 9 から 17 へ増えており、**書き込み自体は確かに起きた** |
| 抑止が効いている | `grep -c sync-pause ~/bin/m2-sync.sh` が 0 なら抑止は届いていない | **2**。零ではない |

---

## 6. 作業ツリーと後始末

### Step 3 検証

    make task-validate  →  OK / 1 task(s), 0 failed / validate_exit=0
    make task-preflight →  5 PASS / 0 WARN / 4 SKIP / 0 FAIL / preflight_exit=0

SKIP 4 件（**合格ではなく「実行されなかった」**）: `P2 cuda_ext_loaded` と
`P3 deterministic_flags` は `plan.env.preflight` に記載なし、
`P4 prereg_committed` と `P5 frozen_source_hash` は `kind=analysis` のため対象外。
`P9 spec_lint` は規則 8 件を検査して該当なし。**`host_mismatch` は出なかった**
（SPEC の前提節が既知の偽陽性としていたが、本契約では発生していない）。

### Step 5 変更が契約の範囲に限られること

    make forbidden-check
    {"base": "origin/phase0", "changed": 6, "checked": 6, "errors": [],
     "excluded": 0, "excluded_paths": [], "generated_directories": ["context/auto/"],
     "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
    exit=0

    git --no-pager status --porcelain   →  2 行
    ?? tasks/T-2026-08-12-tunnel-key-audit-efros/
    ?? tasks/inbox.d/T-2026-08-12-tunnel-key-audit-efros.md

    unmerged=0
    runindex=0   context_auto=0   experiments=0

**契約の範囲外の未追跡物は無い。** 前契約では抽出物 2 件が残ったが、
そのとき別 commit で記録したため今回は現れていない。**同じ扱いを要する状況ではない。**

### 試験

    python -m pytest -q  →  7 failed, 417 passed, 4 skipped （28.04 s）
    実行前後の作業ツリー: 1 件 → 1 件（差分なし）

**本契約のために実測した値である**（前契約の数値を流用していない）。
失敗 7 件の内訳は前契約と同一で、SPEC 前提節が
「`test_self_contract_has_no_hit` と `test_spec_lint_passes_on_clean_contract` は
lecun 以外の全ホストで必ず失敗する。本契約に起因しない」と記すとおり。
残る 5 件（`test_engines` 1 / `test_research_logger` 4）は環境起因である。
**本契約が増やした失敗は 0。**

### Step 6 送信前の自己検査（前契約で判明した道具の欠陥を避ける）

    RESULT.md   bmp_over=0  hex40=0
    result.yaml bmp_over=0  hex40=0
    audit.md    bmp_over=0  hex40=0
    inbox.d     bmp_over=0  hex40=0

**両方とも零。** 受け皿は送信本文ではないが同じ commit に載るため併せて検査した。

**陽性対照**（この自己検査が空振りでないこと）:

    囮の文字列（基本多言語面の外の文字 1 つと 40 桁の 16 進 1 つを含む）
    decoy bmp_over=1  hex40=1

検査は働いている。前契約では送信が 2 回止まったが、**本契約では
送信前に零であることを確かめてから送る。**

### Step 7 commit

| # | hash | 内容 |
|---|---|---|
| 1 | **`ee9421c`** | `docs(sync): audit tunnel key distribution on efros`。契約 5 ファイルと受け皿 |
| 2 | （下記） | 本節のハッシュと返送結果の記録 |

commit 後の作業ツリーは **0 件（clean）**。

### Step 8 抑止の解除（削除ではなく移動）

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-12-tunnel-key-audit-efros  →  released
    ls -la .sync-pause  →  repo 直下から消えた
    退避先: -rw-rw-r-- 1 ubuntu ubuntu 0  8月 12 11:10

退避先が repo の外であるため、追跡外の残骸は作業ツリーに残らない（**0 件**）。

### Step 9 報告の返送

**一度で送信できた。**

    {
      "task_id": "T-2026-08-12-tunnel-key-audit-efros",
      "verdict": "pass",
      "n_issuer_defects": 1,
      "report_sha256": "5ba19c3f4ec48402fb43acd9e449b27207a982fe5fbd3987d3e8054bc09d8217",
      "report_bytes": 18946,
      "replaced_blocks": 0
    }
    exit=0

前契約では返送が 2 回止まった（秘匿検査が git のハッシュを鍵と誤認、
および切り分けの単位が UTF-16 でなかったための上限超過）。
**本 SPEC はその 2 件を Step 6 の自己検査として取り込んでおり、
送信前に零であることを確かめたため一度で通った。**
**報告が次の契約の品質を上げた実例である。**

### 完了判定 13〜17 の実測値

| # | 判定 | 実測値 |
|---|---|---|
| 13 | 12 項目すべてに実測値または UNKNOWN がある | **空欄なし**（§2 の 12 行） |
| 14 | 送信前の自己検査が両方とも零 | `bmp_over=0` / `hex40=0` を 4 ファイルすべてで確認。囮による陽性対照は `1` / `1` |
| 15 | 作業ツリーの変更が契約の範囲に限られる | `forbidden-check` **pass / violations 0 / errors 0**（changed 6 / checked 6）。未追跡は契約の 2 経路のみ。`runindex/` `context/auto/` `experiments/` はいずれも 0 件。未解決 0 |
| 16 | 抑止が repo 直下から消えている | `released` / `repo 直下から消えた`。退避先は `/tmp/.sync-pause.released.T-2026-08-12-tunnel-key-audit-efros`（**repo 外**）。作業ツリーの残骸 0 件 |
| 17 | 報告が台帳へ返っている | **一度で `exit=0`**。`verdict: pass` / `report_bytes: 18946` / `n_issuer_defects: 1`。前契約では 2 回止まったが、本 SPEC が予防手順を取り込んだため停止しなかった |

---

## 7. 逸脱

1. **（spec_defect）Task 3 Step 2 に `UserKnownHostsFile` を足した。**
   禁止 #2 と `accept-new` の衝突を避けるため。§4.1 のとおりで、
   迂回しなければ 8 件の書き込みが `~/.ssh/` に入っていた。
2. **（judgement）SPEC にない追加測定を行った。**
   中継の鍵だけでは「efros はどこへ入れるか」が
   `Permission denied` 一色になり判断材料にならない。専用鍵
   `id_rsa_efrostolecun` で lecun を測り `REACHABLE` を得た。
   **同じ宛先が鍵によって異なる結果を返すことが、測定の妥当性の裏づけにもなった。**
3. **（judgement）鍵の代理の状態を測った。**
   SPEC は要求していないが、`-i /dev/null` の陽性対照が代理経由で
   迂回されていないことを示すために必要と判断した。
4. **（judgement）手元 5 鍵すべてについて受け入れ照合を行った。**
   SPEC は中継の鍵 1 件のみを求めているが、共有鍵方式かどうかの
   判定には全件が要ると判断した。5 件すべて 0 であった。
5. **（judgement）`ip` コマンドが不在のため住所の測定を代替した。**
   `/proc/net/fib_trie` と `/etc/hosts` と `hostname -I` の三通りで
   一致を確認した。SPEC は `fib_trie` を代替として挙げており、その範囲内である。

`conventions_rev` の実測と置換は SPEC が「逸脱ではなく手順」と定めているため
ここには書かない（§1 に記載）。

---

## 8. 断定できなかったこと（UNKNOWN）

- **efros が他ノードからどの住所で見えるか。** 自ホストの住所は `172.17.0.21`
  （容器の内側）で、物理側に `50072` の転送があるかは外からしか測れない。
- **philip へ認証が通るか。** 経路が無いため**判定不能**。鍵の有無ではなく
  経路の問題であり、前契約の結論と一致する。
- **lecun を中心にできるか。** efros から lecun へ入れることは測った。
  **他の 9 台から lecun へ入れるかは efros からは測れない。**
- **他ノードの `authorized_keys` の中身。** 読み取りも他ホストでの命令実行も
  禁じられている（`echo` のみ許可）。どのノードがどの鍵を受け入れるかは
  各ホストの並行測定でしか埋まらない。
- **`id_ed25519_github.pub` の注釈が `ubuntu@lecun` である理由。**
  lecun で作った鍵が複製された可能性を示唆するが、**注釈は自己申告であり
  断定しない。** 本契約の判断には影響しない（github 用であり中継に使わない）。
- **`~/.ssh/config` の philip 用 `IdentityFile` が macOS の経路
  `/Users/dakyo-mba/...` を指し、このホストに存在しない理由。**
  別の機械の設定が持ち込まれたと見えるが経緯は測れない。
  **中継はこの別名を使わない**（`keeper.sh:16` が経路を直接与える）ため、
  同期停止の原因ではない。

# RESULT — T-2026-08-12-tunnel-key-audit-andrew

**kind:** analysis  **status:** pass  **host:** `Andrew`  **branch:** `exp/andrew`
**depends_on:** `T-2026-08-12-sync-audit-andrew`

実測の生ログは `audit.md`。**秘密鍵の中身は一切含まない。指紋と経路名のみ。**

---

## 1. 解決された参照

| spec の記載 | 解決先 | 値 |
|---|---|---|
| `contract.conventions_rev` | `git --no-pager log -1 --format=%h -- context/conventions.md` | **`d422b08`**（spec.yaml の記載と一致。置換不要） |
| `contract.inject_verbatim: [conventions#prohibitions]` | `context/conventions.md` の `prohibitions` アンカー | 下記に原文をそのまま置く |

`inputs.denominator.ref` / `inputs.sigma_policy` / `inputs.frozen_source.ref` は本契約に無い。

### conventions#prohibitions（原文・要約していない）

    <a id="prohibitions"></a>
    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### 参照しなかったものの明示

SPEC の指示に従い記す。**本契約はいずれの Task でもデータも分割も参照していない。**
`inputs.data.dataset`（`egosurgery_phase_v1`）と `inputs.data.split_files`
（`data/splits/ego_val.txt`）は雛形の必須項目として残っているだけで、一度も開いていない。
したがって `no_split_redefine` `no_raw_write` `no_frozen_change` は
**本契約では成立しようがない**（触れる対象が測定の範囲に入っていない）。

---

## 2. 結論

**中心を別のホストへ移す案は、鍵の登録を追加しなければ採れない。** 双方向とも塞がっている。

1. **出て行く向き: 通らない。** 中継に使われている鍵（`id_ed25519_andrewtophilip`、
   `SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k`）で他の九台へ SSH した結果、
   **認証が通った先は 0 件**。九台すべてが `Permission denied (publickey,password)` である。
   口は開いている（前契約で `50072` が `OPEN`）が、**鍵が通らない。**
2. **入って来る向き: 受け入れていない。** 自ホストの `authorized_keys` は **2 行のみ**で、
   登録されているのは `ubuntu@aolab`（RSA）と `dakyo-mba@dmba.local`（ED25519）。
   **中継の鍵の指紋は含まれない（照合 0、陽性対照 1）。**
   すなわち**自ホストは現状のままでは中心になれない。**
3. **鍵は philip 専用に配られていた。** 目印は `.tunnel_to_philip` の 1 件だけで、
   他ホスト向けの目印は存在しない。`known_hosts` に載っている構内の宛先も
   `192.168.196.150`（philip）のみで、残り九台は未知であった。
   **星型は経路だけでなく鍵の配布でも星型である。**
4. したがって前契約の結論（同期処理側の設定変更は要らない）に対し、**鍵の側は要る。**
   どのホストを中心にするにせよ、**各ノードの公開鍵を新しい中心の `authorized_keys` へ
   登録する作業が必要**である。本契約はその作業を行っていない（読み取りのみ）。

**測れなかった重要な点**: 「正しい鍵なら通る」という向きの確認は取れていない（§5）。
唯一の実績のある宛先（philip）が到達不能なためである。

---

## 3. 完了判定 12 項目（実測値。「実施した」ではなく「何が出たか」）

| # | 判定 | 実測値 |
|:--:|---|---|
| 1 | 中継の目印を集合として列挙した | **2 件**（`.tunnel.log` / `.tunnel_to_philip`）。経路を指すのは後者のみ、44 バイト、`POINTS_TO=/home/ubuntu/.ssh/id_ed25519_andrewtophilip`。**他ホスト向けの目印は 0 件** |
| 2 | 鍵の実在と指紋を測った | 実在。ED25519 256 ビット、権限 `600`、公開鍵が並置。`SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k`（`ubuntu@Andrew`）。**中身は出力していない** |
| 3 | 手元の公開鍵を集合として列挙した | **4 件**。`dvnHda...`(deploy-Andrew) / `i7+kCZ...`(中継鍵) / `zcSWxJ...`(github 用) / `DIwYkc...`(RSA 版、3072) |
| 4 | 記録に鍵の値が含まれない | 検査 **2 件**だが、いずれも `sshd_config` の注釈行に現れる語（`prohibit-password` 等）で**名前であり値ではない**。鍵の値由来は **0**。囮による陽性対照 **1** |
| 5 | 受け入れの一覧を集合として探した | `~/.ssh/authorized_keys` の **1 ファイル・2 行**。`authorized_keys2` は不在。`sshd_config` の `AuthorizedKeysFile` は注釈のままで既定値、**別の場所を指していない** |
| 6 | 登録されている指紋を列挙した | **2 件**。`SHA256:NtZ4Kl...`（`ubuntu@aolab`、RSA 3072）と `SHA256:rpVfps...`（`dakyo-mba@dmba.local`、ED25519） |
| 7 | 中継の鍵が自ホストに登録されているかを照合した | **0 件**。陽性対照は実在する 2 指紋でいずれも **1**、存在しない指紋で **0**。手元 4 鍵すべてでも **0** |
| 8 | 自ホストの住所を測った | `172.17.0.26`（`/etc/hosts`）。保有する帯は `127.0.0.0/8` と `172.17.0.0/16` のみで、**`192.168.196.0/24` を持たない**。`ip` コマンドは不在のため `/proc/net/fib_trie` で代替。**外からどう見えるかは UNKNOWN** |
| 9 | 対象一覧を三つの出所から集め件数を記録した | `~/.ssh/config` **2 件** / `/etc/hosts` **7 行** / 同期処理の設定 **11 アドレス** -> 構内 **10 台** + 自ホスト = **11 台**。既知の構成と一致し**縮んでいない** |
| 10 | 全対象で認証を測り合計が一致した | **10 対象**を測定。`AUTH_OK 0 + DENIED 9 + NOCONN 1 = 10 = total_lines`。**一致** |
| 11 | 認証の可否と接続の可否を区別した | 認証成功 **0** / 鍵が通らない（`Permission denied (publickey,password)`）**9** / 接続失敗（`No route to host`）**1**（`192.168.196.150` のみ） |
| 12 | 通らないはずの鍵で通らないことを確かめた | `/dev/null` と github 用鍵の 2 通りとも `Permission denied`。**`REACHABLE` は返らず。** ただし正方向の対照は取れず（§5） |
| 13 | 12 項目すべてに実測値または UNKNOWN | 空欄なし（本表） |
| 14 | 送信前の自己検査が両方とも零 | 末尾に記す |
| 15 | 作業ツリーの変更が契約の範囲に限られる | 末尾に記す |
| 16 | 抑止が repo 直下から消えている | 末尾に記す |
| 17 | 報告が台帳へ返っている | 末尾に記す |

---

## 4. 測れなかったもの（UNKNOWN）

| 項目 | 理由 |
|---|---|
| 「正しい鍵なら認証が通る」向きの対照 | 実績のある唯一の宛先（philip）が `No route to host` で到達できない。到達できる九台では正しい鍵が手元に無い |
| 自ホストが他ノードからどの住所で見えるか | 自ホストは `172.17.0.26` のみを持ち、外側での対応付けは容器の内側から観測できない |
| `authorized_keys` の `ubuntu@aolab` が philip と ilya のどちらか | 前契約で `hostname` が `aolab` を返すのは 2 台と判明している。指紋だけでは判別できない |
| 外から見える `50072` と sshd の待受 `22` の対応付け | `sshd_config` の `Port` は注釈のままで既定値 22。転送は容器の外側の設定であり読めない |
| 他ホスト側の `authorized_keys` の中身 | 他ホストで `echo` 以外を実行しない契約のため測れない。**推測で埋めない** |
| 他ホストが互いに認証できるか | 同上。本ホストからは自分が出す向きしか測れない |

---

## 5. 陽性対照（判定が空振りでないことの確認）

| 判定 | 何を入れれば失敗するはずか | 実測 |
|---|---|---|
| 指紋の照合（中継鍵が未登録＝0） | `/tmp/authfp.txt` に実在する指紋を与える。常に 0 を返す壊れ方なら 0 が返る | 実在指紋 2 種でいずれも **1**、存在しない指紋で **0**。識別している |
| 記録に鍵の値が無い | 鍵の書き出しを模した囮（`-----BEGIN OPENSSH PRIVATE KEY-----`）を同じ検査に通す | 囮で **1**。検査は働いている。囮は外部へ送らず削除した |
| 認証が通らない（`AUTH_OK=0`） | 通らないはずの鍵を、到達できた住所へ与える。返れば鍵が効いていない | `/dev/null` **不通** / github 用鍵 **不通**。いずれも `REACHABLE` を返さず |
| 認証の測定が空振りでない | 成功を示す語を別の探し方で数える | `REACHABLE` の出現 **0**、`Welcome`/`Last login` の出現 **0**。三通りで零が一致 |
| `~/.ssh/` を変更していない | 変更していれば要約値が動く | 測定前後とも `sha256` 先頭 16 = `66ecff7020e05c5b`、`mtime` `7月3 00:47`、`size` 1956 で同一 |

**限界の明示**: 通らないはずの鍵も、中継の鍵と**同じ文言**で拒否される。したがって本測定が
示せるのは「誤った鍵が誤って通ることはない」ことまでであり、**「正しい鍵なら通る」向きの
対照は取れていない。** この向きは UNKNOWN とする。

---

## 6. 起票者の誤り

**2 件あった。**

### 1. `self_contradiction` — 指示された選択肢が自らの禁止事項に触れる

Task 3 Step 2 は `-o StrictHostKeyChecking=accept-new` を必ず付けるよう指示するが、
この選択肢は**未知の宛先の公開鍵を `~/.ssh/known_hosts` へ書き込む**。同じ SPEC の
禁止 2 は `~/.ssh/**` の変更を禁じている（読むのは可）。実測したところ、十台のうち
`known_hosts` に既知なのは `192.168.196.150` のみで、**残り九台は未知**であった。
すなわち指示どおり実行すると九件の書き込みが発生し、禁止 2 に触れる。
指示に従えば禁止に触れ、禁止を守れば指示に従えないという、契約内部で両立しない指定である。
是正: 書き込みの起きない `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null`
に替え、測定前後の要約値が同一であることで無変更を示した。

### 2. `check_does_not_check` — 陽性対照が意図した性質を検査していない

Task 3 Step 4 は「通らないはずの鍵を与えて `REACHABLE` が返らないこと」を陽性対照とする。
しかし到達できる九台では**どの鍵でも `Permission denied` になる**ため、この対照は
「鍵による識別が働いていること」を示さない。**鍵を無視して常に拒否する壊れ方**でも
同じ結果になり、区別がつかない。対照が意味を持つのは、正しい鍵で通る宛先が
少なくとも一つある場合に限られるが、その宛先（philip）は経路の消失で到達できない。
是正: 対照は指示どおり実行して結果を記録したうえで、**この対照が示せる範囲**
（誤った鍵が誤って通ることはない）と**示せない範囲**（正しい鍵なら通る）を分けて明記し、
後者を UNKNOWN とした。

---

## 7. 逸脱（deviations）

1. **judgement** — Task 3 Step 2 の `StrictHostKeyChecking=accept-new` を
   `StrictHostKeyChecking=no` と `UserKnownHostsFile=/dev/null` に替えた。理由は前項 1。
   認証の測定内容は変わらない。無変更は測定前後の要約値の一致で示した。
2. **judgement** — Task 3 Step 4 の陽性対照を、指示された `/dev/null` に加えて
   **用途の違う実在の鍵**（github 用 ED25519）でも実施した。`/dev/null` は鍵として
   読み込めないため「鍵を渡さなかった場合」に近く、**実在するが登録されていない鍵**で
   確かめたほうが対照として強いと判断した。結果は両方とも不通で一致。
3. **judgement** — Task 2 Step 3 の照合を、指示された中継鍵 1 件だけでなく
   **手元の 4 鍵すべて**について実施した。零を別の探し方で確かめるため（申し送り 1）。
4. **environment** — Task 2 Step 4 の `ip -4 addr show` は `ip` コマンドが不在で
   実行できなかった。SPEC の代替（`/proc/net/fib_trie`）へ落として測った。

### 常駐処理による統合（実行者の逸脱ではない・事実として記録）

抑止の目印は契約の冒頭で設置し、稼働中の `~/bin/m2-sync.sh` が対応していることを
`grep -c sync-pause` = **2**（0 なら未対応）で確認した。設置後の統合の有無は末尾に記す。

---

## 8. `P9 spec_lint` と `SKIP` の一覧

    P9 spec_lint  WARN  host_mismatch@tasks/T-2026-08-12-tunnel-key-audit-andrew/SPEC.md:4

**SPEC が既知の偽陽性と明記している**（`socket.gethostname()` を正規化せず比べるため。
実測 `Andrew`、宣言 `andrew` の大文字小文字の差）。切り分けは繰り返していない。

`SKIP` された項目（合格ではなく実行されなかった）: `P2 cuda_ext_loaded`、
`P3 deterministic_flags`（いずれも `plan.env.preflight` に記載なし）、
`P4 prereg_committed`、`P5 frozen_source_hash`（いずれも `kind=analysis` のため対象外）。

---

## 9. 終盤の判定（完了判定 14 から 17）

### 14 送信前の自己検査

    RESULT.md   bmp_over=0 hex40=0
    result.yaml bmp_over=0 hex40=0
    audit.md    bmp_over=0 hex40=0
    inbox.d の記録 bmp_over=0 hex40=0

**両方とも零。** 基本多言語面の外の文字と四十桁の十六進はいずれの報告ファイルにも無い。
履歴の識別子は短縮形のみを使った。

### 15 作業ツリーの変更が契約の範囲に限られる

    make forbidden-check
    {"base": "origin/phase0", "changed": 14, "checked": 14, "errors": [], "excluded": 0,
     "excluded_paths": [], "generated_directories": ["context/auto/"],
     "generated_files": ["tasks/inbox.md"], "status": "pass", "violations": []}
    exit=0

    git --no-pager status --porcelain
    ?? tasks/T-2026-08-12-tunnel-key-audit-andrew/
    ?? tasks/inbox.d/T-2026-08-12-tunnel-key-audit-andrew.md
    2 行

    unmerged=0

**契約のディレクトリと受け皿の 2 件のみ。** 範囲外の未追跡物は無く、前契約のような
別 commit への切り分けは不要であった。`.sync-pause` は `.gitignore` 済みのため
一覧に現れない（実在は `ls -la` で確認済み）。

### 16 抑止の解除

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-12-tunnel-key-audit-andrew
    released
    ls -la .sync-pause  ->  repo 直下から消えた

**退避先: `/tmp/.sync-pause.released.T-2026-08-12-tunnel-key-audit-andrew`。**
削除ではなく移動で解除し、repo 直下に未追跡ファイルを残していない。

抑止が実際に効いていたことの確認:

    2026-08-12 11:41:36 [andrew] 一時停止中: /home/ubuntu/slocal2/m2/.sync-pause があるため分岐へ書き込まない（消せば再開）
    設置（11:33）以降の auto-merge / auto-push 件数 = 0

**常駐処理による統合は本契約の実行中に発生していない。**

### 17 報告が台帳へ返っている

    make task-report TASK=T-2026-08-12-tunnel-key-audit-andrew; echo "exit=$?"
    {
      "task_id": "T-2026-08-12-tunnel-key-audit-andrew",
      "verdict": "pass",
      "n_issuer_defects": 2,
      "report_sha256": "8b08ea0c4c6dbae4 ...（先頭 16 文字のみ記載）",
      "report_bytes": 13751,
      "replaced_blocks": 0
    }
    exit=0

**終了コードは 0。** 前契約では配管を通したために zsh の配列添字で取得できなかったが、
本契約の SPEC は配管を挟まない書き方を指示しており、そのまま取得できた。
秘匿の検査は `make task-report` の内側にあり、停止していない。

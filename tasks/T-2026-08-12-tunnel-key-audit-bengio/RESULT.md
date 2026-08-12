# RESULT — T-2026-08-12-tunnel-key-audit-bengio

**task_id:** `T-2026-08-12-tunnel-key-audit-bengio`　**kind:** `analysis`
**depends_on:** `T-2026-08-12-sync-audit-bengio`
**実行ホスト:** `bengio`　**分岐:** `feat/tunnel-key-audit-bengio`（起点 `origin/phase0`）
**実行日:** 2026-08-12　**repo:** `~/slocal2/m2`

読み取りのみで実行した。**鍵の生成・配布・変更は一切行っていない。中心の移設も行っていない。**
秘密鍵の中身はどこにも含めていない。生の出力は `audit.md`（296 行）にある。

`inputs.data` の `dataset` と `split_files` は雛形の必須項目であり、**本契約はいずれの Task でも
データも分割も参照しなかった。** `no_split_redefine` `no_raw_write` `no_frozen_change` は
本契約では成立しようがなく、抵触しようもない。**参照しなかったことを記録する。**

---

## 1. 解決された参照

### 1.1 `contract.inject_verbatim` — `conventions#prohibitions`

`context/conventions.md`（実測 rev `d422b08`）の**原文**。要約していない。

    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### 1.2 継承された `sigma_policy`

`inputs.sigma_policy` の記載が無いため `conventions#sigma` の既定値を継承した。
本契約は σ 判定を行わないが記録する。

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

### 1.3 `conventions_rev`

起票時の記載 `d422b08`、実測 `d422b08`。**一致しており置換は不要だった。**

### 1.4 解決しなかった参照

`inputs.denominator.ref` と `inputs.frozen_source.ref` はいずれも記載が無く対象外。
`P4` と `P5` も `kind=analysis` のため SKIP。

---

## 2. 検証

| 検査 | 結果 |
|---|---|
| `make task-validate` | **exit 0**、WARN 0 件 |
| `make task-preflight` | **exit 0**（4 PASS / 1 WARN / 4 SKIP / 0 FAIL） |
| `make forbidden-check` | **exit 0**、`status=pass` / `violations` なし |
| 送信前の自己検査 | `bmp_over=0` / `hex40=0`（全報告ファイル） |

**SKIP された 4 項目は「合格」ではなく「実行されなかった」。** `P2` と `P3` は
`plan.env.preflight` に記載が無いため、`P4` と `P5` は `kind=analysis` のため。

`P9` の `host_mismatch` WARN は SPEC が既知の偽陽性と明記しており、切り分けを繰り返していない。

`.sync-pause` の実効性は SPEC §0 の手順で確認した。`grep -c sync-pause ~/bin/m2-sync.sh` は
**2** を返し、該当は 40 行目と 41 行目である。抑止は効く。

---

## 3. 結論

**中継の鍵は philip 専用であり、他のどのホストにも通らない。**
**bengio が受け入れている遠隔ノードは philip と lecun の二台だけである。**

| 問い | 実測による答え |
|---|---|
| 中継に使う鍵はどれか | `~/.ssh/id_ed25519_bengiotophilip`（ED25519、指紋 `SHA256:FsFyZQKu…`） |
| その鍵で他の九台へ入れるか | **一台も入れない。** 九台すべてで拒否、philip は経路なし |
| 拒否は鍵を提示したうえでのものか | **そうである。** 詳細出力で `Offering public key` まで到達している |
| bengio は誰を受け入れているか | **三件のみ。** 遠隔ノード由来は `philip-to-bengio` と `lecuntobengio` の二件 |
| bengio は中心になれるか | **そのままではなれない。** 八台からの登録が無い |

**中心を別ホストへ移す案は、鍵の登録を追加しない限り採れない。**
口が開いていること（前契約で実測）と、鍵が通ることは別であった。

---

## 4. 実測

### 4.1 中継に使われている鍵（Task 1）

中継の目印は集合として列挙し、**先頭がドットのものも落としていない**（注意 7）。

| 項目 | 実測 |
|---|---|
| 目印の件数 | **2**（`.tunnel.log` と `.tunnel_to_philip`） |
| `.tunnel_to_philip` の大きさ | 44 バイト |
| 指す経路 | `/home/ubuntu/.ssh/id_ed25519_bengiotophilip` |
| 鍵の実在 | あり（399 バイト、権限 600）。公開鍵も並置（95 バイト） |
| 種別と指紋 | **ED25519 256 ビット、`SHA256:FsFyZQKufeBgfNiNZfztXw2FclTab7ySNm1vsfxPPSE`**、コメント `ubuntu@Bengio` |

手元の鍵は集合として列挙した。**特定の名前を探していない。**

| 数え方 | 件数 |
|---|---|
| 公開鍵から指紋を出せたもの | **6** |
| 秘密鍵から指紋を導出できたもの | **5** |

差の一件は `id_rsa_mactobengio.pub`（RSA 4096、`dakyo-mba@dmba.local`）で、
**外部の機械が bengio へ入るための公開鍵**であり秘密鍵側が無いのは当然である。

**名前が実体と食い違うものがある。** `id_rsa_bengiotolecun` と `id_rsa_bengiotophilip` は
名前に `rsa` を含むが、実体はいずれも **ED25519** である。名前から種別を推定してはならない。

### 4.2 自ホストが受け入れているもの（Task 2）

| 項目 | 実測 |
|---|---|
| 受け入れの一覧 | `~/.ssh/authorized_keys` のみ（`authorized_keys2` は不在） |
| 行数 | **3** |
| 別の場所を指す設定 | 無し。`sshd_config` の該当行はすべて番号記号で始まる既定値のまま |

登録されている三件の指紋。

| 種別 | 指紋（先頭） | コメント |
|---|---|---|
| RSA 4096 | `SHA256:Vrh/uPWK…` | `dakyo-mba@dmba.local` |
| RSA 4096 | `SHA256:438go0wA…` | `philip-to-bengio` |
| RSA 4096 | `SHA256:xkvYaIjp…` | `lecuntobengio` |

**中継の鍵の指紋で照合した結果は 0 件である。** 陽性対照として実在する二つの指紋で
同じ照合を行うと、いずれも 1 件を返した。**照合は常に零を返す壊れ方をしていない。**

**ただしこの検査は、SPEC が主張する問いに答えていない（§6.1）。** 中継の鍵
`id_ed25519_bengiotophilip` はコメントが `ubuntu@Bengio` であり、**bengio 自身が philip へ
出て行くための鍵**である。それが bengio の受け入れ一覧にあるかは「bengio が自分自身へ
入れるか」を測っているにすぎない。

**「bengio が中心になれるか」を決めるのは、他ノードの鍵が bengio に登録されているかである。**
集合として突き合わせた結果は次のとおり。

| 項目 | 件数 |
|---|---|
| 手元の公開鍵の指紋 | 6 |
| 受け入れ一覧の指紋 | 3 |
| 両方に現れる指紋 | **1**（`dakyo-mba@dmba.local`。手元に写しがある外部の機械） |
| 受け入れにあるが手元に秘密鍵が無いもの | **2**（`philip-to-bengio` と `lecuntobengio`） |

**遠隔ノード由来の登録は二件のみ。他の八台は bengio に鍵を登録していない。**

自ホストの住所は `172.17.0.15` のみである（`ip` コマンドは不在のため `/proc/net/fib_trie` と
外向き経路の両方から測った。`/etc/hosts` の記載とも一致）。他ノードは `192.168.196.x` 帯にある。
**bengio がその帯からどの住所で見えるかは自分では測れない。UNKNOWN とする。**

### 4.3 他の九台への認証（Task 3）

対象一覧は三つの出所から集めた。`~/.ssh/config`（`ssh_count=3`）、`/etc/hosts`、
syncthing 設定の `tcp://`。和集合は 12、うち自ホストと loopback を除く**遠隔は 10 台**。
**自ホスト 1 と遠隔 10 で 11 台、既知の構成と一致する。一覧は縮んでいない。**

`~/.ssh/config` は philip に `id_rsa_bengiotophilip` を指定しているが、**中継が使う鍵は
`id_ed25519_bengiotophilip` であり別物である。** 本 Task は後者で測った。

| 分類 | 件数 | 意味 |
|---|---|---|
| AUTH_OK | **0** | 中継の鍵で入れるホストは一台も無い |
| DENIED | **9** | 口は開いているが鍵が通らない。登録の追加が要る |
| NOCONN | **1** | philip のみ。`No route to host`（前契約と一致） |
| 未分類 | 0 | なし |
| **合計** | **10** | **対象数 10 と一致。測り漏れなし** |

拒否された九台は `dlsta` `adam` `ilya` `hinton` `he` `ian` `lecun` `andrew` `efros`。
いずれも `Permission denied (publickey,password)` である。

**陰性対照。** 通らないはずの鍵（`/dev/null`）を、口が開いていた住所へ与えた結果は
`Permission denied (publickey,password)` であり、**`REACHABLE` は返らなかった。**

**追加の切り分け。** 陰性対照と本測定が同じ文言を返すため、鍵が実際に提示されて
いるかを詳細出力で分けた。

    中継の鍵: Offering public key: .../id_ed25519_bengiotophilip ED25519 SHA256:FsFyZQKu... explicit
    /dev/null: Trying private key: /dev/null   （Offering に至らない）

**実鍵は提示まで到達してサーバに拒否されている。** したがって九台の拒否は
「鍵を提示したうえでの拒否」であり、「提示していないための拒否」ではない。**測定は健全である。**

### 4.4 記録に鍵の値が含まれないこと

`audit.md` への検査は **13 件**に一致した。**一件ずつ目視し、すべて名前であって値でないことを
確かめた。**

| 箇所 | 実体 |
|---|---|
| 2 件 | `sshd_config` の既定コメント（`PermitRootLogin prohibit-password` と説明文） |
| 10 件 | SSH が返した認証方式の名前 `publickey,password`。拒否を示す文言 |
| 1 件 | `Trying private key` という経路の説明 |

別の探し方でも値の不在を確かめた。`BEGIN` で始まる行 **0**、base64 の長い連続（60 文字超）
**0**、公開鍵本体（`AAAAB3` / `AAAAC3` 始まり）**0**。

**陽性対照。** 囮（`-----BEGIN OPENSSH PRIVATE KEY-----` を含む一時ファイル）へ同じ検査を
かけると **1** を返した。**検査は働いている。** 囮は外部へ送らず削除した。

---

## 5. 完了判定

| # | 判定 | 実測値 |
|---|---|---|
| 1 | 中継の目印を集合として列挙 | **2 件**。経路は `/home/ubuntu/.ssh/id_ed25519_bengiotophilip` |
| 2 | 鍵の実在と指紋 | 実在（399 バイト、権限 600）。**ED25519 256、`SHA256:FsFyZQKu…`**。中身なし |
| 3 | 手元の公開鍵を集合として列挙 | **公開鍵 6 件 / 秘密鍵から導出 5 件**。全件の指紋を記録 |
| 4 | 記録に鍵の値が含まれない | 一致 13 件を目視、**すべて名前**。`BEGIN` 行 0 / base64 長連続 0 / 鍵本体 0 |
| 5 | 受け入れの一覧を集合として探した | `~/.ssh/authorized_keys` のみ、**3 行**。別の場所を指す設定なし |
| 6 | 登録されている指紋を列挙 | **3 件**（Mac / `philip-to-bengio` / `lecuntobengio`） |
| 7 | 中継の鍵が登録されているかの照合 | **0 件**。陽性対照は 1 件を返す。照合は健全 |
| 8 | 自ホストの住所 | **`172.17.0.15` のみ**。他帯からどう見えるかは **UNKNOWN** |
| 9 | 対象一覧を三つの出所から集めた | 和集合 **12**、遠隔 **10**、自ホスト込み **11**。既知の構成と一致 |
| 10 | 全対象で認証を測り合計が一致 | **10 = 10**。未分類 0 |
| 11 | 認証の可否と接続の可否を区別 | **AUTH_OK 0 / DENIED 9 / NOCONN 1** |
| 12 | 通らないはずの鍵で通らないこと | `/dev/null` で `Permission denied`。**`REACHABLE` は返らない** |
| 13 | 全項目に実測値または UNKNOWN | 空欄なし。UNKNOWN は §7 に列挙 |
| 14 | 送信前の自己検査が両方とも零 | `bmp_over=0` / `hex40=0`（3 ファイルすべて） |
| 15 | 変更が契約の範囲 | Task 4 Step 5 で確認（下記） |
| 16 | 抑止が repo 直下から消えている | Task 4 Step 8 で実施（下記） |
| 17 | 報告が台帳へ返っている | Task 4 Step 9 で実施（下記） |

---

## 6. deviations

**空にしてはならない項目である。**

### 6.1 起票者の誤り

| # | 箇所 | 誤り | 対処 |
|---|---|---|---|
| 1 | Task 2 Step 3 | **検査が主張する問いに答えていない。** 「中継の鍵が自ホストに登録されていれば自ホストは中心になれる」とするが、中継の鍵は自ホストが**出て行くための鍵**であり、それを自分の受け入れ一覧と照合しても「自分自身へ入れるか」しか分からない。中心になれるかを決めるのは**他ノードの鍵が登録されているか**である | 指示どおりの照合（結果 0）も記録したうえで、手元の鍵と受け入れ一覧を**集合として突き合わせ**、遠隔ノード由来の登録が 2 件であることを測った |
| 2 | Task 3 Step 2 | **禁止事項と衝突する。** 命令の `StrictHostKeyChecking=accept-new` は未知のホスト鍵を `~/.ssh/known_hosts` へ書き込むが、禁止 2 は `~/.ssh/**` の変更を禁じている | 意図（対話的な問い合わせで止まらない）を保つため `UserKnownHostsFile` を `/tmp` 側へ向けた。実行前後で `known_hosts` の要約値と更新時刻が不変であることを測って示した |

### 6.2 自分で判断した箇所

| # | 判断 | 理由 |
|---|---|---|
| 1 | 鍵が実際に提示されているかを詳細出力で分けた | 陰性対照と本測定が同じ文言を返すため、「提示のうえで拒否」と「提示せずに拒否」を区別しないと結論が立たない。SPEC は要求していないが、注意 6 の趣旨に沿う |
| 2 | 認証の測定に中継の鍵を使った（`~/.ssh/config` の指定鍵ではない） | 問いは「中継を張れるか」であり、中継は `~/.tunnel_to_philip` が指す鍵を使う。`config` の `IdentityFile` は別の鍵を指しており、そちらを測ると別の問いに答えてしまう |
| 3 | 秘密鍵側からも指紋を導出して突き合わせた | 公開鍵だけを数えると、公開鍵の並置が無い鍵を見落とす。注意 1 の別の探し方にあたる |
| 4 | 到達先の利用者名を `ubuntu` とした | `~/.ssh/config` に利用者名の指定が無く、自ホストの利用者が `ubuntu` であるため既定に従った。**他の利用者名は試していない**（§7） |

### 6.3 常駐処理による事象（実行者の逸脱ではない）

抑止は実効性を確認したうえで置いた（`m2-sync.sh` の 40 行目と 41 行目が参照する）。
**本契約の実行中に常駐処理による統合は発生しなかった。**

---

## 7. UNKNOWN（測れなかったこと）

| 項目 | 理由 |
|---|---|
| 他ノードが持つ中継の鍵の指紋 | 他ホストでは `echo` 以外を実行できない。**本結果は bengio 側から見た片方向のみである** |
| `philip-to-bengio` と `lecuntobengio` が、それらのホストの**中継用**の鍵かどうか | bengio からは指紋しか見えない。相手側の `~/.tunnel_to_*` を読めないため対応づけられない |
| bengio が `192.168.196.x` 帯からどの住所で見えるか | 自ホストは `172.17.0.15` しか持たない。外から見た住所は自分では測れない |
| 他の八台が bengio へ入れるか | 相手側から測る必要がある。bengio 側の受け入れ一覧に登録が無いことまでは測れた |
| 利用者名が `ubuntu` 以外で通る可能性 | 既定の `ubuntu` のみで測った。別の利用者名は試していない |
| philip が停止しているのか経路のみが遮断されているのか | 前契約と同じく bengio からは区別できない |
| 中心を移した場合に同期処理側の再設定が要るか | 共有相手の登録は全台で済んでいるという前提を再測定していない（SPEC が再測定不要としている） |

---

## 8. 生成物

| 種別 | パス |
|---|---|
| 新規 | `tasks/T-2026-08-12-tunnel-key-audit-bengio/audit.md`（生の出力） |
| 新規 | `tasks/T-2026-08-12-tunnel-key-audit-bengio/RESULT.md` / `result.yaml` |
| 新規 | `tasks/inbox.d/T-2026-08-12-tunnel-key-audit-bengio.md` |
| **未変更** | `~/.ssh/**`（要約値と更新時刻で確認）　`~/bin/**`　`~/claude-sync/**` |
| **未変更** | `runindex/` `context/auto/` `tasks/inbox.md` `experiments/` `transfer/` `data/splits/` |

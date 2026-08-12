# RESULT — 中継の鍵の配布状況の実測（lecun）

**task_id:** `T-2026-08-12-tunnel-key-audit-lecun`  **kind:** `analysis`
**実行ホスト:** `lecun`  **分岐:** `feat/tunnel-key-audit-lecun`  **status:** pass

**読み取りのみ。鍵の生成・配布・変更、中心の移設は一切行っていない。方針の判断はユーザーが行う。**
生の出力は `audit.md`（434 行）。機械可読の対は `result.yaml`。
**秘密鍵の中身はどこにも含まない。** 指紋は公開鍵の要約であり秘匿ではない。

同じ内容の契約を複数ホストで並行実行している。**他ホストの結果は見えない前提で書いた。**

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

### 参照しなかったもの（SPEC の明示による）

`inputs.data`（`egosurgery_phase_v1`）と `split_files` は雛形の必須項目として残っているが、
**本契約はいずれの Task でもデータも分割も参照していない。**
したがって `no_split_redefine` `no_raw_write` `no_frozen_change` は成立しようがない。
**参照しなかったことを記録する。**

### `inputs.sigma_policy`（省略）

`context/conventions.md#sigma` の既定値を継承した。原文。

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

本契約は数値の比較を行わないため**この継承は使っていない。使わなかったことを記録する。**

### `contract.conventions_rev`

実測して `d422b08`。`spec.yaml` の記載と一致したため置換していない（手順であり逸脱ではない）。

### L3 で実行されなかった検査

`make task-preflight` は **5 PASS / 0 WARN / 4 SKIP / 0 FAIL**。
**`SKIP` は合格ではない。** 実行されなかったのは P2 `cuda_ext_loaded`（契約に未記載）、
P3 `deterministic_flags`（同）、P4 `prereg_committed`（`kind=analysis` のため対象外）、
P5 `frozen_source_hash`（同）。`P9` の `host_mismatch` は本ホストでは発火していない
（宣言 `lecun` と `hostname` が一致するため）。

---

## 2. 結論

**残っていた未確定は解けた。ただし SPEC が指示した測り方では答えが出ない。**

| 問い | 実測による答え |
|---|---|
| 中継に使う鍵はどれか | `~/.ssh/id_ed25519_lecuntophilip`（ED25519 256、指紋 `SHA256:dL4qKLl4`） |
| その鍵はどこで通るか | **どこでも通らない。** 到達できる 9 台すべてで `Permission denied`。philip は到達不能で測れない |
| 自ホストは誰を受け入れるか | **3 台**（philip・bengio・efros）+ 人の端末 1 件。遠隔 10 台のうち **7 台は受け入れない** |
| 自ホストから誰へ入れるか | **bengio と efros へは既存の鍵で通る**（`REACHABLE`）。他 7 台へは中継の鍵では通らない |
| 中心を移せるか | **鍵の面では lecun-bengio と lecun-efros の間は既に通る。** ただし目印の新規作成と、受け入れていない 7 台分の登録が別途要る |

### 自ホストが受け入れる側として登録しているもの

`~/.ssh/authorized_keys` は **4 行**。`authorized_keys2` は無く、`sshd_config` の
`AuthorizedKeysFile` は註釈されている（既定のまま。**別の場所を指していない**）。

| 種別 | 指紋（先頭） | 註釈 | 対応 |
|---|---|---|---|
| RSA 4096 | `SHA256:hWCLg+DQ` | `philip-to-lecun` | **philip** |
| ED25519 256 | `SHA256:KS+FRL3p` | `dakyo-mba@dmba.local` | 人の端末（device 一覧に無い） |
| ED25519 256 | `SHA256:MKli4Hqp` | `bengiotolecun` | **bengio** |
| RSA 3072 | `SHA256:fOip68JP` | `ubuntu@efros` | **efros** |

    遠隔の peer 10 台のうち lecun へ入れるのは 3 台: bengio, efros, philip
    入れない 7 台: adam, andrew, dlsta, he, hinton, ian, ilya

**註釈から対応づけたものであり、指紋と相手ホストの対応を相手側で確認していない。**
註釈は自己申告である。

### 手元にある鍵（6 対。秘密鍵はすべて権限 600）

| 鍵 | 種別 | 指紋（先頭） | 名前が示す用途 | 認証の実測 |
|---|---|---|---|---|
| `id_ed25519_github` | ED25519 256 | `SHA256://dnKA2F` | 版管理 | 測っていない（対象外） |
| `id_ed25519_lecuntophilip` | ED25519 256 | `SHA256:dL4qKLl4` | **中継に使用中** | **9 台すべて拒否**。philip は到達不能 |
| `id_lecundeploy` | ED25519 256 | `SHA256:PK9k6A98` | 配備 | 測っていない |
| `id_rsa_lecuntobengio` | RSA 4096 | `SHA256:xkvYaIjp` | lecun から bengio | **`REACHABLE`** |
| `id_rsa_lecuntoefros` | RSA 3072 | `SHA256:bIJpiGyR` | lecun から efros | **`REACHABLE`** |
| `id_rsa_lecuntophilip` | RSA 3072 | `SHA256:yLlX2CaN` | lecun から philip（旧） | 測っていない（到達不能） |

### 認証の三分類（中継の鍵で全 10 台）

    AUTH_OK=0  DENIED=9  NOCONN=1  total_lines=10

**0 + 9 + 1 = 10 = 対象数。一致した。**

| 分類 | 意味 | 件数 |
|---|---|---|
| `REACHABLE` | 認証が通る。中継を張れる | **0** |
| `Permission denied (publickey,password)` | **口は開いているが鍵が通らない** | **9** |
| 接続の失敗 | 経路の問題 | **1**（philip の `No route to host`。前契約と一致） |

### 環境側の欠陥（起票者の誤りではない）

`~/.ssh/config` の `philip` の項の `IdentityFile` が
`/Users/dakyo-mba/.ssh/id_rsa_lecuntophilip` という **macOS の経路**であり、
lecun（Linux、`/home/ubuntu`）には**不在**である。人の端末の設定が写されたものと読める。

**中継はこの設定を使っていない。** `keeper.sh` は `-i "$(cat ~/.tunnel_to_philip)"` で
経路を明示的に渡すため中継の動作には影響しない。ただし人が `ssh philip` を手で叩くと
既定の鍵へ落ちる。

### 禁止 2 を守ったことの証明

SPEC Task 3 Step 2 の命令は `-o StrictHostKeyChecking=accept-new` を含み、これは
`~/.ssh/known_hosts` へ**追記する**。禁止 2 は `~/.ssh/**` の変更を禁じている。
書き込まない形へ置き換え、**測定の前後で要約値と更新時刻が変わっていないことを記録した。**

    測定前: b7dd7291ed3c8b6a292b04d31cef9f16  known_hosts  更新 2026-07-01 09:11:14
    測定後: b7dd7291ed3c8b6a292b04d31cef9f16  known_hosts  更新 2026-07-01 09:11:14

10 台すべてが未知のホストであったため、そのまま実行すれば **10 件の追記**が起きていた。

---

## 3. 完了判定 17 項目

**「実施した」ではなく「何が出たか」を書いた。空欄は無い。**

| # | 判定 | 実測値 |
|---|---|---|
| 1 | 中継の目印を集合として列挙した | **2 件**（`.tunnel.log` / `.tunnel_to_philip`）。`find` でも 2 件。`.tunnel_to_<他>` は無い。経路は `~/.ssh/id_ed25519_lecuntophilip` |
| 2 | 鍵の実在と指紋を測った | 実在。ED25519 256、`SHA256:dL4qKLl4pYnZpvnVL3kRlipacdq7ipqTpxExhCJqRr8`、399 バイト、権限 600、公開鍵の並置あり。**中身は出していない** |
| 3 | 手元の公開鍵を集合として列挙した | **6 件**（指紋を全件記載）。秘密鍵も 6 件、いずれも権限 600 |
| 4 | 記録に鍵の値が含まれない | 本番 **0** / 囮 **1**（空振りでない）。囮は repo 外に置き削除した |
| 5 | 受け入れの一覧を集合として探した | `~/.ssh/authorized_keys`（**4 行**、1504 バイト）。`authorized_keys2` なし。`AuthorizedKeysFile` は註釈されており既定のまま |
| 6 | 登録されている指紋を列挙した | **4 件**（philip / 人の端末 / bengio / efros） |
| 7 | 中継の鍵が自ホストに登録されているかを照合した | **0**。陽性対照は **1**（空振りでない）。**手元 6 鍵すべてが 0 であり、この照合は構造的に 0 を返す**（外向き鍵と受け入れ一覧の比較） |
| 8 | 自ホストの住所を測った | **`172.17.0.22`**（`127.0.0.1` も LOCAL）。既定経路 `172.17.0.1`。SPEC 指定の命令は broadcast `172.17.255.255` を返した。**他ノードから見える住所は UNKNOWN** |
| 9 | 対象一覧を三つの出所から集め件数を記録した | `ssh_count=4` / `/etc/hosts` の遠隔 **0** / `stcfg_count=11` -> 和集合 **10 台**。既知 11 台 = 遠隔 10 + 自ホスト。**縮んでいない** |
| 10 | 全対象で認証を測り合計が一致した | **10 行**。0 + 9 + 1 = **10 = 対象数** |
| 11 | 認証の可否と接続の可否を区別した | `REACHABLE` **0** / `Permission denied` **9** / 接続の失敗 **1**（philip） |
| 12 | 通らないはずの鍵で通らないことを確かめた | `/dev/null` で `REACHABLE` **0 件**（`IdentitiesOnly` の有無の二通り）。**代理は到達不能で偶然の成功はない** |
| 13 | 12 項目すべてに実測値または UNKNOWN | **空欄なし。** UNKNOWN は `result.yaml` の `unknowns` に 5 件を明示 |
| 14 | 送信前の自己検査が両方とも零 | **3 ファイルすべて `bmp_over=0` `hex40=0`**（受け皿も零）。記録の追記後に再実行しても零 |
| 15 | 作業ツリーの変更が契約の範囲に限られる | **2 行**。`tasks/T-2026-08-12-tunnel-key-audit-lecun/` と `tasks/inbox.d/T-2026-08-12-tunnel-key-audit-lecun.md`。`make forbidden-check` は `pass`（changed 6 / checked 6 / violations 0）。unmerged **0**。**契約の範囲外の未追跡物は無い** |
| 16 | 抑止が repo 直下から消えている | **消えた。** `/tmp/.sync-pause.released.T-2026-08-12-tunnel-key-audit-lecun` へ移動（repo 外）。移動後の作業ツリーは**空**。削除は使っていない |
| 17 | 報告が台帳へ返っている | **返った。** `exit=0`、`report_bytes=18683`、`n_issuer_defects=5`、`replaced_blocks=0` |

### 秘匿の検査は件数では判定できない

秘匿の検査は記録を書き進めると一致が増える。**自己言及の性質がある。**
検査の型そのものや `ssh` の誤りの表示（`publickey,password` を含む）を記録に書けば、
その語がまた一致する。**「一致件数が零」を合格条件にすると、記録を書くほど不合格に近づく。**

一致した **18 件**を一件ずつ、値の形（鍵の書き出し行 / 基数六十四の長い塊 /
語に区切りと値が続く形）に該当するかで判定した。

    一致の総数 18 / 値の形に該当 0

| 由来 | 件数 |
|---|---|
| `ssh` の認証失敗の表示 | 13 |
| 検査の型そのものの引用 | 2 |
| `sshd_config` の註釈行 | 2 |
| 囮の説明 | 1 |

**値の形に該当するものは無い。** SPEC が「値の混入と名前の一致を分けて判定する」と
指示したのは正しい設計である。**判定すべきは件数ではなく形である。**

---

## 4. 起票者の誤り（5 件）

型と本文は `result.yaml` の `issuer_defects` にある。**本文は要約していない方を読むこと。**

1. **`check_does_not_check`** — Task 2 Step 3 の照合が問いに答えていない。
   照合するのは lecun の**外向き**の鍵（philip 宛）と lecun の**受け入れ**一覧である。
   鍵は対ごとに別に作られており（外向きが `lecuntophilip`、受け入れが `philip-to-lecun`）、
   外向きの鍵を自分の受け入れ一覧に置く理由が無い。**この照合は構造的に必ず 0 を返す。**
   手元 6 鍵すべてで 0 だったことがそれを示す。SPEC は「0 なら中心にするには登録の追加が
   要る」と結論づけるが、**実際には lecun は既に 3 台を受け入れており、答えは同じ Task の
   Step 2 のデータにある。**

2. **`self_contradiction`** — 禁止 2 が `~/.ssh/**` の変更を禁じる一方、Task 3 Step 2 の命令が
   `-o StrictHostKeyChecking=accept-new` を含む。これは `~/.ssh/known_hosts` へ追記する動作で
   ある。**指示どおり実行すると禁止事項を破る。** 10 台すべてが未知であったため、
   そのまま実行すれば 10 件の追記が起きていた。

3. **`check_does_not_check`** — Task 2 Step 4 の代替命令が **broadcast の住所**を返す。
   住所は `/32 host LOCAL` の行の**前**にあるため `-A1` の向きが逆である。
   指示どおり読むと `172.17.255.255` を自ホストの住所と誤る。正しくは `172.17.0.22`。
   加えてこの命令は `| head -20` の切り詰めを含み、**SPEC 自身の注意 3 に反している。**

4. **`check_does_not_check`** — Task 3 Step 2 が中継の鍵だけで全対象を測らせる。
   この鍵は philip 専用であり他 9 台では必ず拒否される（実測で 9 件すべて）。
   決定事項は「どのホストが中心になれるか」であり、**指示どおり実行すると「どのホストへも
   認証が通らない」と結論して終わる。** `~/.ssh/config` が宣言する対応で測ると bengio と
   efros は `REACHABLE` であり、**答えが逆向きに出る。**
   同 Step は `IdentityFile` を Step 1 で表示させておきながら Step 2 で使わせていない。

5. **`check_does_not_check`** — Task 3 Step 4 の陽性対照が鍵を隔離していない。
   `IdentitiesOnly` が無いと ssh は代理や既定の鍵へ落ちるため、有効な鍵が代理に載っていれば
   `REACHABLE` が返りうる。その場合 `escalate_if`「通らないはずの鍵で認証が通り、鍵による
   識別が働いていない疑い」に該当して停止することになるが、**原因は鍵の識別ではなく対照の
   設計である。** 本環境では `SSH_AUTH_SOCK` が設定されていながら代理が到達不能だったため
   影響しなかったが、**その条件を測るよう指示されていない。**

### 申し送りは効いた

注意 7（**先頭がドットのものを落とさない**）は前契約の誤りを踏まえた追加であり、
本契約では目印（`.tunnel_to_philip`）と記録（`.tunnel.log`）の両方を落とさずに拾えた。
注意 1（零件を別の探し方で確かめる）と注意 5（一覧そのものを疑う）により、
`grep -A1` が broadcast を返していることに気付けた。
**前契約で確定した環境の事実の表**（`ps` の自己一致・`ss` の不在）により、
同じ切り分けを繰り返さずに済んだ。

---

## 5. 逸脱（8 件）

`result.yaml` の `deviations` に全件。**空にしていない。** 主なものは次のとおり。

- `accept-new` を書き込まない形へ置き換えた（禁止 2 を守るため。要約値で証明）
- 中継の鍵だけでなく `~/.ssh/config` が宣言する対応でも測った（決定事項に答えるため）
- 陽性対照に `IdentitiesOnly=yes` の形を加え、**代理の到達性を先に測った**
- `/proc/net/fib_trie` を正しく解析し直した（SPEC 指定の出力と両方を記録）
- **目印の中身を印字する前に、経路か鍵の中身かを判定した**（印字は取り消せない）
- 手元 6 公開鍵すべてを照合にかけ、0 が正常であることを示した
- 全 6 鍵と全 9 台の総当たりは**行っていない**（宣言された対応の検証にとどめた）
- `audit.md` にキリル文字が一箇所混入したため直した

### 検査が捕まえない種類の誤り

送信前の自己検査は**基本多言語面の外**の文字を数える。キリル文字は面の内側にあるため
**捕まらない。** 実際に一箇所混入し、目視で見つけて直した。
検査は既知の失敗様式（絵文字による切片の膨張）を防ぐものであり、
**文字種の妥当性を保証するものではない。**

---

## 6. 未解決（5 件）

`result.yaml` の `unknowns` に全件。要点は 3 つである。

**他ホストの受け入れ一覧は読めない。** bengio と efros へ通ることは実測したが、
他 7 台へ通らない理由が「鍵が未登録」なのか「別の利用者名が要る」のかは区別できない。
いずれも `Permission denied (publickey,password)` という同じ表示になる。

**philip への認証は測れない。** 3 ポートすべて到達不能である。中継の鍵が philip で
受け入れられているかは UNKNOWN（停止前は通っていたことが前契約の記録から読めるが、
本契約では確かめていない）。

**他ノードから lecun がどの住所で見えるかは測れない。** 自ホストは `172.17.0.22`
（容器の内側）にあり、他ノードは `192.168.196.0/24` にある。容器の外側で住所の変換が
行われている可能性があるが、その設定は自ホストから読めない。

---

## 7. 禁止事項の遵守

| # | 禁止 | 遵守 |
|---|---|---|
| 1 | 鍵の生成・複製・配布・変更・削除 | 行っていない |
| 2 | `~/.ssh/**` `~/bin/**` `~/claude-sync/**` の変更 | 読み取りのみ。`known_hosts` の無変更を要約値で証明 |
| 3 | 秘密鍵の中身の出力・記録 | 出していない。指紋と経路名と大きさと権限のみ |
| 4 | 他ホストで `echo` 以外の命令の実行・書き込み | `echo REACHABLE` のみ。他は実行していない |
| 5 | 同期処理・常駐処理の起動・停止・再起動、中継の張り切り | 行っていない |
| 6 | 中心を移す。設定を書き換える | 行っていない |
| 7 | 装置の使用・統合・自動統合の有効化 | 行っていない。抑止の目印を置いた状態で作業した |
| 8 | `make task-report` 以外の経路での外部送信 | 他の経路は使っていない |
| 9 | 生成物の再生成（`make context` / `taskindex` / `inbox`） | **実行していない** |
| 10 | 未測定の値を書く | UNKNOWN として明示（5 件） |
| 11 | `runindex/**` `context/auto/**` の手編集 | 触っていない |
| 12 | `experiments/**` `transfer/**` `data/splits/**` の変更・削除 | 触っていない。**本契約はデータを参照していない** |

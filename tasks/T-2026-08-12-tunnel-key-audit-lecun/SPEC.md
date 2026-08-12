# 中継の鍵の配布状況の実測（lecun）

**task_id:** `T-2026-08-12-tunnel-key-audit-lecun`  **kind:** `analysis`  **depends_on:** `T-2026-08-12-sync-audit-lecun`
**実行ホスト:** `lecun`  **repo:** `~/slocal2/m2`

## Goal

前契約で、設定共有が止まった原因は**中心に据えた一台への経路が失われたこと**であると
確定した。中心は常駐処理の実装に**定数で直書き**されており、他の九台へは SSH の口が
開いている。共有相手の登録は全十一台が相互に済んでおり、**中心を移しても同期処理側の
設定変更は要らない。**

**残る未確定は一つだけである。中継に使う鍵がどこに配られているか。**

中継は「中心へ SSH して転送を張る」形で組まれている。よって中心を移すには
**各ノードから新しい中心へ SSH できる**必要がある。口が開いていることは測ったが、
**鍵が通るかは測っていない。** 本契約はこれを読み取りのみで確定する。

判断の材料は三つ。中継に使われている鍵の実体（**中身は出さない。指紋のみ**）、
自ホストが**受け入れる側**として登録している鍵、他の九台へ**実際に認証が通るか**。

**鍵の生成・配布・変更は一切行わない。中心の移設も行わない。方針の判断はユーザーが行う。**

同じ内容の契約を複数ホストで並行実行している。**他ホストの結果は見えない前提で書き、
自ホストで測れないものは `UNKNOWN` とする。他ホストの値を推測で埋めない。**

## 0. 前提と禁止事項

`make task-start` が取得・分岐の作成・契約の取り込みを行う。続けて次を実行する。

    cd ~/slocal2/m2 && touch .sync-pause && grep -c sync-pause ~/bin/m2-sync.sh

**二つ目の値が `0` なら抑止は効いていない。** その場合も続行してよいが、常駐処理に
よる統合が起こりうることを報告に記す。**解除は最後の Task で行う。削除ではなく
repo の外への移動を使う。**

| # | 禁止 |
|---|---|
| 1 | 鍵を生成・複製・配布・変更・削除する |
| 2 | `~/.ssh/**` `~/bin/**` `~/claude-sync/**` を変更する（読むのは可） |
| 3 | 秘密鍵の中身を出力・記録する（**指紋と経路名は可**） |
| 4 | 他ホストで `echo` 以外の命令を実行する。他ホストへ書き込む |
| 5 | 同期処理・常駐処理を起動・停止・再起動する。中継を張る、切る |
| 6 | 中心を移す。設定を書き換える |
| 7 | 装置を使う。統合する。自動統合を有効化する |
| 8 | 外部への送信を `make task-report` 以外の経路で行う |
| 9 | 生成物を再生成する（`make context` `make taskindex` `make inbox` を実行しない） |
| 10 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 11 | `runindex/**` `context/auto/**` を手で編集する |
| 12 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |

禁止 4 の理由。他ホストでも同じ契約が並行して走っている。片方から書き込むと
もう片方の測定対象が動く。**認証が通るかを測るための `echo` だけを許す。**

**常駐処理による統合は実行者の逸脱ではない。事実として記録する。**

`inputs.data` は雛形の必須項目として残しているが、**本契約はいずれの Task でも
データも分割も参照しない。** `prohibitions` の `no_split_redefine` `no_raw_write`
`no_frozen_change` も本契約では成立しようがない。**参照しなかったことを記録する。**

### 起票者からの申し送り

前契約で起票者の誤りが十五件報告された。**同じ型を繰り返さないよう本 SPEC を直したが、
直し漏れがありうる。** 以下は全 Task に適用される。各 Step では再掲しない。

| # | 注意 |
|---|---|
| 1 | 一致件数が零のとき、別の探し方でも零になることを確かめてから結論する |
| 2 | 仕組みの挙動は実装を読んでから信じる |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない。作ってから別命令で表示する |
| 4 | 検査が空振りでないことを陽性対照で確かめる |
| 5 | 対象の一覧そのものが正しいかを確かめる。件数を必ず出力する |
| 6 | 終了コードで判定する前に、その命令が本当に走ったかを確かめる |
| 7 | 探す対象の名前を決め打ちしない。**先頭がドットのものを落とさない** |
| 8 | 出力は要約せず `tasks/T-2026-08-12-tunnel-key-audit-lecun/audit.md` へ貼る |

### 前契約で確定した環境の事実（再測定は不要）

**これらは実測済みである。同じ切り分けを繰り返さないこと。**

| 事実 | 実測値 |
|---|---|
| プロセスの計数 | **`ps -eo args \| grep -c "[x]xx"` は自己一致する。** 測定命令の全文が別プロセスの引数に載るため。`/proc/*/cmdline` を読み、**自分と祖先を除いて**数える |
| 待ち受けの一覧 | **`ss` `netstat` `lsof` はいずれも存在しない。** `/proc/net/tcp` と `/proc/net/tcp6` から復号する |
| 同期処理の記録 | `~/.syncthing.log` と `~/.tunnel.log`。**先頭がドットである** |
| 試験の失敗 | `test_self_contract_has_no_hit` と `test_spec_lint_passes_on_clean_contract` は **lecun 以外の全ホストで必ず失敗する**（`SELF_TASK` が固定）。**本契約に起因しない** |
| `P9` の `host_mismatch` | `socket.gethostname()` を正規化せず比べるための**偽陽性**。大文字小文字の差である |
| 局所の同期処理 | 四ホストすべてで `127.0.0.1:22000` が **OPEN**。**中心側の待ち受けは既に揃っている。再測定は不要** |
| 常駐処理の周期 | `sleep 1800`。稼働数は各ホスト一。**再測定は不要** |

### 道具の欠陥を避けるための書き方（前契約で判明）

| # | 守ること | 理由 |
|---|---|---|
| 1 | **報告に絵文字などの基本多言語面の外の文字を使わない** | 送信側が符号位置で切るが受け側は別の単位で数えるため、その文字を含む切片だけが上限を超えて `HTTP 400` になる |
| 2 | **四十桁の十六進を書かない。履歴の識別子は短縮形にする** | 送信前の秘匿検査が四十桁十六進を鍵と誤認して送信を止める |

対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲む。** 配列の添字に
よる終了コードの取得は使えず、単語分割も起きない。`git` を使う操作は `git --no-pager`。
`contract.conventions_rev` は起票者が現在の値を知り得ないため**実行者が実測して置換する。
これは逸脱ではなく手順であり `deviations` に書かない。**

---

## Task 1 (Phase A): 中継に使われている鍵を特定する

**Files:** Create: `tasks/T-2026-08-12-tunnel-key-audit-lecun/audit.md`

**秘密鍵の中身は絶対に出さない。指紋と経路名だけを記録する。**

- [ ] **Step 1: 中継の目印を集合として列挙し、中身が指す経路を読む**

    ls -a ~/ | grep -i tunnel; echo "count=$(ls -a ~/ | grep -c -i tunnel)"
    for f in ~/.tunnel_to_*; do
      test -f "${f}" && echo "FILE ${f} size=$(wc -c < "${f}")" && echo "POINTS_TO=$(cat "${f}")"
    done

目印の中身は**秘密鍵そのものではなく、その経路**である（実装のコメントによる）。
経路を記録し、**中身は読まない。**

- [ ] **Step 2: その鍵が実在するか、種別と指紋を測る**

上で得た経路を `KEY` に入れる。

    ls -la "${KEY}" 2>/dev/null || echo "鍵が実在しない"
    ls -la "${KEY}.pub" 2>/dev/null || echo "公開鍵の並置なし"
    ssh-keygen -lf "${KEY}.pub" 2>/dev/null || ssh-keygen -yf "${KEY}" < /dev/null 2>&1 | head -1

**指紋（`SHA256:` で始まる値）は公開鍵の要約であり秘匿ではない。記録してよい。**
`-----BEGIN` で始まる行は**絶対に出さない。**

- [ ] **Step 3: 手元にある鍵を集合として列挙する**

    ls -la ~/.ssh/ 2>/dev/null
    for f in ~/.ssh/*; do
      case "${f}" in
        *.pub) ssh-keygen -lf "${f}" 2>/dev/null && echo "  ^ ${f}" ;;
      esac
    done

**特定の名前を探さない。** 見つかった公開鍵すべての指紋を記録する。

- [ ] **Step 4: 秘匿が混ざっていないことを確かめる**

    grep -c -i -E "BEGIN [A-Z ]*PRIVATE|api[_-]?key|password|passphrase|secret" tasks/T-2026-08-12-tunnel-key-audit-lecun/audit.md

Expected: **鍵の中身に由来する一致が零。** 名前や説明文に語が現れるのは差し支えない。
**値の混入と名前の一致を分けて判定する。** 一致があれば一件ずつ実体を確かめ、
値であれば削り、名前であればその旨を記す。

**陽性対照**: 囮の行（`-----BEGIN OPENSSH PRIVATE KEY-----`）を含む一時ファイルに
同じ検査をかけ、**一以上を返すこと**を確かめる。囮は外部へ送らない。

| # | 完了判定 |
|---|---|
| 1 | 中継の目印を集合として列挙した（件数と経路） |
| 2 | 鍵の実在と指紋を測った（指紋のみ。中身なし） |
| 3 | 手元の公開鍵を集合として列挙した（件数と指紋） |
| 4 | 記録に鍵の値が含まれない（値と名前を分けて判定） |

---

## Task 2 (Phase A): 自ホストが受け入れる側として何を登録しているか

**Files:** Modify: `tasks/T-2026-08-12-tunnel-key-audit-lecun/audit.md`

**ここが決定的である。** 自ホストが中心になれるかは、**他ノードの鍵を受け入れるか**で決まる。

- [ ] **Step 1: 受け入れの一覧を集合として探す**

    for f in ~/.ssh/authorized_keys ~/.ssh/authorized_keys2; do
      test -f "${f}" && echo "FILE ${f} lines=$(grep -c -v '^\s*$' "${f}")"
    done
    ls -la ~/.ssh/authorized_keys* 2>/dev/null || echo "受け入れの一覧なし"

**零件でも「無い」と結論しない。** 別の場所を指す設定がありうる。

    grep -i -E "AuthorizedKeysFile|Port|PermitRootLogin" /etc/ssh/sshd_config 2>/dev/null \
      || echo "設定を読めない（権限または不在）"

- [ ] **Step 2: 登録されている鍵の指紋を列挙する**

    ssh-keygen -lf ~/.ssh/authorized_keys 2>/dev/null | tee /tmp/authfp.txt
    echo "count=$(wc -l < /tmp/authfp.txt)"

**指紋のみ。鍵の本体は出さない。**

- [ ] **Step 3: 中継の鍵が自ホストに登録されているかを照合する**

Task 1 Step 2 の指紋を `FP` に入れる。

    grep -c -F "${FP}" /tmp/authfp.txt

**これが `1` 以上なら、この鍵を持つノードは自ホストへ入れる。** すなわち
**自ホストは中心になれる。** `0` なら、中心にするには登録の追加が要る。

**陽性対照**: `/tmp/authfp.txt` に実在する別の指紋で同じ照合を行い、**一を返すこと**を
確かめる。**照合が常に零を返す壊れ方をしていないことを示す。**

- [ ] **Step 4: 自ホストが外からどの住所で見えるかを測る**

    ip -4 addr show 2>/dev/null | grep -E "inet " || cat /proc/net/fib_trie 2>/dev/null | grep -A1 "32 host" | head -20
    grep -v "^#" /etc/hosts | grep -v "^$"

前契約で、自ホストは容器の内側の住所を持ち、他ノードは別の帯にあることが分かっている。
**自ホストが他ノードからどの住所で見えるかは自分では測りきれない。** 測れた範囲を記し、
測れない部分は `UNKNOWN` とする。

| # | 完了判定 |
|---|---|
| 5 | 受け入れの一覧を集合として探した（場所と行数） |
| 6 | 登録されている指紋を列挙した（件数） |
| 7 | 中継の鍵が自ホストに登録されているかを照合した（値と陽性対照） |
| 8 | 自ホストの住所を測った（測れない部分は UNKNOWN） |

---

## Task 3 (Phase B): 他の九台へ実際に認証が通るかを測る

**Files:** Modify: `tasks/T-2026-08-12-tunnel-key-audit-lecun/audit.md`

**口が開いていることと、鍵が通ることは別である。** 前契約で口は測った。ここは認証を測る。

- [ ] **Step 1: 対象の一覧を三つの出所から集める**

    grep -i -E "^Host |HostName|Port|IdentityFile" ~/.ssh/config 2>/dev/null
    echo "ssh_count=$(grep -c -i '^Host ' ~/.ssh/config 2>/dev/null || echo 0)"
    grep -v "^#" /etc/hosts | grep -v "^$"
    grep -o "tcp://[0-9.]*:[0-9]*" ~/.local/state/syncthing/config.xml 2>/dev/null | sort -u

**三つの和集合を対象とし件数を必ず記録する。** 既知の構成は十一台である。
**それより少なければ一覧が縮んでいる可能性を明記する。**

- [ ] **Step 2: 認証を測る。実行する命令は `echo` だけである**

対象ごとに次を実行する。**`ConnectTimeout` と `BatchMode` を必ず付ける**
（対話的な問い合わせで止まらないようにするため）。

    ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new \
        -p 50072 -i "${KEY}" <addr> 'echo REACHABLE' 2>&1 | tail -2

**結果を一件ずつファイルへ書き、あとで別命令で表示する。**
判定は次の三つに分ける。

| 結果 | 意味 |
|---|---|
| `REACHABLE` が返る | **認証が通る。中継を張れる** |
| `Permission denied` 等 | 口は開いているが**鍵が通らない**。登録の追加が要る |
| 接続そのものが失敗 | 経路または口の問題（前契約の結果と突き合わせる） |

- [ ] **Step 3: 三分類で集計し、合計が対象数と一致することを確かめる**

    echo "AUTH_OK=$(grep -c 'REACHABLE' /tmp/auth.txt)"
    echo "DENIED=$(grep -c -i 'denied\|publickey' /tmp/auth.txt)"
    echo "NOCONN=$(grep -c -i 'refused\|no route\|timed out\|timeout' /tmp/auth.txt)"
    echo "total_lines=$(wc -l < /tmp/auth.txt)"

**一致しなければ分類から漏れている。** 漏れた行を実物で確かめて分類を足す。

- [ ] **Step 4: 陽性対照。** 通らないはずの鍵を、到達できた住所へ与える。

    ssh -o BatchMode=yes -o ConnectTimeout=8 -p 50072 -i /dev/null <到達できた住所> 'echo REACHABLE' 2>&1 | tail -1

Expected: **`REACHABLE` が返らない。** 返るなら鍵が効いていないか測定が壊れている。
**停止して報告する（G2）。**

| # | 完了判定 |
|---|---|
| 9 | 対象一覧を三つの出所から集め件数を記録した |
| 10 | 全対象で認証を測り合計が一致した |
| 11 | 認証の可否と接続の可否を区別した（三分類） |
| 12 | 通らないはずの鍵で通らないことを確かめた（陽性対照） |

---

## Task 4 (Phase C): 全項目を検証し、報告する

**Files:** Create: `tasks/T-2026-08-12-tunnel-key-audit-lecun/RESULT.md`, `tasks/T-2026-08-12-tunnel-key-audit-lecun/result.yaml`,
`tasks/inbox.d/T-2026-08-12-tunnel-key-audit-lecun.md`

- [ ] **Step 1: 完了判定 12 項目を一つの表にまとめ、各項目に実測値または `UNKNOWN` を記す。**
**「実施した」ではなく「何が出たか」を書く。**

- [ ] **Step 2: `conventions_rev` を実測して置換する。** 逸脱ではなく手順である。

    git --no-pager log -1 --format=%h -- context/conventions.md

- [ ] **Step 3: 検証を通す。** `make` 経由の終了コードはレシピ失敗時に `2` になる。

    make task-validate TASK=T-2026-08-12-tunnel-key-audit-lecun; echo "validate_exit=$?"
    make task-preflight TASK=T-2026-08-12-tunnel-key-audit-lecun; echo "preflight_exit=$?"

**`P9` の `host_mismatch` は既知の偽陽性である。** 切り分けを繰り返さない。

- [ ] **Step 4: 判断の受け皿へ置く。** `tasks/inbox.d/T-2026-08-12-tunnel-key-audit-lecun.md` に
**起票者が次の判断に使える事実だけ**を置く。**中心をどこにするかの提案は書かない。**

- [ ] **Step 5: 変更が契約の範囲に限られること、未解決が無いことを行数で確かめる**

    make forbidden-check; echo "exit=$?"
    git --no-pager status --porcelain > /tmp/wt.txt; wc -l /tmp/wt.txt; cat /tmp/wt.txt
    git --no-pager diff --name-only --diff-filter=U > /tmp/un.txt
    echo "unmerged=$(wc -l < /tmp/un.txt)"; cat /tmp/un.txt

**契約の範囲外の未追跡物があった場合**、前契約では抽出物を別 commit にする判断が
採られた。同じ状況なら**同じ扱いでよい。判断と理由を報告に記す。**

- [ ] **Step 6: 送信前の自己検査（道具の欠陥を避ける）**

    .venv/bin/python - <<'PY'
    import pathlib, re
    for f in ["RESULT.md", "result.yaml", "audit.md"]:
        p = pathlib.Path("tasks/T-2026-08-12-tunnel-key-audit-lecun") / f
        if not p.exists(): continue
        s = p.read_text(encoding="utf-8")
        print("%s bmp_over=%d hex40=%d" % (f, sum(1 for c in s if ord(c) > 0xFFFF),
              len(re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])", s))))
    PY

**両方が零になるまで直してから送る。** 零でないまま送ると停止するか拒否される。

- [ ] **Step 7: commit する**

    git add tasks/T-2026-08-12-tunnel-key-audit-lecun/ tasks/inbox.d/T-2026-08-12-tunnel-key-audit-lecun.md
    git commit -m "docs(sync): audit tunnel key distribution on lecun"
    git --no-pager log -1 --format='%h %s'

- [ ] **Step 8: 抑止を解除する（削除ではなく移動）**

    mv .sync-pause /tmp/.sync-pause.released.T-2026-08-12-tunnel-key-audit-lecun 2>/dev/null \
      && echo "released" || echo "解除に失敗。手当てが要る"
    ls -la .sync-pause 2>/dev/null && echo "まだ残っている" || echo "repo 直下から消えた"

- [ ] **Step 9: 報告を台帳へ返す**

    make task-report TASK=T-2026-08-12-tunnel-key-audit-lecun; echo "exit=$?"

| # | 完了判定 |
|---|---|
| 13 | 12 項目すべてに実測値または UNKNOWN がある（空欄なし） |
| 14 | 送信前の自己検査が両方とも零 |
| 15 | 作業ツリーの変更が契約の範囲に限られる（一覧を記載） |
| 16 | 抑止が repo 直下から消えている |
| 17 | 報告が台帳へ返っている（終了コード） |

---

## 想定外が起きたときの扱い

| 事象 | 対応 |
|---|---|
| 陽性対照が期待どおりでない | **停止して報告**（G1 / G2）。測定系が信用できない |
| 通らないはずの鍵で認証が通った | **停止して報告**。鍵が効いていないか測定が壊れている |
| 中継の目印または鍵が無い | 記録して続行。**作らない。生成しない** |
| 受け入れの一覧が読めない | 権限か不在かを区別して記録。`UNKNOWN` とする |
| 対話的な問い合わせが出た | **応答しない。** `BatchMode` を確かめ、それでも出るなら中断して記録する |
| 認証が全対象で通った | 記録する。**候補が複数あるということであり、異常ではない** |
| 変更しなければ測れない項目が生じた | **測らずに `UNKNOWN` とする。** 読み取り専用である |
| 抑止の解除に失敗した | 残っている場所を報告に明記する。自動で再試行しない |

**言い訳をしない。事実と、測れなかったことを書く。**

# audit — 手続きの証跡（T-2026-09-21-philip-sync-outbound-off）

実行ホスト: 中心（同期処理上の名前 `philip`）。OS の `hostname` は `aolab`。
repo: `~/slocal2/m2`。版: `v2.1.3`（画面の経路 `GET /rest/system/version` で実測）。

秘匿の扱い: 画面の鍵は変数へ読み込むだけで、出力にも記録にも残していない。
相手の識別子は先頭 7 文字までに切り詰めた。公開側の住所は末尾を伏せた。

---

## 1. 実行ホストの同定（契約の宣言と OS 名が食い違うため）

`P9 spec_lint` が `host_mismatch` を出した。**宣言 `philip` に対し `socket.gethostname()` は `aolab`。**

| 確かめたこと | 実測 |
|---|---|
| 自機の識別子 `GET /rest/system/status` の `myID` | `3J4TRX4…` |
| その識別子の登録名（`config.xml` の `<device>`） | **`philip`** |
| 接続中の相手 `GET /rest/system/connections` | **6 件**（andrew / bengio / dlsta / efros / ilya / lecun） |
| repo の位置 | `/home/ubuntu/slocal2/m2`（`context/env-facts.md` の philip の位置と一致） |
| 自機の住所 | `172.17.0.13`（容器の内側。外側の `192.168.196.150` は見えない） |

**自機は中心 philip である。** `host_mismatch` は検査が OS 名を見ているための誤検出であり、
この repo の「ホスト」は同期処理上の名前である。**契約の誤りではなく検査の誤りとして扱う。**

## 2. 稼働しているものと接続の状態（変更前）

プロセスは `/proc/PID/exe` の実体で絞った（部分一致は実行基盤の包み込みを拾うため）。
件数は `grep -c` で数えた（終了コードを件数と呼ばない）。

    pid=122452 exe=/home/ubuntu/bin/syncthing   起動 2026-08-23 22:29:04
    pid=122530 exe=/home/ubuntu/bin/syncthing   起動 2026-08-23 22:29:18
    件数 = 2

稼働時間 `uptime` = 2,501,884 秒（約 28.9 日）。接続は 6 件すべて `tcp-server`、
相手側住所はいずれも `127.0.0.1:<高位番号>`（星型の中継を経由しており、公開経路は使っていない）。

共有フォルダの定義は 2 件（`claude-sync` → `/home/ubuntu/claude-sync`、`m2` → `/home/ubuntu/slocal2/m2`）。
登録されている相手は 7 件（自分を含む）。

変更前の全体は repo の外へ控えた。**版管理へは置かない**（画面の鍵を含みうるため）。

    /home/ubuntu/task-backups/T-2026-09-21-philip-sync-outbound-off/before.json   19,074 bytes

控えへの秘匿の混入は形で検査した（値は出力していない）: `apikey` の語 = 0 件、
`BEGIN .* PRIVATE KEY` = 0 件。

## 3. 記録から拾った外向きの通信（変更前）

記録: `~/.syncthing.log`、244,194,818 bytes / 819,933 行。
範囲は 2026-08-23 22:29:04 〜 2026-09-21 21:22:56。**途中で版が上がっている**
（`v1.27.10` で起動 → 自動更新で `v2.1.3` へ → 以後 v2 の様式）。

種類ごとの件数（完全一致の語を `grep -c` で数えた）。

| # | 種類 | 件数 | 記録の行 | 宛先 |
|---|---|---|---|---|
| 1 | STUN で外側の住所を解決 | **1** | 31 | `stun.voipstunt.com:3478`（公開） |
| 2 | STUN で NAT の種別を判定 | **1** | 30 | 同上（`type="Port restricted NAT"`） |
| 3 | 使用状況の送信 | **2** | 759194, 817681 | `https://data.syncthing.net/newdata`（公開） |
| 4 | 版の確認（自動更新） | **1** | 2 | `https://upgrades.syncthing.net/meta.json`（公開） |
| 5 | 端口の自動開放（UPnP/NAT-PMP）の探索 | **1** | 29 | `count=0`（見つからず。公開へは出ていない） |
| 6 | 局所の告知 | 2 | 12, 13 | IPv4 broadcast / IPv6 multicast。**外向きではない** |
| — | 公開中継への参加 | **0** | — | `Joined relay` / `relay://` とも 0 件 |

該当行（抜粋。公開側の住所は末尾を伏せた）:

    29:2026-08-23 22:29:38 INF Detected NAT services (count=0 log.pkg=nat)
    30:2026-08-23 22:29:48 INF Detected NAT type (uri=quic://0.0.0.0:22000 type="Port restricted NAT" log.pkg=connections)
    31:2026-08-23 22:29:48 INF Resolved external address (uri=quic://0.0.0.0:22000 address=quic://131.113.39.x:62442 via=stun.voipstunt.com:3478 log.pkg=connections)
    759194:2026-09-20 17:32:36 INF Sent usage report (version=3 log.pkg=ur)
    817681:2026-09-21 17:32:38 INF Sent usage report (version=3 log.pkg=ur)

**中心でも起きている。** 契約は dlsta の実測を根拠に立っているが、STUN は中心でも起動時に出ていた。

### 3.1 STUN の産物は今も状態に残っている

`GET /rest/system/status` の `connectionServiceStatus`:

    "quic://0.0.0.0:22000": wanAddresses = ["quic://0.0.0.0:22000", "quic://131.113.39.x:62442"]
    "tcp://0.0.0.0:22000" : wanAddresses = ["tcp://0.0.0.0:0", "tcp://0.0.0.0:22000"]

**公開側の住所は STUN でしか得られない。** これが変更前の陽性対照になる。

### 3.2 使用状況の送信は前契約の最中に有効化されている（原因は UNKNOWN）

| 時点 | 出所 | `urAccepted` |
|---|---|---|
| 2026-08-23 22:41 | `~/task-hold/T-2026-09-17-philip-accept-efros/backup/config.xml.orig` | `0` |
| 2026-08-23 22:29（v1→v2 移行時の控え） | `~/.local/state/syncthing/config.xml.v37` | `0` |
| 2026-09-17 05:07 | `~/task-backups/T-2026-09-20-philip-accept-dlsta/config.xml.orig` | `0` |
| 2026-09-20 17:32:39（現行） | `~/.local/state/syncthing/config.xml` | **`3`** |

初回の送信は `2026-09-20 17:32:36`、設定ファイルの更新は `17:32:39`。
**28 日間 0 件だったものが、この時刻から日次 1 件になった。**

前契約 `T-2026-09-20-philip-accept-dlsta` の証跡に残る経路は
`POST /rest/config/devices` と `PATCH /rest/config/folders/{claude-sync,m2}` だけで、
**`options` を変える経路は無い。** したがって**誰が `0` から `3` へ変えたかは UNKNOWN。**
事実として有効であることだけを扱い、推測で原因を書かない。

## 4. 外向きの通信を決める設定の特定（実装から）

実体 `/home/ubuntu/bin/syncthing`（27,045,912 bytes）を読んだ。記号表は除去されているため、
`.gopclntab` を解析して関数の配置を求め、`objdump` で逆アセンブルした。
関数の基点は `.text` の VMA + `0x40`（`RequiresRestartOnly` の大きさ 384 と実際の関数境界が
一致することで確定した）。設定項目の offset は Go の型情報（`structField.Offset`）から直接読んだ。

### 4.1 STUN — `IsStunDisabled()`

`github.com/syncthing/syncthing/lib/config.OptionsConfiguration.IsStunDisabled`（64 bytes）:

    cmpq $0x0,0x1b8(%rsp)   ; 受け手は rsp+8 → 構造体 offset 0x1b0
    jle  → 真（無効）
    cmpq $0x0,0x1b0(%rsp)   ; → 構造体 offset 0x1a8
    jg   → 論理値へ
    mov  $0x1,%ecx          ; 真（無効）
    movzbl 0x81(%rsp),%ecx  ; → 構造体 offset 0x79
    xor  $0x1,%ecx          ; 否定を返す

型情報から読んだ offset:

| 参照位置 | 構造体 offset | 項目 |
|---|---|---|
| `0x1b8(%rsp)` | 432 (`0x1b0`) | `StunKeepaliveMinS` |
| `0x1b0(%rsp)` | 424 (`0x1a8`) | `StunKeepaliveStartS` |
| `0x81(%rsp)` | 121 (`0x79`) | `NATEnabled` |

すなわち **`IsStunDisabled() = (stunKeepaliveMinS < 1) || (stunKeepaliveStartS < 1) || !natEnabled`。**
**三つのいずれか一つで STUN は止まる。**

この判定は `lib/stun.(*Service).Serve` に埋め込まれている。同関数は設定構造体を
`0x2d8(%rsp)` へ複写したうえで、**同じ三つを同じ順序で**比較する（2 箇所。周回と設定変更時）:

    259db0f: cmpq $0x0,0x488(%rsp)   ; 0x2d8+0x1b0 = stunKeepaliveMinS
    259db1e: cmpq $0x0,0x480(%rsp)   ; 0x2d8+0x1a8 = stunKeepaliveStartS
    259db2d: cmpb $0x0,0x351(%rsp)   ; 0x2d8+0x79  = natEnabled

**無効のときの分岐先は `time.(*Timer).Reset(1 秒)` を呼んで周回へ戻るだけである**（0x259de05）。
**既に得た外側の住所を消す処理は無い。** 3.1 の `wanAddresses` は変更後も残りうる。

### 4.2 使用状況の送信 — `urAccepted`

`lib/ur.(*Service).Serve` は設定構造体を `0x7c0(%rsp)` へ複写し、

    268fedb: cmpq $0x2,0x858(%rsp)   ; 0x7c0+0x98 = urAccepted（offset 152）
    268fee4: jl   → 送らない
    268ff02: call 0x268f7a0          ; = lib/ur.(*Service).sendUsageReport

すなわち **`urAccepted >= 3` のとき送る。** 記録の `Sent usage report (version=3)` と整合する。
画面の公式文言: 「The encrypted usage report is sent daily.」（日次）。

### 4.3 版の確認 — `autoUpgradeIntervalH`

`OptionsConfiguration.AutoUpgradeEnabled`（32 bytes）:

    cmpq $0x0,0xe0(%rsp)    ; 構造体 offset 216 = AutoUpgradeIntervalH
    setg %al

**`autoUpgradeIntervalH > 0` のときだけ有効。現在 `0` なので既に無効。**
記録でも `Upgrade available` は v1.27.10 の起動時（`autoUpgradeIntervalH=12` だった頃）の 1 件だけで、
v2 になって以後 29 日間 0 件である。**確認だけが走る、ということは起きていない。**

### 4.4 障害報告 — `crashReportingEnabled`

型情報上の名前は `CREnabled`（offset 416）。宛先 `crashReportingURL = https://crash.syncthing.net/newcrash`。
画面の公式文言:「Syncthing now supports automatically reporting crashes to the developers.
This feature is enabled by default.」**既定で有効。** 現在も `true`。

**記録に送信の痕跡は 0 件**（障害が起きていないため）。`lib/ur.(*failureHandler)` が担う。
**`CREnabled` を直接読む判定の位置は特定できなかった → その点は UNKNOWN。**
ただし項目名・既定値・宛先・担当は上記のとおり確定している。

### 4.5 端口の自動開放（UPnP / NAT-PMP）

画面の公式文言で `natEnabled` の呼び名は **「Enable NAT traversal」**。
記録は `Detected NAT services (count=0 log.pkg=nat)` の 1 件で、**装置が見つかっていない**。
探索は LAN の multicast と gateway 宛であり、**公開の宛先へは出ていない**。

**`lib/nat.(*Service).Serve` の中に `natEnabled` を読む判定は見つけられなかった → UNKNOWN。**
`natEnabled` を落とすと STUN が止まることは 4.1 で確定しているが、
**UPnP 側も同時に止まるかは実装から確かめられていない。**

### 4.6 読み取れなかったもの（UNKNOWN）

| 事項 | 状態 |
|---|---|
| `urAccepted` が `0` から `3` へ変わった原因 | **UNKNOWN**（3.2） |
| `crashReportingEnabled` を読む判定の位置 | **UNKNOWN**（4.4） |
| `natEnabled` が UPnP/NAT-PMP も止めるか | **UNKNOWN**（4.5） |

**いずれも推測で書かない。** 変更するのは根拠の取れた項目だけにする。

## 5. 再起動が要るか（禁止 1 に触れないための事前確認）

Syncthing は構造体タグ `restart:"true"` の付いた項目だけを再起動の対象にする
（`OptionsConfiguration.RequiresRestartOnly`）。型情報からタグを読んだ:

| 項目 | タグ | 再起動 |
|---|---|---|
| `natEnabled` | `json:"natEnabled" xml:"natEnabled" default:"true"` | **不要** |
| `stunKeepaliveStartS` | `… default:"180"` | **不要** |
| `stunKeepaliveMinS` | `… default:"20"` | **不要** |
| `urAccepted` | `json:"urAccepted" xml:"urAccepted"` | **不要** |
| `crashReportingEnabled` | `… default:"true"` | **不要** |
| `autoUpgradeIntervalH` | `… default:"12"` | **不要** |
| `localAnnounceEnabled` | `… default:"true"` | **不要** |

**どれにも `restart:"true"` が無い。** 変更しても再起動を求められない見込み。
実際に求められたら**停止して判断を仰ぐ**（`GET /rest/config/restart-required` で確かめる）。

## 6. 変更前の値と戻し方

変更前（`GET /rest/config/options` と `config.xml` で一致を確認済み）:

| 項目 | 変更前 | 外向きか |
|---|---|---|
| `globalAnnounceEnabled` | `false` | 既に無効 |
| `relaysEnabled` | `false` | 既に無効 |
| `localAnnounceEnabled` | `true` | **外向きではない。禁止 3 により触れない** |
| `natEnabled` | **`true`** | **STUN が動く** |
| `stunKeepaliveStartS` | `180` | STUN の周期 |
| `stunKeepaliveMinS` | `20` | STUN の周期の下限 |
| `urAccepted` | **`3`** | **日次で公開へ送る** |
| `urSeen` | `3` | 表示済みの版。通信はしない |
| `crashReportingEnabled` | **`true`** | 障害時に公開へ送る |
| `autoUpgradeIntervalH` | `0` | 既に無効 |

**戻し方（実行しない。記録だけ）** — 画面の経路で、戻す項目だけを送る:

    # 1) 値を戻す（PATCH は与えた鍵だけを変える）
    PATCH /rest/config/options   {"natEnabled": true}
    PATCH /rest/config/options   {"urAccepted": 3}
    PATCH /rest/config/options   {"crashReportingEnabled": true}

    # 2) 反映を確かめる
    GET /rest/config/options            → 上の 3 項目が元の値
    grep -o '<natEnabled>[^<]*' ~/.local/state/syncthing/config.xml

    # 3) 最後の手段（稼働中は効かない）
    # 控え /home/ubuntu/task-backups/T-2026-09-21-philip-sync-outbound-off/before.json に
    # 変更前の options 全体が入っている。**設定ファイルの直接復元は行わない。**
    # 稼働中の処理が書き戻すため効かない（前契約で実測済み）。

## 7. 「止まったこと」を測れるか（測定の器を先に検証する）

**この節は Phase B の実測を受けて書き直した。** 変更前に書いた見立て（「記録では確かめられない」）は
**誤りだった。** 実測を正とする（`conventions#issuer_cautions` 注意 1）。

### 7.1 使えなかった手段

| 手段 | 使えるか |
|---|---|
| `tcpdump` / `ss` / `lsof` / `conntrack` | **いずれも無い。** 通信そのものは観測できない |
| `/proc/net/nf_conntrack` | **存在しない**（容器の中） |
| `/rest/system/debug`（周回中の詳細記録の切り替え） | **404。v2.1.3 には無い** |
| `STTRACE` による詳細記録 | **再起動が要る。禁止 1 により採らない** |

### 7.2 変更前に立てた見立て（**誤りだった**）

STUN の keepalive は詳細記録の水準でしか出ない（`%s stun keepalive on %s: %s (%v)`）。
通常の記録に出るのは外側の住所が変わったときだけ（`Resolved external address`）で、
変更前は 29 日間に 1 件（起動時）しかなかった。
**そこから「周期を越えて待って新しい行が無いことは証拠にならない」と見立てた。**

**この見立ては、遷移そのものが記録されることを見落としていた。**

### 7.3 実際には遷移が記録される（実装で確認）

`lib/stun.(*Service).Serve` の無効側の分岐（`0x259d97d`）は、

    0x259d998: lea …  # 0x1281f8c    ; 文言の先頭
    0x259d99f: mov $0xd,%r8d          ; 長さ 13 = "STUN disabled"
    0x259d9ae: call 0x1f32de0         ; 記録器へ
    0x259d9c0: call 0x259f400         ; = lib/stun.(*Service).setNATType

**`STUN disabled` を通常の水準で記録し、続けて NAT の種別を戻す。**
実体に `STUN disabled` の文字列は 1 件あり、実測された行と一致する。

**したがって「止まったこと」は記録で直接確かめられる。** 7.2 の見立ては取り消す。

---

## 8. Phase B — 変更と確認

### 8.1 変更直前の基準点（2026-09-22 09:02:55 UTC）

    記録の行数 = 827,152 / 246,341,716 bytes
    natEnabled=True  urAccepted=3  crashReportingEnabled=True
    stunKeepaliveStartS=180  stunKeepaliveMinS=20  autoUpgradeIntervalH=0
    globalAnnounceEnabled=False  relaysEnabled=False  localAnnounceEnabled=True
    接続中=6  相手の登録=7  共有フォルダ=2  requiresRestart=False
    wanAddresses quic://0.0.0.0:22000 = ["quic://0.0.0.0:22000", "quic://131.113.39.x:62442"]

### 8.2 送った操作（変える鍵だけを送る）

| 操作 | 本体 | 結果 |
|---|---|---|
| `PATCH /rest/config/options` | `{"natEnabled": false}` | **200** |
| `PATCH /rest/config/options` | `{"urAccepted": -1}` | **200** |
| `PATCH /rest/config/options` | `{"crashReportingEnabled": false}` | **200** |
| `GET /rest/config/restart-required` | — | **200** `{"requiresRestart": false}` |

**再起動は求められなかった。** 5 節で型情報から読んだとおりである（禁止 1 に触れていない）。

### 8.3 反映の確認（二つの経路で）

**画面の経路の読み戻し** — 変更前の 55 項目すべてと比較した。

    natEnabled              True → False
    urAccepted              3    → -1
    crashReportingEnabled   True → False
    変わった項目数 = 3   増えた項目 = なし

**設定ファイル** `~/.local/state/syncthing/config.xml`（mtime 2026-09-22 09:03:20）:

    natEnabled            = false      urAccepted           = -1
    crashReportingEnabled = false      localAnnounceEnabled = true
    globalAnnounceEnabled = false      relaysEnabled        = false
    stunKeepaliveStartS   = 180        stunKeepaliveMinS    = 20
    autoUpgradeIntervalH  = 0

**送った 3 項目だけが変わり、設定ファイルにも書き戻された。**
`stunKeepaliveStartS` / `stunKeepaliveMinS` は**触っていない**（`natEnabled` だけで判定は真になるため、
変える項目を最小にした）。

### 8.4 既存が無傷であること

| 確認 | 変更前 | 変更後 | 判定 |
|---|---|---|---|
| 六ノードとの接続 | 6 | **6**（andrew / bengio / dlsta / efros / ilya / lecun すべて `connected=True`） | **無傷** |
| 相手の登録 | 7 件 | **7 件。識別子と名前の対応が完全一致** | **無傷** |
| 共有フォルダ | 2 件 | **2 件**（`claude-sync` / `m2`、いずれも相手 7 件） | **無傷** |
| 局所の告知 | `true` | **`true`** | **無傷**（禁止 3） |
| 同期処理 | 2 件 pid=122452,122530 | **2 件 pid=122452,122530** | **無傷**（PID 同一） |

### 8.5 STUN の産物は残った（実装どおり）

    変更直後 wanAddresses quic://0.0.0.0:22000 = ["quic://0.0.0.0:22000", "quic://131.113.39.x:62442"]

**消えていない。** 4.1 で読んだとおり、無効の分岐は `Timer.Reset(1 秒)` を呼んで周回へ戻るだけで、
**既に得た外側の住所を消す処理が無い。** 実装の読みが実測と一致した。
**したがって `wanAddresses` は「止まったこと」の指標にならない。** 変更前の陽性対照としてのみ使える。

### 8.6 止まったことの確認（周期を越えて待った）

周期は実装から読んだ値を使った（`stunKeepaliveStartS = 180` 秒）。**それを越えて 300 秒待った。**

    開始 UTC = 2026-09-22 09:04:36   記録の行数 = 827,152
    終了 UTC = 2026-09-22 09:09:36   記録の行数 = 827,339   増えた行数 = 187

増えた 187 行のうち、外向きに関わる語の件数（`grep -c`）:

| 語 | 件数 |
|---|---|
| `Resolved external address` | **0** |
| `Detected NAT type` | **0** |
| `Detected NAT services` | **0** |
| `Sent usage report` | **0** |
| `Upgrade available` | **0** |
| `Joined relay` | **0** |
| `stun` | **1** |

その 1 件が決め手である。

    2026-09-22 09:06:09 INF STUN disabled (log.pkg=stun)

**設定変更（09:03:20）から 169 秒後に、同期処理自身が STUN を無効にしたと記録した。**
169 秒は keepalive の周期 180 秒の内側であり、**待ちが明けた最初の周回で止まった**ことと整合する。

**これは不在による証拠ではなく、遷移そのものの記録である。**
7.3 のとおり、この行は無効側の分岐でだけ出る。

### 8.7 使用状況の送信は、まだ止まったと言えない

**周期が日次であり、セッションの中では越えられない。**

| 事実 | 値 |
|---|---|
| 直近の送信 | `2026-09-20 17:32:36` と `2026-09-21 17:32:38`（いずれも UTC） |
| 変更の時刻 | `2026-09-22 09:03:20` UTC |
| 次に送るはずだった時刻 | **`2026-09-22 17:32` 前後 UTC**（変更の約 8.5 時間後） |
| 待った時間 | 300 秒。**周期を越えていない** |

**したがって「止まった」とは書かない。UNKNOWN とする。**
判定の根拠は実装（4.2。`urAccepted >= 3` のときだけ送る）と読み戻しだけである。

確かめ方は申し送りへ置く。**2026-09-22 17:32 UTC を過ぎてから**次を見ること。

    grep -c 'Sent usage report' ~/.syncthing.log      # 変更時点で 2 件。増えていなければ止まっている

### 8.8 障害報告は元から痕跡が無い

記録に送信の痕跡は **0 件**（変更前も変更後も）。**障害が起きていないためである。**
契約の言う「痕跡が元から無かった場合、止まったとは言えない」に該当する。
**止まったとは書かない。** 設定が `false` になったことだけを事実として記録する。

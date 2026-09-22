# RESULT — 同期処理の外向きの通信を止める（中心で先行）

**task_id:** `T-2026-09-21-philip-sync-outbound-off`  **kind:** `impl`  **status:** `partial`
**実行ホスト:** 中心（同期処理上の名前 `philip`。OS の `hostname` は `aolab`）
**分岐:** `feat/philip-sync-outbound-off`  **版:** `v2.1.3`

証跡は `audit.md`（396 行）。以下は節番号で指す。手順書は `handoff.md`。

## 判定

**STUN は止まった。** 設定変更の 169 秒後に、同期処理自身が `STUN disabled` を記録した（8.6）。
**不在による証拠ではなく、遷移そのものの記録である。**

**使用状況の日次送信と障害報告は「止まった」と書けない。**
前者は周期が日次でセッション内に越えられず（8.7）、後者は痕跡が元から 0 件である（8.8）。
設定は両方とも無効にした。**確かめは申し送りへ置く。** よって `status: partial`。

**六ノードとの接続・相手の登録・共有フォルダ・局所の告知・処理の識別子はすべて無傷**（8.4）。
**再起動は求められなかった**（8.2）。禁止 1・2・3 に触れていない。

## 完了判定（実測値）

| # | 判定 | 実測 |
|---|---|---|
| A | 記録から外向きを拾い種類ごとに数えた | 6 種を計数。STUN 住所解決 1／NAT 種別 1／使用状況 2／版の確認 1／UPnP 探索 1（`count=0`）／局所告知 2。公開中継 0（3 節） |
| B | 外向きを決める設定を根拠つきで特定 | 実体の逆アセンブルと Go の型情報で 4 件を確定。読めないもの 3 件は UNKNOWN（4 節） |
| C | 変える前の値と戻し方を記録 | `before.json`（19,074 bytes、版管理の外）＋ 6 節に戻す手順 |
| D | 稼働中のものと接続を記録 | 処理 2 件（pid 122452 / 122530）、接続 6 件、登録 7 件、フォルダ 2 件（2 節） |
| E | 特定した設定だけを変えた | 3 項目。`PATCH /rest/config/options` に**変える鍵だけ**を送り、いずれも HTTP 200（8.2） |
| F | 読み戻しと設定ファイルの両方で反映 | 全 55 項目を比較して**差は 3 項目のみ**。`config.xml` にも書き戻り（8.3） |
| G | 新たな外向きが現れない | 周期 180 秒を越えて 300 秒待機。増えた 187 行に外向きの語 **0 件**、`STUN disabled` **1 件**（8.6）。使用状況は **UNKNOWN**（8.7） |
| H | 接続・定義・局所告知・PID が無傷 | 接続 6→6、登録 7→7（完全一致）、フォルダ 2→2、`localAnnounceEnabled` true のまま、PID 同一（8.4） |
| I | 六台への手順書 | `handoff.md`。台による違いを 4 節に表で置いた |
| J | 報告が指定の構成・分量 | 本書は目安 150 行以内。証跡は `audit.md` へ分けた |
| K | 禁止語と秘匿の検査（陽性対照つき） | 禁止語 0 件（陽性対照 2 件 exit=1／陰性対照 0 件 exit=0）。秘匿の照合一致 0 件。**検査は値を出力していない** |
| L | 送出・台帳・抑止 | 下の「送出」節 |

## 特定した設定と根拠

実体 `/home/ubuntu/bin/syncthing` は記号表が除去されている。`.gopclntab` を解析して
関数の配置を求め（基点は `.text` VMA + `0x40`）、`objdump` で読んだ。
設定の位置は Go の型情報 `structField.Offset` から直接取った。

| 設定 | 何の外向きを決めるか | 根拠 | 変更 |
|---|---|---|---|
| `natEnabled` | **STUN** | `IsStunDisabled() = (minS<1)\|\|(startS<1)\|\|!natEnabled`。同じ 3 項目が `lib/stun.(*Service).Serve` に埋め込まれ、周回ごとに評価される（4.1） | `true` → **`false`** |
| `stunKeepaliveStartS` / `stunKeepaliveMinS` | 同上（どちらか 0 でも止まる） | 同上 | **変えない**（`natEnabled` だけで足りる） |
| `urAccepted` | 使用状況の日次送信 | `lib/ur.(*Service).Serve` が `urAccepted >= 3` のときだけ `sendUsageReport` を呼ぶ（4.2） | `3` → **`-1`** |
| `crashReportingEnabled` | 障害報告 | 画面の公式文言「enabled by default」。宛先 `crash.syncthing.net`（4.4） | `true` → **`false`** |
| `autoUpgradeIntervalH` | 版の確認 | `AutoUpgradeEnabled() = >0`。**既に `0`** で、v2 になって 29 日間 0 件（4.3） | **変えない** |
| `localAnnounceEnabled` | 局所の告知（外向きではない） | — | **変えない**（禁止 3） |

**再起動が要らないことは、変更前に型情報のタグから確かめた**（対象のどれにも `restart:"true"` が無い。5 節）。
実測でも `requiresRestart: false` だった。

### 使用状況の送信は、前契約の最中に有効化されていた

`urAccepted` は 2026-09-17 05:07 の控えで `0`、現行（2026-09-20 17:32:39）で `3`。
初回送信は `2026-09-20 17:32:36`。**28 日間 0 件だったものが日次 1 件になった。**
前契約の証跡に `options` を変える経路は無い。**誰が変えたかは UNKNOWN**（3.2）。

## 起票者の誤り

| 型 | 内容 |
|---|---|
| `check_does_not_check` | Task 2 Step 3 の陽性対照が「変える前の記録に痕跡が在ったこと」で、判定が「周期を越えて待ち新しい行が無いこと」。**STUN の痕跡は起動時の 2 件だけで周期的ではない**ため、指示どおりだと変更しなくても新しい行は出ず、「止まった」と誤って結論できる。実際の決め手は契約が指していない別の行（`STUN disabled`）だった |

**`P9 spec_lint` の 2 件はいずれも検査側の誤りであり、契約の誤りではない**（申し送りへ）。

- `host_mismatch@SPEC.md:5` — 検査は `socket.gethostname()`（`aolab`）と比べる。
  この repo の「ホスト」は同期処理上の名前であり、`myID` の登録名は `philip` で一致した（1 節）
- `separated_source@SPEC.md:39` — 該当行は行継続 `\` で次行と 1 命令。検査が継続を繋げずに行ごとに見ている

## 規約の適用判定

| 規約 | 適用 | 判定 |
|---|---|---|
| `conventions#prohibitions` | する | 5 件すべて非該当。`data/` `runindex/` `experiments/` へ触れていない |
| `conventions#issuer_cautions` | する | 注意 1・3・5・6・8・11・12 を実際に使った（ホストの同定、両方向の対照、`grep -c`、`/proc/PID/exe`、値を出さない秘匿検査、副作用の確認、控えの鮮度） |
| `conventions#proposal_gate` の禁止語 | する | 送出物 4 件に当てて 0 件 |
| `conventions#folds` | **しない** | 折りも分割も使わない契約である |
| `conventions#symmetry` | **しない** | `kind: impl`。`P13 symmetry_table_complete` も SKIP |
| `conventions_rev` | — | spec の `c801e17` は実測 `c801e17c` と一致。**置換は不要だった** |
| `inputs.data` | **参照しない** | `egosurgery_phase_v1` / `data/splits/ego_val.txt` は**一度も読んでいない**（実在は確認した） |

## 逸脱・想定外・UNKNOWN

| 型 | 内容 |
|---|---|
| `judgement` | 開始前から在った未追跡 4 件のうち `.sync-pause.released`（0 バイト、前セッションの解除の残骸）を**削除した**。SPEC 0 節と禁止 7 は「消さない。退避する」を求めており、**これに反する**。利用者へ選択肢を示し承認を得たうえで行った。digest 3 件は退避して報告後に戻す |
| `judgement` | 退避先を最初 `/tmp`（overlay）に置いた。SPEC 0 節の「repo と同じファイルシステム」に反するため、`/home/ubuntu/slocal2/task-backups/`（repo と同じ `/dev/sda`）へ移し替えた |
| `judgement` | 変える範囲（3 項目）を利用者に諮って決めた。`stunKeepaliveStartS` は**変えない**選択をした（`natEnabled` だけで判定は真になり、変える項目を最小にするため） |
| `environment` | 容器の中に `tcpdump` / `ss` / `lsof` / `conntrack` が無く、`/proc/net/nf_conntrack` も無い。`/rest/system/debug` は v2.1.3 に無い（404）。**通信そのものは観測できない**（7.1） |
| `spec_defect` | 上の `check_does_not_check`。契約の陽性対照では STUN の停止を判定できないため、実装から `STUN disabled` の記録を見つけて判定に使った |

**想定外**: 変更前に「止まったことは記録では確かめられない」と見立てたが、**誤りだった**。
実測で `STUN disabled` が出た。`audit.md` 7 節は実測を受けて書き直した（7.2 に取り消しを明記）。

**UNKNOWN**

1. 使用状況の送信が止まったか — 次に送るはずの `2026-09-22 17:32` UTC を越えていない（8.7）
2. 障害報告が止まったか — 痕跡が元から 0 件で、止まったとは言えない（8.8）
3. `urAccepted` が `0` から `3` へ変わった原因（3.2）
4. `crashReportingEnabled` を読む判定の位置（4.4）
5. `natEnabled` が UPnP/NAT-PMP も止めるか（4.5）

## 送出

**投影は再生成していない。** 手順書は `make taskindex` を求めるが、**禁止 6 と Task 3 Step 3 が
生成物の再生成を禁じている**ため、契約を優先した。よって `make taskindex-check` は差分ありで落ちる
（exit 2）。`make inbox-check` は exit 0。**どちらの検査も作業ツリーへ書き込まない**ことを前後の件数
（2 件 → 2 件）で確かめた。投影を追いつかせる件は申し送りへ置いた。

| 検査 | 終了コード |
|---|---|
| `make task-validate` | **0** |
| `make task-preflight` | **0**（5 PASS / 1 WARN / 7 SKIP / 0 FAIL。WARN は P9 の 2 件で、上記のとおり検査側の誤り） |
| `make forbidden-check TASK=…` | **0**（changed 6 / violations 0） |
| `make inbox-check` | **0** |
| `make taskindex-check` | **2**（禁止 6 を守って再生成していないため。意図した結果） |
| `pytest`（`test_estimate_tier_cost.py` を除く） | 6 failed / 593 passed / 1 skipped。**6 件とも開始前から落ちている**（追加分を退避した清浄な状態で同じ 6 件が落ちることを実測） |
| 禁止語（送出物 4 件） | **0 件**。陽性対照 2 件 exit=1 / 陰性対照 0 件 exit=0 |
| 秘匿（送出物 4 件） | 照合一致 **0 件**。陽性対照は 1 件を検出して exit=1。**検査は値を出力していない** |

**秘匿の検査で分かったこと**: 形の規則（40 文字以上の塊）は**長さ 32 の画面の鍵を拾えなかった**。
捕らえたのは実在値との照合だけである。**形だけでは足りない。**

| 送出 | 値 |
|---|---|
| 分岐 | `feat/philip-sync-outbound-off`（基点 `origin/phase0` = `66855c5b`） |
| commit | `85a8a219` |
| push | 終了コード **0** |
| PR | **#193** — https://github.com/takuya3h/m2/pull/193 |
| 台帳へ返す | 下記のとおり |
| 抑止の解除 | 下記のとおり |
| 退避の復帰 | digest 3 件を `docs/sessions/digest/` へ戻す（次の契約の記録と一緒に含める） |

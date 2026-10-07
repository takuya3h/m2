# RESULT — 残る六台の外向き通信を中心から止める

**task_id:** `T-2026-09-21-fleet-sync-outbound-off`  **kind:** `impl`  **status:** `partial`
**実行ホスト:** 中心（同期処理上の名前 `philip`。OS の `hostname` は `aolab`）
**分岐:** `feat/fleet-sync-outbound-off`  **版:** 七台とも `v2.1.3`

証跡は `audit.md`。以下は節番号で指す。手順の正は前契約の `handoff.md`。
**時刻は JST**（記録の原文は UTC。JST = UTC + 9 時間）。

## 判定

**六台すべてで STUN は止まった。** 各台で変更の 20〜172 秒後に、同期処理自身が `STUN disabled` を
記録した。六台とも記録の全期間でこの 1 件だけで、時刻は変更の後である（5.1）。

**使用状況の日次送信と障害報告は「止まった」と書けない。** lecun は記録の始まりから毎日送っていたが、
次の送信予定（2026-10-08 06:06 JST ごろ）を越えていない。他の五台と障害報告は痕跡が元から 0 件（5.2, 5.3）。
設定はすべて無効にした。確かめは申し送りへ置く。よって `status: partial`。

**六台それぞれで、中心との接続・相手の登録・共有フォルダ・局所告知・処理の識別子は無傷。**
**中心から見て六ノードすべてが繋がったまま。** 再起動は不要だった（4 節）。

## 認証に使った鍵

**中心の手元の鍵 `~/.ssh/id_ed25519_aolab`（ED25519、`SHA256:6NnjKh1smLfcXIttfc13hhMZNludreWCkWuWcQa04H0`）。
転送に依存しない。** `SSH_AUTH_SOCK` を外し `IdentityAgent=none` で agent の経路を断ったうえで、
lecun が `Server accepts key … explicit` を返し exit 0（1.3）。転送の受け口は環境に在るが、指す先の
ソケットが存在せず使えない状態だった（1.2）。六台の別名はすべて `IdentitiesOnly yes` でこの鍵を指す（1.1）。

## 六台の結果

| ノード | 変更 | natEnabled | urAccepted | crashReporting | 変わった項目 | API / config.xml | 局所告知 | 接続・登録・共有 | 処理の識別子 | STUN disabled |
|---|---|---|---|---|---|---|---|---|---|---|
| lecun | 14:38:09 | true→false | **3**→-1 | true→false | 3 | 目標値 / 目標値 | true | 同一 | 同一 | +129 秒 |
| bengio | 14:38:42 | true→false | 0→-1 | true→false | 3 | 目標値 / 目標値 | true | 同一 | 同一 | +103 秒 |
| andrew | 14:39:23 | true→false | 0→-1 | true→false | 3 | 目標値 / 目標値 | true | 同一 | 同一 | +156 秒 |
| ilya | 14:39:38 | true→false | 0→-1 | true→false | 3 | 目標値 / 目標値 | true | 同一 | 同一 | +20 秒 |
| efros | 14:39:52 | true→false | 0→-1 | true→false | 3 | 目標値 / 目標値 | true | 同一 | 同一 | +172 秒 |
| dlsta | 14:40:06 | true→false | 0→-1 | true→false | 3 | 目標値 / 目標値 | true | 同一 | 同一 | +95 秒 |

- PATCH は 18 回すべて HTTP 200。既に目標値だった項目は無い。全 55 項目のうち変わったのは 3 項目だけ（4 節）。
- 中心の options は各台の変更後も変更前の控えと完全一致（禁止 5）。
- `globalAnnounceEnabled` / `relaysEnabled` は六台とも既に false、`autoUpgradeIntervalH` は既に 0（3.2）。

## 完了判定（実測値）

| # | 判定 | 実測 |
|---|---|---|
| A | 認証の鍵を特定 | 手元の `id_ed25519_aolab`、転送非依存（1 節） |
| B | 手順書を記録 | 3 項目・値・経路・確かめ方（2 節） |
| C | 現在値と接続を変えずに読んだ | 全 55 項目を repo の外へ控えた（3.2） |
| D | 版が中心と同じ | 六台とも `v2.1.3` |
| E | 手順書の項目だけを変えた | 上表。前後の値つき |
| F | 読み戻しと設定ファイル | 六台とも両方で目標値 |
| G | 接続・定義・局所告知・識別子が無傷 | 六台とも前後で同一 |
| H | 中心から六ノードが繋がったまま | 各台の変更直後に 6/6 |
| I | 止まったことの確認 | STUN は六台とも確認。使用状況（lecun）は UNKNOWN、他は痕跡が元から無い（5 節） |
| J | 報告の構成と分量 | 本書は 150 行以内。証跡は `audit.md` |
| K | 禁止語と秘匿の検査 | 下の「送出」節 |
| L | 送出・台帳・抑止 | 下の「送出」節 |

## 起票者の誤り

| 型 | 内容 |
|---|---|
| `self_contradiction` | SPEC 0 節が `touch .sync-pause` の後に `make task-start` を置く。`task_start.sh` は目印を自分で作り、**実行前から在る目印は失敗時の巻き戻しで消さない**。指示どおりだと取り込みが失敗したとき目印が残り、そのホストの同期が止まったままになる。手で置かず `task_start.sh` に任せた |
| `self_contradiction` | Task 3 Step 3 が「退避したものを戻す」とし、退避した digest を未追跡へ戻す。`tasks/README.md` は抽出物を**契約の記録と一緒に含めよ**と定め、未追跡のまま残すと自動統合が止まる。利用者の指示で規約に従い commit に含めた |

**`P9 spec_lint` の 2 件は検査側の誤りで、契約の誤りではない**（前契約の申し送りと同じ型）。

- `host_mismatch@SPEC.md:5` — 検査は OS 名 `aolab` と比べる。この repo の「ホスト」は同期処理上の名前 `philip`
- `separated_source@SPEC.md:37` — 該当行は行継続 `\` で次行と 1 命令

## 規約の適用判定

| 規約 | 適用 | 判定 |
|---|---|---|
| `conventions#prohibitions` | する | 5 件すべて非該当。`data/` `runindex/` `experiments/` に触れていない |
| `conventions#issuer_cautions` | する | ホストの同定（別名と OS 名の食い違いを記録）、両方向の対照、`grep -c`、値を出さない秘匿の扱い、副作用の確認（`known_hosts` の要約値） |
| `conventions#proposal_gate` の禁止語 | する | 送出物に当てた（送出節） |
| `conventions#folds` | **しない** | 折りも分割も使わない |
| `conventions#symmetry` | **しない** | `kind: impl`。P13 も SKIP |
| `conventions_rev` | — | spec の `c801e17` に対し実測は `073f9dc0`（2026-10-02）。差分は `proposal_gate` の exp 向け節・`det_groups`・`crossfit`・変更履歴で、注入する 2 節は無変更（0 節）。spec.yaml は書き換えず本書に記録した |
| `inputs.data` | **参照しない** | `egosurgery_phase_v1` / `data/splits/ego_val.txt` は一度も読んでいない |

## 逸脱・想定外・UNKNOWN

| 型 | 内容 |
|---|---|
| `environment` | 実行基盤（auto mode）が、ノードの画面の鍵を読む命令と最初の SSH を「資格情報の探索」として拒んだ。**迂回せず**、鍵を使う命令（現状の読み取り・六台の PATCH）は**利用者が `!` で実行**し、実行者は結果の照合だけをした（1.3, 3.2, 4 節） |
| `environment` | 利用者の全体設定 `~/.claude/settings.json` が末尾のカンマで JSON として壊れていた。利用者が直し、セッションを開き直した |
| `judgement` | digest 3 件を同一ファイルシステムへ退避し、規約と利用者の指示に従い本契約の commit に含めた（Task 3 の「戻す」と食い違う） |
| `judgement` | `.sync-pause` を手で置かなかった（SPEC 0 節と食い違う）。利用者の指示 |
| `judgement` | 生成物（投影・集約結果）を再生成していない。手順書は `make taskindex` を求めるが禁止 7 を優先した |
| `judgement` | `conventions_rev` を spec.yaml へ置換せず、実測値を本書に記録した |

**想定外**: lecun の `urAccepted` が 3 で、記録の始まりから 44 日分を毎日送っていた（5.2）。
ilya と dlsta は OS 名が別名と違う（`aolab` / `4f3861ae8d3b`。住所は SPEC と一致、3.1）。

**UNKNOWN**

1. lecun の使用状況の送信が止まったか — 次の予定 2026-10-08 06:06 JST ごろを越えていない
2. 障害報告が止まったか — 六台とも痕跡が元から 0 件
3. lecun の `urAccepted` が 3 だった経緯
4. 他の五台の使用状況 — 元から送っていない（`urAccepted` 0）ため、止まったとは書けない

## 送出

**生成物は再生成していない**（禁止 7）。よって `make inbox-check` と `make taskindex-check` は差分ありで落ちる
（どちらも exit 2）。検査の前後で作業ツリーの件数は 7 → 7 で、書き込みは無い。

| 検査 | 結果 |
|---|---|
| `make task-validate` | OK（0 failed） |
| `make task-preflight` | exit 0（5 PASS / 1 WARN / 8 SKIP / 0 FAIL。WARN は P9 の 2 件） |
| `make forbidden-check` | exit 0（changed 11 / violations 0） |
| `make inbox-check` / `make taskindex-check` | exit 2 / exit 2（禁止 7 を守ったため。意図した結果） |
| `pytest` | 前 7 failed / 後 6 failed / 670 passed（5.4。条件が揃っていない） |
| 禁止語（送出物 4 件） | **0 件**。陽性対照 2 語で 2 件検出 |
| 禁止語（digest 5 件） | `2026-09-20-2944a71b` に 2 件。過去のセッションで禁止語を**取り除いた sed 命令**の機械抽出で、主張ではない。digest は生成物のため手で直していない |
| 秘匿（環境の資格情報、9 件） | 照合一致 **0 件**。陽性対照は検出あり |
| 秘匿（七台の画面の鍵、9 件） | 七台とも **hits=0 / pc_hits=1**。鍵はノードの中で照合し、値も件数以外も出していない |
| 32 文字以上の塊 | 5 件すべて `SHA256:` に続く公開鍵の指紋 |

| 送出 | 値 |
|---|---|
| 分岐 | `feat/fleet-sync-outbound-off`（基点 `origin/phase0` = `ef8f641a`） |
| commit | `f739448d`（記録の本体）＋ 本表の追記 |
| push | 終了コード **0** |
| PR | **#206** — https://github.com/takuya3h/m2/pull/206 |
| 台帳へ返す | `make task-report`（本表の追記を commit した後に実行。結果は利用者への報告に記す） |
| 抑止の解除 | 台帳へ返した後に `rm -f .sync-pause`。稼働中の `~/bin/m2-sync.sh` は目印に対応した版（`grep -c sync-pause` = 2） |
| 退避の扱い | digest 3 件は退避先から戻し、作業中に生じた 2 件と合わせて 5 件を本契約に含めた（退避先に残り 0 件） |

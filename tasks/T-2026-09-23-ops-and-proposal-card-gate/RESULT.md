# RESULT — T-2026-09-23-ops-and-proposal-card-gate

**判定: partial。** 完了判定 10 件のうち 8 件を充足し、e は部分未達、h は利用者の決定により未達。
未達はいずれも実測に基づき、数値の捏造も推測での穴埋めも行っていない。

実行ホスト `m2` / 分岐 `feat/ops-and-proposal-card-gate`（起点 `origin/phase0`）/ 起点 commit `66855c5b`。
本契約は GPU を使用していない。

## 1. 解決された参照

| spec の記載 | 解決結果 | 出所 |
|---|---|---|
| `contract.conventions_rev`（占位） | `c801e17c3231fe1f2b7c8072e1a960e6dbab8ca5` | `git log -1 --format=%H -- context/conventions.md`（変更前） |
| `meta.created_from.runindex_commit`（占位） | `4e97b3deae28e653948c19309d229c755587c42b` | `git log -1 --format=%H -- runindex/` |
| `meta.created_from.counts`（起票時 0/0/0） | 実測 index 1558 / experiments 476 / verdicts 1506 | `runindex/*.csv` の行数 − 1 |
| `contract.inject_verbatim` | `conventions#prohibitions` `conventions#issuer_cautions` `conventions#proposal_gate` の三節。**原文のまま参照し要約していない。** | `context/conventions.md` |

占位は Task A-4 の指示どおり実測値へ差し替えた。`created_from.counts` は SPEC が差し替えを
指示していないが、起票時の値 0/0/0 は実測と一致しないため実測値を併記した（規約の注意 1）。

## 2. ゲートの通過状況

| ゲート | after | 判定 | 実測した内容 |
|---|---|---|---|
| G1 | A | pass | 作業ツリー清浄（未追跡 4 件は `git stash push -u` で退避）、HEAD `66855c5b`、変更前の数を 3 節に記録 |
| G2 | C | pass | P14 の 7 種を試験（21 件）と端から端まで（`make task-preflight`）の両方で実測。4 節の表 |
| G3 | D | pass | 実例 3 件で FAIL、宣言を満たす 1 件で PASS。**4 件目は起票時の宣言漏れが是正済みのため該当しない**（5 節） |

## 3. 実測（変更前と変更後）

| 項目 | 変更前 | 変更後 |
|---|---|---|
| 規約のアンカー数 | 11 | 11（新設なし。既存節へ追記のみ） |
| `check_spec.py` の規則数 | 8 | 9 |
| L3 の検査数 | P1〜P13 | P1〜P14（**末尾に追加。P1〜P13 の番号・順序・挙動は不変**） |
| L1 の検査の識別子 | L1-1〜L1-9 | L1-1〜L1-10 |
| `spec.yaml` の件数 / schema 通過 | 127 / 127 | 127 / 127 |
| 試験 | 6 failed / 609 passed | 6 failed / 644 passed（**失敗数は不変。35 件増**） |
| 旧様式 `result.yaml` の schema エラー | 15 件 | 15 件（据え置き。7 節） |
| `conventions.md` の差分 | — | 10 行追加 / 0 行削除（**既存行の本文は不変**） |

検証の結果（すべて `TASK=T-2026-09-23-ops-and-proposal-card-gate`）:

| 検査 | 結果 |
|---|---|
| `make task-validate`（L1+L2） | exit 0 |
| `make task-preflight`（L3） | 6 PASS / 0 WARN / 8 SKIP / 0 FAIL、exit 0 |
| `make forbidden-check` | `violations: []`、`permitted` は `context/conventions.md` 1 件、exit 0 |
| `make spec-check` | 規則 9 件を検査し該当 0 件、exit 0 |

commit の後は L2-6 の WARN が出る（`conventions.md が c801e17c 以降に変更されています`）。
**規約を変えた契約では必ず出る警告であり、終了コードは変えない。** 記録した rev は
変更前の値であり、契約の逐語の出所として正しい。

L3 で SKIP になった 8 件: P2・P3・P11（`plan.env.preflight` に記載なし）、
P4・P5・P13・P14（`kind=impl` のため対象外）、P12（解決前提の参照なし）。
**SKIP は合格ではなく「実行されなかった」である。**

## 4. P14 `proposal_card_checked` の 7 種（完了判定 d）

| 入力 | 期待 | 実測 |
|---|---|---|
| `kind` が impl | SKIP | SKIP「kind=impl のため対象外（exp のみ）」 |
| `kind` が analysis | SKIP | `decide_applicability` が False |
| 完了済みの exp（`result.yaml` に `gates[].verdict`） | SKIP | SKIP「完了済み（result.yaml に verdict あり: 1 件）」 |
| 例外 `T-2026-09-19-stage1-detector-towers-r2` | SKIP | SKIP「導入前の契約のため対象外」 |
| 例外 `T-2026-09-19-stage1-phase-tower-r3` | SKIP | 同上 |
| `intent.proposal_card` が無い exp | FAIL | FAIL「intent.proposal_card が無い」 |
| 経路のファイルが無い exp | FAIL | FAIL「提案カードが無い: docs/proposals/2026-01-01-no-such-card.md」 |
| 検査を通らないカードを指す exp | FAIL | FAIL「check_proposal.py を通らない（検出 3 件）」＋検出の内容 |
| 検査を通るカードを指す exp | PASS | PASS「検出 0 件（カード 16 件 / 禁止語 15 語を検査）」 |

**例外は task_id の完全一致で照合する。** 空振りでないことを 3 方向で確かめた。
一文字違い `…-towers-r3`、例外を接頭辞に持つ `…-towers-r2-followup`、部分列
`stage1-detector-towers-r2` のいずれも FAIL になる（部分一致にすると全て免除される）。

配線まで確かめるため、一時契約を置いて `make task-preflight` を端から端まで回した
（カード無し → FAIL、雛形を指す → FAIL）。測定後にその一時契約は削除した。

## 5. `allow_write_incomplete` の実例（完了判定 e、部分未達）

| 実例 | kind | destination | allow_write | 判定 |
|---|---|---|---|---|
| `T-2026-09-16-proposal-gate` | impl | `docs/` | `context/conventions.md` | **FAIL**（spec.yaml:29） |
| `T-2026-09-17-amp-compile-timing` | impl | `docs/stage0/` | `experiments/transfer/pd_refin_empty_seed42_tf32/` | **FAIL**（spec.yaml:38） |
| `T-2026-09-19-p13-skip-and-enum` | impl | `tasks/T-2026-09-19-p13-skip-and-enum/` | `tasks/_schema/result.schema.json` | **FAIL**（spec.yaml:31） |
| `T-2026-09-18-stage1-detector-towers` | exp | `experiments/baselines/stage1_dtower/` | 同経路 ＋ `runindex/` | PASS |

**完了判定 e が求める「実例 4 件で FAIL」は達成できない。** 4 件目は起票時に宣言を欠いたが、
実行者が同じ `spec.yaml` へ追記して是正しており（`meta.amendments` に記録がある）、
現行の本文は destination と `runindex/` の双方を宣言している。**是正済みの契約が
該当しないのは規則が正しく働いている証拠であって、規則の欠陥ではない。**
この 4 件目こそが完了判定 e の後半「allow_write を足した同じ spec で PASS」の実測である。

### 適用範囲（利用者の決定 2026-09-22）

SPEC Task D-1 は規則を `kind` が exp の契約に限るが、裏付けの実例 4 件のうち 3 件は impl で、
そのままでは該当が 0 件になる。範囲を三つ測って諮り、変種 C を採った。

| 変種 | 内容 | 全 127 契約中の該当 |
|---|---|---|
| A | 全 kind 無条件 | **123 件**（`allow_write` を宣言する契約は 9 件しかなく、ほぼ常に該当する） |
| B | 宣言がある契約だけ | 5 件（宣言を一行も書かない起票を見逃す） |
| **C（採用）** | exp は無条件、それ以外は宣言がある時だけ | **15 件**（exp 10 / impl 5） |

## 6. L1-10 と `.gitignore`（完了判定 f・g）

L1-10 は `gates[].after` の実在と、ゲートの並びがフェーズの並びと同じ順であることを見る。
**既存 127 契約での該当は 0 件**（新しい検査で過去の契約を落としていない）。対照は両方向:

| 入力 | 判定 |
|---|---|
| 正しい順（A → C） | PASS |
| 同じフェーズの直後に二つ | PASS（戻る場合だけを咎める） |
| 順序を入れ替え（C → A） | FAIL |
| 実在しないフェーズ `Z` | FAIL |
| `after` が空 | FAIL |

`.gitignore` の型を `.sync-pause` から `.sync-pause*` へ広げた。`git check-ignore -v` は
`.sync-pause` と `.sync-pause.released` の両方を `.gitignore:244` で捕捉する。
陽性対照として型に一致しない `.sync-paus-control` を置くと未追跡として現れるため、
`git status` が常に空になっているのではない。

**抑止は版管理の除外の影響を受けない。** 実装が見るのは目印の実在だけである
（`scripts/sync/m2-sync.sh:44` の `[ -f "$M2DIR/.sync-pause" ]`）。この行は `git` に触れない。
稼働中の `~/bin/m2-sync.sh` が抑止に対応していることも確かめた（`grep -c sync-pause` が 2）。

## 7. 旧様式 `result.yaml` の対応表（完了判定 h、未達）

`tasks/T-2026-08-22-philip-hub-foundation/result.yaml` は現行 schema で 15 件のエラーを出す。
書き直しは**利用者の決定により行わず据え置いた**。対応表は次のとおり。

| 旧の項目 | 現行 schema の項目 | 対応 |
|---|---|---|
| `meta.task_id` | `task_id` | 取れる |
| `meta.host` / `meta.branch` | `host` / `branch` | 取れる |
| `meta.verdict: PARTIAL` | `status: partial` | 取れる（語形を小文字へ） |
| `push.local_commit` | `commits[]` | 取れる |
| `unknown_reason` | `unknowns[]` | 取れる |
| `reported_to_ledger_reason` | `followups[]` | 取れる |
| `deviations_count: 12` | `deviations` | 版 1 なら整数のまま。**版 2 以降は一覧が要る**（中身は RESULT.md §5 にある） |
| `gates[].{id,verdict}` | `gates[].{id,verdict}` | 取れる（`after` は現行 schema に無く、`note` は版 2 以降で必須） |
| `meta.kind` / `meta.executed_at` / `resolved.*` / `measured.*`（25 項目） / `validation.*`（11 項目） / `git_identity.*` | — | **該当する項目が無い**（`additionalProperties: false`） |
| （旧に無い） | `tests.{before_failed,after_failed,after_passed}` | **旧報告にも旧 RESULT.md にも試験の記録が一切無い。整数のみを受ける必須項目であり、推測で埋めれば捏造になる** |
| （旧に無い） | `issuer_defects[]` / `positive_controls[]` | 当時測っていない。版 3 は `positive_controls` を必須にする |

`tests` の 3 整数が最後まで塞がらない。加えて `result.schema.json` 自身と `/task` 手順書が
「**過去の報告に版 2・版 3 の要件を遡って適用しない／過去を書き換えて通す方法は採らない**」と
明記しており、`result.schema.json` は本契約の `allow_write` に無く改訂もできない。
そこで諮り、据え置きと申し送りを選んだ。

## 8. 完了判定の充足

| # | 判定 | 結果 |
|---|---|---|
| a | 雛形が 16 項目と却下表を持ち、雛形のままで落ちる | 充足（検出 3 件・見出し欠落 0 件。埋めると検出 0 件） |
| b | 規約に 4 つの規則が足され既存行が不変 | 充足（10 行追加 / 0 行削除） |
| c | `intent.proposal_card` が任意で既存 spec 全件通過 | 充足（127 / 127。整数を入れると落ちる） |
| d | P14 の 7 種 | 充足（4 節） |
| e | 規則が実例 4 件で FAIL、宣言を足すと PASS | **部分未達**（3 件 FAIL、4 件目は是正済みで PASS。5 節） |
| f | L1 の `after` 検査 | 充足（6 節） |
| g | `.gitignore` | 充足（6 節） |
| h | 旧様式の書き直し | **未達**（利用者の決定により据え置き。7 節） |
| i | 試験の失敗数が不変 | 充足（6 → 6、通過 609 → 644） |
| j | PR が Draft でなく base が phase0 | 送出時に記録 |

## 9. 起票者の誤り

1. **`self_contradiction`** — 付録 A は提案カードを表で示すが、SPEC §3 Task B-1 は「16 項目の見出しと
   空欄」と書く。`check_proposal.py` は markdown の見出しから番号を取るため、付録 A の表だけを
   置くと 16 件すべて `missing_heading` で落ち、**表のセルを埋めても落ち続ける**（実測）。
   完了判定 a の四列目「項目を全部埋めた文書で通る」が原理的に達成できない。
2. **`asserted_without_measuring`** — 完了判定 e は「実例 4 件の spec で FAIL する」と書くが、
   Task D-1 の指示どおり exp 限定で実装すると該当は 0 件になる（3 件は impl で対象外、
   残る 1 件は是正後の本文が宣言を満たす）。**4 件という数は現行の本文を測らずに書かれている。**
3. **`self_contradiction`** — Task D-4 は旧様式 `result.yaml` を版 3 へ書き直すことを求めるが、
   `result.schema.json` と `/task` 手順書は「過去を書き換えて通す方法は採らない」と明記し、
   版 3 が必須とする `tests` の 3 整数は旧報告に存在しない。指示どおり書き直すと未測定の値を
   書くことになり `governance.integrity` の `unknown_if_unmeasured` と衝突する。
4. **`asserted_without_measuring`** — Task D-4 は旧版の退避先を `result.v2.yaml` と指定するが、
   当該ファイルの `result_version` は 1 である。指示どおりの名にすると版番号と名が食い違う
   記録が残る。据え置きの決定により顕在化しなかったが、名の指定そのものが未測定である。

## 10. deviations（指示書どおりにしなかった箇所）

1. **判断** — 提案カードの雛形を、付録 A の表だけでなく項目ごとの見出しと併記にした
   （利用者の決定 2026-09-22）。付録 A の逐語ではない。9 節 1 の理由による。
2. **判断** — 規則の適用範囲を Task D-1 の「exp 限定」から変種 C へ変えた（利用者の決定 2026-09-22）。
   全 kind 無条件では 127 件中 123 件が該当し判別力を失う（実測）。
3. **判断** — 旧様式 `result.yaml` を書き直さず据え置いた（利用者の決定 2026-09-22）。完了判定 h は未達。
4. **契約の誤り** — 完了判定 e の「実例 4 件で FAIL」は 3 件にとどまる。4 件目は是正済みで該当しない。
5. **判断** — L1 の新しい検査の識別子を L1-10 とした。SPEC は番号を指定していないが、
   L1-9 は `validate_spec_md` が使用済みで、重ねると既存の該当と見分けられなくなる。
6. **判断** — `tests/test_symmetry_gate.py` の「P13 が末尾である」ことを固定していた試験を、
   「P13 の位置が 13 番目である」ことの固定へ変えた。P14 を末尾に足したため。
   **P1〜P13 の番号・順序・名前・挙動は変えていない。**
7. **判断** — `meta.created_from.counts` の 0/0/0 を実測値へ差し替えた。SPEC は差し替えを
   指示していないが、起票時の値が実測と一致しないため（規約の注意 1）。
8. **判断** — 規約の変更履歴の commit 欄は、最初の commit で `(本契約)` と置き、
   commit 後に実際の値へ差し替える二段で記録した（自分の commit 番号は事前に書けない）。
9. **環境** — 開始時に未追跡だった session digest 4 件は `git stash push -u` で退避した。
   **開始前から在る未追跡を消していない**（禁止事項 7）。
10. **判断** — SPEC 禁止事項 5 は `context/auto/*` と `tasks/inbox.md` の再生成を禁じるが、
    `/task` 手順書は投影の生成と `taskindex-check` / `inbox-check` の exit 0 を求める。
    **契約と手順書が衝突する。** 諮って再生成を選んだ（利用者の決定 2026-09-22）。
    `forbidden-check` は生成物を除外して検査する設計であり、生成物 4 経路
    （`context/auto/` の 3 件と `tasks/inbox.md`）を除外したうえで違反 0 件を確かめた。
    再生成しなければ `tasks/inbox.d/` に書いた 6 行が集約結果に載らず、
    次の契約の検査も失敗したままになる。

## 11. 想定外と申し送り

- 例外の二件（`T-2026-09-19-stage1-detector-towers-r2` / `T-2026-09-19-stage1-phase-tower-r3`）は
  配布台帳にあるが repo には未取得である。P14 の例外の経路は試験で確かめたが、
  **実物の契約で SKIP になることは取得後に確かめること。**
- `result.schema.json` に、遡及の書き直しをどう扱うか（`tests` を任意にする版、または旧様式の
  退避の規約）を足す契約が要る。本契約では同ファイルは `allow_write` に無く触れていない。
- `tasks/_templates/result.yaml` と `.claude/skills/task/SKILL.md` は `issuer_defects` の型を
  4 種と書くが、`result.schema.json` は 6 種である（PR #192 で拡張済み）。**写しが古い。**
- `make spec-check` を `TASK` 無しで回すと `allow_write_incomplete` が 15 件出る（exp 10 / impl 5）。
  過去の契約の是正は別契約で行うこと。
- 本契約の統合後、起票者は Stage 2 の提案カードを `docs/proposals/` に置き、
  `check_proposal.py` を通してから exp を起票する（SPEC §8）。

## 12. 送出

| 項目 | 実測 |
|---|---|
| commit | `ae76c1b9`（本体）、`4369cf5e`（変更履歴の commit 欄の記録） |
| PR | **#194**。`isDraft: false`、`baseRefName: phase0`、`headRefName: feat/ops-and-proposal-card-gate`、`state: OPEN` |
| push の経路 | `origin` の `pushurl` が https で資格情報を解決できず失敗した。fetch 側の ssh は通るため、**設定を変えずに** ssh の URL を明示して push した。上流は `origin/feat/ops-and-proposal-card-gate` に設定済み |
| 配布台帳への報告 | 下に追記 |

**完了判定 j は充足。** PR は Draft でなく、base は `phase0`、分岐名は `feat/` で始まる。

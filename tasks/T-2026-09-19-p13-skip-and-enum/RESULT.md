# RESULT — T-2026-09-19-p13-skip-and-enum

**判定: PASS。** 完了済みの exp 契約 13 件すべてで P13 が SKIP になり、未完了の挙動は
変わっていない。様式の列挙に二型が入り、既存の報告は変更前と同数が通る。

実行ホスト `efros` / 分岐 `feat/p13-skip-and-enum`（`origin/phase0` = `cd5aba2b`）/
2026-09-21（JST）。**GPU は使用していない。** 証跡は `audit.md`、変更の要点は `notes.md`。

---

## 1. 解決された参照

| 記載 | 解決先 | 実測値 |
|---|---|---|
| `contract.conventions_rev`（占位） | `git log -1 -- context/conventions.md` | `c801e17c3231fe1f2b7c8072e1a960e6dbab8ca5` |
| `meta.created_from.runindex_commit`（占位） | `git log -1 -- runindex/` | `4e97b3deae28e653948c19309d229c755587c42b` |
| `meta.created_from.counts`（占位 0） | `runindex/*.csv` の行数 − 1 | index 1558 / experiments 476 / verdicts 1506 |
| `inputs.denominator.ref` | — | 記載なし（`kind: impl`） |
| `inputs.frozen_source.ref` | — | 記載なし |
| `contract.inject_verbatim` | `context/conventions.md` | `conventions#prohibitions`、`conventions#issuer_cautions` の 2 アンカー。L2 が実在を確認（`make task-validate` exit 0） |

`inputs.sigma_policy` は記載が無く、本契約は統計判定を行わないため継承していない。

---

## 2. 完了判定

| # | 判定 | 結果 | 実測（空振りでないことの確認） |
|---|---|---|---|
| a | 完了済み exp で SKIP、理由に完了済み | **充足** | 13/13 が SKIP。理由は `完了済み（result.yaml に verdict あり: N 件）のため対象外`。**変更前は 13/13 が FAIL**（§A5） |
| b | 未完了 exp の挙動が変わらない | **充足** | 対照 11 件中、未完了の 9 種すべてが期待どおり（表なし FAIL／揃う PASS／UNKNOWN FAIL／理由欠落 FAIL／三値外 FAIL／prereg 無し FAIL）（§A6） |
| c | 判定は result.yaml の実在と verdict のみ | **充足** | verdict を欠く 5 種（`gates: []`／空文字／項目なし／`gates` なし／壊れた YAML）がすべて FAIL。**名前が完了済み契約を含む未完了も FAIL**（§A6 #7〜#9・#11） |
| d | 二型が通り未知が落ちる。既存が全件通る | **充足（記録つき）** | 二型と既存の語が通り、`zz_unknown` が落ちた。既存は **103 件中 102 件が通過**。不通過 1 件は**変更前から不通過**（§A7・§4） |
| e | 「enum には未追加」の注記が消えている | **充足** | 変更前は `docs/issuer-defects.md:11` に 1 件、それを受ける `:12` の「（同上）」が 1 件。**変更後は 0 件**（§A8） |
| f | 試験の失敗数不変、規則数不変 | **充足** | 6 failed → **6 failed**（同一の 6 件）。595 passed → 609 passed（追加 14 件）。`len(check_spec.RULES)` = **8 → 8**（§A9） |
| g | PR が Draft でなく base が phase0、分岐が feat/ | **充足** | PR **#192**、`isDraft: false`、`baseRefName: phase0`、`headRefName: feat/p13-skip-and-enum`、`state: OPEN`（`gh pr view 192 --json` の実測） |

**判定 d の 12 件と 13 件の差。** 契約は「完了済みの exp 契約 12 件」と書くが、実測は
**13 件**である。起票後に `T-2026-09-19-stage1-phase-tower-r2` が完了したためで、
矛盾ではない。**未完了の exp は 0 件**であった（§A4）。

---

## 3. 何を変えたか

| ファイル | 変更 |
|---|---|
| `tools/preflight_task.py` | `completed_verdicts(task_id)` を追加。`check_symmetry_table` の冒頭で印を見て SKIP。**P1〜P12 と、未完了 exp に対する P13 の挙動は 1 行も変えていない** |
| `tasks/_schema/result.schema.json` | `issuer_defects[].type` の列挙を 4 → 6 種。既存の語は不変 |
| `docs/issuer-defects.md` | 「enum には未追加」と「（同上）」を削除。それ以外は触れていない |
| `tools/build_taskindex.py` | `DEFECT_TYPES` を 6 種へ。**契約に無い変更**（§5 の逸脱 2） |
| `tests/test_symmetry_gate.py` | 試験 14 件を追加（28 → 42 件） |

🔴 **`verdict` は `result.yaml` の最上位の項目ではない。** 様式が持つのは
`gates[].verdict` であり、最上位は `status` である。契約の §2 は「完了済み契約は
`result.yaml` を持ち `verdict` が入っている」と書くが、**最上位を見る実装にすると
完了済みが 0 件になり、関門は誰も救わないまま 13 件すべてを止め続ける**（実測）。

`status` ではなく `gates[].verdict` を採った根拠は契約自身にある。契約 §5 の対照が
「`result.yaml` を verdict なしにした一時契約で FAIL」を求めるが、`status` で判定すると
その一時契約も `status` を持つため SKIP になり、**契約が要求する対照を通せない**。
契約が名指しした語で、実在する唯一の場所を採った（§A3）。

---

## 4. 想定外（契約 §6 に該当）

**既存の `result.yaml` 1 件が schema を通らない。** `T-2026-08-22-philip-hub-foundation`
が旧様式（`meta:` の下に `task_id` と `verdict: PARTIAL` を置く形）で書かれており、
最上位の `task_id` と `status` を欠く。**変更前から不通過**であり、本契約の変更とは
無関係である（`kind: impl` で exp でもない）。契約 §6 に従い**触らず記録して続けた**。

契約 §6 のもう一方（完了済みの印が `result.yaml` 以外に要る）には**該当しなかった**。
印は `result.yaml` の内側にあり、諮る必要は生じていない。

---

## 5. 起票者の誤り

| # | 型 | 内容 |
|---|---|---|
| 1 | `asserted_without_measuring` | 「完了済み契約は `result.yaml` を持ち `verdict` が入っている」と断定したが、`verdict` は最上位に存在しない。指示どおり最上位を見る実装にすると完了済みが 0 件になり、13 件すべてが FAIL のまま残る |
| 2 | `asserted_without_measuring` | 「完了済みの exp 契約 12 件」と断定したが実測は 13 件。起票後に 1 件が完了した。件数を完了判定 a の根拠に置いていたため、字面どおりでは充足を示せない |
| 3 | `self_contradiction` | ゲート G1 が `after: B` で「検証（対照つき）」の結果を求めるが、それを測るのはフェーズ C である。字面どおり B の終了時に評価すると未測定の値を書くことになり、`governance.integrity` の `unknown_if_unmeasured` と衝突する。L3 の P9 と `make spec-check` が同一の指摘を出した |
| 4 | `check_does_not_check` | `contract.allow_write` が `tasks/_schema/result.schema.json` だけを挙げるが、Task B は `tools/preflight_task.py` と `docs/issuer-defects.md` の変更も求める。今回は 3 つとも禁止領域の外だったため `make forbidden-check` は通ったが、**宣言は求める作業を覆っていない** |

## 6. 逸脱

| # | 型 | 内容 |
|---|---|---|
| 1 | `spec_defect` | ゲート G1 を `after: B` の時点では評価せず、**フェーズ C の実測が揃った時点で評価した**。B の時点では対照も試験も測っておらず、評価すれば未測定の値を書くことになる。**契約は書き換えていない**（§5 の誤り 3） |
| 2 | `judgement` | 契約の Task B に無い `tools/build_taskindex.py` の `DEFECT_TYPES` を 6 種へ揃えた。この一覧は自ら「`result.schema.json` の列挙と同じ 4 種」と宣言しており、**様式だけ増やすと新しい型の欠陥が投影の集計表から黙って落ちる**。禁止事項には触れない（`context/auto/` の生成物ではなく生成器であり、規則数にも関わらない）。一致を試験で縛った |
| 3 | `judgement` | 契約の Task C が求める「雛形から作った一時契約」を、repo 内ではなく**一時ディレクトリへ `preflight_task.TASKS_DIR` を差し替えて**作った。repo 内に一時契約を残すと L1/L2 と投影が拾うため。判定の対象は同一の関数である |
| 4 | `environment` | 開始時の未追跡 1 件（`docs/sessions/digest/2026-09-17-….md`）を利用者の指示により `git stash push -u` で退避した。契約 §4 の「開始前から在る未追跡を消さない」は守っている（消さずに退避しており、`git stash pop` で戻る） |

## 7. 陽性対照

**判定が働いていることは、判定を壊して確かめた。** 4 件の変異を実際に当てて測った
（当てた後はいずれも復元し、42 件が通ることを確認した）。

| 判定 | 何を入力すれば失敗するはずか | 実際に何が起きたか（実測） |
|---|---|---|
| a 完了済みで SKIP | 完了済みの判定を外す（`if verdicts:` → `if False:`） | **1 failed / 41 passed**。`test_completed_contract_is_skipped` が落ちた |
| b 未完了は従来どおり | 判定を「常に SKIP」へ壊す（`if verdicts:` → `if True:`） | **18 failed / 24 passed**。未完了の対照が総崩れになった |
| c 名前で判定しない | `result.yaml` が無いとき task_id の部分一致で他契約の印を引く | **1 failed / 41 passed**。`test_name_containing_a_completed_task_id_is_not_completed` が落ちた |
| c 印を読み損ねたら未完了 | `result.yaml` を壊れた YAML にする | 例外で止まらず FAIL を返した（対照 #9）。**黙って SKIP へ倒れない** |
| d 未知の型を拒む | `zz_unknown` を `issuer_defects[].type` に置く | `'zz_unknown' is not one of [...]` で落ちた |
| d 様式と投影の一致 | 様式の列挙にだけ `zz_probe` を足して投影に足さない | **1 failed / 41 passed**。`test_defect_types_in_the_projection_match_the_schema` が落ちた |
| e 注記の削除 | 変更前の本文を入力する | 変更前は 1 件（`docs/issuer-defects.md:11`）、変更後は 0 件。件数の差で空振りでないことを示した |
| f 失敗数不変 | 変更前を測らずに「不変」と書く | 変更前 6 failed / 595 passed を先に測り、変更後の 6 件が**同一の試験名**であることを照合した |

## 8. 送出

| 項目 | 実測 |
|---|---|
| commit | `d86c778b` |
| push | `origin/feat/p13-skip-and-enum`（新規分岐） |
| PR | **#192** https://github.com/takuya3h/m2/pull/192 — Draft でない / base `phase0` |
| `make task-report` | exit 0。`verdict: pass` / `n_issuer_defects: 4` / `report_bytes: 10703` / `replaced_blocks: 0`。秘匿の検査を通過 |
| `.sync-pause` の解除 | `mv .sync-pause .sync-pause.released`（実測は下表） |

# 提案カードの置き場と exp からの参照を必須にする。allow_write の漏れを止める。運用の残件

**task_id:** T-2026-09-23-ops-and-proposal-card-gate  **kind:** impl

## 1. 背景

提案関門（T-2026-09-16-proposal-gate）は規約・文書・検査器として存在するが、**Stage 1 の実験は関門を通っていない**。
提案カードが会話の中にしか無く repo に置かれず、検査器は試験でしか動かず、二周目・三周目は prereg を直接書いてカードを飛ばした。
関門を作った起票者自身が飛ばした。**文言による自制は働かないので機械で止める**（README の設計思想、対称性関門と同じ）。

利用者の決定（2026-09-22）: exp 契約は検査を通ったカードへの参照を必須にする。配布済みの二件（検出塔二周目、工程塔三周目）は
「導入前の契約」として例外。候補数の下限は 3。批判会話では web 検索を必須にする。F の既存行の分類し直しは後回し。

あわせて運用の残件: allow_write の宣言漏れが 4 契約で再発した（spec-check の規則で止める）。`.sync-pause.released` が毎回
未追跡として残る（.gitignore）。ゲートの `after` がフェーズの順と合っていない起票があった（L1 で検査）。旧様式の result.yaml が
1 件 schema を通らない（書き直す）。

**本契約では GPU を使用しない。**

## 2. 確定した事実（ホストによらない値だけ）

- `tools/check_proposal.py` は禁止語と提案カードの見出し 16 件（#15・#16 を含む）と #5・#6・#10 の数字を検査する。規約の表から見出しを読む
- L3 は `tools/preflight_task.py` に P1〜P13。P13 は完了済み（result.yaml の gates[].verdict あり）で SKIP（PR #192）
- `tools/check_spec.py` の規則は issuer_defects の実例を裏付けに持つ。allow_write の漏れの実例は 4 件:
  T-2026-09-16-proposal-gate（conventions.md）、T-2026-09-17-amp-compile-timing（実験出力）、T-2026-09-18-stage1-detector-towers（実験出力）、
  T-2026-09-19-p13-skip-and-enum（3 ファイル中 1 つしか宣言せず）
- 旧様式の result.yaml: `tasks/T-2026-08-22-philip-hub-foundation/result.yaml`。現行 schema（版 3）を通らない（PR #192 の実測）
- 例外の二件: `T-2026-09-19-stage1-detector-towers-r2`、`T-2026-09-19-stage1-phase-tower-r3`（配布済み。カード無しで起動してよい）
- 規約のアンカーは 11。新設は無い（既存の proposal_gate 節に行を足す）
- 対話シェルは zsh。`git --no-pager`。`make` には読み込みを同じ命令に含める

## 3. Task

**コマンドは書かない。実装を読んで決めてよい。**

### Task A — 開始状態

1. 作業ツリーの清浄、HEAD が phase0。未追跡は移動で退避（拒まれたら残して要約値を記録）
2. 変更前の数: check_spec の規則数、L1 の検査数、L3 の検査数、規約のアンカー数、試験の失敗数、既存 spec.yaml の件数と schema 通過数
3. 旧様式 result.yaml の全文を読み、現行 schema との対応表（旧の項目 → 新の項目）を作る。対応の取れない項目があれば停止して諮る
4. `conventions_rev` と `runindex_commit` を実測し占位を差し替える

### Task B — カードの置き場と規約

1. `docs/proposals/` を作り、`_template.md` を置く。内容は付録 A（16 項目の見出しと空欄、却下表の骨組み）。**雛形のままでは check_proposal が落ちる**（項目が空）ことが意図
2. `conventions#proposal_gate` に付録 B の行を足す（候補数の下限 3、批判会話の web 検索必須、カードは `docs/proposals/YYYY-MM-DD-slug.md`、
   exp は `intent.proposal_card` で参照、導入前の例外二件）。既存の行の本文は変えない
3. `docs/proposal-gate.md` の B.3（流れ）に、カードを repo に置く段と、exp が参照する段を足す
4. `docs/issuer-defects.md` に、起票者が自作の関門を二度飛ばした実例を `self_contradiction` の項へ追記（新しい型は作らない）
5. 変更履歴に本契約の行

### Task C — L3 P14 と schema

1. `spec.schema.json` の `intent` に `proposal_card`（string、任意）を足す。既存の spec.yaml 全件が通ることを確かめる
2. L3 に **P14 `proposal_card_checked`** を末尾に足す。仕様:
   - kind が exp 以外 → SKIP
   - 完了済み（P13 と同じ判定）→ SKIP
   - task_id が例外の二件 → SKIP。理由に「導入前の契約」と出す。**例外は task_id の完全一致**。部分一致にしない
   - `intent.proposal_card` が無い → FAIL
   - 経路のファイルが無い → FAIL
   - `check_proposal.py` を当てて検出があれば → FAIL（検出の内容を出す）
   - それ以外 → PASS
3. P1〜P13 の番号・順序・挙動を変えない

### Task D — spec-check、L1、.gitignore、旧様式

1. `check_spec.py` に規則を一つ足す: **kind が exp なら、`contract.allow_write` に `outputs.destination`（またはその親）と `runindex/` の両方が無ければ FAIL**。
   裏付けの実例 4 件を規則の注記に書く。impl・analysis は対象外（出力先が禁止領域と限らないため）
2. L1 に検査を足す: `gates[].after` が `phases[].id` に実在すること、gates の並びが phases の並びと同じ順であること
3. `.gitignore` に `.sync-pause*` を足す。同期の仕組み（`.sync-pause` を見て止まる処理）が ignore の影響を受けないことを、
   実装を読んで確かめる（git の追跡と、ファイルの実在の検査は別）。影響があるなら足さずに諮る
4. 旧様式 result.yaml を現行 schema（版 3）に書き直す。Task A の対応表に沿い、判定・欠陥・逸脱の内容を失わない。
   旧版は `result.v2.yaml` として同じディレクトリに残す。**内容を推測で足さない**

### Task E — 検証と報告

1. 対照（完了判定 a〜h の四列目）。特に P14 は 7 種、spec-check は実例 4 件 + 宣言を足した同じ spec、L1 は順序を入れ替えた spec
2. L1、L2、L3、`make forbidden-check`（permitted に宣言分、violations 0）、`make spec-check TASK=T-2026-09-23-ops-and-proposal-card-gate`、試験
3. `RESULT.md`、`result.yaml`（版 3）、`audit.md`、`tasks/inbox.d/`
4. commit、push、**PR の base は phase0**。分岐名 `feat/ops-and-proposal-card-gate`。`.sync-pause` を移動で解除

## 4. 禁止事項

**禁止は実行者の操作に対するものであり、同期処理による配布を含まない。**

1. P1〜P13、L1 の既存検査、check_spec の既存規則の番号・順序・挙動を変えない
2. `context/conventions.md` の既存行の本文を変えない。足すのは指定の行だけ
3. 例外の二件と完了済み以外に、P14 を免除する経路を作らない
4. 旧様式 result.yaml 以外の過去の契約のファイルを変えない
5. `context/auto/*` と `tasks/inbox.md` を再生成しない
6. `experiments/**`、`data/**`、`runindex/**` に触れない
7. 開始前から在る未追跡を消さない
8. 外部への送信は `make task-report` 以外の経路で行わない

## 5. 完了判定

`spec.yaml` の `outputs.acceptance` と一致させている。**四列目を空にしない。**

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 雛形 | 16 項目と却下表。雛形のままで落ちる | 項目を全部埋めた文書で通る |
| b | 規約の追記 | 4 つの規則が読める。既存行の要約値が不変 | 追記前後の既存行の要約値 |
| c | schema | `intent.proposal_card` 任意。既存 spec 全件通過 | 件数と通過数が一致。文字列以外を入れた spec で落ちる |
| d | P14 の 7 種 | 表のとおり | 例外の task_id を一文字変えた一時契約で FAIL（完全一致の対照） |
| e | spec-check の規則 | 実例 4 件で FAIL、宣言を足すと PASS | impl の spec は対象外で不変 |
| f | L1 の after 検査 | 順序を入れ替えた spec で FAIL | 存在しない id で FAIL、正しい spec で PASS |
| g | .gitignore | 未追跡に出ない | `.sync-pause` の実在検査が ignore の影響を受けないことを実装の行で示す |
| h | 旧様式の書き直し | 現行 schema 通過、対応表 | 旧版を残す。schema 通過の前後 |
| i | 試験 | 失敗数不変 | 陽性対照の入力を壊して落ちることを一度示す |
| j | PR | 番号、base phase0 | 分岐名 |

## 6. 想定外と停止条件

- P14 を末尾に足せない → 諮る
- schema の任意項目で既存 spec が落ちる → 諮る
- 旧様式の対応が取れない項目 → 諮る（推測で埋めない）
- `.sync-pause` の実在検査が ignore で壊れる → 足さずに諮る
- 実行基盤が書き込みや `mv` を拒む → 回避せず提示

## 7. 報告の構成

`RESULT.md` は判断に使う事実だけ。判定／完了判定／実測（数の前後、P14 の 7 種、規則の 4 実例、対応表）／起票者の誤り／逸脱／想定外／送出。

## 8. 申し送り

- 本契約は GPU を使わない。ilya・efros の学習契約と並行可
- 本契約の統合後、起票者は Stage 2 の提案カードを `docs/proposals/` に置き、check_proposal を通してから exp を起票する
- 例外の二件は本契約の実装で明示的に列挙する。三件目を足すときは規約の改訂が要る

---

## 付録 A — `docs/proposals/_template.md`

    # 提案カード — YYYY-MM-DD-slug

    生成会話: （題名）／批判会話: （題名）／判定: 利用者（日付）／出所の証拠地図: docs/evidence/...

    | # | 項目 | 内容 |
    |---|---|---|
    | 1 | 問い（yes/no で答えが出る一文） | |
    | 2 | 最も近い先行研究三件（著者・年・DOI か arXiv ID・設定・効果量） | |
    | 3 | 先行研究がやらなかった／効かなかった理由の推定 | |
    | 4 | 否定的な先行研究二件 | |
    | 5 | 期待効果量（点）と外挿の出所 | |
    | 6 | 成功確率（0.0 から 1.0） | |
    | 7 | 成功の閾値（主判定規則） | |
    | 8 | 失敗の閾値と、失敗時に捨てるもの（案／設計／問い） | |
    | 9 | 最安の殺し実験 | |
    | 10 | 費用（run 本数 × 時間） | |
    | 11 | この案の結果で変わる判断 | |
    | 12 | 最も近い既存研究との差分一文 | |
    | 13 | F の却下・予測外れと同型でないことの宣言と読んだ行 | |
    | 14 | 初回にセットで試す設定の掃引集合と固定の理由 | |
    | 15 | 揃えるべき条件の一覧と両腕の実測値（conventions#symmetry の様式） | |
    | 16 | 排除済みの交絡の一覧 | |

    ## 却下表（批判会話の出力）

    | 案 | やらない理由 | 残す理由 | 順位（期待情報量） |
    |---|---|---|---|

    ## 失敗時手順（修正案のときだけ）

    | 区分 | 識別実験 | 結果 | 修正の水準 |
    |---|---|---|---|
    | 測定器 | | | |
    | データ | | | |
    | モデル・実装 | | | |
    | 仮説 | | | |
    | 問い | | | |

## 付録 B — `conventions#proposal_gate` に足す行（役割分離の表の後）

    ### 置き場と参照（2026-09-23 追加）

    - 提案カードは docs/proposals/YYYY-MM-DD-slug.md に置き、tools/check_proposal.py を通す
    - 生成会話は候補を三案以上出す
    - 批判会話は web 検索を必須とし、検索語と件数と見つかった否定例を却下表に書く
    - exp 契約は spec.yaml の intent.proposal_card にカードの経路を書く。L3 の P14 が、カードの実在と検査の通過を確かめる。
      無い exp は起動できない
    - 導入前の契約（T-2026-09-19-stage1-detector-towers-r2、T-2026-09-19-stage1-phase-tower-r3）は例外。三件目を足すときは本節を改訂する

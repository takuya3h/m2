# RESULT — T-2026-08-29-projection-refresh

**kind:** `impl` / ホスト `philip` / 分岐 `feat/projection-refresh` / **GPU 不使用**

証跡は `audit.md`。**同じ内容を二度書かない。**

**`inputs.data.split_files` は様式を満たすための記載であり、本契約は分割を参照していない。**

---

## 判定

**verdict: pass**（判断待ち 1 件、逸脱 3 件）

| Gate | 結果 | 根拠 |
|---|---|---|
| G1 | **pass** | 未統合の commit は **0 件**（`audit.md:56-73`）。再生成前の状態を全て記録（`audit.md:75-94`） |

---

## 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 投影の検査 | `context-check` `taskindex-check` `inbox-check` の三つが**全て exit 0** | 各生成物に一文字追加すると**対応する検査だけ** exit 2、他は exit 0。復元は sha256 一致で確認（`audit.md:165-179`） |
| b | 再生成が働いた | 再生成前は**三つとも exit 2**、後は**全て exit 0** | 8 ファイル全ての内容が変化（`audit.md:181-194`） |
| c | 変更範囲 | §2 の対象と契約ディレクトリ・受け皿のみ | 全量を `audit.md:196-207` に列挙。対象外 **0 件** |
| d | 索引が不変 | `runindex/` の変更 **0 件** | 契約ディレクトリへ同じ検査を当てると **1 件**出る（`audit.md:209-213`） |
| e | 禁止領域 | `forbidden-check` **exit 0・違反 0**（`changed=16` → 生成物 8 件除外 → `checked=8`） | 除外ディレクトリ・ファイルが出力に明示（`audit.md:215-224`） |
| f | 退避 | Phase A-4 の実測と**完全一致**（stash@{0} 追跡1・未追跡23／stash@{1} 未追跡10）。**消えたものは無い** | 復帰前後の一覧を並べ、差が復帰した 4 項目のみであることを示した（`audit.md:294-303`） |

---

## 実測（次の契約で使う値）

| 値 | 実測 |
|---|---|
| `runindex_commit` | `7918b5dd`（短縮形。前契約の記録と完全一致 = 統合はこの索引に触れていない） |
| `conventions_rev` | `a8c07e81`（同上） |
| 索引の件数 | index 1177 / experiments 213 / verdicts 1038（前契約時点と不変） |
| 投影の来歴（再生成後の要約値） | STATE.md `9eaa0252`／experiments_summary.csv `ac28d297`／open_questions.md `dc705103`／verdicts_summary.csv `7b2cc5d9`／tasks_summary.csv `260bbdb1`／followups.md `df792d8b`／results_recent.md `cd8a40df`／inbox.md `e382894f` |
| 退避の残件数 | **2 件**（`stash@{0}` 24件相当・`stash@{1}` 10件）。**どちらも drop していない** |
| philip の定位置分岐 | `exp/philip` は origin に**存在しない**。実体は `exp/philip-wip-20260703`（phase0 と 0 commit 差） |

---

## 起票者の誤り

1. **`asserted_without_measuring`** — SPEC §1「前契約が残した退避は二件」「同期の抑止の目印…
   存在する場合、前契約が解除しなかったことを意味する」。実測では `.sync-pause` は**今回の
   `task-start` が新規作成したもの**（`scripts/task_start.sh:37`「既にあれば触れない」＝作成時は
   無かった証拠）。前契約は `.sync-pause.released` へ正しく解除済みで、退避内に保全されている。
2. **`asserted_without_measuring`** — SPEC §1「philip の定位置分岐」を前提にした Step A-2 の
   「作業ホストの定位置分岐と起点の分岐の差を確かめる」。実測では `exp/philip` は origin に
   **存在しない**。`OPERATION.md` に「実際の分岐切替は別作業」とあるとおり未実施であり、
   実行者は `exp/philip-wip-20260703` を代わりに測った。

---

## 逸脱・想定外・UNKNOWN

### 逸脱

1. **開始前から在った汚れ（8件）を退避してから進めた。** `mv` は使っていない。
2. **`decisions_required` 1 件を利用者へ提示して停止し、回答（判断待ちとして報告に残す）を得た。**
   Phase A の実測を先に済ませ、具体的な項目（`.sync-pause.released` 計2件）を示してから確認した。
3. **禁止領域配下（`experiments/analysis/` 計 28 件）を復帰させていない。** SPEC 指示どおり
   要約値で照合し（全件一致）、結果だけを報告した。触っていない。消していない。

### 想定外

- 🔴 **判定 a の空振り確認で、再生成の成果を一度失った。** `git checkout -- context/auto/STATE.md`
  が「1文字の取り消し」ではなく「未 commit の再生成分ごと HEAD（古い版）への復元」になった。
  **手で直さず** `make context` を再実行して修復（`audit.md:154-163`）。以後は `cp` による
  複製方式へ切り替えた。
- **`stash@{1}` の中身が予想と異なる時系列だった。** 2026-08-26 作成（`error-shape-selectivity`
  契約由来）で、`policy-v2-doc-sync`（2026-08-28）より**前**にできている。SPEC の「前契約が
  残した二件」という時系列の対応は成立しない（起票者の誤り 1 と関連）。

### UNKNOWN

**無し。**

---

## 判断待ち

| 対象 | 経路 | 件数 | 状態 |
|---|---|---|---|
| 抑止解除の名残 | `.sync-pause.released`（0 B） | 2（`stash@{0}` と `stash@{1}` に各1） | **版管理へ記録する規約に当たらない。処分は判断事項のため実行者は決めていない。** 退避内に残置 |

---

## 送出

（この節は commit・PR の後に埋める）

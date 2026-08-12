# RESULT — T-2026-08-11-inbox-per-task-split

**実行者:** `lecun` / `feat/inbox-split` / `origin/phase0` の `11e3575` から分岐
**実行日時:** 2026-08-09T17:34Z 〜 2026-08-09T17:55Z
**判定:** **PASS** — 34 件を無損失で移行し、**旧方式で衝突し新方式で衝突しないことを実際に併合して確認した。**

| 検証 | 結果 |
|---|---|
| 既存の項目が契約ごとの記録へ移された | ✅ 10 ファイル（9 契約 + `_unassigned`） |
| 移行の前後で項目が一件も失われていない | ✅ **34 → 34、本文が完全一致** |
| 集約が冪等 | ✅ 2 回実行して md5 が一致 |
| 手による編集を検出できる | ✅ 陽性対照が失敗（`make` exit 2 / 検査器 exit 1） |
| 並行して別の task が書いても衝突しない | ✅ **実際に併合して確認**（元の記録の衝突 0 件） |
| 起票と実行の手順が新しい置き場を指す | ✅ `tasks/README.md` と `SKILL.md` の両方 |

---

## 1. 解決された参照

| 項目 | spec の記載 | 解決結果 |
|---|---|---|
| `inputs.denominator.ref` | **記載なし** | 対象外（本契約に分母の宣言は無い） |
| `inputs.sigma_policy` | **記載なし** | 対象外（判定を行わない） |
| `inputs.frozen_source.ref` | **記載なし** | 対象外。preflight の `P5` も `kind=impl` のため SKIP |
| `contract.conventions_rev` | `1201f4f` | **`d422b08` へ実測置換**（SPEC Task 5 Step 1 の手順に従う） |
| `contract.inject_verbatim` | `conventions#prohibitions`, `conventions#naming` | 下記に原文を転記 |

### `conventions#prohibitions`（原文）

```
<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

### `conventions#naming`（原文）

```
<a id="naming"></a>
## naming

実験フォルダは手作業で命名せず、`ExperimentManager` が次の規則で自動採番する。

    {step}_{seq:03d}_{description}_seed{seed}

- `step`: `s0`〜`s9`、または `a1`〜`a7`
- `seq`: 同一 category と step 内の3桁ゼロ埋め連番
- `description`: 実験内容の短い説明
- `seed`: 乱数シード。既定42

転記元: `README.md` の「命名規則」。
```

### `conventions_rev` の差分

`1201f4f` → `d422b08` は **+10 / −0**。差分ハンクは `frozen_source` 節（L56 に 9 行）と
変更履歴（L143 に 1 行）の 2 箇所のみ。**原文注入する 2 アンカーはいずれも無変更**
（`prohibitions` L98–108 / `naming` L121–133）。

---

## 2. 実行の前提の確認

SPEC は「受け皿へ追記する未統合の契約が残っていれば停止して報告する」と定める。

`gh pr list --state open` は**空**を返した。件数 0 は測り誤りでも起こるため、
**3 通りで照合した。**

| 方法 | 結果 |
|---|---|
| `gh pr list --state open`（再実行） | 空 |
| `gh pr list --state all --limit 10`（道具が動くかの確認） | 10 件を出力。道具は正常 |
| 既知の番号を直接引く（#51 / #56 / #57 / #58） | #51 は `CLOSED`、他は `MERGED` |

**開いている契約は 0 件であり、前提は充足していた。**
なお #51 は統合されず CLOSED になっている（#52 が派生物を除いた形で置き換えた）。

---

## 3. ゲートの通過状況

| gate | 判定 | 実測 |
|---|---|---|
| **G1**（after A） | **PASS** | 34 → 34、本文が完全一致。重複 0、項目行以外の混入 0 |
| **G2**（after B） | **PASS** | 冪等（md5 一致）。陽性対照が実際に失敗し、再生成で 0 に戻る |
| **G3**（after C） | **PASS** | 旧方式で `CONFLICT`、新方式で元の記録の衝突 0 件 |

---

## 4. 移行の実測

### 4-1. 現状の測定

| 項目 | 実測 |
|---|---|
| `tasks/inbox.md` の行数 | 63 |
| 節の構成 | `# inbox` / `## 様式` / `## 未処理` / `## 処理済み` の 4 見出し |
| 未処理の項目 `- [ ]` | **34** |
| 処理済みの項目 `- [x]` | **0** |
| 項目の書式 | `- [ ] YYYY-MM-DD [面] 内容（参照）` |

### 4-2. 帰属先の判定

| 帰属 | ファイル数 | 項目数 |
|---|---|---|
| 契約の識別子を持つ | 9 | **13** |
| 識別子を持たない（`_unassigned`） | 1 | **21** |
| 計 | **10** | **34** |

**1 行に識別子が 2 つ以上ある項目は 0 件だった**（1 個: 13 行 / 0 個: 21 行）。
SPEC の骨子は `ID.search(line)` で最初の一致を採るが、帰属先は末尾の括弧に書かれる規約なので、
複数あれば別物を拾う恐れがあった。**実測では該当が無く、この懸念は生じなかった。**

### 4-3. 識別子を含まない 21 件の扱い

**`tasks/inbox.d/_unassigned.md` へまとめた。捨てていない。**

これは異常ではない。受け皿の様式は「参照には、**抽出物のパスか**契約の識別子を書く」と定めており、
`（Makefile）` `（PR #51）` `（runindex/index.csv）` のような参照は**様式どおり**である。
したがって識別子を持たない項目が多数派になるのは書式からの当然の帰結である。

衝突回避の観点でも問題は無い。`_unassigned.md` は**移行時点の過去分を収めた凍結された保管先**であり、
今後の契約は自分の `<task_id>.md` へ書くため、ここへの追記は起きない。

### 4-4. G1 — 一件も失われていないことの確認

**件数だけでなく本文で照合した。**

| 検査 | 結果 |
|---|---|
| 移行前の項目数 | **34** |
| 移行後の項目数（`inbox.d/*.md` の合計） | **34** |
| 本文の照合（並び順に依存しない `sort` + `diff`） | **完全一致** |
| 重複（同じ行が 2 ファイルに入っていないか） | 34 行 / 重複除去後 34 行 → **重複なし** |
| 分割ファイルへの項目行以外の混入 | **0 件** |

`entry_lost_during_migration` は発生していない。

### 4-5. 移行後の内訳

| ファイル | 項目数 |
|---|---|
| `T-2026-08-08-session-durability.md` | 2 |
| `T-2026-08-09-run-wiring-verification.md` | 2 |
| `T-2026-08-09-scoped-integration.md` | 1 |
| `T-2026-08-09-wiring-followup-and-integration.md` | 1 |
| `T-2026-08-10-analysis-artifact-integration.md` | 2 |
| `T-2026-08-10-branch-naming-and-canonical-index.md` | 1 |
| `T-2026-08-10-third-host-verification.md` | 1 |
| `T-2026-08-11-identity-tracking-and-harvest-scope.md` | 1 |
| `T-2026-08-11-leftover-relocation.md` | 2 |
| `_unassigned.md` | 21 |
| （本 task の記録）`T-2026-08-11-inbox-per-task-split.md` | 5 |
| 計 | **39** |

移行分は 34 件。本 task 自身の記録 5 件を新方式で追加して 39 件になった。

---

## 5. 集約の仕組み

### 5-1. 試験を先に書いた

`tests/test_build_inbox.py` を先に置き、実装が無い状態で失敗することを確認した。

```
E   ModuleNotFoundError: No module named 'build_inbox'
1 error in 0.18s
```

実装後は **6 試験すべて通過**。

### 5-2. 要件の充足

| # | 要件 | 実装 |
|---|---|---|
| 1 | `tasks/inbox.d/*.md` を読み項目を集める | `collect()` が `sorted(glob("*.md"))` で走査。項目行以外は読み飛ばす |
| 2 | 未処理と処理済みを分けて出力 | `render()` が `- [x]` を処理済みとして分離 |
| 3 | **壁時計を使わない** | 日時を一切出力しない。並び順は「項目の日付 → 由来ファイル名 → ファイル内の出現順」で決定的 |
| 4 | 生成物であり手で編集しない旨を冒頭に | `AUTO-GENERATED` 宣言 + 検査の案内 + 日本語の明示の 3 行 |
| 5 | `--check` で最新かを検査 | 再生成して本文比較。差分時は unified diff を出して 1 を返す |
| 6 | 空のときも落ちない | ディレクトリ不在でも `collect()` は空リストを返す |

**要件 3 が設計の要である。** 既存の `build_context.py` は生成物に `generated_from_date` を
刻むため実行のたびに出力が変わる。それでは `--check` が「手による編集」と「時刻の経過」を
区別できない。本実装は日時を書かないため、**差分が出れば手による編集と断定できる。**

`--check` の骨格（一時領域へ再生成 → 本文比較 → unified diff → 1 を返す）は
`build_context.py:367` の `check()` に揃えた。単一ファイルのため一時ディレクトリは使っていない。

### 5-3. G2 — 冪等と検出

| 検査 | 実測 |
|---|---|
| `make inbox` を 2 回実行した md5 | **一致（冪等 OK）** |
| `make inbox-check`（最新のとき） | **exit 0** |
| 手で 1 行追記したあとの `make inbox-check` | **make exit 2 / 検査器 exit 1** |
| 同上の出力 | unified diff で `- [ ] 手で足した行` を明示 |
| `make inbox` で再生成したあと | **exit 0 に戻る** |

**陽性対照が実際に失敗することを確認した。** 失敗しなければこの検査は無効である。

`make` はレシピ失敗時に自身の終了コード 2 を返すため、検査器そのものの終了コード（1）は
`.venv/bin/python tools/build_inbox.py --check` を直接実行して測った。

---

## 6. 衝突しないことの実演

**「衝突しないはず」では足りないため、実際に併合した。**

### 6-1. 陰性対照 — 旧方式では衝突する

同じ基点（`073f305`）から 2 つの分岐を作り、両方が `tasks/inbox.md` の末尾へ追記した。

```
Auto-merging tasks/inbox.md
CONFLICT (content): Merge conflict in tasks/inbox.md
Automatic merge failed; fix conflicts and then commit the result.
```

衝突ファイル: `UU tasks/inbox.md`。**対照は有効である。**

### 6-2. 新方式 — 元の記録は衝突しない

同じ基点から 2 つの分岐を作り、それぞれ**別のファイル**へ書いた。

| 分岐 | 追加したファイル |
|---|---|
| `probe/new-style-a` | `tasks/inbox.d/T-2026-01-01-probe-a.md` |
| `probe/new-style-b` | `tasks/inbox.d/T-2026-01-02-probe-b.md` |

併合の結果:

| 対象 | 衝突 |
|---|---|
| `tasks/inbox.d/` の全ファイル | **0 件** ✅ |
| `tasks/inbox.md`（集約結果） | **1 件**（想定内） |

**元の記録は衝突しない。** 併合後、両方の probe ファイルが揃っていることも確認した。

### 6-3. 集約結果が衝突した場合の解消手順

**再生成すれば解消する。** 実測した手順は次のとおり。

    git merge <相手の分岐>
    # tasks/inbox.md が CONFLICT になる
    make inbox            # 併合済みの tasks/inbox.d/ から作り直す
    git add tasks/inbox.md
    git commit --no-edit

実測値:

| 段階 | 実測 |
|---|---|
| 解消前の衝突マーカーの数 | 3 |
| `make inbox` 後のマーカーの数 | **0** |
| 未解決の衝突 | **0 件** |
| 併合後の集約結果に両方の追記が載ったか | **両方あり**（18 行目と 19 行目） |
| 併合後の `make inbox-check` | **exit 0** |
| 項目数 | 34 → **36**（両分岐の 1 件ずつが加わった） |

**衝突マーカーを手で消す必要は無い。** 集約結果は派生物であり、
併合済みの `tasks/inbox.d/` から作り直せば正しい内容になる。

`conflict_still_occurs` は発生していない。

### 6-4. 確認用の記録の後始末

| 検査 | 結果 |
|---|---|
| `probe/*` の分岐 | **0 件**（4 本すべて削除） |
| `tasks/inbox.d/` の probe ファイル | **残っていない** |
| 集約結果の項目数 | **34**（実演前の状態に戻った） |
| `make inbox-check` | **exit 0** |

---

## 7. 手順の更新

| ファイル | 変更 |
|---|---|
| `tasks/README.md` | 「判断の受け皿」節を新設。新しい置き場・`make inbox` / `make inbox-check`・衝突時の解消・様式（面の一覧）を記載。「対話の記録」節の `tasks/inbox.md` への参照を新節へ向けた |
| `.claude/skills/task/SKILL.md` | 手順 6「報告する」に受け皿の指示を**追加**。禁止事項に「`tasks/inbox.md` を手で編集しない」を追加 |

**旧 `tasks/inbox.md` にあった様式の表（面の一覧 `app` / `cc` / `cx` / `human`）は
生成物には出力されないため、`tasks/README.md` へ引き継いだ。** これを怠ると
「面 `cc` とは何か」が版管理から消える。

`.codex/skills/task` は `.claude/skills/task` への**シンボリックリンク**であり、
手順書の実体は 1 つである。片方の更新で両実装系に反映される（実測で確認）。

---

## 8. 完了判定

| # | 判定 | 期待 | 実測 |
|---|---|---|---|
| 1 | 項目が失われていない | 完全一致 | ✅ 34 → 34、本文一致 |
| 2 | 帰属先が判定された | 契約ごとにファイル | ✅ 9 契約 + `_unassigned` |
| 3 | 識別子の無い項目も残っている | 存在 | ✅ `_unassigned.md` に 21 件 |
| 4 | 集約が冪等 | 冪等 OK | ✅ md5 一致 |
| 5 | 手による編集を検出 | 非ゼロ → 0 | ✅ exit 2（検査器 1）→ 0 |
| 6 | 旧方式で衝突する | 衝突した | ✅ `CONFLICT (content)` |
| 7 | 新方式で元の記録が衝突しない | 衝突しない | ✅ `inbox.d/` の衝突 0 件 |
| 8 | 確認用の記録が残っていない | 残っていない | ✅ 分岐 0 本・ファイル 0 件 |
| 9 | 手順書が新しい置き場を指す | 該当あり | ✅ README 3 箇所 / SKILL.md 2 箇所 |
| 10 | 自分の記録がある | 1 行以上 | ✅ 5 行 |
| 11 | 契約検証が通る | exit 0 | ✅ exit 0（WARN 2 件は L2-8 の分母変動） |
| 12 | 実行前検査が通る | exit 0 | ✅ 4 PASS / 4 SKIP / 0 FAIL |
| 13 | 試験が不変 | 開始前と比較 | ✅ **前 5 failed, 258 passed → 後 5 failed, 264 passed**。失敗テスト名も同一 |
| 14 | 禁止領域が無変更 | 出力なし | ✅ **出力なし** |

**判定13 の基準点（本 task 開始前・2026-08-09 17:35 実測）**

```
FAILED tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
FAILED tests/test_research_logger.py::test_log_run_idempotent
FAILED tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
FAILED tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
FAILED tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
5 failed, 258 passed, 22 warnings in 25.71s
```

**失敗は 5 件のまま増えていない。** 通過が 258 → 264 に増えたのは、本 task が追加した 6 試験である。

### preflight で SKIP された項目（合格ではない）

| 項目 | 理由 |
|---|---|
| `P2 cuda_ext_loaded` | `plan.env.preflight` に記載なし → **未実施** |
| `P3 deterministic_flags` | `plan.env.preflight` に記載なし → 未実施 |
| `P4 prereg_committed` | `kind=impl` のため対象外 |
| `P5 frozen_source_hash` | `kind=impl` のため対象外 |

本 task は演算装置を使わないため、`P2` `P3` の未実施に実害は無い。

---

## 9. deviations（指示書どおりにしなかった箇所）

### D-1. SPEC が自己矛盾していた（`tasks/README.md` の扱い）

- **指示:** §0「並行して進む作業との衝突を避ける」は `tasks/README.md` を
  「**触らないこと**」とし、「本 task が触るのは、このホストのディスクと
  自分の契約ディレクトリのみである」と結ぶ。
  一方 Task 4 は `Modify: tasks/README.md` を指定し、完了判定 9 は
  `grep -n "inbox.d" tasks/README.md` に該当があることを要求する。
- **実際:** 利用者へ提示し、**Task 4 に従って更新する**判断を得た。
- **根拠:** §0 の当該節は前 task（退避作業）からの写し取りと読める。閉じの一文は
  `tools/build_inbox.py` `tests/` `Makefile` を作る本 task の実態と矛盾する。
  また開いている PR は 0 件で、実際に奪い合う相手はいなかった。
- **分類:** **SPEC の欠陥**

### D-2. 手順書には受け皿の指示が元から無かった

- **指示:** Task 4 Step 2「**受け皿へ書く指示を、新しい置き場へ変える**」
- **実際:** `.claude/skills/task/SKILL.md` に `inbox` も「受け皿」も**存在しなかった**。
  3 通りで確かめた（`inbox` の検索 / 見出し一覧 / 関連語の検索）。
  変更すべき記述が無いため、手順 6 に**新規に追加**した。
- **判明した構造:** 受け皿へ書く指示は各 SPEC 側（起票者が書く本文）にあり、
  実装系の手順書には無かった。
- **分類:** **SPEC の欠陥**（変更ではなく追加が必要だった）

### D-3. 試験コードから未使用の import を除いた

- **指示:** SPEC が示した `tests/test_build_inbox.py` は `import pytest` を含む
- **実際:** この試験群で `pytest` は使われておらず（`tmp_path` は fixture 名で解決され、
  `raises` も marker も無い）、`ruff` が F401 を出す。**削除した。**
- **測定:** 着手前の `ruff check tests/` は既に 1 件の指摘を持つ（`test_branch_naming.py` の
  I001。別ホストの作業由来）。私のファイルはそこに 2 件目を足す形だった。
  削除後は本ファイル単体で `All checks passed`。
  **既存の I001 は範囲外のため触っていない。**
- **分類:** **判断が必要だった**

### D-4. 実装から不要な一時ディレクトリを除いた

- **実際:** `check()` を `build_context.py` に揃える過程で
  `with tempfile.TemporaryDirectory():` を写したが、単一ファイルの比較には不要である。
  除去し、`tempfile` の import も外した（残すと F401 になる）。
- **分類:** **判断が必要だった**

### D-5. 一時ファイルの置き場を変えた

- **指示:** `/tmp/inbox_migration/`
- **実際:** 本セッションの作業領域へ置いた。機能は同一。
- **分類:** **環境差**

### D-6. `conventions_rev` を実測値へ置換した

- **指示:** SPEC Task 5 Step 1 が「実行者が実測して置換する。**これは逸脱ではなく手順である**」と明記
- **実際:** `1201f4f` → `d422b08` に更新した
- **分類:** 手順どおり（記録のため列挙）

### 事前の懸念が外れた点（逸脱ではないが記録する）

分割の骨子が `ID.search(line)`（最初の一致）を使うため、
1 行に識別子が複数あれば末尾の帰属先ではなく先頭の別物を拾うと予想した。
**実測では識別子が 2 つ以上ある行は 0 件で、この懸念は生じなかった。**

また `.claude` と `.codex` の `SKILL.md` を当初「ハードリンク」と述べたが、
実体は `.codex/skills/task` が `.claude/skills/task` を指す**シンボリックリンク**である。

---

## 10. 未解決・申し送り

### 10-1. 既に開いている契約が旧方式で追記している場合の扱い

**本 task の着手時点では開いている契約が 0 件だったため、この問題は起きなかった。**
ただし今後、本 task の統合前に起票された契約が `tasks/inbox.md` へ直接追記して
統合されると、次のことが起きる。

| 事象 | 結果 |
|---|---|
| その追記は `tasks/inbox.d/` に無い | 次の `make inbox` で**集約結果から消える** |
| `make inbox-check` | 差分を検出して**失敗する** |

**復旧は容易である。** 消えた行は git の履歴に残っているため、
該当行を `tasks/inbox.d/<task_id>.md` へ移してから `make inbox` を実行すればよい。

    git show <統合前の commit>:tasks/inbox.md | grep '^- \['

**推奨は、本 task の統合を他の契約より先に済ませること。**
統合後に起票される契約は、更新済みの手順書が新しい置き場を指すため問題にならない。

### 10-2. SPEC 側の重複した指示

受け皿へ書く指示は各 SPEC の本文にも書かれている（本 task の Task 5 Step 6 など）。
手順書へも追加したため、**同じ指示が 2 箇所に存在する。**
SPEC 側の記述をやめて手順書に一本化するかは未決。

### 10-3. 生成物の日時の扱いが道具間で揃っていない

`tools/build_inbox.py` は日時を書かない（`--check` が手による編集を断定できるようにするため）。
一方 `tools/build_context.py` は生成物に `generated_from_date` を刻む。
**方式が揃っていない。** `context-check` が時刻の経過をどう扱っているかは本 task では未測定。

### 10-4. `_unassigned.md` の 21 件をどう扱うか

移行時点の過去分を凍結した保管先である。契約へ結びつかないため、
週次の棚卸しで昇格・破棄を判断する際の単位が粗い。分割し直すかは未決。

---

## 11. 数値の出所

**すべての数値は本ホスト（lecun）での実測である。** 未測定の項目は無い。
未測定と判断した事項（`context-check` が時刻の経過をどう扱うか）は
**未測定と明記**しており、推測で補っていない。

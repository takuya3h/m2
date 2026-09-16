# audit — T-2026-09-17-fold-table

実行ホスト: `lecun`（`/home/ubuntu/slocal/m2`）。対話シェルは zsh。分岐 `feat/fold-table`（起点 `origin/phase0` = `b2b8d580`）。
命令はすべて読み込みを同じ命令に含めた（`source .venv/bin/activate && ...`）。履歴は `git --no-pager` で読んだ。

## 1. 開始状態

    git status --short | wc -l        → 33（追跡下の削除 31 / 未追跡 2）
    git stash push -m "pre-T-2026-09-17-fold-table: 31 deletions"
    git stash push -u -m "pre-T-2026-09-17-fold-table: untracked 2件"
    git status --porcelain | wc -l    → 0

退避は 2 件の stash。`task_start.sh` は `git status --porcelain` が非ゼロなら exit 3 で止まる実装のため、
未追跡 2 件も退避が要った（repo 外への移動ではなく stash を選んだ。SPEC Task A-1 が許している）。

| stash | 名前 | 件数 |
|---|---|---|
| `stash@{0}` | `pre-T-2026-09-17-fold-table: untracked 2件` | 2（`.sync-pause.released`、`docs/sessions/digest/2026-08-29-23fa444b-….md`）|
| `stash@{1}` | `pre-T-2026-09-17-fold-table: 31 deletions` | 31（`experiments/analysis/**/*.py` 23 件、`experiments/transfer/**/logs/*.json` 8 件）|

前契約の stash も残っている。**本契約は触れていない**（SPEC 申し送り）。

    git stash list | wc -l            → 4（うち本契約が 2、前契約が 2）

## 2. 取り込みと検証

    source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-09-17-fold-table
      → git fetch origin / 分岐 feat/fold-table 作成 / .sync-pause 作成 / OK T-2026-09-17-fold-table

    make task-validate TASK=T-2026-09-17-fold-table   → OK / 1 task(s), 0 failed / exit 0（WARN なし）

L2-6 の WARN は**出なかった**。SPEC §2 は「規約ファイルが変わると全契約に出る」と述べるが、
本契約の検証は規約ファイルを変える**前**に行ったためである。

### 同期抑止

    ls -la .sync-pause                 → 0 バイト（task_start.sh が作成、19:53）
    grep -c sync-pause ~/bin/m2-sync.sh → 2（0 ではないので稼働版は対応済み）
    grep '一時停止中' ~/claude-sync/sync-alerts.log | tail -2
      → 2026-09-16 15:21:03 [lecun] 一時停止中: /home/ubuntu/slocal/m2/.sync-pause があるため分岐へ書き込まない

## 3. プリフライト（L3）

一度目（占位のまま）:

    P6 decisions_answered  FAIL 未回答 2 件
    RESULT: 5 PASS / 0 WARN / 6 SKIP / 1 FAIL       ← ここで停止して利用者に諮った

SKIP の一覧: P2 cuda_ext_loaded / P3 deterministic_flags（`plan.env.preflight` に記載なし）、
P4 prereg_committed / P5 frozen_source_hash（`kind: impl` のため対象外）、
P11 gpu_free（記載なし）、P12 refs_resolved（解決前提の参照なし）。

利用者の回答を `spec.yaml` の `meta.amendments` と `tasks/inbox.d/` に記録し、`decisions_required` を空にしてから二度目:

    RESULT: 6 PASS / 0 WARN / 6 SKIP / 0 FAIL / exit 0

## 4. Task A — 材料と公式分割（Gate G1）

材料は A1 の表を写さず、**同じ出所から読み直した**（`scripts/analysis/a1_fold_table.py` の `load_*`）。

    工程CSVの動画 15 / 術具COCOの動画 15 / HTSの動画 15
    公式分割の合計 15（train 10 / val 2 / test 3）
    G1-a 公式分割の合計が15か: True
    G1-b 工程 vs 公式 集合差: [] → 0 件
    G1-c 術具 vs 公式 集合差: [] → 0 件
    G1-d HTS  vs 公式 集合差: [] → 0 件
    工程の種類: 9（anesthesia closure design disinfection dissection dressing hemostasis incision irrigation）
    術具クラス数: 15
    総フレーム: 17233 / 総images: 15437 / 総boxes: 49652
    追加動画: ['17', '18', '19', '20', '21', '22']
    HTS 3系統すべて: 15 動画すべて True

総フレーム・images・boxes は `docs/stage0/A1_fold_material.md` の合計行（17233 / 15437 / 49652）と一致した。
**独立に読み直して一致したので、A1 の材料は写し誤りを含まない。**

`escalate_if` の 2 条件（材料の欠落・合計が 15 でない）はいずれも**該当しなかった**。**Gate G1 通過。**

### 実測した値（Task A-5）

    git --no-pager log -1 --format='%h' -- context/conventions.md   → 4300b7d2
    git --no-pager log -1 --format='%h' -- runindex/                → 96eb3a1c
    grep -c '<a id=' context/conventions.md                         → 9（追記後 10）
    runindex 行数（ヘッダ除く）: index 1266 / experiments 285 / verdicts 1506

`spec.yaml` の占位 `REPLACE-BY-EXECUTOR-*` 2 件を上の実測値へ差し替え、`meta.amendments` に記録した。

## 5. Task B — 折り表（Gate G2）

生成器は `scripts/analysis/a1_fold_table.py`。**乱数は対照でのみ使い、表の生成には使わない。**
12 動画を 3 本ずつ 4 組へ分ける分け方を**全数列挙**（15400 通り）したため、選ばれた表は近似ではなく最適である。

    python scripts/analysis/a1_fold_table.py --write
      → 書きました: docs/stage0/A1_fold_table.md（7297 バイト）
      → 表の要約値: 237837faa843e1b3da77f669039129e5ffbfde732f3a7869d07756206746976b

| 折り | test | val | train |
|---|---|---|---|
| A | 04, 05, 07 | 09, 10 | 01, 02, 03, 06, 08, 11, 12, 13, 14, 15 |
| B | 01, 03, 14 | 02, 08 | 04, 05, 06, 07, 09, 10, 11, 12, 13, 15 |
| C | 02, 08, 11 | 06, 12 | 01, 03, 04, 05, 07, 09, 10, 13, 14, 15 |
| D | 06, 13, 15 | 04, 05 | 01, 02, 03, 07, 08, 09, 10, 11, 12, 14 |
| E | 09, 10, 12 | 07, 15 | 01, 02, 03, 04, 05, 06, 08, 11, 13, 14 |

均衡指標 `d(S) = TV(工程比率, 全体) + TV(術具クラス比率, 全体)`。選び方は
`max_f d(test_f)` → `sum_f d(test_f)` → 動画識別子の辞書順。**同点は 1 通りだったので辞書順の出番は無く、
利用者へ諮る条件（decisions_required 1 件目）は発生しなかった。**

| 折り | d(test) |
|---|---|
| A（固定・最適化対象外） | 0.2966 |
| B | 0.2844 |
| C | 0.2628 |
| D | 0.2667 |
| E | 0.2811 |

折り B〜E の最大 0.2844 / 最小 0.2628 / **最大差 0.0216**。5 折り込みでは最大差 0.0338。

### 無作為対照

    seed = 20260917（random.Random(seed).shuffle）
    提案の表   max d = 0.2844 / sum d = 1.0951
    無作為     max d = 0.6102 / sum d = 1.6287   → **悪化していない**

全数列挙しているため分布全体とも比べられる。15400 通りの `max d` は最小 0.2844 / 中央 0.5246 / 最大 0.7972。
**提案の表は最小値そのもの**（全体の最良）である。

### 制約検査の対照（`--controls` の出力全文）

```
OK  提案の表（陰性対照。落ちてはならない）: 違反 0 件 / —
OK  同じ動画 02 を折り B と C の test に置く: 違反 4 件 / 動画 02 が test に現れた回数が 1 でない: ['B', 'C']
OK  折り A の test の一本を 01 へ入れ替える: 違反 5 件 / 折り A の test が公式 test と一致しない: ['01', '04', '05']
OK  折り A の val の一本を入れ替える: 違反 3 件 / 折り A の val が公式 val と一致しない: ['01', '09']
OK  折り B の val に自分の test の動画を入れる: 違反 2 件 / 折り B: val が test と重なる ['01']
OK  折り C の val を折り D と同じにする: 違反 4 件 / 動画 04 が val に 2 回以上現れる: ['C', 'D']
OK  折り E の test を 2 本に減らす: 違反 3 件 / 折り E: test が 3 本でない（2 本）
```

**件数だけでは「別の理由で落ちた」と区別できない。** 狙った違反の文言そのものを照合し、7 件すべてで一致した。

### 決定性（Gate G2）

```
digest_1          237837faa843e1b3da77f669039129e5ffbfde732f3a7869d07756206746976b
digest_2          237837faa843e1b3da77f669039129e5ffbfde732f3a7869d07756206746976b
identical         true
perturbation      動画 01 の工程 anesthesia に +100000 フレーム（記憶上のみ。data/ は書き換えない）
digest_perturbed  febee3775bec5785d7d8d55913d558cc5ad7075c33bd7d9d032f1e79380f0902
changed           true
```

ファイル水準でも確かめた。

    sha256sum docs/stage0/A1_fold_table.md   → eb66170a8565b993…（一度目）
    python … --write                          （二度目）
    sha256sum docs/stage0/A1_fold_table.md   → eb66170a8565b993…（一致）
    diff -q first.md docs/stage0/A1_fold_table.md → 差分なし

**Gate G2 通過。**

### 追加 6 動画（decisions_required 2 件目）

```json
{"extra": ["17","18","19","20","21","22"], "n_extra": 6,
 "overlap_15": [], "overlap_official_test": [], "overlap_official_val": [], "overlap_official_train": [],
 "positive_control_injected": "04", "positive_control_overlap": ["04"]}
```

重複 0 件。**陽性対照**として追加動画の集合へ `04` を混ぜると重複 1 件になり、集合演算が働いていることを示した。
`docs/stage0/A2_id_overlap.md` の既報（0 件・陽性対照 1 件）と一致する。**重複が無いので停止条件は発生しなかった。**

repo に Phase 専用の分割ファイルは存在しない（`find data -iname "*split*"` は `data/splits` のみ、
生データ側にも phase 用の train/test 一覧は無い）。したがって「Phase 公式 test」に対応する実体は
`data/splits/ego_test.txt` であり、A2 と同じ解釈を採った。

## 6. Task C — conventions.md の folds 節

    行数 260 → 297（+37）
    sha256 47e899d00a9c4473… → de3f25ffeb97f63b…
    アンカー 9 → 10（末尾に folds を追加）
    git diff --stat  → 1 file changed, 37 insertions(+)
    git diff | grep -c '^-[^-]'  → 0    ← **削除行 0。既存節の本文は無変更**

`folds` 節に置いたもの: 折り表（折り／test／val）、追加 6 動画の一覧と用途（訓練のみ・test にも val にも現れない）、
規律の一文（選定・early stopping・ハイパラ・界面の型の選択は折り内 val、test は腕ごとに一度）、
出所（`docs/stage0/A1_fold_table.md`、`T-2026-09-17-fold-table`）。

変更履歴には 2 行を足した（残件②の `a8c07e81` と本契約の行）。本契約の commit 欄は、
本体の commit が確定するまで `PENDING` とし、確定後に `537c968c` を埋めた（commit `e7a51005`）。

### 完了判定 g の検証

    conventions_anchors() → ['env_p0','eval_recipe','folds','frozen_source','issuer_cautions',
                             'naming','prohibitions','proposal_gate','sigma','split']
    "folds"    in anchors → True
    "folds_zz" in anchors → False   ← 陰性対照。存在しないアンカーは引けない

表の突き合わせ（`| 折り | test | val |` を両ファイルから抜いて比較）:

    conventions#folds  {'A': ('04, 05, 07','09, 10'), 'B': ('01, 03, 14','02, 08'),
                        'C': ('02, 08, 11','06, 12'), 'D': ('06, 13, 15','04, 05'),
                        'E': ('09, 10, 12','07, 15')}
    docs/A1_fold_table {同一}
    差分の行数: 0

## 7. Task D — 残件三つ

### D-1 docs_audit への登録

    make docs-check（前）→ [docs-check] 対象 42 文書 / Makefile のターゲット 34 件 / 食い違いなし
    docs/docs_audit.md に `| docs/proposal-gate.md | 現行手順 | 提案の関門の手順。静的検査は tools/check_proposal.py |` を追加
    本文の「42 件を現行手順とした」の直後に、本契約で 43 件になった旨を追記
    make docs-check（後）→ [docs-check] 対象 43 文書 / Makefile のターゲット 34 件 / 食い違いなし / exit 0

### D-2 変更履歴の欠落行

`a8c07e81` の実在を先に確かめた。

    git --no-pager log -1 --format='%h %ad %s' --date=short a8c07e81
      → a8c07e81 2026-08-25 feat(context): move issuer references into version control and inject the cautions
    git --no-pager show --stat a8c07e81 | grep conventions
      → context/conventions.md | 35 ++      ← issuer_cautions 節の追加に相当する

日付順の正しい位置（`290da51`（2026-08-07）と `6c95e4f`（2026-09-16）のあいだ）へ挿入した。既存行は変えていない。

### D-3 issuer-defects への 4 件

まず**生成物でないこと**を確かめた。

    generated_locations() → ディレクトリ ['context/auto/'] / ファイル ['tasks/inbox.md']
    'docs/issuer-defects.md' はどちらにも該当しない → 手編集してよい（escalate_if は発生せず）

4 件それぞれの実体を、出所の RESULT ではなく**実装と契約本文**で確かめた。

| # | 主張 | 確かめ方 | 結果 |
|---|---|---|---|
| 1 | 規約への追記を命じつつ `allow_write` 未宣言 | `FORBIDDEN_FILES` に `context/conventions.md` があるか | あり。前契約 RESULT §4-1 と inbox.d が実行者による補いを記録 |
| 2 | L2-6 は `inject_verbatim` を見ない | `_warn_conventions_rev` 内の `grep -c inject_verbatim` | **0**（読んでいない） |
| 3 | repo に無い報告のファイル名とバイト数を要求 | 前契約 SPEC:52 の指示と `git ls-files \| grep -ci deep.research` | 指示あり／該当ファイル **0 件** |
| 4 | 付録に無い節を完了判定で要求 | 前契約 SPEC:89（判定 e）と付録の節見出し | 判定 e は両地図に要求。付録は **A.3 のみで B に該当節なし** |

    git diff --stat docs/issuer-defects.md → 4 insertions(+)
    git diff docs/issuer-defects.md | grep -c '^-[^-]' → 0（既存行は無変更）

型ごとの節へ振り分けた（self_contradiction の 2 件 → 「禁止と要求が両立しなかった」、
asserted_without_measuring の 2 件 → 「測らずに断定した」）。日付は各行に `2026-09-16。` として入れた。

**出所と契約の記載に食い違いがあった**（§9 の起票者の誤り 5 件目）。契約の指定した型で書き、食い違いを記録した。

## 8. Task E — 検証

| 検査 | 結果 | 終了コード |
|---|---|---|
| `make task-validate TASK=…`（L1+L2） | OK / 1 task(s), 0 failed | 0 |
| `make task-preflight TASK=…`（L3） | 6 PASS / 0 WARN / 6 SKIP / 0 FAIL | 0 |
| `make spec-check TASK=…` | `status: pass` / `rules_checked: 8` / 該当 0 | 0 |
| `make docs-check` | 対象 43 文書 / 食い違いなし | 0 |
| `python -m pytest tests/ -q` | **6 failed / 535 passed** | 1 |
| `check_forbidden.py --task …` | `permitted` 1 件 / `violations` **7 件** | 1 |

### 試験の 6 件について

直前契約 `T-2026-09-16-proposal-gate` の RESULT が記録した基準は **6 failed / 535 passed**。
本契約も **6 failed / 535 passed** で、**失敗の増減は 0**、顔ぶれも同じである。

    tests/test_research_logger.py の 4 件 — docs_audit.md:132 が既知として記録（B-40、origin/phase0 時点から失敗）
    tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics — experiments/ の metrics を走査し
      NMS-free の run が score_thr=0.0 を持つため落ちる。**experiments/ の内容に依存し、本契約は同領域に触れていない**
    tests/test_fetch_task.py::test_rejects_unknown_file_name — 実装の文言「経路として受け取れない名前です」と
      試験の期待「受け取れないファイル」の食い違い。**実装側の drift**

失敗した 3 ファイルのいずれも、本契約が変えた `context/conventions.md` `docs/docs_audit.md`
`docs/issuer-defects.md` `docs/stage0/A1_fold_table.md` `scripts/analysis/a1_fold_table.py` を参照しない
（`grep -l` の該当 0 件）。

### forbidden-check の violations 7 件

```
permitted:  [{"path": "context/conventions.md", "reason": "契約の allow_write context/conventions.md により許可"}]
violations: experiments/analysis/hts_candidate_acceptance/.syncthing.{apply_criteria,hand_count,make_outputs,scan_candidates}.py.tmp
            experiments/analysis/official_split_reassessment/.syncthing.{controls,inventory,juxtapose}.py.tmp
```

`permitted` は要求どおり `context/conventions.md` **1 件**。`violations` の 7 件は**すべて syncthing の一時ファイル**である。

素性の確認:

    pgrep -a syncthing        → 140103 /home/ubuntu/bin/syncthing serve --no-browser（稼働中）
    find … -printf '%T+ %s %p' → 7 件とも mtime 2026-09-16 20:06:26、8 分後も変化なし（停滞＝転送は完了済み）
    cmp .syncthing.X.py.tmp X.py → 3 件すべて **同一**（本体が復元済みで、一時ファイルは取り残された孤児）

経緯は、開始時に stash した 31 件の削除（`experiments/analysis/**/*.py` を含む）を syncthing が
他ホストから復元し、その際の一時ファイルが残ったものである。**実行者が作ったファイルではない。**

SPEC §4 前文は「**禁止は実行者の操作に対するものであり、同期処理による配布を含まない**」と定める。
また禁止事項 4 は `experiments/**` に触れることを禁じる。**削除は禁止事項 4 に当たるため行わず、記録した。**

## 9. 起票者の誤り

§7 の D-3 で追記した 4 件とは別に、**本契約自身の誤りが 1 件**ある。

`asserted_without_measuring` — SPEC Task D-3 は 4 件の出所を
`T-2026-09-16-evidence-map-ab/RESULT.md §4・§5` と書くが、**当該 §4 は「起票者の誤り **無し**」と述べており**、
3 件目は §4 の「補足（誤りではない）」、4 件目は §5 の「逸脱 2（judgement）」である。
また 2 件目の型を `asserted_without_measuring` と指定するが、出所の
`T-2026-09-16-proposal-gate/RESULT.md §4-2` は **`check_does_not_check`** と分類している。
内容自体はいずれも実測で裏が取れたため契約の指定どおり書き、食い違いをここに記録する。

## 10. 変更範囲

    commit 537c968c（本体）
      context/conventions.md | 37 +++++++++++++++++++++++++++++++++++++
      docs/docs_audit.md     |  2 ++
      docs/issuer-defects.md |  4 ++++
      3 files changed, 43 insertions(+)   ← **削除行 0**
      docs/stage0/A1_fold_table.md / scripts/analysis/a1_fold_table.py /
      tasks/T-2026-09-17-fold-table/ / tasks/inbox.d/T-2026-09-17-fold-table.md を新規で加え、
      合計 11 files changed, 1655 insertions(+)

    commit e7a51005（PENDING の解消）
      context/conventions.md の変更履歴の commit 欄と spec.yaml の conventions_rev を 537c968c へ

    禁止領域の混入: git diff --cached --name-only | grep -cE '^(experiments|data|runindex|context/auto|transfer)/' → **0**
    syncthing の一時ファイル 7 件は staging していない

    git push -u origin feat/fold-table        → [new branch] / exit 0
    gh pr create --base master                → **PR #176**（draft=false / state=OPEN）

    新規（未追跡）
      docs/stage0/A1_fold_table.md          折り表の正本（7297 バイト）
      scripts/analysis/a1_fold_table.py     生成器・制約検査・対照
      tasks/T-2026-09-17-fold-table/        契約と報告

    触れていない（禁止事項）
      data/splits/**  data/raw  data/processed  experiments/**  runindex/**
      context/auto/**  tasks/inbox.md  既存の tasks/*/

生成器を `tools/` ではなく `scripts/analysis/` に置いた理由は 2 つある。同ディレクトリが解析用スクリプトの
既存の置き場であること、および SPEC 申し送りが並行契約 `T-2026-09-17-tier1-cost-estimate` に
「`tools/` の新規一件」を割り当てており、生成物の分離を保つためである。

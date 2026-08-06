# runindex から軽量ビューを生成し、外部の面が実測値を読めるようにする

**task_id:** `T-2026-08-06-make-context`
**kind:** `impl`
**depends_on:** `T-2026-08-06-frozen-source-and-sigma-notation`（PR #44・マージ済み）

---

## Goal

`runindex/` は数値の正本だが大きすぎて外部の面（Claude アプリのプロジェクト知識）に載らない。
実測では `runindex/` 単体でプロジェクト容量の 107% を占める。

本 task は、`runindex` から**軽量ビュー `context/auto/` を冪等に生成**し、外部の面が
実験の実測値を読めるようにする。あわせて、契約と run を結ぶ `task_id` 列を収穫器へ追加する。

これが完成すると、起票から結果確認までの輪が初めて閉じる。

## 設計原則

| # | 原則 | 帰結 |
|---|---|---|
| 1 | **判断は載せない** | `STATE.md` は数値の現在地のみ。主軸・確定結論は人が書く `context/plan_mirror.md` の役目であり本 task の範囲外 |
| 2 | **生成物と手編集物をディレクトリで分ける** | `context/auto/` は自動生成。`context/` 直下は人手管理（`conventions.md` など） |
| 3 | **冪等** | 二度実行して差分ゼロ。壁時計を使わない |
| 4 | **容量に上限を置く** | 外部の面に載らなければ意味が無い |
| 5 | **推測しない** | 列名・行数は必ず実測してから実装する |

### 冪等性と鮮度の両立

生成物には「いつの状態か」を示す必要があるが、壁時計を書くと実行のたびにハッシュが変わり
冪等性が壊れる。**壁時計ではなく HEAD のコミット日時と commit を使う**ことで両立させる。

```
generated_from_commit: <HEAD の sha>
generated_from_date:   <HEAD のコミット日時>
runindex_counts:       index=<N> experiments=<N> verdicts=<N>
```

同じ repo 状態なら何度生成しても同一になり、かつ外部の面は「どの状態を見ているか」を
判定できる。

---

## 0. 前提と禁止事項

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git checkout -b feat/make-context origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | `runindex/**` の生成物を手で編集する |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 3 | 学習・評価コードを変更する |
| 4 | `context/conventions.md` を変更する（人手管理・本 task の範囲外） |
| 5 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 6 | 生成物に人の判断・解釈・評価を書く |
| 7 | テスト件数を合わせるためだけのテストを足す |

### 本 task に限り解禁するもの

**`tools/harvest_runindex.py` の変更を解禁する。** 過去3本の SPEC では PR 衝突を避けるため
禁止していたが、`task_id` 列の追加は収穫器を通さなければ実現できない。ただし Task 1 で
**他ホストの未マージ変更が無いことを確認してから**着手する（G1）。

---

## Task 1: 実測による事前確認（Phase A）

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 収穫器に対する並行作業の有無を確認する（G1 ゲート）**

```bash
gh pr list --state open --json number,title,headRefName,files \
  --jq '.[] | {n:.number, t:.title, b:.headRefName}'
echo "--- 収穫器を触っている open PR ---"
for n in $(gh pr list --state open --json number --jq '.[].number'); do
  if gh pr view "$n" --json files --jq '.files[].path' | grep -q "harvest_runindex.py"; then
    echo "PR #$n が harvest_runindex.py を変更しています"
  fi
done
echo "--- 他ホストのブランチ ---"
git for-each-ref --format='%(refname:short) %(committerdate:short)' refs/remotes/origin | sort -k2 -r | head -20
```

**収穫器を触っている open PR があれば停止して報告する**（`concurrent_harvester_change`）。
Task 2 の変更が衝突し、`runindex` の再生成が二重に走る危険がある。

- [ ] **Step 2: 現在の母集団を実測する**

```bash
make runindex 2>&1 | tail -20
echo "--- 行数 ---"
for f in index experiments per_class verdicts; do
  printf "%s: %s\n" "$f" "$(($(wc -l < runindex/$f.csv) - 1))"
done
echo "--- 除外内訳 ---"
python - <<'PY'
import csv, collections
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
print("列数:", len(cols))
ex_cols = [c for c in cols if "exclud" in c.lower()]
print("除外に関係しそうな列:", ex_cols)
for c in ex_cols:
    print(f"  {c}:", dict(collections.Counter(r.get(c, "") for r in rows).most_common(10)))
PY
```

**出力された除外理由の列名を控える。** 前 task で私のヒューリスティックが列を特定できず
`wrong_frozen_source` 3件が `UNKNOWN` のまま残った。**同じ誤りを繰り返さないこと。**
以降の実装では、ここで確認した実際の列名を使う。

- [ ] **Step 3: 他の CSV の列名を実測する**

```bash
python - <<'PY'
import csv
for name in ["experiments.csv", "verdicts.csv", "per_class.csv"]:
    with open(f"runindex/{name}", newline="", encoding="utf-8") as fh:
        cols = next(csv.reader(fh))
    print(f"=== {name}: {len(cols)} 列 ===")
    print(cols)
PY
```

- [ ] **Step 4: `verdicts.csv` の粒度を実測する**

`verdicts.csv` は 1038 行ある。1 実験あたり複数指標の行があるはずで、そのままでは軽量ビューに
載らない可能性がある。**主指標だけに絞れるかを確認する。**

```bash
python - <<'PY'
import csv, collections
rows = list(csv.DictReader(open("runindex/verdicts.csv", encoding="utf-8")))
cols = list(rows[0].keys())
print("列:", cols)
for c in cols:
    vals = collections.Counter(r.get(c, "") for r in rows)
    if 1 < len(vals) <= 12:
        print(f"  {c}: {dict(vals.most_common(12))}")
print("行数:", len(rows))
PY
```

- [ ] **Step 5: `BACKLOG` の構造を確認する**

`open_questions.md` の生成元になる。

```bash
python - <<'PY'
import ast, pathlib, re
src = pathlib.Path("tools/harvest_runindex.py").read_text(encoding="utf-8")
m = re.search(r"^BACKLOG\s*=\s*", src, re.M)
print("BACKLOG の定義:", "あり" if m else "なし")
if m:
    print(src[m.start():m.start()+400])
PY
```

- [ ] **Step 6: 実測値をすべて控える**

RESULT §1 に、除外理由の列名・各 CSV の列名・`verdicts.csv` の粒度・`BACKLOG` の形式を記録する。
**以降の Task はこの実測に基づく。推測で進めない。**

---

## Task 2: 収穫器に `task_id` 列を追加（Phase B）

**Files:**
- Modify: `tools/harvest_runindex.py`
- Modify: `tests/`（既存の収穫器テストがあれば追随）

契約と run を結ぶ鍵。現時点で `task_id` を持つ run は存在しないため、**全行が空になるのが正常**。

- [ ] **Step 1: 変更前の状態を保存する**

```bash
mkdir -p /tmp/ctx_before
cp runindex/index.csv runindex/experiments.csv /tmp/ctx_before/
python - <<'PY'
import csv, collections, json
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
ex = [c for c in cols if "exclud" in c.lower()]
snap = {
    "index_rows": len(rows),
    "index_cols": len(cols),
    "exclude_breakdown": {c: dict(collections.Counter(r.get(c, "") for r in rows)) for c in ex},
}
json.dump(snap, open("/tmp/ctx_before/snapshot.json", "w"), ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in snap.items() if k != "exclude_breakdown"}, ensure_ascii=False))
PY
```

- [ ] **Step 2: `config.yaml` からの読み取りを実装する**

run ごとの `config.yaml` を読んでいる既存箇所に、`task_id` の抽出を足す。

- キーはトップレベルの `task_id`
- 無ければ空文字（`UNKNOWN` にしない。**未設定と未測定は違う**）
- `index.csv` の列に `task_id` を追加する

- [ ] **Step 3: `experiments.csv` へ集約する**

1 実験に複数 run があるため、**distinct な `task_id` をカンマ結合**する。既存の `hosts` や
`arm` と同じ扱いにする。列名は `task_ids`（複数形）とし、`index.csv` の `task_id`（単数）と
区別する。

- [ ] **Step 4: 再生成して回帰を確認する（G2 ゲート）**

```bash
make runindex 2>&1 | tail -20
python - <<'PY'
import csv, collections, json
before = json.load(open("/tmp/ctx_before/snapshot.json"))
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
ex = [c for c in cols if "exclud" in c.lower()]
after = {
    "index_rows": len(rows),
    "index_cols": len(cols),
    "exclude_breakdown": {c: dict(collections.Counter(r.get(c, "") for r in rows)) for c in ex},
}
print("行数:", before["index_rows"], "->", after["index_rows"],
      "OK" if before["index_rows"] == after["index_rows"] else "NG")
print("列数:", before["index_cols"], "->", after["index_cols"],
      "OK" if after["index_cols"] == before["index_cols"] + 1 else "NG")
print("除外内訳 不変:", before["exclude_breakdown"] == after["exclude_breakdown"])
print("task_id 列:", "task_id" in cols)
print("非空の task_id:", sum(1 for r in rows if r.get("task_id")))
PY
```

Expected: 行数不変 / 列数 +1 / 除外内訳 不変 / `task_id` 列あり / 非空 0 件

**一つでも NG なら停止して報告する**（`index_row_count_changed`）。

- [ ] **Step 5: 冪等性を確認する**

```bash
md5sum runindex/*.csv > /tmp/h1.txt
make runindex >/dev/null 2>&1
md5sum runindex/*.csv > /tmp/h2.txt
diff /tmp/h1.txt /tmp/h2.txt && echo "IDEMPOTENT OK" || echo "IDEMPOTENT NG"
```

- [ ] **Step 6: commit**

```bash
git add tools/harvest_runindex.py runindex/
git commit -m "feat(runindex): add task_id column linking contracts to runs"
```

---

## Task 3: `STATE.md` の生成（Phase C）

**Files:**
- Create: `tools/build_context.py`

`STATE.md` は**数値の現在地のみ**。300 行以内。人の判断・解釈・評価を書かない。

- [ ] **Step 1: 生成する内容を決める**

| 節 | 内容 | 出所 |
|---|---|---|
| ヘッダ | 自動生成の宣言、`generated_from_commit`、`generated_from_date`、各 CSV の行数 | git, CSV |
| 母集団 | 総 run 数、除外数と**内訳**、host 別内訳 | `index.csv` |
| 実験 | 総数、`control_of` を持つ数、group 別内訳 | `experiments.csv` |
| 判定 | `verdict_10_1` の値別件数、母集団σと標本σの一致率 | `experiments.csv` |
| σ の健全性 | `sigma_interpretation` の値別件数、`sigma_source` の値別件数 | `experiments.csv` |
| 未解決 | backlog の件数（重大度別）と slug 一覧 | `BACKLOG` |
| 契約 | `task_id` を持つ run の数と割合 | `index.csv` |
| 参照先 | 詳細を見るためのファイルパス一覧 | 固定 |

**「主軸」「確定した結論」「次にやるべきこと」は書かない。** これらは人の判断であり、
`context/plan_mirror.md`（人手管理・別 task）の役目である。

- [ ] **Step 2: ヘッダを実装する**

```python
HEADER = """<!-- AUTO-GENERATED by `make context`. DO NOT EDIT. -->
<!-- 手で編集した場合 `make context-check` が検出して失敗します。 -->

# STATE — 数値の現在地

    generated_from_commit: {commit}
    generated_from_date:   {date}
    runindex_counts:       index={n_index} experiments={n_exp} verdicts={n_verdict}

このファイルは runindex から機械的に生成されたものです。
判断・解釈・評価は含みません。研究方針は context/plan_mirror.md を参照してください。
"""
```

`commit` と `date` は次で取得する。**壁時計を使わない。**

```python
commit = subprocess.run(["git", "rev-parse", "HEAD"], ...).stdout.strip()
date = subprocess.run(["git", "log", "-1", "--format=%cI"], ...).stdout.strip()
```

- [ ] **Step 3: 集計を実装する**

Task 1 Step 2〜3 で実測した**実際の列名**を使う。列が見つからない場合は、その節を
`UNKNOWN（列未特定）` と出力し、**推測で代替列を使わない**。

- [ ] **Step 4: 単体で動かして目視確認する**

```bash
.venv/bin/python tools/build_context.py --only state
head -60 context/auto/STATE.md
wc -l context/auto/STATE.md
```

Expected: 300 行以内。判断を含む文が無いこと。

---

## Task 4: `experiments_summary.csv` と `verdicts_summary.csv`（Phase C）

**Files:**
- Modify: `tools/build_context.py`

- [ ] **Step 1: `experiments_summary.csv` の列を選ぶ**

`experiments.csv` は列が多い。外部の面で使う分だけに絞る。**Task 1 で実測した列名から選ぶ。**

| 用途 | 列 |
|---|---|
| 同定 | `experiment_id`, `group`, `step`, `description` |
| 対応 | `arm`, `control_of`, `task_ids` |
| 規模 | `n_runs`, `n_seeds`, `hosts`, `split` |
| 主指標 | `<primary>_mean`, `<primary>_pstd`, `<primary>_sstd` |
| 差 | `delta_<primary>`, `delta_pstd_<primary>`, `abs_delta_over_sigma_<primary>` |
| 判定 | `verdict_metric`, `verdict_10_1`, `verdict_10_1_sstd`, `verdict_10_1_agree` |
| σ の質 | `sigma_source`, `delta_sigma_source`, `sigma_interpretation` |

**主指標が実験によって違う場合**（tool は AP、phase は F1）、指標名を固定せず
`verdict_metric` に対応する値を取る。判別できない行は空欄にし、`UNKNOWN` とはしない
（未測定ではなく該当なしのため）。

- [ ] **Step 2: `verdicts_summary.csv` を作る**

Task 1 Step 4 の実測に基づき、**主指標の行だけに絞る**。絞れない場合は全行を出し、
容量が上限を超えるなら主指標のみへ縮退させ、**どちらを採ったか RESULT に記録する**。

- [ ] **Step 3: 容量を確認する**

```bash
.venv/bin/python tools/build_context.py
du -sh context/auto/
ls -lh context/auto/
```

**上限: 各ファイル 300KB 以内、`context/auto/` 合計 1MB 以内。**
超えた場合は列を減らして再測定し、RESULT に経緯を記録する。

---

## Task 5: `open_questions.md`（Phase C）

**Files:**
- Modify: `tools/build_context.py`

- [ ] **Step 1: `BACKLOG` から抽出する**

`tools/harvest_runindex.py` の `BACKLOG` を `ast.literal_eval` で読み、**slug・番号・重大度・
見出しのみ**を出力する。本文は長大なので載せない（詳細は `runindex/anomalies/backlog.md` を参照）。

半角パイプを含む見出しがある場合は、markdown 表へ出力する前に**エスケープする**
（backlog B-33 と同型の事故を生成器側で防ぐ）。

- [ ] **Step 2: 解決済みを除外する**

取り消し線などで解決済みと分かるものは除外し、**除外件数を末尾に記載する**。

- [ ] **Step 3: 目視確認**

```bash
.venv/bin/python tools/build_context.py --only questions
cat context/auto/open_questions.md
```

Expected: 未解決の slug が列挙され、列崩れが無いこと。

---

## Task 6: `make context` と手編集検出（Phase C）

**Files:**
- Modify: `Makefile`
- Create: `tests/test_build_context.py`

- [ ] **Step 1: Makefile にターゲットを追加する**

**挿入位置に注意。** 前 task で既存レシピの途中へ挿入する事故が起きている。
`.PHONY` 宣言の並びと既存ターゲットの終端を確認してから足すこと。

```makefile
.PHONY: context context-check
context:
	@.venv/bin/python tools/build_context.py

context-check:
	@.venv/bin/python tools/build_context.py --check
```

- [ ] **Step 2: `--check` を実装する**

一時ディレクトリへ生成し、`context/auto/` と比較する。差分があれば標準出力へ表示し
`exit 1`。**手編集と再生成漏れの両方を検出できる。**

- [ ] **Step 3: 冪等性を確認する（G3 ゲート）**

```bash
make context
md5sum context/auto/* > /tmp/c1.txt
make context
md5sum context/auto/* > /tmp/c2.txt
diff /tmp/c1.txt /tmp/c2.txt && echo "IDEMPOTENT OK" || echo "IDEMPOTENT NG"
du -sh context/auto/
```

Expected: `IDEMPOTENT OK` かつ合計 1MB 以内

**NG なら停止して報告する。** 壁時計が混入している可能性が高い。

- [ ] **Step 4: 手編集検出を確認する**

```bash
make context-check; echo "exit=$?"          # 0 のはず
echo "手編集" >> context/auto/STATE.md
make context-check; echo "exit=$?"          # 1 のはず
make context                                 # 元に戻す
make context-check; echo "exit=$?"          # 0 のはず
```

- [ ] **Step 5: テストを書く**

生成器の純粋な部分（集計関数・エスケープ）を対象にする。**git や CSV に触る部分は
Step 3〜4 の実地確認が担保**とし、無理にモックしない。件数は実測で報告する。

- [ ] **Step 6: commit**

```bash
git add Makefile tools/build_context.py tests/test_build_context.py context/auto/
git commit -m "feat(context): generate lightweight views from runindex idempotently"
```

---

## Task 7: 文書の更新

**Files:**
- Modify: `context/README.md`
- Modify: `README.md`

- [ ] **Step 1: `context/README.md` を更新する**

自動生成側が `context/auto/` に移ったこと、`make context` と `make context-check` の使い方、
`STATE.md` に判断を書かない理由を明記する。

- [ ] **Step 2: `README.md` に節を追加する**

`make context` を標準ライフサイクルへ組み込む。**`make runindex` の直後に実行する**ことを
明記する。

- [ ] **Step 3: commit**

```bash
git add README.md context/README.md
git commit -m "docs(context): document make context and the auto/hand boundary"
```

---

## Task 8: 自己契約の配置と完了判定

**Files:**
- Create: `tasks/T-2026-08-06-make-context/{spec.yaml,SPEC.md,RESULT.md}`

- [ ] **Step 1: `conventions_rev` を実測値へ置換する**

配布された `spec.yaml` は `conventions_rev: "8b17c4d"` を持つが、これは前 task で
`conventions.md` が更新される前の値である。**起票者は現在の sha を知り得ないため、
実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

置換した値を RESULT §1 に記録する。§5 の deviations には書かない。

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-06-make-context; echo "exit=$?"
```

Expected: `OK` / `exit=0`

`L2-8` の WARN が出た場合は正常。起票時の `created_from.counts` は
`index 749 / experiments 206 / verdicts 1038` であり、Task 2 で列を足したことにより
行数は変わらないはずだが、他ホストの run が入っていれば差が出る。**WARN の出力を
そのまま RESULT へ記録する。** これは前 task で未検証だった L2-8 の動作確認を兼ねる。

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 生成が通る | `make context` | exit 0・4 ファイル |
| 2 | 冪等 | Task 6 Step 3 | `IDEMPOTENT OK` |
| 3 | 手編集検出 | Task 6 Step 4 | 0 / 1 / 0 |
| 4 | 容量 | `du -sb context/auto/` | 1MB 以内 |
| 5 | index 行数不変 | Task 2 Step 4 | 749 のまま |
| 6 | 除外内訳不変 | 同上 | 一致 |
| 7 | `task_id` 列あり | 同上 | あり・非空 0 件 |
| 8 | ヘッダに反映元 | `head -8 context/auto/STATE.md` | commit と date |
| 9 | 判断が混入していない | `STATE.md` を目視 | 主軸・結論・推奨が無い |
| 10 | 契約検証が通る | `make task-validate` | exit 0 |
| 11 | 全体テストが不変 | `.venv/bin/python -m pytest tests/ -q` | 失敗 5 件のまま |
| 12 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- experiments/ transfer/ data/splits/ context/conventions.md` | 出力なし |

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Task 1 の**実測値すべて**（除外理由の実列名、各 CSV の列名、`verdicts.csv` の粒度）
- `verdicts_summary.csv` を全行にしたか主指標のみにしたか、その判断理由
- `context/auto/` の**ファイル別サイズ**
- `task_id` 列の非空件数（0 が正常）
- L2-8 の WARN の生出力（出た場合）
- `deviations` を空にしない
- §6 に「**`context/` を外部の面へ接続する設定作業が未実施**」を申し送る

- [ ] **Step 5: push と PR**

```bash
git add tasks/T-2026-08-06-make-context/
git commit -m "feat(tasks): self-apply the contract to the context generator"
git push -u origin feat/make-context
gh pr create --base phase0 \
  --title "feat(context): generate lightweight views from runindex" \
  --body-file tasks/T-2026-08-06-make-context/RESULT.md
```

**マージは行わない。auto-merge も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 収穫器を触る open PR がある | **G1 停止。** `concurrent_harvester_change` として報告 |
| index の行数が変わった | **G2 停止。** `index_row_count_changed`。列追加が収穫条件を変えている |
| 冪等でない | **G3 停止。** 壁時計・辞書順の不定・浮動小数の表現ゆれを疑う |
| 容量が 1MB を超える | 列を減らして再測定。**判断と結果を RESULT に記録**してから続行 |
| 除外理由の列が特定できない | 該当節を `UNKNOWN（列未特定）` として出力。**推測で代替列を使わない** |
| `BACKLOG` が `ast.literal_eval` で読めない | 生成を諦め `open_questions.md` に `UNKNOWN` と出力し、理由を RESULT へ |
| `config.yaml` に `task_id` を持つ run が既にある | 想定外。件数と run 名を報告してから続行 |

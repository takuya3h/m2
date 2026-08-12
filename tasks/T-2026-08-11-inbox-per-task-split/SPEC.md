# 受け皿を task ごとの独立した記録へ分け、並行作業での衝突を構造的に無くす

**task_id:** `T-2026-08-11-inbox-per-task-split`
**kind:** `impl`
**depends_on:** `T-2026-08-11-leftover-relocation`

---

## Goal

判断の受け皿は単一のファイルであり、**すべての契約が同じ節へ追記する。**
並行して 2 つの契約を実行したところ、**両方が末尾へ追記したため衝突した。**

これは運用の不注意ではなく**構造の問題**である。並行実行を続ける限り必ず起きる。
起票者が両方の契約に「受け皿へ書く」と指示したことが直接の原因だが、
**逐次実行に戻すのは後退である。**

**task ごとの独立した記録へ分け、集約は機械が行う。**

## 移行後の形

```
tasks/inbox.d/<task_id>.md     ← 各契約が自分の分だけを作る
tasks/inbox.md                 ← 集約結果。機械が生成する
```

異なる契約は**異なるファイル**を作るため、併合しても衝突しない。

## 実行の前提

**先行する契約が統合されてから着手すること。** 未統合の契約が受け皿へ追記していると、
移行と衝突する。

```bash
git fetch origin
git log --oneline -3 origin/phase0
gh pr list --state open --json number,title,headRefName
```

**受け皿へ追記する未統合の契約が残っていれば、停止して報告する。**

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git fetch origin
git checkout -b feat/inbox-split origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | **既存の項目を削除・要約・言い換える** |
| 2 | `runindex/**` `context/auto/**` を手で編集する |
| 3 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 4 | `context/conventions.md` を変更する |
| 5 | 学習・評価コードを変更する |
| 6 | 演算装置を使う |
| 7 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | 統合する。自動統合を有効化する |

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが 8 task 連続で発生している。
また**実行環境の対話シェルは bash ではない。** 直近の 2 task で次の事故が起きた。

| 事象 | 内容 |
|---|---|
| 記録と表示を同じ流れに混ぜた | 表示側が入力を打ち切り、記録が途中で切れた |
| 削除命令が別名に捕まった | 対話確認が出て 1 件も削除されなかった |
| 変数の直後の文字が修飾子と解釈された | 存在しない引数になった。2 度発生 |
| 出力の振り分けが複製として働いた | 無関係な件数を数えた |

**本 SPEC のコマンドも同型の事故を起こしうる。** 次を守ること。

| # | 注意 |
|---|---|
| 1 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 2 | 変数の直後に記号が続く場合は波括弧で囲む |
| 3 | 出力の振り分けは、意図どおりか実測してから使う |
| 4 | 一致件数が 0 のとき、別の探し方でも 0 になることを確かめる |

---

# Phase A — 既存の項目の移行

## Task 1: 現状を測り、移行する

**Files:**
- Create: `tasks/inbox.d/*.md`
- Modify: `tasks/inbox.md`

- [ ] **Step 1: 現状を測る**

```bash
wc -l tasks/inbox.md
grep -c '^- \[ \]' tasks/inbox.md || echo "未処理の項目なし"
grep -c '^- \[x\]' tasks/inbox.md || echo "処理済みの項目なし"
sed -n '1,40p' tasks/inbox.md
```

**節の構成と項目の書式を実測する。** 起票者は書式を推測で決めない。

- [ ] **Step 2: 項目の控えを作る**

**記録を作る流れに表示用の切り詰めを混ぜないこと。**

```bash
mkdir -p /tmp/inbox_migration
cp tasks/inbox.md /tmp/inbox_migration/inbox_before.md
grep -n '^- \[' tasks/inbox.md > /tmp/inbox_migration/entries_before.txt
wc -l /tmp/inbox_migration/entries_before.txt
```

控えを作ったあとで、必要なら別のコマンドで表示する。

- [ ] **Step 3: 帰属先を判定する**

各項目の末尾には、由来する契約の識別子が括弧書きされている。**実測で確かめる。**

```bash
grep -oE 'T-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+' tasks/inbox.md | sort | uniq -c | sort -rn
echo "===== 識別子を含まない項目 ====="
grep '^- \[' tasks/inbox.md | grep -vE 'T-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+' | wc -l
```

**識別子を含まない項目がある場合、それらの行き先を決める。**
推奨は `tasks/inbox.d/_unassigned.md` である。**捨てない。**

- [ ] **Step 4: 分割する**

**1 項目 1 行の原則を保ち、本文を一切変えない。**

```python
# 実装は実測した書式に合わせること。以下は骨子である
import re, pathlib, collections

src = pathlib.Path("tasks/inbox.md").read_text(encoding="utf-8")
ID = re.compile(r"T-\d{4}-\d{2}-\d{2}-[a-z0-9-]+")
buckets = collections.defaultdict(list)
for line in src.splitlines():
    if not line.startswith("- ["):
        continue
    m = ID.search(line)
    buckets[m.group(0) if m else "_unassigned"].append(line)

out = pathlib.Path("tasks/inbox.d")
out.mkdir(exist_ok=True)
for key, lines in buckets.items():
    body = "\n".join(lines) + "\n"
    (out / f"{key}.md").write_text(body, encoding="utf-8")
print("作成:", len(buckets), "件")
```

**同じ識別子を持つ項目は 1 ファイルにまとめる。** 契約と 1 対 1 に対応させる。

- [ ] **Step 5: G1 ゲート — 一件も失われていないことを確認する**

**件数だけでなく本文で照合する。**

```bash
echo "===== 移行前の項目数 ====="
grep -c '^- \[' /tmp/inbox_migration/inbox_before.md

echo "===== 移行後の項目数 ====="
cat tasks/inbox.d/*.md | grep -c '^- \['

echo "===== 本文の照合 ====="
grep '^- \[' /tmp/inbox_migration/inbox_before.md | sort > /tmp/inbox_migration/a.txt
cat tasks/inbox.d/*.md | grep '^- \[' | sort > /tmp/inbox_migration/b.txt
diff /tmp/inbox_migration/a.txt /tmp/inbox_migration/b.txt && echo "完全一致" || echo "差分あり"
```

Expected: 件数が一致し、`完全一致`

**差分があれば停止して報告する**（`entry_lost_during_migration`）。

---

# Phase B — 集約の仕組み

## Task 2: 集約を実装する

**Files:**
- Create: `tools/build_inbox.py`
- Create: `tests/test_build_inbox.py`
- Modify: `Makefile`

- [ ] **Step 1: 失敗する試験を書く**

```python
# tests/test_build_inbox.py
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from build_inbox import collect, render  # noqa: E402


def test_collect_reads_every_file(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("- [ ] one\n", encoding="utf-8")
    (d / "T-2026-01-02-beta.md").write_text("- [ ] two\n- [x] three\n", encoding="utf-8")
    entries = collect(d)
    assert len(entries) == 3


def test_render_is_deterministic(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("- [ ] one\n", encoding="utf-8")
    (d / "T-2026-01-02-beta.md").write_text("- [ ] two\n", encoding="utf-8")
    assert render(collect(d)) == render(collect(d))


def test_render_separates_open_and_done(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("- [ ] open\n- [x] done\n", encoding="utf-8")
    text = render(collect(d))
    assert "open" in text and "done" in text


def test_empty_directory_does_not_crash(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    assert isinstance(render(collect(d)), str)


def test_malformed_lines_are_ignored(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("見出し\n- [ ] valid\n\n", encoding="utf-8")
    assert len(collect(d)) == 1


def test_generated_header_marks_it_as_generated(tmp_path):
    d = tmp_path / "inbox.d"
    d.mkdir()
    (d / "T-2026-01-01-alpha.md").write_text("- [ ] x\n", encoding="utf-8")
    text = render(collect(d))
    assert "生成" in text
```

- [ ] **Step 2: 失敗を確認する**

```bash
python -m pytest tests/test_build_inbox.py -q
```

Expected: FAIL

- [ ] **Step 3: 実装する**

要件は次のとおり。

| # | 要件 |
|---|---|
| 1 | `tasks/inbox.d/*.md` を読み、項目を集める |
| 2 | 未処理と処理済みを分けて出力する |
| 3 | **壁時計を使わない**（同じ入力から同じ出力） |
| 4 | 冒頭に「生成物であり手で編集しない」旨を書く |
| 5 | `--check` で、生成物が最新かを検査する |
| 6 | 空のときも落ちない |

**`--check` の設計は既存の投影の仕組みに揃えること。** 独自の方式を持ち込まない。

```bash
grep -n "check" tools/build_context.py | head -20
```

- [ ] **Step 4: Makefile へ足す**

**挿入位置に注意。** 既存レシピの途中へ入れない。`.PHONY` の並びを確認する。

```makefile
.PHONY: inbox inbox-check
inbox:
	@.venv/bin/python tools/build_inbox.py

inbox-check:
	@.venv/bin/python tools/build_inbox.py --check
```

- [ ] **Step 5: G2 ゲート — 冪等と検出を確認する**

```bash
make inbox
md5sum tasks/inbox.md > /tmp/inbox_migration/h1.txt
make inbox
md5sum tasks/inbox.md > /tmp/inbox_migration/h2.txt
diff /tmp/inbox_migration/h1.txt /tmp/inbox_migration/h2.txt && echo "冪等 OK" || echo "冪等 NG"

make inbox-check; echo "exit=$?"

echo "===== 手による編集を検出するか ====="
printf '\n- [ ] 手で足した行\n' >> tasks/inbox.md
make inbox-check; echo "exit=$?（非ゼロであること）"
make inbox
make inbox-check; echo "exit=$?（0 に戻ること）"
```

**陽性対照が実際に失敗することを確認する。** 検出できなければこの検査は無効である。

- [ ] **Step 6: 項目が保たれていることを再確認する**

```bash
cat tasks/inbox.d/*.md | grep '^- \[' | sort > /tmp/inbox_migration/c.txt
diff /tmp/inbox_migration/a.txt /tmp/inbox_migration/c.txt && echo "移行前と一致" || echo "差分あり"
grep -c '^- \[' tasks/inbox.md
```

- [ ] **Step 7: commit**

---

# Phase C — 衝突しないことの実演

## Task 3: 実際に併合して確かめる

**Files:** なし（一時的な分岐を使い、確認後に消す）

**「衝突しないはず」では足りない。実際に衝突させてみる。**

- [ ] **Step 1: 旧方式なら衝突することを確認する**

**陰性対照である。** 分割前の形で 2 つの分岐が同じ末尾へ追記すると衝突する。

```bash
BASE=$(git rev-parse HEAD)
git checkout -b probe/old-style-a "$BASE"
printf -- '- [ ] 旧方式 A の追記\n' >> tasks/inbox.md
git commit -am "probe: old style a" >/dev/null

git checkout -b probe/old-style-b "$BASE"
printf -- '- [ ] 旧方式 B の追記\n' >> tasks/inbox.md
git commit -am "probe: old style b" >/dev/null

git merge probe/old-style-a >/dev/null 2>&1 && echo "衝突しなかった（想定外）" || echo "衝突した（想定どおり）"
git merge --abort 2>/dev/null || true
```

**衝突しなかった場合、この対照は無効である。** 追記位置を変えて測り直す。

- [ ] **Step 2: 新方式では衝突しないことを確認する**

```bash
git checkout "$BASE" 2>/dev/null
git checkout -b probe/new-style-a "$BASE"
printf -- '- [ ] 新方式 A の追記（T-2026-01-01-probe-a）\n' > tasks/inbox.d/T-2026-01-01-probe-a.md
make inbox >/dev/null
git add tasks/inbox.d tasks/inbox.md
git commit -m "probe: new style a" >/dev/null

git checkout -b probe/new-style-b "$BASE"
printf -- '- [ ] 新方式 B の追記（T-2026-01-02-probe-b）\n' > tasks/inbox.d/T-2026-01-02-probe-b.md
make inbox >/dev/null
git add tasks/inbox.d tasks/inbox.md
git commit -m "probe: new style b" >/dev/null

git merge probe/new-style-a
echo "exit=$?"
```

**集約結果は依然として同じファイルであるため、そこは衝突しうる。**
その場合の解消手順を確認する。

```bash
git status --porcelain
# 集約結果が衝突した場合は、再生成すれば解消する
make inbox
git add tasks/inbox.md
git status --porcelain
```

**要点は「元となる記録は衝突せず、集約結果は再生成で解消できる」ことである。**
これを実測で示す。

- [ ] **Step 3: G3 ゲート — 判定する**

| 観測 | 判定 |
|---|---|
| 旧方式で衝突し、新方式で元の記録が衝突しない | **PASS** |
| 新方式でも元の記録が衝突する | **停止**（`conflict_still_occurs`） |
| 集約結果が衝突するが再生成で解消できる | **PASS**（手順を記録する） |

- [ ] **Step 4: 一時的な分岐を消す**

```bash
git checkout feat/inbox-split
git branch -D probe/old-style-a probe/old-style-b probe/new-style-a probe/new-style-b
git branch --list 'probe/*'
rm -f tasks/inbox.d/T-2026-01-0*-probe-*.md
git status --porcelain
```

**確認用の記録が残っていないことを確かめる。**

---

## Task 4: 手順を更新する

**Files:**
- Modify: `tasks/README.md`
- Modify: `.claude/skills/task/SKILL.md`

- [ ] **Step 1: 受け皿の説明を更新する**

```markdown
## 判断の受け皿

対話で出た判断は、**契約ごとの記録へ 1 行で置く。**

    tasks/inbox.d/<task_id>.md

集約結果 `tasks/inbox.md` は機械が生成する。**手で編集しない。**

    make inbox
    make inbox-check

契約ごとに別のファイルへ書くため、並行して進む作業が衝突しない。
集約結果が併合で衝突した場合は、再生成すれば解消する。

**1 契約 = 最低 1 行。** 置くものが無い場合も「なし」と書いた行を残す。
```

- [ ] **Step 2: 手順書の該当箇所を更新する**

```bash
grep -n "inbox" .claude/skills/task/SKILL.md
```

**受け皿へ書く指示を、新しい置き場へ変える。**

- [ ] **Step 3: 集約結果が誤って編集されないようにする**

生成物であることを冒頭に明記する。**併合時の扱いを記述で補う。**

```bash
head -5 tasks/inbox.md
```

- [ ] **Step 4: commit**

---

## Task 5: 自己契約と起票

**Files:**
- Create: `tasks/T-2026-08-11-inbox-per-task-split/RESULT.md`
- Create: `tasks/inbox.d/T-2026-08-11-inbox-per-task-split.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-11-inbox-per-task-split; echo "exit=$?"
make task-preflight TASK=T-2026-08-11-inbox-per-task-split; echo "exit=$?"
make inbox-check; echo "exit=$?"
```

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 項目が失われていない | Task 1 Step 5 | 完全一致 |
| 2 | 帰属先が判定された | `ls tasks/inbox.d/` | 契約ごとにファイル |
| 3 | 識別子の無い項目も残っている | `ls tasks/inbox.d/_unassigned.md` | 該当があれば存在 |
| 4 | 集約が冪等 | Task 2 Step 5 | 冪等 OK |
| 5 | 手による編集を検出 | 同上 | 非ゼロ → 0 |
| 6 | 旧方式で衝突する | Task 3 Step 1 | 衝突した |
| 7 | 新方式で元の記録が衝突しない | Task 3 Step 2 | 衝突しない |
| 8 | 確認用の記録が残っていない | Task 3 Step 4 | 残っていない |
| 9 | 手順書が新しい置き場を指す | `grep -n "inbox.d" tasks/README.md .claude/skills/task/SKILL.md` | 該当あり |
| 10 | 自分の記録がある | `cat tasks/inbox.d/T-2026-08-11-inbox-per-task-split.md` | 1 行以上 |
| 11 | 契約検証が通る | `make task-validate` | exit 0 |
| 12 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 13 | 試験が不変 | `pytest tests/ -q` | **開始前を先に測る** |
| 14 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- runindex/ context/auto/ experiments/ transfer/ data/splits/ context/conventions.md` | 出力なし |

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- 移行前後の項目数と、本文の照合結果
- 帰属先ごとのファイル数
- 識別子を含まない項目の扱い
- **陰性対照（旧方式で衝突すること）の実測結果**
- 集約結果が併合で衝突した場合の解消手順
- **`deviations` を空にしない**
- §6 に、既に開いている契約が旧方式で追記している場合の扱いを申し送る

- [ ] **Step 5: 起票**

```bash
git add tasks/ tools/ tests/ Makefile .claude/
git commit -m "feat(tasks): split the inbox per task to avoid merge conflicts"
git push -u origin feat/inbox-split
gh pr create --base phase0 \
  --title "feat(tasks): split the decision inbox per task" \
  --body-file tasks/T-2026-08-11-inbox-per-task-split/RESULT.md
```

**統合しない。自動統合も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 受け皿へ追記する未統合の契約がある | **着手前に停止して報告** |
| 項目が失われた | **G1 停止。** `entry_lost_during_migration` |
| 書式が想定と違う | **実測に合わせる。** 推測で正規表現を書かない |
| 識別子を含まない項目がある | `_unassigned` へ。**捨てない** |
| 陰性対照が衝突しなかった | **その対照は無効。** 追記位置を変えて測り直す |
| 新方式でも元の記録が衝突する | **G3 停止。** `conflict_still_occurs` |
| 集約結果が衝突する | **想定内。** 再生成で解消し、手順を記録する |
| 確認用の分岐や記録が残った | 消してから進む |
| 試験の failed が開始前より増えた | 本 task が壊した。停止して報告 |

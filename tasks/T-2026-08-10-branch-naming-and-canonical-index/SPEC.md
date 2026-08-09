# 定位置分岐の命名を整理し、索引の正本の作り方を規約として残す

**task_id:** `T-2026-08-10-branch-naming-and-canonical-index`
**kind:** `impl`
**depends_on:** `T-2026-08-10-conventions-survey`

---

## Goal

各ホストの定位置分岐の名前が揃っていない。実測された現状は次のとおり。

| ホスト | 現在 |
|---|---|
| bengio | `exp/Bengio-wip-20260703` |
| andrew | `exp/Andrew-wip-20260703` |
| efros | `exp/efros-wip-20260703` |
| he | `exp/he-wip-20260804` |
| adam | `exp/adam-wip-20260804` |
| hinton | `exp/hinton-wip-20260804` |
| ian | `exp/ian-wip-20260804` |
| dlsta | `exp/dlstation-wip-20260804` |
| lecun | 作業分岐に滞留 |
| ilya | 作業分岐に滞留 |
| philip | 未確認（到達不能） |

**日付が 2 種類、大文字小文字が不統一、ホスト名と分岐名の不一致が 1 件。**

## 採用する命名

```
exp/<ホストの論理名>
```

- 論理名は小文字英数とハイフン、2 文字以上 20 文字以下
- **日付と作業状態を表す語を含めない**
- ホストの論理名と一致させる

### 接頭辞を保つ理由

先行調査により、接頭辞に依存する箇所が 5 つ見つかっている。うち 3 つは
**接頭辞さえ保てば変更が不要**である。

| 箇所 | 接頭辞を保つ場合 |
|---|---|
| 自動同期の判定 | 変更不要 |
| その試験 | 変更不要 |
| 継続的統合の起動条件 | 変更不要 |
| 分岐名の生成規則 | **変更が要る** |
| 常駐設定の導入手順 | **実測して判断** |

**ただしこれは起票者の推定である。Phase A で実測して確かめる。**

## 移行時の制約（先行調査で判明）

常駐する送出スクリプトは、**現在の分岐と同名の遠隔参照が存在する場合にのみ**送出と
起票を行う。したがって **新しい遠隔参照を先に作ってから切り替える。**

## 本 task の範囲

**実装と文書化までとし、各ホストの切り替えは行わない。** 統合後に別途実施する。

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git fetch origin
git checkout -b feat/branch-naming origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | **各ホストの分岐を実際に切り替える**（本 task の範囲外） |
| 2 | 既存の遠隔参照を削除する |
| 3 | **過去の記録を書き換える**（過去の契約・実験証跡・調査記録・snapshot） |
| 4 | `runindex/**` `context/auto/**` を手で編集する |
| 5 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 6 | 学習・評価コードを変更する |
| 7 | 演算装置を使う |
| 8 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 9 | 統合する。自動統合を有効化する |

### 書き換えてよい文書と、いけない文書

| 種別 | 扱い |
|---|---|
| 現行の運用手順書 | **更新する** |
| 過去の契約・結果 | **触らない** |
| 実験証跡の記述 | **触らない** |
| 過去の調査記録 | **触らない** |
| 外部由来の複製 | **触らない** |

**先行調査が「記録」と分類したものは、すべて触らない。**

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが 8 task 連続で発生している。
直近では、常駐スクリプトへの検索が空を返したのを「該当なし」と扱ったが、
**別の探し方では実際の依存が見つかった。**

**本 SPEC の検査も同型の誤りを含みうる。** 次の点に注意すること。

| # | 注意 |
|---|---|
| 1 | 一致件数が 0 のとき、別の探し方でも 0 になることを確かめる |
| 2 | 仕組みの挙動は実装を読んでから信じる |
| 3 | 表への追記は列数を数えてから書く |

---

# Phase A — 影響箇所の再確認

## Task 1: 接頭辞を保つ場合に何が要るかを実測する

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 先行調査の結果を読む**

```bash
sed -n '/## 3. 分岐名への依存/,/## 4./p' tasks/T-2026-08-10-conventions-survey/survey.md
```

**この一覧を出発点とする。ただし鵜呑みにせず、致命に分類された箇所を自分で読む。**

- [ ] **Step 2: 判定の実装を読む**

```bash
sed -n '160,190p' src/egosurgery/utils/git_autosync.py
grep -n "startswith\|exp/" src/egosurgery/utils/git_autosync.py
```

**新しい名前がこの判定を通るかを、実装から判断する。**

- [ ] **Step 3: 試験が何を固定しているかを読む**

```bash
grep -n "exp/" tests/test_git_autosync.py
```

試験が特定の分岐名を直書きしている場合、**新しい名前でも通るかを確認する。**
接頭辞のみを条件にしているなら変更不要である。

- [ ] **Step 4: 起動条件を読む**

```bash
grep -n "branches\|exp/" .github/workflows/auto-draft-pr.yml
```

- [ ] **Step 5: 生成規則を読む**

```bash
cat scripts/sync/new_experiment_branch.sh
```

- [ ] **Step 6: 常駐設定の導入手順を読む**

```bash
sed -n '1,40p' scripts/sync/setup_host_autosync.sh
sed -n '150,185p' scripts/sync/setup_host_autosync.sh
grep -n "exp/" scripts/sync/setup_host_autosync.sh
```

**接頭辞のみを見ているのか、日付や作業状態の語も見ているのかを判別する。**

- [ ] **Step 7: 送出スクリプトの前提を確かめる**

先行調査により、これは追跡外にある。**存在を先に確認する。**

```bash
for f in ~/bin/m2-sync.sh ~/bin/keeper.sh; do
  [ -e "$f" ] || { echo "対象が存在しない: $f"; continue; }
  echo "===== $f ====="
  grep -nE "branch|origin/|rev-parse|show-current|ls-remote" "$f" | head -20
done
```

**遠隔参照の存在をどう確かめているかを読む。** 移行手順の設計に必要である。

- [ ] **Step 8: G1 ゲート — 変更が要る箇所を確定する**

| 箇所 | 接頭辞を保つ場合 | 根拠 |
|---|---|---|

**推定ではなく、読んだ結果を書く。** 推定と実測が食い違えば、実測に従い記録する。

変更が要る箇所が 0 件なら、Phase B は文書のみとなる。**それも正しい結果である。**

---

# Phase B — 生成規則と移行補助

## Task 2: 生成規則を新しい命名へ

**Files:**
- Modify: `scripts/sync/new_experiment_branch.sh`
- Modify: `scripts/sync/setup_host_autosync.sh`（Phase A で必要と判明した場合のみ）

- [ ] **Step 1: 生成規則を変える**

日付と作業状態の語を含めない形にする。**論理名の妥当性を検査すること。**

| 要件 | 内容 |
|---|---|
| 1 | 小文字英数とハイフンのみを受け付ける |
| 2 | 2 文字以上 20 文字以下 |
| 3 | 条件を満たさない入力は**明確な理由とともに失敗する** |
| 4 | 生成される名前は接頭辞から始まる |

- [ ] **Step 2: 失敗する試験を書く**

```python
# tests/test_branch_naming.py
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync" / "new_experiment_branch.sh"


def _run(*args):
    return subprocess.run(["bash", str(SCRIPT), *args],
                          capture_output=True, text=True)


def test_accepts_lowercase_host_name():
    r = _run("--dry-run", "bengio")
    assert r.returncode == 0, r.stderr
    assert "exp/bengio" in r.stdout


def test_rejects_uppercase():
    r = _run("--dry-run", "Bengio")
    assert r.returncode != 0


def test_rejects_name_with_date():
    r = _run("--dry-run", "bengio-wip-20260703")
    assert r.returncode != 0 or "20260703" not in r.stdout


def test_rejects_too_short():
    r = _run("--dry-run", "a")
    assert r.returncode != 0


def test_generated_name_keeps_prefix():
    r = _run("--dry-run", "lecun")
    assert r.stdout.strip().endswith("exp/lecun") or "exp/lecun" in r.stdout
```

**`--dry-run` が既存の実装に無ければ追加する。** 実際に分岐を作らずに名前だけを
出力する経路が要る。試験が本物の分岐を作ってはならない。

- [ ] **Step 3: 実装して試験を通す**

```bash
python -m pytest tests/test_branch_naming.py -q
```

- [ ] **Step 4: G2 ゲート — 新しい名前が判定を通ることを実装から確かめる**

**文書の記述ではなく、実装を呼び出して確かめる。**

```bash
python - <<'PY'
import sys
sys.path.insert(0, "src")
from egosurgery.utils import git_autosync as ga

# 判定に相当する関数または条件を、実装を読んで特定してから呼ぶ
# 名前だけを与えて可否が分かる経路が無い場合は、条件式を直接評価して記録する
names_ok  = ["exp/bengio", "exp/lecun", "exp/dlsta", "exp/he"]
names_ng  = ["phase0", "master", "HEAD", "feat/x", "host/bengio"]
for n in names_ok + names_ng:
    print(f"{n:20} -> startswith exp/: {n.startswith('exp/')}")
PY
```

**上は接頭辞の確認にすぎない。** 実際の判定関数を呼べる場合は呼び、その出力を記録する。
呼べない場合は、判定を含む行を引用し、**新しい名前がその条件を満たすことを説明する。**

**満たさない場合は停止して報告する**（`guard_rejects_new_name`）。

- [ ] **Step 5: commit**

---

## Task 3: 移行を補助する手順

**Files:**
- Create: `scripts/sync/rename_host_branch.sh`
- Create: `tasks/T-2026-08-10-branch-naming-and-canonical-index/migration_plan.md`

**切り替えは行わない。手順を用意するだけである。**

- [ ] **Step 1: 補助スクリプトを作る**

要件は次のとおり。**順序が重要である。**

| # | 要件 |
|---|---|
| 1 | 引数で新しい論理名を受け取り、妥当性を検査する |
| 2 | 作業ツリーが汚れていれば**何もせず失敗する** |
| 3 | 現在の分岐を取得し、既に新しい名前ならそのまま終了する |
| 4 | **遠隔参照を先に作る**（新しい名前で送出し上流を設定する） |
| 5 | そのあとで局所の分岐名を変える |
| 6 | **古い遠隔参照を削除しない** |
| 7 | 変更後に、送出スクリプトの前提が満たされることを確認する |
| 8 | 各段階の結果を出力する。失敗したらそこで止まる |

**要件 4 と 5 の順序を逆にしてはならない。** 先に局所を変えると、遠隔参照が無い状態が
生じ、常駐スクリプトの前提が崩れる。

**`--dry-run` を用意し、何をするかだけを表示できるようにする。**

- [ ] **Step 2: 対応表を書く**

```markdown
# 定位置分岐の移行計画

## 対応表

| ホスト | 現在 | 移行後 |
|---|---|---|
| lecun | 作業分岐に滞留 | exp/lecun |
| philip | 未確認 | exp/philip |
| ilya | 作業分岐に滞留 | exp/ilya |
| bengio | exp/Bengio-wip-20260703 | exp/bengio |
| andrew | exp/Andrew-wip-20260703 | exp/andrew |
| he | exp/he-wip-20260804 | exp/he |
| adam | exp/adam-wip-20260804 | exp/adam |
| hinton | exp/hinton-wip-20260804 | exp/hinton |
| ian | exp/ian-wip-20260804 | exp/ian |
| dlsta | exp/dlstation-wip-20260804 | exp/dlsta |
| efros | exp/efros-wip-20260703 | exp/efros |

## 実施の順序

1. 本 task を統合する
2. 全ホストへ行き渡ったことを確認する
3. 作業分岐に滞留しているホストは、先に作業を統合するか退避する
4. 1 台で試し、送出と起票と自動同期が働くことを確認する
5. 残りのホストで実施する
6. 全ホストで働くことを確認したあとに、古い遠隔参照の扱いを判断する

## 注意

- 到達できないホストは実施を保留する
- 作業ツリーが汚れているホストは、先に整理する
- **古い遠隔参照は当面残す**
```

**大文字小文字のみが異なる改名は、環境によって扱いが異なる。** 該当する場合は
中間の名前を経由する必要がありうる。**実装で対処するか、注意として明記する。**

- [ ] **Step 3: 空実行で確認する**

```bash
bash scripts/sync/rename_host_branch.sh --dry-run bengio
echo "exit=$?"
git branch --show-current    # 変わっていないこと
git status --porcelain       # 汚れていないこと
```

**空実行で何も変わらないことを確認する。**

- [ ] **Step 4: 不正な入力を拒むことを確認する**

```bash
for n in "Bengio" "bengio-wip-20260703" "a" "exp/bengio" "b engio" "bengio;rm -rf /"; do
  printf "%-24s " "$n"
  bash scripts/sync/rename_host_branch.sh --dry-run "$n" >/dev/null 2>&1 && echo "受理（要確認）" || echo "拒否"
done
```

**すべて拒否されること。** 一つでも受理されたら修正する。

- [ ] **Step 5: commit**

---

# Phase C — 手順書と正本規約

## Task 4: 現行の手順書を更新する

**Files:**
- Modify: `OPERATION.md`
- Modify: `README.md`
- Modify: `docs/host_autosync_onboarding.md`
- Modify: `tasks/README.md`

**先行調査が「表示」と分類したものだけを更新する。「記録」は触らない。**

- [ ] **Step 1: 対象を確認する**

```bash
grep -n "exp/" OPERATION.md | head -30
grep -n "exp/" README.md | head -20
grep -n "exp/" docs/host_autosync_onboarding.md | head -20
grep -n "exp/" tasks/README.md
```

- [ ] **Step 2: 更新する**

日付と作業状態の語を含む例を、新しい命名へ置き換える。
**過去の出来事を述べている記述は変えない。** 現在の手順を述べている記述だけを変える。

判別に迷う場合は**変えずに残し、その旨を記録する。**

- [ ] **Step 3: 触ってはいけないものに触れていないことを確認する**

```bash
git diff --name-only | sort
echo "===== 触れてはいけない領域 ====="
git diff --name-only | grep -E "^(tasks/T-2026-08-0|experiments/|third_party_snapshot/|docs/sync_|docs/runindex_|docs/superpowers/|runindex/)" && echo "!!! 過去の記録に触れている" || echo "問題なし"
```

**該当があれば戻す**（`historical_record_modified`）。

---

## Task 5: 索引の正本の規約

**Files:**
- Modify: `tasks/README.md`

別ホストでの実測により、索引はディスクを走査するため**ホストによって行数が変わる**ことが
分かっている。退避物を持たないホストで生成したものが正本の候補になる。

- [ ] **Step 1: 実測を確認する**

```bash
grep -n "index" tasks/T-2026-08-10-third-host-verification/host_parity.md | head -20
```

- [ ] **Step 2: 規約を書く**

```markdown
## 索引の正本

索引はディスクを走査して生成されるため、**同じ commit でもホストによって内容が変わる。**
特定のホストにのみ残る過去の run があると、その分だけ行が増える。

したがって次を規約とする。

- 索引の再生成と記録は、**追跡外の run を持たないホストで行う**
- 記録の前に、追跡外の経路を持つ行が 0 件であることを確認する
- 他のホストは再生成せず、配られたものを使う
- 汚れた索引を記録しない。汚れたまま放置すると自動統合が止まる

確認の方法は次のとおり。

    make runindex
    （索引の各行の経路が追跡されているかを確かめる）

追跡外の行があるホストで生成したものは正本にしない。
```

- [ ] **Step 3: G3 ゲート — 矛盾がないことを確認する**

```bash
grep -n "exp/" OPERATION.md README.md docs/host_autosync_onboarding.md tasks/README.md | \
  grep -E "wip|20260703|20260804" && echo "古い例が残っている" || echo "古い例なし"
```

**残っている場合、それが「記録」なのか「更新漏れ」なのかを判別する。**
記録なら残してよい。判別できなければ残し、記録する。

`on_fail: ask` である。**判断が要る場合は提示して仰ぐ。**

- [ ] **Step 4: commit**

---

# Phase D — 自己契約

## Task 6: 完了判定と起票

**Files:**
- Create: `tasks/T-2026-08-10-branch-naming-and-canonical-index/RESULT.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-10-branch-naming-and-canonical-index; echo "exit=$?"
make task-preflight TASK=T-2026-08-10-branch-naming-and-canonical-index; echo "exit=$?"
```

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 影響箇所が実測で絞られた | `RESULT.md` | 表が埋まっている |
| 2 | 生成規則が新命名に従う | `pytest tests/test_branch_naming.py -q` | 全 pass |
| 3 | 不正入力を拒む | Task 3 Step 4 | 全て拒否 |
| 4 | 新しい名前が判定を通る | Task 2 Step 4 | 通る |
| 5 | 空実行が何も変えない | Task 3 Step 3 | 分岐も作業ツリーも不変 |
| 6 | 遠隔参照を先に作る順序 | 実装を目視 | 要件 4 が 5 より前 |
| 7 | 手順書が更新された | `grep -c "exp/" OPERATION.md` | 更新済み |
| 8 | 正本規約がある | `grep -n "索引の正本" tasks/README.md` | 1 件 |
| 9 | 過去の記録が不変 | Task 4 Step 3 | 問題なし |
| 10 | 分岐を切り替えていない | `git branch --show-current` | `feat/branch-naming` |
| 11 | 契約検証が通る | `make task-validate` | exit 0 |
| 12 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 13 | 試験が不変 | `pytest tests/ -q` | **開始前を先に測る** |
| 14 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- runindex/ context/auto/ experiments/ transfer/ data/splits/ context/conventions.md` | 出力なし |

**判定13**: 本 task で試験を 5 件追加するため、pass の数は増える。**failed の数が
開始前と同じであることを見る。**

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Phase A の実測（**推定と実測が食い違った箇所を明示**）
- 変更が不要と判明した箇所と、その根拠
- 生成規則の変更内容
- 移行補助の要件のうち、実装で担保した順序
- 大文字小文字のみが異なる改名への対処
- 手順書のうち、判別に迷って残した記述
- **`deviations` を空にしない**
- §6 に、切り替えの実施が別作業であることを申し送る

- [ ] **Step 5: 受け皿へ書く**

`tasks/inbox.md` へ本 task の判断を 1 行以上置く。

- [ ] **Step 6: 起票**

```bash
git add tasks/T-2026-08-10-branch-naming-and-canonical-index/ tasks/inbox.md
git commit -m "docs(tasks): record branch naming and canonical index conventions"
git push -u origin feat/branch-naming
gh pr create --base phase0 \
  --title "feat(sync): unify home branch naming and document the canonical index" \
  --body-file tasks/T-2026-08-10-branch-naming-and-canonical-index/RESULT.md
```

**統合しない。自動統合も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 判定が新しい名前を拒む | **G2 停止。** `guard_rejects_new_name` |
| 変更が要る箇所が推定より多い | 全て記録し、範囲が広がることを提示して判断を仰ぐ |
| 変更が要る箇所が 0 件だった | **それも正しい結果。** 文書のみ更新する |
| 生成規則に空実行が無い | 追加する。**試験が本物の分岐を作ってはならない** |
| 過去の記録に触れた | **即座に戻す。** `historical_record_modified` |
| 更新すべきか判別できない記述 | **残す。** 判別できなかったことを記録する |
| 常駐スクリプトが読めない | 対象の有無を先に確認し、無ければ「対象なし」と記録する |
| 大文字小文字のみの改名で問題が出る | 中間の名前を経由する手順を用意し、注意として明記する |
| 試験の failed が開始前より増えた | 本 task が壊した。停止して報告 |

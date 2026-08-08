# 配線検証の後始末と、そこで判明した環境差と失効の記録

**task_id:** `T-2026-08-09-wiring-followup-and-integration`
**kind:** `impl`
**depends_on:** `T-2026-08-09-run-wiring-verification`
**実行ホスト:** `lecun`（分岐 `exp/lecun-wip-20260703`）

---

## Goal

前 task で 3 つの配線が確認できた一方、**4 つの未処理事項**が残った。

| # | 事項 | 状態 |
|---|---|---|
| 1 | 生成された成果物の記述が雛形のまま | 索引に載っており、読み手を誤導する |
| 2 | 収穫器が走査するホストによって索引が変わる | 未起票 |
| 3 | 依存導入の手順がホストによって異なる | 未記録 |
| 4 | 自動同期の記録が成功時には書かれない | 未文書化。**起票者の検査条件が誤っていた原因** |

あわせて、資格情報の失効が未設定と区別されずに報告される問題と、依存の一括導入手段の
不在に対処し、成果を統合する。

## 統合の方針

利用者の判断により、本 task の完了後に分岐を統合する。ただし分岐には配線検証以前の
作業が含まれている可能性があるため、**統合対象を先に確認する**（Phase A）。

---

## 0. 前提と禁止事項

```bash
cd /home/ubuntu/slocal2/m2
git branch --show-current     # exp/lecun-wip-20260703
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | **演算装置を使う**（本 task は計算資源を要しない） |
| 2 | `runindex/**` の生成物を手で編集する |
| 3 | **配線検証の run 以外の** `experiments/**` `transfer/**` を変更・削除する |
| 4 | `data/splits/**` を変更する |
| 5 | 学習・評価コードを変更する |
| 6 | `context/conventions.md` を変更する |
| 7 | 実測値を書き換える。未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | 資格情報そのものを再発行・変更する（**利用者の操作領域**） |

### 本 task で解禁するもの

| 対象 | 範囲 |
|---|---|
| `tools/harvest_runindex.py` | **未解決事項の一覧への追記のみ。** 収穫の条件・列・除外規則には触れない |
| 配線検証で生成された run の `notes.md` | **記述の追記のみ。** 数値は一切変更しない |

### 起票者からの申し送り

**起票者の検査コマンドが検証対象を検証できていない誤りが 5 task 連続で発生している。**
直近では、記録の有無で自動同期の発火を判定させたが、実装上その記録は中断時にしか
書かれず、指示どおりなら結論が反転していた。

**本 SPEC の検査も同型の誤りを含みうる。** 判定の根拠となる仕組みは、条件を信じる前に
**実装を読んで確かめること。** 読んで食い違えば、SPEC ではなく実装に従い記録する。

### 起票時点の母集団について

`meta.created_from.counts` は起票者が把握している最後の値であり、前 task で索引が
変化したため**現在と食い違う**。実行前検査で警告が出るのは正常である。
**現在の実測値を RESULT へ記録すること。** 契約の値は書き換えない。

---

# Phase A — 統合範囲の確認

## Task 1: 何が統合されるかを確かめる

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 統合対象の変更集合を列挙する**

```bash
git fetch origin
BR=$(git branch --show-current)
echo "===== 分岐が持つ、統合先に無いコミット ====="
git log --oneline origin/phase0.."$BR"
echo "===== 件数 ====="
git rev-list --count origin/phase0.."$BR"
echo "===== 変更されるファイル ====="
git diff --stat origin/phase0..."$BR"
echo "===== 遠隔との差 ====="
git rev-list --count "origin/$BR..HEAD"
```

- [ ] **Step 2: 想定と照合する（G1 ゲート）**

前 task で作られたコミットは 3 件である。

| 想定 | 内容 |
|---|---|
| 自動同期によるもの | 配線検証の run の成果物 |
| 索引の再生成 | `runindex/` と `context/auto/` |
| 記録 | `tasks/` と `tasks/inbox.md` |

**これ以外のコミットが含まれていれば停止して報告する**（`unexpected_commits_in_range`）。

配線検証以前の作業が混ざっている場合、**統合すると意図しない変更が全ホストへ配られる**。
その場合は、統合対象を絞る方法（別の分岐を切って必要なコミットだけ移す等）を
提案して判断を仰ぐ。**自分で範囲を決めない。**

- [ ] **Step 3: 索引の現状を実測する**

```bash
python - <<'PY'
import csv
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
ex = next((c for c in cols if "exclu" in c.lower() and "reason" not in c.lower()), None)
n_task = sum(1 for r in rows if r.get("task_id"))
print(f"index 行数: {len(rows)}")
print(f"task_id を持つ行: {n_task}")
if ex:
    print(f"除外列 {ex}: 除外 {sum(1 for r in rows if str(r.get(ex)).lower() in ('true','1'))}")
PY
for f in experiments verdicts per_class; do
  printf "%-12s %s\n" "$f" "$(($(wc -l < runindex/$f.csv) - 1))"
done
```

**この値を RESULT §1 へ記録する。** 契約の `created_from` は書き換えない。

---

# Phase B — 後始末

## Task 2: 成果物の記述を埋める

**Files:**
- Modify: 配線検証で生成された run の `notes.md` のみ

雛形のまま索引に載っている状態は、読み手を誤導する。**数値は一切変更しない。**

- [ ] **Step 1: 現状を確認する**

```bash
RUN=experiments/baselines/s0_040_wiring_verification_seed42
ls -la "$RUN"
echo "===== notes.md ====="
cat "$RUN/notes.md"
echo "===== metrics.json ====="
cat "$RUN/metrics.json"
echo "===== config の識別子 ====="
grep -n "task_id" "$RUN/config.yaml"
```

- [ ] **Step 2: 記述を埋める**

**次の点を必ず含める。**

| # | 内容 |
|---|---|
| 1 | この run が**配線の確認**を目的とすること |
| 2 | 学習量が極小であり、**性能の主張には使えない**こと |
| 3 | 対応する契約の識別子 |
| 4 | 対照実験の宣言を持たないこと |
| 5 | 実測された数値（`metrics.json` から**転記**する。計算し直さない） |
| 6 | 使用した装置と所要時間 |

**評価・解釈・見込みを書かない。** 事実と、この run を何に使ってはならないかだけを書く。

- [ ] **Step 3: 数値が変わっていないことを確認する**

```bash
git diff --stat "$RUN"
git diff "$RUN/metrics.json" | head    # 出力が無いこと
```

**`metrics.json` に差分が出たら停止して報告する。**

- [ ] **Step 4: commit**

```bash
git add "$RUN/notes.md"
git commit -m "docs(experiments): describe the wiring verification run and its limits"
```

---

# Phase C — 判明した事項の記録

## Task 3: 未解決事項を起票する

**Files:**
- Modify: `tools/harvest_runindex.py`（未解決事項の一覧のみ）

**2 件を起票する。**

| 内容 | 背景 |
|---|---|
| 収穫器が走査するホストによって索引が変わる | 別ホストで再生成したところ、退避済みの 34 件が加わった |
| 自動同期の記録が成功時には書かれない | 記録の有無で発火を判定できない。起票者の検査が誤った原因 |

- [ ] **Step 1: 採番の衝突を避ける**

過去に採番の衝突が起きている。**全ての遠隔分岐を走査して実在の最大を確認する。**

```bash
git fetch origin
for ref in $(git for-each-ref --format='%(refname)' refs/remotes/origin | grep -v HEAD); do
  n=$(git show "$ref:tools/harvest_runindex.py" 2>/dev/null | grep -oE '"B-[0-9]+"' | tr -d '"B-' | sort -n | tail -1)
  [ -n "$n" ] && printf "%-50s B-%s\n" "$ref" "$n"
done | sort -k2 -V | tail -5
```

**実在の最大の次から採番する。**

- [ ] **Step 2: 記法を守る**

**本文に半角パイプを書かない。** 過去に 3 度、表の列が壊れている。列挙は語で区切る。

```bash
grep -n "BACKLOG" tools/harvest_runindex.py | head -3
```

既存の項目の形式に揃える。**列数を変えない。**

- [ ] **Step 3: 起票する**

| 項目 | 内容の要点 |
|---|---|
| 1 件目 | 収穫器はディスクを走査するため、同じ commit でもホストによって索引の行数が変わる。解析対象の行は除外規約により保護されるが、**索引の同一性は保証されない** |
| 2 件目 | 自動同期の記録は中断時にのみ書かれる。**記録が無いことは不発火を意味しない**。発火の確認には commit の履歴を見る |

**再現手順と、実測された値を含める。推測を書かない。**

- [ ] **Step 4: 構文と表の整合を確認する**

```bash
python -m py_compile tools/harvest_runindex.py && echo "構文 OK"
python - <<'PY'
import re, pathlib
src = pathlib.Path("tools/harvest_runindex.py").read_text(encoding="utf-8")
m = re.search(r"^BACKLOG\s*=\s*", src, re.M)
if not m:
    print("BACKLOG が見つからない")
else:
    seg = src[m.start():]
    rows = [ln for ln in seg.splitlines() if ln.strip().startswith("|")]
    cols = {ln.count("|") for ln in rows}
    print("表の行数:", len(rows), "区切りの種類:", cols)
    assert len(cols) <= 1, f"列数が揃っていない: {cols}"
    print("列数 OK")
PY
```

**列数の種類が 1 でなければ、パイプの混入である。** 修正してから進む。

- [ ] **Step 5: G2 ゲート — 再生成の影響を測る**

```bash
md5sum runindex/*.csv > /tmp/bl_before.txt
make runindex 2>&1 | tail -10
md5sum runindex/*.csv > /tmp/bl_after.txt
diff /tmp/bl_before.txt /tmp/bl_after.txt && echo "CSV 不変" || echo "CSV が変化した"
git status --porcelain runindex/
```

Expected: **CSV は 4 種とも不変**、変化するのは未解決事項の一覧のみ

**CSV が変化したら停止して報告する**（`harvester_output_changed_beyond_backlog`）。

- [ ] **Step 6: 軽量ビューへ反映する**

```bash
make context
make context-check; echo "exit=$?"
grep -c "^| BL-" context/auto/open_questions.md
```

- [ ] **Step 7: commit**

```bash
git add tools/harvest_runindex.py runindex/ context/auto/
git commit -m "docs(runindex): file host-dependent scan and autosync log semantics"
```

---

## Task 4: 既知差と規約を記録する

**Files:**
- Modify: `tasks/README.md`

- [ ] **Step 1: 依存導入の差を記録する**

実測により、ホストによって仮想環境の作られ方が異なることが判明した。**一方では
依存の導入コマンドが別の環境へ入り、成功したように見える。**

```bash
which pip python
ls .venv/bin/ | grep -E "^pip|^uv" || echo "pip は無い"
.venv/bin/python -m pip --version 2>&1 | head -1
```

`tasks/README.md` の既知差の節へ追記する。

```markdown
| 依存の導入 | ホストによって仮想環境の作られ方が異なる。一方の実行ホストでは
仮想環境に導入コマンドが無く、別の環境へフォールバックする。**導入済みと表示されても
仮想環境には入っていない。** 導入は `make setup` を使うこと |
```

- [ ] **Step 2: 自動同期の記録の性質を書く**

```markdown
## 自動同期の確認方法

自動同期の記録は**中断時にのみ書かれる**。成功時も見送り時も書かれないため、
**記録が無いことは不発火を意味しない。**

発火の確認には、生成された commit の履歴と遠隔との差を見る。

    git log --oneline -5
    git rev-list --count origin/$(git branch --show-current)..HEAD
```

- [ ] **Step 3: commit**

```bash
git add tasks/README.md
git commit -m "docs(tasks): record host differences in dependency install and autosync logs"
```

---

# Phase D — 仕組み

## Task 5: 依存の一括導入

**Files:**
- Modify: `Makefile`
- Modify: `tasks/README.md`

前 task で、契約の取り込みが依存不足で失敗した。**ホストごとに手で導入する必要があり、
しかも導入方法がホストによって違う。**

- [ ] **Step 1: 実行ホストで動く方法を実測する**

```bash
command -v uv && uv --version || echo "uv は無い"
ls ~/.local/bin/uv 2>/dev/null
.venv/bin/python -m ensurepip --version 2>&1 | head -1
grep -n "jsonschema\|optional-dependencies\|\[project\]" pyproject.toml | head -20
```

- [ ] **Step 2: ターゲットを追加する**

**挿入位置に注意。** 既存レシピの途中へ入れない。

要件は次のとおり。

| # | 要件 |
|---|---|
| 1 | 導入先を仮想環境へ**明示的に指定**する。環境変数の状態に依存しない |
| 2 | 導入手段が使えない場合、**明確なエラーで停止**する。黙って別の環境へ入れない |
| 3 | 導入後に**実際に読み込めることを確認**する |
| 4 | 何度実行しても同じ結果になる |

**要件 3 が重要である。** 導入コマンドが成功を返しても、仮想環境に入っていない事例が
実際に起きている。**読み込みまで確認して初めて成功とする。**

- [ ] **Step 3: G3 ゲート — 実行ホストで動くことを確認する**

```bash
make setup 2>&1 | tail -20; echo "exit=$?"
.venv/bin/python -c "import jsonschema, yaml; print('読み込み OK')"
echo "===== 冪等 ====="
make setup 2>&1 | tail -5; echo "exit=$?"
```

Expected: 両方 `exit=0`、読み込みが成功

`on_fail: ask` である。**動かなくても自動で停止せず、原因と代替案を提示して判断を仰ぐ。**
他ホストでの動作は未検証のまま残るので、その旨を記録する。

- [ ] **Step 4: 文書化する**

`tasks/README.md` に、契約を扱う前に `make setup` を実行する旨を書く。

- [ ] **Step 5: commit**

```bash
git add Makefile tasks/README.md
git commit -m "feat: add make setup to install dev dependencies into the venv"
```

---

## Task 6: 資格情報の失効を検出する

**Files:**
- Modify: `.github/workflows/auto-draft-pr.yml`

**資格情報そのものは変更しない。** 検出と報告のみを直す。

- [ ] **Step 1: 現状を確認する**

```bash
cat .github/workflows/auto-draft-pr.yml
echo "===== 直近の実行 ====="
gh run list --workflow=auto-draft-pr.yml --limit 10 --json conclusion,createdAt,headBranch 2>&1
```

**実装を読んで、未設定をどう検出しているかを確かめる。**

- [ ] **Step 2: 検出を足す**

現在は未設定を検出するが、**失効を検出しない。** その結果、失効時にも未設定と同じ
文言が出て誤誘導する。

| 状態 | 現在 | 望ましい |
|---|---|---|
| 未設定 | 検出される | そのまま |
| 設定済みだが失効 | **未設定として報告** | **失効として報告** |
| 有効 | 通過 | そのまま |

資格情報の有効性を確かめる呼び出しを足し、**応答に応じて文言を分ける。**
値そのものは出力しない。

- [ ] **Step 3: 検証の限界を記録する**

**有効な資格情報が無いため、通過経路は検証できない。** 失効時に正しい文言が出ることの
確認までとし、**通過経路は未検証として記録する。** 推測で「動くはず」と書かない。

- [ ] **Step 4: commit**

```bash
git add .github/workflows/auto-draft-pr.yml
git commit -m "fix(ci): distinguish expired credentials from missing ones"
```

---

# Phase E — 統合

## Task 7: 自己契約と統合

**Files:**
- Create: `tasks/T-2026-08-09-wiring-followup-and-integration/RESULT.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-09-wiring-followup-and-integration; echo "exit=$?"
make task-preflight TASK=T-2026-08-09-wiring-followup-and-integration; echo "exit=$?"
```

**母集団の警告が出るのは正常。** 出力を記録する。

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 統合範囲が想定どおり | Task 1 Step 2 | 想定外なし |
| 2 | 記述が埋まった | `cat <run>/notes.md` | 雛形でない |
| 3 | 数値が不変 | `git diff <run>/metrics.json` | 出力なし |
| 4 | 未解決事項が 2 件増えた | `grep -c "^| BL-" context/auto/open_questions.md` | 前より 2 増 |
| 5 | 表の列が揃っている | Task 3 Step 4 | 列数の種類が 1 |
| 6 | 収穫器の出力が不変 | Task 3 Step 5 | CSV 不変 |
| 7 | 軽量ビューが整合 | `make context-check` | exit 0 |
| 8 | 依存導入が動く | Task 5 Step 3 | 読み込み OK |
| 9 | 依存導入が冪等 | 同上 | 2 回目も exit 0 |
| 10 | 失効の文言が分かれた | Task 6 | 実装に反映 |
| 11 | 既知差が記録された | `grep -n "依存の導入" tasks/README.md` | 1 件 |
| 12 | 契約検証が通る | `make task-validate` | exit 0 |
| 13 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 14 | 全体テストが不変 | `python -m pytest tests/ -q` | **開始前を先に測ってから比較** |
| 15 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- data/splits/ context/conventions.md src/` | 出力なし |

**判定14に注意**: 失敗件数の基準はホストによって異なる。**開始前を測っていなければ
`UNKNOWN` と記録する。**

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Task 1 の統合対象の一覧と、想定との照合結果
- 索引の現在の実測値（起票時の値との差）
- 記述に書いた内容の要点
- 起票した未解決事項の番号と slug
- 依存導入の実測（どの手段が使えたか、他ホストは未検証である旨）
- 資格情報の検出について、**通過経路が未検証である旨**
- **`deviations` を空にしない**
- §6 に、他ホストでの `make setup` 動作確認が未達であることを申し送る

- [ ] **Step 5: 受け皿へ書く**

`tasks/inbox.md` へ本 task の判断を 1 行以上置く。

- [ ] **Step 6: 送出と統合の起票**

```bash
git add tasks/T-2026-08-09-wiring-followup-and-integration/ tasks/inbox.md
git commit -m "docs(tasks): record the wiring follow-up"
BR=$(git branch --show-current)
git push origin "$BR"
gh pr create --base phase0 --head "$BR" \
  --title "feat: wiring verification results, host differences, and dependency setup" \
  --body-file tasks/T-2026-08-09-wiring-followup-and-integration/RESULT.md
```

**統合は行わない。自動統合も有効化しない。** 利用者が判断する。

**本文には、Task 1 で列挙した統合対象の一覧を含めること。** 何が全ホストへ配られるかを
利用者が判断できるようにする。

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 統合対象に想定外のコミットがある | **G1 停止。** 範囲を絞る案を提示し判断を仰ぐ。**自分で決めない** |
| 数値に差分が出た | **停止。** 記述の追記で数値が動くことはありえない |
| 未解決事項の表の列が壊れた | 修正してから進む。**壊れたまま commit しない** |
| 収穫器の出力が変わった | **G2 停止。** 追記だけで出力が変わるなら別の原因がある |
| 依存の導入手段が無い | **G3。** 代替案を提示して判断を仰ぐ |
| 資格情報の有効性を確かめられない | 失効の検出のみ実装し、**通過経路は未検証と記録** |
| 実装が SPEC の想定と食い違う | **実装に従う。** SPEC の誤りとして記録する |
| 全体テストの失敗が開始前より増えた | 本 task が壊した。停止して報告 |

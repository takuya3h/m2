# 全ホストへの伝播を実測し、契約の配布経路と軽量ビューの鮮度判定を整える

**task_id:** `T-2026-08-07-propagation-and-distribution`
**kind:** `impl`
**depends_on:** `T-2026-08-07-task-preflight`（PR #46・マージ済み）

---

## Goal

パイプラインの残る穴のうち、GPU を使わずに閉じられるものをまとめて処理する。

| Phase | 対象 | 現状 |
|---|---|---|
| A | 全ホストへの伝播（②） | **一度も検証していない** |
| B | 軽量ビューの鮮度判定 | **常時 FAIL の状態** |
| C | 契約の配布経路（①） | 手作業4アクション。残骸が出た実績あり |
| D | 凍結源の規約の明文化 | 前 task の申し送り |

## Phase B の背景（設計上の欠陥）

`context/auto/` の各ファイルは `generated_from_commit` に HEAD の sha を書いている。
ところが `context/auto/` 自体を commit すると HEAD が進むため、**生成物が自分自身の
commit によって即座に陳腐化する**。結果として `make context-check` はマージのたびに
必ず失敗し、検査として機能しない。

これは起票者の設計誤りである。`context/auto/` が反映しているのは HEAD の状態ではなく
**`runindex/` の状態**であり、`runindex/` が動かない限り再生成は不要である。したがって
生成元の識別子を **`runindex/` を最後に変更した commit** へ変える。

---

## 0. 前提と禁止事項

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git checkout -b feat/propagation-and-distribution origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | `runindex/**` を手で編集する |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 3 | `tools/harvest_runindex.py` を変更する |
| 4 | 学習・評価コードを変更する |
| 5 | 他ホストのファイルを変更する（Phase A は**読み取りのみ**） |
| 6 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 7 | テスト件数を合わせるためだけのテストを足す |
| 8 | GPU を使う |

**YAML と markdown 表の本文に半角パイプを書かない。**

---

# Phase A — 伝播の実測

## Task 1: 全ホストの到達状況を測る

**Files:**
- Create: `tasks/T-2026-08-07-propagation-and-distribution/propagation_audit.md`

**このフェーズは読み取り専用。他ホストに一切書き込まない。**

- [ ] **Step 1: 対象ホストとパスを確認する**

```bash
grep -E "^Host " ~/.ssh/config 2>/dev/null | awk '{print $2}' || echo "ssh config なし"
```

`tasks/README.md` の「ホスト環境の既知差」により、**efros は repo パスが他と異なる**。
パスを決め打ちしないこと。各ホストで repo を探す方式にする。

- [ ] **Step 2: 到達状況を一括で測る**

```bash
HOSTS=(lecun philip ilya bengio andrew he adam hinton ian dlsta efros)
OUT="$HOME/propagation_audit_$(date +%Y%m%d_%H%M).tsv"
printf "host\trepo\tbranch\thead\ttasks\tcontext_auto\tconventions\tclaude_skill\tcodex_skill\tbehind\n" > "$OUT"

for h in "${HOSTS[@]}"; do
  echo "=== $h ===" >&2
  line=$(ssh -o ConnectTimeout=10 -o BatchMode=yes "$h" '
    R=""
    for cand in ~/m2 ~/slocal2/m2 /home/ubuntu/slocal2/m2 ~/work/m2; do
      if [ -d "$cand/.git" ]; then R="$cand"; break; fi
    done
    if [ -z "$R" ]; then R=$(find ~ -maxdepth 4 -type d -name .git -path "*m2*" 2>/dev/null | head -1 | xargs -r dirname); fi
    if [ -z "$R" ]; then echo -e "NO_REPO\t-\t-\t-\t-\t-\t-\t-\t-"; exit 0; fi
    cd "$R" || exit 0
    BR=$(git branch --show-current 2>/dev/null)
    HD=$(git rev-parse --short HEAD 2>/dev/null)
    NT=$(ls -1d tasks/T-* 2>/dev/null | wc -l)
    NC=$(ls -1 context/auto/ 2>/dev/null | wc -l)
    CV=$([ -f context/conventions.md ] && echo yes || echo no)
    CS=$([ -f .claude/skills/task/SKILL.md ] && echo yes || echo no)
    XS=$([ -e .codex/skills/task ] && echo yes || echo no)
    BH=$(git rev-list --count HEAD..origin/phase0 2>/dev/null || echo "?")
    echo -e "$R\t$BR\t$HD\t$NT\t$NC\t$CV\t$CS\t$XS\t$BH"
  ' 2>/dev/null)
  [ -z "$line" ] && line=$(printf "UNREACHABLE\t-\t-\t-\t-\t-\t-\t-\t-")
  printf "%s\t%s\n" "$h" "$line" >> "$OUT"
done

echo; echo "===== 結果 ====="
column -t -s $'\t' "$OUT"
echo; echo "保存先: $OUT"
```

- [ ] **Step 3: keeper の実体を確認する**

「keeper が30分で全11台へ」という設計上の想定が、実際にどう実装されているかを確認する。

```bash
crontab -l 2>/dev/null | grep -i "keep\|sync\|fetch\|m2" || echo "crontab に該当なし"
systemctl --user list-timers 2>/dev/null | head -20 || true
ls -la scripts/ tools/ 2>/dev/null | grep -i "keep\|sync"
grep -rn "keeper" README.md docs/ 2>/dev/null | head -10
```

**実体が特定できなければ `UNKNOWN` と記録する。推測で「動いている」と書かない。**

- [ ] **Step 4: Syncthing の除外設定を確認する**

```bash
cat .stglobalignore 2>/dev/null || echo ".stglobalignore なし"
echo "--- git 追跡状況 ---"
git ls-files .claude/ .codex/ | head -20
echo "--- 追跡外のもの ---"
git status --porcelain --ignored .claude/ .codex/ 2>/dev/null | head -20
```

- [ ] **Step 5: G1 ゲート — 欠落を判定する**

| 観測 | 判定 |
|---|---|
| 全ホストで `tasks` `context_auto` `conventions` `claude_skill` `codex_skill` が揃う | **伝播は機能している。** Phase B へ |
| 一部ホストで欠落 | **`propagation_gap_found`。** 原因を記録し、ユーザーへ提示して続行の可否を尋ねる |
| `behind` が大きいホストがある | 同期の遅延。実測値を記録 |

`on_fail: ask` なので、**欠落があっても自動で停止せず、ユーザーに提示して判断を仰ぐ**。
本 task の主目的は実測であり、欠落の修復は別 task の対象である。

- [ ] **Step 6: `propagation_audit.md` に記録する**

```markdown
# 全ホスト伝播状況の実測（2026-08-07）

## 到達状況

| host | repo | branch | head | tasks | context/auto | conventions | .claude skill | .codex skill | behind |
|---|---|---|---|---|---|---|---|---|---|

## keeper の実体

（Step 3 の結果。特定できなければ UNKNOWN と明記）

## 追跡と同期の設定

（Step 4 の結果）

## 欠落と原因

（無ければ「なし」と明記）
```

- [ ] **Step 7: commit**

```bash
git add tasks/T-2026-08-07-propagation-and-distribution/propagation_audit.md
git commit -m "docs(tasks): audit propagation of contracts and conventions across hosts"
```

---

# Phase B — 軽量ビューの鮮度判定

## Task 2: 生成元の識別子を runindex 基準へ変える

**Files:**
- Modify: `tools/build_context.py`
- Modify: `tests/test_build_context.py`

- [ ] **Step 1: 現状を再現する**

```bash
make context-check; echo "exit=$?"
head -8 context/auto/STATE.md
echo "--- HEAD ---"
git rev-parse HEAD
echo "--- runindex を最後に変更した commit ---"
git log -1 --format='%H %cI' -- runindex/
```

**`generated_from_commit` が HEAD と一致せず FAIL していることを実測で確認する。**

- [ ] **Step 2: 失敗するテストを書く**

```python
# tests/test_build_context.py に追記
def test_stamp_uses_runindex_commit_not_head():
    """生成元は HEAD ではなく runindex の最終更新 commit である。

    context/auto/ を commit すると HEAD が進むため、HEAD を基準にすると
    生成物が自分自身の commit で陳腐化し、検査が常時失敗する。
    """
    from build_context import resolve_stamp_source

    source = resolve_stamp_source()
    assert source["path"] == "runindex/"
    assert source["commit"]
    assert source["date"]


def test_stamp_is_stable_when_only_head_moves():
    """runindex が変わらない限り、スタンプは変化しない。"""
    from build_context import resolve_stamp_source

    first = resolve_stamp_source()
    second = resolve_stamp_source()
    assert first == second
```

- [ ] **Step 3: 失敗を確認する**

```bash
python -m pytest tests/test_build_context.py -q
```

Expected: FAIL（`resolve_stamp_source` が未実装）

- [ ] **Step 4: 実装する**

```python
def resolve_stamp_source() -> dict[str, str]:
    """生成物のスタンプ元を返す。

    context/auto/ は runindex/ の投影であり、HEAD の状態ではない。
    HEAD を使うと context/auto/ 自身の commit で陳腐化するため、
    runindex/ を最後に変更した commit を基準にする。
    """
    out = subprocess.run(
        ["git", "log", "-1", "--format=%H%x09%cI", "--", "runindex/"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    ).stdout.strip()
    if not out:
        return {"path": "runindex/", "commit": "UNKNOWN", "date": "UNKNOWN"}
    commit, date = out.split("\t", 1)
    return {"path": "runindex/", "commit": commit, "date": date}
```

ヘッダの記述も変える。**何を基準にしているかが読み手に分かるようにする。**

```
generated_from:        runindex/
generated_from_commit: <runindex の最終更新 commit>
generated_from_date:   <その commit の日時>
runindex_counts:       index=<N> experiments=<N> verdicts=<N>
```

- [ ] **Step 5: テストが通ることを確認する**

```bash
python -m pytest tests/test_build_context.py -q
```

Expected: 全件 pass。**件数を実測して控える。**

- [ ] **Step 6: G2 ゲート — 連続実行と commit をまたいだ安定性を確認する**

```bash
make context
make context-check; echo "exit_1=$?"

# 生成物を commit して HEAD を進める
git add context/auto/ tools/build_context.py tests/test_build_context.py
git commit -m "fix(context): stamp views with the runindex commit instead of HEAD"

# HEAD が進んだあとも検査が通ること
make context-check; echo "exit_2=$?"
```

Expected: `exit_1=0` かつ `exit_2=0`

**これが本 Phase の核心である。** 従来は `exit_2` が非ゼロになっていた。

- [ ] **Step 7: 手編集は依然として検出されることを確認する**

```bash
echo "手編集テスト" >> context/auto/STATE.md
make context-check; echo "exit=$?"   # 非ゼロのはず
make context
make context-check; echo "exit=$?"   # 0 のはず
git checkout -- context/auto/ 2>/dev/null || true
```

**鮮度判定を緩めた結果、手編集まで見逃すようになっていないことを確認する。**

- [ ] **Step 8: commit**

Step 6 で既に commit 済みであれば、Step 7 の確認結果のみ RESULT に記録する。
追加の変更があれば commit する。

---

# Phase C — 契約の配布経路

## Task 3: 配布経路を設計する

現状は次の4アクションを人が行っている。

```
ファイルを受け取る → ダウンロード → ディレクトリを作る → 2ファイルを配置する
```

過去に `SPEC copy.md` という残骸が発生した。**一つの操作で完結し、失敗時に痕跡を残さない**
経路へ変える。

- [ ] **Step 1: 入力形式を決める**

契約は `spec.yaml` と `SPEC.md` の2ファイル（`kind: exp` では `prereg.md` も）。
これを一つのファイルとして受け渡すため、**単一のアーカイブまたは区切り付きテキスト**を
入力とする。

推奨する形式は次のとおり。**実装前に、どちらが運用に合うかを判断して RESULT に記録する。**

| 形式 | 利点 | 欠点 |
|---|---|---|
| tar アーカイブ | 構造をそのまま保持。バイナリ安全 | 中身を目視できない |
| 区切り付きテキスト | 目視できる。差分が読める | 区切り文字の衝突に注意 |

**区切り付きテキストを選ぶ場合**、SPEC 本文にヒアドキュメントが含まれるため、
区切りは十分に長く一意な文字列にすること（例: 40 文字以上のランダム文字列）。
**衝突検出を実装し、衝突した場合は失敗させる。**

- [ ] **Step 2: `tools/fetch_task.py` を実装する**

要件は次のとおり。

| # | 要件 |
|---|---|
| 1 | ローカルファイルパスまたは URL を入力に取る |
| 2 | **一時ディレクトリへ展開**し、`tasks/` へは直接書かない |
| 3 | `spec.yaml` から `meta.task_id` を読み、それをディレクトリ名とする |
| 4 | 同名の task が既に存在すれば**失敗**する（上書きしない） |
| 5 | 展開後に `make task-validate TASK=<id>` を実行する |
| 6 | **検証が失敗したら展開を巻き戻す**（`tasks/` に痕跡を残さない） |
| 7 | 成功時のみ `tasks/<task_id>/` を残し、次の操作を出力する |
| 8 | 一時ディレクトリは成否にかかわらず必ず削除する |

**要件6が最も重要である。** 検証に失敗した契約が `tasks/` に残ると、以後
`make task-validate` が常時 FAIL する。

- [ ] **Step 3: `make task-fetch` を追加する**

**挿入位置に注意。** 既存レシピの途中へ入れない。

```makefile
.PHONY: task-fetch
task-fetch:
	@.venv/bin/python tools/fetch_task.py --src $(SRC)
```

- [ ] **Step 4: テストを書く**

```python
# tests/test_fetch_task.py
```

最低限、次を検証する。**モックで足りる範囲に留め、無理に実 git 操作を模さない。**

| # | テスト |
|---|---|
| 1 | 正常な入力から `task_id` を抽出できる |
| 2 | `spec.yaml` が無い入力を拒否する |
| 3 | `meta.task_id` が無い入力を拒否する |
| 4 | 同名 task が存在する場合に拒否する |
| 5 | 区切り文字が本文に含まれる場合に拒否する（区切り形式を選んだ場合） |

- [ ] **Step 5: G3 ゲート — 一操作完結と痕跡なしを実地で確認する**

```bash
# 正常系
BEFORE=$(ls -1d tasks/T-* | wc -l)
# 実際の配布物を1つ作って投入する（例として現在の task 自身の複製を使い、task_id を変える）
# 手順は実装に合わせる

# 異常系: 検証に失敗する契約を投入し、痕跡が残らないことを確認する
make task-fetch SRC=/tmp/broken_task.txt; echo "exit=$?"
AFTER=$(ls -1d tasks/T-* | wc -l)
echo "before=$BEFORE after=$AFTER"
git status --porcelain tasks/
```

Expected: 異常系で `exit` が非ゼロ、`before` と `after` が同数、`git status` が空

**痕跡が残った場合は停止して報告する**（`distribution_leaves_residue`）。

- [ ] **Step 6: 使い方を文書化する**

`tasks/README.md` に「契約の受け取り」節を追加する。

```markdown
## 契約の受け取り

外部で起票された契約は次の一操作で取り込む。

    make task-fetch SRC=<path or url>

取得、展開、L1 と L2 の検証までを行う。検証に失敗した場合は展開を巻き戻すため、
`tasks/` に不完全な契約が残らない。成功した場合のみ次の操作が表示される。
```

- [ ] **Step 7: commit**

```bash
git add tools/fetch_task.py tests/test_fetch_task.py Makefile tasks/README.md
git commit -m "feat(tasks): fetch and validate contracts in one operation"
```

---

# Phase D — 規約への追記と自己適用

## Task 4: 凍結源の規約に適用時の扱いを明記する

**Files:**
- Modify: `context/conventions.md`

前 task の申し送り。`conventions#frozen_source` は「skip する経路は設けない」と書いている
一方、検査器の P5 は `kind: exp` のときのみ適用される。**両者は矛盾しないが、明文化されて
いない。**

- [ ] **Step 1: `frozen_source` 節に追記する**

```markdown
### 検査の適用範囲

凍結源の照合は、凍結源を使う契約に対して適用される。実行直前の検査では
`meta.kind` が `exp` の契約に対して実施し、それ以外は適用対象外として
未実施と記録する。

**適用対象となった場合に、照合を省略する経路は存在しない。**
照合に失敗した場合は実行を中止し、人へ差し戻す。
```

- [ ] **Step 2: 変更履歴に追記する**

日付と変更内容を書く。sha は Task 5 で追記する。

- [ ] **Step 3: アンカー数が変わっていないことを確認する**

```bash
grep -c '<a id=' context/conventions.md
```

Expected: `7`

- [ ] **Step 4: commit**

```bash
git add context/conventions.md
git commit -m "docs(context): clarify when the frozen-source check applies"
```

---

## Task 5: 自己契約の配置と完了判定

**Files:**
- Create: `tasks/T-2026-08-07-propagation-and-distribution/{spec.yaml,SPEC.md,RESULT.md}`

- [ ] **Step 1: `conventions_rev` を実測値へ置換する**

**起票者は現在の sha を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**
ただし Task 4 で `conventions.md` を変更するため、**Task 4 の commit 後の sha を使う**。

```bash
git log -1 --format=%h -- context/conventions.md
```

置換した値を RESULT §1 に記録する。§5 には書かない。

- [ ] **Step 2: `conventions.md` の変更履歴に sha を追記する**

- [ ] **Step 3: 自己検証**

```bash
make task-validate TASK=T-2026-08-07-propagation-and-distribution; echo "exit=$?"
make task-preflight TASK=T-2026-08-07-propagation-and-distribution; echo "exit=$?"
```

Expected: 両方 `exit=0`。preflight は `P2` `P3` `P4` `P5` が `SKIP`

- [ ] **Step 4: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 伝播が記録された | `propagation_audit.md` | 全ホスト分の行がある |
| 2 | 鮮度判定が commit をまたいで安定 | Task 2 Step 6 | `exit_1=0` `exit_2=0` |
| 3 | 手編集は検出される | Task 2 Step 7 | 非ゼロ → 0 |
| 4 | 配布が一操作で完結 | Task 3 Step 5 | 正常系 exit 0 |
| 5 | 失敗時に痕跡が残らない | 同上 | 件数不変・`git status` 空 |
| 6 | 凍結源の規約が明文化 | `grep -n "適用対象外" context/conventions.md` | 1 件以上 |
| 7 | アンカー数が不変 | `grep -c '<a id=' context/conventions.md` | 7 |
| 8 | 契約検証が通る | `make task-validate` | exit 0 |
| 9 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 10 | テストが全 pass | `python -m pytest tests/test_build_context.py tests/test_fetch_task.py -q` | 全 pass・件数を実測記録 |
| 11 | 全体テストが不変 | `python -m pytest tests/ -q` | 失敗 5 件のまま |
| 12 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- runindex/ experiments/ transfer/ data/splits/ tools/harvest_runindex.py` | 出力なし |

**判定11に注意**: 本 task の前から `tests/test_engines.py` 1 件と
`tests/test_research_logger.py` 4 件、計5件が失敗している。**5 のままなら PASS**、
増えたら停止して報告する。

- [ ] **Step 5: `RESULT.md` を書く**

必ず含めるもの。

- Phase A の到達状況表と、**keeper の実体（特定できなければ `UNKNOWN`）**
- 欠落があった場合はその一覧と、ユーザーへ提示した内容
- Task 2 Step 1 の実測（`generated_from_commit` と HEAD の差）
- Task 2 Step 6 の `exit_1` `exit_2`
- Task 3 Step 1 で選んだ入力形式と、その判断理由
- Task 3 Step 5 の正常系・異常系の結果
- テスト件数（実測）
- **`deviations` を空にしない**
- §6 に、Phase A で見つかった欠落の修復（別 task の対象）を申し送る

- [ ] **Step 6: push と PR**

```bash
git add tasks/T-2026-08-07-propagation-and-distribution/
git commit -m "feat(tasks): self-apply the contract to propagation and distribution"
git push -u origin feat/propagation-and-distribution
gh pr create --base phase0 \
  --title "feat(tasks): audit propagation, fix view staleness, add one-step distribution" \
  --body-file tasks/T-2026-08-07-propagation-and-distribution/RESULT.md
```

**マージは行わない。auto-merge も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 到達できないホストがある | `UNREACHABLE` として記録し続行。**停止しない** |
| repo が見つからないホストがある | `NO_REPO` として記録。パス探索の候補を RESULT に残す |
| keeper の実体が特定できない | `UNKNOWN` と記録。**推測で「動いている」と書かない** |
| 一部ホストで `.codex/skills/task` が無い | 前 task の成果がまだ届いていないだけの可能性。`behind` の値と併せて記録し、ユーザーへ提示 |
| `runindex/` の log が空 | `resolve_stamp_source` は `UNKNOWN` を返す仕様。RESULT に記録 |
| 鮮度判定を直したら手編集を検出しなくなった | **G2 停止。** 比較対象からスタンプ以外まで除外していないか確認 |
| 配布で痕跡が残った | **G3 停止。** `distribution_leaves_residue` として報告 |
| 区切り文字が本文と衝突した | 形式の選択を見直す。**衝突を検出せず通す実装にしない** |
| 全体テストの失敗が 5 件から増えた | 本 task が壊した。停止して報告 |

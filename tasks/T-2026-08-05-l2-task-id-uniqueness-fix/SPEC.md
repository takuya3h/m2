# L2-1 の task_id 一意性検査を ref ベースへ置換する

**task_id:** `T-2026-08-05-l2-task-id-uniqueness-fix`
**kind:** `impl`
**depends_on:** `T-2026-08-03-task-contract-bootstrap`

---

## 背景

`tools/validate_task.py` の L2-1 は、`task_id` の重複を
「その `spec.yaml` を**追加した commit** の数」で判定している。

```python
out = git log --all --name-only --diff-filter=A --pretty=format:%H -- tasks/*/spec.yaml
...
return commits if len(commits) > 1 else []
```

これは squash merge や rebase merge で壊れる。同じ `spec.yaml` が

- feature ブランチの元 commit
- `phase0` の squash された commit

の2箇所で「追加」されたことになり、**`len(commits) == 2` で FAIL する**。

さらに悪いことに、判定結果が**ホストごとに変わる**。旧ブランチを削除したホストでは1件、
ローカルに残っているホストでは2件になる。同じ commit を検証しているのに結論が変わるのは、
検証層としては致命的である。

本 repo は auto-merge が設定済みであり、この不具合は放置すれば必ず発火する。

## 修正方針

判定の鍵を「commit の数」から「**`refs/remotes/origin` 配下の各 ref に存在する
`spec.yaml` の `meta.created_at`**」へ変える。

| 状況 | 旧 | 新 |
|---|---|---|
| squash merge 後に旧ブランチ残存 | FAIL（偽陽性） | OK |
| rebase merge | FAIL（偽陽性） | OK |
| `meta.amendments` による改訂 | OK | OK |
| 別ホストが同じ `task_id` を独立に起票 | 検出 | 検出 |

`created_at` を同一性の鍵にする理由は、**改訂しても変わらず、独立起票ではまず一致しない**
ためである。blob hash を鍵にすると `RESULT.md` 追記や amendments で偽陽性が復活する。

### 既知の限界（RESULT へ必ず記載すること）

衝突しているブランチを fetch していないホストでは検出できない（偽陰性）。
偽陽性より安全側であるため許容する。この限界を `tasks/README.md` に明記する。

---

## 前提と禁止事項

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git checkout -b fix/l2-task-id-uniqueness origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | `runindex/**` を手で編集する |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 3 | `tools/harvest_runindex.py` を変更する |
| 4 | repo root の6ファイルを移動・削除する |
| 5 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 6 | テスト件数を合わせるためだけのテストを足す |
| 7 | `git update-ref` で作った検査用 ref を残したまま終える |

**YAML の文字列値に半角パイプを書かない。** L1-3 で reject される。

---

## Task 1: 現状診断（Phase A）

**この Task は読み取りのみ。ファイルを変更しない。**

- [ ] **Step 1: 現在このバグが顕在化しているか確認する**

```bash
echo "===== add-commit の数（旧 L2-1 の入力） ====="
git log --all --name-only --diff-filter=A --pretty=format:%H -- 'tasks/*/spec.yaml'

echo; echo "===== 現在の L2 結果 ====="
make task-validate; echo "exit=$?"

echo; echo "===== origin の ref 一覧 ====="
git for-each-ref --format='%(refname)' refs/remotes/origin
```

- [ ] **Step 2: 結果を分類する**

| 観測 | 意味 | 記録先 |
|---|---|---|
| 同じ task_id が2つ以上の commit で追加されている | **バグは既に顕在化している**。`make task-validate` は現在 FAIL しているはず | RESULT §2 |
| 各 task_id が1 commit のみ | バグは潜在。Task 2 のユニットテストで示す | RESULT §2 |

**どちらであっても実測値をそのまま RESULT に書くこと。** 推測で「既に壊れている」と書かない。

- [ ] **Step 3: commit しない**

この Task は診断のみ。次へ進む。

---

## Task 2: 失敗するテストを追加（Phase A）

**Files:**
- Modify: `tests/test_validate_task.py`

- [ ] **Step 1: 新しい関数シグネチャに対するテストを書く**

既存の `test_task_id_conflict_detected` を**置き換える**。`self_ref` 引数は廃止する。

```python
# tests/test_validate_task.py
# 既存の import 行に task_identity_on_refs を追加する
from validate_task import (  # noqa: E402
    Finding,
    resolve_sigma_policy,
    task_id_conflicts,
    validate_l1,
)


def test_task_id_single_ref_is_not_conflict():
    identities = {"2026-08-05T09:00:00Z": ["refs/remotes/origin/phase0"]}
    assert task_id_conflicts("T-2026-08-05-example-task", identities) == []


def test_task_id_same_created_at_across_refs_is_not_conflict():
    """squash merge 後に旧ブランチが残っている状態の回帰テスト。"""
    identities = {
        "2026-08-05T09:00:00Z": [
            "refs/remotes/origin/phase0",
            "refs/remotes/origin/feat/task-contract-bootstrap",
        ]
    }
    assert task_id_conflicts("T-2026-08-05-example-task", identities) == []


def test_task_id_differing_created_at_is_conflict():
    """別ホストが同じ task_id を独立に起票した状態。"""
    identities = {
        "2026-08-05T09:00:00Z": ["refs/remotes/origin/phase0"],
        "2026-08-05T11:30:00Z": ["refs/remotes/origin/exp/lecun-foo"],
    }
    conflicts = task_id_conflicts("T-2026-08-05-example-task", identities)
    assert len(conflicts) == 2
    assert any("phase0" in c for c in conflicts)
```

- [ ] **Step 2: 置換前の実装で失敗することを確認する**

```bash
.venv/bin/python -m pytest tests/test_validate_task.py -q
```

Expected: FAIL（旧 `task_id_conflicts` は引数3つで、`existing` の意味も違うため）

**ここが G1 ゲート。失敗を確認できなければ停止して報告すること。**

- [ ] **Step 3: commit**

```bash
git add tests/test_validate_task.py
git commit -m "test(tasks): add ref-based L2-1 uniqueness tests (currently failing)"
```

---

## Task 3: 実装を置換（Phase B）

**Files:**
- Modify: `tools/validate_task.py`

- [ ] **Step 1: 旧関数を削除する**

`all_task_ids_in_history()` を**関数ごと削除**する。他からの参照が無いことを確認する。

```bash
grep -n "all_task_ids_in_history" tools/ tests/ -r
```

Expected: 削除後に出力なし

- [ ] **Step 2: 新しい関数を追加する**

`task_id_conflicts` の直前に配置する。

```python
def _origin_refs() -> list[str]:
    """refs/remotes/origin 配下の ref 名を返す。origin/HEAD は除く。"""
    out = subprocess.run(
        ["git", "for-each-ref", "--format=%(refname)", "refs/remotes/origin"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    ).stdout
    refs = [line.strip() for line in out.splitlines() if line.strip()]
    return [ref for ref in refs if not ref.endswith("/HEAD")]


def task_identity_on_refs(task_id: str) -> dict[str, list[str]]:
    """task_id を含む ref を meta.created_at 別に集める。

    戻り値は created_at をキー、その値を持つ ref のリストを値とする dict。
    ref に spec.yaml が無い場合と、解析できない場合はその ref を無視する。
    """
    spec_path = f"tasks/{task_id}/spec.yaml"
    identities: dict[str, list[str]] = {}
    for ref in _origin_refs():
        shown = subprocess.run(
            ["git", "show", f"{ref}:{spec_path}"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=False,
        )
        if shown.returncode != 0:
            continue
        try:
            data = yaml.safe_load(shown.stdout) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(data, dict):
            continue
        created_at = str(data.get("meta", {}).get("created_at", "") or "")
        if created_at:
            identities.setdefault(created_at, []).append(ref)
    return identities


def task_id_conflicts(task_id: str, identities: dict[str, list[str]]) -> list[str]:
    """同じ task_id が異なる meta.created_at で複数 ref に存在すれば衝突とみなす。

    squash merge や rebase merge で同一 task が複数 ref に現れるのは正常なので、
    created_at が一致する限り衝突としない。
    """
    if len(identities) <= 1:
        return []
    return [
        f"{created_at} <- {', '.join(sorted(refs))}"
        for created_at, refs in sorted(identities.items())
    ]
```

- [ ] **Step 3: 呼び出し側を差し替える**

`validate_l2` の冒頭を次に置き換える。

```python
    conflicts = task_id_conflicts(task_id, task_identity_on_refs(task_id))
    if conflicts:
        findings.append(
            Finding(
                "L2-1",
                "meta.task_id",
                "同じ task_id が異なる created_at で複数の ref に存在します: "
                + "; ".join(conflicts),
            )
        )
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
.venv/bin/python -m pytest tests/test_validate_task.py -q
```

Expected: 全件 pass。**件数を控えて RESULT に実測で書くこと。**

- [ ] **Step 5: commit**

```bash
git add tools/validate_task.py
git commit -m "fix(tasks): make L2-1 uniqueness check ref-based instead of commit-based"
```

---

## Task 4: 実 ref を使った end-to-end 確認（Phase B）

ユニットテストは純関数のみを検査する。ここでは実際の git ref を使って、
**同一 task が複数 ref に存在しても発火しないこと**を確認する。

- [ ] **Step 1: 検査用の ref を作る**

```bash
git update-ref refs/remotes/origin/_l2check-dup HEAD
git for-each-ref --format='%(refname)' refs/remotes/origin | grep _l2check
```

Expected: `refs/remotes/origin/_l2check-dup` が表示される

- [ ] **Step 2: 検証を回す**

```bash
make task-validate; echo "exit=$?"
```

Expected: `exit=0`。L2-1 の finding が出ないこと。

- [ ] **Step 3: 検査用 ref を必ず削除する**

```bash
git update-ref -d refs/remotes/origin/_l2check-dup
git for-each-ref --format='%(refname)' refs/remotes/origin | grep _l2check || echo "cleaned"
```

Expected: `cleaned`

**この Step を飛ばしてはならない。** 残すと以後の検証結果が汚染される。

- [ ] **Step 4: 削除後にもう一度検証する**

```bash
make task-validate; echo "exit=$?"
```

Expected: `exit=0`

---

## Task 5: 文書の更新（Phase B）

**Files:**
- Modify: `tasks/README.md`
- Modify: `README.md`

- [ ] **Step 1: `tasks/README.md` の検証表を更新する**

L1 の行の「task_id 一意」という記述を削除し（一意性は L2 の責務）、L2 の行に
ref ベースであることと偽陰性の限界を書く。

```markdown
| L1 | スキーマ・書式・パイプ混入・task_id とディレクトリ名の一致 | なし | 1 秒 |
| L2 | 参照解決（分母・凍結源・split・規約版・sigma_policy 継承）と task_id の重複 | runindex, git | 数秒 |
```

同ファイルの末尾に次を追記する。

```markdown
## task_id の重複検出の範囲

L2-1 は `refs/remotes/origin` 配下の各 ref にある `spec.yaml` を読み、
`meta.created_at` が食い違う場合のみ衝突とみなす。
squash merge や rebase merge で同じ task が複数 ref に現れるのは正常なので発火しない。

**限界**: 衝突しているブランチを fetch していないホストでは検出できない。
検出は fetch 済みの範囲に限られる。偽陽性を避けるための意図的な設計である。
```

- [ ] **Step 2: `README.md` の L2 説明を更新する**

「task_id の履歴衝突」という記述を「`refs/remotes/origin` 間での task_id 重複」に変える。

- [ ] **Step 3: 記述と実装の一致を確認する**

```bash
grep -n "履歴衝突" README.md tasks/README.md || echo "no stale wording"
```

Expected: `no stale wording`

- [ ] **Step 4: commit**

```bash
git add README.md tasks/README.md
git commit -m "docs(tasks): describe ref-based L2-1 uniqueness and its known blind spot"
```

---

## Task 6: 自己契約の配置と完了判定

**Files:**
- Create: `tasks/T-2026-08-05-l2-task-id-uniqueness-fix/spec.yaml`（配布物をそのまま配置）
- Create: `tasks/T-2026-08-05-l2-task-id-uniqueness-fix/SPEC.md`（このファイル）
- Create: `tasks/T-2026-08-05-l2-task-id-uniqueness-fix/RESULT.md`

- [ ] **Step 1: `conventions_rev` を実測値へ合わせる**

配布された `spec.yaml` は `conventions_rev: "8b17c4d"` を持つ。現在のブランチで
`context/conventions.md` を最後に変更した commit を確認する。

```bash
git log -1 --format=%h -- context/conventions.md
```

異なる場合は `spec.yaml` の値を実測値へ置き換え、**RESULT §5 の deviations に記録する**。
一致する場合は変更しない。

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-05-l2-task-id-uniqueness-fix; echo "exit=$?"
```

Expected: `OK` / `1 task(s), 0 failed` / `exit=0`

`L2-8` の WARN（母集団の差）が出た場合は**正常**である。起票時点の
`created_from.counts` は `index 749 / experiments 206 / verdicts 1038` であり、
その後 runindex が動いていれば WARN が出る。WARN の内容を RESULT §2 に記録する。

- [ ] **Step 3: 完了判定を全て確認する**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 全 task の検証が通る | `make task-validate` | exit 0 |
| 2 | validator テストが全件 pass | `.venv/bin/python -m pytest tests/test_validate_task.py -q` | 全 pass・件数を実測記録 |
| 3 | 全体テストが Task 実行前と同じ | `.venv/bin/python -m pytest tests/ -q` | 失敗件数が実行前と不変 |
| 4 | 旧関数が消えている | `grep -rn "all_task_ids_in_history" tools/ tests/` | 出力なし |
| 5 | 死に引数が消えている | `grep -n "self_ref" tools/validate_task.py` | 出力なし |
| 6 | 複数 ref でも発火しない | Task 4 | exit 0 |
| 7 | 検査用 ref が残っていない | `git for-each-ref refs/remotes/origin \| grep _l2check` | 出力なし |
| 8 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- runindex/ experiments/ transfer/ data/splits/ tools/harvest_runindex.py` | 出力なし |
| 9 | 文書が実装と一致 | Task 5 Step 3 | `no stale wording` |

**判定3に注意**: 本 task の前から `tests/test_engines.py` と `tests/test_research_logger.py` の
計5件が失敗していると報告されている。**件数が5のままであれば「不変」として PASS** とする。
増えていれば本 task が壊したことになるので停止して報告する。

- [ ] **Step 4: `RESULT.md` を書く**

`tasks/_templates/impl/RESULT.md` を土台に全セクションを埋める。次を必ず含める。

- Task 1 Step 1 の**生の出力**（add-commit の数と、その時点の `make task-validate` の exit code）
- 置換前後のテスト件数（実測。**11 から何件になったか**）
- Task 4 の end-to-end 結果
- `conventions_rev` を変更したか
- **`deviations` を空にしない。** 逸脱が無ければ「なし」と明記する
- 既知の限界（fetch 範囲外の衝突は検出できない）を §6 未解決・申し送りへ

- [ ] **Step 5: commit して push**

```bash
git add tasks/T-2026-08-05-l2-task-id-uniqueness-fix/
git commit -m "feat(tasks): self-apply the contract to the L2-1 uniqueness fix"
git push -u origin fix/l2-task-id-uniqueness
```

- [ ] **Step 6: PR を作る**

```bash
gh pr create --base phase0 \
  --title "fix(tasks): make L2-1 task_id uniqueness check ref-based" \
  --body-file tasks/T-2026-08-05-l2-task-id-uniqueness-fix/RESULT.md
```

**auto-merge が有効な場合、この PR のマージ自体が修正の実地検証になる。**
マージ後に別ホストで `make task-validate` を回し、exit 0 であることを確認して
RESULT §6 に追記すること（本 task の commit 後に判明する情報なので、追記は
`meta.amendments` ではなく RESULT の申し送りへ書く）。

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| Task 1 で `make task-validate` が既に FAIL している | **バグが顕在化済み**。そのまま修正へ進み、RESULT に「顕在化していた」と実測で記録する |
| `refs/remotes/origin` が空（remote 未設定のホスト） | `task_identity_on_refs` は空 dict を返し衝突なしになる。これは仕様。RESULT に記録する |
| `git show` が巨大な出力を返す | 対象は `spec.yaml` のみなので想定外。停止して報告 |
| 全体テストの失敗が5件から増えた | 本 task が壊した。停止して報告 |
| `conventions_rev` の実測値が見つからない | `UNKNOWN` とせず停止して報告（規約版が特定できない状態で契約を commit しない） |

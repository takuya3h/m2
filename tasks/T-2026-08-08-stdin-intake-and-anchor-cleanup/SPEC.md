# 契約の取り込みを標準入力へ対応させ、収穫器に残る終端一致を揃える

**task_id:** `T-2026-08-08-stdin-intake-and-anchor-cleanup`
**kind:** `impl`
**depends_on:** `T-2026-08-08-regex-audit-and-cleanup`（PR #48・マージ済み）

---

## Goal

### Phase A の背景

契約の取り込みは一つの操作で完結するようになったが、**供給元が外部のテキスト面である
ため、実行ホストへ届けるまでに中間ファイルが必要**である。実際に、取り込みが
「入力が見つかりません」で失敗した。供給元はファイルを手元へ渡すだけで、実行ホストの
ファイルシステムには置けない。

標準入力に対応すれば、貼り付けで完結し、中間ファイルが残らない。失敗しても何も残らない。

### Phase B の背景

前 task で終端一致の統一を行ったが、`tools/harvest_runindex.py` は当時の禁止事項に
より対象外とした。**統一が中途半端なまま残っている。** 収穫器は索引の生成元であり、
ここに同型の脆弱性が残ると、以後の検証がすべてその上に乗る。

### Phase C の背景

伝播監査は前々 task で試みたが、監査を実施したホストから他ホストへ到達できず、
**全ホストが未確認のまま**である。到達可能なホストがあるなら、そこから測り直す。

---

## 0. 前提と禁止事項

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git checkout -b feat/stdin-intake-and-anchor-cleanup origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | `runindex/**` の生成物を手で編集する |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更・削除する |
| 3 | 学習・評価コードを変更する |
| 4 | `context/conventions.md` を変更する（本 task の範囲外） |
| 5 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 6 | テスト件数を合わせるためだけのテストを足す |
| 7 | GPU を使う |
| 8 | 他ホストへ書き込む（Phase C は**読み取りのみ**） |

### 本 task で解禁するもの

**`tools/harvest_runindex.py` の変更を解禁する。** ただし変更は**終端一致の書き方のみ**に
限り、収穫の条件・列・除外規則には手を触れない。G2 でそれを実測により担保する。

### 起票者からの申し送り（重要）

前 2 task で、起票者が書いた**検証コマンドが検証対象を検証できていない**誤りが連続した。

| task | 誤り |
|---|---|
| 実行前検査 | 変数だけを消す方法では、経路が残るため無効化できていなかった |
| 終端一致 | 攻撃入力の形が誤っており、全パターンで陰性になり脆弱性を隠していた |

**本 SPEC の検証コマンドも同型の誤りを含みうる。** 各ゲートでは、
**陽性対照（意図的に失敗させる入力）が実際に失敗すること**を必ず確認すること。
陽性対照が失敗しない場合、その検証コマンドは無効であり、修正して記録すること。

---

# Phase A — 標準入力からの取り込み

## Task 1: 陽性対照の設計

**Files:** なし（設計と実測のみ）

実装前に「何が起きたら失敗と分かるか」を決める。

- [ ] **Step 1: 現在の取り込み経路を確認する**

```bash
.venv/bin/python tools/fetch_task.py --help
grep -n "argparse\|add_argument\|--src\|--pack" tools/fetch_task.py | head -20
grep -n "def \|_read_source\|urlopen\|Path(" tools/fetch_task.py | head -30
```

- [ ] **Step 2: 陽性対照を4種決める**

| # | 入力 | 期待 |
|---|---|---|
| N1 | 正常なバンドル | 取り込み成功・`tasks/<id>/` が残る |
| N2 | 先頭行が宣言でないテキスト | 失敗・痕跡なし |
| N3 | 区切りが本文と衝突するバンドル | 失敗・痕跡なし |
| N4 | 検証を通らない契約を含むバンドル | 失敗・**巻き戻し**・痕跡なし |

**N2 から N4 が実際に失敗することを確認できなければ、この検証は無効である。**

- [ ] **Step 3: 陽性対照の入力を作る**

```bash
mkdir -p /tmp/intake_probe
# N1: 既存契約から組み立てる
.venv/bin/python tools/fetch_task.py --pack tasks/T-2026-08-08-regex-audit-and-cleanup \
  > /tmp/intake_probe/n1_valid.txt 2>/dev/null || echo "pack に失敗"
head -1 /tmp/intake_probe/n1_valid.txt

# N2: 宣言のないテキスト
printf 'これはバンドルではありません\n' > /tmp/intake_probe/n2_no_header.txt

# N3 と N4 は N1 を加工して作る。加工方法は実装を読んでから決める
```

**N1 の `task_id` は既存と重複するため、そのままでは取り込めない。**
重複拒否が働くことも確認対象に含める（これも陽性対照の一つ）。

- [ ] **Step 4: 実測を記録する**

RESULT §1 に、現在の取り込み経路と、陽性対照4種の内容を記録する。

---

## Task 2: 標準入力への対応

**Files:**
- Modify: `tools/fetch_task.py`
- Modify: `tests/test_fetch_task.py`
- Modify: `Makefile`
- Modify: `tasks/README.md`

- [ ] **Step 1: 失敗するテストを書く**

```python
# tests/test_fetch_task.py に追記
def test_src_dash_reads_stdin(monkeypatch, capsys):
    """--src - は標準入力からバンドルを読む。"""
    import io
    from fetch_task import read_source

    monkeypatch.setattr("sys.stdin", io.StringIO("#!TASK-BUNDLE v1 delim=X\n"))
    text = read_source("-")
    assert text.startswith("#!TASK-BUNDLE")


def test_stdin_empty_input_is_rejected(monkeypatch):
    """空の標準入力は拒否する。"""
    import io
    from fetch_task import BundleError, read_source

    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    with pytest.raises(BundleError):
        read_source("-")
```

- [ ] **Step 2: 失敗を確認する**

```bash
python -m pytest tests/test_fetch_task.py -q
```

Expected: FAIL（`read_source` が未実装、または `-` を扱えない）

**FAIL しなければ、既に実装済みかテストが対象を検証していない。** どちらかを実測で判別する。

- [ ] **Step 3: 実装する**

`--src -` のとき `sys.stdin.read()` から読む。**空入力は拒否する。**

既存の取り込み処理は**一時ディレクトリへ展開してから設置し、検証に失敗したら巻き戻す**
実装になっている。標準入力からの読み取りは**入力の取得方法だけを変える**ものであり、
その後の流れは共通化すること。**巻き戻しの処理を複製しない。**

- [ ] **Step 4: Makefile を更新する**

**挿入位置に注意。** 既存レシピの途中へ入れない。

```makefile
.PHONY: task-paste
task-paste:
	@.venv/bin/python tools/fetch_task.py --src -
```

`task-fetch` は既存のまま残し、標準入力用の別名を足す。**利用者が用途で選べるようにする。**

- [ ] **Step 5: G1 ゲート — 陽性対照を全て投げる**

```bash
BEFORE=$(ls -1d tasks/T-* | wc -l)

echo "===== N1 正常（重複するため拒否されるはず） ====="
make task-paste < /tmp/intake_probe/n1_valid.txt; echo "exit=$?"

echo "===== N2 宣言なし ====="
make task-paste < /tmp/intake_probe/n2_no_header.txt; echo "exit=$?"

echo "===== N3 区切り衝突 ====="
make task-paste < /tmp/intake_probe/n3_collision.txt; echo "exit=$?"

echo "===== N4 検証不合格 ====="
make task-paste < /tmp/intake_probe/n4_invalid.txt; echo "exit=$?"

echo "===== 空入力 ====="
printf '' | make task-paste; echo "exit=$?"

AFTER=$(ls -1d tasks/T-* | wc -l)
echo "before=$BEFORE after=$AFTER"
git status --porcelain tasks/
```

Expected: **N2 から N4 と空入力がすべて非ゼロで終了**し、`before` と `after` が同数、
`git status` が空

**一つでも成功してしまう、または痕跡が残る場合は停止して報告する**
（`stdin_intake_leaves_residue`）。

- [ ] **Step 6: 正常系を確認する**

`task_id` を変えたバンドルを作り、実際に取り込めることを確認する。
確認後は取り込んだものを削除し、作業領域を元に戻す。

```bash
# 例: N1 の task_id を書き換えたものを作って投入する
# 手順は実装に合わせる。投入後は git status で確認し、確認用の契約は削除する
```

- [ ] **Step 7: 文書を更新する**

`tasks/README.md` の「契約の受け取り」節に追記する。

```markdown
供給元が外部のテキスト面である場合、実行ホストへファイルを置けないことがある。
その場合は標準入力から取り込む。

    make task-paste
    （バンドルを貼り付けて入力終了）

中間ファイルを作らないため、失敗しても作業領域に何も残らない。
```

- [ ] **Step 8: commit**

```bash
git add tools/fetch_task.py tests/test_fetch_task.py Makefile tasks/README.md
git commit -m "feat(tasks): accept contract bundles from standard input"
```

---

# Phase B — 収穫器の終端一致

## Task 3: 収穫器のアンカーを揃える

**Files:**
- Modify: `tools/harvest_runindex.py`

**変更は終端一致の書き方のみ。収穫の条件・列・除外規則には触れない。**

- [ ] **Step 1: 変更前の状態を保存する**

```bash
mkdir -p /tmp/harv_before
cp runindex/index.csv runindex/experiments.csv runindex/per_class.csv runindex/verdicts.csv /tmp/harv_before/
md5sum runindex/*.csv > /tmp/harv_before/hashes.txt
python - <<'PY'
import csv, collections, json
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
ex = [c for c in cols if "exclu" in c.lower()]
snap = {
    "index_rows": len(rows),
    "index_cols": len(cols),
    "exclude_breakdown": {c: dict(collections.Counter(r.get(c, "") for r in rows)) for c in ex},
}
json.dump(snap, open("/tmp/harv_before/snapshot.json", "w"), ensure_ascii=False, indent=2)
print("rows:", snap["index_rows"], "cols:", snap["index_cols"])
for c, v in snap["exclude_breakdown"].items():
    print(c, dict(sorted(v.items(), key=lambda kv: -kv[1])[:8]))
PY
```

- [ ] **Step 2: 対象箇所を列挙する**

```bash
grep -n 're\.compile\|re\.match\|re\.fullmatch\|re\.search' tools/harvest_runindex.py
echo "--- 終端が \$ のもの ---"
grep -n '\$"' tools/harvest_runindex.py | grep -v '\\\\Z'
```

- [ ] **Step 3: 各箇所の挙動を実測する**

**推測で「安全」「危険」と判断しない。** 各パターンについて、末尾改行つき入力が
一致するかを実際に測る。

```bash
python - <<'PY'
import re, pathlib
src = pathlib.Path("tools/harvest_runindex.py").read_text(encoding="utf-8")
for m in re.finditer(r're\.compile\(\s*r?["\']([^"\']+)["\']', src):
    pat = m.group(1)
    line = src[:m.start()].count("\n") + 1
    if not pat.endswith("$"):
        continue
    rx = re.compile(pat)
    # 一致する最小の例を作れないパターンもあるため、実際に使われている値で試す必要がある
    print(f"line {line}: {pat}")
PY
```

**パターン単体では試せない場合、実際に渡される値の形を確認してから試すこと。**
試せない箇所は `UNKNOWN` と記録し、**変更しない**。

- [ ] **Step 4: 修正する**

終端が `$` のものを `\Z` へ、`re.match` を `re.fullmatch` へ揃える。
**`re.search` を `fullmatch` に変えてはならない。** 意味が変わる。

`re.search` で終端に `$` を使っている箇所は、**意図的に部分一致を狙っている可能性**が
ある。変更前に用途を読み、判断できなければ変更せず `UNKNOWN` として記録する。

- [ ] **Step 5: G2 ゲート — 出力が変わらないことを実測する**

```bash
make runindex 2>&1 | tail -20
echo "===== ハッシュ比較 ====="
md5sum runindex/*.csv > /tmp/harv_after.txt
diff /tmp/harv_before/hashes.txt /tmp/harv_after.txt && echo "IDENTICAL" || echo "DIFFERS"
echo "===== 行数と除外内訳 ====="
python - <<'PY'
import csv, collections, json
before = json.load(open("/tmp/harv_before/snapshot.json"))
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
ex = [c for c in cols if "exclu" in c.lower()]
after = {
    "index_rows": len(rows),
    "index_cols": len(cols),
    "exclude_breakdown": {c: dict(collections.Counter(r.get(c, "") for r in rows)) for c in ex},
}
print("行数:", before["index_rows"], "->", after["index_rows"])
print("列数:", before["index_cols"], "->", after["index_cols"])
print("除外内訳 不変:", before["exclude_breakdown"] == after["exclude_breakdown"])
PY
```

Expected: `IDENTICAL`、行数・列数・除外内訳がすべて不変

**一つでも変われば停止して報告する**（`harvester_output_changed`）。終端一致の書き方を
変えただけで出力が変わるなら、**その差分こそが従来の脆弱性の実害**である。差分の内容を
記録してから判断を仰ぐ。

- [ ] **Step 6: 冪等性を確認する**

```bash
make runindex >/dev/null 2>&1
md5sum runindex/*.csv > /tmp/harv_after2.txt
diff /tmp/harv_after.txt /tmp/harv_after2.txt && echo "IDEMPOTENT OK" || echo "IDEMPOTENT NG"
```

- [ ] **Step 7: 軽量ビューへの影響を確認する**

```bash
make context
make context-check; echo "exit=$?"
git status --porcelain context/auto/
```

収穫器の出力が不変なら、軽量ビューも不変のはずである。**差分が出たら停止して報告する。**

- [ ] **Step 8: commit**

```bash
git add tools/harvest_runindex.py
git commit -m "fix(runindex): align end-of-string anchors with the validation stack"
```

---

# Phase C — 到達可能な範囲での伝播監査

## Task 4: 到達範囲を測り直す

**Files:**
- Modify: `tasks/T-2026-08-07-propagation-and-distribution/propagation_audit.md`（追記）

前回の監査では、実施ホストから他ホストへ到達できなかった。**到達できないこと自体が
実測結果**であり、伝播の欠落を意味しない。今回は到達可能な範囲を広げられるかを試す。

**このフェーズは読み取り専用。他ホストへ一切書き込まない。**

- [ ] **Step 1: 到達手段を確認する**

```bash
echo "=== ssh config ==="
grep -E "^Host |HostName|ProxyJump|ProxyCommand" ~/.ssh/config 2>/dev/null | head -40
echo "=== 名前解決 ==="
for h in lecun philip ilya bengio andrew he adam hinton ian dlsta efros; do
  printf "%-8s " "$h"
  getent hosts "$h" >/dev/null 2>&1 && echo "resolvable" || echo "NG"
done
echo "=== 経路 ==="
ip route 2>/dev/null | head -5
```

- [ ] **Step 2: 到達できるホストを特定する**

```bash
for h in lecun philip ilya bengio andrew he adam hinton ian dlsta efros; do
  printf "%-8s " "$h"
  timeout 8 ssh -o ConnectTimeout=5 -o BatchMode=yes "$h" 'echo OK' 2>&1 | head -1
done
```

- [ ] **Step 3: 到達できたホストで状態を測る**

前 task の監査スクリプトを、到達できたホストに限って実行する。
**repo パスを決め打ちしない**（既知差の記録による）。

- [ ] **Step 4: G3 ゲート — 到達範囲を判定する**

| 観測 | 対応 |
|---|---|
| 一台も到達できない | 前回と同じ。**「未確認」として記録**し、続行 |
| 一部到達できた | 到達分を記録し、残りは `UNKNOWN` と明記 |
| 全台到達できた | 完全な監査結果を記録 |

`on_fail: ask` である。**到達できなくても自動で停止せず、結果を提示して判断を仰ぐ。**

**「到達できなかった」を「伝播していない」と書かないこと。** 両者は別である。

- [ ] **Step 5: 追記する**

前 task の `propagation_audit.md` に、日付を明示した節として追記する。
**既存の記録を書き換えない。**

```markdown
## 再監査（2026-08-08）

### 到達手段の実測

### 到達できたホスト

### 到達できなかったホスト

（理由を実測で。到達不能は伝播の欠落を意味しない）

### 結論
```

- [ ] **Step 6: commit**

```bash
git add tasks/T-2026-08-07-propagation-and-distribution/propagation_audit.md
git commit -m "docs(tasks): re-audit propagation within the reachable scope"
```

---

## Task 5: 自己契約の配置と完了判定

**Files:**
- Create: `tasks/T-2026-08-08-stdin-intake-and-anchor-cleanup/RESULT.md`

`spec.yaml` と `SPEC.md` は取り込みにより既に配置されている。

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-08-stdin-intake-and-anchor-cleanup; echo "exit=$?"
make task-preflight TASK=T-2026-08-08-stdin-intake-and-anchor-cleanup; echo "exit=$?"
```

Expected: 両方 `exit=0`

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 標準入力から取り込める | Task 2 Step 6 | 成功 |
| 2 | 陽性対照が全て失敗する | Task 2 Step 5 | N2 から N4 と空入力が非ゼロ |
| 3 | 失敗時に痕跡が残らない | 同上 | 件数不変・`git status` 空 |
| 4 | 収穫器の出力が不変 | Task 3 Step 5 | `IDENTICAL` |
| 5 | 収穫器が冪等 | Task 3 Step 6 | `IDEMPOTENT OK` |
| 6 | 軽量ビューが不変 | Task 3 Step 7 | `git status` 空 |
| 7 | 到達範囲が区別して記録 | `propagation_audit.md` | 到達分と未確認分が別 |
| 8 | 契約検証が通る | `make task-validate` | exit 0 |
| 9 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 10 | テストが全 pass | `python -m pytest tests/test_fetch_task.py -q` | 全 pass・件数を実測記録 |
| 11 | 全体テストが不変 | `python -m pytest tests/ -q` | 失敗 5 件のまま |
| 12 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- experiments/ transfer/ data/splits/ context/conventions.md` | 出力なし |

**判定11に注意**: 本 task の前から 5 件が失敗している。**5 のままなら PASS**、増えたら停止。

**判定4は禁止領域の例外である。** `runindex/` の生成物は `make runindex` により
再生成されるが、**内容が変わってはならない**。ハッシュが一致することを確認する。

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Task 1 の陽性対照4種の設計と、**実際に失敗したかどうかの生の出力**
- 陽性対照が失敗しなかったものがあれば、その事実と対応
- Task 3 Step 3 の実測（各パターンの挙動。試せなかったものは `UNKNOWN`）
- 変更しなかった箇所とその理由（`re.search` の用途など）
- Task 3 Step 5 のハッシュ比較結果
- Phase C の到達範囲（到達できた台数と、できなかった台数・理由）
- テスト件数（実測。**前回から何件になったか**）
- **`deviations` を空にしない**
- §6 に、未確認のまま残るホストを引き続き申し送る

- [ ] **Step 5: push と PR**

```bash
git add tasks/T-2026-08-08-stdin-intake-and-anchor-cleanup/
git commit -m "feat(tasks): self-apply the contract to stdin intake and anchor cleanup"
git push -u origin feat/stdin-intake-and-anchor-cleanup
gh pr create --base phase0 \
  --title "feat(tasks): accept bundles from stdin and align harvester anchors" \
  --body-file tasks/T-2026-08-08-stdin-intake-and-anchor-cleanup/RESULT.md
```

**マージは行わない。auto-merge も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 陽性対照が失敗しない | **その検証コマンドは無効。** 入力を作り直し、両方を記録する |
| 標準入力が既に対応済みだった | その事実を実測で記録し、テストのみ追加する |
| 収穫器の出力が変わった | **G2 停止。** 差分の内容を記録し判断を仰ぐ。**自分で「軽微だから続行」と判断しない** |
| `re.search` の用途が読み取れない | **変更しない。** `UNKNOWN` として記録 |
| 収穫器のパターンを単体で試せない | 変更せず `UNKNOWN` と記録。推測で置換しない |
| 一台も到達できない | 前回と同じ結果として記録し続行。**伝播の欠落と書かない** |
| 軽量ビューに差分が出た | 収穫器の出力が変わった疑い。**停止して報告** |
| 全体テストの失敗が 5 件から増えた | 本 task が壊した。停止して報告 |

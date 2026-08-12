# 凍結源の正本ハッシュを固定し、判定規約の表記と L1-3 の対象を整合させる

**task_id:** `T-2026-08-06-frozen-source-and-sigma-notation`
**kind:** `impl`
**depends_on:** `T-2026-08-05-l2-task-id-uniqueness-fix`（PR #43・マージ済み）

---

## Goal

`kind: exp` の契約を起票できる状態にする。現在、exp を起票すると次の2箇所で確実に止まる。

| ブロッカー | 症状 |
|---|---|
| `conventions#frozen_source` の SHA-256 が `UNKNOWN` | exp テンプレの既定 `verify: ckpt_sha256` が照合先を持たない |
| 判定規約の標準表記が L1-3 に抵触 | `prereg.decision_rule` に絶対値記号を含む式を書けない |

これを潰したうえで、前 task からの申し送り2件と、テンプレートの設計不整合1件を併せて解消する。

## 起票時に確定している事実

2026-08-06 に MacBook から11ホストを ssh 一括監査した結果、凍結源 ckpt は次のとおり。

| 項目 | 値 |
|---|---|
| パス | `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth` |
| SHA-256 | `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824` |
| サイズ | `195421066` bytes |
| mtime | `2026-05-30 07:42:27.376519004 +0000` |
| 存在ホスト | 11 / 11 |
| distinct SHA-256 | 1 |

**mtime がナノ秒まで全ホストで一致**しており、`third_party/` は git 追跡対象外だが実体はホスト間で同期されている。起票者が当初「`third_party/` は同期対象外なので多くのホストで verify 不能」と述べたのは**誤り**であり、この監査で訂正された。この経緯も記録対象とする。

---

## 0. 前提と禁止事項

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git checkout -b feat/frozen-source-and-sigma-notation origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | `runindex/**` を手で編集する |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 3 | `tools/harvest_runindex.py` を変更する |
| 4 | 凍結源 ckpt そのものを移動・改変・再生成する |
| 5 | repo root のファイルを移動・削除する |
| 6 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 7 | テスト件数を合わせるためだけのテストを足す |
| 8 | efros の repo パス差を「修正」する（記録のみ。利用者の明示判断） |

**YAML と markdown 表の本文に半角パイプを書かない。** Task 4 完了後も `meta.title` などの厳格対象では FAIL する。

### 本 task で意図的に発生させる WARN

Task 3 で `context/conventions.md` を変更するため、本 task 自身の `contract.conventions_rev`
（`8b17c4d`）が古くなり、Task 8 の自己検証で **L2-6 が WARN する**。これは正常であり、
**L2-6 が実際に発火する初めての事例**でもある。前 task の RESULT で「L2-8 は未検証」と
申し送られたのと同様、L2-6 の動作確認としてこの WARN の出力をそのまま RESULT に記録すること。
WARN を消すために `conventions_rev` を書き換えてはならない。

---

## Task 1: 凍結源ハッシュの実測と照合（Phase A）

**Files:** なし（読み取りのみ）

- [ ] **Step 1: 実行ホストで実測する**

```bash
CKPT=third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth
ls -l "$CKPT"
stat -c '%s %y' "$CKPT"
sha256sum "$CKPT"
```

- [ ] **Step 2: 監査記録と照合する（G1 ゲート）**

| 項目 | 期待値 |
|---|---|
| SHA-256 | `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824` |
| サイズ | `195421066` |

**一致しなければ Task 2 以降へ進まず停止して報告する。** 一致しない場合、監査時点から
ckpt が差し替わったか、実行ホストが監査対象外である。いずれも `no_frozen_change` に関わる
重大事象であり、`escalate_if: frozen_source_hash_mismatch` に該当する。

- [ ] **Step 3: 実測値を控える**

RESULT §1 に、実行ホスト名・実測 SHA-256・サイズ・mtime を記録する。

---

## Task 2: 紛らわしい ckpt 候補の棚卸し（Phase A）

`runindex` には `wrong_frozen_source` で除外された run が 3 件ある。正本が11ホストで一致
している以上、**別の ckpt が存在した（する）**はずである。正本を固定する前に候補を洗う。

**Files:**
- Create: `tasks/T-2026-08-06-frozen-source-and-sigma-notation/pth_inventory.md`

- [ ] **Step 1: 大きな ckpt を列挙する**

```bash
find third_party checkpoints work_dirs experiments -name "*.pth" -size +100M 2>/dev/null \
  | while read -r f; do
      printf "%s\t%s\t%s\n" "$(sha256sum "$f" | cut -c1-16)" "$(stat -c%s "$f")" "$f"
    done | sort
```

- [ ] **Step 2: 除外された 3 run の凍結源を特定する**

```bash
source .venv/bin/activate
python - <<'PY'
import csv, json, pathlib
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = rows[0].keys()
reason_col = next((c for c in cols if "exclude" in c and "reason" in c), None)
print("除外理由の列:", reason_col)
if reason_col is None:
    print("UNKNOWN: 除外理由の列が特定できない")
else:
    hits = [r for r in rows if r.get(reason_col) == "wrong_frozen_source"]
    print(f"wrong_frozen_source: {len(hits)} 件")
    for r in hits:
        key = next((c for c in cols if c.endswith("ledger_key")), None)
        print(" -", r.get(key), "|", r.get("workdir") or r.get("path") or "")
PY
```

- [ ] **Step 3: 各 run の `config.yaml` から凍結源の記載を読む**

Step 2 で得たパスの `config.yaml` を開き、`frozen_source` に相当する記載を転記する。

- [ ] **Step 4: `pth_inventory.md` に記録する**

```markdown
# 凍結源候補の棚卸し（2026-08-06）

## 正本

| 項目 | 値 |
|---|---|
| パス | third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth |
| SHA-256 | （実測値） |
| 11ホスト監査 | 11 / 11 一致 |

## 実行ホスト上の 100MB 超 ckpt

| SHA-256 先頭16 | サイズ | パス | 正本と同一か |
|---|---|---|---|

## wrong_frozen_source で除外された run

| ledger_key | config.yaml の凍結源記載 | 正本と一致するか |
|---|---|---|

特定できなかった項目は UNKNOWN と明記する。推測で埋めない。
```

- [ ] **Step 5: commit**

```bash
git add tasks/T-2026-08-06-frozen-source-and-sigma-notation/pth_inventory.md
git commit -m "docs(tasks): inventory frozen-source checkpoint candidates"
```

**この Task で run を除外し直したり、`runindex` を再生成したりしない。** 棚卸しのみ。

---

## Task 3: conventions の更新（Phase A / B の境界）

**Files:**
- Modify: `context/conventions.md`

- [ ] **Step 1: `frozen_source` 節の `UNKNOWN` を置換する**

現在の記述はこうなっている。

> checkpoint の正本 SHA-256 は `UNKNOWN（転記元未特定）`。実行時に対象ファイルから計算し、契約の解決結果へ記録する。

これを次に置き換える。**実測 SHA-256 を Task 1 Step 1 の出力から転記すること。**

```markdown
checkpoint の正本 SHA-256 は次のとおり。

    03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824

サイズは 195421066 bytes。転記元は 2026-08-06 に実施した11ホストの ssh 一括監査であり、
11 ホスト全てで SHA-256 が一致し、mtime もナノ秒まで同一であった。
`third_party/` は git の追跡対象外だが、実体はホスト間で同期されている。

`verify: ckpt_sha256` は全ホストで実行可能である。照合に失敗した場合は
`no_frozen_change` の違反として扱い、実行を中止して人へ escalate する。
skip する経路は設けない。
```

- [ ] **Step 2: `sigma` 節に表記ルールを追記する**

`### 既定値` ブロックの**直後**に次を挿入する。

```markdown
### 判定規約の表記

判定規約を `spec.yaml` や `prereg.md` に書くときは、絶対値を `abs(...)` の関数形で書く。
縦線による絶対値記法は markdown 表のセル区切りと衝突し、表を壊すため使わない
（backlog B-33 と同型の事故）。

    正: abs(delta) / sigma >= 1 かつ 全 seed 同符号
    誤: 縦線で delta を囲む記法

同じ理由で、区切りを表したいときは `/` かスラッシュ区切りの語を使う。
```

- [ ] **Step 3: 変更履歴を追記する**

末尾の変更履歴表に行を足す。**`（このコミット）` というプレースホルダを実 sha に置き換える**
のは commit 後になるため、ここでは日付と変更内容のみ書き、Task 8 Step 2 で sha を追記する。

- [ ] **Step 4: プレースホルダと UNKNOWN の残存を確認する**

```bash
grep -n "UNKNOWN" context/conventions.md
```

Expected: `select_box_nums_for_evaluation` に関する 1 件のみ（これは転記元が存在しないため残す）

- [ ] **Step 5: アンカー数が変わっていないことを確認する**

```bash
grep -c '<a id=' context/conventions.md
```

Expected: `7`

- [ ] **Step 6: commit**

```bash
git add context/conventions.md
git commit -m "docs(context): fix canonical frozen-source hash and add sigma notation rule"
```

---

## Task 4: L1-3 の対象を限定する（Phase B）

**Files:**
- Modify: `tests/test_validate_task.py`
- Modify: `tools/validate_task.py`

現在 L1-3 は spec 内の**全文字列**を対象にしており、`prereg.decision_rule` に判定規約を
書けない。B-33 の実害は「markdown 表の列が壊れる」ことなので、**表へ流れるフィールドのみ
FAIL、それ以外は警告**に変える。

### 厳格対象（FAIL）

| パス | 表へ流れる先 |
|---|---|
| `meta.title` | RESULT / PR の見出しと表 |
| `intent.question` `intent.decision_at_stake` `intent.hypothesis` | RESULT §1 の表 |
| `plan.phases[].name` | RESULT §2 のゲート表 |
| `plan.gates[].check` | 同上 |
| `outputs.acceptance[]` | RESULT §4 の表 |

### 警告対象（WARN・exit code を変えない）

上記以外のすべて。`prereg.*` `governance.*` `contract.*` などが該当する。

- [ ] **Step 1: 失敗するテストを追加する**

既存の `test_pipe_in_string_fails` は `intent.question` を対象にしており、厳格対象なので
**そのまま残す**。次を追加する。

```python
def _hard(findings):
    return [f for f in findings if not f.check.endswith("W")]


def test_pipe_in_gate_check_fails():
    spec = _minimal_impl_spec()
    spec["plan"]["gates"] = [
        {"id": "G1", "after": "A", "check": "a と b のどちらか", "on_fail": "stop"}
    ]
    spec["plan"]["gates"][0]["check"] = "a " + chr(124) + " b のどちらか"
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert "L1-3" in {f.check for f in _hard(findings)}


def test_pipe_outside_table_fields_is_warning_only():
    spec = _minimal_impl_spec()
    spec["meta"]["kind"] = "exp"
    spec["inputs"]["denominator"] = {"ref": "exp:transfer/s4_base_tecno", "metric": "accuracy"}
    spec["outputs"]["expected_runs"] = 6
    spec["outputs"]["stamp"] = {"task_id_in": "config.yaml"}
    spec["prereg"] = {
        "prediction": "p",
        "primary_endpoint": "macro_f1",
        "decision_rule": "abs(delta) " + chr(124) + " sigma",
        "stop_conditions": ["s"],
        "committed_at": None,
        "commit": None,
    }
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert _hard(findings) == []
    assert "L1-3W" in {f.check for f in findings}


def test_abs_notation_decision_rule_passes():
    spec = _minimal_impl_spec()
    spec["meta"]["kind"] = "exp"
    spec["inputs"]["denominator"] = {"ref": "exp:transfer/s4_base_tecno", "metric": "accuracy"}
    spec["outputs"]["expected_runs"] = 6
    spec["outputs"]["stamp"] = {"task_id_in": "config.yaml"}
    spec["prereg"] = {
        "prediction": "非飽和域では正の差が出る",
        "primary_endpoint": "macro_f1",
        "decision_rule": "abs(delta) / sigma >= 1 かつ 全 seed 同符号",
        "stop_conditions": ["G1 不通過"],
        "committed_at": None,
        "commit": None,
    }
    findings = validate_l1(spec, dir_name="T-2026-08-03-example-task")
    assert findings == [], [str(f) for f in findings]
```

**注:** テスト本文に半角パイプの文字を直接書くと、このテストファイル自体が
将来 markdown へ引用されたときに同じ事故を起こす。`chr(124)` で組み立てている。

- [ ] **Step 2: 失敗を確認する**

```bash
.venv/bin/python -m pytest tests/test_validate_task.py -q
```

Expected: 新規3件のうち少なくとも `test_pipe_outside_table_fields_is_warning_only` と
`test_abs_notation_decision_rule_passes` が FAIL

- [ ] **Step 3: 実装する**

`tools/validate_task.py` の定数部に追加する。

```python
_PIPE_STRICT_PATHS = (
    re.compile(r"^meta\.title$"),
    re.compile(r"^intent\.(question|decision_at_stake|hypothesis)$"),
    re.compile(r"^plan\.phases\.\d+\.name$"),
    re.compile(r"^plan\.gates\.\d+\.check$"),
    re.compile(r"^outputs\.acceptance\.\d+$"),
)
_WARN_CHECKS = {"L1-3W"}


def _is_pipe_strict(path: str) -> bool:
    return any(pattern.match(path) for pattern in _PIPE_STRICT_PATHS)
```

`validate_l1` の L1-3 ブロックを次に置き換える。

```python
    for path, value in _walk_strings(spec):
        if chr(124) not in value:
            continue
        if _is_pipe_strict(path):
            findings.append(
                Finding("L1-3", path, "表へ流れるフィールドに区切り文字を含みます")
            )
        else:
            findings.append(
                Finding("L1-3W", path, "区切り文字を含みます。表へ引用する際は注意してください")
            )
```

`main()` の集計を、警告を失敗に数えないよう変える。

```python
        findings = validate_l1(spec, dir_name=task_dir.name)
        if args.level == "l2" and not [f for f in findings if f.check not in _WARN_CHECKS]:
            findings += validate_l2(spec)
        hard = [f for f in findings if f.check not in _WARN_CHECKS]
        warn = [f for f in findings if f.check in _WARN_CHECKS]
        for f in warn:
            print(f"WARN {task_dir.name}: {f}", file=sys.stderr)
        if hard:
            failed += 1
            print(f"FAIL {task_dir.name}")
            for f in hard:
                print(f"  {f}")
        else:
            print(f"OK   {task_dir.name}")
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
.venv/bin/python -m pytest tests/test_validate_task.py -q
```

Expected: 全件 pass。**件数を実測して控える。水増ししない。**

- [ ] **Step 5: G2 ゲート — 実物の契約で確認する**

```bash
mkdir -p /tmp/g2check && cp tasks/_templates/exp/spec.yaml /tmp/g2check/spec.yaml
.venv/bin/python - <<'PY'
import sys, yaml
sys.path.insert(0, "tools")
from validate_task import validate_l1
spec = yaml.safe_load(open("/tmp/g2check/spec.yaml", encoding="utf-8"))
spec["meta"]["task_id"] = "T-2026-08-06-g2check"
spec["prereg"]["decision_rule"] = "abs(delta) / sigma >= 1 かつ 全 seed 同符号"
findings = validate_l1(spec, dir_name="T-2026-08-06-g2check")
pipe = [f for f in findings if f.check.startswith("L1-3")]
print("L1-3 系 finding:", pipe)
assert not pipe, pipe
print("G2 OK")
PY
rm -rf /tmp/g2check
```

Expected: `G2 OK`

**通らなければ Task 5 以降へ進まず停止して報告する。**

- [ ] **Step 6: commit**

```bash
git add tools/validate_task.py tests/test_validate_task.py
git commit -m "feat(tasks): limit L1-3 to table-bound fields and warn elsewhere"
```

---

## Task 5: テンプレートの修正（Phase C）

**Files:**
- Modify: `tasks/_templates/analysis/spec.yaml`

`analysis` テンプレートは `sigma_policy: {series: pstd}` を明示している。これは
「省略して `conventions#sigma` から継承する」という設計決定に反しており、継承経路が
使われないまま既定値が固定される。

- [ ] **Step 1: `sigma_policy` の行を削除する**

```yaml
  denominator:
    ref: "exp:group/experiment_id"
    metric: ""
    require: {n_seeds: ">=3", sigma: present, split: val}
  data:
```

- [ ] **Step 2: 3種のテンプレートが厳格 L1-3 を通ることを確認する**

```bash
.venv/bin/python - <<'PY'
import sys, yaml
from pathlib import Path
sys.path.insert(0, "tools")
from validate_task import validate_l1
for kind in ["exp", "impl", "analysis"]:
    spec = yaml.safe_load(Path(f"tasks/_templates/{kind}/spec.yaml").read_text(encoding="utf-8"))
    findings = validate_l1(spec, dir_name=spec["meta"]["task_id"])
    hard = [f for f in findings if f.check in {"L1-3", "L1-4"}]
    print(kind, "hard:", hard)
    assert not hard, hard
print("templates OK")
PY
```

Expected: `templates OK`

- [ ] **Step 3: commit**

```bash
git add tasks/_templates/analysis/spec.yaml
git commit -m "fix(tasks): let analysis template inherit sigma policy instead of pinning it"
```

---

## Task 6: 未追跡 smoke ディレクトリの実測（Phase C）

前 task の申し送り。`experiments/transfer/_smoke_*` 3 件が未追跡のまま残っている。
未追跡ということは他ホストに存在せず、`make runindex` の結果がホスト間で割れる可能性がある。

**Files:**
- Modify: `tasks/T-2026-08-06-frozen-source-and-sigma-notation/pth_inventory.md`（末尾へ追記）

- [ ] **Step 1: 実体を確認する**

```bash
git status --porcelain experiments/transfer/ | head
ls -d experiments/transfer/_smoke_* 2>/dev/null
```

- [ ] **Step 2: runindex 上の扱いを実測する**

```bash
.venv/bin/python - <<'PY'
import csv
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
key_col = next((c for c in cols if c.endswith("ledger_key")), None)
reason_col = next((c for c in cols if "exclude" in c and "reason" in c), None)
hits = [r for r in rows if "_smoke" in str(r.get(key_col, ""))]
print("列:", key_col, reason_col)
print(f"index.csv 内の smoke 系: {len(hits)} 件")
for r in hits:
    print(" -", r.get(key_col), "->", r.get(reason_col))
PY
```

- [ ] **Step 3: 結論を記録する**

| 観測 | 意味 |
|---|---|
| 除外済み（`smoke_test` 等） | 無害。記録のみ |
| index に載っている | **ホスト間で runindex が割れる**。backlog 起票が必要 |
| index に無く除外にも無い | 収穫対象外。無害だが理由を記録 |

**この Task では削除も追加もしない。** 実測と記録のみ。backlog 起票が必要な場合は
RESULT §6 の申し送りに書き、別 task とする。

- [ ] **Step 4: commit**

```bash
git add tasks/T-2026-08-06-frozen-source-and-sigma-notation/pth_inventory.md
git commit -m "docs(tasks): record how untracked smoke dirs are handled by runindex"
```

---

## Task 7: ホスト環境の既知差を記録（Phase C）

**Files:**
- Modify: `tasks/README.md`

- [ ] **Step 1: 末尾に節を追加する**

```markdown
## ホスト環境の既知差

修正対象ではない。指示書を書くときに前提としないための記録。

| ホスト | 差分 | 影響 |
|---|---|---|
| efros | repo パスが他ホストの標準と異なる | ホスト横断スクリプトでパスを決め打ちすると失敗する。実行時に確認すること |

凍結源 ckpt は 2026-08-06 時点で 11 ホスト中 11 ホストに存在し、SHA-256 は全一致。
mtime もナノ秒まで同一である。`third_party/` は git の追跡対象外だが、実体は
ホスト間で同期されている。「git 追跡外イコール同期外」と仮定してはならない。
```

- [ ] **Step 2: commit**

```bash
git add tasks/README.md
git commit -m "docs(tasks): record known host environment differences"
```

---

## Task 8: 自己契約の配置と完了判定

**Files:**
- Create: `tasks/T-2026-08-06-frozen-source-and-sigma-notation/spec.yaml`（配布物を配置）
- Create: `tasks/T-2026-08-06-frozen-source-and-sigma-notation/SPEC.md`（このファイル）
- Create: `tasks/T-2026-08-06-frozen-source-and-sigma-notation/RESULT.md`

- [ ] **Step 1: `conventions_rev` を確認する**

配布された `spec.yaml` は `conventions_rev: "8b17c4d"` を持つ。これは **Task 3 で
conventions.md を変更する前の値**であり、意図的に古い。

```bash
git log -1 --format=%h -- context/conventions.md
```

**Task 3 のコミットが返るはずだが、`spec.yaml` は書き換えない。** L2-6 の WARN を
発火させることが目的である。ただし `8b17c4d` が現在のブランチに**存在しない**場合
（履歴の書き換えがあった場合）は、存在する直前の sha に置き換え、RESULT §5 に記録する。

- [ ] **Step 2: conventions.md の変更履歴に sha を追記する**

Task 3 Step 3 で日付のみ書いた行に、Task 3 のコミット sha を追記する。あわせて
既存行の `（このコミット）` プレースホルダも実 sha に置き換える。

```bash
git log --format='%h %ad %s' --date=short -- context/conventions.md
```

- [ ] **Step 3: 自己検証**

```bash
make task-validate TASK=T-2026-08-06-frozen-source-and-sigma-notation; echo "exit=$?"
```

Expected: `OK` / `exit=0`、かつ **stderr に L2-6 の WARN**（conventions.md が変更された旨）

**WARN の生出力をそのまま RESULT §2 に貼ること。** これは L2-6 の初の実発火であり、
前 task で「L2-8 は未検証」と申し送ったのと対になる動作確認である。

- [ ] **Step 4: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 凍結源の UNKNOWN が消えた | `grep -n "UNKNOWN" context/conventions.md` | `select_box_nums_for_evaluation` の 1 件のみ |
| 2 | アンカー数が不変 | `grep -c '<a id=' context/conventions.md` | 7 |
| 3 | sigma 節に表記ルールがある | `grep -n "abs(" context/conventions.md` | 1 件以上 |
| 4 | 全 task の検証が通る | `make task-validate` | exit 0 |
| 5 | validator テストが全 pass | `.venv/bin/python -m pytest tests/test_validate_task.py -q` | 全 pass・件数を実測記録 |
| 6 | 全体テストが不変 | `.venv/bin/python -m pytest tests/ -q` | 失敗 5 件のまま |
| 7 | テンプレート3種が通る | Task 5 Step 2 | `templates OK` |
| 8 | analysis が sigma を明示しない | `grep -n "sigma_policy" tasks/_templates/analysis/spec.yaml` | 出力なし |
| 9 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- runindex/ experiments/ transfer/ data/splits/ tools/harvest_runindex.py third_party/` | 出力なし |
| 10 | L2-6 が WARN した | Task 8 Step 3 | WARN の出力あり |

**判定6に注意**: 本 task の前から `tests/test_engines.py` 1 件と
`tests/test_research_logger.py` 4 件、計5件が失敗している。**5 のままなら PASS**、
増えていれば本 task が壊したので停止して報告する。

- [ ] **Step 5: `RESULT.md` を書く**

`tasks/_templates/impl/RESULT.md` を土台に全セクションを埋める。次を必ず含める。

- Task 1 の実測（実行ホスト・SHA-256・サイズ・mtime）と、監査記録との一致
- Task 2 の棚卸し結果。`wrong_frozen_source` 3 件の凍結源が特定できたか、`UNKNOWN` か
- Task 4 のテスト件数（**置換前から何件へ増えたか、実測で**）
- Task 6 の smoke 系の実測結果と、backlog 起票が必要かの判断
- Task 8 Step 3 の **L2-6 WARN の生出力**
- **`deviations` を空にしない。** 逸脱が無ければ「なし」と明記する
- §6 に、起票者が当初「`third_party/` は同期対象外なので verify 不能」と述べたのが
  11ホスト監査により誤りと判明した経緯

- [ ] **Step 6: push と PR**

```bash
git add tasks/T-2026-08-06-frozen-source-and-sigma-notation/
git commit -m "feat(tasks): self-apply the contract to the frozen-source and sigma notation fix"
git push -u origin feat/frozen-source-and-sigma-notation
gh pr create --base phase0 \
  --title "feat(context): pin canonical frozen-source hash and align sigma notation with L1-3" \
  --body-file tasks/T-2026-08-06-frozen-source-and-sigma-notation/RESULT.md
```

**マージは行わない。** Web UI で人が判断する。auto-merge も有効化しない。

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| Task 1 で SHA-256 が監査記録と不一致 | **G1 停止。** `frozen_source_hash_mismatch` として報告。以降へ進まない |
| 正本と異なる大きな `.pth` が見つかった | 削除も移動もせず `pth_inventory.md` に記録。`unexpected_pth_candidate` として報告 |
| `wrong_frozen_source` の除外理由の列が特定できない | `UNKNOWN` と記録し Task 2 を部分完了とする。推測で列を代用しない |
| Task 4 Step 5 の G2 が通らない | **停止して報告。** 厳格対象の定義に漏れがある可能性 |
| 全体テストの失敗が 5 件から増えた | 本 task が壊した。停止して報告 |
| `8b17c4d` がブランチに存在しない | 直前の存在する sha に置換し RESULT §5 へ記録 |
| L2-6 が WARN しない | conventions.md が実際には変更されていない可能性。Task 3 を再確認して報告 |

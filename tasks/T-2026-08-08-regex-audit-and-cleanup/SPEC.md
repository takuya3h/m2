# 終端一致の脆弱性を水平展開で潰し、作業領域と記録の食い違いを解消する

**task_id:** `T-2026-08-08-regex-audit-and-cleanup`
**kind:** `impl`
**depends_on:** `T-2026-08-07-propagation-and-distribution`（PR #47・マージ済み）

---

## Goal

前 task の敵対的レビューで、`fetch_task.py` の `_TASK_ID_RE` に検証バイパスが見つかった。
Python の `$` は文字列末尾の改行にも一致するため、改行を含む識別子が正規表現を通り、
`make` のレシピを分断して別の契約を検証させ、終了コード 0 を返させる経路があった。

**この欠陥は `fetch_task.py` に固有ではない可能性が高い。** 起票者は同じ書き方を
`validate_task.py` の JSON Schema と Python 側の双方で使っている。もし同型の脆弱性が
検証系に残っていれば、**これまでの全 task の検証結果が信頼できない**ことになる。

本 task は水平展開の棚卸しと修正を主目的とし、あわせて前 task の申し送りのうち
GPU を要さないものを片付ける。

## 副次的な目的

| # | 対象 | 背景 |
|---|---|---|
| 1 | 動作確認用ディレクトリ3件が未追跡のまま残存 | keeper の pull と自動マージを阻害している |
| 2 | 整形のみの未コミット差分1件 | 同上。内容は行末空白の削除のみ |
| 3 | 伝播経路の記述が実体と違う | 実測により、経路は共有ドライブ的な同期ではなく版管理ホスト経由と判明 |
| 4 | 凍結源の取り違え候補の除外理由が未特定 | 実列名が判明済みで、再調査すれば特定できる |

---

## 0. 前提と禁止事項

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git checkout -b feat/regex-audit-and-cleanup origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | `runindex/**` `context/auto/**` を手で編集する |
| 2 | `experiments/**` `transfer/**` `data/splits/**` の**中身**を変更・削除する |
| 3 | `tools/harvest_runindex.py` を変更する |
| 4 | 学習・評価コードを変更する |
| 5 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 6 | テスト件数を合わせるためだけのテストを足す |
| 7 | GPU を使う |
| 8 | 動作確認用ディレクトリを**削除する**（無視設定の追加のみ行う） |

**YAML と markdown 表の本文に半角パイプを書かない。**

### 本 task の姿勢

前 task で敵対的レビューが実施され、自己検証だけでは見つからない欠陥が4件出た。
**本 task でも、修正後に「本当に塞がったか」を反証する視点で確認すること。**
特に Phase B では、修正した正規表現に対して**通ってはならない入力を実際に投げる**。

---

# Phase A — 棚卸しと再現

## Task 1: 終端一致の全数調査

**Files:**
- Create: `tasks/T-2026-08-08-regex-audit-and-cleanup/regex_audit.md`

- [ ] **Step 1: 検証系の正規表現を全数列挙する**

```bash
echo "===== Python 側 ====="
grep -rn "re\.compile\|re\.match\|re\.fullmatch\|re\.search" \
  tools/validate_task.py tools/preflight_task.py tools/build_context.py tools/fetch_task.py
echo
echo "===== 終端が \$ のもの ====="
grep -rn '\$"' tools/*.py | grep -v "\\\\Z"
echo
echo "===== JSON Schema 側 ====="
grep -n "pattern" tasks/_schema/spec.schema.json
```

- [ ] **Step 2: `match` と `fullmatch` の使い分けを確認する**

`re.match` は先頭一致のみで、末尾は検査しない。`$` と組み合わせても改行が通る。
**どの関数が使われているかまで含めて記録する。**

```bash
grep -rn "_RE\.\(match\|fullmatch\|search\)" tools/*.py
```

- [ ] **Step 3: 実際に改行入り入力を投げて挙動を測る**

**推測で「危ない」「安全」と書かない。実測する。**

```bash
python - <<'PY'
import json, re, sys
sys.path.insert(0, "tools")

# 検証系で使われている書き方の代表例を、実際の定数から取り出して試す
patterns = {
    "task_id_dollar_fullmatch": (r"T-\d{4}-\d{2}-\d{2}-[a-z0-9-]{3,60}$", "fullmatch"),
    "task_id_dollar_match": (r"^T-\d{4}-\d{2}-\d{2}-[a-z0-9-]{3,60}$", "match"),
    "task_id_zed_fullmatch": (r"T-\d{4}-\d{2}-\d{2}-[a-z0-9-]{3,60}\Z", "fullmatch"),
}
evil = "T-2026-08-08-evil\nrm -rf /"
benign = "T-2026-08-08-benign"
for name, (pat, fn) in patterns.items():
    rx = re.compile(pat)
    f = getattr(rx, fn)
    print(f"{name:34} benign={bool(f(benign))} evil={bool(f(evil))}")

# JSON Schema 側
schema = json.load(open("tasks/_schema/spec.schema.json"))
pat = schema["properties"]["meta"]["properties"]["task_id"]["pattern"]
print(f"\nschema pattern: {pat}")
try:
    from jsonschema import Draft202012Validator
    v = Draft202012Validator({"type": "string", "pattern": pat})
    print("schema benign:", not list(v.iter_errors(benign)))
    print("schema evil  :", not list(v.iter_errors(evil)))
except ImportError:
    print("jsonschema 未導入のため未検証")
PY
```

**`evil=True` になったものが脆弱である。**

- [ ] **Step 4: 実際の検証系に改行入り識別子を通してみる**

```bash
python - <<'PY'
import sys
sys.path.insert(0, "tools")
from validate_task import validate_l1

spec = {
    "spec_version": 1,
    "meta": {
        "task_id": "T-2026-08-08-evil\nmalicious",
        "kind": "impl",
        "title": "t",
        "origin": "claude-app",
        "created_at": "2026-08-08T00:00:00Z",
        "created_from": {"runindex_commit": "12cc0e8",
                         "counts": {"index": 749, "experiments": 206, "verdicts": 1038}},
    },
    "intent": {"question": "q", "decision_at_stake": "d"},
    "inputs": {"data": {"dataset": "d", "split_files": ["data/splits/ego_val.txt"]},
               "code": {"entrypoints": ["tools/validate_task.py"]}},
    "contract": {"inject_verbatim": ["conventions#split"], "conventions_rev": "1201f4f",
                 "prohibitions": ["no_raw_write"], "verbatim_forbidden": True},
    "plan": {"phases": [{"id": "A", "name": "n", "gpu": False}],
             "env": {"venv": ".venv", "preflight": ["venv_active"]}},
    "outputs": {"must_have": ["RESULT.md"], "destination": "tools/", "acceptance": ["a"]},
    "governance": {"deviations_required": True, "integrity": ["no_fabrication"]},
}
findings = validate_l1(spec, dir_name="T-2026-08-08-evil\nmalicious")
hard = [f for f in findings if not f.check.endswith("W")]
print("hard findings:", [str(f) for f in hard] or "なし（=素通り）")
PY
```

**`なし（=素通り）` と出たら、`validate_task.py` にも同型の脆弱性がある。**

- [ ] **Step 5: G1 ゲート — 棚卸し結果を判定する**

| 観測 | 判定 |
|---|---|
| 悪用可能な箇所がゼロ | Phase B は文書化のみ。**それでも `\Z` への統一は行う**（将来の再発防止） |
| 悪用可能な箇所がある | **`additional_bypass_found`。** 件数と場所を記録し、Phase B で修正 |

**どちらであっても停止はしない。** 記録して Phase B へ進む。ただし棚卸しが完了しない
（実測できない箇所が残る）場合は停止して報告する。

- [ ] **Step 6: `regex_audit.md` に記録する**

```markdown
# 終端一致の棚卸し（2026-08-08）

## 検証系の正規表現一覧

| ファイル | 定数名 | パターン | 呼び出し | 終端 | 改行入力 | 判定 |
|---|---|---|---|---|---|---|

## JSON Schema 側

| 場所 | パターン | 改行入力 | 判定 |
|---|---|---|---|

## 実際の検証系への攻撃入力

（Task 1 Step 4 の結果。素通りしたかどうかを実測で）

## 結論

（悪用可能な箇所の件数と、その影響範囲）
```

- [ ] **Step 7: commit**

```bash
git add tasks/T-2026-08-08-regex-audit-and-cleanup/regex_audit.md
git commit -m "docs(tasks): audit end-of-string anchors across the validation stack"
```

---

# Phase B — 修正と回帰

## Task 2: 終端一致を統一する

**Files:**
- Modify: `tools/validate_task.py`
- Modify: `tasks/_schema/spec.schema.json`（必要な場合）
- Modify: `tests/test_validate_task.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
# tests/test_validate_task.py に追記
def test_newline_in_task_id_is_rejected():
    """終端一致に改行が紛れ込む経路を塞ぐ。

    Python の $ は文字列末尾の改行に一致するため、改行入り識別子が
    検証を素通りしうる。fetch_task.py で実際に見つかった欠陥の水平展開。
    """
    spec = _minimal_impl_spec()
    evil = "T-2026-08-03-example-task\nmalicious"
    spec["meta"]["task_id"] = evil
    findings = validate_l1(spec, dir_name=evil)
    hard = [f for f in findings if not f.check.endswith("W")]
    assert hard, "改行入り task_id が素通りしました"


def test_trailing_newline_only_is_rejected():
    """末尾の改行だけでも拒否する。"""
    spec = _minimal_impl_spec()
    evil = "T-2026-08-03-example-task\n"
    spec["meta"]["task_id"] = evil
    findings = validate_l1(spec, dir_name=evil)
    hard = [f for f in findings if not f.check.endswith("W")]
    assert hard, "末尾改行つき task_id が素通りしました"
```

- [ ] **Step 2: 失敗を確認する**

```bash
python -m pytest tests/test_validate_task.py -q
```

Phase A Step 4 で素通りが確認されていれば FAIL する。**素通りしていなければ最初から
pass するので、その事実を RESULT に記録する**（既に安全だった、という実測）。

- [ ] **Step 3: Python 側を修正する**

`tools/*.py` の正規表現のうち、終端が `$` のものを `\Z` へ置き換える。
あわせて `re.match` を使っている箇所は `re.fullmatch` へ寄せる。

**`\Z` は Python の正規表現で「文字列の絶対的な末尾」を意味し、改行に一致しない。**

- [ ] **Step 4: JSON Schema 側を確認する**

JSON Schema の `pattern` は ECMA-262 の意味論で解釈され、`$` の扱いが実装依存になりうる。
**Phase A Step 3 で `schema evil` が `True` だった場合のみ修正する。**

修正する場合、ECMA-262 には `\Z` が無いため、否定先読みで表現する。

```
^T-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{3,60}$
  ↓
^T-[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{3,60}(?![\s\S])
```

**ただし、Python 側で `fullmatch` + `\Z` を使っていれば二重防御になる。**
Schema 側を変えるかどうかは実測結果で判断し、判断理由を RESULT に書く。

- [ ] **Step 5: G2 ゲート — 塞がったことを実測する**

```bash
python -m pytest tests/test_validate_task.py -q
echo "--- 攻撃入力の再投入 ---"
python - <<'PY'
import sys
sys.path.insert(0, "tools")
from validate_task import validate_l1
# Phase A Step 4 と同じ spec を使い、今度は拒否されることを確認する
PY
```

Expected: 全テスト pass。攻撃入力が拒否される。

**塞がっていなければ停止して報告する。**

- [ ] **Step 6: 反証を試みる**

**修正が「本当に塞がったか」を疑う。** 少なくとも次の入力を試す。

| 入力 | 期待 |
|---|---|
| 末尾に改行1つ | 拒否 |
| 中間に改行 | 拒否 |
| 末尾にキャリッジリターン | 拒否 |
| 末尾に空白 | 拒否 |
| 正常な識別子 | 受理 |

**通ってしまうものがあれば、それも修正して記録する。**

- [ ] **Step 7: commit**

```bash
git add tools/ tasks/_schema/ tests/test_validate_task.py
git commit -m "fix(tasks): reject newline-bearing identifiers in the validation stack"
```

---

# Phase C — 作業領域の整理と記録の訂正

## Task 3: 未追跡ディレクトリを無視設定へ

**Files:**
- Modify: `.gitignore`

前 task の記録により、`experiments/transfer/_smoke_artifacts_ctrl` `_smoke_artifacts_inj`
`_smoke_fullval` の3件は **収穫器の要件を満たさず、索引にも除外記録にも現れない**ことが
実測で確認済みである。調査は不要。

- [ ] **Step 1: 実測記録を再確認する**

```bash
grep -n "_smoke" tasks/T-2026-08-06-frozen-source-and-sigma-notation/*.md
```

**記録が見つからない場合のみ再実測する。** 見つかれば引用して RESULT に載せる。

- [ ] **Step 2: 無視設定を追加する**

```bash
grep -n "_smoke" .gitignore || echo "未設定"
```

`.gitignore` に次を追加する。既存の記述と重複しないこと。

```
# 動作確認用の一時成果物（収穫対象外）
experiments/**/_smoke_*/
```

- [ ] **Step 3: 効果を確認する**

```bash
git status --porcelain experiments/
git check-ignore -v experiments/transfer/_smoke_fullval/ || echo "無視されていない"
```

Expected: `git status` に3件が現れない

**ディレクトリ自体は削除しない。** checkpoints を含むため、将来の検証に使える可能性がある。

- [ ] **Step 4: commit**

```bash
git add .gitignore
git commit -m "chore: ignore smoke-test artifacts that the harvester does not collect"
```

---

## Task 4: 整形のみの差分を破棄

- [ ] **Step 1: 差分を再確認する**

```bash
git diff tasks/T-2026-08-03-task-contract-bootstrap/SPEC.md
```

**行末の空白2つの削除のみであることを確認する。** 内容の変更が含まれていれば
**破棄せず停止して報告する。**

- [ ] **Step 2: 破棄する**

行末2空白は markdown の強制改行指定であり、削除すると見出し直下の4項目が1行に
繋がって表示される。**整形として改悪であり、ブートストラップの証跡でもある。**

```bash
git checkout -- tasks/T-2026-08-03-task-contract-bootstrap/SPEC.md
git status --porcelain tasks/
```

Expected: 出力なし

---

## Task 5: 伝播経路の記述を実体に合わせる

**Files:**
- Modify: `tasks/README.md`

前 task の実測により、伝播は共有ドライブ的な同期ではなく、各ホストの常駐スクリプトが
30 分ごとに版管理ホストから取得する経路であることが判明した。

- [ ] **Step 1: 実測記録を確認する**

```bash
grep -n "keeper" tasks/T-2026-08-07-propagation-and-distribution/*.md | head -20
```

- [ ] **Step 2: `tasks/README.md` に節を追加する**

```markdown
## 伝播の経路

各ホストの常駐スクリプトが一定間隔で版管理ホストから取得する。共有ファイル同期に
よる伝播ではない。

**したがって、統合されていない作業ブランチの内容は他ホストへ届かない。**
契約や規約を全ホストへ行き渡らせるには、統合が必要である。

実体・間隔・到達状況の実測は
[`tasks/T-2026-08-07-propagation-and-distribution/propagation_audit.md`](T-2026-08-07-propagation-and-distribution/propagation_audit.md)
を参照。当該監査では、監査を実施したホストから他ホストへ到達できず、
他ホストの状態は未確認のまま残っている。
```

**「全11台へ届いている」と書かないこと。** 実測されていない。

- [ ] **Step 3: commit**

```bash
git add tasks/README.md
git commit -m "docs(tasks): describe the actual propagation path and its unverified scope"
```

---

## Task 6: 凍結源の取り違え候補を特定する

**Files:**
- Modify: `tasks/T-2026-08-08-regex-audit-and-cleanup/regex_audit.md`（末尾へ追記）

前 task で、**正本と同一サイズだが異なるハッシュを持つ checkpoint が4件**見つかっている。
実際の列名も判明している。

- [ ] **Step 1: 実列名を確認する**

```bash
python - <<'PY'
import csv
with open("runindex/index.csv", newline="", encoding="utf-8") as fh:
    cols = next(csv.reader(fh))
print([c for c in cols if "exclu" in c.lower()])
PY
```

**判明している名前を使う前に、実測で確認する。** 前 task の記録と食い違えば停止して報告。

- [ ] **Step 2: 除外された run を特定する**

```bash
python - <<'PY'
import csv
rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
cols = list(rows[0].keys())
reason_col = "exclusion_reason" if "exclusion_reason" in cols else None
if reason_col is None:
    print("UNKNOWN: 想定した列が無い")
else:
    key = next((c for c in cols if c.endswith("ledger_key")), None)
    hits = [r for r in rows if r.get(reason_col) == "wrong_frozen_source"]
    print(f"件数: {len(hits)}")
    for r in hits:
        print(" -", r.get(key))
        for c in cols:
            if "path" in c or "dir" in c or "work" in c:
                print("   ", c, "=", r.get(c))
PY
```

- [ ] **Step 3: 各 run の設定から凍結源の記載を読む**

Step 2 で得たパスの `config.yaml` を開き、凍結源に相当する記載を転記する。
**推測で補完しない。** 記載が無ければ `UNKNOWN` と書く。

- [ ] **Step 4: 候補との対応を取る**

前 task の `pth_inventory.md` に記録された4候補と突き合わせる。

```bash
cat tasks/T-2026-08-06-frozen-source-and-sigma-notation/pth_inventory.md
```

- [ ] **Step 5: `regex_audit.md` の末尾へ追記する**

```markdown
## 凍結源の取り違えで除外された run

| ledger_key | config の凍結源記載 | 対応する候補 | 正本と一致するか |
|---|---|---|---|

特定できなかった項目は UNKNOWN と明記する。
```

- [ ] **Step 6: commit**

```bash
git add tasks/T-2026-08-08-regex-audit-and-cleanup/regex_audit.md
git commit -m "docs(tasks): identify runs excluded for using the wrong frozen source"
```

---

## Task 7: 自己契約の配置と完了判定

**Files:**
- Create: `tasks/T-2026-08-08-regex-audit-and-cleanup/RESULT.md`

`spec.yaml` と `SPEC.md` はバンドル取り込みにより既に配置されている。

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

配布された値と異なれば置換し、RESULT §1 に記録する。§5 には書かない。

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-08-regex-audit-and-cleanup; echo "exit=$?"
make task-preflight TASK=T-2026-08-08-regex-audit-and-cleanup; echo "exit=$?"
```

Expected: 両方 `exit=0`。preflight は `P2` `P3` `P4` `P5` が `SKIP`

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 棚卸しが記録された | `regex_audit.md` | 表が埋まっている |
| 2 | 改行入り識別子が拒否される | Task 2 Step 5 | 拒否 |
| 3 | 反証入力が全て拒否される | Task 2 Step 6 | 5 種の期待どおり |
| 4 | 動作確認用が無視される | `git status --porcelain experiments/` | 出力なし |
| 5 | 動作確認用が削除されていない | `ls -d experiments/transfer/_smoke_*` | 3 件存在 |
| 6 | 整形差分が解消 | `git status --porcelain tasks/` | 出力なし |
| 7 | 伝播経路が文書化 | `grep -n "伝播の経路" tasks/README.md` | 1 件 |
| 8 | 除外理由が特定または UNKNOWN と明記 | `regex_audit.md` | 表が埋まっている |
| 9 | 契約検証が通る | `make task-validate` | exit 0 |
| 10 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 11 | テストが全 pass | `python -m pytest tests/test_validate_task.py -q` | 全 pass・件数を実測記録 |
| 12 | 全体テストが不変 | `python -m pytest tests/ -q` | 失敗 5 件のまま |
| 13 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- runindex/ context/auto/ experiments/ transfer/ data/splits/ tools/harvest_runindex.py` | 出力なし |

**判定12に注意**: 本 task の前から 5 件が失敗している。**5 のままなら PASS**、増えたら停止。

**判定4と5は両立する。** 無視設定は追加するが削除はしない。

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Phase A Step 3・Step 4 の**生の出力**（どれが素通りしたか）
- 悪用可能だった箇所の件数と場所
- JSON Schema 側を修正したか、その判断理由
- Task 2 Step 6 の反証入力5種の結果
- 除外された run の特定結果、または `UNKNOWN` とその理由
- テスト件数（実測。**前回 31 から何件になったか**）
- **`deviations` を空にしない**
- §6 に、他ホストからの伝播監査が未達であることを引き続き申し送る

- [ ] **Step 5: push と PR**

```bash
git add tasks/T-2026-08-08-regex-audit-and-cleanup/
git commit -m "feat(tasks): self-apply the contract to the regex audit"
git push -u origin feat/regex-audit-and-cleanup
gh pr create --base phase0 \
  --title "fix(tasks): reject newline-bearing identifiers and clean the working tree" \
  --body-file tasks/T-2026-08-08-regex-audit-and-cleanup/RESULT.md
```

**マージは行わない。auto-merge も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 検証系に悪用可能な箇所が複数見つかった | 全て記録し、全て修正する。**件数を隠さない** |
| 最初から安全だった | その事実を実測で記録する。**それでも `\Z` への統一は行う**（将来の再発防止） |
| JSON Schema の挙動が実装依存で判定できない | Python 側の二重防御に依存する旨を記録し、Schema は変えない |
| 整形差分に内容変更が含まれていた | **破棄せず停止して報告** |
| 除外理由の列が想定と違う | `UNKNOWN` と記録。**推測で代替列を使わない** |
| 動作確認用が索引に現れた | 前 task の記録と矛盾する。停止して報告 |
| 全体テストの失敗が 5 件から増えた | 本 task が壊した。停止して報告 |

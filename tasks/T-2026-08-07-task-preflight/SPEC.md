# 実行直前の検査を機械化し、複数の実装系で同一の結果になるようにする

**task_id:** `T-2026-08-07-task-preflight`
**kind:** `impl`
**depends_on:** `T-2026-08-06-make-context`（PR #45・マージ済み）

---

## Goal

L3（実行直前の検査）は現在 `.claude/skills/task/SKILL.md` の散文であり、agent が読んで守る
構造になっている。この構造には実証済みの欠陥がある。

| 実績 | 内容 |
|---|---|
| `venv_active` の付け忘れ | `source .venv/bin/activate` を忘れて実行し、その場で気づいて修正した。**気づかなければ検出手段が無かった** |
| `decisions_required` の素通り | 空リストであることは目に入っていたが、確認する独立ステップは踏まれなかった |

さらに第二の実装系（Codex CLI）を併用する方針が決まった。Codex は SKILL.md 標準に対応する一方、
フックは Bash ツールのイベントしか捕捉しない。**フックによるガードレールは実装系をまたげない。**

したがって L3 を `make task-preflight` として決定論的な検査へ移し、手順書は
「検査器を呼び、終了コードが非ゼロなら停止する」へ縮約する。これにより
**どの実装系で実行しても同じ検査が同じ結果になる。**

## 設計原則

| # | 原則 | 帰結 |
|---|---|---|
| 1 | **未実施と合格を区別する** | 契約に列挙されていない検査は `SKIP` と明示。「実行しなかった」を「通った」と混同させない |
| 2 | **検査器自身が環境を固定しない** | venv の検査器を `.venv/bin/python` で起動すると、activate していなくても通ってしまう |
| 3 | **出力は機械可読** | 実装系をまたいだ比較を diff で行えるようにする |
| 4 | **判断を agent から奪う** | 手順書に「確認する」と書かず「コマンドを叩き、非ゼロなら停止」と書く |
| 5 | **推測しない** | 環境変数名・拡張の import パスは実測してから実装する |

---

## 0. 前提と禁止事項

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git checkout -b feat/task-preflight origin/phase0
```

| # | 禁止 |
|---|---|
| 1 | `runindex/**` `context/auto/**` を手で編集する |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 3 | `tools/harvest_runindex.py` `tools/build_context.py` を変更する |
| 4 | `context/conventions.md` を変更する（本 task の範囲外） |
| 5 | 学習・評価コードを変更する |
| 6 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 7 | テスト件数を合わせるためだけのテストを足す |
| 8 | GPU を使う（本 task は GPU 不要） |

**YAML と markdown 表の本文に半角パイプを書かない。** 厳格対象では L1-3 が FAIL する。

---

## Task 1: 現状確認と実測（Phase A）

**Files:** なし（読み取りのみ）

- [ ] **Step 1: agent 設定の現状を確認する**

```bash
echo "=== .claude ==="
ls -la .claude/ .claude/commands/ .claude/skills/ 2>&1
echo "=== .codex ==="
ls -la .codex/ 2>&1 || echo "存在しない"
echo "=== git 追跡 ==="
git ls-files .claude/ .codex/ 2>&1
echo "=== Syncthing 除外 ==="
grep -n "claude\|codex" .stglobalignore 2>&1 || echo "除外指定なし"
echo "=== Codex の版 ==="
codex --version 2>&1 || echo "codex が PATH に無い"
```

**`.claude/` が git 追跡外なら、11台に伝播しない。** その場合は Task 5 で対応する。

- [ ] **Step 2: venv の検出方法を実測する（G1 の一部）**

```bash
echo "--- activate なし ---"
env -u VIRTUAL_ENV bash -c 'echo "VIRTUAL_ENV=[$VIRTUAL_ENV]"; which python; python -c "import sys; print(sys.prefix)"'
echo "--- activate あり ---"
bash -c 'source .venv/bin/activate; echo "VIRTUAL_ENV=[$VIRTUAL_ENV]"; which python; python -c "import sys; print(sys.prefix)"'
echo "--- 別 venv ---"
bash -c 'source .venv-relation-detr/bin/activate 2>/dev/null && echo "VIRTUAL_ENV=[$VIRTUAL_ENV]" || echo "存在しない"'
```

**`$VIRTUAL_ENV` と `sys.prefix` のどちらが信頼できるかを実測で決める。**
`$VIRTUAL_ENV` は activate 以外の方法で venv を使うと空になりうる。両方を見て、
**片方でも一致すれば PASS、両方外れれば FAIL** とするのが安全側である。

- [ ] **Step 3: CUDA 拡張の同定方法を実測する（G1 の一部）**

```bash
source .venv-relation-detr/bin/activate 2>/dev/null || source .venv/bin/activate
python - <<'PY'
import importlib, sys
for name in ["MultiScaleDeformableAttention", "torch"]:
    try:
        m = importlib.import_module(name)
        print(f"{name}: OK {getattr(m, '__file__', '')}")
    except Exception as e:
        print(f"{name}: NG {type(e).__name__} {e}")
PY
echo "--- 拡張の実体を探す ---"
find third_party .venv-relation-detr -name "*MultiScaleDeformableAttention*" 2>/dev/null | head
grep -rn "MultiScaleDeformableAttention\|MSDeformAttn" src/ scripts/ 2>/dev/null | head -5
```

**import 名が確認できなければ P2 を `UNKNOWN` として実装し、常に SKIP させる。**
推測した名前で import を書かないこと。

- [ ] **Step 4: 決定性フラグの現状を実測する**

```bash
grep -rn "deterministic\|CUBLAS_WORKSPACE_CONFIG\|use_deterministic_algorithms" \
  src/ scripts/ configs/ 2>/dev/null | head -20
echo "--- 環境変数 ---"
env | grep -i "cublas\|deterministic\|cudnn" || echo "未設定"
```

- [ ] **Step 5: 凍結源の同定方法を確認する**

`context/conventions.md` の `frozen_source` 節から、正本 SHA-256 とパスを**読み取る**
（変更しない）。パーサが節をどう切り出すかを決めるため、実際の書式を確認する。

```bash
sed -n '/<a id="frozen_source"><\/a>/,/<a id=/p' context/conventions.md
```

- [ ] **Step 6: 実測値をすべて控える**

RESULT §1 に記録する。以降の実装はこの実測に基づく。**推測で進めない。**

---

## Task 2: 検査器の実装（Phase B）

**Files:**
- Create: `tools/preflight_task.py`
- Create: `tests/test_preflight_task.py`

### 検査項目

| ID | 名前 | 対象 | 内容 |
|---|---|---|---|
| P1 | `venv_active` | 全 | `$VIRTUAL_ENV` または `sys.prefix` が `plan.env.venv` と一致 |
| P2 | `cuda_ext_loaded` | exp | 拡張を実 import して成功する |
| P3 | `deterministic_flags` | exp | 決定性の環境変数と設定が有効 |
| P4 | `prereg_committed` | exp | `prereg.commit` が存在し、その commit 時刻が現在より前 |
| P5 | `frozen_source_hash` | exp | ckpt の SHA-256 が conventions と一致 |
| P6 | `decisions_answered` | 全 | `governance.decisions_required` が空 |
| P7 | `destination_writable` | 全 | `outputs.destination` へ書き込める |
| P8 | `contract_valid` | 全 | L1 + L2 を再実行して合格 |

### 適用規則

- **P1 P6 P7 P8 は常に実行する。** 契約の記載に依らない
- **P2 P3 は `plan.env.preflight` に列挙されている場合のみ実行**。無ければ `SKIP`
- **P4 P5 は `meta.kind` が `exp` の場合のみ実行**。それ以外は `SKIP`
- 実測できない検査（Task 1 で `UNKNOWN` になったもの）は `SKIP` とし、理由を出力する

- [ ] **Step 1: 失敗するテストを書く**

```python
# tests/test_preflight_task.py
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from preflight_task import Check, decide_applicability, format_report, summarize  # noqa: E402


def _spec(kind="impl", preflight=None, decisions=None):
    return {
        "meta": {"kind": kind},
        "plan": {"env": {"venv": ".venv", "preflight": preflight or ["venv_active"]}},
        "governance": {"decisions_required": decisions or []},
        "outputs": {"destination": "tools/"},
    }


def test_impl_skips_exp_only_checks():
    applicable = decide_applicability(_spec(kind="impl"))
    assert applicable["P4"] is False
    assert applicable["P5"] is False
    assert applicable["P1"] is True
    assert applicable["P8"] is True


def test_exp_applies_prereg_and_frozen():
    applicable = decide_applicability(_spec(kind="exp"))
    assert applicable["P4"] is True
    assert applicable["P5"] is True


def test_cuda_check_requires_explicit_listing():
    without = decide_applicability(_spec(kind="exp", preflight=["venv_active"]))
    assert without["P2"] is False
    with_it = decide_applicability(
        _spec(kind="exp", preflight=["venv_active", "cuda_ext_loaded"])
    )
    assert with_it["P2"] is True


def test_skip_is_not_pass():
    checks = [
        Check("P1", "venv_active", "PASS", "VIRTUAL_ENV=.venv"),
        Check("P2", "cuda_ext_loaded", "SKIP", "契約に未記載"),
    ]
    counts = summarize(checks)
    assert counts["PASS"] == 1
    assert counts["SKIP"] == 1
    assert counts["FAIL"] == 0


def test_any_fail_makes_exit_nonzero():
    checks = [
        Check("P1", "venv_active", "PASS", ""),
        Check("P6", "decisions_answered", "FAIL", "未回答が 1 件"),
    ]
    assert summarize(checks)["FAIL"] == 1


def test_report_is_machine_readable():
    checks = [
        Check("P1", "venv_active", "PASS", "VIRTUAL_ENV=/x/.venv"),
        Check("P2", "cuda_ext_loaded", "SKIP", "契約に未記載"),
    ]
    text = format_report(checks)
    lines = [line for line in text.splitlines() if line.startswith("P")]
    assert len(lines) == 2
    for line in lines:
        parts = line.split(None, 3)
        assert parts[0].startswith("P")
        assert parts[2] in {"PASS", "SKIP", "FAIL"}
    assert "RESULT:" in text


def test_report_is_stable_across_runs():
    checks = [Check("P1", "venv_active", "PASS", "VIRTUAL_ENV=/x/.venv")]
    assert format_report(checks) == format_report(checks)
```

- [ ] **Step 2: 失敗を確認する**

```bash
source .venv/bin/activate
python -m pytest tests/test_preflight_task.py -q
```

Expected: FAIL（`No module named 'preflight_task'`）

- [ ] **Step 3: 実装する**

`tools/preflight_task.py` を作る。骨子は次のとおり。

```python
#!/usr/bin/env python3
"""TASK 契約の実行直前検査。

L1 と L2 は tools/validate_task.py が担う。ここは実行環境に依存する検査のみを行う。
出力は実装系をまたいで比較できるよう、固定書式とする。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = REPO_ROOT / "tasks"
STATUSES = ("PASS", "SKIP", "FAIL")

CHECK_NAMES = {
    "P1": "venv_active",
    "P2": "cuda_ext_loaded",
    "P3": "deterministic_flags",
    "P4": "prereg_committed",
    "P5": "frozen_source_hash",
    "P6": "decisions_answered",
    "P7": "destination_writable",
    "P8": "contract_valid",
}
ALWAYS = {"P1", "P6", "P7", "P8"}
EXP_ONLY = {"P4", "P5"}
LISTED_ONLY = {"P2": "cuda_ext_loaded", "P3": "deterministic_flags"}


@dataclass(frozen=True)
class Check:
    check_id: str
    name: str
    status: str
    detail: str


def decide_applicability(spec: dict) -> dict[str, bool]:
    """各検査を実行するかどうかを契約から決める。環境には触らない純関数。"""
    kind = spec.get("meta", {}).get("kind", "")
    listed = set(spec.get("plan", {}).get("env", {}).get("preflight", []) or [])
    applicable: dict[str, bool] = {}
    for cid in CHECK_NAMES:
        if cid in ALWAYS:
            applicable[cid] = True
        elif cid in EXP_ONLY:
            applicable[cid] = kind == "exp"
        else:
            applicable[cid] = LISTED_ONLY[cid] in listed
    return applicable


def summarize(checks: list[Check]) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for check in checks:
        counts[check.status] += 1
    return counts


def format_report(checks: list[Check]) -> str:
    lines = [
        f"{c.check_id} {c.name:<22} {c.status:<4} {c.detail}".rstrip()
        for c in checks
    ]
    counts = summarize(checks)
    lines.append("")
    lines.append(
        f"RESULT: {counts['PASS']} PASS / {counts['SKIP']} SKIP / {counts['FAIL']} FAIL"
    )
    return "\n".join(lines)
```

**各検査の実装で守ること。**

| 検査 | 実装上の注意 |
|---|---|
| P1 | `os.environ.get("VIRTUAL_ENV")` と `sys.prefix` の**両方**を見る。片方でも `plan.env.venv` の絶対パスと一致すれば PASS |
| P2 | Task 1 Step 3 で確認した**実際の import 名**を使う。確認できていなければ常に `SKIP` とし detail に理由を書く |
| P3 | 環境変数と設定を実測する。判定基準が実測で定まらなければ `SKIP` |
| P4 | `git show -s --format=%cI <commit>` で時刻を取り、現在時刻と比較。commit が存在しなければ FAIL |
| P5 | `hashlib.sha256` でファイルを読み、`conventions.md` の `frozen_source` 節から抽出した値と比較。**節の切り出しは `<a id="frozen_source"></a>` から次の `<a id=` まで** |
| P6 | `governance.decisions_required` が空なら PASS。非空なら FAIL とし、**項目をそのまま detail に出す** |
| P7 | `destination` に一時ファイルを作って削除。**削除の確認まで行う** |
| P8 | `tools/validate_task.py` を `subprocess` で呼び、終了コードを見る。**実装を複製しない** |

- [ ] **Step 4: 終了コードを実装する**

`FAIL` が 1 件でもあれば `1`。それ以外は `0`。**`SKIP` は終了コードを変えない。**

- [ ] **Step 5: テストが通ることを確認する**

```bash
python -m pytest tests/test_preflight_task.py -q
```

Expected: 全件 pass。**件数を実測して控える。**

- [ ] **Step 6: G2 ゲート — 未実施と合格が区別されることを実地で確認する**

```bash
echo "--- impl task（P2 P3 P4 P5 は SKIP になるはず）---"
python tools/preflight_task.py --task T-2026-08-06-make-context; echo "exit=$?"
```

Expected: `P2` `P3` `P4` `P5` が `SKIP`、それ以外が `PASS`、`exit=0`

```bash
echo "--- venv なしで実行（P1 が FAIL になるはず）---"
env -u VIRTUAL_ENV python tools/preflight_task.py --task T-2026-08-06-make-context; echo "exit=$?"
```

Expected: `P1` が `FAIL`、`exit=1`

**両方が期待どおりでなければ停止して報告する。**

- [ ] **Step 7: commit**

```bash
git add tools/preflight_task.py tests/test_preflight_task.py
git commit -m "feat(tasks): add machine-checked preflight for contract execution"
```

---

## Task 3: `make task-preflight`

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: ターゲットを追加する**

**挿入位置に注意。** 既存レシピの途中へ入れない。`.PHONY` 宣言の並びと既存ターゲットの
終端を確認してから足すこと。

```makefile
.PHONY: task-preflight
task-preflight:
	@python tools/preflight_task.py --task $(TASK)
```

**`.venv/bin/python` を使わない。** 既存の `context` ターゲットは `.venv/bin/python` を
直叩きしているが、preflight は「venv が有効か」を検査するものであり、Makefile 側で
venv を固定すると activate していなくても通ってしまう。**PATH 上の `python` を使い、
現在の環境をそのまま検査対象にする。**

- [ ] **Step 2: 動作確認**

```bash
source .venv/bin/activate
make task-preflight TASK=T-2026-08-06-make-context; echo "exit=$?"
echo "--- venv なし ---"
env -u VIRTUAL_ENV make task-preflight TASK=T-2026-08-06-make-context; echo "exit=$?"
```

**`make` はレシピ失敗時に自身の終了コード 2 を返す。** 前 task で `make context-check` に
ついて同じ観測がある。**スクリプト単体の終了コードと `make` 経由の終了コードを両方記録する。**

- [ ] **Step 3: commit**

```bash
git add Makefile
git commit -m "feat(tasks): add make task-preflight target"
```

---

## Task 4: 手順書の縮約（Phase C）

**Files:**
- Modify: `.claude/skills/task/SKILL.md`
- Modify: `tasks/README.md`

- [ ] **Step 1: `SKILL.md` の §4 を置き換える**

現在の §4 は検査項目の表を並べ、agent に読んで守らせる構造になっている。これを次に置き換える。

```markdown
### 4. L3 プリフライト（実行直前）

    make task-preflight TASK=<task_id>

**終了コードが 0 でなければ、ここで停止して報告する。** 出力をそのまま提示すること。
検査項目を自分で判断してはならない。何を検査するかは契約と検査器が決める。

`SKIP` は「合格」ではなく「実行されなかった」を意味する。SKIP された項目があれば、
その一覧を報告に含める。

`P6 decisions_answered` が FAIL なら、出力に列挙された項目をユーザーへ提示して停止する。
**自分で決めてはならない。**
```

- [ ] **Step 2: 冒頭に実装系非依存の記述を足す**

```markdown
## 実装系について

この手順は実装系に依存しない。Claude Code では `/task <task_id>`、
Codex では `$task` または本ファイルを読ませることで同じ手順を実行できる。

検査は `make task-validate` と `make task-preflight` が行う。
**判断を実装系に委ねる箇所は無い。** 手順書が求めるのはコマンドの実行と、
終了コードに従った停止だけである。
```

- [ ] **Step 3: `tasks/README.md` の L3 の記述を更新する**

検証表の L3 行を、散文ではなく機械検証であることが分かる記述に変える。

```markdown
| L3 | 実行直前（venv・拡張・prereg 時刻・凍結源・decisions・書き込み権限） | 実行環境 | 数秒 |
```

あわせて検証コマンドの節に `make task-preflight TASK=<task_id>` を追記し、
**`SKIP` と `PASS` の意味の違い**を明記する。

- [ ] **Step 4: 散文の判断が残っていないことを確認する**

```bash
grep -n "確認する\|判断する\|守ること\|注意する" .claude/skills/task/SKILL.md
```

出力された各行について、**コマンドの実行に置き換えられないかを検討する**。置き換えられない
ものだけを残し、その理由を RESULT に記録する。

- [ ] **Step 5: commit**

```bash
git add .claude/skills/task/SKILL.md tasks/README.md
git commit -m "docs(tasks): replace prose preflight with machine-checked command"
```

---

## Task 5: 第二の実装系からの利用（Phase C）

**Files:**
- Create: `.codex/skills/task`（symlink）
- Modify: `.gitignore` / `.stglobalignore`（必要な場合のみ）

- [ ] **Step 1: symlink を作る**

```bash
mkdir -p .codex/skills
ln -s ../../.claude/skills/task .codex/skills/task
ls -la .codex/skills/
cat .codex/skills/task/SKILL.md | head -5
```

**`AGENTS.md` が `CLAUDE.md` への symlink になっているのと同じ手法である。**
実体は `.claude/skills/task/SKILL.md` 一つだけとし、二重管理を作らない。

- [ ] **Step 2: git が symlink を追跡することを確認する**

```bash
git add .codex/
git status --porcelain .codex/
git cat-file -p :.codex/skills/task 2>/dev/null || echo "blob として未登録"
```

symlink は git 上ではリンク先パスを内容とする blob として記録される。**実体が複製されて
いないことを確認する。**

- [ ] **Step 3: Task 1 Step 1 の結果に応じて追跡設定を直す**

`.claude/` が git 追跡外だった場合、11台に伝播しない。`.gitignore` を確認し、
**追跡すべきものが除外されていれば解除する**。ただし認証情報が含まれうるファイル
（セッション記録・トークン）は除外したままにすること。判断がつかない場合は
除外を維持し、RESULT に申し送る。

- [ ] **Step 4: G3 ゲート — 二つの実装系で出力が一致することを確認する**

```bash
source .venv/bin/activate

# 第一の実装系（あるいは素のシェル）で実行し保存
make task-preflight TASK=T-2026-08-06-make-context > /tmp/pf_a.txt 2>&1; echo "exit_a=$?"

# Codex から実行させる
codex exec "make task-preflight TASK=T-2026-08-06-make-context を実行して、出力をそのまま貼ってください。要約しないでください。" 2>&1 | tee /tmp/pf_codex_raw.txt
```

Codex の出力から検査結果の行だけを抜き出して比較する。

```bash
grep -E "^P[0-9] |^RESULT:" /tmp/pf_codex_raw.txt > /tmp/pf_b.txt
diff /tmp/pf_a.txt /tmp/pf_b.txt && echo "AGENT PARITY OK" || echo "AGENT PARITY NG"
```

Expected: `AGENT PARITY OK`

**一致しなければ停止して報告する**（`agent_output_mismatch`）。差分の内容によって
対応が変わるため、推測で修正しない。

> 注意: Codex の応答には前後に説明文が付く。**比較対象は検査結果の行のみ**とする。
> 上の `grep` で抽出できない場合は、抽出条件を実測に合わせて調整し、RESULT に記録する。

- [ ] **Step 5: Codex から契約を実行できることを確認する**

```bash
codex exec "tasks/README.md と .codex/skills/task/SKILL.md を読み、T-2026-08-06-make-context の契約に対して手順 1 から 4 までを実行してください。手順 5 の実行フェーズには進まないでください。" 2>&1 | tail -40
```

Expected: `make task-validate` と `make task-preflight` が実行され、手順 5 の手前で停止する

**実行フェーズへ進んでしまった場合は、手順書の記述が不十分である。** その事実を
RESULT に記録し、`SKILL.md` の停止条件の書き方を修正する。

- [ ] **Step 6: commit**

```bash
git add .codex/ .gitignore
git commit -m "feat(codex): share the task procedure with a second agent via symlink"
```

---

## Task 6: 自己契約の配置と完了判定

**Files:**
- Create: `tasks/T-2026-08-07-task-preflight/{spec.yaml,SPEC.md,RESULT.md}`

- [ ] **Step 1: `conventions_rev` を実測値へ置換する**

配布された `spec.yaml` は `conventions_rev: "1201f4f"` を持つ。**起票者は現在の sha を
知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

置換した値を RESULT §1 に記録する。§5 の deviations には書かない。

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-07-task-preflight; echo "exit=$?"
make task-preflight TASK=T-2026-08-07-task-preflight; echo "exit=$?"
```

Expected: 両方 `exit=0`。preflight は `P2` `P3` `P4` `P5` が `SKIP`

**本 task 自身が新しい検査器を通ることが、最初の実運用になる。**

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 検査器が動く | `make task-preflight TASK=T-2026-08-06-make-context` | exit 0 |
| 2 | SKIP と PASS が区別される | 同上の出力 | P2 P3 P4 P5 が SKIP |
| 3 | FAIL で非ゼロ | `env -u VIRTUAL_ENV` で実行 | exit 非ゼロ |
| 4 | テストが全 pass | `python -m pytest tests/test_preflight_task.py -q` | 全 pass・件数を実測記録 |
| 5 | 契約検証が通る | `make task-validate` | exit 0 |
| 6 | 全体テストが不変 | `python -m pytest tests/ -q` | 失敗 5 件のまま |
| 7 | symlink が実体を複製していない | `ls -la .codex/skills/` | `task -> ../../.claude/skills/task` |
| 8 | 二実装系で出力一致 | Task 5 Step 4 | `AGENT PARITY OK` |
| 9 | Codex が手順を実行できる | Task 5 Step 5 | 手順 4 まで実行・5 の手前で停止 |
| 10 | 手順書に散文の判断が残っていない | Task 4 Step 4 | 残存分の理由が記録されている |
| 11 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- runindex/ context/auto/ context/conventions.md experiments/ transfer/ data/splits/ tools/harvest_runindex.py tools/build_context.py` | 出力なし |

**判定6に注意**: 本 task の前から 5 件が失敗している。**5 のままなら PASS**、増えたら停止して報告。

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Task 1 の実測（`$VIRTUAL_ENV` と `sys.prefix` の挙動、CUDA 拡張の import 名、
  決定性フラグの現状、`.claude/` の git 追跡状況、Codex の版）
- `UNKNOWN` として常時 SKIP にした検査があれば、その一覧と理由
- スクリプト単体と `make` 経由の終了コードの差
- Task 5 Step 4 の diff 結果（一致しなかった場合は差分の全文）
- Task 5 Step 5 で Codex が手順 5 へ進んでしまったか
- テスト件数（実測）
- **`deviations` を空にしない**
- §6 に「`.claude/` `.codex/` が 11 台へ伝播するかは未検証」を申し送る（次 task の対象）

- [ ] **Step 5: push と PR**

```bash
git add tasks/T-2026-08-07-task-preflight/
git commit -m "feat(tasks): self-apply the contract to the preflight task"
git push -u origin feat/task-preflight
gh pr create --base phase0 \
  --title "feat(tasks): machine-checked preflight and second-agent parity" \
  --body-file tasks/T-2026-08-07-task-preflight/RESULT.md
```

**マージは行わない。auto-merge も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| CUDA 拡張の import 名が特定できない | P2 を常時 SKIP として実装し、理由を detail と RESULT に書く。**推測した名前で import を書かない** |
| 決定性フラグの判定基準が実測で定まらない | P3 を常時 SKIP。同上 |
| `$VIRTUAL_ENV` と `sys.prefix` が食い違う | **両方を見て片方でも一致すれば PASS**。挙動を RESULT に記録（`venv_detection_unreliable`） |
| `codex` が PATH に無い | **G3 停止。** 実行ホストを変えるか、Codex 確認を別 task へ切り出す判断をユーザーへ戻す |
| 二実装系の出力が一致しない | **G3 停止。** 差分の全文を報告。推測で片方に合わせない |
| Codex が手順 5 へ進んでしまった | 停止条件の記述が弱い。`SKILL.md` を修正し、再度 Step 5 を実行。両方の結果を記録 |
| `.claude/` が git 追跡外だった | 追跡設定を直す。認証情報が含まれうるものは除外を維持し、RESULT へ申し送る |
| 全体テストの失敗が 5 件から増えた | 本 task が壊した。停止して報告 |

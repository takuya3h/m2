# 対話の記録を不揮発化し、実装系をまたいで後から検索できるようにする

**task_id:** `T-2026-08-08-session-durability`
**kind:** `impl`
**depends_on:** `T-2026-08-08-stdin-intake-and-anchor-cleanup`（PR #49・マージ済み）

---

## Goal

契約の往路と復路は閉じたが、**対話そのものは今も揮発している。**

| 面 | 検索手段 | 状態 |
|---|---|---|
| 起票側の対話面 | 面の機能として過去の会話を検索できる | ある |
| **実装系の対話** | **無い** | **毎セッション消える** |

実装レベルの議論、逸脱の判断、試して駄目だった経路は、すべて実装系のセッション内に
閉じている。契約の `RESULT.md` に残るのは結論だけで、**そこへ至る過程は残らない。**

本 task は、対話の記録から**機械的に抽出できる要素だけ**を取り出して版管理へ残し、
後から検索できるようにする。

## 設計原則

| # | 原則 | 帰結 |
|---|---|---|
| 1 | **生の記録を版管理へ入れない** | 秘匿情報が混入しうる。記録は各ホストの既定の場所に留める |
| 2 | **抽出は決定論的に行う** | 言語モデルによる要約は捏造を生む。抽出のみを版管理へ入れる |
| 3 | **判断は人が起票する** | 抽出物は素材であり、判断ではない。受け皿へ人が1行書く |
| 4 | **実装系に依存しない受け皿** | 様式を先に決め、収集はそれぞれで実装する |
| 5 | **伏せ字を既定にする** | 秘匿らしき文字列は既定で伏せる。通す方を例外にする |

---

## 0. 前提と禁止事項

```bash
cd "$(git rev-parse --show-toplevel)"
git fetch origin
git checkout -b feat/session-durability origin/phase0
source .venv/bin/activate
```

| # | 禁止 |
|---|---|
| 1 | `runindex/**` `context/auto/**` を手で編集する |
| 2 | `experiments/**` `transfer/**` `data/splits/**` を変更する |
| 3 | `tools/harvest_runindex.py` `tools/build_context.py` を変更する |
| 4 | `context/conventions.md` を変更する（本 task の範囲外） |
| 5 | **生の対話記録を版管理へ追加する** |
| 6 | 抽出物に自由記述の要約を含める |
| 7 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | テスト件数を合わせるためだけのテストを足す |
| 9 | GPU を使う |

### 起票者からの申し送り

過去 2 task で、起票者の検証コマンドが検証対象を検証できていない誤りが連続した。
**本 SPEC でも同型の誤りを想定すること。** 特に Phase A の伏せ字検査では、
**秘匿情報を含む入力と含まない入力の両方**を投げ、前者だけが伏せられることを確認する。
片方しか試さない検査は無効である。

### 実行環境について

実行ホストは 11 サーバのうちの 1 台であり、コンテナ内から他ホストへは到達できない。
本 task は**自ホストのみで完結する**。他ホストでの動作確認は申し送りとする。

---

# Phase A — 受け皿と抽出器

## Task 1: 受け皿の様式を決める

**Files:**
- Create: `tasks/inbox.md`
- Modify: `tasks/README.md`

抽出物は素材であり、判断ではない。**判断は人が 1 行書く。** その受け皿を先に作る。

- [ ] **Step 1: `tasks/inbox.md` を作る**

```markdown
# inbox — 判断の受け皿

対話で出た判断・気づき・申し送りを 1 行で置く場所。週次で空にする。
空にするとは、意思決定として昇格させるか、破棄することを意味する。

**1 セッション = 最低 1 行。** 逸脱や気づきが無い場合も「なし」と書いた行を残す。
書くべきものが無いことと、書き忘れたことを区別するためである。

## 様式

    - [ ] YYYY-MM-DD [面] 内容（参照）

面は次のいずれか。

| 面 | 意味 |
|---|---|
| `app` | 起票側の対話面 |
| `cc` | 第一の実装系 |
| `cx` | 第二の実装系 |
| `human` | 人が直接書いた |

参照には、抽出物のパスか契約の識別子を書く。

## 未処理

- [ ] 2026-08-08 [human] inbox を開設した（本 task）

## 処理済み

（週次で移す。破棄した場合も理由とともにここへ残す）
```

- [ ] **Step 2: `tasks/README.md` に節を追加する**

```markdown
## 対話の記録

実装系の対話は既定ではセッションごとに失われる。機械的に抽出できる要素のみを
`docs/sessions/` へ残し、後から検索できるようにしている。

    rg <検索語> docs/sessions/

**生の対話記録は版管理へ入れない。** 秘匿情報が混入しうるためである。
生の記録は各実装系の既定の保存先に残るので、必要ならそこを直接参照する。

判断は抽出物からは生まれない。対話で出た判断は `tasks/inbox.md` へ 1 行で置き、
週次で意思決定として昇格させるか破棄する。
```

- [ ] **Step 3: commit**

```bash
git add tasks/inbox.md tasks/README.md
git commit -m "feat(tasks): open the inbox for decisions surfaced in conversation"
```

---

## Task 2: 抽出器を実装する

**Files:**
- Create: `tools/session_digest.py`
- Create: `tests/test_session_digest.py`
- Modify: `.gitignore`

- [ ] **Step 1: 対話記録の形式を実測する**

**推測で構造を仮定しない。** 実際の記録を読み、行の形式を確認する。

```bash
ls -la ~/.claude/projects/ 2>/dev/null | head
PROJ=$(ls -1d ~/.claude/projects/*/ 2>/dev/null | head -1)
echo "PROJ=$PROJ"
ls -la "$PROJ" 2>/dev/null | tail -5
LATEST=$(ls -1t "$PROJ"*.jsonl 2>/dev/null | head -1)
echo "LATEST=$LATEST"
wc -l "$LATEST"
head -1 "$LATEST" | python3 -m json.tool | head -30
echo "--- 行の種類 ---"
python3 - "$LATEST" <<'PY'
import json, sys, collections
path = sys.argv[1]
kinds = collections.Counter()
keys = collections.Counter()
with open(path, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            kinds["<parse error>"] += 1
            continue
        kinds[obj.get("type", "<no type>")] += 1
        for k in obj:
            keys[k] += 1
print("type の分布:", dict(kinds))
print("出現するキー:", dict(keys.most_common(20)))
PY
```

**この出力を RESULT §1 へそのまま記録する。以降の実装はこの実測に基づく。**

- [ ] **Step 2: 抽出する要素を決める**

**機械的に取り出せるものだけ。** 自由記述の要約は含めない。

| 要素 | 出所 |
|---|---|
| セッション識別子 | 記録のファイル名または内容 |
| 開始と終了の時刻 | 記録内の時刻 |
| 実行されたコマンド | ツール呼び出しの入力 |
| 編集されたファイルのパス | 同上 |
| 発生したエラーの種類 | ツール出力のうち失敗を示すもの |
| 作られた識別子 | 契約の識別子など、様式が定まっているもの |

**含めないもの**: 会話本文、モデルの応答、要約、評価。

- [ ] **Step 3: 伏せ字の規則を決める**

既定で伏せる。通す方を例外にする。

| 対象 | 規則 |
|---|---|
| 環境変数の代入 | 値を伏せる |
| 秘密鍵らしき接頭辞を持つ文字列 | 全体を伏せる |
| 長い十六進文字列 | 先頭のみ残して伏せる |
| ファイルパス | 伏せない（`~` からの相対に正規化する） |

**判断に迷うものは伏せる。** 伏せすぎて困ることはあるが、漏れると取り返しがつかない。

- [ ] **Step 4: 失敗するテストを書く**

```python
# tests/test_session_digest.py
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from session_digest import extract, redact, render  # noqa: E402


def test_redacts_secret_assignments():
    text = "export SOME_API_KEY=abcd1234efgh5678"
    out = redact(text)
    assert "abcd1234efgh5678" not in out
    assert "SOME_API_KEY" in out


def test_redacts_token_like_strings():
    text = "使うのは sk-" + "x" * 40 + " です"
    out = redact(text)
    assert "x" * 40 not in out


def test_does_not_redact_ordinary_text():
    """伏せ字が過剰でないことを確認する。陽性対照の対。"""
    text = "make task-validate を実行し tools/validate_task.py を編集した"
    assert redact(text) == text


def test_does_not_redact_paths():
    text = "編集: tools/session_digest.py"
    assert "tools/session_digest.py" in redact(text)


def test_extract_collects_commands_and_files():
    lines = [
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "make task-validate"}}
        ]}}),
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Edit", "input": {"file_path": "tools/x.py"}}
        ]}}),
    ]
    result = extract(lines)
    assert "make task-validate" in result["commands"]
    assert "tools/x.py" in result["files"]


def test_extract_ignores_conversation_text():
    """会話本文を拾わないことを確認する。"""
    lines = [
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "これは会話本文であり抽出対象ではない"}
        ]}}),
    ]
    result = extract(lines)
    blob = json.dumps(result, ensure_ascii=False)
    assert "会話本文" not in blob


def test_render_has_no_free_text_summary():
    result = {"session_id": "abc", "commands": ["make x"], "files": ["a.py"],
              "errors": [], "started": "", "ended": ""}
    text = render(result)
    assert "make x" in text
    assert "要約" not in text


def test_malformed_lines_do_not_crash():
    lines = ["これは JSON ではない", "{壊れた", ""]
    result = extract(lines)
    assert result["commands"] == []
```

- [ ] **Step 5: 失敗を確認する**

```bash
python -m pytest tests/test_session_digest.py -q
```

Expected: FAIL（`session_digest` が未実装）

- [ ] **Step 6: 実装する**

`tools/session_digest.py` を作る。要件は次のとおり。

| # | 要件 |
|---|---|
| 1 | 記録のパスを引数に取り、抽出結果を標準出力か指定先へ書く |
| 2 | 解析できない行は**黙って飛ばす**（落ちない） |
| 3 | 抽出後に必ず伏せ字を適用する |
| 4 | 出力は `docs/sessions/digest/<日付>-<セッション識別子>.md` |
| 5 | 同じ入力からは同じ出力になる（**壁時計を使わない**） |
| 6 | 入力が空でも落ちず、空の抽出結果を出す |

**Step 1 の実測に基づいて実装する。** 構造が想定と違えば、実測に合わせる。
実測できない要素は抽出対象から外し、その旨を RESULT へ記録する。

- [ ] **Step 7: `.gitignore` を更新する**

生の記録が誤って版管理へ入らないようにする。

```
# 対話の生記録は版管理へ入れない
docs/sessions/raw/
*.jsonl
```

**`*.jsonl` の除外が既存のデータ形式と衝突しないかを確認する。**

```bash
git ls-files | grep "\.jsonl$" || echo "追跡中の jsonl は無い"
```

**追跡中のものがあれば `*.jsonl` は書かず、`docs/sessions/raw/` のみにする。**

- [ ] **Step 8: G1 ゲート — 伏せ字を両方向で確認する**

```bash
python -m pytest tests/test_session_digest.py -q

echo "===== 秘匿を含む入力 ====="
printf 'export TEST_TOKEN=abcdef0123456789abcdef\n' | \
  .venv/bin/python -c "import sys;sys.path.insert(0,'tools');from session_digest import redact;print(redact(sys.stdin.read()))"

echo "===== 秘匿を含まない入力 ====="
printf 'make task-validate && python tools/validate_task.py\n' | \
  .venv/bin/python -c "import sys;sys.path.insert(0,'tools');from session_digest import redact;print(redact(sys.stdin.read()))"
```

Expected: 前者は値が伏せられ、**後者は 1 文字も変わらない**

**後者が変わってしまう場合、伏せ字が過剰で使い物にならない。** 停止して報告する。

- [ ] **Step 9: 実物で試す**

```bash
LATEST=$(ls -1t ~/.claude/projects/*/*.jsonl 2>/dev/null | head -1)
.venv/bin/python tools/session_digest.py --transcript "$LATEST" --stdout | head -40
echo "===== 秘匿らしき文字列の混入検査 ====="
.venv/bin/python tools/session_digest.py --transcript "$LATEST" --stdout | \
  grep -nE "(sk-|ghp_|_KEY=|_TOKEN=|_SECRET=)[A-Za-z0-9_-]{8,}" && \
  echo "!!! 混入あり" || echo "混入なし"
```

**混入があれば停止して報告する**（`secret_leaked_into_digest`）。

- [ ] **Step 10: commit**

```bash
git add tools/session_digest.py tests/test_session_digest.py .gitignore
git commit -m "feat(sessions): extract machine-derived facts from transcripts with redaction"
```

---

# Phase B — 第一の実装系での自動化

## Task 3: セッション終了時に記録を残す

**Files:**
- Create: `.claude/hooks/session_end.sh`
- Modify: `.claude/settings.json`（存在しなければ作成）
- Create: `docs/sessions/README.md`

`SessionEnd` はセッション終了時に発火し、終了理由を伝える。ブロックはできず、
記録とクリーンアップのための事象である。標準入力に `session_id` `transcript_path`
`cwd` `hook_event_name` を含む JSON が渡される。

- [ ] **Step 1: 現在の設定を確認する**

```bash
ls -la .claude/
cat .claude/settings.json 2>/dev/null || echo "settings.json は無い"
cat ~/.claude/settings.json 2>/dev/null | head -30 || echo "ユーザ設定は無い"
```

**既存の設定を壊さない。** hook が既にあれば追記の形にする。

- [ ] **Step 2: 実行環境の差を確認する**

hook が呼ぶコマンドは、対話シェルと異なる `PATH` で動く可能性がある。

```bash
which python3 jq
echo "PATH=$PATH"
```

**`jq` に依存しない実装にする。** Python の標準ライブラリで標準入力の JSON を読む。

- [ ] **Step 3: hook を書く**

```bash
mkdir -p .claude/hooks docs/sessions/digest
cat > .claude/hooks/session_end.sh <<'SH'
#!/usr/bin/env bash
# セッション終了時に、対話記録から機械的な要素を抽出して残す。
# 標準入力に session_id と transcript_path を含む JSON が渡される。
# 記録に失敗してもセッションの終了を妨げない。
set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || exit 0

"$PY" "$ROOT/tools/session_digest.py" --from-hook --root "$ROOT" >/dev/null 2>&1 || true
exit 0
SH
chmod +x .claude/hooks/session_end.sh
```

**必ず `exit 0` で終える。** 記録の失敗でセッション終了を妨げてはならない。

- [ ] **Step 4: `--from-hook` を実装する**

`tools/session_digest.py` に、標準入力の JSON から `transcript_path` を読む経路を足す。
`jq` を使わず、Python の `json` で読む。

- [ ] **Step 5: 設定へ登録する**

`.claude/settings.json` に `SessionEnd` の hook を追加する。既存の設定がある場合は
**そこへ追記し、既存の項目を消さない。**

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/session_end.sh\""
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 6: 手動で経路を確認する**

hook を実際に発火させる前に、標準入力からの経路が動くことを確かめる。

```bash
LATEST=$(ls -1t ~/.claude/projects/*/*.jsonl 2>/dev/null | head -1)
printf '{"session_id":"probe","transcript_path":"%s","cwd":"%s","hook_event_name":"SessionEnd"}\n' \
  "$LATEST" "$(pwd)" | .claude/hooks/session_end.sh
echo "exit=$?"
ls -la docs/sessions/digest/ | tail -5
```

Expected: `exit=0` かつ抽出物が生成される

- [ ] **Step 7: G2 ゲート — 実際にセッションを終了させて確認する**

**これは実行者が自分のセッションを終了する必要がある。** 手順を利用者へ提示し、
確認を依頼する。

1. 現在の抽出物の件数を数える
2. セッションを終了する
3. 新しいセッションで件数を数え直す
4. 増えていれば PASS

```bash
ls -1 docs/sessions/digest/ | wc -l
```

**増えていなければ、hook が発火していないか、設定が読まれていない。**
停止して報告する。設定の優先順位（ユーザ全体・プロジェクト・プロジェクト個別）を
確認すること。

- [ ] **Step 8: `docs/sessions/README.md` を書く**

```markdown
# sessions — 対話から抽出した記録

## 中身

    docs/sessions/digest/<日付>-<セッション識別子>.md

対話記録から機械的に抽出した要素のみ。会話本文・要約・評価は含まない。

## 生の記録

版管理へは入れない。各実装系の既定の保存先に残る。必要ならそこを直接参照する。

## 検索

    rg <検索語> docs/sessions/

## 判断

抽出物は素材であり判断ではない。判断は `tasks/inbox.md` へ 1 行で置く。
```

- [ ] **Step 9: commit**

```bash
git add .claude/ docs/sessions/README.md tools/session_digest.py
git commit -m "feat(sessions): capture a digest when a session ends"
```

**抽出物そのものを commit するかは判断が要る。** 版管理へ入れれば他ホストからも
検索できるが、量が増え続ける。**本 task では 1 件だけ commit して動作を示し、
継続的に commit するかは申し送りとする。**

---

# Phase C — 第二の実装系と記録の訂正

## Task 4: 第二の実装系でも記録を残す

**Files:**
- Create または Modify: 第二の実装系の設定

第二の実装系にも同種の事象がある。ただし**文脈の渡し方が異なり、標準入力の JSON のみで
渡される**。専用の環境変数は設定されない。

- [ ] **Step 1: 設定の場所と形式を確認する**

```bash
ls -la ~/.codex/ 2>/dev/null || echo "ユーザ設定なし"
cat ~/.codex/config.toml 2>/dev/null | head -40 || echo "config.toml なし"
ls -la .codex/ 2>/dev/null
codex --version 2>&1
```

- [ ] **Step 2: 対話記録の保存先を実測する**

```bash
find ~/.codex -name "*.jsonl" 2>/dev/null | head -5
ls -la ~/.codex/sessions/ 2>/dev/null | head || echo "sessions ディレクトリなし"
```

**保存先も形式も実測する。第一の実装系と同じと仮定しない。**

- [ ] **Step 3: 抽出器が第二の形式を読めるか確認する**

```bash
CX=$(find ~/.codex -name "*.jsonl" 2>/dev/null | head -1)
if [ -n "$CX" ]; then
  head -1 "$CX" | python3 -m json.tool | head -20
  .venv/bin/python tools/session_digest.py --transcript "$CX" --stdout | head -20
else
  echo "記録が見つからない"
fi
```

**形式が違って読めない場合、抽出器を分岐させるか、第二の実装系は対象外とする。**
どちらを選んだかと理由を RESULT へ記録する。**推測で構造を仮定して実装しない。**

- [ ] **Step 4: 設定へ登録する**

Step 1 で確認した形式に従って登録する。**環境変数に依存しない実装にする**
（第二の実装系では専用の環境変数が設定されない）。

- [ ] **Step 5: G3 ゲート — 記録が生成されることを確認する**

```bash
BEFORE=$(ls -1 docs/sessions/digest/ | wc -l)
codex exec "echo 動作確認" >/dev/null 2>&1
sleep 2
AFTER=$(ls -1 docs/sessions/digest/ | wc -l)
echo "before=$BEFORE after=$AFTER"
```

`on_fail: ask` である。**生成されなくても自動で停止せず、結果と原因を提示して
判断を仰ぐ。** 第二の実装系での自動化が難しい場合、**手動で抽出する手順を文書化する**
ことで代替とし、その旨を記録する。

- [ ] **Step 6: commit**

```bash
git add .codex/ docs/sessions/README.md
git commit -m "feat(sessions): capture digests from the second agent as well"
```

---

## Task 5: 記録の訂正

**Files:**
- Modify: `tasks/T-2026-08-07-propagation-and-distribution/propagation_audit.md`
- Modify: `tasks/README.md`
- Modify: `context/glossary.md`（新規作成する場合）

- [ ] **Step 1: 実行ホストと到達不能の原因を追記する**

起票者は実行ホストを誤って認識していた。実際の実行ホストは 11 サーバのうちの 1 台であり、
過去の契約もすべて同じホストで実行されている。到達できないのはコンテナの構成によるもので、
**別のサーバへ移っても同じ構成なら結果は変わらない。**

`propagation_audit.md` に追記する。

```markdown
## 実行ホストと到達不能の原因（2026-08-08 追記）

これまでの契約はすべて同一ホストの同一コンテナ内で実行されている。
到達不能はコンテナから外部ネットワークへ出られない構成に起因し、
**他ホストの伝播状況を否定するものではない。**

実測ホストを別のサーバへ変えても、同じコンテナ構成であれば結果は変わらない。
監査を前進させるには、コンテナの外から実行する必要がある。
```

- [ ] **Step 2: プロセス計数の落とし穴を規約へ記す**

同一の誤り（自分自身のプロセスを数えてしまう）が 2 度発生している。**手順で防ぐ。**

`tasks/README.md` の既知差の節に追記する。

```markdown
### 計測上の落とし穴

プロセス数を数えるとき、パターン一致による検索は**検索コマンド自身にも一致する**。
実際に 2 度、誤った値を得ている。プロセスの一覧を取得してから数えること。
```

- [ ] **Step 3: 契約の受け渡しが閉じたことを反映する**

`tasks/README.md` の「契約の受け取り」節を確認し、標準入力からの経路が
既定の手段であることを明記する。

- [ ] **Step 4: commit**

```bash
git add tasks/ 
git commit -m "docs(tasks): correct the propagation record and note measurement pitfalls"
```

---

## Task 6: 自己契約の配置と完了判定

**Files:**
- Create: `tasks/T-2026-08-08-session-durability/RESULT.md`

- [ ] **Step 1: `conventions_rev` を確認する**

**起票者は現在の識別子を知り得ないため、実行者が実測して置換する。これは逸脱ではなく手順である。**

```bash
git log -1 --format=%h -- context/conventions.md
```

- [ ] **Step 2: 自己検証**

```bash
make task-validate TASK=T-2026-08-08-session-durability; echo "exit=$?"
make task-preflight TASK=T-2026-08-08-session-durability; echo "exit=$?"
```

- [ ] **Step 3: 完了判定**

| # | 判定 | コマンド | 期待 |
|---|---|---|---|
| 1 | 抽出器が動く | Task 2 Step 9 | 抽出物が出る |
| 2 | 秘匿が伏せられる | Task 2 Step 8 前半 | 値が伏せ字 |
| 3 | **通常の文が変わらない** | Task 2 Step 8 後半 | 1 文字も変わらない |
| 4 | 秘匿の混入なし | Task 2 Step 9 後半 | `混入なし` |
| 5 | 会話本文が含まれない | `docs/sessions/digest/` を目視 | 自由記述なし |
| 6 | 生の記録が版管理外 | `git status --porcelain \| grep jsonl` | 出力なし |
| 7 | 第一の実装系で自動生成 | Task 3 Step 7 | 件数が増える |
| 8 | 第二の実装系の結果が記録 | Task 4 Step 5 | 生成または理由の記録 |
| 9 | 受け皿が存在する | `cat tasks/inbox.md` | 様式と行がある |
| 10 | 契約検証が通る | `make task-validate` | exit 0 |
| 11 | 実行前検査が通る | `make task-preflight TASK=<本 task>` | exit 0 |
| 12 | テストが全 pass | `python -m pytest tests/test_session_digest.py -q` | 全 pass・件数を実測記録 |
| 13 | 全体テストが不変 | `python -m pytest tests/ -q` | 失敗 5 件のまま |
| 14 | 禁止領域が無変更 | `git diff --name-only origin/phase0...HEAD -- runindex/ context/auto/ context/conventions.md experiments/ transfer/ data/splits/` | 出力なし |

**判定3は判定2の対**である。片方だけでは検査として成立しない。

**判定13に注意**: 本 task の前から 5 件が失敗している。**5 のままなら PASS**、増えたら停止。

- [ ] **Step 4: `RESULT.md` を書く**

必ず含めるもの。

- Task 2 Step 1 の**生の出力**（記録の形式・行の種類・出現するキー）
- 抽出対象から外した要素があれば、その理由
- 伏せ字の規則と、両方向の検査結果
- Task 3 Step 7 の件数の変化
- 第二の実装系の記録の保存先と形式。**読めた場合と読めなかった場合の判断**
- 抽出物を継続的に版管理へ入れるかの判断と理由
- テスト件数（実測）
- **`deviations` を空にしない**
- §6 に、他ホストでの動作確認が未達であることを申し送る
- **`tasks/inbox.md` に本 task の判断を 1 行以上追加したことを記録する**

- [ ] **Step 5: 受け皿へ書く**

**本 task 自身が最初の利用者である。** 対話で出た判断を `tasks/inbox.md` へ置く。
無ければ「なし」と書く。

- [ ] **Step 6: push と PR**

```bash
git add tasks/T-2026-08-08-session-durability/ tasks/inbox.md
git commit -m "feat(tasks): self-apply the contract to session durability"
git push -u origin feat/session-durability
gh pr create --base phase0 \
  --title "feat(sessions): persist machine-derived facts from agent conversations" \
  --body-file tasks/T-2026-08-08-session-durability/RESULT.md
```

**マージは行わない。auto-merge も有効化しない。**

---

## 想定外が起きたときの扱い

| 状況 | 対応 |
|---|---|
| 対話記録の形式が想定と違う | **実測に合わせる。** 読めない要素は抽出対象から外し記録する |
| 伏せ字が過剰で通常の文まで変わる | **G1 停止。** 規則を絞り、両方向で測り直す |
| 抽出物に秘匿が混入した | **G1 停止。** `secret_leaked_into_digest` として報告。commit しない |
| 追跡中の記録形式のファイルがある | `.gitignore` の広い除外は書かない。特定のディレクトリのみにする |
| hook が発火しない | **G2 停止。** 設定の優先順位を確認して報告 |
| 第二の実装系の記録が読めない | 対象外とし、手動の手順を文書化して代替する |
| 抽出物の量が多すぎる | 継続的な版管理を見送り、申し送りとする |
| 全体テストの失敗が 5 件から増えた | 本 task が壊した。停止して報告 |

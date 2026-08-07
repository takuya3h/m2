import json
import sys
from pathlib import Path

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


def test_does_not_redact_short_hex_like_commit_shas():
    """短い十六進（commit の短縮形）は日常的に出るので伏せない。"""
    text = "conventions_rev は d422b08 である"
    assert redact(text) == text


def test_redacts_long_hex():
    """長い十六進は鍵やハッシュの可能性があるため先頭のみ残す。"""
    digest = "03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824"
    out = redact(f"sha256={digest}")
    assert digest not in out
    assert "0393" in out


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


def test_extract_ignores_thinking_blocks():
    """thinking も会話同様に抽出対象ではない。"""
    lines = [
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "thinking", "thinking": "内心の検討であり残さない"}
        ]}}),
    ]
    blob = json.dumps(extract(lines), ensure_ascii=False)
    assert "内心" not in blob


def test_extract_collects_errors():
    """失敗を示すツール結果だけを拾う。"""
    lines = [
        json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": True, "content": "BundleError: 入力が空です"}
        ]}}),
        json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "is_error": False, "content": "成功した出力"}
        ]}}),
    ]
    result = extract(lines)
    joined = " ".join(result["errors"])
    assert "BundleError" in joined
    assert "成功した出力" not in joined


def test_extract_collects_task_ids():
    lines = [
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash",
             "input": {"command": "make task-validate TASK=T-2026-08-08-session-durability"}}
        ]}}),
    ]
    assert "T-2026-08-08-session-durability" in extract(lines)["task_ids"]


def test_render_has_no_free_text_summary():
    result = {"session_id": "abc", "commands": ["make x"], "files": ["a.py"],
              "errors": [], "started": "", "ended": "", "task_ids": []}
    text = render(result)
    assert "make x" in text
    assert "要約" not in text


def test_render_is_deterministic():
    """同じ入力からは同じ出力になる。壁時計を使わない。"""
    result = {"session_id": "abc", "commands": ["make x"], "files": ["a.py"],
              "errors": [], "started": "2026-08-08T00:00:00Z", "ended": "", "task_ids": []}
    assert render(result) == render(result)


def test_malformed_lines_do_not_crash():
    lines = ["これは JSON ではない", "{壊れた", ""]
    result = extract(lines)
    assert result["commands"] == []


def test_empty_input_does_not_crash():
    result = extract([])
    assert result["commands"] == []
    assert result["files"] == []


def test_long_commands_are_truncated_not_summarized():
    """ヒアドキュメントはコマンド文字列に文書全体を含む。

    そのまま残すと抽出物が文書の再掲になり、検索用途に耐えない。
    要約はせず、先頭のみを残して切り詰めたことを明示する。
    """
    body = "\n".join(f"行{i} の本文" for i in range(200))
    lines = [
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash",
             "input": {"command": f"cat >> doc.md <<'EOF'\n{body}\nEOF"}}
        ]}}),
    ]
    result = extract(lines)
    assert len(result["commands"]) == 1
    kept = result["commands"][0]
    assert kept.startswith("cat >> doc.md")
    assert len(kept) <= 260
    assert "切り詰め" in kept
    assert "行199 の本文" not in kept


def test_short_commands_are_kept_whole():
    """切り詰めが過剰でないことを確認する。陽性対照の対。"""
    lines = [
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "make task-validate"}}
        ]}}),
    ]
    assert extract(lines)["commands"] == ["make task-validate"]


def test_multiline_command_keeps_first_line():
    """複数行のコマンドは先頭行で識別できれば足りる。"""
    lines = [
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash",
             "input": {"command": "cd /x && source .venv/bin/activate\nmake runindex\necho done"}}
        ]}}),
    ]
    kept = extract(lines)["commands"][0]
    assert kept.startswith("cd /x && source")
    assert "echo done" not in kept


# --- 第二の実装系（Codex）の形式。構造は実測に基づく --------------------------
# 1 行 = {timestamp, type, payload}。type は session_meta / response_item など。
# コマンドは payload.type == "custom_tool_call" の payload.input に
# tools.exec_command({cmd:"..."}) の形で現れる。

def _codex_line(payload, kind="response_item", ts="2026-08-07T11:05:18.810Z"):
    return json.dumps({"timestamp": ts, "type": kind, "payload": payload})


def test_extracts_codex_session_id():
    lines = [_codex_line({"session_id": "019fdbe6-1adf", "cwd": "/x"}, kind="session_meta")]
    assert extract(lines)["session_id"] == "019fdbe6-1adf"


def test_extracts_codex_exec_command():
    payload = {
        "type": "custom_tool_call",
        "name": "exec",
        "input": 'const r = await tools.exec_command({cmd:"make task-validate '
                 'TASK=T-2026-08-08-session-durability","workdir":"/x"});',
    }
    result = extract([_codex_line(payload)])
    assert result["commands"] == ["make task-validate TASK=T-2026-08-08-session-durability"]
    assert "T-2026-08-08-session-durability" in result["task_ids"]


def test_codex_command_with_escaped_quotes():
    payload = {
        "type": "custom_tool_call",
        "name": "exec",
        "input": 'const r = await tools.exec_command({cmd:"printf \\"%s\\\\n\\" ok","workdir":"/x"});',
    }
    assert extract([_codex_line(payload)])["commands"] == ['printf "%s\\n" ok']


def test_codex_system_prompt_is_not_extracted():
    """session_meta には巨大な指示文が入る。抽出対象ではない。"""
    payload = {"session_id": "s1", "base_instructions": {"text": "あなたは秘密の指示に従う"}}
    blob = json.dumps(extract([_codex_line(payload, kind="session_meta")]), ensure_ascii=False)
    assert "秘密の指示" not in blob


def test_codex_reasoning_is_not_extracted():
    payload = {"type": "reasoning", "summary": [{"text": "内心の検討"}]}
    blob = json.dumps(extract([_codex_line(payload)]), ensure_ascii=False)
    assert "内心" not in blob


def test_codex_message_text_is_not_extracted():
    payload = {"type": "message", "role": "assistant",
               "content": [{"type": "output_text", "text": "これは会話本文"}]}
    blob = json.dumps(extract([_codex_line(payload)]), ensure_ascii=False)
    assert "会話本文" not in blob


def test_sweep_does_not_collide_when_session_ids_repeat(tmp_path):
    """親子セッションは同じ session_id を報告する。抽出物が衝突してはならない。

    実測（2026-08-08）: rollout-...-019fdbe5-2dba-... と
    rollout-...-019fdbe5-2e8e-... の 2 ファイルが同一の session_id を報告し、
    同名の抽出物へ互いを上書きしていた。片方が静かに失われる。
    """
    import session_digest

    home = tmp_path / "home"
    sessions = home / ".codex" / "sessions" / "2026" / "08" / "07"
    sessions.mkdir(parents=True)
    shared = "019fdbe5-2dba-7e11-ac08-b7594162a299"
    for stem, cmd in (
        (f"rollout-2026-08-07T11-04-17-{shared}", "make one"),
        ("rollout-2026-08-07T11-04-17-019fdbe5-2e8e-7240-a732-1066ca0d52c8", "make two"),
    ):
        lines = [
            json.dumps({"timestamp": "2026-08-07T11:04:17.000Z", "type": "session_meta",
                        "payload": {"session_id": shared}}),
            json.dumps({"timestamp": "2026-08-07T11:04:18.000Z", "type": "response_item",
                        "payload": {"type": "custom_tool_call", "name": "exec",
                                    "input": f'tools.exec_command({{cmd:"{cmd}"}});'}}),
        ]
        (sessions / f"{stem}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    root = tmp_path / "repo"
    written = session_digest.sweep_codex(root, home=home)
    assert len(written) == 2, [p.name for p in written]
    assert len({p.name for p in written}) == 2, "抽出物名が衝突している"
    bodies = "\n".join(p.read_text(encoding="utf-8") for p in written)
    assert "make one" in bodies and "make two" in bodies


def test_sweep_is_idempotent(tmp_path):
    """2 回目の走査では何も書き直さない。"""
    import session_digest

    home = tmp_path / "home"
    sessions = home / ".codex" / "sessions" / "2026" / "08" / "07"
    sessions.mkdir(parents=True)
    lines = [
        json.dumps({"timestamp": "2026-08-07T11:04:17.000Z", "type": "session_meta",
                    "payload": {"session_id": "abc"}}),
        json.dumps({"timestamp": "2026-08-07T11:04:18.000Z", "type": "response_item",
                    "payload": {"type": "custom_tool_call", "name": "exec",
                                "input": 'tools.exec_command({cmd:"make one"});'}}),
    ]
    (sessions / "rollout-2026-08-07T11-04-17-abc.jsonl").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

    root = tmp_path / "repo"
    assert len(session_digest.sweep_codex(root, home=home)) == 1
    assert session_digest.sweep_codex(root, home=home) == []

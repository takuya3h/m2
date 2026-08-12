"""notes.md の構造化ブロック parser/validator（§8 スキーマ）。

各実験フォルダの `notes.md` にはフェンス付きブロックを書ける:

    ```decision
    title: phase→det は機構非依存で弱い
    status: 撤退        # 採用 / 撤退 / 保留
    affects: §17.1, 方向非対称
    body: |
      oracle-phase 等で改善せず確定。
    ```

    ```lesson
    title: NpzFile OOM
    recurrence_guard: _index_npz で一括展開
    body: |
      eval_det2phase_test.py の per-key ループが exit137 の原因。
    ```

設計原則（§8）:
- **未知キーは警告して無視**（前方互換）
- ブロックが無ければ何もしない（fail-open）
- 数値は書かない（台帳が持つ）。本文は人間が書く（LLM 自動生成しない）
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# 公式キーの allow-list（未知キーは警告のみ・無視）
DECISION_KEYS = {
    "title",
    "status",
    "affects",
    "body",
    "type",
    "impact",
    "related_steps",
    "date",
    "source",
    "revisit_trigger",
}
LESSON_KEYS = {
    "title",
    "recurrence_guard",
    "body",
    "category",
    "severity",
    "status",
    "symptom",
    "root_cause",
    "prevention",
    "related_steps",
    "date",
    "evidence",
}
PROMPT_KEYS = {
    "title",
    "body",
    "target",
    "tags",
    "related_step",
    "status",
    "version",
}

# 公式の status enum (decision)
DECISION_STATUS_MAP = {
    "採用": "active",
    "撤退": "superseded",
    "保留": "needs review",
    # 英語直書きもそのまま受け入れる
    "active": "active",
    "superseded": "superseded",
    "needs review": "needs review",
    "rejected": "rejected",
}

# fenced block の正規表現（```<type>\n...\n```）。改行を含むため DOTALL。
BLOCK_RE = re.compile(
    r"^```(?P<type>decision|lesson|prompt)\s*\n(?P<body>.*?)\n```",
    re.MULTILINE | re.DOTALL,
)


@dataclass
class ParsedBlock:
    """parse 後のブロック。type/parsed dict/raw body/警告メッセージ。"""

    type: str  # "decision" | "lesson" | "prompt"
    data: dict
    raw: str
    warnings: list[str] = field(default_factory=list)


def _parse_yaml_body(text: str) -> dict:
    """ブロック本文を YAML としてパース。PyYAML が無い環境向けに最小 fallback あり。

    body: | の multi-line literal も対応。
    """
    try:
        import yaml

        result = yaml.safe_load(text)
        return result if isinstance(result, dict) else {}
    except ImportError:
        # PyYAML が無い場合の最小フォールバック（key: value, body: | block 対応）
        return _fallback_parse(text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("notes_schema: YAML parse 失敗 → 空 dict (%s)", exc)
        return {}


def _fallback_parse(text: str) -> dict:
    """PyYAML 非依存の最小 parser。`key: value` と `body: |` の literal block のみ対応。"""
    out: dict = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^(?P<key>\w+)\s*:\s*(?P<val>.*?)\s*$", line)
        if not m:
            i += 1
            continue
        key, val = m.group("key"), m.group("val")
        if val == "|":
            # literal block: 次行以降のインデント付き行を集める
            block_lines = []
            i += 1
            indent: str | None = None
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip():
                    block_lines.append("")
                    i += 1
                    continue
                cur_indent = re.match(r"^(\s*)", nxt).group(1)
                if indent is None:
                    indent = cur_indent
                if not nxt.startswith(indent) or len(cur_indent) < len(indent):
                    break
                block_lines.append(nxt[len(indent) :])
                i += 1
            out[key] = "\n".join(block_lines).rstrip()
        else:
            out[key] = val.strip("\"'")
            i += 1
    return out


def _validate(block_type: str, data: dict) -> list[str]:
    """allow-list 外のキーを警告。title 欠落は致命的（ブロック無効）。"""
    warnings: list[str] = []
    allowed = {
        "decision": DECISION_KEYS,
        "lesson": LESSON_KEYS,
        "prompt": PROMPT_KEYS,
    }.get(block_type, set())
    for key in data:
        if key not in allowed:
            warnings.append(f"unknown key '{key}' in {block_type} block (ignored)")
    if not data.get("title"):
        warnings.append(f"{block_type} block has no 'title' (block invalid)")
    return warnings


def parse_notes(text: str) -> list[ParsedBlock]:
    """notes.md 全文から fenced block を全部抜き出し、parse + validate して返す。

    無効なブロック（title 欠落）も含めて返す（caller が warnings を見て決める）。
    """
    blocks: list[ParsedBlock] = []
    for m in BLOCK_RE.finditer(text):
        btype = m.group("type")
        body = m.group("body")
        data = _parse_yaml_body(body)
        warns = _validate(btype, data)
        # decision の日本語 status を正規化（採用/撤退/保留 → active/superseded/needs review）
        if btype == "decision" and data.get("status") in DECISION_STATUS_MAP:
            data["status"] = DECISION_STATUS_MAP[data["status"]]
        blocks.append(ParsedBlock(type=btype, data=data, raw=body, warnings=warns))
    return blocks


def parse_notes_file(path: Path | str) -> list[ParsedBlock]:
    """notes.md を読んで parse する。存在しなければ空 list（fail-open）。"""
    p = Path(path)
    if not p.exists():
        return []
    try:
        return parse_notes(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("notes_schema: %s 読込失敗 → 空 list (%s)", p, exc)
        return []


def valid_blocks(blocks: list[ParsedBlock]) -> list[ParsedBlock]:
    """title 持ちの有効ブロックのみ filter。"""
    return [b for b in blocks if b.data.get("title")]

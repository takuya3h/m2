"""Phase A — 直す前の状態を実測して audit/before.json へ残す。

**文法は実装から読む。** 本文に書かれた形を写すと、実装がそれと違っていた場合に
測定そのものが嘘になる。JSON Schema は読み込んで取り出し、Python 側の正規表現は
構文木から literal を取り出す。どちらも人が転記しない。

**記録を作ってから表示する。** 表示のための切り詰めを記録へ混ぜない。
"""

import ast
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
SCHEMA = ROOT / "tasks" / "_schema" / "spec.schema.json"
VALIDATOR = ROOT / "tools" / "validate_task.py"
EXPERIMENTS = ROOT / "runindex" / "experiments.csv"

# 本契約が対象とする群と段（起票者が候補を選ぶ対象）。
TARGET_GROUP, TARGET_STEP = "phase1", "s4_phase_baseline"


def schema_pattern() -> str:
    """スキーマから分母の参照の文法を取り出す。"""
    node = json.loads(SCHEMA.read_text())
    for key in ("properties", "inputs", "properties", "denominator", "properties", "ref"):
        node = node[key]
    return node["pattern"]


def validator_pattern() -> str:
    """実装の構文木から L1-4 の正規表現 literal を取り出す。

    行番号や前後の文脈に依存させない。`re.fullmatch` の第一引数が
    `exp:` で始まる文字列 literal である呼び出しを拾う。
    """
    tree = ast.parse(VALIDATOR.read_text())
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name != "fullmatch" or not node.args:
            continue
        arg = node.args[0]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("exp:"):
            found.append(arg.value)
    if len(found) != 1:
        raise SystemExit(f"L1-4 の正規表現を一意に特定できません: {found}")
    return found[0]


def main() -> None:
    rows = list(csv.DictReader(EXPERIMENTS.open()))
    ids = [r["experiment_id"] for r in rows]

    sch = schema_pattern()
    val = validator_pattern()
    # スキーマ側は先頭固定のみ（末尾は否定先読み）、実装側は fullmatch で全体一致。
    # **それぞれの使われ方に合わせて適用する。** 揃えて測ると実挙動と乖離する。
    sch_re, val_re = re.compile(sch), re.compile(val)

    def passes_schema(eid: str) -> bool:
        return sch_re.match(f"exp:{eid}") is not None

    def passes_validator(eid: str) -> bool:
        return val_re.fullmatch(f"exp:{eid}") is not None

    by_group_step = defaultdict(list)
    for r in rows:
        by_group_step[(r["group"], r["step"])].append(r["experiment_id"])
    ambiguous = {f"{g}/{s}": sorted(v) for (g, s), v in by_group_step.items() if len(v) > 1}

    before = {
        "source": {
            "experiments_csv": str(EXPERIMENTS.relative_to(ROOT)),
            "schema": str(SCHEMA.relative_to(ROOT)),
            "validator": str(VALIDATOR.relative_to(ROOT)),
        },
        "grammar_before": {
            "schema_pattern": sch,
            "validator_pattern": val,
            "are_two_independent_sites": sch != val,
        },
        "counts": {
            "identifiers_total": len(ids),
            "separator_count_2": sum(1 for e in ids if e.count("/") == 2),
            "identifier_equals_step": sum(1 for r in rows if r["experiment_id"] == r["step"]),
            "passes_grammar_before_schema": sum(1 for e in ids if passes_schema(e)),
            "passes_grammar_before_validator": sum(1 for e in ids if passes_validator(e)),
            "ambiguous_group_step_pairs": len(ambiguous),
            "ambiguous_rows": sum(len(v) for v in ambiguous.values()),
            "target_candidates": len(by_group_step[(TARGET_GROUP, TARGET_STEP)]),
        },
        "identifier_prefix_equals_group": sum(
            1 for r in rows if r["experiment_id"].split("/", 1)[0] == r["group"]
        ),
        "separator_dialects": {
            "tilde": sum(1 for e in ids if "~" in e),
            "hash": sum(1 for e in ids if "#" in e),
            "both": sum(1 for e in ids if "~" in e and "#" in e),
            "neither": sum(1 for e in ids if "~" not in e and "#" not in e),
            "hash_identifiers": sorted(e for e in ids if "#" in e),
        },
        "ambiguous_detail": ambiguous,
        "target": {
            "group": TARGET_GROUP,
            "step": TARGET_STEP,
            "candidates": sorted(by_group_step[(TARGET_GROUP, TARGET_STEP)]),
        },
    }

    (AUDIT / "before.json").write_text(json.dumps(before, ensure_ascii=False, indent=2) + "\n")

    c = before["counts"]
    print(f"記録: {AUDIT / 'before.json'}")
    print()
    print("直す前の文法（実装から取得）")
    print(f"  schema   : {sch}")
    print(f"  validator: {val}")
    print(f"  二箇所に独立して存在するか: {before['grammar_before']['are_two_independent_sites']}")
    print()
    print(f"{'測るもの':<34}{'実測':>8}")
    for label, key in (
        ("識別子の総数", "identifiers_total"),
        ("区切りが二個のもの", "separator_count_2"),
        ("識別子が段と等しいもの", "identifier_equals_step"),
        ("直す前の文法を通るもの（schema）", "passes_grammar_before_schema"),
        ("直す前の文法を通るもの（validator）", "passes_grammar_before_validator"),
        ("群と段の組が一意でない組", "ambiguous_group_step_pairs"),
        ("その行数", "ambiguous_rows"),
        ("本件の群と段の候補", "target_candidates"),
    ):
        print(f"{label:<34}{c[key]:>8}")
    d = before["separator_dialects"]
    print()
    print(f"区切りの方言: ~={d['tilde']}  #={d['hash']}  両方={d['both']}  無し={d['neither']}")


if __name__ == "__main__":
    main()

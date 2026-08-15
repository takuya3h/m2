"""Phase B Step 2-3 — 候補の文法を実物に当て、被覆と広げすぎを同時に測る。

**通ることだけを確かめない。** 被覆（実在する識別子がすべて通る）と
広げすぎの検査（落ちるべきものが落ちる）を対で測る。どちらか片方では、
文法が「何でも通す」状態になっていても気づけない。

確定してから実装へ入れる。実装へ入れた後にこの測定器を再実行すると、
実装から読み直した文法で同じ測定が行われる（`--from-impl`）。
"""

import ast
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
SCHEMA = ROOT / "tasks" / "_schema" / "spec.schema.json"
VALIDATOR = ROOT / "tools" / "validate_task.py"
EXPERIMENTS = ROOT / "runindex" / "experiments.csv"

SEG = r"[A-Za-z0-9_.-]+"
# 候補: exp:<群>/<段>/<説明>@<分割> のあとに ~<レシピ> または #<変種> が付いてもよい。
CANDIDATE_BODY = rf"exp:{SEG}/{SEG}/{SEG}@{SEG}(?:~{SEG}|#{SEG})?"
CANDIDATE_SCHEMA = rf"^{CANDIDATE_BODY}(?![\s\S])"

# 広げすぎていないかを見る種。**すべて落ちなければならない。**
REJECT_CASES = [
    ("二区画だけの旧い書式", "exp:phase1/s4_phase_baseline"),
    ("区画が一つ欠けたもの", "exp:phase1/s4_phase_baseline/frozen_tecno_phase_baseline"),
    ("分離の記号が無いもの", "exp:phase1/s4_phase_baseline/frozen_tecno_phase_baseline~relation_detr_seed42"),
    ("許されない記号を含むもの", "exp:phase1/s4_phase_baseline/frozen tecno@val"),
    ("末尾に改行が付いたもの", "exp:phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val\n"),
]


def _impl_patterns() -> tuple[str, str]:
    """実装に入っている文法を読み出す（適用後の確認用）。"""
    node = json.loads(SCHEMA.read_text())
    for key in ("properties", "inputs", "properties", "denominator", "properties", "ref"):
        node = node[key]
    schema_pat = node["pattern"]

    tree = ast.parse(VALIDATOR.read_text())
    found = [
        a.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and (n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")) == "fullmatch"
        and n.args
        for a in [n.args[0]]
        if isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value.startswith("exp:")
    ]
    if len(found) != 1:
        raise SystemExit(f"L1-4 の正規表現を一意に特定できません: {found}")
    return schema_pat, found[0]


def main() -> None:
    from_impl = "--from-impl" in sys.argv
    out_name = "grammar_after.json" if from_impl else "grammar_candidate.json"

    if from_impl:
        schema_pat, validator_pat = _impl_patterns()
        source = "実装から読み出した"
    else:
        schema_pat, validator_pat = CANDIDATE_SCHEMA, CANDIDATE_BODY
        source = "候補（未適用）"

    schema_re, validator_re = re.compile(schema_pat), re.compile(validator_pat)

    def accepts(ref: str) -> tuple[bool, bool]:
        """スキーマ（部分一致＋否定先読み）と実装（全体一致）を、それぞれの使われ方で当てる。"""
        return schema_re.match(ref) is not None, validator_re.fullmatch(ref) is not None

    rows = list(csv.DictReader(EXPERIMENTS.open()))
    ids = [r["experiment_id"] for r in rows]

    # 被覆。**集合差で不通過を出す。** 件数の一致だけでは取りこぼしを見逃す。
    uncovered = sorted({e for e in ids if not all(accepts(f"exp:{e}"))})

    # 区画が列の値と対応しているか（文言を正しく書くための裏づけ）。
    decompose_mismatch = []
    for r in rows:
        m = re.fullmatch(rf"({SEG})/({SEG})/({SEG})@({SEG})(?:[~#]({SEG}))?", r["experiment_id"])
        if not m:
            decompose_mismatch.append({"experiment_id": r["experiment_id"], "reason": "分解できない"})
            continue
        group, step, desc, split, _tail = m.groups()
        if (group, step, desc, split) != (r["group"], r["step"], r["description"], r["split"]):
            decompose_mismatch.append(
                {
                    "experiment_id": r["experiment_id"],
                    "from_id": [group, step, desc, split],
                    "from_columns": [r["group"], r["step"], r["description"], r["split"]],
                }
            )

    rejects = []
    for label, ref in REJECT_CASES:
        s_ok, v_ok = accepts(ref)
        rejects.append(
            {"label": label, "ref": ref, "schema_accepts": s_ok, "validator_accepts": v_ok,
             "rejected_by_both": not s_ok and not v_ok}
        )

    result = {
        "source": source,
        "patterns": {"schema": schema_pat, "validator": validator_pat},
        "coverage": {
            "total": len(ids),
            "covered": len(ids) - len(uncovered),
            "uncovered": uncovered,
            "all_covered": not uncovered,
        },
        "decomposition": {
            "matches_columns": len(rows) - len(decompose_mismatch),
            "total": len(rows),
            "mismatch": decompose_mismatch,
        },
        "overreach": {"cases": rejects, "all_rejected": all(r["rejected_by_both"] for r in rejects)},
    }
    (AUDIT / out_name).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"記録: {AUDIT / out_name}   ({source})")
    print(f"  schema   : {schema_pat}")
    print(f"  validator: {validator_pat}")
    print()
    cov = result["coverage"]
    print(f"被覆: {cov['covered']} / {cov['total']}   全件通過={cov['all_covered']}")
    if uncovered:
        for e in uncovered[:10]:
            print(f"    通らない: {e}")
    d = result["decomposition"]
    print(f"区画が列と対応: {d['matches_columns']} / {d['total']}")
    for m in d["mismatch"][:5]:
        print(f"    不一致: {m}")
    print()
    print("広げすぎの検査（すべて落ちること）")
    for r in rejects:
        mark = "落ちる" if r["rejected_by_both"] else "★通ってしまう★"
        print(f"  {mark:<16} {r['label']}")
    print()
    print(f"確定してよいか（被覆かつ広げすぎ無し）: {cov['all_covered'] and result['overreach']['all_rejected']}")


if __name__ == "__main__":
    main()

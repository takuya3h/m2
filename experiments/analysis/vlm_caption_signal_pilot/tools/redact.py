"""SPEC §4.1 の伏せ字（甲・乙・丙）と検査（プロンプト選択肢 0 件・陽性対照）。"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

KO_TOOL_SYNONYMS = (
    "tweezer", "pickup", "sponge", "needle driver", "suction tube", "sucker",
    "shears", "cautery", "electrocautery", "diathermy", "bovie",
    "knife", "knives", "blade", "periosteal elevator", "elevator", "bipolar", "gag",
)
KO_PHASE_SPELLING = ("anaesthesia", "haemostasis")

OTSU_STEMS = (
    "disinfect", "design", "anesthe", "anaesthe", "incis", "dissect",
    "hemosta", "haemosta", "irrigat", "clos", "dress", "tweez",
    "gauze", "forcep", "gag", "suction", "suck", "scissor", "retract",
    "cauter", "diatherm", "hook", "scalpel", "raspator", "bipolar",
    "syring", "skewer",
)


def load_ko_terms() -> list[str]:
    ann = json.loads((ROOT / "data/annotations/egosurgery_tool/instances_train.json").read_text())
    tool_names = [c["name"] for c in sorted(ann["categories"], key=lambda x: x["id"])]
    vocab = json.loads((ROOT / "data/processed/phase_manifest/phase_vocab.json").read_text())
    phase_names = sorted(vocab.keys())
    raw = list(dict.fromkeys(tool_names + list(KO_TOOL_SYNONYMS) + phase_names + list(KO_PHASE_SPELLING)))
    return raw


def _term_to_regex(term: str) -> str:
    """単数・複数形を語の境界でマッチする正規表現片を作る。"""
    t = term.strip().lower()
    parts = t.split()
    last = parts[-1]
    if last == "knives":
        last_pat = "knives"
    elif last == "knife":
        last_pat = r"kni(?:fe|ves)"
    elif last == "cannula":
        last_pat = r"cannul(?:a|as|ae)"
    elif last.endswith("y") and len(last) > 1 and last[-2] not in "aeiou":
        last_pat = re.escape(last[:-1]) + r"(?:y|ies)"
    elif last.endswith("s"):
        # 既に複数形（Forceps, Scissors, Tweezers, Holders, shears, hemostasis 等）
        if last in ("holders", "tweezers"):
            last_pat = re.escape(last[:-1]) + r"s?"
        else:
            last_pat = re.escape(last) + r"(?:es)?"
    elif last.endswith(("x", "z", "ch", "sh")):
        last_pat = re.escape(last) + r"(?:es)?"
    else:
        last_pat = re.escape(last) + r"s?"
    if len(parts) > 1:
        prefix = r"\s+".join(re.escape(p) for p in parts[:-1])
        body = prefix + r"\s+" + last_pat
    else:
        body = last_pat
    return rf"\b{body}\b"


def build_ko_pattern() -> re.Pattern:
    terms = sorted(load_ko_terms(), key=lambda s: (-len(s), s.lower()))
    return re.compile("|".join(_term_to_regex(t) for t in terms), re.IGNORECASE)


def build_otsu_stem_pattern() -> re.Pattern:
    stems = sorted(OTSU_STEMS, key=lambda s: (-len(s), s))
    return re.compile(rf"\b(?:{'|'.join(re.escape(s) for s in stems)})[a-z]*\b", re.IGNORECASE)


KO_PATTERN = build_ko_pattern()
OTSU_STEM_PATTERN = build_otsu_stem_pattern()


def redact_ko(text: str) -> tuple[str, list[str]]:
    hits = [m.group(0) for m in KO_PATTERN.finditer(text)]
    out = KO_PATTERN.sub("something", text)
    return out, hits


def redact_otsu(text: str) -> tuple[str, list[str]]:
    # まず甲の長い語句から置換し、次に乙の語幹で始まる語を置換
    t1, h1 = redact_ko(text)
    h2 = [m.group(0) for m in OTSU_STEM_PATTERN.finditer(t1)]
    t2 = OTSU_STEM_PATTERN.sub("something", t1)
    return t2, h1 + h2


def otsu_collapsed_choices(choices: dict[str, list[str]]) -> dict[str, list[str]]:
    """乙の語幹を含む選択肢（cannot tell に寄せる対象）を返す。"""
    collapsed = {}
    for k, vals in choices.items():
        hit_vals = [v for v in vals if OTSU_STEM_PATTERN.search(v)]
        if hit_vals:
            collapsed[k] = hit_vals
    return collapsed


def check_prompt_choices(choices: dict[str, list[str]]) -> dict:
    ko_hits = []
    for k, vals in choices.items():
        for v in vals:
            _, h = redact_ko(v)
            if h:
                ko_hits.append({"key": k, "value": v, "hits": h})
    # 陽性対照: 術具クラス名を 1 つ含む文を甲の照合器にかけると 1 件を出す
    pos_text = "The surgeon uses a Scalpel near the skin."
    _, pos_hits = redact_ko(pos_text)
    return {
        "ko_terms_count": len(load_ko_terms()),
        "prompt_choices_ko_hits": ko_hits,
        "prompt_choices_ko_zero": len(ko_hits) == 0,
        "otsu_collapsed_choices": otsu_collapsed_choices(choices),
        "positive_control": {
            "input": pos_text,
            "hits": pos_hits,
            "count": len(pos_hits),
        },
    }


def redact_record(parsed: dict | None, choices: dict[str, list[str]], mode: str) -> tuple[dict | None, Counter]:
    """parsed 辞書に mode ('ko'|'otsu'|'hei') の伏せ字を適用する。"""
    counts = Counter()
    if parsed is None:
        return None, counts
    out = {
        "wound": parsed["wound"],
        "tissue_action": parsed["tissue_action"],
        "surface": parsed["surface"],
        "visibility": parsed["visibility"],
        "attributes": dict(parsed["attributes"]),
    }
    fn = redact_otsu if mode == "otsu" else redact_ko
    for field in ("wound", "tissue_action", "surface"):
        new_text, hits = fn(out[field])
        out[field] = new_text
        counts[field] += len(hits)
    if mode == "otsu":
        collapsed = otsu_collapsed_choices(choices)
        if out["visibility"] in collapsed.get("visibility", ()):
            out["visibility"] = "cannot tell"
            counts["attr_collapsed"] += 1
        for k, vals in collapsed.items():
            if k != "visibility" and out["attributes"].get(k) in vals:
                out["attributes"][k] = "cannot tell"
                counts["attr_collapsed"] += 1
    if mode == "hei":
        # 丙: 甲と同じ伏せ字に加えて tissue_action の文と属性 action・target を外す
        out["tissue_action"] = ""
        out["attributes"]["action"] = None
        out["attributes"]["target"] = None
    return out, counts


if __name__ == "__main__":
    import captions as cap
    ch = cap.options()
    print(json.dumps(check_prompt_choices(ch), ensure_ascii=False, indent=2))

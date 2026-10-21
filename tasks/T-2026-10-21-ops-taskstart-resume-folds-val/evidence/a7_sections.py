"""A-7: 規約をアンカーごとの節に切り、節ごとの sha256 を出す。切り方は tools/validate_task.py の _ANCHOR_RE。
先頭（最初のアンカーより前）は _preamble とする。引数: 規約のファイル（省略時 context/conventions.md）"""
import hashlib, sys
from pathlib import Path
sys.path.insert(0, "tools")
import validate_task
text = Path(sys.argv[1] if len(sys.argv) > 1 else "context/conventions.md").read_text(encoding="utf-8")
ms = list(validate_task._ANCHOR_RE.finditer(text))
spans = [("_preamble", 0, ms[0].start() if ms else len(text))]
for i, m in enumerate(ms):
    spans.append((m.group(1), m.start(), ms[i + 1].start() if i + 1 < len(ms) else len(text)))
for name, a, b in spans:
    print(f"{name}\t{hashlib.sha256(text[a:b].encode()).hexdigest()}\t{text[a:b].count(chr(10))}")

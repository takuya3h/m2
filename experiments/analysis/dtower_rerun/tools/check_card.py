"""G1 (Task A-3): the proposal card's version line must say 五版.

    python check_card.py [card path]   # exit 0 when the first 「版:」 field is 五版, 1 otherwise
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/proposals/2026-10-21-tower-reselect-search.md"
match = re.search(r"版: ([^（／\n]+)", path.read_text(encoding="utf-8"))
found = match.group(1).strip() if match else None
print(f"card={path} version={found}")
sys.exit(0 if found == "五版" else 1)

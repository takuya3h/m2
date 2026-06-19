#!/usr/bin/env python3
"""
reference_check.py —— M2研究計画 リライト検証スクリプト

blueprint §6（参照張り替えマップ）と §9（リスク・チェックリスト）に基づき、
リライト後の Markdown に旧フレームの参照が残っていないか、知識（子ページ
リンク・テーブル様式）が保全されているかを機械的に検証する。

使い方:
    python reference_check.py <path>            # 単一 .md ファイル or ディレクトリ
    python reference_check.py sections/         # ディレクトリは *.md を再帰走査
    python reference_check.py m2_plan_v2_full.md

出力: チェック項目ごとに [PASS]/[WARN]/[FAIL] と該当行。終了コードは FAIL があれば 1。

注意:
- このスクリプトは「検出補助」であり最終判断は人間が行う。WARN は文脈確認用。
- S0 / S0-frozen / S4 は D3 で「名前を残す」確定のため許容（FAIL にしない）。
"""

import re
import sys
from pathlib import Path

# ---- 期待値 ----
EXPECTED_CHILD_PAGES = 22          # §11 サーベイ子ページ数（blueprint §2）
RELATION_DETR_MAP = "0.730"        # 実測値（捏造検出の補助）

# ---- パターン定義 ----
# 「消えているべき」旧フレーム語（残っていたら FAIL）
PAT_MUTUAL = re.compile(r"相互改善|mutual\s+improvement", re.IGNORECASE)

# H1〜H4（バウンダリつき）。結合効果/Phase-2 に翻訳されているべき → 残存は FAIL
PAT_H1234 = re.compile(r"(?<![A-Za-z0-9\-])H[1-4](?![0-9A-Za-z])")

# H-C / H-A / H-H（維持されているべき → 存在を確認、WARN ではなく情報）
PAT_HPOOL = re.compile(r"(?<![A-Za-z0-9\-])H-[CAH](?![A-Za-z])")

# S5〜S9（STEP/Phase-2 へ翻訳されているべき → 残存は FAIL）
PAT_S59 = re.compile(r"(?<![A-Za-z0-9\-])S[5-9](?![0-9A-Za-z\-])")

# S1/S2/S3/S7.5（知識章の歴史参照は許容だが要確認 → WARN）
PAT_S123 = re.compile(r"(?<![A-Za-z0-9\-])S[123](?![0-9A-Za-z\-])|S7\.5")

# 許容される名前（FAIL から除外）: S0-frozen, S0, S4
PAT_ALLOWED_S = re.compile(r"S0-frozen|(?<![A-Za-z0-9\-])S0(?![0-9A-Za-z\-])|(?<![A-Za-z0-9\-])S4(?![0-9A-Za-z\-])")

# Stage B / Stage B' / Stage C（Exo 段階 → Phase-2 へ。残存は WARN：縮約節に残る場合あり）
PAT_STAGE_BC = re.compile(r"Stage\s+B['′]?|Stage\s+C(?![A-Za-z])")

# 子ページ参照（§11 で 22 本保全すべき）
PAT_CHILD_PAGE = re.compile(r'<page\s+url="[^"]+">')

# Notion 様式テーブル（パイプ表ではなく <table> を使うべき）
PAT_NOTION_TABLE = re.compile(r'<table\b')
PAT_PIPE_TABLE = re.compile(r"^\s*\|.+\|\s*$", re.MULTILINE)

# STEP 0–D の骨子が入っているか（新フレームの存在確認）
PAT_STEP = re.compile(r"STEP\s*[0ABCD]")


def gather_files(path: Path):
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.md"))


def find_lines(text, pattern):
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            # 許容Sを除いた純粋なヒットか確認（S系のみ）
            hits.append((i, line.strip()))
    return hits


def filter_s_hits(text, pattern):
    """S系: 許容名(S0-frozen/S0/S4)だけの行は除外する。"""
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if not pattern.search(line):
            continue
        # その行から許容Sを取り除いてもまだヒットするか
        stripped = PAT_ALLOWED_S.sub("", line)
        if pattern.search(stripped):
            hits.append((i, line.strip()))
    return hits


def report(tag, msg):
    print(f"[{tag}] {msg}")


def check_file(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    print("\n" + "=" * 70)
    print(f"FILE: {path}")
    print("=" * 70)
    fail = False

    # 1. 「相互改善」残存
    hits = find_lines(text, PAT_MUTUAL)
    if hits:
        fail = True
        report("FAIL", f"『相互改善/mutual improvement』が {len(hits)} 箇所残存（→『タスク結合の効果』へ）")
        for ln, s in hits[:8]:
            print(f"        L{ln}: {s[:90]}")
    else:
        report("PASS", "『相互改善』なし")

    # 2. H1〜H4 残存
    hits = find_lines(text, PAT_H1234)
    if hits:
        fail = True
        report("FAIL", f"H1〜H4 が {len(hits)} 箇所残存（→ 結合効果①/② or Phase-2 へ翻訳）")
        for ln, s in hits[:12]:
            print(f"        L{ln}: {s[:90]}")
    else:
        report("PASS", "H1〜H4 の残存なし")

    # 3. H-C/H-A/H-H 存在確認（情報）
    hits = find_lines(text, PAT_HPOOL)
    if hits:
        report("INFO", f"H-C/H-A/H-H を {len(hits)} 箇所で確認（仮説プール・維持で正しい）")
    # 存在しなくても章によっては正常なので FAIL/WARN にしない

    # 4. S5〜S9 残存
    hits = filter_s_hits(text, PAT_S59)
    if hits:
        fail = True
        report("FAIL", f"S5〜S9 が {len(hits)} 箇所残存（→ STEP B/C/D or Phase-2 へ）")
        for ln, s in hits[:12]:
            print(f"        L{ln}: {s[:90]}")
    else:
        report("PASS", "S5〜S9 の残存なし")

    # 5. S1/S2/S3/S7.5（要確認）
    hits = filter_s_hits(text, PAT_S123)
    if hits:
        report("WARN", f"S1/S2/S3/S7.5 が {len(hits)} 箇所（知識章の歴史参照なら可・STEP対応注記を確認）")
        for ln, s in hits[:8]:
            print(f"        L{ln}: {s[:90]}")

    # 6. Stage B/C 残存（要確認）
    hits = find_lines(text, PAT_STAGE_BC)
    if hits:
        report("WARN", f"Stage B/B'/C が {len(hits)} 箇所（Phase-2 縮約節に残るなら可・本文の主軸でないか確認）")
        for ln, s in hits[:6]:
            print(f"        L{ln}: {s[:90]}")

    # 7. 子ページ参照数（§11 を含むファイルのみ意味を持つ）
    n_child = len(PAT_CHILD_PAGE.findall(text))
    if n_child > 0:
        if n_child >= EXPECTED_CHILD_PAGES:
            report("PASS", f"子ページ参照 {n_child} 本（期待 {EXPECTED_CHILD_PAGES} 本以上）")
        else:
            fail = True
            report("FAIL", f"子ページ参照が {n_child} 本のみ（§11 は {EXPECTED_CHILD_PAGES} 本必要・脱落は子ページ削除リスク）")

    # 8. テーブル様式
    n_notion = len(PAT_NOTION_TABLE.findall(text))
    pipe_rows = PAT_PIPE_TABLE.findall(text)
    if pipe_rows:
        report("WARN", f"パイプ表らしき行が {len(pipe_rows)} 行（Notion 様式 <table> へ変換推奨）")
    if n_notion:
        report("INFO", f"Notion 様式テーブル <table> を {n_notion} 個検出")

    # 9. STEP 骨子の存在（新フレーム導入の確認・§12/§13 を含むファイルで意味）
    if PAT_STEP.search(text):
        report("INFO", "STEP 0–D の語を検出（新フレーム導入済み）")

    # 10. 実測値の整合（捏造検出の補助）
    if "Relation-DETR" in text and RELATION_DETR_MAP not in text:
        report("WARN", f"Relation-DETR の言及があるが mAP {RELATION_DETR_MAP} が見当たらない（実測値の整合を確認）")
    if "0.327" in text:
        report("WARN", "旧 README 値 0.327 を検出（無効値・現行は DETR 系へ更新のはず）")

    return fail


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    root = Path(sys.argv[1])
    if not root.exists():
        print(f"パスが存在しません: {root}")
        sys.exit(2)

    files = gather_files(root)
    if not files:
        print(f"対象 .md が見つかりません: {root}")
        sys.exit(2)

    any_fail = False
    for f in files:
        if check_file(f):
            any_fail = True

    print("\n" + "#" * 70)
    if any_fail:
        print("# 結果: FAIL あり —— 上記 [FAIL] を blueprint §6 に沿って解消すること。")
        print("#" * 70)
        sys.exit(1)
    else:
        print("# 結果: FAIL なし。WARN は文脈確認のうえ問題なければ完了。")
        print("#" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()

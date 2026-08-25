"""results.json から REPORT.md を描く。**数値を手で転記しない。**

判定は則に依存するが、効果量と符号の個数は依存しない。表では両者を別の列に置き、
後から別の則を当てられるようにする。
"""
import json, sys
from pathlib import Path

D = Path(sys.argv[1])          # 成果物の置き場
R = json.load(open(D / "results.json", encoding="utf-8"))
rows, missing, ctrl = R["rows"], R["missing"], R["controls"]
RULES = ["R0", "R1", "R2", "R3"]
LABEL = {"R0": "R0 現行", "R1": "R1 NB 補正", "R2": "R2 反復 LOVO", "R3": "R3 符号反転"}


def mark(row, k):
    if k not in row or row[k] is None:
        return "未測定"
    v = row[k]
    if v.get("se") is None and k == "R2":
        return "UNKNOWN"
    return "検出" if v["detect"] else "—"


def stat(row, k):
    if k not in row or row[k] is None:
        return "UNKNOWN"
    v = row[k]
    if k == "R3":
        return f"p={v['p']:.4f}"
    if k == "R2":
        if v.get("se") is None:
            return "UNKNOWN"
        return f"[{v['lo']:+.4f}, {v['hi']:+.4f}]"
    return f"{v['stat']:.2f}"


out = []
A = out.append
A("# 一つ抜き検証の判定則の再構築と既存結論の再判定")
A("")
A("**task_id:** T-2026-08-26-lovo-decision-rule  **kind:** analysis")
A("")
A("本書の数値はすべて実測である。出所は `folds/*.json`（fold ごとの素の値）と")
A("`results.json`（判定）で、いずれも `analyze.py` が生成する。**手で転記した数値は無い。**")
A("")

# --- 1 まず結論
changed = [r for r in rows if r["R0"]["detect"] != r["R1"]["detect"]]
changed2 = [r for r in rows if "R2" in r and r["R2"] and r["R2"].get("se") is not None
            and r["R0"]["detect"] != r["R2"]["detect"]]
A("## 1. 報告会で最初に知りたいこと")
A("")
A(f"- 再判定した行: **{len(rows)} 行**（結論 × 指標）")
for k in RULES:
    n = sum(1 for r in rows if mark(r, k) == "検出")
    u = sum(1 for r in rows if mark(r, k) in ("未測定", "UNKNOWN"))
    A(f"- {LABEL[k]}: 検出 **{n} 行**" + (f"（測れなかった {u} 行）" if u else ""))
A(f"- **現行の則 R0 と R1 で判定が変わった行: {len(changed)} 行**")
A(f"- **現行の則 R0 と R2 で判定が変わった行: {len(changed2)} 行**")
A("")

# --- 2 判定が変わった行
A("## 2. 判定が変わった行（本契約の主たる成果）")
A("")
A("| id | 結論 | 指標 | 効果量 Δ | 符号 | R0 | R1 | R2 | R3 |")
A("|---|---|---|---:|---:|---|---|---|---|")
seen = {r["id"] + r["metric"] for r in changed} | {r["id"] + r["metric"] for r in changed2}
for r in rows:
    if r["id"] + r["metric"] not in seen:
        continue
    e = r["effect"]
    A(f"| {r['id']} | {r['note']} | {r['metric_label']} | {e['mean']:+.4f} | "
      f"{e['n_pos']}/{e['n']} | {mark(r,'R0')} | {mark(r,'R1')} | {mark(r,'R2')} | {mark(r,'R3')} |")
A("")

# --- 3 全行
A("## 3. すべての結論に同じ則を当てた結果")
A("")
A("**効果量と符号の個数は判定と別の列にある。** 判定は則に依存するが、この 2 つは依存しない。")
A("")
A("| id | 種別 | 節 | 結論 | 指標 | Δ | 符号 | R0 統計量 | R1 統計量 | R2 区間 | R3 p | R0 | R1 | R2 | R3 | 変化 |")
A("|---|---|---|---|---|---:|---:|---:|---:|---|---:|---|---|---|---|---|")
for r in rows:
    e = r["effect"]
    ch = "変わった" if (r["R0"]["detect"] != r["R1"]["detect"]) or (r["id"]+r["metric"] in {x["id"]+x["metric"] for x in changed2}) else ""
    A(f"| {r['id']} | {r['kind']} | {r['section']} | {r['note']} | {r['metric_label']} | "
      f"{e['mean']:+.4f} | {e['n_pos']}/{e['n']} | {stat(r,'R0')} | {stat(r,'R1')} | "
      f"{stat(r,'R2')} | {stat(r,'R3')} | {mark(r,'R0')} | {mark(r,'R1')} | {mark(r,'R2')} | {mark(r,'R3')} | {ch} |")
A("")

# --- 4 再判定できなかったもの
A("## 4. 再判定できなかったもの")
A("")
if missing:
    A("| id | 台本 | 理由 |")
    A("|---|---|---|")
    for cid, script, why in missing:
        A(f"| {cid} | {script} | {why} |")
else:
    A("なし。")
A("")
A("**推定で埋めた行は無い。** 測れなかったものは測れなかったと書いた。")
A("")

# --- 5 対照
A("## 5. 対照が両方向で働いていることの実測")
A("")
for c in ctrl.get("positive", []):
    A(f"- 陽性対照 {c['id']} {c['metric']}: そのまま `{c['as_is']}` / 差を零へ潰すと `{c['zeroed']}`")
for c in ctrl.get("negative", []):
    A(f"- 陰性対照 {c['id']} {c['metric']} 定数倍 x{c['scale']}: そのまま `{c['as_is']}` / 定数倍後 `{c['scaled']}`"
      "（定数倍は分子と分母を同じ倍率で変えるため t 型では不変。これ自体が予期された振る舞いである）")
for c in ctrl.get("negative_shift", []):
    A(f"- 陰性対照 {c['id']} {c['metric']} 平行移動で検出へ反転する量: `{c['flip_at']}`")
A("")
(D / "REPORT.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"REPORT.md 生成 {len(out)} 行")

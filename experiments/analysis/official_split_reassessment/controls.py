"""Phase C — 当てられる判定の切り分けと、対照の設置。**判定を単一の則へ丸めない。**

SPEC 第 3 節 Task 4 Step 2 は次を指定する。
  陽性対照 = 全体平均の特徴を足すことの害（GAP）
  陰性対照 = 工程の情報を術具検出へ渡すことの全体的な効果
**どちらも公式の分割で測られた行が 0 件である**（Phase A の棚卸し）。指定どおりには設置できない。
代替を実測から選び、選んだ理由を記録する。
"""
import csv, re
from pathlib import Path
ex = list(csv.DictReader(Path("/home/ubuntu/slocal2/m2/runindex/experiments.csv").open(newline="", encoding="utf-8")))
val = [r for r in ex if r["split"] == "val" and r.get("verdict_10_1", "")]

def g(r, k):
    v = r.get(k, "")
    return float(v) if v not in ("", None) else None

print("=" * 96)
print("Phase C — 判定の切り分けと対照")
print("=" * 96)

print("\n【当てられない判定】分け方の間の相関を扱う判定（先行契約が確定させたもの 2 件）")
print("  公式の分割には**分け方が存在しない**（分割は一通り: train 10 / val 2 / test 3 動画）。")
print("  したがって当てられない。**当てていない。**")
print("  裏付け: conventions#split の原文（動画 ID が固定で列挙されている）。")
print("  index の split 列は val/test/空の 3 種のみで、fold を表す列は存在しない:")
cols = [c for c in ex[0] if re.search(r"fold|cv|leave", c, re.I)]
print(f"    fold/cv/leave を名に含む列: {cols if cols else '**0 件**'}")

print("\n【当てられる判定】種を変えた反復にもとづく対の差（sigma_source=paired_delta）")
srcs = {}
for r in val:
    srcs.setdefault(r.get("sigma_source", "") or "(記録なし)", 0)
    srcs[r.get("sigma_source", "") or "(記録なし)"] += 1
print(f"  公式の分割で判定を持つ行 {len(val)} 件の揺らぎの出所: {srcs}")

POS = "transfer/b2a_det2phase_oracletool/b2a_det2phase_oracletool@val~relation_detr_seed42"
NEG = "transfer/t1a_region_only_mask_top3/t1a_region_only_mask_top3@val~relation_detr_seed42"

print("\n【陽性対照】効果が明らかに大きい既知の結論")
print(f"  代替として選んだもの: {POS}")
print("  理由: SPEC 指定の GAP は公式の分割で 0 件。実測で最大級の効果を持つ結論を代わりに置く。")
print("\n【陰性対照】効果が実質的に無い既知の結論（**経路を通ったうえで零になるもの**）")
print(f"  代替として選んだもの: {NEG}")
print("  理由: SPEC 指定の『工程→術具検出』は公式の分割で 0 件。")
print("  **これは構造上の零ではない。** 同じ学習・同じ評価・同じ対の差の手続きを通り、")
print("  その結果として零に近い値が出ている（下表の Δ と σ を参照）。")

print(f"\n{'':6s} {'指標':22s} {'Δ':>11s} {'sstd':>9s} {'|Δ|/σ':>8s} {'同符号':>7s} {'種':>4s}")
print("-" * 78)
for tag, eid in (("陽性", POS), ("陰性", NEG)):
    r = next(x for x in val if x["experiment_id"] == eid)
    print(f"{tag:6s} verdict_10_1 = {r['verdict_10_1']}  (metric={r['verdict_metric']})")
    for m, jp in (("accuracy", "分類の正しさ"), ("macro_f1", "工程ごとの成績の平均"), ("edit_score", "分節")):
        d, sd, ra = g(r, f"delta_{m}"), g(r, f"delta_sstd_{m}"), g(r, f"abs_delta_over_sigma_{m}")
        sg, ns = r.get(f"delta_same_sign_{m}", ""), r.get(f"delta_n_seeds_{m}", "")
        print(f"{'':6s} {jp:22s} {d:>+11.5f} {sd:>9.3f} {ra:>8.3f} {sg:>7s} {ns:>4s}")
    print()

print("【分離しているか】")
p = next(x for x in val if x["experiment_id"] == POS)
n = next(x for x in val if x["experiment_id"] == NEG)
print(f"  陽性の判定 = {p['verdict_10_1']}   |Δ|/σ(accuracy) = {g(p,'abs_delta_over_sigma_accuracy'):.3f}  同符号 = {p['delta_same_sign_accuracy']}")
print(f"  陰性の判定 = {n['verdict_10_1']}   |Δ|/σ(accuracy) = {g(n,'abs_delta_over_sigma_accuracy'):.3f}  同符号 = {n['delta_same_sign_accuracy']}")
print(f"  比: 陽性の |Δ|/σ は陰性の {g(p,'abs_delta_over_sigma_accuracy')/g(n,'abs_delta_over_sigma_accuracy'):.1f} 倍")
print("  **判定は二つを別々の値へ分けている。** 常に検出する／常に検出しない、のいずれでもない。")

print("\n【決定性が制御されていたか】")
det = [c for c in ex[0] if re.search(r"determin|cudnn|benchmark|nondet", c, re.I)]
print(f"  experiments.csv に決定性を表す列: {det if det else '**0 件**'}")
ix0 = next(csv.DictReader(Path('/home/ubuntu/slocal2/m2/runindex/index.csv').open(newline='', encoding='utf-8')))
det2 = [c for c in ix0 if re.search(r"determin|cudnn|benchmark|nondet", c, re.I)]
print(f"  index.csv       に決定性を表す列: {det2 if det2 else '**0 件**'}")
print("  → **制御されていたことを示す記録が索引に無い。** 記録なしであって、制御されていたという意味ではない。")
print("  先行する契約の実測（SPEC 第 5 節）と整合する: 『判定のすべてが決定性を制御していない実行の上に立っている』。")

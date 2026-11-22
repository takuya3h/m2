"""Task D: 記録から REPORT.md と機械可読のファイルを作る（非公式 T-2026-11-22-dtower-class-error-breakdown）。

    .venv/bin/python .../make_report.py

読むもの: start/a_start.json、b/b_repro.json、b/eval_*.json、c/decomp_*.json、c/fix_*.json、c/tables.json と対照の記録。
書くもの: REPORT.md、summary.json（RESULT の「実測」の値）、csv/*.csv（utf-8-sig）。値は記録から写すだけで、手で書かない。
解釈・順位・採否は書かない。
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

OUTDIR = C.OUT
GT_CATS = ["correct", "confusion", "localization", "missed"]
GT_JA = {"correct": "正解", "confusion": "取り違え", "localization": "位置のずれ", "missed": "見落とし"}
PRED_CATS = ["hit", "duplicate", "confusion", "localization", "background", "other"]
PRED_JA = {"hit": "当たり", "duplicate": "重複", "confusion": "取り違え", "localization": "位置のずれ",
           "background": "背景", "other": "その他"}
FIX_JA = {"a": "(a) 重複を除く", "b": "(b) クラスを直す", "c": "(c) 枠を直す", "d": "(d) 在否を直す",
          "e": "(e) 工程で在り得ないクラスを除く"}
GROUP_JA = {"all": "全クラス", "signature": "signature class", "negative": "negative control", "other": "その他"}
TOWER_JA = {"T1": "塔 1", "T2": "塔 2"}
SIX = C.FOCUS + C.COMPARE


def load(p):
    return json.loads((OUTDIR / p).read_text())


def nan(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


def f4(x):
    return "nan" if nan(x) else f"{x:.4f}"


def s4(x):
    return "nan" if nan(x) else f"{x:+.4f}"


def pc(n, d):
    return f"{n} ({100 * n / d:.1f}%)" if d else f"{n} (—)"


def label(key):
    t, f = key.split("_")
    return f"{TOWER_JA[t]} Fold {f}"


def write_csv(name, header, rows):
    path = OUTDIR / "csv" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        w = csv.writer(handle)
        w.writerow(header)
        w.writerows(rows)


def main():
    keys = [f"{t}_{f}" for t, f in C.TARGETS]
    a = load("start/a_start.json")
    b = load("b/b_repro.json")
    dec = {k: load(f"c/decomp_{k}.json") for k in keys}
    fix = {k: load(f"c/fix_{k}.json") for k in keys}
    tab = load("c/tables.json")
    ev = {k: load(f"b/eval_{k}.json") for k in keys}
    names = dec[keys[0]]["class_names"]
    L = []
    w = L.append
    w("# 検出塔のクラス別の誤りの分解と、直した場合の上限の目安（非公式）")
    w("")
    w(f"task_id: `{C.TASK_ID}`。保存済みの val の予測だけを使う記述である。GPU・学習・推論を使っていない。"
      "**解釈・順位・採否は書かない。** 値と、定義から直接言えることだけを置く。")
    w("塔 1 は T-2026-11-07-dtower-rerun の 12 番・seed 42（Fold A〜E）、塔 2 は D*-COCO・seed 42（Fold A）。"
      "**二つの塔の値の差を塔の優劣として書かない**（学習設定が違う）。seed は 1 本で、seed の間の揺れは分からない。")
    w("割合には件数を並べる。val の動画は Fold ごとに 2 本である。")
    w("")
    w("定義: SPEC §4。AP の類は予測の全件、分解（§2〜§4）は score 0.05 以上の予測だけ。IoU 0.5 と 0.1。"
      "クラス別 AP は記録と同じ COCOeval（area all、maxDets 100）。val に注釈の無いクラスは nan にし、平均から除く。"
      "注釈の `id: 0` の一つはそのまま使う（記録の値と同じ扱い。pycocotools はこの注釈に一致した検出を誤検出に数える）。")
    w("")
    # §1
    w("## 1. 材料と再現（Task A・B）")
    w("")
    w("| 対象 | 予測の経路 | sha256（先頭 16） | 画像 | 予測 | 再現の差の最大 | 小数第 4 位で一致 | val に注釈の無いクラス |")
    w("|---|---|---|---|---|---|---|---|")
    for r, k in zip(a["inventory"], keys):
        t = b["targets"][k]
        w(f"| {label(k)} | `{r['path']}` | `{r['sha256'][:16]}` | {r['val_images']} | {r['predictions']} | "
          f"{t['max_abs_diff']:.2e} | {t['all_equal_4dp']} | {'、'.join(t['missing_classes']) or 'なし'} |")
    w("")
    w(f"G2: {b['G2_pass']}（差の最大 {b['max_abs_diff_over_all']:.2e}。塔 2 の記録は SPEC §1.1 の 7 桁の表示の値）。"
      f"対照（塔 1 Fold A、画像 id 0 の score の並びを逆にした写し）: 一致 {b['control_score_reversed_in_one_image']['all_equal_4dp']}、"
      f"差の最大 {b['control_score_reversed_in_one_image']['max_abs_diff']:.4f}。")
    w("")
    # §2 GT side
    w("## 2. GT の側の分解（SPEC §4.2）")
    w("")
    w("位置のずれと見落としは二つの読みで同じである。読み 1 は IoU が最大の予測（同じ IoU なら score が最大）、"
      "読み 2 は IoU 0.5 以上に同じクラスの予測が一つでもあれば正解。")
    w("")
    rows_csv = []
    for k in keys:
        d = dec[k]
        w(f"### {label(k)}（GT {d['n_gt']}、score 0.05 以上の予測 {d['n_pred_ge_0.05']}）")
        w("")
        w("| クラス | GT | 読み 1 正解 | 読み 1 取り違え | 読み 2 正解 | 読み 2 取り違え | 位置のずれ | 見落とし |")
        w("|---|---|---|---|---|---|---|---|")
        for c in names + ["(計)"]:
            if c == "(計)":
                n = d["n_gt"]
                r1, r2 = d["totals"]["r1"], d["totals"]["r2"]
            else:
                x = d["classes"][c]
                n, r1, r2 = x["n_gt"], x["r1"], x["r2"]
                rows_csv.append([k, c, n, *[r1[g] for g in GT_CATS], *[r2[g] for g in GT_CATS],
                                 *[x["r1_ties"][t] for t in ("max_iou_gt0", "max_iou_ge0.5", "max_iou_ge0.5_classes_differ",
                                                             "score_also_tied")]])
            if n == 0:
                w(f"| {c} | 0 | — | — | — | — | — | — |")
                continue
            w(f"| {c} | {n} | {pc(r1['correct'], n)} | {pc(r1['confusion'], n)} | {pc(r2['correct'], n)} | "
              f"{pc(r2['confusion'], n)} | {pc(r1['localization'], n)} | {pc(r1['missed'], n)} |")
        w("")
    write_csv("gt_decomposition.csv", ["target", "class", "n_gt", *[f"r1_{g}" for g in GT_CATS], *[f"r2_{g}" for g in GT_CATS],
                                        "r1_tie_maxiou_gt0", "r1_tie_maxiou_ge05", "r1_tie_ge05_classes_differ",
                                        "r1_tie_score_also_tied"], rows_csv)
    # ties
    w("### 読み 1 で IoU が同じ予測が複数あった GT の数")
    w("")
    w("列は、最大の IoU が 0 より大きい GT のうち同じ最大の IoU の予測が 2 つ以上あった数 / そのうち最大の IoU が 0.5 以上 / "
      "さらにその予測のクラスが一つでない / さらに score も同じで保存の並びで決めた数。")
    w("")
    w("| クラス | " + " | ".join(label(k) for k in keys) + " |")
    w("|---|" + "---|" * len(keys))
    for c in names:
        cells = []
        for k in keys:
            t = dec[k]["classes"][c]["r1_ties"]
            cells.append(f"{t['max_iou_gt0']} / {t['max_iou_ge0.5']} / {t['max_iou_ge0.5_classes_differ']} / {t['score_also_tied']}")
        w(f"| {c} | " + " | ".join(cells) + " |")
    tot = {k: [sum(dec[k]["classes"][c]["r1_ties"][t] for c in names) for t in
               ("max_iou_gt0", "max_iou_ge0.5", "max_iou_ge0.5_classes_differ", "score_also_tied")] for k in keys}
    w("| (計) | " + " | ".join(" / ".join(str(v) for v in tot[k]) for k in keys) + " |")
    w("")
    # §3 confusion partners
    w("## 3. 取り違えの相手（SPEC §4.3）")
    w("")
    w("GT のクラスごとに、取り違えの相手の上位 3 つ（件数と、その GT のクラスの取り違えの件数に占める割合）。全件の表は "
      "`csv/confusion_matrix.csv`。")
    w("")
    conf_rows = []
    for k in keys:
        d = dec[k]
        w(f"### {label(k)}")
        w("")
        w("| GT のクラス | 読み 1 取り違え | 読み 1 の相手の上位 | 読み 2 取り違え | 読み 2 の相手の上位 |")
        w("|---|---|---|---|---|")
        for c in names:
            cells = []
            for r in ("r1", "r2"):
                tops = d["top_partners"][r][c]
                cells.append(str(d["classes"][c][r]["confusion"]))
                cells.append("、".join(f"{t['class']} {t['count']} ({100 * t['share']:.1f}%)" for t in tops[:3]) or "—")
            w(f"| {c} | " + " | ".join(cells) + " |")
        w("")
        for r in ("r1", "r2"):
            for i, c in enumerate(names):
                for j, cc in enumerate(names):
                    if d["confusion"][r][i][j]:
                        conf_rows.append([k, r, c, cc, d["confusion"][r][i][j]])
    write_csv("confusion_matrix.csv", ["target", "reading", "gt_class", "pred_class", "count"], conf_rows)
    # §4 pred side
    w("## 4. 予測の側の分解（SPEC §4.4）")
    w("")
    w("score 0.05 以上の予測を、当たり → 重複 → 取り違え → 位置のずれ → 背景 → その他 の順で最初に当たった区分に入れる。"
      "下の表は件数（そのクラスの予測に占める割合）。score の中央値と取り違えの相手の GT のクラスは `csv/pred_decomposition.csv`。")
    w("")
    pred_rows = []
    for k in keys:
        d = dec[k]
        w(f"### {label(k)}")
        w("")
        w("| クラス | 予測 | " + " | ".join(PRED_JA[g] for g in PRED_CATS) + " | 取り違えの相手の GT の上位 |")
        w("|---|---|" + "---|" * len(PRED_CATS) + "---|")
        for c in names:
            x = d["classes"][c]
            n = x["n_pred"]
            part = sorted(x["pred_confusion_partner"].items(), key=lambda kv: -kv[1])
            w(f"| {c} | {n} | " + " | ".join(pc(x["pred"][g], n) for g in PRED_CATS) + " | "
              + ("、".join(f"{p} {v}" for p, v in part[:3]) or "—") + " |")
            pred_rows.append([k, c, n, *[x["pred"][g] for g in PRED_CATS],
                              *[("" if x["pred_median_score"][g] is None else f"{x['pred_median_score'][g]:.6f}") for g in PRED_CATS],
                              json.dumps(x["pred_confusion_partner"], ensure_ascii=False)])
        n = d["n_pred_ge_0.05"]
        w("| (計) | " + str(n) + " | " + " | ".join(pc(d["totals"]["pred"][g], n) for g in PRED_CATS) + " | |")
        w("")
        w("score の中央値（区分ごと）: " + "、".join(
            f"{c} " + "/".join(("—" if d['classes'][c]['pred_median_score'][g] is None else f"{d['classes'][c]['pred_median_score'][g]:.3f}")
                               for g in PRED_CATS) for c in SIX) + "（当たり/重複/取り違え/位置のずれ/背景/その他）")
        w("")
    write_csv("pred_decomposition.csv", ["target", "class", "n_pred", *PRED_CATS, *[f"median_score_{g}" for g in PRED_CATS],
                                          "confusion_partner_gt_class"], pred_rows)
    # §5 AP AP50 AP75
    w("## 5. クラス別の AP・AP50・AP75（SPEC §4.6）")
    w("")
    w("| クラス | " + " | ".join(label(k) for k in keys) + " |")
    w("|---|" + "---|" * len(keys))
    ap_rows = []
    for c in names:
        w(f"| {c} | " + " | ".join(f"{f4(ev[k]['per_class'][c]['AP'])} / {f4(ev[k]['per_class'][c]['AP50'])} / "
                                   f"{f4(ev[k]['per_class'][c]['AP75'])}" for k in keys) + " |")
        for k in keys:
            x = ev[k]["per_class"][c]
            ap_rows.append([k, c, x["AP"], x["AP50"], x["AP75"]])
    for g in ("all", "signature", "negative", "other"):
        w(f"| 平均（{GROUP_JA[g]}） | " + " | ".join(f"{f4(ev[k]['means'][g])} / {f4(ev[k]['means50'][g])} / {f4(ev[k]['means75'][g])}"
                                                   for k in keys) + " |")
    w("")
    w("各欄は AP / AP50 / AP75。AP50 ≥ AP は全対象の全クラスで成り立つ（" + "、".join(
        f"{label(k)} {tab['targets'][k]['AP50_ge_AP_all_classes']}" for k in keys) + "）。")
    w("")
    write_csv("ap_ap50_ap75.csv", ["target", "class", "AP", "AP50", "AP75"], ap_rows)
    # §6 fixes
    w("## 6. 直した場合の上限の目安（SPEC §4.5）")
    w("")
    w("**どれも厳密な上限ではない。** 一つの誤りの型を除くと AP がどれだけ動くかの目安で、直し方は一つずつ別々に当てた。"
      "(b)−(a) と (c)−(a) は、(b)・(c) の後と (a) の後の差。直す前の値は §5 と同じ（Task B と一致: "
      + "、".join(f"{label(k)} {fix[k]['before_equals_taskB']}" for k in keys) + "）。")
    w("")
    fix_rows = []
    for metric in ("AP", "AP50"):
        w(f"### {metric} の差（直した後 − 直す前）")
        w("")
        for k in keys:
            fx = fix[k]
            w(f"#### {label(k)}")
            w("")
            w("| クラス | 直す前 | Δ(a) | Δ(b) | Δ(c) | Δ(d) | Δ(e) | Δ(b)−(a) | Δ(c)−(a) |")
            w("|---|---|---|---|---|---|---|---|---|")
            for c in names:
                cells = [f4(fx["before"]["per_class"][c][metric])]
                for f in ("a", "b", "c", "d", "e", "b_minus_a", "c_minus_a"):
                    v = fx["fixes"].get(f)
                    cells.append(s4(v["per_class"][c][metric]["diff"]) if v and v.get("status", "measured") == "measured"
                                 and "per_class" in v else "UNKNOWN")
                w(f"| {c} | " + " | ".join(cells) + " |")
                if metric == "AP":
                    fix_rows.append([k, c] + [fx["before"]["per_class"][c][m] for m in ("AP", "AP50")] + [
                        (fx["fixes"][f]["per_class"][c][m]["diff"] if "per_class" in fx["fixes"].get(f, {}) else "UNKNOWN")
                        for f in ("a", "b", "c", "d", "e", "b_minus_a", "c_minus_a") for m in ("AP", "AP50")])
            for g in ("all", "signature", "negative", "other"):
                cells = [f4(fx["fixes"]["a"]["means"][metric][g]["before"])]
                for f in ("a", "b", "c", "d", "e", "b_minus_a", "c_minus_a"):
                    v = fx["fixes"].get(f)
                    cells.append(s4(v["means"][metric][g]["diff"]) if v and "means" in v else "UNKNOWN")
                w(f"| 平均（{GROUP_JA[g]}） | " + " | ".join(cells) + " |")
            w("")
    write_csv("fixes.csv", ["target", "class", "AP_before", "AP50_before"] + [
        f"d{m}_{f}" for f in ("a", "b", "c", "d", "e", "b_minus_a", "c_minus_a") for m in ("AP", "AP50")], fix_rows)
    w("### 直し方で動いた予測の数")
    w("")
    w("| 対象 | 予測 | (a) 除いた | (b) 書き換えた / 除いた | (c) 置き換えた / 除いた | (d) 除いた | (e) 除いた | 最大 IoU の GT が同値で二つ以上 |")
    w("|---|---|---|---|---|---|---|---|")
    for k in keys:
        i = fix[k]["info"]
        w(f"| {label(k)} | {i['preds']} | {i['a_removed']} | {i['b_relabelled']} / {i['b_removed_after_relabel']} | "
          f"{i['c_boxes_replaced']} / {i['c_removed_after_replace']} | {i['d_removed']} | {i.get('e_removed', 'UNKNOWN')} | "
          f"{i['gt_ties_ge0.5']} |")
    w("")
    w("### (e) で除いた組と工程の正解")
    w("")
    w("工程の正解は `data/processed/phase_manifest`（前回の予備測定の正解の腕と同じ出所）。Fold ごとにその Fold の train と val の"
      "動画の項目だけを使った（利用者の判断 2026-11-22。Fold B〜E は公式の test の動画 04・05・07 の項目を含む test.json を開いた。"
      "各 Fold の test の動画の項目は使っていない）。")
    w("")
    w("| Fold | 開いたマニフェスト | 使わなかった動画（フレーム数） | train の画像（工程なし） | val の画像（工程あり） | train に現れない工程 | 除いた組の数 |")
    w("|---|---|---|---|---|---|---|")
    seen = set()
    for k in keys:
        f = k.split("_")[1]
        if f in seen:
            continue
        seen.add(f)
        p = fix[k]["phase"]
        if "removed_pairs" not in p:
            w(f"| {f} | UNKNOWN | | | | | UNKNOWN（{p.get('reason')}） |")
            continue
        sk = "、".join(f"{v} ({n})" for v, n in sorted(p["videos_skipped_frames"].items())) or "なし"
        w(f"| {f} | {'・'.join(x + '.json' for x in p['files'])} | {sk} | {p['train_images']} ({p['train_images_without_phase']}) | "
          f"{p['val_images']} ({p['val_images_with_phase']}) | {'、'.join(p['phases_not_in_train']) or 'なし'} | {len(p['removed_pairs'])} |")
    w("")
    pair_rows = []
    for f in sorted(seen):
        k = [x for x in keys if x.endswith(f"_{f}")][0]
        p = fix[k]["phase"]
        if "removed_pairs" in p:
            by_phase = {}
            for ph, c in p["removed_pairs"]:
                by_phase.setdefault(ph, []).append(c)
                pair_rows.append([f, ph, c])
            w(f"- Fold {f}: " + "；".join(f"{ph}（val {p['val_images_by_phase'].get(ph, 0)} 枚）: {'、'.join(cs)}"
                                         for ph, cs in by_phase.items()))
            inr = p.get("val_gt_boxes_in_removed_pairs", {})
            w("  - 除いた組に当たる val の GT の box（その工程の val の画像にそのクラスの GT が在るもの）: "
              + ("、".join(f"{c} {n}" for c, n in sorted(inr.items(), key=lambda kv: -kv[1])) or "0 件"))
    w("")
    write_csv("phase_removed_pairs.csv", ["fold", "phase", "class"], pair_rows)
    # §7 fold table
    w("## 7. Fold・動画ごとの表（SPEC §4.6）")
    w("")
    w("box と動画の数は注釈ファイルの数え上げ（pycocotools の索引の数え上げと一致: " + "、".join(
        f"Fold {f} {x['counts_match_index']}" for f, x in tab["folds"].items()) + "）。動画の集合は正本の表と conventions#folds の"
      "表に一致（" + "、".join(f"Fold {f} {x['train_videos_match_fold_table'] and x['val_videos_match_fold_table']}"
                             for f, x in tab["folds"].items()) + "）。AP・AP50 は塔 1。")
    w("")
    fold_rows = []
    w("| クラス | " + " | ".join(f"Fold {f} train box / 動画" for f in "ABCDE") + " |")
    w("|---|" + "---|" * 5)
    for c in names:
        w(f"| {c} | " + " | ".join(f"{tab['folds'][f]['train']['boxes'][c]} / {tab['folds'][f]['train']['videos'][c]}"
                                   for f in "ABCDE") + " |")
    w("")
    w("| クラス | " + " | ".join(f"Fold {f} val box / 動画 / AP / AP50" for f in "ABCDE") + " |")
    w("|---|" + "---|" * 5)
    for c in names:
        cells = []
        for f in "ABCDE":
            x = tab["folds"][f]
            e = ev[f"T1_{f}"]["per_class"][c]
            cells.append(f"{x['val']['boxes'][c]} / {x['val']['videos'][c]} / {f4(e['AP'])} / {f4(e['AP50'])}")
            fold_rows.append([f, c, x["train"]["boxes"][c], x["train"]["videos"][c], x["val"]["boxes"][c], x["val"]["videos"][c],
                              e["AP"], e["AP50"], ev["T2_A"]["per_class"][c]["AP"] if f == "A" else "",
                              ev["T2_A"]["per_class"][c]["AP50"] if f == "A" else ""])
        w(f"| {c} | " + " | ".join(cells) + " |")
    w("")
    write_csv("fold_table.csv", ["fold", "class", "train_boxes", "train_videos", "val_boxes", "val_videos", "T1_AP", "T1_AP50",
                                 "T2_AP", "T2_AP50"], fold_rows)
    w("### 動画ごとのクラス別 AP")
    w("")
    w("塔 1 は記録（eval_val.per_video.json）と計算し直した値の差の最大が " + "、".join(
        f"{label(k)} {tab['targets'][k]['per_video_vs_record']['max_abs_diff']:.1e}（{tab['targets'][k]['per_video_vs_record']['values_compared']} 値）"
        for k in keys) + "。塔 2 は pd_plain.json の動画ごとの mAP と比べた。動画に注釈の無いクラスは nan。")
    w("")
    vid_rows = []
    cols = [(k, v) for k in keys for v in sorted(tab["targets"][k]["per_video"])]
    w("| クラス | " + " | ".join(f"{label(k)} 動画 {v}" for k, v in cols) + " |")
    w("|---|" + "---|" * len(cols))
    for c in names + ["(mAP)"]:
        cells = []
        for k, v in cols:
            x = tab["targets"][k]["per_video"][v]
            val = x["AP"] if c == "(mAP)" else x["per_class"][c]["AP"]
            cells.append(f4(val))
            if c != "(mAP)":
                vid_rows.append([k, v, c, x["per_class"][c]["AP"], x["per_class"][c]["AP50"]])
        w(f"| {c} | " + " | ".join(cells) + " |")
    w("")
    write_csv("per_video_ap.csv", ["target", "video", "class", "AP", "AP50"], vid_rows)
    (OUTDIR / "REPORT.md").write_text("\n".join(L) + "\n")
    # summary for RESULT
    summ = {"task_id": C.TASK_ID, "targets": keys, "focus": SIX, "gt": {}, "pred": {}, "ap": {}, "fix": {}, "fix_means": {},
            "ties_total": tot, "partners": {}}
    for k in keys:
        d = dec[k]
        summ["gt"][k] = {c: {"n": d["classes"][c]["n_gt"], "r1": d["classes"][c]["r1"], "r2": d["classes"][c]["r2"]} for c in SIX}
        summ["partners"][k] = {c: {r: d["top_partners"][r][c][:2] for r in ("r1", "r2")} for c in SIX}
        summ["pred"][k] = {c: {"n": d["classes"][c]["n_pred"], **d["classes"][c]["pred"]} for c in SIX}
        summ["ap"][k] = {c: ev[k]["per_class"][c] for c in SIX}
        summ["fix"][k] = {c: {f: (fix[k]["fixes"][f]["per_class"][c]["AP"]["diff"] if "per_class" in fix[k]["fixes"].get(f, {})
                                  else None) for f in ("a", "b", "c", "d", "e")} for c in SIX}
        summ["fix_means"][k] = {g: {f: (fix[k]["fixes"][f]["means"]["AP"][g]["diff"] if "means" in fix[k]["fixes"].get(f, {})
                                        else None) for f in ("a", "b", "c", "d", "e")} for g in ("all", "signature", "negative", "other")}
    C.write_json(OUTDIR / "summary.json", summ)
    print("REPORT.md lines", len(L))


if __name__ == "__main__":
    main()

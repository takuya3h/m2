"""REPORT.md と diffs.csv を記録から作る（非公式 T-2026-11-21-grasp-hand-graph-t2p-match、Task E、SPEC §7・§10）。値は手で写さない。

    python3 experiments/analysis/grasp_hand_graph_t2p/tools/make_report.py --summary <T>/e/summary.json --checks-dir <T> \
        --out experiments/analysis/grasp_hand_graph_t2p/REPORT.md --csv experiments/analysis/grasp_hand_graph_t2p/diffs.csv
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

SCOPES = ("W1", "W2", "W3")
SETS = ("s1", "s2", "s3", "s4")
SETN = {"s1": "N10 L1", "s2": "N10 L2", "s3": "N30 L1", "s4": "N30 L2"}
EPOCHS = (4, 8, 12, 16)
TP_TYPES = ("D1-L1", "D1-L2", "D2", "D3-L2")


def f(x, nd=4):
    return "—" if x is None else f"{x:+.{nd}f}"


def v(x, nd=4):
    return "—" if x is None else f"{x:.{nd}f}"


def mark(d):
    return f"{f(d['six'])}{'' if d['readable'] else '（読めない）'}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--checks-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv", required=True)
    a = ap.parse_args()
    S = json.loads(Path(a.summary).read_text())
    T = Path(a.checks_dir)
    J = {k: json.loads((T / p).read_text()) for k, p in {
        "b": "b/b_check.json", "graphs": "c/graphs_report.json", "repro": "c/repro_compare.json", "ident": "c/identity_summary.json",
        "ep4": "d/ep4_compare.json", "omit": "d/omitted_compare.json", "optim": "d/optim_check.json"}.items()}
    runs, diffs, band = S["runs"], S["diffs"], S["band"]
    L = []
    w = L.append
    w("# REPORT — 術具と手のグラフを T→P と同じ条件で回し直す（非公式 T-2026-11-21-grasp-hand-graph-t2p-match）")
    w("")
    w("非公式の予備測定。関門と設計の判断（案の採否を含む）には使わない。差を並べるだけで、採否と順位は書かない。")
    w("andrew、Fold A（train 10 本・val 09・10）、seed 42、RTX A6000 × 2。主は 4 epoch 目、副次は同じ run を続けた 8・12・16 epoch 目（最良の回を選ばない）。")
    w(f"6 工程 = val に現れる 7 工程（{'・'.join(S['present_phases'])}）から dressing を除いた平均の Jaccard。7 工程 = PhaseEvaluator の phase_jaccard。"
      f"差の幅 ±{band} の中は「読めない」と書き、符号で解釈しない。同じ W・同じ設定・同じ epoch の中だけで比べる。")
    w("全部の差（工程別・動画ごとを含む）は `diffs.csv`（UTF-8 BOM 付き）。値は各 run の `metrics_ep<E>.json` と `predictions/val_probs_ep<E>.npz` から道具で作った。")
    w("")
    # 確かめ
    w("## 1. 確かめ")
    w("")
    b, g = J["b"]["summary"], J["graphs"]["parts"]
    e = S["end_check"]
    w("| 項目 | 結果 |")
    w("|---|---|")
    w(f"| 材料の照合（前回のグラフの目録 26 件、T→P の信号と入れ替え 12 件、T→P の run 36 本の入力） | {b['graph_manifest_ok']}・{b['tp_shuffle_ok']}・{b['tp_runs_files_ok']}（1 バイト変えた写しは 3 つとも食い違い {b['controls_detect']}） |")
    w(f"| 塔単独の val | J {S['tower_alone']['phase_jaccard']}・frame accuracy {S['tower_alone']['phase_accuracy']}・6 工程 {S['tower_alone']['six_phase_mean']:.6f}（記録と一致 {S['tower_alone']['equals_record']}） |")
    w(f"| T→P の学習設定の食い違い（W ごと、4 型） | {b['tp_settings_disagree']} |")
    w(f"| グラフの組み直しと前回の一致（CF 5 腕と DGH-noCF） | train {all(x.get('bit_equal', True) for x in g['train']['equals_previous'].values())}・val {all(x.get('bit_equal', True) for x in g['val']['equals_previous'].values())} |")
    w(f"| 表と出どころの外れ（train・val） | 表 {g['train']['table_check']['violations']}・{g['val']['table_check']['violations']}、noCF {g['train']['provenance_noCF']['violations']}・{g['val']['provenance_noCF']['violations']}、CF {g['train']['provenance_CF']['violations']}・{g['val']['provenance_CF']['violations']}（対照: 表と違う腕 {g['train']['table_check_control_wrong_arm']['violations']}、CF を混ぜた写し {g['train']['provenance_noCF_control_cf_mixed']['violations']}） |")
    sh_t, sh_v = g["train"]["shuffle"], g["val"]["shuffle"]
    w(f"| 入れ替え（T→P の対応表をそのまま使用） | 不動点 train {sh_t['fixed_point_fraction']:.5f}・val {sh_v['fixed_point_fraction']:.5f}、同じ動画から train {sh_t['same_video_fraction']:.5f}・val {sh_v['same_video_fraction']:.5f}、"
      f"値の集合が元と同じ {all(x['value_set_equal'] for x in sh_t['per_arm'].values()) and all(x['value_set_equal'] for x in sh_v['per_arm'].values())}（恒等の並べ替えの対照で不動点 {g['train']['shuffle_control_identity']['fixed_point_fraction']}） |")
    idn = J["ident"]
    w(f"| 恒等性（240 組） | 塔単独との差の最大 {idn['identity_max']}、陽性対照で変わる {idn['n_ok']}/{idn['n']}（変わらない 9 組は D1・D3 の空の腕で構造上。audit C-4） |")
    rp = J["repro"]
    w(f"| 既定の挙動（前回のグラフ 1 本・T→P 1 本の回し直し） | 記録と一致 {rp['graph']['all_equal']}・{rp['tp']['all_equal']}（1e-6 ずらした写しで不一致 {not rp['controls']['probs_one_value_shifted_1e-6']['equal']}） |")
    w(f"| 4 epoch で止めた run と続けた run の 4 epoch 目（W ごとに 2 本） | 一致 {J['ep4']['all_equal']}（4 と 8 epoch 目の確率で差が出る {J['ep4']['controls_detect']}） |")
    w(f"| 省いた run の確かめ（W ごとに A0 s4・D-noCF s2） | 一致 {J['omit']['checks_all_equal']}（D-noCF と DG-noCF で差が出る {J['omit']['controls_detect']}） |")
    w(f"| optimizer の群ごとの学習率と weight decay | 写した値と一致 {J['optim']['n_ok']}/{J['optim']['n']} |")
    w(f"| 確率からの測り直し（{S['recompute_n']} 組） | 記録とのずれの最大 {S['recompute_max_dev']}、1e-6 ずらした写しを検出 {S['recompute_control_all_detected']} |")
    w(f"| 終わり | {e['found']}/{e['expected']} 本、記録がそろう {e['complete']} 本、存在しない名前 {e['nonexistent_name_hits']} 件・在る名前 {e['known_name_hits']} 件 |")
    w(f"| test の動画 | run の動画 {S['videos_in_runs']['videos']}、{{04, 05, 07}} との共通 {S['videos_in_runs']['test_overlap']}（04 を混ぜた対照 {S['videos_control_04']['test_overlap']}） |")
    w("")
    # 主の表: 腕の値
    def val_of(sc, s, arm, ep):
        k = S["table_source"].get(f"{sc}|{s}|{arm}")
        if not k:
            return None
        key = next(kk for kk in runs if kk.startswith("GR|") and runs[kk]["run"] == k["run"])
        return runs[key]["epochs"][str(ep)] if str(ep) in runs[key]["epochs"] else runs[key]["epochs"][ep]
    arms = ["A0"] + [f"{c}-{s}" for c in ("D", "DG", "DH", "DGH", "DGH-U") for s in ("noCF", "CF", "S")] + ["DGH-GT"]
    for ep in EPOCHS:
        w(f"## {'2.' if ep == 4 else '5.' + str(EPOCHS.index(ep))} 腕の値（{ep} epoch 目{'、主' if ep == 4 else '、副次'}）— 6 工程 / frame accuracy / 7 工程")
        w("")
        for sc in SCOPES:
            w(f"**{sc}**（省いた run は出所の設定の値。A0 は s1、辺の無い腕は s2 ← s1・s4 ← s3）")
            w("")
            w("| 腕 | " + " | ".join(f"{s}（{SETN[s]}）" for s in SETS) + " |")
            w("|---|" + "---|" * len(SETS))
            for arm in arms:
                cells = []
                for s in SETS:
                    r = val_of(sc, s, arm, ep)
                    cells.append("—" if r is None else f"{v(r['six'])} / {v(r['acc'])} / {v(r['j7'])}")
                w(f"| {arm} | " + " | ".join(cells) + " |")
            w("")
            w("| T→P | 空 | 予測-noCF | 入れ替え |")
            w("|---|---|---|---|")
            for t in TP_TYPES:
                cells = []
                for arm in ("empty", "pred_noCF", "shuffle"):
                    r = runs.get(f"TP|{sc}|{t}|{arm}")
                    r = None if r is None else r["epochs"].get(str(ep), r["epochs"].get(ep))
                    cells.append("—" if r is None else f"{v(r['six'])} / {v(r['acc'])} / {v(r['j7'])}")
                w(f"| {t} | " + " | ".join(cells) + " |")
            w("")
        if ep == 4:
            # 主の差の表
            w("## 3. 差（4 epoch 目、主）— 6 工程 / frame accuracy / 7 工程")
            w("")
            for sc in SCOPES:
                w(f"**{sc}**")
                w("")
                w("| 差 | 読むこと | " + " | ".join(SETS) + " |")
                w("|---|---|" + "---|" * len(SETS))
                seen = []
                for d in diffs:
                    if d["group"] == "graph" and d["scope"] == sc and d["epoch"] == 4 and (d["arm1"], d["arm2"]) not in seen:
                        seen.append((d["arm1"], d["arm2"]))
                for a1, a2 in seen:
                    rows = {d["setting"]: d for d in diffs if d["group"] == "graph" and d["scope"] == sc and d["epoch"] == 4
                            and d["arm1"] == a1 and d["arm2"] == a2}
                    reads = next(iter(rows.values()))["reads"]
                    w(f"| {a1} − {a2} | {reads} | " + " | ".join(
                        "—" if s not in rows else f"{mark(rows[s])} / {f(rows[s]['acc'])} / {f(rows[s]['j7'])}" for s in SETS) + " |")
                w("")
                w("| T→P | 予測-noCF − 入れ替え | 予測-noCF − 空 |")
                w("|---|---|---|")
                for t in TP_TYPES:
                    cells = []
                    for a2 in ("shuffle", "empty"):
                        d = next((x for x in diffs if x["group"] == "tp" and x["scope"] == sc and x["epoch"] == 4 and x["type"] == t and x["arm2"] == a2), None)
                        cells.append("—" if d is None else f"{mark(d)} / {f(d['acc'])} / {f(d['j7'])}")
                    w(f"| {t} | " + " | ".join(cells) + " |")
                w("")
            # 主の差の工程別・動画ごと（4 epoch 目、c-noCF − c-S と T→P の予測-noCF − 入れ替え、s1）
            w("### 3.1 主の差の工程別と動画ごと（4 epoch 目。グラフは s1〜s4、T→P は型ごと）")
            w("")
            ph = S["present_phases"]
            w("| W | 設定 | 差 | " + " | ".join(ph) + " | 09 の 6 工程 | 10 の 6 工程 | 09 の acc | 10 の acc |")
            w("|---|---|---|" + "---|" * (len(ph) + 4))
            for sc in SCOPES:
                for d in diffs:
                    if d["epoch"] != 4 or d["scope"] != sc:
                        continue
                    is_main = (d["group"] == "graph" and d["arm2"] == d["arm1"].replace("-noCF", "-S") and d["arm1"].endswith("-noCF")) or \
                              (d["group"] == "tp" and d["arm2"] == "shuffle")
                    if not is_main:
                        continue
                    lab = d.get("setting", d.get("type"))
                    w(f"| {sc} | {lab} | {d['arm1']} − {d['arm2']} | " + " | ".join(f(d["per_phase"][p]) for p in ph) + " | "
                      + " | ".join(f(d["per_video"][vv]["six"]) for vv in ("09", "10")) + " | "
                      + " | ".join(f(d["per_video"][vv]["acc"]) for vv in ("09", "10")) + " |")
            w("")
            # W1 の塔単独との差
            w("### 3.2 W1 の塔単独との差（4 epoch 目）— 6 工程 / frame accuracy / 7 工程")
            w("")
            w("| 腕 | " + " | ".join(SETS) + " |")
            w("|---|" + "---|" * len(SETS))
            for arm in arms:
                rows = {x["setting"]: x for x in S["w1_vs_tower_alone"] if x["group"] == "graph" and x["arm"] == arm and x["epoch"] == 4}
                w(f"| {arm} | " + " | ".join("—" if s not in rows else f"{f(rows[s]['six'])} / {f(rows[s]['acc'])} / {f(rows[s]['j7'])}" for s in SETS) + " |")
            for t in TP_TYPES:
                rows = {x["arm"]: x for x in S["w1_vs_tower_alone"] if x["group"] == "tp" and x["type"] == t and x["epoch"] == 4}
                w(f"| T→P {t}（空 / 予測-noCF / 入れ替え） | " + " | ".join(
                    "—" if aa not in rows else f"{f(rows[aa]['six'])} / {f(rows[aa]['acc'])} / {f(rows[aa]['j7'])}" for aa in ("empty", "pred_noCF", "shuffle")) + " | |")
            w("")
            # 参考の列
            w("## 4. 参考の列")
            w("")
            w("### 4.1 T→P の回し直し（4 epoch 目）と前回の記録（W1 は andrew の stage2fix、W2・W3 は bengio の w23b）— 6 工程 / frame accuracy / 7 工程")
            w("")
            w("| W | 型 | 腕 | 前回の記録 | 前回のホスト | 本契約（4 epoch 目） | 本契約 − 前回 | val の確率が一致 | 確率の差の最大 |")
            w("|---|---|---|---|---|---|---|---|---|")
            for x in S["tp_prev"]:
                pv, nw, dd = x["prev"], x["new_ep4"], x["new_minus_prev"]
                w(f"| {x['scope']} | {x['type']} | {x['arm']} | {v(pv['six'])} / {v(pv['acc'])} / {v(pv['j7'])} | {pv['host']} | "
                  f"{v(nw['six'])} / {v(nw['acc'])} / {v(nw['j7'])} | {f(dd['six'])} / {f(dd['acc'])} / {f(dd['j7'])} | {x['probs_equal']} | {x['probs_max_abs_diff']:.3g} |")
            w("")
            w("### 4.2 前回のグラフ（収束規則、val の最良の回。読み方の規則には使わない）— 6 工程 / frame accuracy / 7 工程（最良の回）")
            w("")
            w("| W | 腕（前回の名前） | " + " | ".join(SETS) + " |")
            w("|---|---|" + "---|" * len(SETS))
            for sc in SCOPES:
                for arm in ("A0", "D-CF", "DG-CF", "DH-CF", "DGH-CF", "DGH-U-CF", "DGH-noCF", "DGH-GT"):
                    rows = {x["setting"]: x for x in S["graph_prev"] if x["scope"] == sc and x["arm"] == arm}
                    w(f"| {sc} | {arm} | " + " | ".join("—" if s not in rows else f"{v(rows[s]['six'])} / {v(rows[s]['acc'])} / {v(rows[s]['j7'])}（{rows[s]['epoch']}）" for s in SETS) + " |")
            w("")
    # 副次の差の表（8・12・16）
    w("## 6. 差（副次 8・12・16 epoch 目）— 6 工程 / frame accuracy / 7 工程")
    w("")
    for ep in (8, 12, 16):
        for sc in SCOPES:
            w(f"**{ep} epoch 目・{sc}**")
            w("")
            w("| 差 | " + " | ".join(SETS) + " |")
            w("|---|" + "---|" * len(SETS))
            seen = []
            for d in diffs:
                if d["group"] == "graph" and d["scope"] == sc and d["epoch"] == ep and (d["arm1"], d["arm2"]) not in seen:
                    seen.append((d["arm1"], d["arm2"]))
            for a1, a2 in seen:
                rows = {d["setting"]: d for d in diffs if d["group"] == "graph" and d["scope"] == sc and d["epoch"] == ep
                        and d["arm1"] == a1 and d["arm2"] == a2}
                w(f"| {a1} − {a2} | " + " | ".join("—" if s not in rows else f"{mark(rows[s])} / {f(rows[s]['acc'])} / {f(rows[s]['j7'])}" for s in SETS) + " |")
            for t in TP_TYPES:
                cells = []
                for a2 in ("shuffle", "empty"):
                    d = next((x for x in diffs if x["group"] == "tp" and x["scope"] == sc and x["epoch"] == ep and x["type"] == t and x["arm2"] == a2), None)
                    cells.append("—" if d is None else f"{mark(d)} / {f(d['acc'])} / {f(d['j7'])}")
                w(f"| T→P {t}: 予測-noCF − 入れ替え / 予測-noCF − 空 | {cells[0]} | {cells[1]} | | |")
            w("")
    # 指標がちょうど同じ・argmax・射影
    w("## 7. 指標がちょうど同じになった差の数、argmax の一致、零初期化の層の大きさ")
    w("")
    w("| W | epoch | グラフの差（同じ / 計） | T→P の差（同じ / 計） | 読めない差 | argmax の一致（最小・中央） |")
    w("|---|---|---|---|---|---|")
    for k, x in S["identical_by_scope_epoch"].items():
        sc, ep = k.split("|")
        w(f"| {sc} | {ep} | {x['graph_identical']} / {x['graph_diffs']} | {x['tp_identical']} / {x['tp_diffs']} | {x['unreadable']} | "
          f"{v(x['argmax_agree_min'])}・{v(x['argmax_agree_median'])} |")
    w("")
    w("| 群 | W | epoch | 本数 | 零初期化の層の重みの L2（最小・中央・最大） |")
    w("|---|---|---|---|---|")
    for k, x in S["iface_last_norms"].items():
        gname, sc, ep = k.split("|")
        w(f"| {'グラフ' if gname == 'GR' else 'T→P'} | {sc} | {ep} | {x['n']} | {x['min']:.4f}・{x['median']:.4f}・{x['max']:.4f} |")
    w("")
    # 予測
    p = S["predictions"]
    w("## 8. 予測（SPEC §7.1）の当たり外れ（4 epoch 目、6 工程）")
    w("")
    w(f"1. DGH-GT − A0 ≥ DGH-noCF − A0（各 W・各設定）: 当たり {sum(x['hit'] for x in p['p1'])}/{len(p['p1'])} — "
      + "、".join(f"{x['scope']} {x['setting']} {f(x['gt_minus_a0'])} vs {f(x['dgh_minus_a0'])}" for x in p["p1"]))
    w(f"2. W1 の D-noCF − D-S が ±{band} の中（s1・s3）: 当たり {sum(x['hit'] for x in p['p2'])}/{len(p['p2'])} — "
      + "、".join(f"{x['setting']} {f(x['six'])}" for x in p["p2"]))
    if p["p3"]:
        w(f"3. W2 のグラフの DGH-noCF − DGH-S の 4 設定の最大 < D1-L2 の予測-noCF − 入れ替え: {'当たり' if p['p3']['hit'] else '外れ'} — "
          f"グラフの最大 {f(p['p3']['graph_max'])}（{', '.join(f(x) for x in p['p3']['graph_by_setting'])}）、D1-L2 {f(p['p3']['d1l2'])}")
    w(f"4. DG-noCF − D-noCF が全 W・全設定で ±{band} の中: 当たり {sum(x['hit'] for x in p['p4'])}/{len(p['p4'])} — "
      + "、".join(f"{x['scope']} {x['setting']} {f(x['six'])}" for x in p["p4"]))
    w("")
    w("## 9. 所要")
    w("")
    w(f"run の学習と評価の合計 {S['elapsed_seconds_total'] / 3600:.2f} GPU 時間相当（各 run の elapsed_seconds の和。並行 GPU 2 枚 × 4 本）。費用は記録であり判断に使わない。")
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    # 全部の差の CSV
    ph = S["present_phases"]
    with open(a.csv, "w", encoding="utf-8-sig", newline="") as fh:
        cw = csv.writer(fh)
        cw.writerow(["group", "scope", "setting_or_type", "N", "L", "epoch", "arm1", "arm2", "reads", "six", "acc", "j7",
                     *[f"phase:{x}" for x in ph], "v09_six", "v09_acc", "v09_j7", "v10_six", "v10_acc", "v10_j7",
                     "argmax_agree", "metrics_identical", "readable"])
        for d in diffs:
            cw.writerow([d["group"], d["scope"], d.get("setting", d.get("type")), d.get("N", ""), d.get("L", ""), d["epoch"], d["arm1"], d["arm2"],
                         d["reads"], d["six"], d["acc"], d["j7"], *[d["per_phase"][x] for x in ph],
                         d["per_video"]["09"]["six"], d["per_video"]["09"]["acc"], d["per_video"]["09"]["j7"],
                         d["per_video"]["10"]["six"], d["per_video"]["10"]["acc"], d["per_video"]["10"]["j7"],
                         d["argmax_agree"], d["metrics_identical"], d["readable"]])
    print("REPORT lines", len(L), "diffs", len(diffs))


if __name__ == "__main__":
    main()

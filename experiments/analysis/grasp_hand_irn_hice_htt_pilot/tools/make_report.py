"""REPORT.md と diffs.csv を記録から作る（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、Task E、SPEC §7・§10）。手で写さない。

    python3 experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/make_report.py

読むもの: $T/e/summary.json（aggregate.py）、$T/d/chk_compare.json・ends.json、$T/c/c_types.json・identity_summary.json・repro_compare.json、$T/b/b_tokens.json。
書くもの: experiments/analysis/grasp_hand_irn_hice_htt_pilot/REPORT.md と diffs.csv（UTF-8 BOM つき）。採否・順位は書かない（SPEC §7）。
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
T = Path("/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt")
OUT = ROOT / "experiments/analysis/grasp_hand_irn_hice_htt_pilot"
SETS = ("s1", "s2", "s3", "s4")
SN = {"s1": "N10 L1", "s2": "N10 L2", "s3": "N30 L1", "s4": "N30 L2"}
SCOPES = ("W1", "W2", "W3")
TYPES = ("GR", "IRN", "HiCE", "HTT")
DIFF_ORDER = [("DGH", "A0"), ("D", "A0"), ("DG", "D"), ("DH", "D"), ("DGH", "DG"), ("DGH", "DGH-U"), ("DGH", "DGH-noCF"), ("DGH-GT", "A0")]
CROSS = [("DGH", "A0"), ("DGH-GT", "A0"), ("DG", "D"), ("DGH", "DGH-U")]
ARMS = ("A0", "D", "DG", "DH", "DGH", "DGH-U", "DGH-noCF", "DGH-GT")


def load(p):
    return json.loads(Path(p).read_text())


def f4(x):
    return f"{x:+.4f}"


def cell(d, band):
    mark = "" if abs(d["six"]) > band else "·"
    b = "†" if d.get("borrowed") else ""
    return f"{f4(d['six'])}{mark}{b} / {f4(d['acc'])} / {f4(d['j7'])}"


def main():
    s = load(T / "e/summary.json")
    chk = load(T / "d/chk_compare.json")["pairs"]
    ends = load(T / "d/ends.json")
    ct = load(T / "c/c_types.json")["summary"]
    idn = load(T / "c/identity_summary.json")
    rep = load(T / "c/repro_compare.json")
    bt = load(T / "b/b_tokens.json")["summary"]
    band = s["band"]
    within = {(d["type"], d["scope"], d["setting"], d["arm1"], d["arm2"], d["state"]): d for d in s["diffs"]}
    cross = {(d["type"], d["scope"], d["setting"], d["arm1"], d["arm2"], d["state"]): d for d in s["cross"]}
    L = []
    w = L.append
    w("# REPORT — T-2026-11-21-grasp-hand-irn-hice-htt-pilot（非公式の予備測定。関門の判定と設計の判断に使わない）")
    w("")
    w("把持・手・術具の予測（前回のグラフの節と同じトークン）を、三つの渡し方 IRN・HiCE・HTT で工程塔の時間ヘッドの入力へ渡した腕の val の値。")
    w("andrew、Fold A、seed 42 の 1 本ずつ、収束規則。全値は記録（`$T/e/summary.json`）から `tools/aggregate.py` と本道具が作った。")
    w("**採否・順位は書かない**（SPEC §7）。差は ±0.015 を並べて書き、その中の差（「·」）は読めない。")
    w("")
    w("- 6 工程 = val に現れる 7 工程から dressing を除いた Jaccard の平均、acc = frame accuracy、7 工程 = 7 工程の Jaccard の平均（記録の phase_jaccard と同じ）")
    w("- 表の値は「6 工程 / acc / 7 工程」の差。「·」は 6 工程の差が ±0.015 の中、「†」は SPEC §5.2 の流用の値を含む差")
    w(f"- GR = 前回のグラフの型（`grasp_hand_graph_arm_*` 96 本の記録を測り直した値）。塔単独: 6 工程 {s['tower_alone']['six_phase_mean']:.4f}・"
      f"acc {s['tower_alone']['phase_accuracy']:.4f}・7 工程 {s['tower_alone']['phase_jaccard']:.4f}")
    w("")
    w("## 1. run と確かめ")
    w("")
    w(f"- 本契約の run: {ends['n']} 本（表の 248 本）、完了 {ends['n_complete']}、収束規則 {ends['n_converge']}、規則で打ち切り {ends['n_stopped_by_rule']}、"
      f"上限 120 に張り付き {ends['n_cap']}、学習率と weight decay が写した値 {ends['n_lr_ok']}、ホスト {', '.join(ends['hosts'])}、"
      f"所要 {ends['elapsed_range'][0]:.1f}〜{ends['elapsed_range'][1]:.1f} s。欠け {len(ends['missing'])}。"
      f"存在しない名前で {ends['control_nonexistent_name']} 件・在る名前で {ends['control_existing_name']} 件")
    w(f"- 測り直し: {s['n_recomputed']} 本（GR 96 を含む）で確率から測り直した値と記録のずれの最大 {s['recompute_max_dev']}、"
      f"1e-6 ずらした写しを {'全部' if s['recompute_control_all_detected'] else '一部だけ'}検出。7 工程 = phase_jaccard: {s['j7_equals_phase_jaccard_all']}")
    w(f"- 流用した組み合わせ {s['n_borrowed']}、欠け {len(s['missing'])}")
    w("")
    w("| 確かめ | 一致 | 最良の確率の最大の差 | 最後の確率の最大の差 | 1e-6 ずらした写しが一致するか |")
    w("|---|---|---|---|---|")
    for p in chk:
        w(f"| {p['name']} | {p['equal']} | {p['best'].get('max_abs_diff')} | {p['last'].get('max_abs_diff')} | {p['best_control_shift_1e-6_equal']} |")
    w("")
    w("## 2. 型と設定（実行者が決めたものは audit C-1）")
    w("")
    w("| 型 | s1 | s2 | s3 | s4 | run（流用を除く） | 最良の回の中央 W1 / W2 / W3 | 総 epoch | 最後 − 最良の 6 工程の中央 W1 / W2 / W3 | 所要 s |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for t in TYPES:
        st = s["stats"][t]
        p = st["params_by_setting"]
        be = " / ".join(f"{st['by_scope'][sc]['best_epoch_median']:.0f}" for sc in SCOPES)
        lm = " / ".join(f4(st["by_scope"][sc]["last_minus_best_six_median"]) for sc in SCOPES)
        w(f"| {t} | {p['s1']} | {p['s2']} | {p['s3']} | {p['s4']} | {st['runs']} | {be} | {st['epochs_run_range'][0]}〜{st['epochs_run_range'][1]} | "
          f"{lm} | {st['elapsed_range'][0]:.1f}〜{st['elapsed_range'][1]:.1f} |")
    w("")
    w(f"- 型の定義の検査（audit C-2）: 中身を零にした入力で g_t を替えた差の最大 {ct['zero_content_g_change_max']:.2e}、HiCE の A0・D の鍵の最大 {ct['hice_A0_D_keys_max']}、"
      f"学習前の一致 {idn['n_ok']}/{idn['n']}（差 {idn['identity_diff_max']}）、陽性対照 {idn['positive_changed']}/{idn['n']}")
    w(f"- トークン（audit B-1）: 中身の一致 {bt['content_equal']}/{bt['content_n']}、持ち手の一致 train {bt['agreement']['train'][0]}/{bt['agreement']['train'][1]}・"
      f"val {bt['agreement']['val'][0]}/{bt['agreement']['val'][1]}。回し直し（audit C-3）: グラフ {rep['gr']['all_equal']}、T→P {rep['tp']['all_equal']}")
    w("")
    w("## 3. 同じ型の中の差（同じ W・同じ設定）")
    w("")
    for t in TYPES:
        c = s["counts"][t]
        w(f"### 3.{TYPES.index(t) + 1} {t}")
        w("")
        w(f"最良の回の差 {c['n_diffs_best']} 個のうち ±0.015 の中 {c['n_unreadable_best']}、指標がちょうど同じ {c['n_metrics_identical_best']}、"
          f"最良と最後で 6 工程の差の符号が変わった差 {c['n_sign_flip']}")
        w("")
        for state in ("best", "last"):
            w(f"**{'最良の回' if state == 'best' else '最後の回'}**")
            w("")
            w("| 差 | W | " + " | ".join(f"{x}（{SN[x]}）" for x in SETS) + " |")
            w("|---|---|" + "---|" * len(SETS))
            for a1, a2 in DIFF_ORDER:
                for sc in SCOPES:
                    row = [cell(within[(t, sc, x, a1, a2, state)], band) if (t, sc, x, a1, a2, state) in within else "—" for x in SETS]
                    w(f"| {a1} − {a2} | {sc} | " + " | ".join(row) + " |")
            w("")
    w("## 4. 型の間の並べ（同じ W・同じ設定。各型の中の差）")
    w("")
    for state in ("best", "last"):
        w(f"**{'最良の回' if state == 'best' else '最後の回'}**（6 工程 / acc / 7 工程）")
        w("")
        w("| 差 | W | 設定 | " + " | ".join(TYPES) + " |")
        w("|---|---|---|" + "---|" * len(TYPES))
        for a1, a2 in CROSS:
            for sc in SCOPES:
                for x in SETS:
                    row = [cell(within[(t, sc, x, a1, a2, state)], band) if (t, sc, x, a1, a2, state) in within else "—" for t in TYPES]
                    w(f"| {a1} − {a2} | {sc} | {x} | " + " | ".join(row) + " |")
        w("")
    w("## 5. 同じ腕どうしの型の差（6 工程 / acc / 7 工程。新しい型 − GR）")
    w("")
    a0 = s["a0_vs_graph"]
    w("各型の A0 とグラフの型の A0 の確かめ（s1。SPEC §7.1 の予測 2）: " + "、".join(f"{x['name']} {'一致' if x['equal'] else '不一致'}"
                                                                          f"（最大の差 {x['best_max_abs_diff']}）" for x in a0))
    w("")
    for state in ("best", "last"):
        w(f"**{'最良の回' if state == 'best' else '最後の回'}**")
        w("")
        w("| 型の差 | W | 設定 | " + " | ".join(ARMS) + " |")
        w("|---|---|---|" + "---|" * len(ARMS))
        for t in ("IRN", "HiCE", "HTT"):
            for sc in SCOPES:
                for x in SETS:
                    row = []
                    for arm in ARMS:
                        k = (f"{t}−GR", sc, x, f"{t} {arm}", f"GR {arm}", state)
                        row.append(cell(cross[k], band) if k in cross else "—")
                    w(f"| {t} − GR | {sc} | {x} | " + " | ".join(row) + " |")
        w("")
    w("新しい型どうしの差（IRN − HiCE など）は diffs.csv の kind = cross に在る。")
    w("")
    w("## 6. W1 の塔単独との差（6 工程。最良の回 / 最後の回）")
    w("")
    al = {(r["type"], r["setting"], r["arm"], r["state"]): r for r in s["w1_vs_tower_alone"]}
    w("| 型 | 腕 | " + " | ".join(SETS) + " |")
    w("|---|---|" + "---|" * len(SETS))
    for t in TYPES:
        for arm in ARMS:
            row = [f"{f4(al[(t, x, arm, 'best')]['six'])} / {f4(al[(t, x, arm, 'last')]['six'])}" if (t, x, arm, "best") in al else "—" for x in SETS]
            w(f"| {t} | {arm} | " + " | ".join(row) + " |")
    w("")
    w("## 7. 工程別と動画ごと（最良の回。DGH − A0 と DGH-GT − A0）")
    w("")
    phases = s["present_phases"]
    vids = sorted(next(iter(s["diffs"]))["per_video"])
    w("| 型 | 差 | W | 設定 | " + " | ".join(phases) + " | " + " | ".join(f"動画 {v} の 6 工程" for v in vids) + " |")
    w("|---|---|---|---|" + "---|" * (len(phases) + len(vids)))
    for t in TYPES:
        for a1, a2 in (("DGH", "A0"), ("DGH-GT", "A0")):
            for sc in SCOPES:
                for x in SETS:
                    d = within.get((t, sc, x, a1, a2, "best"))
                    if d:
                        w(f"| {t} | {a1} − {a2} | {sc} | {x} | " + " | ".join(f4(d["per_phase"][p]) for p in phases) + " | "
                          + " | ".join(f4(d["per_video"][v]["six_phase_mean"]) for v in vids) + " |")
    w("")
    w("全差の工程別・動画ごとは diffs.csv。")
    w("")
    w("## 8. argmax の一致と指標が同じ差")
    w("")
    for t in TYPES:
        ag = [d["argmax_agree"] for d in s["diffs"] if d["type"] == t and d["state"] == "best"]
        w(f"- {t}: 腕の間の argmax の一致の割合 {min(ag):.3f}〜{max(ag):.3f}、指標がちょうど同じ差 {s['counts'][t]['n_metrics_identical_best']}")
    w("")
    w("## 9. 予測（SPEC §7.1。結果を見る前に起票者が書いたもの）")
    w("")
    pr = s["predictions"]
    w(f"1. DGH-GT − A0 ≥ DGH − A0（6 工程、各型・各 W・各設定）: {pr['p1_n'][0]}/{pr['p1_n'][1]} で当たり。外れ: "
      + ("、".join(f"{x['type']} {x['scope']} {x['setting']}（{f4(x['gt_minus_a0'])} 対 {f4(x['dgh_minus_a0'])}）" for x in pr["p1"] if not x["hit"]) or "なし"))
    w("2. 各型の A0 の val の確率が同じ W のグラフの型の A0 の記録と一致: " + "、".join(f"{x['name']} {'当たり' if x['equal'] else '外れ'}" for x in a0))
    w("3. W1 の DGH − A0 が 4 設定のうち 3 つ以上で ±0.015 の中: " + "、".join(
        f"{t} {'当たり' if v['hit'] else '外れ'}（{v['n_in_band']}/4、{' '.join(f4(z) for z in v['values'])}）" for t, v in pr["p3"].items()))
    w("4. W2 の DGH − A0 が 4 設定のうち 2 つ以上で +0.015 を上回る: " + "、".join(
        f"{t} {'当たり' if v['hit'] else '外れ'}（{v['n_above']}/4、{' '.join(f4(z) for z in v['values'])}）" for t, v in pr["p4"].items()))
    w("5. W1 の各型の DGH − グラフの型の DGH が全設定で ±0.015 の中: " + "、".join(
        f"{t} {'当たり' if pr['p5_hit'][t] else '外れ'}（{' '.join(f4(x['six']) for x in pr['p5'] if x['type'] == t)}）" for t in ("IRN", "HiCE", "HTT")))
    w("")
    w("## 10. 要約（6 工程の差、4 設定の範囲。括弧は正の数 / ±0.015 の外の数）")
    w("")
    for state in ("best", "last"):
        w(f"**{'最良の回' if state == 'best' else '最後の回'}**")
        w("")
        w("| 型 | 差 | W1 | W2 | W3 |")
        w("|---|---|---|---|---|")
        for t in TYPES:
            for a1, a2 in DIFF_ORDER:
                row = []
                for sc in SCOPES:
                    v = [within[(t, sc, x, a1, a2, state)]["six"] for x in SETS if (t, sc, x, a1, a2, state) in within]
                    row.append(f"{f4(min(v))}〜{f4(max(v))}（{sum(z > 0 for z in v)}/{sum(abs(z) > band for z in v)}）" if v else "—")
                w(f"| {t} | {a1} − {a2} | " + " | ".join(row) + " |")
        w("")
        w("| 型の差（同じ腕） | 腕 | W1 | W2 | W3 |")
        w("|---|---|---|---|---|")
        for t in ("IRN", "HiCE", "HTT"):
            for arm in ("DGH", "DGH-GT"):
                row = []
                for sc in SCOPES:
                    v = [cross[k]["six"] for x in SETS if (k := (f"{t}−GR", sc, x, f"{t} {arm}", f"GR {arm}", state)) in cross]
                    row.append(f"{f4(min(v))}〜{f4(max(v))}（{sum(z > 0 for z in v)}/{sum(abs(z) > band for z in v)}）" if v else "—")
                w(f"| {t} − GR | {arm} | " + " | ".join(row) + " |")
        w("")
    (OUT / "REPORT.md").write_text("\n".join(L) + "\n")
    phases_cols = [f"per_phase_{p}" for p in phases]
    video_cols = [f"per_video_{v}_{k}" for v in vids for k in ("six_phase_mean", "phase_jaccard", "phase_accuracy")]
    with open(OUT / "diffs.csv", "w", newline="", encoding="utf-8-sig") as fh:
        wr = csv.writer(fh)
        wr.writerow(["kind", "type", "scope", "setting", "arm1", "arm2", "state", "six", "acc", "j7", "outside_band_0.015", "metrics_identical",
                     "argmax_agree", "borrowed", "key1", "key2"] + phases_cols + video_cols)
        for d in s["diffs"] + s["cross"]:
            wr.writerow([d["kind"], d["type"], d["scope"], d["setting"], d["arm1"], d["arm2"], d["state"], d["six"], d["acc"], d["j7"],
                         d["readable"], d["metrics_identical"], d["argmax_agree"], ";".join(d["borrowed"]), d["key1"], d["key2"]]
                        + [d["per_phase"][p] for p in phases] + [d["per_video"][v][k] for v in vids
                                                                  for k in ("six_phase_mean", "phase_jaccard", "phase_accuracy")])
    print(f"REPORT.md {len(L)} lines, diffs.csv {len(s['diffs']) + len(s['cross'])} rows")


if __name__ == "__main__":
    main()

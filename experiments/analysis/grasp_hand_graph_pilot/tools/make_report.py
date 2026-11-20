"""REPORT.md を記録から作る（非公式 T-2026-11-20-grasp-hand-graph-pilot、Task E）。数値は summary.json と各検査の記録から読み、手で写さない。

    .venv/bin/python experiments/analysis/grasp_hand_graph_pilot/tools/make_report.py --out experiments/analysis/grasp_hand_graph_pilot/REPORT.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

O = Path("/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph")
SETTINGS = ["s1", "s2", "s3", "s4"]
SET_DESC = {"s1": "N10 L1", "s2": "N10 L2", "s3": "N30 L1", "s4": "N30 L2"}
DIFF_ORDER = [("DGH", "A0"), ("D", "A0"), ("DG", "D"), ("DH", "D"), ("DGH", "DG"), ("DGH", "DGH-U"), ("DGH", "DGH-noCF"), ("DGH-GT", "A0")]


def f4(x):
    return "—" if x is None else f"{x:.4f}"


def sg(x):
    return "—" if x is None else (f"{x:+.4f}" if x != 0 else "0.0")


def load(p):
    p = Path(p)
    return json.loads(p.read_text()) if p.exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary", default=str(O / "e/summary.json"))
    a = ap.parse_args()
    s = load(a.summary)
    L = ["# REPORT — T-2026-11-20-grasp-hand-graph-pilot（非公式の予備測定。関門と設計の判断に使わない）", "",
         "andrew、折り A、seed 42。数値はすべて記録から `tools/make_report.py` が作った（手で写していない）。test の動画 04・05・07 は通していない。", ""]
    # ---- 塔
    L += ["## 1. 塔（SPEC §3）", "", "| 塔 | 学ぶフレーム | 学習前 | 選んだ回 | 止まった回 | val mask mAP | 所要 (h) | 最大確保 (GB) |", "|---|---|---|---|---|---|---|---|"]
    for k, t in s["towers"].items():
        if t is None:
            L.append(f"| {k} | 未 | | | | | | |")
            continue
        L.append(f"| {k} | {t['train_frames']} | {f4(t['pre_segm_mAP'])} | {t['best_epoch']} | {t['stopped_epoch']} | {f4(t['best_segm_mAP'])} | "
                 f"{t['elapsed_seconds'] / 3600:.2f} | {t['peak_alloc_bytes'] / 1e9:.1f} |")
    L.append("")
    for k, t in s["towers"].items():
        if t is None:
            continue
        names = list(t["best_per_class_ap"].keys())
        L += [f"### {k} の epoch ごとの val（mask mAP とクラス別 AP）", "", "| epoch | mAP | " + " | ".join(names) + " |",
              "|---" * (2 + len(names)) + "|"]
        for e in t["epochs"]:
            L.append(f"| {e['epoch']} | {f4(e['segm_mAP'])} | " + " | ".join(f4(e["per_class_ap"].get(n)) for n in names) + " |")
        L.append("")
    c = s.get("tower_compare")
    if c:
        L += ["### G3 と G5r の器具 3 クラス（同じホスト・同じ道具・同じ設定。記述だけ）", "",
              "| クラス | G3 | G5r | G3 − G5r | 参考: bengio の G（別のホスト） |", "|---|---|---|---|---|"]
        for r in c["rows"]:
            L.append(f"| {r['class']} | {f4(r['G3'])} | {f4(r['G5r'])} | {sg(r['G3_minus_G5r'])} | {f4(r['bengio_G_reference'])} |")
        L += [f"| 平均 | {f4(c['G3_tool3_mean'])} | {f4(c['G5r_tool3_mean'])} | {sg(c['diff_mean'])} | "
              f"{f4(sum(c['bengio_G'][x] for x in ('Left Hand Tool', 'Right Hand Tool', 'Two Hands Tool')) / 3)} |", "",
              f"- G3 の 3 クラスの mask mAP {f4(c['G3_segm_mAP'])}、G5r の 5 クラスの mask mAP {f4(c['G5r_segm_mAP_5cls'])}"
              f"（G5r の器具 3 クラスの平均 {f4(c['G5r_tool3_mean'])} とは別の値）",
              f"- 目標 0.80 との差（G3 の器具 3 クラスの平均 − 0.80）: {sg(c['target_0p80_gap_G3_tool3_mean'])}",
              f"- bengio の G の出所: {c['bengio_G']['source']}", ""]
    h = s.get("hands")
    if h:
        L += [f"- H4 の自分の手 2 クラスの AP の平均 {f4(h['own_mean'])}（左 {f4(h['own'][0])}・右 {f4(h['own'][1])}）、"
              f"他者の手 {f4(h['other_mean'])}（左 {f4(h['other'][0])}・右 {f4(h['other'][1])}）", ""]
    # ---- 反転
    L += ["## 2. 反転（SPEC §3.4、完了判定 c）", "", "取り出し（train の 24 フレーム、反転を強制）:", "",
          "| 塔 | 経路 | 画像 | マスク | ラベルを入れ替えた | ラベルが変わらない |", "|---|---|---|---|---|---|"]
    for t in ("G3", "H4", "G5r"):
        d = load(O / f"flip/flipdata_{t}.json")
        if d:
            for name, v in d["paths"].items():
                L.append(f"| {t} | {name} | {v['image_flipped']}/{d['frames']} | {v['masks_flipped']}/{d['frames']} | "
                         f"{v['labels_swapped']}/{d['frames']} | {v['labels_unchanged']}/{d['frames']} |")
    L += ["", "学習後の整合（val の 40 フレーム、soft IoU。入れ替えた一致 / 入れ替えない写し）:", "",
          "| 塔 | 重み | 全クラス swap | 全クラス noswap | 左右のクラス swap | 左右のクラス noswap |", "|---|---|---|---|---|---|"]
    for t in ("G3", "H4", "G5r"):   # G5r は §3.4 の外。G2 の「三種の塔」に合わせて測った
        for lab in ("final", "coco"):
            d = load(O / f"flip/flipmodel_{t}_{lab}.json")
            if d:
                L.append(f"| {t} | {lab} | {f4(d['swap_soft_iou_mean_over_classes'])} | {f4(d['noswap_soft_iou_mean_over_classes'])} | "
                         f"{f4(d['swap_soft_iou_mean_over_lr_classes'])} | {f4(d['noswap_soft_iou_mean_over_lr_classes'])} |")
    L.append("")
    # ---- 信号とグラフ
    man = load(Path(__file__).resolve().parents[1] / "signals_manifest.json")
    rep = load(O / "graph/assemble_report.json")
    if man and rep:
        L += ["## 3. 信号の目録とグラフ（SPEC §4・§5、完了判定 e・f・i）", "", "| 信号 | 当てた塔 | 動画 | フレーム | 被覆 | sha256 |", "|---|---|---|---|---|---|"]
        for k, v in man["raw_signals"].items():
            L.append(f"| {k} | {v['tower_videos']} | {','.join(v['videos'])} | {v['frames']} | {v['coverage']:.4f} | {v['sha256'][:16]}… |")
        for k, v in man["det"].items():
            L.append(f"| det {k} | — | {','.join(v['videos'])} | {v['frames']} | — | {v['npz_sha256'][:16]}… |")
        L += ["", "| part | 腕 | 術具の節のあるフレーム | 左手の節 | 右手の節 | 空のフレーム | 術具の節の平均 |", "|---|---|---|---|---|---|---|"]
        for p in ("train", "val"):
            for arm, f in rep["parts"][p]["files"].items():
                L.append(f"| {p} | {arm} | {f['frames_with_tools']}/{f['frames']} | {f['frames_with_hand_L']} | {f['frames_with_hand_R']} | "
                         f"{f['frames_empty']} | {f['tool_nodes_mean']:.2f} |")
        L.append("")
        for p in ("train", "val"):
            r = rep["parts"][p]
            L.append(f"- {p}: 表の検査の外れ {r['table_check']['violations']}（表と違う腕を作った写し {r['table_check_control_wrong_arm']['violations']}）、"
                     f"数え {json.dumps(r['counts'], ensure_ascii=False)}、正解の手の和集合 {json.dumps(r['gt_stats'], ensure_ascii=False)}")
            pv = r["provenance"]
            if p == "train":
                L.append(f"  - 交差適合の外れ G3 {pv['G3_cf']['violations']}・H4 {pv['H4_cf']['violations']}・検出 {pv['det_cf']['violations']}"
                         f"（確定の G3 を 5 フレーム混ぜた写し {pv['G3_cf_control_mixed_final']['violations']}）")
            ag, ags = r["gt_grasp_agreement"], r["gt_grasp_agreement_control_swapLR"]
            if ag:
                L.append(f"  - 正解の持ち手と注釈の把持の一致 {ag['agree']}/{ag['boxes']}（{ag['rate']:.4f}）、左右を入れ替えた写し {ags['agree']}/{ags['boxes']}（{ags['rate']:.4f}）")
        L += ["", f"- test を通さない: 各段の動画の集合と {{04, 05, 07}} の共通 {sum(x['n_overlap'] for x in rep['i_test_unused'].values())} 件"
              f"（{len(rep['i_test_unused'])} 段）。04 を混ぜた写しで {rep['i_control_04_mixed']['n_overlap']} 件", ""]
    idn = load(O / "identity/identity_summary.json")
    if idn:
        rows = idn["rows"]
        L += ["## 4. 恒等性（完了判定 g）", "", f"- {len(rows)} 件（4 設定 × 3 W × 8 腕）。学習前のロジットの差の最大 {max(r[2] for r in rows)}、"
              f"出力射影を N(0, 0.05²) にしたときの差の最小 {min(r[3] for r in rows):.4f}、外れ {len(idn['bad'])} 件", ""]
    al = s["tower_alone"]
    L += [f"- 塔単独（本契約の識別子で 1 回）: J {f4(al['phase_jaccard'])}・acc {f4(al['phase_accuracy'])}・6 工程 {f4(al['six_phase_mean'])}、"
          f"記録との一致 {al['equals_record']}", ""]
    # ---- 腕
    L += ["## 5. 腕の差（SPEC §7。同じ W・同じ設定の中だけ。最良の回。セルは 6 工程 / acc / 7 工程の J）", "",
          f"±{s['band']} の中の 6 工程の差は「読めない」（*）。符号で解釈しない。確率から測り直したずれの最大 {s['recompute_max_dev']}、"
          f"1e-6 ずらした写しの検出 {s['recompute_control_all_detected']}。7 工程の J = phase_jaccard（{s['j7_equals_phase_jaccard_all']}）。", ""]
    best = [d for d in s["diffs"] if d["state"] == "best"]
    for sc in ("W1", "W2", "W3"):
        L += [f"### {sc}", "", "| 差 | 読むこと | " + " | ".join(f"{x}（{SET_DESC[x]}）" for x in SETTINGS) + " |", "|---|---|" + "---|" * 4]
        for a1, a2 in DIFF_ORDER:
            cells, what = [], ""
            for st in SETTINGS:
                d = next((x for x in best if x["scope"] == sc and x["setting"] == st and x["arm1"] == a1 and x["arm2"] == a2), None)
                if d is None:
                    cells.append("未")
                    continue
                what = d["reads"]
                cells.append(f"{sg(d['six'])}{'' if d['readable'] else '*'} / {sg(d['acc'])} / {sg(d['j7'])}")
            L.append(f"| {a1} − {a2} | {what} | " + " | ".join(cells) + " |")
        L.append("")
    L += ["### W1 の塔単独との差（6 工程 / acc / 7 工程の J）", "", "| 腕 | " + " | ".join(SETTINGS) + " |", "|---|" + "---|" * 4]
    for arm in ("A0", "D", "DG", "DH", "DGH", "DGH-U", "DGH-noCF", "DGH-GT"):
        cells = []
        for st in SETTINGS:
            d = next((x for x in s["w1_vs_tower_alone"] if x["setting"] == st and x["arm"] == arm), None)
            cells.append("未" if d is None else f"{sg(d['six'])} / {sg(d['acc'])} / {sg(d['j7'])}")
        L.append(f"| {arm} | " + " | ".join(cells) + " |")
    L += ["", f"- 差 {s['n_diffs_best']} 個のうち、指標（J と acc）がちょうど同じ {s['n_metrics_identical_best']} 個、6 工程の差が ±{s['band']} の中 {s['n_unreadable_best']} 個", "",
          "### argmax の一致の割合（val の全フレーム、最良の回）", "", "| W | 差 | " + " | ".join(SETTINGS) + " |", "|---|---|" + "---|" * 4]
    for sc in ("W1", "W2", "W3"):
        for a1, a2 in DIFF_ORDER:
            cells = []
            for st in SETTINGS:
                d = next((x for x in best if x["scope"] == sc and x["setting"] == st and x["arm1"] == a1 and x["arm2"] == a2), None)
                cells.append("未" if d is None else f"{d['argmax_agree']:.4f}")
            L.append(f"| {sc} | {a1} − {a2} | " + " | ".join(cells) + " |")
    L.append("")
    # 工程別・動画ごと（DGH − A0 と DGH-GT − A0）
    L += ["### 工程別と動画ごと（最良の回。DGH − A0 と DGH-GT − A0）", ""]
    for a1 in ("DGH", "DGH-GT"):
        L += [f"**{a1} − A0**", "", "| W | 設定 | " + " | ".join(s["present_phases"]) + " | 動画 09（6 工程） | 動画 10（6 工程） |",
              "|---|---|" + "---|" * (len(s["present_phases"]) + 2)]
        for sc in ("W1", "W2", "W3"):
            for st in SETTINGS:
                d = next((x for x in best if x["scope"] == sc and x["setting"] == st and x["arm1"] == a1 and x["arm2"] == "A0"), None)
                if d is None:
                    continue
                L.append(f"| {sc} | {st} | " + " | ".join(sg(d["per_phase"][p]) for p in s["present_phases"]) + " | "
                         + " | ".join(sg(d["per_video"][v]["six_phase_mean"]) for v in ("09", "10")) + " |")
        L.append("")
    # 最後の回
    last = [d for d in s["diffs"] if d["state"] == "last"]
    L += ["### 最後の回の差（参考。6 工程 / acc / 7 工程の J）", "", "| W | 差 | " + " | ".join(SETTINGS) + " |", "|---|---|" + "---|" * 4]
    for sc in ("W1", "W2", "W3"):
        for a1, a2 in DIFF_ORDER:
            cells = []
            for st in SETTINGS:
                d = next((x for x in last if x["scope"] == sc and x["setting"] == st and x["arm1"] == a1 and x["arm2"] == a2), None)
                cells.append("未" if d is None else f"{sg(d['six'])} / {sg(d['acc'])} / {sg(d['j7'])}")
            L.append(f"| {sc} | {a1} − {a2} | " + " | ".join(cells) + " |")
    L.append("")
    # 収束
    L += ["## 6. 腕の学習（収束規則）", "", "| W | 設定 | 腕 | epoch | 学習率を落とした回 | 選んだ回 | 上限 | 所要 (s) | 6 工程（最良） |", "|---|---|---|---|---|---|---|---|---|"]
    for k, r in s["runs"].items():
        sc, st, arm = k.split("|")
        L.append(f"| {sc} | {st} | {'A0' if arm == 'empty' else arm} | {r['epochs_run']} | {r['lr_drop_epoch']} | {r['best_epoch']} | {r['reached_cap']} | "
                 f"{r['elapsed_seconds']:.1f} | {f4(r['best']['six_phase_mean'])} |")
    L += ["", f"- run {s['n_runs']} 本、欠け {len(s['missing'])} 件。並行は GPU 2 枚 × 4 本（`tools/run_arms.sh` の NW = 8）", ""]
    # 予測
    p = s["predictions"]
    L += ["## 7. 予測の当たり外れ（SPEC §7.1）", ""]
    hits1 = [x["hit"] for x in p["p1_gt_ge_dgh"]]
    L.append(f"1. DGH-GT − A0 ≥ DGH − A0（6 工程）: {sum(hits1)}/{len(hits1)} で当たり")
    hits2 = [x["hit"] for x in p["p2_w1_dg_minus_d_in_band"]]
    L.append(f"2. W1 の DG − D が ±0.015 の中: {sum(hits2)}/{len(hits2)} で当たり（" + "、".join(f"{x['setting']} {sg(x['six'])}" for x in p["p2_w1_dg_minus_d_in_band"]) + "）")
    if "p3_g3_vs_g5r_tool3_within_0p03" in p:
        x = p["p3_g3_vs_g5r_tool3_within_0p03"]
        L.append(f"3. G3 と G5r の器具 3 クラスの平均の差が ±0.03 の中: 差 {sg(x['diff'])}、{'当たり' if x['hit'] else '外れ'}")
    if "p4_h4_own_gt_other" in p:
        x = p["p4_h4_own_gt_other"]
        L.append(f"4. H4 の自分の手の AP > 他者の手の AP: {f4(x['own'])} と {f4(x['other'])}、{'当たり' if x['hit'] else '外れ'}")
    L.append("")
    Path(a.out).write_text("\n".join(L) + "\n")
    print("wrote", a.out, len(L), "lines")


if __name__ == "__main__":
    main()

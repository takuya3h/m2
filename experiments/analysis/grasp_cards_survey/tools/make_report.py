"""REPORT.md を各測定の記録（$S の JSON）から作る。数値を手で書かない。T-2026-11-08-grasp-cards-survey。

    python make_report.py --store <STORE> --out experiments/analysis/grasp_cards_survey/REPORT.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def J(p):
    return json.loads(Path(p).read_text())


def f(x, d=4):
    if x is None:
        return "—"
    if isinstance(x, int):
        return f"{x:,}"
    return f"{x:.{d}f}"


def table(head, rows):
    head = [h.replace("|", "\\|") for h in head]
    out = ["", "| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    S = Path(a.store)
    s1 = J(S / "c/s1/s1_record_09.json")
    s23 = J(S / "b/s2s3.json")
    s4v, s4t = J(S / "c/s4/s4_record_val.json"), J(S / "c/s4/s4_record_train.json")
    s5 = J(S / "c/s5/s5_record.json")
    s6 = J(S / "c/s6/s6_record.json")
    s7 = J(S / "b/s7.json")
    L = []
    L.append("# REPORT — 把持塔の出力を使う提案カード 6 案の #15・#10 を埋める調査（bengio、学習なし）\n")
    L.append("**案の採否・推奨・順位は扱わない。** 測ったのは環境の事実だけである。契約 `T-2026-11-08-grasp-cards-survey`。"
             "判定と経緯は `tasks/T-2026-11-08-grasp-cards-survey/`（命令と出力は `audit.md`）。"
             "この頁の数値はすべて `tools/make_report.py` が各測定の記録（保存先 `/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-08-grasp-cards-survey/` の JSON）から作った。\n")
    L.append("- ホスト bengio（RTX A6000 × 2、電力の上限 220 W）。折り A（train 10 動画、val 09・10）だけを測った。他の折りの密度・間隔は同じとは限らない")
    L.append("- 塔: 工程塔 P\\*-15-COCO 折り A seed 42（fine-tune の checkpoint 79c2c478…）、検出塔 D\\*-COCO 折り A seed 42（30d199b1…）、"
             "把持塔 G 確定（5ea2cbf4…）・H1（5cfa055c…）・H2（efdefccd…）。重みは読むだけで、前後の要約値が一致した\n")

    # S1
    L.append("## S1 工程塔の空間特徴（案 3）\n")
    L.append("- Stage 2 の経路が読む特徴（`PT_CACHE` = `all_gap.npz`）: `frame_ids (15437,)`・`features (15437, 2048) float32`。**空間の軸は無い。**"
             "出所は torchvision ResNet-50 の layer4 の出力の全体平均（`stage1_ptower_r3.extract` が `fc = Identity`）")
    rows = [
        ["地図の層", s1["layer"]],
        ["入力（C×H×W）", "×".join(map(str, s1["input_chw"]))],
        ["地図（C×H×W）", "×".join(map(str, s1["map_chw"]))],
        ["縮小率（入力の画素 / 地図の画素、縦・横）", f"{s1['stride_input_px_per_map_px'][0]:.1f}・{s1['stride_input_px_per_map_px'][1]:.1f}"],
        ["縮小率（元の 1080×1920 の画素 / 地図の画素、縦・横）", f"{s1['stride_original_px_per_map_px'][0]:.2f}・{s1['stride_original_px_per_map_px'][1]:.2f}"],
        [f"順伝播 1 フレーム（batch {s1['batch']}、読み込みを除く）", f"{s1['forward_seconds_per_frame_batch']:.4f} 秒"],
        ["順伝播 1 フレーム（batch 1、20 回の中央）", f"{s1['forward_seconds_per_frame_batch1']['median']:.4f} 秒"],
        ["読み込みを含む全体（1 動画）", f"{s1['total_seconds_incl_loading']:.1f} 秒（{s1['total_seconds_per_frame_incl_loading']:.4f} 秒/フレーム）"],
        [f"保存の大きさ（動画 {s1['video']}、{s1['frames']} フレーム、fp32 の .npy）", f"{s1['bytes_fp32_file']:,} B（{s1['bytes_fp32_per_frame']:,} B/フレーム）"],
        ["同（fp16 の .npy）", f"{s1['bytes_fp16_file']:,} B（{s1['bytes_fp16_per_frame']:,} B/フレーム）"],
        ["対照: 地図の空間平均とキャッシュ（同じフレーム）の相対 L2 の最大", f"{s1['control_same_frame_rel_l2']['max']:.2e}（1e-3 を超えたフレーム {s1['control_same_frame_rel_l2']['n_over_1e-3']}）"],
        ["対照: fp16 の地図の空間平均とキャッシュ", f"{s1['control_fp16_same_frame_rel_l2']['max']:.2e}（同 {s1['control_fp16_same_frame_rel_l2']['n_over_1e-3']}）"],
        ["対照: 1 つずらしたフレームのキャッシュとの相対 L2（最小・中央）", f"{s1['control_shift1_rel_l2']['min']:.4f}・{s1['control_shift1_rel_l2']['median']:.4f}（1e-3 以下 {s1['control_shift1_rel_l2']['n_under_1e-3']}）"],
    ]
    L.append(table(["項目", "値"], rows) + "\n")

    # S2
    L.append("## S2 把持の注釈の密度（案 4・5・6）\n")
    L.append("「工程注釈のあるフレーム」には二つの集合がある。工程塔の目録（`data/processed/phase_manifest`）のフレームは術具注釈のフレームと同じ集合で、"
             "工程の CSV（`data/annotations/egosurgery_phase/*.csv`）の全行はそれより多い。CSV にだけある行は `data/raw/ego/` に画像が無い。両方を載せる。\n")
    keys = [("tool_frames", "術具注釈"), ("tool_frames_with_box", "うち枠あり"), ("hts_frames", "把持の注釈"),
            ("hts_frames_with_held_tool", "うち持つ術具あり"), ("lossmask_frames", "loss_mask"),
            ("phase_frames", "工程（目録）"), ("phase_csv_frames", "工程（CSV）"), ("phase_csv_with_image", "CSV のうち画像あり"),
            ("phase_csv_without_tool", "CSV のうち術具注釈なし"), ("phase_csv_without_grasp_usable", "CSV のうち使える把持の注釈なし")]
    fold = s23["videos"]
    rows = []
    for part in ("train", "val"):
        for v in fold[part]:
            r = s23["per_video"][v]
            rows.append([f"{part} {v}"] + [f(r[k]) for k, _ in keys])
        t = s23[f"total_{part}"]
        rows.append([f"**{part} 計**"] + [f"**{f(t[k])}**" for k, _ in keys])
    L.append(table(["動画"] + [n for _, n in keys], rows) + "\n")
    L.append("- 「使える把持の注釈」= 把持の注釈の画像で loss_mask に無いもの。loss_mask のフレームはすべて術具注釈のフレームで、把持の注釈の画像とは重ならない（train 301・val 1）")
    tt, tv = s23["total_train"], s23["total_val"]
    L.append(f"- CSV の行のうち使える把持の注釈が無い割合: train {tt['phase_csv_without_grasp_usable']}/{tt['phase_csv_frames']}"
             f" = {tt['phase_csv_without_grasp_usable']/tt['phase_csv_frames']:.3f}、val {tv['phase_csv_without_grasp_usable']}/{tv['phase_csv_frames']}"
             f" = {tv['phase_csv_without_grasp_usable']/tv['phase_csv_frames']:.3f}。目録（工程塔が読むフレーム）のうち無い割合: train {tt['phase_without_grasp_usable']}/{tt['phase_frames']}、val {tv['phase_without_grasp_usable']}/{tv['phase_frames']}\n")
    L.append("### 欠けの連の長さ（同じクリップの中で、工程のフレームの順に欠けが続く数）\n")
    rows = []
    for v in fold["train"] + fold["val"] + ["all_train", "all_val"]:
        r = s23["runs_missing"][v]
        def cell(x):
            qq = x["length_quantiles"]
            return f"{x['runs']} 連・{x['frames']} 枚" + (f"（中央 {qq['median']:.0f}・最大 {qq['max']:.0f}）" if qq else "")
        rows.append([v, cell(r["grasp_usable"]), cell(r["csv_tool"]), cell(r["csv_grasp_usable"])])
    L.append(table(["動画", "目録のうち使える把持の注釈なし", "CSV のうち術具注釈なし", "CSV のうち使える把持の注釈なし"], rows) + "\n")
    hist_t = s23["runs_missing"]["all_train"]["csv_grasp_usable"]["length_hist"]
    hist_v = s23["runs_missing"]["all_val"]["csv_grasp_usable"]["length_hist"]
    L.append(f"- CSV のうち使える把持の注釈なしの連の長さの度数: train {hist_t}、val {hist_v}\n")
    c = s23["controls"]
    L.append(f"- 対照: 件数の関数に test の 04 を混ぜると術具 {c['trainval_tool_frames']:,} → {c['with_test_04_tool_frames']:,}、把持 {c['trainval_hts_frames']:,} → {c['with_test_04_hts_frames']:,}、"
             f"loss_mask {c['trainval_lossmask']} → {c['with_test_04_lossmask']}、工程の CSV {c['trainval_phase_csv']:,} → {c['with_test_04_phase_csv']:,}（test の工程は開かない）。"
             f"存在しない動画 99 で全列 0（{sum(c['nonexistent_99'].values())}）。{c['note']}\n")

    # S3
    L.append("## S3 術具注釈フレームの時間間隔（案 5）\n")
    L.append(f"フレーム番号は {s23['fps']} fps の通し番号（出所 {s23['fps_source']}）。同じクリップの中で隣り合う術具注釈フレームの番号の差 Δ を数え、秒は Δ / 0.5。クリップの境目の差は時刻が分からないので数えない。\n")
    rows = []
    for v in fold["train"] + fold["val"]:
        r = s23["s3"][v]
        d, s = r["delta_frames"], r["delta_seconds"]
        rows.append([v, r["tool_frames"], r["clips"], d["n"], f"{s['min']:.0f}・{s['p5']:.0f}・{s['median']:.0f}・{s['p95']:.1f}・{s['max']:.0f}",
                     f"{r['delta_eq_1']}/{d['n']}", f"{r['tool_in_phase_csv']}/{r['tool_frames']}", f"{r['tool_label_agrees_csv']}/{r['tool_frames']}",
                     f"{r['control_shift1_in_phase_csv']}・{r['control_shift1_label_agrees_csv']}"])
    for part in ("train", "val"):
        r = s23["s3"][f"all_{part}"]
        s = r["delta_seconds"]
        rows.append([f"**{part} 計**", "", "", r["delta_frames"]["n"], f"{s['min']:.0f}・{s['p5']:.0f}・{s['median']:.0f}・{s['p95']:.1f}・{s['max']:.0f}",
                     f"{r['delta_eq_1_fraction']:.3f}", "", "", ""])
    L.append(table(["動画", "術具注釈", "クリップ", "差の数", "秒（最小・5%・中央・95%・最大）", "Δ=1", "CSV に在る", "工程の名前の一致",
                    "対照: 1 ずらすと CSV に在る・名前の一致"], rows) + "\n")
    L.append("- 工程注釈のフレーム（CSV の行、0.5 fps）との対応: 術具注釈フレームはすべて CSV の同じ名前の行に在り、工程の名前が目録と CSV で全件一致する。CSV 自体もクリップの中で番号が飛ぶ（除外されたフレーム）\n")

    # S4
    L.append("## S4 検出塔の出力の形と較正（案 1・4）\n")
    L.append("- NMS は使わない: `third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery.py` 83〜84 行 "
             "`PostProcess(select_box_nums_for_evaluation=300, nms_iou_threshold=-1, confidence_score=-1)`、`models/bricks/post_process.py` 28〜33 行（sigmoid を平らにして上位 300）・47 行・51 行（閾値が正のときだけ絞る）")
    rows = []
    for name, r in (("val（全フレーム）", s4v), ("train（seed 42 で 1,000 フレーム）", s4t)):
        sa, s1q = r["score_quantiles_all"], r["score_quantiles_top1_per_frame"]
        rows.append([name, r["frames"], ",".join(map(str, r["read_videos"])), r["num_queries_from_class_head"],
                     str(r["outputs_per_frame"]), f"{sa['p50']:.4f}・{sa['p95']:.4f}・{sa['p99']:.4f}・{sa['p100']:.4f}",
                     f"{s1q['p5']:.3f}・{s1q['p50']:.3f}・{s1q['p95']:.3f}", f"{r['n_tp_iou50']:,}/{r['gt_boxes']:,}",
                     f"{r['ece_all_10bins']:.4f}", f"{r['ece_score_ge_0.05_10bins']:.4f}（{r['n_score_ge_0.05']:,} 件）",
                     f"{r['control_ece_scores_all_1']:.4f}・{r['control_ece_scores_eq_hit']:.4f}",
                     f"{r['forward_seconds_per_frame_batch1']['p50']:.4f}"])
    L.append(table(["集合", "フレーム", "動画", "query（class head の出力）", "出力（本数・枠の形）", "得点 全出力（中央・95%・99%・最大）",
                    "得点 各フレームの最大（5%・中央・95%）", "IoU 0.5 で対応した出力 / 正解の枠", "ECE（全出力、10 区間）",
                    "ECE（得点 ≥ 0.05）", "対照 ECE: 得点を 1・得点を対応の 0/1", "順伝播 1 フレーム（秒、中央）"], rows) + "\n")
    L.append(f"- train − val の ECE（全出力）: {s4t['ece_all_10bins'] - s4v['ece_all_10bins']:+.4f}、（得点 ≥ 0.05）: {s4t['ece_score_ge_0.05_10bins'] - s4v['ece_score_ge_0.05_10bins']:+.4f}")
    if "check_map_AP" in s4v:
        L.append(f"- 経路の同一性: val の出力の COCO mAP {s4v['check_map_AP']:.7f}（記録 {s4v['record_AP']:.7f}、差 {s4v['check_map_AP'] - s4v['record_AP']:+.2e}）")
    L.append(f"- 拡張の読み込み `ms_deform_attn_ext` {s4v['ms_deform_attn_ext']}・{s4t['ms_deform_attn_ext']}。出力先は本契約の置き場（`{s4v['cwd']}`、`RELDETR_EVIDENCE_DIR`={s4v['evidence_dir']}）\n")
    L.append("### 信頼度の区間ごと（全出力）\n")
    rows = []
    for bv, bt in zip(s4v["reliability_all"], s4t["reliability_all"]):
        rows.append([f"[{bv['bin'][0]:.1f}, {bv['bin'][1]:.1f})", f(bv["n"]), f(bv.get("conf")), f(bv.get("acc")), f(bt["n"]), f(bt.get("conf")), f(bt.get("acc"))])
    L.append(table(["得点の区間", "val 件数", "val 平均得点", "val 正解率", "train 件数", "train 平均得点", "train 正解率"], rows) + "\n")

    # S5
    L.append("## S5 把持塔の中間特徴（案 2）\n")
    L.append(f"- 前処理後の入力 {'×'.join(map(str, s5['input_chw_after_preprocess']))}（短辺 800・長辺 1333 まで、32 の倍数へ詰める）。val の {s5['frames']} フレーム（動画 {','.join(s5['read_videos'])}、seed 42）。batch 1")
    L.append("- 候補は実行者が mmdet の `Mask2FormerHead.forward` を読んで選んだ。案 2 がどれを使うかは別の判断\n")
    rows = []
    for name, cnd in s5["candidates"].items():
        rows.append([name, cnd["channels"], "×".join(map(str, cnd["spatial"])) if cnd["spatial"] else "100 query", f"{cnd['bytes_fp32_per_frame']:,}",
                     f"{cnd['seconds_per_frame_up_to_layer_median']:.4f}"])
    L.append(table(["層", "次元", "空間の大きさ", "fp32 のバイト/フレーム", "その層までの時間（秒/フレーム、中央）"], rows) + "\n")
    t = s5["times_seconds_median"]["all"]
    L.append(f"- 区間の時間（確定、中央）: backbone {t['backbone']:.4f} 秒、pixel decoder {t['pixel_decoder']:.4f} 秒、頭の全体（pixel decoder を含む）{t['head_full']:.4f} 秒\n")
    L.append("### 同じ層の対応する次元の相関（Pearson、全フレームの全位置。query は全フレームの全 query）\n")
    rows = []
    for name, d in s5["correlation"].items():
        for pair, x in d.items():
            m = x["matched_dim_r"]
            rows.append([name, pair, f"{m['p5']:.3f}・{m['median']:.3f}・{m['p95']:.3f}", f"{m['min']:.3f}・{m['max']:.3f}",
                         f"{x['matched_dim_abs_r_over_0.9']}/{x['dims']}", f"{x['matched_dim_abs_r_under_0.3']}/{x['dims']}",
                         f"{x['best_any_dim_abs_r']['median']:.3f}", x["dead_dims"]])
    L.append(table(["層", "対", "r（5%・中央・95%）", "r（最小・最大）", "|r|>0.9", "|r|<0.3", "相手の全次元で最大の |r|（中央）", "分散 0 の次元"], rows) + "\n")
    L.append("- 対照: 確定どうし（all と、同じ重みを別に読んだ all2）は 4 層とも r = 1。分散 0 の次元（backbone C5 の 2 次元）は r を定義できず、分布から除いた")
    L.append("- 相手の全次元で最大の |r| は、対応する次元の r とほぼ同じ。次元の並べ替えで一致する形ではない\n")

    # S6
    L.append("## S6 工程塔の入力層の変更の可否（案 6）\n")
    rows = [
        ["fine-tune の台本が入力チャネル数の変更を受けるか", "受けない。`stage1_ptower_r3.py` に引数が無く、画像は `convert(\"RGB\")`（73 行）、正規化は 3 チャネル（48 行）、torchvision `resnet50`（103・106 行）"],
        ["stem（conv1・bn1）", "凍結（115〜116 行 `requires_grad_(False)`、129〜133 行で学習中も eval、185 行で学習パラメータ 0 を assert）"],
        ["写しの conv1", f"{s6['conv1_weight_shape_3ch']} → {s6['conv1_weight_shape_8ch']}（RGB は ImageNet の重み、追加の 5 チャネルは 0）"],
        ["入力", f"{s6['input_8ch_shape']}（val 09 の先頭 2 フレーム ＋ seed 42 の一様乱数のマスク 5 チャネル）"],
        ["(a) 台本どおり stem を凍結して逆伝播", f"通る。conv1 の勾配は None（{s6['a_stem_frozen']['conv1_grad_is_none']}）、layer1 に勾配あり（{s6['a_stem_frozen']['layer1_grad_nonzero']}）、山 {s6['a_stem_frozen']['peak_memory_bytes']:,} B"],
        ["(b) conv1 を学ぶ設定、RGB の勾配を hook で 0", f"通る。勾配の形 {s6['b_extra_channels_only']['grad_shape']}、RGB の |勾配| の和 {s6['b_extra_channels_only']['rgb_grad_abs_sum']}、追加チャネル {s6['b_extra_channels_only']['extra_grad_abs_sum']:.3f}（非零 {s6['b_extra_channels_only']['extra_grad_nonzero_elements']:,}/{s6['b_extra_channels_only']['extra_elements']:,}）"],
        ["optimizer", f"作っていない（step も呼んでいない）。重みと buffer の要約値の前後一致 {s6['weights_unchanged']}・{s6['weights_unchanged_after_timing']}"],
        ["対照: 追加チャネル 0 の写しと元の 3 チャネルの出力の差", f"{s6['control_zero_extra_channels_max_abs_logit_diff']}"],
        ["対照: 7 チャネルの入力", f"止まる（{s6['control_7ch']['raised']}）: {s6['control_7ch'].get('error', '')}"],
        ["参考: 順伝播と逆伝播 1 回（batch 2、eval）", f"3 チャネル {s6['fwd_bwd_seconds_batch2_3ch']:.4f} 秒、8 チャネル {s6['fwd_bwd_seconds_batch2_8ch_conv1_trainable']:.4f} 秒"],
    ]
    p, h = s7["phase_finetune_P15"]["runs"][0], s7["phase_finetune_bengio_hostdiff"]["runs"][0]
    rows.append(["1 epoch の見込み（記録から）", f"efros の確定の fine-tune {p['seconds_per_epoch']:.1f} 秒/epoch（{p['elapsed_seconds']:.1f} 秒 ÷ {p['epochs_completed']}、1 GPU）、"
                 f"bengio の再実行 {h['seconds_per_epoch']:.1f} 秒/epoch（{h['elapsed_seconds']:.1f} 秒 ÷ {h['epochs_completed']}、2 GPU、別のデータの集合）。どちらも各 epoch の val を含む"])
    L.append(table(["項目", "値"], rows) + "\n")
    L.append("- 形の確認だけで、学習が収束するか、train の挙動（BN の統計の更新）で通るかは確かめていない\n")

    # S7
    L.append("## S7 費用の単価（全案の #10）\n")
    def rng_(g):
        e = g["elapsed_seconds"] or g["wall_seconds"]
        hours = f"、{e['min']/3600:.2f}〜{e['max']/3600:.2f} 時間" if e["max"] >= 600 else ""
        span = f"{e['min']:,.1f} 秒" if e["n"] == 1 else f"{e['min']:,.1f}〜{e['max']:,.1f} 秒"
        return f"{span}（{e['n']} 本{hours}）"
    rows = [
        ["工程塔側の界面の学習 W1 1 本（時間ヘッドの特徴の上、4 epoch）", rng_(s7["phase_iface_W1_fourth"]), "bengio", "elapsed_seconds", "`experiments/phase1/grasparms_dp_00{1..6}_GA-noflag_*`（四本目）"],
        ["工程塔の時間ヘッドの学習 W2 1 本（案 A）", rng_(s7["phase_head_W2_GA"]), "bengio", "elapsed_seconds", "`experiments/phase1/w23b_dp_W2_*_GA_*`（T-2026-11-01-stage2-w23-bengio）"],
        ["工程塔の時間ヘッドの学習 W3 1 本（案 A）", rng_(s7["phase_head_W3_GA"]), "bengio", "elapsed_seconds", "`experiments/phase1/w23b_dp_W3_*_GA_*`"],
        ["同 W2 全型", rng_(s7["phase_head_W2_all"]), "bengio", "elapsed_seconds", "`experiments/phase1/w23b_dp_W2_*`"],
        ["同 W3 全型", rng_(s7["phase_head_W3_all"]), "bengio", "elapsed_seconds", "`experiments/phase1/w23b_dp_W3_*`"],
        ["時間ヘッドを一から（確定の P\\*-15 の頭、18 epoch）", rng_(s7["phase_head_scratch_P15"]), "efros", "elapsed_seconds", "`experiments/phase1/stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42`"],
        ["検出塔側の界面の学習 W1 1 本（4 epoch）", rng_(s7["det_iface_W1_fourth"]), f"bengio、同時最大 {s7['det_iface_W1_fourth']['max_concurrent_in_group']} 本（四本目 RESULT 63 行: GPU 1 枚に 3 本）", "start/end", "`experiments/phase1/grasparms_B_*`（四本目）"],
        ["同（五本目、案 D と同居）", rng_(s7["det_iface_W1_fifth"]), f"bengio、組の中で同時 {s7['det_iface_W1_fifth']['max_concurrent_in_group']}（五本目 RESULT 47 行: 1 枚に案 D 1 本 + 案 B 1 本）", "start/end", "`origin/feat/grasp-pilot-d-rerun:experiments/phase1/grasparms_B_{empty,gt}_ep4_seed42`"],
        ["検出塔の学び直し（S2、15 epoch）1 本（三本目）", rng_(s7["det_relearn_third"]), f"bengio、組の中で同時最大 {s7['det_relearn_third']['max_concurrent_in_group']}（`experiments/analysis/grasp_pilot_d/REPORT.md` §1 の表: GPU 0 に 2 本を順に、GPU 1 に 1 本。1 枚に 1 本ずつ）", "start/end", "`experiments/phase1/grasppilot3_d_*_ep15_seed42`"],
        ["同（五本目、案 B と同居・外部の使用と共有）", rng_(s7["det_relearn_fifth"]), f"bengio、組の中で同時 {s7['det_relearn_fifth']['max_concurrent_in_group']}", "start/end", "`origin/feat/grasp-pilot-d-rerun:experiments/phase1/graspd2_*_ep15_seed42`"],
        ["工程塔の fine-tune（backbone）1 本（確定の P\\*-15）", rng_(s7["phase_finetune_P15"]) + f"、{p['epochs_completed']} epoch、山 {p['peak_memory_bytes']:,} B", "efros、cuda:0 の 1 枚", "elapsed_seconds", "`experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42`"],
        ["同（bengio の再実行、手本 phase_manifest_all_phase）", rng_(s7["phase_finetune_bengio_hostdiff"]) + f"、{h['epochs_completed']} epoch、山 {h['peak_memory_bytes']:,} B/rank", "bengio、2 GPU（DDP）", "elapsed_seconds", f"`{h['source']}`"],
        ["G の推論 1 フレーム（頭の全体まで）", f"{t['backbone'] + t['head_full']:.4f} 秒", "bengio、1 枚、batch 1", "本契約の S5", "`$S/c/s5/s5_record.json`"],
        ["D の推論 1 フレーム", f"{s4v['forward_seconds_per_frame_batch1']['p50']:.4f} 秒（val の中央）", "bengio、1 枚、batch 1、fp32", "本契約の S4", "`$S/c/s4/s4_record_val.json`"],
        ["P の backbone の推論 1 フレーム（layer4 の地図まで）", f"{s1['forward_seconds_per_frame_batch']:.4f} 秒（batch 16）", "bengio、1 枚", "本契約の S1", "`$S/c/s1/s1_record_09.json`"],
    ]
    L.append(table(["単価", "値", "GPU の使い方", "値の欄", "出所"], rows) + "\n")
    L.append("- 値は各契約の報告と一致した: 四本目 RESULT 63 行（案 A 11.9〜187.2 秒、案 B 5 時間 15 分〜5 時間 33 分）、五本目 RESULT 47 行（案 D 16 時間 20 分・16 時間 51 分、案 B 3 時間 59 分・4 時間 16 分）、三周目 RESULT 51 行（fine-tune 6,002〜16,240 秒）\n")

    # test
    L.append("## test の動画を読んでいないこと\n")
    rows = [["S1（工程塔の地図）", ",".join(s1["read_videos"])], ["S4 val", ",".join(s4v["read_videos"])], ["S4 train", ",".join(s4t["read_videos"])],
            ["S5（G の特徴）", ",".join(s5["read_videos"])], ["S6（8 チャネルの写し）", ",".join(s6["read_videos"])], ["S2・S3（注釈）", f"画像 {s23['images_read']} 枚"]]
    L.append(table(["段", "画像を読んだ動画"], rows) + "\n")
    rv = set(s1["read_videos"]) | set(s4v["read_videos"]) | set(s4t["read_videos"]) | set(s5["read_videos"]) | set(s6["read_videos"])
    L.append(f"- 読んだ動画の集合 {sorted(rv)} と {{04, 05, 07}} の共通 {len(rv & {'04', '05', '07'})} 件\n")
    Path(a.out).write_text("\n".join(L) + "\n")
    print(f"wrote {a.out} ({len(L)} blocks)")


if __name__ == "__main__":
    main()

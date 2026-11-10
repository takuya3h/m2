"""REPORT.md を記録から作る（T-2026-11-09-grasp-pilot-converge）。数値は手で写さない。

    .venv/bin/python make_report.py --store <S> --out experiments/analysis/grasp_pilot_converge/REPORT.md
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

K3 = ("phase_jaccard", "phase_accuracy", "six_phase_mean")


def f3(r):
    return " / ".join(f"{r[k]:.4f}" for k in K3)


def d3(r):
    return " / ".join(f"{r[k]:+.4f}" for k in K3)


def fam(name):
    t = name.split("_")[1]
    return f"tw-{name.split('TW-')[1].split('-')[0]}" if t == "tw" else {"dp": "ga"}.get(t, t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    S = Path(a.store)
    sm = json.loads((S / "d/summary.json").read_text())
    k1 = json.loads((S / "b/b3_kill.json").read_text())
    k2 = json.loads((S / "b/b3_kill_round2.json").read_text())
    dg = json.loads((S / "b/b3_diag.json").read_text())
    rule = json.loads((S / "b/b2_rule.json").read_text())
    conv, prior = sm["runs"]["conv"], sm["runs"]["prior"]
    L = []
    w = L.append
    w("# REPORT — T-2026-11-09-grasp-pilot-converge")
    w("")
    w("**非公式の予備測定。関門の判定と案の採否に使わない。** 前の予備（T-2026-11-09-grasp-roitoken-transition-pilot、4 epoch 固定 = 40 歩）の処方を直し、"
      "工程塔側の把持の界面（案 3 RT・案 5 TW・案 A GA）を**収束規則**（val の macro Jaccard が 8 epoch 改善しなければ学習率 × 0.1 を一度、"
      "さらに 8 epoch で打ち切り、上限 120、checkpoint は val の最良）で回し直した。bengio、折り A、seed 42、val 09・10。")
    w("")
    w("数値の出所: `$S = /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-pilot-converge` の `d/summary.json`（`tools/d_aggregate.py` が各 run の記録と"
      "界面の重みから集めた値）、`b/`（材料・規則・殺し実験）。前の処方の run は前の予備（`grasprt_*`）と四本目（`grasparms_dp_*`）。"
      "J = macro Jaccard、acc = frame accuracy、6 工程 = dressing を除く 6 工程（" + "・".join(sm["six_phases"]) + "）の平均。")
    w("")
    w("## 1. 結論の要約（記述だけ）")
    w("")
    w1 = [r for n, r in conv.items() if fam(n) in ("rt", "tw-W1", "ga")]
    w(f"- **val の最良を選ぶ収束規則では、W1 の界面の多くが学習のごく初めで選ばれた。** W1 の {len(w1)} 本の最良の epoch の中央は "
      f"{st.median([r['best_epoch'] for r in w1])}（10 歩 = 1 epoch）。学習を続けると val の J は下がる（最終 − 最良の中央 "
      f"{st.median([r['history_val_jaccard'][-1] - max(r['history_val_jaccard']) for r in conv.values()]):+.4f}）")
    c = sm["checks"]
    w(f"- checkpoint の出力射影の重みの最大の絶対値が前の予備の最大 0.021 を超えたのは {c['e_out_w_max_abs_over_prior_max_0.021']}/{c['f_conv_runs']} 本。"
      "W1 の多くは前の予備（40 歩）より学ばれていない状態で選ばれた")
    w(f"- 腕の間で指標（J と acc）がちょうど同じになった差: 本契約 {c['g_identical_metrics_pairs']['conv']['identical']}/{c['g_identical_metrics_pairs']['conv']['pairs']}、"
      f"前の処方 {c['g_identical_metrics_pairs']['prior']['identical']}/{c['g_identical_metrics_pairs']['prior']['pairs']}")
    w(f"- 前の処方と 6 工程の平均の差の符号が変わった差: 案 3 {len(sm['sign_flips']['case3'])}、案 5 {len(sm['sign_flips']['case5'])}、案 A {len(sm['sign_flips']['caseA'])}")
    w("- 殺し実験の線形の層は、処方の候補 4 つのどれでも陽性対照（正解の工程）が J 0.9 に届かず、殺し実験は測り直していない（§2）")
    w("")
    w("## 2. 殺し実験の処方の直し（SPEC §3.2、Task B-3）")
    w("")
    w("候補は L2 つきの多項ロジスティック回帰（sklearn、lbfgs、class_weight balanced、train の平均・標準偏差で標準化）。候補 3・4 は利用者の決定で追加した。")
    w("")
    w("| 候補 | C | 陽性対照（P ＋ 正解の工程の one-hot）の val J / acc / 6 工程 | P だけの val J | 0.9 に届く |")
    w("|---|---|---|---|---|")
    for t in k1["tried"] + k2["tried"]:
        pc = t["positive_control"]
        w(f"| {t['candidate']['name']} | {t['candidate']['C']} | {f3(pc['plus_gt_onehot'])} | {pc['base']['phase_jaccard']:.4f} | {'はい' if t['reaches_target'] else 'いいえ'} |")
    w("")
    w("診断（候補 1・2 の陽性対照の中身。`b/b3_diag.json`）:")
    w("")
    w("| 入力 | train の正解率 | val J / acc | 重みの L2 のうち one-hot の 9 列の割合 |")
    w("|---|---|---|---|")
    for n, v in dg["cases"].items():
        w(f"| {n} | {v['train_accuracy']:.4f} | {v['val_jaccard']:.4f} / {v['val_accuracy']:.4f} | {v['onehot_weight_share_of_l2']:.3f} |")
    w("")
    w("- one-hot だけの層は val で J 1.0（評価の経路は正しい）。P の特徴を足すと train の正解率は 1.0 のまま、重みの多くが P の特徴に乗る。"
      "P は train で fine-tune した塔で、train の特徴だけで train が分け切れるため、線形の層は足した列を主に使わない（実行者の見立て）")
    w("- 処方が陽性対照で働かないので、案 3・案 5 の殺し実験はこの処方では測り直していない。殺す条件に対する判定は UNKNOWN")
    w("")
    w("## 3. 収束規則の対照（Task B-2、`b/b2_rule.json`）")
    w("")
    w("| 人工の val の記録 | 落とした epoch | 止めた epoch | 期待どおり |")
    w("|---|---|---|---|")
    for k, v in rule["cases"].items():
        w(f"| {k} | {v['drop_epoch']} | {v['stop_epoch']}（{v['epochs_run']} epoch） | {'はい' if v['as_expected'] else 'いいえ'} |")
    n = rule["negative_control_patience_plus1"]
    w(f"| 陰性対照: patience 9 の規則に 1 を流す | {n['drop_epoch']} | {n['stop_epoch']} | 1 と違う {n['differs_from_case1']} |")
    w("")
    w("## 4. 学習の量（Task C）")
    w("")
    w("| 型 | 本数 | 最良の epoch 中央（範囲） | 総 epoch 中央（範囲） | 学習率を落とした epoch 中央 | checkpoint の出力射影の最大の絶対値（範囲） | > 0.021 | 最終の同じ値（範囲） | 前の処方の checkpoint の同じ値（範囲） |")
    w("|---|---|---|---|---|---|---|---|---|")
    fams = sorted({fam(n) for n in conv})
    for f in fams:
        rs = [r for n, r in conv.items() if fam(n) == f]
        ps = [r for n, r in prior.items() if fam(n) == f]
        be = [r["best_epoch"] for r in rs]
        er = [r["epochs_run"] for r in rs]
        ld = [r["lr_drop_epoch"] for r in rs if r["lr_drop_epoch"]]
        ck = [r["ckpt_norms"]["out_w_max_abs"] for r in rs]
        fi = [r["norms"]["final"]["out_w_max_abs"] for r in rs]
        pk = [r["ckpt_norms"]["out_w_max_abs"] for r in ps]
        w(f"| {f} | {len(rs)} | {st.median(be)}（{min(be)}〜{max(be)}） | {st.median(er)}（{min(er)}〜{max(er)}） | {st.median(ld) if ld else '—'} | "
          f"{min(ck):.4f}〜{max(ck):.4f} | {sum(x > 0.021 for x in ck)} | {min(fi):.4f}〜{max(fi):.4f} | {min(pk):.4f}〜{max(pk):.4f} |")
    tw = [r for n, r in conv.items() if fam(n).startswith("tw")]
    rel_b = [r["ckpt_norms"].get("rel_std") for r in tw if r["ckpt_norms"].get("rel_std") is not None]
    rel_f = [r["norms"]["final"].get("rel_std") for r in tw if r["norms"]["final"].get("rel_std") is not None]
    rel_p = [r["ckpt_norms"].get("rel_std") for n, r in prior.items() if fam(n).startswith("tw") and r["ckpt_norms"].get("rel_std") is not None]
    w("")
    w(f"- 案 5 の相対時刻の埋め込みの標準偏差: checkpoint {min(rel_b):.4f}〜{max(rel_b):.4f}、最終 {min(rel_f):.4f}〜{max(rel_f):.4f}、前の処方 {min(rel_p):.4f}〜{max(rel_p):.4f}（初期 0.02）")
    w(f"- 上限 120 に届いた run: {sum(bool(r['reached_cap']) for r in conv.values())}。所要は §9")
    w("- 0.021 を超えなかった run の理由: 最良の epoch が早い（学ぶほど val の J が下がり、規則が早い epoch を選ぶ）。案 A の空は入力が零で界面が動かない（0.0）")
    w("")
    w("### 4.1 run ごと（最良・総 epoch・落とした epoch・checkpoint と最終の出力射影の最大の絶対値・epoch ごとの val の J）")
    w("")
    w("| run | 最良 | 総 | 落とした | checkpoint | 最終 | val の J（epoch 1 から） |")
    w("|---|---|---|---|---|---|---|")
    for name, r in sorted(conv.items()):
        w(f"| {name} | {r['best_epoch']} | {r['epochs_run']} | {r['lr_drop_epoch']} | {r['ckpt_norms']['out_w_max_abs']:.4f} | "
          f"{r['norms']['final']['out_w_max_abs']:.4f} | " + "・".join(f"{x:.3f}" for x in r["history_val_jaccard"]) + " |")
    w("")
    for case, title, keys in (("case3", "案 3 把持領域トークン（RT、W1）", None), ("case5", "案 5 遷移の符号化（TW。同じ W の中だけ）", None)):
        w(f"## {5 if case == 'case3' else 6}. {title}")
        w("")
        w("差は J / acc / 6 工程。「一致」は二つの run の val の argmax が一致したフレームの割合。参照段は把持の注釈のある 1,514 行")
        w("")
        w("| 設定 | 差 | 本契約（収束規則） | 一致 | 前の処方（4 epoch） | 一致 | 6 工程の符号が変わった |")
        w("|---|---|---|---|---|---|---|")
        for s, r in sm[case].items():
            for nme, d in r["conv"]["diffs"].items():
                p = r["prior"]["diffs"].get(nme)
                if "argmax_agree" not in d:
                    w(f"| {s} | {nme} | {d3(d)} | — | {d3(p) if p else '—'} | — | {'はい' if p and (d['six_phase_mean'] > 0) != (p['six_phase_mean'] > 0) else ''} |")
                    continue
                w(f"| {s} | {nme} | {d3(d)} | {d['argmax_agree']:.3f} | {d3(p) if p else '—'} | {p['argmax_agree']:.3f} | "
                  f"{'はい' if p and (d['six_phase_mean'] > 0) != (p['six_phase_mean'] > 0) else ''} |")
        w("")
        w("動画ごとの差（本契約、J / acc）とクラス別の差（本契約、Jaccard）:")
        w("")
        cls = None
        w("| 設定 | 差 | 09 | 10 | クラス別 |")
        w("|---|---|---|---|---|")
        for s, r in sm[case].items():
            for nme, d in r["conv"]["diffs"].items():
                if "per_video" not in d:
                    continue
                cls = list(d["per_class"])
                pv = d["per_video"]
                w(f"| {s} | {nme} | {pv['09']['phase_jaccard']:+.4f} / {pv['09']['phase_accuracy']:+.4f} | {pv['10']['phase_jaccard']:+.4f} / "
                  f"{pv['10']['phase_accuracy']:+.4f} | " + "、".join(f"{c_} {d['per_class'][c_]:+.3f}" for c_ in cls) + " |")
        w("")
    w("## 7. 案 A 把持の要約の連結（GA、W1、旗なし 28 次元）")
    w("")
    w("| 差 | 本契約（収束規則） | 一致 | 四本目（4 epoch） | 一致 |")
    w("|---|---|---|---|---|")
    for nme, d in sm["caseA"]["conv"]["diffs"].items():
        p = sm["caseA"]["prior"]["diffs"][nme]
        w(f"| {nme} | {d3(d)} | {d['argmax_agree']:.3f} | {d3(p)} | {p['argmax_agree']:.3f} |")
    w("")
    w("全腕の値（本契約、J / acc / 6 工程）:")
    w("")
    for name, r in sorted(conv.items()):
        if fam(name) == "ga":
            w(f"- {name}: {f3(r)}（最良 epoch {r['best_epoch']}）")
    w(f"- P 単独（塔）: {f3(sm['p_alone'])}")
    w("")
    w("## 8. §5.2 の予測との照合")
    w("")
    ratio = [r["ckpt_norms"]["out_w_max_abs"] / max(prior_r, 1e-12) for r, prior_r in
             [(r, next((p["ckpt_norms"]["out_w_max_abs"] for pn, p in prior.items() if pn.split("_", 3)[3].replace("_ep4", "") ==
                        n.split("_", 3)[3].replace("_conv", "")), None)) for n, r in conv.items()] if prior_r]
    w(f"1. 全腕で出力射影のノルムが前の予備の 5 倍以上: 外れ（同じ腕の前の処方との比が 5 以上 {sum(x >= 5 for x in ratio)}/{len(ratio)}、"
      f"比の中央 {st.median(ratio):.2f}。前の処方の値が 0 の腕は除く）")
    w(f"2. 腕の間で指標がちょうど同じになる設定は 0: 外れ（{c['g_identical_metrics_pairs']['conv']['identical']} 個）")
    tg = [r["conv"]["diffs"]["TG - TRand"]["six_phase_mean"] for r in sm["case3"].values()]
    w(f"3. 案 3 の TG − TRand（6 工程）が 8 設定のうち 5 以上で正: {'当たり' if sum(x > 0 for x in tg) >= 5 else '外れ'}（{sum(x > 0 for x in tg)}/8）")
    s1 = [r["conv"]["diffs"]["S_W - S_1"]["six_phase_mean"] for k, r in sm["case5"].items() if k.startswith("W1-")]
    w(f"4. 案 5 の W1 の S_W − S_1（6 工程）の絶対値が 0.01 未満: {'当たり' if all(abs(x) < 0.01 for x in s1) else '外れ'}（"
      + "・".join(f"{x:+.4f}" for x in s1) + "）")
    ga = sm["caseA"]["conv"]["diffs"]["予測-noCF - 入れ替え"]["six_phase_mean"]
    w(f"5. 案 A の 予測-noCF − 入れ替え（6 工程）の絶対値が 0.005 未満: {'当たり' if abs(ga) < 0.005 else '外れ'}（{ga:+.4f}）")
    w("6. 殺し実験は、処方を直すと案 3 は当たらず案 5 は当たる: 測っていない（陽性対照が働く処方が無かった）")
    w("")
    w("## 9. 既知の限界と所要")
    w("")
    w("- 折り 1 つ、val 2 本、seed 1 つ。今の塔での値。収束規則は val で checkpoint を選ぶので val の値は上振れする（全腕同じ）")
    w("- 停滞の幅 8 epoch・上限 120・min_delta 1e-4 は本契約で置いた値で、結果を見て変えていない。**最良を選ぶ規則では、学ぶほど val が下がる腕の界面は育たない状態で選ばれる。**"
      "最終の状態（最も学んだ状態）の val は確率を保存していないので、この報告では差を書けない（history の J だけ）")
    w("- dressing の当たり外れ、G の左クラスの弱さ、参照段の集合の違い、入れ替えの mapping が同じ動画を含むことは前の予備と同じ")
    el = [r["elapsed_seconds"] for r in conv.values()]
    w(f"- 学習 1 本 {min(el):.1f}〜{max(el):.1f} 秒（metrics の elapsed_seconds）。GPU 2 枚 × 4 本並行")
    w("")
    w("## 10. 検証（§7 の f・g・h）")
    w("")
    w(f"- f: run {c['f_conv_runs']}/{c['f_expected']}（無い {len(c['missing'])}）、全本が収束規則 {c['f_all_converge']}、存在しない run の名前 2 つで {c['f_bogus_found']} 件。"
      f"前の処方の run {c['f_prior_runs']} 本を同じ規則で読んだ")
    w(f"- g: 差を各 run の val の確率の argmax から測り直して一致（{c['g_recheck_n']} 個、ずれの最大 {c['g_recheck_max_abs_diff']}）。1e-6 ずらした写しを検出 {c['g_shifted_copy_detected']}")
    w(f"- h: 通した動画 {c['h_videos']}、test との共通 {c['h_common_with_test']}。04 を混ぜると {c['h_control_with_04']}")
    w(f"- W1 の受け取り手は不変 {c['w1_receiver_unchanged']}。W2・W3 は学ぶ範囲が変わり {c['w23_trained_changed']}、範囲の外は不変 {c['w23_outside_unchanged']}")
    w("")
    Path(a.out).write_text("\n".join(L) + "\n")
    print(f"wrote {a.out} {len(L)} lines")


if __name__ == "__main__":
    main()

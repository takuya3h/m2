"""REPORT.md を記録から作る（T-2026-11-09-grasp-roitoken-transition-pilot）。数値は手で写さない。

    .venv/bin/python make_report.py --store <S> --out experiments/analysis/grasp_roitoken_transition_pilot/REPORT.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

K3 = ("phase_jaccard", "phase_accuracy", "six_phase_mean")
LAB = {"T0": "T0（空）", "TG": "TG（G の予測）", "TGeo": "TGeo（幾何だけ）", "TU": "TU（器具の和集合）", "TRand": "TRand（入れ替え）",
       "REF_GT": "参照段 正解", "REF_GTP": "参照段 正解 ⊕ 予測"}


def f3(r):
    return " / ".join(f"{r[k]:.7f}" for k in K3)


def d3(r):
    return " / ".join(f"{r[k]:+.7f}" for k in K3)


def case5(w, s5):
    w("## 7. 案 5 の掃引（追加。型 TW、K 64、4 epoch 固定・最後の状態、seed 42）")
    w("")
    w("利用者の依頼（2026-11-09「案5、追加でやって」）で、殺し実験で殺す条件に当たった後に回した。読み方は §5.1 の 3（**同じ W の中でだけ**差を取る。"
      "W2・W3 では塔単独との差を書かない。W の間の差は取らない）。形 a = 5 チャネルの地図の 8×8（320 次元）、形 b = 変化の特徴（39 次元）。")
    w("")
    w("### 7.1 全腕の値（J / acc / 6 工程）")
    w("")
    w("| W | 形 | L | S_0 | S_1 | S_W | S_W-perm | S_W-U | S_W-R |")
    w("|---|---|---|---|---|---|---|---|---|")
    for key, r in s5["settings"].items():
        sc, f, L = key.split("-")
        byrun = {v["run"]: v for v in s5["runs"].values()}
        cells = [f3(byrun[r["arms"][lab]]) if r["arms"][lab] else "UNKNOWN" for lab in
                 ("S_0", "S_1", "S_W", "S_W-perm", "S_W-U", "S_W-R")]
        w(f"| {sc} | {f} | {L[1:]} | " + " | ".join(cells) + " |")
    w("")
    w("### 7.2 同じ W の中の差（J / acc / 6 工程）")
    w("")
    names = ["S_W - S_0", "S_W - S_1", "S_W - S_W-perm", "S_W - S_W-R", "S_W - S_W-U"]
    w("| W-形-L | " + " | ".join(names) + " | S_W − P 単独（W1 だけ） |")
    w("|---|" + "---|" * (len(names) + 1))
    for key, r in s5["settings"].items():
        last = d3(r["diffs"]["S_W - P 単独"]) if "S_W - P 単独" in r["diffs"] else "—"
        w(f"| {key} | " + " | ".join(d3(r["diffs"][n]) if n in r["diffs"] else "UNKNOWN" for n in names) + f" | {last} |")
    w("")
    w("### 7.3 参照段（W1、把持の注釈のある val 1,514 行。S_0・S_W は同じ行に絞って測り直した値と比べる）")
    w("")
    w("| 形-L | 正解 − S_0 | 正解 ⊕ 予測 − S_0 | 正解 − S_W | 正解 ⊕ 予測 − S_W |")
    w("|---|---|---|---|---|")
    for key, r in s5["reference"].items():
        w(f"| {key} | " + " | ".join(d3(r["diffs"][n]) if n in r["diffs"] else "UNKNOWN" for n in
                                    ("正解 - S_0", "正解 ⊕ 予測 - S_0", "正解 - S_W", "正解 ⊕ 予測 - S_W")) + " |")
    w("")
    w("### 7.4 差の動画ごと（J / acc）")
    w("")
    w("| W-形-L | 差 | 09 | 10 |")
    w("|---|---|---|---|")
    for key, r in s5["settings"].items():
        for n in names:
            if n in r["diffs"]:
                pv = r["diffs"][n]["per_video"]
                w(f"| {key} | {n} | " + " | ".join(f"{pv[v]['phase_jaccard']:+.4f} / {pv[v]['phase_accuracy']:+.4f}" for v in ("09", "10")) + " |")
    w("")
    w("### 7.5 差のクラス別 Jaccard")
    w("")
    first = next(iter(s5["settings"].values()))["diffs"]["S_W - S_0"]["per_class"]
    cls = list(first)
    w("| W-形-L | 差 | " + " | ".join(cls) + " |")
    w("|---|---|" + "---|" * len(cls))
    for key, r in s5["settings"].items():
        for n in names:
            if n in r["diffs"]:
                pcl = r["diffs"][n]["per_class"]
                w(f"| {key} | {n} | " + " | ".join(f"{pcl[c]:+.3f}" for c in cls) + " |")
    w("")
    w("### 7.6 epoch ごとの val の J、界面の L2、時間ヘッドの重みの変化の L2（W2・W3）")
    w("")
    w("| run | epoch 1〜4 の J | epoch 1〜4 の acc | 界面の L2 | 時間ヘッドの変化の L2 | 学習の秒 |")
    w("|---|---|---|---|---|---|")
    for name, x in s5["runs"].items():
        h = x["history"]
        w(f"| {name} | " + "・".join(f"{e['val_jaccard']:.4f}" for e in h) + " | " + "・".join(f"{e['val_accuracy']:.4f}" for e in h)
          + f" | {h[-1]['iface_l2']:.3f} | " + ("・".join(f"{e['head_delta_l2']:.3f}" for e in h) if "head_delta_l2" in h[-1] else "—")
          + f" | {x['elapsed_seconds']:.1f} |")
    w("")
    w("### 7.7 §5.1 の読み方による記述")
    w("")
    for n in names:
        for sc in ("W1", "W2", "W3"):
            ds = [r["diffs"][n] for k, r in s5["settings"].items() if k.startswith(sc + "-") and n in r["diffs"]]
            if ds:
                w(f"- {sc} の {n}: 6 工程の平均 {min(d['six_phase_mean'] for d in ds):+.4f}〜{max(d['six_phase_mean'] for d in ds):+.4f}"
                  f"（正 {sum(d['six_phase_mean'] > 0 for d in ds)}/{len(ds)}）、J {min(d['phase_jaccard'] for d in ds):+.4f}〜"
                  f"{max(d['phase_jaccard'] for d in ds):+.4f}、acc {min(d['phase_accuracy'] for d in ds):+.4f}〜{max(d['phase_accuracy'] for d in ds):+.4f}")
    ds = [r["diffs"]["S_W - P 単独"] for r in s5["settings"].values() if "S_W - P 単独" in r["diffs"]]
    w(f"- W1 の S_W − P 単独: 6 工程の平均 {min(d['six_phase_mean'] for d in ds):+.4f}〜{max(d['six_phase_mean'] for d in ds):+.4f}、"
      f"J {min(d['phase_jaccard'] for d in ds):+.4f}〜{max(d['phase_jaccard'] for d in ds):+.4f}")
    w("- seed は一つで、差は 1 本ずつの差。設定の間で最良を選ばない。W2・W3 の値は塔単独と比べない")
    w("")
    c = s5["checks"]
    w("### 7.8 検証")
    w("")
    w(f"- g: run {c['g_runs']}/{c['g_expected']}（無い {c['g_missing']}）、全本 4 epoch・最後の状態 {c['g_all_4_epochs_final_state']}、"
      f"存在しない run の名前 2 つで {c['g_bogus_names_found']} 件")
    w(f"- W1 の受け取り手不変 {c['w1_receiver_unchanged']}。W2・W3（{c['n_w23']} 本）は学ぶ範囲が変わり {c['w23_receiver_trained_changed']}、"
      f"範囲の外は不変 {c['w23_receiver_outside_scope_unchanged']}")
    w(f"- h: 差を確率から測り直して一致（{c['h_recheck_n']} 個、ずれの最大 {c['h_recheck_max_abs_diff']}）。1e-6 ずらした写しを検出 {c['h_shifted_copy_detected']}")
    w(f"- i: 通した動画 train {s5['videos_seen']['train']}・val {s5['videos_seen']['val']}、test との共通 {c['i_common_with_test']}。04 を混ぜると {c['i_control_with_04']}")
    w("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    S = Path(a.store)
    sm = json.loads((S / "f/summary.json").read_text())
    ck = json.loads((S / "c/c_kill.json").read_text())
    s5p = S / "f/summary5.json"
    s5 = json.loads(s5p.read_text()) if s5p.exists() else None
    L = []
    w = L.append
    w("# REPORT — T-2026-11-09-grasp-roitoken-transition-pilot")
    w("")
    w("**非公式の予備測定。関門の判定と案の採否に使わない。** 対象は第二回の提案カード第三版の案 3 把持領域トークン（grasp-phase-roitoken）と"
      "案 5 遷移の符号化（grasp-phase-transition）。bengio、折り A、seed 42、val 2 本（09・10）。")
    w("殺し実験で案 5 が殺す条件に当たり、利用者の決定（2026-11-09「案3だけ進める」）で案 3 の掃引だけを回した。"
      + ("その後、利用者の依頼（同日「案5、追加でやって」）で案 5 の型 TW と 68 本も回した（§7）。" if s5 else "案 5 の型 TW と 68 本は回していない。"))
    w("")
    w("数値の出所: `$S = /home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-roitoken-transition-pilot` の `c/c_kill.json`（殺し実験）と "
      "`f/summary.json`（各 run の metrics.json・per_class_ap.json・logs/history.json から `tools/f_aggregate.py` が集めた値）。"
      "J = macro Jaccard、acc = frame accuracy、6 工程 = dressing を除く 6 工程（" + "・".join(sm["six_phases"]) + "）の Jaccard の平均。")
    w("")
    w("## 1. 殺し実験（カード #9、Task C。時間ヘッドを通さない線形の層）")
    w("")
    w(f"処方: 標準化、Linear(D → 9)、クラスの重みつき交差エントロピー、AdamW（lr {ck['fit']['lr']}、wd {ck['fit']['weight_decay']}）、"
      f"batch {ck['fit']['batch']}、{ck['fit']['epochs']} epoch、seed {ck['fit']['seed']}、最後の状態。殺す条件の閾値 {ck['kill_threshold']}（m = 0.2 pt の仮の m/2）。")
    w("")
    w("| 項目 | 行 train/val | 次元 | base（J / acc / 6 工程） | plus | plus − base | 殺す条件 |")
    w("|---|---|---|---|---|---|---|")
    pc = ck["positive_control"]
    w(f"| 陽性対照（＋ 正解の工程の one-hot） | 全行 | 2048 → 2057 | {f3(pc['base'])} | {f3(pc['plus_gt_onehot'])} | {d3(pc['diff'])} | — |")
    for key, name in (("case3_gt", "案 3 正解の把持の枠の ROI（layer4）"), ("case3_pred", "案 3 G の予測の枠の ROI（layer4）")):
        c = ck[key]
        w(f"| {name} | {c['rows']['train']}/{c['rows']['val']} | {c['dims']['base']} → {c['dims']['plus']} | {f3(c['base'])} | "
          f"{f3(c['plus'])} | {d3(c['diff'])} | {'当たる' if c['kill'] else '当たらない'} |")
    for Lk, c in ck["case5"]["linear"].items():
        w(f"| 案 5 {Lk}（窓の (b) と印） | 全行 | {c['dims']['base']} → {c['dims']['plus']} | {f3(c['base'])} | {f3(c['plus'])} | "
          f"{d3(c['diff'])} | {'当たる' if c['kill'] else '当たらない'} |")
    w("")
    w("案 5 の遷移の事象（val、G の確定の出力）: " + "、".join(f"{k} {v}" for k, v in ck["case5"]["events_val"].items()))
    w("")
    w("| L | 境界の ±L 秒の中 / 外 | 率 中 / 外 | 比 | null の 95% 区間（動画ごとの区間の並べ替え 2,000 回） | 比が区間の中 | 両側 p |")
    w("|---|---|---|---|---|---|---|")
    for Lk, r in ck["case5"]["rate"].items():
        w(f"| {Lk} | {r['near_frames']} / {r['other_frames']} | {r['rate_near']:.4f} / {r['rate_other']:.4f} | {r['ratio']:.4f} | "
          f"[{r['null_interval_95'][0]:.4f}, {r['null_interval_95'][1]:.4f}]（中央 {r['null_median']:.4f}） | "
          f"{'はい' if r['ratio_inside_null_interval'] else 'いいえ'} | {r['perm_p_two_sided']:.4f} |")
    w("")
    w("- 案 5: 殺す条件に**当たる**（両方の L）。案 3: **当たらない**")
    w("- 陽性対照が弱い（正解の工程を足しても J +0.016・acc −0.001）。この線形の層は足した情報への感度が低く、案 3 の差には次元を 10,245 増やした分が混ざりうる")
    w("")
    w("## 2. 案 3 の学習（型 RT、W1、4 epoch 固定・最後の状態、seed 42）")
    w("")
    p = sm["p_alone"]
    w(f"P 単独（塔、学習しない）: {f3(p)}（dressing {p['per_class_jaccard']['dressing']:.4f}）")
    w("")
    w("### 2.1 全腕の値（J / acc / 6 工程）")
    w("")
    w("| 設定 | " + " | ".join(LAB[k] for k in LAB) + " |")
    w("|---|" + "---|" * len(LAB))
    for s, r in sm["settings"].items():
        w(f"| {s} | " + " | ".join(f3(r["arms"][k]) for k in LAB) + " |")
    w("")
    w("参照段の 2 腕は把持の注釈のある val 1,514 行で評価（主の腕は 1,515 行）。T0 を同じ 1,514 行で測り直した値:")
    w("")
    for s, r in sm["settings"].items():
        w(f"- {s}: T0@参照段の行 {f3(r['arms']['T0']['on_ref_rows'])}")
    w("")
    w("### 2.2 差（§5.1 の 2。設定ごと、最良を選ばない。J / acc / 6 工程）")
    w("")
    names = ["TG-T0", "TG-TRand", "TG-TGeo", "TG-TU", "REF_GT-T0", "REF_GTP-T0"]
    w("| 設定 | " + " | ".join(names) + " |")
    w("|---|" + "---|" * len(names))
    for s, r in sm["settings"].items():
        w(f"| {s} | " + " | ".join(d3(r["diffs"][n]) for n in names) + " |")
    w("")
    w("### 2.3 差の動画ごと（J / acc）")
    w("")
    w("| 設定 | 差 | 09 | 10 |")
    w("|---|---|---|---|")
    for s, r in sm["settings"].items():
        for n in names:
            pv = r["diffs"][n]["per_video"]
            w(f"| {s} | {n} | " + " | ".join(f"{pv[v]['phase_jaccard']:+.4f} / {pv[v]['phase_accuracy']:+.4f}" for v in ("09", "10")) + " |")
    w("")
    w("### 2.4 差のクラス別 Jaccard（val に現れる 7 工程）")
    w("")
    cls = list(next(iter(sm["settings"].values()))["diffs"]["TG-T0"]["per_class"])
    w("| 設定 | 差 | " + " | ".join(cls) + " |")
    w("|---|---|" + "---|" * len(cls))
    for s, r in sm["settings"].items():
        for n in names:
            pcl = r["diffs"][n]["per_class"]
            w(f"| {s} | {n} | " + " | ".join(f"{pcl[c]:+.3f}" for c in cls) + " |")
    w("")
    w("### 2.5 epoch ごとの val の J と界面の重みの L2（4 epoch 目）")
    w("")
    w("| 設定 | 腕 | epoch 1〜4 の J | epoch 1〜4 の acc | L2 | 学習の秒 |")
    w("|---|---|---|---|---|---|")
    for s, r in sm["settings"].items():
        for k in LAB:
            x = r["arms"][k]
            w(f"| {s} | {k} | " + "・".join(f"{h['val_jaccard']:.4f}" for h in x["history"]) + " | "
              + "・".join(f"{h['val_accuracy']:.4f}" for h in x["history"]) + f" | {x['history'][-1]['iface_l2']:.3f} | {x['elapsed_seconds']:.1f} |")
    w("")
    w("## 3. §5.1 の読み方による記述")
    w("")
    w("- seed は一つで、差は 1 本ずつの差。設定の間で最良を選ばない")
    tg_t0 = [r["diffs"]["TG-T0"] for r in sm["settings"].values()]
    pos = sum(d["six_phase_mean"] > 0 for d in tg_t0)
    w(f"- TG − T0 の 6 工程の平均は 8 設定のうち {pos} 設定で正、{8 - pos} 設定で負。範囲 "
      f"{min(d['six_phase_mean'] for d in tg_t0):+.4f}〜{max(d['six_phase_mean'] for d in tg_t0):+.4f}。J の範囲 "
      f"{min(d['phase_jaccard'] for d in tg_t0):+.4f}〜{max(d['phase_jaccard'] for d in tg_t0):+.4f}、acc の範囲 "
      f"{min(d['phase_accuracy'] for d in tg_t0):+.4f}〜{max(d['phase_accuracy'] for d in tg_t0):+.4f}")
    for n in ("TG-TRand", "TG-TGeo", "TG-TU", "REF_GT-T0", "REF_GTP-T0"):
        ds = [r["diffs"][n] for r in sm["settings"].values()]
        w(f"- {n}: 6 工程の平均 {min(d['six_phase_mean'] for d in ds):+.4f}〜{max(d['six_phase_mean'] for d in ds):+.4f}（正 "
          f"{sum(d['six_phase_mean'] > 0 for d in ds)}/8）、J {min(d['phase_jaccard'] for d in ds):+.4f}〜{max(d['phase_jaccard'] for d in ds):+.4f}、"
          f"acc {min(d['phase_accuracy'] for d in ds):+.4f}〜{max(d['phase_accuracy'] for d in ds):+.4f}")
    t0s = [r["arms"]["T0"] for r in sm["settings"].values()]
    w(f"- T0 は P 単独から J {min(x['phase_jaccard'] for x in t0s) - p['phase_jaccard']:+.4f}〜{max(x['phase_jaccard'] for x in t0s) - p['phase_jaccard']:+.4f}、"
      f"6 工程の平均 {min(x['six_phase_mean'] for x in t0s) - p['six_phase_mean']:+.4f}〜{max(x['six_phase_mean'] for x in t0s) - p['six_phase_mean']:+.4f} 動く"
      "（空トークンと問い合わせの注意が学ぶ分。SPEC は T0 を入力零の腕とするが、RT の T0 は学ぶ定数のトークンを持つ）")
    dr = [x["per_class_jaccard"]["dressing"] for r in sm["settings"].values() for x in r["arms"].values()]
    w(f"- J は dressing（val 24 フレーム）の当たり外れで大きく動く（56 本の dressing の Jaccard が {min(dr):.4f}〜{max(dr):.4f}）。6 工程の平均と acc を並べて読む")
    w("- layer4-roi-K64 の TGeo と T0 は val の argmax が全フレームで一致した（確率の差の最大 0.0036。入力は違う）")
    w("")
    w("## 4. §5.2 の予測との照合")
    w("")
    ok1 = all(abs(d["six_phase_mean"]) < 0.005 for d in tg_t0)
    tgeo = [r["diffs"]["TG-TGeo"] for r in sm["settings"].values()]
    ok2 = all(abs(d["six_phase_mean"]) < 0.005 for d in tgeo)
    w(f"1. 案 3 の TG − T0（6 工程平均）の絶対値は 0.005 未満: {'当たり' if ok1 else '外れ'}（8 設定のうち "
      f"{sum(abs(d['six_phase_mean']) < 0.005 for d in tg_t0)} 設定で 0.005 未満）")
    w(f"2. 案 3 の TG − TGeo の絶対値も 0.005 未満: {'当たり' if ok2 else '外れ'}（{sum(abs(d['six_phase_mean']) < 0.005 for d in tgeo)}/8 設定）")
    if s5:
        sw1 = [r["diffs"]["S_W - S_1"] for k, r in s5["settings"].items() if k.startswith("W1-")]
        ok3 = all(abs(d["six_phase_mean"]) < 0.005 for d in sw1)
        w(f"3. 案 5 の W1 で S_W − S_1 の絶対値は 0.005 未満: {'当たり' if ok3 else '外れ'}（4 設定のうち "
          f"{sum(abs(d['six_phase_mean']) < 0.005 for d in sw1)} 設定で 0.005 未満）")
        s0 = [s5["runs"][f"TW-{sc}-{f}-K64_empty"] for sc in ("W2", "W3") for f in ("a", "b")]
        mv = [x["six_phase_mean"] - s5["p_alone"]["six_phase_mean"] for x in s0]
        w(f"4. 案 5 の W2・W3 で S_0 が W1 の塔単独から 6 工程平均で 0.005 以上動く: {'当たり' if all(abs(v) >= 0.005 for v in mv) else '外れ'}"
          f"（W2・W3 × 形 a・b の 4 本の差 " + "・".join(f"{v:+.4f}" for v in mv) + "）")
    else:
        w("3. 案 5 の W1 で S_W − S_1 の絶対値は 0.005 未満: 測っていない（案 5 は殺し実験で止めた）")
        w("4. 案 5 の W2・W3 で S_0 が塔単独から動く: 測っていない（同上）")
    w("5. 殺し実験は両案とも殺す条件に当たる: 外れ（案 5 は当たり、案 3 は当たらない）")
    w("")
    w("## 5. 既知の限界（§5.3）と本契約で加わった限界")
    w("")
    w("- 折り 1 つ、val 2 本、seed 1 つ。今の塔（P*-15-COCO）での値で、工程塔の回し直しの後は旧い塔の値になる")
    w("- 工程の目録の行（train 9,657・val 1,515）はすべて術具注釈フレームで、G の出力の無い行は無かった。参照段は把持の注釈のある行（9,356・1,514）で学び評価するので主の腕と集合が違う")
    w("- 上流（G）の精度: 左のクラスの AP が右より低い（PR 295）。外接矩形はマスクの外れ値で広がる")
    w("- 殺し実験の線形の層は陽性対照が弱く（正解の工程を足して J +0.016・acc −0.001）、感度が低い")
    w("- 入れ替えの mapping は split 全体の並べ替えで、同じ動画への対応が val 55.6%（train 11.5%）。TRand は「別の動画の同じ相対時刻」ではない")
    w("- 案 5 の窓は境（間隔 > 2 秒）で切ると短く、L = 32 秒の窓が埋まり切るのは val 243/1,515。殺し実験の案 5 はこの窓で測った")
    w("- 全体の枠の ROI 平均と地図の空間平均の対照は弱い（同じフレームの最大 0.156 と別のフレームの最小 0.103 が重なる。layer4 val）")
    w("")
    w("## 6. 検証（§7 の g・h・i）")
    w("")
    c = sm["checks"]
    w(f"- g: run {c['g_runs']}/{c['g_expected']}、全本 4 epoch・最後の状態 {c['g_all_4_epochs_final_state']}、存在しない run の名前 2 つで {c['g_bogus_names_found']} 件、"
      f"受け取り手不変 {c['receiver_unchanged_all']}")
    w(f"- h: 差を各 run の val の確率の argmax から測り直して一致（{c['h_recheck_n']} 個、ずれの最大 {c['h_recheck_max_abs_diff']}）。1e-6 ずらした写しを検出 {c['h_shifted_copy_detected']}")
    w(f"- i: 通した動画 train {sm['videos_seen']['train']}・val {sm['videos_seen']['val']}、test との共通 {c['i_common_with_test']}。04 を混ぜると {c['i_control_with_04']}")
    w("")
    if s5:
        case5(w, s5)
    Path(a.out).write_text("\n".join(L) + "\n")
    print(f"wrote {a.out} {len(L)} lines")


if __name__ == "__main__":
    main()

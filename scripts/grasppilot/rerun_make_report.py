"""REPORT.md を summary.json と tables.md から作る（非公式 T-2026-11-06-grasp-pilot-d-rerun、Task E-3）。数値は summary.json の値だけを使う。

    python scripts/grasppilot/rerun_make_report.py
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

A = Path(__file__).resolve().parents[2] / "experiments/analysis/grasp_pilot_d_rerun"
S = json.loads((A / "summary.json").read_text())
V = json.loads((A / "verify.json").read_text())
T = json.loads((A / "testcheck.json").read_text())
D, B, B2, X, P, TOWER = S["D"], S["B"], S["B_second_andrew"], S["diffs"], S["predictions"], S["tower_record"]
f = lambda x: f"{x:.7f}"          # noqa: E731
s = lambda x: f"{x:+.7f}"         # noqa: E731


def dur(a, b):
    t0 = dt.datetime.strptime(a.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S")
    t1 = dt.datetime.strptime(b.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S")
    sec = int((t1 - t0).total_seconds())
    return f"{sec // 3600} 時間 {sec % 3600 // 60:02d} 分"


def row3(d):
    return f"overall {s(d['AP'])} / 標的群 {s(d['target_AP'])} / 陰性対照群 {s(d['control_AP'])}"


g, h, n = D["gteach"], D["shuf"], D["none"]
dg, dh, dgh = X["D_gteach_minus_none"], X["D_shuf_minus_none"], X["D_gteach_minus_shuffle"] if "D_gteach_minus_shuffle" in X else X["D_gteach_minus_shuf"]
pg, ph = X["D_gteach_minus_none_per_video"], X["D_shuf_minus_none_per_video"]
pgh = X["D_gteach_minus_shuf_per_video"]
e, t_ = B["empty"], B["gt"]
L = []
L += ["# REPORT — T-2026-11-06-grasp-pilot-d-rerun", "",
      "**非公式の測定。関門と設計の判断に使わない。** 1 折り（A）・val 2 動画（09・10）・seed 1 つ。判定の語（陽性・陰性・有意）は使わず、差は 1 本ずつの差として書く。",
      "数値はすべて `summary.json`（`scripts/grasppilot/rerun_aggregate.py aggregate` が各 run の記録から作る）の値。命令と出力は `tasks/T-2026-11-06-grasp-pilot-d-rerun/audit.md`。", "",
      "## 0. 位置づけ", "",
      "- 三本目 `T-2026-11-01-grasp-pilot-d` の案 D のうち、**G を教師・入れ替えた教師の 2 腕は無効**（教師の q が設計の誤りの二本目の G から作られていた）。本契約は、作り直した G の標的 q"
      "（目録 `signals_manifest.json` の `D_q.CF_train`）で 2 腕を回し直して置き換えた。補助損失なしの腕は有効なので回し直さず、三本目の値を使った"
      "（三本目の `code_sha256` が本契約の案 D の経路と一致し、GPU の使い方〔1 枚・batch 2・ため込み 2〕も同じ。audit Task B-3）",
      "- 四本目 `T-2026-11-06-grasp-pilot-arms` の案 B は、空と正解を二本目（andrew）の値で済ませていた。本契約は **空と正解を bengio で回し**、四本目の予測の腕とホストを揃えた", ""]

L += ["## 1. 案 D（overall mAP が主。最後の状態 = epoch 14）", "",
      "| 腕 | overall mAP | 標的群 AP | 陰性対照群 AP |", "|---|---|---|---|",
      f"| 補助損失なし（三本目の run） | {f(n['AP'])} | {f(n['target_AP'])} | {f(n['control_AP'])} |",
      f"| G を教師（本契約） | {f(g['AP'])} | {f(g['target_AP'])} | {f(g['control_AP'])} |",
      f"| 入れ替えた教師（本契約） | {f(h['AP'])} | {f(h['target_AP'])} | {f(h['control_AP'])} |", "",
      "1 本ずつの差（§6.2 の規則 2: 符号が食い違うときは両方を書き、一つにまとめない）:", "",
      f"- G を教師 − 補助損失なし: {row3(dg)}（動画 09 {s(pg['09'])}、10 {s(pg['10'])}）",
      f"- 入れ替えた教師 − 補助損失なし: {row3(dh)}（動画 09 {s(ph['09'])}、10 {s(ph['10'])}）",
      f"- G を教師 − 入れ替えた教師: {row3(dgh)}（動画 09 {s(pgh['09'])}、10 {s(pgh['10'])}）",
      f"- 標的群 AP では、G を教師 − 補助損失なし が {s(dg['target_AP'])}（負）、入れ替えた教師 − 補助損失なし が {s(dh['target_AP'])}（正）で符号が分かれる。"
      f"overall mAP では 2 本とも補助損失なしより高い（{s(dg['AP'])}、{s(dh['AP'])}）",
      f"- **陰性対照群 AP が動いた**（規則 5）: G を教師 {s(dg['control_AP'])}、入れ替えた教師 {s(dh['control_AP'])}（補助損失なしとの差）。"
      "陰性対照群は差が 0 付近のはずの群で、動いた分は処置の外の揺れを含みうる", "",
      f"- 補助損失（重みの前の交差エントロピーの平均）: G を教師 epoch 0 {g['aux_ce_by_epoch'][0]:.4f} → epoch 14 {g['aux_ce_by_epoch'][-1]:.4f}、"
      f"入れ替えた教師 {h['aux_ce_by_epoch'][0]:.4f} → {h['aux_ce_by_epoch'][-1]:.4f}。頭の出力の最大が q の最大と一致する割合（対応づいた枠、枠数で重み付けした平均）は G を教師 {g['aux_acc_by_epoch'][0]:.3f} → {g['aux_acc_by_epoch'][-1]:.3f}、"
      f"入れ替えた教師 {h['aux_acc_by_epoch'][0]:.3f} → {h['aux_acc_by_epoch'][-1]:.3f}。全 epoch で対応づいた枠の数が主経路の正解の枠の数と一致",
      f"- 補助損失なしの val mAP は epoch 13 が {n['inloop_val_mAP_by_epoch'][13]:.3f}、epoch 14 が {n['inloop_val_mAP_by_epoch'][14]:.3f} と、最後の 2 epoch の間で 0.005 動く"
      "（学習中の評価の値。最後の状態を使う規則なので epoch 14 の値を使っている）", ""]

L += ["## 2. 案 B（bengio の値だけ。W1、4 epoch）", "",
      f"- **空（bengio）は塔単独と同値**: overall {f(e['AP'])} / 標的群 {f(e['target_AP'])} / 陰性対照群 {f(e['control_AP'])}。界面の重みは学習後も 0.0（入力が全零で勾配が 0 のため。全 epoch で val mAP は 0.7273 のまま）。"
      f"二本目（andrew）の空との差は {s(X['host_diff_empty_bengio_minus_andrew']['AP'])} で完全に一致",
      f"- 正解（bengio）: overall {f(t_['AP'])} / 標的群 {f(t_['target_AP'])} / 陰性対照群 {f(t_['control_AP'])}。二本目（andrew）の正解との差（ホストの差の目安）: "
      f"{row3(X['host_diff_gt_bengio_minus_andrew'])}。**処置の差として読まない**", "",
      "bengio の空・正解を基準にした差（四本目の予測の腕を含む）:", "",
      "| 腕 | Δ空 overall | Δ空 標的群 | Δ空 陰性対照群 | 正解との差 overall | 標的群 | 陰性対照群 |", "|---|---|---|---|---|---|---|"]
for arm in ("gt", "pred_noCF", "pred_CF", "gtpred_CF", "shuffle", "toolonly_pred_noCF", "toolonly_shuffle"):
    ve = X["B_vs_empty"][arm]
    vg = X["B_vs_gt"].get(arm)
    L.append(f"| {arm} | {s(ve['AP'])} | {s(ve['target_AP'])} | {s(ve['control_AP'])} | " + (f"{s(vg['AP'])} | {s(vg['target_AP'])} | {s(vg['control_AP'])} |" if vg else "— | — | — |"))
d1, d2 = X["B_pred_noCF_minus_shuffle"], X["T_minus_B_pred_noCF"]
pn = X["B_pred_noCF_minus_shuffle_per_video"]
L += ["",
      f"- 案 B の Δ入替（予測-noCF − 入れ替え）: {row3(d1)}（動画 09 {s(pn['09'])}、10 {s(pn['10'])}）",
      f"- 予測-noCF の正解との差（bengio の正解）: {row3(X['B_vs_gt']['pred_noCF'])}。四本目の RESULT が書いた「二本目の正解との差」"
      f"（標的群 −0.0061118）とは、正解の腕のホストの差の分（標的群 {s(X['host_diff_gt_bengio_minus_andrew']['target_AP'])}）だけ違う",
      "- 四本目の Δ空（二本目の空との差）は、空が塔単独と完全に一致するので、bengio の空との差と同じ値になる（`tables.md` の「四本目の RESULT の書き方」の表）。"
      "ホストを揃えて値が変わったのは**正解の腕とそれを基準にした差だけ**",
      f"- 誰の手かの情報による差（術具だけ − 案 B、予測-noCF）: {row3(d2)}", ""]

L += ["## 3. 参考の表（本文の差の計算に使わない）", "",
      "| 腕 | overall | 標的群 | 陰性対照群 | 出所 |", "|---|---|---|---|---|"]
for k, v in S["D_invalid_third"].items():
    L.append(f"| 案 D {k}（三本目。**無効**） | {f(v['AP'])} | {f(v['target_AP'])} | {f(v['control_AP'])} | {v['run']} |")
for k in ("empty", "gt"):
    v = B2[k]
    L.append(f"| 案 B {k}（二本目、andrew） | {f(v['AP'])} | {f(v['target_AP'])} | {f(v['control_AP'])} | {v['run']} |")
L += [f"| 塔単独の記録 | {f(TOWER['AP'])} | {f(TOWER['target_AP'])} | {f(TOWER['control_AP'])} | 一本目の RESULT §3 |", "",
      "三本目の無効な腕と本契約の腕の違いは q の出所（二本目の G か、作り直した G の交差適合）だけでなく、GPU の共有の有無も含む。差を処置の差として読まない。", ""]

L += ["## 4. 事前登録の予測（§6.3。外れても判定は変わらない）", ""]
for k in ("1", "2", "3", "4"):
    p = P[k]
    vals = {kk: vv for kk, vv in p.items() if kk not in ("text", "held")}
    L.append(f"{k}. {p['text']} → **{'当たり' if p['held'] else '外れ'}**（" + "、".join(f"{kk} {vv:.7f}" for kk, vv in vals.items()) + "）")
L += ["", "## 5. 所要・GPU の載せ方・外部の使用", ""]
L += [f"- 案 D: G を教師 {dur(g['start'], g['end'])}、入れ替えた教師 {dur(h['start'], h['end'])}（GPU 1 枚ずつ。三本目の単独は 10 時間 05 分〜10 時間 26 分）",
      f"- 案 B: 空 {dur(e['start'], e['end'])}、正解 {dur(t_['start'], t_['end'])}（案 D と同じ枚に 1 本ずつ。四本目の 5 時間 15 分〜5 時間 33 分は 1 枚 3 本並行）",
      "- 電力の上限は 220 W × 2（RTX A6000）。載せ方は audit Task C の記憶の実測で決めた（GPU 0: 案 D G を教師 + 案 B 空、GPU 1: 案 D 入れ替えた教師 + 案 B 正解）",
      "- **学習中に本契約以外の GPU の使用が現れた**（audit D-2・D-3）: 11-07 17:20〜17:29 JST に両 GPU で数分ずつの山（37 GiB 級）、"
      "11-07 23:18 JST から 11-08 08:38 JST（GPU1）・09:12 JST（GPU0）まで両 GPU で 約 26 GiB の増加（利用率 85〜100 %）。"
      "他のプロセスは止めていない。OOM は起きず、4 本とも rc 0 で完走した。共有による案 D の所要の延びと数値の揺れの有無は UNKNOWN。"
      "学習の途中で気づけず、その場で諮れなかった", ""]

L += ["## 6. 検算・test 不使用", "",
      f"- 差を各 run の記録から別の経路で計算し直して一致: {V['recompute_equal']}。案 D は保存した予測から計算し直しても一致: {'、'.join(k + ' ' + ('一致' if v else '不一致') for k, v in V['preds_recompute_equal_D'].items())}。"
      f"1e-6 ずらした写しで不一致を検出: {V['control_detects']}。存在しない run の名前で 0 件: {V['n_fake_runs_present'] == 0}",
      f"- 学習と評価に通した動画: {', '.join(T['union'])}。{{04, 05, 07}} との共通: {T['common'] or '0 件'}。04 を混ぜた対照: {T['control_with_04']}", ""]

L += ["## 7. 既知の限界（§6.4）", "",
      "- 折りは 1 つ、val は 2 動画、seed は 1 つ。1 本ずつの差で、揺れの大きさは測っていない（補助損失なしの val mAP が最後の 2 epoch で 0.005 動く）",
      "- 案 D の GPU の使い方（1 枚・ため込み 2）は記録の検出塔（2 枚）と違う。補助損失なしの腕と記録の値の差は処置の差として読まない。"
      "さらに三本目の補助損失なしは GPU を単独で使った run で、本契約の 2 本は案 B・外部の使用と GPU を共有した",
      "- 案 D の標的 q は交差適合の半分の G から作られる。G の質は PR 295 の RESULT に従う（左のクラスの AP が右より低い理由は未解明）",
      "- 案 B は bf16 の自動混合精度（規約の TF32 ではない）。空の腕は界面の重みが 0 のままで塔単独と同値なので、Δ空 は「他の腕の界面を学んだ後の値 − 塔単独」の差である",
      "- 今の塔（D\\*-COCO）での測定。塔の選び直しの後は旧い塔での値になる", ""]

L += ["## 8. 全値の表（`tables.md` と同じ。クラス別・動画ごと・epoch ごと）", "", (A / "tables.md").read_text()]
(A / "REPORT.md").write_text("\n".join(L) + "\n")
print("REPORT.md", len(L), "行（tables.md を含む前）")

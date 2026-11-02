"""REPORT.md を集計の JSON から作る（非公式 T-2026-11-01-stage2-w23-bengio、SPEC §10）。

数値はすべて ``tools/aggregate.py --part all`` の出力（各 run の記録から読んだ値）と、Task B・C の記録から読む。
手で数値を書かない。記述は SPEC §6.2 の規則（1 本ずつの差として書き、陽性・陰性・有意などの語を使わない）に従う。

    python make_report.py --agg <aggregate.json> --out <REPORT.md> [--result-tables <md>]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AN = ROOT / "experiments/analysis/stage2_w23_bengio"
PD_ORDER = (("P2L", "W2"), ("P2L", "W3"), ("P3", "W3"), ("P1", "W3"))
PD_ARMS = ("empty", "pred_noCF", "gt", "shuffle")
ARM_JA = {"empty": "空", "pred_noCF": "予測-noCF", "gt": "正解", "pred_CF": "予測-CF", "gtpred_CF": "正解予測-CF",
          "shuffle": "入れ替え"}
DP_TYPES = ("D1-L1", "D1-L2", "D2", "D3-L1", "D3-L2", "LC", "TH", "TH-NG", "GA")
TYPE_JA = {"P2L": "P2L", "P3": "P3（query）", "P1": "P1（FiLM）", "LC": "logit-correction", "TH": "tool-history",
           "TH-NG": "tool-history（ゲートなし）", "GA": "案 A（D1 concat、g30）"}


def f(x, n=4, sign=False):
    if x is None:
        return "—"
    return f"{x:+.{n}f}" if sign else f"{x:.{n}f}"


def unk(x, n=4, sign=True):
    return "UNKNOWN（未完了）" if x is None else f(x, n, sign)


def pd_table(pd):
    L = ["| 型 | W | 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | AP50 | Δ空 overall | Δ空 標的群 | Δ入替 overall | Δ入替 標的群 | Δ塔 overall | Δ塔 標的群 |",
         "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for t, w in PD_ORDER:
        rows = pd.get(t, {}).get(w, {})
        for a in PD_ARMS:
            r = rows.get(a)
            if not r:
                L.append(f"| {t} | {w} | {ARM_JA[a]} | UNKNOWN（未完了） | | | | | | | | | |")
                continue
            L.append(f"| {t} | {w} | {ARM_JA[a]} | {f(r['AP'])} | {f(r['target_AP'])} | {f(r['control_AP'])} | {f(r['AP50'])} | "
                     f"{f(r['d_empty_AP'], sign=True)} | {f(r['d_empty_target_AP'], sign=True)} | "
                     f"{f(r['d_shuffle_AP'], sign=True)} | {f(r['d_shuffle_target_AP'], sign=True)} | "
                     f"{f(r['d_tower_AP'], sign=True)} | {f(r['d_tower_target_AP'], sign=True)} |")
    return "\n".join(L)


def pd_ref_table(pd):
    L = ["| 型 | W | 腕 | overall mAP | 標的群 AP | 陰性対照群 AP | Δ空 overall | Δ空 標的群 | ホスト | 値の出所 |",
         "|---|---|---|---:|---:|---:|---:|---:|---|---|"]
    for t in ("P2L", "P3", "P1"):
        for w in ("W1_ref", "W2_ref"):
            for a, r in pd.get(t, {}).get(w, {}).items():
                L.append(f"| {t} | {w[:2]} | {ARM_JA[a]} | {f(r['AP'])} | {f(r['target_AP'])} | {f(r['control_AP'])} | "
                         f"{f(r['d_empty_AP'], sign=True)} | {f(r['d_empty_target_AP'], sign=True)} | {r['host']} | {r['source']} |")
    return "\n".join(L)


def pd_side(pd):
    """型ごとの W1・W2・W3 の正解の腕と予測-noCF の Δ空（overall / 標的群）。ホストを付ける。"""
    L = ["| 型 | 腕 | W1（参考） | W2（参考は P1） | W3 |", "|---|---|---|---|---|"]
    for t in ("P2L", "P3", "P1"):
        by = pd.get(t, {})
        for a in ("gt", "pred_noCF"):
            cells = []
            for w in ("W1", "W2", "W3"):
                r = (by.get(w) or {}).get(a) or (by.get(f"{w}_ref") or {}).get(a)
                if t == "P3" and w == "W2":
                    cells.append("回さない（W1 と同じ集合）")
                elif r is None:
                    cells.append("UNKNOWN（未完了）" if w == "W3" else "—")
                else:
                    cells.append(f"{f(r['d_empty_AP'], sign=True)} / {f(r['d_empty_target_AP'], sign=True)}（{r['host']}）")
            L.append(f"| {t} | {ARM_JA[a]} | " + " | ".join(cells) + " |")
    return "\n".join(L)


def dp_table(dp):
    L = ["| 型 | W | 腕 | macro Jaccard | frame accuracy | Δ空 | Δ入替 | Δ塔 | 09 Δ空 | 10 Δ空 |",
         "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for t in DP_TYPES:
        for w in ("W2", "W3"):
            for a, r in dp[t][w].items():
                pv = r["d_empty_per_video"] or {}
                L.append(f"| {t} | {w} | {ARM_JA[a]} | {f(r['jaccard'])} | {f(r['accuracy'])} | {f(r['d_empty'], sign=True)} | "
                         f"{f(r['d_shuffle'], sign=True)} | {f(r['d_tower'], sign=True)} | {f(pv.get('09'), sign=True)} | "
                         f"{f(pv.get('10'), sign=True)} |")
    return "\n".join(L)


def dp_side(dp):
    L = ["| 型 | 腕 | W1（参考、ホスト） | W2 | W3 | W2 Δ入替 | W3 Δ入替 |", "|---|---|---:|---:|---:|---:|---:|"]
    for t in DP_TYPES:
        k = "gt" if "gt" in dp[t]["W2"] else "pred_noCF"
        for a in dict.fromkeys((k, "pred_noCF")):
            w1 = dp[t]["W1"].get(a)
            L.append(f"| {t} | {ARM_JA[a]} | {f(w1['d_empty'], sign=True)}（{w1['host']}） | {f(dp[t]['W2'][a]['d_empty'], sign=True)} | "
                     f"{f(dp[t]['W3'][a]['d_empty'], sign=True)} | {f(dp[t]['W2'][a]['d_shuffle'], sign=True)} | "
                     f"{f(dp[t]['W3'][a]['d_shuffle'], sign=True)} |")
    return "\n".join(L)


def per_class_pd(pd):
    classes = None
    L = []
    for t, w in PD_ORDER:
        for a in PD_ARMS:
            r = pd.get(t, {}).get(w, {}).get(a)
            if not r:
                continue
            if classes is None:
                classes = sorted(r["per_class"])
                L += ["| run | " + " | ".join(classes) + " |", "|---|" + "---:|" * len(classes)]
            L.append(f"| {t} {w} {ARM_JA[a]} | " + " | ".join(f(r["per_class"][c], 3) for c in classes) + " |")
    return "\n".join(L)


def per_class_dp(dp):
    classes = None
    L = []
    for t in DP_TYPES:
        for w in ("W2", "W3"):
            for a, r in dp[t][w].items():
                if classes is None:
                    classes = list(r["per_class"])
                    L += ["| run | " + " | ".join(classes) + " |", "|---|" + "---:|" * len(classes)]
                L.append(f"| {t} {w} {ARM_JA[a]} | " + " | ".join(f(r["per_class"][c], 3) for c in classes) + " |")
    return "\n".join(L)


def epochs_pd(pd):
    L = ["| run | 学習前 | epoch 0 | epoch 1 | epoch 2 | epoch 3 |", "|---|---:|---:|---:|---:|---:|"]
    for t, w in PD_ORDER:
        for a in PD_ARMS:
            r = pd.get(t, {}).get(w, {}).get(a)
            if not r:
                continue
            e = {int(k): v for k, v in (r["per_epoch_mAP"] or {}).items()}
            L.append(f"| {t} {w} {ARM_JA[a]} | {f(e.get(-1, r['init']))} | " + " | ".join(f(e.get(i)) for i in range(4)) + " |")
    return "\n".join(L)


def epochs_dp(dp):
    L = ["| run | epoch 1 | epoch 2 | epoch 3 | epoch 4 |", "|---|---:|---:|---:|---:|"]
    for t in DP_TYPES:
        for w in ("W2", "W3"):
            for a, r in dp[t][w].items():
                h = {x["epoch"]: x["val_jaccard"] for x in (r["history"] or [])}
                L.append(f"| {t} {w} {ARM_JA[a]} | " + " | ".join(f(h.get(i)) for i in range(1, 5)) + " |")
    return "\n".join(L)


def per_video_pd(pd):
    L = ["| run | 09 | 10 | 09 Δ空 | 10 Δ空 |", "|---|---:|---:|---:|---:|"]
    for t, w in PD_ORDER:
        rows = pd.get(t, {}).get(w, {})
        e = rows.get("empty")
        for a in PD_ARMS:
            r = rows.get(a)
            if not r:
                continue
            d = {v: (r["per_video"][v] - e["per_video"][v]) if e else None for v in ("09", "10")}
            L.append(f"| {t} {w} {ARM_JA[a]} | {f(r['per_video']['09'])} | {f(r['per_video']['10'])} | "
                     f"{f(d['09'], sign=True)} | {f(d['10'], sign=True)} |")
    return "\n".join(L)


def describe(dp, pd):
    """SPEC §6.2 の規則による記述: 空の腕の Δ塔（規則 3）と、Δ空 と Δ入替 の符号が食い違う組（規則 4）。"""
    L = ["空の腕の Δ塔（受け取り手を学んだこと自体の動き。規則 3）:"]
    for t, w in PD_ORDER:
        e = pd.get(t, {}).get(w, {}).get("empty")
        L.append(f"- 工程から検出 {t} {w}: overall {unk(e and e['d_tower_AP'])}、標的群 {unk(e and e['d_tower_target_AP'])}")
    for t in DP_TYPES:
        L.append(f"- 検出から工程 {t}: W2 {f(dp[t]['W2']['empty']['d_tower'], sign=True)}、W3 {f(dp[t]['W3']['empty']['d_tower'], sign=True)}（macro Jaccard）")
    L.append("")
    L.append("Δ空 と Δ入替 の符号が食い違う組（両方を書き、一つにまとめない。規則 4。どちらかが 0 の組は含めない）:")
    n = 0
    for t, w in PD_ORDER:
        for a, r in pd.get(t, {}).get(w, {}).items():
            for k, name in (("AP", "overall"), ("target_AP", "標的群")):
                x, y = r[f"d_empty_{k}"], r[f"d_shuffle_{k}"]
                if x and y and (x > 0) != (y > 0):
                    n += 1
                    L.append(f"- 工程から検出 {t} {w} {ARM_JA[a]} {name}: Δ空 {f(x, sign=True)}、Δ入替 {f(y, sign=True)}")
    for t in DP_TYPES:
        for w in ("W2", "W3"):
            for a, r in dp[t][w].items():
                x, y = r["d_empty"], r["d_shuffle"]
                if x and y and (x > 0) != (y > 0):
                    n += 1
                    L.append(f"- 検出から工程 {t} {w} {ARM_JA[a]}: Δ空 {f(x, sign=True)}、Δ入替 {f(y, sign=True)}")
    if n == 0:
        L.append("- なし")
    L.append("")
    L.append("W をまたぐ比べは同じ型の中でだけ行い（規則 2）、ホストが違う W1 の値は §3.1・§4.1 の参考の表に置いた。seed は一つで、差は 1 本ずつの差（規則 1）。"
             "結果は関門の判定と設計の判断に使わない（規則 5）。")
    return "\n".join(L)


def predictions(pd):
    """SPEC §6.3 の照合（外れても判定は変わらない）。"""
    rows, n_big, n_known = [], 0, 0
    for t in ("P2L", "P3", "P1"):
        w3 = (pd.get(t, {}).get("W3") or {}).get("gt")
        w1 = (pd.get(t, {}).get("W1_ref") or {}).get("gt")
        if w3 and w1:
            n_known += 1
            big = w3["d_empty_AP"] > w1["d_empty_AP"]
            n_big += big
            rows.append(f"{t}: W3 {f(w3['d_empty_AP'], sign=True)}、W1 {f(w1['d_empty_AP'], sign=True)}（{w1['host']}）→ {'W3 が大きい' if big else 'W3 が大きくない'}")
        else:
            rows.append(f"{t}: UNKNOWN（W3 の正解の腕が未完了）")
    p1 = ("当たり" if n_big * 2 > 3 else "外れ") if n_known == 3 else f"UNKNOWN（{n_known}/3 型だけ測れた。W3 が大きい型 {n_big}）"
    rows2 = []
    neg = []
    for t in ("P2L", "P3", "P1"):
        e = (pd.get(t, {}).get("W3") or {}).get("empty")
        if e:
            neg.append(e["d_tower_AP"] < 0)
            rows2.append(f"{t}: {f(e['d_tower_AP'], sign=True)}")
        else:
            rows2.append(f"{t}: UNKNOWN（未完了）")
    p2 = ("当たり" if all(neg) else "外れ") if len(neg) == 3 else f"UNKNOWN（{len(neg)}/3 型だけ測れた）"
    return p1, rows, p2, rows2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--status-note", default=None, help="冒頭に置く状態の注記（中止の理由など。数値は書かない）")
    a = ap.parse_args()
    agg = json.loads(Path(a.agg).read_text())
    dp, pd = agg["dp"], agg["pd"]
    b2 = json.loads((AN / "repro/b2_summary.json").read_text())
    ta = json.loads((AN / "final/test_audit.json").read_text())
    dps = json.loads((AN / "taskC/dp_scopes.json").read_text())["types"]
    pds = json.loads((AN / "taskC/pd_scopes.json").read_text())["types"]
    pds.update(json.loads((AN / "taskC/pd_scopes_P1.json").read_text())["types"])
    p1, p1rows, p2, p2rows = predictions(pd)
    n_pd = sum(len(pd.get(t, {}).get(w, {})) for t, w in PD_ORDER)
    out = f"""# REPORT — Stage 2 の界面の型を W2・W3 で回す（bengio の分）

**非公式の測定。関門と設計の判断に使わない。** 契約 `T-2026-11-01-stage2-w23-bengio`。判定と経緯は `tasks/T-2026-11-01-stage2-w23-bengio/`。
この頁の数値はすべて `tools/aggregate.py` と `tools/make_report.py` が各 run の記録から作った（手で書いていない）。

## 1. 条件

- 折り A（train 10 動画、val 09・10）、seed 42、4 epoch の固定の長さ、4 epoch 目の状態。test の動画（04・05・07）は学習にも評価にも通していない
  （本契約の {ta['n_runs']} 本の run で通した動画は {', '.join(ta['videos_used'])}、test との共通 {len(ta['intersection_with_test'])} 件）
- ホスト bengio（RTX A6000 × 2、電力の上限 220 W）。型ごとのホストの集合: {', '.join(f'{k} {v}' for k, v in ta['hosts_by_type'].items())}
- 塔単独（Task B-2 の再現）: 工程 macro Jaccard {f(b2['ptower']['phase_jaccard'], 7)}・frame accuracy {f(b2['ptower']['phase_accuracy'], 7)}、
  検出 overall mAP {f(b2['dtower_seed42']['AP'], 7)}・標的群 AP {f(b2['dtower_seed42']['target_AP'], 7)}・陰性対照群 AP {f(b2['dtower_seed42']['control_AP'], 7)}・AP50 {f(b2['dtower_seed42']['AP50'], 7)}
- 工程から検出: W2 = 界面 ＋ decoder の最終層とその層のクラスと box の頭（`--trainable w2`）、W3 = 界面 ＋ 設定の凍結（backbone の 11 個）以外の検出器の全体（`--trainable all`）。
  受け取り手の学習率 1e-4・界面 5e-4、batch 2、学習は bf16 の自動混合精度・評価は単精度。run は {n_pd}/16 本
- 検出から工程と案 A: W2 = 界面 ＋ 時間ヘッドの最後の段、W3 = 界面 ＋ 時間ヘッドの全体（eval、dropout なし）。受け取り手の学習率 5e-4・重み減衰 0.01。run は 100 本
- 回す組は利用者の決定（`spec.yaml` の `meta.amendments`）: P3 は W3 だけ（W1 が既に `--trainable w2`）、extra-queries は回さない、P1 の W3 を足す、工程から検出は四腕
- Δ空 = 腕 − 同じ型・同じ W の空の腕、Δ入替 = 腕 − 同じ型・同じ W の入れ替えの腕、Δ塔 = 腕 − 塔単独。すべて 1 本ずつの差

## 2. 学ぶ集合（型と W ごと。`taskC/dp_scopes.json`、`taskC/pd_scopes*.json`）

| 受け取り手 | 型 | W1 | W2 | W3 |
|---|---|---:|---:|---:|
""" + "\n".join(f"| 検出塔 | {t} | {pds[t]['W1']['n_params']:,} | " + ("—（W1 と同じ集合）" if t == "P3" else f"{pds[t]['W2']['n_params']:,}")
                + f" | {pds[t]['W3']['n_params']:,} |" for t in ("P2L", "P3", "P1")) + "\n" + \
        "\n".join(f"| 時間ヘッド | {t} | {dps[t]['W1']['n_trainable']} 個 | {dps[t]['W2']['n_trainable']} 個（受け取り手 {dps[t]['W2']['receiver_trainable_params']:,}） | "
                  f"{dps[t]['W3']['n_trainable']} 個（受け取り手 {dps[t]['W3']['receiver_trainable_params']:,}） |" for t in DP_TYPES) + f"""

検出塔はパラメータの要素数、時間ヘッドはパラメータの名前の数（括弧は受け取り手の要素数）。すべて SPEC §3.1 の定義と一致し、定義の外を一つ混ぜると一致しない。

## 3. 工程から検出（val、4 epoch 目）

{pd_table(pd)}

### 3.1 型ごとの W1・W2・W3（正解の腕と予測-noCF の Δ空、overall / 標的群。参考。ホストが違う値は処置の差として読まない）

{pd_side(pd)}

### 3.2 参考: W1 と P1 の W2 の記録（直しの契約の `report.json`）

{pd_ref_table(pd)}

### 3.3 動画ごとの mAP

{per_video_pd(pd)}

## 4. 検出から工程と案 A（val、4 epoch 目）

{dp_table(dp)}

### 4.1 型ごとの W1・W2・W3（Δ空。W1 は参考、ホストつき）

{dp_side(dp)}

## 5. epoch ごとの val

### 5.1 工程から検出（overall mAP。epoch は 0 始まり）

{epochs_pd(pd)}

### 5.2 検出から工程と案 A（macro Jaccard。epoch は 1 始まり）

{epochs_dp(dp)}

## 6. クラス別

### 6.1 工程から検出（AP、area all、maxDets 100）

{per_class_pd(pd)}

### 6.2 検出から工程と案 A（Jaccard）

{per_class_dp(dp)}

## 7. 記述（SPEC §6.2）

""" + describe(dp, pd) + f"""

## 8. 予測の照合（SPEC §6.3。記述のための事前の記録。外れても判定は変わらない）

1. 工程から検出の正解の腕の Δ空（overall mAP）は、型ごとに W3 が W1 より大きい型が過半を占める → **{p1}**
   - """ + "\n   - ".join(p1rows) + f"""
2. W3 の空の腕の Δ塔（overall mAP）は負である → **{p2}**
   - """ + "\n   - ".join(p2rows) + """

## 9. 既知の限界（SPEC §6.4）

- 折りは 1 つ、val は 2 動画、seed は 1 つ。工程は動画 09 が塔単独で上限に近い（macro Jaccard 0.993）
- 受け取り手は train で学習済みで、W2・W3 は同じ train でさらに学ぶ
- 長さは固定の 4 epoch で、受け取り手を学ぶときの収束規則に従っていない（利用者の決定）
- 工程塔の W3 は時間ヘッドまでで、CNN は学ばない
- 型を二つのホストに配分したので、ホストをまたいで型どうしを並べるときはホストの差を含む。W1 の参考の値の多くは andrew で、P2L の 5 腕と P1 の一部は前回の run の epoch 3 の記録
- 数値精度は前回の経路のまま（工程から検出は bf16 の自動混合精度）
- 工程から検出の W3 は 1 枚に 3 本までしか載らず（学習中 1 本 約 13.5 GiB）、P3 の W3 の正解・入れ替えは一度止まって回し直した（同時に回った本数が他の run と違う）
"""
    if a.status_note:
        head, rest = out.split("\n", 1)
        out = f"{head}\n\n**{a.status_note}**\n{rest}"
    Path(a.out).write_text(out)
    print(f"wrote {a.out}: pd {n_pd}/16, p1={p1}, p2={p2}")


if __name__ == "__main__":
    main()

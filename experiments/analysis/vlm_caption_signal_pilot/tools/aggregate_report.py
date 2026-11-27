"""SPEC §7・§7.1・§9 i・§10: 記録ファイルだけから REPORT.md・diffs.csv・summary.json を自動生成する。

途中版（V→P 完了時点、V→T W1/W2/W3 完了時点）と最終版の両方に対応。
値は一切手で写さず、保存済み metrics/predictions から機械計算し、再計算検証（1e-6 陽性対照つき）も行う。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from stage2pilot import common as C  # noqa: E402

STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot")
P1_DIR = ROOT / "experiments/phase1"
BAND_V2P = 0.015
EPOCHS = (4, 8, 12, 16)
DP_TYPES = ("D1-L2", "D2", "D3-L2")
PD_TYPES = ("P1", "P2L")
SCOPES = ("W1", "W2", "W3")
ARMS = ("empty", "vlm_ko", "vlm_otsu", "vlm_hei", "vlm_ko_shuf", "vlm_otsu_shuf", "vlm_hei_shuf")
ARM_LABEL = {
    "empty": "空", "vlm_ko": "予測-甲", "vlm_otsu": "予測-乙", "vlm_hei": "予測-丙",
    "vlm_ko_shuf": "入替-甲", "vlm_otsu_shuf": "入替-乙", "vlm_hei_shuf": "入替-丙",
}

# SPEC §1.1 の前回の参考値（4 epoch 目、予測-noCF − 入れ替え）
PREV_REF_V2P = {
    ("W1", "D1-L2"): 0.0371, ("W2", "D1-L2"): 0.0643, ("W3", "D1-L2"): 0.0852,
    ("W1", "D2"): 0.0288, ("W2", "D2"): 0.0203, ("W3", "D2"): 0.0093,
    ("W1", "D3-L2"): 0.0480, ("W2", "D3-L2"): 0.0665, ("W3", "D3-L2"): 0.0200,
}
PREV_REF_V2T = {
    ("W1", "P1"): 0.0087, ("W1", "P2L"): 0.0075,
}
PRESENT_7 = ("anesthesia", "closure", "design", "dissection", "dressing", "hemostasis", "incision")
SIX_PHASES = tuple(p for p in PRESENT_7 if p != "dressing")


def six_jaccard(per_class: dict) -> float:
    return float(np.mean([per_class[p] for p in SIX_PHASES]))


def load_v2p_runs() -> dict:
    runs = {}
    for sc in SCOPES:
        prefix = f"vlm_caption_signal_pilot_dp_{sc}"
        for typ in DP_TYPES:
            for arm in ARMS:
                cands = sorted(P1_DIR.glob(f"{prefix}_*_{typ}_{arm}_ep16_seed42"))
                if not cands:
                    continue
                d = cands[-1]
                ep_data = {}
                for ep in EPOCHS:
                    mp = d / f"metrics_ep{ep}.json"
                    pp = d / f"predictions/val_probs_ep{ep}.npz"
                    if not (mp.exists() and pp.exists()):
                        continue
                    m = json.loads(mp.read_text())
                    ep_data[str(ep)] = {
                        "six": six_jaccard(m["phase_per_class_jaccard"]),
                        "acc": float(m["phase_accuracy"]),
                        "j7": float(m["phase_jaccard"]),
                        "per_class": m["phase_per_class_jaccard"],
                        "per_video": m["per_video"],
                        "iface_last": m.get("iface_last"),
                        "probs_path": str(pp),
                    }
                if len(ep_data) == len(EPOCHS):
                    met = json.loads((d / "metrics.json").read_text())
                    runs[f"{sc}|{typ}|{arm}"] = {
                        "run": d.name, "scope": sc, "type": typ, "arm": arm,
                        "elapsed_seconds": met.get("elapsed_seconds"),
                        "epochs": ep_data,
                    }
    return runs


def load_v2t_runs() -> dict:
    runs = {}
    for sc in SCOPES:
        for typ in PD_TYPES:
            for arm in ARMS:
                d = P1_DIR / f"vlm_caption_signal_pilot_pd_{typ}_{sc}_{arm}_ep16_seed42"
                mp = d / "v2t_metrics.json"
                if not mp.exists():
                    continue
                m = json.loads(mp.read_text())
                ep_data = {}
                for ep in EPOCHS:
                    ev = m["per_epoch_1idx"].get(str(ep))
                    if ev is None:
                        continue
                    ep_data[str(ep)] = {
                        "target_AP": float(ev["target_AP"]),
                        "AP": float(ev["AP"]),
                        "control_AP": float(ev["control_AP"]),
                        "per_class_ap": ev["per_class_ap"],
                        "per_video_AP": ev["per_video_AP"],
                        "iface_last": m.get("iface_last_by_ep1", {}).get(str(ep)),
                    }
                if len(ep_data) == len(EPOCHS):
                    runs[f"{sc}|{typ}|{arm}"] = {
                        "run": d.name, "scope": sc, "type": typ, "arm": arm,
                        "elapsed_seconds": m.get("seconds_to_finalize"),
                        "epochs": ep_data,
                    }
    return runs


def argmax_agreement(p1_path: str, p2_path: str) -> float:
    a, b = np.load(p1_path), np.load(p2_path)
    eq, tot = 0, 0
    for k in sorted(a.files):
        pa = a[k].argmax(-1)
        pb = b[k].argmax(-1)
        eq += int((pa == pb).sum())
        tot += int(pa.size)
    return eq / max(tot, 1)


def recompute_v2p_check(runs: dict) -> dict:
    names = C.phase_names()
    split = C.fold_a()
    gt = {v: y for v, _, y in C.phase_sequences(split["val"])}
    max_dev = 0.0
    n_checked = 0
    ctrl_detected = 0
    for r in runs.values():
        for ep in EPOCHS:
            ed = r["epochs"][str(ep)]
            probs = np.load(ed["probs_path"])
            ev = PhaseEvaluator(num_classes=len(names), class_names=names)
            for v in ("09", "10"):
                ev.update(probs[v].argmax(-1), gt[v], video_id=v)
            rec = ev.compute()
            j6 = six_jaccard(rec["phase_per_class_jaccard"])
            dev = max(abs(j6 - ed["six"]), abs(rec["phase_jaccard"] - ed["j7"]),
                      abs(rec["phase_accuracy"] - ed["acc"]))
            max_dev = max(max_dev, dev)
            n_checked += 1
            if abs((j6 + 1e-6) - ed["six"]) > 0:
                ctrl_detected += 1
    return {
        "n_checked": n_checked,
        "max_dev": max_dev,
        "control_1e-6_detected": ctrl_detected,
        "control_all_detected": ctrl_detected == n_checked,
    }


def compute_diffs(v2p: dict, v2t: dict) -> list[dict]:
    pairs = [
        ("vlm_ko", "vlm_ko_shuf", "予測-甲 − 入替-甲（主）"),
        ("vlm_otsu", "vlm_otsu_shuf", "予測-乙 − 入替-乙（主）"),
        ("vlm_hei", "vlm_hei_shuf", "予測-丙 − 入替-丙（主）"),
        ("vlm_ko_shuf", "empty", "入替-甲 − 空（分布）"),
        ("vlm_otsu_shuf", "empty", "入替-乙 − 空（分布）"),
        ("vlm_hei_shuf", "empty", "入替-丙 − 空（分布）"),
        ("vlm_ko", "empty", "予測-甲 − 空（全体）"),
        ("vlm_otsu", "empty", "予測-乙 − 空（全体）"),
        ("vlm_hei", "empty", "予測-丙 − 空（全体）"),
        ("vlm_otsu", "vlm_ko", "予測-乙 − 予測-甲（伏せ字拡大）"),
        ("vlm_hei", "vlm_ko", "予測-丙 − 予測-甲（伏せ字拡大）"),
    ]
    rows = []
    for sc in SCOPES:
        for typ in DP_TYPES:
            for ep in EPOCHS:
                for a1, a2, reads in pairs:
                    k1, k2 = f"{sc}|{typ}|{a1}", f"{sc}|{typ}|{a2}"
                    if k1 not in v2p or k2 not in v2p:
                        continue
                    r1, r2 = v2p[k1]["epochs"][str(ep)], v2p[k2]["epochs"][str(ep)]
                    d6 = r1["six"] - r2["six"]
                    dacc = r1["acc"] - r2["acc"]
                    dj7 = r1["j7"] - r2["j7"]
                    agree = argmax_agreement(r1["probs_path"], r2["probs_path"])
                    ref = PREV_REF_V2P.get((sc, typ)) if (ep == 4 and a1 == "vlm_ko" and a2 == "vlm_ko_shuf") else None
                    rows.append({
                        "direction": "V2P", "scope": sc, "type": typ, "epoch": ep,
                        "arm1": a1, "arm2": a2, "reads": reads,
                        "primary": d6, "secondary1": dacc, "secondary2": dj7,
                        "readable": abs(d6) > BAND_V2P,
                        "metrics_identical": (d6 == 0.0 and dacc == 0.0 and dj7 == 0.0),
                        "argmax_agree": agree,
                        "prev_ref_ep4": ref,
                    })
    for sc in SCOPES:
        for typ in PD_TYPES:
            for ep in EPOCHS:
                for a1, a2, reads in pairs:
                    k1, k2 = f"{sc}|{typ}|{a1}", f"{sc}|{typ}|{a2}"
                    if k1 not in v2t or k2 not in v2t:
                        continue
                    r1, r2 = v2t[k1]["epochs"][str(ep)], v2t[k2]["epochs"][str(ep)]
                    dt = r1["target_AP"] - r2["target_AP"]
                    dm = r1["AP"] - r2["AP"]
                    dc = r1["control_AP"] - r2["control_AP"]
                    ref = PREV_REF_V2T.get((sc, typ)) if (ep == 4 and a1 == "vlm_ko" and a2 == "vlm_ko_shuf") else None
                    rows.append({
                        "direction": "V2T", "scope": sc, "type": typ, "epoch": ep,
                        "arm1": a1, "arm2": a2, "reads": reads,
                        "primary": dt, "secondary1": dm, "secondary2": dc,
                        "readable": None,  # V→T は揺れの幅を測っていない
                        "metrics_identical": (dt == 0.0 and dm == 0.0 and dc == 0.0),
                        "argmax_agree": None,
                        "prev_ref_ep4": ref,
                    })
    return rows


def evaluate_predictions(diffs: list[dict]) -> dict:
    def get_main(direction, sc, typ, a1, a2):
        for d in diffs:
            if d["direction"] == direction and d["scope"] == sc and d["type"] == typ and d["epoch"] == 4 and d["arm1"] == a1 and d["arm2"] == a2:
                return d["primary"]
        return None

    p1, p2, p3, p4 = [], [], [], []
    for sc in SCOPES:
        for typ in DP_TYPES:
            ko = get_main("V2P", sc, typ, "vlm_ko", "vlm_ko_shuf")
            ot = get_main("V2P", sc, typ, "vlm_otsu", "vlm_otsu_shuf")
            he = get_main("V2P", sc, typ, "vlm_hei", "vlm_hei_shuf")
            if ko is not None and ot is not None:
                p1.append({"scope": sc, "type": typ, "ko": ko, "otsu": ot, "hit": ko >= ot})
            if ko is not None and he is not None:
                p2.append({"scope": sc, "type": typ, "ko": ko, "hei": he, "hit": ko >= he})
            if sc == "W1" and ko is not None:
                ref = PREV_REF_V2P[(sc, typ)]
                p3.append({"type": typ, "ko": ko, "prev_ref": ref, "hit": ko < ref})
    for typ in PD_TYPES:
        ko = get_main("V2T", "W1", typ, "vlm_ko", "vlm_ko_shuf")
        if ko is not None:
            ref = PREV_REF_V2T[("W1", typ)]
            p4.append({"type": typ, "ko": ko, "prev_ref": ref, "hit": ko < ref})
    return {"p1": p1, "p2": p2, "p3": p3, "p4": p4}


def fmt(x, signed=False):
    if x is None:
        return "—"
    return f"{x:+.4f}" if signed else f"{x:.4f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-label", default="途中版", help="途中版ラベルまたは最終版")
    ap.add_argument("--out-md", type=Path, required=True)
    ap.add_argument("--out-csv", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    a = ap.parse_args()

    v2p = load_v2p_runs()
    v2t = load_v2t_runs()
    diffs = compute_diffs(v2p, v2t)
    recomp = recompute_v2p_check(v2p) if v2p else None
    preds = evaluate_predictions(diffs)

    pt_alone = json.loads((STORE / "task_b/ptower_alone.json").read_text()) if (STORE / "task_b/ptower_alone.json").exists() else {}
    dt_alone = json.loads((STORE / "task_b/dtower_alone.json").read_text()) if (STORE / "task_b/dtower_alone.json").exists() else {}
    cap_stats = json.loads((STORE / "caption_stats.json").read_text()) if (STORE / "caption_stats.json").exists() else {}
    ex20 = json.loads((STORE / "val_examples_20.json").read_text()) if (STORE / "val_examples_20.json").exists() else []

    summary = {
        "stage_label": a.stage_label,
        "v2p_count": len(v2p), "v2t_count": len(v2t),
        "v2p_runs": v2p, "v2t_runs": v2t,
        "diffs": diffs, "recompute_v2p": recomp,
        "predictions": preds,
        "ptower_alone": pt_alone, "dtower_alone": dt_alone,
    }
    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    a.out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")

    # CSV (UTF-8 BOM)
    a.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(a.out_csv, "w", encoding="utf-8-sig", newline="") as fh:
        cw = csv.writer(fh)
        cw.writerow(["direction", "scope", "type", "epoch", "arm1", "arm2", "reads",
                     "primary", "secondary1", "secondary2", "readable", "metrics_identical",
                     "argmax_agree", "prev_ref_ep4"])
        for d in diffs:
            cw.writerow([d["direction"], d["scope"], d["type"], d["epoch"], d["arm1"], d["arm2"], d["reads"],
                         d["primary"], d["secondary1"], d["secondary2"], d["readable"], d["metrics_identical"],
                         d["argmax_agree"], d["prev_ref_ep4"]])

    # REPORT.md
    L = []
    w = L.append
    w(f"# REPORT — VLM キャプション信号の予備測定（{a.stage_label}、非公式 T-2026-11-26-vlm-caption-signal-pilot）")
    w("")
    w("非公式の予備測定。関門の判定と設計の判断（案の採否を含む）には使わない。差を並べるだけで採否・順位は書かない。")
    w(f"ホスト ilya（RTX 6000 Ada × 2）、Fold A（train 10 本・val 09・10）、seed 42。V→P 完了 {len(v2p)}/63 本、V→T 完了 {len(v2t)}/42 本。")
    w(f"V→P の差の幅 ±{BAND_V2P} の中は「読めない」と書き符号で解釈しない。V→T は揺れの幅を測っていない。")
    w("")
    if cap_stats:
        w("## 1. VLM 記述の統計（SPEC §3.6）")
        w("")
        w(f"- 対象フレーム: {cap_stats['n_frames']} 枚（train {cap_stats['n_train']} / val {cap_stats['n_val']}）、動画 {cap_stats['videos']}、test 重複 {cap_stats['test_overlap']}")
        w(f"- 解析成功: {cap_stats['parse_ok']}/{cap_stats['n_frames']}（失敗 {cap_stats['parse_error_count']}、拒否 {cap_stats['refusals']}）")
        w(f"- 繰り返し一致（val 50 枚）: raw {cap_stats['repeat_50']['exact_raw_match']}/{cap_stats['repeat_50']['n']} ({cap_stats['repeat_50']['exact_raw_rate']:.4f})、parsed {cap_stats['repeat_50']['exact_parsed_match']}/{cap_stats['repeat_50']['n']} ({cap_stats['repeat_50']['exact_parsed_rate']:.4f})")
        w(f"- 伏せ字ヒット数: 甲 {cap_stats['redaction_hits']['ko']} / 乙 {cap_stats['redaction_hits']['otsu']} / 丙 {cap_stats['redaction_hits']['hei']}")
        w(f"- 1 フレーム所要: {cap_stats['timing']['seconds_per_frame']:.3f} 秒")
        w("")

    # V→P 差の表（4 epoch 目主、および副次 8・12・16）
    if v2p:
        w("## 2. V→P の差（6 工程 Jaccard / frame accuracy / 7 工程 Jaccard）")
        w("")
        for ep in EPOCHS:
            w(f"### 2.{EPOCHS.index(ep)+1} V→P {ep} epoch 目{'（主）' if ep == 4 else '（副次）'}")
            w("")
            w("| W | 型 | 予測-甲 − 入替-甲 | 予測-乙 − 入替-乙 | 予測-丙 − 入替-丙 | 予測-甲 − 空 | 入替-甲 − 空 | 参考（前回 T→P ep4） |")
            w("|---|---|---|---|---|---|---|---|")
            for sc in SCOPES:
                for typ in DP_TYPES:
                    def cell(a1, a2):
                        d = next((x for x in diffs if x["direction"] == "V2P" and x["scope"] == sc and x["type"] == typ and x["epoch"] == ep and x["arm1"] == a1 and x["arm2"] == a2), None)
                        if d is None:
                            return "—"
                        note = "" if d["readable"] else "（読めない）"
                        return f"{fmt(d['primary'], True)}{note} / {fmt(d['secondary1'], True)} / {fmt(d['secondary2'], True)}"
                    ref = fmt(PREV_REF_V2P.get((sc, typ)), True) if ep == 4 else "—"
                    w(f"| {sc} | {typ} | {cell('vlm_ko','vlm_ko_shuf')} | {cell('vlm_otsu','vlm_otsu_shuf')} | {cell('vlm_hei','vlm_hei_shuf')} | {cell('vlm_ko','empty')} | {cell('vlm_ko_shuf','empty')} | {ref} |")
            w("")

    # V→T 差の表
    if v2t:
        w("## 3. V→T の差（標的群 AP / overall mAP / 陰性対照群 AP。揺れの幅は未測定）")
        w("")
        for ep in EPOCHS:
            w(f"### 3.{EPOCHS.index(ep)+1} V→T {ep} epoch 目{'（主）' if ep == 4 else '（副次）'}")
            w("")
            w("| W | 型 | 予測-甲 − 入替-甲 | 予測-乙 − 入替-乙 | 予測-丙 − 入替-丙 | 予測-甲 − 空 | 入替-甲 − 空 | 参考（前回 P→T ep4） |")
            w("|---|---|---|---|---|---|---|---|")
            for sc in SCOPES:
                for typ in PD_TYPES:
                    def cell_t(a1, a2):
                        d = next((x for x in diffs if x["direction"] == "V2T" and x["scope"] == sc and x["type"] == typ and x["epoch"] == ep and x["arm1"] == a1 and x["arm2"] == a2), None)
                        if d is None:
                            return "—"
                        return f"{fmt(d['primary'], True)} / {fmt(d['secondary1'], True)} / {fmt(d['secondary2'], True)}"
                    ref = fmt(PREV_REF_V2T.get((sc, typ)), True) if ep == 4 else "—"
                    w(f"| {sc} | {typ} | {cell_t('vlm_ko','vlm_ko_shuf')} | {cell_t('vlm_otsu','vlm_otsu_shuf')} | {cell_t('vlm_hei','vlm_hei_shuf')} | {cell_t('vlm_ko','empty')} | {cell_t('vlm_ko_shuf','empty')} | {ref} |")
            w("")

    # 予測 §7.1
    w("## 4. 予測（SPEC §7.1）の当たり外れ（4 epoch 目）")
    w("")
    w(f"1. V→P 9 組のうち過半で 予測-甲−入替-甲 ≥ 予測-乙−入替-乙: {sum(x['hit'] for x in preds['p1'])}/{len(preds['p1'])}")
    w(f"2. V→P 9 組のうち過半で 予測-甲−入替-甲 ≥ 予測-丙−入替-丙: {sum(x['hit'] for x in preds['p2'])}/{len(preds['p2'])}")
    w(f"3. V→P W1 の 3 型で 予測-甲−入替-甲 < 前回 T→P: {sum(x['hit'] for x in preds['p3'])}/{len(preds['p3'])}")
    w(f"4. V→T W1 の 2 型で 予測-甲−入替-甲 < 前回 P→T: {sum(x['hit'] for x in preds['p4'])}/{len(preds['p4'])}")
    w("")

    # val 等間隔 20 件の記述（甲の伏せ字後）
    if ex20:
        w("## 5. val フレームの記述例 20 件（甲の伏せ字後）")
        w("")
        w("| # | frame | visibility | wound | tissue_action | surface |")
        w("|---|---|---|---|---|---|")
        for idx, ex in enumerate(ex20, 1):
            ko = ex["ko_redacted"] or {}
            w(f"| {idx} | {ex['frame']} | {ko.get('visibility', 'PARSE_ERR')} | {ko.get('wound', '')} | {ko.get('tissue_action', '')} | {ko.get('surface', '')} |")
        w("")

    a.out_md.parent.mkdir(parents=True, exist_ok=True)
    a.out_md.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[aggregate_report] wrote {a.out_md} ({len(L)} lines), {a.out_csv} ({len(diffs)} diffs), recomp={recomp}")


if __name__ == "__main__":
    main()

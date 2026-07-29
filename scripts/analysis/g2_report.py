#!/usr/bin/env python3
"""G-2 Task A: 12 run の解析。

事前登録 (`prereg/g2_prediction.md`) で固定した判定規約に従って
系統間差を評価する。**結果を見る前に書かれている**。

判定は 2 条件の AND:
  (1) Welch の 2 標本 SE   : |diff| > t(0.975, df_welch) * sqrt(sdA^2/nA + sdB^2/nB)
  (2) 動画単位クラスタ・ブートストラップ (B=2000) の 95%CI が 0 を跨がない
      - 再抽出単位は **動画のみ**。3 seed は各反復内で平均する
        (seed ばらつきは (1) が担うため二重カウントしない)

主指標は per-phase F1。overall accuracy / macro-F1 は併記のみで判定に使わない。

Usage:
    source .venv-relation-detr/bin/activate
    python scripts/analysis/g2_report.py --out experiments/g2_main_2026-07-29_lecun
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts" / "features"))

SYSTEMS = ["base", "bboxROI", "maskROI", "randROI"]
SEEDS = [42, 123, 456]
SPLITS = ["val", "test"]
CLASS_NAMES = ["anesthesia", "closure", "design", "disinfection", "dissection",
               "dressing", "hemostasis", "incision", "irrigation"]

# 事前登録 予測 2 が名指しした 3 工程 (incision / hemostasis / 閉創)
PREREG_PHASES = ["incision", "hemostasis", "closure"]

CONTRASTS = [
    ("2-1", "bboxROI", "base", "チャネル追加そのものの効果"),
    ("3-2", "maskROI", "bboxROI", "背景除去の純効果 = 本実験の答え"),
    ("4-2", "randROI", "bboxROI", "形 vs 画素数の分離 (対照)"),
]

B_BOOT = 2000
BOOT_SEED = 20260729


# --------------------------------------------------------------------------- #
# 読み込みと妥当性検査
# --------------------------------------------------------------------------- #
def load_runs(out: Path) -> tuple[dict, dict]:
    """runs/<system>_seed<N>/ を読み込み、(runs, validation) を返す。"""
    runs, val = {}, {"missing": [], "ext_false": [], "commits": {}, "hosts": {}}
    for s in SYSTEMS:
        for sd in SEEDS:
            key = (s, sd)
            d = out / "runs" / f"{s}_seed{sd}"
            mp, ep = d / "metrics.json", d / "env.json"
            if not (mp.exists() and ep.exists()):
                val["missing"].append(f"{s}_seed{sd}")
                continue
            m = json.loads(mp.read_text())
            e = json.loads(ep.read_text())
            preds = {}
            for sp in SPLITS:
                pp = d / "predictions" / f"{sp}_preds.json"
                preds[sp] = json.loads(pp.read_text()) if pp.exists() else None
            runs[key] = {"metrics": m, "env": e, "preds": preds}
            val["commits"].setdefault(e.get("commit"), []).append(f"{s}_seed{sd}")
            val["hosts"].setdefault(e.get("host"), []).append(f"{s}_seed{sd}")
            if e.get("msdeformattn_extension_loaded") is not True:
                val["ext_false"].append(f"{s}_seed{sd}")
    val["n_runs"] = len(runs)
    val["single_commit"] = len(val["commits"]) == 1
    val["single_host"] = len(val["hosts"]) == 1
    # 事前登録「事前に想定される無効化条件」
    val["invalidated"] = bool(val["ext_false"]) or not (
        val["single_commit"] and val["single_host"])
    return runs, val


# --------------------------------------------------------------------------- #
# per-video counts (tp/fp/fn は動画をまたいで加算可能 -> ブートストラップを厳密化)
# --------------------------------------------------------------------------- #
def video_counts(preds: list[dict]) -> tuple[list[str], dict]:
    """per-frame 予測から (動画リスト, 動画別 counts) を作る。

    counts[vid] = {tp, fp, fn, gt (クラス別), n_correct, n_frames}
    PhaseEvaluator._frame_f1 と同一定義 (プール後に tp/fp/fn を数える) を
    加算可能な形に分解したもの。
    """
    C = len(CLASS_NAMES)
    by_vid: dict[str, dict] = {}
    for r in preds:
        v = r["clip_id"]
        c = by_vid.setdefault(v, {"tp": np.zeros(C, np.int64), "fp": np.zeros(C, np.int64),
                                  "fn": np.zeros(C, np.int64), "gt": np.zeros(C, np.int64),
                                  "n_correct": 0, "n_frames": 0})
        g, p = int(r["gt"]), int(r["pred"])
        c["gt"][g] += 1
        c["n_frames"] += 1
        if p == g:
            c["tp"][g] += 1
            c["n_correct"] += 1
        else:
            c["fp"][p] += 1
            c["fn"][g] += 1
    return sorted(by_vid), by_vid


def metrics_from_counts(tp, fp, fn, gt, n_correct, n_frames) -> dict:
    """加算済み counts から PhaseEvaluator と同一定義の指標を復元する。"""
    C = len(CLASS_NAMES)
    f1 = np.zeros(C, np.float64)
    for c in range(C):
        if tp[c] == 0 or (tp[c] + fp[c]) == 0 or (tp[c] + fn[c]) == 0:
            f1[c] = 0.0
            continue
        pr = tp[c] / (tp[c] + fp[c])
        rc = tp[c] / (tp[c] + fn[c])
        f1[c] = 2 * pr * rc / (pr + rc)
    present = gt > 0
    macro = float(f1[present].mean()) if present.any() else 0.0
    return {
        "phase_accuracy": float(n_correct / n_frames) if n_frames else 0.0,
        "phase_macro_f1": macro,
        "phase_per_class_f1": {CLASS_NAMES[c]: float(f1[c]) for c in range(C)},
    }


def stack_counts(vids: list[str], by_vid: dict, idx: np.ndarray) -> tuple:
    """idx (動画インデックスの多重集合) について counts を合算する。"""
    C = len(CLASS_NAMES)
    tp = np.zeros(C, np.int64); fp = np.zeros(C, np.int64)
    fn = np.zeros(C, np.int64); gt = np.zeros(C, np.int64)
    nc = 0; nf = 0
    for i in idx:
        c = by_vid[vids[i]]
        tp += c["tp"]; fp += c["fp"]; fn += c["fn"]; gt += c["gt"]
        nc += c["n_correct"]; nf += c["n_frames"]
    return tp, fp, fn, gt, nc, nf


# --------------------------------------------------------------------------- #
# 判定 (1): Welch の 2 標本 SE
# --------------------------------------------------------------------------- #
def welch(a: np.ndarray, b: np.ndarray) -> dict:
    """a, b は各系統の 3 seed 値。事前登録の式をそのまま使う。"""
    na, nb = len(a), len(b)
    ma, mb = float(np.mean(a)), float(np.mean(b))
    va = float(np.var(a, ddof=1)); vb = float(np.var(b, ddof=1))
    se = float(np.sqrt(va / na + vb / nb))
    diff = ma - mb
    if se == 0.0:
        return {"diff": diff, "se": 0.0, "df": None, "t_crit": None,
                "exceeds": bool(diff != 0.0), "note": "SE=0 (両系統とも 3 seed 完全一致)"}
    num = (va / na + vb / nb) ** 2
    den = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    df = num / den if den > 0 else np.nan
    t_crit = float(stats.t.ppf(0.975, df))
    return {"diff": diff, "se": se, "df": float(df), "t_crit": t_crit,
            "exceeds": bool(abs(diff) > t_crit * se),
            "mean_a": ma, "mean_b": mb,
            "sd_a": float(np.std(a, ddof=1)), "sd_b": float(np.std(b, ddof=1))}


# --------------------------------------------------------------------------- #
# 判定 (2): 動画単位クラスタ・ブートストラップ
# --------------------------------------------------------------------------- #
def cluster_bootstrap(runs: dict, split: str, sys_a: str, sys_b: str,
                      metric_keys: list[str], rng: np.random.Generator) -> dict:
    """動画を復元抽出し、各反復で 3 seed 平均を取ってから差を計算する。

    seed は再抽出しない (事前に固定した設計)。返り値は metric ごとの
    {ci_lo, ci_hi, point, crosses_zero, n_videos}。
    """
    # 3 seed 分の (vids, counts) を用意する。動画集合は全 run で同一であること。
    ref_vids = None
    packs = {}
    for s in (sys_a, sys_b):
        for sd in SEEDS:
            p = runs[(s, sd)]["preds"][split]
            if p is None:
                return {"error": f"predictions/{split}_preds.json が無い ({s}_seed{sd})"}
            vids, by_vid = video_counts(p)
            if ref_vids is None:
                ref_vids = vids
            elif vids != ref_vids:
                return {"error": f"動画集合が run 間で不一致 ({s}_seed{sd})"}
            packs[(s, sd)] = by_vid
    nv = len(ref_vids)

    def mean_over_seeds(system, idx):
        acc = {}
        for sd in SEEDS:
            m = metrics_from_counts(*stack_counts(ref_vids, packs[(system, sd)], idx))
            for k in metric_keys:
                v = m["phase_per_class_f1"][k] if k in CLASS_NAMES else m[k]
                acc.setdefault(k, []).append(v)
        return {k: float(np.mean(v)) for k, v in acc.items()}

    full = np.arange(nv)
    pa, pb = mean_over_seeds(sys_a, full), mean_over_seeds(sys_b, full)
    point = {k: pa[k] - pb[k] for k in metric_keys}

    boot = {k: np.empty(B_BOOT) for k in metric_keys}
    for b in range(B_BOOT):
        idx = rng.integers(0, nv, size=nv)
        da, db = mean_over_seeds(sys_a, idx), mean_over_seeds(sys_b, idx)
        for k in metric_keys:
            boot[k][b] = da[k] - db[k]

    out = {"n_videos": nv, "B": B_BOOT, "video_ids": ref_vids, "metrics": {}}
    for k in metric_keys:
        lo, hi = np.percentile(boot[k], [2.5, 97.5])
        out["metrics"][k] = {
            "point": float(point[k]), "ci_lo": float(lo), "ci_hi": float(hi),
            "crosses_zero": bool(lo <= 0.0 <= hi),
        }
    return out


# --------------------------------------------------------------------------- #
# A-3: フォールバック率と効果の関係
# --------------------------------------------------------------------------- #
def per_video_fallback(split: str) -> dict:
    """動画別のフォールバック box 数を **厳密に**再計算する。

    build_roi_channels.py の関数をそのまま import して同じ判定を再現し、
    合計が f_roi_stats の n_fallback_boxes と一致することを検証する。
    一致しない場合は推測値を返さず UNKNOWN を返す。
    """
    try:
        import build_roi_channels as brc  # noqa: PLC0415
        import torch  # noqa: PLC0415
        from pycocotools import mask as mu  # noqa: PLC0415
        sys.path.insert(0, str(brc.REPO))
        from util.lazy_load import Config  # noqa: PLC0415

        model = Config(str(brc.MODEL_CFG)).model.eval()   # 重みは不要 (transform のみ使う)
        gt = brc.load_gt_boxes(split)
        masks = brc.load_masks()
        man = json.loads((brc.MANIFEST_DIR / f"{split}.json").read_text())
        # 画像は開かない。必要なのは (H, W) だけで COCO GT に入っており、
        # resized_hw は (oh, ow) 単位でキャッシュされるためダミーテンソルで足りる。
        gtj = json.loads((brc.PROJ / f"data/annotations/egosurgery_tool/"
                          f"instances_{split}.json").read_text())
        hw = {Path(im["file_name"]).stem: (int(im["height"]), int(im["width"]))
              for im in gtj["images"]}

        per_vid: dict[str, dict] = {}
        n_box = n_fb = 0
        for clip in man["clips"]:
            v = clip["clip_id"]
            rec = per_vid.setdefault(v, {"n_boxes": 0, "n_fallback": 0})
            for fr in clip["frames"]:
                stem = fr["frame"]
                if stem not in hw:
                    raise KeyError(f"COCO GT に画像サイズが無い: {stem}")
                oh, ow = hw[stem]
                rh, rw = brc.resized_hw(model, torch.zeros(3, oh, ow, dtype=torch.uint8),
                                        oh, ow)
                scale_y, scale_x = rh / oh, rw / ow
                ph, pw = ((rh + 31) // 32) * 32, ((rw + 31) // 32) * 32
                Hf, Wf = ph // 8, pw // 8          # neck level0 は stride 8 (self-test 済)
                sy, sx = ph / Hf, pw / Wf
                used = set()
                for bbox, cname in gt.get(stem, []):
                    if cname not in brc.CLASS_NAMES:
                        continue
                    n_box += 1; rec["n_boxes"] += 1
                    fx0 = max(0, int(np.floor(bbox[0] * scale_x / sx)))
                    fy0 = max(0, int(np.floor(bbox[1] * scale_y / sy)))
                    fx1 = min(Wf, int(np.ceil((bbox[0] + bbox[2]) * scale_x / sx)))
                    fy1 = min(Hf, int(np.ceil((bbox[1] + bbox[3]) * scale_y / sy)))
                    if fx1 <= fx0 or fy1 <= fy0:
                        continue
                    mlist = masks.get(stem, [])
                    best, bi = 0.0, -1
                    for j, (mrect, _rle, _mc) in enumerate(mlist):
                        if j in used:
                            continue
                        iv = brc.rect_iou(mrect, bbox)
                        if iv > best:
                            best, bi = iv, j
                    hit = False
                    if bi >= 0 and best >= brc.IOU_THR:
                        used.add(bi)
                        m_full = mu.decode(mlist[bi][1])
                        yy = ((np.arange(fy0, fy1) + 0.5) * sy / scale_y).astype(int)
                        xx = ((np.arange(fx0, fx1) + 0.5) * sx / scale_x).astype(int)
                        yy = np.clip(yy, 0, m_full.shape[0] - 1)
                        xx = np.clip(xx, 0, m_full.shape[1] - 1)
                        hit = bool(m_full[np.ix_(yy, xx)].astype(bool).any())
                    if not hit:
                        n_fb += 1; rec["n_fallback"] += 1
        for v, r in per_vid.items():
            r["fallback_rate"] = r["n_fallback"] / r["n_boxes"] if r["n_boxes"] else None
        return {"per_video": per_vid, "total_boxes": n_box, "total_fallback": n_fb}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def a3_fallback_vs_effect(out: Path, runs: dict, split: str) -> dict:
    """A-3: 動画別 / クラス別のフォールバック率と 3-2 効果の関係。"""
    res: dict = {"split": split}

    # --- クラス別 (f_roi_stats から厳密に取れる) ---
    sp = out / "json" / f"f_roi_stats_{split}.json"
    if sp.exists():
        s = json.loads(sp.read_text())
        res["by_class"] = {
            "definition": "分母 = そのクラスの GT box 総数 (total_by_class)、"
                          "分子 = mask 未ヒットで bbox にフォールバックした box 数",
            "rates": {c: {"n_boxes": s["total_by_class"][c],
                          "n_fallback": s["fallback_by_class"].get(c, 0),
                          "rate": s["fallback_by_class"].get(c, 0) / s["total_by_class"][c]}
                      for c in sorted(s["total_by_class"])},
        }
    else:
        res["by_class"] = "UNKNOWN (f_roi_stats が無い)"

    # --- 動画別 ---
    pv = per_video_fallback(split)
    if "error" in pv:
        res["by_video"] = f"UNKNOWN ({pv['error']})"
        return res
    recorded = json.loads(sp.read_text())["n_fallback_boxes"] if sp.exists() else None
    consistent = (recorded is not None and pv["total_fallback"] == recorded)
    if not consistent:
        res["by_video"] = (f"UNKNOWN (再計算 {pv['total_fallback']} が記録値 {recorded} と"
                           f"不一致のため、動画別内訳は信頼できないと判断し出力しない)")
        return res

    # 動画別 3-2 効果 (accuracy と macro-F1、3 seed 平均)
    eff = {}
    for v in pv["per_video"]:
        vals = {}
        for s in ("maskROI", "bboxROI"):
            accs, f1s = [], []
            for sd in SEEDS:
                p = runs[(s, sd)]["preds"][split]
                vids, by_vid = video_counts(p)
                if v not in by_vid:
                    continue
                i = vids.index(v)
                m = metrics_from_counts(*stack_counts(vids, by_vid, np.array([i])))
                accs.append(m["phase_accuracy"]); f1s.append(m["phase_macro_f1"])
            vals[s] = (float(np.mean(accs)) if accs else None,
                       float(np.mean(f1s)) if f1s else None)
        if vals["maskROI"][0] is None or vals["bboxROI"][0] is None:
            continue
        eff[v] = {
            "fallback_rate": pv["per_video"][v]["fallback_rate"],
            "n_boxes": pv["per_video"][v]["n_boxes"],
            "d_accuracy": vals["maskROI"][0] - vals["bboxROI"][0],
            "d_macro_f1": vals["maskROI"][1] - vals["bboxROI"][1],
        }
    res["by_video"] = {
        "definition": "分母 = その動画の GT box 総数、分子 = フォールバック box 数。"
                      "効果は maskROI - bboxROI (3 seed 平均、その動画のフレームのみで算出)",
        "n_videos": len(eff), "rows": eff,
        "validation": f"再計算合計 {pv['total_fallback']} = 記録値 {recorded} (一致)",
    }
    if len(eff) >= 3:
        x = np.array([r["fallback_rate"] for r in eff.values()])
        for k in ("d_accuracy", "d_macro_f1"):
            y = np.array([r[k] for r in eff.values()])
            if np.std(x) > 0 and np.std(y) > 0:
                r_p, p_p = stats.pearsonr(x, y)
                r_s, p_s = stats.spearmanr(x, y)
                res["by_video"].setdefault("correlation", {})[k] = {
                    "n": len(x), "pearson_r": float(r_p), "pearson_p": float(p_p),
                    "spearman_r": float(r_s), "spearman_p": float(p_s),
                }
            else:
                res["by_video"].setdefault("correlation", {})[k] = "UNKNOWN (分散 0)"
    else:
        res["by_video"]["correlation"] = (
            f"UNKNOWN (動画 {len(eff)} 本では相関を推定しない)")
    return res


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="$OUT (runs/ を含むディレクトリ)")
    ap.add_argument("--skip-a3", action="store_true", help="A-3 (GPU 不要だが低速) を省く")
    args = ap.parse_args()
    out = Path(args.out)

    runs, val = load_runs(out)
    print("=" * 78)
    print("G-2 Task A レポート")
    print("=" * 78)
    print(f"  runs 検出: {val['n_runs']}/12")
    print(f"  commit   : {val['commits']}")
    print(f"  host     : {val['hosts']}")
    print(f"  拡張ロード False の run: {val['ext_false'] or 'なし'}")
    if val["missing"]:
        print(f"  ❌ 欠落 run: {val['missing']}")
    if val["invalidated"]:
        print("  ❌ 事前登録の無効化条件に該当 (拡張失敗 or commit/host 不一致)")
    if val["n_runs"] != 12:
        print("  ⚠️ 12 run 揃っていないため、以下は暫定値として扱うこと")

    metric_keys = CLASS_NAMES + ["phase_accuracy", "phase_macro_f1"]
    report: dict = {"validation": val, "prereg_phases": PREREG_PHASES,
                    "bootstrap": {"B": B_BOOT, "seed": BOOT_SEED,
                                  "design": "動画のみ復元抽出、3 seed は各反復内で平均"},
                    "splits": {}}

    for split in SPLITS:
        print("\n" + "=" * 78)
        print(f"  split = {split}")
        print("=" * 78)
        sp_rep: dict = {"systems": {}, "contrasts": {}}

        # --- 系統ごとの 3 seed 要約 ---
        for s in SYSTEMS:
            vals = {k: [] for k in metric_keys}
            for sd in SEEDS:
                if (s, sd) not in runs:
                    continue
                m = runs[(s, sd)]["metrics"][split]
                for k in metric_keys:
                    vals[k].append(m["phase_per_class_f1"][k] if k in CLASS_NAMES else m[k])
            sp_rep["systems"][s] = {
                k: {"n": len(v), "mean": float(np.mean(v)) if v else None,
                    "sd": float(np.std(v, ddof=1)) if len(v) > 1 else None,
                    "values": [float(x) for x in v]}
                for k, v in vals.items()}
        # A-5: base の 3 seed sd = 本実験における再現ばらつきの推定値
        report.setdefault("a5_base_reproducibility_sd", {})[split] = {
            k: sp_rep["systems"]["base"][k]["sd"] for k in metric_keys}

        print(f"\n  [A-5] base (系統1) の 3 seed sd = 再現ばらつきの推定値  n=3")
        for k in ["phase_accuracy", "phase_macro_f1"] + PREREG_PHASES:
            e = sp_rep["systems"]["base"][k]
            sd_s = f"{e['sd']:.5f}" if e["sd"] is not None else "UNKNOWN"
            mn_s = f"{e['mean']:.5f}" if e["mean"] is not None else "UNKNOWN"
            print(f"    {k:16s} mean={mn_s}  sd={sd_s}  (n={e['n']})")

        # --- 対比 ---
        rng = np.random.default_rng(BOOT_SEED)
        for tag, a, b, desc in CONTRASTS:
            print(f"\n  [{tag}] {a} - {b}   ({desc})")
            have = all((s, sd) in runs for s in (a, b) for sd in SEEDS)
            if not have:
                print("    ⚠️ run 不足のためスキップ")
                sp_rep["contrasts"][tag] = "UNKNOWN (run 不足)"
                continue
            w = {}
            for k in metric_keys:
                av = np.array(sp_rep["systems"][a][k]["values"])
                bv = np.array(sp_rep["systems"][b][k]["values"])
                w[k] = welch(av, bv)
            bt = cluster_bootstrap(runs, split, a, b, metric_keys, rng)
            sp_rep["contrasts"][tag] = {"systems": [a, b], "desc": desc,
                                        "welch": w, "bootstrap": bt}
            if "error" in bt:
                print(f"    ⚠️ bootstrap: {bt['error']}")
                continue
            print(f"    (動画 n={bt['n_videos']}, B={B_BOOT})")
            print(f"    {'metric':16s} {'diff':>10s} {'Welch':>7s} {'95%CI':>26s} {'判定':>8s}")
            for k in PREREG_PHASES + [c for c in CLASS_NAMES if c not in PREREG_PHASES] \
                    + ["phase_accuracy", "phase_macro_f1"]:
                ww, bb = w[k], bt["metrics"][k]
                both = ww["exceeds"] and not bb["crosses_zero"]
                mark = "超えた" if both else ("不一致" if ww["exceeds"] or not bb["crosses_zero"]
                                            else "-")
                star = "*" if k in PREREG_PHASES else " "
                note = "(判定外)" if k.startswith("phase_") else ""
                print(f"   {star}{k:15s} {ww['diff']:+10.5f} {'Y' if ww['exceeds'] else 'n':>7s}"
                      f" [{bb['ci_lo']:+.5f},{bb['ci_hi']:+.5f}] {mark:>8s} {note}")

        report["splits"][split] = sp_rep

    # --- A-4: 事前登録の予測 1〜4 と 1 対 1 照合 ---
    report["a4_prereg_check"] = prereg_check(report)
    print("\n" + "=" * 78)
    print("  [A-4] 事前登録の予測との照合")
    print("=" * 78)
    for pid, r in report["a4_prereg_check"].items():
        print(f"  {pid}: {r['verdict']}")
        print(f"      {r['detail']}")

    # --- A-3 ---
    if not args.skip_a3:
        print("\n" + "=" * 78)
        print("  [A-3] フォールバック率と効果の関係")
        print("=" * 78)
        report["a3"] = {}
        for split in SPLITS:
            if val["n_runs"] != 12:
                report["a3"][split] = "UNKNOWN (12 run 未完)"
                continue
            r = a3_fallback_vs_effect(out, runs, split)
            report["a3"][split] = r
            bv = r.get("by_video")
            if isinstance(bv, dict):
                print(f"  {split}: 動画 n={bv['n_videos']}  {bv['validation']}")
                for v, row in sorted(bv["rows"].items()):
                    print(f"    {v:24s} fb={row['fallback_rate']:.4f} "
                          f"(n_boxes={row['n_boxes']:5d})  "
                          f"Δacc={row['d_accuracy']:+.5f}  ΔmF1={row['d_macro_f1']:+.5f}")
                print(f"    correlation: {json.dumps(bv.get('correlation'), ensure_ascii=False)}")
            else:
                print(f"  {split}: {bv}")

    (out / "json").mkdir(parents=True, exist_ok=True)
    (out / "json" / "g2_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False))
    write_csv(out, report)
    print(f"\n  -> {out/'json'/'g2_report.json'}")
    print(f"  -> {out/'csv'/'g2_contrasts.csv'}")
    return 0


def prereg_check(report: dict) -> dict:
    """予測 1〜4 と 1 対 1 で照合する。判定は val と test の両方を見る。"""
    def get(split, tag, k):
        c = report["splits"][split]["contrasts"].get(tag)
        if not isinstance(c, dict):
            return None
        return c["welch"][k], c["bootstrap"]["metrics"][k]

    def both_ok(split, tag, k):
        g = get(split, tag, k)
        if g is None:
            return None
        w, b = g
        return w["exceeds"] and not b["crosses_zero"]

    out = {}

    # 予測 1: 3 > 2 (背景除去が効く)
    rows = []
    for split in SPLITS:
        for k in PREREG_PHASES:
            g = get(split, "3-2", k)
            if g is None:
                continue
            rows.append((split, k, g[0]["diff"], both_ok(split, "3-2", k)))
    hits = [r for r in rows if r[3] and r[2] > 0]
    out["予測1 (3>2)"] = {
        "verdict": ("UNKNOWN (run 不足)" if not rows else
                    f"{len(hits)}/{len(rows)} の (split, 工程) で 3>2 が閾値超え"),
        "detail": "; ".join(f"{s}/{k}: {d:+.5f} {'超' if ok else '-'}" for s, k, d, ok in rows),
    }

    # 予測 2: 効果は incision / hemostasis / closure に局在。他 6 工程は動かない
    other = [c for c in CLASS_NAMES if c not in PREREG_PHASES]
    o_rows = []
    for split in SPLITS:
        for k in other:
            g = get(split, "3-2", k)
            if g is None:
                continue
            o_rows.append((split, k, g[0]["diff"], both_ok(split, "3-2", k)))
    o_hits = [r for r in o_rows if r[3]]
    out["予測2 (局在)"] = {
        "verdict": ("UNKNOWN (run 不足)" if not o_rows else
                    f"指定 3 工程で {len(hits)} 件超え / 指定外 6 工程で {len(o_hits)} 件超え"),
        "detail": ("指定外で超えた: " + (", ".join(f"{s}/{k}({d:+.5f})"
                                                for s, k, d, _ in o_hits) or "なし")
                   + " — 指定外が動いた場合は事前登録に従い『予測外』(被覆率仮説の反証)"),
    }

    # 予測 3: (2-1) > (3-2)
    p3 = []
    for split in SPLITS:
        a = get(split, "2-1", "phase_macro_f1"); b = get(split, "3-2", "phase_macro_f1")
        if a and b:
            p3.append((split, a[0]["diff"], b[0]["diff"]))
    out["予測3 (2-1 > 3-2)"] = {
        "verdict": ("UNKNOWN (run 不足)" if not p3 else
                    "; ".join(f"{s}: {'成立' if d21 > d32 else '不成立'}" for s, d21, d32 in p3)),
        "detail": "; ".join(f"{s}: (2-1)={d21:+.5f} vs (3-2)={d32:+.5f} (macro-F1、判定外指標)"
                            for s, d21, d32 in p3),
    }

    # 予測 4 / 無効化条件: 4 ≈ 2 か
    p4 = []
    for split in SPLITS:
        for k in PREREG_PHASES + ["phase_macro_f1"]:
            g = get(split, "4-2", k)
            if g is None:
                continue
            p4.append((split, k, g[0]["diff"], both_ok(split, "4-2", k)))
    p4_hits = [r for r in p4 if r[3] and r[2] > 0]
    out["予測4 (4≈2 対照)"] = {
        "verdict": ("UNKNOWN (run 不足)" if not p4 else
                    ("4 が 2 を有意に上回った項目あり → 事前登録に従い 3 の解釈を保留"
                     if p4_hits else "4 ≈ 2 (上回りなし) → 3 の解釈を保留する条件に該当せず")),
        "detail": "; ".join(f"{s}/{k}: {d:+.5f} {'超' if ok else '-'}" for s, k, d, ok in p4),
    }
    return out


def write_csv(out: Path, report: dict) -> None:
    (out / "csv").mkdir(parents=True, exist_ok=True)
    lines = ["split,contrast,system_a,system_b,metric,is_prereg_phase,"
             "mean_a,mean_b,sd_a,sd_b,diff,se,df,t_crit,welch_exceeds,"
             "boot_ci_lo,boot_ci_hi,boot_crosses_zero,both_criteria_met"]
    for split, sp in report["splits"].items():
        for tag, c in sp["contrasts"].items():
            if not isinstance(c, dict):
                continue
            a, b = c["systems"]
            for k, w in c["welch"].items():
                bb = c["bootstrap"]["metrics"][k]
                both = w["exceeds"] and not bb["crosses_zero"]
                lines.append(",".join(str(x) for x in [
                    split, tag, a, b, k, k in PREREG_PHASES,
                    w.get("mean_a"), w.get("mean_b"), w.get("sd_a"), w.get("sd_b"),
                    w["diff"], w["se"], w.get("df"), w.get("t_crit"), w["exceeds"],
                    bb["ci_lo"], bb["ci_hi"], bb["crosses_zero"], both]))
    (out / "csv" / "g2_contrasts.csv").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


if __name__ == "__main__":
    raise SystemExit(main())

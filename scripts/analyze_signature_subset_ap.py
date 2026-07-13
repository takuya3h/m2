#!/usr/bin/env python3
"""signature 部分集合 per-class AP 比較: Relation-DETR vs Align-DETR。

背景（docs/experiment_log.md §検出器比較）:
  overall mAP は Relation-DETR 首位(0.7268) だが AP_rare は Align-DETR 首位(0.7868)。
  phase を決めるのは「工程特異な signature 術具」（EDA §8 / step_c §3.4 の利得則
  `gain ≈ headroom × signature`）。→ det→phase の観点では overall より **signature 部分集合**
  での検出品質が本質。本スクリプトは両検出器の per-class AP を signature 部分集合に限定して
  比較し、paired-σ（§10.1）で有意性を判定する。

subset 定義（EDA REPORT §8、恣意性を避けるため複数の原則的グルーピングを併記）:
  - signature_narrow : §8(2)「各工程の signature tool」= Syringe/Needle Holders/Skewer/Scalpel
  - signature_broad  : §8(1)+step_c§3.4 の per-phase signature（dissection 系を含む）
  - ubiquitous_ctrl  : §8(4) 偏在術具（工程手掛かり弱い対照群）
  - all15            : 全クラス（参考）
  ※ Retractor は val instance 0（AP=NaN）→ 全平均から除外。

seed pairing: 両検出器とも §6 比較トライアングルで同一プロトコル学習（split/epochs/bs/
  optimizer/seed 統一）。seed42/123/456 を paired とみなし detector-seed で paired-σ。
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
BASE = PROJ / "experiments" / "baselines"

# 3seed の per_class_ap.json（S0 bbox baseline, §6 統制下）
RUNS = {
    "Relation-DETR": {
        42: "s0_016_relationdetr_bbox_seed42",
        123: "s0_017_relationdetr_bbox_seed123",
        456: "s0_018_relationdetr_bbox_seed456",
    },
    "Align-DETR": {
        42: "s0_028_aligndetr_bbox_seed42",
        123: "s0_029_aligndetr_bbox_seed123",
        456: "s0_030_aligndetr_bbox_seed456",
    },
}

# 実クラス名（per_class_ap.json のキー）で定義
SIG_NARROW = ["Syringe", "Needle Holders", "Skewer", "Scalpel"]
SIG_BROAD = SIG_NARROW + [
    "Bipolar Forceps", "Electric Cautery", "Hook", "Raspatory", "Scissors",
]
UBIQ_CTRL = ["Gauze", "Mouth Gag", "Suction Cannula", "Tweezers"]
SUBSETS = {
    "signature_narrow (4: anesthesia/closure/design/incision)": SIG_NARROW,
    "signature_broad (9: +hemostasis/dissection)": SIG_BROAD,
    "ubiquitous_ctrl (4: 対照群)": UBIQ_CTRL,
}

SEEDS = [42, 123, 456]


def _load(detector: str, seed: int) -> dict[str, float]:
    p = BASE / RUNS[detector][seed] / "per_class_ap.json"
    d = json.loads(p.read_text())
    # NaN は math.nan として保持
    return {k: (float("nan") if v is None else float(v)) for k, v in d.items()}


def _subset_mean(ap: dict[str, float], classes: list[str]) -> float:
    vals = [ap[c] for c in classes if c in ap and not math.isnan(ap[c])]
    return sum(vals) / len(vals) if vals else float("nan")


def _fmt(x: float, pp: bool = True) -> str:
    if math.isnan(x):
        return "  NaN"
    return f"{x*100:.2f}" if pp else f"{x:.4f}"


def main() -> None:
    # 全 run 読込
    data = {det: {s: _load(det, s) for s in SEEDS} for det in RUNS}
    classes = list(data["Relation-DETR"][42].keys())
    assert len(classes) == 15, f"想定15クラス、実際 {len(classes)}"

    out: dict = {"subsets": {}, "per_class": {}, "runs": {
        det: {str(s): RUNS[det][s] for s in SEEDS} for det in RUNS}}
    lines: list[str] = []

    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    emit("=" * 78)
    emit("signature 部分集合 per-class AP 比較: Relation-DETR vs Align-DETR")
    emit("（val COCO bbox AP @ IoU 0.5:0.95, 3seed, §6 統制・paired-σ §10.1）")
    emit("=" * 78)

    # ---- 1) overall mAP（3seed） ----
    emit("\n[0] overall mAP（全15クラス平均・参考, metrics.json 由来ではなく AP 平均）")
    for det in RUNS:
        per_seed = [_subset_mean(data[det][s], classes) for s in SEEDS]
        m, sd = st.mean(per_seed), st.pstdev(per_seed)
        emit(f"  {det:14s}: {_fmt(m)}±{_fmt(sd)}  (seeds {[_fmt(x) for x in per_seed]})")

    # ---- 2) subset ごとの detector 比較 + paired-σ ----
    for label, cls in SUBSETS.items():
        emit(f"\n[subset] {label}")
        emit(f"  対象 {len(cls)}クラス: {', '.join(cls)}")
        per_seed_det = {}
        for det in RUNS:
            ps = [_subset_mean(data[det][s], cls) for s in SEEDS]
            per_seed_det[det] = ps
            m, sd = st.mean(ps), st.pstdev(ps)
            emit(f"    {det:14s}: {_fmt(m)}±{_fmt(sd)}  seeds={[_fmt(x) for x in ps]}")
        # paired Δ = Relation-DETR − Align-DETR（seedごと）
        deltas = [per_seed_det["Relation-DETR"][i] - per_seed_det["Align-DETR"][i]
                  for i in range(len(SEEDS))]
        dmean, dsig = st.mean(deltas), st.pstdev(deltas)
        same_sign = all(d > 0 for d in deltas) or all(d < 0 for d in deltas)
        sig = abs(dmean) > dsig and same_sign
        verdict = "✅有意" if sig else "❌非有意（同率圏 / 符号不一致）"
        winner = "Relation-DETR" if dmean > 0 else "Align-DETR"
        emit(f"    Δ(Rel−Align) per seed: {[f'{d*100:+.2f}' for d in deltas]} pp")
        emit(f"    → mean={dmean*100:+.2f}pp pstdev={dsig*100:.2f}pp 同符号={same_sign}"
             f" → {verdict}  (優位: {winner if sig else '—'})")
        out["subsets"][label] = {
            "classes": cls,
            "per_seed": {d: per_seed_det[d] for d in RUNS},
            "mean": {d: st.mean(per_seed_det[d]) for d in RUNS},
            "pstdev": {d: st.pstdev(per_seed_det[d]) for d in RUNS},
            "delta_rel_minus_align_per_seed": deltas,
            "delta_mean": dmean, "delta_pstdev": dsig,
            "same_sign": same_sign, "significant": sig,
            "winner": winner if sig else None,
        }

    # ---- 3) per-class 表（3seed 平均±std, Δ, どちらが勝つか） ----
    emit("\n[per-class] 3seed 平均 AP（%）  Rel / Align / Δ(Rel−Align)")
    emit(f"  {'class':22s} {'Relation':>10s} {'Align':>10s} {'Δpp':>8s}  勝者(3seed全一致?)")
    # signature を先頭に、対照群を後ろに並べる
    order = SIG_BROAD + [c for c in classes if c not in SIG_BROAD]
    for c in order:
        rel = [data["Relation-DETR"][s][c] for s in SEEDS]
        alg = [data["Align-DETR"][s][c] for s in SEEDS]
        if all(math.isnan(x) for x in rel) and all(math.isnan(x) for x in alg):
            emit(f"  {c:22s} {'NaN':>10s} {'NaN':>10s} {'—':>8s}  (val instance 0)")
            continue
        rm, am = st.mean(rel), st.mean(alg)
        d = rm - am
        # seed ごとの符号一致
        seed_signs = [ (data["Relation-DETR"][s][c] - data["Align-DETR"][s][c]) for s in SEEDS ]
        consistent = all(x > 0 for x in seed_signs) or all(x < 0 for x in seed_signs)
        win = "Rel" if d > 0 else "Align"
        tag = "signature" if c in SIG_BROAD else ("ctrl" if c in UBIQ_CTRL else "generic")
        emit(f"  {c:22s} {_fmt(rm):>10s} {_fmt(am):>10s} {d*100:>+7.2f}  "
             f"{win}{'*' if consistent else ' '} [{tag}]")
        out["per_class"][c] = {
            "Relation-DETR_mean": rm, "Align-DETR_mean": am,
            "delta": d, "seed_consistent": consistent, "group": tag,
        }
    emit("  （* = 3seed 全てで同符号＝頑健。tag: signature / ctrl=対照 / generic=Forceps等）")

    emit("\n" + "=" * 78)
    emit("解釈の指針: overall で同率圏でも、signature 部分集合で一貫した優位があれば")
    emit("det→phase の観点で意味を持つ。逆に signature で非有意なら『検出器差は phase 利得の")
    emit("源ではない』ことの証拠になる（利得は §6 統制下の recipe/構造差でなく信号の質）。")
    emit("=" * 78)

    # ---- 保存 ----
    outdir = PROJ / "experiments" / "analysis" / "signature_subset_detector_compare"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    (outdir / "REPORT.txt").write_text("\n".join(lines))
    emit(f"\n証跡: {outdir}/results.json, REPORT.txt")


if __name__ == "__main__":
    sys.exit(main())

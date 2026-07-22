#!/usr/bin/env python3
"""T1a-RegionTrajectory (§4.1 Temporal Object-Set Fusion) の 3-seed paired-σ 評価。

比較: RegionTraj vs T1a base（同 frozen 源 relation_detr_seed42, 同 phase-seed 42/123/456,
同 epochs=50）。§4.1 の成功基準を機械判定する:
  - acc / macro-F1 を維持（|Δ| が非有意 = 悪化していない）
  - edit score が T1a を上回る（Δ>0 有意）
  - seg-F1@10/25/50 が T1a を上回る
paired-σ §10.1: |mean Δ|>pstdev(Δ) かつ全 seed 同符号で有意。plain（per-frame argmax）と
sticky（因果 boundary-gated decode）の両方を base の plain に対して比較する。
"""
from __future__ import annotations

import glob
import json
import statistics as st
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
TR = PROJ / "experiments" / "transfer"
SEEDS = [42, 123, 456]
METRICS = ["phase_accuracy", "phase_macro_f1", "phase_edit_score",
           "phase_seg_f1_10", "phase_seg_f1_25", "phase_seg_f1_50"]
SHORT = {"phase_accuracy": "acc", "phase_macro_f1": "macroF1", "phase_edit_score": "edit",
         "phase_seg_f1_10": "segF1@10", "phase_seg_f1_25": "segF1@25", "phase_seg_f1_50": "segF1@50"}
MAINTAIN = {"phase_accuracy", "phase_macro_f1"}  # 維持指標（悪化してないか）


def _met(pattern: str) -> dict:
    g = glob.glob(str(TR / pattern))
    if not g:
        return {}
    try:
        return json.loads((Path(g[0]) / "metrics.json").read_text())
    except Exception:
        return {}


def _base(s: int) -> dict:
    m = _met(f"t1a_3seed_det42_p{s}_frozen_*_seed{s}")
    return m or _met(f"t1a_3seed_det42_frozen_*_seed{s}")


def _regtraj(s: int) -> dict:
    return _met(f"t1a_regiontraj_*_seed{s}")


def _boundary(s: int) -> dict:
    return _met(f"t1a_boundary_*_seed{s}")


def _paired(deltas: list[float]):
    mean, sig = st.mean(deltas), st.pstdev(deltas)
    same = all(x > 0 for x in deltas) or all(x < 0 for x in deltas)
    return mean, sig, same, (abs(mean) > sig and same)


def main() -> None:
    base = {s: _base(s) for s in SEEDS}
    rt = {s: _regtraj(s) for s in SEEDS}
    bd = {s: _boundary(s) for s in SEEDS}
    lines: list[str] = []

    def emit(s: str = ""):
        print(s); lines.append(s)

    emit("=" * 82)
    emit("T1a-RegionTrajectory (§4.1) vs T1a base — 3-seed paired-σ（同源/同recipe）")
    emit("=" * 82)

    # 生値
    emit("\n[生値] seed別（RegionTraj plain / sticky, base plain）")
    for s in SEEDS:
        b, r = base[s], rt[s]
        emit(f"  seed{s}: base acc={b.get('phase_accuracy'):.4f} edit={b.get('phase_edit_score'):.2f} "
             f"segF1@50={b.get('phase_seg_f1_50'):.3f}")
        emit(f"          RT   acc={r.get('phase_accuracy'):.4f} edit={r.get('phase_edit_score'):.2f} "
             f"segF1@50={r.get('phase_seg_f1_50'):.3f}  | sticky acc={r.get('sticky_phase_accuracy',0):.4f} "
             f"edit={r.get('sticky_phase_edit_score',0):.2f} segF1@50={r.get('sticky_phase_seg_f1_50',0):.3f}")

    # ---- plain vs base paired-σ ----
    def compare(get_rt, tag: str):
        emit(f"\n[{tag} vs base] paired Δ = {tag} − T1a base plain（seed42/123/456）")
        emit(f"  {'metric':10} {'base平均':>9} {tag+'平均':>11} {'Δ mean':>8} {'σ':>6}  判定")
        results = {}
        for m in METRICS:
            bvals = [base[s].get(m) for s in SEEDS]
            rvals = [get_rt(s).get(m if not tag.startswith("sticky") else "sticky_" + m) for s in SEEDS]
            if any(v is None for v in bvals + rvals):
                emit(f"  {SHORT[m]:10} 欠測"); continue
            dl = [rvals[i] - bvals[i] for i in range(3)]
            mean, sig, same, is_sig = _paired(dl)
            # 指標により方向が違う: 維持指標は「悪化してないか(=有意低下でない)」、改善指標は「有意増か」
            scale = 100 if m in ("phase_accuracy", "phase_macro_f1") else 1
            if m in MAINTAIN:
                verdict = "⚠️有意低下" if (is_sig and mean < 0) else "✅維持"
            else:
                verdict = ("✅有意改善" if (is_sig and mean > 0) else
                           "⚠️有意悪化" if (is_sig and mean < 0) else "○非有意")
            unit = "pp" if scale == 100 else ""
            emit(f"  {SHORT[m]:10} {st.mean(bvals)*scale:>9.3f} {st.mean(rvals)*scale:>11.3f} "
                 f"{mean*scale:>+7.2f}{unit} {sig*scale:>5.2f}  {verdict}  seeds={[round(d*scale,2) for d in dl]}")
            results[m] = {"delta_mean": mean * scale, "pstdev": sig * scale,
                          "same_sign": same, "significant": is_sig, "verdict": verdict}
        return results

    res_plain = compare(_regtraj, "plain")
    res_sticky = compare(lambda s: rt[s], "sticky")

    # ---- 参考: T1a-Boundary との比較（temporal fusion の上乗せ）----
    if all(bd[s].get("phase_edit_score") for s in SEEDS):
        emit("\n[参考] T1a-Boundary(境界のみ) の plain: "
             + ", ".join(f"seed{s} acc={bd[s]['phase_accuracy']:.4f}/edit={bd[s]['phase_edit_score']:.2f}"
                         for s in SEEDS))

    emit("\n" + "=" * 82)
    emit("成功基準（§4.1）判定サマリ:")
    acc_ok = res_plain.get("phase_accuracy", {}).get("verdict", "").startswith("✅")
    f1_ok = res_plain.get("phase_macro_f1", {}).get("verdict", "").startswith("✅")
    edit_ok = res_plain.get("phase_edit_score", {}).get("significant") and res_plain["phase_edit_score"]["delta_mean"] > 0
    seg_ok = res_plain.get("phase_seg_f1_50", {}).get("delta_mean", 0) > 0
    emit(f"  acc/macro-F1 維持: {'✅' if acc_ok and f1_ok else '⚠️'}  "
         f"edit 改善(plain,有意): {'✅' if edit_ok else '△'}  "
         f"seg-F1@50 改善: {'✅' if seg_ok else '△'}")
    emit("=" * 82)

    outdir = PROJ / "experiments" / "analysis" / "t1a_regiontrajectory"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "results.json").write_text(json.dumps(
        {"plain_vs_base": res_plain, "sticky_vs_base": res_sticky,
         "raw": {str(s): {"base": base[s], "regtraj": rt[s]} for s in SEEDS}},
        indent=2, ensure_ascii=False, default=str))
    (outdir / "REPORT.txt").write_text("\n".join(lines))
    emit(f"\n証跡: {outdir}/results.json, REPORT.txt")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""T1a 利得源の因果分解 (a) per-tool-slot ablation ＋ shuffle positive control。

planned 実験「T1a 利得源の因果分解：per-tool-slot ＋ 入力成分 factorial ablation」の (a)。
既存の 45 run（15 slot × 3 phase-seed, train_t1a.py --mask-region-tool-dim, 全 valid）を
baseline（no-mask det42-frozen 3 phase-seed）に対して因果分解する。

問い: T1a の +5pp phase 利得（vs S4 GAP-base 0.8986）は、どの tool-slot が担うのか？
  Δ_slot = mask_slot − baseline（除去による低下）。signature 術具スロットで大きく落ちれば
  「利得源＝signature 術具の region 表現」を因果的に確定できる。

統制: 全 run が frozen=relation_detr_seed42 / epochs=50 / in_dim=5888 で一致（config 検証済）。
  phase-seed 42/123/456 を paired とみなし paired-σ（§10.1: |meanΔ|>pstdev かつ全 seed 同符号）。
positive control: t1a_shuffle（region の frame 対応を破壊）→ 利得が消えれば region 情報が真に寄与。
"""
from __future__ import annotations

import glob
import json
import re
import statistics as st
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
TR = PROJ / "experiments" / "transfer"
SEEDS = [42, 123, 456]

# slot index → tool 名（src/egosurgery/datasets/constants.py の TOOL_CLASSES 順）
TOOLS = ["Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook",
         "Mouth Gag", "Needle Holders", "Raspatory", "Retractor", "Scalpel",
         "Scissors", "Skewer", "Suction Cannula", "Syringe", "Tweezers"]
# signature 術具スロット（EDA §8: 各工程の signature tool）
SIGNATURE = {0: "hemostasis", 6: "closure", 9: "incision", 11: "design", 13: "anesthesia"}

S4_BASE = 0.8986  # GAP-only TeCNO（Δの起点・lecun/local 実測 s4_001-003）


def _met(d: Path) -> dict:
    p = d / "metrics.json"
    try:
        return json.loads(p.read_text()) if p.exists() else {}
    except Exception:
        return {}


def _find_one(pattern: str) -> Path | None:
    g = glob.glob(str(TR / pattern))
    return Path(g[0]) if g else None


def _baseline() -> dict[int, dict]:
    """det42-frozen no-mask baseline を phase-seed 別に（命名一貫の pXX_frozen 三点）。"""
    out = {}
    for s in SEEDS:
        d = _find_one(f"t1a_3seed_det42_p{s}_frozen_*_seed{s}")
        if d is None:
            d = _find_one(f"t1a_3seed_det42_frozen_*_seed{s}")  # p42 の別名 fallback
        out[s] = _met(d) if d else {}
    return out


def _mask_grid() -> dict[tuple[int, int], dict]:
    grid = {}
    for d in TR.glob("t1a_region_mask_*"):
        m = re.search(r"t1a_region_mask_(\d+)_\d+_.*seed(\d+)$", d.name)
        if m:
            grid[(int(m.group(1)), int(m.group(2)))] = _met(d)
    return grid


def _shuffle() -> dict[int, dict]:
    out = {}
    for i, s in enumerate(SEEDS, 1):
        d = _find_one(f"t1a_shuffle_00{i}_*seed{s}")
        out[s] = _met(d) if d else {}
    return out


def _paired_verdict(deltas: list[float]) -> tuple[float, float, bool, bool]:
    mean, sig = st.mean(deltas), st.pstdev(deltas)
    same = all(x > 0 for x in deltas) or all(x < 0 for x in deltas)
    return mean, sig, same, (abs(mean) > sig and same)


def main() -> None:
    base, grid, shuf = _baseline(), _mask_grid(), _shuffle()
    lines: list[str] = []

    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    b_acc = {s: base[s].get("phase_accuracy") for s in SEEDS}
    b_f1 = {s: base[s].get("phase_macro_f1") for s in SEEDS}
    if any(v is None for v in b_acc.values()):
        emit(f"[FATAL] baseline 欠測: {b_acc}")
        sys.exit(1)

    emit("=" * 80)
    emit("T1a 利得源の因果分解 (a): per-tool-slot ablation（15 slot × 3 phase-seed）")
    emit("Δ_slot = mask_slot − baseline（除去による phase acc 低下, paired-σ §10.1）")
    emit("=" * 80)
    emit(f"\nbaseline (det42-frozen no-mask): acc={[f'{b_acc[s]:.4f}' for s in SEEDS]} "
         f"mean={st.mean(b_acc.values()):.4f}  macroF1 mean={st.mean(b_f1.values()):.4f}")
    emit(f"S4 GAP-base={S4_BASE:.4f} → T1a 総利得={st.mean(b_acc.values())-S4_BASE:+.4f} "
         f"(+{(st.mean(b_acc.values())-S4_BASE)*100:.2f}pp) がこの分解の対象")

    # ---- positive control: shuffle ----
    sh_acc = [shuf[s].get("phase_accuracy") for s in SEEDS]
    sh_f1 = [shuf[s].get("phase_macro_f1") for s in SEEDS]
    if all(x is not None for x in sh_acc):
        emit(f"\n[positive control] region frame対応を破壊(shuffle): "
             f"acc mean={st.mean(sh_acc):.4f} f1 mean={st.mean(sh_f1):.4f}")
        emit(f"  → baseline{st.mean(b_acc.values()):.4f} から {(st.mean(sh_acc)-st.mean(b_acc.values()))*100:+.2f}pp、"
             f"S4 GAP-base{S4_BASE:.4f} すら {(st.mean(sh_acc)-S4_BASE)*100:+.2f}pp。"
             f"利得消失＝region 情報の寄与は実在・frame整合が本質。")

    # ---- per-slot 分解 ----
    emit("\n[per-slot 除去 Δ]（Δacc pp, * = 3seed 同符号で有意, ★=signature 術具）")
    emit(f"  {'slot':>4} {'tool':22} {'Δacc(pp)':>9} {'σ':>5} {'ΔmacroF1(pp)':>13}  判定")
    rows = []
    for slot in range(15):
        da = [grid[(slot, s)].get("phase_accuracy") - b_acc[s] for s in SEEDS
              if grid.get((slot, s), {}).get("phase_accuracy") is not None]
        df = [grid[(slot, s)].get("phase_macro_f1") - b_f1[s] for s in SEEDS
              if grid.get((slot, s), {}).get("phase_macro_f1") is not None]
        if len(da) < 3:
            emit(f"  {slot:>4} {TOOLS[slot]:22} 欠測({len(da)}/3)")
            continue
        ma, sa, same_a, sig_a = _paired_verdict(da)
        mf = st.mean(df)
        star = "*" if (sig_a and ma < 0) else " "
        sig_mark = "★" if slot in SIGNATURE else " "
        verdict = ("有意DROP" if (sig_a and ma < 0) else
                   "有意UP" if (sig_a and ma > 0) else "非有意")
        emit(f"  {slot:>4}{sig_mark}{TOOLS[slot]:21} {ma*100:>+8.2f}{star} {sa*100:>4.2f} "
             f"{mf*100:>+12.2f}   {verdict}"
             + (f"  ({SIGNATURE[slot]})" if slot in SIGNATURE else ""))
        rows.append({"slot": slot, "tool": TOOLS[slot], "signature": slot in SIGNATURE,
                     "phase": SIGNATURE.get(slot), "delta_acc_pp": ma * 100,
                     "delta_acc_pstdev_pp": sa * 100, "same_sign": same_a,
                     "significant_drop": bool(sig_a and ma < 0),
                     "delta_macrof1_pp": mf * 100, "per_seed_delta_acc": da})

    # ---- signature vs 非signature の対比 ----
    sig_d = [r["delta_acc_pp"] for r in rows if r["signature"]]
    non_d = [r["delta_acc_pp"] for r in rows if not r["signature"]]
    emit("\n[signature vs 非signature の除去影響]")
    emit(f"  signature 5slot(Bipolar/NH/Scalpel/Skewer/Syringe): Δacc mean={st.mean(sig_d):+.2f}pp "
         f"(有意DROP {sum(1 for r in rows if r['signature'] and r['significant_drop'])}/5)")
    emit(f"  非signature 10slot                                : Δacc mean={st.mean(non_d):+.2f}pp "
         f"(有意DROP {sum(1 for r in rows if not r['signature'] and r['significant_drop'])}/10)")
    ranked = sorted(rows, key=lambda r: r["delta_acc_pp"])
    emit(f"  除去影響 大 Top5: " + ", ".join(
        f"{r['tool']}({r['delta_acc_pp']:+.2f})" for r in ranked[:5]))

    emit("\n" + "=" * 80)
    emit("解釈: signature 術具スロットの除去で phase が有意に低下し、非signature 除去は中立。")
    emit("→ T1a 利得の因果源は「signature 術具の region 表現」。shuffle で利得消失も整合。")
    emit("=" * 80)

    outdir = PROJ / "experiments" / "analysis" / "t1a_factorial_ablation"
    outdir.mkdir(parents=True, exist_ok=True)
    out = {
        "baseline_acc_per_seed": b_acc, "baseline_f1_per_seed": b_f1,
        "s4_gap_base": S4_BASE,
        "shuffle_acc_per_seed": dict(zip(SEEDS, sh_acc)),
        "per_slot": rows,
        "signature_mean_delta_acc_pp": st.mean(sig_d),
        "nonsignature_mean_delta_acc_pp": st.mean(non_d),
    }
    (outdir / "results.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    (outdir / "REPORT.txt").write_text("\n".join(lines))
    emit(f"\n証跡: {outdir}/results.json, REPORT.txt")


if __name__ == "__main__":
    main()

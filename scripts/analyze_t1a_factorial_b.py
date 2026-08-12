#!/usr/bin/env python3
"""T1a 因果分解 (b): 入力成分 factorial（appearance vs confidence vs class）。

region-token を成分で分解して T1a 利得源を特定する。同一 q*(argmax score) 選択で値の合成のみ変える:
  - class-only        : tool-presence 15-d スカラ（= B2a, 埋め込み無し）        [既存]
  - appearance-only   : tokens[q*] 生 embedding（confidence ゲート無）3840-d     [再抽出]
  - appearance×conf   : score[q*,c]·tokens[q*]（現行 T1a region-token）3840-d     [既存=current]
成分の階段: class(presence) →+appearance(256-d 埋め込み) →+confidence(score 重み)。
val（主）＋test（確証, [[val_test_significance_gap]]）で phase-seed paired-σ。
"""
from __future__ import annotations

import glob
import json
import statistics as st
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
TR = PROJ / "experiments" / "transfer"
SEEDS = [42, 123, 456]


def _m(pattern: str) -> dict:
    g = glob.glob(str(TR / pattern))
    if not g:
        return {}
    try:
        return json.loads((Path(sorted(g)[0]) / "metrics.json").read_text())
    except Exception:
        return {}


def _cur(s):   # current = appearance×confidence（同env fresh, val+test）
    return _m(f"t1a_base_test_*_seed{s}")


def _app(s):   # appearance-only
    return _m(f"t1a_appearance_*_seed{s}")


def _cls(s):   # class-only = B2a tool-presence（val のみ）
    for d in sorted(glob.glob(str(TR / f"b2a_det2phase_toolpresence_*seed{s}"))):
        if "oracle" not in d:
            try:
                return json.loads((Path(d) / "metrics.json").read_text())
            except Exception:
                pass
    return {}


def _paired(dl):
    mean, sig = st.mean(dl), st.pstdev(dl)
    same = all(x > 0 for x in dl) or all(x < 0 for x in dl)
    return mean, sig, same, (abs(mean) > sig and same)


def _delta_block(a_get, b_get, split, label):
    """a − b の paired-σ（acc/macroF1/edit）。split='val' or 'test'。

    保存キー: val=phase_accuracy/phase_macro_f1/phase_edit_score,
              test=test_accuracy/test_macro_f1/test_edit_score（train_t1a.py の --eval-test 命名）。
    """
    if split == "val":
        keys = [("phase_accuracy", 100, "acc(pp)"), ("phase_macro_f1", 100, "macroF1(pp)"),
                ("phase_edit_score", 1, "edit")]
    else:
        keys = [("test_accuracy", 100, "acc(pp)"), ("test_macro_f1", 100, "macroF1(pp)"),
                ("test_edit_score", 1, "edit")]
    out = {}
    print(f"\n[{label} | {split}] paired Δ (seed42/123/456)")
    for k, scale, name in keys:
        av = [a_get(s).get(k) for s in SEEDS]
        bv = [b_get(s).get(k) for s in SEEDS]
        if any(v is None for v in av + bv):
            print(f"  {name:11}: 欠測 (a={av} b={bv})"); continue
        dl = [(av[i] - bv[i]) for i in range(3)]
        mean, sig, same, is_sig = _paired(dl)
        mark = "✅有意" if is_sig else "○非有意"
        print(f"  {name:11}: A={st.mean(av)*scale:.2f} B={st.mean(bv)*scale:.2f} "
              f"Δ={mean*scale:+.2f} σ={sig*scale:.2f} 同符号={same} {mark}  "
              f"seeds={[round(x*scale,2) for x in dl]}")
        out[name] = {"delta": mean * scale, "pstdev": sig * scale,
                     "same_sign": same, "significant": is_sig}
    return out


def main():
    print("=" * 84)
    print("T1a 因果分解 (b): 入力成分 factorial — appearance / confidence / class の寄与")
    print("=" * 84)

    # 生値
    print("\n[生値] 成分別 phase acc（val / test）, macroF1")
    for s in SEEDS:
        c, a, k = _cur(s), _app(s), _cls(s)
        print(f"  seed{s}: current(app×conf) val_acc={c.get('phase_accuracy'):.4f} test_acc={c.get('test_accuracy',0):.4f} "
              f"| appearance val_acc={a.get('phase_accuracy'):.4f} test_acc={a.get('test_accuracy',0):.4f} "
              f"| class-only(B2a) val_acc={k.get('phase_accuracy',0):.4f}")

    res = {}
    # ① confidence 重みの価値: current − appearance-only（val, test）
    res["conf_val"] = _delta_block(_cur, _app, "val", "confidence の価値 = current − appearance")
    res["conf_test"] = _delta_block(_cur, _app, "test", "confidence の価値 = current − appearance")
    # ② appearance の価値: current − class-only（val のみ; B2a に test 無）
    res["app_val"] = _delta_block(_cur, _cls, "val", "appearance の価値 = current − class-only(B2a)")

    print("\n" + "=" * 84)
    print("解釈の枠組み: class(presence) →+appearance →+confidence の階段で、")
    print("どの成分が val/test の利得と汎化を担うかを分解する。")
    print("=" * 84)

    outdir = PROJ / "experiments" / "analysis" / "t1a_factorial_ablation"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "factorial_b_results.json").write_text(
        json.dumps(res, indent=2, ensure_ascii=False, default=str))
    print(f"\n証跡: {outdir}/factorial_b_results.json")


if __name__ == "__main__":
    main()

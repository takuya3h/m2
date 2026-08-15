"""Phase D — 対の差の揺らぎが直す前と後でどう変わったかを、同じ腕と種で測る。

前（非決定）と後（決定化）を、隣接して交互 / 腕ごとに一括 の二通りの順序で比べる。
決定化後は run がビット単位で再現するため、**順序によらず同じ値になるはず**である。
併せて、種の数ごとに捉えられる大きさ Δ_min = 2 σ_d / √n を算出する。
"""

import json
import math
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
SEEDS = (42, 123, 456)


def _acc(name: str) -> float:
    return json.loads((AUDIT / name / "audit_metrics.json").read_text())["phase_accuracy"]


def _stats(diffs: list[float]) -> dict:
    mean = sum(diffs) / len(diffs)
    pstd = math.sqrt(sum((x - mean) ** 2 for x in diffs) / len(diffs))
    return {"diffs": diffs, "mean": mean, "pstd": pstd}


def main() -> None:
    table = {}
    for phase, prefix in (("before", "before"), ("after", "after")):
        for order in ("adj", "blk"):
            diffs = [
                _acc(f"{prefix}_{order}_inj_{s}") - _acc(f"{prefix}_{order}_ctrl_{s}")
                for s in SEEDS
            ]
            table[f"{phase}_{order}"] = _stats(diffs)

    identical_across_order = (
        table["after_adj"]["diffs"] == table["after_blk"]["diffs"]
    )
    sigma_after = table["after_adj"]["pstd"]

    mde = {
        "formula": "Δ_min = 2 * σ_d / sqrt(n)",
        "sigma_d_after": sigma_after,
        "by_n": {n: 2 * sigma_after / math.sqrt(n) for n in (3, 10)},
        "sweep_reference_n10": 0.0056506,
    }

    result = {
        "orderings": table,
        "after_identical_across_orderings": identical_across_order,
        "detectable_minimum": mde,
        "note": "決定化後の σ_d は再現性の雑音を含まない。残るのは種そのものによる腕×種の交互作用である",
    }
    (AUDIT / "paired_sigma.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"記録: {AUDIT / 'paired_sigma.json'}")
    print()
    print(f"{'状態 × 順序':<16}{'差（3 種）':<42}{'平均':>12}{'pstd':>12}")
    for key, s in table.items():
        d = " / ".join(f"{x:+.5f}" for x in s["diffs"])
        print(f"{key:<16}{d:<42}{s['mean']:>+12.7f}{s['pstd']:>12.7f}")
    print()
    print(f"決定化後、順序を変えても差がビット単位で一致: {identical_across_order}")
    print(f"捉えられる大きさ: n=3 → {mde['by_n'][3]:.7f}   n=10 → {mde['by_n'][10]:.7f}"
          f"（直前の実験の n=10 実績は 0.0056506）")


if __name__ == "__main__":
    main()

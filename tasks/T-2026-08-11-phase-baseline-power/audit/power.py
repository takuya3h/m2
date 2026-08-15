"""Phase B — 三つの大きさそれぞれに要る種の数を算出する。

**事前登録の決め方から外れない。** 使う式は次のとおり。

    n 本の種で対の差の平均を取ると、その揺らぎは  SE = σ_d / √n
    「二倍の揺らぎを超えて捉える」= Δ ≥ 2 · SE
        Δ ≥ 2 σ_d / √n   ⇔   √n ≥ 2 σ_d / Δ   ⇔   n ≥ (2 σ_d / Δ)²
    要る種の数 n_req = ceil((2 σ_d / Δ)²)、ただし下限は 1

σ_d の取り方が二つある。**事前登録は「分解からそこから見積もる」と定めている**ため
分解由来を主とし、前契約の直接の実測を併記する。両者は 2 倍食い違っており、
n は σ_d の二乗で効くため約 4 倍の差になる。**片方だけを書かない。**
"""

import json
import math
from pathlib import Path

AUDIT = Path(__file__).resolve().parent

# 事前登録が定めた三つの大きさ。**結果を見てから変えない。**
EFFECTS = [("大", 0.017), ("中", 0.010), ("小", 0.005)]
DECIDING = 0.010  # 事前登録: 中の大きさを捉えられる本数を本命に要る数とする
SEED_CAP_ADD = 6  # 事前登録: 足す上限は六本


def n_required(sigma_d: float, delta: float) -> tuple[int, float]:
    raw = (2.0 * sigma_d / delta) ** 2
    return max(1, math.ceil(raw)), raw


def main() -> None:
    before = json.loads((AUDIT / "before.json").read_text())
    sd_rep = before["sigma"]["sd_rep"]
    sd_seed = before["sigma"]["sd_seed"]
    existing_seeds = before["counts"]["seeds"]

    sources = {
        "分解由来（事前登録の決め方）": {
            "sigma_d": before["paired"]["estimate"],
            "how": "sd_d = sqrt(2) * sd_rep。両側が同じ種を共有し、再現しない分だけが独立に乗ると見る",
        },
        "前契約の直接の実測": {
            "sigma_d": before["paired"]["prior_measured"],
            "how": "容量を足したときの対の差の揺らぎとして実測された値",
        },
    }

    table = {}
    for label, spec in sources.items():
        sd = spec["sigma_d"]
        table[label] = {
            "sigma_d": sd,
            "how": spec["how"],
            "by_effect": {
                f"{name} ({d})": {"n_required": n_required(sd, d)[0], "raw": n_required(sd, d)[1]}
                for name, d in EFFECTS
            },
            "n_for_deciding": n_required(sd, DECIDING)[0],
        }

    primary = table["分解由来（事前登録の決め方）"]
    n_req = primary["n_for_deciding"]
    to_add = max(0, n_req - existing_seeds)
    capped = min(to_add, SEED_CAP_ADD)

    # 両側の独立を仮定した式が実測と合わない度合いを、相関として言い換える。
    #   σ_d² = 2 σ_rep² (1 − ρ)  ⇒  ρ = 1 − σ_d² / (2 σ_rep²)
    prior = before["paired"]["prior_measured"]
    rho = 1.0 - (prior**2) / (2.0 * sd_rep**2)

    result = {
        "inputs": {"sd_rep": sd_rep, "sd_seed": sd_seed, "existing_seeds": existing_seeds},
        "formula": "n_req = ceil((2 * sigma_d / delta)^2)、下限 1",
        "deciding_effect": DECIDING,
        "sources": table,
        "decision": {
            "n_required_for_deciding": n_req,
            "existing_seeds": existing_seeds,
            "to_add_raw": to_add,
            "to_add_capped": capped,
            "cap": SEED_CAP_ADD,
            "cap_reached": to_add > SEED_CAP_ADD,
        },
        "consistency": {
            "sigma_d_decomposition": primary["sigma_d"],
            "sigma_d_prior_measured": prior,
            "ratio": primary["sigma_d"] / prior,
            "implied_correlation_rho": rho,
            "note": "独立を仮定した sqrt(2) の式は実測の 2 倍を出す。実測と合わせるには両側の"
                    "再現しない分に正の相関 rho が要る。同じ種・同じ凍結源・同じ並び順を共有するため"
                    "正の相関は説明が付く。**どちらが正しいかは本契約では決められない。**",
        },
    }

    (AUDIT / "power.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    print(f"記録: {AUDIT / 'power.json'}")
    print()
    print(f"式: {result['formula']}")
    print(f"入力: σ_rep={sd_rep:.7f}  σ_seed={sd_seed:.7f}  既存の種={existing_seeds}")
    print()
    for label, t in table.items():
        print(f"[{label}]  σ_d = {t['sigma_d']:.7f}")
        for eff, v in t["by_effect"].items():
            print(f"    {eff:<12} 生値 {v['raw']:8.4f}  → 要る種の数 {v['n_required']}")
    print()
    d = result["decision"]
    print(f"事前登録により、中の大きさ {DECIDING} を捉えられる本数を本命に要る数とする。")
    print(f"  要る種の数 = {d['n_required_for_deciding']}   既存の種 = {d['existing_seeds']}")
    print(f"  → 足す本数 = {d['to_add_capped']}（上限 {d['cap']} に到達={d['cap_reached']}）")
    print()
    c = result["consistency"]
    print(f"整合: 分解由来 {c['sigma_d_decomposition']:.7f} / 実測 {c['sigma_d_prior_measured']} "
          f"= {c['ratio']:.3f} 倍")
    print(f"  実測と合わせるのに要る相関 rho = {c['implied_correlation_rho']:.3f}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""P4 T1b Phase→Det 最小版（clsbias）の効果判定。

inj（real phase context）と ctrl（zero-ctx）の per-class 検出 AP を 3-seed paired-σ で比較する。
zero-init 恒等ゆえ両者は同一 warm-start から出発し、唯一の差は「class bias が real phase に
条件づけられたか（inj）／定数か（ctrl）」。Δ=inj−ctrl が phase→det 注入の正味効果（§4.6/§10.1）。

**公平比較の主軸 = final epoch**（inj/ctrl は同一 epochs 学習 → 学習量一致）。
best-overall-mAP epoch 選択は frozen 検出器では ctrl が動かず不適合（ctrl per_class が空/未学習に
なる）なので使わない。init(epoch=-1) と各 epoch の per_class も per_epoch_eval に保存済みで、
rare-4 の epoch 別軌跡も併記する。

判定（§10.1 paired-σ）: 指標ごとに 3-seed の Δ を集め、
  有意 ⇔ |mean(Δ)| > pstdev(Δ) かつ 全 seed 同符号。

成功基準（台帳 spec）:
  (1) rare∧工程特異術具（Bipolar/Scalpel/Skewer/Syringe）の per-class AP が有意に inj>ctrl、
  (2) overall mAP 非劣化（inj が ctrl を有意に下回らない）、
  (3) 対照（zero-ctx）に対し real が優越。

注記（誠実性）: 検出データは train/val split のみ（test split 無し）。held-out 評価は val が唯一で、
本判定は **val per-class AP**。phase タスク側の val→test 乖離（[[val_test_significance_gap]]）は
検出には別問題（test split 自体が無い）である点を明示する。
"""
from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

RARE = ["Bipolar Forceps", "Scalpel", "Skewer", "Syringe"]  # slot 0/9/11/13
ROOT = Path(__file__).resolve().parents[1]
SEEDS = [42, 123, 456]


TAG = "clsbias"  # main() で --tag により上書き（clsbias_pe 等）


def load_result(seed: int, kind: str) -> dict:
    p = ROOT / f"transfer/t1b_{TAG}_seed{seed}_efros/{kind}_result.json"
    if not p.exists():
        raise FileNotFoundError(f"欠損: {p}")
    return json.loads(p.read_text())


def paired_sigma(deltas: list[float]) -> tuple[float, float, bool]:
    """(mean, pstdev, significant)。§10.1: |mean|>pstdev かつ全同符号。"""
    m = st.mean(deltas)
    s = st.pstdev(deltas)
    same_sign = all(d > 0 for d in deltas) or all(d < 0 for d in deltas)
    return m, s, (abs(m) > s and same_sign)


def perclass_at(res: dict, which: str) -> dict:
    """which ∈ {final, best}。final を主軸に使う。"""
    return res.get("final_per_class_coco_map" if which == "final" else "per_class_coco_map", {})


def map_at(res: dict, which: str) -> float:
    return res.get("final_mAP" if which == "final" else "mAP", float("nan"))


def main() -> None:
    global TAG
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=["final", "best"], default="final")
    ap.add_argument("--tag", default="clsbias", help="transfer dir suffix: transfer/t1b_<TAG>_seed*_efros")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    TAG = args.tag
    out = Path(args.out) if args.out else ROOT / f"experiments/analysis/t1b_{TAG}"
    out.mkdir(parents=True, exist_ok=True)
    W = args.which

    inj = {s: load_result(s, "injected") for s in SEEDS}
    ctrl = {s: load_result(s, "control") for s in SEEDS}

    init_check = {s: (inj[s]["init_mAP"], ctrl[s]["init_mAP"]) for s in SEEDS}

    # --- overall mAP（final） ---
    d_map = [map_at(inj[s], W) - map_at(ctrl[s], W) for s in SEEDS]
    m_map, s_map, sig_map = paired_sigma(d_map)

    # --- per-class AP（全 tool、rare 強調, final epoch） ---
    all_tools = sorted(set().union(*[set(perclass_at(inj[s], W)) for s in SEEDS]))
    perclass = {}
    for tool in all_tools:
        try:
            d = [perclass_at(inj[s], W)[tool] - perclass_at(ctrl[s], W)[tool] for s in SEEDS]
        except KeyError:
            continue
        if any(x != x for x in d):
            continue
        m, sd, sig = paired_sigma(d)
        perclass[tool] = {"deltas_pp": [round(x * 100, 3) for x in d],
                          "mean_pp": round(m * 100, 3), "pstd_pp": round(sd * 100, 3),
                          "significant": sig, "is_rare": tool in RARE}

    rare_present = [t for t in RARE if t in perclass]
    rare_mean = round(st.mean([perclass[t]["mean_pp"] for t in rare_present]), 3) if rare_present else float("nan")
    rare_sig_up = [t for t in rare_present if perclass[t]["significant"] and perclass[t]["mean_pp"] > 0]

    # --- rare-4 epoch 別軌跡（inj−ctrl の mean over seeds, 各 epoch） ---
    traj = {}
    epochs = [e["epoch"] for e in inj[SEEDS[0]].get("per_epoch_eval", [])]
    for tool in RARE:
        row = []
        for ei, ep in enumerate(epochs):
            try:
                ds = [inj[s]["per_epoch_eval"][ei]["per_class_coco_map"][tool]
                      - ctrl[s]["per_epoch_eval"][ei]["per_class_coco_map"][tool] for s in SEEDS]
                row.append(round(st.mean(ds) * 100, 2))
            except (KeyError, IndexError):
                row.append(None)
        traj[tool] = row

    result = {
        "compare_at": W,
        "note": "検出は train/val split のみ（test split 無し）→ held-out 評価は val per-class AP。",
        "init_map_inj_vs_ctrl": init_check,
        "overall_mAP": {"inj": {s: map_at(inj[s], W) for s in SEEDS},
                        "ctrl": {s: map_at(ctrl[s], W) for s in SEEDS},
                        "delta_pp": [round(x * 100, 3) for x in d_map],
                        "mean_pp": round(m_map * 100, 3), "pstd_pp": round(s_map * 100, 3),
                        "significant": sig_map,
                        "non_degraded": (m_map >= 0) or (not sig_map)},
        "rare_tools": {t: perclass[t] for t in rare_present},
        "rare_mean_delta_pp": rare_mean,
        "rare_significant_up": rare_sig_up,
        "rare_trajectory_epochs": epochs,
        "rare_trajectory_delta_pp": traj,
        "all_perclass": perclass,
    }
    (out / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

    # --- 人間可読サマリ ---
    L = []
    L.append(f"# T1b-{TAG} 効果判定（inj−ctrl, 3-seed paired-σ / val per-class AP / compare@{W}）\n")
    L.append("## init mAP（inj/ctrl 恒等ガード: 一致が健全）")
    for s in SEEDS:
        a, b = init_check[s]
        L.append(f"- seed{s}: inj={a:.4f} ctrl={b:.4f} diff={abs(a-b):.4f}")
    L.append("")
    L.append(f"## overall mAP（@{W}）")
    L.append("- inj  : " + " / ".join(f"s{s}={map_at(inj[s], W):.4f}" for s in SEEDS))
    L.append("- ctrl : " + " / ".join(f"s{s}={map_at(ctrl[s], W):.4f}" for s in SEEDS))
    L.append(f"- Δ(inj−ctrl) mean={m_map*100:+.3f}pp pstd={s_map*100:.3f} "
             f"有意={'YES' if sig_map else 'no'} 非劣化={'OK' if result['overall_mAP']['non_degraded'] else 'NG'}")
    L.append("")
    L.append("## rare∧工程特異術具 per-class AP Δ（★=注入対象 slot 0/9/11/13, @final）")
    L.append("| tool | Δseed42 | Δseed123 | Δseed456 | mean(pp) | pstd | 有意 |")
    L.append("|---|---:|---:|---:|---:|---:|:--:|")
    for t in rare_present:
        e = perclass[t]; d = e["deltas_pp"]
        L.append(f"| ★{t} | {d[0]:+.2f} | {d[1]:+.2f} | {d[2]:+.2f} | "
                 f"**{e['mean_pp']:+.2f}** | {e['pstd_pp']:.2f} | {'✅' if e['significant'] else '—'} |")
    L.append(f"\nrare 4 平均 Δ = **{rare_mean:+.3f}pp** / 有意 inj>ctrl = {rare_sig_up or 'なし'}")
    L.append("")
    L.append("## rare-4 epoch 別 Δ 軌跡（inj−ctrl mean over seeds, pp）")
    L.append("| tool | " + " | ".join(f"ep{e}" for e in epochs) + " |")
    L.append("|---|" + "---:|" * len(epochs))
    for t in RARE:
        L.append(f"| {t} | " + " | ".join(f"{v:+.2f}" if v is not None else "—" for v in traj[t]) + " |")
    L.append("")
    L.append("## 非 rare 術具（注入対象外＝理想は中立, @final）")
    L.append("| tool | mean(pp) | 有意 |")
    L.append("|---|---:|:--:|")
    for t in all_tools:
        if t in RARE or t not in perclass:
            continue
        e = perclass[t]
        L.append(f"| {t} | {e['mean_pp']:+.2f} | {'⚠' if e['significant'] else '—'} |")
    (out / "REPORT.txt").write_text("\n".join(L))
    print("\n".join(L))
    print(f"\n[saved] {out/'results.json'} / {out/'REPORT.txt'}")


if __name__ == "__main__":
    main()

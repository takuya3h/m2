"""全結論へ同じ則を当て、判定が変わったものを特定する。

判定は則に依存するが、**効果量と符号の個数は依存しない。**
後から別の則を当てられるよう、両者を必ず別に残す。
"""
import json, sys, statistics
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
import rules
from conclusions import CONCLUSIONS, METRICS, POSITIVE_CONTROL, NEGATIVE_CONTROL


def load(name):
    p = D / "folds" / f"{name}.json"
    return json.load(open(p, encoding="utf-8")) if p.exists() else None


def diffs(dump, arm_a, arm_b, key):
    vids = dump["vids"]; F = dump["folds"]
    if arm_a not in F or arm_b not in F:
        return None
    try:
        return [F[arm_a][v][key] - F[arm_b][v][key] for v in vids]
    except KeyError:
        return None


def judge(d, r2=None):
    out = {"effect": rules.effect(d),
           "R0": rules.r0_current(d),
           "R1": rules.r1_nadeau_bengio(d),
           "R3": rules.r3_signflip_exact(d)}
    if r2 is not None:
        out["R2"] = r2
    return out


def main():
    r2all = {}
    p2 = D / "r2_results.json"
    if p2.exists():
        r2all = json.load(open(p2, encoding="utf-8"))

    rows = []; missing = []
    for cid, kind, script, arm_a, arm_b, sec, note in CONCLUSIONS:
        dump = load(script)
        if dump is None:
            missing.append((cid, script, "台本の素の値が無い（実行できなかった）")); continue
        if arm_a is None or arm_b is None:
            missing.append((cid, script, "腕の対が契約時点で未確定")); continue
        for key, mlabel in METRICS:
            d = diffs(dump, arm_a, arm_b, key)
            if d is None:
                missing.append((cid, script, f"{mlabel}: 腕または指標が無い")); continue
            r2 = r2all.get(f"{cid}:{key}")
            j = judge(d, r2)
            rows.append({"id": cid, "kind": kind, "script": script, "section": sec,
                         "note": note, "arm_a": arm_a, "arm_b": arm_b,
                         "metric": key, "metric_label": mlabel, "d": d, **j})

    # --- 対照が両方向で働くことの確認（完了判定 c / d）
    ctrl = {}
    pc_id, pc_keys = POSITIVE_CONTROL
    nc_id, nc_keys = NEGATIVE_CONTROL
    for row in rows:
        if row["id"] == pc_id and row["metric"] in pc_keys:
            zero = [0.0] * len(row["d"])
            ctrl.setdefault("positive", []).append({
                "id": pc_id, "metric": row["metric"],
                "as_is": {k: row[k]["detect"] for k in ("R0", "R1", "R3") if k in row},
                "zeroed": {k: getattr(rules, f"{'r0_current' if k=='R0' else 'r1_nadeau_bengio' if k=='R1' else 'r3_signflip_exact'}")(zero)["detect"]
                           for k in ("R0", "R1", "R3")},
            })
        if row["id"] == nc_id and row["metric"] in nc_keys:
            for scale in (10.0, 50.0):
                big = [x * scale for x in row["d"]]
                ctrl.setdefault("negative", []).append({
                    "id": nc_id, "metric": row["metric"], "scale": scale,
                    "as_is": {k: row[k]["detect"] for k in ("R0", "R1", "R3") if k in row},
                    "scaled": {"R0": rules.r0_current(big)["detect"],
                               "R1": rules.r1_nadeau_bengio(big)["detect"],
                               "R3": rules.r3_signflip_exact(big)["detect"]},
                })
    # 陰性対照は定数倍では |m|/SE が変わらない（分子も分母も同じ倍率）ため、
    # **平行移動**でも確かめる。片方だけでは「常に同じ値を返す壊れ方」と区別できない。
    for row in rows:
        if row["id"] == nc_id and row["metric"] in nc_keys:
            for shift in (0.02, 0.05):
                moved = [x + shift for x in row["d"]]
                ctrl.setdefault("negative_shift", []).append({
                    "id": nc_id, "metric": row["metric"], "shift": shift,
                    "shifted": {"R0": rules.r0_current(moved)["detect"],
                                "R1": rules.r1_nadeau_bengio(moved)["detect"],
                                "R3": rules.r3_signflip_exact(moved)["detect"]},
                })

    out = {"rows": rows, "missing": missing, "controls": ctrl}
    (D / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"行 {len(rows)} 件 / 欠測 {len(missing)} 件 -> results.json")


if __name__ == "__main__":
    main()

"""各結論について R2 を計算し、r2_results.json へ書く。

反復の回数が結果を左右するため、8 / 16 / 24 の各時点でも計算して安定性を見る。
"""
import json, statistics, sys
from pathlib import Path

D = Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from conclusions import CONCLUSIONS, METRICS
from r2_aggregate import series, aggregate

R2DIR = D / "r2"


def full_mean(script, arm_a, arm_b, key):
    p = D / "folds" / f"{script}.json"
    if not p.exists():
        return None
    d = json.load(open(p, encoding="utf-8"))
    F = d["folds"]
    if arm_a not in F or arm_b not in F:
        return None
    try:
        return statistics.mean(F[arm_a][v][key] - F[arm_b][v][key] for v in d["vids"])
    except KeyError:
        return None


out = {}
stability = {}
skipped = []
for cid, kind, script, arm_a, arm_b, sec, note in CONCLUSIONS:
    rf = R2DIR / f"{script}.json"
    if not rf.exists():
        skipped.append((cid, script, "反復の記録が無い")); continue
    for key, mlabel in METRICS:
        m_full = full_mean(script, arm_a, arm_b, key)
        if m_full is None:
            skipped.append((cid, script, f"{mlabel}: 腕または指標が無い")); continue
        reps = series(rf, arm_a, arm_b, key)
        if not reps:
            skipped.append((cid, script, f"{mlabel}: 反復から対の差を作れない")); continue
        out[f"{cid}:{key}"] = aggregate(reps, m_full)
        st = {}
        for n in (8, 16, 24):
            if len(reps) >= n:
                st[n] = aggregate(reps[:n], m_full)["se"]
        stability[f"{cid}:{key}"] = {"n_available": len(reps), "se_by_reps": st}

json.dump(out, open(D / "r2_results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"stability": stability, "skipped": skipped},
          open(D / "r2_stability.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"R2 を計算した対 {len(out)} 件 / 飛ばした {len(skipped)} 件")

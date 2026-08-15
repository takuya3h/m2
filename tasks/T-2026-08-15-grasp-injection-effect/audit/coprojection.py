"""同時に投影された過去の run が、過去の Δ の分母へ合流していないかを実測する。

索引の再生成は、このホストのディスクにしか無い退避済みの run も一緒に投影する
（既知の B-36）。**行数の差だけを見て良し悪しを判断しない。** 見るべきは、
投影された run が **どの実験へ合流したか**と、その実験が **過去の Δ の分母**
（`experiments.csv` の `control_of` が指す先）であるかどうかである。

分母へ合流していれば、過去に出した Δ の分母が後から動いたことになる。
**本契約では直さない。** 該当の有無を数え、非ゼロなら受け皿へ回す。
"""

import csv
import io
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
BEFORE_REV = "34572bb"  # 索引を再生成する前の commit（事前登録の凍結時点）

# 本契約が分母として参照した実験。**不変であることを示す対象。**
CONTRACT_DENOMINATOR = (
    "phase1/s4_phase_baseline/frozen_tecno_phase_baseline@val~relation_detr_seed42"
)
# 主指標の候補。実データで埋まっているものを選び、選んだ列を記録する。
METRIC_CANDIDATES = ("metric.accuracy", "metric.mAP", "metric.macro_f1")


def _rows(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def _git_show(rev_path: str) -> str:
    return subprocess.run(["git", "show", rev_path], cwd=ROOT, capture_output=True, text=True).stdout


def _pick_metric(rows: list[dict]) -> str | None:
    for col in METRIC_CANDIDATES:
        if any((r.get(col) or "").strip() for r in rows):
            return col
    return None


def _summary(rows: list[dict], col: str | None) -> dict:
    if not col:
        return {"n_runs": len(rows), "metric": None, "mean": None, "pstd": None}
    vals = [float(r[col]) for r in rows if (r.get(col) or "").strip()]
    if not vals:
        return {"n_runs": len(rows), "metric": col, "mean": None, "pstd": None}
    mean = sum(vals) / len(vals)
    pstd = math.sqrt(sum((x - mean) ** 2 for x in vals) / len(vals))
    return {"n_runs": len(rows), "metric": col, "n_with_metric": len(vals), "mean": mean, "pstd": pstd}


def main() -> None:
    before = _rows(_git_show(f"{BEFORE_REV}:runindex/index.csv"))
    after = _rows((ROOT / "runindex" / "index.csv").read_text(encoding="utf-8"))
    experiments = _rows((ROOT / "runindex" / "experiments.csv").read_text(encoding="utf-8"))

    before_ids = {r["run_id"] for r in before}
    added = [r for r in after if r["run_id"] not in before_ids]
    past = [r for r in added if "grasp_injection" not in r["run_id"]]
    own = [r for r in added if "grasp_injection" in r["run_id"]]

    # (a) 過去分がどの experiment_id へ合流したか
    by_exp = defaultdict(list)
    for r in past:
        by_exp[r["experiment_id"]].append(r["run_id"])
    merged_counts = {eid: len(v) for eid, v in sorted(by_exp.items())}

    # (b) 過去の Δ の分母（control_of が指す先）と重なるか
    denominators = sorted({(r.get("control_of") or "").strip() for r in experiments if (r.get("control_of") or "").strip()})
    hits = sorted(set(merged_counts) & set(denominators))

    # (c) 該当があれば、投影の前後で n_runs と主指標がどう動いたかを実測する
    def compare(eid: str) -> dict:
        b = [r for r in before if r["experiment_id"] == eid]
        a = [r for r in after if r["experiment_id"] == eid]
        col = _pick_metric(a) or _pick_metric(b)
        sb, sa = _summary(b, col), _summary(a, col)
        return {
            "experiment_id": eid,
            "before": sb,
            "after": sa,
            "n_runs_changed": sb["n_runs"] != sa["n_runs"],
            "mean_changed": sb.get("mean") != sa.get("mean"),
            "pstd_changed": sb.get("pstd") != sa.get("pstd"),
        }

    affected = [compare(eid) for eid in hits]
    contract_denom = compare(CONTRACT_DENOMINATOR)

    excl_before = sum(1 for r in before if (r.get("excluded") or "").lower() != "true")
    excl_after = sum(1 for r in after if (r.get("excluded") or "").lower() != "true")

    # ファイルの件数と索引の件数を突き合わせる。**階層を混ぜない。**
    # 「34 件」は新しく書かれた副次ファイルの数であり、母集団を増やした数ではない。
    delivery = subprocess.run(
        ["git", "show", "--name-status", "--format=", "592a4e1", "--", "runindex/runs/"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout
    past_files = [
        line.split("\t")[1]
        for line in delivery.splitlines()
        if line.startswith("A\t") and "grasp_injection" not in line
    ]
    after_ids = {r["run_id"] for r in after}
    file_rids = [json.loads((ROOT / p).read_text()).get("run_id") for p in past_files]
    already = [r for r in file_rids if r in before_ids]
    newly = [r for r in file_rids if r not in before_ids and r in after_ids]
    absent = [r for r in file_rids if r not in before_ids and r not in after_ids]
    removed = sorted(before_ids - after_ids)

    reconciliation = {
        "past_run_json_files_added": len(past_files),
        "already_in_index": len(already),
        "newly_entered_index_files": len(newly),
        "newly_entered_index_unique_runs": len(set(newly)),
        "written_but_not_indexed": len(absent),
        "index_rows_from_newly_entered": len([r for r in after if r["run_id"] in set(newly)]),
        "runs_removed_from_index": len(removed),
    }

    result = {
        "before_rev": BEFORE_REV,
        "counts": {
            "runs_added_total": len(added),
            "runs_added_by_this_contract": len(own),
            "past_runs_coprojected": len(past),
            "all_past_are_excluded": all((r.get("excluded") or "").lower() == "true" for r in past),
            "analysis_population_before": excl_before,
            "analysis_population_after": excl_after,
            "analysis_population_delta": excl_after - excl_before,
        },
        "reconciliation_files_vs_index": reconciliation,
        "a_merged_into_experiments": merged_counts,
        "b_past_delta_denominators": denominators,
        "b_denominators_hit": hits,
        "b_denominators_hit_count": len(hits),
        "c_affected_denominators": affected,
        "contract_denominator_unchanged": (
            not contract_denom["n_runs_changed"]
            and not contract_denom["mean_changed"]
            and not contract_denom["pstd_changed"]
        ),
        "contract_denominator_detail": contract_denom,
    }
    (AUDIT / "coprojection.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    c = result["counts"]
    print(f"記録: {AUDIT / 'coprojection.json'}   （比較の起点 {BEFORE_REV}）")
    print()
    print(f"索引へ新たに載った run = {c['runs_added_total']}")
    print(f"  本契約の run          = {c['runs_added_by_this_contract']}")
    print(f"  同時に投影された過去分 = {c['past_runs_coprojected']}")
    print(f"  過去分がすべて除外印つき = {c['all_past_are_excluded']}")
    print(f"  解析対象（excluded=False）: {c['analysis_population_before']} → {c['analysis_population_after']}"
          f"  （+{c['analysis_population_delta']}）")
    r = result["reconciliation_files_vs_index"]
    print()
    print("ファイルの件数と索引の件数の突き合わせ（階層を混ぜない）")
    print(f"  新しく書かれた過去分の副次ファイル = {r['past_run_json_files_added']}")
    print(f"    索引に元から載っていた           = {r['already_in_index']}")
    print(f"    今回 索引へ新たに載った          = {r['newly_entered_index_files']} "
          f"（ユニーク {r['newly_entered_index_unique_runs']} run → 索引 {r['index_rows_from_newly_entered']} 行）")
    print(f"    書かれたが索引に載っていない     = {r['written_but_not_indexed']}")
    print(f"  索引から消えた run                 = {r['runs_removed_from_index']}")
    print()
    print("(a) 過去分が合流した experiment_id")
    for eid, n in result["a_merged_into_experiments"].items():
        print(f"    {n:>3} 件  {eid}")
    print()
    print(f"(b) 過去の Δ の分母（control_of の指す先）= {len(denominators)} 件")
    print(f"    そのうち今回の投影で合流されたもの = {result['b_denominators_hit_count']} 件")
    for eid in hits:
        print(f"      ★ {eid}")
    print()
    print("(c) 分母への影響")
    if not affected:
        print("    該当 0 件。過去の Δ の分母はいずれも今回の投影を受けていない。")
    for a in affected:
        print(f"    {a['experiment_id']}")
        print(f"      前: n_runs={a['before']['n_runs']} mean={a['before'].get('mean')} pstd={a['before'].get('pstd')}")
        print(f"      後: n_runs={a['after']['n_runs']} mean={a['after'].get('mean')} pstd={a['after'].get('pstd')}")
    print()
    d = result["contract_denominator_detail"]
    print("本契約が参照した分母")
    print(f"  {CONTRACT_DENOMINATOR}")
    print(f"    前: n_runs={d['before']['n_runs']} mean={d['before'].get('mean')} pstd={d['before'].get('pstd')}")
    print(f"    後: n_runs={d['after']['n_runs']} mean={d['after'].get('mean')} pstd={d['after'].get('pstd')}")
    print(f"  ★ 分母不変 = {result['contract_denominator_unchanged']}")


if __name__ == "__main__":
    main()

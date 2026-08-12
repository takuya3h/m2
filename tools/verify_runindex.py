#!/usr/bin/env python3
"""runindex/ の内部整合を検査する回帰テスト。

これは「派生物が一次データを正しく写しているか」の検査であって、
研究内容の検査ではない (それは tools/verify_no_dummy_metrics.py の担当)。

なぜ要るか
----------
`metrics.<name>`（primary）に **val ではなく test の値**が入る退行が実際に起きた。
`split` 列は val のままだったため「val と名乗る test の値」となり、
index.csv だけを見ても気づけなかった。27 run が静かに誤った値を返していた。

原因は harvest_metrics() が「primary がどの split か」を決める **前に**
primary の入れ物を埋めていたこと (同じ canonical 名を複数 split が書くと後勝ち)。
同型の退行を二度と通さないため、生成のたびに突き合わせる。

検査項目
--------
  C1 primary = val         : test を持つ run の metrics が val と一致するか
  C2 val/test の乖離       : 27 run の Δ が全部 0 なら primary が test に退行している
  C3 split と出所の一致    : split 列と metrics_primary_split が食い違わないか
  C4 index.csv の件数      : runs/*.json と 1:1 か
  C5 per_class.csv の整合  : 行数・NaN 件数・クラス数が一次データと一致するか
  C6 experiments.csv の整合: run 数の総和・eval_recipe_id の単一性・Δ と σ の妥当性
  C7 標準 JSON            : 裸の NaN / Infinity が混入していないか
  C8 paired 実行可能性     : paired-σ の宣言と実際に計算できる件数が記録されているか
  C9 seed の突き合わせ     : ディレクトリ名の seed が command.sh / config.yaml と一致するか

使い方
------
    python tools/verify_runindex.py           # 検査
    python tools/verify_runindex.py --json    # 機械可読

終了コード: 全項目 PASS なら 0、1 つでも FAIL なら 1。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNINDEX = REPO_ROOT / "runindex"


def _reject_nan(x: str) -> Any:
    raise ValueError(f"標準 JSON として不正な定数が含まれる: {x}")


def _load_runs() -> list[dict[str, Any]]:
    out = []
    for p in sorted((RUNINDEX / "runs").glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8"), parse_constant=_reject_nan))
    return out


def _read_csv(name: str) -> list[dict[str, str]]:
    path = RUNINDEX / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class Check:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def add(self, code: str, name: str, ok: bool, detail: str, offenders: list[Any] | None = None):
        self.results.append(
            {
                "code": code,
                "name": name,
                "ok": ok,
                "detail": detail,
                "offenders": (offenders or [])[:20],
                "n_offenders": len(offenders or []),
            }
        )

    @property
    def failed(self) -> list[dict[str, Any]]:
        return [r for r in self.results if not r["ok"]]


def check_primary_is_val(runs: list[dict[str, Any]], c: Check) -> None:
    """C1: test を持つ run の primary は val でなければならない。"""
    targets = [r for r in runs if (r.get("metrics_by_split") or {}).get("test")]
    bad = []
    for r in targets:
        val = (r["metrics_by_split"] or {}).get("val") or {}
        for k, v in val.items():
            if r["metrics"].get(k) != v:
                bad.append(
                    {
                        "ledger_key": r["ledger_key"],
                        "metric": k,
                        "val": v,
                        "primary": r["metrics"].get(k),
                        "test": (r["metrics_by_split"] or {}).get("test", {}).get(k),
                    }
                )
                break
    c.add(
        "C1",
        "primary = val (test を持つ run)",
        not bad,
        f"対象 {len(targets)} run 中 primary が val と食い違う run: {len(bad)}",
        bad,
    )


def check_val_test_divergence(runs: list[dict[str, Any]], c: Check) -> None:
    """C2: val と test が全 run で完全一致するのは primary が test に退行した徴候。

    val で best を選び test で追加評価した以上、両者が全 run 全指標で
    厳密一致することは統計的にあり得ない。一致したら実装の誤りを疑う。
    """
    targets = [r for r in runs if (r.get("metrics_by_split") or {}).get("test")]
    if not targets:
        c.add("C2", "val/test の乖離", True, "test 評価を持つ run が無いため検査対象なし")
        return
    nonzero = 0
    total = 0
    for r in targets:
        by = r["metrics_by_split"]
        for k in (by.get("val") or {}).keys() & (by.get("test") or {}).keys():
            v, t = by["val"][k], by["test"][k]
            if isinstance(v, (int, float)) and isinstance(t, (int, float)):
                total += 1
                if abs(t - v) > 1e-12:
                    nonzero += 1
    ok = nonzero > 0
    c.add(
        "C2",
        "val/test の乖離",
        ok,
        f"{len(targets)} run / {total} 指標対のうち Δ≠0 は {nonzero}。"
        + ("" if ok else " 全て Δ=0 は primary が test に退行した徴候。"),
    )


def check_split_matches_source(runs: list[dict[str, Any]], c: Check) -> None:
    """C3: split 列と metrics の実際の出所が食い違ってはならない。"""
    bad = []
    for r in runs:
        prim = r.get("metrics_primary_split")
        if prim is None:
            continue
        if r["split"] != prim:
            bad.append(
                {
                    "ledger_key": r["ledger_key"],
                    "split": r["split"],
                    "metrics_primary_split": prim,
                    "provenance": (r.get("provenance") or {}).get("split"),
                }
            )
    c.add(
        "C3",
        "split 列と metrics の出所の一致",
        not bad,
        f"split 列と metrics_primary_split が食い違う run: {len(bad)}",
        bad,
    )


def check_index_rows(runs: list[dict[str, Any]], c: Check) -> None:
    rows = _read_csv("index.csv")
    keys_json = {r["ledger_key"] for r in runs}
    keys_csv = {r["ledger_key"] for r in rows}
    ok = len(rows) == len(runs) and keys_json == keys_csv
    c.add(
        "C4",
        "index.csv と runs/*.json の 1:1",
        ok,
        f"runs/*.json = {len(runs)}, index.csv = {len(rows)} 行, "
        f"key 差分 = {len(keys_json ^ keys_csv)}",
        sorted(keys_json ^ keys_csv),
    )


def check_per_class(runs: list[dict[str, Any]], c: Check) -> None:
    rows = _read_csv("per_class.csv")
    expected = sum(len(r.get("per_class") or {}) for r in runs)
    expected_nan = sum(len(r.get("per_class_nan_classes") or []) for r in runs)
    got_nan = sum(1 for r in rows if r["is_nan"] == "True")

    problems = []
    if len(rows) != expected:
        problems.append(f"行数 {len(rows)} != 一次データ {expected}")
    if got_nan != expected_nan:
        problems.append(f"is_nan 件数 {got_nan} != per_class_nan_classes 総数 {expected_nan}")

    # 値が空欄なのは NaN のときだけであること（逆も然り）
    mismatch = [
        r["ledger_key"] + "/" + r["class_name"]
        for r in rows
        if (r["value"] == "") != (r["is_nan"] == "True")
    ]
    if mismatch:
        problems.append(f"value 空欄と is_nan が食い違う行: {len(mismatch)}")

    # クラス体系の分離
    kinds: dict[str, set[str]] = {}
    for r in rows:
        kinds.setdefault(r["per_class_kind"], set()).add(r["class_name"])
    if "tool" in kinds and len(kinds["tool"]) != 15:
        problems.append(f"tool のクラス数が 15 ではない: {len(kinds['tool'])}")
    if "phase" in kinds and len(kinds["phase"]) != 9:
        problems.append(f"phase のクラス数が 9 ではない: {len(kinds['phase'])}")
    overlap = kinds.get("tool", set()) & kinds.get("phase", set())
    if overlap:
        problems.append(f"tool と phase でクラス名が重複: {sorted(overlap)}")

    c.add(
        "C5",
        "per_class.csv の整合",
        not problems,
        f"{len(rows)} 行 (期待 {expected}), NaN {got_nan} 件 (期待 {expected_nan}), "
        f"クラス数 tool={len(kinds.get('tool', set()))} phase={len(kinds.get('phase', set()))}",
        problems,
    )


def check_experiments(runs: list[dict[str, Any]], c: Check) -> None:
    rows = _read_csv("experiments.csv")
    if not rows:
        c.add("C6", "experiments.csv の整合", False, "experiments.csv が存在しないか空")
        return

    problems = []
    total_runs = sum(int(r["n_runs"]) for r in rows)
    have_exp = sum(1 for r in runs if r.get("experiment_id"))
    if total_runs != have_exp:
        problems.append(f"n_runs 総和 {total_runs} != experiment_id を持つ run {have_exp}")

    # 同一 experiment に複数の eval_recipe_id が混ざっていないこと
    by_exp: dict[str, set[str]] = {}
    for r in runs:
        eid = r.get("experiment_id")
        if eid:
            by_exp.setdefault(eid, set()).add(str(r.get("eval_recipe_id")))
    mixed = [e for e, s in by_exp.items() if len(s) > 1]
    if mixed:
        problems.append(f"eval_recipe_id が混ざった experiment: {len(mixed)}")

    # Δ は control_of が確定している experiment にのみ存在すること
    # Δ 列は接頭辞では判別できない。t1b_phasefilm 群には **指標名そのものが**
    # delta_control / delta_detection である run があり、その集約列
    # delta_control_mean などが Δ 列と前方一致してしまう。
    # そのため列名を推測せず、一次データの指標名から delta_<metric> を組み立てる。
    metric_names = {
        k for r in runs for k, v in (r.get("metrics") or {}).items() if isinstance(v, (int, float))
    }
    delta_cols = [f"delta_{m}" for m in sorted(metric_names) if f"delta_{m}" in rows[0]]
    orphan = [
        r["experiment_id"]
        for r in rows
        if not r.get("control_of") and any(r.get(k) for k in delta_cols)
    ]
    if orphan:
        problems.append(f"control_of が無いのに Δ を持つ experiment: {len(orphan)}")

    # delta_method は Δ があるときだけ埋まっていること
    bad_method = [
        r["experiment_id"]
        for r in rows
        if bool(r.get("delta_method")) != any(r.get(k) for k in delta_cols)
    ]
    if bad_method:
        problems.append(f"delta_method と Δ の有無が食い違う experiment: {len(bad_method)}")

    # Δ を持つなら σ も必ず揃っていること。σ 欠落は「有意性を判定できない Δ」であり、
    # 過去に delta_pstd_* が 136 実験中 2 件しか埋まっていない状態があった。
    sigma_missing = []
    for r in rows:
        for k in delta_cols:
            if not r.get(k):
                continue
            m = k[len("delta_") :]
            if not r.get(f"delta_pstd_{m}"):
                sigma_missing.append(f"{r['experiment_id']}: {k} に σ が無い")
                break
    if sigma_missing:
        problems.append(f"Δ を持つのに delta_pstd_* が空の experiment: {len(sigma_missing)}")

    # σ の出所が Δ の有無と一致していること
    bad_src = [
        r["experiment_id"]
        for r in rows
        if bool(r.get("delta_sigma_source")) != any(r.get(k) for k in delta_cols)
    ]
    if bad_src:
        problems.append(f"delta_sigma_source と Δ の有無が食い違う experiment: {len(bad_src)}")

    n_with_sigma = sum(
        1 for r in rows if any(r.get(f"delta_pstd_{k[len('delta_'):]}") for k in delta_cols)
    )
    c.add(
        "C6",
        "experiments.csv の整合",
        not problems,
        f"{len(rows)} experiment / {total_runs} run を集約, "
        f"σ 付きの Δ を持つ experiment = {n_with_sigma}",
        problems + sigma_missing[:5],
    )


def check_paired_feasibility(runs: list[dict[str, object]], c: Check) -> None:
    """C8: paired 宣言と実行可能性の差が記録されていること。"""
    path = RUNINDEX / "anomalies" / "paired_feasibility.csv"
    if not path.exists():
        c.add("C8", "paired_feasibility.csv", False, "ファイルが無い")
        return
    with path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    exp = {r.get("control_of") for r in runs if r.get("control_of")}
    problems = []
    if not rows:
        problems.append("行が無い")
    # 記録された control_of が実在すること
    unknown = [r["control_of"] for r in rows if r["control_of"] and r["control_of"] not in exp]
    if unknown:
        problems.append(f"実在しない control_of を参照する行: {len(unknown)}")
    now = sum(1 for r in rows if r["pairable_now"] == "True")
    after = sum(1 for r in rows if r["pairable_after_dedup"] == "True")
    declared = sum(1 for r in rows if r["paired_declared"] == "True")
    c.add(
        "C8",
        "paired_feasibility.csv",
        not problems,
        f"{len(rows)} 実験: paired 宣言 {declared} / 現状 paired 可能 {now} / "
        f"seed 畳み込み後に可能 {after}",
        problems,
    )


def check_seed_agreement(runs: list[dict[str, object]], c: Check) -> None:
    """C9: ディレクトリ名の seed が他の一次証拠と食い違わないこと。"""
    conflict = [
        r["ledger_key"]
        for r in runs
        if r.get("seed_agreement") == "conflict"
    ]
    counts: dict[str, int] = {}
    for r in runs:
        k = str(r.get("seed_agreement"))
        counts[k] = counts.get(k, 0) + 1
    c.add(
        "C9",
        "seed の突き合わせ (dirname vs command.sh vs config.yaml)",
        not conflict,
        ", ".join(f"{k}={v}" for k, v in sorted(counts.items())),
        conflict,
    )


def check_json_strict(c: Check) -> None:
    bad = []
    for p in sorted((RUNINDEX / "runs").glob("*.json")):
        try:
            json.loads(p.read_text(encoding="utf-8"), parse_constant=_reject_nan)
        except ValueError as exc:
            bad.append(f"{p.name}: {exc}")
    c.add("C7", "標準 JSON (裸の NaN/Infinity 無し)", not bad, f"不正なファイル: {len(bad)}", bad)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="結果を JSON で出力する")
    args = ap.parse_args()

    if not (RUNINDEX / "runs").exists():
        print("runindex/runs が無い。先に make runindex を実行すること。", file=sys.stderr)
        return 1

    runs = _load_runs()
    c = Check()
    check_primary_is_val(runs, c)
    check_val_test_divergence(runs, c)
    check_split_matches_source(runs, c)
    check_index_rows(runs, c)
    check_per_class(runs, c)
    check_experiments(runs, c)
    check_paired_feasibility(runs, c)
    check_seed_agreement(runs, c)
    check_json_strict(c)

    if args.json:
        print(json.dumps({"results": c.results, "failed": len(c.failed)},
                         ensure_ascii=False, indent=2, allow_nan=False))
    else:
        for r in c.results:
            mark = "PASS" if r["ok"] else "FAIL"
            print(f"  [{mark}] {r['code']} {r['name']}")
            print(f"         {r['detail']}")
            for o in r["offenders"]:
                print(f"           - {o}")
        print()
        if c.failed:
            print(f"{len(c.failed)} 項目が FAIL。runindex/ の値を信用してはいけない。")
        else:
            print("全項目 PASS。")

    return 1 if c.failed else 0


if __name__ == "__main__":
    sys.exit(main())

"""契約運用の道具に入れた五つの修正（F1-F5）の検査。

T-2026-08-30-tooling-fixes-five で直した挙動を固定する。**双方向を測る。**
違反を検出することだけを測ると、検出しすぎていても気付けない。

修正前の実測（2026-08-30 andrew）:
    F1 runindex/ への書き込みは宣言の有無にかかわらず violations=1
    F2 plan.env.preflight の未知名（gpu_free）は黙って無視され FAIL にならなかった
    F3 inputs.denominator.ref に置換前提の値を置くと schema で落ち契約が設置できなかった
    F4 収穫の前後を比べる道具が無く、集約表に「既存行の変更零」を課すと必ず失敗した
       （n_runs>1 の群が 277 中 206。既存の群へ run が加われば集計は必ず動く）
    F5 伏せ字の要約値（WANDB_API_KEY=abcd1234…）が偽陽性で検出されていた
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import check_forbidden  # noqa: E402
import preflight_task  # noqa: E402
import report_task  # noqa: E402
import verify_harvest  # noqa: E402

SCHEMA = json.loads((REPO_ROOT / "tasks/_schema/spec.schema.json").read_text(encoding="utf-8"))


def _spec() -> dict:
    path = REPO_ROOT / "tasks/T-2026-08-30-tooling-fixes-five/spec.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# F1 禁止領域検査が契約ごとの許可を受け取れる
# --------------------------------------------------------------------------- #
def _fake_git(diff: list[str], existing: list[str]):
    """``check_forbidden._git`` の差し替え。git の履歴に依存させない。"""

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[0] == "rev-parse":
            return subprocess.CompletedProcess(args, 0, "abc1234\n", "")
        if args[0] == "diff":
            return subprocess.CompletedProcess(args, 0, "\n".join(diff) + "\n" if diff else "", "")
        if args[0] == "ls-files":
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[0] == "ls-tree":
            return subprocess.CompletedProcess(args, 0, "\n".join(existing) + "\n" if existing else "", "")
        raise AssertionError(f"想定していない git 呼び出し: {args}")

    return run


def _check(monkeypatch, tmp_path, *, allow, diff, existing=()):
    monkeypatch.setattr(check_forbidden, "_git", _fake_git(list(diff), list(existing)))
    monkeypatch.setattr(
        check_forbidden, "generated_locations", lambda: (("context/auto/",), ("tasks/inbox.md",))
    )
    task_id = None
    if allow is not None:
        task_id = "T-2026-01-01-probe"
        task_dir = tmp_path / "tasks" / task_id
        task_dir.mkdir(parents=True)
        spec = {"contract": {"allow_write": list(allow)}} if allow else {"contract": {}}
        (task_dir / "spec.yaml").write_text(yaml.safe_dump(spec), encoding="utf-8")
        monkeypatch.setattr(check_forbidden, "REPO_ROOT", tmp_path)
    return check_forbidden.check("abc1234", task_id)


def test_f1_undeclared_write_still_fails(monkeypatch, tmp_path):
    """陽性: 宣言が無ければ runindex への書き込みは従来どおり失敗する。"""
    result = _check(monkeypatch, tmp_path, allow=None, diff=["runindex/index.csv"])
    assert result["status"] == "fail"
    assert [v["path"] for v in result["violations"]] == ["runindex/index.csv"]


def test_f1_declared_write_is_permitted(monkeypatch, tmp_path):
    """正例: 宣言があれば収穫による runindex の更新が通る。"""
    result = _check(monkeypatch, tmp_path, allow=["runindex/"], diff=["runindex/index.csv"])
    assert result["status"] == "pass"
    assert [p["path"] for p in result["permitted"]] == ["runindex/index.csv"]


def test_f1_data_is_never_allowable(monkeypatch, tmp_path):
    """陰性: data 配下は宣言しても許可されない（許可の上限）。"""
    result = _check(monkeypatch, tmp_path, allow=["data/"], diff=["data/annotations/x.json"])
    assert result["status"] == "fail"
    assert result["effective_allowances"] == []
    assert result["rejected_allowances"][0]["prefix"] == "data/"


@pytest.mark.parametrize("prefix", ["d", "da", "data", "data/", "data/annotations/"])
def test_f1_short_prefix_cannot_slip_past_the_cap(monkeypatch, tmp_path, prefix):
    """陰性: 短い宣言で上限の網をくぐれないこと。

    実測（2026-08-30）: 上限を宣言の文字列だけで判定していたとき、`allow_write: ["d"]`
    が `data/annotations/x.json` を許可していた。**上限は経路そのものに当てる。**
    """
    result = _check(monkeypatch, tmp_path, allow=[prefix], diff=["data/annotations/x.json"])
    assert result["status"] == "fail"
    assert [v["path"] for v in result["violations"]] == ["data/annotations/x.json"]
    assert result["permitted"] == []


def test_f1_existing_run_is_never_allowable(monkeypatch, tmp_path):
    """陰性: 既存 run 配下の変更は宣言しても許可されない。新規の経路は許可される。"""
    result = _check(
        monkeypatch, tmp_path,
        allow=["experiments/"],
        diff=["experiments/old_run/metrics.json", "experiments/new_dir/report.md"],
        existing=["experiments/old_run/metrics.json"],
    )
    assert [v["path"] for v in result["violations"]] == ["experiments/old_run/metrics.json"]
    assert [p["path"] for p in result["permitted"]] == ["experiments/new_dir/report.md"]


# --------------------------------------------------------------------------- #
# F2 preflight の未知名
# --------------------------------------------------------------------------- #
def test_f2_unknown_preflight_name_fails():
    """陽性: 実装されていない名前は FAIL。**黙って PASS にしない。**"""
    spec = _spec()
    spec["plan"]["env"]["preflight"] = ["venv_active", "zzz_not_a_check"]
    check = preflight_task.check_preflight_names(spec)
    assert check.status == "FAIL"
    assert "zzz_not_a_check" in check.detail


@pytest.mark.parametrize("names", [
    ["venv_active"],
    ["venv_active", "gpu_free"],
    ["venv_active", "cuda_ext_loaded", "deterministic_flags", "gpu_free"],
])
def test_f2_known_preflight_names_pass(names):
    """陰性: 既存契約が使っている名前は引き続き PASS する。"""
    spec = _spec()
    spec["plan"]["env"]["preflight"] = names
    assert preflight_task.check_preflight_names(spec).status == "PASS"


def test_f2_schema_enum_matches_implementation():
    """schema の enum と検査器の既知名が同じ集合であること。**片方だけ増やさせない。**"""
    enum = SCHEMA["properties"]["plan"]["properties"]["env"]["properties"]["preflight"]["items"]["enum"]
    assert set(enum) == set(preflight_task.KNOWN_PREFLIGHT_NAMES)


def test_f2_every_contract_uses_known_names():
    """既存の全契約が既知の名前しか使っていないこと（回帰の分母）。"""
    offenders = {}
    for path in sorted((REPO_ROOT / "tasks").glob("T-*/spec.yaml")):
        spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        unknown = preflight_task.unknown_preflight_names(spec)
        if unknown:
            offenders[path.parent.name] = unknown
    assert offenders == {}


# --------------------------------------------------------------------------- #
# F3 置換前提の欄
# --------------------------------------------------------------------------- #
def _validate(denominator: dict) -> str | None:
    spec = _spec()
    spec.setdefault("inputs", {})["denominator"] = denominator
    try:
        jsonschema.validate(spec, SCHEMA)
    except jsonschema.ValidationError as exc:
        return exc.message
    return None


def test_f3_declared_placeholder_installs():
    """正例: 宣言つきの置換前提は取り込みで落ちない。"""
    assert _validate({
        "ref": "unresolved:runindex/experiments.csv から分母を引く",
        "resolve_by_executor": True,
        "metric": "mAP",
    }) is None


def test_f3_resolved_ref_installs():
    """陰性: 解決済みの参照は従来どおり通る。"""
    assert _validate({"ref": "exp:baselines/s0/relationdetr@mAP", "metric": "mAP"}) is None


@pytest.mark.parametrize("ref,declared", [
    ("TBD", False),
    ("unresolved:あとで", False),
    ("TBD", True),
])
def test_f3_undeclared_placeholder_still_fails(ref, declared):
    """陽性: 宣言の無い置換前提と、宣言があっても形式が不正なものは落ちる。"""
    denominator = {"ref": ref, "metric": "mAP"}
    if declared:
        denominator["resolve_by_executor"] = True
    assert _validate(denominator) is not None


def test_f3_preflight_stops_before_resolution(tmp_path, monkeypatch):
    """陽性: 解決が済んでいなければ実行直前で止まる。済んでいれば止まらない。"""
    monkeypatch.setattr(preflight_task, "TASKS_DIR", tmp_path)
    task_id = "T-2026-01-01-probe"
    (tmp_path / task_id).mkdir(parents=True)
    spec = _spec()
    spec["inputs"]["denominator"] = {
        "ref": "unresolved:runindex から分母を引く", "resolve_by_executor": True, "metric": "mAP",
    }
    assert preflight_task.check_refs_resolved(task_id, spec).status == "FAIL"

    (tmp_path / task_id / "resolved.yaml").write_text(yaml.safe_dump(
        {"inputs.denominator.ref": {"resolved_to": "unresolved:まだ", "how": "未了"}},
    ), encoding="utf-8")
    assert preflight_task.check_refs_resolved(task_id, spec).status == "FAIL"

    (tmp_path / task_id / "resolved.yaml").write_text(yaml.safe_dump(
        {"inputs.denominator.ref": {
            "resolved_to": "exp:baselines/s0/relationdetr@mAP",
            "how": "runindex/experiments.csv の experiment_id と照合",
        }},
    ), encoding="utf-8")
    assert preflight_task.check_refs_resolved(task_id, spec).status == "PASS"


def test_f3_no_placeholder_is_skipped(tmp_path, monkeypatch):
    """陰性: 置換前提の参照が無い契約は対象外（SKIP）。"""
    monkeypatch.setattr(preflight_task, "TASKS_DIR", tmp_path)
    assert preflight_task.check_refs_resolved("T-2026-01-01-probe", _spec()).status == "SKIP"


# --------------------------------------------------------------------------- #
# F4 収穫の検証
# --------------------------------------------------------------------------- #
VERDICT_ROWS = [
    {"experiment_id": "g/a/x@val", "metric": "mAP", "n_seeds": "3",
     "delta": "0.010", "same_sign": "True", "verdict_pstd": "undecidable",
     "verdict_sstd": "undecidable", "agree": "True", "reason": ""},
    {"experiment_id": "g/b/y@val", "metric": "mAP", "n_seeds": "3",
     "delta": "0.020", "same_sign": "True", "verdict_pstd": "significant",
     "verdict_sstd": "significant", "agree": "True", "reason": ""},
]
INDEX_ROWS = [
    {"ledger_key": "k1", "metric.mAP": "0.10"},
    {"ledger_key": "k2", "metric.mAP": "0.20"},
]
VERDICTS = "runindex/verdicts.csv"
INDEX = "runindex/index.csv"


def test_f4_identical_pair_passes():
    """陰性: 同一入力の対では追加零・変更零で通る。"""
    for table, rows in ((VERDICTS, VERDICT_ROWS), (INDEX, INDEX_ROWS)):
        result = verify_harvest.compare(table, verify_harvest.TABLES[table], rows, copy.deepcopy(rows))
        assert result["pass"] and not result["added"] and not result["removed"]


def test_f4_aggregate_judgement_column_change_fails():
    """陽性: 集約表の判定列を一箇所変えると失敗する。"""
    after = copy.deepcopy(VERDICT_ROWS)
    after[0]["verdict_pstd"] = "significant"
    result = verify_harvest.compare(VERDICTS, verify_harvest.TABLES[VERDICTS], VERDICT_ROWS, after)
    assert result["pass"] is False
    assert result["changed_judgement"][0]["columns"]["verdict_pstd"]["after"] == "significant"


def test_f4_aggregate_value_column_change_passes():
    """陰性: 集計値の列だけが変わるのは正常な収穫。**ここで落とすと必ず失敗する。**"""
    after = copy.deepcopy(VERDICT_ROWS)
    after[0]["delta"] = "0.999"
    result = verify_harvest.compare(VERDICTS, verify_harvest.TABLES[VERDICTS], VERDICT_ROWS, after)
    assert result["pass"] is True
    assert result["changed_rows"] == 1 and result["changed_judgement"] == []


def test_f4_run_level_addition_only():
    """陰性: run 単位は追加のみなら通る。陽性: 既存行が変わると落ちる。"""
    added = copy.deepcopy(INDEX_ROWS) + [{"ledger_key": "k3", "metric.mAP": "0.30"}]
    assert verify_harvest.compare(INDEX, verify_harvest.TABLES[INDEX], INDEX_ROWS, added)["pass"]

    changed = copy.deepcopy(INDEX_ROWS)
    changed[0]["metric.mAP"] = "0.99"
    result = verify_harvest.compare(INDEX, verify_harvest.TABLES[INDEX], INDEX_ROWS, changed)
    assert result["pass"] is False and result["changed_rows"] == 1


def test_f4_removal_always_fails():
    """陽性: 削除はどちらの表でも失敗する。"""
    for table, rows in ((VERDICTS, VERDICT_ROWS), (INDEX, INDEX_ROWS)):
        result = verify_harvest.compare(table, verify_harvest.TABLES[table], rows, rows[:1])
        assert result["pass"] is False and len(result["removed"]) == 1


def test_f4_judgement_columns_exist_in_real_tables():
    """規約の判定列が実在の表に本当にあること。**名前だけの規約にしない。**"""
    import csv

    for table in (VERDICTS, "runindex/experiments.csv"):
        with open(REPO_ROOT / table, newline="", encoding="utf-8") as handle:
            columns = next(csv.reader(handle))
        judged = [c for c in columns if verify_harvest.is_judgement_column(c)]
        assert judged, f"{table} に判定列が無い"
        assert any("verdict" in c for c in judged)
        assert any("n_seeds" in c for c in judged)


# --------------------------------------------------------------------------- #
# F5 秘匿検出の偽陽性
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("text", [
    "WANDB_API_KEY=abcd1234…（先頭 8 桁・以降は伏せる）",
    "NOTION_API_KEY: ntn_synthetic...(伏せ字)",
    "report_sha256: 2f648079f286a825…（先頭 16 桁のみ）",
    "ckpt の sha256 は notes.md に記録した",
])
def test_f5_redacted_summaries_are_not_flagged(text):
    """陰性: 伏せ字の要約値は検出しない。"""
    assert report_task.scan_secrets(text, env={}) == []


@pytest.mark.parametrize("text", [
    "ntn_" + "S" * 30,
    "secret_" + "S" * 25,
    "MY_API_KEY = 'zzzzzzzzzzzzzzzzzzzz'",
    "NOTION_API_KEY=" + "x" * 40,
    "old=abcd…  MY_TOKEN='yyyyyyyyyyyyyyyyyy'",
])
def test_f5_real_shapes_are_still_flagged(text):
    """陽性: 鍵の形と名前つきの値は引き続き検出する。合成値のみを使う。"""
    assert report_task.scan_secrets(text, env={}) != []


def test_f5_output_carries_no_fragment_of_the_value():
    """検査の出力に値の断片が出ないこと。"""
    synthetic = "ntn_" + "S" * 30
    findings = report_task.scan_secrets(synthetic, env={})
    assert findings
    assert all(synthetic[:12] not in finding for finding in findings)

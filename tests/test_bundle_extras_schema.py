"""契約の追加ファイルの宣言（inputs.bundle_extras）を spec の schema が受け付けることの試験。

宣言は tools/fetch_task.py の extras_from_spec が読む。schema が受け付けないと、取り込みの最後の
make task-validate が L1-1 で落ち、取り込みが巻き戻る（T-2026-10-18-evidence-verify-place の環境の罠の一）。
**schema と取り込みの制約が食い違わないことをここで縛る。**
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import fetch_task  # noqa: E402
from validate_task import validate_l1, validate_spec_md  # noqa: E402

TASK_ID = "T-2026-08-03-example-task"
EXTRA_BODY = "起票者の一覧\tarxiv\t1602.03012\n"
EXTRA_SHA = hashlib.sha256(EXTRA_BODY.encode()).hexdigest()
SCHEMA = json.loads((REPO_ROOT / "tasks" / "_schema" / "spec.schema.json").read_text(encoding="utf-8"))
EXTRAS_SCHEMA = SCHEMA["properties"]["inputs"]["properties"]["bundle_extras"]


def _spec(extras=None) -> dict:
    spec = {
        "spec_version": 1,
        "meta": {
            "task_id": TASK_ID,
            "kind": "impl",
            "title": "example",
            "origin": "claude-app",
            "created_at": "2026-08-03T00:00:00Z",
            "created_from": {"runindex_commit": "762a5c8", "counts": {"index": 749, "experiments": 206, "verdicts": 1038}},
        },
        "intent": {"question": "q", "decision_at_stake": "d"},
        "inputs": {
            "data": {"dataset": "not-referenced", "split_files": ["data/splits/ego_val.txt"]},
            "code": {"entrypoints": ["tools/fetch_task.py"]},
        },
        "contract": {
            "inject_verbatim": ["conventions#prohibitions"],
            "conventions_rev": "762a5c8",
            "prohibitions": ["no_estimated_values"],
            "verbatim_forbidden": True,
        },
        "plan": {"phases": [{"id": "A", "name": "impl", "gpu": False}], "env": {"venv": ".venv", "preflight": ["venv_active"]}},
        "outputs": {"must_have": ["RESULT.md"], "destination": "tools/", "acceptance": ["make task-validate が exit 0"]},
        "governance": {"deviations_required": True, "integrity": ["no_fabrication"]},
    }
    if extras is not None:
        spec["inputs"]["bundle_extras"] = extras
    return spec


GOOD = {"path": "expected-ids.txt", "sha256": EXTRA_SHA, "bytes": len(EXTRA_BODY.encode())}


def _l1(extras):
    return [str(f) for f in validate_l1(_spec(extras), dir_name=TASK_ID)]


def test_spec_without_declaration_still_passes():
    assert _l1(None) == []


def test_well_formed_declaration_passes():
    assert _l1([GOOD, {**GOOD, "path": "inputs/extra.md"}]) == []


@pytest.mark.parametrize(
    "broken",
    [
        {**GOOD, "sha256": EXTRA_SHA[:-1]},
        {**GOOD, "sha256": EXTRA_SHA.upper()},
        {**GOOD, "sha256": EXTRA_SHA + "\n"},
        {**GOOD, "path": "../escape.txt"},
        {**GOOD, "path": "/abs/path.txt"},
        {**GOOD, "path": "dir//x.txt"},
        {**GOOD, "path": "spec.yaml"},
        {**GOOD, "bytes": -1},
        {"sha256": EXTRA_SHA, "bytes": 1},
    ],
)
def test_broken_declaration_fails_l1(broken):
    found = _l1([broken])
    assert found and all("L1-1" in f for f in found), found


# --- 取り込みの側と同じ制約であること --------------------------------------------------

def _schema_path_ok(path: str) -> bool:
    return not validate_l1(_spec([{**GOOD, "path": path}]), dir_name=TASK_ID)


@pytest.mark.parametrize(
    "path",
    ["a.txt", "dir/a.txt", "a-b_c.d/e", "x", ".hidden", "a/../b", "a/./b", "a b.txt", "a/", "", "日本語.md", "a.txt\n"],
)
def test_path_rule_agrees_with_fetch_task(path):
    assert _schema_path_ok(path) == bool(fetch_task._EXTRA_PATH_RE.fullmatch(path))


def test_reserved_names_agree_with_fetch_task():
    assert set(EXTRAS_SCHEMA["items"]["properties"]["path"]["not"]["enum"]) == set(fetch_task.ALLOWED_FILES)


def test_declaration_key_agrees_with_fetch_task():
    assert fetch_task.EXTRA_DECL_KEY == ("inputs", "bundle_extras")


# --- 取り込みを通した端から端まで -------------------------------------------------------

SPEC_MD = "# 例\n\n本文\n"


def _bundle(extra_body: str) -> str:
    spec_yaml = yaml.safe_dump(_spec([GOOD]), allow_unicode=True, sort_keys=False)
    return fetch_task.pack_bundle({"spec.yaml": spec_yaml, "SPEC.md": SPEC_MD, "expected-ids.txt": extra_body})


def _validate_with_schema(tasks_dir: Path):
    """make task-validate の代わりに、設置した契約を同じ L1 の検査にかける（repo の契約群には触れない）。"""

    def _run(task_id: str) -> tuple[int, str]:
        task_dir = tasks_dir / task_id
        spec = yaml.safe_load((task_dir / "spec.yaml").read_text(encoding="utf-8"))
        findings = validate_l1(spec, dir_name=task_id) + validate_spec_md(spec, task_dir)
        return (1 if findings else 0), "\n".join(str(f) for f in findings) or f"OK   {task_id}"

    return _run


def test_declared_bundle_is_installed_and_validates(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(fetch_task, "TASKS_DIR", tasks_dir)
    monkeypatch.setattr(fetch_task, "_validate", _validate_with_schema(tasks_dir))
    src = tmp_path / "bundle.txt"
    src.write_text(_bundle(EXTRA_BODY), encoding="utf-8")
    assert fetch_task.fetch(str(src)) == 0
    installed = tasks_dir / TASK_ID / "expected-ids.txt"
    assert hashlib.sha256(installed.read_bytes()).hexdigest() == EXTRA_SHA


def test_tampered_bundle_is_rejected_and_leaves_nothing(tmp_path, monkeypatch, capsys):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(fetch_task, "TASKS_DIR", tasks_dir)
    monkeypatch.setattr(fetch_task, "_validate", _validate_with_schema(tasks_dir))
    src = tmp_path / "bundle.txt"
    src.write_text(_bundle(EXTRA_BODY.replace("1602", "1603")), encoding="utf-8")
    assert fetch_task.fetch(str(src)) == 1
    assert "要約値が宣言と一致しません" in capsys.readouterr().err
    assert not (tasks_dir / TASK_ID).exists()

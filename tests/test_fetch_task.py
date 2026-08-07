import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from fetch_task import (  # noqa: E402
    BundleError,
    ensure_absent,
    pack_bundle,
    parse_bundle,
    task_id_from_spec,
)

DELIM = "d" * 48

SPEC_YAML = """spec_version: 1

meta:
  task_id: "T-2026-08-09-example-task"
  kind: impl
"""

SPEC_MD = """# 例

本文にはヒアドキュメントが入ることがある。

```bash
python - <<'PY'
print("hello")
PY
```
"""


def _bundle(spec_yaml=SPEC_YAML, spec_md=SPEC_MD, delim=DELIM, end=True):
    parts = [f"#!TASK-BUNDLE v1 delim={delim}"]
    if spec_yaml is not None:
        parts += [f"{delim} FILE spec.yaml", spec_yaml.rstrip("\n")]
    if spec_md is not None:
        parts += [f"{delim} FILE SPEC.md", spec_md.rstrip("\n")]
    if end:
        parts.append(f"{delim} END")
    return "\n".join(parts) + "\n"


def test_extracts_task_id_from_valid_bundle():
    files = parse_bundle(_bundle())
    assert set(files) == {"spec.yaml", "SPEC.md"}
    assert task_id_from_spec(files["spec.yaml"]) == "T-2026-08-09-example-task"


def test_heredoc_in_body_survives_round_trip():
    """SPEC 本文のヒアドキュメントが壊れないこと。"""
    files = parse_bundle(_bundle())
    assert "<<'PY'" in files["SPEC.md"]
    assert files["SPEC.md"].rstrip("\n") == SPEC_MD.rstrip("\n")


def test_rejects_bundle_without_spec_yaml():
    with pytest.raises(BundleError, match="必須のファイル"):
        parse_bundle(_bundle(spec_yaml=None))


def test_rejects_spec_without_task_id():
    files = parse_bundle(_bundle(spec_yaml="spec_version: 1\nmeta:\n  kind: impl\n"))
    with pytest.raises(BundleError, match="meta.task_id"):
        task_id_from_spec(files["spec.yaml"])


def test_rejects_task_id_that_is_unsafe_as_directory_name():
    files = parse_bundle(
        _bundle(spec_yaml='spec_version: 1\nmeta:\n  task_id: "../escape"\n')
    )
    with pytest.raises(BundleError, match="task_id の形式"):
        task_id_from_spec(files["spec.yaml"])


def test_rejects_existing_task(tmp_path):
    (tmp_path / "T-2026-08-09-example-task").mkdir()
    with pytest.raises(BundleError, match="既にあります"):
        ensure_absent("T-2026-08-09-example-task", tmp_path)


def test_accepts_absent_task(tmp_path):
    ensure_absent("T-2026-08-09-example-task", tmp_path)


def test_rejects_delimiter_colliding_with_body():
    """区切りが本文に現れる場合は、構造違反として失敗する。"""
    colliding = _bundle(spec_md=f"本文の途中に {DELIM} FILE evil.md が現れる")
    with pytest.raises(BundleError):
        parse_bundle(colliding)


def test_pack_refuses_when_delimiter_appears_in_body():
    with pytest.raises(BundleError, match="衝突"):
        pack_bundle({"spec.yaml": SPEC_YAML, "SPEC.md": f"x {DELIM} y"}, delim=DELIM)


def test_rejects_short_delimiter():
    with pytest.raises(BundleError, match="区切りが短すぎます"):
        parse_bundle(_bundle(delim="short"))


def test_rejects_truncated_bundle_without_end():
    with pytest.raises(BundleError, match="END 標識がありません"):
        parse_bundle(_bundle(end=False))


def test_rejects_unknown_file_name():
    text = (
        f"#!TASK-BUNDLE v1 delim={DELIM}\n"
        f"{DELIM} FILE spec.yaml\n{SPEC_YAML.rstrip()}\n"
        f"{DELIM} FILE SPEC.md\n{SPEC_MD.rstrip()}\n"
        f"{DELIM} FILE ../../etc/passwd\nx\n"
        f"{DELIM} END\n"
    )
    with pytest.raises(BundleError, match="受け取れないファイル"):
        parse_bundle(text)


def test_pack_and_parse_round_trip():
    text = pack_bundle({"spec.yaml": SPEC_YAML, "SPEC.md": SPEC_MD})
    files = parse_bundle(text)
    assert files["spec.yaml"].rstrip("\n") == SPEC_YAML.rstrip("\n")
    assert files["SPEC.md"].rstrip("\n") == SPEC_MD.rstrip("\n")


def test_rolls_back_when_validation_command_raises(tmp_path, monkeypatch):
    """検証コマンド自体が例外で落ちた場合も、設置を巻き戻して痕跡を残さない。"""
    import fetch_task

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(fetch_task, "TASKS_DIR", tasks_dir)

    def _boom(_task_id):
        raise OSError("make が見つからない")

    monkeypatch.setattr(fetch_task, "_validate", _boom)

    bundle = tmp_path / "bundle.txt"
    bundle.write_text(pack_bundle({"spec.yaml": SPEC_YAML, "SPEC.md": SPEC_MD}), encoding="utf-8")

    assert fetch_task.fetch(str(bundle)) == 1
    assert list(tasks_dir.iterdir()) == []


def test_rolls_back_when_validation_fails(tmp_path, monkeypatch):
    """検証が非ゼロで返った場合に設置を巻き戻す。"""
    import fetch_task

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(fetch_task, "TASKS_DIR", tasks_dir)
    monkeypatch.setattr(fetch_task, "_validate", lambda _t: (1, "FAIL"))

    bundle = tmp_path / "bundle.txt"
    bundle.write_text(pack_bundle({"spec.yaml": SPEC_YAML, "SPEC.md": SPEC_MD}), encoding="utf-8")

    assert fetch_task.fetch(str(bundle)) == 1
    assert list(tasks_dir.iterdir()) == []


def test_keeps_task_when_validation_passes(tmp_path, monkeypatch):
    """検証が通った場合のみ tasks/ に残る。"""
    import fetch_task

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setattr(fetch_task, "TASKS_DIR", tasks_dir)
    monkeypatch.setattr(fetch_task, "_validate", lambda _t: (0, "OK"))

    bundle = tmp_path / "bundle.txt"
    bundle.write_text(pack_bundle({"spec.yaml": SPEC_YAML, "SPEC.md": SPEC_MD}), encoding="utf-8")

    assert fetch_task.fetch(str(bundle)) == 0
    installed = tasks_dir / "T-2026-08-09-example-task"
    assert sorted(p.name for p in installed.iterdir()) == ["SPEC.md", "spec.yaml"]

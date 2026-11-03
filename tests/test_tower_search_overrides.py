"""Tower-search tools keep the dlsta defaults when the override variables are unset.

T-2026-11-02-hostdiff-andrew added environment overrides (contract id, phase publish place,
detector W&B seed, an optional observer). Unset, every value must stay the dlsta search's.
"""
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DLSTA = "T-2026-10-22-tower-reselect-search-dlsta"
OVERRIDES = ("TOWER_SEARCH_TASK", "TOWER_SEARCH_OBSERVER", "TOWER_SEARCH_PHASE_PUBLISH", "TOWER_SEARCH_SEED")


def load(path, name, monkeypatch, env=None):
    for key in OVERRIDES:
        monkeypatch.delenv(key, raising=False)
    for key, value in (env or {}).items():
        monkeypatch.setenv(key, value)
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_common_defaults(module):
    assert module.TASK == DLSTA
    assert module.SCRATCH == Path.home() / "m2-scratch" / DLSTA
    assert module.ANALYSIS == ROOT / "experiments/analysis/tower_reselect_search_dlsta"
    assert module.load_observer() is None


def test_common_defaults_unchanged(monkeypatch):
    check_common_defaults(load(ROOT / "scripts/tower_search_common.py", "tsc_default", monkeypatch))


def test_common_override_applies(monkeypatch, tmp_path):
    hook = tmp_path / "hook.py"
    hook.write_text("VALUE = 7\n")
    module = load(ROOT / "scripts/tower_search_common.py", "tsc_override", monkeypatch,
                  {"TOWER_SEARCH_TASK": "T-x", "TOWER_SEARCH_OBSERVER": str(hook)})
    assert module.TASK == "T-x"
    assert module.SCRATCH == Path.home() / "m2-scratch" / "T-x"
    assert module.load_observer().VALUE == 7


def test_breaking_control_changed_default_fails(monkeypatch, tmp_path):
    """A copy whose default contract id is changed must fail the default check."""
    text = (ROOT / "scripts/tower_search_common.py").read_text()
    broken = tmp_path / "tower_search_common.py"
    broken.write_text(text.replace(f'"{DLSTA}"', '"T-changed"', 1))
    module = load(broken, "tsc_broken", monkeypatch)
    with pytest.raises(AssertionError):
        check_common_defaults(module)


def test_phase_publish_default_unchanged(monkeypatch):
    pytest.importorskip("hydra")
    module = load(ROOT / "scripts/run_ptower_search.py", "rps_default", monkeypatch)
    assert module.PUBLISH == "experiments/phase1/stage1_ptower_search"
    assert module.TASK == DLSTA
    module = load(ROOT / "scripts/run_ptower_search.py", "rps_override", monkeypatch,
                  {"TOWER_SEARCH_PHASE_PUBLISH": "experiments/phase1/x"})
    assert module.PUBLISH == "experiments/phase1/x"


def test_detector_seed_default_is_42():
    """The detector script imports Relation-DETR, so read the default from its source."""
    text = (ROOT / "scripts/train_relation_detr_search.py").read_text()
    assert re.search(r'os\.environ\.get\("TOWER_SEARCH_SEED", "42"\)', text)
    assert 'observer = load_observer()' in text


def test_observer_unset_runs_nothing_in_a_fresh_process():
    env = {k: v for k, v in os.environ.items() if k not in OVERRIDES}
    env["PYTHONPATH"] = str(ROOT / "scripts")
    out = subprocess.run([sys.executable, "-c",
                          "import tower_search_common as t; print(t.TASK, t.load_observer())"],
                         capture_output=True, text=True, env=env, check=True).stdout.split()
    assert out == [DLSTA, "None"]

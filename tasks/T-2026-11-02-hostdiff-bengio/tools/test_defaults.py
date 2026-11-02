"""道具の既定の挙動が変わっていないことの試験（T-2026-11-02-hostdiff-bengio、Task A-7、完了判定 g）。

環境変数を置かないとき、dlsta の探索の契約名・scratch・公開先・一歩ごとの記録の無効が変更前と同じであること、
置いたときだけ上書きされることを、子プロセスで確かめる。

    TOWER_TOOLS_DIR=<scripts の置き場> .venv/bin/python -m pytest -q -p no:cacheprovider <この試験>

``TOWER_TOOLS_DIR`` を変えた写しの置き場に向けると、陽性対照（写しの既定を一つ変えると落ちる）に使える。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = Path(os.environ.get("TOWER_TOOLS_DIR", ROOT / "scripts"))
DLSTA = "T-2026-10-22-tower-reselect-search-dlsta"
OVERRIDES = ("TOWER_SEARCH_TASK", "TOWER_SEARCH_SCRATCH", "TOWER_SEARCH_PHASE_PUBLISH",
             "TOWER_SEARCH_STEP_LOG", "TOWER_SEARCH_LOSS_LOG")


def probe(code, **env):
    base = {k: v for k, v in os.environ.items() if k not in OVERRIDES}
    base.update(PYTHONPATH=f"{TOOLS}:{ROOT / 'src'}", PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES="", **env)
    out = subprocess.run([sys.executable, "-B", "-c", code], env=base, capture_output=True, text=True, check=True)
    return json.loads(out.stdout.strip().splitlines()[-1])


COMMON = "import json, tower_search_common as c; print(json.dumps([c.TASK, str(c.SCRATCH)]))"
PUBLISH = ("import json, sys; sys.argv=['x']; import run_ptower_search as r; "
           "print(json.dumps(str(r.publish_root())))")


def test_common_defaults_unchanged():
    task, scratch = probe(COMMON)
    assert task == DLSTA
    assert scratch == str(Path.home() / "m2-scratch" / DLSTA)


def test_common_overrides_only_with_env():
    task, scratch = probe(COMMON, TOWER_SEARCH_TASK="T-x", TOWER_SEARCH_SCRATCH="/tmp/x")
    assert (task, scratch) == ("T-x", "/tmp/x")


def test_publish_default_unchanged():
    assert probe(PUBLISH) == str(ROOT / "experiments/phase1/stage1_ptower_search")
    assert probe(PUBLISH, TOWER_SEARCH_PHASE_PUBLISH="experiments/phase1/y") == str(ROOT / "experiments/phase1/y")


def test_step_logs_are_gated():
    """一歩ごとの記録は環境変数があるときだけ入る（既定の経路では差し替えない）。"""
    phase = (TOOLS / "run_ptower_search.py").read_text()
    assert 'if os.environ.get("TOWER_SEARCH_STEP_LOG") and cfg.action == "finetune":' in phase
    assert "if step_handle is not None:" in phase
    detector = (TOOLS / "train_relation_detr_search.py").read_text()
    assert 'step_log = os.environ.get("TOWER_SEARCH_STEP_LOG")' in detector
    assert "        if step_log:\n" in detector
    assert "optimizer.step =" not in detector

"""dp_train.py の既定の経路が、契約 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle の拡張の後も従来のままであることを固定する。

拡張（--fixed-epochs / --task-id / --exp-prefix / --smoke / 腕 shuffle / identity --arm）は、渡さなければ何も変えない。
既定の run は前回の契約の識別子・名前の接頭辞・置き場のままで、既存の腕の信号の出所も変わらない。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

dp_train = pytest.importorskip("stage2pilot.dp_train")
C = dp_train.C


def parse(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["dp_train.py", *argv])
    captured = {}
    monkeypatch.setattr(dp_train, "cmd_train", lambda a: captured.setdefault("a", a))
    monkeypatch.setattr(dp_train, "cmd_identity", lambda a: captured.setdefault("a", a))
    dp_train.main()
    return captured["a"]


def test_new_train_options_default_to_previous_contract(monkeypatch):
    a = parse(monkeypatch, ["train", "--type", "D1-L1", "--arm", "gt", "--seed", "42"])
    assert a.fixed_epochs is None and a.smoke is False and a.max_epochs is None
    assert a.task_id == C.TASK_ID == "T-2026-10-18-stage2-pilot-folda"
    assert a.exp_prefix == "stage2pilot_dp"
    assert C.STORE.parent / a.task_id == C.STORE                # 界面の重みの置き場は従来どおり


def test_identity_default_arms_are_unchanged(monkeypatch):
    a = parse(monkeypatch, ["identity", "--type", "D2", "--out", "/dev/null"])
    assert a.arm is None and a.task_id == C.TASK_ID


def test_existing_arm_sources_are_unchanged():
    f = dp_train.FINAL
    assert dp_train.sources("D1-L1", "pred_noCF", "val", "literal") == [(f / "D0_val.npz", False)]
    assert dp_train.sources("D1-L1", "gtpred_CF", "train", "literal") == [
        (f / "D-GT_train.npz", True), (dp_train.CF / "D0_train.npz", False)]
    assert dp_train.sources("D3-L2", "pred_noCF", "val", "uq") == [(f / "D0-INST-UQ_val.npz", False)]
    assert dp_train.sources("D2", "empty", "train", "literal") == []


def test_shuffle_arm_reads_the_fix_store():
    assert dp_train.sources("D1-L2", "shuffle", "val", "literal") == [(C.FIX_STORE / "signals/shuffle/D0-RT_val.npz", False)]
    assert dp_train.sources("D3-L1", "shuffle", "train", "uq") == [
        (C.FIX_STORE / "signals/shuffle/D0-INST-UQ_train.npz", False)]


def test_fixed_and_smoke_combinations_are_guarded(monkeypatch):
    with pytest.raises(SystemExit):
        parse(monkeypatch, ["train", "--type", "D2", "--arm", "gt", "--seed", "42", "--fixed-epochs", "4", "--max-epochs", "1"])
    with pytest.raises(SystemExit):
        parse(monkeypatch, ["train", "--type", "D2", "--arm", "gt", "--seed", "42", "--smoke"])

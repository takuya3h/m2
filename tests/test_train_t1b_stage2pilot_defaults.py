"""train_t1b.py の既定の経路が、契約 T-2026-10-18-stage2-pilot-folda の拡張の後も従来のままであることを固定する。

拡張（--det-ckpt / --signal-train / --signal-val / --fixed-table / --eval-only / --patience /
--best-excludes-init / --ckpt-dir / --save-trainable-only / --trainable w2）は、渡さなければ何も変えない。
既定で解決される検出器の checkpoint と工程の信号の経路は、拡張の前の値と同じでなければならない。

T1B_UNDER_TEST に別の写しの経路を渡すと、その写しを検査する（既定を変えた写しで落ちることの確認用）。
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
TARGET = Path(os.environ.get("T1B_UNDER_TEST", ROOT / "scripts/train_t1b.py"))


@pytest.fixture
def t1b(monkeypatch):
    monkeypatch.setattr(os, "chdir", lambda path: None)      # import 時の chdir を無効にする
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    monkeypatch.setattr(sys, "argv", ["train_t1b.py"])
    spec = importlib.util.spec_from_file_location("train_t1b_under_test", TARGET)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_new_options_default_to_off(t1b):
    a = t1b.parse_args()
    assert a.det_ckpt is None and a.signal_train is None and a.signal_val is None
    assert a.fixed_table is None and a.ckpt_dir is None and a.patience is None
    assert not a.eval_only and not a.best_excludes_init and not a.save_trainable_only
    assert a.trainable == "all" and a.phase_source == "real" and a.epochs == 6 and a.inject == "film"
    assert not a.fixed_epochs                                  # 契約 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle で足した


def test_default_detector_checkpoint_is_unchanged(t1b):
    expected = ROOT / "third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth"
    assert t1b.resolve_detector_ckpt(42, None) == expected
    assert t1b.resolve_detector_ckpt(42, t1b.parse_args().det_ckpt) == expected
    assert t1b.detector_ckpt(123) == ROOT / "third_party/Relation-DETR/checkpoints/incoming/seed123/best_ap.pth"
    assert t1b.resolve_detector_ckpt(42, "/x/best.pth") == Path("/x/best.pth")


def test_default_signal_route_is_unchanged(t1b, monkeypatch):
    assert t1b.PHASECTX_DIR == ROOT / "data/processed/phase_context/relation_detr_seed42"
    assert t1b.MODEL_CFG == "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b.py"
    calls = []

    def fake(split):
        calls.append(split)
        return {"01_1_0001": np.zeros(9, np.float32)}

    monkeypatch.setattr(t1b, "load_phase_ctx", fake)
    tr, va, dim = t1b.resolve_ctx_sources(t1b.parse_args())
    assert calls == ["train", "val"] and dim == t1b.NUM_PHASES == 9


def test_signal_files_route_and_pairing(t1b, tmp_path, monkeypatch):
    for part in ("train", "val"):
        np.savez(tmp_path / f"{part}.npz", frame_ids=np.array(["01_1_0001"]), x=np.ones((1, 18), np.float32))
    monkeypatch.setattr(sys, "argv", ["train_t1b.py", "--signal-train", str(tmp_path / "train.npz"),
                                      "--signal-val", str(tmp_path / "val.npz")])
    tr, va, dim = t1b.resolve_ctx_sources(t1b.parse_args())
    assert dim == 18 and tr["01_1_0001"].shape == (18,)
    monkeypatch.setattr(sys, "argv", ["train_t1b.py", "--signal-train", str(tmp_path / "train.npz")])
    with pytest.raises(SystemExit):
        t1b.resolve_ctx_sources(t1b.parse_args())


def test_default_zero_context_is_nine_dimensional(t1b):
    class Coco:
        imgs = {7: {"file_name": "train/01/01_1_0001.jpg"}}

    m, miss = t1b.build_imgid_to_ctx(Coco(), {})
    assert miss == 1 and m[7].shape == (9,)
    z = t1b.ctx_for_targets([{"image_id": 7}], m, "cpu", zero_ctx=True)
    assert tuple(z.shape) == (1, 9)

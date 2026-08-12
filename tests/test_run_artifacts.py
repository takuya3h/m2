"""``scripts/run_artifacts.py`` の単体テスト（成果物レイアウトと predictions 保存）。

検出側 run の成果物が ``/tmp`` に消えて eval-only の追認が不能になる事故への構造的な
手当てを、コードで固定するためのテスト。特に

- predictions が **round-trip して同一内容**であること（保存形式が解析を壊さない）
- top-k 打ち切りが eval recipe 上限（300）と一致し、通常は恒等変換であること
- score 閾値による足切りを一切しないこと（AP が再現不能になるため）
- inj / ctrl の init 予測が一致すれば恒等性検証が PASS すること

を落とさないよう固定する。``scripts/run_artifacts.py`` は標準ライブラリのみに依存する
（``.venv-relation-detr`` から import されるため）ので、本テストも重い依存を持たない。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "run_artifacts", Path(__file__).resolve().parents[1] / "scripts" / "run_artifacts.py"
)
ra = importlib.util.module_from_spec(_SPEC)
sys.modules["run_artifacts"] = ra
_SPEC.loader.exec_module(ra)


def _results(n_images: int = 2, per_image: int = 3) -> list:
    """COCO detection results 形式のダミー予測。score は降順にならないよう混ぜる。"""
    out = []
    for img in range(n_images):
        for k in range(per_image):
            out.append({
                "image_id": img,
                "category_id": k % 3,
                "bbox": [float(k), float(k + 1), 10.0, 20.0],
                "score": (k * 7 % per_image) / per_image,
            })
    return out


# --------------------------------------------------------------------------- #
# レイアウト
# --------------------------------------------------------------------------- #
def test_ensure_layout_creates_required_subdirs(tmp_path):
    run = ra.ensure_layout(tmp_path / "myrun")
    for sub in ("checkpoints", "predictions", "logs"):
        assert (run / sub).is_dir(), f"{sub}/ が作られていない"


def test_resolve_run_dir_defaults_under_experiments_transfer():
    assert ra.resolve_run_dir("t1b_x_seed42") == ra.TRANSFER_ROOT / "t1b_x_seed42"


def test_resolve_run_dir_honours_explicit_work_dir(tmp_path):
    assert ra.resolve_run_dir("ignored", work_dir=tmp_path) == tmp_path


def test_resolve_run_dir_resolves_relative_work_dir_against_project_root():
    # os.chdir(RELDETR) 後に相対パスを渡されても誤配置しないこと。
    got = ra.resolve_run_dir("ignored", work_dir="experiments/transfer/foo")
    assert got == ra.PROJECT_ROOT / "experiments/transfer/foo"


def test_find_checkpoint_prefers_checkpoints_dir_then_legacy_flat(tmp_path):
    run = ra.ensure_layout(tmp_path / "run")
    assert ra.find_checkpoint(run) is None
    legacy = run / "best_t1b.pth"
    legacy.write_bytes(b"legacy")
    assert ra.find_checkpoint(run) == legacy, "旧 flat レイアウトを拾えること"
    new = run / "checkpoints" / "best_t1b.pth"
    new.write_bytes(b"new")
    assert ra.find_checkpoint(run) == new, "checkpoints/ を優先すること"


# --------------------------------------------------------------------------- #
# predictions
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("compress", [True, False])
def test_predictions_round_trip_is_lossless(tmp_path, compress):
    results = _results()
    path = ra.save_predictions(tmp_path / "run", results, split="val", tag="inj", epoch=-1,
                               compress=compress)
    assert path.exists()
    assert ra.load_predictions(path) == results


def test_predictions_filename_encodes_split_tag_and_epoch():
    assert ra.predictions_name("val", "inj", epoch=-1, compress=False) == "val_inj_ep-1.json"
    assert ra.predictions_name("test", "ctrl", best=True, compress=False) == "test_ctrl_best.json"
    assert ra.predictions_name("val", "inj", epoch=3) == "val_inj_ep3.json.gz"


def test_find_predictions_handles_both_compression_forms(tmp_path):
    run = tmp_path / "run"
    ra.save_predictions(run, _results(), split="test", tag="ctrl", best=True, compress=False)
    found = ra.find_predictions(run, "test", "ctrl", best=True)
    assert found is not None and found.suffix == ".json"


def test_truncate_topk_is_identity_when_under_limit():
    results = _results(n_images=2, per_image=5)
    # eval recipe 上限（300）以下なら並び順ごと不変＝AP 再現に影響しない。
    assert ra.truncate_topk(results, ra.EVAL_TOPK) == results


def test_truncate_topk_keeps_highest_scores_per_image():
    results = _results(n_images=2, per_image=5)
    kept = ra.truncate_topk(results, topk=2)
    assert len(kept) == 4
    for img in (0, 1):
        rows = [r for r in kept if r["image_id"] == img]
        assert len(rows) == 2
        allsc = sorted((r["score"] for r in results if r["image_id"] == img), reverse=True)
        assert sorted((r["score"] for r in rows), reverse=True) == allsc[:2]


def test_truncate_topk_never_drops_low_scores_below_limit():
    """score 閾値による足切りをしないこと（足切りすると AP が再現不能になる）。"""
    results = [
        {"image_id": 0, "category_id": 1, "bbox": [0, 0, 1, 1], "score": 0.0},
        {"image_id": 0, "category_id": 1, "bbox": [0, 0, 1, 1], "score": 1e-12},
    ]
    assert ra.truncate_topk(results, ra.EVAL_TOPK) == results


def test_predictions_sha256_is_independent_of_compression(tmp_path):
    results = _results()
    a = ra.save_predictions(tmp_path / "a", results, split="val", tag="inj", epoch=-1,
                            compress=True)
    b = ra.save_predictions(tmp_path / "b", results, split="val", tag="inj", epoch=-1,
                            compress=False)
    assert ra.predictions_sha256(a) == ra.predictions_sha256(b)


# --------------------------------------------------------------------------- #
# ログ・恒等性検証
# --------------------------------------------------------------------------- #
def test_eval_meta_is_split_scoped(tmp_path):
    run = tmp_path / "run"
    ra.save_eval_meta(run, {"split": "val", "image_ids": [1]})
    ra.save_eval_meta(run, {"split": "test", "image_ids": [2, 3]})
    assert ra.load_eval_meta(run, "val")["image_ids"] == [1]
    assert ra.load_eval_meta(run, "test")["image_ids"] == [2, 3]


def test_save_epoch_log_is_readable_json(tmp_path):
    payload = {"best_epoch": 2, "init": {"mAP": 0.5}}
    path = ra.save_epoch_log(tmp_path / "run", payload)
    assert path.name == ra.EPOCH_LOG_NAME
    assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_verify_init_identity_detects_match_and_mismatch(tmp_path):
    inj, ctrl = tmp_path / "inj", tmp_path / "ctrl"
    results = _results()
    ra.save_predictions(inj, results, split="val", tag="inj", epoch=-1)
    ra.save_predictions(ctrl, results, split="val", tag="ctrl", epoch=-1)
    assert ra.verify_init_identity(inj, ctrl)["identical"] is True

    other = tmp_path / "other"
    ra.save_predictions(other, _results(n_images=3), split="val", tag="ctrl", epoch=-1)
    assert ra.verify_init_identity(inj, other)["identical"] is False


def test_verify_init_identity_reports_missing_run(tmp_path):
    inj = tmp_path / "inj"
    ra.save_predictions(inj, _results(), split="val", tag="inj", epoch=-1)
    res = ra.verify_init_identity(inj, tmp_path / "nope")
    assert res["status"] == "missing" and "identical" not in res


# --------------------------------------------------------------------------- #
# ホスト名付きパス（マルチサーバ運用）
# --------------------------------------------------------------------------- #
def test_host_path_prefixes_server_name(tmp_path, monkeypatch):
    monkeypatch.setenv("SERVERNAME", "Efros")
    assert ra.host_path(tmp_path) == f"efros:{tmp_path.resolve()}"


def test_artifact_paths_lists_only_existing_subdirs(tmp_path, monkeypatch):
    monkeypatch.setenv("SERVERNAME", "efros")
    run = ra.ensure_layout(tmp_path / "run")
    paths = ra.artifact_paths(run)
    assert set(paths) == {"run_dir", "checkpoints", "predictions", "logs"}
    assert all(v.startswith("efros:/") for v in paths.values())


def test_write_evidence_creates_expected_files(tmp_path, monkeypatch):
    monkeypatch.setenv("SERVERNAME", "efros")
    run = tmp_path / "run"
    ra.write_evidence(run, config={"seed": 42}, notes="# note\n")
    for name in ("command.sh", "git_commit.txt", "server.txt", "config.yaml", "notes.md"):
        assert (run / name).exists(), f"{name} が無い"
    assert (run / "server.txt").read_text(encoding="utf-8").strip() == "efros"

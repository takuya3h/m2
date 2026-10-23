"""The search must reject missing frames, changed settings and unknown point tables."""
import importlib.util
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_tower_search as search  # noqa: E402
from tower_search_common import check_detector_groups, points_from_prereg  # noqa: E402


def test_preregistered_point_table_and_broken_table():
    text = (ROOT / "tasks/T-2026-10-22-tower-reselect-search-dlsta/prereg.md").read_text()
    rows = points_from_prereg(text)
    assert rows[0]["lr"] == 1e-4
    assert rows[13]["lr"] == 4.83e-4
    assert rows[3]["phase_weight_decay"] == 2.71
    with pytest.raises(ValueError, match="exactly"):
        points_from_prereg(text.replace("| 13 |", "| 99 |"))


def test_detector_groups_reject_changed_lr_and_decay():
    point = {"lr": 1e-4, "detector_weight_decay": 1e-4}
    groups = [{"lr": lr, "weight_decay": wd} for lr, wd in
              [(1e-4, 1e-4), (1e-5, 1e-4), (1e-5, 0),
               (1e-5, 1e-4), (1e-5, 0), (1e-4, 0)]]
    check_detector_groups(groups, point)
    groups[2]["weight_decay"] = 1e-4
    with pytest.raises(ValueError, match="optimizer groups"):
        check_detector_groups(groups, point)
    groups[2]["weight_decay"] = 0
    groups[0]["lr"] *= 2
    with pytest.raises(ValueError, match="optimizer groups"):
        check_detector_groups(groups, point)


def test_full_manifest_uses_fallback_without_changing_default(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("search_manifest", ROOT / "scripts/build_phase_manifest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "PROJ", tmp_path)
    monkeypatch.setattr(module, "PAPER_SPLIT_VIDEOS", {"train": ["01"], "val": [], "test": []})
    monkeypatch.setattr(module, "PHASE_CSV_DIR", tmp_path / "csv")
    monkeypatch.setattr(module, "EGO_ROOT", tmp_path / "raw")
    monkeypatch.setattr(module, "OUT_DIR", tmp_path / "default")
    (tmp_path / "csv").mkdir()
    (tmp_path / "csv/01_1.csv").write_text("Frame,Phase\n01_1_0001,cut\n01_1_0002,cut\n")
    raw = tmp_path / "raw/train/01"
    raw.mkdir(parents=True)
    (raw / "01_1_0001.jpg").write_bytes(b"image")
    fallback = tmp_path / "distributed/01_1"
    fallback.mkdir(parents=True)
    image = fallback / "01_1_0002.jpg"
    image.write_bytes(b"image")
    module.build()
    original = (tmp_path / "default/train.json").read_bytes()
    assert json.loads(original)["num_frames"] == 1
    module.build(fallback_root=tmp_path / "distributed", out_dir=tmp_path / "full")
    assert json.loads((tmp_path / "full/train.json").read_text())["num_frames"] == 2
    assert (tmp_path / "default/train.json").read_bytes() == original
    image.rename(fallback / "absent.jpg")
    module.build(fallback_root=tmp_path / "distributed", out_dir=tmp_path / "missing")
    assert json.loads((tmp_path / "missing/train.json").read_text())["num_frames"] == 1
    with pytest.raises(ValueError, match="separate"):
        module.build(fallback_root=tmp_path / "distributed")


def test_kill_gate_rejects_four_points_of_the_wrong_kinds(monkeypatch):
    monkeypatch.setattr(search, "records", [{"kind": "detector", "point": {"point": p}}
                                          for p in (0, 1, 2, 13)])
    with pytest.raises(RuntimeError, match="four successful"):
        search.gate_c()


def test_kill_gate_rejects_missing_initialization_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(search, "records", [{"kind": kind, "point": {"point": p}, "work": str(tmp_path)}
                                          for kind, p in [("detector", 0), ("detector", 13),
                                                          ("phase", 0), ("phase", 13)]])
    with pytest.raises(FileNotFoundError):
        search.gate_c()


def test_detector_distributes_each_evaluation_over_both_gpus(tmp_path, monkeypatch):
    monkeypatch.setattr(search, "SCRATCH", tmp_path / "scratch")
    monkeypatch.setattr(search, "ROOT", tmp_path)
    monkeypatch.setattr(search.subprocess, "check_output", lambda *a, **kw: "commit\n")
    monkeypatch.setattr(search, "record_run", lambda *a: None)
    assigned = {}

    def command(cmd, env, cwd, log, tag, timeout):
        work = log.parent
        log.write_text("loaded checkpoint\n")
        if "DTOWER_EVAL_SPLIT" in env:
            split = env["DTOWER_EVAL_SPLIT"]
            assigned[split] = env["CUDA_VISIBLE_DEVICES"]
            assert cmd[cmd.index("--num_processes") + 1] == "2"
            assert cmd[cmd.index("--mixed_precision") + 1] == "no"
            (work / f"eval_{split}.json").write_text(json.dumps({"AP": .5, "per_class_ap": {"Skewer": .5}}))
        elif tag.endswith("_records"):
            (work / "search_metrics.json").write_text('{"mAP": 0.5}')
            for name in ("posthoc_records.json", "convergence.json"):
                (work / name).write_text("{}")
            (work / "wandb").mkdir()
            (work / "wandb/wandb_run.json").write_text("{}")
        else:
            (work / "train.command.sh").write_text("training command")

    monkeypatch.setattr(search, "command", command)
    result = search.detector_point(2, "1,2", 0)
    assert assigned == {"val": "1,2", "train": "1,2"}
    assert result["metric"] == .5


def test_phase_parallel_stages_and_ten_heads_keep_separate_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(search, "SCRATCH", tmp_path)
    monkeypatch.setattr(search, "record_run", lambda *a: None)
    simultaneous = threading.Barrier(2)
    head_work = {}

    def command(cmd, env, cwd, log, tag, timeout):
        work = log.parent
        if tag == "phase2_finetune":
            run = work / "backbone"
            run.mkdir()
            (run / "metrics.json").write_text('{"phase_accuracy": 0.8}')
            (work / "finetune_last_run.json").write_text(json.dumps({"path": str(run)}))
        elif tag in ("phase2_train_eval", "phase2_extract"):
            simultaneous.wait(timeout=5)
            if tag == "phase2_extract":
                (work / "extract_last_run.json").write_text(json.dumps({"path": str(work)}))
        elif tag.startswith("phase2_head") and not tag.endswith("_records"):
            index = int(tag.removeprefix("phase2_head"))
            head_work[index] = (work, env["CUDA_VISIBLE_DEVICES"])
            simultaneous.wait(timeout=5)
            (work / "train_last_run.json").write_text(json.dumps({"path": str(work)}))
            (work / "metrics.json").write_text(json.dumps({"phase_jaccard": index / 10}))

    monkeypatch.setattr(search, "command", command)
    monkeypatch.setattr(search, "publish_phase", lambda work, action, *a:
                        Path(json.loads((work / f"{action}_last_run.json").read_text())["path"]))
    result = search.phase_point(2, "1,2", 0)
    assert len(result["heads"]) == 10
    assert len({work for work, gpu in head_work.values()}) == 10
    assert {gpu for work, gpu in head_work.values()} == {"1", "2"}
    assert [h["metrics"]["phase_jaccard"] for h in result["heads"]] == [i / 10 for i in range(10)]


def test_handoff_rejects_unfinished_training_even_with_a_checkpoint(tmp_path):
    log = tmp_path / "train.log"
    log.write_text("Training time: 01:00:00\n")
    (tmp_path / "best_ap.pth").write_bytes(b"checkpoint")
    convergence = tmp_path / "convergence.json"
    convergence.write_text('{"stopped_epoch": null, "observed_epochs": 10}')
    assert not search.completed_command(log)
    convergence.write_text('{"stopped_epoch": 10, "observed_epochs": 11}')
    assert search.completed_command(log)
    log.write_text("Training time: 01:00:00\nTraceback (most recent call last)\n")
    assert not search.completed_command(log)


def test_handoff_preserves_a_detached_running_command(tmp_path, monkeypatch):
    child_code = (
        "import pathlib,sys,time; time.sleep(.5); "
        "pathlib.Path(sys.argv[1], 'train.log').write_text('Training time: 00:00:01')"
    )
    parent_code = (
        "import subprocess,sys,time; "
        "p=subprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2]],start_new_session=True,"
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
        "print(p.pid,flush=True); time.sleep(30)"
    )
    log = tmp_path / "train.log"
    (tmp_path / "best_ap.pth").write_bytes(b"checkpoint")
    (tmp_path / "convergence.json").write_text('{"stopped_epoch": 10, "observed_epochs": 11}')
    parent = subprocess.Popen([sys.executable, "-c", parent_code, child_code, str(tmp_path)],
                              stdout=subprocess.PIPE, text=True, start_new_session=True)
    try:
        pid = int(parent.stdout.readline())
        identity = search.process_identity(pid)
        assert identity is not None
        parent.terminate()
        parent.wait(timeout=5)
        assert search.process_identity(pid) == identity
        monkeypatch.setattr(search, "handoff_commands", {str(log): {
            "pid": pid, "identity": identity, "time_jst": search.now(), "gpus": ""}})
        assert search.adopt_command(log, "control", 1)
        assert json.loads(log.with_suffix(".adopted.json").read_text())["exit_code"] is None
    finally:
        if parent.poll() is None:
            parent.terminate()
            parent.wait(timeout=5)


def test_completed_run_record_is_idempotent_and_conflicts_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(search, "ANALYSIS", tmp_path)
    run = tmp_path / "run"
    run.mkdir()
    metrics = run / "metrics.json"
    metrics.write_text('{"mAP": 0.5}')
    (run / "posthoc_records.json").write_text("{}")
    search.record_run("detector", 1, "train", run, "1,2")
    original = (tmp_path / "records.csv").read_bytes()
    search.record_run("detector", 1, "train", run, "1,2")
    assert (tmp_path / "records.csv").read_bytes() == original
    metrics.write_text('{"mAP": 0.6}')
    with pytest.raises(RuntimeError, match="Conflicting"):
        search.record_run("detector", 1, "train", run, "1,2")

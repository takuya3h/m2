"""Replace only the search supervisor, retaining its running command process groups."""
from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import run_tower_search as search  # noqa: E402


def main():
    state = json.loads((search.ANALYSIS / "live_status.json").read_text())
    pid = state["supervisor_pid"]
    identity = search.process_identity(pid)
    if identity is None or str(ROOT / "scripts/run_tower_search.py").encode() not in Path(f"/proc/{pid}/cmdline").read_bytes():
        raise RuntimeError("Previous search supervisor identity differs")
    source = search.SCRATCH / f"handoff_{time.time_ns()}.json"
    log_path = source.with_suffix(".log")
    ready = search.SCRATCH / "handoff_ready.json"
    if ready.exists():
        raise RuntimeError("A handoff has already been prepared; inspect it before another")
    replacement = None
    transferred = False
    os.kill(pid, signal.SIGSTOP)
    try:
        for _ in range(50):
            fields = Path(f"/proc/{pid}/stat").read_text().rpartition(") ")[2].split()
            if fields[0] == "T":
                break
            time.sleep(.02)
        else:
            raise RuntimeError("Previous supervisor did not stop")
        state = json.loads((search.ANALYSIS / "live_status.json").read_text())
        completed = json.loads((search.ANALYSIS / "point_records.json").read_text())
        known = {(r["kind"], r["point"]["point"]) for r in completed}
        commands, begins = {}, {}
        for pair, tag in state["active"].items():
            kind, number = tag.split("_point")
            if (kind, int(number)) in known:
                raise RuntimeError("Point completion crossed capture; resume and retry")
            work = search.SCRATCH / kind / f"point{number}"
            if kind == "phase" and (work / "extract_last_run.json").exists():
                raise RuntimeError("Phase postprocessing already started; wait for its boundary")
            start = search.SCRATCH / f"{tag}_input_before.command.json"
            begins[pair] = json.loads(start.read_text())["time_jst"]
            for meta in work.glob("*.command.json"):
                item = json.loads(meta.read_text())
                item["identity"] = search.process_identity(item["pid"])
                replay = meta.with_name(meta.name.removesuffix(".json") + ".sh").read_text()
                assignment = next(line for line in replay.splitlines() if line.startswith("export CUDA_VISIBLE_DEVICES="))
                item["gpus"] = shlex.split(assignment)[1].partition("=")[2]
                log = meta.with_name(meta.name.removesuffix(".command.json") + ".log")
                if item["identity"] is not None:
                    argv = Path(f"/proc/{item['pid']}/cmdline").read_bytes()
                    scripts = [arg for arg in item["cmd"] if arg.startswith((str(ROOT / "scripts"), "scripts/"))]
                    if not scripts or any(arg.encode() not in argv for arg in scripts):
                        raise RuntimeError("Running command identity differs")
                elif not search.completed_command(log):
                    raise RuntimeError(f"No successful completion evidence: {log}")
                commands[str(log)] = item
        handoff = {"task_id": search.TASK, "time_jst": search.now(), "old_pid": pid,
                   "old_identity": identity, "active": state["active"], "commands": commands,
                   "point_started_jst": begins,
                   "previous_supervisor": json.loads((search.SCRATCH / "supervisor.json").read_text())}
        search.write_json(source, handoff)
        with log_path.open("x") as output:
            replacement = subprocess.Popen(
                [search.BODY, "-u", str(ROOT / "scripts/run_tower_search.py"), "--resume-handoff", str(source)],
                cwd=ROOT, env={**os.environ, "CUDA_VISIBLE_DEVICES": "", "WANDB_MODE": "offline"},
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                start_new_session=True, close_fds=True)
        for _ in range(100):
            if ready.exists() and json.loads(ready.read_text())["pid"] == replacement.pid:
                transferred = True
                break
            if replacement.poll() is not None:
                raise RuntimeError(f"Replacement exited; inspect {log_path}")
            time.sleep(.05)
        if not transferred:
            raise RuntimeError("Replacement did not acknowledge ownership")
        # Pending SIGTERM is delivered before the stopped parent can schedule more jobs.
        os.kill(pid, signal.SIGTERM)
        os.kill(pid, signal.SIGCONT)
        print(json.dumps({"old_supervisor": pid, "new_supervisor": replacement.pid,
                          "handoff": str(source), "active": state["active"],
                          "running_commands_preserved": [r["pid"] for r in commands.values() if r["identity"] is not None]},
                         ensure_ascii=False), flush=True)
    finally:
        if not transferred:
            if replacement is not None and replacement.poll() is None:
                replacement.terminate()
                replacement.wait(timeout=10)
            if search.process_identity(pid) == identity:
                os.kill(pid, signal.SIGCONT)


if __name__ == "__main__":
    main()

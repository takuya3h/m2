"""A-8 / D-2: 全契約について completed_verdicts が空でないか（完了済みか）を出す。TASKS_DIR 直下の T-* が対象。"""
import sys
sys.path.insert(0, "tools")
import preflight_task
ids = sorted(p.name for p in preflight_task.TASKS_DIR.iterdir() if p.is_dir() and p.name.startswith("T-"))
done = [t for t in ids if preflight_task.completed_verdicts(t)]
print(f"# contracts={len(ids)} completed={len(done)}", file=sys.stderr)
for t in done: print(t)

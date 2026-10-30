"""JSON-line stdin bridge into offline W&B, using the existing body environment."""
import json
import sys

from egosurgery.utils import tracking


def main():
    record = json.loads(sys.stdin.readline())
    run = tracking.init(record["name"], config=record["config"],
                        group=record["config"]["task_id"], job_type="detector",
                        exp_dir=record["directory"])
    if run is None:
        raise RuntimeError("W&B offline tracking unavailable")
    print("TRACKING_READY", flush=True)
    for line in sys.stdin:
        record = json.loads(line)
        if record.get("finish"):
            break
        tracking.log(record["metrics"], step=record["step"])
    tracking.finish()


if __name__ == "__main__":
    main()

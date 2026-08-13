#!/usr/bin/env python3
"""Launch only the fixed deployed keeper in a detached session."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

KEEPER = Path("/home/ubuntu/bin/keeper.sh")


def main() -> int:
    if len(sys.argv) != 1:
        print("launch_keeper.py does not accept arguments", file=sys.stderr)
        return 2
    process = subprocess.Popen(
        [str(KEEPER)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    print(json.dumps({"keeper_pid": process.pid}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

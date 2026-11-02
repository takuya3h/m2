#!/bin/bash
# andrew へ読むだけの命令を送る包み。送った命令をすべて記録する（Task G-2）
LOG=/home/ubuntu/slocal2/m2/tasks/T-2026-11-02-bengio-align-andrew/andrew_cmds.log
STDIN_NOTE="${A_STDIN:-}"
printf '%s\t%s\t%s\n' "$(date -Is)" "${STDIN_NOTE:+stdin=$STDIN_NOTE }" "$1" >> "$LOG"
exec ssh -o StrictHostKeyChecking=yes -o UpdateHostKeys=no -o BatchMode=yes -o ConnectTimeout=15 andrew "$1"

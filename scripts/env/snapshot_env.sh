#!/usr/bin/env bash
# D3-1: 環境の完全記録。**環境を変更する前に必ず実行する**（可逆性の担保）。
#
# 出力先は第 1 引数 (既定: $OUT/env)。読み取りのみで、環境を一切変更しない。
#
# Usage:
#   bash scripts/env/snapshot_env.sh experiments/analysis/<run>/env
set -uo pipefail

OUTDIR="${1:-${OUT:-.}/env}"
mkdir -p "$OUTDIR"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

{ date; hostname; uname -a; } > "$OUTDIR/system.txt"
nvidia-smi > "$OUTDIR/nvidia_smi.txt" 2>&1 || echo "nvidia-smi failed" >> "$OUTDIR/nvidia_smi.txt"

# venv の実在と素性 (存在しない場合もその事実を記録する)
{
  echo "## ls -la .venv"
  ls -la .venv 2>&1 | head -20
  echo
  echo "## .venv/pyvenv.cfg (作成主体と Python バージョンが分かる)"
  cat .venv/pyvenv.cfg 2>&1
  echo
  echo "## .venv/bin/python --version"
  .venv/bin/python --version 2>&1
  echo
  echo "## site-packages 件数"
  ls .venv/lib/*/site-packages/ 2>/dev/null | wc -l
} > "$OUTDIR/venv_exists.txt" 2>&1

# pip freeze (pip 非搭載の uv 製 venv では失敗しうるので uv pip も試す)
.venv/bin/python -m pip freeze > "$OUTDIR/before_pip_freeze.txt" 2>&1
if ! grep -qE '^[A-Za-z0-9_.-]+==' "$OUTDIR/before_pip_freeze.txt" 2>/dev/null; then
  echo "# python -m pip freeze が使えないため uv pip freeze を併記" >> "$OUTDIR/before_pip_freeze.txt"
  uv pip freeze --python .venv/bin/python >> "$OUTDIR/before_pip_freeze.txt" 2>&1 || true
fi

.venv/bin/python -c \
  "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())" \
  > "$OUTDIR/before_torch.txt" 2>&1

# uv.lock / pyproject の状態 (uv run の副作用で書き換わることがある)
{
  echo "## git status (uv.lock / pyproject.toml / .venv)"
  git status --porcelain uv.lock pyproject.toml .venv 2>&1
  echo
  echo "## uv.lock mtime"
  stat -c '%y %n' uv.lock 2>&1
  echo "## pyproject.toml mtime"
  stat -c '%y %n' pyproject.toml 2>&1
} > "$OUTDIR/repo_state.txt" 2>&1

echo "snapshot written to $OUTDIR"

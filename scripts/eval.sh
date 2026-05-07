#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: bash scripts/eval.sh experiments/YYYY-MM-DD_NNN_short-description"
    exit 1
fi

EXPERIMENT_DIR="$1"

if [ ! -f "${EXPERIMENT_DIR}/config.yaml" ]; then
    echo "Error: config.yaml not found in ${EXPERIMENT_DIR}"
    exit 1
fi

if [ ! -f "${EXPERIMENT_DIR}/eval_command.sh" ]; then
    echo "Error: eval_command.sh not found in ${EXPERIMENT_DIR}"
    exit 1
fi

mkdir -p "${EXPERIMENT_DIR}/logs"

LOG_FILE="${EXPERIMENT_DIR}/logs/eval.log"
echo "Starting evaluation for experiment: ${EXPERIMENT_DIR}"
echo "Log: ${LOG_FILE}"

bash "${EXPERIMENT_DIR}/eval_command.sh" 2>&1 | tee "${LOG_FILE}"

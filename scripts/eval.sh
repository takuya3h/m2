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

mkdir -p "${EXPERIMENT_DIR}/logs"

LOG_FILE="${EXPERIMENT_DIR}/logs/eval.log"

echo "Starting evaluation for experiment: ${EXPERIMENT_DIR}"
echo "Log: ${LOG_FILE}"

python -m research_template.evaluate \
    --config "${EXPERIMENT_DIR}/config.yaml" \
    --output-dir "${EXPERIMENT_DIR}" \
    2>&1 | tee "${LOG_FILE}"

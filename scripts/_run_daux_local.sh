#!/usr/bin/env bash
# STEP D-aux ローカル実行（efros・system python3・GAP/region キャッシュは lecun 由来を symlink 済）。
# 引数で「フェーズ」を選ぶ: gate / hand_rest / sys2 / shuffle
# 各 run は ExperimentManager が採番し証跡を残す（notion 自動投稿は .env 認証時のみ）。
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH=src
[ -f .env ] && { set -a; source .env; set +a; }
mkdir -p logs
PY=python3
PHASE="${1:-gate}"

# 1 run 実行ヘルパ: <gpu> <logname> <script> <args...>
run1() { local gpu="$1" log="$2"; shift 2
  local t0; t0=$(date +%H:%M:%S)
  echo "[$t0] START gpu$gpu $log :: $*"
  CUDA_VISIBLE_DEVICES="$gpu" $PY "$@" > "logs/$log.log" 2>&1
  local rc=$?
  echo "[$(date +%H:%M:%S)] DONE  gpu$gpu $log (rc=$rc)"
  return $rc
}

# 2 GPU に振り分けて 2 本ずつ wave 実行するランナー。job = "logname|script arg...".
run_waves() {
  local -a jobs=("$@"); local i=0
  while [ $i -lt ${#jobs[@]} ]; do
    local ja="${jobs[$i]}"; local jb="${jobs[$((i+1))]:-}"
    local la="${ja%%|*}" ca="${ja#*|}"
    run1 0 "$la" $ca &
    local pa=$!
    local pb=""
    # 起動を数秒ずらして ExperimentManager の seq 採番競合（並列 setup レース）を回避
    sleep 4
    if [ -n "$jb" ]; then local lb="${jb%%|*}" cb="${jb#*|}"; run1 1 "$lb" $cb & pb=$!; fi
    wait "$pa"; [ -n "$pb" ] && wait "$pb"
    i=$((i+2))
  done
}

S4="scripts/train_s4_tecno.py"
HAUX="scripts/train_haux.py"
TAUX="scripts/train_taux.py"

case "$PHASE" in
  gate)
    # S4 分母 3seed + H-1 presence oracle 3seed（同一環境で paired-σ を取るため）
    run_waves \
      "s4_seed42|$S4 --seed 42"   "s4_seed123|$S4 --seed 123" \
      "s4_seed456|$S4 --seed 456" "h1_presence_oracle_seed42|$HAUX --hand-feature-type presence --hand-source oracle --seed 42" \
      "h1_presence_oracle_seed123|$HAUX --hand-feature-type presence --hand-source oracle --seed 123" \
      "h1_presence_oracle_seed456|$HAUX --hand-feature-type presence --hand-source oracle --seed 456"
    ;;
  hand_rest)
    # H-2 count / H-3 geom / H-5 own_other / H-6 presence+tool（各 3seed・oracle）
    run_waves \
      "h2_count_oracle_seed42|$HAUX --hand-feature-type count --hand-source oracle --seed 42" \
      "h2_count_oracle_seed123|$HAUX --hand-feature-type count --hand-source oracle --seed 123" \
      "h2_count_oracle_seed456|$HAUX --hand-feature-type count --hand-source oracle --seed 456" \
      "h3_geom_oracle_seed42|$HAUX --hand-feature-type geom --hand-source oracle --seed 42" \
      "h3_geom_oracle_seed123|$HAUX --hand-feature-type geom --hand-source oracle --seed 123" \
      "h3_geom_oracle_seed456|$HAUX --hand-feature-type geom --hand-source oracle --seed 456" \
      "h5_ownother_oracle_seed42|$HAUX --hand-feature-type own_other --hand-source oracle --seed 42" \
      "h5_ownother_oracle_seed123|$HAUX --hand-feature-type own_other --hand-source oracle --seed 123" \
      "h5_ownother_oracle_seed456|$HAUX --hand-feature-type own_other --hand-source oracle --seed 456" \
      "h6_presencetool_oracle_seed42|$HAUX --hand-feature-type presence --hand-source oracle --with-tool --tool-source oracle --seed 42" \
      "h6_presencetool_oracle_seed123|$HAUX --hand-feature-type presence --hand-source oracle --with-tool --tool-source oracle --seed 123" \
      "h6_presencetool_oracle_seed456|$HAUX --hand-feature-type presence --hand-source oracle --with-tool --tool-source oracle --seed 456"
    ;;
  shuffle)
    # 最良手法の shuffle control（引数で手法を渡す。既定 presence）
    FT="${2:-presence}"
    run_waves \
      "hshuf_${FT}_seed42|$HAUX --hand-feature-type $FT --hand-source oracle --shuffle-hand --seed 42" \
      "hshuf_${FT}_seed123|$HAUX --hand-feature-type $FT --hand-source oracle --shuffle-hand --seed 123" \
      "hshuf_${FT}_seed456|$HAUX --hand-feature-type $FT --hand-source oracle --shuffle-hand --seed 456"
    ;;
  sys2)
    # 系統②: 問いA(T-1/2/3・kernel=tecno) + 問いB(T-4 tecno / T-6 mingru・feature=none)。各3seed。
    run_waves \
      "t1_movavg_seed42|$TAUX --temporal-kernel tecno --temporal-feature movavg --temporal-k 3 --seed 42" \
      "t1_movavg_seed123|$TAUX --temporal-kernel tecno --temporal-feature movavg --temporal-k 3 --seed 123" \
      "t1_movavg_seed456|$TAUX --temporal-kernel tecno --temporal-feature movavg --temporal-k 3 --seed 456" \
      "t2_delta_seed42|$TAUX --temporal-kernel tecno --temporal-feature delta --seed 42" \
      "t2_delta_seed123|$TAUX --temporal-kernel tecno --temporal-feature delta --seed 123" \
      "t2_delta_seed456|$TAUX --temporal-kernel tecno --temporal-feature delta --seed 456" \
      "t3_window_seed42|$TAUX --temporal-kernel tecno --temporal-feature window --temporal-k 3 --seed 42" \
      "t3_window_seed123|$TAUX --temporal-kernel tecno --temporal-feature window --temporal-k 3 --seed 123" \
      "t3_window_seed456|$TAUX --temporal-kernel tecno --temporal-feature window --temporal-k 3 --seed 456" \
      "t4_tecno_seed42|$TAUX --temporal-kernel tecno --temporal-feature none --seed 42" \
      "t4_tecno_seed123|$TAUX --temporal-kernel tecno --temporal-feature none --seed 123" \
      "t4_tecno_seed456|$TAUX --temporal-kernel tecno --temporal-feature none --seed 456" \
      "t6_mingru_seed42|$TAUX --temporal-kernel mingru --temporal-feature none --seed 42" \
      "t6_mingru_seed123|$TAUX --temporal-kernel mingru --temporal-feature none --seed 123" \
      "t6_mingru_seed456|$TAUX --temporal-kernel mingru --temporal-feature none --seed 456"
    ;;
  *) echo "unknown phase: $PHASE"; exit 2 ;;
esac
echo "[$(date +%H:%M:%S)] PHASE=$PHASE 完了"

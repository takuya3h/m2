#!/usr/bin/env bash
# 改善検出器 vs 凍結源 の phase probe（seed42・S4 GAP-only / B2a-pred / T1a）。
# 抽出（scripts/_extract_improved.sh）完了後に実行。改善検出器 tag を第1引数で渡す。
#   bash scripts/_run_phase_probe.sh relation_detr_augstrong_seed42
# 各手法を {凍結源, 改善} の 2 特徴で seed42 学習し、best metrics.json を突き合わせて Δ を出す。
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH=src
[ -f .env ] && { set -a; source .env; set +a; }
PY=python3
AUG="${1:?improved frozen_tag}"
SEED="${2:-42}"
GPU="${3:-0}"
FRO=relation_detr_seed42
RES="logs/phase_probe_results_seed${SEED}.tsv"
: > "$RES"

runone() { # <tag> <src> <script...>
  local tag="$1" src="$2"; shift 2
  echo "[$(date +%H:%M:%S)] probe $tag seed$SEED (src=$src)"
  local d
  d=$(RELDETR_FROZEN_TAG="$src" CUDA_VISIBLE_DEVICES=$GPU $PY "$@" --seed "$SEED" 2>"logs/probe_${tag}_s${SEED}.err" \
        | tee "logs/probe_${tag}_s${SEED}.log" | grep -oE "evidence written -> .*" | tail -1 | sed 's/.*-> //')
  echo -e "${tag}\t${d}" >> "$RES"
  echo "   -> $d"
}

runone s4_frozen  "$FRO" scripts/train_s4_tecno.py
runone s4_aug     "$AUG" scripts/train_s4_tecno.py
runone b2a_frozen "$FRO" scripts/train_b2a.py --tool-source pred
runone b2a_aug    "$AUG" scripts/train_b2a.py --tool-source pred
runone t1a_frozen "$FRO" scripts/train_t1a.py --description t1a_probe_frozen
runone t1a_aug    "$AUG" scripts/train_t1a.py --description t1a_probe_aug

echo "" && echo "=== PHASE PROBE 結果（seed42・acc / macro-F1）==="
$PY - "$RES" <<'PY'
import json, sys
rows = [l.split("\t") for l in open(sys.argv[1]) if l.strip()]
M = {}
for tag, d in rows:
    try:
        m = json.load(open(f"{d.strip()}/metrics.json"))
        M[tag] = (m.get("phase_accuracy"), m.get("phase_macro_f1"))
    except Exception as e:
        M[tag] = (None, None)
def line(name, fro, aug):
    fa, ff = M.get(fro, (None, None)); aa, af = M.get(aug, (None, None))
    if None in (fa, aa):
        print(f"{name:6s} | frozen={fa} aug={aa} (欠測)"); return
    print(f"{name:6s} | frozen acc={fa:.4f} F1={ff:.4f} | aug acc={aa:.4f} F1={af:.4f} "
          f"| Δacc={ (aa-fa)*100:+.2f}pp ΔF1={(af-ff)*100:+.2f}pp")
line("S4",  "s4_frozen",  "s4_aug")
line("B2a", "b2a_frozen", "b2a_aug")
line("T1a", "t1a_frozen", "t1a_aug")
print("\n[gate] B2a Δacc>0 かつ S4/T1a も非劣化なら『検出器改善→phase 改善』方向あり → 3-seed 昇格")
PY
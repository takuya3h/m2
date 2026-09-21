#!/usr/bin/env bash
# Stage 1 検出塔の全 run を評価して証跡を作る。契約 T-2026-09-18-stage1-detector-towers。
#
#   val  : 全 14 run（best_ap.pth を折りの val で評価。per-class AP を得るため）
#   test : **確定した両塔について折りごとに一度だけ**（2 塔 × 5 折り = 10 回）。
#          折り A は seed 42 を確定塔とする（凍結源と同じ seed）。
#          **test は選定に使わない。** 学習の最良 epoch は既に折り内 val で決まっている。
#
# test の評価は毎回 test アクセス台帳へ 1 行追記する。回数はその行数で数える。
set -uo pipefail
BODY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$BODY/experiments/baselines/stage1_dtower"
LEDGER="$BODY/experiments/baselines/stage1_dtower/test_access_ledger.csv"
MODE="${1:-all}"   # all | val | test

if [ ! -f "$LEDGER" ]; then
    echo "timestamp_utc,task_id,tower,fold,seed,split,checkpoint_sha256,n_images,mAP,reason" > "$LEDGER"
fi

cd "$BODY"
# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda
export EGO_ROOT="$BODY/data/raw/ego"

eval_one() {   # tower fold seed split
    local tower="$1" fold="$2" seed="$3" split="$4"
    local run="d${tower}_fold${fold}_seed${seed}"
    local dir="$ROOT/$run"
    local ckpt="$dir/work/best_ap.pth"
    local out="$dir/eval_${split}.json"
    [ -f "$ckpt" ] || { echo "[eval] ckpt 無し: $ckpt"; return 1; }
    [ -f "$out" ] && { echo "[eval] 済み: $run $split"; return 0; }
    case "$tower" in
      coco)     cfg="configs/train_config_egosurgery_seed${seed}.py" ;;
      imagenet) cfg="configs/train_config_egosurgery_stage1_imagenet_seed${seed}.py" ;;
    esac
    export EGO_ANN_DIR="$BODY/data/annotations/egosurgery_tool_folds/${fold}"
    echo "[eval] $run $split 開始 $(date -u '+%H:%M:%S')"
    accelerate launch --num_processes 2 --main_process_port 29701 \
        "$BODY/scripts/eval_relation_detr_map.py" \
        --config "$cfg" --checkpoint "$ckpt" --split "$split" --out "$out" \
        > "$dir/eval_${split}.log" 2>&1
    local rc=$?
    if [ $rc -ne 0 ]; then echo "[eval] 失敗 rc=$rc: $run $split"; return $rc; fi
    if [ "$split" = "test" ]; then
        local sha n m
        sha=$(sha256sum "$ckpt" | cut -d' ' -f1)
        n=$(python -c "import json;print(len(json.load(open('$EGO_ANN_DIR/instances_test.json'))['images']))")
        m=$(python -c "import json;print(json.load(open('$out'))['AP'])")
        echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ'),T-2026-09-18-stage1-detector-towers,${tower},${fold},${seed},test,${sha},${n},${m},確定塔の最終評価（折りごとに一度）" >> "$LEDGER"
    fi
    echo "[eval] $run $split 完了 $(date -u '+%H:%M:%S')"
}

if [ "$MODE" = "all" ] || [ "$MODE" = "val" ]; then
    for tower in coco imagenet; do
        for seed in 42 123 456; do eval_one "$tower" A "$seed" val; done
        for fold in B C D E; do eval_one "$tower" "$fold" 42 val; done
    done
fi
if [ "$MODE" = "all" ] || [ "$MODE" = "test" ]; then
    for tower in coco imagenet; do
        for fold in A B C D E; do eval_one "$tower" "$fold" 42 test; done
    done
fi
echo "[eval] 全て終了 $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "[eval] test 台帳の行数（ヘッダ除く）: $(( $(wc -l < "$LEDGER") - 1 ))"

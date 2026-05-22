---
description: S0〜S9 のステージ実験を smoke / 本番構成で起動・監視する
argument-hint: <stage> [smoke|full] (例: s0_tool_baseline smoke)
---

ステージ実験を起動します。引数: `$ARGUMENTS`

手順:

1. 第1引数をステージ名（Hydra の `stage=` の値）、第2引数を構成（`smoke` / `full`、
   省略時は `full`）として解釈する。第1引数が無ければユーザーに確認する。
2. `.venv` の Python を使う（`source .venv/bin/activate` 済みか、`.venv/bin/python` を明示）。
3. **smoke 構成**の場合は次の override を付けて短時間で疎通確認する:
   `model.backbone=dinov2_vits14_reg data.img_size=224 data.limit=16 data.batch_size=2`
   `data.num_workers=0 train.epochs=1 train.freeze_backbone=true logging.wandb_enabled=false`
4. **full 構成**の場合はステージ config の既定値で実行する。長時間（GPU 多時間）に
   なるため、必ず `run_in_background: true` で起動し、Monitor で
   `\[S0\]\[epoch|Traceback|Error|OOM|completed` 等の進捗・失敗シグネチャを監視する。
5. 実行コマンドは
   `PYTHONPATH=src .venv/bin/python -m egosurgery.train stage=<stage> seed=42 <override>`。
   研究計画に従い、本番は seed 42/123/456 の 3 回（または `scripts/run_sX.sh`）で回す。
6. 完了後、`experiments/` に生成されたフォルダと `metrics.json` の主要値を要約する。
   **mAP 等の数値は実測値のみを報告し、捏造しない。**

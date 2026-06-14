# Sense-X Co-DETR (9-encoder) seed42 — 退避チェックポイント (再開用)

**ステータス: 中止 (環境統一のため)。本フォルダは「将来 9encoder を再開したくなった場合」の退避物。**
ベンチマーク (Δ基準点) には使わない。経緯は `docs/experiment_log.md` 2026-05-29 の項、
および `experiments/baselines/s0_013_sensex_codino_bbox_seed42/STOPPED_for_env_unification.md` 参照。

## なぜ退避したか
学習ログ・ckpt は元々 `/tmp/sensex_codino_work_seed42/` にあったが、`/tmp` は
サーバー再起動で消える。再起動後も epoch7 から再開できるよう永続パスへ退避した。

## 退避物 (2026-05-29, md5 検証済み)
- `epoch_7.pth` (782MB, md5 386c663a..., **再開点**。state_dict + optimizer + meta(epoch7,iter16905) 含む)
- `best_bbox_mAP_epoch_7.pth` (782MB, md5 750be7cb..., ベスト重み)
- `20260528_225228.log.json` / `20260529_114906.log.json` (epoch1-7 の学習曲線。wandb backfill 用)
- `co_dino_5scale_9encoder_lsj_r50_egosurgery.py` (使用した config のコピー)

## 評価済み val bbox_mAP (epoch1-7)
e1=0.590 / e2=0.640 / e3=0.661 / e4=0.686 / e5=0.687 / e6=0.675 / e7=0.696(best)
※ epoch8 は train 途中 (iter950/2415) で停止、val 未実施。12 epoch 未完。

## 再開手順 (もし将来やる場合)
**環境**: `.venv-mmdet2` (torch 1.13.1+cu117 / mmcv-full 1.7 / mmdet 2.25 / Python 3.8)。
torch 2.1 では mmcv-full 1.x の CUDA 拡張がビルドできないため、この専用 venv が必須
(これが中止理由でもある。詳細は memory:mmdet2x-ddp-gotchas / s0-detector-seq-mapping)。

```bash
# 1. ckpt を作業ディレクトリへ戻す
mkdir -p /tmp/sensex_codino_work_seed42
cp experiments/baselines/_aborted_sensex_codino_9enc/epoch_7.pth /tmp/sensex_codino_work_seed42/
cp experiments/baselines/_aborted_sensex_codino_9enc/*.log.json /tmp/sensex_codino_work_seed42/

# 2. DDP 2GPU で resume (前回 /tmp/run_sensex_codino_resume.sh と同パターン)
cd /home/ubuntu/slocal2/m2
source .venv-mmdet2/bin/activate
export PYTHONPATH=third_party/Co-DETR
CONFIG=third_party/Co-DETR/projects/configs/co_dino/co_dino_5scale_9encoder_lsj_r50_egosurgery.py
# rank0/rank1 をそれぞれ起動 (CUDA_VISIBLE_DEVICES=0 / =1, MASTER_PORT 任意):
#   python third_party/Co-DETR/tools/train.py $CONFIG \
#     --work-dir /tmp/sensex_codino_work_seed42 --seed 42 --launcher pytorch \
#     --resume-from /tmp/sensex_codino_work_seed42/epoch_7.pth
# → "resumed epoch 7, iter 16905" が出れば成功。残り epoch8-12。
```

resume は optimizer/lr/epoch カウンタも復元するので Δ基準点汚染なし
(ただし環境が torch1.13 で他検出器=torch2.1 と異なる点は変わらないので、
ベンチに使うなら「環境差あり」の明記が必要)。

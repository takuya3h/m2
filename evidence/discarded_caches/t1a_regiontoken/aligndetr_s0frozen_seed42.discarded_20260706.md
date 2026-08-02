# 破棄理由

破棄日: 2026-07-06（ディレクトリ名） / ディレクトリ mtime は 2026-07-07 17:50
記録日: 2026-08-02（`/tmp` の実行痕跡から再構成）

## 🔴 破棄理由は判別不能

git / `docs/` / `tasks/` のいずれにも理由の記載が無く、2026-08-02 時点で**判別できない**。
以下は実測できた事実のみを記す。推測で埋めていない。

## 実測できたこと

### 生成の経緯

- **生成日時**: 2026-07-06 03:26（val）/ 03:32（train）
- **生成元**: `/tmp/queue_runner/queue4_parallel_extract.sh`
  （`model_final.pth` の出現を watch し、2 GPU で 4 抽出を並列実行する watchdog）
- **使用 ckpt**: `/tmp/aligndetr_s0frozen_seed42_v2/model_final.pth`
  （2026-07-06 03:24 完了の S0-frozen 2 GPU DDP 学習。bbox AP 68.596）
- **使用 config**: `aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py`

07-03 の 1 GPU 学習が NCCL 失敗したため、`queue4_v2.sh` で
「他 AlignDETR (s0_028) と GPU 数を揃える」目的で 2 GPU DDP に切り替えた版である。

### 抽出は正常完走している

```
val   1515 x 3840   (23,325,456 bytes)   nonzero frac=1.000  absmax=4.572
train 9657 x 3840  (148,679,688 bytes)   nonzero frac=1.000  absmax=4.576
```

本ディレクトリの `*_regiontoken.log` が一次証拠。エラー・警告なし。

### 後継（07-10 版）との差

| 項目 | 本ディレクトリ（07-06） | 後継 `aligndetr_s0frozen_seed42`（07-10 17:39-17:47） |
|---|---|---|
| val / train の npz サイズ | 同一 | 同一 |
| **val / train の内容（md5）** | **不一致** | **不一致** |
| test split | **無し** | `test_regiontoken.npz`（65,664,456 bytes）**有り** |
| 抽出ログ | 有り | **無し** |

md5 実測値:

```
val_regiontoken.npz    07-06: 1ed44cd3fda8c84cd24b8f8be86b15c1
                       07-10: e41ede905f0f93acc658875698990f7f
train_regiontoken.npz  07-06: 29e132a2ad290f45acd4e0f4d3451904
                       07-10: 9e4e40ef6ab797c990709dab0cdacffb
```

**同じ形状・同じサイズだが内容が異なる。** したがって破棄は単なる整理ではなく、
何らかの是正であったと考えられる（ただし理由の記録は無い）。

## 判別できなかったこと

1. **破棄の明示的理由。** どこにも記録が無い。

2. **なぜ 07-06 版と 07-10 版で内容が変わったのか。** 以下をすべて確認したが説明がつかない。
   - 抽出スクリプト `scripts/extract_t1a_regiontoken_aligndetr.py` は
     **HEAD（`891953c`, 07-03）と一致**しており、作業ツリー差分も無い。
     mtime は 07-10 10:31:06 だが、`extract_stage1_features_aligndetr.py` と
     **秒まで同一**であり、個別編集ではなく checkout / rsync 等の一括操作の痕跡と見られる。
   - **v3 の ckpt は存在しない。** `/tmp` に残る S0-frozen 学習成果は v2（07-06 03:24）のみ。
   - 07-10 の再抽出はログを残していないため、実際に渡された引数を確認できない。

   考えうる原因（**いずれも未検証。推測である**）: 抽出処理の非決定性、
   異なる GPU での実行、記録に残っていない引数の違い。

3. **なぜ test split が 07-06 版に無いのか。**
   `queue4_parallel_extract.sh` は val と train しか抽出しない実装なので、
   test が無いこと自体はスクリプトどおりである。ただし test を後から必要と
   判断したのか、最初から漏れていたのかは判別できない。

## 関連

- `data/processed/stage1_features/aligndetr_seed42.discarded_20260705/DISCARDED.md`
  （07-03 の NCCL 失敗に端を発する一連の是正。本件はその後段）
- `data/processed/b2a_detsignal/aligndetr_s0frozen_seed42.discarded_20260706/DISCARDED.md`
  （同じ watchdog が同時刻に生成した対の成果物）
- `evidence/aligndetr_s0frozen_incident_20260703/`
  （`queue4_v2.sh` / `queue4_parallel_extract.sh` の原本を保全）

---

## このファイルの git 追跡について

`.gitignore:15` の `data/processed/**` により本ファイルは **git で追跡されていない**。
同内容の追跡コピーが `evidence/discarded_caches/` にある（対応表は同ディレクトリの `README.md`）。
**両者が食い違った場合は `evidence/` 側を正とする。**

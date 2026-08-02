# 破棄理由

破棄日: 2026-07-06（ディレクトリ名） / ディレクトリ mtime は 2026-07-06 03:40
記録日: 2026-08-02（`/tmp` の実行痕跡から再構成）

## 🔴 破棄理由は判別不能

git / `docs/` / `tasks/` のいずれにも理由の記載が無く、2026-08-02 時点で**判別できない**。
以下は実測できた事実のみを記す。推測で埋めていない。

## 実測できたこと

### 生成の経緯

- **生成日時**: 2026-07-06 03:28（val）/ 03:40（train）
- **生成元**: `/tmp/queue_runner/queue4_parallel_extract.sh`
  （`t1a_regiontoken` 側と**同じ watchdog が同時刻に生成した対の成果物**）
- **使用 ckpt**: `/tmp/aligndetr_s0frozen_seed42_v2/model_final.pth`
  （2026-07-06 03:24 完了の S0-frozen 2 GPU DDP 学習。bbox AP 68.596）
- **使用 config**: `aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py`

### 抽出は正常完走している

```
val   1515 x 15    (145,956 bytes)   mean=0.156  max=0.958
train 9657 x 15    (927,588 bytes)
```

本ディレクトリの `*_toolpresence.log` が一次証拠。エラー・警告なし。
15 次元は術具 15 クラスの presence スコア。

### 🔴 後継が存在しない

`data/processed/b2a_detsignal/` に `aligndetr_s0frozen_seed42`（破棄されていない版）は
**存在しない**。対になる `t1a_regiontoken` 側は 07-10 17:39-17:47 に作り直されているが、
**tool-presence 側は作り直されていない**。

```
data/processed/b2a_detsignal/
  aligndetr_s0frozen_seed42.discarded_20260706   ← 本ディレクトリ（後継なし）
  relation_detr_augstrong_hires_seed42
  relation_detr_augstrong_seed{42,123,456}
  relation_detr_seed{42,123,456}
```

したがって **AlignDETR の tool-presence 信号は現在どこにも存在しない**。

## 判別できなかったこと

1. **破棄の明示的理由。** どこにも記録が無い。

2. **なぜ後継が作られなかったのか。** 以下のいずれかだが判別できない。
   - 07-10 の再抽出時に tool-presence を実施し忘れた（取りこぼし）
   - AlignDETR の tool-presence は不要と判断された（意図的）
   - 別の場所に作られた（`data/processed/` 配下には見当たらない）

   `t1a_regiontoken` 側だけが再生成されている非対称は実測できるが、
   それが意図か取りこぼしかを示す記録は無い。

3. **破棄が是正だったのか整理だったのか。**
   対になる `t1a_regiontoken` 側は 07-06 版と 07-10 版で
   **npz の内容が md5 レベルで異なる**ことを確認済み（同サイズ・同形状）。
   本ディレクトリは後継が無いため同様の比較ができない。

## 関連

- `data/processed/t1a_regiontoken/aligndetr_s0frozen_seed42.discarded_20260706/DISCARDED.md`
  （同じ watchdog が同時刻に生成した対の成果物。内容差の md5 実測値を記載）
- `data/processed/stage1_features/aligndetr_seed42.discarded_20260705/DISCARDED.md`
  （07-03 の NCCL 失敗に端を発する一連の是正。本件はその後段）
- `evidence/aligndetr_s0frozen_incident_20260703/`
  （`queue4_parallel_extract.sh` の原本を保全）

---

## このファイルの git 追跡について

`.gitignore:15` の `data/processed/**` により本ファイルは **git で追跡されていない**。
同内容の追跡コピーが `evidence/discarded_caches/` にある（対応表は同ディレクトリの `README.md`）。
**両者が食い違った場合は `evidence/` 側を正とする。**

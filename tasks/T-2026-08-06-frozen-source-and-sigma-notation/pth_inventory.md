# 凍結源候補の棚卸し（2026-08-06）

## 正本

| 項目 | 値 |
|---|---|
| パス | third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth |
| SHA-256 | 03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824 |
| 11ホスト監査 | 11 / 11 一致 |

## 実行ホスト上の 100MB 超 ckpt

実行ホスト: `aolab`。`find third_party checkpoints work_dirs experiments -name "*.pth" -size +100M` の全件（`checkpoints/` `work_dirs/` は本ホストに存在せず 0 件）。

| SHA-256 先頭16 | サイズ | パス | 正本と同一か |
|---|---|---|---|
| 03936318f9d45ac9 | 195421066 | third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth | 同一（正本そのもの） |
| 03936318f9d45ac9 | 195421066 | third_party/Relation-DETR/checkpoints/relation_detr_resnet50_egosurgery/train/seed42/best_ap.pth | 同一 |
| 073c7cdad902f717 | 614008369 | experiments/baselines/s0_011_ddq_bbox_seed123/epoch_12.pth | 異なる |
| 090a6064544289a1 | 593767417 | experiments/baselines/s0_001_maskdino_bbox_seed42/epoch_12.pth | 異なる |
| 0b8a5c7186100f2d | 135887560 | experiments/baselines/s0_004_varifocanet_bbox_seed42/best_val_mAP_epoch_12.pth | 異なる |
| 0c098c953c88be7c | 821644285 | experiments/baselines/s0_009_codetr_bbox_seed456/epoch_12.pth | 異なる |
| 145e86fe089d19dc | 195422778 | experiments/detector_improve/augstrong_seed123/best_ap50.pth | 異なる（サイズも別） |
| 171be0939f8cb89d | 135888328 | experiments/baselines/s0_005_varifocanet_bbox_seed123/best_val_mAP_epoch_12.pth | 異なる |
| 28b57085b47e1f9e | 215072844 | experiments/baselines/s0_002_maskdino_bbox_seed123/best_val_mAP_epoch_12.pth | 異なる |
| 2c4ab252cfb4cbb5 | 195458910 | experiments/hand2det_dev/hand2det_1ep_4ch_film_seed42/checkpoints/best_hand2det.pth | 異なる |
| 430e6d247822437a | 195422778 | third_party/Relation-DETR/checkpoints/relation_detr_resnet50_egosurgery/train/seed42/best_ap50.pth | 異なる（サイズも別） |
| 44cd1d5c447457c0 | 614008945 | experiments/baselines/s0_010_ddq_bbox_seed42/epoch_12.pth | 異なる |
| 46723a7d708df616 | 228925138 | experiments/baselines/s0_011_ddq_bbox_seed123/best_val_mAP_epoch_12.pth | 異なる |
| 4a6b85199e5cd01f | 593769209 | experiments/baselines/s0_003_maskdino_bbox_seed456/epoch_12.pth | 異なる |
| 4b706b43fe05e2ad | 266036700 | experiments/baselines/s0_006_varifocanet_bbox_seed456/epoch_12.pth | 異なる |
| 4b84fae28c07b8a1 | 195421066 | experiments/detector_improve/augstrong_seed456/best_ap.pth | 異なる（**サイズは正本と同一** → 紛らわしい候補） |
| 4dc2ea546fe3e2af | 195422778 | experiments/detector_improve/augstrong_hires_seed42/best_ap50.pth | 異なる |
| 5992c5ee518de62b | 195421066 | third_party/Relation-DETR/checkpoints/relation_detr_resnet50_egosurgery/train/2026-05-30-04_24_20/best_ap.pth | 異なる（**サイズは正本と同一** → 紛らわしい候補） |
| 5f784237e147af70 | 228922258 | experiments/baselines/s0_012_ddq_bbox_seed456/best_val_mAP_epoch_12.pth | 異なる |
| 61d4d3d46b51d10c | 228925778 | experiments/baselines/s0_010_ddq_bbox_seed42/best_val_mAP_epoch_12.pth | 異なる |
| 63cbbb04941a5dac | 195422778 | experiments/detector_improve/augstrong_seed456/best_ap50.pth | 異なる |
| 6c481d5e7f94895f | 821644477 | experiments/baselines/s0_008_codetr_bbox_seed123/epoch_12.pth | 異なる |
| 772d206a72886721 | 593767737 | experiments/baselines/s0_002_maskdino_bbox_seed123/epoch_12.pth | 異なる |
| 7f72b509a24e838d | 195421066 | experiments/detector_improve/augstrong_seed123/best_ap.pth | 異なる（**サイズは正本と同一** → 紛らわしい候補） |
| 8e494ca98d2ee95d | 306754158 | experiments/baselines/s0_009_codetr_bbox_seed456/best_val_mAP_epoch_12.pth | 異なる |
| 8f829b9a090a080f | 215072524 | experiments/baselines/s0_001_maskdino_bbox_seed42/best_val_mAP_epoch_12.pth | 異なる |
| a86aff2a91e91281 | 821643005 | experiments/baselines/s0_007_codetr_bbox_seed42/epoch_12.pth | 異なる |
| b20430a931e0bcb5 | 266034332 | experiments/baselines/s0_004_varifocanet_bbox_seed42/epoch_12.pth | 異なる |
| b5ad70cfbc69b48c | 195422778 | experiments/detector_improve/augstrong_seed42/best_ap50.pth | 異なる |
| bb01eb27385d4fd9 | 195421066 | third_party/Relation-DETR/checkpoints/incoming/seed123/best_ap.pth | 異なる（別 seed の正規 ckpt。サイズは正本と同一） |
| bb01eb27385d4fd9 | 195421066 | third_party/Relation-DETR/checkpoints/relation_detr_resnet50_egosurgery/train/seed123/best_ap.pth | 異なる（同上のコピー） |
| bcff848d58399924 | 215074316 | experiments/baselines/s0_003_maskdino_bbox_seed456/best_val_mAP_epoch_12.pth | 異なる |
| bd6927d32849f6bc | 614005425 | experiments/baselines/s0_012_ddq_bbox_seed456/epoch_12.pth | 異なる |
| c7ddf7df17699349 | 195421066 | experiments/detector_improve/augstrong_hires_seed42/best_ap.pth | 異なる（**サイズは正本と同一** → 紛らわしい候補） |
| d5d2dee55d7a9879 | 195422778 | third_party/Relation-DETR/checkpoints/relation_detr_resnet50_egosurgery/train/seed123/best_ap50.pth | 異なる |
| e543e4aaade14c6a | 306752878 | experiments/baselines/s0_007_codetr_bbox_seed42/best_val_mAP_epoch_12.pth | 異なる |
| e5be543e3ba58c1e | 306754350 | experiments/baselines/s0_008_codetr_bbox_seed123/best_val_mAP_epoch_12.pth | 異なる |
| f0204ae9843e0529 | 195421066 | third_party/Relation-DETR/checkpoints/incoming/seed456/best_ap.pth | 異なる（別 seed の正規 ckpt。サイズは正本と同一） |
| f0204ae9843e0529 | 195421066 | third_party/Relation-DETR/checkpoints/relation_detr_resnet50_egosurgery/train/seed456/best_ap.pth | 異なる（同上のコピー） |
| f4bb109df643f493 | 195421066 | experiments/detector_improve/augstrong_seed42/best_ap.pth | 異なる（**サイズは正本と同一** → 紛らわしい候補） |
| f9dabee44638b262 | 195422778 | third_party/Relation-DETR/checkpoints/relation_detr_resnet50_egosurgery/train/2026-05-30-04_24_20/best_ap50.pth | 異なる |
| faaa228db1025431 | 266035036 | experiments/baselines/s0_005_varifocanet_bbox_seed123/epoch_12.pth | 異なる |
| fb5f112695ae6204 | 135889992 | experiments/baselines/s0_006_varifocanet_bbox_seed456/best_val_mAP_epoch_12.pth | 異なる |
| fd4cf4fbc01f2bcd | 195422778 | third_party/Relation-DETR/checkpoints/relation_detr_resnet50_egosurgery/train/seed456/best_ap50.pth | 異なる |

補足: サイズが正本と同じ 195421066 バイトだが SHA-256 が異なるファイルが複数存在する
（`experiments/detector_improve/augstrong_*/best_ap.pth` 3件、
`third_party/.../train/2026-05-30-04_24_20/best_ap.pth` 1件）。
これらはバイト数だけでは正本と区別できず「紛らわしい候補」に該当するが、
下記のとおり `wrong_frozen_source` 除外 run との対応は本 Task の範囲では特定できていない（UNKNOWN）。

## wrong_frozen_source で除外された run

| ledger_key | config.yaml の凍結源記載 | 正本と一致するか |
|---|---|---|
| UNKNOWN | UNKNOWN | UNKNOWN |

**特定できなかった理由（推測で埋めない）:** `runindex/index.csv` に実在する除外理由列は
`exclusion_reason` だが、SPEC Task 2 Step 2 のスクリプトが用いる列特定ロジック
（`"exclude" in c and "reason" in c`）は `"exclusion_reason"` にマッチしない
（"exclusion" は "exclude" の部分文字列ではない）。この結果、スクリプトは列を
`None` と判定し `UNKNOWN` を出力する。これは SPEC「想定外が起きたときの扱い」表の
「`wrong_frozen_source` の除外理由の列が特定できない」に該当する既定の停止条件であり、
指示どおり実列名を使った代用（推測での置き換え）はせず、`UNKNOWN` のまま記録し
Task 2 を部分完了とする。3件の `wrong_frozen_source` run の特定と、その凍結源記載の
転記（Step 3）は本 Task では未実施。

## 未追跡 smoke ディレクトリの実測（2026-08-06、Task 6）

`git status --porcelain experiments/transfer/` で未追跡（`??`）と確認された3件:

- `experiments/transfer/_smoke_artifacts_ctrl/`
- `experiments/transfer/_smoke_artifacts_inj/`
- `experiments/transfer/_smoke_fullval/`

`runindex/index.csv` を `ledger_key` および `path` 列で全文検索したが、3件とも
**1件もヒットしない**（`excluded` 済み run としても含まれていない）。各ディレクトリの
中身は `checkpoints/` `logs/` `predictions/` のみで、`config.yaml` と `metrics.json` が
存在しない。これは `make runindex`（`harvest_runindex.py`）が run として認識するために
必要な最低要件を満たしていないためと考えられ、収穫対象外であることと整合する。

| 観測 | 判定 |
|---|---|
| index に載っている | いいえ（0件） |
| 除外済みとして載っている | いいえ（0件） |
| index に無く除外にも無い | **該当**。`config.yaml`/`metrics.json` を欠き収穫要件未達のため |

**結論:** ホスト間で `runindex` が割れるリスクは無い（そもそも収穫されないため、
未追跡ホストの有無に関わらず全ホストで同じ結果になる）。backlog 起票は不要と判断する。


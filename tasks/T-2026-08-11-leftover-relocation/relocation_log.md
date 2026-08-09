# 退避の記録（2026-08-09 実施）

実行ホスト `lecun`。契約 `T-2026-08-11-leftover-relocation` に基づく。

## 退避先

    ~/m2-archive/20260811/

元の階層構造を保って移動した。**削除していない。**
repo と同一ファイルシステム（デバイス番号 1048697）のため、移動は rename であり
データの複製は発生していない。

## 対応表

退避先での経路は、上の退避先に元の相対経路をそのまま連結したものである。
例: `experiments/baselines/_smoke_e3/s0_001_smoke_e3_seed42` は
`~/m2-archive/20260811/experiments/baselines/_smoke_e3/s0_001_smoke_e3_seed42` にある。

| 元の場所 | ファイル数 | 容量 | 分類 |
|---|---|---|---|
| `experiments/baselines/_aborted_codetr_no_config/s0_007_codetr_bbox_seed42` | 7 | 48 KB | 中断した run |
| `experiments/baselines/_aborted_codetr_no_config/s0_008_codetr_bbox_seed123` | 7 | 48 KB | 中断した run |
| `experiments/baselines/_aborted_codetr_no_config/s0_009_codetr_bbox_seed456` | 7 | 48 KB | 中断した run |
| `experiments/baselines/_aborted_s0_cuda_visible_misconfig/s0_001_maskdino_bbox_seed42` | 22 | 206416 KB | 中断した run |
| `experiments/baselines/_failed_num_workers_zero/s0_001_maskdino_bbox_seed42` | 11 | 144 KB | 失敗した run |
| `experiments/baselines/_failed_num_workers_zero/s0_002_maskdino_bbox_seed123` | 11 | 144 KB | 失敗した run |
| `experiments/baselines/_failed_num_workers_zero/s0_003_maskdino_bbox_seed456` | 11 | 144 KB | 失敗した run |
| `experiments/baselines/_failed_num_workers_zero/s0_005_varifocanet_bbox_seed42` | 11 | 108 KB | 失敗した run |
| `experiments/baselines/_failed_num_workers_zero/s0_006_varifocanet_bbox_seed123` | 11 | 108 KB | 失敗した run |
| `experiments/baselines/_smoke_e3/s0_001_smoke_e3_seed42` | 20 | 188884 KB | 動作確認 |
| `experiments/baselines/_smoke_prior_simplehead/s0_001_maskdino_bbox_seed42` | 16 | 123268 KB | 動作確認 |
| `experiments/baselines/_smoke_prior_simplehead/s0_002_maskdino_bbox_seed123` | 16 | 123268 KB | 動作確認 |
| `experiments/baselines/_smoke_prior_simplehead/s0_003_maskdino_bbox_seed456` | 16 | 123268 KB | 動作確認 |
| `experiments/baselines/_smoke_prior_simplehead/s0_004_varifocanet_bbox_seed42` | 16 | 123268 KB | 動作確認 |
| `experiments/baselines/_smoke_prior_simplehead/s0_005_varifocanet_bbox_seed123` | 16 | 123268 KB | 動作確認 |
| `experiments/baselines/_smoke_prior_simplehead/s0_006_varifocanet_bbox_seed456` | 16 | 123268 KB | 動作確認 |
| `experiments/baselines/_smoke_v2_part3/s0_001_maskdino_bbox_seed42` | 20 | 186712 KB | 動作確認 |
| `experiments/baselines/_smoke_v2_part3/s0_002_maskdino_bbox_seed123` | 20 | 186712 KB | 動作確認 |
| `experiments/baselines/_smoke_v2_part3/s0_003_maskdino_bbox_seed456` | 20 | 186712 KB | 動作確認 |
| `experiments/baselines/_smoke_v2_part3/s0_004_varifocanet_bbox_seed42` | 20 | 128584 KB | 動作確認 |
| `experiments/baselines/_smoke_v2_part3/s0_005_varifocanet_bbox_seed123` | 20 | 128584 KB | 動作確認 |
| `experiments/baselines/_smoke_v2_part3/s0_006_varifocanet_bbox_seed456` | 20 | 128584 KB | 動作確認 |
| `experiments/phase0/_pre_redo_s0_smoke/s2_001_hand_detection_seed42` | 24 | 188660 KB | 動作確認 |
| `experiments/phase0/_pre_redo_s0_smoke/s2_002_hand_detection_seed123` | 24 | 188656 KB | 動作確認 |
| `experiments/phase0/_pre_redo_s0_smoke/s2_003_hand_detection_seed456` | 24 | 188656 KB | 動作確認 |
| `experiments/phase0/_pre_redo_s0_smoke/s3_001_phase_frame_seed42` | 6 | 28 KB | 動作確認 |
| `experiments/phase0/_pre_redo_s0_smoke/s3_002_phase_frame_seed123` | 6 | 28 KB | 動作確認 |
| `experiments/phase0/_pre_redo_s0_smoke/s3_003_phase_frame_seed456` | 6 | 28 KB | 動作確認 |
| `experiments/phase0/_prior_no_eval_recipe/s2_001_hand_detection_seed42` | 13 | 1972 KB | 置き換え済み |
| `experiments/phase0/_prior_no_eval_recipe/s2_002_hand_detection_seed123` | 13 | 1972 KB | 置き換え済み |
| `experiments/phase0/_prior_no_eval_recipe/s2_003_hand_detection_seed456` | 13 | 1972 KB | 置き換え済み |
| `experiments/phase0/_prior_no_eval_recipe/s3_001_phase_frame_seed42` | 6 | 28 KB | 置き換え済み |
| `experiments/phase0/_prior_no_eval_recipe/s3_002_phase_frame_seed123` | 6 | 28 KB | 置き換え済み |
| `experiments/phase0/_prior_no_eval_recipe/s3_003_phase_frame_seed456` | 6 | 28 KB | 置き換え済み |

### 分類の内訳

| 分類 | 索引の除外理由 | 件数 |
|---|---|---|
| 動作確認 | `smoke_test` | 19 |
| 置き換え済み | `superseded` | 6 |
| 失敗した run | `failed_run` | 5 |
| 中断した run | `aborted_run` | 4 |
| 計 | | 34 |

**全 34 件が版管理の追跡下に無いことを一件ずつ確認した。** 配下に追跡下のファイルを持つものも 0 件だった。

## 照合

| 項目 | 移動前 | 移動後 |
|---|---|---|
| ディレクトリ数 | 34 | 34 |
| 合計ファイル数 | 481 | 481 |
| 合計容量 | 2653644 KB | 2653644 KB |
| 合計バイト数 | 2715007414 | 2715007414 |

照合は 2 通りで行った。

1. ディレクトリ単位の `path` と `ファイル数` と `容量` の突き合わせ。差分なし。
2. 全 481 ファイルの `サイズ` と `相対経路` の突き合わせ。差分なし。

控えは退避先に残してある。

    ~/m2-archive/20260811/manifest_before.txt   ディレクトリ単位（移動前）
    ~/m2-archive/20260811/manifest_after.txt    ディレクトリ単位（移動後）
    ~/m2-archive/20260811/files_before.tsv      全ファイル（移動前）
    ~/m2-archive/20260811/files_after.tsv       全ファイル（移動後）
    ~/m2-archive/20260811/leftover_list.txt     退避対象の一覧

## 索引への影響

| 項目 | 退避前 | 退避後 |
|---|---|---|
| このホストで再生成した行数 | 785 | 751 |
| 統合先に記録されている行数 | 751 | 751 |
| 追跡外の経路を持つ行 | 34 | 0 |
| CSV 4 種の md5 が統合先と一致するか | 不一致 | 一致 |

**退避後、このホストが生成する索引は統合先のものと完全に一致する。**

## 元の場所に残ったもの

移動元の run ディレクトリは 34 件すべて消えたが、その親にあたる次の 8 ディレクトリは
**空のまま残している**。禁止事項「退避物を削除する（移動のみ）」に従い、削除していない。

    experiments/baselines/_aborted_codetr_no_config
    experiments/baselines/_aborted_s0_cuda_visible_misconfig
    experiments/baselines/_failed_num_workers_zero
    experiments/baselines/_smoke_e3
    experiments/baselines/_smoke_prior_simplehead
    experiments/baselines/_smoke_v2_part3
    experiments/phase0/_pre_redo_s0_smoke
    experiments/phase0/_prior_no_eval_recipe

空ディレクトリは版管理が追跡せず、収穫器も走査対象にしないため索引には現れない。
実測でも、退避後の再生成で追跡外の経路は 0 件だった。

## 戻す方法

退避先から元の相対経路へ戻す。repo の作業ディレクトリで実行する。

    cd /home/ubuntu/slocal2/m2
    ARC=~/m2-archive/20260811
    while read -r d; do
      mkdir -p "$(dirname "$d")"
      mv "$ARC/$d" "$d"
    done < "$ARC/leftover_list.txt"

戻した後は索引が 785 行に戻り、追跡外の経路が 34 件現れる。
**そのホストは索引の正本を作れなくなる**ため、戻す場合は正本を別ホストで生成すること。

一部だけ戻す場合は `leftover_list.txt` から該当行を抜き出して同じ手順を使う。

戻した結果の照合には `files_before.tsv` を使う。移動前の全ファイルのサイズと
相対経路が記録されているため、欠損の有無を機械的に確かめられる。

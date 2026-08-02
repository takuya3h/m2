# Relation-DETR スナップショット（efros）

- upstream: https://github.com/xiuqhou/Relation-DETR.git
- base commit: b485955c72452788240600da6d0f0b8cc49f33c7 (2024-11-24)
  ※ shallow clone (grafted) のため深い履歴は無い
- 取得日: 2026-08-02 / 取得ホスト: efros
- 取得時の m2 HEAD: b6b25e1 (exp/efros-wip-20260703)

## 内訳（実測値）

| ファイル | 内容 |
|---|---|
| `reldetr_upstream_mods.patch` | upstream 追跡ファイルへの改変 3 件（`optimizer/param_dict.py` / `transforms/presets.py` / `util/engine.py`）。265 行 |
| `reldetr_project_files.tar.gz` | 未追跡ファイル。実ファイル 43 件 |
| `file_list.txt` | `git status --porcelain` の未追跡エントリ 32 件（うち 2 件はディレクトリ） |
| `tar_contents.txt` | tarball に実際に含まれる 43 件の完全な一覧 |

tarball 43 件の内訳:

- **実装コード 31 件**
  - `configs/train_config_egosurgery*.py` 10 件
  - `configs/relation_detr/relation_detr_resnet50_egosurgery*.py` 11 件
    （`t1b` / `t1b_ca` / `t1b_camt` / `t1b_clsbias` / `t1b_hc` / `b1_mtl` /
    `hand2det` / `s0_frozen` / `s0_frozen_neck` / `lockeddown` / 無印）
  - `models/detectors/relation_detr_*.py` 8 件
    （`phaseclsbias` / `phasecrossattn` / `phasecrossattn_mt` / `phasefilm` /
    `phase_hc` / `handprior` / `b1_mtl` / `c5neck`）
  - `models/bricks/relation_decoder_phaseca.py` 1 件
  - `models/temporal/tecno_mirror.py` 1 件
- **出力データ 12 件**
  - `per_class_coco_map/epoch_0{00..11}.json`
    （実装コードではなく、ある検出 run の epoch 別 per-class COCO mAP。
    どの run に対応するかはこのスナップショットからは特定できない）

`models/temporal/__pycache__/tecno_mirror.cpython-311.pyc` は
ビルド生成物のため tarball から除外した。

## 何のための保全か

`third_party/` は `.gitignore:135-136` で除外され、`.gitmodules` も無く、
`.stglobalignore` でも同期対象外である。つまり **git にも Syncthing にも乗っていない**。
そのためこれらの実装は efros のディスク上にのみ存在していた。
t1b 系（phase→det）・b1_mtl（MTL baseline）・hand2det の実装が含まれ、
失われると再現も比較もできない。

なお、実験の証跡に含まれる `git_commit.txt` は m2 本体のコミットしか指さないため、
`third_party/` 配下のコード状態は証跡検査を構造的に素通りする。
`git merge-base --is-ancestor <git_commit.txt> HEAD` が通っても、
その run を動かした検出器コードが保全されている保証にはならない。

## 注意

これは**保全用スナップショットであり、正式な管理方法ではない**。
サブモジュール化 / `src/` への移設 / 別リポジトリ化のいずれにするかは、
全サーバーの報告が揃ってから決定する。
このスナップショットから直接ビルド・実行することを想定していない。

他サーバーにも改変がある場合に備え、ホスト名でディレクトリを分けている
（`third_party_snapshot/<hostname>/Relation-DETR/`）。
サーバー間で実装が異なっていた場合は、この単位で比較すること。

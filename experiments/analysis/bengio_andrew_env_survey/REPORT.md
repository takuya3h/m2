# bengio と andrew の環境の違い（T-2026-11-02-bengio-andrew-env-survey）

測定は 2026-11-02 11:16〜11:37 UTC（20:16〜20:37 JST）。andrew は読むだけで、bengio から ssh で命令を送り、結果は標準出力で受け取った（全件 `tasks/T-2026-11-02-bengio-andrew-env-survey/andrew_cmds.log`）。
**GPU は使っていない。** 基準は andrew（利用者の決定 2026-11-02）。表の「判定」は andrew と bengio が同じかどうかだけを言い、どちらが正しいかは問わない。
このファイルは手で書いた記述（`report_head.md`）と、JSON から生成した表（`report_tables.md`。`tasks/<id>/tools/make_tables.py`）をつなげたもの。

## 要約（揃える必要のある項目）

| 区分 | 違い | 量 |
|---|---|---|
| Relation-DETR 本体（bengio main） | andrew だけにあるファイル 15、中身が違うファイル 8。bengio だけにあるファイル 0 | andrew の版で 15 件 58,053 B と 8 件 50,902 B |
| 同・重ねの BODY（`~/slocal2/s2fix-bengio-body`） | andrew main と全 155 件一致。揃える材料に使える | — |
| MS-Deform-Attn のビルド物 | `.so`・`.o`・`build.ninja` の要約値が違う。bengio のものは重ねの BODY の `.cu` の経路で 2026-10-19 13:50 UTC にビルドされた（`build.ninja` の差は 27 行目の経路だけ） | — |
| 仮想環境のパッケージ | 差なし（二つとも、二通りの取り方で） | — |
| python の実体 | 両ホスト同じ uv の 3.11.16（sha256 2874a0b9…）。andrew の `.venv/pyvenv.cfg` の `home` だけが存在しない pyenv 3.11.4 を指す | — |
| データ（画像・注釈・manifest・分割・折り表・重み・塔の checkpoint） | 差なし | 揃える量 0 B |
| Stage 2 の材料 | andrew だけ 9 件（案 B の見取り 6 と地図 3）。案 A の信号 8 件は bengio では別の経路の写し（中身は同じ） | 13,497,919,828 B（bengio に無いもの） |
| 装置 | 電力の上限 300 W と 220 W（既定・最大はともに 300 W）。CPU 7950X 16C/32T と 3900X 12C/24T。メモリ 97,909,244 kB と 131,823,000 kB | — |
| IOMMU | andrew は有効の手がかり（群 32、`ivhd0`、GPU は群 13・24）。bengio は群 0・GPU の所属なし | — |

**揃えると失われる bengio の中身**: `main.py`（CRLF の改行の上流の原形。CR を除くと bengio 固有の行は 3 行で、いずれも andrew の版の機能を外した形）と `transforms/presets.py`（上流の原形。bengio 固有の行 0）。どちらも mtime が上流の展開の一括の時刻（2026-05-28 08:05:39）で、`third_party_snapshot/Bengio/` の tar に無い。
ほかの 6 件（configs の 5 件と `optimizer/param_dict.py`）は bengio の中身がその tar に同じ経路・同じ中身で在る。

## Task B — Relation-DETR の本体

要約値（`reldetr_digest.py`、§3.2 と同じ規則）。**§3.2 の記録と三つとも一致した（G2 通過）。**

| 場所 | source_files | source_tree_sha256 | all_files | all_tree_sha256 |
|---|---:|---|---:|---|
| andrew main | 142 | 2f08e5213cb5c377… | 155 | 20f15c061b435ce4… |
| bengio main | 127 | 3ade18f0709362fa… | 140 | 89dc93b4a82f1e06… |
| bengio 重ねの BODY | 142 | 2f08e5213cb5c377… | 155 | 20f15c061b435ce4… |

ファイル単位の三分類は表 B-1（下）。和集合 155 = andrew だけ 15 + bengio だけ 0 + 違う 8 + 同じ 132。除外した最上位は表 B-2、`checkpoints` の 12 件は表 B-3（両ホストで全件一致）。

学習の挙動に関わりうる違い（diff の全文は `b/diffs_bengio_vs_andrew.patch`。意味の解釈は書かない）:

| ファイル | andrew だけの行 | bengio だけの行 | 箇所 |
|---|---:|---:|---|
| `main.py` | 68（CR を除いて比べた値） | 3 | `parse_args`（`--convergence-schedule`・`--plateau-patience`・`--plateau-factor`・`--max-epochs`）、`train` の epoch の繰り返しと `lr_scheduler.step()` の条件、停滞判定と `convergence.json` の書き出し。import に `json`・`broadcast`・`util.convergence` |
| `util/convergence.py` | andrew だけのファイル（4,054 B） | — | `PlateauSchedule`（`main.py` が import する） |
| `transforms/presets.py` | 17 | 0 | 増強のプリセット `detr_1200` の追加（`detr` は同じ） |
| `optimizer/param_dict.py` | 56 | 0 | 最適化の群の関数 `finetune_hand2det` の追加 |
| `configs/train_config_egosurgery_seed{42,123,456}.py` | 13 | 1 | `output_dir` の決め方（andrew は `RELDETR_OUTPUT_DIR` と `EGO_BODY` を読む。bengio は `/tmp/reldetr_work_seed*` 固定） |
| `configs/train_config_egosurgery_s0_frozen{,_neck}.py` | 2 | 2 | 注釈の行の出力先の例だけ |
| andrew だけの configs 10 件と detectors 4 件 | — | — | 表 B-1。ImageNet 初期化の検出塔の設定 `train_config_egosurgery_stage1_imagenet_seed{42,123,456}.py`（2026-10-17）を含む |

## Task C — 二つの仮想環境

| 項目 | andrew | bengio |
|---|---|---|
| `.venv` のパッケージ（`importlib.metadata`「名前==版」の列） | 108、9020a519e653562f… | 108、9020a519e653562f…（差 0） |
| `.venv-relation-detr` の同 | 72、8f08a2457e681d6d… | 72、8f08a2457e681d6d…（差 0） |
| site-packages の dist-info 名の列（二つの venv、182 行） | 5fbdb86394d31bea… | 5fbdb86394d31bea…（同一） |
| `uv pip list --format freeze` の行 | 記録: `.venv` 108 行 9c7be5c9…、`.venv-relation-detr` 72 行 a74c9c78…（`tasks/T-2026-11-01-stage2-w23-andrew/audit.md` 68〜70 行。andrew では `uv pip` を回していない） | 実測: 108 行 9c7be5c99d6b768a…、72 行 a74c9c787e79f014… |
| `.venv/bin/python` の解決先 | uv `cpython-3.11.16-linux-x86_64-gnu/bin/python3.11` | 同じ |
| `.venv-relation-detr/bin/python` の解決先 | uv `cpython-3.11-linux-x86_64-gnu`（→ 3.11.16 への記号リンク）経由で同じ実体 | uv `cpython-3.11.16-...` を直接 |
| 実体の版・sha256 | 3.11.16、2874a0b9344d06b7…（21,740,000 B） | 3.11.16、2874a0b9344d06b7… |
| `.venv/pyvenv.cfg` の `home`・`version_info`・`uv` | `/home/ubuntu/.pyenv/versions/3.11.4/bin`（**存在しない**）・3.11.4・0.11.26 | uv の 3.11.16 の bin・3.11.4・0.11.15 |
| `.venv-relation-detr/pyvenv.cfg` の同 | uv `cpython-3.11-...` の bin・3.11・0.12.5 | uv `cpython-3.11.16-...` の bin・3.11.16・0.11.15 |
| uv の実体の置き場 `~/.local/share/uv/python/` | `cpython-3.11-linux-x86_64-gnu`（記号リンク）と `cpython-3.11.16-linux-x86_64-gnu` | 同じ構成 |
| uv（`~/.local/bin/uv`） | 0.12.5 | 0.12.5 |
| 非対話の ssh で `python3` | `/usr/bin/python3` 3.12.3（PATH に uv も venv も無い） | （対話シェル）`.venv/bin/python3` 3.11.16 |
| torch・torchvision | 2.1.2+cu118・0.16.2+cu118（二つの venv とも） | 同じ |
| torch が報告する CUDA・cuDNN・NCCL | 11.8・8700・2.18.6 | 同じ |
| MS-Deform-Attn の `.so`（`~/.cache/torch_extensions/py311_cu118/MultiScaleDeformableAttention/`） | 1,655,680 B、79b55a8ab270ed6d…、2026-10-13 19:48 UTC | 1,655,680 B、b16285382d085e2b…、2026-10-19 13:50 UTC |
| 同 `.o` | 2,423,632 B、966a3806518a4a80… | 2,423,984 B、508f845e1ee0d8c9… |
| 同 `build.ninja` | 2,706 B、f72b62a067a6540a…（`.cu` は `~/slocal2/m2/third_party/...`） | 2,721 B、7f066861a16ef4e2…（`.cu` は `~/slocal2/s2fix-bengio-body/third_party/...`） |
| 拡張の読み込み（装置を見せず、`.so` を直接読む） | 読めた（`ms_deform_attn_forward`・`_backward`）。CUDA は初期化されないまま | 同じ |

拡張の読み込みについて: 上流の `models/bricks/ms_deform_attn.py` は `torch.cuda.is_available()` が偽だと JIT の読み込みを試みない。装置を見せない形では上流の経路は試せないので、ビルド物の `.so` を `importlib` で直接読んだ。**上流の経路（`load()` によるビルドの要否の判定を含む）での読み込みは UNKNOWN。**

## Task D — データと checkpoint

集合の根拠（実装の行）:

| 項目 | 読む実装 | 既定値 |
|---|---|---|
| 検出塔の画像と注釈 | `third_party/Relation-DETR/configs/train_config_egosurgery.py` 28〜41 行（`EGO_ROOT`・`EGO_ANN_DIR`）、`scripts/run_stage1_dtower.sh` 44・59 行（`EGO_ANN_DIR=.../egosurgery_tool_folds/<折り>`） | `data/raw/ego`、`data/annotations/egosurgery_tool` |
| 検出塔の評価 | `scripts/eval_relation_detr_map.py` 45〜46・74〜75 行 | 同上（`instances_<split>.json`） |
| 検出塔の COCO の重み | `train_config_egosurgery.py` 52〜55 行（`RELDETR_COCO_CKPT`） | `data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth` |
| 検出塔の backbone の初期値（ImageNet の系統） | `models/backbones/resnet.py` 371・428〜432 行（`resnet50_v2` の URL を `load_checkpoint`） | torch hub の置き場 `~/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth` |
| 工程塔の manifest と画像 | `scripts/stage1_ptower.py` 70〜75 行（`cfg.manifest_dir`）、`scripts/stage1_ptower_r3.py` 62〜72 行（`image_path`） | `configs/stage1_ptower_r3.yaml` 38 行 `data/processed/phase_manifest`。塔の探索は `scripts/run_tower_search.py` 34 行 `data/processed/phase_manifest_all_phase` |
| 工程塔の折り | `scripts/stage1_ptower.py` 52〜67 行（`docs/stage0/A1_fold_table.md` と `data/splits/ego_{train,val,test}.txt`） | — |
| 工程塔の初期化 | `scripts/stage1_ptower_r3.py` 56 行（COCO の重み）、103 行（torchvision `ResNet50_Weights.IMAGENET1K_V1`） | `~/.cache/torch/hub/checkpoints/resnet50-0676ba61.pth` |
| 工程塔の二段目 | `scripts/stage1_ptower.py` 229〜236 行（`cfg.cache` の特徴の npz。一段目が作る） | 本契約は一段目が作る生成物として件数とバイト数だけ取った（表 D-3 の `stage1_features`） |
| 工程の注釈 | `experiments/analysis/dlsta_tower_feasibility/inputs_inventory.py` の `phase_rows`（`data/annotations/egosurgery_phase/*.csv`） | — |
| Stage 2 の予備測定 | w23 の二契約の材料の一覧（`experiments/analysis/stage2_w23_bengio/material/material_check.json` の 40 件、`experiments/analysis/stage2_w23_andrew/material/material.json` の 25 件、和集合 63 経路） | — |

画像（前例 `inputs_inventory.py` と同じ取り方）:

| 項目 | andrew | bengio | 記録 |
|---|---|---|---|
| B1 画像 01〜15（`data/raw/ego`、`other` を除く） | 15,437 枚、1,204,884,895 B、45ee4cc2e9ed72df… | 同じ | 15,437、45ee4cc2e9ed72df…（`tower_reselect_search_dlsta/inputs_inventory.json`）。動画ごとの 15 個も三者一致 |
| 固定記録 `image_input_lock.json` の 17,233 行（selected と counterpart の 32,670 経路） | 欠け 0、不一致 0、2,110,782,515 B | 欠け 0、不一致 0 | 各画像の sha256 |
| 工程の注釈 CSV | 43 件 545,778 B、01〜15 の行 17,233、工程注釈だけのフレーム 1,796 | 同じ（43 件すべて sha256 一致。git の blob も phase0 と一致） | 17,233・1,796（`conventions#frame_sets`） |

個別のファイル 101 件（manifest 8、術具注釈 3、折り 16、分割と折り表 4、重み 3、塔 4、Stage 2 の材料 63）は表 D-2。**Stage 2 の材料以外の 38 件は全件一致。**
版管理下の術具注釈 3 件・分割 3 件・折り表は、git の blob が phase0 の木と一致した（audit D-4）。
`data/raw/ego` の全体（表 D-3）は andrew が 1 件多く、その 1 件は `train/.DS_Store`（12,292 B）。

写す量（後続の実装契約の見積もり）: 塔と画像と注釈は 0 B。Stage 2 の材料のうち bengio に無いものは 9 件 13,497,919,828 B
（`T-2026-11-01-grasp-pilot-g/signals/views/B_*.json` 6 件 727,444 B、`signals/B/pred_CF_train_m.npy`・`signals/raw/all_{train,val}_m.npy` 3 件 13,497,192,384 B）。
案 A の信号 8 件（4,301,984 B）は bengio の `stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/` に同じ中身の写しがある（経路が違う）。
`T-2026-10-19-stage2-pilot-four-new-types/xq/missed_train.json` は bengio だけにある（版管理下の写し `experiments/analysis/stage2_pilot_four/xq/missed_train.json` と同じ中身、c312323d…）。

## Task E — 前の契約の残り物（bengio）

定義どおり（bengio の範囲にあり、phase0 の木に無く、andrew の同じ相対経路に無いもの）に集合で取った。全件は `e/leftovers_repo_00.json`（repo）と `e/leftovers_other.json`（それ以外と git の管理情報）。

| 範囲 | 件数 | 内訳 |
|---|---:|---|
| repo の作業ツリー（無視されたものを含む、`.git` と本契約の出力を除く） | 393 | 表 E-1（最上位ごと）、表 E-2（experiments 以外の全 386 件）、表 E-3（experiments の 7 件） |
| `~/slocal2` 直下 | 14 | 表 E-4 |
| 家の直下 | 9 | 表 E-4 |
| `/tmp` 直下の自分のもの | 514 | 表 E-5（名前の型ごと） |
| worktree（bengio だけ） | 3 | `~/slocal2/m2-four`（`feat/stage2-pilot-four-new-types`、792527a7）、`~/slocal2/m2-s2fix-bengio`（`feat/stage2-pilot-fix-epoch4-shuffle-bengio`、78f8260b）、別のセッションの scratchpad の `wt_phase0`（detached、67c4cc44） |
| `.git/info/exclude` の行（bengio だけ） | 5 | `experiments/analysis/frame_signal_audit/`、`experiments/analysis/stage2_pilot_folda/`、`experiments/phase1/stage2pilot_*/`、`experiments/phase1/stage2fix_pd_P1-W1_shuffle_ep4_seed42_smoke/logs/{eval_meta_val,val_metrics_by_epoch}.json` |
| 上流の無い手元の分岐（bengio だけ） | 1 | `chore/evidence-map-a-place-start` |

`~/slocal2/stage2pilot_store` は andrew にも同じ名前があるので定義の (2) で外れる。二段目まで比べると bengio だけにあるのは
`T-2026-11-01-grasp-pilot-d/`（18,137,294,352 B、287 ファイル）、`T-2026-11-01-stage2-w23-bengio/`（3,248,788,205 B、737 ファイル）、
`T-2026-10-19-stage2-pilot-four-new-types/{dp_ckpt,k3,xq,xq_contrib}`（1,861,033・134,930・86,535,909・176,296,316 B）。

参照しているもの（機械で埋めた記号リンクの先のほか）:

- `~/slocal2/s2fix-bengio-body` は `.venv`・`.venv-relation-detr`・`data`・`experiments` を `~/slocal2/m2` への記号リンクで持つ。**bengio の MS-Deform-Attn のビルド物（`~/.cache/torch_extensions/.../build.ninja` 27 行目）がこの BODY の `.cu` を指す**
- `~/slocal2/m2-four` は worktree として `.git/worktrees` に登録され、`.venv`・`data/processed/phase_manifest`・`data/eval_staging/egosurgery_val/val2017` を `~/slocal2/m2` への記号リンクで持つ
- 走っているプロセスで、cwd がこれらの置き場にあるものは 0 件（`/proc/*/cwd` を読んだ）

§3.3 の手がかりの行方:

| 手がかり | 一覧に載ったか |
|---|---|
| 記号リンク `.venv` と `data/processed/phase_manifest`（worktree に足した） | 載った（`~/slocal2/m2-four` の中。worktree ごと `~/slocal2` 直下の残り物） |
| 前回・直しの契約の保存先の bengio の写し（32 本） | 定義の (2) で外れた（`~/slocal2/stage2pilot_store` が andrew にもある）。二段目の差は上の段落 |
| `.git/info/exclude` に足した 3 経路と控え `~/m2-git-info-exclude.bak-20261019` | 載った（除外の行は bengio だけの 5 行の中、控えは家の直下） |
| 仮想環境を uv の 3.11.16 に向け直したまま | 向け直しの控えが載った（`.venv-relation-detr/pyvenv.cfg.before_s2fix`、`/tmp/pyvenv.cfg.bak`）。向け先は andrew と同じ uv の 3.11.16 の実体で、Task C の差はない |
| worktree `~/slocal2/m2-four`、重ねの BODY `~/slocal2/s2fix-bengio-body`、保存先 `~/slocal2/stage2pilot_store` | 前の二つは載った。保存先は (2) で外れた |
| `/tmp/sp.txt` | 載らなかった。**既に無い**（`ls` と `find /tmp -maxdepth 1 -name sp.txt` の二通りで 0） |

陽性対照と陰性対照: andrew にもある既知のファイル `README.md` は一覧に出ない。既知の残り物 `~/m2-git-info-exclude.bak-20261019` は一覧に出る。

同期の欄: repo の `.stignore`（phase0 の `.stglobalignore` と同一）を近似で照合した結果、repo の残り物 393 件はすべて「渡らない」。家の直下の残り物 9 件は Syncthing のフォルダ（`~/.claude`・`~/.codex`・`~/.agents`・`~/claude-sync`）の外。
同期の途中で片方にだけあるもの: 同期の対象に当たる残り物が 0 件なので、この欄に入るものは無い。

## Task F — 装置と系の設定（11:29:39〜40 UTC、両ホストとも GPU は無負荷・P8・使用率 0%）

| 項目 | andrew | bengio |
|---|---|---|
| GPU の型 | NVIDIA RTX A6000 × 2 | NVIDIA RTX A6000 × 2 |
| UUID | 0: GPU-06de23a6-117b-46f2-427c-002409cf5a05、1: GPU-07e03d7e-7920-b988-01b6-02389e69294c | 0: GPU-1b153400-9ec9-25fe-d601-7ddc39431aad、1: GPU-525aae08-a3e0-1148-1887-8e541011ba04 |
| PCI の bus id | 01:00.0、17:00.0 | 03:00.0、0D:00.0 |
| VBIOS・driver・NVML | 94.02.5C.00.02・595.84・595.84（CUDA Version 13.2） | 同じ |
| メモリ | 49,140 MiB | 49,140 MiB |
| 電力の上限 現在値（enforced） | **300.00 W**（300.00 W） | **220.00 W**（220.00 W） |
| 電力の上限 既定値・最大値・最小値 | 300.00・300.00・100.00 W | 300.00・300.00・100.00 W |
| 最大クロック SM・メモリ | 2,100・8,001 MHz | 2,100・8,001 MHz |
| 永続モード・ECC（現在・保留） | Disabled・Disabled・Disabled | 同じ |
| PCIe の世代 現在・最大（GPU 側・ホスト側） | 1・4（4・5） | 1・4（4・4） |
| PCIe の幅 現在・最大 | GPU0 16・16、GPU1 4・16 | GPU0 4・16、GPU1 16・16 |
| GPU 間の接続（`topo -m`） | PHB | PHB |
| CPU の親和性・NUMA | 0-31・NUMA 0（GPU の numa_node は -1） | 0-23・NUMA 0（同 -1） |
| IOMMU | `/sys/kernel/iommu_groups` 32 群、`/sys/class/iommu` に `ivhd0`、GPU は群 13・24 | 0 群、`/sys/class/iommu` 空、GPU の `iommu_group` 無し |
| kernel の起動引数 | `iommu` の指定なし | `iommu` の指定なし |
| CPU | AMD Ryzen 9 7950X 16-Core、論理 32（16 コア × 2） | AMD Ryzen 9 3900X 12-Core、論理 24（12 コア × 2） |
| メモリ（MemTotal）・swap | 97,909,244 kB・2,097,148 kB | 131,823,000 kB・2,097,148 kB |
| cgroup の上限 memory.max・cpu.max・pids.max | 89,120,571,392・max 100000・max | 123,480,309,760・max 100000・max |
| 容器 | docker（`/.dockerenv` あり） | docker（同） |
| repo と data の file system | ext4 `/dev/sdc1[/tuchihashi]`、総量 7,937,302,376,448 B、空き 1,645,381,390,336 B | ext4 `/dev/sdb1[/tuchihashi]`、総量 7,937,302,376,448 B、空き 1,415,041,777,664 B |
| 家と `/tmp`（overlay） | 総量 2,014,574,526,464 B、空き 1,505,323,528,192 B | 総量 1,967,317,549,056 B、空き 1,400,596,619,264 B |
| kernel・OS | 6.8.0-138-generic・Ubuntu 24.04.4 LTS | 同じ |
| nvcc・gcc | 12.9（V12.9.86）・13.3.0 | 同じ |
| OS 側の cuDNN・NCCL（`ldconfig`） | `libcudnn.so.9`・`libnccl.so.2`（`/lib/x86_64-linux-gnu`） | 同じ |

PCIe の世代と幅は無負荷で測った（P8）。世代の現在値 1 は省電力で下がった値の可能性がある。幅の現在値は負荷をかけた値ではない。
存在しない GPU の番号（7）を同じ問い合わせで指定すると、両ホストとも `No devices were found`・終了コード 6 になった。

## 試験（Task F-5・F-6）

bengio（本契約の起点 231c280e、`CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors`）:
`11 failed, 965 passed, 5 skipped, 26 warnings, 1 error`。失敗と収集の失敗の名前 12 件は、w23-bengio の開始時の記録と同じ集合。
andrew: 試験は `/tmp` に一時ディレクトリを作るため回していない。直近の記録（`tasks/T-2026-11-01-stage2-w23-andrew/audit.md` 59〜66 行と 302〜304 行、andrew の当時の分岐の起点）の 6 件を使った。

| 名前 | andrew | bengio | Relation-DETR の違いとの結び付き |
|---|---|---|---|
| `tests/test_stage1_dtower_convergence.py`（収集の失敗） | — | 収集の失敗 | **結び付く。** `FileNotFoundError: .../third_party/Relation-DETR/util/convergence.py`。このファイルは andrew だけにある（表 B-1） |
| `tests/test_check_spec.py::test_teacher_detection_rate` | — | 失敗 | 結び付かない。Relation-DETR を読まない。試験の文書が「期待値を hostname から計算する」と書く（`tests/test_check_spec.py` 370〜371 行）。`assert 14 == 15` |
| `tests/test_stage1_ptower_heads.py::test_existing_candidates_match_baseline[A]`・`[B]`・`[C]`・`[linear]` | — | 失敗 | 結び付かない。Relation-DETR を読まない。CPU 4 スレッドの出力の sha256 を固定値と比べる（同 29〜55 行）。CPU の型の違い（Task F）との関係は測っていない |
| `test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics`、`test_fetch_task.py::test_rejects_unknown_file_name`、`test_research_logger.py` の 4 件 | 失敗 | 失敗 | 両ホスト共通 |

## 表 B-1 Relation-DETR のファイル単位の三分類（andrew main を基準、bengio main と比べる）

| 分類 | 経路 | andrew バイト | bengio バイト | bengio の中身が third_party_snapshot/Bengio の tar に在るか |
|---|---|---:|---:|---|
| andrew_only | `configs/relation_detr/relation_detr_resnet50_egosurgery_hand2det.py` | 4331 | — | —（bengio に無い） |
| andrew_only | `configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_camt.py` | 4120 | — | —（bengio に無い） |
| andrew_only | `configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_clsbias.py` | 4248 | — | —（bengio に無い） |
| andrew_only | `configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_hc.py` | 4834 | — | —（bengio に無い） |
| andrew_only | `configs/train_config_egosurgery_seed42_augstrong.py` | 2937 | — | —（bengio に無い） |
| andrew_only | `configs/train_config_egosurgery_seed42_augstrong_hires.py` | 2904 | — | —（bengio に無い） |
| andrew_only | `configs/train_config_egosurgery_seed42_hires.py` | 2865 | — | —（bengio に無い） |
| andrew_only | `configs/train_config_egosurgery_stage1_imagenet_seed123.py` | 3390 | — | —（bengio に無い） |
| andrew_only | `configs/train_config_egosurgery_stage1_imagenet_seed42.py` | 3389 | — | —（bengio に無い） |
| andrew_only | `configs/train_config_egosurgery_stage1_imagenet_seed456.py` | 3390 | — | —（bengio に無い） |
| andrew_only | `models/detectors/relation_detr_handprior.py` | 6818 | — | —（bengio に無い） |
| andrew_only | `models/detectors/relation_detr_phase_hc.py` | 3987 | — | —（bengio に無い） |
| andrew_only | `models/detectors/relation_detr_phaseclsbias.py` | 3130 | — | —（bengio に無い） |
| andrew_only | `models/detectors/relation_detr_phasecrossattn_mt.py` | 3656 | — | —（bengio に無い） |
| andrew_only | `util/convergence.py` | 4054 | — | —（bengio に無い） |
| differ | `configs/train_config_egosurgery_s0_frozen.py` | 1966 | 1934 | 在る（同じ経路・同じ中身） |
| differ | `configs/train_config_egosurgery_s0_frozen_neck.py` | 2413 | 2381 | 在る（同じ経路・同じ中身） |
| differ | `configs/train_config_egosurgery_seed123.py` | 3230 | 2729 | 在る（同じ経路・同じ中身） |
| differ | `configs/train_config_egosurgery_seed42.py` | 3229 | 2728 | 在る（同じ経路・同じ中身） |
| differ | `configs/train_config_egosurgery_seed456.py` | 3230 | 2729 | 在る（同じ経路・同じ中身） |
| differ | `main.py` | 12809 | 9337 | **無い（揃えると失われる中身）** |
| differ | `optimizer/param_dict.py` | 12839 | 10204 | 在る（同じ経路・同じ中身） |
| differ | `transforms/presets.py` | 11186 | 10407 | **無い（揃えると失われる中身）** |

件数: andrew 155、bengio 140、和集合 155 = andrew だけ 15 + bengio だけ 0 + 中身が違う 8 + 同じ 132。
重ねの BODY と andrew main: andrew だけ 0、BODY だけ 0、違う 0、同じ 155。

## 表 B-2 除外した最上位（件数・バイト数）

| 最上位 | andrew | bengio main | bengio 重ねの BODY |
|---|---|---|---|
| `.git` | 28 件 757399 B | 無い | 無い |
| `__pycache__` | 71 件 1240933 B | 72 件 1229233 B | 69 件 1220182 B |
| `checkpoints` | 12 件 2149639562 B | 12 件 2149639562 B | 無い |
| `experiments` | 1 件 1762 B | 無い | 無い |
| `per_class_coco_map` | 22 件 13948 B | 無い | 15 件 9490 B |
| `third_party` | 25 件 2235383808 B | 25 件 2235383808 B | 無い |

## 表 B-3 除外した最上位 `checkpoints` のファイル（両ホスト）

| 経路 | andrew バイト | andrew sha256 | bengio バイト | bengio sha256 | 判定 |
|---|---:|---|---:|---|---|
| `checkpoints/incoming/seed123/best_ap.pth` | 195421066 | bb01eb27385d4fd9… | 195421066 | bb01eb27385d4fd9… | 一致 |
| `checkpoints/incoming/seed42/best_ap.pth` | 195421066 | 03936318f9d45ac9… | 195421066 | 03936318f9d45ac9… | 一致 |
| `checkpoints/incoming/seed456/best_ap.pth` | 195421066 | f0204ae9843e0529… | 195421066 | f0204ae9843e0529… | 一致 |
| `checkpoints/relation_detr_resnet50_egosurgery/train/2026-05-30-04_24_20/best_ap.pth` | 195421066 | 5992c5ee518de62b… | 195421066 | 5992c5ee518de62b… | 一致 |
| `checkpoints/relation_detr_resnet50_egosurgery/train/2026-05-30-04_24_20/best_ap50.pth` | 195422778 | f9dabee44638b262… | 195422778 | f9dabee44638b262… | 一致 |
| `checkpoints/relation_detr_resnet50_egosurgery/train/2026-05-30-04_24_20/checkpoints/checkpoint_0/scaler.pt` | 988 | b8e23a14af81a4a4… | 988 | b8e23a14af81a4a4… | 一致 |
| `checkpoints/relation_detr_resnet50_egosurgery/train/seed123/best_ap.pth` | 195421066 | bb01eb27385d4fd9… | 195421066 | bb01eb27385d4fd9… | 一致 |
| `checkpoints/relation_detr_resnet50_egosurgery/train/seed123/best_ap50.pth` | 195422778 | d5d2dee55d7a9879… | 195422778 | d5d2dee55d7a9879… | 一致 |
| `checkpoints/relation_detr_resnet50_egosurgery/train/seed42/best_ap.pth` | 195421066 | 03936318f9d45ac9… | 195421066 | 03936318f9d45ac9… | 一致 |
| `checkpoints/relation_detr_resnet50_egosurgery/train/seed42/best_ap50.pth` | 195422778 | 430e6d247822437a… | 195422778 | 430e6d247822437a… | 一致 |
| `checkpoints/relation_detr_resnet50_egosurgery/train/seed456/best_ap.pth` | 195421066 | f0204ae9843e0529… | 195421066 | f0204ae9843e0529… | 一致 |
| `checkpoints/relation_detr_resnet50_egosurgery/train/seed456/best_ap50.pth` | 195422778 | fd4cf4fbc01f2bcd… | 195422778 | fd4cf4fbc01f2bcd… | 一致 |

## 表 D-2 個別のファイル（両ホスト。sha256 は先頭 16 桁、全桁は `d/data_compare.json`）

| 群 | 経路 | andrew バイト | andrew sha256 | bengio バイト | bengio sha256 | 判定 |
|---|---|---:|---|---:|---|---|
| manifest | `~/slocal2/m2/data/processed/phase_manifest/train.json` | 1068981 | f8bee9f9b4651add | 1068981 | f8bee9f9b4651add | 一致 |
| manifest | `~/slocal2/m2/data/processed/phase_manifest/val.json` | 164386 | 9f935375a093024a | 164386 | 9f935375a093024a | 一致 |
| manifest | `~/slocal2/m2/data/processed/phase_manifest/test.json` | 465823 | f2077541feb0b3c9 | 465823 | f2077541feb0b3c9 | 一致 |
| manifest | `~/slocal2/m2/data/processed/phase_manifest/phase_vocab.json` | 164 | ad3c1e4a4b0913bc | 164 | ad3c1e4a4b0913bc | 一致 |
| manifest | `~/slocal2/m2/data/processed/phase_manifest_all_phase/train.json` | 1204959 | 0d25c99f97df63c2 | 1204959 | 0d25c99f97df63c2 | 一致 |
| manifest | `~/slocal2/m2/data/processed/phase_manifest_all_phase/val.json` | 221723 | fe3da175937033d8 | 221723 | fe3da175937033d8 | 一致 |
| manifest | `~/slocal2/m2/data/processed/phase_manifest_all_phase/test.json` | 536860 | 4525bfac4b4a6be1 | 536860 | 4525bfac4b4a6be1 | 一致 |
| manifest | `~/slocal2/m2/data/processed/phase_manifest_all_phase/phase_vocab.json` | 164 | ad3c1e4a4b0913bc | 164 | ad3c1e4a4b0913bc | 一致 |
| tool_ann | `~/slocal2/m2/data/annotations/egosurgery_tool/instances_train.json` | 14801507 | fc63621ea496ccdc | 14801507 | fc63621ea496ccdc | 一致 |
| tool_ann | `~/slocal2/m2/data/annotations/egosurgery_tool/instances_val.json` | 2184273 | db605c06626ff824 | 2184273 | db605c06626ff824 | 一致 |
| tool_ann | `~/slocal2/m2/data/annotations/egosurgery_tool/instances_test.json` | 5943287 | f4ce5243fd01fc6e | 5943287 | f4ce5243fd01fc6e | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/A/instances_train.json` | 14801507 | fc63621ea496ccdc | 14801507 | fc63621ea496ccdc | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/A/instances_val.json` | 2184273 | db605c06626ff824 | 2184273 | db605c06626ff824 | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/A/instances_test.json` | 5943287 | f4ce5243fd01fc6e | 5943287 | f4ce5243fd01fc6e | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/B/instances_train.json` | 7503332 | 6a4b2d1e9ca209f2 | 7503332 | 6a4b2d1e9ca209f2 | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/B/instances_val.json` | 1256005 | cdc0c5a73eedd6ad | 1256005 | cdc0c5a73eedd6ad | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/B/instances_test.json` | 3162280 | 94a54dd492ab78db | 3162280 | 94a54dd492ab78db | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/C/instances_train.json` | 8358151 | 9a30b9a8e902cee0 | 8358151 | 9a30b9a8e902cee0 | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/C/instances_val.json` | 1726523 | 9e8bdc2e501acfe8 | 1726523 | 9e8bdc2e501acfe8 | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/C/instances_test.json` | 1839413 | 86423dc6ac487fb9 | 1839413 | 86423dc6ac487fb9 | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/D/instances_train.json` | 8291581 | a4caac8e78d6db2d | 8291581 | a4caac8e78d6db2d | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/D/instances_val.json` | 1540508 | 2108db7904f728bb | 1540508 | 2108db7904f728bb | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/D/instances_test.json` | 2087925 | 04574e9d56b4faa4 | 2087925 | 04574e9d56b4faa4 | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/E/instances_train.json` | 8268140 | e7da2a9351188cf5 | 8268140 | e7da2a9351188cf5 | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/E/instances_val.json` | 1962795 | d2701bea92190601 | 1962795 | d2701bea92190601 | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/E/instances_test.json` | 1694043 | 57b052da3ec8249d | 1694043 | 57b052da3ec8249d | 一致 |
| tool_folds | `~/slocal2/m2/data/annotations/egosurgery_tool_folds/fold_report.json` | 8554 | f3560e7cd3464c72 | 8554 | f3560e7cd3464c72 | 一致 |
| splits | `~/slocal2/m2/data/splits/ego_train.txt` | 30 | c28816de94c5ed83 | 30 | c28816de94c5ed83 | 一致 |
| splits | `~/slocal2/m2/data/splits/ego_val.txt` | 6 | f1bc456a0439b606 | 6 | f1bc456a0439b606 | 一致 |
| splits | `~/slocal2/m2/data/splits/ego_test.txt` | 9 | 7edeab6294574cfd | 9 | 7edeab6294574cfd | 一致 |
| splits | `~/slocal2/m2/docs/stage0/A1_fold_table.md` | 7987 | 883a1bf08f42c797 | 7987 | 883a1bf08f42c797 | 一致 |
| weights | `~/slocal2/m2/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth` | 196140106 | 2d2c19a7a49e7d77 | 196140106 | 2d2c19a7a49e7d77 | 一致 |
| weights | `~/.cache/torch/hub/checkpoints/resnet50-0676ba61.pth` | 102530333 | 0676ba61b6795bbe | 102530333 | 0676ba61b6795bbe | 一致 |
| weights | `~/.cache/torch/hub/checkpoints/resnet50-11ad3fa6.pth` | 102540417 | 11ad3fa62ca79e40 | 102540417 | 11ad3fa62ca79e40 | 一致 |
| towers | `~/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth` | 195421066 | 30d199b15201cf3c | 195421066 | 30d199b15201cf3c | 一致 |
| towers | `~/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldB_seed42/work/best_ap.pth` | 195421066 | be84c64bea271eae | 195421066 | be84c64bea271eae | 一致 |
| towers | `~/slocal2/m2/experiments/phase1/stage1_ptower_r3_005_ft_coco_lr0.0001_foldA_seed42/checkpoints/best.pth` | 94405478 | a90cf04de88fcd02 | 94405478 | a90cf04de88fcd02 | 一致 |
| towers | `~/slocal2/m2/experiments/phase1/stage1_ptower_r3_008_ft_coco_lr0.0001_foldB_seed42/checkpoints/best.pth` | 94405478 | 835d556855a4cd8c | 94405478 | 835d556855a4cd8c | 一致 |
| stage2 | `~/slocal2/m2/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth` | 195421066 | 30d199b15201cf3c | 195421066 | 30d199b15201cf3c | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/arms/PD/gtpred_CF_train.npz` | 1043462 | 6b0e99369b350caf | 1043462 | 6b0e99369b350caf | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/arms/PD/gtpred_noCF_val.npz` | 164126 | 5fe0a89c8402f455 | 164126 | 5fe0a89c8402f455 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/efros_ptower/data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz` | 127016156 | c402e214d28d32c6 | 127016156 | c402e214d28d32c6 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/efros_ptower/experiments/phase1/stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42/checkpoints/best.pth` | 1610970 | 0d76d446796f855a | 1610970 | 0d76d446796f855a | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/cf/D0-INST-UQ_train.npz` | 117197858 | 603a1ef90dbb8af2 | 117197858 | 603a1ef90dbb8af2 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/cf/D0-RT_train.npz` | 148679678 | d4cb0a79874032f9 | 148679678 | d4cb0a79874032f9 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/cf/D0_train.npz` | 927578 | fdbf285bc9278e8a | 927578 | fdbf285bc9278e8a | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/cf/P0_train.npz` | 695810 | e7b23991bce769ab | 695810 | e7b23991bce769ab | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D-GT-INST_train.npz` | 8498908 | 12e308efb6cef730 | 8498908 | 12e308efb6cef730 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D-GT-INST_val.npz` | 1333948 | 590a72d47bf220c1 | 1333948 | 590a72d47bf220c1 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D-GT_train.npz` | 927578 | 058a9a82d3edfb89 | 927578 | 058a9a82d3edfb89 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D-GT_val.npz` | 145946 | 3e81cb221c074c7d | 145946 | 3e81cb221c074c7d | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D0-INST-UQ_train.npz` | 117197858 | 7624d3c86cf2a4a8 | 117197858 | 7624d3c86cf2a4a8 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D0-INST-UQ_val.npz` | 18386546 | 3a090681fcbbbb43 | 18386546 | 3a090681fcbbbb43 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D0-RT_train.npz` | 148679678 | 9892e3e236abdbd5 | 148679678 | 9892e3e236abdbd5 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D0-RT_val.npz` | 23325446 | 259ff024f6d7cf45 | 23325446 | 259ff024f6d7cf45 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D0_train.npz` | 927578 | cdecdb958fd97d0a | 927578 | cdecdb958fd97d0a | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/D0_val.npz` | 145946 | 4403d1fed34e3115 | 145946 | 4403d1fed34e3115 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P-GT_train.npz` | 695810 | 6cb729a9724efdf5 | 695810 | 6cb729a9724efdf5 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P-GT_val.npz` | 109586 | d21a3cf09246aece | 109586 | d21a3cf09246aece | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P0_train.npz` | 695810 | e58308d39813b490 | 695810 | e58308d39813b490 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/signals/final/P0_val.npz` | 109586 | 082387a092fe456d | 109586 | 082387a092fe456d | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/D0-INST-UQ_train.npz` | 117197858 | 534360a1afeba620 | 117197858 | 534360a1afeba620 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/D0-INST-UQ_val.npz` | 18386546 | e010ba9bf3de861b | 18386546 | e010ba9bf3de861b | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/D0-RT_train.npz` | 148679678 | 902e1ef1921a7811 | 148679678 | 902e1ef1921a7811 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/D0-RT_val.npz` | 23325446 | 7712b191a7d2ca92 | 23325446 | 7712b191a7d2ca92 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/D0_train.npz` | 927578 | 3db75c460cbffef5 | 927578 | 3db75c460cbffef5 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/D0_val.npz` | 145946 | ee6c21da462bf4ad | 145946 | ee6c21da462bf4ad | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/P0_train.npz` | 695810 | 09814ab2f51153a8 | 695810 | 09814ab2f51153a8 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/signals/shuffle/P0_val.npz` | 109586 | 9ffc4e4d84a43010 | 109586 | 9ffc4e4d84a43010 | 一致 |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types/xq/missed_train.json` | 無い | — | 5930 | c312323d6decfc0e | bengio だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe/signals/g_train.npz` | 928564 | 741cecb5d42decd7 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-probe/signals/g_train.npz` | 無い | — | 928564 | 741cecb5d42decd7 | bengio だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe/signals/g_val.npz` | 146932 | 235e2c2bde3a0478 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-probe/signals/g_val.npz` | 無い | — | 146932 | 235e2c2bde3a0478 | bengio だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/A/g_pred_CF_train.npz` | 928564 | ed086f44877f8097 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-g/signals/A/g_pred_CF_train.npz` | 無い | — | 928564 | ed086f44877f8097 | bengio だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/A/g_pred_CF_val.npz` | 146932 | 616121b2a18b5899 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-g/signals/A/g_pred_CF_val.npz` | 無い | — | 146932 | 616121b2a18b5899 | bengio だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/A/g_pred_noCF_train.npz` | 928564 | ddc41ea5243e5abe | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-g/signals/A/g_pred_noCF_train.npz` | 無い | — | 928564 | ddc41ea5243e5abe | bengio だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/A/g_pred_noCF_val.npz` | 146932 | 616121b2a18b5899 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-g/signals/A/g_pred_noCF_val.npz` | 無い | — | 146932 | 616121b2a18b5899 | bengio だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/A/g_shuffle_train.npz` | 928564 | 3138ea720b813dbb | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-g/signals/A/g_shuffle_train.npz` | 無い | — | 928564 | 3138ea720b813dbb | bengio だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/A/g_shuffle_val.npz` | 146932 | d92f029f1d9c3329 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio/copied/grasp-pilot-g/signals/A/g_shuffle_val.npz` | 無い | — | 146932 | d92f029f1d9c3329 | bengio だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/views/B_pred_noCF_train.json` | 125756 | 033c27db2a3d88df | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/views/B_pred_noCF_val.json` | 19906 | 104f7ae0dd7cc344 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/views/B_pred_CF_train.json` | 125756 | b57ee6282d10d1a5 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/views/B_pred_CF_val.json` | 19904 | c5122560249e6901 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/views/B_shuffle_train.json` | 376832 | c229a9a455d4c0d8 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/views/B_shuffle_val.json` | 59290 | 5f3bcfded7d883f4 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/B/pred_CF_train_m.npy` | 6257736128 | c55cbfd781f9da2e | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/raw/all_train_m.npy` | 6257736128 | 10577ab898a812f1 | 無い | — | andrew だけ |
| stage2 | `~/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/raw/all_val_m.npy` | 981720128 | 911951dbf273966a | 無い | — | andrew だけ |
| stage2 | `~/slocal2/m2/data/annotations/egosurgery_hts/hand_tool_seg/train.json` | 94917937 | 8d36e75d6fe23ed5 | 94917937 | 8d36e75d6fe23ed5 | 一致 |
| stage2 | `~/slocal2/m2/data/annotations/egosurgery_hts/hand_tool_seg/val.json` | 16325511 | 0c61c3ea383449af | 16325511 | 0c61c3ea383449af | 一致 |
| stage2 | `~/slocal2/m2/data/annotations/egosurgery_hts/hand_seg/train.json` | 82782614 | 265c64d10f78e6fa | 82782614 | 265c64d10f78e6fa | 一致 |
| stage2 | `~/slocal2/m2/data/annotations/egosurgery_hts/hand_seg/val.json` | 15300013 | d07e9cf3ae2a58bb | 15300013 | d07e9cf3ae2a58bb | 一致 |
| stage2 | `~/slocal2/m2/data/annotations/egosurgery_hts/tool_seg/train.json` | 46859122 | 3863a41f9893dad3 | 46859122 | 3863a41f9893dad3 | 一致 |
| stage2 | `~/slocal2/m2/data/annotations/egosurgery_hts/tool_seg/val.json` | 6178686 | 8672005bd10d115c | 6178686 | 8672005bd10d115c | 一致 |

## 表 D-3 ディレクトリ単位（件数・バイト数。中身の要約値は取っていない）

| 経路 | andrew | bengio |
|---|---|---|
| `data/raw/ego` | 25902 件 4079420974 B | 25901 件 4079408682 B |
| `data/raw/OpenSurgery_Dataset/01_frames/initial_videos` | 27535 件 1450711807 B | 27535 件 1450711807 B |
| `data/processed/stage1_features` | 154 件 9810030144 B | 154 件 9810030144 B |
| `data/annotations/egosurgery_hts` | 21 件 409499407 B | 21 件 409499407 B |
| `data/annotations/egosurgery_tool_folds` | 16 件 70628317 B | 16 件 70628317 B |
| `data/processed/phase_manifest` | 4 件 1699354 B | 4 件 1699354 B |
| `data/processed/phase_manifest_all_phase` | 4 件 1963706 B | 4 件 1963706 B |

## 表 E-1 repo の作業ツリーの残り物（最上位ごと。experiments は二段目まで）

| 最上位 | 件数 | バイト数（ファイルの合計） | 同期の対象（近似） |
|---|---:|---:|---:|
| `.codegraph` | 2 | 4791400 | 0 |
| `.remember` | 12 | 4302 | 0 |
| `.ruff_cache` | 4 | 764 | 0 |
| `.venv` | 188 | 4047547 | 0 |
| `.venv-relation-detr` | 4 | 5755 | 0 |
| `configs` | 1 | 4476 | 0 |
| `data` | 61 | 0 | 0 |
| `experiments/baselines` | 6 | 9706 | 0 |
| `experiments/phase1` | 1 | 0 | 0 |
| `node_modules` | 72 | 151158556 | 0 |
| `package-lock.json` | 1 | 705 | 0 |
| `package.json` | 1 | 73 | 0 |
| `scripts` | 5 | 112955 | 0 |
| `src` | 18 | 111248 | 0 |
| `tasks` | 2 | 51337 | 0 |
| `tests` | 1 | 14733 | 0 |
| `third_party` | 4 | 17523 | 0 |
| `tools` | 1 | 30263 | 0 |
| `wandb` | 9 | 22672 | 0 |
| 計 | 393 | 160384015 | 0 |

## 表 E-2 repo の作業ツリーの残り物（experiments 以外の全件）

種類: file・symlink・empty_dir。作った契約は経路に契約の識別子があるものだけ埋め、ほかは UNKNOWN（audit の E-2 で個別に手がかりを書く）。同期は repo の `.stignore` の近似照合（`tools/leftovers.py` の冒頭）。参照は記号リンクの先だけを機械で埋める。

| 経路 | 種類 | バイト数 | 更新時刻（UTC） | 作った契約 | 参照 | 同期 |
|---|---|---:|---|---|---|---|
| `.codegraph/codegraph.db-shm` | file | 32768 | 2026-08-16 02:54 | UNKNOWN |  | 渡らない |
| `.codegraph/codegraph.db-wal` | file | 4758632 | 2026-08-16 02:54 | UNKNOWN |  | 渡らない |
| `.remember/tmp/capture-alive.d/0fb9f294-52ca-4cc1-b044-c1b1ef6fd6f1` | file | 0 | 2026-08-15 06:59 | UNKNOWN |  | 渡らない |
| `.remember/tmp/capture-alive.d/3debac97-ed17-4d22-a0a3-1af12c7bde68` | file | 0 | 2026-08-12 11:43 | UNKNOWN |  | 渡らない |
| `.remember/tmp/capture-gap-reported` | file | 36 | 2026-08-09 14:17 | UNKNOWN |  | 渡らない |
| `.remember/tmp/case-divergence` | file | 31 | 2026-08-09 14:17 | UNKNOWN |  | 渡らない |
| `.remember/tmp/now-day` | file | 11 | 2026-08-15 06:22 | UNKNOWN |  | 渡らない |
| `.remember/tmp/session-slug` | file | 244 | 2026-08-15 05:57 | UNKNOWN |  | 渡らない |
| `.remember/today-2026-06-21.done.md` | file | 146 | 2026-06-21 17:52 | UNKNOWN |  | 渡らない |
| `.remember/today-2026-06-22.done.md` | file | 809 | 2026-06-22 18:36 | UNKNOWN |  | 渡らない |
| `.remember/today-2026-07-02.done.md` | file | 716 | 2026-07-02 19:24 | UNKNOWN |  | 渡らない |
| `.remember/today-2026-08-09.done.md` | file | 1421 | 2026-08-10 19:49 | UNKNOWN |  | 渡らない |
| `.remember/today-2026-08-10.done.md` | file | 495 | 2026-08-10 22:10 | UNKNOWN |  | 渡らない |
| `.remember/today-2026-08-12.md` | file | 393 | 2026-08-15 06:11 | UNKNOWN |  | 渡らない |
| `.ruff_cache/0.15.14/12654479039210283474` | file | 115 | 2026-08-13 13:21 | UNKNOWN |  | 渡らない |
| `.ruff_cache/0.15.14/14247143544276483342` | file | 110 | 2026-08-13 12:24 | UNKNOWN |  | 渡らない |
| `.ruff_cache/0.15.14/5545426402685671108` | file | 280 | 2026-11-02 07:58 | UNKNOWN |  | 渡らない |
| `.ruff_cache/0.15.14/6578473635478274190` | file | 259 | 2026-08-13 11:31 | UNKNOWN |  | 渡らない |
| `.venv-relation-detr/lib/python3.10/site-packages/_virtualenv.pth` | file | 18 | 2026-05-28 08:45 | UNKNOWN |  | 渡らない |
| `.venv-relation-detr/lib/python3.10/site-packages/distutils-precedence.pth` | file | 151 | 2026-05-28 08:45 | UNKNOWN |  | 渡らない |
| `.venv-relation-detr/lib/python3.11/site-packages/torch/backends/opt_einsum/__pycache__/__init__.cpython-311.pyc` | file | 5442 | 2026-10-19 16:48 | UNKNOWN |  | 渡らない |
| `.venv-relation-detr/pyvenv.cfg.before_s2fix` | file | 144 | 2026-06-21 17:34 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/__init__.cpython-311.pyc` | file | 930 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/annotate.cpython-311.pyc` | file | 5918 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/bytecode.cpython-311.pyc` | file | 9751 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/collector.cpython-311.pyc` | file | 21738 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/config.cpython-311.pyc` | file | 30225 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/context.cpython-311.pyc` | file | 3244 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/control.cpython-311.pyc` | file | 66066 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/core.cpython-311.pyc` | file | 6274 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/data.cpython-311.pyc` | file | 13448 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/debug.cpython-311.pyc` | file | 35920 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/disposition.cpython-311.pyc` | file | 2562 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/env.cpython-311.pyc` | file | 4043 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/exceptions.cpython-311.pyc` | file | 3579 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/files.cpython-311.pyc` | file | 26930 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/html.cpython-311.pyc` | file | 44484 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/inorout.cpython-311.pyc` | file | 29869 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/jsonreport.cpython-311.pyc` | file | 10123 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/lcovreport.cpython-311.pyc` | file | 11840 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/misc.cpython-311.pyc` | file | 19774 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/multiproc.cpython-311.pyc` | file | 6019 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/numbits.cpython-311.pyc` | file | 8554 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/parser.cpython-311.pyc` | file | 57739 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/patch.cpython-311.pyc` | file | 6782 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/phystokens.cpython-311.pyc` | file | 8179 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/plugin.cpython-311.pyc` | file | 25712 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/plugin_support.cpython-311.pyc` | file | 19769 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/python.cpython-311.pyc` | file | 12974 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/pytracer.cpython-311.pyc` | file | 11905 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/regions.cpython-311.pyc` | file | 7165 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/report.cpython-311.pyc` | file | 17123 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/report_core.cpython-311.pyc` | file | 5723 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/results.cpython-311.pyc` | file | 24672 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/sqldata.cpython-311.pyc` | file | 70756 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/sqlitedb.cpython-311.pyc` | file | 13269 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/sysmon.cpython-311.pyc` | file | 24228 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/templite.cpython-311.pyc` | file | 15796 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/tomlconfig.cpython-311.pyc` | file | 12040 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/types.cpython-311.pyc` | file | 8642 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/version.cpython-311.pyc` | file | 1252 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/coverage/__pycache__/xmlreport.cpython-311.pyc` | file | 14759 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/__pycache__/__init__.cpython-311.pyc` | file | 460 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/__pycache__/unicode.cpython-311.pyc` | file | 2781 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/cffLib/__pycache__/__init__.cpython-311.pyc` | file | 139056 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/colorLib/__pycache__/__init__.cpython-311.pyc` | file | 198 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/colorLib/__pycache__/builder.cpython-311.pyc` | file | 34578 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/colorLib/__pycache__/errors.cpython-311.pyc` | file | 434 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/colorLib/__pycache__/geometry.cpython-311.pyc` | file | 5889 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/colorLib/__pycache__/table_builder.cpython-311.pyc` | file | 11759 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/colorLib/__pycache__/unbuilder.cpython-311.pyc` | file | 4247 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/config/__pycache__/__init__.cpython-311.pyc` | file | 3864 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/designspaceLib/__pycache__/__init__.cpython-311.pyc` | file | 139683 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/designspaceLib/__pycache__/split.cpython-311.pyc` | file | 18803 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/designspaceLib/__pycache__/statNames.cpython-311.pyc` | file | 10223 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/designspaceLib/__pycache__/types.cpython-311.pyc` | file | 6847 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/encodings/__pycache__/__init__.cpython-311.pyc` | file | 281 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/encodings/__pycache__/codecs.cpython-311.pyc` | file | 6366 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/feaLib/__pycache__/__init__.cpython-311.pyc` | file | 280 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/feaLib/__pycache__/ast.cpython-311.pyc` | file | 134258 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/feaLib/__pycache__/error.cpython-311.pyc` | file | 1633 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/feaLib/__pycache__/location.cpython-311.pyc` | file | 885 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/feaLib/__pycache__/lookupDebugInfo.cpython-311.pyc` | file | 818 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/__init__.cpython-311.pyc` | file | 276 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/arrayTools.cpython-311.pyc` | file | 16435 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/classifyTools.cpython-311.pyc` | file | 7312 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/cliTools.cpython-311.pyc` | file | 2681 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/configTools.cpython-311.pyc` | file | 17593 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/dictTools.cpython-311.pyc` | file | 4243 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/encodingTools.cpython-311.pyc` | file | 1964 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/enumTools.cpython-311.pyc` | file | 1126 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/etree.cpython-311.pyc` | file | 17838 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/filenames.cpython-311.pyc` | file | 9233 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/fixedTools.cpython-311.pyc` | file | 8839 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/intTools.cpython-311.pyc` | file | 1199 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/iterTools.cpython-311.pyc` | file | 837 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/lazyTools.cpython-311.pyc` | file | 2821 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/loggingTools.cpython-311.pyc` | file | 26393 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/psCharStrings.cpython-311.pyc` | file | 70792 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/roundTools.cpython-311.pyc` | file | 4262 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/sstruct.cpython-311.pyc` | file | 9542 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/textTools.cpython-311.pyc` | file | 8058 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/timeTools.cpython-311.pyc` | file | 3959 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/transform.cpython-311.pyc` | file | 21435 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/treeTools.cpython-311.pyc` | file | 2075 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/vector.cpython-311.pyc` | file | 10215 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/visitor.cpython-311.pyc` | file | 8163 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/__pycache__/xmlWriter.cpython-311.pyc` | file | 13020 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/misc/plistlib/__pycache__/__init__.cpython-311.pyc` | file | 29153 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/otlLib/__pycache__/__init__.cpython-311.pyc` | file | 248 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/otlLib/__pycache__/builder.cpython-311.pyc` | file | 171913 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/otlLib/__pycache__/error.cpython-311.pyc` | file | 1014 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/otlLib/__pycache__/maxContextCalc.cpython-311.pyc` | file | 3836 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/otlLib/optimize/__pycache__/__init__.cpython-311.pyc` | file | 2773 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/otlLib/optimize/__pycache__/gpos.cpython-311.pyc` | file | 21054 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/pens/__pycache__/__init__.cpython-311.pyc` | file | 276 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/pens/__pycache__/basePen.cpython-311.pyc` | file | 22379 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/pens/__pycache__/boundsPen.cpython-311.pyc` | file | 5254 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/pens/__pycache__/filterPen.cpython-311.pyc` | file | 19823 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/pens/__pycache__/pointPen.cpython-311.pyc` | file | 27960 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/pens/__pycache__/recordingPen.cpython-311.pyc` | file | 16388 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/pens/__pycache__/transformPen.cpython-311.pyc` | file | 7086 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/subset/__pycache__/__init__.cpython-311.pyc` | file | 227040 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/subset/__pycache__/cff.cpython-311.pyc` | file | 10593 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/subset/__pycache__/svg.cpython-311.pyc` | file | 11135 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/subset/__pycache__/util.cpython-311.pyc` | file | 1391 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/__pycache__/__init__.cpython-311.pyc` | file | 1699 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/__pycache__/sfnt.cpython-311.pyc` | file | 31782 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/__pycache__/standardGlyphOrder.cpython-311.pyc` | file | 2360 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/__pycache__/ttCollection.cpython-311.pyc` | file | 6497 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/__pycache__/ttFont.cpython-311.pyc` | file | 93026 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/__pycache__/ttGlyphSet.cpython-311.pyc` | file | 27548 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/__pycache__/ttVisitor.cpython-311.pyc` | file | 2025 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/BitmapGlyphMetrics.cpython-311.pyc` | file | 3137 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/C_F_F_.cpython-311.pyc` | file | 3941 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/C_O_L_R_.cpython-311.pyc` | file | 9511 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/C_P_A_L_.cpython-311.pyc` | file | 18837 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/D_S_I_G_.cpython-311.pyc` | file | 9010 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/DefaultTable.cpython-311.pyc` | file | 4276 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/E_B_D_T_.cpython-311.pyc` | file | 40438 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/E_B_L_C_.cpython-311.pyc` | file | 40352 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/G_D_E_F_.cpython-311.pyc` | file | 725 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/G_P_O_S_.cpython-311.pyc` | file | 826 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/G_S_U_B_.cpython-311.pyc` | file | 720 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/H_V_A_R_.cpython-311.pyc` | file | 739 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/M_A_T_H_.cpython-311.pyc` | file | 768 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/O_S_2f_2.cpython-311.pyc` | file | 33484 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/S_V_G_.cpython-311.pyc` | file | 10303 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/TupleVariation.cpython-311.pyc` | file | 40857 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/V_A_R_C_.cpython-311.pyc` | file | 715 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/V_O_R_G_.cpython-311.pyc` | file | 9856 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/V_V_A_R_.cpython-311.pyc` | file | 745 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/__init__.cpython-311.pyc` | file | 5177 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_a_n_k_r.cpython-311.pyc` | file | 912 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_b_s_l_n.cpython-311.pyc` | file | 812 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_c_m_a_p.cpython-311.pyc` | file | 70047 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_c_v_t.cpython-311.pyc` | file | 3695 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_f_p_g_m.cpython-311.pyc` | file | 3038 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_f_v_a_r.cpython-311.pyc` | file | 15305 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_g_a_s_p.cpython-311.pyc` | file | 3626 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_g_l_y_f.cpython-311.pyc` | file | 106710 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_g_v_a_r.cpython-311.pyc` | file | 17025 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_h_d_m_x.cpython-311.pyc` | file | 8358 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_h_e_a_d.cpython-311.pyc` | file | 6144 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_h_h_e_a.cpython-311.pyc` | file | 7064 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_h_m_t_x.cpython-311.pyc` | file | 8262 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_k_e_r_n.cpython-311.pyc` | file | 15532 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_l_c_a_r.cpython-311.pyc` | file | 819 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_l_o_c_a.cpython-311.pyc` | file | 4453 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_m_a_x_p.cpython-311.pyc` | file | 7090 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_n_a_m_e.cpython-311.pyc` | file | 50648 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_o_p_b_d.cpython-311.pyc` | file | 795 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_p_o_s_t.cpython-311.pyc` | file | 16104 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_p_r_e_p.cpython-311.pyc` | file | 903 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_p_r_o_p.cpython-311.pyc` | file | 771 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_s_b_i_x.cpython-311.pyc` | file | 6770 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/_v_m_t_x.cpython-311.pyc` | file | 999 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/otBase.cpython-311.pyc` | file | 68647 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/otConverters.cpython-311.pyc` | file | 131671 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/otData.cpython-311.pyc` | file | 135236 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/otDataSchema.cpython-311.pyc` | file | 2260 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/otTables.cpython-311.pyc` | file | 135306 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/otTraverse.cpython-311.pyc` | file | 7443 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/sbixGlyph.cpython-311.pyc` | file | 6953 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/sbixStrike.cpython-311.pyc` | file | 7467 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/ttLib/tables/__pycache__/ttProgram.cpython-311.pyc` | file | 27316 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/unicodedata/__pycache__/Blocks.cpython-311.pyc` | file | 8670 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/unicodedata/__pycache__/Mirrored.cpython-311.pyc` | file | 12346 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/unicodedata/__pycache__/OTTags.cpython-311.pyc` | file | 1090 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/unicodedata/__pycache__/ScriptExtensions.cpython-311.pyc` | file | 10993 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/unicodedata/__pycache__/Scripts.cpython-311.pyc` | file | 24232 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/unicodedata/__pycache__/__init__.cpython-311.pyc` | file | 9400 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/__init__.cpython-311.pyc` | file | 75864 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/builder.cpython-311.pyc` | file | 13068 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/errors.cpython-311.pyc` | file | 14312 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/featureVars.cpython-311.pyc` | file | 30923 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/merger.cpython-311.pyc` | file | 96579 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/models.cpython-311.pyc` | file | 36337 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/multiVarStore.cpython-311.pyc` | file | 15335 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/mvar.cpython-311.pyc` | file | 1381 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/stat.cpython-311.pyc` | file | 7670 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/fontTools/varLib/__pycache__/varStore.cpython-311.pyc` | file | 33527 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/hydra/_internal/core_plugins/__pycache__/__init__.cpython-311.pyc` | file | 208 | 2026-08-08 04:24 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/matplotlib/__pycache__/_type1font.cpython-311.pyc` | file | 41460 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/matplotlib/backends/__pycache__/_backend_pdf_ps.cpython-311.pyc` | file | 8833 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/matplotlib/backends/__pycache__/backend_mixed.cpython-311.pyc` | file | 4890 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/matplotlib/backends/__pycache__/backend_pdf.cpython-311.pyc` | file | 137178 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/matplotlib/backends/__pycache__/backend_svg.cpython-311.pyc` | file | 67478 | 2026-08-26 09:58 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/pytest_cov/__pycache__/engine.cpython-311-pytest-9.0.3.pyc` | file | 22577 | 2026-10-18 17:07 | UNKNOWN |  | 渡らない |
| `.venv/lib/python3.11/site-packages/torch/backends/cudnn/__pycache__/rnn.cpython-311.pyc` | file | 2915 | 2026-10-19 16:41 | UNKNOWN |  | 渡らない |
| `configs/stage2pilot/__pycache__/pd_extra_q_d9.cpython-311.pyc` | file | 4476 | 2026-11-01 15:40 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/01` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/02` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/03` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/04` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/05` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/06` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/07` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/08` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/09` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/10` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/11` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/12` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/13` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/14` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_all/15` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/01` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/02` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/03` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/04` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/05` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/06` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/07` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/08` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/09` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/10` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/11` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/12` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/13` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/14` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/annotations/tool_bbox/annotations_bbox_tool_only/15` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandDataset/seg_ann` | empty_dir | 4096 | 2026-07-27 17:22 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/01` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/02` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/03` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/04` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/05` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/06` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/07` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/08` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/09` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/10` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/11` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/12` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/13` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/14` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_all/15` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/01` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/02` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/03` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/04` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/05` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/06` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/07` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/08` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/09` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/10` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/11` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/12` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/13` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/14` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `data/annotations/HandToolDataset/annotations/tool_bbox/annotations_bbox_tool_only/15` | empty_dir | 4096 | 2026-07-27 18:08 | UNKNOWN |  | 渡らない |
| `node_modules/.bin/azmcp-linux-x64` | symlink | 34 | 2026-08-15 05:58 | UNKNOWN | → `../@azure/mcp-linux-x64/dist/azmcp` | 渡らない |
| `node_modules/.package-lock.json` | file | 607 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/LICENSE` | file | 1077 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/NOTICE.txt` | file | 824667 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/README.md` | file | 35693 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Azure.Mcp.Tools.AzureMigrate.xml` | file | 38853 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/ActivityProcessors.md` | file | 5855 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/AddApplicationInsightsTelemetry.md` | file | 5422 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/AddApplicationInsightsTelemetryWorkerService.md` | file | 4733 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/AddOpenTelemetry.md` | file | 4428 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/ApplicationInsightsWeb.md` | file | 4238 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/AzureMonitorExporter.md` | file | 5820 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/ConfigureOpenTelemetryProvider.md` | file | 8083 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/ConfigureResource.md` | file | 4830 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/ConsoleExporter.md` | file | 1433 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/EntityFrameworkInstrumentation.md` | file | 2250 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/HttpInstrumentation.md` | file | 4534 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/LogProcessors.md` | file | 3248 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/OpenTelemetrySdkCreate.md` | file | 4473 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/OtlpExporter.md` | file | 3189 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/RedisInstrumentation.md` | file | 2038 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/Sampling.md` | file | 3123 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/SdkCreateTracerProviderBuilder.md` | file | 4118 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/SqlClientInstrumentation.md` | file | 2033 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/TelemetryClient.md` | file | 6517 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/TelemetryConfigurationBuilder.md` | file | 6025 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/UseAzureMonitor.md` | file | 2552 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/UseAzureMonitorExporter.md` | file | 5746 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/WithLogging.md` | file | 4125 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/WithMetrics.md` | file | 3993 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/api-reference/dotnet/WithTracing.md` | file | 3142 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/concepts/dotnet/appinsights-aspnetcore.md` | file | 3574 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/concepts/dotnet/aspnet-classic-appinsights.md` | file | 3606 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/concepts/dotnet/azure-monitor-distro.md` | file | 2578 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/concepts/dotnet/opentelemetry-pipeline.md` | file | 2195 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/concepts/nodejs/azure-monitor-overview.md` | file | 3103 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/concepts/nodejs/opentelemetry-pipeline.md` | file | 6777 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/concepts/python/azure-monitor-overview.md` | file | 3747 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/concepts/python/opentelemetry-pipeline.md` | file | 7008 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/dotnet/aspnet-classic-setup.md` | file | 2337 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/dotnet/aspnetcore-distro-setup.md` | file | 3344 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/dotnet/aspnetcore-setup.md` | file | 3870 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/dotnet/workerservice-setup.md` | file | 4172 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/bunyan-setup.md` | file | 8168 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/console-setup.md` | file | 8384 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/express-setup.md` | file | 4122 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/fastify-setup.md` | file | 5993 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/langchain-js-setup.md` | file | 8285 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/mongodb-setup.md` | file | 5049 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/mysql-setup.md` | file | 5860 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/nestjs-setup.md` | file | 4627 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/nextjs-setup.md` | file | 12242 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/postgres-setup.md` | file | 4050 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/redis-setup.md` | file | 5416 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/nodejs/winston-setup.md` | file | 6238 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/python/console-setup.md` | file | 10994 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/python/django-setup.md` | file | 6402 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/python/fastapi-setup.md` | file | 6654 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/python/flask-setup.md` | file | 5188 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/python/genai-setup.md` | file | 6030 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/examples/python/generic-setup.md` | file | 3843 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/migration/dotnet/aad-authentication-migration.md` | file | 6636 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/migration/dotnet/appinsights-2x-to-3x-code-migration.md` | file | 9198 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/migration/dotnet/appinsights-2x-to-3x-no-code-change.md` | file | 3307 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/migration/dotnet/aspnet-classic-2x-to-3x-code-migration.md` | file | 9361 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/migration/dotnet/console-2x-to-3x-code-migration.md` | file | 5543 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/migration/dotnet/ilogger-migration.md` | file | 2788 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/migration/dotnet/workerservice-2x-to-3x-code-migration.md` | file | 6846 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/Instrumentation/Resources/migration/dotnet/workerservice-2x-to-3x-no-code-change.md` | file | 3226 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/dist/azmcp` | file | 149938074 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/index.js` | file | 2121 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `node_modules/@azure/mcp-linux-x64/package.json` | file | 755 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `package-lock.json` | file | 705 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `package.json` | file | 73 | 2026-08-15 05:58 | UNKNOWN |  | 渡らない |
| `scripts/__pycache__/post_experiments_to_notion.cpython-312.pyc` | file | 6474 | 2026-08-21 21:27 | UNKNOWN |  | 渡らない |
| `scripts/__pycache__/train_b2a.cpython-312.pyc` | file | 24716 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `scripts/__pycache__/train_s4_tecno.cpython-312.pyc` | file | 22670 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `scripts/__pycache__/train_t1a.cpython-312.pyc` | file | 28888 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `scripts/stage2pilot/__pycache__/pd_four.cpython-311.pyc` | file | 30207 | 2026-11-01 15:40 | UNKNOWN |  | 渡らない |
| `src/egosurgery/__pycache__/__init__.cpython-312.pyc` | file | 147 | 2026-08-21 21:27 | UNKNOWN |  | 渡らない |
| `src/egosurgery/__pycache__/train.cpython-311.pyc` | file | 3248 | 2026-08-08 04:24 | UNKNOWN |  | 渡らない |
| `src/egosurgery/metrics/__pycache__/__init__.cpython-312.pyc` | file | 155 | 2026-08-21 22:16 | UNKNOWN |  | 渡らない |
| `src/egosurgery/metrics/__pycache__/phase.cpython-312.pyc` | file | 15590 | 2026-08-21 22:16 | UNKNOWN |  | 渡らない |
| `src/egosurgery/models/__pycache__/__init__.cpython-312.pyc` | file | 154 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `src/egosurgery/models/heads/__pycache__/__init__.cpython-312.pyc` | file | 160 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `src/egosurgery/models/heads/__pycache__/tecno_head.cpython-312.pyc` | file | 6334 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/__init__.cpython-312.pyc` | file | 153 | 2026-08-21 21:27 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/eval_recipe.cpython-312.pyc` | file | 6696 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/experiment_id.cpython-312.pyc` | file | 2909 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/experiment_manager.cpython-312.pyc` | file | 16415 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/git_utils.cpython-312.pyc` | file | 1867 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/idempotency.cpython-312.pyc` | file | 4482 | 2026-08-21 21:27 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/notes_schema.cpython-312.pyc` | file | 7776 | 2026-08-21 21:27 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/notion_logger.cpython-312.pyc` | file | 23643 | 2026-08-21 21:27 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/research_logger.cpython-312.pyc` | file | 12546 | 2026-08-21 21:27 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/server_name.cpython-312.pyc` | file | 2691 | 2026-08-21 23:58 | UNKNOWN |  | 渡らない |
| `src/egosurgery/utils/__pycache__/tracking.cpython-312.pyc` | file | 6282 | 2026-08-21 23:59 | UNKNOWN |  | 渡らない |
| `tasks/T-2026-08-13-bengio-lecun-deadman-cutover/__pycache__/session_probe.cpython-311.pyc` | file | 20785 | 2026-08-13 12:27 | T-2026-08-13-bengio-lecun-deadman-cutover |  | 渡らない |
| `tasks/T-2026-08-13-bengio-lecun-zmx-deadman-cutover/__pycache__/topology_probe.cpython-311.pyc` | file | 30552 | 2026-08-13 13:23 | T-2026-08-13-bengio-lecun-zmx-deadman-cutover |  | 渡らない |
| `tests/__pycache__/test_check_evidence_map.cpython-311.pyc` | file | 14733 | 2026-10-18 17:29 | UNKNOWN |  | 渡らない |
| `third_party/Relation-DETR/configs/relation_detr/__pycache__/relation_detr_resnet50_egosurgery_t1b.cpython-311.pyc` | file | 4483 | 2026-06-21 17:38 | UNKNOWN |  | 渡らない |
| `third_party/Relation-DETR/configs/relation_detr/__pycache__/relation_detr_resnet50_egosurgery_t1b_ca.cpython-311.pyc` | file | 4570 | 2026-06-22 13:25 | UNKNOWN |  | 渡らない |
| `third_party/Relation-DETR/models/bricks/__pycache__/relation_decoder_phaseca.cpython-311.pyc` | file | 4761 | 2026-06-22 13:25 | UNKNOWN |  | 渡らない |
| `third_party/Relation-DETR/models/detectors/__pycache__/relation_detr_phasecrossattn.cpython-311.pyc` | file | 3709 | 2026-06-22 13:25 | UNKNOWN |  | 渡らない |
| `tools/__pycache__/validate_task.cpython-312.pyc` | file | 30263 | 2026-08-22 00:04 | UNKNOWN |  | 渡らない |
| `wandb/run-20261101_154226-ntyprqmi/files/config.yaml` | file | 5128 | 2026-11-01 15:43 | UNKNOWN |  | 渡らない |
| `wandb/run-20261101_154226-ntyprqmi/files/requirements.txt` | file | 1957 | 2026-11-01 15:42 | UNKNOWN |  | 渡らない |
| `wandb/run-20261101_154226-ntyprqmi/files/wandb-metadata.json` | file | 1456 | 2026-11-01 15:42 | UNKNOWN |  | 渡らない |
| `wandb/run-20261101_154226-ntyprqmi/files/wandb-summary.json` | file | 194 | 2026-11-01 15:43 | UNKNOWN |  | 渡らない |
| `wandb/run-20261101_154226-ntyprqmi/logs/debug-core.log` | symlink | 61 | 2026-11-01 15:42 | UNKNOWN | → `/home/ubuntu/.cache/wandb/logs/core-debug-20261101_154226.log` | 渡らない |
| `wandb/run-20261101_154226-ntyprqmi/logs/debug-internal.log` | file | 2240 | 2026-11-01 15:43 | UNKNOWN |  | 渡らない |
| `wandb/run-20261101_154226-ntyprqmi/logs/debug.log` | file | 4520 | 2026-11-01 15:43 | UNKNOWN |  | 渡らない |
| `wandb/run-20261101_154226-ntyprqmi/run-ntyprqmi.wandb` | file | 7177 | 2026-11-01 15:43 | UNKNOWN |  | 渡らない |
| `wandb/run-20261101_154226-ntyprqmi/tmp/code` | empty_dir | 4096 | 2026-11-01 15:42 | UNKNOWN |  | 渡らない |

## 表 E-3 repo の作業ツリーの残り物（experiments の全件）

| 経路 | 種類 | バイト数 | 更新時刻（UTC） | 参照 | 同期 |
|---|---|---:|---|---|---|
| `experiments/baselines/s0_041_wiring_verification_seed42/wandb/debug-internal.log` | symlink | 60 | 2026-08-08 04:40 | → `offline-run-20260808_044037-vtpz98fi/logs/debug-internal.log` | 渡らない |
| `experiments/baselines/s0_041_wiring_verification_seed42/wandb/debug.log` | symlink | 51 | 2026-08-08 04:40 | → `offline-run-20260808_044037-vtpz98fi/logs/debug.log` | 渡らない |
| `experiments/baselines/s0_041_wiring_verification_seed42/wandb/latest-run` | symlink | 36 | 2026-08-08 04:40 | → `offline-run-20260808_044037-vtpz98fi` | 渡らない |
| `experiments/baselines/s0_041_wiring_verification_seed42/wandb/offline-run-20260808_044037-vtpz98fi/files/requirements.txt` | file | 1929 | 2026-08-08 04:40 |  | 渡らない |
| `experiments/baselines/s0_041_wiring_verification_seed42/wandb/offline-run-20260808_044037-vtpz98fi/run-vtpz98fi.wandb` | file | 7777 | 2026-08-08 04:40 |  | 渡らない |
| `experiments/baselines/s0_041_wiring_verification_seed42/wandb/offline-run-20260808_044037-vtpz98fi/tmp/code` | empty_dir | 4096 | 2026-08-08 04:40 |  | 渡らない |
| `experiments/phase1/stage2pilot_cf_ptower_002_ft_coco_lr0.0001_foldAH2_seed42` | empty_dir | 4096 | 2026-10-18 18:22 |  | 渡らない |

## 表 E-4 `~/slocal2` 直下の残り物

| 経路 | 種類 | バイト数（`du -sb --apparent-size`） | 更新時刻（UTC） | 同期 |
|---|---|---:|---|---|
| `~/slocal2/.claude` | d | 659 | 2026-05-16 10:08 | 渡らない |
| `~/slocal2/.remember` | d | 30410 | 2026-05-24 17:11 | 渡らない |
| `~/slocal2/MIRU2026` | d | 8127402 | 2026-05-11 08:53 | 渡らない |
| `~/slocal2/claude-pulse` | d | 4121033 | 2026-05-17 04:24 | 渡らない |
| `~/slocal2/egosurgery_multitask` | d | 17199677441 | 2026-05-24 20:40 | 渡らない |
| `~/slocal2/ghost` | d | 657295649 | 2026-05-16 09:38 | 渡らない |
| `~/slocal2/m2-four` | d | 858489549 | 2026-10-19 21:55 | 渡らない |
| `~/slocal2/m2-s2fix-bengio` | d | 587164888 | 2026-10-19 13:09 | 渡らない |
| `~/slocal2/philip_setup_guide.md` | f | 21879 | 2026-05-24 20:29 | 渡らない |
| `~/slocal2/research-skills.zip` | f | 22625 | 2026-05-11 13:18 | 渡らない |
| `~/slocal2/s2fix-bengio-body` | d | 3097942 | 2026-10-19 13:47 | 渡らない |
| `~/slocal2/setup_philip.sh` | f | 9526 | 2026-05-24 20:54 | 渡らない |
| `~/slocal2/transfer_from_bengio.sh` | f | 5321 | 2026-05-24 20:36 | 渡らない |
| `~/slocal2/zmx` | d | 5090293 | 2026-05-16 09:58 | 渡らない |

## 表 E-4 家の直下の残り物

| 経路 | 種類 | バイト数（`du -sb --apparent-size`） | 更新時刻（UTC） | 同期 |
|---|---|---:|---|---|
| `~/.superpowers` | d | 315 | 2026-08-24 16:32 | 渡らない |
| `~/.vscode` | d | 39 | 2026-10-19 13:12 | 渡らない |
| `~/.zcompdump-Bengio-5.9` | f | 53250 | 2026-11-01 15:20 | 渡らない |
| `~/.zcompdump-Bengio-5.9.lock` | d | 0 | 2026-10-21 18:07 | 渡らない |
| `~/.zcompdump-Bengio-5.9.zwc` | f | 119904 | 2026-10-21 18:07 | 渡らない |
| `~/.zcompdump-Bengio-5.9.zwc.old` | f | 119992 | 2026-10-21 18:07 | 渡らない |
| `~/.zshrc.bak.agent-autoupdate.20261013124307` | f | 4373 | 2026-10-13 12:43 | 渡らない |
| `~/.zshrc.orig` | f | 2322 | 2026-08-23 21:00 | 渡らない |
| `~/m2-git-info-exclude.bak-20261019` | f | 565 | 2026-07-03 23:17 | 渡らない |

## 表 E-5 `/tmp` 直下の自分の残り物（名前の型ごと。全件は `e/leftovers_other.json` の tmp）

| 名前（型） | 件数 | 種類 |
|---|---:|---|
| `.sync-pause.released.T-2026-08-24-bengio-keeper-autosync` | 1 | f |
| `.sync-pause.released.T-2026-08-24-bengio-syncthing-node` | 1 | f |
| `T-2026-10-22-evidence-map-a-place-align-sh0fttqv` | 1 | d |
| `bsn_auth.out` | 1 | f |
| `bsn_decoy.txt` | 1 | f |
| `bsn_ib.txt` | 1 | f |
| `bsn_pf.txt` | 1 | f |
| `bsn_ssh.txt` | 1 | f |
| `bsn_ti.txt` | 1 | f |
| `bsn_wt.txt` | 1 | f |
| `cc-daemon-1000` | 1 | d |
| `code-792bbd71-a080-4429-826e-d7a37350aace` | 1 | s |
| `config.xml.before_folder_fix` | 1 | f |
| `conventions-and-defect-records-pr.md` | 1 | f |
| `dummy_gpu_cpu_861br2y7` | 1 | d |
| `evidence-map-a-positive-control-cs8r72_u` | 1 | d |
| `evidence-map-a-pr-b7k3jmo4.md` | 1 | f |
| `evidence-maps-revise-pr.md` | 1 | f |
| `gpu_dummy_0.log` | 1 | f |
| `gpu_dummy_1.log` | 1 | f |
| `gpu_dummy_load.py` | 1 | f |
| `hf_bengio.txt` | 1 | f |
| `hmm_val.npz` | 1 | f |
| `ka_bengio.txt` | 1 | f |
| `ka_bengio_baseline.txt` | 1 | f |
| `ka_ib.txt` | 1 | f |
| `ka_ti.txt` | 1 | f |
| `kh_bsn.txt` | 1 | f |
| `lovo_gap.json` | 1 | f |
| `m2-exclude-control-sl2bpe9j` | 1 | d |
| `m2-forbidden-control-sul12p6f` | 1 | d |
| `mcp-*` | 31 | d |
| `proposal-gate-brief-pr-corrected.md` | 1 | f |
| `proposal-gate-brief-pr.md` | 1 | f |
| `pymp-*` | 8 | d |
| `pyvenv.cfg.bak` | 1 | f |
| `smoke_hmm_presence_fixed_lag.txt` | 1 | f |
| `smoke_proxy_lovo_presence.txt` | 1 | f |
| `smoke_proxy_phase_presence_denoise.txt` | 1 | f |
| `smoke_signal_video_identity_probe.txt` | 1 | f |
| `ssh-*` | 5 | d |
| `st_bengio.tar.gz` | 1 | f |
| `st_v2_bengio.tar.gz` | 1 | f |
| `syncthing-linux-amd64-v2.1.3` | 1 | d |
| `syncthing.v1.27.10.bak` | 1 | f |
| `torchinductor_ubuntu` | 1 | d |
| `vscode-git-*` | 6 | s |
| `vscode-ipc-*` | 57 | s |
| `vscode-ssh-auth-sock-*` | 44 | l |
| `wandb-*` | 145 | d |
| `wandb_xpu-*` | 175 | s |

計 514 件。

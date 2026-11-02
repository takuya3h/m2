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


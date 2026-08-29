# lecun への検出器環境の用意（Relation-DETR）

出所: `T-2026-08-29-lecun-detector-env-pd`（2026-08-29 実施・実測）。

**用意するものは同期対象外である。** `third_party/` は `.gitignore:133`、venv は `.gitignore:63`
で除外されており、各ホストで用意する。**手順（how）だけを記録し、実装本体は追跡しない。**

## 0. 前提の実測（このホストで確かめた値）

| 項目 | 実測 |
|---|---|
| nvcc | **12.9**（`/usr/local/cuda`）。11.8 は**存在しない** |
| torch（本体 venv） | 2.1.2+cu118 |
| GPU | RTX A6000 × 2 |
| uv | `~/.local/bin/uv`。キャッシュ 6.4G |

🔴 **文書の前提（CUDA 11.8）とホストの実体（12.9）が食い違う。**
`scripts/setup_env_relation_detr.sh` は nvcc が 11.8 でなければ停止するため
`SKIP_CUDA_CHECK=1` が要る。**実測では 12.9 でも MS-Deform-Attn の JIT ビルドは成功し、
凍結源の mAP が完全再現した**（§3）。ただしこれは実測であって保証ではない。

## 1. 実装の用意（版管理下の snapshot から復元）

**上流を直接 clone するだけでは足りない。** 独自の config 15 件と detector 実装 6 件は
upstream に無く、`third_party_snapshot/lecun/Relation-DETR/`（版管理下）に在る。
`configs/detector_relation_detr/` のミラーは augstrong 系 2 件のみで、
凍結源が使う `train_config_egosurgery_seed42.py` を**含まない**。

    SNAP=third_party_snapshot/lecun/Relation-DETR
    TMP=<作業用の一時ディレクトリ>

    # 1-1. provenance の記録どおりに clone（origin と commit は provenance.txt にある）
    git clone --depth 50 https://github.com/xiuqhou/Relation-DETR.git "$TMP"
    cd "$TMP" && git checkout b485955c72452788240600da6d0f0b8cc49f33c7

    # 1-2. upstream 改変を当てる（--check で適合を先に確かめる）
    git apply --check "$SNAP/upstream_mods.patch"    # exit 0 を確認してから
    git apply "$SNAP/upstream_mods.patch"            # optimizer/param_dict.py と util/engine.py

    # 1-3. 独自ファイルを展開（config 15 / detector 6 / temporal 1 など 23 件）
    tar xzf "$SNAP/project_files.tar.gz"

    # 1-4. 記録の file_list と現物を突き合わせる（欠落 0 を確認）
    while read -r f; do [ -e "$f" ] || echo "欠落: $f"; done < "$SNAP/file_list.txt"

    # 1-5. checkpoints を残したまま合流（既存の ckpt を上書きしない）
    rsync -a --exclude 'checkpoints/' "$TMP/" <repo>/third_party/Relation-DETR/

🔴 **`--exclude 'checkpoints/'` を外さないこと。** `checkpoints/` は同期で配られており
凍結源 ckpt（195MB）を含む。合流の前後で sha256 が変わらないことを確かめる。

## 2. venv の構築

    SKIP_CUDA_CHECK=1 CUDA_HOME=/usr/local/cuda bash scripts/setup_env_relation_detr.sh

`requirements.relation_detr.lock.txt`（正本 72 pkg）を厳密適用する。
MS-Deform-Attn はここではビルドされず、**初回の detector forward で JIT ビルド**される。

## 3. 検証（必ず行う）

凍結源 ckpt を読み込んで val の mAP を出し、記録値と突き合わせる。

    export CUDA_HOME=/usr/local/cuda
    export PATH="<repo>/.venv-relation-detr/bin:$PATH"     # ninja を PATH に載せる
    .venv-relation-detr/bin/python scripts/eval_relation_detr_map.py \
        --config configs/train_config_egosurgery_seed42.py \
        --checkpoint checkpoints/incoming/seed42/best_ap.pth

**2026-08-29 の実測（lecun）**:

    [eval] => mAP=0.7303  mAP50=0.8546  (凍結源 目標 val/mAP≈0.7297 / mAP50≈0.854)
    AP  = 0.7302938994613697
    AP50 = 0.8545901117284289

`configs/stage/s4_phase_baseline.yaml:9` が記す「再 eval mAP 0.7303」と**完全一致**した。
索引の `s0_016` の 0.729749 は旧 recipe（`_legacy_score_thr_0`）の値であり、別物である。

**一致しない場合は環境の不備を疑う。取り繕わない。**

## 4. B4 用の ImageNet-R50（任意）

torchvision の標準重み。認証を伴わない。

    python -c "from torchvision.models import resnet50, ResNet50_Weights; resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)"

保存先 `~/.cache/torch/hub/checkpoints/resnet50-0676ba61.pth`（102,530,333 バイト）。
sha256 の先頭がファイル名の `0676ba61` と一致することが torchvision の完全性検査である。

なお検出器の backbone 初期化で `resnet50-11ad3fa6.pth`（IMAGENET1K_V2）も自動取得される。

## 5. 版管理に入れないこと

    git check-ignore -v .venv-relation-detr           -> .gitignore:63  .venv*/
    git check-ignore -v third_party/Relation-DETR/main.py -> .gitignore:133 third_party/

用意した後に `git status` が実装や venv を出さないことを確かめる。

# 候補 5 の計算量の実測（T-2026-10-23-ptower-cand5-compute-probe）

andrew の RTX A6000 一枚（GPU 0、49,140 MiB、driver 595.84）、torch 2.1.2+cu118、timm 1.0.27、
mamba-ssm 2.2.2、causal-conv1d 1.4.0。測定は 2026-10-23 05:59〜06:08 JST（28 試行、壁時計の和 470 秒）。
**学習は一つも収束まで回していない。checkpoint は残していない。** 生の記録は `results.jsonl`（1 行 = 1 試行）。
表は `make_tables.py` が `results.jsonl` から作ったものを写した。

## 測り方

- 1 試行 = 1 プロセス（`run_probe.py` → `probe.py`）。OOM が次の試行を汚さない。30 分で打ち切る（打ち切りは 0 件）
- 一歩 = 順伝播＋逆伝播＋最適化の一回。最初の 3 歩を除き、続く 10 歩の平均（`step s`）
- 記憶量は `torch.cuda.max_memory_allocated`（peak alloc）、`max_memory_reserved`（reserved）、
  `nvidia-smi --query-gpu=memory.used -lms 100` の最大（CUDA の文脈の分を含む）の三つ
- `PYTORCH_CUDA_ALLOC_CONF` は空（expandable_segments なし）。全試行 fp32 で TF32 は切ってある
- batch は目標から半分ずつ下げる。**すべての構成が目標で収まった**ため、探索の中で失敗は起きなかった。
  探索が失敗を拾えることの対照として、目標の一つ上（倍）を三構成で測った（下の各表の oom の行）
- ViT・MoCo v2・映像 MAE は乱数の入力と乱数の初期化（重みは読まない）。較正だけ実データと r3 の初期値
- 1 epoch の見込み = ⌈枚数 / batch⌉ × 一歩の時間。**データの読み込みは含まない**（較正以外は読み込みを測っていない）
- 枚数: `data/processed/phase_manifest_all_phase` の全体 17,233、折り A の train（01・02・03・06・08・11・12・13・14・15）10,580。
  17〜21 は manifest に無く、`docs/phase_annotation_stats_videos17-21.md` の 10,461 を使った

## 較正（三周目の工程塔の処方）

ResNet-50（r3 の `build_backbone(init=coco)`、stem 凍結）、入力 800×1422、AdamW、fp32、
`stage1_ptower.deterministic(42)`、実データ（折り A の train、`FoldFrames(train=True)`、4 workers）。

| batch | step s | peak alloc GiB | reserved GiB | nvidia-smi GiB | 読み込み s/batch |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.097 | 2.05 | 2.19 | 2.65 | 0.016 |
| 2 | 0.171 | 4.14 | 4.95 | 5.41 | 0.030 |
| 16 | 1.066 | 26.97 | 31.81 | 32.27 | 0.199 |

三周目の記録（別ホスト、学習全体の最大確保）は 27.06 GiB。batch 16 の 26.97 GiB と同じ桁。1 → 2 → 16 で単調に増える。
一歩の時間は host から device への写しを含み、読み込みを含まない（読み込みは別列）。

## ViT の fine-tune（DINOv3 型、乱数初期化）

timm の `vit_{base,large}_patch16_dinov3`（Eva 系、RoPE、接頭トークン 5 = CLS＋register 4）、`pretrained=False`、9 クラスの線形の頭。
800 系統は 800×1422 の幅を 16 の倍数へ切り上げた 800×1424（50 × 89 = 4,450 トークン）。
学ぶ範囲: full = 全体、top4 = 末尾 4 ブロック＋norm＋頭、linear = 頭だけ（backbone は `no_grad` で順伝播）。
SDPA の核は、各行の形（batch 1）で flash・efficient・math を一つずつ許して順伝播と逆伝播が通るかを調べ、
PyTorch 2.1 の優先順（flash → efficient → math）で最初に通るものを書いた。fp32 では flash が通らない（全行で usable=false）。

| 規模 | 入力 | トークン | 範囲 | 収まる batch | 一つ上 | step s | peak alloc GiB | reserved GiB | nvidia-smi GiB | SDPA | 取り出し s/枚 | 1 epoch（折り A の train） |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| ViT-B/16 | 224² | 196+5 | full | 64 | 未測定 | 0.500 | 10.19 | 10.54 | 10.99 | efficient | — | ⌈10580/64⌉×0.500 s = 1.4 min |
| ViT-B/16 | 224² | 196+5 | top4 | 64 | 未測定 | 0.281 | 3.84 | 4.11 | 4.53 | efficient | — | ⌈10580/64⌉×0.281 s = 0.8 min |
| ViT-B/16 | 224² | 196+5 | linear | 64 | 未測定 | 0.170 | 0.82 | 1.12 | 1.54 | efficient | 0.0027 | ⌈10580/64⌉×0.170 s = 0.5 min |
| ViT-B/16 | 448² | 784+5 | full | 16 | 未測定 | 0.596 | 9.99 | 10.40 | 10.86 | efficient | — | ⌈10580/16⌉×0.596 s = 6.6 min |
| ViT-B/16 | 448² | 784+5 | top4 | 16 | 未測定 | 0.330 | 3.77 | 4.06 | 4.48 | efficient | — | ⌈10580/16⌉×0.330 s = 3.6 min |
| ViT-B/16 | 448² | 784+5 | linear | 16 | 未測定 | 0.196 | 0.82 | 1.12 | 1.54 | efficient | 0.0122 | ⌈10580/16⌉×0.196 s = 2.2 min |
| ViT-B/16 | 800×1424 | 4450+5 | full | 4 | 未測定 | 1.760 | 13.65 | 14.23 | 14.69 | efficient | — | ⌈10580/4⌉×1.760 s = 77.6 min |
| ViT-B/16 | 800×1424 | 4450+5 | top4 | 4 | 未測定 | 0.961 | 5.05 | 5.37 | 5.79 | efficient | — | ⌈10580/4⌉×0.961 s = 42.4 min |
| ViT-B/16 | 800×1424 | 4450+5 | linear | 4 | 未測定 | 0.559 | 1.00 | 1.35 | 1.77 | efficient | 0.1395 | ⌈10580/4⌉×0.559 s = 24.6 min |
| ViT-L/16 | 224² | 196+5 | full | 64 | 未測定 | 1.615 | 27.45 | 28.80 | 29.26 | efficient | — | ⌈10580/64⌉×1.615 s = 4.5 min |
| ViT-L/16 | 224² | 196+5 | top4 | 64 | 未測定 | 0.740 | 5.87 | 6.23 | 6.65 | efficient | — | ⌈10580/64⌉×0.740 s = 2.0 min |
| ViT-L/16 | 224² | 196+5 | linear | 64 | 未測定 | 0.567 | 1.77 | 2.25 | 2.67 | efficient | 0.0088 | ⌈10580/64⌉×0.567 s = 1.6 min |
| ViT-L/16 | 448² | 784+5 | full | 16 | 未測定 | 1.847 | 27.11 | 27.53 | 27.98 | efficient | — | ⌈10580/16⌉×1.847 s = 20.4 min |
| ViT-L/16 | 448² | 784+5 | top4 | 16 | 未測定 | 0.824 | 5.81 | 6.00 | 6.42 | efficient | — | ⌈10580/16⌉×0.824 s = 9.1 min |
| ViT-L/16 | 448² | 784+5 | linear | 16 | 未測定 | 0.621 | 1.76 | 2.09 | 2.51 | efficient | 0.0387 | ⌈10580/16⌉×0.621 s = 6.9 min |
| ViT-L/16 | 800×1424 | 4450+5 | full | 4 | 8: OOM（46.46 GiB 確保時） | 5.125 | 36.66 | 37.20 | 37.66 | efficient | — | ⌈10580/4⌉×5.125 s = 225.9 min |
| ViT-L/16 | 800×1424 | 4450+5 | top4 | 4 | 未測定 | 2.261 | 7.49 | 7.80 | 8.22 | efficient | — | ⌈10580/4⌉×2.261 s = 99.7 min |
| ViT-L/16 | 800×1424 | 4450+5 | linear | 4 | 未測定 | 1.691 | 1.99 | 2.40 | 2.82 | efficient | 0.4221 | ⌈10580/4⌉×1.691 s = 74.5 min |

「一つ上 未測定」は目標で収まったため探していないことを表す（SPEC §5 Task C-1「目標が収まればそれ以上は探さない」）。
収まる最大は「目標以上」であり、上限は測っていない。
224² の linear の行（B 0.82、L 1.77 GiB）は 800 系統の full の行（B 13.65、L 36.66 GiB）より小さい。

## MoCo v2（ResNet-50）

二つのビュー（224² の乱数）、MLP の頭 2048–2048–128、queue K = 65,536、momentum 0.999、温度 0.2、SGD（lr 0.03、momentum 0.9、wd 1e-4）。
key の encoder は `no_grad`。単一 GPU のため shuffle BN は再現していない。

| batch | 状態 | step s | peak alloc GiB | reserved GiB | nvidia-smi GiB |
|---:|---|---:|---:|---:|---:|
| 256 | ok | 0.858 | 23.54 | 24.20 | 24.66 |
| 512 | OOM（対照） | — | 44.98 | 46.53 | 46.92 |

- 1 epoch（折り A の train 10,580）: ⌈10580/256⌉ × 0.858 s = 42 × 0.858 s = 0.6 min
- 1 epoch（折り A の train＋17〜21 = 10,580＋10,461 = 21,041）: ⌈21041/256⌉ × 0.858 s = 83 × 0.858 s = 1.2 min

## 映像 MAE（ViT-S/16）

encoder は ViT-S/16（384 次元、12 層、6 頭）で可視のトークンだけを通す。decoder は 192 次元、4 層、3 頭。
入力 10 フレーム × 224²、tubelet 2（5 × 196 = 980 トークン）、tube マスク。可視は時間の各段に 19 位置 × 5 = 95（実際のマスク比 0.903）。
損失は隠したトークンの画素の MSE（目標は乱数）。AdamW。パラメータ 24.58 M。

| batch | 状態 | step s | peak alloc GiB | reserved GiB | nvidia-smi GiB |
|---:|---|---:|---:|---:|---:|
| 256 | ok | 0.916 | 25.97 | 27.55 | 28.01 |
| 512 | OOM（対照） | — | 46.58 | 46.98 | 47.37 |

- 1 epoch（クリップ数 = 折り A の train の枚数 10,580）: ⌈10580/256⌉ × 0.916 s = 42 × 0.916 s = 0.6 min
- 視線のマスクは測っていない。可視のトークン数が同じなら、どの位置を隠すかで記憶量と時間は変わらない（encoder を通るのは可視のトークンの数だけで決まる）

## mamba-ssm の決定性

`Linear 2048→512`、`Mamba(d_model 512, d_state 64, d_conv 4, expand 2)` × 2、`Linear 512→9`。
入力は 1 × 1,400 × 2,048、seed 42。causal-conv1d の核を使っている（`causal_conv1d_fn` が None でない）。
各行は、同じ過程で模型と入力を作り直して二度、順伝播と逆伝播を行った差である。

| 行 | 出力の最大絶対差 | 勾配の最大絶対差 | 出力のビット一致 | 勾配のビット一致 |
|---|---:|---:|---|---|
| 同じ seed・決定論的（`stage1_ptower.deterministic`） | 0.0 | 5.684e-14 | 一致 | **不一致** |
| 同じ seed・決定論的を切る（補足の行） | 0.0 | 1.137e-13 | 一致 | 不一致 |
| 陽性対照: 決定論的を切る＋二度目の入力に 1e-3 | 1.272e-06 | 1.199e-07 | 不一致 | 不一致 |

- 二度目の実行（別のプロセス）でも三行とも同じ値だった（`results.jsonl` の mamba の 2 行）
- 決定論的な設定でも勾配はビット単位で一致しない。差が出たのは Mamba 層のパラメータだけで、
  逆伝播で最初に通る 2 層目の Mamba（`2.conv1d`、`2.x_proj`、`2.in_proj`）と、その下流の 1 層目の
  `dt_proj`・`out_proj`。入口と出口の `Linear` の勾配はビット一致した（切り分けの出力は契約の audit.md）。
  `torch.use_deterministic_algorithms(True)` は mamba-ssm と causal-conv1d の独自の CUDA 核に及んでいない、と読める。
  どちらの核の逆伝播が非決定かは切り分けていない

## 範囲外・測っていないもの

- adapter / LoRA の水準（SPEC §4 で対象外）、混合精度の行、データの読み込みを含む一歩（較正以外）
- 収まる batch の上限（目標で収まった行）

# RESULT — T-2026-10-21-ptower-multigpu-syncbn

ホスト dlsta（容器 `4f3861ae8d3b`、repo `/home/ubuntu/local/m2`）。分岐 `feat/ptower-multigpu-syncbn`（起点 origin/phase0 `0a111a6e`）。
時刻は JST。詳細と命令の出力は `audit.md`（以下 `audit:行`）。

## 1. 解決された参照

`inputs.denominator`・`sigma_policy`・`frozen_source` は契約に無い。`contract.inject_verbatim`（prohibitions・issuer_cautions・env_p0）は
`context/conventions.md`（`2d946b07`、起票時と同じ）の原文に従った。`conventions_rev`・`runindex_commit`・counts は起票時と一致し、
`meta.amendments` は空（audit:70）。§3.1 の行番号は起点の版で全件照合して一致した。

## 2. 判定

**verdict: partial。** 実装・通し・測定は完了。acceptance c は契約の字面（fp32 で測る前の許容差に本番が収まる）では未達で、
利用者の判断（G3）で float64 の照合を判定に使った。h の NODE の組（GPU0+GPU1）は利用者の指示で UNKNOWN。

| 関門 | 結果 | 実測 |
|---|---|---|
| G1 | pass | feat/ 分岐、起点 = origin/phase0、作業ツリーは契約だけ、空き GPU は 2・3・4（audit:119） |
| G2 | pass | 一枚の道の要約値が直す前後で `0e7bc888…` 一致。失敗の名前の集合は 6 → 6（新規 0）（audit:142） |
| G3 | ask → 利用者が続行を選択 | fp32 の本番が許容差を外れた（勾配 8.4e-3 > 1e-3）。float64 では 1.4e-13（陽性対照 1.5）（audit:187、216、234） |

## 3. 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 済 | 分岐・起点・目印・五枚の使用量と所有者・版・起点・試験の前の値（audit:12〜119） | 自分の python 1 本を GPU2 に起こし数え 1、存在しない exe で 0 |
| b | 済 | 直す前・後とも `0e7bc8889d88…`（state 320 項目）、失敗の名前 6 → 6 | 同じ設定の二度で一致、ft_lr 0.0001 の写しで `98ea7600…`（前後とも同じ値） |
| c | **字面では未達** | fp32: 陰性対照 0（収まる）、陽性対照 grad 1.4（外れる）、本番 grad 8.4e-3・loss 4.0e-4（**外れる**）。float64: 本番 1.4e-13、陽性対照 1.5 | 一枚どうしの fp32 と float64 の差が 1.1e-2（丸めの床）。三者を同じ許容差で判定した表は audit:187 |
| d | 済 | 本番の通しで 4 epoch とも両 rank 合わせて 38 枚・重複 0。照合で末尾 3/2・2/1 を一枚と比べ float64 で 5.4e-13 | 重複を一件入れた写しを試験が検出（duplicates 1, missing 1）。末尾を rank ごとの平均にした写しは末尾の更新だけ 0.31 外れる |
| e | 済 | 反転の列は rank 間で不一致（同じ位置の一致 44/76）。同じ seed の二度で要約値 `f43442a6…` 一致、反転と画像の列も同一 | 全 rank に同じ種を与えると列が一致することを試験が検出（workers 0・2）。seed 43 で要約値 `7fb6b73f…` |
| f | 済 | stem の bn1 の running の統計は一枚・二枚ともビット単位で不変。layer1〜4 は SyncBatchNorm 52 層（float64 で一枚と 3e-13） | stem を train にした写しで bn1 が変わる。SyncBN なしで統計の変化量が 0.18 ずれる |
| g | 済 | 評価・保存・証拠・W&B は rank 0 だけ（rank 1 の呼び出し 0 件）。低下は両 rank epoch 2、打ち切りは両 rank epoch 4。checkpoint 320 鍵が一枚の模型と差 0、`extract` で strict に読めた | rank ごとの呼び出しの記録ファイルの集合（rank1 は無し）。試験が保存を条件の外へ出した写しを検出 |
| h | 済（NODE は UNKNOWN） | 下の §4 の表 | 各測定の間の五枚の 1 秒ごとの記録で、使っていない GPU は 22 MiB のまま。REPORT §3 と同じ取り方の値を含む |
| i | 済 | 全 rank で決定性の設定が True。止まった演算 0 件（SyncBatchNorm・NCCL とも） | 切った写しで両 rank が `deterministic_algorithms=False` と読み出し、照合も 0.43 ずれた |
| j | 済 | env-facts の dlsta の行の下に 2 行（日付と契約つき） | 行の集合差: 消えた行 0、足した行 2 |
| k | 済 | 使った GPU は 1〜4（利用者の許可の範囲）。experiments・runindex の追加 0、data の差 0 行、新しい失敗 0 | 写しで data へ 1 件足すと forbidden-check が fail、足さなければ pass |
| l | — | PR は §7 に記す | 実測で draft・base・head を記録する |

## 4. 実測（次の契約で使う値）

**起動**: `CUDA_VISIBLE_DEVICES=1,2 torchrun --nproc_per_node=2 --master_port=29501 scripts/stage1_ptower_r3.py action=finetune ...`。
二本同時は `--master_port` を分ける。設定の `device` は二枚以上では使わない。普通の起動は一枚の道のまま（README の末尾の節）。

**照合の許容差と差**（fp32、参照は一枚の一度目。許容差は測る前に audit:158 へ書いた）:

| 候補 | loss_rel ≤1e-4 | grad_rel ≤1e-3 | bn_delta_rel ≤1e-3 | weight_update_rel ≤1e-2 |
|---|---|---|---|---|
| 陰性対照（一枚を二度） | 0 | 0 | 0 | 0 |
| 陽性対照（SyncBN なし） | 1.1e-02 | 1.4 | 1.8e-01 | 1.5 |
| 本番（SyncBN あり） | 4.0e-04 | 3.5e-01（最初の更新 8.4e-03） | 9.1e-03 | 1.9e-01 |
| 診断: 本番 float64（B=2） | 2.4e-16 | 3.1e-13 | 3.0e-13 | 8.4e-11 |
| 診断: 一枚 fp32 vs 一枚 float64 | 1.7e-05 | 2.1e-01（最初の更新 1.1e-02） | 5.3e-03 | 1.7e-01 |

**処方のままの二枚**（GPU ごと 8・累積 4・800×1422・fp32・決定性あり。一歩 = micro-step、読み込みの待ちを含む 60 歩の平均、最初の 8 を除く）:

| 構成 | 一歩 [s] | rank ごとの torch 最大確保 [bytes] | 予約 [bytes] | nvidia-smi 最大 [MiB] |
|---|---|---|---|---|
| NVLink GPU1–GPU2 | 0.7938 | 14,873,543,680 ×2 | 16,315,842,560 | 16,167 |
| NVLink GPU3–GPU4 | 0.7913 | 14,873,543,680 ×2 | 16,315,842,560 | 16,167 |
| SYS GPU1+GPU3 | 0.8014 | 14,868,907,008 ×2 | 16,336,814,080 | 16,097 |
| NODE GPU0+GPU1 | UNKNOWN | — | — | — |
| 二本同時 GPU1–GPU2 / GPU3–GPU4 | 0.8219 / 0.8064 | 14.87e9 前後 | 16.3e9 前後 | 16,187 |

一 epoch 604 歩。**学習だけの計算値** 約 480 s（単独）/ 約 496 s（二本同時の GPU1–2）。val の時間は含まない。
dlsta の版: git 2.43.0、torch 2.1.2+cu118、NCCL 2.18.6、cuDNN 8700、driver 595.84、論理 CPU 96。

## 5. 起票者の誤り

- **check_does_not_check**: 宣言した preflight の `gpu_free` は容器の中の compute プロセスだけを数え、開始時の GPU0（99〜813 MiB）と GPU1（442 MiB・96%）の外部使用でも PASS した（audit:112）
- **self_contradiction**: A.3 は他の利用者の使用が見える GPU を使わないと定めるが、Task E の組と二本同時は GPU1 を前提にし、代わりは GPU0 にしか書いていない。GPU1 に外部使用が出て、字面どおりでは E.1・E.3 を回せなかった（利用者の許可で測った）

## 6. 逸脱

- 利用者の指示で GPU0 を使わない（契約 §2 の許可を狭めた）。NODE の組は UNKNOWN
- GPU1 は外部使用が断続的に見えたが、利用者の許可（「1-2, 3-4を確実に使って良い」）で使った
- 測る前の許容差（勾配 1e-3）が fp32 の丸めの床（1.1e-2）より厳しかった（実行者の見積もりの誤り）。許容差は変えず、利用者の判断で float64 の照合を判定に使った
- float64・B=2 の照合は契約に無い診断として足した。照合の道具は `--per-gpu` と `--frames` を足した（torchrun が `--n` を自分の省略形と取り違えたため改名）
- 照合は増強を外した（§5.2.9）。通しと再現は増強あり
- W&B はオフラインにした（送らない）。証拠は ExperimentManager の置き場を repo の外へ差し替えて実物を通した
- `docs/experiment_log.md` は更新していない（run を作らない impl のため。前の同種の契約に合わせた）

## 7. 想定外・UNKNOWN・送出

- UNKNOWN: NODE の組の一歩の時間と記憶量。val を含む一 epoch の時間。全 epoch を通した溢れの有無（68 歩だけ測った）
- repo の外 `~/m2-scratch/T-2026-10-21-ptower-multigpu-syncbn/`（約 10 GB。照合の run と checkpoint、測定、GPU の記録）を残した。片付けは利用者の判断
- 送出: PR と `make task-report` の結果は commit の後に audit へ記す

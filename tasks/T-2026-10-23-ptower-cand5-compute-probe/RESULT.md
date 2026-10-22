# T-2026-10-23-ptower-cand5-compute-probe 結果

## 判定

status: pass。G1・G2 は pass。andrew の A6000 一枚（GPU 0）、fp32 で、候補 5 の全構成が目標の batch で収まった。
ViT 18 行、MoCo v2 の batch 256、映像 MAE の batch 256 がすべて収まった。mamba-ssm は、決定論的な設定でも勾配がビット単位で一致しない（最大絶対差 5.684e-14、出力は一致）。
学習は収束まで回しておらず、checkpoint を残していない。表の全体は `experiments/analysis/ptower_cand5_compute_probe/REPORT.md`、生の記録は同じ場所の `results.jsonl`（28 試行）にある。

## 完了判定

| # | 実測 |
|---|---|
| a | 分岐 feat/ptower-cand5-compute-probe、起点 origin/phase0 = bfe45510、作業ツリーは清浄、A6000 × 2（49,140 MiB、driver 595.84、compute プロセス 0）。版は torch 2.1.2+cu118、torchvision 0.16.2、timm 1.0.27、mamba-ssm 2.2.2、causal-conv1d 1.4.0。空きは 1.6T（[audit.md](audit.md) L5〜L54）。manifest は 17,233 で、折り A の train 10,580 は動画ごとの和と manifest の train の値の二通りで一致した（L42）。試験の前は 6 failed / 924 passed（L55） |
| b | batch 1・2・16 の最大確保は 2.05・4.14・26.97 GiB で単調に増える。26.97 は三周目の記録 27.06 GiB と同じ桁（L66） |
| c | 18 行すべてに値がある（UNKNOWN 0）。各行に注意の実装を書いた（全行 efficient で、fp32 のため flash は使えない）。ViT-L 800 系統の全体の行も測った（batch 4、36.66 GiB、5.12 s/歩）。対照として、その行を batch 8 にすると OOM になった（L81）。224² の全凍結＋線形の行（B 0.82、L 1.77 GiB）は、800 系統の全体の行（B 13.65、L 36.66 GiB）より小さい |
| d | MoCo v2 は batch 256 で 23.54 GiB・0.858 s。映像 MAE は batch 256 で 25.97 GiB・0.916 s。どちらも batch 512 は OOM（L81）。1 epoch の見込みは式つきで書き、式の枚数 10,580 は Task A の値と一致する |
| e | 同じ seed の二度の差は、決定論的な設定で出力 0.0・勾配 5.684e-14。陽性対照（決定論的を切り、入力に 1e-3 を足す）では出力 1.272e-06・勾配 1.199e-07。別プロセスで二度目を流しても同じ値だった（L81、L91） |
| f | 変更は置き場・契約のディレクトリ・受け皿の一件だけ（L125）。checkpoint は 0 件。forbidden-check は pass で違反 0。試験の後は 6 failed / 924 passed で、失敗の名前の集合は前と同じ。陽性対照として、写しの data/ に一件足すと fail・exit 1 になった（L106） |
| g | PR #259、base phase0、head feat/ptower-cand5-compute-probe、isDraft false、OPEN（gh pr view の応答。audit「commit と送出」） |

解決された参照（手順書 3）: `inject_verbatim` の 4 節（prohibitions・issuer_cautions・precision・folds）の原文は、audit.md の「解決された参照」に写した。conventions の blob ceb7ef0f は契約の conventions_rev と一致する。denominator・frozen_source の参照は無い。

## 実測（次の契約で使う値）

A6000 一枚、fp32、TF32 は切った。expandable_segments は無し。1 epoch は折り A の train 10,580 枚で、データの読み込みを含まない。

| 規模・入力 | 全体: batch / GiB / s / 1 epoch | 上位 4: batch / GiB / s / 1 epoch | 全凍結＋線形: batch / GiB / s / 1 epoch / 取り出し s/枚 |
|---|---|---|---|
| ViT-B 224² | 64 / 10.19 / 0.500 / 1.4 min | 64 / 3.84 / 0.281 / 0.8 min | 64 / 0.82 / 0.170 / 0.5 min / 0.0027 |
| ViT-B 448² | 16 / 9.99 / 0.596 / 6.6 min | 16 / 3.77 / 0.330 / 3.6 min | 16 / 0.82 / 0.196 / 2.2 min / 0.0122 |
| ViT-B 800×1424 | 4 / 13.65 / 1.760 / 77.6 min | 4 / 5.05 / 0.961 / 42.4 min | 4 / 1.00 / 0.559 / 24.6 min / 0.1395 |
| ViT-L 224² | 64 / 27.45 / 1.615 / 4.5 min | 64 / 5.87 / 0.740 / 2.0 min | 64 / 1.77 / 0.567 / 1.6 min / 0.0088 |
| ViT-L 448² | 16 / 27.11 / 1.847 / 20.4 min | 16 / 5.81 / 0.824 / 9.1 min | 16 / 1.76 / 0.621 / 6.9 min / 0.0387 |
| ViT-L 800×1424 | 4 / 36.66 / 5.125 / 225.9 min | 4 / 7.49 / 2.261 / 99.7 min | 4 / 1.99 / 1.691 / 74.5 min / 0.4221 |

- GiB は torch の最大確保。予約と nvidia-smi の値は REPORT にある。1 epoch は ⌈10580 / batch⌉ × 一歩の時間で出した
- 800 系統は 800×1422 の幅を 1424 へ切り上げた（50 × 89 = 4,450 トークン、接頭トークン 5）
- MoCo v2（K 65,536）: batch 256 で 23.54 GiB・0.858 s。1 epoch は ⌈10580/256⌉ × 0.858 = 0.6 min、17〜21 を足すと ⌈21041/256⌉ × 0.858 = 1.2 min
- 映像 MAE（ViT-S、10 フレーム、tubelet 2、tube マスク、可視 95 / 980）: batch 256 で 25.97 GiB・0.916 s。1 epoch は ⌈10580/256⌉ × 0.916 = 0.6 min
- mamba-ssm（causal-conv1d の核を使う）: 決定論的な設定で、出力はビット一致し、勾配は不一致。差が出るのは Mamba 層のパラメータだけで、Linear の勾配は一致する（audit L91）
- 較正（r3 の処方、実データ）: batch 16 は 26.97 GiB・1.066 s/歩、読み込みは 0.199 s/batch

## 起票者の誤り

- `check_does_not_check`: 完了判定 c と d の空振りの確認は「batch を一つ上げると失敗する」である。一方、手順の Task C-1 は「目標が収まればそれ以上は探さない」と定め、D と E も目標の 256 から下げる探索しか書いていない。実際には全構成が目標で収まったため、指示どおりの探索では失敗が一度も起きず、確認が成り立たない。目標の倍を三構成で別に測って補った
- `asserted_without_measuring`: SPEC は「17,233 フレームの manifest」と書くが、経路を名指ししていない。参照先の `configs/stage1_ptower_r3.yaml` の `manifest_dir`（`data/processed/phase_manifest`）は 15,437 で、Task A-5 の規則どおりに読むと停止に当たる。17,233 と一致するのは `phase_manifest_all_phase` である
- `asserted_without_measuring`: SPEC §2 は「工程塔の数値精度は fp32（規約 `conventions#precision`）」と出所を示すが、規約のその節の原文は「工程塔の学習の精度は本節で定めない」と書く（audit の precision の写し）。本契約は SPEC の指定どおり fp32 で測ったため、値は変わらない

## 逸脱

- judgement: manifest は `phase_manifest_all_phase` を使った（上の理由）
- judgement: 目標の倍の対照試行 3 本と、mamba の再実行・パラメータごとの切り分けを足した。SPEC の手順に無い
- judgement: 800 系統の入力は 800×1424（切り上げ）とした。ViT は DINOv3 型の timm の構造（Eva、RoPE、register 4）で、乱数初期化。全凍結＋線形の頭は timm 既定の pooling の出力に当てた
- judgement: 映像 MAE の tubelet 2・decoder（192 次元、4 層）・可視 95 は実装者の選択。SPEC に値が無い
- judgement: CLAUDE.md の README.md・experiment_log・W&B の要求は適用していない。コードを変えず、学習の run も作らない測定で、変更範囲（完了判定 f）の外になるためである
- judgement: MoCo v2 の queue K = 65,536・m 0.999・T 0.2 は原典（arXiv:1911.05722、2003.04297 と公式実装の既定）として既知の値を置いた。外部への接続は事前の確認を要するため、このセッションでは原典を引いて照合していない。queue は 32 MiB で、記憶量への寄与は小さい
- judgement: 単一 GPU のため、MoCo の shuffle BN は再現していない
- judgement: ViT・MoCo・MAE の行は決定論的な設定を使わず、fp32 で TF32 を切っただけである。較正と mamba は `stage1_ptower.deterministic` を使った

## 想定外・UNKNOWN

- 想定外: mamba-ssm は決定論的な設定でも勾配が非決定である。selective scan と causal-conv1d のどちらの核の逆伝播かは UNKNOWN
- UNKNOWN: 目標で収まった構成の収まる上限、データの読み込みを含む一歩（較正以外）、adapter/LoRA の水準と混合精度の行（対象外）

## 送出

PR #259（主作業の commit 165cd94c）。task-report の終了コードと台帳の応答は audit.md の「commit と送出」に記録する。

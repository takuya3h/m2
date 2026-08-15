# T-2026-08-11-grasp-linear-probe 実行結果

**status:** pass  
**host:** Bengio  
**branch:** `feat/grasp-linear-probe`

## 1. 解決された参照

`context/conventions.md` の現在版は `d422b08` で、契約の
`conventions_rev` と一致した。`contract.inject_verbatim` の原文は次のとおり。

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

`runindex/` の現在版は `44697d9` で、契約作成元の版と一致した。

## 2. Phase A — 特徴と教師

契約が入口に挙げた `src/egosurgery/engines/phase_trainer.py` は、保存済みの
検出器特徴を読まず、raw image から frozen ImageNet ResNet50 の特徴を毎回計算する旧 S3
経路だった。象徴名をリポジトリ全体で辿ると、現行 S4 系は
`scripts/train_s4_tecno.py` から次の保存済み特徴を読む。

`data/processed/stage1_features/relation_detr_seed42/{train,val,test}_gap.npz`

1 ファイルを実際に開いた。保存単位は split ごとの NPZ、1 行が 1 frame、特徴は
2048 要素の `float32`、対応鍵は `frame_ids` の basename stem である。3 split の合計は
127,017,196 bytes（`du` 表示 122 MiB）で、全要素は有限だった。

| split | feature shape | 教師 frame | 教師∩特徴 | 教師のみ | 特徴のみ |
|---|---:|---:|---:|---:|---:|
| train | 9,657 × 2,048 | 9,356 | 9,356 | 0 | 301 |
| val | 1,515 × 2,048 | 1,514 | 1,514 | 0 | 1 |
| test | 4,265 × 2,048 | 4,107 | 4,107 | 0 | 158 |

直接対照として `01_1_0124` は train 特徴 index 0 と教師次元 1・2 に対応した。
集合差は両方向で計算し、教師側の全 ID について直接 membership も確認した。したがって
G1 は **pass** である。

### 5 次元の正例率

分子/教師 frame 数（括弧内は割合）。test は分布確認だけに読み、model の fit・評価には
使っていない。

| 次元 | train | val | test |
|---|---:|---:|---:|
| 1 左手が写る | 8,659/9,356 (0.925502) | 1,491/1,514 (0.984808) | 3,816/4,107 (0.929145) |
| 2 右手が写る | 8,386/9,356 (0.896323) | 1,463/1,514 (0.966314) | 3,663/4,107 (0.891892) |
| 3 左手が器具を持つ | 7,129/9,356 (0.761971) | 1,231/1,514 (0.813078) | 3,107/4,107 (0.756513) |
| 4 右手が器具を持つ | 7,176/9,356 (0.766994) | 1,274/1,514 (0.841480) | 3,136/4,107 (0.763574) |
| 5 両手で器具を持つ | 952/9,356 (0.101753) | 176/1,514 (0.116248) | 333/4,107 (0.081081) |

## 3. Phase B — 一段の線形 probe

train だけで `StandardScaler` を fit し、その後に各次元独立の binary logistic
regression を fit した。score は全体として一つの affine 変換であり、非線形層・時間情報は
無い。L2、`C=1.0`、`class_weight=balanced`、`liblinear`、最大 2,000 iteration とし、
ハイパーパラメータ探索は行わなかった。測定は val のみで、収束警告は 5 次元とも 0。

| 次元 | val 正例率 | ROC-AUC | Average Precision |
|---|---:|---:|---:|
| 1 左手が写る | 0.984808 | 0.644913 | 0.991323 |
| 2 右手が写る | 0.966314 | 0.758849 | 0.988731 |
| 3 左手が器具を持つ | 0.813078 | 0.829266 | 0.945261 |
| 4 右手が器具を持つ | 0.841480 | 0.743446 | 0.923416 |
| 5 両手で器具を持つ | 0.116248 | 0.792754 | 0.411158 |

次元 1–2 の平均 ROC-AUC は 0.701881、次元 3–5 は 0.788489、点推定の差
（把持−可視性）は +0.086608 だった。ただし negative control の群差の seed 間 range は
乱数特徴で 0.110561、教師 shuffle で 0.312919 であり、実差より大きい。したがって
**5 次元はいずれも読み取れるが、把持群の方が可視性群より読みやすいとは断定しない。**

## 4. Phase C — 対照

seed 42/123/456 の 3 回で測った。教師 shuffle は train の全 frame を一括 permutation し、
同一動画内に限定していない。

| 対照 | ROC-AUC 全15値の平均 | sample SD | min–max |
|---|---:|---:|---:|
| train 教師を動画横断で shuffle | 0.476591 | 0.099015 | 0.321443–0.626426 |
| 同じ shape の乱数特徴 | 0.498646 | 0.034304 | 0.431313–0.547649 |

どちらも全体平均は偶然水準へ落ちた。各実特徴の AUC は、同じ次元の全 negative-control
seed の最大値より高かった。

契約指定の陽性対照「術具 annotation が 1 件以上」は train 9,618/9,657、val
1,515/1,515 だった。val が全陽性なので ROC-AUC は **UNKNOWN**、AP=1.0 は定数陽性でも
得られ、対照として無効である。これは測定前に分布を確認していない起票者欠陥である。

指定対照を置換せず、追加の有効な陽性対照として正負が揃う Tweezers 有無を測った。
train 5,764/9,657、val 825/1,515、ROC-AUC 0.921263、AP 0.934747 だった。
陰性対照が偶然水準へ落ち、追加陽性対照が高値を返したため G2 は **pass** とした。

## 5. 設計判断

把持に関わる次元 3–5 は ROC-AUC 0.743446–0.829266 で、希少な次元 5 も AP
0.411158（正例率 0.116248）だった。従って、Relation-DETR seed42 の frozen GAP 特徴を
入力として把持を推論する構成には、少なくとも線形に読み出せる情報が残っている。
並行実装を継続する判断材料になる。

この値は、**同じ frozen GAP と frame-level 教師を使う線形 head の実用的な上限目安**で
あり、数学的な上限ではない。並行実装が大きく下回る場合は、frame ID/教師対応、特徴経路、
class imbalance と loss、最適化、工程へ渡す前の推論 head を順に疑う。強い非線形 head は
この値を上回り得るため、「超えたら誤り」とは扱わない。

起票者の「次元 1–2 は読みやすい」は一部だけ裏づけられたが、次元 1 は 0.644913 に
留まった。「次元 3–5 の方が難しい」という見込みは点推定では否定された。ただし群差は
対照の振れ幅より小さく、難しさの群差そのものは **UNKNOWN** とする。

## 6. 起票者欠陥、判断、逸脱

1. `phase_trainer.py` を現行 frozen 検出器特徴の入口としていたが、実装は ImageNet
   ResNet50 を raw image に毎回適用する旧経路だった。リポジトリ全体を辿って現行 S4 の
   NPZ を解決した。
2. 指定陽性対照は val の class support を測らずに成立すると断定しており、指示どおり
   AUC を出すと定義不能だった。指定結果は UNKNOWN のまま残し、追加対照を明示した。
3. task 固有の書き込み範囲を一般規約の `tasks/todo.md` / root `README.md` 更新より優先し、
   それらは変更しなかった。
4. 導入済み CodeGraph は index 1,082 files / 5,245 nodes で up-to-date だったが、現行 CLI
   に `watch` サブコマンドが無かったため、常駐 watch は開始できなかった。
5. 同期抑止は `.sync-pause` の改名で解除した。`.sync-pause.released` は ignore 対象外だった
   ため削除せず、`/tmp/m2-sync-pause.released.T-2026-08-11-grasp-linear-probe` へ退避した。

ユーザー判断が必要な未回答事項は無い。次の契約では、陽性対照を class support のある
対象へ事前登録し、入口を `train_s4_tecno.py` と S4 config に更新する必要がある。

## 7. 検証と証跡

- L1/L2: 1 task、0 failed、WARN なし
- L3: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL
  - SKIP: `cuda_ext_loaded`、`deterministic_flags`、`prereg_committed`、`frozen_source_hash`
- 独立出力検証: 12 PASS / 0 FAIL
- `audit/probe_result.csv` / `audit/control.csv`: UTF-8 BOM 付き
- model fit/eval: train/val のみ、test 不使用、GPU 不使用

証跡は `audit/phase_a.json`、`audit/probe_result.csv`、`audit/control.csv`、
`audit/control.txt`、`audit/summary.json`、`audit/run_probe.py`、
`audit/verify_outputs.py` に残した。

### 再現性の確認（2026-08-15、独立な再実行）

`/task` の再実行にあたり `audit/run_probe.py` を同じ環境で最初から回し直し、
実行前に退避した控えと生成物をバイト単位で照合した。

| 生成物 | 照合 |
|---|---|
| `audit/phase_a.json` | 一致 |
| `audit/probe_result.csv` | 一致 |
| `audit/control.csv` | 一致 |
| `audit/control.txt` | 一致 |
| `audit/summary.json` | 一致 |

5 件すべて一致した。Phase A と Phase B は途中で打ち切られた 1 回目を含め 2 回とも
一致している。`verify_outputs.py` は再実行後も 12 PASS / 0 FAIL だった。

併せて次を実測で裏づけた。

- NPZ 3 file の形状は 9,657 / 1,515 / 4,265 × 2,048 の `float32`、全要素有限、
  合計 127,017,196 bytes。
- `phase_trainer.py` は `torchvision` の ResNet50（ImageNet 事前学習）を raw image へ
  毎回適用する S3 経路で、実装のコメントにも「検出器とは独立」と書かれている。
  現行 S4 の `scripts/train_s4_tecno.py` は `_FROZEN_SRC` の既定値
  `relation_detr_seed42` の `{split}_gap.npz` を読む。**起票者欠陥 1 は実装で確認できた。**
- 5 次元それぞれの実測 ROC-AUC は、同じ次元の陰性対照 6 値（2 種 × 3 seed）の最大値を
  いずれも上回った。余裕が最も小さいのは次元 1 の +0.083224 である。
- `.sync-pause` による抑止は 2026-08-15 06:21:31 の常駐処理のループで実際に効き、
  記録に `一時停止中` が出た。**抑止そのものにも対照が取れている。**

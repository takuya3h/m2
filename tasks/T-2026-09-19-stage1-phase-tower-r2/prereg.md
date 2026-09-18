# 事前登録 — T-2026-09-19-stage1-phase-tower-r2

学習開始より前に commit する。commit 後は変えない。変更は `meta.amendments` に追記する。

## 1. 問い

一周目（T-2026-09-18-stage1-phase-tower）は凍結 ImageNet-1K R50 の特徴の上で時間ヘッドを比べ、val 0.329 / test 0.225 の塔を確定した。
Stage 0 の S4（検出 backbone 由来）は同じ折り A の val で 0.645。差 0.28 は時間ヘッドの差ではなく特徴の差である。

検出塔 D\* は backbone を EgoSurgery の box ラベルで fine-tune している（stem のみ凍結、layer1〜4 を学習）。
工程塔 P\* の backbone を同様に EgoSurgery の工程ラベルで fine-tune し、D\* と対称にする。
M §5.1「P\* は ImageNet か中立 SSL の初期化」は初期化の出所の規則であり、凍結を求めていない。
D\* と P\* が共有するのは ImageNet の初期値だけで、D の情報は P に入らない。

## 2. 設計

### backbone の fine-tune

| 項目 | 値 |
|---|---|
| 初期化 | torchvision ImageNet-1K ResNet-50（一周目と同じ重み、要約値を記録） |
| 凍結範囲 | **stem のみ凍結。layer1〜4 を学習**（検出塔 D\* の `freeze_indices=(0,)` と揃える） |
| 教師 | 折りの train 動画の工程ラベル（フレーム単位、9 工程） |
| データ | 折りの train 動画のみ。val は最良 epoch の選択にだけ使う。test は見ない |
| epoch | 上限 12（D\* と揃える）。val の frame accuracy で最良 epoch を選ぶ |
| 学習率 | **2 水準**（掃引）。値は `scripts/train_phase_tower_r50.py` の既定を高い方とし、その 1/3 を低い方とする。実行者が既定を読んで値を記録する |
| その他 | batch、増強、最適化器は同スクリプトの既定に固定。値を記録する |
| seed | 折り A は 42・123・456、折り B〜E は 42 |
| 本数 | 2 水準 × 7 = 14 fine-tune |

### 特徴と時間ヘッド

- fine-tune 後の backbone から C5 GAP 2048-d を、その折りの全動画（train・val・test）について抽出する（折り・seed・学習率ごとに別の特徴）
- 時間ヘッドは一周目と同じ 10 構成（候補 A 2、B 4、C 4。受容野・履歴・平滑化の値は一周目と同一）を同じ折り・seed で回す
- 一周目の確定 recipe（C・8 層・0.30・30）が再び勝つとは限らないので、10 構成を回し直す

### P\*-21

追加 6 動画（17〜22）の 0.5 fps フレームが本ホストに在れば、P\*-15 で確定した recipe（学習率と時間ヘッド）で、
各折りの train に 6 動画を足して学習する。無ければ UNKNOWN。

## 3. 予測（結果を見る前に書く）

1. fine-tune 後の 5 折り平均 val macro Jaccard は、一周目の確定塔（0.329）を **5 点以上**上回る
2. 折り A の val は S4（0.645）との差が一周目の 0.28 の**半分以下**に縮む
3. 時間ヘッドの最良は一周目の候補 C とは限らない。特徴が強くなると単純な候補 A か B が最良になりうる
4. 学習率 2 水準のうち**低い方**が最良になる（fine-tune は小さい学習率が安定する一般則）
5. val と test の乖離は一周目（0.33 → 0.22）より縮む（特徴が汎化するため）

## 4. Primary endpoint

候補・掃引点・学習率ごとの **5 折り平均の折り内 val macro Jaccard**（折り A は 3 seed の平均、他は 1 seed）。
co-primary は frame accuracy で同方向。定義は `conventions#eval_recipe`（online-causal、Jaccard strict）。

## 5. 判定規則（G1 の再確定）

1. backbone の学習率と時間ヘッドの（候補、掃引点）の組を、5 折り平均の val macro Jaccard が最大で、co-primary が同方向のものに決める
2. 最良と次点の差が折り A の seed 間 SD 以内で、1 run の所要時間が ±20% 以内なら、構成の単純さで決める。順は候補 A ＞ C ＞ B、次に受容野の短い方、次に折り A の seed 間 pstd が小さい方（一周目の追加規則を最初から含める）
3. P\*-15 の recipe を確定し、P\*-21 は画像があれば同じ recipe で学習する。別のトーナメントは行わない
4. test は確定塔について折りごとに一度だけ評価し、台帳に記録する。選定に test を使わない

## 6. 対照

- **一周目の確定塔**（凍結特徴 + C・8・0.30・30）を同じ折りで並置する。fine-tune の効果量がこれで出る
- **一周目の単フレーム線形対照**（折り A、0.2250）。fine-tune 後の frame accuracy がこれを下回る折りがあれば停止
- 特徴の決定性: 二度の抽出で要約値が一致。backbone を変えると変わる
- 折り A の S4 との並置（判定に使わない）

## 7. 停止条件

- fine-tune 後の frame accuracy が線形対照を下回る折りがある → 停止
- 特徴の要約値が二度で一致しない → 停止
- 1 fine-tune が 1 時間を超える → 諮る
- 装置が使われている → 停止

## 8. 予測外れの記録

§3 の 5 項目の当たり・外れを RESULT に書く。外れは F に「予測外れ」として残す。

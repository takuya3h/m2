# 事前登録 — T-2026-09-18-stage1-detector-towers

学習開始より前に commit する。commit 後は変えない。変更は `meta.amendments` に追記する。

## 1. 問い

Stage 0 の凍結源を生んだ処方で検出塔（Relation-DETR）を 5 折りに広げる。
D\*-COCO（COCO 事前学習の初期化）と D\*-ImageNet（backbone のみ ImageNet-1K 初期化、検出ヘッドは乱数初期化）の 2 塔を確定する。
M §5.2 の要求。トーナメントではない。

## 2. 処方

- Stage 0 の凍結源（`conventions#frozen_source`、seed 42 の `best_ap.pth`）を生んだ処方を記録から特定し、そのまま使う。
  epoch・batch・解像度・増強・最適化器・学習率を変えない。候補間で recipe 同一（M §5.1）
- **数値精度は TF32**（利用者の決定 2026-09-18。T-2026-09-17-amp-compile-timing で主指標の差 0.03σ を確認）。
  凍結源は fp32 で学習されているため、折り A の再現には TF32 由来の差が含まれる。許容差はそれを見込んで置く
- 折りは `conventions#folds`。seed は折り A が 42・123・456、折り B〜E が 42。計 7 run × 2 塔 = 14 run
- 学習は折り内 val で最良 epoch を選ぶ。test は見ない

## 3. 予測（結果を見る前に書く）

1. 折り A seed 42 の D\*-COCO は、凍結源の val mAP（`conventions#frozen_source` の記録値）と 1 mAP 以内で一致する
2. D\*-ImageNet は 5 折りすべてで D\*-COCO より低く、差は 5〜15 mAP（証拠地図 A の SurgMAE Table 7 が示す初期化源の支配性からの外挿。距離 2〜3）
3. 折り B〜E の val mAP の折り間 SD は、折り A の 3 seed の SD より大きい（動画 3 本の test は動画の個性を強く受ける）
4. D\*-ImageNet の学習は D\*-COCO より収束が遅く、同 epoch 数では最良 epoch が後ろに寄る

## 4. Primary endpoint

各塔・各折りの **val mAP**（`conventions#eval_recipe` の検出 recipe）。折り A は 3 seed の平均と SD。副次に AP rare（長尾クラス）。

## 5. 判定規則

1. 選定は行わない。両塔を確定する
2. 折り A seed 42 の D\*-COCO と凍結源の差が **1 mAP 以内**なら再現。**1 を超え 3 以内**なら続行して差を記録し、報告に理由の候補（TF32、非決定性、処方の細部）を書く。**3 を超えたら停止**し、処方の差分を提示する
3. test は確定した両塔について折りごとに一度だけ評価し、test アクセス台帳に記録する。合計 10 回

## 6. 対照

- 処方の照合: 凍結源の config と本契約の config の差分を機械で取り、TF32 の設定以外が 0 項目であることを示す
- 折り表の照合: 各 run の train・val・test の画像集合を動画 ID に戻し、規約の表と集合差 0
- 陰性対照: 折り A の test 動画を一本入れ替えた注釈で照合が差 1 を返すことを一度示す

## 7. 停止条件

- 再現が 3 mAP を超えて外れる → 停止
- ImageNet 初期化が発散・非数 → 停止し記録を提示
- 1 run が 12 時間を超える → run 数の見直しを諮る
- 装置が使われている → 停止

## 8. 予測外れの記録

§3 の 4 項目の当たり・外れを RESULT に書く。外れは F に「予測外れ」として残す。

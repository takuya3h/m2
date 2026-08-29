# A4 既存信号のクリップID識別プローブ（記述統計）

**判定に変換しない。** 識別率と偶然水準の対だけを示す。

## 手続き

- 入力: 保存済み特徴（再抽出はしていない）
- 学習と評価: **既存の分割ファイルの train 内**を frame_id 昇順で偶数番目/奇数番目へ決定的に二分
  （val/test は動画単位で分かれておりクリップIDが train と重ならないため、
   **分割の再定義を避けて** train 内で測った）
- 分類器: `LogisticRegression(max_iter=1000, random_state=42)` + `StandardScaler`。GPU 不使用
- 偶然水準: 1 / クラス数（クラス = クリップID）

## 結果

| 信号 | 次元 | クラス数 | 学習フレーム | 識別率 | 偶然水準 | 比 |
|---|---|---|---|---|---|---|
| region-token (relation_detr_augstrong_seed456) | 3840 次元 | 13 | 4829 | **0.9712** | 0.0769 | 12.6× |
| 在否 (oracle_toolpresence) | 15 次元 | 13 | 4829 | **0.6319** | 0.0769 | 8.2× |

## 出所

| 信号 | ファイル |
|---|---|
| region-token | `data/processed/t1a_regiontoken/relation_detr_augstrong_seed456/train_regiontoken.npz`（`region`: 9657×3840 float32） |
| 在否 | `data/processed/oracle_toolpresence/train_oracletool.npz`（`signal`: 9657×15 float32） |

**特徴の再抽出は行っていない。保存済みのものを読んだだけである。**

## この数値の扱い

**「指紋である／ない」の判定に変換していない。** 識別率と偶然水準の対を出すところまでが本項目の範囲。
判定則は方針側の作業である。

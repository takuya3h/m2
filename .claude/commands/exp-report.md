---
description: 指定した実験フォルダの metrics / per-class AP / notes / confusion を要約する
argument-hint: <実験フォルダ名 or パス> (例: s0_004_varifocanet_bbox_seed42)
---

実験フォルダ `$ARGUMENTS` の結果を要約します。

手順:

1. `experiments/` 配下から該当フォルダ（部分一致可）を特定する。
2. 以下を読み取り、簡潔に要約する:
   - `config.yaml` — 主要な実験条件（backbone / detection_head / epochs / seed / 長尾対策）
   - `metrics.json` — mAP / mAP_50 / mAP_75 / AP_rare / AP_common 等
   - `per_class_ap.json` — 15 クラスの AP。**最高 3 クラスと最低 3 クラス**を抽出
   - `notes.md` — 仮説・解釈の記入状況
   - `visualizations/confusion_matrix.npy` — 存在すれば形状類似ペアの混同傾向
   - `git_commit.txt` — どのコード状態の結果か
3. 「条件 → 結果 → 気づき」の順でまとめ、稀少クラス（Skewer/Syringe/Forceps）の
   AP が特に低い場合はその点を明示する。
4. 数値はファイルの実測値をそのまま用いる。

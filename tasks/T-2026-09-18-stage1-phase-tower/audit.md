# S4 参照と開始材料の監査

## S4 参照値の確定

旧 S4 参照は run 001（seed42）・002（seed456）・003（seed123）を採用する。契約本文と docs/experiment_log.md:411 が明示する当初の3 runであり、性能を見て選び直したものではない。

| seed | val accuracy | val macro Jaccard |
|---|---|---|
| 42 | 0.9023102310231023 | 0.6569478711055682 |
| 456 | 0.8957095709570957 | 0.6286106389366275 |
| 123 | 0.8976897689768977 | 0.6486607763266027 |

| 指標 | 平均 | 母標準偏差 (ddof=0) | 標本標準偏差 (ddof=1) |
|---|---|---|---|
| accuracy | 0.8985698569856986 | 0.0027656336831631398 | 0.0033871956696018865 |
| jaccard | 0.6447397621229328 | 0.011896230384401817 | 0.014569847152188916 |

旧記載 0.6447 ± 0.0146 は平均と標本標準偏差を丸めたものとして再現できた。既定の pstd は 0.011896230384401817。標本標準偏差と混同しない。

保存された per_class_ap.json は本群では F1。val manifest の GT 存在7クラスに対して F1/(2-F1) を平均した。macro F1 が metrics.json と 1e-12 未満の差で一致することも確認。GT不在クラスを含む9クラス平均では保存 macro F1 に一致しない対照を確認した。checkpoint 推論による再評価は未実施。test 指標は読んでいない。

runindex の該当実験は17 runを含み、旧3 runには Jaccard のキーが無い。残る14 runの平均・母標準偏差を再計算すると索引の 0.6321606095182377 / 0.021544225014892025 と一致した。よって差は集計対象の相違であり、旧値の誤記ではない。この14 run集計を3 seedの基準値に代用しない。

phase_jaccard → jaccard は tools/harvest_runindex.py:normalize_metric_key の正規化。以前の「対応未確定」は本調査で解消。集計処理 build_experiments は各 run の非欠損値を _agg へ渡す。索引・元run・事前登録は変更していない。詳細と入力SHA-256は s4_reference_audit.json。

## Task A の材料

- プロジェクトのサーバー名 ilya（OS hostname aolab）。RTX 6000 Ada 2枚、確認時 compute プロセス0件。学習開始直前の再確認は必要。
- 開始時点の分岐は feat/stage1-phase-tower。phase0 ではない点は原契約からの逸脱。
- 追加17–22の工程注釈は実在。data/raw と data/external の画像接頭辞探索と動画ディレクトリ名探索で画像候補は0件。探索範囲外の画像の有無はUNKNOWN。
- 既存15動画のmanifest: train 9657、val 1515、test 4265フレーム。参照画像の欠損はすべて0件。test は所在確認のみで推論・指標評価なし。
- 利用者承認の例外によりP*-15で続行可能。P*-21はUNKNOWN。Stage 2の主分母P*-21のため追加6動画の画像を使えるようにする別契約が必要。P*-15の選定recipeをP*-21へ適用する。
- 候補Cの平滑化重み2水準、同点規則の所要時間の許容差は未確定で、利用者に照会中。学習・特徴抽出は未開始。
- .sync-pause は開始前から存在し、この調査では変更していない。

## Task B〜E の実測（学習・選定・test を行ったあとの追記）

上の「学習・特徴抽出は未開始」は追記時点より前の状態である。書き換えない。

### 特徴抽出

凍結 ImageNet-1K ResNet-50 の C5 GAP 2048 次元。二度の抽出で要約値が一致
（`63cd91453b76bc8f28118494893ec59ce369a2f0e1175335cf4d0bab21de2d81`）。フレーム数 15437 が
manifest と一致し欠損 0。陰性対照は重みの差し替えと manifest から 1 動画の削除の 2 件で、
ともに検出した。大きさ 127016156 バイト、所要 91.09361817780882 秒。
**15 動画分のみである。** 追加 6 動画の画像が無いため 21 動画分にはなっていない。

### 学習格子

10 構成 × 7 run = 70 run が完走。欠落 0、重複 0（config.yaml の `candidate`・`layers`・
`smoothing_weight`・`history`・`fold`・`seed` の 6 つ組で照合）。線形対照 1 run と特徴抽出 1 run を
別に持つ。71 の train run すべてで、train・val・test の動画集合が `conventions#folds` と集合差 0。
陽性対照として 1 run の test を 07→11 に差し替えると差が出た。

### 選定

`validation_recipes.csv`（10 行）に規則を機械で当てた。最良 C/L8/w0.15（0.33280）と
次点 C/L8/w0.30（0.32891）の差 0.003889677441420769 は最良の折り A seed 間 pstd
0.09595915486783717 以内、所要時間比 1.0509 は ±20% 以内で、修正条項の同点規則
（候補 A>C>B、受容野の短い方）も同一候補・同一受容野のため決着しなかった。
事前登録 §6.3 に従い停止して諮り、平滑化 0.30 を確定。

選定が test に依存しないことの根拠は 3 つ。表の 19 列に test 由来の列が 0 列。
`selection.json` の作成 16:10:45 が最初の台帳 16:11:02 より前。学習経路 `stage1_ptower.train` が
`load_fold(cfg)` を既定の `parts=("train","val")` で呼ぶ（実装で確認）。

### test

確定塔 C/L8/w0.3/h30 の 5 折りのみ、各 1 回、計 5 回。台帳 `test_access_{A..E}.json` は
`open("x")` で作るため、二度目の評価は台帳の衝突で止まる（陽性対照で `FileExistsError` を実測、
台帳 269 バイトは無傷）。5 折り平均 test macro Jaccard 0.22471876589180543、
frame accuracy 0.54535、折り間 pstd 0.06162368547190434。

### 検査

`make forbidden-check` は `contract.allow_write` の宣言前に status fail・違反 672 件で落ちた
（内訳: 新 run 配下 577、runindex 77、出力先 18）。`["experiments/phase1/stage1_ptower", "runindex/"]`
を宣言して status pass・違反 0・許可 672 になった。上限に触れた宣言（rejected_allowances）は 0 件。

試験は `origin/phase0` の worktree で開始前 6 失敗 536 通過を実測し、終了後は 6 失敗 558 通過。
失敗の内訳も同一（test_engines 1 / test_fetch_task 1 / test_research_logger 4）。
`tests/` `src/` `tools/` は `origin/phase0` と差分 0 であり、失敗はいずれも本契約と無関係である。

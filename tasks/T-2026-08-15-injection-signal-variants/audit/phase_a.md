# Phase A — いま選べる形の実測（G1）

## 環境と現在値

| 項目 | 実測 |
|---|---|
| 分岐 | `feat/injection-signal-variants`（`origin/phase0` = `f93b247` 起点） |
| `.sync-pause` | 設置済み |
| python | `.venv/bin/python` |
| conventions | `d422b08`（契約の記載と一致。置換不要） |
| runindex 最終 commit | `592a4e1`（契約の記載は `44697d9` だが、`created_from.counts` の index 791 / experiments 217 は現状と一致。**記載の commit だけが古い。** 逸脱として記録） |

## 設定の `signal` が受け付ける値（実装から読んだ）

**受け付けられる値は存在しなかった。`signal` キーは実装のどこからも読まれていなかった。**

| 確認 | 実測 |
|---|---|
| 分岐している箇所 | **無い。** `forward` は `torch.sigmoid(grasp_logits).detach()` を直書き（修正前の `grasp_inference_injection.py:112`） |
| `build_component_cfg` が渡すキー | enabled / arm / input_dim / hidden_dim / num_classes / num_phases / temporal のみ。**signal は含まれない** |
| 既定の値 | 事実上 `predicted_sigmoid` 相当（直書き） |
| 未知の値を与えたときの挙動 | **どんな値でも黙って無視される**（読まれないため）。「黙って既定になる」欠陥の最強形 |

前の実験の設定にあった `signal: predicted_sigmoid`（inj）と `signal: zeros`（ctrl）は
**注釈にすぎなかった。** 実挙動は `arm` で決まっており、記述と挙動の一致は偶然である。

**直した。** モデルが `signal` を読み、未知の値は `ValueError` で落ちる
（`SIGNAL_MODES` に無い値を拒む）。既定は `predicted_sigmoid` で挙動不変。

## 足す必要のある形（G1 確定）

| 形 | 既にあるか | 判定 |
|---|---|---|
| 正解（oracle） | **無い** | 足す |
| 押しつぶす前（raw_logits） | **無い** | 足す |
| 揃えた値（standardized） | **無い** | 足す |
| 段階を分ける（staged） | **無い** | 足す |

**四つすべてを足す。** Phase B は検査だけでは済まない。

## 教師を引ける経路と、教師の無いフレームの扱い

| 確認 | 実測 |
|---|---|
| 学習中に教師を引く経路 | ある。`load_clips` が `load_grasp_target_index` で教師と有効フラグを clip ごとに返し、`_batch` が `(x, phase_y, grasp_y, grasp_mask)` を渡す。**そのまま使える**（forward へ渡す引数を足すだけ） |
| 教師の無いフレームの扱い（既存） | `grasp_mask` で **損失から除外**されるのみ。信号側は従来 sigmoid 予測が流れていた |
| 教師の無いフレームの実測 | **学習側 301 枚**（教師つき 9356）、測る側 1 枚（1515−1514）。SPEC の 460 枚（2.98%）は全 split 合算とみられる。test 側は本契約では数えていない |

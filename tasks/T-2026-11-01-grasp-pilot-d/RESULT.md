# RESULT — T-2026-11-01-grasp-pilot-d（非公式の測定。関門と設計の判断に使わない）

ホスト bengio、分岐 `feat/grasp-pilot-d`、起点 origin/phase0 ebc35d7b。全値は `experiments/analysis/grasp_pilot_d/REPORT.md`、命令と出力は `audit.md`（以下「audit §」）。

## 1. 判定

**status: pass**（3 腕が回り、§8 の a〜i を実測で埋めた。h の `forbidden-check` は並行する二本目の未追跡の出力だけで fail。§2 の h）

| 関門 | 判定 | 実測 |
|---|---|---|
| G1 | pass | 本契約以外の compute 0 件。bengio main の Relation-DETR は andrew と違い（127 vs 142 ファイル）、重ねの BODY が andrew と全 155 ファイル・パッケージ 72 個で一致。COCO の重み 2d2c19a7…（andrew と同じ）（audit Task A） |
| G2 | pass | 塔単独の val: overall 0.7273450248・標的群 0.7950748009（記録との差 0、< 1e-7）。別 seed 123 は標的群 +0.0284 で許容差を超える（audit Task B） |
| G3 | pass | 重み 0 で頭の無い経路と全項・合計が差 0.0（4 batch）、0.3 で 全損失 − 検出の損失 ≈ 0.3 × CE ≠ 0、頭の勾配 0 / 正、対応づいた枠 = 正解の枠、COCO の読み込みで要約値が変化（audit C-2） |

## 2. 完了判定（SPEC §8）

| # | 期待 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 分岐・起点・未追跡 5 件・compute 0 件・空き 1,445,682,802,688 B・失敗 11+1 件の名前・Relation-DETR と venv の照合・COCO の sha256・電力 220 W × 2（RTX A6000） | 列挙は自分のシェルを含む zsh 8 件、存在しない経路で 0 件。中身の照合は 1 ファイル変えた写しで不一致 |
| b | 再現と処方 | 差 0。lr 低下 epoch 9 の後、15 epoch、2 GPU × batch 2、最良 10（記録のログから） | seed 123 で標的群の差 +0.0284 |
| c | 補助の頭 | 重み 0 で一致、0.3 で入る、主経路だけ（特徴のフック 2 回の 1 回目・末尾 900）、COCO を読んだ | 0.3 で差 0.351〜0.388。COCO の経路を存在しない経路にすると読み込みの行と記録が消える |
| d | 標的 | sha256 一致 6c41a912…、欠け 0・余り 0、和が 1 を超える 11 枠を和で割った（利用者の決定）、枠が一つの画像 575、元に戻った割合 0.2997 | 1 バイト反転の写しで不一致。恒等の並べ替えで割合 1.0 |
| e | 3 腕 | 同じコード（要約値一致）、lr 1e-4 → epoch 10 から 1e-5、15 epoch、最後の状態。epoch ごとの記録は REPORT §3 | 設定の差分は重み・標的の経路と run ごとの置き場・ポート・GPU 番号だけ（REPORT §1） |
| f | 記述 | REPORT §2・§4 | 保存した予測から計算し直した値が 3 腕で記録と一致 |
| g | test 不使用 | 通した動画 train 10 本と val {09,10}、{04,05,07} との共通 0 | 04 を混ぜると 1 件 |
| h | 書き込みと試験 | bengio main と重ねの BODY の Relation-DETR、重み、注釈、工程塔の材料の要約値が開始時と一致。venv の一覧 9c7be5c9…・a74c9c78… が一致。試験の失敗の名前の集合は同じ（11 failed・1 error）。`forbidden-check` は fail（違反 9 件はすべて二本目の `grasppilot2_*`・`grasp_pilot_g` の同期で届いた未追跡ファイル） | 本契約の新しいファイル 187 件が許可の一覧に名前で出る |
| i | PR | #275、Draft でない、base phase0 | 分岐名 `feat/grasp-pilot-d`（`gh pr view 275`） |

## 3. 実測

- 再現: G2 のとおり。処方: 記録 `stage1_dtower_r2/dcoco_foldA_seed42`（audit B-2）
- GPU の使い方: 1 腕 = GPU 1 枚・batch 2・ため込み 2。電力の上限 220 W。所要 10:26:00（なし）・10:16:49（G）・10:05:05（入替）
- val（最後の状態）:

| 腕 | overall mAP | 標的群 AP | 陰性対照群 AP |
|---|---:|---:|---:|
| 補助損失なし | 0.7227621 | 0.8165308 | 0.6728241 |
| G を教師 | 0.7265707 | 0.8149187 | 0.6737715 |
| 入れ替えた教師 | 0.7263878 | 0.8242032 | 0.6741003 |
| G − なし | +0.0038087 | −0.0016121 | +0.0009474 |
| 入替 − なし | +0.0036257 | +0.0076724 | +0.0012763 |
| G − 入替 | +0.0001829 | −0.0092845 | −0.0003288 |

- 補助損失（重みの前、epoch 0 → 14）: G 0.6007 → 0.5115、入替 0.6160 → 0.5698。予測 §6.3 は 2 件とも当たり（REPORT §5）
- 1 本ずつの差。動画ごとでは G − なし が 09 で +0.0090、10 で −0.0061

## 4. 追加の測定（利用者の指示。`meta.amendments` の 1 件目。全値は `experiments/analysis/grasp_pilot_d/extra/REPORT.md`）

- 一本目の正解の腕を seed 123・456（bengio）で回し、seed 42（andrew、一本目）と並べた。Δ塔は bengio の塔単独との差
- 案 B（4 epoch）: overall mAP の Δ塔 +0.0084730〜+0.0092627、標的群 AP の Δ塔 +0.0152653〜+0.0156591（3 seed の最小〜最大）
- 案 A（4 epoch）: macro Jaccard の Δ塔 +0.0028222〜+0.0058387
- 案 B seed 42 の 12 epoch（bengio）: overall mAP は 4・8・12 epoch 目で 0.7363979・0.7370089・0.7347534
- 全 run で学習前の出力が塔単独と同値。seed 42 だけホストが違い、ホストをまたぐ差を処置の差として読まない

## 5. 起票者の誤り

- asserted_without_measuring: §5 D-2 は「q の 4 値の和が 1 であることを確かめる」とするが、二本目の q は なし = 1 − min(Σr, 1) で作られ、Σr > 1 の 11 枠で和が最大 1.538。和が 1 を前提に書かれた手順のとおりでは照合が落ちて止まる
- asserted_without_measuring: §2 は評価の入口に `scripts/eval_relation_detr_map.py` を挙げ「checkpoint は絶対経路で渡す」と書くが、この台本は自分の位置から `third_party/Relation-DETR` を引く。bengio で使うと andrew と違う main の中身で評価する。重ねの BODY を指せる `pd_eval.py` を使った
- check_does_not_check: §5 E-1 と §8-h は `make forbidden-check` の合格を求めるが、検査は未追跡のファイルを数え、並行する二本目の出力が同期で届くと本契約の操作によらず fail する。本契約のファイルの検査としては働かない形になる

## 6. 逸脱

- 記録との処方の違い: GPU 1 枚・ため込み 2（warmup が更新 500 回で終わる、損失の正規化が違う）。学習の長さは低下の位置と epoch 数に固定（SPEC どおり）
- 利用者の決定: 反転で q の左右を入れ替え。和が 1 を超える 11 枠を和で割る。追加の (c) は最後まで回す
- 利用者の指示（meta.amendments）: 追加の測定。`run_pd_grasp.sh` と `pd_grasp_finalize.py` に環境変数の上書きを足した（既定は不変）。案 A の W&B は利用者の決定で手元だけに記録（仮の資格情報の値、外部送信なし）。止まった空のフォルダ 2 つは版管理の外へ移した
- 利用者の指示: 標的が届くまでのダミーの負荷を用意した。目録が bengio の run の終わる前に届いたので、一度も起動していない
- W&B を使わなかった（§7.11）。Relation-DETR は重ねの BODY（前例 handoff_bengio §6）を読むだけで使った
- 確かめの台本の不備を 4 回直した（python の種、no_grad、倍精度の和、sha の対照で同じバイトを書いた）。実装は変えていない（audit C-2・D-1）

## 7. 想定外・UNKNOWN

- 記録の検出塔のホストは記録に無い（UNKNOWN）
- `index.lock` が commit のとき 2 回残っていた（数秒で消えた。作った処理は UNKNOWN）

## 8. 送出

- PR: #275（Draft でない、base phase0、分岐 feat/grasp-pilot-d）
- `make task-report` の終了コード: 0（verdict pass、n_issuer_defects 3、report_sha256 46d15adf…a6e5、7,906 B、2026-11-01 22:5x JST）

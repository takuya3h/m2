# 結果 — T-2026-10-19-stage2-pilot-four-new-types

**非公式の測定。関門の判定と設計の判断に使わない。** 前回（T-2026-10-18-stage2-pilot-folda）と直しの契約（T-2026-10-19-stage2-pilot-fix-epoch4-shuffle）と同じ条件
（折り A、seed 42、4 epoch 目の状態、6 腕）で、提案カードの四つの型（工程から検出の decoder-xattn・extra-queries、検出から工程の logit-correction・tool-history）と
tool-history のゲートなし版を回した。全値と §6.2 の記述は `experiments/analysis/stage2_pilot_four/REPORT.md`。命令と出力は `audit.md`（andrew の分は `audit_andrew.md`）。
利用者の承認による逸脱は `spec.yaml` の `meta.amendments`（8 件）。

**status: pass。** G1〜G3 は pass。run の表の 31 本（PD 12、DP 18、K3 の GRU 1）がすべて固定の長さで回り、型ごとのホストは一つ
（decoder-xattn は andrew、ほかは bengio）。decoder-xattn は正解の腕で標的群 AP の Δ空 +0.0051・Δ入替 +0.0055、予測-noCF で +0.0006・+0.0010、
層ごとのゲートは 4 epoch 目で ±0.04〜0.12 まで開いた。
extra-queries は 6 腕とも 4 epoch のすべての時点で塔単独と同じ値で、追加の出力は最終の上位 300 に一件も入らなかった（スコアの定数は −10 → −9.44〜−9.50）。
tool-history のゲートは開かず（4 epoch 目の tanh(α) 0.005〜0.012）、空以外の 5 腕は予測した工程が同じだった。ゲートなし版は空の腕でも塔単独より Jaccard が 0.082 下がる。

## 1. 解決された参照

| 記載 | 解決先 |
|---|---|
| `contract.inject_verbatim` | `context/conventions.md` の 7 節（prohibitions、issuer_cautions、env_p0、folds、split、eval_recipe、det_groups）を、起票時の版 5c0eaeeb の原文で適用（audit「A-6」） |
| `contract.conventions_rev` | 起票時 5c0eaeeb。起点（直しの分岐の先頭）では最新が b12eda6c で 5c0eaeeb は祖先でなかった（7 節で違うのは folds の追加動画の記述だけ）。差し替えず、phase0 の merge の後に測り直して 5c0eaeeb と一致（audit「A-6」「phase0 の取り込み」、amendments 6 件目） |
| `meta.created_from` | runindex 起票時 31af81e7 → 前回と同じ読みで 63ae65da（内容は同一、差し替え）。件数 1961 / 750 / 1506 は一致 |
| 塔単独の値（SPEC §2） | 工程 Jaccard 0.7762186、検出 mAP 0.7273450 を bengio（両塔）と andrew（検出塔）で再現（差 0.0） |

## 2. 関門

| 関門 | 判定 | 実測 |
|---|---|---|
| G1（A の後） | **pass** | 分岐 `feat/stage2-pilot-four-new-types`、起点は直しの分岐の先頭 a7a5aa67（amendments 2 件目）で直しの道具が在る、bengio の本契約以外の compute プロセス 0 件、空き 879,879,020,544 B、失敗の名前 9 件（audit「A」） |
| G2（B の後） | **pass** | 材料 18 本が両契約の記録と一致、塔単独の val を bengio で再現（差 0.0、標的群 −1.1e−16）、B-3: 既定の集計の道具が直しの契約の report.json を 5c89f5d2 とバイト単位で同じに再現（audit「B」「phase0 の取り込み」） |
| G3（C の後） | **pass** | 五つの界面の全腕（DP 18、PD 12）で学習前の出力が塔単独と差 0、陽性対照で変わる、extra-queries の元の query の出力は界面の重みによらず差 0 で mask を外すと変わる、学習前の上位 300 は全 val 画像で塔単独と同じ、既存の型の照合が直しの契約の記録と全項目一致、test の動画との共通 0 件（audit「C」） |

## 3. 完了判定

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | 分岐・起点・直しの道具（起点に在り phase0 に無い）・退避 0 件・bengio の compute プロセス 0 件（andrew は audit_andrew の S1 で 0 件）・空き・失敗の名前 9 件（audit「A」） | 目印の bash を 1 件、存在しない exe で 0 件。存在しない道具の名前は ABSENT |
| b | 材料 | 本契約が読む 18 本の sha256 が直しの契約の版管理下の記録と一致。andrew から写した 32 本を含む 44 本が andrew の値と一致（audit「入力の写し」「B-1」） | 1 バイト変えた複製で不一致 |
| c | 塔単独の再現 | bengio: 工程 Jaccard・accuracy、検出 mAP・群 AP とも差 0.0（標的群 −1.1e−16）。andrew: 検出塔の mAP・群 AP が bengio と全項目一致（audit_andrew「0」「S4」） | 別の時間ヘッドで Jaccard 0.6379、seed 123 の検出塔で mAP 0.7289 |
| d | 実装 | 五つの界面（DP は `dp_model.py`・`dp_train.py`、PD は新しい `pd_four.py`）。学習する名前の集合が全腕で界面のパラメータの全部と一致。既存の型（PD の P3・P1、DP の 5 型）が直しの契約の記録と全項目一致、既定の経路の試験 10 passed、既定の集計が直しの report.json と同値（audit「C-1」「C-5」「phase0 の取り込み」） | 界面の外のパラメータを一つ混ぜた集合で不一致（全腕） |
| e | 恒等性と対照 | 全 30 腕で学習前の出力が塔単独と差 0。extra-queries の元の出力は 6 腕とも差 0、界面の重みを乱数にしても差 0（audit「C-5」） | ゲート・零の層を零でない値にすると変わる（DP ロジット差 0.00024〜0.229、decoder-xattn score 差 0.0070）、mask を外すと元の出力が変わる（score 差 0.564）、スコアの定数を 0 にすると最終の検出が変わる |
| f | 見落とし | train 73 / 32,272（クラスごと・閾値 {0, 0.01, 0.05, 0.1, 0.3, 0.5} ごとの数は audit「C-4」）、val 78 / 4,707 | ただ一つ覆う検出を消すとその正解が見落としに数えられ、正解を検出に入れると 0 件（train・val） |
| g | 殺し実験 | K1 神託の差 overall mAP +0.0208・標的群 +0.0000・陰性対照群 +0.0290、K2 (ii)−(i) Jaccard +0.0118・(iii)−(i) +0.0069、K3 GRU 単独 0.2200・(2) +0.0009・(3) +0.0009。術式の精度は UNKNOWN（audit「D」） | K1 で見落とし 0 件の写しは差 0.0、K2 で正解の工程の one-hot を入れると (ii)−(i) +0.0952 |
| h | 学習 | 31 本すべて固定の長さ（PD は epoch 3、DP は epoch 4 の状態）。型ごとのホストの集合: decoder-xattn {andrew}、extra-queries・LC・TH・TH-NG {bengio}（REPORT「型ごとのホスト」） | 存在しない run の名前を数えると 0 件（集計は名前の型・腕の組に合う run だけを数える） |
| i | ゲートと寄与 | tool-history の tanh(α) と decoder-xattn の層ごとの tanh(α_l) を epoch ごと（REPORT「ゲートの値」）。extra-queries の寄与: 上位 300 の追加 0 件・照合した見落とし 0 個（6 腕） | ゲートの値は学習前に 0（全腕）。スコアの定数を 0 にした学習後の界面では追加 425,322 件・照合 3 個 |
| j | 記述 | REPORT の表（4 epoch 目の値・Δ空・Δ入替・Δ塔・動画ごと・クラス別）と §6.2 の記述、§6.3 の照合 | 表の値を予測（PD 12 本）と事後確率（DP 18 本）から計算し直して差の最大 0.0 |
| k | 中間記録 | DP の全腕と中間記録（02715aaa）、extra-queries（7de70400・630b44f4）、decoder-xattn（andrew の分岐の準備 cf517ee5・起動 00475133・終わり 5d753beb を 7a2cdcc2 で merge）、最終（送出の commit） | 各 commit が遠隔の分岐の先頭の祖先（`git merge-base --is-ancestor`） |
| l | test 不使用 | 各段（DP・K3・PD の run の信号と注釈、見落とし、D\* の train の出力、評価の記録）で {04, 05, 07} との共通 0 件（REPORT と `test_audit/test_audit_final.json`） | `--inject 04` で共通 1 件 |
| m | 書き込みと試験 | `make forbidden-check` violations 0（変更 722 本、すべて許可の内か禁止領域の外）。前回・直しの契約の run・集計・tasks に書き込み 0（保存先は利用者の指示で bengio の写しにファイルを足しただけ）。試験は終了時も 8 failed・862 passed・15 skipped・収集の誤り 1 で、失敗の名前の集合は開始時と同じ（`experiments/analysis/stage2_pilot_four/final/pytest_end.txt`） | 同じ道具が本契約の新しいファイルを変更として拾い、allow_write の許可として分類した |
| n | PR | #243、base phase0、Draft でない（送出の前に外す） | 分岐名 `feat/stage2-pilot-four-new-types` |

## 4. 実測

4 epoch 目の値の差（seed 42、1 本ずつ。全値・動画ごと・クラス別・ゲートの推移は REPORT）:

| 方向 | 型 | ホスト | 空の腕の値 | 予測-noCF の Δ空 / Δ入替 | 正解の Δ空 / Δ入替 | 空の腕の Δ塔 |
|---|---|---|---|---|---|---|
| 検出から工程（Jaccard） | logit-correction | bengio | 0.7687 | −0.0021 / +0.0016 | −0.0032 / +0.0006 | −0.0075 |
| 〃 | tool-history | bengio | 0.7762 | −0.0054 / 0.0000 | −0.0054 / 0.0000 | 0.0000 |
| 〃 | ゲートなし版 | bengio | 0.6947 | −0.0238 / −0.0045 | −0.0234 / −0.0041 | −0.0815 |
| 工程から検出（標的群 AP） | decoder-xattn | andrew | 0.7972 | +0.0006 / +0.0010 | +0.0051 / +0.0055 | +0.0021 |
| 〃 | extra-queries | bengio | 0.7951 | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 |

- ゲート: tool-history の 4 epoch 目の tanh(α) は +0.0050〜+0.0125（ゲートは開かなかった）。decoder-xattn の層ごとの tanh(α_l) は 4 epoch 目で全腕・全層 −0.122〜+0.099（層 1・5 は全腕で正、層 2〜4 は全腕で負、層 6 は正解と予測-CF だけ負）
- 1 本の所要: DP 19〜117 秒、K3 の GRU 数十秒、extra-queries 2.42〜2.72 時間（bengio、1 枚 2〜3 本）、decoder-xattn 3.78〜3.84 時間（andrew、1 枚 3 本）
- 見落とし: train 73 個（0.23%）、val 78 個（1.66%）。SPEC §6.3 の予測は 4 件とも当たり（4 は decoder-xattn の正解の Δ空 +0.0051）

## 5. 起票者の誤り

1. **asserted_without_measuring**: SPEC §4 は空の腕を「すべて 0」とし、分母にした。tool-history（GRU）は入力が一定でも動画の先頭からの経過を内に持てるため、ゲートなし版の空の腕は
   塔単独より Jaccard が 0.082 下がった。指示どおりに読むと、Δ空 は「信号の有無」ではなく「経過の情報を持つ空の腕との差」になる（Δ入替 は影響を受けにくい）
2. **asserted_without_measuring**: SPEC §3.2 はスコアの定数の初期値 −10 を「学習前に上位 300 に入らないため」とし、4 epoch・学習率 5e-4・W1 で上がるかを見積もっていない。
   train の見落としは 73 個しかなく、定数は −9.44〜−9.50 までしか上がらず、6 腕とも学習後も上位 300 に入らなかった。指示どおりに回すと、extra-queries の全腕が塔単独と同値になる
3. **check_does_not_check**: Task C-7 は「1 epoch の短い試走で 1 本の所要時間を測る」としたが、試走の経路（`--smoke`）は 6 歩・val 20 枚で、1 本の所要は測れない。所要は本番の壁時計で測った

## 6. 逸脱

- 利用者の承認・決定による逸脱 8 件（amendments）: 前倒しの開始と手順（/task・task-start・task-release を使わない）、起点、主のホストを bengio に（decoder-xattn は andrew）、
  入力の写しと環境、B-3 の時期、A-6 の扱い、限界の二点、ホストの割り振りと GPU（1 枚 3 本まで）
- 数値精度は規約の precision 節（TF32）ではなく前回の経路のまま（SPEC §2 のとおり）
- 実行者の誤り: 相対経路の `--out` で回した評価 3 本の json が重ねの BODY の Relation-DETR の下に書かれた（移して、作った空のフォルダを除いた。ソースの一覧は不変）。
  引き渡しで bengio の decoder-xattn の試走の置き場を分岐に入れたため、andrew の試走が名前の衝突で写しの場所で回った。zsh の単語分割で起動の命令が二度空振りした（bengio の陽性対照、andrew の起動）
- K3 の試走の run 名に ep4 が付いた（1 epoch の試走。以後は実際の epoch 数を名前に入れた）
- worktree に追跡外の記号リンク `.venv` と `data/processed/phase_manifest` を置いた（どちらも bengio の main を指す。`rm` で戻せる）

## 7. 想定外・UNKNOWN

- K3 の「GRU の最終状態から術式を当てる精度」: UNKNOWN（動画ごとの術式の対応が repo に無い）
- tool-history の空以外の 5 腕は予測した工程が同じ（事後確率は違う）。ゲートの小ささによる
- bengio の試験の失敗は開始時 8 件と収集の誤り 1 件で、andrew の直しの契約の開始時（6 件）より 3 件多い（worktree に版管理外のファイルが無いこと 2 件、ホスト名に依存する試験 1 件）
- andrew の run の `git_commit.txt` は main の作業場所の HEAD を書く（`EGO_BODY` で取るため。audit_andrew「記録の注意」）。bengio の run は `unknown`

## 8. 送出

PR #243（base phase0、head `feat/stage2-pilot-four-new-types`、Draft でない。07:0x JST に Draft を外した）。`make task-report` の終了コード **0**（判定 pass、起票者の誤り 3 件、報告 13,579 B、sha256 `b47dc73cd4911776…`）。`make task-release` は使っていない（task-start を使っていないため。amendments 1 件目）。

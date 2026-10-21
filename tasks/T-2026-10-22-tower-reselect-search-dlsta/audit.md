# audit — T-2026-10-22-tower-reselect-search-dlsta
## 開始と利用者の決定
- 再開: feat/tower-reselect-search-dlsta。開始時 HEAD と origin/phase0 は 39dd92d671466edb7c96edf6c34af34c9c29ef62。追跡下変更 0、未追跡は本契約の SPEC.md・spec.yaml・prereg.md のみ。
- 開始時 .sync-pause は不在。task スキルの再開時例外により task_id と branch の所有情報つきで作成。稼働中 ~/bin/m2-sync.sh の sync-pause は 2 件。
- 利用者は incoming/seed42/best_ap.pth を andrew から追加承認なしで取得してよいと明示。
- agentmemory と CodeGraph は利用可能なツールに無い。planning-with-files の SKILL.md も利用可能なローカル一覧では発見できず。計画は契約の A→B→C→D→E→F を参照。
- prereg の学習前コミット: e9f4e3b4f34410c023c7a4ab240971c1d70c2510、2026-10-22T04:55:13+09:00。学習は未開始。
## L1/L2

```text
OK   T-2026-10-22-tower-reselect-search-dlsta

1 task(s), 0 failed
```
## 1. 解決された参照

索引参照は比較の分母として使用しない（SPEC §4）。以下は CSV 原文。

```yaml
experiment_id: "phase1/stage1_ptower_r3/P15_C_L8_w0.3_h30_foldA_coco_lr0.0001@val"
split: "val"
n_seeds: "3"
seeds: "42,123,456"
jaccard_mean: "0.70683155993455"
jaccard_pstd: "0.015181164464046479"
jaccard_sstd: "0.018593053319093167"
jaccard_n: "3"
sigma_source: ""
```

### 原文 conventions#sigma

<a id="sigma"></a>
## sigma

sigma に関する列は 4 系統ある（backlog B-18）。

1. `{metric}_pstd` / `{metric}_sstd` — seed 間の sigma（母集団 / 標本）
2. `delta_pstd_{metric}` / `delta_sstd_{metric}` — 実験間 paired Delta の sigma
3. `sigma_source` — sigma の系統。値は paired_delta または within_run_seed_spread
4. `delta_sigma_source` — paired sigma の計算方法。値は paired または unpaired_pooled

3 と 4 は直交する（どの sigma を使ったか vs paired sigma をどう計算したか）。

### 既定値（spec.yaml が sigma_policy を省略した場合に継承される値）

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

この既定は暫定である。正本（ddof=0 / ddof=1）は未決定であり、
決定され次第ここを変更する。変更時は過去の task を横断で再判定できるよう、
`RESULT.md` に解決済み sigma_policy が記録されていることを前提とする。

### 判定規約の表記

判定規約を `spec.yaml` や `prereg.md` に書くときは、絶対値を `abs(...)` の関数形で書く。
縦線による絶対値記法は markdown 表のセル区切りと衝突し、表を壊すため使わない
（backlog B-33 と同型の事故）。

    正: abs(delta) / sigma >= 1 かつ 全 seed 同符号
    誤: 縦線で delta を囲む記法

同じ理由で、区切りを表したいときは `/` かスラッシュ区切りの語を使う。


### 原文 conventions#prohibitions

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |


### 原文 conventions#issuer_cautions

<a id="issuer_cautions"></a>
## issuer_cautions

**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**

| # | 注意 |
|---|---|
| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 2 | 一致 0 件なら別の異質な方法でも確認する |
| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
| 4 | 仕組みの挙動は実装を読んでから信じる |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
| 7 | **丸めた表示を実数として扱わない** |
| 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
| 9 | 無変更は要約値で確かめる。表示属性では足りない |
| 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
| 11 | 測定の副作用が禁止領域へ触れないか確かめる |
| 12 | **判断の前に、いま見ているものが最新かを確かめる** |
| 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
| 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |

**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
確かめると 3 件とも実在した。

**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
（自分の命令行にその語が含まれるため）。

**注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。

**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。


### 原文 conventions#proposal_gate

<a id="proposal_gate"></a>
## proposal_gate

手法・結合・補助信号・修正案の提案は、本節の関門を通ったものだけを契約に落とす。
関門は四つ。提案カードの充足／禁止語の不在／失敗時手順の履行／引用の照合。

### 提案カード（全項目が埋まるまで推奨を書かない）

| # | 項目 | 空欄を許す条件 |
|---|---|---|
| 1 | 問い。yes/no で答えが出る一文 | 許さない |
| 2 | 最も近い先行研究三件。著者・年・DOI か arXiv ID・設定・報告された効果量 | 三件未満なら「探して見つからなかった」と検索語を書く |
| 3 | 先行研究がこれをやらなかった／効かなかった理由の推定 | 許さない |
| 4 | 否定的な先行研究二件（効かなかった、負の転移の報告） | 同上の「探して見つからなかった」 |
| 5 | 期待効果量（点）。#2 のどの値から外挿したか | 許さない |
| 6 | 成功確率（主観。0.0 から 1.0） | 許さない |
| 7 | 成功の閾値（主判定規則で書く） | 許さない |
| 8 | 失敗の閾値と、失敗時に捨てるもの（案／設計／問い のどれか） | 許さない |
| 9 | この案を殺せる最安の実験（GPU 一日以内） | 無いなら「無い」と理由 |
| 10 | 費用（run 本数 × 時間） | 許さない |
| 11 | この案の結果でどの判断（関門・分岐）が変わるか | 変わらないなら提案しない |
| 12 | 最も近い既存研究との差分一文 | 許さない |
| 13 | F の「却下」「予測外れ」と同型でないことの宣言。読んだ行の id | 許さない |
| 14 | 初回にセットで試す設定の掃引集合。掃引する主要因、固定する交互作用、固定の理由 | 許さない |
| 15 | この比較で揃えるべき条件の一覧と、両腕の実測値。conventions#symmetry の表の様式。UNKNOWN は先に測る | 許さない |
| 16 | 差を仮説の効果と読むために排除済みの交絡の一覧。排除していない交絡があれば、その影響の向き | 許さない |

#5 #6 #10 は数値で書く。#10 は #14 の掃引集合全体で見積もる。
#11 が空なら、新規性の有無によらず提案から外す。

#15 の表に UNKNOWN が残る提案は、契約にせず先に調査契約を出す。

### 禁止語（提案と契約の本文。完全一致で検査する）

最大の新規性／世界初／画期的／有望／筋が良い／本命／未踏／空白／決定的／確実に効く／
明らかに／大幅／劇的／必ず改善／唯一の

「未踏」「空白」を使う場合は禁止を解かず、「空白である理由の仮説（技術的困難／価値が無い／偶然）」を
添えた別の語で書く。形容詞の代わりに #5 #6 #10 の三数値を併記する。

### 設定・設計・問いの三水準

| 水準 | 含むもの | 変えるときの手続き |
|---|---|---|
| 設定 | 学習率・epoch・batch・seed、特徴の取り出し層、豊かさ L0 から L3、学習範囲 W1/W2、損失の重み、送り手の掃引点 | 初回の契約に掃引として入れる。後から足さない |
| 設計 | 界面の型、塔の選択、方向、信号の種類、時間文脈の与え方 | 提案カードを書き直し、批判会話を通す |
| 問い | どの仮説を測るか、相互改善の定義、論文の段 | 利用者が決める。関門で扱う |

設定の掃引は初回にセットで試す。主要因は掃引し、交互作用は固定する。
何を固定したかと理由をカード #14 に書く。掃引集合はカードに書いた時点で固定する
（最良格子の選定は折り内 val、test は腕ごとに一度。conventions#split の規則に従う）。

### 失敗時手順（修正案を書く前に、この順で書く）

1. 失敗の定義は初回の契約にある閾値による。掃引のどの格子でも閾値に届かなければ、
   その設計の失敗である。格子を足すことは修正ではない
2. 原因候補を五区分で列挙する。測定器（eval・split・seed）／データ（ラベル・分布）／
   モデル・実装／仮説そのもの／問いの立て方
3. 区分ごとに識別実験を一つ書く（どの結果が出ればその区分だと分かるか）
4. 識別実験の結果で修正の水準を決める。測定器・データ・実装が原因なら、それを直して
   同じ設計を測り直す（設計は変えない）。仮説・問いが原因なら、設計か問いを変える
5. 設定水準の修正は選べない。例外は、初回に入れなかった設定があり、入れなかった理由が
   契約に書いてある場合のみ。その場合も後から足さず、掃引を再設計して一括で出す
6. 修正案に提案カードを付ける。設計変更一回の費用を #10 に含める

### 引用規約

- DOI か arXiv ID の無い引用は引用として扱わない
- 引用は機械で存在照合する。照合の出力を証跡に残す
- 数値つきで引く。「改善した」ではなく「指標・値・表番号・設定」
- 設定の違い（データセット・タスク粒度・入力）を必ず書く。「文献に数値がある」を「効く」と読み替えない
- 反証を先に探す。検索語・件数・見つかった否定例を記録する

### 役割分離

| 役割 | 会話 | 出力 | 禁止 |
|---|---|---|---|
| 生成 | 別会話（プロジェクトの外）。証拠地図・カードの雛形・依頼文だけを渡す | 提案カード三から五案。互いに排他的な方向 | 推奨・順位。repo の現状を見ること |
| 批判 | 別会話。カードだけを渡す | 却下表と順位。順位は期待情報量（#11）で付ける | 生成側の推奨文を読む |
| 判定 | 利用者 | 決定。F に一行 | — |
| 起票 | 別会話 | 契約 | 手法の変更 |

生成と批判を同じ会話で行わない。批判は「やらない理由」から書く。

### 置き場と参照（2026-09-23 追加）

- 提案カードは docs/proposals/YYYY-MM-DD-slug.md に置き、tools/check_proposal.py を通す
- 生成会話は候補を三案以上出す
- 批判会話は web 検索を必須とし、検索語と件数と見つかった否定例を却下表に書く
- exp 契約は spec.yaml の intent.proposal_card にカードの経路を書く。L3 の P14 が、カードの実在と検査の通過を確かめる。
  無い exp は起動できない
- 導入前の契約（T-2026-09-19-stage1-detector-towers-r2、T-2026-09-19-stage1-phase-tower-r3）は例外。三件目を足すときは本節を改訂する

### 生成会話への依頼文（2026-10-19 追加）

- 書いてよいものは二つ。F で状態が「有効」の決定の結論（行の日付を付ける）と、M の問い・判定規則。
- 書かないものは次のとおり。実測値、実装の状態、決定の理由のうち実装や実測に触れる部分、旧カード、報告者の解釈。
- 決定ごとに、どこまで縛るかを書く。カードの候補として開いているものも書く。
- 依頼文は渡す直前に F を読み直して、一から書く。前の依頼文を直して使わない。
- 依頼文は docs/proposals/briefs/ に置き、カードから参照する。
- 生成会話は、カード #10（費用）と #15（両腕の実測値）を UNKNOWN と書く。起票者が repo の実測で埋めてから批判会話へ回す。

---


### 原文 conventions#folds

<a id="folds"></a>
## folds

動画単位の 5-fold。**正本は `docs/stage0/A1_fold_table.md`**（契約 `T-2026-09-17-fold-table` が確定）。
本節はその表と同じ値を持つ。数値が食い違ったら正本を正とする。

| 折り | test（3） | val（2） |
|---|---|---|
| A | 04, 05, 07 | 09, 10 |
| B | 01, 03, 14 | 02, 08 |
| C | 02, 08, 11 | 06, 12 |
| D | 06, 13, 15 | 04, 05 |
| E | 09, 10, 12 | 07, 15 |

train はその折りの test と val を除いた 10 本である。
**折り A は公式分割そのもの**（`conventions#split` の test と val に一致）。
各動画は test にちょうど一度現れ、val は全折りを通じて高々一度しか使わない。

### 追加 6 動画

工程の注釈がある追加動画は次の 6 本である。

    17, 18, 19, 20, 21, 22

**22 はフレーム画像が無く使えない。工程塔に足すのは 17〜21 の 5 本で、その塔を P\*-20 と呼ぶ。**
旧称は P\*-21。古い記録の P\*-21 は P\*-20 と読み替える。
出所: 利用者の確認と決定 2026-09-27（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）、
`tasks/T-2026-09-27-stage1-ptower-20/audit.md` の `verify_folds` の記録。

**用途は訓練のみである。どの折りの test にも val にも現れない。**
15 動画との重複 0 件、公式 test との重複 0 件（陽性対照つきで実測。正本の「追加 6 動画」節）。

### 規律

**選定・early stopping・ハイパラ・界面の型の選択は、すべてその折りの val で行う。
test は腕ごとに一度だけ触る。** 折りをまたいで val を使い回さない。

出所: `docs/stage0/A1_fold_table.md`、契約 `T-2026-09-17-fold-table`。

### val と test の重なり

各折りの val 2 本（計 10 本）は、どれもほかの折りの test に現れる。上の表から読める対応は次のとおり。

| val の動画 | val に使う折り | test に持つ折り |
|---|---|---|
| 09, 10 | A | E |
| 02, 08 | B | C |
| 06 | C | D |
| 12 | C | E |
| 04, 05 | D | A |
| 07 | E | A |
| 15 | E | D |

**val に一度も入らないのは 01・03・11・13・14 の 5 本**である。test としては折り B に 3 本（01・03・14）、
C に 1 本（11）、D に 1 本（13）、A と E には 0 本。

val で設定・処方・構造・型・止め方を選ぶ段（両塔の学び直しと Stage 2 以降）では、次の三つを守る。

1. この重なりを prereg と報告に明記する
2. test の値を報告するときは、val に一度も入らない 5 動画だけで集計した値を副次として添える。
   各動画の値は、その動画を test に持つ折りのモデルが出す。集計の仕方は prereg に書く
3. 副次の値は、判定・関門・選定のどれにも使わない

選ぶ規則（規律の小節。その折りの val で選ぶ）は変えない。

出所: 利用者の決定 2026-10-19（契約 `T-2026-10-21-ops-taskstart-resume-folds-val` SPEC §2）、上の折りの表、
`docs/stage1/design_val_subsets.md` 223 行。

---


### 原文 conventions#eval_recipe

<a id="eval_recipe"></a>
## eval_recipe

転記元: `src/egosurgery/utils/eval_recipe.py`。

- `LOCKED_DOWN_TEST_CFG`: `score_thr=1e-8`, `max_per_img=300`, `nms_pre=3000`, `nms_iou=0.6`
- `NMS_FREE_TEST_CFG`: `score_thr=0.0`, `max_per_img=300`, `nms_pre=None`, `nms_iou=None`
- `PHASE_EVAL_PROTOCOL`: `inference_protocol=online_causal`, `jaccard_mode=strict`

比較の三角形および DETR-family の公式評価は NMS-free とする。工程評価は online causal と Jaccard strict を固定する。`select_box_nums_for_evaluation` は転記元で定義されていないため `UNKNOWN（転記元未特定）`。


### 原文 conventions#symmetry

<a id="symmetry"></a>
## symmetry

比較する腕の条件を、起票の前に並べて確かめる。差が出たとき、それを仮説の効果と読めるだけの対称性が
無ければ、その実験は測りたいものを測れない。

### 対象

exp 契約のすべて。比較の類型は三つ。

| 類型 | 腕 | 例 |
|---|---|---|
| 塔どうし | 同じ役割の塔の候補、または方向で対になる塔 | 検出塔 D と工程塔 P、P の候補 A と B |
| 送り手と受け取り手 | 信号を出す塔と受ける塔 | P→D の P と D |
| 腕と分母 | 処置あり と 空入力 | 予測段の界面 と 空入力界面 |

### 表の様式

prereg.md に次の表を置く。列名はこのとおりにする（L3 の P13 が列名で表を探す）。

| 条件 | 腕1 | 腕2 | 判定 | 理由 |
|---|---|---|---|---|

判定は三値。**揃える**／**意図的に変える**／**UNKNOWN**。
「意図的に変える」には理由を書く。理由は次の三つに限る。

1. 仮説の操作である
2. タスクの性質上避けられない
3. **各塔の構造の標準の処方である**（使い方は下の「各塔の構造の標準の処方」に従う）

**UNKNOWN が一件でもある契約は起票しない。** 先に測る。

### 各塔の構造の標準の処方

理由 3 は、塔どうしで最適化の細部を揃えないことを認める。主判定の差（方向ごとの Δ）は、比べる腕と分母が
同じ受け取り手を持つので、塔どうしの最適化の差を含まない。揃えるのは塔の知識の出どころと収束規則である。

| 項目 | 範囲 |
|---|---|
| 使える比較 | 類型「塔どうし」だけ |
| 使える行 | 正規化層の扱い、学習率、勾配の刈り込み、weight decay、実効 batch、数値精度、決定性、入力の縮小規則（短辺の目標と長辺の上限） |
| 使える条件 | その塔どうしの差が、主判定（方向ごとの Δ）に入らないこと。つまり、比べる腕と分母が同じ受け取り手を持つ設計であること。入力の縮小規則の行に使うときは、画面の残る割合（切り出し）が両腕で同じであること |
| 使えない行 | 初期化の鎖の各段、in-domain のデータの範囲、相手タスクのラベルを使わないこと、収束規則、入力の切り出し（画面の残る割合） |

- **同じ塔の変種どうし**（確定塔、交差適合用の塔、診断点の塔）には使わない。変える一点（データか初期化）以外を揃える
- 理由 3 を使った行は、表の理由の欄に「各塔の構造の標準の処方」と書き、両腕の実際の値を書く
- 入力の縮小規則に理由 3 を使うときは、「必ず置く行」の「入力解像度と切り出し」を二行に分ける。切り出しの行は「揃える」、縮小規則の行は「意図的に変える」で理由 3 とし、両腕の実際の大きさを書く
- 実例: 検出塔の評価時の入力は 1333×749（pad 後 1344×768）、工程塔は 800×1422。画面の残る割合はどちらも 100%。前者は `tasks/T-2026-10-17-tower-reselect-prereq/RESULT.md` §4、後者は `tasks/T-2026-09-19-stage1-phase-tower-r3/RESULT.md` 完了判定 c の実測。方向ごとの Δ は同じ受け取り手を持つ腕と分母の差なので、塔どうしの入力の大きさの差を含まない。界面が渡すのは塔の出力であり画像ではない
- 出所: 利用者の決定 2026-10-17（契約 `T-2026-10-17-tower-reselect-prereq` の SPEC §2）
- 入力の縮小規則の出所: 利用者の決定 2026-10-18（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）

### 必ず置く行

初期化の鎖の各段（ImageNet 分類、COCO 検出、中立 SSL、in-domain。段ごとに一行）／凍結範囲／
入力解像度と切り出し（画面の何割が残るか）／前処理・増強／教師の種類と密度／epoch と上限への張り付き／
学習率／実効 batch（単位が違うなら比較不能と書く）／数値精度／ヘッドの容量／ヘッドの epoch／評価 recipe／ホストと装置型。

### ホストと装置型

比べる腕と分母は、同じホスト・同じ装置型で回す。ホストの行は「揃える」以外にしない。理由 1〜3 のどれも使わない。
別のホストの値と比べる必要があるときは、同じ設定を両方のホストで回した対照を置き、対照の差を並べて書く。
対照の無いホストをまたぐ差を、処置の差として読まない。

実測: 同じ設定（P\*-15、COCO、折り A、seed 42）で efros 0.7762、ilya 0.7066、差 +0.0696。
折り A の seed 間の標本 SD 0.0186 の 3.7 倍（`tasks/T-2026-09-27-stage1-ptower-20/RESULT.md` 関門 G2・完了判定 c）。
出所: 利用者の決定 2026-10-06 と 2026-10-17（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）。

### 規則の読み

規則の字面に複数の読みがあるとき、狭い読みを既定にしない。読みの候補を列挙し、利用者に諮る。
実測: 「P の初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、非対称を二周した。

### 出所

T-2026-09-19-symmetry-gate。実例は docs/symmetry-checklist.md。


### 原文 conventions#frame_sets

<a id="frame_sets"></a>
## frame_sets

塔と界面が学習・評価に使うフレームの集合。数は `experiments/analysis/frame_signal_audit/REPORT.md` の実測。

| 用途 | 集合 |
|---|---|
| 工程塔の学習と評価（主測定） | 動画 01〜15 の、工程注釈のある全フレーム（17,233。術具注釈の無い 1,796 を含む） |
| 検出塔の学習と評価 | 術具注釈のあるフレーム（15,437） |
| 工程の値（工程塔単独、D→P の予測段） | 工程注釈のある全フレーム。副次に、両タスクの注釈があるフレームでも出す |
| D→P の参照段（正解、正解と予測）と実現率 | 両タスクの注釈があるフレーム。比べる予測段の値も同じ集合で出す |
| P→D の界面の学習と評価 | 術具注釈のあるフレーム |

### 規則

- 各塔は、15 動画の折り（`conventions#folds`）の中にある自タスクの注釈を、すべて使う
- 追加動画 17〜21 は Stage 2 の主測定に入れない
- P→D の送り手を変えて測る比較に、**術具注釈のあるフレームだけで学んだ工程塔**を診断の一点として置く。関門の判定には使わない
- 出所: 利用者の決定 2026-10-16（契約 `T-2026-10-17-tower-reselect-prereq` の SPEC §2）

### 原文 conventions#det_groups

<a id="det_groups"></a>
## det_groups

検出の co-primary と陰性対照の集合。研究方針 v2 §7.3（2026-06-19 に EDA から事前登録。結果を見て選んだ群ではない）。

| 群 | クラス | 用途 |
|---|---|---|
| 標的群 | Skewer、Bipolar Forceps、Scalpel、Syringe、Raspatory | 検出の co-primary（標的群 AP = 5 クラスの AP の平均） |
| 陰性対照群 | Gauze、Mouth Gag、Suction Cannula、Tweezers | Δ ≈ 0 であるべき群。動いたら交絡を疑う |

- クラス名は検出塔の注釈と完全一致で照合する
- ある折りの評価集合に出現しないクラスは、その折りの群 AP から除き、除いたことを明記する。0 で埋めない
- AP rare（Skewer、Syringe）は副次指標として別に報告する


### 原文 conventions#precision

<a id="precision"></a>
## precision

| 対象 | 精度 | 出所 |
|---|---|---|
| 界面の学習（`train_t1b.py` 系。既定は fp32） | TF32。Tier 1 の全腕（分母の空入力界面を含む）で同じ設定にする | `tasks/T-2026-09-17-amp-compile-timing/RESULT.md`、利用者の決定 2026-09-18 |
| 検出塔のフル学習 | fp16 の autocast。凍結源と同じ。TF32 の採用の範囲に入らない | `tasks/T-2026-09-18-stage1-detector-towers/RESULT.md`、利用者の判断 2026-09-18 |

- `torch.compile` は使わない。compile 系の条件は完走しなかった
- 界面の学習に TF32 を当てる前に、その学習が fp32 で始まることを実測する
- `train_t1b.py --tf32` は `torch.backends.cuda.matmul.allow_tf32 = True` により行列積の TF32 を許す。`torch.backends.cudnn.allow_tf32` は変更せず、実測した既定は True（畳み込み側）。`--amp no` で autocast と GradScaler を作らない。設定は同じ過程の評価にも効く（`scripts/train_t1b.py`、`tasks/T-2026-09-17-amp-compile-timing/audit.md`）
- 計算器は TF32 を持たない。計算器の日数は単精度の値として読む（`tasks/T-2026-09-27-stage2-prep/RESULT.md` §3）
- 工程塔の学習の精度は本節で定めない
- 実測: TF32 は W1 で 1.182 倍、W2 で 1.286 倍速く、主指標の差は 0.030σ（`tasks/T-2026-09-17-amp-compile-timing/RESULT.md` §2・§3）
- 出所: 利用者の決定と訂正 2026-09-18（契約 `T-2026-10-19-conventions-and-defect-records` SPEC §2）、上記三契約の報告

### 原文 conventions#env_p0

<a id="env_p0"></a>
## env_p0

学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
数値が変わったまま完走する。

    source .venv-relation-detr/bin/activate   # 検出系
    source .venv/bin/activate                 # 解析・工程系

拡張のロード確認をログに残すこと。


### 原文 conventions#frozen_source

<a id="frozen_source"></a>
## frozen_source

比較の三角形で認める凍結源は Relation-DETR seed42 完走 checkpoint。
同定パスは `third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth`。
転記元: `docs/experiment_log.md` の STEP 0-2、および `configs/stage/s4_phase_baseline.yaml`。

凍結源を変更してはならない。変更が必要な場合は別 task で判断を記録し、同じ凍結源を使う比較群と分母を再構成する。

checkpoint の正本 SHA-256 は次のとおり。

    03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824

サイズは 195421066 bytes。転記元は 2026-08-06 に実施した11ホストの ssh 一括監査であり、
11 ホスト全てで SHA-256 が一致し、mtime もナノ秒まで同一であった。
`third_party/` は git の追跡対象外だが、実体はホスト間で同期されている。

`verify: ckpt_sha256` は全ホストで実行可能である。照合に失敗した場合は
`no_frozen_change` の違反として扱い、実行を中止して人へ escalate する。
skip する経路は設けない。

### 検査の適用範囲

凍結源の照合は、凍結源を使う契約に対して適用される。実行直前の検査では
`meta.kind` が `exp` の契約に対して実施し、それ以外は適用対象外として
未実施と記録する。

**適用対象となった場合に、照合を省略する経路は存在しない。**
照合に失敗した場合は実行を中止し、人へ差し戻す。


## checkpoint の取得試行

取得元: ubuntu@192.168.196.190:50072 /home/ubuntu/slocal2/m2/third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth

`ssh -o BatchMode=yes -o ConnectTimeout=10 -p 50072 ubuntu@192.168.196.190` で stat と sha256sum を試行。終了コード 255。

```text
ubuntu@192.168.196.190: Permission denied (publickey,password).
```

接続は認証段階で拒否。秘密鍵・トークンの内容は参照せず。コピー未実施、ローカルの照合値は UNKNOWN。

## L3 の原文

```text
P1 venv_active            PASS expected=/home/ubuntu/local/m2/.venv VIRTUAL_ENV=/home/ubuntu/local/m2/.venv sys.prefix=/home/ubuntu/local/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP UNKNOWN 判定基準が未確定。決定性設定は実行プロセス内で行われ外部から観測できない。backlog B-20 が未解決
P4 prereg_committed       PASS e9f4e3b4f34410c023c7a4ab240971c1d70c2510 committed_at=2026-10-21T19:55:13+00:00
P5 frozen_source_hash     FAIL 凍結源が存在しない: third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS experiments/phase1/stage1_ptower_search/ は未作成だが作成可能（experiments/phase1 へ書き込みと削除ができた）
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              WARN 規則 9 件のうち 1 件が該当: host_mismatch@tasks/T-2026-10-22-tower-reselect-search-dlsta/SPEC.md:5（終了コードは変わらない）
P10 preflight_names_known  PASS 宣言 3 件はすべて実装済み（既知: cuda_ext_loaded, deterministic_flags, gpu_free, venv_active）
P11 gpu_free               PASS GPU を占有する compute プロセスは 0 件
P12 refs_resolved          SKIP 解決前提の参照は無い
P13 symmetry_table_complete PASS 対称性の表 2 個 / 34 行に UNKNOWN と理由欠落は無い
P14 proposal_card_checked  PASS docs/proposals/2026-10-21-tower-reselect-search.md は検出 0 件（カード 16 件 / 禁止語 15 語を検査）

RESULT: 9 PASS / 1 WARN / 3 SKIP / 1 FAIL
make: *** [Makefile:179: task-preflight] Error 1
```

make 終了コード 2。プリフライト本体の失敗により手順 4 で停止。P4 の原文時刻は JST では 2026-10-22 04:55:13。

## 停止時の実施範囲

学習 0 run、GPU を使うコマンド 0、試験未実施（result.yaml の tests は実行して観測した件数 0 であり、既存の失敗数が零という主張ではない）。旧 0b 記録の削除・実装変更・runindex 再生成・PR 起票・台帳送信は未実施。

## 再開（2026-10-22 JST）

利用者が転送完了を伝え再開を指示。実体は ~/third_party/Relation-DETR/checkpoints/incoming/seed42/best_ap.pth に在った。SHA-256 とサイズの正本一致を確認し repo の指定先へコピー（元は残した）。再開時の追跡変更・未追跡は0、目印不在なので所有記録つきで設置。L3 は10 PASS /1 WARN /3 SKIP /0 FAIL。G1 PASS。全試験924 passed /6 failed /1 skipped。開始状態・環境・入力・試験は experiments/analysis/tower_reselect_search_dlsta/、生記録は ~/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/ に保存。Task B→G2→C→G3→D→G4→E→F の順を守る。

## Task A の完了と Task B の停止

- checkpoint: 195421066 bytes、SHA-256 03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824、正本一致。元の ~/third_party/ のファイルは残存。
- G1 PASS。入力監査は前回の全項目について count と digest も一致。旧0b記録は削除前10708453397 bytes、削除後不在、隣接する dlsta_tower_feasibility の記録は前後とも在る。
- GPU所有者対照: GPU1 の自分のPythonをPIDとexe完全一致で1件、存在しないPIDで0件。使用プローブ終了コード0。GPU0の使用なし。
- 環境は env_dlsta.json。これは学習前プローブの値で、学習時の決定性設定の証明ではない。
- 重複画像15437枚、欠け0、SHA-256不一致6001。内訳 train3998 /val961 /test1042。代表例と両側のハッシュは image_overlap_summary.json、全不一致は image_overlap.json。
- 再現: `source .venv/bin/activate && python tasks/T-2026-10-22-tower-reselect-search-dlsta/check_image_overlap.py`。画像を変更せず、count・missing・differentだけを標準出力へ出す。不一致ならexit1。
- SPEC Task B.1 と prereg の停止条件に従い、新manifest生成と探索学習を停止。画素内容・再圧縮・対応フレームなどの原因は未測定。
- 利用者に「学習を停止したまま原因調査のみ続ける／ここで止める」を問い合わせた。返事待ちのため task-release は呼ばず所有情報つき .sync-pause を維持。
- 探索用設定・起動・記録口は下書き状態。追加CPU試験3件とlintは通過。GPU経路、W&B別プロセス、勾配ノルムの記録、二枚の実データ対照は未検証。
- third_party 本体と既存の二枚の道は未変更。新しいsnapshotの作成は不要だった。依存の追加・削除は実施していない。
- data/processed の新manifestは生成していない。既存manifest、raw、external、splitsは変更していない。

## 停止時の検証

画像照合の再実行は count15437 /missing0 /different6001、exit1。全試験変更後は927 passed /6 failed /1 skipped、失敗名の集合は開始前と同じで新しい失敗0。追加CPU試験3件、ruff、bash -nは通過。ログはrepo外の tests_after_B_partial.log・tests_after_B_partial.xml。

## 画像原因調査の承認と結果（2026-10-22T05:23:10.959091+09:00）

利用者の「よい」は、学習を停止し画像を変更せず原因調査のみ続けることへの承認として扱った。analyze_image_overlap.pyで6001対を全数復号。エラー0・寸法同一6001・画素完全一致0・開始前ハッシュ維持True。JPEG保存形式は不一致分のrawのみ全て共通JFIF/品質95相当、配布側はLavcコメント。別コピーの在る5997枚は全て配布側と一致。平均RGB差は要約JSONを参照。標本47例の近隣比較は47例全て同名が最小。単純再保存13例の3方法は完全再現0。具体的な生成経路はUNKNOWN。

IMAGE_MISMATCH_ANALYSIS.mdに実測・推論・限界を分けて記録。proposed_image_amendment.mdに未承認の選択肢を作成した。契約・preregは変更せず、画像の書換・学習再開もしていない。詳細JSONLはrepo外、要約と試行結果JSONはanalysis配下。

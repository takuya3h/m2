# 検出塔のクラス別の誤りの分解と、直した場合の上限の目安 — 保存済みの val の予測だけを使う記述

**task_id:** T-2026-11-22-dtower-class-error-breakdown  **kind:** analysis  **ホスト:** andrew（repo は ~/slocal2/m2。context/env-facts.md の「repo の位置」）  **PR の base:** phase0  **分岐:** feat/dtower-class-error-breakdown

## 0. この契約の位置づけ

- **非公式の記述である。** 関門（Stage ごとに型や方向を落とすかを決める判定）の判定にも、設計の判断（案の採否を含む）にも使わない。提案カードを通さない（手法・結合・補助信号の案を含まない。保存済みの予測の読み方だけを扱う）
- **本契約では GPU を使用しない。学習も推論もしない。** 読むのは保存済みの val の予測と、val・train の注釈だけである
- 利用者の決定（2026-11-22、起票の会話）: 予備測定で低かったクラス（Forceps、Gauze、Hook、Scissors）を上げる方法を考える前に、誤りの型と上限の目安を測る
- `meta.created_from` と `contract.conventions_rev` は、起票者が origin の phase0（6953d6e4、2026-11-22）の写しで測った値である（runindex は git log -1 -- runindex/ と csv.DictReader の件数、規約は git log -1 -- context/conventions.md）。実行者が起点で測り、違えば差し替えて `meta.amendments` に記録する
- `inputs.data.split_files` は様式を通すための値で、本契約は参照しない（使う分割は conventions#folds の各 Fold の val と train）。報告に「参照しなかった」と書く
- 本書の語: **signature class** は conventions#det_groups の標的群（Skewer、Bipolar Forceps、Scalpel、Syringe、Raspatory）、**negative control** は同じ節の陰性対照群（Gauze、Mouth Gag、Suction Cannula、Tweezers）、**hash** は sha256、**Fold** は conventions#folds の折り

## 1. 前提

### 1.1 分かっていること（出所つき）

- 凍結した検出塔（以下 **塔 1**）: T-2026-11-07-dtower-rerun が andrew で学んだ探索の 12 番・seed 42 の 5 本（Fold A〜E）。checkpoint の経路・hash・val の値は `experiments/analysis/dtower_rerun/frozen_towers.json`。val mAP は Fold A から順に 0.7196、0.4755、0.4428、0.5063、0.5226（同ファイルの `val_mAP`）
- 塔 1 の評価は包み `experiments/analysis/dtower_rerun/tools/eval_dump.py` を通り、評価器が集めた予測の全件を `eval_val.detections.json.gz` に、動画ごとの COCO の値とクラス別 AP を `eval_val.per_video.json` に書く実装である（同ファイルの冒頭の説明）。置き場は実行器の実装では `/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-07-dtower-rerun/runs/` の下の run ごとのフォルダ（`tools/run_rerun.py` の `STORE` と `work`）。**同じフォルダに test の予測（`eval_test.*`）も在る。本契約は読まない**
- 前回までの予備測定が使った検出塔（以下 **塔 2**）: D\*-COCO の Fold A・seed 42（`experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42`。学んだホストを起票者は repo の記録で確かめていない）。val の overall mAP 0.7273450、signature class の AP 0.7950748、negative control の AP 0.6726632（tasks/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/RESULT.md §2 の G2）
- 塔 2 の val の予測は、同じ契約が `FIX/identity/plain_val_preds.json.gz` として作り直し、前回の基準と score・枠・ラベルの差が 0、mAP 0.7273450 だった（同 audit.md の C-4。`FIX` が指す場所は同 audit の定義による）
- 塔 2 の Fold A の val のクラス別 AP（`experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/per_class_ap.json`）: Forceps 0.3561、Gauze 0.2692、Hook 0.6365、Scissors 0.7097、Tweezers 0.7874。Retractor は val に現れず非数
- 4 クラスは少数クラスではない。box の構成比は Gauze 13.5%、Forceps 12.2%、Scissors 5.5%、Hook 2.7%（docs/phase_tool_annotation_stats.md §1.1）。工程を知ったときに在否の不確かさが減る割合は Forceps 8.2%、Gauze 8.4%、Hook 21.7%、Scissors 24.9%（同 §3.7）
- 全クラス合計の誤りの分解の前例（Stage 0 の別の検出器の予測）: 正解 90.99%、分類誤り 5.27%、局在誤り 2.68%、見落とし 1.06%。区分の定義と足切り（score 0.05 以上、IoU 0.5 と 0.1）は docs/stage0/A6_error_decomposition.md。クラス別の値は無い
- 形が似て取り違えやすいクラスとして、コードは Forceps・Tweezers・Needle Holders・Bipolar Forceps を定義している（src/egosurgery/datasets/constants.py の `CONFUSABLE_CLASSES`）
- 検出塔は一つの query を複数のクラスで出すことがある。前回の予備測定では、後処理後の出力の上位の 45% が同じ query の重複だった（tasks/inbox.d/T-2026-10-18-stage2-pilot-folda.md）。同じ枠が別のクラスで並ぶので、「最大 IoU の予測」は一つに決まらないことがある（§4.2）
- どの注釈ファイルにも `id: 0` の注釈が一つあり、pycocotools はその注釈に一致した検出を誤検出に数える。塔の評価の値はこの影響を注釈一つ分だけ含む（experiments/analysis/dtower_rerun/REPORT.md §8）。本契約の再現（§5 の Task B）は、記録の値を作ったのと同じ扱いで行う
- 正解の工程から固定の表でクラスの score を直す型（P2F。学習なし）の値は既に在る: 塔 2 の Fold A で overall 0.7325、signature class 0.8169、negative control 0.6624（`experiments/analysis/stage2_pilot_fix/report.json` の `previous_values` の `P2F/gt_p2f`）。本契約は P2F を回し直さない。§4.5 の (d)・(e) は別の定義である

### 1.2 起票者が確かめていない前提

- **保存済みの予測が今も在るか。** 塔 1 の 5 本の `eval_val.detections.json.gz`、塔 2 の `plain_val_preds.json.gz` の実在と中身を、起票者は測っていない（andrew に届かない）。Task A で測る
- 保存済みの予測の様式（画像の id の振り方、枠の形式、足切りの有無、画像あたりの件数）を確かめていない。実装と中身を読んで決める
- pycocotools がどの仮想環境に在るかを確かめていない。conventions#env_p0 は検出系に `.venv-relation-detr` を挙げる。在る環境を使い、新しく導入しない。`plan.env.venv` の `.venv` は起動直前の検査のための値で、計算に別の既存の環境を使ってよい（使った環境を記録する）
- val の画像ごとの正解の工程の出所（§4.5 の (e) に使う）を確かめていない。前回の予備測定で正解の腕の信号を作った出所と同じものを使い、出所を記録する
- 塔 1 の Fold B〜E の val に、注釈の無いクラスがある（Fold A の Retractor と同じ型）。クラス別の値は非数にし、平均から除く（conventions#det_groups の扱い）

### 1.3 対象

| 名前 | 塔 | Fold | 予測 | 役割 |
|---|---|---|---|---|
| 塔 1 | T-2026-11-07-dtower-rerun の 12 番・seed 42 | A・B・C・D・E | `eval_val.detections.json.gz` | 主。これから使う塔の実態 |
| 塔 2 | D\*-COCO・seed 42 | A | `plain_val_preds.json.gz` | 前回までの予備測定の値とつなぐ |

- 塔 1 と塔 2 は学習設定が違う（塔 1 は探索の 12 番）。学んだホストが同じかは確かめていない。**二つの塔の値の差を、塔の優劣として書かない**（並べるだけ）
- 塔 1 の Fold B〜E の予測が無ければ、在る Fold だけで続け、無い Fold を UNKNOWN と書く。Fold A が無ければ G1 で止まる
- 塔 2 の予測が無ければ、塔 2 の欄を UNKNOWN にして続ける

## 2. 禁止と申し送り

- 注入される規約の節（prohibitions・issuer_cautions・env_p0・folds・split・eval_recipe・det_groups）に従う
- 禁止は実行者の操作に対するものである。Syncthing による他の台への配布（本契約の出力が他の台に届くこと、他の契約の出力が届くこと）を含まない
- **本契約では GPU を使用しない。** 学習・推論・特徴の取り出しをしない。予測が無いものを作り直さない
- **test の動画の予測と注釈を読まない。** `eval_test.*`、`instances_test.json`、`per_class_ap_test.json`、`eval_test.json` を開かない。フォルダの一覧に名前が出ることは構わない
- 保存先 `/home/ubuntu/slocal2/stage2pilot_store` の既存の中身、前回までの契約の出力と集計、data の注釈、凍結した塔の重み、third_party、既存の仮想環境を変えない。本契約の出力は allow_write の接頭辞 `experiments/analysis/dtower_class_error_breakdown/` の下にだけ書く（道具もここに置く）
- 既存の道具（`scripts/eval_relation_detr_map.py`、`eval_dump.py` など）を書き換えない。読んで同じ計算を本契約の道具から呼ぶか、同じ計算を本契約の道具に書く
- 新しい依存を導入しない。外部の取得をしない（外部への送信は `make task-report` と PR だけ）
- runindex と context/auto の生成物は作り直さない。`*-check` は回さない（`make forbidden-check` は回す）
- andrew には別の契約 T-2026-11-22-conv-epoch-history-extract が配布されている（GPU を使わない）。同じ repo の作業ツリーを使う場合は同時に走らせない。始める段の表示に従う

## 3. 読むもの

- 予測: §1.3 の表のファイル。経路は Task A で実在を測って記録する
- val の注釈: 塔の評価が使ったのと同じ注釈ファイル（Fold ごと。実行器と評価の道具の実装から経路を読む）
- train の注釈: 同じ Fold の train の注釈（§4.5 の (e) と §4.6 の数え上げだけ）
- 工程の正解: §1.2 のとおり
- 記録: `frozen_towers.json`、塔 1 の run ごとの `eval_val.per_video.json` と評価の出力、塔 2 の `per_class_ap.json` と §1.1 の値

## 4. 定義（本契約の記述だけに使う。規約には置かない）

閾値の出所: score の足切り 0.05、IoU 0.5、IoU 0.1 は docs/stage0/A6_error_decomposition.md。AP・AP50・AP75 は COCO の評価の定義。**ほかの閾値を足さない。**

字面に複数の読みがあって結果が変わるときは、読みを一つに決めずに、両方の読みの値を出して並べる。両方を出せないときだけ停止して利用者に尋ねる。

### 4.1 共通

- AP の類（§4.5、§4.6、Task B）は、保存済みの予測の全件で計算する（塔の評価と同じ。足切りを足さない）
- 分解（§4.2〜§4.4）は、score が 0.05 以上の予測だけで行う
- クラスは 15 クラス。val に注釈の無いクラスは、その Fold では非数にして平均から除き、除いたクラスを書く
- 平均は、全クラス、signature class、negative control、どちらにも入らないクラス（以下「その他」）の四つを出す

### 4.2 GT の側の分解（GT の box を一つずつ四つに分ける）

A6 の区分をクラス別に出す。同じ枠が別のクラスで並ぶこと（§1.1）への扱いを二通り出す。

| 区分 | 定義 |
|---|---|
| 正解 | 対応する予測との IoU が 0.5 以上で、クラスが同じ |
| 取り違え（A6 の分類誤り） | 対応する予測との IoU が 0.5 以上で、クラスが違う |
| 位置のずれ（A6 の局在誤り） | 予測との最大の IoU が 0.1 以上 0.5 未満 |
| 見落とし | 予測との最大の IoU が 0.1 未満（予測が無い場合を含む） |

- **読み 1（A6 の字面）**: 対応する予測は、クラスを問わず IoU が最大の予測。IoU が同じ予測が複数あれば、score が最大のもの
- **読み 2（同じクラスを優先）**: IoU が 0.5 以上の予測の中に同じクラスのものが一つでもあれば正解。無ければ、IoU が 0.5 以上の予測のうち score が最大のものを対応する予測にする
- 読み 1 で IoU が同じ予測が複数あった GT の数を、クラスごとに記録する

### 4.3 取り違えの表

- §4.2 の「取り違え」について、GT のクラス（行）× 対応する予測のクラス（列）の件数の表を、読み 1 と読み 2 のそれぞれで出す
- 行ごとに、取り違えの相手の上位を件数と割合で出す

### 4.4 予測の側の分解（足切りを通った予測を一つずつ分ける）

クラスごとに、予測を score の高い順に、同じクラスの GT と IoU 0.5 以上で一対一に対応させる（COCO の評価の対応づけと同じ考え方。一つの GT には一つの予測だけ）。対応しなかった予測を、次の順で最初に当たった区分に入れる。

| 順 | 区分 | 定義 |
|---|---|---|
| 0 | 当たり | 同じクラスの GT に一対一で対応した |
| 1 | 重複 | 同じクラスの GT と IoU 0.5 以上だが、その GT は score のより高い予測に対応済み |
| 2 | 取り違え | 別のクラスの GT と IoU 0.5 以上 |
| 3 | 位置のずれ | 同じクラスの GT との最大の IoU が 0.1 以上 0.5 未満 |
| 4 | 背景 | どの GT との IoU も 0.1 未満 |
| 5 | その他 | 上のどれでもない |

- 区分 2 は、相手の GT のクラスごとの件数も出す
- 区分ごとに、件数と、score の中央値を出す

### 4.5 直した場合の上限の目安

予測を次の五通りに直し、直す前と後のクラス別 AP・AP50 と、その差を出す。**どれも厳密な上限ではない。** 一つの誤りの型を除くと AP がどれだけ動くかの目安である。直し方は一つずつ別々に当てる（重ねない）。

| 記号 | 直し方 | 定義 |
|---|---|---|
| (a) | 重複を除く | 画像ごとに、クラスを問わず IoU が最大の GT（IoU 0.5 以上）が同じで、クラスも同じ予測のうち、score が最大の一つだけを残す。IoU 0.5 以上の GT を持たない予測は残す |
| (b) | クラスを直す | クラスを問わず IoU が最大の GT（IoU 0.5 以上）を持つ予測のクラスを、その GT のクラスに書き換える。その後に (a) の除き方を当てる |
| (c) | 枠を直す | 同じクラスの GT との最大の IoU が 0.1 以上 0.5 未満の予測の枠を、その GT の枠に置き換える。その後に (a) の除き方を当てる |
| (d) | 在否を直す | クラス c の GT が一つも無い画像から、クラス c の予測を除く |
| (e) | 工程で在り得ないクラスを除く | その Fold の train の動画で、工程 p のフレームにクラス c が一度も写らない組（p, c）について、val の正解の工程が p の画像からクラス c の予測を除く。train に現れない工程の画像からは何も除かない |

- (b) と (c) の「クラスを直した分」「枠を直した分」は、(a) との差としても出す（重複を除いた分と分けるため）
- (e) では、Fold ごとに、除いた組（p, c）の一覧と、val の画像のうち工程の正解が付いた数を記録する
- (d) は在否の情報がすべて正しく渡った場合、(e) は工程から分かる在否だけが渡った場合の目安である。二つの差は、工程では分からない在否の分にあたる
- 直す前の値は Task B の再現の値と同じでなければならない（同じ評価の計算を通す）

### 4.6 クラス別の AP・AP50・AP75 と、Fold・動画ごとの表

- クラス別の AP・AP50・AP75 を、対象の塔と Fold ごとに出す
- Fold ごと・クラスごとに、train の box の数、train でそのクラスが写る動画の数、val の box の数、val でそのクラスが写る動画の数、AP、AP50 を一つの表に並べる
- 動画ごとのクラス別 AP を出す（塔 1 は `eval_val.per_video.json` に在ればそれを読む。塔 2 は予測から同じ計算で出す）。動画に注釈の無いクラスは非数

## 5. 手順

**コマンドは書かない。実装と記録を読んで決めてよい。** 命令と出力は `audit.md` に残す。

- **Task A（開始状態と材料）**: 分岐が `feat/` で始まること、起点、前提の道具と記録の在否（§1.1 が名指すファイル）、未追跡、試験の失敗の名前、使う仮想環境と pycocotools の在否を記録する。`meta.created_from` と `conventions_rev` を測り、違えば差し替える。§1.3 の予測の実在・経路・hash・画像数・予測数を測り、塔 1 の予測が `frozen_towers.json` の run のものであることを、run の名前で確かめる。読んだファイルの一覧を作り始める（Task D まで足し続ける）。欠けがあれば §1.3 の規則と G1 に従う
- **Task B（再現）**: 保存済みの予測と val の注釈から、overall mAP・クラス別 AP・signature class の AP・negative control の AP を計算し直し、記録（塔 1 は `frozen_towers.json` と評価の出力、塔 2 は §1.1 の値と `per_class_ap.json`）と比べる。記録の表示の桁（小数第 4 位）で一致しなければ G2 で止まる。差の最大を記録する
- **Task C（分解と表）**: §4.2〜§4.6 を、対象の塔と Fold ごとに出す。道具は allow_write の下に置く。§6 の対照を道具ごとに取る
- **Task D（集計と報告）**: 表を記録から道具で作る（手で写さない）。§7 の構成で報告を書き、`make forbidden-check` を回し、commit・push・PR（base phase0、Draft でない）・`make task-report` を行う

## 6. 完了判定

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態の記録 | spec の acceptance a の項目がすべて audit にある | 存在しない仮想環境の経路で pycocotools の検査が「無い」を返す |
| b | 材料の目録 | 対象の塔と Fold ごとに経路・hash・画像数・予測数があり、無いものは理由つきで UNKNOWN | 1 バイト変えた写しで hash の照合が食い違いを出す。存在しない run の名前で 0 件になる |
| c | 再現 | 計算し直した overall mAP・クラス別 AP・群の AP が、記録と小数第 4 位まで一致する | 予測の score を一つの画像だけ入れ替えた写しで、比べが差を出す |
| d | GT の側の分解 | 読み 1・読み 2 とも、四つの区分の件数の和がクラスごとの GT の数と一致する。取り違えの表の行の和が「取り違え」の件数と一致する | GT と同じ枠・同じクラスの予測だけを与えた作り物で全件が正解になる。クラスだけを一つ変えた作り物で取り違えが 1 件、枠をずらした作り物で位置のずれが 1 件、予測を除いた作り物で見落としが 1 件になる |
| e | 予測の側の分解 | 六つの区分の件数の和が、足切りを通った予測の数と一致する | 同じ枠の予測を二つ与えた作り物で重複が 1 件、GT から離れた予測を足した作り物で背景が 1 件になる |
| f | AP50 と AP75 | クラス別の AP・AP50・AP75 が対象の塔と Fold ごとにある。AP は完了判定 c の値と一致する | AP50 が AP 以上であることを全クラスで確かめる。枠を一律にずらした写しで AP75 が下がる |
| g | 上限の目安 | 五つの直し方で、直す前と後のクラス別 AP・AP50 と差がある。直す前の値が完了判定 c の値と一致する | GT をそのまま予測にした作り物では、五つとも直す前後の差が 0 になる。クラスだけを変えた作り物では (b) だけが上がる。在否の違う画像に予測を足した作り物では (d) が上がり (c) は動かない |
| h | Fold と動画ごとの表 | §4.6 の表が対象の塔と Fold ごとにある。train と val の box の数が注釈ファイルの数え上げと一致する | 注釈を一つ除いた写しで数が 1 減る。動画の集合が conventions#folds の表と一致し、別の Fold の動画を混ぜた写しで不一致になる |
| i | test を読まない | 読んだファイルの一覧に、test の予測と注釈が 0 件。読んだ画像の動画の集合と、その Fold の test の動画の共通が 0 件 | 一覧に test のファイルの名前を一つ混ぜた写しで検査が 1 件を返す |
| j | 変えていない | 保存先の読んだファイルの hash が開始時と終了時で一致。試験の失敗の名前が開始時と同じ。forbidden-check で本契約の経路の違反が 0 | 本契約の新しいファイルが変更として拾われ、allow_write の許可として名指されることを示す |
| k | PR | Draft でない PR が base phase0・分岐 feat/dtower-class-error-breakdown で在る | 分岐名と base を `gh pr view` の出力で示す |

## 7. 報告の構成

`RESULT.md` は 150 行以内。節は 判定（status と G1・G2）／完了判定（表。実測値つき）／実測／起票者の誤り（一件 3 行以内）／逸脱／想定外・UNKNOWN／送出（PR 番号と終了コードだけ）。

「実測」には、次の契約と利用者の判断で使う値を置く。

- 材料の在否（塔と Fold ごと）と、再現の差の最大
- Forceps・Gauze・Hook・Scissors と、比べる相手として Tweezers・Syringe について、塔 1 の Fold A〜E と塔 2 の Fold A の: GT の側の四区分の割合（読み 1・読み 2）、取り違えの相手の上位、予測の側の区分の割合、AP・AP50・AP75、五つの直し方の差
- 全クラス・signature class・negative control・その他の平均での、五つの直し方の差
- 読み 1 で IoU が同じ予測が複数あった GT の数
- §4.6 の表のうち、4 クラスの行

**解釈・順位・採否は書かない。** 値と、定義から直接言えること（どの区分が多いか）だけを書く。

命令とその出力、参照の解決の全文、対照の出力、変更範囲の一覧、台帳の応答は `audit.md` へ。`RESULT.md` から `audit.md` を行番号で指し、同じ内容を二度書かない。全値と表は `experiments/analysis/dtower_class_error_breakdown/REPORT.md` と機械可読のファイル（記録から道具で作る）。

## 8. 申し送り

- 本契約の値は val の動画の数が少ない（Fold ごとに 2 本）。クラスによっては val の box が百数十しか無い（docs/phase_tool_annotation_stats.md §5.2 の公式分割の val で Forceps 154、Hook 147）。割合には件数を必ず並べる
- seed は 1 本である。seed の間の揺れは本契約では分からない
- 費用（壁時計）は記録であり、判断に使わない

# RESULT — T-2026-11-06-dtower-batch-search

andrew の A6000 × 2 で、探索の 12 番の設定のまま GPU ごとの batch 2・4・6 を折り A・seed 42 と 123 で各 1 本、計 6 本学んだ。prereg §3 の規則で **batch 6** を選んだ。
値は処方の効果として読まない（折り A の 2 本の平均で、3 水準の最大を取るので上振れする）。採否・推奨は書かない。
全値は `experiments/analysis/dtower_batch_search/REPORT.md`、命令と出力は `audit.md`（以下 `audit:行`）。

## 判定

- status: **pass**
- G1 pass（audit:133-140）: 分岐と起点、prereg の先行、カードが五版、入力の要約値の一致、compute プロセス 0 件、空き 2 倍以上
- G2 pass（audit:191-196）: 設定が optimizer の群と DataLoader に届く。陽性対照で値が変わる。立ち上げの歩数の記録の口が働く。既定の挙動は不変
- G3 pass（audit:263-267）: 6 本とも完走。損失の非数 0 件、溢れ 0 件。6 本とも COCO の重みを読んだ行と要約値の一致が在る

## 完了判定

| # | 判定 | 実測 |
|---|---|---|
| a | prereg の先行 | b71ffafd（11-06 07:08:51 JST）は最初の学習の開始（07:51:55 JST）の前。P4・P13・P14 PASS（audit:43-51）。UNKNOWN の写しで P13 FAIL、存在しないカードで P14 FAIL（audit:127-131） |
| b | 開始状態と環境 | 分岐・起点 9d45351b・PR 290/292 の内容・未追跡 0・GPU・試験の前 7 failed / 989 passed・カード五版・環境の表・電力の上限 300 W（audit:53-125）。列挙は対照で 1/0/0、四版の写しで rc 1 |
| c | 入力と道具 | 13 件の sha256 が一致。空き 1,644,097,175,552 bytes ≥ 見込み 19.2 GB の 2 倍。1 バイト変えた写しで不一致 1（audit:70-85） |
| d | 設定の到達 | 6 本の `posthoc_records.json` の群の値と `loader_rank0/1.json` の batch が水準どおり（REPORT §2.1）。changed・wd_mismatch・batch_mismatch・default の対照（audit:163-177） |
| e | 6 本の run | 6 本とも完走。config.yaml に task_id・batch・seed・lr・weight decay・max_norm・S（audit:198-262）。存在しない名前（b8）は 0 件 |
| f | 記録する量 | prereg §5 の 8 項目を各 run で記録（REPORT §2・§4・§5）。立ち上げは b2・b4 で 1,000 歩、b6 で 801 歩（802 歩目で目標に達する） |
| g | 表と選択 | 下の表。平均と差を metrics.json から計算し直して全桁で一致（audit:282-286） |
| h | 対称性 | prereg の表に UNKNOWN 0 件。P13 PASS（表 1 個、**23 行**。SPEC は 24 行と書く → 起票者の誤り） |
| i | test 不使用と置き場 | 評価した区分は 6 本とも {train, val}、test の動画の読み 0 件。test を足した写しで 6 本とも外れ（audit:288-292）。checkpoint は同期の外 `$STORE/runs/` |
| j | 収穫と無変更 | runindex に 6 本が task_id つきで現れた。ただし検証の C5 が別の契約の 3 run で FAIL（audit:304-312）。要約値は 82 項目すべて一致（audit:300-302）。試験は後も 7 failed / 989 passed で失敗の名前は同じ 7 件（audit:328-333）。forbidden-check は同期で届いた別の契約の 13 件で fail、13 件を除くと pass（audit:319-326） |
| k | PR | #299、base phase0、isDraft false、head feat/dtower-batch-search |

## 実測

| 水準 | GPU ごと / 実効 batch | weight decay | val mAP（42 / 123） | 平均（全桁） | 最大との差 | 標的群 AP の平均 | 陰性対照群 AP の平均 | 総 epoch（42 / 123） |
|---|---|---|---|---|---|---|---|---|
| b2 | 2 / 4 | 3.37e-4 | 0.7301 / 0.7269 | 0.7284992 | −0.0071529 | 0.8125 | 0.6687 | 22 / 18 |
| b4 | 4 / 8 | 6.7428e-4 | 0.7283 / 0.7311 | 0.7297248 | −0.0059273 | 0.8205 | 0.6659 | 25 / 16 |
| b6 | 6 / 12 | 1.01058e-3 | 0.7385 / 0.7328 | 0.7356521 | 0 | 0.8211 | 0.6745 | 15 / 18 |

- 規則（prereg §3）: 最大は b6。b2・b4 は最大との差が同点幅 0.0076 以下で、3 水準とも同点。同点の中で最も大きい batch → **b6（GPU ごとの batch 6）**
  - b2 は同点幅まで 0.0004 の余り。全桁の平均で判定した
- co-primary（標的群 AP の平均）の最良も b6。**食い違いはなし**
- 2 本の差（42 − 123）: b2 +0.0032、b4 −0.0028、b6 +0.0056
- 記録だけ: b2 の平均と探索の 12 番（dlsta、0.7374）の差は −0.0089。ホストが違うので比べない
- 予測（prereg §3.1）: 1（b4 が選ばれる）**外れ**、2（b6 が b2 より低い）**外れ**、3（発散なし）当たり（REPORT §6）
- weight decay の換算: 実測の 1 epoch の歩数 2,405・1,202・802 から 3.37e-4 × 2,405 ÷ 歩数を計算し、表と 5 桁で一致した（audit:186-189）
- 立ち上げ・歩数: 1 epoch 2,405・1,202・802 歩。総更新回数は 52,910・43,290（b2）、30,050・19,232（b4）、12,030・14,436（b6）
- 所要: 学習の壁時計 6.6・5.3（b2）、6.2・3.9（b4）、3.6・4.3 h（b6）。最大確保（rank ごと）は b2 13.2〜13.5 GB、b4 25.8〜26.2 GB、b6 38.0〜38.7 GB
- 勾配が非数の歩（fp16 の scaler が飛ばした歩。学習は止まらない）: 27・21・19・14・12・12。刈り込んだ歩の割合は 6 本とも 0.999
- 環境: torch 2.1.2+cu118、cuDNN 8700、NCCL 2.18.6、torchvision 0.16.2、accelerate 1.14.0、driver 595.84、TF32 matmul False / cudnn True、300 W（audit:87-103）

## 起票者の誤り

- self_contradiction: prereg §3 の同点幅 0.0106 は二周目の 3 本の SD 0.0053 の 2 倍で、本文が定義に引く mAP_sstd（0.0037965）と食い違う。利用者の決定で 0.0076 に改訂（audit:22-41）
- asserted_without_measuring: weight decay の表は丸めた S 5.0e-3 から換算しており、b2 が 12 番の 3.37e-4 と 0.5 % 違った（3.386e-4）。利用者の決定で改訂
- asserted_without_measuring: SPEC §1 は「点ごとの学習率・weight decay・max_norm を受ける」と書くが、スクリプトは epoch 0 で群を `points.csv` の 12 番と 1e-15 で照合し、b4・b6 は止まる。包みで点を差し替えた（audit:150-153）
- asserted_without_measuring: SPEC §5 h は P13 の行数を 24 と書くが、prereg の表は 23 行
- check_does_not_check: SPEC §5 g の「同点幅を 0 にした写しで選択が変わる」は、最大の平均が最大の batch でもあるとき（今回の b6）見分けない。合成の入力で代えた（audit:282-286）

## 逸脱

- batch と worker 数は、`train_search.py` の 2 行だけを環境変数にした写しを repo の外に置いて渡した（SPEC が許す方法。audit:146-148）
- 包み `tools/train_level.py` で `load_point` だけを prereg の値の JSON に差し替えた。照合は働いたまま（audit:150-153）
- 観測器 `tools/observer.py` を `TOWER_SEARCH_OBSERVER` で読ませ、batch・枚数・立ち上げ・評価の組ごとの AP・読んだ動画を記録した。ファイル・既定の挙動は無変更
- 「発散・非数」は探索と同じく「損失が非数で学習が止まる」で数えた。勾配が非数の歩は記録する量として残した
- 要約値の経路を前の契約より 6 本足した（audit:80）
- 同じ識別子の一度目の着手は、カードが四版のため G1 の前で中止し、利用者の指示で「実行しなかった扱い」とした（audit:9）
- 集計の道具 `summarize.py` を学習の後に 2 回直した（評価した区分の読み方と glob）。選択の計算は変えていない（audit:294-298）
- forbidden-check の fail（同期で届いた別の契約の 13 件）はそのまま記録した。13 件は消さず、無視の一覧にも足していない（audit:319-326）
- runindex は検証の C5 が FAIL のまま commit した。原因は別の契約の run で、直していない（audit:304-312）

## 想定外・UNKNOWN

- runindex の C5 の FAIL（`phase1__grasppilot2_G_*` 3 本の value 空欄 51 行）。phase0 の上で収穫しても同じく落ちる
- 学習の最中に別の契約の未追跡のファイル 13 件が同期で届き、forbidden-check を落とした
- runindex の本契約の行の `eval_recipe_id` は空欄。収穫器が評価の recipe を引けなかった理由は調べていない
- b6 の最大確保 38.0〜38.7 GB は PR 290 の 34.6 GB（数歩）より大きい。原因は測っていない
- 停止条件の「COCO の重みを読まない」「評価が checkpoint を読まない」の検査を、壊した入力で働かせてはいない（UNKNOWN）

## 送出

- PR: #299（base phase0、isDraft false、head feat/dtower-batch-search。内容の commit d3e319ac）
- `make task-report`: 終了コード 0（78497b91 の版を送った。verdict pass、n_issuer_defects 5、report_sha256 58fdc049…、8,872 bytes）

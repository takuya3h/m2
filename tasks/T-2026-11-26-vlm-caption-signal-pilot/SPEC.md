# VLM の記述を術具と工程の名前を伏せて工程塔・検出塔へ渡す予備測定 — Qwen3.8-27B、甲・乙・丙の三通り、空・予測・入れ替え、W1〜W3

**task_id:** T-2026-11-26-vlm-caption-signal-pilot  **kind:** analysis  **ホスト:** ilya（repo は ~/slocal2/m2。context/env-facts.md の「repo の位置」）  **PR の base:** phase0  **分岐:** feat/vlm-caption-signal-pilot

2026-11-27 JST の利用者指示により、本契約の実行ホストを ilya（RTX 6000 Ada Generation 2 枚）に変更した。本文のうち今回の計算、空きの確認、画像・記述の保管に関する andrew は ilya と読む。不足する既存の材料は rsync で取得する。過去の測定ホストと参考値は各記録の記載に従う。

## 0. この契約の位置づけ

- **非公式の予備測定である。** 関門（Stage ごとに型や方向を落とすかを決める判定。M §5.2）の判定にも、設計の判断（案の採否を含む）にも使わない
- **提案カードを通さない**（利用者の決定 2026-11-26）
- **VLM** は画像と文を入出力にする大きなモデル（vision-language model）。本契約では、フレームの画像を見せて決まった形の記述を書かせ、その記述を数値の信号にして interface（塔の間に置く小さな学習可能な層）で塔へ渡す
- 方向は二つ。**V→P**（VLM の信号を工程塔へ渡す）と **V→T**（VLM の信号を検出塔へ渡す）。前回までの予備測定の T→P（検出塔から工程塔）・P→T（工程塔から検出塔）と同じ受け取り手・同じ interface の型・同じ条件で回し、送り手だけを VLM に替える
- 利用者の決定（2026-11-26。Notion F に記録する。実行者は Notion を読まないので、要る部分を本書に写した）:
  1. VLM は Qwen3.8-27B だけを使う（手術向けの VLM は重みが手に入らないため回さない）。画像も記述も andrew の外の計算機やサービスへ送らない
  2. VLM に術具の種類と工程を明示させない（後段の塔が推論するため）。明示を禁じる範囲を三通り（甲・乙・丙。§4.1）にし、三通りとも回す
  3. 型は V→P が D1-L2・D2・D3-L2、V→T が P1・P2（本書は P2 を学習版の P2L と読む。固定版 P2F は学習せず W1〜W3 が無いため）
  4. 条件は前回の予備測定と同じ: Fold A、seed 42、4 epoch の固定が主で 8・12・16 epoch は副次、W1〜W3、腕は空・予測・入れ替え、主の指標はこれまでと同じ
  5. 記述だけを読む中間の検査（読み出し検査）は行わない。利用者の確認を待たず最後まで回す
- 学習の長さを固定の epoch にするのは、収束規則で揃えるという運用の約束からの例外である（前回までの予備測定と同じ、利用者の決定）
- `meta.created_from` と `contract.conventions_rev` は起票者が phase0（8395be39）で測った値。実行者が起点で測り直し、違えば差し替えて `meta.amendments` に記録する
- `inputs.data.split_files` は様式を通すための値で、本契約は参照しない（使う分割は conventions#folds の Fold A）。報告に「参照しなかった」と書く

## 1. 前提

### 1.1 分かっていること（出所つき）

- Fold A の train は動画 01・02・03・06・08・11・12・13・14・15、val は 09・10、test は 04・05・07。術具注釈のある画像は train 9,657、val 1,515（`data/README.md` の Fold の表）。画像は `data/raw/ego/` の分割と動画のフォルダの下、1920×1080 の JPEG（`tasks/T-2026-10-22-tower-reselect-search-dlsta/IMAGE_MISMATCH_ANALYSIS.md`）
- 追加動画 17〜21 の画像は `data/raw/ego/other(17~21)/` にあり、どの Fold の val・test にも使わない（`data/README.md` §3.1。フォルダ名に括弧とチルダを含むので、シェルでは引用符で囲む）
- V→P の受け取り手・型・学習設定・入れ替えは前回の T→P と同じ: 工程塔は P\*-15-COCO Fold A seed 42 の特徴のキャッシュを使い、塔単独の val の Jaccard は 0.7762185528074379。interface の学習率 5e-4・weight decay 0.01、W2・W3 の受け取り手 5e-4・weight decay 0.01、AdamW の別の群、1 歩は train の動画 1 本、時間ヘッドは eval。`--fixed-epochs` の経路は学習率が一定で、16 epoch まで続けた run の 4 epoch 目は 4 epoch で止めた run と確率まで一致した。入れ替えの対応表は `mapping_{train,val}.json`（seed 42）（tasks/T-2026-11-21-grasp-hand-graph-t2p-match/RESULT.md §2・§3）
- V→P の W の定義: W1 は interface だけ、W2 は W1 に時間ヘッドの最後の段、W3 は W1 に時間ヘッド全体（同 SPEC §3.3）
- V→T の受け取り手と型: 検出塔は D\*-COCO Fold A seed 42（`experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth`）。塔単独の val は overall mAP 0.7273450・signature class AP 0.7950748・陰性対照群 AP 0.6726632（tasks/T-2026-11-09-stage2-pd-w3-lowlr-andrew/RESULT.md §2 b）。P1 は FiLM で C5 を変調、P2L はクラスの点数への学習するバイアス。信号は `scripts/train_t1b.py` の `--signal-train`・`--signal-val`（frame_ids と x の npz）で渡し、次元は config（`configs/stage2pilot/pd_film_d9.py`、`pd_clsbias_lin_d9.py`）で決まる（`scripts/w23/run_pd_w23_andrew.sh`、`run_pd_w23_bengio.sh`）
- V→T の W の定義と学習率: W1 は `--trainable film`、W2 は `--trainable w2`（interface と decoder の最終層とその層のクラスと box の頭）、W3 は `--trainable all`（設定の凍結以外の検出器の全体）。学習は bf16 の自動混合精度・評価は単精度、batch 2、`--fixed-epochs`、seed 42（`scripts/w23/run_pd_w23_andrew.sh` の冒頭）。W2 の受け取り手は 1e-4（同台本の既定）、W3 の受け取り手は 1e-5・比 0.1 の群は 1e-6・interface 5e-4（tasks/T-2026-11-09-stage2-pd-w3-lowlr-andrew/RESULT.md §3）。`--fixed-epochs` では学習率の予定が無く一定（`scripts/train_t1b.py` の `--fixed-epochs` の説明と scheduler の分岐）
- V→T の 1 本の所要（4 epoch、andrew、1 枚 2〜3 本）: W1 の P1 3.35〜4.67 時間・P2L 3.36 時間（tasks/T-2026-10-19-stage2-pilot-fix-epoch4-shuffle/RESULT.md §4）、W2 3.11〜4.76 時間・W3 5.33〜5.87 時間（tasks/T-2026-11-01-stage2-w23-andrew/RESULT.md §3）。16 epoch まで続けると 1 本が約 4 倍になる（起票者の外挿。測っていない）
- 前回の参考の値（4 epoch 目）: T→P の 予測-noCF − 入れ替え（6 工程の Jaccard、W1・W2・W3）は D1-L2 +0.0371・+0.0643・+0.0852、D2 +0.0288・+0.0203・+0.0093、D3-L2 +0.0480・+0.0665・+0.0200（t2p-match の RESULT §3）。P→T の W1 の 予測-noCF − 入れ替え（signature class AP）は P1 +0.0087、P2L +0.0075（fix-epoch4 の RESULT §4）
- 工程塔側の W1 の予備では、腕の差は 6 工程の平均で ±0.015 の中で符号が学習の長さで変わった（tasks/T-2026-11-09-grasp-pilot-converge/RESULT.md §3）。検出塔側の揺れの幅は測っていない
- andrew の 2 プロセスの学習には `NCCL_P2P_DISABLE=1` が要ることがある（env-facts の装置の節と tasks/inbox.d/T-2026-10-18-stage2-pilot-folda.md）

### 1.2 起票者が確かめていない前提

- andrew から Hugging Face（重みの配布元）と pypi.org に届くか。届かなければ G1 で止まる
- Qwen3.8-27B（Hugging Face の `Qwen/Qwen3.8-27B`、Apache-2.0、BF16 の重み、思考の出力が既定で有効）が、andrew の RTX A6000 二枚で BF16 のまま動くか。どの推論の道具で動くか。1 フレームの所要
- 文埋め込み `Qwen/Qwen3-Embedding-0.6B`（Apache-2.0、1024 次元）が andrew で動くか
- 重み（約 56 GB。起票者の計算）・仮想環境・取得の一時置き場を、Syncthing の同期の対象の外に置ける場所が andrew のどこにあるか。`/home/ubuntu/slocal2/stage2pilot_store`（以下 `$S`）は bengio と andrew の間で同期される（t2p-match の SPEC §1.3）
- V→T の入れ替えの対応表（直しの契約 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle の P0 の入れ替え）が、本契約のフレームの集合を覆うか
- VLM の学習データに EgoSurgery の画像が入っているか（学習データは非公開。本契約では測れない。報告に UNKNOWN と書く）

### 1.3 前提の道具と材料（Task A・B で起点と andrew にあることを確かめる）

- 道具: `scripts/stage2pilot/dp_train.py`（`--fixed-epochs`、`--record-epochs`、`--save-last-probs`、`--scope`）、`dp_model.py`（FiLM、SetAttention）、`scripts/train_t1b.py`、`scripts/w23/` の台本と照合・恒等性の道具、t2p-match の集計の道具（`experiments/analysis/grasp_hand_graph_t2p/tools/`）
- 材料: 工程塔の重みと特徴のキャッシュ（P\*-15-COCO Fold A seed 42）、T→P の入れ替えの対応表、検出塔の checkpoint、P→T の入れ替えの対応表。置き場は前回の契約の台本と audit から実行者が読む

## 2. 禁止と申し送り

- 注入される規約の節（prohibitions・issuer_cautions・env_p0・folds・split・symmetry・det_groups）に従う
- 禁止は実行者の操作に対するものである。Syncthing による他の台への配布（本契約の出力が bengio に届くこと、他の契約の出力が届くこと）を含まない
- **画像と記述を andrew の外の計算機やサービスへ送らない。** 外への接続は、重みと道具の取得（Hugging Face と pypi.org などの配布元からの取得）だけに使う。外部の API、Web の推論の窓口、W&B の送信は使わない（W&B は offline）
- `$S` の既存の中身、前回までの予備測定の run の置き場と集計、data の raw と external と注釈、凍結した塔の重み、既存の checkpoint、third_party、既存の仮想環境（`.venv`、`.venv-relation-detr`）を変えない
- 本契約の出力は、`$S` の下の新しいフォルダ `vlm_caption_signal_pilot/`、allow_write の二つの接頭辞の下、§3.1 の同期の外の置き場にだけ書く。run の記録は `experiments/phase1/vlm_caption_signal_pilot_` で始まる名前の下に置く。道具の既定の置き場が別で引数で変えられないなら、停止して利用者に尋ねる
- **VLM の重み・文埋め込みの重み・新しい仮想環境・取得の一時置き場は、同期の対象の外に置く。** 同期の対象のフォルダは Syncthing の設定を読んで確かめる（設定は読むだけで変えない）。repo の中にも `$S` の中にも置かない
- 塔（検出塔・工程塔）は学ばない（W2・W3 で受け取り手の一部を学ぶのは interface の学習の一部で、塔の重みの原本は変えない）
- 既存の道具は足す形で直す。既定の挙動（引数を足さないときの挙動）を変えない。新しい config は新しい名前のファイルで足す
- runindex と context/auto の生成物は作り直さない。`*-check` は回さない（`make forbidden-check` は回す）
- GPU を使ってよいのは andrew の 2 枚だけ。本契約以外の compute プロセスがあれば止めずに停止して利用者に尋ねる（プロセスの数え方は `/proc/PID/exe` の解決か引数の完全一致で。andrew が容器の中なら、全体の使用量とプロセス一覧の差も見る）
- 利用者は途中の確認を求めていない（§0 の 5）。escalate_if に当たらない判断（読みの曖昧さ、手順の選択）は実行者が決め、逸脱として記録して続ける

## 3. VLM の記述の生成

### 3.1 モデルと置き場

- VLM は `Qwen/Qwen3.8-27B`、文埋め込みは `Qwen/Qwen3-Embedding-0.6B`。どちらも Hugging Face から取得し、取得した版（commit の識別子）、ファイルごとの sha256、ライセンスの表記を記録する。別のモデルや量子化した版に替えない（載らなければ escalate_if）
- 重みは BF16 のまま、GPU 二枚に分けて載せる。推論の道具（vLLM か transformers など）は実行者が選び、版と選んだ理由を記録する
- 新しい仮想環境を同期の対象の外に作る。既存の仮想環境に足さない

### 3.2 入力

- 1 回の問い合わせに、フレーム t の画像 1 枚だけを入れる。過去・未来のフレームは入れない
- 画像は原寸のまま渡し、縮小はモデルの前処理の既定に任せる。前処理後の画素数と画像のトークン数を記録する
- 工程名・術式・術具名の一覧・塔の予測・正解のラベルは入れない

### 3.3 プロンプト（本文は変えない。形式の直しは §3.5 だけ）

    You are looking at one frame from a head-mounted camera worn by a surgeon during open surgery.
    Describe only what is visible in this frame.
    Do not name any surgical instrument, device, or material by its type. If you need to refer to one, write "an instrument".
    Do not name the procedure, the surgical step, or the surgical phase.
    If something cannot be judged from this frame, use "cannot tell".
    Answer with one JSON object and nothing else, with these keys:
    "wound": one sentence on the state of the skin and the wound.
    "tissue_action": one sentence on what is being done to tissue at this moment.
    "surface": one sentence on the surface of the operative field (blood, fluid, coloring or lines on the skin, things placed on the skin).
    "visibility": one of "field visible", "field hidden by hands or head", "camera not facing the field".
    "attributes": an object with these keys, each with exactly one of the listed values:
      "skin": "intact", "marked only", "cut and open", "partly closed", "fully closed", "covered", "cannot tell"
      "depth": "skin surface", "fat layer", "deeper layer", "cannot tell"
      "stitches": "none", "thread through the wound", "row of knots", "cannot tell"
      "spread": "held open", "not held open", "cannot tell"
      "bleeding": "none", "oozing", "pooled", "cannot tell"
      "wetness": "dry", "wet or pooled", "cannot tell"
      "skin_color": "antiseptic color", "marking lines", "none", "cannot tell"
      "placed": "bandage or tape", "tube", "implant or graft", "none", "cannot tell"
      "action": "grasp or pull", "cut", "burn", "pass a needle", "tie", "wipe or press", "suck fluid", "rinse", "inject", "draw lines", "no action", "cannot tell"
      "target": "skin", "under the skin", "deep tissue", "thread or needle", "handing over", "cannot tell"

### 3.4 生成の設定

- 思考の出力を無効にする（`enable_thinking` を偽にする。モデルの説明の書き方による）。復号は greedy（温度 0）、出力の上限は 768 トークン。設定の全文を記録する
- 生成するのは Fold A の train と val のフレーム全部。フレームの集合は、V→P の特徴のキャッシュのフレームの集合と、V→T の Fold A の COCO の train と val の画像の集合の和で、両者が同じことを確かめる（違えば和を生成し、違いを記録する）
- 同じ入力での繰り返しの一致: val から等間隔に 50 フレームを選び、同じ設定で 2 回目を生成し、文字列が完全に一致する割合を記録する（判定には使わない）

### 3.5 出力の形式の確かめ（追加動画 17〜21 のフレームだけ）

- 本番の前に、17〜21 から等間隔に 30 フレームを選んで生成し、JSON として読めるか、鍵と選択肢が §3.3 どおりか、§4.1 の伏せる語がどれだけ出るかを数える
- 読めない・鍵が違う出力があれば、**出力の形式の指示だけ**（例: JSON の前後に文を書かない旨の一文）を直してよい。記述の中身に関わる指示は変えない。直しは 2 回まで。直しの前後の文と理由を記録する
- 直し終えたらプロンプトの全文の sha256 を記録し、本番の生成はその文だけで行う
- 動画 01〜15 の画像をこの確かめに使わない

### 3.6 記録

- フレームごとに、生の出力、解析した結果、解析の成否、応答の拒否（記述を返さない出力）の有無を JSONL に保存する（`$S/vlm_caption_signal_pilot/` の下）
- 数える量: 解析の失敗、応答の拒否、鍵ごとの「cannot tell」の割合、属性の値の分布、同じ文字列の記述の数（鍵ごと）、§4.1 の伏せた語の数（鍵ごと・三通りごと）、1 フレームの所要
- 報告には val のフレームから等間隔に 20 件の記述（甲の伏せ字の後）を例として載せる

## 4. 信号

### 4.1 伏せる範囲（甲・乙・丙）

三通りとも **§3 の一回の生成から作る**（生成を三回しない）。違うのは記述から取り除く範囲だけである。伏せた語は `something` に置き換えてから数値にする。照合は大文字と小文字を区別せず、語の境界で切り、複数形を含め、長い語句から先に当てる。

| 範囲 | 取り除くもの |
|---|---|
| 甲 | 術具 15 クラスの名前（`data/annotations/egosurgery_tool` の COCO の categories から読む）と下の同義語、工程 9 種の名前（工程 CSV のラベルの集合から読む）と下の綴りの違い |
| 乙 | 甲に加えて、下の語幹で始まる語すべて（動詞・形容詞を含む）。属性の値のうち、英語の名前に語幹を含むものは「cannot tell」に寄せる |
| 丙 | 甲と同じ伏せ字に加えて、tissue_action の文と、属性 action と target を信号から外す（その部分を 0 にする） |

- 甲の同義語（起票者が決めた。足すなら逸脱として記録）: tweezer、pickup、sponge、needle driver、suction tube、sucker、shears、cautery、electrocautery、diathermy、bovie、knife、knives、blade、periosteal elevator、elevator、bipolar、gag。工程名の綴りの違い: anaesthesia、haemostasis
- 乙の語幹: disinfect、design、anesthe、anaesthe、incis、dissect、hemosta、haemosta、irrigat、clos、dress、tweez、gauze、forcep、gag、suction、suck、scissor、retract、cauter、diatherm、hook、scalpel、raspator、bipolar、syring、skewer
- §3.3 のプロンプトの選択肢の名前に甲の語が無いことを、甲の照合器で確かめる（0 件であること）

### 4.2 数値の信号

- 鍵ごとの文（wound、tissue_action、surface）を、伏せ字の後に文埋め込みで 1024 次元にし、L2 で正規化する（指示文は付けない）。文が無い・解析に失敗した鍵は 0 にする
- 属性は鍵ごとの one-hot（visibility 3、skin 7、depth 4、stitches 4、spread 3、bleeding 4、wetness 3、skin_color 4、placed 5、action 12、target 6）。解析に失敗したフレームは属性をすべて 0 にし、解析の失敗の旗（1 次元）を立てる
- 一本のベクトルを受け取る型（D1-L2、D2、P1、P2L）には、[wound, tissue_action, surface, 属性, 旗] をつないだベクトルを渡す。次元は 3 × 1024 + 55 + 1 = 3128 で、三通りで同じ
- 集合を受け取る型（D3-L2）には、wound・tissue_action・surface の文の 3 個と、属性と旗を 0 で埋めて 1024 次元にした 1 個の、計 4 個のトークンを渡す。丙では tissue_action のトークンを無いもの（mask）として扱う
- 次元と並びの定義を記録し、三通りで同じことを示す

### 4.3 入れ替えた信号

- 予測の信号と同じ値を使い、フレームとの対応だけを壊す。train は train の間で、val は val の間で、それぞれ一つの固定の並べ替えで入れ替える。split 全体のフレームにわたって並べ替える（動画の中だけで入れ替えない）。学習時と評価時の両方で入れ替えた信号を使う
- V→P は T→P の対応表、V→T は P→T の対応表を使う。対応表が本契約のフレームの集合をちょうど覆わなければ、seed 42 で新しく作り、理由を記録する
- 三通り（甲・乙・丙）で同じ並べ替えを使う。元と同じフレームに来る割合と、同じ動画から来た割合を記録する

### 4.4 交差適合をしない理由

VLM は本研究のラベルで学習していないので、送り手の train と val の差がラベルへの過適合から生じない。そのため予測の腕は一本（train も val も同じ VLM）で、conventions#crossfit は当てない。プロンプトの形式の確かめは追加動画だけで行い（§3.5）、Fold A の動画を見て直さない

## 5. 腕と run

### 5.1 腕（型 × W ごとに同じ組）

| 腕 | 信号 |
|---|---|
| 空 | 零の信号（V→P は前回の空の腕と同じ作り方、V→T は `--zero-ctx`）。次元は予測の腕と同じ。三通りで共通の一本 |
| 予測-甲・予測-乙・予測-丙 | §4.2 の信号 |
| 入替-甲・入替-乙・入替-丙 | §4.3 の信号 |

### 5.2 本数

| 群 | 本数 |
|---|---|
| V→P: 3 型（D1-L2・D2・D3-L2）× 3 W × 7 腕 | 63 |
| V→P: 4 epoch で止める確かめ（W ごとに D2 の予測-甲） | 3 |
| V→P: 既定の挙動の確かめ（前回の T→P の D2 の予測-noCF・W1 を本契約の識別子で回し直す） | 1 |
| V→T: 2 型（P1・P2L）× 3 W × 7 腕 | 42 |
| V→T: 4 epoch で止める確かめ（W1 の P1 の予測-甲） | 1 |
| 計 | 110 |

- V→T の既定の挙動の確かめは、学習の run ではなく、変更の前と後の版で同じ既存の腕（前回の P1 の予測-noCF・W1）の試走（1 epoch の短い経路）を回し、損失と val の出力が一致することで示す
- 塔単独（学習なし）は記録の値を使い、本契約の識別子で 1 回だけ評価して一致を示す

### 5.3 対称性の表（conventions#symmetry の様式）

**表 1 — 同じ型・同じ W の腕どうし（腕1 = 予測-甲、腕2 = 同じ型・同じ W のほかの腕）**

| 条件 | 腕1 | 腕2 | 判定 | 理由 |
|---|---|---|---|---|
| 受け取り手 | V→P は P\*-15-COCO Fold A seed 42、V→T は D\*-COCO Fold A seed 42 | 同じ | 揃える | |
| 凍結範囲と学習範囲 W | W1・W2・W3 の各水準 | 同じ水準 | 揃える | 同じ W の中でだけ比べる |
| interface の型・入力の次元・容量・入れる位置 | 型ごとの interface、入力 3128 次元（D3-L2 は 4 トークン × 1024） | 同じ | 揃える | 空の腕も同じ次元の interface を持つ |
| 入力解像度・前処理・増強 | 前回の予備測定と同じ | 同じ | 揃える | |
| 教師の種類と量 | Fold A の train の受け取り手のタスクのラベル | 同じ | 揃える | |
| 学習の長さ | 4 epoch の固定（副次 8・12・16） | 同じ | 揃える | §6.1 |
| 学習率・weight decay・batch・数値精度 | §1.1 と §6.2 で写した値 | 同じ | 揃える | |
| seed | 42 | 42 | 揃える | |
| 送り手の信号の中身 | 甲の伏せ字の記述 | 乙・丙の伏せ字、空、入れ替え | 意図的に変える | 本契約の問いそのもの |
| フレームとの対応 | あり | 入れ替えの腕だけ壊す | 意図的に変える | 信号の中身を読む対照 |
| 送り手の初期化の鎖 | 公開重みの VLM（学習データは非公開） | 同じ VLM | 揃える | 腕の間で送り手は一つ |
| ホストと装置型 | ilya、RTX 6000 Ada Generation | 同じ | 揃える | 利用者指定の実行先 |

UNKNOWN: 0 件。

**表 2 — 本契約の腕と前回の参考の値（腕1 = 本契約の予測-甲、腕2 = 前回の同じ型の予測-noCF。参考の列にだけ並べ、差は取らない）**

| 条件 | 腕1 | 腕2 | 判定 | 理由 |
|---|---|---|---|---|
| 受け取り手・W の定義・学習の長さ・学習設定・seed・評価 | §1.1・§6 | 同じ | 揃える | |
| 送り手 | VLM の記述 | 検出塔（T→P）または工程塔（P→T）の出力 | 意図的に変える | 比べる対象そのもの |
| interface の入力の次元 | 3128（D3-L2 は 4 トークン） | 前回の型の信号の次元 | 意図的に変える | 送り手の出力の形が違う |
| 送り手の交差適合 | なし | なし（noCF） | 揃える | |
| ホストと装置型 | ilya、RTX 6000 Ada Generation | andrew、RTX A6000（T→P の W2・W3 と P→T の一部は bengio） | 異なる | 過去の値は参考列に載せる。実行先変更の指示と t2p-match の RESULT §3 |

UNKNOWN: 0 件。

## 6. 学習と記録

### 6.1 学習の長さと記録する epoch

- **主**: 4 epoch 学習し、途中で止めず、4 epoch 目の状態を結果にする
- **副次**: 学習率の予定が全体の長さに依らない場合に限り、同じ run を 16 epoch まで続け、8・12・16 epoch 目の状態も記録する。最良の回を選ばない。早期打ち切りを使わない。長さに依る場合は 4 epoch だけ回し、理由を報告に書く（停止しない）
- 続けた run の 4 epoch 目が 4 epoch で止めた run と同じことを、§5.2 の確かめの run で示す。V→P で一致しなければ主の値は 4 epoch で止めた run を全腕で回して取る。V→T で一致しなければ、主の値は続けた run の 4 epoch 目のまま使い、食い違いの大きさを報告に書く（V→T を全腕回し直すと所要が約 1.25 倍になるため。起票者の判断）

### 6.2 学習設定

- V→P は T→P の run（W1 は `stage2fix_dp_*`、W2・W3 は `w23b_dp_*` の D1-L2・D2・D3-L2）の config と記録から、V→T は P→T の run（W1 は `stage2fix_pd_*`、W2 は `w23*_pd_*`、W3 は `w3lra_pd_*` の P1・P2L）の config と記録から写す。写した値と出所を報告に書く
- 同じ方向の型の間で食い違えば停止して利用者に尋ねる（escalate_if）
- optimizer の群ごとの学習率と weight decay の実際の値を学習の記録から読み、写した値と比べる。W ごとに、受け取り手の側の学ぶパラメータの名前の集合を記録する
- V→T の新しい config は、入力の次元だけを 3128 に変えた写しにする（`pd_film_d9.py` と `pd_clsbias_lin_d9.py` からの写し）。次元以外の差が 0 であることを示す

### 6.3 評価と保存

- 評価は val（動画 09・10）
- V→P の指標: 6 工程の Jaccard（主。val に現れる 7 工程から dressing を除いた平均。前回と同じ定義）、frame accuracy、7 工程の Jaccard、工程別 Jaccard、動画ごとの値。記録する epoch ごとに val の確率を保存する
- V→T の指標: signature class AP（主。conventions#det_groups の標的群）、overall mAP、陰性対照群 AP、クラス別 AP、動画ごとの値。記録する epoch ごとに val の予測を保存する（`--save-predictions-all`）
- 各 run で、interface の零から始まる層の重みの大きさ（L2）を記録する epoch ごとに保存する
- 並行は GPU 2 枚 × 数本まででよい。並行の数を記録する。VLM の生成は学習の前に行い、生成と学習を同じ GPU で同時に回さない
- 進み具合が利用者に見えるよう、V→P の全本が終わった時点と、V→T の各 W が終わった時点で、その時点の集計（REPORT の途中版）を分岐に commit して push する（PR は最後でよい）

## 7. 読み方（差を出すだけ。採否・順位は書かない）

- **同じ型・同じ W・同じ epoch の中だけで比べる。** 主は 4 epoch 目。W2・W3 では空の腕も塔単独から動くので、塔単独との差は W1 でだけ書く
- 出す差（V→P は 6 工程の Jaccard・frame accuracy・7 工程の Jaccard、V→T は signature class AP・overall mAP・陰性対照群 AP を並べる）:

| 差 | 読むこと |
|---|---|
| 予測-x − 入替-x（x は甲・乙・丙） | フレームに対応した信号の中身による差（主） |
| 入替-x − 空 | 信号の値の分布だけによる差 |
| 予測-x − 空 | 信号を入れたことの全体 |
| 予測-乙 − 予測-甲、予測-丙 − 予測-甲 | 伏せる範囲を広げたときの変化 |
| 前回の同じ型の 予測-noCF − 入れ替え | 参考の列（差は取らない） |

- V→P の差には ±0.015（§1.1）を並べて書く。この幅の中の差は「読めない」と書き、符号で解釈しない。V→T は揺れの幅を測っていないと書く
- 腕の間で argmax が一致する割合と、指標がちょうど同じになった差の数を、W と epoch ごとに記録する（V→P）
- epoch の間で最良を選ばない。全部の値を並べる

### 7.1 予測（結果を見る前に書く。当たり外れを報告する）

1. 4 epoch 目の V→P で、9 組（3 型 × 3 W）のうち過半で、予測-甲 − 入替-甲 ≥ 予測-乙 − 入替-乙（6 工程の Jaccard）
2. 同じく 9 組のうち過半で、予測-甲 − 入替-甲 ≥ 予測-丙 − 入替-丙
3. 4 epoch 目の V→P の W1 で、3 型とも 予測-甲 − 入替-甲 は前回の T→P の同じ型の 予測-noCF − 入れ替え（§1.1）より小さい
4. 4 epoch 目の V→T の W1 で、P1・P2L とも 予測-甲 − 入替-甲（signature class AP）は前回の P→T の同じ型の値（§1.1）より小さい

## 8. 手順

**コマンドは書かない。実装と記録を読んで決めてよい。** 命令と出力は `audit.md` に残す。

- **Task A（開始状態と置き場）**: 分岐が `feat/` で始まること、起点、§1.3 の道具と記録の在否、未追跡、compute プロセス、`$S` の空き、試験の失敗の名前、既存の仮想環境の要約値、GPU の電力の上限を記録する。`meta.created_from` と `conventions_rev` を測って差し替える。Syncthing の設定を読み、同期の対象のフォルダの一覧を記録し、その外に重み・仮想環境・取得の一時置き場を決めて空きを測る。Hugging Face と pypi.org に届くかを確かめ、§3.1 の二つの重みを取得して版・sha256・ライセンスの表記を記録する。欠けがあれば G1 で止まる
- **Task B（材料と形式）**: 前回の材料（工程塔の特徴のキャッシュ、二つの方向の入れ替えの対応表、検出塔の checkpoint）の要約値を記録と照合する。両方の塔単独の val を本ホストで評価し、記録と比べる（許容 0.005）。§6.2 の学習設定を写し、型の間で食い違わないことを確かめる。新しい仮想環境で VLM を GPU 二枚に載せ、§3.5 の形式の確かめを行い、1 フレームの所要と記憶量を測り、§3.4 の生成の全体の所要を見積もって記録する
- **Task C（生成と信号）**: §3.4 のフレームの集合を確かめて生成し、§3.6 を記録する。§4 の三通りの信号と入れ替えた信号を作り、目録（要約値、フレーム数、次元、被覆）に書く。通した動画の集合を記録する
- **Task D（道具と確かめ）**: dp_train.py と train_t1b.py（とその台本）に VLM の信号を読む口を足す形で実装し、V→T の新しい config を足す。§5.2 の既定の挙動の確かめを行う。学習前の出力が全腕で塔単独と一致すること、interface の零から始まる層を N(0, 0.05²) にすると出力が変わること（陽性対照）を示す。空の腕のうち入力が届かない型（D1・D3 の空の腕）は、同じ型の入力のある腕で陽性対照を示す（前回の起票者の誤りの再発を避けるため。t2p-match の RESULT §4）。腕ごとの信号の出どころが §5.1 の表と一致することを示す
- **Task E（V→P）**: §5.2 の V→P を回す。確かめの run を先に回し、結果で残りを決める。全本の終了を確かめる（存在しない run の名前で 0 件になることも示す）。途中の集計を push する
- **Task F（V→T）**: §5.2 の V→T を W1、W2、W3 の順に回す。W ごとに途中の集計を push する。所要が Task B の見積もりの 1.5 倍を超えたら、その時点の実測と見直した見積もりを audit と途中の集計に書いて続ける（停止しない）
- **Task G（集計と報告）**: §7 の表を記録から道具で作る（手で写さない）。§10 の構成で報告を書き、`make forbidden-check` を回し、commit・push・PR（base phase0、Draft でない）・`make task-report` を行う

## 9. 完了判定

| # | 判定 | 期待 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態の記録 | spec の acceptance a の項目がすべて audit にある | 存在しない GPU の番号と存在しない実行ファイルの経路で、列挙が 0 件になることを示す |
| b | 重みと置き場 | 二つの重みの版・sha256・ライセンスの表記、道具の版がある。重み・仮想環境・一時置き場の経路が、同期の対象のフォルダのどれの下にも無い | 同期の対象のフォルダの一つの下の経路を同じ検査にかけると「同期の下」と判定される |
| c | 材料と塔単独 | 前回の材料の要約値が記録と一致し、塔単独の val が記録と 0.005 以内。学習設定が写されている | 1 バイト変えた写しで照合が食い違いを出す。学習率を一つ変えた設定で、写しの検査が食い違いを出す |
| d | 形式の確かめとプロンプトの固定 | 確かめに通した動画が 17〜21 だけ。直しの前後の文と理由、固定したプロンプトの sha256 がある。本番の全出力の記録のプロンプトの sha256 が固定した値と一致する | 01 のフレームを混ぜた確かめの入力で、動画の検査が外れを出す。プロンプトを 1 文字変えた写しで sha256 の照合が食い違う |
| e | 生成の記録 | §3.4 のフレームの集合の全部に記述がある。§3.6 の量が数えてある | 記述を 1 件消した写しで、被覆の検査が欠け 1 件を出す |
| f | 三通りの信号と入れ替え | 三通りの次元が 3128（D3-L2 は 4 × 1024）で同じ。甲の照合器でプロンプトの選択肢の名前に一致 0 件。甲・乙・丙の伏せ字が §4.1 の定義どおり。入れ替えた信号を並べ直すと元と一致し、train と val をまたいでいない | 術具のクラス名を一つ含む文を甲の照合器にかけると 1 件を出す。恒等の並べ替えで、元と同じフレームに来る割合が 1 になる |
| g | 恒等性と既定の挙動 | 学習前の出力が全腕で塔単独と一致する。既定の挙動の確かめが記録（V→P）と変更前の版（V→T）に一致する | interface の零から始まる層を N(0, 0.05²) にすると、入力のある腕で出力が変わる。一つの値を 1e-6 ずらした写しで既定の挙動の比べが違いを拾う |
| h | 全本の終了と記録 | §5.2 の全本の終了、記録する epoch の値と確率（V→P）または予測（V→T）、零から始まる層の大きさがそろう。4 epoch で止めた run と続けた run の 4 epoch 目の比べがある | 存在しない run の名前で 0 件。4 と 8 epoch 目の確率（または予測）を同じ検査にかけると差が出る |
| i | 差の表 | §7 の差が全型・全 W・記録した epoch で表にあり、参考の列が並ぶ | 差を記録から測り直してずれが 0。1e-6 ずらした写しを検出する |
| j | test を通さない | 生成・信号・入れ替え・学習・評価の各段で通した動画の集合と {04, 05, 07} の共通が 0 件 | 04 を混ぜた入力で共通が 1 件になる |
| k | 変えていない・送っていない | 既存の中身の要約値が開始時と一致し、試験の失敗の名前が開始時と同じ。forbidden-check で本契約の経路の違反が 0。生成と埋め込みの道具が手元の重みだけを読み、外部の推論の窓口を呼ばないことを、設定と実装を読んで示す。W&B は offline | 本契約の新しいファイルが変更として拾われ、allow_write の許可として名指されることを示す。外部の窓口の URL を一つ足した設定の写しを同じ検査にかけると外れを出す |
| l | PR | Draft でない PR が base phase0・分岐 feat/vlm-caption-signal-pilot で在る | 分岐名と base を `gh pr view` の出力で示す |

## 10. 報告の構成

`RESULT.md` は 150 行以内。節は 判定（status と G1〜G6）／完了判定（表。実測値つき）／実測（次の契約で使う値: 重みの版と置き場、生成の所要と記憶量、解析の失敗と拒否と伏せた語の数、写した学習設定と出所、学習率の予定が長さに依るか、入れ替えの対応表と割合、§7 の主な差の要約〔4 epoch 目、方向・型・W ごと〕、零から始まる層の大きさの要約、§7.1 の予測の当たり外れ、所要）／起票者の誤り（一件 3 行以内）／逸脱／想定外・UNKNOWN（VLM の学習データに EgoSurgery が入っているかは UNKNOWN と書く）／送出（PR 番号と終了コードだけ）。

命令とその出力、参照の解決の全文、対照の出力、変更範囲の一覧、台帳の応答は `audit.md` へ。`RESULT.md` から `audit.md` を行番号で指し、同じ内容を二度書かない。全値と表、記述の例 20 件は `experiments/analysis/vlm_caption_signal_pilot/REPORT.md`（記録から道具で作る）。

## 11. 次の契約と申し送り

- 本契約の結果は、VLM の記述を補助信号として次の予備や提案カードに進めるか、伏せる範囲をどう決めるかを、利用者が考える材料にする。進めるかは利用者が決める
- 手術向けの VLM（SurgAtlas-VLM、SurgVLM）は重みが手に入った時点で、本契約の §3〜§5 をそのまま当てて足せる（受け取り手と腕は同じ）
- 費用（壁時計、GPU 時間）は記録であり、判断に使わない

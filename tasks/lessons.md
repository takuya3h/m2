# Lessons — ミスと再発防止ルール

セッション中のミスを記録し、**記憶でなく仕組み**で再発を防ぐ。新しいミスは必ずここに追記する。

---

## 2026-05-30 セッションのミス全件分析

### カテゴリA: 架空生成 (幻覚) — 最重大
確認していない数値・ファイル状態を「事実」として報告した。研究インテグリティの根幹を脅かす。

- **A1. epoch8 mAP=0.692 架空値**: Sense-X 9enc 中止記録で、評価済みは epoch7(0.696)までなのに STOPPED ファイルと experiment_log に「e8=0.692」と実在しない値を記載。→ 実ログ照合で発覚し訂正。
- **A2. gdown/COCO重みDL「成功」架空報告**: pip 無い venv で実際は失敗していたのに「成功」と報告。さらに `rekeyed.pth`・`dim_rekey.py` 等**実在しないファイルを前提に検証を重ねた**(プレフィックス問題も架空)。
- **A3. s0_022 mAP=0.473 架空生成**: metrics.json 未生成(未確認)なのに「mAP=0.4732」と数値を生成し、AskUserQuestion でユーザーの判断材料にした。実際の途中値は別(best 0.29)。

**根本原因**: 並列バッチの途中キャンセルで「後続コマンドが未実行なのに結果が見えた」錯覚 + 期待値を事実と混同。

**再発防止ルール (厳守)**:
1. **数値・ファイル状態・プロセス状態は、必ず Read/cat/ls の"生出力"を当該ターンで取得し、それだけを引用する**。前ターンの記憶・期待値・推測は report に書かない。
2. metrics 値は `metrics.json` を Read した生JSON、または python集計の stdout をそのままコピー。**手打ち・暗算・記憶からの転記は禁止**。
3. ファイル作成/DL の「成功」は、直後に `ls -la`(サイズ) + 用途別検証(torch.load/compile)の生出力を見てから宣言する。
4. AskUserQuestion に数値を載せる前に、その数値のソース(ファイルパス+生出力)を同一ターンで確認済みであること。

### カテゴリB: 並列実行の制御不全
- **B1. 並列バッチ多投**: 1メッセージに10〜30個の tool call を詰め、1つのエラーで全部巻き込みキャンセル。どれが実行されたか不明になり A1-A3 の温床に。
- **B2. pkill exit code 連鎖キャンセル**: `pkill` が対象なしで exit 1 を返し、同一バッチの後続コマンドを巻き込んでキャンセル。

**再発防止ルール**:
1. **状態確認・ファイル作成・破壊的操作は単独 tool call で実行**。並列は「相互に独立かつ非破壊な読み取り」に限る。
2. `pkill`/`kill` は必ず `|| true` を付け、かつ**単独実行**(後続を巻き込まない)。
3. 1メッセージの tool call は原則5個以内。多段検証は1つずつ結果を見て進める。

### カテゴリC: 検証前の結論
- **C1. rank1ログ誤読**: rank1ログが小さいのを「クラッシュ」と誤診(実際は mmdet が rank0 のみログ出力する正常仕様)。samples_per_gpu 削減を危うくしかけた。
- **C2. Stable-DINO 本番「成功」早まり報告**: 走行確認前に Slack 通知。実際は unset 未適用で CUDA 衝突即死。
- **C3. DI-MaskDINO「modeling改修要」誤診**: 実際は config 1行(OUT_FEATURES 継承漏れ)で直る浅い問題だったのに「深い問題」と memory に誤記。
- **C4. 誤kill を「実害ゼロ」と誤判定**: exit code ブロックで安全と思ったが、実際は rc=137 で seed42 を殺していた。

**再発防止ルール**:
1. **「成功」「完走」「正常」を報告する前に、GPU使用率 + iter番号 + ファイル実在 の3点を生出力で確認**する(3点確認ルール)。
2. プロセスの生死は GPU使用量(nvidia-smi)で判断。pgrep 数値は自己カウント混入で信用しない。
3. 異常の原因究明は「推測した修正を入れる前に、関連変数を print して事実を掴む」(デバッグ駆動)。rank1ログ等のフレームワーク固有挙動は memory:[[mmdet2x-ddp-gotchas]] を先に参照。
4. kill 後は「対象PIDの /proc 消滅 + GPUメモリ解放」を確認してから次へ。exit code だけで判断しない。

### カテゴリD: 破壊的操作の不注意 — 最重大(実害発生)
- **D1. 走行中 DI-MaskDINO seed42 を誤kill**: 「Relation-DETR残骸掃除」のつもりが `pkill -9 -f train_net_egosurgery`(=走行中 DI-MaskDINO 本体)を投下。rc=137 で iter15599 の学習を破壊。

**再発防止ルール (最優先)**:
1. **kill 前に「今 GPU で何が走っているか」を nvidia-smi --query-compute-apps で確認し、kill 対象 PID を明示列挙**してから実行。`pkill -f <pattern>` の広域パターンは使わず、**nvidia-smi が示す PID を直接 kill** する。
2. 停止したいのが「launcher だけ」なら launcher の PID のみ。「特定実験だけ」なら work_dir/seed で PID を特定。**パターンを広げない**。
3. `scripts/safe_gpu_cleanup.sh` を使う(稼働中実験を列挙→確認を促す設計)。

### カテゴリE: 手作業の精度
- **E1. Slack 平均値 手打ちミス**: Relation-DETR seed456 を 0.7269 と手打ち(正 0.7220)、平均 0.7284(正 0.7268)を誤報告。「metrics.json 直読みで出す」と決めた直後に手打ちを混ぜた。
- **E1-再発 (2026-05-31)**: 9enc s0_013 を Slack に mAP=0.7266/AP_rare=0.7564/mAP_50=0.871 と手打ち(正 0.7180/0.7435/0.856)。**notify_experiment.py が正しいテキスト(mAP 0.7180)を直前に stdout 出力していたのに、それを貼らず記憶から別値をタイプした**。スレッドで訂正。

**再発防止ルール**:
1. **複数検出器/seed の集計は必ず `scripts/report_detector_results.py` で生成**し、その stdout をそのまま貼る。手打ち・部分転記しない。
2. **Slack/Notion へ数値を出すときは notify_experiment.py / report_detector_results.py の stdout を一字一句コピペ**する。`slack_send_message` の message に数値を**自分でタイプしない**。1値でも手で書いたら E1 再発とみなす。生成器の出力ブロックをそのまま渡すこと。

### カテゴリF: 証跡の完全性
- **F1. config.yaml 欠落で verify FAIL**: post_process_relation_detr が config.yaml を生成せず、verify_seed_integrity が必須証跡欠落で FAIL。
- **F2. AP_common=nan**: 最初の post_process_detrex で NaN除外を入れ忘れ(Retractor が val 非存在)。→ 修正済。

**再発防止ルール**:
1. 新しい post_process スクリプトは、**ExperimentManager と同じ必須証跡**(config.yaml/command.sh/git_commit.txt/metrics.json/per_class_ap.json/notes.md/server.txt)を全て生成する。
2. seed群完走後は必ず `verify_seed_integrity.py --group <det>` を通し、PASS を確認してから「完了」と report。

### カテゴリG: 学習の生死の誤診 — 破壊操作に直結する最重大の誤判断
2026-05-30 セッション再開時、稼働中の Phase E を **2度誤診**した(いずれも実害寸前で回避)。
- **G1. 「ゾンビGPUメモリ→要GPUリセット」**: `nvidia-smi --compute-apps` の PID を `/proc` で
  DEAD 判定し、実際は稼働中の2学習を「死んだメモリ」と誤認。**リセットしていたら稼働中の
  計算(計~5h)を破壊していた**。
- **G2. 「seed42クラッシュ→resume要」**: `metrics.json` が iter 凍結(eval中) + `ps` grep に
  出ない、でクラッシュと誤認。実際は **eval フェーズで training metrics が一時停止しただけ**。
  危うく存在しない問題を報告するところだった(捏造に近い誤報)。

**根本原因**: 生死を**単一の曖昧な信号**(compute-apps の PID 表示 / metrics.json の mtime /
ps grep)で判断した。どれも単独では誤る(PIDは再spawnで変わり表示も残る、eval中はmetrics凍結、
grepは子プロセス・表記揺れを取りこぼす)。

**G3. オーケストレータが `set -u` + venv activate で無言死 (2026-05-31)**: nohup 常駐の
orchestrate_phaseE.sh が seed456 起動の `source .venv/bin/activate` で死亡。原因は
**`set -u`(nounset)下では activate 内の未定義変数参照(`$PS1` 等)が即 fatal 終了**になること。
seed42 完走後処理までは正常だったが launch_seed で初めて activate に到達して落ち、seed456 が
16分起動せず GPU が遊んだ。**防止**: 常駐スクリプトで venv activate する箇所は必ず
`set +u; source activate; ...; set -u` で囲む(または venv python を直叩きして activate を避ける)。
nohup 常駐プロセスは「最後のログ行が進んでいるか」「pid が /proc にあるか」を定期確認する
(無言死を検知するため)。

**再発防止メカニズム (willpower でなく機械化)**:
1. **生死判断は `scripts/train_status.py` を唯一の正規ルートにする**。時間差2サンプルで
   COMPLETED/TRAINING/EVALUATING/STALLED/DEAD/NOT_STARTED を一意分類。iter増加→TRAINING、
   iter不変でも log.txt 更新中→EVALUATING(**evalを死と誤認しない**)。プロセス検出は ps grep でなく
   `/proc` 全 cmdline を workdir で走査(PID変化・子プロセスに頑健)。**実証済**(稼働中seedをTRAININGと判定)。
2. **GPUリセット/kill の前に必ず `train_status.py --can-i-reset`**。稼働中が1つでもあれば exit 3 で禁止。**実証済**。
3. `safe_gpu_cleanup.sh --kill <PID>` にゲート**組込済**: 対象が稼働中学習なら `--force` 無しで拒否(実証済 exit3)。
4. **metrics.json の mtime 凍結だけ / PID表示の有無だけ で死亡判定しない**(eval中は数分凍結が正常)。

---

## 教訓: np.load の NpzFile は遅延ロード — ループ内で `d["key"]` を繰り返すな (2026-06-15)

**症状**: `train_s4_tecno.py` の smoke が出力ゼロで SIGKILL(exit 137)。val(小)は生存、train(大)で死亡。
**原因**: `{str(fid): d["features"][i] for i, fid in enumerate(d["frame_ids"])}`。`d=np.load(...)` の
`NpzFile` は **アクセス毎に zip から全配列を再展開**する。9657 回ループ = 79MB×9657 ≈ 760GB の反復読込で OOM kill。
**修正**: `feats_all = d["features"]` と**一度だけ**取り出してから添字アクセスする。
**一般則**: `np.load(npz)` の戻り値は dict 風だが遅延 I/O。ループ前に必要 array をローカル変数へ実体化する。
**切り分けの効いた手**: 段階 print(`flush=True`) を前景で流し「どの行で消えるか」を特定。exit 137 + 出力ゼロ
は「最初の print 到達前に kill」= import/load 段の重さを疑う。`| grep` 越しだと python の kill が
パイプ成功で隠れる(PIPESTATUS を見るか直接実行)。

## L: matched(対応のある)差の有意性は base群σ でなく paired-σ で測る（2026-06-20）
**症状**: 三角形 Δ（S4″−S4）の判定に base 3-seed の σ を流用したら accuracy ΔL2=+0.37 が「有意(改善)」と出た。
だが per-seed 差は +0.79/−0.33/+0.66pp で **seed123 が負**＝符号混在。対seed差の σ(0.61)は平均(0.37)を上回り、実際はゼロと区別不能。
**根因**: matched 差の分散は **対応差(paired)の分散**で評価すべき。独立群(base)の σ を代用すると seed 間で相殺する符号反転を見落とし**偽陽性**を出す。
**ルール**: 三角形 Δ の §10.1 判定は「|平均(対seed差)| > paired1σ **かつ** 全 seed 同符号」。`analyze_phase_coupling.py` に実装。
**併発教訓(小標本の罠)**: n=2 で「segmental +5〜10pt 予備有意」と見えた解離が n=3 で全消滅（paired σ ≫ 平均）。
**予備値は必ず「予備・要 n 増」と明示し、n を増やして潰す**。撤回は記録に残す(experiment_log 2026-06-20)＝Fail Loud の実践。

## L: 学習プロセスの生死は nvidia-smi 単発でなくログ進行で判定（2026-06-19）
`nvidia-smi --query-compute-apps` はクエリ瞬間がカーネル境界だと**稼働中 PID を偽陰性で落とす**ことがある（実際 epoch 6/12 進行中の
seed456 検出が compute-apps に出ず「ハング?」と誤認しかけた）。**生死の確定信号は学習ログの mtime + iter_time/loss の前進**。
0.5s/iter 級の cadence が出ていれば GPU 実行（CPU なら数十倍遅い）。単発スナップショットで kill 判断をしない。

## L: 全 Run は Notion「実験Run台帳」へ記録する（手動転記は server pivot で脱落する）（2026-06-20）
**症状**: lecun の Phase-2 STEP B 21 Run（s0_frozen/s4_phase/b2a/t1a, 06-16〜20）が台帳に1件も無かった。
台帳は philip/aolab の検出器ズー（〜06-01）で止まっていた。
**根因**: `ExperimentManager` はローカル証跡(config/command/git_commit/metrics)を自動生成するが、**Notion 台帳への転記は手動**。
サーバー移行（06-17 lecun）で転記ステップが落ちた。副因: Server select に lecun が無く入れ先が曖昧だった。
**ルール**: Run 完走→証跡確認の直後に台帳へ記録（`docs/notion_run_ledger_recipe.md` 準拠）。
新サーバーは `update_data_source` で Server オプションを追加してから記録。数値は metrics.json 逐語、legacy Step に無ければ空。
**横展**: 「全実験は台帳に記録」(CLAUDE.md/運用ルール)は**自動化されていない手動規約**＝作業フェーズの切れ目で最も落ちやすい。
区切りごとに「台帳件数 vs ローカル Run 数」を突合する。

---

## 即実行チェックリスト (各操作前に自問)

- [ ] **報告する数値**: この値を同一ターンで Read/集計したか? 手打ち・記憶でないか?
- [ ] **「成功」と書く前**: GPU使用率 + iter + ファイル実在の3点を生出力で見たか?
- [ ] **学習の生死を判断する前**: `scripts/train_status.py <workdir>` を回したか? mtime/PID表示の単一信号で「死んだ」と決めつけていないか?
- [ ] **GPUリセット/kill する前**: `train_status.py --can-i-reset` で稼働中ゼロを確認したか? 対象PIDを明示したか? 広域 pkill でないか?
- [ ] **ファイル作成/DL後**: ls -la(サイズ) と用途検証(load/compile)を見たか?
- [ ] **tool call の数**: 5個以内か? 破壊的操作・作成は単独か?
- [ ] **seed群完走後**: verify_seed_integrity を通したか?

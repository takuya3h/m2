# RESULT — T-2026-09-17-frozen-feature-cache-timing

ホスト `efros`（RTX A6000 × 2 / driver 595.84 / nvcc 12.9 / torch 2.1.2+cu118）。2026-09-17 JST。

## 判定

`verdict: partial`。**問いには答えが出た。完了判定 b だけ実測していない**（利用者の判断で
限定版に切り替えた。理由は下記 4）。

| Gate | 判定 | 何を実測したか |
|---|---|---|
| G1（A の後） | pass | 基準 run `pd_refin_empty_seed42` を索引と証跡から特定（処方・seed・折り・主指標が揃う）。装置は仮占有 2 件を停止して compute プロセス 0 件になった |
| G2（B の後） | pass | 別過程で二度生成し `aggregate_sha256` が一致（`96ab87b8…d3183e84`）。塔を seed123 に変えると `5db5f7ef…f84ad8105` へ変わった |
| G3（C の後） | ask | 「キャッシュ経路の run が完走し基準と同じ評価が出た」は**回していない**。上限倍率と実測倍率が先に判明したため利用者へ提示し、限定版で結論とする判断を得た |

## 1. 解決された参照

- `contract.inject_verbatim` = `conventions#prohibitions` / `conventions#issuer_cautions` /
  `conventions#frozen_source`。原文は `context/conventions.md` rev
  `e7a5100597a79b3b9c60935bf38d232f8ae96822` の該当アンカー。要約していない。
- `inputs.sigma_policy` は省略のため `conventions#sigma` の既定値を継承
  （`series: pstd` / `sigma_source: paired_delta` / `delta_sigma_source: paired`）。
  **本契約は sigma を使う判定を持たないため継承のみで適用していない。**
- `inputs.denominator.ref` と `inputs.frozen_source.ref` は spec に無い。凍結源は
  `conventions#frozen_source` の記載どおり実測が一致した
  （sha256 `03936318f9d45ac956fa928278cff9a869d3c2583e86b3af3ac1bbd27675e824` / 195,421,066 bytes）。
- 占位の差し替え: `conventions_rev` = `e7a5100597a79b3b9c60935bf38d232f8ae96822`、
  `runindex_commit` = `96eb3a1ca20ab7eb4b373d93304c9e6b33b733d5`、
  `counts` = index 1266 / experiments 285 / verdicts 1506。

## 2. 完了判定

| # | 判定 | 実測 |
|---|---|---|
| a | 同じ処方で両方の時間 | **一部未達。** 処方は完全一致（命令・config を照合、差 0 項目）。本ホストの実測は 41.8 分/epoch・4.18 h/run。**基準 run の壁時計は散文のみ、GPU 時間はどこにも記録が無い**（UNKNOWN） |
| b | 主指標が一致 | **UNKNOWN。** 6 epoch 完走比較を行っていない（4 を参照） |
| c | キャッシュの決定性 | **達成。** 二度生成で鍵も要約値も一致。塔を seed123 に変えると両方変わった（陰性対照） |
| d | 大きさと空き容量 | **達成。** 1 枚 45,783,450 bytes（学習・増強後の実測平均）／1 epoch 440.3 GB／6 epoch 2.64 TB／折り A の val 87.6 GB／15 動画分 892.3 GB。空きは 6,718,071,545,856 bytes。丸めた表示は使っていない |
| e | W2 の範囲 | **達成。** `freeze_indices=(0,1,2,3)`（`…egosurgery_t1b.py:42-43`）により W1・W2 とも backbone は凍結。境界は layer2/3/4 出力で**同一**。学習対象は W1 266,880 / W2 25,505,568 param（`scripts/train_t1b.py:252-261`） |
| f | 短縮の倍率 | **達成（測り方は限定版）。** step あたり上限 1.049〜1.083×、実測 0.558〜0.661×（＝遅い）。run 全体は step 比がそのまま乗る（1 epoch の 94.7% が学習 step）。キャッシュ生成は別行（下記 3） |
| g | 装置の使用 | **達成。** 開始前 40,361/40,381 MiB・util 100%（利用者の仮占有 2 件）、停止後および終了後は compute プロセス **0 件**・15/35 MiB・util 0% |
| h | PR | **達成。** #181・base `phase0`・`isDraft: false`・分岐 `feat/frozen-feature-cache-timing` |

## 3. 実測

**答え: 4 時間の原因は凍結塔の再計算ではない。**

| 量 | 実測 |
|---|---:|
| 1 step | 0.4937 s（2.03 it/s）。データ供給 0.51% / 順伝播 62.52% / 逆伝播 36.45% / 最適化 0.52% |
| 1 epoch | 4,809 step × 0.4937 s = 39.6 分 ＋ val 評価 1,515 枚 × 0.0877 s = 2.2 分 → **41.8 分** |
| 1 run（6 epoch） | **4.18 h**（記録の「約 4 時間」と整合） |
| 凍結塔の順伝播 | **0.0200〜0.0402 s = step の 4.63〜7.68%**（差分法・4 条件） |
| 上限倍率（塔が無料でも） | **1.049〜1.083×** |
| キャッシュ経路の実測倍率 | **0.558〜0.661×（1.5〜1.8 倍遅い）** |
| キャッシュ読み出し | 0.2482〜0.3712 s/step（91,566,899 bytes、0.367 GB/s） |
| 損益分岐に要る読み速度 | 2.28〜4.58 GB/s。実測は 0.367 GB/s（経路内）／0.472 GB/s（`dd`・direct・4 GiB）。**一桁足りない** |
| キャッシュ生成（別行） | val 8 枚で 2.88〜3.03 s（0.36〜0.38 s/枚）。学習 1 epoch 分 9,618 枚なら同率で約 1 時間。**償却しても読み出しが再計算より高いため本数によらず回収しない** |
| W2/W1 の 1 step 比 | 1.205（同一バッチ・n=20） |

時間の約 85% は FiLM より後段の transformer の順伝播と逆伝播である。これは界面の重みに
依存するため原理的にキャッシュできない。詳細と根拠は `docs/stage0/C1_frozen_feature_cache_timing.md`、
手順と生データは `audit.md`。

**Tier 1 計算器への差し戻し**: `det_iface_w1` の 4.00 h は本ホストの 4.18 h と整合するため
変更しない。`det_iface_w2` の代理 4.00 h は実測比 1.205 から **4.82 h** へ置き換えられる。
キャッシュは短縮しないため日数は変わらず、縮退なしで **153.1〜208.7 日**。塔が完全に無料と
仮定して全行へ 1.06× を当てても degrade 節は 84.1〜111.9 日 → 79.3〜105.5 日で、
IPCAI 2027 intention（残 39 日）にも long abstract（残 121 日）にも届かない。

## 4. 起票者の誤り

| 型 | 内容 |
|---|---|
| `asserted_without_measuring` | SPEC §2 は「環境は `.venv-relation-detr`」を確定事実として書くが、本ホストではその venv にインタプリタが 1 つも存在せず（`pyvenv.cfg` の `home` が指す pyenv 3.11.4 も不在）、L3 が `make: python: No such file or directory` で起動すらしなかった。指示どおり進めると Task A の途中で止まる |
| `check_does_not_check` | preflight の P1 は `.venv-relation-detr` を要求する一方、P8 は `sys.executable`（＝その venv）で `validate_task.py` を起動する。その venv の正本 lock 72 pkg に `jsonschema` が無いため、**検出系の契約では P8 が構造的に必ず FAIL する**。指示どおり実行すると L3 が exit 0 にならず実行へ進めない |
| `asserted_without_measuring` | 完了判定 a は「両方の run の所要時間が壁時計と GPU 時間で記録されている」を要求するが、基準 run の証跡（`config.yaml` / `metrics.json` / `t1b_result.json` / `logs/`）に時間の列が無く GPU 時間は記録が無い。指示どおりでは基準側が原理的に埋まらず、4 時間の再実行（escalate 対象）を強いる |
| `self_contradiction` | §3 Task B は「塔の出力を**一度だけ**保存して界面だけを学習する」を前提に置くが、§4 禁止事項 2 は「処方を変えない」と定める。学習の前処理 `presets.detr` は毎 epoch 乱択（水平反転・11 段の解像度・crop）であるため、一度きりの保存を使い回すことは処方の変更にあたる。両立には epoch ごとのキャッシュ（6 倍の保管量）が要る |
| `self_contradiction` | §4 禁止事項 4 は「`context/auto/*` と `tasks/inbox.md` を再生成しない」と定めるが、手順書 §6 は `make taskindex` / `make inbox` での生成と、`taskindex-check` / `inbox-check` で差分 0 を確かめることを要求する。**禁止事項に従うとこの 2 つの検査は必ず exit 2 を返し、手順書に従うと禁止事項に触れる。** 禁止事項を優先し、一度回した生成物を元へ戻した |

## 5. 逸脱

1. `environment` — `.venv-relation-detr` を `docs/setup/lecun_detector.md` に従い再構築した
   （`UV_VENV_CLEAR=1 SKIP_CUDA_CHECK=1`。利用者の許可）。nvcc は 12.9 で文書の前提 11.8 は不在。
2. `environment` — P8 を通すため同 venv へ `jsonschema>=4`（依存込み 5 件）を追加導入した。
   **正本 lock `requirements.relation_detr.lock.txt` は変更していない**（利用者の指示）。
3. `judgement` — 完了判定 b の 6 epoch 完走比較を行っていない。上限 1.05〜1.08×・実測 0.65× が
   先に判明し、9 GPU 時間と 2.64 TB を投じる根拠が無くなったため、数値を提示して利用者の
   判断（限定版で結論とする）を得た。
4. `judgement` — 装置の仮占有 2 件を実験直前に停止した（利用者の明示の許可）。停止前に
   `/proc/PID/exe` と `nvidia-smi --query-compute-apps` の両方で同定し、部分一致を使っていない。
5. `spec_defect` — `scripts/profile_t1b_step.py` と `scripts/t1b_backbone_cache.py` を新設した。
   §3 は「コマンドは書かない。実装を読んで決めてよい」とするが `scripts/` への新設は対象外である。
   `scripts/train_t1b.py` は 1 行も変えていないため、既存の経路は構成上壊れない。
6. `judgement` — キャッシュの実体は `third_party/Relation-DETR/data/processed/` 配下へ落ちた。
   `train_t1b` が import 時に `os.chdir(RELDETR)` するため相対経路がそこへ解決される。
   版管理外・同期対象外で禁止領域ではない。証跡（`index.json` 3 件）は契約フォルダへ取り出した。
7. `judgement` — 決定性の検査は val（前処理が決定的）で行った。学習側は増強が乱択で
   「同じ入力で二度」が定義できないため。
8. `spec_defect` — 手順書 §6 に従い `make taskindex` と `make inbox` を一度回したが、
   §4 禁止事項 4 に従って `git checkout` で元へ戻した。併合後に中央で再生成される想定と解した
   （直近の `bbd1792c chore(taskindex): #179 の併合後に投影と集約結果を再生成する` と同じ扱い）。

## 6. 想定外・UNKNOWN

1. 基準 run とキャッシュ経路 run の 6 epoch 完走比較（主指標の一致）— 上記逸脱 3。
2. 基準 run の GPU 時間 — 記録が無い。本ホストでも 6 epoch を回していない。
3. 決定化（ビット一致）の可否 — 1 を回していないため未確認。
4. 開始時の未追跡 2 件は、**実行者の操作の前**（08:53:56 UTC）に `stash@{0}` へ退避されていた。
   実行者は消していない。`git stash list` は 2 件。

## 7. 送出

| 項目 | 値 |
|---|---|
| `make task-validate` | exit 0（`OK` / 0 failed） |
| `make task-preflight`（`.venv-relation-detr`） | **exit 0**。7 PASS / 0 WARN / 5 SKIP / 0 FAIL。SKIP は P3・P4・P5・P11・P12 |
| `make forbidden-check` | exit 0 / `"status": "pass"` / `"violations": []` |
| `make spec-check` | exit 0 / `"status": "pass"` / 規則 8 件・該当 0 |
| `make taskindex-check` | **exit 2（差分あり）。** §4 禁止事項 4 に従い投影を再生成していないため。期待どおりの結果である |
| `make inbox-check` | **exit 2（差分あり）。** 同上。`tasks/inbox.d/<task_id>.md` は書いてある |
| 試験 | 変更前 6 failed / 536 passed / 14 skipped（HEAD の worktree）→ 変更後 6 failed / 550 passed。**失敗の増加 0** |
| 分岐 | `feat/frozen-feature-cache-timing` |
| commit | `8dbee161` |
| PR | **#181**（base `phase0` / head `feat/frozen-feature-cache-timing` / `isDraft: false` / `state: OPEN`） |

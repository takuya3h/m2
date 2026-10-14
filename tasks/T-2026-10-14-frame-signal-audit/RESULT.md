# 結果 — T-2026-10-14-frame-signal-audit

Stage 2 の前提を andrew で読むだけで実測した。装置も推論も使っていない。表と CSV は
`experiments/analysis/frame_signal_audit/REPORT.md`、命令と出力は `audit.md`。未測定は UNKNOWN。

**status: pass。** 四つの集合は二通りの方法で全セル一致し、起票者の写しの値とも全項目一致した。
既存の送り手信号はすべて「同時刻 t」で、「一つ前の時刻まで」の規則は実装にも文書にも無い。
Stage 1 の工程塔は動画の区間を連結した 1 本の列を見ており、評価の Jaccard は全フレーム合算である。

## 1. 解決された参照

| 記載 | 解決先 |
|---|---|
| `contract.inject_verbatim` | `context/conventions.md` の prohibitions / issuer_cautions / folds / split / crossfit を原文のまま適用 |
| `contract.conventions_rev` | 実測 `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6`（起票時と一致） |
| `meta.created_from` | runindex `63ae65da8c7d32df591f5e2ee4358286b72c726b`、1961 / 750 / 1506（一致。amendments 不要）。起点 `origin/phase0` は `57717f6c`（起票時の `8b331ac6` から本日の #226 で進んだ。注釈の木は同一） |
| `inputs.denominator` / `sigma_policy` / `frozen_source` | 契約に無し。凍結源は Task F で照合し `conventions#frozen_source` の正本と一致 |

## 2. 関門

| 関門 | 判定 | 実測 |
|---|---|---|
| G1（A の後） | **pass** | 分岐 `feat/frame-signal-audit`、起点 = `origin/phase0`、注釈 46 ファイルの木の要約値が起点と一致、装置 0 件、`.sync-pause` は task-start が作成 |
| G2（B の後） | **pass** | 方法 A（Python）と方法 B（シェル）が 43 区間 × 20 列 = 860 セルで一致。§3.2 の 14 項目と動画ごと 15 行 × 4 値がすべて一致 |

## 3. 完了判定

| # | 判定 | 結果 | 実測 | 空振りでないことの確認 |
|---|---|---|---|---|
| a | 四つの集合 | 達成 | `sets_by_clip.csv` 43 区間、`sets_by_video.csv` 20 動画、片方だけの一覧 `phase_only_frames.csv`（12,257 行） | 1 フレーム抜いた写しで tool−phase 0→1、phase−tool 12,257→12,258。同じ集合どうし 0 |
| b | 起票者の値 | 達成 | 全項目一致 | 数え方は起票者（版管理の写し）/ 方法 A（注釈・画像・manifest）/ 方法 B（cut・grep・find・comm）。方法 B の awk の誤りを照合が捕まえ、直して一致 |
| c | 時刻の根拠と飛び | 達成 | 番号は区間ごとの抽出の通し番号（配布物の生フレームが 1 から連続）。0.5 fps は repo の文書が原著を引く。番号→秒は UNKNOWN（仮定として換算）。manifest15 の飛び 1,013 か所、1 / 2〜4 / 5〜14 / 15〜59 / 60+ = 526 / 286 / 118 / 60 / 23、最大 253 | 番号を 1 つ抜いた写しで飛び 52→53 |
| d | 塔が使った集合 | 達成 | 三周目 = manifest15（15,437）、P\*-20 = manifest20（25,898）。1,796 と 03_3 は manifest 生成で落ち、学習・評価・抽出のどこにも入らない | キャッシュの `video_counts` と FT の config（9657 / 1515、20118 / 1515）が manifest の動画ごとの数と一致 |
| e | 履歴と評価の単位 | 達成 | 区間を番号順に連結した動画 1 本の列。履歴は区間の境界で初期化されない。Jaccard と accuracy は全フレーム合算、segment 系だけ動画ごとの平均 | 実装の行（`stage1_ptower.py:205-215`、`metrics/phase.py:211-241`）と、別契約 `T-2026-10-04-ptower-attribution-val` が同じ連結で val J・acc を全桁再現した記録。本契約の run 自体は単位を記録していない |
| f | 送り手の時刻 | 達成 | 6 経路すべて同時刻 t（REPORT §3.1） | ずらした写し 6 / 6 が「ずらし(−1)」、ずらさない写し 6 / 6 が「同時刻」 |
| g | 参照入力段 | 達成 | P→D: 空 / 予測 / 正解 / 正解⊕予測（連結、正解→予測、18-d）。D→P: 空は S4 base、予測 / 正解 / 連結 30-d。領域トークンに正解段と組み合わせ段は無い。正解の時刻は同じフレーム | §3.3 の行 2〜4 は実装と一致、行 5 は食い違い（§5） |
| h | 信号の形 | 達成 | 検出塔: 15 クラス、query 900 × 256-d、logits (900,15)、枠 (900,4)、後処理 300 件、backbone C3/C4/C5 = 512/1024/2048ch、neck 4 × 256。工程塔: 事後 9-d、TeCNO 64ch、backbone 2048-d。空間の大きさは計算値 | 各行に行番号。推論 0 件 |
| i | メタデータ | 達成 | 術式・術者・手術室・撮影日・機器は動画ごとに UNKNOWN（全体で 10 種類・8 人・15 時間は HTS 論文の抜き書き）。長さは注釈からの表 | 探した場所 9 か所以上（REPORT §4） |
| j | andrew の材料 | 達成 | 画像 25,898 枚全数復号可、重み・凍結源・検出塔 10 本・本体・venv・道具 7 本すべて在り、空き 1,697,382,440,960 B | 「無い」項目は 0。本体は `find -L` の網羅探索でも唯一 |
| k | 無変更と装置 | 達成 | 装置 0 / 0、`data/` 書き込み 0、要約値 4 組が前後で一致、`forbidden-check` pass | 開始時に要約値を先に取った |
| l | 試験 | 達成 | 前後とも 793 passed / 6 failed / 1 error（同じ集合） | 開始前を先に測った |
| m | PR | 達成 | 下の §8 | `gh pr view --json` |

## 4. 実測（次の契約で使う値）

- **集合**: 術具 = manifest15 = ホストの画像（01〜15）= 15,437 で完全一致。工程 CSV 17,233 のうち **1,796 は画像が `raw/ego` に無く**、
  **全 1,796 枚が配布物 `data/raw/OpenSurgery_Dataset/01_frames/initial_videos/` に在り復号できる**（1920×1080）。区間 03_3 の 168 枚もそこに在る
- **番号と時刻**: 番号は区間ごとの抽出の通し番号。**区間が変わると番号は振り直される**（7 動画の境界すべてで次の区間が小さい番号から始まる）。
  区間の間の時間は不明。秒への換算は 0.5 fps の仮定（出所: 原著を引いた `docs/evidence/…:30`）
- **飛び**: manifest15 で隣接しない対 6.6%、中央値 1、最大 253（0.5 fps なら 506 秒）。P\*-20 は 1,316 か所、最大 329
- **塔の列**: Stage 1 は動画ごとに区間を連結（履歴は境界をまたぐ。受容野 1021 フレーム）。Stage 0 の経路は区間ごとに forward（履歴は区間の先頭で初期化）
- **評価**: Jaccard・accuracy は合算、edit・segmental F1 は動画ごと平均。動画単位に直した値は UNKNOWN（予測が保存されていない）
- **送り手の時刻**: 工程文脈は「t 以前を含み t 自身も含む」。術具在否・領域トークン・正解系は t のみ。欠けは P→D が 0 埋め、D→P が KeyError
- **参照入力段**: 連結はいずれも正解→予測の順。P→D の 18-d は `T1B_MODEL_CFG` で指す `num_phases` 18 の設定が要るが、版管理下に無い
- **形**: 検出塔の後処理出力は上位 300 の scores / labels / boxes（閾値・NMS なし）。query 埋め込み 256-d。工程塔の TeCNO は 64ch、事後 9-d
- **メタデータ**: 動画ごとの術式・術者・手術室・撮影日・機器は本ホストのどこにも無い。経過時間の対照は注釈の番号から作るしかなく、区間の間が抜ける
- **andrew**: 後続 2 契約の材料は揃っている（REPORT §5）

## 5. 起票者の誤り

`result.yaml` の `issuer_defects` に 2 件。(1) §3.3 行 5「評価器にクリップの識別子を渡しているように読める」は変数名の読みで、実際は動画の識別子。
(2) §1 の 2「設計文書に『一つ前の時刻まで』の規則があった」は出所が示されず、repo 内に該当の文言が無い。
いずれも停止条件には触れず、本契約の測定で正した。

## 6. 逸脱

`result.yaml` の `deviations` に 7 件。**「逸脱なし」ではない。** 主なもの: 試験は収集エラーを飛ばして全件を走らせた（前後とも同じ扱い）、
方法 B の awk を照合後に直した、時刻判定の対照の期待符号を直した（データの判定値は不変）、C.5 は UNKNOWN、
起点が起票時より進んでいたが注釈は同一なので続行した。

## 7. 想定外・UNKNOWN

- 番号 → 秒の対応は配布物に無い（0.5 fps は文書の記載）。C.5（動画単位の値）は予測が無く UNKNOWN。動画ごとのメタデータは UNKNOWN
- 工程文脈の時刻判定は 0 と −1 の一致率の差が 0.0015 と小さい。判定は最大値で取ったが余裕は小さい

## 8. 送出

- commit `432e1f10`（25 ファイル）→ push → **PR #227**（`https://github.com/takuya3h/m2/pull/227`、base `phase0`、Draft でない、OPEN。`gh pr view --json` で実測）
- `make task-report` 成功。台帳の応答: verdict `pass`、issuer_defects 2、report_sha256 `2d02e042a4c9d16f39d1d208c5eb86437fc3e2de38e5d024664f3aec78abd2cb`、8,851 bytes、replaced_blocks 0
- commit は `.git/index.lock`（状態行スクリプトの `git status` が一瞬置く）との競合で 2 回失敗し、再試行で通った。経緯は `audit.md` §8
- 本節と `result.yaml` の `pr` / `commits` を書いた 2 つ目の commit は、台帳へ送った本文には含まれない

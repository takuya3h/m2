# RESULT — T-2026-08-30-hts-candidate-acceptance

kind: analysis / host: andrew / branch: `feat/hts-candidate-acceptance` / GPU 不使用

## 判定

**status: pass。** 関門 G1 は通過。SPEC §5 の完了判定 a–g をすべて満たした。

## 1. 解決された参照

- `contract.inject_verbatim` = `conventions#prohibitions` `conventions#issuer_cautions`
  → `context/conventions.md` の当該アンカーの原文をそのまま参照した（要約していない）。
  なお **`spec.contract.prohibitions` の 5 語のうち `no_runindex_regen` と `no_history_rewrite`
  は conventions#prohibitions の表に存在しない**（表は `no_split_redefine` `no_raw_write`
  `no_frozen_change` `no_estimated_values` `no_runindex_hand_edit`）。SPEC §4 の禁止事項を正として運用した。
- `conventions_rev: a8c07e81` → 実測 `git log -1 --format=%h -- context/conventions.md` = `a8c07e81`。一致。置換不要。
- `created_from.counts` = index 1250 / experiments 277 / verdicts 1486 → 実測と全一致。
  `runindex_commit: 09fdefb3` も実在。置換不要。
- `inputs.denominator.ref` `inputs.sigma_policy` `inputs.frozen_source.ref` は本契約に無い。

## 2. 完了判定（SPEC §5）

| # | 判定 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 走査の網羅性 | 方法1（find・74 エントリ）に対し、方法2（文書逆引き＋ひな型展開・実在 27 経路）が取りこぼしを 0 件で確認 | 方法1 から 1 件除くと差として検出（3 例中 2 例）。残る 1 例は退避後の経路を指す文書が無いための説明のつく差。audit.md §4 |
| b | 候補の棚卸し | `candidates.csv` 107 行（配下 63・参照先 44）、候補 71 件 | 点で始まる `.gitkeep` と退避先 `_deprecated/egosurgery_hand4/*` が一覧に含まれる。audit.md §3 |
| c | 検査器の再現 | 主判定 C1/C2/C3/C4 は前回と一致。陽性（C1–C3 が落ちる）を再現 | C3 の数値が 46,320→0、C5 が PASS→FAIL に変化。入力（`egosurgery_hand4` の退避）が変わっている。audit.md §5 |
| d | マスク型の判定 | RLE 例 → `is_real=True` / 4 頂点 polygon 例 → `is_real=False`。判定が分かれる | 双方とも実データから抜いた。audit.md §6 |
| e | 手の件数 | 既存記録 46,320 を再現。候補合算の集合件数は最大 57,172 | 単純加算と集合件数が異なる（差 1 / 14,833 / 61,154）。重複除去は働いている。audit.md §7 |
| f | 三値の結論 | `REPORT.md` に結論 1 つと根拠の行列 | `criteria_matrix.csv` 45 行 × 6 列、空欄 0。audit.md §10 |
| g | 変更範囲 | `git status --porcelain data/` が空 | 同じ絞り込みを destination に当てると 2 行出る。audit.md §10 |

## 3. 三値の結論

**一部欠落。**

主判定のうち C1（真マスク）・C2（値5=Two Hands Tool）・C4（リーク不在）は満たす候補が存在する。
**C3 を満たす候補は 0 件で、実装どおりの C3 は現在の原資料からは満たせない。**

| 欠け | 実測 | 原資料の所在 |
|---|---|---|
| C3 の動画被覆 | 検査器は raw 02_hand の**ディレクトリ名 26 件**の被覆を要求。最良の候補 `hts_hand_seg` でも 25 件で、欠落は `03_3` のみ | **無い。** `data/annotations` と `data/raw` の COCO JSON 全 291 個で `03_3_*` フレームを持つ注釈は 0 件。フレームは `01_frames/initial_videos/03_3/` に 261 枚、工程注釈 `egosurgery_phase/03_3.csv` は実在するが、手・把持・マスクの注釈は存在しない |
| C3 の件数 | `hts_hand_seg`(train+val+test+extra) の単純加算は 57,173 で目標一致。集合件数は 57,172 | 差 1 は正本 `02_hand/json_per_video/05_1/05_1.json` の完全重複（`05_1_0575.jpg` / bbox `(0.0,6.0,940.0,1066.0)` / cat 4 / ann id 1519・1520）。**目標値 57,173 自体がこの重複を含む** |

C3 の未達は**組立作業では埋まらない**（`03_3` の手注釈が存在しないため）。
選択肢は REPORT.md「組み立てるとしたら」に 3 つ挙げた。**本契約は判定に変換しない。決めるのはユーザーである。**

## 4. 実測（次の契約で使う値）

| 候補 | 経路 | 画像 | 注釈 | 手注釈 | マスク | 動画 |
|---|---|---:|---:|---:|---|---:|
| `hts_hand_seg` | `data/annotations/egosurgery_hts/hand_seg/{train,val,test,extra}.json` | 9627/1515/4255/4035 | 57,173 | 57,173 | RLE 100% | 25 |
| `hts_hand_tool_seg` | `.../hand_tool_seg/{train,val,test,extra}.json` | 9356/1514/4107/3420 | 62,087 | 33,465 | RLE 100% | 24 |
| `hts_tool_seg` | `.../tool_seg/{train,val,test,extra}.json` | 9528/1512/3927/3532 | 54,137 | 0 | RLE 100% | 24 |
| `hand4_deprecated` | `data/annotations/_deprecated/egosurgery_hand4/instances_{split}.json` | 9657/1515/4265 | 46,320 | 46,320 | seg 無し | 22 |
| `tool_hand_19cls` | `data/annotations/egosurgery_tool_hand/instances_{split}.json` | 9657/1515/4265 | 95,972 | 46,320 | 4 頂点ダミー | 22 |
| `raw04_5cls`（参照先） | `data/raw/.../04_handtool/coco_splits_5cls/{split}.json` | 5668/2094/1344 | 34,175 | 18,123 | RLE 100% | 13 |

`hts_hand_tool_seg` の cat5（Two Hands Tool）注釈は **2,021 件**。

組立に要する操作の種類（**本契約では実施していない**）: 手 seg と把持 seg の結合、
公式 split の image 一覧への揃え（注釈 0 件フレーム 40 枚の扱いを決める）、C3 の閾値定義の改訂。

## 5. 起票者の誤り

- `asserted_without_measuring`: SPEC §2 は「C1 から C5 の定義を正」とするが、実装の主判定は
  `main_keys = C1/C2/C3/C4` の 4 つで C5 は含まれない。C1–C5 を主判定として扱うと C5 の
  PASS/FAIL が結論を左右し、実装と異なる判定になる。実装を優先し、食い違いを本報告に残した。
- `self_contradiction`: `spec.contract.prohibitions` の `no_runindex_regen` `no_history_rewrite`
  は `conventions#prohibitions` の表に無い語である。`inject_verbatim` で当該アンカーの原文を
  注入する契約でありながら、その原文に無い id を並べている。照合すると解決先が見つからない。

## 6. 逸脱・想定外・UNKNOWN・判断待ち

**逸脱 6 件。**

1. `judgement` — 実行開始時、作業ツリーに未追跡ファイル（`pd_refin_*_seed42` の run ログ 4 組と
   セッションダイジェスト 1 件）が残り `make task-start` が止まった。破棄は研究記録に関わるため
   ユーザーに選択肢を示し、**「stash で一時退避」を選んでもらった**。`git stash push -u` で退避済み
   （`stash@{0}`）。**本契約の完了後に `git stash pop` で戻す必要がある。**
2. `judgement` — 契約の実行前に `git checkout phase0` を行った（開始時は `feat/denoise-falsification`）。
   ユーザーの指示した起動命令に含まれていた。
3. `judgement` — **契約 §4-2 に触れた。** 対照のため `python scripts/audit_l0_hts_acceptance.py` を
   そのまま実行したところ、検査器が `experiments/audit/l0_hts_acceptance/acceptance_report.json`
   （destination 外）を上書きした。実行前に控えを取っていたため直ちに復元し、
   `git status --porcelain experiments/audit/` が空であることを確認済み。以降は `main()` を
   呼ばず判定関数のみを import して評価した。**検査器を素直に実行すると必ずこの書き込みが起きる。**
4. `spec_defect` — 手順書（`.claude/skills/task/SKILL.md` 手順 6）は `make taskindex` /
   `make taskindex-check` / `make inbox` の実行を求めるが、**契約 §4-3 はこれらの再生成を禁止**
   している（並行契約あり）。契約を優先していずれも実行しなかった。したがって本報告は
   `context/auto/` の投影にまだ現れない。統合後に一台で再生成すること。
5. `spec_defect` — `make forbidden-check` が `status=fail` を返すが、**違反 12 件はすべて本契約の
   `outputs.destination` の内側**である。道具は生成物（`context/auto/` と `tasks/inbox.md`）しか
   除外できず、契約ごとの destination を表現できない。destination の外側にある違反が 0 件で
   あることは個別に確かめた（変更 17 件 = destination 12・契約ディレクトリ 4・`tasks/inbox.d/` 1）。
6. `judgement` — G1 の照合が初回は空振りだった（ひな型未展開のため 3 例すべて非検出）。
   ひな型展開を足して照合を強めてから G1 を判定した。弱いままなら G1 は空振りで通っていた。

**想定外 1 件**（SPEC §6 の「検査器の基準と文書の記述が食い違う」に該当）:
C5 の位置づけ（§5 起票者の誤り 1 件目）。実装の定義で続行し、食い違いを報告に残した。

**UNKNOWN**: 検査器 C1 の polygon>4 頂点の枝は**実データで踏めない**（polygon 形式は全 371,335 件が
4 頂点）。この枝の実データ上の挙動は UNKNOWN であり、合成入力でのみ確認した。

**判断待ち**: 三値の結論の後段（C3 の定義を直すか、手信号の腕を外すか、`03_3` を新規注釈するか）。

## 7. 送出

- PR: 本文末尾に番号を追記
- `make task-report` の終了コード: 本文末尾に追記

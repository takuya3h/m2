# audit — T-2026-08-30-hts-candidate-acceptance

RESULT.md はここを行番号で指す。命令と出力を時系列で置く。

## 1. 契約の取り込みと検証

```
$ git fetch origin && git checkout phase0 && git pull
Switched to branch 'phase0'
Your branch is up to date with 'origin/phase0'.
Already up to date.

$ git stash push -u -m "task-start用の一時退避 T-2026-08-30-hts-candidate-acceptance"
Saved working directory and index state On phase0: ...
（未追跡の pd_refin_*_seed42 の logs/*.json 4 組 と digest md 1 件。作業ツリーを clean にするため）

$ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-08-30-hts-candidate-acceptance
[task-start] 分岐を作成: feat/hts-candidate-acceptance（起点 origin/phase0）
[task-start] .sync-pause を作成
OK   T-2026-08-30-hts-candidate-acceptance
1 task(s), 0 failed

$ make task-validate TASK=T-2026-08-30-hts-candidate-acceptance ; echo $?
OK   T-2026-08-30-hts-candidate-acceptance
1 task(s), 0 failed
0

$ make task-preflight TASK=T-2026-08-30-hts-candidate-acceptance
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=... sys.prefix=...
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=analysis のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=analysis のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS experiments/analysis/hts_candidate_acceptance/ は未作成だが作成可能
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              PASS 規則 8 件を検査し該当なし
RESULT: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL   (EXIT=0)
```

同期の抑止:

```
$ ls -la .sync-pause          -> -rw-rw-r-- 0 Aug 30 02:30 .sync-pause
$ grep -c sync-pause ~/bin/m2-sync.sh   -> 2   （稼働中の常駐版は抑止に対応済み）
```

## 2. 参照の解決（Step 1-1）

```
$ git --no-pager log -1 --format=%h -- context/conventions.md
a8c07e81                       ← 契約の conventions_rev と一致

$ for f in index experiments verdicts; do echo "$f: $(($(wc -l < runindex/$f.csv) - 1))"; done
index: 1250 / experiments: 277 / verdicts: 1486     ← 契約の created_from.counts と一致

$ git --no-pager log -1 --format='%h %s' 09fdefb3
09fdefb3 exp(stage0-b): measure the D->P reference-input ladder; ...   ← 実在
```

置換は不要だった。

## 3. Phase A — 走査（Step 1-2）

```
$ find data/annotations -mindepth 1 \( -type f -o -type l -o -type d \) -printf '%y\t%s\t%p\t%l\n'
総エントリ 74 ： d=11 / f=60 / l=3

symlink 3 件（すべて配下内を指す）:
  data/annotations/egosurgery_tool/hand/test.json  -> ../../egosurgery_tool_hand/test.json
  data/annotations/egosurgery_tool/hand/train.json -> ../../egosurgery_tool_hand/train.json
  data/annotations/egosurgery_tool/hand/val.json   -> ../../egosurgery_tool_hand/val.json

点で始まるもの 1 件:
  data/annotations/egosurgery_hts/.gitkeep

退避先 1 件:
  data/annotations/_deprecated/egosurgery_hand4/instances_{train,val,test}.json
```

参照先（配下外）— 検査器と README が指すもの。すべて到達可:

```
data/raw/OpenSurgery_Dataset                                    到達可
data/raw/OpenSurgery_Dataset/02_hand/json_per_video             到達可（26 dir）
data/raw/OpenSurgery_Dataset/04_handtool/coco_splits_5cls       到達可（3 json）
data/raw/OpenSurgery_Dataset/00_master_annotations/annotations_raw 到達可（15 json）
```

## 4. Phase A — 網羅性の異質な二方法（Step 1-3, G1）

- 方法1: `find` による配下の全走査（74 エントリ）
- 方法2: `grep -rhoE 'data/annotations/[...]'` で文書・スクリプト・設定から経路を逆引きし、
  `{train,val,test}` `{split}` `{sp}` `{s}` のひな型を展開して実体化（80 経路、うち実在 27）

```
方法2 で実在が確認された経路: 27
そのうち方法1 の走査に現れないもの: 0 []
```

空振りでないことの確認（方法1 の一覧から 1 件を除いて差が出るか）:

```
除外=data/annotations/egosurgery_hts/hand_tool_seg/train.json
   具体参照に含まれる=True  検出された差=['.../hand_tool_seg/train.json']      ← 検出
除外=data/annotations/egosurgery_tool_hand/instances_val.json
   具体参照に含まれる=True  検出された差=['.../instances_val.json']            ← 検出
除外=data/annotations/_deprecated/egosurgery_hand4/instances_train.json
   具体参照に含まれる=False 検出された差=[]                                     ← 非検出
```

第 3 例が非検出なのは、`egosurgery_hand4` が `_deprecated/` へ退避された後も文書が
**旧経路のまま**を指しており、退避後の経路を具体参照する文書が存在しないため。説明のつく差である。

**初回の照合はひな型を展開しておらず、3 例すべてが非検出（空振り）だった。** ひな型展開を
足して照合を強めた結果が上記である。この修正が無ければ G1 は空振りのまま通っていた。

**G1 通過。**

## 5. Phase B — 対照: 検査器の再実行（Step 2-2, 判定 c）

⚠ 最初に `python scripts/audit_l0_hts_acceptance.py` をそのまま実行したところ、
検査器が `experiments/audit/l0_hts_acceptance/acceptance_report.json` を上書きした。
これは契約 §4-2（destination 以外の experiments への書き込み禁止）に触れる。
実行前に控えを取ってあったため直ちに復元した。

```
上書き後 sha256: e4c7f2e90136eea4daa18a7e4af51b87fc879c88fa922ea1535ddb6374146e7b
復元後   sha256: d9ac7ced89e5c57487d6dc8ed17b39cfd974fa79f68ff96522148f422e747126
$ git status --porcelain experiments/audit/     -> （空。完全復元）
```

以降は `main()` を呼ばず判定関数だけを import して評価した（書き込みを起こさない）。

```
基準                         前回     今回     一致
C1_polygon_points          False    False    YES
C2_value5_two_hands_tool   False    False    YES
C3_hand_total_57173        False    False    YES
C4_leakage_fingerprint     True     True     YES
C5_official_split          True     False    *** NO ***

C3 前回 hand_instances_current = 46320
C3 今回 hand_instances_current = 0
C5 前回 image_counts = {'train': 9657, 'val': 1515, 'test': 4265}
C5 今回 image_counts = {}
```

**主判定 C1/C2/C3/C4 は前回と一致し、陽性（C1–C3 が落ちる）も再現した。**
ただし C3 の数値と C5 の判定が変わった。原因は `egosurgery_hand4` の `_deprecated/`
退避を検査器が検知せず、`_splits()` が不在ファイルを黙って飛ばすこと。

## 6. Phase B — 対照: マスク型の判定（判定 d）

```
真マスク側: hand_seg/val.json ann#0            seg型={'rle': 1}                -> is_real=True
ダミー側  : egosurgery_tool_hand/val.json ann#0 seg型={'polygon': 1} 頂点={4:1} -> is_real=False
判定が分かれる: True
```

polygon>4 頂点の枝は実データに例が無いため合成入力で枝だけ確認した:

```
合成 polygon 8頂点 x1: is_real=True
合成 polygon 4頂点 x1: is_real=False
```

全候補を通じた polygon 頂点数分布は `{4: 371335}`。**実データに真の多角形は 1 件も無い。**

## 7. Phase B — 手の件数（Step 2-3, 判定 e）

```
集合                    単純加算   集合(frame,bbox)  集合(frame,bbox,cat)
hand4_deprecated          46320          46320            46320
hts_hand_seg_splits       46320          46319            46319
hts_hand_seg_extra        10853          10853            10853
tool_hand_4cls            46320          46320            46320
tool_hand_19cls           46320          46320            46320
raw02_hand_source         57173          57172            57172

既存記録の再現: hand4_deprecated 単純加算 = 46320 / 既存記録 46320 → 再現 True
正本の合計    : raw02_hand_source 単純加算 = 57173 / 完全版 57173 → 一致 True

候補の合算（重複除去つき）:
  hand_seg(split)+hand_seg(extra)          単純加算  57173  集合  57172  差      1
  hand_seg(全)+hand4(退避)                 単純加算 103493  集合 103492  差      1
  hand4(退避)+tool_hand_4cls               単純加算  92640  集合  77807  差  14833
  hand_seg(全)+hand4+tool_hand_4cls+19cls  単純加算 196133  集合 134979  差  61154
```

**単純加算と集合件数が異なる（差 1 / 14,833 / 61,154）。重複除去は働いている。**

差 1 の実体:

```
重複した (frame, bbox) の組: 1
  frame=05_1_0575.jpg bbox=(0.0, 6.0, 940.0, 1066.0)  出現 2 回
      02_hand/json_per_video/05_1/05_1.json  ann id=1519  cat 4 "Other Person's Right Hand"
      02_hand/json_per_video/05_1/05_1.json  ann id=1520  cat 4 "Other Person's Right Hand"
```

目標値 57,173 はこの完全重複を含む単純加算である。

## 8. Phase B — 03_3 の所在

```
$ ls -la data/raw/OpenSurgery_Dataset/02_hand/json_per_video/03_3/
-rw-rw-r-- 255407 Jan  7 2025 03_3.json
images: 1472  annotations: 0
先頭 5 画像: ['03_1_0001.jpg', ... ]   末尾 5 画像: ['03_2_1687.jpg', ...]
```

`03_3` という名のディレクトリはあるが、注釈は 0 件で、画像リストは `03_1`/`03_2` のもの。

全注釈源の走査:

```
走査する注釈 JSON: 291（data/annotations + data/raw、realpath で重複排除）
=== 03_3 のフレームを含む注釈ファイル ===  該当なし
```

一方でフレームと工程注釈は実在する:

```
data/raw/OpenSurgery_Dataset/01_frames/initial_videos/03_3/   261 枚
data/annotations/egosurgery_phase/03_3.csv                    実在
公式 split (egosurgery_tool) に現れる動画: 22 件。03_3 は含まれない
phase にあり公式 split に無い: ['03_3']
```

検査器の C3 は `glob(02_hand/json_per_video/*)` の**ディレクトリ名 26 件**と、
`file_name` から導く**動画 id 25 件**を比べる。`03_3` は右辺に現れ得ないため
`missing == []` は構成上成立しない。

## 9. Phase B — 基準×候補（Step 2-1）と組み合わせ（Step 2-4）

```
候補                        C1    C2    C3    C4    C5   手件数
hand4_deprecated          FAIL  FAIL  FAIL  PASS  PASS   46320
hts_hand_seg              PASS  FAIL  FAIL  PASS  FAIL   57173
hts_hand_tool_seg         PASS  PASS  FAIL  PASS  FAIL   33465
hts_tool_seg              PASS  FAIL  FAIL  PASS  FAIL       0
tool_bbox                 FAIL  FAIL  FAIL  PASS  PASS       0
tool_hand_19cls           FAIL  FAIL  FAIL  PASS  PASS   46320
tool_hand_4cls            FAIL  FAIL  FAIL  PASS  FAIL   46320
tool_hand_4cls_link       FAIL  FAIL  FAIL  PASS  FAIL   46320
raw04_5cls                PASS  PASS  FAIL  PASS  FAIL   18123

C1: 満たす候補 4 件 ['hts_hand_seg','hts_hand_tool_seg','hts_tool_seg','raw04_5cls']
C2: 満たす候補 2 件 ['hts_hand_tool_seg','raw04_5cls']
C3: 満たす候補 0 件 []
C4: 満たす候補 9 件（全候補）
C5: 満たす候補 3 件 ['hand4_deprecated','tool_bbox','tool_hand_19cls']
主判定 C1-C4 すべてに満たす候補があるか: False
```

C3 の欠落動画（候補別）:

```
hts_hand_seg      : 在 25 / dir 26 / 欠落 ['03_3']
hand4_deprecated  : 在 22 / dir 26 / 欠落 ['03_1','03_3','12_2','15_2']
hts_hand_tool_seg : 在 24 / dir 26 / 欠落 ['03_3','12_2']
raw04_5cls        : 在 13 / dir 26 / 欠落 13 件
```

## 10. 判定 f・g

```
$ criteria_matrix.csv  45 行 x 6 列   空欄: 0
$ candidates.csv      107 行 x 17 列
$ git status --porcelain data/          -> （空。data 配下の変更零）
$ git status --porcelain
?? experiments/analysis/hts_candidate_acceptance/
?? tasks/T-2026-08-30-hts-candidate-acceptance/
```

同じ絞り込みを destination に当てると変更が出る（上記 2 行目）。判定 g の空振りではない。

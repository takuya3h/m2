# RESULT — T-2026-11-02-bengio-andrew-env-survey

実行ホスト bengio、比べる相手 andrew（読むだけ）。2026-11-02 11:16〜11:4x UTC（20:16〜20:4x JST）。表は `experiments/analysis/bengio_andrew_env_survey/REPORT.md`、手続きは `audit.md`（行番号で指す）。

## 1. 判定

**pass。** G1 通過（audit 92〜95 行）。G2 通過: andrew main・bengio main・重ねの BODY の要約値が §3.2 と三つとも一致（audit 113〜115 行）。
解決した参照: `conventions_rev` 2d946b07 は現在の `context/conventions.md` の最後の commit と同じ、runindex 68befc3b・2363/1130/1736 も同じ（差し替えなし）。
注入の 4 アンカーの原文は `resolved_refs.md`。分母は本契約に無い（`inputs.denominator` を参照しなかった）。

## 2. 完了判定（§6）

| # | 期待 | 実測 | 空振りでないことの確認 |
|---|---|---|---|
| a | 開始状態 | bengio: 分岐 `feat/bengio-andrew-env-survey`、起点 = HEAD = origin/phase0 231c280e、追跡下の変更 0、空き 1,415,044,030,464 B、本契約以外の compute 0。andrew: `feat/stage2-w23-andrew`、HEAD a78e2f3c、変更 0、未追跡 41、compute 0（audit 20〜55 行） | zsh 8、存在しない経路 0 |
| b | Relation-DETR | 三分類: andrew だけ 15、bengio だけ 0、違う 8、同じ 132。違う 8 件のうち 6 件は bengio の中身が tar に在り、2 件（`main.py`・`transforms/presets.py`）は無い | 和 155 = 和集合 155。1 ファイルの要約値を変えた写しで「違う」が 8 → 9 |
| c | 仮想環境 | パッケージの差 0（二つの venv、二通りの取り方）。python は両ホスト uv の 3.11.16（同じ sha256）。torch 2.1.2+cu118・CUDA 11.8・cuDNN 8700・NCCL 2.18.6 で同じ。拡張のビルド物は要約値が違う（bengio は重ねの BODY の `.cu` から） | 一行に `.post999` を足した写しで差に 1 件出た |
| d | データと checkpoint | 画像 B1 15,437 枚と固定記録の 32,670 経路は両ホストと記録で全件一致。工程 CSV 43、manifest 8、術具注釈 3、折り 16、分割と折り表 4、重み 3、塔 4 は全件一致（git の blob も一致）。Stage 2 の材料 63 経路のうち一致 37、andrew だけ 17、bengio だけ 9 | 記録の一画像の要約値を一文字変えると不一致 1。存在しない経路は `exists false` |
| e | 残り物 | repo 393、`~/slocal2` 直下 14、家の直下 9、`/tmp` 直下 514、worktree 3、除外の行 5、上流の無い分岐 1。全件 JSON、REPORT に欄つき。§3.3 の行方は REPORT の Task E | `README.md`（andrew にもある）は出ない。`~/m2-git-info-exclude.bak-20261019` は出る |
| f | 装置と系 | 両ホストの GPU（型・UUID・VBIOS・driver・電力・クロック・永続・ECC・PCIe）、接続、NUMA、IOMMU、CPU、メモリ、cgroup、記憶領域、kernel、容器、nvcc・gcc を並べた | 存在しない GPU 番号 7 は両ホストで `No devices were found`・終了コード 6 |
| g | 試験 | bengio 11 failed・1 error（名前 12）、andrew の記録 6 failed。差 6 件のうち 1 件（`test_stage1_dtower_convergence.py` の収集）は Relation-DETR の差で説明が付き、5 件は付かない | andrew の集合に名前を 1 つ足すと差が 6 → 5 |
| h | 無変更 | andrew に書き込みの向き先を持つ命令 0 件（34 行の全件、audit 167〜178 行）。bengio の Relation-DETR 3 か所・stat の木 12 個・認証情報 16 件が前後一致。andrew の要約値も前後一致。**ただし本契約の出力の 8 件が同期で andrew に渡り、利用者の決定で改名して同期が消した。andrew には空のディレクトリ 3 つが残る（5.）** | 本契約の出力の置き場は同じ取り方で前後が違う値 |
| i | GPU 不使用 | torch を読む命令は 4 回とも `CUDA_VISIBLE_DEVICES=` で `device_count 0`・`cuda_initialized false`。compute の計数は開始時 0 | 陽性 zsh 8、陰性 0 |
| j | PR | 本ファイルの 6. | — |

## 3. 実測（後続の契約で使う値）

**揃える必要のある項目（基準 andrew）**

- Relation-DETR（bengio main）: andrew だけ 15 件 58,053 B、中身が違う 8 件（andrew の版 50,902 B）。重ねの BODY `~/slocal2/s2fix-bengio-body/third_party/Relation-DETR` は andrew main と全 155 件一致し、揃える材料に使える
- MS-Deform-Attn のビルド物: 要約値が違う。bengio の `build.ninja` は重ねの BODY の `.cu` を指す（27 行目）
- 仮想環境: パッケージの差なし。`pyvenv.cfg` の `home` は andrew の `.venv` だけ存在しない pyenv 3.11.4 を指す（bin/python は uv の 3.11.16）
- データ・塔: 差なし。写す量 0 B
- Stage 2 の材料: bengio に無いもの 9 件 13,497,919,828 B（案 B の見取り 6 件と地図 3 件）。案 A の信号 8 件は bengio に別経路の写しが在る（中身同じ）

**揃えると失われる bengio の中身**: `main.py`（CRLF の上流の原形）と `transforms/presets.py`（上流の原形）。mtime は上流の展開の一括の時刻で、snapshot の tar に無い。

**残り物の内訳（最上位ごとの件数とバイト数）**: REPORT の表 E-1。repo は `.venv` 188 件 4,047,547 B、`node_modules` 72 件 151,158,556 B、`data` 61 件（空のディレクトリ）、
`src` 18、`.remember` 12、`wandb` 9、experiments 7 ほか。`~/slocal2` 直下は `m2-four`（858,489,549 B）、`m2-s2fix-bengio`（587,164,888 B）、`s2fix-bengio-body`（3,097,942 B）と、5 月の別の作業の置き場 11 件（`egosurgery_multitask` 17,199,677,441 B ほか）。
定義の外の補足: `stage2pilot_store` の二段目で bengio だけのものは `T-2026-11-01-grasp-pilot-d`（18,137,294,352 B）と `T-2026-11-01-stage2-w23-bengio`（3,248,788,205 B）ほか 4 件。

**装置と系の差**

| 項目 | andrew | bengio |
|---|---|---|
| 電力の上限（現在・既定・最大） | 300・300・300 W | **220**・300・300 W |
| CPU | Ryzen 9 7950X、論理 32 | Ryzen 9 3900X、論理 24 |
| メモリ・cgroup の memory.max | 97,909,244 kB・89,120,571,392 B | 131,823,000 kB・123,480,309,760 B |
| IOMMU | 有効の手がかり（32 群、`ivhd0`） | 手がかり無し（0 群） |
| PCIe ホスト側の最大世代 | 5 | 4 |
| PCIe の幅（無負荷の現在値） | GPU0 16、GPU1 4 | GPU0 4、GPU1 16 |
| 同じもの | GPU の型・VBIOS・driver 595.84・クロックの最大・接続 PHB・kernel・OS・nvcc 12.9・gcc 13.3・容器 | |

## 4. 起票者の誤り

- asserted_without_measuring: 本契約の書き込み先（`experiments/analysis/...`）が bengio に留まる前提で「andrew に何も書かない」を求めたが、`.stignore` の `!experiments/**/*.py` を確かめていなかった。diff の材料を `.py` で置くと Syncthing が andrew へ 8 件を配った
- self_contradiction: Task E の定義は `~/slocal2` を直下だけで比べるため、andrew にも同名がある `stage2pilot_store` は外れる。一方 §3.3 はそれを残り物の手がかりに挙げる。定義どおりでは bengio だけの約 21 GB の契約の置き場が一覧に出ない

## 5. 逸脱

- `~/.ssh` の sha256（秘密鍵を読む）は利用者の方針に従い事前に確かめ、「取る」の回答で取った
- 同期で andrew に渡った写し 8 件は、利用者の決定で `.py.txt` に改名し同期から外した（andrew では同期が消し、未追跡は 41 件に戻った。同期が作った空のディレクトリ 3 つは andrew に残る。消していない）
- 試験に `PYTHONDONTWRITEBYTECODE=1` を足した（repo に `__pycache__` を書かないため）。andrew の試験は `/tmp` への書き込みが避けられず回さず、別の起点（andrew の当時の分岐）の記録を使った
- 拡張の読み込みは上流の `load()` ではなく `.so` の直接の読み込みで確かめた（装置を見せない形では上流の経路が読み込みを試みない）
- `make forbidden-check` は TASK を渡さないと allow_write が効かず fail（違反 59）。`TASK=` を渡して pass
- Task E の定義の外の補足として `stage2pilot_store` の二段目を並べた（4. の矛盾への対処。一覧の本体には入れていない）
- `README.md`・`docs/experiment_log.md` は更新していない（契約の allow_write が二つの置き場に限るため）

## 6. 想定外・UNKNOWN

- 上流の `load()` 経路での拡張の読み込み（ビルドし直しの要否を含む）: UNKNOWN（装置が要る）
- andrew の現在の起点での試験の名前: UNKNOWN（記録は andrew の 2026-11-01 の分岐の起点で取ったもの）
- PCIe の負荷時の世代と幅: UNKNOWN（無負荷で測った）。`dmesg` は両ホストで出力なし
- 試験の CPU 出力の bit 一致の差が CPU の型によるか: 測っていない
- 同期の欄は `.stignore` の近似の照合（Syncthing の実装そのものではない）

## 7. 送出

- PR #282（base phase0、分岐 feat/bengio-andrew-env-survey、Draft でない）
- `make task-report`: 送信の後に audit の末尾へ記録する

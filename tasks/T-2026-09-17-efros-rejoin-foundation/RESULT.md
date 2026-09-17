# RESULT — T-2026-09-17-efros-rejoin-foundation

**host** `efros` / **repo** `~/slocal2/m2` / **branch** `feat/efros-rejoin-foundation` / 2026-09-17 JST
手続きの証跡は `audit.md`（490 行）。本書は起票者が判断に使う事実だけを置く。

## 判定

**verdict: pass**

| Gate | 判定 | 実測の要点 |
|---|---|---|
| G1（Phase A の後） | **pass** | 既存 `.venv` を `11279712329` バイト / `63549` ファイルと測り、**移動で退避**（削除していない）。退避先で同じ値を再測して一致。他台と同じ Python `3.11.16` / torch `2.1.2+cu118` / torchvision `0.16.2+cu118` / mmcv `2.1.0` で作り直し、`torch.cuda.is_available()` が `True`、GPU 行列積が通った。`jsonschema 4.26.0` を仮想環境を明示して導入し `task-validate` が exit `0`。論理名は zsh 3 形態と bash 2 形態で `efros` を返す |
| G2（Phase B の後） | **pass** | 鍵を作り指紋を記録。公開鍵だけであることを三検査と囮で示した。配布物・配置物の要約値がともに中心の `e8a08fdd…` と一致。識別子を一行で公開。ポートとプロセスの双方で起動していないことを**両方向の対照つき**で確認 |

L3 プリフライトは `5 PASS / 1 WARN / 6 SKIP / 0 FAIL`、終了コード `0`。
**SKIP は合格ではない**（P2 `cuda_ext_loaded` / P3 `deterministic_flags` / P4 `prereg_committed` /
P5 `frozen_source_hash` / P11 `gpu_free` / P12 `refs_resolved` の 6 件は実行されていない）。
WARN は P9 `spec_lint` の `separated_source@SPEC.md:47`（契約本文の誤り。下の「起票者の誤り」2 番）。

## 完了判定

| # | 実測値 |
|---|---|
| A | 退避前 `11279712329` B / `63549` F / `7053` D / `70602` 要素 → 退避後**すべて同値**。`mv` で `/home/ubuntu/slocal2/venv-archive/venv-py312-2026-09-17` へ。**削除していない** |
| B | Python `3.11.16` / torch `2.1.2+cu118` / torchvision `0.16.2+cu118` / mmcv `2.1.0` / mmdet `3.3.0` / mmengine `0.10.7` / mamba-ssm `2.2.2` / causal-conv1d `1.4.0` / numpy `1.26.4` / transformers `4.44.2`。新 `.venv` は `6380737283` B（`env-facts.md:23` の「6.3 GB」と整合） |
| C | `torch.cuda.is_available()=True` / `torch.version.cuda=11.8` / `device_count=2` / `NVIDIA RTX A6000` / 256×256 行列積が通った。`mmcv` は当初 `libGL.so.1` で落ち、**利用者が `libgl1` を導入**して解消（`ldconfig` の該当 `0`→`1`、`import mmcv` が `2.1.0` を返す） |
| D | `jsonschema 4.26.0`。`sys.executable` が `/home/ubuntu/slocal2/m2/.venv/bin/python`。`task-validate` exit `0` |
| E | 設定前 `SERVERNAME=未設定` / `EGOSURGERY_SERVER_NAME=未設定` / `hostname=efros` / `hostname -f=efros`。5 形態すべて「未設定」。`~/.bash_profile` `~/.bash_login` は無し |
| F | `~/.zshenv:8-10` `~/.profile:32-34` `~/.bashrc:123-125` に同一の 3 行（`export SERVERNAME=efros` を標識で挟む） |
| G | `zsh -c` `zsh -ic` `zsh -lc` `bash -lc` `bash -ic` の 5 形態で `efros`。`bash -c`（非対話・非ログイン）のみ未設定＝**利用者ファイルでは覆えない既知の限界**（スクリプトが毎回表示する） |
| H | `id_ed25519_efrostophilip` は **0 件**だったので作った。`id_ed25519_github` は別用途。**触っていない** |
| I | `256 SHA256:Ney1waioF2sdDnbxOZyo/ff1Y6yz8x8kvnLSJGM0qF0 efrostophilip (ED25519)`。合言葉なし。**秘密鍵の中身は読んでいない・記録していない** |
| J | `~/.ssh`=`700` / 秘密鍵=`600` / 公開鍵=`644`、いずれも `ubuntu:ubuntu` |
| K | `scripts/sync/hub_keys/efros.pub`。指紋は生成物と `diff` で一致。先頭 `ssh-`=`1` / 秘密鍵の書き出し=`0` / 行数=`1` / `95` B。**囮は同じ三検査で `0` / `1` / `4` と逆向きに落ちた** |
| L | 書庫内で名前が `syncthing` の要素は **3 件**（`1709` / `175` / **`27045912`**）。大きさで特定した実行ファイルの要約値が中心と**一致**。否定対照（囮への同じ照合）は不一致 |
| M | `~/bin/syncthing` `27045912` B / 権限 `600` / 要約値**一致**。`[ -x ]` は **FALSE**、実行権を立てた囮への同じ判定は **TRUE** |
| N | `~/.local/state/syncthing/` は**存在しなかった**ので `generate`。`config.xml` `cert.pem` `key.pem` を生成。**上書きしていない** |
| O | `scripts/sync/device_ids/efros.txt` に `1` 行 `64` B。他台 5 件と行数・大きさ・書式がすべて一致 |
| P | ポート `22000` / `8384` の LISTEN は `0` / `0`。**対照用リスナを立てると `1` / `1`、撤去で `0` / `0`**。`/proc/PID/exe` の `syncthing` 一致は `0` 件、対照 `/bin/sleep` は `2` 件、否定対照 `zzz_no_such_exe` は `0` 件。`~/bin/keeper.sh` `~/bin/m2-sync.sh` `~/.syncthing.log` はいずれも無し |
| Q | `context/env-facts.md` の **7 行**（12 / 18 / 19 / 24 / 25 / 29 / 62）。内訳は `audit.md` の「8. Task 5」 |
| R | 本書は指定の 8 節。手続きの証跡は `audit.md` へ分離した |
| S | 下の「`proposal_gate` と `folds` の適用」 |
| T | 秘匿検査は形だけを見る（先頭 4 バイト・`PRIVATE KEY` の件数・行数・バイト数）。**値を出力していない**。陽性対照つき。`make task-report` 内側の検査も通した（後掲） |
| U | 変更は 4 経路のみ。範囲外は **0 件**。PR は「送出」節 |
| V | 「送出」節 |

## 後続で使う値

| 項目 | 値 |
|---|---|
| 鍵の指紋（中心の受け入れ一覧へ入れる値） | `SHA256:Ney1waioF2sdDnbxOZyo/ff1Y6yz8x8kvnLSJGM0qF0` |
| 公開鍵の置き場 | `scripts/sync/hub_keys/efros.pub`（注記 `efrostophilip`） |
| 秘密鍵（**このホストから出していない**） | `~/.ssh/id_ed25519_efrostophilip` |
| 識別子 | `LW4CO4U-XINDYL5-WDTK4LN-NANREIJ-LHSPA6F-6VPGZ3R-2ADLKLP-GG6AUQW` |
| 識別子の置き場 | `scripts/sync/device_ids/efros.txt` |
| 同期処理の版 | `v2.1.3`（`e8a08fdd8b25340aae0c0a00ab131b293830e4ea47504d4b83a82f31b52b96c4`）。`~/bin/syncthing`、権限 `600` |
| 設定の場所 | `~/.local/state/syncthing/`（既定） |

**後続の契約への申し送り**: `env-facts.md:63-64` の「公開の探索網と公開中継を起動前に無効にする」
「自動更新を実行権を戻す前に 0 にする」は**まだ当てていない**。本契約は起動しないため設定を変更していない。
起動を伴う契約で当てること。

## `proposal_gate` と `folds` の適用

| 節 | 適用 | 根拠（実測） |
|---|---|---|
| `proposal_gate` の提案カード・失敗時手順・引用規約・役割分離 | **適用されない** | 節は「手法・結合・補助信号・修正案の提案は…契約に落とす」を対象とする。本契約は `kind: impl` の基盤整備で、手法も結合も補助信号も修正案も提案していない |
| `proposal_gate` の**禁止語** | **適用される** | 節が対象を「提案**と契約の本文**」と明記する。`tools/check_proposal.py --only forbidden` を `SPEC.md` `audit.md` `RESULT.md` に当てた（検出 `0` 件）。陽性対照の囮は `4` 件を返した |
| `folds` | **適用されない** | 節は動画単位 5-fold の評価規律であり、本契約は学習も評価も行わない（`plan.phases` は 3 段すべて `gpu: false`、`expected_runs` 無し）。`inputs.data.split_files` の `data/splits/ego_val.txt` は雛形の必須項目で、**参照していない**（SPEC が明記。`data/**` に触れていないことは `git status` で確認） |

## 訂正した記述

`context/env-facts.md` の 7 行（12 / 18 / 19 / 24 / 25 / 29 / 62）。**`conventions.md` には触れていない。**
起票者が挙げた 3 件（repo の位置・到達性・uv の実体）に加え、**本ホストで実測して食い違った 2 件**を直した。

- 行 24「壊れ方は dangling symlink。貼り直しで足りる」→ **efros は `.venv/bin/python` が 0 件**で、貼り直しでは足りなかった
- 行 62「識別子は `serve --device-id`。`device-id` という下位命令は無い」→ **v2.1.3 では逆**

行 25 の訂正には注記が要る。**起票時点では `~/.local/share/uv/python/` 自体が存在しなかった**（私も着手時に確認した）。
**本契約の作り直しで uv が `cpython-3.11.16` を取得し、いま存在する。** ただし `.venv/bin/python` が指す先は
`cpython-3.11-linux-x86_64-gnu`（**patch 番号を含まない名前**）で、五台の記述とはディレクトリ名が異なる。

## 起票者の誤り

- **`asserted_without_measuring`** — Task 4 Step 4「取り方は `serve --home ... --device-id`。`device-id` という下位命令は無い（五台での実測）」。
  指示どおり実行すると `syncthing: error: unknown flag --device-id` / exit `80` / stdout `0` 行で識別子が取れない。
  実測では `device-id` 下位命令が `--help` の Commands に載り、正しい値を返す。**記述が逆である。**
- **`shell_assumption`** — SPEC.md:47-48。`source .venv/bin/activate` が単独の命令で終わり、次の `make task-start` がそれを前提にする。
  命令ごとに新しいシェルが起きる実装系では引き継がれず `make` が仮想環境の外で走る。
  P9 `spec_lint` が同じ箇所を該当として出した。**私は `make` を含む全命令に読み込みを同じ命令内へ入れて回避した。**
- **`asserted_without_measuring`** — Task 1 Step 2「`README.md` の『推奨セットアップ』に従う」。
  その経路の `scripts/setup_env.sh:43` は `nvcc != 11.8` で `exit 1` する。**本ホストの nvcc は 12.9 で 11.8 は無い**ため、指示どおり実行すると環境を作れずに止まる。
- **`check_does_not_check`** — `scripts/setup_env.sh:43` の nvcc 検査（起票者ではなく repo の道具の誤りだが、本契約の遂行を止めたので記す）。
  検査の根拠は `:8` の「mamba-ssm / causal-conv1d のソースビルド」だが、同スクリプトの `:77-91` は GitHub の prebuilt wheel を `--no-deps` で入れる。**ソースビルドを行わない経路に対して nvcc を要求している。**

## 逸脱・想定外・UNKNOWN

**逸脱**

1. `SKIP_CUDA_CHECK=1` を付けて `setup_env.sh` を実行した（上の 4 番目の誤りが理由）。prebuilt wheel 経路は nvcc を使わない。結果として mamba-ssm / causal-conv1d は正常に読み込めた。
2. 退避先を `~/` ではなく `/home/ubuntu/slocal2/venv-archive/` にした。`~/` は overlay、`~/slocal2` は `/dev/sdd1` で**別のファイルシステム**であり、跨ぐと 11 GB の実コピーになる。**同一ファイルシステム内の rename にして、失う経路を断った。** repo の外という条件は満たす。
3. 実行順。手順書は L3 プリフライトを実行の前に置くが、着手時点の `.venv` は壊れており `make` 自体が `Error 127` で動かなかった。**Task 1 を先に済ませてからプリフライトを回した**（SPEC の指示に沿う）。
4. `make taskindex` `make inbox` を**実行していない**。手順書の第 6 節はこれらを求めるが、契約の禁止 7 が「生成物を再生成する」を禁じる。**契約を優先した。** `tasks/inbox.d/` への書き込み（生成元）は行った。
5. 論理名の追記先。SPEC は `~/.zshenv` と `~/.profile` の 2 件を指定するが、`setup_host_servername.sh` は `~/.bashrc` を含む 3 件へ書く。**上位集合であり、スクリプトを読んだうえでそのまま使った。**
6. `sudo` を私は実行していない。`libgl1` の導入は**利用者に提示して許諾を得て、利用者自身が実行した。**
7. `make task-start` を使っていない。契約と分岐が既に存在し、着手時点では仮想環境が壊れていて `make` が動かなかった。

**想定外**

- `.venv/bin/` に Python の実体が**1 件も無かった**（`env-facts.md` が書く dangling symlink ですらない）。`pyvenv.cfg` が指す `~/.local/share/uv/python/` ごと存在しなかった。
- 本ホストの nvcc は `12.9`、driver は `595.84`（`README.md` の「driver 535 / nvcc 11.8」と異なる）。それでも cu118 の wheel は動いた。
- `~/.ssh/**` の一覧も `~/bin/**` への書き込みも**拒まれなかった**（`env-facts.md:46-47` は「拒まれることがある」）。
- 試験が `6 failed, 550 passed`。**落ちた 6 件は本契約と無関係な既存の不一致**（文言の不一致と、退役した投稿経路の戻り値を期待する試験）。`src/**` `tests/**` は一切変更していない。

**UNKNOWN**

- 試験の**開始前の値**。着手時点の `.venv` には Python の実体が無く `pytest` の実行系が起動しないため、測れなかった。落ちた試験は `0` 件だが、**通った試験も `0` 件**である。
- 落ちた 6 件が**他台でも落ちるか**。他ホストへ接続しない（禁止 5）ため測っていない。
- 中心 philip への**到達性**。本契約では測っていない（SPEC が「中心から測定済み」とする値を引き写していない）。
- **`he` の到達性**。測っていない。
- 本ホストの**平文 `.env` が `.env.gpg` と異なる**。`load_env.sh` が警告を出して上書きを拒み、保護は働いた。
  どちらを正とするかは**判断していない**（`.env` は禁止領域であり触っていない）。起票者へ申し送る。

## 送出

| 項目 | 値 |
|---|---|
| commit | `99db7264` |
| PR | **#178**（`feat/efros-rejoin-foundation` → `phase0`） |
| push | 終了コード `0` |
| `make task-report` の終了コード | `0` |
| 台帳の応答 | `verdict: pass` / `n_issuer_defects: 4` / `report_bytes: 14176` / `report_sha256: c994b3c7d0da8c58687eb1778ec31ff21c5587b65aa756b374a312d67a1b89c4` / `replaced_blocks: 0` |
| 記録の追補 | `bae4045d`（PR と秘匿検査）、本節の追記 |

**秘匿検査（完了判定 T）は送出の前に自分で行った。** 変更 9 件に対し、秘密鍵の書き出し `0` /
40 桁 16 進 `0` / 合言葉様の並び `0`。さらに**秘密鍵の本体行そのものとの照合**で出現 `0` 回。
**陽性対照**は同じ検査で `1` / `1` / `1`、本体行を含む囮との照合で `5` 回を返した。
**検査は件数だけを返し、一致した中身を出力していない。** 照合用の一時ファイルは消去した。

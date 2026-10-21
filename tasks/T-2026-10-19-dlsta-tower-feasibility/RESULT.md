# RESULT — T-2026-10-19-dlsta-tower-feasibility

ホスト dlsta（repo `~/local/m2`）、2026-10-21。命令と出力は `audit.md`（以下 `audit:` と節で指す）。表と道の一覧は
`experiments/analysis/dlsta_tower_feasibility/REPORT.md`。

## 1. 解決された参照

`contract.inject_verbatim` の原文（`context/conventions.md`、版 `5c0eaeeb`）。

### conventions#prohibitions

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### conventions#env_p0

<a id="env_p0"></a>
## env_p0

学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
数値が変わったまま完走する。

    source .venv-relation-detr/bin/activate   # 検出系
    source .venv/bin/activate                 # 解析・工程系

拡張のロード確認をログに残すこと。

### conventions#issuer_cautions

<a id="issuer_cautions"></a>
## issuer_cautions

**起票者が書いた検査も誤り得る。静的検査を通過したことは正しさを保証しない。**
実装・実環境・対象集合を確認し、**契約の前提と実測が食い違う場合は変更前に停止して記録すること。**

| # | 注意 |
|---|---|
| 1 | **起票者が「確定」と書いた値も、実測と食い違えば実測を正とする** |
| 2 | 一致 0 件なら別の異質な方法でも確認する |
| 3 | **対照は両方向で取る。** 片方向では「常に 0 を返す壊れ方」と区別できない |
| 4 | 仕組みの挙動は実装を読んでから信じる |
| 5 | **終了コードを件数と呼ばない。** 数えるなら `grep -c` |
| 6 | **プロセスは `/proc/PID/exe` で絞る。** 部分一致は実行基盤の包み込みを拾う |
| 7 | **丸めた表示を実数として扱わない** |
| 8 | **秘匿検査は形で判定し、検査自身が値を出力しない。** 要るのは長さと有無だけ |
| 9 | 無変更は要約値で確かめる。表示属性では足りない |
| 10 | 記録作成と表示用の切り詰めを同じ流れにしない |
| 11 | 測定の副作用が禁止領域へ触れないか確かめる |
| 12 | **判断の前に、いま見ているものが最新かを確かめる** |
| 13 | **要素の階層を見ずに検索しない。** ひな型と実体を取り違える |
| 14 | **規則の字面に複数の読みがあるとき、狭い読みを既定にしない。** 読みの候補を列挙して利用者に諮る |

**注意 12 の実測**: 古い版管理の状態で見たため「道具が存在しない」と 3 件報告されたが、
確かめると 3 件とも実在した。

**注意 3 の実測**: 陽性対照が実際に落ちて検査器の欠陥を検出した
（`${(P)var}` を bash が解釈できず、照合が黙って飛んでいた）。

**注意 6 の実測**: 否定対照 `zzz_no_such_token` が 1 を返した
（自分の命令行にその語が含まれるため）。

**注意 14 の実測**: 「初期化は ImageNet か中立 SSL」を「凍結」「COCO 排除」と二度狭く読み、比較する塔の非対称を二周した。

**シェルの前提**: 対話シェルは zsh。配列添字で終了コードを取れない。単語分割が起きない。
一致しないグロブはコマンド自体を実行させない。**実装を評価するなら実装が指すシェルで行う。**

**命令ごとに新しいシェルが起きる実装系がある。** `make` を含む命令には読み込みを同じ命令に含める。

`inputs.denominator` と `frozen_source` は本契約に無い。`conventions_rev` は実測で `5c0eaeeb` に差し替えた（`meta.amendments`、audit: A.11）。

## 2. 判定

**verdict: pass。** G1 pass（GPU1〜4 が空き。GPU0 は後に利用者の許可で使用）、G2 pass（欠け 0）、G3 pass（39/39、拡張 OK、9/9）。

## 3. 完了判定

| # | 実測 |
|---|---|
| a | repo `/home/ubuntu/local/m2` と RTX A5000 × 5（24,564 MiB）で dlsta。compute プロセス 0 枚 5、GPU0 だけ 99 MiB（容器の外の確保）。NVLink は 1–2 と 3–4。版・空き・到達は audit: A.4–A.7。対照: 自分の python 1 件 → 1（所有者 ubuntu）、PID 999999 → 0 |
| b | 28 項目すべて在り期待と一致（audit: B）。欠け 0 で諮る項目なし。対照: 期待を 15,438 にすると不一致、無い経路で 0 件 |
| c | 写しから復元、39/39 一致、拡張のビルドと読み込み OK、収束規則 9/9（構築前は収集エラー）。対照: 1 件変えた写しで FAILED（audit: C） |
| d | 処方そのまま: 最大 12,285,587,968 / 11,599,943,168 bytes、一歩 0.598 s、通信の設定は不要。batch/GPU 3 は収まり 4 は OOM。組の違いと 2 本同時（audit: D）。引数は二周目の `command.sh` と port 以外同一。batch 2 と 3 で最大確保が変わる |
| e | 処方そのまま（batch 16）は一枚に収まらない（forward で OOM）。最大は batch 13（23,689,911,808 bytes、1.235 s/micro-step）、14 は OOM。取り出し 400.7 s、時間ヘッド 10.4 s（audit: E） |
| f | 未対応。BN 53 層のうち 52 層が物理 batch 16 の統計で学ぶ。足すもの 8 項目と確かめ方の案（REPORT §5）。行は sha256 `3ee4325d…` の版の行番号（audit: E.5） |
| g | 工程塔 005: 7 指標全桁一致。検出塔 D\*-COCO A/42: AP 差 −2.31e−07、標的群 −7.59e−07（全桁一致しない）。対照: 折り B の塔で値が変わる（audit: F） |
| h | andrew・philip の 50072 に TCP で届く。port 1 は refused。同期は動作中。checkpoint 195,421,066 / 94,405,478 bytes。known_hosts の要約値は前後同じ（audit: G） |
| i | env-facts に 9 行。消えた行 0（対照: 1 行消した写しで 1）（audit: H） |
| j | 他の利用者のプロセスに触れていない。data/raw と data/external の一覧の要約値は前後同じ。試験の失敗は 6 → 6（収集エラー 1 → 0、新しい失敗 0）。`forbidden-check` pass（対照: data の経路を足すと fail）。commit するファイルの最大は §8 |
| k | §8 |

## 4. 実測（次の契約で使う値）

- **装置**: GPU1–2 と GPU3–4 が NVLink の組。GPU0 は compute プロセスが見えないまま 99 MiB 確保されている（容器の外）。
- **検出塔（処方そのまま）**: GPU ごとの最大確保 約 12.29 GB、一歩 0.598 s（NV）/ 0.600 s（GPU0+1）/ 0.606 s（GPU1+3）。
  **2 本を二つの NVLink の組で同時に回しても遅くならない**（0.596 / 0.586 s）。`NCCL_P2P_DISABLE` は要らない。batch/GPU の上限は 3（4 は OOM）。
- **dlsta で既存のスクリプトを使う落とし穴**: 設定の既定値が andrew の位置を指し、`run_stage1_dtower.sh` のままだと COCO の重みを読まない。
  評価の道具に相対経路を渡すと重みを読まずに AP 0 を返す（REPORT §2）。
- **工程塔**: 三周目の処方は一枚に収まらない。一枚の最大は batch 13。特徴の取り出しと時間ヘッドは一枚に収まる。
- **ホストをまたぐ評価**: 工程塔は全桁一致、特徴も bit 一致。検出塔は 1e−7 の桁の差（seed 間の標準偏差 0.0053）。
- **受け渡し**: Syncthing（philip 経由。`experiments/**/*.pth` は配る対象）、andrew への直接の SSH（TCP は届く、認証は未測定）、philip 中継。決めない。
- **入力の欠け**: 無い。

## 5. 起票者の誤り

- check_does_not_check: A.5 の所有者の数え方（compute-apps の PID を `/proc` で引く）は容器の外のプロセスを数えられず、GPU0 の確保を 0 件と数える。
  字面どおりだと GPU0 を「他の利用者なし」と判定して使うことになった。使用量の差で見つけた（audit: A.5）。
- self_contradiction: D.6 は GPU0 を含む組を指定するが、A.5 の除外が GPU0 に当たる場合（§3.2 に前例）の扱いが無い。
  字面どおりでは D.6 を回せない。GPU1+GPU3 で測り、許可の後に GPU0+GPU1 も測った。

## 6. 逸脱

result.yaml の `deviations` に 11 件。主なもの: GPU0 の除外と利用者の許可後の使用、利用者の指示で測定を並べた（時間の値に同時実行の条件を併記）、
`main.py` を `runpy` で包んで記憶領域を bytes で取った、環境変数 `EGO_ROOT` と `RELDETR_COCO_CKPT` を足した、検出塔の評価の 1 回目は
相対経路で重みを読まず AP 0（回し直した）、時間ヘッドは早期打ち切りまで 1 本回した、README と実験ログは allow_write の外なので更新していない。

## 7. 想定外・UNKNOWN

- 検出塔の評価の差の原因（UNKNOWN）。
- batch/GPU 3 の検出塔が全 epoch で溢れないか（300 歩だけ）。
- 工程塔の一歩の時間は検出塔の測定と同時に測った値。単独の値は未測定。
- andrew から dlsta へ届くか、SSH の認証、転送の速さ、andrew が Syncthing の同じ folder に参加しているか。
- repo の置き場の空きが 74 GB 減った分のうち、本契約以外の出所。

## 8. 送出

- PR #245（`gh pr view` の実測: isDraft false、baseRefName phase0、headRefName feat/dlsta-tower-feasibility）
- commit 1e2d7444（成果）と、本節を埋めた commit。commit した 17 件の最大は `audit.md` 40,636 bytes
- `make task-report` の終了コードは audit の末尾（送った後に記録）

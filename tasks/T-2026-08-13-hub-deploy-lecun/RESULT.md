# RESULT — lecun keeper配置（契約矛盾により停止）

**task_id:** `T-2026-08-13-hub-deploy-lecun`  **kind:** `impl`
**実行ホスト:** `lecun`  **分岐:** `feat/hub-deploy-lecun`

## 1. 解決された参照

### `contract.inject_verbatim: [conventions#prohibitions]`

`context/conventions.md` の該当アンカーの原文。

<a id="prohibitions"></a>
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |

### 省略された `inputs.sigma_policy`

`context/conventions.md#sigma` の原文。

<a id="sigma"></a>
## sigma

sigma に関する列は 4 系統ある（backlog B-18）。

1. `{metric}_pstd` / `{metric}_sstd` — seed 間の sigma（母集団 / 標本）
2. `delta_pstd_{metric}` / `delta_sstd_{metric}` — 実験間 paired Delta の sigma
3. `sigma_source` — sigma の系統。値は paired_delta または within_run_seed_spread
4. `delta_sigma_source` — paired sigma の計算方法。値は paired または unpaired_pooled

3 と 4 は直交する（どの sigma を使ったか vs paired sigma をどう計算したか）。

### 既定値（spec.yaml が sigma_policy を省略した場合に継承される値）

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

この既定は暫定である。正本（ddof=0 / ddof=1）は未決定であり、
決定され次第ここを変更する。変更時は過去の task を横断で再判定できるよう、
`RESULT.md` に解決済み sigma_policy が記録されていることを前提とする。

### 判定規約の表記

判定規約を `spec.yaml` や `prereg.md` に書くときは、絶対値を `abs(...)` の関数形で書く。
縦線による絶対値記法は markdown 表のセル区切りと衝突し、表を壊すため使わない
（backlog B-33 と同型の事故）。

    正: abs(delta) / sigma >= 1 かつ 全 seed 同符号
    誤: 縦線で delta を囲む記法

同じ理由で、区切りを表したいときは `/` かスラッシュ区切りの語を使う。

本契約は統計値を比較しないため、継承値は使用していない。

### `contract.conventions_rev`

実測値は `d422b08` でspecの値と一致した。置換は不要だった。

### L3

`5 PASS / 0 WARN / 4 SKIP / 0 FAIL`。SKIPはP2 `cuda_ext_loaded`、P3
`deterministic_flags`、P4 `prereg_committed`、P5 `frozen_source_hash`。

## 2. 停止理由

handoff 59行はlecunの全markerを退避し、74行はmarker 0件を成功条件とする。本SPECは禁止4で
markerの変更・削除・移動を禁じ、334–340行ではmarkerのSHA不変を要求する。本SPEC 18行は
食い違い時にhandoffへ従うよう命じるため、従うと同じSPECの禁止4へ違反する。

markerを残す回避も成立しない。実測でmarkerは1件、1行目非空、現在の中継は0件。正本keeper
7–23行はこのmarkerを解決し、33–38行はssh起動を試みるため、本SPECの「sshを一度も実行しない」
および「中継なし」と両立しない。

明示停止条件「handoffの手順と本SPECが両立せず、どちらに従っても禁止に触れる」に該当した。
そのため投影再生成、控え、配置、TERM、新版起動は実施していない。

## 3. 実測状態

| 項目 | 実測値 |
|---|---|
| handoff | 188行、全文読了 |
| 稼働keeper | 34行、SHA `603a6c...e503`、PID 1071、FD9 flock保持 |
| 正本keeper | 52行、SHA `9fe9c4...dd90`。稼働版と不一致 |
| marker | 1件、1行、1行目非空、2行目空、SHA `e179ab...1f46` |
| process | keeper 1 / m2-sync 0 / syncthing 2 / 22001一致0 / 不存在対照0 |
| LISTEN | 22000あり / 8384あり / 22001なし |
| keeper変更 | なし |
| marker変更 | なし |
| TERM・起動 | なし |
| rollback | 配置前停止のため不要・未実施 |

## 4. 起票者の誤り

`self_contradiction`: handoffを正としてmarkerを退避するよう命じる一方、本SPECは禁止4でmarkerの
変更・削除・移動を禁じ、後段でもmarker不変を要求する。指示どおりhandoffへ従えば禁止違反となり、
markerを残せば正本keeperがssh起動を試みるため、「sshを一度も実行しない」「中継なし」も満たせない。

`self_contradiction`: 本SPEC禁止10は統合を禁じる一方、Task 7 Step 6は
`git merge origin/phase0` を明示的に命じる。指示どおり実行すると同じ契約の禁止事項を破るため、
停止報告の分岐はmergeせず、そのままpushしてPRを作る。

## 5. 逸脱

- `judgement`: 変更を伴うPhase A Task 1の投影再生成より先に、正と指定されたhandoffとの
  整合性を読み取り専用で検査した。明示停止条件を検出後は追加変更を行わなかった。
- `judgement`: 禁止10とTask 7 Step 6の矛盾では禁止を優先し、`git merge origin/phase0` を
  実行せず、停止報告分岐のpushとPR作成だけを行う。

## 6. 陽性対照

- marker検査は実在pathでexit 0、契約専用の不存在pathでexit 1。
- process走査はkeeper 1・syncthing 2を検出し、不存在語は0。
- port復号は22000・8384をLISTENと検出し、22001は不在。
- 稼働keeperと正本keeperは異なるSHAを返し、配置が未実施であることを識別した。

## 7. 再開条件

起票者が、handoffどおりmarker移動を許可してmarker不変条件を外すか、markerを保持しても中心では
中継を起動しない別実装を先に正本化する必要がある。どちらを採るかは `UNKNOWN`。

## 8. 送出・台帳

| 項目 | 実測値 |
|---|---|
| task-validate | exit 0 |
| 文字自己検査 | 3ファイルともbmp_over 0 / hex40 0 |
| forbidden-check | exit 0、changed 6 / checked 6 / violations 0 |
| 変更範囲 | 契約ディレクトリと専用受け皿だけ、unmerged 0、diff-check 0 |
| 投影 | taskindex-check 2 / inbox-check 2。矛盾確定後のため再生成なし |

停止報告作成時点ではcommit、push、PR、同期抑止解除、台帳返送は未実施。

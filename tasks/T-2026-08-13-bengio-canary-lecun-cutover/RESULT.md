# RESULT — bengio canaryは独立復旧経路不在のため変更前停止

**task_id:** `T-2026-08-13-bengio-canary-lecun-cutover`  **kind:** `impl`
**host:** `bengio`  **branch:** `feat/bengio-canary-lecun-cutover`

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

本契約は統計値を判定しないため、継承値は使用していない。
`inputs.denominator.ref` と `inputs.frozen_source.ref` は無く、追加解決はない。

## 2. 結論と停止理由

Phase A の読み取りpreflightと補助器self-testは合格した。host変更直前の契約上の質問
「bengioのlocal consoleまたはSSHとは独立した復旧経路を現在保持しているか」に対し、
ユーザーは「ssh接続でしか操作できない」と回答した。

これは `governance.escalate_if` と G1 の明示停止条件に該当する。そのため Phase B 以降に進まず、
bengioの keeper、marker、SSH中継、Syncthing device addressは一つも変更していない。
rollbackは変更前停止のため不要で、未実施である。結果は `stopped`。

## 3. Phase A の実測

| 項目 | 実測 |
|---|---|
| bengio keeper | 1件、PID 773、PPID 1、FD9 lock保持、FD255 SHA `603a6c...e503` |
| bengio Syncthing | 2 process、22000/8384 LISTEN |
| bengio marker | `.tunnel_to_philip` 1件、1行、mode 664 |
| bengio SSH中継 / 22001 | 0件 / LISTEN 0件 |
| lecun 中心 | marker 0、keeper 1、FD9 lock保持、Syncthing 2、22000 LISTEN、22001 0 |
| strict SSH | port 50072、BatchMode=yes、StrictHostKeyChecking=yes、ClearAllForwardings=yesでexit 0 |
| 対別鍵指紋 | `SHA256:MKli4Hqp8sYzekheqdjEYKJiYALrCkJqSKGZzZ+VY58`、過去bengio監査とlecun登録監査に一致 |
| lecun authorized_keys | 対別鍵指紋が1件、mode 600、SHA `4e861b...d9db` |
| bengio known_hosts | mode 600、4054 bytes、SHA `50a529...5fe3`、strict SSH後も不変 |
| Syncthing REST | v2.1.3、granular endpoint対応、restart-required=false |
| localhost route | `tcp://127.0.0.1:22001` はphilip deviceだけに1件 |
| lecun direct address | `tcp://192.168.196.176:22000` が1件 |
| announce / relay | 両方 false |

生のsnapshotとユーザ回答は `canary-audit.md` に記録した。

## 4. L3と試験

- task-validate: exit 0、1 task、0 failed。
- L3: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL。
- SKIP: `cuda_ext_loaded`、`deterministic_flags`、`prereg_committed`、`frozen_source_hash`。
- ruff: `All checks passed!`。
- canary probe self-test: 18項目PASS。
- center probe self-test: 11項目PASS。
- Syncthing route self-test: 5項目PASS。
- rollback self-test: 5項目PASS。

## 5. Gate

| Gate | 判定 | 理由 |
|---|---|---|
| G1 | stop | 読み取り条件は成立したが、ユーザ確認によりSSH非依存の復旧経路が無い |
| G2 | UNKNOWN | G1 stopのためbackup・stagingは未実施 |
| G3 | UNKNOWN | host切替未実施 |
| G4 | UNKNOWN | device接続・双方向probe未実施 |
| G5 | UNKNOWN | 1800秒canary観測未実施 |

## 6. 陽性対照

- process/listener: 実在keeper・Syncthing・22000・8384を検出し、不存在語・22001は0件と区別した。
- lock: 一時lockを保持中は非待機取得が失敗し、解放後は成功する反転を実測した。
- route: localhostがphilipだけ、lecunだけ、重複、両方欠落のfixtureを別の判定に分類した。
- 秘匿: 囮secretは検査関数が1件検出し、通常snapshotは0件だった。
- rollback: 対象外pathとPID 1を拒否し、fake REST復旧が1回呼ばれることを実測した。

## 7. 起票者の誤り

なし。本停止は契約が意図した安全gateが正常に働いた結果で、契約の欠陥ではない。

## 8. 逸脱

- なし。G1 `on_fail: stop` に従い、host変更前に停止した。
- 環境差: 導入済みCodeGraphに `watch` サブコマンドがないため、`codegraph init` と
  `codegraph status` の up-to-date 確認までを行った。task判定には影響しない。

## 9. 再開条件

bengioにlocal console、リモートKVM、仮想基盤console、または親ホストからのコンテナ操作など、
現在のSSH・keeper・中継に依存しない復旧経路を確保する。確保後はPhase Aを再測定し、
新しい明示的肯定を記録してからPhase B以降を実行する。

## 10. 送出・台帳

| 項目 | 実測 |
|---|---|
| task-validate | exit 0、1 task、0 failed |
| spec-check | exit 0、8 rules、finding 0 |
| taskindex / inbox | 生成exit 0、taskindex-check / inbox-checkともにexit 0 |
| forbidden-check | exit 0、changed 17 / checked 13 / excluded 4 / violations 0 |
| commit / push / PR | 初稿時点で未実施 |
| 同期抑止解除 | 報告・push後に実施 |
| 台帳返送 | 最終報告commit後に実施 |

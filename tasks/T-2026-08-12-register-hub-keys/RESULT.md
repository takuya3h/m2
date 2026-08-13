# RESULT — 中心の受け入れ一覧への二件登録

**task_id:** `T-2026-08-12-register-hub-keys`  **kind:** `impl`
**実行ホスト:** `lecun`  **分岐:** `feat/register-hub-keys`

`/home/ubuntu/.ssh/authorized_keys` の既存四行を維持し、検証済みの andrew と ilya の
公開鍵を末尾へ一行ずつ追加した。秘密鍵の内容は読まず、出力・記録・複製していない。
全生出力は `audit.md`、変更前の公開鍵一覧は `authorized_keys.before`、機械可読の対は
`result.yaml` にある。

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

実測値は `d422b08` で spec の値と一致した。置換は不要だった。

### L3 で実行されなかった検査と警告

プリフライトは **4 PASS / 1 WARN / 4 SKIP / 0 FAIL**。SKIP は P2
`cuda_ext_loaded`、P3 `deterministic_flags`、P4 `prereg_committed`、P5
`frozen_source_hash`。前二者は契約に未記載、後二者は `kind=impl` のため対象外。
P9 `spec_lint` は `separated_source` を `SPEC.md:350,353,356,359,406` の5箇所で警告した。

## 2. 結論

開始時の受け入れ一覧は4行、非空4行、SHA-256
`31c96f80dd0ac97f632af95ecc00dcc6ec9d54948771d23aaf78a9ba95ec3694`、
1504 bytes、権限 `664` だった。内容を控えへ保存して完全一致を確認し、契約が必須とする
権限 `600` へ追記前に是正した。

追記後は6行、非空6行、1693 bytes、権限 `600`。`ssh-keygen` は全6行を解析し、
既存の消失は0件、増加は期待する二指紋の2件、控えとの差は末尾への追加二行だけだった。

| ホスト | 実測指紋 | 登録後註釈 |
|---|---|---|
| andrew | `SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k` | `ubuntu@Andrew` |
| ilya | `SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo` | `ubuntu@aolab` |

andrew と ilya から実際に入れるかは、このホストからは測れない。

## 3. 完了判定 13 項目

| # | 実測値 |
|---|---|
| 1 | 開始時4行・非空4、1504 bytes、mtime `1785346380`、SHA-256 `31c96f...3694`、mode `664` |
| 2 | `ssh-keygen` exit 0、4件。註釈 `philip-to-lecun`、`dakyo-mba@dmba.local`、`bengiotolecun`、`ubuntu@efros` |
| 3 | `authorized_keys.before` と原本は SHA-256 一致、`cmp=0`、`PRIVATE` 0件。囮は1件 |
| 4 | 戻し方を `audit.md` に記録し、実行していない |
| 5 | 提出物2件。andrew 95 bytes・1行、ilya 94 bytes・1行 |
| 6 | 二件の実測指紋は契約値と一致し、両 `ssh-keygen` は exit 0 |
| 7 | 両方 `ssh-` 始まり、`PRIVATE` 0件、1行 |
| 8 | 新規指紋は grep と awk 完全一致で各0件。既存指紋の陽性対照は両方式で1件 |
| 9 | 追記後6行・非空6、1693 bytes、mode `600` |
| 10 | 既存4件に対する `comm -23` は0件 |
| 11 | 増加2件。andrew と ilya の期待指紋は各1件 |
| 12 | 非空行6、解析行6、`ssh-keygen` exit 0 |
| 13 | `diff` は削除0・追加2。既存行の変更なし |

## 4. 起票者の誤り

1. `asserted_without_measuring`: 契約は追記前の権限を `600` と断定し、追記後も
   「600 のまま」としているが、実測開始値は `664` だった。指示を字面どおり
   「維持」すると G2 の期待値を満たせないため、内容照合と控え作成後、追記前に `600` へ是正した。
2. `check_does_not_check`: 非変更検査は目印を `ls -la`、keeperを `wc -c`、SSH内の
   他ファイルを一覧属性だけで比較する。指示どおり一致しても、同じサイズ・mtimeの内容変更は
   検出できないため、内容が完全同一であることまではこの検査から断定できない。

## 5. 逸脱

- `spec_defect`: 開始時権限が契約前提 `600` と異なる `664` だったため、控えと内容一致を
  確認後、追記前に `chmod 600` で是正した。
- `environment`: 陽性対照の一時ファイル削除に使う `rm -f` は実行基盤に拒否され、命令全体が
  未実行となった。削除を使わず別の一意な `/tmp` ファイルで再測定し、囮はそのパスに残した。
- `judgement`: タスク固有の禁止9を優先し、`make taskindex` と `make inbox` は実行しない。
  投影の未反映は検査結果としてのみ記録する。

## 6. 陽性対照

- 秘密鍵語検査: `PRIVATE` を含む囮は1件、控えは0件。
- 既登録照合: 既存指紋は grep と awk 完全一致で各1件、新規二指紋は各0件。
- 全行解析: 解析不能行を混ぜる試験は安全上実施せず、観測値は `UNKNOWN`。
- 既存保持差分: 既存行を削除・変更する試験は禁止のため実施せず、観測値は `UNKNOWN`。

## 7. 非変更対象の前後比較

目印 `/home/ubuntu/.tunnel_to_philip` の表示属性、`/home/ubuntu/bin/keeper.sh` の
2250 bytes、`~/.ssh/` 内の他の各項目の表示属性は前後一致した。
`ssh -N -L=0`、`keeper.sh=1`、`syncthing=2`、不存在対照 `zzz_no_such_process=0` も前後一致。
一覧に含まれる親ディレクトリ `..` の時刻だけが `06:51` から `06:58` に変わったが、
これは `~/.ssh/` 内のファイルではない。

## 8. 送出・PR・台帳

| 項目 | 実測値 |
|---|---|
| 契約検証 | `task-validate=0` |
| L3 | `preflight=0`、4 PASS / 1 WARN / 4 SKIP / 0 FAIL |
| 禁止領域 | changed 7 / checked 7 / excluded 0 / violations 0、`forbidden-check=0` |
| 投影 | `taskindex-check=2`、`inbox-check=2`。禁止9に従い再生成なし |
| 変更範囲 | status 2行、契約ディレクトリと専用受け皿だけ。unmerged 0、`diff-check=0` |
| 記録commit | `53b9d22 feat(sync): register andrew and ilya keys on hub` |
| PR記録commit | `0e6f3d2 docs(task): record PR for hub key registration` |
| 最終報告commit | `657dc66 docs(task): finalize hub key registration result` |
| 分岐送出 | `feat/register-hub-keys` をoriginへpush、上流設定済み、ahead表示なし |
| PR | **#98**、OPEN、非Draft、base `phase0`、head `feat/register-hub-keys` |
| 抑止解除 | repo直下は不存在。`/tmp/.sync-pause.released.T-2026-08-12-register-hub-keys` へ退避 |
| 台帳返送 | pass版 exit 0、`verdict=pass`、9161 bytes、起票者欠陥2件、置換1件 |

PR: https://github.com/takuya3h/m2/pull/98

| # | 最終完了判定 | 実測値 |
|---|---|---|
| 14 | 13項目に実測値またはUNKNOWN | 13項目すべて記載、UNKNOWNなし |
| 15 | 非変更対象 | 目印・keeper bytes・SSH内他項目の表示属性・プロセス件数が前後一致 |
| 16 | 変更範囲 | 契約ディレクトリと専用受け皿のみ。unmerged 0、禁止違反0 |
| 17 | 分岐送出 | 上流設定済み、ahead表示なし |
| 18 | PR | #98、OPEN、非Draft |
| 19 | 抑止解除 | repo直下に `.sync-pause` なし、契約専用 `/tmp` パスへ退避 |
| 20 | 台帳返送 | pass版 `task-report=0`、`verdict=pass`、既存ブロック1件を置換 |

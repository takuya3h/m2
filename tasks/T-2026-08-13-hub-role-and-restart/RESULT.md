# RESULT — 中心の役割と配置・再起動手順

**task_id:** `T-2026-08-13-hub-role-and-restart`  **kind:** `analysis`
**実行ホスト:** `lecun`  **分岐:** `feat/hub-role-and-restart`

本契約では配置、marker変更、keeper/m2-sync/Syncthing/SSH中継の起動・停止・再起動、
信号送信を一切行っていない。生出力と全文は `audit.md`、次契約の手順は `handoff.md`、
機械可読の対は `result.yaml` にある。

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

### L3で実行されなかった検査と警告

プリフライトは **4 PASS / 1 WARN / 4 SKIP / 0 FAIL**。SKIPはP2
`cuda_ext_loaded`、P3 `deterministic_flags`、P4 `prereg_committed`、P5
`frozen_source_hash`。前二者は契約に未記載、後二者は `kind=analysis` のため対象外。
P9 `spec_lint` は `separated_source` を `SPEC.md:353,356,359,362,399` の5箇所で警告した。

## 2. 結論

**配置順序はlecunが先、その後は一般ノードを一台ずつ。** 一般ノードの最初のcanaryを
efrosとbengioのどちらにするかは実装から決まらず `UNKNOWN` であり、現地preflightで選ぶ。

中心で不要なのはSSH中継だけである。正本7–23/31–38行のmarker分岐から外れた
Syncthing死活監視39–43、m2-sync自己更新44–46、`.stignore`反映47–49、m2-sync実行50は
中心でも必要。m2-syncは133行、稼働版と正本のSHA-256が一致し、中継語の一致は0件だった。

配置だけ、marker変更だけ、keeper再起動だけでは一般ノードの切替は完了しない。
旧SSH中継が残ると、正本33行の接続先を区別しない`pgrep`が成立し、新lecun中継を抑止する。
次契約では旧keeperを数値PID限定でTERMし、旧SSH中継も数値PID限定でTERMした後、
新版keeperを明示nohup起動する。

## 3. 完了判定13項目

| # | 実測値 |
|---:|---|
| 1 | 稼働keeper 34行・SHA `603a6c...e503`、正本52行・SHA `9fe9c4...dd90`。両全文をauditへ記録 |
| 2 | keeper全文差分47行、`diff_exit=1`。m2-syncは全文差分0行 |
| 3 | 正本31–51行の7処理を列挙。中心で不要2、必要5、UNKNOWN 0 |
| 4 | marker分岐は7–23と33–38。39–51は分岐外 |
| 5 | m2-syncの `22001`、`127.0.0.1`、`tunnel`、`ssh` は各0。keeper陽性対照15件 |
| 6 | systemd/cron/4 shell設定等の実在7出所を検索し、起動記述は `.zshrc:56` の1件 |
| 7 | keeper PID 1071、PPID 1、開始 `2026-07-18T09:44:50.750000+00:00`、子孫3件 |
| 8 | FD9にWRITE flock、非待機probe exit 1。FD255で本文保持、自己再実行なし |
| 9 | 6候補を副作用付きで比較。最安全は配置検証後、旧PIDへTERM、lock解放、明示nohup起動 |
| 10 | lecun先行。その後一台ずつ。根拠は正本31–50行 |
| 11 | handoffに中心用・一般用の事前記録、控え、配置、marker、再起動、確認、rollbackを記載 |
| 12 | 8確認について示すこと/示さないことを分離。最強確認は接続先記録付き双方向SHA一致 |
| 13 | 失敗9様式を症状・検出・rollback付きで列挙 |

## 4. 起票者の誤り

1. `check_does_not_check`: systemd確認が `/etc/systemd/system/` のファイル名だけを
   `keeper` で絞るため、別名unitの`ExecStart`にkeeperが書かれていても検出しない。
   指示どおり0件でも自動起動なしとは言えないため、system/user unit本文とcron・shell設定の
   実在7出所を全文検索し、`.zshrc:56` の1件だけと確定した。
2. `check_does_not_check`: m2-syncの4語grepが0件でも、別名変数・呼出先・設定経由の
   間接依存までは否定しない。指示どおり0件だけで中継非依存と断定すると見落とすため、
   稼働版と正本の同一性を確認して133行全文を読み、同じ検索がkeeperで15件出る陽性対照も取った。

## 5. 逸脱

- `environment`: `ss` が未導入だったため、LISTEN確認は `/proc/net/tcp` と
  `/proc/net/tcp6` を読み、8384と22000の2件を実測した。
- `judgement`: systemdのファイル名検索だけでは不十分なため、system/user unit本文、cron、
  4 shell設定を含む実在7出所を追加検索した。
- `judgement`: efrosとbengioのcanary優先順位は実装から決めず `UNKNOWN` とし、
  現地preflightで鍵指紋・旧中継・復旧経路が揃う一台を選ぶgateにした。
- `judgement`: 契約固有の禁止9を優先し、`make taskindex` と `make inbox` は実行しない。

## 6. 陽性対照

- 差分器: 同一m2-syncは差分0行、異なるkeeperは47行。
- 起動経路検索: `.zshrc:56` を1件検出し、他の出所は0件。
- lock判定: PID 1071のFD9にFLOCK表示、別probeはexit 1。
- 中継依存検索: m2-syncは0件、同じ正規表現をkeeperへ与えると15件。
- process計数: keeper 1、存在しない語 `zzz_no_such_process` は0。

## 7. 無変更

開始時と分析後で次が一致した。

| 対象 | 開始時・分析後 |
|---|---|
| keeper SHA-256 | `603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503` |
| m2-sync SHA-256 | `bcf46ba9031a45cb5f22371e6a1e598b2218782f6b0db74ab80ca6fea0aeb25f` |
| marker | 1件、`e179abd206de589bd220f3b05184b6ff5c9c764daa4624eeb409487498361f46` |
| authorized_keys SHA-256 | `4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db` |
| process | tunnel 0 / keeper 1 / syncthing 2 / m2-sync 0 / 不存在対照0 |
| lock | 同じpath・size 0・mode 664・mtime |

## 8. 送出・PR・台帳

| 項目 | 実測値 |
|---|---|
| 契約検証 | `task-validate=0` |
| L3 | `preflight=0`、4 PASS / 1 WARN / 4 SKIP / 0 FAIL |
| 禁止領域 | changed 7 / checked 7 / violations 0、`forbidden-check=0` |
| 投影 | `taskindex-check=2`、`inbox-check=2`。禁止9に従い再生成なし |
| 変更範囲 | status 2行、契約ディレクトリと専用受け皿だけ。unmerged 0、diff-check 0 |

暫定状態。commit、push、PR、抑止解除、台帳返送は未実施。

# RESULT — 中継用公開鍵の提出と中心住所の実測（andrew）

**task_id:** `T-2026-08-12-submit-hub-key-andrew`  **kind:** `impl`
**実行ホスト:** `andrew`  **分岐:** `feat/submit-hub-key-andrew`

秘密鍵の中身は出力・記録・複製していない。公開鍵、指紋、鍵の経路名だけを記録した。
生出力は `audit.md`、次契約への受け渡しは `handoff.md`、機械可読の対は `result.yaml` にある。

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

### L3 で実行されなかった検査

プリフライトは **5 PASS / 0 WARN / 4 SKIP / 0 FAIL**。SKIP は P2
`cuda_ext_loaded`、P3 `deterministic_flags`、P4 `prereg_committed`、P5
`frozen_source_hash`。前二者は契約に未記載、後二者は `kind=impl` のため対象外である。

## 2. 結論

既存の中継用秘密鍵から公開鍵を導出できた。並置公開鍵と一致し、別鍵とは異なった。
公開鍵を `scripts/sync/hub_keys/andrew.pub` に配置した。

| 項目 | 実測値 |
|---|---|
| 公開鍵指紋 | `SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k` |
| 中心住所 | `192.168.196.176`（Syncthing の `lecun` 対応と SSH `:50072` OPEN） |
| 現在の認証 | 拒否（`auth_exit=255`, `Permission denied`） |
| 通常の known_hosts | 1956 bytes、mtime `1783039635` のまま不変 |

## 3. 完了判定 14 項目

| # | 実測値 |
|---|---|
| 1 | 目印1件。`/home/ubuntu/.tunnel_to_philip`、44 bytes、1行、一行目は `/home/ubuntu/.ssh/id_ed25519_andrewtophilip`。変更なし |
| 2 | 鍵399 bytes・mode 600、並置公開鍵95 bytes・mode 644。いずれも実在 |
| 3 | 導出 exit 0。ED25519 256、上記指紋。秘密鍵本文なし |
| 4 | 導出と並置は `cmp=0`。別鍵は自身の並置と `cmp=0`、対象とは `cmp=1` |
| 5 | audit の秘密鍵書き出し形0件、囮1件。一般語一致1件は SSH エラーの認証方式名で値なし |
| 6 | 3出所から IPv4 候補12件を収集 |
| 7 | 12行を OPEN 9 / REFUSED 2 / No route 1 に分類し、合計12。対照は OPEN / REFUSED / TIMEOUT を出し分けた |
| 8 | `lecun` の Syncthing 住所と OPEN の一致から `192.168.196.176` に確定 |
| 9 | 認証 `exit=255`、公開鍵認証を拒否 |
| 10 | known_hosts の size 1956・mtime 1783039635 が前後一致 |
| 11 | `scripts/sync/hub_keys/` は不在で、同名用途との衝突なし |
| 12 | 配置公開鍵95 bytes、導出物と `cmp=0`、指紋一致 |
| 13 | `ssh-` 始まり、`PRIVATE` 0件、1行。囮は1件 |
| 14 | `handoff.md` に公開鍵場所・指紋・中心住所・目印案・認証結果を記録。目印は未変更 |

## 4. 起票者の誤り

1. `check_does_not_check`: 目印件数の命令が `grep -i tunnel` で `.tunnel.log` まで数える。
   実測で広い件数は2、`.tunnel_to_*` の目印は1だった。
2. `self_contradiction`: 禁止8が統合を禁じる一方、Phase C Step 8 が
   `git merge origin/phase0` を命じる。禁止を優先し、手動 merge は行わない。
3. `shell_assumption`: 独立シェルを前提とする手順なのに、Phase C の preflight と report の
   命令が venv・資格情報の読み込みを同じ命令に含めない。必要な source を同じ命令に加える。

## 5. 逸脱

- 環境制約で組み込み `apply_patch` が失敗したため、同じ `apply_patch` をホスト側で実行した。
- 目印件数は広い `tunnel` 名の件数と `.tunnel_to_*` の正確な件数を分けて記録した。
- 到達性候補は3出所の全 IPv4 を重複排除した12件とした。
- 禁止8との矛盾を避けるため、Phase C の手動 merge は実行しない。

## 6. 禁止領域の前後比較

目印は1件、44 bytes、mtime `1783121767`、sha256
`776609f37ad24bd6232d0d9dcace5551f8057b381c69b8e48bf56774bafc1cd3` のまま一致。
`~/bin/keeper.sh` は2250 bytes、sha256
`603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503` のまま一致。
`ssh -N -L=0`、`keeper.sh=1` も前後一致し、中継は増えていない。

## 7. 送出・PR・台帳

| # | 完了判定 | 実測値 |
|---|---|---|
| 15 | 14項目に実測値または UNKNOWN | 上表に空欄なし、UNKNOWN なし |
| 16 | 目印・稼働版・中継数 | 前後一致。詳細は「6. 禁止領域の前後比較」 |
| 17 | 変更範囲 | `forbidden-check` は changed 12 / checked 8 / excluded 4 / violations 0。unmerged 0 |
| 18 | 分岐送出 | 上流との差 `0 0`、phase0 に対して ahead 1 / behind 0 |
| 19 | PR | **#97**、OPEN、非Draft、base `phase0`、head `feat/submit-hub-key-andrew` |
| 20 | 抑止解除 | PENDING |
| 21 | 台帳送信 | PENDING |

記録 commit は `02e651b feat(sync): submit tunnel public key for andrew`。
PR: https://github.com/takuya3h/m2/pull/97

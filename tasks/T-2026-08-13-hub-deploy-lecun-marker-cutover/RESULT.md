# RESULT — lecun markerless hub keeper cutover

**task_id:** `T-2026-08-13-hub-deploy-lecun-marker-cutover`
**kind:** `impl`
**host:** `lecun`
**branch:** `feat/hub-deploy-lecun-marker-cutover`

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

`inputs.denominator.ref`、`inputs.frozen_source.ref`、`inputs.sigma_policy` は本契約に無く、追加解決はない。

## 2. 結論

lecun の旧markerを契約専用backupへ可逆退避し、Git正本keeperへ切り替えた。新keeperは一件で
FD9 lockを保持し、home直下marker、SSH local forwarding、22001 LISTENは全て零件である。
SyncthingのPID、開始tick、件数、22000 LISTENは切替前後で一致した。成功条件を全て満たしたため
rollbackは実施していない。

host切替、近接検査、記録commit、push、PR作成、同期抑止解除まで完了した。既知のspec-check
findingはL3 WARNとして提示し、ユーザー了承を得ている。台帳返送は本報告の最終commit後に実行する。

## 3. 開始時と終了時

| 項目 | 開始時 | 終了時 |
|---|---|---|
| keeper | PID 1071 / PPID 1 / start tick 7893775 | PID 3967705 / PPID 1 / start tick 232784150 |
| keeper FD255 SHA-256 | `603a6cc89cd98ed6e2def545c7b0bee362de7eb6a05ac2d6b97759a4bb93e503` | `9fe9c423002e426e774bf8366f0cb307b5bcc31da0fa1fb15ff603c5f219dd90` |
| keeper FD9 | inode 35033503、lock保持 | inode 35033503、lock保持 |
| marker | `/home/ubuntu/.tunnel_to_philip` 一件、mode 664 | home直下零件、backup内二件、mode 664 |
| SSH中継 / 22001 | 零件 / LISTENなし | 零件 / LISTENなし |
| Syncthing | PID 1079 tick 7893778、PID 1395414 tick 164743067 | 同一PID・同一tick・同一件数 |
| 22000 | LISTEN一件、inode 27311444 | LISTEN一件、inode 27311444 |
| 8384 | LISTEN一件、inode 27303292 | LISTEN一件、inode 27303292 |
| authorized_keys | mode 600、SHA `4e861bdd5c7376d2613300517f2ba7c1412bb2db7abee190c69e05310be1d9db` | 不変 |
| known_hosts | mode 600、SHA `735eccd5c2c8eae141d52252f3aa0c7b45e8b6039715d1fea41e87e7c9a737b2` | 不変 |
| sync-alerts.log | size 62065 / mtime 1786615769 | size 62210 / mtime 1786616795 |

切替後の追加領域には `2026-08-13 10:26:35 [lecun] 一時停止中` があり、新keeperによる
m2-sync一周を確認した。

## 4. 可逆性と配置照合

- keeper開始時原本と `.before.T-2026-08-13-hub-deploy-lecun-marker-cutover` は同一SHA、mode 775。
- marker原本、`marker.copy`、移動後 `.tunnel_to_philip.active` は同一SHA、mode 664。
- backup directoryはmode 700。終了時にmarker実体二件を保持する。
- Git object staging、作業ツリー正本、`/home/ubuntu/bin/keeper.sh` は同一SHA、配置mode 755。
- 旧PIDへ送った信号は数値PID 1071一件へのTERMのみ。PIDは即時消滅し、lock取得が成功した。
- launcherは固定pathを一度だけ起動し、PID 3967705を返した。

## 5. Gate

| Gate | 判定 | 実測根拠 |
|---|---|---|
| G1 | pass | 依存三object検査exit 0、不存在object exit 128、開始状態と陽性対照を取得 |
| G2 | pass | keeper/marker控えが各原本とcmp exit 0、mode一致、backup mode 700 |
| G3 | pass | 正本三者cmp exit 0、home marker 0、backup file 2、marker二実体cmp exit 0 |
| G4 | pass | 旧PID消滅、lock解放後、新PID一件が正本FD255とFD9 lockを保持 |
| G5 | pass | marker/中継/22001が0、SyncthingとSSH関連ファイル不変、pauseログ増分あり |

## 6. L3と試験

- task-validate: exit 0、1 task、0 failed。
- L3: 4 PASS / 1 WARN / 4 SKIP / 0 FAIL。
- WARN: `gate_requires_report_before_end@spec.yaml:39`。ユーザーが承知して続行を許可した。
- SKIP: `cuda_ext_loaded`、`deterministic_flags`、`prereg_committed`、`frozen_source_hash`。
- probe self-test: 修正後11項目全てPASS。
- ruff: `All checks passed!`。
- launcher引数拒否対照: exit 2、keeper件数は一件を維持。
- spec-check: exit 2。`gate_requires_report_before_end@spec.yaml:39` 一件。
- forbidden-check: exit 0、changed 8 / checked 8 / violations 0。
- taskindex-check / inbox-check: ともにexit 0。
- 文字自己検査: 4ファイルともbmp_over 0 / hex40 0。

## 7. 起票者の誤り

`shell_assumption`: Phase C Step 1の `git show --output=PATH object:path` は、このGit環境ではblobを
標準出力へ出し、PATHを空ファイルにした。指示どおりではstagingが空になって正本と一致しない。
同じGit objectを標準出力リダイレクトで再展開し、作成、mode設定、cmp、SHA確認を別命令に分けた。

## 8. 逸脱

- `spec_defect`: 上記の `git show --output` を、同じGit objectを読む標準出力リダイレクトへ置き換えた。
- `judgement`: 初回の複合コマンドは失敗したcmpを後続sha256sumの成功で隠した。host変更前に検出し、
  結論を撤回して以後のstaging作成・chmod・cmpを単独実行した。
- `judgement`: PR情報を含む完了報告をPR作成前には確定できないため、初稿をpartialで記録し、
  PR作成後に実測情報でpassへ更新する二段階記録を採る。
- `judgement`: spec-checkはG1の前契約「停止報告」を本契約の完了報告と解釈した。同じfindingを
  L3 WARNとして提示してユーザー了承済みであり、配布契約を改変して検査を黙らせず非零を記録した。

## 9. 陽性対照

- process: keeper/Syncthingを検出し、不存在語は零件。
- listener: 22000と8384を開、22001を閉として区別。
- marker: 開始時の実在path一件と不存在pathを区別し、移動後はhome零件とbackup二件を区別。
- lock: keeper稼働中は非待機取得失敗、旧PID停止後は成功、新keeper起動後は再び失敗。
- keeper配置: 旧配置版と正本はcmp不一致、控えとは一致、切替後配置版と正本は一致。
- 依存報告: 正しい三objectはexit 0、不存在task objectはexit 128。

## 10. 送出・台帳

| 項目 | 状態 |
|---|---|
| task-validate | exit 0、1 task、0 failed |
| spec-check | exit 2、既知finding一件 |
| forbidden-check | exit 0、changed 8 / checked 8 / violations 0 |
| 投影 | 生成exit 0、taskindex-check / inbox-checkともにexit 0 |
| Python検査 | ruff合格、self-test 11項目PASS、launcher拒否対照exit 2 |
| 記録commit | `9fbb65c`。最終報告更新は後続commit |
| push / upstream / ahead | push成功、`origin/feat/hub-deploy-lecun-marker-cutover`、remote比 behind 0 / ahead 0 |
| PR | #101、OPEN、非Draft、base `phase0`、head `feat/hub-deploy-lecun-marker-cutover` |
| 同期抑止解除 | repo直下なし、`/tmp/.sync-pause.released.T-2026-08-13-hub-deploy-lecun-marker-cutover` あり |
| 台帳返送 | 最終報告commit後に実行 |

PR: https://github.com/takuya3h/m2/pull/101

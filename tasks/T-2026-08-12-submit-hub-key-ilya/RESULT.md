# RESULT — T-2026-08-12-submit-hub-key-ilya

**中継用の公開鍵を提出し、中心への到達住所を測る（ilya）**  
ホスト`aolab`（契約上ilya）/ 分岐`feat/submit-hub-key-ilya` / 実行日2026-08-12

既存中継鍵から公開鍵を導出し、`scripts/sync/hub_keys/ilya.pub`へ置いた。秘密鍵本文、
目印、稼働版、常駐処理、lecun側は変更していない。生出力は`audit.md`に記録した。

## 1. 解決された参照

`contract.inject_verbatim: [conventions#prohibitions]`の原文:

```text
## prohibitions

| id | 禁止事項 |
|---|---|
| `no_split_redefine` | split を再定義しない |
| `no_raw_write` | `data/raw` `data/external` に書き込まない |
| `no_frozen_change` | 凍結源を変更しない |
| `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
| `no_runindex_hand_edit` | `runindex/` を手で編集しない |
```

`conventions_rev`は実測`d422b08`で契約記載と一致。`inputs.data`は雛形の必須項目だが
本契約では参照していない。preflightのSKIPは4件、WARNは既知のhost mismatch 1件。

## 2. 結果

- 公開鍵指紋: `SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo`（ED25519 256）
- 中心住所: `192.168.196.176`。Syncthingの`device name=lecun`対応から確定し、50072番OPEN
- 現時点の認証: 拒否、exit 255。登録前の期待と一致
- 公開鍵配置: `scripts/sync/hub_keys/ilya.pub`（94バイト、1行、導出物とバイト一致）

## 3. 完了判定21項目

| # | 完了判定 | 実測値 |
|---:|---|---|
| 1 | 目印の件数・行数・1行目 | 目印1件、42バイト、1行。1行目は`/home/ubuntu/.ssh/id_ed25519_ilyatophilip` |
| 2 | 鍵の実在と権限 | 秘密鍵399バイト・600、並置公開鍵94バイト・644 |
| 3 | 公開鍵導出と指紋 | derive exit 0、94バイト、上記指紋。秘密鍵本文なし |
| 4 | 鍵との対応 | 並置公開鍵と指紋・バイト一致。別鍵の指紋は異なる |
| 5 | 秘匿混入 | 監査本文の一致1件はSSH認証方式名のみ。囮は1件検出 |
| 6 | 住所候補 | SSH設定・hosts・Syncthing設定を確認。lecun候補1件 |
| 7 | 到達性 | 候補1件に対し分類1件、`192.168.196.176:50072 OPEN`。陽性対照は三分類 |
| 8 | 中心住所 | `192.168.196.176`。Syncthingのdevice名と住所の対応を使用 |
| 9 | 現時点の認証 | `Permission denied`、exit 255。`REACHABLE`なし |
| 10 | known_hosts前後 | サイズ1956・mtime`2026-08-03 22:14:59.236043451 +0000`で同一。隔離先1行 |
| 11 | 置き場所の衝突 | `hub_keys`と`ilya.pub`は不在で用途衝突なし |
| 12 | 配置公開鍵の指紋 | 導出時と一致、導出物とcmp exit 0 |
| 13 | 公開鍵だけか | `ssh-`開始、`PRIVATE`一致0、1行。囮は一致1 |
| 14 | handoff | 公開鍵場所・指紋・住所・目印案・認証拒否を記録。目印未変更 |
| 15 | 1–14の空欄 | 0。すべて実測値あり |
| 16 | 目印・稼働版・中継 | SHA-256前後一致、keeper 2250バイト、`ssh -N -L=0` |
| 17 | 変更範囲 | 公開鍵、本契約、判断受け皿、上位指示の`tasks/todo.md`、Skillが正規生成した投影4件だけ |
| 18 | 分岐送出 | 上流設定済み、ahead/behind=`0 0` |
| 19 | PR | #96、OPEN、非Draft、base=`phase0`、head=`feat/submit-hub-key-ilya` |
| 20 | 抑止解除 | `released`。repo直下から消え、`/tmp`へ退避済み |
| 21 | 台帳報告 | UNKNOWN（後続Stepで更新） |

## 4. 陽性対照

| 判定 | 壊す入力 | 実測 |
|---|---|---|
| 公開鍵導出 | 別用途鍵を同じ方法で導出 | 指紋が異なる`fingerprints_differ=True` |
| 秘匿検査 | 秘密鍵ヘッダー型の囮 | 囮1件、監査の実質的資格情報0件 |
| 到達性 | 開いた先・閉じた先・経路なし | OPEN・REFUSED・`Network_is_unreachable`を区別 |
| 公開鍵形式 | PRIVATE語を含む囮 | 配置物0、囮1、配置物1行・`ssh-`開始 |
| プロセス計数 | 存在しない語 | 0。keeperは1、中継は0 |
| 禁止領域無変更 | 前後の要約値比較 | 目印・keeperのSHA-256、known_hostsのサイズ・mtimeが一致 |

## 5. 逸脱

- `/tmp/kh_audit.txt`には前契約の9行が残っていたため、タスク専用
  `/tmp/kh_submit_hub_key_ilya.txt`を使った。禁止領域の隔離という目的は同じで、1行を記録した。
- 上位指示に従い`tasks/todo.md`へ計画を追記した。Codegraphは既に初期化済みで、完了時にsyncする。
- `task` Skillに従い`make taskindex`と`make inbox`で投影4件を正規生成した。手編集はしていない。

## 6. 起票者の誤り

1. `ls -a ~/ | grep -i tunnel`の件数は目印件数ではなく`.tunnel.log`も含む。このホストでは2を
   返すが、実際の`~/.tunnel_to_*`は1件である。指示どおり2を目印件数と読むと完了判定1が誤るため、
   別の集合検査で1件と確定した。
2. 禁止9は外部送信を`make task-report`だけに限定する一方、Task 4 Step 8はGit pushとPR作成を
   必須にする。両方を同時には守れない。ユーザーへ公開鍵がGit履歴に残る影響を説明し、明示承認を
   得たうえで契約の提出目的とStep 8を優先する。

## 7. UNKNOWN

- lecun側で登録作業がいつ実施されるか。本契約では登録していない。
- 登録後に同じ鍵で認証が通るか。次契約で再測定が必要。

ソースコードの変更はなく、公開鍵と記録の追加だけなのでREADME更新は行っていない。

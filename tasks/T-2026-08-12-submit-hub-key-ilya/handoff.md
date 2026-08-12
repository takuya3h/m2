# handoff — ilyaをlecunへ接続する次契約向け

| 項目 | 実測または案 |
|---|---|
| 公開鍵の場所 | `scripts/sync/hub_keys/ilya.pub` |
| 指紋 | `SHA256:5auPdGk/WfnGcmpQ8yygEc6mMv7svH8CzqulBjV3pRo`（ED25519 256） |
| 中心の住所 | `192.168.196.176`（Syncthingの`device name=lecun`対応、SSH 50072番OPEN） |
| 目印の中身（案）1行目 | `/home/ubuntu/.ssh/id_ed25519_ilyatophilip` |
| 目印の中身（案）2行目 | `192.168.196.176` |
| 現時点の認証 | 拒否。`Permission denied (publickey,password)`、exit 255 |

目印は作成・変更していない。lecun側の受け入れ一覧にも登録していない。


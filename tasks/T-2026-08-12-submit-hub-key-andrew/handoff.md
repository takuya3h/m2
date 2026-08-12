# Handoff — andrew の中心接続準備

| 項目 | 内容 |
|---|---|
| 公開鍵の場所 | `scripts/sync/hub_keys/andrew.pub` |
| 指紋 | `SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k` |
| 中心の住所 | `192.168.196.176`（Syncthing の device 名 `lecun` との対応、および `:50072` OPEN で確定） |
| 目印の中身（案） | 1行目 `/home/ubuntu/.ssh/id_ed25519_andrewtophilip`、2行目 `192.168.196.176` |
| 現時点の認証 | 拒まれた（`auth_exit=255`, `Permission denied`） |

目印そのものは作成・変更していない。中心側で公開鍵を登録する作業は次の契約で扱う。

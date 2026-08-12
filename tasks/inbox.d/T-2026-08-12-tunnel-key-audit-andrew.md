# T-2026-08-12-tunnel-key-audit-andrew

- 2026-08-12 / andrew / **出て行く向きは通らない。** 中継の鍵（`id_ed25519_andrewtophilip`、指紋 `SHA256:i7+kCZH9Yb2oX5TOd/u/AqAqvyQk0G7Yu//7BFd2G3k`）で他の九台へ SSH した結果、**認証が通った先は 0 件**。九台すべてが `Permission denied (publickey,password)`、philip のみ `No route to host`。集計は `0+9+1=10=対象数`で一致。
- 2026-08-12 / andrew / **入って来る向きも受け入れていない。** 自ホストの `authorized_keys` は **2 行のみ**（`ubuntu@aolab` RSA / `dakyo-mba@dmba.local` ED25519）。中継の鍵の指紋は**含まれない**（照合 0、陽性対照は実在指紋で 1・非実在で 0）。手元 4 鍵すべてでも 0。**自ホストは現状のままでは中心になれない。**
- 2026-08-12 / andrew / **鍵の配布も星型だった。** 中継の目印は `.tunnel_to_philip` の 1 件のみで、他ホスト向けの目印は 0 件。`known_hosts` に載っている構内の宛先も philip のみで、残り九台は未知。
- 2026-08-12 / andrew / したがって前契約の「同期処理側の設定変更は不要」に対し、**鍵の側は必要**。どのホストを中心にするにせよ、各ノードの公開鍵を新しい中心の `authorized_keys` へ登録する作業が要る。本契約は読み取りのみで、その作業は行っていない。
- 2026-08-12 / andrew / **測れていない向きがある。** 「正しい鍵なら通る」対照は取れていない（UNKNOWN）。到達できる九台ではどの鍵でも同じ文言で拒否されるため、鍵を無視して常に拒否する壊れ方と区別がつかない。実績のある唯一の宛先 philip が到達不能なため。
- 2026-08-12 / andrew / `~/.ssh/config` の `Host philip` は `IdentityFile` に **RSA 版**を指定しているが、中継の目印が指すのは **ED25519 版**。常駐処理は別名を経由せず住所へ直接つなぎ `-i` を明示するため（`keeper.sh:16`）、実際に使われるのは ED25519 版。
- 2026-08-12 / andrew / 起票者の誤り 2 件。(1) Task 3 Step 2 の `StrictHostKeyChecking=accept-new` は未知の宛先を `known_hosts` へ書き込み、同 SPEC の禁止 2（`~/.ssh/**` を変更しない）と両立しない。十台中九台が未知で実際に書き込みが発生する。(2) Task 3 Step 4 の陽性対照は、到達できる九台ではどの鍵でも拒否されるため鍵による識別が働いていることを示せない。
- 2026-08-12 / andrew / 測れなかったもの: 正方向の認証対照／自ホストが外からどの住所で見えるか／`ubuntu@aolab` が philip と ilya のどちらか／`50072` と sshd の待受 `22` の対応付け／他ホスト側の `authorized_keys` の中身。

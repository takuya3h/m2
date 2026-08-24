# T-2026-08-24-andrew-syncthing-node

- 2026-08-24 判断 — 目印の 2 行目（中心の SSH の住所）は `192.168.196.150` を採った。SPEC は
  `tcp://127.0.0.1:22001`（syncthing の device address）しか与えず、版管理内の
  `T-2026-08-12-submit-hub-key-andrew/handoff.md:8` は案として `192.168.196.176` を持つ。
  前契約 `T-2026-08-24-bengio-syncthing-node/audit.md:547` の実測（`Authenticated to 192.168.196.150`）
  を正とした。申し送り #1「起票者が確定と書いた値も、実測と食い違えば実測を正とする」に従う。
- 2026-08-24 判断 — 中心への到達確認は `ssh -N`（中心で命令を実行しない形）で行った。禁止 1 の
  但し書きを守るため。前契約の判断を踏襲。`timeout 20` の `exit 124` は接続維持を意味し、
  `Server accepts key` と `denied=0` で裏づけた。
- 2026-08-24 判断 — 自分の登録名を `Andrew` から `andrew` へ直した。bengio も初期値が `Bengio`
  だった。**`ilya` `lecun` でも同じ確認が要る。**
- 2026-08-24 判断 — 既存の共有フォルダ `default`（`/home/ubuntu/Sync`）は `claude-sync` と `m2` へ
  置き換えて消した。`<defaults>` 配下の `<folder id="">` は同期対象ではないひな型のため触っていない
  （禁止 5）。最上位の folder は編集後 2 件、起動後も 2 件。
- 2026-08-24 判断 — 禁止 6 に従い `make taskindex` と `make inbox` を実行していない。技能書は
  投影の確認を求めるが、契約の禁止が勝つと判断した。全台の統合後に一台で一度だけ回すこと。

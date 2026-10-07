# T-2026-09-21-fleet-sync-outbound-off — 判断

- [ ] 2026-10-07 [cc] 中心から六台へは手元の鍵 `id_ed25519_aolab` で入る。転送には依存しない（agent の経路を断って実測）。今後の遠隔操作の契約はこれを前提にしてよい（T-2026-09-21-fleet-sync-outbound-off）
- [ ] 2026-10-07 [cc] auto mode の実行基盤は、ノードの画面の鍵を読む操作を実行者に許さない。鍵を使う命令は利用者が `!` で実行し、実行者は照合だけをする分担で進めた（T-2026-09-21-fleet-sync-outbound-off）
- [ ] 2026-10-07 [human] `.sync-pause` は手で置かず、`task_start.sh` に任せる。SPEC の手動 touch は起票者の誤りとして扱う（T-2026-09-21-fleet-sync-outbound-off）
- [ ] 2026-10-07 [human] 退避した digest は報告の後に戻すのではなく、規約どおり契約の commit に含める（T-2026-09-21-fleet-sync-outbound-off）
- [ ] 2026-10-07 [cc] lecun は `urAccepted=3` で、記録の始まりから毎日使用状況を送っていた。中心に続いて二台目である。契約のたびに options 全体を控える運用を続ける（T-2026-09-21-fleet-sync-outbound-off）
- [ ] 2026-10-07 [human] digest はセッション終了フック（`.claude/hooks/session_end.sh`）が commit の後に書くため、契約のたびに必ず残る。`task_start.sh` の汚れの判定と規約「次の契約と一緒に含める」が衝突し、次の契約が開始できない。起票側で新しい契約として扱う（詳細は result.yaml の followups）（T-2026-09-21-fleet-sync-outbound-off）

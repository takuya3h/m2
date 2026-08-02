# t1b_filmonly seed42/123/456（inj/ctrl）

## 何か
T1b-FiLM arm（trainable=film / 6ep / film_params=266,880 / total_trainable=266,880）
の本走。experiments/ に一度も登録されていなかった（backlog B-24 参照）。

登録済みの transfer/t1b_phasefilm_{001,002} は実体が trainable=all / 3ep
（total_trainable=25,505,568）であり、この film arm とは別物。
scripts/postprocess_t1b.py:35 が TRANSFER.glob("t1b_seed*") を読み、
all arm を phasefilm という名前で登録していたことが原因。

（2026-08-02 実測で裏づけ）experiments/transfer/t1b_phasefilm_001_..._seed123 の
metrics.json は init_mAP=control_mAP=mAP=0.7291778095772903 / epoch=-1 であり、
これは /tmp/t1b_seed123（all/3ep）および /tmp/t1b_zeroctx_seed123（all/3ep/zero_ctx）
の値と一致する。film arm（/tmp/t1b_film_seed123, init=0.7291948117188538）とは
別系統であることが数値で確認できる。

## 出所と帰属
原本は lecun の /tmp/t1b_film_{,zeroctx_}seed{N}/t1b_result.json（2026-06-22 付）。
ログは lecun の WIP 退避コミット 5dcfe17 で追加された。
Bengio の退避コミット 10dc6f8 には film が 1 本も含まれず、Bengio の /tmp にも
film は残っていない（ca/all の seed42 系 4 arm のみ）。
**lecun 実行を強く示唆するが、server.txt が無く断定はできない。**
throughput（1.0–1.7 it/s）は lecun の範囲（1.0–2.3）に入るが
Bengio（1.8–2.9）と重なるため判別材料にならない。

## 実測値（原本 16 桁）
seed42  inj 0.7368020015037875 (ep2) / ctrl 0.7336931058190956 (ep2)
seed123 inj 0.7314101669777430 (ep5) / ctrl 0.7291778095772903 (ep-1)
seed456 inj 0.7256822794945949 (ep1) / ctrl 0.7254479085888478 (ep1)
共通: lr=0.0001 / film_lr=0.0005 / epochs=6 / det_steps/ep=4809 / miss_ctx=0/0
      denominator="S0-frozen 0.7051±0.0052"
warm-start ckpt: third_party/Relation-DETR/checkpoints/incoming/seed{N}/best_ap.pth
                 （seed ごとに分離、inj/ctrl は同一 ckpt を共有）

## 注意 3 点
1. t1b_film_zeroctx_seed123 は best_epoch=-1（6 epoch とも init を超えず）のため
   per_class_coco_map が空、checkpoint も無し。**欠損ではなく結果である。**
   ファイルサイズが 320 bytes（他は 860〜866）と小さいのはこのため。

2. per-class AP の "Retractor" は NaN。val に GT が存在しないため。
   RFC 8259 の標準トークンではなく、Python の json.load / jq は許容するが
   厳密パーサ（JS の JSON.parse 等）は失敗する。
   既存の experiments/**/per_class_ap.json 570 件も同形式。**正規化していない。**

3. 🔴 同一 seed でも init_mAP が inj/ctrl で一致しない:
     seed42  0.7303082181713886 == 0.7303082181713886  （完全一致）
     seed123 0.7291948117188538 != 0.7291778095772903  （5 桁目以降で相違）
     seed456 0.7216619814840780 != 0.7216586914703580  （相違）
   init_mAP は学習前の凍結評価であり、同一 ckpt・同一 eval なら同値のはず。
   丸めて同一視してはならない（backlog B-20 関連）。

   ■ 2026-08-02 追記（/tmp 全 37 result.json の実測による更新）
   当初これを「評価そのものが非決定的な証拠」と解したが、実測はそれを支持しない。
   /tmp の全 37 件で init_mAP を集計すると、seed ごとに **ちょうど 2 値**しか現れず、
   各群の内部では独立実行の run どうしが **16 桁でビット一致**する:
     seed123: 0.7291778095772903 (n=3, mtime 06-21 22:15〜06-22 05:55)
              0.7291948117188538 (n=10, mtime 06-22 06:42〜06-29 16:10)
     seed456: 0.7216586914703580 (n=3, mtime 06-21 22:09〜06-22 05:57)
              0.7216619814840780 (n=10, mtime 06-22 06:41〜06-29 20:04)
     seed42 : 0.7303082181713886 (n=8, mtime 06-22 17:18 以降のみ)
              ※ 0.8876398918087298 は work/smoke 系（別データ）で本走とは無関係
   2 群は mtime で完全に分離しており（seed123 は 05:55 < 06:42、seed456 は 05:57 < 06:41）、
   境界は 2026-06-22 の 05:57〜06:41 の間にある。
   評価が非決定的なら 13 通りの異なる値が出るはずで、実際は 2 値・群内完全一致である。
   → **評価は決定的であり、この時点で評価系に変更が入った**と読むのが実測に整合する。

   この解釈は seed42 が一致した理由も説明する。seed42 の inj/ctrl は
   **両方とも境界より後**（06-22 17:18 / 17:19）に実行されている。一方 seed123/456 は
   **ctrl が境界より前、inj が後**である。
   → seed123/456 の inj−ctrl 差は **時期の交絡を含む**。seed42 のみ交絡がない。
   Δ_inj−Δ_ctrl を 3 seed で平均する際はこの点を考慮すること。

   変更の中身は未特定。warm-start ckpt は 3 seed とも mtime 2026-05-30 で
   境界前後を通じて不変であり、ckpt 差し替えが原因ではない。

## checkpoint
best_t1b.pth 各 196,491,166 bytes を 5 run が保持（zeroctx_seed123 は無し）。
git ではなく Syncthing 層の対象。
/tmp は tmpfs ではなく overlay で、最終起動 2026-07-17 に対し
2026-06-22 付のファイルが残存＝再起動を跨いで生存している。
ただしバックアップ対象ではなく、コンテナ再作成で失われる。

## 配置場所についての注意
本ディレクトリはリポジトリ直下 transfer/ にあり、既存 26 run（hc_*, oracle_phase_*,
t1b_ca_*, t1b_camt_*, t1b_clsbias_* 等）と同じ回収原本の置き場である。
tools/harvest_runindex.py は EXPERIMENTS = REPO_ROOT/"experiments" のみを走査するため、
**ここに置いた run は runindex に登録されない**（既存 26 run も同様に未登録）。
解析対象に載せるには experiments/transfer/ 配下へ 6 点証跡を伴って昇格させる必要がある。

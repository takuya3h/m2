# audit — T-2026-10-07-design-val-subset-balance

ホスト efros。時刻は JST。命令はすべて repo 直下（`~/slocal2/m2`）、zsh。秘密の値は出力していない。

## 1. 起動前（Task A-1、A-2）

    git branch --show-current                    → feat/stage1-ptower-20（起動前）
    git status --porcelain --untracked-files=no  → 0 行（追跡ファイルの未 commit の変更なし）
    git ls-files --others --exclude-standard     → 24 件（一覧は scratchpad の untracked_before.txt）

未追跡 24 件の内訳と扱い:

| 種別 | 件数 | 扱い |
|---|---|---|
| 注釈 CSV `data/annotations/egosurgery_phase/{17..21}_*.csv` | 20 | (a) `.git/info/exclude` に 20 行（このホスト限り）。内容・場所は不変 |
| session digest `docs/sessions/digest/*.md` | 3 | `~/slocal2/m2_stash/20261007-042417/` へ mv。報告の commit で戻した |
| `stage1_ptower_20.log`（0 バイト、10/2 18:00） | 1 | 利用者の選択 1 により同じ退避先へ mv（戻さない）。開いているプロセス 0、runner 不在、コードからの参照 0 を確かめてから |

退避の対応表: `~/slocal2/m2_stash/20261007-042417/mapping.tsv`（同じファイルシステム sdd1）。

    make task-start TASK=T-2026-10-07-design-val-subset-balance
    → [task-start] 分岐を作成: feat/design-val-subset-balance（起点 origin/phase0）… 完了

開始状態: HEAD `feat/design-val-subset-balance`、HEAD = origin/phase0 = 分岐点 = `4b175b70d5cd0b10350d13b854343f532c3968ff`。
`git status --porcelain` は取り込んだ契約ディレクトリ 1 件のみ。

    make task-validate → OK、1 task(s), 0 failed
    make task-preflight → RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL
      SKIP: P2 cuda_ext_loaded, P3 deterministic_flags, P11 gpu_free（plan.env.preflight に記載なし）、
            P4 prereg_committed, P5 frozen_source_hash, P13 symmetry_table_complete, P14 proposal_card_checked（exp のみ）、
            P12 refs_resolved（解決前提の参照なし）
    .sync-pause は task-start が作成済み。grep -c sync-pause ~/bin/m2-sync.sh → 2（対応版）

## 2. 未追跡の注釈 CSV の実態（Task A-3）

| 項目 | 実測 |
|---|---|
| 件数 | 20（起動前の一覧の該当行 20 と一致。存在しない経路 `99_*.csv` で数えると 0） |
| 合計バイト | 210618 |
| 一覧の要約値 | sha256(経路\tsha256 の列) = `87f62aeef0985a9e3623f964df75a52b0b6945b536179b1ac93ac74e1996135d` |
| origin/phase0 で追跡 | 0 件（陽性対照: 同じ数え方で `01_1.csv` は 1 件） |
| `.gitignore` の対象 | 0 件（`git check-ignore -v --no-index` で info/exclude 以外の出所を数えた。陽性対照: `.sync-pause` は `.gitignore:244` に一致） |
| 同じ内容の別の場所 | 20/20 が 2 か所に同一 sha256 で在る: `data/raw/OpenSurgery_Dataset/05_egosurgery_hts/egosurgery_tool_bbox/annotations/phase/`（20）、`~/slocal2/EgoSurgery/annotations/coco_format/phase/`（20） |
| 参照する repo 内の設定とコード | 文字列 `egosurgery_phase` を含む追跡ファイル 137（153 行）。内訳: コード・設定 19、tasks 107、experiments 7（過去 run の config.yaml）、docs 3、tests 1。コード・設定 19 は下に列挙 |
| 15 動画の注釈と同じファイルか | **別のファイル**（動画 17〜21。15 動画は追跡済みの 23 クリップ 01_1〜15_1）。ただし**同じディレクトリ**にあり、`a1_fold_table.load_phase` と `phase_dataset` の既定の glob `*.csv` に入る |

探し方: `find /home/ubuntu /home/ubuntu/slocal2 -xdev -type f -name '*.csv' -size -40k`（repo の当該ディレクトリを除く）357 件を sha256 で照合。
**一回目は `/home/ubuntu` だけを起点にして 0 件だった**。`/home/ubuntu/slocal2` が別のファイルシステム（sdd1）で `-xdev` から外れていたため。
起点を足して 40 件（20 種）。陽性対照: 追跡済み `01_1.csv` の sha256 は同じ候補に 2 件、存在しない値は 0 件。

コード・設定 19: `configs/stage/s3_phase_frame.yaml` `configs/stage/s4_phase_baseline.yaml` `scripts/analysis/a1_fold_table.py`
`scripts/analysis/hts_phase_coverage.py` `scripts/analysis/split_thinning_rule.py` `scripts/analysis/verify_thinning_rule.py`
`scripts/analyze_annotations_advanced.py` `scripts/analyze_annotations_eda.py` `scripts/analyze_annotations_extra.py`
`scripts/audit_hts_coverage_export.py` `scripts/audit_hts_vs_tool_phase.py` `scripts/audit_l0_hts_acceptance.py`
`scripts/audit_l0b_raw_provenance.py` `scripts/build_phase_manifest.py` `scripts/diag_hand_tool_consistency.py`
`scripts/preprocess_ego.py` `src/egosurgery/datasets/constants.py` `src/egosurgery/datasets/phase_dataset.py`
`src/egosurgery/engines/phase_trainer.py`

**影響の実測**: この 20 件が在る本ホストでは、生成器を書き込みなしで走らせると止まる。

    python scripts/analysis/a1_fold_table.py --controls
    → IndexError（choose_test_groups の scored[0]）、exit 1

`load_phase` が 20 動画（01〜15 と 17〜21）を返し、公式 test を除く 17 本を 3 本ずつ 4 組に分ける分け方が 0 通りになるため。

各ファイル（経路、バイト、sha256）:

    data/annotations/egosurgery_phase/17_1.csv	1172	847ba667fec2ece3b3734749d2594fe2275cf726b4bafdb7a77795bcc49dfe24
    data/annotations/egosurgery_phase/18_1.csv	7684	9ee21848060fc1e0ae16036ba4ef37edce38e0acadc5d389cc5bca218b918433
    data/annotations/egosurgery_phase/18_2.csv	11703	49b82ab82f5f7f4a8d472345fe7375b002158a9fd3c2b9f045f863107c90c632
    data/annotations/egosurgery_phase/19_1.csv	28413	d71b7815046cab4c953e7e4e9cfdd3d5affbafcbc5cc8ba74eee309deaa49c10
    data/annotations/egosurgery_phase/19_2.csv	8829	05843bef7c6445e242ce778313bf5cf83a57dcb7a9d14fe4e8228d6987ee035a
    data/annotations/egosurgery_phase/19_3.csv	25929	59da9280e608f0fa67551cfb5951faaa3b7bc1d75840de1b1233d32e6eae4144
    data/annotations/egosurgery_phase/19_4.csv	2238	177d3d06cd2aa96abce55d6e378fe500cb20aeb33a2ee3129007426f0ddf8f8e
    data/annotations/egosurgery_phase/19_5.csv	11793	e38d49234eadf4fd20c484dfd40b30722081accc227af1d7123597ed3dbf15b1
    data/annotations/egosurgery_phase/19_6.csv	27816	5ffb84449faf8ad2233fbd763cbce0f23f3c3948da1d61de0353d573a4b58d88
    data/annotations/egosurgery_phase/20_2.csv	9399	84f7047653d03b448246b64cffcbeb35a1830c306e03dc001e4accad6e1e9a43
    data/annotations/egosurgery_phase/20_4.csv	8706	4da37d58fd68bc224934595b605ef2935e7b1609c61ee4d62c837443bcbf113e
    data/annotations/egosurgery_phase/20_5.csv	7047	792e85f385ba5b94b122676e14db3240b83e3ff97fe52f79301a21c2f7b306c3
    data/annotations/egosurgery_phase/20_6.csv	5850	bf4def2b7ec833645df6eec49ee73017bef07c0759a55c24cba2d2d228ff9923
    data/annotations/egosurgery_phase/20_7.csv	432	0f541540834ce9e3e510cc57c2c75da8c378eb06b911eeb037e07ea2ba7fc235
    data/annotations/egosurgery_phase/20_8.csv	852	c1453c3409a5d66dd92bb7739e6ccaf3464d74472b9a457123e1663112026958
    data/annotations/egosurgery_phase/21_1.csv	1185	9318a0c659432bd12ac767b70f1cbd4ea686607b15f7b276ea4cc54cf480d2f4
    data/annotations/egosurgery_phase/21_2.csv	9672	6144b2bcda856632f77fec2f4933889372761492634e15266d1c411915b886e6
    data/annotations/egosurgery_phase/21_3.csv	16611	620af49d4d0f8075a4516beb989a61ba7d9d14cc2809ee01b757a2454c667da1
    data/annotations/egosurgery_phase/21_4.csv	21425	e3d01c25e928c623b275f30d3667b8613b416ecc7b6b251c02e2600fb493a072
    data/annotations/egosurgery_phase/21_5.csv	3862	2acf8ed508f812f006cc813b6518329e871ba8b64ed947d3cdd929b9d7d9e700

## 3. 参照の解決（Task A-4〜A-9）

- 生成器 `scripts/analysis/a1_fold_table.py`: `load_phase`（`Frame,Phase` の CSV を動画ごとに数える、glob `*.csv`）、
  `load_tool`（COCO 3 ファイル、動画は `file_name` の親ディレクトリ名）、`Material.cost` = TV_phase + TV_tool、
  `total_variation` = 0.5Σ|x−y|、比率はフレーム数／box 数の割合。val の選び方は `choose_vals`（文書 §val の選ばれ方）
- `conventions#folds` と正本 `docs/stage0/A1_fold_table.md` の表は一致（道具が両方を読んで比較）
- `conventions#det_groups`: 標的群 Skewer、Bipolar Forceps、Scalpel、Syringe、Raspatory／陰性対照群 Gauze、Mouth Gag、Suction Cannula、Tweezers。注釈のクラス名と完全一致
- `conventions_rev` = `073f9dc0b80b7ca48c2766eb6f8f2ccd17cf0fe6`（`git log -1 -- context/conventions.md`。作業ツリーと同一を `git diff --quiet` で確認）
- `runindex_commit` = `2fb7c905b51aac5ec2b0ee5fe5c70e835f4024a8`（`git log -1 -- runindex/`、作業ツリーと同一）。counts は中身を開かず、同じ commit で T-2026-10-04 が測った 1911/718/1506 を引き継いだ
- 逐語注入の原文は `context/conventions.md` の 4 節（prohibitions 98–107、issuer_cautions 150–187、folds 284–318、det_groups 362–374 行）。要約していない
- 公式分割 3 ファイルを読んだ（test 04 05 07、val 09 10、train 10 本）。折り A と一致

## 4. 道具の実行（Task A-5〜C）

    source .venv/bin/activate && python scripts/analysis/design_val_subsets.py --write   # 二回

二回とも exit 0、FAIL 0、PASS 35。出力（二回目、開いた入力の行は §5）:

    INFO load_phase の既定の読み込みが返した動画: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '17', '18', '19', '20', '21']
    PASS 15 動画（折り表の test の和）: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15']
    PASS 工程の注釈が 15 動画にある: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15']
    PASS 術具の注釈の動画が 15 動画に一致: ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15']
    PASS 合計値が材料の合計行に一致: {"frames": 17233, "images": 15437, "boxes": 49652, "phases": 9, "classes": 15, "videos": 15}
    PASS 対照: 入力を一行変えると総フレームが変わる
    PASS 工程の母数（宣言 9）と注釈の工程が一致: ['anesthesia', 'closure', 'design', 'disinfection', 'dissection', 'dressing', 'hemostasis', 'incision', 'irrigation']
    PASS 術具の母数（COCO categories 15）と注釈のクラスが一致
    PASS 規約の折り表が正本の表と一致
    PASS 折り A が公式分割に一致
    INFO val の導出: {"02": ["C"], "04": ["A"], "05": ["A"], "06": ["D"], "07": ["A"], "08": ["C"], "09": ["E"], "10": ["E"], "12": ["E"], "15": ["D"]}
    PASS val 10 本、各 val 動画は自分の折りの test に入らず、test になる折りがちょうど一つ
    PASS 対照: val を自分の折りの test に置いた表で検査が落ちる: 動画 09 が自分の折りの test に入る: ['A']
    PASS 群のクラス名が注釈のクラス名と完全一致で照合できる: target=['Skewer', 'Bipolar Forceps', 'Scalpel', 'Syringe', 'Raspatory'] negative=['Gauze', 'Mouth Gag', 'Suction Cannula', 'Tweezers']
    PASS 対照: 一文字違いの群の定義で照合が落ちる: ['Skewers']
    GATE G1 PASS
    PASS d(test_A) が正本と小数第 4 位まで一致: 0.296647
    PASS d(test_B) が正本と小数第 4 位まで一致: 0.284446
    PASS d(test_C) が正本と小数第 4 位まで一致: 0.262836
    PASS d(test_D) が正本と小数第 4 位まで一致: 0.266745
    PASS d(test_E) が正本と小数第 4 位まで一致: 0.281091
    PASS d(15 動画全体) = 0: 0.000e+00
    PASS 対照: 動画 1 本の d はすべて 0 より大きい: min=0.3666
    PASS 対照: 比率の一要素を変えると TV が変わる
    INFO 15 動画全体の欠落: 工程 0 [] / 術具 0 []
    PASS 対照: 工程 anesthesia を除くと工程の欠落が一つ増える
    PASS 対照: 術具 Bipolar Forceps を除くと術具の欠落が一つ増える
    PASS 清浄側: §2 の val_A の内訳と一致: 実測 (3, 3, 3, 3, 1) / 起票 (3, 3, 3, 3, 1)
    PASS 清浄側: §2 の val_C の内訳と一致: 実測 (3, 3, 3, 2, 2) / 起票 (3, 3, 3, 2, 2)
    PASS 清浄側: §2 の val_all の内訳と一致: 実測 (0, 3, 1, 1, 0) / 起票 (0, 3, 1, 1, 0)
    PASS 清浄側の恒等式が全行で成り立つ: 1023 行
    PASS 対照: 一行の折り内訳を変えると恒等式の検査が落ちる: 違反 511 行
    GATE G2 PASS
    PASS 列挙: 行数・本数ごとの件数・重複 0: 1023 行 = 2^10-1 = 1023
    PASS 対照: 同じ集合を二度入れた表で重複の検査が落ちる: 行数 1024 != 2^10-1; 本数 1: 11 != C(10,1); 重複行 1
    PASS 再現性: 二度の実行で csv の要約値が一致: 18c06016f8ffbf5a37ab8aed04cf02527baa88cdf6538c634b49203791a3cd68
    PASS 対照: 入力を一行変えると csv の要約値が変わる: 動画 01 の工程 anesthesia に +100000（記憶上のみ） → f49a730a00148f2e
    PASS 文書に推奨の語が無い: {"推奨": 0, "勧め": 0, "最良": 0, "最適": 0}
    PASS 対照: 語を含む一時の文で数え方が働く
    INFO 本数ごとの非劣（全体）: [5, 7, 2, 4, 2, 3, 6, 5, 1, 1]
    INFO 本数ごとの非劣（公式 test 無）: [3, 5, 6, 5, 2, 3, 1, 0, 0, 0]
    PASS experiments と runindex の配下を開いていない: 0 件 / 一覧 54 件
    書きました: docs/stage1/design_val_subsets.csv（1023 行）, docs/stage1/design_val_subsets.md

ファイルの要約値（二回で同一）:

    155324f620c5882c667514c56848a153bb04e72dc433e7834a0b0bf0f808c374  docs/stage1/design_val_subsets.csv（UTF-8 BOM 付き。本文の要約値 18c06016… は BOM を除いた文字列）
    7b7d311685051e6de0bc8b7ae896684a26c6ac01fecddb606d38b06d1229f018  docs/stage1/design_val_subsets.md

参考の照合: 各折りの val の d・フレーム・box は正本の「val の値」表（0.3339 / 0.3167 / 0.2507 / 0.2806 / 0.3567）と一致。

## 5. 開いた入力（受け入れ h）

`sys.addaudithook` の open 事象で repo 内の読み込みを記録した。54 件、`experiments/` と `runindex/` の配下 0 件。
内訳: `context/conventions.md`、`docs/stage0/A1_fold_table.md`、`data/splits/ego_{test,train,val}.txt`、
`data/annotations/egosurgery_tool/instances_{test,train,val}.json`、`data/annotations/egosurgery_phase/*.csv` 43 件
（15 動画の 23 クリップ＋**未追跡の 17〜21 の 20 件**。`load_phase` の glob が開く。集計には入れていない）、
`src/egosurgery/**/__pycache__/*.pyc` 3 件（`PHASE_CLASSES` の import）。

## 6. 検証（Task D）

    make task-validate TASK=…        → OK（占位の差し替え後）
    make forbidden-check BASE=4b175b70 TASK=…  → status pass, changed 6, violations []
    陽性対照: BASE=2360768a~1 → status fail, exit 2（data/README.md、experiments/analysis/ptower_attribution/… を違反として列挙）
    試験 基準: pytest tests/ -q -p no:cacheprovider → 6 failed, 690 passed（新規 3 ファイルを一時的に外して測った）
    注釈 CSV の除外を外した後（D-7 の後）: python tools/check_forbidden.py --base 4b175b70 --task … → status fail、違反 20、
      すべて data/annotations/egosurgery_phase/{17..21}_*.csv（起動前から在る未追跡。sha256 は起動前と同一で本契約は書いていない）
    試験 変更後: 6 failed, 690 passed。失敗 6 件の名前は基準と同一（test_research_logger 4、test_engines 1、test_fetch_task 1）
    make taskindex-check → exit 0、make inbox-check → exit 0
    make agent-check → fail 1 件（docs/experiment_settings.md:155、phase0 から変化なし。本契約は触れていない）

## 7. 未追跡の注釈 CSV を戻す（Task D-7）

    .git/info/exclude から本契約が足した 21 行（注記 1 行 + 20 経路）を外した（バックアップは scratchpad の exclude.bak）
    git ls-files --others --exclude-standard -- 'data/annotations/egosurgery_phase/*.csv' → 20 件、経路は起動前の一覧と一致
    各ファイルのバイトと sha256 → 起動前の表と cmp で同一。一覧の要約値 87f62aee… で一致

## 8. session digest（Task D-6）

退避先から元の経路へ mv（3 件）。伏せ字の検査: 32 文字以上の十六進 0、鍵らしき接頭辞の長い文字列 0、
秘密を示す名前への伏せていない代入 0（3 件とも）。陽性対照: 同じ正規表現が見本の 2 行に 2 件一致。値は出力していない。

## 9. 送出

    make task-report TASK=… → exit 0
    {"verdict": "pass", "n_issuer_defects": 2, "report_sha256": "0cc4a195dde771056a21d7b7a912627b22cbe10a211f7b4dc76575233aaa1e1d", "report_bytes": 6185, "replaced_blocks": 0}

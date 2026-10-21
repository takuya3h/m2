# audit — T-2026-10-22-evidence-map-a-place

実行ホストは Bengio。時刻は JST。受入条件a〜gとG1〜G3を充足。送出・終了は末尾に記録する。

## 0. 開始と作業ツリーの整備

- 当初の分岐は `feat/proposal-gate-brief`、HEAD は `23183b42fb5609061aab9dceb35afb7198548f9a`。PR #247 の `0f3948a7` は祖先に無かった。
- 利用者の指示で origin/phase0 を fetch。先頭は `39dd92d671466edb7c96edf6c34af34c9c29ef62`。未追跡31ディレクトリの68ファイルを `git show origin/phase0:経路` とバイト比較し、同じ68・違う0・phase0に無い0。
- 利用者の指示で、追跡変更0・想定の31ディレクトリ/68ファイルだけであることを再確認し、SHA-256をrepo外に記録した。記録先は `/tmp/T-2026-10-22-evidence-map-a-place-align-sh0fttqv/` の `before.json` / `before.sha256`。
- 明示許可された `git checkout --detach --force 39dd92d671466edb7c96edf6c34af34c9c29ef62` を実行。直後の68件のSHA-256は全件一致、git statusは清浄、保持対象の分岐参照・m2-fourの分岐/HEADも同一。実測は同所の `after.json` / `after.sha256`。
- task手順書のdetached停止条件を提示し、利用者「すすめて」を受けて `git switch -c chore/evidence-map-a-place-start` を実行した。
- `git fetch origin && python scripts/task_start_classify.py` の結果は全て0件、分類は「通す」。
- `source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-10-22-evidence-map-a-place` は完了。起点origin/phase0の上に `feat/evidence-map-a-place` を作成し、契約を取り込んだ。
- task-startが `.sync-pause` を**作成**。所有は本契約・本契約分岐の2行。稼働版 `~/bin/m2-sync.sh` にsync-pauseの記載2件。解除は未実施。
- 利用者データの移動・削除、除外規則への追加、他worktreeの操作は行っていない。
- agentmemoryの検索・保存ツールは提供されていなかった。repoの `tasks/lessons.md` を確認した。Claude Code側の接続を調べるなら `/plugin list` → agentmemoryの有効化確認 → 再起動 → `/mcp` の順となる。

## 1. 検証とプリフライト

`source .venv/bin/activate && make task-validate TASK=T-2026-10-22-evidence-map-a-place`

```text
OK   T-2026-10-22-evidence-map-a-place

1 task(s), 0 failed
```

終了コード0。警告なし。

`source .venv/bin/activate && make task-preflight TASK=T-2026-10-22-evidence-map-a-place`

```text
P1 venv_active            PASS expected=/home/ubuntu/slocal2/m2/.venv VIRTUAL_ENV=/home/ubuntu/slocal2/m2/.venv sys.prefix=/home/ubuntu/slocal2/m2/.venv
P2 cuda_ext_loaded        SKIP plan.env.preflight に cuda_ext_loaded の記載なし
P3 deterministic_flags    SKIP plan.env.preflight に deterministic_flags の記載なし
P4 prereg_committed       SKIP kind=impl のため対象外（exp のみ）
P5 frozen_source_hash     SKIP kind=impl のため対象外（exp のみ）
P6 decisions_answered     PASS decisions_required は空
P7 destination_writable   PASS docs/evidence/ へ書き込みと削除ができた
P8 contract_valid         PASS validate_task.py --level l2 が exit 0
P9 spec_lint              PASS 規則 9 件を検査し該当なし
P10 preflight_names_known  PASS 宣言 1 件はすべて実装済み（既知: cuda_ext_loaded, deterministic_flags, gpu_free, venv_active）
P11 gpu_free               SKIP plan.env.preflight に gpu_free の記載なし
P12 refs_resolved          SKIP 解決前提の参照は無い
P13 symmetry_table_complete SKIP kind=impl のため対象外（exp のみ）
P14 proposal_card_checked  SKIP kind=impl のため対象外（exp のみ）

RESULT: 6 PASS / 0 WARN / 8 SKIP / 0 FAIL
```

終了コード0。SKIPは実行されなかった項目で、合格とは扱わない。

## A. 起点と受け渡し

`hostname` / `git branch --show-current` / `git rev-parse HEAD origin/phase0`、SPECの表を読み、各ファイルのバイト数と `hashlib.sha256(path.read_bytes()).hexdigest()` を計算した。アーカイブは `tarfile.open` / `extractfile(...).read()` で読むだけとし、展開・コピー・元ファイルの変更は行っていない。

全測定値は [phase-a-inventory.json](phase-a-inventory.json)。変えない7文書のSHA-256は7/7一致し、既存の報告5件と照合結果6件のSHA-256も起点で測った。

受け渡しの指定名での一致は5/9件。次の4件は指定名では置き場直下に無い。

| 指定名 | 一致する内容の所在 |
|---|---|
| 2026-10-21-A-phase-tower-candidates.md | 直下の2026-10-21-A-phase-tower-candidates_4.md、およびmap.tar.gz内 |
| A2-deep-research-report.md | 直下の「A2-deep-research-report .md」（拡張子前に半角スペース）、およびreports.tar.gz内 |
| A2-supplement-deep-research-report.md | reports.tar.gz内のA2_supplimental_deep-research-report.md |
| expected-ids.txt | 直下のexpected-ids_3.txt、およびmap.tar.gz内 |

アーカイブ内では、9/9件のバイト数とSHA-256がSPECの表に一致した。元のアーカイブを残したまま不足4件を指定名で置き場直下へコピーする方法を利用者に確認中。回答を得るまでPhase B以降へ進まない。

## A-4. 照合先への到達性

既存の `tools/verify_evidence_ids.py` の `Client` をそのまま使い、`client.get(service, path)` を逐次に呼んだ。既定の間隔・再試行規則・User-Agentを使用し、連絡先を含めていない。

| JST | 系統 | 問い合わせ先 | HTTP | 応答バイト数 |
|---|---|---|---:|---:|
| 2026-10-22 06:10:31 | doi | https://doi.org/api/handles/10.1038/s41586-020-2649-2 | 200 | 540 |
| 2026-10-22 06:10:31 | crossref | https://api.crossref.org/works/10.1038/s41586-020-2649-2 | 200 | 26102 |
| 2026-10-22 06:10:32 | datacite | https://api.datacite.org/dois?page%5Bsize%5D=1 | 200 | 3690 |
| 2026-10-22 06:10:33 | arxiv | https://export.arxiv.org/api/query?id_list=1706.03762&max_results=1 | 200 | 2962 |

到達4/4。終了コード0。本番の地図の書誌照合とは別の到達性確認である。


## A-3 補足: 受け渡しの指定名へのコピーとG1

利用者の回答「よい。今後承認不要。」を受領。tarfileで照合済みのmemberを読み、置き場直下の不足4件だけを排他的作成（openのxb）でコピーした。元のアーカイブ・別名ファイル・既存5件は変更していない。[phase-a-materials.json](phase-a-materials.json) に実測を残した。

- 作成4件、指定名でのSHA-256/バイト数の一致9/9、元の11ファイルの一致11/11。
- 起点39dd92d6、変更しない7文書の一致7/7、照合先4/4到達と合わせ、G1はPASS。
- 受け渡しの直下への配置を実行者が行った点は、利用者の明示指示に従った逸脱として報告する。

## B. 配置とG2

受け渡しの9件を、SPEC指定のrepo内経路へバイト列のまま排他的に作成した。末尾改行・私用領域の文字を変換していない。置いた後に再読し、SHA-256とバイト数が9/9件で表と一致した。[phase-b-placement.json](phase-b-placement.json) を参照。

旧地図Aの表題直後にSPEC B-2の一段落だけを挿入した。

```text
2	0	docs/evidence/2026-09-16-A-phase-tower-candidates.md
```

上は git --no-pager diff --numstat の出力（追加2行・削除0行）。挿入を取り除いたバイト列が起点の全バイト列と同一であることも確認した。git diff --name-only HEAD と git ls-files --others --exclude-standard の経路の和集合を許可範囲と比べ、範囲外は0件。G2はPASS。

## C-1. 様式の検査

命令: `source .venv/bin/activate && python tools/check_evidence_map.py`。全文出力は [format-check.txt](format-check.txt)。

```text
検査 docs/evidence/2026-10-18-B-p2d-interface.md: 違反 0 件
検査 docs/evidence/2026-10-18-C-d2p-interface.md: 違反 0 件
検査 docs/evidence/2026-10-18-N-novelty.md: 違反 0 件
検査 docs/evidence/2026-10-21-A-phase-tower-candidates.md: 違反 0 件
```

地図A v2が検査対象であることを出力で確認した。旧様式・雛形・報告・旧照合結果は対象外と表示された。プロセス終了コードは0であるが、判定には表示された違反件数を用いた。

## C-2. 書誌IDの照合

命令: `source .venv/bin/activate && python -u tools/verify_evidence_ids.py docs/evidence/2026-10-21-A-phase-tower-candidates.md`。終了コード0。

```text
実在・書誌一致 101 / 実在・書誌に差 5 / 実在・照合不能 20 / 不在 0 / 到達不能 0（計 126）
```

出力は docs/evidence/verification/2026-10-21-A-phase-tower-candidates.json と同名.md。開始は2026-10-22 06:21:18 JST、最後の問い合わせは06:22:21 JST。DOI 60回（実在・登録機関）、Crossref 30回、arXiv 2回の計92回で、全てHTTP 200。問い合わせに連絡先は含めていない。地図・元の報告は変更していない。

## C-3. IDの集合とG3

命令: `python tools/verify_evidence_ids.py docs/evidence/2026-10-21-A-phase-tower-candidates.md --extract-only`。

抽出結果 [extracted-ids.txt](extracted-ids.txt) と指定のexpected-ids.txtを、地図名・種別・IDの三つ組の集合にして差を取った。

```text
expected_count=126 actual_count=126 arxiv=96 doi=30
expected_minus_actual=[]
actual_minus_expected=[]
```

[id-set-comparison.json](id-set-comparison.json) に記録。書誌照合の結果JSONの126 IDについても同じ集合の差が両方向0だった。分類の件数の和=結果の行数=126。様式違反0と合わせ、G3はPASS。

## C-4. 事前予測との比較

事前予測はSPEC本文にある値を使用し、書き換えていない。ID単位の対応は [expected-classifications.json](expected-classifications.json) に照合結果を読む前に記録した。差の全レコードと名指しされたIDの全レコードは [phase-c-analysis.json](phase-c-analysis.json) にある。

| 分類 | 事前予測 | 実測 |
|---|---:|---:|
| 実在・書誌一致 | 104 | 101 |
| 実在・書誌に差 | 2 | 5 |
| 実在・照合不能 | 20 | 20 |
| 不在 | 0 | 0 |
| 到達不能 | 0 | 0 |

書誌に差の5 IDを全て示す。うち予測外は3 ID（A-04の2 IDとA-109のarXiv）。題名・著者の判定の説明は照合器が返した値である。

| 行・地図の行番号 | 種別・ID | 予測外 | 地図の文献欄 | 題名の判定 | 著者の判定 | 照合先の題名 | 照合先の著者全員 | 年 |
|---|---|---|---|---|---|---|---|---|
| A-04 L194 | arxiv 2503.18755 | はい | Fujii ほか 2025, EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos | 一致 / 全体 | 差 / 「ほか」の前の著者が照合先の同じ位置の著者と合わない: Fujii | EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos | Nathan Darjana / Ryo Fujii / Hideo Saito / Hiroki Kajita | 2025 |
| A-04 L194 | doi 10.1049/htl2.70049 | はい | Fujii ほか 2025, EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos | 一致 / 全体 | 差 / 「ほか」の前の著者が照合先の同じ位置の著者と合わない: Fujii | EgoSurgery‐HTS: A Dataset for Egocentric Hand–Tool Segmentation in Open Surgery Videos | Nathan Darjana / Ryo Fujii / Hideo Saito / Hiroki Kajita | 2025 |
| A-11 L201 | arxiv 2103.16327 | いいえ | 2021, TMRNet: Surgical Phase Recognition with Temporal Memory Relation Network（題名は A2g の記載） | 差 / 題名が一致しない | None / 地図に著者なし | Temporal Memory Relation Network for Workflow Recognition from Surgical Video | Yueming Jin / Yonghao Long / Cheng Chen / Zixu Zhao / Qi Dou / Pheng-Ann Heng | 2021 |
| A-28 L218 | arxiv 2107.03377 | いいえ | Xu, Gao, Chen, Davis, Crandall 2021（LSTR。旧地図の記載。旧地図は題名を書いていない） | None / 地図に題名なし | 差 / 地図 5 名・照合先 7 名。照合先に無い地図の著者: Gao, Davis, Crandall。地図に無い照合先の著者: Yuanjun Xiong, Xinyu Li, Wei Xia, Zhuowen Tu, Stefano Soatto | Long Short-Term Transformer for Online Action Detection | Mingze Xu / Yuanjun Xiong / Hao Chen / Xinyu Li / Wei Xia / Zhuowen Tu / Stefano Soatto | 2021 |
| A-109 L299 | arxiv 2202.02326 | はい | Chen, Wen, Shi, Lin, Rajbahadur, Jiang 2022, Towards Training Reproducible Deep Learning Models | 一致 / 全体 | 差 / 地図 6 名・照合先 7 名。地図に無い照合先の著者: Zhen Ming | Towards Training Reproducible Deep Learning Models | Boyuan Chen / Mingzhi Wen / Yong Shi / Dayi Lin / Gopi Krishnan Rajbahadur / Zhen Ming / Jiang | 2022 |

A-109ではarXiv APIが「Zhen Ming」と「Jiang」を別々の著者要素として返している。一方、同じ行のDOI 10.1145/3510003.3510163はCrossrefの「Zhen Ming (Jack) Jiang」を含む6名を返し、照合器の分類は書誌一致。原典の著者表記の正誤やAPI側の原因は本契約では判断しない。差を反映するための地図・照合器の修正は行っていない。

## C-5a. 名指しされた要注意ID

A-11とA-28の返値は上の5件の表に記録した。以下はSPECの「見込みに自信が無いID」の各行・9件の2026年ID・A-05/A-48/A-49のDOIである。同じIDは1件にまとめた。

| 地図の行 | 種別・ID | 分類 | 照合先の題名 | 照合先の著者全員 | 年 |
|---|---|---|---|---|---|
| A-02 | arxiv 2602.05638 | 実在・書誌一致 | SurgMotion: A Video-Native Foundation Model for Universal Understanding of Surgical Videos | Jinlin Wu / Felix Holm / Chuxi Chen / An Wang / Yaxin Hu / Xiaofan Ye / Zelin Zang / Miao Xu / Lihua Zhou / Huarui Wu / Huai Liao / Danny T. M. Chan / Ming Feng / Wai S. Poon / Hongliang Ren / Dong Yi / Nassir Navab / Gaofeng Meng / Jiebo Luo / Hongbin Liu / Zhen Lei | 2026 |
| A-04 | arxiv 2503.18755 | 実在・書誌に差 | EgoSurgery-HTS: A Dataset for Egocentric Hand-Tool Segmentation in Open Surgery Videos | Nathan Darjana / Ryo Fujii / Hideo Saito / Hiroki Kajita | 2025 |
| A-04 | doi 10.1049/htl2.70049 | 実在・書誌に差 | EgoSurgery‐HTS: A Dataset for Egocentric Hand–Tool Segmentation in Open Surgery Videos | Nathan Darjana / Ryo Fujii / Hideo Saito / Hiroki Kajita | 2025 |
| A-05 | doi 10.1007/978-3-032-31119-1_38 | 実在・照合不能 | SURGE Phase 1: An AR/VR-Based Deep Learning Framework for Surgical Scene Analysis | Hirdyansh Mahajan / Subham Singh / Saanuj Joshi / Anushka Phogat / Anmolpreet Puri / Jinee Goyal / Sachin Kansal | 2026 |
| A-13 | arxiv 2401.11644 | 実在・書誌一致 | Friends Across Time: Multi-Scale Action Segmentation Transformer for Surgical Phase Recognition | Bokai Zhang / Jiayuan Meng / Bin Cheng / Dean Biskup / Svetlana Petculescu / Angela Chapman | 2024 |
| A-19 | arxiv 2605.14889 | 実在・書誌一致 | SurgicalMamba: Dual-Path SSD with State Regramming for Online Surgical Phase Recognition | Sukju Oh / Sukkyu Sun | 2026 |
| A-23 | doi 10.52202/079017-1881 | 実在・書誌一致 | OnlineTAS: An Online Baseline for Temporal Action Segmentation | Qing Zhong / Guodong Ding / Angela Yao | 2024 |
| A-24 | doi 10.1109/CVPR52733.2024.01722 | 実在・書誌一致 | Progress-Aware Online Action Segmentation for Egocentric Procedural Task Videos | Yuhan Shen / Ehsan Elhamifar | 2024 |
| A-25 | doi 10.1109/ICCV51070.2023.00949 | 実在・書誌一致 | MiniROAD: Minimal RNN Framework for Online Action Detection | Joungbin An / Hyolim Kang / Su Ho Han / Ming-Hsuan Yang / Seon Joo Kim | 2023 |
| A-32 | arxiv 2606.02246 | 実在・書誌一致 | Ego-METAS: Egocentric online Multimodal Energy-efficient Temporal Action Segmentation benchmark | Maria Santos-Villafranca / Jesus Bermudez-cameo / Alejandro Perez-Yus / Giovanni Maria Farinella / Antonino Furnari | 2026 |
| A-41 | arxiv 2506.02692 | 実在・書誌一致 | Large-scale Self-supervised Video Foundation Model for Intelligent Surgery | Shu Yang / Fengtao Zhou / Leon Mayer / Fuxiang Huang / Yiliang Chen / Yihui Wang / Sunan He / Yuxiang Nie / Xi Wang / Ömer Sümer / Yueming Jin / Huihui Sun / Shuchang Xu / Alex Qinyang Liu / Zheng Li / Jing Qin / Jeremy YuenChun Teoh / Lena Maier-Hein / Hao Chen | 2025 |
| A-41 | doi 10.1038/s41746-026-02403-0 | 実在・書誌一致 | Large-scale self-supervised video foundation model for intelligent surgery | Shu Yang / Fengtao Zhou / Leon Mayer / Fuxiang Huang / Yiliang Chen / Yihui Wang / Sunan He / Yuxiang Nie / Xi Wang / Ömer Sümer / Yueming Jin / Huihui Sun / Shuchang Xu / Alex Qinyang Liu / Zheng Li / Jing Qin / Jeremy YuenChun Teoh / Lena Maier-Hein / Hao Chen | 2026 |
| A-48 | doi 10.1001/jamasurg.2023.6262 | 実在・照合不能 | Analyzing Surgical Technique in Diverse Open Surgical Videos With Multitask Machine Learning | Emmett D. Goodman / Krishna K. Patel / Yilun Zhang / William Locke / Chris J. Kennedy / Rohan Mehrotra / Stephen Ren / Melody Guan / Orr Zohar / Maren Downing / Hao Wei Chen / Jevin Z. Clark / Margaret T. Berrigan / Gabriel A. Brat / Serena Yeung-Levy | 2024 |
| A-49 | doi 10.1038/s41551-026-01622-w | 実在・照合不能 | An ophthalmic video foundation model for surgical recognition and navigation with wet-lab porcine eye validation | Puxun Tu / Ce Zheng / Xiaoling Xie / Jiao Lv / Meng Xie / Jinming Guo / Shengjie Yin / Kunliang Qiu / Yue Wei / Chongyang Wang / Jingfeng Cai / Wei Mi / Yafu Wang / Xiao Zhang / Danba Jiachu / Kun Peng / Wanqi Zhang / Fengfeng Tong / Huiying Chu / Peiquan Zhao / Mingzhi Zhang / Xiaojun Chen | 2026 |
| A-50 | arxiv 2608.31048 | 実在・照合不能 | OmniRAS: Standardizing Foundation Model Training and Evaluation in Robot-Assisted Surgery | Leonardo Borgioli / Neil Getty / Wenli Xiu / Jessica Cassiani / Alvaro Ducas / Carlos Agustin Orda / Hira Waris / Fangfang Xia / Rick Stevens / Pier Cristoforo Giulianotti / Milos Zefran | 2026 |
| A-51 | arxiv 2602.13633 | 実在・照合不能 | A generalizable foundation model for intraoperative understanding across surgical procedures | Kanggil Park / Yongjun Jeon / Soyoung Lim / Seonmin Park / Jongmin Shin / Jung Yong Kim / Sehyeon An / Jinsoo Rhu / Jongman Kim / Gyu-Seong Choi / Namkee Oh / Kyu-Hwan Jung | 2026 |
| A-52 | arxiv 2609.04555 | 実在・照合不能 | DART: Depth-as-Target Pretraining for Surgical Vision Foundation Models | John J. Han / Adam Schmidt / Muhammad Abdullah Jamal / Jie Ying Wu / Omid Mohareri | 2026 |
| A-69 | arxiv 2608.20157 | 実在・照合不能 | G3Ego: Gaze-Guided Graphs for Egocentric Action Understanding | Marko Haralović / Akash Ramakrishnan / Estefania Talavera Martinez | 2026 |
| A-71 | arxiv 2605.14031 | 実在・照合不能 | Masked Autoencoders with Limited Data: Does It Work? A Fine-Grained Bioacoustics Case Study | Wuao Liu / Mustafa Chasmai / Subhransu Maji / Grant Van Horn | 2026 |
| A-73 | arxiv 2603.14271 | 実在・照合不能 | Toward Clinically Ready Foundation Models in Medical Image Analysis: Adaptation Mechanisms and Deployment Trade-offs | Karma Phuntsho / Abdullah / Kyungmi Lee / Ickjai Lee / Euijoon Ahn | 2026 |
| A-79 | doi 10.1007/s11548-024-03166-3 | 実在・書誌一致 | Challenges in multi-centric generalization: phase and step recognition in Roux-en-Y gastric bypass surgery | Joël L. Lavanchy / Sanat Ramesh / Diego Dall’Alba / Cristians Gonzalez / Paolo Fiorini / Beat P. Müller-Stich / Philipp C. Nett / Jacques Marescaux / Didier Mutter / Nicolas Padoy | 2024 |
| A-79 | arxiv 2312.11250 | 実在・書誌一致 | Challenges in Multi-centric Generalization: Phase and Step Recognition in Roux-en-Y Gastric Bypass Surgery | Joel L. Lavanchy / Sanat Ramesh / Diego Dall'Alba / Cristians Gonzalez / Paolo Fiorini / Beat Muller-Stich / Philipp C. Nett / Jacques Marescaux / Didier Mutter / Nicolas Padoy | 2023 |
| A-95 | arxiv 2605.16387 | 実在・書誌一致 | Stabilizing Temporal Inference Dynamics for Online Surgical Phase Recognition | Yang Liu / Ning Zhu / Jingjing Peng / Xiwu Chen / Alejandro Granados / Guotai Wang / Sebastien Ourselin | 2026 |
| A-96 | arxiv 2403.20254 | 実在・書誌一致 | Benchmarking the Robustness of Temporal Action Detection Models Against Temporal Corruptions | Runhao Zeng / Xiaoyong Chen / Jiaming Liang / Huisi Wu / Guangzhong Cao / Yong Guo | 2024 |
| A-98 | doi 10.1145/3097983.3097997 | 実在・書誌一致 | Patient Subtyping via Time-Aware LSTM Networks | Inci M. Baytas / Cao Xiao / Xi Zhang / Fei Wang / Anil K. Jain / Jiayu Zhou | 2017 |
| A-107 | arxiv 2605.09742 | 実在・書誌一致 | TIDES: Implicit Time-Awareness in Selective State Space Models | Taylan Soydan / Miguel A. Bessa / Dirk Mohr / Rui Barreira | 2026 |
| A-108 | arxiv 2609.34409 | 実在・書誌一致 | MASCIT: A Mask-Aware State Space Classifier for Naturally Irregular Time Series | Yoo-Min Jung / Hyeon-Gi Kim / Jonghun Park | 2026 |
| A-110 | doi 10.1109/eScience55777.2022.00056 | 実在・書誌一致 | Examining the Effect of Implementation Factors on Deep Learning Reproducibility | Kevin Coakley / Christine R. Kirkpatrick / Odd Erik Gundersen | 2022 |
| A-110 | arxiv 2312.06633 | 実在・書誌一致 | Examining the Effect of Implementation Factors on Deep Learning Reproducibility | Kevin Coakley / Christine R. Kirkpatrick / Odd Erik Gundersen | 2023 |

## C-5b. 照合不能と予測した20 IDの実在と題名

「実在」は照合先のAPIが在ると答えたことを表す。論文の内容や主張が正しいことを意味しない。20件とも実在・照合不能だった。

| 地図の行 | 種別・ID | 実在の確認 | 照合先の題名 |
|---|---|---|---|
| 書誌の行なし | arxiv 2505.12890 | 在ると回答 | Specialized Foundation Models for Intelligent Operating Rooms |
| A-05 | doi 10.1007/978-3-032-31119-1_38 | 在ると回答 | SURGE Phase 1: An AR/VR-Based Deep Learning Framework for Surgical Scene Analysis |
| A-22 | arxiv 2506.01471 | 在ると回答 | SemiVT-Surge: Semi-Supervised Video Transformer for Surgical Phase Recognition |
| A-48 | doi 10.1001/jamasurg.2023.6262 | 在ると回答 | Analyzing Surgical Technique in Diverse Open Surgical Videos With Multitask Machine Learning |
| A-49 | doi 10.1038/s41551-026-01622-w | 在ると回答 | An ophthalmic video foundation model for surgical recognition and navigation with wet-lab porcine eye validation |
| A-50 | arxiv 2608.31048 | 在ると回答 | OmniRAS: Standardizing Foundation Model Training and Evaluation in Robot-Assisted Surgery |
| A-51 | arxiv 2602.13633 | 在ると回答 | A generalizable foundation model for intraoperative understanding across surgical procedures |
| A-52 | arxiv 2609.04555 | 在ると回答 | DART: Depth-as-Target Pretraining for Surgical Vision Foundation Models |
| A-55 | arxiv 2210.06096 | 在ると回答 | Masked Motion Encoding for Self-Supervised Video Representation Learning |
| A-56 | arxiv 2508.10104 | 在ると回答 | DINOv3 |
| A-60 | arxiv 2211.09529 | 在ると回答 | InternVideo-Ego4D: A Pack of Champion Solutions to Ego4D Challenges |
| A-68 | arxiv 2203.04752 | 在ると回答 | Human Gaze Guided Attention for Surgical Activity Recognition |
| A-69 | arxiv 2608.20157 | 在ると回答 | G3Ego: Gaze-Guided Graphs for Egocentric Action Understanding |
| A-70 | arxiv 2410.21302 | 在ると回答 | Domain-Adaptive Pre-training of Self-Supervised Foundation Models for Medical Image Classification in Gastrointestinal Endoscopy |
| A-71 | arxiv 2605.14031 | 在ると回答 | Masked Autoencoders with Limited Data: Does It Work? A Fine-Grained Bioacoustics Case Study |
| A-72 | arxiv 2209.12157 | 在ると回答 | Dive into Self-Supervised Learning for Medical Image Analysis: Data, Models and Tasks |
| A-73 | arxiv 2603.14271 | 在ると回答 | Toward Clinically Ready Foundation Models in Medical Image Analysis: Adaptation Mechanisms and Deployment Trade-offs |
| 書誌の行なし | arxiv 2106.11028 | 在ると回答 | Neural Controlled Differential Equations for Online Prediction Tasks |
| A-105 | arxiv 2402.10635 | 在ると回答 | ContiFormer: Continuous-Time Transformer for Irregular Time Series Modeling |
| 書誌の行なし | arxiv 2112.07219 | 在ると回答 | A real-time spatiotemporal AI model analyzes skill in open surgical videos |

## C-5c. 書誌IDの無い行

A-06、A-20、A-45、A-65、A-66、A-67、A-76、A-80、A-81、A-88、A-94（11行）。書誌照合の対象外。

## C-6. 陽性対照とSPECの記載との相違

[positive-controls.json](positive-controls.json) と [positive-control-format.txt](positive-control-format.txt) に実測を残した。元の地図は全バイトが同一のまま。

| 判定 | 壊した入力 | 実測 |
|---|---|---|
| 報告SHA-256の様式検査 | repo外のコピーでA-chatgptの参照SHA-256を64個の0に1か所だけ置換 | report_sha256違反1件、終了コード1 |
| ID集合の欠落 | 実抽出集合から1 IDだけ除く | 指定集合−実集合=1、逆方向=0 |
| ID集合の余分 | 実抽出集合に対照用IDを1件だけ足す | 指定集合−実集合=0、逆方向=1 |
| 配置した中身の照合 | 地図の先頭1バイトをメモリ上だけで変える | 期待SHA-256と不一致。実ファイルの9/9一致は維持 |

SPECの「罠5」は、同じ起点39dd92d6でSHA-256を1か所壊したコピーが終了コード0になると断定しているが、実測は1だった。違反件数を読む指示には従い、道具は変更していない。この断定と実測の相違を起票者の誤りとして報告する。誤った断定に従って終了コードを無視しても今回は違反件数で判定できたが、現在の実装の終了コードの仕様を示す根拠にはならなかった。

## D-1. 必須検証

`source .venv/bin/activate && make forbidden-check` は終了コード0、status=pass、violations=[]。全出力は [forbidden-check.txt](forbidden-check.txt)。

`source .venv/bin/activate && make spec-check TASK=T-2026-10-22-evidence-map-a-place` は終了コード0、検査9規則、該当0、errors=[]。全出力は [spec-check.txt](spec-check.txt)。

コード変更が無いため、SPECの罠6に従いmake testは実行しなかった。testsの0件は試験実施を意味しない。生成物の再生成、context-check、inbox-check、taskindex-checkも契約に従い実行していない。

## D-2. 保護文書と変更範囲の最終検証

[final-verification.json](final-verification.json) に全ての測定値と経路集合を記録した。

- 保護文書17件（旧地図A以外の指定6件、既存の報告5件、既存の照合結果6件）は起点とSHA-256一致。
- 配置9件のSHA-256とバイト数は9/9件で指定値と一致。
- SPEC.mdとspec.yamlはPhase B前に測ったSHA-256と同一。事前予測と契約本文は書き換えていない。
- 旧地図Aは指定の一段落を挿入した全バイト列と一致。gitの集計は追加2行・削除0行。
- gitの変更経路の集合のうち、許可範囲外は0件。
- agentmemoryはツール未提供により読み書き未実施。教訓・利用者の指示はrepoのauditとtasks/inbox.dの本契約の記録へ残した。

## D-3. 版管理・PR・配布台帳

commit・push・PRの作成と台帳の応答は、実施後にこの節へ追記する。PRのbaseはphase0、Draftにしない。

### D-3a. commitとPR

- 成果物のcommit: `92c368fd18c1b781a4eaa3dd34591ec967686a28`。32ファイルの追加・挿入だけで、削除・名前変更なし。契約分岐を `git push -u origin feat/evidence-map-a-place` でpushした（終了コード0）。
- `gh pr create --base phase0 --head feat/evidence-map-a-place --body-file <repo外の本文ファイル>` で通常PRを作成した。終了コード0。
- `gh pr view --json number,url,state,isDraft,baseRefName,headRefName,headRefOid` の応答を [pr.json](pr.json) へ保存した。

```json
{
  "baseRefName": "phase0",
  "headRefName": "feat/evidence-map-a-place",
  "headRefOid": "92c368fd18c1b781a4eaa3dd34591ec967686a28",
  "isDraft": false,
  "number": 254,
  "state": "OPEN",
  "url": "https://github.com/takuya3h/m2/pull/254"
}
```

- PR #254、OPEN、Draftではない、base=phase0、head=feat/evidence-map-a-place。これにより受入条件gも充足した。報告をpassに更新した。統合・自動統合の有効化は行っていない。

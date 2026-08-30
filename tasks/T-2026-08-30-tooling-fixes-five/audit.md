# audit — T-2026-08-30-tooling-fixes-five

RESULT.md はここを行番号で指す。命令と出力を時系列で置く。

## 1. 取り込み・検証・プリフライト

```
$ git stash push -u -m "task-start用の一時退避 T-2026-08-30-tooling-fixes-five"
（前契約と同じ未追跡 5 件。作業ツリーを clean にするため。完了後に pop する）

$ source .venv/bin/activate && source scripts/load_env.sh && make task-start TASK=T-2026-08-30-tooling-fixes-five
[task-start] 分岐を作成: feat/tooling-fixes-five（起点 origin/phase0）
[task-start] .sync-pause を作成
OK   T-2026-08-30-tooling-fixes-five     1 task(s), 0 failed

$ make task-validate TASK=T-2026-08-30-tooling-fixes-five ; echo $?
OK / 1 task(s), 0 failed / 0

$ make task-preflight TASK=T-2026-08-30-tooling-fixes-five
RESULT: 5 PASS / 0 WARN / 4 SKIP / 0 FAIL   (EXIT=0)
SKIP: P2 cuda_ext_loaded・P3 deterministic_flags（plan.env.preflight に記載なし）
      P4 prereg_committed・P5 frozen_source_hash（kind=impl のため対象外）
```

## 2. Step 1-1 参照の解決

```
$ git --no-pager log -1 --format=%h -- context/conventions.md      -> a8c07e81   （契約と一致）
$ runindex の行数（ヘッダ除く）  index 1250 / experiments 277 / verdicts 1486   （契約と一致）
```

置換は不要だった。

## 3. Step 1-3 回帰の分母（修正前の L1）

```
$ python tools/validate_task.py --level l1
104 task(s), 1 failed        exit=1
  OK   103
  FAIL   1   T-2026-08-22-philip-hub-foundation（result.yaml が版 1 の様式。修正前から失敗）
  SKIP   1   inbox.d: spec.yaml なし
```

## 4. Step 1-4 preflight で使われている名前

```
venv_active              104 件
deterministic_flags        5 件
gpu_free                   1 件   <- 検査器が知らない
cuda_ext_loaded            1 件
gpu_free を使う契約: T-2026-08-29-k1-reeval-and-harvest
```

## 5. Step 1-2 五件の再現（修正前）

### F1 禁止領域検査

```
再現: $ touch runindex/__f1_probe.tmp && python tools/check_forbidden.py
      status: fail   violations: ['runindex/__f1_probe.tmp']
正常: $ touch tools/__f1_ok.tmp && python tools/check_forbidden.py
      status: pass   violations: []
```

### F2 preflight の未知名

```
再現: preflight=['venv_active','gpu_free']       -> 適用 ['P1','P6','P7','P8','P9']（gpu_free は無視）
      preflight=['venv_active','zzz_not_a_check'] -> 同上。**FAIL にならない**
      schema: どちらも通過（enum が無い）
正常: preflight=['venv_active','cuda_ext_loaded'] -> P2 が適用される
```

### F3 置換前提の欄

```
再現: denominator.ref='TBD'                    -> 落ちる（pattern 不一致）
      denominator.ref='<resolve_from_runindex>' -> 落ちる
      denominator.ref='exp:?/?/?@?'             -> 落ちる
正常: denominator.ref='exp:baselines/s0/relationdetr@mAP' -> 設置できる
```

### F4 収穫の検証

```
再現: experiments.csv の群 277 のうち n_runs>1 が 206。
      例 _smoke_prior/s0/maskdino_bbox@val は n_runs=3 n_seeds=3 mAP_mean=0.014483654371968963。
      同じ群に seed を 1 つ足せば n_runs・n_seeds・*_mean・*_pstd が必ず変わる。
      → 集約表に「既存行の変更零」を課すと正常な収穫でも必ず失敗する。
正常: run 単位の index.csv は追加のみで成立する。
道具の有無: tools/ に前後比較の道具は無い（verify_runindex.py は内部整合のみ）。
```

### F5 秘匿検出

```
再現: 'WANDB_API_KEY=abcd1234…（先頭 8 桁・以降は伏せる）' -> ['鍵らしい代入（1 行目・値は伏せる）']
      'NOTION_API_KEY: ntn_XXXXXXXX...(伏せ字)'          -> ['鍵らしい代入（1 行目・値は伏せる）']
正常: 'ntn_' + 'A'*30                                   -> ['Notion の内部鍵（…）']
      'MY_API_KEY = ...'                                -> ['鍵らしい代入（…）']
      'ckpt の sha256 は notes.md に記録した'             -> 非検出
```

**G1 通過。** 五件すべてで再現する入力と正常に振る舞う入力を実測した。

## 6. Phase B — 採った方式

| # | 方式 |
|---|---|
| F1 | `contract.allow_write`（接頭辞の配列）を spec に足し、`check_forbidden.py --task` が許可として読む。上限は**経路そのものに当てる** |
| F2 | schema に `enum` を足し、実行直前検査に `P10 preflight_names_known` を足して未知名を FAIL にする。既存契約の `gpu_free` は `P11` として実装した |
| F3 | `ref: "unresolved:…"` + `resolve_by_executor: true` を宣言として許し、`P12 refs_resolved` が `tasks/<id>/resolved.yaml` を要求する |
| F4 | `tools/verify_harvest.py` と `make harvest-verify` を新設。run 単位は追加のみ、集約表は判定列の不変 |
| F5 | 一致した**断片**に伏せ字の目印があれば拾わない。目印は狭く取る |

## 7. Phase B — 対照の出力

### F1

```
陽性（宣言なし + runindex 書き込み）  違反=['runindex/__probe.tmp']  許可=[]
正例（宣言あり + runindex 書き込み）  違反=[]  許可=['runindex/__probe.tmp']
陰性（宣言あり + data 書き込み）      違反=['data/__probe.tmp']  許可=[]
     宣言が拒まれた理由: [{'prefix': 'data/', 'reason': '許可の上限: data/ 配下は宣言しても許可されない'}]
陰性（宣言あり + 既存 run 配下の変更）
     違反=['experiments/audit/l0_hts_acceptance/acceptance_report.json']  許可=[]
```

⚠ 対照の途中で、検査用の `touch`/`unlink` が実在ファイル
`experiments/audit/l0_hts_acceptance/acceptance_report.json` を**削除**した。
`git checkout --` で復元し、要約値 `d9ac7ced89e5c574…` が前契約で記録した値と一致することと、
`git status` に差分が無いことを確認した。以降の対照は**控えを取って書き換え、必ず戻す**方式に変えた。

⚠ 上限の判定に**穴**があった。修正当初は宣言の文字列だけを見ていたため、
短い宣言が網をくぐった。実測:

```
capped("d") = None
grant("data/annotations/x.json", ("d",), frozenset()) = 契約の allow_write d により許可   ← 通ってしまう
```

`grant()` を経路ごとの上限判定に直した。修正後:

```
grant("data/annotations/x.json", ("d",), frozenset()) = None
grant("runindex/index.csv", ("runindex/",), frozenset()) = 契約の allow_write runindex/ により許可
```

`d` `da` `data` `data/` `data/annotations/` の 5 通りを試験で固定した。

### F2

```
['venv_active']                                                    -> P10 PASS
['venv_active', 'gpu_free']                                        -> P10 PASS
['venv_active', 'zzz_not_a_check']                                 -> P10 FAIL
['venv_active','cuda_ext_loaded','deterministic_flags','gpu_free'] -> P10 PASS

$ make task-preflight TASK=T-2026-08-29-k1-reeval-and-harvest
P10 preflight_names_known  PASS 宣言 2 件はすべて実装済み
P11 gpu_free               PASS GPU を占有する compute プロセスは 0 件
RESULT: 7 PASS / 0 WARN / 5 SKIP / 0 FAIL
```

### F3

```
schema:
  陰性 解決済みの参照            -> 設置できる
  正例 宣言つきの置換前提         -> 設置できる
  陽性 宣言なしの TBD            -> 落ちる: 'TBD' is not valid under any of the given schemas
  陽性 宣言なしの unresolved:     -> 落ちる: 'resolve_by_executor' is a required property
  陽性 宣言はあるが形式が不正      -> 落ちる

実行直前検査:
  陽性 解決していない          P12 FAIL 解決前提の参照 1 件（inputs.denominator.ref）に対し resolved.yaml が無い
  陽性 解決先が未解決のまま     P12 FAIL 解決先がまだ未解決のまま: inputs.denominator.ref
  正例 解決済み                P12 PASS 解決前提の参照 1 件がすべて resolved.yaml で解決済み
  陰性 解決前提の参照が無い     P12 SKIP 解決前提の参照は無い
```

仮契約の `exit` はいずれも 1 だが、これは `P8 contract_valid`（仮契約に SPEC.md が無い）
によるもので P12 とは無関係である。実測で確かめた。

### F4

```
陰性 同一入力の対                -> pass=True  追加0 削除0 既存変更0
陽性 判定列を 1 箇所変えた集約表   -> pass=False 判定列が変わった行=1
     ['hand2det_dev/.../hand2det_1ep_4ch_all@val','detection_max'] verdict_pstd: 'undecidable' -> 'significant'
陰性 集計値の列だけ変えた集約表    -> pass=True  既存変更1 判定列0
陽性 集約表から 1 行削除         -> pass=False 削除1
陰性 run 単位に 1 行追加のみ     -> pass=True  追加1
陽性 run 単位の既存行を変更      -> pass=False 既存変更1

判定列の見分け（experiments.csv の実列）: 全 631 列中 106 件が判定列。
  例: n_seeds, verdict_metric, verdict_10_1, verdict_10_1_sstd, verdict_10_1_agree,
      verdict_10_1_reason, delta_same_sign_AP_common, delta_n_seeds_AP_common
  判定列でない例: experiment_id, group, step, description, split, eval_recipe_id

$ make harvest-verify
PASS runindex/index.csv        1250 -> 1250 行
PASS runindex/experiments.csv   277 ->  277 行
PASS runindex/verdicts.csv     1486 -> 1486 行
PASS runindex/per_class.csv    9027 -> 9027 行
RESULT: PASS
```

**runindex には一切書いていない。** 対照は表を読み込んでから作業領域の写しを比較関数へ渡した。

### F5

```
陰性 伏せ字(省略記号)   'WANDB_API_KEY=abcd1234…（先頭 8 桁）'        -> 非検出
陰性 伏せ字(三点リーダ)  'NOTION_API_KEY: ntn_synthetic...(伏せ字)'   -> 非検出
陰性 要約値の伏せ字     'report_sha256: 2f648079f286a825…'          -> 非検出
陰性 無害な文          'ckpt の sha256 は notes.md に記録した'        -> 非検出
陽性 合成の鍵本体       'ntn_'+'S'*30                                -> 検出
陽性 合成の鍵本体       'secret_'+'S'*25                             -> 検出
陽性 名前つきの値       "MY_API_KEY = 'zzzz…'"                       -> 検出
陽性 伏せ字と本物が同じ行 "old=abcd…  MY_TOKEN='yyyy…'"               -> 検出
出力に値の断片を含まない: True
```

⚠ 目印を最初は `xxxx` `**` まで広く取ったため、**既存の試験を 1 件壊した**
（`NOTION_API_KEY=` + `x`*40 という合成鍵を伏せ字と誤認した）。目印を
省略記号と明示的な「伏せ字」語だけに絞り込んで解消した。**対照に使う値はすべて合成値である。**

## 8. Phase C — 回帰

```
$ diff l1_before.txt l1_after.txt
（差分なし。104 task(s), 1 failed / OK 103 / FAIL 1 / SKIP 1 / exit 1）

$ python -m pytest tests/ -q
修正前: 6 failed, 471 passed
修正後: 6 failed, 509 passed        （509 - 471 = 38 = 本契約で足した試験の数）
```

**失敗 6 件は修正前と完全に同一で、いずれも本契約の五件とは無関係である。**

```
tests/test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics
tests/test_fetch_task.py::test_rejects_unknown_file_name
tests/test_research_logger.py::test_log_run_idempotent
tests/test_research_logger.py::test_run_logging_invokes_log_run_on_finally
tests/test_research_logger.py::test_run_logging_no_double_post_on_normal_exit
tests/test_research_logger.py::test_run_logging_swallows_exception_in_user_block
```

修正前の状態で同じ 6 件が落ちることは、修正を stash して実測した。

```
$ make docs-check    -> [docs-check] 対象 42 文書 / Makefile のターゲット 34 件 / 食い違いなし
$ make agent-check   -> {"errors": [], "pager_violations": [], "status": "pass", "targets": 111, "violations": []}
```

## 9. Step 3-3 変更範囲

```
$ git status --porcelain experiments/ data/ runindex/
（空。変更なし）

$ git status --porcelain
 M Makefile
 M tasks/README.md
 M tasks/_schema/spec.schema.json
 M tasks/_templates/analysis/spec.yaml
 M tasks/_templates/exp/spec.yaml
 M tasks/_templates/impl/spec.yaml
 M tools/check_forbidden.py
 M tools/preflight_task.py
 M tools/report_task.py
?? tasks/T-2026-08-30-tooling-fixes-five/
?? tests/test_tooling_fixes_five.py
?? tools/verify_harvest.py
```

同じ絞り込みを `tools/` と `tasks/` に当てると 10 行出る。**絞り込みは働いている。**

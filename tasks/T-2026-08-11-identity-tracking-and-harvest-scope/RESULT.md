# RESULT — T-2026-08-11-identity-tracking-and-harvest-scope

**task_id:** `T-2026-08-11-identity-tracking-and-harvest-scope`
**kind:** `impl`
**実行ホスト:** `bengio`（分岐 `feat/identity-and-tracking`、基点 `origin/phase0` = `63edc44`）
**実行日:** 2026-08-09

---

## 1. 解決された参照

### 1.1 `contract.inject_verbatim`

`context/conventions.md`（実測 rev `d422b08`）の該当アンカーの**原文**。要約していない。

#### `conventions#prohibitions`

    ## prohibitions

    | id | 禁止事項 |
    |---|---|
    | `no_split_redefine` | split を再定義しない |
    | `no_raw_write` | `data/raw` `data/external` に書き込まない |
    | `no_frozen_change` | 凍結源を変更しない |
    | `no_estimated_values` | 未測定の値を書かない。未測定は UNKNOWN |
    | `no_runindex_hand_edit` | `runindex/` を手で編集しない |

#### `conventions#naming`

    ## naming

    実験フォルダは手作業で命名せず、`ExperimentManager` が次の規則で自動採番する。

        {step}_{seq:03d}_{description}_seed{seed}

    - `step`: `s0`〜`s9`、または `a1`〜`a7`
    - `seq`: 同一 category と step 内の3桁ゼロ埋め連番
    - `description`: 実験内容の短い説明
    - `seed`: 乱数シード。既定42

    転記元: `README.md` の「命名規則」。

（本アンカーは文書末尾のため、切り出し範囲に「変更履歴」表が続く。規約本文は上記まで。）

#### `conventions#env_p0`

    ## env_p0

    学習・評価スクリプトを起動する前に、必ず対象の venv を activate すること。
    activate を省略すると CUDA 拡張が読み込まれず、無言で CPU 実装へフォールバックし、
    数値が変わったまま完走する。

        source .venv-relation-detr/bin/activate   # 検出系
        source .venv/bin/activate                 # 解析・工程系

    拡張のロード確認をログに残すこと。

### 1.2 継承された `sigma_policy`

`spec.yaml` が `inputs.sigma_policy` を省略しているため `conventions#sigma` の既定値を継承した。
本 task は `kind: impl` で σ 判定を行わないが、記録のため残す。

    series: pstd
    sigma_source: paired_delta
    delta_sigma_source: paired

### 1.3 解決しなかった参照

| 参照 | 状態 |
|---|---|
| `inputs.denominator.ref` | `spec.yaml` に記載なし。解決対象外 |
| `inputs.frozen_source.ref` | `spec.yaml` に記載なし。解決対象外（P5 も `kind=impl` で SKIP） |

### 1.4 `conventions_rev` の実測と置換

起票時の値は `1201f4f`。実測値は `d422b08`。SPEC Task 7 Step 1 の手順に従い置換した。

置換前に差分を確認した。`1201f4f..d422b08` は `+10 / -0` の追記のみで、変更箇所は
`frozen_source` 節（「検査の適用範囲」の新設）とファイル末尾の変更履歴表である。
**引用対象 3 アンカーの規約本文は無変更**であることをアンカー単位の比較で確認した。

| アンカー | 新旧比較 |
|---|---|
| `prohibitions` | バイト一致 |
| `env_p0` | バイト一致 |
| `naming` | 差異あり。ただし末尾の変更履歴表に 1 行増えただけで、命名規約の本文は無変更 |

---

## 2. 検証の結果

### 2.1 `make task-validate`

| 時点 | 結果 |
|---|---|
| 開始時 | `exit 0`。WARN 3 件（L2-6 conventions 変更 / L2-8 index 749→751 / L2-8 experiments 206→207） |
| 完了時 | `exit 0`。WARN 2 件（L2-6 は `conventions_rev` の実測置換により解消） |

WARN はユーザーへ提示し、続行の承認を得てから実行に入った。残る L2-8 2 件は本契約が
`inputs.denominator` を持たず件数を主張の分母に使わないため、判定に影響しない。

### 2.2 `make task-preflight`

初回は `P1 venv_active` が FAIL した（`VIRTUAL_ENV` 未設定）。SPEC §0 が
`source .venv/bin/activate` を前提として明記しているため activate して再実行し `exit 0`。

    P1 venv_active            PASS
    P2 cuda_ext_loaded        SKIP  plan.env.preflight に記載なし
    P3 deterministic_flags    SKIP  plan.env.preflight に記載なし
    P4 prereg_committed       SKIP  kind=impl のため対象外
    P5 frozen_source_hash     SKIP  kind=impl のため対象外
    P6 decisions_answered     PASS  decisions_required は空
    P7 destination_writable   PASS
    P8 contract_valid         PASS
    RESULT: 4 PASS / 4 SKIP / 0 FAIL

**SKIP された 4 項目は「合格」ではなく「実行されなかった」。** 特に P2 / P3 は
`plan.env.preflight` に `venv_active` しか書かれていないため実行されていない。

---

## 3. 実測

### 3.1 識別子の解決順（実装から確認）

`src/egosurgery/utils/server_name.py:25 resolve_server_name()` の実測。

| 順 | 経路 | 実装位置 |
|---|---|---|
| 1 | 環境変数 `SERVERNAME` | `server_name.py:37` |
| 2 | 環境変数 `EGOSURGERY_SERVER_NAME` | `server_name.py:37`（同一式の `or` 右辺） |
| 3 | `cfg.logging.server_name` | `server_name.py:41-52` |
| 4 | `socket.gethostname().split(".")[0].lower()` | `server_name.py:54` |

**先行調査の記述（環境変数 2 つ、設定の項目、最後に system の呼び出し）と一致した。食い違いはない。**

証跡へ書く側は `experiment_manager.py:156-157` で、`resolve_server_name(cfg)` の戻り値を
`server.txt` へ書く。索引側で正規化するのは `harvest_runindex.py:811 normalize_host()` で、
`HOST_ALIASES` に無い値と `aolab` を `host=null` に落とす（推測しない設計）。

### 3.2 索引の host 分布（751 行）

| `host` | 件数 |  | `host_raw` | 件数 |
|---|---|---|---|---|
| lecun | 467 |  | lecun | 467 |
| efros | 206 |  | efros | 206 |
| (空) | 41 |  | (空) | 31 |
| philip | 31 |  | philip | 31 |
| andrew | 3 |  | aolab | 10 |
| bengio | 3 |  | andrew | 3 |
|  |  |  | bengio | 3 |

**`host_raw=aolab` かつ `host` が空の行は 10 件。** 先行調査の「生の値が 10 行、正規化後は全て空」と一致した。

### 3.3 環境変数を書く場所と、なぜ非対話シェルでも読めるのか

ログインシェルは `/usr/bin/zsh`（`getent passwd` で確認）。`env -i` で親からの継承を断って測定した。

| 起動形態 | 適用前 | 適用後 | 読まれる利用者ファイル |
|---|---|---|---|
| `zsh -c`（非対話・非ログイン） | bengio | bengio | `~/.zshenv` |
| `zsh -ic`（対話） | bengio | bengio | `~/.zshenv` |
| `zsh -lc`（ログイン） | bengio | bengio | `~/.zshenv` |
| `bash -lc`（ログイン） | bengio | bengio | `~/.profile` |
| `bash -ic`（対話） | 未設定 | bengio | `~/.bashrc`（本 task で追記） |
| `bash -c`（非対話・非ログイン） | 未設定 | 未設定 | **なし（既知の限界）** |

**主経路は `~/.zshenv` である。** zsh は `~/.zshenv` を対話・非対話・ログイン・スクリプトの
**全形態で無条件に読む**。bash にはこれに相当する利用者ファイルが存在しない
（`~/.bashrc` は非対話で早期 return、`~/.profile` はログインシェル限定）。学習が対話シェルから
起動されるとは限らないため、全形態を覆える `~/.zshenv` を主経路に据えた。

**既知の限界。** `env -i bash -c` は**どの利用者ファイルでも覆えない**。`BASH_ENV` は
それ自体が環境変数のため clean env からは設定できない（鶏卵問題）。覆うなら
`/etc/environment`（PAM 経由・要 root・システム全体）か起動側での明示 export が要る。
本スクリプトは root 権限を要求しないため対象外とし、実行のたびに表示して黙らせない設計にした。

なお適用前の時点で `~/.zshenv:16` と `~/.profile:29` に `export SERVERNAME=bengio` が
手で書かれていた（`~/.zshrc:2` にも）。導入スクリプトはファイル単位で冪等に判定するため、
この 2 ファイルは skip し、`~/.bashrc` にのみ標識付きブロックを追記した。

既存の永続化の仕組みが無いことは 4 通りの探し方で確認した（rc ファイル名での検索 /
永続化を示す語での検索 / `SERVERNAME=` 書き込み箇所の検索 / 常駐の仕組みの調査）。
`setup_host_autosync.sh` は `SERVERNAME` を**読むだけで永続化しない**。

### 3.4 G1 ゲート — 設定の有無で証跡の値が変わる

解決順の再現ではなく、**実際に証跡へ書く経路**（`ExperimentManager.setup()` →
`server.txt`）を一時ディレクトリで呼んで測った。`experiments/` には触れていない。

| 条件 | `server.txt` の中身 |
|---|---|
| `SERVERNAME` / `EGOSURGERY_SERVER_NAME` とも未設定 | `bengio` |
| `SERVERNAME=probe-host` | `probe-host` |
| `EGOSURGERY_SERVER_NAME=legacy-host` | `legacy-host` |

**G1 PASS。** なお未設定時に `bengio` になるのは、本ホストの `hostname` が `Bengio` で
小文字化すると論理名と一致するためである。**本ホストでは注入の効果が値として現れない。**
注入が効くのは `hostname` が `aolab` を返す ilya / philip である。

誤入力の拒否は 9 通りで確認し、すべて拒否された（`Bengio` / `a` / `b engio` /
`bengio;rm -rf /` / 空 / 21 文字 / `-bengio` / `bengio-` / `ben_gio`）。

### 3.5 外部記録の識別子を取得する経路

`src/egosurgery/utils/tracking.py` の `_run`（`wandb.init()` の戻り値）から
`id` / `url` / `project` / `entity` / `name` を読む。新設した
`record_run_identity(exp_dir)` が run ディレクトリ直下へ `wandb_run.json` を書く。

| 要件 | 実装 |
|---|---|
| 有効なときのみ書く | `_run is None` なら `False` を返して**何も書かない**。空ファイルも作らない |
| 資格情報を書かない | 読むのは上記 5 属性のみ。`WANDB_API_KEY` には触れない |
| 失敗しても学習を止めない | 全体を `try/except` で囲み、警告を出して `False` を返す |
| 既存の証跡の様式に合わせる | run 直下のフラットファイル。複数フィールドのため JSON |

`init()` に任意引数 `exp_dir` を足し、run 開始に成功したときだけ自動で書く。
既存の呼び出し元 7 箇所以上は引数省略で挙動が変わらない。

試験は `tests/test_tracking_ids.py` の 6 件。外部サービスへは接続していない。
**空振りでないことを陽性対照で確認した**（実装を変更前へ戻すと 6 件すべて失敗、戻すと 6 件 pass）。

### 3.6 G2 ゲート — 索引の指紋の比較結果

| 項目 | 値 |
|---|---|
| 行数 | 751 → **751**（不変） |
| 列数 | 89 → **91**（`wandb_run_id` / `wandb_run_url` を末尾に追加） |
| `ledger_key` 集合 | 同一 |
| 既存 89 列の指紋 | `7ab8e8b9bfe0ccd7` → `7ab8e8b9bfe0ccd7`（**一致**） |
| セル単位の直接比較 | 既存列で値が変わったセル **0 件** |
| 新しい列が空でない行 | **0 / 751**（遡及していないので正しい） |

**G2 PASS。** 索引は `git checkout` で復元し、md5 が変更前と全一致することを確認した。
`runindex/` は記録していない。

**ただし SPEC が指定した G2 の検査コマンドには欠陥がある。** §5 の逸脱に記す。

### 3.7 自ホストで無視設定済みのディレクトリは何件あったか

**0 件である。** 別ホストの 37 件は持ち込んでいない。

| 測ったもの | 実測値 |
|---|---|
| 収穫器が走査する run ディレクトリ | 722 件 |
| うち `git check-ignore --stdin` に該当 | **0 件** |
| うち `git ls-files --error-unmatch` が失敗（未追跡） | **0 件** |
| `experiments/` 配下の無視エントリ総数 | 936 件 |
| うち `metrics.json` を含むもの | **0 件** |

936 件はすべて追跡済み run 配下の checkpoint / logs / predictions / wandb 等であり、
`metrics.json` を含まないため走査対象にならない。

仕組みとしての非一致はコードで確認した。収穫器は
`EXPERIMENTS.rglob("metrics.json")` の親を run とし、無視設定への照会を一切持たない
（3 通りの探し方で該当 0 件）。**したがって仕組み上は無関係だが、本ホストでは観測される
乖離が 0 件である。**

**G3 は `on_fail: ask` のためユーザーへ提示し、PASS として続行する判断を得た。**

### 3.8 起票した未解決事項

| 項目 | 値 |
|---|---|
| 番号 | **B-38** |
| slug | **`BL-ignore-does-not-protect-index`** |
| 見出し | 版管理の無視設定は索引を保護しない。収穫器はファイルシステムを直接走査し、無視設定を参照しない |
| 対処案 | 3 案を挙げ、**選んでいない**（走査時に無視設定を参照する / 除外規約へ移す / 正本ホストの条件で担保する） |

採番は全 remote ref 49 本とローカル HEAD を横断して最大 `B-37` を確認したうえで決めた。
`open_questions.md` の `BL-` 行数は 36 → **37**。

**同一の根本原因を持つ `B-36` が既存である。** 重複起票を避けるため、B-36 が扱う
「ホスト間で索引の行数が変わる」側面とは別に、本エントリは「無視設定が索引を保護しない」
側面を扱うものとして範囲を分け、相互参照を本文に明記した。§5 の逸脱に記す。

### 3.9 抽出物の件数（追跡済みと未追跡を分けて）

| 区分 | 件数 |
|---|---|
| `docs/sessions/digest/` のファイル総数 | 6 |
| **追跡済み** | **6** |
| **未追跡** | **0** |
| 無視設定に該当 | 0 |
| 容量 | 48KB |

**未追跡が 0 件のため、記録すべき新規の抽出物は無かった。** SPEC が想定した
「生成のたびに作業ツリーが汚れる」状態は、本ホストの現時点では発生していない。
方針そのものは `docs/sessions/README.md` と `tasks/README.md` に文書化した。

秘匿の検査は 4 通り行い、すべて 0 件だった（SPEC 指定の正規表現 / 既知の鍵接頭辞 /
32 文字以上の連続英数 / 大文字小文字を区別しない版）。**検査器が動作することを
陽性対照で確認した**（仕込んだカナリアに反応することを確認してから 0 件を信じた）。

---

## 4. 完了判定

| # | 判定 | 期待 | 実測 | |
|---|---|---|---|---|
| 1 | 解決順を実装から確認 | 記録あり | §3.1 に記録。先行調査と一致 | OK |
| 2 | 設定の有無で値が変わる | 変わる | `bengio` / `probe-host` / `legacy-host` | OK |
| 3 | 誤入力を拒む | すべて拒否 | 9 通りすべて拒否 | OK |
| 4 | 非対話シェルでも読める | 読める | `zsh -c` で `bengio`。`bash -c` は既知の限界 | OK |
| 5 | 識別子を書く経路がある | 実装済み | `tracking.py:71 record_run_identity()` | OK |
| 6 | 無効時は何も書かない | pass | `test_tracking_ids.py` 6 件 pass | OK |
| 7 | 索引に列が増えた | 追加された | `wandb_run_id` / `wandb_run_url` | OK |
| 8 | 既存の値が不変 | 指紋が一致 | `7ab8e8b9bfe0ccd7` 一致。変化セル 0 件 | OK |
| 9 | 新しい列は全行で空 | 空 | 0 / 751 行 | OK |
| 10 | 収穫の範囲が起票された | 前より増 | `BL-` 行 36 → 37 | OK |
| 11 | 表の列が揃っている | 種類が 1 | 区切り数 `{6}`、40 行 | OK |
| 12 | 抽出物の方針が文書化 | 1 件 | `docs/sessions/README.md:39` | OK |
| 13 | 索引を記録していない | 0 | `runindex/` の変更 0 件 | OK |
| 14 | 契約検証が通る | exit 0 | `exit 0`（WARN 2） | OK |
| 15 | 実行前検査が通る | exit 0 | `exit 0`（4 PASS / 4 SKIP） | OK |
| 16 | 試験が不変 | 開始前と同じ | 開始前 5 failed / 252 passed → 5 failed / 258 passed。**新規失敗 0** | OK |
| 17 | 禁止領域が無変更 | 出力なし | 出力なし | OK |

判定 16 の失敗 5 件は本 task 開始前から失敗しているもので、内訳は
`test_engines.py::test_mmdet_trainer_eval_recipe_in_metrics` と
`test_research_logger.py` の 4 件である。増加分の 6 pass は本 task が追加した試験。

---

## 5. deviations

**空にしてはならない項目である。逸脱と、自分で判断した箇所を挙げる。**

### 5.1 SPEC の検査コマンドの欠陥（3 件）

起票者の申し送り（検査コマンドが検証対象を検証できていない誤りが 8 task 連続）に該当する
誤りを 3 件見つけた。いずれも指示どおり実行すると誤った結論に至る。

| # | 箇所 | 欠陥 | 実行者の対処 |
|---|---|---|---|
| 1 | Task 4 Step 3（G2 の指紋比較） | 新列を `any(k in c.lower() for k in ("wandb","tracking","run_url","run_id"))` で検出するが、**`run_id` は既存列である**。変更後の指紋だけがこの既存列を除外するため、何も壊れていなくても指紋が一致しない | 新旧ヘッダの**集合差**で新列を求め、両側から同じ列集合を除外して比較した。加えてセル単位の直接比較も行った。SPEC のコマンドをそのまま実行した結果（不一致）も記録した |
| 2 | Task 5 Step 2（採番の衝突回避） | `"$ref:tools/..."` の `:t` を **zsh が tail 修飾子として解釈**し、`$ref` を basename に潰す。ユーザーのログインシェルは zsh のため**黙って空を返す** | `"${ref}:tools/..."` と波括弧で囲んで再実行し、全 remote ref 49 本を走査して最大 `B-37` を得た |
| 3 | Task 6 Step 3（秘匿の検査） | 正規表現が**大文字小文字を区別する**ため、小文字の `password =` を取りこぼす。仕込んだカナリア 3 行のうち 2 行しか捕まえなかった | `-i` を付けた版を含む 4 通りで検査し、すべて 0 件であることを確認した |

### 5.2 自分で判断した箇所

| # | 判断 | 理由 |
|---|---|---|
| 1 | B-38 を B-36 の重複ではなく**側面を分けた別エントリ**として起票した | 同一の根本原因を持つ B-36 が既存だった。判定 10 が `BL-` 行数の増加を求める一方、単純な重複は避けるべきと判断し、B-36 が扱わない「無視設定が索引を保護しない」側面に範囲を絞り、相互参照を本文へ明記した |
| 2 | 導入スクリプトの書き込み先を `~/.zshenv` / `~/.profile` / `~/.bashrc` の 3 つとした | SPEC は「実測してから決める」とのみ指示。6 形態の測定マトリクスにもとづき、全形態を覆う `~/.zshenv` を主経路、bash 経路を補助と位置づけた |
| 3 | 冪等性を**ファイル単位**で判定した（全体の no-op ではなく） | 要件 3「既に同じ値なら何もしない」と要件 2「両方で有効になる場所へ書く」を同時に満たすため。本ホストでは `~/.zshenv` と `~/.profile` を skip し `~/.bashrc` のみ追記した |
| 4 | `record_run_identity()` を新設し `init()` に任意引数を足す形にした | SPEC は「`tracking.py`（または実測で特定した箇所）」とのみ指示。呼び出し元が 7 箇所以上に散っており、各所を書き換えると変更面が広がるため |
| 5 | 新列を `SCALAR_COLUMNS` の末尾に置いた（ヘッダ全体の末尾ではない） | 要件「列の順序は末尾に足す」と既存様式（`task_id` も `SCALAR_COLUMNS` へ追加）の両立。既存列の相対順序は変えていない |
| 6 | `provenance` 辞書には触れなかった | `host` と同様に `provenance` へ足すのが自然に見えたが、全行の既存値が変わり G2 の指紋が壊れる。要件「既存の行の他の列を変えない」を優先した |

### 5.3 手順として実施したもの（逸脱ではない）

| # | 内容 |
|---|---|
| 1 | `conventions_rev` を `1201f4f` から実測値 `d422b08` へ置換した。SPEC Task 7 Step 1 が「これは逸脱ではなく手順である」と明記している |
| 2 | プリフライト初回の `P1 venv_active` FAIL に対し `source .venv/bin/activate` して再実行した。SPEC §0 の前提に含まれる |

### 5.4 実装の不具合と、それを見つけた経緯

| # | 内容 |
|---|---|
| 1 | 導入スクリプトの `$(...)` を全角 `）` で閉じており構文エラーになっていた。`bash -n` で検出し修正した |
| 2 | 適用後の確認が `bash -ic` で NG になっていた。原因は Ubuntu の sudo 案内文が stdout に混ざることで、**機能は正しいのに検査だけが落ちていた**。センチネルで値を囲って抽出する方式へ変更した |
| 3 | `--verify` が空値を返していた。`probe_shell` の定義が `--verify` の早期 exit より後にあり未定義だった。**適用経路しか試していなかったため、契約の完了判定（判定 4）を実行するまで露見しなかった** |

### 5.5 SPEC の前提と実測が食い違った点

| # | 前提 | 実測 |
|---|---|---|
| 1 | 「収穫が無視設定と一致しない。別ホストで 37 件」 | **自ホストでは 0 件。** SPEC の想定外表が先回りしているとおり、これも実測結果として記録した |
| 2 | 「抽出物は生成のたびに作業ツリーを汚し、自動統合を妨げる」 | **本ホストでは未追跡 0 件。** 6 件すべて追跡済みで、記録すべき新規の抽出物は無かった |
| 3 | 「常駐スクリプトへの検索」 | `crontab` は**そもそも導入されていない**（exit 127）。常駐は `keeper.sh`（PID 773、`~/.zshrc` から `nohup` 起動）。「`crontab -l` が空＝該当なし」と読むのは誤りだった |

---

## 6. 申し送り

### 6.1 遡っての対応づけが別途必要である

**本 task は遡っての対応づけを行っていない。** 外部記録の識別子は今後の run からのみ
証跡へ書かれ、索引の `wandb_run_id` / `wandb_run_url` は既存 751 行すべてで空である。

過去の run と W&B run を結ぶには別の契約が要る。着手する場合の前提を挙げる。

- 外部サービスへの問い合わせが要る（本 task では禁止されていた）
- 対応づけの根拠をどこに置くか未定。run 名の一致だけでは足りない可能性がある
  （同名 run が複数の W&B project に存在しうる）
- 遡って書いた識別子と、実行時に書かれた識別子を区別できるようにするか未定

### 6.2 索引の正本生成

本 task は索引を記録していない。`wandb_run_id` / `wandb_run_url` の 2 列は、
**正本ホストの条件を満たす機会に生成して記録する**必要がある。B-36 と B-38 が示すとおり、
どのホストを正本とするかは未定である。

### 6.3 `bash -c` 非対話の残存ギャップ

`env -i bash -c` は利用者ファイルでは覆えない。現状これが問題になる経路は確認していない
（`crontab` 未導入、systemd の該当ユニットなし、常駐は zsh 起動の `keeper.sh`）。
将来 cron や systemd から学習を起動するなら、`/etc/environment` か起動側の明示 export が要る。

### 6.4 PR #58 は `tasks/inbox.md` で衝突している（未解消）

本 task の実行中に `origin/phase0` が 7 commit 進んだ（別ホストが PR #56 と #57 を統合した。
SPEC §0 が予告していた並行作業にあたる）。その結果 PR #58 は `mergeable: CONFLICTING` である。

| 項目 | 実測 |
|---|---|
| 衝突するファイル | **`tasks/inbox.md` の 1 件のみ**（`git merge-tree` で確認） |
| 衝突の性質 | 双方が末尾へ追記しただけの追記どうしの衝突 |
| 起票時の `origin/phase0` | `63edc44` |
| 現在の `origin/phase0` | `c8dc178` |

**解消していない。** 禁止事項 9「統合する」に該当するため、実行者の判断で
`origin/phase0` を取り込むことはしなかった。

同型の衝突は既に `e050aa9 merge: keep inbox entries from both contracts` で
「双方の行を残す」形で解消された前例がある。本 PR も同じ扱いで解消できる見込みだが、
判断は統合を行う者に委ねる。

### 6.5 B-36 と B-38 は同時に検討すること

根本原因が同一のため、片方だけ直しても他方は残る。対処案もそれぞれ 3 案あり重なっている。

---

## 7. 生成物

| 種別 | パス |
|---|---|
| 新規 | `scripts/sync/setup_host_servername.sh` |
| 新規 | `tests/test_tracking_ids.py` |
| 変更 | `src/egosurgery/utils/tracking.py` |
| 変更 | `tools/harvest_runindex.py`（新列 2 つ + B-38） |
| 変更 | `README.md`（運用手順） |
| 変更 | `docs/sessions/README.md` / `tasks/README.md`（抽出物の方針） |
| 変更 | `context/auto/open_questions.md` / `context/auto/STATE.md`（`make context` による生成） |
| **未変更** | `runindex/` / `experiments/` / `transfer/` / `data/splits/` / `context/conventions.md` |

### commit

    a3027a0  fix(sync): define probe_shell before the --verify early exit
    fd9aa1b  docs(sessions): settle the tracking policy for conversation digests
    7d4d82c  docs(runindex): file B-38 on ignore settings not protecting the index
    3977a02  feat(tracking): link W&B runs to evidence and the index
    af8e184  feat(sync): inject logical SERVERNAME per host

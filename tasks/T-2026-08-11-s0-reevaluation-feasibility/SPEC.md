# S0 検出器比較の再評価が学習なしで可能かを測る

**task_id:** `T-2026-08-11-s0-reevaluation-feasibility`  **kind:** `analysis`
**depends_on:** `T-2026-08-11-split-and-recipe-audit`
**実行ホスト:** `lecun`

## Goal

前 task で、S0 の検出器比較表が **6 種類の `eval_recipe_id` に跨り、`score_thr` が
`1e-08` と `0.0` の 2 系統に分かれている**ことが判明した。上位 7 検出器の mAP は
0.6973〜0.7268 に固まっており、**その幅が検出器の実力差か評価条件の差かを分離できない。**

取りうる道は 3 つある。

1. 同一条件で再評価して表を作り直す
2. 条件差を明記して表を載せる
3. 表を落とし、検出器の選定根拠を別のものに差し替える

**この三択を決めるための材料を測る。** 読み取りのみ。学習も評価も行わない。GPU も使わない。

**「再評価が可能か」は、重みが残っているかだけでは決まらない。** 生の予測が保存されて
いれば重み無しでも採点し直せる場合があり、逆に重みがあっても後処理の設定を差し替える
経路が無ければ再評価できない。**両方を測る。**

さらに、**系統差の中身がまだ開かれていない。** 6 系統の差が実は無害なキーだけで
生じているなら、再評価そのものが不要になる。**先にそこを開く。**

## 0. 前提と禁止事項

    cd "$(git rev-parse --show-toplevel)"
    git fetch origin
    git checkout -b feat/s0-reevaluation-feasibility origin/phase0
    touch .sync-pause
    source .venv/bin/activate
    source scripts/load_env.sh

| # | 禁止 |
|---|---|
| 1 | `runindex/**` `context/auto/**` を手で編集する（生成は可） |
| 2 | `experiments/**` `transfer/**` `data/**` を変更・削除する（読み取りのみ） |
| 3 | `tools/harvest_runindex.py` `tools/build_context.py` を変更する |
| 4 | `context/conventions.md` を変更する |
| 5 | 学習・評価コードを変更する（`src/**` `scripts/**` `configs/**`） |
| 6 | 資格情報の値を出力・記録する |
| 7 | 未測定の値を書く（未測定は `UNKNOWN`） |
| 8 | **GPU を使う。推論も評価も本 task では行わない** |
| 9 | 統合する。自動統合を有効化する |

書き込み先は `tasks/T-2026-08-11-s0-reevaluation-feasibility/` 配下と
`tasks/inbox.d/T-2026-08-11-s0-reevaluation-feasibility.md` に限る。
以下 `AUD` を `tasks/T-2026-08-11-s0-reevaluation-feasibility/audit` の意味で使う。

`conventions_rev` には前 task の実測値 `d422b08` を入れてある。**Task 1 で現在値を
確認し、変わっていれば置換すること。これは逸脱ではなく手順である。**
常駐処理による統合は**実行者の逸脱ではない。事実として記録する。**

### 起票者からの申し送り

**前 task で起票者は 4 件の欠陥を出した。うち 1 件は致命的だった。**

`Path.rglob` で画像を数える指示を書いたが、動画ディレクトリは symlink であり
`rglob` はこれを辿らない。**指示どおり実行すると画像 0 枚・重複 0 件が返り、
「分割は健全」と誤って結論するところだった。** 実行者が総件数の照合で気づき、
`find -L` と `os.walk(followlinks=True)` で測り直したことで救われた。

**本 task はまさにその同じ経路（ディスク上のファイル探索）を主対象とする。**
同型の誤りが起きれば「重みが残っていない」と誤って結論する。**そちらの誤りの方が
被害が大きい。** 実際には残っているのに、再学習を選ばせてしまう。

もう 1 件は、ファイルの不在を `ls` で出すだけにして、**不在が何を意味するかを
問わなかった**こと。それが核心に直結していた。

| # | 注意 |
|---|---|
| 1 | **ファイル探索は必ず symlink を辿る方法で行う。** 辿れることを既知の実在物で確かめる |
| 2 | 件数が 0 のとき、別の探し方でも 0 になることを直接確認で裏づける |
| 3 | **不在を見つけたら、その不在が何を意味するかまで追う。** `ls` して終わらせない |
| 4 | 仕組みの挙動は実装を読んでから信じる。食い違えば実装に従い記録する |
| 5 | 対象の一覧そのものが正しいかを確かめる。母集団が縮んでも通る検査を書かない |
| 6 | 差分の検出は集合差で求める。特定のキーだけを見て差の全体と呼ばない |
| 7 | 記録を作る流れに表示用の切り詰めを混ぜない |
| 8 | 変数の直後に記号が続く場合は波括弧で囲む。実行シェルは bash ではない |

---

# Phase A — 比較表の対象一覧を確定する

## Task 1: 何を比べていた表なのかを確定する（G1）

**Files:** Create `AUD/`

- [ ] **Step 1: 環境と現在値を確認する**

        mkdir -p tasks/T-2026-08-11-s0-reevaluation-feasibility/audit
        pwd; git branch --show-current; ls -la .sync-pause; which python
        git log -1 --format=%h -- context/conventions.md
        git log -1 --format='%h %cI' -- runindex/

  `conventions.md` の値が `d422b08` と異なれば `spec.yaml` を置換する。
  runindex の commit は `spec.yaml` の `created_from.runindex_commit` の
  `UNKNOWN` を置き換える。

- [ ] **Step 2: 索引側から対象一覧を作る**

  前 task では `baselines/s0/maskdino_bbox@val` と `varifocanet_bbox@val` が
  `experiments.csv` に見つからず `UNKNOWN` のままだった。**この 2 つの所在も確定する。**

        python - <<'PY'
        import csv, pathlib, collections
        A = "tasks/T-2026-08-11-s0-reevaluation-feasibility/audit"
        exp = list(csv.DictReader(open("runindex/experiments.csv", encoding="utf-8")))
        s0 = [r for r in exp if r.get("group") == "baselines" and "s0" in (r.get("step") or "")]
        print("baselines かつ step に s0 を含む実験:", len(s0))
        for r in sorted(s0, key=lambda x: x["experiment_id"]):
            print(" ", r["experiment_id"], "n_runs", r.get("n_runs"),
                  "recipe", r.get("eval_recipe_id"), "split", r.get("split"))
        idx = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
        ids = {r["experiment_id"] for r in s0}
        runs = [r for r in idx if r.get("experiment_id") in ids]
        print("該当 run:", len(runs))
        with open(f"{A}/target_runs.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["experiment_id", "path", "seed",
                                               "excluded", "exclusion_reason"])
            w.writeheader()
            for r in runs:
                w.writerow({k: r.get(k, "") for k in w.fieldnames})
        PY
        wc -l tasks/T-2026-08-11-s0-reevaluation-feasibility/audit/target_runs.csv

  **`step` の値そのものを一度出力してから絞り込むこと。** `s0` を含むという条件が
  想定と違うものを拾う、あるいは落とす可能性がある。

- [ ] **Step 3: 実体側から対象一覧を作り、索引側と突き合わせる**

        find -L experiments/baselines -maxdepth 2 -type d -name "s0_*" | sort \
          > /tmp/s0_dirs.txt
        wc -l /tmp/s0_dirs.txt
        sed -n '1,10p' /tmp/s0_dirs.txt

        python - <<'PY'
        import csv, pathlib
        A = "tasks/T-2026-08-11-s0-reevaluation-feasibility/audit"
        disk = {l.strip() for l in open("/tmp/s0_dirs.txt", encoding="utf-8") if l.strip()}
        idxp = {r["path"] for r in csv.DictReader(open(f"{A}/target_runs.csv", encoding="utf-8"))}
        print("実体側:", len(disk), "索引側:", len(idxp))
        print("実体にのみ:", len(disk - idxp))
        for p in sorted(disk - idxp)[:20]: print("   ", p)
        print("索引にのみ:", len(idxp - disk))
        for p in sorted(idxp - disk)[:20]: print("   ", p)
        PY

  **集合差を両方向で出すこと。** 一方向では包含関係が確定しない。
  差が非ゼロなら G1 は `ask`。件数と内容を記録し、以降どちらの一覧を使うかを明記して続行する。

- [ ] **Step 4: 検出器名と run の対応を作る**

  比較表の 1 行が何本の run から成るかを確定する。**seed が 3 本揃っていない
  検出器があれば、それも比較の前提に関わる。**

        python - <<'PY'
        import csv, collections
        A = "tasks/T-2026-08-11-s0-reevaluation-feasibility/audit"
        rows = list(csv.DictReader(open(f"{A}/target_runs.csv", encoding="utf-8")))
        by = collections.defaultdict(list)
        for r in rows: by[r["experiment_id"]].append(r)
        print("検出器（experiment_id）数:", len(by))
        for k in sorted(by):
            seeds = sorted(x.get("seed") or "?" for x in by[k])
            exc = sum(1 for x in by[k] if (x.get("excluded") or "").lower() == "true")
            print(f"  {k}: runs {len(by[k])} seeds {seeds} 除外 {exc}")
        PY

| Phase A 完了判定 | 期待 |
|---|---|
| `conventions_rev` と runindex commit の現在値 | 実測値 |
| 索引側の対象一覧 | 実測値。`maskdino` と `varifocanet` の所在を明記 |
| 実体側との集合差（両方向） | 実測値。差の内容を記載 |
| 検出器ごとの run 数と seed | 実測値。3 seed 未満があれば明記 |

---

# Phase B — 評価条件の系統差の中身を開く

## Task 2: 6 系統が何によって分かれているかを測る

**Files:** Create `AUD/recipe_diff.txt`

**この Phase の結果次第で、再評価そのものが不要になる可能性がある。**
系統差が無害なキーだけで生じているなら、表はそのまま使える。

- [ ] **Step 1: `eval_recipe_id` の定義を実装から確かめる**

        grep -n "eval_recipe_id" tools/harvest_runindex.py | cut -c1-160

  **何をハッシュしているのかを実装から確定する。** 記述用キーを含んでいるなら、
  id が違っても実効的な差が無い場合がある。**推測で書かない。**

- [ ] **Step 2: 対象 run の評価条件を全キーで並べ、集合差を取る**

        python - <<'PY'
        import csv, json, pathlib, collections
        A = "tasks/T-2026-08-11-s0-reevaluation-feasibility/audit"
        rows = list(csv.DictReader(open(f"{A}/target_runs.csv", encoding="utf-8")))
        recs = {}
        for r in rows:
            p = pathlib.Path(r["path"]) / "metrics.json"
            if not p.exists():
                recs[r["path"]] = None; continue
            d = json.loads(p.read_text(encoding="utf-8"))
            recs[r["path"]] = d.get("eval_recipe")
        missing = [k for k, v in recs.items() if v is None]
        print("metrics.json か eval_recipe が無い run:", len(missing))
        for m in missing: print("   ", m)
        # 全 run に現れるキーの和集合を先に作る（片方にしか無いキーを落とさない）
        keys = set()
        for v in recs.values():
            if isinstance(v, dict):
                keys |= set(v)
                tc = v.get("test_cfg")
                if isinstance(tc, dict): keys |= {"test_cfg." + k for k in tc}
        print("出現した全キー:", len(keys))
        def get(v, k):
            if not isinstance(v, dict): return None
            if k.startswith("test_cfg."):
                tc = v.get("test_cfg") or {}
                return tc.get(k[len("test_cfg."):]) if isinstance(tc, dict) else None
            return v.get(k)
        out = []
        for k in sorted(keys):
            vals = collections.Counter(repr(get(v, k)) for v in recs.values())
            if len(vals) > 1:
                out.append((k, dict(vals)))
        print("値が割れているキー:", len(out))
        for k, v in out: print("  ", k, v)
        pathlib.Path(f"{A}/recipe_diff.txt").write_text(
            "\n".join(f"{k}\t{v}" for k, v in out), encoding="utf-8")
        PY

  **キーの和集合を先に作ること。** 片方の run にしか無いキーを落とすと、
  差の全体を見たことにならない。

- [ ] **Step 3: 割れているキーを、mAP に影響するものとしないものに分ける**

  **実装を読んで判断すること。** 起票者は判断材料を持たない。

  - `score_thr` `nms_pre` `nms_iou` `max_per_img` は後処理の設定であり、
    値が違えば同じ重みでも mAP が変わりうる
  - `server_name` は `recipes_match` が判定から除外している
  - `gpu_count` `effective_batch_size` は**学習時**の条件であり、
    評価そのものには効かないが、重みが違うため mAP に影響する

  分類の根拠を RESULT に書く。**判断が付かないキーは `UNKNOWN` とする。**

- [ ] **Step 4: 影響するキーだけで系統を数え直す**

        python - <<'PY'
        import csv, json, pathlib, collections
        A = "tasks/T-2026-08-11-s0-reevaluation-feasibility/audit"
        rows = list(csv.DictReader(open(f"{A}/target_runs.csv", encoding="utf-8")))
        EFFECTIVE = ("score_thr", "nms_pre", "nms_iou", "max_per_img")
        grp = collections.defaultdict(list)
        for r in rows:
            p = pathlib.Path(r["path"]) / "metrics.json"
            if not p.exists(): continue
            tc = (json.loads(p.read_text(encoding="utf-8")).get("eval_recipe") or {}).get("test_cfg") or {}
            key = tuple(repr(tc.get(k)) for k in EFFECTIVE)
            grp[key].append(r["experiment_id"])
        print("後処理設定で見た系統数:", len(grp))
        for k, v in sorted(grp.items(), key=lambda x: -len(x[1])):
            print("  ", dict(zip(EFFECTIVE, k)), "run", len(v),
                  "検出器", sorted(set(v)))
        PY

  **系統が 1 つなら、再評価は不要である。** その場合はそう結論してよい。
  2 つ以上なら、どの検出器がどちらに属するかを表にする。

| Phase B 完了判定 | 期待 |
|---|---|
| `eval_recipe_id` の定義 | 実装から確定した記述 |
| 値が割れているキーの全列挙 | 実測値。キーの和集合から取ったこと |
| 影響する／しないの分類と根拠 | 実測値。判断不能は UNKNOWN |
| 後処理設定で見た系統数と所属 | 実測値。1 系統なら再評価不要と結論 |

---

# Phase C — 重みと予測の残存を測る

## Task 3: 何が残っているかを測る（G2）

**Files:** Create `AUD/artifacts.csv`

- [ ] **Step 1: 走査が symlink を辿ることを先に確かめる（陽性対照）**

  **前 task の致命的欠陥がここで再発しうる。先に走査能力を検査する。**

        mkdir -p /tmp/probe_real/sub && echo x > /tmp/probe_real/sub/probe.bin
        ln -sfn /tmp/probe_real /tmp/probe_link
        echo "--- find -L ---"
        find -L /tmp/probe_link -name "probe.bin"
        echo "--- python os.walk followlinks ---"
        python - <<'PY'
        import os
        hit = [os.path.join(r, f) for r, _, fs in os.walk("/tmp/probe_link", followlinks=True)
               for f in fs if f == "probe.bin"]
        print("検出:", hit)
        assert hit, "走査が symlink を辿れていない。この方法は使えない"
        PY
        echo "--- 対照: rglob は辿らない ---"
        python - <<'PY'
        import pathlib
        print("rglob 検出:", [str(p) for p in pathlib.Path("/tmp/probe_link").rglob("probe.bin")])
        PY
        rm -rf /tmp/probe_real /tmp/probe_link

  **`find -L` と `os.walk(followlinks=True)` が検出し、`rglob` が検出しないことを
  確認する。** 検出できなければ G2 は `stop`。以降の走査はこの 2 系統のみを使う。

- [ ] **Step 2: run ごとの成果物を測る**

        python - <<'PY'
        import csv, os, pathlib, json
        A = "tasks/T-2026-08-11-s0-reevaluation-feasibility/audit"
        rows = list(csv.DictReader(open(f"{A}/target_runs.csv", encoding="utf-8")))
        out = []
        for r in rows:
            base = r["path"]
            rec = {"experiment_id": r["experiment_id"], "path": base}
            found = {"ckpt": [], "pred": [], "cfg": []}
            for root, dirs, files in os.walk(base, followlinks=True):
                for f in files:
                    p = os.path.join(root, f)
                    low = f.lower()
                    if low.endswith((".pth", ".pt", ".ckpt")): found["ckpt"].append(p)
                    elif low.endswith((".pkl", ".bbox.json", ".segm.json")) or \
                         "predict" in root.lower(): found["pred"].append(p)
                    elif low.endswith(".py") and "config" in low: found["cfg"].append(p)
            for k, v in found.items():
                rec["n_" + k] = len(v)
                total = 0
                for p in v:
                    try: total += os.path.getsize(p)
                    except OSError: pass
                rec["bytes_" + k] = total
                rec["example_" + k] = v[0] if v else ""
            rec["has_config_yaml"] = (pathlib.Path(base) / "config.yaml").exists()
            out.append(rec)
        cols = sorted({k for r in out for k in r})
        with open(f"{A}/artifacts.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(out)
        n = len(out)
        print("対象 run:", n)
        for k in ("ckpt", "pred", "cfg"):
            have = sum(1 for r in out if r["n_" + k] > 0)
            print(f"  {k} を持つ run: {have} / {n}")
        PY
        wc -l tasks/T-2026-08-11-s0-reevaluation-feasibility/audit/artifacts.csv

  **`predictions/` の中身の判定条件は実装ではなく起票者の推測である。**
  実際のディレクトリ名とファイル拡張子を 1 run 分だけ直接見て、条件が正しいかを
  確かめてから全件に適用すること。

- [ ] **Step 3: 件数ゼロを直接確認で裏づける（G2）**

  **重みが 0 件と出た run について、別の方法で本当に無いことを確かめる。**

        python - <<'PY'
        import csv
        A = "tasks/T-2026-08-11-s0-reevaluation-feasibility/audit"
        rows = list(csv.DictReader(open(f"{A}/artifacts.csv", encoding="utf-8")))
        zero = [r["path"] for r in rows if r["n_ckpt"] == "0"]
        print("重み 0 件の run:", len(zero))
        for p in zero[:10]: print("   ", p)
        PY

  上で出た run について、次を実行する。**`-L` を付けること。**

        for d in <上で出たパスを 3 件ほど>; do
          echo "=== ${d} ==="
          ls -lL "${d}"
          ls -lL "${d}/checkpoints" 2>/dev/null || echo "  checkpoints ディレクトリ無し"
        done

  **不在を確認したら、そこで止めない。** そのディレクトリに何があるのかを記録し、
  **重みがどこへ行ったのか**（別の場所に退避された形跡があるか、そもそも
  保存する設定でなかったか）を追う。学習スクリプトの保存設定を読むこと。

- [ ] **Step 4: 重みの実体が退避先にないかを確かめる**

  本ホストでは退避物が `~/m2-archive/` 配下へ移動している。

        ls -d ~/m2-archive/* 2>/dev/null || echo "退避ディレクトリ無し"
        find -L ~/m2-archive -name "*.pth" -maxdepth 4 2>/dev/null | head -20
        find -L ~/m2-archive -name "*.pth" -maxdepth 4 2>/dev/null | wc -l

  **件数を必ず出す。** 見つかった場合は、それが対象 run のものかを名前で照合する。

| Phase C 完了判定 | 期待 |
|---|---|
| 走査能力の陽性対照 | `find -L` と `os.walk` が検出、`rglob` が非検出 |
| run ごとの重み・予測・設定の有無 | 実測値。件数と容量 |
| 判定条件の妥当性確認 | 1 run を直接見て確かめたこと |
| 重み 0 件の直接確認と原因追跡 | 実測値。不在の意味まで記載 |
| 退避先の走査結果 | 実測値。件数を明記 |

---

# Phase D — 再評価の経路と規模を測る

## Task 4: やり直せる経路があるかを測る

- [ ] **Step 1: 評価だけを走らせる経路が存在するかを実装から確かめる**

        ls scripts/ | grep -i -E "eval|test|infer" || echo "該当なし"
        grep -rn "eval-test\|--eval\b\|test_cfg" scripts/*.py | cut -c1-160 | head -40
        grep -n "test_cfg" src/egosurgery/engines/mmdet_trainer.py | cut -c1-160

  **後処理の設定を外から差し替えて評価だけを走らせられるか**を実装から確定する。
  できない場合、何が足りないか（引数が無い、学習と一体になっている等）を書く。

- [ ] **Step 2: 予測から採点し直せるかを判断する**

  Phase C で予測が残っていた場合、**それが後処理の前か後かを確かめる。**

  - 後処理の**後**（`max_per_img` で切られた後）の予測しか無ければ、
    `nms_pre` や `max_per_img` を変える再採点はできない
  - `score_thr` を**下げる**方向は、閾値より上の予測しか保存されていなければできない

  1 件の予測ファイルを開き、件数と score の最小値を見て判断する。
  **判断が付かなければ `UNKNOWN` とする。**

- [ ] **Step 3: 再学習になった場合の規模の材料を測る**

        python - <<'PY'
        import csv, json, pathlib
        A = "tasks/T-2026-08-11-s0-reevaluation-feasibility/audit"
        rows = list(csv.DictReader(open(f"{A}/target_runs.csv", encoding="utf-8")))
        for r in rows[:5]:
            p = pathlib.Path(r["path"])
            for name in ("config.yaml", "command.sh"):
                f = p / name
                print("---", f, "存在" if f.exists() else "無し")
            log = p / "logs"
            if log.is_dir():
                fs = sorted(x.name for x in log.iterdir())
                print("   logs:", fs[:8])
        PY

  学習ログから 1 run あたりの所要時間が読めるなら記録する。
  **読めなければ `UNKNOWN`。推定値を書かない。**

| Phase D 完了判定 | 期待 |
|---|---|
| 評価だけを走らせる経路の有無 | 実装から確定。無ければ何が足りないか |
| 予測からの再採点可否 | 実測値または UNKNOWN。根拠を明記 |
| 再学習時の規模の材料 | 実測値または UNKNOWN |

---

# Phase E — 総括

## Task 5: 三択の材料をまとめる

**Files:** Create `RESULT.md`, `result.yaml`, `tasks/inbox.d/T-2026-08-11-s0-reevaluation-feasibility.md`

- [ ] **Step 1: `RESULT.md` を書く。次を必ず含める**

  1. **結論。**「学習をやり直さずに再評価できるか」を Yes / No / 一部 で答える
  2. その根拠（何が残っていて何が無いか）
  3. **Phase B の結果として、そもそも再評価が必要かどうか**
  4. 三択（作り直す / 条件差を明記して載せる / 表を落とす）それぞれの可否とコスト
  5. **起票者の推測のうち、実測で裏づけられたものと否定されたもの**

- [ ] **Step 2: 未解決事項を受け皿へ起票する**

- [ ] **Step 3: 全完了判定を検証し、作業ツリーを確認する**

        git status --porcelain | cut -c1-120

  Expected: 変更は `tasks/` 配下のみ。

- [ ] **Step 4: 同期の抑止を解除する**

        rm -f .sync-pause
        ls -la .sync-pause || echo "解除済み"

| Phase E 完了判定 | 期待 |
|---|---|
| RESULT に 5 点が記載されている | あり |
| 受け皿への起票 | あり |
| 作業ツリーの変更が `tasks/` 配下のみ | あり |
| `.sync-pause` の削除 | あり |

---

## 想定外が起きたときの扱い

| 事象 | 扱い |
|---|---|
| 走査が symlink を辿れない | **G2 は `stop`。** 前 task の欠陥の再発であり、そのまま進めば誤った結論に至る |
| 重みが 1 件も無い | **そこで止めない。** どこへ行ったか、保存設定はどうだったかを追う。`escalate_if` に該当するため RESULT の冒頭に書く |
| Phase B で系統が 1 つと判明 | **再評価は不要。** そう結論し、Phase C 以降は「将来のための棚卸し」として続ける |
| 判定条件が実態と合わない | 起票者の推測なので、実態を見て条件を直し、直したことを記録する |
| 実装が SPEC の記述と食い違う | **実装に従う。** SPEC のどこが誤っていたかを書く |
| 対象一覧が索引側と実体側で食い違う | G1 は `ask`。どちらを使うかを明記して続行する |
| 容量の走査が遅い | 重みは大きい。`getsize` のみで開かないこと。数分かかっても待つ |

# tool と phase の split 整合性および eval_recipe の実効性を実測する

**task_id:** `T-2026-08-11-split-and-recipe-audit`  **kind:** `analysis`  **depends_on:** なし
**実行ホスト:** `lecun`

## Goal

`egosurgery_tool` と `egosurgery_phase` の分割定義と評価条件が、**記録の上でも実体の上でも
一貫していたか**を実測で確定する。読み取りのみ。学習も評価も行わない。

検出側には論文サイズとの照合（`assert_paper_split`）と陽性対照を持つテストがある。
**一方で工程側には同等の機構が無い。** 工程の分割は `data/raw/ego/<split>/` の配置だけで
決まり、検証が入っていない。

さらに `src/egosurgery/engines/phase_trainer.py` の `_build_eval_recipe` は、注釈ファイルを
読めなかった場合に split サイズへ **0 を静かに書く**。config が指す
`data/annotations/egosurgery_phase/instances_*.json` は `configs/stage/s4_phase_baseline.yaml`
自身が暫定プレースホルダと書いている。実在しないなら記録は 3 つとも 0 になり、
`recipes_match` は **0 と 0 を一致と判定しうる**。分割の照合が素通りしている恐れがある。

**これは起票者の推測であり未実測である。推測を裏づけることが目的ではない。
推測が誤りであることの確認も等価に価値がある。**

工程 CSV は配布物として 21 動画分あり、使用しているのは 15 動画分のみと確認済み。
その差が数字で説明できるかも本 task で測る。

## 0. 前提と禁止事項

    cd "$(git rev-parse --show-toplevel)"
    git fetch origin
    git checkout -b feat/split-and-recipe-audit origin/phase0
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
| 8 | GPU を使う。本 task に GPU を要する処理は無い |
| 9 | 統合する。自動統合を有効化する |

書き込み先は `tasks/T-2026-08-11-split-and-recipe-audit/` 配下と
`tasks/inbox.d/T-2026-08-11-split-and-recipe-audit.md` に限る。以下 `AUD` を
`tasks/T-2026-08-11-split-and-recipe-audit/audit` の意味で使う。

`contract.conventions_rev` は `UNKNOWN` にしてある。Task 1 で実測して置換すること。
**これは逸脱ではなく手順である。`deviations` に書かない。**
常駐処理による統合は**実行者の逸脱ではない。事実として記録する。**

### 起票者からの申し送り

起票者の検査コマンドが検証対象を検証できていない誤りが 18 task 連続で発生している。
直近では、対象の一覧そのものが縮んでも通る検査を出し、17 文書が静かに落ちても合格する
設計を作った。また記録を作る流れに表示用の切り詰めを混ぜ、肝心の候補が読めなくなった。

実行環境の対話シェルは bash ではない。**変数の直後に記号が続く場合は波括弧で囲むこと。**
配列の添字による終了コードの取得は使えない。単語分割も起きない。

**本 SPEC の検査も同型の誤りを含みうる。** 次を守ること。

| # | 注意 |
|---|---|
| 1 | 件数が 0 のとき、対象が実在することを先に確かめ、別の探し方でも 0 になることを確認する |
| 2 | 仕組みの挙動は実装を読んでから信じる。食い違えば実装に従い記録する |
| 3 | 記録を作る流れに表示用の切り詰めを混ぜない。記録を作ってから別のコマンドで表示する |
| 4 | 検査が空振りでないことを陽性対照で確かめる |
| 5 | 対象の一覧そのものが正しいかを確かめる。母集団が縮んでも通る検査を書かない |
| 6 | 列や項目の検出は新旧の集合差で求める。名前の部分一致で探さない |

---

# Phase A — 母集団と前提の確定

## Task 1: 環境と母集団を確定する

**Files:** Create `AUD/`

- [ ] **Step 1: 位置と環境を記録する**

        mkdir -p tasks/T-2026-08-11-split-and-recipe-audit/audit
        pwd; git branch --show-current; git rev-parse --short HEAD
        ls -la .sync-pause; python -V; which python

  Expected: repo 直下。ブランチ `feat/split-and-recipe-audit`。`.sync-pause` 実在。
  `python` が `.venv` 配下。

- [ ] **Step 2: `conventions_rev` を実測して置換する**

        git log -1 --format=%h -- context/conventions.md
        git log -1 --format='%h %cI' -- runindex/

  前者で `spec.yaml` の `contract.conventions_rev` の `UNKNOWN` を置き換える。

- [ ] **Step 3: 母集団が縮んでいないことを確かめる（G1）**

  本ホストでは退避物が `~/m2-archive/20260811/` へ移動している。**index が指す run の
  ディレクトリが実在するかを数える。列名は推測せず実測してから使う。**

        python - <<'PY'
        import csv, pathlib
        rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
        print("行数:", len(rows))
        print("列候補:", [c for c in rows[0] if "path" in c or "dir" in c or "key" in c])
        key = "path" if "path" in rows[0] else None
        assert key, "path 列が無い。実在する列名を見て決めること"
        miss = [r[key] for r in rows if not pathlib.Path(r[key]).exists()]
        print("欠落:", len(miss))
        pathlib.Path("tasks/T-2026-08-11-split-and-recipe-audit/audit/missing_runs.txt"
                     ).write_text("\n".join(miss), encoding="utf-8")
        for n in ("experiments", "verdicts"):
            print(n, len(list(csv.DictReader(open(f"runindex/{n}.csv", encoding="utf-8")))))
        PY

  起票時は index=749 / experiments=206 / verdicts=1038、commit `12cc0e8`。
  **食い違ってよい。実測値を記録する。** 欠落が非ゼロなら G1 は `ask`。件数と代表例を
  記録し、以降の集計が縮んだ母集団の上で行われる旨を明記して続行してよい。

| Phase A 完了判定 | 期待 |
|---|---|
| 出力先と環境 | 記録済み |
| `conventions_rev` の置換 | 実測の短縮 sha |
| runindex 3 ファイルの行数 | 実測値 |
| index が指す run の欠落件数 | 実測値。0 が望ましい |

---

# Phase B — データ実体の分割整合性

## Task 2: 実体としての分割を測る

**Files:** Create `AUD/split_entity.txt`

- [ ] **Step 1: 分割の実体・重なり・識別子衝突を測る（陽性対照つき・G2）**

  `phase_dataset.py` の `_build_frame_index` は `index[frame_id] = (split, img)` で
  辞書に入れる。**衝突すると後勝ちで静かに上書きされる。** 実際に衝突があるかを測る。

        python - <<'PY'
        import pathlib, collections
        root = pathlib.Path("data/raw/ego")
        vids, owner = {}, collections.defaultdict(list)
        for s in ("train", "val", "test"):
            d = root / s
            if not d.is_dir():
                print(s, "ディレクトリが無い"); continue
            vids[s] = sorted(p.name for p in d.iterdir() if p.is_dir())
            for p in d.rglob("*"):
                if p.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    owner[p.stem].append(s)
        for s, v in vids.items():
            n = sum(1 for x in owner.values() if s in x)
            print(s, "動画", len(v), v, "画像", n)
        ks = sorted(vids)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                print(ks[i], ks[j], "動画の重なり:", sorted(set(vids[ks[i]]) & set(vids[ks[j]])))
        cross = {k: v for k, v in owner.items() if len(set(v)) > 1}
        print("総 frame_id:", len(owner), "split 跨ぎ重複:", len(cross))
        for k in sorted(cross)[:20]:
            print("  ", k, cross[k])
        probe = dict(owner); probe["__PROBE__"] = ["train", "val"]
        pc = {k: v for k, v in probe.items() if len(set(v)) > 1}
        print("陽性対照 検出:", len(pc), "期待:", len(cross) + 1)
        assert len(pc) == len(cross) + 1, "陽性対照が働いていない"
        PY

  Expected: 動画は 10 / 2 / 3 本。動画の重なりも split 跨ぎ重複も 0。
  **総 frame_id が画像枚数の合計と一致すること。** 陽性対照が 1 件多く検出しなければ
  G2 は `stop`。

- [ ] **Step 2: 動画 ID の重なりを別の探し方でも測る**

        for s in train val test; do ls -1 "data/raw/ego/${s}" | sort > "/tmp/vid_${s}.txt"; done
        wc -l /tmp/vid_train.txt /tmp/vid_val.txt /tmp/vid_test.txt
        comm -12 /tmp/vid_train.txt /tmp/vid_val.txt
        comm -12 /tmp/vid_train.txt /tmp/vid_test.txt
        comm -12 /tmp/vid_val.txt /tmp/vid_test.txt

  **`wc -l` を必ず出す。** 対象が空なら重なりは自明に 0 件になり検査が空振りする。

- [ ] **Step 3: `data/splits/ego_*.txt` の実内容を測る**

  `README.md` は「動画 ID リスト」、`data/README.md` は「サンプルの ID 一覧」と書いており
  **記述が食い違っている。実態を測る。**

        for s in train val test; do echo "--- ${s} ---"; wc -l "data/splits/ego_${s}.txt"; \
          sed -n '1,3p' "data/splits/ego_${s}.txt"; done
        python - <<'PY'
        import pathlib
        root = pathlib.Path("data/raw/ego")
        for s in ("train", "val", "test"):
            f = pathlib.Path("data/splits") / f"ego_{s}.txt"
            if not f.exists(): print(s, "splits ファイルが無い"); continue
            lines = {x.strip() for x in f.read_text(encoding="utf-8").splitlines() if x.strip()}
            d = root / s
            v = {p.name for p in d.iterdir() if p.is_dir()} if d.is_dir() else set()
            print(s, "行数", len(lines), "実体動画", len(v),
                  "splits にのみ", sorted(lines - v)[:8], "実体にのみ", sorted(v - lines)[:8])
        PY

  **集合差で求めること。名前の部分一致で探さない。**

- [ ] **Step 4: 検出注釈の実測サイズと分割間の重なりを測る**

        python - <<'PY'
        import json, pathlib, collections
        base = pathlib.Path("data/annotations/egosurgery_tool")
        sets = {}
        for s in ("train", "val", "test"):
            p = base / f"instances_{s}.json"
            if not p.exists(): p = base / "tool" / f"{s}.json"
            if not p.exists(): print(s, "注釈が無い"); continue
            d = json.loads(p.read_text(encoding="utf-8"))
            fn = [pathlib.Path(i["file_name"]).name for i in d["images"]]
            dup = [k for k, v in collections.Counter(fn).items() if v > 1]
            print(s, p.name, "images", len(d["images"]), "anns", len(d["annotations"]),
                  "videos", sorted({f.split("_")[0] for f in fn}), "内部重複", len(dup))
            sets[s] = set(fn)
        print("実在した split:", {k: len(v) for k, v in sets.items()})
        ks = sorted(sets)
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                ov = sets[ks[i]] & sets[ks[j]]
                print(ks[i], ks[j], "重なり", len(ov), sorted(ov)[:5])
        PY

  期待は train 9657 枚 32272 件、val 1515 枚 4707 件、test 4265 枚 12673 件、動画 10 / 2 / 3 本。
  **`実在した split` の件数を必ず出す。** 空集合同士の比較は自明に 0 件になる。

| Phase B 完了判定 | 期待 |
|---|---|
| 分割ごとの動画数と画像枚数 | 10 / 2 / 3 本。実測値 |
| 動画 ID の重なり（2 系統） | 0 件。両系統が一致 |
| フレーム識別子の split 跨ぎ重複 | 0 件。陽性対照が働くこと |
| `data/splits/*.txt` と実体の集合差 | 実測値。差の内容を明記 |
| 検出注釈のサイズ・動画集合・重なり | 実測値。母数を併記 |

---

# Phase C — 工程ラベルの母集団

## Task 3: 工程側の実体と落ちている量を測る

**Files:** Create `AUD/phase_entity.txt`

- [ ] **Step 1: 工程 CSV の実体と語彙を測る**

  `constants.py` は「CSV に id は無いため当方で割り当てる」と書いている。
  **実データの語彙と割当の一致を集合差で測る。**

        python - <<'PY'
        import pathlib, csv, collections, sys
        sys.path.insert(0, "src")
        from egosurgery.datasets.constants import PHASE_NAME_TO_ID
        d = pathlib.Path("data/annotations/egosurgery_phase")
        files = sorted(d.glob("*.csv"))
        vids, total, raw = set(), 0, collections.Counter()
        for f in files:
            vids.add(f.stem.split("_")[0])
            with f.open(encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    total += 1; raw[repr(row.get("Phase"))] += 1
        print("CSV", len(files), "動画 ID", len(vids), sorted(vids), "総行数", total)
        print("表記の種類:", len(raw))
        for k, v in raw.most_common(): print("  ", k, v)
        seen = {eval(k).strip() if eval(k) is not None else "" for k in raw}
        print("定義にのみ:", sorted(set(PHASE_NAME_TO_ID) - seen))
        print("データにのみ:", sorted(seen - set(PHASE_NAME_TO_ID)))
        PY

  **`repr` で出すこと。** 前後の空白や大文字小文字の違いはそのままでは見えない。

- [ ] **Step 2: データセット構築時に落ちる件数と split 別採用数を測る**

        python - <<'PY'
        import pathlib, sys, collections
        sys.path.insert(0, "src")
        from egosurgery.datasets.constants import PHASE_NAME_TO_ID
        from egosurgery.datasets.phase_dataset import _build_frame_index, _load_phase_csv
        idx = _build_frame_index(pathlib.Path("data/raw/ego"))
        print("画像索引:", len(idx))
        per, no_img, unk, phase_ids = collections.Counter(), 0, 0, set()
        for f in sorted(pathlib.Path("data/annotations/egosurgery_phase").glob("*.csv")):
            for fid, name in _load_phase_csv(f):
                phase_ids.add(fid)
                m = idx.get(fid)
                if m is None: no_img += 1; continue
                if PHASE_NAME_TO_ID.get(name) is None: unk += 1; continue
                per[m[0]] += 1
        print("画像が無い行:", no_img, "語彙外の行:", unk, "split 別採用:", dict(per))
        import json
        base = pathlib.Path("data/annotations/egosurgery_tool")
        tool = set()
        for s in ("train", "val", "test"):
            p = base / f"instances_{s}.json"
            if not p.exists(): p = base / "tool" / f"{s}.json"
            if not p.exists(): continue
            for i in json.loads(p.read_text(encoding="utf-8"))["images"]:
                tool.add(pathlib.Path(i["file_name"]).stem)
        print("phase", len(phase_ids), "tool", len(tool),
              "tool のみ", len(tool - phase_ids), "phase のみ", len(phase_ids - tool),
              "共通", len(phase_ids & tool))
        PY

  Expected: split 別採用が train 9657 / val 1515 / test 4265。**`画像が無い行` は
  使っていない 6 動画分に相当するはず。その差が説明できるかを見る。**
  集合差は**両方向を出すこと。** 片方向では包含関係が確定しない。

- [ ] **Step 3: 工程論文の分割定義が repo 内にあるかを確かめる**

  工程論文の分割は 14 / 2 / 5 本と `prompts/research_pivot_summary_and_roadmap.md` にある。
  **その動画割当が一次情報として存在するかを探す。**

        grep -rn "14/2/5" --include=*.md --include=*.py --include=*.yaml . | cut -c1-180
        grep -rln "PHASE_SPLIT" --include=*.py src tools scripts

  見つからなければ **`UNKNOWN`** とし、推測で対応表を作らない。

- [ ] **Step 4: manifest の整合テストを実走する**

        .venv/bin/python -m pytest tests/test_joint_dataset.py -v \
          > tasks/T-2026-08-11-split-and-recipe-audit/audit/pytest_joint.txt 2>&1
        echo "exit=$?"
        tail -20 tasks/T-2026-08-11-split-and-recipe-audit/audit/pytest_joint.txt
        grep -c SKIPPED tasks/T-2026-08-11-split-and-recipe-audit/audit/pytest_joint.txt

  **`SKIPPED` の件数を必ず数える。** 実 manifest が無ければ skip し、緑に見えても
  何も検証していない。

| Phase C 完了判定 | 期待 |
|---|---|
| CSV 数・動画 ID 数・総行数 | 実測値。動画 21 本の想定 |
| ラベル語彙の集合差（両方向） | 一致。表記ゆれの有無を明記 |
| 落ちる行数と split 別採用数 | 実測値。9657 / 1515 / 4265 か |
| 工程と検出の frame 集合差（両方向） | 実測値。包含関係を明記 |
| 工程論文の分割定義の所在 | 実測値または UNKNOWN |
| manifest 整合テストと skip 件数 | 実測値。skip が多ければその旨を明記 |

---

# Phase D — 評価条件の記録と照合の実効性

## Task 4: 記録された評価条件を横断で測る

**Files:** Create `AUD/eval_recipe.csv`, `AUD/nonofficial_split.txt`

- [ ] **Step 1: 走査対象の根を確定し、全 run の評価条件を 1 枚に集める**

  **`experiments/` だけを見て「全 run」と呼ばないこと。** 根を先に実測する。

        ls -d experiments transfer 2>/dev/null
        find . -maxdepth 3 -name metrics.json -not -path "./tasks/*" | sed 's#/[^/]*$##' \
          | cut -d/ -f1-2 | sort -u

        python - <<'PY'
        import json, pathlib, csv
        roots = [p for p in (pathlib.Path("experiments"), pathlib.Path("transfer")) if p.is_dir()]
        print("根:", [str(r) for r in roots])
        rows = []
        for root in roots:
            for p in sorted(root.rglob("metrics.json")):
                try: d = json.loads(p.read_text(encoding="utf-8"))
                except Exception as e:
                    rows.append({"path": str(p), "error": type(e).__name__}); continue
                r = d.get("eval_recipe")
                rec = {"path": str(p), "has_recipe": bool(r)}
                if isinstance(r, dict):
                    for k in ("split_train_images", "split_val_images", "split_test_images",
                              "split_train_annotations", "server_name", "gpu_count",
                              "effective_batch_size", "lr_scaling"):
                        rec[k] = r.get(k)
                    tc = r.get("test_cfg") or {}
                    if isinstance(tc, dict):
                        for k in ("task", "score_thr", "max_per_img", "nms_pre", "nms_iou",
                                  "inference_protocol", "jaccard_mode"):
                            rec["tc_" + k] = tc.get(k)
                rows.append(rec)
        cols = sorted({k for r in rows for k in r})
        out = pathlib.Path("tasks/T-2026-08-11-split-and-recipe-audit/audit/eval_recipe.csv")
        with out.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
        print("metrics.json 総数:", len(rows))
        PY
        wc -l tasks/T-2026-08-11-split-and-recipe-audit/audit/eval_recipe.csv

- [ ] **Step 2: split サイズの分布を測る**

        python - <<'PY'
        import csv, collections, pathlib
        A = "tasks/T-2026-08-11-split-and-recipe-audit/audit"
        rows = list(csv.DictReader(open(f"{A}/eval_recipe.csv", encoding="utf-8")))
        print("総数", len(rows), "recipe あり", sum(1 for r in rows if r["has_recipe"] == "True"))
        key = ("split_train_images", "split_val_images", "split_test_images")
        for task in ("phase", "not_phase"):
            sub = [r for r in rows if r["has_recipe"] == "True" and
                   ((r.get("tc_task") == "phase") == (task == "phase"))]
            c = collections.Counter(tuple(r.get(k) or "" for k in key) for r in sub)
            print(f"--- {task} ({len(sub)} run) ---")
            for k, v in c.most_common(): print("  ", k, v)
        official = ("9657", "1515", "4265")
        bad = [r["path"] for r in rows if r["has_recipe"] == "True"
               and tuple(r.get(x) or "" for x in key) != official]
        zero = [r["path"] for r in rows if (r.get("split_train_images") or "") in ("0", "0.0")]
        print("公式値と異なる:", len(bad), "train が 0:", len(zero))
        pathlib.Path(f"{A}/nonofficial_split.txt").write_text("\n".join(bad), encoding="utf-8")
        PY
        head -20 tasks/T-2026-08-11-split-and-recipe-audit/audit/nonofficial_split.txt

  **記録を作ってから表示している。切り詰めを記録の流れに混ぜない。**

- [ ] **Step 3: 照合関数の実挙動を陽性対照で測る（G3・本 task の中心）**

  **`recipes_match` の実装を先に読むこと。** 起票者は「split サイズの一致を見る」と
  書いたが、実装を読まずに書いた記述である。**食い違えば実装に従う。**

        sed -n '/def recipes_match/,/^def /p' src/egosurgery/utils/eval_recipe.py

        python - <<'PY'
        import sys
        sys.path.insert(0, "src")
        from egosurgery.utils.eval_recipe import (recipes_match, build_eval_recipe,
                                                  LOCKED_DOWN_TEST_CFG, PAPER_SPLIT_SIZES)
        Z = {k: {"images": 0, "annotations": 0} for k in ("train", "val", "test")}
        W = {"train": {"images": 8000, "annotations": 25000},
             "val": {"images": 1515, "annotations": 4707},
             "test": {"images": 4265, "annotations": 12673}}
        mk = lambda s: build_eval_recipe(LOCKED_DOWN_TEST_CFG, s, "probe")
        for name, a, b, exp in [
            ("公式 と 公式", mk(PAPER_SPLIT_SIZES), mk(PAPER_SPLIT_SIZES), "True"),
            ("ゼロ と ゼロ", mk(Z), mk(Z), "要観察"),
            ("公式 と ゼロ", mk(PAPER_SPLIT_SIZES), mk(Z), "False"),
            ("公式 と 誤分割", mk(PAPER_SPLIT_SIZES), mk(W), "False")]:
            print(f"{name}: 実測={recipes_match(a, b)} 期待={exp}")
        PY

  **「ゼロ と ゼロ」が `True` を返すなら、split サイズが 0 で記録された run どうしの
  照合は素通りしている。これが本 task の中心的な問いである。**
  **「公式 と 誤分割」が `False` を返さなければ照合そのものが機能していない。G3 は `stop`。**

- [ ] **Step 4: 工程側が実際に何を記録しているかを測る**

        python - <<'PY'
        import csv, collections
        A = "tasks/T-2026-08-11-split-and-recipe-audit/audit"
        rows = list(csv.DictReader(open(f"{A}/eval_recipe.csv", encoding="utf-8")))
        ph = [r for r in rows if (r.get("tc_task") or "") == "phase"]
        print("工程 run:", len(ph))
        for k in ("split_train_images", "tc_inference_protocol", "tc_jaccard_mode", "server_name"):
            print(k, dict(collections.Counter(r.get(k) or "(空)" for r in ph)))
        det = [r for r in rows if r["has_recipe"] == "True" and (r.get("tc_task") or "") != "phase"]
        print("検出 run:", len(det))
        for k in ("tc_score_thr", "tc_nms_pre", "tc_nms_iou", "tc_max_per_img"):
            print(k, dict(collections.Counter(r.get(k) or "(空)" for r in det)))
        PY
        ls -la data/annotations/egosurgery_phase/instances_train.json || echo "存在しない"

  **検出側の評価条件が 2 系統に分かれている場合、どの対照ペアが跨いでいるかまで特定する。**

- [ ] **Step 5: 対照ペアの評価条件が実際に一致しているかを測る**

  `runindex/experiments.csv` の `control_of` が対照を名指しする。**実験 ID から run の
  パスを引き、双方の `eval_recipe` を `recipes_match` に通して不一致の組を列挙する。**
  列名は実測してから使う。引けない組は `UNKNOWN` とし件数を記録する。

        python - <<'PY'
        import csv
        exp = list(csv.DictReader(open("runindex/experiments.csv", encoding="utf-8")))
        print("列に control_of があるか:", "control_of" in exp[0])
        pairs = [(r["experiment_id"], r["control_of"]) for r in exp if r.get("control_of")]
        print("対照宣言のある実験:", len(pairs))
        idx = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
        print("index に experiment_id があるか:", "experiment_id" in idx[0])
        PY

- [ ] **Step 6: 除外規則の取りこぼしを測る**

  backlog の `BL-exclusion-rules-exact-match` は、除外規則が完全一致のみのため退避 run が
  解析対象に混入しうると述べている。**実際に混入しているかを測る。**

        python - <<'PY'
        import pathlib, csv
        dirs = sorted({str(p) for p in pathlib.Path("experiments").rglob("_*") if p.is_dir()})
        print("アンダースコア始まりのディレクトリ:", len(dirs))
        rows = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
        for d in dirs:
            hit = [r for r in rows if r["path"].startswith(d)]
            exc = [r for r in hit if (r.get("excluded") or "").lower() == "true"]
            print(f"  {d}: index {len(hit)} 件 / 除外 {len(exc)} 件")
        PY

  **除外されていない退避 run があれば、それは解析に混ざっている。**

| Phase D 完了判定 | 期待 |
|---|---|
| 走査した根と metrics 総数 | 実測値。`experiments` 以外の根の有無を明記 |
| split サイズの分布 | 工程と検出で分けた実測値 |
| 公式値以外の件数と train が 0 の件数 | 実測値 |
| 照合関数の 4 ケース | 全て記載。ゼロ同士の結果を明記 |
| 工程 run の推論手順と厳密性の分布 | 実測値 |
| 対照ペアの照合結果 | 不一致件数と代表例。引けない組は UNKNOWN |
| 退避ディレクトリの除外状況 | 実測値。混入があれば列挙 |

---

# Phase E — 評価手順の構造的な偏り

## Task 5: 検証で選び検証で報告する構造を測る

- [ ] **Step 1: 最良 epoch の選び方と報告 split を実装で確定する**

        grep -n "max(records" src/egosurgery/engines/*.py | cut -c1-160
        grep -rn "val/mAP\|phase_accuracy" src/egosurgery/engines/*.py | cut -c1-160
        grep -rn "best" scripts/train_s4_tecno.py | cut -c1-160

  **どの指標で最良 epoch を選び、どの split の値を報告しているかを実装から確定する。
  推測で書かない。** 検出側と工程側の双方について書く。

- [ ] **Step 2: 検証側と試験側の乖離の母数を確かめる**

        wc -l runindex/anomalies/val_test_pairs.csv
        python - <<'PY'
        import csv
        rows = list(csv.DictReader(open("runindex/anomalies/val_test_pairs.csv", encoding="utf-8")))
        print("対応表の行数:", len(rows), "列:", sorted(rows[0]) if rows else "なし")
        idx = list(csv.DictReader(open("runindex/index.csv", encoding="utf-8")))
        print("index で試験側を持つ run:", sum(1 for r in idx
              if (r.get("has_test") or "").lower() == "true"))
        PY

  **両者が一致するかを先に見る。** 一致しなければ差の理由を記録し、乖離の集計は
  その母数の上で行われている旨を明記する。

| Phase E 完了判定 | 期待 |
|---|---|
| 最良 epoch の選択指標と報告 split | 実装から確定した記述 |
| 対応表の行数と index 側件数の一致 | 一致。不一致なら差の説明 |

---

# Phase F — 総括と起票

## Task 6: 結論をまとめ、全項目を検証する

**Files:** Create `RESULT.md`, `result.yaml`, `tasks/inbox.d/T-2026-08-11-split-and-recipe-audit.md`

- [ ] **Step 1: `RESULT.md` を書く。次を必ず含める**

  1. 既存の基準点をそのまま論文の数値として使えるか。**使える範囲と使えない範囲を分ける**
  2. 使えない範囲がある場合、再取得に要する対象と規模
  3. **起票者の推測のうち、実測で裏づけられたものと否定されたものを明記する**
  4. 判断が要る事項

- [ ] **Step 2: 未解決事項を受け皿へ起票する**

  `tasks/inbox.d/T-2026-08-11-split-and-recipe-audit.md` に書く。
  **`runindex/` 配下や `tools/harvest_runindex.py` の BACKLOG を手で編集しない。**

- [ ] **Step 3: 全完了判定を検証する**

  Phase A から E の完了判定の表を全て読み直し、**各項目に実測値または UNKNOWN が
  対応していることを確かめる。** 対応していない項目は RESULT に明記する。

        git status --porcelain | cut -c1-120

  Expected: 変更は `tasks/` 配下のみ。`experiments/` `data/` `runindex/` `src/`
  `configs/` `scripts/` に変更が無いこと。**あれば禁止事項に触れている。**

- [ ] **Step 4: 同期の抑止を解除する**

        rm -f .sync-pause
        ls -la .sync-pause || echo "解除済み"

| Phase F 完了判定 | 期待 |
|---|---|
| RESULT に 4 点が記載されている | あり |
| 受け皿への起票 | あり。`runindex/` は無変更 |
| Phase A から E の全項目に値が対応 | あり |
| 作業ツリーの変更が `tasks/` 配下のみ | あり |
| `.sync-pause` が削除されている | あり |

---

## 想定外が起きたときの扱い

| 事象 | 扱い |
|---|---|
| データ実体が本ホストに無い | Phase B と C を `UNKNOWN` とし、Phase D と E は続行する。**実行できなかった検査を明記する** |
| 期待値と実測が食い違う | **実測を採る。** 期待値の側が誤りである可能性を書く |
| 実装が SPEC の記述と食い違う | **実装に従う。** SPEC のどの記述が誤っていたかを書く |
| 列名が存在しない | 推測で代替しない。実在する列名を出力してから使い、記録する |
| 陽性対照が働かない | **G2 と G3 は `stop`。** 何が起きたかを記録して停止する |
| 常駐処理が作業分岐へ統合を行った | **実行者の逸脱ではない。事実として記録する** |
| 画像走査が長い | 数分かかりうる。中断せず待つ。10 分を超えるなら件数を記録して分割する |
| 検査に変更が必要になった | **本 task は読み取りのみ。実施せず、必要な変更内容を受け皿へ起票する** |

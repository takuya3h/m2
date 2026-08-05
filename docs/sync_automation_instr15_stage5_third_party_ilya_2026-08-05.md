# 指示書 #15 段 5 — `third_party/` 同期の設計案（調査のみ・実装なし）

| | |
|---|---|
| 実施 | ilya（hostname `aolab` / `SERVERNAME=ilya`）, 2026-08-05 |
| ブランチ | `feat/sync-automation-20260805` |
| 種別 | **調査と設計案の提示のみ。実装は一切なし** |
| 一次データ | 変更 0 件 |
| `.stignore` / `.gitignore` | 変更 0 件 |
| 検証用に行った操作 | `/tmp` に upstream リポジトリを一時 clone → 検証後に削除済み |

---

## 0. 背景

`third_party/` は `.gitignore:132-133` と `.stignore:35` の両方で除外され、
git にも Syncthing にも乗らない。各サーバーが独立に clone している。

2026-08-02〜04 の全台調査で判明した実態:

| host | `.git` | 独自実装 | 備考 |
|---|:--:|---:|---|
| **philip** | あり | **9 fork / 42 file** | S0 の 4 fork（Mr.DETR / Stable-DINO / DI-MaskDINO / Co-DETR）が**ここにしかない** |
| efros | あり | 31 | Relation-DETR |
| lecun | あり | 28 | Relation-DETR + detrex |
| Bengio | なし | 22（mtime 推定） | バージョン記録不能 |
| ilya / Andrew | — | 0 | checkpoints のみ |
| he / adam / hinton / ian / dlsta | なし | 0 | checkpoints のみ（2.1G） |

既に `third_party_snapshot/<host>/` が 5 ホスト分あり（philip / efros / lecun /
Bengio / Andrew）、patch + tarball + provenance の形式で保全済み。

---

## 1. 調査結果

### 1.1 Syncthing の除外構文で入れ子 `.git` を落とせるか

```
syncthing v2.1.2 "Hafnium Hornet"
.stignore:9   .git          ← パス区切りなしの単独パターン
.stignore:3   コメント: 「先にマッチした行が勝つ」
```

**判定: 落とせる。既存の `.git` ルール（9 行目）が既に入れ子の `.git` にも効く設計。**

gitignore 系記法ではパス区切りを含まないパターンは深さを問わず basename
マッチする。ファイル冒頭のコメントが「先にマッチした行が勝つ」と明記しており、
`third_party/**` を後段に許可追加しても `.git` 除外が先に評価されて勝つ。

⚠️ **ilya には third_party 配下に `.git` を持つリポジトリが 1 つも無く、
この host では実地の再現確認ができなかった。** 根拠は①設計コメント自体の
明記、②philip の snapshot README にも同じ設計判断が記録されている、の 2 点。
**推論であり実証ではない。** philip / efros / lecun での再検証を推奨。

#### 受け手側で何が起きるか — 壊れる／壊れないの境界

```
.git が正しく除外された場合  → 作業ツリーのみ届く（.git 無し）= Bengio の現状と同じ
                                「壊れる」のではなく「劣化した状態」
                                （provenance 喪失・diff/commit 不能。クラッシュはしない）
.git 除外が壊れた場合        → .git 内部ファイルが部分的に同期され、
                                受け手側の既存 git リポジトリの
                                オブジェクト DB / ref が汚染される
                                → これが唯一の「本当に壊れる」経路
```

境界は「`.git` 除外ルールが将来編集で壊れないか」に尽きる。`.stglobalignore`
は phase0 上の編集が 30 分以内に全台へ自動反映される設計（`keeper.sh:30-31`）
なので、**1 回のタイプミスが 11 台同時に波及する**。実 git リポジトリを持つ
philip / efros / lecun の 3 台が被害を受ける。

### 1.2 snapshot の現状

```
Andrew   8.0K（provenance のみ、ソース無し）
Bengio   48K
efros    60K
lecun    80K
philip   212K（9 fork 分）
```

philip の README（`third_party_snapshot/philip/README.md`）が設計意図と
限界を明記している。

> これは保全用スナップショットであり、正式な管理方法ではない。
> サブモジュール化 / `src/` への移設 / 別リポジトリ化のいずれにするかは、
> 全サーバーの報告が揃ってから決定する。
> **このスナップショットから直接ビルド・実行することを想定していない。**

#### 復元可能性 — 実測で確認

Relation-DETR（philip 分）で patch + tarball の完全復元テストを実施した。

```
1. git clone --depth 50 https://github.com/xiuqhou/Relation-DETR.git
   → 成功（ネットワーク到達可）
2. git checkout b485955c72452788240600da6d0f0b8cc49f33c7
   → snapshot 記録の commit と完全一致
3. git apply --check upstream_mods.patch
   → exit 0（適合）
4. git apply upstream_mods.patch
   → 成功
5. tar xzf project_files.tar.gz
   → 成功（8 ファイル、configs/ 含む）
```

**復元手順は README に文書化されていたが、「実行して確認する」検証は
今回が初めて**（README 自体が「実行を想定していない」と書いていたため）。
一時 clone は検証後に削除済み。

#### 更新検出の仕組み

```
grep -rn 'third_party_snapshot' scripts/ tools/   → ヒット 0 件
m2-sync.sh の third_party 言及                     → 0 件
```

現在は完全に手動。snapshot 作成は 2026-08-02〜03 の 1 回のみで、
それ以降の `third_party/` の変更を検出する仕組みは存在しない。

### 1.3 submodule 化の可能性

ilya には third_party のソース実体が無いため `git remote -v` を直接
実行できず、snapshot の `provenance.txt` から origin を確認した。

```
Mr.DETR       : https://github.com/Visual-AI/Mr.DETR.git       ← upstream 本家
Relation-DETR : https://github.com/xiuqhou/Relation-DETR.git   ← upstream 本家
Co-DETR       : https://github.com/Sense-X/Co-DETR.git         ← upstream 本家
```

🔴 **判定: 9 fork すべてが upstream 直接 clone であり、team 管理の fork ではない。**

submodule は「ある remote の、ある commit」を指すだけなので、remote が
upstream（push 権限なし）である以上、**submodule はその upstream の commit
しか指せない。**

```
philip の 9 fork 中 upstream 改変あり : 4 本（DAC-DETR / DI-MaskDINO / Relation-DETR / detrex）
未追跡の独自実装                      : 42 file（全ホスト合計では 100+ file）
```

これらの patch と未追跡ファイルは submodule に一切乗らない。submodule 化
するには、まず team 管理の fork（例: `takuya3h/Relation-DETR`）を新規作成し、
patch を commit として積み、未追跡ファイルも commit してから push する
必要がある。

さらに **同一 upstream commit でもホスト間で中身が違う**ことが既に判明
している（Relation-DETR: efros dirty 35 / lecun dirty 25 / philip dirty 8、
同じ `b485955` 上で）。submodule は 1 commit しか指せないため、**どのホストの
variant を正とするかの統合作業**が事前に必要。

---

## 2. 4 案の比較

| | (a) Syncthing 部分同期 | (b) snapshot 自動化 | (c) submodule 化 | (d) 配らない・drift 検出 |
|---|---|---|---|---|
| **実現可能性** | 技術的には可能（`.git` は既存ルールで除外済み）。ただし**大容量 checkpoint も一緒に配ってしまう** | 可能。`m2-sync.sh` に検出ロジックを足すだけ | **困難**。upstream 直接 clone のため、まず 9+ 本の team fork を新規作成し patch/未追跡ファイルを commit する前段作業が要る | 容易。検出のみで配布ロジック自体を作らない |
| **既存 5 ホスト snapshot との関係** | **不要になる**（実体が届くため） | **そのまま活かす**。既存形式を自動生成に流用 | **土台として使えるが加工が要る**（1 と同じ理由） | **そのまま活かす**。むしろ本来の使い方に近い |
| **作業量** | 中〜大。`.stignore` 編集は数行だが 11 台の容量・帯域への影響評価が別途必要 | 小〜中。検出+コミットロジックを追加。4 ホスト分の初回テストが要る | **大**。9 fork の team 化・履歴統合・全ホスト `.gitmodules` 設定・4 台 variant 統合判断 | **小**。検出ロジックのみ（(b) の縮小版） |
| **🔴 最悪ケース** | `.stglobalignore` の将来編集ミスで `.git` 除外が壊れ、**philip/efros/lecun の実 git リポジトリのオブジェクト DB が汚染される**（3 台同時・30 分で伝播） | 自動 commit のバグで**間違った内容が snapshot として記録される**（実体は破壊しない） | 履歴統合ミスで**4 台のうちどれかの variant が消える** | 何も壊れない（検出のみ） |
| **復旧可能性** | **壊れたホストは再 clone すれば復旧**。ただし気づくまでの間、当該ホストでの commit/push が全部失敗する | 常に復旧可能（git 管理下） | 復旧可能だが元のホストのディスク実体が無ければ喪失 | 該当なし |

---

## 3. 推奨: **(d) を主軸に、(b) の自動化を薄く足す**

### 3.1 理由

1. **「配る」前提そのものが疑わしい。** `third_party/` を実際に使っているのは
   4 台（lecun / efros / philip / Andrew）のみ。残り 7 台は checkpoints しか
   持たず、S0 検出 run を再実行する予定が無い限り source は不要。
2. **(a) は費用対効果が悪い。** `.git` 除外自体は安全に実現できるが、
   checkpoint（ilya だけでも 195MB × 数個）を 11 台に配ると現状 2.1G/ホスト
   （checkpoints のみの 7 台）が数倍に膨らむ。被害範囲（実 git リポジトリを
   持つ 3 台）に対する「1 回のタイプミスで同時汚染」というリスクに見合わない。
3. **(c) は「正統」だが今のタイミングでは早すぎる。** team fork を新規作成
   する前段作業が必須（指示書は条件付き懸念だったが、実測の結果その条件が
   現実に成立していた）。4 台の variant 統合という研究上の判断を先に
   済ませないと着手できない。

### 3.2 (d) + (b) の具体像（実装しない・提案のみ）

- 配布はしない。現状の「各ホストが独立に clone」を維持。
- `m2-sync.sh` に、**third_party を使う 4 台限定**で「ディスク上の実体と
  `third_party_snapshot/<host>/` の provenance がずれていないか」を検出する
  チェックを追加（commit ハッシュの diff のみ、軽量）。
- ずれを検出したら `sync-alerts.log` にアラート（人間が snapshot 更新を判断）。
- **snapshot の更新自体は自動 commit にしない**（絶対規則 3 と同じ理由 —
  実装は生成物だが、何を「正」とするかは研究上の判断）。

---

## 4. 判断に迷った点

### 4.1 `.git` 除外の安全性を実地で再現できなかった

ilya に third_party のソース実体が無いため、`.git` 除外ルールが実際に
入れ子ディレクトリに効くかをこの host では検証できない。設計コメントと
philip の README から論理的に導いているが、**philip か efros か lecun での
再検証を推奨する**（3 台とも実 `.git` を持つため）。

### 4.2 checkpoint の容量影響を定量化できなかった

third_party 配下の checkpoint 総量（4 台 × 各 fork）は今回の調査対象外。
案 (a) の「作業量」評価に必要な数字だが、**全台の `du` が無いと出せない。**

### 4.3 案 (d) の「検出」の粒度

commit ハッシュだけで比較するか、patch+untracked ファイルの内容まで
ハッシュ比較するかで実装量が変わる。前者は軽量だが「同じ commit でも
dirty 内容が違う」実態（efros dirty 35 / lecun dirty 25）を見逃す。
実装に入る前に確認が必要な設計判断。

---

## 5. 実施内容の確認

すべて読み取り専用。以下は行っていない。

- `.stignore` / `.gitignore` の変更
- `third_party_snapshot/` の変更
- `m2-sync.sh` への third_party 関連コードの追加
- GPU への接触

検証で行った `git clone`（1 回、`/tmp` 配下、upstream リポジトリの
public read のみ）は完了後に削除済み。

## 6. 現在の状態

```
ブランチ  : feat/sync-automation-20260805
作業ツリー: 追跡変更 0 件 / 未追跡 3 件（_smoke_* の除外規約該当）
PR        : #41（Draft・段 2〜4 の実装。未マージ）
```

## 7. 次の段（未着手）

- **段 6**: GitHub の auto-merge 設定（人間が Web UI で実施）
- **段 7**: `.servername` の全台配布、PR #41 の扱い

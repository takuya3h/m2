# ホスト間の索引の差（2026-08-10）

## 実測

| ホスト | run 数 | 識別子を持つ行 | 退避物 | 測定日 |
|---|---:|---:|---:|---|
| lecun | 784 | 1 | 34 | 2026-08-07 |
| bengio | 751 | 2 | 0 | 2026-08-08 |

lecun の退避物34件は Git 追跡外のホスト固有ディレクトリである。bengio の0件は `index.csv` の全 path を `git ls-files --error-unmatch` で照合した結果であり、追跡外経路は無かった。

## このホストで生成した索引の性質

bengio で再生成した `index.csv` は 751 run で、全751行の path が Git 追跡下にある。除外理由の内訳は、理由なし703、`identity_check` 24、`smoke_test` 7、`known_bad_split` 6、`failed_run` 6、`wrong_frozen_source` 3、`mislabeled_arm_all_not_film` 2 だった。

再生成前749 run からの増分は2件である。統合で加わった `s0_040_wiring_verification_seed42` と、本 task が生成した `s0_041_wiring_verification_seed42` が各1件。削除0件、既存749行の変更0件だった。

CSVの物理行数は、`index.csv` 752、`experiments.csv` 208、`per_class.csv` 6241、`verdicts.csv` 1039。`index.csv` はヘッダー1行を含むため、run数は751である。

## 正本としての適否

bengio 生成版はホスト固有の追跡外退避物を含まず、749から751への増分を一次証跡2件で説明できるため、退避物を含まない正本候補としての条件を満たす。これを正本として採用するか、各ホストの差異を許容するかの最終判断は利用者へ委ねる。

## 依存導入の再現性

| ホスト | 仮想環境内の導入コマンド | 一括導入の結果 |
|---|---|---|
| lecun | pipなし。uvを使用 | 2回とも exit 0。2回目はeditable再登録のみ |
| bengio | pipなし。uvを使用 | 2回とも exit 0。パッケージ一覧の事前事後差分なし |

bengio では `jsonschema` と `yaml` の読み込み成功、`torch 2.1.2+cu118` の不変も確認した。

## 自動同期の再現性

| ホスト | 鍵の種類 | 自動記録 | 自動送出 | 起票 |
|---|---|---|---|---|
| lecun | 配備鍵 | 成功。commit `25ea5ef` | 成功 | 常駐スクリプトが PR 51 を起票。Actionsは401で失敗 |
| bengio | 通常のSSH鍵 | 成功。commit `5f7e255` | 成功。遠隔との差0 | 最終task送出後に常駐スクリプトが PR 53 を起票。Actionsは無効なトークンで失敗 |

bengio の学習直後と索引再生成後の確認では open PR は0件だった。最終 task commit の push から45秒後に Draft PR #53 が現れた。資格情報の値そのものには触れていない。

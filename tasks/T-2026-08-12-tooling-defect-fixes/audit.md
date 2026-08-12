# Phase A 修正前監査

## 1. 該当実装

`tools/report_task.py`:

```text
73:def scan_secrets(text: str, env: dict[str, str] | None = None) -> list[str]:
125:def _rich_text(text: str) -> list[dict]:
```

修正前の判定式:

```python
("W&B の鍵らしい 40 桁", re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")),
("鍵らしい代入", re.compile(
    r"\b[A-Za-z_]*(?:API_KEY|SECRET|TOKEN|PASSWORD|PASSPHRASE)[A-Za-z_]*\s*[:=]\s*['\"]?\S{12,}"
)),
chunks = [text[i:i + RICH_TEXT_LIMIT] for i in range(0, len(text), RICH_TEXT_LIMIT)] or [""]
```

`tools/check_spec.py` と固定契約参照:

```text
296:def rule_host_mismatch(c: Contract) -> list[Finding]:
307:    actual = socket.gethostname()
318:                    "host_mismatch",
tests/test_check_spec.py:34:SELF_TASK = "T-2026-08-11-issuer-defect-detector"
tests/test_preflight_task.py:137:SELF_TASK = "T-2026-08-11-issuer-defect-detector"
```

## 2. 秘匿検査の修正前実測

本物の資格情報を使わず、`env={}` と明らかな囮文字列で測定した。

```text
hex40_should_pass -> ['W&B の鍵らしい 40 桁（1 行目・値は伏せる）']
notion_should_stop -> ['鍵らしい代入（1 行目・値は伏せる）']
wandb_should_stop -> ['鍵らしい代入（1 行目・値は伏せる）']
dash_should_stop -> []
password_should_stop -> []
plain_should_pass -> []
```

契約前提との比較:

- `hex40_should_pass` の偽陽性は再現した。
- `dash_should_stop` と小文字 `password_should_stop` の偽陰性は再現した。
- `notion_should_stop` と `wandb_should_stop` は修正前実装でも検出され、契約記載の「三通りとも取りこぼす」は再現しなかった。

## 3. rich_text 切片の修正前実測

```text
0 codepoints=2000 utf16units=2010
1 codepoints=10 utf16units=20
joined_equals_original True
```

UTF-16 で 2,000 単位を超える切片があり、単位の食い違いは再現した。

## 4. ホスト警告と試験の修正前実測

```text
P9 spec_lint              PASS 規則 8 件を検査し該当なし
preflight_exit=0
```

本契約のプリフライトでは `host_mismatch` は再現しなかった。実ホスト名は次のとおり。

```text
efros
```

対象試験の結果:

```text
FAILED tests/test_check_spec.py::test_self_contract_has_no_hit - AssertionErr...
FAILED tests/test_preflight_task.py::test_spec_lint_passes_on_clean_contract
2 failed, 35 passed in 3.74s
pytest_exit=1
```

固定 `SELF_TASK` に起因する 2 件の失敗は再現した。

## 5. G1 判定

起票者訂正後の G1 は「再現した項目について修正前後で結果が変わること」とする。

- `NOTION_API_KEY` と `WANDB_API_KEY` は修正前から検出される。欠陥ではなく回帰対照へ変更する。
- 実際の取りこぼしは `api-key` と小文字 `password` であり、修正対象とする。
- 自然な本契約ではホスト名が同じ小文字なので警告は出ない。人工入力による陽性対照を追加した。

人工入力の修正前実測:

```text
case_only declared=Efros actual=efros hits=1 ['host_mismatch']
other_host declared=definitely-not-this-host actual=efros hits=1 ['host_mismatch']
temporary_exists_after False
```

大小文字だけが異なる宣言で偽陽性を再現し、別ホストでも警告が出ることを確認した。一時契約は測定後に残っていない。訂正版 G1 を通過し、再現した項目の修正へ進む。

## 6. 追加試験を旧実装へ当てた結果

道具本体を変更する前に回帰試験を追加し、旧実装で次の 6 件が失敗した。

```text
hex40_should_pass: FAIL
dash_should_stop: FAIL
lower_password_stop: FAIL
UTF-16 境界: FAIL 2 件
host_mismatch の大小文字対照: FAIL
6 failed, 58 passed
pytest_exit=1
```

## 7. 秘匿検査の修正後実測

```text
hex40_should_pass stop=False expected=False pass=True []
plain_should_pass stop=False expected=False pass=True []
dash_should_stop stop=True expected=True pass=True ['鍵らしい代入（1 行目・値は伏せる）']
lower_password_stop stop=True expected=True pass=True ['鍵らしい代入（1 行目・値は伏せる）']
notion_should_stop stop=True expected=True pass=True ['鍵らしい代入（1 行目・値は伏せる）']
wandb_should_stop stop=True expected=True pass=True ['鍵らしい代入（1 行目・値は伏せる）']
report_like stop=False expected=False pass=True []
all_seven_pass True
```

七件すべてが訂正後の期待どおりである。名前だけの `password` を含む報告文は通り、代入と値が続く小文字 `password` は止まる。

## 8. rich_text 切片の修正後実測

```text
task1_original chunks=2 utf16units=[2000, 30] max=2000 joined=True
astral_only chunks=2 utf16units=[2000, 2] max=2000 joined=True
astral_at_boundary chunks=2 utf16units=[1999, 3] max=1999 joined=True
bmp_only chunks=3 utf16units=[2000, 2000, 501] max=2000 joined=True
```

四入力すべてで各切片は UTF-16 2,000 単位以下で、連結結果は元本文と一致した。

## 9. ホスト比較の修正後実測

```text
case_only declared=Efros actual=efros hits=0 []
other_host declared=definitely-not-this-host actual=efros hits=1 ['host_mismatch']
temporary_exists_after False
P9 spec_lint              PASS 規則 8 件を検査し該当なし
```

大小文字だけの差は通り、別ホストは引き続き検出された。一時契約は残っていない。

## 10. 試験結果

近接試験の修正後:

```text
64 passed in 1.19s
pytest_exit=0
```

全試験の修正後:

```text
5 failed, 430 passed, 4 skipped, 10 warnings in 40.33s
pytest_exit=1
```

`origin/phase0` の一時 worktree に同じ `.venv` を接続して測った修正前全体:

```text
7 failed, 407 passed, 14 skipped, 10 warnings in 30.75s
pytest_exit=1
```

一時 worktree は測定後に削除した。データ manifest の有無により pass / skip 数は現行 repo と
異なるため比較に使わず、失敗内訳を比較した。修正前の対象 2 失敗は消え、残存 5 件は不変だった。
内訳は次のとおり。

- `tests/test_engines.py` 1 件: 既存 S0 証跡の `score_thr=0.0` と試験期待 `1e-8` の不一致。
- `tests/test_research_logger.py` 4 件: 空または欠落した `metrics.json` を completed として投稿しない現行実装と、投稿を期待する試験の不一致。

## 11. 実地送信

同期抑止を解除し、認証環境を読み込んだ同一コマンドで `make task-report` を実行した。

```text
released
repo 直下から消えた
verdict=pass
n_issuer_defects=2
replaced_blocks=0
exit=0
```

資格情報の値は出力・記録していない。本契約で修正した秘匿検査と UTF-16 分割を通る最初の実地送信に成功した。

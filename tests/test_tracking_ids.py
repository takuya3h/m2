"""外部記録（W&B）の識別子を証跡へ書く経路の試験。

外部サービスへは接続しない。``tracking._run`` へ偽の run を差し込んで、
書く / 書かない / 落ちない / 秘匿を漏らさない の 4 点だけを見る。
"""
from __future__ import annotations

import json

import pytest

from egosurgery.utils import tracking


class _FakeRun:
    """wandb.Run の代役。読む属性だけを持つ。"""

    def __init__(self, **kw):
        self.id = kw.get("id", "abc123xyz")
        self.url = kw.get("url", "https://wandb.ai/acme/egosurgery_multitask/runs/abc123xyz")
        self.project = kw.get("project", "egosurgery_multitask")
        self.entity = kw.get("entity", "acme")
        self.name = kw.get("name", "s0_001_probe_seed42")


@pytest.fixture
def restore_run():
    """テストが _run を汚したまま終わらないようにする。"""
    before = tracking._run
    yield
    tracking._run = before


def test_records_identifier_when_enabled(tmp_path, restore_run):
    """外部記録が有効なとき、識別子が証跡へ渡る。"""
    tracking._run = _FakeRun()

    assert tracking.record_run_identity(tmp_path) is True

    path = tmp_path / tracking.RUN_IDENTITY_FILE
    assert path.exists(), "有効なのに証跡が書かれていない"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["run_id"] == "abc123xyz"
    assert data["run_url"].endswith("/runs/abc123xyz")
    assert data["project"] == "egosurgery_multitask"
    assert data["entity"] == "acme"


def test_records_nothing_when_disabled(tmp_path, restore_run):
    """無効なときは何も書かない。空文字も書かない。"""
    tracking._run = None

    assert tracking.record_run_identity(tmp_path) is False

    path = tmp_path / tracking.RUN_IDENTITY_FILE
    assert not path.exists(), "無効なのに証跡が作られている（空欄と区別できなくなる）"
    # ディレクトリ自体を汚していないこと。
    assert list(tmp_path.iterdir()) == []


def test_no_identifier_writes_nothing(tmp_path, restore_run):
    """run はあるが id を取れない場合も書かない（中途半端な証跡を残さない）。"""
    run = _FakeRun()
    run.id = None
    tracking._run = run

    assert tracking.record_run_identity(tmp_path) is False
    assert not (tmp_path / tracking.RUN_IDENTITY_FILE).exists()


def test_failure_does_not_stop_training(tmp_path, restore_run):
    """外部記録の取得に失敗しても例外を投げない。"""

    class _Exploding:
        @property
        def id(self):
            raise RuntimeError("wandb backend down")

    tracking._run = _Exploding()

    # 例外が漏れれば学習が止まる。False を返して黙って続くこと。
    assert tracking.record_run_identity(tmp_path) is False

    # 書けない場所を渡した場合も同様。
    tracking._run = _FakeRun()
    assert tracking.record_run_identity(tmp_path / "does" / "not" / "exist") is False


def test_no_credentials_in_output(tmp_path, restore_run, monkeypatch):
    """資格情報が出力に含まれない。"""
    secret = "wandbsecret0123456789abcdef0123456789abcd"
    monkeypatch.setenv("WANDB_API_KEY", secret)

    run = _FakeRun()
    # run 側に資格情報様の属性がぶら下がっていても拾わないこと。
    run.api_key = secret
    run.settings = {"api_key": secret}
    tracking._run = run

    assert tracking.record_run_identity(tmp_path) is True
    text = (tmp_path / tracking.RUN_IDENTITY_FILE).read_text(encoding="utf-8")
    assert secret not in text
    assert "api_key" not in text
    # 書かれるキーは想定した 5 つだけ。
    assert set(json.loads(text)) <= {"run_id", "run_url", "project", "entity", "run_name"}


def test_init_writes_nothing_when_disabled(tmp_path, monkeypatch, restore_run):
    """init() が no-op のとき、exp_dir を渡しても証跡は作られない。"""
    monkeypatch.delenv("WANDB_API_KEY", raising=False)
    tracking._run = None

    assert tracking.init("probe", exp_dir=tmp_path) is None
    assert not (tmp_path / tracking.RUN_IDENTITY_FILE).exists()

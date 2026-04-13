import sys

import pytest

from batch import run_like


class DummyConn:
    def __init__(self):
        self.commit_called = False
        self.closed = False

    def commit(self):
        self.commit_called = True

    def close(self):
        self.closed = True


def test_main_saves_like_when_not_exists(monkeypatch, capsys):
    article_id = 123

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    def fake_check_like_exists(conn, aid):  # noqa: ARG001
        # まだ存在していない
        assert aid == article_id
        return 0

    saved_ids = []

    def fake_save_like(conn, aid):  # noqa: ARG001
        saved_ids.append(aid)

    monkeypatch.setattr(run_like, "get_conn", fake_get_conn)
    monkeypatch.setattr(run_like, "check_like_exists", fake_check_like_exists)
    monkeypatch.setattr(run_like, "save_like", fake_save_like)

    run_like.main(article_id)

    out = capsys.readouterr().out

    # メッセージが出力されること
    assert f"記事ID {article_id} にいいねを保存しました" in out

    # DB接続、commit、close が行われること
    assert len(conns) == 1
    assert conns[0].commit_called is True
    assert conns[0].closed is True

    # save_like が正しい article_id で1回呼ばれていること
    assert saved_ids == [article_id]


def test_main_does_nothing_when_like_exists(monkeypatch, capsys):
    article_id = 456

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    def fake_check_like_exists(conn, aid):  # noqa: ARG001
        # 既に1件存在している
        assert aid == article_id
        return 1

    def fake_save_like(conn, aid):  # noqa: ARG001
        raise AssertionError("save_like should not be called when like exists")

    monkeypatch.setattr(run_like, "get_conn", fake_get_conn)
    monkeypatch.setattr(run_like, "check_like_exists", fake_check_like_exists)
    monkeypatch.setattr(run_like, "save_like", fake_save_like)

    run_like.main(article_id)

    out = capsys.readouterr().out

    # 既に存在する場合は何も出力しない仕様
    assert out == ""

    # DB接続は1回だけ、commit は呼ばれず close は呼ばれる
    assert len(conns) == 1
    assert conns[0].commit_called is False
    assert conns[0].closed is True


def test_main_raises_system_exit_on_exception(monkeypatch, capsys):
    article_id = 789

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    def fake_check_like_exists(conn, aid):  # noqa: ARG001
        # 何らかの例外が発生したケースをシミュレート
        raise RuntimeError("DB error")

    monkeypatch.setattr(run_like, "get_conn", fake_get_conn)
    monkeypatch.setattr(run_like, "check_like_exists", fake_check_like_exists)

    with pytest.raises(SystemExit) as excinfo:
        run_like.main(article_id)

    # sys.exit(1) が呼ばれていること
    assert excinfo.value.code == 1

    # 標準エラー出力にエラーメッセージが出ていること
    captured = capsys.readouterr()
    assert "Error during like operations:" in captured.err
    assert "DB error" in captured.err

    # 例外発生時でもコネクションは close されていること
    assert len(conns) == 1
    assert conns[0].closed is True

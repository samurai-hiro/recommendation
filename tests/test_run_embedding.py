import pytest

from batch import run_embedding


class DummyConn:
    def __init__(self):
        self.commit_called = False
        self.closed = False

    def commit(self):
        self.commit_called = True

    def close(self):
        self.closed = True


def test_main_saves_embeddings(monkeypatch, capsys):

    # embeddings が空の記事を2件返す想定
    articles = [
        {"id": 1, "content": "a"},
        {"id": 2, "content": "b"},
    ]

    def fake_get_article_empty_embedd(conn):  # noqa: ARG001
        return articles

    # generate_embeddings がダミーの埋め込み2件を返す
    embeddings = [
        {"id": 1, "embedding": b"x"},
        {"id": 2, "embedding": b"y"},
    ]

    def fake_generate_embeddings(arts):  # noqa: ARG001
        return embeddings

    saved = []

    def fake_save_embeddings(conn, emb):  # noqa: ARG001
        saved.append(list(emb))

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    monkeypatch.setattr(run_embedding, "get_article_empty_embedd", fake_get_article_empty_embedd)
    monkeypatch.setattr(run_embedding, "generate_embeddings", fake_generate_embeddings)
    monkeypatch.setattr(run_embedding, "save_embeddings", fake_save_embeddings)
    monkeypatch.setattr(run_embedding, "get_conn", fake_get_conn)

    run_embedding.main()

    out = capsys.readouterr().out

    # 2件保存メッセージ
    assert "2件の記事のembeddingsを保存しました。" in out

    # DB 接続と commit/close
    assert len(conns) == 1
    assert conns[0].commit_called is True
    assert conns[0].closed is True

    # save_embeddings が1回呼ばれ、埋め込み2件を受け取っている
    assert len(saved) == 1
    assert saved[0] == embeddings


def test_main_no_empty_articles(monkeypatch, capsys):

    def fake_get_article_empty_embedd(conn):  # noqa: ARG001
        # 空リスト -> embeddings が空の記事は無し
        return []

    def fake_generate_embeddings(arts):  # noqa: ARG001
        raise AssertionError("generate_embeddings should not be called")

    def fake_save_embeddings(conn, emb):  # noqa: ARG001
        raise AssertionError("save_embeddings should not be called")

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    monkeypatch.setattr(run_embedding, "get_article_empty_embedd", fake_get_article_empty_embedd)
    monkeypatch.setattr(run_embedding, "generate_embeddings", fake_generate_embeddings)
    monkeypatch.setattr(run_embedding, "save_embeddings", fake_save_embeddings)
    monkeypatch.setattr(run_embedding, "get_conn", fake_get_conn)

    run_embedding.main()

    out = capsys.readouterr().out

    # 空の記事がないメッセージ
    assert "embeddingsが空の記事はありませんでした。" in out

    # DB は1回開かれ、commit は呼ばれず close は呼ばれる
    assert len(conns) == 1
    assert conns[0].commit_called is False
    assert conns[0].closed is True


def test_main_raises_system_exit_on_exception(monkeypatch, capsys):
    # embeddings が空の記事取得時に例外が発生するケースをシミュレート

    def fake_get_article_empty_embedd(conn):  # noqa: ARG001
        raise RuntimeError("DB error")

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    monkeypatch.setattr(run_embedding, "get_article_empty_embedd", fake_get_article_empty_embedd)
    monkeypatch.setattr(run_embedding, "get_conn", fake_get_conn)

    with pytest.raises(SystemExit) as excinfo:
        run_embedding.main()

    # sys.exit(1) が呼ばれていること
    assert excinfo.value.code == 1

    # 標準エラー出力にエラーメッセージが出ていること
    captured = capsys.readouterr()
    assert "Error during embedding operations:" in captured.err
    assert "DB error" in captured.err

    # 例外発生時でもコネクションは close されていること
    assert len(conns) == 1
    assert conns[0].closed is True

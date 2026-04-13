import pytest

from batch import run_crawler


class DummyConn:
    def __init__(self):
        self.commit_called = False
        self.closed = False

    def commit(self):
        self.commit_called = True

    def close(self):
        self.closed = True


def test_main_saves_new_articles(monkeypatch, capsys):

    urls = ["https://example.com/1", "https://example.com/2"]

    def fake_get_article_links():
        return urls

    def fake_get_article_content(url):  # noqa: ARG001
        # URLごとに記事辞書を返す（最低限必要なキーのみ）
        return {
            "title": f"title-{url[-1]}",
            "content": f"content-{url[-1]}",
            "url": url,
            "published_at": "2024-01-01 00:00:00",
        }

    def fake_existing_articles(conn):  # noqa: ARG001
        # 既存記事は無い想定
        return set()

    unique_articles = [
        {
            "title": "title-1",
            "content": "content-1",
            "url": "https://example.com/1",
            "published_at": "2024-01-01 00:00:00",
        }
    ]

    received_new_articles = {}

    def fake_check_duplicate(existing, new_articles):  # noqa: ARG001
        # 渡された新着記事を記録して、1件だけユニークとみなす
        received_new_articles["value"] = list(new_articles)
        return unique_articles

    article_insert_calls = []

    def fake_article_insert(conn, articles):  # noqa: ARG001
        article_insert_calls.append(list(articles))

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    # 依存関係をモック
    monkeypatch.setattr(run_crawler, "get_article_links", fake_get_article_links)
    monkeypatch.setattr(run_crawler, "get_article_content", fake_get_article_content)
    monkeypatch.setattr(run_crawler, "existing_articles", fake_existing_articles)
    monkeypatch.setattr(run_crawler, "check_duplicate", fake_check_duplicate)
    monkeypatch.setattr(run_crawler, "article_insert", fake_article_insert)
    monkeypatch.setattr(run_crawler, "get_conn", fake_get_conn)

    run_crawler.main()

    out = capsys.readouterr().out

    # 1件保存メッセージが出ていること
    assert "1件の記事を保存しました。" in out

    # DB接続とコミット・クローズが行われていること
    assert len(conns) == 1
    assert conns[0].commit_called is True
    assert conns[0].closed is True

    # article_insert がユニーク記事を1回だけ受け取っていること
    assert len(article_insert_calls) == 1
    assert article_insert_calls[0] == unique_articles

    # check_duplicate に渡された new_articles が get_article_content の結果になっていること
    assert "value" in received_new_articles
    assert len(received_new_articles["value"]) == len(urls)
    assert {a["url"] for a in received_new_articles["value"]} == set(urls)

def test_main_no_new_articles(monkeypatch, capsys):
    urls = ["https://example.com/1"]

    def fake_get_article_links():
        return urls

    def fake_get_article_content(url):  # noqa: ARG001
        return {
            "title": "title-1",
            "content": "content-1",
            "url": "https://example.com/1",
            "published_at": "2024-01-01 00:00:00",
        }

    def fake_existing_articles(conn):  # noqa: ARG001
        return {"https://example.com/1"}

    def fake_check_duplicate(existing, new_articles):  # noqa: ARG002
        # すべて既存とみなし、ユニーク記事はなし
        return []

    article_insert_calls = []

    def fake_article_insert(conn, articles):  # noqa: ARG001
        article_insert_calls.append(list(articles))

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    monkeypatch.setattr(run_crawler, "get_article_links", fake_get_article_links)
    monkeypatch.setattr(run_crawler, "get_article_content", fake_get_article_content)
    monkeypatch.setattr(run_crawler, "existing_articles", fake_existing_articles)
    monkeypatch.setattr(run_crawler, "check_duplicate", fake_check_duplicate)
    monkeypatch.setattr(run_crawler, "article_insert", fake_article_insert)
    monkeypatch.setattr(run_crawler, "get_conn", fake_get_conn)

    run_crawler.main()

    out = capsys.readouterr().out

    # 「新しい記事はありませんでした。」メッセージ
    assert "新しい記事はありませんでした。" in out

    # DB接続は1回されているが、コミットは呼ばれていない
    assert len(conns) == 1
    assert conns[0].commit_called is False
    assert conns[0].closed is True

    # article_insert は呼ばれていない
    assert article_insert_calls == []


def test_main_raises_system_exit_on_exception(monkeypatch, capsys):
    urls = ["https://example.com/1"]

    def fake_get_article_links():
        return urls

    def fake_get_article_content(url):  # noqa: ARG001
        return {
            "title": "title-1",
            "content": "content-1",
            "url": "https://example.com/1",
            "published_at": "2024-01-01 00:00:00",
        }

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    def fake_existing_articles(conn):  # noqa: ARG001
        # DBエラーなどを想定して例外を送出
        raise RuntimeError("DB error")

    monkeypatch.setattr(run_crawler, "get_article_links", fake_get_article_links)
    monkeypatch.setattr(run_crawler, "get_article_content", fake_get_article_content)
    monkeypatch.setattr(run_crawler, "existing_articles", fake_existing_articles)
    monkeypatch.setattr(run_crawler, "get_conn", fake_get_conn)

    with pytest.raises(SystemExit) as excinfo:
        run_crawler.main()

    # sys.exit(1) が呼ばれていること
    assert excinfo.value.code == 1

    # 標準エラー出力にエラーメッセージが出ていること
    captured = capsys.readouterr()
    assert "Error during crawling:" in captured.err
    assert "DB error" in captured.err

    # 例外発生時でもコネクションは close されていること
    assert len(conns) == 1
    assert conns[0].closed is True

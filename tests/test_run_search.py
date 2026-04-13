import pytest

from batch import run_search


class DummyConn:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_main_prints_results_using_search_articles2(monkeypatch, capsys):
    # ダミーの検索結果
    results = [
        {"title": "t1", "score": 90.0, "id": 1, "url": "u1", "liked": "liked"},
        {"title": "t2", "score": 80.0, "id": 2, "url": "u2", "liked": None},
    ]

    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    def fake_search_articles2(conn):
        # main が get_conn の戻り値を渡していることを確認
        assert isinstance(conn, DummyConn)
        return results

    # 依存関数をモック
    monkeypatch.setattr(run_search, "get_conn", fake_get_conn)
    monkeypatch.setattr(run_search, "search_articles2", fake_search_articles2)

    run_search.main()

    out = capsys.readouterr().out

    # ヘッダ行が出力されていること（クエリ文字列を含む）
    assert "クエリ:AIに対して類似度の高い記事" in out

    # 各結果行がタイトルやスコアを含んで出力されていること
    assert "タイトル: t1" in out
    assert "スコア: 90.0 %" in out
    assert "URL: u1" in out
    assert "liked: liked" in out

    assert "タイトル: t2" in out
    assert "スコア: 80.0 %" in out
    assert "URL: u2" in out
    # liked が None の場合もそのまま文字列化される
    assert "liked: None" in out

    # DB接続が1回だけ行われ、close されていること
    assert len(conns) == 1
    assert conns[0].closed is True


def test_main_no_results_prints_nothing(monkeypatch, capsys):
    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    def fake_search_articles2(conn):  # noqa: ARG001
        # 検索結果ゼロ件
        return []

    monkeypatch.setattr(run_search, "get_conn", fake_get_conn)
    monkeypatch.setattr(run_search, "search_articles2", fake_search_articles2)

    run_search.main()

    out = capsys.readouterr().out

    # 結果が空のときは何も表示されない（ヘッダも出ない）想定
    assert out == ""

    # DB接続は1回だけ行われ、close されている
    assert len(conns) == 1
    assert conns[0].closed is True


def test_main_raises_system_exit_on_exception(monkeypatch, capsys):
    conns = []

    def fake_get_conn():
        conn = DummyConn()
        conns.append(conn)
        return conn

    def fake_search_articles2(conn):  # noqa: ARG001
        # 検索処理中に例外が発生するケースをシミュレート
        raise RuntimeError("DB error")

    monkeypatch.setattr(run_search, "get_conn", fake_get_conn)
    monkeypatch.setattr(run_search, "search_articles2", fake_search_articles2)

    with pytest.raises(SystemExit) as excinfo:
        run_search.main()

    # 終了コードは1であること
    assert excinfo.value.code == 1

    captured = capsys.readouterr()

    # 標準エラーにエラーメッセージと原因が出力されていること
    assert "Error during search operations:" in captured.err
    assert "DB error" in captured.err

    # 例外時でもコネクションはクローズされていること
    assert len(conns) == 1
    assert conns[0].closed is True

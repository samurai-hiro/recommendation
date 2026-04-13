import sqlite3

import numpy as np
import pytest

from services import search


def _setup_db(conn):
    conn.execute(
        "CREATE TABLE articles (id INTEGER PRIMARY KEY, title TEXT, url TEXT, embeddings BLOB)"
    )
    conn.execute(
        "CREATE TABLE likes (article_id INTEGER)"
    )


class DummyEmbeddingObject:
    def __init__(self, vector):
        self.embedding = vector


class DummyEmbeddingData:
    def __init__(self, vector):
        self.data = [DummyEmbeddingObject(vector)]


class DummyOpenAIClient:
    def __init__(self, vector):
        self._vector = vector

        class _Embeddings:
            def __init__(self, outer):
                self._outer = outer

            def create(self, input, model):  # noqa: ARG002
                return DummyEmbeddingData(self._outer._vector)

        self.embeddings = _Embeddings(self)


def test_calculate_similarity_simple():
    # query: (1, 0), article: (1, 0) -> 100%
    query = np.array([1.0, 0.0], dtype=np.float32)
    article = np.array([1.0, 0.0], dtype=np.float32).tobytes()

    sim = search.calculate_similarity(query, article)

    assert sim == 100.0


def test_search_articles2_with_likes(tmp_path):
    db_path = tmp_path / "test_search2.db"
    conn = sqlite3.connect(db_path)
    try:
        _setup_db(conn)

        # ベクトル長は2次元とする
        v_like = np.array([1.0, 0.0], dtype=np.float32).tobytes()
        v_similar = np.array([0.9, 0.1], dtype=np.float32).tobytes()
        v_different = np.array([0.0, 1.0], dtype=np.float32).tobytes()

        # 記事を3つ用意
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings) VALUES (1, 't1', 'u1', ?)",
            (v_similar,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings) VALUES (2, 't2', 'u2', ?)",
            (v_different,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings) VALUES (3, 't3', 'u3', ?)",
            (v_like,),
        )

        # id=3 の記事にいいね
        conn.execute("INSERT INTO likes (article_id) VALUES (3)")
        conn.commit()

        results = search.search_articles2(conn, top_k=3)

        # liked 記事のembeddingがクエリの元になるので、id=3 に最も近い記事が高スコアになる
        assert len(results) == 3
        # 最初の要素が id=3 (自分自身) で、liked フラグ付き
        assert results[0]["id"] == 3
        assert results[0]["liked"] == "liked"
        # 2番目は id=1 (似ているベクトル)
        assert results[1]["id"] == 1
        # 3番目は id=2 (直交に近い)
        assert results[2]["id"] == 2

    finally:
        conn.close()


def test_search_articles2_no_likes(tmp_path):
    db_path = tmp_path / "test_search2_nolikes.db"
    conn = sqlite3.connect(db_path)
    try:
        _setup_db(conn)

        v1 = np.array([1.0, 0.0], dtype=np.float32).tobytes()
        v2 = np.array([0.0, 1.0], dtype=np.float32).tobytes()

        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings) VALUES (1, 't1', 'u1', ?)",
            (v1,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings) VALUES (2, 't2', 'u2', ?)",
            (v2,),
        )
        conn.commit()

        results = search.search_articles2(conn, top_k=10)

        # likes が無いので query_embedding は None -> score は全て 0
        assert len(results) == 2
        assert all(r["score"] == 0 for r in results)
        assert all(r["liked"] is None for r in results)

    finally:
        conn.close()


def test_search_articles_with_query_and_likes(tmp_path, monkeypatch):
    db_path = tmp_path / "test_search_query.db"
    conn = sqlite3.connect(db_path)
    try:
        _setup_db(conn)

        # クエリのembeddingを [1, 0] に固定
        query_vec = [1.0, 0.0]

        dummy_client = DummyOpenAIClient(query_vec)

        def fake_openai_client(api_key):  # noqa: ARG001
            return dummy_client

        monkeypatch.setattr(search, "OpenAI", fake_openai_client)

        # 記事embedding
        v_close = np.array([0.9, 0.1], dtype=np.float32).tobytes()
        v_far = np.array([0.0, 1.0], dtype=np.float32).tobytes()

        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings) VALUES (1, 'close', 'u1', ?)",
            (v_close,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings) VALUES (2, 'far', 'u2', ?)",
            (v_far,),
        )
        # id=1 にいいね
        conn.execute("INSERT INTO likes (article_id) VALUES (1)")
        conn.commit()

        results = search.search_articles(conn, query="dummy", top_k=2)

        assert len(results) == 2
        # クエリに近い id=1 が先頭
        assert results[0]["id"] == 1
        assert results[0]["title"] == "close"
        assert results[0]["liked"] == "liked"
        # 2番目は id=2
        assert results[1]["id"] == 2
        assert results[1]["liked"] is None

    finally:
        conn.close()

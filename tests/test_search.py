import sqlite3

import numpy as np
import pytest

from services import search


def _setup_db(conn):
    conn.create_function("TO_CHAR", 2, lambda value, fmt: value)
    conn.execute(
        "CREATE TABLE articles (id INTEGER PRIMARY KEY, title TEXT, url TEXT, embeddings BLOB, created_at TEXT)"
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
        v_very_similar = np.array([0.99, 0.01], dtype=np.float32).tobytes()
        v_similar = np.array([0.9, 0.1], dtype=np.float32).tobytes()
        v_middle = np.array([0.5, 0.5], dtype=np.float32).tobytes()
        v_different = np.array([0.0, 1.0], dtype=np.float32).tobytes()

        # 未いいね記事4件と、いいね済み記事1件を用意
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (1, 't1', 'u1', ?, '2026-05-21 13:00')",
            (v_different,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (2, 't2', 'u2', ?, '2026-05-21 12:00')",
            (v_similar,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (3, 't3', 'u3', ?, '2026-05-21 11:00')",
            (v_middle,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (4, 't4', 'u4', ?, '2026-05-21 10:00')",
            (v_very_similar,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (5, 't5', 'u5', ?, '2026-05-21 09:00')",
            (v_like,),
        )

        # id=5 の記事にいいね
        conn.execute("INSERT INTO likes (article_id) VALUES (5)")
        conn.commit()

        results = search.search_articles2(conn, top_k=3)

        # top_kは現状未使用なので全件返る
        assert len(results) == 5

        # 未いいね最新3件が先頭に並ぶ
        assert [result["id"] for result in results[:3]] == [1, 2, 3]
        assert all(result["liked"] is None for result in results[:4])

        # 4件目以降の未いいね記事は created_at 優先で続く
        assert results[3]["id"] == 4
        assert results[3]["score"] > results[0]["score"]

        # いいね済み記事は末尾に追加され、liked フラグと作成日を持つ
        assert results[4]["id"] == 5
        assert results[4]["liked"] == "liked"
        assert results[4]["created_at"] == "2026-05-21 09:00"
        assert results[4]["score"] == 100.0

    finally:
        conn.close()


def test_search_articles2_orders_results_2_by_created_at_then_score(tmp_path):
    db_path = tmp_path / "test_search2_tiebreak.db"
    conn = sqlite3.connect(db_path)
    try:
        _setup_db(conn)

        v_like = np.array([1.0, 0.0], dtype=np.float32).tobytes()
        v_newer = np.array([0.1, 0.9], dtype=np.float32).tobytes()
        v_high = np.array([0.95, 0.05], dtype=np.float32).tobytes()
        v_low = np.array([0.2, 0.8], dtype=np.float32).tobytes()

        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (1, 'top1', 'u1', ?, '2026-05-21 13:00')",
            (v_newer,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (2, 'top2', 'u2', ?, '2026-05-21 12:00')",
            (v_newer,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (3, 'top3', 'u3', ?, '2026-05-21 11:00')",
            (v_newer,),
        )

        # results_2 の先頭候補。created_at が新しいため score が低くても先に出る
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (4, 'newer', 'u4', ?, '2026-05-21 10:30')",
            (v_low,),
        )
        # results_2 の残り2件。created_at 同点なので score で順序が決まる
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (5, 'high', 'u5', ?, '2026-05-21 10:00')",
            (v_high,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (6, 'low', 'u6', ?, '2026-05-21 10:00')",
            (v_low,),
        )

        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (7, 'liked', 'u7', ?, '2026-05-21 09:00')",
            (v_like,),
        )
        conn.execute("INSERT INTO likes (article_id) VALUES (7)")
        conn.commit()

        results = search.search_articles2(conn, top_k=10)

        assert [result["id"] for result in results[:3]] == [1, 2, 3]
        assert [result["id"] for result in results[3:6]] == [4, 5, 6]
        assert results[4]["created_at"] == results[5]["created_at"]
        assert results[4]["score"] > results[5]["score"]

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
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (1, 't1', 'u1', ?, '2026-05-21 10:00')",
            (v1,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (2, 't2', 'u2', ?, '2026-05-21 11:00')",
            (v2,),
        )
        conn.commit()

        results = search.search_articles2(conn, top_k=10)

        # likes が無いので query_embedding は None -> score は全て 0
        assert len(results) == 2
        assert all(r["score"] == 0 for r in results)
        assert all(r["liked"] is None for r in results)
        assert [r["id"] for r in results] == [2, 1]
        assert [r["created_at"] for r in results] == ["2026-05-21 11:00", "2026-05-21 10:00"]

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
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (1, 'close', 'u1', ?, '2026-05-21 10:00')",
            (v_close,),
        )
        conn.execute(
            "INSERT INTO articles (id, title, url, embeddings, created_at) VALUES (2, 'far', 'u2', ?, '2026-05-21 11:00')",
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

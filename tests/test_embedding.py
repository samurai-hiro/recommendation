import sqlite3

import numpy as np
import pytest

from services import embedding


class DummyEmbeddingObject:
    def __init__(self, vector):
        self.embedding = vector


class DummyEmbeddingData:
    def __init__(self, vector):
        self.data = [DummyEmbeddingObject(vector)]


class DummyOpenAIClient:
    def __init__(self, vector):
        # 毎回同じベクトルを返すようにしておく
        self._vector = vector

        class _Embeddings:
            def __init__(self, outer):
                self._outer = outer

            def create(self, input, model):  # noqa: ARG002
                # input は使わず、固定のベクトルを返す
                return DummyEmbeddingData(self._outer._vector)

        self.embeddings = _Embeddings(self)


def test_get_article_empty_embedd(tmp_path):
    # 一時DBにテーブルとデータを用意
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE articles (id INTEGER PRIMARY KEY, content TEXT, embeddings BLOB)"
        )
        # embeddings が NULL のレコードと、そうでないレコードを作る
        conn.execute("INSERT INTO articles (id, content, embeddings) VALUES (1, 'a', NULL)")
        conn.execute(
            "INSERT INTO articles (id, content, embeddings) VALUES (2, 'b', X'00')"
        )
        conn.commit()

        articles = embedding.get_article_empty_embedd(conn)

        assert len(articles) == 1
        assert articles[0]["id"] == 1
        assert articles[0]["content"] == "a"
    finally:
        conn.close()


def test_generate_embeddings(monkeypatch):
    # ダミーの記事
    articles = [
        {"id": 1, "content": "hello"},
        {"id": 2, "content": "world"},
    ]

    # ダミーのベクトル（長さ3の例）
    vector = [0.1, 0.2, 0.3]

    # OpenAI クライアントをダミーに差し替え
    dummy_client = DummyOpenAIClient(vector)

    def fake_openai_client(api_key):  # noqa: ARG001
        return dummy_client

    monkeypatch.setattr(embedding, "OpenAI", fake_openai_client)

    embeddings = embedding.generate_embeddings(articles)

    assert len(embeddings) == 2
    # id が保持されていること
    assert embeddings[0]["id"] == 1
    assert embeddings[1]["id"] == 2

    # BLOB を元のベクトルに復元して確認
    for item in embeddings:
        arr = np.frombuffer(item["embedding"], dtype=np.float32)
        assert np.allclose(arr, np.array(vector, dtype=np.float32))


def test_save_embeddings(tmp_path):
    # 一時DBにテーブルとデータを用意
    db_path = tmp_path / "test_save.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE articles (id INTEGER PRIMARY KEY, content TEXT, embeddings BLOB)"
        )
        conn.execute("INSERT INTO articles (id, content, embeddings) VALUES (1, 'a', NULL)")
        conn.execute("INSERT INTO articles (id, content, embeddings) VALUES (2, 'b', NULL)")
        conn.commit()

        # ダミーの埋め込みデータ
        v1 = np.array([0.1, 0.2], dtype=np.float32).tobytes()
        v2 = np.array([0.3, 0.4], dtype=np.float32).tobytes()
        embeddings_data = [
            {"id": 1, "embedding": v1},
            {"id": 2, "embedding": v2},
        ]

        embedding.save_embeddings(conn, embeddings_data)
        conn.commit()

        rows = conn.execute(
            "SELECT id, embeddings FROM articles ORDER BY id"
        ).fetchall()

        assert len(rows) == 2
        # BLOB が正しく保存されていることを確認
        arr1 = np.frombuffer(rows[0][1], dtype=np.float32)
        arr2 = np.frombuffer(rows[1][1], dtype=np.float32)
        assert np.allclose(arr1, np.array([0.1, 0.2], dtype=np.float32))
        assert np.allclose(arr2, np.array([0.3, 0.4], dtype=np.float32))
    finally:
        conn.close()

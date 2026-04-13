import sqlite3

import pytest

from services import save_articles


def _setup_db(conn):
    conn.execute(
        "CREATE TABLE articles (id INTEGER PRIMARY KEY, title TEXT, content TEXT, url TEXT, embeddings BLOB)"
    )


def test_existing_articles(tmp_path):
    db_path = tmp_path / "test_existing.db"
    conn = sqlite3.connect(db_path)
    try:
        _setup_db(conn)
        conn.execute(
            "INSERT INTO articles (title, content, url, embeddings) VALUES (?, ?, ?, NULL)",
            ("t1", "c1", "https://example.com/1"),
        )
        conn.execute(
            "INSERT INTO articles (title, content, url, embeddings) VALUES (?, ?, ?, NULL)",
            ("t2", "c2", "https://example.com/2"),
        )
        conn.commit()

        urls = save_articles.existing_articles(conn)

        assert urls == {"https://example.com/1", "https://example.com/2"}
    finally:
        conn.close()


def test_check_duplicate():
    existing = {"https://example.com/1", "https://example.com/2"}
    new_articles = [
        {"title": "t1", "content": "c1", "url": "https://example.com/1"},
        {"title": "t3", "content": "c3", "url": "https://example.com/3"},
    ]

    unique = save_articles.check_duplicate(existing, new_articles)

    # 既存にないURLだけが残る
    assert len(unique) == 1
    assert unique[0]["url"] == "https://example.com/3"
    assert unique[0]["title"] == "t3"
    assert unique[0]["content"] == "c3"


def test_article_insert(tmp_path):
    db_path = tmp_path / "test_insert.db"
    conn = sqlite3.connect(db_path)
    try:
        _setup_db(conn)

        articles = [
            {"title": "t1", "content": "c1", "url": "https://example.com/1"},
            {"title": "t2", "content": "c2", "url": "https://example.com/2"},
        ]

        save_articles.article_insert(conn, articles)
        conn.commit()

        rows = conn.execute(
            "SELECT title, content, url FROM articles ORDER BY id"
        ).fetchall()

        assert len(rows) == 2
        assert rows[0] == ("t1", "c1", "https://example.com/1")
        assert rows[1] == ("t2", "c2", "https://example.com/2")
    finally:
        conn.close()

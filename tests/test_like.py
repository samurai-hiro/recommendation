import sqlite3

import pytest

from services import like


def _setup_db(conn):
    conn.execute("CREATE TABLE likes (article_id INTEGER)")


def test_check_like_exists(tmp_path):
    db_path = tmp_path / "test_like_exists.db"
    conn = sqlite3.connect(db_path)
    try:
        _setup_db(conn)
        # article_id=1 を2件、article_id=2 を1件入れてみる
        conn.execute("INSERT INTO likes (article_id) VALUES (1)")
        conn.execute("INSERT INTO likes (article_id) VALUES (1)")
        conn.execute("INSERT INTO likes (article_id) VALUES (2)")
        conn.commit()

        count1 = like.check_like_exists(conn, 1)
        count2 = like.check_like_exists(conn, 2)
        count3 = like.check_like_exists(conn, 3)

        assert count1 == 2
        assert count2 == 1
        assert count3 == 0
    finally:
        conn.close()


def test_save_like(tmp_path):
    db_path = tmp_path / "test_save_like.db"
    conn = sqlite3.connect(db_path)
    try:
        _setup_db(conn)

        like.save_like(conn, 10)
        like.save_like(conn, 20)
        conn.commit()

        rows = conn.execute("SELECT article_id FROM likes ORDER BY article_id").fetchall()

        assert [r[0] for r in rows] == [10, 20]
    finally:
        conn.close()

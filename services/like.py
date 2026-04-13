# ruff: noqa: ANN401
from typing import Any


#likeテーブルに記事が存在しているか確認する
def check_like_exists(conn: Any, article_id: int) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM likes WHERE article_id = %s", (article_id,))
    count = cur.fetchone()[0]
    return count

#likeテーブルに記事を保存する
def save_like(conn: Any, article_id: int) -> None:
    cur = conn.cursor()
    cur.execute("INSERT INTO likes (article_id) VALUES (%s)", (article_id,))

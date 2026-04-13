import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from db.db_connect import get_conn

# 共通の接続ヘルパー経由でDBに接続（DATABASE_URL があればPostgres）
conn = get_conn()
cur = conn.cursor()

# articlesテーブルを作成（PostgreSQL想定の型定義）
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS articles (
        id SERIAL PRIMARY KEY,
        title TEXT,
        url TEXT UNIQUE,
        content TEXT,
        published_at TIMESTAMPTZ,
        embeddings BYTEA DEFAULT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """
)

# likesテーブルを作成
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS likes (
        id SERIAL PRIMARY KEY,
        article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );
    """
)
conn.commit()

conn.close()

if __name__ == "__main__":
    print("テーブルの作成が完了しました。")
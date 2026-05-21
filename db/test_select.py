import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from db.db_connect import get_conn

import os
from pathlib import Path

conn = get_conn()

cur = conn.cursor()
cur.execute("select count(title) from articles inner join likes on articles.id = likes.article_id")
rows = cur.fetchall()
for row in rows:
    print(row)
conn.close()
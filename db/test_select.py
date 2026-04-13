import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from db.db_connect import get_conn

import os
from pathlib import Path

conn = get_conn()

cur = conn.cursor()
cur.execute("select * from articles")
rows = cur.fetchall()
for row in rows:
    print(row)
conn.close()
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# プロジェクトルートからSQLiteのデフォルトパスを決定
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_conn() -> Any:
    """アプリ共通のDB接続を返す。

    - DATABASE_URL が設定されていれば PostgreSQL に接続
    """

    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # PostgreSQL (psycopg3) を利用
        # ※ requirements.txt に "psycopg[binary]" などのドライバを追加しておくこと
        import psycopg  # type: ignore[import-not-found]

        return psycopg.connect(db_url)
    else:
        return None


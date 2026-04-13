import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from db.db_connect import get_conn
from services.like import check_like_exists, save_like

def main(article_id):
    conn = None
    
    try:
        conn = get_conn()
        #likeテーブルに記事が存在しているか確認する
        count = check_like_exists(conn, article_id)

        #likeテーブルに記事が存在していない場合は保存する
        if count == 0:
            save_like(conn, article_id)
            conn.commit()
            print(f"記事ID {article_id} にいいねを保存しました")
    except Exception as e:
        print(f"Error during like operations: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_like.py <article_id>")
        sys.exit(1)
    article_id = sys.argv[1]
    main(article_id)
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from db.db_connect import get_conn
from services.search import search_articles,search_articles2

def main():
    # クエリを入力して類似度の高い記事を検索
    conn = None
    try:
        conn = get_conn()
        query = "AI"
        # results = search_articles(conn, query)
        results = search_articles2(conn)

        if results:
            print(f"クエリ:{query}に対して類似度の高い記事：")
            for result in results:
                print(f"タイトル: {result['title']}, スコア: {result['score']} %, 興味: {result['id']}, URL: {result['url']}, liked: {result['liked']}")
        
    except Exception as e:
        print(f"Error during search operations: {e}", file=sys.stderr)
        sys.exit(1)
    
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    main()
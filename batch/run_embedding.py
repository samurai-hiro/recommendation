import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
from db.db_connect import get_conn
from services.embedding import (get_article_empty_embedd,
                                generate_embeddings,
                                save_embeddings)

def main():
    
    # embeddingsが空の記事を取得して
    # 取得した記事のembeddingsを生成して保存
    conn = None
    try:
        conn = get_conn()
        # embeddingsが空の記事を取得
        articles = get_article_empty_embedd(conn)

        # 取得した記事のembeddingsを生成して保存
        if articles:
            embeddings = generate_embeddings(articles)
            save_embeddings(conn, embeddings)
            conn.commit()
            print(f"{len(articles)}件の記事のembeddingsを保存しました。")
        else:
            print("embeddingsが空の記事はありませんでした。")

    except Exception as e:
        print(f"Error during embedding operations: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()
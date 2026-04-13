import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
import os
from services.crawler import get_article_content, get_article_links
from services.save_articles import existing_articles, check_duplicate, article_insert
from db.db_connect import get_conn

def main():
    
    # crawlerで記事のリンクを取得
    conn = None
    try:
        # crawlerで記事のリンクを取得
        urls = get_article_links()

        # crawlerで記事の内容を取得
        buf = []
        new_articles = []
        for url in urls:
            buf = get_article_content(url)
            new_articles.append(buf)
        
        conn = get_conn()
        existing = existing_articles(conn)
        unique_articles = check_duplicate(existing, new_articles)
        # 重複していない記事があったらDBに保存
        if unique_articles:
            article_insert(conn, unique_articles)
            conn.commit()
            print(f"{len(unique_articles)}件の記事を保存しました。")
        else:
            print("新しい記事はありませんでした。")
        
    except Exception as e:
        print(f"Error during crawling: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        if conn is not None:
            conn.close()
    
if __name__ == "__main__":
    main()




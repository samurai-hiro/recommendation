from typing import Any, Dict, Iterable, List, Mapping, Set


# 既存記事の取得
def existing_articles(conn: Any) -> Set[str]:
    
    cur = conn.cursor()
    cur.execute("SELECT url FROM articles")
    rows = cur.fetchall()
    existing_articles = {row[0] for row in rows}
    return existing_articles

# 新しい記事が既存記事と重複するかチェック
def check_duplicate(existing_articles: Set[str], new_articles: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    unique_articles: List[Dict[str, Any]] = []
    for article in new_articles:
        if article['url'] not in existing_articles:
            unique_articles.append(article)
    
    return unique_articles


# 新しい記事の保存
def article_insert(conn: Any, articles: Iterable[Mapping[str, Any]]) -> None:
    
    cur = conn.cursor()
    for article in articles:
        
        cur.execute(
            "INSERT INTO articles (title, content, url, published_at) VALUES (%s, %s, %s, %s)",
            (article['title'], article['content'], article['url'], article['published_at'])
            )

from typing import Any, Dict, List, Optional
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()


# likedされた記事で類似度の高い記事を検索
def search_articles2(conn: Any, top_k: int = 10) -> List[Dict[str, Any]]:
    API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=API_KEY)
    
    # データベースから全ての記事のembeddingを取得
    cur = conn.cursor()
    cur.execute("SELECT title, url, embeddings, id FROM articles WHERE embeddings IS NOT NULL")
    rows = cur.fetchall()

    # likesテーブルから記事のidを取得
    cur.execute("SELECT article_id FROM likes")
    liked_ids = set(row[0] for row in cur.fetchall())
    
    # articlesテーブルからlikedされた記事のembeddingを取得
    cur.execute("SELECT embeddings FROM articles inner join likes on articles.id = likes.article_id")
    buf_embeddings = [row[0] for row in cur.fetchall()]
    liked_embeddings = []
    if buf_embeddings:
        # likedされた記事のembeddingをnumpy配列に変換
        for buf in buf_embeddings:
            liked_embeddings.append(np.frombuffer(buf, dtype=np.float32))

    # likedされた記事のembeddingの平均をクエリのembeddingとする
    query_embedding = None
    if liked_embeddings:
        query_embedding = np.mean(liked_embeddings, axis=0)
    
    results = []
    for title, url, article_embedding, id in rows:
        if query_embedding is None:
            score = 0
        else:
            score = calculate_similarity(query_embedding,
                                           article_embedding)
        buf = None
        # いいねされている記事には "liked" を付与
        for liked_id in liked_ids:
            if id == liked_id:
                buf = "liked"
                break
        results.append({"title": title, "url": url, "score": score, "id": id, "liked": buf})

    # 類似度の高い順にソートして上位top_k件を返す
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]



# クエリに対して類似度の高い記事を検索
def search_articles(conn: Any, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=API_KEY)
    
    # クエリのembeddingを生成
    response = client.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    query_embedding = response.data[0].embedding

    # データベースから全ての記事のembeddingを取得
    cur = conn.cursor()
    cur.execute("SELECT title, url, embeddings, id FROM articles WHERE embeddings IS NOT NULL")
    rows = cur.fetchall()

    # likesテーブルから記事のidを取得
    cur.execute("SELECT article_id FROM likes")
    liked_ids = set(row[0] for row in cur.fetchall())
    
    # クエリのembeddingと記事のembeddingで類似度を計算
    results = []
    for title, url, article_embedding, id in rows:
        score = calculate_similarity(query_embedding,
                                           article_embedding)
        buf = None
        # いいねされている記事には "liked" を付与
        for liked_id in liked_ids:
            if id == liked_id:
                buf = "liked"
                break
        results.append({"title": title, "url": url, "score": score, "id": id, "liked": buf})

    # 類似度の高い順にソートして上位top_k件を返す
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


# クエリのembeddingと記事のembeddingで類似度を計算
def calculate_similarity(query_embedding: np.ndarray, article_embedding: bytes) -> float:
    article = np.frombuffer(article_embedding, dtype=np.float32)

    # コサイン類似度を計算
    similarity = np.dot(query_embedding, article) / (np.linalg.norm(query_embedding) * np.linalg.norm(article))
    # 類似度をパーセンテージに変換
    similarity = float(similarity) * 100
    # 類似度を小数点以下3桁に丸める
    similarity = round(similarity, 3)
    return similarity




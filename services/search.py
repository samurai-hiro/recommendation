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
    results_1 = []
    results_2 = []
    myresults = []

    #likedされていない最新記事上位3件を取得
    #results_1に格納
    cur = conn.cursor()
    cur.execute("SELECT ar.title, ar.url, ar.embeddings, ar.id, TO_CHAR(ar.created_at, 'YYYY/FMMM/FMDD HH24:MI') as created_at_str, ar.created_at FROM articles as ar inner join (SELECT id FROM articles EXCEPT SELECT article_id FROM likes) as unliked on ar.id = unliked.id order by ar.created_at desc limit 3")
    rows = cur.fetchall()
    for title, url, article_embedding, id, created_at_str, created_at in rows:
        results_1.append({"title": title, "url": url, "score": 0, "id": id, "liked": None, "created_at": created_at, "embeddings": article_embedding, "created_at_str": created_at_str})

    #likedされていない記事を取得
    cur.execute("SELECT ar.title, ar.url, ar.embeddings, ar.id, TO_CHAR(ar.created_at, 'YYYY/FMMM/FMDD HH24:MI') as created_at_str, ar.created_at FROM articles as ar inner join (SELECT id FROM articles EXCEPT SELECT article_id FROM likes) as unliked on ar.id = unliked.id order by ar.created_at desc")
    rows = None #初期化
    rows = cur.fetchall()
    cnt = 0
    #最初の3件はすでにresultsに追加されているため、4件目以降をresultsに追加
    #results_2に格納
    for title, url, article_embedding, id, created_at_str, created_at in rows:
        if cnt < 3:
            cnt += 1
            continue
        results_2.append({"title": title, "url": url, "score": 0, "id": id, "liked": None, "created_at": created_at, "embeddings": article_embedding, "created_at_str": created_at_str})


    # # likesテーブルから記事のidを取得
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
        #results_1とresults_2の各記事のembeddingと
        #クエリのembeddingで類似度を計算してscoreに格納
        
        for result in results_1 + results_2:
            if query_embedding is None:
                score = 0
            else:
                score = calculate_similarity(query_embedding,
                                             result["embeddings"])
            result["score"] = score

    #results_2はscore降順でソート
    #myresultsにresults_1とresults_2を格納
    results_2.sort(key=lambda x: (x["created_at"], x["score"]), reverse=True)
    for result in results_1 + results_2:
        myresults.append(result)
    
    #likedされた記事を格納
    cur.execute("SELECT ar.title, ar.url, ar.embeddings, ar.id, TO_CHAR(ar.created_at, 'YYYY/FMMM/FMDD HH24:MI') as created_at_str, ar.created_at FROM articles as ar inner join likes on ar.id = likes.article_id order by ar.created_at desc")
    rows = cur.fetchall()

    for title, url, article_embedding, id, created_at_str, created_at in rows:
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
        myresults.append({"title": title, "url": url, "score": score, "id": id, "liked": buf, "created_at": created_at, "created_at_str": created_at_str})

    return myresults



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




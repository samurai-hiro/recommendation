from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# embeddingsを保存
def save_embeddings(conn: Any, embeddings: Iterable[Mapping[str, Any]]) -> None:
    cur = conn.cursor()
    for item in embeddings:
        cur.execute("UPDATE articles SET embeddings = %s WHERE id = %s",
                    (item["embedding"], item["id"]))

# embeddingsを生成
def generate_embeddings(articles: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    client = OpenAI(api_key=API_KEY)
    embeddings = []
    for article in articles:
        response = client.embeddings.create(
            input=article["content"],
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding
        arr = np.array(embedding, dtype=np.float32)
        embeddings.append({"id": article["id"], "embedding": arr.tobytes()})

    return embeddings


# embeddingsが空の記事を取得
def get_article_empty_embedd(conn: Any) -> List[Dict[str, Any]]:

    articles = []
    cur = conn.cursor()
    cur.execute("SELECT id, content FROM articles WHERE embeddings IS NULL")
    rows = cur.fetchall()
    articles = [{"id": id, "content": content} for id, content in rows]
    return articles
    
    

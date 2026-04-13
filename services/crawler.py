from typing import Any, Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime


headers = {
    "User-Agent": "Mozilla/5.0"}


def get_article_links() -> List[str]:
    url = "https://www.itmedia.co.jp/news/"
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    links = []
    for a in soup.select("a"):
        href = a.get("href")
        if href and "articles" in href:
            links.append(href)
    
    articles = list(set(links)) #重複を除く
    #降順にソート
    articles.sort(reverse=True)
    return articles[:3] #最初の3件

def get_article_content(url: str) -> Dict[str, Any]:

    time.sleep(1) # サーバーへの負荷を減らすために1秒待機
    res = requests.get(url, headers=headers)
    
    soup = BeautifulSoup(res.content, "html.parser")
    
    # タイトルを取得
    element = soup.select_one("h1")
    if element:
        title = element.text.strip()
    else:
        title = "タイトルなし"

    # 公開日時を取得
    published_at = None
    date_element = soup.select_one("#cmsDate #update")
    if date_element:
        text = date_element.get_text(strip=True)
        published_at = text.replace(" 公開", "")

        #datetime文字列に変換
        published_at = datetime.strptime(published_at, "%Y年%m月%d日 %H時%M分")
        published_at = published_at.strftime("%Y-%m-%d %H:%M:00")
    else:
        # 公開日時が見つからない場合は、別のセレクタを試す
        meta_time = soup.find("meta", attrs={"name": "cXenseParse:recs:publishtime"})
        if meta_time and meta_time.get("content"):
            published_at = meta_time["content"]
            # datetimeの文字列に変換
            published_at = datetime.strptime(published_at, "%Y-%m-%dT%H:%M")
            published_at = published_at.strftime("%Y-%m-%d %H:%M:00")

    # 本文を取得
    body = soup.select("#cmsBody .inner > p")
    if body:
        content = "\n".join([p.text for p in body])
    else:
        content = "本文なし"
    
    return {"title": title,
             "content": content,
             "url": url,
             "published_at": published_at
             }


if __name__ == "__main__":
    article_links = get_article_links()
    for links in article_links:
        print(links)
    print("記事の内容を取得します...")
    new_articles = []
    for url in article_links:
        article = get_article_content(url)
        new_articles.append(article)
        # print(f"タイトル: {article['title']}")
        # print(f"content: {article['content']}")
    
    print(new_articles)

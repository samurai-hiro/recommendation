import pytest

from services import crawler


class DummyResponse:
    def __init__(self, content: str):
        # requests.Response.content と同じく bytes を想定
        self.content = content.encode("utf-8")


def test_get_article_links_filters_and_sorts(monkeypatch):
    html = """
    <html><body>
      <a href="/news/articles/12345/">a1</a>
      <a href="/news/articles/12346/">a2</a>
      <a href="/news/other/999/">no</a>
      <a href="/news/articles/12345/">dup</a>
    </body></html>
    """

    def fake_get(url, headers):  # noqa: ARG001
        return DummyResponse(html)

    monkeypatch.setattr(crawler, "requests", crawler.requests)
    monkeypatch.setattr(crawler.requests, "get", fake_get)

    links = crawler.get_article_links()

    # "articles" を含むリンクのみ、重複除去 & 降順ソート & 最大3件
    expected = sorted({"/news/articles/12345/", "/news/articles/12346/"}, reverse=True)
    assert links == expected


def test_get_article_content_with_cms_date(monkeypatch):
    html = """
    <html>
      <head></head>
      <body>
        <h1>テストタイトル</h1>
        <div id="cmsDate"><span id="update">2024年01月02日 03時04分 公開</span></div>
        <div id="cmsBody">
          <div class="inner">
            <p>本文1</p>
            <p>本文2</p>
          </div>
        </div>
      </body>
    </html>
    """

    def fake_get(url, headers):  # noqa: ARG001
        return DummyResponse(html)

    def fake_sleep(seconds):  # noqa: ARG001
        # テストを高速化するために何もしない
        return None

    monkeypatch.setattr(crawler, "requests", crawler.requests)
    monkeypatch.setattr(crawler.requests, "get", fake_get)
    monkeypatch.setattr(crawler.time, "sleep", fake_sleep)

    url = "https://example.com/articles/12345/"
    result = crawler.get_article_content(url)

    assert result["title"] == "テストタイトル"
    assert result["content"] == "本文1\n本文2"
    assert result["url"] == url
    assert result["published_at"] == "2024-01-02 03:04:00"


def test_get_article_content_with_meta_time(monkeypatch):
    html = """
    <html>
      <head>
        <meta name="cXenseParse:recs:publishtime" content="2024-01-02T03:04" />
      </head>
      <body>
        <h1>メタタイトル</h1>
        <div id="cmsBody">
          <div class="inner">
            <p>本文のみ</p>
          </div>
        </div>
      </body>
    </html>
    """

    def fake_get(url, headers):  # noqa: ARG001
        return DummyResponse(html)

    def fake_sleep(seconds):  # noqa: ARG001
        return None

    monkeypatch.setattr(crawler, "requests", crawler.requests)
    monkeypatch.setattr(crawler.requests, "get", fake_get)
    monkeypatch.setattr(crawler.time, "sleep", fake_sleep)

    url = "https://example.com/articles/67890/"
    result = crawler.get_article_content(url)

    assert result["title"] == "メタタイトル"
    assert result["content"] == "本文のみ"
    assert result["url"] == url
    assert result["published_at"] == "2024-01-02 03:04:00"


def test_get_article_content_no_title_no_body(monkeypatch):
    # タイトルも本文もない場合のフォールバック
    html = """
    <html>
      <head></head>
      <body>
      </body>
    </html>
    """

    def fake_get(url, headers):  # noqa: ARG001
        return DummyResponse(html)

    def fake_sleep(seconds):  # noqa: ARG001
        return None

    monkeypatch.setattr(crawler, "requests", crawler.requests)
    monkeypatch.setattr(crawler.requests, "get", fake_get)
    monkeypatch.setattr(crawler.time, "sleep", fake_sleep)

    url = "https://example.com/no-content"
    result = crawler.get_article_content(url)

    assert result["title"] == "タイトルなし"
    assert result["content"] == "本文なし"
    assert result["url"] == url
    # 日付が取得できない場合は None のまま
    assert result["published_at"] is None

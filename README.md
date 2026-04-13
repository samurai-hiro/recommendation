
# ニュース記事推薦システム

ITmediaニュース記事をクローリングし、OpenAI埋め込みを用いて「いいね」履歴に基づくレコメンドを行うWebアプリです。

## 機能概要

- **クローラー**: ITmediaから最新記事を取得しDB保存
- **埋め込み生成**: OpenAI APIで記事本文のベクトル化
- **検索・推薦**: いいね履歴をもとに類似記事を推薦
- **いいね**: 記事ごとに「いいね」登録
- **Web UI**: Streamlitによる簡易UI

## ディレクトリ構成

- `src/recommendation/app.py` : Streamlitアプリ本体
- `batch/` : バッチ処理スクリプト群（クローラ・埋め込み・検索・いいね）
- `services/` : 各種ビジネスロジック（クローラ・埋め込み・保存・検索・いいね）
- `db/` : テーブル作成スクリプト
- `tests/` : pytestによるユニットテスト

## セットアップ手順

1. **Python 3.13** をインストール
2. **PostgreSQL** をインストールし、DB作成
	- 例: `recommendation` データベースを作成
3. `.env` ファイルを作成し、以下を記載
	```
	DATABASE_URL=postgresql://<user>:<password>@localhost:5432/recommendation
	OPENAI_API_KEY=...
	```
4. 依存パッケージをインストール
	- Poetry利用時:
	  ```sh
	  poetry install --with dev
	  ```
	- もしくは requirements.txt:
	  ```sh
	  pip install -r requirements.txt
	  ```
5. テーブル作成
	```sh
	python db/create_table.py
	```

## 使い方

### ローカルでの起動

```sh
poetry run streamlit run src/recommendation/app.py
# または
make run
```

### バッチスクリプトの手動実行

- クローラ: `python batch/run_crawler.py`
- 埋め込み: `python batch/run_embedding.py`
- 検索: `python batch/run_search.py`
- いいね: `python batch/run_like.py <article_id>`

### テスト実行

```sh
poetry run pytest
# または
pytest
```

## Herokuデプロイ手順

1. Heroku Postgresアドオンを追加し、`DATABASE_URL`が設定されていることを確認
2. `OPENAI_API_KEY` をHerokuのConfig Varsに追加
3. 必要に応じて依存パッケージを書き出し
	```sh
	make export-req
	```
4. Procfile/requirements.txtをコミットし、Herokuにデプロイ
5. テーブル作成
	```sh
	heroku run python db/create_table.py
	```
6. Web Dynoを起動

## 主要依存パッケージ

- streamlit
- requests, beautifulsoup4
- openai
- psycopg
- python-dotenv
- numpy
- pytest（開発用）

---
作者: samurai-hiro

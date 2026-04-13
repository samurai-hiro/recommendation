import subprocess
import sys
import streamlit as st
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

crawler_script = PROJECT_ROOT / "batch" / "run_crawler.py"
embedding_script = PROJECT_ROOT / "batch" / "run_embedding.py"
search_script = PROJECT_ROOT / "batch" / "run_search.py"
like_script = PROJECT_ROOT / "batch" / "run_like.py"

#session_stateに格納する変数
if "rows" not in st.session_state:
	st.session_state.rows = []


if st.button("①クローラー実行"):
	
	with st.spinner("クローラーを実行中です..."):
		result = subprocess.run(
			[sys.executable, str(crawler_script)],
			capture_output=True,
			text=True,
		)

	if result.returncode == 0:
		st.success("クローラーの実行が完了しました。")
		if result.stdout:
			st.text(result.stdout)
	else:
		st.error("クローラー実行中にエラーが発生しました。")
		if result.stderr:
			st.text(result.stderr)

if st.button("②embedding生成・保存実行"):
	with st.spinner("embeddingを生成・保存中です..."):
		result = subprocess.run(
			[sys.executable, str(embedding_script)],
			capture_output=True,
			text=True,
		)

	if result.returncode == 0:
		st.success("embedding処理が完了しました。")
		if result.stdout:
			st.text(result.stdout)
	else:
		st.error("embedding処理中にエラーが発生しました。")
		if result.stderr:
			st.text(result.stderr)

if st.button("③検索実行"):
	with st.spinner("検索を実行中です..."):
		result = subprocess.run(
			[sys.executable, str(search_script)],
			capture_output=True,
			text=True,
		)
	if result.returncode == 0:
		if result.stdout:
            # --- 出力をパースして rows に格納 ---
			rows = []
			for line in result.stdout.splitlines():
				line = line.strip()
				if not line.startswith("タイトル:"):
					continue

				parts = [p.strip() for p in line.split(",")]
				data = {}
				for p in parts:
					if ":" in p:
						key, value = p.split(":", 1)
						data[key.strip()] = value.strip()
				rows.append(data)

            #セッションに保存
			st.session_state.rows = rows
			st.success(f"検索処理が完了しました。")
	else:
		st.session_state.rows = []
		st.error("検索処理中にエラーが発生しました。")
		if result.stderr:
			st.text(result.stderr)
	

def render_results(rows):
	if not rows:
		return
	st.subheader("検索結果")
	header_cols = st.columns([4, 1, 1, 2])
	header_cols[0].write("タイトル")
	header_cols[1].write("スコア")
	header_cols[2].write("興味")
	header_cols[3].write("URL")

	for i, r in enumerate(rows):
		title = r.get("タイトル", "")
		score = r.get("スコア", "")
		like_id = r.get("興味", "")  # ← 渡したい id
		url = r.get("URL", "")
		liked = r.get("liked", None)

		cols = st.columns([4, 1, 1, 2])
		cols[0].write(title)
		cols[1].write(score)

		# 興味列：いいねボタン
		# すでにいいねされている場合はボタンを無効化
		is_liked = (liked == "liked")
		if cols[2].button("👍 いいね",
					 key=f"like_{like_id}_{i}",
					 disabled=is_liked):
			try:
				# 非同期に実行
				result = subprocess.run(
					[sys.executable, str(like_script), str(like_id)],
					capture_output=True,
					text=True,
				)
				if result.returncode == 0:
					msg = result.stdout.strip() or f"id={like_id} にいいねを保存しました"
					st.success(msg)
				else:
					err_msg = result.stderr.strip() or f"id={like_id} へのいいね保存に失敗しました"
					st.error(err_msg)

			except Exception as e:
				st.error(f"いいねの保存中にエラーが発生しました: {e}")
		
		# URL 列：リンク表示
		if url:
			cols[3].markdown(f"[リンク]({url})")

render_results(st.session_state.rows)
		


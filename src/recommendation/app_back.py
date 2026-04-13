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
		st.success("検索処理が完了しました。")
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

            # --- テーブル風に表示（「興味」列はいいねボタン） ---
			if rows:
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

					cols = st.columns([4, 1, 1, 2])
					cols[0].write(title)
					cols[1].write(score)

                    # 興味列：いいねボタン
					if cols[2].button("👍 いいね", key=f"like_{like_id}_{i}"):
						try:
							subprocess.run(
                                [sys.executable, str(like_script), str(like_id)],
                                check=False,
                            )
							st.success(f"id={like_id} にいいねしました")
						except Exception as e:
							st.error(f"いいね処理でエラーが発生しました: {e}")

                    # URL 列：リンク表示
					if url:
						cols[3].markdown(f"[リンク]({url})")
		else:
            # パースできなければ元のテキストをそのまま表示
			st.text(result.stdout)
	else:
		st.error("検索処理中にエラーが発生しました。")
		if result.stderr:
			st.text(result.stderr)
	

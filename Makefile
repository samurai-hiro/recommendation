.PHONY: run export-req

run:
	poetry run streamlit run src/recommendation/app.py

export-req:
	poetry export -f requirements.txt --output requirements.txt --without-hashes
.PHONY: install dev test docker-up docker-down

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	pytest -q

docker-up:
	docker compose up --build

docker-down:
	docker compose down

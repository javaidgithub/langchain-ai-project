.PHONY: help setup backend frontend test lint build up down clean

help:            ## Show this help
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

setup:           ## Install backend + frontend dependencies and create .env
	@test -f .env || cp .env.example .env
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -r backend/requirements-dev.txt
	cd frontend && npm install

backend:         ## Run the API with auto-reload on :8000
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:        ## Run the React dev server on :5173
	cd frontend && npm run dev

test:            ## Run backend tests and the frontend type check
	cd backend && .venv/bin/python -m pytest -q
	cd frontend && npm run typecheck

lint:            ## Lint the backend
	cd backend && .venv/bin/ruff check app tests

build:           ## Production build of the frontend
	cd frontend && npm run build

up:              ## Start everything with Docker (UI on :8080)
	docker compose up --build -d

down:            ## Stop the Docker stack
	docker compose down

clean:           ## Remove build artifacts and caches
	rm -rf frontend/dist backend/.pytest_cache backend/.ruff_cache
	find backend -name __pycache__ -type d -prune -exec rm -rf {} +

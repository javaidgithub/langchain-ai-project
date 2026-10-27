# Quick Start

Get the project running locally in under five minutes.

## Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **Git**
- **An API key** for at least one provider, or [Ollama](https://ollama.com) running locally

## 1. Clone and install

```bash
git clone https://github.com/javaidgithub/langchain-ai-project.git
cd langchain-ai-project
make setup
```

`make setup` copies `.env.example` → `.env`, creates a Python venv, installs all Python packages, and runs `npm install`.

!!! note "No make?"
    ```bash
    cp .env.example .env
    cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
    cd ../frontend && npm install
    ```

## 2. Add a provider key

Open `.env` and add at least one key:

```dotenv
OPENAI_API_KEY=sk-...
# or ANTHROPIC_API_KEY=sk-ant-...
# or DEFAULT_PROVIDER=ollama  (no key needed with Ollama)
```

!!! tip "No API key? Use Ollama"
    Install [Ollama](https://ollama.com), run `ollama pull llama3.2`, then set:
    ```dotenv
    DEFAULT_PROVIDER=ollama
    DEFAULT_MODEL=llama3.2
    EMBEDDINGS_PROVIDER=ollama
    ```

## 3. Start the servers

```bash
make backend    # terminal 1 — API on http://localhost:8000
make frontend   # terminal 2 — UI  on http://localhost:5173
```

Open **http://localhost:5173**.

## 4. Quick Docker alternative

```bash
cp .env.example .env   # add your keys
docker compose up --build
# open http://localhost:8080
```

## Useful commands

| Command | What it does |
|---|---|
| `make test` | Backend tests + frontend type check |
| `make lint` | Ruff linter |
| `make build` | Production frontend build |
| `make up` | Full Docker stack |
| `make clean` | Remove build artefacts |

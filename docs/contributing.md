# Contributing

Contributions are welcome. This is a reference project, so clarity and teaching value matter as much as functionality.

---

## Development setup

```bash
git clone https://github.com/javaidgithub/langchain-ai-project.git
cd langchain-ai-project
make setup
```

---

## Running tests

```bash
make test    # backend pytest + frontend typecheck
make lint    # ruff on backend
```

The backend tests run the real LangGraph graphs through the real HTTP and SSE layer using a scripted fake model — no API keys needed.

---

## Adding a tool

See [Tools & Registry — Adding a tool](concepts/tools.md#adding-a-tool).

## Adding a provider

See [Providers — Adding a provider](concepts/providers.md#adding-a-provider).

## Adding an agent

1. Build a `StateGraph` in `backend/app/agents/`.
2. Register it in `backend/app/agents/registry.py`.
3. Add the id to `AgentName` in `backend/app/schemas/chat.py` and `AgentId` in `frontend/src/api/types.ts`.

---

## Code style

- Backend: Python 3.11+, `ruff` for lint, type hints everywhere.
- Frontend: TypeScript strict mode, no `any` except in explicit casts.
- Docstrings on every tool — the model reads them.

---

## Opening an issue

Please include:

- The provider and model you were using
- The full error message from the browser or terminal
- Relevant `.env` settings (redact API keys)

---

## License

By contributing, you agree your code is released under the [MIT License](https://github.com/javaidgithub/langchain-ai-project/blob/main/LICENSE).

# Configuration

All settings are environment variables, read from `.env` in the repo root.

```bash
cp .env.example .env
```

## Provider keys

| Variable | Provider | Docs |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI | [platform.openai.com](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | Anthropic | [console.anthropic.com](https://console.anthropic.com) |
| `GOOGLE_API_KEY` | Google Gemini | [aistudio.google.com](https://aistudio.google.com/apikey) |
| `DEEPSEEK_API_KEY` | DeepSeek | [platform.deepseek.com](https://platform.deepseek.com/api_keys) |
| `XAI_API_KEY` | xAI Grok | [console.x.ai](https://console.x.ai) |
| `OPENROUTER_API_KEY` | OpenRouter | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `GROQ_API_KEY` | Groq | [console.groq.com](https://console.groq.com/keys) |
| `OLLAMA_BASE_URL` | Ollama | No key — default `http://localhost:11434` |

All keys are optional at the server level. Users can also paste a key in the **Settings** panel — it is stored in the browser only and sent per-request, never persisted on the server.

## Model defaults

```dotenv
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini
```

## Embeddings

```dotenv
EMBEDDINGS_PROVIDER=openai   # openai | google | ollama | huggingface
```

!!! warning "No OpenAI key?"
    Set `EMBEDDINGS_PROVIDER=ollama` or `huggingface` so document upload works without an OpenAI key.

## Agent behaviour

```dotenv
CHECKPOINTER=sqlite          # sqlite | memory
MAX_CONTEXT_TOKENS=6000
KEEP_LAST_MESSAGES=6
RECURSION_LIMIT=25
ENABLE_LLM_CACHE=false
PYTHON_REPL_TIMEOUT=10
```

## Server

```dotenv
ENVIRONMENT=development      # development | production
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
DATA_DIR=./data
API_AUTH_TOKEN=              # protect the API with a bearer token
```

## LangSmith tracing

```dotenv
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=langchain-ai-project
```

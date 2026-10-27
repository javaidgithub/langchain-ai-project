# LLM Providers

The project supports 8 providers through a single factory function. Switching provider is a UI dropdown — no code change or restart needed.

**Source files:** `backend/app/llm/factory.py`, `backend/app/llm/catalog.py`

---

## Supported providers

=== "OpenAI"
    ```dotenv
    OPENAI_API_KEY=sk-...
    DEFAULT_PROVIDER=openai
    DEFAULT_MODEL=gpt-4o-mini
    ```
    Suggested models: `gpt-4o-mini`, `gpt-4o`, `gpt-4.1`, `o4-mini`

=== "Anthropic"
    ```dotenv
    ANTHROPIC_API_KEY=sk-ant-...
    DEFAULT_PROVIDER=anthropic
    DEFAULT_MODEL=claude-sonnet-5-5
    ```
    Suggested models: `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-haiku-5-5`

=== "Google Gemini"
    ```dotenv
    GOOGLE_API_KEY=AIza...
    DEFAULT_PROVIDER=gemini
    DEFAULT_MODEL=gemini-2.5-flash
    ```
    Suggested models: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash`

=== "DeepSeek"
    ```dotenv
    DEEPSEEK_API_KEY=...
    DEFAULT_PROVIDER=deepseek
    DEFAULT_MODEL=deepseek-chat
    ```
    Suggested models: `deepseek-chat`, `deepseek-reasoner`

    !!! note "deepseek-reasoner"
        `deepseek-reasoner` streams its internal reasoning into a collapsible block in the UI. Check your provider's current docs for tool-calling support.

=== "xAI Grok"
    ```dotenv
    XAI_API_KEY=xai-...
    DEFAULT_PROVIDER=xai
    DEFAULT_MODEL=grok-3
    ```
    Suggested models: `grok-4`, `grok-3`, `grok-3-mini`

=== "OpenRouter"
    ```dotenv
    OPENROUTER_API_KEY=sk-or-...
    DEFAULT_PROVIDER=openrouter
    DEFAULT_MODEL=openai/gpt-4o-mini
    ```
    OpenRouter is an OpenAI-compatible gateway to 200+ models. Model ids are `vendor/model`, e.g. `anthropic/claude-sonnet-4.5`, `meta-llama/llama-3.3-70b-instruct`.

=== "Groq"
    ```dotenv
    GROQ_API_KEY=gsk_...
    DEFAULT_PROVIDER=groq
    DEFAULT_MODEL=llama-3.3-70b-versatile
    ```
    Groq serves open-source models with extremely low latency.

=== "Ollama (local)"
    ```dotenv
    OLLAMA_BASE_URL=http://localhost:11434
    DEFAULT_PROVIDER=ollama
    DEFAULT_MODEL=llama3.2
    ```
    No API key. Run `ollama pull llama3.2` (or any model) first.

---

## How the factory works

```python
def get_chat_model(provider: str, model: str, temperature: float = 0.2) -> BaseChatModel:
    key = resolve_api_key(provider)   # per-request key first, then .env
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature, api_key=key)
    if provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=key, base_url="https://openrouter.ai/api/v1")
    # ... one branch per provider
```

All providers are imported lazily. Missing a package only breaks that provider, not the whole app.

---

## Adding a provider

1. Add a `ProviderSpec` in `backend/app/llm/catalog.py`:

    ```python
    "myprovider": ProviderSpec(
        "myprovider", "My Provider",
        ["model-a", "model-b"],
        docs_url="https://myprovider.com/docs",
    ),
    ```

2. Add a branch in `backend/app/llm/factory.py`:

    ```python
    if provider == "myprovider":
        from langchain_myprovider import ChatMyProvider
        return ChatMyProvider(model=model, temperature=temperature, api_key=key)
    ```

3. Add `myprovider_api_key` to `Settings` and `provider_keys` in `backend/app/core/config.py`.

For OpenAI-compatible APIs (like OpenRouter), step 2 is just `ChatOpenAI(base_url=..., api_key=...)`.

---

## Per-request keys

Keys pasted in the UI travel in the request body and are stored in a `ContextVar` — they are never written to the database or checkpointer. `resolve_api_key` prefers the per-request key and falls back to the server environment key.

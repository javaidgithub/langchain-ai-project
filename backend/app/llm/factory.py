"""Provider-agnostic chat model factory.

Every provider is imported lazily so a missing optional dependency only breaks
that provider, never the whole app.
"""
from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import get_settings
from app.core.context import request_credentials
from app.core.errors import ProviderNotConfigured
from app.llm.catalog import PROVIDERS


def resolve_api_key(provider: str) -> str | None:
    """Per-request key (from the UI) wins over the server-side environment key."""
    supplied = (request_credentials.get() or {}).get(provider)
    return supplied or get_settings().provider_keys.get(provider)


def is_configured(provider: str) -> bool:
    spec = PROVIDERS.get(provider)
    return bool(spec) and (not spec.needs_key or bool(get_settings().provider_keys.get(provider)))


def get_chat_model(provider: str, model: str, temperature: float = 0.2, **kwargs) -> BaseChatModel:
    if provider not in PROVIDERS:
        raise ProviderNotConfigured(f"Unknown provider '{provider}'. Choose one of: {', '.join(PROVIDERS)}")

    key = resolve_api_key(provider)
    if PROVIDERS[provider].needs_key and not key:
        raise ProviderNotConfigured(
            f"No API key for {PROVIDERS[provider].label}. Add it to your .env file or paste it in Settings."
        )

    try:
        if provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model=model, temperature=temperature, api_key=key, **kwargs)

        if provider == "openrouter":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={"HTTP-Referer": "https://github.com/", "X-Title": get_settings().app_name},
                **kwargs,
            )

        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(model=model, temperature=temperature, api_key=key, **kwargs)

        if provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(model=model, temperature=temperature, google_api_key=key, **kwargs)

        if provider == "deepseek":
            from langchain_deepseek import ChatDeepSeek

            return ChatDeepSeek(model=model, temperature=temperature, api_key=key, **kwargs)

        if provider == "xai":
            from langchain_xai import ChatXAI

            return ChatXAI(model=model, temperature=temperature, api_key=key, **kwargs)

        if provider == "groq":
            from langchain_groq import ChatGroq

            return ChatGroq(model=model, temperature=temperature, api_key=key, **kwargs)

        if provider == "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(model=model, temperature=temperature, base_url=get_settings().ollama_base_url, **kwargs)
    except ImportError as exc:  # pragma: no cover - depends on installed extras
        raise ProviderNotConfigured(
            f"The package for '{provider}' is not installed ({exc.name}). Run `pip install -r requirements.txt`."
        ) from exc

    raise ProviderNotConfigured(f"Provider '{provider}' is not implemented")  # pragma: no cover

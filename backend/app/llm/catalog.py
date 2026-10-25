"""Static catalog of supported providers and suggested models.

Model ids change often. Treat the lists below as suggestions: the UI also lets
users type any model id their provider supports.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    models: list[str] = field(default_factory=list)
    needs_key: bool = True
    docs_url: str = ""


PROVIDERS: dict[str, ProviderSpec] = {
    "openai": ProviderSpec(
        "openai", "OpenAI",
        ["gpt-4o-mini", "gpt-4o", "gpt-4.1", "gpt-4.1-mini", "o4-mini"],
        docs_url="https://platform.openai.com/api-keys",
    ),
    "anthropic": ProviderSpec(
        "anthropic", "Anthropic",
        ["claude-sonnet-5-5", "claude-opus-5-5", "claude-haiku-5-5"],
        docs_url="https://console.anthropic.com/",
    ),
    "gemini": ProviderSpec(
        "gemini", "Google Gemini",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
        docs_url="https://aistudio.google.com/apikey",
    ),
    "deepseek": ProviderSpec(
        "deepseek", "DeepSeek",
        ["deepseek-chat", "deepseek-reasoner"],
        docs_url="https://platform.deepseek.com/api_keys",
    ),
    "xai": ProviderSpec(
        "xai", "xAI Grok",
        ["grok-4", "grok-3", "grok-3-mini"],
        docs_url="https://console.x.ai/",
    ),
    "openrouter": ProviderSpec(
        "openrouter", "OpenRouter",
        [
            "openai/gpt-4o-mini",
            "anthropic/claude-sonnet-4.5",
            "google/gemini-2.5-flash",
            "deepseek/deepseek-chat",
            "meta-llama/llama-3.3-70b-instruct",
            "x-ai/grok-3-mini",
        ],
        docs_url="https://openrouter.ai/keys",
    ),
    "groq": ProviderSpec(
        "groq", "Groq",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        docs_url="https://console.groq.com/keys",
    ),
    "ollama": ProviderSpec(
        "ollama", "Ollama (local)",
        ["llama3.2", "qwen2.5", "mistral"],
        needs_key=False,
        docs_url="https://ollama.com/",
    ),
}

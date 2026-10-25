from __future__ import annotations

from langchain_core.embeddings import Embeddings

from app.core.config import get_settings
from app.core.errors import ProviderNotConfigured
from app.llm.factory import resolve_api_key

_DEFAULT_MODELS = {
    "openai": "text-embedding-3-small",
    "google": "models/gemini-embedding-001",
    "ollama": "nomic-embed-text",
    "huggingface": "sentence-transformers/all-MiniLM-L6-v2",
}


def get_embeddings() -> Embeddings:
    s = get_settings()
    provider = s.embeddings_provider
    model = s.embeddings_model or _DEFAULT_MODELS[provider]

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        key = resolve_api_key("openai")
        if not key:
            raise ProviderNotConfigured("Embeddings need OPENAI_API_KEY (or set EMBEDDINGS_PROVIDER to ollama/huggingface).")
        return OpenAIEmbeddings(model=model, api_key=key)
    if provider == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        key = resolve_api_key("gemini")
        if not key:
            raise ProviderNotConfigured("Embeddings need GOOGLE_API_KEY.")
        return GoogleGenerativeAIEmbeddings(model=model, google_api_key=key)
    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=model, base_url=s.ollama_base_url)
    if provider == "huggingface":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError as exc:
            raise ProviderNotConfigured("Run `pip install langchain-huggingface sentence-transformers`.") from exc
        return HuggingFaceEmbeddings(model_name=model)
    raise ProviderNotConfigured(f"Unknown embeddings provider '{provider}'")

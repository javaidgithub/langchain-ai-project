"""RAG service: ingest -> split -> embed -> store -> retrieve."""
from __future__ import annotations

import asyncio
from functools import lru_cache
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.errors import AppError
from app.rag.embeddings import get_embeddings

COLLECTION = "knowledge_base"
SUPPORTED = {".pdf", ".txt", ".md", ".markdown", ".csv", ".json"}


@lru_cache
def get_vectorstore():
    from langchain_chroma import Chroma

    settings = get_settings()
    settings.ensure_dirs()
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.chroma_dir),
    )


def reset_vectorstore_cache() -> None:
    get_vectorstore.cache_clear()


def get_retriever(k: int | None = None) -> VectorStoreRetriever:
    """MMR retrieval reduces near-duplicate chunks in the context window."""
    k = k or get_settings().retriever_k
    return get_vectorstore().as_retriever(search_type="mmr", search_kwargs={"k": k, "fetch_k": k * 4})


def _load(path: Path) -> list[Document]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from langchain_community.document_loaders import PyPDFLoader

        return PyPDFLoader(str(path)).load()
    if suffix not in SUPPORTED:
        raise AppError(f"Unsupported file type '{suffix}'. Supported: {', '.join(sorted(SUPPORTED))}")
    return [Document(page_content=path.read_text(encoding="utf-8", errors="replace"))]


def _ingest_sync(path: Path, display_name: str) -> int:
    s = get_settings()
    docs = _load(path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata = {**chunk.metadata, "source": display_name, "chunk": i}
        chunk.metadata.pop("file_path", None)
    if not chunks:
        raise AppError("The file has no extractable text.")
    store = get_vectorstore()
    store._collection.delete(where={"source": display_name})  # re-uploading replaces the old version
    store.add_documents(chunks)
    return len(chunks)


async def ingest_file(path: Path, display_name: str) -> int:
    return await asyncio.to_thread(_ingest_sync, path, display_name)


async def search_documents(query: str, k: int | None = None) -> list[Document]:
    return await get_retriever(k).ainvoke(query)


def _list_sync() -> list[dict]:
    data = get_vectorstore()._collection.get(include=["metadatas"])
    counts: dict[str, int] = {}
    for meta in data.get("metadatas") or []:
        src = (meta or {}).get("source", "unknown")
        counts[src] = counts.get(src, 0) + 1
    return [{"name": name, "chunks": n} for name, n in sorted(counts.items())]


async def list_documents() -> list[dict]:
    return await asyncio.to_thread(_list_sync)


async def delete_document(name: str) -> None:
    await asyncio.to_thread(lambda: get_vectorstore()._collection.delete(where={"source": name}))


def format_docs(docs: list[Document]) -> str:
    return "\n\n".join(f"[{i}] {d.page_content}" for i, d in enumerate(docs, 1))


def docs_to_sources(docs: list[Document]) -> list[dict]:
    return [
        {"index": i, "source": d.metadata.get("source", "unknown"), "page": d.metadata.get("page"),
         "snippet": d.page_content[:240]}
        for i, d in enumerate(docs, 1)
    ]

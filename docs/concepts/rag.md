# RAG — Document Intelligence

RAG (Retrieval-Augmented Generation) lets the model answer questions using your own documents rather than its training data. This project implements an **agentic RAG** pipeline — one that checks its own work and rewrites the query if the first retrieval fails.

**Source files:** `backend/app/rag/`, `backend/app/agents/rag_agent.py`

---

## The pipeline

```
Upload → Load → Split → Embed → Store (Chroma)
                                      │
Query  ──────────────────────────► Retrieve (MMR)
                                      │
                                   Grade (LLM)
                                      │
                             sufficient? ──no──► Rewrite query ──► Retrieve again
                                      │
                                    yes
                                      │
                                  Generate (LLM) + cite sources
```

---

## Ingestion

### Supported file types

| Extension | Loader |
|---|---|
| `.pdf` | `PyPDFLoader` (one `Document` per page) |
| `.txt`, `.md`, `.markdown` | Plain text |
| `.csv`, `.json` | Plain text |

### Chunking

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,    # configured via CHUNK_SIZE
    chunk_overlap=150,  # configured via CHUNK_OVERLAP
)
chunks = splitter.split_documents(docs)
```

`RecursiveCharacterTextSplitter` tries to split on paragraph breaks, then sentences, then words — so chunks are semantically coherent.

### Re-uploading

Re-uploading a file with the same name deletes the old chunks first:

```python
store._collection.delete(where={"source": display_name})
store.add_documents(chunks)
```

---

## Embeddings

Controlled by `EMBEDDINGS_PROVIDER` in `.env`:

| Provider | Default model | Package |
|---|---|---|
| `openai` | `text-embedding-3-small` | `langchain-openai` |
| `google` | `models/gemini-embedding-001` | `langchain-google-genai` |
| `ollama` | `nomic-embed-text` | `langchain-ollama` |
| `huggingface` | `all-MiniLM-L6-v2` | `langchain-huggingface` |

---

## Vector store — Chroma

```python
from langchain_chroma import Chroma

vectorstore = Chroma(
    collection_name="knowledge_base",
    embedding_function=get_embeddings(),
    persist_directory="./data/chroma",   # persists to disk
)
```

Chroma stores vectors locally in `data/chroma/`. No external service needed.

---

## Retrieval — MMR

MMR (Maximal Marginal Relevance) balances relevance and diversity — it avoids returning five near-identical chunks:

```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "fetch_k": 16},  # fetch 16, keep 4 most diverse
)
```

---

## Agentic loop

The Documents agent adds two extra steps around retrieval:

**Grade** — the model judges whether the retrieved chunks actually answer the question:

```python
class Grade(BaseModel):
    sufficient: bool
    reason: str

verdict = await llm.with_structured_output(Grade).ainvoke(
    f"Question: {question}\n\nDocuments: {context}\n\nDo these answer the question?"
)
```

**Rewrite** — if not sufficient (max 2 rewrites):

```python
better_query = await llm.ainvoke(
    f"Rewrite this as a better search query: {question}"
)
```

---

## Citations

Every retrieved chunk carries metadata. `generate` returns `sources`:

```python
[
  {"index": 1, "source": "report.pdf", "page": 3, "snippet": "...first 240 chars..."},
  {"index": 2, "source": "notes.md",   "page": null, "snippet": "..."},
]
```

The model is instructed to cite sources as `[1]`, `[2]` inline. The UI renders them as expandable source cards below the answer.

---

## One-shot vs. agentic

| | One-shot (`POST /api/rag/query`) | Agentic (Documents agent in Chat) |
|---|---|---|
| Loop | Single retrieval | Retrieve → grade → (rewrite) → retrieve |
| Multi-turn | No | Yes — tracks conversation history |
| Use for | Quick lookups | Deep Q&A over documents |

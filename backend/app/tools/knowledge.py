from langchain_core.tools import tool

from app.rag.service import search_documents


@tool
async def search_knowledge_base(query: str) -> str:
    """Search the user's uploaded documents (knowledge base). Use for questions about their own files."""
    try:
        docs = await search_documents(query)
    except Exception as exc:
        return f"Knowledge base unavailable: {exc}"
    if not docs:
        return "The knowledge base has no relevant content. The user may need to upload documents first."
    return "\n\n".join(
        f"[{i}] (source: {d.metadata.get('source', 'unknown')}, page {d.metadata.get('page', '-')})\n{d.page_content}"
        for i, d in enumerate(docs, 1)
    )

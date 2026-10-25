import re
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.chains.lcel import rag_chain
from app.core.config import get_settings
from app.core.context import request_credentials
from app.core.errors import AppError
from app.llm.factory import get_chat_model
from app.rag import service
from app.schemas.chat import ModelSelection

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    s = get_settings()
    s.ensure_dirs()
    name = re.sub(r"[^\w.\- ]", "_", Path(file.filename or "upload").name)
    if Path(name).suffix.lower() not in service.SUPPORTED:
        raise HTTPException(400, f"Unsupported file type. Supported: {', '.join(sorted(service.SUPPORTED))}")

    dest = s.uploads_dir / f"{uuid.uuid4().hex}_{name}"
    size = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > s.max_upload_mb * 1024 * 1024:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(413, f"File is larger than {s.max_upload_mb} MB")
            out.write(chunk)
    try:
        chunks = await service.ingest_file(dest, name)
    except AppError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    finally:
        dest.unlink(missing_ok=True)  # chunks live in the vector store; the raw upload is not kept
    return {"name": name, "chunks": chunks}


@router.get("/documents")
async def documents():
    try:
        return await service.list_documents()
    except AppError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc


@router.delete("/documents/{name}", status_code=204)
async def remove(name: str):
    await service.delete_document(name)


class QueryBody(BaseModel):
    question: str
    model: ModelSelection


@router.post("/query")
async def query(body: QueryBody):
    """One-shot RAG via a plain LCEL chain (no agent loop). Returns the answer and its sources."""
    request_credentials.set({body.model.provider: body.model.api_key} if body.model.api_key else {})
    try:
        llm = get_chat_model(body.model.provider, body.model.model, body.model.temperature)
        result = await rag_chain(llm).ainvoke(body.question)
    except AppError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    return {"answer": result["answer"], "sources": service.docs_to_sources(result["docs"])}

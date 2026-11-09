from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from salesvoice_common.auth_deps import CurrentUser, admin_only, current_user

from app.chunking import chunk_text
from app.config import settings
from app.db import db
from app.embeddings import embedder
from app.extract import ALLOWED, extract_text
from app.models import Chunk, Document
from app.schemas import DocumentOut, SearchHit, SearchIn, SearchOut

router = APIRouter()


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), title: str | None = Form(default=None),
                          user: CurrentUser = Depends(current_user),
                          s: AsyncSession = Depends(db.session)):
    admin_only(user)
    filename = file.filename or "upload"
    if not any(filename.lower().endswith(ext) for ext in ALLOWED):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Allowed: {sorted(ALLOWED)}")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Max {settings.max_upload_mb} MB")

    doc = Document(title=title or filename, filename=filename, uploaded_by=user.id)
    s.add(doc)
    try:
        text = extract_text(filename, data)
        pieces = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not pieces:
            raise ValueError("no readable text found (is it a scanned PDF?)")
        vectors = await embedder.embed(pieces)
        doc.chunks = [Chunk(position=i, text=t, embedding=v)
                      for i, (t, v) in enumerate(zip(pieces, vectors))]
        doc.chunk_count, doc.status = len(pieces), "ready"
    except Exception as e:
        doc.status, doc.error = "failed", str(e)[:500]
    await s.commit()
    await s.refresh(doc)
    return doc


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents(user: CurrentUser = Depends(current_user), s: AsyncSession = Depends(db.session)):
    rows = await s.scalars(select(Document).order_by(Document.created_at.desc()))
    return list(rows)


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str, user: CurrentUser = Depends(current_user),
                          s: AsyncSession = Depends(db.session)):
    admin_only(user)
    doc = await s.get(Document, doc_id)
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    await s.delete(doc)
    await s.commit()


@router.post("/search", response_model=SearchOut)
async def search(body: SearchIn, user: CurrentUser = Depends(current_user),
                 s: AsyncSession = Depends(db.session)):
    [qvec] = await embedder.embed([body.query])
    distance = Chunk.embedding.cosine_distance(qvec)
    rows = await s.execute(
        select(Chunk, Document.title, distance.label("distance"))
        .join(Document)
        .where(Document.status == "ready")
        .order_by(distance)
        .limit(body.top_k)
    )
    hits = [SearchHit(chunk_id=c.id, document_id=c.document_id, document_title=title,
                      text=c.text, score=round(1 - dist, 4))
            for c, title, dist in rows if 1 - dist >= body.min_score]
    return SearchOut(query=body.query, hits=hits)

import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, SparseVector

from app.core.config import get_settings
from app.core.database import get_connection
from app.models.schemas import TextUploadRequest, DocumentUploadResponse
from app.services.chunking import chunk_text
from app.services.embeddings import get_embedding, get_sparse_embedding
from app.services.extraction import extract_text_from_pdf
from app.services.entity import extract_entities, store_entities

router = APIRouter()
settings = get_settings()


def get_qdrant():
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )


def process_and_store(
    document_id: str,
    text: str,
    title: str,
    author: Optional[str],
    source: Optional[str],
    tags: Optional[List[str]],
    doc_type: str
) -> tuple[int, int]:
    qdrant = get_qdrant()
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO documents (id, title, author, source, tags, doc_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            document_id,
            title,
            author,
            source,
            ",".join(tags) if tags else "",
            doc_type
        ))

        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        points = []
        total_entities = 0

        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"

            # Dense embedding
            dense_vector = get_embedding(chunk)

            # Sparse BM25 embedding
            sparse_indices, sparse_values = get_sparse_embedding(chunk)

            
            # Extract entities — non blocking
            try:
                entities = extract_entities(chunk)
                total_entities += store_entities(document_id, chunk_id, entities, conn)
            except Exception as entity_error:
                print(f"Entity extraction failed for chunk {chunk_id}: {entity_error}")

            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense": dense_vector,
                    "sparse": SparseVector(
                        indices=sparse_indices,
                        values=sparse_values
                    )
                },
                payload={
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "text": chunk,
                    "title": title,
                    "author": author or "",
                    "source": source or "",
                    "tags": tags or [],
                    "chunk_index": i
                }
            ))

        qdrant.upsert(
            collection_name=settings.collection_name,
            points=points
        )

        conn.commit()
        return len(chunks), total_entities

    except Exception as e:
        conn.rollback()
        print(f"FULL ERROR: {type(e).__name__}: {e}")
        raise e
    finally:
        conn.close()


@router.post("/text", response_model=DocumentUploadResponse)
async def upload_text(request: TextUploadRequest):
    document_id = str(uuid.uuid4())
    try:
        chunks_created, entities_extracted = process_and_store(
            document_id=document_id,
            text=request.text,
            title=request.title,
            author=request.author,
            source=request.source,
            tags=request.tags,
            doc_type="text"
        )
        return DocumentUploadResponse(
            document_id=document_id,
            title=request.title,
            chunks_created=chunks_created,
            entities_extracted=entities_extracted,
            message="Text uploaded and indexed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    author: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    tags: Optional[str] = Form(None)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    document_id = str(uuid.uuid4())
    try:
        file_bytes = await file.read()
        text = extract_text_from_pdf(file_bytes)

        if not text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        tags_list = [t.strip() for t in tags.split(",")] if tags else []

        chunks_created, entities_extracted = process_and_store(
            document_id=document_id,
            text=text,
            title=title,
            author=author,
            source=source,
            tags=tags_list,
            doc_type="pdf"
        )
        return DocumentUploadResponse(
            document_id=document_id,
            title=title,
            chunks_created=chunks_created,
            entities_extracted=entities_extracted,
            message="Document uploaded and indexed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
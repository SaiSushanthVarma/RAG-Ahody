from fastapi import APIRouter, Query
from typing import Optional, List
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

from app.core.config import get_settings
from app.models.schemas import SearchResponse, SearchResult
from app.services.embeddings import get_query_embedding

router = APIRouter()
settings = get_settings()


def get_qdrant():
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of results to return"),
    author: Optional[str] = Query(None, description="Filter by author"),
    source: Optional[str] = Query(None, description="Filter by source"),
    tags: Optional[str] = Query(None, description="Filter by tag")
):
    """
    Search the knowledge base using semantic vector search.
    Supports metadata filtering by author, source and tags.
    """
    qdrant = get_qdrant()

    # Build metadata filters if provided
    conditions = []

    if author:
        conditions.append(
            FieldCondition(
                key="author",
                match=MatchValue(value=author)
            )
        )

    if source:
        conditions.append(
            FieldCondition(
                key="source",
                match=MatchValue(value=source)
            )
        )

    if tags:
        conditions.append(
            FieldCondition(
                key="tags",
                match=MatchAny(any=[tags])
            )
        )

    search_filter = Filter(must=conditions) if conditions else None

    # Embed the query
    query_vector = get_query_embedding(q)

    # Search Qdrant
    results = qdrant.search(
        collection_name=settings.collection_name,
        query_vector=query_vector,
        limit=top_k,
        query_filter=search_filter,
        with_payload=True
    )

    # Format results
    search_results = []
    for hit in results:
        payload = hit.payload
        search_results.append(SearchResult(
            chunk_id=payload.get("chunk_id", ""),
            document_id=payload.get("document_id", ""),
            title=payload.get("title", ""),
            text=payload.get("text", ""),
            score=hit.score,
            author=payload.get("author", ""),
            source=payload.get("source", ""),
            tags=payload.get("tags", [])
        ))

    return SearchResponse(
        query=q,
        results=search_results,
        total=len(search_results)
    )
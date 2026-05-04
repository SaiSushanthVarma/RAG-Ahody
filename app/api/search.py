from fastapi import APIRouter, Query, HTTPException
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
    qdrant = get_qdrant()

    try:
        # Build metadata filters
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
                    match=MatchValue(value=tags)
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


@router.get("/search/graph-enhanced")
async def graph_enhanced_search(
    q: str = Query(..., description="Search query"),
    entity_a: str = Query(..., description="First entity to filter by"),
    entity_b: Optional[str] = Query(None, description="Second entity - finds docs mentioning both"),
    top_k: int = Query(5, description="Number of results to return")
):
    """
    Graph-enhanced search combining entity co-occurrence with vector search.
    
    Step 1: Use graph to find documents mentioning entity_a (and entity_b if provided)
    Step 2: Run vector search ONLY within those documents
    
    This gives more precise results than pure vector search alone.
    Example: /search/graph-enhanced?q=AI strategy&entity_a=Sarah Mitchell&entity_b=DataBridge Solutions
    """
    from app.core.database import get_connection

    qdrant = get_qdrant()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Step 1 — Graph: find document IDs where entities co-occur
        if entity_b:
            cursor.execute("""
                SELECT DISTINCT document_id
                FROM co_occurrences
                WHERE (
                    (entity_a = ? AND entity_b = ?)
                    OR
                    (entity_a = ? AND entity_b = ?)
                )
            """, (entity_a, entity_b, entity_b, entity_a))
        else:
            cursor.execute("""
                SELECT DISTINCT document_id
                FROM entities
                WHERE name = ?
            """, (entity_a,))

        rows = cursor.fetchall()
        document_ids = [row["document_id"] for row in rows]

        if not document_ids:
            return {
                "query": q,
                "entity_filter": {"entity_a": entity_a, "entity_b": entity_b},
                "strategy": "graph_enhanced_vector_search",
                "message": f"No documents found for entity filter — falling back to pure vector search",
                "graph_filtered_documents": 0,
                "results": []
            }

        # Step 2 — Vector search filtered to those document IDs only
        query_vector = get_query_embedding(q)

        # Build Qdrant filter for specific document IDs
        from qdrant_client.models import Filter, FieldCondition, MatchAny

        doc_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchAny(any=document_ids)
                )
            ]
        )

        results = qdrant.search(
            collection_name=settings.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=doc_filter,
            with_payload=True
        )

        # Format results
        search_results = []
        for hit in results:
            payload = hit.payload
            search_results.append({
                "chunk_id": payload.get("chunk_id", ""),
                "document_id": payload.get("document_id", ""),
                "title": payload.get("title", ""),
                "text": payload.get("text", ""),
                "score": hit.score,
                "author": payload.get("author", ""),
                "source": payload.get("source", ""),
                "tags": payload.get("tags", [])
            })

        return {
            "query": q,
            "entity_filter": {"entity_a": entity_a, "entity_b": entity_b},
            "strategy": "graph_enhanced_vector_search",
            "message": f"Graph found {len(document_ids)} relevant document(s), vector search returned {len(search_results)} chunk(s)",
            "graph_filtered_documents": len(document_ids),
            "results": search_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
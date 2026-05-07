from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny, SparseVector, FusionQuery, Fusion
from qdrant_client.models import Prefetch
from app.core.config import get_settings
from app.core.auth import verify_api_key
from app.models.schemas import SearchResponse, SearchResult
from app.services.embeddings import get_query_embedding, get_sparse_embedding
from google import genai

router = APIRouter()
settings = get_settings()
gemini_client = genai.Client(api_key=settings.gemini_api_key)


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
    Hybrid search combining dense vector and sparse BM25 search.
    Supports metadata filtering by author, source and tags.
    """
    qdrant = get_qdrant()

    try:
        conditions = []

        if author:
            conditions.append(FieldCondition(key="author", match=MatchValue(value=author)))
        if source:
            conditions.append(FieldCondition(key="source", match=MatchValue(value=source)))
        if tags:
            conditions.append(FieldCondition(key="tags", match=MatchValue(value=tags)))

        search_filter = Filter(must=conditions) if conditions else None

        # Dense vector
        dense_vector = get_query_embedding(q)

        # Sparse BM25 vector
        sparse_indices, sparse_values = get_sparse_embedding(q)

        # Hybrid search using Qdrant fusion
        results = qdrant.query_points(
            collection_name=settings.collection_name,
            prefetch=[
                Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=top_k * 2,
                    filter=search_filter
                ),
                Prefetch(
                    query=SparseVector(
                        indices=sparse_indices,
                        values=sparse_values
                    ),
                    using="sparse",
                    limit=top_k * 2,
                    filter=search_filter
                )
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            with_payload=True
        )

        search_results = []
        for hit in results.points:
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

        # Generate summary of results
        summary = None
        if search_results:
            try:
                summary_prompt = f"""You are a search assistant.
The user searched for: "{q}"

Here are the top results found:
{chr(10).join([f"- [{r.title}] {r.text[:200]}..." for r in search_results])}

Write a 2-3 sentence summary of what was found. Be concise and factual.
Mention which documents are most relevant."""

                response = gemini_client.models.generate_content(
                    model=settings.llm_model,
                    contents=summary_prompt
                )
                summary = response.text
            except Exception:
                pass

        return SearchResponse(
            query=q,
            summary=summary,
            results=search_results,
            total=len(search_results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/graph-enhanced")
async def graph_enhanced_search(
    q: str = Query(..., description="Search query"),
    entity_a: str = Query(..., description="First entity to filter by"),
    entity_b: Optional[str] = Query(None, description="Second entity"),
    top_k: int = Query(5, description="Number of results to return")
):
    """
    3-layer smart search:
    Layer 1 - Graph: find documents where entities co-occur
    Layer 2 - Hybrid search: vector + BM25 within those documents
    Layer 3 - LLM reranking: Gemini re-ranks results by relevance
    """
    from app.core.database import get_connection
    import json

    qdrant = get_qdrant()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Layer 1 — Graph filtering
        if entity_b:
            cursor.execute("""
                SELECT DISTINCT document_id FROM co_occurrences
                WHERE (entity_a = ? AND entity_b = ?)
                OR (entity_a = ? AND entity_b = ?)
            """, (entity_a, entity_b, entity_b, entity_a))
        else:
            cursor.execute("""
                SELECT DISTINCT document_id FROM entities WHERE name = ?
            """, (entity_a,))

        rows = cursor.fetchall()
        document_ids = [row["document_id"] for row in rows]

        if not document_ids:
            return {
                "query": q,
                "strategy": "graph_hybrid_llm",
                "message": f"No documents found for entities",
                "results": []
            }

        # Layer 2 — Hybrid search within graph-filtered documents
        dense_vector = get_query_embedding(q)
        sparse_indices, sparse_values = get_sparse_embedding(q)

        doc_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchAny(any=document_ids)
                )
            ]
        )

        results = qdrant.query_points(
            collection_name=settings.collection_name,
            prefetch=[
                Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=top_k * 2,
                    filter=doc_filter
                ),
                Prefetch(
                    query=SparseVector(
                        indices=sparse_indices,
                        values=sparse_values
                    ),
                    using="sparse",
                    limit=top_k * 2,
                    filter=doc_filter
                )
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k * 2,
            with_payload=True
        )

        if not results.points:
            return {
                "query": q,
                "strategy": "graph_hybrid_llm",
                "message": "No results found",
                "results": []
            }

        # Layer 3 — LLM reranking
        chunks_for_reranking = []
        for i, hit in enumerate(results.points):
            chunks_for_reranking.append({
                "index": i,
                "chunk_id": hit.payload.get("chunk_id", ""),
                "document_id": hit.payload.get("document_id", ""),
                "title": hit.payload.get("title", ""),
                "text": hit.payload.get("text", "")[:500],
                "score": hit.score
            })

        rerank_prompt = f"""You are a search relevance expert.
Given this question: "{q}"

Re-rank these chunks from most to least relevant.
Return ONLY a JSON array of indices in order of relevance, most relevant first.
Example: [2, 0, 3, 1, 4]

Chunks:
{json.dumps([{"index": c["index"], "title": c["title"], "text": c["text"]} for c in chunks_for_reranking], indent=2)}

Return only the JSON array, nothing else:"""

        response = gemini_client.models.generate_content(
            model=settings.llm_model,
            contents=rerank_prompt
        )

        try:
            raw = response.text.strip().replace("```json", "").replace("```", "").strip()
            ranked_indices = json.loads(raw)
        except:
            ranked_indices = list(range(len(chunks_for_reranking)))

        # Build final reranked results
        reranked_results = []
        for rank, idx in enumerate(ranked_indices[:top_k]):
            if idx < len(chunks_for_reranking):
                chunk = chunks_for_reranking[idx]
                hit = results.points[idx]
                reranked_results.append({
                    "rank": rank + 1,
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk["document_id"],
                    "title": chunk["title"],
                    "text": hit.payload.get("text", ""),
                    "hybrid_score": chunk["score"],
                    "author": hit.payload.get("author", ""),
                    "source": hit.payload.get("source", ""),
                    "tags": hit.payload.get("tags", [])
                })

        return {
            "query": q,
            "entity_filter": {"entity_a": entity_a, "entity_b": entity_b},
            "strategy": "graph_hybrid_llm_reranking",
            "message": f"Graph filtered {len(document_ids)} docs → Hybrid search → LLM reranked to top {len(reranked_results)}",
            "graph_filtered_documents": len(document_ids),
            "results": reranked_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
from fastapi import APIRouter, HTTPException
import google.generativeai as genai
from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.models.schemas import ChatRequest, ChatResponse, SourceReference
from app.services.embeddings import get_query_embedding

router = APIRouter()
settings = get_settings()


def get_qdrant():
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the knowledge base.
    Retrieves relevant chunks and generates an answer with source references.
    """
    qdrant = get_qdrant()
    genai.configure(api_key=settings.gemini_api_key)

    try:
        # Step 1 — Embed the question
        query_vector = get_query_embedding(request.question)

        # Step 2 — Retrieve relevant chunks from Qdrant
        results = qdrant.search(
            collection_name=settings.collection_name,
            query_vector=query_vector,
            limit=request.top_k,
            with_payload=True
        )

        if not results:
            return ChatResponse(
                question=request.question,
                answer="I could not find any relevant information in the knowledge base.",
                sources=[]
            )

        # Step 3 — Build context from retrieved chunks
        context_parts = []
        sources = []

        for i, hit in enumerate(results):
            payload = hit.payload
            context_parts.append(
                f"[Source {i+1}] Title: {payload.get('title', 'Unknown')}\n"
                f"{payload.get('text', '')}"
            )
            sources.append(SourceReference(
                document_id=payload.get("document_id", ""),
                chunk_id=payload.get("chunk_id", ""),
                title=payload.get("title", ""),
                text=payload.get("text", ""),
                score=hit.score
            ))

        context = "\n\n---\n\n".join(context_parts)

        # Step 4 — Generate answer with Gemini
        prompt = f"""You are a helpful assistant for a knowledge base.
Answer the question based ONLY on the provided sources below.
Always reference which source(s) you used by saying [Source 1], [Source 2] etc.
If the answer is not in the sources, say "I could not find this information in the knowledge base."

Sources:
{context}

Question: {request.question}

Answer:"""

        model = genai.GenerativeModel(settings.llm_model)
        response = model.generate_content(prompt)

        return ChatResponse(
            question=request.question,
            answer=response.text,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
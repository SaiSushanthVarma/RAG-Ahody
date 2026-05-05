from fastapi import APIRouter, HTTPException
from google import genai
from groq import Groq
from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.models.schemas import ChatRequest, ChatResponse, SourceReference
from app.services.embeddings import get_query_embedding

router = APIRouter()
settings = get_settings()

gemini_client = genai.Client(api_key=settings.gemini_api_key)
groq_client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None


def get_qdrant():
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )


def generate_answer(prompt: str) -> str:
    """Generate answer with Gemini, fall back to Groq if unavailable."""
    try:
        response = gemini_client.models.generate_content(
            model=settings.llm_model,
            contents=prompt
        )
        return response.text
    except Exception as e:
        if groq_client and ("503" in str(e) or "UNAVAILABLE" in str(e) or "429" in str(e)):
            print(f"Gemini unavailable, falling back to Groq: {e}")
            response = groq_client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        raise e


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the knowledge base.
    Retrieves relevant chunks and generates answer with source references.
    Falls back to Groq if Gemini is unavailable.
    """
    qdrant = get_qdrant()

    try:
        query_vector = get_query_embedding(request.question)

        results = qdrant.search(
            collection_name=settings.collection_name,
            query_vector=query_vector,
            vector_name="dense",
            limit=request.top_k,
            with_payload=True
        )

        if not results:
            return ChatResponse(
                question=request.question,
                answer="I could not find any relevant information in the knowledge base.",
                sources=[]
            )

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

        prompt = f"""You are a helpful assistant for a knowledge base.
Answer the question based ONLY on the provided sources below.
Always reference which source(s) you used by saying [Source 1], [Source 2] etc.
If the answer is not in the sources, say "I could not find this information in the knowledge base."

Sources:
{context}

Question: {request.question}

Answer:"""

        answer = generate_answer(prompt)

        return ChatResponse(
            question=request.question,
            answer=answer,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
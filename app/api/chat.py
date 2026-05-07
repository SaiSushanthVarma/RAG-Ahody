from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from google import genai
from groq import Groq
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import json

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


def get_relevant_chunks(question: str, top_k: int):
    """Retrieve relevant chunks using dense vector search."""
    qdrant = get_qdrant()
    query_vector = get_query_embedding(question)

    results = qdrant.query_points(
        collection_name=settings.collection_name,
        query=query_vector,
        using="dense",
        limit=top_k,
        with_payload=True
    ).points

    return results


def build_prompt(question: str, results: list) -> tuple[str, list]:
    """Build prompt and sources from results."""
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

Question: {question}

Answer:"""

    return prompt, sources


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


async def stream_answer(prompt: str, sources: list):
    """Stream response using SSE."""
    try:
        # Send sources first
        sources_data = [
            {
                "document_id": s.document_id,
                "chunk_id": s.chunk_id,
                "title": s.title,
                "score": s.score
            }
            for s in sources
        ]
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources_data})}\n\n"

        # Stream Gemini response
        try:
            response = gemini_client.models.generate_content_stream(
                model=settings.llm_model,
                contents=prompt
            )
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'type': 'token', 'text': chunk.text})}\n\n"

        except Exception as e:
            if groq_client and ("503" in str(e) or "UNAVAILABLE" in str(e) or "429" in str(e)):
                print(f"Gemini unavailable, falling back to Groq: {e}")
                response = groq_client.chat.completions.create(
                    model=settings.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True
                )
                for chunk in response:
                    text = chunk.choices[0].delta.content or ""
                    if text:
                        yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the knowledge base.
    Retrieves relevant chunks and generates answer with source references.
    Falls back to Groq if Gemini is unavailable.
    """
    try:
        results = get_relevant_chunks(request.question, request.top_k)

        if not results:
            return ChatResponse(
                question=request.question,
                answer="I could not find any relevant information in the knowledge base.",
                sources=[]
            )

        prompt, sources = build_prompt(request.question, results)
        answer = generate_answer(prompt)

        return ChatResponse(
            question=request.question,
            answer=answer,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint using Server-Sent Events.
    Returns tokens as they are generated.

    Response format:
    data: {"type": "sources", "sources": [...]}
    data: {"type": "token", "text": "..."}
    data: {"type": "done"}
    """
    try:
        results = get_relevant_chunks(request.question, request.top_k)

        if not results:
            async def empty_stream():
                yield f"data: {json.dumps({'type': 'sources', 'sources': []})}\n\n"
                yield f"data: {json.dumps({'type': 'token', 'text': 'I could not find any relevant information in the knowledge base.'})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return StreamingResponse(empty_stream(), media_type="text/event-stream")

        prompt, sources = build_prompt(request.question, results)

        return StreamingResponse(
            stream_answer(prompt, sources),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
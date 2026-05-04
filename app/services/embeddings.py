import google.generativeai as genai
from app.core.config import get_settings

settings = get_settings()


def init_gemini():
    genai.configure(api_key=settings.gemini_api_key)


def get_embedding(text: str) -> list[float]:
    """
    Generate embedding for a single text using Gemini text-embedding-004.
    Returns a 768-dimensional vector.
    """
    init_gemini()
    result = genai.embed_content(
        model=settings.embedding_model,
        content=text,
        task_type="retrieval_document"
    )
    return result["embedding"]


def get_query_embedding(text: str) -> list[float]:
    """
    Generate embedding for a search query.
    Uses retrieval_query task type for better search results.
    """
    init_gemini()
    result = genai.embed_content(
        model=settings.embedding_model,
        content=text,
        task_type="retrieval_query"
    )
    return result["embedding"]
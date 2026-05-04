from google import genai
from google.genai import types
from app.core.config import get_settings

settings = get_settings()

client = genai.Client(api_key=settings.gemini_api_key)


def get_embedding(text: str) -> list[float]:
    """
    Generate embedding for document using text-embedding-004.
    Returns a 768-dimensional vector.
    """
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
        config=types.EmbedContentConfig(task_type="retrieval_document")
    )
    return result.embeddings[0].values


def get_query_embedding(text: str) -> list[float]:
    """
    Generate embedding for search query.
    Uses retrieval_query for better search accuracy.
    """
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=text,
        config=types.EmbedContentConfig(task_type="retrieval_query")
    )
    return result.embeddings[0].values
from google import genai
from google.genai import types
from app.core.config import get_settings
from fastembed import SparseTextEmbedding

settings = get_settings()
client = genai.Client(api_key=settings.gemini_api_key)

# Initialize sparse embedding model (BM25)
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")


def get_embedding(text: str) -> list[float]:
    """
    Generate dense embedding for document using gemini-embedding-001.
    Returns a 3072-dimensional vector.
    """
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    return result.embeddings[0].values


def get_query_embedding(text: str) -> list[float]:
    """
    Generate dense embedding for search query.
    Uses retrieval_query for better search accuracy.
    """
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    return result.embeddings[0].values


def get_sparse_embedding(text: str) -> tuple[list[int], list[float]]:
    """
    Generate sparse BM25 embedding for hybrid search.
    Returns indices and values for sparse vector.
    """
    embeddings = list(sparse_model.embed([text]))
    sparse = embeddings[0]
    return sparse.indices.tolist(), sparse.values.tolist()
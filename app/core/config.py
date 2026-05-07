from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    

    # API key for securing endpoints
    api_key: str

    # Qdrant collection name
    collection_name: str = "knowledge_base"
    
    # Embedding settings
    embedding_model: str = "gemini-embedding-001"
    embedding_dimension: int = 3072
    
    # Gemini LLM model
    llm_model: str = "gemini-2.5-flash-lite"

    groq_api_key: str = ""
    groq_model: str = "qwen3-32b"
    
    # Chunking settings
    chunk_size: int = 512
    chunk_overlap: int = 48

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    gemini_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    
    # Qdrant collection name
    collection_name: str = "knowledge_base"
    
    # Embedding settings
    embedding_model: str = "gemini-embedding-001"
    embedding_dimension: int = 3072
    
    # Gemini LLM model
    llm_model: str = "gemini-2.5-flash"
    
    # Chunking settings
    chunk_size: int = 500
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
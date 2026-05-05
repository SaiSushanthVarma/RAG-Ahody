from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import init_db
from app.core.auth import verify_api_key
from app.api import documents, search, chat, graph

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType, SparseVectorParams, SparseIndexParams

settings = get_settings()


def init_qdrant():
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )

    existing = [c.name for c in client.get_collections().collections]

    if settings.collection_name not in existing:
        client.create_collection(
            collection_name=settings.collection_name,
            vectors_config={
                "dense": VectorParams(
                    size=settings.embedding_dimension,
                    distance=Distance.COSINE
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            }
        )
        print(f"Created Qdrant collection with dense + sparse vectors: {settings.collection_name}")
    else:
        print(f"Qdrant collection already exists: {settings.collection_name}")

    client.create_payload_index(
        collection_name=settings.collection_name,
        field_name="author",
        field_schema=PayloadSchemaType.KEYWORD
    )
    client.create_payload_index(
        collection_name=settings.collection_name,
        field_name="source",
        field_schema=PayloadSchemaType.KEYWORD
    )
    client.create_payload_index(
        collection_name=settings.collection_name,
        field_name="tags",
        field_schema=PayloadSchemaType.KEYWORD
    )
    client.create_payload_index(
        collection_name=settings.collection_name,
        field_name="document_id",
        field_schema=PayloadSchemaType.KEYWORD
    )
    print("Payload indexes created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    init_db()
    init_qdrant()
    print("Ready!")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Ahody Knowledge Base API",
    description="RAG-powered knowledge base with semantic search and entity graph",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routes protected by API key
app.include_router(
    documents.router,
    tags=["Documents"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    search.router,
    tags=["Search"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    chat.router,
    tags=["Chat"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    graph.router,
    tags=["Graph"],
    dependencies=[Depends(verify_api_key)]
)


@app.get("/")
async def root():
    return {
        "message": "Ahody Knowledge Base API",
        "version": "1.0.0",
        "endpoints": [
            "POST /text",
            "POST /document",
            "GET /search",
            "POST /chat",
            "GET /graph",
            "GET /graph/search",
            "GET /search/graph-enhanced"
        ]
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "groq_fallback_model": settings.groq_model,
        "collection": settings.collection_name,
        "embedding_dimension": settings.embedding_dimension
    }
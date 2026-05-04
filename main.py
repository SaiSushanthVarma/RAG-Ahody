from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import init_db
from app.api import documents, search, chat, graph

from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PayloadSchemaType

settings = get_settings()


def init_qdrant():
    """Create Qdrant collection and indexes if they don't exist."""
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )

    existing = [c.name for c in client.get_collections().collections]

    if settings.collection_name not in existing:
        client.create_collection(
            collection_name=settings.collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dimension,
                distance=Distance.COSINE
            )
        )
        print(f"Created Qdrant collection: {settings.collection_name}")
    else:
        print(f"Qdrant collection already exists: {settings.collection_name}")

    # Create payload indexes for metadata filtering
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
    print("Payload indexes created for author, source, tags")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and Qdrant on startup."""
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

app.include_router(documents.router, tags=["Documents"])
app.include_router(search.router, tags=["Search"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(graph.router, tags=["Graph"])


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
            "GET /graph"
        ]
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
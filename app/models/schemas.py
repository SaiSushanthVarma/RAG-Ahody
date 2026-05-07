from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# --- Upload schemas ---

class TextUploadRequest(BaseModel):
    text: str
    title: str
    author: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = []


class DocumentUploadResponse(BaseModel):
    document_id: str
    title: str
    chunks_created: int
    entities_extracted: int
    message: str


# --- Search schemas ---

class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    title: str
    text: str
    score: float
    author: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = []


class SearchResponse(BaseModel):
    query: str
    summary: Optional[str] = None
    results: List[SearchResult]
    total: int

# --- Chat schemas ---

class ChatRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class SourceReference(BaseModel):
    document_id: str
    chunk_id: str
    title: str
    text: str
    score: float


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceReference]


# --- Graph schemas ---

class GraphNode(BaseModel):
    id: str
    name: str
    entity_type: str
    document_count: int


class GraphEdge(BaseModel):
    source: str
    target: str
    document_id: str
    weight: int


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
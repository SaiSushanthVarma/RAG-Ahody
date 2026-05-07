# Ahody Knowledge Base API

A RAG-powered internal knowledge base where teams can upload source material and ask questions in, with full source references.

---

## Background

The core RAG architecture in this project builds on patterns I developed while building a production Swedish tax advisor (swedentax.vercel.app),a deployed AI system that answers questions from official Skatteverket documents in Swedish and English across 7,224 chunks. That project taught me the hard lessons: why PDF quality is 80% of RAG quality, how silent chunk failures kill retrieval, the difference between embedding models and LLMs, and how to debug AI pipelines in production.

This project takes those foundations and extends them with hybrid search, entity graph extraction, LLM reranking, and a more structured metadata model that the advisor dodn't need but a general knowledgebase does.

---

## Stack

| Layer | Choice | Why |

| Backend | Python + FastAPI | Simple, fast, automatic API docs |
| Vector DB | Qdrant Cloud | Native hybrid search support, persistent, free tier |
| LLM | Gemini 2.5 Flash Lite | Best free-tier model for RAG and instruction following |
| LLM Fallback | Qwen3-32B via Groq | Auto fallback when Gemini hits rate limits |
| Embeddings | gemini-embedding-001 | Google's latest, 3072 dimensions, purpose-built for RAG |
| Sparse vectors | BM25 via fastembed | Keyword matching to complement semantic search |
| Entity storage | SQLite | Lightweight, no extra infrastructure needed |
| PDF extraction | PyMuPDF | Fast, reliable, handles multi-page documents |

---

## How to Run

### Prerequisites
- Python 3.11 or 3.12 (3.14 not yet fully supported by all dependencies)
- Qdrant Cloud account — free at cloud.qdrant.io
- Google AI Studio account — free at aistudio.google.com
- Groq account — free at console.groq.com

### Setup

```bash
# Clone the repo
git clone https://github.com/SaiSushanthVarma/RAG-Ahody.git
cd RAG-Ahody

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env template and fill in your keys
cp .env.example .env
```

Edit `.env`:
GEMINI_API_KEY=your_gemini_api_key
QDRANT_URL=your_qdrant_cluster_url
QDRANT_API_KEY=your_qdrant_api_key
API_KEY=ahody-secret-key-2026
GROQ_API_KEY=your_groq_api_key

### Start the server
```bash
uvicorn main:app --reload
```

### Load sample documents
```bash
# Linux/Mac
bash sample_data/load_samples.sh

# Windows — use Git Bash or import postman_collection.json into Postman
```

### API Documentation
Visit `http://127.0.0.1:8000/docs` — click Authorize and enter your API key.

### Check which models are running
```bash
curl http://127.0.0.1:8000/health -H "X-API-Key: your_key"
```

---

## Authentication

All endpoints require an API key header:
X-API-Key: your_api_key

In Swagger UI click the Authorize button at the top right and enter your key.

---

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /text | Upload plain text with metadata |
| POST | /document | Upload PDF, text extracted server-side |
| POST | /chat/stream | Streaming chat via Server-Sent Events |
| GET | /search | Hybrid search with metadata filtering + LLM summary |
| GET | /search/graph-enhanced | Graph + hybrid + LLM reranking |
| POST | /chat | RAG chat with source references |
| GET | /graph | Entity relationship graph |
| GET | /graph/search | Find documents by entity co-occurrence |
| GET | /health | Health check with model info |

---

## Metadata Fields

When uploading documents:

```json
{
  "text": "document content",
  "title": "Document Title",
  "author": "Author Name",
  "source": "Internal Memo",
  "tags": ["finance", "Q2", "2024"]
}
```

Filter search results by `author`, `source`, and `tags`.

---

## Retrieval Pipeline
User query
 Layer 1: Graph filtering
SQLite co-occurrences finds documents where both entities appear together

 Layer 2: Hybrid search (Gemini embeddings + BM25 via Reciprocal Rank Fusion)
vector finds semantic matches
BM25 finds exact keyword matches
RRF combines both scores

 Layer 3: LLM reranking
Gemini re-ranks results by actual relevance to the question
 Final results with LLM-generated summary

Available via `GET /search/graph-enhanced`.

---

## Data Model

### SQLite — documents table
```sql
documents (
  id TEXT PRIMARY KEY,
  title TEXT,
  author TEXT,
  source TEXT,
  tags TEXT,
  doc_type TEXT,
  created_at TIMESTAMP
)
```

### SQLite — entities table
```sql
entities (
  id INTEGER PRIMARY KEY,
  document_id TEXT,
  name TEXT,
  entity_type TEXT  -- people, organizations, places
)
```

### SQLite — co_occurrences table
```sql
co_occurrences (
  id INTEGER PRIMARY KEY,
  entity_a TEXT,
  entity_b TEXT,
  document_id TEXT,
  chunk_id TEXT
)
```

### Qdrant — vector points
```json
{
  "id": "uuid",
  "vector": {
    "dense": [3072 floats],
    "sparse": {"indices": [...], "values": [...]}
  },
  "payload": {
    "chunk_id": "doc_id_chunk_0",
    "document_id": "uuid",
    "text": "chunk text",
    "title": "document title",
    "author": "author name",
    "source": "source name",
    "tags": ["tag1", "tag2"],
    "chunk_index": 0
  }
}
```

---

## Architectural Choices and Tradeoffs

### Chunk size: 512 tokens, 48 overlap
512 tokens gives a focused paragraph-level context large enough to contain complete sentences and ideas, small enough to return precise results without noise. 1024 would return too much text per chunk making it harder to pinpoint the exact relevant passage. 256 would cut sentences mid-thought and lose context. 48 token overlap ensures context is preserved at chunk boundaries,if a key sentence falls at the boundary between two chunks it appears in both. This is slightly tighter than what I used in the Swedish tax project (where longer chunks helped with legal document structure) because internal memos have shorter, more modular paragraphs.

### Embedding model: gemini-embedding-001
Google's latest embedding model, 3072 dimensions, purpose-built for RAG. Chosen because we already use Gemini for the LLM  one provider, one API key, consistent quality. In the Swedish tax project I used mxbai-embed-large via HuggingFace which worked well locally but required self-hosting. gemini-embedding-001 removes that dependency entirely. text-embedding-004 was deprecated January 2026 so this is the current stable model.

### Hybrid search: dense vectors + BM25
Pure vector search misses exact keyword matches names, numbers, specific terms like "5 million SEK". Pure BM25 misses semantic meaning  "financial performance" won't match "revenue growth" without vector search. Hybrid with RRF fusion gives both. Qdrant supports this natively. In the tax project I used pure vector search adding BM25 here was a deliberate improvement based on what I learned about retrieval failures with specific named entities.

### LLM reranking
After hybrid search, Gemini re-reads the top results and re-orders them by actual relevance to the question. This is something I wished I had built into the tax advisor  where retrieval order affected answer quality significantly. Here it's implemented as non-blocking so if it fails the search still returns results.

### Graph storage: SQLite relations table vs Neo4j
A co-occurrence table in SQLite achieves the core requirement  finding documents where two entities appear together  without adding infrastructure complexity. Neo4j would require a separate server and the Cypher query language. With more time I would migrate to Neo4j for multi-hop graph traversal, for example finding all people connected to Sarah Mitchell within 2 degrees.

### Groq fallback
Gemini free tier has daily limits. When Gemini returns 503 or 429 the system automatically falls back to Qwen3-32B via Groq for chat and entity extraction. I ran Qwen locally in the tax project running it via Groq API here is faster and removes the hardware dependency.

### What would I have done differently with more time?
- **Neo4j** for proper graph traversal instead of SQLite relations table
- **Streaming responses** on the chat endpoint for better UX
- **Chunk size evaluation** — run offline evals across chunk sizes using a test question set to find the optimal for this specific document type
- **Contradiction detection** — explicitly flag when two documents disagree rather than letting the LLM handle it silently

---

## What I Built vs What I Left Out

### Built
- POST /text — upload plain text with metadata 
- POST /document — upload PDF with server-side text extraction 
- Streaming chat responses via SSE — POST /chat/stream 
- Chunking + embeddings + persistent storage 
- GET /search — hybrid search with score and document reference 
- Metadata filtering by author, source, tags 
- POST /chat — RAG with LLM answer and source references 
- Persistence — Qdrant Cloud + SQLite survive restarts 
- Graph entity extraction and co-occurrence storage 
- Graph-enhanced retrieval — GET /graph/search 
- Hybrid search — dense vectors + BM25 via RRF 
- LLM reranking of search results 
- API key authentication 

### Left Out and Why

**Neo4j/Memgraph** — SQLite relations table achieves the same retrieval improvement with zero extra infrastructure. Pragmatic choice. 
**Contradiction detection**
When two documents disagree the chat endpoint currently lets Gemini handle it naturally. A proper implementation would explicitly detect semantic similarity with conflicting facts and surface both versions to the user with a warning. This is something I want to build into the next project.

**Hybrid search on graph-enhanced endpoint**
The /search/graph-enhanced endpoint uses hybrid search for retrieval but the /chat endpoint still uses dense-only vector search. With more time I would unify both to use the full hybrid pipeline consistently.

**Document deletion and updates**
No endpoint to delete or update documents. Once uploaded a document stays forever. A production system needs versioning and the ability to remove outdated content from both Qdrant and SQLite.
---

## How I Used AI Tools

I used Claude as the primary coding assistant throughout this project. My approach to AI collaboration comes from building the Swedish tax advisor — where I learned that the AI is good at boilerplate and bad at architectural decisions, and that the most important skill is knowing which decisions to take back.

### What I delegated to AI
- Boilerplate FastAPI route setup and Pydantic schema definitions
- Qdrant client initialization code
- SQLite schema creation
- Entity extraction prompt template
- Initial service file structure

### What I decided myself
- **Chunk size of 512 tokens with 48 overlap** — based on the document type (internal memos have shorter paragraphs than legal documents) and lessons from the tax project
- **SQLite over Neo4j** — pragmatism over complexity
- **gemini-embedding-001 over Voyage AI** — single provider reduces complexity. Voyage AI free tier had only 3 RPM without a payment method which would have blocked testing
- **3-layer retrieval pipeline** — graph filtering → hybrid search → LLM reranking. This architecture was my own design based on what I learned about retrieval failures in the tax project. The AI would have built a simpler single-step vector search
- **Groq as fallback** — added after hitting Gemini rate limits during development, based on experience running Qwen locally in the tax project
- **Non-blocking entity extraction** — if the LLM fails during upload the document still gets indexed. The AI's original implementation would block the entire upload on entity extraction failure
- **What to leave out and why** — streaming and Neo4j were conscious tradeoff decisions

### Where I corrected the AI
- Initial embedding model was `text-embedding-004` which was deprecated January 2026 — upgraded to `gemini-embedding-001`
- AI used deprecated `google-generativeai` library — migrated to `google-genai` SDK
- AI used wrong Qdrant import name `PrefetchQuery` — corrected to `Prefetch` after debugging
- AI suggested Neo4j — overrode with SQLite relations table
- AI did not handle entity extraction failures — made it non-blocking
- AI missed Qdrant payload index for `document_id` — added after graph-enhanced search failed in testing
- AI generated entity extraction that blocked the upload pipeline when the LLM was rate limited — restructured to be fault-tolerant

---

## Sample Data

Four related documents about fictional company NordMedia Group in `/sample_data`:

- `memo1.txt` — Q1 Strategy Update (author: Sarah Mitchell, tags: strategy, Q1, 2024)
- `memo2.txt` — AI Platform Launch Update (author: Erik Lindqvist, tags: AI, platform, 2024)
- `memo3.txt` — Q2 Financial Review (author: Marcus Johansson, tags: finance, Q2, 2024)
- `board_report_q2_2024.pdf` — Board Report Q2 2024 (author: Sarah Mitchell, tags: board, Q2, finance)

All four documents share the same entities (Sarah Mitchell, Erik Lindqvist, DataBridge Solutions, Stockholm) making them ideal for demonstrating:
- **Metadata filtering** — search by author or tags returns only matching documents
- **Cross-document semantic search** — body text vectors match relevant content across all 4 documents
- **Entity graph** — shared people and organizations appear as connected nodes
- **Chat with source references** — answers cite specific chunks from specific documents

Load them:
```bash
# Linux/Mac
bash sample_data/load_samples.sh

# Windows — use Git Bash, or import postman_collection.json into Postman and run upload requests
```

---

## Testing

Import `postman_collection.json` into Postman for one-click testing of all endpoints.
See `curl_examples.sh` for curl commands.

**Postman setup:**
1. Open Postman desktop app
2. Click Import → select `postman_collection.json`
3. Click the collection → Edit → Authorization → enter `ahody-secret-key-2026`
4. Run requests in this order: Health Check → Upload memos → Upload PDF → Search → Chat → Graph

**Key test cases that demonstrate the requirements:**

```bash
# Metadata filtering — returns only Sarah Mitchell's documents
curl "http://127.0.0.1:8000/search?q=AI+platform&author=Sarah+Mitchell" \
  -H "X-API-Key: ahody-secret-key-2026"

# Body text vectors — finds related content across documents
curl "http://127.0.0.1:8000/search?q=DataBridge+Solutions+revenue+expansion" \
  -H "X-API-Key: ahody-secret-key-2026"

# Chat with verifiable source references
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "X-API-Key: ahody-secret-key-2026" \
  -H "Content-Type: application/json" \
  -d '{"question": "Who approved the Norway expansion and what was the investment amount?"}'

# Graph search — find all docs mentioning both entities together
curl "http://127.0.0.1:8000/graph/search?entity_a=Sarah+Mitchell&entity_b=DataBridge+Solutions" \
  -H "X-API-Key: ahody-secret-key-2026"

# 3-layer search — graph + hybrid + LLM reranking
curl "http://127.0.0.1:8000/search/graph-enhanced?q=AI+strategy&entity_a=Sarah+Mitchell&entity_b=DataBridge+Solutions" \
  -H "X-API-Key: ahody-secret-key-2026"
```

---

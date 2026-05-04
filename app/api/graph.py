from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from collections import defaultdict

from app.core.database import get_connection
from app.models.schemas import GraphResponse, GraphNode, GraphEdge

router = APIRouter()


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    document_id: Optional[str] = Query(None, description="Filter by document"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type e.g. people, organizations, places")
):
    """
    Returns entities and their relationships as nodes and edges.
    Used for graph visualization of the knowledge base.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        entity_query = "SELECT name, entity_type, document_id FROM entities WHERE 1=1"
        entity_params = []

        if document_id:
            entity_query += " AND document_id = ?"
            entity_params.append(document_id)

        if entity_type:
            entity_query += " AND entity_type = ?"
            entity_params.append(entity_type)

        cursor.execute(entity_query, entity_params)
        entity_rows = cursor.fetchall()

        node_map = defaultdict(lambda: {"entity_type": "", "documents": set()})

        for row in entity_rows:
            name = row["name"]
            node_map[name]["entity_type"] = row["entity_type"]
            node_map[name]["documents"].add(row["document_id"])

        nodes = [
            GraphNode(
                id=name,
                name=name,
                entity_type=data["entity_type"],
                document_count=len(data["documents"])
            )
            for name, data in node_map.items()
        ]

        edge_query = "SELECT entity_a, entity_b, document_id FROM co_occurrences WHERE 1=1"
        edge_params = []

        if document_id:
            edge_query += " AND document_id = ?"
            edge_params.append(document_id)

        cursor.execute(edge_query, edge_params)
        edge_rows = cursor.fetchall()

        edge_map = defaultdict(int)
        edge_docs = {}

        for row in edge_rows:
            key = (row["entity_a"], row["entity_b"])
            edge_map[key] += 1
            edge_docs[key] = row["document_id"]

        edges = [
            GraphEdge(
                source=key[0],
                target=key[1],
                document_id=edge_docs[key],
                weight=weight
            )
            for key, weight in edge_map.items()
        ]

        return GraphResponse(nodes=nodes, edges=edges)

    finally:
        conn.close()


@router.get("/graph/search")
async def graph_search(
    entity_a: str = Query(..., description="First entity name"),
    entity_b: Optional[str] = Query(None, description="Second entity name - finds documents mentioning both"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type")
):
    """
    Graph-enhanced retrieval endpoint.
    Find all documents that mention entity_a, or both entity_a AND entity_b together.
    This shows how the graph improves retrieval beyond pure vector search.
    
    Example: /graph/search?entity_a=Sarah Mitchell&entity_b=DataBridge Solutions
    Returns all documents where both are mentioned together.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        if entity_b:
            # Find documents where BOTH entities co-occur
            cursor.execute("""
                SELECT DISTINCT c.document_id, d.title, d.author, d.source, d.tags
                FROM co_occurrences c
                JOIN documents d ON c.document_id = d.id
                WHERE (
                    (c.entity_a = ? AND c.entity_b = ?)
                    OR
                    (c.entity_a = ? AND c.entity_b = ?)
                )
            """, (entity_a, entity_b, entity_b, entity_a))

            rows = cursor.fetchall()

            if not rows:
                return {
                    "query": {"entity_a": entity_a, "entity_b": entity_b},
                    "strategy": "graph_co_occurrence",
                    "message": f"No documents found mentioning both '{entity_a}' and '{entity_b}' together",
                    "documents": []
                }

            documents = []
            for row in rows:
                # Get all entities in this document
                cursor.execute("""
                    SELECT name, entity_type FROM entities
                    WHERE document_id = ?
                    ORDER BY entity_type
                """, (row["document_id"],))
                entities = cursor.fetchall()

                documents.append({
                    "document_id": row["document_id"],
                    "title": row["title"],
                    "author": row["author"],
                    "source": row["source"],
                    "tags": row["tags"].split(",") if row["tags"] else [],
                    "entities": [
                        {"name": e["name"], "type": e["entity_type"]}
                        for e in entities
                    ]
                })

            return {
                "query": {"entity_a": entity_a, "entity_b": entity_b},
                "strategy": "graph_co_occurrence",
                "message": f"Found {len(documents)} document(s) mentioning both '{entity_a}' and '{entity_b}'",
                "documents": documents
            }

        else:
            # Find all documents mentioning entity_a
            query = """
                SELECT DISTINCT e.document_id, d.title, d.author, d.source, d.tags
                FROM entities e
                JOIN documents d ON e.document_id = d.id
                WHERE e.name = ?
            """
            params = [entity_a]

            if entity_type:
                query += " AND e.entity_type = ?"
                params.append(entity_type)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                return {
                    "query": {"entity_a": entity_a},
                    "strategy": "graph_entity_lookup",
                    "message": f"No documents found mentioning '{entity_a}'",
                    "documents": []
                }

            documents = []
            for row in rows:
                cursor.execute("""
                    SELECT name, entity_type FROM entities
                    WHERE document_id = ?
                    ORDER BY entity_type
                """, (row["document_id"],))
                entities = cursor.fetchall()

                documents.append({
                    "document_id": row["document_id"],
                    "title": row["title"],
                    "author": row["author"],
                    "source": row["source"],
                    "tags": row["tags"].split(",") if row["tags"] else [],
                    "entities": [
                        {"name": e["name"], "type": e["entity_type"]}
                        for e in entities
                    ]
                })

            return {
                "query": {"entity_a": entity_a},
                "strategy": "graph_entity_lookup",
                "message": f"Found {len(documents)} document(s) mentioning '{entity_a}'",
                "documents": documents
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
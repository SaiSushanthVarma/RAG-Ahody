from fastapi import APIRouter, Query
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
        # Build entity query with optional filters
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

        # Build nodes — deduplicate by name
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

        # Build edges from co-occurrences
        edge_query = "SELECT entity_a, entity_b, document_id FROM co_occurrences WHERE 1=1"
        edge_params = []

        if document_id:
            edge_query += " AND document_id = ?"
            edge_params.append(document_id)

        cursor.execute(edge_query, edge_params)
        edge_rows = cursor.fetchall()

        # Count edge weights (how many times two entities co-occur)
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
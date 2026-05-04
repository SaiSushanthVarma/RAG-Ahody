import sqlite3
import os

DB_PATH = "knowledge_base.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            source TEXT,
            tags TEXT,
            doc_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Entities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            name TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)

    # Co-occurrences table (for graph)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS co_occurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_a TEXT NOT NULL,
            entity_b TEXT NOT NULL,
            document_id TEXT NOT NULL,
            chunk_id TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
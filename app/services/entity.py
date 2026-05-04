import json
from google import genai
from app.core.config import get_settings

settings = get_settings()

client = genai.Client(api_key=settings.gemini_api_key)


def extract_entities(text: str) -> dict:
    """
    Extract named entities from text using Gemini.
    Returns people, organizations and places found in the text.
    """
    prompt = f"""Extract all named entities from the following text.
Return ONLY a valid JSON object with no extra text, no markdown, no backticks.

Format:
{{
    "people": ["name1", "name2"],
    "organizations": ["org1", "org2"],
    "places": ["place1", "place2"]
}}

If none found for a category return an empty list.

Text:
{text}"""

    response = client.models.generate_content(
        model=settings.llm_model,
        contents=prompt
    )

    try:
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        entities = json.loads(raw)
        return entities
    except json.JSONDecodeError:
        return {"people": [], "organizations": [], "places": []}


def store_entities(document_id: str, chunk_id: str, entities: dict, conn) -> int:
    """
    Store extracted entities and co-occurrences in SQLite.
    Returns total number of entities stored.
    """
    cursor = conn.cursor()
    total = 0
    all_entities = []

    for entity_type, names in entities.items():
        for name in names:
            if name.strip():
                cursor.execute("""
                    INSERT INTO entities (document_id, name, entity_type)
                    VALUES (?, ?, ?)
                """, (document_id, name.strip(), entity_type))
                all_entities.append(name.strip())
                total += 1

    for i in range(len(all_entities)):
        for j in range(i + 1, len(all_entities)):
            cursor.execute("""
                INSERT INTO co_occurrences (entity_a, entity_b, document_id, chunk_id)
                VALUES (?, ?, ?, ?)
            """, (all_entities[i], all_entities[j], document_id, chunk_id))

    return total
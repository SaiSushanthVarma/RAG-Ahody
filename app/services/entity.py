import json
import google.generativeai as genai
from app.core.config import get_settings

settings = get_settings()


def extract_entities(text: str) -> dict:
    """
    Extract named entities from text using Gemini.
    Returns people, organizations and places found in the text.
    """
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.llm_model)

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

    response = model.generate_content(prompt)
    
    try:
        # Clean response in case model adds extra formatting
        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        entities = json.loads(raw)
        return entities
    except json.JSONDecodeError:
        # Return empty if parsing fails
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

    # Store co-occurrences between all entities in this chunk
    for i in range(len(all_entities)):
        for j in range(i + 1, len(all_entities)):
            cursor.execute("""
                INSERT INTO co_occurrences (entity_a, entity_b, document_id, chunk_id)
                VALUES (?, ?, ?, ?)
            """, (all_entities[i], all_entities[j], document_id, chunk_id))

    return total
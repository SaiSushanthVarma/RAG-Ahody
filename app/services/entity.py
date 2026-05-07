import json
from google import genai
from groq import Groq
from app.core.config import get_settings

settings = get_settings()
gemini_client = genai.Client(api_key=settings.gemini_api_key)
groq_client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None


def extract_entities_with_gemini(text: str) -> dict:
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

    response = gemini_client.models.generate_content(
        model=settings.llm_model,
        contents=prompt
    )
    raw = response.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def extract_entities_with_groq(text: str) -> dict:
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

    response = groq_client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def extract_entities(text: str) -> dict:
    """
    Extract entities with Gemini, fall back to Groq if unavailable.
    """
    try:
        return extract_entities_with_gemini(text)
    except Exception as e:
        if groq_client and ("503" in str(e) or "UNAVAILABLE" in str(e) or "429" in str(e)):
            print(f"Gemini unavailable, falling back to Groq: {e}")
            return extract_entities_with_groq(text)
        return {"people": [], "organizations": [], "places": []}


def store_entities(document_id: str, chunk_id: str, entities: dict, conn) -> int:
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
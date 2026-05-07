#!/bin/bash
# Ahody Knowledge Base API - curl examples
# Make sure server is running: uvicorn main:app --reload
# Replace API_KEY with your actual key

BASE_URL="http://127.0.0.1:8000"
API_KEY="ahody-secret-key-2026"

echo "=== 1. Health Check ==="
curl "$BASE_URL/health" \
  -H "X-API-Key: $API_KEY"

echo -e "\n\n=== 2. Upload Plain Text ==="
curl -X POST "$BASE_URL/text" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "text": "INTERNAL MEMO - Q1 Strategy Update. NordMedia Group had a strong start to 2024 under CEO Sarah Mitchell.",
    "title": "Q1 Strategy Update",
    "author": "Sarah Mitchell",
    "source": "Internal Memo",
    "tags": ["strategy", "Q1", "2024"]
  }'

echo -e "\n\n=== 3. Upload PDF Document ==="
curl -X POST "$BASE_URL/document" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@sample_data/board_report_q2_2024.pdf" \
  -F "title=Board Report Q2 2024" \
  -F "author=Sarah Mitchell" \
  -F "source=Board Report" \
  -F "tags=board,Q2,2024,finance"

echo -e "\n\n=== 4. Hybrid Search ==="
curl "$BASE_URL/search?q=AI+platform+revenue&top_k=5" \
  -H "X-API-Key: $API_KEY"

echo -e "\n\n=== 5. Search with Author Filter ==="
curl "$BASE_URL/search?q=AI+platform&author=Sarah+Mitchell" \
  -H "X-API-Key: $API_KEY"

echo -e "\n\n=== 6. Search with Tag Filter ==="
curl "$BASE_URL/search?q=financial+targets&tags=finance" \
  -H "X-API-Key: $API_KEY"

echo -e "\n\n=== 7. Chat with Knowledge Base ==="
curl -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Who approved the Norway expansion and what was the investment amount?",
    "top_k": 5
  }'

echo -e "\n\n=== 8. Chat - Cross Document Question ==="
curl -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "What role did DataBridge Solutions play and what was the revenue growth?",
    "top_k": 5
  }'

echo -e "\n\n=== 9. Get Full Entity Graph ==="
curl "$BASE_URL/graph" \
  -H "X-API-Key: $API_KEY"

echo -e "\n\n=== 10. Graph Search - Find docs mentioning both entities ==="
curl "$BASE_URL/graph/search?entity_a=Sarah+Mitchell&entity_b=DataBridge+Solutions" \
  -H "X-API-Key: $API_KEY"

echo -e "\n\n=== 11. Graph Search - Find docs mentioning one entity ==="
curl "$BASE_URL/graph/search?entity_a=Marcus+Johansson" \
  -H "X-API-Key: $API_KEY"

echo -e "\n\n=== 12. Graph Enhanced Search - 3 layer pipeline ==="
curl "$BASE_URL/search/graph-enhanced?q=AI+strategy&entity_a=Sarah+Mitchell&entity_b=DataBridge+Solutions&top_k=5" \
  -H "X-API-Key: $API_KEY"

echo -e "\n\nDone!"

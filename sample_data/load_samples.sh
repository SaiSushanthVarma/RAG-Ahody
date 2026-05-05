#!/bin/bash
BASE_URL="http://127.0.0.1:8000"
API_KEY="ahody-secret-key-2026"

echo "Loading sample documents..."

# Memo 1
curl -s -X POST "$BASE_URL/text" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "text": "INTERNAL MEMO\nTo: All Staff\nFrom: Sarah Mitchell, CEO\nDate: March 15, 2024\nSubject: Q1 Strategy Update - NordMedia Group\n\nNordMedia Group had a strong start to 2024. Under the leadership of Sarah Mitchell, the company has expanded its digital division by 40% since January. Our partnerships with TechVentures AB and Scandinavia Press have been instrumental in this growth.\n\nThe new AI content platform, developed in collaboration with DataBridge Solutions, is scheduled to launch in April 2024. This platform will revolutionize how NordMedia Group produces and distributes content across all channels.\n\nKey appointments this quarter include Erik Lindqvist as Head of Digital Operations and Anna Bergstrom as Chief Technology Officer. Both will report directly to Sarah Mitchell.\n\nNordMedia Group Stockholm headquarters will undergo renovation starting May 2024, with the Gothenburg office serving as temporary headquarters. The renovation is being managed by Nordic Construction AB.\n\nFinancial targets for Q2 have been set by CFO Marcus Johansson, with a focus on expanding revenue streams in Norway and Denmark through partnerships with Oslo Media House and Copenhagen Digital.",
    "title": "Q1 Strategy Update",
    "author": "Sarah Mitchell",
    "source": "Internal Memo",
    "tags": ["strategy", "Q1", "2024"]
  }' | python3 -c "import sys,json; r=json.load(sys.stdin); print('Memo 1 uploaded:', r['title'])"

# Memo 2
curl -s -X POST "$BASE_URL/text" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "text": "INTERNAL MEMO\nTo: Digital Team\nFrom: Erik Lindqvist, Head of Digital Operations\nDate: April 2, 2024\nSubject: AI Platform Launch Update - NordMedia Group\n\nFollowing the Q1 strategy announcement by CEO Sarah Mitchell, the AI content platform developed with DataBridge Solutions is on track for April launch. Erik Lindqvist and Anna Bergstrom have been working closely with the DataBridge Solutions team to finalize the integration.\n\nThe platform uses advanced machine learning to automate content tagging, distribution, and audience targeting. NordMedia Group expects this to reduce manual content operations by 60% within six months.\n\nDataBridge Solutions CEO, James Carter, visited NordMedia Group Stockholm headquarters last week to review the final implementation. James Carter expressed confidence that the platform will set a new industry standard across Scandinavia.\n\nTechVentures AB has also agreed to provide ongoing technical support for the platform. Their representative, Lisa Holm, will be embedded in the NordMedia Group digital team starting May 2024.\n\nCFO Marcus Johansson has confirmed the platform budget is within the Q2 financial targets set for NordMedia Group. The Gothenburg office team led by Erik Lindqvist will handle the platform rollout across Norway and Denmark.",
    "title": "AI Platform Launch Update",
    "author": "Erik Lindqvist",
    "source": "Internal Memo",
    "tags": ["AI", "platform", "2024"]
  }' | python3 -c "import sys,json; r=json.load(sys.stdin); print('Memo 2 uploaded:', r['title'])"

# Memo 3
curl -s -X POST "$BASE_URL/text" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "text": "INTERNAL MEMO\nTo: Executive Team\nFrom: Marcus Johansson, CFO\nDate: April 20, 2024\nSubject: Q2 Financial Review and Norway/Denmark Expansion\n\nNordMedia Group Q2 financial performance has exceeded expectations. CFO Marcus Johansson confirms that revenue is up 28% compared to Q2 2023, driven primarily by the partnership with Oslo Media House and Copenhagen Digital.\n\nThe AI platform launched in April by Erik Lindqvist and Anna Bergstrom has already shown measurable impact. DataBridge Solutions has reported a 45% improvement in content delivery efficiency since the platform went live.\n\nCEO Sarah Mitchell has approved an additional investment of 5 million SEK into the Norway and Denmark expansion. Oslo Media House CEO, Peter Hansen, and Copenhagen Digital Director, Maria Andersen, will meet with Sarah Mitchell and Marcus Johansson in Stockholm next month to finalize partnership agreements.\n\nTechVentures AB has proposed extending their technical support contract through 2025. Lisa Holm from TechVentures AB presented the proposal to Anna Bergstrom and Erik Lindqvist last week.\n\nThe Stockholm headquarters renovation managed by Nordic Construction AB is progressing on schedule. NordMedia Group expects to return to Stockholm from the Gothenburg temporary office by September 2024.\n\nMarcus Johansson projects NordMedia Group will hit annual revenue targets by Q3, with further growth expected from the Scandinavia Press partnership finalized by Sarah Mitchell in Q1.",
    "title": "Q2 Financial Review",
    "author": "Marcus Johansson",
    "source": "Internal Memo",
    "tags": ["finance", "Q2", "2024", "expansion"]
  }' | python3 -c "import sys,json; r=json.load(sys.stdin); print('Memo 3 uploaded:', r['title'])"

# PDF
curl -s -X POST "$BASE_URL/document" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@sample_data/board_report_q2_2024.pdf" \
  -F "title=Board Report Q2 2024" \
  -F "author=Sarah Mitchell" \
  -F "source=Board Report" \
  -F "tags=board,Q2,2024,finance" | python3 -c "import sys,json; r=json.load(sys.stdin); print('PDF uploaded:', r['title'], '- chunks:', r['chunks_created'])"

echo "Done! All sample documents loaded."

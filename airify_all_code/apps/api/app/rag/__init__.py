"""RAG / Knowledge foundation (V1 — STUB ONLY).

Prepares architecture for future Retrieval-Augmented Generation:
- Knowledge base for air quality facts
- Source citation requirements
- Grounding policy (no hallucination)

V1 rules:
- No OpenAI API calls
- No embedding model calls
- No internet search
- No external vector database
- Local stub only
- All claims labeled as mock/ungrounded unless source exists
- Future RAG must cite source documents
"""

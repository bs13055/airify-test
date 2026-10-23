# RAG Readiness Notes

## Status: Architecture Prepared, No External APIs

V1 includes a local stub knowledge base only. No embedding models,
external APIs, or vector databases are used.

## Future RAG Purposes

- Ground explanations in cited air quality research
- Provide contextual knowledge about PM2.5 sources and effects
- Support multi-language factual responses
- Enable source-attributed recommendations

## Source Citation Rules

All RAG-generated content must:
1. Cite the source document or knowledge entry
2. Distinguish verified facts from general knowledge
3. Label ungrounded content clearly
4. Never present hallucinated content as factual
5. Never make medical claims regardless of source

## No-Hallucination Rules

- If no relevant source exists, say so explicitly
- Do not generate plausible-sounding but unsourced claims
- Label confidence level of retrieved information
- Prefer "unknown" over fabrication
- Always include grounding status in output

## No Medical Advice Rule

Even if RAG retrieves health-related content from sources:
- It MUST NOT be presented as medical advice
- It MUST include disclaimers
- It MUST be labeled as general information only
- Clinical claims require separate validation pipeline

## Future Vector DB Options (Design Only)

- PostgreSQL + pgvector (portable, self-hosted)
- ChromaDB (lightweight, local-first)
- Pinecone (managed, cloud)
- Qdrant (self-hosted, performant)

Selection criteria: portability, self-hosting capability, no vendor lock-in.

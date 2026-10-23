"""Repository layer (storage abstractions).

Provides portable, database-agnostic interfaces for persistence. In bootstrap,
only in-memory implementations are provided. Future Postgres/Redis backends
can be swapped in without changing service layer code.
"""

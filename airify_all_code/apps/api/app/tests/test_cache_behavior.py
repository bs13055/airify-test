"""Tests for TTL cache behavior."""

from __future__ import annotations

import time

from app.providers.cache import TTLCache


def test_cache_set_and_get():
    cache = TTLCache(default_ttl_seconds=10)
    cache.set("key", "value")
    assert cache.get("key") == "value"


def test_cache_miss_returns_none():
    cache = TTLCache()
    assert cache.get("nonexistent") is None


def test_cache_expired_entry_returns_none():
    """Expired entries must not be returned."""
    cache = TTLCache(default_ttl_seconds=0.01)
    cache.set("key", "value")
    time.sleep(0.02)
    assert cache.get("key") is None


def test_cache_custom_ttl():
    cache = TTLCache(default_ttl_seconds=100)
    # Short TTL should expire quickly.
    cache.set("short", "v", ttl_seconds=-1)
    assert cache.get("short") is None
    # Normal TTL should remain valid.
    cache.set("normal", "v")
    assert cache.get("normal") == "v"


def test_cache_delete():
    cache = TTLCache()
    cache.set("k", "v")
    assert cache.has("k") is True
    cache.clear()
    assert cache.has("k") is False


def test_cache_has_method():
    cache = TTLCache()
    assert cache.has("x") is False
    cache.set("x", 42)
    assert cache.has("x") is True


def test_cache_overwrite():
    cache = TTLCache()
    cache.set("k", "old")
    cache.set("k", "new")
    assert cache.get("k") == "new"

"""Tests for provider contracts: roles, stub behavior, and no network imports."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from app.models.observations import GeoPoint
from app.models.providers import ProviderKind, ProviderRole
from app.providers.air4thai_provider import Air4ThaiProvider
from app.providers.cache import TTLCache
from app.providers.open_meteo_provider import OpenMeteoProvider
from app.providers.openweathermap_provider import OpenWeatherMapProvider

_FORBIDDEN_NETWORK_MODULES = {
    "requests",
    "httpx",
    "aiohttp",
    "urllib",
    "urllib.request",
    "urllib3",
    "socket",
    "http",
    "http.client",
}


def test_provider_roles():
    assert Air4ThaiProvider().kind == ProviderKind.PM25
    assert Air4ThaiProvider().role == ProviderRole.PM25_SOURCE

    assert OpenMeteoProvider().kind == ProviderKind.WEATHER
    assert OpenMeteoProvider().role == ProviderRole.WEATHER_PRIMARY

    assert OpenWeatherMapProvider().kind == ProviderKind.WEATHER
    assert OpenWeatherMapProvider().role == ProviderRole.WEATHER_FALLBACK


def test_owm_is_not_a_pm25_source():
    owm = OpenWeatherMapProvider()
    assert owm.kind != ProviderKind.PM25
    assert owm.role != ProviderRole.PM25_SOURCE


def test_live_methods_raise_not_implemented():
    point = GeoPoint(lat=13.75, lon=100.50)
    for provider in (OpenMeteoProvider(), OpenWeatherMapProvider(), Air4ThaiProvider()):
        with pytest.raises(NotImplementedError):
            provider.fetch_live(point)


def test_ttl_cache_basic_behavior():
    cache = TTLCache(default_ttl_seconds=100)
    assert cache.get("missing") is None
    cache.set("k", "v")
    assert cache.get("k") == "v"
    assert cache.has("k") is True
    # Expired entries are not returned.
    cache.set("short", "v", ttl_seconds=-1)
    assert cache.get("short") is None


def test_provider_files_do_not_import_network_libraries():
    """Static check: provider modules must not import network libraries."""
    providers_dir = Path(__file__).resolve().parents[1] / "providers"
    py_files = sorted(providers_dir.glob("*.py"))
    assert py_files, "expected provider files to scan"

    offenders = {}
    for f in py_files:
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in _FORBIDDEN_NETWORK_MODULES:
                        offenders.setdefault(f.name, []).append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                if mod in _FORBIDDEN_NETWORK_MODULES:
                    offenders.setdefault(f.name, []).append(node.module)

    assert offenders == {}, f"Network imports found in provider files: {offenders}"

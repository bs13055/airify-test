"""Phase 3 — provider refresh/cache + weather fallback + request-path safety.

Verifies: Air4Thai=PM2.5-only, Open-Meteo=primary wind, OpenWeatherMap=weather
fallback only (never PM2.5, gated by OPENWEATHER_API_KEY presence), cache-first
adapter with mock fallback, and that the user-request path never calls a provider.
"""

from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.providers.air4thai_provider import Air4ThaiProvider
from app.providers.open_meteo_provider import OpenMeteoProvider
from app.providers.openweathermap_provider import OpenWeatherMapProvider
from app.services import core_engine_adapter_service as adapter
from app.services import engine_snapshot_cache
from app.services import provider_normalizers as norm
from app.services.provider_refresh_service import ProviderRefreshService

COVERED = (13.7563, 100.5018)

AIR4THAI_RAW = {
    "stations": [
        {"stationID": "BKK_N", "nameTH": "เหนือ", "nameEN": "North", "lat": 13.90, "long": 100.50, "AQILast": {"PM25": {"value": "22"}, "AQI": {"aqi": "68"}}},
        {"stationID": "BKK_S", "nameTH": "ใต้", "nameEN": "South", "lat": 13.60, "long": 100.50, "AQILast": {"PM25": {"value": "30"}, "AQI": {"aqi": "84"}}},
        {"stationID": "BKK_E", "nameTH": "ออก", "nameEN": "East", "lat": 13.75, "long": 100.70, "AQILast": {"PM25": {"value": "26"}, "AQI": {"aqi": "76"}}},
        {"stationID": "BKK_W", "nameTH": "ตก", "nameEN": "West", "lat": 13.75, "long": 100.30, "AQILast": {"PM25": {"value": "19"}, "AQI": {"aqi": "63"}}},
        {"stationID": "BKK_C1", "nameTH": "กลาง1", "nameEN": "C1", "lat": 13.79, "long": 100.55, "AQILast": {"PM25": {"value": "24"}, "AQI": {"aqi": "72"}}},
        {"stationID": "BKK_C2", "nameTH": "กลาง2", "nameEN": "C2", "lat": 13.72, "long": 100.47, "AQILast": {"PM25": {"value": "28"}, "AQI": {"aqi": "80"}}},
    ]
}
OPEN_METEO_RAW = {"current_weather": {"windspeed": 2.6, "winddirection": 50.0}}
# Note the bogus "pm25" — it must NEVER be read (OpenWeatherMap is weather-only).
OWM_RAW = {"wind": {"speed": 3.1, "deg": 60.0}, "pm25": 999}


@pytest.fixture(autouse=True)
def _clean_state():
    engine_snapshot_cache.clear()
    get_settings.cache_clear()
    yield
    engine_snapshot_cache.clear()
    get_settings.cache_clear()


# ---------------- Normalizers ----------------
class TestNormalizers:
    def test_air4thai_pm25_and_aqi_separate(self):
        stations = norm.normalize_air4thai_stations(AIR4THAI_RAW)
        assert len(stations) == 6
        c1 = next(s for s in stations if s.station_id == "BKK_C1")
        assert c1.pm25 == 24.0 and c1.aqi == 72.0  # separate values
        assert c1.source == "air4thai_pcd"

    def test_open_meteo_wind(self):
        w = norm.normalize_open_meteo_wind(OPEN_METEO_RAW, 13.75, 100.5)
        assert w is not None and w.source == "open_meteo"
        assert w.speed_mps == 2.6 and w.direction_from_deg == 50.0
        assert w.direction_to_deg == (50.0 + 180.0) % 360.0

    def test_owm_wind_is_weather_only_no_pm25(self):
        w = norm.normalize_openweathermap_wind(OWM_RAW, 13.75, 100.5)
        assert w is not None and w.source == "openweathermap_fallback"
        assert w.speed_mps == 3.1 and w.direction_from_deg == 60.0
        # WindObservation has NO pm25 attribute — OWM can never carry PM2.5.
        assert not hasattr(w, "pm25")


# ---------------- Refresh + weather fallback + secret gating ----------------
class TestRefresh:
    def test_open_meteo_primary(self):
        svc = ProviderRefreshService()
        status = svc.refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=OPEN_METEO_RAW)
        assert status["status"] == "ok" and status["cached"] is True
        assert status["weather_provider_used"] == "open_meteo"
        assert status["source_mode"] == "cached"
        assert status["station_source"] == "air4thai_pcd"
        assert status["provider_calls"] == "none"
        snap = engine_snapshot_cache.get_snapshot()
        assert snap is not None and snap.wind.source == "open_meteo"

    def test_owm_fallback_used_only_with_key_and_enabled(self, monkeypatch):
        monkeypatch.setenv("OPENWEATHER_API_KEY", "dummy-not-a-real-key")
        monkeypatch.setenv("OPENWEATHER_ENABLED", "true")
        get_settings.cache_clear()
        svc = ProviderRefreshService()
        status = svc.refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=None, owm_raw=OWM_RAW)
        assert status["status"] == "ok"
        assert status["weather_provider_used"] == "openweathermap_fallback"
        snap = engine_snapshot_cache.get_snapshot()
        assert snap.wind.source == "openweathermap_fallback"
        # OWM never becomes a PM2.5 source: stations still come from Air4Thai.
        assert all(s.source == "air4thai_pcd" for s in snap.stations)
        assert next(s for s in snap.stations if s.station_id == "BKK_C1").pm25 == 24.0

    def test_owm_fallback_blocked_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENWEATHER_API_KEY", raising=False)
        monkeypatch.setenv("OPENWEATHER_ENABLED", "true")
        get_settings.cache_clear()
        svc = ProviderRefreshService()
        status = svc.refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=None, owm_raw=OWM_RAW)
        assert status["status"] == "unavailable" and status["cached"] is False
        assert status["weather_provider_used"] == "none"
        assert any("OPENWEATHER_API_KEY not set" in w for w in status["warnings"])
        assert engine_snapshot_cache.get_snapshot() is None

    def test_owm_fallback_blocked_when_disabled(self, monkeypatch):
        monkeypatch.setenv("OPENWEATHER_API_KEY", "dummy-not-a-real-key")
        monkeypatch.setenv("OPENWEATHER_ENABLED", "false")
        get_settings.cache_clear()
        svc = ProviderRefreshService()
        status = svc.refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=None, owm_raw=OWM_RAW)
        assert status["weather_provider_used"] == "none"

    def test_no_secret_value_in_status_payload(self, monkeypatch):
        monkeypatch.setenv("OPENWEATHER_API_KEY", "SUPER-SECRET-VALUE-123")
        monkeypatch.setenv("OPENWEATHER_ENABLED", "true")
        get_settings.cache_clear()
        svc = ProviderRefreshService()
        status = svc.refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=None, owm_raw=OWM_RAW)
        import json
        assert "SUPER-SECRET-VALUE-123" not in json.dumps(status)

    def test_live_flag_sets_live_cached(self):
        svc = ProviderRefreshService()
        svc.refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=OPEN_METEO_RAW, live=True)
        assert engine_snapshot_cache.get_snapshot().source_mode == "live_cached"


# ---------------- Cache-first adapter ----------------
class TestAdapterCacheFirst:
    def test_mock_fallback_when_no_cache(self):
        r = adapter.simulate(*COVERED)
        assert r["data_status"] == "engine_demo"
        assert r["weather_provider_used"] == "mock_cache"
        assert r["provider_calls"] == "none"

    def test_uses_cache_when_present(self):
        ProviderRefreshService().refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=OPEN_METEO_RAW)
        r = adapter.simulate(*COVERED)
        assert r["data_status"] == "cached"
        assert r["weather_provider_used"] == "open_meteo"
        assert r["provider_calls"] == "none"
        # PM2.5/AQI separation + ADE forecast-only preserved through the cache path.
        assert r["pm25"]["value_ug_m3"] is not None and r["aqi"]["index"] is not None
        assert r["methods"]["ade_forecast"]["target_time"] is not None
        assert "ade_nowcast" not in r["methods"]

    def test_live_cached_status(self):
        ProviderRefreshService().refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=OPEN_METEO_RAW, live=True)
        assert adapter.simulate(*COVERED)["data_status"] == "live_cached"


# ---------------- Request-path provider safety ----------------
class TestRequestPathNoProviderCall:
    def test_simulate_never_calls_provider_fetch(self, monkeypatch):
        calls: list[str] = []

        def spy(name):
            def _f(self, point):
                calls.append(name)
                raise AssertionError(f"{name}.fetch_live called on the request path!")
            return _f

        monkeypatch.setattr(Air4ThaiProvider, "fetch_live", spy("air4thai"))
        monkeypatch.setattr(OpenMeteoProvider, "fetch_live", spy("open_meteo"))
        monkeypatch.setattr(OpenWeatherMapProvider, "fetch_live", spy("openweathermap"))

        # Both with and without a cache, the request path must not fetch.
        adapter.simulate(*COVERED)
        ProviderRefreshService().refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=OPEN_METEO_RAW)
        adapter.simulate(*COVERED)
        assert calls == []

    def test_endpoint_uses_cache_and_reports_provider(self, client):
        ProviderRefreshService().refresh_engine_snapshot(station_raw=AIR4THAI_RAW, open_meteo_raw=OPEN_METEO_RAW)
        body = client.post("/v1/engine/simulate", json={"location": {"lat": 13.7563, "lon": 100.5018}}).json()
        assert body["data_status"] == "cached"
        assert body["weather_provider_used"] == "open_meteo"
        assert body["provider_calls"] == "none"

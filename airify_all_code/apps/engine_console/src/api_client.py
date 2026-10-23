"""Small provider-free API client for the engine simulation endpoint."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from .engine_console_config import DEFAULT_API_BASE_URL, DEFAULT_TIMEOUT_SECONDS
from .simulation_models import SimulationSummary, parse_simulation_response


@dataclass(frozen=True)
class ApiClientError:
    message: str
    url: str


@dataclass(frozen=True)
class ApiClientResult:
    summary: SimulationSummary | None
    error: ApiClientError | None = None

    @property
    def ok(self) -> bool:
        return self.summary is not None and self.error is None


class EngineApiClient:
    """Client wrapper for /v1/engine/simulate.

    This client only calls the Airify API endpoint. It does not import or call
    provider fetchers and it does not handle secrets.
    """

    def __init__(self, base_url: str = DEFAULT_API_BASE_URL, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def build_get_url(
        self,
        *,
        lat: float,
        lon: float,
        selection_kind: str = "generic_point",
        station_id: str | None = None,
        include_diagnostics: bool = True,
    ) -> str:
        params: dict[str, str] = {
            "lat": str(float(lat)),
            "lon": str(float(lon)),
            "selection_kind": selection_kind,
            "include_diagnostics": "true" if include_diagnostics else "false",
        }
        if station_id:
            params["station_id"] = station_id
        return f"{urljoin(self.base_url + '/', 'v1/engine/simulate')}?{urlencode(params)}"

    def simulate_get(
        self,
        *,
        lat: float,
        lon: float,
        selection_kind: str = "generic_point",
        station_id: str | None = None,
        include_diagnostics: bool = True,
    ) -> ApiClientResult:
        url = self.build_get_url(
            lat=lat,
            lon=lon,
            selection_kind=selection_kind,
            station_id=station_id,
            include_diagnostics=include_diagnostics,
        )
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return ApiClientResult(summary=parse_simulation_response(payload))
        except HTTPError as exc:
            return ApiClientResult(summary=None, error=ApiClientError(f"API returned HTTP {exc.code}.", url))
        except URLError as exc:
            return ApiClientResult(summary=None, error=ApiClientError(f"API not available: {exc.reason}.", url))
        except TimeoutError:
            return ApiClientResult(summary=None, error=ApiClientError("API request timed out.", url))
        except (json.JSONDecodeError, OSError) as exc:
            return ApiClientResult(summary=None, error=ApiClientError(f"Could not read API response: {exc}.", url))


def parse_api_payload(payload: dict[str, Any]) -> SimulationSummary:
    """Test-friendly wrapper for response parsing."""
    return parse_simulation_response(payload)


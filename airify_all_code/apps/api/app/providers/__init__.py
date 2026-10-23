"""Provider abstractions (offline stubs).

NO network libraries are imported anywhere in this package. Provider roles:
- Air4Thai/PCD = PM2.5 observation provider
- Open-Meteo   = primary weather provider
- OpenWeatherMap = weather FALLBACK only (never a PM2.5 source)

All live methods are stubs that raise NotImplementedError. Access is cache-first and
refresh is backend-controlled.
"""

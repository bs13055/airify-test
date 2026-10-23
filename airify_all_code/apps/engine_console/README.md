# Airify PM2.5 Simulation Console

Task: `AIRIFY-COM2-PM25-SIMULATION-CONSOLE-V1-001`

This is a COM2-only analyst/demo console for exploring the Airify PM2.5 engine
workflow:

click point or station -> run `/v1/engine/simulate` -> inspect triangle geometry
-> compare method outputs -> explain validation evidence.

It is intentionally separate from:

- Health App UI
- Developer Portal UI
- Auth/Login/Register
- API provider refresh/fetch path

## Safety

- Demo / validation tool only.
- Environmental PM2.5 estimate only.
- Not medical diagnosis.
- No production/live accuracy claim.
- No trained PI-ML production model claim.
- The console must not call Air4Thai, Open-Meteo, or OpenWeatherMap directly.
- The console calls only `/v1/engine/simulate` or local deterministic demo data.

## Environment

Use the COM2 conda environment:

```bash
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate Zentia
python --version
which python
```

Expected on COM2:

```text
Python 3.12.x
/opt/anaconda3/envs/Zentia/bin/python
```

## Install Console Dependencies

Streamlit, Pandas, and Plotly are dashboard-only dependencies. They are isolated
to this app and are not API runtime dependencies.

```bash
cd /Users/knight/Development/Airify
python -m pip install -r airify_all_code/apps/engine_console/requirements.txt
```

## Start API For API Mode

Run from `/Users/knight/Development/Airify/airify_all_code`:

```bash
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate Zentia
cd /Users/knight/Development/Airify/airify_all_code
python -m uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port 8000
```

The console default API base URL is:

```text
http://localhost:8000
```

For LAN use from another machine, open the console host IP and keep the API
server bound to `0.0.0.0`.

## Start Console

```bash
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate Zentia
cd /Users/knight/Development/Airify/airify_all_code/apps/engine_console
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```

Then open:

```text
http://localhost:8501
```

or from LAN:

```text
http://<COM2_LAN_IP>:8501
```

## Modes

### 1. Free Point Simulation

Uses `selection_kind=generic_point` with a clicked/manual lat/lon. Shows:

- selected point
- data status
- provider calls
- weather provider used
- PM2.5 method outputs
- contributing stations
- triangle geometry
- unavailable reason when no valid triangle exists

Free point has no actual sensor value, so accuracy should be validated through
Station Validation mode.

### 2. Station Validation

Uses `selection_kind=station_validation` and `station_id`. Shows predicted vs
actual PM2.5 for a held-out station.

Hold-out rule:

```text
Hide the target station from the estimation process, predict it from neighbors,
then compare prediction with actual.
```

ADE is shown as forecast-only and is not scored as a same-time nowcast.

### 3. Benchmark Comparison

Uses deterministic demo benchmark data to show:

- MAE / RMSE bar chart
- Actual vs predicted scatter plot with y=x line
- Error spread boxplot
- demo model winner label

The XGBoost / PI-ML rows are prepared benchmark examples only. They are not
production-trained model results.

### 4. Triangle Preview

Shows a 2D lat/lon plot:

- target point/station
- triangle vertices
- support stations
- triangle polygon
- demo wind arrow when the API response uses `mock_cache`

Current API responses do not expose wind speed/direction for cached provider
snapshots, so the console displays `not_exposed_by_api` when needed.

### 5. Trust Explanation

Explains:

- IDW
- Wind-IDW
- ADE forecast
- station validation
- MAE/RMSE
- PM2.5 vs AQI separation
- why OpenWeatherMap is weather fallback only
- why the console makes no medical or production accuracy claim

## Tests

Run from `/Users/knight/Development/Airify/airify_all_code`:

```bash
source /opt/anaconda3/etc/profile.d/conda.sh
conda activate Zentia
python -m pytest packages/core_engine -q
python -m pytest apps/api/app/tests/test_engine_adapter.py -q
python -m pytest apps/api/app/tests/test_engine_provider_cache.py -q
python -m pytest apps/engine_console/tests -q
```

Console tests cover:

- validation metrics
- deterministic demo benchmark generation
- API response parsing
- unavailable response parsing
- API client URL contract
- no provider-fetch imports in console helper modules

## OpenWeatherMap Role

- Open-Meteo is primary weather/wind source.
- OpenWeatherMap is weather fallback only.
- Air4Thai/PCD remains PM2.5 source.
- OpenWeatherMap must never be a PM2.5 source.
- `OPENWEATHER_API_KEY` is env-only and is not handled by this console.
- `/v1/engine/simulate` should continue to report `provider_calls: none`.


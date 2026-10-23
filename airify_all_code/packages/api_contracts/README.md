# packages/api_contracts (scaffold)

> Status: **scaffold pointer.** The live contract is defined by the API at
> `/backend/app/api/v1/demo.py` and documented in
> `airify_all_docs/00_project_entry/17_airify_demo_v1_data_contract.md`.

Target home for the shared, language-neutral Airify API contract (request/response schemas)
consumed by both `apps/api` and `apps/web`. **Not extracted yet.**

## Current demo contract (summary — see docs for full detail)

Prediction fields: `pm25_estimate, forecast_type, confidence, uncertainty, model_version, data_status`
Exposure fields: `activity, duration_minutes, estimated_exposure, add_estimate, exposure_level, safety_note`
Developer fields: `api_version, contract, model_version, data_status, safety_note`

`data_status: demo` labels all current values as demo data. `safety_note` is mandatory on
every payload. No field asserts medical diagnosis or validated model accuracy.

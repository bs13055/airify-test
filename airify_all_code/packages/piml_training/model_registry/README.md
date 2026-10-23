# PI-ML `model_registry/` (empty)

Records model versions and their metadata once training exists. **Empty** — no models registered.

Each future entry should record: `model_version`, artifact path, training config hash,
data window, and a link to its `validation_reports/` entry. A model version **must not** be
promoted for use by the exposure/ADD layer until its validation report exists and passes the gate.

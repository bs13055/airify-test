# airify_all_code/tests (scaffold)

Target home for cross-package / integration tests under the portable layout.

The current passing suite lives with the API at `/backend/app/tests/` and is run from the
repo root:

```bash
python3 -m pytest -q          # backend/app/tests
```

Backend tests are **not moved here yet** (they use `parents[N]` path math tied to the current
layout — see the migration breakpoints in `apps/api/README.md`). Add portable
integration/smoke tests here as packages are extracted.

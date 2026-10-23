"""Make the isolated ``airify_core_engine`` package importable from the API.

Phase-2 demo bridge for the monorepo: if the package is not installed (e.g. no
editable install in the current interpreter), add its ``src`` directory to
``sys.path`` so ``import airify_core_engine`` succeeds. This keeps the demo
runnable in any environment (the ``Zentia`` conda env used for tests, or the
base-env server) without a per-environment install.

Recommended production approach (deferred): install ``airify_core_engine`` as an
editable package or add it to backend package discovery. The core runtime stays
provider-free — importing it triggers NO network I/O.
"""

from __future__ import annotations

import pathlib
import sys


def ensure_importable() -> None:
    try:
        import airify_core_engine  # noqa: F401
        return
    except ModuleNotFoundError:
        # apps/api/app/services/_engine_bridge.py -> parents[4] == airify_all_code
        root = pathlib.Path(__file__).resolve().parents[4]
        src = root / "packages" / "core_engine" / "src"
        if src.is_dir() and str(src) not in sys.path:
            sys.path.insert(0, str(src))


ensure_importable()

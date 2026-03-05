"""Top-level ASGI entrypoint for container runtimes."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_BACKEND_MAIN_PATH = Path(__file__).resolve().parent / "backend" / "main.py"
_BACKEND_MAIN_SPEC = spec_from_file_location("backend_main", _BACKEND_MAIN_PATH)
if _BACKEND_MAIN_SPEC is None or _BACKEND_MAIN_SPEC.loader is None:
    raise RuntimeError(f"Unable to load backend entrypoint from {_BACKEND_MAIN_PATH}")

_backend_main = module_from_spec(_BACKEND_MAIN_SPEC)
_BACKEND_MAIN_SPEC.loader.exec_module(_backend_main)

app = _backend_main.app
celery_app = _backend_main.celery_app

__all__ = ["app", "celery_app"]

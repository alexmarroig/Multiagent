"""Top-level ASGI entrypoint for container runtimes."""

from backend.main import app, celery_app

__all__ = ["app", "celery_app"]

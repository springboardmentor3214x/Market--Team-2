"""
Proxy entry point to support running with:
  uvicorn backend.app.main:app --reload
as well as:
  uvicorn backend.main:app --reload
  uvicorn main:app --reload
"""
from backend.main import app

__all__ = ["app"]

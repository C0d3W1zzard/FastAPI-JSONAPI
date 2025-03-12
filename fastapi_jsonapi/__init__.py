"""JSON API utils package."""

from pathlib import Path

from fastapi_jsonapi.exceptions import BadRequest
from fastapi_jsonapi.exceptions.json_api import HTTPException
from fastapi_jsonapi.querystring import QueryStringManager

from fastapi_jsonapi.api.application_builder import ApplicationBuilder  # isort: skip

__version__ = Path(__file__).parent.joinpath("VERSION").read_text().strip()

__all__ = [
    "ApplicationBuilder",
    "BadRequest",
    "HTTPException",
    "QueryStringManager",
]

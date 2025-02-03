"""
Main module for w_mount service.

In module placed db initialization functions, app factory.
"""

import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from examples.api_for_sqlalchemy.api.views_base import db
from examples.api_for_sqlalchemy.models.base import Base
from examples.api_for_sqlalchemy.urls import add_routes
from fastapi_jsonapi import init

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.append(f"{CURRENT_DIR.parent.parent}")


async def sqlalchemy_init() -> None:
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_app() -> FastAPI:
    """
    Create app factory.

    :return: app
    """
    app = FastAPI(
        title="FastAPI and SQLAlchemy",
        debug=True,
        openapi_url="/openapi.json",
        docs_url="/docs",
    )
    app.config = {"MAX_INCLUDE_DEPTH": 5}
    add_routes(app)
    app.on_event("startup")(sqlalchemy_init)
    app.on_event("shutdown")(db.dispose)
    init(app)
    return app


if __name__ == "__main__":
    uvicorn.run(
        "asgi:app",
        host="0.0.0.0",
        port=8082,
        reload=True,
        app_dir=f"{CURRENT_DIR}",
    )

"""
Main module for w_mount service.

In module placed db initialization functions, app factory.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse as JSONResponse

from examples.api_for_sqlalchemy.api.views_base import db
from examples.api_for_sqlalchemy.models.base import Base
from examples.api_for_sqlalchemy.urls import add_routes

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.append(f"{CURRENT_DIR.parent.parent}")


# noinspection PyUnusedLocal
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.config = {"MAX_INCLUDE_DEPTH": 5}
    add_routes(app)

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await db.engine.dispose()


app = FastAPI(
    title="FastAPI and SQLAlchemy",
    lifespan=lifespan,
    debug=True,
    default_response_class=JSONResponse,
    docs_url="/docs",
    openapi_url="/openapi.json",
)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8082,
        reload=True,
        app_dir=f"{CURRENT_DIR}",
    )

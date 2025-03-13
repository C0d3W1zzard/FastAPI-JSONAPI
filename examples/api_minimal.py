import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, ClassVar, Optional

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.responses import ORJSONResponse as JSONResponse
from pydantic import ConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from examples.api_for_sqlalchemy.models.db import DB
from fastapi_jsonapi import ApplicationBuilder
from fastapi_jsonapi.misc.sqla.generics.base import ViewBaseGeneric
from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.views import Operation, OperationConfig, ViewBase

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.append(f"{CURRENT_DIR.parent.parent}")
db = DB(
    url=make_url(f"sqlite+aiosqlite:///{CURRENT_DIR}/db.sqlite3"),
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]


class UserSchema(BaseModel):
    """User base schema."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    name: str


class SessionDependency(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    session: AsyncSession = Depends(db.session)


def session_dependency_handler(view: ViewBase, dto: SessionDependency) -> dict[str, Any]:
    return {
        "session": dto.session,
    }


class UserView(ViewBaseGeneric):
    operation_dependencies: ClassVar = {
        Operation.ALL: OperationConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=session_dependency_handler,
        ),
    }


def add_routes(app: FastAPI):
    builder = ApplicationBuilder(app)
    builder.add_resource(
        path="/users",
        tags=["User"],
        view=UserView,
        schema=UserSchema,
        model=User,
        resource_type="user",
    )
    builder.initialize()


# noinspection PyUnusedLocal
@asynccontextmanager
async def lifespan(app: FastAPI):
    add_routes(app)

    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await db.dispose()


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
        app,
        host="0.0.0.0",
        port=8080,
    )

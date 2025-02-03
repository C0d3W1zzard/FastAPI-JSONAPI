import sys
from pathlib import Path
from typing import ClassVar, Annotated, Optional

import uvicorn
from fastapi import APIRouter, Depends, FastAPI
from pydantic import ConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from examples.api_for_sqlalchemy.models.db import DB
from fastapi_jsonapi import RoutersJSONAPI, init
from fastapi_jsonapi.misc.sqla.generics.base import DetailViewBaseGeneric, ListViewBaseGeneric
from fastapi_jsonapi.schema_base import BaseModel
from fastapi_jsonapi.types_metadata import ClientCanSetId
from fastapi_jsonapi.views.utils import HTTPMethod, HTTPMethodConfig
from fastapi_jsonapi.views.view_base import ViewBase

CURRENT_FILE = Path(__file__).resolve()
CURRENT_DIR = CURRENT_FILE.parent
sys.path.append(f"{CURRENT_DIR.parent.parent}")
db = DB(
    url=make_url(f"sqlite+aiosqlite:///{CURRENT_DIR.absolute()}/db.sqlite3"),
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]]


class UserAttributesBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    name: str


class UserSchema(UserAttributesBaseSchema):
    """User base schema."""


class UserPatchSchema(UserAttributesBaseSchema):
    """User PATCH schema."""


class UserInSchema(UserAttributesBaseSchema):
    """User input schema."""

    id: Annotated[int, ClientCanSetId()]


async def sqlalchemy_init() -> None:
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class SessionDependency(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    session: AsyncSession = Depends(db.session)


def session_dependency_handler(view: ViewBase, dto: SessionDependency) -> dict:
    return {
        "session": dto.session,
    }


class UserDetailView(DetailViewBaseGeneric):
    method_dependencies: ClassVar = {
        HTTPMethod.ALL: HTTPMethodConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=session_dependency_handler,
        )
    }


class UserListView(ListViewBaseGeneric):
    method_dependencies: ClassVar = {
        HTTPMethod.ALL: HTTPMethodConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=session_dependency_handler,
        )
    }


def add_routes(app: FastAPI):
    tags = [
        {
            "name": "User",
            "description": "",
        },
    ]

    router: APIRouter = APIRouter()
    RoutersJSONAPI(
        router=router,
        path="/users",
        tags=["User"],
        class_detail=UserDetailView,
        class_list=UserListView,
        schema=UserSchema,
        resource_type="user",
        schema_in_patch=UserPatchSchema,
        schema_in_post=UserInSchema,
        model=User,
    )

    app.include_router(router, prefix="")
    return tags


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
    add_routes(app)
    app.on_event("startup")(sqlalchemy_init)
    app.on_event("shutdown")(db.dispose)
    init(app)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        f"{CURRENT_FILE.name.replace(CURRENT_FILE.suffix, '')}:app",
        host="0.0.0.0",
        port=8084,
        reload=True,
        app_dir=f"{CURRENT_DIR}",
    )

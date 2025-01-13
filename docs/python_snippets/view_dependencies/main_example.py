from __future__ import annotations

from typing import ClassVar

from fastapi import Depends, Header
from pydantic import BaseModel, ConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from typing_extensions import Annotated, Optional

from fastapi_jsonapi.exceptions import Forbidden
from fastapi_jsonapi.misc.sqla.generics.base import (
    DetailViewBaseGeneric,
    ListViewBaseGeneric,
)
from fastapi_jsonapi.views.utils import (
    HTTPMethod,
    HTTPMethodConfig,
)
from fastapi_jsonapi.views.view_base import ViewBase


def get_async_sessionmaker() -> sessionmaker:
    return sessionmaker(
        bind=create_async_engine(
            url=make_url(
                f"sqlite+aiosqlite:///tmp/db.sqlite3",
            )
        ),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def async_session_dependency():
    """
    Get session as dependency

    :return:
    """
    session_maker = get_async_sessionmaker()
    async with session_maker() as db_session:  # type: AsyncSession
        yield db_session
        await db_session.rollback()


class SessionDependency(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    session: AsyncSession = Depends(async_session_dependency)


async def common_handler(view: ViewBase, dto: SessionDependency) -> dict:
    return {
        "session": dto.session,
    }


async def check_that_user_is_admin(x_auth: Annotated[str, Header()]):
    if x_auth != "admin":
        raise Forbidden(detail="Only admin user have permissions to this endpoint")


class AdminOnlyPermission(BaseModel):
    is_admin: Optional[bool] = Depends(check_that_user_is_admin)


class DetailView(DetailViewBaseGeneric):
    method_dependencies: ClassVar[dict[HTTPMethod, HTTPMethodConfig]] = {
        HTTPMethod.ALL: HTTPMethodConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=common_handler,
        ),
    }


class ListView(ListViewBaseGeneric):
    method_dependencies: ClassVar[dict[HTTPMethod, HTTPMethodConfig]] = {
        HTTPMethod.GET: HTTPMethodConfig(dependencies=AdminOnlyPermission),
        HTTPMethod.ALL: HTTPMethodConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=common_handler,
        ),
    }

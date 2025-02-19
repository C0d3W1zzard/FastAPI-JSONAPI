from typing import Optional, ClassVar

from fastapi import Depends, Header
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from examples.api_for_sqlalchemy.models.db import DB
from fastapi_jsonapi.exceptions import Forbidden
from fastapi_jsonapi.misc.sqla.generics.base import DetailViewBaseGeneric, ListViewBaseGeneric
from fastapi_jsonapi.views.utils import HTTPMethod, HTTPMethodConfig
from fastapi_jsonapi.views.view_base import ViewBase

db = DB(
    url="sqlite+aiosqlite:///tmp/db.sqlite3",
)


class SessionDependency(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    session: AsyncSession = Depends(db.session)


async def common_handler(view: ViewBase, dto: SessionDependency) -> dict:
    return {
        "session": dto.session,
    }


async def check_that_user_is_admin(x_auth: Annotated[str, Header()]):
    if x_auth != "admin":
        raise Forbidden(detail="Only admin user have permissions to this endpoint.")


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
        HTTPMethod.GET: HTTPMethodConfig(
            dependencies=AdminOnlyPermission,
        ),
        HTTPMethod.ALL: HTTPMethodConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=common_handler,
        ),
    }

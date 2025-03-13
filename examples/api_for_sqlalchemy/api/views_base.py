from typing import ClassVar

from fastapi import Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from examples.api_for_sqlalchemy import config
from examples.api_for_sqlalchemy.models.db import DB
from fastapi_jsonapi.data_layers.sqla.orm import SqlalchemyDataLayer
from fastapi_jsonapi.misc.sqla.generics.base import ViewBaseGeneric
from fastapi_jsonapi.views import Operation, OperationConfig, ViewBase

db = DB(
    url=make_url(config.SQLA_URI),
)


class SessionDependency(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    session: AsyncSession = Depends(db.session)


def handler(view: ViewBase, dto: SessionDependency) -> dict:
    return {
        "session": dto.session,
    }


class ViewBase(ViewBaseGeneric):
    """
    Generic view base (detail)
    """

    data_layer_cls = SqlalchemyDataLayer

    operation_dependencies: ClassVar = {
        Operation.ALL: OperationConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=handler,
        ),
    }

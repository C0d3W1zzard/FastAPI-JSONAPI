from typing import ClassVar

from fastapi import Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_jsonapi.misc.sqla.generics.base import ViewBaseGeneric as ViewBaseGenericHelper
from fastapi_jsonapi.views import Operation, OperationConfig, ViewBase
from tests.fixtures.db_connection import async_session_dependency


class ArbitraryModelBase(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class SessionDependency(ArbitraryModelBase):
    session: AsyncSession = Depends(async_session_dependency)


def common_handler(view: ViewBase, dto: SessionDependency) -> dict:
    return {
        "session": dto.session,
    }


class ViewBaseGeneric(ViewBaseGenericHelper):
    operation_dependencies: ClassVar = {
        Operation.ALL: OperationConfig(
            dependencies=SessionDependency,
            prepare_data_layer_kwargs=common_handler,
        ),
    }

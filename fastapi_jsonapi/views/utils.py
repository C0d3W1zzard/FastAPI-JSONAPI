from enum import Enum
from functools import cache
from typing import Callable, Coroutine, Optional, Type, Union

from pydantic import BaseModel, ConfigDict

from fastapi_jsonapi.schema_builder import JSONAPIResultDetailSchema, JSONAPIResultListSchema

JSONAPIResponse = Union[JSONAPIResultDetailSchema, JSONAPIResultListSchema]


class HTTPMethod(Enum):
    ALL = "all"
    GET = "get"
    POST = "post"
    PATCH = "patch"
    DELETE = "delete"

    @staticmethod
    @cache
    def names() -> set[str]:
        return {item.name for item in HTTPMethod}


class HTTPMethodConfig(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    dependencies: Optional[Type[BaseModel]] = None
    prepare_data_layer_kwargs: Optional[Union[Callable, Coroutine]] = None

    @property
    def handler(self) -> Optional[Union[Callable, Coroutine]]:
        return self.prepare_data_layer_kwargs
